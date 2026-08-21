---
search:
  exclude: true
title: Продвинутый JDBC с Kora
summary: Learn advanced Kora JDBC repository patterns with related tables, nullable foreign keys, entity macros, batch inserts, transactions, projections, and custom mappers
tags: database, jdbc, postgres, transactions, batch, macros
---

# Продвинутый JDBC с Kora { #advanced-jdbc-kora }

Это руководство расширяет пользовательский API на PostgreSQL управлением задачами. Вы добавите вторую таблицу, будете вставлять задачи пакетами, проверять необязательных исполнителей, обновлять
состояние задачи, а затем добавите проекцию чтения, которая объединяет задачи с пользователями.

Главная идея в том, что JDBC-репозитории Kora остаются SQL-first и удобно работают с проекциями. Репозиторий не привязан к одному классу сущности. Один репозиторий может использовать модель для
вставки, скалярные результаты запросов, счетчики обновлений и несколько проекций чтения, каждая из которых выбирается под конкретный запрос. Это сохраняет доступ к данным явным и позволяет каждому
SQL-запросу выбирать только те поля, которые ему действительно нужны.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java Database JDBC Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-database-jdbc-advanced-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin Database JDBC Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-database-jdbc-advanced-app).

## Что вы соберете { #youll-build }

Вы добавите управление задачами в JDBC-приложение:

- таблицу `tasks` с nullable-внешним ключом `user_assignee_id` на `users.id`
- компактную модель вставки `TaskDAO`
- пользовательские преобразователи JDBC для `TaskStatus` и параметров массивов PostgreSQL `List<Long>`
- `TaskRepository`, который вставляет пакеты, проверяет исполнителей и обновляет состояние задачи
- проекцию назначенной задачи, которая переиспользует `TaskDAO` и `UserDAO` через `@Embedded`
- DTO запросов и ответов для HTTP API
- сервисный слой, который держит проверку и пакетную вставку в одной транзакции

## Что понадобится { #youll-need }

- JDK 17 или новее
- Docker или другой локальный экземпляр PostgreSQL
- Gradle 7+
- текстовый редактор или среда разработки
- пройденное руководство [База данных JDBC](database-jdbc.md)

## Требования { #prerequisites }

!!! note "Обязательно: пройдите руководство по базе данных JDBC"

    Это руководство предполагает, что вы уже прошли **[Базу данных JDBC](database-jdbc.md)** и у вас уже есть рабочий пользовательский API на PostgreSQL с `UserDAO`, `UserRepository`, миграциями Flyway, JDBC-конфигурацией и модулями базы данных Kora.

    Если вы еще не прошли базовое JDBC-руководство, сделайте это сначала. Это руководство сохраняет существующую таблицу `users` и добавляет продвинутое поведение репозитория вокруг связанной таблицы `tasks`.

## Обзор { #overview }

Базовое JDBC-руководство использует одну таблицу и один репозиторий. Этого достаточно, чтобы изучить настройку соединения, миграции Flyway, `@Repository`, `@Query`, `@EntityJdbc` и явное сопоставление
столбцов. В настоящих приложениях быстро появляются связанные таблицы, и здесь возникают несколько практических вопросов по работе с базой данных:

- как представить необязательную связь в SQL и Java/Kotlin?
- когда модель для вставки должна отличаться от проекции чтения?
- как макросы сущностей уменьшают повторяющийся SQL, сохраняя запросы видимыми?
- как пользовательские преобразователи JDBC становятся частью сгенерированного кода репозитория?
- где выполнять многошаговые проверки согласованности в одной транзакции?
- как передать много идентификаторов в PostgreSQL без ручной сборки SQL-строк?
- как один репозиторий может раскрывать несколько форм результата под конкретные запросы?

Ответ Kora намеренно остается SQL-first. Задача ссылается на пользователя через `user_assignee_id`, но `TaskDAO` не превращается в лениво загружаемый граф объектов. Операции вставки используют
компактную модель задачи. Операции чтения, которым нужны данные исполнителя, используют явный `JOIN` и проекцию, которая переиспользует `TaskDAO` и `UserDAO`.

### `Nullable`-внешние ключи { #nullable-foreign-keys }

Столбец `tasks.user_assignee_id` допускает `NULL`. Задачу можно создать до того, как у нее появится исполнитель, а назначить позже. Когда значение присутствует, PostgreSQL все равно обеспечивает
ссылочную целостность:

```sql
user_assignee_id BIGINT NULL REFERENCES users(id) ON DELETE SET NULL
```

Эта nullable-семантика видна в схеме, в DAO-модели и в правилах сервиса. Необязательные связи часто встречаются в промышленных системах. Когда они остаются явными столбцами базы данных, поведение
легко понимать, тестировать и оптимизировать.

### Репозиторий для всех { #repository-everything }

Во многих фреймворках шаблон репозитория часто объясняется как "один репозиторий для одной сущности". Это может приводить к лишним репозиториям или дублированию классов моделей всякий раз, когда
запросу нужна немного другая форма. Kora JDBC не навязывает такую структуру.

Метод репозитория Kora может возвращать:

- скалярное значение, например `Long`
- `UpdateCount`
- базовую сущность, например `TaskDAO`
- вложенную проекцию, например `TaskDAO.SelectAssigned`
- список любой из этих форм

Это значит, что один репозиторий может оставаться рядом с одной областью базы данных и при этом раскрывать проекции под конкретные запросы. Вы можете выбирать только те поля, которые нужны текущему
сценарию, вместо загрузки полного графа объектов. Это повышает производительность, сохраняет SQL осмысленным и избавляет от создания отдельного репозитория под каждую проекцию.

### Макросы репозитория { #repository-macros }

Аннотации общего модуля Kora для баз данных описывают, как прикладные типы сопоставляются со столбцами базы данных. JDBC-репозитории могут использовать эти метаданные через макросы, например `%{entity#inserts}`.
Это руководство сначала записывает SQL вставки явно, а затем заменяет повторяющийся фрагмент вставки итоговой формой с макросом:

```java
@Query("INSERT INTO %{entity#inserts} RETURNING id")
@Id
List<Long> insert(@Batch List<TaskDAO> entity);
```

Макрос раскрывается обработчиком аннотаций Kora во время компиляции. Это не построитель SQL во время выполнения. Сгенерированный репозиторий все равно содержит явный SQL, поэтому вы можете посмотреть,
что именно будет выполняться.

### Пользовательские преобразователи по типу { #custom-type-mappers }

JDBC не знает, как ваш доменный enum должен быть представлен в базе данных, и не знает, как Java/Kotlin `List<Long>` должен превращаться в массив PostgreSQL. Приложение предоставляет сфокусированные
компоненты Kora:

- `JdbcResultColumnMapper<TaskStatus>` для чтения `TaskStatus`
- `JdbcParameterColumnMapper<TaskStatus>` для привязки `TaskStatus`
- `JdbcParameterColumnMapper<List<Long>>` для привязки массивов PostgreSQL

Поскольку эти преобразователи являются компонентами и их обобщенные сигнатуры совпадают с полями и параметрами репозитория, Kora может разрешить их по типу. Вам не нужно повторять явные аннотации преобразователей на
каждом параметре `TaskStatus`.

### Пакетные вставки и транзакции { #batch-inserts-transactions }

