---
description: "Explains Kora resilience aspects for circuit breakers, retries, timeouts, fallback methods, telemetry, configuration, and supported signatures. Use when working with @CircuitBreaker, @Retry, @Timeout, @Fallback, CircuitBreakerConfig, RetryConfig, TimeoutConfig, ResilientModule."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora resilience aspects for circuit breakers, retries, timeouts, fallback methods, telemetry, configuration, and supported signatures; key triggers include @CircuitBreaker, @Retry, @Timeout, @Fallback, CircuitBreakerConfig, RetryConfig, TimeoutConfig, ResilientModule."
---

Module for building a fault-tolerant application using mechanisms such as [CircuitBreaker](#circuitbreaker),
[Fallback](#fallback), [Retry](#retry), and [Timeout](#timeout).
These mechanisms can be applied declaratively through aspect annotations or directly through manager components when protection is needed in imperative code.

`ResilientModule` combines `CircuitBreakerModule`, `RetryModule`, `TimeoutModule`, and `FallbackModule`.

For a step-by-step walkthrough before the reference details, see [Resilience](../guides/resilient.md).

## Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:resilient-kora"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends ResilientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:resilient-kora")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : ResilientModule
    ```

## CircuitBreaker { #circuitbreaker }

`CircuitBreaker` is a proxy that controls the request flow to a particular method
and can temporarily prohibit execution of this method if it throws many exceptions matching the configured filter (`CircuitBreakerPredicate`).

The purpose of applying CircuitBreaker is to give the system time to correct the error that caused the failure before allowing the application to attempt the operation again.
The `CircuitBreaker` pattern provides stability while the system recovers from the failure and reduces the impact on performance.
`CircuitBreaker` can be in one of several states: `CLOSED`, `OPEN`, `HALF_OPEN`.

- `CLOSED`: an application request is passed to the protected operation. The proxy counts recent failures within the configured number of operations (`slidingWindowSize`) passing through it, and increments this count when the operation does not complete successfully.
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
    @Component
    public class SomeService {

        @CircuitBreaker("custom")
        public String getValue() {
            throw new IllegalStateException("Ops");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    open class SomeService {

        @CircuitBreaker("custom")
        fun value(): String = throw IllegalStateException("Ops")
    }
    ```

### Configuration { #configuration }

There is a default configuration that is applied to a CircuitBreaker when it is created
and then the named settings of a particular CircuitBreaker are applied to override the default settings.

You can change the default settings for all CircuitBreakers at the same time by changing the `default` configuration.

Example of a complete configuration described in the `CircuitBreakerConfig` class (example values or default values are indicated):

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
        circuitbreaker {
            default {
                slidingWindowSize = 100 //(1)!
                minimumRequiredCalls = 10 //(2)!
                failureRateThreshold = 50 //(3)!
                waitDurationInOpenState = "25s" //(4)!
                permittedCallsInHalfOpenState = 15 //(5)!
                enabled = true //(6)!
                failurePredicateName = "MyPredicate" //(7)!
            }
        }
    }
    ```

    1.  Maximum number of requests used to calculate `failureRateThreshold` and determine the state (`required`, default not specified).
    2.  Minimum number of requests required to start state calculation (`required`, default not specified).
    3.  Percentage of failed requests required to transition to `OPEN`; the value must be from `1` to `100` (`required`, default not specified).
    4.  Waiting time in `OPEN`, after which the transition to `HALF_OPEN` is performed (`required`, default not specified).
    5.  Number of requests in `HALF_OPEN` that must complete successfully to transition to `CLOSED` (`required`, default not specified).
    6.  Enable or disable `CircuitBreaker` (default: `true`).
    7.  Exception filter name from `CircuitBreakerPredicate#name()` (all errors are recorded by default).


=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      circuitbreaker:
        default:
          slidingWindowSize: 100 #(1)!
          minimumRequiredCalls: 10 #(2)!
          failureRateThreshold: 50 #(3)!
          waitDurationInOpenState: "25s" #(4)!
          permittedCallsInHalfOpenState: 15 #(5)!
          enabled: true #(6)!
          failurePredicateName: "MyPredicate" #(7)!
    ```

    1.  Maximum number of requests used to calculate `failureRateThreshold` and determine the state (`required`, default not specified).
    2.  Minimum number of requests required to start state calculation (`required`, default not specified).
    3.  Percentage of failed requests required to transition to `OPEN`; the value must be from `1` to `100` (`required`, default not specified).
    4.  Waiting time in `OPEN`, after which the transition to `HALF_OPEN` is performed (`required`, default not specified).
    5.  Number of requests in `HALF_OPEN` that must complete successfully to transition to `CLOSED` (`required`, default not specified).
    6.  Enable or disable `CircuitBreaker` (default: `true`).
    7.  Exception filter name from `CircuitBreakerPredicate#name()` (all errors are recorded by default).

An example of overriding named settings for a particular CircuitBreaker:

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
        circuitbreaker {
            custom {
                waitDurationInOpenState = "50s"
            }
        }
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      circuitbreaker:
        custom:
          waitDurationInOpenState: "50s"
    ```

Module metrics are described in the [Metrics Reference](metrics.md#resilience) section.

### Exception filtering { #exception-filtering }

In order to register which errors should be recorded as CircuitBreaker errors, you can override the default filter,
you need to implement `CircuitBreakerPredicate` and register your component in the context and specify in the CircuitBreaker configuration its name returned in the `name()` method.

`CircuitBreaker` records all errors by default.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MyFailurePredicate implements CircuitBreakerPredicate {

        @Override
        public String name() {
            return "MyPredicate";
        }

        @Override
        public boolean test(Throwable throwable) {
            return true;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyFailurePredicate : CircuitBreakerPredicate {

        override fun name(): String = "MyPredicate"

        override fun test(throwable: Throwable): Boolean = true
    }
    ```

Configuration:

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
        circuitbreaker {
            custom {
                failurePredicateName = "MyPredicate" //(1)!
            }
        }
    }
    ```

    1. Exception filter name from `CircuitBreakerPredicate#name()` (all errors are recorded by default).

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      circuitbreaker:
        custom:
          failurePredicateName: "MyPredicate" #(1)!
    ```

    1. Exception filter name from `CircuitBreakerPredicate#name()` (all errors are recorded by default).

