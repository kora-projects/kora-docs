Basic principles and mechanisms of database modules in Kora.

We adhere to the concept that the best way to write queries for SQL databases is to use the SQL language.
Other tools often have limitations on using specific functions of a particular database,
or a complex program language for building queries that requires a separate understanding.

## Entity

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

### Table

You can specify which table the entity belongs to, this will be needed if you use [macros](#macros) when building queries.

If no table is specified, macros will use the class name in [snake_lower_case](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/).

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

### Identifier

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

#### Sequential

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

The identifier will be created at the stage of insertion into the database,
and it is supposed to be received in the application code with the help of `RETURNING` construction at insertion:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record Entity(Long id, String name) {}

    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("SELECT * FROM entities WHERE id = :id")
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

        @Query("SELECT * FROM entities WHERE id = :id")
        fun findById(id: Long): Entity?

        @Query("INSERT INTO entities(name) VALUES (:entity.name) RETURNING id")
        fun insert(entity: Entity): Long
    }
    ```

#### Random

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

        @Query("SELECT * FROM entities WHERE id = :id")
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

        @Query("SELECT * FROM entities WHERE id = :id")
        fun findById(id: UUID): Entity?

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        fun insert(entity: Entity)
    }
    ```

#### Composite

When a composite key is required, it is intended to use the `@Embedded` annotation to create [embedded fields](#embedded-fields).

### Naming

By default, entity field names are translated to [snake_lower_case](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/) when retrieving a
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

#### Naming Strategy

If you want to use a naming strategy for the entire entity, it is suggested to create a `NameConverter` implementation and then use it in the `@NamingStrategy` annotation.
It is required that the `NameConverter` implementation has a constructor without parameters.

Either use the available strategies from Kora:

- `NoopNameConverter` - the strategy uses the default field name.
- `SnakeCaseNameConverter` - strategy uses [snake_lower_case](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/).
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

### Required fields

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

### Optional fields

===! ":fontawesome-brands-java: `Java`"

    In case a field in an entity is optional, that is, it may not exist then,
    you can use the `@Nullable` annotation to match the field in Json and DTO.

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

### Embedded fields

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
        @field:Column("name") val info: String
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
                SELECT * FROM entities
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
            SELECT * FROM entities
            WHERE name = :id.name AND surname = :id.surname;
            """
        )
        fun findById(id: Entity.CompositeID): Entity?

        @Query(
            """
            INSERT INTO entities(name, surname, name)
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

## Repository

Main tool for working with databases in Kora is to use [repository pattern](https://java-design-patterns.com/patterns/repository/#explanation) when designing the database access abstraction.
Repository interface must be annotated with `@Repository`.
Queries for repository methods are described using the `@Query` annotation.
Repository implementation is created at compile time, all `@Query` methods will execute described query and assemble the query arguments and process the result optimally.

SQL queries are supposed to be written by the developer because it increases the developer's understanding of the query plan,
gives more insight and context to the developer about what he is doing and how his query will work.
You can use [macros](#macros) to improve the user experience to avoid writing all model fields/columns.

Repository must extend of one of the implementations, in the examples below the [JDBC](database-jdbc.md) implementation will be considered:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository //(1)!
    public interface EntityRepository extends JdbcRepository {

        public record Entity(String id, String name) { }

        //(2)!
        @Query("SELECT * FROM entities WHERE id = :id")
        @Nullable
        Entity findById(String id);
    }
    ```

    1. Indicates that the interface is a repository.
    2. Indicates that it is necessary to create a method implementation that executes the SQL query specified in the annotation.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository //(1)!
    interface EntityRepository : JdbcRepository {

        data class Entity(val id: String, val name: String)

        //(2)!
        @Query("SELECT * FROM entities WHERE id = :id")
        fun findById(id: String): Entity?
    }
    ```

    1. Indicates that the interface is a repository.
    2. Indicates that it is necessary to create a method implementation that executes the SQL query specified in the annotation.

### Batch query

Kora supports batch queries with the `@Batch` annotation.

Unlike executing SQL queries sequentially, batch processing allows you to send an entire set of queries in a single call,
reducing the number of network connections required and allowing some queries to be executed in parallel on the database side,
which can increase the speed of execution.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        void insert(@Batch List<Entity> entity);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        fun insert(@Batch entity: List<Entity>)
    }
    ```

### Affected rows

Kora does not process the contents of the query, the result of the method is always derived from the rows returned by the database.
If you want to get the number of updated rows as a result, you should use a special type `UpdateCount`.

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

### Manual query

In case there is not enough functionality for some reason with queries in `@Query` annotation or manual control of the connection is required,
you can use the built-in connection factory method to create a method with fully manual control.

You can also use other repository methods within the method and they will also be executed within a single transaction if required.
For more details about transactions, see the documentation for the specific repository implementation.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        public record Entity(Long id, String name) {}

        default int insert(Entity entity) {
            return getJdbcConnectionFactory().inTx(connection -> {
                String sql = "INSERT INTO entities(name) VALUES (?) RETURNING id";
                try(PreparedStatement preparedStatement = connection.prepareStatement(sql)) {
                    preparedStatement.setString(1, entity.name());
                    try(ResultSet resultSet = preparedStatement.executeQuery()) {
                        return resultSet.getInt(1);
                    }
                }
            });
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        data class Entity(val id: Long, val name: String)

        fun insert(entity: Entity): Int {
            return jdbcConnectionFactory.inTx<Int> { connection ->
                val sql = "INSERT INTO entities(name) VALUES (?) RETURNING id"
                connection.prepareStatement(sql).use { preparedStatement ->
                    preparedStatement.setString(1, entity.name)
                    preparedStatement.executeQuery().use { resultSet -> resultSet.getInt(1) }
                }
            }
        }
    }
    ```

### Macros

The most frustrating part of writing SQL queries can be listing and keeping the columns and fields of an entity up to date.

In order to solve this problem you can use special macros constructions within the SQL query within the `@Query` annotation.
These constructions allow you to operate target [entity](#entity) and expand it into specific SQL constructions  and easily augment into SQL queries.
Macros is an assistant when writing SQL queries, expands into constructions that the user could write with his own hands.

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

#### Commands

Available macros commands:

- `table` - construction exposes the entity value in [annotation](#table) `@Table` or if none is available, translates the entity name to [snake_lower_case](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/)
- `selects` - creates an entity column enumeration construction for a `SELECT` query
- `inserts` - creates a table, column enumeration construction and corresponding entity fields for an `INSERT` query
- `updates` - creates a column enumeration construction and corresponding entity fields for `UPDATE` query
- `where` - creates a column enumeration construction with a value from the entity for the `WHERE` part of the query

#### Field enumeration

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

##### Identifier

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

#### Repository example

An example of a complete repository with all the basic methods for operating an entity.

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
        VALUES(:entity.id, :entity.value1, :entity.value2, :entity.value3)
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
        VALUES(:entity.id, :entity.value1, :entity.value2, :entity.value3)
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
        VALUES(:entity.id, :entity.value1, :entity.value2, :entity.value3)
        ON CONFLICT (id) DO UPDATE 
        SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3 
        ```

##### Composite example

Example repository with [composite identifier](#composite) and basic methods to operate on an entity,
it is almost identical to the previous one except for the `WHERE` conditions for search and delete.

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

    1.  Раскрывается в запрос:
        ```sql
        SELECT code, type, value1, value2, value3 
        FROM entities 
        WHERE code = :code AND type = :type
        ```
    2.  Раскрывается в запрос:
        ```sql
        SELECT code, type, value1, value2, value3 
        FROM entities
        ```
    3.  Раскрывается в запрос:
        ```sql
        INSERT INTO entities(code, type, value1, value2, value3) 
        VALUES(:entity.code, :entity.type, :entity.value1, :entity.value2, :entity.value3)
        ```
    4.  Раскрывается в запрос:
        ```sql
        UPDATE entities
        SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3 
        WHERE code = :entity.id.code AND type = :entity.id.type
        ```
    5.  Раскрывается в запрос:
        ```sql
        INSERT INTO entities(code, type, value1, value2, value3) 
        VALUES(:entity.code, :entity.type, :entity.value1, :entity.value2, :entity.value3)
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

    1.  Раскрывается в запрос:
        ```sql
        SELECT code, type, value1, value2, value3 
        FROM entities 
        WHERE code = :code AND type = :type
        ```
    2.  Раскрывается в запрос:
        ```sql
        SELECT code, type, value1, value2, value3 
        FROM entities
        ```
    3.  Раскрывается в запрос:
        ```sql
        INSERT INTO entities(code, type, value1, value2, value3) 
        VALUES(:entity.code, :entity.type, :entity.value1, :entity.value2, :entity.value3)
        ```
    4.  Раскрывается в запрос:
        ```sql
        UPDATE entities
        SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3 
        WHERE code = :entity.id.code AND type = :entity.id.type
        ```
    5.  Раскрывается в запрос:
        ```sql
        INSERT INTO entities(code, type, value1, value2, value3) 
        VALUES(:entity.code, :entity.type, :entity.value1, :entity.value2, :entity.value3)
        ON CONFLICT (code, type) DO UPDATE 
        SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3 
        ```

##### Inheritance example

You can also create an abstract CRUD repository and then use it in inheritance:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface JdbcCrudRepository<K, V> extends JdbcRepository {

        @Query("SELECT %{return#selects} FROM %{return#table} WHERE %{id#where}")
        Optional<V> findById(K id);

        @Query("SELECT %{return#selects} FROM %{return#table}")
        List<V> findAll();

        @Query("INSERT INTO %{entity#inserts}")
        UpdateCount insert(V entity);

        @Query("INSERT INTO %{entity#inserts}")
        UpdateCount insertBatch(@Batch List<V> entity);

        @Query("UPDATE %{entity#table} SET %{entity#updates} WHERE %{entity#where = @id}")
        UpdateCount update(V entity);

        @Query("UPDATE %{entity#table} SET %{entity#updates} WHERE %{entity#where = @id}")
        UpdateCount updateBatch(@Batch List<V> entity);

        @Query("INSERT INTO %{entity#inserts} ON CONFLICT (a, b) DO UPDATE SET %{entity#updates}")
        UpdateCount upsert(V entity);

        @Query("INSERT INTO %{entity#inserts} ON CONFLICT (a, b) DO UPDATE SET %{entity#updates}")
        UpdateCount upsertBatch(@Batch List<V> entity);

        @Query("DELETE FROM %{entity#table} WHERE %{entity#where = @id}")
        UpdateCount delete(V entity);

        @Query("DELETE FROM %{entity#table} WHERE %{entity#where = @id}")
        UpdateCount deleteBatch(@Batch List<V> entity);
    }

    @Repository
    public interface EntityRepository extends JdbcCrudRepository<String, Entity> {

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
    interface JdbcCrudRepository<K, V> : JdbcRepository {

        @Query("SELECT %{return#selects} FROM %{return#table} WHERE %{id#where}")
        fun findById(id: K): V?

        @Query("SELECT %{return#selects} FROM %{return#table}")
        fun findAll(): List<V>

        @Query("INSERT INTO %{entity#inserts}")
        fun insert(entity: V): UpdateCount

        @Query("INSERT INTO %{entity#inserts}")
        fun insertBatch(@Batch entity: List<V>): UpdateCount

        @Query("UPDATE %{entity#table} SET %{entity#updates} WHERE %{entity#where = @id}")
        fun update(entity: V): UpdateCount

        @Query("UPDATE %{entity#table} SET %{entity#updates} WHERE %{entity#where = @id}")
        fun updateBatch(@Batch entity: List<V>): UpdateCount

        @Query("INSERT INTO %{entity#inserts} ON CONFLICT (a, b) DO UPDATE SET %{entity#updates}")
        fun upsert(entity: V): UpdateCount

        @Query("INSERT INTO %{entity#inserts} ON CONFLICT (a, b) DO UPDATE SET %{entity#updates}")
        fun upsertBatch(@Batch entity: List<V>): UpdateCount

        @Query("DELETE FROM %{entity#table} WHERE %{entity#where = @id}")
        fun delete(entity: V): UpdateCount

        @Query("DELETE FROM %{entity#table} WHERE %{entity#where = @id}")
        fun deleteBatch(@Batch entity: List<V>): UpdateCount
    }

    @Repository
    interface EntityRepository : JdbcCrudRepository<String, Entity> {

        @Table("entities")
        data class Entity(
            @field:Id val id: String,
            @field:Column("value1") val field1: Int,
            val value2: String,
            @field:Nullable val value3: String
        )

        @Query("DELETE FROM entities WHERE id = :id")
        fun deleteById(id: String?): UpdateCount

        @Query("DELETE FROM entities")
        fun deleteAll(): UpdateCount
    }
    ```
