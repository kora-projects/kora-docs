---
search:
  exclude: true
title: HTTP Server Advanced Guide
summary: Extend the basic Kora HTTP server with request context mapping, additional body formats, controller interceptors, consistent error responses, and simple API-key authorization
tags: http-server, advanced, interceptors, request-mapping, auth, forms
---

# Advanced HTTP Server Guide { #advanced-http-server-guide }

This guide introduces advanced HTTP server capabilities in Kora. It covers how request context, form bodies, multipart uploads, controller interceptors, global error handling, and simple API-key
authorization fit around the same controller-service structure used by basic APIs. You will also see how these transport concerns stay explicit at the HTTP boundary without forcing storage or
application logic to know about low-level request handling.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java HTTP Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-http-server-advanced-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin HTTP Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-http-server-advanced-app).

## What You'll Build { #youll-build }

You will extend the server with:

- a typed `RequestContextMapper`
- a `DataController` for forms, multipart uploads, and helper routes for the advanced client guide
- a controller-level `LoggingInterceptor`
- a shared `ErrorResponse`
- a global `ExceptionHandler`
- a simple `Authorization: ApiKey ...` check for `DataController`

## What You'll Need { #youll-need }

- JDK 17 or later
- Gradle 7+
- A text editor or IDE
- Completed [HTTP Server Guide](http-server.md)

## Prerequisites { #prerequisites }

!!! note "Required: Complete HTTP Server Guide"

    This guide assumes you have completed **[HTTP Server Guide](http-server.md)** and have the working CRUD application with `Application`, `UserController`, `UserService`, `UserRepository`, and `InMemoryUserRepository`.

    If you haven't completed the HTTP server guide yet, do that first, because this guide extends the same API with advanced request mapping, interceptors, error handling, and authorization.

## Overview { #overview }

