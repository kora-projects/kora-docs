---
description: "Common Kora database model shared by the JDBC and Cassandra modules: entities, identifiers, naming, embedded fields, query parameters, SQL macros, batch queries, affected rows, several databases in one application, and query telemetry. Use when working with @Repository, @Query, @Table, @Column, @Id, @Embedded, @Batch, @Mapping and UpdateCount."
agent:
  use_when: "Use this file for Kora docs or implementation questions about the common database model shared by the JDBC and Cassandra modules: entities and views, @Table, @Column, @Id, @Embedded, naming strategies, @Repository and @Query, query parameter binding, SQL macros (%{return#selects}, %{entity#inserts}, %{entity#where = @id}), @Batch, UpdateCount, several databases in one application, and DatabaseTelemetry."
---

Basic principles and mechanisms of database modules in Kora.
This section describes the common model for `JDBC` and `Cassandra`: entities, repositories, query parameters, batch queries, affected row counts, and macros.
Connection configuration, transactions, supported signatures, and driver-specific mappers are described in the documentation for each database implementation.

This section intentionally does not describe driver-specific details.
For connection configuration, transactions, return value types, database-generated identifiers, service method parameters,
and exact mapper interfaces, see the documentation for the required implementation:
[`JDBC`](database-jdbc.md) or [`Cassandra`](database-cassandra.md).

We think that the best way to communicate with a SQL database is to communicate in its native SQL language.
Other tools often have limitations on using specific functions of a particular database,
or a complex program language for building queries that requires additional and considerable time to learn and master,
carries a lot of non-obviousness and potential errors on the part of the developer, and also sometimes has low performance.

For a step-by-step walkthrough before the reference details, see [JDBC Database](../guides/database-jdbc.md) and [Advanced JDBC Database](../guides/database-jdbc-advanced.md).

## Usage { #usage }

Usage is shown with the [`JDBC`](database-jdbc.md) module: a repository is declared as an interface annotated with `@Repository`
that extends `JdbcRepository`.
Every method annotated with `@Query` carries a plain `SQL` query. Method parameters are bound by name with the
`:parameter` syntax, and entity fields are addressed as `:entity.field`.

