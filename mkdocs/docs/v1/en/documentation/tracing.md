---
description: "Explains Kora OpenTelemetry tracing over gRPC and HTTP, tracing configuration, trace context propagation, synchronous tracing, and asynchronous tracing. Use when working with OpentelemetryTracingModule, OpenTelemetry, OpentelemetryContext, Span, OTLP."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora OpenTelemetry tracing over gRPC and HTTP, tracing configuration, trace context propagation, synchronous tracing, and asynchronous tracing; key triggers include OpentelemetryTracingModule, OpenTelemetry, OpentelemetryContext, Span, OTLP."
---

Tracing helps link separate application operations into a single execution chain and understand where a request spent time or failed.
Kora uses [`OpenTelemetry`](https://opentelemetry.io/docs/what-is-opentelemetry/) to create `Span`, store the current tracing context in `OpentelemetryContext`, and export data in the `OTLP` format.

The current `Span` is stored in the Kora context, so it can be propagated between application components and used when manually creating nested `Span`.
When `OpentelemetryContext` is set, Kora also adds `traceId` and `spanId` to `MDC` so these identifiers appear in logs when the logging module is used.

Most `Span` are created automatically: the module instruments the HTTP server and client, database, `Kafka` consumer and producer, gRPC server and client, and other subsystems out of the box,
and propagates the trace context between services over the [W3C traceparent](https://www.w3.org/TR/trace-context/) standard.

Kora provides two mutually exclusive exporter modules, `OTLP/gRPC` and `OTLP/HTTP`; choose exactly one depending on the protocol your collector accepts.
Either exporter module transitively provides the core tracing wiring (`OpentelemetryTracingModule`) and the automatic instrumentation (`OpentelemetryModule`), so no other tracing dependency is required.

For a step-by-step walkthrough before the reference details, see [Observability](../guides/observability.md).

## gRPC { #grpc }

The module exports tracing data to `OpenTelemetry Collector` through `OTLP/gRPC`.
It builds an `OtlpGrpcSpanExporter` behind a `BatchSpanProcessor`, and the typical collector endpoint is `http://localhost:4317`.

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) in `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:opentelemetry-tracing-exporter-grpc"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends OpentelemetryGrpcExporterModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) in `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:opentelemetry-tracing-exporter-grpc")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : OpentelemetryGrpcExporterModule
    ```

## HTTP { #http }

The module exports tracing data to `OpenTelemetry Collector` through `OTLP/HTTP`.
It builds an `OtlpHttpSpanExporter` behind a `BatchSpanProcessor`, and the typical collector endpoint is `http://localhost:4318/v1/traces`.

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) in `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:opentelemetry-tracing-exporter-http"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends OpentelemetryHttpExporterModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) in `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:opentelemetry-tracing-exporter-http")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : OpentelemetryHttpExporterModule
    ```

## Configuration { #configuration }

Export parameters under `tracing.exporter` are described by `OpentelemetryGrpcExporterConfig` (for `OTLP/gRPC`) and `OpentelemetryHttpExporterConfig` (for `OTLP/HTTP`); both classes share the same field set.
Resource attributes under `tracing.attributes` are described by `OpentelemetryResourceConfig`.
If `tracing.exporter.endpoint` is not specified, no exporter is created (the config resolves to the internal `Empty` value and a no-op `SpanExporter`/`SpanProcessor` is used), and the application starts without sending traces to an external collector.

The `tracing.attributes` field defines `OpenTelemetry Resource` attributes that are attached to **every** exported `Span` of the whole service.
It usually contains the service name and namespace, for example `service.name` and `service.namespace`.
These service-wide `Resource` attributes are different from per-module span attributes configured under `<module>.telemetry.tracing.attributes`, which are added only to the spans of a specific subsystem — see [Module tracing configuration](#module-config).

===! ":material-code-json: `Hocon`"

    ```javascript
    tracing {
      exporter {
        endpoint = "http://localhost:4317" //(1)!
        connectTimeout = "60s" //(2)!
        exportTimeout = "3s" //(3)!
        scheduleDelay = "2s" //(4)!
        maxExportBatchSize = 512 //(5)!
        maxQueueSize = 2048 //(6)!
        batchExportTimeout = "30s" //(7)!
        compression = "gzip" //(8)!
        exportUnsampledSpans = false //(9)!
        retryPolicy {
          maxAttempts = 5 //(10)!
          initialBackoff = "1s" //(11)!
          maxBackoff = "5s" //(12)!
          backoffMultiplier = 1.5 //(13)!
        }
      }
      attributes { //(14)!
        "service.name" = "example-service"
        "service.namespace" = "kora"
      }
    }
    ```

    1. `OpenTelemetry Collector` endpoint for exporting traces (default: not specified, optional). `gRPC` usually uses `http://localhost:4317`, and `HTTP` usually uses `http://localhost:4318/v1/traces`.
    2. Timeout for establishing a connection to the exporter (default: not specified, optional).
    3. Maximum time to wait while the exporter sends data (default: `3s`).
    4. Delay between sending accumulated `Span` to the collector (default: `2s`).
    5. Maximum number of `Span` in one export batch (default: `512`).
    6. Maximum queue size for `Span` waiting to be sent (default: `2048`).
    7. Maximum time the `BatchSpanProcessor` waits for one accumulated batch to be exported; this is distinct from `exportTimeout`, which bounds a single `OTLP` request (default: `30s`).
    8. Data compression used during export, `gzip` or `none` (default: `gzip`).
    9. Whether to export `Span` that were not selected by `Sampler` (default: `false`).
    10. Maximum number of retry attempts (default: `5`).
    11. Initial delay before a retry attempt (default: `1s`).
    12. Maximum delay before a retry attempt (default: `5s`).
    13. Delay multiplier between retry attempts (default: `1.5`).
    14. `OpenTelemetry Resource` attributes added to exported `Span` (default: `{}`).

