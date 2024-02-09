Модуль для сбора трассировка приложения по стандарту [OpenTelemetry](https://opentelemetry.io/docs/what-is-opentelemetry/)
и экспорта трассировки по gRPC/HTTP в формате OTLP. 

## gRPC

Модуль позволяет собирать трассировку с помощью [gRPC протокола](https://github.com/open-telemetry/oteps/blob/main/text/0035-opentelemetry-protocol.md#protocol-details) по средствам `GrpcSender`.

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

Модуль позволяет собирать трассировку с помощью [HTTP протокола](https://github.com/open-telemetry/oteps/blob/main/text/0099-otlp-http.md) по средствам `HttpSender`.

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

## Конфигурация

Обязательным полем является только `endpoint`, аттрибуты из поля `attributes` будут отправляться с каждым спаном.

Параметры, описанные в классах `OpentelemetryGrpcExporterConfig`/`OpentelemetryHttpExporterConfig` и `OpentelemetryResourceConfig`:

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

    1.  URL от [OpenTelemetry](https://opentelemetry.io/docs/collector/) коллектор сервиса
    2.  Максимальное время ожидания обработки телеметрии коллектором 
    3.  Время между экспортом телеметрии в коллектор
    4.  Максимальная кол-во телеметрии в рамках одного экспорта
    5.  Максимальный размер очереди неотправленной телеметрии
    6.  Дополнительные атрибуты телеметрии

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

    1.  URL от [OpenTelemetry](https://opentelemetry.io/docs/collector/) коллектор сервиса
    2.  Максимальное время ожидания обработки телеметрии коллектором 
    3.  Время между экспортом телеметрии в коллектор
    4.  Максимальная кол-во телеметрии в рамках одного экспорта
    5.  Максимальный размер очереди неотправленной телеметрии
    6.  Дополнительные атрибуты телеметрии

Параметры конфигурации сбора трассировки описываются в модулях в которых присутствует сбор трассировки, например [HTTP сервер](http-server.md), [HTTP клиент](http-client.md) и т.д.

## Императивная трассировка

Помимо автоматически создаваемых спанов вы можете пользоваться объектом `Tracer` из контейнера. 
Создать спан с текущим в parent можно следующим образом:

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
