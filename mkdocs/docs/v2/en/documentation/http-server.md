---
description: "Explains Kora HTTP server, declarative and imperative controllers, routing, request and response mapping, interceptors, error handling, authorization and Undertow configuration. Use when working with @HttpController, @HttpRoute, @Path, @Query, @Header, @Cookie, @Json, @InterceptWith."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora HTTP server, declarative and imperative controllers, routing, request and response mapping, interceptors, error handling, authorization and Undertow configuration; key triggers include @HttpController, @HttpRoute, @Path, @Query, @Header, @Cookie, @Json, @InterceptWith, HttpServerInterceptor, HttpServerParameterReader, UndertowPublicHttpServerModule, @Tag(HttpServer.class), httpServer.port, httpServer.system."
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
            headerServerDateEnabled = true //(8)!
            maxRequestBodySize = "256MiB" //(9)!
            telemetry {
                logging {
                    enabled = false //(10)!
                    stacktrace = true //(11)!
                    mask = "***" //(12)!
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
        8.  Whether to always send the `Date` response header (default: `true`)
        9.  Maximum allowed size of an incoming request body (default: `256MiB`)
        10.  Enables module logging (default: `false`)
        11.  Enables call stack logging on exception (default: `true`)
        12.  Mask used to hide specified headers and request or response parameters (default: `***`)
        13.  List of request parameters to hide (default: `[]`)
        14.  List of request or response headers to hide (default: `[ "authorization", "cookie", "set-cookie" ]`)
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
          headerServerDateEnabled: true #(8)!
          maxRequestBodySize: "256MiB" #(9)!
          telemetry:
            logging:
              enabled: false #(10)!
              stacktrace: true #(11)!
              mask: "***" #(12)!
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
        8.  Whether to always send the `Date` response header (default: `true`)
        9.  Maximum allowed size of an incoming request body (default: `256MiB`)
        10.  Enables module logging (default: `false`)
        11.  Enables call stack logging on exception (default: `true`)
        12.  Mask used to hide specified headers and request or response parameters (default: `***`)
        13.  List of request parameters to hide (default: `[]`)
        14.  List of request or response headers to hide (default: `[ "authorization", "cookie", "set-cookie" ]`)
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

For everything that has no configuration option, Kora provides `Configurer<T>` extension points.
A `Configurer<T>` receives the object being built and returns the object to use:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends UndertowPublicHttpServerModule {

        default Configurer<Undertow.Builder> undertowConfigurer() { //(1)!
            return builder -> builder.setServerOption(UndertowOptions.ENABLE_HTTP2, true);
        }

        default Configurer<HttpHandler> handlerConfigurer() { //(2)!
            return handler -> new RequestDumpingHandler(handler);
        }

        default Configurer<XnioWorker.Builder> workerConfigurer() { //(3)!
            return builder -> builder.setWorkerName("my-worker");
        }
    }
    ```

    1.  Configures the `Undertow` builder of the public server before it is started
    2.  Wraps the root `HttpHandler` of the public server
    3.  Configures the `XnioWorker` shared by both servers

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : UndertowPublicHttpServerModule {

        fun undertowConfigurer(): Configurer<Undertow.Builder> = //(1)!
            Configurer { builder -> builder.setServerOption(UndertowOptions.ENABLE_HTTP2, true) }

        fun handlerConfigurer(): Configurer<HttpHandler> = //(2)!
            Configurer { handler -> RequestDumpingHandler(handler) }

        fun workerConfigurer(): Configurer<XnioWorker.Builder> = //(3)!
            Configurer { builder -> builder.setWorkerName("my-worker") }
    }
    ```

    1.  Configures the `Undertow` builder of the public server before it is started
    2.  Wraps the root `HttpHandler` of the public server
    3.  Configures the `XnioWorker` shared by both servers

An untagged `Configurer<Undertow.Builder>` or `Configurer<HttpHandler>` applies to the **public** server.
To configure the system server, mark the component with the `@SystemApi` tag.

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

To indicate that the body is `JSON` and requires an automatically created and injected `JsonReader<T>`,
use the `@Json` annotation:

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

You can use `FormUrlEncoded` as the body argument type and it will be processed as [form data](https://www.w3.org/TR/html401/interact/forms.html#h-17.13.4.1).

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        public String helloWorld(FormUrlEncoded body) {
            var part = body.get("name"); //(1)!
            return "Hello World";
        }
    }
    ```

    1. `FormUrlEncoded.get(String)` returns `FormPart(String name, List<String> values)` or `null`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun helloWorld(body: FormUrlEncoded): String {
            val part = body.get("name") //(1)!
            return "Hello World"
        }
    }
    ```

    1. `FormUrlEncoded.get(String)` returns `FormPart(String name, List<String> values)` or `null`

##### Form Multipart { #form-multipart }

You can use `FormMultipart` as the body argument type and it will be treated as a [binary form](https://www.w3.org/TR/html401/interact/forms.html#h-17.13.4.2).

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        public String helloWorld(FormMultipart body) {
            for (var part : body.parts()) { //(1)!
                System.out.println(part.name());
            }
            return "Hello World";
        }
    }
    ```

    1. `FormMultipart.parts()` returns a sealed `FormPart`: `MultipartData`, `MultipartFile` or `MultipartFileStream`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun helloWorld(body: FormMultipart): String {
            for (part in body.parts()) { //(1)!
                println(part.name())
            }
            return "Hello World"
        }
    }
    ```

    1. `FormMultipart.parts()` returns a sealed `FormPart`: `MultipartData`, `MultipartFile` or `MultipartFileStream`

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

    The `T` refers to the type of the return value.

    - `T myMethod()`
    - `void myMethod()` — answers `200` with an empty body

    Returning `CompletionStage<T>`, `Future<T>` or a reactive `Publisher<T>` is **not supported**:
    the processor prints a warning that the return type *"is unsupported and has no meaning"*,
    and the graph build then fails because there is no `HttpServerResponseMapper` for such a type.

=== ":simple-kotlin: `Kotlin`"

    By `T` we mean the type of the return value.

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
if the returned `PrincipalWithScopes.scopes()` does not contain a required scope, the request is answered with `401`.

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
                throw new SecurityException("Invalid API key"); //(1)!
            }
            return chain.process(request);
        }
    }
    ```

    1. The exception is turned into `403` by the global [authorization error handler](#auth-error-handling)

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ApiKeyAuthInterceptor(private val config: ApiKeyAuthConfig) : HttpServerInterceptor {

        override fun intercept(request: HttpServerRequest, chain: HttpServerInterceptor.InterceptChain): HttpServerResponse {
            val authorization = request.headers().getFirst("authorization")
            if (config.value() != authorization) {
                throw SecurityException("Invalid API key") //(1)!
            }
            return chain.process(request)
        }
    }
    ```

    1. The exception is turned into `403` by the global [authorization error handler](#auth-error-handling)

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

Headers listed in `maskHeaders` and query parameters listed in `maskQueries` are replaced with the `mask` value.
The logged operation uses the route template by default and the full path when `pathFull = true` or the logger level is `TRACE`.

Metrics and tracing are described in the [Metrics Reference](metrics.md#http-server) section.
