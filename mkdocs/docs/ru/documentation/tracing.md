---
description: "Explains Kora OpenTelemetry tracing over gRPC and HTTP, tracing configuration, trace context propagation, synchronous tracing, and asynchronous tracing. Use when working with TracingModule, OpenTelemetry, GrpcSender, OpentelemetryContext, Span, TraceContext, OTLP."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora OpenTelemetry tracing over gRPC and HTTP, tracing configuration, trace context propagation, synchronous tracing, and asynchronous tracing; key triggers include TracingModule, OpenTelemetry, GrpcSender, OpentelemetryContext, Span, TraceContext, OTLP."
---

Трассировка помогает связать отдельные операции приложения в одну цепочку выполнения и понять, где запрос провел время или завершился ошибкой.
Kora использует [`OpenTelemetry`](https://opentelemetry.io/docs/what-is-opentelemetry/) для создания `Span`, хранения текущего контекста трассировки в `OpentelemetryContext` и экспорта данных в формате `OTLP`.

Текущий `Span` хранится в контексте Kora, поэтому его можно передавать между компонентами приложения и использовать при ручном создании вложенных `Span`.
При установке `OpentelemetryContext` Kora также добавляет `traceId` и `spanId` в `MDC`, чтобы эти идентификаторы попадали в логи при использовании модуля логирования.

Если нужен пошаговый разбор перед справочным описанием, смотрите [Наблюдаемость](../guides/observability.md).

## gRPC { #grpc }

Модуль экспортирует трассировку в `OpenTelemetry Collector` через `OTLP/gRPC`.
Для этого используется `GrpcSender`, а типичный адрес коллектора выглядит как `http://localhost:4317`.

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

Модуль экспортирует трассировку в `OpenTelemetry Collector` через `OTLP/HTTP`.
Для этого используется `HttpSender`, а типичный адрес коллектора выглядит как `http://localhost:4318/v1/traces`.

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

Параметры экспорта описаны в классах `OpentelemetryGrpcExporterConfig` и `OpentelemetryHttpExporterConfig`, а атрибуты ресурса описаны в классе `OpentelemetryResourceConfig`.
Если `tracing.exporter.endpoint` не указан, экспортер не создается и приложение стартует без отправки трассировок во внешний коллектор.

Поле `tracing.attributes` задает атрибуты `OpenTelemetry Resource`, которые добавляются к экспортируемым `Span`.
Обычно здесь указывают имя сервиса и пространство имен, например `service.name` и `service.namespace`.

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

    1. Адрес `OpenTelemetry Collector` для экспорта трассировок (по умолчанию не указано, необязательно). Для `gRPC` обычно используется `http://localhost:4317`, для `HTTP` обычно используется `http://localhost:4318/v1/traces`.
    2. Время ожидания соединения с экспортером (по умолчанию не указано, необязательно).
    3. Максимальное время ожидания отправки данных экспортером (по умолчанию: `3s`).
    4. Период между отправками накопленных `Span` в коллектор (по умолчанию: `2s`).
    5. Максимальное количество `Span` в одной отправке (по умолчанию: `512`).
    6. Максимальный размер очереди `Span`, ожидающих отправки (по умолчанию: `2048`).
    7. Максимальное время ожидания пакетной отправки (по умолчанию: `30s`).
    8. Сжатие данных при экспорте (по умолчанию: `gzip`).
    9. Экспортировать ли `Span`, которые не были выбраны `Sampler` (по умолчанию: `false`).
    10. Максимальное количество попыток повторной отправки (по умолчанию: `5`).
    11. Начальная задержка перед повторной отправкой (по умолчанию: `1s`).
    12. Максимальная задержка перед повторной отправкой (по умолчанию: `5s`).
    13. Множитель задержки между повторными отправками (по умолчанию: `1.5`).
    14. Атрибуты `OpenTelemetry Resource`, которые будут добавлены к экспортируемым `Span` (по умолчанию: `{}`).

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

    1. Адрес `OpenTelemetry Collector` для экспорта трассировок (по умолчанию не указано, необязательно). Для `gRPC` обычно используется `http://localhost:4317`, для `HTTP` обычно используется `http://localhost:4318/v1/traces`.
    2. Время ожидания соединения с экспортером (по умолчанию не указано, необязательно).
    3. Максимальное время ожидания отправки данных экспортером (по умолчанию: `3s`).
    4. Период между отправками накопленных `Span` в коллектор (по умолчанию: `2s`).
    5. Максимальное количество `Span` в одной отправке (по умолчанию: `512`).
    6. Максимальный размер очереди `Span`, ожидающих отправки (по умолчанию: `2048`).
    7. Максимальное время ожидания пакетной отправки (по умолчанию: `30s`).
    8. Сжатие данных при экспорте (по умолчанию: `gzip`).
    9. Экспортировать ли `Span`, которые не были выбраны `Sampler` (по умолчанию: `false`).
    10. Максимальное количество попыток повторной отправки (по умолчанию: `5`).
    11. Начальная задержка перед повторной отправкой (по умолчанию: `1s`).
    12. Максимальная задержка перед повторной отправкой (по умолчанию: `5s`).
    13. Множитель задержки между повторными отправками (по умолчанию: `1.5`).
    14. Атрибуты `OpenTelemetry Resource`, которые будут добавлены к экспортируемым `Span` (по умолчанию: `{}`).

Параметры включения трассировки в конкретных модулях описываются в документации этих модулей, например [HTTP сервер](http-server.md), [HTTP клиент](http-client.md), [gRPC-сервер](grpc-server.md), [gRPC-клиент](grpc-client.md).

## Контекст трассировки { #tracing-context }

Чтобы получить текущий `Span`, можно использовать метод `getSpan` у `OpentelemetryContext`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var span = OpentelemetryContext.getSpan();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val span = OpentelemetryContext.getSpan()
    ```

Для получения текущего идентификатора трассировки можно использовать метод `getTraceId()` у `OpentelemetryContext`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var traceId = OpentelemetryContext.getTraceId();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val traceId = OpentelemetryContext.getTraceId()
    ```

Если текущего `Span` нет, оба метода вернут `null`.
Если нужно получить значение-заглушку от `OpenTelemetry`, используйте методы `getSpanOrInvalid()` и `getTraceIdOrInvalid()`.

## Синхронная трассировка { #tracing-sync }

Помимо автоматически создаваемых фреймворком `Span`, можно использовать объект `Tracer` из графа приложения и создавать собственные вложенные `Span`.
При ручной трассировке важно сохранить текущий `OpentelemetryContext`, установить новый контекст на время работы и восстановить исходный контекст в `finally`.

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

При переходе в другой поток выполнения нужно передать не только `Span`, но и контекст Kora.
Для `CompletionStage` используется `Context.fork()`, а для `suspend`-кода - `Context.Kotlin.asCoroutineContext(ctx)`.

===! ":fontawesome-brands-java: `Java`"

    Пример для асинхронного кода на `CompletionStage`:

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
