---
description: "Explains Kora OpenTelemetry tracing with the OTLP/gRPC and OTLP/HTTP exporters, tracing configuration, trace context propagation, sampling, manual spans and carrying the trace context across threads. Use when working with OpentelemetryTracingModule, OpentelemetryGrpcExporterModule, OpentelemetryHttpExporterModule, KoraTracer, OpentelemetryContext, Tracer, Span, OTLP."
agent:
  use_when: "Use this file for Kora docs or implementation questions about OpenTelemetry tracing: choosing the OTLP/gRPC or OTLP/HTTP exporter, the tracing and tracing.exporter config sections, per-module telemetry.tracing options, W3C trace context propagation, sampling, creating spans manually and carrying the trace context to another thread; key triggers include OpentelemetryTracingModule, OpentelemetryGrpcExporterModule, OpentelemetryHttpExporterModule, OpentelemetryTracingConfig, KoraTracer, OpentelemetryContext, Tracer, Span, SpanProcessor, SpanExporter, Sampler, OTLP."
---

Tracing helps link separate application operations into a single execution chain and understand where a request spent time or failed.
Kora uses [`OpenTelemetry`](https://opentelemetry.io/docs/what-is-opentelemetry/) to create `Span` and to export them in the `OTLP` format.

Kora registers its own `ContextStorage` implementation for `OpenTelemetry`, so the current trace context is carried by a `ScopedValue` rather than by a thread local.
Because of that, `io.opentelemetry.context.Context.current()` and `io.opentelemetry.api.trace.Span.current()` return the correct values anywhere inside a traced operation, including on virtual threads.

Most `Span` are created for you: the HTTP server and client, the database, the `Kafka` consumer and producer, the gRPC server and client and other subsystems create their own spans through their telemetry,
and the trace context is carried between services with the [W3C Trace Context](https://www.w3.org/TR/trace-context/) standard.

Kora provides two mutually exclusive exporter modules, `OTLP/gRPC` and `OTLP/HTTP`; choose exactly one depending on the protocol your collector accepts.
Either exporter module transitively provides the core tracing wiring (`OpentelemetryTracingModule`), so no other tracing dependency is required.

For a step-by-step walkthrough before the reference details, see [Observability](../guides/observability.md).

## gRPC { #grpc }

The module exports tracing data to `OpenTelemetry Collector` through `OTLP/gRPC`.
It builds an `OtlpGrpcSpanExporter` behind a `BatchSpanProcessor`, and the typical collector endpoint is `http://localhost:4317`.

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) in `build.gradle`:
    ```groovy
    implementation "io.koraframework:opentelemetry-tracing-exporter-grpc"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends OpentelemetryGrpcExporterModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) in `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:opentelemetry-tracing-exporter-grpc")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : OpentelemetryGrpcExporterModule
    ```

The module is `io.koraframework.opentelemetry.tracing.exporter.grpc.OpentelemetryGrpcExporterModule` and it ships the `OkHttp` sender that the `OTLP/gRPC` exporter uses.

## HTTP { #http }

The module exports tracing data to `OpenTelemetry Collector` through `OTLP/HTTP`.
It builds an `OtlpHttpSpanExporter` behind a `BatchSpanProcessor`, and the typical collector endpoint is `http://localhost:4318/v1/traces`.

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) in `build.gradle`:
    ```groovy
    implementation "io.koraframework:opentelemetry-tracing-exporter-http"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends OpentelemetryHttpExporterModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) in `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:opentelemetry-tracing-exporter-http")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : OpentelemetryHttpExporterModule
    ```

The module is `io.koraframework.opentelemetry.tracing.exporter.http.OpentelemetryHttpExporterModule`.
Unlike the `OTLP/gRPC` module it sends over the `JDK` HTTP client sender and does not pull `OkHttp` into the application.

## Configuration { #configuration }

Tracing is described by two configuration sections.

The `tracing` section is described by `OpentelemetryTracingConfig` and is provided by `OpentelemetryTracingModule`:

- `enabled` — the global tracing switch (default: `true`). With `false` Kora installs a no-op `TracerProvider`, so no `Span` are recorded and nothing is exported.
- `attributes` — `OpenTelemetry Resource` attributes (default: `{}`).

The `tracing.exporter` section is described by `OpentelemetryGrpcExporterConfig` (for `OTLP/gRPC`) and `OpentelemetryHttpExporterConfig` (for `OTLP/HTTP`); both interfaces have the same field set, so switching the exporter module does not change the configuration.
If `tracing.exporter.endpoint` is not specified, no exporter and no span processor are created — the application starts and spans are still created and propagated, they are simply never sent to an external collector.

The `tracing.attributes` field defines `OpenTelemetry Resource` attributes that are attached to **every** exported `Span` of the whole service.
It is empty by default, so set at least the service name and namespace there, for example `service.name` and `service.namespace`, otherwise the collector receives spans without service identity.
These service-wide `Resource` attributes are different from per-module span attributes configured under `<module>.telemetry.tracing.attributes`, which are added only to the spans of a specific subsystem — see [Module tracing configuration](#module-config).

===! ":material-code-json: `Hocon`"

    ```javascript
    tracing {
      enabled = true //(1)!
      exporter {
        endpoint = "http://localhost:4317" //(2)!
        connectTimeout = "60s" //(3)!
        exportTimeout = "3s" //(4)!
        scheduleDelay = "2s" //(5)!
        maxExportBatchSize = 512 //(6)!
        maxQueueSize = 2048 //(7)!
        batchExportTimeout = "30s" //(8)!
        compression = "gzip" //(9)!
        exportUnsampledSpans = false //(10)!
        retryPolicy { //(11)!
          maxAttempts = 5 //(12)!
          initialBackoff = "1s" //(13)!
          maxBackoff = "5s" //(14)!
          backoffMultiplier = 1.5 //(15)!
        }
      }
      attributes { //(16)!
        "service.name" = "example-service"
        "service.namespace" = "kora"
      }
    }
    ```

    1. Enables tracing for the whole application (default: `true`).
    2. `OpenTelemetry Collector` endpoint for exporting traces (optional, no default). `gRPC` usually uses `http://localhost:4317`, and `HTTP` usually uses `http://localhost:4318/v1/traces`.
    3. Timeout for establishing a connection to the exporter (optional, no default — the `OpenTelemetry` exporter default applies).
    4. Maximum time to wait while the exporter sends one `OTLP` request (default: `3s`).
    5. Delay between sending accumulated `Span` to the collector (default: `2s`).
    6. Maximum number of `Span` in one export batch (default: `512`).
    7. Maximum queue size for `Span` waiting to be sent (default: `2048`).
    8. Maximum time the `BatchSpanProcessor` waits for one accumulated batch to be exported; this is distinct from `exportTimeout`, which bounds a single `OTLP` request (default: `30s`).
    9. Data compression used during export, `gzip` or `none` (default: `gzip`).
    10. Whether to export `Span` that were not selected by `Sampler` (default: `false`).
    11. Retry policy applied to failed export attempts (optional, the whole block may be omitted and every value below then takes its default).
    12. Maximum number of retry attempts (default: `5`).
    13. Initial delay before a retry attempt (default: `1s`).
    14. Maximum delay before a retry attempt (default: `5s`).
    15. Delay multiplier between retry attempts (default: `1.5`).
    16. `OpenTelemetry Resource` attributes added to every exported `Span` (default: `{}`).

