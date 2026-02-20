Module for collecting application metrics using [Micrometer](https://micrometer.io/docs/concepts#_purpose).

Requires [private HTTP server](http-server.md) module added to provide metrics in [prometheus](https://prometheus.io/docs/concepts/data_model/) format.

## Dependency

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:micrometer-module"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends MetricsModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:micrometer-module")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : MetricsModule
    ```

## Configuration

Example of HTTP server path configuration for retrieving metrics described in the `HttpServerConfig` class (default values are specified):

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
        privateApiHttpMetricsPath = "/metrics" //(1)!
    }
    ```

    1. Path to get metrics in `prometheus` format (if [HTTP server](http-server.md) module is added):

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      privateApiHttpMetricsPath: "/metrics" #(1)!
    ```

    1. Path to get metrics in `prometheus` format (if [HTTP server](http-server.md) module is added):

Example of the complete configuration described in the `MetricsConfig` class (default values are specified):

===! ":material-code-json: `Hocon`"

    ```javascript
    metrics {
        opentelemetrySpec = "V120" //(1)!
    }
    ```

    1. OpenTelemetry standard metrics format (available values: [V120](https://opentelemetry.io/docs/specs/semconv/http/migration-guide/#migrating-from-a-version-prior-to-v1200) / [V123](https://opentelemetry.io/docs/specs/semconv/http/migration-guide/))

=== ":simple-yaml: `YAML`"

    ```yaml
    metrics:
      opentelemetrySpec: "V120" #(1)!
    ```

    1. OpenTelemetry standard metrics format (available values: [V120](https://opentelemetry.io/docs/specs/semconv/http/migration-guide/#migrating-from-a-version-prior-to-v1200) / [V123](https://opentelemetry.io/docs/specs/semconv/http/migration-guide/))

Metrics collection configuration parameters are described in modules where metrics collection is present, e.g. [HTTP server](http-server.md), [HTTP client](http-client.md), etc.

## Usage

We follow and encourage to use the notation described in the [specification](https://prometheus.io/docs/concepts/data_model/).

Once the `Metrics.globalRegistry` module is connected, the `PrometheusMeterRegistry` will be registered and used in all components that collect metrics.

## Personalization

In order to make changes to the `PrometheusMeterRegistry` configuration, you need to add to the `PrometheusMeterRegistryInitializer` container.

**Important**, `PrometheusMeterRegistryInitializer` is applied only once when the application is initialized.

For example, we want to add a common tag for all metrics:

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

Standard metrics have some configurations such as `ServiceLayerObjectives` for Distribution summary metrics.
The configuration field names can be viewed in `ru.tinkoff.kora.micrometer.module.MetricsConfig`.

## Standard

The original metrics format used the OpenTelemetry `V120` standard, after Kora `1.1.0` it became possible to provide metrics
in the OpenTelemetry `V123` standard, a partial list of changes can be seen [in the OpenTelemetry documentation](https://opentelemetry.io/blog/2023/http-conventions-declared-stable/)
and [OpenTelemetry migration guidelines](https://opentelemetry.io/docs/specs/semconv/http/migration-guide/)

## Metrics Reference

All Kora metrics use [OpenTelemetry semantic conventions](https://opentelemetry.io/docs/specs/semconv/) for naming and tags.

[Micrometer](https://docs.micrometer.io/micrometer/reference/concepts.html) metric types used:

- [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) — value distribution, including durations
- [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) — monotonically increasing counter
- [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) — current metric value


### HTTP Server

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `http.server.request.duration` | `http_server_request_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | HTTP server request processing duration | `http.request.method`, `http.route`, `url.scheme`, `server.address` |
| `http.server.active_requests` | `http_server_active_requests` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Number of active HTTP requests | `http.request.method`, `http.route`, `url.scheme`, `server.address` |

See [HTTP Server](http-server.md) module documentation for more details.

### HTTP Client

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `http.client.request.duration` | `http_client_request_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | HTTP client request duration | `http.request.method`, `http.response.status_code`, `server.address`, `url.scheme`, `http.route`, `error.type` |

See [HTTP Client](http-client.md) module documentation for more details.

### Database

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `db.client.operation.duration` | `db_client_operation_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Database operation/query duration | `db.client.connection.pool.name`, `db.query.text`, `db.operation.name` |

See [Database](database-common.md) module documentation for more details.

### Kafka

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `messaging.client.operation.duration` | `messaging_client_operation_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Message send duration | `messaging.system`, `messaging.destination.name`, `messaging.client.id`, `messaging.operation.type` |
| `messaging.client.sent.messages` | `messaging_client_sent_messages_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Number of sent messages | `messaging.system`, `messaging.destination.name`, `messaging.client.id` |
| `messaging.process.batch.duration` | `messaging_process_batch_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Message batch processing duration | `messaging.system`, `messaging.client.id`, `messaging.consumer.group.name`, `messaging.kafka.consumer.name` |
| `messaging.kafka.consumer.lag` | `messaging_kafka_consumer_lag` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Consumer lag per partition | `messaging.system`, `messaging.destination.name`, `messaging.destination.partition.id`, `messaging.client.id`, `messaging.kafka.consumer.name` |

See [Kafka](kafka.md) module documentation for more details.

### gRPC Server

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `rpc.server.duration` | `rpc_server_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | gRPC server call processing duration | `rpc.system`, `rpc.service`, `rpc.method` |

See [gRPC Server](grpc-server.md) module documentation for more details.

### gRPC Client

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `rpc.client.duration` | `rpc_client_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | gRPC client call duration | `rpc.method`, `rpc.service`, `rpc.system`, `server.address`, `server.port` |

See [gRPC Client](grpc-client.md) module documentation for more details.

### Scheduling

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `scheduling.job.duration` | `scheduling_job_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Scheduled job execution duration | `code.function` |

See [Scheduling](scheduling.md) module documentation for more details.

### Cache

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `cache.duration` | `cache_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Cache operation duration (GET, SET, DELETE, etc.) | `cache`, `operation`, `origin` |
| `cache.ratio` | `cache_ratio_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Cache hit/miss counter | `cache`, `origin` |
| `lettuce.command.completion.duration` | `lettuce_command_completion_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Redis command completion latency | `type`, `local`, `remote`, `command`, `error.type` |
| `lettuce.command.firstresponse.duration` | `lettuce_command_firstresponse_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Redis command first response latency | `type`, `local`, `remote`, `command`, `error.type` |

See [Cache](cache.md) module documentation for more details.

### Resilience

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `resilient.retry.attempts` | `resilient_retry_attempts_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Number of retry attempts | `name` |
| `resilient.retry.exhausted` | `resilient_retry_exhausted_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Number of exhausted retries | `name` |
| `resilient.timeout.exhausted` | `resilient_timeout_exhausted_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Number of timeouts | `name` |
| `resilient.fallback.attempts` | `resilient_fallback_attempts_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Number of fallback invocations | `type`, `name` |
| `resilient.circuitbreaker.state` | `resilient_circuitbreaker_state` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Circuit breaker state (0=CLOSED, 1=HALF_OPEN, 2=OPEN) | `name` |
| `resilient.circuitbreaker.transition` | `resilient_circuitbreaker_transition_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Circuit breaker state transitions | `name`, `state` |
| `resilient.circuitbreaker.call.acquire` | `resilient_circuitbreaker_call_acquire_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Circuit breaker call acquire attempts/rejections | `name`, `state`, `status` |

See [Resilience](resilient.md) module documentation for more details.

### JMS

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `messaging.receive.duration` | `messaging_receive_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | JMS message receive duration | `messaging.system`, `messaging.destination.name` |

### SOAP Client

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `rpc.client.duration` | `rpc_client_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | SOAP client call duration | `rpc.system`, `rpc.service`, `rpc.method`, `server.address`, `server.port` |

See [SOAP Client](soap-client.md) module documentation for more details.

### S3 Client

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `rpc.client.duration` | `rpc_client_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | S3 API operation duration | `rpc.system`, `rpc.method`, `aws.s3.bucket` |

See [S3 Client](s3-client.md) module documentation for more details.

### Camunda 7 BPMN

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `camunda.engine.delegate.duration` | `camunda_engine_delegate_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Camunda BPMN Java delegate execution duration | `delegate` |

See [Camunda 7 BPMN](camunda7-bpmn.md) module documentation for more details.

### Camunda 8 Worker

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `zeebe.worker.handler.duration` | `zeebe_worker_handler_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Zeebe worker job handler duration | `job.name`, `job.type` |

See [Camunda 8 Worker](camunda8-worker.md) module documentation for more details.

### System

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `kora.up` | `kora_up` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Framework status/version | `version` |

### JVM

Standard JVM metrics are collected automatically via [Micrometer](https://docs.micrometer.io/micrometer/reference/concepts.html):

- `jvm.gc.*` — garbage collection
- `jvm.memory.*` — memory
- `jvm.threads.*` — threads
- `process.*` — process metrics
- `system.*` — system metrics
- `logback.events.*` — logging
- `classloader.*` — class loader
- `process.files.*` — file descriptors
- `process.uptime.*` — uptime
