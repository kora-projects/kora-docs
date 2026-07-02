---
description: "Explains Kora metrics with Micrometer, Prometheus export, OpenTelemetry metric standards, registry customization, and module-specific metric references. Use when working with MetricsModule, Micrometer, PrometheusMeterRegistry, MetricsConfig, PrometheusMeterRegistryInitializer, OpenTelemetry, Metrics Reference."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora metrics with Micrometer, Prometheus export, OpenTelemetry metric standards, registry customization, and module-specific metric references; key triggers include MetricsModule, Micrometer, PrometheusMeterRegistry, MetricsConfig, PrometheusMeterRegistryInitializer, OpenTelemetry, Metrics Reference."
---

Модуль для сбора метрик приложения с помощью [Micrometer](https://micrometer.io/docs/concepts#_purpose).
Он создает `PrometheusMeterRegistry`, подключает к нему метрики компонентов Kora и отдает результат в формате `Prometheus` через приватный `HTTP`-сервер.
Это позволяет собирать метрики приложения, `JVM`, процесса и встроенных интеграций в одном месте и опрашивать их внешней системой наблюдаемости.

Для публикации метрик требуется [приватный HTTP-сервер](http-server.md), который отдает их в формате [Prometheus](https://prometheus.io/docs/concepts/data_model/).

Для пошагового разбора перед справочным описанием смотрите [Наблюдаемость](../guides/observability.md).

## Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:micrometer-module"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends MetricsModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:micrometer-module")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : MetricsModule
    ```

## Конфигурация { #configuration }

Пример конфигурации пути приватного `HTTP`-сервера для получения метрик, описанной в классе `HttpServerConfig` (указаны значения по умолчанию):

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
        privateApiHttpMetricsPath = "/metrics" //(1)!
    }
    ```

    1. Путь для получения метрик в формате `Prometheus` (по умолчанию: `"/metrics"`).

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      privateApiHttpMetricsPath: "/metrics" #(1)!
    ```

    1. Путь для получения метрик в формате `Prometheus` (по умолчанию: `"/metrics"`).

Пример полной конфигурации, описанной в классе `MetricsConfig` (указаны значения по умолчанию):

===! ":material-code-json: `Hocon`"

    ```javascript
    metrics {
        opentelemetrySpec = "V120" //(1)!
    }
    ```

    1. Формат метрик согласно стандарту `OpenTelemetry` (доступные значения: [V120](https://opentelemetry.io/docs/specs/semconv/http/migration-guide/#migrating-from-a-version-prior-to-v1200) / [V123](https://opentelemetry.io/docs/specs/semconv/http/migration-guide/), по умолчанию: `V120`).

=== ":simple-yaml: `YAML`"

    ```yaml
    metrics:
      opentelemetrySpec: "V120" #(1)!
    ```

    1. Формат метрик согласно стандарту `OpenTelemetry` (доступные значения: [V120](https://opentelemetry.io/docs/specs/semconv/http/migration-guide/#migrating-from-a-version-prior-to-v1200) / [V123](https://opentelemetry.io/docs/specs/semconv/http/migration-guide/), по умолчанию: `V120`).

### Метрики модуля { #module-metrics }

Блок `metrics` выше настраивает реестр глобально. Каждый модуль, собирающий метрики, дополнительно предоставляет собственный
блок `telemetry.metrics`, описанный в `TelemetryConfig.MetricsConfig`, который позволяет включать и отключать метрики, настраивать корзины гистограммы
и добавлять дополнительные теги только для этого модуля. В примере ниже в качестве носителя используется модуль [HTTP-сервер](http-server.md), но
те же поля `telemetry.metrics` применяются дословно к [HTTP-клиенту](http-client.md), [Базе данных](database-common.md),
[Kafka](kafka.md), [gRPC-серверу](grpc-server.md), [gRPC-клиенту](grpc-client.md), [Планировщику](scheduling.md),
[Кэшу](cache.md) и любой другой интеграции, которая сообщает метрики:

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
        telemetry {
            metrics {
                enabled = true //(1)!
                slo = [1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000] //(2)!
                tags { //(3)!
                    "key1" = "value1"
                    "key2" = "value2"
                }
            }
        }
    }
    ```

    1.  Включает сбор метрик для модуля (по умолчанию: `true`)
    2.  Корзины гистограммы [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) для метрик `DistributionSummary`/`Timer` (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO` в миллисекундах для `V120` / `#DEFAULT_SLO_V123` в секундах для `V123`)
    3.  Дополнительные общие теги, добавляемые к каждой метрике, которую сообщает модуль (по умолчанию: `{}`)

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      telemetry:
        metrics:
          enabled: true #(1)!
          slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(2)!
          tags: #(3)!
            key1: value1
            key2: value2
    ```

    1.  Включает сбор метрик для модуля (по умолчанию: `true`)
    2.  Корзины гистограммы [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) для метрик `DistributionSummary`/`Timer` (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO` в миллисекундах для `V120` / `#DEFAULT_SLO_V123` в секундах для `V123`)
    3.  Дополнительные общие теги, добавляемые к каждой метрике, которую сообщает модуль (по умолчанию: `{}`)

Установка `enabled = false` полностью отключает создание метрик для этого модуля (`MetricsFactory` модуля не возвращает
метрик), что является рекомендованным способом заглушить шумную интеграцию. Значения корзин `slo` по умолчанию для каждого стандарта
перечислены в разделе [Персонализация](#personalization).

Параметры конфигурации сбора метрик также описаны в модулях, которые собирают метрики: [HTTP-сервер](http-server.md), [HTTP-клиент](http-client.md), [gRPC-сервер](grpc-server.md), [gRPC-клиент](grpc-client.md), [Планировщик](scheduling.md), [Кэш](cache.md) и другие интеграции.

## Использование { #usage }

Kora следует нотации, описанной в [спецификации `Prometheus`](https://prometheus.io/docs/concepts/data_model/).

После подключения модуля `PrometheusMeterRegistry` регистрируется в `Metrics.globalRegistry` и используется всеми компонентами, которые собирают метрики.
При остановке приложения этот реестр удаляется из `Metrics.globalRegistry` и закрывается.

Компонент `PrometheusMeterRegistryWrapper` является `Root`-компонентом и реализует `Wrapped<PrometheusMeterRegistry>`, поэтому пользовательский код может внедрять как обобщенный `MeterRegistry`, так и конкретный `PrometheusMeterRegistry`:

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

Реестр автоматически получает стандартные привязки `Micrometer`: `ClassLoaderMetrics`, `JvmMemoryMetrics`, `JvmGcMetrics`, `JvmThreadMetrics`, `ProcessorMetrics`, `FileDescriptorMetrics`, `UptimeMetrics`.
Kora также регистрирует метрику `kora.up` со значением `1` и тегом `version`.

Kora дополнительно связывает реестр `Micrometer` с `MeterProvider` из `OpenTelemetry` (`MicrometerMeterProvider` из `io.opentelemetry.contrib.metrics.micrometer`), поэтому библиотеки, инструментированные с помощью API метрик `OpenTelemetry`, публикуют данные через тот же `PrometheusMeterRegistry`.

Готовый к запуску базовый пример, который связывает `MetricsModule` вместе с `HoconConfigModule`, `LogbackModule`, `UndertowHttpServerModule` и экспортером `OpenTelemetry`, доступен в примере [kora-java-telemetry](https://github.com/kora-projects/kora-examples/tree/master/examples/java/kora-java-telemetry).

### Экспорт в Prometheus { #prometheus-export }

Метрики отдаются в текстовом формате [Prometheus](https://prometheus.io/docs/concepts/data_model/) [приватным HTTP-сервером](http-server.md) по пути `privateApiHttpMetricsPath` (по умолчанию `/metrics`), обслуживаемому на порту `privateApiHttpPort`.
У приватного сервера должен быть настроен порт, чтобы эндпоинт был доступен.
При примерной конфигурации (`privateApiHttpPort = 8085`) текущий снимок метрик можно получить так:

```shell
curl http://localhost:8085/metrics
```

Направьте цель опроса вашего `Prometheus` (или любого совместимого сборщика) на тот же хост, порт и путь.

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
        fun commonTagsInit(): PrometheusMeterRegistryInitializer? {
            return PrometheusMeterRegistryInitializer {
                it.config().commonTags("tag", "value")
                it
            }
        }
    }
    ```

У стандартных метрик также есть собственные настройки, например корзины гистограммы `slo` для метрик `DistributionSummary`/`Timer`, настраиваемые для каждого модуля в блоке [`telemetry.metrics`](#module-metrics).
Когда `slo` не переопределено, значения по умолчанию зависят от выбранного стандарта `OpenTelemetry`:

- `V120` — `DEFAULT_SLO` в **миллисекундах**: `1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000`
- `V123` — `DEFAULT_SLO_V123` в **секундах**: `0.001, 0.010, 0.050, 0.100, 0.200, 0.500, 1, 2, 5, 10, 20, 30, 60, 90`

Оба массива объявлены в `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig`; имена полей глобального реестра находятся в `ru.tinkoff.kora.micrometer.module.MetricsConfig`.

### Поставщики тегов { #tag-providers }

Набор тегов, прикрепляемых к метрикам фреймворка, формируется поставщиками тегов для каждого модуля, зарегистрированными как `@DefaultComponent`.
Чтобы изменить, какие теги выдаются для конкретной интеграции, предоставьте собственную реализацию соответствующего интерфейса в качестве переопределения `@DefaultComponent`:

- `MicrometerHttpServerTagsProvider` (пакет `ru.tinkoff.kora.micrometer.module.http.server.tag`) — метрики HTTP-сервера
- `MicrometerHttpClientTagsProvider` (пакет `ru.tinkoff.kora.micrometer.module.http.client.tag`) — метрики HTTP-клиента
- `MicrometerGrpcServerTagsProvider` / `MicrometerGrpcClientTagsProvider` (пакеты `...grpc.server.tag` / `...grpc.client.tag`) — метрики gRPC
- `MicrometerKafkaConsumerTagsProvider` / `MicrometerKafkaProducerTagsProvider` (пакеты `...kafka.consumer.tag` / `...kafka.producer.tag`) — метрики Kafka

Поставщик по умолчанию выбирается по значению `metrics.opentelemetrySpec`, поэтому переопределение заменяет сопоставление тегов для обоих стандартов.

## Стандарт { #standard }

Изначально формат метрик использовал стандарт `V120` из `OpenTelemetry`; начиная с Kora `1.1.0` метрики также могут предоставляться
в стандарте `V123` из `OpenTelemetry`. Частичный список изменений доступен в [документации OpenTelemetry](https://opentelemetry.io/blog/2023/http-conventions-declared-stable/)
и в [руководстве по миграции OpenTelemetry](https://opentelemetry.io/docs/specs/semconv/http/migration-guide/).

Параметр `metrics.opentelemetrySpec` влияет на некоторые имена метрик, единицы измерения и наборы тегов.
Справочник ниже перечисляет варианты как `V120`, так и `V123` для таких метрик; если вариант не указан, имя одинаково для обоих стандартов.

## Справочник метрик { #metrics-reference }

Все метрики Kora используют [семантические соглашения OpenTelemetry](https://opentelemetry.io/docs/specs/semconv/) для именования и тегов.

Используемые типы метрик [Micrometer](https://docs.micrometer.io/micrometer/reference/concepts.html):

- [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) — используется для сбора распределений произвольных значений.
Этот тип метрики обеспечивает эффективную визуализацию данных по корзинам и вычисление процентилей.
- [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) — монотонно возрастающий счетчик
- [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) — текущее значение метрики
- [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) — длительность операции с поддержкой count, sum, max и корзин

### HTTP-сервер { #http-server }

| Метрика | Prometheus | Тип | Описание | Теги |
|--------|------------|------|-------------|------|
| `http.server.duration` (`V120`), `http.server.request.duration` (`V123`) | `http_server_duration_milliseconds` (`V120`) / `http_server_request_duration_seconds` (`V123`) / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность обработки запроса `HTTP`-сервером | `V120`: `http.request.method`, `http.response.status_code`, `http.route`, `server.address`, `url.scheme`, `http.target`, `http.method`, `http.status_code`; `V123`: `http.request.method`, `http.response.status_code`, `http.route`, `url.scheme`, `server.address`, `error.type` |
| `http.server.active_requests` | `http_server_active_requests` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Количество активных `HTTP`-запросов | `V120`: `http.route`, `http.request.method`, `server.address`, `url.scheme`, `http.target`, `http.method`; `V123`: `http.route`, `http.request.method`, `server.address`, `url.scheme` |

Подробнее смотрите в документации модуля [HTTP-сервер](http-server.md).

### HTTP-клиент { #http-client }

| Метрика | Prometheus | Тип | Описание | Теги |
|--------|------------|------|-------------|------|
| `http.client.duration` (`V120`), `http.client.request.duration` (`V123`) | `http_client_duration_milliseconds` (`V120`) / `http_client_request_duration_seconds` (`V123`) / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность запроса `HTTP`-клиента | `V120`: `http.request.method`, `http.response.status_code`, `server.address`, `url.scheme`, `http.route`, `http.status_code`, `http.method`, `http.target`, `error.type`; `V123`: `http.request.method`, `http.response.status_code`, `server.address`, `url.scheme`, `http.route`, `http.status_code`, `error.type` |

Подробнее смотрите в документации модуля [HTTP-клиент](http-client.md).

### База данных { #database }

| Метрика | Prometheus | Тип | Описание | Теги |
|--------|------------|------|-------------|------|
| `database.client.request.duration` (`V120`), `db.client.request.duration` (`V123`) | `database_client_request_duration_milliseconds` (`V120`) / `db_client_request_duration_seconds` (`V123`) / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность операции/запроса к базе данных | `V120`: `pool`, `query.id`, `query.operation`, `error`; `V123`: `db.pool.name`, `db.statement`, `db.operation`, `error.type` |

Подробнее смотрите в документации модуля [База данных](database-common.md).

### Kafka { #kafka }

| Метрика | Prometheus | Тип | Описание | Теги |
|--------|------------|------|-------------|------|
| `messaging.receive.duration` | `messaging_receive_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность обработки одного сообщения | `messaging.system`, `messaging.destination`, `messaging.operation`, `error.type` |
| `messaging.publish.duration` | `messaging_publish_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность отправки сообщения | `messaging.system`, `messaging.destination`, `messaging.partition_id`, `error.type` |
| `messaging.process.batch.duration` | `messaging_process_batch_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность обработки пакета сообщений | `messaging.system`, `messaging.destination`, `error.type` |
| `messaging.kafka.consumer.lag` | `messaging_kafka_consumer_lag` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Отставание потребителя по разделу | `messaging.system`, `messaging.destination`, `messaging.partition_id`, `messaging.consumer_group` |

Подробнее смотрите в документации модуля [Kafka](kafka.md).

### gRPC-сервер { #grpc-server }

| Метрика | Prometheus | Тип | Описание | Теги |
|--------|------------|------|-------------|------|
| `rpc.server.duration` | `rpc_server_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность обработки вызова gRPC-сервером | `rpc.service`, `rpc.method`, `rpc.status`, `error.type` |
| `rpc.server.requests_per_rpc` | `rpc_server_requests_per_rpc_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество запросов, полученных за один RPC | `rpc.service`, `rpc.method` |
| `rpc.server.responses_per_rpc` | `rpc_server_responses_per_rpc_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество ответов, отправленных за один RPC | `rpc.service`, `rpc.method` |

Подробнее смотрите в документации модуля [gRPC-сервер](grpc-server.md).

### gRPC-клиент { #grpc-client }

| Метрика | Prometheus | Тип | Описание | Теги |
|--------|------------|------|-------------|------|
| `rpc.client.duration` | `rpc_client_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность вызова gRPC-клиента | `rpc.service`, `rpc.method`, `rpc.status`, `error.type`, `server.address` |
| `rpc.client.requests_per_rpc` | `rpc_client_requests_per_rpc_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество запросов, отправленных за один RPC | `rpc.service`, `rpc.method`, `server.address` |
| `rpc.client.responses_per_rpc` | `rpc_client_responses_per_rpc_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество ответов, полученных за один RPC | `rpc.service`, `rpc.method`, `server.address` |

Подробнее смотрите в документации модуля [gRPC-клиент](grpc-client.md).

### SOAP-клиент { #soap-client }

| Метрика | Prometheus | Тип | Описание | Теги |
|--------|------------|------|-------------|------|
| `rpc.client.duration` | `rpc_client_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность вызова SOAP-клиента | `rpc.system`, `rpc.service`, `rpc.method`, `rpc.result`, `server.address`, `server.port` |

Подробнее смотрите в документации модуля [SOAP-клиент](soap-client.md).

### Планировщик { #scheduling }

| Метрика | Prometheus | Тип | Описание | Теги |
|--------|------------|------|-------------|------|
| `scheduling.job.duration` | `scheduling_job_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность выполнения запланированной задачи | `code.class`, `code.function`, `error.type` |

Подробнее смотрите в документации модуля [Планировщик](scheduling.md).

### Кэш { #cache }

| Метрика | Prometheus | Тип | Описание | Теги |
|--------|------------|------|-------------|------|
| `cache.duration` | `cache_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | Длительность операции с кэшем (`GET`, `SET`, `DELETE` и другие) | `cache`, `operation`, `origin`, `status` |
| `cache.ratio` | `cache_ratio_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Счетчик попаданий/промахов кэша | `cache`, `origin`, `type` |
| `cache.hit`, `cache.miss` | `cache_hit_total`, `cache_miss_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Устаревшие счетчики попаданий/промахов, сохраненные для совместимости | `cache`, `origin` |

Стандартные метрики `Micrometer` регистрируются автоматически при использовании `Caffeine`:

| Метрика | Prometheus | Тип | Описание |
|--------|------------|------|-------------|
| `cache.gets` | `cache_gets_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество обращений к кэшу |
| `cache.puts` | `cache_puts_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество записей в кэш |
| `cache.evictions` | `cache_evictions_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество вытеснений из кэша |
| `cache.size` | `cache_size` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Текущий размер кэша |

Подробнее смотрите в документации модуля [Кэш](cache.md).

### Redis / Lettuce { #redis-lettuce }

| Метрика | Prometheus | Тип | Описание | Теги |
|--------|------------|------|-------------|------|
| `lettuce.command.completion.duration` | `lettuce_command_completion_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность завершения команды Redis | `type`, `remote`, `local`, `command`, `error.type` |
| `lettuce.command.firstresponse.duration` | `lettuce_command_firstresponse_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность первого ответа на команду Redis | `type`, `remote`, `local`, `command`, `error.type` |

### Отказоустойчивость { #resilience }

| Метрика | Prometheus | Тип | Описание | Теги |
|--------|------------|------|-------------|------|
| `resilient.circuitbreaker.state` | `resilient_circuitbreaker_state` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Состояние предохранителя (0=CLOSED, 1=HALF_OPEN, 2=OPEN) | `name` |
| `resilient.circuitbreaker.transition` | `resilient_circuitbreaker_transition_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Переходы состояний предохранителя | `name`, `state` |
| `resilient.circuitbreaker.call.acquire` | `resilient_circuitbreaker_call_acquire_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Попытки/отклонения захвата вызова предохранителем | `name`, `state`, `status` |
| `resilient.retry.attempts` | `resilient_retry_attempts_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество повторных попыток | `name` |
| `resilient.retry.exhausted` | `resilient_retry_exhausted_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество исчерпанных повторов | `name` |
| `resilient.timeout.exhausted` | `resilient_timeout_exhausted_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество таймаутов | `name` |
| `resilient.fallback.attempts` | `resilient_fallback_attempts_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество вызовов резервного варианта | `name`, `type` |

Подробнее смотрите в документации модуля [Отказоустойчивость](resilient.md).

### JMS { #jms }

| Метрика | Prometheus | Тип | Описание | Теги |
|--------|------------|------|-------------|------|
| `messaging.receive.duration` | `messaging_receive_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность получения сообщения JMS | `messaging.system`, `messaging.destination.name`, `error.type` |

### S3-клиент { #s3-client }

| Метрика | Prometheus | Тип | Описание | Теги |
|--------|------------|------|-------------|------|
| `s3.client.duration` | `s3_client_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность HTTP-запроса к S3 | `aws.s3.bucket`, `aws.operation.name`, `error.type` |
| `s3.kora.client.duration` | `s3_kora_client_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность операции S3-клиента Kora | `aws.client.name`, `aws.s3.bucket`, `aws.operation.name`, `error.type` |

Подробнее смотрите в документации модуля [S3-клиент](s3-client.md).

### Camunda 7 BPMN { #camunda-7-bpmn }

| Метрика | Prometheus | Тип | Описание | Теги |
|--------|------------|------|-------------|------|
| `camunda.engine.delegate.duration` | `camunda_engine_delegate_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность выполнения Java-делегата Camunda BPMN | `delegate`, `business.key`, `error.type` |
| `camunda.engine.delegate.active_requests` | `camunda_engine_delegate_active_requests` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Количество активных выполнений делегата | `delegate`, `business.key` |

Подробнее смотрите в документации модуля [Camunda 7 BPMN](camunda7-bpmn.md).

### Camunda REST { #camunda-rest }

| Метрика | Prometheus | Тип | Описание | Теги |
|--------|------------|------|-------------|------|
| `camunda.rest.server.duration` (`V120`), `camunda.rest.server.request.duration` (`V123`) | `camunda_rest_server_duration_milliseconds` (`V120`) / `camunda_rest_server_request_duration_seconds` (`V123`) / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность запроса `Camunda REST` | `V120`: `http.request.method`, `http.response.status_code`, `http.route`, `server.address`, `url.scheme`, `http.target`, `http.method`, `http.status_code`; `V123`: `http.request.method`, `http.response.status_code`, `http.route`, `url.scheme`, `server.address`, `error.type` |
| `camunda.rest.server.active_requests` | `camunda_rest_server_active_requests` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Количество активных запросов Camunda REST | `http.route`, `http.request.method`, `server.address`, `url.scheme` |

Подробнее смотрите в документации модуля [Camunda 7 REST](camunda7-rest.md).

### Camunda 8 Worker { #camunda-8-worker }

| Метрика | Prometheus | Тип | Описание | Теги |
|--------|------------|------|-------------|------|
| `zeebe.worker.handler` (`V120`), `zeebe.worker.handler.duration` (`V123`) | `zeebe_worker_handler_seconds` (`V120`) / `zeebe_worker_handler_duration_seconds` (`V123`) / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность обработчика задачи `Zeebe Worker` | `job.name`, `job.type`, `status`, `error`, `error.code` |
| `zeebe.worker.handler` | `zeebe_worker_handler_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Счетчик ошибок `Zeebe Worker` | `job.name`, `job.type`, `status`, `error.code` |
| `zeebe.client.worker.job` | `zeebe_client_worker_job_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество активированных и обработанных задач `Zeebe` | `action`, `type` |

Подробнее смотрите в документации модуля [Camunda 8 Worker](camunda8-worker.md).

### Система { #system }

| Метрика | Prometheus | Тип | Описание | Теги |
|--------|------------|------|-------------|------|
| `kora.up` | `kora_up` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Индикатор состояния фреймворка (значение = 1) | `version` |

### JVM { #jvm }

Стандартные метрики JVM собираются автоматически через [Micrometer](https://docs.micrometer.io/micrometer/reference/concepts.html):

| Метрика | Prometheus | Тип | Описание | Теги |
|--------|------------|------|-------------|------|
| `jvm.gc.pause` | `jvm_gc_pause_milliseconds` / `_count` / `_sum` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность паузы GC | `action`, `cause` |
| `jvm.gc.memory.allocated` | `jvm_gc_memory_allocated_bytes_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Размер выделенной памяти | — |
| `jvm.gc.memory.promoted` | `jvm_gc_memory_promoted_bytes_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Память, повышенная в старое поколение | — |
| `jvm.gc.max.data.size` | `jvm_gc_max_data_size_bytes` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Максимальный размер старого поколения | — |
| `jvm.gc.live.data.size` | `jvm_gc_live_data_size_bytes` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Размер старого поколения после полной сборки GC | — |
| `jvm.memory.used` | `jvm_memory_used_bytes` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Используемая память | `area`, `id` |
| `jvm.memory.committed` | `jvm_memory_committed_bytes` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Зарезервированная память JVM | `area`, `id` |
| `jvm.memory.max` | `jvm_memory_max_bytes` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Максимально доступная память | `area`, `id` |
| `jvm.threads.live` | `jvm_threads_live_threads` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Количество живых потоков | — |
| `jvm.threads.daemon` | `jvm_threads_daemon_threads` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Количество потоков-демонов | — |
| `jvm.threads.peak` | `jvm_threads_peak_threads` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Пиковое количество потоков | — |
| `jvm.threads.states` | `jvm_threads_states_threads` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Количество потоков по состоянию | `state` |
| `process.cpu.usage` | `process_cpu_usage` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Использование CPU процессом | — |
| `system.cpu.usage` | `system_cpu_usage` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Использование CPU системой | — |
| `system.cpu.count` | `system_cpu_count` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Количество доступных процессоров | — |
| `logback.events` | `logback_events_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество событий логирования | `level` |
| `jvm.classes.loaded` | `jvm_classes_loaded_classes` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Количество загруженных классов | — |
| `jvm.classes.unloaded` | `jvm_classes_unloaded_classes_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество выгруженных классов | — |
| `process.files.open` | `process_files_open_files` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Количество открытых файловых дескрипторов | — |
| `process.files.max` | `process_files_max_files` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Максимальное количество файловых дескрипторов | — |
| `process.uptime` | `process_uptime_milliseconds` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Время работы процесса | — |
