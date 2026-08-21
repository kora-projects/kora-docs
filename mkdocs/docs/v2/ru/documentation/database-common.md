---
description: "Explains Common Kora database model and repository conventions: entities, identifiers, naming, embedded fields, query macros, batch queries, and repository inheritance. Use when working with @Table, @Column, @Id, @Embedded, @Repository, @Query, @Batch, @Mapping."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Common Kora database model and repository conventions: entities, identifiers, naming, embedded fields, query macros, batch queries, and repository inheritance; key triggers include @Table, @Column, @Id, @Embedded, @Repository, @Query, @Batch, @Mapping, Entity, Repository."
---

Базовые принципы и механизмы работы модулей баз данных в Kora.
В этом разделе описана общая модель для `JDBC`, `Cassandra`, `R2DBC` и `Vertx`: отображения, репозитории, параметры запросов, пакетные запросы, количество затронутых строк и макросы.
Конфигурация подключения, транзакции, поддерживаемые сигнатуры и специфичные для драйвера отображатели описаны в документации для каждой реализации базы данных.

Этот раздел намеренно не описывает специфичные для драйвера детали.
Конфигурацию подключения, транзакции, типы возвращаемых значений, генерируемые базой данных идентификаторы, служебные параметры методов
и точные интерфейсы отображателей смотрите в документации для нужной реализации:
[`JDBC`](database-jdbc.md), [`Cassandra`](database-cassandra.md), [`R2DBC`](database-r2dbc.md) или [`Vertx`](database-vertx.md).

Мы считаем, что лучший способ общения с базой данных SQL — это общение на её родном языке SQL.
Другие инструменты часто имеют ограничения на использование специфичных функций конкретной базы данных
или сложный программный язык для построения запросов, который требует дополнительного и значительного времени на изучение и освоение,
несёт много неочевидности и потенциальных ошибок со стороны разработчика, а также порой обладает низкой производительностью.

Если нужен пошаговый разбор перед справочным описанием, смотрите [База данных JDBC](../guides/database-jdbc.md) и [Продвинутая база данных JDBC](../guides/database-jdbc-advanced.md).

## Использование { #usage }

Использование показано на примере [`JDBC`](database-jdbc.md) модуля, сначала репозиторий объявляется как интерфейс, помеченный аннотацией `@Repository`, и должен наследовать `JdbcRepository`.
Каждый метод, помеченный `@Query`, содержит обычный `SQL`-запрос. Параметры метода связываются по имени с помощью
синтаксиса `:parameter`, а к полям объекта можно обращаться как `:entity.field`.

