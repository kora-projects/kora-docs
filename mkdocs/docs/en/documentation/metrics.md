Module for collecting application metrics using [Micrometer](https://micrometer.io/docs/concepts#_purpose).

Requires [HTTP server](http-server.md) module added to provide metrics in [prometheus](https://prometheus.io/docs/concepts/data_model/) format.

## Dependency

=== ":fontawesome-brands-java: `Java`"

    Dependency `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:micrometer-module"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends MetricsModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Dependency `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:micrometer-module")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : MetricsModule
    ```

## Configuration

Configuration described in the `HttpServerConfig` class:

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

Configuration described in the `MetricsConfig` class:

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

=== ":fontawesome-brands-java: `Java`"

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

The original metrics format used the OpenTelemetry `V120` standard, after Kora `1.1.0` it became possible to provide metrics in the OpenTelemetry `V123` standard.
in the OpenTelemetry `V123` standard, a partial list of changes can be seen [in the OpenTelemetry documentation](https://opentelemetry.io/blog/2023/http-conventions-declared-stable/)
and [OpenTelemetry migration guidelines](https://opentelemetry.io/docs/specs/semconv/http/migration-guide/)
