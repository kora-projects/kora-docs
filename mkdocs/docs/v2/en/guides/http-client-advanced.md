---
search:
  exclude: true
title: HTTP Client Advanced Guide
summary: Extend the basic HTTP client guide with form and multipart bodies, custom request mapping, response-code-aware decoding, method and client interceptors, API-key authorization and imperative calls
description: "Advanced declarative HTTP client patterns for Kora 2.0: FormUrlEncoded and FormMultipart request bodies built from FormPart values, a custom HttpClientRequestMapper attached with @Mapping, @ResponseCodeMapper with ResponseCodeMapper.DEFAULT and per-status HttpClientResponseMapper implementations, HttpClientInterceptor applied through @InterceptWith for method logging and API-key authorization backed by @ConfigSource and @ConfigMapper, per-operation settings from HttpClientOperationConfig, and the imperative HttpClient with HttpClientRequest.of and a closeable HttpClientResponse."
agent:
  use_when: "Use this file for questions about non-trivial Kora 2.0 HTTP client calls: sending FormUrlEncoded or FormMultipart bodies with FormPart, writing an HttpClientRequestMapper and binding it with @Mapping, decoding different status codes into typed variants with @ResponseCodeMapper and ResponseCodeMapper.DEFAULT, HttpClientDecoderException raised inside a mapper, HttpClientInterceptor with @InterceptWith on a method or the whole interface, adding an API-key header from an @ConfigSource or @ConfigMapper value, per-operation keys such as httpClient.dataApi.getMappedByCode.requestTimeout and HttpClientOperationConfig, and building requests by hand with HttpClientRequest.of, HttpClient.with and HttpClient.execute."
tags: http-client, advanced, form, multipart, interceptor, mapping, auth, imperative
---

# Advanced HTTP Client Guide { #advanced-http-client-guide }

This guide introduces advanced declarative HTTP client patterns in Kora. It covers how clients call form, multipart, and helper transport routes, how custom body mappers shape unusual request and
response payloads, and how typed response variants represent different HTTP statuses. You will also see how method-level and client-level interceptors add cross-cutting behavior such as API-key
authorization, and how to drop down to the imperative `HttpClient` when a request must be built by hand.

Everything on this page stays synchronous. Interceptors return an `HttpClientResponse`, `HttpClient.execute(...)` returns an `HttpClientResponse`, and mappers work on a response that is already
available. There is no callback, future, or coroutine anywhere in the client contract.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java HTTP Client Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-http-client-advanced-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin HTTP Client Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-http-client-advanced-app).

## What You'll Build { #youll-build }

You will extend the client application with:

- a dedicated `DataApiClient`
- `FormUrlEncoded` and `FormMultipart` requests
- a custom `HttpClientRequestMapper`
- response-code-aware decoding with `@ResponseCodeMapper`
- a method-level `HttpClientInterceptor`
- a client-wide API-key auth interceptor
- an imperative call through the base `HttpClient` reusing the generated client configuration
- a dedicated aggregate endpoint in `ClientTestController` that exercises the advanced data routes

## What You'll Need { #youll-need }

- JDK 25 or later
- Gradle 9+ (the reference applications use Gradle Wrapper `9.5.1`)
- Docker Desktop or another local Docker environment for container-based tests
- A text editor or IDE

## Prerequisites { #prerequisites }

!!! note "Required: Complete HTTP Client and Advanced HTTP Server Guides"

    This guide assumes you have completed **[HTTP Server Advanced Guide](http-server-advanced.md)** and **[HTTP Client Guide](http-client.md)**, and that the advanced server side already exposes the `DataController` routes.

    If you haven't completed those guides yet, do that first, because they already cover the base HTTP server/client flow and this guide focuses only on advanced client mapping against the advanced server routes.

## Overview { #overview }

