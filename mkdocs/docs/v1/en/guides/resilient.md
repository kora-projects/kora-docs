---
search:
  exclude: true
title: Build Resilient CRUD Operations with Retry, Timeout, Circuit Breaker, and Fallback
summary: Extend the HTTP Server guide by applying Kora resilience annotations directly to your existing UserService methods
tags: resilient, retry, timeout, circuitbreaker, fallback, http-server, hocon
---

# Resilience Patterns { #resilience-patterns }

This guide introduces resilience patterns for Kora service methods. It covers how retry, timeout, circuit breaker, and fallback annotations wrap application operations, how resilience configuration
controls failure behavior, and how the HTTP API can stay unchanged while service calls become more fault tolerant. You will also see how each pattern protects a different kind of unstable dependency
or operation.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java Resilient App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-resilient-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin Resilient App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-resilient-app).

## What You'll Build { #youll-build }

You will enhance the `UserService` from the HTTP Server guide with:

- `@Retry` on `getUser()` for transient read failures
- `@Fallback` on `createUser()` for graceful degradation when creation fails
- `@Timeout` on `deleteUser()` to stop hanging delete operations
- `@CircuitBreaker` on `updateUser()` to stop repeated failing updates
- a combined `@CircuitBreaker + @Retry + @Timeout` chain on `getUsers()`

## What You'll Need { #youll-need }

- JDK 17 or later
- Gradle 7.0 or later
- A text editor or IDE
- A working project from the [HTTP Server](http-server.md) guide

## Prerequisites { #prerequisites }

!!! note "Required: Complete HTTP Server Guide"

    This guide assumes you have completed **[HTTP Server](http-server.md)** and already have `Application`, `UserController`, `UserService`, `UserRepository`, `InMemoryUserRepository`, `UserRequest`, and `UserResponse`.

    If you haven't completed the HTTP server guide yet, do that first, because this guide adds resilience patterns to the existing CRUD API rather than creating the API from scratch.

## Overview { #overview }

[Kora resilience](../documentation/resilient.md) is about controlling how an application behaves when a dependency is slow, unstable, or temporarily unavailable. Without explicit resilience rules,
failures tend to spread: one slow operation can tie up request threads, repeated transient errors can overload a dependency, and a failing downstream call can make every endpoint look broken.

The goal is not to hide every failure. The goal is to make failure behavior intentional. A service should know when to try again, when to stop waiting, when to avoid a dependency for a while, and when
a safe fallback is acceptable.

### Resilience Basics { #resilience-basics }

In this guide, the HTTP contract stays unchanged. The resilience behavior is added around service methods because services are where application operations meet unstable work: storage calls, remote
calls, expensive computations, or background dependencies. Keeping resilience at this boundary lets controllers keep their routing role while service operations become more defensive.

### Core Patterns { #core-patterns }

Kora's resilience module provides several patterns, each with a different purpose:

- retry repeats an operation when a failure may be temporary
- timeout stops waiting when an operation takes too long
- circuit breaker stops calling a repeatedly failing operation for a period of time
- fallback provides an alternate result or behavior when the primary path fails

These patterns should not be used blindly. Retrying a non-idempotent write can duplicate work. A timeout that is too short can create false failures. A fallback can hide real outages if it is too
broad. The guide keeps each pattern visible so the trade-off is clear.

### Configuration and Composition { #configuration-composition }

Resilience behavior belongs in configuration as much as in annotations. Thresholds, attempts, delays, and timeout durations often differ between local development and production. Kora annotations mark
which pattern applies to which method, while configuration controls how aggressive that pattern is.

The guide also shows combined resilience behavior. In real services, a read path may need retry, timeout, and circuit breaker together. The important lesson is to compose these patterns deliberately
around a well-defined operation, then test the behavior as part of the service contract.

The practical flow is:

1. add the resilient module to the application graph
2. annotate service methods with one pattern at a time
3. configure thresholds, delays, and timeouts in HOCON
4. simulate failure modes in tests
5. verify that the HTTP contract stays stable while service behavior becomes more defensive

## Dependencies { #dependencies }

Add the resilience dependency to the existing project from the HTTP Server guide.

