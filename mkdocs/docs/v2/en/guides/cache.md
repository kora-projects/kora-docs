---
search:
  exclude: true
title: Caching Strategies with Kora
summary: Learn how to extend the HTTP Server guide with typed Caffeine caching, cache annotations, and local performance optimization
description: "Step-by-step in-process caching for a Kora 2.0 service with Caffeine: the io.koraframework:cache-caffeine artifact, CaffeineCacheModule, a typed @Cache contract extending CaffeineCache<K, V>, the @Cacheable, @CachePut, @CacheInvalidate and @CacheInvalidateAll aspects, the args attribute that selects cache key parameters, imperative warm-up through the injected cache contract, the cache.caffeine configuration section, and the generated AOP proxy and cache implementation sources."
agent:
  use_when: "Use this file for questions about adding an in-process Caffeine cache to a Kora 2.0 service: io.koraframework:cache-caffeine, CaffeineCacheModule, the @Cache annotation with a config path, CaffeineCache<K, V>, @Cacheable, @CachePut with the args attribute, @CacheInvalidate, @CacheInvalidateAll, CacheMode, maximumSize and expireAfterWrite config keys, why cache aspects need a non-final Java class or an open Kotlin class, and how to read the generated cache AOP proxy."
tags: caching, performance, caffeine, cacheable, cacheput, cache-invalidate, optimization
---

# Caching Strategies with Kora { #caching-strategies-kora }

This guide introduces local caching with Kora and Caffeine. It covers how cache interfaces describe stored values, how cache annotations wrap service methods, and how invalidation keeps reads aligned
with create, update, and delete operations. You will also see how a local in-memory cache improves repeated lookups while the repository remains the source of truth.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java Cache App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-cache-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin Cache App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-cache-app).

## What You'll Build { #youll-build }

In this guide, you'll turn the `UserService` from the HTTP Server guide into a cache-aware service that:

- warms the cache immediately after `createUser()`
- reuses cached values for repeated `getUser()` calls
- refreshes cached values on `updateUser()`
- evicts stale entries on `deleteUser()`
- keeps the same `/users` HTTP contract while making repeated reads cheaper

## What You'll Need { #youll-need }

- JDK 25 or later
- Gradle 9+
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

- **Declarative caching** with `@Cacheable`, `@CachePut`, `@CacheInvalidate`, and `@CacheInvalidateAll`
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
- `getAll()` to read the whole content of a Caffeine cache

This makes the cache both declarative-friendly and operationally explicit. You keep framework support, but you do not lose control.

## Dependencies { #dependencies }

Add the Caffeine cache dependency to the application from the HTTP Server guide. Everything else — the config module, the HTTP server, JSON, logging, and the JUnit test setup — is already in place.

===! ":fontawesome-brands-java: `Java`"

    Add to the `dependencies` block in `build.gradle`:

    ```groovy
    dependencies {
        // ... existing dependencies ...

        implementation("io.koraframework:cache-caffeine")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Add to the `dependencies` block in `build.gradle.kts`:

    ```kotlin
    dependencies {
        // ... existing dependencies ...

        implementation("io.koraframework:cache-caffeine")
    }
    ```

The artifact version comes from the `io.koraframework:kora-bom` platform that the application already imports, so no explicit version is needed here. `cache-caffeine` brings both the Caffeine library
and the Kora cache contracts, so the annotation processor can generate the cache implementation for your typed contract.

## Modules { #modules }

The application from the HTTP Server guide already uses `HoconConfigModule`, `JsonModule`, `LogbackModule`, and `UndertowPublicHttpServerModule`. Here we add `CaffeineCacheModule` so Kora can build
the cache implementation and its telemetry.

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/java/io/koraframework/guide/cache/Application.java`:

    ```java
    package io.koraframework.guide.cache;

    import io.koraframework.application.graph.KoraApplication;
    import io.koraframework.cache.caffeine.CaffeineCacheModule;
    import io.koraframework.common.annotation.KoraApp;
    import io.koraframework.config.hocon.HoconConfigModule;
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule;
    import io.koraframework.json.common.JsonModule;
    import io.koraframework.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            UndertowPublicHttpServerModule,
            CaffeineCacheModule {  // <----- Connected module

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update `src/main/kotlin/io/koraframework/guide/cache/Application.kt`:

    ```kotlin
    package io.koraframework.guide.cache

    import io.koraframework.application.graph.KoraApplication
    import io.koraframework.cache.caffeine.CaffeineCacheModule
    import io.koraframework.common.annotation.KoraApp
    import io.koraframework.config.hocon.HoconConfigModule
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule
    import io.koraframework.json.common.JsonModule
    import io.koraframework.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        UndertowPublicHttpServerModule,
        CaffeineCacheModule  // <----- Connected module

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

