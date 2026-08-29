---
description: "Explains Kora resilience aspects built on typed specification interfaces: circuit breakers, retries with backoff/jitter/budget, timeouts, rate limiters, fallback methods, exception filtering, telemetry, configuration, and supported signatures. Use when working with @CircuitBreakable, @Retryable, @Timeout, @RateLimited, @Fallback, @CircuitBreakerSpec, @RetrySpec, @TimeoutSpec, @RateLimiterSpec, ResilientModule."
agent:
  use_when: "Use this file for Kora docs or implementation questions about resilience aspects bound to typed specification interfaces, circuit breaker implementations, retry backoff/jitter/budget, timeouts, rate limiting, fallback methods, exception filtering, telemetry and supported signatures; key triggers include @CircuitBreakable, @CircuitBreakerSpec, @Retryable, @RetrySpec, @Timeout, @TimeoutSpec, @RateLimited, @RateLimiterSpec, @Fallback, Fallback.Reason, CircuitBreaker, CircuitBreakerPredicate, Retry, RetryPredicate, Timeouter, RateLimiter, CallNotPermittedException, RetryExhaustedException, TimeoutExhaustedException, RateLimitExceededException, ResilientException, ResilientModule."
---

Module for building a fault-tolerant application using mechanisms such as [CircuitBreaker](#circuitbreaker),
[Retry](#retry), [Timeout](#timeout), [RateLimiter](#ratelimiter) and [Fallback](#fallback).

Every mechanism except `Fallback` is described by a [specification interface](#specifications): a typed contract that
points at a configuration path. The annotation on the protected method references that interface, so the binding between
a method and its resilience settings is checked by the compiler rather than by a string.

`ResilientModule` combines `CircuitBreakerModule`, `RetryModule`, `TimeoutModule`, `FallbackModule` and `RateLimiterModule`.

For a step-by-step walkthrough before the reference details, see [Resilience](../guides/resilient.md).

## Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:resilient-kora"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends ResilientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:resilient-kora")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : ResilientModule
    ```

The annotation processor (`annotation-processors`) or the `KSP` processor (`symbol-processors`) is required: it both
generates the specification implementations and applies the aspects.

## Specifications { #specifications }

A specification is an interface that extends a resilience contract and carries the annotation with the configuration path:

| Method annotation  | Specification annotation | Contract the interface extends | Package                                        |
|--------------------|--------------------------|--------------------------------|------------------------------------------------|
| `@CircuitBreakable` | `@CircuitBreakerSpec`    | `CircuitBreaker`               | `io.koraframework.resilient.circuitbreaker`     |
| `@Retryable`       | `@RetrySpec`             | `Retry`                        | `io.koraframework.resilient.retry`              |
| `@Timeout`         | `@TimeoutSpec`           | `Timeouter`                    | `io.koraframework.resilient.timeout`            |
| `@RateLimited`     | `@RateLimiterSpec`       | `RateLimiter`                  | `io.koraframework.resilient.ratelimiter`        |
| `@Fallback`        | —                        | —                              | `io.koraframework.resilient.fallback.annotation` |

The method annotations live in the `annotation` sub-package of each contract package, for example
`io.koraframework.resilient.circuitbreaker.annotation.CircuitBreakable`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @CircuitBreakerSpec("resilient.circuitbreaker.pet") //(1)!
    public interface PetCircuitBreaker extends CircuitBreaker { }

    @RetrySpec("resilient.retry.pet")
    public interface PetRetry extends Retry { }

    @TimeoutSpec("resilient.timeout.pet")
    public interface PetTimeouter extends Timeouter { }

    @Component
    public class PetService {

        @CircuitBreakable(PetCircuitBreaker.class) //(2)!
        @Retryable(PetRetry.class)
        @Timeout(PetTimeouter.class)
        public Optional<Pet> findById(long id) {
            return petRepository.findById(id);
        }
    }
    ```

    1.  Full path of the configuration section that describes this instance.
    2.  The aspect is bound to the specification type, not to a string name.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @CircuitBreakerSpec("resilient.circuitbreaker.pet") //(1)!
    interface PetCircuitBreaker : CircuitBreaker

    @RetrySpec("resilient.retry.pet")
    interface PetRetry : Retry

    @TimeoutSpec("resilient.timeout.pet")
    interface PetTimeouter : Timeouter

    @Component
    open class PetService {

        @CircuitBreakable(PetCircuitBreaker::class) //(2)!
        @Retryable(PetRetry::class)
        @Timeout(PetTimeouter::class)
        open fun findById(id: Long): Pet? = petRepository.findById(id)
    }
    ```

    1.  Full path of the configuration section that describes this instance.
    2.  The aspect is bound to the specification type, not to a string name.

What the processor does with a specification:

- generates its implementation and a module that publishes it, and the module is picked up by `@KoraApp` automatically — nothing has to be wired by hand;
- publishes the specification interface itself as an application graph component, so it can be injected for [imperative use](#imperative-usage);
- reads the configuration from exactly the path given in the annotation.

!!! warning "One instance per specification"

    All methods annotated with the same specification type share **one** instance, and therefore one state and one set of
    metrics. Two methods that must not influence each other's circuit breaker state need two specification interfaces
    pointing at two configuration sections.

!!! warning "The configuration path is absolute and is not merged with anything"

    The path in the annotation is the complete path to the section. There is no `default` section that a named section
    inherits from: every value the configuration requires must be present at that exact path. Any path works, including
    one outside the `resilient` prefix — `@CircuitBreakerSpec("payment")` reads the root-level `payment` section.

Common compile-time errors:

- `@CircuitBreakerSpec can only be applied to an interface` — the annotation was placed on a class or a record.
- `@CircuitBreakerSpec annotated interface 'X' must extend io.koraframework.resilient.circuitbreaker.CircuitBreaker` — the interface does not extend the contract.
- `config path can't be blank` — the annotation value is an empty string.
- `@CircuitBreakable on 'X#y()' references an invalid resilient component type` — the class passed to the method annotation does not implement the expected contract.

## CircuitBreaker { #circuitbreaker }

`CircuitBreaker` is a proxy that controls the request flow to a particular method
and can temporarily prohibit execution of this method if it throws many exceptions matching the configured filter.

The purpose of applying CircuitBreaker is to give the system time to correct the error that caused the failure before allowing the application to attempt the operation again.
The `CircuitBreaker` pattern provides stability while the system recovers from the failure and reduces the impact on performance.
`CircuitBreaker` can be in one of several states: `CLOSED`, `OPEN`, `HALF_OPEN`.

- `CLOSED`: an application request is passed to the protected operation. The proxy counts recent failures within the configured number of operations (`countBased.windowSize`) passing through it, and increments this count when the operation does not complete successfully.
  If the number of requests exceeds the minimum amount required for calculation (`minimumRequiredCalls`) and the number of recent failures exceeds the configured threshold (`failureRateThreshold`), the proxy moves to `OPEN`.
- `OPEN`: While in this status, the request from the application immediately terminates with an error and an exception is returned to the application.
  At this point, the proxy starts a wait timer (`waitDurationInOpenState`), and when it expires, the proxy moves to `HALF_OPEN`.
- `HALF_OPEN`: a limited number of requests (`permittedCallsInHalfOpenState`) from the application are allowed to pass through and invoke the operation. If these requests are successful, it is assumed that the error that previously caused the
  failure has been resolved, and `CircuitBreaker` enters the `CLOSED` state (the failure counter is reset). If any request terminates with a failure, `CircuitBreaker` assumes that the
  fault is still present, so it returns to the `OPEN` state and restarts the wait time timer (`waitDurationInOpenState`) to give the system additional time to recover from the failure.

The `HALF_OPEN` state helps prevent requests to the service from growing rapidly: after recovery starts, the service may be able to handle only a limited number of requests for some time.

Initially it has the `CLOSED` state.

### Declarative usage { #declarative-usage }

If `CircuitBreaker` is in the `OPEN` state, the call fails with `CallNotPermittedException`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @CircuitBreakerSpec("resilient.circuitbreaker.custom")
    public interface CustomCircuitBreaker extends CircuitBreaker { }

    @Component
    public class SomeService {

        @CircuitBreakable(CustomCircuitBreaker.class)
        public String getValue() {
            throw new IllegalStateException("Ops");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @CircuitBreakerSpec("resilient.circuitbreaker.custom")
    interface CustomCircuitBreaker : CircuitBreaker

    @Component
    open class SomeService {

        @CircuitBreakable(CustomCircuitBreaker::class)
        open fun value(): String = throw IllegalStateException("Ops")
    }
    ```

### Configuration { #configuration }

The section that `@CircuitBreakerSpec` points at is described by the `CircuitBreakerConfig` class:

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
        circuitbreaker {
            custom {
                type = STRIPED_APPROX //(1)!
                failureRateThreshold = 50 //(2)!
                minimumRequiredCalls = 10 //(3)!
                waitDurationInOpenState = "25s" //(4)!
                permittedCallsInHalfOpenState = 15 //(5)!
                enabled = true //(6)!
                countBased {
                    windowSize = 100 //(7)!
                    stripedApprox {
                        stripes = 16 //(8)!
                    }
                }
            }
        }
    }
    ```

    1.  [Implementation](#circuitbreaker-implementations) of the call window: `STRIPED_APPROX`, `FIXED_WINDOW`, `RING_BUFFER` or `TIME_BASED` (default: `STRIPED_APPROX`).
    2.  Percentage of failed requests required to transition to `OPEN`; the value must be from `1` to `100` (required, no default).
    3.  Minimum number of requests required to start state calculation (required, no default).
    4.  Waiting time in `OPEN`, after which the transition to `HALF_OPEN` is performed (required, no default).
    5.  Number of requests in `HALF_OPEN` that must complete successfully to transition to `CLOSED` (required, no default).
    6.  Enable or disable `CircuitBreaker` (default: `true`).
    7.  Maximum number of requests used to calculate `failureRateThreshold` and determine the state (required for every type except `TIME_BASED`, no default).
    8.  Number of independent counter stripes, from `1` to `64`; used only by `STRIPED_APPROX` (default: `16`).

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      circuitbreaker:
        custom:
          type: STRIPED_APPROX #(1)!
          failureRateThreshold: 50 #(2)!
          minimumRequiredCalls: 10 #(3)!
          waitDurationInOpenState: "25s" #(4)!
          permittedCallsInHalfOpenState: 15 #(5)!
          enabled: true #(6)!
          countBased:
            windowSize: 100 #(7)!
            stripedApprox:
              stripes: 16 #(8)!
    ```

    1.  [Implementation](#circuitbreaker-implementations) of the call window: `STRIPED_APPROX`, `FIXED_WINDOW`, `RING_BUFFER` or `TIME_BASED` (default: `STRIPED_APPROX`).
    2.  Percentage of failed requests required to transition to `OPEN`; the value must be from `1` to `100` (required, no default).
    3.  Minimum number of requests required to start state calculation (required, no default).
    4.  Waiting time in `OPEN`, after which the transition to `HALF_OPEN` is performed (required, no default).
    5.  Number of requests in `HALF_OPEN` that must complete successfully to transition to `CLOSED` (required, no default).
    6.  Enable or disable `CircuitBreaker` (default: `true`).
    7.  Maximum number of requests used to calculate `failureRateThreshold` and determine the state (required for every type except `TIME_BASED`, no default).
    8.  Number of independent counter stripes, from `1` to `64`; used only by `STRIPED_APPROX` (default: `16`).

The `telemetry` key inside the same section overrides the module-wide settings described in [Telemetry](#telemetry).

!!! warning "Constraints"

    The following are validated when the graph is built — violating any of them fails application startup with an explicit
    `CircuitBreaker '<name>' property '<key>' ...` message:
    `countBased` is required for every type except `TIME_BASED` and `timeBased` is required for `TIME_BASED`;
    `failureRateThreshold` must be in range `1..100`; `countBased.windowSize` ≥ `1`; `minimumRequiredCalls` ≥ `1`
    **and** ≤ `countBased.windowSize`; `permittedCallsInHalfOpenState` must be in range `1..65535`;
    `waitDurationInOpenState` must not be negative;
    `countBased.stripedApprox.stripes` must be in range `1..64` and `countBased.windowSize` must not exceed `stripes * 65535`;
    `countBased.windowSize` must not exceed `4194304` for `RING_BUFFER`.

!!! note

    Setting `enabled = false` turns the aspect into a transparent pass-through — the method is invoked directly with no circuit-breaking.
    The remaining values are still read and validated, because the configuration object is built either way.

Module metrics are described in the [Metrics Reference](metrics.md#resilience) section.

### Implementations { #circuitbreaker-implementations }

`type` selects how the `CLOSED`-state statistics are collected. The state machine itself is identical and strictly atomic in all four.

| `type`           | Window                              | Statistics                                              | When to use                                                              |
|------------------|-------------------------------------|---------------------------------------------------------|--------------------------------------------------------------------------|
| `STRIPED_APPROX` | count-based, `countBased.windowSize` | approximate — writes are spread over independent stripes | default; the fastest option on hot, highly concurrent paths               |
| `FIXED_WINDOW`   | count-based, `countBased.windowSize` | fixed counter, reset once the window fills up            | lowest overhead, a single packed counter, no exact history of the last N calls |
| `RING_BUFFER`    | count-based, `countBased.windowSize` | exact history of the last N calls in global order        | when exact count-based semantics matter more than coordination overhead   |
| `TIME_BASED`     | time-based, `timeBased.windowDuration` | latest time window, eventually consistent around bucket rollover | when the load rate varies and a fixed number of calls is not a meaningful window |

`TIME_BASED` ignores `countBased` and reads its own section instead:

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
        circuitbreaker {
            custom {
                type = TIME_BASED
                failureRateThreshold = 50
                minimumRequiredCalls = 10
                waitDurationInOpenState = "25s"
                permittedCallsInHalfOpenState = 15
                timeBased {
                    windowDuration = "10s" //(1)!
                    sampleCount = 16 //(2)!
                    counterStripes = 16 //(3)!
                    counterType = ATOMIC //(4)!
                }
            }
        }
    }
    ```

    1.  Length of the time window the failure rate is computed over (required for `TIME_BASED`, no default).
    2.  Number of buckets the window is split into, from `1` to `1024` (default: `16`).
    3.  Number of independent counter stripes inside a bucket, from `1` to `64` (default: `16`).
    4.  Counter implementation: `ATOMIC` for predictable reset semantics, `LONG_ADDER` for heavy contention at the cost of more approximate resets around bucket boundaries (default: `ATOMIC`).

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      circuitbreaker:
        custom:
          type: TIME_BASED
          failureRateThreshold: 50
          minimumRequiredCalls: 10
          waitDurationInOpenState: "25s"
          permittedCallsInHalfOpenState: 15
          timeBased:
            windowDuration: "10s" #(1)!
            sampleCount: 16 #(2)!
            counterStripes: 16 #(3)!
            counterType: ATOMIC #(4)!
    ```

    1.  Length of the time window the failure rate is computed over (required for `TIME_BASED`, no default).
    2.  Number of buckets the window is split into, from `1` to `1024` (default: `16`).
    3.  Number of independent counter stripes inside a bucket, from `1` to `64` (default: `16`).
    4.  Counter implementation: `ATOMIC` for predictable reset semantics, `LONG_ADDER` for heavy contention at the cost of more approximate resets around bucket boundaries (default: `ATOMIC`).

### Exception filtering { #exception-filtering }

`CircuitBreaker` records all errors as failures by default. There are two ways to change that.

The simplest one is to override `isFailure` right on the specification interface — no extra component and no configuration:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @CircuitBreakerSpec("resilient.circuitbreaker.custom")
    public interface CustomCircuitBreaker extends CircuitBreaker {

        @Override
        default boolean isFailure(Throwable throwable) {
            return !(throwable instanceof HttpServerResponseException e) || e.code() >= 500;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @CircuitBreakerSpec("resilient.circuitbreaker.custom")
    interface CustomCircuitBreaker : CircuitBreaker {

        override fun isFailure(throwable: Throwable): Boolean =
            throwable !is HttpServerResponseException || throwable.code() >= 500
    }
    ```

The second way is a `CircuitBreakerPredicate` component bound to the specification with `@Tag`. It takes precedence over
`isFailure` and is the right choice when the filter itself needs dependencies:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(CustomCircuitBreaker.class) //(1)!
    @Component
    public final class MyFailurePredicate implements CircuitBreakerPredicate {

        @Override
        public boolean isCircuitBreakerFailure(Throwable throwable) { //(2)!
            return !(throwable instanceof HttpServerResponseException e) || e.code() >= 500;
        }
    }
    ```

    1.  Binds the predicate to one specification; without the tag the predicate is not picked up.
    2.  Returning `true` records the exception as a failure.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(CustomCircuitBreaker::class) //(1)!
    @Component
    class MyFailurePredicate : CircuitBreakerPredicate {

        override fun isCircuitBreakerFailure(throwable: Throwable): Boolean = //(2)!
            throwable !is HttpServerResponseException || throwable.code() >= 500
    }
    ```

    1.  Binds the predicate to one specification; without the tag the predicate is not picked up.
    2.  Returning `true` records the exception as a failure.

An exception that the filter rejects is neither counted as a failure nor as a success: it is simply ignored by the breaker
and propagates to the caller unchanged.

### Imperative usage { #imperative-usage }

The specification interface is an ordinary application graph component, so a breaker can be used in imperative code by
injecting it directly:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final CustomCircuitBreaker circuitBreaker;

        public SomeService(CustomCircuitBreaker circuitBreaker) {
            this.circuitBreaker = circuitBreaker;
        }

        public String doWork() {
            return circuitBreaker.accept(this::doSomeWork);
        }

        private String doSomeWork() {
            // do some work
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(private val circuitBreaker: CustomCircuitBreaker) {

        fun doWork(): String {
            return circuitBreaker.accept(ThrowableCallable { doSomeWork() })
        }

        private fun doSomeWork(): String {
            // do some work
        }
    }
    ```

The `accept` methods take `ThrowableCallable<T, E>` or `ThrowableRunnable<E>` from `io.koraframework.resilient.common`,
so the protected code may throw checked exceptions.

To return a fallback value instead of throwing `CallNotPermittedException` when the breaker is `OPEN`, use the `accept` overload that takes a second callable:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public String doWork() {
        return circuitBreaker.accept(this::doSomeWork, () -> "fallback");
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun doWork(): String {
        return circuitBreaker.accept(ThrowableCallable { doSomeWork() }, ThrowableCallable { "fallback" })
    }
    ```

When the protected call cannot be wrapped in a single callable, acquire and release the permit manually.
Call `acquire()` (throws `CallNotPermittedException` when the breaker is `OPEN`, or `HALF_OPEN` with no test calls left) to obtain a permit, then **always** report the outcome with `releaseOnSuccess()` or `releaseOnError(Throwable)` — otherwise the breaker leaks a permit and its accounting becomes incorrect:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public String doWork() {
        circuitBreaker.acquire(); // throws CallNotPermittedException when the call is not permitted
        try {
            var result = doSomeWork();
            circuitBreaker.releaseOnSuccess();
            return result;
        } catch (Throwable e) {
            circuitBreaker.releaseOnError(e);
            throw e;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun doWork(): String {
        circuitBreaker.acquire() // throws CallNotPermittedException when the call is not permitted
        try {
            val result = doSomeWork()
            circuitBreaker.releaseOnSuccess()
            return result
        } catch (e: Throwable) {
            circuitBreaker.releaseOnError(e)
            throw e
        }
    }
    ```

`tryAcquire()` is the non-throwing alternative: it returns `false` when the call is not permitted, so you can branch without catching `CallNotPermittedException`.
When `acquire()` does throw, the current breaker [state](#circuitbreaker) (`OPEN` or `HALF_OPEN`) is available via `CallNotPermittedException#state()`.

## Retry { #retry }

`Retry` provides the ability to configure repeated invocation of annotated methods.
It allows you to specify when a method should be retried and configure retry parameters when the method throws an exception matching the configured filter.

### Declarative usage { #declarative-usage-2 }

If all attempts are exhausted, the call fails with `RetryExhaustedException`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @RetrySpec("resilient.retry.custom")
    public interface CustomRetry extends Retry { }

    @Component
    public class SomeService {

        @Retryable(CustomRetry.class)
        public String getValue() {
            throw new IllegalStateException("Ops");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @RetrySpec("resilient.retry.custom")
    interface CustomRetry : Retry

    @Component
    open class SomeService {

        @Retryable(CustomRetry::class)
        open fun execute(arg: String): Unit = throw IllegalStateException("Ops")
    }
    ```

### Configuration { #configuration-2 }

The section that `@RetrySpec` points at is described by the `RetryConfig` class:

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
        retry {
            custom {
                delay = "100ms" //(1)!
                attempts = 2 //(2)!
                delayStep = "100ms" //(3)!
                enabled = true //(4)!
            }
        }
    }
    ```

    1.  Initial delay before a repeated call (required, no default).
    2.  Number of retry attempts (required, no default).
    3.  Delay increment for subsequent attempts; ignored when `backoff` is configured (default: `0`).
    4.  Enable or disable `Retry` (default: `true`).

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      retry:
        custom:
          delay: "100ms" #(1)!
          attempts: 2 #(2)!
          delayStep: "100ms" #(3)!
          enabled: true #(4)!
    ```

    1.  Initial delay before a repeated call (required, no default).
    2.  Number of retry attempts (required, no default).
    3.  Delay increment for subsequent attempts; ignored when `backoff` is configured (default: `0`).
    4.  Enable or disable `Retry` (default: `true`).

The optional `backoff`, `jitter` and `retryBudget` sections are described in [Backoff and jitter](#retry-backoff) and
[Retry budget](#retry-budget), and the `telemetry` key overrides the settings from [Telemetry](#telemetry).

!!! warning "Constraints & delay progression"

    `delay` and `attempts` are required and startup fails without them.
    `attempts` counts the retries **after** the initial call, so `attempts = 2` allows up to `3` executions in total, and
    `attempts = 0` turns the aspect into a transparent pass-through.
    With no `backoff` section each retry waits `delayStep` (default `0`) longer than the previous one, so the delays are
    `delay`, `delay + delayStep`, `delay + 2·delayStep`, … .

!!! note

    Setting `enabled = false` turns `@Retryable` into a transparent pass-through (the method runs once).
    A retry that runs out of attempts throws `RetryExhaustedException` whose `getCause()` is the last failure and whose
    suppressed exceptions are all the earlier failures.

### Backoff and jitter { #retry-backoff }

The `backoff` section replaces the linear `delayStep` progression with an exponential one, and `jitter` spreads the
delays of concurrent callers so they do not retry in lockstep:

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
        retry {
            custom {
                delay = "100ms"
                attempts = 4
                backoff {
                    type = EXPONENTIAL //(1)!
                    multiplier = 2.0 //(2)!
                    delayMax = "5s" //(3)!
                }
                jitter {
                    type = FULL //(4)!
                    ratio = 1.0 //(5)!
                }
            }
        }
    }
    ```

    1.  Backoff strategy; the only supported value is `EXPONENTIAL` (default: `EXPONENTIAL`).
    2.  Multiplier applied on every attempt, must be greater than `0` (default: `2.0`).
    3.  Upper bound for the computed delay (optional, unbounded by default).
    4.  Jitter strategy: `NONE` disables it, `FULL` randomizes the delay (default: `NONE`).
    5.  Fraction of the computed delay that may be subtracted, must be in range `0..1` (default: `1.0`).

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      retry:
        custom:
          delay: "100ms"
          attempts: 4
          backoff:
            type: EXPONENTIAL #(1)!
            multiplier: 2.0 #(2)!
            delayMax: "5s" #(3)!
          jitter:
            type: FULL #(4)!
            ratio: 1.0 #(5)!
    ```

    1.  Backoff strategy; the only supported value is `EXPONENTIAL` (default: `EXPONENTIAL`).
    2.  Multiplier applied on every attempt, must be greater than `0` (default: `2.0`).
    3.  Upper bound for the computed delay (optional, unbounded by default).
    4.  Jitter strategy: `NONE` disables it, `FULL` randomizes the delay (default: `NONE`).
    5.  Fraction of the computed delay that may be subtracted, must be in range `0..1` (default: `1.0`).

With the settings above the computed delay for attempt `n` is `delay * multiplier^(n-1)`, capped at `delayMax`:
`100ms`, `200ms`, `400ms`, `800ms`. Jitter then picks the actual delay uniformly from
`[computed - computed * ratio, computed]`, so `ratio = 1.0` means anything from `0` up to the computed delay.

### Retry budget { #retry-budget }

A retry budget caps how much extra load retries may add. It is a token bucket: every retry takes one token, every
successful call returns `ratio` tokens, and when the bucket is empty the retry is refused and the original exception is
rethrown as is — without waiting and without `RetryExhaustedException`.

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
        retry {
            custom {
                delay = "100ms"
                attempts = 3
                retryBudget {
                    enabled = true //(1)!
                    ratio = 0.1 //(2)!
                    tokensMax = 100 //(3)!
                    tokensInitial = 10 //(4)!
                    minTokensPerSecond = 0.0 //(5)!
                }
            }
        }
    }
    ```

    1.  Enable or disable the budget (default: `true`).
    2.  Tokens added per successful call — `0.1` allows roughly one retry per ten successful calls (default: `0.1`).
    3.  Upper bound of the bucket (default: `100`).
    4.  Number of tokens the bucket starts with, must not exceed `tokensMax` (default: `10`).
    5.  Guaranteed refill rate that applies even without successful calls (default: `0.0`).

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      retry:
        custom:
          delay: "100ms"
          attempts: 3
          retryBudget:
            enabled: true #(1)!
            ratio: 0.1 #(2)!
            tokensMax: 100 #(3)!
            tokensInitial: 10 #(4)!
            minTokensPerSecond: 0.0 #(5)!
    ```

    1.  Enable or disable the budget (default: `true`).
    2.  Tokens added per successful call — `0.1` allows roughly one retry per ten successful calls (default: `0.1`).
    3.  Upper bound of the bucket (default: `100`).
    4.  Number of tokens the bucket starts with, must not exceed `tokensMax` (default: `10`).
    5.  Guaranteed refill rate that applies even without successful calls (default: `0.0`).

!!! note

    The budget is off unless the `retryBudget` section is declared. Declaring it with `enabled = false` also leaves it off.

### Exception filtering { #exception-filtering-2 }

`Retry` retries on every error by default, and the two ways to narrow that down mirror the
[circuit breaker](#exception-filtering): override `isFailure` on the specification, or register a `RetryPredicate`
component tagged with the specification. The tagged component wins when both are present.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @RetrySpec("resilient.retry.custom")
    public interface CustomRetry extends Retry {

        @Override
        default boolean isFailure(Throwable throwable) {
            return throwable instanceof IOException;
        }
    }

    @Tag(CustomRetry.class)
    @Component
    public final class MyRetryPredicate implements RetryPredicate {

        @Override
        public boolean isRetryFailure(Throwable throwable) {
            return throwable instanceof IOException;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @RetrySpec("resilient.retry.custom")
    interface CustomRetry : Retry {

        override fun isFailure(throwable: Throwable): Boolean = throwable is IOException
    }

    @Tag(CustomRetry::class)
    @Component
    class MyRetryPredicate : RetryPredicate {

        override fun isRetryFailure(throwable: Throwable): Boolean = throwable is IOException
    }
    ```

An exception the filter rejects is rethrown immediately, without further attempts and without being wrapped in
`RetryExhaustedException`.

### Imperative usage { #imperative-usage-2 }

Inject the specification interface and call it directly:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final CustomRetry retry;

        public SomeService(CustomRetry retry) {
            this.retry = retry;
        }

        public String doWork() {
            return retry.retry(this::doSomeWork);
        }

        private String doSomeWork() {
            // do some work
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(private val retry: CustomRetry) {

        fun doWork(): String {
            return retry.retry(ThrowableCallable { doSomeWork() })
        }

        private fun doSomeWork(): String {
            // do some work
        }
    }
    ```

To return a fallback value instead of throwing `RetryExhaustedException` once all attempts are used up, pass a second callable:

===! ":fontawesome-brands-java: `Java`"

    ```java
    return retry.retry(this::doSomeWork, () -> "fallback");
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    return retry.retry(ThrowableCallable { doSomeWork() }, ThrowableCallable { "fallback" })
    ```

For asynchronous imperative code there is an overload that retries a `Supplier<CompletionStage<T>>` and returns a `CompletionStage<T>`, scheduling each attempt after the configured delay without blocking the calling thread.

#### Manual retry state { #manual-retry-state }

For full control over the retry loop, use `retry.asState()`, which returns a `Retry.RetryState`.
It is `AutoCloseable`, so wrap it in try-with-resources (Java) or `use` (Kotlin) to record metrics on completion.
On each caught exception call `onException(Throwable)`, which returns a `RetryStatus`:

- `ACCEPTED` — another attempt is allowed; call `doDelay()` (blocks for the current backoff) and retry.
- `REJECTED` — the exception was rejected by the filter or the [retry budget](#retry-budget) is empty, and it must not be retried; rethrow it.
- `EXHAUSTED` — all attempts are used up; throw `RetryExhaustedException` (or fall back to a default).

`getAttempts()` / `getAttemptsMax()` report progress and `getDelayNanos()` returns the next delay.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public String doWork() {
        try (var state = retry.asState()) {
            while (true) {
                try {
                    return doSomeWork();
                } catch (Exception e) {
                    switch (state.onException(e)) {
                        case ACCEPTED -> state.doDelay();   // wait, then loop and retry
                        case REJECTED -> throw e;           // not retryable
                        case EXHAUSTED -> throw new RetryExhaustedException("custom", state.getAttemptsMax(), e);
                    }
                }
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun doWork(): String {
        retry.asState().use { state ->
            while (true) {
                try {
                    return doSomeWork()
                } catch (e: Exception) {
                    when (state.onException(e)) {
                        Retry.RetryState.RetryStatus.ACCEPTED -> state.doDelay()   // wait, then loop and retry
                        Retry.RetryState.RetryStatus.REJECTED -> throw e           // not retryable
                        Retry.RetryState.RetryStatus.EXHAUSTED -> throw RetryExhaustedException("custom", state.attemptsMax, e)
                    }
                }
            }
        }
    }
    ```

## Timeout { #timeout }

`Timeout` sets the maximum execution time of the annotated method.
For synchronous methods the call is offloaded to a virtual thread and interrupted once the limit is reached; for Kotlin
`suspend` functions the coroutine is cancelled by `withTimeout`.

### Declarative usage { #declarative-usage-3 }

If the method does not complete within `duration`, the call fails with `TimeoutExhaustedException`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @TimeoutSpec("resilient.timeout.custom")
    public interface CustomTimeouter extends Timeouter { }

    @Component
    public class SomeService {

        @Timeout(CustomTimeouter.class)
        public String getValue() {
            try {
                Thread.sleep(3000);
                return "OK";
            } catch (InterruptedException e) {
                throw new IllegalStateException(e);
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @TimeoutSpec("resilient.timeout.custom")
    interface CustomTimeouter : Timeouter

    @Component
    open class SomeService {

        @Timeout(CustomTimeouter::class)
        open fun value(): String = try {
            Thread.sleep(3000)
            "OK"
        } catch (e: InterruptedException) {
            throw IllegalStateException(e)
        }
    }
    ```

### Configuration { #configuration-3 }

The section that `@TimeoutSpec` points at is described by the `TimeoutConfig` class:

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
        timeout {
            custom {
                duration = "1s" //(1)!
                enabled = true //(2)!
            }
        }
    }
    ```

    1.  Operation time limit after which `TimeoutExhaustedException` will be thrown (required, no default).
    2.  Enable or disable `Timeout` (default: `true`).

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      timeout:
        custom:
          duration: "1s" #(1)!
          enabled: true #(2)!
    ```

    1.  Operation time limit after which `TimeoutExhaustedException` will be thrown (required, no default).
    2.  Enable or disable `Timeout` (default: `true`).

The `telemetry` key inside the same section overrides the module-wide settings described in [Telemetry](#telemetry).

!!! note

    `duration` is required and startup fails without it.
    Setting `enabled = false` turns `@Timeout` into a transparent pass-through — the method runs with no time limit.
    An exception thrown by the method before the limit is reached propagates unchanged, including checked exceptions.

### Imperative usage { #imperative-usage-3 }

Inject the specification interface and call it directly:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final CustomTimeouter timeouter;

        public SomeService(CustomTimeouter timeouter) {
            this.timeouter = timeouter;
        }

        public String doWork() {
            return timeouter.execute(this::doSomeWork);
        }

        private String doSomeWork() {
            // do some work
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(private val timeouter: CustomTimeouter) {

        fun doWork(): String {
            return timeouter.execute(ThrowableCallable { doSomeWork() })
        }

        private fun doSomeWork(): String {
            // do some work
        }
    }
    ```

`Timeouter` also exposes an `execute` overload for operations that return nothing, and `timeout()` returns the configured `Duration`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    Duration limit = timeouter.timeout();  // configured duration
    timeouter.execute(this::cleanup);      // void operation, throws TimeoutExhaustedException on timeout
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val limit: Duration = timeouter.timeout()           // configured duration
    timeouter.execute(ThrowableRunnable { cleanup() })  // void operation, throws TimeoutExhaustedException on timeout
    ```

## RateLimiter { #ratelimiter }

`RateLimiter` caps how many times a method may be called within a period. The limiter is a fixed-window counter: it hands
out `limitForPeriod` permits, and the counter is reset to that value on the first call after `limitRefreshPeriod` has
elapsed. Acquiring a permit never blocks — a call that finds no permit left fails immediately with `RateLimitExceededException`.

### Declarative usage { #declarative-usage-5 }

===! ":fontawesome-brands-java: `Java`"

    ```java
    @RateLimiterSpec("resilient.ratelimiter.custom")
    public interface CustomRateLimiter extends RateLimiter { }

    @Component
    public class SomeService {

        @RateLimited(CustomRateLimiter.class)
        public String getValue() {
            return "OK";
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @RateLimiterSpec("resilient.ratelimiter.custom")
    interface CustomRateLimiter : RateLimiter

    @Component
    open class SomeService {

        @RateLimited(CustomRateLimiter::class)
        open fun value(): String = "OK"
    }
    ```

### Configuration { #configuration-5 }

The section that `@RateLimiterSpec` points at is described by the `RateLimiterConfig` class:

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
        ratelimiter {
            custom {
                limitForPeriod = 100 //(1)!
                limitRefreshPeriod = "1s" //(2)!
                enabled = true //(3)!
            }
        }
    }
    ```

    1.  Number of calls permitted within one period (required, no default).
    2.  Length of the period after which the permits are replenished (required, no default).
    3.  Enable or disable `RateLimiter` (default: `true`).

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      ratelimiter:
        custom:
          limitForPeriod: 100 #(1)!
          limitRefreshPeriod: "1s" #(2)!
          enabled: true #(3)!
    ```

    1.  Number of calls permitted within one period (required, no default).
    2.  Length of the period after which the permits are replenished (required, no default).
    3.  Enable or disable `RateLimiter` (default: `true`).

The `telemetry` key inside the same section overrides the module-wide settings described in [Telemetry](#telemetry).

!!! note

    Setting `enabled = false` turns `@RateLimited` into a transparent pass-through — every call is permitted.
    The limiter is per application instance: with several replicas the effective limit is `limitForPeriod` multiplied by the number of replicas.

### Imperative usage { #imperative-usage-5 }

Inject the specification interface and call it directly:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final CustomRateLimiter rateLimiter;

        public SomeService(CustomRateLimiter rateLimiter) {
            this.rateLimiter = rateLimiter;
        }

        public String doWork() {
            return rateLimiter.execute(this::doSomeWork); //(1)!
        }

        public boolean doWorkIfPermitted() {
            if (!rateLimiter.tryAcquire()) { //(2)!
                return false;
            }
            doSomeWork();
            return true;
        }

        private String doSomeWork() {
            // do some work
        }
    }
    ```

    1.  Acquires a permit and runs the operation, throwing `RateLimitExceededException` when the limit is exhausted.
    2.  Non-throwing alternative: returns `false` instead of raising an exception.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(private val rateLimiter: CustomRateLimiter) {

        fun doWork(): String {
            return rateLimiter.execute(ThrowableCallable { doSomeWork() }) //(1)!
        }

        fun doWorkIfPermitted(): Boolean {
            if (!rateLimiter.tryAcquire()) { //(2)!
                return false
            }
            doSomeWork()
            return true
        }

        private fun doSomeWork(): String {
            // do some work
        }
    }
    ```

    1.  Acquires a permit and runs the operation, throwing `RateLimitExceededException` when the limit is exhausted.
    2.  Non-throwing alternative: returns `false` instead of raising an exception.

`acquire()` takes a permit without running anything and throws `RateLimitExceededException` when there is none left.

## Fallback { #fallback }

`Fallback` specifies a method that is called when the annotated method fails.
Unlike the other mechanisms it has no specification interface and no configuration section of its own: the fallback method
is the whole contract.

The fallback method **must match** the return type of the annotated method and **must be declared in the same class**.

### Declarative usage { #declarative-usage-4 }

An example of a backup method with no arguments:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @Fallback(method = "getFallback()")
        public String getValue() {
            return "value";
        }

        protected String getFallback() {
            return "fallback";
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    open class SomeService {

        @Fallback(method = "getFallback()")
        open fun value(): String = "value"

        fun getFallback(): String = "fallback"
    }
    ```

Example for *Fallback* with arguments:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @Fallback(method = "getFallback(arg3, arg1)")     // Passes the arguments of the annotated method in the specified order to the Fallback method
        public String getValue(String arg1, Integer arg2, Long arg3) {
            return "value";
        }

        protected String getFallback(Long argLong, String argString) {
            return "fallback";
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    open class SomeService {

        // Passes the arguments of the annotated method in the specified order to the Fallback method
        @Fallback(method = "getFallback(arg3, arg1)")
        open fun getValue(arg1: String, arg2: Int, arg3: Long): String = "value"

        fun getFallback(argLong: Long, argString: String): String = "fallback"
    }
    ```

The reference is validated at compile time. Common errors:

- `@Fallback method reference '…' has invalid syntax` — the value must look like `name()` or `name(arg1, arg2)`.
- `@Fallback method reference '…' uses unknown source arguments` — an argument that the annotated method does not declare.
- `@Fallback method '…' was not found` — no method with that name in the same class.
- `@Fallback method '…' does not match requested signature` — the fallback method must accept exactly the referenced arguments plus an optional `@Fallback.Reason` parameter.

### Exception filtering { #exception-filtering-3 }

By default the fallback is invoked for every `Throwable`. Adding a single `@Fallback.Reason` parameter to the fallback
method both delivers the exception that triggered the fallback and narrows down what triggers it: an exception that is not
an instance of the declared parameter type is rethrown and the fallback is not called.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @Fallback(method = "getFallback()")
        public String getValue() {
            throw new IllegalStateException("Ops");
        }

        protected String getFallback(@Fallback.Reason RuntimeException reason) { //(1)!
            return "fallback: " + reason.getMessage();
        }
    }
    ```

    1.  At most one such parameter is allowed and it is not part of the argument list in `method = "..."`.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    open class SomeService {

        @Fallback(method = "getFallback()")
        open fun value(): String = throw IllegalStateException("Ops")

        fun getFallback(@Fallback.Reason reason: RuntimeException): String = //(1)!
            "fallback: " + reason.message
    }
    ```

    1.  At most one such parameter is allowed and it is not part of the argument list in `method = "..."`.

In Java the parameter type must match what the annotated method can throw: `RuntimeException` when it declares no
`throws`, `Exception` when it declares checked exceptions, and `Throwable` when it declares `throws Throwable`.
A narrower type is reported as a compile-time error, so use a plain `instanceof` check inside the fallback for finer filtering.

## Telemetry { #telemetry }

Logging, metrics and tracing are configured per mechanism under `resilient.telemetry`, and every specification may
override the module-wide values through a `telemetry` key inside its own configuration section:

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
        telemetry {
            circuitBreaker { //(1)!
                logging.enabled = false //(2)!
                metrics {
                    enabled = false //(3)!
                    tags { "service" = "pets" } //(4)!
                }
                tracing {
                    enabled = false //(5)!
                    attributes { "component" = "resilient" } //(6)!
                }
            }
            retry {}
            timeout {}
            fallback {}
            rateLimiter {}
        }
        circuitbreaker {
            custom {
                telemetry.metrics.enabled = true //(7)!
            }
        }
    }
    ```

    1.  Sections: `circuitBreaker`, `retry`, `timeout`, `fallback`, `rateLimiter`.
    2.  Enable logging for the mechanism (default: `false`).
    3.  Enable metrics for the mechanism (default: `false`).
    4.  Extra tags added to every metric of the mechanism (default: empty).
    5.  Enable tracing for the mechanism (default: `false`).
    6.  Extra attributes added to every span of the mechanism (default: empty).
    7.  Per-specification override; unset keys fall back to the values under `resilient.telemetry`.

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      telemetry:
        circuitBreaker: #(1)!
          logging:
            enabled: false #(2)!
          metrics:
            enabled: false #(3)!
            tags:
              service: "pets" #(4)!
          tracing:
            enabled: false #(5)!
            attributes:
              component: "resilient" #(6)!
        retry: {}
        timeout: {}
        fallback: {}
        rateLimiter: {}
      circuitbreaker:
        custom:
          telemetry:
            metrics:
              enabled: true #(7)!
    ```

    1.  Sections: `circuitBreaker`, `retry`, `timeout`, `fallback`, `rateLimiter`.
    2.  Enable logging for the mechanism (default: `false`).
    3.  Enable metrics for the mechanism (default: `false`).
    4.  Extra tags added to every metric of the mechanism (default: empty).
    5.  Enable tracing for the mechanism (default: `false`).
    6.  Extra attributes added to every span of the mechanism (default: empty).
    7.  Per-specification override; unset keys fall back to the values under `resilient.telemetry`.

The whole `resilient.telemetry` block is optional — omitting it leaves every mechanism with the defaults above.
The metric names are listed in the [Metrics Reference](metrics.md#resilience).

## Combination { #combination }

It is possible to combine all of the above annotations simultaneously over a single method.

The order in which the annotations are applied depends on the order in which the annotations are declared.
You can change the order as you wish and combine it with other annotations that are also applied in the order of declaration.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @Fallback(method = "getFallback(arg1)")           // 4
        @CircuitBreakable(CustomCircuitBreaker.class)     // 3
        @Retryable(CustomRetry.class)                     // 2
        @Timeout(CustomTimeouter.class)                   // 1
        public String getValueSync(String arg1) {
            return "result-" + arg1;
        }

        protected String getFallback(String arg1) {       // 4
            return "fallback-" + arg1;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    open class SomeService {

        @Fallback(method = "getFallback(arg1)")             // 4
        @CircuitBreakable(CustomCircuitBreaker::class)      // 3
        @Retryable(CustomRetry::class)                      // 2
        @Timeout(CustomTimeouter::class)                    // 1
        open fun getValueSync(arg1: String): String = "result-$arg1"

        protected fun getFallback(arg1: String): String = "fallback-$arg1"  // 4
    }
    ```

In the example above:

1. `@Timeout` is applied and checks that the method does not run longer than the time specified in the configuration.
2. `@Retryable` is applied and attempts to repeat method execution the configured number of times if the method throws an exception in the chain, including an exception from `@Timeout`.
3. `@CircuitBreakable` is applied and works according to its configuration and [state](#circuitbreaker), depending on the successful method result or an exception in the chain, including exceptions from `@Timeout` and `@Retryable`.
4. `@Fallback` is applied and calls the `getFallback` method with the `arg1` argument if the method throws an exception in the chain, including exceptions from `@Timeout`, `@Retryable`, and `@CircuitBreakable`.

Aspect invocation order follows the annotation order on the method: from top to bottom, so the topmost annotation is the outermost wrapper.
`@RateLimited` fits into the same chain and is usually placed above `@CircuitBreakable`, so rejected calls never reach the breaker.

Example configuration for all aspects:

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
        circuitbreaker {
            custom {
                type = FIXED_WINDOW
                countBased.windowSize = 1
                minimumRequiredCalls = 1
                failureRateThreshold = 100
                permittedCallsInHalfOpenState = 1
                waitDurationInOpenState = "1s"
            }
        }
        timeout {
            custom {
                duration = "300ms"
            }
        }
        retry {
            custom {
                delay = "100ms"
                attempts = 2
            }
        }
        ratelimiter {
            custom {
                limitForPeriod = 100
                limitRefreshPeriod = "1s"
            }
        }
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      circuitbreaker:
        custom:
          type: FIXED_WINDOW
          countBased:
            windowSize: 1
          minimumRequiredCalls: 1
          failureRateThreshold: 100
          permittedCallsInHalfOpenState: 1
          waitDurationInOpenState: "1s"
      timeout:
        custom:
          duration: "300ms"
      retry:
        custom:
          delay: "100ms"
          attempts: 2
      ratelimiter:
        custom:
          limitForPeriod: 100
          limitRefreshPeriod: "1s"
    ```

## Exceptions { #exceptions }

All resilience exceptions extend `io.koraframework.resilient.exception.ResilientException` (a `RuntimeException`), which exposes `name()` — the simple name of the specification interface that raised it.

| Exception                    | Thrown by                                                                                                        | Additional API                                                                          |
|------------------------------|------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| `ResilientException`         | base type for all of the below                                                                                   | `name()`                                                                                 |
| `CallNotPermittedException`  | `@CircuitBreakable` / `CircuitBreaker#acquire()` when the breaker is `OPEN`, or `HALF_OPEN` with no test calls left | `state()` returns the `CircuitBreaker.State` (`OPEN` / `HALF_OPEN`)                       |
| `RetryExhaustedException`    | `@Retryable` / `Retry#retry(...)` when every attempt failed                                                       | `name()`; message carries the number of attempts, the last failure is the `getCause()`, earlier failures are suppressed |
| `TimeoutExhaustedException`  | `@Timeout` / `Timeouter#execute(...)` when the method exceeds `duration`                                          | `name()`                                                                                  |
| `RateLimitExceededException` | `@RateLimited` / `RateLimiter#acquire()` when no permit is left in the current period                             | `name()`                                                                                  |

Each exception lives in the `exception` sub-package of its mechanism, for example `io.koraframework.resilient.circuitbreaker.exception.CallNotPermittedException`.

**Description** — resilience aspects signal failure by throwing one of these unchecked exceptions out of the protected method.

**Causes**

- `CallNotPermittedException` — the circuit breaker is short-circuiting calls because the failure rate reached `failureRateThreshold`; the call was rejected without invoking the method.
- `RetryExhaustedException` — the method kept throwing a retryable exception until `attempts` was reached; the underlying failure is available via `getCause()`.
- `TimeoutExhaustedException` — the method did not complete within `duration`.
- `RateLimitExceededException` — `limitForPeriod` calls were already permitted within the current `limitRefreshPeriod`.

**Recommendations**

- Catch `ResilientException` to handle any resilience failure uniformly, or catch the concrete type when the handling differs.
- When aspects are [combined](#combination), a downstream aspect's exception propagates up the chain: e.g. a `TimeoutExhaustedException` from `@Timeout` is observed by `@Retryable`, then `@CircuitBreakable`, and finally `@Fallback`. Prefer a `@Fallback` method or an imperative fallback over turning these into user-facing errors.
- An exception rejected by an [exception filter](#exception-filtering) is rethrown as is and never wrapped, so callers still see the original type.

Handling example:

===! ":fontawesome-brands-java: `Java`"

    ```java
    try {
        return service.getValue();
    } catch (CallNotPermittedException e) {
        log.warn("CircuitBreaker '{}' is {}", e.name(), e.state());
        return cachedValue();
    } catch (TimeoutExhaustedException | RetryExhaustedException | RateLimitExceededException e) {
        log.warn("Resilient '{}' failed", e.name(), e);
        return cachedValue();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    try {
        return service.value()
    } catch (e: CallNotPermittedException) {
        log.warn("CircuitBreaker '{}' is {}", e.name(), e.state())
        return cachedValue()
    } catch (e: ResilientException) { // TimeoutExhaustedException, RetryExhaustedException, RateLimitExceededException, ...
        log.warn("Resilient '{}' failed", e.name(), e)
        return cachedValue()
    }
    ```

## Signatures { #signatures }

Available method signatures supported by these annotations out of the box.
Reactive return types (`Mono`, `Flux` and any other `Publisher`) are not supported by any of the resilience aspects.

===! ":fontawesome-brands-java: `Java`"

    Class must be non `final` in order for aspects to work.

    `T` means the return value type.

    - `void myMethod()`
    - `T myMethod()`
    - `Optional<T> myMethod()`
    - `CompletionStage<T> myMethod()` / `CompletableFuture<T> myMethod()` ([CompletionStage](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/CompletionStage.html)) — supported by every annotation except `@RateLimited`

=== ":simple-kotlin: `Kotlin`"

    Class must be `open` in order for aspects to work.

    By `T` we mean the type of the return value, either `T?`, or `Unit`.

    - `myMethod(): T`
    - `suspend myMethod(): T` ([Kotlin Coroutines](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine), requires [dependency](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) as `implementation`)
    - `myMethod(): Flow<T>` ([Kotlin Coroutines](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine), requires [dependency](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) as `implementation`)

    `CompletionStage` and `CompletableFuture` are not supported in Kotlin — use `suspend` instead.

Applying an aspect to an unsupported return type is a compile-time error of the form
`@Retryable cannot be applied to '…' because return type '…' is not supported by this aspect`.
