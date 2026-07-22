---
description: "Explains Kora OpenTelemetry tracing over gRPC and HTTP, tracing configuration, trace context propagation, synchronous tracing, and asynchronous tracing. Use when working with OpentelemetryTracingModule, OpenTelemetry, OpentelemetryContext, Span, OTLP."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora OpenTelemetry tracing over gRPC and HTTP, tracing configuration, trace context propagation, synchronous tracing, and asynchronous tracing; key triggers include OpentelemetryTracingModule, OpenTelemetry, OpentelemetryContext, Span, OTLP."
---

Трассировка помогает связать отдельные операции приложения в единую цепочку выполнения и понять, где запрос провел время или завершился ошибкой.
Kora использует [`OpenTelemetry`](https://opentelemetry.io/docs/what-is-opentelemetry/) для создания `Span`, хранения текущего контекста трассировки в `OpentelemetryContext` и экспорта данных в формате `OTLP`.

Текущий `Span` хранится в контексте Kora, поэтому его можно передавать между компонентами приложения и использовать при ручном создании вложенных `Span`.
Когда установлен `OpentelemetryContext`, Kora также добавляет `traceId` и `spanId` в `MDC`, чтобы эти идентификаторы появлялись в логах при использовании модуля логирования.

Большинство `Span` создаются автоматически: модуль из коробки инструментирует HTTP-сервер и клиент, базу данных, потребителя и производителя `Kafka`, gRPC-сервер и клиент, а также другие подсистемы,
и распространяет контекст трассировки между сервисами по стандарту [W3C traceparent](https://www.w3.org/TR/trace-context/).

Kora предоставляет два взаимоисключающих модуля экспортера, `OTLP/gRPC` и `OTLP/HTTP`; выберите ровно один в зависимости от протокола, который принимает ваш коллектор.
Любой из модулей экспортера транзитивно предоставляет базовую обвязку трассировки (`OpentelemetryTracingModule`) и автоматическую инструментацию (`OpentelemetryModule`), так что никакой другой зависимости для трассировки не требуется.

Пошаговое руководство перед справочным описанием смотрите в разделе [Наблюдаемость](../guides/observability.md).

## gRPC { #grpc }

Модуль экспортирует данные трассировки в `OpenTelemetry Collector` через `OTLP/gRPC`.
Он строит `OtlpGrpcSpanExporter` поверх `BatchSpanProcessor`, а типичный адрес коллектора — `http://localhost:4317`.

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:opentelemetry-tracing-exporter-grpc"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends OpentelemetryGrpcExporterModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:opentelemetry-tracing-exporter-grpc")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : OpentelemetryGrpcExporterModule
    ```

## HTTP { #http }

Модуль экспортирует данные трассировки в `OpenTelemetry Collector` через `OTLP/HTTP`.
Он строит `OtlpHttpSpanExporter` поверх `BatchSpanProcessor`, а типичный адрес коллектора — `http://localhost:4318/v1/traces`.

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:opentelemetry-tracing-exporter-http"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends OpentelemetryHttpExporterModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:opentelemetry-tracing-exporter-http")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : OpentelemetryHttpExporterModule
    ```

## Конфигурация { #configuration }

Параметры экспорта в секции `tracing.exporter` описываются классами `OpentelemetryGrpcExporterConfig` (для `OTLP/gRPC`) и `OpentelemetryHttpExporterConfig` (для `OTLP/HTTP`); оба класса имеют одинаковый набор полей.
Атрибуты ресурса в секции `tracing.attributes` описываются классом `OpentelemetryResourceConfig`.
Если `tracing.exporter.endpoint` не указан, экспортер не создается (конфигурация разрешается во внутреннее значение `Empty`, и используются пустые `SpanExporter`/`SpanProcessor`), и приложение запускается без отправки трассировок во внешний коллектор.

Поле `tracing.attributes` задает атрибуты `OpenTelemetry Resource`, которые добавляются к **каждому** экспортируемому `Span` всего сервиса.
Обычно оно содержит имя и пространство имен сервиса, например `service.name` и `service.namespace`.
Эти общесервисные атрибуты `Resource` отличаются от атрибутов уровня отдельного span, настраиваемых в секции `<module>.telemetry.tracing.attributes`, которые добавляются только к span конкретной подсистемы — смотрите [Конфигурация трассировки модуля](#module-config).

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

    1. Адрес `OpenTelemetry Collector` для экспорта трассировок (по умолчанию не указан, необязательный). Для `gRPC` обычно используется `http://localhost:4317`, а для `HTTP` — `http://localhost:4318/v1/traces`.
    2. Таймаут установки соединения с экспортером (по умолчанию не указан, необязательный).
    3. Максимальное время ожидания при отправке данных экспортером (по умолчанию `3s`).
    4. Задержка между отправками накопленных `Span` в коллектор (по умолчанию `2s`).
    5. Максимальное количество `Span` в одной партии экспорта (по умолчанию `512`).
    6. Максимальный размер очереди `Span`, ожидающих отправки (по умолчанию `2048`).
    7. Максимальное время, которое `BatchSpanProcessor` ждет экспорта одной накопленной партии; отличается от `exportTimeout`, ограничивающего один запрос `OTLP` (по умолчанию `30s`).
    8. Сжатие данных при экспорте, `gzip` или `none` (по умолчанию `gzip`).
    9. Экспортировать ли `Span`, которые не были выбраны `Sampler` (по умолчанию `false`).
    10. Максимальное количество повторных попыток (по умолчанию `5`).
    11. Начальная задержка перед повторной попыткой (по умолчанию `1s`).
    12. Максимальная задержка перед повторной попыткой (по умолчанию `5s`).
    13. Множитель задержки между повторными попытками (по умолчанию `1.5`).
    14. Атрибуты `OpenTelemetry Resource`, добавляемые к экспортируемым `Span` (по умолчанию `{}`).

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

    1. Адрес `OpenTelemetry Collector` для экспорта трассировок (по умолчанию не указан, необязательный). Для `gRPC` обычно используется `http://localhost:4317`, а для `HTTP` — `http://localhost:4318/v1/traces`.
    2. Таймаут установки соединения с экспортером (по умолчанию не указан, необязательный).
    3. Максимальное время ожидания при отправке данных экспортером (по умолчанию `3s`).
    4. Задержка между отправками накопленных `Span` в коллектор (по умолчанию `2s`).
    5. Максимальное количество `Span` в одной партии экспорта (по умолчанию `512`).
    6. Максимальный размер очереди `Span`, ожидающих отправки (по умолчанию `2048`).
    7. Максимальное время, которое `BatchSpanProcessor` ждет экспорта одной накопленной партии; отличается от `exportTimeout`, ограничивающего один запрос `OTLP` (по умолчанию `30s`).
    8. Сжатие данных при экспорте, `gzip` или `none` (по умолчанию `gzip`).
    9. Экспортировать ли `Span`, которые не были выбраны `Sampler` (по умолчанию `false`).
    10. Максимальное количество повторных попыток (по умолчанию `5`).
    11. Начальная задержка перед повторной попыткой (по умолчанию `1s`).
    12. Максимальная задержка перед повторной попыткой (по умолчанию `5s`).
    13. Множитель задержки между повторными попытками (по умолчанию `1.5`).
    14. Атрибуты `OpenTelemetry Resource`, добавляемые к экспортируемым `Span` (по умолчанию `{}`).