=== ":simple-yaml: `YAML`"

    ```yaml
    tracing:
      enabled: true #(1)!
      exporter:
        endpoint: http://localhost:4317 #(2)!
        connectTimeout: 60s #(3)!
        exportTimeout: 3s #(4)!
        scheduleDelay: 2s #(5)!
        maxExportBatchSize: 512 #(6)!
        maxQueueSize: 2048 #(7)!
        batchExportTimeout: 30s #(8)!
        compression: gzip #(9)!
        exportUnsampledSpans: false #(10)!
        retryPolicy: #(11)!
          maxAttempts: 5 #(12)!
          initialBackoff: 1s #(13)!
          maxBackoff: 5s #(14)!
          backoffMultiplier: 1.5 #(15)!
      attributes: #(16)!
        service.name: example-service
        service.namespace: kora
    ```

    1. Enables tracing for the whole application (default: `true`).
    2. `OpenTelemetry Collector` endpoint for exporting traces (optional, no default). `gRPC` usually uses `http://localhost:4317`, and `HTTP` usually uses `http://localhost:4318/v1/traces`.
    3. Timeout for establishing a connection to the exporter (optional, no default — the `OpenTelemetry` exporter default applies).
    4. Maximum time to wait while the exporter sends one `OTLP` request (default: `3s`).
    5. Delay between sending accumulated `Span` to the collector (default: `2s`).
    6. Maximum number of `Span` in one export batch (default: `512`).
    7. Maximum queue size for `Span` waiting to be sent (default: `2048`).
    8. Maximum time the `BatchSpanProcessor` waits for one accumulated batch to be exported; this is distinct from `exportTimeout`, which bounds a single `OTLP` request (default: `30s`).
    9. Data compression used during export, `gzip` or `none` (default: `gzip`).
    10. Whether to export `Span` that were not selected by `Sampler` (default: `false`).
    11. Retry policy applied to failed export attempts (optional, the whole block may be omitted and every value below then takes its default).
    12. Maximum number of retry attempts (default: `5`).
    13. Initial delay before a retry attempt (default: `1s`).
    14. Maximum delay before a retry attempt (default: `5s`).
    15. Delay multiplier between retry attempts (default: `1.5`).
    16. `OpenTelemetry Resource` attributes added to every exported `Span` (default: `{}`).

