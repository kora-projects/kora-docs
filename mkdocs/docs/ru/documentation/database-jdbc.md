---
description: "Explains Kora JDBC repositories, JDBC configuration, result and parameter mapping, generated identifiers, transactions, and repository method signatures. Use when working with @Repository, @Query, @EntityJdbc, @Table, @Id, @Column, @Batch, JdbcDatabaseModule."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora JDBC repositories, JDBC configuration, result and parameter mapping, generated identifiers, transactions, and repository method signatures; key triggers include @Repository, @Query, @EntityJdbc, @Table, @Id, @Column, @Batch, JdbcDatabaseModule, JdbcConnectionFactory, JdbcRepository."
---

Модуль предоставляет реализацию репозитория на основе [JDBC](https://proselyte.net/tutorials/jdbc/introduction/) для
работы с реляционными базами данных и использует [Hikari](https://github.com/brettwooldridge/HikariCP) для управления пулом
соединений.
Вы описываете интерфейс репозитория и `SQL`-запросы с помощью `@Repository` и `@Query`, а `Kora` генерирует реализацию,
которая получает соединение из пула, связывает параметры, читает результат и участвует в транзакциях.

Общие правила для отображений, `@Repository`, `@Query`, `@Batch`, `UpdateCount`, макросов, ручных запросов и других механизмов
репозитория описаны в разделе [Общие правила работы с базами данных](database-common.md).

Если нужен пошаговый разбор перед справочным описанием, смотрите [База данных JDBC](../guides/database-jdbc.md) и [Продвинутая база данных JDBC](../guides/database-jdbc-advanced.md).

## Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:database-jdbc"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends JdbcDatabaseModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:database-jdbc")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : JdbcDatabaseModule
    ```

Также вы **обязаны предоставить** реализацию драйвера базы данных в качестве зависимости.

## Конфигурация { #configuration }

Основные параметры конфигурации JDBC:

===! ":material-code-json: `HOCON`"

    ```javascript
    db {
        jdbcUrl = "jdbc:postgresql://localhost:5432/postgres" //(1)!
        username = "postgres" //(2)!
        password = "postgres" //(3)!
        poolName = "kora" //(4)!
        maxPoolSize = 10 //(5)!
    }
    ```

    1.  `JDBC URL` для подключения к базе данных (`обязательный`, по умолчанию: не указано)
    2.  Имя пользователя для подключения (`обязательный`, по умолчанию: не указано)
    3.  Пароль пользователя для подключения (`обязательный`, по умолчанию: не указано)
    4.  Имя пула соединений `Hikari` (`обязательный`, по умолчанию: не указано)
    5.  Максимальный размер пула соединений `Hikari` (по умолчанию: `10`)

=== ":simple-yaml: `YAML`"

    ```yaml
    db:
      jdbcUrl: "jdbc:postgresql://localhost:5432/postgres" #(1)!
      username: "postgres" #(2)!
      password: "postgres" #(3)!
      poolName: "kora" #(4)!
      maxPoolSize: 10 #(5)!
    ```

    1.  `JDBC URL` для подключения к базе данных (`обязательный`, по умолчанию: не указано)
    2.  Имя пользователя для подключения (`обязательный`, по умолчанию: не указано)
    3.  Пароль пользователя для подключения (`обязательный`, по умолчанию: не указано)
    4.  Имя пула соединений `Hikari` (`обязательный`, по умолчанию: не указано)
    5.  Максимальный размер пула соединений `Hikari` (по умолчанию: `10`)

??? note "Полная конфигурация"

    Пример полной конфигурации, описанной в классе `JdbcDatabaseConfig`:

    ===! ":material-code-json: `HOCON`"

        ```javascript
        db {
            jdbcUrl = "jdbc:postgresql://localhost:5432/postgres" //(1)!
            username = "postgres" //(2)!
            password = "postgres" //(3)!
            schema = "public" //(4)!
            poolName = "kora" //(5)!
            maxPoolSize = 10 //(6)!
            minIdle = 0 //(7)!
            connectionTimeout = "10s" //(8)!
            validationTimeout = "5s" //(9)!
            idleTimeout = "10m" //(10)!
            maxLifetime = "15m" //(11)!
            leakDetectionThreshold = "0s" //(12)!
            initializationFailTimeout = "0s" //(13)!
            readinessProbe = false //(14)!
            dsProperties { //(15)!
                "hostRecheckSeconds": "2"
            }
            telemetry {
                logging {
                    enabled = false //(16)!
                }
                metrics {
                    enabled = true //(17)!
                    slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(18)!
                    tags = { // (19)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
                tracing {
                    enabled = true //(20)!
                    attributes = { // (21)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
            }
        }
        ```

        1.  `JDBC URL` для подключения к базе данных (`обязательный`, по умолчанию: не указано)
        2.  Имя пользователя для подключения (`обязательный`, по умолчанию: не указано)
        3.  Пароль пользователя для подключения (`обязательный`, по умолчанию: не указано)
        4.  Схема базы данных для подключения (по умолчанию: не указано, необязательно)
        5.  Имя пула соединений `Hikari` (`обязательный`, по умолчанию: не указано)
        6.  Максимальный размер пула соединений `Hikari` (по умолчанию: `10`)
        7.  Минимальное количество простаивающих готовых соединений в пуле `Hikari` (по умолчанию: `0`)
        8.  Максимальное время ожидания соединения из пула `Hikari` (по умолчанию: `10s`)
        9.  Максимальное время проверки соединения `Hikari` (по умолчанию: `5s`)
        10. Максимальное время простоя соединения `Hikari` (по умолчанию: `10m`)
        11. Максимальное время жизни соединения `Hikari` (по умолчанию: `15m`)
        12. Время, после которого занятое соединение считается возможной утечкой (по умолчанию: `0s`)
        13. Максимальное время ожидания инициализации соединения при запуске сервиса (по умолчанию: не указано, необязательно)
        14. Включать ли [пробу готовности](probes.md) для соединения с базой данных (по умолчанию: `false`)
        15. Дополнительные свойства соединения `JDBC`, передаваемые в `dataSourceProperties` `Hikari` (по умолчанию: `{}`)
        16. Включает логирование модуля (по умолчанию: `false`)
        17. Включает метрики модуля (по умолчанию: `true`)
        18. Настраивает [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
        19. Настраивает теги метрик (по умолчанию: `{}`)
        20. Включает трассировку модуля (по умолчанию: `true`)
        21. Настраивает атрибуты трассировки (по умолчанию: `{}`)

    === ":simple-yaml: `YAML`"

        ```yaml
        db:
          jdbcUrl: "jdbc:postgresql://localhost:5432/postgres" #(1)!
          username: "postgres" #(2)!
          password: "postgres" #(3)!
          schema: "public" #(4)!
          poolName: "kora" #(5)!
          maxPoolSize: 10 #(6)!
          minIdle: 0 #(7)!
          connectionTimeout: "10s" #(8)!
          validationTimeout: "5s" #(9)!
          idleTimeout: "10m" #(10)!
          maxLifetime: "15m" #(11)!
          leakDetectionThreshold: "0s" #(12)!
          initializationFailTimeout: "0s" #(13)!
          readinessProbe: false #(14)!
          dsProperties: #(15)!
            hostRecheckSeconds: "1"
          telemetry:
            logging:
              enabled: false #(16)!
            metrics:
              enabled: true #(17)!
              slo: [ 2, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(18)!
              tags: #(19)!
                key1: value1
                key2: value2
            tracing:
              enabled: true #(20)!
              attributes: #(21)!
                key1: value1
                key2: value2
        ```

        1.  `JDBC URL` для подключения к базе данных (`обязательный`, по умолчанию: не указано)
        2.  Имя пользователя для подключения (`обязательный`, по умолчанию: не указано)
        3.  Пароль пользователя для подключения (`обязательный`, по умолчанию: не указано)
        4.  Схема базы данных для подключения (по умолчанию: не указано, необязательно)
        5.  Имя пула соединений `Hikari` (`обязательный`, по умолчанию: не указано)
        6.  Максимальный размер пула соединений `Hikari` (по умолчанию: `10`)
        7.  Минимальное количество простаивающих готовых соединений в пуле `Hikari` (по умолчанию: `0`)
        8.  Максимальное время ожидания соединения из пула `Hikari` (по умолчанию: `10s`)
        9.  Максимальное время проверки соединения `Hikari` (по умолчанию: `5s`)
        10. Максимальное время простоя соединения `Hikari` (по умолчанию: `10m`)
        11. Максимальное время жизни соединения `Hikari` (по умолчанию: `15m`)
        12. Время, после которого занятое соединение считается возможной утечкой (по умолчанию: `0s`)
        13. Максимальное время ожидания инициализации соединения при запуске сервиса (по умолчанию: не указано, необязательно)
        14. Включать ли [пробу готовности](probes.md) для соединения с базой данных (по умолчанию: `false`)
        15. Дополнительные свойства соединения `JDBC`, передаваемые в `dataSourceProperties` `Hikari` (по умолчанию: `{}`)
        16. Включает логирование модуля (по умолчанию: `false`)
        17. Включает метрики модуля (по умолчанию: `true`)
        18. Настраивает [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
        19. Настраивает теги метрик (по умолчанию: `{}`)
        20. Включает трассировку модуля (по умолчанию: `true`)
        21. Настраивает атрибуты трассировки (по умолчанию: `{}`)


## Использование { #usage }

Репозиторий `JDBC` объявляется как интерфейс, помеченный аннотацией `@Repository`, и должен наследовать `JdbcRepository`.
Каждый метод, помеченный `@Query`, содержит обычный `SQL`-запрос. Параметры метода связываются по имени с помощью
синтаксиса `:parameter`, а к полям объекта можно обращаться как `:entity.field`.

Отображения описываются с помощью [общих аннотаций баз данных](database-common.md) и помечаются `@EntityJdbc`,
чтобы `Kora` сгенерировала отображатель на этапе компиляции (см. [Отображение](database-common.md#view)):

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
Общие правила для отображений, `@Table`, `@Column`, `@Id`, `@Embedded`, `@Batch` и макросов описаны в разделе
[Общие правила работы с базами данных](database-common.md#macros).

**Связывание параметров:** Kora выполняет типизированное внедрение аргументов в SQL-запрос на этапе компиляции.
Параметры запроса (например, `:id`, `:entity.name`) заменяются в сгенерированном коде на соответствующие вызовы `PreparedStatement`.
Например, для параметра `String name` будет сгенерировано что-то вроде `statement.setString(1, name)`, где индекс соответствует порядку параметра в запросе.
Это обеспечивает безопасность (защита от SQL-инъекций) и производительность (использование подготовленных запросов).

## Отображение { #mapping }

Вы можете переопределить отображение различных частей [отображения](database-common.md), результата запроса и параметров запроса.
Для этого `Kora` предоставляет несколько интерфейсов-отображателей.

### Результат { #result }

Используйте `JdbcResultSetMapper<T>`, когда нужно вручную отобразить весь `ResultSet`.
Такой отображатель получает весь результат запроса и сам решает, сколько строк прочитать и что вернуть.

===! ":fontawesome-brands-java: `Java`"

    ```java
    final class ResultMapper implements JdbcResultSetMapper<UUID> {

        @Override
        public UUID apply(ResultSet rs) throws SQLException {
            // mapping code
        }
    }

    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Mapping(ResultMapper.class)
        @Query("SELECT id FROM entities")
        List<UUID> getIds();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class ResultMapper : JdbcResultSetMapper<UUID> {

        @Throws(SQLException::class)
        override fun apply(rs: ResultSet): UUID {
            // mapping code
        }
    }

    @Repository
    interface EntityRepository : JdbcRepository {

        @Mapping(ResultMapper::class)
        @Query("SELECT id FROM entities")
        fun countIds(): List<UUID>
    }
    ```

`JdbcResultSetMapper` также предоставляет статические вспомогательные методы `singleResultSetMapper`, `listResultSetMapper`
и `optionalResultSetMapper`, которые создают отображатель всего `ResultSet` из `JdbcRowMapper<T>`.

#### Отображение { #view }

Используйте аннотацию `@EntityJdbc` для оптимального отображения.
Аннотация позволяет обработчику аннотаций сгенерировать все необходимые отображатели за **один раунд** аннотационной обработки.
Без этой аннотации отображатели генерируются по требованию, что может потребовать **множества раундов** обработки и значительно увеличить время компиляции.

Ожидается, что все вложенные отображения также используют эту аннотацию.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @EntityJdbc
    public record Entity(String id, String name) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @EntityJdbc
    data class Entity(val id: String, val name: String)
    ```

### Строка { #row }

Используйте `JdbcRowMapper<T>`, когда нужно вручную отобразить одну строку.
Учтите, что в `JDBC` индексы столбцов в `ResultSet` начинаются с `1`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    final class RowMapper implements JdbcRowMapper<UUID> {

        @Override
        public UUID apply(ResultSet rs) throws SQLException {
            return UUID.fromString(rs.getString(1));
        }
    }

    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Mapping(RowMapper.class)
        @Query("SELECT id FROM entities")
        List<UUID> findAll();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class RowMapper : JdbcRowMapper<UUID> {

        @Throws(SQLException::class)
        override fun apply(rs: ResultSet): UUID {
            return UUID.fromString(rs.getString(1))
        }
    }

    @Repository
    interface EntityRepository : JdbcRepository {

        @Mapping(RowMapper::class)
        @Query("SELECT id FROM entities")
        fun findAll(): List<UUID>
    }
    ```

### Столбец { #column }

Используйте `JdbcResultColumnMapper<T>`, когда нужно вручную отобразить значение одного столбца:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class ColumnMapper implements JdbcResultColumnMapper<UUID> {

        @Override
        public UUID apply(ResultSet row, int index) throws SQLException {
            return UUID.fromString(row.getString(index));
        }
    }

    @EntityJdbc
    @Table("entities")
    public record Entity(@Mapping(ColumnMapper.class) @Id UUID id, String name) { }

    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("SELECT id, name FROM entities")
        List<Entity> findAll();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class ColumnMapper : JdbcResultColumnMapper<UUID> {

        @Throws(SQLException::class)
        override fun apply(row: ResultSet, index: Int): UUID {
            return UUID.fromString(row.getString(index))
        }
    }

    @EntityJdbc
    @Table("entities")
    data class Entity(
        @Id @Mapping(ColumnMapper::class) val id: UUID,
        val name: String
    )

    @Repository
    interface EntityRepository : JdbcRepository {

        @Query("SELECT id, name FROM entities")
        fun findAll(): List<Entity>
    }
    ```

### Параметр { #parameter }

Используйте `JdbcParameterColumnMapper<T>`, когда нужно вручную отобразить значение параметра запроса:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class ParameterMapper implements JdbcParameterColumnMapper<UUID> {

        @Override
        public void set(PreparedStatement stmt, int index, @Nullable UUID value) throws SQLException {
            if (value != null) {
                stmt.setString(index, value.toString());
            }
        }
    }

    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("SELECT id, name FROM entities WHERE id = :id")
        List<Entity> findById(@Mapping(ParameterMapper.class) UUID id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class ParameterMapper : JdbcParameterColumnMapper<UUID?> {

        @Throws(SQLException::class)
        override fun set(stmt: PreparedStatement, index: Int, value: UUID?) {
            if (value != null) {
                stmt.setString(index, value.toString())
            }
        }
    }

    @Repository
    interface EntityRepository : JdbcRepository {

        @Query("SELECT id, name FROM entities WHERE id = :id")
        fun findById(@Mapping(ParameterMapper::class) id: UUID): List<Entity>
    }
    ```

### Поддерживаемые типы { #supported-types }

??? abstract "Список поддерживаемых типов для аргументов/возвращаемых значений из коробки"

    Эти типы выбраны потому, что поддерживаются большинством популярных баз данных.
    `Kora` предоставляет для них встроенные отображатели строк, столбцов и параметров.

    * void
    * boolean / Boolean
    * short / Short
    * int / Integer
    * long / Long
    * double / Double
    * float / Float
    * byte[]
    * String
    * BigDecimal
    * UUID
    * LocalDate
    * LocalTime
    * LocalDateTime
    * OffsetTime
    * OffsetDateTime

    Поля отображения без явного `@Mapping` нативно поддерживают `boolean` / `Boolean`, `short` / `Short`,
    `int` / `Integer`, `long` / `Long`, `double` / `Double`, `float` / `Float`, `byte[]`, `String`,
    `BigDecimal`, `LocalDate` и `LocalDateTime`.
    Для остальных типов используйте встроенные отображатели `JdbcResultColumnMapper<T>` / `JdbcParameterColumnMapper<T>` или объявите собственные отображатели.

## Выборка по списку { #select-by-list }

Иногда нужно выбрать строки по списку значений.
На уровне `JDBC` такие параметры должны подготавливаться драйвером отдельно, поскольку длина списка заранее неизвестна.
`Kora` старается выполнять отображения во время компиляции и не переписывает `SQL` во время выполнения, поэтому для таких параметров требуется собственный отображатель.

`Kora` не предоставляет отображение такого параметра из коробки, но его легко добавить самостоятельно.
В примере ниже показан `Postgres` через `JDBC Array`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    class ListOfStringJdbcParameterMapper implements JdbcParameterColumnMapper<List<String>> {

        @Override
        public void set(PreparedStatement stmt, int index, List<String> value) throws SQLException {
            String[] typedArray = value.toArray(String[]::new);
            Array sqlArray = stmt.getConnection().createArrayOf("VARCHAR", typedArray);
            stmt.setArray(index, sqlArray);
        }
    }

    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("SELECT id, name FROM entities WHERE id = ANY(:ids)")
        List<Entity> findAllByIds(@Mapping(ListOfStringJdbcParameterMapper.class) List<String> ids);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ListOfStringJdbcParameterMapper : JdbcParameterColumnMapper<List<String>> {

        @Throws(SQLException::class)
        override fun set(stmt: PreparedStatement, index: Int, value: List<String>) {
            val typedArray = value.toTypedArray()
            val sqlArray = stmt.connection.createArrayOf("VARCHAR", typedArray)
            stmt.setArray(index, sqlArray)
        }
    }

    @Repository
    interface EntityRepository : JdbcRepository {

        @Query("SELECT id, name FROM entities WHERE id = ANY(:ids)")
        fun findAllByIds(@Mapping(ListOfStringJdbcParameterMapper::class) ids: List<String>): List<Entity>
    }
    ```

## JSON / JSONB { #json }

Столбец `JSON` / `JSONB` можно отобразить на поле отображения, зарегистрировав обобщенные
`JdbcParameterColumnMapper<T>` и `JdbcResultColumnMapper<T>` как компоненты по умолчанию в `@Module`, помеченные `@Json`.
Эти отображатели связывают `JsonWriter<T>` / `JsonReader<T>` из модуля [JSON](json.md) со значением, специфичным для драйвера.
В примере для `Postgres` ниже значение сериализуется в `PGobject` типа `jsonb` при связывании параметра,
`null` обрабатывается через `setNull(index, Types.NULL)`, а столбец читается обратно как `String`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface JdbcJsonbMapperModule {

        @Json
        default <T> JdbcParameterColumnMapper<T> jdbcJsonParameterColumnMapper(JsonWriter<T> writer) {
            return (stmt, index, value) -> {
                if (value != null) {
                    PGobject jsonb = new PGobject();
                    jsonb.setType("jsonb");
                    jsonb.setValue(writer.toStringUnchecked(value));
                    stmt.setObject(index, jsonb);
                } else {
                    stmt.setNull(index, Types.NULL);
                }
            };
        }

        @Json
        default <T> JdbcResultColumnMapper<T> jdbcJsonResultColumnMapper(JsonReader<T> reader) {
            return (row, index) -> {
                var value = row.getString(index);
                if (value == null) {
                    return null;
                } else {
                    return reader.readUnchecked(value);
                }
            };
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface JdbcJsonbMapperModule {

        @Json
        fun <T> jdbcJsonParameterColumnMapper(writer: JsonWriter<T>): JdbcParameterColumnMapper<T> {
            return JdbcParameterColumnMapper { stmt, index, value ->
                if (value == null) {
                    stmt.setNull(index, Types.NULL)
                } else {
                    val jsonb = PGobject()
                    jsonb.type = "jsonb"
                    jsonb.value = writer.toStringUnchecked(value)
                    stmt.setObject(index, jsonb)
                }
            }
        }

        @Json
        fun <T> jdbcJsonResultColumnMapper(reader: JsonReader<T>): JdbcResultColumnMapper<T> {
            return JdbcResultColumnMapper { row, index ->
                val value = row.getString(index)
                if (value == null) null else reader.readUnchecked(value)
            }
        }
    }
    ```

Пометьте поле отображения аннотацией `@Json` (и `@Column`, если имя столбца отличается), где тип поля сам является `@Json`-типом.
В `INSERT` используется приведение `::jsonb`, чтобы `Postgres` принял сериализованную строку как `JSONB`;
`findById` читает ее обратно через тот же отображатель столбца, помеченный `@Json`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface JdbcJsonbRepository extends JdbcRepository {

        @EntityJdbc
        record Entity(UUID id,
                      @Column("value") @Json JsonbValue value) {

            @Json
            record JsonbValue(String name, String surname) {}
        }

        @Query("SELECT * FROM entities_jsonb WHERE id = :id")
        @Nullable
        Entity findById(UUID id);

        @Query("INSERT INTO entities_jsonb(id, value) VALUES (:entity.id, :entity.value::jsonb)")
        void insert(Entity entity);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface JdbcJsonbRepository : JdbcRepository {

        @EntityJdbc
        data class Entity(
            val id: UUID,
            @field:Column("value") @Json val value: JsonbValue
        ) {

            @Json
            data class JsonbValue(val name: String, val surname: String)
        }

        @Query("SELECT * FROM entities_jsonb WHERE id = :id")
        fun findById(id: UUID): Entity?

        @Query("INSERT INTO entities_jsonb(id, value) VALUES (:entity.id, :entity.value::jsonb)")
        fun insert(entity: Entity)
    }
    ```

Зависимость модуля [JSON](json.md) обязательна, чтобы `Kora` мог сгенерировать `JsonWriter` / `JsonReader` для типа поля,
а `@Module` с отображателями должен быть добавлен в [граф приложения](container.md).

## Сгенерированный идентификатор { #generated-identifier }

Если нужно вернуть первичные ключи, сгенерированные базой данных,
используйте аннотацию `@Id` над методом.
Этот подход также работает для `@Batch`-запросов.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @EntityJdbc
        public record Entity(Long id, String name) {}

        @Query("INSERT INTO entities(name) VALUES (:entity.name)")
        @Id
        long insert(Entity entity);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @EntityJdbc
        data class Entity(val id: Long, val name: String)

        @Query("INSERT INTO entities(name) VALUES (:entity.name)")
        @Id
        fun insert(entity: Entity): Long
    }
    ```

Сгенерированный ключ также можно вернуть как тип ключа отображения, а не как скалярное значение.
Когда идентификатор является составным ключом, описанным записью [`@Embedded`](database-common.md#embedded-fields),
метод `@Id` возвращает эту запись, а вставка `@Batch` возвращает `List` ключей — по одному на каждую вставленную строку:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @EntityJdbc
        record Entity(@Id @Embedded EntityId id, @Column("name") String name) {

            @EntityJdbc
            record EntityId(Long a, Long b) {}
        }

        @Query("INSERT INTO entities_composite(name) VALUES (:entity.name)")
        @Id
        Entity.EntityId insertGenerated(Entity entity);

        @Query("INSERT INTO entities_composite(name) VALUES (:entity.name)")
        @Id
        List<Entity.EntityId> insertGenerated(@Batch List<Entity> entities);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @EntityJdbc
        data class Entity(
            @field:Id @field:Embedded val id: EntityId?,
            @field:Column("name") val name: String
        ) {

            @EntityJdbc
            data class EntityId(val a: Long?, val b: Long?)
        }

        @Id
        @Query("INSERT INTO entities_composite(name) VALUES (:entity.name)")
        fun insertGenerated(entity: Entity): Entity.EntityId

        @Id
        @Query("INSERT INTO entities_composite(name) VALUES (:entity.name)")
        fun insertGenerated(@Batch entities: List<Entity>): List<Entity.EntityId>
    }
    ```

## Ручной запрос с телеметрией { #query }

Если запрос сложно выразить одной статической `@Query`, вы можете создать обычный метод с реализацией и построить `SQL` вручную.
Используйте `JdbcConnectionFactory#query` для выполнения такого запроса.
Этот метод создает `PreparedStatement`, выполняет запрос через телеметрию Kora и использует то же соединение, что и другие методы репозитория.
Если `query` вызывается внутри активной транзакции `inTx`, запрос выполняется на текущем транзакционном соединении.

`QueryContext` содержит идентификатор запроса и итоговый `SQL`.
Идентификатор запроса передается в телеметрию, поэтому удобно использовать стабильное имя, например `Repository.method`.
Значения должны передаваться через параметры `PreparedStatement`, а не конкатенироваться напрямую в строку запроса.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        default List<Entity> findByFilter(@Nullable String name, boolean onlyActive) {
            var sql = new StringBuilder("SELECT id, name FROM entities WHERE 1 = 1");
            var params = new ArrayList<String>();

            if (name != null) {
                sql.append(" AND name = ?");
                params.add(name);
            }
            if (onlyActive) {
                sql.append(" AND active = true");
            }

            var queryContext = new QueryContext("EntityRepository.findByFilter", sql.toString());
            return getJdbcConnectionFactory().query(queryContext, statement -> {
                for (int i = 0; i < params.size(); i++) {
                    statement.setString(i + 1, params.get(i));
                }
                try (var resultSet = statement.executeQuery()) {
                    var result = new ArrayList<Entity>();
                    while (resultSet.next()) {
                        result.add(new Entity(resultSet.getLong("id"), resultSet.getString("name")));
                    }
                    return result;
                }
            });
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        fun findByFilter(name: String?, onlyActive: Boolean): List<Entity> {
            val sql = StringBuilder("SELECT id, name FROM entities WHERE 1 = 1")
            val params = mutableListOf<String>()

            if (name != null) {
                sql.append(" AND name = ?")
                params += name
            }
            if (onlyActive) {
                sql.append(" AND active = true")
            }

            val queryContext = QueryContext("EntityRepository.findByFilter", sql.toString())
            return jdbcConnectionFactory.query(queryContext) { statement ->
                params.forEachIndexed { index, value ->
                    statement.setString(index + 1, value)
                }
                statement.executeQuery().use { resultSet ->
                    val result = mutableListOf<Entity>()
                    while (resultSet.next()) {
                        result += Entity(resultSet.getLong("id"), resultSet.getString("name"))
                    }
                    result
                }
            }
        }
    }
    ```

## Транзакции { #transaction }

Для выполнения блокирующих запросов `Kora` предоставляет интерфейс `JdbcConnectionFactory` через контракт `JdbcRepository`.
Все методы репозитория, вызванные внутри лямбды транзакции, выполняются в этой же транзакции.

Используйте `inTx` для транзакционного выполнения запросов.
Если в текущем потоке уже есть активная транзакция, вложенный вызов `inTx` использует то же соединение и не открывает
новую транзакцию.

Транзакционную последовательность операций можно оставить внутри самого репозитория в виде обычного метода с реализацией.
Это удобно, когда несколько методов `@Query` или сложный ручной `SQL`-запрос должны находиться рядом с остальными запросами репозитория,
без переноса технической работы с базой данных в слой сервиса.
Внутри такого метода можно использовать как методы репозитория `@Query`, так и `JdbcConnectionFactory#query` для ручного запроса с телеметрией.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        UpdateCount insert(Entity entity);

        @Query("UPDATE entities SET name = :name WHERE id = :id")
        UpdateCount updateName(long id, String name);

        public List<Entity> saveAll(Entity one, Entity two) {
            return getJdbcConnectionFactory().inTx(() -> {
                insert(one); //(1)!
                updateName(two.id(), two.name()); //(2)!
                return List.of(one, two);
            });
        }
    }
    ```

    1. Выполняется в рамках транзакции или откатывается, если вся лямбда выбрасывает исключение
    2. Выполняется в рамках транзакции или откатывается, если вся лямбда выбрасывает исключение

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        fun insert(entity: Entity): UpdateCount

        @Query("UPDATE entities SET name = :name WHERE id = :id")
        fun updateName(id: Long, name: String): UpdateCount

        fun saveAll(one: Entity, two: Entity): List<Entity> {
            return jdbcConnectionFactory.inTx<List<Entity>> {
                insert(one) //(1)!
                updateName(two.id, two.name) //(2)!
                listOf(one, two)
            }
        }
    }
    ```

    1. Выполняется в рамках транзакции или откатывается, если вся лямбда выбрасывает исключение
    2. Выполняется в рамках транзакции или откатывается, если вся лямбда выбрасывает исключение

Транзакция считается успешно зафиксированной после завершения метода, если он не выбросил исключение.
Если метод выбрасывает исключение, все изменения в базе данных, сделанные в рамках транзакции, не применяются.

Уровень изоляции транзакции берется из конфигурации `dsProperties` пула `Hikari`,
либо вы можете изменить его вручную через `java.sql.Connection` перед выполнением запросов.

```java
connection.setTransactionIsolation(Connection.TRANSACTION_READ_COMMITTED);
```

### Ручное управление соединением { #connection }

Если для запроса нужна более сложная логика или запросы вне репозитория, вы можете использовать `java.sql.Connection`.
Метод `withConnection` выполняет код с соединением, но сам по себе не открывает транзакцию.

`withConnection` работает следующим образом:

- если текущий `Context` уже содержит `ConnectionContext`, метод передает текущее соединение в лямбду;
- если текущий `Context` не содержит соединения, метод берет новое соединение из `DataSource`, сохраняет его в `ConnectionContext` на время выполнения лямбды и закрывает после завершения;
- вложенные вызовы `withConnection`, `JdbcConnectionFactory#query` и методов репозитория внутри этой лямбды используют то же текущее соединение;
- если исключение `JDBC` является `SQLException`, оно оборачивается в `RuntimeSqlException`.

!!! note

    Ручные вызовы `query`, `withConnection` и `inTx` представляют сбой `JDBC` как непроверяемое исключение `RuntimeSqlException`,
    которое оборачивает исходное `java.sql.SQLException`. Перехватывайте `RuntimeSqlException` (а не `SQLException`) в месте вызова
    и используйте `getCause()`, чтобы добраться до исходного `SQLException`.

Метод `inTx` открывает транзакцию и построен поверх `withConnection`.
Если текущее соединение уже находится в активной транзакции, то есть `autoCommit = false`, вложенный `inTx` использует ту же транзакцию.
Если активной транзакции нет, `inTx` отключает `autoCommit`, выполняет лямбду, а затем вызывает `commit` при успехе или `rollback` при исключении.
После завершения транзакции выполняются зарегистрированные обратные вызовы `addPostCommitAction` или `addPostRollbackAction`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final EntityRepository repository;

        public SomeService(EntityRepository repository) {
            this.repository = repository;
        }

        public List<Entity> saveAll(Entity one, Entity two) {
            return repository.getJdbcConnectionFactory().inTx(connection -> {
                // do some work
                return List.of(one, two);
            });
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(private val repository: EntityRepository) {

        fun saveAll(one: Entity, two: Entity): List<Entity> {
            return repository.jdbcConnectionFactory.inTx(SqlFunction1 { connection: Connection ->
                // do some work
                listOf(one, two)
            })
        }
    }
    ```

### Действия после фиксации { #post-commit-actions }

Если нужно выполнить действия после успешной фиксации транзакции, добавьте их с помощью `addPostCommitAction`.
Действие выполняется после `commit` и только если транзакция завершилась успешно.
Такие действия можно добавлять только внутри активной транзакции.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final EntityRepository repository;

        public SomeService(EntityRepository repository) {
            this.repository = repository;
        }

        public List<Entity> saveAll(Entity one, Entity two) {
            return repository.getJdbcConnectionFactory().inTx(connection -> {
                var ccc = repository.getJdbcConnectionFactory().currentConnectionContext();
                ccc.addPostCommitAction(conn -> {
                    // do some work
                });

                // do some work
                return List.of(one, two);
            });
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(private val repository: EntityRepository) {

        fun saveAll(one: Entity, two: Entity): List<Entity> {
            return repository.jdbcConnectionFactory.inTx(SqlFunction1 { connection: Connection ->
                val ccc = repository.jdbcConnectionFactory.currentConnectionContext()!!
                ccc.addPostCommitAction { conn ->
                    // do some work
                }

                // do some work
                listOf(one, two)
            })
        }
    }
    ```

### Действия после отката { #post-rollback-actions }

Если нужно выполнить действия после отката транзакции, добавьте их с помощью `addPostRollbackAction`.
Действие получает соединение и исключение, вызвавшее откат транзакции.
Такие действия можно добавлять только внутри активной транзакции.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final EntityRepository repository;

        public SomeService(EntityRepository repository) {
            this.repository = repository;
        }

        public List<Entity> saveAll(Entity one, Entity two) {
            return repository.getJdbcConnectionFactory().inTx(connection -> {
                var ccc = repository.getJdbcConnectionFactory().currentConnectionContext();
                ccc.addPostRollbackAction((conn, e) -> {
                    // do some work
                });

                // do some work
                return List.of(one, two);
            });
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(private val repository: EntityRepository) {

        fun saveAll(one: Entity, two: Entity): List<Entity> {
            return repository.jdbcConnectionFactory.inTx(SqlFunction1 { connection: Connection ->
                val ccc = repository.jdbcConnectionFactory.currentConnectionContext()!!
                ccc.addPostRollbackAction { conn, e ->
                    // do some work
                }

                // do some work
                listOf(one, two)
            })
        }
    }
    ```

## Сигнатуры { #signatures }

Доступные из коробки сигнатуры методов репозитория:

===! ":fontawesome-brands-java: `Java`"

    `T` означает тип возвращаемого значения, либо `List<T>`, либо `Void`, либо `UpdateCount`.
    `CompletionStage<T>`, `CompletableFuture<T>` и `Mono<T>` требуют компонент `Executor`.

    - `T myMethod()`
    - `@Nullable T myMethod()`
    - `Optional<T> myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletionStage.html) (требует `Executor`)
    - `CompletableFuture<T> myMethod()` [CompletableFuture](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletableFuture.html) (требует `Executor`)
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (требует `Executor` и [зависимость](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

=== ":simple-kotlin: `Kotlin`"

    `T` означает тип возвращаемого значения, либо `T?`, либо `List<T>`, либо `Unit`, либо `UpdateCount`.
    Методы `suspend` требуют компонент `Executor`.

    - `myMethod(): T`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (требует `Executor` и [зависимость](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) как `implementation`)

Для асинхронных методов вы можете указать отдельный тег `Executor` через параметр `executorTag` в `@Repository`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class BlockingJdbcExecutorTag {}

    @Repository(executorTag = @Tag(BlockingJdbcExecutorTag.class))
    public interface EntityRepository extends JdbcRepository {

        @Query("SELECT id, name FROM entities")
        CompletionStage<List<Entity>> findAll();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class BlockingJdbcExecutorTag

    @Repository(executorTag = Tag(BlockingJdbcExecutorTag::class))
    interface EntityRepository : JdbcRepository {

        @Query("SELECT id, name FROM entities")
        suspend fun findAll(): List<Entity>
    }
    ```

## Телеметрия { #telemetry }

Логирование, метрики и трассировка настраиваются через блок `telemetry` в [конфигурации](#configuration) и описаны в разделе [Справочник метрик](metrics.md#database).
Чтобы переопределить телеметрию полностью, можно предоставить собственные SPI-фабрики, подробнее в [Общей документации по Базам данных](database-common.md#telemetry).
