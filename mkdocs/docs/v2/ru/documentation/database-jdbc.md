---
description: "Explains Kora JDBC repositories, the jdbc configuration section, Hikari pool tuning, result and parameter mapping, generated identifiers, manual queries built with JdbcQuery, transactions and isolation levels. Use when working with @Repository, @Query, @EntityJdbc, @Table, @Id, @Column, @Batch, JdbcDatabaseModule."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora JDBC repositories, the jdbc configuration section, Hikari pool tuning, result and parameter mapping, generated identifiers, manual queries and transactions; key triggers include @Repository, @Query, @EntityJdbc, @Table, @Id, @Column, @Batch, JdbcDatabaseModule, JdbcRepository, JdbcExecutor, JdbcQuery, UncheckedSqlException."
---

Модуль предоставляет реализацию репозитория на основе [JDBC](https://proselyte.net/tutorials/jdbc/introduction/) для
работы с реляционными базами данных и использует [Hikari](https://github.com/brettwooldridge/HikariCP) для управления пулом
соединений.
Вы описываете интерфейс репозитория и `SQL`-запросы с помощью `@Repository` и `@Query`, а `Kora` генерирует реализацию,
которая получает соединение из пула, связывает параметры, читает результат и участвует в транзакциях.

Общие правила для отображений, `@Repository`, `@Query`, `@Batch`, `UpdateCount`, макросов, ручных запросов и других механизмов
репозитория описаны в разделе [Общие правила работы с базами данных](database-common.md).

Если нужен пошаговый разбор перед справочным описанием, смотрите [База данных JDBC](../guides/database-jdbc.md) и [Продвинутая база данных JDBC](../guides/database-jdbc-advanced.md).

## Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:database-jdbc"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends JdbcDatabaseModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:database-jdbc")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : JdbcDatabaseModule
    ```

Также **требуется предоставить** реализацию драйвера базы данных как зависимость.

Модуль регистрирует пул соединений как компонент `JdbcDataSource`. Он реализует `JdbcExecutor`,
поэтому репозитории получают его автоматически, и оборачивает `javax.sql.DataSource`,
поэтому обычный `javax.sql.DataSource` можно внедрить в свои компоненты, если его требует сторонняя библиотека.

## Конфигурация { #configuration }

Основные параметры конфигурации JDBC читаются из секции `jdbc`:

===! ":material-code-json: `Hocon`"

    ```javascript
    jdbc {
        jdbcUrl = "jdbc:postgresql://localhost:5432/postgres" //(1)!
        username = "postgres" //(2)!
        password = "postgres" //(3)!
        poolName = "kora" //(4)!
        maxPoolSize = 10 //(5)!
    }
    ```

    1.  `JDBC URL` для подключения к базе данных (`обязательный`, без значения по умолчанию)
    2.  Имя пользователя для подключения (`обязательный`, без значения по умолчанию)
    3.  Пароль пользователя для подключения (`обязательный`, без значения по умолчанию)
    4.  Имя пула соединений `Hikari` (`обязательный`, без значения по умолчанию)
    5.  Максимальный размер пула соединений `Hikari` (по умолчанию: `10`)

=== ":simple-yaml: `YAML`"

    ```yaml
    jdbc:
      jdbcUrl: "jdbc:postgresql://localhost:5432/postgres" #(1)!
      username: "postgres" #(2)!
      password: "postgres" #(3)!
      poolName: "kora" #(4)!
      maxPoolSize: 10 #(5)!
    ```

    1.  `JDBC URL` для подключения к базе данных (`обязательный`, без значения по умолчанию)
    2.  Имя пользователя для подключения (`обязательный`, без значения по умолчанию)
    3.  Пароль пользователя для подключения (`обязательный`, без значения по умолчанию)
    4.  Имя пула соединений `Hikari` (`обязательный`, без значения по умолчанию)
    5.  Максимальный размер пула соединений `Hikari` (по умолчанию: `10`)

??? note "Полная конфигурация"

    Пример полной конфигурации, описанной в классе `JdbcDatabaseConfig` (указаны примеры значений или значения по умолчанию):

    ===! ":material-code-json: `Hocon`"

        ```javascript
        jdbc {
            jdbcUrl = "jdbc:postgresql://localhost:5432/postgres" //(1)!
            username = "postgres" //(2)!
            password = "postgres" //(3)!
            schema = "public" //(4)!
            poolName = "kora" //(5)!
            maxPoolSize = 10 //(6)!
            minIdle = 0 //(7)!
            connectionTimeout = "10s" //(8)!
            validationTimeout = "5s" //(9)!
            idleTimeout = "10m" //(10)!
            maxLifetime = "15m" //(11)!
            leakDetectionThreshold = "0s" //(12)!
            initializationFailTimeout = "10s" //(13)!
            readinessProbe = false //(14)!
            dsProperties { //(15)!
                "hostRecheckSeconds": "2"
            }
            telemetry {
                logging {
                    enabled = false //(16)!
                }
                metrics {
                    enabled = false //(17)!
                    driverMetrics = true //(18)!
                    slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(19)!
                    tags = { // (20)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
                tracing {
                    enabled = true //(21)!
                    attributes = { // (22)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
            }
        }
        ```

        1.  `JDBC URL` для подключения к базе данных (`обязательный`, без значения по умолчанию)
        2.  Имя пользователя для подключения (`обязательный`, без значения по умолчанию)
        3.  Пароль пользователя для подключения (`обязательный`, без значения по умолчанию)
        4.  Схема базы данных для подключения (опциональный, без значения по умолчанию)
        5.  Имя пула соединений `Hikari` (`обязательный`, без значения по умолчанию)
        6.  Максимальный размер пула соединений `Hikari` (по умолчанию: `10`)
        7.  Минимальное количество простаивающих готовых соединений в пуле `Hikari` (по умолчанию: `0`)
        8.  Максимальное время ожидания соединения из пула `Hikari` (по умолчанию: `10s`)
        9.  Максимальное время проверки соединения `Hikari` (по умолчанию: `5s`)
        10. Максимальное время простоя соединения `Hikari` (по умолчанию: `10m`)
        11. Максимальное время жизни соединения `Hikari` (по умолчанию: `15m`)
        12. Время, после которого занятое соединение считается возможной утечкой (по умолчанию: `0s`)
        13. Максимальное время ожидания проверки соединения при старте сервиса. Если параметр не указан, сервис стартует, не обращаясь к базе данных (опциональный, без значения по умолчанию)
        14. Включать ли [проверку готовности](probes.md#readiness) для соединения с базой данных (по умолчанию: `false`)
        15. Дополнительные параметры `JDBC`-соединения, передаваемые в `dataSourceProperties` пула `Hikari` (по умолчанию: `{}`)
        16. Включает логирование модуля (по умолчанию: `false`)
        17. Включает метрики модуля (по умолчанию: `false`)
        18. Публиковать ли собственные метрики пула `Hikari`: размер пула, время получения соединения и прочие (по умолчанию: `true`)
        19. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик в миллисекундах (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
        20. Настройка тегов метрик (по умолчанию: `{}`)
        21. Включает трассировку модуля (по умолчанию: `true`)
        22. Настройка атрибутов трассировки (по умолчанию: `{}`)

    === ":simple-yaml: `YAML`"

        ```yaml
        jdbc:
          jdbcUrl: "jdbc:postgresql://localhost:5432/postgres" #(1)!
          username: "postgres" #(2)!
          password: "postgres" #(3)!
          schema: "public" #(4)!
          poolName: "kora" #(5)!
          maxPoolSize: 10 #(6)!
          minIdle: 0 #(7)!
          connectionTimeout: "10s" #(8)!
          validationTimeout: "5s" #(9)!
          idleTimeout: "10m" #(10)!
          maxLifetime: "15m" #(11)!
          leakDetectionThreshold: "0s" #(12)!
          initializationFailTimeout: "10s" #(13)!
          readinessProbe: false #(14)!
          dsProperties: #(15)!
            hostRecheckSeconds: "2"
          telemetry:
            logging:
              enabled: false #(16)!
            metrics:
              enabled: false #(17)!
              driverMetrics: true #(18)!
              slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(19)!
              tags: #(20)!
                key1: value1
                key2: value2
            tracing:
              enabled: true #(21)!
              attributes: #(22)!
                key1: value1
                key2: value2
        ```

        1.  `JDBC URL` для подключения к базе данных (`обязательный`, без значения по умолчанию)
        2.  Имя пользователя для подключения (`обязательный`, без значения по умолчанию)
        3.  Пароль пользователя для подключения (`обязательный`, без значения по умолчанию)
        4.  Схема базы данных для подключения (опциональный, без значения по умолчанию)
        5.  Имя пула соединений `Hikari` (`обязательный`, без значения по умолчанию)
        6.  Максимальный размер пула соединений `Hikari` (по умолчанию: `10`)
        7.  Минимальное количество простаивающих готовых соединений в пуле `Hikari` (по умолчанию: `0`)
        8.  Максимальное время ожидания соединения из пула `Hikari` (по умолчанию: `10s`)
        9.  Максимальное время проверки соединения `Hikari` (по умолчанию: `5s`)
        10. Максимальное время простоя соединения `Hikari` (по умолчанию: `10m`)
        11. Максимальное время жизни соединения `Hikari` (по умолчанию: `15m`)
        12. Время, после которого занятое соединение считается возможной утечкой (по умолчанию: `0s`)
        13. Максимальное время ожидания проверки соединения при старте сервиса. Если параметр не указан, сервис стартует, не обращаясь к базе данных (опциональный, без значения по умолчанию)
        14. Включать ли [проверку готовности](probes.md#readiness) для соединения с базой данных (по умолчанию: `false`)
        15. Дополнительные параметры `JDBC`-соединения, передаваемые в `dataSourceProperties` пула `Hikari` (по умолчанию: `{}`)
        16. Включает логирование модуля (по умолчанию: `false`)
        17. Включает метрики модуля (по умолчанию: `false`)
        18. Публиковать ли собственные метрики пула `Hikari`: размер пула, время получения соединения и прочие (по умолчанию: `true`)
        19. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик в миллисекундах (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
        20. Настройка тегов метрик (по умолчанию: `{}`)
        21. Включает трассировку модуля (по умолчанию: `true`)
        22. Настройка атрибутов трассировки (по умолчанию: `{}`)

### Настройка пула { #pool-customization }

Ключи конфигурации покрывают те настройки `Hikari`, которые нужны большинству сервисов.
Если требуется настройка, которой нет в `JdbcDatabaseConfig`, предоставьте компонент `Configurer<HikariConfig>`.
`Kora` вызывает его с уже собранным из конфигурации `HikariConfig` непосредственно перед созданием пула,
поэтому ваш компонент правит только то, что ему нужно.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class HikariConfigurer implements Configurer<HikariConfig> {

        @Override
        public HikariConfig configure(HikariConfig config) {
            config.setTransactionIsolation("TRANSACTION_REPEATABLE_READ"); //(1)!
            return config;
        }
    }
    ```

    1.  Уровень изоляции по умолчанию для всех соединений пула, смотрите также [Уровень изоляции](#isolation)

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class HikariConfigurer : Configurer<HikariConfig> {

        override fun configure(config: HikariConfig): HikariConfig {
            config.transactionIsolation = "TRANSACTION_REPEATABLE_READ" //(1)!
            return config
        }
    }
    ```

    1.  Уровень изоляции по умолчанию для всех соединений пула, смотрите также [Уровень изоляции](#isolation)

### Дополнительные источники данных { #additional-data-sources }

Сервис может одновременно работать с несколькими базами данных. `JdbcDatabaseModule` объявляет источник данных
по умолчанию поверх секции конфигурации `jdbc`, а каждый дополнительный источник данных объявляется как
фабричный модуль со своим тегом и своей секцией конфигурации:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends JdbcDatabaseModule {

        final class Analytics { } //(1)!

        @Tag(Analytics.class)
        @FactoryModule //(2)!
        default JdbcDatabaseFactoryModule analyticsDatabase() {
            return new JdbcDatabaseFactoryModule("analyticsJdbc"); //(3)!
        }
    }
    ```

    1.  Класс-маркер, который идентифицирует этот источник данных в [графе приложения](container.md)
    2.  Тег фабричного модуля переносится на все создаваемые им компоненты, поэтому пул аналитики регистрируется как `@Tag(Analytics.class) JdbcDataSource`
    3.  Секция конфигурации, которую читает этот источник данных, описана тем же `JdbcDatabaseConfig`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : JdbcDatabaseModule {

        class Analytics //(1)!

        @Tag(Analytics::class)
        @FactoryModule //(2)!
        fun analyticsDatabase(): JdbcDatabaseFactoryModule {
            return JdbcDatabaseFactoryModule("analyticsJdbc") //(3)!
        }
    }
    ```

    1.  Класс-маркер, который идентифицирует этот источник данных в [графе приложения](container.md)
    2.  Тег фабричного модуля переносится на все создаваемые им компоненты, поэтому пул аналитики регистрируется как `@Tag(Analytics::class) JdbcDataSource`
    3.  Секция конфигурации, которую читает этот источник данных, описана тем же `JdbcDatabaseConfig`

Репозиторий указывает на источник данных, отличный от основного, через атрибут `executorTag` аннотации `@Repository`.
Репозитории без этого атрибута используют источник данных по умолчанию из секции `jdbc`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository(executorTag = Application.Analytics.class)
    public interface AnalyticsRepository extends JdbcRepository {

        @Query("SELECT count(*) FROM events WHERE type = :type")
        long countByType(String type);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository(executorTag = Application.Analytics::class)
    interface AnalyticsRepository : JdbcRepository {

        @Query("SELECT count(*) FROM events WHERE type = :type")
        fun countByType(type: String): Long
    }
    ```

## Использование { #usage }

Репозиторий `JDBC` объявляется как интерфейс, помеченный аннотацией `@Repository`, и должен наследовать `JdbcRepository`.
Каждый метод, помеченный `@Query`, содержит обычный `SQL`-запрос. Параметры метода связываются по имени с помощью
синтаксиса `:parameter`, а к полям объекта можно обращаться как `:entity.field`.

Отображения описываются с помощью [общих аннотаций баз данных](database-common.md) и помечаются `@EntityJdbc`,
чтобы `Kora` сгенерировала отображатель на этапе компиляции (см. [Отображение](#view)):

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

    1.  Использует макрос `%{return#selects}` и `%{return#table}`. Разворачивается в запрос:
        ```sql
        SELECT id, name, description
        FROM entities
        WHERE id = :id
        ```
        Метод использует макросы для `SELECT`. Подробнее: [Общие правила работы с базами данных — Макросы](database-common.md#macros)
    2.  Поля перечислены вручную без использования макросов — это допустимо, но требует поддержки при изменении отображения.
    3.  Использует макрос `%{entity#inserts}`. Разворачивается в запрос:
        ```sql
        INSERT INTO entities(id, name, description)
        VALUES(:entity.id, :entity.name, :entity.description)
        ```
        Метод использует макросы для `INSERT`. Подробнее: [Общие правила работы с базами данных — Макросы](database-common.md#macros)

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

        @Query("INSERT INTO %{entity#inserts}") //(3)!
        fun insert(entity: Entity): UpdateCount
    }
    ```

    1.  Использует макрос `%{return#selects}` и `%{return#table}`. Разворачивается в запрос:
        ```sql
        SELECT id, name, description
        FROM entities
        WHERE id = :id
        ```
        Метод использует макросы для `SELECT`. Подробнее: [Общие правила работы с базами данных — Макросы](database-common.md#macros)
    3.  Использует макрос `%{entity#inserts}`. Разворачивается в запрос:
        ```sql
        INSERT INTO entities(id, name, description)
        VALUES(:entity.id, :entity.name, :entity.description)
        ```
        Метод использует макросы для `INSERT`. Подробнее: [Общие правила работы с базами данных — Макросы](database-common.md#macros)

`SQL` остается под контролем разработчика: вы можете использовать специфичные для базы данных возможности, тогда как `Kora`
берет на себя только безопасное связывание параметров, выполнение запроса и отображение результата.
Общие правила для отображений, `@Table`, `@Column`, `@Id`, `@Embedded`, `@Batch` и макросов описаны в разделе
[Общие правила работы с базами данных](database-common.md#macros).

**Связывание параметров:** Kora выполняет типизированное внедрение аргументов в SQL-запрос на этапе компиляции.
Параметры запроса (например, `:id`, `:entity.name`) заменяются в сгенерированном коде на соответствующие вызовы `PreparedStatement`.
Например, для параметра `String name` будет сгенерировано что-то вроде `statement.setString(1, name)`, где индекс соответствует порядку параметра в запросе.
Это обеспечивает безопасность (защита от SQL-инъекций) и производительность (использование подготовленных запросов).

**Отсутствие значения:** в `Java` отсутствие значения помечается аннотацией [JSpecify](https://jspecify.dev) `org.jspecify.annotations.Nullable`,
в `Kotlin` это выражается типом возвращаемого значения `T?`.
Если метод не помечен как допускающий отсутствие значения, а отображатель все же вернул `null`,
сгенерированный код завершается с `NullPointerException` и сообщением `Result mapping is expected non-null, but was null`.

**Ошибки:** исключение `java.sql.SQLException` от драйвера никогда не покидает метод репозитория как проверяемое.
Оно оборачивается в непроверяемое `UncheckedSqlException` из пакета `io.koraframework.database.jdbc.exception`,
а исходное исключение доступно через `getCause()`.

## Отображение { #mapping }

Вы можете переопределить отображение различных частей [отображения](database-common.md), результата запроса и параметров запроса.
Для этого `Kora` предоставляет несколько интерфейсов-отображателей.

Класс-отображатель, указанный в `@Mapping`, `Kora` создает самостоятельно, если он `final`
(классы `Kotlin` являются final, если не объявлены как `open`) и имеет публичный конструктор без аргументов.
Такой отображатель **не** нужно помечать аннотацией `@Component`.
Отображатель с зависимостями в конструкторе, наоборот, разрешается из [графа приложения](container.md),
поэтому он должен быть объявлен как `@Component` либо предоставлен через `@Module`.

### Результат { #result }

Используйте `JdbcResultSetMapper<T>`, когда нужно вручную отобразить весь `ResultSet`.
Такой отображатель получает весь результат запроса и сам решает, сколько строк прочитать и что вернуть.

===! ":fontawesome-brands-java: `Java`"

    ```java
    final class ResultMapper implements JdbcResultSetMapper<UUID> {

        @Override
        public UUID apply(ResultSet rs) throws SQLException {
            // mapping code
        }
    }

    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Mapping(ResultMapper.class)
        @Query("SELECT id FROM entities")
        List<UUID> getIds();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class ResultMapper : JdbcResultSetMapper<UUID> {

        override fun apply(rs: ResultSet): UUID {
            // mapping code
        }
    }

    @Repository
    interface EntityRepository : JdbcRepository {

        @Mapping(ResultMapper::class)
        @Query("SELECT id FROM entities")
        fun getIds(): List<UUID>
    }
    ```

`JdbcResultSetMapper` также предоставляет статические методы `singleResultSetMapper`, `listResultSetMapper`
и `optionalResultSetMapper`, которые строят отображатель всего `ResultSet` из `JdbcRowMapper<T>`.

#### Отображение { #view }

`Kora` генерирует отображатели результата для ваших типов на этапе компиляции, и чтобы понять, для каких типов их
генерировать, ей нужна аннотация `@EntityJdbc` из пакета `io.koraframework.database.jdbc.annotation`.
Помечайте ею каждый тип, который возвращается из метода репозитория, включая тип идентификатора
метода с [`@Id`](#generated-identifier):

===! ":fontawesome-brands-java: `Java`"

    ```java
    @EntityJdbc
    public record Entity(String id, String name) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @EntityJdbc
    data class Entity(val id: String, val name: String)
    ```

Без этой аннотации `Kora` нечего использовать для построения `JdbcResultSetMapper` / `JdbcRowMapper`,
и сборка [графа приложения](container.md) падает с неразрешенной зависимостью-отображателем —
если только вы не предоставите отображатель сами через [`@Mapping`](#result).
Типы, которые встречаются только как поля [`@Embedded`](database-common.md#embedded-fields) другого отображения,
разворачиваются в объемлющее отображение и своей аннотации не требуют,
но пометить их тоже стоит: тогда отображение не сломается, когда такой тип станет самостоятельным результатом запроса.

Встроенным типам вроде `long` или `String` ничего не нужно: модуль предоставляет для них
отображатели строк, столбцов и параметров из коробки, см. [Поддерживаемые типы](#supported-types).

### Строка { #row }

Используйте `JdbcRowMapper<T>`, когда нужно вручную отобразить одну строку.
Учитывайте, что в `JDBC` индексы столбцов в `ResultSet` начинаются с `1`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    final class RowMapper implements JdbcRowMapper<UUID> {

        @Override
        public UUID apply(ResultSet rs) throws SQLException {
            return UUID.fromString(rs.getString(1));
        }
    }

    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Mapping(RowMapper.class)
        @Query("SELECT id FROM entities")
        List<UUID> findAll();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class RowMapper : JdbcRowMapper<UUID> {

        override fun apply(rs: ResultSet): UUID {
            return UUID.fromString(rs.getString(1))
        }
    }

    @Repository
    interface EntityRepository : JdbcRepository {

        @Mapping(RowMapper::class)
        @Query("SELECT id FROM entities")
        fun findAll(): List<UUID>
    }
    ```

`JdbcRowMapper<T>` достаточно для любой формы результата: `Kora` сама оборачивает его в `singleResultSetMapper`,
`optionalResultSetMapper` или `listResultSetMapper` в зависимости от того, возвращает ли метод
`T`, `Optional<T>` или `List<T>`.

### Столбец { #column }

Используйте `JdbcResultColumnMapper<T>`, когда нужно вручную отобразить значение одного столбца:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class ColumnMapper implements JdbcResultColumnMapper<UUID> {

        @Override
        public UUID apply(ResultSet row, int index) throws SQLException {
            return UUID.fromString(row.getString(index));
        }
    }

    @EntityJdbc
    @Table("entities")
    public record Entity(@Mapping(ColumnMapper.class) @Id UUID id, String name) { }

    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("SELECT id, name FROM entities")
        List<Entity> findAll();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class ColumnMapper : JdbcResultColumnMapper<UUID> {

        override fun apply(row: ResultSet, index: Int): UUID {
            return UUID.fromString(row.getString(index))
        }
    }

    @EntityJdbc
    @Table("entities")
    data class Entity(
        @field:Id @Mapping(ColumnMapper::class) val id: UUID,
        val name: String
    )

    @Repository
    interface EntityRepository : JdbcRepository {

        @Query("SELECT id, name FROM entities")
        fun findAll(): List<Entity>
    }
    ```

### Параметр { #parameter }

Используйте `JdbcParameterColumnMapper<T>`, когда нужно вручную отобразить значение параметра запроса.
Контракт объявляет значение как допускающее `null`, поэтому отображатель отвечает и за связывание `NULL`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class ParameterMapper implements JdbcParameterColumnMapper<UUID> {

        @Override
        public void set(PreparedStatement stmt, int index, @Nullable UUID value) throws SQLException {
            if (value == null) {
                stmt.setNull(index, Types.VARCHAR);
            } else {
                stmt.setString(index, value.toString());
            }
        }
    }

    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("SELECT id, name FROM entities WHERE id = :id")
        List<Entity> findById(@Mapping(ParameterMapper.class) UUID id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class ParameterMapper : JdbcParameterColumnMapper<UUID> {

        override fun set(stmt: PreparedStatement, index: Int, value: UUID?) {
            if (value == null) {
                stmt.setNull(index, Types.VARCHAR)
            } else {
                stmt.setString(index, value.toString())
            }
        }
    }

    @Repository
    interface EntityRepository : JdbcRepository {

        @Query("SELECT id, name FROM entities WHERE id = :id")
        fun findById(@Mapping(ParameterMapper::class) id: UUID): List<Entity>
    }
    ```

!!! warning "Kotlin"

    Контракты отображателей размечены [JSpecify](https://jspecify.dev), поэтому отображаемое значение в контракте
    допускает `null`. Переопределение в `Kotlin` обязано объявлять его как `T?` —
    `override fun set(stmt: PreparedStatement, index: Int, value: UUID?)`.
    Объявление параметра непустым не компилируется.

В `Java` аннотация `org.jspecify.annotations.Nullable` применяется к типу, поэтому важна её позиция.
Для вложенного типа аннотация ставится перед вложенной частью имени:
`void set(PreparedStatement stmt, int index, Entity.@Nullable Status value)`.

### Поддерживаемые типы { #supported-types }

??? abstract "Список поддерживаемых типов аргументов/возвращаемых значений из коробки"

    Эти типы выбраны потому, что поддерживаются большинством популярных баз данных.
    `Kora` предоставляет для них встроенные отображатели строк, столбцов и параметров.

    * void
    * boolean / Boolean
    * byte / Byte
    * short / Short
    * int / Integer
    * long / Long
    * double / Double
    * float / Float
    * byte[]
    * String
    * BigDecimal
    * UUID
    * LocalDate
    * LocalTime
    * LocalDateTime
    * OffsetTime
    * OffsetDateTime

    Поля отображения без явного `@Mapping` читаются и записываются встроенными вызовами `ResultSet` / `PreparedStatement`
    для `boolean` / `Boolean`, `short` / `Short`, `int` / `Integer`, `long` / `Long`, `double` / `Double`,
    `float` / `Float`, `byte[]`, `String`, `BigDecimal`, `LocalDate` и `LocalDateTime`.
    Для остальных типов используются встроенные отображатели `JdbcResultColumnMapper<T>` / `JdbcParameterColumnMapper<T>`
    либо объявляются собственные отображатели.

## Выборка по списку { #select-by-list }

Иногда требуется выбрать строки по списку значений.
На уровне `JDBC` такие параметры должен готовить драйвер отдельно, потому что длина списка заранее неизвестна.
`Kora` старается выполнять отображения на этапе компиляции и не переписывает `SQL` во время выполнения,
поэтому такие параметры требуют собственного отображателя.

`Kora` не предоставляет такое отображение параметра из коробки, но добавить его несложно.
Пример ниже показывает `Postgres` через `JDBC Array`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class ListOfStringJdbcParameterMapper implements JdbcParameterColumnMapper<List<String>> {

        @Override
        public void set(PreparedStatement stmt, int index, @Nullable List<String> value) throws SQLException {
            if (value == null) {
                stmt.setNull(index, Types.ARRAY);
                return;
            }

            String[] typedArray = value.toArray(String[]::new);
            Array sqlArray = stmt.getConnection().createArrayOf("VARCHAR", typedArray);
            stmt.setArray(index, sqlArray);
        }
    }

    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("SELECT id, name FROM entities WHERE id = ANY(:ids)")
        List<Entity> findAllByIds(@Mapping(ListOfStringJdbcParameterMapper.class) List<String> ids);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class ListOfStringJdbcParameterMapper : JdbcParameterColumnMapper<List<String>> {

        override fun set(stmt: PreparedStatement, index: Int, value: List<String>?) {
            if (value == null) {
                stmt.setNull(index, Types.ARRAY)
                return
            }

            stmt.setArray(index, stmt.connection.createArrayOf("VARCHAR", value.toTypedArray()))
        }
    }

    @Repository
    interface EntityRepository : JdbcRepository {

        @Query("SELECT id, name FROM entities WHERE id = ANY(:ids)")
        fun findAllByIds(@Mapping(ListOfStringJdbcParameterMapper::class) ids: List<String>): List<Entity>
    }
    ```

[Запросу, собранному вручную](#query), такой отображатель не нужен: `JdbcQuery` разворачивает
конструкцию `IN (:name)` в один placeholder `?` на каждый элемент с помощью `bindIn`.

## JSON / JSONB { #json }

Столбец `JSON` / `JSONB` можно отобразить в поле отображения, зарегистрировав обобщённые
`JdbcParameterColumnMapper<T>` и `JdbcResultColumnMapper<T>` как компоненты `@Module` с тегом `@Json`.
Эти отображатели связывают `JsonWriter<T>` / `JsonReader<T>` из модуля [JSON](json.md) со значением, понятным драйверу.
Пример для `Postgres` ниже сериализует значение в `PGobject` типа `jsonb` при связывании параметра,
обрабатывает `null` через `setNull(index, Types.NULL)` и читает столбец обратно как `String`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface JdbcJsonbMapperModule {

        @Json
        default <T> JdbcParameterColumnMapper<T> jdbcJsonParameterColumnMapper(JsonWriter<T> writer) {
            return (stmt, index, value) -> {
                if (value != null) {
                    PGobject jsonb = new PGobject();
                    jsonb.setType("jsonb");
                    jsonb.setValue(writer.toString(value));
                    stmt.setObject(index, jsonb);
                } else {
                    stmt.setNull(index, Types.NULL);
                }
            };
        }

        @Json
        default <T> JdbcResultColumnMapper<T> jdbcJsonResultColumnMapper(JsonReader<T> reader) {
            return (row, index) -> {
                var value = row.getString(index);
                if (value == null) {
                    return null;
                } else {
                    return reader.read(value);
                }
            };
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface JdbcJsonbMapperModule {

        @Json
        fun <T> jdbcJsonParameterColumnMapper(writer: JsonWriter<T>): JdbcParameterColumnMapper<T> {
            return JdbcParameterColumnMapper { stmt, index, value ->
                if (value == null) {
                    stmt.setNull(index, Types.NULL)
                } else {
                    val jsonb = PGobject()
                    jsonb.type = "jsonb"
                    jsonb.value = writer.toString(value)
                    stmt.setObject(index, jsonb)
                }
            }
        }

        @Json
        fun <T> jdbcJsonResultColumnMapper(reader: JsonReader<T>): JdbcResultColumnMapper<T> {
            return JdbcResultColumnMapper { row, index ->
                val value = row.getString(index)
                if (value == null) null else reader.read(value)
            }
        }
    }
    ```

Пометьте поле отображения аннотацией `@Json` (и `@Column`, если имя столбца отличается), где тип поля сам является `@Json`-типом.
В `INSERT` используется приведение `::jsonb`, чтобы `Postgres` принял сериализованную строку как `JSONB`;
`findById` читает значение обратно через тот же отображатель столбца с тегом `@Json`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface JdbcJsonbRepository extends JdbcRepository {

        @EntityJdbc
        record Entity(UUID id,
                      @Column("value") @Json JsonbValue value) {

            @Json
            record JsonbValue(String name, String surname) {}
        }

        @Query("SELECT * FROM entities_jsonb WHERE id = :id")
        @Nullable
        Entity findById(UUID id);

        @Query("INSERT INTO entities_jsonb(id, value) VALUES (:entity.id, :entity.value::jsonb)")
        void insert(Entity entity);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface JdbcJsonbRepository : JdbcRepository {

        @EntityJdbc
        data class Entity(
            val id: UUID,
            @field:Column("value") @Json val value: JsonbValue
        ) {

            @Json
            data class JsonbValue(val name: String, val surname: String)
        }

        @Query("SELECT * FROM entities_jsonb WHERE id = :id")
        fun findById(id: UUID): Entity?

        @Query("INSERT INTO entities_jsonb(id, value) VALUES (:entity.id, :entity.value::jsonb)")
        fun insert(entity: Entity)
    }
    ```

Модуль [JSON](json.md) обязателен, чтобы `Kora` смогла сгенерировать `JsonWriter` / `JsonReader` для типа поля,
а `@Module` с отображателями становится частью [графа приложения](container.md).

## Сгенерированный идентификатор { #generated-identifier }

Если требуется возвращать первичные ключи, сгенерированные базой данных,
используйте аннотацию `@Id` на методе.
`Kora` подготовит выражение с флагом `RETURN_GENERATED_KEYS` и отобразит `PreparedStatement#getGeneratedKeys`.
Этот подход работает и для `@Batch`-запросов.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @EntityJdbc
        record Entity(@Id Long id, String name) {

            public Entity(String name) {
                this(null, name);
            }
        }

        @Query("INSERT INTO entities(name) VALUES (:entity.name)")
        @Id
        Long insert(Entity entity);

        @Query("INSERT INTO entities(name) VALUES (:entity.name)")
        @Id
        List<Long> insert(@Batch List<Entity> entities);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @EntityJdbc
        data class Entity(@field:Id val id: Long?, val name: String)

        @Query("INSERT INTO entities(name) VALUES (:entity.name)")
        @Id
        fun insert(entity: Entity): Long

        @Query("INSERT INTO entities(name) VALUES (:entity.name)")
        @Id
        fun insert(@Batch entities: List<Entity>): List<Long>
    }
    ```

Сгенерированный ключ можно возвращать не только как скалярное значение, но и как тип ключа отображения.
Если идентификатор является составным ключом, описанным записью с [`@Embedded`](database-common.md#embedded-fields),
метод с `@Id` возвращает эту запись, а `@Batch`-вставка возвращает `List` ключей — по одному на каждую вставленную строку:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @EntityJdbc
        record Entity(@Id @Embedded EntityId id, @Column("name") String name) {

            @EntityJdbc
            record EntityId(Long a, Long b) {}
        }

        @Query("INSERT INTO entities_composite(name) VALUES (:entity.name)")
        @Id
        Entity.EntityId insertGenerated(Entity entity);

        @Query("INSERT INTO entities_composite(name) VALUES (:entity.name)")
        @Id
        List<Entity.EntityId> insertGenerated(@Batch List<Entity> entities);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @EntityJdbc
        data class Entity(
            @field:Id @field:Embedded val id: EntityId?,
            @field:Column("name") val name: String
        ) {

            @EntityJdbc
            data class EntityId(val a: Long?, val b: Long?)
        }

        @Id
        @Query("INSERT INTO entities_composite(name) VALUES (:entity.name)")
        fun insertGenerated(entity: Entity): Entity.EntityId

        @Id
        @Query("INSERT INTO entities_composite(name) VALUES (:entity.name)")
        fun insertGenerated(@Batch entities: List<Entity>): List<Entity.EntityId>
    }
    ```

Без `@Id` метод с `@Batch` не может отобразить произвольные строки, поэтому его возвращаемое значение ограничено
типами `void` / `Unit`, `UpdateCount`, `int[]` / `IntArray` либо `long[]` / `LongArray`.

## Ручной запрос с телеметрией { #query }

Если запрос сложно выразить одним статическим `@Query`, объявите обычный метод с реализацией
и соберите `SQL` самостоятельно.
`JdbcRepository#executor()` возвращает тот же `JdbcExecutor`, который используют сгенерированные методы `@Query`,
поэтому ручной запрос выполняется на том же соединении, попадает в активную транзакцию и учитывается телеметрией.

Рекомендуемый способ собрать динамический запрос — `JdbcQuery`.
`JdbcQuery.named()` строит `SQL` с именованными placeholder-ами `:name` и связывает значения по имени,
`JdbcQuery.template()` строит `SQL` с позиционными placeholder-ами `?`.
Оба построителя разделяют фрагменты `SQL` и значения: `sql` / `sqlIf` добавляют `SQL`,
`bind` / `bindIf` передают значения, а `bindIn` / `bindInIf` разворачивают конструкцию `IN (:name)`
в один placeholder на каждый элемент.
Каждый именованный параметр из `SQL` должен быть связан, и каждый связанный параметр должен использоваться в `SQL`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @EntityJdbc
        record Entity(long id, String name) {}

        default List<Entity> findByFilter(@Nullable String name, List<Long> ids) {
            var query = JdbcQuery.named()
                    .sql("SELECT id, name FROM entities WHERE 1 = 1") //(1)!
                    .sqlIf(" AND name = :name", name != null) //(2)!
                    .bindIf("name", name, name != null) //(3)!
                    .sqlIf(" AND id IN (:ids)", !ids.isEmpty())
                    .bindInIf("ids", ids, !ids.isEmpty()) //(4)!
                    .sql(" ORDER BY id")
                    .build();

            return executor().queryList(query, rs -> new Entity(rs.getLong("id"), rs.getString("name"))); //(5)!
        }
    }
    ```

    1.  Статическая часть запроса. Идентификаторы и фрагменты `SQL` форматируются до передачи в построитель, значения — никогда.
    2.  Добавляет фрагмент `SQL` только при выполнении условия.
    3.  Связывает значение только при выполнении того же условия.
    4.  Разворачивается в один placeholder `?` на каждый элемент, то есть `id IN (:ids)` превращается в `id IN (?, ?, ?)`.
    5.  `queryList` выполняет выражение через телеметрию и отображает каждую строку с помощью `JdbcRowMapper`. Также доступны `queryOne`, `queryOptional`, `executeUpdate` и `executeUpdateBatch`.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @EntityJdbc
        data class Entity(val id: Long, val name: String)

        fun findByFilter(name: String?, ids: List<Long>): List<Entity> {
            val query = JdbcQuery.named()
                .sql("SELECT id, name FROM entities WHERE 1 = 1") //(1)!
                .sqlIf(" AND name = :name", name != null) //(2)!
                .bindIf("name", name, name != null) //(3)!
                .sqlIf(" AND id IN (:ids)", ids.isNotEmpty())
                .bindInIf("ids", ids, ids.isNotEmpty()) //(4)!
                .sql(" ORDER BY id")
                .build()

            return executor().queryList(query, JdbcRowMapper<Entity> { rs -> //(5)!
                Entity(rs.getLong("id"), rs.getString("name"))
            })
        }
    }
    ```

    1.  Статическая часть запроса. Идентификаторы и фрагменты `SQL` форматируются до передачи в построитель, значения — никогда.
    2.  Добавляет фрагмент `SQL` только при выполнении условия.
    3.  Связывает значение только при выполнении того же условия.
    4.  Разворачивается в один placeholder `?` на каждый элемент, то есть `id IN (:ids)` превращается в `id IN (?, ?, ?)`.
    5.  `queryList` выполняет выражение через телеметрию и отображает каждую строку с помощью `JdbcRowMapper`. Также доступны `queryOne`, `queryOptional`, `executeUpdate` и `executeUpdateBatch`.

Если итоговый `SQL` уже готов и нужен полный контроль над `PreparedStatement`,
используйте `JdbcExecutor#query` с `QueryContext`.
`QueryContext` содержит идентификатор запроса, который попадает в телеметрию — удобно использовать
устойчивое имя вида `Repository.method` — и итоговый текст `SQL`.
Значения должны передаваться через параметры `PreparedStatement`, а не конкатенацией в строку запроса:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        default int countByPrefix(String prefix) {
            var queryContext = new QueryContext(
                    "EntityRepository.countByPrefix", //(1)!
                    "SELECT count(*) FROM entities WHERE name LIKE ?");

            return executor().query(queryContext, statement -> { //(2)!
                statement.setString(1, prefix + "%");
                try (var rs = statement.executeQuery()) {
                    return rs.next() ? rs.getInt(1) : 0;
                }
            });
        }
    }
    ```

    1.  Идентификатор запроса, который попадает в телеметрию
    2.  Создаёт `PreparedStatement`, оборачивает выполнение телеметрией и переиспользует текущее соединение

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        fun countByPrefix(prefix: String): Int {
            val queryContext = QueryContext(
                "EntityRepository.countByPrefix", //(1)!
                "SELECT count(*) FROM entities WHERE name LIKE ?"
            )

            return executor().query(queryContext) { statement -> //(2)!
                statement.setString(1, "$prefix%")
                statement.executeQuery().use { rs -> if (rs.next()) rs.getInt(1) else 0 }
            }
        }
    }
    ```

    1.  Идентификатор запроса, который попадает в телеметрию
    2.  Создаёт `PreparedStatement`, оборачивает выполнение телеметрией и переиспользует текущее соединение

### Параметры выражения { #query-options }

`JdbcQuery` умеет настраивать создаваемый `PreparedStatement` через `opts`:
`fetchSize`, `maxRows`, `queryTimeoutSeconds`, `resultSetType`, `resultSetConcurrency`, `resultSetHoldability`,
`generatedKeys` и `returnGeneratedKeys(columns...)`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    var query = JdbcQuery.template()
            .sql("SELECT id, name FROM entities WHERE name LIKE ?")
            .bind("prefix%")
            .opts(o -> o.fetchSize(500).queryTimeoutSeconds(5)) //(1)!
            .build();

    var entities = executor().queryList(query, rs -> new Entity(rs.getLong("id"), rs.getString("name")));
    ```

    1.  `fetchSize` определяет, сколько строк драйвер читает за раз, `queryTimeoutSeconds` ограничивает время выполнения выражения

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val query = JdbcQuery.template()
        .sql("SELECT id, name FROM entities WHERE name LIKE ?")
        .bind("prefix%")
        .opts { o -> o.fetchSize(500).queryTimeoutSeconds(5) } //(1)!
        .build()

    val entities = executor().queryList(query, JdbcRowMapper<Entity> { rs ->
        Entity(rs.getLong("id"), rs.getString("name"))
    })
    ```

    1.  `fetchSize` определяет, сколько строк драйвер читает за раз, `queryTimeoutSeconds` ограничивает время выполнения выражения

### Ручной пакетный запрос { #query-batch }

Те же построители создают пакет из коллекции: `batch()` переводит построитель в пакетный режим,
а `executeUpdateBatch` отправляет его одним вызовом `PreparedStatement#executeBatch`.
Результатом является суммарное количество затронутых строк либо `UpdateCount(-1)`,
если драйвер вернул `Statement.SUCCESS_NO_INFO`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    default UpdateCount insertAll(List<Entity> entities) {
        var batch = JdbcQuery.named()
                .sql("INSERT INTO entities(id, name) VALUES (:id, :name)")
                .batch()
                .bindAll(entities, (row, entity) -> row
                        .bind("id", entity.id())
                        .bind("name", entity.name()))
                .build();

        return executor().executeUpdateBatch(batch);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun insertAll(entities: List<Entity>): UpdateCount {
        val batch = JdbcQuery.named()
            .sql("INSERT INTO entities(id, name) VALUES (:id, :name)")
            .batch()
            .bindAll(entities) { row, entity ->
                row.bind("id", entity.id)
                row.bind("name", entity.name)
            }
            .build()

        return executor().executeUpdateBatch(batch)
    }
    ```

## Транзакции { #transaction }

`JdbcRepository` предоставляет контракт `JdbcExecutor` через метод `executor()`.
Все методы репозитория, вызванные внутри транзакционного колбэка, выполняются в этой же транзакции,
потому что переиспользуют соединение, привязанное к текущей области выполнения.

Используйте `inTx`, чтобы выполнять запросы транзакционно.
Если транзакция в текущей области выполнения уже активна, вложенный вызов `inTx` использует то же соединение
и не открывает новую транзакцию.

Транзакционную последовательность операций можно оставить внутри самого репозитория как обычный метод с реализацией.
Это удобно, когда несколько методов `@Query` или сложный ручной `SQL`-запрос должны находиться рядом с остальными
запросами репозитория, без вынесения технической работы с базой данных в слой сервисов.
Внутри такого метода можно использовать и методы `@Query`, и [ручные запросы](#query).

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        UpdateCount insert(Entity entity);

        @Query("UPDATE entities SET name = :name WHERE id = :id")
        UpdateCount updateName(long id, String name);

        default List<Entity> saveAll(Entity one, Entity two) {
            return executor().inTx(() -> {
                insert(one); //(1)!
                updateName(two.id(), two.name()); //(2)!
                return List.of(one, two);
            });
        }
    }
    ```

    1. Выполняется в рамках транзакции либо откатывается, если вся лямбда выбросит исключение
    2. Выполняется в рамках транзакции либо откатывается, если вся лямбда выбросит исключение

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        fun insert(entity: Entity): UpdateCount

        @Query("UPDATE entities SET name = :name WHERE id = :id")
        fun updateName(id: Long, name: String): UpdateCount

        fun saveAll(one: Entity, two: Entity): List<Entity> {
            return executor().inTx(JdbcExecutor.SqlSupplier { //(1)!
                insert(one) //(2)!
                updateName(two.id, two.name) //(3)!
                listOf(one, two)
            })
        }
    }
    ```

    1. Явный SAM-конструктор, смотрите предупреждение ниже
    2. Выполняется в рамках транзакции либо откатывается, если вся лямбда выбросит исключение
    3. Выполняется в рамках транзакции либо откатывается, если вся лямбда выбросит исключение

!!! warning "Kotlin"

    У `inTx` несколько перегрузок, и все они принимают единственный функциональный аргумент,
    поэтому обычную лямбду `Kotlin` компилятор разрешить не может.
    Передавайте явный SAM-конструктор: `JdbcExecutor.SqlSupplier { … }`, если блок возвращает значение,
    и `JdbcExecutor.SqlRunnable { … }`, если не возвращает.
    Без этого компилятор сообщает `Overload resolution ambiguity` или `Cannot infer type for type parameter T` —
    ни то, ни другое на транзакцию не указывает.

Транзакция считается успешно зафиксированной после завершения метода, если он не выбросил исключение.
Если метод выбросил исключение, все изменения в базе данных, сделанные в рамках транзакции, откатываются,
а исключение пробрасывается дальше.

Соединение привязано к текущей области выполнения, поэтому работа, переданная в посторонний поток,
в текущую транзакцию не попадает — такой поток получит собственное соединение.

### Уровень изоляции { #isolation }

По умолчанию транзакция выполняется с уровнем изоляции, настроенным в драйвере, базе данных
либо в [пуле соединений](#pool-customization) — для большинства баз данных это `READ_COMMITTED`.
Чтобы запросить другой уровень для одной транзакции, передайте значение `JdbcExecutor.TxIsolation` первым аргументом `inTx`:
`READ_UNCOMMITTED`, `READ_COMMITTED`, `REPEATABLE_READ` либо `SERIALIZABLE`.
После завершения транзакции предыдущий уровень соединения восстанавливается.

===! ":fontawesome-brands-java: `Java`"

    ```java
    default List<Entity> saveAll(Entity one, Entity two) {
        return executor().inTx(JdbcExecutor.TxIsolation.REPEATABLE_READ, () -> {
            insert(one);
            insert(two);
            return List.of(one, two);
        });
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun saveAll(one: Entity, two: Entity): List<Entity> {
        return executor().inTx(JdbcExecutor.TxIsolation.REPEATABLE_READ, JdbcExecutor.SqlSupplier {
            insert(one)
            insert(two)
            listOf(one, two)
        })
    }
    ```

Уровень изоляции применяется только тогда, когда `inTx` действительно открывает транзакцию.
Вложенный `inTx` внутри уже открытой транзакции переиспользует её и аргумент игнорирует.

### Меж-репозиторные транзакции

Когда в приложении используется несколько репозиториев, вы можете объединить их операции в одной транзакции.
Все репозитории, которые `extend JdbcRepository`, используют один и тот же `JdbcConnectionFactory` (если не указан отдельный `@Tag` для другой базы данных).
`JdbcConnectionFactory` хранит соединение в `Context` текущего потока.
При входе в `inTx` соединение сохраняется в контекст.
Любой `@Query` метод любого репозитория, вызванный внутри `inTx`, проверяет контекст и использует существующее соединение вместо создания нового.
Таким образом, все операции в лямбде выполняются на одном соединении и в одной транзакции.

Если любой из вызовов бросает исключение — все изменения откатываются.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface OrderRepository extends JdbcRepository {

        @Query("INSERT INTO orders(customer_id, total) VALUES (:customerId, :total)")
        UpdateCount create(long customerId, long total);
    }

    @Repository
    public interface StockRepository extends JdbcRepository {

        @Query("UPDATE stock SET quantity = quantity - :quantity WHERE product_id = :productId")
        UpdateCount reserve(long productId, long quantity);
    }

    @Component
    public class OrderService {

        private final OrderRepository orderRepo;
        private final StockRepository stockRepo;

        public OrderService(OrderRepository orderRepo, StockRepository stockRepo) {
            this.orderRepo = orderRepo;
            this.stockRepo = stockRepo;
        }

        public void placeOrder(long customerId, long productId, long total, long quantity) {
            orderRepo.getJdbcConnectionFactory().inTx(() -> {
                stockRepo.reserve(productId, quantity);
                orderRepo.create(customerId, total);
            });
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface OrderRepository : JdbcRepository {

        @Query("INSERT INTO orders(customer_id, total) VALUES (:customerId, :total)")
        fun create(customerId: Long, total: Long): UpdateCount
    }

    @Repository
    interface StockRepository : JdbcRepository {

        @Query("UPDATE stock SET quantity = quantity - :quantity WHERE product_id = :productId")
        fun reserve(productId: Long, quantity: Long): UpdateCount
    }

    @Component
    class OrderService(
        private val orderRepo: OrderRepository,
        private val stockRepo: StockRepository
    ) {

        fun placeOrder(customerId: Long, productId: Long, total: Long, quantity: Long) {
            orderRepo.jdbcConnectionFactory.inTx {
                stockRepo.reserve(productId, quantity)
                orderRepo.create(customerId, total)
            }
        }
    }
    ```

**Ограничение:** Если репозитории подключены к разным базам данных (через `@Tag(OtherDatabase.class)`), они используют разные экземпляры `JdbcConnectionFactory` — транзакция НЕ распространяется между ними.

### Ручное управление соединением { #connection }

Если запросу нужна более сложная логика или запросы вне репозитория, можно использовать `java.sql.Connection`.
Метод `withConnection` выполняет код с соединением, но сам транзакцию не открывает.

`withConnection` работает следующим образом:

- если текущая область выполнения уже содержит `ConnectionContext`, метод передаёт в лямбду текущее соединение;
- если текущая область выполнения соединения не содержит, метод берёт новое соединение из пула, привязывает его к `ConnectionContext` на время выполнения лямбды и закрывает после завершения;
- вложенные вызовы `withConnection`, [ручные запросы](#query) и методы репозитория внутри этой лямбды используют то же текущее соединение;
- исключение `java.sql.SQLException` оборачивается в `UncheckedSqlException`.

`withContext` делает то же самое, но передаёт `ConnectionContext` вместо самого `Connection` —
именно он нужен для регистрации действий [после фиксации](#post-commit-actions) и [после отката](#post-rollback-actions).
`currentConnection` и `currentContext` возвращают соединение, привязанное к текущей области выполнения, либо `null`, если его нет,
а `acquireConnection` берёт из пула новое соединение, которое вызывающий код обязан закрыть сам.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final EntityRepository repository;

        public SomeService(EntityRepository repository) {
            this.repository = repository;
        }

        public List<Entity> saveAll(Entity one, Entity two) {
            return repository.executor().withConnection(connection -> {
                // do some work with java.sql.Connection
                return List.of(one, two);
            });
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(private val repository: EntityRepository) {

        fun saveAll(one: Entity, two: Entity): List<Entity> {
            return repository.executor().withConnection(JdbcExecutor.SqlFunction<Connection, List<Entity>> { connection ->
                // do some work with java.sql.Connection
                listOf(one, two)
            })
        }
    }
    ```

Метод `inTx` открывает транзакцию и построен поверх `withContext`.
Если текущее соединение уже находится в активной транзакции, то есть `autoCommit = false`, вложенный `inTx` использует ту же транзакцию.
Если активной транзакции нет, `inTx` выключает `autoCommit`, выполняет лямбду, а затем вызывает `commit` при успехе либо `rollback` при исключении.

Метод с `@Query` также может принимать аргумент типа `java.sql.Connection`.
Сгенерированный код подготовит выражение именно на этом соединении вместо текущего,
что удобно, когда соединение приходит извне репозитория:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        void insert(Connection connection, Entity entity);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        fun insert(connection: Connection, entity: Entity)
    }
    ```

### Действия после фиксации { #post-commit-actions }

Если нужно выполнить действия после успешной фиксации транзакции, зарегистрируйте их на `ConnectionContext`
методом `afterCommit`.
Действие получает соединение, выполняется после `commit` и только если транзакция завершилась успешно.
Такие действия можно добавлять только внутри активной транзакции — иначе `afterCommit` выбрасывает `IllegalStateException`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final EntityRepository repository;

        public SomeService(EntityRepository repository) {
            this.repository = repository;
        }

        public List<Entity> saveAll(Entity one, Entity two) {
            return repository.executor().inTx(context -> { //(1)!
                context.afterCommit(connection -> {
                    // do some work after commit
                });

                repository.insert(one);
                repository.insert(two);
                return List.of(one, two);
            });
        }
    }
    ```

    1.  Перегрузка `inTx` с одним аргументом передаёт `ConnectionContext` текущей транзакции

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(private val repository: EntityRepository) {

        fun saveAll(one: Entity, two: Entity): List<Entity> {
            return repository.executor().inTx(JdbcExecutor.SqlFunction<ConnectionContext, List<Entity>> { context -> //(1)!
                context.afterCommit { connection ->
                    // do some work after commit
                }

                repository.insert(one)
                repository.insert(two)
                listOf(one, two)
            })
        }
    }
    ```

    1.  Перегрузка `inTx` с одним аргументом передаёт `ConnectionContext` текущей транзакции

Исключение, выброшенное действием после фиксации, пробрасывается вызывающему коду, но транзакция остаётся зафиксированной.

### Действия после отката { #post-rollback-actions }

Если нужно выполнить действия после отката транзакции, зарегистрируйте их методом `afterRollback`.
Действие получает соединение и исключение, из-за которого транзакция была откачена.
Такие действия можно добавлять только внутри активной транзакции — иначе `afterRollback` выбрасывает `IllegalStateException`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final EntityRepository repository;

        public SomeService(EntityRepository repository) {
            this.repository = repository;
        }

        public List<Entity> saveAll(Entity one, Entity two) {
            return repository.executor().inTx(context -> {
                context.afterRollback((connection, e) -> {
                    // do some work after rollback
                });

                repository.insert(one);
                repository.insert(two);
                return List.of(one, two);
            });
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(private val repository: EntityRepository) {

        fun saveAll(one: Entity, two: Entity): List<Entity> {
            return repository.executor().inTx(JdbcExecutor.SqlFunction<ConnectionContext, List<Entity>> { context ->
                context.afterRollback { connection, e ->
                    // do some work after rollback
                }

                repository.insert(one)
                repository.insert(two)
                listOf(one, two)
            })
        }
    }
    ```

Исключение, выброшенное действием после отката, не подменяет исходную ошибку:
оно добавляется к ней как подавленное (suppressed).

## Сигнатуры { #signatures }

Контракты `JDBC`-репозиториев синхронные — метод блокирует вызывающий поток до ответа базы данных.
Серверные транспорты `Kora` выполняют обработку запросов на виртуальных потоках, поэтому блокирующий вызов `JDBC` не занимает платформенный поток.
Асинхронных и реактивных сигнатур репозитория не существует.

Доступные сигнатуры методов репозитория из коробки:

===! ":fontawesome-brands-java: `Java`"

    `T` — тип возвращаемого значения.

    - `T myMethod()` — результат не должен быть `null`
    - `@Nullable T myMethod()`
    - `Optional<T> myMethod()`
    - `List<T> myMethod()`
    - `void myMethod()`
    - `UpdateCount myMethod()` — количество затронутых строк
    - `int[] myMethod(@Batch List<T> values)` / `long[] myMethod(@Batch List<T> values)` — результаты по строкам [пакетного запроса](database-common.md#batch-query)

=== ":simple-kotlin: `Kotlin`"

    `T` — тип возвращаемого значения.

    - `fun myMethod(): T` — результат не должен быть `null`
    - `fun myMethod(): T?`
    - `fun myMethod(): List<T>`
    - `fun myMethod()` — возвращает `Unit`
    - `fun myMethod(): UpdateCount` — количество затронутых строк
    - `fun myMethod(@Batch values: List<T>): IntArray` / `fun myMethod(@Batch values: List<T>): LongArray` — результаты по строкам [пакетного запроса](database-common.md#batch-query)

Чтобы привязать репозиторий к источнику данных, отличному от основного, используйте атрибут `executorTag`
аннотации `@Repository`, смотрите [Дополнительные источники данных](#additional-data-sources).

## Телеметрия { #telemetry }

Логирование, метрики и трассировка настраиваются через блок `telemetry` в [конфигурации](#configuration) и описаны в разделе [Справочник метрик](metrics.md#database).
Пул `Hikari` публикует собственные метрики, пока включён параметр `telemetry.metrics.driverMetrics`.
Чтобы полностью переопределить телеметрию, можно предоставить собственные SPI-фабрики, подробнее в разделе [Общая документация по базам данных](database-common.md#telemetry).
