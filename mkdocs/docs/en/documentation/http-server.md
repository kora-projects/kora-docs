Module provides a thin layer of abstraction over HTTP server libraries to create HTTP request handlers
using both declarative-style annotations and imperative-style annotations.

## Dependency

Implementation based on [Undertow](https://undertow.io/).

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

## Configuration

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
        telemetry {
            logging {
                enabled = false //(14)!
                stacktrace = true //(15)!
                mask = "***" //(16)!
                maskQueries = [ ] //(17)!
                maskHeaders = [ "authorization" ] //(18)!
                pathTemplate = true //(19)!
            }
            metrics {
                enabled = true //(20)!
                slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(21)!
            }
            tracing {
                enabled = true //(22)!
            }
        }
    }
    ```

    1.  Public server port
    2.  Private server port
    3.  Path to get [metrics](metrics.md) on the private server
    4.  Path to get [probes](probes.md) status on the private server
    5.  Path to get [probes viability](probes.md) status on a private server
    6.  Whether to ignore the slash at the end of the path, if enabled `/my/path` and `/my/path/` will be interpreted the same way, default is off
    7.  Number of server threads, default is the number of CPU cores or minimum `2`.
    8.  Number of blocking threads, default is the number of CPU cores multiplied by 2 or a minimum of `2` threads.
    9.  Waiting time to shut down the server in case of [normal termination](https://maxilect.ru/blog/pochemu-vazhen-graceful-shutdown-v-oblachnoy-srede-na-pr/)
    10.  Maximum lifetime of the request handler thread
    11.  Maximum waiting time for reading data from the socket/connection
    12.  Maximum waiting time for writing data to the socket/connection
    13.  Whether to send `keep-alive' messages during TCP socket/connection lifetime
    14.  Enables module logging (default `false`)
    15.  Enables call stack logging in case of exception
    16.  Mask that is used to hide specified headers and request/response parameters
    17.  List of request parameters to be hidden
    18.  List of request/response headers that should be hidden
    19.  Whether to always use the request path template when logging. The default is to always use the path template, except for the `TRACE` logging level, which uses the full path.
    20.  Enables module metrics (default `true`)
    21.  Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    22.  Enables module tracing (default is `true`)

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
      telemetry:
        logging:
          enabled: false #(14)!
          stacktrace: true #(15)!
          mask: "***" #(16)!
          maskQueries: [ ] #(17)!
          maskHeaders: [ "authorization" ] #(18)!
          pathTemplate: true #(19)!
        metrics:
          enabled: true #(20)!
          slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(21)!
        telemetry:
          enabled: true #(22)!
    ```

    1.  Public server port
    2.  Private server port
    3.  Path to get [metrics](metrics.md) on the private server
    4.  Path to get [probes](probes.md) status on the private server
    5.  Path to get [probes viability](probes.md) status on a private server
    6.  Whether to ignore the slash at the end of the path, if enabled `/my/path` and `/my/path/` will be interpreted the same way, default is off
    7.  Number of server threads, default is the number of CPU cores or minimum `2`.
    8.  Number of blocking threads, default is the number of CPU cores multiplied by 2 or a minimum of `2` threads.
    9.  Waiting time to shut down the server in case of [normal termination](https://maxilect.ru/blog/pochemu-vazhen-graceful-shutdown-v-oblachnoy-srede-na-pr/)
    10.  Maximum lifetime of the request handler thread
    11.  Maximum waiting time for reading data from the socket/connection
    12.  Maximum waiting time for writing data to the socket/connection
    13.  Whether to send `keep-alive' messages during TCP socket/connection lifetime
    14.  Enables module logging (default `false`)
    15.  Enables call stack logging in case of exception
    16.  Mask that is used to hide specified headers and request/response parameters
    17.  List of request parameters to be hidden
    18.  List of request/response headers that should be hidden
    19.  Whether to always use the request path template when logging. The default is to always use the path template, except for the `TRACE` logging level, which uses the full path.
    20.  Enables module metrics (default `true`)
    21.  Configures [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    22.  Enables module tracing (default is `true`)

## SomeController declarative

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
    4. Indicates the type of HTTP method handler
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
    4. Indicates the type of HTTP method handler
    5. Indicates the path of the handler method

### Request

The section describes HTTP request transformations at the controller.
It is suggested to use special annotations to specify the request parameters.

#### Path parameter

`@Path` - denotes the value of the request path part, the parameter itself is specified in `{path}` in the path
and the name of the parameter is specified in `value` or defaults to the name of the method argument.

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

#### Query parameter

`@Query` - value of the query parameter, the name of the parameter is specified in `value` or is equal to the name of the method argument by default.

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

#### Request header

`@Header` - value of [request header](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers), the parameter name is specified in `value` or defaults to the method argument name.

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

#### Request body

Specifying the body of a request requires using a method argument without special annotations,
default supported types are `byte[]`, `ByteBuffer`, `String`.

##### Json

In order to indicate that the body is Json and needs to automatically create such a reader and embed it,
is required to use the `@Json` annotation:

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

    1. Specifies that the body should be written as Json

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

    1. Specifies that the body should be written as Json

Need to connect [Json](json.md) module.

##### Form UrlEncoded

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

##### Form Multipart

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

#### Cookie

`@Cookie` - [Cookie](https://developer.mozilla.org/en-US/docs/Glossary/Cookie) value, the parameter name is specified in `value` or defaults to the method argument name.

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

#### Custom parameter

In case you need to handle the request in a different way, you can use a special `HttpServerRequestMapper` interface:

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
        @Mapping(UserContextRequestMapper::class)
        operator fun get(@Mapping(RequestMapper::class) context: UserContext): String {
            return "Hello World"
        }
    }
    ```

#### Required parameters

===! ":fontawesome-brands-java: `Java`"

    By default, all arguments declared in a method are **required** (*NotNull*).

=== ":simple-kotlin: `Kotlin`"

    By default, all arguments declared in a method that do not use the [Kotlin Nullability](https://kotlinlang.org/docs/null-safety.html) syntax are **required** (*NotNull*).

#### Optional parameters

===! ":fontawesome-brands-java: `Java`"

    In case a method argument is optional, that is, it may not exist then,
    `@Nullable` annotation can be used:

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

    1.  Any `@Nullable` annotation will do, such as `javax.annotation.Nullable` / `jakarta.annotation.Nullable` / `org.jetbrains.annotations.Nullable` / etc.

=== ":simple-kotlin: `Kotlin`"

    It is expected to use the [Kotlin Nullability](https://kotlinlang.org/docs/null-safety.html) syntax and mark such a parameter as Nullable:

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

### Response

By default, you can use standard return value types,
such as `byte[]`, `ByteBuffer`, `String` which will be processed with status code `200` and corresponding response type header
or `HttpServerResponse` where you will have to fill in all information about HTTP response yourself.

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
                    HttpBody.plaintext(body) //(3)!
            ); 
        }
    }
    ```

    1. HTTP status response code
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
                HttpBody.plaintext(body) //(3)!
            )
        }
    }
    ```

    1. HTTP status response code
    2. Response headers
    3. Response body

#### Json

If you intend to respond in Json format, you are required to use the `@Json` annotation over the method:

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

    1. Specifies that the response should be in Json format

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

    1. Specifies that the response should be in Json format

[Json](json.md) module is required.

#### Response entity

If the intention is to read the body and also get the headers and status code of the response,
then the `HttpResponseEntity` is supposed to be used, it is a wrapper over the response body.

Below is an example similar to the Json example along with the `HttpResponseEntity` wrapper:

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

#### Respond exception

If you need to respond with an error, you can use `HttpServerResponseException` to throw an exception.

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

#### Custom response

In case you need to read the response in a different way, you can use the special `HttpServerResponseMapper` interface:

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

### Signatures

Available signatures for repository methods out of the box:

===! ":fontawesome-brands-java: `Java`"

    The `T` refers to the type of the return value.

    - `T myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletionStage.html)
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (require [dependency](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

=== ":simple-kotlin: `Kotlin`"

    By `T` we mean the type of the return value.

    - `myMethod(): T`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (require [dependency](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) as `implementation`)

## Interceptors

You can create interceptors to change behavior or create additional behavior using the `HttpServerInterceptor` class.

Interceptors can be used on:

- Specific controller methods
- Entire controller
- All controllers at once (requires using `@Tag(HttpServerModule.class)` over the interceptor class) (there can be only one such interceptor).

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

### Error handling

Error handling at the level of all HTTP responses can also be realized by means of an interceptor,
below is a simple example of such an interceptor.

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

## SomeController imperative

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

    1. Specifies the HTTP method type of the handler method
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

    1. Specifies the HTTP method type of the handler method
    2. Indicates the path of the handler method
