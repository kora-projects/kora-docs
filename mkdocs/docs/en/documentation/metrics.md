Module for collecting application metrics using [Micrometer](https://micrometer.io/docs/concepts#_purpose).

Requires a [HTTP server](http-server.md) connection to provide metrics in [prometheus](https://prometheus.io/docs/concepts/data_model/) format.

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

By default, the method to get metrics in `prometheus` format is available at the `/metrics` path, but the path can be customized through configuration:

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
        privateApiHttpMetricsPath = "/metrics"
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      privateApiHttpMetricsPath: "/metrics"
    ```

Metrics collection configuration parameters are described in modules where metrics collection is present, e.g. [HTTP server](http-server.md), [HTTP client](http-client.md), etc.

## Usage

We follow and you are encouraged to use the notation described in the [specification](https://prometheus.io/docs/concepts/data_model/).

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