### Imperative usage { #imperative-usage }

You can use a breaker in imperative code: inject `CircuitBreakerManager`
and get `CircuitBreaker` from it by the configuration name that would be specified in the annotation:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final CircuitBreakerManager manager;

        public SomeService(CircuitBreakerManager manager) {
            this.manager = manager;
        }

        public String doWork() {
            var circuitBreaker = manager.get("custom");
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
    class SomeService(val manager: CircuitBreakerManager) {

        fun doWork(): String {
            val circuitBreaker = manager["custom"]
            return circuitBreaker.accept { doSomeWork() }
        }

        private fun doSomeWork(): String {
            // do some work
        }
    }
    ```

## Retry { #retry }

`Retry` provides the ability to configure repeated invocation of annotated methods.
It allows you to specify when a method should be retried and configure retry parameters when the method throws an exception matching the configured filter (`RetryPredicate`).

### Declarative usage { #declarative-usage-2 }

If all attempts are exhausted, the call fails with `RetryExhaustedException`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @Retry("custom1")
        public String getValue() {
            throw new IllegalStateException("Ops");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    open class SomeService {

        @Retry("custom1")
        fun execute(arg: String): Unit = throw IllegalStateException("Ops")
    }
    ```

### Configuration { #configuration-2 }

There is a `default` configuration that is applied to `Retry` at creation
and then the named settings of a particular `Retry` are applied to override the default settings.

It is possible to change the default settings for all `Retry` at the same time by changing the `default` configuration.

Example of the complete configuration described in the `RetryConfig` class (default or example values are specified):

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
        retry {
            default {
                delay = "100ms" //(1)!
                attempts = 2 //(2)!
                delayStep = "100ms" //(3)!
                enabled = true //(4)!
                failurePredicateName = "MyPredicate" //(5)!
            }
        }
    }
    ```

    1. Initial delay before a repeated call (`required`, default not specified).
    2. Number of retry attempts (`required`, default not specified).
    3. Delay increment for subsequent attempts (default: `0`).
    4. Enable or disable `Retry` (default: `true`).
    5. Exception filter name from `RetryPredicate#name()` (all errors are recorded by default).

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      retry:
        default:
          delay: "100ms" #(1)!
          attempts: 2 #(2)!
          delayStep: "100ms" #(3)!
          enabled: true #(4)!
          failurePredicateName: "MyPredicate" #(5)!
    ```

    1. Initial delay before a repeated call (`required`, default not specified).
    2. Number of retry attempts (`required`, default not specified).
    3. Delay increment for subsequent attempts (default: `0`).
    4. Enable or disable `Retry` (default: `true`).
    5. Exception filter name from `RetryPredicate#name()` (all errors are recorded by default).

