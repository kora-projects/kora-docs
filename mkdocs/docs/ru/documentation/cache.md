---
description: "Explains Kora cache module, cache annotations, Caffeine and Redis cache backends, cache key mapping, telemetry, invalidation, and async cache signatures. Use when working with @Cache, @Cacheable, @CachePut, @CacheInvalidate, CaffeineCacheModule, RedisCacheModule, CacheKeyMapper, LoadableCache."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora cache module, cache annotations, Caffeine and Redis cache backends, cache key mapping, telemetry, invalidation, and async cache signatures; key triggers include @Cache, @Cacheable, @CachePut, @CacheInvalidate, CaffeineCacheModule, RedisCacheModule, CacheKeyMapper, LoadableCache."
---

Модуль предоставляет типизированные `кеши` для хранения результатов вычислений и повторно используемых данных,
чтобы не выполнять дорогие операции при каждом обращении. `Кеш` можно использовать декларативно через аннотации над методами
или императивно через внедренный интерфейс, а в качестве хранилища доступны локальный `Caffeine` и внешний `Redis`.
Локальный `Caffeine` полезен для быстрого хранения внутри одного процесса, а `Redis` подходит для общего `кеша`,
который разделяют несколько экземпляров приложения.

Если нужен пошаговый разбор перед справочным описанием, смотрите [Кеширование](../guides/cache.md) и [Многоуровневое кеширование](../guides/cache-multi-level.md).

## Caffeine { #caffeine }

