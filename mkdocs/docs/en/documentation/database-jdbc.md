Module provides a repository implementation based on the [JDBC](https://proselyte.net/tutorials/jdbc/introduction/) database protocol
and using [Hikari](https://github.com/brettwooldridge/HikariCP) for connection set management.

## Dependency

=== ":fontawesome-brands-java: `Java`"

    Dependency `build.gradle`:
    ```groovy
    annotationProcessor "ru.tinkoff.kora:annotation-processors"
    implementation "ru.tinkoff.kora:database-jdbc"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends JdbcDatabaseModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Dependency `build.gradle.kts`:
    ```groovy
    ksp("ru.tinkoff.kora:symbol-processors")
    implementation("ru.tinkoff.kora:database-jdbc")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : JdbcDatabaseModule
    ```

Also **required to provide** the database driver implementation as a dependency.

## Configuration

Parameters described in the `JdbcDatabaseConfig` class:

===! ":material-code-json: `Hocon`"

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
            }
            telemetry {
                enabled = true //(19)!
            }
        }
    }
    ```

    1. JDBC database connection URL **(mandatory)**
    2. Username to connect **(required)**
    3. Password of the user to connect **(required)**
    4. Database schema for the connection
    5. Name of the database connection set in Hikari **(required)**
    6. Maximum size of the database connection set in Hikari
    7. Minimum size of the set of ready connections to the database in Hikari in standby mode
    8. Maximum time to establish a connection in Hikari
    9. Maximum time for connection verification in Hikari
    10. Maximum time for connection downtime in Hikari
    11. Maximum lifetime of a connection in Hikari
    12. Maximum time a connection can be idle in Hikari before it is considered a leak (disabled by default)
    13. Maximum time to wait for connection initialization at service startup (disabled by default)
    14. Whether to enable [probes.md#_2](probes.md#_2) for database connection
    15. Additional JDBC connection attributes `dataSourceProperties` (below example `hostRecheckSeconds` parameters)
    16. Whether to enable module logging
    17. Enables module metrics (default `true`)
    18. Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    19. Enables module tracing (default `true`)

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
      initializationFailTimeout: "0s" //(13)!
      readinessProbe: false //(14)!
      dsProperties: #(15)!
        hostRecheckSeconds: "1"  
      telemetry:
        logging:
          enabled: true #(16)!
        metrics:
          enabled: true #(17)!
          slo: [ 2, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(18)!
        telemetry:
          enabled: true #(19)!
    }
    ```

    1. JDBC database connection URL **(mandatory)**
    2. Username to connect **(required)**
    3. Password of the user to connect **(required)**
    4. Database schema for the connection
    5. Name of the database connection set in Hikari **(required)**
    6. Maximum size of the database connection set in Hikari
    7. Minimum size of the set of ready connections to the database in Hikari in standby mode
    8. Maximum time to establish a connection in Hikari
    9. Maximum time for connection verification in Hikari
    10. Maximum time for connection downtime in Hikari
    11. Maximum lifetime of a connection in Hikari
    12. Maximum time a connection can be idle in Hikari before it is considered a leak (disabled by default)
    13. Maximum time to wait for connection initialization at service startup (disabled by default)
    14. Whether to enable [probes.md#_2](probes.md#_2) for database connection
    15. Additional JDBC connection attributes `dataSourceProperties` (below example `hostRecheckSeconds` parameters)
    16. Whether to enable module logging
    17. Enables module metrics (default `true`)
    18. Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    19. Enables module tracing (default `true`)

## Usage

=== ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository
    ```

## Mapping

It is possible to override the conversion of different parts of [entity](database-common.md) and query parameters, Kora provides special interfaces for this.

### Result

If you need to convert the result manually, it is suggested to use `JdbcResultSetMapper`:

=== ":fontawesome-brands-java: `Java`"

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
    class ResultMapper : JdbcResultSetMapper<Long> {

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

### Row

If you need to convert the string manually, it is suggested to use `JdbcRowMapper`:

=== ":fontawesome-brands-java: `Java`"

    ```java
    final class RowMapper implements JdbcRowMapper<UUID> {

        @Override
        public UUID apply(ResultSet rs) throws SQLException {
            return UUID.fromString(rs.getString(0));
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
            return UUID.fromString(rs.getString(0))
        }
    }

    @Repository
    interface EntityRepository : JdbcRepository {

        @Mapping(RowMapper::class)
        @Query("SELECT id FROM entities")
        fun findAll(): List<UUID>
    }
    ```

### Column

If you need to convert the column value manually, it is suggested to use the `JdbcResultColumnMapper`:

=== ":fontawesome-brands-java: `Java`"

    ```java
    public final class ColumnMapper implements JdbcResultColumnMapper<UUID> {

        @Override
        public UUID apply(ResultSet row, int index) throws SQLException {
            return UUID.fromString(row.getString(index));
        }
    }

    @Table("entities")
    public record Entity(@Mapping(ColumnMapper.class) @Id UUID id, String name) { }

    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("SELECT * FROM entities")
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

    @Table("entities")
    data class Entity(
        @Id @Mapping(ColumnMapper::class) val id: UUID,
        val name: String
    )

    @Repository
    interface EntityRepository : JdbcRepository {

        @Query("SELECT * FROM entities")
        fun findAll(): List<Entity>
    }
    ```

### Parameter

If you want to convert the value of a query parameter manually, it is suggested to use `JdbcParameterColumnMapper`:

=== ":fontawesome-brands-java: `Java`"

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

        @Query("SELECT * FROM entities WHERE id = :id")
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

        @Query("SELECT * FROM entities WHERE id = :id")
        fun findById(@Mapping(ParameterMapper::class) id: UUID): List<Entity>
    }
    ```

## Transactions

In order to execute blocking queries, Kora has a `JdbcConnectionFactory` interface, which is provided in a method within the `JdbcRepository` contract.
All repository methods called within a transaction lambda will be executed in that transaction.

In order to execute queries transactionally, the `inTx` contract can be used:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final EntityRepository repository;

        public SomeService(EntityRepository repository) {
            this.repository = repository;
        }

        public List<Entity> saveAll(Entity one, Entity two) {
            return repository.getJdbcConnectionFactory().inTx(() -> {
                repository.insert(one); //(1)!
                // do some work
                repository.insert(two); //(2)!
                return List.of(one, two);
            });
        }
    }
    ```

    1. will be executed within the transaction or rolled back if the entire lambda throws an exception
    2. will be executed within the transaction or rolled back if the entire lambda throws an exception

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(private val repository: EntityRepository) {

        fun saveAll(one: List<Entity>, two: List<Entity>): List<Entity> {
            return repository.jdbcConnectionFactory.inTx(SqlFunction1 {
                repository.insert(one) //(1)!
                // do some work
                repository.insert(two) //(2)!
                one + two
            })
        }
    }
    ```

    1. will be executed within the transaction or rolled back if the entire lambda throws an exception
    2. will be executed within the transaction or rolled back if the entire lambda throws an exception

The isolation level is taken from the `dsProperties` configuration of the Hikari pool,
or you can change it yourself via `java.sql.Connection` before executing queries.

```java
connection.setTransactionIsolation(Connection.TRANSACTION_READ_COMMITTED);
```

### Connection

If you need some more complex logic for a query and `@Query` is not enough, you can use `java.sql.Connection`:

=== ":fontawesome-brands-java: `Java`"

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

## Signatures

Available signatures for repository methods out of the box:

=== ":fontawesome-brands-java: `Java`"

    The `T` refers to the type of the return value, either `Void` or `UpdateCount`.

    - `T myMethod()`
    - `@Nullable T myMethod()`
    - `Optional<T> myMethod()`
    - `List<T> myMethod()`
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/)
    - `Mono<List<T>>> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/)

=== ":simple-kotlin: `Kotlin`"

    By `T` we mean the type of the return value, either `Unit` or `UpdateCount`.

    - `myMethod(): T`
    - `myMethod(): T?`
    - `myMethod(): List<T>`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine)
    - `suspend myMethod(): T?` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine)
    - `suspend myMethod(): List<T>?` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine)
