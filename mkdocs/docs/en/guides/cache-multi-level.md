---
title: Multi-Level Caching with Redis
summary: Learn how to add Redis as a second cache layer to your existing Caffeine-cached Kora applications
tags: caching, redis, caffeine, multi-level, distributed, performance
---

# Multi-Level Caching with Redis

This comprehensive guide demonstrates how to implement high-performance multi-level caching using Redis as a distributed second-level cache alongside your existing Caffeine in-memory cache. You'll learn to build scalable, fault-tolerant caching architectures that can handle millions of requests per second across multiple application instances.

## What is Redis?

**Redis (Remote Dictionary Server)** is an open-source, in-memory data structure store that can be used as a database, cache, and message broker. Originally developed by Salvatore Sanfilippo in 2009, Redis has become the most popular key-value store and is widely adopted for caching, session management, real-time analytics, and pub/sub messaging in enterprise applications.

### Core Redis Concepts

- **In-Memory Storage**: All data is stored in RAM for ultra-fast access (microsecond latency)
- **Data Structures**: Supports strings, hashes, lists, sets, sorted sets, bitmaps, hyperloglogs, and geospatial indexes
- **Persistence Options**: RDB snapshots and AOF (Append Only File) for data durability
- **Replication**: Master-slave replication for high availability and read scaling
- **Clustering**: Automatic sharding and failover across multiple nodes
- **Pub/Sub**: Built-in publish/subscribe messaging capabilities

### Key Capabilities for Caching

- **Sub-millisecond Latency**: In-memory operations provide consistent low-latency access
- **High Throughput**: Can handle hundreds of thousands of operations per second
- **Data Persistence**: Optional disk persistence ensures cache survival across restarts
- **TTL Support**: Automatic key expiration prevents memory leaks and stale data
- **Atomic Operations**: Single-threaded execution ensures data consistency
- **Rich Data Types**: Beyond simple key-value, supports complex data structures
- **Distributed**: Clustering enables horizontal scaling across multiple servers

## Why Multi-Level Caching with Redis?

**Traditional single-level caching** has significant limitations in distributed systems:

- **No Instance Sharing**: Each application instance maintains its own cache
- **Memory Waste**: Same data cached redundantly across all instances
- **Cache Invalidation Issues**: Updates in one instance don't invalidate caches in others
- **Limited Scalability**: Cache size limited by individual instance memory
- **No Persistence**: Cache loss on application restart or deployment

**Multi-level caching with Redis** solves these problems:

- **Distributed Cache Sharing**: All instances share the same Redis cache
- **Memory Efficiency**: Eliminates redundant caching across instances
- **Automatic Synchronization**: Cache updates propagate across all instances
- **Horizontal Scalability**: Redis clustering enables virtually unlimited cache capacity
- **Data Persistence**: Cache survives application restarts and deployments
- **Fault Tolerance**: Redis replication ensures cache availability during failures

## Redis as L2 Cache Architecture

In a multi-level caching architecture:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Application   │───►│   L1 Caffeine   │───►│   L2 Redis      │───►│    Database     │
│     Instance    │    │   (Local)       │    │   (Distributed) │    │    (Source)     │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • Business      │    │ • Sub-ms access │    │ • 1-5ms access  │    │ • 10-100ms+     │
│   Logic         │    │ • Instance-local│    │ • Shared across │    │ • Persistent    │
│ • API Calls     │    │ • Limited size  │    │ • All instances │    │ • Authoritative │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │                       │
         │                       │                       │                       │
         └───────────────────────┼───────────────────────┼───────────────────────┘
                                 │                       │
                                 └───────────────────────┘
                                         Cache Updates
