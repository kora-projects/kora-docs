---
seo_title: "Kora JDBC PostgreSQL: массивы, интервалы, диапазоны и JSON"
seo_description: "Справочник по модулю database-jdbc-postgres в Kora: подключение, массивы и коллекции PostgreSQL, интервалы, диапазоны и отображатели столбцов JSON / JSONB."
keywords: ["Kora Framework", "Kora JDBC", "PostgreSQL", "database-jdbc-postgres", "PostgreSQL arrays", "PostgreSQL range types", "PostgreSQL JSONB"]
description: "Explains the Kora PostgreSQL JDBC module, its dependencies and column mappers for arrays, collections, intervals, ranges and JSON / JSONB. Use when working with PostgresJdbcDatabaseModule, @Pg, @PgJson, @PgJsonb and PgRange."
agent:
  use_when: "Use this file for PostgreSQL-specific JDBC column mappers; key triggers include database-jdbc-postgres, PostgresJdbcDatabaseModule, PgCollectionJdbcMappersModule, PgArrayJdbcMappersModule, PgIntervalJdbcMappersModule, PgRangeJdbcMappersModule, PgJsonJdbcMappersModule, @Pg, @PgJson, @PgJsonb, PgRange, JsonNullable, interval, int4range, tstzrange."
---

Модуль `database-jdbc-postgres` добавляет отображатели столбцов для представлений, специфичных для `PostgreSQL`:
массивов, `interval`, range-типов и `json` / `jsonb`.
Репозитории, отображения и конфигурация `jdbc` описаны в [документации JDBC](database-jdbc.md);
модуль лишь добавляет отображатели в [граф приложения](container.md).

