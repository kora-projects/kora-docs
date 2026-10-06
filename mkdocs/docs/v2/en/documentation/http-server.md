---
seo_title: "Kora HTTP Server: Controllers, Routing and Interceptors"
seo_description: "Reference for the Kora HTTP server: declarative and imperative controllers, routing, request and response mapping, interceptors, errors, auth and Undertow config."
keywords: ["Kora Framework", "Kora HTTP server", "@HttpController", "REST controller", "Undertow", "HTTP interceptors", "HTTP telemetry masking"]
description: "Explains Kora HTTP server, declarative and imperative controllers, routing, request and response mapping, interceptors, error handling, authorization, telemetry masking and Undertow configuration. Use when working with @HttpController, @HttpRoute, @Path, @Query, @Header, @Cookie, @Json, @InterceptWith, MaskingStrategy, DataMasker."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora HTTP server, declarative and imperative controllers, routing, request and response mapping, interceptors, error handling, authorization and Undertow configuration; key triggers include @HttpController, @HttpRoute, @Path, @Query, @Header, @Cookie, @Json, @InterceptWith, HttpServerInterceptor, HttpServerParameterReader, UndertowPublicHttpServerModule, @Tag(HttpServer.class), httpServer.port, httpServer.system, headerServerNameEnabled, maskHeaders, maskQueries, MaskingStrategy tagged @Tag(HttpServerTelemetry.class), DataMasker, JsonDataMasker, MaskingPathRules, MaskingUtils, http.server.request.duration."
---

The `HTTP server` module describes the incoming HTTP boundary of an application: accepting a request, parsing parameters,
reading the body, selecting a handler, creating a response, telemetry, and interceptors. In Kora, controllers can be described
declaratively with `@HttpController` and `@HttpRoute`, or handlers can be registered imperatively with `HttpServerRequestHandler`.

The declarative approach fits most APIs: the method signature describes the HTTP contract, and Kora creates the handler at
compile time without using `Reflection` at runtime. The imperative approach is useful for low-level or dynamic routes where
it is easier to process the request manually.

Request handling is **synchronous**. Every request is dispatched onto a virtual thread, so a handler may block:
controller methods, interceptors and mappers all return their result directly and never return `CompletionStage`,
`Mono`/`Flux` or a `suspend` function.

???+ tip "Recommendation"

    **We recommend** using an approach where OpenAPI file is primary contract
    and controllers are created from it using a OpenAPI generator.
    This approach allows you to achieve consistency between the consumer and owner of the contract
    and allows you to share this contract to create clients for it using the same approach.
    For more information about the generator, see the [section on generating from OpenAPI](openapi-codegen.md).

For a step-by-step walkthrough before the reference details, see [HTTP Server](../guides/http-server.md) and [Advanced HTTP Server](../guides/http-server-advanced.md).

## Dependency { #dependency }