```

### Cache Lookup Flow

1. **Check L1 (Caffeine)**: Ultra-fast in-memory lookup (microseconds)
2. **Check L2 (Redis)**: Network call to distributed cache (milliseconds)
3. **Database Query**: Expensive operation if not in either cache (10-100ms+)
4. **Populate Both Caches**: Store result in both L1 and L2 for future requests

### Cache Update Flow

1. **Update Database**: Write changes to primary data store
2. **Update Both Caches**: Simultaneously update L1 and L2 caches
3. **Invalidate if Needed**: Clear stale data from both cache layers

## When to Use Multi-Level Caching

Choose Redis multi-level caching when you need:

- **Multiple Application Instances**: More than one instance of your application running
- **High Read Throughput**: Thousands of cache reads per second across instances
- **Data Consistency**: Cache updates must be visible across all application instances
- **Fault Tolerance**: Cache should survive application restarts and deployments
- **Scalability**: Application may need to scale beyond single-instance limits
- **Complex Data Relationships**: Need to cache related data structures efficiently

## Redis vs Other Distributed Caches

| Feature | Redis | Memcached | Hazelcast | Apache Ignite |
|---------|-------|-----------|-----------|----------------|
| Data Types | Rich (10+ types) | Simple (strings only) | Rich | Rich |
| Persistence | Yes (RDB/AOF) | No | Yes | Yes |
| Clustering | Yes | Basic | Yes | Yes |
| Pub/Sub | Yes | No | Yes | Yes |
| Transactions | Yes | No | Yes | Yes |
| Performance | Excellent | Excellent | Good | Good |

Redis excels in simplicity, performance, and feature richness while maintaining operational simplicity.

This guide will transform your single-instance Caffeine cache into a robust, distributed multi-level caching system capable of supporting high-traffic, multi-instance deployments.

## What You'll Build

You'll enhance your existing cached API with:

- **Two-level caching**: Caffeine (L1) + Redis (L2) for optimal performance
- **Distributed cache sharing**: Redis enables cache sharing across multiple application instances
- **Cache synchronization**: Automatic cache updates across both layers
- **Redis configuration**: Docker Compose setup and connection configuration
- **Fallback strategies**: Graceful degradation when Redis is unavailable

## What You'll Need

- JDK 17 or later
- Gradle 7.0+
- A text editor or IDE
- Docker and Docker Compose
- Completed [Caching Strategies](../cache.md) guide

## Prerequisites

!!! note "Required: Complete Basic Caching Setup"

    This guide assumes you have completed the **[Caching Strategies](../cache.md)** guide and have a working Kora application with Caffeine caching.

    If you haven't completed the basic caching guide yet, please do so first as this guide builds upon that foundation.

## Add Dependencies

Add the Redis caching dependency to your existing `build.gradle` or `build.gradle.kts`:

===! ":fontawesome-brands-java: `Java`"

    Add to the `dependencies` block in `build.gradle`:

    ```groovy
    dependencies {
        // ... existing dependencies ...

        // Add Redis for distributed caching
        implementation("ru.tinkoff.kora:cache-redis")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Add to the `dependencies` block in `build.gradle.kts`:

    ```kotlin
    dependencies {
        // ... existing dependencies ...

        // Add Redis for distributed caching
        implementation("ru.tinkoff.kora:cache-redis")
    }
    ```

## Updating Your Application

Update your existing `Application.java` or `Application.kt` to include the `RedisCacheModule`:

===! ":fontawesome-brands-java: Java"

    Update `src/main/java/ru/tinkoff/kora/example/Application.java`:

    ```java
    package ru.tinkoff.kora.example;

    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule;
    import ru.tinkoff.kora.json.module.JsonModule;
    import ru.tinkoff.kora.validation.module.ValidationModule;
    import ru.tinkoff.kora.cache.caffeine.CaffeineCacheModule;
    import ru.tinkoff.kora.cache.redis.RedisCacheModule;

    @KoraApp
    public interface Application extends
            UndertowHttpServerModule,
            JsonModule,
            ValidationModule,
            CaffeineCacheModule,
            RedisCacheModule {  // Add Redis for distributed caching
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
    import ru.tinkoff.kora.cache.redis.RedisCacheModule

    @KoraApp
    interface Application :
        UndertowHttpServerModule,
        JsonModule,
        ValidationModule,
        CaffeineCacheModule,
        RedisCacheModule  // Add Redis for distributed caching
    ```

## Creating Redis Cache Interfaces

Create Redis cache interfaces for distributed caching (L2):

===! ":fontawesome-brands-java: Java"

    Create `src/main/java/ru/tinkoff/kora/example/cache/UserRedisCache.java`:

    ```java
    package ru.tinkoff.kora.example.cache;

    import ru.tinkoff.kora.cache.annotation.Cache;
    import ru.tinkoff.kora.cache.redis.RedisCache;

    @Cache("cache.redis.users")
    public interface UserRedisCache extends RedisCache<String, UserResponse> {
    }
    ```

=== ":simple-kotlin: Kotlin"

    Create `src/main/kotlin/ru/tinkoff/kora/example/cache/UserRedisCache.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.cache

    import ru.tinkoff.kora.cache.annotation.Cache
    import ru.tinkoff.kora.cache.redis.RedisCache

    @Cache("cache.redis.users")
    interface UserRedisCache : RedisCache<String, UserResponse>
    ```

## Updating Your Service

Update your existing `UserService` to implement two-level caching:

===! ":fontawesome-brands-java: Java"

    Update `src/main/java/ru/tinkoff/kora/example/UserService.java`:

    ```java
    package ru.tinkoff.kora.example;

    import ru.tinkoff.kora.cache.annotation.CacheInvalidate;
    import ru.tinkoff.kora.cache.annotation.CachePut;
    import ru.tinkoff.kora.cache.annotation.Cacheable;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.example.cache.UserCaffeineCache;
    import ru.tinkoff.kora.example.cache.UserRedisCache;

    import java.time.LocalDateTime;
    import java.util.Optional;

    @Component
    public final class UserService {

        private final UserCaffeineCache caffeineCache;
        private final UserRedisCache redisCache;

        public UserService(UserCaffeineCache caffeineCache, UserRedisCache redisCache) {
            this.caffeineCache = caffeineCache;
            this.redisCache = redisCache;
        }

        record UserRequest(String name, String email) {}
        record UserResponse(String id, String name, String email, LocalDateTime createdAt) {}

        @Cacheable(UserCaffeineCache.class)  // L1: Caffeine cache (checked first)
        @Cacheable(UserRedisCache.class)   // L2: Redis cache (checked second)
        public Optional<UserResponse> findById(String id) {
            // Simulate expensive database operation
            try {
                Thread.sleep(100); // Simulate database latency
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }

            // In real app, this would query database
            return Optional.empty();
        }

        @CachePut(value = UserCaffeineCache.class, parameters = "user.id()")  // Update L1 cache
        @CachePut(value = UserRedisCache.class, parameters = "user.id()")   // Update L2 cache
        public UserResponse save(UserResponse user) {
            // Simulate database save operation
            try {
                Thread.sleep(50); // Simulate database latency
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
            return user;
        }

        @CacheInvalidate(UserCaffeineCache.class)  // Invalidate L1 cache
        @CacheInvalidate(UserRedisCache.class)   // Invalidate L2 cache
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

    Update `src/main/kotlin/ru/tinkoff/kora/example/UserService.kt`:

    ```kotlin
    package ru.tinkoff.kora.example

    import ru.tinkoff.kora.cache.annotation.CacheInvalidate
    import ru.tinkoff.kora.cache.annotation.CachePut
    import ru.tinkoff.kora.cache.annotation.Cacheable
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.example.cache.UserCaffeineCache
    import ru.tinkoff.kora.example.cache.UserRedisCache

    import java.time.LocalDateTime

    @Component
    class UserService(
        private val caffeineCache: UserCaffeineCache,
        private val redisCache: UserRedisCache
    ) {

        data class UserRequest(val name: String, val email: String)
        data class UserResponse(val id: String, val name: String, val email: String, val createdAt: LocalDateTime)

        @Cacheable(UserCaffeineCache::class)  // L1: Caffeine cache (checked first)
        @Cacheable(UserRedisCache::class)   // L2: Redis cache (checked second)
        fun findById(id: String): UserResponse? {
            // Simulate expensive database operation
            Thread.sleep(100) // Simulate database latency

            // In real app, this would query database
            return null
        }

        @CachePut(value = UserCaffeineCache::class, parameters = ["user.id"])  // Update L1 cache
        @CachePut(value = UserRedisCache::class, parameters = ["user.id"])   // Update L2 cache
        fun save(user: UserResponse): UserResponse {
            // Simulate database save operation
            Thread.sleep(50) // Simulate database latency
            return user
        }

        @CacheInvalidate(UserCaffeineCache::class)  // Invalidate L1 cache
        @CacheInvalidate(UserRedisCache::class)   // Invalidate L2 cache
        fun deleteById(id: String) {
            // Simulate database delete operation
            Thread.sleep(30) // Simulate database latency
        }
    }
    ```

## Configuration

Update your `application.conf` to configure both cache layers:

```hocon
# Caffeine Cache Configuration (L1)
cache.caffeine.users {
  maximumSize = 1000
  expireAfterWrite = 10m
}

# Redis Cache Configuration (L2)
cache.redis.users {
  expireAfterWrite = 30m
}

# Redis Connection
lettuce {
  uri = "redis://localhost:6379"
  database = 0
  commandTimeout = 2000ms
}
```

## Redis Setup

Before running the application, set up Redis using Docker Compose:

### Create docker-compose.yml

Create `docker-compose.yml` in your project root:

```yaml
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

volumes:
  redis_data:
```

### Start Redis

```bash
docker-compose up -d redis
```

### Verify Redis is Running

```bash
docker-compose ps
```

You should see the Redis container running and healthy.

## Running the Application

```bash
./gradlew run
```

## Testing Multi-Level Caching

Test the two-level caching behavior:

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

### Second Request (L1 Cache Hit - ~1ms)

```bash
time curl http://localhost:8080/users/1
```

### Stop and Restart Application

Stop the application, then restart it:

```bash
# Stop with Ctrl+C, then restart
./gradlew run
```

### Third Request (L2 Cache Hit - ~5ms)

```bash
time curl http://localhost:8080/users/1
```

### Delete User (Invalidates Both Caches)

```bash
curl -X DELETE http://localhost:8080/users/1
```

### Next Request (Complete Cache Miss - ~100ms)

```bash
time curl http://localhost:8080/users/1
```

## Testing Cache Distribution

To test distributed caching, run multiple application instances:

### Terminal 1 - Start First Instance

```bash
./gradlew run
```

### Terminal 2 - Start Second Instance

```bash
# In another terminal
./gradlew run
```

### Create User in Instance 1

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Jane Doe", "email": "jane@example.com"}'
```

### Retrieve User from Instance 2

```bash
# This should hit Redis cache even though created in Instance 1
curl http://localhost:8080/users/2
```

## Key Concepts Learned

### Multi-Level Caching Strategy
- **L1 (Caffeine)**: Ultra-fast in-memory cache for frequently accessed data
- **L2 (Redis)**: Distributed cache for sharing data across application instances
- **Cache Hierarchy**: L1 checked first, then L2, then database
- **Write-Through**: Updates go to both cache layers and database

### Cache Synchronization
- **Multiple Annotations**: Use multiple `@Cacheable`, `@CachePut`, and `@CacheInvalidate` annotations
- **Automatic Updates**: Cache annotations handle synchronization across both layers automatically
- **Invalidation Cascade**: Deleting from one layer invalidates all layers
- **Consistency**: Both layers stay synchronized through annotation-based cache management

### Performance Benefits
- **Optimal Speed**: L1 provides sub-millisecond access for hot data
- **Scalability**: L2 enables horizontal scaling across multiple instances
- **Fault Tolerance**: Application continues working if Redis is temporarily unavailable
- **Memory Efficiency**: L1 reduces Redis load for frequently accessed data

### Distributed Caching Patterns
- **Cache Warming**: Pre-populate caches on application startup
- **Cache Partitioning**: Use different Redis databases for different data types
- **TTL Strategies**: Different expiration times for different cache layers
- **Monitoring**: Track hit rates and performance for both cache layers

## What's Next?

- [Add API Documentation](../api-documentation.md)
- [Implement Security](../openapi-security.md)
- [Advanced Testing Strategies](../testing-strategies.md)

## Help

If you encounter issues:

- Check the [Cache Module Documentation](../../documentation/cache.md)
- Check the [Redis Cache Documentation](../../documentation/cache.md#redis)
- Ensure Redis is running: `docker-compose ps`
- Check Redis logs: `docker-compose logs redis`
- Check the [Redis Cache Example](https://github.com/kora-projects/kora-examples/tree/master/kora-java-cache-redis)
- Ask questions on [GitHub Discussions](https://github.com/kora-projects/kora/discussions)

## Troubleshooting

### Redis Connection Issues
- Verify Redis container is running: `docker-compose ps`
- Check Redis logs: `docker-compose logs redis`
- Test Redis connection: `docker exec -it <container_id> redis-cli ping`
- Verify `application.conf` Redis configuration

### Cache Not Working
- Ensure both `CaffeineCacheModule` and `RedisCacheModule` are included
- Verify `@Cache` annotations on cache interfaces
- Check cache configuration in `application.conf`

### Performance Issues
- Monitor both L1 and L2 cache hit rates
- Adjust TTL settings based on data access patterns
- Consider cache key optimization for better distribution

### Memory Usage
- Configure appropriate maximum sizes for both cache layers
- Monitor Redis memory usage: `docker stats`
- Use Redis persistence for cache durability if needed

### Distributed Cache Issues
- Ensure all instances connect to the same Redis server
- Check network connectivity between application instances and Redis
- Verify cache invalidation is working across instances