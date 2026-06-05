---
search:
  exclude: true
title: Caching Strategies with Kora
summary: Learn how to extend the HTTP Server guide with typed Caffeine caching, cache annotations, and local performance optimization
tags: caching, performance, caffeine, cacheable, cache-invalidate, optimization
---

# Caching Strategies with Kora { #caching-strategies-kora }

This guide introduces local caching with Kora and Caffeine. It covers how cache interfaces describe stored values, how cache annotations wrap service methods, and how invalidation keeps reads aligned
with create, update, and delete operations. You will also see how a local in-memory cache improves repeated lookups while the repository remains the source of truth.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java Cache App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-cache-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin Cache App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-cache-app).

## What You'll Build { #youll-build }

In this guide, you'll turn the `UserService` from the HTTP Server guide into a cache-aware service that:

- warms the cache immediately after `createUser()`
- reuses cached values for repeated `getUser()` calls
- refreshes cached values on `updateUser()`
- evicts stale entries on `deleteUser()`
- keeps the same `/users` HTTP contract while making repeated reads cheaper

## What You'll Need { #youll-need }

- JDK 17 or later
- Gradle 7+
- A text editor or IDE
- Completed [HTTP Server](http-server.md)

## Prerequisites { #prerequisites }

!!! note "Required: Complete the HTTP Server Guide"

    This guide assumes you have completed **[HTTP Server](http-server.md)** and already have the same `UserController`, `UserService`, DTOs, and in-memory `UserRepository` flow from that guide.

    If you haven't completed the HTTP server guide yet, do that first, because this guide keeps the `/users` API contract and adds caching on top of the existing service layer.

## Overview { #overview }

If you have never worked with caches before, the main idea is simple: a cache keeps already computed or already loaded data in a faster storage layer so the application does not need to repeat the
same expensive work on every request.

Without caching, a typical read flow looks like this:

1. HTTP request arrives.
2. The service asks the repository or an external system for data.
3. The repository performs work again.
4. The service returns the result.

With caching, the flow becomes:

1. HTTP request arrives.
2. The service first checks whether the value is already cached.
3. If it is cached, the application returns it immediately.
4. If it is not cached, the application loads the data from the original source, returns it, and stores it in the cache for the next call.

This matters because the original source is often much slower or much more expensive than memory:

- a database call costs network, connection-pool, query, and mapping time
- an external HTTP call adds network latency and downstream risk
- a heavy computation spends CPU every time
- a repeated lookup under load amplifies all of the above

So the main reasons to use a cache are:

- reduce latency for repeated reads
- reduce pressure on databases and downstream services
- improve throughput under high traffic
- make hot paths more predictable

At the same time, caching is a trade-off, not free magic. Cached data can become stale, memory is finite, and cache invalidation must be designed carefully. That is why good caching starts from
understanding **what kind of data changes**, **how often it changes**, and **how harmful stale data would be**.

### When Caching Helps Most { #caching-helps-most }

Caching is most useful when all or most of these are true:

- the same keys are requested repeatedly
- the source of truth is noticeably slower than memory
- the data changes less frequently than it is read
- short-term staleness is acceptable, or invalidation is easy to model

Typical examples are:

- user profiles
- feature flags and reference data
- product metadata
- configuration snapshots
- expensive aggregate results

Caching is usually a poor fit when:

- values change almost every time they are read
- every request uses a unique key only once
- strict real-time consistency is required for every read
- the invalidation rules are unknown or extremely complex

### Local and Distributed Cache { #local-distributed-cache }

In this guide we use **Caffeine**, which is an **in-memory local cache**. That means the cache lives inside a single application process.

This has important consequences:

- it is extremely fast because it is just local memory
- it does not require extra infrastructure such as Redis
- it is isolated per process, so each pod or instance has its own cache contents

In an N-pod environment like Kubernetes, each pod warms and stores its cache independently.

That is often perfectly fine when:

- cache warm-up is cheap
- eventual consistency across pods is acceptable
- you mainly want to reduce repeated work inside each pod

But it also means:

- cache entries are not shared between pods
- one pod updating or evicting a value does not directly update another pod's local cache
- a restarted pod starts with an empty cache

So local Caffeine caches are best seen as **per-instance acceleration**, not as a globally shared source of truth.

