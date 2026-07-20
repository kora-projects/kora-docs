---
description: "Explains Kora JDBC repositories, JDBC configuration, result and parameter mapping, generated identifiers, transactions, and repository method signatures. Use when working with @Repository, @Query, @EntityJdbc, @Table, @Id, @Column, @Batch, JdbcDatabaseModule."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora JDBC repositories, JDBC configuration, result and parameter mapping, generated identifiers, transactions, and repository method signatures; key triggers include @Repository, @Query, @EntityJdbc, @Table, @Id, @Column, @Batch, JdbcDatabaseModule, JdbcConnectionFactory, JdbcRepository."
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
    implementation "ru.tinkoff.kora:database-jdbc"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends JdbcDatabaseModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:database-jdbc")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : JdbcDatabaseModule
    ```

You also **must provide** the database driver implementation as a dependency.

## Configuration { #configuration }

Basic JDBC configuration parameters:

===! ":material-code-json: `HOCON`"

    ```javascript
    db {
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
    db:
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

    ===! ":material-code-json: `HOCON`"

        ```javascript
        db {
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
            initializationFailTimeout = "0s" //(13)!
            readinessProbe = false //(14)!
            dsProperties { //(15)!
                "hostRecheckSeconds": "2"
            }
            telemetry {
                logging {
                    enabled = false //(16)!
                }
                metrics {
                    enabled = true //(17)!
                    slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(18)!
                    tags = { // (19)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
                tracing {
                    enabled = true //(20)!
                    attributes = { // (21)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
            }
        }
        ```

        1.  `JDBC URL` for connecting to the database (`required`, default: not specified)
        2.  Username for the connection (`required`, default: not specified)
        3.  User password for the connection (`required`, default: not specified)
        4.  Database schema for the connection (default: not specified, optional)
        5.  `Hikari` connection pool name (`required`, default: not specified)
        6.  Maximum `Hikari` connection pool size (default: `10`)
        7.  Minimum number of idle ready connections in the `Hikari` pool (default: `0`)
        8.  Maximum time to wait for a connection from the `Hikari` pool (default: `10s`)
        9.  Maximum time for `Hikari` connection validation (default: `5s`)
        10. Maximum idle time for a `Hikari` connection (default: `10m`)
        11. Maximum lifetime of a `Hikari` connection (default: `15m`)
        12. Time after which a busy connection is considered a possible leak (default: `0s`)
        13. Maximum time to wait for connection initialization at service startup (default: not specified, optional)
        14. Whether to enable the [readiness probe](probes.md#readiness) for the database connection (default: `false`)
        15. Additional `JDBC` connection properties passed to `Hikari` `dataSourceProperties` (default: `{}`)
        16. Enables module logging (default: `false`)
        17. Enables module metrics (default: `true`)
        18. Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
        19. Configures metric tags (default: `{}`)
        20. Enables module tracing (default: `true`)
        21. Configures tracing attributes (default: `{}`)

    === ":simple-yaml: `YAML`"

        ```yaml
        db:
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
          initializationFailTimeout: "0s" #(13)!
          readinessProbe: false #(14)!
          dsProperties: #(15)!
            hostRecheckSeconds: "1"
          telemetry:
            logging:
              enabled: false #(16)!
            metrics:
              enabled: true #(17)!
              slo: [ 2, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(18)!
              tags: #(19)!
                key1: value1
                key2: value2
            tracing:
              enabled: true #(20)!
              attributes: #(21)!
                key1: value1
                key2: value2
        ```

        1.  `JDBC URL` for connecting to the database (`required`, default: not specified)
        2.  Username for the connection (`required`, default: not specified)
        3.  User password for the connection (`required`, default: not specified)
        4.  Database schema for the connection (default: not specified, optional)
        5.  `Hikari` connection pool name (`required`, default: not specified)
        6.  Maximum `Hikari` connection pool size (default: `10`)
        7.  Minimum number of idle ready connections in the `Hikari` pool (default: `0`)
        8.  Maximum time to wait for a connection from the `Hikari` pool (default: `10s`)
        9.  Maximum time for `Hikari` connection validation (default: `5s`)
        10. Maximum idle time for a `Hikari` connection (default: `10m`)
        11. Maximum lifetime of a `Hikari` connection (default: `15m`)
        12. Time after which a busy connection is considered a possible leak (default: `0s`)
        13. Maximum time to wait for connection initialization at service startup (default: not specified, optional)
        14. Whether to enable the [readiness probe](probes.md#readiness) for the database connection (default: `false`)
        15. Additional `JDBC` connection properties passed to `Hikari` `dataSourceProperties` (default: `{}`)
        16. Enables module logging (default: `false`)
        17. Enables module metrics (default: `true`)
        18. Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
        19. Configures metric tags (default: `{}`)
        20. Enables module tracing (default: `true`)
        21. Configures tracing attributes (default: `{}`)

## Usage { #usage }

A `JDBC` repository is declared as an interface annotated with `@Repository` and must extend `JdbcRepository`.
Each method annotated with `@Query` contains a regular `SQL` query. Method parameters are bound by name with the
`:parameter` syntax, and object fields can be referenced as `:entity.field`.

Entities are described with the [common database annotations](database-common.md) and marked with `@EntityJdbc`
so that `Kora` generates the view mapper at compile time (see [View](database-common.md#view)):

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

## Mapping { #mapping }

You can override the mapping of different parts of an [entity](database-common.md), a query result, and query parameters.
For this, `Kora` provides several mapper interfaces.

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

        @Throws(SQLException::class)
        override fun apply(rs: ResultSet): UUID {
            // mapping code
        }
    }

    @Repository
    interface EntityRepository : JdbcRepository {

        @Mapping(ResultMapper::class)
        @Query("SELECT id FROM entities")
        fun countIds(): List<UUID>
    }
    ```

`JdbcResultSetMapper` also exposes static helpers `singleResultSetMapper`, `listResultSetMapper`,
and `optionalResultSetMapper` that build a full-`ResultSet` mapper from a `JdbcRowMapper<T>`.

#### View { #view }

Use the `@EntityJdbc` annotation for optimal view mapping.
The annotation allows the annotation processor to generate all necessary mappers in **one round** of annotation processing.
Without this annotation, mappers are generated on-demand, which can require **multiple rounds** of processing and significantly increase compilation time.

All nested views are also expected to use this annotation.

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

        @Throws(SQLException::class)
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

        @Throws(SQLException::class)
        override fun apply(row: ResultSet, index: Int): UUID {
            return UUID.fromString(row.getString(index))
        }
    }

    @EntityJdbc
    @Table("entities")
    data class Entity(
        @Id @Mapping(ColumnMapper::class) val id: UUID,
        val name: String
    )

    @Repository
    interface EntityRepository : JdbcRepository {

        @Query("SELECT id, name FROM entities")
        fun findAll(): List<Entity>
    }
    ```

### Parameter { #parameter }

Use `JdbcParameterColumnMapper<T>` when you need to manually map a query parameter value:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class ParameterMapper implements JdbcParameterColumnMapper<UUID> {

        @Override
        public void set(PreparedStatement stmt, int index, @Nullable UUID value) throws SQLException {
            if (value != null) {
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
    class ParameterMapper : JdbcParameterColumnMapper<UUID?> {

        @Throws(SQLException::class)
        override fun set(stmt: PreparedStatement, index: Int, value: UUID?) {
            if (value != null) {
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

### Supported Types { #supported-types }

??? abstract "List of supported types for arguments/return values out of the box"

    These types are selected because they are supported by most popular databases.
    `Kora` provides built-in row, column, and parameter mappers for them.

    * void
    * boolean / Boolean
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

    View fields without an explicit `@Mapping` natively support `boolean` / `Boolean`, `short` / `Short`,
    `int` / `Integer`, `long` / `Long`, `double` / `Double`, `float` / `Float`, `byte[]`, `String`,
    `BigDecimal`, `LocalDate`, and `LocalDateTime`.
    For other types, use built-in `JdbcResultColumnMapper<T>` / `JdbcParameterColumnMapper<T>` mappers or declare custom mappers.

## Select by List { #select-by-list }

Sometimes you need to select rows by a list of values.
At the `JDBC` level, such parameters must be prepared separately by the driver because the list length is not known in advance.
`Kora` tries to perform mappings at compile time and does not rewrite `SQL` at runtime, so such parameters require a custom mapper.

`Kora` does not provide this parameter mapping out of the box, but it is easy to add yourself.
The example below shows `Postgres` through a `JDBC Array`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    class ListOfStringJdbcParameterMapper implements JdbcParameterColumnMapper<List<String>> {

        @Override
        public void set(PreparedStatement stmt, int index, List<String> value) throws SQLException {
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
    @Component
    class ListOfStringJdbcParameterMapper : JdbcParameterColumnMapper<List<String>> {

        @Throws(SQLException::class)
        override fun set(stmt: PreparedStatement, index: Int, value: List<String>) {
            val typedArray = value.toTypedArray()
            val sqlArray = stmt.connection.createArrayOf("VARCHAR", typedArray)
            stmt.setArray(index, sqlArray)
        }
    }

    @Repository
    interface EntityRepository : JdbcRepository {

        @Query("SELECT id, name FROM entities WHERE id = ANY(:ids)")
        fun findAllByIds(@Mapping(ListOfStringJdbcParameterMapper::class) ids: List<String>): List<Entity>
    }
    ```

## JSON / JSONB { #json }

A `JSON` / `JSONB` column can be mapped to a view field by registering generic
`JdbcParameterColumnMapper<T>` and `JdbcResultColumnMapper<T>` as default `@Module` components tagged with `@Json`.
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
                    jsonb.setValue(writer.toStringUnchecked(value));
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
                    return reader.readUnchecked(value);
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
                    jsonb.value = writer.toStringUnchecked(value)
                    stmt.setObject(index, jsonb)
                }
            }
        }

        @Json
        fun <T> jdbcJsonResultColumnMapper(reader: JsonReader<T>): JdbcResultColumnMapper<T> {
            return JdbcResultColumnMapper { row, index ->
                val value = row.getString(index)
                if (value == null) null else reader.readUnchecked(value)
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

The [JSON](json.md) module dependency is required so `Kora` can generate `JsonWriter` / `JsonReader` for the field type,
and the mapper `@Module` must be added to the [application graph](container.md).

## Generated Identifier { #generated-identifier }

If you need to return primary keys generated by the database,
use the `@Id` annotation on the method.
This approach also works for `@Batch` queries.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @EntityJdbc
        public record Entity(Long id, String name) {}

        @Query("INSERT INTO entities(name) VALUES (:entity.name)")
        @Id
        long insert(Entity entity);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @EntityJdbc
        data class Entity(val id: Long, val name: String)

        @Query("INSERT INTO entities(name) VALUES (:entity.name)")
        @Id
        fun insert(entity: Entity): Long
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

## Manual Query With Telemetry { #query }

If a query is hard to express as a single static `@Query`, you can create a regular method with an implementation and build `SQL` manually.
Use `JdbcConnectionFactory#query` to execute such a query.
This method creates a `PreparedStatement`, runs the query through Kora telemetry, and uses the same connection as other repository methods.
If `query` is called inside an active `inTx` transaction, the query is executed on the current transactional connection.

`QueryContext` contains the query identifier and the final `SQL`.
The query identifier is reported to telemetry, so it is convenient to use a stable name such as `Repository.method`.
Values must be passed through `PreparedStatement` parameters, not concatenated directly into the query string.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        default List<Entity> findByFilter(@Nullable String name, boolean onlyActive) {
            var sql = new StringBuilder("SELECT id, name FROM entities WHERE 1 = 1");
            var params = new ArrayList<String>();

            if (name != null) {
                sql.append(" AND name = ?");
                params.add(name);
            }
            if (onlyActive) {
                sql.append(" AND active = true");
            }

            var queryContext = new QueryContext("EntityRepository.findByFilter", sql.toString());
            return getJdbcConnectionFactory().query(queryContext, statement -> {
                for (int i = 0; i < params.size(); i++) {
                    statement.setString(i + 1, params.get(i));
                }
                try (var resultSet = statement.executeQuery()) {
                    var result = new ArrayList<Entity>();
                    while (resultSet.next()) {
                        result.add(new Entity(resultSet.getLong("id"), resultSet.getString("name")));
                    }
                    return result;
                }
            });
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        fun findByFilter(name: String?, onlyActive: Boolean): List<Entity> {
            val sql = StringBuilder("SELECT id, name FROM entities WHERE 1 = 1")
            val params = mutableListOf<String>()

            if (name != null) {
                sql.append(" AND name = ?")
                params += name
            }
            if (onlyActive) {
                sql.append(" AND active = true")
            }

            val queryContext = QueryContext("EntityRepository.findByFilter", sql.toString())
            return jdbcConnectionFactory.query(queryContext) { statement ->
                params.forEachIndexed { index, value ->
                    statement.setString(index + 1, value)
                }
                statement.executeQuery().use { resultSet ->
                    val result = mutableListOf<Entity>()
                    while (resultSet.next()) {
                        result += Entity(resultSet.getLong("id"), resultSet.getString("name"))
                    }
                    result
                }
            }
        }
    }
    ```

## Transactions { #transaction }

For executing blocking queries, `Kora` provides the `JdbcConnectionFactory` interface through the `JdbcRepository` contract.
All repository methods called inside the transaction lambda are executed in that same transaction.

Use `inTx` to execute queries transactionally.
If there is already an active transaction on the current thread, a nested `inTx` call uses the same connection and does not open
a new transaction.

A transactional sequence of operations can stay inside the repository itself as a regular method with an implementation.
This is useful when several `@Query` methods or a complex manual `SQL` query should stay next to the rest of the repository queries,
without moving technical database work to a service layer.
Inside such a method, you can use both repository `@Query` methods and `JdbcConnectionFactory#query` for a manual query with telemetry.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        UpdateCount insert(Entity entity);

        @Query("UPDATE entities SET name = :name WHERE id = :id")
        UpdateCount updateName(long id, String name);

        public List<Entity> saveAll(Entity one, Entity two) {
            return getJdbcConnectionFactory().inTx(() -> {
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
            return jdbcConnectionFactory.inTx<List<Entity>> {
                insert(one) //(1)!
                updateName(two.id, two.name) //(2)!
                listOf(one, two)
            }
        }
    }
    ```

    1. Executed within the transaction, or rolled back if the whole lambda throws an exception
    2. Executed within the transaction, or rolled back if the whole lambda throws an exception

The transaction is considered successfully committed after the method completes if it did not throw an exception.
If the method throws an exception, all database changes made within the transaction are not applied.

The transaction isolation level is taken from the `Hikari` pool `dsProperties` configuration,
or you can change it manually through `java.sql.Connection` before executing queries.

```java
connection.setTransactionIsolation(Connection.TRANSACTION_READ_COMMITTED);
```

### Manual Connection Management { #connection }

If a query needs more complex logic or queries outside a repository, you can use `java.sql.Connection`.
The `withConnection` method executes code with a connection, but does not open a transaction by itself.

`withConnection` works as follows:

- if the current `Context` already contains a `ConnectionContext`, the method passes the current connection to the lambda;
- if the current `Context` does not contain a connection, the method takes a new connection from the `DataSource`, stores it in `ConnectionContext` for the duration of the lambda, and closes it after completion;
- nested calls to `withConnection`, `JdbcConnectionFactory#query`, and repository methods inside this lambda use the same current connection;
- if a `JDBC` exception is a `SQLException`, it is wrapped in `RuntimeSqlException`.

!!! note

    Manual `query`, `withConnection`, and `inTx` calls surface a `JDBC` failure as an unchecked `RuntimeSqlException`
    that wraps the original `java.sql.SQLException`. Catch `RuntimeSqlException` (not `SQLException`) at the call site,
    and use `getCause()` to reach the underlying `SQLException`.

The `inTx` method opens a transaction and is built on top of `withConnection`.
If the current connection is already in an active transaction, meaning `autoCommit = false`, nested `inTx` uses the same transaction.
If there is no active transaction, `inTx` disables `autoCommit`, executes the lambda, and then calls `commit` on success or `rollback` on exception.
After the transaction completes, registered `addPostCommitAction` or `addPostRollbackAction` callbacks are executed.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final EntityRepository repository;

        public SomeService(EntityRepository repository) {
            this.repository = repository;
        }

        public List<Entity> saveAll(Entity one, Entity two) {
            return repository.getJdbcConnectionFactory().inTx(connection -> {
                // do some work
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
            return repository.jdbcConnectionFactory.inTx(SqlFunction1 { connection: Connection ->
                // do some work
                listOf(one, two)
            })
        }
    }
    ```

### Post-Commit Actions { #post-commit-actions }

If you need to perform actions after a transaction is successfully committed, add them with `addPostCommitAction`.
The action is executed after `commit` and only if the transaction completed successfully.
Such actions can be added only inside an active transaction.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final EntityRepository repository;

        public SomeService(EntityRepository repository) {
            this.repository = repository;
        }

        public List<Entity> saveAll(Entity one, Entity two) {
            return repository.getJdbcConnectionFactory().inTx(connection -> {
                var ccc = repository.getJdbcConnectionFactory().currentConnectionContext();
                ccc.addPostCommitAction(conn -> {
                    // do some work
                });

                // do some work
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
            return repository.jdbcConnectionFactory.inTx(SqlFunction1 { connection: Connection ->
                val ccc = repository.jdbcConnectionFactory.currentConnectionContext()!!
                ccc.addPostCommitAction { conn ->
                    // do some work
                }

                // do some work
                listOf(one, two)
            })
        }
    }
    ```

### Post-Rollback Actions { #post-rollback-actions }

If you need to perform actions after a transaction is rolled back, add them with `addPostRollbackAction`.
The action receives the connection and the exception that caused the transaction to roll back.
Such actions can be added only inside an active transaction.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final EntityRepository repository;

        public SomeService(EntityRepository repository) {
            this.repository = repository;
        }

        public List<Entity> saveAll(Entity one, Entity two) {
            return repository.getJdbcConnectionFactory().inTx(connection -> {
                var ccc = repository.getJdbcConnectionFactory().currentConnectionContext();
                ccc.addPostRollbackAction((conn, e) -> {
                    // do some work
                });

                // do some work
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
            return repository.jdbcConnectionFactory.inTx(SqlFunction1 { connection: Connection ->
                val ccc = repository.jdbcConnectionFactory.currentConnectionContext()!!
                ccc.addPostRollbackAction { conn, e ->
                    // do some work
                }

                // do some work
                listOf(one, two)
            })
        }
    }
    ```

## Signatures { #signatures }

Available repository method signatures out of the box:

===! ":fontawesome-brands-java: `Java`"

    `T` means the return value type, or `List<T>`, or `Void`, or `UpdateCount`.
    `CompletionStage<T>`, `CompletableFuture<T>`, and `Mono<T>` require an `Executor` component.

    - `T myMethod()`
    - `@Nullable T myMethod()`
    - `Optional<T> myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletionStage.html) (requires `Executor`)
    - `CompletableFuture<T> myMethod()` [CompletableFuture](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletableFuture.html) (requires `Executor`)
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (requires `Executor` and the [dependency](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

=== ":simple-kotlin: `Kotlin`"

    `T` means the return value type, or `T?`, or `List<T>`, or `Unit`, or `UpdateCount`.
    `suspend` methods require an `Executor` component.

    - `myMethod(): T`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (requires `Executor` and the [dependency](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) as `implementation`)

For asynchronous methods, you can specify a separate `Executor` tag through the `executorTag` parameter in `@Repository`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class BlockingJdbcExecutorTag {}

    @Repository(executorTag = @Tag(BlockingJdbcExecutorTag.class))
    public interface EntityRepository extends JdbcRepository {

        @Query("SELECT id, name FROM entities")
        CompletionStage<List<Entity>> findAll();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class BlockingJdbcExecutorTag

    @Repository(executorTag = Tag(BlockingJdbcExecutorTag::class))
    interface EntityRepository : JdbcRepository {

        @Query("SELECT id, name FROM entities")
        suspend fun findAll(): List<Entity>
    }
    ```

## Telemetry { #telemetry }

Logging, metrics, and tracing are configured via the `telemetry` block in the [configuration](#configuration) and described in the [Metrics Reference](metrics.md#database) section.
To completely override telemetry, you can provide custom SPI factories; see the [Common Database Documentation](database-common.md#telemetry) for details.
