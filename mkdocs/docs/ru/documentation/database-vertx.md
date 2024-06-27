Модуль предоставляет реализацию репозиториев на основе [Vertx](https://vertx.io/docs/#databases) реактивного протокола работы с базой данных.

## Подключение

===! ":fontawesome-brands-java: `Java`"

    Зависимость `build.gradle`:
    ```groovy
    annotationProcessor "ru.tinkoff.kora:annotation-processors"
    implementation "ru.tinkoff.kora:database-vertx"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends VertxDatabaseModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Зависимость `build.gradle.kts`:
    ```groovy
    ksp("ru.tinkoff.kora:symbol-processors")
    implementation("ru.tinkoff.kora:database-vertx")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : VertxDatabaseModule
    ```

Также **требуется предоставить** реализацию драйвера как зависимость версии не выше [4.3.8](https://mvnrepository.com/artifact/io.vertx/vertx-pg-client/4.3.8)

В отдельных случаях как например с [PostgreSQL](https://postgrespro.ru/docs/postgresql), требуется также добавить [зависимость](https://mvnrepository.com/artifact/com.ongres.scram/client/2.1)

## Конфигурация

Пример полной конфигурации, описанной в классе `VertxDatabaseConfig` (указаны примеры значений или значения по умолчанию):

===! ":material-code-json: `Hocon`"

    ```javascript
    db {
        connectionUri = "postgresql://localhost:5432/postgres" //(1)!
        username = "postgres" //(2)!
        password = "postgres" //(3)!
        poolName = "kora" //(4)!
        maxPoolSize = 10 //(5)!
        connectionTimeout = "10s" //(6)!
        acquireTimeout = "0s" //(7)!
        idleTimeout = "10m" //(8)!
        cachePreparedStatements = true //(9)!
        initializationFailTimeout = "0s" //(10)!
        readinessProbe = false //(11)!
        telemetry {
            logging {
                enabled = false //(12)!
            }
            metrics {
                enabled = true //(13)!
                slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(14)!
            }
            telemetry {
                enabled = true //(15)!
            }
        }
    }
    ```

    1.  [URI](https://vertx.io/docs/vertx-pg-client/java/#_connection_uri) подключения к базе данных (**обязательный**)
    2.  Имя пользователя для подключения (**обязательный**)
    3.  Пароль пользователя для подключения (**обязательный**)
    4.  Имя набора соединений к базе данных (**обязательный**)
    5.  Максимальный размер набора соединений к базе данных
    6.  Максимальное время на установку соединения
    7.  Максимальное время на получение соединения из набора соединений (по умолчанию отсутвует)
    7.  Максимальное время на простой соединения
    9.  Кэшировать ли подготовленные запросы
    10.  Максимальное время ожидания инициализации соединения при старте сервиса (по умолчанию отсутвует)
    11.  Включить ли [пробу готовности](probes.md#_2) для соединения базы данных
    12.  Включает логгирование модуля (по умолчанию `false`)
    13.  Включает метрики модуля (по умолчанию `true`)
    14.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    15.  Включает трассировку модуля (по умолчанию `true`)

=== ":simple-yaml: `YAML`"

    ```yaml
    db:
      connectionUri = "postgresql://localhost:5432/postgres" #(1)!
      username: "postgres" #(2)!
      password: "postgres" #(3)!
      poolName: "kora" #(4)!
      maxPoolSize: 10 #(5)!
      connectionTimeout: "10s" #(6)!
      acquireTimeout: "10s" #(7)!
      idleTimeout: "10m" #(8)!
      cachePreparedStatements: true #(9)!
      initializationFailTimeout: "0s" #(10)!
      readinessProbe: false #(11)!
      telemetry:
        logging:
          enabled: false #(12)!
        metrics:
          enabled: true #(13)!
          slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(14)!
        telemetry:
          enabled: true #(15)!
    ```

    1.  [URI](https://vertx.io/docs/vertx-pg-client/java/#_connection_uri) подключения к базе данных (**обязательный**)
    2.  Имя пользователя для подключения (**обязательный**)
    3.  Пароль пользователя для подключения (**обязательный**)
    4.  Имя набора соединений к базе данных (**обязательный**)
    5.  Максимальный размер набора соединений к базе данных
    6.  Максимальное время на установку соединения
    7.  Максимальное время на получение соединения из набора соединений (по умолчанию отсутвует)
    7.  Максимальное время на простой соединения
    9.  Кэшировать ли подготовленные запросы
    10.  Максимальное время ожидания инициализации соединения при старте сервиса (по умолчанию отсутвует)
    11.  Включить ли [пробу готовности](probes.md#_2) для соединения базы данных
    12.  Включает логгирование модуля (по умолчанию `false`)
    13.  Включает метрики модуля (по умолчанию `true`)
    14.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    15.  Включает трассировку модуля (по умолчанию `true`)

Можно также настроить [Netty транспорт](netty.md).

## Использование

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends VertxRepository { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : VertxRepository
    ```

## Конвертация

Возможно переопределять преобразование различных частей [сущности](database-common.md) и параметров запроса, для этого Kora предоставляет специальные интерфейсы.

### Результат

Если требуется преобразовать результат в ручную, предлагается использовать `VertxRowSetMapper`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    final class ResultMapper implements VertxRowSetMapper<List<UUID>> {

        @Override
        public List<UUID> apply(RowSet<Row> rows) {
            // код преобразования
        }
    }

    @Repository
    public interface EntityRepository extends VertxRepository {

        @Mapping(ResultMapper.class)
        @Query("SELECT id FROM entities")
        Mono<List<UUID>> getIds();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class ResultMapper : VertxRowSetMapper<List<UUID>> {
        override fun apply(rows: RowSet<Row>): List<UUID> {
            // код преобразования
        }
    }

    @Repository
    interface EntityRepository : VertxRepository {

        @Mapping(ResultMapper::class)
        @Query("SELECT id FROM entities")
        fun getIds(): Mono<List<UUID>>
    }
    ```

### Строка

Если требуется преобразовать строку в ручную, предлагается использовать `VertxRowMapper`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    final class RowMapper implements VertxRowMapper<UUID> {

        @Override
        public UUID apply(Row row) {
            return UUID.fromString(rs.get(0, String.class));
        }
    }

    @Repository
    public interface EntityRepository extends VertxRepository {

        @Mapping(RowMapper.class)
        @Query("SELECT id FROM entities")
        Flux<UUID> findAll();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class RowMapper : VertxRowMapper<UUID> {

        override fun apply(row: Row): UUID {
            return UUID.fromString(rs.get(0, String.class))
        }
    }

    @Repository
    interface EntityRepository : VertxRepository {

        @Mapping(RowMapper::class)
        @Query("SELECT id FROM entities")
        fun findAll(): Flux<UUID>
    }
    ```

### Колонка

Если требуется преобразовать значение колонки в ручную, предлагается использовать `VertxResultColumnMapper`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class ColumnMapper implements VertxResultColumnMapper<UUID> {

        @Override
        public UUID apply(Row row, int index) {
            return UUID.fromString(row.get(String.class, index));
        }
    }

    @Table("entities")
    public record Entity(@Mapping(ColumnMapper.class) @Id UUID id, String name) { }

    @Repository
    public interface EntityRepository extends VertxRepository {

        @Query("SELECT * FROM entities")
        Flux<Entity> findAll();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class ColumnMapper : VertxResultColumnMapper<UUID> {

        override fun apply(row: Row, index: Int): UUID {
            return UUID.fromString(row.get(String.class, index))
        }
    }

    @Table("entities")
    data class Entity(
        @Id @Mapping(ColumnMapper::class) val id: UUID,
        val name: String
    )

    @Repository
    interface EntityRepository : VertxRepository {

        @Query("SELECT * FROM entities")
        fun findAll(): Flux<Entity>
    }
    ```

### Параметр

Если требуется преобразовать значение параметра запроса в ручную, предлагается использовать `VertxParameterColumnMapper`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class ParameterMapper implements VertxParameterColumnMapper<UUID> {

        @Override
        public Object apply(@Nullable UUID value) {
            return value.toString();
        }
    }

    @Repository
    public interface EntityRepository extends VertxRepository {

        @Query("SELECT * FROM entities WHERE id = :id")
        Flux<Entity> findById(@Mapping(ParameterMapper.class) UUID id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class ParameterMapper : VertxParameterColumnMapper<UUID?> {
        override fun apply(value: UUID?): Any {
            return value.toString()
        }
    }

    @Repository
    interface EntityRepository : VertxRepository {

        @Query("SELECT * FROM entities WHERE id = :id")
        fun findById(@Mapping(ParameterMapper::class) id: UUID): Flux<Entity>
    }
    ```

## Транзакции

Для выполнения ручных запросов в Kora есть интерфейс `ru.tinkoff.kora.database.vertx.VertxConnectionFactory`,
который предоставляется в методе в рамках контракта `VertxRepository`.
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
            return repository.getVertxConnectionFactory().inTx(connection -> {
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
            return repository.getVertxConnectionFactory.inTx {
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
            return repository.getVertxConnectionFactory().inTx(connection -> {
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
            return repository.getVertxConnectionFactory.inTx { connection ->
                // do some work
            }
        }
    }
    ```

## Сигнатуры

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
