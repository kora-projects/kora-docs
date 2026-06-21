---
description: "Explains Kora metrics with Micrometer, Prometheus export, OpenTelemetry metric standards, registry customization, and module-specific metric references. Use when working with MetricsModule, Micrometer, PrometheusMeterRegistry, MetricsConfig, PrometheusMeterRegistryInitializer, OpenTelemetry, Metrics Reference."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora metrics with Micrometer, Prometheus export, OpenTelemetry metric standards, registry customization, and module-specific metric references; key triggers include MetricsModule, Micrometer, PrometheusMeterRegistry, MetricsConfig, PrometheusMeterRegistryInitializer, OpenTelemetry, Metrics Reference."
---

Модуль для сбора метрик приложения с использованием [Micrometer](https://micrometer.io/docs/concepts#_purpose).
Он создает `PrometheusMeterRegistry`, подключает к нему метрики компонентов Kora и отдает результат в формате `Prometheus` через служебный `HTTP`-сервер.
Такой подход позволяет собирать метрики приложения, `JVM`, процесса и встроенных интеграций единым способом, а затем забирать их внешней системой наблюдаемости.

Для публикации метрик требуется подключение [служебного HTTP-сервера](http-server.md), который предоставляет их в формате [Prometheus](https://prometheus.io/docs/concepts/data_model/).

Если нужен пошаговый разбор перед справочным описанием, смотрите [Наблюдаемость](../guides/observability.md).

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

Пример конфигурации пути служебного `HTTP`-сервера для получения метрик, описанной в классе `HttpServerConfig` (указаны значения по умолчанию):

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

    1. Формат метрик по стандарту `OpenTelemetry` (доступные значения: [V120](https://opentelemetry.io/docs/specs/semconv/http/migration-guide/#migrating-from-a-version-prior-to-v1200) / [V123](https://opentelemetry.io/docs/specs/semconv/http/migration-guide/), по умолчанию: `V120`).

=== ":simple-yaml: `YAML`"

    ```yaml
    metrics:
      opentelemetrySpec: "V120" #(1)!
    ```

    1. Формат метрик по стандарту `OpenTelemetry` (доступные значения: [V120](https://opentelemetry.io/docs/specs/semconv/http/migration-guide/#migrating-from-a-version-prior-to-v1200) / [V123](https://opentelemetry.io/docs/specs/semconv/http/migration-guide/), по умолчанию: `V120`).

Параметры конфигурации сбора метрик описываются в модулях, где присутствует сбор метрик: [HTTP-сервер](http-server.md), [HTTP-клиент](http-client.md), [gRPC-сервер](grpc-server.md), [gRPC-клиент](grpc-client.md), [Планировщик](scheduling.md), [Кэш](cache.md) и другие интеграции.

## Использование { #usage }

Kora следует нотации, описанной в [спецификации `Prometheus`](https://prometheus.io/docs/concepts/data_model/).

После подключения модуля в `Metrics.globalRegistry` будет зарегистрирован `PrometheusMeterRegistry`, который используется всеми компонентами, собирающими метрики.
При остановке приложения этот реестр удаляется из `Metrics.globalRegistry` и закрывается.

Компонент `PrometheusMeterRegistryWrapper` является `Root`-компонентом и реализует `Wrapped<PrometheusMeterRegistry>`, поэтому в пользовательский код можно внедрять как общий `MeterRegistry`, так и конкретный `PrometheusMeterRegistry`:

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

Вместе с реестром автоматически подключаются стандартные сборщики `Micrometer`: `ClassLoaderMetrics`, `JvmMemoryMetrics`, `JvmGcMetrics`, `JvmThreadMetrics`, `ProcessorMetrics`, `FileDescriptorMetrics`, `UptimeMetrics`.
Дополнительно регистрируется метрика `kora.up` со значением `1` и тегом `version`.

### Своя метрика { #custom-metric }

Для собственной метрики лучше выделять отдельный компонент, внедрять в него `MeterRegistry` и переиспользовать созданные `Meter`.
Не стоит создавать новую метрику на каждый вызов метода: если набор тегов зависит от операции, используйте ключ с ограниченной кардинальностью и кешируйте метрику в `ConcurrentHashMap`.
Вызов `register(...)` нужен для первичной регистрации метрики в `MeterRegistry`, а на горячем пути лучше обращаться к уже созданному `Timer` / `Counter` / `Gauge` и вызывать только `record(...)` или `increment(...)`.
Такой подход используется во внутренних метриках Kora.

Например, метрика длительности обработки внешней операции:

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

Значения тегов должны иметь ограниченное количество вариантов.
Не используйте в тегах идентификаторы пользователей, номера заявок, полный текст ошибки или другие значения с высокой кардинальностью.

## Персонализация { #personalization }

Для внесения изменений в конфигурацию `PrometheusMeterRegistry` нужно добавить в контейнер `PrometheusMeterRegistryInitializer`.
Инициализатор получает созданный реестр до регистрации стандартных системных метрик, поэтому через него можно добавлять общие теги, `MeterFilter`, правила переименования или собственные настройки `PrometheusMeterRegistry`.

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

Также стандартные метрики имеют собственные настройки, например `slo` для метрик `DistributionSummary`.
Имена полей конфигурации можно посмотреть в `ru.tinkoff.kora.micrometer.module.MetricsConfig`.

## Стандарты { #standard }

Изначальный формат метрик использовал стандарт `OpenTelemetry` `V120`, после Kora `1.1.0` появилась возможность предоставления метрик
в стандарте `OpenTelemetry` `V123`, частичный список изменений можно посмотреть [в документации OpenTelemetry](https://opentelemetry.io/blog/2023/http-conventions-declared-stable/)
и [рекомендациях миграции OpenTelemetry](https://opentelemetry.io/docs/specs/semconv/http/migration-guide/).

Параметр `metrics.opentelemetrySpec` влияет на имена части метрик, единицы измерения и набор тегов.
В справочнике ниже для таких метрик указаны варианты `V120` и `V123`; если вариант не указан, имя одинаковое для обоих стандартов.

## Справочник метрик { #metrics-reference }

Все метрики Kora используют [OpenTelemetry semantic conventions](https://opentelemetry.io/docs/specs/semconv/) для именования и тегов.

Используемые типы метрик [Micrometer](https://docs.micrometer.io/micrometer/reference/concepts.html):

- [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) — применяется как инструмент для сбора распределения произвольных величин.
Тип метрики позволяет эффективно визуализировать данные по бакетам и рассчитывать персентиль.
- [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) — монотонно возрастающий счётчик
- [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) — текущее значение метрики
- [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) — длительность операции с поддержкой количества, суммы, максимума и бакетов

### HTTP-сервер { #http-server }

| Метрика | Prometheus | Тип | Описание | Теги |
|---------|------------|-----|----------|------|
| `http.server.duration` (`V120`), `http.server.request.duration` (`V123`) | `http_server_duration_milliseconds` (`V120`) / `http_server_request_duration_seconds` (`V123`) / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность обработки `HTTP`-запроса на сервере | `V120`: `http.request.method`, `http.response.status_code`, `http.route`, `server.address`, `url.scheme`, `http.target`, `http.method`, `http.status_code`; `V123`: `http.request.method`, `http.response.status_code`, `http.route`, `url.scheme`, `server.address`, `error.type` |
| `http.server.active_requests` | `http_server_active_requests` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Количество активных `HTTP`-запросов | `V120`: `http.route`, `http.request.method`, `server.address`, `url.scheme`, `http.target`, `http.method`; `V123`: `http.route`, `http.request.method`, `server.address`, `url.scheme` |

Подробнее о модуле в документации [HTTP-сервер](http-server.md).

### HTTP-клиент { #http-client }

| Метрика | Prometheus | Тип | Описание | Теги |
|---------|------------|-----|----------|------|
| `http.client.duration` (`V120`), `http.client.request.duration` (`V123`) | `http_client_duration_milliseconds` (`V120`) / `http_client_request_duration_seconds` (`V123`) / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность `HTTP`-запроса клиента | `V120`: `http.request.method`, `http.response.status_code`, `server.address`, `url.scheme`, `http.route`, `http.status_code`, `http.method`, `http.target`, `error.type`; `V123`: `http.request.method`, `http.response.status_code`, `server.address`, `url.scheme`, `http.route`, `http.status_code`, `error.type` |

Подробнее о модуле в документации [HTTP-клиент](http-client.md).

### База данных { #database }

| Метрика | Prometheus | Тип | Описание | Теги |
|---------|------------|-----|----------|------|
| `database.client.request.duration` (`V120`), `db.client.request.duration` (`V123`) | `database_client_request_duration_milliseconds` (`V120`) / `db_client_request_duration_seconds` (`V123`) / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность операции/запроса к базе данных | `V120`: `pool`, `query.id`, `query.operation`, `error`; `V123`: `db.pool.name`, `db.statement`, `db.operation`, `error.type` |

Подробнее о модуле в документации [Базы данных](database-common.md).

### Kafka { #kafka }

| Метрика | Prometheus | Тип | Описание | Теги |
|---------|------------|-----|----------|------|
| `messaging.receive.duration` | `messaging_receive_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность обработки одного сообщения | `messaging.system`, `messaging.destination`, `messaging.operation`, `error.type` |
| `messaging.publish.duration` | `messaging_publish_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность отправки сообщения | `messaging.system`, `messaging.destination`, `messaging.partition_id`, `error.type` |
| `messaging.process.batch.duration` | `messaging_process_batch_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность обработки пакета сообщений | `messaging.system`, `messaging.destination`, `error.type` |
| `messaging.kafka.consumer.lag` | `messaging_kafka_consumer_lag` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Задержка `Kafka Consumer` по разделам | `messaging.system`, `messaging.destination`, `messaging.partition_id`, `messaging.consumer_group` |

Подробнее о модуле в документации [Kafka](kafka.md).

### gRPC-сервер { #grpc-server }

| Метрика | Prometheus | Тип | Описание | Теги |
|---------|------------|-----|----------|------|
| `rpc.server.duration` | `rpc_server_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность обработки gRPC-вызова на сервере | `rpc.service`, `rpc.method`, `rpc.status`, `error.type` |
| `rpc.server.requests_per_rpc` | `rpc_server_requests_per_rpc_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество запросов, полученных за один RPC | `rpc.service`, `rpc.method` |
| `rpc.server.responses_per_rpc` | `rpc_server_responses_per_rpc_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество ответов, отправленных за один RPC | `rpc.service`, `rpc.method` |

Подробнее о модуле в документации [gRPC-сервер](grpc-server.md).

### gRPC-клиент { #grpc-client }

| Метрика | Prometheus | Тип | Описание | Теги |
|---------|------------|-----|----------|------|
| `rpc.client.duration` | `rpc_client_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность gRPC-вызова клиента | `rpc.service`, `rpc.method`, `rpc.status`, `error.type`, `server.address` |
| `rpc.client.requests_per_rpc` | `rpc_client_requests_per_rpc_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество запросов, отправленных за один RPC | `rpc.service`, `rpc.method`, `server.address` |
| `rpc.client.responses_per_rpc` | `rpc_client_responses_per_rpc_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество ответов, полученных за один RPC | `rpc.service`, `rpc.method`, `server.address` |

Подробнее о модуле в документации [gRPC-клиент](grpc-client.md).

### SOAP клиент { #soap-client }

| Метрика | Prometheus | Тип | Описание | Теги |
|---------|------------|-----|----------|------|
| `rpc.client.duration` | `rpc_client_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность SOAP-вызова клиента | `rpc.system`, `rpc.service`, `rpc.method`, `rpc.result`, `server.address`, `server.port` |

Подробнее о модуле в документации [SOAP клиент](soap-client.md).

### Планировщик { #scheduling }

| Метрика | Prometheus | Тип | Описание | Теги |
|---------|------------|-----|----------|------|
| `scheduling.job.duration` | `scheduling_job_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность выполнения запланированной задачи | `code.class`, `code.function`, `error.type` |

Подробнее о модуле в документации [Планировщик](scheduling.md).

### Кэш { #cache }

| Метрика | Prometheus | Тип | Описание | Теги |
|---------|------------|-----|----------|------|
| `cache.duration` | `cache_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | Длительность операции кэша (`GET`, `SET`, `DELETE` и другие) | `cache`, `operation`, `origin`, `status` |
| `cache.ratio` | `cache_ratio_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Счётчик попаданий/промахов кэша | `cache`, `origin`, `type` |
| `cache.hit`, `cache.miss` | `cache_hit_total`, `cache_miss_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Устаревшие счётчики попаданий/промахов, оставлены для совместимости | `cache`, `origin` |

При использовании `Caffeine` автоматически регистрируются стандартные метрики `Micrometer`:

| Метрика | Prometheus | Тип | Описание |
|---------|------------|-----|----------|
| `cache.gets` | `cache_gets_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество запросов к кэшу |
| `cache.puts` | `cache_puts_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество записей в кэш |
| `cache.evictions` | `cache_evictions_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество вытеснений из кэша |
| `cache.size` | `cache_size` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Текущий размер кэша |

Подробнее о модуле в документации [Кэш](cache.md).

### Redis / Lettuce { #redis-lettuce }

| Метрика | Prometheus | Тип | Описание | Теги |
|---------|------------|-----|----------|------|
| `lettuce.command.completion.duration` | `lettuce_command_completion_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность выполнения `Redis`-команды | `type`, `remote`, `local`, `command`, `error.type` |
| `lettuce.command.firstresponse.duration` | `lettuce_command_firstresponse_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Время до первого ответа `Redis`-команды | `type`, `remote`, `local`, `command`, `error.type` |

### Отказоустойчивость { #resilience }

| Метрика | Prometheus | Тип | Описание | Теги |
|---------|------------|-----|----------|------|
| `resilient.circuitbreaker.state` | `resilient_circuitbreaker_state` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Состояние `Circuit Breaker` (`0` = `CLOSED`, `1` = `HALF_OPEN`, `2` = `OPEN`) | `name` |
| `resilient.circuitbreaker.transition` | `resilient_circuitbreaker_transition_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Переходы состояния `Circuit Breaker` | `name`, `state` |
| `resilient.circuitbreaker.call.acquire` | `resilient_circuitbreaker_call_acquire_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Попытки вызова и отказы через `Circuit Breaker` | `name`, `state`, `status` |
| `resilient.retry.attempts` | `resilient_retry_attempts_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество повторных попыток | `name` |
| `resilient.retry.exhausted` | `resilient_retry_exhausted_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество исчерпанных повторных попыток | `name` |
| `resilient.timeout.exhausted` | `resilient_timeout_exhausted_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество таймаутов | `name` |
| `resilient.fallback.attempts` | `resilient_fallback_attempts_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество вызовов `Fallback` | `name`, `type` |

Подробнее о модуле в документации [Отказоустойчивость](resilient.md).

### JMS { #jms }

| Метрика | Prometheus | Тип | Описание | Теги |
|---------|------------|-----|----------|------|
| `messaging.receive.duration` | `messaging_receive_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность получения JMS-сообщения | `messaging.system`, `messaging.destination.name`, `error.type` |

### S3 клиент { #s3-client }

| Метрика | Prometheus | Тип | Описание | Теги |
|---------|------------|-----|----------|------|
| `s3.client.duration` | `s3_client_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность S3 HTTP-запроса | `aws.s3.bucket`, `aws.operation.name`, `error.type` |
| `s3.kora.client.duration` | `s3_kora_client_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность операции Kora S3-клиента | `aws.client.name`, `aws.s3.bucket`, `aws.operation.name`, `error.type` |

Подробнее о модуле в документации [S3 клиент](s3-client.md).

### Camunda 7 BPMN { #camunda-7-bpmn }

| Метрика | Prometheus | Тип | Описание | Теги |
|---------|------------|-----|----------|------|
| `camunda.engine.delegate.duration` | `camunda_engine_delegate_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность выполнения `Camunda BPMN Java Delegate` | `delegate`, `business.key`, `error.type` |
| `camunda.engine.delegate.active_requests` | `camunda_engine_delegate_active_requests` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Количество активных `execution` делегата | `delegate`, `business.key` |

Подробнее о модуле в документации [Camunda 7 BPMN](camunda7-bpmn.md).

### Camunda REST { #camunda-rest }

| Метрика | Prometheus | Тип | Описание | Теги |
|---------|------------|-----|----------|------|
| `camunda.rest.server.duration` (`V120`), `camunda.rest.server.request.duration` (`V123`) | `camunda_rest_server_duration_milliseconds` (`V120`) / `camunda_rest_server_request_duration_seconds` (`V123`) / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность `Camunda REST`-запроса | `V120`: `http.request.method`, `http.response.status_code`, `http.route`, `server.address`, `url.scheme`, `http.target`, `http.method`, `http.status_code`; `V123`: `http.request.method`, `http.response.status_code`, `http.route`, `url.scheme`, `server.address`, `error.type` |
| `camunda.rest.server.active_requests` | `camunda_rest_server_active_requests` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Количество активных Camunda REST-запросов | `http.route`, `http.request.method`, `server.address`, `url.scheme` |

Подробнее о модуле в документации [Camunda 7 REST](camunda7-rest.md).

### Camunda 8 Worker { #camunda-8-worker }

| Метрика | Prometheus | Тип | Описание | Теги |
|---------|------------|-----|----------|------|
| `zeebe.worker.handler` (`V120`), `zeebe.worker.handler.duration` (`V123`) | `zeebe_worker_handler_seconds` (`V120`) / `zeebe_worker_handler_duration_seconds` (`V123`) / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность обработки задачи `Zeebe Worker` | `job.name`, `job.type`, `status`, `error`, `error.code` |
| `zeebe.worker.handler` | `zeebe_worker_handler_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Счётчик ошибок `Zeebe Worker` | `job.name`, `job.type`, `status`, `error.code` |
| `zeebe.client.worker.job` | `zeebe_client_worker_job_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество активированных и обработанных задач `Zeebe` | `action`, `type` |

Подробнее о модуле в документации [Camunda 8 Worker](camunda8-worker.md).

### Система { #system }

| Метрика | Prometheus | Тип | Описание | Теги |
|---------|------------|-----|----------|------|
| `kora.up` | `kora_up` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Индикатор статуса фреймворка (значение = 1) | `version` |

### JVM { #jvm }

Стандартные JVM-метрики собираются автоматически через [Micrometer](https://docs.micrometer.io/micrometer/reference/concepts.html):

| Метрика | Prometheus | Тип | Описание | Теги |
|---------|------------|-----|----------|------|
| `jvm.gc.pause` | `jvm_gc_pause_milliseconds` / `_count` / `_sum` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность пауз сборщика мусора | `action`, `cause` |
| `jvm.gc.memory.allocated` | `jvm_gc_memory_allocated_bytes_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Объём выделенной памяти | — |
| `jvm.gc.memory.promoted` | `jvm_gc_memory_promoted_bytes_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Объём памяти, перемещённой в `old gen` | — |
| `jvm.gc.max.data.size` | `jvm_gc_max_data_size_bytes` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Максимальный размер `old gen` | — |
| `jvm.gc.live.data.size` | `jvm_gc_live_data_size_bytes` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Размер `old gen` после полной сборки мусора | — |
| `jvm.memory.used` | `jvm_memory_used_bytes` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Использованная память | `area`, `id` |
| `jvm.memory.committed` | `jvm_memory_committed_bytes` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Выделенная JVM память | `area`, `id` |
| `jvm.memory.max` | `jvm_memory_max_bytes` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Максимально доступная память | `area`, `id` |
| `jvm.threads.live` | `jvm_threads_live_threads` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Количество активных потоков | — |
| `jvm.threads.daemon` | `jvm_threads_daemon_threads` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Количество `daemon`-потоков | — |
| `jvm.threads.peak` | `jvm_threads_peak_threads` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Пиковое количество потоков | — |
| `jvm.threads.states` | `jvm_threads_states_threads` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Количество потоков по состояниям | `state` |
| `process.cpu.usage` | `process_cpu_usage` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Использование CPU процессом | — |
| `system.cpu.usage` | `system_cpu_usage` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Использование CPU системой | — |
| `system.cpu.count` | `system_cpu_count` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Количество доступных процессоров | — |
| `logback.events` | `logback_events_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество событий логирования | `level` |
| `jvm.classes.loaded` | `jvm_classes_loaded_classes` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Количество загруженных классов | — |
| `jvm.classes.unloaded` | `jvm_classes_unloaded_classes_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество выгруженных классов | — |
| `process.files.open` | `process_files_open_files` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Количество открытых файловых дескрипторов | — |
| `process.files.max` | `process_files_max_files` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Максимальное количество файловых дескрипторов | — |
| `process.uptime` | `process_uptime_milliseconds` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Время работы процесса | — |
