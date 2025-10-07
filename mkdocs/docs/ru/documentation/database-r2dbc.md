Модуль предоставляет реализацию репозиториев на основе [R2DBC](https://r2dbc.io/) реактивного протокола работы с базами данных, 
реализацией как пример является [Postgres R2DBC](https://github.com/pgjdbc/r2dbc-postgresql).

## Подключение

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#_4) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:database-r2dbc"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends R2dbcDatabaseModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#_4) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:database-r2dbc")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : R2dbcDatabaseModule
    ```

Также **требуется предоставить** реализацию драйвера базы данных как зависимость.

## Конфигурация

Пример полной конфигурации, описанной в классе `R2dbcDatabaseConfig` (указаны примеры значений или значения по умолчанию):

===! ":material-code-json: `Hocon`"

    ```javascript
    db {
        r2dbcUrl = "r2dbc:postgresql://localhost:5432/postgres" //(1)!
        username = "postgres" //(2)!
        password = "postgres" //(3)!
        poolName = "kora" //(4)!
        maxPoolSize = 10 //(5)!
        minIdle = 0 //(6)!
        acquireRetry = 3 //(7)!
        connectionTimeout = "10s" //(8)!
        connectionCreateTimeout = "30s" //(9)!
        idleTimeout = "10m" //(10)!
        maxLifetime = "0s" //(11)!
        statementTimeout = "0s" //(12)!
        readinessProbe = false //(13)!
        options { //(14)!
            "backgroundEvictionInterval": "PT120S"
        }
        telemetry {
            logging {
                enabled = false //(15)!
            }
            metrics {
                enabled = true //(16)!
                slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(17)!
            }
            tracing {
                enabled = true //(18)!
            }
        }
    }
    ```

    1.  R2DBC URL подключения к базе данных (**обязательный**)
    2.  Имя пользователя для подключения (**обязательный**)
    3.  Пароль пользователя для подключения (**обязательный**)
    4.  Имя набора соединений к базе данных (**обязательный**)
    5.  Максимальный размер набора соединений к базе данных
    6.  Минимальный размер набора готовых соединений к базе данных в режиме ожидания
    7.  Максимальное количество попыток получения соединения
    8.  Максимальное время на установку соединения
    9.  Максимальное время на создание соединения
    10.  Максимальное время на простой соединения
    11.  Максимальное время жизни соединения (по умолчанию отсутвует)
    12.  Максимальное время на выполнение запроса в базу данных (по умолчанию отсутвует)
    13.  Включить ли [пробу готовности](probes.md#_2) для соединения базы данных
    14.  Дополнительные атрибуты R2DBC соединения (по умолчанию отсутвует)
    15.  Включает логгирование модуля (по умолчанию `false`)
    16.  Включает метрики модуля (по умолчанию `true`)
    17.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    18.  Включает трассировку модуля (по умолчанию `true`)

=== ":simple-yaml: `YAML`"

    ```yaml
    db:
      r2dbcUrl: "r2dbc:postgresql://localhost:5432/postgres" #(1)!
      username: "postgres" #(2)!
      password: "postgres" #(3)!
      poolName: "kora" #(4)!
      maxPoolSize: 10 #(5)!
      minIdle: 0 #(6)!
      acquireRetry: 3 #(7)!
      connectionTimeout: "10s" #(8)!
      connectionCreateTimeout: "30s" #(9)!
      idleTimeout: "10m" #(10)!
      maxLifetime: "0s" #(11)!
      statementTimeout: "0ms" #(12)!
      readinessProbe: false #(13)!
      options: #(14)!
        backgroundEvictionInterval: "PT120S"
      telemetry:
        logging:
          enabled: false #(15)!
        metrics:
          enabled: true #(16)!
          slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(17)!
        tracing:
          enabled: true #(18)!
    ```

    1.  R2DBC URL подключения к базе данных (**обязательный**)
    2.  Имя пользователя для подключения (**обязательный**)
    3.  Пароль пользователя для подключения (**обязательный**)
    4.  Имя набора соединений к базе данных (**обязательный**)
    5.  Максимальный размер набора соединений к базе данных
    6.  Минимальный размер набора готовых соединений к базе данных в режиме ожидания
    7.  Максимальное количество попыток получения соединения
    8.  Максимальное время на установку соединения
    9.  Максимальное время на создание соединения
    10.  Максимальное время на простой соединения
    11.  Максимальное время жизни соединения (по умолчанию отсутвует)
    12.  Максимальное время на выполнение запроса в базу данных (по умолчанию отсутвует)
    13.  Включить ли [пробу готовности](probes.md#_2) для соединения базы данных
    14.  Дополнительные атрибуты R2DBC соединения (по умолчанию отсутвует)
    15.  Включает логгирование модуля (по умолчанию `false`)
    16.  Включает метрики модуля (по умолчанию `true`)
    17.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    18.  Включает трассировку модуля (по умолчанию `true`)

## Использование

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends R2dbcRepository { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : R2dbcRepository
    ```

## Конвертация

Возможно переопределять преобразование различных частей [сущности](database-common.md) и параметров запроса, для этого Kora предоставляет специальные интерфейсы.

### Результат

Если требуется преобразовать результат вручную, предлагается использовать `R2dbcResultFluxMapper`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    final class ResultMapper implements R2dbcResultFluxMapper<UUID, Flux<UUID>> {

        @Override
        public Flux<UUID> apply(Flux<Result> resultFlux) {
            // код преобразования
        }
    }

    @Repository
    public interface EntityRepository extends R2dbcRepository {

        @Mapping(ResultMapper.class)
        @Query("SELECT id FROM entities")
        Flux<UUID> getIds();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Для Kotlin писать преобразователи надо только для `T?` типов, так в интерфейсах тип указан как `@Nullable`.

    ```kotlin
    class ResultMapper : R2dbcResultFluxMapper<UUID, Flux<UUID>> {
        override fun apply(resultFlux: Flux<Result>): Flux<UUID> {
            // код преобразования
        }
    }

    @Repository
    interface EntityRepository : R2dbcRepository {

        @Mapping(ResultMapper::class)
        @Query("SELECT id FROM entities")
        fun getIds(): Flux<UUID>
    }
    ```

### Строка

Если требуется преобразовать строку вручную, предлагается использовать `R2dbcRowMapper`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    final class RowMapper implements R2dbcRowMapper<UUID> {

        @Override
        public UUID apply(Row row) {
            return UUID.fromString(rs.get(0, String.class));
        }
    }

    @Repository
    public interface EntityRepository extends R2dbcRepository {

        @Mapping(RowMapper.class)
        @Query("SELECT id FROM entities")
        Flux<UUID> findAll();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Для Kotlin писать преобразователи надо только для `T?` типов, так в интерфейсах тип указан как `@Nullable`.

    ```kotlin
    class RowMapper : R2dbcRowMapper<UUID> {

        override fun apply(row: Row): UUID {
            return UUID.fromString(rs.get(0, String.class))
        }
    }

    @Repository
    interface EntityRepository : R2dbcRepository {

        @Mapping(RowMapper::class)
        @Query("SELECT id FROM entities")
        fun findAll(): Flux<UUID>
    }
    ```

### Колонка

Если требуется преобразовать значение колонки вручную, предлагается использовать `R2dbcResultColumnMapper`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class ColumnMapper implements R2dbcResultColumnMapper<UUID> {

        @Override
        public UUID apply(Row row, String label) {
            return UUID.fromString(row.get(label, String.class));
        }
    }

    @Table("entities")
    public record Entity(@Mapping(ColumnMapper.class) @Id UUID id, String name) { }

    @Repository
    public interface EntityRepository extends R2dbcRepository {

        @Query("SELECT id, name FROM entities")
        Flux<Entity> findAll();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Для Kotlin писать преобразователи надо только для `T?` типов, так в интерфейсах тип указан как `@Nullable`.

    ```kotlin
    class ColumnMapper : R2dbcResultColumnMapper<UUID> {

        override fun apply(row: Row, label: String): UUID {
            return UUID.fromString(row.get(label, String.class))
        }
    }

    @Table("entities")
    data class Entity(
        @Id @Mapping(ColumnMapper::class) val id: UUID,
        val name: String
    )

    @Repository
    interface EntityRepository : R2dbcRepository {

        @Query("SELECT id, name FROM entities")
        fun findAll(): Flux<Entity>
    }
    ```

### Параметр

Если требуется преобразовать значение параметра запроса вручную, предлагается использовать `R2dbcParameterColumnMapper`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class ParameterMapper implements R2dbcParameterColumnMapper<UUID> {

        @Override
        public void set(Statement stmt, int index, @Nullable UUID value) {
            if (value != null) {
                stmt.bind(index, value.toString());
            }
        }
    }

    @Repository
    public interface EntityRepository extends R2dbcRepository {

        @Query("SELECT id, name FROM entities WHERE id = :id")
        Flux<Entity> findById(@Mapping(ParameterMapper.class) UUID id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Для Kotlin писать преобразователи надо только для `T?` типов, так в интерфейсах тип указан как `@Nullable`.

    ```kotlin
    class ParameterMapper : R2dbcParameterColumnMapper<UUID?> {

        override fun set(stmt: Statement, index: Int, value: UUID?) {
            if (value != null) {
                stmt.bind(index, value.toString())
            }
        }
    }

    @Repository
    interface EntityRepository : R2dbcRepository {

        @Query("SELECT id, name FROM entities WHERE id = :id")
        fun findById(@Mapping(ParameterMapper::class) id: UUID): Flux<Entity>
    }
    ```

### Поддерживаемые типы

??? abstract "Список поддерживаемых типов для аргументов/возвращаемых значений из коробки"

    Такие типы выбраны так как поддерживаются большинством популярных баз данных.

    * void
    * boolean / Boolean
    * short / Short
    * int / Integer
    * long / Long
    * double / Double
    * float / Float
    * byte[]
    * String
    * BigInteger
    * BigDecimal
    * UUID
    * LocalDate
    * LocalTime
    * LocalDateTime
    * OffsetTime
    * OffsetDateTime

## Созданный идентификатор

Если необходимо получить в качестве результата созданные базой данных первичные ключи сущности,
предлагается использовать аннотацию `@Id` над методом, где тип возвращаемого значения является идентификаторами.
Такой подход работает и для `@Batch` запросов.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends R2dbcRepository {

        public record Entity(Long id, String name) {}

        @Query("INSERT INTO entities(name) VALUES (:entity.name)")
        @Id
        Mono<Long> insert(Entity entity);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : R2dbcRepository {

        public record Entity(Long id, String name) {}

        @Query("INSERT INTO entities(name) VALUES (:entity.name)")
        @Id
        fun insert(entity: Entity): Mono<Long>
    }
    ```

## Транзакции

Для выполнения ручных запросов в Kora есть интерфейс `ru.tinkoff.kora.database.r2dbc.R2dbcConnectionFactory`,
который предоставляется в методе в рамках контракта `R2dbcRepository`.
Все методы репозитория вызванные в рамках лямбды транзакции будут выполнены в этой самой транзакции.

Для того чтобы выполнять запросы транзакционно, можно использовать контракт `inTx`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final EntityRepository repository;

        public SomeService(EntityRepository repository) {
            this.repository = repository;
        }

        public Mono<List<Entity>> saveAll(Entity one, Entity two) {
            return repository.getR2dbcConnectionFactory().inTx(connection -> {
                // do some work
                return repository.insert(one) //(1)!
                        .zipWith(repository.insert(two), //(2)!
                            (r1, r2) -> List.of(one, two));
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

        fun saveAll(
            one: Entity,
            two: Entity
        ): Mono<List<Entity>> {
            return repository.r2dbcConnectionFactory.inTx {
                repository.insert(one).zipWith(repository.insert(two)) //(1)!
                { r1: UpdateCount, r2: UpdateCount -> listOf(one, two) }
            }
        }
    }
    ```

    1. Будет выполнено в рамках транзакции либо откатится если вся лямбра выкинет исключение

### Ручное управление

Если для запроса нужна какая-то более сложная логика, либо запросы вне репозитория, можно использовать `io.r2dbc.spi.Connection`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final EntityRepository repository;

        public SomeService(EntityRepository repository) {
            this.repository = repository;
        }

        public Mono<List<Entity>> saveAll(Entity one, Entity two) {
            return repository.getR2dbcConnectionFactory().inTx(connection -> {
                // do some work
            });
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(private val repository: EntityRepository) {

        fun saveAll(
            one: Entity,
            two: Entity
        ): Mono<List<Entity>> {
            return repository.r2dbcConnectionFactory.inTx { connection ->
                // do some work
            }
        }
    }
    ```

## Сигнатуры

Под `T` подразумевается тип возвращаемого значения, либо `Void`, либо `UpdateCount`.

Доступные сигнатуры для методов репозитория из коробки:

===! ":fontawesome-brands-java: `Java`"

    Под `T` подразумевается тип возвращаемого значения, либо `List<T>`, либо `Void`, либо `UpdateCount`.

    - `T myMethod()`
    - `@Nullable T myMethod()`
    - `Optional<T> myMethod()`
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (надо подключить [зависимость](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))
    - `Flux<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (надо подключить [зависимость](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

=== ":simple-kotlin: `Kotlin`"

    Под `T` подразумевается тип возвращаемого значения, либо `T?`, либо `List<T>`, либо `Unit`, либо `UpdateCount`.

    - `myMethod(): T`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (надо подключить [зависимость](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) как `implementation`)
    - `myMethod(): Flow<T>` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (надо подключить [зависимость](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) как `implementation`)
