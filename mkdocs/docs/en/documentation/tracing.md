---
description: "Explains Kora OpenTelemetry tracing over gRPC and HTTP, tracing configuration, trace context propagation, synchronous tracing, and asynchronous tracing. Use when working with TracingModule, OpenTelemetry, GrpcSender, OpentelemetryContext, Span, TraceContext, OTLP."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora OpenTelemetry tracing over gRPC and HTTP, tracing configuration, trace context propagation, synchronous tracing, and asynchronous tracing; key triggers include TracingModule, OpenTelemetry, GrpcSender, OpentelemetryContext, Span, TraceContext, OTLP."
---

Tracing helps link separate application operations into a single execution chain and understand where a request spent time or failed.
Kora uses [`OpenTelemetry`](https://opentelemetry.io/docs/what-is-opentelemetry/) to create `Span`, store the current tracing context in `OpentelemetryContext`, and export data in the `OTLP` format.

The current `Span` is stored in the Kora context, so it can be propagated between application components and used when manually creating nested `Span`.
When `OpentelemetryContext` is set, Kora also adds `traceId` and `spanId` to `MDC` so these identifiers appear in logs when the logging module is used.

For a step-by-step walkthrough before the reference details, see [Observability](../guides/observability.md).

## gRPC { #grpc }

The module exports tracing data to `OpenTelemetry Collector` through `OTLP/gRPC`.
It uses `GrpcSender`, and the typical collector endpoint is `http://localhost:4317`.

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
It uses `HttpSender`, and the typical collector endpoint is `http://localhost:4318/v1/traces`.

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

Export parameters are described by `OpentelemetryGrpcExporterConfig` and `OpentelemetryHttpExporterConfig`, and resource attributes are described by `OpentelemetryResourceConfig`.
If `tracing.exporter.endpoint` is not specified, the exporter is not created and the application starts without sending traces to an external collector.

The `tracing.attributes` field defines `OpenTelemetry Resource` attributes that are added to exported `Span`.
It usually contains the service name and namespace, for example `service.name` and `service.namespace`.

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
        retry {
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
    7. Maximum time to wait for a batch export (default: `30s`).
    8. Data compression used during export (default: `gzip`).
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
        retry:
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
    7. Maximum time to wait for a batch export (default: `30s`).
    8. Data compression used during export (default: `gzip`).
    9. Whether to export `Span` that were not selected by `Sampler` (default: `false`).
    10. Maximum number of retry attempts (default: `5`).
    11. Initial delay before a retry attempt (default: `1s`).
    12. Maximum delay before a retry attempt (default: `5s`).
    13. Delay multiplier between retry attempts (default: `1.5`).
    14. `OpenTelemetry Resource` attributes added to exported `Span` (default: `{}`).

Tracing enablement parameters for specific modules are described in those modules' documentation, for example [HTTP server](http-server.md), [HTTP client](http-client.md), [gRPC server](grpc-server.md), and [gRPC client](grpc-client.md).

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
If you need an invalid placeholder value from `OpenTelemetry`, use `getSpanOrInvalid()` and `getTraceIdOrInvalid()`.

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