Реализация на основе библиотеки [Caffeine](https://github.com/ben-manes/caffeine) для `кеша` внутри памяти приложения.

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

Пример полной конфигурации для `кеша` по пути `mycache.config`; параметры описаны в классе `CaffeineCacheConfig` (указаны примеры значений или значения по умолчанию):

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

    1.  Время, после которого значение будет удалено из `кеша`; отсчитывается после записи значения (по умолчанию не указано, необязательно)
    2.  Время, после которого значение будет удалено из `кеша`; отсчитывается после чтения значения (по умолчанию не указано, необязательно)
    3.  Начальный размер `кеша`, помогает избежать расширения при быстром росте количества значений (по умолчанию не указано, необязательно)
    4.  Максимальный размер `кеша`; при достижении границы **или чуть раньше** будут исключаться [наименее актуальные значения](https://blog.skillfactory.ru/glossary/lru/) (по умолчанию: `100000`)

=== ":simple-yaml: `YAML`"

    ```yaml
    mycache:
      config:
        expireAfterWrite: "10s" #(1)!
        expireAfterAccess: "10s" #(2)!
        initialSize: 10 #(3)!
        maximumSize: 100000 #(4)!
    ```

    1.  Время, после которого значение будет удалено из `кеша`; отсчитывается после записи значения (по умолчанию не указано, необязательно)
    2.  Время, после которого значение будет удалено из `кеша`; отсчитывается после чтения значения (по умолчанию не указано, необязательно)
    3.  Начальный размер `кеша`, помогает избежать расширения при быстром росте количества значений (по умолчанию не указано, необязательно)
    4.  Максимальный размер `кеша`; при достижении границы **или чуть раньше** будут исключаться [наименее актуальные значения](https://blog.skillfactory.ru/glossary/lru/) (по умолчанию: `100000`)

## Redis { #redis }

Реализация на основе базы данных в памяти [Redis](https://redis.io/docs/about/) и драйвера подключения [Lettuce](https://github.com/lettuce-io/lettuce-core).

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

Требуется отдельно сконфигурировать `Lettuce` драйвер для подключения к `Redis`.
Используется одно подключение для всех `Redis`-кешей.

Пример полной конфигурации для `Lettuce` драйвера; параметры описаны в классе `LettuceClientConfig` (указаны примеры значений или значения по умолчанию):

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

    1.  `URI` для подключения к `Redis` (`обязательная`, по умолчанию не указано).
        Подключение для одного сервера: `redis://localhost:6379`.
        Подключение для нескольких серверов: `redis://localhost:6379,localhost:6380`.
        Подключение с `SSL`: `rediss://localhost:6380`.
        Подключение с `TLS`: `redis+tls://localhost:6380`.
    2.  Имя пользователя для подключения (по умолчанию не указано, необязательно)
    3.  Пароль пользователя для подключения (по умолчанию не указано, необязательно)
    4.  Номер базы для подключения (по умолчанию не указано, необязательно)
    5.  Протокол подключения, может иметь значения `RESP2` или `RESP3` (по умолчанию: `RESP3`)
    6.  Время ожидания подключения по сокету (по умолчанию: `10s`)
    7.  Время ожидания выполнения команды (по умолчанию: `60s`)
    8.  Создавать кластерный клиент даже при одном `URI` подключения (по умолчанию: `false`)
    9.  Алгоритмы шифрования для безопасного соединения между клиентом и сервером (по умолчанию: `[]`)
    10. Время ожидания установки безопасного соединения с сервером (по умолчанию: `10s`)
    11. Включает логирование модуля (по умолчанию: `false`)
    12. Включает метрики модуля (по умолчанию: `true`)
    13. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
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

    1.  `URI` для подключения к `Redis` (`обязательная`, по умолчанию не указано).
        Подключение для одного сервера: `redis://localhost:6379`.
        Подключение для нескольких серверов: `redis://localhost:6379,localhost:6380`.
        Подключение с `SSL`: `rediss://localhost:6380`.
        Подключение с `TLS`: `redis+tls://localhost:6380`.
    2.  Имя пользователя для подключения (по умолчанию не указано, необязательно)
    3.  Пароль пользователя для подключения (по умолчанию не указано, необязательно)
    4.  Номер базы для подключения (по умолчанию не указано, необязательно)
    5.  Протокол подключения, может иметь значения `RESP2` или `RESP3` (по умолчанию: `RESP3`)
    6.  Время ожидания подключения по сокету (по умолчанию: `10s`)
    7.  Время ожидания выполнения команды (по умолчанию: `60s`)
    8.  Создавать кластерный клиент даже при одном `URI` подключения (по умолчанию: `false`)
    9.  Алгоритмы шифрования для безопасного соединения между клиентом и сервером (по умолчанию: `[]`)
    10. Время ожидания установки безопасного соединения с сервером (по умолчанию: `10s`)
    11. Включает логирование модуля (по умолчанию: `false`)
    12. Включает метрики модуля (по умолчанию: `true`)
    13. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    14. Настройка тегов для метрик (по умолчанию: `{}`)
    15. Включает трассировку модуля (по умолчанию: `true`)
    16. Настройка атрибутов для трассировки (по умолчанию: `{}`)

Конфигурация `Redis`-кеша настраивает поведение конкретного `кеша`.

Пример полной конфигурации для `кеша` по пути `mycache.config`; параметры описаны в классе `RedisCacheConfig` (указаны примеры значений):

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

    1.  При записи устанавливает время [истечения срока действия](https://redis.io/commands/psetex/) значения (по умолчанию не указано, необязательно)
    2.  При чтении устанавливает время [истечения срока действия](https://redis.io/commands/getex/) значения (по умолчанию не указано, необязательно)
    3.  Префикс ключа в конкретном `кеше`, нужен для избежания коллизий ключей в одной базе `Redis`; может быть пустой строкой, тогда ключи будут без префикса (`обязательная`, по умолчанию не указано)

=== ":simple-yaml: `YAML`"

    ```yaml
    mycache:
      config:
        expireAfterWrite: "10s" #(1)!
        expireAfterAccess: "10s" #(2)!
        keyPrefix: "mykey" #(3)!
    ```

    1.  При записи устанавливает время [истечения срока действия](https://redis.io/commands/psetex/) значения (по умолчанию не указано, необязательно)
    2.  При чтении устанавливает время [истечения срока действия](https://redis.io/commands/getex/) значения (по умолчанию не указано, необязательно)
    3.  Префикс ключа в конкретном `кеше`, нужен для избежания коллизий ключей в одной базе `Redis`; может быть пустой строкой, тогда ключи будут без префикса (`обязательная`, по умолчанию не указано)

Предоставляемые метрики модуля описаны в разделе [Справочник метрик](metrics.md#cache).

### Преобразователи ключей и значений { #redis-mappers }

`Redis` хранит ключи и значения как массивы байт, поэтому для `RedisCache` используются два вида преобразователей:

- `RedisCacheKeyMapper<K>` превращает ключ `кеша` в `byte[]`.
- `RedisCacheValueMapper<V>` записывает значение `кеша` в `byte[]` и читает его обратно.

Обычные ключи строятся через `RedisCacheKeyMapper` для типа ключа. Встроенные преобразователи есть для `String`, `byte[]`,
чисел, `BigInteger`, `BigDecimal`, `UUID`, `Boolean`, `Character`, `Instant`, `LocalDateTime`, `LocalDate`, `ZonedDateTime`,
`Duration`, `Period`, `Enum` и `Collection<T>`, если для `T` тоже есть преобразователь.
Для `Enum` используется значение `toString()`, поэтому его можно переопределить, если нужен другой формат ключа.

Для значений встроенные `RedisCacheValueMapper` есть для тех же простых типов, дат, времени, `Enum` и `byte[]`.
Для остальных типов используется преобразователь через `JsonWriter<V>` и `JsonReader<V>`, если для типа доступна JSON-сериализация.
Если нужно другое представление, зарегистрируйте собственный компонент `RedisCacheValueMapper<V>` или `RedisCacheKeyMapper<K>`.

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

Для составного ключа из `record` или `data class` Kora генерирует отдельный `RedisCacheKeyMapper` для всего ключа.
Он получает преобразователь для каждого поля, преобразует каждое поле в `byte[]`, а затем соединяет части через разделитель `RedisCacheKeyMapper.DELIMITER`.
Порядок частей соответствует порядку компонентов `record` или свойств `data class`.

Для одиночного ключа встроенные `RedisCacheKeyMapper` умеют кодировать `null` специальным байтовым значением.
В составном ключе результат преобразования каждого поля должен быть не `null`: если собственный `RedisCacheKeyMapper` для поля вернет `null`,
создание ключа завершится ошибкой. Поэтому для необязательных полей составного ключа собственный преобразователь должен явно кодировать `null`
в стабильное байтовое значение.

#### Донастройка { #configurator }

Можно зарегистрировать `LettuceConfigurator`, который позволяет донастроить `Lettuce` клиент перед созданием.

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

## Использование { #usage }

Для создания `кеша` требуется зарегистрировать типизированный контракт с аннотацией `@Cache`.
Интерфейс контракта должен наследоваться от предоставляемых `Kora` реализаций: `CaffeineCache` или `RedisCache`.
Для такого `@Cache` будет создана и добавлена в граф реализация, которую можно внедрять как зависимость.

Аргумент `value` у `@Cache` задает полный путь к конфигурации конкретного `кеша`.

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

### Необязательные значения { #optional-values }

Если метод на `Java` возвращает `Optional<T>`, аспект кеширования умеет работать с такой сигнатурой напрямую.
То же правило применяется к асинхронным оберткам, например `CompletionStage<Optional<T>>` и `Mono<Optional<T>>`.
Тип значения самого `кеша` может быть как `T`, так и `Optional<T>`:

- `CaffeineCache<String, String>` и метод `Optional<String> get(String key)`;
- `CaffeineCache<String, Optional<String>>` и метод `String get(String key)`;
- `CaffeineCache<String, Optional<String>>` и метод `Optional<String> get(String key)`.

Для `@Cacheable` это позволяет явно отличать отсутствие значения в `кеше` от результата метода, который тоже означает отсутствие данных.
Для `@CachePut` результат `Optional<T>` обрабатывается с учетом типа значения `кеша`: если `кеш` хранит `Optional<T>`, сохраняется сам `Optional`,
а если `кеш` хранит `T`, сохраняется только присутствующее значение.

### Императивный подход { #imperative }

`Кеши` доступны для внедрения как зависимости по интерфейсу и могут использоваться вместе с декларативными операциями.

`CaffeineCache` предоставляет контракт `Cache` для синхронных операций и дополнительный метод `getAll()`.
`RedisCache` предоставляет `Cache` и `AsyncCache`: его можно использовать как синхронно, так и асинхронно через `CompletionStage`.

`Cache` предоставляет методы `get(...)`, `put(...)`, `computeIfAbsent(...)`, `invalidate(...)`, `invalidateAll(...)`,
а также пакетные варианты для коллекции ключей или карты значений. `AsyncCache` предоставляет такие же операции с суффиксом `Async`.
Методы `computeIfAbsent(...)` сначала пытаются получить значение из `кеша`, а при промахе вызывают переданную функцию загрузки и сохраняют результат.

#### Составной кеш через `Cache.Builder` { #builder-composite-cache }

Если составной `кеш` нужен в императивном коде, можно собрать фасад через `Cache.Builder`.
Порядок слоев задается порядком добавления: сначала обычно добавляют быстрый локальный `кеш`, например `Caffeine`,
а затем более общий `кеш`, например `Redis`.

- `get(key)` проверяет `кеши` по порядку и возвращает первое найденное значение.
- `put(...)`, `invalidate(...)` и `invalidateAll()` выполняются во всех `кешах`.
- `computeIfAbsent(...)` проверяет `кеши` по порядку; если значение найдено в нижнем слое, оно записывается в предыдущие слои.
- Если значения нет ни в одном слое, вызывается функция загрузки, а результат записывается во все `кеши`.

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

Для асинхронного фасада используется `AsyncCache.builder(...)`; в него можно добавлять только `AsyncCache`.
Такой вариант подходит, например, для нескольких `RedisCache` или других асинхронных реализаций с одинаковыми типами ключа и значения.

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

У фасада через `Cache.Builder` не поддержан прямой вызов `get(Collection<K>)`, а у фасада через `AsyncCache.Builder` не поддержан прямой вызов `getAsync(Collection<K>)`.
Для пакетной загрузки используйте `computeIfAbsent(Collection<K>, ...)` или `computeIfAbsentAsync(Collection<K>, ...)`.

### Декларативный подход { #declarative }

Все примеры использования аспектов будут подразумевать реализацию `кеша` выше.

#### Получение { #get }

Для кеширования и получения значения из `кеша` для метода `get()` следует проаннотировать его аннотацией `@Cacheable`.
Если значение найдено в `кеше`, исходный метод не вызывается; если значения нет, метод выполняется, а результат сохраняется в `кеш`.

Ключ для `кеша` составляется из аргументов метода, порядок аргументов имеет значение, в данном случае он будет составляться из значения `arg1`.

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

#### Сохранение { #put }

Для добавления значений в `кеш` через метод `put()` следует проаннотировать его аннотацией `@CachePut`.
Метод с `@CachePut` всегда будет вызван, а его результат будет положен в `кеш`, определенный в `value`.

Ключ для `кеша` составляется из аргументов метода, порядок аргументов имеет значение, в данном случае он будет составляться из значения `arg1`.

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

Для удаления значения по ключу из `кеша` через метод `evict()` следует проаннотировать его аннотацией `@CacheInvalidate`.
Метод с `@CacheInvalidate` будет вызван, а затем из `кеша`, определенного в `value`, будет удалено значение по ключу.

Ключ для `кеша` составляется из аргументов метода, порядок аргументов имеет значение, в данном случае он будет составляться из значения `arg1`.

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

#### Полное удаление { #invalidate-all }

Для удаления всех значений из `кеша` через метод `evictAll()` следует проаннотировать его аннотацией `@CacheInvalidate`
и указать параметр `invalidateAll = true`.

Метод с `@CacheInvalidate` будет вызван, а затем из `кеша`, определенного в `value`, будут удалены все значения.

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

#### Составной кеш { #composite-cache }

Если нужно использовать несколько `кешей`, подключите нужные модули и укажите несколько аннотаций над методом.
Так можно собрать, например, быстрый локальный слой на `Caffeine` и общий слой на `Redis`.

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

А сам проаннотированный класс так:

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

Порядок вызова соответствует порядку аннотаций над методом сверху вниз.
Для `@Cacheable` это означает, что сначала проверяется верхний `кеш`; при промахе проверяется следующий `кеш`,
а после загрузки значения результат сохраняется обратно в проверенные `кеши`.
Та же модель применяется для повторяемых `@CachePut` и `@CacheInvalidate`: метод вызывается один раз,
а затем результат записывается во все указанные `кеши` или удаление выполняется во всех указанных `кешах`.
Также можно использовать контейнерные аннотации `@Cacheables`, `@CachePuts` и `@CacheInvalidates`, если такая форма удобнее.

## Ключ { #key }

Если ключ `кеша` состоит из одного аргумента, требуется зарегистрировать `Cache` с сигнатурой,
которая соответствует типам ключа и значения.

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

Если аргумент не может быть напрямую использован как ключ `кеша`, реализации потребуется преобразователь
с интерфейсом `CacheKeyMapper`. Если аргументов для ключа два, потребуется `CacheKeyMapper2`, если три — `CacheKeyMapper3`, и так далее до `CacheKeyMapper9`.

Такой преобразователь можно предоставить вручную с помощью аннотации `@Mapping`.
Пример преобразования сложного объекта в простой ключ `кеша`:

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

Если ключ `кеша` состоит из нескольких аргументов, требуется зарегистрировать `Cache` с собственным классом,
который описывает такой ключ.

Пример для `Cache`, где составной ключ состоит из двух элементов:

===! ":fontawesome-brands-java: `Java`"
    
    Предполагается создавать собственный `record`, который описывает составной ключ.

    ```java
    @Cache("mycache.config")
    public interface MyCache extends CaffeineCache<MyCache.Key, String> {
        
        record Key(String k1, Long k2) { }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Предполагается создавать собственный `data class`, который описывает составной ключ.

    ```kotlin
    @Cache("mycache.config")
    interface MyCache : CaffeineCache<MyCache.Key, String> {

        data class Key(val k1: String, val k2: Long)
    }
    ```

Если используется `RedisCache`, для составного ключа будет сгенерирован `RedisCacheKeyMapper`.
Он использует преобразователь для каждого поля ключа и ожидает, что результат преобразования каждого поля будет не `null`.
Встроенные преобразователи умеют кодировать `null` специальным значением, а собственные преобразователи должны делать это явно.

### Порядок аргументов { #argument-ordering }

Если метод принимает аргументы, которые нужно исключить из составного ключа, или порядок аргументов не соответствует
порядку аргументов конструктора составного ключа, следует использовать атрибут `parameters` и указать,
какие аргументы метода использовать и в каком порядке.

`parameters` задает полный набор аргументов метода, из которых будет построен ключ. Каждое имя должно совпадать с именем
аргумента метода, а порядок должен соответствовать типу ключа: для одного аргумента — типу ключа `Cache<K, V>`,
для составного ключа — порядку аргументов конструктора `record` или `data class`.
Если имя отсутствует, тип не совпадает или порядок не подходит для ключа, генерация приложения завершится ошибкой.

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

## Подгружаемый кеш { #loadable-cache }

Библиотека предоставляет компонент `LoadableCache`, который объединяет операции `get` и `put` без использования аспектов.
Он полезен, когда нужно управлять загрузкой значения вручную, но при этом оставить стандартную логику: сначала проверить `кеш`,
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

Для асинхронного `кеша` можно использовать `AsyncLoadableCache`. Он создается через `asLoadableAsyncSimple(...)`
для загрузки одного ключа или через `asLoadableAsync(...)` для пакетной загрузки нескольких ключей.
Оба варианта возвращают `CompletionStage` и подходят для `RedisCache`, потому что он реализует `AsyncCache`.

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

Доступные сигнатуры для методов, которые поддерживают аннотации:

===! ":fontawesome-brands-java: `Java`"

    Класс не должен быть `final`, чтобы аспекты работали.

    Под `T` подразумевается тип возвращаемого значения.

    - `T myMethod()`
    - `Optional<T> myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletionStage.html)
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (надо подключить [зависимость](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

    `@Cacheable` и `@CachePut` требуют возвращаемое значение и не применяются к `void`, `Mono<Void>`, `CompletionStage<Void>`, `Flux<T>` или `Publisher<T>`.
    `@CacheInvalidate` можно применять к методам без результата, но нельзя применять к `Flux<T>` или `Publisher<T>`.

=== ":simple-kotlin: `Kotlin`"

    Класс должен быть `open`, чтобы аспекты работали.

    Под `T` подразумевается тип возвращаемого значения, либо `T?`, либо `Unit`.

    - `myMethod(): T`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (надо подключить [зависимость](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) как `implementation`)

    `@Cacheable` и `@CachePut` требуют возвращаемое значение и не применяются к `Unit`.
    `@CacheInvalidate` можно применять к методам без результата.
