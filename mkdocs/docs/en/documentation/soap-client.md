A module for creating and registering SOAP services by classes annotated `javax.jws.WebService`/`jakarta.jws.WebService`.

## Dependency

===! ":fontawesome-brands-java: `Java`"

    Dependency `build.gradle`:
    ```groovy
    annotationProcessor "ru.tinkoff.kora:annotation-processors"
    implementation "ru.tinkoff.kora:soap-client"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends SoapClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Dependency `build.gradle.kts`:
    ```groovy
    ksp("ru.tinkoff.kora:symbol-processors")
    implementation("ru.tinkoff.kora:soap-client")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : SoapClientModule
    ```

**Requires** the [HTTP client](http-client.md) implementation to be connected.

## Description

It is understood that we have classes annotated with `javax.jws.WebService`/`jakarta.jws.WebService` that can be created by other means,
such as [Gradle Plugin](#plugin-wsdl2java).

Based on such classes, Kora is used to create SOAP client implementations with the Impl suffix in the same package and register them as a module with config.

Then the configuration and the SOAP service itself become available for dependency injection automatically.

## Configuration

All configurations for SOAP clients are created with the prefix `soapClient`,
and the bulk of the client configuration is under the client name from the WSDL annotation `@WebService`,
which corresponds often to the `<wsdl:binding type="tns:SimpleService">` tag in the WSDL configuration.

SOAP service named `SimpleService` will have a configuration with the path `soapClient.SimpleService`.

Example of the complete configuration described in the `SoapServiceConfig` class (default or example values are specified):

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
                }
                tracing {
                    enabled = true //(6)!
                }
            }
        }
    }
    ```

    1. URL of the service where requests will be sent (**required**)
    2. Maximum request time
    3. Enables module logging (default `false`)
    4. Enables module metrics (default `true`)
    5. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    6. Enables module tracing (default `true`)

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
          telemetry:
            enabled: true #(6)!
    ```

    1. URL of the service where requests will be sent (**required**)
    2. Maximum request time
    3. Enables module logging (default `false`)
    4. Enables module metrics (default `true`)
    5. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    6. Enables module tracing (default `true`)

## Usage

Once all components have been created the created SOAP service is available for deployment, an example for a `SimpleService` service is shown below:

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

## Wsdl2java plugin

[Gradle Plugin](https://github.com/bjornvester/wsdl2java-gradle-plugin) can be used as one option to create classes annotated `javax.jws.WebService`/`jakarta.jws.WebService`
based on [WSDL](https://coderlessons.com/tutorials/xml-tekhnologii/uznaite-wsdl/wsdl-kratkoe-rukovodstvo).

### Dependency

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

### Usage

Suppose we have a WSDL where `SimpleService` is declared, then configuring the plugin for `jakarta` annotation will look like this:

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
