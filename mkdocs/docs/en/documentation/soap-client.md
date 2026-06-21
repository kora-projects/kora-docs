---
description: "Explains Kora SOAP client setup, SOAP client configuration, usage patterns, generated clients, and wsdl2java Gradle plugin integration. Use when working with SoapClientModule, @SoapClient, wsdl2java, JAX-WS, SOAPAction, WebServiceClient."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora SOAP client setup, SOAP client configuration, usage patterns, generated clients, and wsdl2java Gradle plugin integration; key triggers include SoapClientModule, @SoapClient, wsdl2java, JAX-WS, SOAPAction, WebServiceClient."
---

`SOAP` is a protocol for exchanging `XML` messages, often used for integration with external systems over `HTTP` and a `WSDL` contract.
The `soap-client` module creates client implementations for interfaces annotated with `javax.jws.WebService` or `jakarta.jws.WebService` and registers them in the application graph.

Usually, such interfaces and related `JAXB` classes are generated from `WSDL`, for example with `wsdl2java`.
After generation, Kora creates the client implementation and connects it to an `HTTP client`, `XML` mapping, and telemetry.

## Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:soap-client"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends SoapClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:soap-client")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : SoapClientModule
    ```

**Requires** an [`HTTP client`](http-client.md) implementation, for example `http-client-ok`.

## Description { #description }

The application is expected to already have interfaces annotated with `javax.jws.WebService` or `jakarta.jws.WebService`.
They can be written manually, but are usually created from `WSDL` by a separate tool, for example a [Gradle plugin](#wsdl2java-plugin).

Based on such interfaces, Kora creates SOAP client implementations with the `SoapClientImpl` suffix in the same package.
It also creates a module with the `SoapClientModule` suffix that registers the configuration and the client itself in the application graph.

After that, the configuration and the `SOAP client` become available for dependency injection automatically.

## Configuration { #configuration }

All configurations for `SOAP clients` are created with the `soapClient` prefix.
The main part of the client configuration is placed under the service name from the `@WebService` annotation.

The section name is selected in this order:

1. `name` from `@WebService`
2. `serviceName` from `@WebService`
3. `portName` from `@WebService`
4. interface name

A `SOAP client` named `SimpleService` will have the `soapClient.SimpleService` configuration path.

Example of the complete configuration described by the `SoapServiceConfig` class:

===! ":material-code-json: `Hocon`"

    ```javascript
    soapClient {
        SimpleService {
            url = "https://localhost:8090" //(1)!
            timeout = "60s" //(2)!
            telemetry {
                logging {
                    enabled = false //(3)!
                }
                metrics {
                    enabled = true //(4)!
                    slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(5)!
                    tags = { // (6)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
                tracing {
                    enabled = true //(7)!
                    attributes = { // (8)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
            }
        }
    }
    ```

    1. Service `URL` where requests will be sent (required, default: not specified).
    2. Maximum request execution time (default: `60s`).
    3. Enables module logging (default: `false`).
    4. Enables module metrics (default: `true`).
    5. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for the [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metric (default: `TelemetryConfig.MetricsConfig.DEFAULT_SLO`).
    6. Additional tags for metrics (default: `{}`).
    7. Enables module tracing (default: `true`).
    8. Additional attributes for tracing (default: `{}`).

=== ":simple-yaml: `YAML`"

    ```yaml
    soapClient:
      SimpleService:
        url: "https://localhost:8090" #(1)!
        timeout: "60s" #(2)!
        telemetry:
          logging:
            enabled: false #(3)!
          metrics:
            enabled: true #(4)!
            slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(5)!
            tags: #(6)!
              key1: value1
              key2: value2
          tracing:
            enabled: true #(7)!
            attributes: #(8)!
              key1: value1
              key2: value2
    ```

    1. Service `URL` where requests will be sent (required, default: not specified).
    2. Maximum request execution time (default: `60s`).
    3. Enables module logging (default: `false`).
    4. Enables module metrics (default: `true`).
    5. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for the [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metric (default: `TelemetryConfig.MetricsConfig.DEFAULT_SLO`).
    6. Additional tags for metrics (default: `{}`).
    7. Enables module tracing (default: `true`).
    8. Additional attributes for tracing (default: `{}`).

Module metrics are described in the [Metrics Reference](metrics.md#soap-client) section.

The `SOAP client` uses the connected `HttpClient` and sends requests to the address from the `url` parameter.
If a method has `action` set in `@WebMethod`, the client adds the `SOAPAction` HTTP header.
If the server returns `SOAP Fault`, the client converts it to an exception.

## Usage { #usage }

After all components are created, the `SOAP client` becomes available for injection.
Below is an example for the `SimpleService` client:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final SimpleService service;

        public SomeService(SimpleService service) {
            this.service = service;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(val service: SimpleService) {

    }
    ```

## `wsdl2java` Plugin { #wsdl2java-plugin }

A [Gradle plugin](https://github.com/bjornvester/wsdl2java-gradle-plugin) can be used as one option for creating interfaces annotated with `javax.jws.WebService` or `jakarta.jws.WebService`,
as well as `JAXB` classes based on `WSDL`.

### Dependency { #dependency-2 }

===! ":fontawesome-brands-java: `Java`"

    Plugin `build.gradle`:
    ```groovy
    plugins {
        id "com.github.bjornvester.wsdl2java" version "2.0.2"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Plugin `build.gradle.kts`:
    ```groovy
    plugins {
        id("com.github.bjornvester.wsdl2java") version ("2.0.2")
    }
    ```

### Usage { #usage-2 }

Suppose there is a `WSDL` where the `SimpleService` service is declared.
Then the plugin configuration for generation with `jakarta` annotations will look like this:

===! ":fontawesome-brands-java: `Java`"

    Plugin setup `build.gradle`:
    ```groovy
    wsdl2java {
        cxfVersion = "4.0.2"
        wsdlDir = layout.projectDirectory.dir("src/main/resources/wsdl")
        useJakarta = true
        markGenerated = true
        verbose = false
        packageName = "ru.tinkoff.kora.generated.soap"
        generatedSourceDir.set(layout.buildDirectory.dir("generated/sources/wsdl2java/java"))
        includesWithOptions = [
            "**/simple-service.wsdl": ["-wsdlLocation", "https://kora.tinkoff.ru/simple/service?wsdl"],
        ]
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Plugin setup `build.gradle.kts`:
    ```groovy
    wsdl2java {
        cxfVersion = "4.0.2"
        wsdlDir = layout.projectDirectory.dir("src/main/resources/wsdl")
        useJakarta = true
        markGenerated = true
        verbose = false
        packageName = "ru.tinkoff.kora.generated.soap"
        generatedSourceDir.set(layout.buildDirectory.dir("generated/sources/wsdl2java/java"))
        includesWithOptions.putAll(
            mapOf(
                "**/simple-service.wsdl" to listOf(
                    "-wsdlLocation",
                    "https://kora.tinkoff.ru/simple/service?wsdl"
                )
            )
        )
    }
    ```
