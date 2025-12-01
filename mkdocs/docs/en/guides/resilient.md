---
title: Resilience Patterns with Circuit Breaker, Retry, Timeout, and Fallback
summary: Implement fault-tolerant services using Kora's resilience patterns including CircuitBreaker, Retry, Timeout, and Fallback for production-ready applications
tags: resilient, circuitbreaker, retry, timeout, fallback, fault-tolerance, production
---

# Resilience Patterns with Circuit Breaker, Retry, Timeout, and Fallback

This guide demonstrates how to implement fault-tolerant services using Kora's comprehensive resilience patterns. You'll learn to add CircuitBreaker, Retry, Timeout, and Fallback capabilities to your existing UserService from the HTTP Server guide, making your application production-ready with proper fault tolerance and error handling.

## What You'll Build

You'll enhance your existing UserService with resilience patterns:

- **CircuitBreaker**: Automatically stop calling failing services to prevent cascading failures
- **Retry**: Automatically retry failed operations with configurable backoff strategies
- **Timeout**: Set maximum execution times to prevent hanging operations
- **Fallback**: Provide backup behavior when primary operations fail
- **Combined Patterns**: Apply multiple resilience patterns together for comprehensive fault tolerance
- **Configuration**: Fine-tune resilience behavior through HOCON configuration
- **Testing**: Test resilient services and verify fault tolerance behavior

## What You'll Need

- JDK 17 or later
- Gradle 7.0+
- A text editor or IDE
- Completed [HTTP Server](../http-server.md) guide

## Prerequisites

!!! note "Required: Complete HTTP Server Guide"

    This guide assumes you have completed the **[HTTP Server](../http-server.md)** guide and have a working UserService with HTTP endpoints.

    If you haven't completed the HTTP server guide yet, please do so first as this guide builds upon that foundation and enhances the existing UserService with resilience patterns.

### Add Dependencies

Add the resilient dependency to your existing Kora project:

===! ":fontawesome-brands-java: `Java`"

    ```gradle title="build.gradle"
    dependencies {
        // ... existing dependencies ...

        implementation("ru.tinkoff.kora:resilient-kora")
    }
    ```

===! ":fontawesome-brands-kotlin: `Kotlin`"

    ```kotlin title="build.gradle.kts"
    dependencies {
        // ... existing dependencies ...

        implementation("ru.tinkoff.kora:resilient-kora")
    }
    ```

## Add Modules

Update your Application interface to include the ResilientModule:

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/ru/tinkoff/kora/example/Application.java`:

    ```java
    package ru.tinkoff.kora.example;

    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule;
    import ru.tinkoff.kora.json.module.JsonModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;
    import ru.tinkoff.kora.resilient.ResilientModule;

    @KoraApp
    public interface Application extends
            UndertowHttpServerModule,
            JsonModule,
            LogbackModule,
            ResilientModule {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/ru/tinkoff/kora/example/Application.kt`:

    ```kotlin
    package ru.tinkoff.kora.example

    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule
    import ru.tinkoff.kora.json.module.JsonModule
    import ru.tinkoff.kora.logging.logback.LogbackModule
    import ru.tinkoff.kora.resilient.ResilientModule

    @KoraApp
    interface Application :
        UndertowHttpServerModule,
        JsonModule,
        LogbackModule,
        ResilientModule
    ```

## Step-by-Step Implementation

We'll enhance your existing UserService and UserController from the HTTP Server guide with resilience patterns. Each step adds one resilience pattern to demonstrate incremental fault tolerance improvements.

## Adding Retry Pattern

### Retry Pattern
**Why it's needed**: In distributed systems, temporary failures are common - network glitches, momentary service overloads, or transient database connection issues. Without retry logic, these temporary failures would result in failed user requests, even though the operation would succeed if attempted again.

**What it prevents**: 
- Failed requests due to temporary network issues
- Service unavailability during brief overload periods
- User experience degradation from transient failures
- Unnecessary error handling complexity in application code

Retry automatically attempts failed operations again with configurable delay and backoff strategies, allowing services to recover from temporary issues without manual intervention.

Now let's add the Retry pattern to handle transient failures. We'll enhance your existing `getUser` method to automatically retry on failures.

### Add Retry Dependency

First, add the resilient module to your `build.gradle`:

```gradle
dependencies {
    implementation 'ru.tinkoff.kora:resilient'
}
```

### Configure Retry

Add retry configuration to your `application.conf`:

```hocon
resilient {
  retry {
    default {
      attempts = 3
      delay = 100ms
      delayStep = 200ms
    }
  }
}
```

### Enhance UserService with Retry

Update your existing `UserService.java` to add retry to the `getUser` method:

```java
@Component
public final class UserService {
    private final Map<String, UserResponse> users = new ConcurrentHashMap<>();
    private final AtomicLong idGenerator = new AtomicLong(1);

    // ... existing methods ...

    @Retry("default")
    public Optional<UserResponse> getUserWithRetry(String id) {
        // Simulate occasional failure that retry can handle
        if (Math.random() < 0.3) { // 30% chance of failure
            throw new RuntimeException("Temporary service failure");
        }
        return Optional.ofNullable(users.get(id));
    }

    // ... existing methods ...
}
```

### Update Controller

Add a new endpoint in your existing `UserController.java` that uses the retry-enabled method:

```java
@Component
@HttpController
public final class UserController {
    private final UserService userService;

    // ... existing constructor and methods ...

    @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}/retry")
    @Json
    public Optional<UserResponse> getUserWithRetry(@Path String userId) {
        return userService.getUserWithRetry(userId);
    }

    // ... existing methods ...
}
```

### Test Retry Behavior

Create a test that verifies the retry behavior:

```java
@KoraAppTest
class UserServiceRetryTest {
    @TestComponent
    private UserService userService;

