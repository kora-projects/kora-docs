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

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("SELECT id, name FROM entities WHERE id = :id")
        @Nullable
        Entity findById(long id);

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        UpdateCount insert(Entity entity);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Query("SELECT id, name FROM entities WHERE id = :id")
        fun findById(id: Long): Entity?

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        fun insert(entity: Entity): UpdateCount
    }
    ```

`SQL` remains under the developer's control: you can use database-specific features, while `Kora` only handles safe
parameter binding, query execution, and result mapping.
Common rules for entities, `@Table`, `@Column`, `@Id`, `@Embedded`, `@Batch`, and macros are described in
[Common database rules](database-common.md).

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

#### Entity { #entity }

Use the `@EntityJdbc` annotation for optimal entity mapping.
The annotation processor creates a result mapper for such a type ahead of time.

All nested entities are also expected to use this annotation.

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

    Entity fields without an explicit `@Mapping` natively support `boolean` / `Boolean`, `short` / `Short`,
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
