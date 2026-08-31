---
description: "Common Kora database model shared by the JDBC and Cassandra modules: entities, identifiers, naming, embedded fields, query parameters, SQL macros, batch queries, affected rows, several databases in one application, and query telemetry. Use when working with @Repository, @Query, @Table, @Column, @Id, @Embedded, @Batch, @Mapping and UpdateCount."
agent:
  use_when: "Use this file for Kora docs or implementation questions about the common database model shared by the JDBC and Cassandra modules: entities and views, @Table, @Column, @Id, @Embedded, naming strategies, @Repository and @Query, query parameter binding, SQL macros (%{return#selects}, %{entity#inserts}, %{entity#where = @id}), @Batch, UpdateCount, several databases in one application, and DatabaseTelemetry."
---

Базовые принципы и механизмы работы модулей баз данных в Kora.
В этом разделе описана общая модель для `JDBC` и `Cassandra`: отображения, репозитории, параметры запросов, пакетные запросы, количество затронутых строк и макросы.
Конфигурация подключения, транзакции, поддерживаемые сигнатуры и специфичные для драйвера отображатели описаны в документации для каждой реализации базы данных.

Этот раздел намеренно не описывает специфичные для драйвера детали.
Конфигурацию подключения, транзакции, типы возвращаемых значений, генерируемые базой данных идентификаторы, служебные параметры методов
и точные интерфейсы отображателей смотрите в документации для нужной реализации:
[`JDBC`](database-jdbc.md) или [`Cassandra`](database-cassandra.md).

Мы считаем, что лучший способ общения с базой данных SQL — это общение на её родном языке SQL.
Другие инструменты часто имеют ограничения на использование специфичных функций конкретной базы данных
или сложный программный язык для построения запросов, который требует дополнительного и значительного времени на изучение и освоение,
несёт много неочевидности и потенциальных ошибок со стороны разработчика, а также порой обладает низкой производительностью.

Если нужен пошаговый разбор перед справочным описанием, смотрите [База данных JDBC](../guides/database-jdbc.md) и [Продвинутая база данных JDBC](../guides/database-jdbc-advanced.md).

## Использование { #usage }

Использование показано на примере модуля [`JDBC`](database-jdbc.md): репозиторий объявляется как интерфейс, помеченный
аннотацией `@Repository`, и наследует `JdbcRepository`.
Каждый метод, помеченный `@Query`, содержит обычный `SQL`-запрос. Параметры метода связываются по имени с помощью
синтаксиса `:parameter`, а к полям сущности можно обращаться как `:entity.field`.

