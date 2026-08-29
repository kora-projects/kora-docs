---
search:
  exclude: true
title: Metrics with Kora
summary: Build focused Micrometer metrics for a Kora HTTP service, including framework metrics, business counters, timers, private metrics endpoints, and practical verification.
description: "Step-by-step Micrometer metrics for a Kora HTTP service: the io.koraframework:micrometer-module dependency, MetricsModule and the injected MeterRegistry, the Prometheus scrape endpoint on httpServer.system.metricsPath, the telemetry.metrics.enabled flag that gates every component metric, slo histogram buckets and common tags, and a custom MetricsService with a Timer, a tagged Counter and a ConcurrentHashMap meter cache."
agent:
  use_when: "Use this file for questions about adding metrics to a Kora application step by step: io.koraframework:micrometer-module, MetricsModule, injecting MeterRegistry, Micrometer Counter and Timer, serviceLevelObjectives, tag cardinality, caching meters in a ConcurrentHashMap, the /metrics endpoint on httpServer.system.port, and why http_server_* metrics are missing until telemetry.metrics.enabled is set to true."
tags: observability, metrics, micrometer, meter-registry, counters, timers, monitoring
---

# Metrics with Kora { #observability-metrics-kora }

This guide focuses only on metrics. You will take the HTTP server application and add operational and business metrics: the Micrometer module, the `/metrics` endpoint on the system port, a custom
`MetricsService`, a user creation counter, and a timer around the creation operation.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java Observability App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-observability-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin Observability App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-observability-app).

## What You Will Build { #youll-build }

You will add:

- `MetricsModule`
- the `/metrics` endpoint on the system port
- `telemetry.metrics.enabled = true` for the HTTP server, so component metrics are actually collected
- a custom `MetricsService`
- the `user.creation.duration` timer
- the `user.creation.total` counter with the `email.provider` tag
- a practical check that metrics appear after a business operation

## What You Will Need { #youll-need }

- JDK 25 or later
- Gradle 9+
- A text editor or IDE
- Completed [HTTP Server Guide](http-server.md)

Kora 2.0 artifacts are compiled for Java 25, so the JDK that compiles the application must be 25 or newer.

## Prerequisites { #prerequisites }

!!! note "Required Foundation"

    This guide assumes you have completed **[HTTP Server Guide](http-server.md)** and already have the HTTP controllers, DTOs, repository, service, and configuration from that guide in place.

    If you haven't completed the HTTP server guide yet, do that first, because this observability guide keeps that HTTP surface and layers telemetry on top of it.

## Overview { #overview }

Metrics are numbers that an application exposes to the outside world. Imagine a small dashboard next to the service: it shows how many requests passed through, how many users were created, how long operations took, and how much runtime capacity is being used. One number rarely tells the full story, but a set of numbers can show that the application became slower, started failing more often, or suddenly received more traffic.

Kora as a framework already knows how to produce the main system and module metrics. When you connect the relevant modules and enable their metrics, Kora emits metrics for supported parts of the application: HTTP servers, clients, databases, messaging, runtime infrastructure, and other integrations. These signals are exposed in a standard observability shape: metric names and tags follow OpenTelemetry semantic conventions, and the scrape endpoint speaks the Prometheus text format.

The key idea is that metrics are not only for the framework and not only for infrastructure. The framework can count technical things, such as HTTP requests or runtime measurements. But only your code knows domain meaning. Kora cannot automatically know that `createUser()` means a user was created, so the business metric belongs in the service layer.

This guide uses three main pieces:

- `MetricsModule` creates the registry and the Prometheus scrape endpoint contract
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

`MeterRegistry` is the registration point. When `MetricsService` calls `Counter.builder(...).register(meterRegistry)`, it says: "create or find a metric with this name and description". After that, the counter can be incremented and the timer can record durations. The concrete implementation Kora builds is a `PrometheusMeterRegistry`, so everything registered through it is scrapeable in the Prometheus text format.

The `/metrics` endpoint is the window through which external monitoring reads collected values. It is served by the system HTTP server, which listens on port `8085` by default. That is intentional: metrics can expose internal service shape, so normal users should not receive them through the public API on `8080`.

### Metrics Boundary { #metrics-boundary }

A good business metric is placed where the business meaning exists. For user creation, that place is `UserService`, not the HTTP controller. The controller knows that an HTTP request arrived. The service knows that the application is performing the creation operation.

