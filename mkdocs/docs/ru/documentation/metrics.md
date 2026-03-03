Модуль для сбора метрик приложения с использованием [Micrometer](https://micrometer.io/docs/concepts#_purpose).

Требует подключения [служебного HTTP сервера](http-server.md) для предоставления метрик в формате [prometheus](https://prometheus.io/docs/concepts/data_model/).

## Подключение

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#_4) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:micrometer-module"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends MetricsModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#_4) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:micrometer-module")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : MetricsModule
    ```

## Конфигурация

Пример конфигурации пути HTTP сервера для получения метрик, описанной в классе `HttpServerConfig` (указаны значения по умолчанию):

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
        privateApiHttpMetricsPath = "/metrics" //(1)!
    }
    ```

    1. Путь для получения метрик в формате `prometheus` (если подключен модуль [HTTP сервера](http-server.md)):

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      privateApiHttpMetricsPath: "/metrics" #(1)!
    ```

    1. Путь для получения метрик в формате `prometheus` (если подключен модуль [HTTP сервера](http-server.md)):

Пример полной конфигурации, описанной в классе `MetricsConfig` (указаны значения по умолчанию):

===! ":material-code-json: `Hocon`"

    ```javascript
    metrics {
        opentelemetrySpec = "V120" //(1)!
    }
    ```

    1. Формат метрик по стандарту OpenTelemetry (доступные значения: [V120](https://opentelemetry.io/docs/specs/semconv/http/migration-guide/#migrating-from-a-version-prior-to-v1200) / [V123](https://opentelemetry.io/docs/specs/semconv/http/migration-guide/))

=== ":simple-yaml: `YAML`"

    ```yaml
    metrics:
      opentelemetrySpec: "V120" #(1)!
    ```

    1. Формат метрик по стандарту OpenTelemetry (доступные значения: [V120](https://opentelemetry.io/docs/specs/semconv/http/migration-guide/#migrating-from-a-version-prior-to-v1200) / [V123](https://opentelemetry.io/docs/specs/semconv/http/migration-guide/))

Параметры конфигурации сбора метрик описываются в модулях в которых присутствует сбор метрик, например [HTTP сервер](http-server.md), [HTTP клиент](http-client.md) и т.д.

## Использование

Мы следуем и вам советуем использовать нотацию, описанную в [спецификации](https://prometheus.io/docs/concepts/data_model/).

После подключения модуля `Metrics.globalRegistry` будет зарегистрирован `PrometheusMeterRegistry`, который будет использоваться во всех компонентах, собирающих метрики.

## Персонализация

Для внесения изменений в конфигурацию `PrometheusMeterRegistry` нужно добавить в контейнер `PrometheusMeterRegistryInitializer`.

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

Так же стандартные метрики имеют некоторые конфигурации, такие как `ServiceLayerObjectives` для Distribution summary метрик.
Имена полей конфигурации можно посмотреть в `ru.tinkoff.kora.micrometer.module.MetricsConfig`.

## Стандарты { #standard }

Изначальный формат метрик использовал стандарт OpenTelemetry `V120`, после Kora `1.1.0` появилась возможность предоставления метрик
в стандарте OpenTelemetry `V123`, частичный список изменений можно посмотреть [в документации OpenTelemetry](https://opentelemetry.io/blog/2023/http-conventions-declared-stable/)
и [рекомендациях миграции OpenTelemetry](https://opentelemetry.io/docs/specs/semconv/http/migration-guide/)

## Справочник метрик

Все метрики Kora используют [OpenTelemetry semantic conventions](https://opentelemetry.io/docs/specs/semconv/) для именования и тегов.

Используемые типы метрик [Micrometer](https://docs.micrometer.io/micrometer/reference/concepts.html):

- [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) — распределение значений, в частности длительностей
- [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) — монотонно возрастающий счётчик
- [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) — текущее значение метрики


### HTTP сервер { #http-server }

| Метрика | Prometheus | Тип | Описание | Теги |
|---------|------------|-----|----------|------|
| `http.server.request.duration` | `http_server_request_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность обработки HTTP-запроса на сервере | `http.request.method`, `http.response.status_code`, `http.route`, `url.scheme`, `server.address`, `error.type` |
| `http.server.active_requests` | `http_server_active_requests` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Количество активных HTTP-запросов | `http.request.method`, `http.route`, `server.address`, `url.scheme` |

Подробнее о модуле в документации [HTTP сервер](http-server.md).

### HTTP клиент { #http-client }

| Метрика | Prometheus | Тип | Описание | Теги |
|---------|------------|-----|----------|------|
| `http.client.request.duration` | `http_client_request_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность HTTP-запроса клиента | `http.request.method`, `http.response.status_code`, `server.address`, `url.scheme`, `http.route`, `error.type` |

Подробнее о модуле в документации [HTTP клиент](http-client.md).

### База данных { #database }

| Метрика | Prometheus | Тип | Описание | Теги |
|---------|------------|-----|----------|------|
| `db.client.request.duration` | `db_client_request_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность операции/запроса к БД | `db.pool.name`, `db.statement`, `db.operation`, `error.type` |

Подробнее о модуле в документации [Базы данных](database-common.md).

### Kafka

| Метрика | Prometheus | Тип | Описание | Теги |
|---------|------------|-----|----------|------|
| `messaging.receive.duration` | `messaging_receive_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность обработки одного сообщения | `messaging.system`, `messaging.destination`, `messaging.operation`, `error.type` |
| `messaging.publish.duration` | `messaging_publish_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность отправки сообщения | `messaging.system`, `messaging.destination`, `messaging.partition_id`, `error.type` |
| `messaging.process.batch.duration` | `messaging_process_batch_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность обработки батча сообщений | `messaging.system`, `messaging.destination`, `error.type` |
| `messaging.kafka.consumer.lag` | `messaging_kafka_consumer_lag` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Лаг консьюмера по партициям | `messaging.system`, `messaging.destination`, `messaging.partition_id`, `messaging.consumer_group` |

Подробнее о модуле в документации [Kafka](kafka.md).

### gRPC сервер { #grpc-server }

| Метрика | Prometheus | Тип | Описание | Теги |
|---------|------------|-----|----------|------|
| `rpc.server.duration` | `rpc_server_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность обработки gRPC-вызова на сервере | `rpc.service`, `rpc.method`, `rpc.status`, `error.type` |
| `rpc.server.requests_per_rpc` | `rpc_server_requests_per_rpc_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество запросов, полученных за один RPC | `rpc.service`, `rpc.method` |
| `rpc.server.responses_per_rpc` | `rpc_server_responses_per_rpc_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество ответов, отправленных за один RPC | `rpc.service`, `rpc.method` |

Подробнее о модуле в документации [gRPC сервер](grpc-server.md).

### gRPC клиент { #grpc-client }

| Метрика | Prometheus | Тип | Описание | Теги |
|---------|------------|-----|----------|------|
| `rpc.client.duration` | `rpc_client_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность gRPC-вызова клиента | `rpc.service`, `rpc.method`, `rpc.status`, `error.type`, `server.address` |
| `rpc.client.requests_per_rpc` | `rpc_client_requests_per_rpc_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество запросов, отправленных за один RPC | `rpc.service`, `rpc.method`, `server.address` |
| `rpc.client.responses_per_rpc` | `rpc_client_responses_per_rpc_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество ответов, полученных за один RPC | `rpc.service`, `rpc.method`, `server.address` |

Подробнее о модуле в документации [gRPC клиент](grpc-client.md).

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
| `cache.duration` | `cache_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность операции кэша (GET, SET, DELETE и т.д.) | `cache`, `operation`, `origin`, `status` |
| `cache.ratio` | `cache_ratio_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Счётчик попаданий/промахов кэша | `cache`, `origin`, `type` |

При использовании Caffeine автоматически регистрируются стандартные метрики Micrometer:

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
| `lettuce.command.completion.duration` | `lettuce_command_completion_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность выполнения Redis-команды | `type`, `remote`, `local`, `command`, `error.type` |
| `lettuce.command.firstresponse.duration` | `lettuce_command_firstresponse_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Время до первого ответа Redis-команды | `type`, `remote`, `local`, `command`, `error.type` |

### Отказоустойчивость { #resilience }

| Метрика | Prometheus | Тип | Описание | Теги |
|---------|------------|-----|----------|------|
| `resilient.circuitbreaker.state` | `resilient_circuitbreaker_state` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Состояние circuit breaker (0=CLOSED, 1=HALF_OPEN, 2=OPEN) | `name` |
| `resilient.circuitbreaker.transition` | `resilient_circuitbreaker_transition_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Переходы состояния circuit breaker | `name`, `state` |
| `resilient.circuitbreaker.call.acquire` | `resilient_circuitbreaker_call_acquire_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Попытки/отказы вызова через circuit breaker | `name`, `state`, `status` |
| `resilient.retry.attempts` | `resilient_retry_attempts_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество попыток ретрая | `name` |
| `resilient.retry.exhausted` | `resilient_retry_exhausted_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество исчерпанных ретраев | `name` |
| `resilient.timeout.exhausted` | `resilient_timeout_exhausted_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество таймаутов | `name` |
| `resilient.fallback.attempts` | `resilient_fallback_attempts_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество вызовов фолбэка | `name`, `type` |

Подробнее о модуле в документации [Отказоустойчивость](resilient.md).

### JMS

| Метрика | Prometheus | Тип | Описание | Теги |
|---------|------------|-----|----------|------|
| `messaging.receive.duration` | `messaging_receive_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность получения JMS-сообщения | `messaging.system`, `messaging.destination.name`, `error.type` |

### S3 клиент { #s3-client }

| Метрика | Prometheus | Тип | Описание | Теги |
|---------|------------|-----|----------|------|
| `s3.client.duration` | `s3_client_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность S3 HTTP-запроса | `aws.s3.bucket`, `aws.operation.name`, `error.type` |
| `s3.kora.client.duration` | `s3_kora_client_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность операции Kora S3-клиента | `aws.client.name`, `aws.s3.bucket`, `aws.operation.name`, `error.type` |

Подробнее о модуле в документации [S3 клиент](s3-client.md).

### Camunda 7 BPMN

| Метрика | Prometheus | Тип | Описание | Теги |
|---------|------------|-----|----------|------|
| `camunda.engine.delegate.duration` | `camunda_engine_delegate_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность выполнения Camunda BPMN Java delegate | `delegate`, `business.key`, `error.type` |
| `camunda.engine.delegate.active_requests` | `camunda_engine_delegate_active_requests` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Количество активных executions делегата | `delegate`, `business.key` |

Подробнее о модуле в документации [Camunda 7 BPMN](camunda7-bpmn.md).

### Camunda REST

| Метрика | Prometheus | Тип | Описание | Теги |
|---------|------------|-----|----------|------|
| `camunda.rest.server.request.duration` | `camunda_rest_server_request_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность Camunda REST-запроса | `http.request.method`, `http.response.status_code`, `http.route`, `url.scheme`, `server.address`, `error.type` |
| `camunda.rest.server.active_requests` | `camunda_rest_server_active_requests` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Количество активных Camunda REST-запросов | `http.route`, `http.request.method`, `server.address`, `url.scheme` |

Подробнее о модуле в документации [Camunda 7 REST](camunda7-rest.md).

### Camunda 8 Worker

| Метрика | Prometheus | Тип | Описание | Теги |
|---------|------------|-----|----------|------|
| `zeebe.worker.handler.duration` | `zeebe_worker_handler_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность обработки задачи Zeebe worker | `job.name`, `job.type`, `status`, `error`, `error.code` |
| `zeebe.worker.handler` | `zeebe_worker_handler_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Счётчик ошибок Zeebe worker | `job.name`, `job.type`, `status`, `error.code` |
| `zeebe.client.worker.job` | `zeebe_client_worker_job_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Количество активированных/обработанных задач Zeebe | `action`, `type` |

Подробнее о модуле в документации [Camunda 8 Worker](camunda8-worker.md).

### Система { #system }

| Метрика | Prometheus | Тип | Описание | Теги |
|---------|------------|-----|----------|------|
| `kora.up` | `kora_up` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Индикатор статуса фреймворка (значение = 1) | `version` |

### JVM

Стандартные JVM-метрики собираются автоматически через [Micrometer](https://docs.micrometer.io/micrometer/reference/concepts.html):

| Метрика | Prometheus | Тип | Описание | Теги |
|---------|------------|-----|----------|------|
| `jvm.gc.pause` | `jvm_gc_pause_milliseconds` / `_count` / `_sum` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Длительность пауз сборщика мусора | `action`, `cause` |
| `jvm.gc.memory.allocated` | `jvm_gc_memory_allocated_bytes_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Объём выделенной памяти | — |
| `jvm.gc.memory.promoted` | `jvm_gc_memory_promoted_bytes_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Объём памяти, перемещённой в old gen | — |
| `jvm.gc.max.data.size` | `jvm_gc_max_data_size_bytes` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Максимальный размер old gen | — |
| `jvm.gc.live.data.size` | `jvm_gc_live_data_size_bytes` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Размер old gen после полной сборки мусора | — |
| `jvm.memory.used` | `jvm_memory_used_bytes` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Использованная память | `area`, `id` |
| `jvm.memory.committed` | `jvm_memory_committed_bytes` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Выделенная JVM память | `area`, `id` |
| `jvm.memory.max` | `jvm_memory_max_bytes` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Максимально доступная память | `area`, `id` |
| `jvm.threads.live` | `jvm_threads_live_threads` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Количество активных потоков | — |
| `jvm.threads.daemon` | `jvm_threads_daemon_threads` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Количество daemon-потоков | — |
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
