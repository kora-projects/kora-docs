Module for collecting application trace according to [OpenTelemetry] standard(https://opentelemetry.io/docs/what-is-opentelemetry/)
and export trace by gRPC in OTLP format.

## gRPC

Module allows trace collection using [gRPC protocol](https://github.com/open-telemetry/oteps/blob/main/text/0035-opentelemetry-protocol.md#protocol-details) by means of `GrpcSender`.

===! ":fontawesome-brands-java: `Java`"

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

===! ":fontawesome-brands-java: `Java`"

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

    1. URL from [OpenTelemetry](https://opentelemetry.io/docs/collector/) service collector (**mandatory**)
    2. Time to wait for connection to exporter
    3. Maximum time to wait for telemetry processing by collector
    4. Time between exporting telemetry to the collector 
    5. Maximum number of telemetry within one export
    6. Maximum queue size of unsent telemetry
    7. Maximum waiting time for export
    8. Telemetry compression mechanism when exporting
    9. Whether to export unsampled telemetry
    10. Maximum number of export attempts
    11. Initial value of waiting time before next export attempt
    12. Maximum wait value before next export attempt
    13. Waiting delay value multiplier
    14. Additional telemetry attributes

Translated with DeepL.com (free version)
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

    1. URL from [OpenTelemetry](https://opentelemetry.io/docs/collector/) service collector (**mandatory**)
    2. Time to wait for connection to exporter
    3. Maximum time to wait for telemetry processing by collector
    4. Time between exporting telemetry to the collector 
    5. Maximum number of telemetry within one export
    6. Maximum queue size of unsent telemetry
    7. Maximum waiting time for export
    8. Telemetry compression mechanism when exporting
    9. Whether to export unsampled telemetry
    10. Maximum number of export attempts
    11. Initial value of waiting time before next export attempt
    12. Maximum wait value before next export attempt
    13. Waiting delay value multiplier
    14. Additional telemetry attributes

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