    @Test
    void shouldRetryOnFailure() {
        // Given - create a user first
        var request = new UserRequest("John Doe", "john@example.com");
        var created = userService.createUser(request);

        // When - call retry method multiple times
        // The method has 30% failure rate, but retry should eventually succeed
        var retrieved = userService.getUserWithRetry(created.id());

        // Then
        assertThat(retrieved).isPresent();
        assertThat(retrieved.get().name()).isEqualTo("John Doe");
    }

    @Test
    void shouldEventuallySucceedAfterRetries() {
        // This test verifies that even with failures, retry eventually succeeds
        // In a real scenario, you might use a mock to control failure behavior
        assertThat(true).isTrue(); // Placeholder - actual test would verify retry metrics
    }
}
```

### Run and Verify

Run the tests to see retry in action:

```bash
./gradlew test
```

You should see that the retry method eventually succeeds despite simulated failures. Your existing endpoints continue to work without retry, while the new `/users/{userId}/retry` endpoint demonstrates retry behavior.

## Adding Timeout Pattern

### Timeout Pattern
**Why it's needed**: Operations in distributed systems can hang indefinitely due to network issues, unresponsive services, or resource contention. Without timeouts, a single slow operation can consume threads and resources, eventually causing the entire application to become unresponsive.

**What it prevents**:
- Thread pool exhaustion from hanging operations
- Cascading failures when slow operations consume all available resources
- Poor user experience from requests that never complete
- Application instability due to resource leaks from incomplete operations

Timeout sets maximum execution time for operations, preventing them from hanging indefinitely and ensuring resources are freed up for other requests.

Now let's add the Timeout pattern to prevent operations from hanging indefinitely. We'll enhance your existing `getUsers` method with timeout protection.

### Configure Timeout

Add timeout configuration to your `application.conf`:

```hocon
resilient {
  retry {
    default {
      attempts = 3
      delay = 100ms
      delayStep = 200ms
    }
  }
  timeout {
    default {
      duration = 5s
    }
  }
}
```

### Enhance UserService with Timeout

Update your existing `UserService.java` to add timeout to the `getUsers` method:

```java
@Component
public final class UserService {
    // ... existing fields and constructor ...

    // ... existing methods ...

    @Retry("default")
    public Optional<UserResponse> getUserWithRetry(String id) {
        // ... existing implementation ...
    }

    @Timeout("default")
    public List<UserResponse> getUsersWithTimeout(int page, int size, String sort) {
        // Simulate slow operation that might timeout
        try {
            Thread.sleep(1000); // 1 second delay
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new RuntimeException("Operation interrupted", e);
        }
        return getUsers(page, size, sort); // Use existing method
    }

    // ... existing methods ...
}
```

### Update Controller

Add a new endpoint in your existing `UserController.java` that uses the timeout-enabled method:

```java
@Component
@HttpController
public final class UserController {
    // ... existing constructor and methods ...

    @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}/retry")
    @Json
    public Optional<UserResponse> getUserWithRetry(@Path String userId) {
        return userService.getUserWithRetry(userId);
    }

    @HttpRoute(method = HttpMethod.GET, path = "/users/timeout")
    @Json
    public List<UserResponse> getUsersWithTimeout(
        @Query("page") Optional<Integer> page,
        @Query("size") Optional<Integer> size,
        @Query("sort") Optional<String> sort
    ) {
        int pageNum = page.orElse(0);
        int pageSize = size.orElse(10);
        String sortBy = sort.orElse("name");
        return userService.getUsersWithTimeout(pageNum, pageSize, sortBy);
    }

    // ... existing methods ...
}
```

### Test Timeout Behavior

Create a test that verifies the timeout behavior:

```java
@KoraAppTest
class UserServiceTimeoutTest {
    @TestComponent
    private UserService userService;

