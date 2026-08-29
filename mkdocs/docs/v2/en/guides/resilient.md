---
search:
  exclude: true
title: Build Resilient CRUD Operations with Retry, Timeout, Circuit Breaker, and Fallback
summary: Extend the HTTP Server guide by applying Kora resilience annotations directly to your existing UserService methods
description: "Step-by-step resilience for a Kora 2.0 service: the io.koraframework:resilient-kora artifact and ResilientModule, typed spec interfaces declared with @RetrySpec, @TimeoutSpec, @CircuitBreakerSpec and @RateLimiterSpec, the @Retryable, @Timeout, @CircuitBreakable, @RateLimited and @Fallback aspects that reference them by class, the resilient configuration section with countBased.windowSize and the circuit breaker type, a CircuitBreakerPredicate bound with @Tag, @Fallback.Reason, and the generated AOP proxy sources."
agent:
  use_when: "Use this file for questions about making a Kora 2.0 service fault tolerant: io.koraframework:resilient-kora, ResilientModule, @RetrySpec / @TimeoutSpec / @CircuitBreakerSpec / @RateLimiterSpec interfaces, @Retryable(Spec.class), @Timeout(Spec.class), @CircuitBreakable(Spec.class), @RateLimited(Spec.class), @Fallback(method) and @Fallback.Reason, CircuitBreakerPredicate and RetryPredicate bound with @Tag(Spec.class), the resilient.* config keys (attempts, delay, delayStep, backoff, jitter, retryBudget, duration, type, countBased.windowSize, minimumRequiredCalls, failureRateThreshold, waitDurationInOpenState, limitForPeriod, limitRefreshPeriod), aspect ordering, and reading the generated $UserService__AopProxy."
tags: resilient, retry, timeout, circuitbreaker, ratelimiter, fallback, http-server, hocon
---

# Resilience Patterns { #resilience-patterns }

This guide introduces resilience patterns for Kora service methods. It covers how retry, timeout, circuit breaker, rate limiter, and fallback annotations wrap application operations, how resilience
configuration controls failure behavior, and how the HTTP API can stay unchanged while service calls become more fault tolerant. You will also see how each pattern protects a different kind of
unstable dependency or operation.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java Resilient App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-resilient-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin Resilient App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-resilient-app).

## What You'll Build { #youll-build }

You will enhance the `UserService` from the HTTP Server guide with:

- `@Retryable` on `getUser()` for transient read failures
- `@Fallback` on `createUser()` for graceful degradation when creation fails
- `@Timeout` on `deleteUser()` to stop hanging delete operations
- `@CircuitBreakable` on `updateUser()` to stop repeated failing updates
- a combined `@CircuitBreakable + @Retryable + @Timeout` chain on `getUsers()`

Every one of those annotations points at a small spec interface that you declare yourself, which is how Kora 2.0 connects a method to a configuration section.

## What You'll Need { #youll-need }

- JDK 25 or later
- Gradle 9+
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
- rate limiter caps how many calls an operation may accept per time window
- fallback provides an alternate result or behavior when the primary path fails

These patterns should not be used blindly. Retrying a non-idempotent write can duplicate work. A timeout that is too short can create false failures. A fallback can hide real outages if it is too
broad. The guide keeps each pattern visible so the trade-off is clear.

### Typed Resilience Specs { #typed-specs }

Kora 2.0 does not attach a resilience policy to a method by name. Each policy is described by a spec interface that you declare in your own code:

- it is an `interface`, never a class
- it extends the contract for the pattern: `Retry`, `Timeouter`, `CircuitBreaker`, or `RateLimiter`
- it carries one annotation, `@RetrySpec`, `@TimeoutSpec`, `@CircuitBreakerSpec`, or `@RateLimiterSpec`, whose value is the configuration path that policy reads

The annotation processor then generates two things for every spec: an implementation `$DefaultRetry_Impl` and a `@Module` named `$DefaultRetry_Module` that publishes it into the graph. The method-level
aspects reference the spec by class, so `@Retryable(DefaultRetry.class)` is checked at compile time. A misspelled policy is now a compilation error rather than a runtime lookup that silently finds
nothing.

The spec interface is also the component you inject when you want to use a policy imperatively. Because `DefaultRetry` extends `Retry`, injecting `DefaultRetry` gives you `retry(...)` and `asState()`
directly. Kora 2.0 has no separate manager objects: the spec is the handle.

### Configuration and Composition { #configuration-composition }

Resilience behavior belongs in configuration as much as in annotations. Thresholds, attempts, delays, and timeout durations often differ between local development and production. The spec interface
names which configuration section applies, while the configuration itself controls how aggressive that policy is.

The guide also shows combined resilience behavior. In real services, a read path may need retry, timeout, and circuit breaker together. The important lesson is to compose these patterns deliberately
around a well-defined operation, then test the behavior as part of the service contract.

The practical flow is:

1. add the resilient module to the application graph
2. declare a spec interface pointing at a configuration path
3. annotate a service method with the matching aspect, one pattern at a time
4. configure thresholds, delays, and timeouts in HOCON
5. simulate failure modes in tests
6. verify that the HTTP contract stays stable while service behavior becomes more defensive

## Dependencies { #dependencies }

Add the resilience dependency to the existing project from the HTTP Server guide.

