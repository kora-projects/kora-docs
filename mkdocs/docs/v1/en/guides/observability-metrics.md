---
search:
  exclude: true
title: Metrics with Kora
summary: Build focused Micrometer metrics for a Kora HTTP service, including framework metrics, business counters, timers, private metrics endpoints, and practical verification.
tags: observability, metrics, micrometer, meter-registry, counters, timers, monitoring
---

# Metrics with Kora { #observability-metrics-kora }

This guide focuses only on metrics. You will take the HTTP server application and add operational and business metrics: a private `/metrics` endpoint, the Micrometer module, a custom
`MetricsService`, a user creation counter, and a timer around the creation operation.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java Observability App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-observability-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin Observability App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-observability-app).

## What You Will Build { #youll-build }

You will add:

- `MetricsModule`
- a private `/metrics` endpoint on the management port
- a custom `MetricsService`
- the `user.creation.duration` timer
- the `user.creation.total` counter with the `email.provider` tag
- a practical check that metrics appear after a business operation

## What You Will Need { #youll-need }

- JDK 17 or later
- Gradle 7+
- Docker, if you want to run the black-box smoke test locally
- A text editor or IDE
- Completed [HTTP Server Guide](http-server.md)

## Prerequisites { #prerequisites }

!!! note "Required Foundation"

    This guide assumes you have completed **[HTTP Server Guide](http-server.md)** and already have the HTTP controllers, DTOs, repository, service, and configuration from that guide in place.

    If you haven't completed the HTTP server guide yet, do that first, because this observability guide keeps that HTTP surface and layers telemetry on top of it.

## Overview { #overview }

Metrics are numbers that an application exposes to the outside world. Imagine a small dashboard next to the service: it shows how many requests passed through, how many users were created, how long operations took, and how much runtime capacity is being used. One number rarely tells the full story, but a set of numbers can show that the application became slower, started failing more often, or suddenly received more traffic.

Kora as a framework already provides the main system and module metrics out of the box. When you connect the relevant modules, Kora emits metrics for supported parts of the application: HTTP servers, clients, databases, messaging, runtime infrastructure, and other integrations. These signals are exposed in a standard observability shape compatible with the OpenTelemetry approach and monitoring backends.

The key idea is that metrics are not only for the framework and not only for infrastructure. The framework can count technical things, such as HTTP requests or runtime measurements. But only your code knows domain meaning. Kora cannot automatically know that `createUser()` means a user was created, so the business metric belongs in the service layer.

This guide uses three main pieces:

- `MetricsModule` enables metrics support in the Kora graph
- `MeterRegistry` is the shared place where application code registers custom metrics
- Micrometer provides metric types such as `Counter` and `Timer`

Think of Micrometer as a universal notebook for numbers. You tell it: "here is a counter with this name" or "here is a timer with this name", and Micrometer stores measurements in a format monitoring systems can read. Kora puts that notebook into the application graph so `MetricsService` can receive `MeterRegistry` through the constructor.

### Signal Model { #signal-model }

Counter counts events. It is like a mechanical door counter: every time the event happens, the value goes up. In this guide, `user.creation.total` increments after successful user creation and receives the `email.provider` tag extracted from the email domain. This helps answer questions such as:

- how many user creation operations happened in the last five minutes
- whether business activity suddenly stopped
- whether operation frequency changed after a release
- which email providers appear most often among new users

Timer measures duration. It is like a stopwatch around an operation, but it stores a stream of measurements instead of one value. A timer can later show average duration, maximums, percentiles, and measurement count. In this guide, `user.creation.duration` shows how long user creation takes.

Counter and Timer are more useful together than separately. Counter says "the operation happened"; timer says "the operation took this long". If the counter grows and the timer becomes worse, the operation still works but became slow. If the counter stops growing, requests may no longer reach that operation at all.

### Tools { #tools }

`MetricsModule` is the Kora module that adds metrics infrastructure to the application. After it is connected, `MeterRegistry` becomes available as a normal graph dependency. This matters because metrics are not created through global state or random static fields. They live in the DI graph like a repository or HTTP client.

`MeterRegistry` is the registration point. When `MetricsService` calls `Counter.builder(...).register(meterRegistry)`, it says: "create or find a metric with this name and description". After that, the counter can be incremented and the timer can record durations.

