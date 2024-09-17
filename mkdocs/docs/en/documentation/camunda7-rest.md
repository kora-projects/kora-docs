??? warning “Experimental module”

    **Experimental** module is fully working and tested, but does not guarantee a fully stabilized API and may undergo some minor changes before being fully ready.
    undergo some minor changes before being fully operational.

Module to add [REST API](https://docs.camunda.org/manual/7.21/reference/rest/overview/) for [Camunda 7 BPMN module](camunda7-bpmn.md)

## Dependency

===! ":fontawesome-brands-java: `Java`"

    Dependency `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:camunda-rest-undertow"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends CamundaRestUndertowModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Dependency `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:camunda-rest-undertow")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : CamundaRestUndertowModule
    ```

Requires [Camunda BPMN module](camunda7-bpmn.md) to be added.

## Configuration

Example of the complete configuration described in the `CamundaRestConfig` class (example values or default values are specified):

===! ":material-code-json: `Hocon`"

    ```javascript
    camunda {
        rest {
            enabled = false //(1)!
            path = "/engine-rest" //(2)!
            port = 8081 //(3)!
            shutdownWait = "100ms" //(4)!
            telemetry {
                logging {
                    enabled = false //(5)!
                    stacktrace = true //(6)!
                }
                metrics {
                    enabled = true //(7)!
                    slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(8)!
                }
                tracing {
                    enabled = true //(9)!
                }
            }
        }
    }
    ```

    1.  Enable/disable REST API
    2.  Prefix path to REST API
    3.  Port on which the REST API server will be started
    4.  Maximum time to wait for the server to complete after receiving a floating termination signal
    5.  Enables module logging (default is `false`)
    6.  Enables error stack logging (default is `true`)
    7.  Enables module metrics (default `true`)
    8.  Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    9.  Enables module tracing (default is `true`)

=== ":simple-yaml: `YAML`"

    ```yaml
    camunda:
      rest:
        enabled: false #(1)!
        path: "/engine-rest" #(2)!
        port: 8081 #(3)!
        shutdownWait: "100ms" #(4)!
        telemetry:
          logging:
            enabled: false #(5)!
            stacktrace: true #(6)!
          metrics:
            enabled: true #(7)!
            slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(8)!
          tracing:
            enabled: true #(9)!
    ```

    1.  Enable/disable REST API
    2.  Prefix path to REST API
    3.  Port on which the REST API server will be started
    4.  Maximum time to wait for the server to complete after receiving a floating termination signal
    5.  Enables module logging (default is `false`)
    6.  Enables error stack logging (default is `true`)
    7.  Enables module metrics (default `true`)
    8.  Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    9.  Enables module tracing (default is `true`)

## Applications

You can register custom `jakarta.ws.rs.core.Application` with resources for APIs (e.g. for other [webapp](https://docs.camunda.org/manual/7.21/webapps/)) by providing them as components in a dependency container.
