---
description: "Explains Kora Vert.x database repositories, Vert.x SQL client configuration, mapping, transactions, and repository signatures. Use when working with @Repository, @Query, @Table, @Id, @Column, VertxDatabaseModule, VertxConnectionFactory."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora Vert.x database repositories, Vert.x SQL client configuration, mapping, transactions, and repository signatures; key triggers include @Repository, @Query, @Table, @Id, @Column, VertxDatabaseModule, VertxConnectionFactory, VertxRepository."
---

Модуль предоставляет реализацию репозиториев на основе реактивного `SQL`-клиента [Vert.x](https://vertx.io/docs/#databases).
[Пул](https://vertx.io/docs/vertx-pg-client/java/#_using_connection_pool) соединений Vert.x работает поверх транспорта
[Netty](netty.md). Вы описываете интерфейс репозитория и `SQL`-запросы через `@Repository` и `@Query`, а `Kora` генерирует
реализацию, которая привязывает Vert.x `Tuple`, выполняет подготовленный запрос через телеметрию, преобразует
`RowSet<Row>` и участвует в транзакциях.

Общие правила для сущностей, `@Repository`, `@Query`, `@Batch`, `UpdateCount`, макросов и других механизмов
репозиториев описаны в разделе [Общие правила баз данных](database-common.md).

## Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:database-vertx"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends VertxDatabaseModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:database-vertx")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : VertxDatabaseModule
    ```

Также **требуется предоставить** реализацию драйвера Vert.x как зависимость, версии не выше
[4.3.8](https://mvnrepository.com/artifact/io.vertx/vertx-pg-client/4.3.8), например
[vertx-pg-client](https://mvnrepository.com/artifact/io.vertx/vertx-pg-client/4.3.8) для `PostgreSQL`:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    implementation "io.vertx:vertx-pg-client:4.3.8"
    ```

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    implementation("io.vertx:vertx-pg-client:4.3.8")
    ```

Для базы данных [PostgreSQL](https://postgrespro.ru/docs/postgresql), использующей аутентификацию `SCRAM`, также
необходимо добавить зависимость [com.ongres.scram:client](https://mvnrepository.com/artifact/com.ongres.scram/client/2.1).

Зависимость [io.projectreactor:reactor-core](https://mvnrepository.com/artifact/io.projectreactor/reactor-core)
требуется только если вы используете сигнатуры методов `Mono`/`Flux`.

## Конфигурация { #configuration }

Пример полной конфигурации, описанной в классе `VertxDatabaseConfig` (указаны примеры значений или значения по умолчанию):

===! ":material-code-json: `HOCON`"

    ```javascript
    db {
        connectionUri = "postgresql://localhost:5432/postgres" //(1)!
        username = "postgres" //(2)!
        password = "postgres" //(3)!
        poolName = "kora" //(4)!
        maxPoolSize = 10 //(5)!
        connectionTimeout = "10s" //(6)!
        acquireTimeout = "10s" //(7)!
        idleTimeout = "10m" //(8)!
        cachePreparedStatements = true //(9)!
        initializationFailTimeout = "10s" //(10)!
        readinessProbe = false //(11)!
        telemetry {
            logging {
                enabled = false //(12)!
            }
            metrics {
                enabled = true //(13)!
                slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(14)!
                tags = { // (15)!
                    "key1" = "value1"
                    "key2" = "value2"
                }
            }
            tracing {
                enabled = true //(16)!
                attributes = { // (17)!
                    "key1" = "value1"
                    "key2" = "value2"
                }
            }
        }
    }
    ```

    1.  [URI](https://vertx.io/docs/vertx-pg-client/java/#_connection_uri) подключения к базе данных (`обязательная`, по умолчанию не указано)
    2.  Имя пользователя для подключения (`обязательная`, по умолчанию не указано)
    3.  Пароль пользователя для подключения (`обязательная`, по умолчанию не указано)
    4.  Имя пула соединений (`обязательная`, по умолчанию не указано)
    5.  Максимальный размер пула соединений (по умолчанию: `10`)
    6.  Максимальное время установления физического соединения (по умолчанию: `10s`)
    7.  Максимальное время получения соединения из пула; если не задано, вместо него используется `connectionTimeout` (по умолчанию не указано, необязательно)
    8.  Максимальное время простоя соединения (по умолчанию: `10m`)
    9.  Кэшировать ли подготовленные выражения (по умолчанию: `true`)
    10. Максимальное время ожидания проверки соединения `SELECT 1` при запуске сервиса; если не задано, проверка при запуске не выполняется (по умолчанию не указано, необязательно)
    11. Включить ли [пробу готовности](probes.md#readiness) для соединения с базой данных (по умолчанию: `false`)
    12. Включает логирование модуля (по умолчанию: `false`)
    13. Включает метрики модуля (по умолчанию: `true`)
    14. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    15. Настройка тегов для метрик (по умолчанию: `{}`)
    16. Включает трассировку модуля (по умолчанию: `true`)
    17. Настройка атрибутов для трассировки (по умолчанию: `{}`)

=== ":simple-yaml: `YAML`"

    ```yaml
    db:
      connectionUri: "postgresql://localhost:5432/postgres" #(1)!
      username: "postgres" #(2)!
      password: "postgres" #(3)!
      poolName: "kora" #(4)!
      maxPoolSize: 10 #(5)!
      connectionTimeout: "10s" #(6)!
      acquireTimeout: "10s" #(7)!
      idleTimeout: "10m" #(8)!
      cachePreparedStatements: true #(9)!
      initializationFailTimeout: "10s" #(10)!
      readinessProbe: false #(11)!
      telemetry:
        logging:
          enabled: false #(12)!
        metrics:
          enabled: true #(13)!
          slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(14)!
          tags: #(15)!
            key1: value1
            key2: value2
        tracing:
          enabled: true #(16)!
          attributes: #(17)!
            key1: value1
            key2: value2
    ```

    1.  [URI](https://vertx.io/docs/vertx-pg-client/java/#_connection_uri) подключения к базе данных (`обязательная`, по умолчанию не указано)
    2.  Имя пользователя для подключения (`обязательная`, по умолчанию не указано)
    3.  Пароль пользователя для подключения (`обязательная`, по умолчанию не указано)
    4.  Имя пула соединений (`обязательная`, по умолчанию не указано)
    5.  Максимальный размер пула соединений (по умолчанию: `10`)
    6.  Максимальное время установления физического соединения (по умолчанию: `10s`)
    7.  Максимальное время получения соединения из пула; если не задано, вместо него используется `connectionTimeout` (по умолчанию не указано, необязательно)
    8.  Максимальное время простоя соединения (по умолчанию: `10m`)
    9.  Кэшировать ли подготовленные выражения (по умолчанию: `true`)
    10. Максимальное время ожидания проверки соединения `SELECT 1` при запуске сервиса; если не задано, проверка при запуске не выполняется (по умолчанию не указано, необязательно)
    11. Включить ли [пробу готовности](probes.md#readiness) для соединения с базой данных (по умолчанию: `false`)
    12. Включает логирование модуля (по умолчанию: `false`)
    13. Включает метрики модуля (по умолчанию: `true`)
    14. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    15. Настройка тегов для метрик (по умолчанию: `{}`)
    16. Включает трассировку модуля (по умолчанию: `true`)
    17. Настройка атрибутов для трассировки (по умолчанию: `{}`)

Поскольку пул работает поверх транспорта [Netty](netty.md), вы также можете отдельно настроить [транспорт Netty](netty.md).

## Использование { #usage }

Репозиторий Vert.x объявляется интерфейсом с аннотацией `@Repository` и должен наследовать `VertxRepository`.
Каждый метод с аннотацией `@Query` содержит обычный `SQL`-запрос. Параметры метода подставляются в запрос по имени через
синтаксис `:parameter`, а поля объекта можно указывать через `:entity.field`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends VertxRepository {

        record Entity(String id, @Column("value1") int field1, String value2, @Nullable String value3) {}

        @Query("SELECT * FROM entities WHERE id = :id")
        Mono<Entity> findById(String id);

        @Query("SELECT * FROM entities")
        Flux<Entity> findAll();

        @Query("""
            INSERT INTO entities(id, value1, value2, value3)
            VALUES (:entity.id, :entity.field1, :entity.value2, :entity.value3)
            """)
        Mono<Void> insert(Entity entity);

        @Query("""
            INSERT INTO entities(id, value1, value2, value3)
            VALUES (:entity.id, :entity.field1, :entity.value2, :entity.value3)
            """)
        Mono<UpdateCount> insertBatch(@Batch List<Entity> entities);

        @Query("""
            UPDATE entities
            SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3
            WHERE id = :entity.id
            """)
        Mono<Void> update(Entity entity);

        @Query("DELETE FROM entities WHERE id = :id")
        Mono<Void> deleteById(String id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : VertxRepository {

        data class Entity(val id: String, @Column("value1") val field1: Int, val value2: String, val value3: String?)

        @Query("SELECT * FROM entities WHERE id = :id")
        fun findById(id: String): Mono<Entity>

        @Query("SELECT * FROM entities")
        fun findAll(): Flux<Entity>

        @Query("""
            INSERT INTO entities(id, value1, value2, value3)
            VALUES (:entity.id, :entity.field1, :entity.value2, :entity.value3)
            """)
        fun insert(entity: Entity): Mono<Void>

        @Query("""
            INSERT INTO entities(id, value1, value2, value3)
            VALUES (:entity.id, :entity.field1, :entity.value2, :entity.value3)
            """)
        fun insertBatch(@Batch entities: List<Entity>): Mono<UpdateCount>

        @Query("""
            UPDATE entities
            SET value1 = :entity.field1, value2 = :entity.value2, value3 = :entity.value3
            WHERE id = :entity.id
            """)
        fun update(entity: Entity): Mono<Void>

        @Query("DELETE FROM entities WHERE id = :id")
        fun deleteById(id: String): Mono<Void>
    }
    ```

`SQL` остается под контролем разработчика: можно использовать специфичные возможности конкретной базы данных, а `Kora`
занимается только безопасной подстановкой параметров, выполнением запроса и преобразованием результата.
Общие правила сущностей, `@Table`, `@Column`, `@Id`, `@Embedded`, `@Batch` и макросов описаны в разделе
[Общие правила баз данных](database-common.md).

Реактивные возвращаемые значения `Mono` и `Flux` являются нативными сигнатурами для этого модуля, поскольку клиент Vert.x
асинхронный. Блокирующие возвращаемые значения, такие как `Entity`, `List<Entity>`, `void` и `UpdateCount`, также
поддерживаются, но они блокируют вызывающий поток до завершения асинхронного результата, поэтому в реактивном контексте
предпочтительнее использовать реактивные сигнатуры.

## Преобразование { #mapping }

Можно переопределять преобразование разных частей [сущности](database-common.md), результата запроса и параметров запроса.
Для этого `Kora` предоставляет несколько интерфейсов преобразователей.

### Результат { #result }

Используйте `VertxRowSetMapper<T>`, когда требуется управлять всем `io.vertx.sqlclient.RowSet<Row>`.
Такой преобразователь получает весь набор результата и сам решает, как его прочитать и что вернуть:

===! ":fontawesome-brands-java: `Java`"

    ```java
    final class ResultMapper implements VertxRowSetMapper<Map<Integer, List<EntityPart>>> {

        @Override
        public Map<Integer, List<EntityPart>> apply(RowSet<Row> rows) {
            var result = new LinkedHashMap<Integer, List<EntityPart>>(rows.size());
            for (Row row : rows) {
                var entityPart = new EntityPart(row.getString(0), row.getInteger(1));
                var entityParts = result.computeIfAbsent(entityPart.field1(), k -> new ArrayList<>());
                entityParts.add(entityPart);
            }
            return result;
        }
    }

    @Repository
    public interface EntityRepository extends VertxRepository {

        @Mapping(ResultMapper.class)
        @Query("SELECT id, value1 FROM entities")
        Mono<Map<Integer, List<EntityPart>>> findAllParts();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class ResultMapper : VertxRowSetMapper<Map<Int, List<EntityPart>>> {
        override fun apply(rows: RowSet<Row>): Map<Int, List<EntityPart>> {
            val result = LinkedHashMap<Int, MutableList<EntityPart>>(rows.size())
            for (row in rows) {
                val entityPart = EntityPart(row.getString(0), row.getInteger(1))
                result.computeIfAbsent(entityPart.field1) { ArrayList() }.add(entityPart)
            }
            return result
        }
    }

    @Repository
    interface EntityRepository : VertxRepository {

        @Mapping(ResultMapper::class)
        @Query("SELECT id, value1 FROM entities")
        fun findAllParts(): Mono<Map<Int, List<EntityPart>>>
    }
    ```

В большинстве случаев управлять всем `RowSet<Row>` не требуется.
Достаточно предоставить [VertxRowMapper](#row), и `Kora` автоматически адаптирует его к типу возвращаемого значения метода
с помощью встроенных вспомогательных методов `VertxRowSetMapper`: `singleRowSetMapper` (одиночный `T`), `listRowSetMapper`
(`List<T>`) и `optionalRowSetMapper` (`Optional<T>`). Также есть `VertxRowSetMapper.extractUpdateCount`, который адаптирует результат к `UpdateCount`.

### Строка { #row }

Используйте `VertxRowMapper<T>`, когда требуется вручную преобразовать одну строку результата.
Колонки читаются из `io.vertx.sqlclient.Row` по типу и индексу (начиная с `0`):

===! ":fontawesome-brands-java: `Java`"

    ```java
    final class RowMapper implements VertxRowMapper<EntityPart> {

        @Override
        public EntityPart apply(Row row) {
            return new EntityPart(row.get(String.class, 0), row.get(Integer.class, 1));
        }
    }

    @Repository
    public interface EntityRepository extends VertxRepository {

        @Mapping(RowMapper.class)
        @Query("SELECT id, value1 FROM entities")
        Flux<EntityPart> findAllParts();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class RowMapper : VertxRowMapper<EntityPart> {

        override fun apply(row: Row): EntityPart {
            return EntityPart(row.get(String::class.java, 0), row.get(Integer::class.java, 1))
        }
    }

    @Repository
    interface EntityRepository : VertxRepository {

        @Mapping(RowMapper::class)
        @Query("SELECT id, value1 FROM entities")
        fun findAllParts(): Flux<EntityPart>
    }
    ```

### Колонка { #column }

Используйте `VertxResultColumnMapper<T>`, когда требуется вручную преобразовать значение отдельной колонки по её индексу:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class ColumnMapper implements VertxResultColumnMapper<Entity.FieldType> {

        private static final Entity.FieldType[] ALL = Entity.FieldType.values();

        @Nullable
        @Override
        public Entity.FieldType apply(Row row, int index) {
            var fieldAsInt = row.get(Integer.class, index);
            if (fieldAsInt == null) {
                return null;
            }
            for (var type : ALL) {
                if (type.code() == fieldAsInt) {
                    return type;
                }
            }
            return Entity.FieldType.UNKNOWN;
        }
    }

    @Table("entities")
    public record Entity(String id, @Mapping(ColumnMapper.class) @Column("value1") FieldType field1) {

        enum FieldType {
            UNKNOWN(-10), ONE(1), TWO(2);

            private final int code;

            FieldType(int code) { this.code = code; }

            public int code() { return code; }
        }
    }

    @Repository
    public interface EntityRepository extends VertxRepository {

        @Query("SELECT id, value1 FROM entities")
        Flux<Entity> findAll();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class ColumnMapper : VertxResultColumnMapper<Entity.FieldType> {

        override fun apply(row: Row, index: Int): Entity.FieldType? {
            val fieldAsInt = row.get(Integer::class.java, index) ?: return null
            return Entity.FieldType.entries.firstOrNull { it.code == fieldAsInt } ?: Entity.FieldType.UNKNOWN
        }
    }

    @Table("entities")
    data class Entity(
        val id: String,
        @Mapping(ColumnMapper::class) @Column("value1") val field1: FieldType
    ) {
        enum class FieldType(val code: Int) { UNKNOWN(-10), ONE(1), TWO(2) }
    }

    @Repository
    interface EntityRepository : VertxRepository {

        @Query("SELECT id, value1 FROM entities")
        fun findAll(): Flux<Entity>
    }
    ```

В отличие от некоторых других модулей баз данных, здесь преобразователь колонки читает по числовому `index`, а не по имени колонки.

### Параметр { #parameter }

Используйте `VertxParameterColumnMapper<T>`, когда требуется вручную преобразовать значение параметра запроса.
Преобразователь возвращает исходное значение, которое `Kora` привязывает в Vert.x `Tuple`; для значения `null` возвращайте `null`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class ParameterMapper implements VertxParameterColumnMapper<Entity.FieldType> {

        @Nullable
        @Override
        public Object apply(@Nullable Entity.FieldType fieldType) {
            return (fieldType == null) ? null : fieldType.code();
        }
    }

    @Repository
    public interface EntityRepository extends VertxRepository {

        @Query("UPDATE entities SET value1 = :fieldType WHERE id = :id")
        UpdateCount updateFieldType(String id, @Mapping(ParameterMapper.class) Entity.FieldType fieldType);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class ParameterMapper : VertxParameterColumnMapper<Entity.FieldType?> {

        override fun apply(fieldType: Entity.FieldType?): Any? {
            return fieldType?.code
        }
    }

    @Repository
    interface EntityRepository : VertxRepository {

        @Query("UPDATE entities SET value1 = :fieldType WHERE id = :id")
        fun updateFieldType(id: String, @Mapping(ParameterMapper::class) fieldType: Entity.FieldType): UpdateCount
    }
    ```

Преобразователь колонки результата и преобразователь параметра можно сочетать на одном поле сущности.
Это удобно для преобразования, например, перечисления как при чтении строки, так и при привязке параметра:

===! ":fontawesome-brands-java: `Java`"

    ```java
    record Entity(String id,
                  @Mapping(FieldTypeColumnMapper.class)
                  @Mapping(FieldTypeParameterMapper.class)
                  @Column("value1") FieldType field1) { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class Entity(
        val id: String,
        @Mapping(FieldTypeColumnMapper::class)
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
    * Buffer (`io.vertx.core.buffer.Buffer`)
    * String
    * BigInteger
    * BigDecimal
    * UUID
    * LocalDate
    * LocalDateTime

    Для остальных типов используйте собственные преобразователи `VertxResultColumnMapper<T>` / `VertxParameterColumnMapper<T>`
    либо `VertxRowMapper<T>` / `VertxRowSetMapper<T>`.

## Транзакции { #transactions }

Для объединения запросов в транзакцию `Kora` предоставляет интерфейс `VertxConnectionFactory`
в рамках контракта `VertxRepository`, получаемый через `getVertxConnectionFactory()`.
Все методы репозитория, вызванные внутри лямбды транзакции, выполняются в этой самой транзакции.

Для того чтобы выполнять запросы транзакционно, используйте `inTx`. Лямбда получает `io.vertx.sqlclient.SqlConnection`
и должна вернуть `java.util.concurrent.CompletionStage<T>`, поэтому реактивные результаты `Mono` из методов репозитория
нужно преобразовывать через `.toFuture()`. Если на текущем `Context` уже есть активная транзакция, вложенный вызов `inTx`
использует то же соединение и не открывает новую транзакцию.

Транзакционную последовательность операций можно оставлять внутри самого репозитория с помощью обычного метода с реализацией.
Такой подход удобен, когда нужно оставить несколько `@Query`-методов рядом с остальными запросами репозитория,
не вынося техническую работу с базой данных в сервисный слой.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends VertxRepository {

        @Query("INSERT INTO entities(id, value2) VALUES (:entity.id, :entity.value2)")
        Mono<Void> insert(Entity entity);

        @Query("UPDATE entities SET value2 = :value2 WHERE id = :id")
        Mono<UpdateCount> updateValue(String id, String value2);

        default CompletionStage<List<Entity>> saveAll(Entity one, Entity two) {
            return getVertxConnectionFactory().inTx(connection ->
                insert(one) //(1)!
                    .then(updateValue(two.id(), two.value2())) //(2)!
                    .thenReturn(List.of(one, two))
                    .toFuture());
        }
    }
    ```

    1. Будет выполнено в рамках транзакции или откатится, если вся цепочка сигнализирует об ошибке
    2. Будет выполнено в рамках транзакции или откатится, если вся цепочка сигнализирует об ошибке

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : VertxRepository {

        @Query("INSERT INTO entities(id, value2) VALUES (:entity.id, :entity.value2)")
        fun insert(entity: Entity): Mono<Void>

        @Query("UPDATE entities SET value2 = :value2 WHERE id = :id")
        fun updateValue(id: String, value2: String): Mono<UpdateCount>

        fun saveAll(one: Entity, two: Entity): CompletionStage<List<Entity>> {
            return vertxConnectionFactory.inTx { _ ->
                insert(one) //(1)!
                    .then(updateValue(two.id, two.value2)) //(2)!
                    .thenReturn(listOf(one, two))
                    .toFuture()
            }
        }
    }
    ```

    1. Будет выполнено в рамках транзакции или откатится, если вся цепочка сигнализирует об ошибке
    2. Будет выполнено в рамках транзакции или откатится, если вся цепочка сигнализирует об ошибке

Транзакция фиксируется при успешном завершении возвращаемого `CompletionStage`.
Если `CompletionStage` завершается с ошибкой, транзакция откатывается, а ошибка пробрасывается дальше, поэтому все изменения
в базе данных, сделанные в рамках транзакции, не применяются.

### Ручное управление соединением { #connection }

Если для запроса нужна более сложная логика или запросы вне репозитория, можно работать напрямую с `io.vertx.sqlclient.SqlConnection`.
Метод `withConnection` выполняет лямбду с соединением, но сам по себе не открывает транзакцию:

- если в текущем `Context` уже есть соединение, метод передает в лямбду это текущее соединение;
- если соединения в текущем `Context` нет, метод берет новое соединение из пула, кладет его в `Context` на время выполнения лямбды и закрывает после завершения;
- повторные вызовы `withConnection` и методы репозитория внутри этой лямбды используют то же текущее соединение.

И `withConnection`, и `inTx` возвращают `CompletionStage<T>`, а метод `inTx` построен поверх `withConnection`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final EntityRepository repository;

        public SomeService(EntityRepository repository) {
            this.repository = repository;
        }

        public CompletionStage<List<Entity>> loadAll() {
            return repository.getVertxConnectionFactory().withConnection(connection -> {
                // do some work, returns CompletionStage
            });
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(private val repository: EntityRepository) {

        fun loadAll(): CompletionStage<List<Entity>> {
            return repository.vertxConnectionFactory.withConnection { connection ->
                // do some work, returns CompletionStage
            }
        }
    }
    ```

`VertxConnectionFactory` также предоставляет более низкоуровневые методы доступа: `currentConnection()` возвращает соединение,
привязанное к текущему `Context` (или `null`, если его нет), `newConnection()` получает новый `CompletionStage<SqlConnection>`
из пула, `pool()` возвращает исходный `io.vertx.sqlclient.Pool`, а `telemetry()` возвращает телеметрию базы данных.

## Ручной запрос с телеметрией { #query }

Если запрос сложно выразить одним статическим `@Query`, можно сделать обычный метод с реализацией и самостоятельно собрать
`SQL`. У фабрики нет метода `query`; вместо этого используйте вспомогательный класс `VertxRepositoryHelper`, чтобы выполнить
запрос через телеметрию Kora на текущем или новом соединении.

`VertxRepositoryHelper.completionStage` принимает четыре аргумента:

- `VertxConnectionFactory` (из `getVertxConnectionFactory()`);
- `QueryContext` с идентификатором запроса и итоговым `SQL`. Идентификатор попадает в телеметрию, поэтому для него удобно использовать стабильное имя вида `Repository.method`;
- Vert.x `Tuple` с привязанными значениями параметров;
- `VertxRowSetMapper<T>`, который читает `RowSet<Row>` и формирует возвращаемое значение.

Если соединение уже привязано к текущему `Context` (например, внутри `inTx` или `withConnection`), запрос выполняется на этом
соединении; иначе новое соединение берется из пула и закрывается после завершения.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface EntityRepository extends VertxRepository {

        default CompletionStage<List<Entity>> findByFilter(@Nullable String name, boolean onlyActive) {
            var sql = new StringBuilder("SELECT id, name FROM entities WHERE 1 = 1");
            var params = new ArrayList<Object>();

            if (name != null) {
                params.add(name);
                sql.append(" AND name = $").append(params.size());
            }
            if (onlyActive) {
                sql.append(" AND active = true");
            }

            var queryContext = new QueryContext("EntityRepository.findByFilter", sql.toString());
            return VertxRepositoryHelper.completionStage(
                getVertxConnectionFactory(),
                queryContext,
                Tuple.from(params),
                rows -> {
                    var result = new ArrayList<Entity>(rows.size());
                    for (var row : rows) {
                        result.add(new Entity(row.getString(0), row.getString(1)));
                    }
                    return result;
                }
            );
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface EntityRepository : VertxRepository {

        fun findByFilter(name: String?, onlyActive: Boolean): CompletionStage<List<Entity>> {
            val sql = StringBuilder("SELECT id, name FROM entities WHERE 1 = 1")
            val params = mutableListOf<Any>()

            if (name != null) {
                params += name
                sql.append(" AND name = $").append(params.size)
            }
            if (onlyActive) {
                sql.append(" AND active = true")
            }

            val queryContext = QueryContext("EntityRepository.findByFilter", sql.toString())
            return VertxRepositoryHelper.completionStage(
                vertxConnectionFactory,
                queryContext,
                Tuple.from(params)
            ) { rows ->
                rows.map { row -> Entity(row.getString(0), row.getString(1)) }
            }
        }
    }
    ```

Если вы предпочитаете реактивные типы возвращаемых значений, используйте вместо этого `VertxRepositoryHelper.Reactor.mono`
(возвращает `Mono<T>` с `VertxRowSetMapper`) или `VertxRepositoryHelper.Reactor.flux` (возвращает `Flux<T>` с
`VertxRowMapper`). Это продвинутый путь; для статических запросов предпочтительнее обычные `@Query`-методы.

## Выборка по списку { #select-by-list }

Иногда требуется выборка строк по списку значений.
`Kora` выполняет преобразования во время компиляции и не переписывает `SQL` во время работы, поэтому для параметра-списка
нужен собственный преобразователь, который привязывает всю коллекцию как одно значение.

Пример ниже показывает `Postgres` через массив, привязываемый с помощью `ANY(:ids)`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class ListOfStringParameterMapper implements VertxParameterColumnMapper<List<String>> {

        @Override
        public Object apply(@Nullable List<String> value) {
            return value == null ? null : value.toArray(String[]::new);
        }
    }

    @Repository
    public interface EntityRepository extends VertxRepository {

        @Query("SELECT id, name FROM entities WHERE id = ANY(:ids)")
        Flux<Entity> findAllByIds(@Mapping(ListOfStringParameterMapper.class) List<String> ids);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class ListOfStringParameterMapper : VertxParameterColumnMapper<List<String>?> {

        override fun apply(value: List<String>?): Any? {
            return value?.toTypedArray()
        }
    }

    @Repository
    interface EntityRepository : VertxRepository {

        @Query("SELECT id, name FROM entities WHERE id = ANY(:ids)")
        fun findAllByIds(@Mapping(ListOfStringParameterMapper::class) ids: List<String>): Flux<Entity>
    }
    ```

## Сигнатуры { #signatures }

Доступные сигнатуры для методов репозитория из коробки.
Поскольку клиент Vert.x реактивен нативно, для асинхронных сигнатур не требуется компонент `Executor`.

===! ":fontawesome-brands-java: `Java`"

    Под `T` подразумевается тип возвращаемого значения, либо `List<T>`, либо `Void`, либо `UpdateCount`.

    - `T myMethod()`
    - `@Nullable T myMethod()`
    - `Optional<T> myMethod()`
    - `CompletionStage<T> myMethod()`
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (надо подключить [зависимость](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))
    - `Flux<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (надо подключить [зависимость](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

=== ":simple-kotlin: `Kotlin`"

    Под `T` подразумевается тип возвращаемого значения, либо `T?`, либо `List<T>`, либо `Unit`, либо `UpdateCount`.

    - `myMethod(): T`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (надо подключить [зависимость](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) как `implementation`)
    - `myMethod(): Flow<T>` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (надо подключить [зависимость](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) как `implementation`)

## Телеметрия { #telemetry }

Vert.x драйвер использует общий контракт телеметрии для логирования, метрик и трассировки запросов.
Конфигурация телеметрии (секция `telemetry { logging / metrics / tracing }`) описана в разделе [Конфигурация](#configuration).
Точки расширения находятся в `ru.tinkoff.kora.database.common.telemetry`.

Для каждого запроса создаётся `DataBaseTelemetry.DataBaseTelemetryContext`, который закрывается по завершении запроса.
Выполняемый запрос описывается `QueryContext(queryId, sql, operation)`, где `queryId` — стабильный идентификатор запроса,
`sql` — итоговый текст запроса, а `operation` по умолчанию равно `db_query`.

Фабрика по умолчанию `DefaultDataBaseTelemetryFactory` объединяет три фабрики:
- `DataBaseLoggerFactory` строит `DataBaseLogger` для логирования начала/конца запроса;
- `DataBaseMetricWriterFactory` строит `DataBaseMetricWriter` для записи метрик;
- `DataBaseTracerFactory` строит `DataBaseTracer` для распределённой трассировки.

Метрики и трассировка описаны в разделе [Справочник метрик](metrics.md#vertx).