Basic [JSON](https://www.json.org/json-en.html) CRUD routes cover the most common HTTP use case, but [HTTP](https://www.rfc-editor.org/rfc/rfc9110) has a wider surface area than JSON bodies and path
variables. Real APIs often need richer request mapping, reusable behavior around routes, consistent error responses, and lightweight security checks at the transport boundary.

The advanced server guide keeps the same application model and expands only the HTTP edge. That mirrors production code: the service and repository should not need to know whether a request came from
JSON, a form, a multipart upload, or a route protected by an interceptor.

### Request Forms Beyond JSON { #request-forms-beyond-json }

Not every HTTP request is a JSON document. Some endpoints receive form fields, uploaded files, raw bodies, headers, or request metadata. Kora lets controller methods declare these inputs as typed
parameters, so the method signature still describes the transport contract.

This guide expands request handling with:

- request context for metadata that belongs to the current HTTP request
- form fields for classic `application/x-www-form-urlencoded` flows
- multipart parts for file upload style endpoints
- helper routes that demonstrate custom mapping and response control

### Cross-Cutting HTTP Behavior { #cross-cutting-http-behavior }

Some behavior should apply around routes instead of inside every method body. Interceptors are the HTTP-server tool for that. They can observe or modify request handling before and after a controller
method runs. That makes them suitable for logging, lightweight authorization, request enrichment, or other transport-level policies.

The important boundary is that interceptors should stay focused on HTTP concerns. They should not become a hidden service layer.

### Error and Authorization Boundaries { #error-authorization-boundaries }

As APIs grow, inconsistent errors become painful for clients. A shared exception handler gives failures a predictable response shape. Simple API-key authorization shows another common transport
boundary: the controller area can be protected before business logic runs, while services and repositories stay unaware of headers and auth metadata.

By the end of this guide, the HTTP server layer should feel like more than route annotations: it is the place where request mapping, response shaping, interception, error handling, and simple
authorization are coordinated.

The practical flow is:

1. add a request context mapper for one route
2. add form and multipart handling in a separate controller
3. introduce controller interceptors
4. centralize error responses with an exception handler
5. protect one controller area with a simple API key

## Custom Mapper { #custom-mapper }

For the full rules for custom route parameters and `HttpServerRequestMapper<T>`, see [HTTP Server custom parameters](../documentation/http-server.md#custom-parameter).

Sometimes a route needs more than a JSON body or a path variable. It may also need request metadata such as:

- a request ID from headers
- a user agent
- a session ID from cookies

You could pass all of those values as separate method parameters, but once they conceptually belong together, a typed object is easier to read and easier to evolve later.

That is what `HttpServerRequestMapper<T>` is for. It lets you derive one typed parameter from the raw HTTP request.

Create the `RequestContextMapper`:

===! ":fontawesome-brands-java: `Java`"

    Add these nested types inside `UserController.java`:

    ```java
    public record RequestContext(String requestId, String userAgent, String sessionId) {}

    public static final class RequestContextMapper implements HttpServerRequestMapper<RequestContext> {

        @Override
        public RequestContext apply(HttpServerRequest request) {
            String sessionId = request.cookies().stream()
                    .filter(cookie -> "sessionId".equals(cookie.name()))
                    .map(cookie -> cookie.value())
                    .findFirst()
                    .orElse(null);

            return new RequestContext(
                    request.headers().getFirst("X-Request-ID"),
                    request.headers().getFirst("User-Agent"),
                    sessionId);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Add the same idea in `UserController.kt`:

    ```kotlin
    data class RequestContext(
        val requestId: String?,
        val userAgent: String?,
        val sessionId: String?
    )

    class RequestContextMapper : HttpServerRequestMapper<RequestContext> {
        override fun apply(request: HttpServerRequest): RequestContext {
            val sessionId = request.cookies()
                .firstOrNull { it.name() == "sessionId" }
                ?.value()

            return RequestContext(
                request.headers().getFirst("X-Request-ID"),
                request.headers().getFirst("User-Agent"),
                sessionId
            )
        }
    }
    ```

Use it on `createUser()`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpRoute(method = HttpMethod.POST, path = "/users")
    @Json
    public HttpResponseEntity<UserResponse> createUser(
            @Json UserRequest request,
            @Mapping(RequestContextMapper.class) RequestContext context) {
        System.out.printf(
                "Creating user with request ID: %s, user agent: %s, session ID: %s%n",
                context.requestId(), context.userAgent(), context.sessionId());

        UserResponse user = userService.createUser(request);
        return HttpResponseEntity.of(201, HttpHeaders.of(), user);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpRoute(method = HttpMethod.POST, path = "/users")
    @Json
    fun createUser(
        @Json request: UserRequest,
        @Mapping(RequestContextMapper::class) context: RequestContext
    ): HttpResponseEntity<UserResponse> {
        println(
            "Creating user with request ID: ${context.requestId}, " +
                "user agent: ${context.userAgent}, session ID: ${context.sessionId}"
        )

        val user = userService.createUser(request)
        return HttpResponseEntity.of(201, HttpHeaders.of(), user)
    }
    ```

Why this abstraction is useful:

- `HttpServerRequestMapper<T>` lets you create any typed object from the request
- `@Mapping(...)` tells Kora to use that mapper for one specific parameter
- the route signature stays compact even when the route needs several request-derived values

This is often a better fit than endlessly growing controller method signatures.

## New Controller { #new-controller }

The full request-body model for JSON, forms, and multipart is described in [HTTP Server request body](../documentation/http-server.md#request-body).

The next advanced topic is request bodies that are not JSON.

So far the base guide used only JSON DTOs. Real HTTP APIs also often need:

- `application/x-www-form-urlencoded`
- `multipart/form-data`

What these formats are:

- `application/x-www-form-urlencoded` is the classic browser form format. A very typical example is a standard account-creation form on a website where the browser submits a small set of text fields.
- `multipart/form-data` is the format used when the request is split into named parts, especially when files or binary content are involved.

You can think about them like this:

- use form-url-encoded when the body is basically a small set of text fields
- use multipart when the body is made of named parts and some of those parts may be files

Even in JSON-first systems, these formats still appear often:

- browser-based admin tools
- legacy integrations
- upload endpoints
- webhook providers

DataController helps because we keep these routes out of `UserController` on purpose:

- `UserController` stays focused on user CRUD
- `DataController` becomes a transport playground for alternate HTTP body formats

That keeps the business-oriented controller easier to read.

Create `DataController`:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/httpserver/advanced/controller/DataController.java"
    package ru.tinkoff.kora.guide.httpserver.advanced.controller;

    import java.util.List;
    import java.util.stream.Collectors;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.http.common.HttpMethod;
    import ru.tinkoff.kora.http.common.annotation.HttpRoute;
    import ru.tinkoff.kora.http.common.annotation.Path;
    import ru.tinkoff.kora.http.common.form.FormMultipart;
    import ru.tinkoff.kora.http.common.form.FormUrlEncoded;
    import ru.tinkoff.kora.http.server.common.HttpServerResponseException;
    import ru.tinkoff.kora.http.server.common.annotation.HttpController;
    import ru.tinkoff.kora.json.common.annotation.Json;

    @Component
    @HttpController
    public final class DataController {

        @HttpRoute(method = HttpMethod.POST, path = "/data/form")
        public String processForm(FormUrlEncoded formBody) {
            var namePart = formBody.get("name");
            var name = namePart == null || namePart.values().isEmpty() ? "World" : namePart.values().get(0);
            return "Hello World, " + name;
        }

        @HttpRoute(method = HttpMethod.POST, path = "/data/upload")
        @Json
        public UploadResponse processUpload(FormMultipart multipart) {
            List<String> fileNames = multipart.parts().stream()
                    .map(FormMultipart.FormPart::name)
                    .sorted()
                    .collect(Collectors.toList());
            return new UploadResponse(fileNames.size(), fileNames);
        }

        @HttpRoute(method = HttpMethod.POST, path = "/data/mapping-request")
        public String processMappedRequest(String body) {
            return "Received mapped body: " + body;
        }

        @HttpRoute(method = HttpMethod.GET, path = "/data/mapping-by-code/{code}")
        @Json
        public Payload mappingByCode(@Path int code) {
            if (code == 200) {
                return new Payload("Hello from response mapper");
            }
            throw HttpServerResponseException.of(code, "Request failed with code " + code);
        }

        @Json
        public record Payload(String message) {}

        @Json
        public record UploadResponse(int fileCount, List<String> fileNames) {}
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/httpserver/advanced/controller/DataController.kt"
    package ru.tinkoff.kora.guide.httpserver.advanced.controller

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.http.common.HttpMethod
    import ru.tinkoff.kora.http.common.annotation.HttpRoute
    import ru.tinkoff.kora.http.common.annotation.Path
    import ru.tinkoff.kora.http.common.form.FormMultipart
    import ru.tinkoff.kora.http.common.form.FormUrlEncoded
    import ru.tinkoff.kora.http.server.common.HttpServerResponseException
    import ru.tinkoff.kora.http.server.common.annotation.HttpController
    import ru.tinkoff.kora.json.common.annotation.Json

    @Component
    @HttpController
    class DataController {

        @HttpRoute(method = HttpMethod.POST, path = "/data/form")
        fun processForm(formBody: FormUrlEncoded): String {
            val name = formBody.get("name")?.values()?.firstOrNull() ?: "World"
            return "Hello World, $name"
        }

        @HttpRoute(method = HttpMethod.POST, path = "/data/upload")
        @Json
        fun processUpload(multipart: FormMultipart): UploadResponse {
            val fileNames = multipart.parts().map { it.name() }.sorted()
            return UploadResponse(fileNames.size, fileNames)
        }

        @HttpRoute(method = HttpMethod.POST, path = "/data/mapping-request")
        fun processMappedRequest(body: String): String {
            return "Received mapped body: $body"
        }

        @HttpRoute(method = HttpMethod.GET, path = "/data/mapping-by-code/{code}")
        @Json
        fun mappingByCode(@Path code: Int): Payload {
            if (code == 200) {
                return Payload("Hello from response mapper")
            }
            throw HttpServerResponseException.of(code, "Request failed with code $code")
        }
    }

    @Json
    data class Payload(val message: String)

    @Json
    data class UploadResponse(val fileCount: Int, val fileNames: List<String>)
    ```

The helper routes at the bottom are intentionally tiny. They exist so the next guide, [HTTP Client Advanced Guide](http-client-advanced.md), can demonstrate:

- custom request mapping on `POST /data/mapping-request`
- response-code-specific decoding on `GET /data/mapping-by-code/{code}`

The success branch returns a tiny `Payload(message)`. The error branch throws `HttpServerResponseException`, and the global `ExceptionHandler` turns that into the shared `ErrorResponse(message)` JSON
contract for non-200 responses.

## Logging Interceptor { #logging-interceptor }

For more on local and global HTTP server interceptors, see [HTTP Server interceptors](../documentation/http-server.md#interceptors).

The next topic is interceptors.

An interceptor is useful when you want reusable behavior around request handling, for example:

- logging
- timing
- metrics
- security checks
- custom cross-cutting transport logic

The important design question is scope.

Sometimes you want behavior for the whole server. Sometimes you want it only around one controller or one route group. We start here with the narrower and safer case: a controller-level interceptor.

Create `LoggingInterceptor`:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/httpserver/advanced/controller/LoggingInterceptor.java"
    package ru.tinkoff.kora.guide.httpserver.advanced.controller;

    import java.util.concurrent.CompletionStage;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.Context;
    import ru.tinkoff.kora.http.server.common.HttpServerInterceptor;
    import ru.tinkoff.kora.http.server.common.HttpServerRequest;
    import ru.tinkoff.kora.http.server.common.HttpServerResponse;

    @Component
    public final class LoggingInterceptor implements HttpServerInterceptor {

        @Override
        public CompletionStage<HttpServerResponse> intercept(Context context, HttpServerRequest request, InterceptChain chain)
                throws Exception {
            long started = System.nanoTime();
            return chain.process(context, request).whenComplete((response, throwable) -> {
                long durationMs = (System.nanoTime() - started) / 1_000_000;
                int statusCode = response != null ? response.code() : 500;
                System.out.printf("Request: %s %s -> %d (%d ms)%n", request.method(), request.path(), statusCode, durationMs);
            });
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/httpserver/advanced/controller/LoggingInterceptor.kt"
    package ru.tinkoff.kora.guide.httpserver.advanced.controller

    import java.util.concurrent.CompletionStage
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.Context
    import ru.tinkoff.kora.http.server.common.HttpServerInterceptor
    import ru.tinkoff.kora.http.server.common.HttpServerRequest
    import ru.tinkoff.kora.http.server.common.HttpServerResponse

    @Component
    class LoggingInterceptor : HttpServerInterceptor {

        override fun intercept(
            context: Context,
            request: HttpServerRequest,
            chain: HttpServerInterceptor.InterceptChain
        ): CompletionStage<HttpServerResponse> {
            val started = System.nanoTime()
            return chain.process(context, request).whenComplete { response, _ ->
                val durationMs = (System.nanoTime() - started) / 1_000_000
                val statusCode = response?.code() ?: 500
                println("Request: ${request.method()} ${request.path()} -> $statusCode (${durationMs} ms)")
            }
        }
    }
    ```

Apply it only to `UserController`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    @InterceptWith(LoggingInterceptor.class)
    public final class UserController {
        // existing routes stay the same
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    @InterceptWith(LoggingInterceptor::class)
    class UserController(
        private val userService: UserService
    ) {
        // existing routes stay the same
    }
    ```

This is a good example of why controller-scoped interceptors are useful:

- they keep the behavior reusable
- but they do not affect unrelated controllers
- and they are often easier to reason about than immediately making behavior global

## Error Interceptor { #error-interceptor }

The complete exception and error mapping options are described in [HTTP Server error handling](../documentation/http-server.md#error-handling).

Now we move from controller-local behavior to server-wide behavior.

Error handling is a classic case where teams often want stronger control:

- the same JSON shape for all errors
- one place to translate exceptions into HTTP responses
- less repeated error-formatting logic in controllers

That is why a shared `ErrorResponse` and a global `ExceptionHandler` are common patterns.

Create `ErrorResponse`:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/httpserver/advanced/dto/ErrorResponse.java"
    package ru.tinkoff.kora.guide.httpserver.advanced.dto;

    import ru.tinkoff.kora.json.common.annotation.Json;

    @Json
    public record ErrorResponse(String message) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/httpserver/advanced/dto/ErrorResponse.kt"
    package ru.tinkoff.kora.guide.httpserver.advanced.dto

    import ru.tinkoff.kora.json.common.annotation.Json

    @Json
    data class ErrorResponse(
        val message: String
    )
    ```

Create a small exception for a deliberately restricted form name:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/httpserver/advanced/controller/RestrictedFormNameException.java"
    package ru.tinkoff.kora.guide.httpserver.advanced.controller;

    public final class RestrictedFormNameException extends RuntimeException {

        public RestrictedFormNameException(String name) {
            super("Form name '" + name + "' is restricted");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/httpserver/advanced/controller/RestrictedFormNameException.kt"
    package ru.tinkoff.kora.guide.httpserver.advanced.controller

    class RestrictedFormNameException(name: String) :
        RuntimeException("Form name '$name' is restricted")
    ```

Now update the form route so the new exception has a concrete source:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpRoute(method = HttpMethod.POST, path = "/data/form")
    public String processForm(FormUrlEncoded formBody) {
        var namePart = formBody.get("name");
        var name = namePart == null || namePart.values().isEmpty() ? "World" : namePart.values().get(0);
        if ("admin".equalsIgnoreCase(name)) {
            throw new RestrictedFormNameException(name);
        }
        return "Hello World, " + name;
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpRoute(method = HttpMethod.POST, path = "/data/form")
    fun processForm(formBody: FormUrlEncoded): String {
        val name = formBody.get("name")?.values()?.firstOrNull() ?: "World"
        if (name.equals("admin", ignoreCase = true)) {
            throw RestrictedFormNameException(name)
        }
        return "Hello World, $name"
    }
    ```

Create the global `ExceptionHandler`:

Kora lets us apply an interceptor to the whole HTTP server by tagging it with `HttpServerModule`. That is what makes this interceptor global rather than controller-local.

The interceptor depends on `JsonWriter<ErrorResponse>`, so it can always serialize the same typed error body instead of building ad-hoc strings by hand. That keeps the error transport contract
explicit and consistent.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/httpserver/advanced/controller/ExceptionHandler.java"
    package ru.tinkoff.kora.guide.httpserver.advanced.controller;

    import java.util.concurrent.CompletionException;
    import java.util.concurrent.CompletionStage;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.Context;
    import ru.tinkoff.kora.common.Tag;
    import ru.tinkoff.kora.guide.httpserver.advanced.dto.ErrorResponse;
    import ru.tinkoff.kora.http.common.body.HttpBody;
    import ru.tinkoff.kora.http.server.common.HttpServerInterceptor;
    import ru.tinkoff.kora.http.server.common.HttpServerModule;
    import ru.tinkoff.kora.http.server.common.HttpServerRequest;
    import ru.tinkoff.kora.http.server.common.HttpServerResponse;
    import ru.tinkoff.kora.http.server.common.HttpServerResponseException;
    import ru.tinkoff.kora.json.common.JsonWriter;

    @Tag(HttpServerModule.class)
    @Component
    public final class ExceptionHandler implements HttpServerInterceptor {

        private final JsonWriter<ErrorResponse> errorJsonWriter;

        public ExceptionHandler(JsonWriter<ErrorResponse> errorJsonWriter) {
            this.errorJsonWriter = errorJsonWriter;
        }

        @Override
        public CompletionStage<HttpServerResponse> intercept(Context context, HttpServerRequest request, InterceptChain chain)
                throws Exception {
            return chain.process(context, request).exceptionally(throwable -> {
                Throwable cause = unwrap(throwable);
                if (cause instanceof RestrictedFormNameException restrictedFormNameException) {
                    return jsonResponse(400, restrictedFormNameException.getMessage());
                }
                if (cause instanceof HttpServerResponseException responseException) {
                    return jsonResponse(responseException.code(), responseException.getMessage());
                }
                if (cause instanceof IllegalArgumentException) {
                    return jsonResponse(400, "Invalid request parameters");
                }
                if (cause instanceof SecurityException) {
                    return jsonResponse(403, cause.getMessage() != null ? cause.getMessage() : "Access denied");
                }
                return jsonResponse(500, "An unexpected error occurred");
            });
        }

        private HttpServerResponse jsonResponse(int statusCode, String message) {
            return HttpServerResponse.of(statusCode, HttpBody.json(this.errorJsonWriter.toByteArrayUnchecked(new ErrorResponse(message))));
        }

        private static Throwable unwrap(Throwable throwable) {
            Throwable current = throwable;
            while (current instanceof CompletionException && current.getCause() != null) {
                current = current.getCause();
            }
            return current;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/httpserver/advanced/controller/ExceptionHandler.kt"
    package ru.tinkoff.kora.guide.httpserver.advanced.controller

    import java.util.concurrent.CompletionException
    import java.util.concurrent.CompletionStage
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.Context
    import ru.tinkoff.kora.common.Tag
    import ru.tinkoff.kora.guide.httpserver.advanced.dto.ErrorResponse
    import ru.tinkoff.kora.http.common.body.HttpBody
    import ru.tinkoff.kora.http.server.common.HttpServerInterceptor
    import ru.tinkoff.kora.http.server.common.HttpServerModule
    import ru.tinkoff.kora.http.server.common.HttpServerRequest
    import ru.tinkoff.kora.http.server.common.HttpServerResponse
    import ru.tinkoff.kora.http.server.common.HttpServerResponseException
    import ru.tinkoff.kora.json.common.JsonWriter

    @Tag(HttpServerModule::class)
    @Component
    class ExceptionHandler(
        private val errorJsonWriter: JsonWriter<ErrorResponse>
    ) : HttpServerInterceptor {

        override fun intercept(
            context: Context,
            request: HttpServerRequest,
            chain: HttpServerInterceptor.InterceptChain
        ): CompletionStage<HttpServerResponse> {
            return chain.process(context, request).exceptionally { throwable ->
                val cause = unwrap(throwable)
                when (cause) {
                    is RestrictedFormNameException -> jsonResponse(400, cause.message ?: "Restricted form name")
                    is HttpServerResponseException -> jsonResponse(cause.code(), cause.message ?: "HTTP error")
                    is IllegalArgumentException -> jsonResponse(400, "Invalid request parameters")
                    is SecurityException -> jsonResponse(403, cause.message ?: "Access denied")
                    else -> jsonResponse(500, "An unexpected error occurred")
                }
            }
        }

        private fun jsonResponse(statusCode: Int, message: String): HttpServerResponse {
            return HttpServerResponse.of(statusCode, HttpBody.json(errorJsonWriter.toByteArrayUnchecked(ErrorResponse(message))))
        }

        private fun unwrap(throwable: Throwable): Throwable {
            var current = throwable
            while (current is CompletionException && current.cause != null) {
                current = current.cause!!
            }
            return current
        }
    }
    ```

Keep the regular user lookup local to `UserController`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}")
    @Json
    public UserResponse getUser(@Path String userId) {
        return userService.getUser(userId)
                .orElseThrow(() -> HttpServerResponseException.of(404, "User not found"));
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}")
    @Json
    fun getUser(@Path userId: String): UserResponse {
        return userService.getUser(userId)
            .orElseThrow { HttpServerResponseException.of(404, "User not found") }
    }
    ```

This is a useful separation:

- the form route throws a custom application error only for the new advanced behavior
- regular HTTP status failures can still use `HttpServerResponseException`
- one interceptor translates both forms into the same response shape
- the whole API now returns the same `ErrorResponse` shape

## API Key Authorization { #api-key }

This section uses an interceptor as the transport boundary; the general interceptor rules are covered in the [HTTP Server documentation](../documentation/http-server.md#interceptors).

The last step introduces a small security mechanism.

We do not protect the whole application. We protect only `DataController`, because it is a nice isolated place to demonstrate the pattern without making the main CRUD flow harder to follow.

The idea is intentionally simple:

- the expected API key lives in configuration
- the value can come from `HTTP_ADVANCED_API_KEY`
- an interceptor reads the `Authorization` header
- if the value does not match, the interceptor throws `SecurityException`
- the global `ExceptionHandler` turns that into a `403` JSON response

This is not meant to be enterprise-grade authentication. It is a lightweight teaching example that shows how Kora interceptors and configuration can work together for authorization-like checks.

Create the `DataApiAuthConfig` contract:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/httpserver/advanced/controller/DataApiAuthConfig.java"
    package ru.tinkoff.kora.guide.httpserver.advanced.controller;

    import ru.tinkoff.kora.config.common.annotation.ConfigSource;

    @ConfigSource("auth.apiKey")
    public interface DataApiAuthConfig {
        String value();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/httpserver/advanced/controller/DataApiAuthConfig.kt"
    package ru.tinkoff.kora.guide.httpserver.advanced.controller

    import ru.tinkoff.kora.config.common.annotation.ConfigSource

    @ConfigSource("auth.apiKey")
    interface DataApiAuthConfig {
        fun value(): String
    }
    ```

Create the `DataApiAuthInterceptor`:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/httpserver/advanced/controller/DataApiAuthInterceptor.java"
    package ru.tinkoff.kora.guide.httpserver.advanced.controller;

    import java.util.concurrent.CompletionStage;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.Context;
    import ru.tinkoff.kora.http.server.common.HttpServerInterceptor;
    import ru.tinkoff.kora.http.server.common.HttpServerRequest;
    import ru.tinkoff.kora.http.server.common.HttpServerResponse;

    @Component
    public final class DataApiAuthInterceptor implements HttpServerInterceptor {

        private final DataApiAuthConfig config;

        public DataApiAuthInterceptor(DataApiAuthConfig config) {
            this.config = config;
        }

        @Override
        public CompletionStage<HttpServerResponse> intercept(Context context, HttpServerRequest request, InterceptChain chain)
                throws Exception {
            var authorization = request.headers().getFirst("authorization");
            if (!this.config.value().equals(authorization)) {
                throw new SecurityException("Invalid API key");
            }
            return chain.process(context, request);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/httpserver/advanced/controller/DataApiAuthInterceptor.kt"
    package ru.tinkoff.kora.guide.httpserver.advanced.controller

    import java.util.concurrent.CompletionStage
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.Context
    import ru.tinkoff.kora.http.server.common.HttpServerInterceptor
    import ru.tinkoff.kora.http.server.common.HttpServerRequest
    import ru.tinkoff.kora.http.server.common.HttpServerResponse

    @Component
    class DataApiAuthInterceptor(
        private val config: DataApiAuthConfig
    ) : HttpServerInterceptor {

        override fun intercept(
            context: Context,
            request: HttpServerRequest,
            chain: HttpServerInterceptor.InterceptChain
        ): CompletionStage<HttpServerResponse> {
            val authorization = request.headers().getFirst("authorization")
            if (config.value() != authorization) {
                throw SecurityException("Invalid API key")
            }
            return chain.process(context, request)
        }
    }
    ```

Apply it to `DataController`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    @InterceptWith(DataApiAuthInterceptor.class)
    public final class DataController {
        // routes stay the same
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    @InterceptWith(DataApiAuthInterceptor::class)
    class DataController {
        // routes stay the same
    }
    ```

Configure the API key:

Add the authorization value to `application.conf`:

For the full configuration reference, see [Configuration](../documentation/config.md).

===! ":material-code-json: `Hocon`"

    ```javascript title="src/main/resources/application.conf"
    auth {
      apiKey {
        value = "MySecuredApiKey" //(1)!
        value = ${?HTTP_ADVANCED_API_KEY} //(2)!
      }
    }
    ```

    1. Configured value consumed by the guide component.
    2. Configured value consumed by the guide component. Optional override from `HTTP_ADVANCED_API_KEY`.

=== ":simple-yaml: `YAML`"

    ```yaml title="src/main/resources/application.yaml"
    auth:
      apiKey:
        value: ${?HTTP_ADVANCED_API_KEY:"MySecuredApiKey"} #(1)!
    ```

    1. Configured value consumed by the guide component. Uses the shown default and allows `HTTP_ADVANCED_API_KEY` to override it.

The local default makes the guide easy to run, while the environment-variable override shows the production-friendly pattern.

## Generated Code { #generated-code }

Kora declarative HTTP controllers are compiled into `HttpServerRequestHandler` components.

After you run:

```bash
./gradlew clean classes
```

inspect the generated module:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-http-server-advanced-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/httpserver/advanced/controller/DataControllerModule.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-http-server-advanced-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/httpserver/advanced/controller/DataControllerModule.kt
    ```

For example, the generated handler for the form endpoint looks like this:

===! ":fontawesome-brands-java: `Java`"

    ```java
    default HttpServerRequestHandler post_data_form(DataController _controller,
        HttpServerRequestMapper<FormUrlEncoded> formBodyHttpRequestMapper,
        HttpServerResponseMapper<String> _responseMapper,
        BlockingRequestExecutor _executor,
        DataApiAuthInterceptor _interceptor1) {
      return HttpServerRequestHandlerImpl.of("POST", "/data/form", (_ctx, _request) -> {
        try {
          return _interceptor1.intercept(_ctx, _request, (_ctx_1, _request1) -> {
            return _executor.execute(_ctx, () -> {
              final FormUrlEncoded formBody = formBodyHttpRequestMapper.apply(_request1);
              var _result = _controller.processForm(formBody);
              return _responseMapper.apply(_ctx, _request, _result);
            });
          });
        } catch (Exception _e) {
          return CompletableFuture.failedFuture(_e);
        }
      });
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    public fun post_data_form(
      _controller: DataController,
      _formBodyMapper: HttpServerRequestMapper<FormUrlEncoded>,
      _responseMapper: HttpServerResponseMapper<String>,
      _executor: BlockingRequestExecutor,
    ): HttpServerRequestHandler = HttpServerRequestHandlerImpl.of("POST", "/data/form") { _ctx, _request ->
      try {
        _executor.execute(_ctx) {
          val formBody = (_formBodyMapper as HttpServerRequestMapper<FormUrlEncoded?>).apply(_request)
            ?: throw HttpServerResponseException.of(400, "Parameter formBody is not nullable, but got null from mapper")
          val _result = _controller.processForm(formBody)
          return@execute _responseMapper.apply(_ctx, _request, _result)
        }
      } catch (_e: Exception) {
        if (_e is HttpServerResponse) {
          CompletableFuture.failedFuture(_e)
        } else {
          CompletableFuture.failedFuture(HttpServerResponseException.of(400, _e))
        }
      }
    }
    ```

This generated code is the bridge between the nice controller method and the low-level HTTP server pipeline:

- `HttpServerRequestHandlerImpl.of(...)` registers the route method and path
- `HttpServerRequestMapper<FormUrlEncoded>` reads the request body
- `DataApiAuthInterceptor` wraps the route
- `BlockingRequestExecutor` runs the blocking controller method safely
- `HttpServerResponseMapper<String>` turns the return value into an HTTP response

This is a strong debugging technique for both developers and AI assistants: when route behavior is unclear, generated sources show the exact request pipeline that Kora compiled from annotations.

## Imperative Controller { #imperative-controller }

Most application endpoints should use declarative controllers because they are easier to read and test. Kora also allows a lower-level imperative style through `HttpServerRequestHandler`, which is
useful when you need direct control over the request pipeline or want to understand what generated controllers compile down to.

Add this manual handler to `Application.java` or `Application.kt`:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/httpserver/advanced/Application.java"
    package ru.tinkoff.kora.guide.httpserver.advanced;

    import java.util.concurrent.CompletableFuture;
    import ru.tinkoff.kora.application.graph.KoraApplication;
    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.config.hocon.HoconConfigModule;
    import ru.tinkoff.kora.guide.httpserver.advanced.controller.DataApiAuthConfig;
    import ru.tinkoff.kora.http.common.body.HttpBody;
    import ru.tinkoff.kora.http.server.common.HttpServerResponse;
    import ru.tinkoff.kora.http.server.common.handler.HttpServerRequestHandler;
    import ru.tinkoff.kora.http.server.common.handler.HttpServerRequestHandlerImpl;
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule;
    import ru.tinkoff.kora.json.module.JsonModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            UndertowHttpServerModule {  // <----- Connected module

        default HttpServerRequestHandler manualDataPingHandler(DataApiAuthConfig authConfig) {
            return HttpServerRequestHandlerImpl.get("/manual/data/ping", (context, request) -> {
                var authorization = request.headers().getFirst("authorization");
                if (!authConfig.value().equals(authorization)) {
                    return CompletableFuture.completedFuture(
                            HttpServerResponse.of(403, HttpBody.plaintext("Invalid API key")));
                }
                return CompletableFuture.completedFuture(
                        HttpServerResponse.of(200, HttpBody.plaintext("manual-data-pong")));
            });
        }

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/httpserver/advanced/Application.kt"
    package ru.tinkoff.kora.guide.httpserver.advanced

    import ru.tinkoff.kora.application.graph.KoraApplication
    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.config.hocon.HoconConfigModule
    import ru.tinkoff.kora.guide.httpserver.advanced.controller.DataApiAuthConfig
    import ru.tinkoff.kora.http.common.body.HttpBody
    import ru.tinkoff.kora.http.server.common.HttpServerResponse
    import ru.tinkoff.kora.http.server.common.handler.HttpServerRequestHandler
    import ru.tinkoff.kora.http.server.common.handler.HttpServerRequestHandlerImpl
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule
    import ru.tinkoff.kora.json.module.JsonModule
    import ru.tinkoff.kora.logging.logback.LogbackModule
    import java.util.concurrent.CompletableFuture

    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        UndertowHttpServerModule {  // <----- Connected module

        fun manualDataPingHandler(authConfig: DataApiAuthConfig): HttpServerRequestHandler {
            return HttpServerRequestHandlerImpl.get("/manual/data/ping") { _, request ->
                val authorization = request.headers().getFirst("authorization")
                if (authConfig.value() != authorization) {
                    CompletableFuture.completedFuture(HttpServerResponse.of(403, HttpBody.plaintext("Invalid API key")))
                } else {
                    CompletableFuture.completedFuture(HttpServerResponse.of(200, HttpBody.plaintext("manual-data-pong")))
                }
            }
        }
    }

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

The method returns a framework handler directly:

- `HttpServerRequestHandlerImpl.get(...)` registers `GET /manual/data/ping`
- the lambda receives `Context` and `HttpServerRequest`
- the handler reads the `Authorization` header manually
- the method returns `CompletionStage<HttpServerResponse>` through `CompletableFuture.completedFuture(...)`

After compilation, the generated application graph wires this handler as another HTTP route:

===! ":fontawesome-brands-java: `Java`"

    ```java
    component44 = graphDraw.addNode0(_type_of_component44, new Class<?>[]{}, g -> impl.manualDataPingHandler(
          g.get(ApplicationGraph.holder0.component29)
        ), List.of(), component29);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    component28 = graphDraw.addNode0(map["component28"],
      arrayOf(),
      { impl.manualDataPingHandler(
        it.get(holder0.component27)
      ) },
      listOf(),
      component27
    )
    ```

The important distinction is that declarative controllers generate a `HttpServerRequestHandler` for you, while the imperative style lets you provide that handler yourself.

## Check Application { #check-app }

```
./gradlew clean classes
./gradlew test
./gradlew run
```

Try the richer `createUser` request with request metadata:

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: test-123" \
  -H "User-Agent: curl-test" \
  -H "Cookie: sessionId=session-42" \
  -d '{"name": "John Doe", "email": "john@example.com"}'
```

Then call the protected `DataController` routes with the API key:

```bash
curl -X POST http://localhost:8080/data/form \
  -H "Authorization: MySecuredApiKey" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "name=Ivan"

curl -X POST http://localhost:8080/data/upload \
  -H "Authorization: MySecuredApiKey" \
  -F "file=@README.md"

curl http://localhost:8080/manual/data/ping \
  -H "Authorization: MySecuredApiKey"
```

If the `Authorization` header is missing or wrong, the route should return `403` with the shared `ErrorResponse` body.

## Best Practices { #best-practices }

- Introduce advanced HTTP concepts one at a time instead of mixing them into the first server example.
- Use `HttpServerRequestMapper` when several request values belong to one typed concept.
- Keep transport-specific routes in a separate controller so business controllers stay focused.
- Prefer controller-level interceptors before making behavior global.
- Use a global interceptor only for behavior that truly should affect the whole HTTP server.
- Use imperative `HttpServerRequestHandler` sparingly, when direct request/response control is clearer than annotations.
- Put simple secrets behind environment-variable overrides even in guide applications.

## Summary { #summary }

You extended the basic Kora HTTP server with:

- a typed `RequestContextMapper`
- a `DataController` for forms, multipart uploads, and advanced client helper routes
- a controller-level `LoggingInterceptor`
- a shared `ErrorResponse`
- a global `ExceptionHandler`
- a simple API-key authorization layer on `DataController`
- a manual `HttpServerRequestHandler` endpoint that shows the low-level route API

## What You Learned { #you-learned }

- custom request mapping with `HttpServerRequestMapper` and `@Mapping`
- additional body formats with `FormUrlEncoded` and `FormMultipart`
- controller-level interceptors with `@InterceptWith`
- global interceptors with `@Tag(HttpServerModule.class)`
- simple header-based authorization through an interceptor and configuration
- imperative route registration with `HttpServerRequestHandlerImpl`

## Troubleshooting { #troubleshooting }

**RequestContextMapper is not used:**

- Check that the parameter is annotated with `@Mapping(...)`.
- Make sure the mapper implements `HttpServerRequestMapper<T>`.

**Multipart request does not work:**

- Make sure the client sends `multipart/form-data`.
- Check that the uploaded part names match what the controller processes.

**Controller-level logging does not appear:**

- Check `@InterceptWith(LoggingInterceptor.class)` or `@InterceptWith(LoggingInterceptor::class)` on the controller.
- Verify the interceptor itself is a component.

**Global exception handler does not run:**

- Check `@Tag(HttpServerModule.class)` on the interceptor.
- Make sure the class is also annotated with `@Component`.

**Protected DataController routes return 403:**

- Check the `Authorization` header value.
- Make sure it matches `auth.apiKey.value`.
- If you use `HTTP_ADVANCED_API_KEY`, remember that it overrides the local default.

## What's Next? { #whats-next }

- [Store Files with S3](s3.md) to build on the multipart and advanced HTTP request-handling model.
- [HTTP Client](http-client.md) if you have not built a client app yet.
- [HTTP Client Advanced](http-client-advanced.md) after HTTP Client, to call these richer endpoints from another Kora app.
- [OpenAPI HTTP Server](openapi-http-server.md) before [OpenAPI HTTP Server Advanced](openapi-http-server-advanced.md), because the advanced OpenAPI guide requires both tracks.
- [Observability](observability.md) to monitor advanced request mappings, interceptors, and error handling.

## Help { #help }

If you get stuck:

- compare with [Kora Java HTTP Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-http-server-advanced-app) and [Kora Kotlin HTTP Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-http-server-advanced-app)
- revisit [HTTP Server](http-server.md) for the base controller-service-repository flow
- check the [HTTP Server documentation](../documentation/http-server.md)
- check the [Container documentation](../documentation/container.md)
