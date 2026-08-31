---
description: "Explains Kora metrics with Micrometer, Prometheus export through the system HTTP server, per-module telemetry.metrics configuration, registry and metric factory customization, and a full metric reference. Use when working with MetricsModule, MeterRegistry, MetricsScraper, PrometheusMeterRegistryInitializer, telemetry.metrics.enabled, httpServer.system.metricsPath, Metrics Reference."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora metrics with Micrometer, Prometheus export through the system HTTP server, the per-module telemetry.metrics block, registry and metric factory customization, and module-specific metric names and tags; key triggers include MetricsModule, MeterRegistry, MetricsScraper, PrometheusMeterRegistryInitializer, DefaultHttpServerMetricsFactory, telemetry.metrics.enabled, telemetry.metrics.slo, httpServer.system.metricsPath, Metrics Reference."
---

Модуль для сбора метрик приложения с помощью [Micrometer](https://micrometer.io/docs/concepts#_purpose).
Он создает `PrometheusMeterRegistry`, регистрирует его в контейнере зависимостей как `MeterRegistry` и отдает собранные значения в формате `Prometheus` через [системный HTTP-сервер](http-server.md#system-server).
Это позволяет собирать метрики приложения, `JVM`, процесса и встроенных интеграций в одном месте и опрашивать их внешней системой наблюдаемости.

Для публикации метрик требуется [системный HTTP-сервер](http-server.md#system-server), который отдает их в формате [Prometheus](https://prometheus.io/docs/concepts/data_model/).

!!! warning "Метрики модулей по умолчанию выключены"

    `TelemetryConfig.MetricsConfig#enabled` возвращает `false`, и это значение наследует каждый модуль.
    Приложение, в котором подключен только `MetricsModule`, стартует нормально и отвечает на `/metrics` кодом `200`,
    но в ответе будут лишь значения `JVM`, процесса и `kora.up` — никаких `http_server_*`, `http_client_*`,
    `db_*` или любых других метрик компонентов. Включайте метрики явно для каждого модуля через
    `<module>.telemetry.metrics.enabled = true`, смотрите [Метрики модуля](#module-metrics).

Пошаговое руководство перед справочным описанием смотрите в разделе [Наблюдаемость](../guides/observability.md).

## Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:micrometer-module"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends MetricsModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:micrometer-module")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : MetricsModule
    ```

`MetricsModule` находится в пакете `io.koraframework.micrometer.module`.
Он предоставляет только реестр и контракт эндпоинта для опроса — сами значения метрик создают подключенные вами модули
([HTTP-сервер](http-server.md), [HTTP-клиент](http-client.md), [База данных](database-common.md), [Kafka](kafka.md) и так далее).

## Конфигурация { #configuration }

У самого модуля нет секции конфигурации: в Kora 2.0 нет глобального блока `metrics { }`.
Все настраивается в двух местах — путь и порт эндпоинта опроса на системном сервере,
а также блок `telemetry.metrics` внутри каждого модуля, который сообщает метрики.

Пример конфигурации пути системного `HTTP`-сервера, описанной в классе `SystemHttpServerConfig` (указаны значения по умолчанию):

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
        system {
            port = 8085 //(1)!
            metricsPath = "/metrics" //(2)!
        }
    }
    ```

    1.  Порт системного `HTTP`-сервера, который обслуживает эндпоинт метрик (по умолчанию: `8085`).
    2.  Путь для получения метрик в формате `Prometheus` (по умолчанию: `"/metrics"`).

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      system:
        port: 8085 #(1)!
        metricsPath: "/metrics" #(2)!
    ```

    1.  Порт системного `HTTP`-сервера, который обслуживает эндпоинт метрик (по умолчанию: `8085`).
    2.  Путь для получения метрик в формате `Prometheus` (по умолчанию: `"/metrics"`).

### Метрики модуля { #module-metrics }

Каждый модуль, собирающий метрики, предоставляет блок `telemetry.metrics`, описанный в `TelemetryConfig.MetricsConfig`,
который позволяет включить метрики, настроить корзины гистограммы и добавить дополнительные теги только для этого модуля.
В примере ниже носителем выступает модуль [HTTP-сервер](http-server.md), но те же поля `telemetry.metrics` применяются дословно к
[HTTP-клиенту](http-client.md), [Базе данных](database-common.md), [Kafka](kafka.md), [gRPC-серверу](grpc-server.md),
[gRPC-клиенту](grpc-client.md), [Планировщику](scheduling.md), [Кэшу](cache.md), [Отказоустойчивости](resilient.md)
и любой другой интеграции, которая сообщает метрики:

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
        telemetry {
            metrics {
                enabled = true //(1)!
                slo = ["1ms", "10ms", "50ms", "100ms", "200ms", "500ms", "1s", "2s", "5s", "10s", "20s", "30s", "60s", "90s"] //(2)!
                tags { //(3)!
                    "key1" = "value1"
                    "key2" = "value2"
                }
            }
        }
    }
    ```

    1.  Включает сбор метрик для модуля (по умолчанию: `false`)
    2.  Корзины гистограммы [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) для метрик `Timer`, список длительностей (по умолчанию: `TelemetryConfig.MetricsConfig#DEFAULT_SLO`, перечислен в разделе [Персонализация](#personalization))
    3.  Дополнительные общие теги, добавляемые к каждой метрике, которую сообщает модуль (по умолчанию: `{}`)

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      telemetry:
        metrics:
          enabled: true #(1)!
          slo: [ "1ms", "10ms", "50ms", "100ms", "200ms", "500ms", "1s", "2s", "5s", "10s", "20s", "30s", "60s", "90s" ] #(2)!
          tags: #(3)!
            key1: value1
            key2: value2
    ```

    1.  Включает сбор метрик для модуля (по умолчанию: `false`)
    2.  Корзины гистограммы [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) для метрик `Timer`, список длительностей (по умолчанию: `TelemetryConfig.MetricsConfig#DEFAULT_SLO`, перечислен в разделе [Персонализация](#personalization))
    3.  Дополнительные общие теги, добавляемые к каждой метрике, которую сообщает модуль (по умолчанию: `{}`)

Значения `slo` — это длительности: строка несет свою единицу измерения (`"1ms"`, `"250ms"`, `"1s"`, `PT1S`), а голое число читается как миллисекунды,
поэтому `slo = [1, 10, 50]` и `slo = ["1ms", "10ms", "50ms"]` — это один и тот же список.

Оставленное `enabled = false` (значение по умолчанию) означает, что телеметрия модуля использует `Noop`-фабрику метрик: ни один `Meter` не создается и ничего не регистрируется в реестре.
Это же способ заглушить шумную интеграцию после того, как метрики были включены повсеместно.

Метрики создаются только при выполнении **обоих** условий: подключен `MetricsModule` (то есть в контейнере есть `MeterRegistry`)
и у модуля выставлено `telemetry.metrics.enabled = true`. Если чего-то из этого нет, модуль откатывается на пустую реализацию телеметрии.

### Пути конфигурации { #configuration-paths }

Блок `telemetry.metrics` вложен в собственную секцию конфигурации модуля:

| Модуль | Путь конфигурации |
|--------|--------------------|
| [HTTP-сервер](http-server.md) (публичный) | `httpServer.telemetry.metrics` |
| [HTTP-сервер](http-server.md#system-server) (системный) | `httpServer.system.telemetry.metrics` |
| [HTTP-клиент](http-client.md) | `httpClient.telemetry.metrics` и собственный путь конфигурации клиента из `@HttpClient` |
| [База данных JDBC](database-jdbc.md) | `jdbc.telemetry.metrics` |
| [База данных Cassandra](database-cassandra.md) | `cassandra.telemetry.metrics` |
| [gRPC-сервер](grpc-server.md) | `grpcServer.telemetry.metrics` |
| [gRPC-клиент](grpc-client.md) | `grpcClient.<ServiceName>.telemetry.metrics` |
| [Планировщик](scheduling.md) | `scheduling.telemetry.metrics` |
| [Отказоустойчивость](resilient.md) | `resilient.telemetry.{circuitBreaker,retry,timeout,fallback,rateLimiter}.metrics` |
| [Kafka](kafka.md) | собственный путь конфигурации потребителя или продюсера плюс `.telemetry.metrics` |
| [Кэш](cache.md) | путь конфигурации кэша из `@Cache` плюс `.telemetry.metrics` |
| [S3-клиент](s3-client.md) | `s3client.aws.telemetry.metrics` |
| Redis (`Lettuce`) | `lettuce.telemetry.metrics` |
| [Camunda 7 BPMN](camunda7-bpmn.md) | `camunda.engine.bpmn.telemetry.metrics` |
| [Camunda 7 REST](camunda7-rest.md) | `camunda.rest.telemetry.metrics` |
| [Camunda 8 Worker](camunda8-worker.md) | `zeebe.worker.telemetry.metrics` |

Некоторые модули добавляют рядом с `enabled` / `slo` / `tags` собственные ключи:

- [База данных](database-common.md) — `driverMetrics` (по умолчанию: `true`) регистрирует в том же реестре метрики пула соединений `HikariCP`.
- [Kafka](kafka.md) — `driverMetrics` (по умолчанию: `false`) регистрирует нативные метрики клиента `Kafka` через биндер `KafkaClientMetrics` из Micrometer, с префиксом имен `kafka.*`.
- [Camunda 7 BPMN](camunda7-bpmn.md) — `engineMetrics` (по умолчанию: `false`) включает собственные метрики движка `Camunda`.

Параметры сбора метрик также описаны в модулях, которые эти метрики собирают: [HTTP-сервер](http-server.md), [HTTP-клиент](http-client.md), [gRPC-сервер](grpc-server.md), [gRPC-клиент](grpc-client.md), [Планировщик](scheduling.md), [Кэш](cache.md) и другие интеграции.

## Использование { #usage }

Kora следует нотации, описанной в [спецификации `Prometheus`](https://prometheus.io/docs/concepts/data_model/).

После подключения модуля создается `PrometheusMeterRegistry`, он регистрируется в `Metrics.globalRegistry` и используется всеми компонентами, которые собирают метрики.
При остановке приложения этот реестр удаляется из `Metrics.globalRegistry` и закрывается.

Реестр предоставляется компонентом `PrometheusMeterRegistryWrapper`: это `Root`-компонент, реализующий `Wrapped<MeterRegistry>`,
поэтому пользовательский код внедряет контракт `MeterRegistry`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final MeterRegistry meterRegistry;

        public SomeService(MeterRegistry meterRegistry) {
            this.meterRegistry = meterRegistry;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(
        private val meterRegistry: MeterRegistry
    )
    ```

Реестр автоматически получает стандартные биндеры `Micrometer`: `ClassLoaderMetrics`, `JvmMemoryMetrics`, `JvmGcMetrics`, `ProcessorMetrics`, `JvmThreadMetrics`, `FileDescriptorMetrics`, `UptimeMetrics`.
Они привязываются при создании реестра и **не** зависят ни от одного флага `telemetry.metrics.enabled`.
Kora также регистрирует метрику `kora.up` со значением `1` и тегом `version`.

Дополнительно Kora связывает реестр `Micrometer` с `MeterProvider` из `OpenTelemetry` (`MicrometerMeterProvider` из `io.opentelemetry.contrib.metrics.micrometer`), поэтому библиотеки, инструментированные API метрик `OpenTelemetry`, публикуют данные через тот же реестр.
Мост объявлен как `@DefaultComponent` и принимает необязательный компонент `CallbackRegistrar`, если нужно управлять тем, как опрашиваются асинхронные инструменты.

Готовый к запуску базовый пример, который связывает `MetricsModule` вместе с `HoconConfigModule`, `LogbackModule`, `JdbcDatabaseModule`, `UndertowPublicHttpServerModule` и экспортером трассировок `OpenTelemetry`, доступен в примере [kora-java-telemetry](https://github.com/kora-projects/kora-examples/tree/master/examples/java/kora-java-telemetry).

### Экспорт в Prometheus { #prometheus-export }

Метрики отдаются в текстовом формате [Prometheus](https://prometheus.io/docs/concepts/data_model/) [системным HTTP-сервером](http-server.md#system-server) по пути `httpServer.system.metricsPath` (по умолчанию `/metrics`) на порту `httpServer.system.port` (по умолчанию `8085`):

```shell
curl http://localhost:8085/metrics
```

Направьте цель опроса вашего `Prometheus` (или любого совместимого сборщика) на тот же хост, порт и путь.

Эндпоинт всегда отвечает `200`. Что именно он вернет, зависит от того, что связано в контейнере:

- `MetricsModule` подключен — текстовое представление снимка реестра в формате `Prometheus`.
- `MetricsModule` не подключен — тело `# Metric Scraper disabled`, потому что компонента `MetricsScraper` не существует.
- Пользовательский `MeterRegistry`, который не является `PrometheusMeterRegistry` — пустое тело, потому что такой реестр нельзя выгрузить в формате `Prometheus`.
  В этом случае предоставьте собственную реализацию `MetricsScraper`: она переопределит `@DefaultComponent`, поставляемый `MetricsModule`.

`MetricsScraper` — это контракт с единственным методом из пакета `io.koraframework.telemetry.common`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface MetricsScraperModule {

        default MetricsScraper metricsScraper(MeterRegistry registry) {
            return os -> os.write(renderMyFormat(registry).getBytes(StandardCharsets.UTF_8));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface MetricsScraperModule {

        fun metricsScraper(registry: MeterRegistry): MetricsScraper {
            return MetricsScraper { os -> os.write(renderMyFormat(registry).toByteArray()) }
        }
    }
    ```

### Пользовательская метрика { #custom-metric }

Для пользовательской метрики лучше создать отдельный компонент, внедрить `MeterRegistry` и переиспользовать созданные экземпляры `Meter`.
Не создавайте новую метрику при каждом вызове метода: если набор тегов зависит от операции, используйте ключ с ограниченной кардинальностью и кэшируйте метрику в `ConcurrentHashMap`.
Вызов `register(...)` нужен для первоначальной регистрации метрики в `MeterRegistry`; на горячем пути предпочтительнее использовать уже созданный `Timer` / `Counter` / `Gauge` и вызывать только `record(...)` или `increment(...)`.
Kora использует такой же подход для своих внутренних метрик.

Например, метрика длительности внешней операции:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class ExternalOperationMetrics {

        private record Key(String operation, String status) {}

        private final MeterRegistry meterRegistry;
        private final ConcurrentHashMap<Key, Timer> timers = new ConcurrentHashMap<>();

        public ExternalOperationMetrics(MeterRegistry meterRegistry) {
            this.meterRegistry = meterRegistry;
        }

        public void record(String operation, String status, long durationNanos) {
            var key = new Key(operation, status);
            var timer = this.timers.computeIfAbsent(key, k -> Timer.builder("external.operation.duration")
                .tag("operation", k.operation())
                .tag("status", k.status())
                .register(this.meterRegistry));

            timer.record(durationNanos, TimeUnit.NANOSECONDS);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ExternalOperationMetrics(
        private val meterRegistry: MeterRegistry
    ) {

        private data class Key(
            val operation: String,
            val status: String
        )

        private val timers = ConcurrentHashMap<Key, Timer>()

        fun record(operation: String, status: String, durationNanos: Long) {
            val key = Key(operation, status)
            val timer = timers.computeIfAbsent(key) {
                Timer.builder("external.operation.duration")
                    .tag("operation", it.operation)
                    .tag("status", it.status)
                    .register(meterRegistry)
            }

            timer.record(durationNanos, TimeUnit.NANOSECONDS)
        }
    }
    ```

Значения тегов должны иметь ограниченное число вариантов.
Не используйте в качестве тегов идентификаторы пользователей, номера запросов, полный текст ошибки или другие значения с высокой кардинальностью.

## Персонализация { #personalization }

Чтобы изменить конфигурацию `PrometheusMeterRegistry`, добавьте в контейнер `PrometheusMeterRegistryInitializer`.
Инициализатор получает созданный реестр до регистрации стандартных системных метрик, поэтому он может добавить общие теги, `MeterFilter`, правила переименования или пользовательские настройки `PrometheusMeterRegistry`.
Все найденные в контейнере инициализаторы применяются последовательно, каждый получает результат предыдущего.

**Важно**, `PrometheusMeterRegistryInitializer` применяется только один раз при инициализации приложения.

Например, мы хотим добавить общий тег для всех метрик:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface MetricsConfigModule {

        default PrometheusMeterRegistryInitializer commonTagsInit() {
            return registry -> {
                registry.config().commonTags("tag", "value");
                return registry;
            };
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface MetricsConfigModule {

        fun commonTagsInit(): PrometheusMeterRegistryInitializer {
            return PrometheusMeterRegistryInitializer {
                it.config().commonTags("tag", "value")
                it
            }
        }
    }
    ```

У стандартных метрик также есть собственные настройки, например корзины гистограммы `slo` для метрик `Timer`, которые задаются для каждого модуля в блоке [`telemetry.metrics`](#module-metrics).
Когда `slo` не переопределено, используется `TelemetryConfig.MetricsConfig#DEFAULT_SLO` — 14 корзин:

`1ms`, `10ms`, `50ms`, `100ms`, `200ms`, `500ms`, `1s`, `2s`, `5s`, `10s`, `20s`, `30s`, `60s`, `90s`

Массив объявлен в `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig` и общий для всех модулей, которые строят `Timer`.

### Фабрики метрик { #metrics-factory }

Имена и теги метрик фреймворка формируются фабриками метрик отдельно для каждого модуля — по одному классу `Default<Module>MetricsFactory` на интеграцию
(пакет `<module>.telemetry.impl`). Фабрика телеметрии каждого модуля принимает такой класс как **необязательную** зависимость,
поэтому свой наследник, объявленный компонентом контейнера, заменяет реализацию по умолчанию:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class TenantHttpServerMetricsFactory extends DefaultHttpServerMetricsFactory { //(1)!

        @Override
        public DefaultHttpServerMetrics create(DefaultHttpServerTelemetry.TelemetryContext context) {
            return new TenantHttpServerMetrics(context);
        }

        private static final class TenantHttpServerMetrics extends DefaultHttpServerMetrics {

            private TenantHttpServerMetrics(DefaultHttpServerTelemetry.TelemetryContext context) {
                super(context);
            }

            @Override
            protected Timer.Builder createMetricServerDuration(DurationKey metricKey, //(2)!
                                                               HttpServerRequest request,
                                                               HttpServerResponse response,
                                                               @Nullable Throwable throwable) {
                return super.createMetricServerDuration(metricKey, request, response, throwable)
                    .tag("tenant", "default");
            }
        }
    }
    ```

    1.  Фабрику подхватывает `HttpServerModule#defaultHttpServerTelemetryFactory` вместо встроенной `DefaultHttpServerMetricsFactory`
    2.  В билдере допустимы только статические теги — тег, значение которого меняется от запроса к запросу, должен быть частью ключа метрики, иначе разные наборы тегов схлопнутся в один `Meter`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class TenantHttpServerMetricsFactory : DefaultHttpServerMetricsFactory() { //(1)!

        override fun create(context: DefaultHttpServerTelemetry.TelemetryContext): DefaultHttpServerMetrics {
            return TenantHttpServerMetrics(context)
        }

        private class TenantHttpServerMetrics(
            context: DefaultHttpServerTelemetry.TelemetryContext
        ) : DefaultHttpServerMetrics(context) {

            override fun createMetricServerDuration( //(2)!
                metricKey: DurationKey,
                request: HttpServerRequest,
                response: HttpServerResponse,
                throwable: Throwable?
            ): Timer.Builder {
                return super.createMetricServerDuration(metricKey, request, response, throwable)
                    .tag("tenant", "default")
            }
        }
    }
    ```

    1.  Фабрику подхватывает `HttpServerModule#defaultHttpServerTelemetryFactory` вместо встроенной `DefaultHttpServerMetricsFactory`
    2.  В билдере допустимы только статические теги — тег, значение которого меняется от запроса к запросу, должен быть частью ключа метрики, иначе разные наборы тегов схлопнутся в один `Meter`

Тот же приём работает для любой интеграции, имя класса следует за модулем:
`DefaultHttpClientMetricsFactory`, `DefaultDatabaseMetricsFactory`, `DefaultKafkaConsumerMetricsFactory`, `DefaultKafkaPublisherMetricsFactory`,
`DefaultGrpcServerMetricsFactory`, `DefaultGrpcClientMetricsFactory`, `DefaultSoapClientMetricsFactory`, `DefaultSchedulingMetricsFactory`,
`DefaultCaffeineCacheMetricsFactory`, `DefaultRedisCacheMetricsFactory`, `DefaultCircuitBreakerMetricsFactory`, `DefaultRetryMetricsFactory`,
`DefaultTimeoutMetricsFactory`, `DefaultFallbackMetricsFactory`, `DefaultRateLimiterMetricsFactory`, `DefaultAwsS3ClientMetricsFactory`,
`DefaultJmsConsumerMetricsFactory`.

Если тег должен зависеть от текущего запроса, добавляйте его в ключ метрики, а не в билдер:
у каждой фабрики для этого есть методы `create<Metric>Key(...)` и записи-ключи с методом копирования `withExtraTags(Tags)`.

Если дополнительные теги одинаковы для всех метрик модуля, фабрику писать не нужно — используйте ключ конфигурации [`telemetry.metrics.tags`](#module-metrics).

## Стандарт { #standard }

Все метрики Kora следуют [семантическим соглашениям OpenTelemetry](https://opentelemetry.io/docs/specs/semconv/) для имен и тегов,
и каждый модуль использует ровно одну схему именования — настраиваемой версии спецификации больше нет.
Ключи тегов берутся из констант атрибутов `io.opentelemetry.semconv`, поэтому, например, метрика `HTTP`-сервера несет
`http.request.method`, `http.route`, `url.scheme`, `server.address` и `error.type`.

Имена в экспозиции `Prometheus` выводятся из имени `Micrometer` по соглашению об именовании `Prometheus`:

- `.` заменяется на `_`;
- `Timer` получает суффикс `_seconds`, а гистограмма отдается сериями `_bucket` / `_count` / `_sum` плюс отдельный gauge `_max`;
- `Counter` получает свою базовую единицу измерения и суффикс `_total` (поэтому метрики, построенные с `BaseUnits.OPERATIONS`, заканчиваются на `_operations_total`);
- `Gauge` получает суффиксом свою базовую единицу измерения, если метрика её объявляет.

Тег `error.type` всегда присутствует у метрик, которые могут завершиться ошибкой — он содержит каноническое имя класса исключения или пустую строку при успехе.

## Справочник метрик { #metrics-reference }

Используемые типы метрик [Micrometer](https://docs.micrometer.io/micrometer/reference/concepts.html):

- [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) — длительность операции с поддержкой count, sum, max и корзин гистограммы
- [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) — монотонно возрастающий счетчик
- [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) — текущее значение метрики

Каждая перечисленная ниже метрика дополнительно несет теги, заданные в [`telemetry.metrics.tags`](#module-metrics) соответствующего модуля.

### HTTP-сервер { #http-server }

| Метрика | Prometheus | Тип | Описание | Теги |
|--------|------------|------|-------------|------|
| `http.server.request.duration` | `http_server_request_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | Длительность обработки запроса `HTTP`-сервером | `server.name`, `server.port`, `http.request.method`, `http.route`, `url.scheme`, `server.address`, `error.type` |
| `http.server.active_requests` | `http_server_active_requests` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Количество активных `HTTP`-запросов | `server.name`, `server.port`, `http.request.method`, `http.route`, `url.scheme`, `server.address` |

Тег `server.name` отличает публичный сервер (`kora-undertow`) от системного (`kora-undertow-system`); для запроса, не совпавшего ни с одним маршрутом, `http.route` равен `UNKNOWN_ROUTE`.

Подробнее смотрите в документации модуля [HTTP-сервер](http-server.md).

### HTTP-клиент { #http-client }

| Метрика | Prometheus | Тип | Описание | Теги |
|--------|------------|------|-------------|------|
| `http.client.request.duration` | `http_client_request_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | Длительность запроса `HTTP`-клиента | `http.request.method`, `http.response.status_code`, `server.address`, `url.scheme`, `http.route`, `error.type`, `system.config`, `system.name.simple`, `system.name.canonical` |

`system.config` — путь конфигурации клиента, `system.name.simple` и `system.name.canonical` — простое и каноническое имена интерфейса декларативного клиента.

Подробнее смотрите в документации модуля [HTTP-клиент](http-client.md).

### База данных { #database }

| Метрика | Prometheus | Тип | Описание | Теги |
|--------|------------|------|-------------|------|
| `db.client.operation.duration` | `db_client_operation_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | Длительность операции/запроса к базе данных | `db.client.connection.pool.name`, `db.system.name`, `db.query.text`, `db.operation.name`, `error.type` |

Тег `db.system.name` берется из строки подключения для [JDBC](database-jdbc.md) (`postgresql`, `mysql`, ...) и равен `cassandra` для [Cassandra](database-cassandra.md).
В `db.query.text` попадает идентификатор запроса, а не исходный текст `SQL`.

При `telemetry.metrics.driverMetrics = true` (значение по умолчанию) пул соединений дополнительно регистрирует в том же реестре собственные метрики:
метрики пула `HikariCP` для [JDBC](database-jdbc.md) и метрики драйвера `DataStax`, отобранные настройкой `cassandra.telemetry.metrics`, для [Cassandra](database-cassandra.md).

Подробнее смотрите в документации модуля [База данных](database-common.md).

### Kafka { #kafka }

| Метрика | Prometheus | Тип | Описание | Теги |
|--------|------------|------|-------------|------|
| `messaging.process.duration` | `messaging_process_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | Длительность обработки одного сообщения | `messaging.system`, `messaging.client.id`, `messaging.consumer.group.name`, `messaging.destination.name`, `messaging.destination.partition.id`, `error.type`, `system.config`, `system.name.simple`, `system.name.canonical` |
| `messaging.process.batch.duration` | `messaging_process_batch_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | Длительность обработки пакета сообщений | `messaging.system`, `messaging.client.id`, `messaging.consumer.group.name`, `error.type`, `system.config`, `system.name.simple`, `system.name.canonical` |
| `messaging.kafka.consumer.lag` | `messaging_kafka_consumer_lag` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Отставание потребителя по разделу | `messaging.system`, `messaging.client.id`, `messaging.consumer.group.name`, `messaging.destination.name`, `messaging.destination.partition.id`, `system.config`, `system.name.simple`, `system.name.canonical` |
| `messaging.client.operation.duration` | `messaging_client_operation_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | Длительность отправки сообщения | `messaging.system`, `messaging.client.id`, `messaging.operation.type`, `messaging.destination.name`, `messaging.destination.partition.id`, `error.type`, `system.config`, `system.name.simple`, `system.name.canonical` |
| `messaging.client.sent.messages` | `messaging_client_sent_messages_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество отправленных сообщений | `messaging.system`, `messaging.client.id`, `messaging.operation.type`, `messaging.destination.name`, `messaging.destination.partition.id`, `error.type`, `system.config`, `system.name.simple`, `system.name.canonical` |

Тег `messaging.system` всегда равен `kafka`; `messaging.operation.type` на стороне продюсера равен `send`.

Подробнее смотрите в документации модуля [Kafka](kafka.md).

### gRPC-сервер { #grpc-server }

| Метрика | Prometheus | Тип | Описание | Теги |
|--------|------------|------|-------------|------|
| `rpc.server.duration` | `rpc_server_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | Длительность обработки вызова gRPC-сервером | `server.name`, `server.port`, `rpc.system`, `rpc.service`, `rpc.method`, `rpc.grpc.status_code` |

Подробнее смотрите в документации модуля [gRPC-сервер](grpc-server.md).

### gRPC-клиент { #grpc-client }

| Метрика | Prometheus | Тип | Описание | Теги |
|--------|------------|------|-------------|------|
| `rpc.client.duration` | `rpc_client_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | Длительность вызова gRPC-клиента | `rpc.system`, `rpc.service`, `rpc.method`, `rpc.grpc.status_code`, `server.address`, `server.port`, `error.type` |

Тег `rpc.system` равен `grpc` и для gRPC-сервера, и для gRPC-клиента.

Подробнее смотрите в документации модуля [gRPC-клиент](grpc-client.md).

### SOAP-клиент { #soap-client }

| Метрика | Prometheus | Тип | Описание | Теги |
|--------|------------|------|-------------|------|
| `rpc.client.duration` | `rpc_client_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | Длительность вызова SOAP-клиента | `rpc.system`, `rpc.service`, `rpc.method`, `server.address`, `server.port`, `http.response.status_code`, `error.type`, `fault.code`, `system.config`, `system.name.simple`, `system.name.canonical` |

Тег `rpc.system` равен `soap`; в `fault.code` попадает код ошибки `SOAP`, и он пуст, если вызов не вернул fault.

Подробнее смотрите в документации модуля [SOAP-клиент](soap-client.md).

### Планировщик { #scheduling }

| Метрика | Prometheus | Тип | Описание | Теги |
|--------|------------|------|-------------|------|
| `scheduling.job.duration` | `scheduling_job_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | Длительность выполнения запланированной задачи | `code.function.name`, `system.name.simple`, `system.name.canonical`, `error.type`, а также `system.config`, если у задачи объявлен путь конфигурации |

Подробнее смотрите в документации модуля [Планировщик](scheduling.md).

### Кэш { #cache }

Распределенные кэши `Redis` сообщают собственные метрики операций:

| Метрика | Prometheus | Тип | Описание | Теги |
|--------|------------|------|-------------|------|
| `cache.operation.duration` | `cache_operation_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | Длительность операции с кэшем (`GET`, `PUT`, `INVALIDATE` и другие) | `origin`, `operation`, `error.type`, `system.config`, `system.name.simple`, `system.name.canonical` |
| `cache.ratio` | `cache_ratio_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Счетчик попаданий/промахов кэша | `origin`, `operation`, `type`, `system.config`, `system.name.simple`, `system.name.canonical` |

Тег `origin` равен `redis`, `operation` — имя операции контракта `Cache`, а `type` у `cache.ratio` принимает значения `hit` или `miss`.

Кэши `Caffeine` не сообщают `cache.operation.duration` и `cache.ratio` — их телеметрия делегирует стандартным биндерам кэша `Micrometer`,
которые привязываются к нижележащему кэшу при `telemetry.metrics.enabled = true`:

| Метрика | Prometheus | Тип | Описание | Теги |
|--------|------------|------|-------------|------|
| `cache.gets` | `cache_gets_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество обращений к кэшу | `cache`, `result` (`hit` / `miss`) |
| `cache.puts` | `cache_puts_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество записей в кэш | `cache` |
| `cache.evictions` | `cache_evictions_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество вытесненных записей | `cache` |
| `cache.eviction.weight` | `cache_eviction_weight_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Суммарный вес вытесненных записей | `cache` |
| `cache.loads` | `cache_loads_seconds` / `_count` / `_sum` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | Длительность загрузки значения в кэш | `cache`, `result` (`success` / `failure`) |
| `cache.size` | `cache_size` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Текущий размер кэша | `cache` |

Все метрики `Caffeine` несут тег `cache` с именем кэша плюс теги из `telemetry.metrics.tags`.

Подробнее смотрите в документации модуля [Кэш](cache.md).

### Redis / Lettuce { #redis-lettuce }

| Метрика | Prometheus | Тип | Описание | Теги |
|--------|------------|------|-------------|------|
| `lettuce.command.completion.duration` | `lettuce_command_completion_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | Длительность завершения команды Redis | `type`, `remote`, `command`, `error.type` |
| `lettuce.command.firstresponse.duration` | `lettuce_command_firstresponse_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | Длительность первого ответа на команду Redis | `type`, `remote`, `command`, `error.type` |

Тег `type` различает вид клиента, `remote` — адрес узла `Redis`, `command` — имя команды `Redis`.
У этих двух метрик `error.type` содержит текст ошибки `Redis`, а не имя класса исключения.

### Отказоустойчивость { #resilience }

| Метрика | Prometheus | Тип | Описание | Теги |
|--------|------------|------|-------------|------|
| `resilient.circuitbreaker.state` | `resilient_circuitbreaker_state` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Состояние предохранителя (0=CLOSED, 1=HALF_OPEN, 2=OPEN) | `name` |
| `resilient.circuitbreaker.transition` | `resilient_circuitbreaker_transition_operations_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Переходы в состояния `OPEN` и `HALF_OPEN` | `name`, `state` |
| `resilient.circuitbreaker.call.acquire` | `resilient_circuitbreaker_call_acquire_operations_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Вызовы, пропущенные в `HALF_OPEN`, и вызовы, отклоненные в `OPEN` | `name`, `state`, `status` |
| `resilient.circuitbreaker.call.result` | `resilient_circuitbreaker_call_result_operations_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Результаты вызовов, зарегистрированные предохранителем | `name`, `state`, `status` |
| `resilient.retry.attempts` | `resilient_retry_attempts_operations_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество повторных попыток | `name` |
| `resilient.retry.exhausted` | `resilient_retry_exhausted_operations_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество исчерпанных повторов | `name`, `reason` |
| `resilient.timeout.exhausted` | `resilient_timeout_exhausted_operations_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество таймаутов | `name` |
| `resilient.fallback.attempts` | `resilient_fallback_attempts_operations_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество вызовов резервного варианта | `name`, `type` |
| `resilient.ratelimiter.acquire` | `resilient_ratelimiter_acquire_operations_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Захваты разрешений ограничителем частоты | `name`, `status` |

Значения тегов: `status` равен `PERMITTED` / `REJECTED` / `DISABLED` у `call.acquire` и `SUCCESS` / `FAILURE` / `IGNORED_FAILURE` / `FALLBACK` у `call.result`;
`reason` равен `EXHAUSTED_ATTEMPTS` или `EXHAUSTED_BUDGET`; `status` ограничителя частоты — `acquired` или `rejected`; `type` резервного варианта — `executed`.

Подробнее смотрите в документации модуля [Отказоустойчивость](resilient.md).

### JMS { #jms }

| Метрика | Prometheus | Тип | Описание | Теги |
|--------|------------|------|-------------|------|
| `messaging.receive.duration` | `messaging_receive_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | Длительность получения сообщения JMS | `messaging.system`, `messaging.destination.name`, `error.type` |

Тег `messaging.system` всегда равен `jms`.

### S3-клиент { #s3-client }

| Метрика | Prometheus | Тип | Описание | Теги |
|--------|------------|------|-------------|------|
| `rpc.client.duration` | `rpc_client_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | Длительность операции S3-клиента | `rpc.system`, `rpc.method`, `aws.s3.bucket`, `error.type`, `system.path`, `system.name.simple`, `system.name.canonical` |

Тег `rpc.system` равен `s3-aws` для клиента на базе `AWS`. `rpc.method` — имя операции S3, а `system.path` — путь конфигурации клиента.

Подробнее смотрите в документации модуля [S3-клиент](s3-client.md).

### Camunda 7 BPMN { #camunda-7-bpmn }

| Метрика | Prometheus | Тип | Описание | Теги |
|--------|------------|------|-------------|------|
| `camunda.engine.delegate.duration` | `camunda_engine_delegate_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | Длительность выполнения Java-делегата Camunda BPMN | `delegate`, `error.type` |

Собственные метрики движка публикуются отдельно и требуют `camunda.engine.bpmn.telemetry.metrics.engineMetrics = true`.

Подробнее смотрите в документации модуля [Camunda 7 BPMN](camunda7-bpmn.md).

### Camunda REST { #camunda-rest }

| Метрика | Prometheus | Тип | Описание | Теги |
|--------|------------|------|-------------|------|
| `camunda.rest.request.duration` | `camunda_rest_request_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | Длительность запроса `Camunda REST` | `http.request.method`, `http.response.status_code`, `http.route`, `url.scheme`, `server.address`, `http.response.result_code`, `error.type` |
| `camunda.rest.active_requests` | `camunda_rest_active_requests` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Количество активных запросов Camunda REST | `http.request.method`, `http.route`, `url.scheme`, `server.address` |

Подробнее смотрите в документации модуля [Camunda 7 REST](camunda7-rest.md).

### Camunda 8 worker { #camunda-8-worker }

| Метрика | Prometheus | Тип | Описание | Теги |
|--------|------------|------|-------------|------|
| `zeebe.worker.handler.duration` | `zeebe_worker_handler_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | Длительность обработчика задачи `Zeebe Worker` | `job.name`, `job.type`, `error.type` |

Клиент `Camunda` дополнительно публикует в тот же реестр собственные метрики задач воркера с тегом `type` задачи.

Подробнее смотрите в документации модуля [Camunda 8 Worker](camunda8-worker.md).

### Система { #system }

| Метрика | Prometheus | Тип | Описание | Теги |
|--------|------------|------|-------------|------|
| `kora.up` | `kora_up` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Индикатор состояния фреймворка (значение = 1) | `version` |

### JVM { #jvm }

Стандартные метрики `JVM` и процесса собираются автоматически биндерами [Micrometer](https://docs.micrometer.io/micrometer/reference/concepts.html), привязанными к реестру при старте.
Они не зависят от настройки `telemetry.metrics.enabled` какого-либо модуля:

| Метрика | Prometheus | Тип | Описание | Теги |
|--------|------------|------|-------------|------|
| `jvm.memory.used` | `jvm_memory_used_bytes` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Используемая память | `area`, `id` |
| `jvm.memory.committed` | `jvm_memory_committed_bytes` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Зарезервированная память JVM | `area`, `id` |
| `jvm.memory.max` | `jvm_memory_max_bytes` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Максимально доступная память | `area`, `id` |
| `jvm.buffer.count` | `jvm_buffer_count_buffers` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Количество буферов в пуле | `id` |
| `jvm.buffer.memory.used` | `jvm_buffer_memory_used_bytes` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Память, используемая буферами | `id` |
| `jvm.buffer.total.capacity` | `jvm_buffer_total_capacity_bytes` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Суммарная емкость пула буферов | `id` |
| `jvm.gc.pause` | `jvm_gc_pause_seconds` / `_count` / `_sum` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | Длительность паузы GC | `gc`, `action`, `cause` |
| `jvm.gc.concurrent.phase.time` | `jvm_gc_concurrent_phase_time_seconds` / `_count` / `_sum` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | Длительность конкурентной фазы GC | `gc`, `action`, `cause` |
| `jvm.gc.memory.allocated` | `jvm_gc_memory_allocated_bytes_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Размер выделенной памяти | — |
| `jvm.gc.memory.promoted` | `jvm_gc_memory_promoted_bytes_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Память, повышенная в старое поколение (только для поколенческих сборщиков) | — |
| `jvm.gc.max.data.size` | `jvm_gc_max_data_size_bytes` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Максимальный размер старого поколения | — |
| `jvm.gc.live.data.size` | `jvm_gc_live_data_size_bytes` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Размер старого поколения после полной сборки GC | — |
| `jvm.threads.live` | `jvm_threads_live_threads` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Количество живых потоков | — |
| `jvm.threads.daemon` | `jvm_threads_daemon_threads` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Количество потоков-демонов | — |
| `jvm.threads.peak` | `jvm_threads_peak_threads` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Пиковое количество потоков | — |
| `jvm.threads.started` | `jvm_threads_started_threads_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество запущенных потоков | — |
| `jvm.threads.states` | `jvm_threads_states_threads` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Количество потоков по состоянию | `state` |
| `jvm.classes.loaded` | `jvm_classes_loaded_classes` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Количество загруженных в данный момент классов | — |
| `jvm.classes.loaded.count` | `jvm_classes_loaded_count_classes_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество классов, загруженных с момента старта | — |
| `jvm.classes.unloaded` | `jvm_classes_unloaded_classes_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество выгруженных классов | — |
| `process.cpu.usage` | `process_cpu_usage` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Использование CPU процессом | — |
| `system.cpu.usage` | `system_cpu_usage` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Использование CPU системой | — |
| `system.cpu.count` | `system_cpu_count` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Количество доступных процессоров | — |
| `system.load.average.1m` | `system_load_average_1m` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Средняя загрузка системы за одну минуту | — |
| `process.files.open` | `process_files_open_files` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Количество открытых файловых дескрипторов | — |
| `process.files.max` | `process_files_max_files` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Максимальное количество файловых дескрипторов | — |
| `process.uptime` | `process_uptime_seconds` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Время работы процесса | — |
| `process.start.time` | `process_start_time_seconds` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Время старта процесса от начала эпохи Unix | — |

Часть из них регистрируется только тогда, когда запущенная `JVM` и операционная система предоставляют соответствующее значение `MXBean`, поэтому точный набор серий в одном опросе зависит от платформы.
