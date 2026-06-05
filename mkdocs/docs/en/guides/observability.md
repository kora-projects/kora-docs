---
search:
  exclude: true
title: Observability & Monitoring with Kora
summary: Learn how to extend the HTTP Server guide with metrics, tracing, structured logging, and health probes
tags: observability, metrics, tracing, logging, health-checks, monitoring
---

# Observability and Monitoring with Kora { #observability-monitoring-kora }

This guide introduces production-oriented observability for Kora applications. It covers how metrics, distributed tracing, structured logging, and health probes are wired into the application graph,
how telemetry modules instrument common runtime paths, and how management endpoints expose operational state. You will also see how observability configuration turns local behavior into signals that
monitoring systems can consume.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java Observability App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-observability-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin Observability App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-observability-app).

## What You'll Build { #youll-build }

You will enhance the HTTP server application with:

- Micrometer metrics for framework and business events
- OpenTelemetry tracing export over HTTP
- request logging enriched with trace context
- liveness and readiness probes on the private management port
- observability-focused tests that verify metrics, probes, and tracing behavior

## What You'll Need { #youll-need }

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

Observability is what lets you understand a running service without guessing from symptoms alone. When an API becomes slower, starts failing intermittently, or works in one environment but not
another, you need signals from inside the application that explain what is happening.

The important shift is that observability is not a separate debugging mode. It is part of the runtime contract of a production service. A service should expose enough metrics, traces, logs, and probes
that operators can understand whether it is healthy and where failures are happening.

### Three Core Signals { #three-core-signals }

In practice, Kora observability is built around three complementary signals:

- [Micrometer](https://docs.micrometer.io/micrometer/reference/) metrics tell you how the system behaves in aggregate over time
- [OpenTelemetry](https://opentelemetry.io/docs/) traces show the lifecycle of a single request across the call chain
- probes tell the platform whether the process is alive and ready to receive traffic

Metrics are useful when you want trends, rates, and saturation signals instead of single-event details. Kora uses Micrometer, so the application can publish both framework metrics and business metrics
in one place. In a typical service you will see several categories of metrics:

- infrastructure metrics such as JVM memory, CPU, threads, and process-level usage
- HTTP server metrics such as request count, latency, active requests, and status code distribution
- logging and runtime metrics that help explain internal activity
- custom business metrics, for example how many users were created and how long that operation took

These metric types answer different questions. Counters help track totals and rates, timers help measure duration and latency distributions, and gauges help observe values that go up and down over
time. Together they let you spot regressions, alert on failures, and understand system behavior before users start reporting incidents.

Tracing solves a different problem. Metrics can show that requests are slow, but they do not show which individual request was slow or where the time was spent. Distributed tracing follows one request
through the application and attaches a trace ID and span ID to the work being done. That makes it much easier to correlate logs, inspect request flow, and understand where latency or failures appear
when a request crosses multiple layers or services.

Probes are primarily for operations and orchestration. A liveness probe answers "should this process be restarted?" and a readiness probe answers "is this instance ready to serve traffic right now?"
They are critical for [Docker](https://docs.docker.com/) and [Kubernetes](https://kubernetes.io/docs/home/) style deployments because they let load balancers and orchestrators avoid sending traffic to
an instance that is still warming up or is temporarily unhealthy.

### Observability in Kora { #observability-kora }

Kora wires observability through modules and configuration. Framework components can emit telemetry automatically, and application code can add custom business signals where the framework cannot know
the domain meaning.

This guide adds observability concerns around the HTTP application:

- `MetricsModule` enables framework metrics and gives access to `MeterRegistry`
- `OpentelemetryHttpExporterModule` exports traces to an OpenTelemetry-compatible collector
- `CustomReadinessProbe` and `ApplicationHealthProbe` feed `/system/readiness` and `/system/liveness`
- `MetricsService` records business metrics for user creation
- observability tests become the source of truth for management endpoints and tracing-aware logging

### Operational Boundaries { #operational-boundaries }

Observability endpoints usually belong on a private management port, not the public business API. That separation lets platforms, load balancers, and monitoring tools inspect service health without
exposing internal operational details to normal clients. The guide keeps public API behavior and management behavior separate so the runtime shape matches production expectations.

The practical flow is:

1. add metrics, tracing, logging, and probe modules
2. wire observability modules into the Kora graph
3. add custom readiness and liveness probes
4. record business metrics in service code
5. configure management endpoints and telemetry export
6. verify metrics, probes, and trace-aware logging in tests

## Dependencies { #dependencies }

===! ":fontawesome-brands-java: `Java`"

    Update `build.gradle`:

    ```groovy
    dependencies {
        // ... existing dependencies from http-server guide ...

        implementation("ru.tinkoff.kora:micrometer-module")
        implementation("ru.tinkoff.kora:opentelemetry-tracing-exporter-http")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update `build.gradle.kts`:

    ```kotlin
    dependencies {
        // ... existing dependencies from http-server guide ...

        implementation("ru.tinkoff.kora:micrometer-module")
        implementation("ru.tinkoff.kora:opentelemetry-tracing-exporter-http")
    }
    ```

## Modules { #modules }

Add the observability modules to the same application graph you created in the HTTP server guide.

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/java/ru/tinkoff/kora/guide/observability/Application.java`:

    ```java
    package ru.tinkoff.kora.guide.observability;

    import ru.tinkoff.kora.application.graph.KoraApplication;
    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.config.hocon.HoconConfigModule;
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule;
    import ru.tinkoff.kora.json.module.JsonModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;
    import ru.tinkoff.kora.micrometer.module.MetricsModule;
    import ru.tinkoff.kora.opentelemetry.tracing.exporter.http.OpentelemetryHttpExporterModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            MetricsModule,  // <----- Connected module
            UndertowHttpServerModule,
            OpentelemetryHttpExporterModule {  // <----- Connected module

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update `src/main/kotlin/ru/tinkoff/kora/guide/observability/Application.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.observability

    import ru.tinkoff.kora.application.graph.KoraApplication
    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.config.hocon.HoconConfigModule
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule
    import ru.tinkoff.kora.json.module.JsonModule
    import ru.tinkoff.kora.logging.logback.LogbackModule
    import ru.tinkoff.kora.micrometer.module.MetricsModule
    import ru.tinkoff.kora.opentelemetry.tracing.exporter.http.OpentelemetryHttpExporterModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        MetricsModule,  // <----- Connected module
        UndertowHttpServerModule,
        OpentelemetryHttpExporterModule  // <----- Connected module

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

## Configuration { #config }

The public API still runs on `8080`, but all management endpoints in this guide live on the private port `8085`.

Update `src/main/resources/application.conf`:

For the full configuration reference, see [HTTP Server](../documentation/http-server.md), [Tracing](../documentation/tracing.md) and [Logging SLF4J](../documentation/logging-slf4j.md).

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
      publicApiHttpPort = 8080 //(1)!
      privateApiHttpPort = 8085 //(2)!
      privateApiHttpMetricsPath = "/metrics" //(3)!
      privateApiHttpLivenessPath = "/system/liveness" //(4)!
      privateApiHttpReadinessPath = "/system/readiness" //(5)!
      telemetry.logging.enabled = true //(6)!
    }

    tracing {
      exporter {
        endpoint = "http://localhost:4318/v1/traces" //(7)!
      }
    }

    logging {
      levels {
        "ROOT" = "WARN" //(8)!
        "ru.tinkoff.kora" = "INFO" //(9)!
        "ru.tinkoff.kora.guide.observability" = "DEBUG" //(10)!
      }
    }
    ```

    1. Default public HTTP port used by application endpoints.
    2. Default private HTTP port used by probes, metrics, and management endpoints.
    3. Default private HTTP path that exposes metrics.
    4. Default private HTTP path used for the liveness probe.
    5. Default private HTTP path used for the readiness probe.
    6. Enables the feature for this configuration section.
    7. Telemetry exporter endpoint.
    8. Log level for `ROOT`.
    9. Log level for `ru.tinkoff.kora`.
    10. Log level for `ru.tinkoff.kora.guide.observability`.

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      publicApiHttpPort: 8080 #(1)!
      privateApiHttpPort: 8085 #(2)!
      privateApiHttpMetricsPath: "/metrics" #(3)!
      privateApiHttpLivenessPath: "/system/liveness" #(4)!
      privateApiHttpReadinessPath: "/system/readiness" #(5)!
      telemetry:
        logging:
          enabled: true #(6)!
    tracing:
      exporter:
        endpoint: "http://localhost:4318/v1/traces" #(7)!
    logging:
      levels:
        ROOT: "WARN" #(8)!
        "ru.tinkoff.kora": "INFO" #(9)!
        "ru.tinkoff.kora.guide.observability": "DEBUG" #(10)!
    ```

    1. Default public HTTP port used by application endpoints.
    2. Default private HTTP port used by probes, metrics, and management endpoints.
    3. Default private HTTP path that exposes metrics.
    4. Default private HTTP path used for the liveness probe.
    5. Default private HTTP path used for the readiness probe.
    6. Enables the feature for this configuration section.
    7. Telemetry exporter endpoint.
    8. Log level for `ROOT`.
    9. Log level for `ru.tinkoff.kora`.
    10. Log level for `ru.tinkoff.kora.guide.observability`.

Why this matters:

- `/metrics`, `/system/liveness`, and `/system/readiness` are intentionally isolated from the public API
- `telemetry.logging.enabled = true` lets HTTP telemetry enrich logs with trace information
- the tracing exporter can send spans to any OTLP HTTP collector; if none is running locally, the application still starts and your tests can still validate log correlation and management endpoints

## Metrics { #metrics }

Kora already exposes many framework metrics automatically. Add custom metrics only for business events that matter to your application.

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/guide/observability/service/MetricsService.java`:

    ```java
    package ru.tinkoff.kora.guide.observability.service;

    import io.micrometer.core.instrument.Counter;
    import io.micrometer.core.instrument.MeterRegistry;
    import io.micrometer.core.instrument.Timer;
    import java.util.concurrent.Callable;
    import ru.tinkoff.kora.common.Component;

    @Component
    public final class MetricsService {

        private final Counter userCreationCounter;
        private final Timer userCreationTimer;

        public MetricsService(MeterRegistry meterRegistry) {
            this.userCreationCounter = Counter.builder("user.creation.total")
                    .description("Total number of users created")
                    .register(meterRegistry);
            this.userCreationTimer = Timer.builder("user.creation.duration")
                    .description("Time taken to create users")
                    .register(meterRegistry);
        }

        public <T> T recordUserCreation(Callable<T> action) {
            this.userCreationCounter.increment();
            try {
                return this.userCreationTimer.recordCallable(action);
            } catch (RuntimeException e) {
                throw e;
            } catch (Exception e) {
                throw new IllegalStateException("Failed to record user creation metrics", e);
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/guide/observability/service/MetricsService.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.observability.service

    import io.micrometer.core.instrument.Counter
    import io.micrometer.core.instrument.MeterRegistry
    import io.micrometer.core.instrument.Timer
    import ru.tinkoff.kora.common.Component
    import java.util.concurrent.Callable

    @Component
    class MetricsService(
        meterRegistry: MeterRegistry
    ) {
        private val userCreationCounter: Counter = Counter.builder("user.creation.total")
            .description("Total number of users created")
            .register(meterRegistry)

        private val userCreationTimer: Timer = Timer.builder("user.creation.duration")
            .description("Time taken to create users")
            .register(meterRegistry)

        fun <T> recordUserCreation(action: Callable<T>): T {
            userCreationCounter.increment()
            return try {
                userCreationTimer.recordCallable(action)
            } catch (e: RuntimeException) {
                throw e
            } catch (e: Exception) {
                throw IllegalStateException("Failed to record user creation metrics", e)
            }
        }
    }
    ```

## Tracing Service { #tracing-service }

Framework telemetry already creates spans for supported runtime paths such as HTTP handling. Manual tracing is useful when you want to mark a business operation inside that request, name it in domain
terms, and attach success or failure to that specific piece of work.

The tracing reference shows the general pattern in [Tracing Sync](../documentation/tracing.md#tracing-sync): inject `Tracer`, create a span with the current context as parent, put the span into
`OpentelemetryContext`, and always end the span in `finally`.

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/guide/observability/service/TracingService.java`:

    ```java
    package ru.tinkoff.kora.guide.observability.service;

    import io.opentelemetry.api.trace.StatusCode;
    import io.opentelemetry.api.trace.Tracer;
    import java.util.concurrent.Callable;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.Context;
    import ru.tinkoff.kora.opentelemetry.common.OpentelemetryContext;

    @Component
    public final class TracingService {

        private final Tracer tracer;

        public TracingService(Tracer tracer) {
            this.tracer = tracer;
        }

        public <T> T traceUserCreation(Callable<T> action) {
            var ctx = Context.current();
            var otctx = OpentelemetryContext.get(ctx);
            var span = tracer.spanBuilder("user.create")
                    .setParent(otctx.getContext())
                    .startSpan();

            OpentelemetryContext.set(ctx, otctx.add(span));
            try {
                var result = action.call();
                span.setStatus(StatusCode.OK);
                return result;
            } catch (RuntimeException e) {
                span.recordException(e);
                span.setStatus(StatusCode.ERROR, e.getMessage());
                throw e;
            } catch (Exception e) {
                span.recordException(e);
                span.setStatus(StatusCode.ERROR, e.getMessage());
                throw new IllegalStateException("Failed to trace user creation", e);
            } finally {
                span.end();
                OpentelemetryContext.set(ctx, otctx);
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/guide/observability/service/TracingService.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.observability.service

    import io.opentelemetry.api.trace.StatusCode
    import io.opentelemetry.api.trace.Tracer
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.Context
    import ru.tinkoff.kora.opentelemetry.common.OpentelemetryContext

    @Component
    class TracingService(
        private val tracer: Tracer
    ) {
        fun <T> traceUserCreation(action: () -> T): T {
            val ctx = Context.current()
            val otctx = OpentelemetryContext.get(ctx)
            val span = tracer.spanBuilder("user.create")
                .setParent(otctx.getContext())
                .startSpan()

            OpentelemetryContext.set(ctx, otctx.add(span))
            try {
                val result = action()
                span.setStatus(StatusCode.OK)
                return result
            } catch (e: RuntimeException) {
                span.recordException(e)
                span.setStatus(StatusCode.ERROR, e.message)
                throw e
            } finally {
                span.end()
                OpentelemetryContext.set(ctx, otctx)
            }
        }
    }
    ```

This span becomes a child of the current HTTP request span when the operation is executed during request handling. If the operation fails, the span records the exception and is exported with error
status.

## Tracing Integration { #tracing-integration }

Keep the HTTP contract from the previous guide and add observability where the business action happens.

Only `UserService` constructor wiring and `createUser()` change in this guide. The rest of the service methods stay the same as in the HTTP server guide.

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/java/ru/tinkoff/kora/guide/observability/service/UserService.java`:

    ```java
    package ru.tinkoff.kora.guide.observability.service;

    import java.time.LocalDateTime;
    import org.slf4j.Logger;
    import org.slf4j.LoggerFactory;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.observability.dto.UserRequest;
    import ru.tinkoff.kora.guide.observability.dto.UserResponse;
    import ru.tinkoff.kora.guide.observability.repository.UserRepository;

    @Component
    public final class UserService {

        private static final Logger logger = LoggerFactory.getLogger(UserService.class);

        private final UserRepository userRepository;
        private final MetricsService metricsService;
        private final TracingService tracingService;

        public UserService(UserRepository userRepository, MetricsService metricsService, TracingService tracingService) {
            this.userRepository = userRepository;
            this.metricsService = metricsService;
            this.tracingService = tracingService;
        }

        public UserResponse createUser(UserRequest request) {
            logger.info("Creating user with name={} and email={}", request.name(), request.email());
            return tracingService.traceUserCreation(() -> metricsService.recordUserCreation(() -> {
                var generatedId = userRepository.save(request.name(), request.email());
                var user = new UserResponse(generatedId, request.name(), request.email(), LocalDateTime.now());
                logger.info("Created user with id={}", generatedId);
                return user;
            }));
        }

        // getUser(), getUsers(), updateUser(), deleteUser(), and sorting logic
        // stay the same as in the HTTP server guide.
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update `src/main/kotlin/ru/tinkoff/kora/guide/observability/service/UserService.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.observability.service

    import org.slf4j.LoggerFactory
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.observability.dto.UserRequest
    import ru.tinkoff.kora.guide.observability.dto.UserResponse
    import ru.tinkoff.kora.guide.observability.repository.UserRepository
    import java.time.LocalDateTime

    @Component
    class UserService(
        private val userRepository: UserRepository,
        private val metricsService: MetricsService,
        private val tracingService: TracingService
    ) {
        private val logger = LoggerFactory.getLogger(UserService::class.java)

        fun createUser(request: UserRequest): UserResponse {
            logger.info("Creating user with name={} and email={}", request.name, request.email)
            return tracingService.traceUserCreation {
                metricsService.recordUserCreation {
                    val generatedId = userRepository.save(request.name, request.email)
                    val user = UserResponse(generatedId, request.name, request.email, LocalDateTime.now())
                    logger.info("Created user with id={}", generatedId)
                    user
                }
            }
        }

        // getUser(), getUsers(), updateUser(), deleteUser(), and sorting logic
        // stay the same as in the HTTP server guide.
    }
    ```

## Probes { #probes }

Readiness should become healthy after startup work finishes. It should not fail forever.

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/guide/observability/health/CustomReadinessProbe.java`:

    ```java
    package ru.tinkoff.kora.guide.observability.health;

    import java.time.Duration;
    import java.time.Instant;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.readiness.ReadinessProbe;
    import ru.tinkoff.kora.common.readiness.ReadinessProbeFailure;

    @Component
    public final class CustomReadinessProbe implements ReadinessProbe {

        private static final Duration WARMUP_PERIOD = Duration.ofMillis(500);

        private final Instant startedAt = Instant.now();

        @Override
        public ReadinessProbeFailure probe() {
            var readyAt = startedAt.plus(WARMUP_PERIOD);
            if (Instant.now().isBefore(readyAt)) {
                return new ReadinessProbeFailure("Service is warming up");
            }
            return null;
        }
    }
    ```

    Create `src/main/java/ru/tinkoff/kora/guide/observability/health/ApplicationHealthProbe.java`:

    ```java
    package ru.tinkoff.kora.guide.observability.health;

    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.liveness.LivenessProbe;
    import ru.tinkoff.kora.common.liveness.LivenessProbeFailure;

    @Component
    public final class ApplicationHealthProbe implements LivenessProbe {

        @Override
        public LivenessProbeFailure probe() {
            return null;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/guide/observability/health/CustomReadinessProbe.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.observability.health

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.readiness.ReadinessProbe
    import ru.tinkoff.kora.common.readiness.ReadinessProbeFailure
    import java.time.Duration
    import java.time.Instant

    @Component
    class CustomReadinessProbe : ReadinessProbe {
        private val startedAt = Instant.now()

        override fun probe(): ReadinessProbeFailure? {
            val readyAt = startedAt.plus(Duration.ofMillis(500))
            return if (Instant.now().isBefore(readyAt)) {
                ReadinessProbeFailure("Service is warming up")
            } else {
                null
            }
        }
    }
    ```

    Create `src/main/kotlin/ru/tinkoff/kora/guide/observability/health/ApplicationHealthProbe.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.observability.health

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.liveness.LivenessProbe
    import ru.tinkoff.kora.common.liveness.LivenessProbeFailure

    @Component
    class ApplicationHealthProbe : LivenessProbe {
        override fun probe(): LivenessProbeFailure? = null
    }
    ```

## Docker Compose { #docker-compose }

If you want to inspect traces locally, start a Jaeger all-in-one container that exposes both the OTLP HTTP ingestion endpoint and the Jaeger UI.

Create `docker-compose.yml` in the application module directory:

```yaml
services:
    jaeger:
        image: jaegertracing/all-in-one:latest
        ports:
            - "16686:16686"
            - "4318:4318"
        environment:
            COLLECTOR_OTLP_ENABLED: "true"
```

Start Jaeger:

```bash
docker compose up -d
```

Then:

- keep `tracing.exporter.endpoint = "http://localhost:4318/v1/traces"` in `application.conf`
- start the application with `./gradlew run`
- send a few requests to `http://localhost:8080/users`
- open [http://localhost:16686](http://localhost:16686) and search for the `guide-observability-app` service

Stop Jaeger when you are done:

```bash
docker compose down
```

This setup is optional, but it is the fastest way to verify locally that spans are being exported and that trace IDs from logs correspond to traces visible in the UI.

## Check Application { #check-app }

Use the normal Gradle flow for runtime guides:

```bash
./gradlew clean classes
./gradlew test
./gradlew run
```

Once the app is running, verify the management endpoints on the private port:

```bash
curl http://localhost:8085/system/liveness
curl http://localhost:8085/system/readiness
curl http://localhost:8085/metrics
```

You can still hit the public API on `8080`, for example:

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@example.com"}'
```

## Best Practices { #best-practices }

- Keep business metrics in a dedicated service so controllers stay focused on HTTP concerns.
- Prefer observing business actions in the service layer, where logs, metrics, and trace context meet.
- Use manual spans for domain operations that framework instrumentation cannot name precisely.
- Keep readiness lightweight and temporary. A readiness probe should fail during startup or dependency checks, then recover.
- Expose health and metrics only on the private port `8085`.
- Treat tests as the source of truth for observability behavior and keep them scoped to what the guide actually teaches.

## Summary { #summary }

You extended the HTTP server application with Kora observability features without changing the public API contract. The app now exposes management endpoints on the private port, records business
metrics for user creation, creates a manual `user.create` span, emits tracing-aware logs, and reports liveness/readiness through Kora probes.

## Key Concepts { #key-concepts }

- how `MetricsModule` enables framework metrics and custom `MeterRegistry` usage
- how `OpentelemetryHttpExporterModule` adds tracing export to the application graph
- how an injected `Tracer` and `OpentelemetryContext` create a manual child span for business work
- why management endpoints belong on a private port
- how to model liveness and readiness probes with realistic behavior
- how to validate observability features with focused component and black-box tests

## Troubleshooting { #troubleshooting }

**`./gradlew clean` or `./gradlew test` hangs:**

Stop Gradle daemons and retry:

```bash
./gradlew --stop
./gradlew clean classes
./gradlew test
```

**Windows reports `AccessDeniedException` in the Gradle cache:**

This usually means a daemon or another process still holds files in `.gradle` or `build` directories. Run `./gradlew --stop`, close IDE processes that may lock files, and retry the build.

**Readiness or Liveness or Metrics returns `404`:**

Check that you are using the private port `8085`, not the public port `8080`, and that these paths are configured:

For the full configuration reference, see [HTTP Server](../documentation/http-server.md).

===! ":material-code-json: `Hocon`"

    ```javascript
    privateApiHttpMetricsPath = "/metrics" //(1)!
    privateApiHttpLivenessPath = "/system/liveness" //(2)!
    privateApiHttpReadinessPath = "/system/readiness" //(3)!
    ```

    1. Default private HTTP path that exposes metrics.
    2. Default private HTTP path used for the liveness probe.
    3. Default private HTTP path used for the readiness probe.

=== ":simple-yaml: `YAML`"

    ```yaml
    privateApiHttpMetricsPath: "/metrics" #(1)!
    privateApiHttpLivenessPath: "/system/liveness" #(2)!
    privateApiHttpReadinessPath: "/system/readiness" #(3)!
    ```

    1. Default private HTTP path that exposes metrics.
    2. Default private HTTP path used for the liveness probe.
    3. Default private HTTP path used for the readiness probe.

**Traces are not exported anywhere locally:**

That is expected if no OTLP collector is running on `http://localhost:4318/v1/traces`. The application and tests still work, but you will need a collector such as Jaeger or OpenTelemetry Collector to
inspect exported traces.

## What's Next? { #whats-next }

- [Testing with JUnit](testing-junit.md) to add focused component tests around observable components.
- [Database JDBC](database-jdbc.md) before [Black Box Testing](testing-black-box.md), because the black-box guide assumes the JDBC-backed app.
- [Messaging with Kafka](messaging-kafka.md) to observe asynchronous processing.
- [Resilient Patterns](resilient.md) to connect metrics and traces with failures, retries, and circuit breakers.

## Help { #help }

If something does not match your local application:

- compare with [Kora Java Observability App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-observability-app) and [Kora Kotlin Observability App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-observability-app)
- revisit [HTTP Server](http-server.md) for the base API shape
- check the [Metrics documentation](../documentation/metrics.md)
- check the [Tracing documentation](../documentation/tracing.md)
- check the [Logging documentation](../documentation/logging-slf4j.md)
- check the [Probes documentation](../documentation/probes.md)