If later you need cross-pod shared cache state, this guide naturally leads into a multi-level or distributed cache setup.

### Why Kora's Cache Model Is Useful { #koras-cache-model-useful }

Kora supports caching in two complementary styles:

- **Declarative caching** with `@Cacheable`, `@CachePut`, and `@CacheInvalidate`
- **Imperative caching** by injecting the cache contract and calling `get()`, `put()`, `invalidate()`, or `invalidateAll()` directly

That combination is powerful because different service methods need different control.

In this guide:

- `getUser()` is a classic declarative read-through case, so `@Cacheable` is ideal
- `updateUser()` is a natural refresh case, so `@CachePut` is a good fit
- `deleteUser()` is an obvious eviction case, so `@CacheInvalidate` works well
- `createUser()` needs manual cache warm-up because the cache key is known only after the repository generates the id

### Why the Cache Contract Is Typed { #cache-contract-typed }

Kora caches are not anonymous maps hidden somewhere in framework internals. You define a **typed cache contract** such as `CaffeineCache<String, UserResponse>`.

That gives several advantages:

- the key type is explicit
- the cached value type is explicit
- the compiler helps protect the contract
- the cache can be injected like any other component
- the same cache can be used both by annotations and by direct imperative calls

Because `UserCaffeineCache` extends `CaffeineCache<String, UserResponse>`, it behaves like a normal dependency you can inject into services and tests.

That means you can use the cache directly for operations such as:

- `get(key)` to inspect current cached value
- `put(key, value)` to warm or overwrite an entry manually
- `invalidate(key)` to evict one key
- `invalidateAll()` to clear the whole cache

This makes the cache both declarative-friendly and operationally explicit. You keep framework support, but you do not lose control.

## Dependencies { #dependencies }

Add the Caffeine runtime dependency to the application from the HTTP Server guide.

===! ":fontawesome-brands-java: `Gradle Groovy`"

    Update `guides/guide-cache-app/build.gradle`:

    ```groovy
    dependencies {
        implementation "ru.tinkoff.kora:cache-caffeine"
    }
    ```

=== ":simple-kotlin: `Gradle Kotlin DSL`"

    Update `build.gradle.kts`:

    ```kotlin
    dependencies {
        implementation("ru.tinkoff.kora:cache-caffeine")
    }
    ```

## Modules { #modules }

The application from the HTTP Server guide already uses `HoconConfigModule`, `JsonModule`, and `UndertowHttpServerModule`. Here we add `CaffeineCacheModule` so Kora can generate the cache
implementation.