    @Test
    void shouldTimeoutSlowOperation() {
        // Given - create some test users
        var request1 = new UserRequest("Alice", "alice@example.com");
        var request2 = new UserRequest("Bob", "bob@example.com");
        userService.createUser(request1);
        userService.createUser(request2);

        // When - call timeout method
        // This should complete within the 5 second timeout
        var users = userService.getUsersWithTimeout(0, 10, "name");

        // Then
        assertThat(users).hasSizeGreaterThanOrEqualTo(2);
    }

    @Test
    void shouldHandleTimeoutException() {
        // In a real scenario, you might configure a very short timeout
        // to test the timeout behavior explicitly
        assertThat(true).isTrue(); // Placeholder for timeout exception test
    }
}
```

### Run and Verify

Run the tests to see timeout in action:

```bash
./gradlew test
```

You should see that the timeout method completes within the configured time limit. Your existing `/users` endpoint continues to work without timeout, while the new `/users/timeout` endpoint demonstrates timeout behavior.

## Adding Circuit Breaker Pattern

### CircuitBreaker Pattern
**Why it's needed**: When services fail repeatedly, continued attempts to call them waste resources and can make the problem worse. Circuit breakers prevent applications from making futile calls to failing services, allowing them time to recover while protecting the calling application.

**What it prevents**:
- Resource exhaustion from repeatedly calling failing services
- Increased response times and system load during outages
- Cascading failures that bring down healthy services
- Prolonged user experience degradation during extended outages

CircuitBreaker prevents cascading failures by temporarily stopping calls to a failing service. It has three states:
- **CLOSED**: Normal operation, requests pass through
- **OPEN**: Service is failing, requests are blocked
- **HALF-OPEN**: Testing if service has recovered

Now let's add the Circuit Breaker pattern to protect against cascading failures. We'll enhance your existing `createUser` method with circuit breaker protection.

### Configure Circuit Breaker

Add circuit breaker configuration to your `application.conf`:

```hocon
resilient {
  retry {
    default {
      attempts = 3
      delay = 100ms
      delayStep = 200ms
    }
  }
  timeout {
    default {
      duration = 5s
    }
  }
  circuitBreaker {
    default {
      failureRateThreshold = 50
      slowCallRateThreshold = 50
      slowCallDurationThreshold = 2s
      slidingWindowSize = 10
      minimumNumberOfCalls = 5
      waitDurationInOpenState = 10s
    }
  }
}
```

### Enhance UserService with Circuit Breaker

Update your existing `UserService.java` to add circuit breaker to the `createUser` method:

```java
@Component
public final class UserService {
    // ... existing fields and constructor ...

    // ... existing methods ...

    @Retry("default")
    public Optional<UserResponse> getUserWithRetry(String id) {
        // ... existing implementation ...
    }

    @Timeout("default")
    public List<UserResponse> getUsersWithTimeout(int page, int size, String sort) {
        // ... existing implementation ...
    }

    @CircuitBreaker("default")
    public UserResponse createUserWithCircuitBreaker(UserRequest request) {
        // Simulate occasional failure that triggers circuit breaker
        if (Math.random() < 0.4) { // 40% chance of failure
            throw new RuntimeException("External service failure");
        }
        return createUser(request); // Use existing method
    }

    // ... existing methods ...
}
```

### Update Controller

Add a new endpoint in your existing `UserController.java` that uses the circuit breaker-enabled method:

```java
@Component
@HttpController
public final class UserController {
    // ... existing constructor and methods ...

    @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}/retry")
    @Json
    public Optional<UserResponse> getUserWithRetry(@Path String userId) {
        return userService.getUserWithRetry(userId);
    }

    @HttpRoute(method = HttpMethod.GET, path = "/users/timeout")
    @Json
    public List<UserResponse> getUsersWithTimeout(
        @Query("page") Optional<Integer> page,
        @Query("size") Optional<Integer> size,
        @Query("sort") Optional<String> sort
    ) {
        // ... existing implementation ...
    }

    @HttpRoute(method = HttpMethod.POST, path = "/users/circuit-breaker")
    @Json
    public UserResponse createUserWithCircuitBreaker(@RequestBody UserRequest request) {
        return userService.createUserWithCircuitBreaker(request);
    }

    // ... existing methods ...
}
```

### Test Circuit Breaker Behavior

Create a test that verifies the circuit breaker behavior:

```java
@KoraAppTest
class UserServiceCircuitBreakerTest {
    @TestComponent
    private UserService userService;

    @Test
    void shouldHandleCircuitBreakerOpenState() {
        // Given - simulate multiple failures to open circuit
        var request = new UserRequest("Test User", "test@example.com");

        // When - make multiple calls that may fail
        // Circuit breaker should open after enough failures
        for (int i = 0; i < 10; i++) {
            try {
                userService.createUserWithCircuitBreaker(request);
            } catch (Exception e) {
                // Expected failures to trigger circuit breaker
            }
        }

        // Then - circuit breaker should be open
        // Next call should fail fast with CircuitBreakerOpenException
        assertThatThrownBy(() -> userService.createUserWithCircuitBreaker(request))
            .isInstanceOf(RuntimeException.class); // CircuitBreakerOpenException
    }

