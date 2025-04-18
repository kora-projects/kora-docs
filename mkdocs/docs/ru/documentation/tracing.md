Модуль для сбора трассировка приложения по стандарту [OpenTelemetry](https://opentelemetry.io/docs/what-is-opentelemetry/)
и экспорта трассировки по gRPC/HTTP в формате OTLP. 

## gRPC

Модуль позволяет собирать трассировку с помощью [gRPC протокола](https://github.com/open-telemetry/oteps/blob/main/text/0035-opentelemetry-protocol.md#protocol-details) посредствам `GrpcSender`.

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#_4) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:opentelemetry-tracing-exporter-grpc"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends OpentelemetryGrpcExporterModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#_4) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:opentelemetry-tracing-exporter-grpc")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : OpentelemetryGrpcExporterModule
    ```

## HTTP

Модуль позволяет собирать трассировку с помощью [HTTP протокола](https://github.com/open-telemetry/oteps/blob/main/text/0099-otlp-http.md) посредствам `HttpSender`.

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#_4) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:opentelemetry-tracing-exporter-http"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends OpentelemetryHttpExporterModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#_4) `build.gradle.kts`:
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

Пример полной конфигурации, описанной в классе `OpentelemetryGrpcExporterConfig` или `OpentelemetryHttpExporterConfig`, а также `OpentelemetryResourceConfig` (указаны примеры значений или значения по умолчанию):

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

    1.  URL от [OpenTelemetry](https://opentelemetry.io/docs/collector/) коллектор сервиса (**обязательный**)
    2.  Время ожидания соедининя с экспортером
    3.  Максимальное время ожидания обработки телеметрии коллектором 
    4.  Время между экспортом телеметрии в коллектор
    5.  Максимальная кол-во телеметрии в рамках одного экспорта
    6.  Максимальный размер очереди неотправленной телеметрии
    7.  Максимальное вреия ожидания экспорта
    8.  Механизм сжатия телеметрии при экпорте
    9.  Экспортировать ли не сэмплированную телеметрию
    10. Максимальное кол-во попыток на экспорт
    11. Начальное значение ожидания перед следующей попыткой экспорта
    12. Максимальное значение ожидания перед следующей попыткой экспорта
    13. Мультипликатор значения задержки ожидания
    14. Дополнительные атрибуты телеметрии

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

    1.  URL от [OpenTelemetry](https://opentelemetry.io/docs/collector/) коллектор сервиса (**обязательный**)
    2.  Время ожидания соедининя с экспортером
    3.  Максимальное время ожидания обработки телеметрии коллектором 
    4.  Время между экспортом телеметрии в коллектор
    5.  Максимальная кол-во телеметрии в рамках одного экспорта
    6.  Максимальный размер очереди неотправленной телеметрии
    7.  Максимальное вреия ожидания экспорта
    8.  Механизм сжатия телеметрии при экпорте
    9.  Экспортировать ли не сэмплированную телеметрию
    10. Максимальное кол-во попыток на экспорт
    11. Начальное значение ожидания перед следующей попыткой экспорта
    12. Максимальное значение ожидания перед следующей попыткой экспорта
    13. Мультипликатор значения задержки ожидания
    14. Дополнительные атрибуты телеметрии

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