===! ":fontawesome-brands-java: `Java`"

    `build.gradle`:

    ```groovy
    dependencies {
        implementation("ru.tinkoff.kora:resilient-kora")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `build.gradle.kts`:

    ```kotlin
    dependencies {
        implementation("ru.tinkoff.kora:resilient-kora")
    }
    ```

## Modules { #modules }

First, enable the resilience infrastructure in your Kora application graph. This makes the retry, timeout, circuit breaker, and fallback annotations available to your components.

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/ru/tinkoff/kora/guide/resilient/Application.java`:

    ```java
    package ru.tinkoff.kora.guide.resilient;

    import ru.tinkoff.kora.application.graph.KoraApplication;
    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.config.hocon.HoconConfigModule;
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule;
    import ru.tinkoff.kora.json.module.JsonModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;
    import ru.tinkoff.kora.resilient.ResilientModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            UndertowHttpServerModule,
            JsonModule,
            LogbackModule,
            ResilientModule {  // <----- Connected module

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/ru/tinkoff/kora/guide/resilient/Application.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.resilient

    import ru.tinkoff.kora.application.graph.KoraApplication
    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.config.hocon.HoconConfigModule
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule
    import ru.tinkoff.kora.json.module.JsonModule
    import ru.tinkoff.kora.logging.logback.LogbackModule
    import ru.tinkoff.kora.resilient.ResilientModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        UndertowHttpServerModule,
        JsonModule,
        LogbackModule,
        ResilientModule  // <----- Connected module

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

## Retry { #retry }

`Retry` is the safest place to start because transient failures are most common on reads. A short network glitch, a temporary connection issue, or a brief overload is often resolved if the same
operation is repeated a few moments later.

Kora lets you use resilience both declaratively through annotations and imperatively through manager-style APIs such as `RetryManager`, `TimeoutManager`, `CircuitBreakerManager`,
and `FallbackManager`. In this guide we use the AOP style because it is the shortest way to evolve the existing `UserService`, while the imperative approach is documented in
the [Resilient module reference](../documentation/resilient.md).

Because this step uses annotations, the class must still satisfy the AOP rules:

- in Java, the class must not be `final`
- in Kotlin, the class must be `open`

Retry is useful when:

- failures are short-lived and usually succeed on the next attempt
- the operation is safe to repeat
- the extra latency from retries is acceptable

Use it carefully when:

- the operation changes state and may not be idempotent
- the downstream service is already overloaded and retries would amplify pressure
- the timeout budget is already very small

Retry does not have to react to every exception. By default Kora uses its built-in retry predicate, but you can narrow or replace that behavior by implementing `RetryPredicate` and binding it in
configuration. That is how you say which failures are truly transient and worth retrying. See the predicate and configuration details in the [Resilient documentation](../documentation/resilient.md).

Add the retry config exactly where you introduce the annotation.

`src/main/resources/application.conf`:

For the full configuration reference, see [Resilient](../documentation/resilient.md).

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
      retry {
        default {
          delay = 20ms //(1)!
          attempts = 3 //(2)!
          delayStep = 20ms //(3)!
        }
      }
    }
    ```

    1. Initial delay before a retry attempt.
    2. Maximum number of retry attempts.
    3. Delay increment between retry attempts.

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      retry:
        default:
          delay: 20ms #(1)!
          attempts: 3 #(2)!
          delayStep: 20ms #(3)!
    ```

    1. Initial delay before a retry attempt.
    2. Maximum number of retry attempts.
    3. Delay increment between retry attempts.

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/ru/tinkoff/kora/guide/resilient/service/UserService.java`:

    ```java
    @Component
    public class UserService {

        private final UserRepository userRepository;

        public UserService(UserRepository userRepository) {
            this.userRepository = userRepository;
        }

        @Retry("default")
        public Optional<UserResponse> getUser(String id) {
            return userRepository.findById(id);
        }

        // other methods stay unchanged for now
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/ru/tinkoff/kora/guide/resilient/service/UserService.kt`:

    ```kotlin
    @Component
    open class UserService(
        private val userRepository: UserRepository,
    ) {

        @Retry("default")
        open fun getUser(id: String): UserResponse? = userRepository.findById(id)

        // other methods stay unchanged for now
    }
    ```

The controller does not need a new endpoint. `GET /users/{userId}` already delegates to `getUser()`, so the resilience behavior is applied automatically at the service boundary.