Подробные правила `@Batch` и транзакций описаны в разделах [пакетных запросов](../documentation/database-common.md#batch-query) и [JDBC-транзакций](../documentation/database-jdbc.md#transaction).

Пакетные вставки и транзакции решают разные задачи. `@Batch` уменьшает повторяющийся JDBC-код, когда один SQL-оператор выполняется для многих сущностей. `inTx(...)` заставляет несколько вызовов
репозитория использовать одну транзакцию базы данных.

В этом руководстве используются оба приема:

1. собрать уникальные идентификаторы исполнителей из запроса
2. запросить существующие идентификаторы пользователей через `ANY(:assigneeIds)`
3. завершиться ошибкой до вставки, если какой-то исполнитель отсутствует
4. вставить все строки задач одним пакетом

Если проверка завершается ошибкой, строки задач не создаются. Если вставка завершается ошибкой, транзакция откатывается.

### Специфичные преобразователи { #specific-mappers }

PostgreSQL может сравнить значение с SQL-массивом через `ANY(:assigneeIds)`. Пользовательский преобразователь `List<Long>` превращает прикладной список в массив PostgreSQL `BIGINT`. Так запрос остается
стабильным независимо от размера списка и не требует небезопасной конкатенации строк вроде ручной сборки `WHERE id IN (...)`.

## Зависимости { #dependencies }

Базовое JDBC-руководство уже добавляет основные зависимости базы данных. Оставьте эти зависимости для PostgreSQL, миграций Flyway и JDBC-репозиториев Kora.

===! ":fontawesome-brands-java: `Java`"

    Обновите `build.gradle`:

    ```groovy
    dependencies {
        // ... existing dependencies ...

        runtimeOnly("org.postgresql:postgresql:42.7.7")

        implementation("ru.tinkoff.kora:database-flyway")
        implementation("ru.tinkoff.kora:database-jdbc")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите `build.gradle.kts`:

    ```kotlin
    dependencies {
        // ... existing dependencies ...

        runtimeOnly("org.postgresql:postgresql:42.7.7")

        implementation("ru.tinkoff.kora:database-flyway")
        implementation("ru.tinkoff.kora:database-jdbc")
    }
    ```

`database-jdbc` предоставляет инфраструктуру репозиториев и фабрику соединений. `database-flyway` применяет миграции схемы до использования репозиториев. Драйвер PostgreSQL позволяет приложению
подключиться к базе данных.

## Модули { #modules }

Убедитесь, что интерфейс приложения включает модули JDBC и Flyway. HTTP, JSON, конфигурация и логирование остаются из предыдущих руководств.

===! ":fontawesome-brands-java: `Java`"

    Обновите `src/main/java/ru/tinkoff/kora/guide/databasejdbc/advanced/Application.java`:

    ```java
    package ru.tinkoff.kora.guide.databasejdbc.advanced;

    import ru.tinkoff.kora.application.graph.KoraApplication;
    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.config.hocon.HoconConfigModule;
    import ru.tinkoff.kora.database.flyway.FlywayJdbcDatabaseModule;
    import ru.tinkoff.kora.database.jdbc.JdbcDatabaseModule;
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule;
    import ru.tinkoff.kora.json.module.JsonModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            JdbcDatabaseModule,  // <----- Подключили модуль
            FlywayJdbcDatabaseModule,  // <----- Подключили модуль
            UndertowHttpServerModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите `src/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/advanced/Application.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasejdbc.advanced

    import ru.tinkoff.kora.application.graph.KoraApplication
    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.config.hocon.HoconConfigModule
    import ru.tinkoff.kora.database.flyway.FlywayJdbcDatabaseModule
    import ru.tinkoff.kora.database.jdbc.JdbcDatabaseModule
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule
    import ru.tinkoff.kora.json.module.JsonModule
    import ru.tinkoff.kora.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        JdbcDatabaseModule,  // <----- Подключили модуль
        FlywayJdbcDatabaseModule,  // <----- Подключили модуль
        UndertowHttpServerModule

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

Репозитории не создают инфраструктуру базы данных сами. Они зависят от компонентов графа `JdbcDatabaseModule`. Flyway тоже является частью графа, поэтому миграции выполняются до того, как приложение
начнет обслуживать запросы.

## Новая сущность { #new-entity }

Начните с самой простой модели базы данных: строка задачи в том виде, в котором приложение ее записывает. Пока не добавляйте проекции чтения. На этом этапе нужны только столбцы, которые передаются при
вставке.

`TaskDAO` хранит состояние задачи как enum `TaskStatus`, поэтому сначала создайте этот общий тип. Он находится в пакете DTO задач, потому что позже HTTP API тоже будет использовать тот же enum, но
полноценные DTO запросов и ответов вводятся после завершения проектирования репозитория.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/ru/tinkoff/kora/guide/databasejdbc/advanced/task/dto/TaskStatus.java`:

    ```java
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto;

    import ru.tinkoff.kora.json.common.annotation.Json;

    @Json
    public enum TaskStatus {
        TODO,
        IN_PROGRESS,
        DONE
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/advanced/task/dto/TaskStatus.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto

    import ru.tinkoff.kora.json.common.annotation.Json

    @Json
    enum class TaskStatus {
        TODO,
        IN_PROGRESS,
        DONE
    }
    ```

`@Json` полезен сразу, потому что `TaskStatus` появится в DTO HTTP-запросов и ответов. Если аннотировать его сейчас, это также предотвращает предупреждения о поздней генерации преобразователей JSON позже.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/ru/tinkoff/kora/guide/databasejdbc/advanced/task/repository/TaskDAO.java`:

    ```java
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.repository;

    import jakarta.annotation.Nullable;
    import ru.tinkoff.kora.database.common.annotation.Column;
    import ru.tinkoff.kora.database.common.annotation.Table;
    import ru.tinkoff.kora.database.jdbc.EntityJdbc;
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskStatus;

    @EntityJdbc
    @Table("tasks")
    public record TaskDAO(
            @Column("title") String title,
            @Column("status") TaskStatus status,
            @Column("description") @Nullable String description,
            @Column("user_assignee_id") @Nullable Long userAssigneeId) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/advanced/task/repository/TaskDAO.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.repository

    import ru.tinkoff.kora.database.common.annotation.Column
    import ru.tinkoff.kora.database.common.annotation.Table
    import ru.tinkoff.kora.database.jdbc.EntityJdbc
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskStatus

    @EntityJdbc
    @Table("tasks")
    data class TaskDAO(
        @field:Column("title") val title: String,
        @field:Column("status") val status: TaskStatus,
        @field:Column("description") val description: String?,
        @field:Column("user_assignee_id") val userAssigneeId: Long?
    )
    ```

`@EntityJdbc` говорит Kora сгенерировать преобразователи JDBC для этой модели. `@Table("tasks")` дает макросам имя таблицы. `@Column` сохраняет имена столбцов базы данных явными, особенно там, где имена
Java/Kotlin и SQL отличаются. `description` и `userAssigneeId` nullable, потому что SQL-столбцы необязательны.

## Новая миграция БД { #new-database-migration }

Теперь создайте таблицу базы данных, которая соответствует `TaskDAO`. Базовое JDBC-руководство уже создало `V1__init_users.sql`, поэтому это руководство добавляет `V2__init_tasks.sql`.

```sql title="src/main/resources/db/migration/V2__init_tasks.sql"
CREATE TABLE IF NOT EXISTS tasks (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(32) NOT NULL,
    user_assignee_id BIGINT NULL REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tasks_user_assignee_id ON tasks(user_assignee_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
```

Миграция — это контракт между SQL и кодом репозитория. `TaskDAO` описывает записываемую часть строки, а таблица также содержит поля, которыми управляет база данных, например `id`, `created_at`
и `updated_at`. Эти поля пригодятся позже, когда мы добавим проекции чтения.

## JDBC-преобразователи { #jdbc-mappers }

Подробно о том, как Kora подбирает `JdbcResultColumnMapper` и `JdbcParameterColumnMapper`, см. в разделе [конвертации JDBC](../documentation/database-jdbc.md#mapping).

База данных хранит `TaskStatus` как текст. JDBC умеет читать `String`, но не может вывести, как ваш enum должен преобразовываться. Добавьте один преобразователь для чтения и один преобразователь для привязки.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/ru/tinkoff/kora/guide/databasejdbc/advanced/task/repository/mapper/TaskStatusResultMapper.java`:

    ```java
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.repository.mapper;

    import java.sql.ResultSet;
    import java.sql.SQLException;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.database.jdbc.mapper.result.JdbcResultColumnMapper;
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskStatus;

    @Component
    public final class TaskStatusResultMapper implements JdbcResultColumnMapper<TaskStatus> {

        @Override
        public TaskStatus apply(ResultSet row, int index) throws SQLException {
            var value = row.getString(index);
            return value == null ? null : TaskStatus.valueOf(value);
        }
    }
    ```

    Создайте `src/main/java/ru/tinkoff/kora/guide/databasejdbc/advanced/task/repository/mapper/TaskStatusParameterMapper.java`:

    ```java
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.repository.mapper;

    import java.sql.PreparedStatement;
    import java.sql.SQLException;
    import java.sql.Types;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.database.jdbc.mapper.parameter.JdbcParameterColumnMapper;
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskStatus;

    @Component
    public final class TaskStatusParameterMapper implements JdbcParameterColumnMapper<TaskStatus> {

        @Override
        public void set(PreparedStatement stmt, int index, TaskStatus value) throws SQLException {
            if (value == null) {
                stmt.setNull(index, Types.VARCHAR);
            } else {
                stmt.setString(index, value.name());
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/advanced/task/repository/mapper/TaskStatusResultMapper.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.repository.mapper

    import java.sql.ResultSet
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.database.jdbc.mapper.result.JdbcResultColumnMapper
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskStatus

    @Component
    class TaskStatusResultMapper : JdbcResultColumnMapper<TaskStatus> {

        override fun apply(row: ResultSet, index: Int): TaskStatus {
            val value = row.getString(index)
            return TaskStatus.valueOf(value)
        }
    }
    ```

    Создайте `src/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/advanced/task/repository/mapper/TaskStatusParameterMapper.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.repository.mapper

    import java.sql.PreparedStatement
    import java.sql.Types
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.database.jdbc.mapper.parameter.JdbcParameterColumnMapper
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskStatus

    @Component
    class TaskStatusParameterMapper : JdbcParameterColumnMapper<TaskStatus?> {

        override fun set(stmt: PreparedStatement, index: Int, value: TaskStatus?) {
            if (value == null) {
                stmt.setNull(index, Types.VARCHAR)
            } else {
                stmt.setString(index, value.name)
            }
        }
    }
    ```

Kora находит эти преобразователи по их обобщенным сигнатурам. Репозиторий может использовать `TaskStatus` напрямую, а сгенерированная реализация внедрит подходящий преобразователь там, где он нужен. Поэтому методы
репозитория ниже не требуют повторяющихся явных аннотаций преобразователей для каждого параметра `TaskStatus`.

## PostgreSQL-преобразователь { #postgresql-mapper }

Подробнее о передаче списков и массивов в запросы смотрите в разделах [выборки по списку](../documentation/database-jdbc.md#select-by-list) и [конвертации JDBC](../documentation/database-jdbc.md#mapping).

Репозиторий будет принимать список идентификаторов исполнителей и использовать `ANY(:assigneeIds)` в SQL. JDBC нужна помощь, чтобы превратить `List<Long>` в массив PostgreSQL.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/ru/tinkoff/kora/guide/databasejdbc/advanced/task/repository/mapper/ListOfLongJdbcParameterMapper.java`:

    ```java
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.repository.mapper;

    import java.sql.PreparedStatement;
    import java.sql.SQLException;
    import java.sql.Types;
    import java.util.List;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.database.jdbc.mapper.parameter.JdbcParameterColumnMapper;

    @Component
    public final class ListOfLongJdbcParameterMapper implements JdbcParameterColumnMapper<List<Long>> {

        @Override
        public void set(PreparedStatement stmt, int index, List<Long> value) throws SQLException {
            if (value == null) {
                stmt.setNull(index, Types.ARRAY);
                return;
            }

            var sqlArray = stmt.getConnection().createArrayOf("BIGINT", value.toArray(Long[]::new));
            stmt.setArray(index, sqlArray);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/advanced/task/repository/mapper/ListOfLongJdbcParameterMapper.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.repository.mapper

    import java.sql.PreparedStatement
    import java.sql.Types
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.database.jdbc.mapper.parameter.JdbcParameterColumnMapper

    @Component
    class ListOfLongJdbcParameterMapper : JdbcParameterColumnMapper<List<Long>> {

        override fun set(stmt: PreparedStatement, index: Int, value: List<Long>) {
            val sqlArray = stmt.connection.createArrayOf("BIGINT", value.toTypedArray())
            stmt.setArray(index, sqlArray)
        }
    }
    ```

Преобразователь небольшой, но он централизует преобразование массивов. Методы репозитория остаются декларативными, а сгенерированная реализация делегирует привязку этому компоненту.

## Новый репозиторий { #new-repository }

Теперь создайте первую версию репозитория. На этом этапе он еще не читает проекции назначенных задач. Он содержит только операции, нужные для проверки исполнителей, пакетной вставки задач и обновления
состояния.

Начните с явного SQL. Так модель привязки остается видимой: каждый вставляемый столбец перечислен вручную, а каждое значение приходит из свойства `TaskDAO` через `:entity.propertyName`.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/ru/tinkoff/kora/guide/databasejdbc/advanced/task/repository/TaskRepository.java`:

    ```java
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.repository;

    import jakarta.annotation.Nullable;
    import java.util.List;
    import ru.tinkoff.kora.database.common.UpdateCount;
    import ru.tinkoff.kora.database.common.annotation.Batch;
    import ru.tinkoff.kora.database.common.annotation.Id;
    import ru.tinkoff.kora.database.common.annotation.Query;
    import ru.tinkoff.kora.database.common.annotation.Repository;
    import ru.tinkoff.kora.database.jdbc.JdbcRepository;
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskStatus;

    @Repository
    public interface TaskRepository extends JdbcRepository {

        @Query("SELECT id FROM users WHERE id = ANY(:assigneeIds)")
        List<Long> findExistingAssigneeId(List<Long> assigneeIds);

        @Query("""
                INSERT INTO tasks(title, status, description, user_assignee_id)
                VALUES (:entity.title, :entity.status, :entity.description, :entity.userAssigneeId)
                RETURNING id
                """)
        @Id
        List<Long> insert(@Batch List<TaskDAO> entity);

        @Query("""
                UPDATE tasks
                SET status = :status, updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """)
        UpdateCount updateStatus(long id, TaskStatus status);

        @Query("""
                UPDATE tasks
                SET user_assignee_id = :userAssigneeId, updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """)
        UpdateCount updateAssignee(long id, @Nullable Long userAssigneeId);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/advanced/task/repository/TaskRepository.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.repository

    import ru.tinkoff.kora.database.common.UpdateCount
    import ru.tinkoff.kora.database.common.annotation.Batch
    import ru.tinkoff.kora.database.common.annotation.Id
    import ru.tinkoff.kora.database.common.annotation.Query
    import ru.tinkoff.kora.database.common.annotation.Repository
    import ru.tinkoff.kora.database.jdbc.JdbcRepository
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskStatus

    @Repository
    interface TaskRepository : JdbcRepository {

        @Query("SELECT id FROM users WHERE id = ANY(:assigneeIds)")
        fun findExistingAssigneeId(assigneeIds: List<Long>): List<Long>

        @Query(
            """
            INSERT INTO tasks(title, status, description, user_assignee_id)
            VALUES (:entity.title, :entity.status, :entity.description, :entity.userAssigneeId)
            RETURNING id
            """
        )
        @Id
        fun insert(@Batch entity: List<TaskDAO>): List<Long>

        @Query(
            """
            UPDATE tasks
            SET status = :status, updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
            """
        )
        fun updateStatus(id: Long, status: TaskStatus): UpdateCount

        @Query(
            """
            UPDATE tasks
            SET user_assignee_id = :userAssigneeId, updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
            """
        )
        fun updateAssignee(id: Long, userAssigneeId: Long?): UpdateCount
    }
    ```

Этот репозиторий уже корректен. Он везде использует обычный SQL, и часто это лучший способ ввести новый запрос, потому что таблица, столбцы и параметры полностью видны.

Здесь уже есть три продвинутых приема:

- `findExistingAssigneeId(...)` использует PostgreSQL `ANY(:assigneeIds)` и преобразователь списка.
- `insert(...)` использует `:entity.title`, `:entity.status`, `:entity.description` и `:entity.userAssigneeId`, чтобы привязать поля каждого пакетного `TaskDAO`.
- `@Batch List<TaskDAO>` заставляет Kora сгенерировать повторяющуюся привязку параметров и вызовы `addBatch()`.

Цена такого подхода — дублирование. Запрос вставки повторяет информацию, которая уже есть в `TaskDAO`:

- `@Table("tasks")` уже называет таблицу.
- `@Column("title")`, `@Column("status")`, `@Column("description")` и `@Column("user_assignee_id")` уже называют столбцы.
- свойства record уже дают пути параметров.

Запомните эту версию. Следующая глава заменит повторяющийся SQL вставки макросом, сохранив остальную часть репозитория явной.

## Новый репозиторий с макросами { #new-repository-macros }

Полный синтаксис макросов, команд вроде `%{entity#inserts}` и ограничения `@Batch` описаны в разделах [макросов](../documentation/database-common.md#macros) и [пакетных запросов](../documentation/database-common.md#batch-query).

Макросы общего модуля Kora для баз данных — это помощники SQL на время компиляции. Они не прячут базу данных за ORM и не создают построители запросов во время выполнения. Макрос раскрывает метаданные сущности в
SQL-текст во время обработки аннотаций.

Используйте макрос там, где SQL-фрагмент механически выводится из одной модели. В этом репозитории оператор вставки хорошо подходит, потому что он вставляет все поля из `TaskDAO` в таблицу, описанную
через `@Table("tasks")`.

Не пытайтесь насильно применять макросы ко всем запросам. `findExistingAssigneeId(...)` возвращает скалярные идентификаторы `Long` из существующей таблицы `users`, а не проекцию `UserDAO`, поэтому
явный `SELECT id FROM users WHERE id = ANY(:assigneeIds)` понятнее. Методы обновления тоже намеренно изменяют только выбранные столбцы и `updated_at`, поэтому обычный SQL лучше сообщает поведение.

Обновите только метод `insert(...)`:

===! ":fontawesome-brands-java: `Java`"

    Обновите `src/main/java/ru/tinkoff/kora/guide/databasejdbc/advanced/task/repository/TaskRepository.java`:

    ```java
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.repository;

    import jakarta.annotation.Nullable;
    import java.util.List;
    import ru.tinkoff.kora.database.common.UpdateCount;
    import ru.tinkoff.kora.database.common.annotation.Batch;
    import ru.tinkoff.kora.database.common.annotation.Id;
    import ru.tinkoff.kora.database.common.annotation.Query;
    import ru.tinkoff.kora.database.common.annotation.Repository;
    import ru.tinkoff.kora.database.jdbc.JdbcRepository;
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskStatus;

    @Repository
    public interface TaskRepository extends JdbcRepository {

        @Query("SELECT id FROM users WHERE id = ANY(:assigneeIds)")
        List<Long> findExistingAssigneeId(List<Long> assigneeIds);

        @Query("INSERT INTO %{entity#inserts} RETURNING id")
        @Id
        List<Long> insert(@Batch List<TaskDAO> entity);

        @Query("""
                UPDATE tasks
                SET status = :status, updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """)
        UpdateCount updateStatus(long id, TaskStatus status);

        @Query("""
                UPDATE tasks
                SET user_assignee_id = :userAssigneeId, updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """)
        UpdateCount updateAssignee(long id, @Nullable Long userAssigneeId);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите `src/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/advanced/task/repository/TaskRepository.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.repository

    import ru.tinkoff.kora.database.common.UpdateCount
    import ru.tinkoff.kora.database.common.annotation.Batch
    import ru.tinkoff.kora.database.common.annotation.Id
    import ru.tinkoff.kora.database.common.annotation.Query
    import ru.tinkoff.kora.database.common.annotation.Repository
    import ru.tinkoff.kora.database.jdbc.JdbcRepository
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskStatus

    @Repository
    interface TaskRepository : JdbcRepository {

        @Query("SELECT id FROM users WHERE id = ANY(:assigneeIds)")
        fun findExistingAssigneeId(assigneeIds: List<Long>): List<Long>

        @Query("INSERT INTO %{entity#inserts} RETURNING id")
        @Id
        fun insert(@Batch entity: List<TaskDAO>): List<Long>

        @Query(
            """
            UPDATE tasks
            SET status = :status, updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
            """
        )
        fun updateStatus(id: Long, status: TaskStatus): UpdateCount

        @Query(
            """
            UPDATE tasks
            SET user_assignee_id = :userAssigneeId, updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
            """
        )
        fun updateAssignee(id: Long, userAssigneeId: Long?): UpdateCount
    }
    ```

`%{entity#inserts}` просит Kora раскрыть таблицу вставки, список столбцов и привязки значений из метаданных `TaskDAO`. Польза не в сокращении кода ради сокращения. Польза в том, что у сопоставления
столбцов появляется один источник истины: если имя столбца меняется в `TaskDAO`, макрос вставки последует за этим сопоставлением во время обработки аннотаций. Также вам не нужно вручную
синхронизировать запрос вставки с моделью поле за полем. Макрос работает со всеми полями, описанными метаданными модели, поэтому главная ответственность — держать сам `TaskDAO` согласованным со схемой
базы данных. Сложные соединения и аккуратно сформированные запросы чтения обычно лучше оставлять явными, но повторяющиеся фрагменты вставки сущности хорошо подходят для макросов.

Этот сокращенный фрагмент сгенерированного репозитория показывает раскрытие макроса:

```java
private static final QueryContext QUERY_CONTEXT_2 = new QueryContext(
  "INSERT INTO tasks(title, status, description, user_assignee_id) VALUES (:entity.title, :entity.status, :entity.description, :entity.userAssigneeId) RETURNING id",
  "INSERT INTO tasks(title, status, description, user_assignee_id) VALUES (?, ?, ?, ?) RETURNING id",
  "TaskRepository.insert"
);
```

Он также показывает, как именно Kora реализует пакетную вставку и сгенерированные ключи:

```java
try (_conToClose; var _stmt = _conToUse.prepareStatement(_query.sql(), Statement.RETURN_GENERATED_KEYS)) {
  for (var _i : entity) {
    _stmt.setString(1, _i.title());
    _parameter_mapper_2.set(_stmt, 2, _i.status());
    if (_i.description() != null) {
      _stmt.setString(3, _i.description());
    } else {
      _stmt.setNull(3, Types.VARCHAR);
    }
    if (_i.userAssigneeId() != null) {
      _stmt.setLong(4, _i.userAssigneeId());
    } else {
      _stmt.setNull(4, Types.BIGINT);
    }
    _stmt.addBatch();
  }
  var _batchResult = _stmt.executeBatch();
  try (var _rs = _stmt.getGeneratedKeys()) {
    var _result = _result_mapper_1.apply(_rs);
    return Objects.requireNonNull(_result, "Result mapping is expected non-null, but was null");
  }
}
```

Эта контрольная точка со сгенерированным кодом делает поведение фреймворка проверяемым: привязка `null`, использование преобразователя enum, пакетное выполнение, извлечение сгенерированных ключей и работа с
соединением видны напрямую.

## Новая проекция { #new-projection }

Пока `TaskDAO` является моделью вставки. В ней нет `id`, `created_at`, `updated_at` или данных исполнителя. Это хорошо для записи, но недостаточно для запроса "найти задачи, назначенные этим
пользователям".

Для такого запроса форма результата отличается от `TaskDAO`. У вас есть два распространенных варианта.

### Вариант 1: отдельная проекция { #option-1-separate-projection }

Вы могли бы создать полностью отдельный `TaskSelectDAO` и продублировать каждое выбранное поле:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @EntityJdbc
    public record TaskSelectDAO(
            @Column("task_id") Long id,
            @Column("title") String title,
            @Column("status") TaskStatus status,
            @Nullable @Column("description") String description,
            @Nullable @Column("user_assignee_id") Long userAssigneeId,
            @Column("updated_at") LocalDateTime updatedAt,
            @Column("assignee_id") Long assigneeId,
            @Column("assignee_name") String assigneeName,
            @Column("assignee_email") String assigneeEmail) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @EntityJdbc
    data class TaskSelectDAO(
        @field:Column("task_id") val id: Long,
        @field:Column("title") val title: String,
        @field:Column("status") val status: TaskStatus,
        @field:Column("description") val description: String?,
        @field:Column("user_assignee_id") val userAssigneeId: Long?,
        @field:Column("updated_at") val updatedAt: LocalDateTime,
        @field:Column("assignee_id") val assigneeId: Long,
        @field:Column("assignee_name") val assigneeName: String,
        @field:Column("assignee_email") val assigneeEmail: String
    )
    ```

Иногда это полезно, когда результат запроса действительно независим. Минус — дублирование: поля задачи уже существуют в `TaskDAO`, а поля пользователя уже существуют в `UserDAO`.

### Вариант 2: через `@Embedded` { #option-2-through-embedded }

Подробнее о префиксах, SQL-алиасах и вложенных полях смотрите в разделе [`@Embedded` и вложенных полей](../documentation/database-common.md#embedded-fields).

В этом руководстве используйте вложенную проекцию внутри `TaskDAO`. Она переиспользует `TaskDAO` для полей задачи и `UserDAO` из базового JDBC-руководства для полей исполнителя.

===! ":fontawesome-brands-java: `Java`"

    Обновите `TaskDAO.java`:

    ```java
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.repository;

    import jakarta.annotation.Nullable;
    import java.time.LocalDateTime;
    import ru.tinkoff.kora.database.common.annotation.Column;
    import ru.tinkoff.kora.database.common.annotation.Embedded;
    import ru.tinkoff.kora.database.common.annotation.Id;
    import ru.tinkoff.kora.database.common.annotation.Table;
    import ru.tinkoff.kora.database.jdbc.EntityJdbc;
    import ru.tinkoff.kora.guide.databasejdbc.advanced.repository.UserDAO;
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskStatus;

    @EntityJdbc
    @Table("tasks")
    public record TaskDAO(
            @Column("title") String title,
            @Column("status") TaskStatus status,
            @Column("description") @Nullable String description,
            @Column("user_assignee_id") @Nullable Long userAssigneeId) {

        @EntityJdbc
        public record SelectAssigned(
                @Column("task_id") @Id Long id,
                @Column("created_at") LocalDateTime createdAt,
                @Column("updated_at") LocalDateTime updatedAt,
                @Embedded("assignee_") UserDAO assigned,
                @Embedded TaskDAO base) {}
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите `TaskDAO.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.repository

    import java.time.LocalDateTime
    import ru.tinkoff.kora.database.common.annotation.Column
    import ru.tinkoff.kora.database.common.annotation.Embedded
    import ru.tinkoff.kora.database.common.annotation.Id
    import ru.tinkoff.kora.database.common.annotation.Table
    import ru.tinkoff.kora.database.jdbc.EntityJdbc
    import ru.tinkoff.kora.guide.databasejdbc.advanced.repository.UserDAO
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskStatus

    @EntityJdbc
    @Table("tasks")
    data class TaskDAO(
        @field:Column("title") val title: String,
        @field:Column("status") val status: TaskStatus,
        @field:Column("description") val description: String?,
        @field:Column("user_assignee_id") val userAssigneeId: Long?
    ) {
        @EntityJdbc
        data class SelectAssigned(
            @field:Column("task_id") @field:Id val id: Long,
            @field:Column("created_at") val createdAt: LocalDateTime,
            @field:Column("updated_at") val updatedAt: LocalDateTime,
            @field:Embedded("assignee_") val assigned: UserDAO,
            @field:Embedded val base: TaskDAO
        )
    }
    ```

Такая форма компактна, но выразительна:

- `base` переиспользует поля модели вставки: `title`, `status`, `description`, `user_assignee_id`.
- `assigned` переиспользует существующий `UserDAO`.
- `@Embedded("assignee_")` сопоставляет SQL-алиасы вроде `assignee_id` с полями `UserDAO`, аннотированными как `id`, `name`, `email` и `created_at`.
- репозиторий все еще может возвращать `List<TaskDAO.SelectAssigned>` из того же `TaskRepository`.

Это важный шаблон Kora: репозиторий не привязан к одной модели результата. Используйте ту проекцию, которая соответствует запросу. Можно компоновать проекции, переиспользовать существующие части DAO и
выбирать только поля, нужные конечной точке. Это избегает загрузки ненужных столбцов и избавляет от создания отдельного репозитория для каждого представления данных, что часто возникает в репозиторных
шаблонах фреймворков вроде Spring или Micronaut.

Теперь добавьте запрос проекции в тот же репозиторий:

===! ":fontawesome-brands-java: `Java`"

    Обновите `TaskRepository.java`:

    ```java
    @Query("""
            SELECT
              t.id AS task_id,
              t.created_at,
              t.updated_at,
              u.id AS assignee_id,
              u.name AS assignee_name,
              u.email AS assignee_email,
              u.created_at AS assignee_created_at,
              t.title,
              t.status,
              t.description,
              t.user_assignee_id
            FROM tasks t
            JOIN users u ON u.id = t.user_assignee_id
            WHERE t.user_assignee_id = ANY(:assigneeIds)
            ORDER BY t.id
            """)
    List<TaskDAO.SelectAssigned> findAssignedByAssigneeIds(List<Long> assigneeIds);
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите `TaskRepository.kt`:

    ```kotlin
    @Query(
        """
        SELECT
          t.id AS task_id,
          t.created_at,
          t.updated_at,
          u.id AS assignee_id,
          u.name AS assignee_name,
          u.email AS assignee_email,
          u.created_at AS assignee_created_at,
          t.title,
          t.status,
          t.description,
          t.user_assignee_id
        FROM tasks t
        JOIN users u ON u.id = t.user_assignee_id
        WHERE t.user_assignee_id = ANY(:assigneeIds)
        ORDER BY t.id
        """
    )
    fun findAssignedByAssigneeIds(assigneeIds: List<Long>): List<TaskDAO.SelectAssigned>
    ```

Запрос выбирает только столбцы, нужные для сборки ответа назначенной задачи. Он не загружает все поля пользователя, если они не нужны ответу, и не делает вид, что `TaskDAO` владеет ленивым
пользовательским объектом. SQL остается честным, а проекция остается типизированной.

После компиляции Kora генерирует row mapper для этой проекции:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-database-jdbc-advanced-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/databasejdbc/advanced/task/repository/$TaskDAO_SelectAssigned_JdbcRowMapper.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-database-jdbc-advanced-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/advanced/task/repository/$TaskDAO_SelectAssigned_JdbcRowMapper.kt
    ```

Сгенерированный преобразователь показывает, как Kora применяет префикс, читает столбцы с алиасами, применяет преобразователь enum, обрабатывает nullable-поля и собирает вложенные объекты:

??? example "Сгенерированный JDBC-преобразователь"

    ===! ":fontawesome-brands-java: `Java`"

        ```java
        var _assigned_idColumn = _rs.findColumn("assignee_id");
        var _assigned_nameColumn = _rs.findColumn("assignee_name");
        var _assigned_emailColumn = _rs.findColumn("assignee_email");
        var _assigned_createdAtColumn = _rs.findColumn("assignee_created_at");
        var _base_titleColumn = _rs.findColumn("title");
        var _base_statusColumn = _rs.findColumn("status");
        var _base_descriptionColumn = _rs.findColumn("description");
        var _base_userAssigneeIdColumn = _rs.findColumn("user_assignee_id");

        Long id = _rs.getLong(_idColumn);
        if (_rs.wasNull()) {
          throw new NullPointerException("Result field id is not nullable but row task_id has null");
        }
        LocalDateTime createdAt = _rs.getObject(_createdAtColumn, LocalDateTime.class);
        if (_rs.wasNull()) {
          throw new NullPointerException("Result field createdAt is not nullable but row created_at has null");
        }
        LocalDateTime updatedAt = _rs.getObject(_updatedAtColumn, LocalDateTime.class);
        if (_rs.wasNull()) {
          throw new NullPointerException("Result field updatedAt is not nullable but row updated_at has null");
        }
        Long assigned_id = _rs.getLong(_assigned_idColumn);
        if (_rs.wasNull()) {
          throw new NullPointerException("Result field assigned_id is not nullable but row assignee_id has null");
        }
        String assigned_name = _rs.getString(_assigned_nameColumn);
        if (_rs.wasNull()) {
          throw new NullPointerException("Result field assigned_name is not nullable but row assignee_name has null");
        }
        String assigned_email = _rs.getString(_assigned_emailColumn);
        if (_rs.wasNull()) {
          throw new NullPointerException("Result field assigned_email is not nullable but row assignee_email has null");
        }
        LocalDateTime assigned_createdAt = _rs.getObject(_assigned_createdAtColumn, LocalDateTime.class);
        if (_rs.wasNull()) {
          throw new NullPointerException("Result field assigned_createdAt is not nullable but row assignee_created_at has null");
        }
        String base_title = _rs.getString(_base_titleColumn);
        if (_rs.wasNull()) {
          throw new NullPointerException("Result field base_title is not nullable but row title has null");
        }
        TaskStatus base_status = this._base_statusMapper.apply(_rs, _base_statusColumn);
        if (_rs.wasNull()) {
          throw new NullPointerException("Result field base_status is not nullable but row status has null");
        }
        String base_description = _rs.getString(_base_descriptionColumn);
        if (_rs.wasNull()) {
          base_description = null;
        }
        Long base_userAssigneeId = _rs.getLong(_base_userAssigneeIdColumn);
        if (_rs.wasNull()) {
          base_userAssigneeId = null;
        }

        UserDAO assigned = new UserDAO(assigned_id, assigned_name, assigned_email, assigned_createdAt);
        TaskDAO base = new TaskDAO(base_title, base_status, base_description, base_userAssigneeId);
        var _result = new TaskDAO.SelectAssigned(id, createdAt, updatedAt, assigned, base);
        ```

    === ":simple-kotlin: `Kotlin`"

        ```kotlin
        val _idx_assigned_id = _rs.findColumn("assignee_id")
        val _idx_assigned_name = _rs.findColumn("assignee_name")
        val _idx_assigned_email = _rs.findColumn("assignee_email")
        val _idx_assigned_createdAt = _rs.findColumn("assignee_created_at")
        val _idx_base_title = _rs.findColumn("title")
        val _idx_base_status = _rs.findColumn("status")
        val _idx_base_description = _rs.findColumn("description")
        val _idx_base_userAssigneeId = _rs.findColumn("user_assignee_id")

        var id: Long? = _rs.getLong(_idx_id)
        if (_rs.wasNull() || id == null) {
          throw NullPointerException("Required field task_id is not nullable but row has null")
        }
        var createdAt: LocalDateTime? = _rs.getObject(_idx_createdAt, LocalDateTime::class.java)
        if (_rs.wasNull() || createdAt == null) {
          throw NullPointerException("Required field created_at is not nullable but row has null")
        }
        var updatedAt: LocalDateTime? = _rs.getObject(_idx_updatedAt, LocalDateTime::class.java)
        if (_rs.wasNull() || updatedAt == null) {
          throw NullPointerException("Required field updated_at is not nullable but row has null")
        }
        var assigned_id: Long? = _rs.getLong(_idx_assigned_id)
        if (_rs.wasNull() || assigned_id == null) {
          throw NullPointerException("Required field assignee_id is not nullable but row has null")
        }
        var assigned_name: String? = _rs.getString(_idx_assigned_name)
        if (_rs.wasNull() || assigned_name == null) {
          throw NullPointerException("Required field assignee_name is not nullable but row has null")
        }
        var assigned_email: String? = _rs.getString(_idx_assigned_email)
        if (_rs.wasNull() || assigned_email == null) {
          throw NullPointerException("Required field assignee_email is not nullable but row has null")
        }
        var assigned_createdAt: LocalDateTime? = _rs.getObject(_idx_assigned_createdAt, LocalDateTime::class.java)
        if (_rs.wasNull() || assigned_createdAt == null) {
          throw NullPointerException("Required field assignee_created_at is not nullable but row has null")
        }
        var base_title: String? = _rs.getString(_idx_base_title)
        if (_rs.wasNull() || base_title == null) {
          throw NullPointerException("Required field title is not nullable but row has null")
        }
        var base_status: TaskStatus? = `$base_statusMapper`.apply(_rs, _idx_base_status)
        if (_rs.wasNull() || base_status == null) {
          throw NullPointerException("Required field status is not nullable but row has null")
        }
        var base_description: String? = _rs.getString(_idx_base_description)
        if (_rs.wasNull() || base_description == null) {
          base_description = null
        }
        var base_userAssigneeId: Long? = _rs.getLong(_idx_base_userAssigneeId)
        if (_rs.wasNull() || base_userAssigneeId == null) {
          base_userAssigneeId = null
        }

        val assigned = UserDAO(assigned_id, assigned_name, assigned_email, assigned_createdAt)
        val base = TaskDAO(base_title, base_status, base_description, base_userAssigneeId)
        val _result = TaskDAO.SelectAssigned(id, createdAt, updatedAt, assigned, base)
        ```


Эта контрольная точка со сгенерированным кодом полезна и людям, и ИИ-помощникам. Она показывает точное сопоставление, которое Kora скомпилировала из ваших аннотаций, поэтому отладка сводится к
просмотру конкретного кода, а не к догадкам о поведении фреймворка.

## Новый DTO { #new-dto }

Проекция базы данных — это не HTTP-ответ. DTO являются границей API. Они могут скрывать детали, относящиеся только к базе данных, группировать значения для клиентов и отделять HTTP JSON-преобразование от
JDBC-преобразования строк.

`TaskStatus` уже существует, потому что его используют JDBC-модель и преобразователи. Теперь добавьте модели запросов и ответов, которые определяют HTTP JSON-контракт.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/ru/tinkoff/kora/guide/databasejdbc/advanced/task/dto/TaskRequest.java`:

    ```java
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto;

    import jakarta.annotation.Nullable;
    import java.util.List;
    import ru.tinkoff.kora.json.common.annotation.Json;

    @Json
    public record TaskRequest(List<TaskCreate> tasks) {

        @Json
        public record TaskCreate(
                String title,
                @Nullable String description,
                @Nullable Long userAssigneeId) {}
    }
    ```

    Создайте `src/main/java/ru/tinkoff/kora/guide/databasejdbc/advanced/task/dto/TaskResponse.java`:

    ```java
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto;

    import jakarta.annotation.Nullable;
    import java.time.LocalDateTime;
    import java.util.List;
    import ru.tinkoff.kora.guide.databasejdbc.advanced.dto.UserRequest;
    import ru.tinkoff.kora.json.common.annotation.Json;

    @Json
    public record TaskResponse(List<TaskCreated> tasks) {

        @Json
        public record TaskCreated(
                Long id,
                String title,
                @Nullable String description,
                TaskStatus status,
                @Nullable Long userAssigneeId,
                LocalDateTime updatedAt) {}

        @Json
        public record TaskAssigned(
                Long id,
                String title,
                @Nullable String description,
                TaskStatus status,
                UserRequest assignee,
                LocalDateTime updatedAt) {}
    }
    ```

    Создайте `src/main/java/ru/tinkoff/kora/guide/databasejdbc/advanced/task/dto/TaskStatusRequest.java`:

    ```java
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto;

    import ru.tinkoff.kora.json.common.annotation.Json;

    @Json
    public record TaskStatusRequest(TaskStatus status) {}
    ```

    Создайте `src/main/java/ru/tinkoff/kora/guide/databasejdbc/advanced/task/dto/MessageResponse.java`:

    ```java
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto;

    import ru.tinkoff.kora.json.common.annotation.Json;

    @Json
    public record MessageResponse(String message) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/advanced/task/dto/TaskRequest.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto

    import ru.tinkoff.kora.json.common.annotation.Json

    @Json
    data class TaskRequest(
        val tasks: List<TaskCreate>
    ) {
        @Json
        data class TaskCreate(
            val title: String,
            val description: String?,
            val userAssigneeId: Long?
        )
    }
    ```

    Создайте `src/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/advanced/task/dto/TaskResponse.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto

    import java.time.LocalDateTime
    import ru.tinkoff.kora.guide.databasejdbc.advanced.dto.UserRequest
    import ru.tinkoff.kora.json.common.annotation.Json

    @Json
    data class TaskResponse(
        val tasks: List<TaskCreated>
    ) {
        @Json
        data class TaskCreated(
            val id: Long,
            val title: String,
            val description: String?,
            val status: TaskStatus,
            val userAssigneeId: Long?,
            val updatedAt: LocalDateTime
        )

        @Json
        data class TaskAssigned(
            val id: Long,
            val title: String,
            val description: String?,
            val status: TaskStatus,
            val assignee: UserRequest,
            val updatedAt: LocalDateTime
        )
    }
    ```

    Создайте `src/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/advanced/task/dto/TaskStatusRequest.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto

    import ru.tinkoff.kora.json.common.annotation.Json

    @Json
    data class TaskStatusRequest(
        val status: TaskStatus
    )
    ```

    Создайте `src/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/advanced/task/dto/MessageResponse.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto

    import ru.tinkoff.kora.json.common.annotation.Json

    @Json
    data class MessageResponse(
        val message: String
    )
    ```

`@Json` говорит Kora сгенерировать JSON-читатели/писатели во время обработки аннотаций. `Nullable`-поля отражают необязательные значения API: описание задачи может отсутствовать, а задача может быть
создана без исполнителя.

## Транзакция { #transaction }

Подробнее о том, как `inTx(...)` открывает границу транзакции и переиспользует одно соединение, смотрите в разделе [JDBC-транзакций](../documentation/database-jdbc.md#transaction).

Сервис владеет прикладным поведением. Он решает, что задачи с исполнителями должны ссылаться на существующих пользователей, и решает, что проверка и вставка должны выполняться атомарно.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/ru/tinkoff/kora/guide/databasejdbc/advanced/task/service/TaskService.java`:

    ```java
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.service;

    import java.time.LocalDateTime;
    import java.util.ArrayList;
    import java.util.List;
    import java.util.Objects;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.databasejdbc.advanced.dto.UserRequest;
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskRequest;
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskResponse;
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskStatus;
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.repository.TaskDAO;
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.repository.TaskRepository;
    import ru.tinkoff.kora.http.server.common.HttpServerResponseException;

    @Component
    public final class TaskService {

        private final TaskRepository taskRepository;

        public TaskService(TaskRepository taskRepository) {
            this.taskRepository = taskRepository;
        }

        public List<TaskResponse.TaskCreated> createTasks(List<TaskRequest.TaskCreate> taskCreates) {
            return taskRepository.getJdbcConnectionFactory().inTx(() -> {
                var assigneeIds = taskCreates.stream()
                        .map(TaskRequest.TaskCreate::userAssigneeId)
                        .filter(Objects::nonNull)
                        .distinct()
                        .toList();

                if (!assigneeIds.isEmpty()) {
                    var existingAssigneeIds = taskRepository.findExistingAssigneeId(assigneeIds);
                    if (existingAssigneeIds.size() != assigneeIds.size()) {
                        var nonExistingAssigneeIds = assigneeIds.stream()
                                .filter(aid -> !existingAssigneeIds.contains(aid))
                                .toList();
                        throw HttpServerResponseException.of(404, "Assignee users not found: " + nonExistingAssigneeIds);
                    }
                }

                var tasks = taskCreates.stream()
                        .map(t -> new TaskDAO(t.title(), TaskStatus.TODO, t.description(), t.userAssigneeId()))
                        .toList();
                var taskIds = taskRepository.insert(tasks);

                List<TaskResponse.TaskCreated> taskCreateds = new ArrayList<>();
                for (int i = 0; i < taskIds.size(); i++) {
                    var taskId = taskIds.get(i);
                    var task = tasks.get(i);
                    taskCreateds.add(new TaskResponse.TaskCreated(
                            taskId,
                            task.title(),
                            task.description(),
                            TaskStatus.TODO,
                            task.userAssigneeId(),
                            LocalDateTime.now()));
                }

                return taskCreateds;
            });
        }

        public List<TaskResponse.TaskAssigned> getTasksByAssignees(List<Long> ids) {
            return taskRepository.findAssignedByAssigneeIds(ids).stream()
                    .map(this::toResponseAssigned)
                    .toList();
        }

        public void updateStatus(long id, TaskStatus status) {
            var updated = taskRepository.updateStatus(id, status);
            if (updated.value() < 1) {
                throw HttpServerResponseException.of(404, "Task not found");
            }
        }

        public void assignTask(long taskId, Long userId) {
            taskRepository.getJdbcConnectionFactory().inTx(() -> {
                var updated = taskRepository.updateAssignee(taskId, userId);
                if (updated.value() < 1) {
                    throw HttpServerResponseException.of(404, "Task not found");
                }
            });
        }

        public void unassignTask(long taskId) {
            var updated = taskRepository.updateAssignee(taskId, null);
            if (updated.value() < 1) {
                throw HttpServerResponseException.of(404, "Task not found");
            }
        }

        private TaskResponse.TaskAssigned toResponseAssigned(TaskDAO.SelectAssigned task) {
            return new TaskResponse.TaskAssigned(
                    task.id(),
                    task.base().title(),
                    task.base().description(),
                    task.base().status(),
                    new UserRequest(task.assigned().name(), task.assigned().email()),
                    task.updatedAt());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/advanced/task/service/TaskService.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.service

    import java.time.LocalDateTime
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.database.jdbc.JdbcHelper.SqlFunction1
    import ru.tinkoff.kora.guide.databasejdbc.advanced.dto.UserRequest
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskRequest
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskResponse
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskStatus
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.repository.TaskDAO
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.repository.TaskRepository
    import ru.tinkoff.kora.http.server.common.HttpServerResponseException

    @Component
    class TaskService(
        private val taskRepository: TaskRepository
    ) {

        fun createTasks(taskCreates: List<TaskRequest.TaskCreate>): List<TaskResponse.TaskCreated> {
            return taskRepository.jdbcConnectionFactory.inTx(SqlFunction1 {
                val assigneeIds = taskCreates
                    .mapNotNull { it.userAssigneeId }
                    .distinct()

                if (assigneeIds.isNotEmpty()) {
                    val existingAssigneeIds = taskRepository.findExistingAssigneeId(assigneeIds)
                    if (existingAssigneeIds.size != assigneeIds.size) {
                        val nonExistingAssigneeIds = assigneeIds.filter { it !in existingAssigneeIds }
                        throw HttpServerResponseException.of(404, "Assignee users not found: $nonExistingAssigneeIds")
                    }
                }

                val tasks = taskCreates.map {
                    TaskDAO(it.title, TaskStatus.TODO, it.description, it.userAssigneeId)
                }
                val taskIds = taskRepository.insert(tasks)

                taskIds.mapIndexed { index, taskId ->
                    val task = tasks[index]
                    TaskResponse.TaskCreated(
                        taskId,
                        task.title,
                        task.description,
                        TaskStatus.TODO,
                        task.userAssigneeId,
                        LocalDateTime.now()
                    )
                }
            })
        }

        fun getTasksByAssignees(ids: List<Long>): List<TaskResponse.TaskAssigned> {
            return taskRepository.findAssignedByAssigneeIds(ids)
                .map(::toResponseAssigned)
        }

        fun updateStatus(id: Long, status: TaskStatus) {
            val updated = taskRepository.updateStatus(id, status)
            if (updated.value() < 1) {
                throw HttpServerResponseException.of(404, "Task not found")
            }
        }

        fun assignTask(taskId: Long, userId: Long) {
            taskRepository.jdbcConnectionFactory.inTx(SqlFunction1 {
                val updated = taskRepository.updateAssignee(taskId, userId)
                if (updated.value() < 1) {
                    throw HttpServerResponseException.of(404, "Task not found")
                }
            })
        }

        fun unassignTask(taskId: Long) {
            val updated = taskRepository.updateAssignee(taskId, null)
            if (updated.value() < 1) {
                throw HttpServerResponseException.of(404, "Task not found")
            }
        }

        private fun toResponseAssigned(task: TaskDAO.SelectAssigned): TaskResponse.TaskAssigned {
            return TaskResponse.TaskAssigned(
                task.id,
                task.base.title,
                task.base.description,
                task.base.status,
                UserRequest(task.assigned.name, task.assigned.email),
                task.updatedAt
            )
        }
    }
    ```

`createTasks(...)` — главный продвинутый метод сервиса. Он держит проверку и пакетную вставку в одной транзакции. Он также показывает, почему репозитории раскрывают методы в форме базы данных, а
сервисы раскрывают поведение в форме приложения.

У метода есть одно важное правило согласованности: либо создаются все запрошенные задачи, либо не создается ни одна. Это правило важно, потому что запрос пакетный. Если первая задача содержит
корректного исполнителя, вторая — отсутствующего исполнителя, а третья вообще без исполнителя, сохранение только части запроса оставило бы клиента API с неожиданным частичным результатом.

`taskRepository.getJdbcConnectionFactory().inTx(...)` открывает JDBC-транзакцию вокруг лямбды. Каждый метод репозитория, вызванный внутри этой лямбды, использует одно и то же транзакционное
соединение:

1. `findExistingAssigneeId(assigneeIds)` проверяет уникальные non-`null` идентификаторы исполнителей.
2. Если какие-то исполнители отсутствуют, сервис выбрасывает `HttpServerResponseException`.
3. `insert(tasks)` вызывается только после успешной проверки.
4. DTO ответа собираются из сгенерированных идентификаторов и исходных значений задач.

Если лямбда завершается нормально и возвращает созданные DTO, Kora фиксирует транзакцию. Проверка исполнителей и пакетная вставка становятся видимыми вместе.

Если лямбда выбрасывает исключение, Kora откатывает транзакцию. Это касается и явного `HttpServerResponseException` для отсутствующих исполнителей, и ошибок базы данных из `insert(...)`, например
нарушений ограничений или сбоев соединения. Откат означает, что ни одна строка задачи из этого запроса не будет зафиксирована. Клиент получает ошибку, а база данных остается в том же логическом
состоянии, в котором была до запуска `createTasks(...)`.

Транзакция намеренно размещена в сервисе, а не в репозитории. Репозиторий знает, как выполнять отдельные SQL-операции. Сервис знает, что "проверить всех исполнителей и вставить все задачи" — это одна
бизнес-операция и, следовательно, одна граница транзакции.

`UpdateCount` используется для операций обновления, потому что SQL-обновления могут затронуть ноль строк. Сервис превращает этот факт базы данных в HTTP-facing `404`.

## Новый контроллер { #new-controller }

Контроллер остается тонким. Он сопоставляет HTTP-маршруты с методами сервиса, управляет кодами состояния и возвращает JSON DTO. В нем нет SQL или правил транзакций.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/ru/tinkoff/kora/guide/databasejdbc/advanced/task/controller/TaskController.java`:

    ```java
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.controller;

    import jakarta.annotation.Nullable;
    import java.util.List;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.MessageResponse;
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskRequest;
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskResponse;
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskStatusRequest;
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.service.TaskService;
    import ru.tinkoff.kora.http.common.HttpMethod;
    import ru.tinkoff.kora.http.common.HttpResponseEntity;
    import ru.tinkoff.kora.http.common.annotation.HttpRoute;
    import ru.tinkoff.kora.http.common.annotation.Path;
    import ru.tinkoff.kora.http.common.annotation.Query;
    import ru.tinkoff.kora.http.common.header.HttpHeaders;
    import ru.tinkoff.kora.http.server.common.annotation.HttpController;
    import ru.tinkoff.kora.json.common.annotation.Json;

    @Component
    @HttpController
    public final class TaskController {

        private final TaskService taskService;

        public TaskController(TaskService taskService) {
            this.taskService = taskService;
        }

        @HttpRoute(method = HttpMethod.GET, path = "/tasks/assigned")
        @Json
        public List<TaskResponse.TaskAssigned> getTasksByAssignees(@Nullable @Query("ids") List<Long> ids) {
            return taskService.getTasksByAssignees(ids);
        }

        @HttpRoute(method = HttpMethod.POST, path = "/tasks")
        @Json
        public HttpResponseEntity<TaskResponse> createTask(@Json TaskRequest request) {
            var tasks = taskService.createTasks(request.tasks());
            return HttpResponseEntity.of(201, HttpHeaders.of(), new TaskResponse(tasks));
        }

        @HttpRoute(method = HttpMethod.PUT, path = "/tasks/{taskId}/status")
        @Json
        public MessageResponse updateStatus(@Path Long taskId, @Json TaskStatusRequest request) {
            taskService.updateStatus(taskId, request.status());
            return new MessageResponse("OK");
        }

        @HttpRoute(method = HttpMethod.PUT, path = "/tasks/{taskId}/assignee/{userId}")
        @Json
        public MessageResponse assignTask(@Path Long taskId, @Path Long userId) {
            taskService.assignTask(taskId, userId);
            return new MessageResponse("OK");
        }

        @HttpRoute(method = HttpMethod.DELETE, path = "/tasks/{taskId}/assignee")
        @Json
        public MessageResponse unassignTask(@Path Long taskId) {
            taskService.unassignTask(taskId);
            return new MessageResponse("OK");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/advanced/task/controller/TaskController.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasejdbc.advanced.task.controller

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.MessageResponse
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskRequest
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskResponse
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.dto.TaskStatusRequest
    import ru.tinkoff.kora.guide.databasejdbc.advanced.task.service.TaskService
    import ru.tinkoff.kora.http.common.HttpMethod
    import ru.tinkoff.kora.http.common.HttpResponseEntity
    import ru.tinkoff.kora.http.common.annotation.HttpRoute
    import ru.tinkoff.kora.http.common.annotation.Path
    import ru.tinkoff.kora.http.common.annotation.Query
    import ru.tinkoff.kora.http.common.header.HttpHeaders
    import ru.tinkoff.kora.http.server.common.annotation.HttpController
    import ru.tinkoff.kora.json.common.annotation.Json

    @Component
    @HttpController
    class TaskController(
        private val taskService: TaskService
    ) {

        @HttpRoute(method = HttpMethod.GET, path = "/tasks/assigned")
        @Json
        fun getTasksByAssignees(@Query("ids") ids: List<Long>?): List<TaskResponse.TaskAssigned> {
            return taskService.getTasksByAssignees(ids ?: emptyList())
        }

        @HttpRoute(method = HttpMethod.POST, path = "/tasks")
        @Json
        fun createTask(@Json request: TaskRequest): HttpResponseEntity<TaskResponse> {
            val tasks = taskService.createTasks(request.tasks)
            return HttpResponseEntity.of(201, HttpHeaders.of(), TaskResponse(tasks))
        }

        @HttpRoute(method = HttpMethod.PUT, path = "/tasks/{taskId}/status")
        @Json
        fun updateStatus(@Path taskId: Long, @Json request: TaskStatusRequest): MessageResponse {
            taskService.updateStatus(taskId, request.status)
            return MessageResponse("OK")
        }

        @HttpRoute(method = HttpMethod.PUT, path = "/tasks/{taskId}/assignee/{userId}")
        @Json
        fun assignTask(@Path taskId: Long, @Path userId: Long): MessageResponse {
            taskService.assignTask(taskId, userId)
            return MessageResponse("OK")
        }

        @HttpRoute(method = HttpMethod.DELETE, path = "/tasks/{taskId}/assignee")
        @Json
        fun unassignTask(@Path taskId: Long): MessageResponse {
            taskService.unassignTask(taskId)
            return MessageResponse("OK")
        }
    }
    ```

Контроллер намеренно раскрывает только операции, нужные для продвинутого урока JDBC: создать несколько задач, запросить назначенные задачи по идентификаторам исполнителей, изменить состояние задачи,
назначить задачу и снять назначение.

## Конфигурация { #configuration }

Создайте `src/main/resources/application.conf`:

Полное описание настроек смотрите в разделах [База данных JDBC](../documentation/database-jdbc.md) и [Миграции базы данных](../documentation/database-migration.md).

===! ":material-code-json: `Hocon`"

    ```javascript
    db {
      jdbcUrl = ${POSTGRES_JDBC_URL} //(1)!
      username = ${POSTGRES_USER} //(2)!
      password = ${POSTGRES_PASS} //(3)!
      maxPoolSize = 10 //(4)!
      poolName = "guide-jdbc-advanced" //(5)!
    }

    flyway {
      locations = "db/migration" //(6)!
    }
    ```

    1. URL JDBC-соединения. Необязательное переопределение через `POSTGRES_JDBC_URL`.
    2. Имя пользователя базы данных. Необязательное переопределение через `POSTGRES_USER`.
    3. Пароль пользователя базы данных. Необязательное переопределение через `POSTGRES_PASS`.
    4. Максимальное число соединений в пуле.
    5. Человекочитаемое имя пула соединений, используемое в диагностике.
    6. Расположения миграций, которые просматривает Flyway.

=== ":simple-yaml: `YAML`"

    ```yaml
    db:
      jdbcUrl: ${POSTGRES_JDBC_URL} #(1)!
      username: ${POSTGRES_USER} #(2)!
      password: ${POSTGRES_PASS} #(3)!
      maxPoolSize: 10 #(4)!
      poolName: "guide-jdbc-advanced" #(5)!
    flyway:
      locations: "db/migration" #(6)!
    ```

    1. URL JDBC-соединения. Необязательное переопределение через `POSTGRES_JDBC_URL`.
    2. Имя пользователя базы данных. Необязательное переопределение через `POSTGRES_USER`.
    3. Пароль пользователя базы данных. Необязательное переопределение через `POSTGRES_PASS`.
    4. Максимальное число соединений в пуле.
    5. Человекочитаемое имя пула соединений, используемое в диагностике.
    6. Расположения миграций, которые просматривает Flyway.

## Настройка базы данных { #database-setup }

Приложению нужна та же база данных PostgreSQL из базового JDBC-руководства. Вы можете переиспользовать эту базу или запустить локальную через Docker Compose.

Создайте `docker-compose.yml` в директории модуля приложения:

```yaml
services:
  postgres:
    image: postgres:17.6-alpine
    environment:
      POSTGRES_DB: postgres
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
```

Запустите PostgreSQL:

```bash
docker compose up -d
```

Это запускает PostgreSQL с параметрами:

- база данных: `postgres`
- имя пользователя: `postgres`
- пароль: `postgres`
- порт: `5432`

### Схема базы данных { #db-schema }

Базовое JDBC-руководство уже создало `V1__init_users.sql`. Это руководство добавляет `V2__init_tasks.sql`, поэтому итоговый набор миграций содержит обе таблицы:

```text
src/main/resources/db/migration/
  V1__init_users.sql
  V2__init_tasks.sql
```

Столбец `tasks.user_assignee_id` ссылается на `users.id` и остается nullable:

```sql
user_assignee_id BIGINT NULL REFERENCES users(id) ON DELETE SET NULL
```

Это соответствует поведению сервиса: задачу можно создать без исполнителя, назначить позже или снова снять назначение. Индексы по `user_assignee_id` и `status` поддерживают пути чтения и обновления,
используемые в руководстве.

## Запуск приложения { #run-app }

Запустите приложение со значениями соединения с базой данных:

```bash
POSTGRES_JDBC_URL=jdbc:postgresql://localhost:5432/postgres \
POSTGRES_USER=postgres \
POSTGRES_PASS=postgres \
./gradlew :guides-apps:guide-database-jdbc-advanced-app:run
```

В Windows PowerShell:

```powershell
$env:POSTGRES_JDBC_URL="jdbc:postgresql://localhost:5432/postgres"
$env:POSTGRES_USER="postgres"
$env:POSTGRES_PASS="postgres"
.\gradlew.bat :guides-apps:guide-database-jdbc-advanced-app:run
```

Во время запуска Kora строит граф приложения, инициализирует JDBC-пул, запускает Flyway, а затем поднимает HTTP-сервер на порту `8080`.

## Запуск с Docker { #run-docker }

Соберите дистрибутив приложения и Docker-образ:

```bash
./gradlew :guides-apps:guide-database-jdbc-advanced-app:distTar
docker build -t guide-database-jdbc-advanced-app guides/guide-database-jdbc-advanced-app
```

Запустите контейнер против PostgreSQL, запущенного через Docker Compose:

```bash
docker run --rm \
  --name guide-database-jdbc-advanced-app \
  --network kora-guide_default \
  -p 8080:8080 \
  -p 8085:8085 \
  -e POSTGRES_JDBC_URL=jdbc:postgresql://postgres:5432/postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASS=postgres \
  guide-database-jdbc-advanced-app
```

Если ваш Compose-проект использует другое имя сети, проверьте его командой:

```bash
docker network ls
```

Dockerfile приложения запускает точку входа Gradle-дистрибутива:

```dockerfile
CMD ["/opt/app/application/bin/application"]
```

Это имя берется из `applicationName = "application"` в `build.gradle`.

## Проверка приложения { #check-app }

Миграция добавляет двух пользователей:

- `1` / `John Doe`
- `2` / `Jane Smith`

Создайте несколько задач одним запросом:

```bash
curl -X POST http://localhost:8080/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "tasks": [
      {
        "title": "Prepare database guide",
        "description": "Explain transactions and projections",
        "userAssigneeId": 1
      },
      {
        "title": "Review generated JDBC mapper",
        "description": null,
        "userAssigneeId": 2
      },
      {
        "title": "Unassigned cleanup task",
        "description": "Can be assigned later",
        "userAssigneeId": null
      }
    ]
  }'
```

Получите задачи, назначенные пользователям из начальных данных:

```bash
curl "http://localhost:8080/tasks/assigned?ids=1&ids=2"
```

Обновите состояние задачи:

```bash
curl -X PUT http://localhost:8080/tasks/1/status \
  -H "Content-Type: application/json" \
  -d '{"status": "IN_PROGRESS"}'
```

Назначьте задачу пользователю:

```bash
curl -X PUT http://localhost:8080/tasks/3/assignee/1
```

Снимите назначение задачи:

```bash
curl -X DELETE http://localhost:8080/tasks/3/assignee
```

Проверьте откат транзакции, отправив в одном пакете одного корректного исполнителя и одного отсутствующего:

```bash
curl -X POST http://localhost:8080/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "tasks": [
      {
        "title": "This task should not be committed",
        "description": null,
        "userAssigneeId": 1
      },
      {
        "title": "This task has a missing assignee",
        "description": null,
        "userAssigneeId": 999999
      }
    ]
  }'
```

Сервис выбрасывает исключение до успешного завершения `insert(tasks)`, поэтому вся транзакция `createTasks(...)` откатывается. Повторно выполните запрос назначенных задач, и первая задача из
неудачного пакета не появится.

## Лучшие практики { #best-practices }

- Оставляйте связи базы данных видимыми в схеме и SQL.
- Начинайте с модели, нужной для операции; не заставляйте одну "entity" обслуживать каждый запрос.
- Используйте проекции под конкретные запросы для путей чтения.
- Переиспользуйте существующие части DAO через `@Embedded`, когда проекция естественно содержит их.
- Используйте `@Embedded("prefix_")` для проекций с `JOIN`, чтобы SQL-алиасы оставались уникальными, а вложенные модели сохраняли естественные имена столбцов.
- Используйте макросы для повторяющихся фрагментов вставки сущностей, но оставляйте сложные соединения явными.
- Регистрируйте сфокусированные пользовательские преобразователи и позволяйте Kora разрешать их по обобщенному типу.
- Помещайте многошаговые правила согласованности в `inTx(...)`.
- Изучайте сгенерированные реализации репозиториев при отладке привязки параметров, пакетного поведения, сгенерированных ключей или сопоставления строк.

## Итоги { #summary }

Вы расширили базовое JDBC-приложение второй таблицей и несколькими продвинутыми шаблонами Kora JDBC:

- nullable-внешний ключ из `tasks` в `users`
- компактная модель вставки `TaskDAO`
- метаданные сущности и макросы вставки
- пользовательские преобразователи enum и параметра массива PostgreSQL
- пакетное создание задач со сгенерированными идентификаторами
- транзакционная проверка перед записью связанных строк
- проекция под конкретный запрос с `TaskDAO.SelectAssigned`
- переиспользование `UserDAO` через префиксный `@Embedded`

Итог остается SQL-first и явным. Репозиторий не привязан к одной модели, поэтому он может раскрывать ровно ту проекцию, которая нужна каждому запросу, без умножения репозиториев.

## Ключевые понятия { #key-concepts }

- как `@EntityJdbc`, `@Table`, `@Id`, `@Column` и префиксный `@Embedded` описывают формы сущностей/проекций
- как `%{entity#inserts}` раскрывается в конкретный SQL вставки
- как nullable-столбцы базы данных становятся nullable-полями Java/Kotlin и сгенерированными проверками на `null`
- как пользовательские преобразователи разрешаются по обобщенному типу преобразователя
- как `@Batch` превращается в сгенерированный код `addBatch()` / `executeBatch()`
- как один репозиторий может возвращать разные проекции для разных SQL-запросов
- как `inTx(...)` разделяет одно соединение между вызовами репозитория
- как передать список Java/Kotlin в PostgreSQL через `ANY(:ids)`

## Устранение неполадок { #troubleshooting }

**Преобразователь состояния задачи не используется:**

Убедитесь, что `TaskStatusParameterMapper` и `TaskStatusResultMapper` являются классами `@Component` и реализуют точные обобщенные типы преобразователей. В Java это `JdbcParameterColumnMapper<TaskStatus>`
и `JdbcResultColumnMapper<TaskStatus>`; в Kotlin преобразователь параметра обычно должен быть `JdbcParameterColumnMapper<TaskStatus?>`.

**Запрос назначенных задач сопоставляет неправильные столбцы:**

Проверьте SQL-алиасы в соединении и префикс embedded-поля. При `@Embedded("assignee_") UserDAO assigned` поле `UserDAO` с `@Column("created_at")` ожидает SQL-алиас `assignee_created_at`.

**Проектирование проекций выглядит дублирующим:**

Не создавайте отдельный репозиторий только потому, что запрос возвращает другую форму. Оставьте запрос в репозитории, который владеет операцией базы данных, и верните тип проекции, соответствующий
этому запросу.

**Пакетная вставка падает из-за отсутствующего исполнителя:**

Сервис проверяет идентификаторы исполнителей до вставки. Сначала создайте пользователя или отправьте `null` для `userAssigneeId`, если задача должна быть неназначенной.

**Запрос с `ANY(:ids)` падает:**

Убедитесь, что `ListOfLongJdbcParameterMapper` является `@Component` и создает массив PostgreSQL `BIGINT`.

**Появляется предупреждение преобразователя JSON для `TaskStatus` или DTO задач:**

Аннотируйте DTO и enum, выходящие на JSON-границу, через `@Json`, потому что они появляются в телах HTTP-запросов или ответов.

## Что дальше? { #whats-next }

- [Интеграционное тестирование](testing-integration.md), чтобы проверить транзакции, миграции, пользовательские преобразователи и проекции репозитория на PostgreSQL.
- [Тестирование как черный ящик](testing-black-box.md), чтобы проверить продвинутое JDBC-приложение через его HTTP API.
- [Наблюдаемость](observability.md), чтобы добавить метрики, трассировки, логи и пробы вокруг операций с базой данных.
- [Кэширование](cache.md), чтобы сократить повторные чтения из базы данных после стабилизации слоя хранения.
- [Шаблоны устойчивости](resilient.md), чтобы защитить сервисные операции, которые вызывают нестабильные нижестоящие зависимости.

## Помощь { #help }

Если столкнетесь с проблемами:

- сравните с [Kora Java Database JDBC Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-database-jdbc-advanced-app) и [Kora Kotlin Database JDBC Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-database-jdbc-advanced-app)
- проверьте [документацию по базе данных JDBC](../documentation/database-jdbc.md)
- проверьте [общую документацию по базам данных](../documentation/database-common.md)
- проверьте [документацию по миграциям базы данных](../documentation/database-migration.md)
