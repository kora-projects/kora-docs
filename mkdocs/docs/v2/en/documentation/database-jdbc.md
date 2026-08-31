---
description: "Explains Kora JDBC repositories, the jdbc configuration section, Hikari pool tuning, result and parameter mapping, generated identifiers, manual queries built with JdbcQuery, transactions and isolation levels. Use when working with @Repository, @Query, @EntityJdbc, @Table, @Id, @Column, @Batch, JdbcDatabaseModule."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora JDBC repositories, the jdbc configuration section, Hikari pool tuning, result and parameter mapping, generated identifiers, manual queries and transactions; key triggers include @Repository, @Query, @EntityJdbc, @Table, @Id, @Column, @Batch, JdbcDatabaseModule, JdbcRepository, JdbcExecutor, JdbcQuery, UncheckedSqlException."
---

The module provides a repository implementation based on [JDBC](https://proselyte.net/tutorials/jdbc/introduction/) for
working with relational databases and uses [Hikari](https://github.com/brettwooldridge/HikariCP) to manage the connection
pool.
You describe a repository interface and `SQL` queries with `@Repository` and `@Query`, and `Kora` generates an implementation
that obtains a connection from the pool, binds parameters, reads the result, and participates in transactions.

Common rules for entities, `@Repository`, `@Query`, `@Batch`, `UpdateCount`, macros, manual queries, and other repository
mechanisms are described in [Common database rules](database-common.md).

For a step-by-step walkthrough before the reference details, see [JDBC Database](../guides/database-jdbc.md) and [Advanced JDBC Database](../guides/database-jdbc-advanced.md).

## Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:database-jdbc"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends JdbcDatabaseModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:database-jdbc")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : JdbcDatabaseModule
    ```

You also **must provide** the database driver implementation as a dependency.

The module registers the connection pool as a `JdbcDataSource` component. It implements `JdbcExecutor`,
so repositories receive it automatically, and it wraps a `javax.sql.DataSource`,
so a plain `javax.sql.DataSource` can be injected into your own components when a third-party library requires one.

## Configuration { #configuration }

Basic JDBC configuration parameters are read from the `jdbc` config section:

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

    1.  `JDBC URL` for database connection (`required`, no default)
    2.  Username for connection (`required`, no default)
    3.  Password for connection (`required`, no default)
    4.  `Hikari` connection pool name (`required`, no default)
    5.  Maximum `Hikari` connection pool size (default: `10`)

=== ":simple-yaml: `YAML`"

    ```yaml
    jdbc:
      jdbcUrl: "jdbc:postgresql://localhost:5432/postgres" #(1)!
      username: "postgres" #(2)!
      password: "postgres" #(3)!
      poolName: "kora" #(4)!
      maxPoolSize: 10 #(5)!
    ```

    1.  `JDBC URL` for database connection (`required`, no default)
    2.  Username for connection (`required`, no default)
    3.  Password for connection (`required`, no default)
    4.  `Hikari` connection pool name (`required`, no default)
    5.  Maximum `Hikari` connection pool size (default: `10`)

??? note "Full Configuration"

    Example of the complete configuration described by `JdbcDatabaseConfig` (example values or default values are shown):

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

        1.  `JDBC URL` for connecting to the database (`required`, no default)
        2.  Username for the connection (`required`, no default)
        3.  User password for the connection (`required`, no default)
        4.  Database schema for the connection (optional, no default)
        5.  `Hikari` connection pool name (`required`, no default)
        6.  Maximum `Hikari` connection pool size (default: `10`)
        7.  Minimum number of idle ready connections in the `Hikari` pool (default: `0`)
        8.  Maximum time to wait for a connection from the `Hikari` pool (default: `10s`)
        9.  Maximum time for `Hikari` connection validation (default: `5s`)
        10. Maximum idle time for a `Hikari` connection (default: `10m`)
        11. Maximum lifetime of a `Hikari` connection (default: `15m`)
        12. Time after which a busy connection is considered a possible leak (default: `0s`)
        13. Maximum time to wait for connection validation at service startup. When it is not set, the service starts without touching the database (optional, no default)
        14. Whether to enable the [readiness probe](probes.md#readiness) for the database connection (default: `false`)
        15. Additional `JDBC` connection properties passed to `Hikari` `dataSourceProperties` (default: `{}`)
        16. Enables module logging (default: `false`)
        17. Enables module metrics (default: `false`)
        18. Whether to report the `Hikari` pool's own metrics, such as pool size and connection acquire time (default: `true`)
        19. Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for metrics in milliseconds (default: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
        20. Configures metric tags (default: `{}`)
        21. Enables module tracing (default: `true`)
        22. Configures tracing attributes (default: `{}`)

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

        1.  `JDBC URL` for connecting to the database (`required`, no default)
        2.  Username for the connection (`required`, no default)
        3.  User password for the connection (`required`, no default)
        4.  Database schema for the connection (optional, no default)
        5.  `Hikari` connection pool name (`required`, no default)
        6.  Maximum `Hikari` connection pool size (default: `10`)
        7.  Minimum number of idle ready connections in the `Hikari` pool (default: `0`)
        8.  Maximum time to wait for a connection from the `Hikari` pool (default: `10s`)
        9.  Maximum time for `Hikari` connection validation (default: `5s`)
        10. Maximum idle time for a `Hikari` connection (default: `10m`)
        11. Maximum lifetime of a `Hikari` connection (default: `15m`)
        12. Time after which a busy connection is considered a possible leak (default: `0s`)
        13. Maximum time to wait for connection validation at service startup. When it is not set, the service starts without touching the database (optional, no default)
        14. Whether to enable the [readiness probe](probes.md#readiness) for the database connection (default: `false`)
        15. Additional `JDBC` connection properties passed to `Hikari` `dataSourceProperties` (default: `{}`)
        16. Enables module logging (default: `false`)
        17. Enables module metrics (default: `false`)
        18. Whether to report the `Hikari` pool's own metrics, such as pool size and connection acquire time (default: `true`)
        19. Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for metrics in milliseconds (default: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
        20. Configures metric tags (default: `{}`)
        21. Enables module tracing (default: `true`)
        22. Configures tracing attributes (default: `{}`)

### Pool customization { #pool-customization }

Configuration keys cover the `Hikari` settings that most services need.
If you need a setting that is not exposed by `JdbcDatabaseConfig`, provide a `Configurer<HikariConfig>` component.
`Kora` calls it with the `HikariConfig` it has already built from the configuration, right before the pool is created,
so your component only adjusts what it cares about.

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

    1.  Default isolation level of every connection in the pool, see also [Isolation level](#isolation)

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

    1.  Default isolation level of every connection in the pool, see also [Isolation level](#isolation)

### Additional data sources { #additional-data-sources }

A service can talk to several databases at once. `JdbcDatabaseModule` declares the default data source
over the `jdbc` config section, and every extra data source is declared as a tagged factory module
with its own config section:

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

    1.  Marker class that identifies this data source in the [application graph](container.md)
    2.  The tag of the factory module is propagated to every component it creates, so the analytics pool is registered as `@Tag(Analytics.class) JdbcDataSource`
    3.  Config section this data source reads, described by the same `JdbcDatabaseConfig`

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

    1.  Marker class that identifies this data source in the [application graph](container.md)
    2.  The tag of the factory module is propagated to every component it creates, so the analytics pool is registered as `@Tag(Analytics::class) JdbcDataSource`
    3.  Config section this data source reads, described by the same `JdbcDatabaseConfig`

A repository points at a non-default data source with the `executorTag` attribute of `@Repository`;
repositories without the attribute use the default `jdbc` data source:

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

## Usage { #usage }

A `JDBC` repository is declared as an interface annotated with `@Repository` and must extend `JdbcRepository`.
Each method annotated with `@Query` contains a regular `SQL` query. Method parameters are bound by name with the
`:parameter` syntax, and object fields can be referenced as `:entity.field`.

Entities are described with the [common database annotations](database-common.md) and marked with `@EntityJdbc`
so that `Kora` generates the view mapper at compile time (see [View](#view)):

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

    1.  Uses macros `%{return#selects}` and `%{return#table}`. Expands to query:
        ```sql
        SELECT id, name, description
        FROM entities
        WHERE id = :id
        ```
        Method uses macros for `SELECT`. Details: [Common Database Rules — Macros](database-common.md#macros)
    2.  Fields listed manually without macros — this is valid but requires maintenance when the view changes.
    3.  Uses macro `%{entity#inserts}`. Expands to query:
        ```sql
        INSERT INTO entities(id, name, description)
        VALUES(:entity.id, :entity.name, :entity.description)
        ```
        Method uses macros for `INSERT`. Details: [Common Database Rules — Macros](database-common.md#macros)

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

    1.  Uses macros `%{return#selects}` and `%{return#table}`. Expands to query:
        ```sql
        SELECT id, name, description
        FROM entities
        WHERE id = :id
        ```
        Method uses macros for `SELECT`. Details: [Common Database Rules — Macros](database-common.md#macros)
    3.  Uses macro `%{entity#inserts}`. Expands to query:
        ```sql
        INSERT INTO entities(id, name, description)
        VALUES(:entity.id, :entity.name, :entity.description)
        ```
        Method uses macros for `INSERT`. Details: [Common Database Rules — Macros](database-common.md#macros)

`SQL` remains under the developer's control: you can use database-specific features, while `Kora` only handles safe
parameter binding, query execution, and result mapping.
Common rules for entities, `@Table`, `@Column`, `@Id`, `@Embedded`, `@Batch`, and macros are described in
[Common database rules](database-common.md#macros).

**Parameter binding:** Kora performs typed injection of arguments into the SQL query at compile time.
Query parameters (e.g., `:id`, `:entity.name`) are replaced in the generated code with corresponding `PreparedStatement` calls.
For example, for a `String name` parameter, something like `statement.setString(1, name)` will be generated, where the index corresponds to the parameter order in the query.
This ensures security (protection against SQL injection) and performance (using prepared statements).

**Nullability:** in `Java`, a nullable result is marked with the [JSpecify](https://jspecify.dev) annotation `org.jspecify.annotations.Nullable`,
in `Kotlin` it is expressed by the `T?` return type.
When a method is not marked as nullable and the mapper still produces `null`,
the generated code fails with `NullPointerException` and the message `Result mapping is expected non-null, but was null`.

**Errors:** a `java.sql.SQLException` raised by the driver never leaves a repository method as a checked exception.
It is wrapped into the unchecked `UncheckedSqlException` from `io.koraframework.database.jdbc.exception`,
and the original exception is available through `getCause()`.

## Mapping { #mapping }

You can override the mapping of different parts of an [entity](database-common.md), a query result, and query parameters.
For this, `Kora` provides several mapper interfaces.

A mapper class referenced from `@Mapping` is created by `Kora` itself when it is `final` (`Kotlin` classes are final unless declared `open`)
and has a public constructor without arguments.
Such a mapper must **not** be annotated with `@Component`.
A mapper that has constructor dependencies is resolved from the [application graph](container.md) instead,
so it must be declared as a `@Component` or provided by a `@Module`.

### Result { #result }

Use `JdbcResultSetMapper<T>` when you need to manually map the whole `ResultSet`.
This mapper receives the whole query result and decides how many rows to read and what to return.

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

`JdbcResultSetMapper` also exposes static helpers `singleResultSetMapper`, `listResultSetMapper`,
and `optionalResultSetMapper` that build a full-`ResultSet` mapper from a `JdbcRowMapper<T>`.

#### View { #view }

`Kora` generates result mappers for your own types at compile time, and it needs the `@EntityJdbc` annotation
from `io.koraframework.database.jdbc.annotation` to know which types to generate them for.
Annotate every type that is returned from a repository method, including the identifier type of an
[`@Id`](#generated-identifier) method:

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

Without the annotation `Kora` has nothing to build a `JdbcResultSetMapper` / `JdbcRowMapper` from,
and the [application graph](container.md) fails to build with an unresolved mapper dependency —
unless you provide the mapper yourself with [`@Mapping`](#result).
Types that only appear as [`@Embedded`](database-common.md#embedded-fields) fields of another entity
are flattened into the enclosing view and do not need their own annotation,
but annotating them as well keeps the mapping predictable when they later become a result type of their own.

Built-in types such as `long` or `String` do not need anything: the module provides
row, column, and parameter mappers for them out of the box, see [Supported Types](#supported-types).

### Row { #row }

Use `JdbcRowMapper<T>` when you need to manually map one row.
Keep in mind that in `JDBC`, column indexes in `ResultSet` start from `1`:

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

A `JdbcRowMapper<T>` is enough for any result shape: `Kora` wraps it with `singleResultSetMapper`,
`optionalResultSetMapper`, or `listResultSetMapper` depending on whether the method returns
`T`, `Optional<T>`, or `List<T>`.

### Column { #column }

Use `JdbcResultColumnMapper<T>` when you need to manually map a single column value:

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

### Parameter { #parameter }

Use `JdbcParameterColumnMapper<T>` when you need to manually map a query parameter value.
The contract declares the value as nullable, so the mapper is also responsible for binding `NULL`:

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

    Mapper contracts are annotated with [JSpecify](https://jspecify.dev), so the mapped value is nullable in the contract.
    A `Kotlin` override must declare it as `T?` — `override fun set(stmt: PreparedStatement, index: Int, value: UUID?)`.
    Declaring the parameter as non-null does not compile.

In `Java`, `org.jspecify.annotations.Nullable` is a type-use annotation, so its position matters.
For a nested type, the annotation goes before the nested part of the name:
`void set(PreparedStatement stmt, int index, Entity.@Nullable Status value)`.

### Supported Types { #supported-types }

??? abstract "List of supported types for arguments/return values out of the box"

    These types are selected because they are supported by most popular databases.
    `Kora` provides built-in row, column, and parameter mappers for them.

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

    View fields without an explicit `@Mapping` are read and written by inlined `ResultSet` / `PreparedStatement` calls
    for `boolean` / `Boolean`, `short` / `Short`, `int` / `Integer`, `long` / `Long`, `double` / `Double`,
    `float` / `Float`, `byte[]`, `String`, `BigDecimal`, `LocalDate`, and `LocalDateTime`.
    For other types, the built-in `JdbcResultColumnMapper<T>` / `JdbcParameterColumnMapper<T>` mappers are used,
    or you declare custom mappers.

## Select by List { #select-by-list }

Sometimes you need to select rows by a list of values.
At the `JDBC` level, such parameters must be prepared separately by the driver because the list length is not known in advance.
`Kora` tries to perform mappings at compile time and does not rewrite `SQL` at runtime, so such parameters require a custom mapper.

`Kora` does not provide this parameter mapping out of the box, but it is easy to add yourself.
The example below shows `Postgres` through a `JDBC Array`:

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

A [manually built query](#query) does not need such a mapper: `JdbcQuery` expands an `IN (:name)` clause
into one `?` placeholder per element with `bindIn`.

## JSON / JSONB { #json }

A `JSON` / `JSONB` column can be mapped to a view field by registering generic
`JdbcParameterColumnMapper<T>` and `JdbcResultColumnMapper<T>` as `@Module` components tagged with `@Json`.
These mappers bridge the [JSON](json.md) module `JsonWriter<T>` / `JsonReader<T>` to a driver-specific value.
The `Postgres` example below serializes the value into a `PGobject` of type `jsonb` when binding a parameter,
handles `null` via `setNull(index, Types.NULL)`, and reads the column back as a `String`:

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

Annotate the view field with `@Json` (and `@Column` if the column name differs), where the field type is itself a `@Json` type.
The `INSERT` uses the `::jsonb` cast so `Postgres` accepts the serialized string as `JSONB`;
`findById` reads it back through the same `@Json`-tagged column mapper:

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

The [JSON](json.md) module is required so `Kora` can generate `JsonWriter` / `JsonReader` for the field type,
and the mapper `@Module` becomes part of the [application graph](container.md).

## Generated Identifier { #generated-identifier }

If you need to return primary keys generated by the database,
use the `@Id` annotation on the method.
`Kora` then prepares the statement with `RETURN_GENERATED_KEYS` and maps `PreparedStatement#getGeneratedKeys`.
This approach also works for `@Batch` queries.

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

The generated key can also be returned as the view key type rather than a scalar.
When the identifier is a composite key described by an [`@Embedded`](database-common.md#embedded-fields) record,
the `@Id` method returns that record, and a `@Batch` insert returns a `List` of keys, one per inserted row:

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

Without `@Id` a `@Batch` method cannot map arbitrary rows, so its return type is limited
to `void` / `Unit`, `UpdateCount`, `int[]` / `IntArray`, or `long[]` / `LongArray`.

## Manual Query With Telemetry { #query }

If a query is hard to express as a single static `@Query`, declare a regular method with an implementation
and build the `SQL` yourself.
`JdbcRepository#executor()` returns the `JdbcExecutor` that the generated `@Query` methods use,
so a manual query runs on the same connection, joins an active transaction, and is reported to telemetry.

The recommended way to assemble a dynamic query is `JdbcQuery`.
`JdbcQuery.named()` builds `SQL` with `:name` placeholders and binds values by name,
`JdbcQuery.template()` builds `SQL` with positional `?` placeholders.
Both builders keep `SQL` fragments and values apart: `sql` / `sqlIf` append `SQL`,
`bind` / `bindIf` supply values, and `bindIn` / `bindInIf` expand an `IN (:name)` clause
into one placeholder per element.
Every named parameter used in `SQL` must be bound, and every bound parameter must be used in `SQL`.

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

    1.  Static part of the query. `SQL` identifiers and fragments are formatted before they reach the builder, values never are.
    2.  Appends the `SQL` fragment only when the condition holds.
    3.  Binds the value only when the same condition holds.
    4.  Expands into one `?` placeholder per element, so `id IN (:ids)` becomes `id IN (?, ?, ?)`.
    5.  `queryList` runs the statement through telemetry and maps every row with a `JdbcRowMapper`. `queryOne`, `queryOptional`, `executeUpdate`, and `executeUpdateBatch` are available as well.

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

    1.  Static part of the query. `SQL` identifiers and fragments are formatted before they reach the builder, values never are.
    2.  Appends the `SQL` fragment only when the condition holds.
    3.  Binds the value only when the same condition holds.
    4.  Expands into one `?` placeholder per element, so `id IN (:ids)` becomes `id IN (?, ?, ?)`.
    5.  `queryList` runs the statement through telemetry and maps every row with a `JdbcRowMapper`. `queryOne`, `queryOptional`, `executeUpdate`, and `executeUpdateBatch` are available as well.

When you already have the final `SQL` and want full control over the `PreparedStatement`,
use `JdbcExecutor#query` with a `QueryContext`.
`QueryContext` carries the query identifier reported to telemetry — a stable name such as `Repository.method` is convenient —
and the final `SQL`.
Values must be passed through `PreparedStatement` parameters, not concatenated into the query string:

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

    1.  Query identifier reported to telemetry
    2.  Creates the `PreparedStatement`, wraps execution in telemetry, and reuses the current connection

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

    1.  Query identifier reported to telemetry
    2.  Creates the `PreparedStatement`, wraps execution in telemetry, and reuses the current connection

### Statement options { #query-options }

`JdbcQuery` can also configure the `PreparedStatement` it creates through `opts`:
`fetchSize`, `maxRows`, `queryTimeoutSeconds`, `resultSetType`, `resultSetConcurrency`, `resultSetHoldability`,
`generatedKeys`, and `returnGeneratedKeys(columns...)`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    var query = JdbcQuery.template()
            .sql("SELECT id, name FROM entities WHERE name LIKE ?")
            .bind("prefix%")
            .opts(o -> o.fetchSize(500).queryTimeoutSeconds(5)) //(1)!
            .build();

    var entities = executor().queryList(query, rs -> new Entity(rs.getLong("id"), rs.getString("name")));
    ```

    1.  `fetchSize` controls how many rows the driver reads at once, `queryTimeoutSeconds` limits statement execution time

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

    1.  `fetchSize` controls how many rows the driver reads at once, `queryTimeoutSeconds` limits statement execution time

### Manual batch { #query-batch }

The same builders create a batch from a collection: `batch()` switches the builder into batch mode,
and `executeUpdateBatch` sends it as a single `PreparedStatement#executeBatch`.
The result is the total number of affected rows, or `UpdateCount(-1)` when the driver
reports `Statement.SUCCESS_NO_INFO`.

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

## Transactions { #transaction }

`JdbcRepository` exposes the `JdbcExecutor` contract through `executor()`.
All repository methods called inside the transaction callback are executed in that same transaction,
because they reuse the connection bound to the current scope.

Use `inTx` to execute queries transactionally.
If there is already an active transaction in the current scope, a nested `inTx` call uses the same connection and does not open
a new transaction.

A transactional sequence of operations can stay inside the repository itself as a regular method with an implementation.
This is useful when several `@Query` methods or a complex manual `SQL` query should stay next to the rest of the repository queries,
without moving technical database work to a service layer.
Inside such a method, you can use both repository `@Query` methods and [manual queries](#query).

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

    1. Executed within the transaction, or rolled back if the whole lambda throws an exception
    2. Executed within the transaction, or rolled back if the whole lambda throws an exception

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

    1. Explicit SAM constructor, see the warning below
    2. Executed within the transaction, or rolled back if the whole lambda throws an exception
    3. Executed within the transaction, or rolled back if the whole lambda throws an exception

!!! warning "Kotlin"

    `inTx` has several overloads that all accept a single functional argument, so a bare `Kotlin` lambda cannot be resolved.
    Pass an explicit SAM constructor instead: `JdbcExecutor.SqlSupplier { … }` when the block returns a value and
    `JdbcExecutor.SqlRunnable { … }` when it does not.
    Without it the compiler reports `Overload resolution ambiguity` or `Cannot infer type for type parameter T`,
    neither of which points at the transaction.

The transaction is considered successfully committed after the method completes if it did not throw an exception.
If the method throws an exception, all database changes made within the transaction are rolled back
and the exception is rethrown.

The connection is bound to the executing scope, so work handed off to an unrelated thread does not join
the current transaction — it acquires its own connection instead.

### Isolation level { #isolation }

By default a transaction runs with the isolation level configured for the driver, the database,
or the [connection pool](#pool-customization) — for most databases that is `READ_COMMITTED`.
To request another level for one transaction, pass a `JdbcExecutor.TxIsolation` value as the first argument of `inTx`:
`READ_UNCOMMITTED`, `READ_COMMITTED`, `REPEATABLE_READ`, or `SERIALIZABLE`.
The previous level of the connection is restored after the transaction completes.

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

The isolation level is applied only when `inTx` actually opens a transaction.
A nested `inTx` inside an already open transaction reuses it and ignores the argument.

### Multi-repository Transactions

When your application uses multiple repositories, you can combine their operations in a single transaction.
All repositories that `extend JdbcRepository` share the same `JdbcConnectionFactory` (unless a separate `@Tag` for a different database is specified).
`JdbcConnectionFactory` stores the connection in the `Context` of the current thread.
When entering `inTx`, the connection is saved to the context.
Any `@Query` method of any repository called inside `inTx` checks the context and uses the existing connection instead of creating a new one.
Thus, all operations in the lambda execute on the same connection and in the same transaction.

If any of the calls throws an exception — all changes are rolled back.

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

**Limitation:** If repositories are connected to different databases (via `@Tag(OtherDatabase.class)`), they use different `JdbcConnectionFactory` instances — the transaction does NOT propagate between them.

### Manual Connection Management { #connection }

If a query needs more complex logic or queries outside a repository, you can use `java.sql.Connection`.
The `withConnection` method executes code with a connection, but does not open a transaction by itself.

`withConnection` works as follows:

- if the current scope already contains a `ConnectionContext`, the method passes the current connection to the lambda;
- if the current scope does not contain a connection, the method takes a new connection from the pool, binds it to a `ConnectionContext` for the duration of the lambda, and closes it after completion;
- nested calls to `withConnection`, [manual queries](#query), and repository methods inside this lambda use the same current connection;
- a `java.sql.SQLException` is wrapped into `UncheckedSqlException`.

`withContext` is the same thing but hands over the `ConnectionContext` instead of the raw `Connection`,
which is what you need to register [post-commit](#post-commit-actions) and [post-rollback](#post-rollback-actions) actions.
`currentConnection` and `currentContext` return the connection bound to the current scope or `null` when there is none,
and `acquireConnection` takes a brand new connection from the pool that the caller must close.

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

The `inTx` method opens a transaction and is built on top of `withContext`.
If the current connection is already in an active transaction, meaning `autoCommit = false`, nested `inTx` uses the same transaction.
If there is no active transaction, `inTx` disables `autoCommit`, executes the lambda, and then calls `commit` on success or `rollback` on exception.

A `@Query` method can also accept a `java.sql.Connection` argument.
The generated code prepares the statement on exactly that connection instead of the current one,
which is useful when the connection comes from outside the repository:

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

### Post-Commit Actions { #post-commit-actions }

If you need to perform actions after a transaction is successfully committed, register them on the `ConnectionContext`
with `afterCommit`.
The action receives the connection, is executed after `commit`, and only if the transaction completed successfully.
Such actions can be added only inside an active transaction — otherwise `afterCommit` throws `IllegalStateException`.

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

    1.  The single-argument `inTx` overload hands over the `ConnectionContext` of the current transaction

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

    1.  The single-argument `inTx` overload hands over the `ConnectionContext` of the current transaction

An exception thrown by a post-commit action is propagated to the caller, but the transaction stays committed.

### Post-Rollback Actions { #post-rollback-actions }

If you need to perform actions after a transaction is rolled back, register them with `afterRollback`.
The action receives the connection and the exception that caused the transaction to roll back.
Such actions can be added only inside an active transaction — otherwise `afterRollback` throws `IllegalStateException`.

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

An exception thrown by a post-rollback action does not replace the original failure:
it is attached to it as a suppressed exception.

## Signatures { #signatures }

`JDBC` repository contracts are synchronous — a method blocks the calling thread until the database answers.
`Kora` server transports dispatch request handling onto virtual threads, so a blocking `JDBC` call does not hold a platform thread.
There are no asynchronous or reactive repository signatures.

Available repository method signatures out of the box:

===! ":fontawesome-brands-java: `Java`"

    `T` means the return value type.

    - `T myMethod()` — the result must not be `null`
    - `@Nullable T myMethod()`
    - `Optional<T> myMethod()`
    - `List<T> myMethod()`
    - `void myMethod()`
    - `UpdateCount myMethod()` — number of affected rows
    - `int[] myMethod(@Batch List<T> values)` / `long[] myMethod(@Batch List<T> values)` — per-row results of a [batch query](database-common.md#batch-query)

=== ":simple-kotlin: `Kotlin`"

    `T` means the return value type.

    - `fun myMethod(): T` — the result must not be `null`
    - `fun myMethod(): T?`
    - `fun myMethod(): List<T>`
    - `fun myMethod()` — returns `Unit`
    - `fun myMethod(): UpdateCount` — number of affected rows
    - `fun myMethod(@Batch values: List<T>): IntArray` / `fun myMethod(@Batch values: List<T>): LongArray` — per-row results of a [batch query](database-common.md#batch-query)

To bind a repository to a data source other than the default one, use the `executorTag` attribute
of `@Repository`, see [Additional data sources](#additional-data-sources).

## Telemetry { #telemetry }

Logging, metrics, and tracing are configured via the `telemetry` block in the [configuration](#configuration) and described in the [Metrics Reference](metrics.md#database) section.
The `Hikari` pool reports its own metrics as long as `telemetry.metrics.driverMetrics` is enabled.
To completely override telemetry, you can provide custom SPI factories; see the [Common Database Documentation](database-common.md#telemetry) for details.