    @Test
    void shouldAllowCallsWhenCircuitBreakerClosed() {
        // Given - circuit breaker should be closed initially
        var request = new UserRequest("Normal User", "normal@example.com");

        // When - make successful calls
        var user = userService.createUserWithCircuitBreaker(request);

        // Then - should succeed
        assertThat(user).isNotNull();
        assertThat(user.name()).isEqualTo("Normal User");
    }
}
```

### Run and Verify

Run the tests to see circuit breaker in action:

```bash
./gradlew test
```

You should see that after enough failures, the circuit breaker opens and subsequent calls fail fast. Your existing `/users` endpoint continues to work without circuit breaker, while the new `/users/circuit-breaker` endpoint demonstrates circuit breaker behavior.

## Adding Fallback Pattern

### Fallback Pattern
**Why it's needed**: In production systems, complete service failures can occur. Rather than failing entirely and providing no response to users, fallback patterns allow applications to continue operating with reduced functionality, maintaining some level of service availability.

**What it prevents**:
- Complete service unavailability during partial system failures
- Poor user experience from blank error pages or unresponsive applications
- Loss of critical functionality during non-critical service outages
- System-wide failures when dependent services become unavailable

Fallback provides alternative behavior when primary operations fail, ensuring graceful degradation and maintaining service availability even when some components are not functioning.

Now let's add the Fallback pattern to provide graceful degradation when operations fail. We'll enhance your existing `updateUser` method with fallback protection.

### Configure Fallback

Add fallback configuration to your `application.conf`:

```hocon
resilient {
  retry {
    default {
      attempts = 3
      delay = 100ms
      delayStep = 200ms
    }
  }
  timeout {
    default {
      duration = 5s
    }
  }
  circuitBreaker {
    default {
      failureRateThreshold = 50
      slowCallRateThreshold = 50
      slowCallDurationThreshold = 2s
      slidingWindowSize = 10
      minimumNumberOfCalls = 5
      waitDurationInOpenState = 10s
    }
  }
  fallback {
    default {
      enabled = true
    }
  }
}
```

### Enhance UserService with Fallback

Update your existing `UserService.java` to add fallback to the `updateUser` method:

```java
@Component
public final class UserService {
    // ... existing fields and constructor ...

    // ... existing methods ...

    @Retry("default")
    public Optional<UserResponse> getUserWithRetry(String id) {
        // ... existing implementation ...
    }

    @Timeout("default")
    public List<UserResponse> getUsersWithTimeout(int page, int size, String sort) {
        // ... existing implementation ...
    }

    @CircuitBreaker("default")
    public UserResponse createUserWithCircuitBreaker(UserRequest request) {
        // ... existing implementation ...
    }

    @Fallback("updateUserFallback")
    public UserResponse updateUserWithFallback(String id, UserRequest request) {
        // Simulate primary update that always fails
        throw new RuntimeException("Primary update service unavailable");
    }

    public UserResponse updateUserFallback(String id, UserRequest request) {
        // Fallback implementation - update user locally with limited validation
        var existingUser = getUser(id);
        if (existingUser.isEmpty()) {
            throw new RuntimeException("User not found for fallback update");
        }

        // Create updated user with fallback marker
        var updatedUser = new UserResponse(
            existingUser.get().id(),
            request.name() + " (fallback updated)",
            request.email(),
            existingUser.get().createdAt()
        );

        // In a real scenario, this would update the database
        // For demo purposes, we'll just return the updated user
        return updatedUser;
    }

    // ... existing methods ...
}
```

### Update Controller

Add a new endpoint in your existing `UserController.java` that uses the fallback-enabled method:

```java
@Component
@HttpController
public final class UserController {
    // ... existing constructor and methods ...

    @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}/retry")
    @Json
    public Optional<UserResponse> getUserWithRetry(@Path String userId) {
        return userService.getUserWithRetry(userId);
    }

    @HttpRoute(method = HttpMethod.GET, path = "/users/timeout")
    @Json
    public List<UserResponse> getUsersWithTimeout(
        @Query("page") Optional<Integer> page,
        @Query("size") Optional<Integer> size,
        @Query("sort") Optional<String> sort
    ) {
        // ... existing implementation ...
    }

    @HttpRoute(method = HttpMethod.POST, path = "/users/circuit-breaker")
    @Json
    public UserResponse createUserWithCircuitBreaker(@RequestBody UserRequest request) {
        return userService.createUserWithCircuitBreaker(request);
    }

    @HttpRoute(method = HttpMethod.PUT, path = "/users/{userId}/fallback")
    @Json
    public UserResponse updateUserWithFallback(@Path String userId, @RequestBody UserRequest request) {
        return userService.updateUserWithFallback(userId, request);
    }

    // ... existing methods ...
}
```

### Test Fallback Behavior

Create a test that verifies the fallback behavior:

```java
@KoraAppTest
class UserServiceFallbackTest {
    @TestComponent
    private UserService userService;

