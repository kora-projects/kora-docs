Module provides a repository implementation based on [R2DBC](https://r2dbc.io/) reactive database protocol,
the implementation as an example is [Postgres R2DBC](https://github.com/pgjdbc/r2dbc-postgresql).

## Dependency

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:database-r2dbc"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends R2dbcDatabaseModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:database-r2dbc")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : R2dbcDatabaseModule
    ```

Also **required to provide** the database driver implementation as a dependency.

## Configuration

Example of the complete configuration described in the `R2dbcDatabaseConfig` class (default or example values are specified):

===! ":material-code-json: `Hocon`"

    ```javascript
    db {
        r2dbcUrl = "r2dbc:postgresql://localhost:5432/postgres" //(1)!
        username = "postgres" //(2)!
        password = "postgres" //(3)!
        poolName = "kora" //(4)!
        maxPoolSize = 10 //(5)!
        minIdle = 0 //(6)!
        acquireRetry = 3 //(7)!
        connectionTimeout = "10s" //(8)!
        connectionCreateTimeout = "30s" //(9)!
        idleTimeout = "1m" //(10)!
        maxLifetime = "0s" //(11)!
        statementTimeout = "0s" //(12)!
        readinessProbe = false //(13)!
        options { //(14)!
            "backgroundEvictionInterval": "PT120S"
        }
        telemetry {
            logging {
                enabled = false //(15)!
            }
            metrics {
                enabled = true //(16)!
                slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(17)!
            }
            tracing {
                enabled = true //(18)!
            }
        }
    }
    ```

    1. R2DBC database connection URL (**required**)
    2. User name for connection (**required**)
    3. Password of the user to connect (**required**)
    4. Database Connection Set Name (**required**)
    5. Maximum size of the database connection set
    6. Minimum idle size of the ready database connection set
    7. Maximum number of attempts to obtain a connection
    8. Maximum time to establish a connection
    9. Maximum time to establish a connection
    10. Maximum time for connection downtime
    11. Maximum connection lifetime (optional)
    12. Maximum time to execute a query to the database (optional)
    13. Whether to enable [probes.md#_2](probes.md#_2) for database connection
    14. Additional attributes of R2DBC connection (optional)
    15. Enables module logging (default `false`)
    16. Enables module metrics (default `true`)
    17. Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    18. Enables module tracing (default `true`)

=== ":simple-yaml: `YAML`"

    ```yaml
    db:
      r2dbcUrl: "r2dbc:postgresql://localhost:5432/postgres" #(1)!
      username: "postgres" #(2)!
      password: "postgres" #(3)!
      poolName: "kora" #(4)!
      maxPoolSize: 10 #(5)!
      minIdle: 0 #(6)!
      acquireRetry: 3 #(7)!
      connectionTimeout: "10s" #(8)!
      connectionCreateTimeout: "30s" #(9)!
      idleTimeout: "1m" #(10)!
      maxLifetime: "0s" #(11)!
      statementTimeout: "0ms" #(12)!
      readinessProbe: false #(13)!
      options: #(14)!
        backgroundEvictionInterval: "PT120S"
      telemetry:
        logging:
          enabled: false #(15)!
        metrics:
          enabled: true #(16)!
          slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(17)!
        tracing:
          enabled: true #(18)!
    ```

    1. R2DBC database connection URL (**required**)
    2. User name for connection (**required**)
    3. Password of the user to connect (**required**)
    4. Database Connection Set Name (**required**)
    5. Maximum size of the database connection set
    6. Minimum idle size of the ready database connection set
    7. Maximum number of attempts to obtain a connection
    8. Maximum time to establish a connection
    9. Maximum time to establish a connection
    10. Maximum time for connection downtime
    11. Maximum connection lifetime (optional)
    12. Maximum time to execute a query to the database (optional)
    13. Whether to enable [probes.md#_2](probes.md#_2) for database connection
    14. Additional attributes of R2DBC connection (optional)
    15. Enables module logging (default `false`)
    16. Enables module metrics (default `true`)
    17. Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    18. Enables module tracing (default `true`)

## Usage

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends R2dbcRepository { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : R2dbcRepository
    ```

## Mapping

It is possible to override the conversion of different parts of [entity](database-common.md) and query parameters, Kora provides special interfaces for this.

### Result

If you need to convert the result manually, it is suggested to use `R2dbcResultFluxMapper`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    final class ResultMapper implements R2dbcResultFluxMapper<UUID, Flux<UUID>> {

        @Override
        public Flux<UUID> apply(Flux<Result> resultFlux) {
            // mapping code
        }
    }

    @Repository
    public interface EntityRepository extends R2dbcRepository {

        @Mapping(ResultMapper.class)
        @Query("SELECT id FROM entities")
        Flux<UUID> getIds();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class ResultMapper : R2dbcResultFluxMapper<UUID, Flux<UUID>> {
        override fun apply(resultFlux: Flux<Result>): Flux<UUID> {
            // mapping code
        }
    }

    @Repository
    interface EntityRepository : R2dbcRepository {

        @Mapping(ResultMapper::class)
        @Query("SELECT id FROM entities")
        fun getIds(): Flux<UUID>
    }
    ```

### Row

If you need to convert the string manually, it is suggested to use `R2dbcRowMapper`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    final class RowMapper implements R2dbcRowMapper<UUID> {

        @Override
        public UUID apply(Row row) {
            return UUID.fromString(rs.get(0, String.class));
        }
    }

    @Repository
    public interface EntityRepository extends R2dbcRepository {

        @Mapping(RowMapper.class)
        @Query("SELECT id FROM entities")
        Flux<UUID> findAll();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class RowMapper : R2dbcRowMapper<UUID> {

        override fun apply(row: Row): UUID {
            return UUID.fromString(rs.get(0, String.class))
        }
    }

    @Repository
    interface EntityRepository : R2dbcRepository {

        @Mapping(RowMapper::class)
        @Query("SELECT id FROM entities")
        fun findAll(): Flux<UUID>
    }
    ```

### Column

If you need to convert the column value manually, it is suggested to use the `R2dbcResultColumnMapper`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class ColumnMapper implements R2dbcResultColumnMapper<UUID> {

        @Override
        public UUID apply(Row row, String label) {
            return UUID.fromString(row.get(label, String.class));
        }
    }

    @Table("entities")
    public record Entity(@Mapping(ColumnMapper.class) @Id UUID id, String name) { }

    @Repository
    public interface EntityRepository extends R2dbcRepository {

        @Query("SELECT id, name FROM entities")
        Flux<Entity> findAll();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class ColumnMapper : R2dbcResultColumnMapper<UUID> {

        override fun apply(row: Row, label: String): UUID {
            return UUID.fromString(row.get(label, String.class))
        }
    }

    @Table("entities")
    data class Entity(
        @Id @Mapping(ColumnMapper::class) val id: UUID,
        val name: String
    )

    @Repository
    interface EntityRepository : R2dbcRepository {

        @Query("SELECT id, name FROM entities")
        fun findAll(): Flux<Entity>
    }
    ```

### Parameter

If you want to convert the value of a query parameter manually, it is suggested to use `R2dbcParameterColumnMapper`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class ParameterMapper implements R2dbcParameterColumnMapper<UUID> {

        @Override
        public void set(Statement stmt, int index, @Nullable UUID value) {
            if (value != null) {
                stmt.bind(index, value.toString());
            }
        }
    }

    @Repository
    public interface EntityRepository extends R2dbcRepository {

        @Query("SELECT id, name FROM entities WHERE id = :id")
        Flux<Entity> findById(@Mapping(ParameterMapper.class) UUID id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class ParameterMapper : R2dbcParameterColumnMapper<UUID?> {

        override fun set(stmt: Statement, index: Int, value: UUID?) {
            if (value != null) {
                stmt.bind(index, value.toString())
            }
        }
    }

    @Repository
    interface EntityRepository : R2dbcRepository {

        @Query("SELECT id, name FROM entities WHERE id = :id")
        fun findById(@Mapping(ParameterMapper::class) id: UUID): Flux<Entity>
    }
    ```

### Supported types

??? abstract "List of supported types for arguments/return values out of the box"

    These types are chosen because they are supported by most popular databases.

    * void
    * boolean / Boolean
    * short / Short
    * int / Integer
    * long / Long
    * double / Double
    * float / Float
    * byte[]
    * String
    * BigInteger
    * BigDecimal
    * UUID
    * LocalDate
    * LocalTime
    * LocalDateTime
    * OffsetTime
    * OffsetDateTime

## Generated identifier

If you want to get the primary keys of an entity created by the database as the result,
it is suggested to use the `@Id` annotation over a method where the return value type is identifiers.
This approach works for `@Batch` queries as well.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends R2dbcRepository {

        public record Entity(Long id, String name) {}

        @Query("INSERT INTO entities(name) VALUES (:entity.name)")
        @Id
        Mono<Long> insert(Entity entity);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : R2dbcRepository {

        public record Entity(Long id, String name) {}

        @Query("INSERT INTO entities(name) VALUES (:entity.name)")
        @Id
        fun insert(entity: Entity): Mono<Long>
    }
    ```

## Transactions

In order to perform manual queries in Kora, there is an interface `ru.tinkoff.kora.database.r2dbc.R2dbcConnectionFactory`,
which is provided in a method within the `R2dbcRepository` contract.
All repository methods called within a transaction lambda will be executed in that transaction.

In order to perform queries transactionally, the `inTx` contract can be used:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final EntityRepository repository;

        public SomeService(EntityRepository repository) {
            this.repository = repository;
        }

        public Mono<List<Entity>> saveAll(Entity one, Entity two) {
            return repository.getR2dbcConnectionFactory().inTx(connection -> {
                // do some work
                return repository.insert(one) //(1)!
                        .zipWith(repository.insert(two), //(2)!
                            (r1, r2) -> List.of(one, two));
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

        fun saveAll(
            one: Entity,
            two: Entity
        ): Mono<List<Entity>> {
            return repository.r2dbcConnectionFactory.inTx {
                repository.insert(one).zipWith(repository.insert(two)) //(1)!
                { r1: UpdateCount, r2: UpdateCount -> listOf(one, two) }
            }
        }
    }
    ```

    1. will be executed within the transaction or will be rolled back if the entire lambda throws an exception

### Connection

If you need some more complex logic for the query and `@Query` is not enough, you can use `io.r2dbc.spi.Connection`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final EntityRepository repository;

        public SomeService(EntityRepository repository) {
            this.repository = repository;
        }

        public Mono<List<Entity>> saveAll(Entity one, Entity two) {
            return repository.getR2dbcConnectionFactory().inTx(connection -> {
                // do some work
            });
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(private val repository: EntityRepository) {

        fun saveAll(
            one: Entity,
            two: Entity
        ): Mono<List<Entity>> {
            return repository.r2dbcConnectionFactory.inTx { connection ->
                // do some work
            }
        }
    }
    ```

## Signatures

Available signatures for repository methods out of the box:

===! ":fontawesome-brands-java: `Java`"

    The `T` refers to the type of the return value, either `List<T>`, either `Void` or `UpdateCount`.

    - `T myMethod()`
    - `@Nullable T myMethod()`
    - `Optional<T> myMethod()`
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (require [dependency](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))
    - `Flux<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (require [dependency](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

=== ":simple-kotlin: `Kotlin`"

    By `T` we mean the type of the return value, either `T?`, either `List<T>`, either `Unit` or `UpdateCount`.

    - `myMethod(): T`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (require [dependency](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) as `implementation`)
    - `myMethod(): Flow<T>` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (require [dependency](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) as `implementation`)
