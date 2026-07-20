---
description: "Explains Kora R2DBC repositories, reactive database configuration, result and parameter mapping, transactions, generated identifiers, and repository method signatures. Use when working with @Repository, @Query, @Table, @Id, @Column, @Batch, R2dbcDatabaseModule, R2dbcConnectionFactory."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora R2DBC repositories, reactive database configuration, result and parameter mapping, transactions, generated identifiers, and repository method signatures; key triggers include @Repository, @Query, @Table, @Id, @Column, @Batch, R2dbcDatabaseModule, R2dbcConnectionFactory, R2dbcRepository."
---

The module provides a repository implementation based on the [R2DBC](https://r2dbc.io/) reactive database protocol;
the driver implementation, for example, is [Postgres R2DBC](https://github.com/pgjdbc/r2dbc-postgresql).
It uses the [io.r2dbc.pool](https://github.com/r2dbc/r2dbc-pool) connection pool to manage connections.
You describe a repository interface and `SQL` queries with `@Repository` and `@Query`, and `Kora` generates an implementation
that obtains a reactive connection from the pool, binds parameters, maps the `Flux<Result>`, and participates in transactions.

Common rules for entities, `@Repository`, `@Query`, `@Batch`, `UpdateCount`, macros, manual queries, and other repository
mechanisms are described in [Common database rules](database-common.md).

## Dependency { #dependency }

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

You also **must provide** the database driver implementation as a dependency.

## Configuration { #configuration }

Example of the complete configuration described by `R2dbcDatabaseConfig` (example values or default values are shown):

===! ":material-code-json: `HOCON`"

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
        idleTimeout = "10m" //(10)!
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
                tags = { // (18)!
                    "key1" = "value1"
                    "key2" = "value2"
                }
            }
            tracing {
                enabled = true //(19)!
                attributes = { // (20)!
                    "key1" = "value1"
                    "key2" = "value2"
                }
            }
        }
    }
    ```

    1.  `R2DBC URL` for connecting to the database (`required`, default: not specified)
    2.  Username for the connection (`required`, default: not specified)
    3.  User password for the connection (`required`, default: not specified)
    4.  Connection pool name (`required`, default: not specified)
    5.  Maximum connection pool size (default: `10`)
    6.  Minimum number of idle ready connections in the pool (default: `0`)
    7.  Maximum number of attempts to acquire a connection (default: `3`)
    8.  Maximum time to acquire a connection from the pool (default: `10s`)
    9.  Maximum time to create a new physical connection (default: `30s`)
    10. Maximum idle time for a connection (default: `10m`)
    11. Maximum lifetime of a connection, `0s` means no limit (default: `0s`)
    12. Maximum time to execute a query on the database (default: not specified, optional)
    13. Whether to enable the [readiness probe](probes.md#readiness) for the database connection (default: `false`)
    14. Additional `R2DBC` connection options passed to the driver (default: `{}`)
    15. Enables module logging (default: `false`)
    16. Enables module metrics (default: `true`)
    17. Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    18. Configures metric tags (default: `{}`)
    19. Enables module tracing (default: `true`)
    20. Configures tracing attributes (default: `{}`)

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
      idleTimeout: "10m" #(10)!
      maxLifetime: "0s" #(11)!
      statementTimeout: "0s" #(12)!
      readinessProbe: false #(13)!
      options: #(14)!
        backgroundEvictionInterval: "PT120S"
      telemetry:
        logging:
          enabled: false #(15)!
        metrics:
          enabled: true #(16)!
          slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(17)!
          tags: #(18)!
            key1: value1
            key2: value2
        tracing:
          enabled: true #(19)!
          attributes: #(20)!
            key1: value1
            key2: value2
    ```

    1.  `R2DBC URL` for connecting to the database (`required`, default: not specified)
    2.  Username for the connection (`required`, default: not specified)
    3.  User password for the connection (`required`, default: not specified)
    4.  Connection pool name (`required`, default: not specified)
    5.  Maximum connection pool size (default: `10`)
    6.  Minimum number of idle ready connections in the pool (default: `0`)
    7.  Maximum number of attempts to acquire a connection (default: `3`)
    8.  Maximum time to acquire a connection from the pool (default: `10s`)
    9.  Maximum time to create a new physical connection (default: `30s`)
    10. Maximum idle time for a connection (default: `10m`)
    11. Maximum lifetime of a connection, `0s` means no limit (default: `0s`)
    12. Maximum time to execute a query on the database (default: not specified, optional)
    13. Whether to enable the [readiness probe](probes.md#readiness) for the database connection (default: `false`)
    14. Additional `R2DBC` connection options passed to the driver (default: `{}`)
    15. Enables module logging (default: `false`)
    16. Enables module metrics (default: `true`)
    17. Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    18. Configures metric tags (default: `{}`)
    19. Enables module tracing (default: `true`)
    20. Configures tracing attributes (default: `{}`)

## Usage { #usage }

An `R2DBC` repository is declared as an interface annotated with `@Repository` and must extend `R2dbcRepository`.
Each method annotated with `@Query` contains a regular `SQL` query. Method parameters are bound by name with the
`:parameter` syntax, and object fields can be referenced as `:entity.field`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends R2dbcRepository {

        @Query("SELECT id, name FROM entities WHERE id = :id")
        Mono<Entity> findById(String id);

        @Query("SELECT id, name FROM entities")
        Flux<Entity> findAll();

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        Mono<Void> insert(Entity entity);

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        Mono<UpdateCount> insertBatch(@Batch List<Entity> entities);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : R2dbcRepository {

        @Query("SELECT id, name FROM entities WHERE id = :id")
        fun findById(id: String): Mono<Entity>

        @Query("SELECT id, name FROM entities")
        fun findAll(): Flux<Entity>

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        fun insert(entity: Entity): Mono<Void>

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        fun insertBatch(@Batch entities: List<Entity>): Mono<UpdateCount>
    }
    ```

`SQL` remains under the developer's control: you can use database-specific features, while `Kora` only handles safe
parameter binding, query execution, and result mapping.
Common rules for entities, `@Table`, `@Column`, `@Id`, `@Embedded`, `@Batch`, and macros are described in
[Common database rules](database-common.md).

Reactive `Mono` and `Flux` returns are the native signatures for this module.
Blocking returns such as `Entity`, `List<Entity>`, `void`, and `UpdateCount` are also supported, but they block the calling
thread until the reactive result completes, so prefer the reactive signatures when running in a reactive context.

## Mapping { #mapping }

You can override the mapping of different parts of an [entity](database-common.md), a query result, and query parameters.
For this, `Kora` provides several mapper interfaces.

### Result { #result }

Use `R2dbcResultFluxMapper<T, P>` when you need to control the whole `Flux<Result>`.
This mapper receives the entire reactive result stream and decides how to consume it and what to return.

===! ":fontawesome-brands-java: `Java`"

    ```java
    final class ResultMapper implements R2dbcResultFluxMapper<UUID, Flux<UUID>> {

        @Override
        public Flux<UUID> apply(Flux<Result> resultFlux) {
            return resultFlux.flatMap(result -> result.map((row, meta) ->
                UUID.fromString(row.get(0, String.class))));
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
            return resultFlux.flatMap { result ->
                result.map { row, _ -> UUID.fromString(row.get(0, String::class.java)) }
            }
        }
    }

    @Repository
    interface EntityRepository : R2dbcRepository {

        @Mapping(ResultMapper::class)
        @Query("SELECT id FROM entities")
        fun getIds(): Flux<UUID>
    }
    ```

In most cases you do not need to control the whole `Flux<Result>`.
It is enough to provide a [R2dbcRowMapper](#row), and `Kora` automatically adapts it to the method return type:
the module provides ready `mono` (`Mono<T>`), `monoList` (`Mono<List<T>>`), and `flux` (`Flux<T>`) result-flux mappers built from a
single row mapper. There is also a `R2dbcResultFluxMapper.monoOptional` helper that adapts a row mapper to `Mono<Optional<T>>`.

### Row { #row }

Use `R2dbcRowMapper<T>` when you need to manually map one row of the result.
Columns are read from `io.r2dbc.spi.Row` by index (starting from `0`) or by label:

===! ":fontawesome-brands-java: `Java`"

    ```java
    final class RowMapper implements R2dbcRowMapper<EntityPart> {

        @Override
        public EntityPart apply(Row row) {
            return new EntityPart(row.get(0, String.class), row.get(1, Integer.class));
        }
    }

    @Repository
    public interface EntityRepository extends R2dbcRepository {

        @Mapping(RowMapper.class)
        @Query("SELECT id, value1 FROM entities")
        Flux<EntityPart> findAllParts();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class RowMapper : R2dbcRowMapper<EntityPart> {

        override fun apply(row: Row): EntityPart {
            return EntityPart(row.get(0, String::class.java), row.get(1, Integer::class.java))
        }
    }

    @Repository
    interface EntityRepository : R2dbcRepository {

        @Mapping(RowMapper::class)
        @Query("SELECT id, value1 FROM entities")
        fun findAllParts(): Flux<EntityPart>
    }
    ```

### Column { #column }

Use `R2dbcResultColumnMapper<T>` when you need to manually map a single column value by its label:

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
            return UUID.fromString(row.get(label, String::class.java))
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

### Parameter { #parameter }

Use `R2dbcParameterColumnMapper<T>` when you need to manually bind a query parameter value onto `io.r2dbc.spi.Statement`.
The value is bound with `stmt.bind(index, value)`, and `stmt.bindNull(index, type)` is used for `null`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class ParameterMapper implements R2dbcParameterColumnMapper<UUID> {

        @Override
        public void apply(Statement stmt, int index, @Nullable UUID value) {
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

        override fun apply(stmt: Statement, index: Int, value: UUID?) {
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

The result column mapper and the parameter mapper can be stacked on the same entity field.
This is convenient for mapping, for example, an enum both when reading a row and when binding a parameter:

===! ":fontawesome-brands-java: `Java`"

    ```java
    record Entity(String id,
                  @Mapping(FieldTypeResultMapper.class)
                  @Mapping(FieldTypeParameterMapper.class)
                  @Column("value1") FieldType field1) { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class Entity(
        val id: String,
        @Mapping(FieldTypeResultMapper::class)
        @Mapping(FieldTypeParameterMapper::class)
        @Column("value1") val field1: FieldType
    )
    ```

### Supported types { #supported-types }

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
    * BigInteger
    * BigDecimal
    * UUID
    * LocalDate
    * LocalTime
    * LocalDateTime
    * OffsetTime
    * OffsetDateTime

    For other types, use custom `R2dbcResultColumnMapper<T>` / `R2dbcParameterColumnMapper<T>` mappers,
    or a `R2dbcRowMapper<T>` / `R2dbcResultFluxMapper<T, P>`.

## Generated identifier { #generated-identifier }

If you need to return primary keys generated by the database,
use the `@Id` annotation on the method where the return value type is the identifier.
This approach also works for `@Batch` queries, in which case the method returns the list of generated identifiers.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends R2dbcRepository {

        record Entity(Long id, String name) {}

        @Query("INSERT INTO entities(name) VALUES (:entity.name)")
        @Id
        Mono<Long> insert(Entity entity);

        @Query("INSERT INTO entities(name) VALUES (:entity.name)")
        @Id
        Mono<List<Long>> insertBatch(@Batch List<Entity> entities);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : R2dbcRepository {

        data class Entity(val id: Long?, val name: String)

        @Query("INSERT INTO entities(name) VALUES (:entity.name)")
        @Id
        fun insert(entity: Entity): Mono<Long>

        @Query("INSERT INTO entities(name) VALUES (:entity.name)")
        @Id
        fun insertBatch(@Batch entities: List<Entity>): Mono<List<Long>>
    }
    ```

Alternatively, you can return generated columns explicitly with a `RETURNING` clause and map them as a regular result,
without the `@Id` annotation:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Query("INSERT INTO entities(name) VALUES (:entity.name) RETURNING id")
    Mono<Long> insert(Entity entity);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Query("INSERT INTO entities(name) VALUES (:entity.name) RETURNING id")
    fun insert(entity: Entity): Mono<Long>
    ```

## Manual Query With Telemetry { #query }

If a query is hard to express as a single static `@Query`, you can create a regular method with an implementation and build `SQL` manually.
Use `R2dbcConnectionFactory#query` to execute such a query.
This method creates an `io.r2dbc.spi.Statement`, runs the query through Kora telemetry, and uses the same connection as other repository methods.
If `query` is called inside an active `inTx` transaction, the query is executed on the current transactional connection.

`query` takes three arguments:

- a `QueryContext` with the query identifier and the final `SQL`. The query identifier is reported to telemetry, so it is convenient to use a stable name such as `Repository.method`;
- a `Consumer<Statement>` that binds parameter values. Values must be bound through `Statement` (`stmt.bind(...)`), not concatenated directly into the query string;
- a `Function<Flux<Result>, Mono<T>>` that consumes the reactive result and produces the return value.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends R2dbcRepository {

        default Mono<List<Entity>> findByFilter(@Nullable String name, boolean onlyActive) {
            var sql = new StringBuilder("SELECT id, name FROM entities WHERE 1 = 1");
            var params = new ArrayList<String>();

            if (name != null) {
                params.add(name);
                sql.append(" AND name = $").append(params.size());
            }
            if (onlyActive) {
                sql.append(" AND active = true");
            }

            var queryContext = new QueryContext("EntityRepository.findByFilter", sql.toString());
            return getR2dbcConnectionFactory().query(
                queryContext,
                statement -> {
                    for (int i = 0; i < params.size(); i++) {
                        statement.bind(i, params.get(i));
                    }
                },
                resultFlux -> resultFlux
                    .flatMap(result -> result.map((row, meta) ->
                        new Entity(row.get("id", String.class), row.get("name", String.class))))
                    .collectList()
            );
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : R2dbcRepository {

        fun findByFilter(name: String?, onlyActive: Boolean): Mono<List<Entity>> {
            val sql = StringBuilder("SELECT id, name FROM entities WHERE 1 = 1")
            val params = mutableListOf<String>()

            if (name != null) {
                params += name
                sql.append(" AND name = $").append(params.size)
            }
            if (onlyActive) {
                sql.append(" AND active = true")
            }

            val queryContext = QueryContext("EntityRepository.findByFilter", sql.toString())
            return r2dbcConnectionFactory.query(
                queryContext,
                { statement ->
                    params.forEachIndexed { index, value ->
                        statement.bind(index, value)
                    }
                },
                { resultFlux ->
                    resultFlux
                        .flatMap { result -> result.map { row, _ ->
                            Entity(row.get("id", String::class.java), row.get("name", String::class.java))
                        } }
                        .collectList()
                }
            )
        }
    }
    ```

## Transactions { #transactions }

For executing manual queries and grouping queries into a transaction, `Kora` provides the `R2dbcConnectionFactory` interface
through the `R2dbcRepository` contract, obtained via `getR2dbcConnectionFactory()`.
All repository methods called inside the transaction lambda are executed in that same transaction.

Use `inTx` to execute queries transactionally.
If there is already an active transaction on the current reactive `Context`, a nested `inTx` call reuses the same connection and does not open
a new transaction.

A transactional sequence of operations can stay inside the repository itself as a regular method with an implementation.
This is useful when several `@Query` methods or a complex manual `SQL` query should stay next to the rest of the repository queries,
without moving technical database work to a service layer.
Inside such a method, you can use both repository `@Query` methods and `R2dbcConnectionFactory#query` for a manual query with telemetry.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends R2dbcRepository {

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        Mono<UpdateCount> insert(Entity entity);

        @Query("UPDATE entities SET name = :name WHERE id = :id")
        Mono<UpdateCount> updateName(String id, String name);

        default Mono<List<Entity>> saveAll(Entity one, Entity two) {
            return getR2dbcConnectionFactory().inTx(connection ->
                insert(one) //(1)!
                    .then(updateName(two.id(), two.name())) //(2)!
                    .thenReturn(List.of(one, two)));
        }
    }
    ```

    1. Executed within the transaction, or rolled back if the whole chain signals an error
    2. Executed within the transaction, or rolled back if the whole chain signals an error

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : R2dbcRepository {

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        fun insert(entity: Entity): Mono<UpdateCount>

        @Query("UPDATE entities SET name = :name WHERE id = :id")
        fun updateName(id: String, name: String): Mono<UpdateCount>

        fun saveAll(one: Entity, two: Entity): Mono<List<Entity>> {
            return r2dbcConnectionFactory.inTx { _ ->
                insert(one) //(1)!
                    .then(updateName(two.id, two.name)) //(2)!
                    .thenReturn(listOf(one, two))
            }
        }
    }
    ```

    1. Executed within the transaction, or rolled back if the whole chain signals an error
    2. Executed within the transaction, or rolled back if the whole chain signals an error

The transaction is committed when the returned `Mono` completes successfully.
If the `Mono` signals an error, the transaction is rolled back and the error is propagated, so all database changes made within
the transaction are not applied.

### Manual Connection Management { #connection }

If a query needs more complex logic or queries outside a repository, you can work with `io.r2dbc.spi.Connection` directly.
The `withConnection` method executes code with a connection, but does not open a transaction by itself.

`withConnection` works as follows:

- if the current reactive `Context` already contains a connection, the method passes that current connection to the lambda;
- if the current `Context` does not contain a connection, the method takes a new connection from the pool, stores it in the `Context` for the duration of the lambda, and closes it after completion;
- nested calls to `withConnection`, `R2dbcConnectionFactory#query`, and repository methods inside this lambda use the same current connection.

`withConnection` returns a `Mono<T>`. For results that are naturally a stream of rows, use `withConnectionFlux`, which is the
`Flux`-returning variant with the same connection semantics.
The `inTx` method opens a transaction and is built on top of `withConnection`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final EntityRepository repository;

        public SomeService(EntityRepository repository) {
            this.repository = repository;
        }

        public Mono<List<Entity>> loadAll() {
            return repository.getR2dbcConnectionFactory().withConnection(connection -> {
                // do some work, returns Mono
            });
        }

        public Flux<Entity> streamAll() {
            return repository.getR2dbcConnectionFactory().withConnectionFlux(connection -> {
                // do some work, returns Flux
            });
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(private val repository: EntityRepository) {

        fun loadAll(): Mono<List<Entity>> {
            return repository.r2dbcConnectionFactory.withConnection { connection ->
                // do some work, returns Mono
            }
        }

        fun streamAll(): Flux<Entity> {
            return repository.r2dbcConnectionFactory.withConnectionFlux { connection ->
                // do some work, returns Flux
            }
        }
    }
    ```

## Select by List { #select-by-list }

Sometimes you need to select rows by a list of values.
`Kora` tries to perform mappings at compile time and does not rewrite `SQL` at runtime, so a list parameter requires a custom mapper
that binds the whole collection as a single value.

The example below shows `Postgres` through an array bound with `ANY(:ids)`.
Note that many `R2DBC` drivers (for example `Postgres`) can bind a Java array directly, so such a mapper is often short:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    class ListOfStringR2dbcParameterMapper implements R2dbcParameterColumnMapper<List<String>> {

        @Override
        public void apply(Statement stmt, int index, @Nullable List<String> value) {
            stmt.bind(index, value.toArray(String[]::new));
        }
    }

    @Repository
    public interface EntityRepository extends R2dbcRepository {

        @Query("SELECT id, name FROM entities WHERE id = ANY(:ids)")
        Flux<Entity> findAllByIds(@Mapping(ListOfStringR2dbcParameterMapper.class) List<String> ids);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ListOfStringR2dbcParameterMapper : R2dbcParameterColumnMapper<List<String>> {

        override fun apply(stmt: Statement, index: Int, value: List<String>?) {
            stmt.bind(index, value!!.toTypedArray())
        }
    }

    @Repository
    interface EntityRepository : R2dbcRepository {

        @Query("SELECT id, name FROM entities WHERE id = ANY(:ids)")
        fun findAllByIds(@Mapping(ListOfStringR2dbcParameterMapper::class) ids: List<String>): Flux<Entity>
    }
    ```

## Signatures { #signatures }

Available repository method signatures out of the box.
Because `R2DBC` is natively reactive, no `Executor` component is required for the asynchronous signatures.

===! ":fontawesome-brands-java: `Java`"

    `T` means the return value type, or `List<T>`, or `Void`, or `UpdateCount`.

    - `T myMethod()`
    - `@Nullable T myMethod()`
    - `Optional<T> myMethod()`
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (requires the [dependency](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))
    - `Flux<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (requires the [dependency](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

=== ":simple-kotlin: `Kotlin`"

    `T` means the return value type, or `T?`, or `List<T>`, or `Unit`, or `UpdateCount`.

    - `myMethod(): T`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (requires the [dependency](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) as `implementation`)
    - `myMethod(): Flow<T>` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (requires the [dependency](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) as `implementation`)

## Telemetry { #telemetry }

R2DBC driver uses a common telemetry contract for logging, metrics, and tracing of queries.
Telemetry configuration (section `telemetry { logging / metrics / tracing }`) is described in the [Configuration](#configuration) section.
Extension points are located in `ru.tinkoff.kora.database.common.telemetry`.

For each query, a `DataBaseTelemetry.DataBaseTelemetryContext` is created, which is closed upon query completion.
The executed query is described by `QueryContext(queryId, sql, operation)`, where `queryId` is a stable query identifier
passed to telemetry, `sql` is the final query text, and `operation` defaults to `db_query`.

The default factory `DefaultDataBaseTelemetryFactory` combines three factories:
- `DataBaseLoggerFactory` builds `DataBaseLogger` for logging query start/end;
- `DataBaseMetricWriterFactory` builds `DataBaseMetricWriter` for writing metrics;
- `DataBaseTracerFactory` builds `DataBaseTracer` for distributed tracing.

Metrics and tracing are described in the [Metrics Reference](metrics.md#r2dbc) section.