The example project uses environment substitution for the endpoint and overrides a few export parameters:

===! ":material-code-json: `Hocon`"

    ```javascript
    tracing {
      exporter {
        endpoint = ${METRIC_COLLECTOR_ENDPOINT} //(1)!
        exportTimeout = "250s"
        scheduleDelay = "50ms"
        maxExportBatchSize = 10000
      }
      attributes {
        "service.name" = "kora-java-telemetry"
        "service.namespace" = "kora"
      }
    }
    ```

    1. Resolved from the `METRIC_COLLECTOR_ENDPOINT` environment variable, see [environment substitution](config.md#environment-variables).

=== ":simple-yaml: `YAML`"

    ```yaml
    tracing:
      exporter:
        endpoint: ${METRIC_COLLECTOR_ENDPOINT} #(1)!
        exportTimeout: "250s"
        scheduleDelay: "50ms"
        maxExportBatchSize: 10000
      attributes:
        service.name: "kora-java-telemetry"
        service.namespace: "kora"
    ```

    1. Resolved from the `METRIC_COLLECTOR_ENDPOINT` environment variable, see [environment substitution](config.md#environment-variables).

If the application also has the [metrics](metrics.md) module, its `MeterProvider` is handed to the exporter and the span processor, and they report their own internal metrics through the same registry.

## Automatic tracing { #automatic }

A tracing module in the application graph provides a `Tracer` component.
Every Kora subsystem that has telemetry picks that `Tracer` up and starts creating `Span` for its own operations: for every incoming request, outgoing call, message, query or scheduled run it opens a `Span`, binds it to the current context, nests it under the currently active `Span` and closes it when the operation ends.
No annotations or manual code are required for these `Span`.

For example, the `GET /text` controller from the telemetry example produces a `SERVER` span named `GET /text`, with the repository query nested inside it as a `CLIENT` span:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface TraceRepository extends JdbcRepository {

        @Query("SELECT 1")
        int selectOne();
    }

    @Component
    @HttpController
    public final class SimpleController {

        private final TraceRepository repository;

        public SimpleController(TraceRepository repository) {
            this.repository = repository;
        }

        @HttpRoute(method = HttpMethod.GET, path = "/text")
        public HttpServerResponse get() {
            var databaseValue = repository.selectOne();
            return HttpServerResponse.of(200, HttpBody.plaintext("Hello world: " + databaseValue));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface TraceRepository : JdbcRepository {

        @Query("SELECT 1")
        fun selectOne(): Int
    }

    @Component
    @HttpController
    class SimpleController(private val repository: TraceRepository) {

        @HttpRoute(method = HttpMethod.GET, path = "/text")
        fun get(): HttpServerResponse {
            val databaseValue = repository.selectOne()
            return HttpServerResponse.of(200, HttpBody.plaintext("Hello world: $databaseValue"))
        }
    }
    ```

The table below lists the subsystems that create `Span`, the resulting span name and [kind](https://opentelemetry.io/docs/specs/otel/trace/api/#spankind), and the main attributes.
Attribute names follow the [OpenTelemetry Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/).

| Subsystem      | Span name                                        | Kind                    | Key attributes                                                                                                                                                     |
|----------------|--------------------------------------------------|-------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| HTTP server    | `<METHOD> <route>`, e.g. `GET /text`             | `SERVER`                | `http.request.method`, `http.route`, `url.scheme`, `url.path`, `server.address`, `server.port`, `server.name`, `http.response.status_code`, `http.response.result_code` |
| HTTP client    | `<METHOD> <uriTemplate>`                         | `CLIENT`                | `http.request.method`, `http.route`, `server.address`, `server.port`, `url.scheme`, `url.path`, `url.full`, `http.response.status_code`, `http.response.result_code`    |
| Database       | `<Repository>.<method>`                          | `CLIENT`                | `db.system.name`, `db.query.text`                                                                                                                                    |
| Kafka consumer | `kafka.poll`, `<topic> process record`           | `CONSUMER`              | `messaging.system` = `kafka`, `messaging.client.id`, `messaging.consumer.group.name`, `messaging.destination.name`, `messaging.destination.partition.id`, `messaging.kafka.offset` |
| Kafka producer | `<topic> send`, `producer transaction`           | `PRODUCER` / `INTERNAL` | `messaging.system` = `kafka`, `messaging.operation.type` = `send`, `messaging.destination.name`                                                                       |
| gRPC server    | `<service>/<method>`                             | `SERVER`                | `rpc.system` = `grpc`, `rpc.service`, `rpc.method`, `server.port`, `server.name`, `network.peer.address`                                                              |
| gRPC client    | `<fullMethodName>`                               | `CLIENT`                | `rpc.system` = `grpc`, `rpc.service`, `rpc.method`, `server.address`, `server.port`                                                                                  |
| SOAP client    | `SOAP <service> <method>`                        | `CLIENT`                | `rpc.system` = `soap`, `rpc.service`, `rpc.method`, `server.address`, `server.port`                                                                                  |
| S3 client      | `S3.<operation>`                                 | `CLIENT`                | `rpc.system` = `s3`, `rpc.method`, `aws.s3.bucket`                                                                                                                   |
| JMS consumer   | `<destination> receive`                          | `CONSUMER`              | `messaging.system` = `jms`, `messaging.destination.name`, `messaging.message.id`                                                                                    |
| Scheduling     | `scheduling <class>`                             | `INTERNAL`              | `code.function.name`                                                                                                                                                 |
| Redis cache    | `cache.operation`                                | `INTERNAL`              | `operation`, `origin` = `redis`                                                                                                                                      |
| Camunda BPMN   | `Camunda Delegate <name>`                        | `INTERNAL`              | `delegate`                                                                                                                                                           |
| Camunda REST   | `<METHOD> <route>`                               | `SERVER`                | `http.request.method`, `http.route`, `url.scheme`, `url.path`, `server.address`                                                                                      |
| Zeebe worker   | `Zeebe Worker <type>`                            | `INTERNAL`              | `jobType`, `jobName`, `jobKey`, `jobWorker`, `processKey`, `elementId`                                                                                              |

Spans produced by a *named* component also carry attributes that say which declaration they came from: `system.config` (the configuration path of the component), `system.name.simple` and `system.name.canonical` (the simple and canonical class name of the declaration).
They are set by the HTTP client, the `Kafka` consumer and producer, the SOAP and S3 clients, caches and scheduled jobs; the AWS S3 client names the first one `system.path` instead of `system.config`.

A few more details worth knowing:

- The HTTP server creates a span only for a request that matched a route, because the span name is built from the route template. Requests that end in `404` because no route matched produce no span.
- `url.path` and `url.full` are only added when `tracePathFull` (server) or `pathFull` (client) is enabled, which is the default — turn them off to keep identifiers out of the trace.
- The `Kafka` consumer opens a `kafka.poll` span for the whole poll and one `<topic> process record` span per record; the per-record span is parented to the context extracted from the record headers and is *linked* to the `kafka.poll` span.
- The `Caffeine` cache and the [resilience](resilient.md) aspects report metrics and logs but do not create spans.
- On failure Kora sets the span status to `ERROR` and records the exception via `Span#recordException`. Most subsystems also set `OK` on success; the HTTP server and HTTP client leave a successful span `UNSET` and only mark `ERROR` for a `4xx`/`5xx` status or a connection failure.

## Module tracing configuration { #module-config }

Tracing of each subsystem is configured under that module's `telemetry.tracing` section, described by `io.koraframework.telemetry.common.TelemetryConfig.TracingConfig`.
Two options are available for every subsystem:

- `enabled` (default: `true`) — turns the subsystem's spans on or off. Set to `false` to stop creating spans for a specific module without removing the exporter.
- `attributes` (default: `{}`) — a map of key/value pairs added to every span produced **by that module only**. These per-span attributes differ from the service-wide `tracing.attributes` (`Resource` attributes) that apply to all spans.

Note that `enabled` defaults to `true` here, unlike `telemetry.logging.enabled` and `telemetry.metrics.enabled`, which default to `false`.
Two groups of modules override that default to `false`: the [system HTTP server](http-server.md) (`httpServer.system.telemetry.tracing`) and the [resilience](resilient.md) aspects.

The `telemetry.tracing` section lives at the same path as the module's own configuration:

| Subsystem            | Configuration path                                                       |
|----------------------|--------------------------------------------------------------------------|
| HTTP server          | `httpServer.telemetry.tracing`                                            |
| System HTTP server   | `httpServer.system.telemetry.tracing`                                     |
| HTTP client          | `httpClient.<name>.telemetry.tracing`                                     |
| JDBC database        | `jdbc.telemetry.tracing`                                                  |
| Cassandra database   | `cassandra.telemetry.tracing`                                             |
| gRPC server          | `grpcServer.telemetry.tracing`                                            |
| gRPC client          | `grpcClient.<ServiceName>.telemetry.tracing`                              |
| Kafka consumer       | `kafka.consumer.<name>.telemetry.tracing`                                 |
| Kafka producer       | `kafka.producer.<name>.telemetry.tracing`                                 |
| Scheduling           | `scheduling.telemetry.tracing`                                            |
| Cache                | `<cache config path>.telemetry.tracing`                                   |

Two subsystems add an option of their own on top of `enabled` and `attributes`:

- `httpServer.telemetry.tracing.tracePathFull` (default: `true`) — adds `url.path` with the real request path to the server span.
- `httpClient.<name>.telemetry.tracing.pathFull` (default: `true`) — adds `url.path` and `url.full` with the real request URI to the client span.

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
      telemetry {
        tracing {
          enabled = true //(1)!
          tracePathFull = true //(2)!
          attributes { //(3)!
            "component" = "gateway"
          }
        }
      }
    }
    jdbc {
      telemetry {
        tracing {
          enabled = false //(4)!
        }
      }
    }
    ```

    1. Enables tracing for the HTTP server (default: `true`).
    2. Adds the real request path as `url.path` to the HTTP server span (default: `true`).
    3. Per-span attributes added only to HTTP server spans (default: `{}`).
    4. Disables tracing for database queries (default: `true`).

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      telemetry:
        tracing:
          enabled: true #(1)!
          tracePathFull: true #(2)!
          attributes: #(3)!
            component: "gateway"
    jdbc:
      telemetry:
        tracing:
          enabled: false #(4)!
    ```

    1. Enables tracing for the HTTP server (default: `true`).
    2. Adds the real request path as `url.path` to the HTTP server span (default: `true`).
    3. Per-span attributes added only to HTTP server spans (default: `{}`).
    4. Disables tracing for database queries (default: `true`).

Module-specific tracing parameters are also described in those modules' own documentation, for example [HTTP server](http-server.md), [HTTP client](http-client.md), [gRPC server](grpc-server.md), [gRPC client](grpc-client.md), and [Kafka](kafka.md).

## Context propagation { #propagation }

Kora stitches distributed traces together with the [W3C Trace Context](https://www.w3.org/TR/trace-context/) standard through `W3CTraceContextPropagator`.
This happens automatically and requires no configuration:

- **HTTP server** — `traceparent` is extracted from the request headers and becomes the parent of the server `Span`; the identifiers of that span are then written back into the **response** headers, so a caller can correlate the response with the trace.
- **Kafka** — `traceparent` is injected into the record headers by the producer and extracted from the record headers by the consumer, so each `<topic> process record` span continues the producer's trace.
- **gRPC client** — `traceparent` is injected into the call metadata.
- **gRPC server** — `traceparent` is extracted from the call metadata and injected back into the response headers metadata.
- **JMS consumer** — `traceparent` is extracted from the message properties.
- **Camunda REST and Zeebe worker** — `traceparent` is extracted from the request headers and the job headers respectively.

The Kora HTTP client is the exception: it opens a `CLIENT` span for the outgoing call so the call is visible in your own trace, but it does **not** write `traceparent` into the outgoing request.
If a downstream service has to continue the same trace, add the header yourself in an `HttpServerInterceptor`-style [HTTP client interceptor](http-client.md).

Within one service nothing has to be propagated by hand: the current `Span` lives in a `ScopedValue`, so a span you create manually (see [Synchronous tracing](#tracing-sync)) automatically becomes the parent of everything called inside it, in the same thread.
Crossing a thread boundary is the one case that needs explicit work — see [Asynchronous tracing](#async-tracing).

## Sampling { #sampling }

The core tracing components are provided by `OpentelemetryTracingModule` as `@DefaultComponent`, which means each of them can be replaced by declaring your own component of the same type:

- `Sampler` — decides which `Span` are recorded. The default is `Sampler.parentBased(Sampler.alwaysOn())`, i.e. record every root `Span` and follow the parent's decision for child `Span`.
- `IdGenerator` — generates trace and span identifiers. The default is `IdGenerator.random()`.
- `Supplier<SpanLimits>` — limits on attributes, events, and links per `Span`. The default is `SpanLimits.getDefault()`.
- `KoraTracer` — the helper used for [manual spans](#tracing-sync).

The exporter modules declare `SpanExporter` and `SpanProcessor` as `@DefaultComponent` too, so an application can send spans somewhere else entirely by providing its own.

To apply head-based sampling, override the `Sampler` factory method in your application, for example to record roughly 10% of root traces:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends OpentelemetryGrpcExporterModule {

        @Override
        default Sampler opentelemetryTracingSampler() {
            return Sampler.parentBased(Sampler.traceIdRatioBased(0.1));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : OpentelemetryGrpcExporterModule {

        override fun opentelemetryTracingSampler(): Sampler {
            return Sampler.parentBased(Sampler.traceIdRatioBased(0.1))
        }
    }
    ```

The `exportUnsampledSpans` export option controls whether `Span` that were **not** selected by the `Sampler` are still sent to the collector; it is `false` by default, so only sampled `Span` are exported.

## Tracing context { #tracing-context }

The current trace context is read through the standard `OpenTelemetry` API — Kora plugs its own storage behind it, so no Kora-specific accessor is needed.

To get the current `Span`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var span = io.opentelemetry.api.trace.Span.current();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val span = io.opentelemetry.api.trace.Span.current()
    ```

To get the current trace identifier:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var traceId = io.opentelemetry.api.trace.Span.current().getSpanContext().getTraceId();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val traceId = io.opentelemetry.api.trace.Span.current().getSpanContext().getTraceId()
    ```

When there is no current `Span`, `Span.current()` returns `Span.getInvalid()` and its `SpanContext` reports `isValid() == false` with an all-zero trace identifier, so these calls never return `null` and never throw.

The pieces that make this work live in `io.koraframework.common.telemetry`:

- `OpentelemetryContext` — an implementation of `io.opentelemetry.context.Context` backed by `ScopedValue`. Kora registers it as an `OpenTelemetry` `ContextStorageProvider`, which is why `Context.current()` and `Span.current()` work on any thread that Kora entered, virtual threads included.
- `OpentelemetryContext.VALUE` — the `ScopedValue<Context>` itself. Binding it with `ScopedValue.where(OpentelemetryContext.VALUE, ctx)` is how a context is made current; `Context#makeCurrent()` is deliberately unsupported and throws `IllegalStateException`, because a scoped value cannot be attached and detached imperatively.
- `Observation` — the per-operation telemetry object of the module that is currently running, also bound to a `ScopedValue`. `Observation.current(HttpServerObservation.class)` returns it and `observation.span()` gives the module's own span; it throws if there is no bound observation of that type.

## Log correlation { #mdc }

Log correlation is done by the [Logback module](logging-slf4j.md#logback): `KoraAsyncAppender` captures `Span.current().getSpanContext()` at the moment the event is queued, and `ConsoleTextRecordEncoder` writes `traceId=` and `spanId=` into the log line whenever that span context is valid.

```xml
<appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
    <encoder class="io.koraframework.logging.logback.ConsoleTextRecordEncoder"/>
</appender>

<appender name="ASYNC" class="io.koraframework.logging.logback.KoraAsyncAppender">
    <appender-ref ref="STDOUT"/>
</appender>
```

As a result every log line emitted within a traced operation carries the `traceId` and `spanId`, which lets you jump from a log entry to the corresponding trace in your observability backend and back.
Lines logged outside any traced operation simply have no such fields.

The Kora [MDC](logging-slf4j.md#mdc) is a separate mechanism for your own structured fields — the trace identifiers do not go through it, so nothing has to be put into or removed from `MDC` around a span.

## Synchronous tracing { #tracing-sync }

In addition to `Span` created by the framework, you can create your own.
The simplest way is the `KoraTracer` component: it builds the `Span`, binds it as the current context for the duration of the call, sets the status, records an exception if one is thrown, and ends the span — all in one call.

- `traceParent(name, …)` — creates a `Span` nested under the currently active one.
- `traceNew(name, …)` — creates a root `Span` with no parent, for work that must start its own trace.
- `tracer()` — returns the underlying `io.opentelemetry.api.trace.Tracer` when you need full control.

Each of them accepts either a `TraceCallable`, which returns a value, or a `TraceRunnable`, which does not; both receive the created `Span` so that attributes and events can be added to it.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MyService {

        private final KoraTracer tracer;

        public MyService(KoraTracer tracer) {
            this.tracer = tracer;
        }

        public String doTraceWork(String userId) {
            return tracer.traceParent("myOperation", span -> {
                span.setAttribute("user.id", userId);
                return doWork(userId);
            });
        }

        private String doWork(String userId) {
            // do some work
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyService(private val tracer: KoraTracer) {

        fun doTraceWork(userId: String): String {
            return tracer.traceParent("myOperation", KoraTracer.TraceCallable<String, RuntimeException> { span -> //(1)!
                span.setAttribute("user.id", userId)
                doWork(userId)
            })
        }

        private fun doWork(userId: String): String {
            // do some work
        }
    }
    ```

    1. `traceParent` is overloaded for `TraceCallable` and `TraceRunnable`, and `Kotlin` cannot choose between two functional interfaces on its own — pass the explicit SAM constructor.

If you need something `KoraTracer` does not cover, such as a custom span kind or a link to another trace, build the `Span` from the `Tracer` yourself and bind it as the current context for the duration of the operation:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MyService {

        private final Tracer tracer;

        public MyService(Tracer tracer) {
            this.tracer = tracer;
        }

        public String doTraceWork() {
            var span = tracer.spanBuilder("myOperation")
                .setSpanKind(SpanKind.INTERNAL)
                .setParent(io.opentelemetry.context.Context.current())
                .startSpan();

            return ScopedValue.where(OpentelemetryContext.VALUE, io.opentelemetry.context.Context.current().with(span))
                .call(() -> {
                    try {
                        var result = doWork();
                        span.setStatus(StatusCode.OK);
                        return result;
                    } catch (Exception e) {
                        span.recordException(e);
                        span.setStatus(StatusCode.ERROR, e.getMessage());
                        throw e;
                    } finally {
                        span.end();
                    }
                });
        }

        private String doWork() {
            // do some work
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyService(private val tracer: Tracer) {

        fun doTraceWork(): String {
            val span = tracer.spanBuilder("myOperation")
                .setSpanKind(SpanKind.INTERNAL)
                .setParent(io.opentelemetry.context.Context.current())
                .startSpan()

            val carrier = ScopedValue.where(
                OpentelemetryContext.VALUE,
                io.opentelemetry.context.Context.current().with(span)
            )
            return carrier.call<String, RuntimeException> {
                try {
                    val result = doWork()
                    span.setStatus(StatusCode.OK)
                    result
                } catch (e: Exception) {
                    span.recordException(e)
                    span.setStatus(StatusCode.ERROR, e.message)
                    throw e
                } finally {
                    span.end()
                }
            }
        }

        private fun doWork(): String {
            // do some work
        }
    }
    ```

## Asynchronous tracing { #async-tracing }

The trace context is a `ScopedValue`, and a scoped value is visible only inside the dynamic scope that bound it.
Handing work to another thread therefore drops the context unless you carry it over explicitly: capture `io.opentelemetry.context.Context.current()` in the calling thread and re-bind it in the worker thread.

`OpentelemetryContext` implements the `wrap` family of the `OpenTelemetry` `Context` interface on top of `ScopedValue`, so wrapping the task is usually all that is needed — `wrap(Runnable)`, `wrap(Callable)`, `wrapSupplier`, `wrapFunction` and `wrapConsumer` are all available.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MyService {

        private final KoraTracer tracer;
        private final ExecutorService executor;

        public MyService(KoraTracer tracer, ExecutorService executor) {
            this.tracer = tracer;
            this.executor = executor;
        }

        public CompletableFuture<String> doTraceWork() {
            return tracer.traceParent("myOperation", span -> {
                var ctx = io.opentelemetry.context.Context.current(); //(1)!
                return CompletableFuture.supplyAsync(ctx.wrapSupplier(this::doWork), executor); //(2)!
            });
        }

        private String doWork() {
            // runs on another thread, but Span.current() is still the "myOperation" span
        }
    }
    ```

    1. Captured while the span is still current, so it already contains the `myOperation` span.
    2. `wrapSupplier` re-binds that context around the call in the worker thread.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyService(private val tracer: KoraTracer, private val executor: ExecutorService) {

        fun doTraceWork(): CompletableFuture<String> {
            return tracer.traceParent("myOperation", KoraTracer.TraceCallable<CompletableFuture<String>, RuntimeException> { span ->
                val ctx = io.opentelemetry.context.Context.current() //(1)!
                CompletableFuture.supplyAsync(ctx.wrapSupplier { doWork() }, executor) //(2)!
            })
        }

        private fun doWork(): String {
            // runs on another thread, but Span.current() is still the "myOperation" span
        }
    }
    ```

    1. Captured while the span is still current, so it already contains the `myOperation` span.
    2. `wrapSupplier` re-binds that context around the call in the worker thread.

Note that `KoraTracer` ends the span as soon as its callback returns, which for the example above is before the future completes.
When the span has to cover the whole asynchronous operation, build it from the `Tracer` yourself as shown in [Synchronous tracing](#tracing-sync) and call `span.end()` from the completion callback.
