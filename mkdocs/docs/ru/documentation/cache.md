---
description: "Explains Kora cache module, cache annotations, Caffeine and Redis cache backends, cache key mapping, telemetry, invalidation, and async cache signatures. Use when working with @Cache, @Cacheable, @CachePut, @CacheInvalidate, CaffeineCacheModule, RedisCacheModule, CacheKeyMapper, LoadableCache."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora cache module, cache annotations, Caffeine and Redis cache backends, cache key mapping, telemetry, invalidation, and async cache signatures; key triggers include @Cache, @Cacheable, @CachePut, @CacheInvalidate, CaffeineCacheModule, RedisCacheModule, CacheKeyMapper, LoadableCache."
---

Модуль предоставляет типизированные кэши для хранения результатов вычислений и повторно используемых данных,
чтобы дорогостоящие операции не приходилось выполнять при каждом обращении. Кэш можно использовать декларативно через аннотации над методами
или императивно через внедряемый интерфейс, а в качестве хранилищ доступны локальный `Caffeine` и внешний `Redis`.
Локальный `Caffeine` полезен для быстрого внутрипроцессного хранения, а `Redis` подходит для общего кэша, используемого несколькими экземплярами приложения.

Если нужен пошаговый разбор перед справочным описанием, смотрите [Кэш](../guides/cache.md) и [Многоуровневый кэш](../guides/cache-multi-level.md).

## Caffeine { #caffeine }