The `/metrics` endpoint is the window through which external monitoring reads collected values. In this guide it lives on the private port `8085`. That is intentional: metrics can expose internal service shape, so normal users should not receive them through the public API.

### Metrics Boundary { #metrics-boundary }

A good business metric is placed where the business meaning exists. For user creation, that place is `UserService`, not the HTTP controller. The controller knows that an HTTP request arrived. The service knows that the application is performing the creation operation.

In this guide, `MetricsService` wraps the action through `recordUserCreation()`. This shape is useful for three reasons:

- metric names live in one component
- the service method stays readable
- the timer measures exactly the callback passed to it

Do not add a metric to every line of code. Metrics should answer questions, not become noise. If a metric does not help make a decision, configure an alert, or explain service behavior, it is probably too early to add it.

Tags are another important point. Tags are useful when they split measurements by stable categories: operation status, command type, or a client name from a small fixed set. Tags are dangerous when they contain user ids, emails, raw paths, or other unbounded values. This is called high cardinality, and it quickly breaks metric storage.

The practical result is simple: connect the Kora module, register clear business metrics through `MeterRegistry`, and verify them on the private `/metrics` endpoint. Metrics then become part of the application instead of separate monitoring magic.

## Dependencies { #dependencies }

===! ":fontawesome-brands-java: `Java`"

    Add the Micrometer module:

    ```groovy
    dependencies {
        // ... existing dependencies from the HTTP server guide ...

        implementation("ru.tinkoff.kora:micrometer-module")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Add the Micrometer module:

    ```kotlin
    dependencies {
        // ... existing dependencies from the HTTP server guide ...

        implementation("ru.tinkoff.kora:micrometer-module")
    }
    ```

## Modules { #modules }

Add `MetricsModule` to the application graph.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            MetricsModule,  // <----- Connected module
            UndertowHttpServerModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        MetricsModule,  // <----- Connected module
        UndertowHttpServerModule
    ```

`MetricsModule` adds `MeterRegistry` to the graph. Use it to register custom counters, timers, gauges, and other meters.

## Configuration { #config }

Expose metrics on the private management port. The public API remains on `8080`; operational endpoints use `8085`.

```hocon title="src/main/resources/application.conf"
httpServer {
  publicApiHttpPort = 8080
  privateApiHttpPort = 8085
  privateApiHttpMetricsPath = "/metrics"
}
```

This shape matters in production: business clients should not see internal metrics, while Prometheus, Kubernetes, or another monitoring agent should have a stable scrape path.

## Metrics Service { #metrics-service }

Create `MetricsService` gradually. First add a simple duration metric, then add a counter, and then make that counter smarter with a tag based on the email provider.

### Timer { #timer }

