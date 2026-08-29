---
description: "Explains Kora cache module, cache annotations, Caffeine and Redis cache backends, cache key mapping, telemetry, invalidation, execution modes and supported method signatures. Use when working with @Cache, @Cacheable, @CachePut, @CacheInvalidate, @CacheInvalidateAll, @CacheMode, CaffeineCacheModule, LettuceRedisCacheModule, CacheKeyMapper, LoadableCache."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora cache module, cache annotations, Caffeine and Redis cache backends, cache key mapping, telemetry, invalidation, execution modes and supported method signatures; key triggers include @Cache, @Cacheable, @CachePut, @CacheInvalidate, @CacheInvalidateAll, CacheMode, CaffeineCacheModule, LettuceRedisCacheModule, RedisCacheClient, CacheKeyMapper, LoadableCache."
---

Модуль предоставляет типизированные кэши для хранения результатов вычислений и повторно используемых данных,
чтобы дорогостоящие операции не приходилось выполнять при каждом обращении. Кэш можно использовать декларативно через аннотации над методами
или императивно через внедряемый интерфейс, а в качестве хранилищ доступны локальный `Caffeine` и внешний `Redis`.
Локальный `Caffeine` полезен для быстрого внутрипроцессного хранения, а `Redis` подходит для общего кэша, используемого несколькими экземплярами приложения.

Весь контракт кэша синхронный: `Cache<K, V>` возвращает значения напрямую, а аспекты кэширования применяются к синхронным методам.

Если нужен пошаговый разбор перед справочным описанием, смотрите [Кэш](../guides/cache.md) и [Многоуровневый кэш](../guides/cache-multi-level.md).

## Caffeine { #caffeine }