=== ":simple-yaml: `YAML`"

    ```yaml
    tracing:
      exporter:
        endpoint: http://localhost:4317 #(1)!
        connectTimeout: 60s #(2)!
        exportTimeout: 3s #(3)!
        scheduleDelay: 2s #(4)!
        maxExportBatchSize: 512 #(5)!
        maxQueueSize: 2048 #(6)!
        batchExportTimeout: 30s #(7)!
        compression: gzip #(8)!
        exportUnsampledSpans: false #(9)!
        retryPolicy:
          maxAttempts: 5 #(10)!
          initialBackoff: 1s #(11)!
          maxBackoff: 5s #(12)!
          backoffMultiplier: 1.5 #(13)!
      attributes: #(14)!
        service.name: example-service
        service.namespace: kora
    ```

    1. `OpenTelemetry Collector` endpoint for exporting traces (default: not specified, optional). `gRPC` usually uses `http://localhost:4317`, and `HTTP` usually uses `http://localhost:4318/v1/traces`.
    2. Timeout for establishing a connection to the exporter (default: not specified, optional).
    3. Maximum time to wait while the exporter sends data (default: `3s`).
    4. Delay between sending accumulated `Span` to the collector (default: `2s`).
    5. Maximum number of `Span` in one export batch (default: `512`).
    6. Maximum queue size for `Span` waiting to be sent (default: `2048`).
    7. Maximum time the `BatchSpanProcessor` waits for one accumulated batch to be exported; this is distinct from `exportTimeout`, which bounds a single `OTLP` request (default: `30s`).
    8. Data compression used during export, `gzip` or `none` (default: `gzip`).
    9. Whether to export `Span` that were not selected by `Sampler` (default: `false`).
    10. Maximum number of retry attempts (default: `5`).
    11. Initial delay before a retry attempt (default: `1s`).
    12. Maximum delay before a retry attempt (default: `5s`).
    13. Delay multiplier between retry attempts (default: `1.5`).
    14. `OpenTelemetry Resource` attributes added to exported `Span` (default: `{}`).

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

## Automatic tracing { #automatic }

Once one exporter module is added, Kora instruments its subsystems automatically: for every incoming request, outgoing call, message, query, or scheduled run it creates a `Span`, attaches it to the current `OpentelemetryContext`, nests it under the currently active `Span`, and propagates the trace context across service boundaries.
No annotations or manual code are required for these `Span`.

