---
description: "Explains Kora HTTP server, declarative and imperative controllers, routing, request and response mapping, interceptors, error handling, and Undertow configuration. Use when working with @HttpController, @HttpRoute, @Path, @Query, @Header, @Cookie, @Json, @InterceptWith."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora HTTP server, declarative and imperative controllers, routing, request and response mapping, interceptors, error handling, and Undertow configuration; key triggers include @HttpController, @HttpRoute, @Path, @Query, @Header, @Cookie, @Json, @InterceptWith, HttpServerModule, UndertowHttpServerModule."
---

The `HTTP server` module describes the incoming HTTP boundary of an application: accepting a request, parsing parameters,
reading the body, selecting a handler, creating a response, telemetry, and interceptors. In Kora, controllers can be described
declaratively with `@HttpController` and `@HttpRoute`, or handlers can be registered imperatively with `HttpServerRequestHandler`.

The declarative approach fits most APIs: the method signature describes the HTTP contract, and Kora creates the handler at
compile time without using `Reflection` at runtime. The imperative approach is useful for low-level or dynamic routes where
it is easier to process the request manually.

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
    implementation "ru.tinkoff.kora:http-server-undertow"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends UndertowHttpServerModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:http-server-undertow")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : UndertowHttpServerModule
    ```

## Configuration { #configuration }

Example of the complete configuration described in the `HttpServerConfig` class (default or example values are specified):

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
        publicApiHttpPort = 8080 //(1)!
        privateApiHttpPort = 8085 //(2)!
        privateApiHttpMetricsPath = "/metrics" //(3)!
        privateApiHttpReadinessPath = "/system/readiness" //(4)!
        privateApiHttpLivenessPath = "/system/liveness" //(5)!
        ignoreTrailingSlash = false //(6)!
        ioThreads = 2 //(7)!
        blockingThreads = 2 //(8)!
        shutdownWait = "30s" //(9)!
        threadKeepAliveTimeout = "60s" //(10)!
        socketReadTimeout = "0s" //(11)!
        socketWriteTimeout = "0s" //(12)!
        socketKeepAliveEnabled = false //(13)!
        virtualThreadsEnabled = false //(14)!
        maxRequestBodySize = "256MiB" //(15)!
        telemetry {
            logging {
                enabled = false //(16)!
                stacktrace = true //(17)!
                mask = "***" //(18)!
                maskQueries = [ ] //(19)!
                maskHeaders = [ "authorization", "cookie", "set-cookie" ] //(20)!
                pathTemplate = true //(21)!
            }
            metrics {
                enabled = true //(22)!
                slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(23)!
                tags = { // (24)!
                    "key1" = "value1"
                    "key2" = "value2"
                }
            }
            tracing {
                enabled = true //(25)!
                attributes = { // (26)!
                    "key1" = "value1"
                    "key2" = "value2"
                }
            }
        }
    }
    ```

    1.  Public `HTTP` server port (default: `8080`)
    2.  Private `HTTP` server port (default: `8085`)
    3.  Path to get [metrics](metrics.md) on the private server (default: `/metrics`)
    4.  Path to get [readiness probe](probes.md) status on the private server (default: `/system/readiness`)
    5.  Path to get [liveness probe](probes.md) status on the private server (default: `/system/liveness`)
    6.  Whether to ignore a trailing `/` in the path: when enabled, `/my/path` and `/my/path/` are treated as the same route (default: `false`)
    7.  Number of network I/O threads (default: number of available processors, but not less than `2`)
    8.  Number of threads for blocking request processing (default: `min(max(available processors, 2) * 8, 200)`)
    9.  Time to wait for processing before server shutdown during [graceful shutdown](container.md#component-lifecycle) (default: `30s`)
    10.  Maximum idle lifetime of a request handler thread (default: `60s`)
    11.  Maximum time to wait for reading data from a socket or connection; `0s` disables the timeout (default: `0s`)
    12.  Maximum time to wait for writing data to a socket or connection; `0s` disables the timeout (default: `0s`)
    13.  Whether to enable `TCP keep-alive` for a socket or connection (default: `false`)
    14.  Enables virtual threads for blocking request processing instead of the `blockingThreads` pool, requires `Java 21+` (default: `false`)
    15.  Maximum allowed size of an incoming request body (default: `256MiB`)
    16.  Enables module logging (default: `false`)
    17.  Enables call stack logging on exception (default: `true`)
    18.  Mask used to hide specified headers and request or response parameters (default: `***`)
    19.  List of request parameters to hide (default: `[]`)
    20.  List of request or response headers to hide (default: `[ "authorization", "cookie", "set-cookie" ]`)
    21.  Whether to use the request path template in logs; when not specified, the template is always used except at `TRACE`, where the full path is used (default not specified, optional)
    22.  Enables module metrics (default: `true`)
    23.  Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    24.  Configures metric tags (default: `{}`)
    25.  Enables module tracing (default: `true`)
    26.  Configures tracing attributes (default: `{}`)

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      publicApiHttpPort: 8080 #(1)!
      privateApiHttpPort: 8085 #(2)!
      privateApiHttpMetricsPath: "/metrics" #(3)!
      privateApiHttpReadinessPath: "/system/readiness" #(4)!
      privateApiHttpLivenessPath: "/system/liveness" #(5)!
      ignoreTrailingSlash: false #(6)!
      ioThreads: 2 #(7)!
      blockingThreads: 2 #(8)!
      shutdownWait: "30s" #(9)!
      threadKeepAliveTimeout: "60s" #(10)!
      socketReadTimeout: "0s" #(11)!
      socketWriteTimeout: "0s" #(12)!
      socketKeepAliveEnabled: false #(13)!
      virtualThreadsEnabled: false #(14)!
      maxRequestBodySize: "256MiB" #(15)!
      telemetry:
        logging:
          enabled: false #(16)!
          stacktrace: true #(17)!
          mask: "***" #(18)!
          maskQueries: [ ] #(19)!
          maskHeaders: [ "authorization", "cookie", "set-cookie" ] #(20)!
          pathTemplate: true #(21)!
        metrics:
          enabled: true #(22)!
          slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(23)!
          tags: #(24)!
            key1: value1
            key2: value2
        tracing:
          enabled: true #(25)!
          attributes: #(26)!
            key1: value1
            key2: value2
    ```

    1.  Public `HTTP` server port (default: `8080`)
    2.  Private `HTTP` server port (default: `8085`)
    3.  Path to get [metrics](metrics.md) on the private server (default: `/metrics`)
    4.  Path to get [readiness probe](probes.md) status on the private server (default: `/system/readiness`)
    5.  Path to get [liveness probe](probes.md) status on the private server (default: `/system/liveness`)
    6.  Whether to ignore a trailing `/` in the path: when enabled, `/my/path` and `/my/path/` are treated as the same route (default: `false`)
    7.  Number of network I/O threads (default: number of available processors, but not less than `2`)
    8.  Number of threads for blocking request processing (default: `min(max(available processors, 2) * 8, 200)`)
    9.  Time to wait for processing before server shutdown during [graceful shutdown](container.md#component-lifecycle) (default: `30s`)
    10.  Maximum idle lifetime of a request handler thread (default: `60s`)
    11.  Maximum time to wait for reading data from a socket or connection; `0s` disables the timeout (default: `0s`)
    12.  Maximum time to wait for writing data to a socket or connection; `0s` disables the timeout (default: `0s`)
    13.  Whether to enable `TCP keep-alive` for a socket or connection (default: `false`)
    14.  Enables virtual threads for blocking request processing instead of the `blockingThreads` pool, requires `Java 21+` (default: `false`)
    15.  Maximum allowed size of an incoming request body (default: `256MiB`)
    16.  Enables module logging (default: `false`)
    17.  Enables call stack logging on exception (default: `true`)
    18.  Mask used to hide specified headers and request or response parameters (default: `***`)
    19.  List of request parameters to hide (default: `[]`)
    20.  List of request or response headers to hide (default: `[ "authorization", "cookie", "set-cookie" ]`)
    21.  Whether to use the request path template in logs; when not specified, the template is always used except at `TRACE`, where the full path is used (default not specified, optional)
    22.  Enables module metrics (default: `true`)
    23.  Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for metrics (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    24.  Configures metric tags (default: `{}`)
    25.  Enables module tracing (default: `true`)
    26.  Configures tracing attributes (default: `{}`)

Module metrics are described in the [Metrics Reference](metrics.md#http-server) section.

Kora provides fine-grained control over the `Undertow` `HTTP` server through two dedicated configuration interfaces: `UndertowConfigurer` and `HttpHandlerConfigurer`.
They allow configuring server behavior and the request processing pipeline without sacrificing integration with Kora's modular architecture.

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

### Request { #request }

This section describes how an `HTTP` request is converted into controller method arguments.
Special annotations are used for request parts, and the request body is passed as an argument without such an annotation.

#### String parameter conversion { #string-parameter-reader }

Values from paths, query parameters, headers, and `cookie` arrive as strings.
Kora uses `StringParameterReader<T>` to convert a string into the target type:

```java
public interface StringParameterReader<T> {
    T read(String string);
}
```

`StringParameterReader<T>` is looked up as a graph component by the exact parameter type. If the parameter is declared as `List<T>` or `Set<T>`,
the converter is applied to every value separately.

Out of the box, Kora supports `String`, `Boolean`, `Integer`, `Long`, `Float`, `Double`, `UUID`, `BigInteger`, `BigDecimal`,
`Duration`, `LocalDate`, `LocalTime`, `LocalDateTime`, `OffsetTime`, `OffsetDateTime`, `ZonedDateTime`, and `enum`.
For `enum`, the default mapping uses the value name via `Enum.name()`. If a value cannot be converted, the request is completed
with a `400` response through `HttpServerResponseException`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record UserId(long value) {}

    @Module
    public interface UserIdModule {

        default StringParameterReader<UserId> userIdStringParameterReader() {
            return StringParameterReader.of(
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

        fun userIdStringParameterReader(): StringParameterReader<UserId> {
            return StringParameterReader.of(
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
The value is converted through `StringParameterReader<T>`, so both built-in and custom types can be used.

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
        operator fun helloWorld(
            @Header("headerName") headerValue: String,
            @Header("headerNameList") headerValues: List<String>
        ): String {
            return "Hello World";
        }
    }
    ```

#### Request body { #request-body }

Specifying the request body requires using a method argument without special annotations.
By default, `byte[]`, `ByteBuffer`, `String`, `FormUrlEncoded`, `FormMultipart`, and custom types through `HttpServerRequestMapper<T>` are supported.

##### JSON { #json }

To indicate that the body is `JSON` and requires an automatically created and injected `JsonReader<T>`,
use the `@Json` annotation:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

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
        fun helloWorld(body: FormUrlEncoded): String {
            return "Hello World"
        }
    }
    ```

##### Form Multipart { #form-multipart }

You can use `FormMultipart` as the body argument type and it will be treated as a [binary form](https://www.w3.org/TR/html401/interact/forms.html#h-17.13.4.2).

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        public String helloWorld(FormMultipart body) {
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
        fun helloWorld(body: FormMultipart): String {
            return "Hello World"
        }
    }
    ```

