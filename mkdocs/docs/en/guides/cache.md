---
title: Caching Strategies with Kora
summary: Learn how to add performance optimization with in-memory and distributed caching to your Kora applications
tags: caching, performance, caffeine, redis, cacheable, optimization
---

# Caching Strategies with Kora

This guide shows you how to add powerful caching capabilities to your Kora applications for improved performance and scalability.

## What is Caching?

**Caching** is a technique that stores frequently accessed data in fast, temporary storage to improve application performance and reduce response times. Instead of fetching data from slow sources (like databases or external APIs) every time it's needed, your application can retrieve it from the cache, which is much faster.

### When to Use Caching

Use caching when you have:

- **Frequently accessed data** that doesn't change often (user profiles, configuration, reference data)
- **Expensive operations** like complex database queries, API calls, or heavy computations
- **Performance bottlenecks** where database or external service calls are slowing down your application
- **High-traffic applications** where reducing load on backend systems is critical
- **Data that can be slightly stale** (acceptable to serve cached data that's a few seconds/minutes old)

### Benefits of Caching

- **Faster response times**: Sub-millisecond cache access vs seconds for database queries
- **Reduced server load**: Fewer requests to databases and external services
- **Better scalability**: Handle more concurrent users with the same infrastructure
- **Cost savings**: Lower database and API usage costs
- **Improved user experience**: Faster page loads and API responses

## What You'll Build

You'll enhance your existing API with:

- **In-memory caching**: Fast local caching with Caffeine
- **Cache annotations**: Declarative caching with `@Cacheable`, `@CachePut`, `@CacheEvict`
- **Custom cache keys**: Flexible key mapping strategies
- **Cache configuration**: TTL, size limits, and performance tuning
- **Performance monitoring**: Cache hit/miss metrics

## What You'll Need

- JDK 17 or later
- Gradle 7.0+
- A text editor or IDE
- Completed [Creating Your First Kora App](../creating-your-first-kora-app.md) guide
- (Optional) Docker for Redis testing

## Prerequisites

!!! note "Required: Complete Basic Kora Setup"

    This guide assumes you have completed the **[Create Your First Kora App](../creating-your-first-kora-app.md)** guide and have a working Kora project with basic setup.

    If you haven't completed the basic guide yet, please do so first as this guide builds upon that foundation.

## Add Dependencies

Add the Caffeine caching dependency to your existing `build.gradle` or `build.gradle.kts`:

===! ":fontawesome-brands-java: `Java`"

    Add to the `dependencies` block in `build.gradle`:

    ```groovy
    dependencies {
        // ... existing dependencies ...

        implementation("ru.tinkoff.kora:cache-caffeine")  // In-memory caching
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Add to the `dependencies` block in `build.gradle.kts`:

    ```kotlin
    dependencies {
        // ... existing dependencies ...

        implementation("ru.tinkoff.kora:cache-caffeine")  // In-memory caching
    }
    ```

## Updating Your Application

Update your existing `Application.java` or `Application.kt` to include the cache modules:

===! ":fontawesome-brands-java: Java"

    Update `src/main/java/ru/tinkoff/kora/example/Application.java`:

    ```java
    package ru.tinkoff.kora.example;

    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule;
    import ru.tinkoff.kora.json.module.JsonModule;
    import ru.tinkoff.kora.validation.module.ValidationModule;
    import ru.tinkoff.kora.cache.caffeine.CaffeineCacheModule;

    @KoraApp
    public interface Application extends
            UndertowHttpServerModule,
            JsonModule,
            ValidationModule,
            CaffeineCacheModule {  // Add for in-memory caching
    }
    ```

=== ":simple-kotlin: Kotlin"

    Update `src/main/kotlin/ru/tinkoff/kora/example/Application.kt`:

    ```kotlin
    package ru.tinkoff.kora.example

    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule
    import ru.tinkoff.kora.json.module.JsonModule
    import ru.tinkoff.kora.validation.module.ValidationModule
    import ru.tinkoff.kora.cache.caffeine.CaffeineCacheModule

    @KoraApp
    interface Application :
        UndertowHttpServerModule,
        JsonModule,
        ValidationModule,
        CaffeineCacheModule  // Add for in-memory caching
    ```

## What is Caffeine?

**Caffeine** is a high-performance, near-optimal Java caching library developed by Ben Manes. Originally created as a rewrite of Google's Guava Cache to address performance and feature limitations, Caffeine has become the de facto standard for in-memory caching in Java applications.

### Core Caffeine Concepts

- **W-TinyLFU**: Advanced eviction algorithm that provides near-optimal hit rates
- **Windowed Statistics**: Tracks access patterns over time windows for better eviction decisions
- **Bounded Caching**: Configurable size and time-based expiration limits
- **Loading Caches**: Automatic value loading with synchronous and asynchronous support
- **Refresh Ahead**: Proactive cache refresh before expiration
- **Listener Support**: Callbacks for eviction, removal, and access events

### Key Capabilities for Caching

- **Sub-millisecond Latency**: Highly optimized for speed with minimal overhead
- **High Throughput**: Can handle millions of operations per second
- **Size-based Eviction**: Automatic removal of least-recently-used entries when size limits are reached
- **Time-based Expiration**: TTL (Time To Live) and TTI (Time To Idle) support
- **Statistics Collection**: Detailed metrics on hits, misses, evictions, and load times
- **Concurrent Access**: Thread-safe operations supporting high concurrency
- **Memory Efficiency**: Optimized memory usage with efficient data structures

## When to Use Caffeine Caching

Choose Caffeine when you need:

- **High-Performance Caching**: Sub-millisecond access with millions of operations per second
- **Optimal Hit Rates**: Advanced algorithms for maximum cache efficiency
- **Memory-Bounded Caching**: Automatic size limits to prevent memory exhaustion
- **Time-Sensitive Data**: TTL and TTI for automatic data expiration
- **Concurrent Access**: Thread-safe operations in multi-threaded applications
- **Detailed Metrics**: Comprehensive statistics for monitoring and optimization
- **Single Instance**: Local caching where data doesn't need to be shared across instances

## Creating Cache Interfaces

The `CaffeineCache` interface is Kora's abstraction over Caffeine's high-performance caching capabilities. By extending `CaffeineCache<KeyType, ValueType>`, your interface inherits powerful caching methods while benefiting from Kora's dependency injection and configuration management.

**Key Benefits of CaffeineCache**:
- **Type Safety**: Generic interface ensures compile-time type checking for keys and values
- **Automatic Implementation**: Kora generates the actual cache implementation at compile-time
- **Configuration Integration**: Seamlessly integrates with Kora's HOCON configuration system
- **Performance Optimized**: Leverages Caffeine's advanced algorithms for optimal performance
- **Memory Management**: Automatic size limits and eviction policies prevent memory leaks

**Core Methods Provided**:
- `Optional<V> get(K key)` - Retrieves a value from cache, returns empty if not present
- `V getOrDefault(K key, V defaultValue)` - Gets value or returns default if missing
- `void put(K key, V value)` - Stores a key-value pair in the cache
- `boolean invalidate(K key)` - Removes a specific entry from the cache
- `void invalidateAll()` - Clears all entries from the cache
- `long size()` - Returns current number of entries in the cache

**Configuration via @Cache Annotation**:
The `@Cache` annotation specifies the configuration key prefix for this cache instance. Kora will look for configuration properties under this key to customize cache behavior (TTL, size limits, etc.).

Create a cache interface for your user data:

===! ":fontawesome-brands-java: Java"

    Create `src/main/java/ru/tinkoff/kora/example/cache/UserCaffeineCache.java`:

    ```java
    package ru.tinkoff.kora.example.cache;

    import ru.tinkoff.kora.cache.annotation.Cache;
    import ru.tinkoff.kora.cache.caffeine.CaffeineCache;

    @Cache("cache.caffeine.users")
    public interface UserCaffeineCache extends CaffeineCache<String, UserResponse> {
    }
    ```

=== ":simple-kotlin: Kotlin"

    Create `src/main/kotlin/ru/tinkoff/kora/example/cache/UserCaffeineCache.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.cache

    import ru.tinkoff.kora.cache.annotation.Cache
    import ru.tinkoff.kora.cache.caffeine.CaffeineCache

    @Cache("cache.caffeine.users")
    interface UserCaffeineCache : CaffeineCache<String, UserResponse>
    ```

## Creating a Cached Service

!!! note "Using Existing Database Service"

    If you're following this guide after completing the [Database Integration guide](../database-integration.md), you can enhance your existing `UserService` with caching instead of creating a new one. Simply add the cache annotations to your existing service methods and inject the cache interface. This approach uses real database operations instead of the simulated latency shown below.

**Classes annotated with cache annotations cannot be declared as `final`**. Kora uses Aspect-Oriented Programming (AOP) to inject caching behavior at compile-time by creating subclasses of your service classes. The `final` modifier prevents subclassing, which would break AOP functionality. This applies to all AOP features in Kora, not just caching.

Create a service that uses caching:

===! ":fontawesome-brands-java: Java"

    Create `src/main/java/ru/tinkoff/kora/example/UserService.java`:

    ```java
    package ru.tinkoff.kora.example;

    import ru.tinkoff.kora.cache.annotation.CacheInvalidate;
    import ru.tinkoff.kora.cache.annotation.CachePut;
    import ru.tinkoff.kora.cache.annotation.Cacheable;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.example.cache.UserCaffeineCache;

    import java.time.LocalDateTime;
    import java.util.Optional;

    @Component
    public class UserService {

        private final UserCaffeineCache userCache;

        public UserService(UserCaffeineCache userCache) {
            this.userCache = userCache;
        }

        record UserRequest(String name, String email) {}
        record UserResponse(String id, String name, String email, LocalDateTime createdAt) {}

        @Cacheable(UserCaffeineCache.class)
        public Optional<UserResponse> findById(String id) {
            // Simulate expensive database operation
            try {
                Thread.sleep(100); // Simulate database latency
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
            return Optional.empty(); // In real app, this would query database
        }

        @CachePut(value = UserCaffeineCache.class, parameters = "user.id()")
        public UserResponse save(UserResponse user) {
            // Simulate database save operation
            try {
                Thread.sleep(50); // Simulate database latency
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
            return user;
        }

        @CacheInvalidate(UserCaffeineCache.class)
        public void deleteById(String id) {
            // Simulate database delete operation
            try {
                Thread.sleep(30); // Simulate database latency
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    Create `src/main/kotlin/ru/tinkoff/kora/example/UserService.kt`:

    ```kotlin
    package ru.tinkoff.kora.example

    import ru.tinkoff.kora.cache.annotation.CacheInvalidate
    import ru.tinkoff.kora.cache.annotation.CachePut
    import ru.tinkoff.kora.cache.annotation.Cacheable
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.example.cache.UserCaffeineCache

    import java.time.LocalDateTime

    @Component
    class UserService(
        private val userCache: UserCaffeineCache
    ) {

        data class UserRequest(val name: String, val email: String)
        data class UserResponse(val id: String, val name: String, val email: String, val createdAt: LocalDateTime)

        @Cacheable(UserCaffeineCache::class)
        fun findById(id: String): UserResponse? {
            // Simulate expensive database operation
            Thread.sleep(100) // Simulate database latency
            return null // In real app, this would query database
        }

        @CachePut(value = UserCaffeineCache::class, parameters = ["user.id"])
        fun save(user: UserResponse): UserResponse {
            // Simulate database save operation
            Thread.sleep(50) // Simulate database latency
            return user
        }

        @CacheInvalidate(UserCaffeineCache::class)
        fun deleteById(id: String) {
            // Simulate database delete operation
            Thread.sleep(30) // Simulate database latency
        }
    }
    ```

!!! tip "Verify AOP Code Generation"

    Kora uses compile-time Aspect-Oriented Programming (AOP) to generate cache implementations. After creating your cached service:

    1. **Compile the project**: Run `./gradlew classes` to trigger code generation
    2. **Navigate to generated classes**: In your IDE, navigate to the compiled `UserService` class
    3. **Check AOP application**: Look for the generated child class (usually `UserService$$CacheAop`) that contains the caching logic

## Updating Your Controller

Update your existing controller to use the cached service:

===! ":fontawesome-brands-java: Java"

    Update `src/main/java/ru/tinkoff/kora/example/UserController.java`:

    ```java
    package ru.tinkoff.kora.example;

    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.http.common.HttpMethod;
    import ru.tinkoff.kora.http.server.common.annotation.HttpController;
    import ru.tinkoff.kora.http.server.common.annotation.HttpRoute;
    import ru.tinkoff.kora.json.common.annotation.Json;
    import ru.tinkoff.kora.validation.common.annotation.Valid;

    import java.time.LocalDateTime;
    import java.util.Optional;
    import java.util.concurrent.atomic.AtomicLong;

    @Component
    @HttpController
    public final class UserController {

        private final UserService userService;
        private final AtomicLong idGenerator = new AtomicLong(1);

        public UserController(UserService userService) {
            this.userService = userService;
        }

        record UserRequest(@Valid String name, @Valid String email) {}
        record UserResponse(String id, String name, String email, LocalDateTime createdAt) {}

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        public UserResponse createUser(@Valid UserRequest request) {
            var id = String.valueOf(idGenerator.getAndIncrement());
            var user = new UserResponse(id, request.name(), request.email(), LocalDateTime.now());
            return userService.save(user);
        }

        @HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
        @Json
        public Optional<UserResponse> getUser(String id) {
            return userService.findById(id);
        }

        @HttpRoute(method = HttpMethod.DELETE, path = "/users/{id}")
        public void deleteUser(String id) {
            userService.deleteById(id);
        }
    }
    ```

=== ":simple-kotlin: Kotlin"

    Update `src/main/kotlin/ru/tinkoff/kora/example/UserController.kt`:

    ```kotlin
    package ru.tinkoff.kora.example

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.http.common.HttpMethod
    import ru.tinkoff.kora.http.server.common.annotation.HttpController
    import ru.tinkoff.kora.http.server.common.annotation.HttpRoute
    import ru.tinkoff.kora.json.common.annotation.Json
    import ru.tinkoff.kora.validation.common.annotation.Valid

    import java.time.LocalDateTime
    import java.util.concurrent.atomic.AtomicLong

    @Component
    @HttpController
    class UserController(
        private val userService: UserService
    ) {

        private val idGenerator = AtomicLong(1)

        data class UserRequest(@Valid val name: String, @Valid val email: String)
        data class UserResponse(val id: String, val name: String, val email: String, val createdAt: LocalDateTime)

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        fun createUser(@Valid request: UserRequest): UserResponse {
            val id = idGenerator.getAndIncrement().toString()
            val user = UserResponse(id, request.name, request.email, LocalDateTime.now())
            return userService.save(user)
        }

        @HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
        @Json
        fun getUser(id: String): UserResponse? {
            return userService.findById(id)
        }

        @HttpRoute(method = HttpMethod.DELETE, path = "/users/{id}")
        fun deleteUser(id: String) {
            userService.deleteById(id)
        }
    }
    ```

## Configuration

Create or update your `application.conf` for cache configuration:

```hocon
# Caffeine Cache Configuration
cache.caffeine.users {
  maximumSize = 1000
  expireAfterWrite = 10m
}
```

## Running the Application

```bash
./gradlew run
```

## Testing Cache Performance

Test the caching performance by making repeated requests:

### Create a User

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com"}'
```

**Expected Response:**
```json
{
  "id": "1",
  "name": "John Doe",
  "email": "john@example.com",
  "createdAt": "2025-09-27T10:30:00"
}
```

### First Request (Cache Miss - ~100ms)

```bash
time curl http://localhost:8080/users/1
```

### Second Request (Cache Hit - ~1ms)

```bash
time curl http://localhost:8080/users/1
```

### Delete User (Invalidates Cache)

```bash
curl -X DELETE http://localhost:8080/users/1
```

### Next Request (Cache Miss Again - ~100ms)

```bash
time curl http://localhost:8080/users/1
```

## Key Concepts Learned

### Cache Types
- **Caffeine**: High-performance in-memory caching with excellent features and performance
- **Local Caching**: Perfect for single-instance applications or when data consistency isn't critical across instances

### Cache Annotations
- **`@Cacheable`**: Cache method results for given parameters
- **`@CachePut`**: Update cache with method result
- **`@CacheInvalidate`**: Remove entries from cache
- **`invalidateAll`**: Clear entire cache contents

### Cache Configuration
- **TTL (Time To Live)**: Automatic expiration of cache entries
- **Size Limits**: Maximum number of entries to prevent memory issues
- **Key Mapping**: Custom strategies for generating cache keys

### Performance Benefits
- **Reduced Latency**: Sub-millisecond cache hits vs database queries
- **Lower Load**: Fewer database requests under high traffic
- **Scalability**: Better resource utilization and response times

## What's Next?

- [Add Multi-Level Caching with Redis](../multi-level-caching-redis.md)
- [Add API Documentation](../api-documentation.md)
- [Implement Security](../openapi-security.md)
- [Advanced Testing Strategies](../testing-strategies.md)

## Help

If you encounter issues:

- Check the [Cache Module Documentation](../../documentation/cache.md)
- Check the [Caffeine Cache Documentation](../../documentation/cache.md#caffeine)
- Check the [Caffeine Cache Example](https://github.com/kora-projects/kora-examples/tree/master/kora-java-cache-caffeine)
- Ask questions on [GitHub Discussions](https://github.com/kora-projects/kora/discussions)

## Troubleshooting

### Cache Not Working
- Ensure `CaffeineCacheModule` is included in Application interface
- Verify `@Cache` annotation on cache interfaces
- Check cache configuration in `application.conf`

### Performance Issues
- Monitor cache hit/miss ratios
- Adjust TTL and size limits based on usage patterns
- Consider cache key optimization for better hit rates

### Memory Usage
- Configure appropriate maximum cache sizes
- Monitor cache metrics and adjust as needed
- Use appropriate expiration policies to prevent memory leaks