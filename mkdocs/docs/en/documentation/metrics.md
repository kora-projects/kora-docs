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
| `http.server.request.duration` | `http_server_request_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | HTTP server request processing duration | `http.request.method`, `http.response.status_code`, `http.route`, `url.scheme`, `server.address`, `error.type` |
| `http.server.active_requests` | `http_server_active_requests` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Number of active HTTP requests | `http.request.method`, `http.route`, `server.address`, `url.scheme` |

See [HTTP Server](http-server.md) module documentation for more details.

### HTTP Client

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `http.client.request.duration` | `http_client_request_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | HTTP client request duration | `http.request.method`, `http.response.status_code`, `server.address`, `url.scheme`, `http.route`, `error.type` |

See [HTTP Client](http-client.md) module documentation for more details.

### Database

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `db.client.request.duration` | `db_client_request_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Database operation/query duration | `db.pool.name`, `db.statement`, `db.operation`, `error.type` |

See [Database](database-common.md) module documentation for more details.

### Kafka

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `messaging.receive.duration` | `messaging_receive_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Single message processing duration | `messaging.system`, `messaging.destination`, `messaging.operation`, `error.type` |
| `messaging.publish.duration` | `messaging_publish_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Message send duration | `messaging.system`, `messaging.destination`, `messaging.partition_id`, `error.type` |
| `messaging.process.batch.duration` | `messaging_process_batch_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Message batch processing duration | `messaging.system`, `messaging.destination`, `error.type` |
| `messaging.kafka.consumer.lag` | `messaging_kafka_consumer_lag` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Consumer lag per partition | `messaging.system`, `messaging.destination`, `messaging.partition_id`, `messaging.consumer_group` |

See [Kafka](kafka.md) module documentation for more details.

### gRPC Server

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `rpc.server.duration` | `rpc_server_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | gRPC server call processing duration | `rpc.service`, `rpc.method`, `rpc.status`, `error.type` |
| `rpc.server.requests_per_rpc` | `rpc_server_requests_per_rpc_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Number of requests received per RPC | `rpc.service`, `rpc.method` |
| `rpc.server.responses_per_rpc` | `rpc_server_responses_per_rpc_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Number of responses sent per RPC | `rpc.service`, `rpc.method` |

See [gRPC Server](grpc-server.md) module documentation for more details.

### gRPC Client

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `rpc.client.duration` | `rpc_client_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | gRPC client call duration | `rpc.service`, `rpc.method`, `rpc.status`, `error.type`, `server.address` |
| `rpc.client.requests_per_rpc` | `rpc_client_requests_per_rpc_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Number of requests sent per RPC | `rpc.service`, `rpc.method`, `server.address` |
| `rpc.client.responses_per_rpc` | `rpc_client_responses_per_rpc_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Number of responses received per RPC | `rpc.service`, `rpc.method`, `server.address` |

See [gRPC Client](grpc-client.md) module documentation for more details.

### SOAP Client

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `rpc.client.duration` | `rpc_client_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | SOAP client call duration | `rpc.system`, `rpc.service`, `rpc.method`, `rpc.result`, `server.address`, `server.port` |

See [SOAP Client](soap-client.md) module documentation for more details.

### Scheduling

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `scheduling.job.duration` | `scheduling_job_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Scheduled job execution duration | `code.class`, `code.function`, `error.type` |

See [Scheduling](scheduling.md) module documentation for more details.

### Cache

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `cache.duration` | `cache_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Cache operation duration (GET, SET, DELETE, etc.) | `cache`, `operation`, `origin`, `status` |
| `cache.ratio` | `cache_ratio_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Cache hit/miss counter | `cache`, `origin`, `type` |

Standard Micrometer metrics are automatically registered when using Caffeine:

| Metric | Prometheus | Type | Description |
|--------|------------|------|-------------|
| `cache.gets` | `cache_gets_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Number of cache requests |
| `cache.puts` | `cache_puts_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Number of cache writes |
| `cache.evictions` | `cache_evictions_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Number of cache evictions |
| `cache.size` | `cache_size` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Current cache size |

See [Cache](cache.md) module documentation for more details.

### Redis / Lettuce

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `lettuce.command.completion.duration` | `lettuce_command_completion_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Redis command completion duration | `type`, `remote`, `local`, `command`, `error.type` |
| `lettuce.command.firstresponse.duration` | `lettuce_command_firstresponse_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Redis command first response duration | `type`, `remote`, `local`, `command`, `error.type` |

### Resilience

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `resilient.circuitbreaker.state` | `resilient_circuitbreaker_state` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Circuit breaker state (0=CLOSED, 1=HALF_OPEN, 2=OPEN) | `name` |
| `resilient.circuitbreaker.transition` | `resilient_circuitbreaker_transition_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Circuit breaker state transitions | `name`, `state` |
| `resilient.circuitbreaker.call.acquire` | `resilient_circuitbreaker_call_acquire_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Circuit breaker call acquire attempts/rejections | `name`, `state`, `status` |
| `resilient.retry.attempts` | `resilient_retry_attempts_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Number of retry attempts | `name` |
| `resilient.retry.exhausted` | `resilient_retry_exhausted_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Number of exhausted retries | `name` |
| `resilient.timeout.exhausted` | `resilient_timeout_exhausted_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Number of timeouts | `name` |
| `resilient.fallback.attempts` | `resilient_fallback_attempts_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Number of fallback invocations | `name`, `type` |

See [Resilience](resilient.md) module documentation for more details.

### JMS

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `messaging.receive.duration` | `messaging_receive_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | JMS message receive duration | `messaging.system`, `messaging.destination.name`, `error.type` |