Implementation is based on [Undertow](https://undertow.io/).
`Undertow` is a lightweight open-source web server for `Java` applications.
It is built on asynchronous and non-blocking I/O operations using `NIO`,
which ensures high performance and low resource consumption.

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:http-server-undertow"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends UndertowPublicHttpServerModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:http-server-undertow")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : UndertowPublicHttpServerModule
    ```

`UndertowPublicHttpServerModule` starts **two** servers: the public one for application controllers
and the system one for [probes](probes.md) and [metrics](metrics.md).
If an application needs only the system server, connect `UndertowSystemHttpServerModule` instead.

## Configuration { #configuration }

Basic HTTP server configuration parameters:

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
        port = 8080 //(1)!
        system.port = 8085 //(2)!
        maxRequestBodySize = "256MiB" //(3)!
        telemetry.logging.enabled = false //(4)!
    }
    ```

    1.  Public `HTTP` server port (default: `8080`)
    2.  System `HTTP` server port (default: `8085`)
    3.  Maximum allowed size of incoming request body (default: `256MiB`)
    4.  Enables request and response logging (default: `false`)

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      port: 8080 #(1)!
      system:
        port: 8085 #(2)!
      maxRequestBodySize: "256MiB" #(3)!
      telemetry:
        logging:
          enabled: false #(4)!
    ```

    1.  Public `HTTP` server port (default: `8080`)
    2.  System `HTTP` server port (default: `8085`)
    3.  Maximum allowed size of incoming request body (default: `256MiB`)
    4.  Enables request and response logging (default: `false`)

??? note "Full Configuration"

    Example of the complete configuration described in the `HttpServerConfig` class (default or example values are specified):

    ===! ":material-code-json: `Hocon`"

        ```javascript
        httpServer {
            port = 8080 //(1)!
            ignoreTrailingSlash = false //(2)!
            shutdownWait = "30s" //(3)!
            socketReadTimeout = "0s" //(4)!
            socketWriteTimeout = "0s" //(5)!
            socketKeepAliveEnabled = false //(6)!
            headerKeepAliveEnabled = false //(7)!
            headerServerNameEnabled = false //(8)!
            headerServerDateEnabled = true //(9)!
            maxRequestBodySize = "256MiB" //(10)!
            telemetry {
                logging {
                    enabled = false //(11)!
                    stacktrace = true //(12)!
                    maskQueries = [ ] //(13)!
                    maskHeaders = [ "authorization", "cookie", "set-cookie" ] //(14)!
                    pathFull = false //(15)!
                    maxRequestBodyLogSize = "2MiB" //(16)!
                    maxResponseBodyLogSize = "2MiB" //(17)!
                }
                metrics {
                    enabled = false //(18)!
                    slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(19)!
                    tags = { // (20)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
                tracing {
                    enabled = true //(21)!
                    tracePathFull = true //(22)!
                    attributes = { // (23)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
            }
        }
        ```

        1.  Public `HTTP` server port (default: `8080`)
        2.  Whether to ignore a trailing `/` in the path: when enabled, `/my/path` and `/my/path/` are treated as the same route (default: `false`)
        3.  Time to wait for processing before server shutdown during [graceful shutdown](container.md#component-lifecycle) (default: `30s`)
        4.  Maximum time to wait for reading data from a socket or connection; `0s` disables the timeout (default: `0s`)
        5.  Maximum time to wait for writing data to a socket or connection; `0s` disables the timeout (default: `0s`)
        6.  Whether to enable `TCP keep-alive` for a socket or connection (default: `false`)
        7.  Whether to always send the `Connection: keep-alive` response header (default: `false`)
        8.  Whether to send the `Server: Kora` response header (default: `false`)
        9.  Whether to always send the `Date` response header (default: `true`)
        10.  Maximum allowed size of an incoming request body (default: `256MiB`)
        11.  Enables module logging (default: `false`)
        12.  Enables call stack logging on exception (default: `true`)
        13.  Query parameter names whose values are masked in the log, compared case-insensitively (default: `[]`). See [Masking](#telemetry-masking)
        14.  Request and response header names whose values are masked in the log, compared case-insensitively (default: `[ "authorization", "cookie", "set-cookie" ]`). See [Masking](#telemetry-masking)
        15.  Whether to log the full request path instead of the route template; when not specified, the template is used except at `TRACE`, where the full path is used (default not specified, optional)
        16.  Maximum request body size that may be written to the log; a larger body is logged without content (default: `2MiB`)
        17.  Maximum response body size that may be written to the log; a larger body is logged without content (default: `2MiB`)
        18.  Enables module metrics (default: `false`)
        19.  Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
        20.  Configures metric tags (default: `{}`)
        21.  Enables module tracing (default: `true`)
        22.  Whether to put the full request path into the `url.path` span attribute (default: `true`)
        23.  Configures tracing attributes (default: `{}`)

    === ":simple-yaml: `YAML`"

        ```yaml
        httpServer:
          port: 8080 #(1)!
          ignoreTrailingSlash: false #(2)!
          shutdownWait: "30s" #(3)!
          socketReadTimeout: "0s" #(4)!
          socketWriteTimeout: "0s" #(5)!
          socketKeepAliveEnabled: false #(6)!
          headerKeepAliveEnabled: false #(7)!
          headerServerNameEnabled: false #(8)!
          headerServerDateEnabled: true #(9)!
          maxRequestBodySize: "256MiB" #(10)!
          telemetry:
            logging:
              enabled: false #(11)!
              stacktrace: true #(12)!
              maskQueries: [ ] #(13)!
              maskHeaders: [ "authorization", "cookie", "set-cookie" ] #(14)!
              pathFull: false #(15)!
              maxRequestBodyLogSize: "2MiB" #(16)!
              maxResponseBodyLogSize: "2MiB" #(17)!
            metrics:
              enabled: false #(18)!
              slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(19)!
              tags: #(20)!
                key1: value1
                key2: value2
            tracing:
              enabled: true #(21)!
              tracePathFull: true #(22)!
              attributes: #(23)!
                key1: value1
                key2: value2
        ```

        1.  Public `HTTP` server port (default: `8080`)
        2.  Whether to ignore a trailing `/` in the path: when enabled, `/my/path` and `/my/path/` are treated as the same route (default: `false`)
        3.  Time to wait for processing before server shutdown during [graceful shutdown](container.md#component-lifecycle) (default: `30s`)
        4.  Maximum time to wait for reading data from a socket or connection; `0s` disables the timeout (default: `0s`)
        5.  Maximum time to wait for writing data to a socket or connection; `0s` disables the timeout (default: `0s`)
        6.  Whether to enable `TCP keep-alive` for a socket or connection (default: `false`)
        7.  Whether to always send the `Connection: keep-alive` response header (default: `false`)
        8.  Whether to send the `Server: Kora` response header (default: `false`)
        9.  Whether to always send the `Date` response header (default: `true`)
        10.  Maximum allowed size of an incoming request body (default: `256MiB`)
        11.  Enables module logging (default: `false`)
        12.  Enables call stack logging on exception (default: `true`)
        13.  Query parameter names whose values are masked in the log, compared case-insensitively (default: `[]`). See [Masking](#telemetry-masking)
        14.  Request and response header names whose values are masked in the log, compared case-insensitively (default: `[ "authorization", "cookie", "set-cookie" ]`). See [Masking](#telemetry-masking)
        15.  Whether to log the full request path instead of the route template; when not specified, the template is used except at `TRACE`, where the full path is used (default not specified, optional)
        16.  Maximum request body size that may be written to the log; a larger body is logged without content (default: `2MiB`)
        17.  Maximum response body size that may be written to the log; a larger body is logged without content (default: `2MiB`)
        18.  Enables module metrics (default: `false`)
        19.  Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
        20.  Configures metric tags (default: `{}`)
        21.  Enables module tracing (default: `true`)
        22.  Whether to put the full request path into the `url.path` span attribute (default: `true`)
        23.  Configures tracing attributes (default: `{}`)

Module metrics are described in the [Metrics Reference](metrics.md#http-server) section.

### System server { #system-server }

The system server is configured in its own `httpServer.system` section.
`SystemHttpServerConfig` extends `HttpServerConfig`, so all options above are available there as well,
plus the paths of the system endpoints:

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer.system {
        port = 8085 //(1)!
        metricsPath = "/metrics" //(2)!
        readinessPath = "/system/readiness" //(3)!
        livenessPath = "/system/liveness" //(4)!
        telemetry.tracing.enabled = false //(5)!
    }
    ```

    1.  System `HTTP` server port (default: `8085`)
    2.  Path to get [metrics](metrics.md) on the system server (default: `/metrics`)
    3.  Path to get [readiness probe](probes.md) status on the system server (default: `/system/readiness`)
    4.  Path to get [liveness probe](probes.md) status on the system server (default: `/system/liveness`)
    5.  Enables tracing of system server requests (default: `false`, unlike the public server)

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      system:
        port: 8085 #(1)!
        metricsPath: "/metrics" #(2)!
        readinessPath: "/system/readiness" #(3)!
        livenessPath: "/system/liveness" #(4)!
        telemetry:
          tracing:
            enabled: false #(5)!
    ```

    1.  System `HTTP` server port (default: `8085`)
    2.  Path to get [metrics](metrics.md) on the system server (default: `/metrics`)
    3.  Path to get [readiness probe](probes.md) status on the system server (default: `/system/readiness`)
    4.  Path to get [liveness probe](probes.md) status on the system server (default: `/system/liveness`)
    5.  Enables tracing of system server requests (default: `false`, unlike the public server)

### Undertow { #undertow }

`Undertow`-specific transport settings live in a separate `httpServer.undertow` section and are shared
by both servers, because they configure a single `XnioWorker`:

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer.undertow {
        ioThreads = 4 //(1)!
        threadKeepAliveTimeout = "60s" //(2)!
    }
    ```

    1.  Number of network I/O threads (default: number of available processors, but not less than `2`)
    2.  Maximum idle lifetime of a worker thread (default: `60s`)

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      undertow:
        ioThreads: 4 #(1)!
        threadKeepAliveTimeout: "60s" #(2)!
    ```

    1.  Number of network I/O threads (default: number of available processors, but not less than `2`)
    2.  Maximum idle lifetime of a worker thread (default: `60s`)

Request handling itself does not use a bounded blocking pool: each connection is dispatched to a virtual thread,
so there are no `blockingThreads` or `virtualThreadsEnabled` options.
The response body is written to the socket over `NIO` by the `Undertow` I/O threads. A body whose content is not already in memory
is buffered on the request's virtual thread and sent in one piece while it fits into `64KiB`; a larger one is streamed through a bounded pipe,
so a large response is never held in memory as a whole.

For everything that has no configuration option, Kora provides `Configurer<T>` extension points.
A `Configurer<T>` receives the object being built and returns the object to use:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends UndertowPublicHttpServerModule {

        default Configurer<Undertow.Builder> undertowConfigurer() { //(1)!
            return builder -> builder.setServerOption(UndertowOptions.ENABLE_HTTP2, true);
        }

        default Configurer<XnioWorker.Builder> workerConfigurer() { //(2)!
            return builder -> builder.setWorkerName("my-worker");
        }
    }
    ```

    1.  Configures the `Undertow` builder of the public server before it is started
    2.  Configures the `XnioWorker` shared by both servers

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : UndertowPublicHttpServerModule {

        fun undertowConfigurer(): Configurer<Undertow.Builder> = //(1)!
            Configurer { builder -> builder.setServerOption(UndertowOptions.ENABLE_HTTP2, true) }

        fun workerConfigurer(): Configurer<XnioWorker.Builder> = //(2)!
            Configurer { builder -> builder.setWorkerName("my-worker") }
    }
    ```

    1.  Configures the `Undertow` builder of the public server before it is started
    2.  Configures the `XnioWorker` shared by both servers

An untagged `Configurer<Undertow.Builder>` applies to the **public** server.
To configure the system server, mark the component with the `@SystemApi` tag.

## Custom internal HTTP server { #internal-server }

`UndertowHttpServerFactoryModule` creates an additional server with its own routes and configuration. Give the [factory module](container.md#factory-module-tag) and controller the same tag: generated handlers inherit that tag and are registered only on the matching server.

Place `InternalHttpModule` in the same compilation module as `@KoraApp`: `@Module` includes it automatically. Keep `UndertowSystemHttpServerModule` or `UndertowPublicHttpServerModule` on the application interface. `UndertowSystemHttpServerModule` provides shared Undertow components and the system server; an existing `UndertowPublicHttpServerModule` also keeps the public server running. Use the same `http-server-undertow` dependency.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface InternalHttpModule {
        interface InternalApi { }

        @FactoryModule
        @Tag(InternalApi.class)
        default UndertowHttpServerFactoryModule internalHttpApi() {
            return new UndertowHttpServerFactoryModule("kora-undertow-internal", "httpServer.internal");
        }
    }
    ```

    ```java
    @Component
    @HttpController
    @Tag(InternalHttpModule.InternalApi.class)
    public final class InternalHelloController {
        @HttpRoute(method = HttpMethod.GET, path = "/hello")
        public String hello() {
            return "Hello World";
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface InternalHttpModule {
        interface InternalApi

        @FactoryModule
        @Tag(InternalApi::class)
        fun internalHttpApi(): UndertowHttpServerFactoryModule =
            UndertowHttpServerFactoryModule("kora-undertow-internal", "httpServer.internal")
    }
    ```

    ```kotlin
    @Component
    @HttpController
    @Tag(InternalHttpModule.InternalApi::class)
    class InternalHelloController {
        @HttpRoute(method = HttpMethod.GET, path = "/hello")
        fun hello(): String = "Hello World"
    }
    ```

The first factory argument names the server for threads and telemetry; the second specifies the `HttpServerConfig` section. Set `httpServer.internal.port` in the application configuration, for example to `8086`; other settings for this server also belong under `httpServer.internal`.

`GET http://localhost:8086/hello` returns `Hello World`. Shared transport settings remain under `httpServer.undertow`. Use the same `InternalApi` tag for internal server `HttpServerInterceptor` and `Configurer<Undertow.Builder>` components. The tag separates routes; network settings restrict access to the port. See [OpenAPI management](openapi-management.md#internal-server) for a similar OpenAPI example.

## SomeController declarative { #somecontroller-declarative }

The `@HttpController` annotation should be used to create a controller, and the `@Component` annotation should be used to register it as a dependency.
The `@HttpRoute` annotation is responsible for specifying the HTTP path and method for a particular handler method.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component //(1)!
    @HttpController //(2)!
    public final class SomeController {

        //(3)!
        @HttpRoute(method = HttpMethod.POST,  //(4)!
                   path = "/hello/world")  //(5)!
        public String helloWorld() {
            return "Hello World";
        }
    }
    ```

    1. Indicates that the class is a component and should be registered in the application dependency container
    2. Indicates that the class is a controller and contains HTTP handlers
    3. Indicates that the method is a path handler in the controller
    4. Indicates the type of the handler `HTTP` method
    5. Indicates the path of the handler method

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component //(1)!
    @HttpController //(2)!
    class SomeController {

        //(3)!
        @HttpRoute(method = HttpMethod.POST,  //(4)!
                   path = "/hello/world") //(5)!
        fun helloWorld(): String {
            return "Hello World"
        }
    }
    ```

    1. Indicates that the class is a component and should be registered in the application dependency container
    2. Indicates that the class is a controller and contains HTTP handlers
    3. Indicates that the method is a path handler in the controller
    4. Indicates the type of the handler `HTTP` method
    5. Indicates the path of the handler method

`HttpRoute.method()` is a `String`, and `HttpMethod` is a set of constants (`GET`, `HEAD`, `POST`, `PUT`, `DELETE`,
`CONNECT`, `OPTIONS`, `TRACE`, `PATCH`, `QUERY`), so a non-standard method can be written as a literal:
`@HttpRoute(method = "PURGE", path = "/cache")`.

### Routing { #routing }

`@HttpRoute` matches a request by its `method` (an [HTTP method](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods) from `HttpMethod`) and its `path`.
The `path` is a template that must start with `/` and may contain one or more `{name}` segments — each is a [path parameter](#path-parameter) bound with `@Path`:

* `/users` — a static path
* `/users/{id}` — one path parameter
* `/users/{userId}/orders/{orderId}` — several path parameters, including in the middle of the path

A path parameter always matches exactly one path segment; a value never spans a `/`.

**Trailing slash.** By default the match is exact, so `/users` and `/users/` are **different** routes — a request to `/users/` against a `/users` route returns `404`.
To treat them as the same route, enable `httpServer.ignoreTrailingSlash` (see [Configuration](#configuration)):

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
        ignoreTrailingSlash = true
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      ignoreTrailingSlash: true
    ```

**Method matching.** A path served with a method that has no matching route returns `405 Method Not Allowed`; an unknown path returns `404 Not Found`.
The matched template is available at runtime as `HttpServerRequest.route()` and is used as the low-cardinality path label in metrics and tracing (see [Telemetry](#telemetry)).

### Request { #request }

This section describes how an `HTTP` request is converted into controller method arguments.
Special annotations are used for request parts, and the request body is passed as an argument without such an annotation.

#### String parameter conversion { #string-parameter-reader }

Values from paths, query parameters, headers, and `cookie` arrive as strings.
Kora uses `HttpServerParameterReader<T>` to convert a string into the target type:

```java
public interface HttpServerParameterReader<T> {
    T read(String string);
}
```

`HttpServerParameterReader<T>` is looked up as a graph component by the exact parameter type. If the parameter is declared as `List<T>` or `Set<T>`,
the converter is applied to every value separately.

`String`, `Boolean`, `Integer`, `Long`, `Double` and `UUID` are parsed by the generated handler itself and need no converter.
Out of the box Kora also provides converters for `Float`, `BigInteger`, `BigDecimal`, `Duration`,
`LocalDate`, `LocalTime`, `LocalDateTime`, `OffsetTime`, `OffsetDateTime`, `ZonedDateTime`, and any `enum`.
For `enum`, the default mapping uses the value name via `Enum.name()`. If a value cannot be converted, the request is completed
with a `400` response through `HttpServerResponseException`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record UserId(long value) {}

    @Module
    public interface UserIdModule {

        default HttpServerParameterReader<UserId> userIdParameterReader() {
            return HttpServerParameterReader.of(
                value -> new UserId(Long.parseLong(value)),
                value -> "Invalid user id: " + value
            );
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class UserId(val value: Long)

    @Module
    interface UserIdModule {

        fun userIdParameterReader(): HttpServerParameterReader<UserId> {
            return HttpServerParameterReader.of(
                { value -> UserId(value.toLong()) },
                { value -> "Invalid user id: $value" }
            )
        }
    }
    ```

After registering the converter, the custom type can be used in controller parameters:

```java
@HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
public User get(@Path("id") UserId id) {
    return userService.get(id);
}
```

#### Path parameter { #path-parameter }

`@Path` - denotes the value of the request path part, the parameter itself is specified in `{path}` in the path
and the name of the parameter is specified in `value` or defaults to the name of the method argument.
The value is converted through `HttpServerParameterReader<T>`, so both built-in and custom types can be used.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/{pathName}")
        public String helloWorld(@Path("pathName") String pathValue) {
            return "Hello World";
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/{pathName}")
        fun helloWorld(
            @Path("pathName") pathValue: String
        ): String {
            return "Hello World";
        }
    }
    ```

A path parameter is always required: if the name in `@Path` is absent from the route template,
compilation fails with `Path parameter '...' is not present in the request mapping path`.

#### Query parameter { #query-parameter }

`@Query` - value of the query parameter, the name of the parameter is specified in `value` or is equal to the name of the method argument by default.
Single values, `List<T>`, and `Set<T>` are supported. `List<T>` keeps all parameter values,
while `Set<T>` removes duplicates and preserves the order of first occurrence.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        public String helloWorld(@Query("queryName") String queryValue,
                                 @Query("queryNameList") List<String> queryValues) {
            return "Hello World";
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun helloWorld(
            @Query("queryName") queryValue: String,
            @Query("queryNameList") queryValues: List<String>
        ): String {
            return "Hello World";
        }
    }
    ```

A query parameter present without a value (`/hello/world?queryName`) counts as missing:
a required parameter is answered with `400` and the message `Query parameter 'queryName' is required`.

#### Request header { #request-header }

`@Header` - value of [request header](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers), the parameter name is specified in `value` or defaults to the method argument name.
Single values, `List<T>`, and `Set<T>` are supported. `List<T>` and `Set<T>` use all values of the header.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        public String helloWorld(@Header("headerName") String headerValue,
                                 @Header("headerNameList") List<String> headerValues) {
            return "Hello World";
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun helloWorld(
            @Header("headerName") headerValue: String,
            @Header("headerNameList") headerValues: List<String>
        ): String {
            return "Hello World";
        }
    }
    ```

#### Request body { #request-body }

Specifying the request body requires using a method argument without special annotations.
By default, `byte[]`, `ByteBuffer`, `String`, `InputStream`, `HttpBodyInput`, `FormUrlEncoded`, `FormMultipart`,
and custom types through `HttpServerRequestMapper<T>` are supported.

`InputStream` and `HttpBodyInput` give access to the body without buffering it in memory, which is useful for large uploads.

##### JSON { #json }

In request body should be treated as `JSON`, than it must be annotated via `@Json` tag to require handler for injection with `JsonReader<T>`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        @Json
        public record Request(String name) {}

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        public String helloWorld(@Json Request body) { //(1)!
            return "Hello World";
        }
    }
    ```

    1. Specifies that the body should be read as `JSON`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        @Json
        data class Request(val name: String)

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun helloWorld(@Json body: Request): String { //(1)!
            return "Hello World"
        }
    }
    ```

    1. Specifies that the body should be read as `JSON`

The [JSON](json.md) module is required.

##### Form UrlEncoded { #form-urlencoded }

Declare a `FormUrlEncoded` (from `io.koraframework.http.common.form`) argument to accept a request with the
`application/x-www-form-urlencoded` content type ([form data](https://www.w3.org/TR/html401/interact/forms.html#h-17.13.4.1)).
No `@Json` or `@Mapping` annotation is needed — Kora has a built-in reader for this type.

`FormUrlEncoded` is iterable and provides:

* `get(String name)` — returns the `FormUrlEncoded.FormPart` with that name, or `null`
* `FormPart.name()` — the field name
* `FormPart.values()` — all values of that field (a field may be repeated in the form)

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/form/encoded")
        public String handle(FormUrlEncoded body) {
            FormUrlEncoded.FormPart name = body.get("name"); //(1)!
            String firstName = (name != null) ? name.values().get(0) : null;
            return "Hello " + firstName;
        }
    }
    ```

    1. Reads the `name` field from the submitted form; `FormUrlEncoded.get(String)` returns `FormPart(String name, List<String> values)` or `null`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/form/encoded")
        fun handle(body: FormUrlEncoded): String {
            val name = body.get("name") //(1)!
            val firstName = name?.values()?.firstOrNull()
            return "Hello $firstName"
        }
    }
    ```

    1. Reads the `name` field from the submitted form; `FormUrlEncoded.get(String)` returns `FormPart(String name, List<String> values)` or `null`

##### Form Multipart { #form-multipart }

Declare a `FormMultipart` (from `io.koraframework.http.common.form`) argument to accept a `multipart/form-data`
request ([binary form](https://www.w3.org/TR/html401/interact/forms.html#h-17.13.4.2)), typically used for file uploads.
No `@Json` or `@Mapping` annotation is needed.

`FormMultipart.parts()` returns the list of parts. `FormMultipart.FormPart` is a sealed interface with the subtypes
`MultipartData`, `MultipartFile` and `MultipartFileStream`, but the server reads the whole request into memory and
delivers **every** part, text fields included, as `MultipartFile`: `name()`, `fileName()`, `contentType()` and `content()` (`byte[]`).
`MultipartData` and `MultipartFileStream` are used when a form is sent, for example by an [HTTP client](http-client.md).

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/form/multipart")
        public String handle(FormMultipart body) {
            for (FormMultipart.FormPart part : body.parts()) {
                if (part instanceof FormMultipart.FormPart.MultipartFile file) { //(1)!
                    String name = file.name();
                    String fileName = file.fileName(); //(2)!
                    String contentType = file.contentType();
                    byte[] content = file.content();
                }
            }
            return "OK";
        }
    }
    ```

    1. Every part of an incoming form is a `MultipartFile`
    2. `fileName()` and `contentType()` are `null` when the part does not declare them, as with a plain text field

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/form/multipart")
        fun handle(body: FormMultipart): String {
            for (part in body.parts()) {
                if (part is FormMultipart.FormPart.MultipartFile) { //(1)!
                    val name = part.name()
                    val fileName = part.fileName() //(2)!
                    val contentType = part.contentType()
                    val content = part.content()
                }
            }
            return "OK"
        }
    }
    ```

    1. Every part of an incoming form is a `MultipartFile`
    2. `fileName()` and `contentType()` are `null` when the part does not declare them, as with a plain text field

#### Cookie { #cookie }

`@Cookie` - [Cookie](https://developer.mozilla.org/en-US/docs/Glossary/Cookie) value, the parameter name is specified in `value` or defaults to the method argument name.
The value can be received as `String`, as a `Cookie` type with name, value, and attributes, or as another type through `HttpServerParameterReader<T>`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        public String helloWorld(@Cookie("cookieName") String cookieValue) {
            return "Hello World";
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun helloWorld(
            @Cookie("cookieName") cookieValue: String
        ): String {
            return "Hello World";
        }
    }
    ```

#### Custom parameter { #custom-parameter }

If a method argument needs to be assembled from the request manually, use the `HttpServerRequestMapper<T>` interface.
This is useful for user context, authorization, complex header validation, or several request parts at once:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        public record UserContext(String userId, String traceId) {}

        @Component //(1)!
        public static final class RequestMapper implements HttpServerRequestMapper<UserContext> {

            @Override
            public UserContext apply(HttpServerRequest request) {
                return new UserContext(request.headers().getFirst("x-user-id"), request.headers().getFirst("x-trace-id"));
            }
        }

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        public String get(@Mapping(RequestMapper.class) UserContext context) {
            return "Hello World";
        }
    }
    ```

    1. The generated controller module **injects** the mapper as a dependency, so the mapper class must be a graph component

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        data class UserContext(val userId: String?, val traceId: String?)

        @Component //(1)!
        class RequestMapper : HttpServerRequestMapper<UserContext> {

            override fun apply(request: HttpServerRequest): UserContext {
                return UserContext(
                    request.headers().getFirst("x-user-id"),
                    request.headers().getFirst("x-trace-id")
                )
            }
        }

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun get(@Mapping(RequestMapper::class) context: UserContext): String {
            return "Hello World"
        }
    }
    ```

    1. The generated controller module **injects** the mapper as a dependency, so the mapper class must be a graph component

???+ warning "No component found for dependency"

    A mapper class referenced from `@Mapping` is never created by the generated module — it is requested from the container.
    Forgetting `@Component` produces a graph build error:

    ```
    No component found for dependency:
      SomeController.RequestMapper (no tags)
    ```

    The same applies to interceptor classes referenced from `@InterceptWith`.

An exception thrown by a mapper is turned into a `400` response unless it is itself an `HttpServerResponse`,
so a mapper is also a convenient place to reject a malformed request with an exact status code.

#### Full request { #full-request }

A controller method can accept `HttpServerRequest` itself when the handler needs the raw request:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        @HttpRoute(method = HttpMethod.GET, path = "/request")
        public HttpServerResponse get(HttpServerRequest request) {
            var header = request.headers().getFirst("header"); //(1)!
            var query = request.queryParams().get("query"); //(2)!
            var path = request.pathParams().get("path"); //(3)!
            return HttpServerResponse.of(200, HttpBody.plaintext(request.path()));
        }
    }
    ```

    1. `HttpHeaders` with `getFirst` and `getAll`
    2. `Map<String, List<String>>` of query parameters
    3. `Map<String, String>` of path parameters resolved from the route template

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        @HttpRoute(method = HttpMethod.GET, path = "/request")
        fun get(request: HttpServerRequest): HttpServerResponse {
            val header = request.headers().getFirst("header") //(1)!
            val query = request.queryParams()["query"] //(2)!
            val path = request.pathParams()["path"] //(3)!
            return HttpServerResponse.of(200, HttpBody.plaintext(request.path()))
        }
    }
    ```

    1. `HttpHeaders` with `getFirst` and `getAll`
    2. `Map<String, List<String>>` of query parameters
    3. `Map<String, String>` of path parameters resolved from the route template

`HttpServerRequest` also exposes `host()`, `scheme()`, `method()`, `path()`, `pathTemplate()`, `cookies()` and `body()`.

#### Required parameters { #required-parameters }

===! ":fontawesome-brands-java: `Java`"

    By default, all arguments declared in a method are **required**.
    If a required value is missing in the request, Kora returns a `400` response.

=== ":simple-kotlin: `Kotlin`"

    By default, all method arguments that do not use the [Kotlin Nullability](https://kotlinlang.org/docs/null-safety.html) syntax
    are **required**. If a required value is missing in the request, Kora returns a `400` response.

#### Optional parameters { #optional-parameters }

===! ":fontawesome-brands-java: `Java`"

    If a method argument is optional, meaning it may be missing in the request,
    use `@Nullable` or `Optional<T>` for single values:

    ```java
    @Component
    @HttpController
    public final class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        public String helloWorld(@Nullable @Query("queryName") String queryValue) { //(1)!
            return "Hello World";
        }
    }
    ```

    1.  Kora and the examples use `org.jspecify.annotations.Nullable`; any annotation whose simple name is `Nullable` is accepted.

=== ":simple-kotlin: `Kotlin`"

    Use the [Kotlin Nullability](https://kotlinlang.org/docs/null-safety.html) syntax and mark such a parameter as optional:

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun helloWorld(@Query("queryName") queryValue: String?): String {
            return "Hello World"
        }
    }
    ```

### Response { #response }

By default, standard return value types can be used: `byte[]`, `ByteBuffer`, `String`, `HttpBodyOutput`.
They are processed with status `200` and the corresponding response content type header.
A `void` method also answers with `200` and an empty body.

If the status, headers, or body must be specified manually, the method can return `HttpServerResponse`.
The main `HttpServerResponse` contract consists of a response code, headers, and an optional body:

```java
public interface HttpServerResponse {
    int code();
    HttpHeaders headers();
    @Nullable
    HttpBodyOutput body();
}
```

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        public HttpServerResponse helloWorld() {
            return HttpServerResponse.of(
                    200, //(1)!
                    HttpHeaders.of("headerName", "headerValue"), //(2)!
                    HttpBody.plaintext("Hello World") //(3)!
            );
        }
    }
    ```

    1. `HTTP` response status code
    2. Response headers
    3. Response body

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun helloWorld(): HttpServerResponse {
            return HttpServerResponse.of(
                200, //(1)!
                HttpHeaders.of("headerName", "headerValue"), //(2)!
                HttpBody.plaintext("Hello World") //(3)!
            )
        }
    }
    ```

    1. `HTTP` response status code
    2. Response headers
    3. Response body

`HttpBody` provides the factory methods `empty()`, `plaintext(...)`, `json(...)`, `octetStream(...)` and `of(contentType, ...)`.
For a streaming response use `HttpBodyOutput.of(contentType, InputStream)` or `HttpBodyOutput.of(contentType, os -> ...)`.

#### Streaming with InputStream { #streaming-inputstream }

Return `HttpBodyOutput.of(contentType, inputStream)` to send a body without loading the whole file into a byte array. Open the stream in the controller and transfer ownership to the response body: the server closes it after response processing, including write failures. Do not wrap the returned stream in a controller-level `try-with-resources` / `use`, because that would close it before the server reads it.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpRoute(method = HttpMethod.GET, path = "/report")
    public HttpServerResponse report() throws java.io.IOException {
        var path = java.nio.file.Path.of("/data/report.csv");
        var stream = java.nio.file.Files.newInputStream(path);
        return HttpServerResponse.of(200, HttpBodyOutput.of("text/csv", stream));
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpRoute(method = HttpMethod.GET, path = "/report")
    fun report(): HttpServerResponse {
        val path = java.nio.file.Path.of("/data/report.csv")
        val stream = java.nio.file.Files.newInputStream(path)
        return HttpServerResponse.of(200, HttpBodyOutput.of("text/csv", stream))
    }
    ```


Import `HttpBodyOutput` from `io.koraframework.http.common.body`. The fixed server-side path keeps this example independent of user-provided filenames. If the exact length is known and the content cannot change during transfer, use `of(contentType, length, stream)` or `octetStream(length, stream)`; otherwise leave it unknown (`-1`). HTTP/1.1 can then use chunked framing; HTTP/2 uses its own data frames.

Undertow buffers a small unknown body up to `64KiB`; larger bodies use a bounded pipe and socket backpressure paces the producer. Reading an `InputStream` is blocking work on the request virtual thread. A disconnected client causes writing to fail; it does not guarantee that a custom blocking stream will immediately stop reading, so configure source read timeouts too. If headers are already sent, a read/write failure cannot be replaced with a JSON error response. This is byte streaming, not SSE event framing.

#### JSON { #json-2 }

If the response should be returned as `JSON`, use the `@Json` annotation on the method.
Kora will find or create `JsonWriter<T>` for the response type:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        @Json
        public record Response(String greeting) {}

        @Json //(1)!
        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        public Response helloWorld() {
            return new Response("Hello World");
        }
    }
    ```

    1. Specifies that the response should be in `JSON` format

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        @Json
        data class Response(val greeting: String)

        @Json //(1)!
        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun helloWorld(): Response {
            return Response("Hello World")
        }
    }
    ```

    1. Specifies that the response should be in `JSON` format

The [JSON](json.md) module is required.

#### Response entity { #response-entity }

If the body, headers, and response status code should be returned together,
use `HttpResponseEntity<T>`, a wrapper around the response body.

Below is an example similar to the `JSON` example with the `HttpResponseEntity` wrapper:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        @Json
        public record Response(String greeting) {}

        @Json
        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        public HttpResponseEntity<Response> helloWorld() {
            return HttpResponseEntity.of(200, HttpHeaders.of("myHeader", "12345"), new Response("Hello World"));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        @Json
        data class Response(val greeting: String)

        @Json
        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun helloWorld(): HttpResponseEntity<Response> {
            return HttpResponseEntity.of(200, HttpHeaders.of("myHeader", "12345"), Response("Hello World"));
        }
    }
    ```

`HttpResponseEntity.of(code, body)` is available when only the status code has to be overridden.
The `content-type` set on the entity headers wins over the one produced by the underlying mapper.

#### Respond exception { #respond-exception }

If processing should be interrupted and an error should be returned immediately, throw `HttpServerResponseException`.
It is both an exception and an `HttpServerResponse`, so it can be thrown from a controller, service, or parameter converter.

The `HttpServerResponseException.of(...)` factory methods allow specifying the status code, response text, cause, and headers.
The response body is written as `text/plain;charset=utf-8`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/{pathName}")
        public String helloWorld(@Path("pathName") String pathValue) {
            if("null".equals(pathValue)) {
                throw HttpServerResponseException.of(400, "Bad request");
            }
            return "OK";
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/{pathName}")
        fun helloWorld(@Path("pathName") pathValue: String): String {
            if ("null" == pathValue) {
                throw HttpServerResponseException.of(400, "Bad request")
            }
            return "OK"
        }
    }
    ```

#### Custom response { #custom-response }

If the response needs to be created in a custom way, use the `HttpServerResponseMapper<T>` interface.
It receives the original `HttpServerRequest` and the controller method result, and returns a ready `HttpServerResponse`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        public record HelloWorldResponse(String greeting, String name) {}

        @Component //(1)!
        public static final class ResponseMapper implements HttpServerResponseMapper<HelloWorldResponse> {

            @Override
            public HttpServerResponse apply(HttpServerRequest request, HelloWorldResponse result) {
                return HttpServerResponse.of(200, HttpBody.plaintext(result.greeting() + " - " + result.name()));
            }
        }

        @Mapping(ResponseMapper.class)
        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        public HelloWorldResponse helloWorld() {
            return new HelloWorldResponse("Hello World", "Bob");
        }
    }
    ```

    1. As with request mappers, the class is injected into the generated module and must be a graph component

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        data class HelloWorldResponse(val greeting: String, val name: String)

        @Component //(1)!
        class ResponseMapper : HttpServerResponseMapper<HelloWorldResponse> {

            override fun apply(request: HttpServerRequest, result: HelloWorldResponse?): HttpServerResponse { //(2)!
                requireNotNull(result)
                return HttpServerResponse.of(200, HttpBody.plaintext("${result.greeting} - ${result.name}"))
            }
        }

        @Mapping(ResponseMapper::class)
        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun helloWorld(): HelloWorldResponse {
            return HelloWorldResponse("Hello World", "Bob")
        }
    }
    ```

    1. As with request mappers, the class is injected into the generated module and must be a graph component
    2. The contract declares the result as nullable, so the Kotlin override must accept `HelloWorldResponse?` — otherwise it does not resolve as an override

### Routes { #routes }

A route is the concatenation of the `@HttpController` path prefix and the `@HttpRoute` path:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController("/api/v1") //(1)!
    public final class SomeController {

        @HttpRoute(method = HttpMethod.GET, path = "/pets/{id}") //(2)!
        public String get(@Path long id) {
            return "OK";
        }

        @HttpRoute(method = HttpMethod.GET, path = "/files/*") //(3)!
        public String file() {
            return "OK";
        }
    }
    ```

    1. Path prefix applied to every route of the controller
    2. Route with a path parameter, the resulting route is `/api/v1/pets/{id}`
    3. Route with a terminal wildcard, the resulting route is `/api/v1/files/*`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController("/api/v1") //(1)!
    class SomeController {

        @HttpRoute(method = HttpMethod.GET, path = "/pets/{id}") //(2)!
        fun get(@Path id: Long): String = "OK"

        @HttpRoute(method = HttpMethod.GET, path = "/files/*") //(3)!
        fun file(): String = "OK"
    }
    ```

    1. Path prefix applied to every route of the controller
    2. Route with a path parameter, the resulting route is `/api/v1/pets/{id}`
    3. Route with a terminal wildcard, the resulting route is `/api/v1/files/*`

Route matching rules:

- A path parameter `{name}` matches a single path segment.
- A wildcard `*` is allowed **once** and only in the **final** segment: `/files/*`, `/files/*.js`, `/files/file-*.txt`,
  `/tenant/{id}/report-*.json`. Anything else (`/foo/*/bar`, `/foo/**`, `/foo/a*b*c`, `/foo/{*}`) fails compilation with
  `HTTP server route path is invalid`.
- Two handlers with equivalent templates for the same method make the server fail on start with
  `Cannot add path template ..., matcher already contains an equivalent pattern ...`.
- An unknown path answers `404`; a known path requested with an unsupported method answers `405`
  with the `Allow` header listing the registered methods.
- With `httpServer.ignoreTrailingSlash = true` an additional variant of every non-wildcard route is registered,
  so `/my/path` and `/my/path/` hit the same handler.

### Signatures { #signatures }

Available signatures for declarative `HTTP` handler methods out of the box:

===! ":fontawesome-brands-java: `Java`"

    The `T` refers to the type of the return value. It can be a body type (`void`, `String`, `byte[]`, a `@Json` type, etc.),
    an [`HttpResponseEntity<T>`](#response-entity) to also set status and headers, or the full [`HttpServerResponse`](#response).

    - `T myMethod()`
    - `void myMethod()` — answers `200` with an empty body

    Returning `CompletionStage<T>`, `Future<T>` or a reactive `Publisher<T>` is **not supported**:
    the processor prints a warning that the return type *"is unsupported and has no meaning"*,
    and the graph build then fails because there is no `HttpServerResponseMapper` for such a type.

=== ":simple-kotlin: `Kotlin`"

    By `T` we mean the type of the return value — a body type, an [`HttpResponseEntity<T>`](#response-entity), or the full [`HttpServerResponse`](#response).

    - `myMethod(): T`
    - `myMethod(): Unit` — answers `200` with an empty body

    `suspend` methods are **not supported** and are rejected at compile time with
    *"Suspend methods are not supported by the HTTP server controller generator"*.
    For parallel work inside a handler use `StructuredTaskScope` instead of coroutines.

## Interceptors { #interceptors }

Interceptors can be created to change behavior or add shared logic around request processing.
Use the `HttpServerInterceptor` interface:

```java
public interface HttpServerInterceptor {
    HttpServerResponse intercept(HttpServerRequest request, InterceptChain chain) throws Exception;

    interface InterceptChain {
        HttpServerResponse process(HttpServerRequest request) throws Exception;
    }
}
```

An interceptor receives the `HttpServerRequest` and the chain of further processing.
To pass the request further, call `chain.process(request)`. If the interceptor returns a response itself,
the controller handler is not called. Because the call is synchronous, an exception thrown further down the chain
is simply caught with `try/catch`.

Interceptors can be used on:

- Specific controller methods — `@InterceptWith` on the method
- Entire controller — `@InterceptWith` on the class
- All controllers at once — register the interceptor component with the `@Tag(HttpServer.class)` tag; there can be several global interceptors

`@InterceptWith` is repeatable, and interceptors declared on the class run before those declared on the method.
Global interceptors are applied in a deterministic order sorted by the interceptor class simple name.

**Execution order:**

Interceptors declared with `@InterceptWith` run in the order they are declared (top to bottom): controller-level interceptors
wrap method-level ones, and within the same target the order follows the annotation order. Each interceptor may modify the request
before `chain.process(...)`, short-circuit by returning a response without calling the chain, or handle the result/exception afterwards.

Global interceptors registered with `@Tag(HttpServerModule.class)` have **no guaranteed order between each other**.
If a strict order across global concerns is required (for example authorization must run before error mapping), do not register
several global interceptors — implement a **single** global interceptor that invokes the concerns in the required order internally.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    @InterceptWith(SomeController.ControllerInterceptor.class) //(1)!
    public final class SomeController {

        @Component
        public static final class ControllerInterceptor implements HttpServerInterceptor {

            @Override
            public HttpServerResponse intercept(HttpServerRequest request, InterceptChain chain) throws Exception {
                return chain.process(request);
            }
        }

        @Component
        public static final class MethodInterceptor implements HttpServerInterceptor {

            @Override
            public HttpServerResponse intercept(HttpServerRequest request, InterceptChain chain) throws Exception {
                return chain.process(request);
            }
        }

        @Tag(HttpServer.class) //(2)!
        @Component
        public static final class ServerInterceptor implements HttpServerInterceptor {

            @Override
            public HttpServerResponse intercept(HttpServerRequest request, InterceptChain chain) throws Exception {
                return chain.process(request);
            }
        }

        @InterceptWith(MethodInterceptor.class) //(3)!
        @HttpRoute(method = HttpMethod.POST, path = "/intercepted")
        public String helloWorld() {
            return "Hello World";
        }
    }
    ```

    1. Intercepts every route of this controller
    2. Intercepts every route of the public server, including `404` and `405` responses
    3. Intercepts only this route

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    @InterceptWith(SomeController.ControllerInterceptor::class) //(1)!
    class SomeController {

        @Component
        class ControllerInterceptor : HttpServerInterceptor {

            override fun intercept(request: HttpServerRequest, chain: HttpServerInterceptor.InterceptChain): HttpServerResponse {
                return chain.process(request)
            }
        }

        @Component
        class MethodInterceptor : HttpServerInterceptor {

            override fun intercept(request: HttpServerRequest, chain: HttpServerInterceptor.InterceptChain): HttpServerResponse {
                return chain.process(request)
            }
        }

        @Tag(HttpServer::class) //(2)!
        @Component
        class ServerInterceptor : HttpServerInterceptor {

            override fun intercept(request: HttpServerRequest, chain: HttpServerInterceptor.InterceptChain): HttpServerResponse {
                return chain.process(request)
            }
        }

        @InterceptWith(MethodInterceptor::class) //(3)!
        @HttpRoute(method = HttpMethod.POST, path = "/intercepted")
        fun helloWorld(): String {
            return "Hello World"
        }
    }
    ```

    1. Intercepts every route of this controller
    2. Intercepts every route of the public server, including `404` and `405` responses
    3. Intercepts only this route

???+ warning "Global interceptor tag"

    The framework collects global interceptors **only** by `@Tag(HttpServer.class)` —
    `HttpServerModule` declares the dependency as `@Tag(HttpServer.class) All<HttpServerInterceptor> interceptors`.
    Tagging a global interceptor with anything else compiles successfully and the interceptor is simply never invoked,
    so error handling, authentication or logging disappear without any warning. Cover it with a test.

    To intercept every request of the **system** server, use the `@SystemApi` tag instead.

### Error handling { #error-handling }

Error handling for all `HTTP` responses can also be implemented through an interceptor.
Below is an example of a global handler that turns exceptions into a `JSON` response.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(HttpServer.class)
    @Component
    public final class ErrorInterceptor implements HttpServerInterceptor {

        private static final Logger logger = LoggerFactory.getLogger(ErrorInterceptor.class);

        private final JsonWriter<ErrorTO> errorWriter;

        public ErrorInterceptor(JsonWriter<ErrorTO> errorWriter) { //(1)!
            this.errorWriter = errorWriter;
        }

        @Override
        public HttpServerResponse intercept(HttpServerRequest request, InterceptChain chain) {
            try {
                return chain.process(request);
            } catch (HttpServerResponseException e) { //(2)!
                return e;
            } catch (Exception e) {
                var body = HttpBody.json(errorWriter.toByteArray(new ErrorTO(e.getMessage()))); //(3)!
                if (e instanceof IllegalArgumentException) {
                    return HttpServerResponse.of(400, body);
                } else if (e instanceof TimeoutException) {
                    return HttpServerResponse.of(408, body);
                } else {
                    logger.error("Request '{} {}' failed", request.method(), request.path(), e);
                    return HttpServerResponse.of(500, body);
                }
            }
        }
    }
    ```

    1. The interceptor has a constructor dependency, so it must be a graph component
    2. `HttpServerResponseException` is itself a response, so it is returned as the client should see it
    3. `JsonWriter.toByteArray(...)` declares no checked exception, so no `IOException` handling is needed

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(HttpServer::class)
    @Component
    class ErrorInterceptor(private val errorWriter: JsonWriter<ErrorTO>) : HttpServerInterceptor { //(1)!

        private val logger = LoggerFactory.getLogger(ErrorInterceptor::class.java)

        override fun intercept(request: HttpServerRequest, chain: HttpServerInterceptor.InterceptChain): HttpServerResponse {
            try {
                return chain.process(request)
            } catch (e: HttpServerResponseException) { //(2)!
                return e
            } catch (e: Exception) {
                val body = HttpBody.json(errorWriter.toByteArray(ErrorTO(e.message))) //(3)!
                return when (e) {
                    is IllegalArgumentException -> HttpServerResponse.of(400, body)
                    is TimeoutException -> HttpServerResponse.of(408, body)
                    else -> {
                        logger.error("Request '{} {}' failed", request.method(), request.path(), e)
                        HttpServerResponse.of(500, body)
                    }
                }
            }
        }
    }
    ```

    1. The interceptor has a constructor dependency, so it must be a graph component
    2. `HttpServerResponseException` is itself a response, so it is returned as the client should see it
    3. `JsonWriter.toByteArray(...)` declares no checked exception, so no `IOException` handling is needed

Parameter parsing errors are handled by Kora before the controller method is called: a value that cannot be read
is answered with `400` and the message produced by `HttpServerParameterReader`. Such a response also passes through
the interceptor chain, so a global handler can reshape it.

## SomeController imperative { #somecontroller-imperative }

In order to create a controller, implement the `HttpServerRequestHandler.HandlerFunction` interface,
and then register it in the `HttpServerRequestHandler` handler.

The following example shows how to handle all the described declarative request parameters from the examples above:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface SomeModule {

        default HttpServerRequestHandler someHttpHandler() {
            return HttpServerRequestHandlerImpl.of(HttpMethod.POST, //(1)!
                                                   "/hello/{world}", //(2)!
                                                   (request) -> {
                var path = HttpRequestHandlerUtils.parsePathString(request, "world");
                var query = HttpRequestHandlerUtils.parseQueryStringNullable(request, "query");
                var queries = HttpRequestHandlerUtils.parseQueryStringListNullable(request, "Queries");
                var header = HttpRequestHandlerUtils.parseHeaderStringNullable(request, "header");
                var headers = HttpRequestHandlerUtils.parseHeaderStringListNullable(request, "Headers");
                return HttpServerResponse.of(200, HttpBody.plaintext("Hello World"));
            });
        }
    }
    ```

    1. Specifies the `HTTP` method type of the handler method
    2. Indicates the path of the handler method

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface SomeModule {

        fun someHttpHandler(): HttpServerRequestHandler {
            return HttpServerRequestHandlerImpl.of(
                HttpMethod.POST, //(1)!
                "/hello/{world}" //(2)!
            ) { request: HttpServerRequest ->
                val path = HttpRequestHandlerUtils.parsePathString(request, "world")
                val query = HttpRequestHandlerUtils.parseQueryStringNullable(request, "query")
                val queries = HttpRequestHandlerUtils.parseQueryStringListNullable(request, "Queries")
                val header = HttpRequestHandlerUtils.parseHeaderStringNullable(request, "header")
                val headers = HttpRequestHandlerUtils.parseHeaderStringListNullable(request, "Headers")
                HttpServerResponse.of(200, HttpBody.plaintext("Hello World"))
            }
        }
    }
    ```

    1. Specifies the `HTTP` method type of the handler method
    2. Indicates the path of the handler method

`HttpServerRequestHandlerImpl` also has shorthand factories per method — `get`, `head`, `post`, `put`, `delete`,
`connect`, `options`, `trace`, `patch` — and an overload with an `enabled` flag that lets a handler be excluded from routing
without removing it from the graph.

An untagged `HttpServerRequestHandler` is registered on the public server; a handler tagged with `@SystemApi`
is registered on the system server.

## Authorization { #authorization }

Kora provides a mechanism for extracting authorization context from HTTP requests via the `HttpServerPrincipalExtractor` interface.
This interface allows implementing any authentication scheme: [Basic/ApiKey/Bearer/OAuth](https://swagger.io/docs/specification/authentication/).

### How It Works { #how-it-works }

`HttpServerPrincipalExtractor<T, P>` receives the credential extracted from the request and returns a `Principal` object,
or `null` when the credential is not accepted.

```java
public interface HttpServerPrincipalExtractor<T, P extends Principal> {
    @Nullable
    P extract(HttpServerRequest request, @Nullable T token);
}
```

Where:

- `request` — the current HTTP request, from which additional data (headers, parameters) can be extracted
- `token` — the credential taken from the request (the `Authorization` header, an API key header, a query parameter or a cookie)
- `T` — the credential type: `String` for a single security scheme, or a generated `AuthData` record when several schemes are combined
- `P extends Principal` — the type of authorization context

The extractor is **invoked by the interceptors generated from an OpenAPI contract** — see [OpenAPI Integration](#openapi).
The generated interceptor reads the credential, calls `extract(...)`, and on a non-null result executes the rest of the chain
inside `Principal.with(principal, () -> chain.process(request))`. When the result is `null` (or the required scopes are missing),
it throws `HttpServerResponseException.of(401, "Unauthorized")`.

For a service without an OpenAPI contract, write a plain [interceptor](#interceptors) instead — see [Authorization without OpenAPI](#authorization-manual).

### Authentication and authorization boundaries { #auth-boundaries }

Authentication validates credentials and creates a principal. Authorization decides whether that principal may perform the operation. A token extractor alone does not enforce ownership or business permissions: check those in the service as well when it can be called outside HTTP. Kora does not infer application roles from a custom principal.

For custom interceptors, use `HttpServerResponseException.of(401, "Unauthorized")` for missing/invalid credentials and `of(403, "Forbidden")` for an authenticated principal without permission. Bind a validated principal with `Principal.with(...)` around `chain.process(request)`. Throwing a bare `SecurityException` does not itself select an HTTP status; the example [error interceptor](#auth-error-handling) performs that mapping. In RC2, generated OpenAPI security returns `401` when no authentication requirement is satisfied, and `403` when the principal is authenticated but lacks the required scopes.

#### Service-level permission check { #service-permissions }

Use the `UserPrincipal` defined below to check a business permission in the service, even when HTTP authentication has already succeeded:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public void requireAdmin() {
        var principal = Principal.current();
        if (principal == null) {
            throw HttpServerResponseException.of(401, "Unauthorized");
        }
        if (!(principal instanceof UserPrincipal user) || !user.roles().contains("admin")) {
            throw HttpServerResponseException.of(403, "Forbidden");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun requireAdmin() {
        val principal = Principal.current()
            ?: throw HttpServerResponseException.of(401, "Unauthorized")
        if (principal !is UserPrincipal || "admin" !in principal.roles) {
            throw HttpServerResponseException.of(403, "Forbidden")
        }
    }
    ```

For a transport-independent service, throw your own permission exception and map it to HTTP in an interceptor. The direct HTTP exception here keeps the example small.

### Principal scope and outbound requests { #principal-propagation }

`Principal.current()` reads a `ScopedValue` available inside `Principal.with(...)`, including synchronous controller and service calls. A task submitted to an independent executor does not automatically receive that binding. Capture the validated principal and explicitly rebind it in the task if needed; do not keep request principals in singleton fields.

An outgoing HTTP client does not automatically copy the authenticated request token. Add credentials explicitly to a client argument or interceptor for a trusted destination; do not forward arbitrary inbound `Authorization` headers to every downstream service. Never log tokens.

### Verify security behavior { #security-testing }

Test requests with missing credentials, invalid credentials, valid credentials with insufficient scopes/roles, and valid permissions. Assert both the status and that protected business code was not called on rejection. Test service-level permission checks with `Principal.with(testPrincipal, () -> service.operation())`, then verify that `Principal.current()` is no longer bound after the callback. See [JUnit5](junit5.md) for replacing token validators and injecting the service.

### Custom Principal { #custom-principal }

Use can create a simple principal for API if needed with or without fields:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record ApiPrincipal(String client) implements Principal {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class ApiPrincipal(val client: String) : Principal
    ```

To pass additional authorization information (userId, roles, scope), create a custom `Principal` implementation:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record UserPrincipal(String userId, List<String> roles) implements Principal {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class UserPrincipal(val userId: String, val roles: List<String>) : Principal
    ```

If scope handling is required, use the `PrincipalWithScopes` interface:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record ScopedUser(String userId, Collection<String> scopes) implements PrincipalWithScopes {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class ScopedUser(val userId: String, val scopes: Collection<String>) : PrincipalWithScopes
    ```

### Basic Example { #basic-example }

Simple example of validating an API key, where `ApiKeyAuth` is the name of the security scheme from the OpenAPI contract:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface AuthModule {

        @ConfigSource("auth.apiKey")
        interface ApiKeyAuthConfig {
            String value();
        }

        @Tag(ApiSecurity.ApiKeyAuth.class) //(1)!
        default HttpServerPrincipalExtractor<String, Principal> apiKeyExtractor(ApiKeyAuthConfig config) {
            return (request, value) -> {
                if (value == null || !config.value().equals(value)) {
                    return null; //(2)!
                }
                return new ApiPrincipal("api-client");
            };
        }
    }
    ```

    1. The tag is named after the security scheme in the contract
    2. Returning `null` makes the generated interceptor answer `401 Unauthorized`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface AuthModule {

        @ConfigSource("auth.apiKey")
        interface ApiKeyAuthConfig {
            fun value(): String
        }

        @Tag(ApiSecurity.ApiKeyAuth::class) //(1)!
        fun apiKeyExtractor(config: ApiKeyAuthConfig): HttpServerPrincipalExtractor<String, Principal> {
            return HttpServerPrincipalExtractor { request, value ->
                if (value == null || config.value() != value) {
                    null //(2)!
                } else {
                    ApiPrincipal("api-client")
                }
            }
        }
    }
    ```

    1. The tag is named after the security scheme in the contract
    2. Returning `null` makes the generated interceptor answer `401 Unauthorized`

### Bearer Token { #bearer }

Example of validating a Bearer token with a custom `Principal` implementation.
For `Bearer`, `Basic` and `OAuth` schemes the generated interceptor passes the whole `Authorization` header value:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface BearerAuthModule {

        @Tag(ApiSecurity.BearerAuth.class)
        default HttpServerPrincipalExtractor<String, Principal> bearerExtractor(TokenValidator validator) {
            return (request, value) -> {
                if (value == null || !value.startsWith("Bearer ")) {
                    return null;
                }

                var token = value.substring("Bearer ".length());
                var userData = validator.validate(token);
                return userData == null
                    ? null
                    : new UserPrincipal(userData.userId(), userData.roles());
            };
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface BearerAuthModule {

        @Tag(ApiSecurity.BearerAuth::class)
        fun bearerExtractor(validator: TokenValidator): HttpServerPrincipalExtractor<String, Principal> {
            return HttpServerPrincipalExtractor { request, value ->
                if (value == null || !value.startsWith("Bearer ")) {
                    null
                } else {
                    val token = value.substring("Bearer ".length)
                    validator.validate(token)
                        ?.let { UserPrincipal(it.userId, it.roles) }
                }
            }
        }
    }
    ```

### Getting Principal { #getting-principal }

The current authorization context is bound to a `ScopedValue` and can be obtained anywhere during request processing:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public class SecureController {

        @HttpRoute(method = HttpMethod.GET, path = "/secure")
        public String getSecureData() {
            Principal principal = Principal.current(); //(1)!
            if (principal instanceof UserPrincipal user) {
                return "Hello, user: " + user.userId();
            }
            throw new SecurityException("Not authenticated");
        }
    }
    ```

    1. Returns `null` when no principal is bound for the current request

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SecureController {

        @HttpRoute(method = HttpMethod.GET, path = "/secure")
        fun getSecureData(): String {
            val principal = Principal.current() //(1)!
            return if (principal is UserPrincipal) {
                "Hello, user: ${principal.userId}"
            } else {
                throw SecurityException("Not authenticated")
            }
        }
    }
    ```

    1. Returns `null` when no principal is bound for the current request

### OAuth2 { #oauth2 }

For OAuth2 authorization, create an `HttpServerPrincipalExtractor` that validates the token via an OAuth2 provider.
For an `OAuth` security scheme the generated code expects a `PrincipalWithScopes`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface OAuth2Module {

        @Tag(ApiSecurity.OAuth.class)
        default HttpServerPrincipalExtractor<String, PrincipalWithScopes> oauth2Extractor(OAuth2Client oauth2Client) {
            return (request, value) -> {
                if (value == null || !value.startsWith("Bearer ")) {
                    return null;
                }

                var token = value.substring("Bearer ".length());
                var introspection = oauth2Client.introspect(token);
                return introspection == null
                    ? null
                    : new ScopedUser(introspection.subject(), introspection.scopes());
            };
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface OAuth2Module {

        @Tag(ApiSecurity.OAuth::class)
        fun oauth2Extractor(oauth2Client: OAuth2Client): HttpServerPrincipalExtractor<String, PrincipalWithScopes> {
            return HttpServerPrincipalExtractor { request, value ->
                if (value == null || !value.startsWith("Bearer ")) {
                    null
                } else {
                    val token = value.substring("Bearer ".length)
                    oauth2Client.introspect(token)
                        ?.let { ScopedUser(it.subject, it.scopes) }
                }
            }
        }
    }
    ```

#### Scope Checking { #scope-check }

When scopes are declared in the OpenAPI contract, the generated interceptor checks them itself:
if the principal is authenticated but `PrincipalWithScopes.scopes()` does not contain a required scope, the request is answered with `403`. Missing suitable credentials result in `401`.

Outside of OpenAPI, an interceptor checks the scopes and binds the principal itself with `Principal.with(...)`,
so that the rest of the chain can read it through `Principal.current()`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class ScopeCheckingInterceptor implements HttpServerInterceptor {

        private final AuthConfig config;
        private final TokenValidator validator;

        public ScopeCheckingInterceptor(AuthConfig config, TokenValidator validator) {
            this.config = config;
            this.validator = validator;
        }

        @Override
        public HttpServerResponse intercept(HttpServerRequest request, InterceptChain chain) throws Exception {
            var principal = validator.validate(request.headers().getFirst("authorization"));
            if (principal == null) {
                throw HttpServerResponseException.of(401, "Unauthorized");
            }
            if (!(principal instanceof PrincipalWithScopes scoped)) {
                throw HttpServerResponseException.of(403, "No scopes available");
            }
            if (!scoped.scopes().contains(config.requiredScope())) {
                throw HttpServerResponseException.of(403, "Insufficient scope");
            }

            return Principal.with(scoped, () -> chain.process(request)); //(1)!
        }
    }
    ```

    1. Binds the principal for the current request, so `Principal.current()` returns it downstream

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ScopeCheckingInterceptor(
        private val config: AuthConfig,
        private val validator: TokenValidator
    ) : HttpServerInterceptor {

        override fun intercept(request: HttpServerRequest, chain: HttpServerInterceptor.InterceptChain): HttpServerResponse {
            val principal = validator.validate(request.headers().getFirst("authorization"))
                ?: throw HttpServerResponseException.of(401, "Unauthorized")
            if (principal !is PrincipalWithScopes) {
                throw HttpServerResponseException.of(403, "No scopes available")
            }
            if (!principal.scopes.contains(config.requiredScope())) {
                throw HttpServerResponseException.of(403, "Insufficient scope")
            }

            return Principal.with(principal) { chain.process(request) } //(1)!
        }
    }
    ```

    1. Binds the principal for the current request, so `Principal.current()` returns it downstream

### OpenAPI Integration { #openapi }

When using the Kora [OpenAPI generator](openapi-codegen.md), authorization is configured automatically based on the OpenAPI specification.
The generator creates:

1. An `ApiSecurity` interface with a marker class for every security scheme, named after the scheme (`ApiKeyAuth`, `BearerAuth`, `BasicAuth`, `CookieAuth`, `OAuth`)
2. An `HttpServerInterceptor` for every security requirement, applied to the generated controller
3. A requirement to provide an `HttpServerPrincipalExtractor` with the corresponding `@Tag`

Example from [kora-examples](https://github.com/kora-projects/kora-examples):

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends
            HoconConfigModule,
            UndertowPublicHttpServerModule,
            JsonModule {

        @Tag(ApiSecurity.ApiKeyAuth.class)
        default HttpServerPrincipalExtractor<String, Principal> apiKeyExtractor(DataApiAuthConfig config) {
            return (request, value) -> {
                if (value == null || !config.value().equals(value)) {
                    return null;
                }
                return new DataApiPrincipal("data-api-client");
            };
        }
    }
    ```

    where `DataApiPrincipal`:

    ```java
    public record DataApiPrincipal(String name) implements Principal {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application :
        HoconConfigModule,
        UndertowPublicHttpServerModule,
        JsonModule {

        @Tag(ApiSecurity.ApiKeyAuth::class)
        fun apiKeyExtractor(config: DataApiAuthConfig): HttpServerPrincipalExtractor<String, Principal> {
            return HttpServerPrincipalExtractor { request, value ->
                if (value == null || config.value() != value) {
                    null
                } else {
                    DataApiPrincipal("data-api-client")
                }
            }
        }
    }
    ```

    where `DataApiPrincipal`:

    ```kotlin
    data class DataApiPrincipal(val name: String) : Principal
    ```

Configuration:

```hocon
auth.apiKey {
  value = "secret-api-key-123"
}
```

When one operation requires several schemes at once, the extractor tag joins the scheme names with `With`
(`BearerAuthWithApiKeyAuth`), and the generator adds an `ApiSecurity.<Tag>AuthData` record holding every credential,
so the extractor is declared as `HttpServerPrincipalExtractor<ApiSecurity.BearerAuthWithApiKeyAuthAuthData, Principal>`.
The interceptor generated for that requirement is tagged separately, joining the same scheme names with `And`
(`ApiSecurity.BearerAuthAndApiKeyAuth`); alternative requirements of one operation are joined with `_`.

### Authorization without OpenAPI { #authorization-manual }

Without a generated `ApiSecurity`, nothing calls `HttpServerPrincipalExtractor`, so authorization is implemented
as a regular [interceptor](#interceptors) placed on the controller, on the route, or globally:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class ApiKeyAuthInterceptor implements HttpServerInterceptor {

        private final ApiKeyAuthConfig config;

        public ApiKeyAuthInterceptor(ApiKeyAuthConfig config) {
            this.config = config;
        }

        @Override
        public HttpServerResponse intercept(HttpServerRequest request, InterceptChain chain) throws Exception {
            var authorization = request.headers().getFirst("authorization");
            if (!this.config.value().equals(authorization)) {
                throw HttpServerResponseException.of(401, "Unauthorized"); //(1)!
            }
            return chain.process(request);
        }
    }
    ```

    1. Missing or invalid credentials are answered with `401`; this exception already carries the HTTP status

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ApiKeyAuthInterceptor(private val config: ApiKeyAuthConfig) : HttpServerInterceptor {

        override fun intercept(request: HttpServerRequest, chain: HttpServerInterceptor.InterceptChain): HttpServerResponse {
            val authorization = request.headers().getFirst("authorization")
            if (config.value() != authorization) {
                throw HttpServerResponseException.of(401, "Unauthorized") //(1)!
            }
            return chain.process(request)
        }
    }
    ```

    1. Missing or invalid credentials are answered with `401`; this exception already carries the HTTP status

The interceptor is then attached with `@InterceptWith(ApiKeyAuthInterceptor.class)` on the controller or on a single route.

### Error Handling { #auth-error-handling }

When an extractor returns `null`, or the required scopes are missing, the generated interceptor answers
with status `401` and the body `Unauthorized`.
To shape authorization errors yourself, add a global interceptor:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(HttpServer.class)
    @Component
    public final class AuthErrorInterceptor implements HttpServerInterceptor {

        @Override
        public HttpServerResponse intercept(HttpServerRequest request, InterceptChain chain) throws Exception {
            try {
                return chain.process(request);
            } catch (IllegalAccessException e) {
                return HttpServerResponse.of(401, HttpBody.plaintext("Unauthorized: " + e.getMessage()));
            } catch (SecurityException e) {
                return HttpServerResponse.of(403, HttpBody.plaintext("Forbidden: " + e.getMessage()));
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(HttpServer::class)
    @Component
    class AuthErrorInterceptor : HttpServerInterceptor {

        override fun intercept(request: HttpServerRequest, chain: HttpServerInterceptor.InterceptChain): HttpServerResponse {
            try {
                return chain.process(request)
            } catch (e: IllegalAccessException) {
                return HttpServerResponse.of(401, HttpBody.plaintext("Unauthorized: ${e.message}"))
            } catch (e: SecurityException) {
                return HttpServerResponse.of(403, HttpBody.plaintext("Forbidden: ${e.message}"))
            }
        }
    }
    ```

Because a global interceptor wraps the generated security interceptor, it also sees the `HttpServerResponseException`
with code `401` raised by the generated code and can replace it with a response of its own.

## Telemetry { #telemetry }

HTTP Server uses a telemetry contract for logging, metrics, and tracing of requests.
Telemetry configuration (section `telemetry { logging / metrics / tracing }`) is described in the [Configuration](#configuration) section.
Extension points are located in `io.koraframework.http.server.common.telemetry`.

For each HTTP request, an `HttpServerObservation` is created and closed upon request completion.
It observes the request, the response, the `HttpResultCode` and any exception.

The default factory `DefaultHttpServerTelemetryFactory` combines three parts:

- `DefaultHttpServerLoggerFactory` builds the logger for the request start/end;
- `DefaultHttpServerMetricsFactory` builds the request metrics;
- an `io.opentelemetry.api.trace.Tracer`, when present in the graph, produces the request span.

Request and response logs are written by two separate loggers, so their level can be tuned independently:

===! ":material-code-json: `Hocon`"

    ```javascript
    logging.levels {
        "io.koraframework.http.server.common.HttpServer.request" = "DEBUG" //(1)!
        "io.koraframework.http.server.common.HttpServer.response" = "TRACE" //(2)!
    }
    ```

    1. `INFO` logs the operation only, `DEBUG` adds headers and query parameters
    2. `TRACE` additionally writes the body, limited by `maxRequestBodyLogSize` / `maxResponseBodyLogSize`

=== ":simple-yaml: `YAML`"

    ```yaml
    logging:
      levels:
        "io.koraframework.http.server.common.HttpServer.request": "DEBUG" #(1)!
        "io.koraframework.http.server.common.HttpServer.response": "TRACE" #(2)!
    ```

    1. `INFO` logs the operation only, `DEBUG` adds headers and query parameters
    2. `TRACE` additionally writes the body, limited by `maxRequestBodyLogSize` / `maxResponseBodyLogSize`

The logged operation uses the route template by default and the full path when `pathFull = true`, or at the `TRACE` logger level when `pathFull` is not set.
Values of sensitive headers, query parameters and body fields are masked, see [Masking](#telemetry-masking).

Metrics require `httpServer.telemetry.metrics.enabled` **and** a `MeterRegistry` supplied by a [metrics](metrics.md) module.
The server reports the `http.server.request.duration` timer, with the buckets from `httpServer.telemetry.metrics.slo` and the tags
`server.name`, `server.port`, `http.request.method`, `http.response.status_code`, `http.route`, `url.scheme` and `error.type`,
and the `http.server.active_requests` gauge with the same tags except `http.response.status_code` and `error.type`;
both carry everything declared in `httpServer.telemetry.metrics.tags`.
The `Host` header value (`server.address`) is not a metric tag: the client sets it and its values are unbounded. It stays a span attribute, and it can be added to metrics through a [metric factory](metrics.md#http-server).
Metrics and tracing are described in the [Metrics Reference](metrics.md#http-server) section.

### Logging { #telemetry-logging }

Server logging is written through `SLF4J` to the `io.koraframework.http.server.common.HttpServer.request` and
`io.koraframework.http.server.common.HttpServer.response` loggers. Enabling logging in the configuration (`httpServer.telemetry.logging.enabled = true`)
turns the logger on, but **what** is actually written is governed by the level of these loggers, so you control verbosity from your logging framework
(`logback`, etc.) without restarting with a different config:

| Log level | What is logged |
|-----------|----------------|
| `INFO`    | Server name and port, authority and operation (method and route template); the response record adds the result code, the status code and the processing time in milliseconds |
| `DEBUG`   | Additionally request query parameters and headers, and response headers |
| `TRACE`   | Additionally request and response bodies, and the full request path instead of the route template |

A request that failed with an exception is logged by the response logger at `WARN`.

The following configuration fields shape the output (see [Configuration](#configuration) for the full list):

* `pathFull` — `true` always logs the full request path (`/users/42`), `false` always logs the route template (`/users/{id}`); when not set, the template is used except at `TRACE`
* `maskHeaders` / `maskQueries` — header and query parameter names whose values are masked, see [Masking](#telemetry-masking)
* `maxRequestBodyLogSize` / `maxResponseBodyLogSize` — a larger body is logged without its content
* `stacktrace` — when `true` (default), logs the exception stack trace when a request fails

Example `logback` configuration that enables header logging for the server:

```xml
<logger name="io.koraframework.http.server.common.HttpServer" level="DEBUG"/>
```

### Masking { #telemetry-masking }

Values of the headers listed in `maskHeaders` (default: `authorization`, `cookie`, `set-cookie`) and of the query parameters
listed in `maskQueries` are replaced with the result of the `MaskingStrategy` tagged `@Tag(HttpServerTelemetry.class)`,
which by default writes `***`. Names are compared case-insensitively, and every value of a repeated header or parameter is masked separately.
To change how the values are masked, register your own strategy with the same tag — it replaces the default one.
Any `MaskingStrategy` fits, including the built-in [strategies](logging-aspect.md#masking-strategies) of the logging module:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends UndertowPublicHttpServerModule {

        @Tag(HttpServerTelemetry.class)
        default MaskingStrategy httpServerMaskingStrategy() {
            return new MaskingKeepLast("***", 4);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : UndertowPublicHttpServerModule {

        @Tag(HttpServerTelemetry::class)
        fun httpServerMaskingStrategy(): MaskingStrategy = MaskingKeepLast("***", 4)
    }
    ```

Request and response bodies logged at `TRACE` are masked by a `DataMasker` component tagged `@Tag(HttpServerTelemetry.class)`
that matches the body format, chosen by `Content-Type`: `json` for `*/json` and `*+json`, `xml` for `*/xml` and `*+xml`,
`form-urlencoded` for `application/x-www-form-urlencoded`. The built-in `JsonDataMasker`, `XmlDataMasker` and `FormUrlencodedDataMasker`
(package `io.koraframework.logging.common.masking.raw`) take the fields to mask as `MaskingPathRules`.
There are no body maskers by default, so a body is logged as is until you register one:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends UndertowPublicHttpServerModule {

        @Tag(HttpServerTelemetry.class)
        default DataMasker httpServerJsonMasker() {
            return new JsonDataMasker(MaskingPathRules.builder() //(1)!
                .mask("password", new MaskingFull()) //(2)!
                .mask("card.number", new MaskingKeepLast("***", 4)) //(3)!
                .build());
        }
    }
    ```

    1.  Masks `JSON` bodies; `XmlDataMasker` and `FormUrlencodedDataMasker` are built the same way
    2.  A field name masks the field wherever it appears
    3.  A dotted path masks the field reached from the root of the payload

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : UndertowPublicHttpServerModule {

        @Tag(HttpServerTelemetry::class)
        fun httpServerJsonMasker(): DataMasker =
            JsonDataMasker(MaskingPathRules.builder() //(1)!
                .mask("password", MaskingFull()) //(2)!
                .mask("card.number", MaskingKeepLast("***", 4)) //(3)!
                .build())
    }
    ```

    1.  Masks `JSON` bodies; `XmlDataMasker` and `FormUrlencodedDataMasker` are built the same way
    2.  A field name masks the field wherever it appears
    3.  A dotted path masks the field reached from the root of the payload

A masker walks the raw bytes without building a document, never fails on a damaged payload and masks everything after the point where it loses
track of the structure. Its output is limited to `64KiB` by default; the rest is replaced with `<masked:truncated>` (`<!--masked:truncated-->` for `XML`).

### Custom logger { #telemetry-custom-logger }

The telemetry is assembled from graph components, so each part is replaced by registering your own component of the same type:
`DefaultHttpServerLoggerFactory` for logs, `DefaultHttpServerMetricsFactory` for metrics, `DefaultHttpServerBodyConverter` for the way
bodies are turned into log text, or the whole `HttpServerTelemetryFactory`. A custom logger can reuse
`io.koraframework.http.common.telemetry.MaskingUtils.toMaskedString(...)` to mask headers and query parameters with a `MaskingStrategy`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MyHttpServerLoggerFactory extends DefaultHttpServerLoggerFactory {

        public MyHttpServerLoggerFactory(@Tag(HttpServerTelemetry.class) MaskingStrategy maskingStrategy) {
            super(maskingStrategy);
        }

        @Override
        public DefaultHttpServerLogger create(DefaultHttpServerTelemetry.TelemetryContext context) {
            return super.create(context); //(1)!
        }
    }
    ```

    1. Return your own `DefaultHttpServerLogger` subclass here to change the format or destination of the records

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyHttpServerLoggerFactory(
        @Tag(HttpServerTelemetry::class) maskingStrategy: MaskingStrategy
    ) : DefaultHttpServerLoggerFactory(maskingStrategy) {

        override fun create(context: DefaultHttpServerTelemetry.TelemetryContext): DefaultHttpServerLoggerFactory.DefaultHttpServerLogger {
            return super.create(context) //(1)!
        }
    }
    ```

    1. Return your own `DefaultHttpServerLogger` subclass here to change the format or destination of the records
