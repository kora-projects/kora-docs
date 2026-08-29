---
search:
  exclude: true
title: Observability & Monitoring with Kora
summary: Assemble metrics, tracing, structured logging, and health probes into one Kora application, and find the focused guide for each signal.
description: "The Kora observability hub: how metrics, tracing, logging and probes fit together in one application, which telemetry is on by default and which is not, the complete module graph with MetricsModule and OpentelemetryHttpExporterModule, the full httpServer.system, tracing and logging configuration, traceId correlation in log lines, the system port that serves /metrics and the probes, and links to the focused metrics, tracing and probes guides."
agent:
  use_when: "Use this file for questions about Kora observability as a whole: which of metrics, tracing, logging or probes to use for a problem, how they combine in one application, the complete @KoraApp graph with MetricsModule and OpentelemetryHttpExporterModule, why telemetry.metrics.enabled and telemetry.logging.enabled default to false while tracing defaults to true, the system HTTP port 8085 serving /metrics, /system/liveness and /system/readiness, correlating logs with traceId and spanId, and where each signal is taught step by step."
tags: observability, metrics, tracing, logging, health-checks, monitoring
---

# Observability and Monitoring with Kora { #observability-monitoring-kora }

This is the hub for Kora observability. It shows how the four signals — metrics, tracing, logging, and probes — fit together in one running application, and points at the focused guide that teaches
each one step by step.

Read this page when you want the whole picture: the complete module graph, the complete configuration, and the rules that cut across all four signals. Read the focused guides when you are implementing
one of them.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java Observability App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-observability-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin Observability App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-observability-app).

## What You Will Build { #youll-build }

One application that carries all four signals:

- Micrometer metrics on `/metrics`, framework and business
- OpenTelemetry traces exported over `OTLP/HTTP`
- log lines carrying `traceId` and `spanId`
- liveness and readiness probes on the system port
- one system port serving every operational endpoint
- tests that assert on metrics, probes, and trace-aware logging

## What You Will Need { #youll-need }

- JDK 25 or later
- Gradle 9+
- Docker, to run Jaeger and the black-box test locally
- A text editor or IDE
- Completed [HTTP Server Guide](http-server.md)

Kora 2.0 artifacts are compiled for Java 25, so the JDK that compiles the application must be 25 or newer.

## Prerequisites { #prerequisites }

!!! note "Required Foundation"

    This guide assumes you have completed **[HTTP Server Guide](http-server.md)** and already have the HTTP controllers, DTOs, repository, service, and configuration from that guide in place.

    If you haven't completed the HTTP server guide yet, do that first, because this observability guide keeps that HTTP surface and layers telemetry on top of it.

## Overview { #overview }

Observability is what lets you understand a running service without guessing from the symptoms. When an API gets slower, fails intermittently, or works in one environment and not another, you need
signals from inside the application that explain what is actually happening.

The shift worth making early is that observability is not a debugging mode you switch on during an incident. It is part of the runtime contract of a production service — by the time you need the data,
it has to already be there.

### Three Core Signals { #three-core-signals }

Kora observability rests on three signals plus one operational one:

- [Micrometer](https://docs.micrometer.io/micrometer/reference/) **metrics** tell you how the system behaves in aggregate over time
- [OpenTelemetry](https://opentelemetry.io/docs/) **traces** show the lifecycle of one request across the call chain
- **logs** record what the code had to say, correlated to the trace that produced them
- **probes** tell the platform whether the process is alive and ready for traffic

Metrics answer questions about trends, rates, and saturation. Kora uses Micrometer, so framework metrics and business metrics land in one registry: JVM and process values, HTTP server latency and
status distribution, database and messaging behavior, plus whatever counters and timers you register yourself.

Traces answer a different question. A metric can show that requests are slow; it cannot show *which* request was slow or where its time went. A trace follows one request through the application,
attaching a trace id and span id to each step, which is what makes it possible to reconstruct a single execution instead of an average.

Logs are the oldest signal and become far more useful once traces exist, because every line emitted inside a traced operation carries the trace id. That is the join key between "what the code said" and
"what the request did".

Probes are for machines rather than people. Liveness answers "should this process be restarted?" and readiness answers "should this instance receive traffic right now?" — and [Kubernetes](https://kubernetes.io/docs/home/)
or a load balancer will act on the answer without asking anyone.

### Choosing a Signal { #choosing-a-signal }

The four overlap enough that it helps to know which one answers which question:

| Question | Signal |
|----------|--------|
| Is the service getting slower over the last hour? | metrics |
| How many users were created today? | metrics |
| Why was *this particular* request slow? | tracing |
| Which step of the request failed? | tracing |
| What did the code decide, and with what values? | logs |
| Should this instance get traffic? | probes |
| Should this process be restarted? | probes |

The common failure is reaching for the wrong one: putting a high-cardinality user id in a metric tag, where it multiplies time series until the monitoring system falls over, when it belongs on a span
attribute; or checking a database in a liveness probe, where a two-second outage restarts the entire fleet, when it belongs in readiness — or in a [CircuitBreaker](../documentation/resilient.md#circuitbreaker).

### Observability in Kora { #observability-kora }

Kora wires observability through modules and configuration. Framework components emit telemetry on their own once their module is connected and enabled; application code adds the business signals the
framework cannot name.

In the assembled application:

- `MetricsModule` puts a `MeterRegistry` in the graph and backs the `/metrics` endpoint
- `OpentelemetryHttpExporterModule` creates spans and exports them, and provides `KoraTracer`
- `LogbackModule` renders log records, including the trace identifiers
- `UndertowPublicHttpServerModule` serves the business API and, through the system server it extends, `/metrics` and both probes
- `MetricsService`, `KoraTracer` calls, and probe components carry the application-specific parts

### Operational Boundaries { #operational-boundaries }

Every operational endpoint lives on the system port, never the public one. Business clients get `8080`; Prometheus, the kubelet, and your monitoring agent get `8085`. That separation is what lets you
expose health and metrics to the platform without exposing them to the internet, and it is the default in Kora rather than something you assemble.

## Focused Guides { #focused-guides }

Each signal has its own guide with the full step-by-step treatment:

[Metrics with Kora](observability-metrics.md):
: Micrometer, the `MeterRegistry`, counters and timers, histogram buckets, tag cardinality, and why `/metrics` shows only JVM values until you enable module metrics.

[Tracing with Kora](observability-tracing.md):
: The OTLP exporter, service identity, business spans with `KoraTracer`, span attributes and errors, trace context propagation, and reading a trace in Jaeger.

[Probes with Kora](observability-probes.md):
: Liveness and readiness, warm-up, aggregation across several probes, built-in framework probes, the response contract, and Kubernetes wiring.

For reference detail behind any of them, see [Metrics](../documentation/metrics.md), [Tracing](../documentation/tracing.md), [Probes](../documentation/probes.md), and [Logging](../documentation/logging-slf4j.md).

## Dependencies { #dependencies }

The assembled application adds two artifacts to the HTTP server guide's build. Versions come from the `io.koraframework:kora-bom` platform.

===! ":fontawesome-brands-java: `Java`"

    Update `build.gradle`:

    ```groovy
    dependencies {
        // ... existing dependencies from the HTTP server guide ...

        implementation "io.koraframework:micrometer-module" //(1)!
        implementation "io.koraframework:opentelemetry-tracing-exporter-http" //(2)!
    }
    ```

    1.  Micrometer metrics: the `PrometheusMeterRegistry` and the scrape contract for the system server.
    2.  `OTLP/HTTP` span exporter. It transitively brings the core tracing wiring.

=== ":simple-kotlin: `Kotlin`"

    Update `build.gradle.kts`:

    ```kotlin
    dependencies {
        // ... existing dependencies from the HTTP server guide ...

        implementation("io.koraframework:micrometer-module") //(1)!
        implementation("io.koraframework:opentelemetry-tracing-exporter-http") //(2)!
    }
    ```

    1.  Micrometer metrics: the `PrometheusMeterRegistry` and the scrape contract for the system server.
    2.  `OTLP/HTTP` span exporter. It transitively brings the core tracing wiring.

Logging and probes add nothing: `LogbackModule` came with the HTTP server guide, and the probe interfaces arrive transitively in `io.koraframework:common`.

## Modules { #modules }

The complete graph for an application carrying all four signals:

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/java/io/koraframework/guide/observability/Application.java`:

    ```java
    package io.koraframework.guide.observability;

    import io.koraframework.application.graph.KoraApplication;
    import io.koraframework.common.annotation.KoraApp;
    import io.koraframework.config.hocon.HoconConfigModule;
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule;
    import io.koraframework.json.common.JsonModule;
    import io.koraframework.logging.logback.LogbackModule;
    import io.koraframework.micrometer.module.MetricsModule;
    import io.koraframework.opentelemetry.tracing.exporter.http.OpentelemetryHttpExporterModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule, //(1)!
            MetricsModule, //(2)!
            UndertowPublicHttpServerModule, //(3)!
            OpentelemetryHttpExporterModule { //(4)!

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

    1.  Logging, including the `traceId` and `spanId` fields on every log line inside a traced operation.
    2.  Metrics: adds `MeterRegistry` and the `MetricsScraper` the system server uses for `/metrics`.
    3.  Public HTTP server; extends the system server that serves `/metrics` and both probes.
    4.  Tracing: creates spans, exports them over `OTLP/HTTP`, and provides `KoraTracer`.

=== ":simple-kotlin: `Kotlin`"

    Update `src/main/kotlin/io/koraframework/guide/observability/Application.kt`:

    ```kotlin
    package io.koraframework.guide.observability

    import io.koraframework.application.graph.KoraApplication
    import io.koraframework.common.annotation.KoraApp
    import io.koraframework.config.hocon.HoconConfigModule
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule
    import io.koraframework.json.common.JsonModule
    import io.koraframework.logging.logback.LogbackModule
    import io.koraframework.micrometer.module.MetricsModule
    import io.koraframework.opentelemetry.tracing.exporter.http.OpentelemetryHttpExporterModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule, //(1)!
        MetricsModule, //(2)!
        UndertowPublicHttpServerModule, //(3)!
        OpentelemetryHttpExporterModule //(4)!

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

    1.  Logging, including the `traceId` and `spanId` fields on every log line inside a traced operation.
    2.  Metrics: adds `MeterRegistry` and the `MetricsScraper` the system server uses for `/metrics`.
    3.  Public HTTP server; extends the system server that serves `/metrics` and both probes.
    4.  Tracing: creates spans, exports them over `OTLP/HTTP`, and provides `KoraTracer`.

There is no separate management module to connect. `UndertowPublicHttpServerModule` extends `UndertowSystemHttpServerModule`, so one `extends` clause gives you two servers: the public one on
`httpServer.port` and the system one on `httpServer.system.port` answering `/metrics`, `/system/liveness`, and `/system/readiness`.

## Configuration { #config }

The complete observability configuration for the assembled application:

```hocon title="src/main/resources/application.conf"
httpServer {
  port = 8080 //(1)!
  system {
    port = 8085 //(2)!
    metricsPath = "/metrics" //(3)!
    livenessPath = "/system/liveness" //(4)!
    readinessPath = "/system/readiness" //(5)!
  }
  telemetry.logging.enabled = true //(6)!
  telemetry.metrics.enabled = true //(7)!
}

tracing {
  exporter {
    endpoint = "http://localhost:4318/v1/traces" //(8)!
    exportTimeout = "5s"
    scheduleDelay = "1s" //(9)!
    maxExportBatchSize = 512
    maxQueueSize = 2048
  }
  attributes { //(10)!
    "service.name" = "guide-observability-app"
    "service.namespace" = "kora-guide"
  }
}

logging {
  levels { //(11)!
    "ROOT": "WARN"
    "io.koraframework": "INFO"
    "io.koraframework.guide.observability": "DEBUG"
  }
}
```

1.  Public HTTP port used by application endpoints (default: `8080`).
2.  System HTTP port serving metrics and probes (default: `8085`).
3.  Prometheus scrape path on the system server (default: `/metrics`).
4.  Liveness path on the system server (default: `/system/liveness`).
5.  Readiness path on the system server (default: `/system/readiness`).
6.  Enables request logging for the public HTTP server (default: `false`).
7.  Enables metric collection for the public HTTP server (default: `false`).
8.  Collector endpoint spans are exported to (no default; without it nothing is exported).
9.  Batching delay, lowered from the `2s` default so local traces appear promptly.
10.  Service identity attached to every exported span (default: `{}`).
11.  Log levels per logger name.

### Telemetry Defaults { #telemetry-defaults }

!!! warning "Tracing is on by default. Metrics and logging are not."

    `TelemetryConfig.TracingConfig#enabled` returns `true`, while `MetricsConfig#enabled` and `LoggingConfig#enabled` both return `false`. Every Kora module inherits those defaults.

This asymmetry catches people out, so it is worth stating plainly. An application that connects `MetricsModule` and nothing else starts fine and answers `/metrics` with `200` — but the body holds only
JVM, process, and `kora.up` values. There is no `http_server_request_duration_seconds`, no `http_client_*`, no `db_*`, and nothing in the log explains why. The module's own
`telemetry.metrics.enabled` has to be `true` as well.

Tracing works the other way. Connect an exporter module, set an endpoint, and spans flow without any further switch. The thing that silently disables tracing is a *missing* endpoint: with no
`tracing.exporter.endpoint`, spans are still created and the trace context still propagates, they are simply never sent anywhere — and again, nothing is logged about it.

Custom metrics you register yourself through `MeterRegistry` are not affected by any of this. They appear as soon as `MetricsModule` is connected and the code runs, because the registry is always live.
The flag only gates the telemetry of Kora modules.

The system server is the deliberate exception in the other direction: `SystemHttpServerConfig` overrides its tracing to `false`, so an orchestrator polling readiness every few seconds does not bury
your real traces.

## Logging { #logging }

The Logback configuration from the HTTP server guide is what makes logs correlate with traces:

```xml title="src/main/resources/logback.xml"
<configuration debug="false">
    <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
        <encoder class="io.koraframework.logging.logback.ConsoleTextRecordEncoder"/>
    </appender>

    <appender name="ASYNC" class="io.koraframework.logging.logback.KoraAsyncAppender">
        <appender-ref ref="STDOUT"/>
    </appender>

    <root level="WARN">
        <appender-ref ref="ASYNC"/>
    </root>
</configuration>
```

`KoraAsyncAppender` captures the current span context at the moment a log event is queued, and `ConsoleTextRecordEncoder` writes `traceId=` and `spanId=` into the line whenever that captured context
is valid. Both appenders are needed: without the async appender there is no captured span context, and without the encoder it is never written out.

Levels come from the `logging.levels` config section rather than from this file, which is what lets you raise a logger at runtime without rebuilding the image.

## Signals Together { #signals-together }

Once all four are connected, one business operation produces all four signals at once. The service layer is where they meet, because that is where the domain meaning lives:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class UserService {

        private static final Logger logger = LoggerFactory.getLogger(UserService.class);

        private final UserRepository userRepository;
        private final MetricsService metricsService;
        private final KoraTracer tracer;

        public UserService(UserRepository userRepository, MetricsService metricsService, KoraTracer tracer) {
            this.userRepository = userRepository;
            this.metricsService = metricsService;
            this.tracer = tracer;
        }

        public UserResponse createUser(UserRequest request) {
            return tracer.traceParent("user.create", span -> { //(1)!
                logger.info("Creating user with name={}", request.name()); //(2)!

                return metricsService.recordUserCreation(() -> { //(3)!
                    var generatedId = userRepository.save(request.name(), request.email());
                    span.setAttribute("user.id", generatedId); //(4)!
                    logger.info("Created user with id={}", generatedId);
                    return new UserResponse(generatedId, request.name(), request.email(), LocalDateTime.now());
                });
            });
        }
    }
    ```

    1.  Tracing: a business span nested under the HTTP server span.
    2.  Logging: this line carries `traceId` and `spanId` because it is inside the span.
    3.  Metrics: the counter and timer for the operation.
    4.  A high-cardinality value is fine on a span, and would not be fine as a metric tag.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class UserService(
        private val userRepository: UserRepository,
        private val metricsService: MetricsService,
        private val tracer: KoraTracer
    ) {
        private val logger = LoggerFactory.getLogger(UserService::class.java)

        fun createUser(request: UserRequest): UserResponse {
            return tracer.traceParent("user.create", KoraTracer.TraceCallable<UserResponse, RuntimeException> { span -> //(1)!
                logger.info("Creating user with name={}", request.name) //(2)!

                metricsService.recordUserCreation { //(3)!
                    val id = userRepository.save(request.name, request.email)
                    span.setAttribute("user.id", id) //(4)!
                    logger.info("Created user with id={}", id)
                    UserResponse(id, request.name, request.email, LocalDateTime.now())
                }
            })
        }
    }
    ```

    1.  Tracing: a business span nested under the HTTP server span.
    2.  Logging: this line carries `traceId` and `spanId` because it is inside the span.
    3.  Metrics: the counter and timer for the operation.
    4.  A high-cardinality value is fine on a span, and would not be fine as a metric tag.

`MetricsService` is the small component built in the [metrics guide](observability-metrics.md#metrics-service); probes stay in their own components, since nothing about them belongs in a request path.

One `POST /users` now leaves behind: a `user.creation.total` increment and a `user.creation.duration` sample, a `user.create` span nested in the HTTP span, two log lines carrying the same trace id, and
no change at all to the probes — which is correct, because creating a user says nothing about whether the instance should receive traffic.

## Docker Compose { #docker-compose }

Jaeger receives the exported traces locally:

```yaml title="docker-compose.yml"
services:
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686" #(1)!
      - "4318:4318" #(2)!
    environment:
      COLLECTOR_OTLP_ENABLED: "true"
```

1.  Jaeger UI.
2.  `OTLP/HTTP` receiver — the port `tracing.exporter.endpoint` points at.

## Check Application { #check-app }

Start the collector and the application:

```bash
docker compose up -d

./gradlew run
```

Exercise the business API:

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@example.com"}'
```

Then read all four signals back:

```bash
curl http://localhost:8085/metrics          # metrics
curl -i http://localhost:8085/system/liveness   # probes
curl -i http://localhost:8085/system/readiness
```

Traces are in the Jaeger UI at [http://localhost:16686](http://localhost:16686) under the `guide-observability-app` service, and the logs are on the application's own stdout:

```text
09:41:12.508 INFO  [kora-undertow-4] i.k.g.o.service.UserService - traceId=4bf92f3577b34da6a3ce929d0e0e4736 spanId=00f067aa0ba902b7 Created user with id=1
```

The `traceId` in that line is the same id the trace carries in Jaeger. That is the whole payoff of wiring the signals together rather than separately.

## Testing { #testing }

Observability is testable, and worth testing — a broken probe or a missing metric is usually discovered during an incident otherwise.

In-process, inject the pieces and assert on them directly:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(Application.class)
    class ObservabilityAppTest {

        @TestComponent
        private UserService userService;
        @TestComponent
        private MeterRegistry meterRegistry; //(1)!

        @Test
        void userCreationUpdatesCustomMetrics() {
            userService.createUser(new UserRequest("Alice", "alice@example.com"));

            var counter = meterRegistry.find("user.creation.total").counter();
            assertNotNull(counter);
            assertEquals(1.0d, counter.count());
        }
    }
    ```

    1.  The registry is an ordinary graph component, so a test can read the meters the code registered.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(Application::class)
    class ObservabilityAppTest {

        @TestComponent
        lateinit var userService: UserService
        @TestComponent
        lateinit var meterRegistry: MeterRegistry //(1)!

        @Test
        fun userCreationUpdatesCustomMetrics() {
            userService.createUser(UserRequest("Alice", "alice@example.com"))

            val counter = meterRegistry.find("user.creation.total").counter()
            assertNotNull(counter)
            assertEquals(1.0, counter!!.count())
        }
    }
    ```

    1.  The registry is an ordinary graph component, so a test can read the meters the code registered.

In a [black-box test](testing-black-box.md), wait on readiness to start the container, then assert on the system port — that `/metrics` contains `http_server_*` values, that both probes answer `200`,
and that the container's stdout contains `traceId=`. That last assertion is the cheapest possible regression test for "is tracing still wired up".

## Best Practices { #best-practices }

- Keep every operational endpoint on the system port and off the public `Service`.
- Enable module telemetry deliberately — metrics and logging are off by default, tracing is on.
- Observe business operations in the service layer, where logs, metrics, and trace context all meet.
- Keep high-cardinality values on span attributes, never on metric tags.
- Check internal state in probes, and external dependencies with a [CircuitBreaker](../documentation/resilient.md#circuitbreaker).
- Set `service.name` and keep it stable per environment.
- Keep personal data out of logs, span attributes, and metric tags alike.
- Assert on observability in tests; a signal nobody verifies is a signal that quietly disappears.

## Summary { #summary }

You assembled one application carrying all four signals: Micrometer metrics on the system port, OpenTelemetry traces exported over `OTLP/HTTP`, log lines correlated by `traceId`, and liveness and
readiness probes — with the public API contract unchanged. Each signal has a focused guide for the depth this page does not go into.

## Key Concepts { #key-concepts }

Metrics:
: aggregate numbers over time, for trends, rates, and alerting.

Tracing:
: the path of one request, for locating where time or correctness was lost.

Log correlation:
: `traceId` and `spanId` on log lines, joining what the code said to what the request did.

Probes:
: the liveness and readiness answers a platform acts on.

System port:
: the separate port serving `/metrics` and both probes, away from the business API.

Telemetry defaults:
: tracing on, metrics and logging off — per module, until enabled.

## Troubleshooting { #troubleshooting }

`/metrics` answers `200` but shows only JVM values:
: Set `<module>.telemetry.metrics.enabled = true`. It defaults to `false` for every module.

`/metrics` answers `# Metric Scraper disabled`:
: `MetricsModule` is not connected, so there is no `MetricsScraper` in the graph.

Nothing reaches the trace collector:
: Check `tracing.exporter.endpoint`. Without it, spans are created and propagated but never exported, silently.

Logs have no `traceId`:
: The line was logged outside a traced operation, or `logback.xml` is not using `KoraAsyncAppender` with `ConsoleTextRecordEncoder`.

Any operational endpoint answers `404`:
: You are on the public port. All of them live on `httpServer.system.port` (default: `8085`).

The application restarts in a loop:
: An external dependency is being checked in liveness. Move it to readiness.

Prometheus stores a huge number of series:
: A metric tag has an unbounded value set. Move that value to a span attribute.

## What's Next? { #whats-next }

- go deep on one signal in [Metrics](observability-metrics.md), [Tracing](observability-tracing.md), or [Probes](observability-probes.md)
- add focused component tests in [Testing with JUnit](testing-junit.md)
- verify the packaged application end to end in [Black-Box Testing](testing-black-box.md)
- connect telemetry to failures, retries, and circuit breakers in [Resilient Patterns](resilient.md)

## Help { #help }

- inspect the finished Java and Kotlin observability applications
- check reference detail in [Metrics](../documentation/metrics.md), [Tracing](../documentation/tracing.md), [Probes](../documentation/probes.md), and [Logging](../documentation/logging-slf4j.md)
- revisit [HTTP Server](http-server.md) for the base API shape