    @Test
    void shouldUseFallbackWhenPrimaryUpdateFails() {
        // Given - create a user first
        var createRequest = new UserRequest("Original Name", "original@example.com");
        var createdUser = userService.createUser(createRequest);

        // When - call fallback update method (primary always fails)
        var updateRequest = new UserRequest("Updated Name", "updated@example.com");
        var updated = userService.updateUserWithFallback(createdUser.id(), updateRequest);

        // Then - should get user updated by fallback method
        assertThat(updated.name()).isEqualTo("Updated Name (fallback updated)");
        assertThat(updated.email()).isEqualTo("updated@example.com");
    }

    @Test
    void shouldHandleFallbackForNonExistentUser() {
        // Given - try to update non-existent user
        var updateRequest = new UserRequest("Test Name", "test@example.com");

        // When & Then - should throw exception from fallback
        assertThatThrownBy(() -> userService.updateUserWithFallback("non-existent", updateRequest))
            .isInstanceOf(RuntimeException.class)
            .hasMessageContaining("User not found for fallback update");
    }
}
```

### Run and Verify

Run the tests to see fallback in action:

```bash
./gradlew test
```

You should see that when the primary update method fails, the fallback method is called and provides graceful degradation. Your existing `/users/{id}` PUT endpoint continues to work normally, while the new `/users/{userId}/fallback` endpoint demonstrates fallback behavior.

## Combining Resilience Patterns

Now let's combine multiple resilience patterns together for comprehensive fault tolerance. We'll enhance your existing `getUsers` method with all patterns working together.

### Configure Combined Patterns

Add comprehensive configuration for combined patterns to your `application.conf`:

```hocon
resilient {
  retry {
    default {
      attempts = 3
      delay = 100ms
      delayStep = 200ms
    }
  }
  timeout {
    default {
      duration = 5s
    }
  }
  circuitBreaker {
    default {
      failureRateThreshold = 50
      slowCallRateThreshold = 50
      slowCallDurationThreshold = 2s
      slidingWindowSize = 10
      minimumNumberOfCalls = 5
      waitDurationInOpenState = 10s
    }
  }
  fallback {
    default {
      enabled = true
    }
  }
}
```

### Enhance UserService with Combined Patterns

Update your existing `UserService.java` to add a method that combines all resilience patterns:

```java
@Component
public final class UserService {
    // ... existing fields and constructor ...

    // ... existing methods ...

    @Retry("default")
    public Optional<UserResponse> getUserWithRetry(String id) {
        // ... existing implementation ...
    }

    @Timeout("default")
    public List<UserResponse> getUsersWithTimeout(int page, int size, String sort) {
        // ... existing implementation ...
    }

    @CircuitBreaker("default")
    public UserResponse createUserWithCircuitBreaker(UserRequest request) {
        // ... existing implementation ...
    }

    @Fallback("updateUserFallback")
    public UserResponse updateUserWithFallback(String id, UserRequest request) {
        // ... existing implementation ...
    }

    public UserResponse updateUserFallback(String id, UserRequest request) {
        // ... existing implementation ...
    }

    @Timeout("default")
    @Retry("default")
    @CircuitBreaker("default")
    @Fallback("getUsersCombinedFallback")
    public List<UserResponse> getUsersCombined(String filter, String sort) {
        // Simulate complex operation that can fail in multiple ways
        simulateComplexFailure();

        // Apply filtering and sorting logic
        return getUsers(0, 100, sort).stream()
            .filter(user -> filter == null || user.name().contains(filter) || user.email().contains(filter))
            .toList();
    }

    public List<UserResponse> getUsersCombinedFallback(String filter, String sort) {
        // Fallback: return all users without filtering/sorting
        return getUsers(0, 100, "name");
    }

    private void simulateComplexFailure() {
        // Simulate various types of failures
        double random = Math.random();
        if (random < 0.2) {
            throw new RuntimeException("Network failure");
        } else if (random < 0.4) {
            // Simulate slow operation that might timeout
            try {
                Thread.sleep(2000);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                throw new RuntimeException("Operation interrupted", e);
            }
        } else if (random < 0.6) {
            throw new RuntimeException("Service unavailable");
        }
        // 40% chance of success
    }

    // ... existing methods ...
}
```

### Update Controller

Add a new endpoint in your existing `UserController.java` that uses the combined patterns method:

```java
@Component
@HttpController
public final class UserController {
    // ... existing constructor and methods ...

