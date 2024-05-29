Модуль предоставляет реализацию репозиториев на основе [JDBC](https://proselyte.net/tutorials/jdbc/introduction/) протокола работы с базами данных 
и с использованием [Hikari](https://github.com/brettwooldridge/HikariCP) для управления набором соединений.

## Подключение

=== ":fontawesome-brands-java: `Java`"

    Зависимость `build.gradle`:
    ```groovy
    annotationProcessor "ru.tinkoff.kora:annotation-processors"
    implementation "ru.tinkoff.kora:database-jdbc"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends JdbcDatabaseModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Зависимость `build.gradle.kts`:
    ```groovy
    ksp("ru.tinkoff.kora:symbol-processors")
    implementation("ru.tinkoff.kora:database-jdbc")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : JdbcDatabaseModule
    ```

Также **требуется предоставить** реализацию драйвера базы данных как зависимость.

## Конфигурация

Параметры, описанные в классе `JdbcDatabaseConfig`:

===! ":material-code-json: `Hocon`"

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
            }
            telemetry {
                enabled = true //(19)!
            }
        }
    }
    ```

    1.  JDBC URL подключения к базе данных **(обязательный)**
    2.  Имя пользователя для подключения **(обязательный)**
    3.  Пароль пользователя для подключения **(обязательный)**
    4.  Схема базы данных для подключения
    5.  Имя набора соединений к базе данных в Hikari **(обязательный)**
    6.  Максимальный размер набора соединений к базе данных в Hikari
    7.  Минимальный размер набора готовых соединений к базе данных в Hikari в режиме ожидания
    8.  Максимальное время на установку соединения в Hikari
    9.  Максимальное время на проверку соединения в Hikari
    10.  Максимальное время на простой соединения в Hikari
    11.  Максимальное время жизни соединения в Hikari
    12.  Максимальное время соединение может отстуствовать в Hikari до того как будет считаться утечкой (отключено по умолчанию)
    13.  Максимальное время ожидания инициализации соединения при старте сервиса (отключено по умолчанию)
    14.  Включить ли [пробу готовности](probes.md#_2) для соединения базы данных
    15.  Дополнительные атрибуты JDBC соединения `dataSourceProperties` (ниже пример `hostRecheckSeconds` параметры)
    16.  Включает логгирование модуля (по умолчанию `false`)
    17.  Включает метрики модуля (по умолчанию `true`)
    18.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    19.  Включает трассировку модуля (по умолчанию `true`)

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
      initializationFailTimeout: "0s" //(13)!
      readinessProbe: false //(14)!
      dsProperties: #(15)!
        hostRecheckSeconds: "1"  
      telemetry:
        logging:
          enabled: true #(16)!
        metrics:
          enabled: true #(17)!
          slo: [ 2, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(18)!
        telemetry:
          enabled: true #(19)!
    }
    ```

    1.  JDBC URL подключения к базе данных **(обязательный)**
    2.  Имя пользователя для подключения **(обязательный)**
    3.  Пароль пользователя для подключения **(обязательный)**
    4.  Схема базы данных для подключения
    5.  Имя набора соединений к базе данных в Hikari **(обязательный)**
    6.  Максимальный размер набора соединений к базе данных в Hikari
    7.  Минимальный размер набора готовых соединений к базе данных в Hikari в режиме ожидания
    8.  Максимальное время на установку соединения в Hikari
    9.  Максимальное время на проверку соединения в Hikari
    10.  Максимальное время на простой соединения в Hikari
    11.  Максимальное время жизни соединения в Hikari
    12.  Максимальное время соединение может отстуствовать в Hikari до того как будет считаться утечкой (отключено по умолчанию)
    13.  Максимальное время ожидания инициализации соединения при старте сервиса (отключено по умолчанию)
    14.  Включить ли [пробу готовности](probes.md#_2) для соединения базы данных
    15.  Дополнительные атрибуты JDBC соединения `dataSourceProperties` (ниже пример `hostRecheckSeconds` параметры)
    16.  Включает логгирование модуля (по умолчанию `false`)
    17.  Включает метрики модуля (по умолчанию `true`)
    18.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    19.  Включает трассировку модуля (по умолчанию `true`)

## Использование

=== ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends JdbcRepository { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : JdbcRepository
    ```

## Конвертация

Возможно переопределять преобразование различных частей [сущности](database-common.md) и параметров запроса, для этого Kora предоставляет специальные интерфейсы. 

### Результат

Если требуется преобразовать результат в ручную, предлагается использовать `JdbcResultSetMapper`:

=== ":fontawesome-brands-java: `Java`"

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
    class ResultMapper : JdbcResultSetMapper<Long> {

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

### Строка

Если требуется преобразовать строку в ручную, предлагается использовать `JdbcRowMapper`:

=== ":fontawesome-brands-java: `Java`"

    ```java
    final class RowMapper implements JdbcRowMapper<UUID> {

        @Override
        public UUID apply(ResultSet rs) throws SQLException {
            return UUID.fromString(rs.getString(0));
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
            return UUID.fromString(rs.getString(0))
        }
    }

    @Repository
    interface EntityRepository : JdbcRepository {

        @Mapping(RowMapper::class)
        @Query("SELECT id FROM entities")
        fun findAll(): List<UUID>
    }
    ```

### Колонка

Если требуется преобразовать значение колонки в ручную, предлагается использовать `JdbcResultColumnMapper`:

=== ":fontawesome-brands-java: `Java`"

    ```java
    public final class ColumnMapper implements JdbcResultColumnMapper<UUID> {

        @Override
        public UUID apply(ResultSet row, int index) throws SQLException {
            return UUID.fromString(row.getString(index));
        }
    }

    @Table("entities")
    public record Entity(@Mapping(ColumnMapper.class) @Id UUID id, String name) { }

    @Repository
    public interface EntityRepository extends JdbcRepository {

        @Query("SELECT * FROM entities")
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

    @Table("entities")
    data class Entity(
        @Id @Mapping(ColumnMapper::class) val id: UUID,
        val name: String
    )

    @Repository
    interface EntityRepository : JdbcRepository {

        @Query("SELECT * FROM entities")
        fun findAll(): List<Entity>
    }
    ```

### Параметр

Если требуется преобразовать значение параметра запроса в ручную, предлагается использовать `JdbcParameterColumnMapper`:

=== ":fontawesome-brands-java: `Java`"

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

        @Query("SELECT * FROM entities WHERE id = :id")
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

        @Query("SELECT * FROM entities WHERE id = :id")
        fun findById(@Mapping(ParameterMapper::class) id: UUID): List<Entity>
    }
    ```

## Выборка по списку

На данный момент точно известно, что поддерживает запрос по списку удобно без костылей и ручного управления такие базы данных как Postgres/Oracle.
Из коробки Kora не предоставляет конвертацию таких параметров, но его легко добавить самостоятельно, ниже показан пример для `Postgres`:

=== ":fontawesome-brands-java: `Java`"

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

        @Query("SELECT * FROM entities WHERE id = ANY(:ids)")
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

        @Query("SELECT * FROM entities WHERE id = ANY(:ids)")
        fun findAllByIds(@Mapping(ListOfStringJdbcParameterMapper::class) ids: List<String>): List<Entity>
    }
    ```

## Транзакции

Для выполнения блокирующих запросов в Kora есть интерфейс `JdbcConnectionFactory`, 
который предоставляется в методе в рамках контракта `JdbcRepository`.
Все методы репозитория вызванные в рамках лямбды транзакции будут выполнены в этой самой транзакции.

Для того чтобы выполнять запросы транзакционно, можно использовать контракт `inTx`:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final EntityRepository repository;

        public SomeService(EntityRepository repository) {
            this.repository = repository;
        }

        public List<Entity> saveAll(Entity one, Entity two) {
            return repository.getJdbcConnectionFactory().inTx(() -> {
                repository.insert(one); //(1)!
                // do some work
                repository.insert(two); //(2)!
                return List.of(one, two);
            });
        }
    }
    ```

    1. Будет выполнено в рамках транзакции либо откатится если вся лямбра выкинет исключение
    2. Будет выполнено в рамках транзакции либо откатится если вся лямбра выкинет исключение

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(private val repository: EntityRepository) {

        fun saveAll(one: List<Entity>, two: List<Entity>): List<Entity> {
            return repository.jdbcConnectionFactory.inTx(SqlFunction1 {
                repository.insert(one) //(1)!
                // do some work
                repository.insert(two) //(2)!
                one + two
            })
        }
    }
    ```

    1. Будет выполнено в рамках транзакции либо откатится если вся лямбра выкинет исключение
    2. Будет выполнено в рамках транзакции либо откатится если вся лямбра выкинет исключение

Уровень изоляции берется из конфигурации `dsProperties` пула Hikari, 
либо можно самостоятельно поменять его через `java.sql.Connection` перед выполнением запросов.

```java
connection.setTransactionIsolation(Connection.TRANSACTION_READ_COMMITTED);
```

### Ручное управление

Если для запроса нужна какая-то более сложная логика, либо запросы вне репозитория, можно использовать `java.sql.Connection`:

=== ":fontawesome-brands-java: `Java`"

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

## Сигнатуры

Доступные сигнатуры для методов репозитория из коробки:

=== ":fontawesome-brands-java: `Java`"

    Под `T` подразумевается тип возвращаемого значения, либо `Void`, либо `UpdateCount`.

    - `T myMethod()`
    - `@Nullable T myMethod()`
    - `Optional<T> myMethod()`
    - `List<T> myMethod()`
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/)
    - `Mono<List<T>> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/)

=== ":simple-kotlin: `Kotlin`"

    Под `T` подразумевается тип возвращаемого значения, либо `Unit`, либо `UpdateCount`.

    - `myMethod(): T`
    - `myMethod(): T?`
    - `myMethod(): List<T>`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine)
    - `suspend myMethod(): T?` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine)
    - `suspend myMethod(): List<T>` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine)
