---
description: "Explains Kora metrics with Micrometer, Prometheus export, OpenTelemetry metric standards, registry customization, and module-specific metric references. Use when working with MetricsModule, Micrometer, PrometheusMeterRegistry, MetricsConfig, PrometheusMeterRegistryInitializer, OpenTelemetry, Metrics Reference."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora metrics with Micrometer, Prometheus export, OpenTelemetry metric standards, registry customization, and module-specific metric references; key triggers include MetricsModule, Micrometer, PrometheusMeterRegistry, MetricsConfig, PrometheusMeterRegistryInitializer, OpenTelemetry, Metrics Reference."
---

Module for collecting application metrics using [Micrometer](https://micrometer.io/docs/concepts#_purpose).
It creates a `PrometheusMeterRegistry`, connects Kora component metrics to it, and exposes the result in the `Prometheus` format through the private `HTTP` server.
This lets you collect application, `JVM`, process, and built-in integration metrics in one place and scrape them with an external observability system.

Publishing metrics requires the [private HTTP server](http-server.md), which exposes them in the [Prometheus](https://prometheus.io/docs/concepts/data_model/) format.

For a step-by-step walkthrough before the reference details, see [Observability](../guides/observability.md).

## Dependency { #dependency }

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

## Configuration { #configuration }

Example of private `HTTP` server path configuration for retrieving metrics described in the `HttpServerConfig` class (default values are specified):

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
        privateApiHttpMetricsPath = "/metrics" //(1)!
    }
    ```

    1. Path for retrieving metrics in the `Prometheus` format (default: `"/metrics"`).

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      privateApiHttpMetricsPath: "/metrics" #(1)!
    ```

    1. Path for retrieving metrics in the `Prometheus` format (default: `"/metrics"`).

Example of the complete configuration described in the `MetricsConfig` class (default values are specified):

===! ":material-code-json: `Hocon`"

    ```javascript
    metrics {
        opentelemetrySpec = "V120" //(1)!
    }
    ```

    1. Metrics format according to the `OpenTelemetry` standard (available values: [V120](https://opentelemetry.io/docs/specs/semconv/http/migration-guide/#migrating-from-a-version-prior-to-v1200) / [V123](https://opentelemetry.io/docs/specs/semconv/http/migration-guide/), default: `V120`).

=== ":simple-yaml: `YAML`"

    ```yaml
    metrics:
      opentelemetrySpec: "V120" #(1)!
    ```

    1. Metrics format according to the `OpenTelemetry` standard (available values: [V120](https://opentelemetry.io/docs/specs/semconv/http/migration-guide/#migrating-from-a-version-prior-to-v1200) / [V123](https://opentelemetry.io/docs/specs/semconv/http/migration-guide/), default: `V120`).

Metrics collection configuration parameters are described in modules that collect metrics: [HTTP Server](http-server.md), [HTTP Client](http-client.md), [gRPC Server](grpc-server.md), [gRPC Client](grpc-client.md), [Scheduling](scheduling.md), [Cache](cache.md), and other integrations.

## Usage { #usage }

Kora follows the notation described in the [`Prometheus` specification](https://prometheus.io/docs/concepts/data_model/).

After the module is connected, `PrometheusMeterRegistry` is registered in `Metrics.globalRegistry` and used by all components that collect metrics.
When the application stops, this registry is removed from `Metrics.globalRegistry` and closed.

The `PrometheusMeterRegistryWrapper` component is a `Root` component and implements `Wrapped<PrometheusMeterRegistry>`, so user code can inject either the generic `MeterRegistry` or the concrete `PrometheusMeterRegistry`:

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

The registry automatically gets standard `Micrometer` binders: `ClassLoaderMetrics`, `JvmMemoryMetrics`, `JvmGcMetrics`, `JvmThreadMetrics`, `ProcessorMetrics`, `FileDescriptorMetrics`, `UptimeMetrics`.
Kora also registers the `kora.up` metric with value `1` and the `version` tag.

### Custom Metric { #custom-metric }

For a custom metric, it is better to create a separate component, inject `MeterRegistry`, and reuse created `Meter` instances.
Do not create a new metric on every method call: if the tag set depends on the operation, use a key with limited cardinality and cache the metric in `ConcurrentHashMap`.
The `register(...)` call is needed for initial metric registration in `MeterRegistry`; on the hot path, prefer using an already created `Timer` / `Counter` / `Gauge` and only call `record(...)` or `increment(...)`.
Kora uses the same approach for its internal metrics.

For example, a duration metric for an external operation:

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

Tag values must have a limited number of variants.
Do not use user identifiers, request numbers, full error text, or other high-cardinality values as tags.

## Personalization { #personalization }

To change `PrometheusMeterRegistry` configuration, add a `PrometheusMeterRegistryInitializer` to the container.
The initializer receives the created registry before standard system metrics are registered, so it can add common tags, `MeterFilter`, renaming rules, or custom `PrometheusMeterRegistry` settings.

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

Standard metrics also have their own settings, for example `slo` for `DistributionSummary` metrics.
The configuration field names can be viewed in `ru.tinkoff.kora.micrometer.module.MetricsConfig`.

## Standard { #standard }

The original metrics format used the `OpenTelemetry` `V120` standard; after Kora `1.1.0`, metrics can also be provided
in the `OpenTelemetry` `V123` standard. A partial list of changes is available in the [OpenTelemetry documentation](https://opentelemetry.io/blog/2023/http-conventions-declared-stable/)
and [OpenTelemetry migration guidelines](https://opentelemetry.io/docs/specs/semconv/http/migration-guide/).

The `metrics.opentelemetrySpec` parameter affects some metric names, units, and tag sets.
The reference below lists both `V120` and `V123` variants for such metrics; if no variant is specified, the name is the same for both standards.

## Metrics Reference { #metrics-reference }

All Kora metrics use [OpenTelemetry semantic conventions](https://opentelemetry.io/docs/specs/semconv/) for naming and tags.

[Micrometer](https://docs.micrometer.io/micrometer/reference/concepts.html) metric types used:

- [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) — used for collecting distributions of arbitrary values.
This metric type enables efficient data visualization across buckets and percentile calculation.
- [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) — monotonically increasing counter
- [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) — current metric value
- [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) — operation duration with count, sum, max, and buckets support

### HTTP Server { #http-server }

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `http.server.duration` (`V120`), `http.server.request.duration` (`V123`) | `http_server_duration_milliseconds` (`V120`) / `http_server_request_duration_seconds` (`V123`) / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | `HTTP` server request processing duration | `V120`: `http.request.method`, `http.response.status_code`, `http.route`, `server.address`, `url.scheme`, `http.target`, `http.method`, `http.status_code`; `V123`: `http.request.method`, `http.response.status_code`, `http.route`, `url.scheme`, `server.address`, `error.type` |
| `http.server.active_requests` | `http_server_active_requests` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Number of active `HTTP` requests | `V120`: `http.route`, `http.request.method`, `server.address`, `url.scheme`, `http.target`, `http.method`; `V123`: `http.route`, `http.request.method`, `server.address`, `url.scheme` |

See [HTTP Server](http-server.md) module documentation for more details.

### HTTP Client { #http-client }

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `http.client.duration` (`V120`), `http.client.request.duration` (`V123`) | `http_client_duration_milliseconds` (`V120`) / `http_client_request_duration_seconds` (`V123`) / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | `HTTP` client request duration | `V120`: `http.request.method`, `http.response.status_code`, `server.address`, `url.scheme`, `http.route`, `http.status_code`, `http.method`, `http.target`, `error.type`; `V123`: `http.request.method`, `http.response.status_code`, `server.address`, `url.scheme`, `http.route`, `http.status_code`, `error.type` |

See [HTTP Client](http-client.md) module documentation for more details.

### Database { #database }

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `database.client.request.duration` (`V120`), `db.client.request.duration` (`V123`) | `database_client_request_duration_milliseconds` (`V120`) / `db_client_request_duration_seconds` (`V123`) / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Database operation/query duration | `V120`: `pool`, `query.id`, `query.operation`, `error`; `V123`: `db.pool.name`, `db.statement`, `db.operation`, `error.type` |

See [Database](database-common.md) module documentation for more details.

### Kafka { #kafka }

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `messaging.receive.duration` | `messaging_receive_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Single message processing duration | `messaging.system`, `messaging.destination`, `messaging.operation`, `error.type` |
| `messaging.publish.duration` | `messaging_publish_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Message send duration | `messaging.system`, `messaging.destination`, `messaging.partition_id`, `error.type` |
| `messaging.process.batch.duration` | `messaging_process_batch_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Message batch processing duration | `messaging.system`, `messaging.destination`, `error.type` |
| `messaging.kafka.consumer.lag` | `messaging_kafka_consumer_lag` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Consumer lag per partition | `messaging.system`, `messaging.destination`, `messaging.partition_id`, `messaging.consumer_group` |

See [Kafka](kafka.md) module documentation for more details.

### gRPC Server { #grpc-server }

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `rpc.server.duration` | `rpc_server_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | gRPC server call processing duration | `rpc.service`, `rpc.method`, `rpc.status`, `error.type` |
| `rpc.server.requests_per_rpc` | `rpc_server_requests_per_rpc_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Number of requests received per RPC | `rpc.service`, `rpc.method` |
| `rpc.server.responses_per_rpc` | `rpc_server_responses_per_rpc_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Number of responses sent per RPC | `rpc.service`, `rpc.method` |

See [gRPC Server](grpc-server.md) module documentation for more details.

### gRPC Client { #grpc-client }

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `rpc.client.duration` | `rpc_client_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | gRPC client call duration | `rpc.service`, `rpc.method`, `rpc.status`, `error.type`, `server.address` |
| `rpc.client.requests_per_rpc` | `rpc_client_requests_per_rpc_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Number of requests sent per RPC | `rpc.service`, `rpc.method`, `server.address` |
| `rpc.client.responses_per_rpc` | `rpc_client_responses_per_rpc_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Number of responses received per RPC | `rpc.service`, `rpc.method`, `server.address` |

See [gRPC Client](grpc-client.md) module documentation for more details.

### SOAP Client { #soap-client }

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `rpc.client.duration` | `rpc_client_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | SOAP client call duration | `rpc.system`, `rpc.service`, `rpc.method`, `rpc.result`, `server.address`, `server.port` |

See [SOAP Client](soap-client.md) module documentation for more details.

### Scheduling { #scheduling }

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `scheduling.job.duration` | `scheduling_job_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Scheduled job execution duration | `code.class`, `code.function`, `error.type` |

See [Scheduling](scheduling.md) module documentation for more details.

### Cache { #cache }

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `cache.duration` | `cache_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | Cache operation duration (`GET`, `SET`, `DELETE`, and others) | `cache`, `operation`, `origin`, `status` |
| `cache.ratio` | `cache_ratio_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Cache hit/miss counter | `cache`, `origin`, `type` |
| `cache.hit`, `cache.miss` | `cache_hit_total`, `cache_miss_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Deprecated hit/miss counters kept for compatibility | `cache`, `origin` |

Standard `Micrometer` metrics are automatically registered when using `Caffeine`:

| Metric | Prometheus | Type | Description |
|--------|------------|------|-------------|
| `cache.gets` | `cache_gets_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Number of cache requests |
| `cache.puts` | `cache_puts_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Number of cache writes |
| `cache.evictions` | `cache_evictions_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Number of cache evictions |
| `cache.size` | `cache_size` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Current cache size |

See [Cache](cache.md) module documentation for more details.

### Redis / Lettuce { #redis-lettuce }

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `lettuce.command.completion.duration` | `lettuce_command_completion_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Redis command completion duration | `type`, `remote`, `local`, `command`, `error.type` |
| `lettuce.command.firstresponse.duration` | `lettuce_command_firstresponse_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Redis command first response duration | `type`, `remote`, `local`, `command`, `error.type` |

### Resilience { #resilience }

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

### JMS { #jms }

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `messaging.receive.duration` | `messaging_receive_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | JMS message receive duration | `messaging.system`, `messaging.destination.name`, `error.type` |

### S3 Client { #s3-client }

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `s3.client.duration` | `s3_client_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | S3 HTTP request duration | `aws.s3.bucket`, `aws.operation.name`, `error.type` |
| `s3.kora.client.duration` | `s3_kora_client_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Kora S3 client operation duration | `aws.client.name`, `aws.s3.bucket`, `aws.operation.name`, `error.type` |

See [S3 Client](s3-client.md) module documentation for more details.

### Camunda 7 BPMN { #camunda-7-bpmn }

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `camunda.engine.delegate.duration` | `camunda_engine_delegate_duration_milliseconds` / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | Camunda BPMN Java delegate execution duration | `delegate`, `business.key`, `error.type` |
| `camunda.engine.delegate.active_requests` | `camunda_engine_delegate_active_requests` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Number of active delegate executions | `delegate`, `business.key` |

See [Camunda 7 BPMN](camunda7-bpmn.md) module documentation for more details.

### Camunda REST { #camunda-rest }

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `camunda.rest.server.duration` (`V120`), `camunda.rest.server.request.duration` (`V123`) | `camunda_rest_server_duration_milliseconds` (`V120`) / `camunda_rest_server_request_duration_seconds` (`V123`) / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | `Camunda REST` request duration | `V120`: `http.request.method`, `http.response.status_code`, `http.route`, `server.address`, `url.scheme`, `http.target`, `http.method`, `http.status_code`; `V123`: `http.request.method`, `http.response.status_code`, `http.route`, `url.scheme`, `server.address`, `error.type` |
| `camunda.rest.server.active_requests` | `camunda_rest_server_active_requests` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Number of active Camunda REST requests | `http.route`, `http.request.method`, `server.address`, `url.scheme` |

See [Camunda 7 REST](camunda7-rest.md) module documentation for more details.

### Camunda 8 Worker { #camunda-8-worker }

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `zeebe.worker.handler` (`V120`), `zeebe.worker.handler.duration` (`V123`) | `zeebe_worker_handler_seconds` (`V120`) / `zeebe_worker_handler_duration_seconds` (`V123`) / `_count` / `_sum` / `_bucket` / `_max` | [DistributionSummary](https://docs.micrometer.io/micrometer/reference/concepts/distribution-summaries.html) | `Zeebe Worker` job handler duration | `job.name`, `job.type`, `status`, `error`, `error.code` |
| `zeebe.worker.handler` | `zeebe_worker_handler_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | `Zeebe Worker` error counter | `job.name`, `job.type`, `status`, `error.code` |
| `zeebe.client.worker.job` | `zeebe_client_worker_job_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Number of activated and handled `Zeebe` jobs | `action`, `type` |

See [Camunda 8 Worker](camunda8-worker.md) module documentation for more details.

### System { #system }

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `kora.up` | `kora_up` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Framework status indicator (value = 1) | `version` |

### JVM { #jvm }

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
