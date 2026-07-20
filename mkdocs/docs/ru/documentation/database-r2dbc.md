---
description: "Explains Kora R2DBC repositories, reactive database configuration, result and parameter mapping, transactions, generated identifiers, and repository method signatures. Use when working with @Repository, @Query, @Table, @Id, @Column, @Batch, R2dbcDatabaseModule, R2dbcConnectionFactory."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora R2DBC repositories, reactive database configuration, result and parameter mapping, transactions, generated identifiers, and repository method signatures; key triggers include @Repository, @Query, @Table, @Id, @Column, @Batch, R2dbcDatabaseModule, R2dbcConnectionFactory, R2dbcRepository."
---

Модуль предоставляет реализацию репозиториев на основе реактивного протокола баз данных [R2DBC](https://r2dbc.io/);
реализацией драйвера может быть, например, [Postgres R2DBC](https://github.com/pgjdbc/r2dbc-postgresql).
Для управления соединениями используется пул соединений [io.r2dbc.pool](https://github.com/r2dbc/r2dbc-pool).
Вы описываете интерфейс репозитория и `SQL`-запросы через `@Repository` и `@Query`, а `Kora` генерирует реализацию,
которая получает реактивное соединение из пула, подставляет параметры, преобразует `Flux<Result>` и участвует в транзакциях.

Общие правила для сущностей, `@Repository`, `@Query`, `@Batch`, `UpdateCount`, макросов, ручных запросов и других
механизмов репозиториев описаны в разделе [Общие правила баз данных](database-common.md).

## Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:database-r2dbc"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends R2dbcDatabaseModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:database-r2dbc")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : R2dbcDatabaseModule
    ```

Также **требуется предоставить** реализацию драйвера базы данных как зависимость.

## Конфигурация { #configuration }

Пример полной конфигурации, описанной в классе `R2dbcDatabaseConfig` (указаны примеры значений или значения по умолчанию):

===! ":material-code-json: `HOCON`"

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
                tags = { // (18)!
                    "key1" = "value1"
                    "key2" = "value2"
                }
            }
            tracing {
                enabled = true //(19)!
                attributes = { // (20)!
                    "key1" = "value1"
                    "key2" = "value2"
                }
            }
        }
    }
    ```

    1.  `R2DBC URL` подключения к базе данных (`обязательная`, по умолчанию не указано)
    2.  Имя пользователя для подключения (`обязательная`, по умолчанию не указано)
    3.  Пароль пользователя для подключения (`обязательная`, по умолчанию не указано)
    4.  Имя пула соединений (`обязательная`, по умолчанию не указано)
    5.  Максимальный размер пула соединений (по умолчанию: `10`)
    6.  Минимальное количество готовых соединений в пуле в режиме ожидания (по умолчанию: `0`)
    7.  Максимальное количество попыток получить соединение (по умолчанию: `3`)
    8.  Максимальное время получения соединения из пула (по умолчанию: `10s`)
    9.  Максимальное время создания нового физического соединения (по умолчанию: `30s`)
    10. Максимальное время простоя соединения (по умолчанию: `10m`)
    11. Максимальное время жизни соединения, `0s` означает отсутствие ограничения (по умолчанию: `0s`)
    12. Максимальное время выполнения запроса к базе данных (по умолчанию не указано, необязательно)
    13. Включить ли [пробу готовности](probes.md#readiness) для соединения с базой данных (по умолчанию: `false`)
    14. Дополнительные параметры соединения `R2DBC`, передаваемые в драйвер (по умолчанию: `{}`)
    15. Включает логирование модуля (по умолчанию: `false`)
    16. Включает метрики модуля (по умолчанию: `true`)
    17. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    18. Настройка тегов для метрик (по умолчанию: `{}`)
    19. Включает трассировку модуля (по умолчанию: `true`)
    20. Настройка атрибутов для трассировки (по умолчанию: `{}`)

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
      statementTimeout: "0s" #(12)!
      readinessProbe: false #(13)!
      options: #(14)!
        backgroundEvictionInterval: "PT120S"
      telemetry:
        logging:
          enabled: false #(15)!
        metrics:
          enabled: true #(16)!
          slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(17)!
          tags: #(18)!
            key1: value1
            key2: value2
        tracing:
          enabled: true #(19)!
          attributes: #(20)!
            key1: value1
            key2: value2
    ```

    1.  `R2DBC URL` подключения к базе данных (`обязательная`, по умолчанию не указано)
    2.  Имя пользователя для подключения (`обязательная`, по умолчанию не указано)
    3.  Пароль пользователя для подключения (`обязательная`, по умолчанию не указано)
    4.  Имя пула соединений (`обязательная`, по умолчанию не указано)
    5.  Максимальный размер пула соединений (по умолчанию: `10`)
    6.  Минимальное количество готовых соединений в пуле в режиме ожидания (по умолчанию: `0`)
    7.  Максимальное количество попыток получить соединение (по умолчанию: `3`)
    8.  Максимальное время получения соединения из пула (по умолчанию: `10s`)
    9.  Максимальное время создания нового физического соединения (по умолчанию: `30s`)
    10. Максимальное время простоя соединения (по умолчанию: `10m`)
    11. Максимальное время жизни соединения, `0s` означает отсутствие ограничения (по умолчанию: `0s`)
    12. Максимальное время выполнения запроса к базе данных (по умолчанию не указано, необязательно)
    13. Включить ли [пробу готовности](probes.md#readiness) для соединения с базой данных (по умолчанию: `false`)
    14. Дополнительные параметры соединения `R2DBC`, передаваемые в драйвер (по умолчанию: `{}`)
    15. Включает логирование модуля (по умолчанию: `false`)
    16. Включает метрики модуля (по умолчанию: `true`)
    17. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    18. Настройка тегов для метрик (по умолчанию: `{}`)
    19. Включает трассировку модуля (по умолчанию: `true`)
    20. Настройка атрибутов для трассировки (по умолчанию: `{}`)

## Использование { #usage }

`R2DBC`-репозиторий объявляется интерфейсом с аннотацией `@Repository` и должен наследовать `R2dbcRepository`.
Каждый метод с `@Query` содержит обычный `SQL`-запрос. Параметры метода подставляются в запрос по имени через
синтаксис `:parameter`, а поля объекта можно указывать через `:entity.field`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends R2dbcRepository {

        @Query("SELECT id, name FROM entities WHERE id = :id")
        Mono<Entity> findById(String id);

        @Query("SELECT id, name FROM entities")
        Flux<Entity> findAll();

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        Mono<Void> insert(Entity entity);

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        Mono<UpdateCount> insertBatch(@Batch List<Entity> entities);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : R2dbcRepository {

        @Query("SELECT id, name FROM entities WHERE id = :id")
        fun findById(id: String): Mono<Entity>

        @Query("SELECT id, name FROM entities")
        fun findAll(): Flux<Entity>

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        fun insert(entity: Entity): Mono<Void>

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        fun insertBatch(@Batch entities: List<Entity>): Mono<UpdateCount>
    }
    ```

`SQL` остается под контролем разработчика: можно использовать специфичные возможности конкретной базы данных, а `Kora`
занимается только безопасной подстановкой параметров, выполнением запроса и преобразованием результата.
Общие правила сущностей, `@Table`, `@Column`, `@Id`, `@Embedded`, `@Batch` и макросов описаны в разделе
[Общие правила баз данных](database-common.md).

Реактивные возвращаемые значения `Mono` и `Flux` являются нативными сигнатурами для этого модуля.
Блокирующие возвращаемые значения, такие как `Entity`, `List<Entity>`, `void` и `UpdateCount`, также поддерживаются, но они
блокируют вызывающий поток до завершения реактивного результата, поэтому в реактивном контексте предпочтительнее использовать
реактивные сигнатуры.

## Преобразование { #mapping }

Можно переопределять преобразование разных частей [сущности](database-common.md), результата и параметров запроса.
Для этого `Kora` предоставляет несколько интерфейсов преобразователей.

### Результат { #result }

Используйте `R2dbcResultFluxMapper<T, P>`, когда требуется управлять всем `Flux<Result>`.
Такой преобразователь получает весь реактивный поток результата и сам решает, как его прочитать и что вернуть.

===! ":fontawesome-brands-java: `Java`"

    ```java
    final class ResultMapper implements R2dbcResultFluxMapper<UUID, Flux<UUID>> {

        @Override
        public Flux<UUID> apply(Flux<Result> resultFlux) {
            return resultFlux.flatMap(result -> result.map((row, meta) ->
                UUID.fromString(row.get(0, String.class))));
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

    ```kotlin
    class ResultMapper : R2dbcResultFluxMapper<UUID, Flux<UUID>> {
        override fun apply(resultFlux: Flux<Result>): Flux<UUID> {
            return resultFlux.flatMap { result ->
                result.map { row, _ -> UUID.fromString(row.get(0, String::class.java)) }
            }
        }
    }

    @Repository
    interface EntityRepository : R2dbcRepository {

        @Mapping(ResultMapper::class)
        @Query("SELECT id FROM entities")
        fun getIds(): Flux<UUID>
    }
    ```

В большинстве случаев управлять всем `Flux<Result>` не требуется.
Достаточно предоставить [R2dbcRowMapper](#row), и `Kora` автоматически адаптирует его к типу возвращаемого значения метода:
модуль предоставляет готовые преобразователи потока результата `mono` (`Mono<T>`), `monoList` (`Mono<List<T>>`) и `flux` (`Flux<T>`),
построенные на основе одного преобразователя строки. Также есть вспомогательный метод `R2dbcResultFluxMapper.monoOptional`, который адаптирует преобразователь строки к `Mono<Optional<T>>`.

### Строка { #row }

Используйте `R2dbcRowMapper<T>`, когда требуется вручную преобразовать одну строку результата.
Колонки читаются из `io.r2dbc.spi.Row` по индексу (начиная с `0`) или по имени:

===! ":fontawesome-brands-java: `Java`"

    ```java
    final class RowMapper implements R2dbcRowMapper<EntityPart> {

        @Override
        public EntityPart apply(Row row) {
            return new EntityPart(row.get(0, String.class), row.get(1, Integer.class));
        }
    }

    @Repository
    public interface EntityRepository extends R2dbcRepository {

        @Mapping(RowMapper.class)
        @Query("SELECT id, value1 FROM entities")
        Flux<EntityPart> findAllParts();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class RowMapper : R2dbcRowMapper<EntityPart> {

        override fun apply(row: Row): EntityPart {
            return EntityPart(row.get(0, String::class.java), row.get(1, Integer::class.java))
        }
    }

    @Repository
    interface EntityRepository : R2dbcRepository {

        @Mapping(RowMapper::class)
        @Query("SELECT id, value1 FROM entities")
        fun findAllParts(): Flux<EntityPart>
    }
    ```

### Колонка { #column }

Используйте `R2dbcResultColumnMapper<T>`, когда требуется вручную преобразовать значение отдельной колонки по её имени:

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

    ```kotlin
    class ColumnMapper : R2dbcResultColumnMapper<UUID> {

        override fun apply(row: Row, label: String): UUID {
            return UUID.fromString(row.get(label, String::class.java))
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

### Параметр { #parameter }

Используйте `R2dbcParameterColumnMapper<T>`, когда требуется вручную привязать значение параметра запроса к `io.r2dbc.spi.Statement`.
Значение привязывается через `stmt.bind(index, value)`, а для `null` используется `stmt.bindNull(index, type)`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class ParameterMapper implements R2dbcParameterColumnMapper<UUID> {

        @Override
        public void apply(Statement stmt, int index, @Nullable UUID value) {
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

    ```kotlin
    class ParameterMapper : R2dbcParameterColumnMapper<UUID?> {

        override fun apply(stmt: Statement, index: Int, value: UUID?) {
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

Преобразователь колонки результата и преобразователь параметра можно сочетать на одном поле сущности.
Это удобно для преобразования, например, перечисления как при чтении строки, так и при привязке параметра:

===! ":fontawesome-brands-java: `Java`"

    ```java
    record Entity(String id,
                  @Mapping(FieldTypeResultMapper.class)
                  @Mapping(FieldTypeParameterMapper.class)
                  @Column("value1") FieldType field1) { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class Entity(
        val id: String,
        @Mapping(FieldTypeResultMapper::class)
        @Mapping(FieldTypeParameterMapper::class)
        @Column("value1") val field1: FieldType
    )
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
    * BigInteger
    * BigDecimal
    * UUID
    * LocalDate
    * LocalTime
    * LocalDateTime
    * OffsetTime
    * OffsetDateTime

    Для остальных типов используйте собственные преобразователи `R2dbcResultColumnMapper<T>` / `R2dbcParameterColumnMapper<T>`
    либо `R2dbcRowMapper<T>` / `R2dbcResultFluxMapper<T, P>`.

## Созданный идентификатор { #generated-identifier }

Если необходимо получить в качестве результата первичные ключи, созданные базой данных,
используйте аннотацию `@Id` над методом, тип возвращаемого значения которого является идентификатором.
Такой подход работает и для `@Batch` запросов, в этом случае метод возвращает список созданных идентификаторов.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends R2dbcRepository {

        record Entity(Long id, String name) {}

        @Query("INSERT INTO entities(name) VALUES (:entity.name)")
        @Id
        Mono<Long> insert(Entity entity);

        @Query("INSERT INTO entities(name) VALUES (:entity.name)")
        @Id
        Mono<List<Long>> insertBatch(@Batch List<Entity> entities);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : R2dbcRepository {

        data class Entity(val id: Long?, val name: String)

        @Query("INSERT INTO entities(name) VALUES (:entity.name)")
        @Id
        fun insert(entity: Entity): Mono<Long>

        @Query("INSERT INTO entities(name) VALUES (:entity.name)")
        @Id
        fun insertBatch(@Batch entities: List<Entity>): Mono<List<Long>>
    }
    ```

В качестве альтернативы можно явно вернуть созданные колонки через `RETURNING` и преобразовать их как обычный результат,
без аннотации `@Id`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Query("INSERT INTO entities(name) VALUES (:entity.name) RETURNING id")
    Mono<Long> insert(Entity entity);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Query("INSERT INTO entities(name) VALUES (:entity.name) RETURNING id")
    fun insert(entity: Entity): Mono<Long>
    ```

## Ручной запрос с телеметрией { #query }

Если запрос сложно выразить одним статическим `@Query`, можно сделать обычный метод с реализацией и самостоятельно собрать `SQL`.
Для выполнения такого запроса используйте `R2dbcConnectionFactory#query`.
Этот метод создает `io.r2dbc.spi.Statement`, проводит запрос через телеметрию `Kora` и использует то же соединение, что и остальные методы репозитория.
Если `query` вызывается внутри активной транзакции `inTx`, запрос будет выполнен на текущем транзакционном соединении.

`query` принимает три аргумента:

- `QueryContext` с идентификатором запроса и итоговым `SQL`. Идентификатор запроса попадает в телеметрию, поэтому для него удобно использовать стабильное имя вида `Repository.method`;
- `Consumer<Statement>`, который привязывает значения параметров. Значения нужно привязывать через `Statement` (`stmt.bind(...)`), а не подставлять в строку запроса напрямую;
- `Function<Flux<Result>, Mono<T>>`, который читает реактивный результат и формирует возвращаемое значение.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends R2dbcRepository {

        default Mono<List<Entity>> findByFilter(@Nullable String name, boolean onlyActive) {
            var sql = new StringBuilder("SELECT id, name FROM entities WHERE 1 = 1");
            var params = new ArrayList<String>();

            if (name != null) {
                params.add(name);
                sql.append(" AND name = $").append(params.size());
            }
            if (onlyActive) {
                sql.append(" AND active = true");
            }

            var queryContext = new QueryContext("EntityRepository.findByFilter", sql.toString());
            return getR2dbcConnectionFactory().query(
                queryContext,
                statement -> {
                    for (int i = 0; i < params.size(); i++) {
                        statement.bind(i, params.get(i));
                    }
                },
                resultFlux -> resultFlux
                    .flatMap(result -> result.map((row, meta) ->
                        new Entity(row.get("id", String.class), row.get("name", String.class))))
                    .collectList()
            );
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : R2dbcRepository {

        fun findByFilter(name: String?, onlyActive: Boolean): Mono<List<Entity>> {
            val sql = StringBuilder("SELECT id, name FROM entities WHERE 1 = 1")
            val params = mutableListOf<String>()

            if (name != null) {
                params += name
                sql.append(" AND name = $").append(params.size)
            }
            if (onlyActive) {
                sql.append(" AND active = true")
            }

            val queryContext = QueryContext("EntityRepository.findByFilter", sql.toString())
            return r2dbcConnectionFactory.query(
                queryContext,
                { statement ->
                    params.forEachIndexed { index, value ->
                        statement.bind(index, value)
                    }
                },
                { resultFlux ->
                    resultFlux
                        .flatMap { result -> result.map { row, _ ->
                            Entity(row.get("id", String::class.java), row.get("name", String::class.java))
                        } }
                        .collectList()
                }
            )
        }
    }
    ```

## Транзакции { #transactions }

Для выполнения ручных запросов и объединения запросов в транзакцию `Kora` предоставляет интерфейс `R2dbcConnectionFactory`
в рамках контракта `R2dbcRepository`, получаемый через `getR2dbcConnectionFactory()`.
Все методы репозитория, вызванные внутри лямбды транзакции, выполняются в этой самой транзакции.

Для того чтобы выполнять запросы транзакционно, используйте `inTx`.
Если на текущем реактивном `Context` уже есть активная транзакция, вложенный вызов `inTx` использует то же соединение и не открывает
новую транзакцию.

Транзакционную последовательность операций можно оставлять внутри самого репозитория с помощью обычного метода с реализацией.
Такой подход удобен, когда нужно оставить несколько `@Query`-методов или сложный самостоятельный `SQL`-запрос рядом с остальными запросами репозитория,
не вынося техническую работу с базой данных в сервисный слой.
Внутри такого метода можно использовать и `@Query`-методы репозитория, и `R2dbcConnectionFactory#query` для ручного запроса с телеметрией.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends R2dbcRepository {

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        Mono<UpdateCount> insert(Entity entity);

        @Query("UPDATE entities SET name = :name WHERE id = :id")
        Mono<UpdateCount> updateName(String id, String name);

        default Mono<List<Entity>> saveAll(Entity one, Entity two) {
            return getR2dbcConnectionFactory().inTx(connection ->
                insert(one) //(1)!
                    .then(updateName(two.id(), two.name())) //(2)!
                    .thenReturn(List.of(one, two)));
        }
    }
    ```

    1. Будет выполнено в рамках транзакции или откатится, если вся цепочка сигнализирует об ошибке
    2. Будет выполнено в рамках транзакции или откатится, если вся цепочка сигнализирует об ошибке

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : R2dbcRepository {

        @Query("INSERT INTO entities(id, name) VALUES (:entity.id, :entity.name)")
        fun insert(entity: Entity): Mono<UpdateCount>

        @Query("UPDATE entities SET name = :name WHERE id = :id")
        fun updateName(id: String, name: String): Mono<UpdateCount>

        fun saveAll(one: Entity, two: Entity): Mono<List<Entity>> {
            return r2dbcConnectionFactory.inTx { _ ->
                insert(one) //(1)!
                    .then(updateName(two.id, two.name)) //(2)!
                    .thenReturn(listOf(one, two))
            }
        }
    }
    ```

    1. Будет выполнено в рамках транзакции или откатится, если вся цепочка сигнализирует об ошибке
    2. Будет выполнено в рамках транзакции или откатится, если вся цепочка сигнализирует об ошибке

Транзакция фиксируется при успешном завершении возвращаемого `Mono`.
Если `Mono` сигнализирует об ошибке, транзакция откатывается, а ошибка пробрасывается дальше, поэтому все изменения в базе данных,
сделанные в рамках транзакции, не применяются.

### Ручное управление соединением { #connection }

Если для запроса нужна более сложная логика или запросы вне репозитория, можно работать напрямую с `io.r2dbc.spi.Connection`.
Метод `withConnection` выполняет код с соединением, но сам по себе не открывает транзакцию.

`withConnection` работает так:

- если в текущем реактивном `Context` уже есть соединение, метод передает в лямбду это текущее соединение;
- если соединения в текущем `Context` нет, метод берет новое соединение из пула, кладет его в `Context` на время выполнения лямбды и закрывает после завершения;
- повторные вызовы `withConnection`, `R2dbcConnectionFactory#query` и методы репозитория внутри этой лямбды используют то же текущее соединение.

`withConnection` возвращает `Mono<T>`. Для результатов, которые естественным образом являются потоком строк, используйте `withConnectionFlux` —
вариант с возвратом `Flux` и той же семантикой работы с соединением.
Метод `inTx` открывает транзакцию и построен поверх `withConnection`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final EntityRepository repository;

        public SomeService(EntityRepository repository) {
            this.repository = repository;
        }

        public Mono<List<Entity>> loadAll() {
            return repository.getR2dbcConnectionFactory().withConnection(connection -> {
                // do some work, returns Mono
            });
        }

        public Flux<Entity> streamAll() {
            return repository.getR2dbcConnectionFactory().withConnectionFlux(connection -> {
                // do some work, returns Flux
            });
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(private val repository: EntityRepository) {

        fun loadAll(): Mono<List<Entity>> {
            return repository.r2dbcConnectionFactory.withConnection { connection ->
                // do some work, returns Mono
            }
        }

        fun streamAll(): Flux<Entity> {
            return repository.r2dbcConnectionFactory.withConnectionFlux { connection ->
                // do some work, returns Flux
            }
        }
    }
    ```

## Выборка по списку { #select-by-list }

Иногда требуется выборка строк по списку значений.
`Kora` старается делать преобразования во время компиляции и не переписывать `SQL` во время работы, поэтому для параметра-списка
нужен собственный преобразователь, который привязывает всю коллекцию как одно значение.

Пример ниже показывает `Postgres` через массив, привязываемый с помощью `ANY(:ids)`.
Обратите внимание, что многие драйверы `R2DBC` (например, `Postgres`) могут привязывать Java-массив напрямую, поэтому такой преобразователь часто короткий:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    class ListOfStringR2dbcParameterMapper implements R2dbcParameterColumnMapper<List<String>> {

        @Override
        public void apply(Statement stmt, int index, @Nullable List<String> value) {
            stmt.bind(index, value.toArray(String[]::new));
        }
    }

    @Repository
    public interface EntityRepository extends R2dbcRepository {

        @Query("SELECT id, name FROM entities WHERE id = ANY(:ids)")
        Flux<Entity> findAllByIds(@Mapping(ListOfStringR2dbcParameterMapper.class) List<String> ids);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ListOfStringR2dbcParameterMapper : R2dbcParameterColumnMapper<List<String>> {

        override fun apply(stmt: Statement, index: Int, value: List<String>?) {
            stmt.bind(index, value!!.toTypedArray())
        }
    }

    @Repository
    interface EntityRepository : R2dbcRepository {

        @Query("SELECT id, name FROM entities WHERE id = ANY(:ids)")
        fun findAllByIds(@Mapping(ListOfStringR2dbcParameterMapper::class) ids: List<String>): Flux<Entity>
    }
    ```

## Сигнатуры { #signatures }

Доступные сигнатуры для методов репозитория из коробки.
Поскольку `R2DBC` реактивен нативно, для асинхронных сигнатур не требуется компонент `Executor`.

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

## Телеметрия { #telemetry }

R2DBC драйвер использует общий контракт телеметрии для логирования, метрик и трассировки запросов.
Конфигурация телеметрии (секция `telemetry { logging / metrics / tracing }`) описана в разделе [Конфигурация](#configuration).
Точки расширения находятся в `ru.tinkoff.kora.database.common.telemetry`.

Для каждого запроса создаётся `DataBaseTelemetry.DataBaseTelemetryContext`, который закрывается по завершении запроса.
Выполняемый запрос описывается `QueryContext(queryId, sql, operation)`, где `queryId` — стабильный идентификатор запроса,
`sql` — итоговый текст запроса, а `operation` по умолчанию равно `db_query`.

Фабрика по умолчанию `DefaultDataBaseTelemetryFactory` объединяет три фабрики:
- `DataBaseLoggerFactory` строит `DataBaseLogger` для логирования начала/конца запроса;
- `DataBaseMetricWriterFactory` строит `DataBaseMetricWriter` для записи метрик;
- `DataBaseTracerFactory` строит `DataBaseTracer` для распределённой трассировки.

Метрики и трассировка описаны в разделе [Справочник метрик](metrics.md#r2dbc).
