---
search:
  exclude: true
title: Multi-Level Caching with Redis
summary: Learn how to extend the Caffeine cache guide with Redis as a shared second-level cache for Kora applications
tags: caching, redis, caffeine, multi-level, distributed, performance
---

# Multi-Level Caching with Redis { #multi-level-caching-redis }

This guide introduces multi-level caching with Kora, Caffeine, and Redis. It covers how a fast local L1 cache and a shared Redis L2 cache work together, how Kora composes cache implementations behind
one cache contract, and how service-level cache annotations keep reads and invalidation consistent. You will also see why Redis is treated as shared cache infrastructure rather than the source of
truth.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java Cache Multi Level App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-cache-multi-level-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin Cache Multi Level App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-cache-multi-level-app).

## What You'll Build { #youll-build }

In this guide, you'll turn the single-level cache from the previous guide into a two-level cache where:

- `UserCaffeineCache` remains the fast local L1 cache
- `UserRedisCache` becomes the shared L2 cache
- `getUser()` checks Caffeine first, then Redis, then the repository
- `createUser()` warms both cache levels immediately
- `updateUser()` refreshes both cache levels
- `deleteUser()` evicts stale data from both cache levels
- the `/users` HTTP API stays unchanged while cache behavior becomes multi-instance friendly

## What You'll Need { #youll-need }

- JDK 17 or later
- Gradle 7+
- A text editor or IDE
- Docker or another local Redis runtime
- Completed [Caching Strategies with Kora](cache.md)

## Prerequisites { #prerequisites }

!!! note "Required: Complete the Cache Guide"

    This guide assumes you have completed **[Caching Strategies with Kora](cache.md)** and already have the same `Application`, `UserController`, `UserService`, DTOs, and `UserCaffeineCache` contract from that guide.

    If you haven't completed the cache guide yet, do that first, because this guide keeps the same `/users` API and adds Redis as a second cache layer.

## Overview { #overview }

The previous guide used a **local in-memory cache** only. That works well when the application runs in one JVM, because every repeated read can be served from local memory.

But once an application runs in several pods or several instances, a local cache alone stops being enough for some workloads:

- each pod has its own cache contents
- a value warmed in pod A is not automatically visible in pod B
- an update handled by pod A does not refresh pod B's local memory
- after a restart, a pod starts with an empty local cache again

That is why a common next step is **multi-level caching**.

In this guide we use two layers:

1. **L1: Caffeine**
   This is the same local in-memory cache from the previous guide. It is the fastest layer and is ideal for hot repeated reads inside one process.
2. **L2: Redis**
   This is a shared distributed cache. It is slower than local memory, but still much faster than going back to the primary source every time.

A typical read flow now becomes:

1. Try Caffeine first.
2. If Caffeine misses, try Redis.
3. If Redis also misses, load from the repository.
4. Store the value back into cache so later reads are cheaper.

This layered model is useful because it balances speed and sharing:

- Caffeine gives the lowest latency for hot values inside one pod.
- Redis lets different pods reuse the same cached value.
- The repository remains the source of truth when both caches miss.

### Redis as an L2 Cache { #redis-l2 }

Redis is a popular second-level cache because it provides:

- in-memory access with low latency
- shared state across instances
- key expiration and key prefixing
- mature operational tooling
- simple deployment for local development and production

In this guide Redis is not treated as the source of truth. It is still a cache. The repository remains authoritative, and Redis just helps different application instances avoid repeating the same
lookups.

### Kora Cache Model { #cache-model }