After compilation, the generated proxy shows that `@Retry` wraps the original method call directly:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-resilient-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/resilient/service/$UserService__AopProxy.java
    ```

    ```java
    private Optional<UserResponse> _getUser_AopProxy_RetryKoraAspect(String id) {
        return retry1.retry(() -> super.getUser(id));
    }

    @Override
    public Optional<UserResponse> getUser(String id) {
        return this._getUser_AopProxy_RetryKoraAspect(id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-resilient-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/resilient/service/$UserService__AopProxy.kt
    ```

    ```kotlin
    private fun _getUser_AopProxy_RetryKoraAspect(id: String): UserResponse? =
        retry1.retry(Retry.RetrySupplier { super.getUser(id) })

    override fun getUser(id: String): UserResponse? = _getUser_AopProxy_RetryKoraAspect(id)
    ```

The important part is `retry1.retry(() -> super.getUser(id))`: Kora generated a retry boundary around your service method, and your original code is still the `super.getUser(id)` call inside that
boundary.

## Fallback { #fallback }

`Fallback` is about graceful degradation. If the primary path fails, you return a controlled alternative instead of simply propagating the failure.

Kora again supports both AOP annotations and imperative fallback usage through `FallbackManager`. In this guide we stay with the annotation-based style so the existing `createUser()` method evolves in
place.

Fallback is useful when:

- you can return a safe substitute or delayed-processing response
- the user experience is better with a degraded answer than with a hard failure
- you have a clearly defined backup policy

Use it carefully when:

- the fallback hides a serious incident for too long
- the fallback can create inconsistent business state
- the team starts using fallback as a silent substitute for proper persistence or delivery guarantees

Fallback also does not have to react to every exception. Kora can decide whether a particular failure should trigger the fallback path through a predicate. If you need to control that behavior,
implement `FallbackPredicate` and wire it through the named configuration. See the predicate section in the [Resilient documentation](../documentation/resilient.md).

Now add only the fallback-capable behavior we need for `createUser()`.

`src/main/resources/application.conf`:

For the full configuration reference, see [Resilient](../documentation/resilient.md).

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
      retry {
        default {
          delay = 20ms //(1)!
          attempts = 3 //(2)!
          delayStep = 20ms //(3)!
        }
      }
    }
    ```

    1. Initial delay before a retry attempt.
    2. Maximum number of retry attempts.
    3. Delay increment between retry attempts.

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      retry:
        default:
          delay: 20ms #(1)!
          attempts: 3 #(2)!
          delayStep: 20ms #(3)!
    ```

    1. Initial delay before a retry attempt.
    2. Maximum number of retry attempts.
    3. Delay increment between retry attempts.

No extra `fallback.default {}` block is required here because the default fallback behavior is already available.

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/ru/tinkoff/kora/guide/resilient/service/UserService.java`:

    ```java
    @Fallback(value = "default", method = "createUserFallback(request)")
    public UserResponse createUser(UserRequest request) {
        var generatedId = userRepository.save(request.name(), request.email());
        return new UserResponse(generatedId, request.name(), request.email(), LocalDateTime.now());
    }

    protected UserResponse createUserFallback(UserRequest request) {
        // Never do this in real systems: imagine we wrote the request to a file
        // and planned to recreate the user during application startup.
        return new UserResponse("pending-file-write", request.name(), request.email(), LocalDateTime.now());
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/ru/tinkoff/kora/guide/resilient/service/UserService.kt`:

    ```kotlin
    @Fallback(value = "default", method = "createUserFallback(request)")
    open fun createUser(request: UserRequest): UserResponse {
        val generatedId = userRepository.save(request.name, request.email)
        return UserResponse(generatedId, request.name, request.email, LocalDateTime.now())
    }

    protected open fun createUserFallback(request: UserRequest): UserResponse {
        // Never do this in real systems: imagine we wrote the request to a file
        // and planned to recreate the user during application startup.
        return UserResponse("pending-file-write", request.name, request.email, LocalDateTime.now())
    }
    ```

The fallback method does not change the controller contract. `POST /users` still returns `UserResponse`, but now the service can degrade gracefully when the primary path fails.

It is important to understand exactly when fallback is called:

1. Kora first invokes the original method.
2. If the original method returns successfully, fallback is not used at all.
3. If the original method throws an exception, Kora checks whether fallback can handle that failure.
4. If the failure matches the fallback rules, Kora calls the fallback method declared in `method = "..."`.
5. The fallback method result becomes the final result returned to the caller.

So fallback is never the primary execution path. It is only a backup path that runs after the original method has already failed.

In this example, `createUserFallback(request)` receives the same `request` argument from the failed `createUser(request)` call. That is what the `method = "createUserFallback(request)"` declaration
means: Kora takes the original method arguments and passes the selected ones into the fallback method in the declared order.

This is also why fallback must be used carefully. It is excellent for graceful degradation, but it can also hide real failures if the fallback response looks too much like a real success. That risk is
especially important for write operations such as `createUser()`, where a fallback may return something useful to the caller even though the original write did not actually complete.

Kora supports both annotation-based AOP usage and imperative fallback usage through `FallbackManager`. In this guide we use the AOP style because it keeps the explanation close to the existing service
method.

After compilation, the generated proxy shows the fallback decision next to the original call:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-resilient-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/resilient/service/$UserService__AopProxy.java
    ```

    ```java
    private UserResponse _createUser_AopProxy_FallbackKoraAspect(UserRequest request) {
        try {
            return super.createUser(request);
        } catch (Throwable _e) {
            if (fallback1.canFallback(_e)) {
                return createUserFallback(request);
            } else {
                throw _e;
            }
        }
    }


    @Override
    public UserResponse createUser(UserRequest request) {
        return this._createUser_AopProxy_FallbackKoraAspect(request);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-resilient-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/resilient/service/$UserService__AopProxy.kt
    ```

    ```kotlin
    private fun _createUser_AopProxy_FallbackKoraAspect(request: UserRequest): UserResponse = try {
      super.createUser(request)
    } catch (_e: Throwable) {
      if(fallback1.canFallback(_e)) {
        createUserFallback(request)
      } else {
        throw _e
      }
    }

    override fun createUser(request: UserRequest): UserResponse =
        _createUser_AopProxy_FallbackKoraAspect(request)
    ```

This makes the fallback rule concrete: Kora first calls `super.createUser(request)`, and only if that call throws does it ask `fallback1.canFallback(_e)` before invoking `createUserFallback(request)`.

## Timeout { #timeout }

`Timeout` keeps slow operations from consuming resources indefinitely. Even when a failure is rare, a hanging call can still damage the whole application by tying up threads and request capacity.

Kora supports timeout both through annotations and through `TimeoutManager`. Here we keep the annotation approach because it reads naturally on the existing method.

Timeout is useful when:

- slow operations are worse than fast failure
- the caller needs a predictable upper bound on latency
- you want retries or circuit breakers to work on top of a bounded execution time

Use it carefully when:

- the timeout is shorter than normal healthy latency
- the operation has side effects that may continue after the caller times out
- you stack retries on top of timeouts without thinking about total worst-case latency

Timeout itself is duration-based, but when you combine it with retry, circuit breaker, or fallback, the resulting exception flow still determines what happens next. That means later layers may or may
not react to timeout exceptions depending on their configured predicates. See the composition details in the [Resilient documentation](../documentation/resilient.md).

Now add timeout config for `deleteUser()`.

`src/main/resources/application.conf`:

For the full configuration reference, see [Resilient](../documentation/resilient.md).

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
      retry {
        default {
          delay = 20ms //(1)!
          attempts = 3 //(2)!
          delayStep = 20ms //(3)!
        }
      }
      timeout {
        default {
          duration = 100ms //(4)!
        }
      }
    }
    ```

    1. Initial delay before a retry attempt.
    2. Maximum number of retry attempts.
    3. Delay increment between retry attempts.
    4. Timeout duration for the protected operation.

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      retry:
        default:
          delay: 20ms #(1)!
          attempts: 3 #(2)!
          delayStep: 20ms #(3)!
      timeout:
        default:
          duration: 100ms #(4)!
    ```

    1. Initial delay before a retry attempt.
    2. Maximum number of retry attempts.
    3. Delay increment between retry attempts.
    4. Timeout duration for the protected operation.

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/ru/tinkoff/kora/guide/resilient/service/UserService.java`:

    ```java
    @Timeout("default")
    public void deleteUser(String id) {
        boolean deleted = userRepository.deleteById(id);
        if (!deleted) {
            throw HttpServerResponseException.of(404, "User not found");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/ru/tinkoff/kora/guide/resilient/service/UserService.kt`:

    ```kotlin
    @Timeout("default")
    open fun deleteUser(id: String) {
        val deleted = userRepository.deleteById(id)
        if (!deleted) {
            throw HttpServerResponseException.of(404, "User not found")
        }
    }
    ```

The endpoint stays `DELETE /users/{userId}`. Only the service method changes.

After compilation, the generated proxy shows that the timeout bounds the original delete operation:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-resilient-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/resilient/service/$UserService__AopProxy.java
    ```

    ```java
    private void _deleteUser_AopProxy_TimeoutKoraAspect(String id) {
        timeout1.execute(() -> {
            super.deleteUser(id);
            return null;
        });
    }

    @Override
    public void deleteUser(String id) {
        this._deleteUser_AopProxy_TimeoutKoraAspect(id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-resilient-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/resilient/service/$UserService__AopProxy.kt
    ```

    ```kotlin
    private fun _deleteUser_AopProxy_TimeoutKoraAspect(id: String) {
      timeout1.execute(Callable { super.deleteUser(id) })
    }

    override fun deleteUser(id: String) {
      _deleteUser_AopProxy_TimeoutKoraAspect(id)
    }
    ```

The generated code is especially useful for void methods: Kora wraps `super.deleteUser(id)` in `timeout1.execute(...)` and returns `null` only to satisfy the lambda shape.

## Circuit Breaker { #circuit-breaker }

`CircuitBreaker` protects the system from repeatedly calling a path that is already failing. Once enough failures happen, Kora opens the breaker and fails fast for a while instead of repeatedly doing
expensive work that is likely to fail again.

This pattern is especially useful when the real problem is not in your controller or service logic itself, but in something the method depends on: a database, another HTTP service, a message broker,
or any unstable downstream operation. Without a circuit breaker, every new request keeps trying the same failing path, which wastes threads, increases latency, and often makes the outage worse.

Kora describes circuit breaker as a proxy around a particular method. It watches recent calls and moves through three classic states:

- `CLOSED`: calls are allowed through normally, and Kora counts recent failures inside the configured `slidingWindowSize`
- `OPEN`: once there are enough calls to evaluate (`minimumRequiredCalls`) and the failure rate crosses `failureRateThreshold`, Kora stops calling the protected method and immediately fails fast
- `HALF-OPEN`: after `waitDurationInOpenState` expires, Kora allows only a limited number of probe calls (`permittedCallsInHalfOpenState`) to check whether the dependency has recovered

If those half-open probe calls succeed, the breaker closes again and normal traffic resumes. If one of them fails, the breaker opens again and starts another wait period. That is the main value of the
pattern: give an unhealthy dependency time to recover instead of continuously hammering it, but still periodically test whether it is healthy again.

Kora supports both annotated and imperative circuit breaker usage. Here we keep the declarative style because it maps cleanly onto the existing `updateUser()` method. If you need finer control, you
can also inject `CircuitBreakerManager` and use a breaker imperatively, as described in the [Resilient module documentation](../documentation/resilient.md).

Circuit breaker is useful when:

- a downstream dependency is unhealthy and repeated calls only waste resources
- fast failure is better than long repeated timeouts
- you want a recovery window before allowing traffic again

Use it carefully when:

- thresholds are tuned too aggressively and healthy traffic gets blocked
- failures that should be treated differently are all grouped together
- the breaker is placed around very cheap, in-process operations where the cost of tripping is higher than the cost of retrying

Circuit breaker does not have to count every exception as a breaker failure. Kora supports custom filtering through `CircuitBreakerPredicate`, so you can decide which errors should affect breaker
state and which ones should be ignored. In this guide we will use that in the next step, because `updateUser()` can legitimately return `404 Not Found`, and a missing user should not look like
infrastructure instability.

Start by adding the circuit breaker config itself.

`src/main/resources/application.conf`:

For the full configuration reference, see [Resilient](../documentation/resilient.md).

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
      retry {
        default {
          delay = 20ms //(1)!
          attempts = 3 //(2)!
          delayStep = 20ms //(3)!
        }
      }
      timeout {
        default {
          duration = 100ms //(4)!
        }
      }
      circuitbreaker {
        default {
          slidingWindowSize = 2 //(5)!
          minimumRequiredCalls = 2 //(6)!
          failureRateThreshold = 100 //(7)!
          permittedCallsInHalfOpenState = 1 //(8)!
          waitDurationInOpenState = 200ms //(9)!
        }
      }
    }
    ```

    1. Initial delay before a retry attempt.
    2. Maximum number of retry attempts.
    3. Delay increment between retry attempts.
    4. Timeout duration for the protected operation.
    5. Number of calls kept in the circuit breaker sliding window.
    6. Minimum calls required before the circuit breaker evaluates failures.
    7. Failure rate that opens the circuit breaker.
    8. Number of trial calls allowed while the circuit breaker is half-open.
    9. Time the circuit breaker stays open before probing recovery.

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      retry:
        default:
          delay: 20ms #(1)!
          attempts: 3 #(2)!
          delayStep: 20ms #(3)!
      timeout:
        default:
          duration: 100ms #(4)!
      circuitbreaker:
        default:
          slidingWindowSize: 2 #(5)!
          minimumRequiredCalls: 2 #(6)!
          failureRateThreshold: 100 #(7)!
          permittedCallsInHalfOpenState: 1 #(8)!
          waitDurationInOpenState: 200ms #(9)!
    ```

    1. Initial delay before a retry attempt.
    2. Maximum number of retry attempts.
    3. Delay increment between retry attempts.
    4. Timeout duration for the protected operation.
    5. Number of calls kept in the circuit breaker sliding window.
    6. Minimum calls required before the circuit breaker evaluates failures.
    7. Failure rate that opens the circuit breaker.
    8. Number of trial calls allowed while the circuit breaker is half-open.
    9. Time the circuit breaker stays open before probing recovery.

A key detail here is that Kora uses `minimumRequiredCalls`, not `minimumNumberOfCalls`.

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/ru/tinkoff/kora/guide/resilient/service/UserService.java`:

    ```java
    @CircuitBreaker("default")
    public UserResponse updateUser(String id, UserRequest request) {
        boolean updated = userRepository.update(id, request.name(), request.email());
        if (!updated) {
            throw HttpServerResponseException.of(404, "User not found");
        }
        return new UserResponse(id, request.name(), request.email(), LocalDateTime.now());
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/ru/tinkoff/kora/guide/resilient/service/UserService.kt`:

    ```kotlin
    @CircuitBreaker("default")
    open fun updateUser(id: String, request: UserRequest): UserResponse {
        val updated = userRepository.update(id, request.name, request.email)
        if (!updated) {
            throw HttpServerResponseException.of(404, "User not found")
        }
        return UserResponse(id, request.name, request.email, LocalDateTime.now())
    }
    ```

Again, the controller stays the same. `PUT /users/{userId}` still calls `updateUser()`, but after enough failures the circuit breaker can open and fail fast.

After compilation, the generated proxy shows the circuit breaker lifecycle around the original update:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-resilient-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/resilient/service/$UserService__AopProxy.java
    ```

    ```java
    private UserResponse _updateUser_AopProxy_CircuitBreakerKoraAspect(String id, UserRequest request) {
        try {
            circuitBreaker1.acquire();
            var _result = super.updateUser(id, request);
            circuitBreaker1.releaseOnSuccess();
            return _result;
        } catch (CallNotPermittedException _e) {
            throw _e;
        } catch (Throwable _e) {
            circuitBreaker1.releaseOnError(_e);
            throw _e;
        }
    }

    @Override
    public UserResponse updateUser(String id, UserRequest request) {
        return this._updateUser_AopProxy_CircuitBreakerKoraAspect(id, request);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-resilient-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/resilient/service/$UserService__AopProxy.kt
    ```

    ```kotlin
    private fun _updateUser_AopProxy_CircuitBreakerKoraAspect(id: String, request: UserRequest):
        UserResponse = try {
      circuitBreaker1.acquire()
      val t = super.updateUser(id, request)
      circuitBreaker1.releaseOnSuccess()
      t
    } catch (e: CallNotPermittedException) {
      throw e
    } catch (e: Throwable) {
      circuitBreaker1.releaseOnError(e)
      throw e
    }

    override fun updateUser(id: String, request: UserRequest): UserResponse =
        _updateUser_AopProxy_CircuitBreakerKoraAspect(id, request)
    ```

This fragment shows the breaker protocol directly: acquire permission, call the original method, release success on a good result, and release error when the protected method fails.

## Circuit Breaker Predicate { #circuit-breaker-predicate }

Now make the circuit breaker smarter for this specific API. We do not want every exception to count as a circuit breaker failure.

In this guide `updateUser()` can fail for two very different reasons:

- the user really does not exist, which is a normal business outcome and should simply return `404 Not Found`
- the update path is genuinely unhealthy, for example because some downstream dependency or internal operation is failing repeatedly

`CircuitBreakerFailurePredicate` lets us separate those cases. We do not want a missing user to push the breaker toward `OPEN`, because that would teach the breaker the wrong lesson about system
health. We only want the breaker to react to failures that actually indicate instability.

Kora calls this predicate whenever the protected method throws an exception. If the predicate returns `true`, that failure is counted by the circuit breaker. If it returns `false`, the exception is
still returned to the caller, but it does not affect the breaker state.

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/ru/tinkoff/kora/guide/resilient/service/CircuitBreakerFailurePredicate.java`:

    ```java
    @Component
    public final class CircuitBreakerFailurePredicate implements CircuitBreakerPredicate {

        @Override
        public String name() {
            return "RecordServerErrorsOnly";
        }

        @Override
        public boolean test(Throwable throwable) {
            if (throwable instanceof HttpServerResponseException exception) {
                return exception.code() >= 500;
            }
            return true;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/ru/tinkoff/kora/guide/resilient/service/CircuitBreakerFailurePredicate.kt`:

    ```kotlin
    @Component
    class CircuitBreakerFailurePredicate : CircuitBreakerPredicate {

        override fun name(): String = "RecordServerErrorsOnly"

        override fun test(throwable: Throwable): Boolean {
            return if (throwable is HttpServerResponseException) {
                throwable.code() >= 500
            } else {
                true
            }
        }
    }
    ```

Then bind it in the circuit breaker config:

`src/main/resources/application.conf`:

For the full configuration reference, see [Resilient](../documentation/resilient.md).

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
      retry {
        default {
          delay = 20ms //(1)!
          attempts = 3 //(2)!
          delayStep = 20ms //(3)!
        }
      }
      timeout {
        default {
          duration = 100ms //(4)!
        }
      }
      circuitbreaker {
        default {
          slidingWindowSize = 2 //(5)!
          minimumRequiredCalls = 2 //(6)!
          failureRateThreshold = 100 //(7)!
          permittedCallsInHalfOpenState = 1 //(8)!
          waitDurationInOpenState = 200ms //(9)!
          failurePredicateName = "RecordServerErrorsOnly" //(10)!
        }
      }
    }
    ```

    1. Initial delay before a retry attempt.
    2. Maximum number of retry attempts.
    3. Delay increment between retry attempts.
    4. Timeout duration for the protected operation.
    5. Number of calls kept in the circuit breaker sliding window.
    6. Minimum calls required before the circuit breaker evaluates failures.
    7. Failure rate that opens the circuit breaker.
    8. Number of trial calls allowed while the circuit breaker is half-open.
    9. Time the circuit breaker stays open before probing recovery.
    10. Value for `resilient.circuitbreaker.default.failurePredicateName`.

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      retry:
        default:
          delay: 20ms #(1)!
          attempts: 3 #(2)!
          delayStep: 20ms #(3)!
      timeout:
        default:
          duration: 100ms #(4)!
      circuitbreaker:
        default:
          slidingWindowSize: 2 #(5)!
          minimumRequiredCalls: 2 #(6)!
          failureRateThreshold: 100 #(7)!
          permittedCallsInHalfOpenState: 1 #(8)!
          waitDurationInOpenState: 200ms #(9)!
          failurePredicateName: "RecordServerErrorsOnly" #(10)!
    ```

    1. Initial delay before a retry attempt.
    2. Maximum number of retry attempts.
    3. Delay increment between retry attempts.
    4. Timeout duration for the protected operation.
    5. Number of calls kept in the circuit breaker sliding window.
    6. Minimum calls required before the circuit breaker evaluates failures.
    7. Failure rate that opens the circuit breaker.
    8. Number of trial calls allowed while the circuit breaker is half-open.
    9. Time the circuit breaker stays open before probing recovery.
    10. Value for `resilient.circuitbreaker.default.failurePredicateName`.

## Combined Pattern { #combined-pattern }

The final step shows how several resilience tools can cooperate on one method. `getUsers()` is a good place to demonstrate this because list operations often become aggregation points: sorting,
paging, cache lookups, remote data fetches, or expensive reads.

Kora allows the same combined logic both declaratively through annotations and imperatively through the manager APIs. In this guide we stay with the declarative path because the ordering is visible
directly above the method.

This combined chain is useful when:

- you want a hard upper time limit
- you still want a few retries for transient failures
- you also want the breaker to open if the method keeps failing

Use it carefully when:

- you stack too many policies and make the total behavior hard to reason about
- retries plus timeout create a much larger worst-case latency than expected
- failures become harder to debug because several layers can transform the final error path

Add the same config blocks that the combined method needs.

`src/main/resources/application.conf`:

For the full configuration reference, see [Resilient](../documentation/resilient.md).

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
      retry {
        default {
          delay = 20ms //(1)!
          attempts = 3 //(2)!
          delayStep = 20ms //(3)!
        }
      }
      timeout {
        default {
          duration = 100ms //(4)!
        }
      }
      circuitbreaker {
        default {
          slidingWindowSize = 2 //(5)!
          minimumRequiredCalls = 2 //(6)!
          failureRateThreshold = 100 //(7)!
          permittedCallsInHalfOpenState = 1 //(8)!
          waitDurationInOpenState = 200ms //(9)!
          failurePredicateName = "RecordServerErrorsOnly" //(10)!
        }
      }
    }
    ```

    1. Initial delay before a retry attempt.
    2. Maximum number of retry attempts.
    3. Delay increment between retry attempts.
    4. Timeout duration for the protected operation.
    5. Number of calls kept in the circuit breaker sliding window.
    6. Minimum calls required before the circuit breaker evaluates failures.
    7. Failure rate that opens the circuit breaker.
    8. Number of trial calls allowed while the circuit breaker is half-open.
    9. Time the circuit breaker stays open before probing recovery.
    10. Value for `resilient.circuitbreaker.default.failurePredicateName`.

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      retry:
        default:
          delay: 20ms #(1)!
          attempts: 3 #(2)!
          delayStep: 20ms #(3)!
      timeout:
        default:
          duration: 100ms #(4)!
      circuitbreaker:
        default:
          slidingWindowSize: 2 #(5)!
          minimumRequiredCalls: 2 #(6)!
          failureRateThreshold: 100 #(7)!
          permittedCallsInHalfOpenState: 1 #(8)!
          waitDurationInOpenState: 200ms #(9)!
          failurePredicateName: "RecordServerErrorsOnly" #(10)!
    ```

    1. Initial delay before a retry attempt.
    2. Maximum number of retry attempts.
    3. Delay increment between retry attempts.
    4. Timeout duration for the protected operation.
    5. Number of calls kept in the circuit breaker sliding window.
    6. Minimum calls required before the circuit breaker evaluates failures.
    7. Failure rate that opens the circuit breaker.
    8. Number of trial calls allowed while the circuit breaker is half-open.
    9. Time the circuit breaker stays open before probing recovery.
    10. Value for `resilient.circuitbreaker.default.failurePredicateName`.

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/ru/tinkoff/kora/guide/resilient/service/UserService.java`:

    ```java
    @CircuitBreaker("default")
    @Retry("default")
    @Timeout("default")
    public List<UserResponse> getUsers(int page, int size, String sort) {
        return userRepository.findAll().stream()
                .sorted(getComparator(sort))
                .skip((long) page * size)
                .limit(size)
                .toList();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/ru/tinkoff/kora/guide/resilient/service/UserService.kt`:

    ```kotlin
    @CircuitBreaker("default")
    @Retry("default")
    @Timeout("default")
    open fun getUsers(page: Int, size: Int, sort: String): List<UserResponse> =
        userRepository.findAll().stream()
            .sorted(getComparator(sort))
            .skip((page.toLong()) * size)
            .limit(size.toLong())
            .toList()
    ```

The annotation order matters because it defines the order in which Kora applies the aspects around the method. In other words, the annotation closest to the method is the innermost layer, and the
annotation listed first becomes the outermost layer.

In this guide the call flow is:

1. `@CircuitBreaker`
2. `@Retry`
3. `@Timeout`

A very common order that works well for many real systems is:

1. `@Fallback` last, if you truly want a degraded backup response
2. `@CircuitBreaker` to stop repeated failing calls from continuing forever
3. `@Retry` to repeat transient failures a limited number of times
4. `@Timeout` to bound one attempt

That order is common because `@Timeout` is the innermost layer and bounds one concrete attempt, `@Retry` wraps that bounded attempt and repeats it a limited number of times, `@CircuitBreaker` wraps
the retry flow and observes whether the whole operation keeps failing, and `@Fallback` is the outermost layer that only gets a chance to produce a degraded response after the inner layers have already
failed. It is not the only valid order, but it is usually the easiest one to reason about.

Also remember that these aspects may still react only to selected failures. Retry, circuit breaker, and fallback can all be configured with custom predicates, so even in a combined chain they do not
have to treat every exception the same way. That matches the [combination rules in the documentation](../documentation/resilient.md#combination).

After compilation, the generated proxy shows the exact nesting for the combined method:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-resilient-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/resilient/service/$UserService__AopProxy.java
    ```

    ```java
    private List<UserResponse> _getUsers_AopProxy_TimeoutKoraAspect(int page, int size, String sort) {
        return timeout1.execute(() -> super.getUsers(page, size, sort));
    }

    private List<UserResponse> _getUsers_AopProxy_RetryKoraAspect(int page, int size, String sort) {
        return retry1.retry(() -> _getUsers_AopProxy_TimeoutKoraAspect(page, size, sort));
    }

    private List<UserResponse> _getUsers_AopProxy_CircuitBreakerKoraAspect(int page, int size, String sort) {
        try {
            circuitBreaker1.acquire();
            var _result = _getUsers_AopProxy_RetryKoraAspect(page, size, sort);
            circuitBreaker1.releaseOnSuccess();
            return _result;
        } catch (CallNotPermittedException _e) {
            throw _e;
        } catch (Throwable _e) {
            circuitBreaker1.releaseOnError(_e);
            throw _e;
        }
    }

    @Override
    public List<UserResponse> getUsers(int page, int size, String sort) {
        return this._getUsers_AopProxy_CircuitBreakerKoraAspect(page, size, sort);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-resilient-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/resilient/service/$UserService__AopProxy.kt
    ```

    ```kotlin
    private fun _getUsers_AopProxy_TimeoutKoraAspect(
      page: Int,
      size: Int,
      sort: String,
    ): List<UserResponse> = timeout1.execute(Callable { super.getUsers(page, size, sort) })

    private fun _getUsers_AopProxy_RetryKoraAspect(
      page: Int,
      size: Int,
      sort: String,
    ): List<UserResponse> = retry1.retry(Retry.RetrySupplier {
      _getUsers_AopProxy_TimeoutKoraAspect(page, size, sort)
    })

    private fun _getUsers_AopProxy_CircuitBreakerKoraAspect(
      page: Int,
      size: Int,
      sort: String,
    ): List<UserResponse> = try {
      circuitBreaker1.acquire()
      val t = _getUsers_AopProxy_RetryKoraAspect(page, size, sort)
      circuitBreaker1.releaseOnSuccess()
      t
    } catch (e: Throwable) {
      circuitBreaker1.releaseOnError(e)
      throw e
    }
    ```

This is the clearest way to verify aspect order: the public method enters the circuit breaker, the circuit breaker calls retry, retry calls timeout, and timeout finally calls `super.getUsers(...)`.

## Generated Code { #generated-code }

The resilience annotations in this guide are applied through compile-time AOP in the same way as the validation and cache annotations.

Kora does not modify `UserService.java` or `UserService.kt` directly. Instead, it generates a proxy subclass around `UserService` and places the resilience behavior into that generated class. That
proxy decides when to:

- retry the original call
- stop waiting because of a timeout
- short-circuit the call through a circuit breaker
- invoke a fallback after a failure

This is why the subclassing rules matter so much:

- in Java, the annotated service class must not be `final`
- in Kotlin, the annotated service class and annotated methods must be `open`

After you run:

```bash
./gradlew clean classes
```

you can inspect the generated proxy here:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-resilient-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/resilient/service/$UserService__AopProxy.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-resilient-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/resilient/service/$UserService__AopProxy.kt
    ```

That file is the most practical place to see how Kora composes the methods introduced above:

- `@Retry`
- `@Fallback`
- `@Timeout`
- `@CircuitBreaker`

The earlier chapters showed the generated fragments directly next to the feature that produced them. Use this final section as a map: when behavior is surprising, open the proxy and search for the
method name you are debugging.

Reading the generated proxy is useful when:

- you want to confirm the real aspect order
- you want to understand why one resilience tool reacts before another
- you are debugging whether the failure came from your method body or from an outer resilience layer
- you want an AI assistant to inspect the actual compiled framework behavior instead of guessing how annotations are applied

## Check Application { #check-app }

Compile the application after adding the annotations and configuration:

```bash
./gradlew clean classes
```

Run the tests:

```bash
./gradlew test
```

Start the application:

```bash
./gradlew run
```

Then exercise the same HTTP endpoints from the HTTP Server guide:

```bash
curl http://localhost:8080/users/1
curl http://localhost:8080/users?page=0&size=10&sort=name
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com"}'
curl -X PUT http://localhost:8080/users/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"John Updated","email":"john.updated@example.com"}'
curl -X DELETE http://localhost:8080/users/1
```

The endpoint paths do not change. Resilience is applied inside the service layer.

## Best Practices { #best-practices }

- Add resilience to the existing service boundary instead of creating separate demo-only methods such as `getUserWithRetry()` or `deleteUserWithTimeout()`.
- Keep the controller contract stable while evolving service behavior.
- Start with a single `default` resilience config, then introduce named configs only when different behaviors are truly needed.
- Remember that Kora supports both AOP-style annotations and imperative managers, and choose the style that keeps the code easiest to reason about.
- Keep Java classes non-`final` and Kotlin classes `open` when you use the annotation-based AOP style.
- Treat fallback as graceful degradation, not as a hidden persistence layer.
- Be conservative with retries and timeouts so the total worst-case latency stays understandable.
- Use custom predicates when some errors are valid business outcomes and should not influence resilience state.
- Inspect the generated proxy source when the runtime behavior of combined annotations feels surprising.

## Summary { #summary }

You started from the CRUD service created in the HTTP Server guide and made the same methods more resilient:

- `getUser()` now retries transient failures
- `createUser()` can fall back to a backup response
- `deleteUser()` is bounded by a timeout
- `updateUser()` is protected by a circuit breaker
- `getUsers()` demonstrates how retry, timeout, and circuit breaker work together

The result is a guide that evolves the same API contract rather than replacing it with separate resilience-only endpoints.

## Key Concepts { #key-concepts }

- Kora resilience can be used both through AOP annotations and through imperative manager APIs.
- Annotation-based resilience on Java requires a non-`final` class, and Kotlin requires an `open` class.
- `@Retry`, `@Timeout`, `@CircuitBreaker`, and `@Fallback` solve different failure modes and should be chosen intentionally.
- `CircuitBreakerPredicate` lets you exclude business errors such as `404` from breaker statistics.
- Annotation order matters when several resilience patterns are combined.
- `minimumRequiredCalls` is the correct circuit breaker key in Kora configuration.
- the generated `$UserService__AopProxy` source shows how Kora actually layers the resilience aspects

## Troubleshooting { #troubleshooting }

**Resilience annotations do not trigger:**

Make sure the Java class is not `final` and the Kotlin class is `open`. Kora uses generated AOP wrappers for the annotation-based style.

**I want to see where retry, timeout, circuit breaker, and fallback are really applied:**

Run:

```bash
./gradlew clean classes
```

Then inspect:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-resilient-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/resilient/service/$UserService__AopProxy.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-resilient-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/resilient/service/$UserService__AopProxy.kt
    ```

That generated file shows the actual wrapper logic around your `UserService` methods and is the best place to verify aspect order and failure flow.

**Retry makes the endpoint slower than expected:**

Retries add delay and can multiply total latency. Check the configured `attempts`, `delay`, and `delayStep`, then estimate the worst-case time budget.

**Circuit breaker never opens:**

Check that your configuration uses `minimumRequiredCalls`, not `minimumNumberOfCalls`, and make sure enough failures happen to cross the threshold.

**Circuit breaker reacts to business errors:**

Add a custom `CircuitBreakerPredicate` and bind it through `failurePredicateName` so business outcomes such as `404 Not Found` do not count as infrastructure failures.

**Fallback is not called:**

Verify the fallback method signature matches the method declaration used in `@Fallback(value = "default", method = "...")`.

**Timeout never fires:**

Make sure the operation actually exceeds the configured timeout duration.

**Gradle hangs or fails unexpectedly:**

Stop Gradle daemons and rerun:

```bash
./gradlew --stop
./gradlew clean classes
```

**Windows shows AccessDeniedException in Gradle cache:**

This usually means another Gradle or Java process is still holding files open. Stop daemons with `./gradlew --stop`, close IDE test runners, and rerun the build.

**Readiness endpoint is not accessible:**

The private HTTP server uses port `8085`. Check:

```text
http://localhost:8085/system/readiness
```

## What's Next? { #whats-next }

- [Observability](observability.md) to measure retry attempts, timeout failures, circuit breaker state changes, and fallback usage.
- [HTTP Client](http-client.md) to apply resilience around outbound calls.
- [HTTP Server Advanced](http-server-advanced.md) and then [HTTP Client Advanced](http-client-advanced.md) if you want advanced outbound examples.
- [Testing with JUnit](testing-junit.md) to test fallback and failure behavior at the component level.
- [Database JDBC](database-jdbc.md) before black-box testing if you want the JDBC-backed end-to-end test path.

## Help { #help }

If you encounter issues:

- compare with [Kora Java Resilient App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-resilient-app) and [Kora Kotlin Resilient App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-resilient-app)
- check the [Resilient documentation](../documentation/resilient.md)
- revisit [HTTP Server](http-server.md) for the base CRUD flow
- revisit [Testing with JUnit](testing-junit.md) for component-level verification patterns
