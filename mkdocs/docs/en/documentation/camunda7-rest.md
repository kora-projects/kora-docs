??? warning "Experimental module"

    **Experimental** module is fully working and tested, but requires additional approbation and usage analytics, 
    for this reason, API may potentially undergo minor changes before fully stable.

Module to add [REST API](https://docs.camunda.org/manual/7.21/reference/rest/overview/) for [Camunda 7 BPMN module](camunda7-bpmn.md)

## Dependency

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
                    maskHeaders = [ "authorization", "cookie", "set-cookie" ] //(23)!
                    pathTemplate = true //(24)!
                }
                metrics {
                    enabled = true //(25)!
                    slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(26)!
                }
                tracing {
                    enabled = true //(27)!
                }
            }
        }
    }
    ```

    1.  Enable/disable REST API
    2.  Prefix path to REST API
    3.  Port on which the REST API server will be started
    4.  Maximum time to wait for the server to complete after receiving a floating termination signal
    5. Relative path to OpenAPI files in the `resources` directory, default is the `openapi.json` OpenAPI file from [Camunda dependencies](https://mvnrepository.com/artifact/org.camunda.bpm/camunda-engine-rest-openapi)
    6. The on/off switch of the controller that gives the OpenAPI
    7. Path where OpenAPI will be available
        5. If a single OpenAPI file is specified, then represent entire path where file is available
        6. If multiple OpenAPI files are specified, is a path prefix to the file name `/openapi/{fileName}`, taking the specified path and appending the file name to it without the directories and its extension, example of the file `someDirectory/my-openapi-1.yaml` the file path will be `/openapi/my-openapi-1`.
    8. On/Off of the controller that gives SwaggerUI
    9. Path where the SwaggerUI will be accessed
    10. On/Off of the controller that gives Rapidoc
    11. Path where Rapidoc will be available
    12.  Enables CORS filter (default `false`)
    13.  Allowed origins for CORS (default `null`)
    14.  Allowed headers for CORS requests (default `["*"]`)
    15.  Allowed HTTP methods for CORS requests (default `["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]`)
    16.  Allows transmission of credentials in CORS requests (default `true`)
    17.  Headers that can be exposed to the client in CORS responses (default `["*"]`)
    18.  Maximum caching time for CORS preflight requests (default `1 hour`)
    19.  Enables module logging (default `false`)
    20.  Enables call stack logging in case of exception
    21.  Mask that is used to hide specified headers and request/response parameters
    22.  List of request parameters to be hidden
    23.  List of request/response headers that should be hidden
    24.  Whether to always use the request path template when logging. The default is to always use the path template, except for the `TRACE` logging level, which uses the full path.
    25.  Enables module metrics (default `true`)
    26.  Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    27.  Enables module tracing (default is `true`)

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
            maskHeaders: [ "authorization", "cookie", "set-cookie" ] #(23)!
            pathTemplate: true #(24)!
          metrics:
            enabled: true #(25)!
            slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(26)!
          tracing:
            enabled: true #(27)!
    ```

    1. Enable/disable REST API
    2. Prefix path to REST API
    3. Port on which the REST API server will be started
    4. Maximum time to wait for the server to complete after receiving a floating termination signal
    5. Relative path to OpenAPI files in the `resources` directory, default is the `openapi.json` OpenAPI file from [Camunda dependencies](https://mvnrepository.com/artifact/org.camunda.bpm/camunda-engine-rest-openapi)
    6. The on/off switch of the controller that gives the OpenAPI
    7. Path where OpenAPI will be available
        5. If a single OpenAPI file is specified, then represent entire path where file is available
        6. If multiple OpenAPI files are specified, is a path prefix to the file name `/openapi/{fileName}`, taking the specified path and appending the file name to it without the directories and its extension, example of the file `someDirectory/my-openapi-1.yaml` the file path will be `/openapi/my-openapi-1`.
    8. On/Off of the controller that gives SwaggerUI
    9. Path where the SwaggerUI will be accessed
    10. On/Off of the controller that gives Rapidoc
    11. Path where Rapidoc will be available
    12.  Enables CORS filter (default `false`)
    13.  Allowed origins for CORS (default `null`)
    14.  Allowed headers for CORS requests (default `["*"]`)
    15.  Allowed HTTP methods for CORS requests (default `["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]`)
    16.  Allows transmission of credentials in CORS requests (default `true`)
    17.  Headers that can be exposed to the client in CORS responses (default `["*"]`)
    18.  Maximum caching time for CORS preflight requests (default `1 hour`)
    19.  Enables module logging (default `false`)
    20.  Enables call stack logging in case of exception
    21.  Mask that is used to hide specified headers and request/response parameters
    22.  List of request parameters to be hidden
    23.  List of request/response headers that should be hidden
    24.  Whether to always use the request path template when logging. The default is to always use the path template, except for the `TRACE` logging level, which uses the full path.
    25.  Enables module metrics (default `true`)
    26.  Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    27.  Enables module tracing (default is `true`)

## Applications

You can register custom `jakarta.ws.rs.core.Application` with resources for APIs (e.g. for other [webapp](https://docs.camunda.org/manual/7.21/webapps/)) by providing them as components in a dependency container.