Пример проекта использует подстановку переменных окружения для адреса и переопределяет несколько параметров экспорта:

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

    1. Разрешается из переменной окружения `METRIC_COLLECTOR_ENDPOINT`, смотрите [подстановку переменных окружения](config.md#environment-variables).

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

    1. Разрешается из переменной окружения `METRIC_COLLECTOR_ENDPOINT`, смотрите [подстановку переменных окружения](config.md#environment-variables).

## Автоматическая трассировка { #automatic }

Как только добавлен один модуль экспортера, Kora автоматически инструментирует свои подсистемы: для каждого входящего запроса, исходящего вызова, сообщения, запроса к базе данных или запланированного запуска она создает `Span`, привязывает его к текущему `OpentelemetryContext`, вкладывает его в текущий активный `Span` и распространяет контекст трассировки за границы сервиса.
Для этих `Span` не требуется ни аннотаций, ни ручного кода.

Например, контроллер `GET /text` из примера телеметрии автоматически создает span типа `SERVER` с именем `GET /text`:

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

В таблице ниже перечислены подсистемы, инструментируемые `OpentelemetryModule`, итоговое имя `Span` и его [тип](https://opentelemetry.io/docs/specs/otel/trace/api/#spankind), а также основные атрибуты.
Имена атрибутов следуют [семантическим соглашениям OpenTelemetry](https://opentelemetry.io/docs/specs/semconv/).

| Подсистема             | Имя span                                       | Тип        | Основные атрибуты                                                                                                        |
|------------------------|------------------------------------------------|------------|-------------------------------------------------------------------------------------------------------------------------|
| HTTP-сервер            | `<METHOD> <route>`, например `GET /text`       | `SERVER`   | `http.request.method`, `url.scheme`, `url.path`, `http.route`, `server.address`, `http.response.status_code`            |
| HTTP-клиент            | `<METHOD> <uriTemplate>`                       | `CLIENT`   | `http.request.method`, `server.address`, `server.port`, `url.scheme`, `url.full`, `http.response.status_code`          |
| База данных            | имя операции запроса                           | `CLIENT`   | `db.system`, `db.user`, `db.statement`                                                                                   |
| Потребитель Kafka      | `kafka.poll`, `<topic> receive`, `<topic> process` | `CONSUMER` | `messaging.system` = `kafka`, `messaging.operation`, `messaging.destination.name`, `messaging.kafka.message.offset`   |
| Производитель Kafka    | `<topic> send`, `producer transaction`         | `PRODUCER` / `INTERNAL` | `messaging.system` = `kafka`, `messaging.operation` = `publish`, `messaging.destination.name`                |
| gRPC-сервер            | `<service>/<method>`                           | `SERVER`   | `rpc.system` = `grpc`, `rpc.service`, `rpc.method`, `network.peer.address`                                               |
| gRPC-клиент            | `<fullMethodName>`                             | `CLIENT`   | `rpc.system` = `grpc`, `rpc.service`, `rpc.method`, `server.address`, `server.port`                                      |
| S3-клиент              | `S3 <client> <method>`                         | `CLIENT`   | `client.name`, `http.request.method`, `aws.s3.bucket`, `aws.s3.key`, `http.response.status_code`                        |
| SOAP-клиент            | `SOAP <service> <method>`                      | `CLIENT`   | `rpc.service`, `rpc.method`, `rpc.system`                                                                                |
| Потребитель JMS        | `<destination> receive`                        | `CONSUMER` | `messaging.system` = `jms`, `messaging.destination.name`, `messaging.message.id`                                        |
| Планирование           | `<class> <method>`                             | `INTERNAL` | `code.function`, `code.filepath`                                                                                         |
| Кэш                    | `cache.call`                                   | `INTERNAL` | `operation`, `cache`, `origin`                                                                                           |

Подсистемы `Camunda` (движок BPMN, REST) и воркер `Zeebe` также инструментируются при наличии их модулей.

При ошибке Kora устанавливает статус span в `ERROR` и записывает исключение через `Span#recordException`; при успехе статус устанавливается в `OK`.

## Конфигурация трассировки модуля { #module-config }

Трассировка каждой инструментируемой подсистемы настраивается в секции `telemetry.tracing` соответствующего модуля, описываемой классом `ru.tinkoff.kora.telemetry.common.TelemetryConfig.TracingConfig`.
Для каждой подсистемы доступны две опции:

- `enabled` (по умолчанию `true`) — включает или выключает span подсистемы. Установите `false`, чтобы прекратить создание span для конкретного модуля, не удаляя экспортер.
- `attributes` (по умолчанию `{}`) — набор пар ключ/значение, добавляемых к каждому span, создаваемому **только этим модулем**. Эти атрибуты уровня span отличаются от общесервисных `tracing.attributes` (атрибутов `Resource`), применяемых ко всем span.

Секция `telemetry.tracing` располагается по тому же пути, что и собственная конфигурация модуля, например `httpServer.telemetry.tracing`, `db.telemetry.tracing`, `grpcServer.telemetry.tracing` или `kafka.<consumer>.telemetry.tracing`.

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

    1. Включает трассировку HTTP-сервера (по умолчанию `true`).
    2. Атрибуты уровня span, добавляемые только к span HTTP-сервера (по умолчанию `{}`).
    3. Отключает трассировку запросов к базе данных (по умолчанию `true`).

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

    1. Включает трассировку HTTP-сервера (по умолчанию `true`).
    2. Атрибуты уровня span, добавляемые только к span HTTP-сервера (по умолчанию `{}`).
    3. Отключает трассировку запросов к базе данных (по умолчанию `true`).

Специфичные для модуля параметры трассировки также описаны в документации соответствующих модулей, например [HTTP-сервер](http-server.md), [HTTP-клиент](http-client.md), [gRPC-сервер](grpc-server.md), [gRPC-клиент](grpc-client.md) и [Kafka](kafka.md).

## Распространение контекста { #propagation }

Kora сшивает распределенные трассировки по стандарту [W3C Trace Context](https://www.w3.org/TR/trace-context/): каждый инструментируемый клиент внедряет текущий `traceparent` в исходящий носитель, а каждый инструментируемый сервер извлекает его, чтобы установить родителя нового `Span`.
Это происходит автоматически и не требует настройки:

- **HTTP** — `traceparent` внедряется в заголовки запроса HTTP-клиентом и извлекается из заголовков запроса HTTP-сервером.
- **Kafka** — `traceparent` внедряется в заголовки записи производителем и извлекается из заголовков записи потребителем (span `process` отдельной записи также связывается со span `receive` партии).
- **gRPC** — `traceparent` внедряется в метаданные вызова клиентом и извлекается из метаданных сервером.
- **JMS** — `traceparent` извлекается из свойств сообщения потребителем.

Поскольку текущий `Span` живет в `Context` Kora, любой span, созданный вами вручную (смотрите [Синхронная трассировка](#tracing-sync)), автоматически подхватывается и распространяется инструментируемыми клиентами, вызываемыми в рамках того же контекста — вам не нужно передавать заголовки самостоятельно.

## Сэмплирование { #sampling }

Базовые компоненты трассировки предоставляются модулем `OpentelemetryTracingModule` как `@DefaultComponent`, а значит каждый из них можно переопределить, объявив собственный компонент того же типа:

- `Sampler` — решает, какие `Span` записываются. По умолчанию используется `Sampler.parentBased(Sampler.alwaysOn())`, то есть записывается каждый корневой `Span`, а для дочерних `Span` следует решению родителя.
- `IdGenerator` — генерирует идентификаторы трассировки и span. По умолчанию используется `IdGenerator.random()`.
- `Supplier<SpanLimits>` — ограничения на количество атрибутов, событий и связей у одного `Span`. По умолчанию используется `SpanLimits.getDefault()`.

Чтобы применить сэмплирование на стороне источника (head-based), переопределите фабричный метод `Sampler` в своем приложении, например для записи примерно 10% корневых трассировок:

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

Опция экспорта `exportUnsampledSpans` управляет тем, отправляются ли в коллектор `Span`, которые **не** были выбраны `Sampler`; по умолчанию она равна `false`, поэтому экспортируются только выбранные `Span`.

## Контекст трассировки { #tracing-context }

Чтобы получить текущий `Span`, используйте метод `getSpan` у `OpentelemetryContext`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var span = OpentelemetryContext.getSpan();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val span = OpentelemetryContext.getSpan()
    ```

Чтобы получить текущий идентификатор трассировки, используйте метод `getTraceId()` у `OpentelemetryContext`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var traceId = OpentelemetryContext.getTraceId();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val traceId = OpentelemetryContext.getTraceId()
    ```

Если текущего `Span` нет, оба метода возвращают `null`.
Если вам нужно недействительное значение-заглушка из `OpenTelemetry`, используйте `getSpanOrInvalid()` и `getTraceIdOrInvalid()`, которые вместо `null` возвращают `Span.getInvalid()` и его нулевой идентификатор трассировки.

Для ручного управления span у `OpentelemetryContext` также есть объектный API, используемый вместе с `Context` Kora:

- `OpentelemetryContext.get(ctx)` — возвращает `OpentelemetryContext`, хранящийся в переданном `Context` Kora (создавая пустой, если его нет).
- `OpentelemetryContext.set(ctx, otctx)` — сохраняет `OpentelemetryContext` в `Context` Kora и обновляет `traceId`/`spanId` в `MDC`.
- `otctx.add(span)` — возвращает новый `OpentelemetryContext` с переданным `Span` (или любым `ImplicitContextKeyed`), добавленным в качестве текущего.
- `otctx.getContext()` — возвращает лежащий в основе `io.opentelemetry.context.Context`, используемый как родитель при построении вложенного `Span`.

## Корреляция логов { #mdc }

Когда вызывается `OpentelemetryContext.set` (автоматической инструментацией или вашим кодом ручной трассировки), Kora записывает текущие `traceId` и `spanId` в [MDC](logging-slf4j.md).
Когда текущего `Span` нет, эти ключи снова удаляются из `MDC`.

В результате, если используется [модуль логирования](logging-slf4j.md), каждая строка лога, порожденная в рамках трассируемой операции, несет `traceId` и `spanId`, что позволяет переходить от записи лога к соответствующей трассировке в системе наблюдаемости и обратно.

## Синхронная трассировка { #tracing-sync }

Помимо `Span`, автоматически создаваемых фреймворком, вы можете использовать объект `Tracer` из графа приложения и создавать собственные вложенные `Span`.
При ручной трассировке важно сохранить текущий `OpentelemetryContext`, установить новый контекст на время операции и восстановить исходный контекст в блоке `finally`.

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

## Асинхронная трассировка { #async-tracing }

При переключении на другой поток выполнения передавайте не только `Span`, но и контекст Kora.
Используйте `Context.fork()` для `CompletionStage` и `Context.Kotlin.asCoroutineContext(ctx)` для `suspend`-кода.

===! ":fontawesome-brands-java: `Java`"

    Пример для асинхронного кода с `CompletionStage`:

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

    Пример для асинхронного `suspend`-кода:

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