`CaffeineCacheModule` contributes a `CaffeineCacheFactory` and a cache telemetry factory as `@DefaultComponent`, which means your own component of the same type would override them. It also pulls in
`CacheCommonModule`, the shared part of the cache subsystem.

## Cache Implementation { #cache-impl }

A Kora cache starts from a typed `@Cache` interface. Kora generates its implementation at compile time and makes it available for dependency injection.

The annotation value is the **configuration path** of this cache. It is not a symbolic name: Kora reads `CaffeineCacheConfig` from exactly that path in `application.conf`, so
`@Cache("cache.caffeine.users")` and the `cache.caffeine.users { ... }` config section belong together.

In this guide the key is the user identifier and the cached value is the full `UserResponse`.

This approach is useful for two reasons at once:

- annotations can refer to the cache contract by type
- services and tests can inject the same cache directly and manage it manually when needed

Since the contract extends `CaffeineCache<String, UserResponse>`, the generated component already exposes the operations you usually need for local cache management.

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/io/koraframework/guide/cache/service/UserCaffeineCache.java`:

    ```java
    package io.koraframework.guide.cache.service;

    import io.koraframework.cache.annotation.Cache;
    import io.koraframework.cache.caffeine.CaffeineCache;
    import io.koraframework.guide.cache.dto.UserResponse;

    @Cache("cache.caffeine.users")
    public interface UserCaffeineCache extends CaffeineCache<String, UserResponse> {}
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/io/koraframework/guide/cache/service/UserCaffeineCache.kt`:

    ```kotlin
    package io.koraframework.guide.cache.service

    import io.koraframework.cache.annotation.Cache
    import io.koraframework.cache.caffeine.CaffeineCache
    import io.koraframework.guide.cache.dto.UserResponse

    @Cache("cache.caffeine.users")
    interface UserCaffeineCache : CaffeineCache<String, UserResponse>
    ```

`@Cache` may only be placed on an interface that extends `CaffeineCache<K, V>` or `RedisCache<K, V>`. Applying it to a class fails compilation with a message that says exactly that.

Now inject the cache into `UserService` next to the repository. The service keeps its existing constructor shape, it just gains one more dependency:

===! ":fontawesome-brands-java: `Java`"

    Update the constructor in `src/main/java/io/koraframework/guide/cache/service/UserService.java`:

    ```java
    @Component
    public class UserService {

        private final UserRepository userRepository;
        private final UserCaffeineCache userCache;

        public UserService(UserRepository userRepository, UserCaffeineCache userCache) {
            this.userRepository = userRepository;
            this.userCache = userCache;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update the constructor in `src/main/kotlin/io/koraframework/guide/cache/service/UserService.kt`:

    ```kotlin
    @Component
    open class UserService(
        private val userRepository: UserRepository,
        private val userCache: UserCaffeineCache
    ) {
    }
    ```

Note the class-level change for Kotlin: `UserService` becomes `open`. Cache annotations are compile-time aspects, and an aspect needs a subclassable target. The same rule in Java means the service
class must not be `final`.

## `@Cacheable` { #cacheable }

The full rules for `@Cacheable`, `@CachePut`, `@CacheInvalidate`, `@CacheInvalidateAll`, and key calculation are covered in [Declarative caching](../documentation/cache.md#declarative) and
[Cache key](../documentation/cache.md#key).

From this point on, assume the application runs in **exactly one instance**. That assumption lets us focus on local Caffeine behavior without solving cross-pod cache consistency yet.

We still keep the service contract from the HTTP Server guide:

- `getUsers()` still applies sorting and pagination
- the comparator helper remains unchanged
- update and delete still translate repository `boolean` results into HTTP-facing `404` errors

`@Cacheable` is the most natural starting point because it models the classic cache read path:

1. try cache first
2. if value is absent, call the original method
3. store the result for the next call

That is exactly what we want for `getUser()`.

===! ":fontawesome-brands-java: `Java`"

    Update only the read path in `src/main/java/io/koraframework/guide/cache/service/UserService.java`:

    ```java
    @Cacheable(UserCaffeineCache.class)
    public Optional<UserResponse> getUser(String id) {
        return userRepository.findById(id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update only the read path in `src/main/kotlin/io/koraframework/guide/cache/service/UserService.kt`:

    ```kotlin
    @Cacheable(UserCaffeineCache::class)
    open fun getUser(id: String): UserResponse? = userRepository.findById(id)
    ```

The method has exactly one parameter and no explicit `args`, so `id` becomes the cache key. `Optional<UserResponse>` in Java and `UserResponse?` in Kotlin are both supported: Kora unwraps the
container before writing to the cache, so the cache still stores plain `UserResponse` values and an empty result is simply not cached.

In a **single-instance** application, this is straightforward and safe when user data is read much more often than it changes.

In an **N-pod** environment, `@Cacheable` still works, but each pod fills its own local cache independently. That can lead to:

- uneven warm-up across pods
- different pods serving different cached generations of the same entity
- more misses right after a rollout or restart

After compilation, the generated AOP proxy shows the read-through cache path:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/java/kora-java-guide-cache-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/cache/service/$UserService__AopProxy.java
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
    guides/kotlin/kora-kotlin-guide-cache-app/build/generated/ksp/main/kotlin/io/koraframework/guide/cache/service/$UserService__AopProxy.kt
    ```

    ```kotlin
    private fun _getUser_AopProxy_CacheableAopKoraAspect(id: String): UserResponse? {
      val _key = id
      return userCaffeineCache1.computeIfAbsent(_key) { super.getUser(id) }
    }

    override fun getUser(id: String): UserResponse? = _getUser_AopProxy_CacheableAopKoraAspect(id)
    ```

The key point is `computeIfAbsent(...)`: Kora asks the cache first and calls `super.getUser(id)` only when the key is missing.

`@Cacheable` requires a method that returns a value synchronously. A `void` method, a `CompletionStage`, a `Future`, or a reactive `Publisher` return type is rejected at compile time with an explicit
message, because a read-through cache has nothing meaningful to store for them.

## `@CachePut` { #cacheput }

Once reads are cached, the next problem is stale data after updates. `@CachePut` solves that by executing the method first and then writing the returned value into the cache under the selected key.

That makes it a good fit for `updateUser()` because after a successful repository update we already know exactly what value should replace the old cache entry.

===! ":fontawesome-brands-java: `Java`"

    Update only the refresh path in `src/main/java/io/koraframework/guide/cache/service/UserService.java`:

    ```java
    @CachePut(value = UserCaffeineCache.class, args = { "id" })
    public UserResponse updateUser(String id, UserRequest request) {
        boolean updated = userRepository.update(id, request.name(), request.email());
        if (!updated) {
            throw HttpServerResponseException.of(404, "User not found");
        }
        return new UserResponse(id, request.name(), request.email(), LocalDateTime.now());
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update only the refresh path in `src/main/kotlin/io/koraframework/guide/cache/service/UserService.kt`:

    ```kotlin
    @CachePut(value = UserCaffeineCache::class, args = ["id"])
    open fun updateUser(id: String, request: UserRequest): UserResponse {
        if (!userRepository.update(id, request.name, request.email)) {
            throw HttpServerResponseException.of(404, "User not found")
        }
        return UserResponse(id, request.name, request.email, LocalDateTime.now())
    }
    ```

### Key Arguments { #key-args }

`updateUser()` is the first method in this guide where the cache key is *not* simply "all parameters". The method takes `id` and `request`, but only `id` identifies the cache entry. That is what the
`args` attribute is for.

The rules Kora applies when it computes a key are short and worth memorizing:

- `args` is omitted — every method parameter takes part in the key, in declaration order. That is why `getUser(String id)` needs no `args` at all.
- `args = { "id" }` — only the listed parameters take part in the key, and the names must match real parameter names. A typo is a compile-time error that lists the parameters that do exist.
- one key parameter — the parameter value is used as the key directly, so its type must match the cache key type.
- several key parameters — Kora looks for a public constructor of the key type whose parameters match, for example a `record` or a `data class` key. If there is none, it asks the graph for a
  `CacheKeyMapper` component with the matching arity, and you can always supply your own with `@Mapping(MyKeyMapper.class)`.
- at most nine key parameters are supported without a custom mapper.

A `CacheKeyMapper` that has no constructor dependencies must **not** be annotated with `@Component`: Kora instantiates such a mapper itself, and an extra component declaration makes the graph fail
with `Multiple components match`. A mapper that does have dependencies is an ordinary component and needs `@Component` as usual.

One more constraint applies to every annotation in this family: repeated cache annotations on the same method must declare the same `args` list, and different operation kinds — `@Cacheable` together
with `@CachePut`, for instance — cannot be mixed on one method. Both cases are compile-time errors.

In an **N-pod** environment, `@CachePut` updates only the local pod cache. Other pods keep their own previous values until they miss, expire, or are invalidated by some other mechanism.

So `@CachePut` is excellent for single-instance apps and still useful in multi-pod setups, but by itself it does **not** create cluster-wide consistency.

After compilation, the generated proxy shows that the original update runs before the cache write:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/java/kora-java-guide-cache-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/cache/service/$UserService__AopProxy.java
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
    guides/kotlin/kora-kotlin-guide-cache-app/build/generated/ksp/main/kotlin/io/koraframework/guide/cache/service/$UserService__AopProxy.kt
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

    Update only the eviction path in `src/main/java/io/koraframework/guide/cache/service/UserService.java`:

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

    Update only the eviction path in `src/main/kotlin/io/koraframework/guide/cache/service/UserService.kt`:

    ```kotlin
    @CacheInvalidate(UserCaffeineCache::class)
    open fun deleteUser(id: String) {
        if (!userRepository.deleteById(id)) {
            throw HttpServerResponseException.of(404, "User not found")
        }
    }
    ```

Unlike `@Cacheable` and `@CachePut`, `@CacheInvalidate` works on `void` methods too — there is no value to store, only a key to remove.

In an **N-pod** environment, the same caveat applies: invalidation affects only the local cache instance. Other pods may continue serving the old value until they are refreshed, expire, or are
explicitly invalidated by a broader mechanism.

After compilation, the generated proxy shows that invalidation happens after the delete method returns successfully:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/java/kora-java-guide-cache-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/cache/service/$UserService__AopProxy.java
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
    guides/kotlin/kora-kotlin-guide-cache-app/build/generated/ksp/main/kotlin/io/koraframework/guide/cache/service/$UserService__AopProxy.kt
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

## `@CacheInvalidateAll` { #cacheinvalidateall }

Sometimes a single key is not enough. A bulk import, a reference-data reload, or an administrative reset makes every cached entry suspect at once. `@CacheInvalidateAll` clears the whole cache after
the annotated method completes.

It is a separate annotation with its own semantics, so it takes no `args` — there is no key to compute.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @CacheInvalidateAll(UserCaffeineCache.class)
    public void reloadUsers() {
        userRepository.reloadAll();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @CacheInvalidateAll(UserCaffeineCache::class)
    open fun reloadUsers() {
        userRepository.reloadAll()
    }
    ```

Use it deliberately. On a hot path, wiping the whole cache turns every following read into a miss, so a burst of load right after the reset hits the source of truth at full strength. Prefer key-level
`@CacheInvalidate` whenever the affected keys are known.

The same operation is available imperatively as `userCache.invalidateAll()`, which is exactly what the companion application does between tests.

## Cache Warm-Up { #cache-warmup }

`createUser()` is the place where declarative annotations are less convenient. The repository generates the identifier first, and only after that do we know the final cache key.

That is why this guide uses the cache imperatively for create:

- save the user
- build the final `UserResponse`
- manually write that value into the cache
- return the response

This is one of the main advantages of a typed cache contract: the same cache can be used declaratively on some methods and directly as a regular injected component on others.

===! ":fontawesome-brands-java: `Java`"

    Update only the create path in `src/main/java/io/koraframework/guide/cache/service/UserService.java`:

    ```java
    public UserResponse createUser(UserRequest request) {
        var generatedId = userRepository.save(request.name(), request.email());
        var createdUser = new UserResponse(generatedId, request.name(), request.email(), LocalDateTime.now());
        this.userCache.put(createdUser.id(), createdUser);
        return createdUser;
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update only the create path in `src/main/kotlin/io/koraframework/guide/cache/service/UserService.kt`:

    ```kotlin
    fun createUser(request: UserRequest): UserResponse {
        val id = userRepository.save(request.name, request.email)
        val user = UserResponse(id, request.name, request.email, LocalDateTime.now())
        userCache.put(user.id, user)
        return user
    }
    ```

Because this method uses the cache directly instead of an annotation, it does not need to be `open` in Kotlin — only aspect-driven methods do.

In a **single-instance** application this gives immediate warm-up, so the next read can be a cache hit right away.

In an **N-pod** environment this still warms only the local pod. Other pods will not see that entry until they load it themselves.

## Generated AOP Code { #aop-code }

The generated AOP code is the implementation of the declarative caching model; see [Declarative caching](../documentation/cache.md#declarative) for the full model.

The cache annotations in this guide are implemented through compile-time AOP.

That means Kora does not rewrite your `UserService` source directly. Instead, it generates a subclass-based proxy around the service and places the caching logic into that generated class. Your
service method still looks like ordinary business code, but the generated proxy decides when to:

- check the cache before calling the original method
- store a returned value in the cache
- invalidate a cache entry after a successful method call

This is why the same AOP rule matters here too:

- in Java, the annotated service class must not be `final`, and annotated methods must be neither `final` nor `private`
- in Kotlin, the annotated service class and annotated methods must be `open`

After you run:

```bash
./gradlew clean classes
```

you can inspect the generated proxy here:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/java/kora-java-guide-cache-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/cache/service/$UserService__AopProxy.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/kora-kotlin-guide-cache-app/build/generated/ksp/main/kotlin/io/koraframework/guide/cache/service/$UserService__AopProxy.kt
    ```

That file is the best place to see what Kora actually generated for:

- `@Cacheable`
- `@CachePut`
- `@CacheInvalidate`
- `@CacheInvalidateAll`

Each aspect becomes one private method named `_<method>_AopProxy_<AspectName>`, and the public override simply delegates to it. When several aspects apply to one method, they are chained: each
generated method calls the next one instead of `super`, and only the innermost call reaches your original code.

The earlier cache chapters showed the generated fragments next to the annotation that produced them. This final generated-code section is a map for debugging: open the proxy and search for the service
method whose cache behavior you want to verify.

If you are curious about the generated cache implementation itself, you can also inspect:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/java/kora-java-guide-cache-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/cache/service/$UserCaffeineCache_Impl.java
    guides/java/kora-java-guide-cache-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/cache/service/$UserCaffeineCache_Module.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/kora-kotlin-guide-cache-app/build/generated/ksp/main/kotlin/io/koraframework/guide/cache/service/$UserCaffeineCache_Impl.kt
    guides/kotlin/kora-kotlin-guide-cache-app/build/generated/ksp/main/kotlin/io/koraframework/guide/cache/service/$UserCaffeineCache_Module.kt
    ```

Together these generated sources make the guide easier to reason about:

- the proxy shows how annotated service methods are wrapped
- `$UserCaffeineCache_Impl` is the concrete cache built on top of Caffeine
- `$UserCaffeineCache_Module` is the module that reads `CaffeineCacheConfig` from the configured path and registers the cache in the graph

## Configuration { #config }

Keep the HTTP server configuration from the previous guide and add the Caffeine section that matches the `@Cache("cache.caffeine.users")` contract.

Update `src/main/resources/application.conf`:

For the full configuration reference, see [Cache](../documentation/cache.md#caffeine).

===! ":material-code-json: `Hocon`"

    ```javascript
    cache.caffeine.users {
      maximumSize = 1000 //(1)!
      expireAfterWrite = "10m" //(2)!
    }
    ```

    1. Maximum number of cache entries before eviction starts *(default: `100000`)*.
    2. Time after which an entry expires after being written *(optional)*.

=== ":simple-yaml: `YAML`"

    ```yaml
    cache:
      caffeine:
        users:
          maximumSize: 1000 #(1)!
          expireAfterWrite: "10m" #(2)!
    ```

    1. Maximum number of cache entries before eviction starts *(default: `100000`)*.
    2. Time after which an entry expires after being written *(optional)*.

The full set of options a Caffeine cache section accepts:

| Option                | Description                                                                | Default                  |
|-----------------------|----------------------------------------------------------------------------|--------------------------|
| `enabled`             | Turns the cache off without removing it from the code                       | `true`                   |
| `maximumSize`         | Maximum number of entries before the least relevant ones are evicted        | `100000`                 |
| `expireAfterWrite`    | Time after which an entry is removed, counted from the write                | *(optional)*             |
| `expireAfterAccess`   | Time after which an entry is removed, counted from the last read            | *(optional)*             |
| `initialSize`         | Initial capacity of the underlying map                                      | *(optional)*             |
| `telemetry.logging.enabled` | Logs cache operations                                                 | `false`                  |
| `telemetry.metrics.enabled` | Registers Caffeine metrics in the meter registry                      | `false`                  |
| `telemetry.tracing.enabled` | Creates a span per cache operation                                    | `true`                   |

Because the config path is part of the `@Cache` contract, adding a second cache means adding a second section. A missing section is a startup failure, not a silent default: the graph cannot build a
cache whose configuration is absent.

## Verify with a Test { #verify-test }

The most convincing proof that caching works is a test that counts how many times the repository was actually asked. The companion application does exactly that: `InMemoryUserRepository` increments a
counter inside `findById`, and the test asserts that the second read never reaches it.

`@KoraAppTest` starts the real application graph, and `@TestComponent` injects components out of it — including the generated cache, which is a normal graph component like any other.

===! ":fontawesome-brands-java: `Java`"

    Create `src/test/java/io/koraframework/guide/cache/CacheAppTest.java`:

    ```java
    @KoraAppTest(Application.class)
    class CacheAppTest {

        @TestComponent
        private UserService userService;
        @TestComponent
        private UserCaffeineCache userCache;
        @TestComponent
        private InMemoryUserRepository userRepository;

        @BeforeEach
        void cleanup() {
            this.userCache.invalidateAll();
            this.userRepository.resetStats();
        }

        @Test
        void cacheablePopulatesCacheOnFirstReadAndUsesCacheOnSecondRead() {
            var created = this.userService.createUser(new UserRequest("Bob", "bob@example.com"));
            this.userCache.invalidate(created.id());
            this.userRepository.resetStats();

            assertNull(this.userCache.get(created.id()));

            var first = this.userService.getUser(created.id());

            assertTrue(first.isPresent());
            assertEquals(created.id(), this.userCache.get(created.id()).id());
            assertEquals(1, this.userRepository.getFindByIdCalls());

            var second = this.userService.getUser(created.id());

            assertTrue(second.isPresent());
            assertEquals(1, this.userRepository.getFindByIdCalls());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/test/kotlin/io/koraframework/guide/cache/CacheAppTest.kt`:

    ```kotlin
    @KoraAppTest(Application::class)
    class CacheAppTest {

        @TestComponent
        lateinit var userService: UserService

        @TestComponent
        lateinit var userCache: UserCaffeineCache

        @Test
        fun cacheablePopulatesCacheOnFirstRead() {
            val created = userService.createUser(UserRequest("Alice", "alice@example.com"))
            userCache.invalidate(created.id)

            assertNull(userCache.get(created.id))

            val first = userService.getUser(created.id)

            assertNotNull(first)
            assertEquals(created.id, first!!.id)
            assertEquals(created.id, userCache.get(created.id)!!.id)
        }
    }
    ```

The important detail is the last assertion of the Java test: the repository counter stays at `1` after two reads. Without the cache it would be `2`.

For the full testing workflow — mocks, config modification, and Testcontainers — see [Testing with JUnit](testing-junit.md).

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
- Name the key parameters with `args` as soon as a method takes more arguments than the key needs.
- Warm the cache manually only when annotations cannot derive the key naturally, such as after id generation in `createUser()`.
- Prefer local Caffeine caches for per-instance acceleration, not for globally shared state.
- Always set a bound: `maximumSize`, `expireAfterWrite`, or both. An unbounded local cache is a slow memory leak.
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
- a component test that proves repeated reads no longer reach the repository

## Key Concepts { #key-concepts }

- a cache is a fast secondary storage layer for repeated reads
- local in-memory caches improve one pod or one process at a time
- `CaffeineCache<K, V>` gives you a typed cache contract that Kora implements at compile time
- the `@Cache` value is a configuration path, so a contract and its config section always come as a pair
- `@Cacheable`, `@CachePut`, `@CacheInvalidate`, and `@CacheInvalidateAll` cover the most common read, refresh, and eviction flows
- `args` selects which method parameters build the cache key; without it every parameter takes part
- imperative and declarative caching can be combined in one service when different methods need different control over cache timing
- the generated `$UserService__AopProxy` source shows exactly how Kora wraps annotated methods

## Troubleshooting { #troubleshooting }

**Cache annotations do not work:**

Make sure the service class is not `final` in Java and is `open` in Kotlin. Kora cache aspects are applied through compile-time AOP and need a subclassable target. The compiler is explicit about it:

```text
AOP aspect cannot be applied to class 'io.koraframework.guide.cache.service.UserService' because the class is final.

Fix: remove the final modifier, or move the aspect annotation to a non-final member method.
```

The Kotlin processor reports the same situation as `because the class is not open`, and both processors have matching messages for a `final`/non-`open` or `private` method.

**`Cache key references unknown method parameter`:**

The name inside `args` must match a real parameter name of the annotated method. The error message lists the parameters that actually exist, so compare them character by character — the usual cause is
a renamed parameter that the annotation did not follow.

**`Cache annotations on ... use different key argument lists`:**

Every repeated cache annotation on one method must use the same `args`. If two layers really need different keys, they belong on different methods.

**`Cache method ... mixes different cache operation annotation types`:**

One method carries exactly one kind of cache operation. Split the method if you need both a read-through cache and an eviction.

**I want to see where the cache annotations really run:**

Run:

```bash
./gradlew clean classes
```

Then inspect:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/java/kora-java-guide-cache-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/cache/service/$UserService__AopProxy.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/kora-kotlin-guide-cache-app/build/generated/ksp/main/kotlin/io/koraframework/guide/cache/service/$UserService__AopProxy.kt
    ```

That generated file shows where Kora inserts the cache checks, cache writes, and invalidation logic around your original `UserService` methods.

**Cache never updates after create:**

`createUser()` generates the identifier after calling the repository, so a manual `userCache.put(createdUser.id(), createdUser)` is required if you want the new entity cached before the first read.

**The cache section is missing from configuration:**

The value of `@Cache` is a config path, not a label. If `cache.caffeine.users` is absent from `application.conf`, the application fails while building the graph because the cache configuration cannot
be read.

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

- compare with [Kora Java Cache App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-cache-app) and [Kora Kotlin Cache App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-cache-app)
- check the [Cache documentation](../documentation/cache.md)
- check the [Caffeine example](https://github.com/kora-projects/kora-examples/tree/master/examples/java/kora-java-cache-caffeine)
- revisit [Database JDBC](database-jdbc.md) if repository behavior is unclear