For example, the `GET /text` controller from the telemetry example produces a `SERVER` span named `GET /text` automatically:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SimpleController {

        @HttpRoute(method = HttpMethod.GET, path = "/text")
        public HttpServerResponse get() {
            return HttpServerResponse.of(200, HttpBody.plaintext("Hello world"));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SimpleController {

        @HttpRoute(method = HttpMethod.GET, path = "/text")
        fun get(): HttpServerResponse {
            return HttpServerResponse.of(200, HttpBody.plaintext("Hello world"))
        }
    }
    ```

The table below lists the subsystems instrumented by `OpentelemetryModule`, the resulting `Span` name and [kind](https://opentelemetry.io/docs/specs/otel/trace/api/#spankind), and the main attributes.
Attribute names follow the [OpenTelemetry Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/).

| Subsystem              | Span name                                      | Kind       | Key attributes                                                                                                            |
|------------------------|------------------------------------------------|------------|-------------------------------------------------------------------------------------------------------------------------|
| HTTP server            | `<METHOD> <route>`, e.g. `GET /text`           | `SERVER`   | `http.request.method`, `url.scheme`, `url.path`, `http.route`, `server.address`, `http.response.status_code`            |
| HTTP client            | `<METHOD> <uriTemplate>`                       | `CLIENT`   | `http.request.method`, `server.address`, `server.port`, `url.scheme`, `url.full`, `http.response.status_code`          |
| Database               | query operation name                           | `CLIENT`   | `db.system`, `db.user`, `db.statement`                                                                                   |
| Kafka consumer         | `kafka.poll`, `<topic> receive`, `<topic> process` | `CONSUMER` | `messaging.system` = `kafka`, `messaging.operation`, `messaging.destination.name`, `messaging.kafka.message.offset`   |
| Kafka producer         | `<topic> send`, `producer transaction`         | `PRODUCER` / `INTERNAL` | `messaging.system` = `kafka`, `messaging.operation` = `publish`, `messaging.destination.name`                |
| gRPC server            | `<service>/<method>`                           | `SERVER`   | `rpc.system` = `grpc`, `rpc.service`, `rpc.method`, `network.peer.address`                                               |
| gRPC client            | `<fullMethodName>`                             | `CLIENT`   | `rpc.system` = `grpc`, `rpc.service`, `rpc.method`, `server.address`, `server.port`                                      |
| S3 client              | `S3 <client> <method>`                         | `CLIENT`   | `client.name`, `http.request.method`, `aws.s3.bucket`, `aws.s3.key`, `http.response.status_code`                        |
| SOAP client            | `SOAP <service> <method>`                      | `CLIENT`   | `rpc.service`, `rpc.method`, `rpc.system`                                                                                |
| JMS consumer           | `<destination> receive`                        | `CONSUMER` | `messaging.system` = `jms`, `messaging.destination.name`, `messaging.message.id`                                        |
| Scheduling             | `<class> <method>`                             | `INTERNAL` | `code.function`, `code.filepath`                                                                                         |
| Cache                  | `cache.call`                                   | `INTERNAL` | `operation`, `cache`, `origin`                                                                                           |

`Camunda` (BPMN engine, REST) and `Zeebe` worker subsystems are also instrumented when their modules are present.

On failure Kora sets the span status to `ERROR` and records the exception via `Span#recordException`; on success the status is set to `OK`.

## Module tracing configuration { #module-config }

Tracing of each instrumented subsystem is configured under that module's `telemetry.tracing` section, described by `ru.tinkoff.kora.telemetry.common.TelemetryConfig.TracingConfig`.
Two options are available for every subsystem:

- `enabled` (default: `true`) — turns the subsystem's spans on or off. Set to `false` to stop creating spans for a specific module without removing the exporter.
- `attributes` (default: `{}`) — a map of key/value pairs added to every span produced **by that module only**. These per-span attributes differ from the service-wide `tracing.attributes` (`Resource` attributes) that apply to all spans.

The `telemetry.tracing` section lives at the same path as the module's own configuration, for example `httpServer.telemetry.tracing`, `db.telemetry.tracing`, `grpcServer.telemetry.tracing`, or `kafka.<consumer>.telemetry.tracing`.

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
      telemetry {
        tracing {
          enabled = true //(1)!
          attributes { //(2)!
            "component" = "gateway"
          }
        }
      }
    }
    db {
      telemetry {
        tracing {
          enabled = false //(3)!
        }
      }
    }
    ```

    1. Enables tracing for the HTTP server (default: `true`).
    2. Per-span attributes added only to HTTP server spans (default: `{}`).
    3. Disables tracing for database queries (default: `true`).

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      telemetry:
        tracing:
          enabled: true #(1)!
          attributes: #(2)!
            component: "gateway"
    db:
      telemetry:
        tracing:
          enabled: false #(3)!
    ```

    1. Enables tracing for the HTTP server (default: `true`).
    2. Per-span attributes added only to HTTP server spans (default: `{}`).
    3. Disables tracing for database queries (default: `true`).

Module-specific tracing parameters are also described in those modules' own documentation, for example [HTTP server](http-server.md), [HTTP client](http-client.md), [gRPC server](grpc-server.md), [gRPC client](grpc-client.md), and [Kafka](kafka.md).

## Context propagation { #propagation }

Kora stitches distributed traces together with the [W3C Trace Context](https://www.w3.org/TR/trace-context/) standard: every instrumented client injects the current `traceparent` into the outgoing carrier, and every instrumented server extracts it to establish the parent of the new `Span`.
This happens automatically and requires no configuration:

- **HTTP** — `traceparent` is injected into request headers by the HTTP client and extracted from request headers by the HTTP server.
- **Kafka** — `traceparent` is injected into record headers by the producer and extracted from record headers by the consumer (the per-record `process` span also links back to the batch `receive` span).
- **gRPC** — `traceparent` is injected into call metadata by the client and extracted from metadata by the server.
- **JMS** — `traceparent` is extracted from message properties by the consumer.

Because the current `Span` lives in the Kora `Context`, any span you create manually (see [Synchronous tracing](#tracing-sync)) is automatically picked up and propagated by the instrumented clients called within the same context — you do not need to pass headers yourself.

## Sampling { #sampling }

The core tracing components are provided by `OpentelemetryTracingModule` as `@DefaultComponent`, which means each of them can be overridden by declaring your own component of the same type:

- `Sampler` — decides which `Span` are recorded. The default is `Sampler.parentBased(Sampler.alwaysOn())`, i.e. record every root `Span` and follow the parent's decision for child `Span`.
- `IdGenerator` — generates trace and span identifiers. The default is `IdGenerator.random()`.
- `Supplier<SpanLimits>` — limits on attributes, events, and links per `Span`. The default is `SpanLimits.getDefault()`.

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

To get the current `Span`, use the `getSpan` method on `OpentelemetryContext`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var span = OpentelemetryContext.getSpan();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val span = OpentelemetryContext.getSpan()
    ```

To get the current trace identifier, use the `getTraceId()` method on `OpentelemetryContext`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var traceId = OpentelemetryContext.getTraceId();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val traceId = OpentelemetryContext.getTraceId()
    ```

If there is no current `Span`, both methods return `null`.
If you need an invalid placeholder value from `OpenTelemetry`, use `getSpanOrInvalid()` and `getTraceIdOrInvalid()`, which return `Span.getInvalid()` and its all-zero trace identifier instead of `null`.

For manual span management, `OpentelemetryContext` also exposes an instance API used together with the Kora `Context`:

- `OpentelemetryContext.get(ctx)` — returns the `OpentelemetryContext` stored in the given Kora `Context` (creating an empty one if absent).
- `OpentelemetryContext.set(ctx, otctx)` — stores the `OpentelemetryContext` in the Kora `Context` and updates the `traceId`/`spanId` in `MDC`.
- `otctx.add(span)` — returns a new `OpentelemetryContext` with the given `Span` (or any `ImplicitContextKeyed`) added as the current one.
- `otctx.getContext()` — returns the underlying `io.opentelemetry.context.Context`, used as the parent when building a nested `Span`.

## Log correlation { #mdc }

When `OpentelemetryContext.set` is called (by the automatic instrumentation or by your manual tracing code), Kora writes the current `traceId` and `spanId` into the [MDC](logging-slf4j.md).
When there is no current `Span`, these keys are removed from the `MDC` again.

As a result, if the [logging module](logging-slf4j.md) is used, every log line emitted within a traced operation carries the `traceId` and `spanId`, which lets you jump from a log entry to the corresponding trace in your observability backend and back.

## Synchronous tracing { #tracing-sync }

In addition to `Span` automatically created by the framework, you can use the `Tracer` object from the application graph and create custom nested `Span`.
When tracing manually, it is important to save the current `OpentelemetryContext`, set the new context for the duration of the operation, and restore the original context in `finally`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MyService {

        private final io.opentelemetry.api.trace.Tracer tracer;

        public MyService(Tracer tracer) {
            this.tracer = tracer;
        }

        public String doTraceWork() {
            var ctx = ru.tinkoff.kora.common.Context.current();
            var otctx = OpentelemetryContext.get(ctx);
            var span = tracer.spanBuilder("myOperation")
                .setParent(otctx.getContext())
                .startSpan();

            OpentelemetryContext.set(ctx, otctx.add(span));
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
                OpentelemetryContext.set(ctx, otctx);
            }
        }

        public String doWork() {
            // do some work
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyService(private val tracer: io.opentelemetry.api.trace.Tracer) {

        fun doTraceWork(): String {
            val ctx = ru.tinkoff.kora.common.Context.current()
            val otctx = OpentelemetryContext.get(ctx)
            val span = tracer.spanBuilder("myOperation")
                .setParent(otctx.getContext())
                .startSpan()

            OpentelemetryContext.set(ctx, otctx.add(span))
            try {
                val result = doWork()
                span.setStatus(StatusCode.OK)
                return result
            } catch (e: Exception) {
                span.recordException(e)
                span.setStatus(StatusCode.ERROR, e.message)
                throw e
            } finally {
                span.end()
                OpentelemetryContext.set(ctx, otctx)
            }
        }

        fun doWork(): String {
            // do some work
        }
    }
    ```

## Asynchronous tracing { #async-tracing }

When switching to another execution thread, pass not only `Span`, but also the Kora context.
Use `Context.fork()` for `CompletionStage` and `Context.Kotlin.asCoroutineContext(ctx)` for `suspend` code.

===! ":fontawesome-brands-java: `Java`"

    Example for asynchronous code with `CompletionStage`:

    ```java
    @Component
    public final class MyService {

        private final io.opentelemetry.api.trace.Tracer tracer;

        public MyService(Tracer tracer) {
            this.tracer = tracer;
        }

        public CompletionStage<String> doTraceWork() {
            var ctx = ru.tinkoff.kora.common.Context.current().fork();
            var otctx = OpentelemetryContext.get(ctx);
            var span = tracer.spanBuilder("myOperation")
                .setParent(otctx.getContext())
                .startSpan();

            return CompletableFuture.supplyAsync(() -> {
                    OpentelemetryContext.set(ctx, otctx.add(span));
                    return doWork();
                })
                .whenComplete((r, e) -> {
                    if (e != null) {
                        span.recordException(e);
                        span.setStatus(StatusCode.ERROR, e.getMessage());
                    } else {
                        span.setStatus(StatusCode.OK);
                    }
                    span.end();
                    OpentelemetryContext.set(ctx, otctx);
                });
        }

        public String doWork() {
            // do some work
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Example for asynchronous `suspend` code:

    ```kotlin
    @Component
    class MyService(private val tracer: io.opentelemetry.api.trace.Tracer) {

        suspend fun doTraceWork(): String {
            val ctx = ru.tinkoff.kora.common.Context.current()
            val otctx = OpentelemetryContext.get(ctx)
            val span = tracer.spanBuilder("myOperation")
                .setParent(otctx.getContext())
                .startSpan()

            OpentelemetryContext.set(ctx, otctx.add(span))
            return withContext(Context.Kotlin.asCoroutineContext(ctx)) {
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
                    OpentelemetryContext.set(ctx, otctx)
                }
            }
        }

        fun doWork(): String {
            // do some work
        }
    }
    ```