In this guide, `MetricsService` wraps the action through `recordUserCreation()`. This shape is useful for three reasons:

- metric names live in one component
- the service method stays readable
- the timer measures exactly the callback passed to it

Do not add a metric to every line of code. Metrics should answer questions, not become noise. If a metric does not help make a decision, configure an alert, or explain service behavior, it is probably too early to add it.

Tags are another important point. Tags are useful when they split measurements by stable categories: operation status, command type, or a client name from a small fixed set. Tags are dangerous when they contain user ids, emails, raw paths, or other unbounded values. This is called high cardinality, and it quickly breaks metric storage.

The practical result is simple: connect the Kora module, enable metrics for the modules you care about, register clear business metrics through `MeterRegistry`, and verify them on the system `/metrics` endpoint. Metrics then become part of the application instead of separate monitoring magic.

## Dependencies { #dependencies }

Micrometer support lives in the `micrometer-module` artifact. Its version comes from the `io.koraframework:kora-bom` platform, so it is not written on the dependency line.

===! ":fontawesome-brands-java: `Java`"

    Update `build.gradle`:

    ```groovy
    dependencies {
        // ... existing dependencies from the HTTP server guide ...

        implementation "io.koraframework:micrometer-module" //(1)!
    }
    ```

    1.  Micrometer metrics module: creates the `PrometheusMeterRegistry` and the scrape contract for the system server.

=== ":simple-kotlin: `Kotlin`"

    Update `build.gradle.kts`:

    ```kotlin
    dependencies {
        // ... existing dependencies from the HTTP server guide ...

        implementation("io.koraframework:micrometer-module") //(1)!
    }
    ```

    1.  Micrometer metrics module: creates the `PrometheusMeterRegistry` and the scrape contract for the system server.

## Modules { #modules }

