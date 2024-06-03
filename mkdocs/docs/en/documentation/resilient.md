A module for creating a fault-tolerant application using approaches such as *CircuitBreaker, Fallback, Timeout, Retry*
using declarative style annotations.

=== ":fontawesome-brands-java: `Java`"

    When applying aspects, class must not be `final`

=== ":simple-kotlin: `Kotlin`"

    When applying aspects, class must be `open`

## Dependency

=== ":fontawesome-brands-java: `Java`"

    Dependency `build.gradle`:
    ```groovy
    annotationProcessor "ru.tinkoff.kora:annotation-processors"
    implementation "ru.tinkoff.kora:resilient-kora"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends ResilientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Dependency `build.gradle.kts`:
    ```groovy
    ksp("ru.tinkoff.kora:symbol-processors")
    implementation("ru.tinkoff.kora:resilient-kora")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : ResilientModule
    ```

## CircuitBreaker

CircuitBreaker is a proxy that controls the flow to requests of a particular method
and can temporarily stop execution of this method if the method throws many exceptions that meet the specified filter requirements (`CircuitBreakerPredicate`).

The purpose of applying CircuitBreaker is to give the system time to correct the error that caused the failure before allowing the application to attempt the operation again.
The CircuitBreaker pattern provides stability while the system recovers from the failure and reduces the impact on performance.

- `CLOSED`: An application request is redirected to an operation. The proxy keeps a count of the number of recent failures within a set number of operations (`slidingWindowSize`) coming through the proxy, and if the operation call did not complete successfully, the proxy increments this number.
  If the number of requests exceeds the specified minimum ceiling required for counts (`minimumRequiredCalls`) and the number of recent failures exceeds the specified threshold (`failureRateThreshold`) for the specified period of time, the proxy is placed in the `OPEN` state.
- `OPEN`: While in this status, the request from the application immediately terminates with an error and an exception is returned to the application.
  At this point, the proxy starts a wait time timer (`waitDurationInOpenState`), and when the time of this timer expires, the proxy is placed in the `HALF-OPEN` state.
- `HALF-OPEN`: A limited number of requests (`permittedCallsInHalfOpenState`) from the application are allowed to pass through and invoke the operation. If these requests are successful, it is assumed that the error that previously caused the
  failure has been resolved, and the circuit breaker enters the `CLOSED` state (the failure counter is reset). If any request terminates with a fault, the circuit breaker assumes that the
  fault is still present, so it returns to the `OPEN` state and restarts the wait time timer (`waitDurationInOpenState`) to give the system additional time to recover from the failure.

The `Half-Open` state helps prevent requests to the service from growing rapidly. Because once a service is started, it may be able to handle a limited number of requests for some time before full recovery.

Initially it has the `CLOSED` state.

### Declarative usage

=== ":fontawesome-brands-java: `Java`"

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

### Configuration

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
                minimumRequiredCalls = 50 //(2)!
                failureRateThreshold = 50 //(3)!
                waitDurationInOpenState = "25s" //(4)!
                permittedCallsInHalfOpenState = 10 //(5)!
            }
        }
    }
    ```

    1.  Limit the number of requests within which `failureRateThreshold` is calculated to determine the state (**required**)
    2.  Minimum number of queries required to start state calculation (**required**)
    3.  Percentage of unsuccessful requests required to transition to `OPEN` states (has values from *1 to 100*) (**required**)
    4.  Waiting time in `OPEN` status, after which the transition to `HALF-OPEN` status is realized (**required**)
    5.  Required number of requests in `HALF-OPEN` status that must be successful for transition to `CLOSED` status (**required**)


=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      circuitbreaker:
        default:
          slidingWindowSize: 100 #(1)!
          minimumRequiredCalls: 50 #(2)!
          failureRateThreshold: 50 #(3)!
          waitDurationInOpenState: "25s" #(4)!
          permittedCallsInHalfOpenState: 10 #(5)!
    ```

    1.  Limit the number of requests within which `failureRateThreshold` is calculated to determine the state (**required**)
    2.  Minimum number of queries required to start state calculation (**required**)
    3.  Percentage of unsuccessful requests required to transition to `OPEN` states (has values from *1 to 100*) (**required**)
    4.  Waiting time in `OPEN` status, after which the transition to `HALF-OPEN` status is realized (**required**)
    5.  Required number of requests in `HALF-OPEN` status that must be successful for transition to `CLOSED` status (**required**)

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

### Exception filtering

In order to register which errors should be recorded as CircuitBreaker errors, you can override the default filter,
you need to implement `CircuitBreakerPredicate` and register your component in the context and specify in the CircuitBreaker configuration its name returned in the `name()` method.

CircuitBreaker register all errors by default.

=== ":fontawesome-brands-java: `Java`"

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

    1. Name of the predicate from the `name()` method

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      circuitbreaker:
        custom:
          failurePredicateName: "MyPredicate" #(1)!
    ```

    1. Name of the predicate from the `name()` method


### Imperative usage

You can use a breaker in imperative code, for this you need to implement `CircuitBreakerManager` as a dependency and take `CircuitBreaker` from it by the name of the configuration that would be specified in the annotation.
and take `CircuitBreaker` from it by the name of the configuration that would be specified in the annotation:

=== ":fontawesome-brands-java: `Java`"

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

## Retry

Retry - provides the ability to customize the policy of repeated invocation of annotated methods.
It allows you to specify when you want to retry a method, customize retry parameters in case the method threw an exception that meets the specified filter requirements (*RetryPredicate*).

### Declarative usage

=== ":fontawesome-brands-java: `Java`"

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

### Configuration

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
            }
        }
    }
    ```

    1. Initial delay time for the operation at Retry (**required**)
    2. Number of Retry attempts for the operation (**required**)
    3. Delay step which is accumulated in consequence of subsequent Retry attempts (**required**)

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      retry:
        default:
          delay: "100ms" #(1)!
          attempts: 2 #(2)!
          delayStep: "100ms" #(3)!
    ```

    1. Initial delay time for the operation at Retry (**required**)
    2. Number of Retry attempts for the operation (**required**)
    3. Delay step which is accumulated in consequence of subsequent Retry attempts (**required**)

### Exception filtering

In order to register which errors should be recorded as errors on the Retry side, you can override the default filter,
it is required to implement `RetryPredicate` and register its component in the context and specify in the Retry configuration its name returned in the `name()` method.

=== ":fontawesome-brands-java: `Java`"

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
    
    1. Name of the predicate from the `name()` method

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      retry:
        custom:
          failurePredicateName: "MyPredicate" #(1)!
    ```

    1. Name of the predicate from the `name()` method

### Imperative usage

It is possible to use a repeater in imperative code, for this you need to implement `RetryManager` as a dependency and take `Retry` from it by the name of the configuration that would be specified in the annotation.
and take `Retry` from it by the name of the configuration that would be specified in the annotation:

=== ":fontawesome-brands-java: `Java`"

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

## Timeout

Timeout - provides the ability to set the maximum time of operation of the annotated method.

### Declarative usage

=== ":fontawesome-brands-java: `Java`"

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

### Configuration

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
            }
        }
    }
    ```

    1.  The time limit of the operation after which a `TimeoutExhaustedException` will be thrown.

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      timeout:
        default:
          delay: "1s" #(1)!
    ```

    1.  The time limit of the operation after which a `TimeoutExhaustedException` will be thrown.

### Imperative usage

You can use a time limiter in imperative code, for this you need to implement `TimeoutManager` as a dependency and take `Timeout` from it by the name of the configuration that would be specified in the annotation.
and take `Timeout` from it by the name of the configuration that would be specified in the annotation:

=== ":fontawesome-brands-java: `Java`"

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

## Fallback

Fallback - provides an opportunity to specify a method that will be called in the case of
if the exception thrown by the annotated method is satisfied by filters (*FallbackPredicate*).

### Declarative usage

An example of a backup method with no arguments:

=== ":fontawesome-brands-java: `Java`"

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

        fun fallback(): String = "fallback"
    }
    ```

Example for *Fallback* with arguments:

=== ":fontawesome-brands-java: `Java`"

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

### Configuration

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
            }
        }
    }
    ```

    1. Name of the predicate from the `name()` method

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      fallback:
        custom:
          failurePredicateName: "MyPredicate" #(1)!
    ```

    1. Name of the predicate from the `name()` method

### Exception filtering

In order to register which errors should be recorded as Fallback errors, you can override the default filter,
you need to implement `FallbackPredicate` and register your component in the context and specify in the Fallback configuration its name returned in the `name()` method.

=== ":fontawesome-brands-java: `Java`"

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

### Imperative usage

You can use the fallback method in imperative code, for this you need to implement as a dependency `FallbackManager`
and take `Fallback` from it by the name of the configuration that would be specified in the annotation:

=== ":fontawesome-brands-java: `Java`"

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

## Combination

It is possible to combine all of the above annotations simultaneously over a single method.

The order in which the annotations are applied depends on the order in which the annotations are declared.
You can change the order as you wish and combine it with other annotations that are also applied in the order of declaration.

=== ":fontawesome-brands-java: `Java`"

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

1. Applies `@Timeout` which says that the method should not run longer than the time specified in the configuration
2. Applies `@Retry` which will attempt to retry the method the number of times specified in the configuration if the method throws an exception along the chain (including `@Timeout`).
3. Applies `@CircuitBreaker` which will operate according to the configuration and [state](#circuitbreaker) depending on the successful result of the method or if the method threw a chain exception (including `@Timeout` & `@Retry`).
4. Applies `@Fallback` which will call *getFallback* method with argument *arg1* in case the method threw an exception along the chain (including `@Timeout` & `@Retry` & `@CircuitBreaker`)

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

## Signatures

Available signatures for repository methods out of the box:

=== ":fontawesome-brands-java: `Java`"

    The `T` refers to the type of the return value, either `Void`.

    - `T myMethod()`
    - `Optional<T> myMethod()`
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/)
    - `Flux<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/)

=== ":simple-kotlin: `Kotlin`"

    By `T` we mean the type of the return value, either `Void`.

    - `myMethod(): T`
    - `myMethod(): T?`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine)
    - `suspend myMethod(): T?` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine)
    - `myMethod(): Flow<T>` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine)
