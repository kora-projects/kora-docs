---
description: "Explains Kora Vert.x database repositories, Vert.x SQL client configuration, mapping, transactions, and repository signatures. Use when working with @Repository, @Query, @Table, @Id, @Column, VertxDatabaseModule, VertxConnectionFactory."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora Vert.x database repositories, Vert.x SQL client configuration, mapping, transactions, and repository signatures; key triggers include @Repository, @Query, @Table, @Id, @Column, VertxDatabaseModule, VertxConnectionFactory, VertxRepository."
---

The module provides a repository implementation based on the [Vert.x](https://vertx.io/docs/#databases) reactive SQL client.
The Vert.x connection [pool](https://vertx.io/docs/vertx-pg-client/java/#_using_connection_pool) runs on top of the
[Netty](netty.md) transport. You describe a repository interface and `SQL` queries with `@Repository` and `@Query`, and
`Kora` generates an implementation that binds a Vert.x `Tuple`, runs the prepared query through telemetry, maps the
`RowSet<Row>`, and participates in transactions.

Common rules for entities, `@Repository`, `@Query`, `@Batch`, `UpdateCount`, macros, and other repository
mechanisms are described in [Common database rules](database-common.md).

## Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:database-vertx"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends VertxDatabaseModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:database-vertx")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : VertxDatabaseModule
    ```

You also **must provide** a Vert.x driver implementation as a dependency, of a version no higher than
[4.3.8](https://mvnrepository.com/artifact/io.vertx/vertx-pg-client/4.3.8), for example
[vertx-pg-client](https://mvnrepository.com/artifact/io.vertx/vertx-pg-client/4.3.8) for `PostgreSQL`:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    implementation "io.vertx:vertx-pg-client:4.3.8"
    ```

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    implementation("io.vertx:vertx-pg-client:4.3.8")
    ```

For a [PostgreSQL](https://postgrespro.ru/docs/postgresql) database using `SCRAM` authentication, you also need to add the
[com.ongres.scram:client](https://mvnrepository.com/artifact/com.ongres.scram/client/2.1) dependency.

The [io.projectreactor:reactor-core](https://mvnrepository.com/artifact/io.projectreactor/reactor-core) dependency is
required only if you use `Mono`/`Flux` method signatures.

## Configuration { #configuration }

Example of the complete configuration described by `VertxDatabaseConfig` (example values or default values are shown):

===! ":material-code-json: `HOCON`"

    ```javascript
    db {
        connectionUri = "postgresql://localhost:5432/postgres" //(1)!
        username = "postgres" //(2)!
        password = "postgres" //(3)!
        poolName = "kora" //(4)!
        maxPoolSize = 10 //(5)!
        connectionTimeout = "10s" //(6)!
        acquireTimeout = "10s" //(7)!
        idleTimeout = "10m" //(8)!
        cachePreparedStatements = true //(9)!
        initializationFailTimeout = "10s" //(10)!
        readinessProbe = false //(11)!
        telemetry {
            logging {
                enabled = false //(12)!
            }
            metrics {
                enabled = true //(13)!
                slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(14)!
                tags = { // (15)!
                    "key1" = "value1"
                    "key2" = "value2"
                }
            }
            tracing {
                enabled = true //(16)!
                attributes = { // (17)!
                    "key1" = "value1"
                    "key2" = "value2"
                }
            }
        }
    }
    ```

    1.  Connection [URI](https://vertx.io/docs/vertx-pg-client/java/#_connection_uri) for the database (`required`, default: not specified)
    2.  Username for the connection (`required`, default: not specified)
    3.  User password for the connection (`required`, default: not specified)
    4.  Connection pool name (`required`, default: not specified)
    5.  Maximum connection pool size (default: `10`)
    6.  Maximum time to establish a physical connection (default: `10s`)
    7.  Maximum time to acquire a connection from the pool; if not set, `connectionTimeout` is used instead (default: not specified, optional)
    8.  Maximum idle time for a connection (default: `10m`)
    9.  Whether to cache prepared statements (default: `true`)
    10. Maximum time to wait for a `SELECT 1` connection check at service startup; if not set, no startup check is performed (default: not specified, optional)
    11. Whether to enable the [readiness probe](probes.md#readiness) for the database connection (default: `false`)
    12. Enables module logging (default: `false`)
    13. Enables module metrics (default: `true`)
    14. Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    15. Configures metric tags (default: `{}`)
    16. Enables module tracing (default: `true`)
    17. Configures tracing attributes (default: `{}`)

=== ":simple-yaml: `YAML`"

    ```yaml
    db:
      connectionUri: "postgresql://localhost:5432/postgres" #(1)!
      username: "postgres" #(2)!
      password: "postgres" #(3)!
      poolName: "kora" #(4)!
      maxPoolSize: 10 #(5)!
      connectionTimeout: "10s" #(6)!
      acquireTimeout: "10s" #(7)!
      idleTimeout: "10m" #(8)!
      cachePreparedStatements: true #(9)!
      initializationFailTimeout: "10s" #(10)!
      readinessProbe: false #(11)!
      telemetry:
        logging:
          enabled: false #(12)!
        metrics:
          enabled: true #(13)!
          slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(14)!
          tags: #(15)!
            key1: value1
            key2: value2
        tracing:
          enabled: true #(16)!
          attributes: #(17)!
            key1: value1
            key2: value2
    ```

    1.  Connection [URI](https://vertx.io/docs/vertx-pg-client/java/#_connection_uri) for the database (`required`, default: not specified)
    2.  Username for the connection (`required`, default: not specified)
    3.  User password for the connection (`required`, default: not specified)
    4.  Connection pool name (`required`, default: not specified)
    5.  Maximum connection pool size (default: `10`)
    6.  Maximum time to establish a physical connection (default: `10s`)
    7.  Maximum time to acquire a connection from the pool; if not set, `connectionTimeout` is used instead (default: not specified, optional)
    8.  Maximum idle time for a connection (default: `10m`)
    9.  Whether to cache prepared statements (default: `true`)
    10. Maximum time to wait for a `SELECT 1` connection check at service startup; if not set, no startup check is performed (default: not specified, optional)
    11. Whether to enable the [readiness probe](probes.md#readiness) for the database connection (default: `false`)
    12. Enables module logging (default: `false`)
    13. Enables module metrics (default: `true`)
    14. Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    15. Configures metric tags (default: `{}`)
    16. Enables module tracing (default: `true`)
    17. Configures tracing attributes (default: `{}`)

Because the pool runs on the [Netty](netty.md) transport, you can also configure the [Netty transport](netty.md) separately.

## Usage { #usage }

A Vert.x repository is declared as an interface annotated with `@Repository` that must extend `VertxRepository`.
Each method annotated with `@Query` contains a regular `SQL` query. Method parameters are bound by name with the
`:parameter` syntax, and object fields can be referenced as `:entity.field`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends VertxRepository {

        record Entity(String id, @Column("value1") int field1, String value2, @Nullable String value3) {}

        @Query("SELECT * FROM entities WHERE id = :id")
        Mono<Entity> findById(String id);

        @Query("SELECT * FROM entities")
        Flux<Entity> findAll();

        @Query("""
            INSERT INTO entities(id, value1, value2, value3)
            VALUES (:entity.id, :entity.field1, :entity.value2, :entity.value3)
            """)
        Mono<Void> insert(Entity entity);

        @Query("""
            INSERT INTO entities(id, value1, value2, value3)
            VALUES (:entity.id, :entity.field1, :entity.value2, :entity.value3)
            """)
        Mono<UpdateCount> insertBatch(@Batch List<Entity> entities);

        @Query("""
            UPDATE entities
            SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3
            WHERE id = :entity.id
            """)
        Mono<Void> update(Entity entity);

        @Query("DELETE FROM entities WHERE id = :id")
        Mono<Void> deleteById(String id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : VertxRepository {

        data class Entity(val id: String, @Column("value1") val field1: Int, val value2: String, val value3: String?)

        @Query("SELECT * FROM entities WHERE id = :id")
        fun findById(id: String): Mono<Entity>

        @Query("SELECT * FROM entities")
        fun findAll(): Flux<Entity>

        @Query("""
            INSERT INTO entities(id, value1, value2, value3)
            VALUES (:entity.id, :entity.field1, :entity.value2, :entity.value3)
            """)
        fun insert(entity: Entity): Mono<Void>

        @Query("""
            INSERT INTO entities(id, value1, value2, value3)
            VALUES (:entity.id, :entity.field1, :entity.value2, :entity.value3)
            """)
        fun insertBatch(@Batch entities: List<Entity>): Mono<UpdateCount>

        @Query("""
            UPDATE entities
            SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3
            WHERE id = :entity.id
            """)
        fun update(entity: Entity): Mono<Void>

        @Query("DELETE FROM entities WHERE id = :id")
        fun deleteById(id: String): Mono<Void>
    }
    ```

`SQL` remains under the developer's control: you can use database-specific features, while `Kora` only handles safe
parameter binding, query execution, and result mapping.
Common rules for entities, `@Table`, `@Column`, `@Id`, `@Embedded`, `@Batch`, and macros are described in
[Common database rules](database-common.md).

Reactive `Mono` and `Flux` returns are the native signatures for this module, since the Vert.x client is asynchronous.
Blocking returns such as `Entity`, `List<Entity>`, `void`, and `UpdateCount` are also supported, but they block the calling
thread until the asynchronous result completes, so prefer the reactive signatures when running in a reactive context.

## Mapping { #mapping }

You can override the mapping of different parts of an [entity](database-common.md), a query result, and query parameters.
For this, `Kora` provides several mapper interfaces.

### Result { #result }

Use `VertxRowSetMapper<T>` when you need to control the whole `io.vertx.sqlclient.RowSet<Row>`.
This mapper receives the entire result set and decides how to consume it and what to return:

===! ":fontawesome-brands-java: `Java`"

    ```java
    final class ResultMapper implements VertxRowSetMapper<Map<Integer, List<EntityPart>>> {

        @Override
        public Map<Integer, List<EntityPart>> apply(RowSet<Row> rows) {
            var result = new LinkedHashMap<Integer, List<EntityPart>>(rows.size());
            for (Row row : rows) {
                var entityPart = new EntityPart(row.getString(0), row.getInteger(1));
                var entityParts = result.computeIfAbsent(entityPart.field1(), k -> new ArrayList<>());
                entityParts.add(entityPart);
            }
            return result;
        }
    }

    @Repository
    public interface EntityRepository extends VertxRepository {

        @Mapping(ResultMapper.class)
        @Query("SELECT id, value1 FROM entities")
        Mono<Map<Integer, List<EntityPart>>> findAllParts();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class ResultMapper : VertxRowSetMapper<Map<Int, List<EntityPart>>> {
        override fun apply(rows: RowSet<Row>): Map<Int, List<EntityPart>> {
            val result = LinkedHashMap<Int, MutableList<EntityPart>>(rows.size())
            for (row in rows) {
                val entityPart = EntityPart(row.getString(0), row.getInteger(1))
                result.computeIfAbsent(entityPart.field1) { ArrayList() }.add(entityPart)
            }
            return result
        }
    }

    @Repository
    interface EntityRepository : VertxRepository {

        @Mapping(ResultMapper::class)
        @Query("SELECT id, value1 FROM entities")
        fun findAllParts(): Mono<Map<Int, List<EntityPart>>>
    }
    ```

In most cases you do not need to control the whole `RowSet<Row>`.
It is enough to provide a [VertxRowMapper](#row), and `Kora` automatically adapts it to the method return type using the
built-in `VertxRowSetMapper` helpers: `singleRowSetMapper` (single `T`), `listRowSetMapper` (`List<T>`), and
`optionalRowSetMapper` (`Optional<T>`). There is also `VertxRowSetMapper.extractUpdateCount` used to adapt a result to `UpdateCount`.

### Row { #row }

Use `VertxRowMapper<T>` when you need to manually map one row of the result.
Columns are read from `io.vertx.sqlclient.Row` by type and index (starting from `0`):

===! ":fontawesome-brands-java: `Java`"

    ```java
    final class RowMapper implements VertxRowMapper<EntityPart> {

        @Override
        public EntityPart apply(Row row) {
            return new EntityPart(row.get(String.class, 0), row.get(Integer.class, 1));
        }
    }

    @Repository
    public interface EntityRepository extends VertxRepository {

        @Mapping(RowMapper.class)
        @Query("SELECT id, value1 FROM entities")
        Flux<EntityPart> findAllParts();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class RowMapper : VertxRowMapper<EntityPart> {

        override fun apply(row: Row): EntityPart {
            return EntityPart(row.get(String::class.java, 0), row.get(Integer::class.java, 1))
        }
    }

    @Repository
    interface EntityRepository : VertxRepository {

        @Mapping(RowMapper::class)
        @Query("SELECT id, value1 FROM entities")
        fun findAllParts(): Flux<EntityPart>
    }
    ```

### Column { #column }

Use `VertxResultColumnMapper<T>` when you need to manually map a single column value by its index:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class ColumnMapper implements VertxResultColumnMapper<Entity.FieldType> {

        private static final Entity.FieldType[] ALL = Entity.FieldType.values();

        @Nullable
        @Override
        public Entity.FieldType apply(Row row, int index) {
            var fieldAsInt = row.get(Integer.class, index);
            if (fieldAsInt == null) {
                return null;
            }
            for (var type : ALL) {
                if (type.code() == fieldAsInt) {
                    return type;
                }
            }
            return Entity.FieldType.UNKNOWN;
        }
    }

    @Table("entities")
    public record Entity(String id, @Mapping(ColumnMapper.class) @Column("value1") FieldType field1) {

        enum FieldType {
            UNKNOWN(-10), ONE(1), TWO(2);

            private final int code;

            FieldType(int code) { this.code = code; }

            public int code() { return code; }
        }
    }

    @Repository
    public interface EntityRepository extends VertxRepository {

        @Query("SELECT id, value1 FROM entities")
        Flux<Entity> findAll();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class ColumnMapper : VertxResultColumnMapper<Entity.FieldType> {

        override fun apply(row: Row, index: Int): Entity.FieldType? {
            val fieldAsInt = row.get(Integer::class.java, index) ?: return null
            return Entity.FieldType.entries.firstOrNull { it.code == fieldAsInt } ?: Entity.FieldType.UNKNOWN
        }
    }

    @Table("entities")
    data class Entity(
        val id: String,
        @Mapping(ColumnMapper::class) @Column("value1") val field1: FieldType
    ) {
        enum class FieldType(val code: Int) { UNKNOWN(-10), ONE(1), TWO(2) }
    }

    @Repository
    interface EntityRepository : VertxRepository {

        @Query("SELECT id, value1 FROM entities")
        fun findAll(): Flux<Entity>
    }
    ```

Unlike some other database modules, the column mapper here reads by numeric `index`, not by column label.

### Parameter { #parameter }

Use `VertxParameterColumnMapper<T>` when you need to manually convert a query parameter value.
The mapper returns the raw value that `Kora` binds into the Vert.x `Tuple`; return `null` for a `null` value:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class ParameterMapper implements VertxParameterColumnMapper<Entity.FieldType> {

        @Nullable
        @Override
        public Object apply(@Nullable Entity.FieldType fieldType) {
            return (fieldType == null) ? null : fieldType.code();
        }
    }

    @Repository
    public interface EntityRepository extends VertxRepository {

        @Query("UPDATE entities SET value1 = :fieldType WHERE id = :id")
        UpdateCount updateFieldType(String id, @Mapping(ParameterMapper.class) Entity.FieldType fieldType);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class ParameterMapper : VertxParameterColumnMapper<Entity.FieldType?> {

        override fun apply(fieldType: Entity.FieldType?): Any? {
            return fieldType?.code
        }
    }

    @Repository
    interface EntityRepository : VertxRepository {

        @Query("UPDATE entities SET value1 = :fieldType WHERE id = :id")
        fun updateFieldType(id: String, @Mapping(ParameterMapper::class) fieldType: Entity.FieldType): UpdateCount
    }
    ```

The result column mapper and the parameter mapper can be stacked on the same entity field.
This is convenient for mapping, for example, an enum both when reading a row and when binding a parameter:

===! ":fontawesome-brands-java: `Java`"

    ```java
    record Entity(String id,
                  @Mapping(FieldTypeColumnMapper.class)
                  @Mapping(FieldTypeParameterMapper.class)
                  @Column("value1") FieldType field1) { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class Entity(
        val id: String,
        @Mapping(FieldTypeColumnMapper::class)
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
    * Buffer (`io.vertx.core.buffer.Buffer`)
    * String
    * BigInteger
    * BigDecimal
    * UUID
    * LocalDate
    * LocalDateTime

    For other types, use custom `VertxResultColumnMapper<T>` / `VertxParameterColumnMapper<T>` mappers,
    or a `VertxRowMapper<T>` / `VertxRowSetMapper<T>`.

## Transactions { #transactions }

For grouping queries into a transaction, `Kora` provides the `VertxConnectionFactory` interface
through the `VertxRepository` contract, obtained via `getVertxConnectionFactory()`.
All repository methods called inside the transaction lambda are executed in that same transaction.

Use `inTx` to execute queries transactionally. The lambda receives an `io.vertx.sqlclient.SqlConnection` and must return
a `java.util.concurrent.CompletionStage<T>`, so reactive `Mono` results from repository methods must be converted with
`.toFuture()`. If there is already an active transaction on the current `Context`, a nested `inTx` call reuses the same
connection and does not open a new transaction.

A transactional sequence of operations can stay inside the repository itself as a regular method with an implementation.
This is useful when several `@Query` methods should stay next to the rest of the repository queries,
without moving technical database work to a service layer.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends VertxRepository {

        @Query("INSERT INTO entities(id, value2) VALUES (:entity.id, :entity.value2)")
        Mono<Void> insert(Entity entity);

        @Query("UPDATE entities SET value2 = :value2 WHERE id = :id")
        Mono<UpdateCount> updateValue(String id, String value2);

        default CompletionStage<List<Entity>> saveAll(Entity one, Entity two) {
            return getVertxConnectionFactory().inTx(connection ->
                insert(one) //(1)!
                    .then(updateValue(two.id(), two.value2())) //(2)!
                    .thenReturn(List.of(one, two))
                    .toFuture());
        }
    }
    ```

    1. Executed within the transaction, or rolled back if the whole chain signals an error
    2. Executed within the transaction, or rolled back if the whole chain signals an error

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : VertxRepository {

        @Query("INSERT INTO entities(id, value2) VALUES (:entity.id, :entity.value2)")
        fun insert(entity: Entity): Mono<Void>

        @Query("UPDATE entities SET value2 = :value2 WHERE id = :id")
        fun updateValue(id: String, value2: String): Mono<UpdateCount>

        fun saveAll(one: Entity, two: Entity): CompletionStage<List<Entity>> {
            return vertxConnectionFactory.inTx { _ ->
                insert(one) //(1)!
                    .then(updateValue(two.id, two.value2)) //(2)!
                    .thenReturn(listOf(one, two))
                    .toFuture()
            }
        }
    }
    ```

    1. Executed within the transaction, or rolled back if the whole chain signals an error
    2. Executed within the transaction, or rolled back if the whole chain signals an error

The transaction is committed when the returned `CompletionStage` completes successfully.
If the `CompletionStage` completes exceptionally, the transaction is rolled back and the error is propagated, so all database
changes made within the transaction are not applied.

### Manual Connection Management { #connection }

If a query needs more complex logic or queries outside a repository, you can work with `io.vertx.sqlclient.SqlConnection`
directly. The `withConnection` method executes the lambda with a connection, but does not open a transaction by itself:

- if the current `Context` already contains a connection, the method passes that current connection to the lambda;
- if the current `Context` does not contain a connection, the method takes a new connection from the pool, stores it in the `Context` for the duration of the lambda, and closes it afterwards;
- nested calls to `withConnection` and repository methods inside this lambda use the same current connection.

Both `withConnection` and `inTx` return a `CompletionStage<T>`, and the `inTx` method is built on top of `withConnection`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final EntityRepository repository;

        public SomeService(EntityRepository repository) {
            this.repository = repository;
        }

        public CompletionStage<List<Entity>> loadAll() {
            return repository.getVertxConnectionFactory().withConnection(connection -> {
                // do some work, returns CompletionStage
            });
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(private val repository: EntityRepository) {

        fun loadAll(): CompletionStage<List<Entity>> {
            return repository.vertxConnectionFactory.withConnection { connection ->
                // do some work, returns CompletionStage
            }
        }
    }
    ```

The `VertxConnectionFactory` also exposes lower-level accessors: `currentConnection()` returns the connection bound to the
current `Context` (or `null` if none), `newConnection()` acquires a new `CompletionStage<SqlConnection>` from the pool,
`pool()` returns the underlying `io.vertx.sqlclient.Pool`, and `telemetry()` returns the database telemetry.

## Manual Query With Telemetry { #query }

If a query is hard to express as a single static `@Query`, you can create a regular method with an implementation and build
`SQL` manually. There is no `query` method on the factory; instead, use the `VertxRepositoryHelper` helper to run a query
through Kora telemetry on the current or a new connection.

`VertxRepositoryHelper.completionStage` takes four arguments:

- the `VertxConnectionFactory` (from `getVertxConnectionFactory()`);
- a `QueryContext` with the query identifier and the final `SQL`. The identifier is reported to telemetry, so it is convenient to use a stable name such as `Repository.method`;
- a Vert.x `Tuple` with the bound parameter values;
- a `VertxRowSetMapper<T>` that consumes the `RowSet<Row>` and produces the return value.

If a connection is already bound to the current `Context` (for example inside `inTx` or `withConnection`), the query is
executed on that connection; otherwise a new connection is taken from the pool and closed afterwards.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends VertxRepository {

        default CompletionStage<List<Entity>> findByFilter(@Nullable String name, boolean onlyActive) {
            var sql = new StringBuilder("SELECT id, name FROM entities WHERE 1 = 1");
            var params = new ArrayList<Object>();

            if (name != null) {
                params.add(name);
                sql.append(" AND name = $").append(params.size());
            }
            if (onlyActive) {
                sql.append(" AND active = true");
            }

            var queryContext = new QueryContext("EntityRepository.findByFilter", sql.toString());
            return VertxRepositoryHelper.completionStage(
                getVertxConnectionFactory(),
                queryContext,
                Tuple.from(params),
                rows -> {
                    var result = new ArrayList<Entity>(rows.size());
                    for (var row : rows) {
                        result.add(new Entity(row.getString(0), row.getString(1)));
                    }
                    return result;
                }
            );
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : VertxRepository {

        fun findByFilter(name: String?, onlyActive: Boolean): CompletionStage<List<Entity>> {
            val sql = StringBuilder("SELECT id, name FROM entities WHERE 1 = 1")
            val params = mutableListOf<Any>()

            if (name != null) {
                params += name
                sql.append(" AND name = $").append(params.size)
            }
            if (onlyActive) {
                sql.append(" AND active = true")
            }

            val queryContext = QueryContext("EntityRepository.findByFilter", sql.toString())
            return VertxRepositoryHelper.completionStage(
                vertxConnectionFactory,
                queryContext,
                Tuple.from(params)
            ) { rows ->
                rows.map { row -> Entity(row.getString(0), row.getString(1)) }
            }
        }
    }
    ```

If you prefer reactive return types, use `VertxRepositoryHelper.Reactor.mono` (returns `Mono<T>` with a `VertxRowSetMapper`)
or `VertxRepositoryHelper.Reactor.flux` (returns `Flux<T>` with a `VertxRowMapper`) instead. This is an advanced path; for
static queries prefer plain `@Query` methods.

## Select by List { #select-by-list }

Sometimes you need to select rows by a list of values.
`Kora` performs mappings at compile time and does not rewrite `SQL` at runtime, so a list parameter requires a custom mapper
that binds the whole collection as a single value.

The example below shows `Postgres` through an array bound with `ANY(:ids)`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class ListOfStringParameterMapper implements VertxParameterColumnMapper<List<String>> {

        @Override
        public Object apply(@Nullable List<String> value) {
            return value == null ? null : value.toArray(String[]::new);
        }
    }

    @Repository
    public interface EntityRepository extends VertxRepository {

        @Query("SELECT id, name FROM entities WHERE id = ANY(:ids)")
        Flux<Entity> findAllByIds(@Mapping(ListOfStringParameterMapper.class) List<String> ids);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class ListOfStringParameterMapper : VertxParameterColumnMapper<List<String>?> {

        override fun apply(value: List<String>?): Any? {
            return value?.toTypedArray()
        }
    }

    @Repository
    interface EntityRepository : VertxRepository {

        @Query("SELECT id, name FROM entities WHERE id = ANY(:ids)")
        fun findAllByIds(@Mapping(ListOfStringParameterMapper::class) ids: List<String>): Flux<Entity>
    }
    ```

## Signatures { #signatures }

Available repository method signatures out of the box.
Because the Vert.x client is natively asynchronous, no `Executor` component is required for the asynchronous signatures.

===! ":fontawesome-brands-java: `Java`"

    `T` means the return value type, or `List<T>`, or `Void`, or `UpdateCount`.

    - `T myMethod()`
    - `@Nullable T myMethod()`
    - `Optional<T> myMethod()`
    - `CompletionStage<T> myMethod()`
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (requires the [dependency](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))
    - `Flux<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (requires the [dependency](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

=== ":simple-kotlin: `Kotlin`"

    `T` means the return value type, or `T?`, or `List<T>`, or `Unit`, or `UpdateCount`.

    - `myMethod(): T`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (requires the [dependency](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) as `implementation`)
    - `myMethod(): Flow<T>` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (requires the [dependency](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) as `implementation`)