Отображения описываются с помощью общих аннотаций отображений и дополнительно помечаются `@EntityJdbc`
(`@EntityCassandra` для `Cassandra`), чтобы Kora сгенерировала отображатель на этапе компиляции:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @EntityJdbc
        @Table("entities")
        record Entity(@Id long id,
                      String name,
                      @Nullable String description) {}

        @Query("SELECT %{return#selects} FROM %{return#table} WHERE id = :id") //(1)!
        @Nullable
        Entity findById(long id);

        @Query("SELECT id, name, description FROM entities") //(2)!
        List<Entity> findAll();

        @Query("INSERT INTO %{entity#inserts}") //(3)!
        UpdateCount insert(Entity entity);
    }
    ```

    1.  Использует [макросы](#macros) `%{return#selects}` и `%{return#table}`. Разворачивается в запрос:
        ```sql
        SELECT id, name, description
        FROM entities
        WHERE id = :id
        ```
    2.  Столбцы перечислены вручную без макросов — это допустимо, но требует поддержки при изменении сущности.
    3.  Использует [макрос](#macros) `%{entity#inserts}`. Разворачивается в запрос:
        ```sql
        INSERT INTO entities(id, name, description)
        VALUES (:entity.id, :entity.name, :entity.description)
        ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @EntityJdbc
        @Table("entities")
        data class Entity(
            @field:Id val id: Long,
            val name: String,
            val description: String?
        )

        @Query("SELECT %{return#selects} FROM %{return#table} WHERE id = :id") //(1)!
        fun findById(id: Long): Entity?

        @Query("SELECT id, name, description FROM entities") //(2)!
        fun findAll(): List<Entity>

        @Query("INSERT INTO %{entity#inserts}") //(3)!
        fun insert(entity: Entity): UpdateCount
    }
    ```

    1.  Использует [макросы](#macros) `%{return#selects}` и `%{return#table}`. Разворачивается в запрос:
        ```sql
        SELECT id, name, description
        FROM entities
        WHERE id = :id
        ```
    2.  Столбцы перечислены вручную без макросов — это допустимо, но требует поддержки при изменении сущности.
    3.  Использует [макрос](#macros) `%{entity#inserts}`. Разворачивается в запрос:
        ```sql
        INSERT INTO entities(id, name, description)
        VALUES (:entity.id, :entity.name, :entity.description)
        ```

`SQL` остаётся под контролем разработчика: вы можете использовать специфичные для базы данных возможности, тогда как Kora
берёт на себя только безопасное связывание параметров, выполнение запроса и отображение результата.

Репозиторий также можно объявить абстрактным классом, реализующим интерфейс драйвера — тогда методы запросов являются
абстрактными методами этого класса, и видимость метода запроса не обязана быть `public`.
В Kotlin метод запроса не может быть `suspend` — генератор репозиториев отвергает такой метод на этапе компиляции.
Точный набор поддерживаемых типов возвращаемых значений специфичен для драйвера и описан на странице каждой реализации.

**Связывание параметров:** Kora генерирует типизированное связывание аргументов `SQL`-запроса на этапе компиляции.
Параметры запроса вида `:id` или `:entity.name` заменяются в сгенерированном коде на соответствующие вызовы драйвера.
Например, для параметра `String name` будет сгенерировано что-то вроде `statement.setString(1, name)`, где индекс
соответствует позиции параметра в запросе.
Это даёт и безопасность (защиту от SQL-инъекций), и производительность (всегда используются подготовленные запросы).

## Отображение { #view }

Отображение — это представление данных из базы данных в виде класса с полями.

===! ":fontawesome-brands-java: `Java`"

    Отображение — это либо `record`, который создаётся через свой канонический конструктор,
    либо `JavaBean` — класс с публичным конструктором без аргументов и парой `getX()` / `setX()` для каждого
    отображаемого поля, который создаётся пустым и затем заполняется [через сеттеры](https://docs.oracle.com/cd/E19316-01/819-3669/bnais/index.html).

    ```java
    public record Entity(String id, String name) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    Отображение должно быть `data class`, оно создаётся через свой первичный конструктор.

    ```kotlin
    data class Entity(val id: String, val name: String)
    ```

### Таблица { #table }

Вы можете указать, к какой таблице относится отображение — это понадобится, если вы используете [макросы](#macros) при построении запросов.

Если таблица не указана, макросы используют имя класса в [`snake_lower_case`](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/).

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Table("entities")
    public record Entity(String id, String name) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Table("entities")
    data class Entity(val id: String, val name: String)
    ```

### Идентификатор { #identifier }

Поскольку все манипуляции с данными выполняются путём преобразования отображения в запрос драйвера,
нет необходимости выделять внутри отображения специальный первичный ключ для работы с ним.

Определение того, что именно является первичным ключом, может быть полезно при использовании [макросов](#macros),
для этого можно использовать аннотацию `@Id`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record Entity(@Id String id, String name) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class Entity(@field:Id val id: String, val name: String)
    ```

#### Последовательный { #sequential }

Рассмотрим создание идентификатора в виде последовательности чисел на примере Postgres:
Kora предлагает использовать механизм базы данных [identity column](https://www.tutorialsteacher.com/postgresql/identity-column).

Пример таблицы для такого отображения выглядел бы так:

```sql
CREATE TABLE IF NOT EXISTS entities
(
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    name VARCHAR NOT NULL,
    PRIMARY KEY (id)
);
```

Идентификатор создаётся на этапе вставки в базу данных,
а получение его в коде приложения предполагается через конструкцию [генерируемого идентификатора](database-jdbc.md#generated-identifier) при вставке
либо через [специальные конструкции](https://www.postgresql.org/docs/current/dml-returning.html) вашей базы данных:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record Entity(Long id, String name) {}

    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("SELECT id, name FROM entities WHERE id = :id")
        @Nullable
        Entity findById(long id);

        @Query("INSERT INTO entities(name) VALUES (:entity.name) RETURNING id")
        long insert(Entity entity);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class Entity(val id: Long, val name: String)

    @Repository
    interface EntityRepository : JdbcRepository {

        @Query("SELECT id, name FROM entities WHERE id = :id")
        fun findById(id: Long): Entity?

        @Query("INSERT INTO entities(name) VALUES (:entity.name) RETURNING id")
        fun insert(entity: Entity): Long
    }
    ```

Вместо специфичного для драйвера `RETURNING` первичный ключ, сгенерированный базой данных при вставке, можно вернуть,
пометив аннотацией `@Id` сам **метод** репозитория (аннотация применима и к полю отображения, и к методу).
Генерируемые идентификаторы поддерживает драйвер [JDBC](database-jdbc.md#generated-identifier), точное поведение
и поддерживаемые сигнатуры возвращаемых значений описаны там:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Table("entities")
        public record Entity(@Id Long id, String name) {}

        @Id //(1)!
        @Query("INSERT INTO %{entity#inserts -= @id}") //(2)!
        long insert(Entity entity);
    }
    ```

    1.  Помечает метод так, чтобы возвращался идентификатор, сгенерированный базой данных.
    2.  Разворачивается в запрос:
        ```sql
        INSERT INTO entities(name) VALUES (:entity.name)
        ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Table("entities")
        data class Entity(@field:Id val id: Long, val name: String)

        @Id //(1)!
        @Query("INSERT INTO %{entity#inserts -= @id}") //(2)!
        fun insert(entity: Entity): Long
    }
    ```

    1.  Помечает метод так, чтобы возвращался идентификатор, сгенерированный базой данных.
    2.  Разворачивается в запрос:
        ```sql
        INSERT INTO entities(name) VALUES (:entity.name)
        ```

#### Случайный { #random }

Для создания случайного идентификатора предлагается использовать стандартный `UUID` из Java:

Пример таблицы для такого отображения выглядел бы так:

```sql
CREATE TABLE IF NOT EXISTS entities
(
    id UUID NOT NULL,
    name VARCHAR NOT NULL,
    PRIMARY KEY (id)
);
```

Идентификатор создаётся на этапе создания объекта в пользовательском коде приложения:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record Entity(UUID id,
                         String name) {}

    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("SELECT id, name FROM entities WHERE id = :id")
        @Nullable
        Entity findById(UUID id);

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        void insert(Entity entity);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class Entity(val id: UUID,
                      val name: String)

    @Repository
    interface EntityRepository : JdbcRepository {

        @Query("SELECT id, name FROM entities WHERE id = :id")
        fun findById(id: UUID): Entity?

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        fun insert(entity: Entity)
    }
    ```

#### Составной { #composite }

Когда требуется составной ключ, предполагается использовать аннотацию `@Embedded` для создания [встроенных полей](#embedded-fields).

### Именование { #naming }

По умолчанию имена полей отображения преобразуются в [`snake_lower_case`](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/) при получении результата.

Если требуется настроить соответствие конкретных полей базы данных отображению, можно использовать аннотацию `@Column`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record Entity(@Column("ID") String id,
                         @Column("NAME") String name) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class Entity(@field:Column("ID") val id: String,
                      @field:Column("NAME") val name: String)
    ```

#### Стратегия именования { #naming-strategy }

Если требуется применить стратегию именования ко всему отображению, предлагается создать реализацию `NameConverter` и указать её в аннотации `@NamingStrategy`.
Реализация `NameConverter` обязана иметь доступный конструктор без параметров.

Либо используйте готовые стратегии из Kora (`io.koraframework.common.naming`):

- `NoopNameConverter` — стратегия использует имя поля как есть.
- `SnakeCaseNameConverter` — стратегия использует [`snake_lower_case`](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/).
- `SnakeCaseUpperNameConverter` — стратегия использует [SNAKE_UPPER_CASE](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/).
- `PascalCaseNameConverter` — стратегия использует [PascalCase](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/).
- `CamelCaseNameConverter` — стратегия использует [camelCase](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/).

===! ":fontawesome-brands-java: `Java`"

    ```java
    @NamingStrategy(NoopNameConverter.class)
    public record Entity(String id,
                         String name) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @NamingStrategy(NoopNameConverter::class)
    data class Entity(val id: String,
                      val name: String)
    ```

Аннотация `@Column` на поле всегда имеет приоритет над стратегией именования отображения.

### Обязательные поля { #required-fields }

===! ":fontawesome-brands-java: `Java`"

    По умолчанию все поля, объявленные в отображении, считаются **обязательными** (*NotNull*).

    ```java
    public record Entity(String id,
                         String name) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    По умолчанию все поля, объявленные в отображении и не использующие синтаксис [Kotlin Nullability](https://kotlinlang.org/docs/null-safety.html), считаются **обязательными** (*NotNull*).

    ```kotlin
    data class Entity(val id: String,
                      val name: String)
    ```

### Необязательные поля { #optional-fields }

===! ":fontawesome-brands-java: `Java`"

    Если поле отображения необязательное, то есть может отсутствовать,
    пометьте его явно аннотацией `@Nullable`.

    ```java
    public record Entity(String id,
                         @Nullable String name) {} //(1)!
    ```

    1.  Сама Kora использует [JSpecify](https://jspecify.dev/) `org.jspecify.annotations.Nullable`, но подойдёт любая
        аннотация, имя которой заканчивается на `Nullable`, например `jakarta.annotation.Nullable` / `org.jetbrains.annotations.Nullable` и т.д.

    Также можно указать необязательные параметры конструктора, если канонический конструктор Record переопределён:

    ```java
    public record Entity(String id,
                         String name) {

        public Entity(String id,
                      @Nullable String name) { //(1)!
            this.id = id;
            this.name = name;
        }
    }
    ```

    1.  Сама Kora использует [JSpecify](https://jspecify.dev/) `org.jspecify.annotations.Nullable`, но подойдёт любая
        аннотация, имя которой заканчивается на `Nullable`, например `jakarta.annotation.Nullable` / `org.jetbrains.annotations.Nullable` и т.д.

=== ":simple-kotlin: `Kotlin`"

    Предполагается использование синтаксиса [Kotlin Nullability](https://kotlinlang.org/docs/null-safety.html) и пометка такого параметра как Nullable:

    ```kotlin
    data class Entity(val id: String,
                      val name: String?)
    ```

### Встроенные поля { #embedded-fields }

Если требуется использовать вложенные поля, то есть преобразовывать поля отображения в отдельные классы, можно использовать аннотацию `@Embedded`.

Предположим, есть SQL-таблица с составным ключом, который мы хотим выразить отдельным классом:

```sql
CREATE TABLE IF NOT EXISTS entities
(
    name    VARCHAR NOT NULL,
    surname VARCHAR NOT NULL,
    info    VARCHAR NOT NULL,
    PRIMARY KEY (name, surname)
)
```

Тогда отображение будет выглядеть так:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record Entity(@Id @Embedded UserID id,
                         @Column("info") String info) {

        public record UserID(String name, String surname) {}
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class Entity(
        @field:Id @field:Embedded val id: UserID,
        @field:Column("info") val info: String
    ) {

        data class UserID(
            val name: String,
            val surname: String
        )
    }
    ```

Тогда репозиторий для такого отображения будет выглядеть так:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("""
                SELECT name, surname, info FROM entities
                WHERE name = :id.name AND surname = :id.surname;
                """)
        @Nullable
        Entity findById(Entity.UserID id);

        @Query("""
            INSERT INTO entities(name, surname, info)
            VALUES (:entity.id.name, :entity.id.surname, :entity.info)
            """)
        void insert(Entity entity);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Query(
            """
            SELECT name, surname, info FROM entities
            WHERE name = :id.name AND surname = :id.surname;
            """
        )
        fun findById(id: Entity.UserID): Entity?

        @Query(
            """
            INSERT INTO entities(name, surname, info)
            VALUES (:entity.id.name, :entity.id.surname, :entity.info)
            """
        )
        fun insert(entity: Entity)
    }
    ```

По умолчанию встроенное поле не добавляет префикс к столбцам вложенного класса.
Если у полей есть общий префикс, его можно указать в аннотации `@Embedded("user_")`:

```sql
CREATE TABLE IF NOT EXISTS entities
(
    user_name       VARCHAR NOT NULL,
    user_surname    VARCHAR NOT NULL,
    info            VARCHAR NOT NULL,
    PRIMARY KEY (user_name, user_surname)
)
```

Встроенное поле может быть `@Nullable`: если все столбцы вложенного класса в строке результата равны `NULL` —
именно это даёт `LEFT JOIN` без совпадения — всё поле выставляется в `null`, а не конструируется.

Встроенное поле также может быть `List` вложенного отображения: строки с одинаковыми значениями столбцов внешнего
отображения схлопываются в один внешний объект, а собранные из этих строк вложенные отображения становятся его коллекцией.
Так связь «один ко многим» через `JOIN` отображается в один объект:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record UserOrdersView(@Embedded("u_") User user,
                                 @Embedded("o_") List<Order> orders) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class UserOrdersView(
        @field:Embedded("u_") val user: User,
        @field:Embedded("o_") val orders: List<Order>
    )
    ```

## Репозиторий { #repository }

Основной инструмент работы с базами данных в Kora — использование [паттерна репозиторий](https://java-design-patterns.com/patterns/repository/#explanation) при проектировании абстракции доступа к базе данных.
Интерфейс репозитория должен быть помечен аннотацией `@Repository`.
Запросы для методов репозитория описываются с помощью аннотации `@Query`.
Реализация репозитория создаётся на этапе компиляции: все методы с `@Query` выполняют описанный запрос, оптимально собирают аргументы запроса и обрабатывают результат.

Предполагается, что `SQL`-запросы пишет разработчик, поскольку это повышает его понимание плана запроса,
даёт больше информации и контекста о том, что запрос делает и как он будет работать.
Чтобы не выписывать все поля и столбцы модели вручную, можно использовать [макросы](#macros).

Репозиторий должен наследовать одну из реализаций, в примерах ниже рассматривается реализация [JDBC](database-jdbc.md):

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository //(1)!
    public interface EntityRepository extends JdbcRepository {

        public record Entity(String id, String name) { }

        //(2)!
        @Query("SELECT id, name FROM entities WHERE id = :id")
        @Nullable
        Entity findById(String id);
    }
    ```

    1. Указывает, что интерфейс является репозиторием.
    2. Указывает, что Kora должна создать реализацию метода, выполняющую `SQL`-запрос, указанный в аннотации.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository //(1)!
    interface EntityRepository : JdbcRepository {

        data class Entity(val id: String, val name: String)

        //(2)!
        @Query("SELECT id, name FROM entities WHERE id = :id")
        fun findById(id: String): Entity?
    }
    ```

    1. Указывает, что интерфейс является репозиторием.
    2. Указывает, что Kora должна создать реализацию метода, выполняющую `SQL`-запрос, указанный в аннотации.

### Параметры запроса { #query-parameters }

Параметры метода репозитория связываются с именованными параметрами в `@Query`.
Простой параметр указывается по имени параметра метода: `:id`, `:name`, `:status`.
Если параметр является сущностью или `DTO`, к его полям можно обращаться через точку: `:entity.id`, `:entity.name`, `:filter.status`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("""
            SELECT id, name FROM entities
            WHERE id = :id AND name = :filter.name
            """)
        @Nullable
        Entity findById(String id, Filter filter);

        record Filter(String name) {}
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Query(
            """
            SELECT id, name FROM entities
            WHERE id = :id AND name = :filter.name
            """
        )
        fun findById(id: String, filter: Filter): Entity?

        data class Filter(val name: String)
    }
    ```

Если параметр встречается в запросе более одного раза, Kora связывает его с каждым вхождением.

Связывание проверяется на этапе компиляции в обе стороны:

- если параметр метода не используется в запросе и не является служебным параметром конкретного драйвера, компиляция падает с ошибкой `Query parameter is unused`;
- если в запросе есть плейсхолдер, которому не соответствует ни один параметр метода, компиляция падает с ошибкой `SQL query placeholder has no matching method parameter` и списком доступных параметров;
- если в запросе указан `:entity.field` для отсутствующего поля сущности, компиляция падает с ошибкой `SQL query placeholder has no matching entity field` и списком доступных полей.

Текст, который лишь выглядит как плейсхолдер, игнорируется, поэтому `SQL` с двоеточиями продолжает компилироваться.
Kora пропускает `:name` внутри строк в одинарных кавычках, идентификаторов в двойных кавычках и обратных апострофах,
идентификаторов в `[квадратных скобках]`, блоков `$$dollar quoted$$` и `$tag$dollar quoted$tag$`,
однострочных комментариев `--` и блочных комментариев `/* */`, а оператор приведения типа Postgres `::` параметром не считается.

### Запрос из ресурса { #query-resource }

Запрос можно хранить в отдельном `SQL`-файле вместо аннотации. Если значение `@Query` начинается с `classpath:/`,
остаток значения трактуется как путь к ресурсу относительно корней исходников и classpath модуля, а содержимое файла
читается на этапе компиляции и используется как запрос.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("classpath:/sql/find-all-entities.sql") //(1)!
        List<Entity> findAll();
    }
    ```

    1.  Файл `src/main/resources/sql/find-all-entities.sql` читается на этапе компиляции.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Query("classpath:/sql/find-all-entities.sql") //(1)!
        fun findAll(): List<Entity>
    }
    ```

    1.  Файл `src/main/resources/sql/find-all-entities.sql` читается на этапе компиляции.

Файл проходит ровно ту же обработку, что и встроенный запрос: разворачиваются [макросы](#macros) и
связываются с проверкой [параметры](#query-parameters).
Если ресурс прочитать не удалось, компиляция падает с ошибкой `SQL query resource wasn't found`.

### Отображатели { #mappers }

Используйте аннотацию `@Mapping`, когда значению нужно нестандартное представление в базе данных.
Её можно разместить на поле отображения, параметре метода или методе репозитория:

- на поле отображения — чтобы настроить чтение или запись конкретного столбца;
- на параметре метода — чтобы настроить запись конкретного параметра запроса;
- на методе репозитория — чтобы настроить обработку всего результата запроса или строки результата.

Произвольный отображатель нельзя использовать в любом месте: его тип должен соответствовать месту применения.
Отображатель параметра применяется к параметру запроса, отображатель столбца — к полю отображения, а отображатель результата или строки — к методу репозитория.
Точный набор поддерживаемых интерфейсов зависит от драйвера: например, `JDBC` использует `JdbcRowMapper`, `JdbcResultSetMapper`, `JdbcResultColumnMapper` и `JdbcParameterColumnMapper`.
Соответствующие интерфейсы для `Cassandra`, а также детали их использования описаны в документации этой реализации.
Все отображатели строк драйверов имеют общий маркерный интерфейс `RowMapper<T>` (`io.koraframework.database.common.RowMapper`), который является базовым типом для специфичных для драйвера отображателей, таких как `JdbcRowMapper` и `CassandraRowMapper`.
Сама аннотация `@Mapping` находится в основном модуле `common` (`io.koraframework.common.annotation.Mapping`), а каждый контракт отображателя реализует её маркер `Mapping.MappingFunction`.
Если отображатель указан через `@Mapping`, Kora добавляет его как зависимость сгенерированного репозитория и использует вместо отображателя по умолчанию.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Table("entities")
    public record Entity(@Id String id,
                         @Mapping(JsonParameterMapper.class)
                         @Column("payload")
                         String payload) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Table("entities")
    data class Entity(
        @field:Id val id: String,
        @field:Mapping(JsonParameterMapper::class)
        @field:Column("payload")
        val payload: String
    )
    ```

Отображатель **с** зависимостями в конструкторе обязан быть компонентом [графа приложения](container.md).
Отображатель **без** зависимостей компонентом быть не должен: Kora создаёт его сама, а объявление его компонентом
приводит к ошибке сборки графа `Multiple components match`.

### Пакетный запрос { #batch-query }

Kora поддерживает пакетные запросы с помощью аннотации `@Batch`.

В отличие от последовательного выполнения SQL-запросов, пакетная обработка позволяет отправить целый набор запросов за один вызов,
сокращая число требуемых сетевых обращений и позволяя выполнять часть запросов параллельно на стороне базы данных,
что может повысить скорость выполнения.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        void insert(@Batch List<Entity> entity);
    }
    ```

    **Пакетный запрос** не может возвращать произвольные значения — такой метод может возвращать `void`, `UpdateCount`, `int[]` или `long[]`,
    либо генерируемые базой данных идентификаторы, если метод помечен `@Id`, для драйвера [JDBC](database-jdbc.md#generated-identifier).

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        fun insert(@Batch entity: List<Entity>)
    }
    ```

    **Пакетный запрос** не может возвращать произвольные значения — такой метод может возвращать `Unit`, `UpdateCount`, `IntArray` или `LongArray`,
    либо генерируемые базой данных идентификаторы, если метод помечен `@Id`, для драйвера [JDBC](database-jdbc.md#generated-identifier).

`@Batch` ставится на параметр типа `List`, и каждый элемент списка по очереди подставляется в один и тот же запрос.
Любой другой тип коллекции отвергается на этапе компиляции с ошибкой `@Batch can be used only with java.util.List<T> parameters`.
Все остальные параметры метода, если они есть, являются общими для всех элементов пакета.
Например, в `INSERT INTO logs(tenant_id, id, value) VALUES (:tenantId, :entity.id, :entity.value)`
параметр `tenantId` одинаков для каждого элемента, тогда как поля `entity` берутся из каждого элемента списка.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Query("INSERT INTO logs(tenant_id, id, value) VALUES (:tenantId, :entity.id, :entity.value)")
    UpdateCount insert(String tenantId, @Batch List<Entity> entity);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Query("INSERT INTO logs(tenant_id, id, value) VALUES (:tenantId, :entity.id, :entity.value)")
    fun insert(tenantId: String, @Batch entity: List<Entity>): UpdateCount
    ```

Метод может объявлять только один параметр с `@Batch`.
Поддержка генерируемых базой данных идентификаторов в пакетных запросах зависит от конкретного драйвера и описана в соответствующем разделе.

### Затронутые строки { #affected-rows }

Kora не обрабатывает содержимое запроса, результат метода всегда выводится из строк, возвращённых базой данных.
Если вы хотите получить в результате количество затронутых строк, используйте специальный тип `UpdateCount` — запись с единственным компонентом `long value()`.
Для обычного запроса `UpdateCount#value()` содержит количество строк, возвращённое драйвером для выполненного запроса.
Для пакетного запроса в `JDBC` значение равно сумме счётчиков по всем элементам пакета и равно `-1`, если хотя бы для одного
элемента драйвер вернул `SUCCESS_NO_INFO` вместо количества строк.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        UpdateCount insert(Entity entity);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        fun insert(entity: Entity): UpdateCount
    }
    ```

### Ручной запрос { #manual-query }

Если по какой-либо причине функциональности запросов в аннотации `@Query` недостаточно или требуется ручное управление соединением,
можно использовать встроенный в репозиторий исполнитель, чтобы создать метод с полностью ручным управлением.

Каждый интерфейс репозитория драйвера отдаёт свой исполнитель методом `executor()`: `JdbcRepository#executor()` возвращает
`JdbcExecutor`, а `CassandraRepository#executor()` — `CassandraExecutor`.

Внутри такого метода можно также использовать другие методы репозитория, и при необходимости они тоже будут выполняться в рамках одной транзакции.
Подробнее о транзакциях смотрите в документации для конкретной реализации репозитория.

Репозитории могут объявлять обычные методы с реализациями.
Это полезно, когда более сложную операцию стоит держать рядом с запросами: например, выполнение нескольких методов `@Query` в одной транзакции,
построение результата из нескольких запросов или хранение последовательности операций с базой данных внутри репозитория вместо переноса её в слой сервиса.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        public record Entity(Long id, String name) {}

        @Query("INSERT INTO entities(name) VALUES (:entity.name)")
        UpdateCount insert(Entity entity);

        @Query("UPDATE entities SET name = :name WHERE id = :id")
        UpdateCount updateName(Long id, String name);

        default Entity saveAndRename(Entity entity, String name) {
            return executor().inTx(() -> { //(1)!
                insert(entity);
                updateName(entity.id(), name);
                return new Entity(entity.id(), name);
            });
        }
    }
    ```

    1.  `JdbcExecutor#inTx` выполняет callback в транзакции, переиспользуя текущую, если транзакция уже открыта.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        data class Entity(val id: Long, val name: String)

        @Query("INSERT INTO entities(name) VALUES (:entity.name)")
        fun insert(entity: Entity): UpdateCount

        @Query("UPDATE entities SET name = :name WHERE id = :id")
        fun updateName(id: Long, name: String): UpdateCount

        fun saveAndRename(entity: Entity, name: String): Entity {
            return executor().inTx(JdbcExecutor.SqlSupplier { //(1)!
                insert(entity)
                updateName(entity.id, name)
                Entity(entity.id, name)
            })
        }
    }
    ```

    1.  У `inTx` много перегрузок, поэтому Kotlin не может вывести, какой функциональный интерфейс реализует обычная лямбда —
        SAM-конструктор `JdbcExecutor.SqlSupplier` (или `JdbcExecutor.SqlRunnable` для метода без результата) нужно указывать явно.

Когда вы строите `SQL` вручную через исполнитель драйвера, а не с помощью метода `@Query`,
запрос всё равно проходит через телеметрию Kora. Выполняемый запрос описывается общим
`QueryContext(queryId, sql, operation)`: `queryId` — это стабильный идентификатор запроса, передаваемый в телеметрию
(удобно использовать имя вида `Repository.method`), `sql` — итоговый текст запроса, а `operation` по умолчанию равно `db_query`.
Точный метод исполнителя и его сигнатура специфичны для драйвера — рабочий пример смотрите в [JDBC](database-jdbc.md#query).

### Несколько баз данных { #multiple-databases }

Иногда в рамках одного приложения нужно обращаться к разным базам данных в разных репозиториях,
это можно решить следующим образом.
Ниже приведён пример для базы данных [JDBC](database-jdbc.md), но принцип тот же и для [Cassandra](database-cassandra.md).

Соединение с базой данных предоставляется модулем-фабрикой: `JdbcDatabaseModule` объявляет `new JdbcDatabaseFactoryModule("jdbc")`
как `@FactoryModule`, и каждый компонент, созданный таким модулем-фабрикой, наследует тег метода-фабрики.
Чтобы добавить вторую базу данных, объявите ещё один метод `@FactoryModule` со своим путём конфигурации и своим тегом:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends JdbcDatabaseModule {

        final class OtherDatabase { }

        @Tag(OtherDatabase.class) //(1)!
        @FactoryModule //(2)!
        default JdbcDatabaseFactoryModule otherJdbcDatabase() {
            return new JdbcDatabaseFactoryModule("otherDb"); //(3)!
        }
    }
    ```

    1.  Тег, который получают все компоненты, созданные этим модулем-фабрикой.
    2.  Сообщает Kora, что возвращаемый объект сам является модулем, а его методы — фабриками компонентов.
    3.  Секция конфигурации второй базы данных.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : JdbcDatabaseModule {

        class OtherDatabase

        @Tag(OtherDatabase::class) //(1)!
        @FactoryModule //(2)!
        fun otherJdbcDatabase(): JdbcDatabaseFactoryModule {
            return JdbcDatabaseFactoryModule("otherDb") //(3)!
        }
    }
    ```

    1.  Тег, который получают все компоненты, созданные этим модулем-фабрикой.
    2.  Сообщает Kora, что возвращаемый объект сам является модулем, а его методы — фабриками компонентов.
    3.  Секция конфигурации второй базы данных.

Каждое соединение читает свою секцию конфигурации:

===! ":material-code-json: `Hocon`"

    ```javascript
    jdbc {
        jdbcUrl = "jdbc:postgresql://localhost:5432/main"
        username = "postgres"
        password = "postgres"
        poolName = "main"
    }

    otherDb {
        jdbcUrl = "jdbc:postgresql://localhost:5432/other"
        username = "postgres"
        password = "postgres"
        poolName = "other"
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    jdbc:
      jdbcUrl: "jdbc:postgresql://localhost:5432/main"
      username: "postgres"
      password: "postgres"
      poolName: "main"

    otherDb:
      jdbcUrl: "jdbc:postgresql://localhost:5432/other"
      username: "postgres"
      password: "postgres"
      poolName: "other"
    ```

А репозитории, которые будут использовать эту базу данных, теперь обязаны указывать тег этого соединения:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository(executorTag = OtherDatabase.class)
    public interface OtherJdbcRepository extends JdbcRepository {

    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository(executorTag = OtherDatabase::class)
    interface OtherJdbcRepository : JdbcRepository {

    }
    ```

Репозиториям с основным соединением к базе данных тег не требуется.

### Макросы { #macros }

Самой утомительной частью написания SQL-запросов может быть перечисление и поддержание в актуальном состоянии столбцов и полей отображения.

Чтобы решить эту проблему, используйте специальные макросы внутри `SQL`-запроса в аннотации `@Query`.
Эти конструкции оперируют целевым [отображением](#view), разворачивают его в конкретные `SQL`-конструкции и упрощают расширение `SQL`-запросов.
Макрос — это помощник для написания `SQL`-запросов, который разворачивается в конструкции, которые пользователь мог бы написать вручную.

Синтаксис макросов выглядит следующим образом: `%{return#selects}`.

1. Макрос ограничен синтаксической конструкцией `%{` и `}`
2. Сначала указывается цель макроса — это может быть имя любого аргумента метода, возвращаемое значение через ключевое слово `return`,
   имя параметра типа репозитория или метода, либо вложенное поле любой из этих целей, записанное через точку: `return.user`
3. Затем символ `#` используется для разделения цели макроса и команды макроса
4. После этого указывается команда макроса, которая сообщает, в какую SQL-конструкцию развернуть отображение

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Table("entities")
        public record Entity(@Id Long id,
                             @Column("entity_name") String name,
                             String code) {}

        @Query("SELECT %{return#selects} FROM %{return#table}") //(1)!
        List<Entity> findAll();
    }
    ```

    1.  Разворачивается в запрос:
        ```sql
        SELECT id, entity_name, code FROM entities
        ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Table("entities")
        data class Entity(@field:Id val id: Long,
                          @field:Column("entity_name") val name: String,
                          val code: String)

        @Query("SELECT %{return#selects} FROM %{return#table}") //(1)!
        fun findAll(): List<Entity>
    }
    ```

    1.  Разворачивается в запрос:
        ```sql
        SELECT id, entity_name, code FROM entities
        ```

Цель `return` разворачивает привычные контейнеры результата, поэтому `List<Entity>`, `Optional<Entity>` и просто `Entity`
приводят к одному и тому же отображению.

#### Команды { #commands }

Доступные команды макросов:

- `table` — разворачивается в значение отображения из [аннотации](#table) `@Table`, а при её отсутствии переводит имя отображения в [`snake_lower_case`](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/)
- `selects` — создаёт конструкцию перечисления столбцов отображения для запроса `SELECT`
- `columns` — создаёт голое перечисление столбцов отображения, без квалификации таблицей и без псевдонимов
- `values` — создаёт перечисление параметров запроса, соответствующих полям отображения
- `inserts` — создаёт конструкцию из таблицы, перечисления столбцов и соответствующих полей отображения для запроса `INSERT`
- `updates` — создаёт конструкцию перечисления столбцов и соответствующих полей отображения для запроса `UPDATE`, поле [идентификатора](#identifier) всегда исключается
- `where` — создаёт конструкцию перечисления столбцов со значением из отображения для части `WHERE` запроса

`columns` и `values` — это две половины `inserts`, они полезны, когда `INSERT` требуется написать вручную:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Query("INSERT INTO %{entity#table}(%{entity#columns -= @id}) VALUES (%{entity#values -= @id})") //(1)!
    UpdateCount insert(Entity entity);
    ```

    1.  Разворачивается в запрос:
        ```sql
        INSERT INTO entities(entity_name, code) VALUES (:entity.name, :entity.code)
        ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Query("INSERT INTO %{entity#table}(%{entity#columns -= @id}) VALUES (%{entity#values -= @id})") //(1)!
    fun insert(entity: Entity): UpdateCount
    ```

    1.  Разворачивается в запрос:
        ```sql
        INSERT INTO entities(entity_name, code) VALUES (:entity.name, :entity.code)
        ```

#### Перечисление полей { #field-enumeration }

Макросы поддерживают дополнительный синтаксис перечисления определённых полей в команде,
если вдруг требуется сделать частичное обновление или частичную выборку данных.
Для этого после команды используется специальная конструкция: `%{return#updates=name}`.

Пробелы можно ставить **только** между полями в перечислении или вокруг специального символа перечисления.

Доступны специальные символы перечисления:

1. `=` — в разворачивании команды участвуют только те поля отображения, имена которых указаны после символа
2. `-=` — в разворачивании команды участвуют все поля отображения, кроме указанных после символа

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Table("entities")
        public record Entity(@Id Long id,
                             @Column("entity_name") String name,
                             String code) {}

        @Query("INSERT INTO %{entity#inserts=name,code}") //(1)!
        UpdateCount insert(Entity entity);
    }
    ```

    1.  Разворачивается в запрос:
        ```sql
        INSERT INTO entities(entity_name, code)
        VALUES (:entity.name, :entity.code)
        ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Table("entities")
        data class Entity(@field:Id val id: Long,
                          @field:Column("entity_name") val name: String,
                          val code: String)

        @Query("INSERT INTO %{entity#inserts=name,code}") //(1)!
        fun insert(entity: Entity): UpdateCount
    }
    ```

    1.  Разворачивается в запрос:
        ```sql
        INSERT INTO entities(entity_name, code)
        VALUES (:entity.name, :entity.code)
        ```

##### Идентификатор { #identifier-2 }

При перечислении полей в макросе можно использовать специальное ключевое слово `@id`,
чтобы сразу сослаться на идентификатор отображения, помеченный [аннотацией](#identifier) `@Id`.

Это особенно полезно, когда идентификатор является [составным ключом](#embedded-fields), чтобы перечислить сразу все столбцы.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Table("entities")
        public record Entity(@Id Long id,
                             @Column("entity_name") String name,
                             String code) {}

        @Query("INSERT INTO %{entity#inserts-=@id}") //(1)!
        UpdateCount insert(Entity entity);
    }
    ```

    1.  Разворачивается в запрос:
        ```sql
        INSERT INTO entities(entity_name, code)
        VALUES (:entity.name, :entity.code)
        ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Table("entities")
        data class Entity(@field:Id val id: Long,
                          @field:Column("entity_name") val name: String,
                          val code: String)

        @Query("INSERT INTO %{entity#inserts-=@id}") //(1)!
        fun insert(entity: Entity): UpdateCount
    }
    ```

    1.  Разворачивается в запрос:
        ```sql
        INSERT INTO entities(entity_name, code)
        VALUES (:entity.name, :entity.code)
        ```

#### Псевдоним таблицы { #table-alias }

Команда `table` принимает псевдоним таблицы через синтаксис `table as <псевдоним>`.
Как только цели назначен псевдоним, все остальные макросы над этой же целью квалифицируют свои столбцы им:
`selects` выдаёт `псевдоним.столбец` и, если отображение переименовывает столбец, добавляет `AS` с итоговым именем,
а `where` выдаёт `псевдоним.столбец = :путь`.

Именно это делает макросы применимыми в `JOIN`, где вложенная цель и [встроенное поле](#embedded-fields) с префиксом
отображают соединяемые таблицы в одно отображение:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface UserOrderRepository extends JdbcRepository {

        @Table("users")
        record User(@Id String id, String name) {}

        @Table("orders")
        record Order(@Id String id, @Column("user_id") String userId, String number) {}

        record UserOrderView(@Embedded("u_") User user, @Embedded("o_") Order order) {}

        @Query("""
            SELECT %{return#selects}
            FROM %{return.user#table as u} JOIN %{return.order#table as o} ON o.user_id = u.id
            WHERE u.id = :id
            """) //(1)!
        @Nullable
        UserOrderView find(String id);
    }
    ```

    1.  Разворачивается в запрос:
        ```sql
        SELECT u.id AS u_id, u.name AS u_name, o.id AS o_id, o.user_id AS o_user_id, o.number AS o_number
        FROM users u JOIN orders o ON o.user_id = u.id
        WHERE u.id = :id
        ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface UserOrderRepository : JdbcRepository {

        @Table("users")
        data class User(@field:Id val id: String, val name: String)

        @Table("orders")
        data class Order(@field:Id val id: String, @field:Column("user_id") val userId: String, val number: String)

        data class UserOrderView(@field:Embedded("u_") val user: User, @field:Embedded("o_") val order: Order)

        @Query(
            """
            SELECT %{return#selects}
            FROM %{return.user#table as u} JOIN %{return.order#table as o} ON o.user_id = u.id
            WHERE u.id = :id
            """
        ) //(1)!
        fun find(id: String): UserOrderView?
    }
    ```

    1.  Разворачивается в запрос:
        ```sql
        SELECT u.id AS u_id, u.name AS u_name, o.id AS o_id, o.user_id AS o_user_id, o.number AS o_number
        FROM users u JOIN orders o ON o.user_id = u.id
        WHERE u.id = :id
        ```

#### Пример репозитория { #repository-example }

Пример полноценного репозитория со всеми базовыми методами работы с отображением для [Postgres SQL](https://postgrespro.com/docs/postgresql):

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Table("entities")
        record Entity(@Id String id,
                      @Column("value1") int field1,
                      String value2,
                      @Nullable String value3) {}

        @Query("SELECT %{return#selects} FROM %{return#table} WHERE id = :id") //(1)!
        @Nullable
        Entity findById(String id);

        @Query("SELECT %{return#selects} FROM %{return#table}") //(2)!
        List<Entity> findAll();

        @Query("INSERT INTO %{entity#inserts}")  //(3)!
        UpdateCount insert(@Batch List<Entity> entity);

        @Query("UPDATE %{entity#table} SET %{entity#updates} WHERE %{entity#where = @id}")  //(4)!
        UpdateCount update(@Batch List<Entity> entity);

        @Query("INSERT INTO %{entity#inserts} ON CONFLICT (id) DO UPDATE SET %{entity#updates}")  //(5)!
        UpdateCount upsert(@Batch List<Entity> entity);

        @Query("DELETE FROM entities WHERE id = :id")
        UpdateCount deleteById(String id);

        @Query("DELETE FROM entities")
        UpdateCount deleteAll();
    }
    ```

    1.  Разворачивается в запрос:
        ```sql
        SELECT id, value1, value2, value3
        FROM entities
        WHERE id = :id
        ```
    2.  Разворачивается в запрос:
        ```sql
        SELECT id, value1, value2, value3
        FROM entities
        ```
    3.  Разворачивается в запрос:
        ```sql
        INSERT INTO entities(id, value1, value2, value3)
        VALUES (:entity.id, :entity.field1, :entity.value2, :entity.value3)
        ```
    4.  Разворачивается в запрос:
        ```sql
        UPDATE entities
        SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3
        WHERE id = :entity.id
        ```
    5.  Разворачивается в запрос:
        ```sql
        INSERT INTO entities(id, value1, value2, value3)
        VALUES (:entity.id, :entity.field1, :entity.value2, :entity.value3)
        ON CONFLICT (id) DO UPDATE
        SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3
        ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Table("entities")
        data class Entity(
            @field:Id val id: String,
            @field:Column("value1") val field1: Int,
            val value2: String,
            val value3: String?
        )

        @Query("SELECT %{return#selects} FROM %{return#table} WHERE id = :id") //(1)!
        fun findById(id: String): Entity?

        @Query("SELECT %{return#selects} FROM %{return#table}") //(2)!
        fun findAll(): List<Entity>

        @Query("INSERT INTO %{entity#inserts}") //(3)!
        fun insert(@Batch entity: List<Entity>): UpdateCount

        @Query("UPDATE %{entity#table} SET %{entity#updates} WHERE %{entity#where = @id}") //(4)!
        fun update(@Batch entity: List<Entity>): UpdateCount

        @Query("INSERT INTO %{entity#inserts} ON CONFLICT (id) DO UPDATE SET %{entity#updates}") //(5)!
        fun upsert(@Batch entity: List<Entity>): UpdateCount

        @Query("DELETE FROM entities WHERE id = :id")
        fun deleteById(id: String): UpdateCount

        @Query("DELETE FROM entities")
        fun deleteAll(): UpdateCount
    }
    ```

    1.  Разворачивается в запрос:
        ```sql
        SELECT id, value1, value2, value3
        FROM entities
        WHERE id = :id
        ```
    2.  Разворачивается в запрос:
        ```sql
        SELECT id, value1, value2, value3
        FROM entities
        ```
    3.  Разворачивается в запрос:
        ```sql
        INSERT INTO entities(id, value1, value2, value3)
        VALUES (:entity.id, :entity.field1, :entity.value2, :entity.value3)
        ```
    4.  Разворачивается в запрос:
        ```sql
        UPDATE entities
        SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3
        WHERE id = :entity.id
        ```
    5.  Разворачивается в запрос:
        ```sql
        INSERT INTO entities(id, value1, value2, value3)
        VALUES (:entity.id, :entity.field1, :entity.value2, :entity.value3)
        ON CONFLICT (id) DO UPDATE
        SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3
        ```

#### Пример с составным идентификатором { #composite-example }

Пример репозитория с [составным идентификатором](#composite) и базовыми методами работы с сущностью:
он почти идентичен предыдущему, за исключением условий `WHERE` для поиска и удаления, для [Postgres SQL](https://postgrespro.com/docs/postgresql):

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Table("entities")
        record Entity(@Id @Embedded  EntityId id,
                      @Column("value1") int field1,
                      String value2,
                      @Nullable String value3) {

            public record EntityId(String code, String type) { }
        }

        @Query("SELECT %{return#selects} FROM %{return#table} WHERE %{id#where}") //(1)!
        @Nullable
        Entity findById(EntityId id);

        @Query("SELECT %{return#selects} FROM %{return#table}") //(2)!
        List<Entity> findAll();

        @Query("INSERT INTO %{entity#inserts}")  //(3)!
        UpdateCount insert(@Batch List<Entity> entity);

        @Query("UPDATE %{entity#table} SET %{entity#updates} WHERE %{entity#where = @id}")  //(4)!
        UpdateCount update(@Batch List<Entity> entity);

        @Query("INSERT INTO %{entity#inserts} ON CONFLICT (code, type) DO UPDATE SET %{entity#updates}")  //(5)!
        UpdateCount upsert(@Batch List<Entity> entity);

        @Query("DELETE FROM entities WHERE %{id#where}") //(6)!
        UpdateCount deleteById(EntityId id);

        @Query("DELETE FROM entities")
        UpdateCount deleteAll();
    }
    ```

    1.  Разворачивается в запрос:
        ```sql
        SELECT code, type, value1, value2, value3
        FROM entities
        WHERE code = :id.code AND type = :id.type
        ```
    2.  Разворачивается в запрос:
        ```sql
        SELECT code, type, value1, value2, value3
        FROM entities
        ```
    3.  Разворачивается в запрос:
        ```sql
        INSERT INTO entities(code, type, value1, value2, value3)
        VALUES (:entity.id.code, :entity.id.type, :entity.field1, :entity.value2, :entity.value3)
        ```
    4.  Разворачивается в запрос:
        ```sql
        UPDATE entities
        SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3
        WHERE code = :entity.id.code AND type = :entity.id.type
        ```
    5.  Разворачивается в запрос:
        ```sql
        INSERT INTO entities(code, type, value1, value2, value3)
        VALUES (:entity.id.code, :entity.id.type, :entity.field1, :entity.value2, :entity.value3)
        ON CONFLICT (code, type) DO UPDATE
        SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3
        ```
    6.  Разворачивается в запрос:
        ```sql
        DELETE FROM entities
        WHERE code = :id.code AND type = :id.type
        ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Table("entities")
        data class Entity(
            @field:Id @field:Embedded val id: EntityId,
            @field:Column("value1") val field1: Int,
            val value2: String,
            val value3: String?
        ) {

            data class EntityId(val code: String, val type: String)
        }

        @Query("SELECT %{return#selects} FROM %{return#table} WHERE %{id#where}") //(1)!
        fun findById(id: EntityId): Entity?

        @Query("SELECT %{return#selects} FROM %{return#table}") //(2)!
        fun findAll(): List<Entity>

        @Query("INSERT INTO %{entity#inserts}") //(3)!
        fun insert(@Batch entity: List<Entity>): UpdateCount

        @Query("UPDATE %{entity#table} SET %{entity#updates} WHERE %{entity#where = @id}") //(4)!
        fun update(@Batch entity: List<Entity>): UpdateCount

        @Query("INSERT INTO %{entity#inserts} ON CONFLICT (code, type) DO UPDATE SET %{entity#updates}") //(5)!
        fun upsert(@Batch entity: List<Entity>): UpdateCount

        @Query("DELETE FROM entities WHERE %{id#where}") //(6)!
        fun deleteById(id: EntityId): UpdateCount

        @Query("DELETE FROM entities")
        fun deleteAll(): UpdateCount
    }
    ```

    1.  Разворачивается в запрос:
        ```sql
        SELECT code, type, value1, value2, value3
        FROM entities
        WHERE code = :id.code AND type = :id.type
        ```
    2.  Разворачивается в запрос:
        ```sql
        SELECT code, type, value1, value2, value3
        FROM entities
        ```
    3.  Разворачивается в запрос:
        ```sql
        INSERT INTO entities(code, type, value1, value2, value3)
        VALUES (:entity.id.code, :entity.id.type, :entity.field1, :entity.value2, :entity.value3)
        ```
    4.  Разворачивается в запрос:
        ```sql
        UPDATE entities
        SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3
        WHERE code = :entity.id.code AND type = :entity.id.type
        ```
    5.  Разворачивается в запрос:
        ```sql
        INSERT INTO entities(code, type, value1, value2, value3)
        VALUES (:entity.id.code, :entity.id.type, :entity.field1, :entity.value2, :entity.value3)
        ON CONFLICT (code, type) DO UPDATE
        SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3
        ```
    6.  Разворачивается в запрос:
        ```sql
        DELETE FROM entities
        WHERE code = :id.code AND type = :id.type
        ```

#### Пример с наследованием { #inheritance-example }

Можно также создать абстрактный CRUD-репозиторий и затем использовать его через наследование для [Postgres SQL](https://postgrespro.com/docs/postgresql).
Макросы разрешают параметры типа родительского репозитория по типовым аргументам конкретного репозитория,
поэтому обобщённого родителя достаточно написать один раз:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface PostgresJdbcCrudRepository<K, V> extends JdbcRepository {

        @Query("SELECT %{return#selects} FROM %{return#table}")
        List<V> findAll();

        @Query("INSERT INTO %{entity#inserts}")
        UpdateCount insert(V entity);

        @Query("INSERT INTO %{entity#inserts}")
        UpdateCount insert(@Batch List<V> entity);

        @Query("UPDATE %{entity#table} SET %{entity#updates} WHERE %{entity#where = @id}")
        UpdateCount update(V entity);

        @Query("UPDATE %{entity#table} SET %{entity#updates} WHERE %{entity#where = @id}")
        UpdateCount update(@Batch List<V> entity);

        @Query("INSERT INTO %{entity#inserts} ON CONFLICT (%{entity#columns = @id}) DO UPDATE SET %{entity#updates}")
        UpdateCount upsert(V entity);

        @Query("INSERT INTO %{entity#inserts} ON CONFLICT (%{entity#columns = @id}) DO UPDATE SET %{entity#updates}")
        UpdateCount upsert(@Batch List<V> entity);

        @Query("DELETE FROM %{entity#table} WHERE %{entity#where = @id}")
        UpdateCount delete(V entity);

        @Query("DELETE FROM %{entity#table} WHERE %{entity#where = @id}")
        UpdateCount delete(@Batch List<V> entity);
    }

    @Repository
    public interface EntityRepository extends PostgresJdbcCrudRepository<String, Entity> {

        @Table("entities")
        record Entity(@Id String id,
                      @Column("value1") int field1,
                      String value2,
                      @Nullable String value3) {
        }

        @Query("DELETE FROM entities WHERE id = :id")
        UpdateCount deleteById(String id);

        @Query("DELETE FROM entities")
        UpdateCount deleteAll();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface PostgresJdbcCrudRepository<K, V> : JdbcRepository {

        @Query("SELECT %{return#selects} FROM %{return#table}")
        fun findAll(): List<V>

        @Query("INSERT INTO %{entity#inserts}")
        fun insert(entity: V): UpdateCount

        @Query("INSERT INTO %{entity#inserts}")
        fun insert(@Batch entity: List<V>): UpdateCount

        @Query("UPDATE %{entity#table} SET %{entity#updates} WHERE %{entity#where = @id}")
        fun update(entity: V): UpdateCount

        @Query("UPDATE %{entity#table} SET %{entity#updates} WHERE %{entity#where = @id}")
        fun update(@Batch entity: List<V>): UpdateCount

        @Query("INSERT INTO %{entity#inserts} ON CONFLICT (%{entity#columns = @id}) DO UPDATE SET %{entity#updates}")
        fun upsert(entity: V): UpdateCount

        @Query("INSERT INTO %{entity#inserts} ON CONFLICT (%{entity#columns = @id}) DO UPDATE SET %{entity#updates}")
        fun upsert(@Batch entity: List<V>): UpdateCount

        @Query("DELETE FROM %{entity#table} WHERE %{entity#where = @id}")
        fun delete(entity: V): UpdateCount

        @Query("DELETE FROM %{entity#table} WHERE %{entity#where = @id}")
        fun delete(@Batch entity: List<V>): UpdateCount
    }

    @Repository
    interface EntityRepository : PostgresJdbcCrudRepository<String, Entity> {

        @Table("entities")
        data class Entity(
            @field:Id val id: String,
            @field:Column("value1") val field1: Int,
            val value2: String,
            val value3: String?
        )

        @Query("DELETE FROM entities WHERE id = :id")
        fun deleteById(id: String): UpdateCount

        @Query("DELETE FROM entities")
        fun deleteAll(): UpdateCount
    }
    ```

## Телеметрия { #telemetry }

Все драйверы баз данных используют общий контракт телеметрии для логирования, метрик и трассировки запросов.
Конкретные параметры конфигурации (секция `telemetry { logging / metrics / tracing }`) описаны в документации
для каждого драйвера, например [JDBC](database-jdbc.md#configuration); этот раздел документирует только общие точки расширения,
которые находятся в `io.koraframework.database.common.telemetry`.

Телеметрию для пула соединений строит `DatabaseTelemetryFactory`:
`DatabaseTelemetry get(DatabaseTelemetryConfig config, String name, String dbType)`,
где `name` — имя пула соединений, а `dbType` — система базы данных, определённая по настройкам соединения.

Для каждого выполняемого запроса драйвер запрашивает у `DatabaseTelemetry#observe(QueryContext)` объект `DatabaseObservation`.
Выполняемый запрос описывается `QueryContext(queryId, sql, operation)`, где `queryId` — стабильный идентификатор запроса,
передаваемый в телеметрию, `sql` — итоговый текст запроса, а `operation` по умолчанию равно `db_query`.

`DatabaseObservation` расширяет общий контракт `Observation` и отмечает стадии запроса:

- `observeConnection()` — соединение получено;
- `observeStatement()` — запрос подготовлен и начинается выполнение, здесь же логируется начало запроса;
- `span()` — спан трассировки запроса;
- `observeError(Throwable)` — запрос завершился ошибкой;
- `end()` — запрос завершён, в этот момент записывается метрика и логируется завершение запроса.

Фабрика по умолчанию `DefaultDatabaseTelemetryFactory` объединяет `Tracer`, `MeterRegistry` и две необязательные вложенные фабрики:

- `DefaultDatabaseLoggerFactory` строит логгер, который пишет начало и завершение запроса (`logQueryBegin` / `logQueryEnd`)
  структурированным аргументом `sqlQuery` с именем пула, операцией, идентификатором запроса и временем обработки;
  полный текст `sql` пишется только при уровне `TRACE`, а упавший запрос логируется на уровне `WARN`;
- `DefaultDatabaseMetricsFactory` строит писателя метрик, который для каждого запроса записывает таймер `db.client.operation.duration`.

Если логирование, [метрики](metrics.md) и [трассировка](tracing.md) отключены в конфигурации целиком,
используется `NoopDatabaseTelemetry`, и телеметрия становится пустой операцией.

Помимо стандартных секций `logging`, `metrics` и `tracing`, общий `DatabaseTelemetryConfig` добавляет одну специфичную для баз данных опцию:

- `telemetry.metrics.driverMetrics` — регистрировать метрики собственного пула соединений драйвера (по умолчанию: `true`)

Обе вложенные фабрики являются необязательными зависимостями фабрики телеметрии по умолчанию, поэтому проще всего
настроить телеметрию, добавив свою вложенную фабрику в [граф приложения](container.md) — никакой аннотации переопределения не требуется:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends JdbcDatabaseModule {

        default DefaultDatabaseLoggerFactory databaseLoggerFactory() { //(1)!
            return new DefaultDatabaseLoggerFactory() {

                @Override
                public DefaultDatabaseLogger create(DefaultDatabaseTelemetry.TelemetryContext context) {
                    var logger = LoggerFactory.getLogger("my.database." + context.poolName());
                    return new DefaultDatabaseLogger(logger, context) { //(2)!

                        @Override
                        public void logQueryBegin(QueryContext query) {
                            this.logger.debug("Executing {}", query.queryId());
                        }
                    };
                }
            };
        }
    }
    ```

    1.  Фабрика `DatabaseTelemetryFactory` по умолчанию принимает `DefaultDatabaseLoggerFactory` и `DefaultDatabaseMetricsFactory` как необязательные зависимости и использует их для каждого пула соединений.
    2.  `DefaultDatabaseLogger` — обычный класс, поэтому переопределять нужно только те методы, которые действительно требуется изменить.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : JdbcDatabaseModule {

        fun databaseLoggerFactory(): DefaultDatabaseLoggerFactory { //(1)!
            return object : DefaultDatabaseLoggerFactory() {

                override fun create(context: DefaultDatabaseTelemetry.TelemetryContext): DefaultDatabaseLogger {
                    val logger = LoggerFactory.getLogger("my.database." + context.poolName())
                    return object : DefaultDatabaseLogger(logger, context) { //(2)!

                        override fun logQueryBegin(query: QueryContext) {
                            this.logger.debug("Executing {}", query.queryId())
                        }
                    }
                }
            }
        }
    }
    ```

    1.  Фабрика `DatabaseTelemetryFactory` по умолчанию принимает `DefaultDatabaseLoggerFactory` и `DefaultDatabaseMetricsFactory` как необязательные зависимости и использует их для каждого пула соединений.
    2.  `DefaultDatabaseLogger` — обычный класс, поэтому переопределять нужно только те методы, которые действительно требуется изменить.

`DatabaseModule` предоставляет фабрику по умолчанию как [компонент по умолчанию](container.md#component-override),
поэтому, если телеметрию нужно заменить целиком, объявите собственную `DatabaseTelemetryFactory` в
[графе приложения](container.md) — она возьмёт верх над той, что даёт модуль.
