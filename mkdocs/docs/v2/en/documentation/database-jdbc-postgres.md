---
seo_title: "Kora JDBC PostgreSQL: Arrays, Intervals, Ranges and JSON"
seo_description: "Reference for the Kora database-jdbc-postgres module: setup, PostgreSQL arrays and collections, intervals, ranges, and JSON / JSONB column mappers."
keywords: ["Kora Framework", "Kora JDBC", "PostgreSQL", "database-jdbc-postgres", "PostgreSQL arrays", "PostgreSQL range types", "PostgreSQL JSONB"]
description: "Explains the Kora PostgreSQL JDBC module, its dependencies and column mappers for arrays, collections, intervals, ranges and JSON / JSONB. Use when working with PostgresJdbcDatabaseModule, @Pg, @PgJson, @PgJsonb and PgRange."
agent:
  use_when: "Use this file for PostgreSQL-specific JDBC column mappers; key triggers include database-jdbc-postgres, PostgresJdbcDatabaseModule, PgCollectionJdbcMappersModule, PgArrayJdbcMappersModule, PgIntervalJdbcMappersModule, PgRangeJdbcMappersModule, PgJsonJdbcMappersModule, @Pg, @PgJson, @PgJsonb, PgRange, JsonNullable, interval, int4range, tstzrange."
---

The `database-jdbc-postgres` module adds column mappers for `PostgreSQL`-specific representations:
arrays, `interval`, range types, and `json` / `jsonb`.
Repositories, entities, and the `jdbc` configuration section follow the [JDBC documentation](database-jdbc.md);
the module only contributes mappers to the [application graph](container.md).

## Dependency { #postgres-dependency }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:database-jdbc-postgres"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends PostgresJdbcDatabaseModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:database-jdbc-postgres")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : PostgresJdbcDatabaseModule
    ```

`PostgresJdbcDatabaseModule` extends `JdbcDatabaseModule`, so it replaces it in the application rather than being added next to it.
The module brings the `PostgreSQL` driver `org.postgresql:postgresql` as a transitive dependency.

`PostgresJdbcDatabaseModule` combines five mapper modules from `io.koraframework.database.jdbc.postgres.mapper`:
`PgCollectionJdbcMappersModule`, `PgArrayJdbcMappersModule`, `PgIntervalJdbcMappersModule`, `PgRangeJdbcMappersModule`, and `PgJsonJdbcMappersModule`.
When only some of the mappers are needed, extend `JdbcDatabaseModule` together with the modules you want:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends JdbcDatabaseModule, PgRangeJdbcMappersModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : JdbcDatabaseModule, PgRangeJdbcMappersModule
    ```

