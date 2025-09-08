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

        fun doWork(): String = // do some work
    }
    ```

## Получение трассировки

Чтобы получить текущий `Span` трассировки можно использовать метод `getSpan` у `OpentelemetryContext`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var span = OpentelemetryContext.getSpan();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val span = OpentelemetryContext.getSpan();
    ```

Для получения текущего идентификатора трассировки можно использовать метод `getTraceId()` у `OpentelemetryContext`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var span = OpentelemetryContext.getTraceId();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val span = OpentelemetryContext.getTraceId();
    ```