Start with `MeterRegistry` and one shared `Timer`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MetricsService {

        private final MeterRegistry meterRegistry;
        private final Timer userCreationTimer;

        public MetricsService(MeterRegistry meterRegistry) {
            this.meterRegistry = meterRegistry;
            this.userCreationTimer = Timer.builder("user.creation.duration")
                    .description("Time taken to create users")
                    .register(meterRegistry);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MetricsService(
        private val meterRegistry: MeterRegistry
    ) {
        private val userCreationTimer = Timer.builder("user.creation.duration")
            .description("Time taken to create users")
            .register(meterRegistry)
    }
    ```

`MeterRegistry` is where metrics are registered. `Timer` measures user creation duration. It is shared for all email providers because duration is one overall signal: how long user creation takes.

#### Duration Buckets { #duration-buckets }

Duration metrics are useful not only for an average value. In production you usually care about questions like "how many operations are faster than 100 ms?", "did the 95th percentile become worse?", or "should an alert fire because too many requests crossed the target latency?". For that, Micrometer can publish bucketed measurements through service level objectives.

Update the timer with a few practical latency boundaries:

===! ":fontawesome-brands-java: `Java`"

    ```java
    this.userCreationTimer = Timer.builder("user.creation.duration")
            .description("Time taken to create users")
            .serviceLevelObjectives(
                    Duration.ofMillis(50),
                    Duration.ofMillis(100),
                    Duration.ofMillis(250),
                    Duration.ofMillis(500))
            .register(meterRegistry);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    private val userCreationTimer = Timer.builder("user.creation.duration")
        .description("Time taken to create users")
        .serviceLevelObjectives(
            Duration.ofMillis(50),
            Duration.ofMillis(100),
            Duration.ofMillis(250),
            Duration.ofMillis(500),
        )
        .register(meterRegistry)
    ```

These values are not universal. They are examples of business latency targets: 50 ms is excellent, 100 ms is healthy, 250 ms is already worth watching, and 500 ms is a clear warning for such a small operation. Pick boundaries that match your own service.

### Operation Wrapper { #operation-wrapper }

Now add a simple wrapper without `email`. It only measures duration and returns the operation result:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public <T> T recordUserCreation(Callable<T> action) {
        try {
            return this.userCreationTimer.recordCallable(action);
        } catch (RuntimeException e) {
            throw e;
        } catch (Exception e) {
            throw new IllegalStateException("Failed to record user creation metrics", e);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun <T> recordUserCreation(action: Callable<T>): T {
        return try {
            userCreationTimer.recordCallable(action)
        } catch (e: RuntimeException) {
            throw e
        } catch (e: Exception) {
            throw IllegalStateException("Failed to record user creation metrics", e)
        }
    }
    ```

At this point the metric answers only "how long did the operation take?". If the operation fails, the exception still goes out normally. Metrics should not change business behavior.

### Counter { #counter }

Now add a second metric: a counter for successful user creation. A plain counter would answer only "how many users were created?". Often you want a little more context, for example which email providers appear most often among new users.

Tags solve this. A tag is a short stable label attached to a metric. For example, the same `user.creation.total` metric can have different `email.provider` tag values: `gmail.com`, `example.com`, `company.org`.

The tag must be stable and have a limited number of possible values. Good tag values usually look like `route`, `provider`, `status`, `result`, or `operation`. Bad tag values are full emails, user ids, request ids, raw paths, and other values that can grow almost without limit.

Kora framework metrics follow the same rule. HTTP metrics use stable values such as method, route template, host, scheme, status code, and error type. A route template like `/users/{id}` is safe; a raw path like `/users/128734` would create a new series for each user. The domain after `@` follows the same idea: it does not identify the concrete user and is useful for grouping.

#### Dynamic Tag { #dynamic-tag }

Now create the counter with the `email.provider` tag:

===! ":fontawesome-brands-java: `Java`"

    ```java
    private Counter userCreationCounter(String emailProvider) {
        return Counter.builder("user.creation.total")
                .description("Total number of users created")
                .tag("email.provider", emailProvider)
                .register(this.meterRegistry);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    private fun userCreationCounter(emailProvider: String): Counter {
        return Counter.builder("user.creation.total")
            .description("Total number of users created")
            .tag("email.provider", emailProvider)
            .register(meterRegistry)
    }
    ```

The monitoring backend can now show both the total number of creations and groups by provider. After requests with `alice@example.com` and `bob@gmail.com`, you can see separate series for `example.com` and `gmail.com`.

To do that, teach the service to extract the provider from `email`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    private static String emailProvider(String email) {
        int at = email.indexOf('@');
        if (at < 0 || at == email.length() - 1) {
            return "unknown";
        }
        return email.substring(at + 1).toLowerCase(Locale.ROOT);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    private fun emailProvider(email: String): String {
        val provider = email.substringAfter('@', missingDelimiterValue = "")
        return provider.ifBlank { "unknown" }.lowercase()
    }
    ```

If the email is invalid or the domain is missing, return `unknown`. That is better than creating an empty tag or failing inside metric code.

#### Cache Metrics { #metric-caching }

There is one more production habit worth copying from Kora metrics internals: do not rebuild the same tagged meter on every request. If a metric has no dynamic tags, the best shape is to create it once in the constructor and keep it as a `final` field, like `userCreationTimer`. Then the hot request path only calls `record(...)` or `increment()`, while meter construction has already happened when the component was created.

Dynamic tags are different. The `email.provider` value is known only while processing a concrete user, so one shared `final Counter` is not enough: `gmail.com`, `example.com`, and `company.org` need different time series of the same metric. But that still does not mean the counter should be rebuilt on every request. The right shape is to create the counter once for every new provider and then reuse it.

Inside Micrometer, a meter is identified by its name and the full tag set. When code calls `Counter.builder(...).tag(...).register(meterRegistry)`, Micrometer builds a meter id, checks the registry, and returns an existing meter or registers a new one. Even though the registry can avoid duplicate meters, calling the builder on every request still creates the builder, description, tags, and registration path again. That is unnecessary work on the hottest part of the application.

That is why Kora builds a key from stable tag values, registers the meter once with `computeIfAbsent`, and then only updates the already registered metric. For HTTP metrics, that key can include method, route template, host, scheme, status code, and error type. In this business example the key is simpler: only `email.provider`.

Do the same for `email.provider`. Add a small cache of counters:

===! ":fontawesome-brands-java: `Java`"

    ```java
    private final ConcurrentHashMap<String, Counter> userCreationCounters = new ConcurrentHashMap<>();

    private Counter userCreationCounter(String emailProvider) {
        return this.userCreationCounters.computeIfAbsent(emailProvider, provider ->
                Counter.builder("user.creation.total")
                        .description("Total number of users created")
                        .tag("email.provider", provider)
                        .register(this.meterRegistry));
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    private val userCreationCounters = ConcurrentHashMap<String, Counter>()

    private fun userCreationCounter(emailProvider: String): Counter {
        return userCreationCounters.computeIfAbsent(emailProvider) { provider ->
            Counter.builder("user.creation.total")
                .description("Total number of users created")
                .tag("email.provider", provider)
                .register(meterRegistry)
        }
    }
    ```

The metric is still created lazily: the `gmail.com` counter appears only when a successful operation with a Gmail address happens. After that, the same counter is reused. On later requests with `gmail.com`, `computeIfAbsent` simply returns the already registered `Counter`, and the code immediately calls `increment()`.

You do not need this cache for every meter. If the tag set is fixed, keep the meter as a service field. Use the cache when a tag comes from runtime data, but that data is still low-cardinality and useful for grouping. This keeps the tag boundary visible, avoids repeated builder/registration work on every call, and matches the way Kora handles system HTTP metrics.

### Final Operation Wrapper { #final-wrapper }

The last step is to update the operation wrapper. It now accepts `email`, measures duration with the timer, and increments the tagged counter after successful execution.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public <T> T recordUserCreation(String email, Callable<T> action) {
        try {
            var result = this.userCreationTimer.recordCallable(action);
            this.userCreationCounter(emailProvider(email)).increment();
            return result;
        } catch (RuntimeException e) {
            throw e;
        } catch (Exception e) {
            throw new IllegalStateException("Failed to record user creation metrics", e);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun <T> recordUserCreation(email: String, action: Callable<T>): T {
        return try {
            val result = userCreationTimer.recordCallable(action)
            userCreationCounter(emailProvider(email)).increment()
            result
        } catch (e: RuntimeException) {
            throw e
        } catch (e: Exception) {
            throw IllegalStateException("Failed to record user creation metrics", e)
        }
    }
    ```

The order matters: the counter increments only after a successful operation. This way `user.creation.total` counts created users, not every attempt to call the method.

### Complete Service { #complete-service }

The final component stays small, and every part now has a clear job:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MetricsService {

        private final MeterRegistry meterRegistry;
        private final Timer userCreationTimer;
        private final ConcurrentHashMap<String, Counter> userCreationCounters = new ConcurrentHashMap<>();

        public MetricsService(MeterRegistry meterRegistry) {
            this.meterRegistry = meterRegistry;
            this.userCreationTimer = Timer.builder("user.creation.duration")
                    .description("Time taken to create users")
                    .serviceLevelObjectives(
                            Duration.ofMillis(50),
                            Duration.ofMillis(100),
                            Duration.ofMillis(250),
                            Duration.ofMillis(500))
                    .register(meterRegistry);
        }

        public <T> T recordUserCreation(String email, Callable<T> action) {
            try {
                var result = this.userCreationTimer.recordCallable(action);
                this.userCreationCounter(emailProvider(email)).increment();
                return result;
            } catch (RuntimeException e) {
                throw e;
            } catch (Exception e) {
                throw new IllegalStateException("Failed to record user creation metrics", e);
            }
        }

        private Counter userCreationCounter(String emailProvider) {
            return this.userCreationCounters.computeIfAbsent(emailProvider, provider ->
                    Counter.builder("user.creation.total")
                            .description("Total number of users created")
                            .tag("email.provider", provider)
                            .register(this.meterRegistry));
        }

        private static String emailProvider(String email) {
            int at = email.indexOf('@');
            if (at < 0 || at == email.length() - 1) {
                return "unknown";
            }
            return email.substring(at + 1).toLowerCase(Locale.ROOT);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MetricsService(
        private val meterRegistry: MeterRegistry
    ) {
        private val userCreationTimer = Timer.builder("user.creation.duration")
            .description("Time taken to create users")
            .serviceLevelObjectives(
                Duration.ofMillis(50),
                Duration.ofMillis(100),
                Duration.ofMillis(250),
                Duration.ofMillis(500),
            )
            .register(meterRegistry)
        private val userCreationCounters = ConcurrentHashMap<String, Counter>()

        fun <T> recordUserCreation(email: String, action: Callable<T>): T {
            return try {
                val result = userCreationTimer.recordCallable(action)
                userCreationCounter(emailProvider(email)).increment()
                result
            } catch (e: RuntimeException) {
                throw e
            } catch (e: Exception) {
                throw IllegalStateException("Failed to record user creation metrics", e)
            }
        }

        private fun userCreationCounter(emailProvider: String): Counter {
            return userCreationCounters.computeIfAbsent(emailProvider) { provider ->
                Counter.builder("user.creation.total")
                    .description("Total number of users created")
                    .tag("email.provider", provider)
                    .register(meterRegistry)
            }
        }

        private fun emailProvider(email: String): String {
            val provider = email.substringAfter('@', missingDelimiterValue = "")
            return provider.ifBlank { "unknown" }.lowercase()
        }
    }
    ```

## Service Integration { #service-integration }

Inject `MetricsService` into `UserService` and wrap user creation. The email is passed to metrics separately because `MetricsService` extracts the provider tag from it.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public UserResponse createUser(UserRequest request) {
        return metricsService.recordUserCreation(request.email(), () -> {
            var generatedId = userRepository.save(request.name(), request.email());
            return new UserResponse(generatedId, request.name(), request.email(), LocalDateTime.now());
        });
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun createUser(request: UserRequest): UserResponse {
        return metricsService.recordUserCreation(request.email) {
            val id = userRepository.save(request.name, request.email)
            UserResponse(id, request.name, request.email, LocalDateTime.now())
        }
    }
    ```

Put business metrics in the service layer, not the controller. The controller knows HTTP shape; the service knows whether the domain operation happened.

## Application Check { #check-app }

Run the app, create two users with different email domains, and inspect metrics:

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@example.com"}'

curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Bob","email":"bob@gmail.com"}'

curl http://localhost:8085/metrics
```

The output should contain `user.creation.duration` and `user.creation.total`. The counter should also show provider tag values such as `example.com` and `gmail.com`. A concrete backend may normalize
the tag name, for example from `email.provider` to `email_provider`.

If metrics are missing, check that `MetricsModule` is wired, the operation reaches `recordUserCreation()`, and the curl command uses the private port.

## Best Practices { #best-practices }

- Start with a small number of business metrics that answer real operational questions.
- Do not add tags with user ids, full emails, raw paths, or other high-cardinality values.
- Normalize tags: `gmail.com` is better than the full `bob@gmail.com`.
- Keep metric names stable because dashboards and alerts depend on them.
- Measure the actual operation, not DTO preparation.
- Keep `/metrics` on the private management port.

## Summary { #summary }

You added Micrometer, exposed `/metrics` on the private port, measured user creation duration, and counted successful creations with an email provider tag.

## Key Concepts { #key-concepts }

Counter:
: counts events and can split them by stable tags.

Timer:
: measures duration and latency distribution.

Tag:
: a stable label used to group metric series.

MeterRegistry:
: the Kora graph dependency used to register custom meters.

Private management port:
: a separate port for operational endpoints.

## Troubleshooting { #troubleshooting }

Metric is missing:
: Make sure the operation was called after the application started.

`/metrics` is unavailable:
: Check `privateApiHttpPort` and `privateApiHttpMetricsPath`.

Too many time series:
: Remove tags with dynamic values.

## What's Next? { #whats-next }

- add tracing in [Tracing with Kora](observability-tracing.md)
- add liveness and readiness checks in [Probes with Kora](observability-probes.md)
- compare details with [Metrics documentation](../documentation/metrics.md)

## Help { #help }

- inspect the finished Java and Kotlin observability applications
- verify module names in [Metrics documentation](../documentation/metrics.md)