Add `MetricsModule` to the application graph next to the modules you already connected in the HTTP server guide.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            MetricsModule,  // <----- Connected module
            UndertowPublicHttpServerModule {

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
        UndertowPublicHttpServerModule

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

`MetricsModule` comes from the `io.koraframework.micrometer.module` package. It adds `MeterRegistry` to the graph, binds the standard JVM and process meters to it, and provides the `MetricsScraper`
contract that the system server uses to answer `/metrics`. `UndertowPublicHttpServerModule` extends `UndertowSystemHttpServerModule`, so the scrape endpoint is already routed — you do not connect a
separate management module.

## Configuration { #config }

The public API stays on `8080` and every operational endpoint lives on the system port `8085`.

For the full configuration reference, see [Metrics](../documentation/metrics.md#configuration) and [HTTP Server](../documentation/http-server.md#system-server).

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
      port = 8080 //(1)!
      system {
        port = 8085 //(2)!
        metricsPath = "/metrics" //(3)!
      }
      telemetry.metrics.enabled = true //(4)!
    }
    ```

    1.  Public HTTP port used by application endpoints (default: `8080`).
    2.  System HTTP port that serves metrics and probes (default: `8085`).
    3.  Path of the Prometheus scrape endpoint on the system server (default: `/metrics`).
    4.  Enables metric collection for the public HTTP server (default: `false`).

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      port: 8080 #(1)!
      system:
        port: 8085 #(2)!
        metricsPath: "/metrics" #(3)!
      telemetry:
        metrics:
          enabled: true #(4)!
    ```

    1.  Public HTTP port used by application endpoints (default: `8080`).
    2.  System HTTP port that serves metrics and probes (default: `8085`).
    3.  Path of the Prometheus scrape endpoint on the system server (default: `/metrics`).
    4.  Enables metric collection for the public HTTP server (default: `false`).

This shape matters in production: business clients should not see internal metrics, while Prometheus, Kubernetes, or another monitoring agent should have a stable scrape path.

### Enabling Module Metrics { #module-metrics }

!!! warning "Component metrics are off until you turn them on"

    `TelemetryConfig.MetricsConfig#enabled` returns `false`, and every Kora module inherits that default. An application that only connects `MetricsModule` starts fine and answers `/metrics` with
    `200`, but the body contains only JVM, process, and `kora.up` values. There is no `http_server_request_duration_seconds`, no `http_client_*`, no `db_*` — and nothing in the log to tell you why.

This is the most common way a metrics setup silently produces an empty dashboard, so it is worth understanding the rule behind it. A module reports metrics only when **both** conditions hold:

- `MetricsModule` is connected, so a `MeterRegistry` exists in the graph
- that module's own `telemetry.metrics.enabled` is `true`

If either is missing, the module falls back to a no-op metrics factory: no `Meter` is created at all, so there is nothing to be missing from the registry later. That is also how you silence a noisy
integration without removing the module.

Every telemetry block is nested under the configuration section of the module that owns it, so you enable metrics where the module is configured:

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer.telemetry.metrics.enabled = true //(1)!
    httpClient.telemetry.metrics.enabled = true //(2)!
    jdbc.telemetry.metrics.enabled = true //(3)!
    ```

    1.  Metrics of the public HTTP server: request duration and active requests.
    2.  Metrics shared by declarative HTTP clients.
    3.  Metrics of the JDBC data source and its connection pool.

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      telemetry:
        metrics:
          enabled: true #(1)!
    httpClient:
      telemetry:
        metrics:
          enabled: true #(2)!
    jdbc:
      telemetry:
        metrics:
          enabled: true #(3)!
    ```

    1.  Metrics of the public HTTP server: request duration and active requests.
    2.  Metrics shared by declarative HTTP clients.
    3.  Metrics of the JDBC data source and its connection pool.

Custom metrics registered by your own code through `MeterRegistry` are not affected by this flag. `user.creation.total` appears as soon as `MetricsModule` is connected and the code runs, because the
registry itself is always live. The flag only gates the telemetry of Kora modules.

### Histogram Buckets and Common Tags { #slo-and-tags }

The same `telemetry.metrics` block carries two more options that shape what a module reports:

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
      telemetry.metrics {
        enabled = true //(1)!
        slo = ["1ms", "10ms", "50ms", "100ms", "500ms", "1s", "5s"] //(2)!
        tags { //(3)!
          "deployment.environment" = "stage"
        }
      }
    }
    ```

    1.  Enables metric collection for the module (default: `false`).
    2.  Histogram buckets for `Timer` metrics of this module, a list of durations (default: 14 buckets from `1ms` to `90000ms`).
    3.  Extra tags added to every metric this module reports (default: `{}`).

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      telemetry:
        metrics:
          enabled: true #(1)!
          slo: [ "1ms", "10ms", "50ms", "100ms", "500ms", "1s", "5s" ] #(2)!
          tags: #(3)!
            "deployment.environment": "stage"
    ```

    1.  Enables metric collection for the module (default: `false`).
    2.  Histogram buckets for `Timer` metrics of this module, a list of durations (default: 14 buckets from `1ms` to `90000ms`).
    3.  Extra tags added to every metric this module reports (default: `{}`).

A duration in `slo` carries its own unit (`"1ms"`, `"250ms"`, `"1s"`), and a bare number is read as milliseconds, so `slo = [1, 10, 50]` and `slo = ["1ms", "10ms", "50ms"]` describe the same list.
These two keys apply only to metrics that the module itself reports. The custom timer you are about to write gets its buckets from the Micrometer builder instead, which the next section shows.

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

This is the custom-metric counterpart of the `telemetry.metrics.slo` key: Kora passes the configured durations to exactly the same `serviceLevelObjectives(...)` builder method when it registers its own module timers.

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

Kora framework metrics follow the same rule. The HTTP server timer `http.server.request.duration` is tagged with `server.name`, `server.port`, `http.request.method`, `http.route`, `url.scheme`, `server.address`, and `error.type` — every one of them from a small, predictable set. A route template like `/users/{id}` is safe; a raw path like `/users/128734` would create a new series for each user, which is exactly why Kora reports the template and falls back to `UNKNOWN_ROUTE` when no route matched. The domain after `@` follows the same idea: it does not identify the concrete user and is useful for grouping.

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

That is why Kora builds a key from stable tag values, registers the meter once with `computeIfAbsent`, and then only updates the already registered metric. Its HTTP server metrics use a record key of method, route template, scheme, host, and error type for exactly this purpose. In this business example the key is simpler: only `email.provider`.

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