Реализация на основе библиотеки [Caffeine](https://github.com/ben-manes/caffeine) для кэша приложения в оперативной памяти.

### Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:cache-caffeine"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends CaffeineCacheModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:cache-caffeine")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : CaffeineCacheModule
    ```

### Конфигурация { #configuration }

Пример полной конфигурации кэша по пути `mycache.config`; параметры описаны в классе `CaffeineCacheConfig` (приведены примерные значения или значения по умолчанию):

===! ":material-code-json: `Hocon`"

    ```javascript
    mycache {
        config {
            enabled = true //(1)!
            expireAfterWrite = "10s" //(2)!
            expireAfterAccess = "10s" //(3)!
            initialSize = 10 //(4)!
            maximumSize = 100000 //(5)!
            telemetry {
                logging {
                    enabled = false //(6)!
                }
                metrics {
                    enabled = false //(7)!
                    slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(8)!
                    tags = { //(9)!
                        "key1" = "value1"
                    }
                }
                tracing {
                    enabled = true //(10)!
                    attributes = { //(11)!
                        "key1" = "value1"
                    }
                }
            }
        }
    }
    ```

    1.  Включает кэш; при значении `false` все операции кэша превращаются в пустые, а `computeIfAbsent` всегда вызывает загрузчик (по умолчанию: `true`)
    2.  Время, после которого значение удаляется из кэша; отсчитывается после записи значения (по умолчанию не указано, опционально)
    3.  Время, после которого значение удаляется из кэша; отсчитывается после чтения значения (по умолчанию не указано, опционально)
    4.  Начальный размер кэша, помогает избежать расширения при быстром росте количества значений (по умолчанию не указано, опционально)
    5.  Максимальный размер кэша; при достижении границы **или чуть раньше** вытесняются [наименее актуальные значения](https://blog.skillfactory.ru/glossary/lru/) (по умолчанию: `100000`)
    6.  Включает логирование кэша (по умолчанию: `false`)
    7.  Включает метрики кэша; также определяет, регистрируются ли стандартные метрики `Micrometer` для `Caffeine` (по умолчанию: `false`)
    8.  Настройка [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) для метрик, значения являются длительностями, а голые числа означают миллисекунды (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    9.  Настройка тегов для метрик (по умолчанию: `{}`)
    10. Включает трассировку кэша (по умолчанию: `true`)
    11. Настройка атрибутов для трассировки (по умолчанию: `{}`)

=== ":simple-yaml: `YAML`"

    ```yaml
    mycache:
      config:
        enabled: true #(1)!
        expireAfterWrite: "10s" #(2)!
        expireAfterAccess: "10s" #(3)!
        initialSize: 10 #(4)!
        maximumSize: 100000 #(5)!
        telemetry:
          logging:
            enabled: false #(6)!
          metrics:
            enabled: false #(7)!
            slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(8)!
            tags: #(9)!
              key1: value1
          tracing:
            enabled: true #(10)!
            attributes: #(11)!
              key1: value1
    ```

    1.  Включает кэш; при значении `false` все операции кэша превращаются в пустые, а `computeIfAbsent` всегда вызывает загрузчик (по умолчанию: `true`)
    2.  Время, после которого значение удаляется из кэша; отсчитывается после записи значения (по умолчанию не указано, опционально)
    3.  Время, после которого значение удаляется из кэша; отсчитывается после чтения значения (по умолчанию не указано, опционально)
    4.  Начальный размер кэша, помогает избежать расширения при быстром росте количества значений (по умолчанию не указано, опционально)
    5.  Максимальный размер кэша; при достижении границы **или чуть раньше** вытесняются [наименее актуальные значения](https://blog.skillfactory.ru/glossary/lru/) (по умолчанию: `100000`)
    6.  Включает логирование кэша (по умолчанию: `false`)
    7.  Включает метрики кэша; также определяет, регистрируются ли стандартные метрики `Micrometer` для `Caffeine` (по умолчанию: `false`)
    8.  Настройка [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) для метрик, значения являются длительностями, а голые числа означают миллисекунды (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    9.  Настройка тегов для метрик (по умолчанию: `{}`)
    10. Включает трассировку кэша (по умолчанию: `true`)
    11. Настройка атрибутов для трассировки (по умолчанию: `{}`)

Нижележащий кэш `Caffeine` создаётся фабрикой `CaffeineCacheFactory`, которая поставляется как `@DefaultComponent`.
Если требуется настройка сверх перечисленных параметров конфигурации (например, собственная политика вытеснения, слабые ссылки на ключи или свой весовщик),
зарегистрируйте собственный компонент `CaffeineCacheFactory` — он переопределит реализацию по умолчанию и позволит настроить билдер `Caffeine` напрямую.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MyCaffeineCacheFactory implements CaffeineCacheFactory {

        @Override
        public <K, V> Cache<K, V> build(String name, CaffeineCacheConfig config) {
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

Переопределение фабрики заменяет и регистрацию метрик по умолчанию, поэтому стандартные метрики `Micrometer` для `Caffeine`
придётся подключить вручную, если они по-прежнему нужны.

## Redis { #redis }

Реализация на основе базы данных в оперативной памяти [Redis](https://redis.io/docs/about/) и драйвера подключения [Lettuce](https://github.com/lettuce-io/lettuce-core).

### Подключение { #dependency-2 }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:cache-redis-lettuce"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends LettuceRedisCacheModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:cache-redis-lettuce")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : LettuceRedisCacheModule
    ```

`LettuceRedisCacheModule` — точка входа для кэша на `Redis`: он расширяет `RedisCacheModule` и `LettuceModule`
и предоставляет `RedisCacheClient` поверх общего подключения `Lettuce`.

Модуль `RedisCacheModule` из артефакта `cache-redis-common` не привязан к транспорту: он поставляет фабрику телеметрии кэша,
мапперы ключей и мапперы значений, но **не** предоставляет `RedisCacheClient`. Он нужен только тогда, когда используется
другой транспорт `Redis` и собственная реализация `RedisCacheClient`.

### Конфигурация { #configuration-2 }

Для подключения к `Redis` требуется отдельно настроить драйвер `Lettuce`.
Для всех кэшей на `Redis` используется одно подключение.

Основные параметры конфигурации Lettuce:

===! ":material-code-json: `Hocon`"

    ```javascript
    lettuce {
        uri = "redis://localhost:6379" //(1)!
        commandTimeout = "30s" //(2)!
    }
    ```

    1.  `URI` для подключения к `Redis` (`обязательный`, без значения по умолчанию)
    2.  Таймаут выполнения команды (по умолчанию: `30s`)

=== ":simple-yaml: `YAML`"

    ```yaml
    lettuce:
      uri: "redis://localhost:6379" #(1)!
      commandTimeout: "30s" #(2)!
    ```

    1.  `URI` для подключения к `Redis` (`обязательный`, без значения по умолчанию)
    2.  Таймаут выполнения команды (по умолчанию: `30s`)

??? note "Полная конфигурация"

    Пример полной конфигурации драйвера `Lettuce`; параметры описаны в классе `LettuceConfig` (приведены примерные значения или значения по умолчанию):

    ===! ":material-code-json: `Hocon`"

        ```javascript
        lettuce {
            uri = "redis://localhost:6379" //(1)!
            user = "admin" //(2)!
            password = "12345" //(3)!
            database = 0 //(4)!
            protocol = "RESP3" //(5)!
            socketTimeout = "10s" //(6)!
            commandTimeout = "30s" //(7)!
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
                    enabled = false //(12)!
                    slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(13)!
                    tags = { //(14)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
            }
        }
        ```

        1.  `URI` для подключения к `Redis` (`обязательный`, без значения по умолчанию).
            Подключение к одному серверу: `redis://localhost:6379`.
            Подключение к нескольким серверам: `redis://localhost:6379,localhost:6380`.
            Подключение по `SSL`/`TLS`: `rediss://localhost:6380`.
        2.  Имя пользователя для подключения (по умолчанию не указано, опционально)
        3.  Пароль пользователя для подключения (по умолчанию не указано, опционально)
        4.  Номер базы данных для подключения (по умолчанию не указано, опционально)
        5.  Протокол подключения, допустимы `RESP2` или `RESP3` (по умолчанию: `RESP3`)
        6.  Таймаут подключения сокета (по умолчанию: `10s`)
        7.  Таймаут выполнения команды (по умолчанию: `30s`)
        8.  Создавать кластерный клиент даже при единственном `URI` подключения (по умолчанию: `false`)
        9.  Алгоритмы шифрования для защищённого соединения между клиентом и сервером (по умолчанию: `[]`)
        10. Таймаут установки защищённого соединения с сервером (по умолчанию: `10s`)
        11. Включает логирование драйвера (по умолчанию: `false`)
        12. Включает метрики драйвера (по умолчанию: `false`)
        13. Настройка [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
        14. Настройка тегов для метрик (по умолчанию: `{}`)

    === ":simple-yaml: `YAML`"

        ```yaml
        lettuce:
          uri: "redis://localhost:6379" #(1)!
          user: "admin" #(2)!
          password: "12345" #(3)!
          database: 0 #(4)!
          protocol: "RESP3" #(5)!
          socketTimeout: "10s" #(6)!
          commandTimeout: "30s" #(7)!
          forceClusterClient: false #(8)!
          ssl:
            ciphers:
              - "TLS_CHACHA20_POLY1305_SHA256" #(9)!
            handshakeTimeout: "10s" #(10)!
          telemetry:
            logging:
              enabled: false #(11)!
            metrics:
              enabled: false #(12)!
              slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(13)!
              tags: #(14)!
                key1: value1
                key2: value2
        ```

        1.  `URI` для подключения к `Redis` (`обязательный`, без значения по умолчанию).
            Подключение к одному серверу: `redis://localhost:6379`.
            Подключение к нескольким серверам: `redis://localhost:6379,localhost:6380`.
            Подключение по `SSL`/`TLS`: `rediss://localhost:6380`.
        2.  Имя пользователя для подключения (по умолчанию не указано, опционально)
        3.  Пароль пользователя для подключения (по умолчанию не указано, опционально)
        4.  Номер базы данных для подключения (по умолчанию не указано, опционально)
        5.  Протокол подключения, допустимы `RESP2` или `RESP3` (по умолчанию: `RESP3`)
        6.  Таймаут подключения сокета (по умолчанию: `10s`)
        7.  Таймаут выполнения команды (по умолчанию: `30s`)
        8.  Создавать кластерный клиент даже при единственном `URI` подключения (по умолчанию: `false`)
        9.  Алгоритмы шифрования для защищённого соединения между клиентом и сервером (по умолчанию: `[]`)
        10. Таймаут установки защищённого соединения с сервером (по умолчанию: `10s`)
        11. Включает логирование драйвера (по умолчанию: `false`)
        12. Включает метрики драйвера (по умолчанию: `false`)
        13. Настройка [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
        14. Настройка тегов для метрик (по умолчанию: `{}`)

Если указан один `URI` и `forceClusterClient` равен `false`, создаётся обычный клиент `RedisClient`;
в остальных случаях для списка `URI` создаётся кластерный клиент `RedisClusterClient`.

Конфигурация кэша на `Redis` определяет поведение конкретного кэша.

Пример полной конфигурации кэша по пути `mycache.config`; параметры описаны в классе `RedisCacheConfig` (приведены примерные значения):

===! ":material-code-json: `Hocon`"

    ```javascript
    mycache {
        config {
            enabled = true //(1)!
            keyPrefix = "mykey" //(2)!
            expireAfterWrite = "10s" //(3)!
            expireAfterAccess = "10s" //(4)!
            telemetry {
                logging {
                    enabled = false //(5)!
                }
                metrics {
                    enabled = false //(6)!
                    slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(7)!
                    tags = { //(8)!
                        "key1" = "value1"
                    }
                }
                tracing {
                    enabled = true //(9)!
                    attributes = { //(10)!
                        "key1" = "value1"
                    }
                }
            }
        }
    }
    ```

    1.  Включает кэш; при значении `false` все операции кэша превращаются в пустые, а `computeIfAbsent` всегда вызывает загрузчик (по умолчанию: `true`)
    2.  Префикс ключа для конкретного кэша, используется во избежание коллизий ключей в одной базе данных `Redis`; может быть пустой строкой, тогда ключи будут без префикса (`обязательный`, без значения по умолчанию)
    3.  Устанавливает время [истечения](https://redis.io/commands/psetex/) значения при записи (по умолчанию не указано, опционально)
    4.  Устанавливает время [истечения](https://redis.io/commands/getex/) значения при чтении (по умолчанию не указано, опционально)
    5.  Включает логирование кэша (по умолчанию: `false`)
    6.  Включает метрики кэша (по умолчанию: `false`)
    7.  Настройка [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    8.  Настройка тегов для метрик (по умолчанию: `{}`)
    9.  Включает трассировку кэша (по умолчанию: `true`)
    10. Настройка атрибутов для трассировки (по умолчанию: `{}`)

=== ":simple-yaml: `YAML`"

    ```yaml
    mycache:
      config:
        enabled: true #(1)!
        keyPrefix: "mykey" #(2)!
        expireAfterWrite: "10s" #(3)!
        expireAfterAccess: "10s" #(4)!
        telemetry:
          logging:
            enabled: false #(5)!
          metrics:
            enabled: false #(6)!
            slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(7)!
            tags: #(8)!
              key1: value1
          tracing:
            enabled: true #(9)!
            attributes: #(10)!
              key1: value1
    ```

    1.  Включает кэш; при значении `false` все операции кэша превращаются в пустые, а `computeIfAbsent` всегда вызывает загрузчик (по умолчанию: `true`)
    2.  Префикс ключа для конкретного кэша, используется во избежание коллизий ключей в одной базе данных `Redis`; может быть пустой строкой, тогда ключи будут без префикса (`обязательный`, без значения по умолчанию)
    3.  Устанавливает время [истечения](https://redis.io/commands/psetex/) значения при записи (по умолчанию не указано, опционально)
    4.  Устанавливает время [истечения](https://redis.io/commands/getex/) значения при чтении (по умолчанию не указано, опционально)
    5.  Включает логирование кэша (по умолчанию: `false`)
    6.  Включает метрики кэша (по умолчанию: `false`)
    7.  Настройка [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    8.  Настройка тегов для метрик (по умолчанию: `{}`)
    9.  Включает трассировку кэша (по умолчанию: `true`)
    10. Настройка атрибутов для трассировки (по умолчанию: `{}`)

Параметр `keyPrefix` обязателен, но может быть пустой строкой. О пустом префиксе при старте выводится предупреждение,
поскольку в этом случае `invalidateAll()` не может просканировать префикс и выполняет `FLUSHALL`, очищая всю базу данных `Redis`.

Метрики модуля описаны в разделе [Справочник метрик](metrics.md#cache), а метрики драйвера —
в разделе [Redis / Lettuce](metrics.md#redis-lettuce).
Собственная телеметрия кэша подключается регистрацией собственного компонента `RedisCacheTelemetryFactory` или `CaffeineCacheTelemetryFactory`,
который переопределяет `@DefaultComponent` из модуля. Если нужно сохранить поведение по умолчанию и изменить только его часть,
зарегистрируйте наследника `DefaultRedisCacheLoggerFactory` / `DefaultRedisCacheMetricsFactory`
(или их аналогов для `Caffeine`) — фабрика телеметрии по умолчанию подхватывает такие компоненты как опциональные зависимости.

### Мапперы ключей и значений { #redis-mappers }

`Redis` хранит ключи и значения как массивы байт, поэтому `RedisCache` использует два вида мапперов:

- `RedisCacheKeyMapper<K>` превращает ключ кэша в `byte[]`.
- `RedisCacheValueMapper<V>` записывает значение кэша в `byte[]` и читает его обратно.

Обычные ключи строятся через `RedisCacheKeyMapper` для типа ключа. Встроенные мапперы доступны для `String`, `byte[]`,
чисел, `BigInteger`, `BigDecimal`, `UUID`, `Boolean`, `Character`, `Instant`, `LocalDateTime`, `LocalDate`, `ZonedDateTime`,
`Duration`, `Period`, `Enum` и `Collection<T>`, если маппер для `T` также доступен.
Для `Enum` используется `toString()`, поэтому его можно переопределить, если нужен другой формат ключа.

Для значений встроенные реализации `RedisCacheValueMapper` доступны для тех же простых типов, типов даты/времени, `Enum` и `byte[]`.
Если требуется другое представление, зарегистрируйте собственный компонент `RedisCacheValueMapper<V>` или `RedisCacheKeyMapper<K>`.
Оба контракта являются компонентами графа, поэтому собственный маппер должен быть помечен `@Component`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class UserIdRedisKeyMapper implements RedisCacheKeyMapper<UserId> {

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

Самый частый случай — хранение объекта в виде `JSON`. Пометьте тип значения аннотацией `@Json`, чтобы `Kora` сгенерировала для него
`JsonWriter` и `JsonReader`, и укажите `@Json` также на аргументе типа значения в контракте кэша: встроенный маппер значений `JSON`
зарегистрирован под тегом `@Json`, поэтому внедряется только туда, где аргумент типа значения несёт этот тег.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
    public record UserData(String id, String name) { }

    @Cache("mycache.config")
    public interface MyCache extends RedisCache<String, @Json UserData> { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    data class UserData(val id: String, val name: String)

    @Cache("mycache.config")
    interface MyCache : RedisCache<String, @Json UserData>
    ```

Чтобы использовать для такого типа другое представление, уберите тег `@Json` с аргумента типа и зарегистрируйте
собственный компонент `RedisCacheValueMapper<V>`.

Для составного ключа на основе `record` или `data class` Kora генерирует отдельный `RedisCacheKeyMapper` для всего ключа как `@DefaultComponent`.
Он получает маппер для каждого поля, преобразует каждое поле в `byte[]` и объединяет части через `RedisCacheKeyMapper.DELIMITER` (`:`).
Порядок частей соответствует порядку компонентов `record` или свойств `data class`.
Если тип ключа не является `record` или `data class`, маппер не генерируется и `RedisCacheKeyMapper` для типа ключа нужно предоставить самостоятельно.

Для одиночного ключа встроенные реализации `RedisCacheKeyMapper` могут кодировать `null` специальным байтовым значением.
В составном ключе результат отображения каждого поля должен быть не-`null`: если собственный `RedisCacheKeyMapper` для поля вернёт `null`,
создание ключа завершится ошибкой. Для необязательных полей составного ключа собственный маппер должен явно кодировать `null`
стабильным байтовым значением.

#### Configurer { #configurator }

Клиент `Lettuce` собирается фабрикой `LettuceFactory`, и его можно донастроить перед созданием, зарегистрировав компоненты `Configurer`.
`Configurer` — это `io.koraframework.common.Configurer`, контракт с единственным методом `T configure(T t)`.
Донастроить можно три билдера: `DefaultClientResources.Builder` для общих ресурсов клиента,
`ClientOptions.Builder` для обычного клиента и `ClusterClientOptions.Builder` для кластерного клиента.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MyLettuceResourcesConfigurer implements Configurer<DefaultClientResources.Builder> {

        @Override
        public DefaultClientResources.Builder configure(DefaultClientResources.Builder builder) {
            return builder.commandLatencyRecorder(CommandLatencyRecorder.disabled());
        }
    }

    @Component
    public final class MyLettuceOptionsConfigurer implements Configurer<ClientOptions.Builder> {

        @Override
        public ClientOptions.Builder configure(ClientOptions.Builder builder) {
            return builder.autoReconnect(true);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyLettuceResourcesConfigurer : Configurer<DefaultClientResources.Builder> {

        override fun configure(builder: DefaultClientResources.Builder): DefaultClientResources.Builder {
            return builder.commandLatencyRecorder(CommandLatencyRecorder.disabled())
        }
    }

    @Component
    class MyLettuceOptionsConfigurer : Configurer<ClientOptions.Builder> {

        override fun configure(builder: ClientOptions.Builder): ClientOptions.Builder {
            return builder.autoReconnect(true)
        }
    }
    ```

Для сценариев за пределами типизированного кэша доступен для внедрения `RedisCacheClient` — низкоуровневый клиент, работающий с сырыми `byte[]`
(`scan`/`get`/`mget`/`getex`/`set`/`mset`/`psetex`/`del`/`flushAll`) поверх общего подключения `Lettuce`; именно на нём построен `RedisCache`.

## Использование { #usage }

Создание кэша потребует регистрации типизированного контракта `@Cache`.
Интерфейс контракта должен наследовать одну из реализаций `Kora`: `CaffeineCache` или `RedisCache`.
Для такого `@Cache` генерируется реализация и добавляется в граф, поэтому его можно внедрять как зависимость.

`@Cache` можно указывать только над интерфейсом, и этот интерфейс должен наследовать ровно один из двух контрактов —
одновременное наследование `CaffeineCache` и `RedisCache` приводит к ошибке компиляции.

Аргумент `value` в `@Cache` задаёт полный путь до конфигурации конкретного кэша.
Он указывает на объект конфигурации этого кэша, поэтому ключи конфигурации могут находиться как по вложенному пути вида `mycache.config { ... }`,
так и плоско прямо по указанному пути вида `my-cache { ... }`, как это сделано в примерах проектов. Оба варианта корректны; выберите один и держите ключи конфигурации внутри него.
Путь должен начинаться с буквы, иначе генерация приложения завершится ошибкой.

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

Если метод в `Java` возвращает `Optional<T>`, аспект кэширования умеет работать с такой сигнатурой напрямую.
Сам тип значения кэша может быть как `T`, так и `Optional<T>`:

- `CaffeineCache<String, String>` и метод `Optional<String> get(String key)`;
- `CaffeineCache<String, Optional<String>>` и метод `String get(String key)`;
- `CaffeineCache<String, Optional<String>>` и метод `Optional<String> get(String key)`.

Для `@Cacheable` это позволяет отличить отсутствие записи в кэше от результата метода, который тоже означает отсутствие данных.
Для `@CachePut` результат `Optional<T>` обрабатывается согласно типу значения кэша: если кэш хранит `Optional<T>`, сохраняется сам `Optional`,
а если кэш хранит `T`, сохраняется только присутствующее значение.

В `Kotlin` то же различие выражается через нullable-тип возвращаемого значения `T?`, обёртка `Optional` не используется.

### Императивный подход { #imperative }

Кэши доступны для внедрения как зависимости по интерфейсу и могут использоваться совместно с декларативными операциями.

`Cache` предоставляет `get(...)`, `put(...)`, `computeIfAbsent(...)`, `invalidate(...)`, `invalidateAll()`,
а также пакетные варианты для коллекции ключей или карты значений.
Методы `computeIfAbsent(...)` сначала пытаются получить значение из кэша, а при промахе вызывают переданную функцию загрузки и сохраняют результат.

`CaffeineCache` дополнительно предоставляет `getAll()`, который возвращает все ключи и значения, находящиеся в памяти.
`RedisCache` дополнительно предоставляет методы ручного управления временем жизни, описанные [ниже](#redis-expiration-override).

`RedisCache` никогда не пробрасывает транспортные ошибки вызывающему коду: неудачная операция фиксируется в телеметрии и деградирует
до промаха при чтении либо до молчаливого пропуска при записи, поэтому недоступность `Redis` не ломает бизнес-метод.

#### Композитный кэш через `Cache.Builder` { #builder-composite-cache }

Если композитный кэш нужен в императивном коде, его можно собрать как фасад через `Cache.Builder`.
Порядок уровней определяется порядком добавления: обычно первым добавляют быстрый локальный кэш, например `Caffeine`,
а следом — более общий кэш, например `Redis`.

- `get(key)` проверяет кэши по порядку и возвращает первое найденное значение.
- `put(...)`, `invalidate(...)` и `invalidateAll()` выполняются во всех кэшах.
- `computeIfAbsent(...)` проверяет кэши по порядку; если значение найдено на нижнем уровне, оно записывается в предыдущие уровни.
- Если значения нет ни на одном уровне, вызывается функция загрузки и результат записывается во все кэши.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Cache("mycache.caffeine.config")
    public interface MyCaffeineCache extends CaffeineCache<String, String> { }

    @Cache("mycache.redis.config")
    public interface MyRedisCache extends RedisCache<String, String> { }

    @KoraApp
    public interface Application extends CaffeineCacheModule, LettuceRedisCacheModule {

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
    interface Application : CaffeineCacheModule, LettuceRedisCacheModule {

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

Фасад, собранный через `Cache.Builder`, не поддерживает прямой `get(Collection<K>)` и выбрасывает на него `UnsupportedOperationException`.
Для пакетной загрузки используйте `computeIfAbsent(Collection<K>, Function<Set<K>, Map<K, V>>)`.

#### Ручное управление временем жизни в Redis { #redis-expiration-override }

Помимо общего набора методов `Cache`, `RedisCache` добавляет методы, переопределяющие настроенный `expireAfterWrite` для отдельной записи.
`putExpireAfterWrite(key, value, Duration)` и его пакетная перегрузка для `Map` применяют переданный `Duration` именно к этой записи
вместо значения из конфигурации. Эти методы доступны только для `Redis`.

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

Один метод несёт ровно один вид операции кэширования. Совмещение `@Cacheable` с `@CachePut`
либо `@CacheInvalidate` с `@CacheInvalidateAll` на одном методе приводит к ошибке компиляции.

#### Получение { #get }

Чтобы кэшировать и получать значение из кэша для метода `get()`, укажите над ним аннотацию `@Cacheable`.
Если значение найдено в кэше, исходный метод не вызывается; если значения нет, метод выполняется и результат сохраняется в кэш.

Ключ кэша строится из аргументов метода, порядок аргументов имеет значение. В данном случае он строится из `arg1`.

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
    open class SomeService {

        @Cacheable(MyCache::class)
        open fun get(arg1: String): String {
            // do something
        }
    }
    ```

`@Cacheable` требует хотя бы один аргумент метода для ключа; метод без аргументов не пройдёт компиляцию.

#### Запись { #put }

Чтобы добавлять значения в кэш методом `put()`, укажите над ним аннотацию `@CachePut`.
Метод с `@CachePut` вызывается всегда, а его результат помещается в кэш, указанный в `value`.

Ключ кэша строится из аргументов метода, порядок аргументов имеет значение. В данном случае он строится из `arg1`.

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
    open class SomeService {

        @CachePut(MyCache::class)
        open fun put(arg1: String): String {
            // do something
        }
    }
    ```

#### Удаление { #invalidate }

Чтобы удалить значение из кэша по ключу методом `evict()`, укажите над ним аннотацию `@CacheInvalidate`.
Метод с `@CacheInvalidate` вызывается, а затем значение удаляется по ключу из кэша, указанного в `value`.

Ключ кэша строится из аргументов метода, порядок аргументов имеет значение. В данном случае он строится из `arg1`.

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
    open class SomeService {

        @CacheInvalidate(MyCache::class)
        open fun evict(arg1: String) {
            // do something
        }
    }
    ```

#### Удаление всего { #invalidate-all }

Чтобы удалить все значения из кэша методом `evictAll()`, укажите над ним аннотацию `@CacheInvalidateAll`.

Метод с `@CacheInvalidateAll` вызывается, а затем из кэша, указанного в `value`, удаляются все значения.
Ключ кэша при этом не строится, поэтому метод может принимать любые аргументы или не принимать их вовсе.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @CacheInvalidateAll(MyCache.class)
        public void evictAll() {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    open class SomeService {

        @CacheInvalidateAll(MyCache::class)
        open fun evictAll() {
            // do something
        }
    }
    ```

Для кэша на `Redis` метод `invalidateAll()` сканирует ключи с настроенным `keyPrefix` и удаляет их.
Если `keyPrefix` — пустая строка, вместо этого выполняется `FLUSHALL` для всей базы данных.

#### Режим выполнения { #cache-mode }

У каждой аннотации кэширования есть атрибут `mode` типа `CacheMode` с двумя значениями:

- `CacheMode.SYNC` (по умолчанию) — запись в кэш происходит в вызывающем потоке до возврата из метода.
- `CacheMode.ASYNC` — запись в кэш отправляется в отдельный `Executor`, и метод возвращается, не дожидаясь её завершения.

`ASYNC` влияет только на записывающую часть операции: `put` для `@Cacheable` и `@CachePut`,
`invalidate` для `@CacheInvalidate` и `invalidateAll` для `@CacheInvalidateAll`.
Чтение кэша в `@Cacheable` остаётся синхронным, поскольку именно его результат определяет, будет ли вызван исходный метод.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @Cacheable(value = MyCache.class, mode = CacheMode.ASYNC)
        public String get(String arg1) {
            // do something
        }

        @CacheInvalidateAll(value = MyCache.class, mode = CacheMode.ASYNC)
        public void evictAll() {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    open class SomeService {

        @Cacheable(value = MyCache::class, mode = CacheMode.ASYNC)
        open fun get(arg1: String): String {
            // do something
        }

        @CacheInvalidateAll(value = MyCache::class, mode = CacheMode.ASYNC)
        open fun evictAll() {
            // do something
        }
    }
    ```

Асинхронная операция выполняется на `Executor`, связанном тегом `@Tag(CacheMode.class)`.
`CacheCommonModule` поставляет его как `@DefaultComponent`, который запускает виртуальный поток на каждую операцию и логирует неудачную операцию на уровне `WARN`.
Собственный компонент `@Tag(CacheMode.class) Executor` переопределяет реализацию по умолчанию.

Для `CaffeineCache` режим `ASYNC` игнорируется, поскольку запись в память не имеет смысла выносить в другой поток; процессор сообщает об этом предупреждением компиляции.

#### Композитный кэш { #composite-cache }

Если требуется использовать несколько кэшей, подключите нужные модули и укажите несколько аннотаций над методом.
Например, так можно объединить быстрый локальный уровень на `Caffeine` и общий уровень на `Redis`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends LettuceRedisCacheModule, CaffeineCacheModule {

        @Cache("mycache.caffeine.config")
        interface MyCaffeineCache extends CaffeineCache<String, String> { }

        @Cache("mycache.redis.config")
        interface MyRedisCache extends RedisCache<String, String> { }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : LettuceRedisCacheModule, CaffeineCacheModule {

        @Cache("mycache.caffeine.config")
        interface MyCaffeineCache : CaffeineCache<String, String>

        @Cache("mycache.redis.config")
        interface MyRedisCache : RedisCache<String, String>
    }
    ```

И сам аннотируемый класс:

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
    open class SomeService {

        @Cacheable(MyCaffeineCache::class)
        @Cacheable(MyRedisCache::class)
        open fun get(arg1: String): String {
            // do something
        }
    }
    ```

Порядок обращения соответствует порядку аннотаций над методом сверху вниз.
Для `@Cacheable` это значит, что сначала проверяется верхний кэш; при промахе проверяется следующий,
а после того как значение найдено на нижнем уровне, оно записывается обратно во все ранее проверенные уровни.
Если значения нет ни на одном уровне, вызывается исходный метод и результат записывается в каждый перечисленный кэш.
Та же модель композиции работает для повторяемых `@CachePut`, `@CacheInvalidate` и `@CacheInvalidateAll`: метод вызывается один раз,
а затем результат записывается во все перечисленные кэши либо во всех перечисленных кэшах выполняется удаление.
Контейнерные аннотации `@Cacheables`, `@CachePuts`, `@CacheInvalidates` и `@CacheInvalidateAlls` также можно использовать, если такая форма удобнее.

Все повторяющиеся аннотации над одним методом должны объявлять одинаковый список `args`; разные списки аргументов ключа на одном методе приводят к ошибке компиляции.

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

Если аргумент нельзя использовать напрямую как ключ кэша, реализации потребуется маппер
с интерфейсом `CacheKeyMapper`. Если для ключа используются два аргумента, потребуется `CacheKeyMapper2`, если три — `CacheKeyMapper3`, и так далее до `CacheKeyMapper9`.
Более девяти аргументов ключа не поддерживается.

Такой маппер можно указать вручную через `@Mapping`. Маппер внедряется в сгенерированный аспект из графа зависимостей,
поэтому его класс должен быть зарегистрирован как компонент через `@Component` — включая вложенные классы.

Пример преобразования сложного объекта в простой ключ кэша:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        public record UserContext(String userId, String traceId) { }

        @Component
        public static final class UserContextMapping implements CacheKeyMapper<String, UserContext> {

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
    open class SomeService {

        data class UserContext(val userId: String, val traceId: String)

        @Component
        class UserContextMapping : CacheKeyMapper<String, UserContext> {
            override fun map(arg: UserContext): String {
                return arg.userId
            }
        }

        @Mapping(UserContextMapping::class)
        @Cacheable(MyCache::class)
        open fun get(context: UserContext): String {
            // do something
        }
    }
    ```

Если разным методам нужны разные мапперы с одинаковой сигнатурой, компоненты мапперов можно различить,
добавив `@Tag` рядом с `@Mapping` над методом и над самим компонентом маппера.

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

Ключ строится вызовом публичного конструктора типа ключа, типы параметров которого по порядку соответствуют аргументам метода.

Если используется `RedisCache`, для составного ключа генерируется `RedisCacheKeyMapper`.
Он использует маппер для каждого поля ключа и ожидает, что результат отображения каждого поля будет не-`null`.
Встроенные мапперы могут кодировать `null` специальным значением, а собственные мапперы должны делать это явно.

### Порядок аргументов { #argument-ordering }

Если метод принимает аргументы, которые нужно исключить из составного ключа, либо порядок аргументов не совпадает
с порядком аргументов конструктора составного ключа, используйте атрибут `args` и укажите,
какие аргументы метода использовать и в каком порядке.

`args` задаёт полный набор аргументов метода, используемых для построения ключа. Каждое имя должно совпадать с именем аргумента метода,
а порядок должен соответствовать типу ключа: для одного аргумента — типу ключа `Cache<K, V>`; для составного ключа —
порядку аргументов конструктора `record` или `data class`.
Если имя не совпадает ни с одним аргументом метода, генерация приложения завершается ошибкой.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @Cacheable(value = MyCache.class, args = {"arg1", "arg2"})
        public String get(Long arg2, String arg3, String arg1) {
            // do something
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    open class SomeService {

        @Cacheable(value = MyCache::class, args = ["arg1", "arg2"])
        open fun get(arg2: Long, arg3: String, arg1: String): String {
            // do something
        }
    }
    ```

Если перечисленные аргументы не подходят ни под один конструктор типа ключа — отличается порядок или типы —
аспект переключается на `CacheKeyMapperN` для этого набора аргументов и ожидает его в графе зависимостей.
Сборка тогда упадёт на разрешении графа, пока такой маппер не зарегистрирован, поэтому либо исправьте порядок аргументов, либо предоставьте маппер через `@Mapping`.

## Loadable Cache { #loadable-cache }

Библиотека предоставляет компонент `LoadableCache`, который объединяет операции `get` и `put` без использования аспектов.
Он полезен, когда загрузкой значения нужно управлять вручную, сохранив стандартную логику: сначала проверить кэш,
а при промахе загрузить данные и сохранить их.

`Cache.asLoadable(Function<Collection<K>, Map<K, V>>)` создаёт `LoadableCache` вокруг пакетного загрузчика, а
`Cache.asLoadableSimple(Function<K, V>)` — вокруг загрузчика одного ключа.
`LoadableCache` предоставляет `get(K)` и `get(Collection<K>)`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Cache("mycache.config")
    public interface MyCache extends CaffeineCache<String, String> { }

    @KoraApp
    public interface Application extends CaffeineCacheModule {

        default LoadableCache<String, String> loadableCache(MyCache cache, SomeService someService) {
            return cache.asLoadable(someService::loadEntities);
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
            return cache.asLoadable(someService::loadEntities)
        }
    }
    ```

То же самое применимо к `RedisCache`, поскольку оба контракта кэша наследуют общий интерфейс `Cache`.

## Сигнатуры { #signatures }

Доступные сигнатуры для методов, поддерживаемые аннотациями:

===! ":fontawesome-brands-java: `Java`"

    Класс не должен быть `final`, чтобы работали аспекты.

    Под `T` подразумевается тип возвращаемого значения.

    - `T myMethod()`
    - `Optional<T> myMethod()`

    `@Cacheable` и `@CachePut` требуют возвращаемого значения и не могут применяться к `void`.
    `@CacheInvalidate` и `@CacheInvalidateAll` могут применяться к методам без результата.

    Асинхронные и реактивные типы возвращаемого значения аспектами кэширования не поддерживаются:
    `CompletionStage<T>`, `Future<T>`, `Publisher<T>`, `Mono<T>` и `Flux<T>` отклоняются на этапе компиляции.

=== ":simple-kotlin: `Kotlin`"

    Класс должен быть `open`, чтобы работали аспекты.

    Под `T` подразумевается тип возвращаемого значения, либо `T`, либо `T?`, либо `Unit`.

    - `myMethod(): T`

    `@Cacheable` и `@CachePut` требуют возвращаемого значения и не могут применяться к `Unit`.
    `@CacheInvalidate` и `@CacheInvalidateAll` могут применяться к методам без результата.

    Асинхронные и реактивные типы возвращаемого значения аспектами кэширования не поддерживаются:
    `CompletionStage<T>`, `Future<T>` и `Publisher<T>` отклоняются на этапе компиляции.
