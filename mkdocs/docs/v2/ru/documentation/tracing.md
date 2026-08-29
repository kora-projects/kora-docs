---
description: "Explains Kora OpenTelemetry tracing with the OTLP/gRPC and OTLP/HTTP exporters, tracing configuration, trace context propagation, sampling, manual spans and carrying the trace context across threads. Use when working with OpentelemetryTracingModule, OpentelemetryGrpcExporterModule, OpentelemetryHttpExporterModule, KoraTracer, OpentelemetryContext, Tracer, Span, OTLP."
agent:
  use_when: "Use this file for Kora docs or implementation questions about OpenTelemetry tracing: choosing the OTLP/gRPC or OTLP/HTTP exporter, the tracing and tracing.exporter config sections, per-module telemetry.tracing options, W3C trace context propagation, sampling, creating spans manually and carrying the trace context to another thread; key triggers include OpentelemetryTracingModule, OpentelemetryGrpcExporterModule, OpentelemetryHttpExporterModule, OpentelemetryTracingConfig, KoraTracer, OpentelemetryContext, Tracer, Span, SpanProcessor, SpanExporter, Sampler, OTLP."
---

Трассировка помогает связать отдельные операции приложения в единую цепочку выполнения и понять, где запрос провел время или завершился ошибкой.
Kora использует [`OpenTelemetry`](https://opentelemetry.io/docs/what-is-opentelemetry/) для создания `Span` и их экспорта в формате `OTLP`.

Kora регистрирует собственную реализацию `ContextStorage` для `OpenTelemetry`, поэтому текущий контекст трассировки переносится через `ScopedValue`, а не через thread local.
Благодаря этому `io.opentelemetry.context.Context.current()` и `io.opentelemetry.api.trace.Span.current()` возвращают корректные значения в любом месте внутри трассируемой операции, в том числе на виртуальных потоках.

Большинство `Span` создаются за вас: HTTP-сервер и клиент, база данных, потребитель и продюсер `Kafka`, gRPC-сервер и клиент и другие подсистемы создают собственные span через свою телеметрию,
а контекст трассировки переносится между сервисами по стандарту [W3C Trace Context](https://www.w3.org/TR/trace-context/).

Kora предоставляет два взаимоисключающих модуля экспортера, `OTLP/gRPC` и `OTLP/HTTP`; выберите ровно один в зависимости от протокола, который принимает ваш коллектор.
Любой из модулей экспортера транзитивно предоставляет базовую обвязку трассировки (`OpentelemetryTracingModule`), так что никакой другой зависимости для трассировки не требуется.

Пошаговое руководство перед справочным описанием смотрите в разделе [Наблюдаемость](../guides/observability.md).

## gRPC { #grpc }

Модуль экспортирует данные трассировки в `OpenTelemetry Collector` через `OTLP/gRPC`.
Он строит `OtlpGrpcSpanExporter` поверх `BatchSpanProcessor`, а типичный адрес коллектора — `http://localhost:4317`.

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:opentelemetry-tracing-exporter-grpc"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends OpentelemetryGrpcExporterModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:opentelemetry-tracing-exporter-grpc")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : OpentelemetryGrpcExporterModule
    ```

Модуль называется `io.koraframework.opentelemetry.tracing.exporter.grpc.OpentelemetryGrpcExporterModule` и приносит с собой отправщик `OkHttp`, который использует экспортер `OTLP/gRPC`.

## HTTP { #http }

Модуль экспортирует данные трассировки в `OpenTelemetry Collector` через `OTLP/HTTP`.
Он строит `OtlpHttpSpanExporter` поверх `BatchSpanProcessor`, а типичный адрес коллектора — `http://localhost:4318/v1/traces`.

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:opentelemetry-tracing-exporter-http"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends OpentelemetryHttpExporterModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:opentelemetry-tracing-exporter-http")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : OpentelemetryHttpExporterModule
    ```

Модуль называется `io.koraframework.opentelemetry.tracing.exporter.http.OpentelemetryHttpExporterModule`.
В отличие от модуля `OTLP/gRPC` он отправляет данные через отправщик на `JDK` HTTP-клиенте и не тянет `OkHttp` в приложение.

## Конфигурация { #configuration }

Трассировка описывается двумя секциями конфигурации.

Секция `tracing` описывается классом `OpentelemetryTracingConfig` и предоставляется модулем `OpentelemetryTracingModule`:

- `enabled` — глобальный переключатель трассировки (по умолчанию: `true`). При `false` Kora ставит `TracerProvider`-заглушку, поэтому `Span` не записываются и ничего не экспортируется.
- `attributes` — атрибуты `OpenTelemetry Resource` (по умолчанию: `{}`).

Секция `tracing.exporter` описывается классами `OpentelemetryGrpcExporterConfig` (для `OTLP/gRPC`) и `OpentelemetryHttpExporterConfig` (для `OTLP/HTTP`); у обоих интерфейсов одинаковый набор полей, поэтому смена модуля экспортера не меняет конфигурацию.
Если `tracing.exporter.endpoint` не указан, ни экспортер, ни обработчик span не создаются — приложение стартует, `Span` по-прежнему создаются и распространяются, просто их никогда не отправляют во внешний коллектор.

Поле `tracing.attributes` задает атрибуты `OpenTelemetry Resource`, которые добавляются к **каждому** экспортируемому `Span` всего сервиса.
По умолчанию оно пусто, поэтому укажите там хотя бы имя и пространство имен сервиса, например `service.name` и `service.namespace`, иначе коллектор получит span без принадлежности к сервису.
Эти общесервисные атрибуты `Resource` отличаются от атрибутов span уровня модуля, настраиваемых в секции `<module>.telemetry.tracing.attributes`: те добавляются только к span конкретной подсистемы — смотрите [Конфигурация трассировки модуля](#module-config).

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

    1. Включает трассировку для всего приложения (по умолчанию: `true`).
    2. Адрес `OpenTelemetry Collector` для экспорта трассировок (необязательный, значения по умолчанию нет). Для `gRPC` обычно используется `http://localhost:4317`, а для `HTTP` — `http://localhost:4318/v1/traces`.
    3. Таймаут установки соединения с экспортером (необязательный, значения по умолчанию нет — применяется значение экспортера `OpenTelemetry`).
    4. Максимальное время ожидания, пока экспортер отправляет один запрос `OTLP` (по умолчанию: `3s`).
    5. Задержка между отправками накопленных `Span` в коллектор (по умолчанию: `2s`).
    6. Максимальное количество `Span` в одной партии экспорта (по умолчанию: `512`).
    7. Максимальный размер очереди `Span`, ожидающих отправки (по умолчанию: `2048`).
    8. Максимальное время, которое `BatchSpanProcessor` ждет экспорта одной накопленной партии; это не то же самое, что `exportTimeout`, ограничивающий один запрос `OTLP` (по умолчанию: `30s`).
    9. Сжатие данных при экспорте, `gzip` или `none` (по умолчанию: `gzip`).
    10. Экспортировать ли `Span`, которые не были выбраны `Sampler` (по умолчанию: `false`).
    11. Политика повторных попыток при неудачном экспорте (необязательная, весь блок можно опустить, и тогда каждое значение ниже принимает своё значение по умолчанию).
    12. Максимальное количество повторных попыток (по умолчанию: `5`).
    13. Начальная задержка перед повторной попыткой (по умолчанию: `1s`).
    14. Максимальная задержка перед повторной попыткой (по умолчанию: `5s`).
    15. Множитель задержки между повторными попытками (по умолчанию: `1.5`).
    16. Атрибуты `OpenTelemetry Resource`, добавляемые к каждому экспортируемому `Span` (по умолчанию: `{}`).

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

    1. Включает трассировку для всего приложения (по умолчанию: `true`).
    2. Адрес `OpenTelemetry Collector` для экспорта трассировок (необязательный, значения по умолчанию нет). Для `gRPC` обычно используется `http://localhost:4317`, а для `HTTP` — `http://localhost:4318/v1/traces`.
    3. Таймаут установки соединения с экспортером (необязательный, значения по умолчанию нет — применяется значение экспортера `OpenTelemetry`).
    4. Максимальное время ожидания, пока экспортер отправляет один запрос `OTLP` (по умолчанию: `3s`).
    5. Задержка между отправками накопленных `Span` в коллектор (по умолчанию: `2s`).
    6. Максимальное количество `Span` в одной партии экспорта (по умолчанию: `512`).
    7. Максимальный размер очереди `Span`, ожидающих отправки (по умолчанию: `2048`).
    8. Максимальное время, которое `BatchSpanProcessor` ждет экспорта одной накопленной партии; это не то же самое, что `exportTimeout`, ограничивающий один запрос `OTLP` (по умолчанию: `30s`).
    9. Сжатие данных при экспорте, `gzip` или `none` (по умолчанию: `gzip`).
    10. Экспортировать ли `Span`, которые не были выбраны `Sampler` (по умолчанию: `false`).
    11. Политика повторных попыток при неудачном экспорте (необязательная, весь блок можно опустить, и тогда каждое значение ниже принимает своё значение по умолчанию).
    12. Максимальное количество повторных попыток (по умолчанию: `5`).
    13. Начальная задержка перед повторной попыткой (по умолчанию: `1s`).
    14. Максимальная задержка перед повторной попыткой (по умолчанию: `5s`).
    15. Множитель задержки между повторными попытками (по умолчанию: `1.5`).
    16. Атрибуты `OpenTelemetry Resource`, добавляемые к каждому экспортируемому `Span` (по умолчанию: `{}`).

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

