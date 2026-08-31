---
description: "Explains Kora cache module, cache annotations, Caffeine and Redis cache backends, cache key mapping, telemetry, invalidation, execution modes and supported method signatures. Use when working with @Cache, @Cacheable, @CachePut, @CacheInvalidate, @CacheInvalidateAll, @CacheMode, CaffeineCacheModule, LettuceRedisCacheModule, CacheKeyMapper, LoadableCache."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora cache module, cache annotations, Caffeine and Redis cache backends, cache key mapping, telemetry, invalidation, execution modes and supported method signatures; key triggers include @Cache, @Cacheable, @CachePut, @CacheInvalidate, @CacheInvalidateAll, CacheMode, CaffeineCacheModule, LettuceRedisCacheModule, RedisCacheClient, CacheKeyMapper, LoadableCache."
---

The module provides typed caches for storing computation results and reusable data,
so expensive operations do not have to run on every access. A cache can be used declaratively through method annotations
or imperatively through an injected interface, with local `Caffeine` and external `Redis` available as storage backends.
Local `Caffeine` is useful for fast in-process storage, while `Redis` is suitable for a shared cache used by several application instances.

The whole cache contract is synchronous: `Cache<K, V>` returns values directly, and cache aspects are applied to synchronous methods.

For a step-by-step walkthrough before the reference details, see [Cache](../guides/cache.md) and [Multi-Level Cache](../guides/cache-multi-level.md).

## Caffeine { #caffeine }

