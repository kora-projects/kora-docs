---
search:
  exclude: true
title: Интеграция с базой данных в Kora
summary: Learn how to integrate databases with Kora using JDBC and perform CRUD operations
tags: database, jdbc, crud, persistence
---

# Интеграция с базой данных в Kora { #database-integration-kora }

В этом руководстве рассматривается хранение данных в PostgreSQL с Kora JDBC. Вы узнаете, как интерфейсы репозиториев используют `@Repository` и `@Query`, как поля записей сопоставляются со столбцами
базы данных, как миграции Flyway создают схему и как JDBC-модуль Kora подключает пул соединений в граф приложения. Вы также увидите, как код сервисов и контроллеров может сохранять тот же вид API,
пока хранение данных переносится в настоящую базу данных.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java Database JDBC App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-database-jdbc-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin Database JDBC App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-database-jdbc-app).

## Что вы создадите { #youll-build }

Вы превратите пользовательский HTTP API в приложение с хранением данных в PostgreSQL:

- миграцию Flyway, которая создает таблицу `users`
- JDBC DAO-модель с явным сопоставлением столбцов
- интерфейс Kora `@Repository` с SQL-запросами для операций создания, чтения, получения списка, обновления и удаления
- реализацию репозитория с базой данных, подключенную к существующему сервисному слою
- HOCON-конфигурацию для пула соединений JDBC и миграций
- тесты на основе Testcontainers, которые проверяют хранение данных на настоящем PostgreSQL

## Что вам понадобится { #youll-need }

- JDK 17 или новее
- база данных PostgreSQL (или Docker)
- Gradle 7+
- текстовый редактор или среда разработки
- пройденное руководство [HTTP-сервер](http-server.md)

## Требования { #prerequisites }

!!! note "Обязательно: пройдите руководство по HTTP-серверу"

    Это руководство предполагает, что вы уже прошли руководство **[HTTP-сервер](http-server.md)** и у вас есть рабочий проект HTTP API с `UserController`, `UserService` и реализацией репозитория в памяти.

    Если вы еще не прошли руководство по HTTP-серверу, сначала сделайте это, потому что здесь хранение в памяти заменяется JDBC/PostgreSQL.

## Обзор { #overview }

