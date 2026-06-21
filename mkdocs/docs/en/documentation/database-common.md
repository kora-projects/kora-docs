---
description: "Explains Common Kora database model and repository conventions: entities, identifiers, naming, embedded fields, query macros, batch queries, and repository inheritance. Use when working with @Table, @Column, @Id, @Embedded, @Repository, @Query, @Batch, @Mapping."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Common Kora database model and repository conventions: entities, identifiers, naming, embedded fields, query macros, batch queries, and repository inheritance; key triggers include @Table, @Column, @Id, @Embedded, @Repository, @Query, @Batch, @Mapping, Entity, Repository."
---

Basic principles and mechanisms of database modules in Kora.
This section describes the common model for `JDBC`, `Cassandra`, `R2DBC`, and `Vertx`: entities, repositories, query parameters, batch queries, affected row counts, and macros.
Connection configuration, transactions, supported signatures, and driver-specific mappers are described in the documentation for each database implementation.

This section intentionally does not describe driver-specific details.
For connection configuration, transactions, return value types, database-generated identifiers, service method parameters,
and exact mapper interfaces, see the documentation for the required implementation:
[`JDBC`](database-jdbc.md), [`Cassandra`](database-cassandra.md), [`R2DBC`](database-r2dbc.md), or [`Vertx`](database-vertx.md).

We think that the best way to communicate with a SQL database is to communicate in its native SQL language.
Other tools often have limitations on using specific functions of a particular database,
or a complex program language for building queries that requires additional and considerable time to learn and master,
carries a lot of non-obviousness and potential errors on the part of the developer, and also sometimes has low performance.

For a step-by-step walkthrough before the reference details, see [JDBC Database](../guides/database-jdbc.md) and [Advanced JDBC Database](../guides/database-jdbc-advanced.md).

## Entity { #entity }

An entity is a representation of data from a database in the form of a class with fields.