===! ":fontawesome-brands-java: `Java`"

    Update `guides/guide-cache-app/src/main/java/ru/tinkoff/kora/guide/cache/Application.java`:

    ```java
    package ru.tinkoff.kora.guide.cache;

    import ru.tinkoff.kora.application.graph.KoraApplication;
    import ru.tinkoff.kora.cache.caffeine.CaffeineCacheModule;
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
            CaffeineCacheModule {  // <----- Connected module

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
        CaffeineCacheModule  // <----- Connected module

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

## Cache Implementation { #cache-impl }

A Kora cache starts from a typed `@Cache` interface. Kora generates its implementation at compile time and makes it available for dependency injection.

In this guide the key is the user identifier and the cached value is the full `UserResponse`.

This approach is useful for two reasons at once:

- annotations can refer to the cache contract by type
- services and tests can inject the same cache directly and manage it manually when needed

Since the contract extends `CaffeineCache<String, UserResponse>`, the generated component already exposes the operations you usually need for local cache management.

===! ":fontawesome-brands-java: `Java`"

    Create `guides/guide-cache-app/src/main/java/ru/tinkoff/kora/guide/cache/service/UserCaffeineCache.java`:

    ```java
    package ru.tinkoff.kora.guide.cache.service;

    import ru.tinkoff.kora.cache.annotation.Cache;
    import ru.tinkoff.kora.cache.caffeine.CaffeineCache;
    import ru.tinkoff.kora.guide.cache.dto.UserResponse;

    @Cache("cache.caffeine.users")
    public interface UserCaffeineCache extends CaffeineCache<String, UserResponse> {}
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/guide/cache/service/UserCaffeineCache.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.cache.service

    import ru.tinkoff.kora.cache.annotation.Cache
    import ru.tinkoff.kora.cache.caffeine.CaffeineCache
    import ru.tinkoff.kora.guide.cache.dto.UserResponse

    @Cache("cache.caffeine.users")
    interface UserCaffeineCache : CaffeineCache<String, UserResponse>
    ```

## `@Cacheable` { #cacheable }

The full rules for `@Cacheable`, `@CachePut`, `@CacheInvalidate`, and key calculation are covered in [Declarative caching](../documentation/cache.md#declarative) and [Cache key](../documentation/cache.md#key).

From this point on, assume the application runs in **exactly one instance**. That assumption lets us focus on local Caffeine behavior without solving cross-pod cache consistency yet.

We still keep the service contract from the HTTP Server guide:

- `getUsers()` still applies sorting and pagination
- the comparator helper remains unchanged
- update and delete still translate repository `boolean` results into HTTP-facing `404` errors

Kora applies cache annotations through compile-time AOP. For Java that means the service class must not be `final`; for Kotlin it must be `open`.

`@Cacheable` is the most natural starting point because it models the classic cache read path:

1. try cache first
2. if value is absent, call the original method
3. store the result for the next call

That is exactly what we want for `getUser()`.

===! ":fontawesome-brands-java: `Java`"

    Update only the read path in `guides/guide-cache-app/src/main/java/ru/tinkoff/kora/guide/cache/service/UserService.java`:

    ```java
    @Cacheable(UserCaffeineCache.class)
    public Optional<UserResponse> getUser(String id) {
        return userRepository.findById(id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update only the read path in `src/main/kotlin/ru/tinkoff/kora/guide/cache/service/UserService.kt`:

    ```kotlin
    @Cacheable(UserCaffeineCache::class)
    open fun getUser(id: String): UserResponse? {
        return userRepository.findById(id).orElse(null)
    }
    ```

In a **single-instance** application, this is straightforward and safe when user data is read much more often than it changes.

In an **N-pod** environment, `@Cacheable` still works, but each pod fills its own local cache independently. That can lead to:

- uneven warm-up across pods
- different pods serving different cached generations of the same entity
- more misses right after a rollout or restart

After compilation, the generated AOP proxy shows the read-through cache path:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-cache-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/cache/service/$UserService__AopProxy.java
    ```

    ```java
    private Optional<UserResponse> _getUser_AopProxy_CacheableAopKoraAspect(String id) {
        var _key = id;
        return Optional.ofNullable(userCaffeineCache1.computeIfAbsent(_key, _k -> super.getUser(id).orElse(null)));
    }

    @Override
    public Optional<UserResponse> getUser(String id) {
        return this._getUser_AopProxy_CacheableAopKoraAspect(id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-cache-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/cache/service/$UserService__AopProxy.kt
    ```

    ```kotlin
    private fun _getUser_AopProxy_CacheableAopKoraAspect(id: String): UserResponse? {
      val _key = id
      return userCaffeineCache1.computeIfAbsent(_key) { super.getUser(id) }
    }

    override fun getUser(id: String): UserResponse? = _getUser_AopProxy_CacheableAopKoraAspect(id)
    ```

The key point is `computeIfAbsent(...)`: Kora asks the cache first and calls `super.getUser(id)` only when the key is missing.

## `@CachePut` { #cacheput }

Once reads are cached, the next problem is stale data after updates. `@CachePut` solves that by executing the method first and then writing the returned value into the cache under the selected key.

That makes it a good fit for `updateUser()` because after a successful repository update we already know exactly what value should replace the old cache entry.

===! ":fontawesome-brands-java: `Java`"

    Update only the refresh path in `guides/guide-cache-app/src/main/java/ru/tinkoff/kora/guide/cache/service/UserService.java`:

    ```java
    @CachePut(value = UserCaffeineCache.class, parameters = { "id" })
    public UserResponse updateUser(String id, UserRequest request) {
        boolean updated = userRepository.update(id, request.name(), request.email());
        if (!updated) {
            throw HttpServerResponseException.of(404, "User not found");
        }
        return new UserResponse(id, request.name(), request.email(), LocalDateTime.now());
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update only the refresh path in `src/main/kotlin/ru/tinkoff/kora/guide/cache/service/UserService.kt`:

    ```kotlin
    @CachePut(value = UserCaffeineCache::class, parameters = ["id"])
    open fun updateUser(id: String, request: UserRequest): UserResponse {
        val updated = userRepository.update(id, request.name, request.email)
        if (!updated) {
            throw HttpServerResponseException.of(404, "User not found")
        }
        return UserResponse(id, request.name, request.email, LocalDateTime.now())
    }
    ```

In an **N-pod** environment, `@CachePut` updates only the local pod cache. Other pods keep their own previous values until they miss, expire, or are invalidated by some other mechanism.

So `@CachePut` is excellent for single-instance apps and still useful in multi-pod setups, but by itself it does **not** create cluster-wide consistency.

After compilation, the generated proxy shows that the original update runs before the cache write:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-cache-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/cache/service/$UserService__AopProxy.java
    ```

    ```java
    private UserResponse _updateUser_AopProxy_CachePutAopKoraAspect(String id, UserRequest request) {
        var _value = super.updateUser(id, request);
        var _key1 = id;
        userCaffeineCache1.put(_key1, _value);
        return _value;
    }

    @Override
    public UserResponse updateUser(String id, UserRequest request) {
        return this._updateUser_AopProxy_CachePutAopKoraAspect(id, request);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-cache-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/cache/service/$UserService__AopProxy.kt
    ```

    ```kotlin
    private fun _updateUser_AopProxy_CachePutAopKoraAspect(id: String, request: UserRequest):
        UserResponse {
      val _value = super.updateUser(id, request)
      val _key1 = id
      userCaffeineCache1.put(_key1, _value)
      return _value
    }

    override fun updateUser(id: String, request: UserRequest): UserResponse =
        _updateUser_AopProxy_CachePutAopKoraAspect(id, request)
    ```

This ordering matters: if `super.updateUser(...)` fails, the cache is not refreshed with a value that was never persisted.

## `@CacheInvalidate` { #cacheinvalidate }

If a record is deleted, the safest thing to do is evict the cached entry completely. That is what `@CacheInvalidate` does.

This is important because a stale cache entry after delete is usually worse than a cache miss: the application may return an entity that no longer exists in the source of truth.

===! ":fontawesome-brands-java: `Java`"

    Update only the eviction path in `guides/guide-cache-app/src/main/java/ru/tinkoff/kora/guide/cache/service/UserService.java`:

    ```java
    @CacheInvalidate(UserCaffeineCache.class)
    public void deleteUser(String id) {
        boolean deleted = userRepository.deleteById(id);
        if (!deleted) {
            throw HttpServerResponseException.of(404, "User not found");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update only the eviction path in `src/main/kotlin/ru/tinkoff/kora/guide/cache/service/UserService.kt`:

    ```kotlin
    @CacheInvalidate(UserCaffeineCache::class)
    open fun deleteUser(id: String) {
        val deleted = userRepository.deleteById(id)
        if (!deleted) {
            throw HttpServerResponseException.of(404, "User not found")
        }
    }
    ```

In an **N-pod** environment, the same caveat applies: invalidation affects only the local cache instance. Other pods may continue serving the old value until they are refreshed, expire, or are
explicitly invalidated by a broader mechanism.

After compilation, the generated proxy shows that invalidation happens after the delete method returns successfully:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-cache-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/cache/service/$UserService__AopProxy.java
    ```

    ```java
    private void _deleteUser_AopProxy_CacheInvalidateAopKoraAspect(String id) {
        super.deleteUser(id);
        var _key1 = id;
        userCaffeineCache1.invalidate(_key1);
    }

    @Override
    public void deleteUser(String id) {
        this._deleteUser_AopProxy_CacheInvalidateAopKoraAspect(id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-cache-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/cache/service/$UserService__AopProxy.kt
    ```

    ```kotlin
    private fun _deleteUser_AopProxy_CacheInvalidateAopKoraAspect(id: String) {
      super.deleteUser(id)
      val _key1 = id
      userCaffeineCache1.invalidate(_key1)
      return
    }

    override fun deleteUser(id: String) {
      _deleteUser_AopProxy_CacheInvalidateAopKoraAspect(id)
    }
    ```

That generated order prevents accidental eviction before the delete operation has actually completed.

## Cache Warm-Up { #cache-warmup }

`createUser()` is the place where declarative annotations are less convenient. The repository generates the identifier first, and only after that do we know the final cache key.

That is why this guide uses the cache imperatively for create:

- save the user
- build the final `UserResponse`
- manually write that value into the cache
- return the response

This is one of the main advantages of a typed cache contract: the same cache can be used declaratively on some methods and directly as a regular injected component on others.

===! ":fontawesome-brands-java: `Java`"

    Update only the create path in `guides/guide-cache-app/src/main/java/ru/tinkoff/kora/guide/cache/service/UserService.java`:

    ```java
    public UserResponse createUser(UserRequest request) {
        var generatedId = userRepository.save(request.name(), request.email());
        var createdUser = new UserResponse(generatedId, request.name(), request.email(), LocalDateTime.now());
        this.userCache.put(createdUser.id(), createdUser);
        return createdUser;
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update only the create path in `src/main/kotlin/ru/tinkoff/kora/guide/cache/service/UserService.kt`:

    ```kotlin
    fun createUser(request: UserRequest): UserResponse {
        val generatedId = userRepository.save(request.name, request.email)
        val createdUser = UserResponse(generatedId, request.name, request.email, LocalDateTime.now())
        userCache.put(createdUser.id, createdUser)
        return createdUser
    }
    ```

In a **single-instance** application this gives immediate warm-up, so the next read can be a cache hit right away.

In an **N-pod** environment this still warms only the local pod. Other pods will not see that entry until they load it themselves.

## Generated AOP Code { #aop-code }

The generated AOP code is the implementation of the declarative caching model; see [Declarative caching](../documentation/cache.md#declarative) for the full model.

The cache annotations in this guide are also implemented through compile-time AOP.

That means Kora does not rewrite your `UserService` source directly. Instead, it generates a subclass-based proxy around the service and places the caching logic into that generated class. Your
service method still looks like ordinary business code, but the generated proxy decides when to:

- check the cache before calling the original method
- store a returned value in the cache
- invalidate a cache entry after a successful method call

This is why the same AOP rule matters here too:

- in Java, the annotated service class must not be `final`
- in Kotlin, the annotated service class and annotated methods must be `open`

After you run:

```bash
./gradlew clean classes
```

you can inspect the generated proxy here:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-cache-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/cache/service/$UserService__AopProxy.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-cache-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/cache/service/$UserService__AopProxy.kt
    ```

That file is the best place to see what Kora actually generated for:

- `@Cacheable`
- `@CachePut`
- `@CacheInvalidate`

The earlier cache chapters showed the generated fragments next to the annotation that produced them. This final generated-code section is a map for debugging: open the proxy and search for the service
method whose cache behavior you want to verify.

If you are curious about the generated cache implementation itself, you can also inspect:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-cache-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/cache/service/$UserCaffeineCacheImpl.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-cache-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/cache/service/$UserCaffeineCacheModule.kt
    ```

Together these generated sources make the guide easier to reason about:

- the proxy shows how annotated service methods are wrapped
- the cache implementation shows how the typed cache contract is materialized for dependency injection

## Configuration { #config }

Keep the HTTP server configuration from the previous guide and add the Caffeine section that matches the `@Cache("cache.caffeine.users")` contract.

Update `guides/guide-cache-app/src/main/resources/application.conf`:

For the full configuration reference, see [Cache](../documentation/cache.md).

===! ":material-code-json: `Hocon`"

    ```javascript
    cache.caffeine.users {
      maximumSize = 1000 //(1)!
      expireAfterWrite = "10m" //(2)!
    }
    ```

    1. Maximum number of cache entries before eviction starts.
    2. Time after which an entry expires after being written.

=== ":simple-yaml: `YAML`"

    ```yaml
    cache:
      caffeine:
        users:
          maximumSize: 1000 #(1)!
          expireAfterWrite: "10m" #(2)!
    ```

    1. Maximum number of cache entries before eviction starts.
    2. Time after which an entry expires after being written.

## Run Application { #run-app }

Run the standard guide flow:

```bash
./gradlew clean classes
./gradlew test
./gradlew run
```

## Check Application { #check-app }

Start by creating a user:

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: req-1" \
  -H "User-Agent: curl" \
  -b "sessionId=test-session" \
  -d '{"name":"John Doe","email":"john@example.com"}'
```

Then read the same user twice. The first request loads it from the repository, and the second one reuses the cache entry.

```bash
curl http://localhost:8080/users/1
curl http://localhost:8080/users/1
```

Update the user. This refreshes the cached value through `@CachePut`.

```bash
curl -X PUT http://localhost:8080/users/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"John Updated","email":"john.updated@example.com"}'
```

Delete the user. This removes the stale cache entry through `@CacheInvalidate`.

```bash
curl -X DELETE http://localhost:8080/users/1
```

You can also verify the list endpoint from the base HTTP guide still works unchanged:

```bash
curl "http://localhost:8080/users?page=0&size=10&sort=name"
```

## Best Practices { #best-practices }

- Cache stable read paths first, then add write-side refresh or invalidation explicitly.
- Keep cache keys simple and predictable. Here the key is just the user id.
- Warm the cache manually only when annotations cannot derive the key naturally, such as after id generation in `createUser()`.
- Prefer local Caffeine caches for per-instance acceleration, not for globally shared state.
- Treat the typed cache contract as part of the design, not just as framework decoration.

## Summary { #summary }

You extended the HTTP Server guide with a local typed Caffeine cache and kept the existing `/users` API contract intact.

The resulting application now uses:

- imperative cache warming in `createUser()`
- declarative read caching in `getUser()`
- declarative cache refresh in `updateUser()`
- declarative invalidation in `deleteUser()`
- a typed cache contract that can be both annotated and injected directly
- generated AOP proxy code to apply the cache annotations around the service methods

## Key Concepts { #key-concepts }

- a cache is a fast secondary storage layer for repeated reads
- local in-memory caches improve one pod or one process at a time
- `CaffeineCache<K, V>` gives you a typed cache contract that Kora implements at compile time
- `@Cacheable`, `@CachePut`, and `@CacheInvalidate` cover the most common read, refresh, and eviction flows
- imperative and declarative caching can be combined in one service when different methods need different control over cache timing
- the generated `$UserService__AopProxy` source shows exactly how Kora wraps annotated methods

## Troubleshooting { #troubleshooting }

**Cache annotations do not work:**

Make sure the service class is not `final` in Java and is `open` in Kotlin. Kora cache aspects are applied through compile-time AOP and need a subclassable target.

**I want to see where the cache annotations really run:**

Run:

```bash
./gradlew clean classes
```

Then inspect:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-cache-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/cache/service/$UserService__AopProxy.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-cache-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/cache/service/$UserService__AopProxy.kt
    ```

That generated file shows where Kora inserts the cache checks, cache writes, and invalidation logic around your original `UserService` methods.

**Cache never updates after create:**

`createUser()` generates the identifier after calling the repository, so a manual `userCache.put(createdUser.id(), createdUser)` is required if you want the new entity cached before the first read.

**Gradle hangs or fails unexpectedly:**

Stop running Gradle daemons and retry:

```bash
./gradlew --stop
./gradlew clean classes
```

**Windows `AccessDeniedException` in Gradle cache:**

If Windows keeps file handles open in `.gradle` or `build/`, stop Gradle daemons, close IDE processes that still watch the directory, and rerun the command.

**Docker build context errors in later black-box tests:**

If you later package this app for black-box testing, make sure the `Dockerfile` uses the module directory as its build context. Errors like `COPY failed` usually mean the build was started from the
wrong folder.

**Readiness checks fail in later observability steps:**

If you continue this app with observability, remember that readiness is checked on `http://localhost:8085/system/readiness`, not on the public `8080` port.

## What's Next? { #whats-next }

- [Multi-Level Cache](cache-multi-level.md) to combine local Caffeine cache with distributed Redis cache.
- [Resilient Patterns](resilient.md) to protect expensive downstream calls before their results are cached.
- [Observability](observability.md) to measure cache-backed request paths with metrics and traces.
- [Testing with JUnit](testing-junit.md) to add focused component checks around cached services.

## Help { #help }

If you run into trouble:

- compare with [Kora Java Cache App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-cache-app) and [Kora Kotlin Cache App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-cache-app)
- check the [Cache documentation](../documentation/cache.md)
- check the [Caffeine example](https://github.com/kora-projects/kora-examples/tree/master/kora-java-cache-caffeine)
- revisit [Database JDBC](database-jdbc.md) if repository behavior is unclear