Entities are described with the common mapping annotations and are additionally marked with `@EntityJdbc`
(`@EntityCassandra` for `Cassandra`), so that Kora generates the mapper at compile time:

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

    1.  Uses the `%{return#selects}` and `%{return#table}` [macros](#macros). Expands into a query:
        ```sql
        SELECT id, name, description
        FROM entities
        WHERE id = :id
        ```
    2.  Columns are listed by hand without macros — this is allowed, but has to be maintained when the entity changes.
    3.  Uses the `%{entity#inserts}` [macro](#macros). Expands into a query:
        ```sql
        INSERT INTO entities(id, name, description)
        VALUES (:entity.id, :entity.name, :entity.description)
        ```

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

        @Query("SELECT id, name, description FROM entities") //(2)!
        fun findAll(): List<Entity>

        @Query("INSERT INTO %{entity#inserts}") //(3)!
        fun insert(entity: Entity): UpdateCount
    }
    ```

    1.  Uses the `%{return#selects}` and `%{return#table}` [macros](#macros). Expands into a query:
        ```sql
        SELECT id, name, description
        FROM entities
        WHERE id = :id
        ```
    2.  Columns are listed by hand without macros — this is allowed, but has to be maintained when the entity changes.
    3.  Uses the `%{entity#inserts}` [macro](#macros). Expands into a query:
        ```sql
        INSERT INTO entities(id, name, description)
        VALUES (:entity.id, :entity.name, :entity.description)
        ```

`SQL` stays under the developer's control: you can use database-specific capabilities, while Kora takes over only
safe parameter binding, query execution, and result mapping.

A repository can also be declared as an abstract class implementing the driver interface, in which case query methods are
abstract methods of that class; the visibility of a query method is not restricted to `public`.
In Kotlin a query method cannot be `suspend` — the repository generator rejects it at compile time.
The exact set of supported return types is driver-specific and is described on the page of each implementation.

**Parameter binding:** Kora generates typed argument binding for the `SQL` query at compile time.
Query parameters such as `:id` or `:entity.name` are replaced in the generated code with the corresponding driver calls.
For a `String name` parameter, for example, something like `statement.setString(1, name)` is generated, where the index
matches the parameter position in the query.
This gives both safety (no `SQL` injection) and performance (prepared statements are always used).

## View { #view }

A view is a representation of data from a database in the form of a class with fields.

===! ":fontawesome-brands-java: `Java`"

    A view is either a `record`, which is created through its canonical constructor,
    or a `JavaBean` — a class with a public no-argument constructor and a matching `getX()` / `setX()` pair
    for every mapped field, which is created empty and then filled [via setters](https://docs.oracle.com/cd/E19316-01/819-3669/bnais/index.html).

    ```java
    public record Entity(String id, String name) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    A view must be a `data class`, it is created through its primary constructor.

    ```kotlin
    data class Entity(val id: String, val name: String)
    ```

### Table { #table }

You can specify which table the view belongs to, this will be needed if you use [macros](#macros) when building queries.

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

Since all data manipulations are performed by converting the view into a driver query,
there is no need to allocate a special primary key within a view to work with the view.

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

An example table for such a view would look like this:

```sql
CREATE TABLE IF NOT EXISTS entities
(
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    name VARCHAR NOT NULL,
    PRIMARY KEY (id)
);
```

Identifier will be created at the stage of insertion into the database,
and getting it in the application code is supposed to be done using the [generated identifier](database-jdbc.md#generated-identifier) construct during insertion
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

Instead of a driver-specific `RETURNING`, the primary key generated by the database on insertion can be returned
by marking the repository **method** itself with `@Id` (the annotation targets both a view field and a method).
Generated identifiers are supported by the [JDBC](database-jdbc.md#generated-identifier) driver, the exact behavior
and the supported return signatures are described there:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Table("entities")
        public record Entity(@Id Long id, String name) {}

        @Id //(1)!
        @Query("INSERT INTO %{entity#inserts -= @id}") //(2)!
        long insert(Entity entity);
    }
    ```

    1.  Marks the method so that the identifier generated by the database is returned.
    2.  Expands into a query:
        ```sql
        INSERT INTO entities(name) VALUES (:entity.name)
        ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Table("entities")
        data class Entity(@field:Id val id: Long, val name: String)

        @Id //(1)!
        @Query("INSERT INTO %{entity#inserts -= @id}") //(2)!
        fun insert(entity: Entity): Long
    }
    ```

    1.  Marks the method so that the identifier generated by the database is returned.
    2.  Expands into a query:
        ```sql
        INSERT INTO entities(name) VALUES (:entity.name)
        ```

#### Random { #random }

It is suggested to use the standard `UUID` from Java to create a random identifier:

An example table for such a view would look like this:

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

By default, view field names are translated to [`snake_lower_case`](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/) when retrieving a
result.

If you want to customize the mapping of specific fields from the database to a view, you can use the `@Column` annotation:

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

If you want to use a naming strategy for the entire view, it is suggested to create a `NameConverter` implementation and then use it in the `@NamingStrategy` annotation.
It is required that the `NameConverter` implementation has an accessible constructor without parameters.

Either use the available strategies from Kora (`io.koraframework.common.naming`):

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
    @NamingStrategy(NoopNameConverter::class)
    data class Entity(val id: String,
                      val name: String)
    ```

A `@Column` annotation on a field always wins over the naming strategy of the view.

### Required fields { #required-fields }

===! ":fontawesome-brands-java: `Java`"

    By default, all fields declared in a view are considered **required** (*NotNull*).

    ```java
    public record Entity(String id,
                         String name) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    By default, all fields declared in a view that do not use the [Kotlin Nullability](https://kotlinlang.org/docs/null-safety.html) syntax are considered **required** (*NotNull*).

    ```kotlin
    data class Entity(val id: String,
                      val name: String)
    ```

### Optional fields { #optional-fields }

===! ":fontawesome-brands-java: `Java`"

    If a view field is optional, meaning it may be absent,
    use the `@Nullable` annotation to mark it explicitly.

    ```java
    public record Entity(String id,
                         @Nullable String name) {} //(1)!
    ```

    1.  Kora itself uses [JSpecify](https://jspecify.dev/) `org.jspecify.annotations.Nullable`, but any annotation
        whose name ends with `Nullable` will do, such as `jakarta.annotation.Nullable` / `org.jetbrains.annotations.Nullable` / etc.

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

    1.  Kora itself uses [JSpecify](https://jspecify.dev/) `org.jspecify.annotations.Nullable`, but any annotation
        whose name ends with `Nullable` will do, such as `jakarta.annotation.Nullable` / `org.jetbrains.annotations.Nullable` / etc.

=== ":simple-kotlin: `Kotlin`"

    It is expected to use the [Kotlin Nullability](https://kotlinlang.org/docs/null-safety.html) syntax and mark such a parameter as Nullable:

    ```kotlin
    data class Entity(val id: String,
                      val name: String?)
    ```

### Embedded fields { #embedded-fields }

In case you want to use nested fields, i.e. convert view fields into specific classes, you can use the `@Embedded` annotation.

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

Then the view will look like this:

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

Then the repository for such a view would look like this:

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

By default an embedded field adds no prefix to the columns of the nested class.
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

An embedded field can be `@Nullable`: when every column of the nested class is `NULL` in the result row — which is what a
`LEFT JOIN` without a match produces — the whole field is set to `null` instead of being constructed.

An embedded field can also be a `List` of a nested view: rows that share the same values of the outer view columns are
folded into one outer object, and the nested views collected from those rows become its collection field.
This is how a one-to-many `JOIN` is mapped into a single object:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record UserOrdersView(@Embedded("u_") User user,
                                 @Embedded("o_") List<Order> orders) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class UserOrdersView(
        @field:Embedded("u_") val user: User,
        @field:Embedded("o_") val orders: List<Order>
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

Binding is validated in both directions at compile time:

- if a method parameter is not used in the query and is not a service parameter of a specific driver, compilation fails with `Query parameter is unused`;
- if the query contains a placeholder that matches no method parameter, compilation fails with `SQL query placeholder has no matching method parameter` and the list of available parameters;
- if the query contains `:entity.field` for a field the entity does not have, compilation fails with `SQL query placeholder has no matching entity field` and the list of available fields.

Text that only looks like a placeholder is ignored, so `SQL` that legitimately contains a colon still compiles.
Kora skips `:name` occurrences inside single-quoted strings, double-quoted and backquoted identifiers, `[bracketed]` identifiers,
`$$dollar quoted$$` and `$tag$dollar quoted$tag$` blocks, `--` line comments and `/* */` block comments,
and it does not treat the Postgres cast operator `::` as a parameter.

### Query from resource { #query-resource }

A query can be kept in a separate `SQL` file instead of the annotation. If the `@Query` value starts with `classpath:/`,
the rest of the value is a resource path resolved against the source and classpath roots of the module, and the file
content is read at compile time and used as the query.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("classpath:/sql/find-all-entities.sql") //(1)!
        List<Entity> findAll();
    }
    ```

    1.  The file `src/main/resources/sql/find-all-entities.sql` is read at compile time.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Query("classpath:/sql/find-all-entities.sql") //(1)!
        fun findAll(): List<Entity>
    }
    ```

    1.  The file `src/main/resources/sql/find-all-entities.sql` is read at compile time.

The file goes through exactly the same processing as an inline query: [macros](#macros) are expanded and
[parameters](#query-parameters) are bound and validated.
If the resource cannot be read, compilation fails with `SQL query resource wasn't found`.

### Mappers { #mappers }

Use the `@Mapping` annotation when a value needs a non-standard database representation.
It can be placed on a view field, a method parameter, or a repository method:

- on a view field, to customize reading or writing a specific column;
- on a method parameter, to customize writing a specific query parameter;
- on a repository method, to customize processing the whole query result or a result row.

An arbitrary mapper cannot be used in every location: its type must match where it is applied.
A parameter mapper is applied to a query parameter, a column mapper to a view field, and a result or row mapper to a repository method.
The exact set of supported interfaces depends on the driver: for example, `JDBC` uses `JdbcRowMapper`, `JdbcResultSetMapper`, `JdbcResultColumnMapper`, and `JdbcParameterColumnMapper`.
The corresponding `Cassandra` interfaces, as well as their usage details, are described in the documentation for that implementation.
All driver row mappers share the common `RowMapper<T>` (`io.koraframework.database.common.RowMapper`) marker interface, which is the base type behind driver-specific mappers such as `JdbcRowMapper` and `CassandraRowMapper`.
The `@Mapping` annotation itself comes from the core `common` module (`io.koraframework.common.annotation.Mapping`), and every mapper contract implements its `Mapping.MappingFunction` marker.
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

A mapper **with** constructor dependencies has to be a component of the [application graph](container.md).
A mapper **without** dependencies must not be a component: Kora instantiates it itself, and declaring it as a component
leads to a `Multiple components match` graph build error.

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

    **Batch query** can't return arbitrary values, such a method can return `void`, `UpdateCount`, `int[]` or `long[]`,
    or database-generated identifiers when the method is annotated with `@Id` for the [JDBC](database-jdbc.md#generated-identifier) driver.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        fun insert(@Batch entity: List<Entity>)
    }
    ```

    **Batch query** can't return arbitrary values, such a method can return `Unit`, `UpdateCount`, `IntArray` or `LongArray`,
    or database-generated identifiers when the method is annotated with `@Id` for the [JDBC](database-jdbc.md#generated-identifier) driver.

`@Batch` is placed on a `List` parameter, and each list element is substituted into the same query one by one.
Any other collection type is rejected at compile time with `@Batch can be used only with java.util.List<T> parameters`.
All other method parameters, if present, are shared by all batch elements.
For example, in `INSERT INTO logs(tenant_id, id, value) VALUES (:tenantId, :entity.id, :entity.value)`,
the `tenantId` parameter is the same for every element, while `entity` fields are taken from each list element.

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

A method may declare only one `@Batch` parameter.
Support for database-generated identifiers in batch queries depends on the specific driver and is described in the corresponding section.

### Affected rows { #affected-rows }

Kora does not process the contents of the query, the result of the method is always derived from the rows returned by the database.
If you want to get the number of affected rows as a result, use the special `UpdateCount` type — a record with a single `long value()` component.
For a regular query, `UpdateCount#value()` contains the row count returned by the driver for the executed query.
For a batch query on `JDBC` the value is the sum of the counts of all batch elements, and it is `-1` when the driver
reports `SUCCESS_NO_INFO` for at least one element instead of a row count.

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
you can use the executor built into the repository to create a method with fully manual control.

Every driver repository interface exposes its executor with the `executor()` method: `JdbcRepository#executor()` returns
a `JdbcExecutor`, `CassandraRepository#executor()` returns a `CassandraExecutor`.

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
            return executor().inTx(() -> { //(1)!
                insert(entity);
                updateName(entity.id(), name);
                return new Entity(entity.id(), name);
            });
        }
    }
    ```

    1.  `JdbcExecutor#inTx` executes the callback in a transaction, reusing the current one if a transaction is already open.

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
            return executor().inTx(JdbcExecutor.SqlSupplier { //(1)!
                insert(entity)
                updateName(entity.id, name)
                Entity(entity.id, name)
            })
        }
    }
    ```

    1.  `inTx` is heavily overloaded, so Kotlin cannot infer which functional interface a bare lambda implements —
        the SAM constructor `JdbcExecutor.SqlSupplier` (or `JdbcExecutor.SqlRunnable` for a method without a result) must be written explicitly.

When you build `SQL` manually through the driver's executor rather than using a `@Query` method,
the query still flows through Kora telemetry. The executed query is described by a shared
`QueryContext(queryId, sql, operation)`: `queryId` is a stable query identifier reported to telemetry
(a name such as `Repository.method` is convenient), `sql` is the final query text, and `operation` defaults to `db_query`.
The exact executor method and its signature are driver-specific — see [JDBC](database-jdbc.md#query) for a worked example.

### Multiple databases { #multiple-databases }

Sometimes you need to access different databases in different repositories within the same application,
this can be solved in the following way.
Below is an example for a [JDBC](database-jdbc.md) database, but the principle is the same for [Cassandra](database-cassandra.md).

A database connection is provided by a factory module: `JdbcDatabaseModule` declares `new JdbcDatabaseFactoryModule("jdbc")`
as a `@FactoryModule`, and every component such a factory module creates inherits the tag of the factory method.
To add a second database, declare one more `@FactoryModule` method with its own configuration path and its own tag:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends JdbcDatabaseModule {

        final class OtherDatabase { }

        @Tag(OtherDatabase.class) //(1)!
        @FactoryModule //(2)!
        default JdbcDatabaseFactoryModule otherJdbcDatabase() {
            return new JdbcDatabaseFactoryModule("otherDb"); //(3)!
        }
    }
    ```

    1.  Tag that all components created by this factory module receive.
    2.  Tells Kora that the returned object is itself a module and that its methods are component factories.
    3.  Configuration section of the second database.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : JdbcDatabaseModule {

        class OtherDatabase

        @Tag(OtherDatabase::class) //(1)!
        @FactoryModule //(2)!
        fun otherJdbcDatabase(): JdbcDatabaseFactoryModule {
            return JdbcDatabaseFactoryModule("otherDb") //(3)!
        }
    }
    ```

    1.  Tag that all components created by this factory module receive.
    2.  Tells Kora that the returned object is itself a module and that its methods are component factories.
    3.  Configuration section of the second database.

Each connection then reads its own configuration section:

===! ":material-code-json: `Hocon`"

    ```javascript
    jdbc {
        jdbcUrl = "jdbc:postgresql://localhost:5432/main"
        username = "postgres"
        password = "postgres"
        poolName = "main"
    }

    otherDb {
        jdbcUrl = "jdbc:postgresql://localhost:5432/other"
        username = "postgres"
        password = "postgres"
        poolName = "other"
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    jdbc:
      jdbcUrl: "jdbc:postgresql://localhost:5432/main"
      username: "postgres"
      password: "postgres"
      poolName: "main"

    otherDb:
      jdbcUrl: "jdbc:postgresql://localhost:5432/other"
      username: "postgres"
      password: "postgres"
      poolName: "other"
    ```

And repositories that will use this database are now required to specify the tag of this connection:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository(executorTag = OtherDatabase.class)
    public interface OtherJdbcRepository extends JdbcRepository {

    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository(executorTag = OtherDatabase::class)
    interface OtherJdbcRepository : JdbcRepository {

    }
    ```

Repositories with a main database connection, doesn't require tag.

### Macros { #macros }

The most frustrating part of writing SQL queries can be listing and keeping the columns and fields of a view up to date.

To solve this problem, use special macro constructions inside an `SQL` query in the `@Query` annotation.
These constructions operate on the target [view](#view), expand it into specific `SQL` constructions, and make it easier to extend `SQL` queries.
A macro is a helper for writing `SQL` queries and expands into constructions that the user could write manually.

The syntax of the macros looks as follows: `%{return#selects}`.

1. The macros is limited by the syntactic construction `%{` and `}`
2. The target of the macros is specified first, it can be the name of any method argument, the return value using the `return` keyword,
   the name of a type parameter of the repository or of the method, or a nested field of any of those written with a dot: `return.user`
3. Then the `#` character is used to separate the macros target and the macros command
4. The macros command is then specified, which tells which SQL construction to expand the view into

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

The `return` target unwraps the usual result containers, so `List<Entity>`, `Optional<Entity>` and a plain `Entity`
all resolve to the same view.

#### Commands { #commands }

Available macros commands:

- `table` - expands the view value from the `@Table` [annotation](#table), or, if it is absent, translates the view name to [`snake_lower_case`](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/)
- `selects` - creates a view column enumeration construction for a `SELECT` query
- `columns` - creates a bare view column enumeration, without table qualification and without aliases
- `values` - creates the enumeration of query parameters that corresponds to the view fields
- `inserts` - creates a table, column enumeration construction and corresponding view fields for an `INSERT` query
- `updates` - creates a column enumeration construction and corresponding view fields for `UPDATE` query, the [identifier](#identifier) field is always excluded
- `where` - creates a column enumeration construction with a value from the view for the `WHERE` part of the query

`columns` and `values` are the two halves of `inserts`, they are useful when the `INSERT` has to be written by hand:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Query("INSERT INTO %{entity#table}(%{entity#columns -= @id}) VALUES (%{entity#values -= @id})") //(1)!
    UpdateCount insert(Entity entity);
    ```

    1.  Expands into a query:
        ```sql
        INSERT INTO entities(entity_name, code) VALUES (:entity.name, :entity.code)
        ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Query("INSERT INTO %{entity#table}(%{entity#columns -= @id}) VALUES (%{entity#values -= @id})") //(1)!
    fun insert(entity: Entity): UpdateCount
    ```

    1.  Expands into a query:
        ```sql
        INSERT INTO entities(entity_name, code) VALUES (:entity.name, :entity.code)
        ```

#### Field enumeration { #field-enumeration }

The macros supports additional syntax for enumerating certain fields in a command,
if you suddenly need to do a partial update or data retrieval.
For this purpose, a special construction is used after the command: `%{return#updates=name}`.

Spaces can be placed **only** between fields in the enumeration or special enumeration symbol.

Special enumeration symbols are available:

1. `=` - only the view fields name specified after the symbol will participate in the command expansion
2. `-=` - all view fields except those specified after the symbol will participate in command expansion

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
        VALUES (:entity.name, :entity.code)
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
        VALUES (:entity.name, :entity.code)
        ```

##### Identifier { #identifier-2 }

When listing fields in a macro, it is possible to use the special keyword `@id`
to refer immediately to the view identifier annotated with [annotation](#identifier) `@Id`.

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
        VALUES (:entity.name, :entity.code)
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
        VALUES (:entity.name, :entity.code)
        ```

#### Table alias { #table-alias }

The `table` command accepts a table alias with the `table as <alias>` syntax.
Once a target is given an alias, every other macro over the same target qualifies its columns with it:
`selects` produces `alias.column` and, when the view renames the column, adds `AS` with the resulting name,
and `where` produces `alias.column = :path`.

This is what makes macros usable in a `JOIN`, where a nested target and a prefixed [embedded field](#embedded-fields)
map the joined tables into one view:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface UserOrderRepository extends JdbcRepository {

        @Table("users")
        record User(@Id String id, String name) {}

        @Table("orders")
        record Order(@Id String id, @Column("user_id") String userId, String number) {}

        record UserOrderView(@Embedded("u_") User user, @Embedded("o_") Order order) {}

        @Query("""
            SELECT %{return#selects}
            FROM %{return.user#table as u} JOIN %{return.order#table as o} ON o.user_id = u.id
            WHERE u.id = :id
            """) //(1)!
        @Nullable
        UserOrderView find(String id);
    }
    ```

    1.  Expands into a query:
        ```sql
        SELECT u.id AS u_id, u.name AS u_name, o.id AS o_id, o.user_id AS o_user_id, o.number AS o_number
        FROM users u JOIN orders o ON o.user_id = u.id
        WHERE u.id = :id
        ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface UserOrderRepository : JdbcRepository {

        @Table("users")
        data class User(@field:Id val id: String, val name: String)

        @Table("orders")
        data class Order(@field:Id val id: String, @field:Column("user_id") val userId: String, val number: String)

        data class UserOrderView(@field:Embedded("u_") val user: User, @field:Embedded("o_") val order: Order)

        @Query(
            """
            SELECT %{return#selects}
            FROM %{return.user#table as u} JOIN %{return.order#table as o} ON o.user_id = u.id
            WHERE u.id = :id
            """
        ) //(1)!
        fun find(id: String): UserOrderView?
    }
    ```

    1.  Expands into a query:
        ```sql
        SELECT u.id AS u_id, u.name AS u_name, o.id AS o_id, o.user_id AS o_user_id, o.number AS o_number
        FROM users u JOIN orders o ON o.user_id = u.id
        WHERE u.id = :id
        ```

#### Repository example { #repository-example }

Example of a complete repository with all the basic methods for operating a view for [Postgres SQL](https://postgrespro.com/docs/postgresql):

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
        VALUES (:entity.id, :entity.field1, :entity.value2, :entity.value3)
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
        VALUES (:entity.id, :entity.field1, :entity.value2, :entity.value3)
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
            val value3: String?
        )

        @Query("SELECT %{return#selects} FROM %{return#table} WHERE id = :id") //(1)!
        fun findById(id: String): Entity?

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
        VALUES (:entity.id, :entity.field1, :entity.value2, :entity.value3)
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
        VALUES (:entity.id, :entity.field1, :entity.value2, :entity.value3)
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

        @Query("DELETE FROM entities WHERE %{id#where}") //(6)!
        UpdateCount deleteById(EntityId id);

        @Query("DELETE FROM entities")
        UpdateCount deleteAll();
    }
    ```

    1.  Expands into a query:
        ```sql
        SELECT code, type, value1, value2, value3
        FROM entities
        WHERE code = :id.code AND type = :id.type
        ```
    2.  Expands into a query:
        ```sql
        SELECT code, type, value1, value2, value3
        FROM entities
        ```
    3.  Expands into a query:
        ```sql
        INSERT INTO entities(code, type, value1, value2, value3)
        VALUES (:entity.id.code, :entity.id.type, :entity.field1, :entity.value2, :entity.value3)
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
        VALUES (:entity.id.code, :entity.id.type, :entity.field1, :entity.value2, :entity.value3)
        ON CONFLICT (code, type) DO UPDATE
        SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3
        ```
    6.  Expands into a query:
        ```sql
        DELETE FROM entities
        WHERE code = :id.code AND type = :id.type
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

        @Query("DELETE FROM entities WHERE %{id#where}") //(6)!
        fun deleteById(id: EntityId): UpdateCount

        @Query("DELETE FROM entities")
        fun deleteAll(): UpdateCount
    }
    ```

    1.  Expands into a query:
        ```sql
        SELECT code, type, value1, value2, value3
        FROM entities
        WHERE code = :id.code AND type = :id.type
        ```
    2.  Expands into a query:
        ```sql
        SELECT code, type, value1, value2, value3
        FROM entities
        ```
    3.  Expands into a query:
        ```sql
        INSERT INTO entities(code, type, value1, value2, value3)
        VALUES (:entity.id.code, :entity.id.type, :entity.field1, :entity.value2, :entity.value3)
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
        VALUES (:entity.id.code, :entity.id.type, :entity.field1, :entity.value2, :entity.value3)
        ON CONFLICT (code, type) DO UPDATE
        SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3
        ```
    6.  Expands into a query:
        ```sql
        DELETE FROM entities
        WHERE code = :id.code AND type = :id.type
        ```

#### Inheritance example { #inheritance-example }

You can also create an abstract CRUD repository and then use it in inheritance for [Postgres SQL](https://postgrespro.com/docs/postgresql).
Macros resolve type parameters of the parent repository against the type arguments of the concrete repository,
so a generic parent can be written once:

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

        @Query("INSERT INTO %{entity#inserts} ON CONFLICT (%{entity#columns = @id}) DO UPDATE SET %{entity#updates}")
        UpdateCount upsert(V entity);

        @Query("INSERT INTO %{entity#inserts} ON CONFLICT (%{entity#columns = @id}) DO UPDATE SET %{entity#updates}")
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

        @Query("INSERT INTO %{entity#inserts} ON CONFLICT (%{entity#columns = @id}) DO UPDATE SET %{entity#updates}")
        fun upsert(entity: V): UpdateCount

        @Query("INSERT INTO %{entity#inserts} ON CONFLICT (%{entity#columns = @id}) DO UPDATE SET %{entity#updates}")
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
            val value3: String?
        )

        @Query("DELETE FROM entities WHERE id = :id")
        fun deleteById(id: String): UpdateCount

        @Query("DELETE FROM entities")
        fun deleteAll(): UpdateCount
    }
    ```

## Telemetry { #telemetry }

All database drivers share a common telemetry contract for logging, metrics, and tracing of queries.
The concrete configuration knobs (the `telemetry { logging / metrics / tracing }` section) are described in the documentation
for each driver, for example [JDBC](database-jdbc.md#configuration); this section documents only the shared extension points
that live in `io.koraframework.database.common.telemetry`.

Telemetry for a connection pool is built by a `DatabaseTelemetryFactory`:
`DatabaseTelemetry get(DatabaseTelemetryConfig config, String name, String dbType)`,
where `name` is the connection pool name and `dbType` is the database system taken from the connection settings.

For every executed query the driver asks `DatabaseTelemetry#observe(QueryContext)` for a `DatabaseObservation`.
The query being executed is described by `QueryContext(queryId, sql, operation)`, where `queryId` is a stable query
identifier reported to telemetry, `sql` is the final query text, and `operation` defaults to `db_query`.

`DatabaseObservation` extends the shared `Observation` contract and marks the stages of a query:

- `observeConnection()` - a connection has been acquired;
- `observeStatement()` - the statement is ready and execution starts, the query begin is logged here;
- `span()` - the tracing span of the query;
- `observeError(Throwable)` - the query failed;
- `end()` - the query is finished, at this point the metric is recorded and the query end is logged.

The default factory `DefaultDatabaseTelemetryFactory` combines a `Tracer`, a `MeterRegistry` and two optional sub-factories:

- `DefaultDatabaseLoggerFactory` builds a logger that writes query begin and end (`logQueryBegin` / `logQueryEnd`)
  as a structured `sqlQuery` argument containing the pool name, the operation, the query identifier and the processing time;
  the full `sql` text is written only when the logger is enabled at `TRACE` level, and a failed query is logged at `WARN` level;
- `DefaultDatabaseMetricsFactory` builds a metrics writer that records the `db.client.operation.duration` timer for every query.

If logging, [metrics](metrics.md) and [tracing](tracing.md) are all disabled in configuration,
`NoopDatabaseTelemetry` is used and telemetry becomes a no-op.

Besides the standard `logging`, `metrics` and `tracing` sections, the shared `DatabaseTelemetryConfig` adds one database-specific option:

- `telemetry.metrics.driverMetrics` - register the metrics of the driver's own connection pool (default: `true`)

Both sub-factories are optional dependencies of the default telemetry factory, so the simplest way to customize telemetry
is to put your own sub-factory into the [application graph](container.md) — no override annotation is required:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends JdbcDatabaseModule {

        default DefaultDatabaseLoggerFactory databaseLoggerFactory() { //(1)!
            return new DefaultDatabaseLoggerFactory() {

                @Override
                public DefaultDatabaseLogger create(DefaultDatabaseTelemetry.TelemetryContext context) {
                    var logger = LoggerFactory.getLogger("my.database." + context.poolName());
                    return new DefaultDatabaseLogger(logger, context) { //(2)!

                        @Override
                        public void logQueryBegin(QueryContext query) {
                            this.logger.debug("Executing {}", query.queryId());
                        }
                    };
                }
            };
        }
    }
    ```

    1.  The default `DatabaseTelemetryFactory` takes `DefaultDatabaseLoggerFactory` and `DefaultDatabaseMetricsFactory` as optional dependencies and uses them for every connection pool.
    2.  `DefaultDatabaseLogger` is an ordinary class, so only the methods you actually want to change have to be overridden.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : JdbcDatabaseModule {

        fun databaseLoggerFactory(): DefaultDatabaseLoggerFactory { //(1)!
            return object : DefaultDatabaseLoggerFactory() {

                override fun create(context: DefaultDatabaseTelemetry.TelemetryContext): DefaultDatabaseLogger {
                    val logger = LoggerFactory.getLogger("my.database." + context.poolName())
                    return object : DefaultDatabaseLogger(logger, context) { //(2)!

                        override fun logQueryBegin(query: QueryContext) {
                            this.logger.debug("Executing {}", query.queryId())
                        }
                    }
                }
            }
        }
    }
    ```

    1.  The default `DatabaseTelemetryFactory` takes `DefaultDatabaseLoggerFactory` and `DefaultDatabaseMetricsFactory` as optional dependencies and uses them for every connection pool.
    2.  `DefaultDatabaseLogger` is an ordinary class, so only the methods you actually want to change have to be overridden.

`DatabaseModule` provides the default factory as a [default component](container.md#component-override),
so if you need to replace telemetry completely, declare your own `DatabaseTelemetryFactory` in the
[application graph](container.md) and it takes precedence over the one supplied by the module.
