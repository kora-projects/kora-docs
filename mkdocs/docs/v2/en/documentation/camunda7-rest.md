---
description: "Explains how Kora exposes the Camunda 7 REST API over a dedicated Undertow HTTP server, with OpenAPI, Swagger UI and Scalar pages, CORS, telemetry, and graceful shutdown. Use when working with CamundaRestUndertowModule, CamundaRestModule, CamundaRestConfig, CamundaRest, KoraProcessEngineProvider, camunda.rest, CORS, telemetry."
agent:
  use_when: "Use this file for Kora docs or implementation questions about exposing the Camunda 7 REST API from a Kora application over its own Undertow HTTP server, its OpenAPI / Swagger UI / Scalar pages, CORS, telemetry, and graceful shutdown; key triggers include CamundaRestUndertowModule, CamundaRestModule, CamundaRestConfig, CamundaRest, KoraProcessEngineProvider, camunda.rest, camunda.rest.openapi.files, camunda.rest.cors, engine-rest, CamundaRestResources."
---

??? warning "Experimental module"

    The **experimental** module is fully working and tested, but requires additional usage validation and analysis.
    Therefore, the `API` may receive minor changes before full readiness.

???+ warning "Camunda 7 is deprecated"

    `CamundaRestModule` is marked `@Deprecated` because [Camunda 7 has reached end of life](https://camunda.com/blog/2025/02/camunda-7-enterprise-end-of-life-extension/).
    The module still works and is still shipped, but no new capabilities are planned for it.
    For new services consider [Camunda 8](camunda8-worker.md) or the [Operaton](https://operaton.org/) engine, a community fork of Camunda 7.

The module exposes the [`Camunda 7 REST API`](https://docs.camunda.org/manual/7.24/reference/rest/overview/) of a Kora application:
it deploys the standard `CamundaRestResources` `JAX-RS` resources on a `RESTEasy` deployment and serves them through a **separate** `Undertow` HTTP server.

It is used together with the [Camunda 7 BPMN module](camunda7-bpmn.md): the `BPMN` engine executes processes, while this module gives HTTP access to `Camunda 7` operations —
starting process instances, querying tasks and deployments, correlating messages, and everything else the engine REST API offers.

The module can also serve the `OpenAPI` description of the `REST API` together with the `Swagger UI` and `Scalar` pages.
Requests to the `REST API` have their own settings for `CORS`, logging, metrics, tracing, and graceful server shutdown.

## Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework.experimental:camunda-rest-undertow"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends CamundaRestUndertowModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework.experimental:camunda-rest-undertow")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : CamundaRestUndertowModule
    ```

Requires the [Camunda 7 BPMN module](camunda7-bpmn.md).
The `Camunda` engine itself is a `compileOnly` dependency of this module, so the engine reaches the classpath only through `camunda-engine-bpmn`, which also creates the `ProcessEngine` this module serves.

`CamundaRestUndertowModule` extends `CamundaRestModule`: the base module contributes the configuration, the telemetry factory, and the default `JAX-RS` application, while the `Undertow` module adds the HTTP handler and the server itself.
Applications connect `CamundaRestUndertowModule` — connecting only `CamundaRestModule` leaves the `REST API` without a transport.

## HTTP server { #http-server }

The module starts a **separate**, independent `Undertow` HTTP server dedicated to the `Camunda 7 REST API`.
It listens on its own `port` (default: `8081`) and is completely isolated from the main [HTTP server](http-server.md) module:
it has its own [CORS](#cors) filter, its own [telemetry](#telemetry), and its own [graceful shutdown](container.md#component-lifecycle).
The `Camunda REST API` and the application's own controllers therefore run on different ports and do not share request handling or configuration.

The server is disabled by default and is started by `camunda.rest.enabled = true`.
The `REST` handler itself is always built during graph initialization — `enabled` only decides whether the HTTP listener is opened.
If the configured `port` is already taken, startup fails with `Camunda HTTP Server (Undertow) failed to start, cause port '<port>' is already in use`.

The `ProcessEngine` that serves these requests is provided by the [Camunda 7 BPMN module](camunda7-bpmn.md).
There is no dependency between the two modules inside the Kora container: the `BPMN` module registers the engine it built in the static `ProcessEngines` registry of `Camunda`,
and this module publishes a `KoraProcessEngineProvider` through the `org.camunda.bpm.engine.rest.spi.ProcessEngineProvider` service loader, which resolves the default engine from that registry.
This module only exposes the engine over HTTP under the configured `path` (default: `/engine-rest`).

Requests are dispatched onto virtual threads, so a `Camunda REST` call blocking on the database does not occupy an `Undertow` I/O thread.

On shutdown, the server stops accepting new requests and waits up to `shutdownWait` (default: `30s`)
for in-flight requests to complete before it terminates.

## Configuration { #configuration }

Example of the complete configuration described by the `CamundaRestConfig` interface:

===! ":material-code-json: `Hocon`"

    ```javascript
    camunda {
        rest {
            enabled = false //(1)!
            path = "/engine-rest" //(2)!
            port = 8081 //(3)!
            shutdownWait = "30s" //(4)!
            openapi {
                enabled = false //(5)!
                files = [ "openapi.json" ] //(6)!
                path = "/openapi" //(7)!
                cache = "GZIP" //(8)!
                swaggerui {
                    enabled = false //(9)!
                    path = "/swagger-ui" //(10)!
                    withCredentials = true //(11)!
                    cache = "GZIP" //(12)!
                    options { //(13)!
                        layout = "StandaloneLayout"
                        validatorUrl = "null"
                        defaultModelsExpandDepth = "0"
                        deepLinking = "true"
                        persistAuthorization = "true"
                        displayOperationId = "true"
                        filter = "true"
                    }
                }
                scalar {
                    enabled = false //(14)!
                    path = "/scalar" //(15)!
                    cache = "GZIP" //(16)!
                }
            }
            cors {
                enabled = false //(17)!
                allowOrigin = "*" //(18)!
                allowHeaders = [ "*" ] //(19)!
                allowMethods = [ "GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD" ] //(20)!
                allowCredentials = true //(21)!
                exposeHeaders = [ "*" ] //(22)!
                maxAge = "1h" //(23)!
            }
            telemetry {
                logging {
                    enabled = false //(24)!
                    stacktrace = true //(25)!
                    mask = "***" //(26)!
                    maskQueries = [ ] //(27)!
                    maskHeaders = [ "authorization", "cookie", "set-cookie" ] //(28)!
                    pathFull = false //(29)!
                }
                metrics {
                    enabled = false //(30)!
                    slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(31)!
                    tags = { //(32)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
                tracing {
                    enabled = true //(33)!
                    attributes = { //(34)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
            }
        }
    }
    ```

    1.  Starts the separate HTTP server with the `Camunda 7 REST API` (default: `false`).
    2.  Path prefix of the `Camunda 7 REST API` (default: `/engine-rest`).
    3.  Port of the separate `Undertow` HTTP server serving the `REST API` (default: `8081`).
    4.  Maximum time to wait for HTTP server [graceful shutdown](container.md#component-lifecycle) (default: `30s`).
    5.  Enables serving `OpenAPI` files (default: `false`).
    6.  List of `OpenAPI` files in application resources (default: `[ "openapi.json" ]`), see [OpenAPI](#openapi). The default value is the specification bundled with the [`camunda-engine-rest-openapi`](https://mvnrepository.com/artifact/org.camunda.bpm/camunda-engine-rest-openapi) dependency.
    7.  Path where `OpenAPI` files are available (default: `/openapi`). With one file it is exactly this path; with several files it becomes a prefix of the `/openapi/{file}` form.
    8.  Response caching mode for `OpenAPI` files: `NONE`, `GZIP`, or `FULL` (default: `GZIP`), see [Caching](openapi-management.md#cache).
    9.  Enables the `Swagger UI` page (default: `false`).
    10. Path where the `Swagger UI` page is available (default: `/swagger-ui`).
    11. Sends browser credentials (cookies, `Authorization` header) with requests issued from `Swagger UI` (default: `true`).
    12. Response caching mode for the `Swagger UI` page: `NONE`, `GZIP`, or `FULL` (default: `GZIP`).
    13. `Swagger UI` initialization options, see [Swagger UI options](openapi-management.md#swagger-ui-options) (default: the seven values shown above).
    14. Enables the `Scalar` page (default: `false`).
    15. Path where the `Scalar` page is available (default: `/scalar`).
    16. Response caching mode for the `Scalar` page: `NONE`, `GZIP`, or `FULL` (default: `GZIP`).
    17. Enables the `CORS` filter (default: `false`).
    18. Allowed origin for `CORS` (default not specified, optional). When not specified, the filter echoes the request `Origin` header, and falls back to `*` when the request has none.
    19. Allowed headers for `CORS` requests (default: `[ "*" ]`).
    20. Allowed HTTP methods for `CORS` requests (default: `[ "GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD" ]`).
    21. Whether credentials are allowed in `CORS` requests (default: `true`).
    22. Headers exposed to the client in a `CORS` response (default: `[ "*" ]`).
    23. Maximum caching time for `CORS` preflight requests (default: `1h`).
    24. Enables module logging (default: `false`).
    25. Enables call stack logging on exception (default: `true`).
    26. Mask used to hide specified headers and request parameters (default: `***`).
    27. List of request parameters to hide (default: `[]`).
    28. List of request or response headers to hide (default: `[ "authorization", "cookie", "set-cookie" ]`).
    29. Whether to log the full request path instead of the route template; when not specified, the template is used except at `TRACE`, where the full path is used (default not specified, optional).
    30. Enables module metrics (default: `false`).
    31. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
    32. Configures metric tags (default: `{}`).
    33. Enables module tracing (default: `true`).
    34. Configures tracing attributes (default: `{}`).

=== ":simple-yaml: `YAML`"

    ```yaml
    camunda:
      rest:
        enabled: false #(1)!
        path: "/engine-rest" #(2)!
        port: 8081 #(3)!
        shutdownWait: "30s" #(4)!
        openapi:
          enabled: false #(5)!
          files: [ "openapi.json" ] #(6)!
          path: "/openapi" #(7)!
          cache: "GZIP" #(8)!
          swaggerui:
            enabled: false #(9)!
            path: "/swagger-ui" #(10)!
            withCredentials: true #(11)!
            cache: "GZIP" #(12)!
            options: #(13)!
              layout: "StandaloneLayout"
              validatorUrl: "null"
              defaultModelsExpandDepth: "0"
              deepLinking: "true"
              persistAuthorization: "true"
              displayOperationId: "true"
              filter: "true"
          scalar:
            enabled: false #(14)!
            path: "/scalar" #(15)!
            cache: "GZIP" #(16)!
        cors:
          enabled: false #(17)!
          allowOrigin: "*" #(18)!
          allowHeaders: [ "*" ] #(19)!
          allowMethods: [ "GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD" ] #(20)!
          allowCredentials: true #(21)!
          exposeHeaders: [ "*" ] #(22)!
          maxAge: "1h" #(23)!
        telemetry:
          logging:
            enabled: false #(24)!
            stacktrace: true #(25)!
            mask: "***" #(26)!
            maskQueries: [ ] #(27)!
            maskHeaders: [ "authorization", "cookie", "set-cookie" ] #(28)!
            pathFull: false #(29)!
          metrics:
            enabled: false #(30)!
            slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(31)!
            tags: #(32)!
              key1: value1
              key2: value2
          tracing:
            enabled: true #(33)!
            attributes: #(34)!
              key1: value1
              key2: value2
    ```

    1.  Starts the separate HTTP server with the `Camunda 7 REST API` (default: `false`).
    2.  Path prefix of the `Camunda 7 REST API` (default: `/engine-rest`).
    3.  Port of the separate `Undertow` HTTP server serving the `REST API` (default: `8081`).
    4.  Maximum time to wait for HTTP server [graceful shutdown](container.md#component-lifecycle) (default: `30s`).
    5.  Enables serving `OpenAPI` files (default: `false`).
    6.  List of `OpenAPI` files in application resources (default: `[ "openapi.json" ]`), see [OpenAPI](#openapi). The default value is the specification bundled with the [`camunda-engine-rest-openapi`](https://mvnrepository.com/artifact/org.camunda.bpm/camunda-engine-rest-openapi) dependency.
    7.  Path where `OpenAPI` files are available (default: `/openapi`). With one file it is exactly this path; with several files it becomes a prefix of the `/openapi/{file}` form.
    8.  Response caching mode for `OpenAPI` files: `NONE`, `GZIP`, or `FULL` (default: `GZIP`), see [Caching](openapi-management.md#cache).
    9.  Enables the `Swagger UI` page (default: `false`).
    10. Path where the `Swagger UI` page is available (default: `/swagger-ui`).
    11. Sends browser credentials (cookies, `Authorization` header) with requests issued from `Swagger UI` (default: `true`).
    12. Response caching mode for the `Swagger UI` page: `NONE`, `GZIP`, or `FULL` (default: `GZIP`).
    13. `Swagger UI` initialization options, see [Swagger UI options](openapi-management.md#swagger-ui-options) (default: the seven values shown above).
    14. Enables the `Scalar` page (default: `false`).
    15. Path where the `Scalar` page is available (default: `/scalar`).
    16. Response caching mode for the `Scalar` page: `NONE`, `GZIP`, or `FULL` (default: `GZIP`).
    17. Enables the `CORS` filter (default: `false`).
    18. Allowed origin for `CORS` (default not specified, optional). When not specified, the filter echoes the request `Origin` header, and falls back to `*` when the request has none.
    19. Allowed headers for `CORS` requests (default: `[ "*" ]`).
    20. Allowed HTTP methods for `CORS` requests (default: `[ "GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD" ]`).
    21. Whether credentials are allowed in `CORS` requests (default: `true`).
    22. Headers exposed to the client in a `CORS` response (default: `[ "*" ]`).
    23. Maximum caching time for `CORS` preflight requests (default: `1h`).
    24. Enables module logging (default: `false`).
    25. Enables call stack logging on exception (default: `true`).
    26. Mask used to hide specified headers and request parameters (default: `***`).
    27. List of request parameters to hide (default: `[]`).
    28. List of request or response headers to hide (default: `[ "authorization", "cookie", "set-cookie" ]`).
    29. Whether to log the full request path instead of the route template; when not specified, the template is used except at `TRACE`, where the full path is used (default not specified, optional).
    30. Enables module metrics (default: `false`).
    31. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
    32. Configures metric tags (default: `{}`).
    33. Enables module tracing (default: `true`).
    34. Configures tracing attributes (default: `{}`).

The listing above shows every available option; in practice you enable only what you need.
A typical setup exposes the `REST API` on a custom `port` together with the `OpenAPI` description, `Swagger UI`, and request logging:

===! ":material-code-json: `Hocon`"

    ```javascript
    camunda {
        rest {
            enabled = true
            port = 8090
            openapi {
                enabled = true
                swaggerui.enabled = true
            }
            telemetry.logging.enabled = true
        }
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    camunda:
      rest:
        enabled: true
        port: 8090
        openapi:
          enabled: true
          swaggerui:
            enabled: true
        telemetry:
          logging:
            enabled: true
    ```

`cache` values are matched against the enum constants exactly, so they must be written in upper case.

## OpenAPI { #openapi }

Besides the `REST API` itself, the separate server can serve the API's `OpenAPI` description together with
the [Swagger UI](https://swagger.io/tools/swagger-ui/) and [Scalar](https://scalar.com/) pages.
All three are disabled by default and are enabled independently through the `openapi` configuration section,
and all three are served by the same handlers the [OpenAPI management](openapi-management.md) module uses, so their behavior matches that module.

When enabled, the pages are available on the `REST` server `port` at the configured paths:

| Page         | Configuration flag          | Default path  |
|--------------|-----------------------------|---------------|
| OpenAPI spec | `openapi.enabled`           | `/openapi`    |
| Swagger UI   | `openapi.swaggerui.enabled` | `/swagger-ui` |
| Scalar       | `openapi.scalar.enabled`    | `/scalar`     |

For example, with `port = 8090` and `openapi.enabled = true` the specification is served at `http://localhost:8090/openapi`,
and `Swagger UI` (when enabled) at `http://localhost:8090/swagger-ui`.
Everything outside these paths and outside the `REST API` `path` prefix answers with `404`.

By default the module serves the `OpenAPI` specification bundled with the
[`camunda-engine-rest-openapi`](https://mvnrepository.com/artifact/org.camunda.bpm/camunda-engine-rest-openapi) dependency, which is why `files` already has a working default.
Before the file is sent, the module rewrites the port `8080` written in it to the configured `port`, and — when `path` differs from `/engine-rest` — rewrites the `engine-rest` prefix as well,
so the served `OpenAPI` always matches the live `REST API` address.

To serve a custom specification instead, point `openapi.files` at one or more files in `resources`:

===! ":material-code-json: `Hocon`"

    ```javascript
    camunda.rest.openapi {
        enabled = true
        files = [ "my-openapi.json" ]
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    camunda:
      rest:
        openapi:
          enabled: true
          files: [ "my-openapi.json" ]
    ```

Each path is resolved as a classpath resource, first as written and then with a leading `/` prepended, so `openapi/my.json` and `/openapi/my.json` address the same resource.
A `.json` file is served as `text/json`, any other extension as `text/x-yaml`.

When more than one file is configured, the public name of a file in the URL is derived from the file name: directories are stripped and a trailing `.json`, `.yml`, or `.yaml` extension is removed.
So with `files = [ "openapi/engine.json", "openapi/custom.json" ]` the specifications are available at `/openapi/engine` and `/openapi/custom`, while `/openapi` itself answers with `404`.

## CORS { #cors }

The `REST` server has its own [CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS) filter, disabled by default and enabled through `cors.enabled`.
When enabled, the filter wraps the whole server — both the `REST API` and the `OpenAPI` pages — and adds the `Access-Control-*` headers to every response, without short-circuiting preflight requests itself.

When `cors.allowOrigin` is not set, the filter reflects the request `Origin` header back in the response,
falling back to `*` when the request carries no `Origin` header.
The remaining `cors.*` options control the allowed headers and methods, whether credentials are allowed,
the headers exposed to the client, and the preflight cache duration.
A header that a resource has already set itself is never overwritten, and `Access-Control-Expose-Headers` is omitted entirely when `exposeHeaders` is empty.

## Telemetry { #telemetry }

Requests handled by the `REST` server are covered by the standard Kora telemetry signals — [logging](logging-slf4j.md),
[metrics](metrics.md), and [tracing](tracing.md) — configured under the `telemetry` section.
Logging and metrics are disabled by default, tracing is enabled by default; when all three are off, the module installs a no-op telemetry and adds no overhead per request.

Logging is written to the `io.koraframework.http.server.common.HttpServer` logger and produces a `CamundaRest received request` event before the call
and a `CamundaRest succeed response` (or `CamundaRest errored response` on failure) event after it.
The `operation` field carries the method with the route template, `resultCode`, `statusCode`, and `processingTime` are attached to the response event, and query parameters and headers are added at the `DEBUG` level.
Headers listed in `maskHeaders` and query parameters listed in `maskQueries` are replaced with the `mask` value.
The logged operation uses the route template by default and the full path when `pathFull = true` or the logger level is `TRACE`.

Tracing creates a `<METHOD> <route template>` `SERVER` span per request with the `http.request.method`, `url.scheme`, `server.address`, `url.path`, `http.route`, `http.response.status_code`, and `http.response.result_code` attributes.
The incoming `W3C` trace context is propagated into the span and the resulting context is written back into the response headers.

Module metrics are described in the [Metrics Reference](metrics.md#camunda-rest) section.

The default telemetry can be overridden by registering your own `DefaultCamundaRestLoggerFactory` or `DefaultCamundaRestMetricsFactory` subclass as a `@Component`;
the whole `CamundaRestTelemetryFactory` is provided via `@DefaultComponent` and can be replaced as well.

### Route templates { #route-templates }

Metrics, tracing, and logging all identify a request by its route template rather than by its full path, so `/engine-rest/process-instance/{id}` stays a single time series no matter how many process instances exist.

The module cannot ask `RESTEasy` for the matched template, so it carries a built-in table of every `Camunda 7 REST API` route, prefixed with the configured `path`, and matches the request against it.
A request that matches nothing in that table — an unknown endpoint, or a custom `JAX-RS` resource added through [Applications](#applications) — is still served, but it produces no log record and no span,
and its duration metric is recorded with the `http.route` tag set to `UNKNOWN_ROUTE`.

## Applications { #applications }

The module already registers a default `@Tag(CamundaRest.class)` `jakarta.ws.rs.core.Application` that exposes the standard
`Camunda 7 REST API` resources (`CamundaRestResources`) together with a `ResteasyJackson2Provider` for `JSON` serialization.

To add custom `JAX-RS` resources, register your own `jakarta.ws.rs.core.Application` component marked with the `@Tag(CamundaRest.class)` tag.
All such applications are collected and merged with the default one — their `getClasses()`, `getSingletons()`, and `getProperties()` are combined —
so custom resources are served on the same `REST` server alongside the standard Camunda endpoints, under the same `path` prefix.

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

Custom resources are not part of the built-in route table, so they are reported as `UNKNOWN_ROUTE` in metrics and are not logged or traced, see [Route templates](#route-templates).
