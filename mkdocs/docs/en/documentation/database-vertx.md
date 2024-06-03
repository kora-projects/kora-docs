Module provides a repository implementation based on the [Vertx](https://vertx.io/docs/#databases) reactive protocol.

## Dependency

=== ":fontawesome-brands-java: `Java`"

    Dependency `build.gradle`:
    ```groovy
    annotationProcessor "ru.tinkoff.kora:annotation-processors"
    implementation "ru.tinkoff.kora:database-vertx"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends VertxDatabaseModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Dependency `build.gradle.kts`:
    ```groovy
    ksp("ru.tinkoff.kora:symbol-processors")
    implementation("ru.tinkoff.kora:database-vertx")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : VertxDatabaseModule
    ```

It is also **required to provide** a driver implementation as a dependency of a version no higher than [4.3.8](https://mvnrepository.com/artifact/io.vertx/vertx-pg-client/4.3.8)

In some cases, such as with a [PostgreSQL](https://postgrespro.ru/docs/postgresql) database, it is also required to add [dependency](https://mvnrepository.com/artifact/com.ongres.scram/client/2.1).

## Configuration

Example of the complete configuration described in the `VertxDatabaseConfig` class (default or example values are specified):

===! ":material-code-json: `Hocon`"

    ```javascript
    db {
        connectionUri = "postgresql://localhost:5432/postgres" //(1)!
        username = "postgres" //(2)!
        password = "postgres" //(3)!
        poolName = "kora" //(4)!
        maxPoolSize = 10 //(5)!
        connectionTimeout = "10s" //(6)!
        acquireTimeout = "0s" //(7)!
        idleTimeout = "10m" //(8)!
        cachePreparedStatements = true //(9)!
        initializationFailTimeout = "0s" //(10)!
        readinessProbe = false //(11)!
        telemetry {
            logging {
                enabled = false //(12)!
            }
            metrics {
                enabled = true //(13)!
                slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(14)!
            }
            telemetry {
                enabled = true //(15)!
            }
        }
    }
    ```

    1. [URI](https://vertx.io/docs/vertx-pg-client/java/#_connection_uri) connection URI (**required**)
    2. User name for connection (**required**)
    3. Password of the user to connect (**required**)
    4. Database connection set name (**required**)
    5. Maximum size of the database connection set
    6. Maximum time to establish a connection
    7. Maximum time to get a connection from a connection set (optional)
    8. Maximum time for connection downtime
    9. Whether to cache prepared requests
    10. Maximum time to wait for connection initialization at service startup (optional)
    11. Whether to enable [probes.md#_2](probes.md#_2) for database connection
    12. Enables module logging (default `false`)
    13. Enables module metrics (default `true`)
    14. Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    15. Enables module tracing (default `true`)

=== ":simple-yaml: `YAML`"

    ```yaml
    db:
      connectionUri = "postgresql://localhost:5432/postgres" #(1)!
      username: "postgres" #(2)!
      password: "postgres" #(3)!
      poolName: "kora" #(4)!
      maxPoolSize: 10 #(5)!
      connectionTimeout: "10s" #(6)!
      acquireTimeout: "10s" #(7)!
      idleTimeout: "10m" #(8)!
      cachePreparedStatements: true #(9)!
      initializationFailTimeout: "0s" #(10)!
      readinessProbe: false #(11)!
      telemetry:
        logging:
          enabled: false #(12)!
        metrics:
          enabled: true #(13)!
          slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(14)!
        telemetry:
          enabled: true #(15)!
    ```

    1. [URI](https://vertx.io/docs/vertx-pg-client/java/#_connection_uri) connection URI (**required**)
    2. User name for connection (**required**)
    3. Password of the user to connect (**required**)
    4. Database connection set name (**required**)
    5. Maximum size of the database connection set
    6. Maximum time to establish a connection
    7. Maximum time to get a connection from a connection set (optional)
    8. Maximum time for connection downtime
    9. Whether to cache prepared requests
    10. Maximum time to wait for connection initialization at service startup (optional)
    11. Whether to enable [probes.md#_2](probes.md#_2) for database connection
    12. Enables module logging (default `false`)
    13. Enables module metrics (default `true`)
    14. Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    15. Enables module tracing (default `true`)

## Usage

=== ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends VertxRepository { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : VertxRepository
    ```

## Mapping

It is possible to override the conversion of different parts of [entity](database-common.md) and query parameters, Kora provides special interfaces for this.

### Result

If you need to convert the result manually, it is suggested to use `VertxRowSetMapper`:

=== ":fontawesome-brands-java: `Java`"

    ```java
    final class ResultMapper implements VertxRowSetMapper<List<UUID>> {

        @Override
        public List<UUID> apply(RowSet<Row> rows) {
            // mapping code
        }
    }

    @Repository
    public interface EntityRepository extends VertxRepository {

        @Mapping(ResultMapper.class)
        @Query("SELECT id FROM entities")
        Mono<List<UUID>> getIds();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class ResultMapper : VertxRowSetMapper<List<UUID>> {
        override fun apply(rows: RowSet<Row>): List<UUID> {
            // mapping code
        }
    }

    @Repository
    interface EntityRepository : VertxRepository {

        @Mapping(ResultMapper::class)
        @Query("SELECT id FROM entities")
        fun getIds(): Mono<List<UUID>>
    }
    ```

### Row

If you need to convert the string manually, it is suggested to use `VertxRowMapper`:

=== ":fontawesome-brands-java: `Java`"

    ```java
    final class RowMapper implements VertxRowMapper<UUID> {

        @Override
        public UUID apply(Row row) {
            return UUID.fromString(rs.get(0, String.class));
        }
    }

    @Repository
    public interface EntityRepository extends VertxRepository {

        @Mapping(RowMapper.class)
        @Query("SELECT id FROM entities")
        Flux<UUID> findAll();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class RowMapper : VertxRowMapper<UUID> {

        override fun apply(row: Row): UUID {
            return UUID.fromString(rs.get(0, String.class))
        }
    }

    @Repository
    interface EntityRepository : VertxRepository {

        @Mapping(RowMapper::class)
        @Query("SELECT id FROM entities")
        fun findAll(): Flux<UUID>
    }
    ```

### Column

If you need to convert the column value manually, it is suggested to use the `VertxResultColumnMapper`:

=== ":fontawesome-brands-java: `Java`"

    ```java
    public final class ColumnMapper implements VertxResultColumnMapper<UUID> {

        @Override
        public UUID apply(Row row, int index) {
            return UUID.fromString(row.get(String.class, index));
        }
    }

    @Table("entities")
    public record Entity(@Mapping(ColumnMapper.class) @Id UUID id, String name) { }

    @Repository
    public interface EntityRepository extends VertxRepository {

        @Query("SELECT * FROM entities")
        Flux<Entity> findAll();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class ColumnMapper : VertxResultColumnMapper<UUID> {

        override fun apply(row: Row, index: Int): UUID {
            return UUID.fromString(row.get(String.class, index))
        }
    }

    @Table("entities")
    data class Entity(
        @Id @Mapping(ColumnMapper::class) val id: UUID,
        val name: String
    )

    @Repository
    interface EntityRepository : VertxRepository {

        @Query("SELECT * FROM entities")
        fun findAll(): Flux<Entity>
    }
    ```

### Parameter

If you want to convert the value of a query parameter manually, it is suggested to use `VertxParameterColumnMapper`:

=== ":fontawesome-brands-java: `Java`"

    ```java
    public final class ParameterMapper implements VertxParameterColumnMapper<UUID> {

        @Override
        public Object apply(@Nullable UUID value) {
            return value.toString();
        }
    }

    @Repository
    public interface EntityRepository extends VertxRepository {

        @Query("SELECT * FROM entities WHERE id = :id")
        Flux<Entity> findById(@Mapping(ParameterMapper.class) UUID id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class ParameterMapper : VertxParameterColumnMapper<UUID?> {
        override fun apply(value: UUID?): Any {
            return value.toString()
        }
    }

    @Repository
    interface EntityRepository : VertxRepository {

        @Query("SELECT * FROM entities WHERE id = :id")
        fun findById(@Mapping(ParameterMapper::class) id: UUID): Flux<Entity>
    }
    ```

## Transactions

In order to perform manual queries, Kora has an interface `ru.tinkoff.kora.database.vertx.VertxConnectionFactory`,
which is provided in a method within the `VertxRepository` contract.
All repository methods called within a transaction lambda will be executed in that transaction.

In order to perform queries transactionally, the `inTx` contract can be used:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final EntityRepository repository;

        public SomeService(EntityRepository repository) {
            this.repository = repository;
        }

        public Mono<List<Entity>> saveAll(Entity one, Entity two) {
            return repository.getVertxConnectionFactory().inTx(connection -> {
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
            return repository.getVertxConnectionFactory.inTx {
                repository.insert(one).zipWith(repository.insert(two)) //(1)!
                { r1: UpdateCount, r2: UpdateCount -> listOf(one, two) }
            }
        }
    }
    ```

    1. will be executed within the transaction or will be rolled back if the entire lambda throws an exception

### Connection

If some more complex logic is needed for the query, and `@Query` is not enough, you can use `io.r2dbc.spi.Connection`:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final EntityRepository repository;

        public SomeService(EntityRepository repository) {
            this.repository = repository;
        }

        public Mono<List<Entity>> saveAll(Entity one, Entity two) {
            return repository.getVertxConnectionFactory().inTx(connection -> {
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
            return repository.getVertxConnectionFactory.inTx { connection ->
                // do some work
            }
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
    - `Flux<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/)

=== ":simple-kotlin: `Kotlin`"

    By `T` we mean the type of the return value, either `Unit` or `UpdateCount`.

    - `myMethod(): T`
    - `myMethod(): T?`
    - `myMethod(): List<T>`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine)
    - `suspend myMethod(): T?` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine)
    - `suspend myMethod(): List<T>?` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine)
    - `myMethod(): Flow<T>` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine)
