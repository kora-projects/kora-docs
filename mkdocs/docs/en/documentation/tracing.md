Module for collecting application trace according to [OpenTelemetry] standard(https://opentelemetry.io/docs/what-is-opentelemetry/)
and export trace by gRPC in OTLP format.

## gRPC

Module allows trace collection using [gRPC protocol](https://github.com/open-telemetry/oteps/blob/main/text/0035-opentelemetry-protocol.md#protocol-details) by means of `GrpcSender`.

=== ":fontawesome-brands-java: `Java`"

    Зависимость `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:opentelemetry-tracing-exporter-grpc"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends OpentelemetryGrpcExporterModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Зависимость `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:opentelemetry-tracing-exporter-grpc")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : OpentelemetryGrpcExporterModule
    ```

## HTTP

Module allows to collect trace using [HTTP protocol](https://github.com/open-telemetry/oteps/blob/main/text/0099-otlp-http.md) by means of `HttpSender`.

=== ":fontawesome-brands-java: `Java`"

    Зависимость `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:opentelemetry-tracing-exporter-http"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends OpentelemetryHttpExporterModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Зависимость `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:opentelemetry-tracing-exporter-http")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : OpentelemetryHttpExporterModule
    ```

## Configuration

`endpoint` is the only a required field, attributes from the `attributes` field will be sent with each span.

Parameters described in the `OpentelemetryGrpcExporterConfig`/`OpentelemetryHttpExporterConfig` and `OpentelemetryResourceConfig` classes:

===! ":material-code-json: `Hocon`"

    ```javascript
    tracing {
      exporter {
        endpoint = "http://localhost:4317" // (1)!
        exportTimeout = "2s" // (2)!
        scheduleDelay = "200ms" // (3)!
        maxExportBatchSize = 512 // (4)!
        maxQueueSize = 1024 // (5)!
      }
      attributes { // (6)!
        "service.name" = "example-service"
        "service.namespace" = "kora"
      }
    }
    ```

    1.  URL from [OpenTelemetry](https://opentelemetry.io/docs/collector/) service collector
    2.  The maximum time to wait for the collector to process telemetry
    3.  Time between exporting telemetry to the collector
    4.  Maximum number of telemetry within one export
    5.  Maximum queue size of unsent telemetry
    6.  Additional telemetry attributes

=== ":simple-yaml: `YAML`"

    ```yaml
    tracing:
      exporter:
        endpoint: http://localhost:4317 # (1)!
        exportTimeout: 2s # (2)!
        maxExportBatchSize: 512 # (3)!
        maxQueueSize: 1024 # (4)!
        scheduleDelay: 200ms # (5)!
      attributes: # (6)!
        service.name: example-service
        service.namespace: kora
    ```

    1.  URL from [OpenTelemetry](https://opentelemetry.io/docs/collector/) service collector
    2.  The maximum time to wait for the collector to process telemetry
    3.  Time between exporting telemetry to the collector
    4.  Maximum number of telemetry within one export
    5.  Maximum queue size of unsent telemetry
    6.  Additional telemetry attributes

Trace collection configuration parameters are described in modules that include trace collection, e.g. [HTTP server](http-server.md), [HTTP client](http-client.md), etc.

## Imperative tracing

In addition to automatically created spans, you can use the `Tracer` object from the dependency container.
You can create a span with the current one in parent as follows:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var context = Context.current();
    var telemetryContext = OpentelemetryContext.get(context);
    var newSpan = this.tracer.spanBuilder("some-span")
        .setParent(telemetryContext.getContext())
        .build();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val context = Context.current();
    val telemetryContext = OpentelemetryContext.get(context);
    val newSpan = this.tracer.spanBuilder("some-span")
        .setParent(telemetryContext.getContext())
        .build();
    ```
