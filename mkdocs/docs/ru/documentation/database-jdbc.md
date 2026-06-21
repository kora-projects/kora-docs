---
description: "Explains Kora JDBC repositories, JDBC configuration, result and parameter mapping, generated identifiers, transactions, and repository method signatures. Use when working with @Repository, @Query, @EntityJdbc, @Table, @Id, @Column, @Batch, JdbcDatabaseModule."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora JDBC repositories, JDBC configuration, result and parameter mapping, generated identifiers, transactions, and repository method signatures; key triggers include @Repository, @Query, @EntityJdbc, @Table, @Id, @Column, @Batch, JdbcDatabaseModule, JdbcConnectionFactory, JdbcRepository."
---

Модуль предоставляет реализацию репозиториев на основе [JDBC](https://proselyte.net/tutorials/jdbc/introduction/) для
работы с реляционными базами данных и использует [Hikari](https://github.com/brettwooldridge/HikariCP) для управления
пулом соединений.
Вы описываете интерфейс репозитория и `SQL`-запросы через `@Repository` и `@Query`, а `Kora` генерирует реализацию,
которая получает соединение из пула, подставляет параметры, читает результат и участвует в транзакциях.

Общие правила для сущностей, `@Repository`, `@Query`, `@Batch`, `UpdateCount`, макросов, ручных запросов и других
механизмов репозиториев описаны в разделе [Общие правила баз данных](database-common.md).

Если нужен пошаговый разбор перед справочным описанием, смотрите [База данных JDBC](../guides/database-jdbc.md) и [База данных JDBC продвинутая](../guides/database-jdbc-advanced.md).

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

Также **требуется предоставить** реализацию драйвера базы данных как зависимость.

## Конфигурация { #configuration }

Пример полной конфигурации, описанной в классе `JdbcDatabaseConfig` (указаны примеры значений или значения по умолчанию):

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

    1.  `JDBC URL` подключения к базе данных (`обязательная`, по умолчанию не указано)
    2.  Имя пользователя для подключения (`обязательная`, по умолчанию не указано)
    3.  Пароль пользователя для подключения (`обязательная`, по умолчанию не указано)
    4.  Схема базы данных для подключения (по умолчанию не указано, необязательно)
    5.  Имя пула соединений `Hikari` (`обязательная`, по умолчанию не указано)
    6.  Максимальный размер пула соединений `Hikari` (по умолчанию: `10`)
    7.  Минимальный размер пула готовых соединений `Hikari` в режиме ожидания (по умолчанию: `0`)
    8.  Максимальное время ожидания получения соединения из пула `Hikari` (по умолчанию: `10s`)
    9.  Максимальное время проверки соединения в `Hikari` (по умолчанию: `5s`)
    10. Максимальное время простоя соединения в `Hikari` (по умолчанию: `10m`)
    11. Максимальное время жизни соединения в `Hikari` (по умолчанию: `15m`)
    12. Время, после которого занятое соединение будет считаться возможной утечкой (по умолчанию: `0s`)
    13. Максимальное время ожидания инициализации соединения при старте сервиса (по умолчанию не указано, необязательно)
    14. Включить ли [пробу готовности](probes.md#readiness) для соединения с базой данных (по умолчанию: `false`)
    15. Дополнительные свойства `JDBC`-соединения, которые будут переданы в `dataSourceProperties` `Hikari` (по умолчанию: `{}`)
    16. Включает логирование модуля (по умолчанию: `false`)
    17. Включает метрики модуля (по умолчанию: `true`)
    18. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    19. Настройка тегов для метрик (по умолчанию: `{}`)
    20. Включает трассировку модуля (по умолчанию: `true`)
    21. Настройка атрибутов для трассировки (по умолчанию: `{}`)

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

    1.  `JDBC URL` подключения к базе данных (`обязательная`, по умолчанию не указано)
    2.  Имя пользователя для подключения (`обязательная`, по умолчанию не указано)
    3.  Пароль пользователя для подключения (`обязательная`, по умолчанию не указано)
    4.  Схема базы данных для подключения (по умолчанию не указано, необязательно)
    5.  Имя пула соединений `Hikari` (`обязательная`, по умолчанию не указано)
    6.  Максимальный размер пула соединений `Hikari` (по умолчанию: `10`)
    7.  Минимальный размер пула готовых соединений `Hikari` в режиме ожидания (по умолчанию: `0`)
    8.  Максимальное время ожидания получения соединения из пула `Hikari` (по умолчанию: `10s`)
    9.  Максимальное время проверки соединения в `Hikari` (по умолчанию: `5s`)
    10. Максимальное время простоя соединения в `Hikari` (по умолчанию: `10m`)
    11. Максимальное время жизни соединения в `Hikari` (по умолчанию: `15m`)
    12. Время, после которого занятое соединение будет считаться возможной утечкой (по умолчанию: `0s`)
    13. Максимальное время ожидания инициализации соединения при старте сервиса (по умолчанию не указано, необязательно)
    14. Включить ли [пробу готовности](probes.md#readiness) для соединения с базой данных (по умолчанию: `false`)
    15. Дополнительные свойства `JDBC`-соединения, которые будут переданы в `dataSourceProperties` `Hikari` (по умолчанию: `{}`)
    16. Включает логирование модуля (по умолчанию: `false`)
    17. Включает метрики модуля (по умолчанию: `true`)
    18. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    19. Настройка тегов для метрик (по умолчанию: `{}`)
    20. Включает трассировку модуля (по умолчанию: `true`)
    21. Настройка атрибутов для трассировки (по умолчанию: `{}`)

## Использование { #usage }

`JDBC`-репозиторий объявляется интерфейсом с аннотацией `@Repository` и должен наследовать `JdbcRepository`.
Каждый метод с `@Query` содержит обычный `SQL`-запрос. Параметры метода подставляются в запрос по имени через
синтаксис `:parameter`, а поля объекта можно указывать через `:entity.field`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("SELECT id, name FROM entities WHERE id = :id")
        @Nullable
        Entity findById(long id);

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        UpdateCount insert(Entity entity);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository {

        @Query("SELECT id, name FROM entities WHERE id = :id")
        fun findById(id: Long): Entity?

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        fun insert(entity: Entity): UpdateCount
    }
    ```

`SQL` остается под контролем разработчика: можно использовать специфичные возможности конкретной базы данных, а `Kora`
занимается только безопасной подстановкой параметров, выполнением запроса и преобразованием результата.
Общие правила сущностей, `@Table`, `@Column`, `@Id`, `@Embedded`, `@Batch` и макросов описаны в разделе
[Общие правила баз данных](database-common.md).

## Преобразование { #mapping }

Можно переопределять преобразование разных частей [сущности](database-common.md), результата и параметров запроса.
Для этого `Kora` предоставляет несколько интерфейсов преобразователей.

### Результат { #result }

Если требуется преобразовать весь `ResultSet` вручную, используйте `JdbcResultSetMapper<T>`.
Такой преобразователь получает весь результат запроса и сам решает, сколько строк прочитать и что вернуть.

===! ":fontawesome-brands-java: `Java`"

    ```java
    final class ResultMapper implements JdbcResultSetMapper<UUID> {

        @Override
        public UUID apply(ResultSet rs) throws SQLException {
            // код преобразования
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
            // код преобразования
        }
    }

    @Repository
    interface EntityRepository : JdbcRepository {

        @Mapping(ResultMapper::class)
        @Query("SELECT id FROM entities")
        fun countIds(): List<UUID>
    }
    ```

#### Сущность { #entity }

Для оптимального преобразования сущности используйте аннотацию `@EntityJdbc`.
Обработчик аннотаций заранее создаст преобразователь результата для такого типа.

Для всех вложенных сущностей также предполагается использовать эту аннотацию.

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

Если требуется преобразовать одну строку вручную, используйте `JdbcRowMapper<T>`.
Имейте в виду, что в `JDBC` порядок колонок в `ResultSet` начинается с `1`:

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

### Колонка { #column }

Если требуется преобразовать значение отдельной колонки вручную, используйте `JdbcResultColumnMapper<T>`:

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

Если требуется преобразовать значение параметра запроса вручную, используйте `JdbcParameterColumnMapper<T>`:

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

    Такие типы выбраны так как поддерживаются большинством популярных баз данных.
    Для них `Kora` предоставляет встроенные преобразователи строк, колонок и параметров.

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

    Для полей сущностей без явного `@Mapping` нативно поддерживаются `boolean` / `Boolean`, `short` / `Short`,
    `int` / `Integer`, `long` / `Long`, `double` / `Double`, `float` / `Float`, `byte[]`, `String`,
    `BigDecimal`, `LocalDate` и `LocalDateTime`.
    Для остальных типов можно использовать встроенные преобразователи `JdbcResultColumnMapper<T>` /
    `JdbcParameterColumnMapper<T>` или объявить собственные преобразователи.

## Выборка по списку { #select-by-list }

Иногда требуется выборка по списку значений из базы данных.
На уровне `JDBC` такие параметры должны быть отдельно подготовлены драйвером, потому что длина списка заранее неизвестна.
`Kora` старается делать преобразования во время компиляции и не переписывать `SQL` во время работы, поэтому для таких
параметров нужно добавить самостоятельный преобразователь.

Из коробки `Kora` не предоставляет преобразование таких параметров, но его легко добавить самостоятельно.
Ниже показан пример для `Postgres` через `JDBC Array`:

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

## Созданный идентификатор { #generated-identifier }

Если необходимо получить в качестве результата первичные ключи, созданные базой данных,
используйте аннотацию `@Id` над методом.
Такой подход работает и для `@Batch` запросов.

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

## Ручной запрос с телеметрией { #query }

Если запрос сложно выразить одним статическим `@Query`, можно сделать обычный метод с реализацией и самостоятельно собрать `SQL`.
Для выполнения такого запроса используйте `JdbcConnectionFactory#query`.
Этот метод создает `PreparedStatement`, проводит запрос через телеметрию `Kora` и использует то же соединение, что и остальные методы репозитория.
Если `query` вызывается внутри активной транзакции `inTx`, запрос будет выполнен на текущем транзакционном соединении.

В `QueryContext` указывается идентификатор запроса и итоговый `SQL`.
Идентификатор запроса попадает в телеметрию, поэтому для него удобно использовать стабильное имя вида `Repository.method`.
Значения нужно передавать через параметры `PreparedStatement`, а не подставлять в строку запроса напрямую.

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

Для выполнения блокирующих запросов в `Kora` есть интерфейс `JdbcConnectionFactory`,
который предоставляется в методе в рамках контракта `JdbcRepository`.
Все методы репозитория, вызванные в рамках лямбды транзакции, будут выполнены в этой самой транзакции.

Для того чтобы выполнять запросы транзакционно, можно использовать метод `inTx`.
Если на текущем потоке уже есть активная транзакция, вложенный вызов `inTx` использует то же соединение и не открывает
новую транзакцию.

Транзакционную последовательность операций можно оставлять внутри самого репозитория с помощью обычного метода с реализацией.
Такой подход удобен, когда нужно инкапсулировать несколько `@Query`-методов или сложный самостоятельный `SQL`-запрос рядом с остальными запросами репозитория,
не вынося техническую работу с базой данных в сервисный слой.
Внутри такого метода можно использовать и `@Query`-методы репозитория, и `JdbcConnectionFactory#query` для ручного запроса с телеметрией.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        UpdateCount insert(Entity entity);

        @Query("UPDATE entities SET name = :name WHERE id = :id")
        UpdateCount updateName(long id, String name);

        default List<Entity> saveAll(Entity one, Entity two) {
            return getJdbcConnectionFactory().inTx(() -> {
                insert(one); //(1)!
                updateName(two.id(), two.name()); //(2)!
                return List.of(one, two);
            });
        }
    }
    ```

    1. Будет выполнено в рамках транзакции или откатится, если вся лямбда выбросит исключение
    2. Будет выполнено в рамках транзакции или откатится, если вся лямбда выбросит исключение

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

    1. Будет выполнено в рамках транзакции или откатится, если вся лямбда выбросит исключение
    2. Будет выполнено в рамках транзакции или откатится, если вся лямбда выбросит исключение

Транзакция считается успешно зафиксированной после выполнения метода, если метод не выбросил исключение.
Если метод выбросил исключение, все изменения в базе данных в рамках транзакции не будут применены.

Уровень изоляции транзакции берется из конфигурации `dsProperties` пула `Hikari`,
либо можно самостоятельно поменять его через `java.sql.Connection` перед выполнением запросов.

```java
connection.setTransactionIsolation(Connection.TRANSACTION_READ_COMMITTED);
```

### Ручное управление соединением { #connection }

Если для запроса нужна более сложная логика или запросы вне репозитория, можно использовать `java.sql.Connection`.
Метод `withConnection` выполняет код с соединением, но сам по себе не открывает транзакцию.

`withConnection` работает так:

- если в текущем `Context` уже есть `ConnectionContext`, метод передает в лямбду текущее соединение;
- если соединения в текущем `Context` нет, метод берет новое соединение из `DataSource`, кладет его в `ConnectionContext` на время выполнения лямбды и закрывает после завершения;
- повторные вызовы `withConnection`, `JdbcConnectionFactory#query` и методы репозитория внутри этой лямбды используют то же текущее соединение;
- если исключение из `JDBC` является `SQLException`, оно оборачивается в `RuntimeSqlException`.

Транзакцию открывает метод `inTx`, который построен поверх `withConnection`.
Если текущее соединение уже находится в активной транзакции, то есть у него `autoCommit = false`, вложенный `inTx` использует эту же транзакцию.
Если активной транзакции нет, `inTx` отключает `autoCommit`, выполняет лямбду, затем делает `commit` при успешном завершении или `rollback` при исключении.
После завершения транзакции выполняются зарегистрированные действия `addPostCommitAction` или `addPostRollbackAction`.

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

Если требуется выполнить действия после успешной фиксации транзакции, можно добавить их с помощью `addPostCommitAction`.
Действие выполняется после `commit` и только если транзакция завершилась успешно.
Добавлять такие действия можно только внутри активной транзакции.

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

Если требуется выполнить действия после отката транзакции, можно добавить их с помощью `addPostRollbackAction`.
Действие получает соединение и исключение, из-за которого транзакция была отменена.
Добавлять такие действия можно только внутри активной транзакции.

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

Доступные сигнатуры для методов репозитория из коробки:

===! ":fontawesome-brands-java: `Java`"

    Под `T` подразумевается тип возвращаемого значения, либо `List<T>`, либо `Void`, либо `UpdateCount`.
    Для `CompletionStage<T>`, `CompletableFuture<T>` и `Mono<T>` нужно предоставить компонент `Executor`.

    - `T myMethod()`
    - `@Nullable T myMethod()`
    - `Optional<T> myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletionStage.html) (надо предоставить `Executor`)
    - `CompletableFuture<T> myMethod()` [CompletableFuture](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletableFuture.html) (надо предоставить `Executor`)
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (надо предоставить `Executor` и подключить [зависимость](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

=== ":simple-kotlin: `Kotlin`"

    Под `T` подразумевается тип возвращаемого значения, либо `T?`, либо `List<T>`, либо `Unit`, либо `UpdateCount`.
    Для `suspend`-методов нужно предоставить компонент `Executor`.

    - `myMethod(): T`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (надо предоставить `Executor` и подключить [зависимость](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) как `implementation`)

Для асинхронных методов можно указать отдельный тег `Executor` через параметр `executorTag` в `@Repository`.

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