Advanced [HTTP](https://www.rfc-editor.org/rfc/rfc9110) clients appear when a remote API is not just JSON CRUD. Some services expose form endpoints, multipart uploads, custom payload formats, or
response contracts where different status codes mean different typed outcomes. A good client should model those details explicitly without leaking low-level HTTP code into the rest of the application.

The key design choice is to keep advanced transport mechanics near the generated client. Form encoding, multipart construction, custom mapping, status decoding, and authorization headers are all
client-boundary concerns, not business logic concerns.

### HTTP Forms { #http-forms }

Kora declarative clients can describe several HTTP interaction styles:

- form parameters for `application/x-www-form-urlencoded` requests
- multipart parts for upload-style calls
- custom request mappers for payloads that do not fit the default JSON model
- typed response mapping for APIs where status codes carry domain meaning

The main principle is the same as the basic client guide: the method signature should describe the remote contract clearly enough that callers do not need to build requests by hand.

### Client Interceptors { #client-interceptors }

Client interceptors run around outbound calls. They are useful for cross-cutting transport behavior such as logging, correlation IDs, authentication headers, API keys, or metrics. Because interceptors
live at the client boundary, they avoid duplicating the same header or logging code in every method.

An interceptor implements one synchronous method, `HttpClientResponse processRequest(InterceptChain chain, HttpClientRequest request)`. It may rewrite the request, call `chain.process(request)`,
inspect the response, and even skip the call entirely. Interceptors declared on the interface run before interceptors declared on a method.

This guide uses interceptors for both method-level behavior and reusable client-level authorization.

### Targeted Changes { #targeted-changes }

Advanced client features can easily spread through an application if the generated client is used everywhere directly. This guide keeps the transport-heavy pieces inside the client interface so form
calls, multipart calls, custom decoding, and authorization remain near the transport boundary. The rest of the application can work with clearer methods and typed results.

The practical flow is:

1. add a dedicated client for the advanced data routes
2. call form and multipart endpoints declaratively
3. add a custom request mapper for one payload shape
4. decode response statuses into typed results
5. attach logging and API-key authorization with interceptors
6. reach for the imperative `HttpClient` where the declarative model does not fit

## New HTTP Client { #new-http-client }

The first advanced client concept is still very concrete: call the extra routes introduced by `DataController`.

We keep these calls in a separate `DataApiClient` so the transport-heavy examples do not clutter the simpler `UserApiClient`.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/httpclient/client/DataApiClient.java"
    package io.koraframework.guide.httpclient.client;

    import java.nio.charset.StandardCharsets;
    import java.util.List;
    import io.koraframework.http.client.common.annotation.HttpClient;
    import io.koraframework.http.common.HttpMethod;
    import io.koraframework.http.common.annotation.HttpRoute;
    import io.koraframework.http.common.form.FormMultipart;
    import io.koraframework.http.common.form.FormUrlEncoded;
    import io.koraframework.json.common.annotation.Json;

    @HttpClient("httpClient.dataApi")
    public interface DataApiClient {

        @HttpRoute(method = HttpMethod.POST, path = "/data/form")
        String processForm(FormUrlEncoded body);

        @HttpRoute(method = HttpMethod.POST, path = "/data/upload")
        @Json
        UploadResponse processUpload(FormMultipart body);

        default UploadResponse sampleUpload() {
            return this.processUpload(new FormMultipart(List.of(
                    FormMultipart.data("field1", "some data content"),
                    FormMultipart.file("field2", "example1.txt", "text/plain", "some file content".getBytes(StandardCharsets.UTF_8)))));
        }

        @Json
        record UploadResponse(int fileCount, List<String> fileNames) {}
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/httpclient/client/DataApiClient.kt"
    package io.koraframework.guide.httpclient.client

    import io.koraframework.http.client.common.annotation.HttpClient
    import io.koraframework.http.common.HttpMethod
    import io.koraframework.http.common.annotation.HttpRoute
    import io.koraframework.http.common.form.FormMultipart
    import io.koraframework.http.common.form.FormUrlEncoded
    import io.koraframework.json.common.annotation.Json
    import java.nio.charset.StandardCharsets

    @HttpClient("httpClient.dataApi")
    interface DataApiClient {

        @HttpRoute(method = HttpMethod.POST, path = "/data/form")
        fun processForm(body: FormUrlEncoded): String

        @HttpRoute(method = HttpMethod.POST, path = "/data/upload")
        @Json
        fun processUpload(body: FormMultipart): UploadResponse

        fun sampleUpload(): UploadResponse {
            return processUpload(
                FormMultipart(
                    listOf(
                        FormMultipart.data("field1", "some data content"),
                        FormMultipart.file(
                            "field2",
                            "example1.txt",
                            "text/plain",
                            "some file content".toByteArray(StandardCharsets.UTF_8)
                        )
                    )
                )
            )
        }

        @Json
        data class UploadResponse(val fileCount: Int, val fileNames: List<String>)
    }
    ```

This separation helps:

- `UserApiClient` stays focused on CRUD
- `DataApiClient` becomes the home for advanced transport examples
- the base guide stays easy to read

Two body types do the heavy lifting here, and both come from `io.koraframework.http.common.form`:

- `FormUrlEncoded` holds `FormPart(name, values)` entries and is encoded as `application/x-www-form-urlencoded`
- `FormMultipart` holds a list of parts built with `FormMultipart.data(...)` for plain fields and `FormMultipart.file(...)` for file parts, and is encoded as `multipart/form-data`

Neither type needs a `@Mapping`: Kora ships request mappers for both. `sampleUpload()` is an ordinary default method on the interface, so it is not a route — it is a convenience wrapper that builds the
multipart body and delegates to `processUpload`. Default methods are also skipped when Kora generates the per-method configuration, so they never add stray configuration keys.

The client needs its own configuration section, named by the `@HttpClient` value:

===! ":material-code-json: `Hocon`"

    ```javascript title="src/main/resources/application.conf"
    httpClient {
      dataApi {
        url = "http://localhost:8080" //(1)!
        url = ${?DATA_API_URL} //(2)!
        requestTimeout = 10s //(3)!
        telemetry.logging.enabled = true //(4)!
        getMappedByCode.requestTimeout = 2s //(5)!
      }
    }
    ```

    1. Base URL of the advanced server application (required, no default).
    2. Optional override of the base URL from the `DATA_API_URL` environment variable.
    3. Maximum time allowed for one client request (optional, no default).
    4. Enables request logging for this client (default: `false`).
    5. Per-operation override: every client method gets its own configuration block named after the method.

=== ":simple-yaml: `YAML`"

    ```yaml title="src/main/resources/application.yaml"
    httpClient:
      dataApi:
        url: ${DATA_API_URL:http://localhost:8080} #(1)!
        requestTimeout: 10s #(2)!
        telemetry:
          logging:
            enabled: true #(3)!
        getMappedByCode:
          requestTimeout: 2s #(4)!
    ```

    1. Base URL of the advanced server application (required, no default). Uses the shown default and allows `DATA_API_URL` to override it.
    2. Maximum time allowed for one client request (optional, no default).
    3. Enables request logging for this client (default: `false`).
    4. Per-operation override: every client method gets its own configuration block named after the method.

## Parameter Mapper { #parameter-mapper }

For more on client request-body mappers, see [HTTP Client request body](../documentation/http-client.md#request-body).

Sometimes a request body should not use the normal JSON or form mapping flow. A remote endpoint may expect a very specific text or binary representation, and you still want to model the input as your
own type.

That is what `HttpClientRequestMapper<T>` is for. It has one method, `HttpBodyOutput apply(T value)`, and `HttpBody` provides the factories for the usual representations: `HttpBody.plaintext(...)`,
`HttpBody.json(...)`, `HttpBody.octetStream(...)` and `HttpBody.of(contentType, bytes)`.

In this guide we use a small example:

- the method accepts `PlainTextGreetingBody`
- a mapper turns it into a plain-text HTTP body
- the advanced server echoes that mapped text back

===! ":fontawesome-brands-java: `Java`"

    Add these pieces inside `DataApiClient.java`:

    ```java
    import io.koraframework.common.annotation.Component;
    import io.koraframework.common.annotation.Mapping;
    import io.koraframework.http.client.common.request.HttpClientRequestMapper;
    import io.koraframework.http.common.body.HttpBody;
    import io.koraframework.http.common.body.HttpBodyOutput;

    @HttpRoute(method = HttpMethod.POST, path = "/data/mapping-request")
    String processMappedRequest(@Mapping(GreetingRequestMapper.class) PlainTextGreetingBody body);

    record PlainTextGreetingBody(String name) {}

    @Component
    final class GreetingRequestMapper implements HttpClientRequestMapper<PlainTextGreetingBody> {

        @Override
        public HttpBodyOutput apply(PlainTextGreetingBody value) {
            return HttpBody.plaintext("Hello " + value.name());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Add the same idea in `DataApiClient.kt`:

    ```kotlin
    import io.koraframework.common.annotation.Component
    import io.koraframework.common.annotation.Mapping
    import io.koraframework.http.client.common.request.HttpClientRequestMapper
    import io.koraframework.http.common.body.HttpBody
    import io.koraframework.http.common.body.HttpBodyOutput

    @HttpRoute(method = HttpMethod.POST, path = "/data/mapping-request")
    fun processMappedRequest(@Mapping(GreetingRequestMapper::class) body: PlainTextGreetingBody): String

    data class PlainTextGreetingBody(val name: String)

    @Component
    class GreetingRequestMapper : HttpClientRequestMapper<PlainTextGreetingBody> {

        override fun apply(value: PlainTextGreetingBody): HttpBodyOutput {
            return HttpBody.plaintext("Hello ${value.name}")
        }
    }
    ```

Note the `@Component` on the mapper. A request mapper referenced with `@Mapping` is always taken from the dependency graph — the generated client receives it as a constructor argument — so it has to be
a graph component even when it has no dependencies of its own. The same rule applies to every interceptor referenced by `@InterceptWith`.

This is the client-side analogue of the request mappers we introduced in the advanced server guide: a typed object becomes a transport representation in one clear place.

## Response Code Mapping { #response-code-mapping }

Default client behavior often treats a response as either:

- a successful body, for `2xx` statuses
- or an `HttpClientResponseException`, for everything else

That is enough for many APIs. But sometimes the contract intentionally says:

- `200` returns one JSON shape
- non-`200` responses return another JSON shape

That is where `@ResponseCodeMapper` becomes useful. It is repeatable, it takes an exact status code plus the `HttpClientResponseMapper` to use for it, and `ResponseCodeMapper.DEFAULT` covers every
status that is not listed explicitly. When at least one `@ResponseCodeMapper` is present, the generated client switches on the status code instead of throwing on non-`2xx`.

In this guide, `GET /data/mapping-by-code/{code}` behaves like this:

- `200` returns `{"message":"Hello from response mapper"}`
- other codes return `{"message":"Request failed with code <status>"}` through the shared server-side error payload

We model that as one sealed result type.

===! ":fontawesome-brands-java: `Java`"

    Add this inside `DataApiClient.java`:

    ```java
    import java.io.IOException;
    import io.koraframework.http.client.common.annotation.ResponseCodeMapper;
    import io.koraframework.http.client.common.exception.HttpClientDecoderException;
    import io.koraframework.http.client.common.response.HttpClientResponse;
    import io.koraframework.http.client.common.response.HttpClientResponseMapper;
    import io.koraframework.http.common.annotation.Path;
    import io.koraframework.json.common.JsonReader;

    @ResponseCodeMapper(code = ResponseCodeMapper.DEFAULT, mapper = MappedResponseErrorMapper.class)
    @ResponseCodeMapper(code = 200, mapper = MappedResponseSuccessMapper.class)
    @HttpRoute(method = HttpMethod.GET, path = "/data/mapping-by-code/{code}")
    MappedResponse getMappedByCode(@Path int code);

    sealed interface MappedResponse permits MappedResponse.Payload, MappedResponse.Error {

        @Json
        record Payload(String message) implements MappedResponse {}

        @Json
        record Error(int code, String message) implements MappedResponse {}

        @Json
        record ErrorPayload(String message) {}
    }

    @Component
    final class MappedResponseSuccessMapper implements HttpClientResponseMapper<MappedResponse> {

        private final JsonReader<MappedResponse.Payload> jsonReader;

        public MappedResponseSuccessMapper(JsonReader<MappedResponse.Payload> jsonReader) {
            this.jsonReader = jsonReader;
        }

        @Override
        public MappedResponse apply(HttpClientResponse response) throws IOException, HttpClientDecoderException {
            try (var is = response.body().asInputStream()) {
                return this.jsonReader.read(is.readAllBytes());
            }
        }
    }

    @Component
    final class MappedResponseErrorMapper implements HttpClientResponseMapper<MappedResponse> {

        private final JsonReader<MappedResponse.ErrorPayload> jsonReader;

        public MappedResponseErrorMapper(JsonReader<MappedResponse.ErrorPayload> jsonReader) {
            this.jsonReader = jsonReader;
        }

        @Override
        public MappedResponse apply(HttpClientResponse response) throws IOException, HttpClientDecoderException {
            try (var is = response.body().asInputStream()) {
                var payload = this.jsonReader.read(is.readAllBytes());
                return new MappedResponse.Error(response.code(), payload.message());
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Add the same idea in Kotlin:

    ```kotlin
    import io.koraframework.http.client.common.annotation.ResponseCodeMapper
    import io.koraframework.http.client.common.exception.HttpClientDecoderException
    import io.koraframework.http.client.common.response.HttpClientResponse
    import io.koraframework.http.client.common.response.HttpClientResponseMapper
    import io.koraframework.http.common.annotation.Path
    import io.koraframework.json.common.JsonReader
    import java.io.IOException

    @ResponseCodeMapper(code = ResponseCodeMapper.DEFAULT, mapper = MappedResponseErrorMapper::class)
    @ResponseCodeMapper(code = 200, mapper = MappedResponseSuccessMapper::class)
    @HttpRoute(method = HttpMethod.GET, path = "/data/mapping-by-code/{code}")
    fun getMappedByCode(@Path code: Int): MappedResponse

    sealed interface MappedResponse {

        @Json
        data class Payload(val message: String) : MappedResponse

        @Json
        data class Error(val code: Int, val message: String) : MappedResponse

        @Json
        data class ErrorPayload(val message: String)
    }

    @Component
    class MappedResponseSuccessMapper(
        private val jsonReader: JsonReader<MappedResponse.Payload>
    ) : HttpClientResponseMapper<MappedResponse> {

        @Throws(IOException::class, HttpClientDecoderException::class)
        override fun apply(response: HttpClientResponse): MappedResponse {
            response.body().asInputStream().use { input ->
                return requireNotNull(jsonReader.read(input.readAllBytes())) { "Empty success payload" }
            }
        }
    }

    @Component
    class MappedResponseErrorMapper(
        private val jsonReader: JsonReader<MappedResponse.ErrorPayload>
    ) : HttpClientResponseMapper<MappedResponse> {

        @Throws(IOException::class, HttpClientDecoderException::class)
        override fun apply(response: HttpClientResponse): MappedResponse {
            response.body().asInputStream().use { input ->
                val payload = requireNotNull(jsonReader.read(input.readAllBytes())) { "Empty error payload" }
                return MappedResponse.Error(response.code(), payload.message)
            }
        }
    }
    ```

This pattern is valuable because the status-code-specific transport logic stays close to the client method instead of leaking into every caller.

Notice a few details in this version of the example:

- both mappers take a `JsonReader` in their constructor, so both must be `@Component`
- the error JSON body contains only `message`
- the mapper gets `code` from the actual HTTP status line
- anything the mapper throws is wrapped into `HttpClientDecoderException` by the generated client

That keeps the server-side error format simpler while still letting the client expose a richer typed result.

!!! tip "Two outcomes without custom mappers"

    When you only need "success payload or error payload" and both are JSON, `Either<T, E>` is a lighter option: a method returning `Either<Payload, ErrorPayload>` maps every status code without
    throwing, and with `@Json` Kora builds both mappers itself. See [Either](../documentation/http-client.md#either).

## Client Interceptor { #client-interceptor }

For more on client interceptors, their scope, and execution order, see [HTTP Client interceptors](../documentation/http-client.md#interceptors).

The next advanced concept is a method-level interceptor.

Interceptors are useful when you want reusable behavior around a call, such as:

- logging
- metrics
- custom transport diagnostics

We keep this example intentionally small and apply it only to `getMappedByCode()`.

===! ":fontawesome-brands-java: `Java`"

    Add this inside `DataApiClient.java`:

    ```java
    import org.slf4j.Logger;
    import org.slf4j.LoggerFactory;
    import io.koraframework.http.client.common.interceptor.HttpClientInterceptor;
    import io.koraframework.http.client.common.request.HttpClientRequest;
    import io.koraframework.http.common.annotation.InterceptWith;

    @InterceptWith(MethodLoggingInterceptor.class)
    @ResponseCodeMapper(code = ResponseCodeMapper.DEFAULT, mapper = MappedResponseErrorMapper.class)
    @ResponseCodeMapper(code = 200, mapper = MappedResponseSuccessMapper.class)
    @HttpRoute(method = HttpMethod.GET, path = "/data/mapping-by-code/{code}")
    MappedResponse getMappedByCode(@Path int code);

    @Component
    final class MethodLoggingInterceptor implements HttpClientInterceptor {

        private static final Logger logger = LoggerFactory.getLogger(MethodLoggingInterceptor.class);

        @Override
        public HttpClientResponse processRequest(InterceptChain chain, HttpClientRequest request) throws Exception {
            logger.info("Advanced HTTP client interceptor invoked");
            return chain.process(request);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Add the same idea in Kotlin:

    ```kotlin
    import org.slf4j.LoggerFactory
    import io.koraframework.http.client.common.interceptor.HttpClientInterceptor
    import io.koraframework.http.client.common.request.HttpClientRequest
    import io.koraframework.http.common.annotation.InterceptWith

    @InterceptWith(MethodLoggingInterceptor::class)
    @ResponseCodeMapper(code = ResponseCodeMapper.DEFAULT, mapper = MappedResponseErrorMapper::class)
    @ResponseCodeMapper(code = 200, mapper = MappedResponseSuccessMapper::class)
    @HttpRoute(method = HttpMethod.GET, path = "/data/mapping-by-code/{code}")
    fun getMappedByCode(@Path code: Int): MappedResponse

    @Component
    class MethodLoggingInterceptor : HttpClientInterceptor {

        private val logger = LoggerFactory.getLogger(MethodLoggingInterceptor::class.java)

        override fun processRequest(chain: HttpClientInterceptor.InterceptChain, request: HttpClientRequest): HttpClientResponse {
            logger.info("Advanced HTTP client interceptor invoked")
            return chain.process(request)
        }
    }
    ```

This is a good local-before-global pattern: we add behavior only where the example actually needs it.

The signature is worth reading closely. `processRequest` receives the chain first and the request second, and it returns the response directly:

- to change the outgoing request, rebuild it with `request.toBuilder()` and pass the new instance to `chain.process(...)`
- to inspect or replace the response, work with the value returned by `chain.process(...)`
- to short-circuit the call, return a response without calling the chain at all

## API Key Authorization { #api-key }

For the broader HTTP client authorization model, see [Authorization](../documentation/http-client.md#authorization).

The advanced server guide protected `DataController` with a simple API-key check on the `Authorization` header.

At this point we already understand the advanced routes themselves, so now it makes sense to add one more reusable client concern: automatic authorization.

We do not want every caller to remember that header manually. That is exactly the kind of repeated transport rule that belongs in an interceptor.

Create the config contract:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/httpclient/client/ApiKeyAuthConfig.java"
    package io.koraframework.guide.httpclient.client;

    import io.koraframework.config.common.annotation.ConfigSource;

    @ConfigSource("auth.apiKey")
    public interface ApiKeyAuthConfig {

        String value();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/httpclient/client/ApiKeyAuthConfig.kt"
    package io.koraframework.guide.httpclient.client

    import io.koraframework.config.common.annotation.ConfigSource

    @ConfigSource("auth.apiKey")
    interface ApiKeyAuthConfig {

        fun value(): String
    }
    ```

Create the auth interceptor:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/httpclient/client/ApiKeyAuthInterceptor.java"
    package io.koraframework.guide.httpclient.client;

    import io.koraframework.common.annotation.Component;
    import io.koraframework.http.client.common.interceptor.HttpClientInterceptor;
    import io.koraframework.http.client.common.request.HttpClientRequest;
    import io.koraframework.http.client.common.response.HttpClientResponse;

    @Component
    public final class ApiKeyAuthInterceptor implements HttpClientInterceptor {

        private final ApiKeyAuthConfig config;

        public ApiKeyAuthInterceptor(ApiKeyAuthConfig config) {
            this.config = config;
        }

        @Override
        public HttpClientResponse processRequest(InterceptChain chain, HttpClientRequest request) throws Exception {
            var authorizedRequest = request.toBuilder()
                    .header("Authorization", this.config.value())
                    .build();
            return chain.process(authorizedRequest);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/httpclient/client/ApiKeyAuthInterceptor.kt"
    package io.koraframework.guide.httpclient.client

    import io.koraframework.common.annotation.Component
    import io.koraframework.http.client.common.interceptor.HttpClientInterceptor
    import io.koraframework.http.client.common.request.HttpClientRequest
    import io.koraframework.http.client.common.response.HttpClientResponse

    @Component
    class ApiKeyAuthInterceptor(
        private val config: ApiKeyAuthConfig
    ) : HttpClientInterceptor {

        override fun processRequest(chain: HttpClientInterceptor.InterceptChain, request: HttpClientRequest): HttpClientResponse {
            val authorizedRequest = request.toBuilder()
                .header("Authorization", config.value())
                .build()
            return chain.process(authorizedRequest)
        }
    }
    ```

Apply it to the whole client, so every route is authorized:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @InterceptWith(ApiKeyAuthInterceptor.class)
    @HttpClient("httpClient.dataApi")
    public interface DataApiClient {
        // routes stay the same
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @InterceptWith(ApiKeyAuthInterceptor::class)
    @HttpClient("httpClient.dataApi")
    interface DataApiClient {
        // routes stay the same
    }
    ```

Interceptors declared on the interface run for every route, and they run **before** any interceptor declared on an individual method. So on `getMappedByCode()` the order is `ApiKeyAuthInterceptor`
first, then `MethodLoggingInterceptor`, then the actual transport call.

This is a very common interceptor use case. Teams often use the same pattern for:

- `Authorization` headers
- cookies
- API keys
- other request metadata that should always be added automatically

Kora also ships ready interceptors for the standard schemes in `io.koraframework.http.client.common.interceptor`, so a custom class is only needed when the scheme is non-standard:

- `BasicAuthHttpClientInterceptor` — sends `Authorization: Basic ...` from a username and password, or from an `HttpClientTokenProvider`
- `BearerAuthHttpClientInterceptor` — sends `Authorization: Bearer ...` from a static token or an `HttpClientTokenProvider`
- `ApiKeyHttpClientInterceptor` — sends an API key as a header, a query parameter, or a cookie, chosen with `ApiKeyLocation.{HEADER,QUERY,COOKIE}`

Configure the API key:

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

    1. Local default API key value used by the guide (required, no default).
    2. Optional override of the API key from the `HTTP_ADVANCED_API_KEY` environment variable.

=== ":simple-yaml: `YAML`"

    ```yaml title="src/main/resources/application.yaml"
    auth:
      apiKey:
        value: ${HTTP_ADVANCED_API_KEY:MySecuredApiKey} #(1)!
    ```

    1. API key used by the guide (required, no default). Uses the shown default and allows `HTTP_ADVANCED_API_KEY` to override it.

Both applications can share the same local default, while `HTTP_ADVANCED_API_KEY` keeps the example environment-friendly. The client telemetry masks the `authorization` header by default, so the key
does not leak into logs.

## Imperative Client { #imperative-client }

Declarative `@HttpClient` interfaces are the usual application-level style, but Kora also exposes the base `HttpClient` component. This is useful when you need to build a request dynamically, apply an
interceptor manually, or debug what the declarative client hides from you.

There is no need to duplicate the client configuration for that. For every `@HttpClient` interface the processor generates a configuration interface named `$<InterfaceName>_Config` plus a module that
binds it to the configured path, and that interface is an ordinary graph component you can inject:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @ConfigMapper
    public interface $DataApiClient_Config extends DeclarativeHttpClientConfig {

        @Override
        HttpClientTelemetryConfig telemetry();

        HttpClientOperationConfig processForm();

        HttpClientOperationConfig processUpload();

        HttpClientOperationConfig processMappedRequest();

        HttpClientOperationConfig getMappedByCode();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @ConfigMapper
    interface `$DataApiClient_Config` : DeclarativeHttpClientConfig {

        override fun telemetry(): HttpClientTelemetryConfig

        fun processForm(): HttpClientOperationConfig

        fun processUpload(): HttpClientOperationConfig

        fun processMappedRequest(): HttpClientOperationConfig

        fun getMappedByCode(): HttpClientOperationConfig
    }
    ```

`DeclarativeHttpClientConfig` contributes `url()`, `requestTimeout()` and `telemetry()`, and each abstract client method contributes one `HttpClientOperationConfig` block. That is exactly why
`httpClient.dataApi.getMappedByCode.requestTimeout` from the configuration above is a valid key, and why default methods such as `sampleUpload()` never appear there.

Now add a small manual client. Notice that it does not put the authorization header directly on the request. It reuses the same auth interceptor through `this.httpClient.with(...)`.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/httpclient/client/ManualDataHttpClient.java"
    package io.koraframework.guide.httpclient.client;

    import java.nio.charset.StandardCharsets;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.http.client.common.HttpClient;
    import io.koraframework.http.client.common.request.HttpClientRequest;

    @Component
    public final class ManualDataHttpClient {

        private final HttpClient httpClient;
        private final $DataApiClient_Config dataApiConfig;
        private final ApiKeyAuthInterceptor apiKeyAuthInterceptor;

        public ManualDataHttpClient(HttpClient httpClient,
                                    $DataApiClient_Config dataApiConfig,
                                    ApiKeyAuthInterceptor apiKeyAuthInterceptor) {
            this.httpClient = httpClient;
            this.dataApiConfig = dataApiConfig;
            this.apiKeyAuthInterceptor = apiKeyAuthInterceptor;
        }

        public String pingManualHandler() {
            var request = HttpClientRequest.of("GET", this.dataApiConfig.url() + "/manual/data/ping")
                    .build();
            var response = this.httpClient.with(this.apiKeyAuthInterceptor).execute(request);
            if (response.code() != 200) {
                throw new IllegalStateException("Manual HTTP call failed with status " + response.code());
            }
            try (var body = response.body().asInputStream()) {
                return new String(body.readAllBytes(), StandardCharsets.UTF_8);
            } catch (Exception exception) {
                throw new IllegalStateException("Failed to read manual HTTP response body", exception);
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/httpclient/client/ManualDataHttpClient.kt"
    package io.koraframework.guide.httpclient.client

    import io.koraframework.common.annotation.Component
    import io.koraframework.http.client.common.HttpClient
    import io.koraframework.http.client.common.request.HttpClientRequest
    import java.nio.charset.StandardCharsets

    @Component
    class ManualDataHttpClient(
        private val httpClient: HttpClient,
        private val dataApiConfig: `$DataApiClient_Config`,
        private val apiKeyAuthInterceptor: ApiKeyAuthInterceptor
    ) {

        fun pingManualHandler(): String {
            val request = HttpClientRequest.of("GET", dataApiConfig.url() + "/manual/data/ping")
                .build()
            val response = httpClient.with(apiKeyAuthInterceptor).execute(request)
            if (response.code() != 200) {
                throw IllegalStateException("Manual HTTP call failed with status ${response.code()}")
            }
            response.body().asInputStream().use { body ->
                return String(body.readAllBytes(), StandardCharsets.UTF_8)
            }
        }
    }
    ```

This example is intentionally small, but it demonstrates four important details:

- `HttpClientRequest.of(method, uriTemplate)` returns an `HttpClientRequestBuilder`; there are also shorthands such as `HttpClientRequest.get(...)`, `.post(...)` and `.delete(...)`
- the builder exposes `pathParam`, `queryParam`, `header`, `body` and `requestTimeout`, and `request.toBuilder()` derives a modified copy of an existing request
- `HttpClient.with(...)` returns a client decorated with an interceptor, so authorization stays in one place
- `execute(...)` is the low-level synchronous operation behind every declarative client, and it returns a `HttpClientResponse` whose body must be read before it is closed

Unlike a declarative method, the imperative client does not translate status codes for you: nothing throws `HttpClientResponseException` here, so checking `response.code()` is your responsibility.

## Check Controller { #check-controller }

Now we wire the advanced client features into one aggregate scenario dedicated only to the `DataController` routes.

The base guide already has a user-oriented aggregate endpoint. We keep that separation:

- `testAllUserEndpoints()` belongs to the basic client guide
- `testAllDataEndpoints()` belongs to this advanced guide

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/httpclient/controller/ClientTestController.java"
    package io.koraframework.guide.httpclient.controller;

    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.httpclient.client.DataApiClient;
    import io.koraframework.guide.httpclient.client.ManualDataHttpClient;
    import io.koraframework.http.common.HttpMethod;
    import io.koraframework.http.common.annotation.HttpRoute;
    import io.koraframework.http.common.form.FormUrlEncoded;
    import io.koraframework.http.server.common.annotation.HttpController;
    import io.koraframework.json.common.annotation.Json;

    @Component
    @HttpController
    public final class ClientTestController {

        private final DataApiClient dataApiClient;
        private final ManualDataHttpClient manualDataHttpClient;

        public ClientTestController(DataApiClient dataApiClient, ManualDataHttpClient manualDataHttpClient) {
            this.dataApiClient = dataApiClient;
            this.manualDataHttpClient = manualDataHttpClient;
        }

        @HttpRoute(method = HttpMethod.POST, path = "/client/test-all-data-endpoints")
        @Json
        public TestResults testAllDataEndpoints() {
            try {
                var formResult = this.dataApiClient.processForm(form("name", "John"));
                boolean formProcessed = "Hello World, John".equals(formResult);

                var uploadResult = this.dataApiClient.sampleUpload();
                boolean uploadProcessed = uploadResult.fileCount() == 2;

                var mappedRequestResult = this.dataApiClient.processMappedRequest(new DataApiClient.PlainTextGreetingBody("Client Mapper"));
                boolean customRequestMapped = "Received mapped body: Hello Client Mapper".equals(mappedRequestResult);

                var mappedSuccess = this.dataApiClient.getMappedByCode(200);
                var mappedFailure = this.dataApiClient.getMappedByCode(404);
                boolean responseMapped = mappedSuccess instanceof DataApiClient.MappedResponse.Payload payload
                        && "Hello from response mapper".equals(payload.message())
                        && mappedFailure instanceof DataApiClient.MappedResponse.Error error
                        && error.code() == 404
                        && "Request failed with code 404".equals(error.message());

                var manualPingResult = this.manualDataHttpClient.pingManualHandler();
                boolean manualHttpClientCallProcessed = "manual-data-pong".equals(manualPingResult);

                boolean allTestsPassed = formProcessed
                        && uploadProcessed
                        && customRequestMapped
                        && responseMapped
                        && manualHttpClientCallProcessed;
                return new TestResults(
                        formProcessed,
                        uploadProcessed,
                        customRequestMapped,
                        responseMapped,
                        manualHttpClientCallProcessed,
                        allTestsPassed,
                        null);
            } catch (Exception exception) {
                return new TestResults(false, false, false, false, false, false, exception.getMessage());
            }
        }

        private static FormUrlEncoded form(String... keyValues) {
            FormUrlEncoded.FormPart[] parts = new FormUrlEncoded.FormPart[keyValues.length / 2];
            for (int i = 0; i < keyValues.length; i += 2) {
                parts[i / 2] = new FormUrlEncoded.FormPart(keyValues[i], keyValues[i + 1]);
            }
            return new FormUrlEncoded(parts);
        }

        @Json
        public record TestResults(
                boolean formProcessed,
                boolean uploadProcessed,
                boolean customRequestMapped,
                boolean responseMapped,
                boolean manualHttpClientCallProcessed,
                boolean allTestsPassed,
                String error) {}
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/httpclient/controller/ClientTestController.kt"
    package io.koraframework.guide.httpclient.controller

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.httpclient.client.DataApiClient
    import io.koraframework.guide.httpclient.client.ManualDataHttpClient
    import io.koraframework.http.common.HttpMethod
    import io.koraframework.http.common.annotation.HttpRoute
    import io.koraframework.http.common.form.FormUrlEncoded
    import io.koraframework.http.server.common.annotation.HttpController
    import io.koraframework.json.common.annotation.Json

    @Component
    @HttpController
    class ClientTestController(
        private val dataApiClient: DataApiClient,
        private val manualDataHttpClient: ManualDataHttpClient
    ) {
        @HttpRoute(method = HttpMethod.POST, path = "/client/test-all-data-endpoints")
        @Json
        fun testAllDataEndpoints(): TestResults {
            return try {
                val formResult = dataApiClient.processForm(form("name", "John"))
                val formProcessed = formResult == "Hello World, John"

                val uploadResult = dataApiClient.sampleUpload()
                val uploadProcessed = uploadResult.fileCount == 2

                val mappedRequestResult =
                    dataApiClient.processMappedRequest(DataApiClient.PlainTextGreetingBody("Client Mapper"))
                val customRequestMapped = mappedRequestResult == "Received mapped body: Hello Client Mapper"

                val mappedSuccess = dataApiClient.getMappedByCode(200)
                val mappedFailure = dataApiClient.getMappedByCode(404)
                val responseMapped =
                    mappedSuccess is DataApiClient.MappedResponse.Payload &&
                            mappedSuccess.message == "Hello from response mapper" &&
                            mappedFailure is DataApiClient.MappedResponse.Error &&
                            mappedFailure.code == 404 &&
                            mappedFailure.message == "Request failed with code 404"

                val manualPingResult = manualDataHttpClient.pingManualHandler()
                val manualHttpClientCallProcessed = manualPingResult == "manual-data-pong"

                val allTestsPassed = formProcessed &&
                        uploadProcessed &&
                        customRequestMapped &&
                        responseMapped &&
                        manualHttpClientCallProcessed
                TestResults(
                    formProcessed,
                    uploadProcessed,
                    customRequestMapped,
                    responseMapped,
                    manualHttpClientCallProcessed,
                    allTestsPassed,
                    null
                )
            } catch (e: Exception) {
                TestResults(false, false, false, false, false, false, e.message)
            }
        }

        private fun form(vararg keyValues: String): FormUrlEncoded {
            val parts = Array(keyValues.size / 2) { index ->
                FormUrlEncoded.FormPart(keyValues[index * 2], keyValues[index * 2 + 1])
            }
            return FormUrlEncoded(*parts)
        }

        @Json
        data class TestResults(
            val formProcessed: Boolean,
            val uploadProcessed: Boolean,
            val customRequestMapped: Boolean,
            val responseMapped: Boolean,
            val manualHttpClientCallProcessed: Boolean,
            val allTestsPassed: Boolean,
            val error: String?
        )
    }
    ```

## Check Application { #check-app }

Run the advanced server and the advanced client in separate terminals.

### Terminal 1: Server { #terminal-1-server }

```bash
./gradlew clean classes
./gradlew run
```

The advanced server app should listen on `http://localhost:8080`.

### Terminal 2: Client { #terminal-2-client }

```bash
./gradlew clean classes
./gradlew run
```

The advanced client app should listen on `http://localhost:8081`.

### Client Scenario { #client-scenario }

```bash
curl -X POST http://localhost:8081/client/test-all-data-endpoints
```

Expected result: a JSON object where `allTestsPassed` is `true`.

The same scenario can be automated exactly like in the basic guide: start the advanced server application in a container, point `DATA_API_URL` at it with `KoraAppTestConfigModifier`, and inject
`DataApiClient` and `ManualDataHttpClient` with `@TestComponent`. See [Container Test](http-client.md#container-test).

## Best Practices { #best-practices }

- Keep the basic HTTP client guide focused on the simplest JSON-first path, and move transport-heavy topics into an advanced follow-up.
- Use separate client interfaces for different remote API areas when that improves readability.
- Reach for `HttpClientRequestMapper` only when the built-in mapping styles are not enough.
- Use `@ResponseCodeMapper` when status-code-aware decoding is part of the contract, and `Either<T, E>` when a plain success/error split is enough.
- Use interceptors for repeated transport behavior like logging or authorization instead of repeating headers and boilerplate manually.
- Prefer the built-in `BasicAuthHttpClientInterceptor`, `BearerAuthHttpClientInterceptor` and `ApiKeyHttpClientInterceptor` for standard schemes.
- Keep the imperative `HttpClient` for genuinely dynamic requests, and remember it does not raise `HttpClientResponseException` on its own.

## Summary { #summary }

You extended the basic HTTP client application with:

- a separate `DataApiClient`
- form and multipart request support
- a custom request mapper
- response-code-aware decoding
- a method-level interceptor
- reusable API-key authorization
- an imperative call that reuses the generated client configuration and the auth interceptor

The result mirrors the spirit of `http-server-advanced.md`: one advanced transport concept at a time, each introduced only after the simpler path is already clear.

## Key Concepts { #key-concepts }

- `FormUrlEncoded` and `FormMultipart` are first-class client-side body types in Kora and need no custom mapper
- `HttpClientRequestMapper<T>` turns a type into an HTTP request body through `HttpBodyOutput apply(T value)`
- `@ResponseCodeMapper` lets different status codes decode into different variants of one result type, with `ResponseCodeMapper.DEFAULT` as the fallback
- `HttpClientInterceptor.processRequest(chain, request)` is synchronous, and interface-level interceptors run before method-level ones
- mappers and interceptors referenced by `@Mapping` and `@InterceptWith` are constructor arguments of the generated client, so they must be graph components
- `$<Client>_Config` is generated for every declarative client and can be injected wherever the client configuration is needed

## Troubleshooting { #troubleshooting }

**Protected calls return 403:**

- Check that the server and client use the same API key value.
- Check the `HTTP_ADVANCED_API_KEY` environment variable on both applications.
- Remember that the environment variable overrides the local default from `application.conf`.

**Form or multipart requests do not work:**

- Make sure the advanced server app is running, not only the basic server app.
- Check that `DataController` is exposed on the target server.
- Do not add `@Json` to a `FormUrlEncoded` or `FormMultipart` parameter — those types already have their own request mappers.

**The build fails with `No component found for dependency:` and a mapper or interceptor type:**

- Add `@Component` to the class referenced by `@Mapping` or `@InterceptWith`. The generated client receives both as constructor arguments, so they must exist in the graph even when they have no
  dependencies of their own.

**Custom request mapper does not run:**

- Make sure the parameter uses `@Mapping(...)`.
- Make sure the mapper implements `HttpClientRequestMapper<T>` for exactly the parameter type.

**Response-code mapping does not behave as expected:**

- Check the `@ResponseCodeMapper` entries carefully.
- Remember that `ResponseCodeMapper.DEFAULT` is the fallback for all unlisted codes, and that without a `DEFAULT` entry an unlisted code raises `HttpClientResponseException`.
- Make sure the server route returns the JSON shape your mapper expects for each branch.
- An exception thrown inside a mapper surfaces as `HttpClientDecoderException`, so check the cause.

**Interceptor logging does not appear:**

- Check `@InterceptWith(...)` on the specific client method or on the interface.
- Make sure the interceptor class implements `HttpClientInterceptor` and is annotated with `@Component`.

**The imperative call hangs or returns an empty body:**

- Read the body before the response is closed; `HttpClientResponse` is `Closeable` and the body is not buffered for you.
- Set a timeout with `HttpClientRequest.of(...).requestTimeout(...)` when the remote service may be slow.

## What's Next? { #whats-next }

- [OpenAPI HTTP Server](openapi-http-server.md) if you have not completed the contract-first server path yet.
- [OpenAPI HTTP Client](openapi-http-client.md) after OpenAPI HTTP Server, to see how contract generation models similar transport behavior.
- [Resilient Patterns](resilient.md) to protect advanced outbound calls with retry, timeout, circuit breaker, and fallback.
- [Observability](observability.md) to trace interceptors, manual `HttpClient` calls, and mapped responses.

## Help { #help }

If you get stuck:

- compare with [Kora Java HTTP Client Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-http-client-advanced-app) and [Kora Kotlin HTTP Client Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-http-client-advanced-app)
- revisit [HTTP Client](http-client.md) for the basic declarative client shape
- revisit [HTTP Server Advanced](http-server-advanced.md) for the server endpoints this client calls
- check the [HTTP Client documentation](../documentation/http-client.md)