Implementation based on the [Caffeine](https://github.com/ben-manes/caffeine) library for an in-memory application cache.

### Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:cache-caffeine"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends CaffeineCacheModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:cache-caffeine")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : CaffeineCacheModule
    ```

### Configuration { #configuration }

Example of a complete configuration for a cache at `mycache.config`; parameters are described in the `CaffeineCacheConfig` class (example values or default values are shown):

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

    1.  Enables the cache; when `false` every cache operation becomes a no-op and `computeIfAbsent` always calls the loader (default: `true`)
    2.  Time after which the value is removed from the cache; counted after the value is written (default not specified, optional)
    3.  Time after which the value is removed from the cache; counted after the value is read (default not specified, optional)
    4.  Initial cache size, helps avoid resizing when the number of values grows quickly (default not specified, optional)
    5.  Maximum cache size; when the boundary is reached **or slightly earlier**, [least relevant values](https://blog.skillfactory.ru/glossary/lru/) are evicted (default: `100000`)
    6.  Enables cache logging (default: `false`)
    7.  Enables cache metrics; also controls whether the standard `Micrometer` `Caffeine` metrics are registered (default: `false`)
    8.  [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) configuration for metrics, values are durations and bare numbers mean milliseconds (default: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    9.  Tags configuration for metrics (default: `{}`)
    10. Enables cache tracing (default: `true`)
    11. Attributes configuration for tracing (default: `{}`)

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

    1.  Enables the cache; when `false` every cache operation becomes a no-op and `computeIfAbsent` always calls the loader (default: `true`)
    2.  Time after which the value is removed from the cache; counted after the value is written (default not specified, optional)
    3.  Time after which the value is removed from the cache; counted after the value is read (default not specified, optional)
    4.  Initial cache size, helps avoid resizing when the number of values grows quickly (default not specified, optional)
    5.  Maximum cache size; when the boundary is reached **or slightly earlier**, [least relevant values](https://blog.skillfactory.ru/glossary/lru/) are evicted (default: `100000`)
    6.  Enables cache logging (default: `false`)
    7.  Enables cache metrics; also controls whether the standard `Micrometer` `Caffeine` metrics are registered (default: `false`)
    8.  [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) configuration for metrics, values are durations and bare numbers mean milliseconds (default: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    9.  Tags configuration for metrics (default: `{}`)
    10. Enables cache tracing (default: `true`)
    11. Attributes configuration for tracing (default: `{}`)

The underlying `Caffeine` cache is built by a `CaffeineCacheFactory` supplied as a `@DefaultComponent`.
If tuning beyond the configuration options above is required (for example custom eviction, weak keys, or a custom weigher),
register your own `CaffeineCacheFactory` component to override the default and customize the `Caffeine` builder directly.

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

Overriding the factory also replaces the default metric registration, so the standard `Micrometer` `Caffeine` metrics
have to be wired manually if they are still required.

## Redis { #redis }

Implementation based on in-memory database [Redis](https://redis.io/docs/about/) and connection driver [Lettuce](https://github.com/lettuce-io/lettuce-core).

### Dependency { #dependency-2 }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:cache-redis-lettuce"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends LettuceRedisCacheModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:cache-redis-lettuce")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : LettuceRedisCacheModule
    ```

`LettuceRedisCacheModule` is the entry point for the `Redis` cache: it extends `RedisCacheModule` and `LettuceModule`,
and provides the `RedisCacheClient` on top of the shared `Lettuce` connection.

The `RedisCacheModule` from the `cache-redis-common` artifact is transport-neutral: it contributes the cache telemetry factory,
key mappers, and value mappers, but does **not** provide a `RedisCacheClient`. It is useful only when a different `Redis` transport
is plugged in by supplying an own `RedisCacheClient` implementation.

### Configuration { #configuration-2 }

The `Lettuce` driver must be configured separately to connect to `Redis`.
A single connection is used for all `Redis` caches.

Basic Lettuce configuration parameters:

===! ":material-code-json: `Hocon`"

    ```javascript
    lettuce {
        uri = "redis://localhost:6379" //(1)!
        commandTimeout = "30s" //(2)!
    }
    ```

    1.  `URI` for connecting to `Redis` (`required`, no default)
    2.  Command execution timeout (default: `30s`)

=== ":simple-yaml: `YAML`"

    ```yaml
    lettuce:
      uri: "redis://localhost:6379" #(1)!
      commandTimeout: "30s" #(2)!
    ```

    1.  `URI` for connecting to `Redis` (`required`, no default)
    2.  Command execution timeout (default: `30s`)

??? note "Full Configuration"

    Example of a complete configuration for the `Lettuce` driver; parameters are described in the `LettuceConfig` class (example values or default values are shown):

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

        1.  `URI` for connecting to `Redis` (`required`, no default).
            Single-server connection: `redis://localhost:6379`.
            Multi-server connection: `redis://localhost:6379,localhost:6380`.
            Connection with `SSL`/`TLS`: `rediss://localhost:6380`.
        2.  Username for the connection (default not specified, optional)
        3.  User password for the connection (default not specified, optional)
        4.  Database number for the connection (default not specified, optional)
        5.  Connection protocol, can be `RESP2` or `RESP3` (default: `RESP3`)
        6.  Socket connection timeout (default: `10s`)
        7.  Command execution timeout (default: `30s`)
        8.  Create a cluster client even with a single connection `URI` (default: `false`)
        9.  Cipher algorithms for a secure connection between client and server (default: `[]`)
        10. Timeout for establishing a secure connection with the server (default: `10s`)
        11. Enables driver logging (default: `false`)
        12. Enables driver metrics (default: `false`)
        13. [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) configuration for metrics (default: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
        14. Tags configuration for metrics (default: `{}`)

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

        1.  `URI` for connecting to `Redis` (`required`, no default).
            Single-server connection: `redis://localhost:6379`.
            Multi-server connection: `redis://localhost:6379,localhost:6380`.
            Connection with `SSL`/`TLS`: `rediss://localhost:6380`.
        2.  Username for the connection (default not specified, optional)
        3.  User password for the connection (default not specified, optional)
        4.  Database number for the connection (default not specified, optional)
        5.  Connection protocol, can be `RESP2` or `RESP3` (default: `RESP3`)
        6.  Socket connection timeout (default: `10s`)
        7.  Command execution timeout (default: `30s`)
        8.  Create a cluster client even with a single connection `URI` (default: `false`)
        9.  Cipher algorithms for a secure connection between client and server (default: `[]`)
        10. Timeout for establishing a secure connection with the server (default: `10s`)
        11. Enables driver logging (default: `false`)
        12. Enables driver metrics (default: `false`)
        13. [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) configuration for metrics (default: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
        14. Tags configuration for metrics (default: `{}`)

If a single `URI` is configured and `forceClusterClient` is `false`, a standalone `RedisClient` is created;
otherwise a `RedisClusterClient` is created for the list of `URI`s.

The `Redis` cache configuration defines behavior for a specific cache.

Example of a complete configuration for a cache at `mycache.config`; parameters are described in the `RedisCacheConfig` class (example values are shown):

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

    1.  Enables the cache; when `false` every cache operation becomes a no-op and `computeIfAbsent` always calls the loader (default: `true`)
    2.  Key prefix for the specific cache, used to avoid key collisions in one `Redis` database; can be an empty string, then keys will have no prefix (`required`, no default)
    3.  Sets the value [expiration](https://redis.io/commands/psetex/) time on write (default not specified, optional)
    4.  Sets the value [expiration](https://redis.io/commands/getex/) time on read (default not specified, optional)
    5.  Enables cache logging (default: `false`)
    6.  Enables cache metrics (default: `false`)
    7.  [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) configuration for metrics (default: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    8.  Tags configuration for metrics (default: `{}`)
    9.  Enables cache tracing (default: `true`)
    10. Attributes configuration for tracing (default: `{}`)

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

    1.  Enables the cache; when `false` every cache operation becomes a no-op and `computeIfAbsent` always calls the loader (default: `true`)
    2.  Key prefix for the specific cache, used to avoid key collisions in one `Redis` database; can be an empty string, then keys will have no prefix (`required`, no default)
    3.  Sets the value [expiration](https://redis.io/commands/psetex/) time on write (default not specified, optional)
    4.  Sets the value [expiration](https://redis.io/commands/getex/) time on read (default not specified, optional)
    5.  Enables cache logging (default: `false`)
    6.  Enables cache metrics (default: `false`)
    7.  [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) configuration for metrics (default: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    8.  Tags configuration for metrics (default: `{}`)
    9.  Enables cache tracing (default: `true`)
    10. Attributes configuration for tracing (default: `{}`)

`keyPrefix` is required but may be an empty string. An empty prefix is reported with a warning at startup, because in that case
`invalidateAll()` cannot scan a prefix and falls back to `FLUSHALL`, which wipes the whole `Redis` database.

Module metrics are described in the [Metrics Reference](metrics.md#cache) section, and the driver metrics
in the [Redis / Lettuce](metrics.md#redis-lettuce) section.
Custom cache telemetry is plugged in by registering your own `RedisCacheTelemetryFactory` or `CaffeineCacheTelemetryFactory` component,
which overrides the `@DefaultComponent` supplied by the module. To keep the default behavior and change only one part of it,
register a subclass of `DefaultRedisCacheLoggerFactory` / `DefaultRedisCacheMetricsFactory`
(or their `Caffeine` counterparts) — the default telemetry factory picks such components up as optional dependencies.

### Key and Value Mappers { #redis-mappers }

`Redis` stores keys and values as byte arrays, so `RedisCache` uses two kinds of mappers:

- `RedisCacheKeyMapper<K>` turns a cache key into `byte[]`.
- `RedisCacheValueMapper<V>` writes a cache value to `byte[]` and reads it back.

Regular keys are built through `RedisCacheKeyMapper` for the key type. Built-in mappers are available for `String`, `byte[]`,
numbers, `BigInteger`, `BigDecimal`, `UUID`, `Boolean`, `Character`, `Instant`, `LocalDateTime`, `LocalDate`, `ZonedDateTime`,
`Duration`, `Period`, `Enum`, and `Collection<T>` when a mapper for `T` is also available.
For `Enum`, `toString()` is used, so it can be overridden when another key format is needed.

For values, built-in `RedisCacheValueMapper` implementations are available for the same simple types, date/time types, `Enum`, and `byte[]`.
If another representation is needed, register your own `RedisCacheValueMapper<V>` or `RedisCacheKeyMapper<K>` component.
Both contracts are graph components, so a custom mapper must be annotated with `@Component`.

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

The common case is storing an object value as `JSON`. Annotate the value type with `@Json` so that `Kora` generates a `JsonWriter`
and `JsonReader` for it, and mark the value type argument of the cache contract with `@Json` as well: the built-in `JSON` value mapper
is registered under the `@Json` tag, so it is only injected where the value type argument carries that tag.

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

To use a different representation for such a type, drop the `@Json` tag from the type argument and register your own
`RedisCacheValueMapper<V>` component instead.

For a composite key based on a `record` or `data class`, Kora generates a separate `RedisCacheKeyMapper` for the whole key as a `@DefaultComponent`.
It receives a mapper for each field, converts every field to `byte[]`, and joins the parts with `RedisCacheKeyMapper.DELIMITER` (`:`).
The part order matches the order of `record` components or `data class` properties.
For a key type that is not a `record` or `data class`, no mapper is generated and a `RedisCacheKeyMapper` for the key type has to be provided.

For a single key, built-in `RedisCacheKeyMapper` implementations can encode `null` as a special byte value.
In a composite key, each field mapping result must be non-`null`: if a custom `RedisCacheKeyMapper` for a field returns `null`,
key creation fails. For optional fields in a composite key, a custom mapper must explicitly encode `null`
as a stable byte value.

#### Configurer { #configurator }

The `Lettuce` client is assembled by `LettuceFactory` and can be customized before creation by registering `Configurer` components.
`Configurer` is `io.koraframework.common.Configurer`, a single-method contract `T configure(T t)`.
Three builders can be customized: `DefaultClientResources.Builder` for shared client resources,
`ClientOptions.Builder` for a standalone client, and `ClusterClientOptions.Builder` for a cluster client.

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

For advanced scenarios beyond the typed cache, `RedisCacheClient` is available for injection as a low-level client that operates on raw `byte[]`
(`scan`/`get`/`mget`/`getex`/`set`/`mset`/`psetex`/`del`/`flushAll`) over the shared `Lettuce` connection; it is the client that `RedisCache` is built on top of.

## Usage { #usage }

Creating a cache will require registering a typed `@Cache` contract.
The contract interface must extend one of the `Kora` implementations: `CaffeineCache` or `RedisCache`.
For such an `@Cache`, an implementation is generated and added to the graph, so it can be injected as a dependency.

`@Cache` can only be applied to an interface, and that interface must extend exactly one of the two contracts —
extending both `CaffeineCache` and `RedisCache` is a compilation error.

The `value` argument in `@Cache` defines the full path to the configuration of the specific cache.
It points at the configuration object of that cache, so the config keys can live under a nested path such as `mycache.config { ... }`,
or flat directly under the path such as `my-cache { ... }` as used in the example projects. Both forms are valid; pick one and keep the config keys under it.
The path must start with a letter, otherwise application generation fails.

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

### Optional Values { #optional-values }

If a `Java` method returns `Optional<T>`, the caching aspect can work with that signature directly.
The cache value type itself can be either `T` or `Optional<T>`:

- `CaffeineCache<String, String>` and method `Optional<String> get(String key)`;
- `CaffeineCache<String, Optional<String>>` and method `String get(String key)`;
- `CaffeineCache<String, Optional<String>>` and method `Optional<String> get(String key)`.

For `@Cacheable`, this makes it possible to distinguish a missing cache entry from a method result that also means no data.
For `@CachePut`, the `Optional<T>` result is handled according to the cache value type: if the cache stores `Optional<T>`, the `Optional` itself is stored,
and if the cache stores `T`, only a present value is stored.

In `Kotlin` the same distinction is expressed with a nullable return type `T?`, and no `Optional` wrapper is used.

### Imperative { #imperative }

Caches are available for injection as dependencies on the interface and can be used in conjunction with declarative operations.

`Cache` provides `get(...)`, `put(...)`, `computeIfAbsent(...)`, `invalidate(...)`, `invalidateAll()`,
as well as batch variants for a collection of keys or a map of values.
`computeIfAbsent(...)` methods first try to get a value from the cache; on a miss, they call the provided loader function and store the result.

`CaffeineCache` additionally provides `getAll()`, which returns every key and value currently held in memory.
`RedisCache` additionally provides the manual expiration methods described [below](#redis-expiration-override).

`RedisCache` never propagates transport errors to the caller: a failed operation is recorded in telemetry and degrades
to a cache miss on read or to a silent no-op on write, so a `Redis` outage does not break the business method.

#### Composite Cache With `Cache.Builder` { #builder-composite-cache }

If a composite cache is needed in imperative code, it can be built as a facade through `Cache.Builder`.
Layer order is defined by the add order: usually a fast local cache, such as `Caffeine`, is added first,
and a more shared cache, such as `Redis`, is added after it.

- `get(key)` checks caches in order and returns the first found value.
- `put(...)`, `invalidate(...)`, and `invalidateAll()` are executed in all caches.
- `computeIfAbsent(...)` checks caches in order; if a value is found in a lower layer, it is written into previous layers.
- If the value is missing in every layer, the loader function is called and the result is written into all caches.

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

The facade built through `Cache.Builder` does not support direct `get(Collection<K>)` and throws `UnsupportedOperationException` for it.
For batch loading, use `computeIfAbsent(Collection<K>, Function<Set<K>, Map<K, V>>)`.

#### Manual Redis expiration { #redis-expiration-override }

Beyond the shared `Cache` surface, `RedisCache` adds methods to override the configured `expireAfterWrite` for a single write.
`putExpireAfterWrite(key, value, Duration)` and its `Map` batch overload apply the provided `Duration` to that specific write
instead of the value from configuration. These methods are `Redis`-only.

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

### Declarative { #declarative }

All aspect examples below assume the cache implementation above.

One method carries exactly one kind of cache operation. Mixing `@Cacheable` with `@CachePut`,
or `@CacheInvalidate` with `@CacheInvalidateAll`, on the same method is a compilation error.

#### Get { #get }

To cache and retrieve a value from the cache for the `get()` method, annotate it with `@Cacheable`.
If the value is found in the cache, the original method is not called; if there is no value, the method is executed and the result is stored in the cache.

The cache key is built from method arguments, and argument order matters. In this case it is built from `arg1`.

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

`@Cacheable` requires at least one method argument for the key; a method without arguments fails at compile time.

#### Put { #put }

To add values to the cache via the `put()` method, annotate it with `@CachePut`.
The method with `@CachePut` is always called, and its result is put into the cache defined in `value`.

The cache key is built from method arguments, and argument order matters. In this case it is built from `arg1`.

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

#### Invalidate { #invalidate }

To remove a value from the cache by key via the `evict()` method, annotate it with `@CacheInvalidate`.
The method with `@CacheInvalidate` is called, and then the value is removed by key from the cache defined in `value`.

The cache key is built from method arguments, and argument order matters. In this case it is built from `arg1`.

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

#### Invalidate all { #invalidate-all }

To remove all values from the cache via the `evictAll()` method, annotate it with `@CacheInvalidateAll`.

The method with `@CacheInvalidateAll` is called, and then all values are removed from the cache defined in `value`.
No cache key is built, so the method may take any arguments or none at all.

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

For a `Redis` cache, `invalidateAll()` scans the keys with the configured `keyPrefix` and deletes them.
If `keyPrefix` is an empty string, it falls back to `FLUSHALL` for the whole database.

#### Execution mode { #cache-mode }

Every cache annotation has a `mode` attribute of type `CacheMode` with two values:

- `CacheMode.SYNC` (default) — the cache write happens on the calling thread before the method returns.
- `CacheMode.ASYNC` — the cache write is submitted to a dedicated `Executor` and the method returns without waiting for it.

`ASYNC` affects only the write side of the operation: `put` for `@Cacheable` and `@CachePut`,
`invalidate` for `@CacheInvalidate`, and `invalidateAll` for `@CacheInvalidateAll`.
The cache read performed by `@Cacheable` stays synchronous, because its result determines whether the original method is called.

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

The asynchronous operation runs on an `Executor` bound with `@Tag(CacheMode.class)`.
`CacheCommonModule` provides it as a `@DefaultComponent` that starts a virtual thread per operation and logs a failed operation at `WARN`.
A custom `@Tag(CacheMode.class) Executor` component overrides that default.

`ASYNC` is ignored for `CaffeineCache`, since an in-memory write is not worth offloading; the processor reports it with a compilation warning.

#### Composite cache { #composite-cache }

If several caches need to be used, connect the required modules and specify several annotations on the method.
For example, this can combine a fast local layer on `Caffeine` and a shared layer on `Redis`.

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

And the annotated class itself:

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

The call order follows the order of annotations on the method from top to bottom.
For `@Cacheable`, this means the upper cache is checked first; on a miss, the next cache is checked,
and after the value is found in a lower layer it is written back into all previously checked layers.
If no layer holds the value, the original method is called and the result is written into every listed cache.
The same composition model works for repeatable `@CachePut`, `@CacheInvalidate`, and `@CacheInvalidateAll`: the method is called once,
and then the result is written to all listed caches or invalidation is executed in all listed caches.
The container annotations `@Cacheables`, `@CachePuts`, `@CacheInvalidates`, and `@CacheInvalidateAlls` can also be used when that form is more convenient.

All repeated annotations on one method must declare the same `args` list; different key argument lists on one method are a compilation error.

## Key { #key }

If the cache key consists of one argument, register `Cache` with a signature that matches the key and value types.

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

### Conversion { #conversion }

If an argument cannot be used directly as a cache key, the implementation requires a mapper
with the `CacheKeyMapper` interface. If there are two arguments for the key, `CacheKeyMapper2` is required; if there are three, `CacheKeyMapper3` is required, and so on up to `CacheKeyMapper9`.
More than nine key arguments are not supported.

Such a mapper can be provided manually with `@Mapping`. The mapper is injected into the generated aspect from the dependency graph,
so its class must be registered as a component with `@Component` — nested classes included.

Example of converting a complex object into a simple cache key:

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

If several methods need different mappers with the same signature, the mapper components can be disambiguated
by adding `@Tag` next to `@Mapping` on the method and on the mapper component.

### Composite key { #composite-key }

If the cache key consists of several arguments, register `Cache` with a custom class
that describes that key.

Example for `Cache` where the composite key consists of two elements:

===! ":fontawesome-brands-java: `Java`"

    Create a custom `record` that describes the composite key.

    ```java
    @Cache("mycache.config")
    public interface MyCache extends CaffeineCache<MyCache.Key, String> {

        record Key(String k1, Long k2) { }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create a custom `data class` that describes the composite key.

    ```kotlin
    @Cache("mycache.config")
    interface MyCache : CaffeineCache<MyCache.Key, String> {

        data class Key(val k1: String, val k2: Long)
    }
    ```

The key is built by calling the public constructor of the key type whose parameter types match the method arguments in order.

If `RedisCache` is used, a `RedisCacheKeyMapper` is generated for the composite key.
It uses a mapper for each key field and expects the mapping result for every field to be non-`null`.
Built-in mappers can encode `null` with a special value, while custom mappers must do this explicitly.

### Argument ordering { #argument-ordering }

If the method accepts arguments that should be excluded from the composite key, or the argument order does not match
the order of the composite-key constructor arguments, use the `args` attribute and specify
which method arguments to use and in what order.

`args` defines the full set of method arguments used to build the key. Each name must match a method argument name,
and the order should match the key type: for a single argument, the `Cache<K, V>` key type; for a composite key,
the constructor argument order of the `record` or `data class`.
If a name does not match any method argument, application generation fails.

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

If the listed arguments do not fit any constructor of the key type — the order or the types differ —
the aspect falls back to a `CacheKeyMapperN` for that exact argument list and expects it in the dependency graph.
The build then fails at graph resolution unless such a mapper is registered, so either fix the argument order or supply a mapper with `@Mapping`.

## Loadable Cache { #loadable-cache }

The library provides the `LoadableCache` component, which combines `get` and `put` operations without using aspects.
It is useful when value loading must be controlled manually while keeping the standard logic: first check the cache,
and on a miss load the data and store it.

`Cache.asLoadable(Function<Collection<K>, Map<K, V>>)` builds a `LoadableCache` around a batch loader, and
`Cache.asLoadableSimple(Function<K, V>)` builds one around a single-key loader.
`LoadableCache` exposes `get(K)` and `get(Collection<K>)`.

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

The same applies to `RedisCache`, since both cache contracts extend the common `Cache` interface.

## Signatures { #signatures }

Available signatures for methods supported by annotations:

===! ":fontawesome-brands-java: `Java`"

    The class must not be `final` for aspects to work.

    The `T` refers to the type of the return value.

    - `T myMethod()`
    - `Optional<T> myMethod()`

    `@Cacheable` and `@CachePut` require a return value and cannot be applied to `void`.
    `@CacheInvalidate` and `@CacheInvalidateAll` can be applied to methods without a result.

    Asynchronous and reactive return types are not supported by cache aspects:
    `CompletionStage<T>`, `Future<T>`, `Publisher<T>`, `Mono<T>`, and `Flux<T>` are rejected at compile time.

=== ":simple-kotlin: `Kotlin`"

    The class must be `open` for aspects to work.

    By `T` we mean the type of the return value, either `T`, `T?`, or `Unit`.

    - `myMethod(): T`

    `@Cacheable` and `@CachePut` require a return value and cannot be applied to `Unit`.
    `@CacheInvalidate` and `@CacheInvalidateAll` can be applied to methods without a result.

    Asynchronous and reactive return types are not supported by cache aspects:
    `CompletionStage<T>`, `Future<T>`, and `Publisher<T>` are rejected at compile time.