Если в приложении подключен также модуль [метрик](metrics.md), его `MeterProvider` передается экспортеру и обработчику span, и они сообщают свои внутренние метрики через тот же реестр.

## Автоматическая трассировка { #automatic }

Модуль трассировки в графе приложения предоставляет компонент `Tracer`.
Каждая подсистема Kora, у которой есть телеметрия, подхватывает этот `Tracer` и начинает создавать `Span` для своих операций: на каждый входящий запрос, исходящий вызов, сообщение, запрос к базе данных или запланированный запуск она открывает `Span`, привязывает его к текущему контексту, вкладывает в активный в этот момент `Span` и закрывает по завершении операции.
Для этих `Span` не требуется ни аннотаций, ни ручного кода.

Например, контроллер `GET /text` из примера телеметрии создает span типа `SERVER` с именем `GET /text`, а запрос репозитория вкладывается в него как span типа `CLIENT`:

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

В таблице ниже перечислены подсистемы, создающие `Span`, итоговое имя span и его [тип](https://opentelemetry.io/docs/specs/otel/trace/api/#spankind), а также основные атрибуты.
Имена атрибутов следуют [семантическим соглашениям OpenTelemetry](https://opentelemetry.io/docs/specs/semconv/).

| Подсистема          | Имя span                                          | Тип                     | Основные атрибуты                                                                                                                                                  |
|---------------------|---------------------------------------------------|-------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| HTTP-сервер         | `<METHOD> <route>`, например `GET /text`          | `SERVER`                | `http.request.method`, `http.route`, `url.scheme`, `url.path`, `server.address`, `server.port`, `server.name`, `http.response.status_code`, `http.response.result_code` |
| HTTP-клиент         | `<METHOD> <uriTemplate>`                          | `CLIENT`                | `http.request.method`, `http.route`, `server.address`, `server.port`, `url.scheme`, `url.path`, `url.full`, `http.response.status_code`, `http.response.result_code`    |
| База данных         | `<Repository>.<method>`                           | `CLIENT`                | `db.system.name`, `db.query.text`                                                                                                                                    |
| Потребитель Kafka   | `kafka.poll`, `<topic> process record`            | `CONSUMER`              | `messaging.system` = `kafka`, `messaging.client.id`, `messaging.consumer.group.name`, `messaging.destination.name`, `messaging.destination.partition.id`, `messaging.kafka.offset` |
| Продюсер Kafka      | `<topic> send`, `producer transaction`            | `PRODUCER` / `INTERNAL` | `messaging.system` = `kafka`, `messaging.operation.type` = `send`, `messaging.destination.name`                                                                       |
| gRPC-сервер         | `<service>/<method>`                              | `SERVER`                | `rpc.system` = `grpc`, `rpc.service`, `rpc.method`, `server.port`, `server.name`, `network.peer.address`                                                              |
| gRPC-клиент         | `<fullMethodName>`                                | `CLIENT`                | `rpc.system` = `grpc`, `rpc.service`, `rpc.method`, `server.address`, `server.port`                                                                                  |
| SOAP-клиент         | `SOAP <service> <method>`                         | `CLIENT`                | `rpc.system` = `soap`, `rpc.service`, `rpc.method`, `server.address`, `server.port`                                                                                  |
| S3-клиент           | `S3.<operation>`                                  | `CLIENT`                | `rpc.system` = `s3`, `rpc.method`, `aws.s3.bucket`                                                                                                                   |
| Потребитель JMS     | `<destination> receive`                           | `CONSUMER`              | `messaging.system` = `jms`, `messaging.destination.name`, `messaging.message.id`                                                                                    |
| Планировщик         | `scheduling <class>`                              | `INTERNAL`              | `code.function.name`                                                                                                                                                 |
| Кэш Redis           | `cache.operation`                                 | `INTERNAL`              | `operation`, `origin` = `redis`                                                                                                                                      |
| Camunda BPMN        | `Camunda Delegate <name>`                         | `INTERNAL`              | `delegate`                                                                                                                                                           |
| Camunda REST        | `<METHOD> <route>`                                | `SERVER`                | `http.request.method`, `http.route`, `url.scheme`, `url.path`, `server.address`                                                                                      |
| Zeebe Worker        | `Zeebe Worker <type>`                             | `INTERNAL`              | `jobType`, `jobName`, `jobKey`, `jobWorker`, `processKey`, `elementId`                                                                                              |

Span *именованных* компонентов дополнительно несут атрибуты, говорящие, из какого объявления они пришли: `system.config` (путь конфигурации компонента), `system.name.simple` и `system.name.canonical` (простое и каноническое имена класса объявления).
Их проставляют HTTP-клиент, потребитель и продюсер `Kafka`, SOAP- и S3-клиенты, кэши и запланированные задачи; в AWS-клиенте S3 первый из них называется `system.path`, а не `system.config`.

Несколько деталей, которые стоит знать:

- HTTP-сервер создает span только для запроса, попавшего в маршрут, потому что имя span строится из шаблона маршрута. Запросы, завершающиеся `404` из-за несовпадения маршрута, span не порождают.
- `url.path` и `url.full` добавляются только при включенном `tracePathFull` (сервер) или `pathFull` (клиент), что является поведением по умолчанию — выключите их, чтобы идентификаторы не попадали в трассировку.
- Потребитель `Kafka` открывает span `kafka.poll` на весь poll и по одному span `<topic> process record` на запись; span записи имеет родителем контекст, извлеченный из заголовков записи, и *связан* со span `kafka.poll`.
- Кэш `Caffeine` и аспекты [отказоустойчивости](resilient.md) сообщают метрики и логи, но span не создают.
- При ошибке Kora устанавливает статус span в `ERROR` и записывает исключение через `Span#recordException`. Большинство подсистем при успехе выставляют `OK`; HTTP-сервер и HTTP-клиент оставляют успешный span в статусе `UNSET` и помечают `ERROR` только для статуса `4xx`/`5xx` или при ошибке соединения.

## Конфигурация трассировки модуля { #module-config }

Трассировка каждой подсистемы настраивается в секции `telemetry.tracing` соответствующего модуля, описываемой классом `io.koraframework.telemetry.common.TelemetryConfig.TracingConfig`.
Для каждой подсистемы доступны две опции:

- `enabled` (по умолчанию: `true`) — включает или выключает span подсистемы. Установите `false`, чтобы прекратить создание span для конкретного модуля, не удаляя экспортер.
- `attributes` (по умолчанию: `{}`) — набор пар ключ/значение, добавляемых к каждому span, создаваемому **только этим модулем**. Эти атрибуты уровня span отличаются от общесервисных `tracing.attributes` (атрибутов `Resource`), применяемых ко всем span.

Обратите внимание, что здесь `enabled` по умолчанию равно `true`, в отличие от `telemetry.logging.enabled` и `telemetry.metrics.enabled`, у которых по умолчанию `false`.
Две группы модулей переопределяют это значение на `false`: [системный HTTP-сервер](http-server.md) (`httpServer.system.telemetry.tracing`) и аспекты [отказоустойчивости](resilient.md).

Секция `telemetry.tracing` располагается по тому же пути, что и собственная конфигурация модуля:

| Подсистема           | Путь конфигурации                                                        |
|----------------------|--------------------------------------------------------------------------|
| HTTP-сервер          | `httpServer.telemetry.tracing`                                            |
| Системный HTTP-сервер | `httpServer.system.telemetry.tracing`                                    |
| HTTP-клиент          | `httpClient.<name>.telemetry.tracing`                                     |
| База данных JDBC     | `jdbc.telemetry.tracing`                                                  |
| База данных Cassandra | `cassandra.telemetry.tracing`                                            |
| gRPC-сервер          | `grpcServer.telemetry.tracing`                                            |
| gRPC-клиент          | `grpcClient.<ServiceName>.telemetry.tracing`                              |
| Потребитель Kafka    | `kafka.consumer.<name>.telemetry.tracing`                                 |
| Продюсер Kafka       | `kafka.producer.<name>.telemetry.tracing`                                 |
| Планировщик          | `scheduling.telemetry.tracing`                                            |
| Кэш                  | `<путь конфигурации кэша>.telemetry.tracing`                              |

Две подсистемы добавляют собственную опцию поверх `enabled` и `attributes`:

- `httpServer.telemetry.tracing.tracePathFull` (по умолчанию: `true`) — добавляет в span сервера `url.path` с реальным путем запроса.
- `httpClient.<name>.telemetry.tracing.pathFull` (по умолчанию: `true`) — добавляет в span клиента `url.path` и `url.full` с реальным URI запроса.

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

    1. Включает трассировку HTTP-сервера (по умолчанию: `true`).
    2. Добавляет реальный путь запроса как `url.path` в span HTTP-сервера (по умолчанию: `true`).
    3. Атрибуты уровня span, добавляемые только к span HTTP-сервера (по умолчанию: `{}`).
    4. Отключает трассировку запросов к базе данных (по умолчанию: `true`).

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

    1. Включает трассировку HTTP-сервера (по умолчанию: `true`).
    2. Добавляет реальный путь запроса как `url.path` в span HTTP-сервера (по умолчанию: `true`).
    3. Атрибуты уровня span, добавляемые только к span HTTP-сервера (по умолчанию: `{}`).
    4. Отключает трассировку запросов к базе данных (по умолчанию: `true`).

Специфичные для модуля параметры трассировки также описаны в документации соответствующих модулей, например [HTTP-сервер](http-server.md), [HTTP-клиент](http-client.md), [gRPC-сервер](grpc-server.md), [gRPC-клиент](grpc-client.md) и [Kafka](kafka.md).

## Распространение контекста { #propagation }

Kora сшивает распределенные трассировки по стандарту [W3C Trace Context](https://www.w3.org/TR/trace-context/) через `W3CTraceContextPropagator`.
Это происходит автоматически и не требует настройки:

- **HTTP-сервер** — `traceparent` извлекается из заголовков запроса и становится родителем серверного `Span`; идентификаторы этого span затем записываются обратно в заголовки **ответа**, чтобы вызывающая сторона могла сопоставить ответ с трассировкой.
- **Kafka** — `traceparent` внедряется в заголовки записи продюсером и извлекается из них потребителем, поэтому каждый span `<topic> process record` продолжает трассировку продюсера.
- **gRPC-клиент** — `traceparent` внедряется в метаданные вызова.
- **gRPC-сервер** — `traceparent` извлекается из метаданных вызова и внедряется обратно в метаданные заголовков ответа.
- **Потребитель JMS** — `traceparent` извлекается из свойств сообщения.
- **Camunda REST и Zeebe Worker** — `traceparent` извлекается из заголовков запроса и заголовков задачи соответственно.

Исключение — HTTP-клиент Kora: он открывает `CLIENT`-span на исходящий вызов, чтобы вызов был виден в вашей собственной трассировке, но **не** пишет `traceparent` в исходящий запрос.
Если нижележащий сервис должен продолжать ту же трассировку, добавьте заголовок самостоятельно в [перехватчике HTTP-клиента](http-client.md).

Внутри одного сервиса передавать вручную ничего не нужно: текущий `Span` живет в `ScopedValue`, поэтому созданный вами вручную span (смотрите [Синхронная трассировка](#tracing-sync)) автоматически становится родителем всего, что вызвано внутри него в том же потоке.
Единственный случай, требующий явных действий, — переход границы потока, смотрите [Асинхронная трассировка](#async-tracing).

## Сэмплирование { #sampling }

Базовые компоненты трассировки предоставляются модулем `OpentelemetryTracingModule` как `@DefaultComponent`, а значит каждый из них можно заменить, объявив собственный компонент того же типа:

- `Sampler` — решает, какие `Span` записываются. По умолчанию используется `Sampler.parentBased(Sampler.alwaysOn())`, то есть записывается каждый корневой `Span`, а для дочерних `Span` следует решению родителя.
- `IdGenerator` — генерирует идентификаторы трассировки и span. По умолчанию используется `IdGenerator.random()`.
- `Supplier<SpanLimits>` — ограничения на количество атрибутов, событий и связей у одного `Span`. По умолчанию используется `SpanLimits.getDefault()`.
- `KoraTracer` — помощник для [ручного создания span](#tracing-sync).

Модули экспортера тоже объявляют `SpanExporter` и `SpanProcessor` как `@DefaultComponent`, поэтому приложение может отправлять span куда угодно, предоставив собственные реализации.

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

Текущий контекст трассировки читается через стандартный API `OpenTelemetry` — Kora подставляет за ним собственное хранилище, поэтому специфичный для Kora аксессор не нужен.

Чтобы получить текущий `Span`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var span = io.opentelemetry.api.trace.Span.current();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val span = io.opentelemetry.api.trace.Span.current()
    ```

Чтобы получить текущий идентификатор трассировки:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var traceId = io.opentelemetry.api.trace.Span.current().getSpanContext().getTraceId();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val traceId = io.opentelemetry.api.trace.Span.current().getSpanContext().getTraceId()
    ```

Если текущего `Span` нет, `Span.current()` возвращает `Span.getInvalid()`, а его `SpanContext` сообщает `isValid() == false` с нулевым идентификатором трассировки, поэтому эти вызовы никогда не возвращают `null` и не бросают исключение.

Механика, которая это обеспечивает, находится в пакете `io.koraframework.common.telemetry`:

- `OpentelemetryContext` — реализация `io.opentelemetry.context.Context` поверх `ScopedValue`. Kora регистрирует её как `ContextStorageProvider` для `OpenTelemetry`, поэтому `Context.current()` и `Span.current()` работают в любом потоке, в который вошла Kora, включая виртуальные.
- `OpentelemetryContext.VALUE` — сам `ScopedValue<Context>`. Привязка через `ScopedValue.where(OpentelemetryContext.VALUE, ctx)` — это и есть способ сделать контекст текущим; `Context#makeCurrent()` намеренно не поддерживается и бросает `IllegalStateException`, потому что scoped value нельзя присоединить и отсоединить императивно.
- `Observation` — объект телеметрии текущей операции того модуля, который сейчас выполняется, также привязанный к `ScopedValue`. `Observation.current(HttpServerObservation.class)` возвращает его, а `observation.span()` дает собственный span модуля; вызов бросает исключение, если привязанного observation такого типа нет.

## Корреляция логов { #mdc }

Корреляция логов выполняется [модулем Logback](logging-slf4j.md#logback): `KoraAsyncAppender` захватывает `Span.current().getSpanContext()` в момент постановки события в очередь, а `ConsoleTextRecordEncoder` пишет `traceId=` и `spanId=` в строку лога всякий раз, когда этот контекст span валиден.

```xml
<appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
    <encoder class="io.koraframework.logging.logback.ConsoleTextRecordEncoder"/>
</appender>

<appender name="ASYNC" class="io.koraframework.logging.logback.KoraAsyncAppender">
    <appender-ref ref="STDOUT"/>
</appender>
```

В результате каждая строка лога, порожденная в рамках трассируемой операции, несет `traceId` и `spanId`, что позволяет переходить от записи лога к соответствующей трассировке в системе наблюдаемости и обратно.
У строк, залогированных вне трассируемой операции, этих полей просто нет.

[MDC](logging-slf4j.md#mdc) в Kora — отдельный механизм для ваших собственных структурированных полей: идентификаторы трассировки через него не проходят, поэтому вокруг span ничего не нужно класть в `MDC` и удалять оттуда.

## Синхронная трассировка { #tracing-sync }

Помимо `Span`, создаваемых фреймворком, вы можете создавать собственные.
Самый простой способ — компонент `KoraTracer`: он строит `Span`, привязывает его как текущий контекст на время вызова, выставляет статус, записывает исключение, если оно было брошено, и завершает span — всё это одним вызовом.

- `traceParent(name, …)` — создает `Span`, вложенный в активный в этот момент.
- `traceNew(name, …)` — создает корневой `Span` без родителя, для работы, которая должна начинать собственную трассировку.
- `tracer()` — возвращает лежащий в основе `io.opentelemetry.api.trace.Tracer`, когда нужен полный контроль.

Каждый из них принимает либо `TraceCallable`, возвращающий значение, либо `TraceRunnable`, который ничего не возвращает; оба получают созданный `Span`, чтобы к нему можно было добавить атрибуты и события.

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

    1. `traceParent` перегружен для `TraceCallable` и `TraceRunnable`, а `Kotlin` не может сам выбрать между двумя функциональными интерфейсами — передайте явный SAM-конструктор.

Если нужно что-то, чего `KoraTracer` не покрывает, например собственный вид span или связь с другой трассировкой, постройте `Span` из `Tracer` самостоятельно и привяжите его как текущий контекст на время операции:

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

## Асинхронная трассировка { #async-tracing }

Контекст трассировки — это `ScopedValue`, а scoped value виден только внутри той динамической области, которая его связала.
Поэтому передача работы в другой поток теряет контекст, если не перенести его явно: захватите `io.opentelemetry.context.Context.current()` в вызывающем потоке и заново привяжите его в рабочем.

`OpentelemetryContext` реализует семейство методов `wrap` интерфейса `Context` из `OpenTelemetry` поверх `ScopedValue`, поэтому обычно достаточно обернуть задачу — доступны `wrap(Runnable)`, `wrap(Callable)`, `wrapSupplier`, `wrapFunction` и `wrapConsumer`.

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

    1. Захвачен, пока span еще текущий, поэтому уже содержит span `myOperation`.
    2. `wrapSupplier` заново привязывает этот контекст вокруг вызова в рабочем потоке.

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

    1. Захвачен, пока span еще текущий, поэтому уже содержит span `myOperation`.
    2. `wrapSupplier` заново привязывает этот контекст вокруг вызова в рабочем потоке.

Учтите, что `KoraTracer` завершает span сразу после возврата из своего колбэка, а для примера выше это происходит до завершения future.
Когда span должен покрывать всю асинхронную операцию, стройте его из `Tracer` самостоятельно, как показано в разделе [Синхронная трассировка](#tracing-sync), и вызывайте `span.end()` из колбэка завершения.