Отображения описываются с помощью общих аннотаций отображений и помечаются `@EntityJdbc`,
чтобы `Kora` сгенерировала отображатель на этапе компиляции оптимальнее:

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

    1.  Использует макрос `%{return#selects}` и `%{return#table}`. Разворачивается в запрос:
        ```sql
        SELECT id, name, description 
        FROM entities 
        WHERE id = :id
        ```
        Метод использует макросы для `SELECT`. Подробнее: [Общие правила работы с базами данных — Макросы](database-common.md#macros)
    2.  Поля перечислены вручную без использования макросов — это допустимо, но требует поддержки при изменении отображения.
    3.  Использует макрос `%{entity#inserts}`. Разворачивается в запрос:
        ```sql
        INSERT INTO entities(id, name, description) 
        VALUES(:entity.id, :entity.name, :entity.description)
        ```
        Метод использует макросы для `INSERT`. Подробнее: [Общие правила работы с базами данных — Макросы](database-common.md#macros)

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

        @Query("INSERT INTO %{entity#inserts}") //(3)!
        fun insert(entity: Entity): UpdateCount
    }
    ```

    1.  Использует макрос `%{return#selects}` и `%{return#table}`. Разворачивается в запрос:
        ```sql
        SELECT id, name, description 
        FROM entities 
        WHERE id = :id
        ```
        Метод использует макросы для `SELECT`. Подробнее: [Общие правила работы с базами данных — Макросы](database-common.md#macros)
    3.  Использует макрос `%{entity#inserts}`. Разворачивается в запрос:
        ```sql
        INSERT INTO entities(id, name, description) 
        VALUES(:entity.id, :entity.name, :entity.description)
        ```
        Метод использует макросы для `INSERT`. Подробнее: [Общие правила работы с базами данных — Макросы](database-common.md#macros)

`SQL` остается под контролем разработчика: вы можете использовать специфичные для базы данных возможности, тогда как `Kora`
берет на себя только безопасное связывание параметров, выполнение запроса и отображение результата.
Общие правила для отображений, `@Table`, `@Column`, `@Id`, `@Embedded`, `@Batch` или макросов описаны в разделе
[макросы](#macros).

**Связывание параметров:** Kora выполняет типизированное внедрение аргументов в SQL-запрос на этапе компиляции.
Параметры запроса (например, `:id`, `:entity.name`) заменяются в сгенерированном коде на соответствующие вызовы `PreparedStatement`.
Например, для параметра `String name` будет сгенерировано что-то вроде `statement.setString(1, name)`, где индекс соответствует порядку параметра в запросе.
Это обеспечивает безопасность (защита от SQL-инъекций) и производительность (использование подготовленных запросов).

## Отображение { #view }

Отображение — это представление данных из базы данных в виде класса с полями.

Отображения, используемые как возвращаемое значение, должны содержать единственный публичный
конструктор. Это может быть либо конструктор по умолчанию, либо конструктор с параметрами.
Если Kora находит конструктор с параметрами, объект отображения создаётся на его основе.
В случае пустого конструктора поля заполняются [через сеттеры](https://docs.oracle.com/cd/E19316-01/819-3669/bnais/index.html).

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record Entity(String id, String name) {}
    ```
=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class Entity(val id: String, val name: String)
    ```

### Таблица { #table }

Вы можете указать, к какой таблице относится отображение — это понадобится, если вы используете [макросы](#macros) при построении запросов.

Если таблица не указана, макросы используют имя класса в [`snake_lower_case`](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/).

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

### Идентификатор { #identifier }

Поскольку все манипуляции с данными выполняются путём преобразования отображения в запрос драйвера,
нет необходимости выделять внутри отображения специальный первичный ключ для работы с ней.

Определение того, что именно является первичным ключом, может быть полезно при использовании [макросов](#macros),
для этого можно использовать аннотацию `@Id`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record Entity(@Id String id, String name) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class Entity(@field:Id val id: String, val name: String)
    ```

#### Последовательный { #sequential }

Рассмотрим создание идентификатора в виде последовательности чисел на примере Postgres:
Kora предлагает использовать механизм базы данных [identity column](https://www.tutorialsteacher.com/postgresql/identity-column).

Пример таблицы для такого отображения выглядел бы так:

```sql
CREATE TABLE IF NOT EXISTS entities
(
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    name VARCHAR NOT NULL,
    PRIMARY KEY (id)
);
```

Идентификатор будет создан на этапе вставки в базу данных,
а его получение в коде приложения предполагается выполнять с помощью [возврата значения идентификатора для JDBC или R2DBC](database-jdbc.md#generated-identifier) при вставке
либо использовать [специальные конструкции](https://www.postgresql.org/docs/current/dml-returning.html) вашей базы данных:

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

Вместо специфичного для драйвера `RETURNING` первичный ключ, сгенерированный базой данных при вставке, можно вернуть,
пометив сам **метод** репозитория аннотацией `@Id` (аннотация применима как к полю отображения, так и к методу).
Точное поведение генерируемого идентификатора и поддерживаемые сигнатуры возвращаемого значения специфичны для драйвера и описаны
для [JDBC](database-jdbc.md#generated-identifier) и [R2DBC](database-r2dbc.md#generated-identifier):

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Table("entities")
        public record Entity(@Id Long id, String name) {}

        @Id //(1)!
        @Query("INSERT INTO %{entity#inserts -= id}") //(2)!
        long insert(Entity entity);
    }
    ```

    1.  Помечает метод так, чтобы возвращался идентификатор, сгенерированный базой данных.
    2.  Разворачивается в запрос:
        ```sql
        INSERT INTO entities(name) VALUES(:entity.name)
        ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Table("entities")
        data class Entity(@field:Id val id: Long, val name: String)

        @Id //(1)!
        @Query("INSERT INTO %{entity#inserts -= id}") //(2)!
        fun insert(entity: Entity): Long
    }
    ```

    1.  Помечает метод так, чтобы возвращался идентификатор, сгенерированный базой данных.
    2.  Разворачивается в запрос:
        ```sql
        INSERT INTO entities(name) VALUES(:entity.name)
        ```

#### Случайный { #random }

Для создания случайного идентификатора предлагается использовать стандартный `UUID` из Java:

Пример таблицы для такого отображения выглядел бы так:

```sql
CREATE TABLE IF NOT EXISTS entities
(
    id UUID NOT NULL,
    name VARCHAR NOT NULL,
    PRIMARY KEY (id)
);
```

Идентификатор будет создан на этапе создания объекта в пользовательском коде приложения:

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

#### Составной { #composite }

Когда требуется составной ключ, для создания [встроенных полей](#embedded-fields) предполагается использовать аннотацию `@Embedded`.

### Именование { #naming }

По умолчанию имена полей отображения при получении результата преобразуются в [`snake_lower_case`](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/).

Если вы хотите настроить отображение конкретных полей из базы данных на отображение, можно использовать аннотацию `@Column`:

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

#### Стратегия именования { #naming-strategy }

Если вы хотите использовать стратегию именования для всего отображения, предлагается создать реализацию `NameConverter`, а затем использовать её в аннотации `@NamingStrategy`.
Требуется, чтобы реализация `NameConverter` имела конструктор без параметров.

Либо используйте доступные стратегии из Kora:

- `NoopNameConverter` — стратегия использует имя поля по умолчанию.
- `SnakeCaseNameConverter` — стратегия использует [`snake_lower_case`](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/).
- `SnakeCaseUpperNameConverter` — стратегия использует [SNAKE_UPPER_CASE](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/).
- `PascalCaseNameConverter` — стратегия использует [PascalCase](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/).
- `CamelCaseNameConverter` — стратегия использует [camelCase](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/).

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

### Обязательные поля { #required-fields }

===! ":fontawesome-brands-java: `Java`"

    По умолчанию все поля, объявленные в отображении, считаются **обязательными** (*NotNull*).

    ```java
    public record Entity(String id,
                         String name) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    По умолчанию все поля, объявленные в отображении и не использующие синтаксис [Kotlin Nullability](https://kotlinlang.org/docs/null-safety.html), считаются **обязательными** (*NotNull*).

    ```kotlin
    data class Entity(val id: String,
                      val name: String)
    ```

### Необязательные поля { #optional-fields }

===! ":fontawesome-brands-java: `Java`"

    Если поле отображения необязательное, то есть может отсутствовать,
    используйте аннотацию `@Nullable`, чтобы явно его пометить.

    ```java
    public record Entity(String id, 
                         @Nullable String name) {} //(1)!
    ```

    1.  Подойдёт любая аннотация `@Nullable`, например `javax.annotation.Nullable` / `jakarta.annotation.Nullable` / `org.jetbrains.annotations.Nullable` / и т.д.

    Также можно указать необязательные параметры конструктора в случае, если канонический конструктор Record переопределён:

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

    1.  Подойдёт любая аннотация `@Nullable`, например `javax.annotation.Nullable` / `jakarta.annotation.Nullable` / `org.jetbrains.annotations.Nullable` / и т.д.

=== ":simple-kotlin: `Kotlin`"

    Ожидается использование синтаксиса [Kotlin Nullability](https://kotlinlang.org/docs/null-safety.html) и пометка такого параметра как Nullable:

    ```kotlin
    data class Entity(val id: String,
                      val name: String?)
    ```

### Встроенные поля { #embedded-fields }

Если вы хотите использовать вложенные поля, то есть преобразовать поля отображения в отдельные классы, можно использовать аннотацию `@Embedded`.

Предположим, есть SQL-таблица, в которой присутствует составной ключ, который мы хотим выразить как отдельный класс:

```sql
CREATE TABLE IF NOT EXISTS entities
(
    name    VARCHAR NOT NULL,
    surname VARCHAR NOT NULL,
    info    VARCHAR NOT NULL,
    PRIMARY KEY (name, surname)
)
```

Тогда отображение будет выглядеть так:

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

Тогда репозиторий для такого отображения выглядел бы так:

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

Если поля имеют общий префикс, его можно указать в аннотации `@Embedded("user_")`:

```sql
CREATE TABLE IF NOT EXISTS entities
(
    user_name       VARCHAR NOT NULL,
    user_surname    VARCHAR NOT NULL,
    info            VARCHAR NOT NULL,
    PRIMARY KEY (user_name, user_surname)
)
```

## Репозиторий { #repository }

Основной инструмент для работы с базами данных в Kora — использование [паттерна репозиторий](https://java-design-patterns.com/patterns/repository/#explanation) при проектировании абстракции доступа к базе данных.
Интерфейс репозитория должен быть помечен аннотацией `@Repository`.
Запросы для методов репозитория описываются с помощью аннотации `@Query`.
Реализация репозитория создаётся во время компиляции, все методы `@Query` будут выполнять описанный запрос, оптимально собирать аргументы запроса и обрабатывать результат.

Предполагается, что `SQL`-запросы пишет разработчик, поскольку это повышает понимание разработчиком плана запроса,
даёт больше представления и контекста о том, что делает запрос и как он будет работать.
Вы можете использовать [макросы](#macros) для улучшения удобства работы, чтобы не писать все поля/столбцы модели.

Репозиторий должен наследовать одну из реализаций, в примерах ниже будет рассмотрена реализация [JDBC](database-jdbc.md):

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

    1. Указывает, что интерфейс является репозиторием.
    2. Указывает, что Kora должна создать реализацию метода, выполняющую `SQL`-запрос, указанный в аннотации.

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

    1. Указывает, что интерфейс является репозиторием.
    2. Указывает, что Kora должна создать реализацию метода, выполняющую `SQL`-запрос, указанный в аннотации.

### Параметры запроса { #query-parameters }

Параметры метода репозитория связываются с именованными параметрами в `@Query`.
Простой параметр указывается по имени параметра метода: `:id`, `:name`, `:status`.
Если параметр является отображением или `DTO`, к его полям можно обращаться через точечную нотацию: `:entity.id`, `:entity.name`, `:filter.status`.

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

Если параметр встречается в запросе более одного раза, Kora связывает его с каждым вхождением.
Если параметр метода не используется в запросе и не является служебным параметром конкретного драйвера, компиляция завершается с ошибкой.

### Отображатели { #mappers }

Используйте аннотацию `@Mapping`, когда значению нужно нестандартное представление в базе данных.
Её можно разместить на поле отображения, параметре метода или методе репозитория:

- на поле отображения — чтобы настроить чтение или запись конкретного столбца;
- на параметре метода — чтобы настроить запись конкретного параметра запроса;
- на методе репозитория — чтобы настроить обработку всего результата запроса или строки результата.

Произвольный отображатель нельзя использовать в любом месте: его тип должен соответствовать месту применения.
Отображатель параметра применяется к параметру запроса, отображатель столбца — к полю отображения, а отображатель результата или строки — к методу репозитория.
Точный набор поддерживаемых интерфейсов зависит от драйвера: например, `JDBC` использует `JdbcRowMapper`, `JdbcResultSetMapper`, `JdbcResultColumnMapper` и `JdbcParameterColumnMapper`.
Похожие интерфейсы для `Cassandra`, `R2DBC` и `Vertx`, а также детали их использования описаны в документации для каждой реализации базы данных.
Все отображатели строк драйверов имеют общий маркерный интерфейс `RowMapper<T>` (`ru.tinkoff.kora.database.common.RowMapper`), который является базовым типом для специфичных для драйвера отображателей, таких как `JdbcRowMapper` и `CassandraRowMapper`.
Сама аннотация `@Mapping` находится в основном модуле `common` (`ru.tinkoff.kora.common.Mapping`).
Если отображатель указан через `@Mapping`, Kora добавляет его как зависимость сгенерированного репозитория и использует вместо отображателя по умолчанию.

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

### Пакетный запрос { #batch-query }

Kora поддерживает пакетные запросы с помощью аннотации `@Batch`.

В отличие от последовательного выполнения SQL-запросов, пакетная обработка позволяет отправить целый набор запросов за один вызов,
сокращая число требуемых сетевых обращений и позволяя выполнять часть запросов параллельно на стороне базы данных,
что может повысить скорость выполнения.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        void insert(@Batch List<Entity> entity);
    }
    ```

    **Пакетный запрос** не может возвращать произвольные значения — такой метод может возвращать `void`, либо `UpdateCount`, 
    либо генерируемые базой данных идентификаторы для драйверов [JDBC](database-jdbc.md#generated-identifier) или [R2DBC](database-r2dbc.md#generated-identifier).

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        fun insert(@Batch entity: List<Entity>)
    }
    ```

    **Пакетный запрос** не может возвращать произвольные значения — такой метод может возвращать `Unit`, либо `UpdateCount`, 
    либо генерируемые базой данных идентификаторы для драйверов [JDBC](database-jdbc.md#generated-identifier) или [R2DBC](database-r2dbc.md#generated-identifier).

`@Batch` ставится на параметр-коллекцию, и каждый элемент коллекции по очереди подставляется в один и тот же запрос.
Все остальные параметры метода, если они есть, являются общими для всех элементов пакета.
Например, в `INSERT INTO logs(tenant_id, id, value) VALUES (:tenantId, :entity.id, :entity.value)`
параметр `tenantId` одинаков для каждого элемента, тогда как поля `entity` берутся из каждого элемента коллекции.

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

Метод должен иметь не более одного параметра, помеченного `@Batch`.
Поддержка генерируемых базой данных идентификаторов в пакетных запросах зависит от конкретного драйвера и описана в соответствующем разделе.

### Затронутые строки { #affected-rows }

Kora не обрабатывает содержимое запроса, результат метода всегда выводится из строк, возвращённых базой данных.
Если вы хотите получить в результате количество затронутых строк, используйте специальный тип `UpdateCount`.
Для обычного запроса `UpdateCount#value()` содержит количество строк, возвращённое драйвером для выполненного запроса.
Для пакетного запроса значение обычно является суммой результатов по всем элементам пакета; точное поведение зависит от драйвера базы данных.

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

### Ручной запрос { #manual-query }

Если по какой-либо причине функциональности запросов в аннотации `@Query` недостаточно или требуется ручное управление соединением,
можно использовать встроенный метод фабрики соединений, чтобы создать метод с полностью ручным управлением.

Внутри такого метода можно также использовать другие методы репозитория, и при необходимости они тоже будут выполняться в рамках одной транзакции.
Подробнее о транзакциях смотрите в документации для конкретной реализации репозитория.

Репозитории могут объявлять обычные методы с реализациями.
Это полезно, когда более сложную операцию стоит держать рядом с запросами: например, выполнение нескольких методов `@Query` в одной транзакции,
построение результата из нескольких запросов или хранение последовательности операций с базой данных внутри репозитория вместо переноса её в слой сервиса.

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

Когда вы строите `SQL` вручную через фабрику соединений драйвера, а не с помощью метода `@Query`,
запрос всё равно проходит через телеметрию Kora. Выполняемый запрос описывается общим
`QueryContext(queryId, sql, operation)`: `queryId` — это стабильный идентификатор запроса, передаваемый в телеметрию
(удобно использовать имя вида `Repository.method`), `sql` — итоговый текст запроса, а `operation` по умолчанию равно `db_query`.
Точный метод фабрики соединений и его сигнатура специфичны для драйвера — рабочий пример смотрите в [JDBC](database-jdbc.md#query).

### Несколько баз данных { #multiple-databases }

Иногда в рамках одного приложения нужно обращаться к разным базам данных в разных репозиториях,
это можно решить следующим образом.
Нужно создать отдельный экземпляр базы данных и подключить его к репозиторию,
ниже приведён пример для базы данных [JDBC](database-jdbc.md), но принцип аналогичен для других типов соединений.

Требуется скопировать фабрики создания `JdbcDatabase` и его конфигурацию из модуля `JdbcDatabaseModule`
и присвоить им собственный тег, который будет указывать, что это соединения для другой базы данных.

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

А репозитории, которые будут использовать эту базу данных, теперь обязаны указывать тег этого соединения:

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

Репозиториям с основным соединением к базе данных тег не требуется.

### Макросы { #macros }

Самой утомительной частью написания SQL-запросов может быть перечисление и поддержание в актуальном состоянии столбцов и полей отображения.

Чтобы решить эту проблему, используйте специальные макросы внутри `SQL`-запроса в аннотации `@Query`.
Эти конструкции оперируют целевым [отображением](#view), разворачивают её в конкретные `SQL`-конструкции и упрощают расширение `SQL`-запросов.
Макрос — это помощник для написания `SQL`-запросов, который разворачивается в конструкции, которые пользователь мог бы написать вручную.

Синтаксис макросов выглядит следующим образом: `%{return#selects}`.

1. Макрос ограничен синтаксической конструкцией `%{` и `}`
2. Сначала указывается цель макроса — это может быть имя любого аргумента метода или возвращаемое значение с помощью ключевого слова `return`
3. Затем символ `#` используется для разделения цели макроса и команды макроса
4. После этого указывается команда макроса, которая сообщает, в какую SQL-конструкцию развернуть отображение

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

    1.  Разворачивается в запрос:
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

    1.  Разворачивается в запрос:
        ```sql
        SELECT id, entity_name, code FROM entities
        ```

#### Команды { #commands }

Доступные команды макросов:

- `table` — разворачивает значение отображения из [аннотации](#table) `@Table`, либо, если она отсутствует, преобразует имя отображения в [`snake_lower_case`](https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/)
- `selects` — создаёт конструкцию перечисления столбцов отображения для запроса `SELECT`
- `inserts` — создаёт конструкцию перечисления таблицы, столбцов и соответствующих полей отображения для запроса `INSERT`
- `updates` — создаёт конструкцию перечисления столбцов и соответствующих полей отображения для запроса `UPDATE`
- `where` — создаёт конструкцию перечисления столбцов со значением из отображения для части `WHERE` запроса

#### Перечисление полей { #field-enumeration }

Макрос поддерживает дополнительный синтаксис для перечисления определённых полей в команде,
если вдруг нужно выполнить частичное обновление или получение данных.
Для этого после команды используется специальная конструкция: `%{return#updates=name}`.

Пробелы можно ставить **только** между полями в перечислении или специальным символом перечисления.

Доступны специальные символы перечисления:

1. `=` — в разворачивании команды будут участвовать только поля отображения, имена которых указаны после символа
2. `-=` — в разворачивании команды будут участвовать все поля отображения, кроме указанных после символа

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

    1.  Разворачивается в запрос:
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

    1.  Разворачивается в запрос:
        ```sql
        INSERT INTO entities(entity_name, code) 
        VALUES(:entity.name, :entity.code)
        ```

##### Идентификатор { #identifier-2 }

При перечислении полей в макросе можно использовать специальное ключевое слово `@id`,
чтобы сразу обратиться к идентификатору отображения, помеченному [аннотацией](#identifier) `@Id`.

Это может быть особенно полезно, когда идентификатор является [составным ключом](#embedded-fields), чтобы перечислить сразу все столбцы.

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

    1.  Разворачивается в запрос:
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

    1.  Разворачивается в запрос:
        ```sql
        INSERT INTO entities(entity_name, code) 
        VALUES(:entity.name, :entity.code)
        ```

#### Пример репозитория { #repository-example }

Пример полного репозитория со всеми основными методами для работы с отображением для [Postgres SQL](https://postgrespro.com/docs/postgresql):

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

    1.  Разворачивается в запрос:
        ```sql
        SELECT id, value1, value2, value3 
        FROM entities 
        WHERE id = :id
        ```
    2.  Разворачивается в запрос:
        ```sql
        SELECT id, value1, value2, value3 
        FROM entities
        ```
    3.  Разворачивается в запрос:
        ```sql
        INSERT INTO entities(id, value1, value2, value3) 
        VALUES(:entity.id, :entity.field1, :entity.value2, :entity.value3)
        ```
    4.  Разворачивается в запрос:
        ```sql
        UPDATE entities
        SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3 
        WHERE id = :entity.id
        ```
    5.  Разворачивается в запрос:
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
    1.  Разворачивается в запрос:
        ```sql
        SELECT id, value1, value2, value3 
        FROM entities 
        WHERE id = :id
        ```
    2.  Разворачивается в запрос:
        ```sql
        SELECT id, value1, value2, value3 
        FROM entities
        ```
    3.  Разворачивается в запрос:
        ```sql
        INSERT INTO entities(id, value1, value2, value3) 
        VALUES(:entity.id, :entity.field1, :entity.value2, :entity.value3)
        ```
    4.  Разворачивается в запрос:
        ```sql
        UPDATE entities
        SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3 
        WHERE id = :entity.id
        ```
    5.  Разворачивается в запрос:
        ```sql
        INSERT INTO entities(id, value1, value2, value3) 
        VALUES(:entity.id, :entity.field1, :entity.value2, :entity.value3)
        ON CONFLICT (id) DO UPDATE 
        SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3 
        ```

#### Пример с составным идентификатором { #composite-example }

Пример репозитория с [составным идентификатором](#composite) и основными методами для работы с отображением,
он практически идентичен предыдущему за исключением условий `WHERE` для поиска и удаления для [Postgres SQL](https://postgrespro.com/docs/postgresql):

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

    1.  Разворачивается в запрос:
        ```sql
        SELECT code, type, value1, value2, value3 
        FROM entities 
        WHERE code = :code AND type = :type
        ```
    2.  Разворачивается в запрос:
        ```sql
        SELECT code, type, value1, value2, value3 
        FROM entities
        ```
    3.  Разворачивается в запрос:
        ```sql
        INSERT INTO entities(code, type, value1, value2, value3) 
        VALUES(:entity.id.code, :entity.id.type, :entity.field1, :entity.value2, :entity.value3)
        ```
    4.  Разворачивается в запрос:
        ```sql
        UPDATE entities
        SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3 
        WHERE code = :entity.id.code AND type = :entity.id.type
        ```
    5.  Разворачивается в запрос:
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
    1.  Разворачивается в запрос:
        ```sql
        SELECT code, type, value1, value2, value3 
        FROM entities 
        WHERE code = :code AND type = :type
        ```
    2.  Разворачивается в запрос:
        ```sql
        SELECT code, type, value1, value2, value3 
        FROM entities
        ```
    3.  Разворачивается в запрос:
        ```sql
        INSERT INTO entities(code, type, value1, value2, value3) 
        VALUES(:entity.id.code, :entity.id.type, :entity.field1, :entity.value2, :entity.value3)
        ```
    4.  Разворачивается в запрос:
        ```sql
        UPDATE entities
        SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3 
        WHERE code = :entity.id.code AND type = :entity.id.type
        ```
    5.  Разворачивается в запрос:
        ```sql
        INSERT INTO entities(code, type, value1, value2, value3) 
        VALUES(:entity.id.code, :entity.id.type, :entity.field1, :entity.value2, :entity.value3)
        ON CONFLICT (code, type) DO UPDATE 
        SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3 
        ```

#### Пример с наследованием { #inheritance-example }

Вы также можете создать абстрактный CRUD-репозиторий, а затем использовать его в наследовании для [Postgres SQL](https://postgrespro.com/docs/postgresql):

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

## Телеметрия { #telemetry }

Все драйверы баз данных используют общий контракт телеметрии для логирования, метрик и трассировки запросов.
Конкретные параметры конфигурации (секция `telemetry { logging / metrics / tracing }`) описаны в документации
для каждого драйвера, например [JDBC](database-jdbc.md#configuration); этот раздел документирует только общие точки расширения,
которые находятся в `ru.tinkoff.kora.database.common.telemetry`.

Для каждого выполняемого запроса создаётся `DataBaseTelemetry.DataBaseTelemetryContext`, который закрывается по завершении запроса
(получая выброшенное исключение, если оно было).
Выполняемый запрос описывается `QueryContext(queryId, sql, operation)`, где `queryId` — это стабильный идентификатор запроса,
передаваемый в телеметрию, `sql` — итоговый текст запроса, а `operation` по умолчанию равно `db_query`.

Фабрика по умолчанию `DefaultDataBaseTelemetryFactory` объединяет три необязательные вложенные фабрики:

- `DataBaseLoggerFactory` строит `DataBaseLogger`, который логирует начало/конец запроса (`logQueryBegin` / `logQueryEnd`);
- `DataBaseMetricWriterFactory` строит `DataBaseMetricWriter`, который записывает метрики для каждого запроса (`recordQuery`);
- `DataBaseTracerFactory` строит `DataBaseTracer`, который создаёт спаны запроса и вызова для распределённой трассировки.

Если ни одна из вложенных фабрик не создаёт реализацию (например, когда логирование, [метрики](metrics.md) и [трассировка](tracing.md)
все отключены в конфигурации), используется `DataBaseTelemetryFactory.EMPTY`, и телеметрия становится пустой операцией.

Чтобы полностью настроить свою собственную телеметрию, предоставьте собственную `DataBaseTelemetryFactory` в [графе приложения](container.md),
которая [переопределяет](container.md#component-override) фабрику по умолчанию:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends JdbcDatabaseModule {

        default DataBaseTelemetryFactory dataBaseTelemetryFactory() { //(1)!
            return (config, name, driverType, dbType, username) -> {
                // build and return a custom DataBaseTelemetry
                return DataBaseTelemetryFactory.EMPTY;
            };
        }
    }
    ```

    1.  Переопределяет фабрику `DataBaseTelemetryFactory` по умолчанию, предоставляемую `DataBaseModule`.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : JdbcDatabaseModule {

        fun dataBaseTelemetryFactory(): DataBaseTelemetryFactory { //(1)!
            return DataBaseTelemetryFactory { config, name, driverType, dbType, username ->
                // build and return a custom DataBaseTelemetry
                DataBaseTelemetryFactory.EMPTY
            }
        }
    }
    ```

    1.  Переопределяет фабрику `DataBaseTelemetryFactory` по умолчанию, предоставляемую `DataBaseModule`.