The full composite cache model is described in [Composite cache](../documentation/cache.md#composite-cache), and the Redis layer is covered in [Redis](../documentation/cache.md#redis).

Kora's cache support works well for layered caches because cache contracts are typed and cache annotations are composable.

That means you can define two separate cache interfaces:

- `UserCaffeineCache extends CaffeineCache<String, UserResponse>`
- `UserRedisCache extends RedisCache<String, @Json UserResponse>`

Then you can place multiple annotations on the same service method:

- `@Cacheable(UserCaffeineCache.class)`
- `@Cacheable(UserRedisCache.class)`

Kora applies them in declaration order, top to bottom. So in practice:

- L1 Caffeine is checked first
- then L2 Redis
- then the original method runs if both miss

The same idea applies to `@CachePut` and `@CacheInvalidate`.

## Dependencies { #dependencies }

Add Redis caching to the existing cache guide application.

===! ":fontawesome-brands-java: `Gradle Groovy`"

    Update `guides/guide-cache-multi-level-app/build.gradle`:

    ```groovy
    dependencies {
        implementation "ru.tinkoff.kora:cache-redis"
    }
    ```

=== ":simple-kotlin: `Gradle Kotlin DSL`"

    Update `build.gradle.kts`:

    ```kotlin
    dependencies {
        implementation("ru.tinkoff.kora:cache-redis")
    }
    ```

## Modules { #modules }

The base cache guide already includes `CaffeineCacheModule`. For a multi-level cache, the application graph also needs `RedisCacheModule`.

===! ":fontawesome-brands-java: `Java`"

    Update `guides/guide-cache-multi-level-app/src/main/java/ru/tinkoff/kora/guide/cache/Application.java`:

    ```java
    package ru.tinkoff.kora.guide.cache;

    import ru.tinkoff.kora.application.graph.KoraApplication;
    import ru.tinkoff.kora.cache.caffeine.CaffeineCacheModule;
    import ru.tinkoff.kora.cache.redis.RedisCacheModule;
    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.config.hocon.HoconConfigModule;
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule;
    import ru.tinkoff.kora.json.module.JsonModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            UndertowHttpServerModule,
            CaffeineCacheModule,  // <----- Connected module
            RedisCacheModule {  // <----- Connected module

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update `src/main/kotlin/ru/tinkoff/kora/guide/cache/Application.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.cache

    import ru.tinkoff.kora.application.graph.KoraApplication
    import ru.tinkoff.kora.cache.caffeine.CaffeineCacheModule
    import ru.tinkoff.kora.cache.redis.RedisCacheModule
    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.config.hocon.HoconConfigModule
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule
    import ru.tinkoff.kora.json.module.JsonModule
    import ru.tinkoff.kora.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        UndertowHttpServerModule,
        CaffeineCacheModule,  // <----- Connected module
        RedisCacheModule  // <----- Connected module

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

## Multi-Level Cache Contract { #cache-contract }

For more on Redis caches, value serialization, and typed cache contracts, see the [Redis cache documentation](../documentation/cache.md#redis).

The previous guide already defined `UserCaffeineCache`. Now we add a second contract for Redis.

This contract is important for two reasons:

- annotations can refer to it declaratively
- the same cache can be injected directly when manual control is needed

A Caffeine cache stores Java objects directly in local memory, so it can keep `UserResponse` as-is. Redis is different: values must be serialized before they can be written to Redis and deserialized
when they are read back.

For this pattern to work cleanly with Kora:

- keep `@Json` on the DTO so Kora knows how to serialize and deserialize the payload
- mark the Redis cache value type as `@Json UserResponse` so the cache contract explicitly says which serialized type Redis stores

`@Json` here also tells Kora that the value should use a serializer and deserializer qualified with the `@Json` tag. For Redis caches, the Redis module provides that tagged mapper out of the box, so
this works without any extra manual wiring.

The same idea is flexible: if you want, you can use a different tag for either the key or the value type, as long as a matching mapper with that tag exists in the graph.

That makes the contract self-describing and lets Kora resolve the correct mapper automatically instead of requiring a separate manual Redis value mapper.

In the working application, Redis stores `UserResponse`, so the contract uses `String` as the key and `@Json UserResponse` as the value type.

===! ":fontawesome-brands-java: `Java`"

    Create `guides/guide-cache-multi-level-app/src/main/java/ru/tinkoff/kora/guide/cache/service/UserRedisCache.java`:

    ```java
    package ru.tinkoff.kora.guide.cache.service;

    import ru.tinkoff.kora.cache.annotation.Cache;
    import ru.tinkoff.kora.cache.redis.RedisCache;
    import ru.tinkoff.kora.guide.cache.dto.UserResponse;
    import ru.tinkoff.kora.json.common.annotation.Json;

    @Cache("cache.redis.users")
    public interface UserRedisCache extends RedisCache<String, @Json UserResponse> {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/guide/cache/service/UserRedisCache.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.cache.service

    import ru.tinkoff.kora.cache.annotation.Cache
    import ru.tinkoff.kora.cache.redis.RedisCache
    import ru.tinkoff.kora.guide.cache.dto.UserResponse
    import ru.tinkoff.kora.json.common.annotation.Json

    @Cache("cache.redis.users")
    interface UserRedisCache : RedisCache<String, @Json UserResponse>
    ```

## Multi-Level Cache Implementation { #cache-impl }

The service continues the one from the cache guide. The unchanged parts still behave the same:

- `getUsers()` still applies sorting and pagination
- the comparator helper stays the same
- HTTP-facing `404` behavior still lives in the service

Here we only show the methods that change for multi-level caching:

- `getUser()` - `@Cacheable` is declared twice so Kora checks Caffeine first and Redis second.
- `updateUser()` - `@CachePut` is declared twice so both layers are refreshed after a successful update.
- `deleteUser()` - `@CacheInvalidate` is declared twice so both layers evict the stale value.

===! ":fontawesome-brands-java: `Java`"

    Update the changed methods in `guides/guide-cache-multi-level-app/src/main/java/ru/tinkoff/kora/guide/cache/service/UserService.java`:

    ```java
    @Cacheable(UserCaffeineCache.class)
    @Cacheable(UserRedisCache.class)
    public Optional<UserResponse> getUser(String id) {
        return userRepository.findById(id);
    }

    @CachePut(value = UserCaffeineCache.class, parameters = { "id" })
    @CachePut(value = UserRedisCache.class, parameters = { "id" })
    public UserResponse updateUser(String id, UserRequest request) {
        boolean updated = userRepository.update(id, request.name(), request.email());
        if (!updated) {
            throw HttpServerResponseException.of(404, "User not found");
        }
        return new UserResponse(id, request.name(), request.email(), LocalDateTime.now());
    }

    @CacheInvalidate(UserCaffeineCache.class)
    @CacheInvalidate(UserRedisCache.class)
    public void deleteUser(String id) {
        boolean deleted = userRepository.deleteById(id);
        if (!deleted) {
            throw HttpServerResponseException.of(404, "User not found");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update the changed methods in `src/main/kotlin/ru/tinkoff/kora/guide/cache/service/UserService.kt`:

    ```kotlin
    @Cacheable(UserCaffeineCache::class)
    @Cacheable(UserRedisCache::class)
    open fun getUser(id: String): UserResponse? {
        return userRepository.findById(id).orElse(null)
    }

    @CachePut(value = UserCaffeineCache::class, parameters = ["id"])
    @CachePut(value = UserRedisCache::class, parameters = ["id"])
    open fun updateUser(id: String, request: UserRequest): UserResponse {
        val updated = userRepository.update(id, request.name, request.email)
        if (!updated) {
            throw HttpServerResponseException.of(404, "User not found")
        }
        return UserResponse(id, request.name, request.email, LocalDateTime.now())
    }

    @CacheInvalidate(UserCaffeineCache::class)
    @CacheInvalidate(UserRedisCache::class)
    open fun deleteUser(id: String) {
        val deleted = userRepository.deleteById(id)
        if (!deleted) {
            throw HttpServerResponseException.of(404, "User not found")
        }
    }
    ```

In an N-pod environment this changes the behavior significantly compared to local-only caching:

- a miss in one pod can still become a hit in Redis
- repeated reads in the same pod still benefit from local Caffeine speed
- updates and deletes now refresh or evict a shared cache level instead of only one pod's memory

## Cache Warm-Up { #cache-warmup }

`createUser()` still needs manual cache management because the user id is generated by the repository first.

This is one of the clearest examples of why typed cache contracts are useful: the same caches used by annotations can also be injected and controlled directly.

===! ":fontawesome-brands-java: `Java`"

    Update the create path in `guides/guide-cache-multi-level-app/src/main/java/ru/tinkoff/kora/guide/cache/service/UserService.java`:

    ```java
    public UserResponse createUser(UserRequest request) {
        var generatedId = userRepository.save(request.name(), request.email());
        var createdUser = new UserResponse(generatedId, request.name(), request.email(), LocalDateTime.now());
        this.userCaffeineCache.put(createdUser.id(), createdUser);
        this.userRedisCache.put(createdUser.id(), createdUser);
        return createdUser;
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update the create path in `src/main/kotlin/ru/tinkoff/kora/guide/cache/service/UserService.kt`:

    ```kotlin
    fun createUser(request: UserRequest): UserResponse {
        val generatedId = userRepository.save(request.name, request.email)
        val createdUser = UserResponse(generatedId, request.name, request.email, LocalDateTime.now())
        userCaffeineCache.put(createdUser.id, createdUser)
        userRedisCache.put(createdUser.id, createdUser)
        return createdUser
    }
    ```

This way the next read can be served from cache immediately, and Redis already contains the new entity for other instances too.

## Configuration { #config }

Keep the HTTP server setup from the previous guide as-is. In this guide, update only the cache and Redis client configuration.

Update `guides/guide-cache-multi-level-app/src/main/resources/application.conf`:

For the full configuration reference, see [Cache](../documentation/cache.md).

===! ":material-code-json: `Hocon`"

    ```javascript
    cache.caffeine.users {
      maximumSize = 1000 //(1)!
      expireAfterWrite = "10m" //(2)!
    }

    cache.redis.users {
      keyPrefix = "users-" //(3)!
      expireAfterWrite = "30m" //(4)!
    }

    lettuce {
      uri = "redis://localhost:6379" //(5)!
      uri = ${?REDIS_URL} //(6)!
      user = ${?REDIS_USER} //(7)!
      password = ${?REDIS_PASS} //(8)!
      socketTimeout = 15s //(9)!
      commandTimeout = 15s //(10)!
    }
    ```

    1. Maximum number of cache entries before eviction starts.
    2. Time after which a Caffeine entry expires after being written.
    3. Prefix added to keys stored in Redis.
    4. Time after which a Redis entry expires after being written.
    5. Default local Redis connection URI.
    6. Connection URI. Optional override from `REDIS_URL`.
    7. User name used by the client connection. Optional override from `REDIS_USER`.
    8. Database user password. Optional override from `REDIS_PASS`.
    9. Socket operation timeout.
    10. Redis command execution timeout.

=== ":simple-yaml: `YAML`"

    ```yaml
    cache:
      caffeine:
        users:
          maximumSize: 1000 #(1)!
          expireAfterWrite: "10m" #(2)!
      redis:
        users:
          keyPrefix: "users-" #(3)!
          expireAfterWrite: "30m" #(4)!
    lettuce:
      uri: ${?REDIS_URL:"redis://localhost:6379"} #(5)!
      user: ${?REDIS_USER} #(6)!
      password: ${?REDIS_PASS} #(7)!
      socketTimeout: 15s #(8)!
      commandTimeout: 15s #(9)!
    ```

    1. Maximum number of cache entries before eviction starts.
    2. Time after which a Caffeine entry expires after being written.
    3. Prefix added to keys stored in Redis.
    4. Time after which a Redis entry expires after being written.
    5. Connection URI with a local default and optional `REDIS_URL` override.
    6. User name used by the client connection. Optional override from `REDIS_USER`.
    7. Database user password. Optional override from `REDIS_PASS`.
    8. Socket operation timeout.
    9. Redis command execution timeout.

A few details matter here:

- `cache.caffeine.users` matches `UserCaffeineCache`
- `cache.redis.users` matches `UserRedisCache`
- `keyPrefix` avoids collisions inside Redis
- `REDIS_URL` allows tests or other environments to override the default local URI

## Docker Compose { #docker-compose }

For local guide runs, the simplest setup is a small Docker Compose file.

Create `docker-compose.yml` in the application module directory:

```yaml
services:
    redis:
        image: redis:8.2-alpine
        ports:
            - "6379:6379"
        command: redis-server --save 60 1 --appendonly yes
        healthcheck:
            test: [ "CMD", "redis-cli", "ping" ]
            interval: 10s
            timeout: 3s
            retries: 5
```

Start Redis:

```bash
docker compose up -d redis
```

Check that it is healthy:

```bash
docker compose ps
```

## Run Application { #run-app }

Use the standard guide flow:

```bash
./gradlew clean classes
./gradlew test
./gradlew run
```

The working companion module also validates multi-level behavior with focused Redis-backed component tests.

## Check Application { #check-app }

Create a user first:

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com"}'
```

Read the same user twice. The second request should be served from cache, and in a real multi-instance deployment Redis gives you a shared fallback when another instance misses its local Caffeine
cache.

```bash
curl http://localhost:8080/users/1
curl http://localhost:8080/users/1
```

Update the user. Both cache levels are refreshed:

```bash
curl -X PUT http://localhost:8080/users/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"John Updated","email":"john.updated@example.com"}'
```

Delete the user. Both cache levels are invalidated:

```bash
curl -X DELETE http://localhost:8080/users/1
```

If you want to stop local Redis afterwards:

```bash
docker compose down
```

## Best Practices { #best-practices }

- Keep Caffeine as the first cache layer for hot in-process reads.
- Use Redis as a shared cache layer, not as a replacement for the source of truth.
- Make cache contracts typed and explicit so they can be used both declaratively and imperatively.
- Put `@Json` on the Redis value type when caching custom DTOs.
- Keep cache update semantics close to business operations: refresh on update, evict on delete, warm explicitly on create.

## Summary { #summary }

You extended the single-level cache guide into a multi-level cache architecture.

The resulting application now uses:

- local `UserCaffeineCache` for ultra-fast repeated reads inside one instance
- shared `UserRedisCache` for cross-instance reuse
- layered `@Cacheable` reads
- layered `@CachePut` refreshes
- layered `@CacheInvalidate` evictions
- manual dual-cache warm-up in `createUser()`

## Key Concepts { #key-concepts }

- multi-level caching combines local latency benefits with shared distributed reuse
- Caffeine and Redis solve different problems and work well together
- Kora applies multiple cache annotations in declaration order
- Redis cache values for custom DTOs need explicit JSON-aware typing
- typed cache contracts can be injected directly for manual cache control

## Troubleshooting { #troubleshooting }

**Graph build fails for `RedisCacheValueMapper<...>`:**

If you cache a custom DTO in Redis, make sure the Redis cache contract uses `@Json` on the value type, for example:

```java
public interface UserRedisCache extends RedisCache<String, @Json UserResponse> {
}
```

Without that, Kora may fail to generate the Redis value mapper for your DTO.

**Redis connection fails at startup:**

Check that Redis is running and that `lettuce.uri` points to a reachable instance:

```bash
docker compose ps
docker compose logs redis
```

**Gradle hangs or fails unexpectedly:**

Stop Gradle daemons and retry:

```bash
./gradlew --stop
./gradlew clean classes
```

**Windows `AccessDeniedException` in Gradle cache:**

If Windows keeps file handles open in `.gradle` or `build/`, stop Gradle daemons, close IDE processes that still watch the directory, and rerun the command.

**Testcontainers-based Redis tests fail:**

Make sure Docker is running and accessible from the current shell. The companion app tests use Redis Testcontainers and inject `REDIS_URL` dynamically.

**Docker build or compose context issues:**

If `docker compose` cannot find the file or starts from the wrong place, run it from the application module directory where `docker-compose.yml` lives.

**Readiness checks fail in later observability steps:**

If you continue this app with observability, remember that the private management API uses port `8085`, and readiness is checked on `/system/readiness`.

## What's Next? { #whats-next }

- [Resilient Patterns](resilient.md) to protect calls before they populate local and distributed caches.
- [Observability](observability.md) to monitor cache hit behavior, Redis calls, latency, and failures.
- [Database JDBC](database-jdbc.md) if you want a persistence-backed app before end-to-end black-box testing.
- [Messaging with Kafka](messaging-kafka.md) when cached read models need to react to events.

## Help { #help }

If you run into trouble:

- compare with [Kora Java Cache Multi Level App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-cache-multi-level-app) and [Kora Kotlin Cache Multi Level App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-cache-multi-level-app)
- check the [Cache documentation](../documentation/cache.md)
- check the [Redis cache example](https://github.com/kora-projects/kora-examples/tree/master/kora-java-cache-redis)
- revisit [Caching Strategies](cache.md) for the single-level cache baseline