You do not need this cache for every meter. If the tag set is fixed, keep the meter as a service field. Use the cache when a tag comes from runtime data, but that data is still low-cardinality and useful for grouping. This keeps the tag boundary visible, avoids repeated builder/registration work on every call, and matches the way Kora handles its own HTTP metrics.

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

    Create `src/main/java/io/koraframework/guide/observability/service/MetricsService.java`:

    ```java
    package io.koraframework.guide.observability.service;

    import io.koraframework.common.annotation.Component;
    import io.micrometer.core.instrument.Counter;
    import io.micrometer.core.instrument.MeterRegistry;
    import io.micrometer.core.instrument.Timer;
    import java.time.Duration;
    import java.util.Locale;
    import java.util.concurrent.Callable;
    import java.util.concurrent.ConcurrentHashMap;

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

    Create `src/main/kotlin/io/koraframework/guide/observability/service/MetricsService.kt`:

    ```kotlin
    package io.koraframework.guide.observability.service

    import io.koraframework.common.annotation.Component
    import io.micrometer.core.instrument.Counter
    import io.micrometer.core.instrument.MeterRegistry
    import io.micrometer.core.instrument.Timer
    import java.time.Duration
    import java.util.concurrent.Callable
    import java.util.concurrent.ConcurrentHashMap

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

Put business metrics in the service layer, not the controller. The controller knows HTTP shape; the service knows whether the domain operation happened. The method also stays synchronous, which is
what makes wrapping it in a timer this simple: there is no callback that finishes after `recordCallable` returns.

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

The Prometheus exposition rewrites meter names: dots become underscores, and a `Timer` gains the `_seconds` unit suffix. So the output should contain `user_creation_duration_seconds_count`,
`user_creation_duration_seconds_sum`, the `user_creation_duration_seconds_bucket` series produced by the service level objectives, and `user_creation_total`. The counter should also show provider tag
values such as `example.com` and `gmail.com`, with the tag key normalized to `email_provider`.

If the business metrics are missing, check that `MetricsModule` is wired, the operation reaches `recordUserCreation()`, and the curl command uses the system port `8085`.

If instead the business metrics are there but framework metrics such as `http_server_request_duration_seconds` are not, that is the default from [Enabling Module Metrics](#module-metrics):
`httpServer.telemetry.metrics.enabled` is still `false`. The endpoint keeps answering `200` in that state, which is why the symptom is an empty dashboard rather than an error.

## Best Practices { #best-practices }

- Start with a small number of business metrics that answer real operational questions.
- Enable `telemetry.metrics.enabled` for the modules you actually want to watch, and leave it off for the noisy ones.
- Do not add tags with user ids, full emails, raw paths, or other high-cardinality values.
- Normalize tags: `gmail.com` is better than the full `bob@gmail.com`.
- Keep metric names stable because dashboards and alerts depend on them.
- Register a meter once and reuse it; cache tagged meters by a low-cardinality key.
- Measure the actual operation, not DTO preparation.
- Keep `/metrics` on the system port.

## Summary { #summary }

You added Micrometer, enabled HTTP server metrics, exposed `/metrics` on the system port, measured user creation duration, and counted successful creations with an email provider tag.

## Key Concepts { #key-concepts }

Counter:
: counts events and can split them by stable tags.

Timer:
: measures duration and latency distribution.

Tag:
: a stable label used to group metric series.

MeterRegistry:
: the Kora graph dependency used to register custom meters.

`telemetry.metrics.enabled`:
: the per-module switch that decides whether a Kora module reports metrics at all.

System port:
: a separate port for operational endpoints such as `/metrics` and the probes.

## Troubleshooting { #troubleshooting }

Metric is missing:
: Make sure the operation was called after the application started.

`/metrics` answers `200` but has only JVM values:
: Set `<module>.telemetry.metrics.enabled = true` for the modules you want to observe.

`/metrics` answers `# Metric Scraper disabled`:
: `MetricsModule` is not connected, so no `MetricsScraper` exists in the graph.

`/metrics` is unavailable:
: Check `httpServer.system.port` and `httpServer.system.metricsPath`.

Too many time series:
: Remove tags with dynamic values.

## What's Next? { #whats-next }

- add tracing in [Tracing with Kora](observability-tracing.md)
- add liveness and readiness checks in [Probes with Kora](observability-probes.md)
- wire all signals into one application in [Observability and Monitoring with Kora](observability.md)
- compare details with [Metrics documentation](../documentation/metrics.md)

## Help { #help }

- inspect the finished Java and Kotlin observability applications
- look up module metric names and tags in the [Metrics reference](../documentation/metrics.md#metrics-reference)
- verify module names in [Metrics documentation](../documentation/metrics.md)
