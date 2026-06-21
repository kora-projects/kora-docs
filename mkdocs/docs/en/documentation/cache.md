---
description: "Explains Kora cache module, cache annotations, Caffeine and Redis cache backends, cache key mapping, telemetry, invalidation, and async cache signatures. Use when working with @Cache, @Cacheable, @CachePut, @CacheInvalidate, CaffeineCacheModule, RedisCacheModule, CacheKeyMapper, LoadableCache."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora cache module, cache annotations, Caffeine and Redis cache backends, cache key mapping, telemetry, invalidation, and async cache signatures; key triggers include @Cache, @Cacheable, @CachePut, @CacheInvalidate, CaffeineCacheModule, RedisCacheModule, CacheKeyMapper, LoadableCache."
---

The module provides typed caches for storing computation results and reusable data,
so expensive operations do not have to run on every access. A cache can be used declaratively through method annotations
or imperatively through an injected interface, with local `Caffeine` and external `Redis` available as storage backends.
Local `Caffeine` is useful for fast in-process storage, while `Redis` is suitable for a shared cache used by several application instances.

For a step-by-step walkthrough before the reference details, see [Cache](../guides/cache.md) and [Multi-Level Cache](../guides/cache-multi-level.md).

## Caffeine { #caffeine }

Implementation based on the [Caffeine](https://github.com/ben-manes/caffeine) library for an in-memory application cache.

### Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:cache-caffeine"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends CaffeineCacheModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:cache-caffeine")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : CaffeineCacheModule
    ```

### Configuration { #configuration }

Example of a complete configuration for a cache at `mycache.config`; parameters are described in the `CaffeineCacheConfig` class (example values or default values are shown):

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

    1.  Time after which the value is removed from the cache; counted after the value is written (default not specified, optional)
    2.  Time after which the value is removed from the cache; counted after the value is read (default not specified, optional)
    3.  Initial cache size, helps avoid resizing when the number of values grows quickly (default not specified, optional)
    4.  Maximum cache size; when the boundary is reached **or slightly earlier**, [least relevant values](https://blog.skillfactory.ru/glossary/lru/) are evicted (default: `100000`)

=== ":simple-yaml: `YAML`"

    ```yaml
    mycache:
      config:
        expireAfterWrite: "10s" #(1)!
        expireAfterAccess: "10s" #(2)!
        initialSize: 10 #(3)!
        maximumSize: 100000 #(4)!
    ```

    1.  Time after which the value is removed from the cache; counted after the value is written (default not specified, optional)
    2.  Time after which the value is removed from the cache; counted after the value is read (default not specified, optional)
    3.  Initial cache size, helps avoid resizing when the number of values grows quickly (default not specified, optional)
    4.  Maximum cache size; when the boundary is reached **or slightly earlier**, [least relevant values](https://blog.skillfactory.ru/glossary/lru/) are evicted (default: `100000`)

## Redis { #redis }

Implementation based on in-memory database [Redis](https://redis.io/docs/about/) and connection driver [Lettuce](https://github.com/lettuce-io/lettuce-core).

### Dependency { #dependency-2 }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:cache-redis"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends RedisCacheModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:cache-redis")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : RedisCacheModule
    ```

### Configuration { #configuration-2 }

The `Lettuce` driver must be configured separately to connect to `Redis`.
A single connection is used for all `Redis` caches.

Example of a complete configuration for the `Lettuce` driver; parameters are described in the `LettuceClientConfig` class (example values or default values are shown):

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

    1.  `URI` for connecting to `Redis` (`required`, default not specified).
        Single-server connection: `redis://localhost:6379`.
        Multi-server connection: `redis://localhost:6379,localhost:6380`.
        Connection with `SSL`: `rediss://localhost:6380`.
        Connection with `TLS`: `redis+tls://localhost:6380`.
    2.  Username for the connection (default not specified, optional)
    3.  User password for the connection (default not specified, optional)
    4.  Database number for the connection (default not specified, optional)
    5.  Connection protocol, can be `RESP2` or `RESP3` (default: `RESP3`)
    6.  Socket connection timeout (default: `10s`)
    7.  Command execution timeout (default: `60s`)
    8.  Create a cluster client even with a single connection `URI` (default: `false`)
    9.  Cipher algorithms for a secure connection between client and server (default: `[]`)
    10. Timeout for establishing a secure connection with the server (default: `10s`)
    11. Enables module logging (default: `false`)
    12. Enables module metrics (default: `true`)
    13. [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) configuration for metrics (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    14. Tags configuration for metrics (default: `{}`)
    15. Enables module tracing (default: `true`)
    16. Attributes configuration for tracing (default: `{}`)
 
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

    1.  `URI` for connecting to `Redis` (`required`, default not specified).
        Single-server connection: `redis://localhost:6379`.
        Multi-server connection: `redis://localhost:6379,localhost:6380`.
        Connection with `SSL`: `rediss://localhost:6380`.
        Connection with `TLS`: `redis+tls://localhost:6380`.
    2.  Username for the connection (default not specified, optional)
    3.  User password for the connection (default not specified, optional)
    4.  Database number for the connection (default not specified, optional)
    5.  Connection protocol, can be `RESP2` or `RESP3` (default: `RESP3`)
    6.  Socket connection timeout (default: `10s`)
    7.  Command execution timeout (default: `60s`)
    8.  Create a cluster client even with a single connection `URI` (default: `false`)
    9.  Cipher algorithms for a secure connection between client and server (default: `[]`)
    10. Timeout for establishing a secure connection with the server (default: `10s`)
    11. Enables module logging (default: `false`)
    12. Enables module metrics (default: `true`)
    13. [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) configuration for metrics (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    14. Tags configuration for metrics (default: `{}`)
    15. Enables module tracing (default: `true`)
    16. Attributes configuration for tracing (default: `{}`)

The `Redis` cache configuration defines behavior for a specific cache.

Example of a complete configuration for a cache at `mycache.config`; parameters are described in the `RedisCacheConfig` class (example values are shown):

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

    1.  Sets the value [expiration](https://redis.io/commands/psetex/) time on write (default not specified, optional)
    2.  Sets the value [expiration](https://redis.io/commands/getex/) time on read (default not specified, optional)
    3.  Key prefix for the specific cache, used to avoid key collisions in one `Redis` database; can be an empty string, then keys will have no prefix (`required`, default not specified)

=== ":simple-yaml: `YAML`"

    ```yaml
    mycache:
      config:
        expireAfterWrite: "10s" #(1)!
        expireAfterAccess: "10s" #(2)!
        keyPrefix: "mykey" #(3)!
    ```

    1.  Sets the value [expiration](https://redis.io/commands/psetex/) time on write (default not specified, optional)
    2.  Sets the value [expiration](https://redis.io/commands/getex/) time on read (default not specified, optional)
    3.  Key prefix for the specific cache, used to avoid key collisions in one `Redis` database; can be an empty string, then keys will have no prefix (`required`, default not specified)

Module metrics are described in the [Metrics Reference](metrics.md#cache) section.

### Key and Value Mappers { #redis-mappers }

`Redis` stores keys and values as byte arrays, so `RedisCache` uses two kinds of mappers:

- `RedisCacheKeyMapper<K>` turns a cache key into `byte[]`.
- `RedisCacheValueMapper<V>` writes a cache value to `byte[]` and reads it back.

Regular keys are built through `RedisCacheKeyMapper` for the key type. Built-in mappers are available for `String`, `byte[]`,
numbers, `BigInteger`, `BigDecimal`, `UUID`, `Boolean`, `Character`, `Instant`, `LocalDateTime`, `LocalDate`, `ZonedDateTime`,
`Duration`, `Period`, `Enum`, and `Collection<T>` when a mapper for `T` is also available.
For `Enum`, `toString()` is used, so it can be overridden when another key format is needed.

For values, built-in `RedisCacheValueMapper` implementations are available for the same simple types, date/time types, `Enum`, and `byte[]`.
For other types, a mapper based on `JsonWriter<V>` and `JsonReader<V>` is used when JSON serialization is available for the type.
If another representation is needed, register your own `RedisCacheValueMapper<V>` or `RedisCacheKeyMapper<K>` component.

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

For a composite key based on a `record` or `data class`, Kora generates a separate `RedisCacheKeyMapper` for the whole key.
It receives a mapper for each field, converts every field to `byte[]`, and joins the parts with `RedisCacheKeyMapper.DELIMITER`.
The part order matches the order of `record` components or `data class` properties.

For a single key, built-in `RedisCacheKeyMapper` implementations can encode `null` as a special byte value.
In a composite key, each field mapping result must be non-`null`: if a custom `RedisCacheKeyMapper` for a field returns `null`,
key creation fails. For optional fields in a composite key, a custom mapper must explicitly encode `null`
as a stable byte value.

#### Configurator { #configurator }

You can register `LettuceConfigurator` to customize the `Lettuce` client before it is created.

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

## Usage { #usage }

Creating a cache will require registering a typed `@Cache` contract.
The contract interface must extend one of the `Kora` implementations: `CaffeineCache` or `RedisCache`.
For such an `@Cache`, an implementation is generated and added to the graph, so it can be injected as a dependency.

The `value` argument in `@Cache` defines the full path to the configuration of the specific cache.

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
The same rule applies to asynchronous wrappers, for example `CompletionStage<Optional<T>>` and `Mono<Optional<T>>`.
The cache value type itself can be either `T` or `Optional<T>`:

- `CaffeineCache<String, String>` and method `Optional<String> get(String key)`;
- `CaffeineCache<String, Optional<String>>` and method `String get(String key)`;
- `CaffeineCache<String, Optional<String>>` and method `Optional<String> get(String key)`.

For `@Cacheable`, this makes it possible to distinguish a missing cache entry from a method result that also means no data.
For `@CachePut`, the `Optional<T>` result is handled according to the cache value type: if the cache stores `Optional<T>`, the `Optional` itself is stored,
and if the cache stores `T`, only a present value is stored.

### Imperative { #imperative }

Caches are available for injection as dependencies on the interface and can be used in conjunction with declarative operations.

`CaffeineCache` provides the `Cache` contract for synchronous operations and the additional `getAll()` method.
`RedisCache` provides `Cache` and `AsyncCache`: it can be used synchronously and asynchronously through `CompletionStage`.

`Cache` provides `get(...)`, `put(...)`, `computeIfAbsent(...)`, `invalidate(...)`, `invalidateAll(...)`,
as well as batch variants for a collection of keys or a map of values. `AsyncCache` provides the same operations with the `Async` suffix.
`computeIfAbsent(...)` methods first try to get a value from the cache; on a miss, they call the provided loader function and store the result.

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

For an asynchronous facade, use `AsyncCache.builder(...)`; only `AsyncCache` instances can be added to it.
This is suitable, for example, for several `RedisCache` instances or other asynchronous implementations with the same key and value types.

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

The facade built through `Cache.Builder` does not support direct `get(Collection<K>)`, and the facade built through `AsyncCache.Builder` does not support direct `getAsync(Collection<K>)`.
For batch loading, use `computeIfAbsent(Collection<K>, ...)` or `computeIfAbsentAsync(Collection<K>, ...)`.

### Declarative { #declarative }

All aspect examples below assume the cache implementation above.

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
    class SomeService {

        @Cacheable(MyCache::class)
        fun get(arg1: String): String {
            // do something
        }
    }
    ```

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
    class SomeService {

        @CachePut(MyCache::class)
        fun put(arg1: String): String {
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
    class SomeService {

        @CacheInvalidate(MyCache::class)
        fun evict(arg1: String) {
            // do something
        }
    }
    ```

#### Invalidate all { #invalidate-all }

To remove all values from the cache via the `evictAll()` method, annotate it with `@CacheInvalidate`
and specify the `invalidateAll = true` parameter.

The method with `@CacheInvalidate` is called, and then all values are removed from the cache defined in `value`.

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

#### Composite cache { #composite-cache }

If several caches need to be used, connect the required modules and specify several annotations on the method.
For example, this can combine a fast local layer on `Caffeine` and a shared layer on `Redis`.

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
    class SomeService {

        @Cacheable(MyCaffeineCache::class)
        @Cacheable(MyRedisCache::class)
        fun get(arg1: String): String {
            // do something
        }
    }
    ```

The call order follows the order of annotations on the method from top to bottom.
For `@Cacheable`, this means the upper cache is checked first; on a miss, the next cache is checked,
and after the value is loaded, the result is stored back into the checked caches.
The same composition model works for repeatable `@CachePut` and `@CacheInvalidate`: the method is called once,
and then the result is written to all listed caches or invalidation is executed in all listed caches.
The container annotations `@Cacheables`, `@CachePuts`, and `@CacheInvalidates` can also be used when that form is more convenient.

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

Such a mapper can be provided manually with `@Mapping`.
Example of converting a complex object into a simple cache key:

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

If `RedisCache` is used, a `RedisCacheKeyMapper` is generated for the composite key.
It uses a mapper for each key field and expects the mapping result for every field to be non-`null`.
Built-in mappers can encode `null` with a special value, while custom mappers must do this explicitly.

### Argument ordering { #argument-ordering }

If the method accepts arguments that should be excluded from the composite key, or the argument order does not match
the order of the composite-key constructor arguments, use the `parameters` attribute and specify
which method arguments to use and in what order.

`parameters` defines the full set of method arguments used to build the key. Each name must match a method argument name,
and the order must match the key type: for a single argument, the `Cache<K, V>` key type; for a composite key,
the constructor argument order of the `record` or `data class`.
If a name is missing, a type does not match, or the order does not fit the key, application generation fails.

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

The library provides the `LoadableCache` component, which combines `get` and `put` operations without using aspects.
It is useful when value loading must be controlled manually while keeping the standard logic: first check the cache,
and on a miss load the data and store it.

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

For an asynchronous cache, use `AsyncLoadableCache`. It is created through `asLoadableAsyncSimple(...)`
for loading one key or through `asLoadableAsync(...)` for batch loading several keys.
Both variants return `CompletionStage` and are suitable for `RedisCache`, because it implements `AsyncCache`.

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

## Signatures { #signatures }

Available signatures for methods supported by annotations:

===! ":fontawesome-brands-java: `Java`"

    The class must not be `final` for aspects to work.

    The `T` refers to the type of the return value.

    - `T myMethod()`
    - `Optional<T> myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletionStage.html)
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (requires [dependency](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

    `@Cacheable` and `@CachePut` require a return value and cannot be applied to `void`, `Mono<Void>`, `CompletionStage<Void>`, `Flux<T>`, or `Publisher<T>`.
    `@CacheInvalidate` can be applied to methods without a result, but cannot be applied to `Flux<T>` or `Publisher<T>`.

=== ":simple-kotlin: `Kotlin`"

    The class must be `open` for aspects to work.

    By `T` we mean the type of the return value, either `T?`, or `Unit`.

    - `myMethod(): T`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (requires [dependency](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) as `implementation`)

    `@Cacheable` and `@CachePut` require a return value and cannot be applied to `Unit`.
    `@CacheInvalidate` can be applied to methods without a result.