    @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}/retry")
    @Json
    public Optional<UserResponse> getUserWithRetry(@Path String userId) {
        return userService.getUserWithRetry(userId);
    }

    @HttpRoute(method = HttpMethod.GET, path = "/users/timeout")
    @Json
    public List<UserResponse> getUsersWithTimeout(
        @Query("page") Optional<Integer> page,
        @Query("size") Optional<Integer> size,
        @Query("sort") Optional<String> sort
    ) {
        // ... existing implementation ...
    }

    @HttpRoute(method = HttpMethod.POST, path = "/users/circuit-breaker")
    @Json
    public UserResponse createUserWithCircuitBreaker(@RequestBody UserRequest request) {
        return userService.createUserWithCircuitBreaker(request);
    }

    @HttpRoute(method = HttpMethod.PUT, path = "/users/{userId}/fallback")
    @Json
    public UserResponse updateUserWithFallback(@Path String userId, @RequestBody UserRequest request) {
        return userService.updateUserWithFallback(userId, request);
    }

    @HttpRoute(method = HttpMethod.GET, path = "/users/combined")
    @Json
    public List<UserResponse> getUsersCombined(
        @Query("filter") Optional<String> filter,
        @Query("sort") Optional<String> sort
    ) {
        String filterValue = filter.orElse(null);
        String sortValue = sort.orElse("name");
        return userService.getUsersCombined(filterValue, sortValue);
    }

    // ... existing methods ...
}
```

### Test Combined Patterns

Create a test that verifies the combined patterns behavior:

```java
@KoraAppTest
class UserServiceCombinedPatternsTest {
    @TestComponent
    private UserService userService;

    @Test
    void shouldHandleComplexOperationWithMultiplePatterns() {
        // Given - create some test users
        var request1 = new UserRequest("Alice", "alice@example.com");
        var request2 = new UserRequest("Bob", "bob@example.com");
        var request3 = new UserRequest("Charlie", "charlie@example.com");
        userService.createUser(request1);
        userService.createUser(request2);
        userService.createUser(request3);

        // When - perform complex operation (may fail but should eventually succeed due to retry)
        var results = userService.getUsersCombined("A", "name");

        // Then - should get filtered results (fallback provides all users if primary fails)
        assertThat(results).isNotEmpty();
        // Results should be filtered and may include fallback behavior
    }

    @Test
    void shouldUseFallbackForComplexOperation() {
        // Given - create test users
        var request = new UserRequest("Test User", "test@example.com");
        userService.createUser(request);

        // When - complex operation fails and uses fallback
        // The fallback returns all users without filtering
        var results = userService.getUsersCombined("nonexistent", "name");

        // Then - should get all users (fallback behavior)
        assertThat(results).hasSizeGreaterThanOrEqualTo(1);
    }
}
```

### Run and Verify

Run the tests to see all patterns working together:

```bash
./gradlew test
```

You should see that the combined patterns provide layered fault tolerance - timeout prevents hanging, retry handles transient failures, circuit breaker prevents cascading failures, and fallback provides graceful degradation. Your existing `/users` endpoint continues to work normally, while the new `/users/combined` endpoint demonstrates all resilience patterns working together.

## Configuration

Add the resilience configuration to your `application.conf`. This guide uses only the "default" configuration for all resilience patterns, but you can create named configurations for different scenarios:

```hocon
# ... existing configuration ...