## Подключение { #postgres-dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:database-jdbc-postgres"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends PostgresJdbcDatabaseModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:database-jdbc-postgres")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : PostgresJdbcDatabaseModule
    ```

`PostgresJdbcDatabaseModule` наследует `JdbcDatabaseModule`, поэтому подключается вместо него, а не рядом с ним.
Модуль приносит драйвер `PostgreSQL` `org.postgresql:postgresql` транзитивной зависимостью.

`PostgresJdbcDatabaseModule` объединяет пять модулей отображателей из `io.koraframework.database.jdbc.postgres.mapper`:
`PgCollectionJdbcMappersModule`, `PgArrayJdbcMappersModule`, `PgIntervalJdbcMappersModule`, `PgRangeJdbcMappersModule` и `PgJsonJdbcMappersModule`.
Если нужна только часть отображателей, унаследуйте `JdbcDatabaseModule` вместе с нужными модулями:

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

Отображатели для обычных типов `JDK` регистрируются с тегом, поэтому никогда не меняют отображение поля неявно:
отображатели коллекций, массивов, `Duration` и `Period` помечены тегом `@Pg`,
а отображатели `JSON` — тегом `@PgJson` или `@PgJsonb` (все из `io.koraframework.database.jdbc.postgres.annotation`).
Чтобы выбрать отображатель `PostgreSQL`, поставьте аннотацию на поле отображения или на параметр метода репозитория.
Отображателям `PgRange` тег не нужен, потому что `PgRange` сам по себе специфичен для `PostgreSQL`.
Каждый отображатель объявлен как [`@DefaultComponent`](container.md#default-factory), поэтому ваш собственный отображатель того же типа и с тем же тегом заменяет его.

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

    1.  Столбец типа `varchar[]`
    2.  Столбец типа `interval`
    3.  Столбец типа `daterange`, тег не нужен
    4.  Столбец типа `jsonb`, `Settings` записывается и читается через `JsonWriter` / `JsonReader`, сгенерированные для типа с `@Json`
    5.  Список связывается как один параметр `int8[]`, поэтому для `= ANY(:ids)` не нужен собственный отображатель

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

    1.  Столбец типа `varchar[]`
    2.  Столбец типа `interval`
    3.  Столбец типа `daterange`, тег не нужен
    4.  Столбец типа `jsonb`, `Settings` записывается и читается через `JsonWriter` / `JsonReader`, сгенерированные для типа с `@Json`
    5.  Список связывается как один параметр `int8[]`, поэтому для `= ANY(:ids)` не нужен собственный отображатель

## Массивы и коллекции { #postgres-arrays }

С `@Pg` коллекции и массивы связываются как массив `PostgreSQL` и читаются из него:

| Тип элемента | Элемент массива `PostgreSQL` |
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

- Параметр может быть `List<T>`, `Set<T>` или `Collection<T>`, поэтому коллекцию не нужно копировать ради вызова.
  Результат всегда `List<T>`; уникальность задается запросом, например через `DISTINCT`.
- Массивы поддерживаются как `T[]` для всех типов элементов выше (`Array<T>` в `Kotlin`) и как примитивные массивы
  `boolean[]`, `short[]`, `int[]`, `long[]`, `float[]`, `double[]` (`BooleanArray`, `ShortArray`, `IntArray`, `LongArray`, `FloatArray`, `DoubleArray` в `Kotlin`).
- Элементы `NULL` передаются как есть для коллекций и массивов объектов.
  Примитивный массив не может содержать `NULL`, поэтому чтение в него массива с элементом `NULL` завершается `SQLException`.
- Столбец `NULL` читается как `null`, а значение `null` связывается как `NULL`.

## Интервалы { #postgres-interval }

С `@Pg` типы `java.time.Duration` и `java.time.Period` связываются со столбцом `interval` и читаются из него.
`Duration` записывается как дни, часы, минуты и секунды с дробной частью, а `Period` — как годы, месяцы и дни.
У месяцев и лет нет фиксированной длины, поэтому чтение `interval` с годами или месяцами в `Duration` завершается `SQLException`;
для таких значений используйте `Period`.
Точно так же чтение `interval` с временной частью в `Period` завершается ошибкой; для него используйте `Duration`.

## Диапазоны { #postgres-range }

`PgRange<T>` из `io.koraframework.database.jdbc.postgres` представляет значение range-типа, и тег ему не нужен:

| Тип `Java` | Тип `PostgreSQL` |
|---|---|
| `PgRange<Integer>` | `int4range` |
| `PgRange<Long>` | `int8range` |
| `PgRange<BigDecimal>` | `numrange` |
| `PgRange<LocalDate>` | `daterange` |
| `PgRange<LocalDateTime>` | `tsrange` |
| `PgRange<OffsetDateTime>` | `tstzrange` |

`PgRange` — это record из `lower`, `upper`, `lowerInclusive`, `upperInclusive` и `isEmpty`; граница `null` означает, что с этой стороны диапазон не ограничен.
Фабричные методы покрывают привычные формы: `closed` `[a,b]`, `closedOpen` `[a,b)`, `openClosed` `(a,b]`, `open` `(a,b)` и `empty()`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface UserRepository extends JdbcRepository {

        @Query("SELECT %{return#selects} FROM %{return#table} WHERE validity && :period")
        List<User> findValidWithin(PgRange<LocalDate> period);
    }

    var users = repository.findValidWithin(PgRange.closedOpen(LocalDate.of(2026, 1, 1), null)); //(1)!
    ```

    1.  `[2026-01-01,)`: с 1 января 2026 года без верхней границы

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface UserRepository : JdbcRepository {

        @Query("SELECT %{return#selects} FROM %{return#table} WHERE validity && :period")
        fun findValidWithin(period: PgRange<LocalDate>): List<User>
    }

    val users = repository.findValidWithin(PgRange.closedOpen(LocalDate.of(2026, 1, 1), null)) //(1)!
    ```

    1.  `[2026-01-01,)`: с 1 января 2026 года без верхней границы

`PostgreSQL` приводит дискретные range-типы (`int4range`, `int8range`, `daterange`) к форме `[)`, а вырожденные диапазоны — к `empty`,
поэтому прочитанное значение может отличаться от записанного: `PgRange.closed(1, 5)` читается обратно как `[1,6)`.
Границы `tstzrange` возвращаются в часовом поясе сессии, поэтому обозначают тот же момент времени, но могут иметь другое смещение.

## JSON { #postgres-json }

`@PgJson` отображает значение в столбец `json`, а `@PgJsonb` — в столбец `jsonb` через `JsonWriter<T>` / `JsonReader<T>`
модуля [JSON](json.md) для типа значения, поэтому у типа значения они должны быть, например за счет аннотации `@Json`.
Теги различаются типом связываемого параметра: операторы `jsonb`, такие как `@>`, `?` и `jsonb_path_query`, требуют, чтобы параметр был именно `jsonb`,
поэтому для столбцов `jsonb` используйте `@PgJsonb`. Приведение `::jsonb` в запросе не нужно.

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

Столбец `NULL` читается как `null`, а значение `null` связывается как `NULL`.
Чтобы отличать `NULL` в столбце от литерала `JSON` `null`, объявите поле как [`JsonNullable<T>`](json.md#jsonnullable-wrapper):
`JsonNullable.undefined()` соответствует `NULL` в столбце, `JsonNullable.nullValue()` — литералу `JSON` `null`,
а определенное значение — сериализованному значению.