### Exception filtering { #exception-filtering-2 }

In order to register which errors should be recorded as errors on the Retry side, you can override the default filter,
it is required to implement `RetryPredicate` and register its component in the context and specify in the Retry configuration its name returned in the `name()` method.

`Retry` records all errors by default.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MyFailurePredicate implements RetryPredicate {

        @Override
        public String name() {
            return "MyPredicate";
        }

        @Override
        public boolean test(Throwable throwable) {
            return true;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyFailurePredicate : RetryPredicate {

        override fun name(): String = "MyPredicate"

        override fun test(throwable: Throwable): Boolean = true
    }
    ```

Configuration:

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
        retry {
            custom {
                failurePredicateName = "MyPredicate" //(1)!
            }
        }
    }
    ```
    
    1. Exception filter name from `RetryPredicate#name()` (all errors are recorded by default).

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      retry:
        custom:
          failurePredicateName: "MyPredicate" #(1)!
    ```

    1. Exception filter name from `RetryPredicate#name()` (all errors are recorded by default).

### Imperative usage { #imperative-usage-2 }

You can use a retrier in imperative code: inject `RetryManager`
and get `Retry` from it by the configuration name that would be specified in the annotation:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final RetryManager manager;

        public SomeService(RetryManager manager) {
            this.manager = manager;
        }

        public String doWork() {
            var retry = manager.get("custom");
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
    class SomeService(private val manager: RetryManager) {

        fun doWork(): String {
            val retry = manager["custom"]
            return retry.retry<String, RuntimeException> { doSomeWork() }
        }

        private fun doSomeWork(): String {
            // do some work
        }
    }
    ```

## Timeout { #timeout }

`Timeout` sets the maximum execution time of the annotated method.

### Declarative usage { #declarative-usage-3 }

If the method does not complete within `duration`, the call fails with `TimeoutExhaustedException`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @Timeout("custom")
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
    @Component
    open class SomeService {

        @Timeout("custom")
        fun value(): String = try {
            Thread.sleep(3000)
            "OK"
        } catch (e: InterruptedException) {
            throw IllegalStateException(e)
        }
    }
    ```

### Configuration { #configuration-3 }

There is a `default` configuration that is applied to the Timeout when it is created
and then the named settings of a particular Timeout are applied to override the default settings.

It is possible to change the default settings for all Timeouts at the same time by changing the `default` configuration.

Example of the complete configuration described in the `TimeoutConfig` class (default or example values are specified):

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
        timeout {
            default {
                duration = "1s" //(1)!
                enabled = true //(2)!
            }
        }
    }
    ```

    1.  Operation time limit after which `TimeoutExhaustedException` will be thrown (`required`, default not specified).
    2.  Enable or disable `Timeout` (default: `true`).

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      timeout:
        default:
          duration: "1s" #(1)!
          enabled: true #(2)!
    ```

    1.  Operation time limit after which `TimeoutExhaustedException` will be thrown (`required`, default not specified).
    2.  Enable or disable `Timeout` (default: `true`).

### Imperative usage { #imperative-usage-3 }

You can use a time limiter in imperative code: inject `TimeoutManager`
and get `Timeout` from it by the configuration name that would be specified in the annotation:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final TimeoutManager manager;

        public SomeService(TimeoutManager manager) {
            this.manager = manager;
        }

        public String doWork() {
            var timeout = manager.get("custom");
            return timeout.execute(this::doSomeWork);
        }

        private String doSomeWork() {
            // do some work
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(private val manager: TimeoutManager) {

        fun doWork(): String {
            val timeout = manager["custom"]
            return timeout.execute<String> { doSomeWork() }
        }

        private fun doSomeWork(): String {
            // do some work
        }
    }
    ```

## Fallback { #fallback }

`Fallback` allows you to specify a method that will be called when an exception thrown by the annotated method matches the configured filters (`FallbackPredicate`).

The fallback method **must match** the return type of the annotated method.

### Declarative usage { #declarative-usage-4 }

An example of a backup method with no arguments:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @Fallback(value = "custom", method = "getFallback()")
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

        @Fallback(value = "custom", method = "getFallback()")
        fun value(): String = "value"

        fun getFallback(): String = "fallback"
    }
    ```

Example for *Fallback* with arguments:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @Fallback(value = "custom", method = "getFallback(arg3, arg1)")     // Passes the arguments of the annotated method in the specified order to the Fallback method
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
        @Fallback(value = "custom", method = "getFallback(arg3, arg1)")
        fun getValue(arg1: String, arg2: Int, arg3: Long): String = "value"

        fun getFallback(argLong: Long, argString: String): String = "fallback"
    }
    ```

### Configuration { #configuration-4 }

There is a `default` configuration that is applied to the Fallback at creation
and then the named settings of a particular Fallback are applied to override the defaults.

It is possible to change the default settings for all Fallbacks at the same time by changing the `default` configuration.

Example of the complete configuration described in the `FallbackConfig` class (default or example values are specified):

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
        fallback {
            custom {
                failurePredicateName = "MyPredicate" //(1)!
                enabled = true //(2)!
            }
        }
    }
    ```

    1. Exception filter name from `FallbackPredicate#name()` (all errors are recorded by default).
    2. Enable or disable `Fallback` (default: `true`).

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      fallback:
        custom:
          failurePredicateName: "MyPredicate" #(1)!
          enabled: true #(2)!
    ```

    1. Exception filter name from `FallbackPredicate#name()` (all errors are recorded by default).
    2. Enable or disable `Fallback` (default: `true`).

### Exception filtering { #exception-filtering-3 }

In order to register which errors should be recorded as Fallback errors, you can override the default filter,
you need to implement `FallbackPredicate` and register your component in the context and specify in the Fallback configuration its name returned in the `name()` method.

`Fallback` records all errors by default.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MyFailurePredicate implements FallbackPredicate {

        @Override
        public String name() {
            return "MyPredicate";
        }

        @Override
        public boolean test(Throwable throwable) {
            return true;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyFailurePredicate : FallbackPredicate {

        override fun name(): String = "MyPredicate"

        override fun test(throwable: Throwable): Boolean = true
    }
    ```

### Imperative usage { #imperative-usage-4 }

You can use the fallback method in imperative code: inject `FallbackManager`
and get `Fallback` from it by the configuration name that would be specified in the annotation:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final FallbackManager manager;

        public SomeService(FallbackManager manager) {
            this.manager = manager;
        }

        public String doWork() {
            var fallback = manager.get("custom");
            return fallback.fallback(this::doSomeWork, () -> "BackupValue");
        }

        private String doSomeWork() {
            // do some work
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(private val manager: FallbackManager) {

        fun doWork(): String {
            val fallback = manager["custom"]
            return fallback.fallback<String>({ doSomeWork() }) { "BackupValue" }
        }

        private fun doSomeWork(): String {
            // do some work
        }
    }
    ```

## Combination { #combination }

It is possible to combine all of the above annotations simultaneously over a single method.

The order in which the annotations are applied depends on the order in which the annotations are declared.
You can change the order as you wish and combine it with other annotations that are also applied in the order of declaration.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @Fallback(value = "default", method = "getFallback(arg1)")   // 4
        @CircuitBreaker("default")                                   // 3
        @Retry("default")                                            // 2
        @Timeout("default")                                          // 1
        public String getValueSync(String arg1) {
            return "result-" + arg1;
        }

        protected String getFallback(String arg1) {                  // 4
            return "fallback-" + arg1;
        }
    }   
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    open class SomeService {

        @Fallback(value = "default", method = "getFallback(arg1)")          // 4
        @CircuitBreaker("default")                                          // 3
        @Retry("default")                                                   // 2
        @Timeout("default")                                                 // 1
        fun getValueSync(arg1: String): String = "result-$arg1"

        protected fun getFallback(arg1: String): String = "fallback-$arg1"  // 4
    }
    ```

In the example above:

1. `@Timeout` is applied and checks that the method does not run longer than the time specified in the configuration.
2. `@Retry` is applied and attempts to repeat method execution the configured number of times if the method throws an exception in the chain, including an exception from `@Timeout`.
3. `@CircuitBreaker` is applied and works according to its configuration and [state](#circuitbreaker), depending on the successful method result or an exception in the chain, including exceptions from `@Timeout` and `@Retry`.
4. `@Fallback` is applied and calls the `getFallback` method with the `arg1` argument if the method throws an exception in the chain, including exceptions from `@Timeout`, `@Retry`, and `@CircuitBreaker`.

Aspect invocation order follows the annotation order on the method: from top to bottom.

Example configuration for all aspects:

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
        circuitbreaker {
            default {
                slidingWindowSize = 1
                minimumRequiredCalls = 1
                failureRateThreshold = 100
                permittedCallsInHalfOpenState = 1
                waitDurationInOpenState = "1s"
            }
        }
        timeout {
            default {
                duration = "300ms"
            }
        }
        retry {
            default {
                delay = "100ms"
                attempts = 2
            }
        }
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      circuitbreaker:
        default:
          slidingWindowSize: 1
          minimumRequiredCalls: 1
          failureRateThreshold: 100
          permittedCallsInHalfOpenState: 1
          waitDurationInOpenState: "1s"
      timeout:
        default:
          duration: "300ms"
      retry:
        default:
          delay: "100ms"
          attempts: 2
    ```

## Signatures { #signatures }

Available method signatures supported by these annotations out of the box:
All four annotations support regular synchronous methods, asynchronous types, and reactive types, but the actual set depends on the language and processor.

===! ":fontawesome-brands-java: `Java`"

    Class must be non `final` in order for aspects to work.

    `T` means the return value type.

    - `void myMethod()`
    - `T myMethod()`
    - `Optional<T> myMethod()`
    - `CompletionStage<T> myMethod()` / `CompletableFuture<T> myMethod()` ([CompletionStage](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletionStage.html))
    - `Mono<T> myMethod()` ([Project Reactor](https://projectreactor.io/docs/core/release/reference/), requires [dependency](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))
    - `Flux<T> myMethod()` ([Project Reactor](https://projectreactor.io/docs/core/release/reference/), requires [dependency](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

=== ":simple-kotlin: `Kotlin`"

    Class must be `open` in order for aspects to work.

    By `T` we mean the type of the return value, either `T?`, or `Unit`.

    - `myMethod(): T`
    - `suspend myMethod(): T` ([Kotlin Coroutines](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine), requires [dependency](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) as `implementation`)
    - `myMethod(): Flow<T>` ([Kotlin Coroutines](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine), requires [dependency](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) as `implementation`)
