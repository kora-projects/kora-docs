Module for creating caches based on [Caffeine](https://github.com/ben-manes/caffeine) or [Redis](https://redis.io/docs/about/)
using both declarative-style annotations and using their imperative style.

## Caffeine

Library-based implementation of [Caffeine](https://github.com/ben-manes/caffeine) for in-memory caches within the application.

### Dependency

===! ":fontawesome-brands-java: `Java`"

    Dependency ``build.gradle``:
    ```groovy
    implementation "ru.tinkoff.kora:cache-caffeine"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends CaffeineCacheModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Dependency ``build.gradle.kts``:
    ```groovy
    implementation("ru.tinkoff.kora:cache-caffeine")
    ```

    Module:
    ````kotlin
    @KoraApp
    interface Application : CaffeineCacheModule
    ```

### Configuration

Example of complete configuration for `mycache.config` cache, parameters are described in the `CaffeineCacheConfig` class (default or example values are specified):

===! ":material-code-json: `Hocon`"

    ```javascript
    mycache {
        config {
            expireAfterWrite = "10s" //(1)!
            expireAfterAccess = "10s" //(2)!
            initialSize = 10 //(3)!
            maximumSize = 10 //(4)!
        }
    }
    ```

    1. Time after which the value for the key will be deleted is reported after the value is added (optional)
    2. Time after which the value for the key will be deleted, counted after a read operation (optional)
    3. Initial cache size (helps to avoid cache expansion in case of active swelling) (optional)
    4. Maximum cache size (When the boundary is reached **or slightly earlier** will exclude the least relevant values from the cache) (default is `100000`)

=== ":simple-yaml: ``YAML``"

    ```yaml
    mycache:
      config:
        expireAfterWrite: "10s" #(1)!
        expireAfterAccess: "10s" #(2)!
        initialSize: 10 #(3)!
        maximumSize: 10 #(4)!
    ```

    1. Time after which the value for the key will be expired is reported after the value is added (optional)
    2. Time after which the value for the key will be deleted is counted after a read operation (optional)
    3. Initial cache size (helps to avoid cache expansion in case of active swelling) (optional)
    4. Maximum cache size (When the boundary is reached **or slightly earlier** will exclude the least relevant values from the cache) (default is `100000`)

## Redis

Implementation based on in-memory database [Redis](https://redis.io/docs/about/) and connection driver [Lettuce](https://github.com/lettuce-io/lettuce-core).

### Dependency

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

    Dependency ``build.gradle.kts``:
    ```groovy
    implementation("ru.tinkoff.kora:cache-redis")
    ```

    Module:
    ````kotlin
    @KoraApp
    interface Application : RedisCacheModule
    ```

### Configuration

It is required to separately configure the Lettuce driver to connect to Redis.
A single connection is used for all caches.

Example of a complete configuration for *lettuce* driver, parameters are described in the `LettuceConfig` class (default or example values are specified):

===! ":material-code-json: `Hocon`"

    ```javascript
    lettuce {
        uri = "redis://locahost:6379" //(1)!
        user = "admin" //(2)!
        password = "12345" //(3)!
        database = 1 //(4)!
        protocol = "REP3" //(5)!
        socketTimeout = "15s" //(6)!
        commandTimeout = "15s" //(7)!
        ssl {
            ciphers = [ "TLS_CHACHA20_POLY1305_SHA256" ] //(8)!
            handshakeTimeout = "10s" //(9)!
        } 
    }
    ```

    1. URI to connect to Redis (**required**)
       Connection for 1 server: `redis://locahost:6379`, 
       Connection for N servers: `redis://locahost:6379,locahost:6380`, 
       Connection with SSL: `rediss://locahost:6380`
       Connection with TLS: `redis+tls://locahost:6380`
    2. Username for connection (optional)
    3. Password for connection (optional)
    4. Database number for connection (optional)
    5. Protocol for connection
    6. Connection timeout
    7. Command execution timeout
    8. Ciphers algorithms to use for secure connections between client and server (optional)
    9. Timeout for establishing a secure connection between client and server (optional)
 
=== ":simple-yaml: `YAML`"

    ```yaml
    lettuce:
      uri: "redis://locahost:6379" #(1)!
      user: "admin" #(2)!
      password: "12345" #(3)!
      database: 1 #(4)!
      protocol: "REP3" #(5)!
      socketTimeout: "15s" #(6)!
      commandTimeout: "15s" #(7)!
      ssl:
        ciphers:
          - "TLS_CHACHA20_POLY1305_SHA256" #(8)!
        handshakeTimeout: "10s" #(9)!
    ```

    1. URI to connect to Redis (**required**)
       Connection for 1 server: `redis://locahost:6379`, 
       Connection for N servers: `redis://locahost:6379,locahost:6380`, 
       Connection with SSL: `rediss://locahost:6380`
       Connection with TLS: `redis+tls://locahost:6380`
    2. Username for connection (optional)
    3. Password for connection (optional)
    4. Database number for connection (optional)
    5. Protocol for connection
    6. Connection timeout
    7. Command execution timeout
    8. Ciphers algorithms to use for secure connections between client and server (optional)
    9. Timeout for establishing a secure connection between client and server (optional)

Redis cache configurations configure the behavior of a particular cache.

Example of a complete configuration for `mycache.config` cache, parameters are described in the `RedisCacheConfig` class (example values are specified):

===! ":material-code-json: `Hocon`"

    ```javascript
    mycache {
        config {    
            expireAfterWrite = "10s" //(1)!
            expireAfterAccess = "10s" //(2)!
            keyPrefix = "mykey" //(3)!
        }
    }
    ```

    1.  When writing, sets the [expiration](https://redis.io/commands/psetex/) time (optional)
    2.  When reading, sets the time [expiration](https://redis.io/commands/getex/) (optional)
    3.  Prefix a key in a particular cache to avoid key collisions within a Redis database, can be an empty string then keys will be without prefixes (**required**)

=== ":simple-yaml: ``YAML`"

    ```yaml
    mycache:
      config:
        expireAfterWrite: "10s" #(1)!
        expireAfterAccess: "10s" #(2)!
        keyPrefix: "mykey" //(3)!
    ```

    1.  Sets the [expiration](https://redis.io/commands/psetex/) time when writing (optional)
    2.  When reading, sets the time [expiration](https://redis.io/commands/getex/) (optional)
    3.  Prefix a key in a specific cache to avoid key collisions within a Redis database, can be an empty string then keys will be without prefixes (**required**)

## Usage

Creating a cache will require registering a typed `@Cache` contract.
The contract interface should only be inherited from Kora's provided implementations: `CaffeineCache` / `RedisCache`.
For such `@Cache` an implementation will be created and added to the graph, it can be used to enforce dependencies.

To register `@Cache` and specify the config, it is required to annotate with the `@Cache` annotation where the `value` argument means the full path to the config.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Cache("mycache.config")
    public interface MyCache extends CaffeineCache<String, String> { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ````kotlin
    @Cache("mycache.config")
    interface MyCache : CaffeineCache<String, String>
    ```

### Imperative

Caches are available for injection as dependencies on the interface and can be used in conjunction with declarative operations.

The `CaffeineCache` implementation provides basic `Cache` interface contracts for synchronous operations,
and `RedisCache` provides both `Cache` and `AsyncCache` for asynchronous operations with `CompletionStage` signatures.

The interfaces provide get, delete, update, batch, etc. operations.
Cache implementations can also provide self-specific contracts.

### Declarative

All aspect use cases will assume the cache implementation above.

#### Get

To cache and retrieve a value from the cache for the *get()* method, annotate it with the `@Cacheable` annotation.

The key for the cache is compiled from the method arguments, the order of the arguments matters, in this case it will be compiled from the value `arg1`.

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

#### Put

To add values to the cache via the *put()* method, annotate it with the `@CachePut` annotation.
The method annotated with `@CachePut` will be called and its value put into the cache defined in *value*.

The key for the cache is compiled from the method arguments, the order of the arguments matters, in this case it will be compiled from the value `arg1`.

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

#### Invalidate

To remove a keyed value from the cache via the *evict()* method, annotate it with the `@CacheInvalidate` annotation.
The method annotated with `@CacheInvalidate` will be called and then the keyed values for the cache defined in *value* will be deleted by key.

The key for the cache is compiled from the method arguments, the order of the arguments matters, in this case it will be compiled from the value `arg1`.

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

#### Invalidate all

To remove all values from the cache via the *evictAll()* method, annotate it with the `@CacheInvalidate` annotation and specify the *invalidateAll = true* parameter.

The method annotated with `@CacheInvalidate` will be called and then all of the cache values defined in *value* will be removed.

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

#### Composite cache

In case you have multiple caches, you need to connect both modules and specify the appropriate number of annotations over the method.

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

And the annotated class itself is like this:

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

The order of aspect calls corresponds to the order of annotations above the method, top to bottom.

## Key

In case the cache key represents 1 argument, it is required to register `Cache` with a signature corresponding to the key and value types.

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

### Conversion

In case an argument cannot be converted to a cache key, the cache implementation will require an appropriate converter
with the `CacheKeyMapper` interface, in case there are 2 arguments for the key then `CacheKeyMapper2` will be required, and so on.

Such a converter can also be provided manually using the `@Mapping` annotation,
example of converting a complex object into a simple cache key:

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

        @Cacheable(MyCache::class)
        fun get(arg1: String, arg2: BigDecimal): String {
            // do something
        }
    }
    ```

### Composite key

In case the cache key represents N arguments, it is required to register `Cache` using an
class to describe such a key.

Example for `Cache` where the composite key consists of 2 elements:

===! ":fontawesome-brands-java: `Java`"

    It is supposed to create its own `record` class that would describe the composite key.

    ```java
    @Cache("mycache.config")
    public interface MyCache extends CaffeineCache<MyCache.Key, String> {
        
        record Key(String k1, Long k2) { }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    It is supposed to create its own `data` class that would describe the composite key.

    ```kotlin
    @Cache("mycache.config")
    interface MyCache : CaffeineCache<MyCache.Key, String> {

        data class Key(val k1: String, val k2: Long)
    }
    ```

If `RedisCache` is used, it is assumed that all composite key arguments will default to non `null`,
or a custom key resolver will need to be used.

### Argument ordering

If the method accepts arguments that you want to exclude from the composite key,
or the order of the arguments does not match the order of the arguments of the composite key constructor,
you should use the `parameters` annotation attribute and define which method arguments to use and in what order.

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

## Loadable Cache

The library provides a component for building an entity that combines GET and PUT operations without using aspects - `LoadableCache`

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Cache("mycache.config")
    public interface MyCache extends CaffeineCache<String, String> { }

    @KoraApp
    public interface Application : CaffeineCacheModule {

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

## Signatures

Available signatures for repository methods out of the box:

===! ":fontawesome-brands-java: `Java`"

    Class must be non `final` in order for aspects to work.

    The `T` refers to the type of the return value.

    - `T myMethod()`
    - `@Nullable T myMethod()`
    - `Optional<T> myMethod()`
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (require [dependency](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

=== ":simple-kotlin: `Kotlin`"

    Class must be `open` in order for aspects to work.

    By `T` we mean the type of the return value, either `T?`, or `Unit`.

    - `myMethod(): T`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (require [dependency](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) as `implementation`)