===! ":fontawesome-brands-java: `Java`"

    Add to the `dependencies` block in `build.gradle`:

    ```groovy
    dependencies {
        // ... existing dependencies ...

        implementation("io.koraframework:resilient-kora")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Add to the `dependencies` block in `build.gradle.kts`:

    ```kotlin
    dependencies {
        // ... existing dependencies ...

        implementation("io.koraframework:resilient-kora")
    }
    ```

The version comes from the `io.koraframework:kora-bom` platform that the HTTP Server guide already applies. No extra annotation processor is required: the resilience processor and the AOP aspects ship
inside the `annotation-processors` (Java) and `symbol-processors` (Kotlin) artifacts you already have.

## Modules { #modules }

First, enable the resilience infrastructure in your Kora application graph. This makes the retry, timeout, circuit breaker, rate limiter, and fallback aspects available to your components.

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/io/koraframework/guide/resilient/Application.java`:

    ```java
    package io.koraframework.guide.resilient;

    import io.koraframework.application.graph.KoraApplication;
    import io.koraframework.common.annotation.KoraApp;
    import io.koraframework.config.hocon.HoconConfigModule;
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule;
    import io.koraframework.json.common.JsonModule;
    import io.koraframework.logging.logback.LogbackModule;
    import io.koraframework.resilient.ResilientModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            UndertowPublicHttpServerModule,
            JsonModule,
            LogbackModule,
            ResilientModule {  // <----- Connected module

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/io/koraframework/guide/resilient/Application.kt`:

    ```kotlin
    package io.koraframework.guide.resilient

    import io.koraframework.application.graph.KoraApplication
    import io.koraframework.common.annotation.KoraApp
    import io.koraframework.config.hocon.HoconConfigModule
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule
    import io.koraframework.json.common.JsonModule
    import io.koraframework.logging.logback.LogbackModule
    import io.koraframework.resilient.ResilientModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        UndertowPublicHttpServerModule,
        JsonModule,
        LogbackModule,
        ResilientModule  // <----- Connected module

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

`ResilientModule` is an umbrella: it extends `CircuitBreakerModule`, `RetryModule`, `TimeoutModule`, `FallbackModule`, and `RateLimiterModule`, and it reads shared telemetry defaults from
`resilient.telemetry`. The modules generated for your own spec interfaces are discovered automatically, because each one is annotated `@Module`.

## Retry { #retry }

`Retry` is the safest place to start because transient failures are most common on reads. A short network glitch, a temporary connection issue, or a brief overload is often resolved if the same
operation is repeated a few moments later.

Retry is useful when:

- failures are short-lived and usually succeed on the next attempt
- the operation is safe to repeat
- the extra latency from retries is acceptable

Use it carefully when:

- the operation changes state and may not be idempotent
- the downstream service is already overloaded and retries would amplify pressure
- the timeout budget is already very small

Because this step uses annotations, the annotated class must still satisfy the AOP rules:

- in Java, the class must not be `final`
- in Kotlin, the class and the annotated methods must be `open`

Start with the configuration, because the spec interface refers to it by path.

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
    3. Linear delay increment added on each subsequent attempt.

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
    3. Linear delay increment added on each subsequent attempt.

Now declare the spec interface that binds this configuration path to a reusable, typed policy.

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/io/koraframework/guide/resilient/service/DefaultRetry.java`:

    ```java
    package io.koraframework.guide.resilient.service;

    import io.koraframework.resilient.retry.Retry;
    import io.koraframework.resilient.retry.annotation.RetrySpec;

    @RetrySpec("resilient.retry.default")
    public interface DefaultRetry extends Retry {

    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/io/koraframework/guide/resilient/service/DefaultRetry.kt`:

    ```kotlin
    package io.koraframework.guide.resilient.service

    import io.koraframework.resilient.retry.Retry
    import io.koraframework.resilient.retry.annotation.RetrySpec

    @RetrySpec("resilient.retry.default")
    interface DefaultRetry : Retry
    ```

The interface stays empty on purpose. Its whole job is to give the configuration path `resilient.retry.default` a type, so that the method aspect and any imperative usage refer to the same policy.

