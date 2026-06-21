---
description: "Explains Kora Camunda 7 REST API exposure, OpenAPI management, REST configuration, CORS, telemetry, and graceful shutdown settings. Use when working with CamundaRestModule, OpenAPI, HttpServerConfig, CamundaRestConfig, CORS, telemetry."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora Camunda 7 REST API exposure, OpenAPI management, REST configuration, CORS, telemetry, and graceful shutdown settings; key triggers include CamundaRestModule, OpenAPI, HttpServerConfig, CamundaRestConfig, CORS, telemetry."
---

??? warning "Experimental module"

    The **experimental** module is fully working and tested, but it requires additional validation and usage analysis.
    For this reason, the `API` may undergo minor changes before it is considered fully stable.

The module connects [`Camunda 7 REST API`](https://docs.camunda.org/manual/7.21/reference/rest/overview/) to a Kora application and exposes the standard `CamundaRestResources` through a separate `Undertow` HTTP server.
It is used together with the [`Camunda 7 BPMN` module](camunda7-bpmn.md): the `BPMN` engine executes processes, while the REST module provides HTTP access to `Camunda 7` operations.

The module can also serve the `OpenAPI` description of the `REST API`, as well as `Swagger UI` and `RapiDoc` pages.
Requests to the `REST API` have separate settings for `CORS`, logging, metrics, tracing, and graceful server shutdown.

## Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora.experimental:camunda-rest-undertow"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends CamundaRestUndertowModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora.experimental:camunda-rest-undertow")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : CamundaRestUndertowModule
    ```

Requires the [`Camunda 7 BPMN` module](camunda7-bpmn.md).

## Configuration { #configuration }

Example of the complete configuration described by the `CamundaRestConfig` class:

===! ":material-code-json: `Hocon`"

    ```javascript
    camunda {
        rest {
            enabled = false //(1)!
            path = "/engine-rest" //(2)!
            port = 8081 //(3)!
            shutdownWait = "30s" //(4)!
            openapi {
                file = [ "openapi.json" ] //(5)!
                enabled = false  //(6)!
                endpoint = "/openapi" //(7)!
                swaggerui {
                    enabled = false //(8)!
                    endpoint = "/swagger-ui" //(9)!
                }
                rapidoc {
                    enabled = false //(10)!
                    endpoint = "/rapidoc" //(11)!
                }
            }
            cors {
                enabled = false //(12)!
                allowOrigin = "*" //(13)!
                allowHeaders = [ "*" ] //(14)!
                allowMethods = [ "GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD" ] //(15)!
                allowCredentials = true //(16)!
                exposeHeaders = [ "*" ] //(17)!
                maxAge = "1h" //(18)!
            }
            telemetry {
                logging {
                    enabled = false //(19)!
                    stacktrace = true //(20)!
                    mask = "***" //(21)!
                    maskQueries = [ ] //(22)!
                    maskHeaders = [ "authorization" ] //(23)!
                    pathTemplate = true //(24)!
                }
                metrics {
                    enabled = true //(25)!
                    slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(26)!
                    tags = { // (27)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
                tracing {
                    enabled = true //(28)!
                    attributes = { // (29)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
            }
        }
    }
    ```

    1. Enables `Camunda 7 REST API` (default: `false`).
    2. Path prefix for `Camunda 7 REST API` (default: `/engine-rest`).
    3. Port of the separate `Undertow` HTTP server for the `REST API` (default: `8081`).
    4. Maximum time to wait for HTTP server [graceful shutdown](container.md#component-lifecycle) (default: `30s`).
    5. Path to the `OpenAPI` file in `resources` (default: `[ "openapi.json" ]`). By default, the file from the [`camunda-engine-rest-openapi` dependency](https://mvnrepository.com/artifact/org.camunda.bpm/camunda-engine-rest-openapi) is used.
    6. Enables the controller that serves the `OpenAPI` file (default: `false`).
    7. Path where the `OpenAPI` file will be available (default: `/openapi`).
    8. Enables the controller that serves `Swagger UI` (default: `false`).
    9. Path where `Swagger UI` will be available (default: `/swagger-ui`).
    10. Enables the controller that serves `RapiDoc` (default: `false`).
    11. Path where `RapiDoc` will be available (default: `/rapidoc`).
    12. Enables the `CORS` filter (default: `false`).
    13. Allowed origin for `CORS` (default: not specified, optional). If the value is not specified, the filter uses the request `Origin` header, and if it is absent, returns `*`.
    14. Allowed headers for `CORS` requests (default: `[ "*" ]`).
    15. Allowed HTTP methods for `CORS` requests (default: `[ "GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD" ]`).
    16. Allows credentials in `CORS` requests (default: `true`).
    17. Headers exposed to the client in a `CORS` response (default: `[ "*" ]`).
    18. Maximum caching time for `CORS` preflight requests (default: `1h`).
    19. Enables module logging (default: `false`).
    20. Enables stack trace logging when an exception occurs (default: `true`).
    21. Mask used to hide specified request or response headers and parameters (default: `***`).
    22. List of request parameters to hide in logs (default: `[ ]`).
    23. List of request or response headers to hide in logs (default: `[ "authorization" ]`).
    24. Defines whether the path template is used for logging (default: not specified, optional). If not specified, the full path is used only at the `TRACE` logging level; if `true`, the path template is used; if `false`, the full path is used.
    25. Enables module metrics (default: `true`).
    26. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for the [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metric (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
    27. Additional tags for metrics (default: `{}`).
    28. Enables module tracing (default: `true`).
    29. Additional attributes for tracing (default: `{}`).

=== ":simple-yaml: `YAML`"

    ```yaml
    camunda:
      rest:
        enabled: false #(1)!
        path: "/engine-rest" #(2)!
        port: 8081 #(3)!
        shutdownWait: "30s" #(4)!
        openapi:
          file: [ "openapi.json" ] #(5)!
          enabled: false  #(6)!
          endpoint: "/openapi" #(7)!
          swaggerui:
            enabled: false #(8)!
            endpoint: "/swagger-ui" #(9)!
          rapidoc:
            enabled: false #(10)!
            endpoint: "/rapidoc" #(11)!
        cors:
          enabled: false #(12)!
          allowOrigin: "*" #(13)!
          allowHeaders: [ "*" ] #(14)!
          allowMethods: [ "GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD" ] #(15)!
          allowCredentials: true #(16)!
          exposeHeaders: [ "*" ] #(17)!
          maxAge: "1h" #(18)!
        telemetry:
          logging:
            enabled: false #(19)!
            stacktrace: true #(20)!
            mask: "***" #(21)!
            maskQueries: [ ] #(22)!
            maskHeaders: [ "authorization" ] #(23)!
            pathTemplate: true #(24)!
          metrics:
            enabled: true #(25)!
            slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(26)!
            tags: #(27)!
              key1: value1
              key2: value2
          tracing:
            enabled: true #(28)!
            attributes: #(29)!
              key1: value1
              key2: value2
    ```

    1. Enables `Camunda 7 REST API` (default: `false`).
    2. Path prefix for `Camunda 7 REST API` (default: `/engine-rest`).
    3. Port of the separate `Undertow` HTTP server for the `REST API` (default: `8081`).
    4. Maximum time to wait for HTTP server [graceful shutdown](container.md#component-lifecycle) (default: `30s`).
    5. Path to the `OpenAPI` file in `resources` (default: `[ "openapi.json" ]`). By default, the file from the [`camunda-engine-rest-openapi` dependency](https://mvnrepository.com/artifact/org.camunda.bpm/camunda-engine-rest-openapi) is used.
    6. Enables the controller that serves the `OpenAPI` file (default: `false`).
    7. Path where the `OpenAPI` file will be available (default: `/openapi`).
    8. Enables the controller that serves `Swagger UI` (default: `false`).
    9. Path where `Swagger UI` will be available (default: `/swagger-ui`).
    10. Enables the controller that serves `RapiDoc` (default: `false`).
    11. Path where `RapiDoc` will be available (default: `/rapidoc`).
    12. Enables the `CORS` filter (default: `false`).
    13. Allowed origin for `CORS` (default: not specified, optional). If the value is not specified, the filter uses the request `Origin` header, and if it is absent, returns `*`.
    14. Allowed headers for `CORS` requests (default: `[ "*" ]`).
    15. Allowed HTTP methods for `CORS` requests (default: `[ "GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD" ]`).
    16. Allows credentials in `CORS` requests (default: `true`).
    17. Headers exposed to the client in a `CORS` response (default: `[ "*" ]`).
    18. Maximum caching time for `CORS` preflight requests (default: `1h`).
    19. Enables module logging (default: `false`).
    20. Enables stack trace logging when an exception occurs (default: `true`).
    21. Mask used to hide specified request or response headers and parameters (default: `***`).
    22. List of request parameters to hide in logs (default: `[ ]`).
    23. List of request or response headers to hide in logs (default: `[ "authorization" ]`).
    24. Defines whether the path template is used for logging (default: not specified, optional). If not specified, the full path is used only at the `TRACE` logging level; if `true`, the path template is used; if `false`, the full path is used.
    25. Enables module metrics (default: `true`).
    26. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for the [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metric (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
    27. Additional tags for metrics (default: `{}`).
    28. Enables module tracing (default: `true`).
    29. Additional attributes for tracing (default: `{}`).

If the standard `Camunda 7` `OpenAPI` file is used, the module substitutes the current `port` and `path` values when serving the file.
This keeps `OpenAPI` aligned with the `REST API` address even when values other than `/engine-rest` or `8081` are configured.

## Applications { #applications }

The module automatically registers the standard `Camunda 7 REST API` resources.
To add custom `JAX-RS` resources, register a `jakarta.ws.rs.core.Application` component with the `CamundaRest` tag.
All such applications will be merged with the standard Camunda resources.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(CamundaRest.class)
    @Component
    public final class CustomCamundaApplication extends Application {

        @Override
        public Set<Class<?>> getClasses() {
            return Set.of(CustomResource.class);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(CamundaRest::class)
    @Component
    class CustomCamundaApplication : Application() {

        override fun getClasses(): Set<Class<*>> {
            return setOf(CustomResource::class.java)
        }
    }
    ```