Переход от хранения в памяти к [PostgreSQL](https://www.postgresql.org/docs/) меняет слой хранения данных, но не меняет публичный контракт API. Это важный промышленный шаблон: контроллеры и методы
сервисов могут сохранять тот же вид, пока реализация репозитория становится долговечной, транзакционной и основанной на настоящем SQL.

Руководство построено вокруг того же разделения, что использовалось в руководстве по HTTP-серверу: транспортный код остается в контроллере, поведение приложения остается в сервисе, а детали хранения
данных уходят за контракт репозитория.

### Как хранение меняет приложение { #persistence-changes-application }

Репозиторий в памяти полезен для обучения, потому что он не требует внешней настройки и позволяет легко запустить первый HTTP API. Но состояние в памяти исчезает при остановке процесса, не может
совместно использоваться несколькими экземплярами приложения и не дает гарантий базы данных, которые обычно нужны настоящим сервисам.

Приложение с базой данных добавляет новые задачи:

- данные должны переживать перезапуски приложения
- параллельные запросы могут читать и записывать одни и те же записи
- изменения схемы должны быть повторяемыми в разных средах
- запросы должны быть явными и безопасными
- тесты должны проверять поведение на настоящей семантике базы данных

Именно поэтому это руководство не просто «добавляет зависимость базы данных». Оно вводит полную границу хранения данных: схему, конфигурацию соединений, запросы репозитория, сопоставление строк,
сгенерированные реализации и тесты на основе контейнеров.

### PostgreSQL как источник истины { #postgresql-source-truth }

В этом руководстве PostgreSQL становится источником истины для пользовательских данных. Репозиторий больше не хранит пользователей в локальной карте; он читает и записывает строки в таблицу `users`.
Это меняет поведение во время выполнения в нескольких важных местах:

- созданные пользователи остаются доступны после перезапуска приложения
- несколько экземпляров приложения могут работать с одной базой данных
- ограничения базы данных могут защищать согласованность данных
- SQL-запросы точно определяют, как данные выбираются, вставляются, обновляются и удаляются

Сервисный слой не должен знать эти детали. Он все еще должен просить репозиторий создать, найти, перечислить, обновить или удалить пользователей. Репозиторий — это адаптер, который переводит эти
операции приложения в SQL.

### JDBC-репозитории в Kora { #jdbc-repositories-kora }

Подробную модель репозиториев, `@Repository`, `@Query` и правил преобразования строк смотрите в [документации JDBC](../documentation/database-jdbc.md) и [общей документации по базам данных](../documentation/database-common.md).

[JDBC](https://docs.oracle.com/javase/tutorial/jdbc/) — это стандартный Java API для доступа к реляционным базам данных. Сам по себе JDBC низкоуровневый: обычно нужно управлять соединениями,
подготавливать выражения, связывать параметры, выполнять запросы, обрабатывать наборы результатов и правильно закрывать ресурсы.

JDBC-репозитории Kora сохраняют явный SQL, но убирают большую часть повторяющегося шаблонного кода. Вы объявляете интерфейс репозитория, аннотируете методы SQL-запросами, а Kora генерирует реализацию.
Именованные SQL-параметры связываются с аргументами методов, а строки результатов сопоставляются с записями Java или классами данных Kotlin.

В этом руководстве рассматривается несколько основных идей репозитория:

- явный SQL через `@Query`
- именованные параметры вместо конкатенации строк
- DAO-модели с сопоставлениями `@Column`
- сгенерированные реализации репозиториев
- методы репозитория, которые соответствуют потребностям сервиса

Явный SQL используется намеренно. Он делает контракт доступа к данным простым для чтения, проверки и оптимизации. Сгенерированная реализация берет на себя связующий код фреймворка, а сам запрос
остается видимым в репозитории.

### Сущности и сопоставление строк { #dao-models }

HTTP DTO и строки базы данных не всегда одно и то же. DTO ответа описывает то, что возвращает API. DAO-модель описывает то, как данные хранятся и читаются из базы данных. В маленьких примерах они
могут выглядеть похоже, но четкое разделение помогает по мере роста систем.

Поскольку `UserRequest` и `UserResponse` по-прежнему являются HTTP JSON DTO, приложение сохраняет `@Json` на этих классах. Это позволяет Kora сгенерировать JSON-читатель и JSON-писатель для границы
API во время обычной обработки аннотаций, тогда как `UserDAO` использует аннотации базы данных для сопоставления строк.

Kora сопоставляет строки базы данных с записями или классами данных. Аннотации `@Column` делают сопоставление явным, что особенно полезно, когда имена полей Java и имена столбцов базы данных
используют разные соглашения. Например, в Java часто используется `createdAt`, а в SQL-схемах — `created_at`.

В этом руководстве сопоставление строк остается простым, чтобы главный урок был заметен: SQL-результаты превращаются в типизированные объекты приложения, а граница репозитория скрывает детали базы
данных от сервисного слоя.

### Схема и миграции { #schema-migrations }

Подробнее о миграциях, настройке Flyway и Liquibase смотрите в [документации по миграциям баз данных](../documentation/database-migration.md).

Приложению с базой данных нужен повторяемый способ создавать и развивать схему. Миграции [Flyway](https://documentation.red-gate.com/fd) дают такую историю. Каждая миграция — это версионированный
SQL-файл, а приложение может запускать миграции при старте до использования репозиториев. Это предотвращает расхождение схемы в стиле «у меня работает» и делает тесты проще для воспроизведения.

Миграции являются частью контракта приложения. Если репозиторий ожидает таблицу `users` с определенными столбцами, эта схема должна создаваться предсказуемо. Версионированные миграции делают изменения
схемы проверяемыми и повторяемыми для локальной разработки, CI, подготовительной среды и промышленной среды.

### Конфигурация запуска { #runtime-config }

JDBC также вводит инфраструктуру времени выполнения: драйвер PostgreSQL, пул соединений, учетные данные и URL базы данных. Kora подключает эти части через конфигурацию и модули. Граф приложения
владеет объектом базы данных, репозиторий зависит от него, а тесты могут переопределять значения соединения через Testcontainers.

Пул соединений важен, потому что приложения не должны открывать новое соединение с базой данных на каждый запрос. Пул управляет ограниченным набором переиспользуемых соединений, что повышает
производительность и защищает базу данных от неконтролируемого роста числа соединений.

Конфигурация важна, потому что URL базы данных и учетные данные отличаются между локальной разработкой, тестами и развернутыми средами. Kora держит эти значения вне кода и внедряет настроенный
компонент базы данных в граф.

### Тестирование хранения { #persistence-testing }

Архитектурный урок в том, что хранение данных должно быть заменяемым за стабильной границей сервиса. API может продолжать возвращать те же DTO, пока репозиторий переезжает из памяти в SQL и получает
долговечность, миграции и реалистичные интеграционные тесты.

Код базы данных по возможности нужно тестировать на настоящей базе данных. Заглушки не могут доказать, что синтаксис SQL верен, что миграции соответствуют ожиданиям репозитория или что сопоставление
строк работает. В этом руководстве используется [Testcontainers](https://java.testcontainers.org/), чтобы тесты могли автоматически запускать PostgreSQL и проверять поведение хранения данных в
изолированной среде.

Практический поток:

1. добавить зависимости JDBC, PostgreSQL и Flyway
2. добавить модули базы данных в приложение Kora
3. создать миграцию для таблицы `users`
4. определить DAO-записи и SQL-методы репозитория
5. подключить JDBC-репозиторий к сервисному слою
6. проверить хранение данных с помощью [Testcontainers](https://java.testcontainers.org/)

## Зависимости { #dependencies }

Теперь добавьте зависимости базы данных для поддержки PostgreSQL и JDBC:

===! ":fontawesome-brands-java: `Java`"

    Добавьте в блок `dependencies` файла `build.gradle`:

    ```groovy
    dependencies {
        // ... existing dependencies ...

        runtimeOnly("org.postgresql:postgresql:42.7.7")
        implementation("ru.tinkoff.kora:database-jdbc")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Добавьте в блок `dependencies` файла `build.gradle.kts`:

    ```kotlin
    dependencies {
        // ... existing dependencies ...

        runtimeOnly("org.postgresql:postgresql:42.7.7")
        implementation("ru.tinkoff.kora:database-jdbc")
    }
    ```

## Модули { #modules }

Обновите интерфейс Application и подключите модули JDBC и Flyway.

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/ru/tinkoff/kora/guide/databasejdbc/Application.java`:

    ```java
    package ru.tinkoff.kora.guide.databasejdbc;

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

    `src/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/Application.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasejdbc

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

## Сущность БД { #entity-db }

Замените старую модель хранения `User` в памяти на JDBC DAO-модель, которую используют сопоставления репозитория.

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/ru/tinkoff/kora/guide/databasejdbc/repository/UserDAO.java`:

    ```java
    package ru.tinkoff.kora.guide.databasejdbc.repository;

    import java.time.LocalDateTime;
    import ru.tinkoff.kora.database.common.annotation.Column;
    import ru.tinkoff.kora.database.jdbc.EntityJdbc;

    @EntityJdbc
    public record UserDAO(
            @Column("id") Long id,
            @Column("name") String name,
            @Column("email") String email,
            @Column("created_at") LocalDateTime createdAt) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/repository/UserDAO.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasejdbc.repository

    import java.time.LocalDateTime
    import ru.tinkoff.kora.database.common.annotation.Column
    import ru.tinkoff.kora.database.jdbc.EntityJdbc

    @EntityJdbc
    data class UserDAO(
        @field:Column("id") val id: Long,
        @field:Column("name") val name: String,
        @field:Column("email") val email: String,
        @field:Column("created_at") val createdAt: LocalDateTime,
    )
    ```

## Репозиторий { #repository }

На этом шаге удалите старый `InMemoryUserRepository` из руководства по HTTP-серверу и создайте настоящий JDBC-репозиторий с SQL-запросами.

Для `update` и `delete` используйте `UpdateCount`, чтобы сервисная логика могла решить, была ли строка действительно изменена или удалена.

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/ru/tinkoff/kora/guide/databasejdbc/repository/UserRepository.java`:

    ```java
    package ru.tinkoff.kora.guide.databasejdbc.repository;

    import java.util.List;
    import java.util.Optional;
    import ru.tinkoff.kora.database.common.UpdateCount;
    import ru.tinkoff.kora.database.common.annotation.Query;
    import ru.tinkoff.kora.database.common.annotation.Repository;
    import ru.tinkoff.kora.database.jdbc.JdbcRepository;

    @Repository
    public interface UserRepository extends JdbcRepository {

        @Query("SELECT id, name, email, created_at FROM users ORDER BY id")
        List<UserDAO> findAll();

        @Query("SELECT id, name, email, created_at FROM users WHERE id = :id")
        Optional<UserDAO> findById(Long id);

        @Query("INSERT INTO users(name, email) VALUES (:name, :email) RETURNING id")
        long save(String name, String email);

        @Query("UPDATE users SET name = :name, email = :email WHERE id = :id")
        UpdateCount update(Long id, String name, String email);

        @Query("DELETE FROM users WHERE id = :id")
        UpdateCount deleteById(Long id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/repository/UserRepository.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasejdbc.repository

    import ru.tinkoff.kora.database.common.UpdateCount
    import ru.tinkoff.kora.database.common.annotation.Query
    import ru.tinkoff.kora.database.common.annotation.Repository
    import ru.tinkoff.kora.database.jdbc.JdbcRepository

    @Repository
    interface UserRepository : JdbcRepository {

        @Query("SELECT id, name, email, created_at FROM users ORDER BY id")
        fun findAll(): List<UserDAO>

        @Query("SELECT id, name, email, created_at FROM users WHERE id = :id")
        fun findById(id: Long): UserDAO?

        @Query("INSERT INTO users(name, email) VALUES (:name, :email) RETURNING id")
        fun save(name: String, email: String): Long

        @Query("UPDATE users SET name = :name, email = :email WHERE id = :id")
        fun update(id: Long, name: String, email: String): UpdateCount

        @Query("DELETE FROM users WHERE id = :id")
        fun deleteById(id: Long): UpdateCount
    }
    ```

`@EntityJdbc` говорит Kora сгенерировать преобразователи JDBC напрямую для DAO-модели. Так генерация преобразователей остается явной и не появляются более медленные поздние раунды генерации, когда граф репозитория
впервые запрашивает преобразователь.

После компиляции Kora генерирует реализацию репозитория и преобразователь строк для этого интерфейса:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-database-jdbc-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/databasejdbc/repository/$UserRepository_Impl.java
    guides/guide-database-jdbc-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/databasejdbc/repository/$UserDAO_JdbcResultSetMapper.java
    guides/guide-database-jdbc-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/databasejdbc/repository/$UserDAO_JdbcRowMapper.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-database-jdbc-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/repository/$UserRepository_Impl.kt
    guides/kotlin/guide-kotlin-database-jdbc-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/repository/$UserDAO_JdbcResultSetMapper.kt
    guides/kotlin/guide-kotlin-database-jdbc-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/repository/$UserDAO_JdbcRowMapper.kt
    ```

Этот сокращенный фрагмент сгенерированного репозитория показывает, как именованные SQL-параметры становятся параметрами подготовленного JDBC-выражения:

===! ":fontawesome-brands-java: `Java`"

    ```java
    private static final QueryContext QUERY_CONTEXT_3 = new QueryContext(
          "INSERT INTO users(name, email) VALUES (:name, :email) RETURNING id",
          "INSERT INTO users(name, email) VALUES (?, ?) RETURNING id",
          "UserRepository.save"
        );

    @Override
    public long save(String name, String email) {
        var _ctxCurrent = ru.tinkoff.kora.common.Context.current();
        var _query = QUERY_CONTEXT_3;
        var _telemetry = this._connectionFactory.telemetry().createContext(_ctxCurrent, _query);
        var _conToUse = this._connectionFactory.currentConnection();
        Connection _conToClose;
        if (_conToUse == null) {
            _conToUse = this._connectionFactory.newConnection();
            _conToClose = _conToUse;
        } else {
            _conToClose = null;
        }
        try (_conToClose; var _stmt = _conToUse.prepareStatement(_query.sql())) {
            _stmt.setString(1, name);
            _stmt.setString(2, email);
            try (var _rs = _stmt.executeQuery()) {
                var _result = _result_mapper_3.apply(_rs);
                _telemetry.close(null);
                return _result;
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    private val _queryContext_3: QueryContext = QueryContext(
      "INSERT INTO users(name, email) VALUES (:name, :email) RETURNING id",
      "INSERT INTO users(name, email) VALUES (?, ?) RETURNING id",
      "UserRepository.save"
    )

    override fun save(name: String, email: String): Long {
      val _query = _queryContext_3
      val _ctxCurrent = Context.current()
      val _telemetry = _jdbcConnectionFactory.telemetry().createContext(_ctxCurrent, _query)
      var _conToUse = _jdbcConnectionFactory.currentConnection()
      val _conToClose = if (_conToUse == null) {
        _conToUse = _jdbcConnectionFactory.newConnection()
        _conToUse
      } else {
        null
      }
      try {
        _conToClose.use {
          _conToUse!!.prepareStatement(_query.sql()).use { _stmt ->
            _stmt.setString(1, name)
            _stmt.setString(2, email)
            _stmt.executeQuery().use { _rs ->
              val _result = _result_mapper_3.apply(_rs)
                ?: throw NullPointerException("Result mapping is expected non-null, but was null")
              _telemetry.close(null)
              return _result
            }
          }
        }
      } finally {
        _ctxCurrent.inject()
      }
    }
    ```

Этот фрагмент показывает конкретную работу фреймворка, скрытую за интерфейсом репозитория: связывание параметров, работу с соединениями, телеметрию запроса и сопоставление результата.

Этот сокращенный фрагмент сгенерированного преобразователя строк также показывает, почему явные имена `@Column` важны:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var _idColumn = _rs.findColumn("id");
    var _nameColumn = _rs.findColumn("name");
    var _emailColumn = _rs.findColumn("email");
    var _createdAtColumn = _rs.findColumn("created_at");

    Long id = _rs.getLong(_idColumn);
    String name = _rs.getString(_nameColumn);
    String email = _rs.getString(_emailColumn);
    LocalDateTime createdAt = _rs.getObject(_createdAtColumn, LocalDateTime.class);

    return new UserDAO(id, name, email, createdAt);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val _idx_id = _rs.findColumn("id")
    val _idx_name = _rs.findColumn("name")
    val _idx_email = _rs.findColumn("email")
    val _idx_createdAt = _rs.findColumn("created_at")

    var id: Long? = _rs.getLong(_idx_id)
    if (_rs.wasNull() || id == null) {
      throw NullPointerException("Required field id is not nullable but row has null")
    }
    var name: String? = _rs.getString(_idx_name)
    if (_rs.wasNull() || name == null) {
      throw NullPointerException("Required field name is not nullable but row has null")
    }
    var email: String? = _rs.getString(_idx_email)
    if (_rs.wasNull() || email == null) {
      throw NullPointerException("Required field email is not nullable but row has null")
    }
    var createdAt: LocalDateTime? = _rs.getObject(_idx_createdAt, LocalDateTime::class.java)
    if (_rs.wasNull() || createdAt == null) {
      throw NullPointerException("Required field created_at is not nullable but row has null")
    }

    val _result = UserDAO(id, name, email, createdAt)
    return _result
    ```

Это лучшее место для отладки связывания SQL и сопоставления строк, потому что здесь видно ровно то, что Kora скомпилировала из `@Repository`, `@Query` и `@Column`.

## Почему шаблон репозитория? { #repository-pattern }

Подход Kora к интеграции с базами данных делает упор на прямое использование SQL с интерфейсами репозиториев, а не на сложные системы объектно-реляционного сопоставления (ORM). Такое решение дает
заметные преимущества в производительности, сопровождаемости и контроле разработчика.

Шаблон репозитория в Kora:

Интерфейсы репозиториев служат чистым слоем абстракции между бизнес-логикой и кодом доступа к данным:

- Разделение интерфейсов: каждый репозиторий может сосредоточиться на конкретных бизнес-операциях и при необходимости работать с несколькими сущностями
- Внедрение зависимостей: репозитории автоматически внедряются как зависимости
- Тестируемость: репозитории легко подменять в модульных тестах
- Типобезопасность: проверка запросов и параметров во время компиляции

Почему SQL вместо сложных ORM?

Хотя ORM вроде Hibernate или JPA дают удобство, у них есть существенные недостатки, которых Kora избегает:

Преимущества производительности:

Прямой контроль SQL:

- Оптимизированные запросы: вы пишете ровно тот SQL, который нужен, без скрытых запросов и проблем N+1
- Предсказуемая производительность: нет неожиданной ленивой загрузки или сложной генерации запросов
- Возможности конкретной базы данных: можно использовать уникальные возможности и оптимизации вашей базы данных
- Планирование запросов: полный контроль над планами выполнения и стратегиями индексации

Без накладных расходов ORM:

- Без объектов-заместителей: прямой доступ к данным без оберток
- Без управления сессиями: нет сложного состояния сессии или стратегий сброса изменений
- Без ленивой загрузки: явный контроль над тем, когда и какие данные загружаются
- Минимальный расход памяти: нет обширных метаданных или слоев кэширования

Преимущества для разработчика:

Явное лучше неявного:

- Ясное намерение: SQL-запросы явные и самодокументируемые
- Отладка: фактические запросы к базе данных легко отлаживать и профилировать
- Сопровождение: изменения логики доступа к данным очевидны и прослеживаемы
- Кривая обучения: знание SQL применимо во всех проектах

Типобезопасность без магии:

- Проверка во время компиляции: параметры запросов проверяются при компиляции
- Поддержка среда разработки: полноценное автодополнение и поддержка рефакторинга для SQL
- Безопасность во время выполнения: нет отказов генерации запросов во время выполнения

Преимущества сопровождаемости:

Простая архитектура:

- Без сложных сопоставлений: нет XML, аннотаций или сложных связей сущностей
- Без головной боли с миграциями: нет сложностей генерации схемы или миграций
- Без конфликтов версий: нет проблем совместимости версий ORM
- Без привязки к поставщику: SQL работает с любыми поставщиками баз данных

Эволюционное проектирование:

- Постепенные изменения: запросы легко менять по мере развития требований
- Безопасный рефакторинг: изменения базы данных не ломают код приложения неожиданно
- Единообразие команды: все разработчики работают с одной SQL-парадигмой

Что предоставляет Kora:

- Управление соединениями: автоматический пул соединений и управление жизненным циклом
- Связывание параметров: типобезопасное связывание параметров с именованными параметрами
- Сопоставление результатов: автоматическое сопоставление результатов запросов с Java-объектами
- Поддержка транзакций: управление транзакциями через обработку методов
- Обработка ошибок: правильное преобразование исключений и очистка ресурсов
- Наблюдаемость: полноценные метрики, трассировка и структурированное журналирование для всех операций репозитория

Что контролируете вы:

- Оптимизация запросов: полный контроль над выполнением SQL и производительностью
- Проектирование схемы: прямое влияние на схему базы данных и индексацию
- Связи данных: явная обработка сложных связей данных
- Настройка производительности: тонкий контроль над выполнением запросов

Такой подход делает Kora особенно подходящей для корпоративных приложений, где производительность, сопровождаемость и контроль разработчика имеют первостепенное значение.

## Переработайте сервис { #refactor-service }

На этом шаге вы перерабатываете существующий `UserService` из руководства по HTTP-серверу.

Важные правила:

- Сохраните те же публичные контракты сервиса, которые использует `UserController`.
- Замените только внутренности хранения: используйте вызовы JDBC-репозитория вместо хранения в памяти.
- Оставьте `UserController` и его HTTP-контракты без изменений.
- При неправильном формате идентификатор в пути выбрасывайте `HttpServerResponseException` с `400`.
- При обновлении или удалении, когда ни одна строка не затронута, выбрасывайте `HttpServerResponseException` с `404`.

===! ":fontawesome-brands-java: Java"

    Обновите `src/main/java/ru/tinkoff/kora/guide/databasejdbc/service/UserService.java`:

    ```java
    package ru.tinkoff.kora.guide.databasejdbc.service;

    import java.time.LocalDateTime;
    import java.util.Comparator;
    import java.util.List;
    import java.util.Optional;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.databasejdbc.dto.UserRequest;
    import ru.tinkoff.kora.guide.databasejdbc.dto.UserResponse;
    import ru.tinkoff.kora.guide.databasejdbc.repository.UserDAO;
    import ru.tinkoff.kora.guide.databasejdbc.repository.UserRepository;
    import ru.tinkoff.kora.http.server.common.HttpServerResponseException;

    @Component
    public final class UserService {

        private final UserRepository userRepository;

        public UserService(UserRepository userRepository) {
            this.userRepository = userRepository;
        }

        public UserResponse createUser(UserRequest request) {
            var generatedId = userRepository.save(request.name(), request.email());
            return new UserResponse(String.valueOf(generatedId), request.name(), request.email(), LocalDateTime.now());
        }

        public Optional<UserResponse> getUser(String id) {
            return parseId(id).flatMap(userRepository::findById).map(this::toResponse);
        }

        public List<UserResponse> getUsers(int page, int size, String sort) {
            return userRepository.findAll().stream()
                    .map(this::toResponse)
                    .sorted(getComparator(sort))
                    .skip((long) page * size)
                    .limit(size)
                    .toList();
        }

        public UserResponse updateUser(String id, UserRequest request) {
            var parsedId = parseIdOrThrow(id);
            var updated = userRepository.update(parsedId, request.name(), request.email());
            if (updated.value() < 1) {
                throw HttpServerResponseException.of(404, "User not found");
            }
            return new UserResponse(String.valueOf(parsedId), request.name(), request.email(), LocalDateTime.now());
        }

        public void deleteUser(String id) {
            var parsedId = parseIdOrThrow(id);
            var deleted = userRepository.deleteById(parsedId);
            if (deleted.value() < 1) {
                throw HttpServerResponseException.of(404, "User not found");
            }
        }

        private long parseIdOrThrow(String id) {
            try {
                return Long.parseLong(id);
            } catch (NumberFormatException ignored) {
                throw HttpServerResponseException.of(400, "Invalid user id: " + id);
            }
        }

        private Optional<Long> parseId(String id) {
            try {
                return Optional.of(Long.parseLong(id));
            } catch (NumberFormatException ignored) {
                return Optional.empty();
            }
        }

        private UserResponse toResponse(UserDAO user) {
            return new UserResponse(String.valueOf(user.id()), user.name(), user.email(), user.createdAt());
        }

        private Comparator<UserResponse> getComparator(String sort) {
            return switch (sort.toLowerCase()) {
                case "name" -> Comparator.comparing(UserResponse::name);
                case "email" -> Comparator.comparing(UserResponse::email);
                case "createdat" -> Comparator.comparing(UserResponse::createdAt);
                default -> Comparator.comparing(UserResponse::name);
            };
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    Обновите `src/main/kotlin/ru/tinkoff/kora/guide/databasejdbc/service/UserService.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.databasejdbc.service

    import java.time.LocalDateTime
    import java.util.Comparator
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.databasejdbc.dto.UserRequest
    import ru.tinkoff.kora.guide.databasejdbc.dto.UserResponse
    import ru.tinkoff.kora.guide.databasejdbc.repository.UserDAO
    import ru.tinkoff.kora.guide.databasejdbc.repository.UserRepository
    import ru.tinkoff.kora.http.server.common.HttpServerResponseException

    @Component
    class UserService(private val userRepository: UserRepository) {

        fun createUser(request: UserRequest): UserResponse {
            val generatedId = userRepository.save(request.name, request.email)
            return UserResponse(generatedId.toString(), request.name, request.email, LocalDateTime.now())
        }

        fun getUser(id: String): UserResponse? =
            parseId(id)?.let { userRepository.findById(it) }?.let { toResponse(it) }

        fun getUsers(page: Int, size: Int, sort: String): List<UserResponse> =
            userRepository.findAll()
                .map { toResponse(it) }
                .sortedWith(getComparator(sort))
                .drop(page * size)
                .take(size)

        fun updateUser(id: String, request: UserRequest): UserResponse {
            val parsedId = parseIdOrThrow(id)
            val updated = userRepository.update(parsedId, request.name, request.email)
            if (updated.value() < 1) {
                throw HttpServerResponseException.of(404, "User not found")
            }
            return UserResponse(parsedId.toString(), request.name, request.email, LocalDateTime.now())
        }

        fun deleteUser(id: String) {
            val parsedId = parseIdOrThrow(id)
            val deleted = userRepository.deleteById(parsedId)
            if (deleted.value() < 1) {
                throw HttpServerResponseException.of(404, "User not found")
            }
        }

        private fun parseIdOrThrow(id: String): Long =
            id.toLongOrNull() ?: throw HttpServerResponseException.of(400, "Invalid user id: $id")

        private fun parseId(id: String): Long? = id.toLongOrNull()

        private fun toResponse(user: UserDAO): UserResponse =
            UserResponse(user.id.toString(), user.name, user.email, user.createdAt)

        private fun getComparator(sort: String): Comparator<UserResponse> = when (sort.lowercase()) {
            "name" -> compareBy { it.name }
            "email" -> compareBy { it.email }
            "createdat" -> compareBy { it.createdAt }
            else -> compareBy { it.name }
        }
    }
    ```

!!! note "Контроллер остается как есть"

    Не переписывайте `UserController` в этом руководстве. Оставьте контроллер из `http-server.md` без изменений, чтобы под капотом была заменена только реализация репозитория.

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
      poolName = "guide-jdbc" //(5)!
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
      poolName: "guide-jdbc" #(5)!
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

### Docker Compose { #docker-compose }

Создайте файл `docker-compose.yml` в каталоге модуля приложения:

```yaml
version: '3.8'
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

Запустите базу данных:

```bash
docker compose up -d
```

Это запустит PostgreSQL со следующими значениями:

- **База данных**: `postgres`
- **Имя пользователя**: `postgres`
- **Пароль**: `postgres`
- **Порт**: `5432`

### Миграция БД { #db-migration }

Используйте миграции Flyway вместо ручного выполнения SQL.

Создайте `src/main/resources/db/migration/V1__init_users.sql`:

```sql
CREATE TABLE IF NOT EXISTS users (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO users (name, email)
VALUES ('John Doe', 'john@example.com'),
       ('Jane Smith', 'jane@example.com')
ON CONFLICT (email) DO NOTHING;
```

`BIGINT GENERATED ALWAYS AS IDENTITY` — современный SQL-стандартный способ автоматически генерировать идентификатор в PostgreSQL.
Внутри PostgreSQL все равно использует объект последовательности, поэтому репозиторий `save(...)` может вернуть сгенерированный `id` через `RETURNING id`, а сервис может построить DTO ответа напрямую
из данных запроса и сгенерированного идентификатор.

## Запуск приложения { #run-app }

```bash
./gradlew run
```

## Проверка приложения { #check-app }

**Получить всех пользователей:**

```bash
curl http://localhost:8080/users
```

**Получить пользователя по идентификатору:**

```bash
curl http://localhost:8080/users/1
```

**Создать нового пользователя:**

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Bob Johnson", "email": "bob@example.com"}'
```

**Обновить пользователя:**

```bash
curl -X PUT http://localhost:8080/users/3 \
  -H "Content-Type: application/json" \
  -d '{"name": "Bob Smith", "email": "bob.smith@example.com"}'
```

**Удалить пользователя:**

```bash
curl -X DELETE http://localhost:8080/users/3
```

## Лучшие практики { #best-practices }

- Держите SQL в методах репозитория, а бизнес-решения — в сервисном слое.
- Используйте именованные параметры в запросах вместо конкатенации строк.
- Добавляйте `@Column` к каждому компоненту DAO-записи, чтобы сопоставления базы данных оставались явными.
- Держите миграции Flyway версионированными и фиксируйте их вместе с кодом, который от них зависит.
- Используйте `RETURNING` для сгенерированных идентификатор, а счетчики обновления и удаления — для решений о ненайденных записях.
- Изучайте сгенерированные реализации репозиториев, когда связывание SQL или сопоставление строк неочевидно.

## Итоги { #summary }

Вы заменили репозиторий в памяти из HTTP-руководства репозиторием на JDBC, добавили конфигурацию PostgreSQL и ввели миграции Flyway для повторяемой настройки схемы.

HTTP-контракт остается стабильным, пока слой хранения становится похожим на промышленный.
Вы также изучили сгенерированный JDBC-код, чтобы увидеть, как Kora превращает аннотации репозитория в подготовленные выражения, вызовы телеметрии и преобразователи строк.

## Ключевые понятия { #key-concepts }

- как объявляются JDBC-репозитории Kora
- как DAO-записи явно сопоставляют столбцы через `@Column`
- как миграции Flyway инициализируют схему
- как сервисная логика переводит результаты репозитория в HTTP-поведение
- как сгенерированные реализации репозиториев выполняют SQL и сопоставляют строки результата

## Устранение неполадок { #troubleshooting }

**Проблемы подключения:**

- Убедитесь, что PostgreSQL запущен и доступен из приложения.
- Проверьте значения `POSTGRES_JDBC_URL`, `POSTGRES_USER`, `POSTGRES_PASS`.
- Убедитесь, что файлы миграций находятся в `src/main/resources/db/migration`.

**Ошибки компиляции:**

- Убедитесь, что добавлены зависимости JDBC и PostgreSQL.
- Убедитесь, что обработка аннотаций включена для Kora.
- Проверьте совместимость версии Java (17+).

**Ошибки во время выполнения:**

- Проверьте журналы Flyway и подключение к базе данных.
- Убедитесь, что схема таблицы соответствует сопоставлениям столбцов `UserDAO`.
- Изучите журналы приложения для подробностей ошибок SQL/HTTP.

## Что дальше? { #whats-next }

- [Продвинутые шаблоны JDBC](database-jdbc-advanced.md), чтобы добавить вторую таблицу, транзакции, пользовательские преобразователи, макросы и проекции.
- [Интеграционное тестирование](testing-integration.md), чтобы проверять JDBC-репозитории, миграции и поведение PostgreSQL с Testcontainers.
- [Тестирование как черный ящик](testing-black-box.md), чтобы проверять упакованное HTTP-приложение сквозным образом.
- [База данных Cassandra](database-cassandra.md), если вы хотите сравнить тот же урок хранения данных с моделью распределенной базы данных.
- [Кэширование](cache.md), чтобы ускорить операции с частым чтением поверх базы данных.

## Помощь { #help }

Если вы столкнулись с проблемами:

- сравните с [Kora Java Database JDBC App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-database-jdbc-app) и [Kora Kotlin Database JDBC App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-database-jdbc-app)
- проверьте [документацию по базе данных JDBC](../documentation/database-jdbc.md)
- проверьте [общую документацию по базам данных](../documentation/database-common.md)
- проверьте [документацию по миграциям базы данных](../documentation/database-migration.md)