Now annotate the read method:

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/io/koraframework/guide/resilient/service/UserService.java`:

    ```java
    @Component
    public class UserService {

        private final UserRepository userRepository;

        public UserService(UserRepository userRepository) {
            this.userRepository = userRepository;
        }

        @Retryable(DefaultRetry.class)
        public Optional<UserResponse> getUser(String id) {
            return userRepository.findById(id);
        }

        // other methods stay unchanged for now
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/io/koraframework/guide/resilient/service/UserService.kt`:

    ```kotlin
    @Component
    open class UserService(
        private val userRepository: UserRepository,
    ) {

        @Retryable(DefaultRetry::class)
        open fun getUser(id: String): UserResponse? = userRepository.findById(id)

        // other methods stay unchanged for now
    }
    ```

The controller does not need a new endpoint. `GET /users/{userId}` already delegates to `getUser()`, so the resilience behavior is applied automatically at the service boundary.

Retry does not have to react to every exception. Implement `RetryPredicate` and bind it to the spec with `@Tag`, and only the failures you accept will be repeated:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(DefaultRetry.class)
    @Component
    public final class TransientOnlyRetryPredicate implements RetryPredicate {

        @Override
        public boolean isRetryFailure(Throwable throwable) {
            return !(throwable instanceof IllegalArgumentException);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(DefaultRetry::class)
    @Component
    class TransientOnlyRetryPredicate : RetryPredicate {

        override fun isRetryFailure(throwable: Throwable): Boolean =
            throwable !is IllegalArgumentException
    }
    ```

The predicate is optional. Without it every exception is retried, which is the behavior this guide keeps.

Beyond `delay`, `delayStep`, and `attempts`, the retry section also accepts a `backoff` block (`type = EXPONENTIAL`, `multiplier`, `delayMax`), a `jitter` block (`type = NONE` or `FULL`, `ratio`), and
a `retryBudget` block that caps how much of your traffic may consist of retries. Those are worth reaching for once a service retries against a dependency that other callers share.

After compilation, the generated proxy shows that `@Retryable` wraps the original method call directly:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/java/kora-java-guide-resilient-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/resilient/service/$UserService__AopProxy.java
    ```

    ```java
    private Optional<UserResponse> _getUser_AopProxy_RetryKoraAspect(String id) {
        return defaultRetry1.retry(() -> super.getUser(id));
    }

    @Override
    public Optional<UserResponse> getUser(String id) {
        return this._getUser_AopProxy_RetryKoraAspect(id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/kora-kotlin-guide-resilient-app/build/generated/ksp/main/kotlin/io/koraframework/guide/resilient/service/$UserService__AopProxy.kt
    ```

    ```kotlin
    private fun _getUser_AopProxy_RetryKoraAspect(id: String): UserResponse? =
        defaultRetry1.retry(ThrowableCallable { super.getUser(id) })

    override fun getUser(id: String): UserResponse? = _getUser_AopProxy_RetryKoraAspect(id)
    ```

The important part is `defaultRetry1.retry(() -> super.getUser(id))`: Kora generated a retry boundary around your service method, the injected field is your own `DefaultRetry` spec, and your original
code is still the `super.getUser(id)` call inside that boundary.

## Fallback { #fallback }

`Fallback` is about graceful degradation. If the primary path fails, you return a controlled alternative instead of simply propagating the failure.

Fallback is useful when:

- you can return a safe substitute or delayed-processing response
- the user experience is better with a degraded answer than with a hard failure
- you have a clearly defined backup policy

Use it carefully when:

- the fallback hides a serious incident for too long
- the fallback can create inconsistent business state
- the team starts using fallback as a silent substitute for proper persistence or delivery guarantees

`@Fallback` is the one pattern in this guide with no spec interface and no configuration section, because there is nothing to tune: it has a single attribute, `method`, naming the backup method to
call.

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/io/koraframework/guide/resilient/service/UserService.java`:

    ```java
    @Fallback(method = "createUserFallback(request)")
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

    `src/main/kotlin/io/koraframework/guide/resilient/service/UserService.kt`:

    ```kotlin
    @Fallback(method = "createUserFallback(request)")
    open fun createUser(request: UserRequest): UserResponse {
        val generatedId = userRepository.save(request.name, request.email)
        return UserResponse(generatedId, request.name, request.email, LocalDateTime.now())
    }

    // Never do this in real systems: imagine we wrote the request to a file
    // and planned to recreate the user during application startup.
    protected open fun createUserFallback(request: UserRequest): UserResponse =
        UserResponse("pending-file-write", request.name, request.email, LocalDateTime.now())
    ```

The fallback method does not change the controller contract. `POST /users` still returns `UserResponse`, but now the service can degrade gracefully when the primary path fails.

It is important to understand exactly when fallback is called:

1. Kora first invokes the original method.
2. If the original method returns successfully, fallback is not used at all.
3. If the original method throws, Kora decides whether this failure is one the fallback should handle.
4. If it is, Kora calls the method declared in `method = "..."`.
5. The fallback method result becomes the final result returned to the caller.

So fallback is never the primary execution path. It is only a backup path that runs after the original method has already failed.

`createUserFallback(request)` receives the same `request` argument from the failed `createUser(request)` call. That is what the `method = "createUserFallback(request)"` declaration means: the names
inside the parentheses must be parameter names of the annotated method, and Kora passes exactly those, in that order, to the fallback. Referencing a name that is not a parameter is a compilation error.

To restrict which failures reach the fallback, add one parameter annotated `@Fallback.Reason`. It receives the exception that triggered the fallback, and anything that is not an instance of its
declared type is rethrown untouched:

===! ":fontawesome-brands-java: `Java`"

    ```java
    protected UserResponse createUserFallback(UserRequest request, @Fallback.Reason RuntimeException reason) {
        log.warn("Falling back on user creation: {}", reason.getMessage());
        return new UserResponse("pending-file-write", request.name(), request.email(), LocalDateTime.now());
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    protected open fun createUserFallback(request: UserRequest, @Fallback.Reason reason: RuntimeException): UserResponse {
        log.warn("Falling back on user creation: {}", reason.message)
        return UserResponse("pending-file-write", request.name, request.email, LocalDateTime.now())
    }
    ```

The parameter type is not free: it must be `RuntimeException` when the annotated method declares no checked exceptions, `Exception` when it declares some, and `Throwable` when it declares
`throws Throwable`. At most one `@Fallback.Reason` parameter is allowed, and it is not counted among the arguments listed in `method = "..."`.

Fallback is excellent for graceful degradation, but it can also hide real failures if the fallback response looks too much like a real success. That risk matters most for write operations such as
`createUser()`, where a fallback may return something useful to the caller even though the original write did not actually complete.

`@Fallback` supports synchronous methods and `CompletionStage`. A plain `Future` return type and a reactive `Publisher` are rejected at compile time.

After compilation, the generated proxy shows the fallback decision next to the original call:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/java/kora-java-guide-resilient-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/resilient/service/$UserService__AopProxy.java
    ```

    ```java
    private UserResponse _createUser_AopProxy_FallbackKoraAspect(UserRequest request) {
        try {
            return super.createUser(request);
        } catch (Throwable _e) {
            var _fallbackObservation = fallbackTelemetry1.observe();
            try {
                _fallbackObservation.recordExecute(_e);
                return createUserFallback(request);
            } catch (Throwable _fallbackException) {
                _fallbackObservation.observeError(_fallbackException);
                throw _fallbackException;
            } finally {
                _fallbackObservation.end();
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
    guides/kotlin/kora-kotlin-guide-resilient-app/build/generated/ksp/main/kotlin/io/koraframework/guide/resilient/service/$UserService__AopProxy.kt
    ```

    ```kotlin
    private fun _createUser_AopProxy_FallbackKoraAspect(request: UserRequest): UserResponse = try {
      super.createUser(request)
    } catch (_e: Throwable) {
      val _fallbackObservation = fallbackTelemetry1.observe()
      try {
        _fallbackObservation.recordExecute(_e)
        createUserFallback(request)
      } catch (_fallbackException: Throwable) {
        _fallbackObservation.observeError(_fallbackException)
        throw _fallbackException
      } finally {
        _fallbackObservation.end()
      }
    }

    override fun createUser(request: UserRequest): UserResponse =
        _createUser_AopProxy_FallbackKoraAspect(request)
    ```

This makes the fallback rule concrete: Kora first calls `super.createUser(request)`, and only if that call throws does it record the failure and invoke `createUserFallback(request)`. When a
`@Fallback.Reason` parameter is present, an `if (!(_e instanceof RuntimeException)) { throw _e; }` guard appears at the top of the `catch` block.

## Timeout { #timeout }

`Timeout` keeps slow operations from consuming resources indefinitely. Even when a failure is rare, a hanging call can still damage the whole application by tying up threads and request capacity.

Timeout is useful when:

- slow operations are worse than fast failure
- the caller needs a predictable upper bound on latency
- you want retries or circuit breakers to work on top of a bounded execution time

Use it carefully when:

- the timeout is shorter than normal healthy latency
- the operation has side effects that may continue after the caller times out
- you stack retries on top of timeouts without thinking about total worst-case latency

`@Timeout` kept its name in Kora 2.0, but its attribute is now a spec class instead of a policy name. Add the timeout configuration first:

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
    3. Linear delay increment added on each subsequent attempt.
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
    3. Linear delay increment added on each subsequent attempt.
    4. Timeout duration for the protected operation.

Then declare the spec. Note the contract name: the interface extends `Timeouter`, not `Timeout`, because `Timeout` is the aspect annotation.

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/io/koraframework/guide/resilient/service/DefaultTimeouter.java`:

    ```java
    package io.koraframework.guide.resilient.service;

    import io.koraframework.resilient.timeout.Timeouter;
    import io.koraframework.resilient.timeout.annotation.TimeoutSpec;

    @TimeoutSpec("resilient.timeout.default")
    public interface DefaultTimeouter extends Timeouter {

    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/io/koraframework/guide/resilient/service/DefaultTimeouter.kt`:

    ```kotlin
    package io.koraframework.guide.resilient.service

    import io.koraframework.resilient.timeout.Timeouter
    import io.koraframework.resilient.timeout.annotation.TimeoutSpec

    @TimeoutSpec("resilient.timeout.default")
    interface DefaultTimeouter : Timeouter
    ```

Now bound the delete operation:

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/io/koraframework/guide/resilient/service/UserService.java`:

    ```java
    @Timeout(DefaultTimeouter.class)
    public void deleteUser(String id) {
        boolean deleted = userRepository.deleteById(id);
        if (!deleted) {
            throw HttpServerResponseException.of(404, "User not found");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/io/koraframework/guide/resilient/service/UserService.kt`:

    ```kotlin
    @Timeout(DefaultTimeouter::class)
    open fun deleteUser(id: String) {
        if (!userRepository.deleteById(id)) {
            throw HttpServerResponseException.of(404, "User not found")
        }
    }
    ```

The endpoint stays `DELETE /users/{userId}`. Only the service method changes. When the duration elapses, the caller receives a `TimeoutExhaustedException`.

After compilation, the generated proxy shows that the timeout bounds the original delete operation:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/java/kora-java-guide-resilient-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/resilient/service/$UserService__AopProxy.java
    ```

    ```java
    private void _deleteUser_AopProxy_TimeoutKoraAspect(String id) {
        defaultTimeouter1.execute(() -> {
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
    guides/kotlin/kora-kotlin-guide-resilient-app/build/generated/ksp/main/kotlin/io/koraframework/guide/resilient/service/$UserService__AopProxy.kt
    ```

    ```kotlin
    private fun _deleteUser_AopProxy_TimeoutKoraAspect(id: String) {
      defaultTimeouter1.execute(ThrowableRunnable { super.deleteUser(id) })
    }

    override fun deleteUser(id: String) {
      _deleteUser_AopProxy_TimeoutKoraAspect(id)
    }
    ```

The generated code is especially instructive for void methods: Kora wraps `super.deleteUser(id)` in `defaultTimeouter1.execute(...)` and, in Java, returns `null` only to satisfy the callable shape.

## Circuit Breaker { #circuit-breaker }

`CircuitBreaker` protects the system from repeatedly calling a path that is already failing. Once enough failures happen, Kora opens the breaker and fails fast for a while instead of repeatedly doing
expensive work that is likely to fail again.

This pattern is especially useful when the real problem is not in your controller or service logic itself, but in something the method depends on: a database, another HTTP service, a message broker,
or any unstable downstream operation. Without a circuit breaker, every new request keeps trying the same failing path, which wastes threads, increases latency, and often makes the outage worse.

Kora describes circuit breaker as a proxy around a particular method. It watches recent calls and moves through three classic states:

- `CLOSED`: calls are allowed through normally, and Kora counts recent failures inside the configured window
- `OPEN`: once there are enough calls to evaluate (`minimumRequiredCalls`) and the failure rate crosses `failureRateThreshold`, Kora stops calling the protected method and immediately fails fast with `CallNotPermittedException`
- `HALF_OPEN`: after `waitDurationInOpenState` expires, Kora allows only a limited number of probe calls (`permittedCallsInHalfOpenState`) to check whether the dependency has recovered

If those half-open probe calls succeed, the breaker closes again and normal traffic resumes. If one of them fails, the breaker opens again and starts another wait period. That is the main value of the
pattern: give an unhealthy dependency time to recover instead of continuously hammering it, but still periodically test whether it is healthy again.

Circuit breaker is useful when:

- a downstream dependency is unhealthy and repeated calls only waste resources
- fast failure is better than long repeated timeouts
- you want a recovery window before allowing traffic again

Use it carefully when:

- thresholds are tuned too aggressively and healthy traffic gets blocked
- failures that should be treated differently are all grouped together
- the breaker is placed around very cheap, in-process operations where the cost of tripping is higher than the cost of retrying

Kora 2.0 lets you choose how the window is counted through the `type` key, and the shape of the window block follows from that choice:

| `type`           | Window block | What it counts                                                                |
|------------------|--------------|-------------------------------------------------------------------------------|
| `STRIPED_APPROX` | `countBased` | Default. Approximate count across striped counters, cheapest under contention. |
| `FIXED_WINDOW`   | `countBased` | Exact counts over a fixed number of calls. Easiest to reason about in tests.   |
| `RING_BUFFER`    | `countBased` | Exact counts over a sliding ring buffer of the last `windowSize` calls.        |
| `TIME_BASED`     | `timeBased`  | Counts over `windowDuration` split into `sampleCount` buckets, not over calls. |

Because the guide wants a breaker that trips predictably after two failures, it uses `FIXED_WINDOW`.

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
          type = FIXED_WINDOW //(5)!
          countBased.windowSize = 2 //(6)!
          minimumRequiredCalls = 2 //(7)!
          failureRateThreshold = 100 //(8)!
          permittedCallsInHalfOpenState = 1 //(9)!
          waitDurationInOpenState = 200ms //(10)!
        }
      }
    }
    ```

    1. Initial delay before a retry attempt.
    2. Maximum number of retry attempts.
    3. Linear delay increment added on each subsequent attempt.
    4. Timeout duration for the protected operation.
    5. Window implementation. Defaults to `STRIPED_APPROX` when omitted.
    6. Number of calls kept in the circuit breaker window.
    7. Minimum calls required before the circuit breaker evaluates failures.
    8. Failure rate percentage that opens the circuit breaker.
    9. Number of trial calls allowed while the circuit breaker is half-open.
    10. Time the circuit breaker stays open before probing recovery.

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
          type: FIXED_WINDOW #(5)!
          countBased:
            windowSize: 2 #(6)!
          minimumRequiredCalls: 2 #(7)!
          failureRateThreshold: 100 #(8)!
          permittedCallsInHalfOpenState: 1 #(9)!
          waitDurationInOpenState: 200ms #(10)!
    ```

    1. Initial delay before a retry attempt.
    2. Maximum number of retry attempts.
    3. Linear delay increment added on each subsequent attempt.
    4. Timeout duration for the protected operation.
    5. Window implementation. Defaults to `STRIPED_APPROX` when omitted.
    6. Number of calls kept in the circuit breaker window.
    7. Minimum calls required before the circuit breaker evaluates failures.
    8. Failure rate percentage that opens the circuit breaker.
    9. Number of trial calls allowed while the circuit breaker is half-open.
    10. Time the circuit breaker stays open before probing recovery.

Two keys are easy to get wrong. The window size lives under `countBased.windowSize`, not at the top level of the section, and the minimum call count is `minimumRequiredCalls`, not
`minimumNumberOfCalls`. Kora validates the whole block at startup and refuses to build the graph with a message naming the offending key, so a typo fails fast rather than silently disabling the
breaker.

Declare the spec:

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/io/koraframework/guide/resilient/service/DefaultCircuitBreaker.java`:

    ```java
    package io.koraframework.guide.resilient.service;

    import io.koraframework.resilient.circuitbreaker.CircuitBreaker;
    import io.koraframework.resilient.circuitbreaker.annotation.CircuitBreakerSpec;

    @CircuitBreakerSpec("resilient.circuitbreaker.default")
    public interface DefaultCircuitBreaker extends CircuitBreaker {

    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/io/koraframework/guide/resilient/service/DefaultCircuitBreaker.kt`:

    ```kotlin
    package io.koraframework.guide.resilient.service

    import io.koraframework.resilient.circuitbreaker.CircuitBreaker
    import io.koraframework.resilient.circuitbreaker.annotation.CircuitBreakerSpec

    @CircuitBreakerSpec("resilient.circuitbreaker.default")
    interface DefaultCircuitBreaker : CircuitBreaker
    ```

And protect the update method with `@CircuitBreakable`:

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/io/koraframework/guide/resilient/service/UserService.java`:

    ```java
    @CircuitBreakable(DefaultCircuitBreaker.class)
    public UserResponse updateUser(String id, UserRequest request) {
        boolean updated = userRepository.update(id, request.name(), request.email());
        if (!updated) {
            throw HttpServerResponseException.of(404, "User not found");
        }
        return new UserResponse(id, request.name(), request.email(), LocalDateTime.now());
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/io/koraframework/guide/resilient/service/UserService.kt`:

    ```kotlin
    @CircuitBreakable(DefaultCircuitBreaker::class)
    open fun updateUser(id: String, request: UserRequest): UserResponse {
        if (!userRepository.update(id, request.name, request.email)) {
            throw HttpServerResponseException.of(404, "User not found")
        }
        return UserResponse(id, request.name, request.email, LocalDateTime.now())
    }
    ```

Again, the controller stays the same. `PUT /users/{userId}` still calls `updateUser()`, but after enough failures the circuit breaker can open and fail fast.

After compilation, the generated proxy shows the circuit breaker lifecycle around the original update:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/java/kora-java-guide-resilient-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/resilient/service/$UserService__AopProxy.java
    ```

    ```java
    private UserResponse _updateUser_AopProxy_CircuitBreakerKoraAspect(String id, UserRequest request) {
        try {
            defaultCircuitBreaker1.acquire();
            var _result = super.updateUser(id, request);
            defaultCircuitBreaker1.releaseOnSuccess();
            return _result;
        } catch (CallNotPermittedException _e) {
            throw _e;
        } catch (Throwable _e) {
            defaultCircuitBreaker1.releaseOnError(_e);
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
    guides/kotlin/kora-kotlin-guide-resilient-app/build/generated/ksp/main/kotlin/io/koraframework/guide/resilient/service/$UserService__AopProxy.kt
    ```

    ```kotlin
    private fun _updateUser_AopProxy_CircuitBreakerKoraAspect(id: String, request: UserRequest):
        UserResponse = try {
      defaultCircuitBreaker1.acquire()
      val t = super.updateUser(id, request)
      defaultCircuitBreaker1.releaseOnSuccess()
      t
    } catch (e: CallNotPermittedException) {
      throw e
    } catch (e: Throwable) {
      defaultCircuitBreaker1.releaseOnError(e)
      throw e
    }

    override fun updateUser(id: String, request: UserRequest): UserResponse =
        _updateUser_AopProxy_CircuitBreakerKoraAspect(id, request)
    ```

This fragment shows the breaker protocol directly: acquire permission, call the original method, release success on a good result, and release error when the protected method fails. Note that
`CallNotPermittedException` is rethrown without being recorded, because a rejected call is the breaker doing its job, not a new failure to count.

## Circuit Breaker Predicate { #circuit-breaker-predicate }

Now make the circuit breaker smarter for this specific API. We do not want every exception to count as a circuit breaker failure.

In this guide `updateUser()` can fail for two very different reasons:

- the user really does not exist, which is a normal business outcome and should simply return `404 Not Found`
- the update path is genuinely unhealthy, for example because some downstream dependency or internal operation is failing repeatedly

`CircuitBreakerPredicate` lets us separate those cases. We do not want a missing user to push the breaker toward `OPEN`, because that would teach the breaker the wrong lesson about system health. We
only want the breaker to react to failures that actually indicate instability.

Kora calls this predicate whenever the protected method throws an exception. If `isCircuitBreakerFailure` returns `true`, that failure is counted by the circuit breaker. If it returns `false`, the
exception is still returned to the caller, but it does not affect the breaker state.

In Kora 2.0 the predicate is bound to a breaker by tagging it with the spec class. There is no `failurePredicateName` key any more, and no `name()` method to override: the `@Tag` is the binding.

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/io/koraframework/guide/resilient/service/CircuitBreakerFailurePredicate.java`:

    ```java
    package io.koraframework.guide.resilient.service;

    import io.koraframework.common.annotation.Component;
    import io.koraframework.common.annotation.Tag;
    import io.koraframework.http.server.common.response.HttpServerResponseException;
    import io.koraframework.resilient.circuitbreaker.CircuitBreakerPredicate;

    @Tag(DefaultCircuitBreaker.class)
    @Component
    public final class CircuitBreakerFailurePredicate implements CircuitBreakerPredicate {

        @Override
        public boolean isCircuitBreakerFailure(Throwable throwable) {
            if (throwable instanceof HttpServerResponseException exception) {
                return exception.code() >= 500;
            }
            return true;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/io/koraframework/guide/resilient/service/CircuitBreakerFailurePredicate.kt`:

    ```kotlin
    package io.koraframework.guide.resilient.service

    import io.koraframework.common.annotation.Component
    import io.koraframework.common.annotation.Tag
    import io.koraframework.http.server.common.response.HttpServerResponseException
    import io.koraframework.resilient.circuitbreaker.CircuitBreakerPredicate

    @Tag(DefaultCircuitBreaker::class)
    @Component
    class CircuitBreakerFailurePredicate : CircuitBreakerPredicate {

        override fun isCircuitBreakerFailure(throwable: Throwable): Boolean {
            if (throwable is HttpServerResponseException) {
                return throwable.code() >= 500
            }
            return true
        }
    }
    ```

No configuration change is needed. The module generated for `DefaultCircuitBreaker` declares a `@Tag(DefaultCircuitBreaker.class) @Nullable CircuitBreakerPredicate` parameter, so your tagged component
is picked up simply by existing in the graph. Remove the `@Tag` and the predicate is no longer connected to this breaker; remove the component entirely and the breaker falls back to counting every
exception.

The same mechanism binds a `RetryPredicate` to a `@RetrySpec` interface. `@TimeoutSpec` and `@RateLimiterSpec` have no predicate: a timeout is decided by elapsed time and a rate limiter by permits, so
there is nothing to classify.

## Rate Limiter { #rate-limiter }

`RateLimiter` is new in Kora 2.0. Where a circuit breaker reacts to failures, a rate limiter reacts to volume: it caps how many calls an operation may accept in a refresh period and rejects the rest
immediately with `RateLimitExceededException`.

Rate limiter is useful when:

- a downstream dependency publishes a hard quota you must not exceed
- an expensive operation should never be allowed to consume the whole thread pool
- you want back pressure that is predictable rather than emergent

Use it carefully when:

- the limit is shared across instances, since each application instance has its own local limiter
- callers have no sensible way to react to rejection
- the operation is cheap enough that limiting it only adds latency

It follows exactly the same spec pattern. Add the configuration:

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
      ratelimiter {
        default {
          limitForPeriod = 100 //(1)!
          limitRefreshPeriod = 1s //(2)!
        }
      }
    }
    ```

    1. Number of permits granted in each refresh period.
    2. How often the permit budget is replenished.

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      ratelimiter:
        default:
          limitForPeriod: 100 #(1)!
          limitRefreshPeriod: 1s #(2)!
    ```

    1. Number of permits granted in each refresh period.
    2. How often the permit budget is replenished.

Declare the spec and annotate a method:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @RateLimiterSpec("resilient.ratelimiter.default")
    public interface DefaultRateLimiter extends RateLimiter {

    }
    ```

    ```java
    @RateLimited(DefaultRateLimiter.class)
    public List<UserResponse> getUsers(int page, int size, String sort) {
        // ...
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @RateLimiterSpec("resilient.ratelimiter.default")
    interface DefaultRateLimiter : RateLimiter
    ```

    ```kotlin
    @RateLimited(DefaultRateLimiter::class)
    open fun getUsers(page: Int, size: Int, sort: String): List<UserResponse> {
        // ...
    }
    ```

Unlike the other aspects, `@RateLimited` supports only synchronous methods and Kotlin `Flow`. `CompletionStage`, `Future`, and reactive `Publisher` return types are rejected at compile time, because a
permit acquired before an asynchronous call says nothing about when that call actually finishes.

The rest of this guide does not use the rate limiter, so leave `getUsers()` unannotated by it and continue with the combined chain below.

## Combined Pattern { #combined-pattern }

The final step shows how several resilience tools can cooperate on one method. `getUsers()` is a good place to demonstrate this because list operations often become aggregation points: sorting,
paging, cache lookups, remote data fetches, or expensive reads.

This combined chain is useful when:

- you want a hard upper time limit
- you still want a few retries for transient failures
- you also want the breaker to open if the method keeps failing

Use it carefully when:

- you stack too many policies and make the total behavior hard to reason about
- retries plus timeout create a much larger worst-case latency than expected
- failures become harder to debug because several layers can transform the final error path

All three configuration blocks are already in place, so only the method changes:

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/io/koraframework/guide/resilient/service/UserService.java`:

    ```java
    @CircuitBreakable(DefaultCircuitBreaker.class)
    @Retryable(DefaultRetry.class)
    @Timeout(DefaultTimeouter.class)
    public List<UserResponse> getUsers(int page, int size, String sort) {
        return userRepository.findAll().stream()
                .sorted(getComparator(sort))
                .skip((long) page * size)
                .limit(size)
                .toList();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/io/koraframework/guide/resilient/service/UserService.kt`:

    ```kotlin
    @CircuitBreakable(DefaultCircuitBreaker::class)
    @Retryable(DefaultRetry::class)
    @Timeout(DefaultTimeouter::class)
    open fun getUsers(page: Int, size: Int, sort: String): List<UserResponse> =
        userRepository.findAll()
            .sortedWith(getComparator(sort))
            .drop(page * size)
            .take(size)
    ```

The annotation order matters because it defines the order in which Kora applies the aspects around the method. The annotation closest to the method is the innermost layer, and the annotation listed
first becomes the outermost layer.

In this guide the call flow is:

1. `@CircuitBreakable`
2. `@Retryable`
3. `@Timeout`

A very common order that works well for many real systems is:

1. `@Fallback` first, so it is the outermost layer and only sees failures the inner layers could not absorb
2. `@CircuitBreakable` to stop repeated failing calls from continuing forever
3. `@Retryable` to repeat transient failures a limited number of times
4. `@Timeout` to bound one attempt

That order is common because `@Timeout` is the innermost layer and bounds one concrete attempt, `@Retryable` wraps that bounded attempt and repeats it a limited number of times, `@CircuitBreakable`
wraps the retry flow and observes whether the whole operation keeps failing, and `@Fallback` is the outermost layer that only gets a chance to produce a degraded response after the inner layers have
already failed. It is not the only valid order, but it is usually the easiest one to reason about.

Because the breaker sits outside retry, note what the breaker actually counts: one exhausted retry sequence, not each individual attempt. That is normally what you want, but it does mean
`minimumRequiredCalls` counts whole operations, not attempts.

Remember too that retry and circuit breaker can each be narrowed with a tagged predicate, so even in a combined chain they do not have to treat every exception the same way. That matches the
[combination rules in the documentation](../documentation/resilient.md).

After compilation, the generated proxy shows the exact nesting for the combined method:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/java/kora-java-guide-resilient-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/resilient/service/$UserService__AopProxy.java
    ```

    ```java
    private List<UserResponse> _getUsers_AopProxy_TimeoutKoraAspect(int page, int size, String sort) {
        return defaultTimeouter1.execute(() -> super.getUsers(page, size, sort));
    }

    private List<UserResponse> _getUsers_AopProxy_RetryKoraAspect(int page, int size, String sort) {
        return defaultRetry1.retry(() -> _getUsers_AopProxy_TimeoutKoraAspect(page, size, sort));
    }

    private List<UserResponse> _getUsers_AopProxy_CircuitBreakerKoraAspect(int page, int size, String sort) {
        try {
            defaultCircuitBreaker1.acquire();
            var _result = _getUsers_AopProxy_RetryKoraAspect(page, size, sort);
            defaultCircuitBreaker1.releaseOnSuccess();
            return _result;
        } catch (CallNotPermittedException _e) {
            throw _e;
        } catch (Throwable _e) {
            defaultCircuitBreaker1.releaseOnError(_e);
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
    guides/kotlin/kora-kotlin-guide-resilient-app/build/generated/ksp/main/kotlin/io/koraframework/guide/resilient/service/$UserService__AopProxy.kt
    ```

    ```kotlin
    private fun _getUsers_AopProxy_TimeoutKoraAspect(
      page: Int,
      size: Int,
      sort: String,
    ): List<UserResponse> = defaultTimeouter1.execute(ThrowableCallable { super.getUsers(page, size, sort) })

    private fun _getUsers_AopProxy_RetryKoraAspect(
      page: Int,
      size: Int,
      sort: String,
    ): List<UserResponse> = defaultRetry1.retry(ThrowableCallable {
      _getUsers_AopProxy_TimeoutKoraAspect(page, size, sort)
    })

    private fun _getUsers_AopProxy_CircuitBreakerKoraAspect(
      page: Int,
      size: Int,
      sort: String,
    ): List<UserResponse> = try {
      defaultCircuitBreaker1.acquire()
      val t = _getUsers_AopProxy_RetryKoraAspect(page, size, sort)
      defaultCircuitBreaker1.releaseOnSuccess()
      t
    } catch (e: CallNotPermittedException) {
      throw e
    } catch (e: Throwable) {
      defaultCircuitBreaker1.releaseOnError(e)
      throw e
    }
    ```

This is the clearest way to verify aspect order: the public method enters the circuit breaker, the circuit breaker calls retry, retry calls timeout, and timeout finally calls `super.getUsers(...)`.

## Generated Code { #generated-code }

Kora generates two kinds of source for this guide, and they are worth separating.

The spec sources come from `@RetrySpec`, `@TimeoutSpec`, `@CircuitBreakerSpec`, and `@RateLimiterSpec`. For every annotated interface the processor writes an implementation and a module:

```text
$DefaultRetry_Impl.java
$DefaultRetry_Module.java
```

`$DefaultRetry_Impl` extends the framework implementation (`KoraRetry`, `KoraTimeouter`, `KoraCircuitBreaker`, `KoraRateLimiter`) and pins the configuration path you declared. `$DefaultRetry_Module` is
annotated `@Module`, reads that path into a `RetryConfig`, and publishes your interface as a component. This is why nothing has to be registered by hand.

The proxy source comes from the method aspects. Kora does not modify `UserService.java` or `UserService.kt` directly. Instead, it generates a proxy subclass around `UserService` and places the
resilience behavior into that generated class. That proxy decides when to:

- retry the original call
- stop waiting because of a timeout
- short-circuit the call through a circuit breaker
- reject the call because the rate limit is exhausted
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
    guides/java/kora-java-guide-resilient-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/resilient/service/$UserService__AopProxy.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/kora-kotlin-guide-resilient-app/build/generated/ksp/main/kotlin/io/koraframework/guide/resilient/service/$UserService__AopProxy.kt
    ```

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
curl "http://localhost:8080/users?page=0&size=10&sort=name"
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
- Name spec interfaces after the policy they represent, not after the method that uses them, so several methods can share one tuned policy.
- Start with a single `default` configuration section per pattern, then introduce named sections only when different behaviors are truly needed.
- Inject the spec interface when you need imperative control: it already is a `Retry`, `Timeouter`, `CircuitBreaker`, or `RateLimiter`.
- Keep Java classes non-`final` and Kotlin classes `open` when you use the annotation-based AOP style.
- Treat fallback as graceful degradation, not as a hidden persistence layer, and narrow it with `@Fallback.Reason` when only some failures deserve a degraded answer.
- Be conservative with retries and timeouts so the total worst-case latency stays understandable, and consider `retryBudget` when several callers share a dependency.
- Use tagged predicates when some errors are valid business outcomes and should not influence resilience state.
- Inspect the generated proxy source when the runtime behavior of combined annotations feels surprising.

## Summary { #summary }

You started from the CRUD service created in the HTTP Server guide and made the same methods more resilient:

- `getUser()` now retries transient failures
- `createUser()` can fall back to a backup response
- `deleteUser()` is bounded by a timeout
- `updateUser()` is protected by a circuit breaker whose predicate ignores `404` responses
- `getUsers()` demonstrates how retry, timeout, and circuit breaker work together

Each policy is a small typed interface pointing at a configuration path, so the whole resilience surface of the service is visible in four short files.

## Key Concepts { #key-concepts }

- A resilience policy in Kora 2.0 is a spec interface: an interface extending `Retry`, `Timeouter`, `CircuitBreaker`, or `RateLimiter`, annotated with the matching `Spec` annotation whose value is a configuration path.
- The method aspects reference specs by class, so `@Retryable(DefaultRetry.class)`, `@Timeout(DefaultTimeouter.class)`, `@CircuitBreakable(DefaultCircuitBreaker.class)`, and `@RateLimited(DefaultRateLimiter.class)` are compile-time checked.
- `@Fallback` has a single attribute, `method`, and an optional `@Fallback.Reason` parameter that narrows which exceptions it handles.
- Predicates are bound with `@Tag(DefaultCircuitBreaker.class)`: `CircuitBreakerPredicate.isCircuitBreakerFailure` and `RetryPredicate.isRetryFailure`.
- The circuit breaker window lives under `countBased.windowSize` (or `timeBased` for `type = TIME_BASED`), and the minimum call count key is `minimumRequiredCalls`.
- Annotation-based resilience on Java requires a non-`final` class, and Kotlin requires an `open` class with `open` methods.
- Annotation order decides aspect nesting: the annotation nearest the method is innermost.
- The generated `$UserService__AopProxy` source shows how Kora actually layers the resilience aspects.

## Troubleshooting { #troubleshooting }

**Resilience annotations do not trigger:**

Make sure the Java class is not `final` and the Kotlin class and methods are `open`. Kora uses generated AOP wrappers for the annotation-based style.

**`@RetrySpec can only be applied to an interface`:**

The spec must be an `interface`, not a class or a record. The same rule holds for `@TimeoutSpec`, `@CircuitBreakerSpec`, and `@RateLimiterSpec`.

**`@RetrySpec annotated interface must extend Retry`:**

Each spec annotation has one matching contract: `@RetrySpec` needs `Retry`, `@TimeoutSpec` needs `Timeouter`, `@CircuitBreakerSpec` needs `CircuitBreaker`, `@RateLimiterSpec` needs `RateLimiter`.
`Timeouter` is a common slip, because the annotation is called `@Timeout`.

**I want to see where retry, timeout, circuit breaker, and fallback are really applied:**

Run:

```bash
./gradlew clean classes
```

Then inspect:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/java/kora-java-guide-resilient-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/resilient/service/$UserService__AopProxy.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/kora-kotlin-guide-resilient-app/build/generated/ksp/main/kotlin/io/koraframework/guide/resilient/service/$UserService__AopProxy.kt
    ```

That generated file shows the actual wrapper logic around your `UserService` methods and is the best place to verify aspect order and failure flow.

**Retry makes the endpoint slower than expected:**

Retries add delay and can multiply total latency. Check the configured `attempts`, `delay`, and `delayStep`, then estimate the worst-case time budget. If a `backoff` block is present, the growth is
multiplicative rather than linear.

**`CircuitBreaker 'default' property 'countBased' is not configured`:**

Every type except `TIME_BASED` needs a `countBased` block with `windowSize`. If you selected `type = TIME_BASED`, provide a `timeBased` block with `windowDuration` instead.

**Circuit breaker never opens:**

Check that your configuration uses `minimumRequiredCalls` and that `countBased.windowSize` is at least as large as it, then make sure enough failures happen to cross `failureRateThreshold`.

**Circuit breaker reacts to business errors:**

Add a `CircuitBreakerPredicate` component annotated `@Tag(DefaultCircuitBreaker.class)` so business outcomes such as `404 Not Found` do not count as infrastructure failures.

**My predicate is ignored:**

The `@Tag` must name the spec interface, not the contract. `@Tag(CircuitBreaker.class)` will not bind; `@Tag(DefaultCircuitBreaker.class)` will.

**Fallback is not called:**

Verify that the names inside `@Fallback(method = "...")` are parameters of the annotated method and that a method with a matching signature exists in the same class. If the fallback declares a
`@Fallback.Reason` parameter, check that the thrown exception is actually an instance of that parameter's type.

**Timeout never fires:**

Make sure the operation actually exceeds the configured `duration`, and remember that a timeout on a blocking call interrupts the waiter, not necessarily the work itself.

**Gradle hangs or fails unexpectedly:**

Stop Gradle daemons and rerun:

```bash
./gradlew --stop
./gradlew clean classes
```

**Windows shows AccessDeniedException in Gradle cache:**

This usually means another Gradle or Java process is still holding files open. Stop daemons with `./gradlew --stop`, close IDE test runners, and rerun the build.

**Readiness endpoint is not accessible:**

The system HTTP server uses port `8085`. Check:

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

- compare with [Kora Java Resilient App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-resilient-app) and [Kora Kotlin Resilient App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-resilient-app)
- check the [Resilient documentation](../documentation/resilient.md)
- revisit [HTTP Server](http-server.md) for the base CRUD flow
- revisit [Testing with JUnit](testing-junit.md) for component-level verification patterns