### S3 Client

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `s3.client.duration` | `s3_client_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | S3 HTTP request duration | `aws.s3.bucket`, `aws.operation.name`, `error.type` |
| `s3.kora.client.duration` | `s3_kora_client_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Kora S3 client operation duration | `aws.client.name`, `aws.s3.bucket`, `aws.operation.name`, `error.type` |

See [S3 Client](s3-client.md) module documentation for more details.

### Camunda 7 BPMN

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `camunda.engine.delegate.duration` | `camunda_engine_delegate_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Camunda BPMN Java delegate execution duration | `delegate`, `business.key`, `error.type` |
| `camunda.engine.delegate.active_requests` | `camunda_engine_delegate_active_requests` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Number of active delegate executions | `delegate`, `business.key` |

See [Camunda 7 BPMN](camunda7-bpmn.md) module documentation for more details.

### Camunda REST

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `camunda.rest.server.request.duration` | `camunda_rest_server_request_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Camunda REST request duration | `http.request.method`, `http.response.status_code`, `http.route`, `url.scheme`, `server.address`, `error.type` |
| `camunda.rest.server.active_requests` | `camunda_rest_server_active_requests` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Number of active Camunda REST requests | `http.route`, `http.request.method`, `server.address`, `url.scheme` |

See [Camunda 7 REST](camunda7-rest.md) module documentation for more details.

### Camunda 8 Worker

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `zeebe.worker.handler.duration` | `zeebe_worker_handler_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Zeebe worker job handler duration | `job.name`, `job.type`, `status`, `error`, `error.code` |
| `zeebe.worker.handler` | `zeebe_worker_handler_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Zeebe worker error counter | `job.name`, `job.type`, `status`, `error.code` |
| `zeebe.client.worker.job` | `zeebe_client_worker_job_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Number of activated/handled Zeebe jobs | `action`, `type` |

See [Camunda 8 Worker](camunda8-worker.md) module documentation for more details.

### System

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `kora.up` | `kora_up` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Framework status indicator (value = 1) | `version` |

### JVM

Standard JVM metrics are collected automatically via [Micrometer](https://docs.micrometer.io/micrometer/reference/concepts.html):

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `jvm.gc.pause` | `jvm_gc_pause_milliseconds` / `_count` / `_sum` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | GC pause duration | `action`, `cause` |
| `jvm.gc.memory.allocated` | `jvm_gc_memory_allocated_bytes_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Allocated memory size | — |
| `jvm.gc.memory.promoted` | `jvm_gc_memory_promoted_bytes_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Memory promoted to old gen | — |
| `jvm.gc.max.data.size` | `jvm_gc_max_data_size_bytes` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Max old gen size | — |
| `jvm.gc.live.data.size` | `jvm_gc_live_data_size_bytes` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Old gen size after full GC | — |
| `jvm.memory.used` | `jvm_memory_used_bytes` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Used memory | `area`, `id` |
| `jvm.memory.committed` | `jvm_memory_committed_bytes` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Committed JVM memory | `area`, `id` |
| `jvm.memory.max` | `jvm_memory_max_bytes` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Max available memory | `area`, `id` |
| `jvm.threads.live` | `jvm_threads_live_threads` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Number of live threads | — |
| `jvm.threads.daemon` | `jvm_threads_daemon_threads` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Number of daemon threads | — |
| `jvm.threads.peak` | `jvm_threads_peak_threads` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Peak thread count | — |
| `jvm.threads.states` | `jvm_threads_states_threads` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Thread count by state | `state` |
| `process.cpu.usage` | `process_cpu_usage` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Process CPU usage | — |
| `system.cpu.usage` | `system_cpu_usage` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | System CPU usage | — |
| `system.cpu.count` | `system_cpu_count` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Number of available processors | — |
| `logback.events` | `logback_events_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Logging event count | `level` |
| `jvm.classes.loaded` | `jvm_classes_loaded_classes` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Number of loaded classes | — |
| `jvm.classes.unloaded` | `jvm_classes_unloaded_classes_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Number of unloaded classes | — |
| `process.files.open` | `process_files_open_files` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Number of open file descriptors | — |
| `process.files.max` | `process_files_max_files` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Max file descriptors | — |
| `process.uptime` | `process_uptime_milliseconds` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Process uptime | — |