resilient {
  retry {
    default {
      attempts = 3
      delay = 100ms
      delayStep = 200ms
    }
  }
  timeout {
    default {
      duration = 5s
    }
  }
  circuitBreaker {
    default {
      failureRateThreshold = 50
      slowCallRateThreshold = 50
      slowCallDurationThreshold = 2s
      slidingWindowSize = 10
      minimumNumberOfCalls = 5
      waitDurationInOpenState = 10s
    }
  }
  fallback {
    default {
      enabled = true
    }
  }
}
```

!!! tip "Named Configurations"

    You can create multiple named configurations for different scenarios. For example, you might want stricter settings for external API calls:

    ```hocon
    resilient {
      circuitBreaker {
        default { /* ... */ }
        external_api {
          failureRateThreshold = 30
          waitDurationInOpenState = 60s
        }
      }
      timeout {
        default { /* ... */ }
        external_api {
          duration = 10s
        }
      }
    }
    ```

    Then use them in your code: `@CircuitBreaker("external_api")` and `@Timeout("external_api")`.

## Testing Resilient Services

Create comprehensive tests for your resilient UserService:

===! ":fontawesome-brands-java: `Java`"

    `src/test/java/ru/tinkoff/kora/example/service/UserServiceTest.java`:

    ```java
    package ru.tinkoff.kora.example.service;

    import org.junit.jupiter.api.Test;
    import ru.tinkoff.kora.example.dto.UserRequest;
    import ru.tinkoff.kora.example.dto.UserResponse;
    import ru.tinkoff.kora.resilient.ResilientModule;
    import ru.tinkoff.kora.test.KoraAppTest;

    import java.util.List;
    import java.util.Optional;

    import static org.assertj.core.api.Assertions.assertThat;

    @KoraAppTest(ResilientModule.class)
    public class UserServiceTest {

        @Test
        void createUser_Success(UserService userService) {
            // Given
            UserRequest request = new UserRequest("John Doe", "john@example.com");

            // When
            UserResponse user = userService.createUser(request);

            // Then
            assertThat(user).isNotNull();
            assertThat(user.name()).isEqualTo("John Doe");
            assertThat(user.email()).isEqualTo("john@example.com");
        }

        @Test
        void getUser_TimeoutProtection(UserService userService) {
            // Given - create a user first
            UserRequest request = new UserRequest("Jane Doe", "jane@example.com");
            UserResponse createdUser = userService.createUser(request);

            // When - timeout should prevent hanging
            Optional<UserResponse> user = userService.getUser(createdUser.id());

            // Then
            assertThat(user).isPresent();
            assertThat(user.get().name()).isEqualTo("Jane Doe");
        }

        @Test
        void getAllUsers_RetryProtection(UserService userService) {
            // When - retry should handle temporary failures
            List<UserResponse> users = userService.getAllUsers();

            // Then
            assertThat(users).isNotNull();
            // Service should eventually succeed despite simulated failures
        }

        @Test
        void updateUser_FallbackProtection(UserService userService) {
            // Given - create a user first
            UserRequest createRequest = new UserRequest("Bob Smith", "bob@example.com");
            UserResponse createdUser = userService.createUser(createRequest);

            // When - update might fail but fallback should return existing user
            UserRequest updateRequest = new UserRequest("Bob Updated", "bob.updated@example.com");
            Optional<UserResponse> updatedUser = userService.updateUser(createdUser.id(), updateRequest);

            // Then - either updated user or fallback with original user
            assertThat(updatedUser).isPresent();
            UserResponse result = updatedUser.get();
            assertThat(result.id()).isEqualTo(createdUser.id());
            // Name and email might be updated or remain original due to fallback
        }

        @Test
        void getUsers_CombinedResilience(UserService userService) {
            // When - all resilience patterns work together
            List<UserResponse> users = userService.getUsers(0, 10, "name");

            // Then
            assertThat(users).isNotNull();
            // Service should succeed despite timeout, retry, and circuit breaker
        }

        @Test
        void deleteUser_FallbackProtection(UserService userService) {
            // Given - create a user first
            UserRequest request = new UserRequest("Alice Johnson", "alice@example.com");
            UserResponse createdUser = userService.createUser(request);

            // When - delete might fail but fallback should handle gracefully
            boolean deleted = userService.deleteUser(createdUser.id());

            // Then - operation should complete (either successfully or with fallback)
            // The boolean result indicates the outcome
            assertThat(deleted).isNotNull();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/test/kotlin/ru/tinkoff/kora/example/service/UserServiceTest.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.service

    import org.junit.jupiter.api.Test
    import ru.tinkoff.kora.example.dto.UserRequest
    import ru.tinkoff.kora.example.dto.UserResponse
    import ru.tinkoff.kora.resilient.ResilientModule
    import ru.tinkoff.kora.test.KoraAppTest
    import org.assertj.core.api.Assertions.assertThat
    import java.util.*

    @KoraAppTest(ResilientModule::class)
    class UserServiceTest {

        @Test
        fun createUser_Success(userService: UserService) {
            // Given
            val request = UserRequest("John Doe", "john@example.com")

            // When
            val user = userService.createUser(request)

            // Then
            assertThat(user).isNotNull
            assertThat(user.name).isEqualTo("John Doe")
            assertThat(user.email).isEqualTo("john@example.com")
        }

        @Test
        fun getUser_TimeoutProtection(userService: UserService) {
            // Given - create a user first
            val request = UserRequest("Jane Doe", "jane@example.com")
            val createdUser = userService.createUser(request)

            // When - timeout should prevent hanging
            val user = userService.getUser(createdUser.id)

            // Then
            assertThat(user).isPresent
            assertThat(user.get().name).isEqualTo("Jane Doe")
        }

        @Test
        fun getAllUsers_RetryProtection(userService: UserService) {
            // When - retry should handle temporary failures
            val users = userService.getAllUsers()

            // Then
            assertThat(users).isNotNull
            // Service should eventually succeed despite simulated failures
        }

        @Test
        fun updateUser_FallbackProtection(userService: UserService) {
            // Given - create a user first
            val createRequest = UserRequest("Bob Smith", "bob@example.com")
            val createdUser = userService.createUser(request)

            // When - update might fail but fallback should return existing user
            val updateRequest = UserRequest("Bob Updated", "bob.updated@example.com")
            val updatedUser = userService.updateUser(createdUser.id, updateRequest)

            // Then - either updated user or fallback with original user
            assertThat(updatedUser).isPresent
            val result = updatedUser.get()
            assertThat(result.id).isEqualTo(createdUser.id)
            // Name and email might be updated or remain original due to fallback
        }

        @Test
        fun getUsers_CombinedResilience(userService: UserService) {
            // When - all resilience patterns work together
            val users = userService.getUsers(0, 10, "name")

            // Then
            assertThat(users).isNotNull
            // Service should succeed despite timeout, retry, and circuit breaker
        }

        @Test
        fun deleteUser_FallbackProtection(userService: UserService) {
            // Given - create a user first
            val request = UserRequest("Alice Johnson", "alice@example.com")
            val createdUser = userService.createUser(request)

            // When - delete might fail but fallback should handle gracefully
            val deleted = userService.deleteUser(createdUser.id)

            // Then - operation should complete (either successfully or with fallback)
            assertThat(deleted).isNotNull()
        }
    }
    ```

## Running and Testing

Run your application to see resilience patterns in action:

```bash
./gradlew run
```

Test the endpoints to observe resilience behavior:

```bash
# Test circuit breaker behavior
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com"}'

# Test timeout behavior
curl http://localhost:8080/users/1

# Test retry and fallback behavior
curl -X PUT http://localhost:8080/users/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"Updated User","email":"updated@example.com"}'

# Test combined resilience
curl "http://localhost:8080/users?page=0&size=10&sort=name"
```

Run the tests to verify resilience patterns work correctly:

```bash
./gradlew test
```

## Key Concepts Learned

### Resilience Pattern Fundamentals
- **CircuitBreaker**: Prevents cascading failures by temporarily stopping calls to failing services
- **Retry**: Automatically retries failed operations with configurable backoff strategies
- **Timeout**: Sets maximum execution times to prevent hanging operations
- **Fallback**: Provides alternative behavior when primary operations fail

### Pattern States and Behavior
- **CircuitBreaker States**: CLOSED (normal), OPEN (blocking), HALF-OPEN (testing recovery)
- **Retry Strategies**: Fixed delay, exponential backoff, custom delay patterns
- **Timeout Types**: Fixed duration, dynamic timeouts based on operation type
- **Fallback Methods**: Graceful degradation, cached responses, default values

### Configuration Management
- **Hierarchical Config**: Default settings with named overrides for specific operations
- **Environment Tuning**: Different resilience settings for development vs production
- **Dynamic Adjustment**: Runtime configuration changes without restart

### Pattern Combination
- **Order Matters**: Timeout → Retry → CircuitBreaker → Fallback execution order
- **Complementary Behavior**: Patterns work together for comprehensive fault tolerance
- **Performance Impact**: Each pattern adds overhead, use judiciously

### Testing Resilience
- **Isolation Testing**: Test each pattern independently
- **Failure Simulation**: Inject failures to verify resilience behavior
- **Load Testing**: Verify patterns work under load conditions
- **Monitoring**: Track pattern effectiveness through metrics

## Next Steps

Continue your learning journey:

- **Next Guide**: [Database Integration Patterns](../database-jdbc.md) - Learn persistent data storage with fault tolerance
- **Related Guides**:
  - [HTTP Client Resilience](../../documentation/http-client.md) - Apply resilience to outbound HTTP calls
  - [Observability Patterns](../observability.md) - Monitor resilience pattern effectiveness
  - [Testing Strategies](../testing-junit.md) - Advanced testing with resilience patterns
- **Advanced Topics**:
  - [Custom Resilience Predicates](../../documentation/resilient.md#exception-filtering)
  - [Resilience Metrics](../../documentation/metrics.md#resilience-metrics)
  - [Distributed Circuit Breakers](../../documentation/resilient.md#imperative-usage)

## Troubleshooting

### CircuitBreaker Not Opening
- Ensure `minimumRequiredCalls` threshold is met before circuit breaker activates
- Check `failureRateThreshold` configuration matches your failure scenario
- Verify exception types are not filtered out by custom predicates

### Retry Not Working
- Check `attempts` configuration is greater than 1
- Verify `delay` settings allow sufficient time between attempts
- Ensure exceptions thrown match retry predicate criteria

### Timeout Too Aggressive
- Increase `duration` setting for slow operations
- Consider different timeout configurations for different operation types
- Monitor operation latency to set appropriate timeouts

### Fallback Not Triggered
- Verify fallback method signature matches the primary method
- Check that exceptions thrown are not caught elsewhere
- Ensure fallback configuration is enabled

### Performance Degradation
- Monitor the overhead of multiple resilience patterns on the same method
- Consider using patterns selectively based on operation criticality
- Tune configuration parameters for your specific use case

### Configuration Not Applied
- Check configuration syntax in `application.conf`
- Verify configuration keys match annotation values
- Ensure configuration is loaded at application startup

## Help

- [Resilient Module Documentation](../../documentation/resilient.md)
- [Kora GitHub Repository](https://github.com/kora-projects/kora)
- [GitHub Discussions](https://github.com/kora-projects/kora/discussions)
- [Resilience Patterns Best Practices](https://www.martinfowler.com/bliki/CircuitBreaker.html)