Реализация на основе библиотеки [Caffeine](https://github.com/ben-manes/caffeine) для кэша приложения в оперативной памяти.

### Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:cache-caffeine"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends CaffeineCacheModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:cache-caffeine")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : CaffeineCacheModule
    ```

### Конфигурация { #configuration }

Пример полной конфигурации кэша по пути `mycache.config`; параметры описаны в классе `CaffeineCacheConfig` (приведены примерные значения или значения по умолчанию):

===! ":material-code-json: `HOCON`"

    ```javascript
    mycache {
        config {
            expireAfterWrite = "10s" //(1)!
            expireAfterAccess = "10s" //(2)!
            initialSize = 10 //(3)!
            maximumSize = 100000 //(4)!
        }
    }
    ```

    1.  Время, по истечении которого значение удаляется из кэша; отсчитывается после записи значения (по умолчанию не указано, опционально)
    2.  Время, по истечении которого значение удаляется из кэша; отсчитывается после чтения значения (по умолчанию не указано, опционально)
    3.  Начальный размер кэша, помогает избежать изменения размера при быстром росте количества значений (по умолчанию не указано, опционально)
    4.  Максимальный размер кэша; при достижении границы **или немного раньше** вытесняются [наименее актуальные значения](https://blog.skillfactory.ru/glossary/lru/) (по умолчанию: `100000`)

=== ":simple-yaml: `YAML`"

    ```yaml
    mycache:
      config:
        expireAfterWrite: "10s" #(1)!
        expireAfterAccess: "10s" #(2)!
        initialSize: 10 #(3)!
        maximumSize: 100000 #(4)!
    ```

    1.  Время, по истечении которого значение удаляется из кэша; отсчитывается после записи значения (по умолчанию не указано, опционально)
    2.  Время, по истечении которого значение удаляется из кэша; отсчитывается после чтения значения (по умолчанию не указано, опционально)
    3.  Начальный размер кэша, помогает избежать изменения размера при быстром росте количества значений (по умолчанию не указано, опционально)
    4.  Максимальный размер кэша; при достижении границы **или немного раньше** вытесняются [наименее актуальные значения](https://blog.skillfactory.ru/glossary/lru/) (по умолчанию: `100000`)

Базовый кэш `Caffeine` создается фабрикой `CaffeineCacheFactory`, предоставляемой как `@DefaultComponent`.
Если требуется настройка сверх перечисленных выше опций конфигурации (например, собственное вытеснение, слабые ключи или собственный весовой оценщик),
зарегистрируйте собственный компонент `CaffeineCacheFactory`, чтобы переопределить фабрику по умолчанию и настроить построитель `Caffeine` напрямую.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MyCaffeineCacheFactory implements CaffeineCacheFactory {

        @Nonnull
        @Override
        public <K, V> Cache<K, V> build(@Nonnull String name, @Nonnull CaffeineCacheConfig config) {
            var builder = Caffeine.newBuilder().weakKeys();
            if (config.expireAfterWrite() != null) {
                builder.expireAfterWrite(config.expireAfterWrite());
            }
            builder.maximumSize(config.maximumSize());
            return builder.build();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyCaffeineCacheFactory : CaffeineCacheFactory {

        override fun <K, V> build(name: String, config: CaffeineCacheConfig): Cache<K, V> {
            val builder = Caffeine.newBuilder().weakKeys()
            config.expireAfterWrite()?.let { builder.expireAfterWrite(it) }
            builder.maximumSize(config.maximumSize())
            return builder.build()
        }
    }
    ```

## Redis { #redis }

Реализация на основе базы данных в оперативной памяти [Redis](https://redis.io/docs/about/) и драйвера подключения [Lettuce](https://github.com/lettuce-io/lettuce-core).

### Подключение { #dependency-2 }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:cache-redis"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends RedisCacheModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:cache-redis")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : RedisCacheModule
    ```

### Конфигурация { #configuration-2 }

Драйвер `Lettuce` необходимо настроить отдельно для подключения к `Redis`.
Для всех кэшей `Redis` используется одно подключение.

Пример полной конфигурации драйвера `Lettuce`; параметры описаны в классе `LettuceClientConfig` (приведены примерные значения или значения по умолчанию):

===! ":material-code-json: `HOCON`"

    ```javascript
    lettuce {
        uri = "redis://localhost:6379" //(1)!
        user = "admin" //(2)!
        password = "12345" //(3)!
        database = 0 //(4)!
        protocol = "RESP3" //(5)!
        socketTimeout = "10s" //(6)!
        commandTimeout = "60s" //(7)!
        forceClusterClient = false //(8)!
        ssl {
            ciphers = [ "TLS_CHACHA20_POLY1305_SHA256" ] //(9)!
            handshakeTimeout = "10s" //(10)!
        }
        telemetry {
            logging {
                enabled = false //(11)!
            }
            metrics {
                enabled = true //(12)!
                slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(13)!
                tags = { // (14)!
                    "key1" = "value1"
                    "key2" = "value2"
                }
            }
            tracing {
                enabled = true //(15)!
                attributes = { // (16)!
                    "key1" = "value1"
                    "key2" = "value2"
                }
            }
        }
    }
    ```

    1.  `URI` для подключения к `Redis` (`обязательный`, по умолчанию не указан).
        Подключение к одному серверу: `redis://localhost:6379`.
        Подключение к нескольким серверам: `redis://localhost:6379,localhost:6380`.
        Подключение с `SSL`: `rediss://localhost:6380`.
        Подключение с `TLS`: `redis+tls://localhost:6380`.
    2.  Имя пользователя для подключения (по умолчанию не указано, опционально)
    3.  Пароль пользователя для подключения (по умолчанию не указано, опционально)
    4.  Номер базы данных для подключения (по умолчанию не указано, опционально)
    5.  Протокол подключения, может быть `RESP2` или `RESP3` (по умолчанию: `RESP3`)
    6.  Таймаут подключения сокета (по умолчанию: `10s`)
    7.  Таймаут выполнения команды (по умолчанию: `60s`)
    8.  Создавать кластерный клиент даже при одном `URI` подключения (по умолчанию: `false`)
    9.  Алгоритмы шифрования для защищенного соединения между клиентом и сервером (по умолчанию: `[]`)
    10. Таймаут установки защищенного соединения с сервером (по умолчанию: `10s`)
    11. Включает логирование модуля (по умолчанию: `false`)
    12. Включает метрики модуля (по умолчанию: `true`)
    13. Настройка [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    14. Настройка тегов для метрик (по умолчанию: `{}`)
    15. Включает трассировку модуля (по умолчанию: `true`)
    16. Настройка атрибутов для трассировки (по умолчанию: `{}`)
 
=== ":simple-yaml: `YAML`"

    ```yaml
    lettuce:
      uri: "redis://localhost:6379" #(1)!
      user: "admin" #(2)!
      password: "12345" #(3)!
      database: 0 #(4)!
      protocol: "RESP3" #(5)!
      socketTimeout: "10s" #(6)!
      commandTimeout: "60s" #(7)!
      forceClusterClient: false #(8)!
      ssl:
        ciphers:
          - "TLS_CHACHA20_POLY1305_SHA256" #(9)!
        handshakeTimeout: "10s" #(10)!
      telemetry:
        logging:
          enabled: false #(11)!
        metrics:
          enabled: true #(12)!
          slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(13)!
          tags: #(14)!
            key1: value1
            key2: value2
        tracing:
          enabled: true #(15)!
          attributes: #(16)!
            key1: value1
            key2: value2
    ```

    1.  `URI` для подключения к `Redis` (`обязательный`, по умолчанию не указан).
        Подключение к одному серверу: `redis://localhost:6379`.
        Подключение к нескольким серверам: `redis://localhost:6379,localhost:6380`.
        Подключение с `SSL`: `rediss://localhost:6380`.
        Подключение с `TLS`: `redis+tls://localhost:6380`.
    2.  Имя пользователя для подключения (по умолчанию не указано, опционально)
    3.  Пароль пользователя для подключения (по умолчанию не указано, опционально)
    4.  Номер базы данных для подключения (по умолчанию не указано, опционально)
    5.  Протокол подключения, может быть `RESP2` или `RESP3` (по умолчанию: `RESP3`)
    6.  Таймаут подключения сокета (по умолчанию: `10s`)
    7.  Таймаут выполнения команды (по умолчанию: `60s`)
    8.  Создавать кластерный клиент даже при одном `URI` подключения (по умолчанию: `false`)
    9.  Алгоритмы шифрования для защищенного соединения между клиентом и сервером (по умолчанию: `[]`)
    10. Таймаут установки защищенного соединения с сервером (по умолчанию: `10s`)
    11. Включает логирование модуля (по умолчанию: `false`)
    12. Включает метрики модуля (по умолчанию: `true`)
    13. Настройка [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    14. Настройка тегов для метрик (по умолчанию: `{}`)
    15. Включает трассировку модуля (по умолчанию: `true`)
    16. Настройка атрибутов для трассировки (по умолчанию: `{}`)

Конфигурация кэша `Redis` определяет поведение конкретного кэша.

Пример полной конфигурации кэша по пути `mycache.config`; параметры описаны в классе `RedisCacheConfig` (приведены примерные значения):

===! ":material-code-json: `HOCON`"

    ```javascript
    mycache {
        config {    
            expireAfterWrite = "10s" //(1)!
            expireAfterAccess = "10s" //(2)!
            keyPrefix = "mykey" //(3)!
        }
    }
    ```

    1.  Задает время [устаревания](https://redis.io/commands/psetex/) значения при записи (по умолчанию не указано, опционально)
    2.  Задает время [устаревания](https://redis.io/commands/getex/) значения при чтении (по умолчанию не указано, опционально)
    3.  Префикс ключа для конкретного кэша, используется во избежание коллизий ключей в одной базе данных `Redis`; может быть пустой строкой, тогда ключи будут без префикса (`обязательный`, по умолчанию не указан)

=== ":simple-yaml: `YAML`"

    ```yaml
    mycache:
      config:
        expireAfterWrite: "10s" #(1)!
        expireAfterAccess: "10s" #(2)!
        keyPrefix: "mykey" #(3)!
    ```

    1.  Задает время [устаревания](https://redis.io/commands/psetex/) значения при записи (по умолчанию не указано, опционально)
    2.  Задает время [устаревания](https://redis.io/commands/getex/) значения при чтении (по умолчанию не указано, опционально)
    3.  Префикс ключа для конкретного кэша, используется во избежание коллизий ключей в одной базе данных `Redis`; может быть пустой строкой, тогда ключи будут без префикса (`обязательный`, по умолчанию не указан)

Метрики модуля описаны в разделе [Справочник по метрикам](metrics.md#cache).
Собственную телеметрию кэша для обоих хранилищ можно подключить, зарегистрировав nullable-компоненты `CacheMetrics` и `CacheTracer`,
которые получают `CacheTelemetryOperation` с именем операции, именем кэша и источником.

### Мапперы ключей и значений { #redis-mappers }

`Redis` хранит ключи и значения как массивы байтов, поэтому `RedisCache` использует два вида мапперов:

- `RedisCacheKeyMapper<K>` преобразует ключ кэша в `byte[]`.
- `RedisCacheValueMapper<V>` записывает значение кэша в `byte[]` и читает его обратно.

Обычные ключи строятся через `RedisCacheKeyMapper` для типа ключа. Встроенные мапперы доступны для `String`, `byte[]`,
чисел, `BigInteger`, `BigDecimal`, `UUID`, `Boolean`, `Character`, `Instant`, `LocalDateTime`, `LocalDate`, `ZonedDateTime`,
`Duration`, `Period`, `Enum` и `Collection<T>`, когда для `T` также доступен маппер.
Для `Enum` используется `toString()`, поэтому его можно переопределить, когда требуется другой формат ключа.

Для значений встроенные реализации `RedisCacheValueMapper` доступны для тех же простых типов, типов даты/времени, `Enum` и `byte[]`.
Для остальных типов используется маппер на основе `JsonWriter<V>` и `JsonReader<V>`, когда для типа доступна сериализация в JSON.
Если требуется другое представление, зарегистрируйте собственный компонент `RedisCacheValueMapper<V>` или `RedisCacheKeyMapper<K>`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class UserIdRedisKeyMapper implements RedisCacheKeyMapper<UserId> {

        @Nonnull
        @Override
        public byte[] apply(@Nullable UserId key) {
            return key == null
                ? "NUL".getBytes(StandardCharsets.UTF_8)
                : key.value().getBytes(StandardCharsets.UTF_8);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class UserIdRedisKeyMapper : RedisCacheKeyMapper<UserId> {

        override fun apply(key: UserId?): ByteArray {
            return key?.value?.toByteArray(Charsets.UTF_8)
                ?: "NUL".toByteArray(Charsets.UTF_8)
        }
    }
    ```

Частый случай — хранение значения-объекта в виде `JSON`. Пометьте тип значения аннотацией `@Json`: `Kora` генерирует для него `JsonWriter` и `JsonReader`,
а `RedisCacheModule` автоматически предоставляет подходящий `RedisCacheValueMapper<V>` (`jsonRedisValueMapper`), поэтому для типов, сериализуемых в `JSON`, ручной маппер не нужен.
Чтобы использовать для такого типа другое представление, зарегистрируйте собственный компонент `RedisCacheValueMapper<V>`, который переопределяет маппер `JSON` по умолчанию.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
    public record UserData(String id, String name) { }

    @Cache("mycache.config")
    public interface MyCache extends RedisCache<String, UserData> { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    data class UserData(val id: String, val name: String)

    @Cache("mycache.config")
    interface MyCache : RedisCache<String, UserData>
    ```

Для составного ключа на основе `record` или `data class` Kora генерирует отдельный `RedisCacheKeyMapper` для всего ключа целиком.
Он получает маппер для каждого поля, преобразует каждое поле в `byte[]` и соединяет части с помощью `RedisCacheKeyMapper.DELIMITER`.
Порядок частей соответствует порядку компонентов `record` или свойств `data class`.

Для одиночного ключа встроенные реализации `RedisCacheKeyMapper` могут кодировать `null` специальным байтовым значением.
В составном ключе результат маппинга каждого поля должен быть не `null`: если собственный `RedisCacheKeyMapper` для поля возвращает `null`,
создание ключа завершается ошибкой. Для опциональных полей в составном ключе собственный маппер должен явно кодировать `null`
стабильным байтовым значением.

#### Конфигуратор { #configurator }

Можно зарегистрировать `LettuceConfigurator`, чтобы настроить клиент `Lettuce` до его создания.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MyLettuceConfigurator implements LettuceConfigurator {
        @Override
        public DefaultClientResources.Builder configure(DefaultClientResources.Builder resourceBuilder) {
            return resourceBuilder;
        }

        @Override
        public ClusterClientOptions.Builder configure(ClusterClientOptions.Builder clusterBuilder) {
            return clusterBuilder;
        }

        @Override
        public ClientOptions.Builder configure(ClientOptions.Builder clientBuilder) {
            return clientBuilder;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class MyLettuceConfigurator : LettuceConfigurator {

        override fun configure(resourceBuilder: DefaultClientResources.Builder): DefaultClientResources.Builder {
            return resourceBuilder
        }

        override fun configure(clusterBuilder: ClusterClientOptions.Builder): ClusterClientOptions.Builder {
            return clusterBuilder
        }

        override fun configure(clientBuilder: ClientOptions.Builder): ClientOptions.Builder {
            return clientBuilder
        }
    }
    ```

Для продвинутых сценариев за пределами типизированного кэша для внедрения доступен `RedisCacheClient` — низкоуровневый клиент, работающий с сырыми `byte[]`
(`scan`/`get`/`mget`/`getex`/`set`/`mset`/`psetex`/`del`/`flushAll`) поверх общего подключения `Lettuce`; именно на этом клиенте построен `RedisCache`.

## Использование { #usage }

Создание кэша потребует регистрации типизированного контракта `@Cache`.
Интерфейс контракта должен наследовать одну из реализаций `Kora`: `CaffeineCache` или `RedisCache`.
Для такого `@Cache` генерируется реализация и добавляется в граф, поэтому его можно внедрять как зависимость.

Аргумент `value` в `@Cache` определяет полный путь к конфигурации конкретного кэша.
Он указывает на объект конфигурации этого кэша, поэтому ключи конфигурации могут располагаться под вложенным путем, таким как `mycache.config { ... }`,
либо плоско прямо под путем, таким как `my-cache { ... }`, как используется в примерах проектов. Обе формы допустимы; выберите одну и держите ключи конфигурации под ней.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Cache("mycache.config")
    public interface MyCache extends CaffeineCache<String, String> { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Cache("mycache.config")
    interface MyCache : CaffeineCache<String, String>
    ```

### Опциональные значения { #optional-values }

Если метод `Java` возвращает `Optional<T>`, аспект кэширования может работать с такой сигнатурой напрямую.
То же правило применяется к асинхронным обёрткам, например `CompletionStage<Optional<T>>` и `Mono<Optional<T>>`.
Сам тип значения кэша может быть либо `T`, либо `Optional<T>`:

- `CaffeineCache<String, String>` и метод `Optional<String> get(String key)`;
- `CaffeineCache<String, Optional<String>>` и метод `String get(String key)`;
- `CaffeineCache<String, Optional<String>>` и метод `Optional<String> get(String key)`.

Для `@Cacheable` это позволяет отличить отсутствующую запись в кэше от результата метода, который также означает отсутствие данных.
Для `@CachePut` результат `Optional<T>` обрабатывается согласно типу значения кэша: если кэш хранит `Optional<T>`, сохраняется сам `Optional`,
а если кэш хранит `T`, сохраняется только присутствующее значение.

### Императивный подход { #imperative }

Кэши доступны для внедрения как зависимости по интерфейсу и могут использоваться совместно с декларативными операциями.

`CaffeineCache` предоставляет контракт `Cache` для синхронных операций и дополнительный метод `getAll()`.
`RedisCache` предоставляет `Cache` и `AsyncCache`: его можно использовать синхронно и асинхронно через `CompletionStage`.

`Cache` предоставляет `get(...)`, `put(...)`, `computeIfAbsent(...)`, `invalidate(...)`, `invalidateAll(...)`,
а также пакетные варианты для коллекции ключей или отображения значений. `AsyncCache` предоставляет те же операции с суффиксом `Async`.
Методы `computeIfAbsent(...)` сначала пытаются получить значение из кэша; при промахе они вызывают переданную функцию загрузки и сохраняют результат.

#### Составной кэш с `Cache.Builder` { #builder-composite-cache }

Если в императивном коде нужен составной кэш, его можно построить как фасад через `Cache.Builder`.
Порядок слоёв определяется порядком добавления: обычно быстрый локальный кэш, такой как `Caffeine`, добавляется первым,
а более общий кэш, такой как `Redis`, добавляется после него.

- `get(key)` проверяет кэши по порядку и возвращает первое найденное значение.
- `put(...)`, `invalidate(...)` и `invalidateAll()` выполняются во всех кэшах.
- `computeIfAbsent(...)` проверяет кэши по порядку; если значение найдено на нижнем слое, оно записывается в предыдущие слои.
- Если значение отсутствует во всех слоях, вызывается функция загрузки, а результат записывается во все кэши.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Cache("mycache.caffeine.config")
    public interface MyCaffeineCache extends CaffeineCache<String, String> { }

    @Cache("mycache.redis.config")
    public interface MyRedisCache extends RedisCache<String, String> { }

    @KoraApp
    public interface Application extends CaffeineCacheModule, RedisCacheModule {

        default Cache<String, String> compositeCache(MyCaffeineCache caffeineCache, MyRedisCache redisCache) {
            return Cache.builder(caffeineCache)
                .addCache(redisCache)
                .build();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Cache("mycache.caffeine.config")
    interface MyCaffeineCache : CaffeineCache<String, String>

    @Cache("mycache.redis.config")
    interface MyRedisCache : RedisCache<String, String>

    @KoraApp
    interface Application : CaffeineCacheModule, RedisCacheModule {

        fun compositeCache(
            caffeineCache: MyCaffeineCache,
            redisCache: MyRedisCache,
        ): Cache<String, String> {
            return Cache.builder(caffeineCache)
                .addCache(redisCache)
                .build()
        }
    }
    ```

Для асинхронного фасада используйте `AsyncCache.builder(...)`; в него можно добавлять только экземпляры `AsyncCache`.
Это подходит, например, для нескольких экземпляров `RedisCache` или других асинхронных реализаций с одинаковыми типами ключа и значения.

===! ":fontawesome-brands-java: `Java`"

    ```java
    default AsyncCache<String, String> compositeAsyncCache(MyRedisCache redisCache1, MyRedisCache redisCache2) {
        return AsyncCache.builder(redisCache1)
            .addCache(redisCache2)
            .build();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun compositeAsyncCache(redisCache1: MyRedisCache, redisCache2: MyRedisCache): AsyncCache<String, String> {
        return AsyncCache.builder(redisCache1)
            .addCache(redisCache2)
            .build()
    }
    ```

Фасад, построенный через `Cache.Builder`, не поддерживает прямой `get(Collection<K>)`, а фасад, построенный через `AsyncCache.Builder`, не поддерживает прямой `getAsync(Collection<K>)`.
Для пакетной загрузки используйте `computeIfAbsent(Collection<K>, ...)` или `computeIfAbsentAsync(Collection<K>, ...)`.

#### Переопределение времени устаревания Redis { #redis-expiration-override }

Помимо общего набора методов `Cache`/`AsyncCache`, `RedisCache` добавляет методы для переопределения настроенного `expireAfterWrite` для отдельной записи.
`putExpireAfterWrite(key, value, Duration)` и его пакетная перегрузка с `Map` записывают синхронно, тогда как `putAsyncExpireAfterWrite(...)`
(одиночный и пакетный с `Map`) возвращают `CompletionStage`. Переданный `Duration` применяется к этой конкретной записи вместо значения из конфигурации.
Эти методы доступны только для `Redis`, поскольку `RedisCache` наследует `AsyncCache`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Cache("mycache.config")
    public interface MyCache extends RedisCache<String, String> { }

    @Component
    public class SomeService {

        private final MyCache cache;

        public SomeService(MyCache cache) {
            this.cache = cache;
        }

        public void cacheFor(String key, String value) {
            cache.putExpireAfterWrite(key, value, Duration.ofMinutes(5));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Cache("mycache.config")
    interface MyCache : RedisCache<String, String>

    @Component
    class SomeService(private val cache: MyCache) {

        fun cacheFor(key: String, value: String) {
            cache.putExpireAfterWrite(key, value, Duration.ofMinutes(5))
        }
    }
    ```

### Декларативный подход { #declarative }

Все примеры аспектов ниже предполагают реализацию кэша, приведённую выше.

#### Получение { #get }

Чтобы кэшировать и извлекать значение из кэша для метода `get()`, пометьте его аннотацией `@Cacheable`.
Если значение найдено в кэше, исходный метод не вызывается; если значения нет, метод выполняется, а результат сохраняется в кэше.

Ключ кэша строится из аргументов метода, и порядок аргументов имеет значение. В данном случае он строится из `arg1`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @Cacheable(MyCache.class)
        public String get(String arg1) {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @Cacheable(MyCache::class)
        fun get(arg1: String): String {
            // do something
        }
    }
    ```

#### Запись { #put }

Чтобы добавлять значения в кэш через метод `put()`, пометьте его аннотацией `@CachePut`.
Метод с `@CachePut` вызывается всегда, а его результат помещается в кэш, определённый в `value`.

Ключ кэша строится из аргументов метода, и порядок аргументов имеет значение. В данном случае он строится из `arg1`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @CachePut(MyCache.class)
        public String put(String arg1) {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @CachePut(MyCache::class)
        fun put(arg1: String): String {
            // do something
        }
    }
    ```

#### Удаление { #invalidate }

Чтобы удалить значение из кэша по ключу через метод `evict()`, пометьте его аннотацией `@CacheInvalidate`.
Метод с `@CacheInvalidate` вызывается, а затем значение удаляется по ключу из кэша, определённого в `value`.

Ключ кэша строится из аргументов метода, и порядок аргументов имеет значение. В данном случае он строится из `arg1`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @CacheInvalidate(MyCache.class)
        public void evict(String arg1) {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @CacheInvalidate(MyCache::class)
        fun evict(arg1: String) {
            // do something
        }
    }
    ```

#### Удаление всех { #invalidate-all }

Чтобы удалить все значения из кэша через метод `evictAll()`, пометьте его аннотацией `@CacheInvalidate`
и укажите параметр `invalidateAll = true`.

Метод с `@CacheInvalidate` вызывается, а затем все значения удаляются из кэша, определённого в `value`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @CacheInvalidate(value = MyCache.class, invalidateAll = true)
        public void evictAll(String arg1) {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @CacheInvalidate(value = MyCache::class, invalidateAll = true)
        fun evict(arg1: String) {
            // do something
        }
    }
    ```

#### Составной кэш { #composite-cache }

Если необходимо использовать несколько кэшей, подключите нужные модули и укажите несколько аннотаций над методом.
Например, так можно объединить быстрый локальный слой на `Caffeine` и общий слой на `Redis`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends RedisCacheModule, CaffeineCacheModule {

        @Cache("mycache.caffeine.config")
        public interface MyCaffeineCache extends CaffeineCache<String, String> { }

        @Cache("mycache.redis.config")
        public interface MyRedisCache extends RedisCache<String, String> { }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : RedisCacheModule, CaffeineCacheModule { 

        @Cache("mycache.caffeine.config")
        interface MyCaffeineCache : CaffeineCache<String, String> { }

        @Cache("mycache.redis.config")
        interface MyRedisCache : RedisCache<String, String> { }
    }
    ```

И сам аннотированный класс:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @Cacheable(MyCaffeineCache.class)
        @Cacheable(MyRedisCache.class)
        public String get(String arg1) {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @Cacheable(MyCaffeineCache::class)
        @Cacheable(MyRedisCache::class)
        fun get(arg1: String): String {
            // do something
        }
    }
    ```

Порядок вызова следует порядку аннотаций над методом сверху вниз.
Для `@Cacheable` это означает, что первым проверяется верхний кэш; при промахе проверяется следующий кэш,
а после загрузки значения результат записывается обратно в проверенные кэши.
Та же модель композиции работает для повторяемых `@CachePut` и `@CacheInvalidate`: метод вызывается один раз,
а затем результат записывается во все перечисленные кэши или удаление выполняется во всех перечисленных кэшах.
Также можно использовать контейнерные аннотации `@Cacheables`, `@CachePuts` и `@CacheInvalidates`, когда такая форма удобнее.

## Ключ { #key }

Если ключ кэша состоит из одного аргумента, зарегистрируйте `Cache` с сигнатурой, соответствующей типам ключа и значения.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Cache("mycache.config")
    public interface MyCache extends CaffeineCache<String, String> { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Cache("mycache.config")
    interface MyCache : CaffeineCache<String, String>
    ```

### Преобразование { #conversion }

Если аргумент нельзя использовать напрямую в качестве ключа кэша, реализации требуется маппер
с интерфейсом `CacheKeyMapper`. Если для ключа два аргумента, требуется `CacheKeyMapper2`; если три — `CacheKeyMapper3`, и так далее вплоть до `CacheKeyMapper9`.

Такой маппер можно указать вручную через `@Mapping`.
Пример преобразования сложного объекта в простой ключ кэша:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        public record UserContext(String userId, String traceId) { }

        public static final class UserContextMapping implements CacheKeyMapper<String, UserContext> {

            @Nonnull
            @Override
            public String map(UserContext arg) {
                return arg.userId();
            }
        }

        @Mapping(UserContextMapping.class)
        @Cacheable(MyCache.class)
        public String get(UserContext context) {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        data class UserContext(val userId: String, val traceId: String)

        class UserContextMapping : CacheKeyMapper<String, UserContext> {
            override fun map(arg: UserContext): String {
                return arg.userId
            }
        }

        @Mapping(UserContextMapping::class)
        @Cacheable(MyCache::class)
        fun get(context: UserContext): String {
            // do something
        }
    }
    ```

### Составной ключ { #composite-key }

Если ключ кэша состоит из нескольких аргументов, зарегистрируйте `Cache` с собственным классом,
описывающим этот ключ.

Пример для `Cache`, где составной ключ состоит из двух элементов:

===! ":fontawesome-brands-java: `Java`"

    Создайте собственный `record`, описывающий составной ключ.

    ```java
    @Cache("mycache.config")
    public interface MyCache extends CaffeineCache<MyCache.Key, String> {
        
        record Key(String k1, Long k2) { }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте собственный `data class`, описывающий составной ключ.

    ```kotlin
    @Cache("mycache.config")
    interface MyCache : CaffeineCache<MyCache.Key, String> {

        data class Key(val k1: String, val k2: Long)
    }
    ```

Если используется `RedisCache`, для составного ключа генерируется `RedisCacheKeyMapper`.
Он использует маппер для каждого поля ключа и ожидает, что результат маппинга для каждого поля будет не `null`.
Встроенные мапперы могут кодировать `null` специальным значением, тогда как собственные мапперы должны делать это явно.

### Порядок аргументов { #argument-ordering }

Если метод принимает аргументы, которые должны быть исключены из составного ключа, или порядок аргументов не совпадает
с порядком аргументов конструктора составного ключа, используйте атрибут `parameters` и укажите,
какие аргументы метода использовать и в каком порядке.

`parameters` определяет полный набор аргументов метода, используемых для построения ключа. Каждое имя должно совпадать с именем аргумента метода,
а порядок должен соответствовать типу ключа: для одиночного аргумента — типу ключа `Cache<K, V>`; для составного ключа —
порядку аргументов конструктора `record` или `data class`.
Если имя отсутствует, тип не совпадает или порядок не подходит к ключу, генерация приложения завершается ошибкой.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @Cacheable(value = MyCache.class, parameters = {"arg1", "arg2"})
        public String get(Long arg2, String arg3, String arg1) {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService {

        @Cacheable(value = MyCache::class, parameters = ["arg1", "arg2"])
        fun get(arg2: Long, arg3: String, arg1: String): String {
            // do something
        }
    }
    ```

## Loadable Cache { #loadable-cache }

Библиотека предоставляет компонент `LoadableCache`, который объединяет операции `get` и `put` без использования аспектов.
Он полезен, когда загрузкой значения нужно управлять вручную, сохраняя при этом стандартную логику: сначала проверить кэш,
а при промахе загрузить данные и сохранить их.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Cache("mycache.config")
    public interface MyCache extends CaffeineCache<String, String> { }

    @KoraApp
    public interface Application extends CaffeineCacheModule {

        default LoadableCache<String, String> loadableCache(MyCache cache, SomeService someService) {
            return cache.asLoadable(someService::loadEntity);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Cache("mycache.config")
    interface MyCache : CaffeineCache<String, String>

    @KoraApp
    interface Application : CaffeineCacheModule {

        fun loadableCache(
            cache: MyCache,
            someService: SomeService,
        ): LoadableCache<String, String> {
            return cache.asLoadable(someService::loadEntity)
        }
    }
    ```

Для асинхронного кэша используйте `AsyncLoadableCache`. Он создаётся через `asLoadableAsyncSimple(...)`
для загрузки одного ключа или через `asLoadableAsync(...)` для пакетной загрузки нескольких ключей.
Оба варианта возвращают `CompletionStage` и подходят для `RedisCache`, поскольку он реализует `AsyncCache`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Cache("mycache.config")
    public interface MyCache extends RedisCache<String, String> { }

    @KoraApp
    public interface Application extends RedisCacheModule {

        default AsyncLoadableCache<String, String> loadableCache(MyCache cache, SomeService someService) {
            return cache.asLoadableAsync(someService::loadEntities);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Cache("mycache.config")
    interface MyCache : RedisCache<String, String>

    @KoraApp
    interface Application : RedisCacheModule {

        fun loadableCache(
            cache: MyCache,
            someService: SomeService,
        ): AsyncLoadableCache<String, String> {
            return cache.asLoadableAsync(someService::loadEntities)
        }
    }
    ```

## Сигнатуры { #signatures }

Доступные сигнатуры для методов, поддерживаемых аннотациями:

===! ":fontawesome-brands-java: `Java`"

    Класс не должен быть `final`, чтобы аспекты работали.

    Под `T` подразумевается тип возвращаемого значения.

    - `T myMethod()`
    - `Optional<T> myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletionStage.html)
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (требуется [зависимость](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

    `@Cacheable` и `@CachePut` требуют возвращаемого значения и не могут применяться к `void`, `Mono<Void>`, `CompletionStage<Void>`, `Flux<T>` или `Publisher<T>`.
    `@CacheInvalidate` можно применять к методам без результата, но нельзя применять к `Flux<T>` или `Publisher<T>`.

=== ":simple-kotlin: `Kotlin`"

    Класс должен быть `open`, чтобы аспекты работали.

    Под `T` подразумевается тип возвращаемого значения, либо `T?`, либо `Unit`.

    - `myMethod(): T`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (требуется [зависимость](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) как `implementation`)

    `@Cacheable` и `@CachePut` требуют возвращаемого значения и не могут применяться к `Unit`.
    `@CacheInvalidate` можно применять к методам без результата.
