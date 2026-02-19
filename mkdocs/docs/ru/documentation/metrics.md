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

## Справочник метрик

Все метрики используют [OpenTelemetry semantic conventions](https://opentelemetry.io/docs/specs/semconv/) для именования и тегов,
а также поддерживают настраиваемые SLO через конфигурацию.

### HTTP

| Метрика | Prometheus | Тип | Модуль | Описание | Теги |
|---------|------------|-----|--------|----------|------|
| `http.server.request.duration` | `http_server_request_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | Timer | http-server-common | Длительность обработки HTTP-запроса на сервере | `http.request.method`, `http.route`, `url.scheme`, `server.address` |
| `http.server.active_requests` | `http_server_active_requests` | Gauge | http-server-common | Количество активных HTTP-запросов | `http.request.method`, `http.route`, `url.scheme`, `server.address` |
| `http.client.request.duration` | `http_client_request_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | Timer | http-client-common | Длительность HTTP-запроса клиента | `http.request.method`, `http.response.status_code`, `server.address`, `url.scheme`, `http.route`, `error.type` |

### Database

| Метрика | Prometheus | Тип | Модуль | Описание | Теги |
|---------|------------|-----|--------|----------|------|
| `db.client.operation.duration` | `db_client_operation_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | Timer | database-common | Длительность операции/запроса к БД | `db.client.connection.pool.name`, `db.query.text`, `db.operation.name` |

### Kafka

| Метрика | Prometheus | Тип | Модуль | Описание | Теги |
|---------|------------|-----|--------|----------|------|
| `messaging.client.operation.duration` | `messaging_client_operation_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | Timer | kafka (producer) | Длительность отправки сообщения | `messaging.system`, `messaging.destination.name`, `messaging.client.id`, `messaging.operation.type` |
| `messaging.client.sent.messages` | `messaging_client_sent_messages_total` | Counter | kafka (producer) | Количество отправленных сообщений | `messaging.system`, `messaging.destination.name`, `messaging.client.id` |
| `messaging.process.batch.duration` | `messaging_process_batch_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | Timer | kafka (consumer) | Длительность обработки батча сообщений | `messaging.system`, `messaging.client.id`, `messaging.consumer.group.name`, `messaging.kafka.consumer.name` |
| `messaging.kafka.consumer.lag` | `messaging_kafka_consumer_lag` | Gauge | kafka (consumer) | Лаг консьюмера по партициям | `messaging.system`, `messaging.destination.name`, `messaging.destination.partition.id`, `messaging.client.id`, `messaging.kafka.consumer.name` |

### gRPC

| Метрика | Prometheus | Тип | Модуль | Описание | Теги |
|---------|------------|-----|--------|----------|------|
| `rpc.server.duration` | `rpc_server_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | Timer | grpc-server | Длительность обработки gRPC-вызова на сервере | `rpc.system`, `rpc.service`, `rpc.method` |
| `rpc.client.duration` | `rpc_client_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | Timer | grpc-client | Длительность gRPC-вызова клиента | `rpc.method`, `rpc.service`, `rpc.system`, `server.address`, `server.port` |

### Scheduling

| Метрика | Prometheus | Тип | Модуль | Описание | Теги |
|---------|------------|-----|--------|----------|------|
| `scheduling.job.duration` | `scheduling_job_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | Timer | scheduling-common | Длительность выполнения запланированной задачи | `code.function` |

### Cache (Redis)

| Метрика | Prometheus | Тип | Модуль | Описание | Теги |
|---------|------------|-----|--------|----------|------|
| `cache.duration` | `cache_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | Timer | cache-redis | Длительность операции кэша (GET, SET, DELETE и т.д.) | `cache`, `operation`, `origin` |
| `cache.ratio` | `cache_ratio_total` | Counter | cache-redis | Счетчик попаданий/промахов кэша | `cache`, `origin` |
| `lettuce.command.completion.duration` | `lettuce_command_completion_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | Timer | cache-redis (lettuce) | Латентность завершения Redis-команды | `type`, `local`, `remote`, `command`, `error.type` |
| `lettuce.command.firstresponse.duration` | `lettuce_command_firstresponse_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | Timer | cache-redis (lettuce) | Латентность первого ответа Redis-команды | `type`, `local`, `remote`, `command`, `error.type` |

### Resilience

| Метрика | Prometheus | Тип | Модуль | Описание | Теги |
|---------|------------|-----|--------|----------|------|
| `resilient.retry.attempts` | `resilient_retry_attempts_total` | Counter | resilient | Количество попыток ретрая | `name` |
| `resilient.retry.exhausted` | `resilient_retry_exhausted_total` | Counter | resilient | Количество исчерпанных ретраев | `name` |
| `resilient.timeout.exhausted` | `resilient_timeout_exhausted_total` | Counter | resilient | Количество таймаутов | `name` |
| `resilient.fallback.attempts` | `resilient_fallback_attempts_total` | Counter | resilient | Количество вызовов фолбэка | `type`, `name` |
| `resilient.circuitbreaker.state` | `resilient_circuitbreaker_state` | Gauge | resilient | Состояние circuit breaker (0=CLOSED, 1=HALF_OPEN, 2=OPEN) | `name` |
| `resilient.circuitbreaker.transition` | `resilient_circuitbreaker_transition_total` | Counter | resilient | Переходы состояния circuit breaker | `name`, `state` |
| `resilient.circuitbreaker.call.acquire` | `resilient_circuitbreaker_call_acquire_total` | Counter | resilient | Попытки/отказы вызова через circuit breaker | `name`, `state`, `status` |

### JMS

| Метрика | Prometheus | Тип | Модуль | Описание | Теги |
|---------|------------|-----|--------|----------|------|
| `messaging.receive.duration` | `messaging_receive_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | Timer | jms | Длительность получения JMS-сообщения | `messaging.system`, `messaging.destination.name` |

### SOAP

| Метрика | Prometheus | Тип | Модуль | Описание | Теги |
|---------|------------|-----|--------|----------|------|
| `rpc.client.duration` | `rpc_client_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | Timer | soap-client | Длительность SOAP-вызова клиента | `rpc.system`, `rpc.service`, `rpc.method`, `server.address`, `server.port` |

### S3

| Метрика | Prometheus | Тип | Модуль | Описание | Теги |
|---------|------------|-----|--------|----------|------|
| `rpc.client.duration` | `rpc_client_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | Timer | s3-client | Длительность S3 API-операции | `rpc.system`, `rpc.method`, `aws.s3.bucket` |

### Camunda

| Метрика | Prometheus | Тип | Модуль | Описание | Теги |
|---------|------------|-----|--------|----------|------|
| `camunda.engine.delegate.duration` | `camunda_engine_delegate_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | Timer | camunda-engine-bpmn | Длительность выполнения Camunda BPMN Java delegate | `delegate` |
| `zeebe.worker.handler.duration` | `zeebe_worker_handler_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | Timer | camunda-zeebe-worker | Длительность обработки задачи Zeebe worker | `job.name`, `job.type` |

### System

| Метрика | Prometheus | Тип | Модуль | Описание | Теги |
|---------|------------|-----|--------|----------|------|
| `kora.up` | `kora_up` | Gauge | micrometer | Статус/версия фреймворка | `version` |

### JVM (Micrometer)

Стандартные JVM-метрики собираются автоматически через Micrometer:

- `jvm.gc.*` — сборка мусора
- `jvm.memory.*` — память
- `jvm.threads.*` — потоки
- `process.*` — метрики процесса
- `system.*` — системные метрики
- `logback.events.*` — логирование
- `classloader.*` — загрузчик классов
- `process.files.*` — файловые дескрипторы
- `process.uptime.*` — аптайм
