---
description: "Explains Kora metrics with Micrometer, Prometheus export through the system HTTP server, per-module telemetry.metrics configuration, registry and metric factory customization, and a full metric reference. Use when working with MetricsModule, MeterRegistry, MetricsScraper, PrometheusMeterRegistryInitializer, telemetry.metrics.enabled, httpServer.system.metricsPath, Metrics Reference."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora metrics with Micrometer, Prometheus export through the system HTTP server, the per-module telemetry.metrics block, registry and metric factory customization, and module-specific metric names and tags; key triggers include MetricsModule, MeterRegistry, MetricsScraper, PrometheusMeterRegistryInitializer, DefaultHttpServerMetricsFactory, telemetry.metrics.enabled, telemetry.metrics.slo, httpServer.system.metricsPath, Metrics Reference."
---

Module for collecting application metrics using [Micrometer](https://micrometer.io/docs/concepts#_purpose).
It creates a `PrometheusMeterRegistry`, registers it in the dependency container as a `MeterRegistry`, and exposes the collected values in the `Prometheus` format through the [system HTTP server](http-server.md#system-server).
This lets you collect application, `JVM`, process, and built-in integration metrics in one place and scrape them with an external observability system.

Publishing metrics requires the [system HTTP server](http-server.md#system-server), which exposes them in the [Prometheus](https://prometheus.io/docs/concepts/data_model/) format.

!!! warning "Module metrics are disabled by default"

    `TelemetryConfig.MetricsConfig#enabled` returns `false`, and every module inherits that default.
    An application that only connects `MetricsModule` starts fine and answers `/metrics` with `200`,
    but the response contains only `JVM`, process, and `kora.up` values — no `http_server_*`, `http_client_*`,
    `db_*` or any other component metric. Enable metrics explicitly per module with
    `<module>.telemetry.metrics.enabled = true`, see [Module metrics](#module-metrics).

For a step-by-step walkthrough before the reference details, see [Observability](../guides/observability.md).

## Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:micrometer-module"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends MetricsModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:micrometer-module")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : MetricsModule
    ```

`MetricsModule` lives in the `io.koraframework.micrometer.module` package.
It only provides the registry and the scrape endpoint contract — the metric values themselves are produced by the modules you connect
([HTTP server](http-server.md), [HTTP client](http-client.md), [Database](database-common.md), [Kafka](kafka.md) and so on).

## Configuration { #configuration }

The module itself has no configuration section: in Kora 2.0 there is no global `metrics { }` block.
Everything is configured in two places — the path and port of the scrape endpoint on the system server,
and a `telemetry.metrics` block inside each module that reports metrics.

Example of the system `HTTP` server path configuration described in the `SystemHttpServerConfig` class (default values are specified):

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
        system {
            port = 8085 //(1)!
            metricsPath = "/metrics" //(2)!
        }
    }
    ```

    1.  Port of the system `HTTP` server that serves the metrics endpoint (default: `8085`).
    2.  Path for retrieving metrics in the `Prometheus` format (default: `"/metrics"`).

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      system:
        port: 8085 #(1)!
        metricsPath: "/metrics" #(2)!
    ```

    1.  Port of the system `HTTP` server that serves the metrics endpoint (default: `8085`).
    2.  Path for retrieving metrics in the `Prometheus` format (default: `"/metrics"`).

### Module metrics { #module-metrics }

Each metric-collecting module exposes a `telemetry.metrics` block described in `TelemetryConfig.MetricsConfig`,
letting you turn metrics on, tune histogram buckets, and attach extra tags for that module only.
The example below uses the [HTTP server](http-server.md) module as the host, but the same `telemetry.metrics` fields apply verbatim to
[HTTP client](http-client.md), [Database](database-common.md), [Kafka](kafka.md), [gRPC server](grpc-server.md),
[gRPC client](grpc-client.md), [Scheduling](scheduling.md), [Cache](cache.md), [Resilience](resilient.md),
and every other integration that reports metrics:

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

    1.  Enables metric collection for the module (default: `false`)
    2.  [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) histogram buckets for `Timer` metrics, a list of durations (default: `TelemetryConfig.MetricsConfig#DEFAULT_SLO`, listed in [Personalization](#personalization))
    3.  Extra common tags added to every metric the module reports (default: `{}`)

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

    1.  Enables metric collection for the module (default: `false`)
    2.  [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) histogram buckets for `Timer` metrics, a list of durations (default: `TelemetryConfig.MetricsConfig#DEFAULT_SLO`, listed in [Personalization](#personalization))
    3.  Extra common tags added to every metric the module reports (default: `{}`)

`slo` values are durations: a string carries its unit (`"1ms"`, `"250ms"`, `"1s"`, `PT1S`), a bare number is read as milliseconds,
so `slo = [1, 10, 50]` and `slo = ["1ms", "10ms", "50ms"]` are the same list.

Leaving `enabled = false` (the default) means the module's telemetry uses a `Noop` metrics factory: no `Meter` is created and nothing is registered in the registry.
That is also the way to silence a noisy integration after you have enabled metrics globally.

Metrics are only produced when **both** conditions hold: `MetricsModule` is connected (so a `MeterRegistry` exists in the container)
and the module's `telemetry.metrics.enabled` is `true`. If either is missing, the module falls back to a no-op telemetry implementation.

### Configuration paths { #configuration-paths }

The `telemetry.metrics` block is nested under the module's own configuration section:

| Module | Configuration path |
|--------|--------------------|
| [HTTP server](http-server.md) (public) | `httpServer.telemetry.metrics` |
| [HTTP server](http-server.md#system-server) (system) | `httpServer.system.telemetry.metrics` |
| [HTTP client](http-client.md) | `httpClient.telemetry.metrics` and the client's own `@HttpClient` configuration path |
| [JDBC database](database-jdbc.md) | `jdbc.telemetry.metrics` |
| [Cassandra database](database-cassandra.md) | `cassandra.telemetry.metrics` |
| [gRPC server](grpc-server.md) | `grpcServer.telemetry.metrics` |
| [gRPC client](grpc-client.md) | `grpcClient.<ServiceName>.telemetry.metrics` |
| [Scheduling](scheduling.md) | `scheduling.telemetry.metrics` |
| [Resilience](resilient.md) | `resilient.telemetry.{circuitBreaker,retry,timeout,fallback,rateLimiter}.metrics` |
| [Kafka](kafka.md) | the consumer's or publisher's own configuration path plus `.telemetry.metrics` |
| [Cache](cache.md) | the cache's `@Cache` configuration path plus `.telemetry.metrics` |
| [S3 client](s3-client.md) | `s3client.aws.telemetry.metrics` |
| Redis (`Lettuce`) | `lettuce.telemetry.metrics` |
| [Camunda 7 BPMN](camunda7-bpmn.md) | `camunda.engine.bpmn.telemetry.metrics` |
| [Camunda 7 REST](camunda7-rest.md) | `camunda.rest.telemetry.metrics` |
| [Camunda 8 worker](camunda8-worker.md) | `zeebe.worker.telemetry.metrics` |

Some modules add their own keys next to `enabled` / `slo` / `tags`:

- [Database](database-common.md) — `driverMetrics` (default: `true`) registers the `HikariCP` pool metrics of the connection pool in the same registry.
- [Kafka](kafka.md) — `driverMetrics` (default: `false`) registers the native `Kafka` client metrics through Micrometer's `KafkaClientMetrics` binder, under the `kafka.*` name prefix.
- [Camunda 7 BPMN](camunda7-bpmn.md) — `engineMetrics` (default: `false`) enables the `Camunda` engine's own metrics.

Metric collection parameters are also described in the modules that collect metrics: [HTTP server](http-server.md), [HTTP client](http-client.md), [gRPC server](grpc-server.md), [gRPC client](grpc-client.md), [Scheduling](scheduling.md), [Cache](cache.md), and other integrations.

## Usage { #usage }

Kora follows the notation described in the [`Prometheus` specification](https://prometheus.io/docs/concepts/data_model/).

After the module is connected, `PrometheusMeterRegistry` is created, registered in `Metrics.globalRegistry`, and used by all components that collect metrics.
When the application stops, this registry is removed from `Metrics.globalRegistry` and closed.

The registry is provided by the `PrometheusMeterRegistryWrapper` component, which is a `Root` component and implements `Wrapped<MeterRegistry>`,
so user code injects the `MeterRegistry` contract:

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

The registry automatically gets standard `Micrometer` binders: `ClassLoaderMetrics`, `JvmMemoryMetrics`, `JvmGcMetrics`, `ProcessorMetrics`, `JvmThreadMetrics`, `FileDescriptorMetrics`, `UptimeMetrics`.
These are bound when the registry is created and do **not** depend on any `telemetry.metrics.enabled` flag.
Kora also registers the `kora.up` metric with value `1` and the `version` tag.

Kora additionally bridges the `Micrometer` registry to an `OpenTelemetry` `MeterProvider` (`MicrometerMeterProvider` from `io.opentelemetry.contrib.metrics.micrometer`), so libraries instrumented with the `OpenTelemetry` metrics API publish through the same registry.
The bridge is a `@DefaultComponent` and accepts an optional `CallbackRegistrar` component if you need to control how asynchronous instruments are polled.

A runnable baseline that wires `MetricsModule` alongside `HoconConfigModule`, `LogbackModule`, `JdbcDatabaseModule`, `UndertowPublicHttpServerModule`, and the `OpenTelemetry` tracing exporter is available in the [kora-java-telemetry](https://github.com/kora-projects/kora-examples/tree/master/examples/java/kora-java-telemetry) example.

### Prometheus export { #prometheus-export }

Metrics are exposed in the [Prometheus](https://prometheus.io/docs/concepts/data_model/) text format by the [system HTTP server](http-server.md#system-server) on `httpServer.system.metricsPath` (default `/metrics`) served at `httpServer.system.port` (default `8085`):

```shell
curl http://localhost:8085/metrics
```

Point your `Prometheus` scrape target (or any compatible collector) at the same host, port, and path.

The endpoint always answers `200`. What it returns depends on what is bound in the container:

- `MetricsModule` connected — the `Prometheus` text exposition of the registry snapshot.
- `MetricsModule` not connected — the body `# Metric Scraper disabled`, because no `MetricsScraper` component exists.
- A custom `MeterRegistry` that is not a `PrometheusMeterRegistry` — an empty body, because that registry cannot be scraped in the `Prometheus` format.
  Provide your own `MetricsScraper` implementation in that case: it overrides the `@DefaultComponent` supplied by `MetricsModule`.

`MetricsScraper` is a single-method contract from the `io.koraframework.telemetry.common` package:

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

### Custom metric { #custom-metric }

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
All initializers found in the container are applied in sequence, each receiving the result of the previous one.

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

        fun commonTagsInit(): PrometheusMeterRegistryInitializer {
            return PrometheusMeterRegistryInitializer {
                it.config().commonTags("tag", "value")
                it
            }
        }
    }
    ```

Standard metrics also have their own settings, for example the `slo` histogram buckets for `Timer` metrics, configured per module under [`telemetry.metrics`](#module-metrics).
When `slo` is not overridden, `TelemetryConfig.MetricsConfig#DEFAULT_SLO` is used — 14 buckets:

`1ms`, `10ms`, `50ms`, `100ms`, `200ms`, `500ms`, `1s`, `2s`, `5s`, `10s`, `20s`, `30s`, `60s`, `90s`

The array is declared in `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig` and shared by every module that builds a `Timer`.

### Metric factories { #metrics-factory }

The names and tags of framework metrics are produced by per-module metric factories, one `Default<Module>MetricsFactory` class per integration
(package `<module>.telemetry.impl`). Each module's telemetry factory accepts that class as an **optional** dependency,
so supplying your own subclass as a container component replaces the default one:

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

    1.  The factory is picked up by `HttpServerModule#defaultHttpServerTelemetryFactory` in place of the built-in `DefaultHttpServerMetricsFactory`
    2.  Only static tags may be added in the builder — a tag whose value varies per request must be part of the metric key, otherwise different tag sets collide on one `Meter`

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

    1.  The factory is picked up by `HttpServerModule#defaultHttpServerTelemetryFactory` in place of the built-in `DefaultHttpServerMetricsFactory`
    2.  Only static tags may be added in the builder — a tag whose value varies per request must be part of the metric key, otherwise different tag sets collide on one `Meter`

The same pattern applies to every integration, the class name follows the module:
`DefaultHttpClientMetricsFactory`, `DefaultDatabaseMetricsFactory`, `DefaultKafkaConsumerMetricsFactory`, `DefaultKafkaPublisherMetricsFactory`,
`DefaultGrpcServerMetricsFactory`, `DefaultGrpcClientMetricsFactory`, `DefaultSoapClientMetricsFactory`, `DefaultSchedulingMetricsFactory`,
`DefaultCaffeineCacheMetricsFactory`, `DefaultRedisCacheMetricsFactory`, `DefaultCircuitBreakerMetricsFactory`, `DefaultRetryMetricsFactory`,
`DefaultTimeoutMetricsFactory`, `DefaultFallbackMetricsFactory`, `DefaultRateLimiterMetricsFactory`, `DefaultAwsS3ClientMetricsFactory`,
`DefaultJmsConsumerMetricsFactory`.

When a tag has to depend on the current request, add it to the metric key instead of the builder:
every factory exposes `create<Metric>Key(...)` methods and key records with a `withExtraTags(Tags)` copy method for exactly that purpose.

If the extra tags are the same for every metric of a module, do not write a factory at all — use the [`telemetry.metrics.tags`](#module-metrics) configuration key.

## Standard { #standard }

All Kora metrics follow the [OpenTelemetry semantic conventions](https://opentelemetry.io/docs/specs/semconv/) for names and tags,
and each module uses exactly one naming scheme — there is no configurable specification version.
Tag keys come from the `io.opentelemetry.semconv` attribute constants, so for example an `HTTP` server metric carries
`http.request.method`, `http.route`, `url.scheme`, `server.address` and `error.type`.

The `Prometheus` exposition names are derived from the `Micrometer` name by the `Prometheus` naming convention:

- `.` is replaced with `_`;
- a `Timer` gets the `_seconds` suffix, and the histogram is exposed as `_bucket` / `_count` / `_sum` series plus a separate `_max` gauge;
- a `Counter` gets its base unit and the `_total` suffix (metrics built with `BaseUnits.OPERATIONS` therefore end with `_operations_total`);
- a `Gauge` gets its base unit as the suffix, if the metric declares one.

The `error.type` tag is always present on metrics that can fail — it holds the canonical exception class name, or an empty string on success.

## Metrics reference { #metrics-reference }

[Micrometer](https://docs.micrometer.io/micrometer/reference/concepts.html) metric types used:

- [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) — operation duration with count, sum, max, and histogram bucket support
- [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) — monotonically increasing counter
- [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) — current metric value

Every metric listed below additionally carries the tags configured in that module's [`telemetry.metrics.tags`](#module-metrics).

### HTTP server { #http-server }

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `http.server.request.duration` | `http_server_request_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | `HTTP` server request processing duration | `server.name`, `server.port`, `http.request.method`, `http.route`, `url.scheme`, `server.address`, `error.type` |
| `http.server.active_requests` | `http_server_active_requests` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Number of active `HTTP` requests | `server.name`, `server.port`, `http.request.method`, `http.route`, `url.scheme`, `server.address` |

`server.name` distinguishes the public server (`kora-undertow`) from the system one (`kora-undertow-system`); a request that matched no route reports `http.route` as `UNKNOWN_ROUTE`.

See [HTTP server](http-server.md) module documentation for more details.

### HTTP client { #http-client }

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `http.client.request.duration` | `http_client_request_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | `HTTP` client request duration | `http.request.method`, `http.response.status_code`, `server.address`, `url.scheme`, `http.route`, `error.type`, `system.config`, `system.name.simple`, `system.name.canonical` |

`system.config` is the client's configuration path, `system.name.simple` and `system.name.canonical` are the simple and canonical names of the declarative client interface.

See [HTTP client](http-client.md) module documentation for more details.

### Database { #database }

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `db.client.operation.duration` | `db_client_operation_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | Database operation/query duration | `db.client.connection.pool.name`, `db.system.name`, `db.query.text`, `db.operation.name`, `error.type` |

`db.system.name` is taken from the connection string for [JDBC](database-jdbc.md) (`postgresql`, `mysql`, ...) and is `cassandra` for [Cassandra](database-cassandra.md).
`db.query.text` holds the query identifier, not the raw `SQL` text.

With `telemetry.metrics.driverMetrics = true` (the default), the connection pool also registers its own metrics in the same registry:
`HikariCP` pool metrics for [JDBC](database-jdbc.md), and the `DataStax` driver metrics selected by `cassandra.telemetry.metrics` for [Cassandra](database-cassandra.md).

See [Database](database-common.md) module documentation for more details.

### Kafka { #kafka }

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `messaging.process.duration` | `messaging_process_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | Single message processing duration | `messaging.system`, `messaging.client.id`, `messaging.consumer.group.name`, `messaging.destination.name`, `messaging.destination.partition.id`, `error.type`, `system.config`, `system.name.simple`, `system.name.canonical` |
| `messaging.process.batch.duration` | `messaging_process_batch_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | Message batch processing duration | `messaging.system`, `messaging.client.id`, `messaging.consumer.group.name`, `error.type`, `system.config`, `system.name.simple`, `system.name.canonical` |
| `messaging.kafka.consumer.lag` | `messaging_kafka_consumer_lag` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Consumer lag per partition | `messaging.system`, `messaging.client.id`, `messaging.consumer.group.name`, `messaging.destination.name`, `messaging.destination.partition.id`, `system.config`, `system.name.simple`, `system.name.canonical` |
| `messaging.client.operation.duration` | `messaging_client_operation_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | Message send duration | `messaging.system`, `messaging.client.id`, `messaging.operation.type`, `messaging.destination.name`, `messaging.destination.partition.id`, `error.type`, `system.config`, `system.name.simple`, `system.name.canonical` |
| `messaging.client.sent.messages` | `messaging_client_sent_messages_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Number of sent messages | `messaging.system`, `messaging.client.id`, `messaging.operation.type`, `messaging.destination.name`, `messaging.destination.partition.id`, `error.type`, `system.config`, `system.name.simple`, `system.name.canonical` |

`messaging.system` is always `kafka`; `messaging.operation.type` on the publisher side is `send`.

See [Kafka](kafka.md) module documentation for more details.

### gRPC server { #grpc-server }

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `rpc.server.duration` | `rpc_server_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | gRPC server call processing duration | `server.name`, `server.port`, `rpc.system`, `rpc.service`, `rpc.method`, `rpc.grpc.status_code` |

See [gRPC server](grpc-server.md) module documentation for more details.

### gRPC client { #grpc-client }

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `rpc.client.duration` | `rpc_client_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | gRPC client call duration | `rpc.system`, `rpc.service`, `rpc.method`, `rpc.grpc.status_code`, `server.address`, `server.port`, `error.type` |

`rpc.system` is `grpc` for both the gRPC server and the gRPC client.

See [gRPC client](grpc-client.md) module documentation for more details.

### SOAP client { #soap-client }

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `rpc.client.duration` | `rpc_client_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | SOAP client call duration | `rpc.system`, `rpc.service`, `rpc.method`, `server.address`, `server.port`, `http.response.status_code`, `error.type`, `fault.code`, `system.config`, `system.name.simple`, `system.name.canonical` |

`rpc.system` is `soap`; `fault.code` holds the `SOAP` fault code and is empty when the call did not return a fault.

See [SOAP client](soap-client.md) module documentation for more details.

### Scheduling { #scheduling }

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `scheduling.job.duration` | `scheduling_job_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | Scheduled job execution duration | `code.function.name`, `system.name.simple`, `system.name.canonical`, `error.type`, and `system.config` when the job declares a configuration path |

See [Scheduling](scheduling.md) module documentation for more details.

### Cache { #cache }

Distributed `Redis` caches report their own operation metrics:

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `cache.operation.duration` | `cache_operation_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | Cache operation duration (`GET`, `PUT`, `INVALIDATE`, and others) | `origin`, `operation`, `error.type`, `system.config`, `system.name.simple`, `system.name.canonical` |
| `cache.ratio` | `cache_ratio_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Cache hit/miss counter | `origin`, `operation`, `type`, `system.config`, `system.name.simple`, `system.name.canonical` |

`origin` is `redis`, `operation` is the `Cache` contract operation name, and `type` on `cache.ratio` is `hit` or `miss`.

`Caffeine` caches do not report `cache.operation.duration` and `cache.ratio` — their telemetry delegates to the standard `Micrometer` cache binders,
which are attached to the underlying cache when `telemetry.metrics.enabled = true`:

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `cache.gets` | `cache_gets_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Number of cache lookups | `cache`, `result` (`hit` / `miss`) |
| `cache.puts` | `cache_puts_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Number of cache writes | `cache` |
| `cache.evictions` | `cache_evictions_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Number of evicted entries | `cache` |
| `cache.eviction.weight` | `cache_eviction_weight_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Total weight of evicted entries | `cache` |
| `cache.loads` | `cache_loads_seconds` / `_count` / `_sum` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | Cache value load duration | `cache`, `result` (`success` / `failure`) |
| `cache.size` | `cache_size` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Current cache size | `cache` |

All `Caffeine` metrics carry the `cache` tag holding the cache name plus the tags from `telemetry.metrics.tags`.

See [Cache](cache.md) module documentation for more details.

### Redis / Lettuce { #redis-lettuce }

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `lettuce.command.completion.duration` | `lettuce_command_completion_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | Redis command completion duration | `type`, `remote`, `command`, `error.type` |
| `lettuce.command.firstresponse.duration` | `lettuce_command_firstresponse_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | Redis command first response duration | `type`, `remote`, `command`, `error.type` |

`type` distinguishes the client kind, `remote` is the address of the `Redis` node, `command` is the `Redis` command name.
On these two metrics `error.type` holds the `Redis` error text rather than an exception class name.

### Resilience { #resilience }

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `resilient.circuitbreaker.state` | `resilient_circuitbreaker_state` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Circuit breaker state (0=CLOSED, 1=HALF_OPEN, 2=OPEN) | `name` |
| `resilient.circuitbreaker.transition` | `resilient_circuitbreaker_transition_operations_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Transitions into `OPEN` and `HALF_OPEN` | `name`, `state` |
| `resilient.circuitbreaker.call.acquire` | `resilient_circuitbreaker_call_acquire_operations_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Calls admitted in `HALF_OPEN` and calls rejected in `OPEN` | `name`, `state`, `status` |
| `resilient.circuitbreaker.call.result` | `resilient_circuitbreaker_call_result_operations_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Call outcomes registered by the circuit breaker | `name`, `state`, `status` |
| `resilient.retry.attempts` | `resilient_retry_attempts_operations_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Number of retry attempts | `name` |
| `resilient.retry.exhausted` | `resilient_retry_exhausted_operations_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Number of exhausted retries | `name`, `reason` |
| `resilient.timeout.exhausted` | `resilient_timeout_exhausted_operations_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Number of timeouts | `name` |
| `resilient.fallback.attempts` | `resilient_fallback_attempts_operations_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Number of fallback invocations | `name`, `type` |
| `resilient.ratelimiter.acquire` | `resilient_ratelimiter_acquire_operations_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Rate limiter permit acquisitions | `name`, `status` |

Tag values: `status` is `PERMITTED` / `REJECTED` / `DISABLED` on `call.acquire` and `SUCCESS` / `FAILURE` / `IGNORED_FAILURE` / `FALLBACK` on `call.result`;
`reason` is `EXHAUSTED_ATTEMPTS` or `EXHAUSTED_BUDGET`; the rate limiter's `status` is `acquired` or `rejected`; the fallback's `type` is `executed`.

See [Resilience](resilient.md) module documentation for more details.

### JMS { #jms }

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `messaging.receive.duration` | `messaging_receive_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | JMS message receive duration | `messaging.system`, `messaging.destination.name`, `error.type` |

`messaging.system` is always `jms`.

### S3 client { #s3-client }

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `rpc.client.duration` | `rpc_client_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | S3 client operation duration | `rpc.system`, `rpc.method`, `aws.s3.bucket`, `error.type`, `system.path`, `system.name.simple`, `system.name.canonical` |

`rpc.system` is `s3-aws` for the `AWS` based client. `rpc.method` is the S3 operation name and `system.path` is the client's configuration path.

See [S3 client](s3-client.md) module documentation for more details.

### Camunda 7 BPMN { #camunda-7-bpmn }

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `camunda.engine.delegate.duration` | `camunda_engine_delegate_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | Camunda BPMN Java delegate execution duration | `delegate`, `error.type` |

The engine's own metrics are published separately and require `camunda.engine.bpmn.telemetry.metrics.engineMetrics = true`.

See [Camunda 7 BPMN](camunda7-bpmn.md) module documentation for more details.

### Camunda REST { #camunda-rest }

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `camunda.rest.request.duration` | `camunda_rest_request_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | `Camunda REST` request duration | `http.request.method`, `http.response.status_code`, `http.route`, `url.scheme`, `server.address`, `http.response.result_code`, `error.type` |
| `camunda.rest.active_requests` | `camunda_rest_active_requests` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Number of active Camunda REST requests | `http.request.method`, `http.route`, `url.scheme`, `server.address` |

See [Camunda 7 REST](camunda7-rest.md) module documentation for more details.

### Camunda 8 worker { #camunda-8-worker }

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `zeebe.worker.handler.duration` | `zeebe_worker_handler_duration_seconds` / `_count` / `_sum` / `_bucket` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | `Zeebe Worker` job handler duration | `job.name`, `job.type`, `error.type` |

The `Camunda` client additionally publishes its own worker job metrics into the same registry, tagged with the job `type`.

See [Camunda 8 worker](camunda8-worker.md) module documentation for more details.

### System { #system }

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `kora.up` | `kora_up` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Framework status indicator (value = 1) | `version` |

### JVM { #jvm }

Standard `JVM` and process metrics are collected automatically by the [Micrometer](https://docs.micrometer.io/micrometer/reference/concepts.html) binders bound to the registry at startup.
They do not depend on any module's `telemetry.metrics.enabled` setting:

| Metric | Prometheus | Type | Description | Tags |
|--------|------------|------|-------------|------|
| `jvm.memory.used` | `jvm_memory_used_bytes` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Used memory | `area`, `id` |
| `jvm.memory.committed` | `jvm_memory_committed_bytes` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Committed JVM memory | `area`, `id` |
| `jvm.memory.max` | `jvm_memory_max_bytes` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Max available memory | `area`, `id` |
| `jvm.buffer.count` | `jvm_buffer_count_buffers` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Number of buffers in the pool | `id` |
| `jvm.buffer.memory.used` | `jvm_buffer_memory_used_bytes` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Memory used by buffers | `id` |
| `jvm.buffer.total.capacity` | `jvm_buffer_total_capacity_bytes` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Total buffer pool capacity | `id` |
| `jvm.gc.pause` | `jvm_gc_pause_seconds` / `_count` / `_sum` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | GC pause duration | `gc`, `action`, `cause` |
| `jvm.gc.concurrent.phase.time` | `jvm_gc_concurrent_phase_time_seconds` / `_count` / `_sum` / `_max` | [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) | Concurrent GC phase duration | `gc`, `action`, `cause` |
| `jvm.gc.memory.allocated` | `jvm_gc_memory_allocated_bytes_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Allocated memory size | — |
| `jvm.gc.memory.promoted` | `jvm_gc_memory_promoted_bytes_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Memory promoted to old gen (generational collectors only) | — |
| `jvm.gc.max.data.size` | `jvm_gc_max_data_size_bytes` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Max old gen size | — |
| `jvm.gc.live.data.size` | `jvm_gc_live_data_size_bytes` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Old gen size after full GC | — |
| `jvm.threads.live` | `jvm_threads_live_threads` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Number of live threads | — |
| `jvm.threads.daemon` | `jvm_threads_daemon_threads` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Number of daemon threads | — |
| `jvm.threads.peak` | `jvm_threads_peak_threads` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Peak thread count | — |
| `jvm.threads.started` | `jvm_threads_started_threads_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Number of started threads | — |
| `jvm.threads.states` | `jvm_threads_states_threads` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Thread count by state | `state` |
| `jvm.classes.loaded` | `jvm_classes_loaded_classes` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Number of currently loaded classes | — |
| `jvm.classes.loaded.count` | `jvm_classes_loaded_count_classes_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Number of classes loaded since start | — |
| `jvm.classes.unloaded` | `jvm_classes_unloaded_classes_total` | [Counter](https://docs.micrometer.io/micrometer/reference/concepts/counters.html) | Number of unloaded classes | — |
| `process.cpu.usage` | `process_cpu_usage` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Process CPU usage | — |
| `system.cpu.usage` | `system_cpu_usage` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | System CPU usage | — |
| `system.cpu.count` | `system_cpu_count` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Number of available processors | — |
| `system.load.average.1m` | `system_load_average_1m` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | System load average over one minute | — |
| `process.files.open` | `process_files_open_files` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Number of open file descriptors | — |
| `process.files.max` | `process_files_max_files` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Max file descriptors | — |
| `process.uptime` | `process_uptime_seconds` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Process uptime | — |
| `process.start.time` | `process_start_time_seconds` | [Gauge](https://docs.micrometer.io/micrometer/reference/concepts/gauges.html) | Process start time since the Unix epoch | — |

Some of these are registered only when the running `JVM` and operating system expose the corresponding `MXBean` value, so the exact set of series in a scrape depends on the platform.