Mappers for regular `JDK` types are registered with a tag, so they never change how a field is mapped implicitly:
mappers for collections, arrays, `Duration`, and `Period` are tagged with `@Pg`,
and `JSON` mappers with `@PgJson` or `@PgJsonb` (all from `io.koraframework.database.jdbc.postgres.annotation`).
Put the annotation on an entity field or on a repository method parameter to select the `PostgreSQL` mapper.
`PgRange` mappers need no tag because `PgRange` is `PostgreSQL`-specific by itself.
Every mapper is declared as a [`@DefaultComponent`](container.md#default-factory), so your own mapper of the same type and tag replaces it.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @EntityJdbc
    @Table("users")
    public record User(@Id long id,
                       @Pg List<String> roles, //(1)!
                       @Pg Duration sessionTtl, //(2)!
                       PgRange<LocalDate> validity, //(3)!
                       @PgJsonb Settings settings) { //(4)!

        @Json
        public record Settings(String theme, boolean notifications) { }
    }

    @Repository
    public interface UserRepository extends JdbcRepository {

        @Query("SELECT %{return#selects} FROM %{return#table} WHERE id = ANY(:ids)")
        List<User> findAllByIds(@Pg List<Long> ids); //(5)!

        @Query("INSERT INTO %{entity#inserts}")
        UpdateCount insert(User entity);
    }
    ```

    1.  Column of type `varchar[]`
    2.  Column of type `interval`
    3.  Column of type `daterange`, no tag required
    4.  Column of type `jsonb`, `Settings` is written and read by the `JsonWriter` / `JsonReader` generated for the `@Json` type
    5.  The list is bound as a single `int8[]` parameter, so `= ANY(:ids)` needs no hand-written mapper

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @EntityJdbc
    @Table("users")
    data class User(
        @field:Id val id: Long,
        @Pg val roles: List<String>, //(1)!
        @Pg val sessionTtl: Duration, //(2)!
        val validity: PgRange<LocalDate>, //(3)!
        @PgJsonb val settings: Settings //(4)!
    ) {

        @Json
        data class Settings(val theme: String, val notifications: Boolean)
    }

    @Repository
    interface UserRepository : JdbcRepository {

        @Query("SELECT %{return#selects} FROM %{return#table} WHERE id = ANY(:ids)")
        fun findAllByIds(@Pg ids: List<Long>): List<User> //(5)!

        @Query("INSERT INTO %{entity#inserts}")
        fun insert(entity: User): UpdateCount
    }
    ```

    1.  Column of type `varchar[]`
    2.  Column of type `interval`
    3.  Column of type `daterange`, no tag required
    4.  Column of type `jsonb`, `Settings` is written and read by the `JsonWriter` / `JsonReader` generated for the `@Json` type
    5.  The list is bound as a single `int8[]` parameter, so `= ANY(:ids)` needs no hand-written mapper

## Arrays and collections { #postgres-arrays }

With `@Pg`, collections and arrays are bound as a `PostgreSQL` array and read back from one:

| Element type | `PostgreSQL` array element |
|---|---|
| `Boolean` | `bool` |
| `Short` | `int2` |
| `Integer` | `int4` |
| `Long` | `int8` |
| `Float` | `float4` |
| `Double` | `float8` |
| `BigDecimal` | `numeric` |
| `String` | `varchar` |
| `UUID` | `uuid` |

- A parameter can be a `List<T>`, `Set<T>`, or `Collection<T>`, so a collection does not have to be copied just to make the call.
  A result is always a `List<T>`; uniqueness is expressed by the query, for example with `DISTINCT`.
- Arrays are supported as `T[]` for every element type above (`Array<T>` in `Kotlin`) and as primitive arrays
  `boolean[]`, `short[]`, `int[]`, `long[]`, `float[]`, `double[]` (`BooleanArray`, `ShortArray`, `IntArray`, `LongArray`, `FloatArray`, `DoubleArray` in `Kotlin`).
- `NULL` elements are passed through as is for collections and object arrays.
  A primitive array cannot hold `NULL`, so reading an array with a `NULL` element into it fails with `SQLException`.
- A `NULL` column is read as `null`, and a `null` value is bound as `NULL`.

## Intervals { #postgres-interval }

With `@Pg`, `java.time.Duration` and `java.time.Period` are bound to and read from an `interval` column.
`Duration` is written as days, hours, minutes, and seconds with a fractional part, and `Period` as years, months, and days.
Months and years have no fixed length, so reading an `interval` that has years or months into a `Duration` fails with `SQLException`;
use `Period` for such values.
In the same way, reading an `interval` with a time part into a `Period` fails; use `Duration` for it.

## Ranges { #postgres-range }

`PgRange<T>` from `io.koraframework.database.jdbc.postgres` represents a range type value and needs no tag:

| `Java` type | `PostgreSQL` type |
|---|---|
| `PgRange<Integer>` | `int4range` |
| `PgRange<Long>` | `int8range` |
| `PgRange<BigDecimal>` | `numrange` |
| `PgRange<LocalDate>` | `daterange` |
| `PgRange<LocalDateTime>` | `tsrange` |
| `PgRange<OffsetDateTime>` | `tstzrange` |

`PgRange` is a record of `lower`, `upper`, `lowerInclusive`, `upperInclusive`, and `isEmpty`; a `null` bound means the range is unbounded on that side.
Factory methods cover the usual shapes: `closed` `[a,b]`, `closedOpen` `[a,b)`, `openClosed` `(a,b]`, `open` `(a,b)`, and `empty()`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface UserRepository extends JdbcRepository {

        @Query("SELECT %{return#selects} FROM %{return#table} WHERE validity && :period")
        List<User> findValidWithin(PgRange<LocalDate> period);
    }

    var users = repository.findValidWithin(PgRange.closedOpen(LocalDate.of(2026, 1, 1), null)); //(1)!
    ```

    1.  `[2026-01-01,)`: from January 1, 2026 with no upper bound

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface UserRepository : JdbcRepository {

        @Query("SELECT %{return#selects} FROM %{return#table} WHERE validity && :period")
        fun findValidWithin(period: PgRange<LocalDate>): List<User>
    }

    val users = repository.findValidWithin(PgRange.closedOpen(LocalDate.of(2026, 1, 1), null)) //(1)!
    ```

    1.  `[2026-01-01,)`: from January 1, 2026 with no upper bound

`PostgreSQL` normalizes discrete range types (`int4range`, `int8range`, `daterange`) to the `[)` form and degenerate ranges to `empty`,
so a value read back may differ from the one written: `PgRange.closed(1, 5)` is read back as `[1,6)`.
`tstzrange` bounds are returned in the session time zone, so they denote the same instant but may carry a different offset.

## JSON { #postgres-json }

`@PgJson` maps a value to a `json` column and `@PgJsonb` to a `jsonb` column, through the [JSON](json.md) module
`JsonWriter<T>` / `JsonReader<T>` of the value type, so the value type must have them, for example by being annotated with `@Json`.
The two tags differ in the type of the bound parameter: `jsonb` operators such as `@>`, `?`, and `jsonb_path_query` require the parameter to be exactly `jsonb`,
so use `@PgJsonb` for `jsonb` columns. No `::jsonb` cast is needed in the query.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface UserRepository extends JdbcRepository {

        @Query("SELECT %{return#selects} FROM %{return#table} WHERE settings @> :filter")
        List<User> findBySettings(@PgJsonb User.Settings filter);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface UserRepository : JdbcRepository {

        @Query("SELECT %{return#selects} FROM %{return#table} WHERE settings @> :filter")
        fun findBySettings(@PgJsonb filter: User.Settings): List<User>
    }
    ```

A `NULL` column is read as `null`, and a `null` value is bound as `NULL`.
To tell a `NULL` column apart from a `JSON` `null` literal, declare the field as [`JsonNullable<T>`](json.md#jsonnullable-wrapper):
`JsonNullable.undefined()` corresponds to `NULL` in the column, `JsonNullable.nullValue()` to the `JSON` `null` literal,
and a defined value to the serialized value.