Entities used as a return value must contain a single public
constructor. This can be either a default constructor or a constructor with parameters.
If Kora finds a constructor with parameters, the entity object will be created based on it.
In the case of an empty constructor, the fields will be filled [via setters](https://docs.oracle.com/cd/E19316-01/819-3669/bnais/index.html).

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record Entity(String id, String name) {}
    ```
=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class Entity(val id: String, val name: String)
    ```

### Table { #table }

You can specify which table the entity belongs to, this will be needed if you use [macros](#macros) when building queries.

If no table is specified, macros will use the class name in [`snake_lower_case`](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/).

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Table("entities")
    public record Entity(String id, String name) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Table("entities")
    data class Entity(val id: String, val name: String)
    ```

### Identifier { #identifier }

Since all data manipulations are performed by converting the entity into a driver query,
there is no need to allocate a special primary key within an entity to work with the entity.

Identifying what exactly is a primary key can be useful when using [macros](#macros),
the `@Id` annotation can be used for this purpose.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record Entity(@Id String id, String name) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class Entity(@field:Id val id: String, val name: String)
    ```

#### Sequential { #sequential }

Let's look at creating an identity as a sequence of numbers using Postgres as an example,
Kora suggests using the database mechanism [identity column](https://www.tutorialsteacher.com/postgresql/identity-column).

An example table for such an entity would look like this:

```sql
CREATE TABLE IF NOT EXISTS entities
(
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    name VARCHAR NOT NULL,
    PRIMARY KEY (id)
);
```

Identifier will be created at the stage of insertion into the database,
and getting it in the application code is supposed to be done using [return identifier value for JDBC or R2DBC](database-jdbc.md#generated-identifier) construct during insertion
or use [special constructs](https://www.postgresql.org/docs/current/dml-returning.html) of your database:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record Entity(Long id, String name) {}

    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("SELECT id, name FROM entities WHERE id = :id")
        @Nullable
        Entity findById(long id);

        @Query("INSERT INTO entities(name) VALUES (:entity.name) RETURNING id")
        long insert(Entity entity);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class Entity(val id: Long, val name: String)

    @Repository
    interface EntityRepository : JdbcRepository {

        @Query("SELECT id, name FROM entities WHERE id = :id")
        fun findById(id: Long): Entity?

        @Query("INSERT INTO entities(name) VALUES (:entity.name) RETURNING id")
        fun insert(entity: Entity): Long
    }
    ```

#### Random { #random }

It is suggested to use the standard `UUID` from Java to create a random identifier:

An example table for such an entity would look like this:

```sql
CREATE TABLE IF NOT EXISTS entities
(
    id UUID NOT NULL,
    name VARCHAR NOT NULL,
    PRIMARY KEY (id)
);
```

The identifier will be created at the stage of object creation in the custom application code:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record Entity(UUID id, 
                         String name) {}

    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("SELECT id, name FROM entities WHERE id = :id")
        @Nullable
        Entity findById(UUID id);

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        void insert(Entity entity);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class Entity(val id: UUID,
                      val name: String)

    @Repository
    interface EntityRepository : JdbcRepository {

        @Query("SELECT id, name FROM entities WHERE id = :id")
        fun findById(id: UUID): Entity?

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        fun insert(entity: Entity)
    }
    ```

#### Composite { #composite }

When a composite key is required, it is intended to use the `@Embedded` annotation to create [embedded fields](#embedded-fields).

### Naming { #naming }

By default, entity field names are translated to [`snake_lower_case`](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/) when retrieving a
result.

If you want to customize the mapping of specific fields from the database to an entity, you can use the `@Column` annotation:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record Entity(@Column("ID") String id, 
                         @Column("NAME") String name) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class Entity(@field:Column("ID") val id: String,
                      @field:Column("NAME") val name: String)
    ```

#### Naming Strategy { #naming-strategy }

If you want to use a naming strategy for the entire entity, it is suggested to create a `NameConverter` implementation and then use it in the `@NamingStrategy` annotation.
It is required that the `NameConverter` implementation has a constructor without parameters.

Either use the available strategies from Kora:

- `NoopNameConverter` - the strategy uses the default field name.
- `SnakeCaseNameConverter` - strategy uses [`snake_lower_case`](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/).
- `SnakeCaseUpperNameConverter` - strategy uses [SNAKE_UPPER_CASE](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/).
- `PascalCaseNameConverter` - the strategy uses [PascalCase](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/).
- `CamelCaseNameConverter` - the strategy uses [camelCase](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/).

===! ":fontawesome-brands-java: `Java`"

    ```java
    @NamingStrategy(NoopNameConverter.class)
    public record Entity(String id, 
                         String name) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @NamingStrategy(NoopNameConverter::class.java)
    data class Entity(val id: String,
                      val name: String)
    ```

### Required fields { #required-fields }

===! ":fontawesome-brands-java: `Java`"

    By default, all fields declared in an entity are considered **required** (*NotNull*).

    ```java
    public record Entity(String id,
                         String name) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    By default, all fields declared in an entity that do not use the [Kotlin Nullability](https://kotlinlang.org/docs/null-safety.html) syntax are considered **required** (*NotNull*).

    ```kotlin
    data class Entity(val id: String,
                      val name: String)
    ```

### Optional fields { #optional-fields }

===! ":fontawesome-brands-java: `Java`"

    If an entity field is optional, meaning it may be absent,
    use the `@Nullable` annotation to mark it explicitly.

    ```java
    public record Entity(String id, 
                         @Nullable String name) {} //(1)!
    ```

    1.  Any `@Nullable` annotation will do, such as `javax.annotation.Nullable` / `jakarta.annotation.Nullable` / `org.jetbrains.annotations.Nullable` / etc.

    It is also possible to specify optional constructor parameters in case the canonical constructor of Record is overridden:

    ```java
    public record Entity(String id,
                         String name) {

        public Entity(String id, 
                      @Nullable String name) { //(1)!
            this.id = id;
            this.name = name;
        }
    }
    ```

    1.  Any `@Nullable` annotation will do, such as `javax.annotation.Nullable` / `jakarta.annotation.Nullable` / `org.jetbrains.annotations.Nullable` / etc.

=== ":simple-kotlin: `Kotlin`"

    It is expected to use the [Kotlin Nullability](https://kotlinlang.org/docs/null-safety.html) syntax and mark such a parameter as Nullable:

    ```kotlin
    data class Entity(val id: String,
                      val name: String?)
    ```

### Embedded fields { #embedded-fields }

In case you want to use nested fields, i.e. convert entity fields into specific classes, you can use the `@Embedded` annotation.

Suppose there is a SQL table where there is a composite key which we want to express as a separate class:

```sql
CREATE TABLE IF NOT EXISTS entities
(
    name    VARCHAR NOT NULL,
    surname VARCHAR NOT NULL,
    info    VARCHAR NOT NULL,
    PRIMARY KEY (name, surname)
)
```

Then the entity will look like this:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record Entity(@Id @Embedded UserID id,
                         @Column("info") String info) {

        public record UserID(String name, String surname) {}
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class Entity(
        @field:Id @field:Embedded val id: UserID,
        @field:Column("info") val info: String
    ) {

        data class UserID(
            val name: String,
            val surname: String
        )
    }
    ```

Then the repository for such an entity would look like this:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("""
                SELECT name, surname, info FROM entities
                WHERE name = :id.name AND surname = :id.surname;
                """)
        @Nullable
        Entity findById(Entity.UserID id);

        @Query("""
            INSERT INTO entities(name, surname, info)
            VALUES (:entity.id.name, :entity.id.surname, :entity.info)
            """)
        void insert(Entity entity);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Query(
            """
            SELECT name, surname, info FROM entities
            WHERE name = :id.name AND surname = :id.surname;
            """
        )
        fun findById(id: Entity.UserID): Entity?

        @Query(
            """
            INSERT INTO entities(name, surname, info)
            VALUES (:entity.id.name, :entity.id.surname, :entity.info)
            """
        )
        fun insert(entity: Entity)
    }
    ```

In case the fields shared a common prefix, it could be specified in the `@Embedded("user_")` annotation:

```sql
CREATE TABLE IF NOT EXISTS entities
(
    user_name       VARCHAR NOT NULL,
    user_surname    VARCHAR NOT NULL,
    info            VARCHAR NOT NULL,
    PRIMARY KEY (user_name, user_surname)
)
```

## Repository { #repository }

Main tool for working with databases in Kora is to use [repository pattern](https://java-design-patterns.com/patterns/repository/#explanation) when designing the database access abstraction.
Repository interface must be annotated with `@Repository`.
Queries for repository methods are described using the `@Query` annotation.
Repository implementation is created at compile time, all `@Query` methods will execute described query and assemble the query arguments and process the result optimally.

`SQL` queries are supposed to be written by the developer because it increases the developer's understanding of the query plan,
gives more insight and context about what the query does and how it will work.
You can use [macros](#macros) to improve the user experience to avoid writing all model fields/columns.

Repository must extend of one of the implementations, in the examples below the [JDBC](database-jdbc.md) implementation will be considered:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository //(1)!
    public interface EntityRepository extends JdbcRepository {

        public record Entity(String id, String name) { }

        //(2)!
        @Query("SELECT id, name FROM entities WHERE id = :id")
        @Nullable
        Entity findById(String id);
    }
    ```

    1. Indicates that the interface is a repository.
    2. Indicates that Kora should create a method implementation that executes the `SQL` query specified in the annotation.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository //(1)!
    interface EntityRepository : JdbcRepository {

        data class Entity(val id: String, val name: String)

        //(2)!
        @Query("SELECT id, name FROM entities WHERE id = :id")
        fun findById(id: String): Entity?
    }
    ```

    1. Indicates that the interface is a repository.
    2. Indicates that Kora should create a method implementation that executes the `SQL` query specified in the annotation.

### Query parameters { #query-parameters }

Repository method parameters are bound to named parameters in `@Query`.
A simple parameter is referenced by the method parameter name: `:id`, `:name`, `:status`.
If a parameter is an entity or a `DTO`, its fields can be referenced with dot notation: `:entity.id`, `:entity.name`, `:filter.status`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("""
            SELECT id, name FROM entities
            WHERE id = :id AND name = :filter.name
            """)
        @Nullable
        Entity findById(String id, Filter filter);

        record Filter(String name) {}
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Query(
            """
            SELECT id, name FROM entities
            WHERE id = :id AND name = :filter.name
            """
        )
        fun findById(id: String, filter: Filter): Entity?

        data class Filter(val name: String)
    }
    ```

If a parameter appears in the query more than once, Kora binds it to every occurrence.
If a method parameter is not used in the query and is not a service parameter of a specific driver, compilation fails.

### Mappers { #mappers }

Use the `@Mapping` annotation when a value needs a non-standard database representation.
It can be placed on an entity field, a method parameter, or a repository method:

- on an entity field, to customize reading or writing a specific column;
- on a method parameter, to customize writing a specific query parameter;
- on a repository method, to customize processing the whole query result or a result row.

An arbitrary mapper cannot be used in every location: its type must match where it is applied.
A parameter mapper is applied to a query parameter, a column mapper to an entity field, and a result or row mapper to a repository method.
The exact set of supported interfaces depends on the driver: for example, `JDBC` uses `JdbcRowMapper`, `JdbcResultSetMapper`, `JdbcResultColumnMapper`, and `JdbcParameterColumnMapper`.
Similar interfaces for `Cassandra`, `R2DBC`, and `Vertx`, as well as their usage details, are described in the documentation for each database implementation.
If a mapper is specified with `@Mapping`, Kora adds it as a dependency of the generated repository and uses it instead of the default mapper.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Table("entities")
    public record Entity(@Id String id,
                         @Mapping(JsonParameterMapper.class)
                         @Column("payload")
                         String payload) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Table("entities")
    data class Entity(
        @field:Id val id: String,
        @field:Mapping(JsonParameterMapper::class)
        @field:Column("payload")
        val payload: String
    )
    ```

### Batch query { #batch-query }

Kora supports batch queries with the `@Batch` annotation.

Unlike executing SQL queries sequentially, batch processing allows you to send an entire set of queries in a single call,
reducing the number of network round trips required and allowing some queries to be executed in parallel on the database side,
which can increase the speed of execution.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        void insert(@Batch List<Entity> entity);
    }
    ```

    **Batch query** can't return arbitrary values, such a method can return `void`, or `UpdateCount`, 
    or database-generated identifiers for [JDBC](database-jdbc.md#generated-identifier) or [R2DBC](database-r2dbc.md#generated-identifier) drivers.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        fun insert(@Batch entity: List<Entity>)
    }
    ```

    **Batch query** can't return arbitrary values, such a method can return `Unit`, or `UpdateCount`, 
    or database-generated identifiers for [JDBC](database-jdbc.md#generated-identifier) or [R2DBC](database-r2dbc.md#generated-identifier) drivers.

`@Batch` is placed on a collection parameter, and each collection element is substituted into the same query one by one.
All other method parameters, if present, are shared by all batch elements.
For example, in `INSERT INTO logs(tenant_id, id, value) VALUES (:tenantId, :entity.id, :entity.value)`,
the `tenantId` parameter is the same for every element, while `entity` fields are taken from each collection element.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Query("INSERT INTO logs(tenant_id, id, value) VALUES (:tenantId, :entity.id, :entity.value)")
    UpdateCount insert(String tenantId, @Batch List<Entity> entity);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Query("INSERT INTO logs(tenant_id, id, value) VALUES (:tenantId, :entity.id, :entity.value)")
    fun insert(tenantId: String, @Batch entity: List<Entity>): UpdateCount
    ```

A method must have no more than one parameter annotated with `@Batch`.
Support for database-generated identifiers in batch queries depends on the specific driver and is described in the corresponding section.

### Affected rows { #affected-rows }

Kora does not process the contents of the query, the result of the method is always derived from the rows returned by the database.
If you want to get the number of affected rows as a result, use the special `UpdateCount` type.
For a regular query, `UpdateCount#value()` contains the row count returned by the driver for the executed query.
For a batch query, the value is usually the sum of results for all batch elements; exact behavior depends on the database driver.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        UpdateCount insert(Entity entity);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        fun insert(entity: Entity): UpdateCount
    }
    ```

### Manual query { #manual-query }

In case there is not enough functionality for some reason with queries in `@Query` annotation or manual control of the connection is required,
you can use the built-in connection factory method to create a method with fully manual control.

You can also use other repository methods within the method and they will also be executed within a single transaction if required.
For more details about transactions, see the documentation for the specific repository implementation.

Repositories can declare regular methods with implementations.
This is useful when a more complex operation should stay close to the queries: for example, executing several `@Query` methods in one transaction,
building a result from several queries, or keeping a database operation sequence inside the repository instead of moving it to a service layer.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        public record Entity(Long id, String name) {}

        @Query("INSERT INTO entities(name) VALUES (:entity.name)")
        UpdateCount insert(Entity entity);

        @Query("UPDATE entities SET name = :name WHERE id = :id")
        UpdateCount updateName(Long id, String name);

        default Entity saveAndRename(Entity entity, String name) {
            return getJdbcConnectionFactory().inTx(() -> {
                insert(entity);
                updateName(entity.id(), name);
                return new Entity(entity.id(), name);
            });
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        data class Entity(val id: Long, val name: String)

        @Query("INSERT INTO entities(name) VALUES (:entity.name)")
        fun insert(entity: Entity): UpdateCount

        @Query("UPDATE entities SET name = :name WHERE id = :id")
        fun updateName(id: Long, name: String): UpdateCount

        fun saveAndRename(entity: Entity, name: String): Entity {
            return jdbcConnectionFactory.inTx<Entity> {
                insert(entity)
                updateName(entity.id, name)
                Entity(entity.id, name)
            }
        }
    }
    ```

### Multiple databases { #multiple-databases }

Sometimes you need to access different databases in different repositories within the same application,
this can be solved in the following way.
You need to create a separate database instance and connect it to a repository,
below is an example for [JDBC](database-jdbc.md) database, but the principle is similar for other types of connections.

It is required to copy the `JdbcDatabase` creation factories and its configuration from the `JdbcDatabaseModule` module
and give them their own tag, which will indicate that they are connections for another database.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends JdbcDatabaseModule {

        final class OtherDatabase { }

        @Tag(OtherDatabase.class)
        default JdbcDatabaseConfig otherJdbcDataBaseConfig(Config config, 
                                                           ConfigValueExtractor<JdbcDatabaseConfig> extractor) {
            var value = config.get("db.other");
            return extractor.extract(value);
        }

        @Tag(OtherDatabase.class)
        default JdbcDatabase otherJdbcDataBase(@Tag(OtherDatabase.class) JdbcDatabaseConfig config,
                                               DataBaseTelemetryFactory telemetryFactory,
                                               @Tag(OtherDatabase.class) @Nullable Executor executor) {
            return new JdbcDatabase(config, telemetryFactory, executor);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : JdbcDatabaseModule {

        class OtherDatabase

        @Tag(OtherDatabase::class)
        fun otherJdbcDataBaseConfig(
            config: Config,
            extractor: ConfigValueExtractor<JdbcDatabaseConfig?>
        ): JdbcDatabaseConfig {
            val value = config.get("db.other")
            return extractor.extract(value) ?: throw ConfigValueExtractionException.missingValue(value)
        }

        @Tag(OtherDatabase::class)
        fun otherJdbcDataBase(
            @Tag(OtherDatabase::class) config: JdbcDatabaseConfig?,
            telemetryFactory: DataBaseTelemetryFactory?,
            @Tag(OtherDatabase::class) executor: Executor?
        ): JdbcDatabase {
            return JdbcDatabase(config, telemetryFactory, executor)
        }
    }
    ```

And repositories that will use this database are now required to specify the tag of this connection:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository(executorTag = @Tag(OtherDatabase.class))
    public interface OtherJdbcRepository extends JdbcRepository {

    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository(executorTag = Tag(value = [OtherDatabase::class]))
    interface OtherJdbcRepository : JdbcRepository {
    
    }
    ```

Repositories with a main database connection, doesn't require tag.

### Macros { #macros }

The most frustrating part of writing SQL queries can be listing and keeping the columns and fields of an entity up to date.

To solve this problem, use special macro constructions inside an `SQL` query in the `@Query` annotation.
These constructions operate on the target [entity](#entity), expand it into specific `SQL` constructions, and make it easier to extend `SQL` queries.
A macro is a helper for writing `SQL` queries and expands into constructions that the user could write manually.

The syntax of the macros looks as follows: `%{return#selects}`.

1. The macros is limited by the syntactic construction `%{` and `}`
2. The target of the macros is specified first, it can be either the name of any method argument or the return value using the `return` keyword
3. Then the `#` character is used to separate the macros target and the macros command
4. The macros command is then specified, which tells which SQL construction to expand the entity into

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Table("entities")
        public record Entity(@Id Long id, 
                             @Column("entity_name") String name, 
                             String code) {}

        @Query("SELECT %{return#selects} FROM %{return#table}") //(1)!
        List<Entity> findAll();
    }
    ```

    1.  Expands into a query:
        ```sql
        SELECT id, entity_name, code FROM entities
        ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Table("entities")
        data class Entity(@field:Id val id: Long, 
                          @field:Column("entity_name") val name: String, 
                          val code: String)

        @Query("SELECT %{return#selects} FROM %{return#table}") //(1)!
        fun findAll(): List<Entity>
    }
    ```

    1.  Expands into a query:
        ```sql
        SELECT id, entity_name, code FROM entities
        ```

#### Commands { #commands }

Available macros commands:

- `table` - expands the entity value from the `@Table` [annotation](#table), or, if it is absent, translates the entity name to [`snake_lower_case`](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/)
- `selects` - creates an entity column enumeration construction for a `SELECT` query
- `inserts` - creates a table, column enumeration construction and corresponding entity fields for an `INSERT` query
- `updates` - creates a column enumeration construction and corresponding entity fields for `UPDATE` query
- `where` - creates a column enumeration construction with a value from the entity for the `WHERE` part of the query

#### Field enumeration { #field-enumeration }

The macros supports additional syntax for enumerating certain fields in a command,
if you suddenly need to do a partial update or data retrieval.
For this purpose, a special construction is used after the command: `%{return#updates=name}`.

Spaces can be placed **only** between fields in the enumeration or special enumeration symbol.

Special enumeration symbols are available:

1. `=` - only the entity fields name specified after the symbol will participate in the command expansion
2. `-=` - all entity fields except those specified after the symbol will participate in command expansion

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Table("entities")
        public record Entity(@Id Long id, 
                             @Column("entity_name") String name, 
                             String code) {}

        @Query("INSERT INTO %{entity#inserts=name,code}") //(1)!
        UpdateCount insert(Entity entity);
    }
    ```

    1.  Expands into a query:
        ```sql
        INSERT INTO entities(entity_name, code) 
        VALUES(:entity.name, :entity.code)
        ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Table("entities")
        data class Entity(@field:Id val id: Long, 
                          @field:Column("entity_name") val name: String, 
                          val code: String)

        @Query("INSERT INTO %{entity#inserts=name,code}") //(1)!
        fun insert(entity: Entity): UpdateCount
    }
    ```

    1.  Expands into a query:
        ```sql
        INSERT INTO entities(entity_name, code) 
        VALUES(:entity.name, :entity.code)
        ```

##### Identifier { #identifier-2 }

When listing fields in a macro, it is possible to use the special keyword `@id`
to refer immediately to the entity identifier annotated with [annotation](#identifier) `@Id`.

This can be especially useful when the identifier is a [compound key](#embedded-fields), to list all columns at once.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Table("entities")
        public record Entity(@Id Long id, 
                             @Column("entity_name") String name, 
                             String code) {}

        @Query("INSERT INTO %{entity#inserts-=@id}") //(1)!
        UpdateCount insert(Entity entity);
    }
    ```

    1.  Expands into a query:
        ```sql
        INSERT INTO entities(entity_name, code) 
        VALUES(:entity.name, :entity.code)
        ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Table("entities")
        data class Entity(@field:Id val id: Long, 
                          @field:Column("entity_name") val name: String, 
                          val code: String)

        @Query("INSERT INTO %{entity#inserts-=@id}") //(1)!
        fun insert(entity: Entity): UpdateCount
    }
    ```

    1.  Expands into a query:
        ```sql
        INSERT INTO entities(entity_name, code) 
        VALUES(:entity.name, :entity.code)
        ```

#### Repository example { #repository-example }

Example of a complete repository with all the basic methods for operating an entity for [Postgres SQL](https://postgrespro.com/docs/postgresql):

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Table("entities")
        record Entity(@Id String id,
                      @Column("value1") int field1,
                      String value2,
                      @Nullable String value3) {}

        @Query("SELECT %{return#selects} FROM %{return#table} WHERE id = :id") //(1)!
        @Nullable
        Entity findById(String id);

        @Query("SELECT %{return#selects} FROM %{return#table}") //(2)!
        List<Entity> findAll();

        @Query("INSERT INTO %{entity#inserts}")  //(3)!
        UpdateCount insert(@Batch List<Entity> entity);

        @Query("UPDATE %{entity#table} SET %{entity#updates} WHERE %{entity#where = @id}")  //(4)!
        UpdateCount update(@Batch List<Entity> entity);

        @Query("INSERT INTO %{entity#inserts} ON CONFLICT (id) DO UPDATE SET %{entity#updates}")  //(5)!
        UpdateCount upsert(@Batch List<Entity> entity);

        @Query("DELETE FROM entities WHERE id = :id")
        UpdateCount deleteById(String id);

        @Query("DELETE FROM entities")
        UpdateCount deleteAll();
    }
    ```

    1.  Expands into a query:
        ```sql
        SELECT id, value1, value2, value3 
        FROM entities 
        WHERE id = :id
        ```
    2.  Expands into a query:
        ```sql
        SELECT id, value1, value2, value3 
        FROM entities
        ```
    3.  Expands into a query:
        ```sql
        INSERT INTO entities(id, value1, value2, value3) 
        VALUES(:entity.id, :entity.field1, :entity.value2, :entity.value3)
        ```
    4.  Expands into a query:
        ```sql
        UPDATE entities
        SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3 
        WHERE id = :entity.id
        ```
    5.  Expands into a query:
        ```sql
        INSERT INTO entities(id, value1, value2, value3) 
        VALUES(:entity.id, :entity.field1, :entity.value2, :entity.value3)
        ON CONFLICT (id) DO UPDATE 
        SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3 
        ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Table("entities")
        data class Entity(
            @field:Id val id: String,
            @field:Column("value1") val field1: Int,
            val value2: String,
            @field:Nullable val value3: String
        )

        @Query("SELECT %{return#selects} FROM %{return#table} WHERE id = :id") //(1)!
        fun findById(id: String?): Entity?

        @Query("SELECT %{return#selects} FROM %{return#table}") //(2)!
        fun findAll(): List<Entity>

        @Query("INSERT INTO %{entity#inserts}") //(3)!
        fun insert(@Batch entity: List<Entity>): UpdateCount

        @Query("UPDATE %{entity#table} SET %{entity#updates} WHERE %{entity#where = @id}") //(4)!
        fun update(@Batch entity: List<Entity>): UpdateCount

        @Query("INSERT INTO %{entity#inserts} ON CONFLICT (id) DO UPDATE SET %{entity#updates}") //(5)!
        fun upsert(@Batch entity: List<Entity>): UpdateCount

        @Query("DELETE FROM entities WHERE id = :id")
        fun deleteById(id: String): UpdateCount

        @Query("DELETE FROM entities")
        fun deleteAll(): UpdateCount
    }
    ```
    1.  Expands into a query:
        ```sql
        SELECT id, value1, value2, value3 
        FROM entities 
        WHERE id = :id
        ```
    2.  Expands into a query:
        ```sql
        SELECT id, value1, value2, value3 
        FROM entities
        ```
    3.  Expands into a query:
        ```sql
        INSERT INTO entities(id, value1, value2, value3) 
        VALUES(:entity.id, :entity.field1, :entity.value2, :entity.value3)
        ```
    4.  Expands into a query:
        ```sql
        UPDATE entities
        SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3 
        WHERE id = :entity.id
        ```
    5.  Expands into a query:
        ```sql
        INSERT INTO entities(id, value1, value2, value3) 
        VALUES(:entity.id, :entity.field1, :entity.value2, :entity.value3)
        ON CONFLICT (id) DO UPDATE 
        SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3 
        ```

#### Composite example { #composite-example }

Example repository with [composite identifier](#composite) and basic methods to operate on an entity,
it is almost identical to the previous one except for the `WHERE` conditions for search and delete for [Postgres SQL](https://postgrespro.com/docs/postgresql):

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Table("entities")
        record Entity(@Id @Embedded  EntityId id,
                      @Column("value1") int field1,
                      String value2,
                      @Nullable String value3) {
            
            public record EntityId(String code, String type) { }
        }

        @Query("SELECT %{return#selects} FROM %{return#table} WHERE %{id#where}") //(1)!
        @Nullable
        Entity findById(EntityId id);

        @Query("SELECT %{return#selects} FROM %{return#table}") //(2)!
        List<Entity> findAll();

        @Query("INSERT INTO %{entity#inserts}")  //(3)!
        UpdateCount insert(@Batch List<Entity> entity);

        @Query("UPDATE %{entity#table} SET %{entity#updates} WHERE %{entity#where = @id}")  //(4)!
        UpdateCount update(@Batch List<Entity> entity);

        @Query("INSERT INTO %{entity#inserts} ON CONFLICT (code, type) DO UPDATE SET %{entity#updates}")  //(5)!
        UpdateCount upsert(@Batch List<Entity> entity);

        @Query("DELETE FROM entities WHERE %{id#where}")
        UpdateCount deleteById(EntityId id);

        @Query("DELETE FROM entities")
        UpdateCount deleteAll();
    }
    ```

    1.  Expands into a query:
        ```sql
        SELECT code, type, value1, value2, value3 
        FROM entities 
        WHERE code = :code AND type = :type
        ```
    2.  Expands into a query:
        ```sql
        SELECT code, type, value1, value2, value3 
        FROM entities
        ```
    3.  Expands into a query:
        ```sql
        INSERT INTO entities(code, type, value1, value2, value3) 
        VALUES(:entity.id.code, :entity.id.type, :entity.field1, :entity.value2, :entity.value3)
        ```
    4.  Expands into a query:
        ```sql
        UPDATE entities
        SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3 
        WHERE code = :entity.id.code AND type = :entity.id.type
        ```
    5.  Expands into a query:
        ```sql
        INSERT INTO entities(code, type, value1, value2, value3) 
        VALUES(:entity.id.code, :entity.id.type, :entity.field1, :entity.value2, :entity.value3)
        ON CONFLICT (code, type) DO UPDATE 
        SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3 
        ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Table("entities")
        data class Entity(
            @field:Id @field:Embedded val id: EntityId,
            @field:Column("value1") val field1: Int,
            val value2: String,
            val value3: String?
        ) {

            data class EntityId(val code: String, val type: String)
        }

        @Query("SELECT %{return#selects} FROM %{return#table} WHERE %{id#where}") //(1)!
        fun findById(id: EntityId): Entity?

        @Query("SELECT %{return#selects} FROM %{return#table}") //(2)!
        fun findAll(): List<Entity>

        @Query("INSERT INTO %{entity#inserts}") //(3)!
        fun insert(@Batch entity: List<Entity>): UpdateCount

        @Query("UPDATE %{entity#table} SET %{entity#updates} WHERE %{entity#where = @id}") //(4)!
        fun update(@Batch entity: List<Entity>): UpdateCount

        @Query("INSERT INTO %{entity#inserts} ON CONFLICT (code, type) DO UPDATE SET %{entity#updates}") //(5)!
        fun upsert(@Batch entity: List<Entity>): UpdateCount

        @Query("DELETE FROM entities WHERE %{id#where}")
        fun deleteById(id: EntityId): UpdateCount

        @Query("DELETE FROM entities")
        fun deleteAll(): UpdateCount
    }
    ```
    1.  Expands into a query:
        ```sql
        SELECT code, type, value1, value2, value3 
        FROM entities 
        WHERE code = :code AND type = :type
        ```
    2.  Expands into a query:
        ```sql
        SELECT code, type, value1, value2, value3 
        FROM entities
        ```
    3.  Expands into a query:
        ```sql
        INSERT INTO entities(code, type, value1, value2, value3) 
        VALUES(:entity.id.code, :entity.id.type, :entity.field1, :entity.value2, :entity.value3)
        ```
    4.  Expands into a query:
        ```sql
        UPDATE entities
        SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3 
        WHERE code = :entity.id.code AND type = :entity.id.type
        ```
    5.  Expands into a query:
        ```sql
        INSERT INTO entities(code, type, value1, value2, value3) 
        VALUES(:entity.id.code, :entity.id.type, :entity.field1, :entity.value2, :entity.value3)
        ON CONFLICT (code, type) DO UPDATE 
        SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3 
        ```

#### Inheritance example { #inheritance-example }

You can also create an abstract CRUD repository and then use it in inheritance for [Postgres SQL](https://postgrespro.com/docs/postgresql):

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface PostgresJdbcCrudRepository<K, V> extends JdbcRepository {

        @Query("SELECT %{return#selects} FROM %{return#table}")
        List<V> findAll();

        @Query("INSERT INTO %{entity#inserts}")
        UpdateCount insert(V entity);

        @Query("INSERT INTO %{entity#inserts}")
        UpdateCount insert(@Batch List<V> entity);

        @Query("UPDATE %{entity#table} SET %{entity#updates} WHERE %{entity#where = @id}")
        UpdateCount update(V entity);

        @Query("UPDATE %{entity#table} SET %{entity#updates} WHERE %{entity#where = @id}")
        UpdateCount update(@Batch List<V> entity);

        @Query("INSERT INTO %{entity#inserts} ON CONFLICT (%{entity#selects = @id}) DO UPDATE SET %{entity#updates}")
        UpdateCount upsert(V entity);

        @Query("INSERT INTO %{entity#inserts} ON CONFLICT (%{entity#selects = @id}) DO UPDATE SET %{entity#updates}")
        UpdateCount upsert(@Batch List<V> entity);

        @Query("DELETE FROM %{entity#table} WHERE %{entity#where = @id}")
        UpdateCount delete(V entity);

        @Query("DELETE FROM %{entity#table} WHERE %{entity#where = @id}")
        UpdateCount delete(@Batch List<V> entity);
    }

    @Repository
    public interface EntityRepository extends PostgresJdbcCrudRepository<String, Entity> {

        @Table("entities")
        record Entity(@Id String id,
                      @Column("value1") int field1,
                      String value2,
                      @Nullable String value3) {
        }

        @Query("DELETE FROM entities WHERE id = :id")
        UpdateCount deleteById(String id);

        @Query("DELETE FROM entities")
        UpdateCount deleteAll();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface PostgresJdbcCrudRepository<K, V> : JdbcRepository {

        @Query("SELECT %{return#selects} FROM %{return#table}")
        fun findAll(): List<V>

        @Query("INSERT INTO %{entity#inserts}")
        fun insert(entity: V): UpdateCount

        @Query("INSERT INTO %{entity#inserts}")
        fun insert(@Batch entity: List<V>): UpdateCount

        @Query("UPDATE %{entity#table} SET %{entity#updates} WHERE %{entity#where = @id}")
        fun update(entity: V): UpdateCount

        @Query("UPDATE %{entity#table} SET %{entity#updates} WHERE %{entity#where = @id}")
        fun update(@Batch entity: List<V>): UpdateCount

        @Query("INSERT INTO %{entity#inserts} ON CONFLICT (%{entity#selects = @id}) DO UPDATE SET %{entity#updates}")
        fun upsert(entity: V): UpdateCount

        @Query("INSERT INTO %{entity#inserts} ON CONFLICT (%{entity#selects = @id}) DO UPDATE SET %{entity#updates}")
        fun upsert(@Batch entity: List<V>): UpdateCount

        @Query("DELETE FROM %{entity#table} WHERE %{entity#where = @id}")
        fun delete(entity: V): UpdateCount

        @Query("DELETE FROM %{entity#table} WHERE %{entity#where = @id}")
        fun delete(@Batch entity: List<V>): UpdateCount
    }

    @Repository
    interface EntityRepository : PostgresJdbcCrudRepository<String, Entity> {

        @Table("entities")
        data class Entity(
            @field:Id val id: String,
            @field:Column("value1") val field1: Int,
            val value2: String,
            @field:Nullable val value3: String
        )

        @Query("DELETE FROM entities WHERE id = :id")
        fun deleteById(id: String): UpdateCount

        @Query("DELETE FROM entities")
        fun deleteAll(): UpdateCount
    }
    ```