#### Cookie { #cookie }

`@Cookie` - [Cookie](https://developer.mozilla.org/en-US/docs/Glossary/Cookie) value, the parameter name is specified in `value` or defaults to the method argument name.
The value can be received as `String`, as a `Cookie` type with name, value, and attributes, or as another type through `StringParameterReader<T>`.

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
        operator fun helloWorld(
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

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class MapperRequestController {

        data class UserContext(val userId: String?, val traceId: String?)

        class RequestMapper : HttpServerRequestMapper<UserContext> {
            override fun apply(request: HttpServerRequest): UserContext {
                return UserContext(
                    request.headers().getFirst("x-user-id"),
                    request.headers().getFirst("x-trace-id")
                )
            }
        }

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        @Mapping(RequestMapper::class)
        operator fun get(@Mapping(RequestMapper::class) context: UserContext): String {
            return "Hello World"
        }
    }
    ```

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

    1.  Any `@Nullable` annotation will do, for example `javax.annotation.Nullable`, `jakarta.annotation.Nullable`, or `org.jetbrains.annotations.Nullable`.

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

By default, standard return value types can be used: `byte[]`, `ByteBuffer`, `String`.
They are processed with status `200` and the corresponding response content type header.

If the status, headers, or body must be specified manually, the method can return `HttpServerResponse`.
The main `HttpServerResponse` contract consists of a response code, headers, and an optional body:

```java
public interface HttpServerResponse {
    int code();
    MutableHttpHeaders headers();
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

#### JSON { #json-2 }

If the response should be returned as `JSON`, use the `@Json` annotation on the method.
Kora will find or create `JsonWriter<T>` for the response type:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

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

        data class Response(val greeting: String)

        @Json
        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun helloWorld(): HttpResponseEntity<Response> {
            return HttpResponseEntity.of(200, HttpHeaders.of("myHeader", "12345"), Response("Hello World"));
        }
    }
    ```

#### Respond exception { #respond-exception }

If processing should be interrupted and an error should be returned immediately, throw `HttpServerResponseException`.
It is both an exception and an `HttpServerResponse`, so it can be thrown from a controller, service, or parameter converter.

The `HttpServerResponseException.of(...)` factory methods allow specifying the status code, response text, cause, and headers.
The response body is written as `text/plain; charset=utf-8`.

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
It receives `Context`, the original `HttpServerRequest`, and the controller method result, and returns a ready `HttpServerResponse`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        public record HelloWorldResponse(String greeting, String name) {}

        public static final class ResponseMapper implements HttpServerResponseMapper<HelloWorldResponse> {

            @Override
            public HttpServerResponse apply(Context ctx, HttpServerRequest request, HelloWorldResponse result) {
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

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        data class HelloWorldResponse(val greeting: String, val name: String)

        class ResponseMapper : HttpServerResponseMapper<HelloWorldResponse> {
            fun apply(ctx: Context, request: HttpServerRequest, result: HelloWorldResponse): HttpServerResponse {
                return HttpServerResponse.of(200, HttpBody.plaintext(result.greeting + " - " + result.name))
            }
        }

        @Mapping(ResponseMapper::class)
        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun helloWorld(): HelloWorldResponse {
            return HelloWorldResponse("Hello World", "Bob")
        }
    }
    ```

### Signatures { #signatures }

Available signatures for declarative `HTTP` handler methods out of the box:

===! ":fontawesome-brands-java: `Java`"

    The `T` refers to the type of the return value.

    - `T myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletionStage.html)
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (require [dependency](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

=== ":simple-kotlin: `Kotlin`"

    By `T` we mean the type of the return value.

    - `myMethod(): T`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (require [dependency](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) as `implementation`)

## Interceptors { #interceptors }

Interceptors can be created to change behavior or add shared logic around request processing.
Use the `HttpServerInterceptor` interface:

```java
public interface HttpServerInterceptor {
    CompletionStage<HttpServerResponse> intercept(Context context, HttpServerRequest request, InterceptChain chain) throws Exception;

    interface InterceptChain {
        CompletionStage<HttpServerResponse> process(Context ctx, HttpServerRequest request) throws Exception;
    }
}
```

An interceptor receives the current `Context`, `HttpServerRequest`, and the chain of further processing.
To pass the request further, call `chain.process(context, request)`. If the interceptor returns a response itself,
the controller handler is not called.

Interceptors can be used on:

- Specific controller methods
- Entire controller
- All controllers at once: register the interceptor component with the `@Tag(HttpServerModule.class)` tag; there can be several global interceptors

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        public static final class MethodInterceptor implements HttpServerInterceptor {

            @Override
            public CompletionStage<HttpServerResponse> intercept(Context context, 
                                                                 HttpServerRequest request, 
                                                                 InterceptChain chain) throws Exception {
                return chain.process(context, request);
            }
        }

        @InterceptWith(MethodInterceptor.class)
        @HttpRoute(method = HttpMethod.POST, path = "/intercepted")
        public String helloWorld() {
            return "Hello World";
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        class MethodInterceptor : HttpServerInterceptor {

            override fun intercept(
                context: Context,
                request: HttpServerRequest,
                chain: HttpServerInterceptor.InterceptChain
            ): CompletionStage<HttpServerResponse> {
                return chain.process(context, request)
            }
        }

        @InterceptWith(MethodInterceptor::class)
        @HttpRoute(method = HttpMethod.POST, path = "/intercepted")
        fun helloWorld(): String {
            return "Hello World"
        }
    }
    ```

### Error handling { #error-handling }

Error handling for all `HTTP` responses can also be implemented through an interceptor.
Below is a simple example of such an interceptor.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(HttpServerModule.class)
    @Component
    public final class ErrorInterceptor implements HttpServerInterceptor {

        @Override
        public CompletionStage<HttpServerResponse> intercept(Context context, 
                                                             HttpServerRequest request, 
                                                             InterceptChain chain) throws Exception {
            return chain.process(context, request).exceptionally(e -> {
                if(e instanceof CompletionException) {
                    e = e.getCause();
                }
                if (e instanceof HttpServerResponseException ex) {
                    return ex;
                }

                var body = HttpBody.plaintext(e.getMessage());
                if (e instanceof IllegalArgumentException) {
                    return HttpServerResponse.of(400, body);
                } else if (e instanceof TimeoutException) {
                    return HttpServerResponse.of(408, body);
                } else {
                    return HttpServerResponse.of(500, body);
                }
            });
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(HttpServerModule.class)
    @Component
    class ErrorInterceptor : HttpServerInterceptor {

        override fun intercept(
            context: Context,
            request: HttpServerRequest,
            chain: HttpServerInterceptor.InterceptChain
        ): CompletionStage<HttpServerResponse> {
            return chain.process(context, request).exceptionally { e ->
                val error = if (e is CompletionException) e.cause!! else e
                if (error is HttpServerResponseException) {
                    return@exceptionally error
                }

                val body = HttpBody.plaintext(error.message)
                when (error) {
                    is IllegalArgumentException -> HttpServerResponse.of(400, body)
                    is TimeoutException -> HttpServerResponse.of(408, body)
                    else -> HttpServerResponse.of(500, body)
                }
            }
        }
    }
    ```

## SomeController imperative { #somecontroller-imperative }

In order to create a controller, implement the `HttpServerRequestHandler.HandlerFunction` interface,
and then register it in the `HttpServerRequestHandler` handler.

The following example shows how to handle all the described declarative request parameters from the examples above:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface SomeModule {

        default HttpServerRequestHandler someHttpHandler() {
            return HttpServerRequestHandlerImpl.of(HttpMethod.POST, //(1)!
                                                   "/hello/{world}", //(2)!
                                                   (context, request) -> {
                var path = RequestHandlerUtils.parseStringPathParameter(request, "world");
                var query = RequestHandlerUtils.parseOptionalStringQueryParameter(request, "query");
                var queries = RequestHandlerUtils.parseOptionalStringListQueryParameter(request, "Queries");
                var header = RequestHandlerUtils.parseOptionalStringHeaderParameter(request, "header");
                var headers = RequestHandlerUtils.parseOptionalStringListHeaderParameter(request, "Headers");
                return CompletableFuture.completedFuture(HttpServerResponse.of(200, HttpBody.plaintext("Hello World")));
            });
        }
    }
    ```

    1. Specifies the `HTTP` method type of the handler method
    2. Indicates the path of the handler method

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface SomeModule {

        fun someHttpHandler(): HttpServerRequestHandler? {
            return HttpServerRequestHandlerImpl.of(
                HttpMethod.POST, //(1)!
                "/hello/{world}" //(2)!
            ) { context: Context, request: HttpServerRequest ->
                val path = RequestHandlerUtils.parseStringPathParameter(request, "world")
                val query = RequestHandlerUtils.parseOptionalStringQueryParameter(request, "query")
                val queries = RequestHandlerUtils.parseOptionalStringListQueryParameter(request, "Queries")
                val header = RequestHandlerUtils.parseOptionalStringHeaderParameter(request, "header")
                val headers = RequestHandlerUtils.parseOptionalStringListHeaderParameter(request, "Headers")
                CompletableFuture.completedFuture(HttpServerResponse.of(200, HttpBody.plaintext("Hello World")))
            }
        }
    }
    ```

    1. Specifies the `HTTP` method type of the handler method
    2. Indicates the path of the handler method
