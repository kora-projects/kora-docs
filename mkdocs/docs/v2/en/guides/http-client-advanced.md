---
search:
  exclude: true
title: HTTP Client Advanced Guide
summary: Extend the basic HTTP client guide with form and multipart bodies, custom request mapping, response-code-aware decoding, method interceptors, and API-key authorization
tags: http-client, advanced, form, multipart, interceptor, mapping, auth
---

# Advanced HTTP Client Guide { #advanced-http-client-guide }

This guide introduces advanced declarative HTTP client patterns in Kora. It covers how clients call form, multipart, and helper transport routes, how custom body mappers shape unusual request and
response payloads, and how typed response variants represent different HTTP statuses. You will also see how method-level and client-level interceptors add cross-cutting behavior such as API-key
authorization.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java HTTP Client Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-http-client-advanced-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin HTTP Client Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-http-client-advanced-app).

## What You'll Build { #youll-build }

You will extend the client application with:

- a dedicated `DataApiClient`
- `FormUrlEncoded` and `FormMultipart` requests
- a custom `HttpClientRequestMapper`
- response-code-aware decoding with `@ResponseCodeMapper`
- a method-level `HttpClientInterceptor`
- a client-wide API-key auth interceptor
- a dedicated aggregate endpoint in `ClientTestController` that exercises the advanced data routes

## What You'll Need { #youll-need }

- JDK 17 or later
- Gradle 7+
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

This guide uses interceptors for both method-level behavior and reusable client-level authorization.

### Targeted Changes { #targeted-changes }

Advanced client features can easily spread through an application if the generated client is used everywhere directly. This guide keeps a service wrapper around the client so form calls, multipart
calls, custom decoding, and authorization remain near the transport boundary. The rest of the application can work with clearer methods and typed results.

The practical flow is:

1. add a dedicated client for the advanced data routes
2. call form and multipart endpoints declaratively
3. add a custom request mapper for one payload shape
4. decode response statuses into typed results
5. attach logging and API-key authorization with interceptors

## New HTTP Client { #new-http-client }

The first advanced client concept is still very concrete: call the extra routes introduced by `DataController`.

We keep these calls in a separate `DataApiClient` so the transport-heavy examples do not clutter the simpler `UserApiClient`.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/httpclient/client/DataApiClient.java"
    package ru.tinkoff.kora.guide.httpclient.client;

    import java.nio.charset.StandardCharsets;
    import java.util.List;
    import ru.tinkoff.kora.http.client.common.annotation.HttpClient;
    import ru.tinkoff.kora.http.common.HttpMethod;
    import ru.tinkoff.kora.http.common.annotation.HttpRoute;
    import ru.tinkoff.kora.http.common.form.FormMultipart;
    import ru.tinkoff.kora.http.common.form.FormUrlEncoded;
    import ru.tinkoff.kora.json.common.annotation.Json;

    @HttpClient(configPath = "httpClient.dataApi")
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

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/httpclient/client/DataApiClient.kt"
    package ru.tinkoff.kora.guide.httpclient.client

    import java.nio.charset.StandardCharsets
    import ru.tinkoff.kora.http.client.common.annotation.HttpClient
    import ru.tinkoff.kora.http.common.HttpMethod
    import ru.tinkoff.kora.http.common.annotation.HttpRoute
    import ru.tinkoff.kora.http.common.form.FormMultipart
    import ru.tinkoff.kora.http.common.form.FormUrlEncoded
    import ru.tinkoff.kora.json.common.annotation.Json

    @HttpClient(configPath = "httpClient.dataApi")
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
                        FormMultipart.file("field2", "example1.txt", "text/plain", "some file content".toByteArray(StandardCharsets.UTF_8))
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

## Parameter Mapper { #parameter-mapper }

For more on client request-body mappers, see [HTTP Client request body](../documentation/http-client.md#request-body).

Sometimes a request body should not use the normal JSON or form mapping flow. A remote endpoint may expect a very specific text or binary representation, and you still want to model the input as your
own type.

That is what `HttpClientRequestMapper<T>` is for.

In this guide we use a small example:

- the method accepts `PlainTextGreetingBody`
- a mapper turns it into a plain-text HTTP body
- the advanced server echoes that mapped text back

===! ":fontawesome-brands-java: `Java`"

    Add these pieces inside `DataApiClient.java`:

    ```java
    import ru.tinkoff.kora.common.Context;
    import ru.tinkoff.kora.common.Mapping;
    import ru.tinkoff.kora.http.client.common.request.HttpClientRequestMapper;
    import ru.tinkoff.kora.http.common.body.HttpBody;
    import ru.tinkoff.kora.http.common.body.HttpBodyOutput;

    record PlainTextGreetingBody(String name) {}

    final class GreetingRequestMapper implements HttpClientRequestMapper<PlainTextGreetingBody> {

        @Override
        public HttpBodyOutput apply(Context ctx, PlainTextGreetingBody value) {
            return HttpBody.plaintext("Hello " + value.name());
        }
    }

    @HttpRoute(method = HttpMethod.POST, path = "/data/mapping-request")
    String processMappedRequest(@Mapping(GreetingRequestMapper.class) PlainTextGreetingBody body);
    ```

=== ":simple-kotlin: `Kotlin`"

    Add the same idea in `DataApiClient.kt`:

    ```kotlin
    import ru.tinkoff.kora.common.Context
    import ru.tinkoff.kora.common.Mapping
    import ru.tinkoff.kora.http.client.common.request.HttpClientRequestMapper
    import ru.tinkoff.kora.http.common.body.HttpBody
    import ru.tinkoff.kora.http.common.body.HttpBodyOutput

    data class PlainTextGreetingBody(val name: String)

    class GreetingRequestMapper : HttpClientRequestMapper<PlainTextGreetingBody> {
        override fun apply(ctx: Context, value: PlainTextGreetingBody): HttpBodyOutput {
            return HttpBody.plaintext("Hello ${value.name}")
        }
    }

    @HttpRoute(method = HttpMethod.POST, path = "/data/mapping-request")
    fun processMappedRequest(@Mapping(GreetingRequestMapper::class) body: PlainTextGreetingBody): String
    ```

This is the client-side analogue of the request mappers we introduced in the advanced server guide: a typed object becomes a transport representation in one clear place.

## Response Code Mapping { #response-code-mapping }

Default client behavior often treats a response as either:

- a successful body
- or an exception

That is enough for many APIs. But sometimes the contract intentionally says:

- `200` returns one JSON shape
- non-`200` responses return another JSON shape

That is where `@ResponseCodeMapper` becomes useful.

In this guide, `GET /data/mapping-by-code/{code}` behaves like this:

- `200` returns `{"message":"Hello from response mapper"}`
- other codes return `{"message":"Request failed with code <status>"}` through the shared server-side `ErrorResponse`

We model that as one sealed result type.

===! ":fontawesome-brands-java: `Java`"

    Add this inside `DataApiClient.java`:

    ```java
    import java.io.IOException;
    import ru.tinkoff.kora.guide.httpclient.client.DataApiClient.MappedResponse.Error;
    import ru.tinkoff.kora.guide.httpclient.client.DataApiClient.MappedResponse.Payload;
    import ru.tinkoff.kora.http.client.common.HttpClientDecoderException;
    import ru.tinkoff.kora.http.client.common.annotation.ResponseCodeMapper;
    import ru.tinkoff.kora.http.client.common.response.HttpClientResponse;
    import ru.tinkoff.kora.http.client.common.response.HttpClientResponseMapper;
    import ru.tinkoff.kora.http.common.annotation.Path;
    import ru.tinkoff.kora.json.common.JsonReader;

    sealed interface MappedResponse permits Payload, Error {

        @Json
        record Payload(String message) implements MappedResponse {}

        @Json
        record Error(int code, String message) implements MappedResponse {}

        @Json
        record ErrorPayload(String message) {}
    }

    final class MappedResponseSuccessMapper implements HttpClientResponseMapper<MappedResponse> {

        private final JsonReader<Payload> jsonReader;

        public MappedResponseSuccessMapper(JsonReader<Payload> jsonReader) {
            this.jsonReader = jsonReader;
        }

        @Override
        public MappedResponse apply(HttpClientResponse response) throws IOException, HttpClientDecoderException {
            try (var is = response.body().asInputStream()) {
                return this.jsonReader.read(is.readAllBytes());
            }
        }
    }

    final class MappedResponseErrorMapper implements HttpClientResponseMapper<MappedResponse> {

        private final JsonReader<MappedResponse.ErrorPayload> jsonReader;

        public MappedResponseErrorMapper(JsonReader<MappedResponse.ErrorPayload> jsonReader) {
            this.jsonReader = jsonReader;
        }

        @Override
        public MappedResponse apply(HttpClientResponse response) throws IOException, HttpClientDecoderException {
            try (var is = response.body().asInputStream()) {
                var payload = this.jsonReader.read(is.readAllBytes());
                return new Error(response.code(), payload.message());
            }
        }
    }

    @ResponseCodeMapper(code = ResponseCodeMapper.DEFAULT, mapper = MappedResponseErrorMapper.class)
    @ResponseCodeMapper(code = 200, mapper = MappedResponseSuccessMapper.class)
    @HttpRoute(method = HttpMethod.GET, path = "/data/mapping-by-code/{code}")
    MappedResponse getMappedByCode(@Path int code);
    ```

=== ":simple-kotlin: `Kotlin`"

    Add the same idea in Kotlin:

    ```kotlin
    import java.io.IOException
    import ru.tinkoff.kora.http.client.common.HttpClientDecoderException
    import ru.tinkoff.kora.http.client.common.annotation.ResponseCodeMapper
    import ru.tinkoff.kora.http.client.common.response.HttpClientResponse
    import ru.tinkoff.kora.http.client.common.response.HttpClientResponseMapper
    import ru.tinkoff.kora.http.common.annotation.Path
    import ru.tinkoff.kora.json.common.JsonReader

    sealed interface MappedResponse {

        @Json
        data class Payload(val message: String) : MappedResponse

        @Json
        data class Error(val code: Int, val message: String) : MappedResponse

        @Json
        data class ErrorPayload(val message: String)
    }

    class MappedResponseSuccessMapper(
        private val jsonReader: JsonReader<MappedResponse.Payload>
    ) : HttpClientResponseMapper<MappedResponse> {

        override fun apply(response: HttpClientResponse): MappedResponse {
            response.body().asInputStream().use { input ->
                return jsonReader.read(input.readAllBytes())
            }
        }
    }

    class MappedResponseErrorMapper(
        private val jsonReader: JsonReader<MappedResponse.ErrorPayload>
    ) : HttpClientResponseMapper<MappedResponse> {

        override fun apply(response: HttpClientResponse): MappedResponse {
            response.body().asInputStream().use { input ->
                val payload = jsonReader.read(input.readAllBytes())
                return MappedResponse.Error(response.code(), payload.message)
            }
        }
    }

    @ResponseCodeMapper(code = ResponseCodeMapper.DEFAULT, mapper = MappedResponseErrorMapper::class)
    @ResponseCodeMapper(code = 200, mapper = MappedResponseSuccessMapper::class)
    @HttpRoute(method = HttpMethod.GET, path = "/data/mapping-by-code/{code}")
    fun getMappedByCode(@Path code: Int): MappedResponse
    ```

This pattern is valuable because the status-code-specific transport logic stays close to the client method instead of leaking into every caller.

Notice one small but important detail in this version of the example:

- the error JSON body contains only `message`
- the mapper gets `code` from the actual HTTP status line

That keeps the server-side error format simpler while still letting the client expose a richer typed result.

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
    import java.util.concurrent.CompletionStage;
    import org.slf4j.Logger;
    import org.slf4j.LoggerFactory;
    import ru.tinkoff.kora.http.client.common.interceptor.HttpClientInterceptor;
    import ru.tinkoff.kora.http.client.common.request.HttpClientRequest;
    import ru.tinkoff.kora.http.client.common.response.HttpClientResponse;
    import ru.tinkoff.kora.http.common.annotation.InterceptWith;

    final class MethodLoggingInterceptor implements HttpClientInterceptor {

        private static final Logger logger = LoggerFactory.getLogger(MethodLoggingInterceptor.class);

        @Override
        public CompletionStage<HttpClientResponse> processRequest(Context ctx, InterceptChain chain, HttpClientRequest request)
                throws Exception {
            logger.info("Advanced HTTP client interceptor invoked");
            return chain.process(ctx, request);
        }
    }

    @InterceptWith(MethodLoggingInterceptor.class)
    @ResponseCodeMapper(code = ResponseCodeMapper.DEFAULT, mapper = MappedResponseErrorMapper.class)
    @ResponseCodeMapper(code = 200, mapper = MappedResponseSuccessMapper.class)
    @HttpRoute(method = HttpMethod.GET, path = "/data/mapping-by-code/{code}")
    MappedResponse getMappedByCode(@Path int code);
    ```

=== ":simple-kotlin: `Kotlin`"

    Add the same idea in Kotlin:

    ```kotlin
    import java.util.concurrent.CompletionStage
    import org.slf4j.LoggerFactory
    import ru.tinkoff.kora.http.client.common.interceptor.HttpClientInterceptor
    import ru.tinkoff.kora.http.client.common.request.HttpClientRequest
    import ru.tinkoff.kora.http.client.common.response.HttpClientResponse
    import ru.tinkoff.kora.http.common.annotation.InterceptWith

    class MethodLoggingInterceptor : HttpClientInterceptor {

        companion object {
            private val logger = LoggerFactory.getLogger(MethodLoggingInterceptor::class.java)
        }

        override fun processRequest(
            ctx: Context,
            chain: HttpClientInterceptor.InterceptChain,
            request: HttpClientRequest
        ): CompletionStage<HttpClientResponse> {
            logger.info("Advanced HTTP client interceptor invoked")
            return chain.process(ctx, request)
        }
    }

    @InterceptWith(MethodLoggingInterceptor::class)
    @ResponseCodeMapper(code = ResponseCodeMapper.DEFAULT, mapper = MappedResponseErrorMapper::class)
    @ResponseCodeMapper(code = 200, mapper = MappedResponseSuccessMapper::class)
    @HttpRoute(method = HttpMethod.GET, path = "/data/mapping-by-code/{code}")
    fun getMappedByCode(@Path code: Int): MappedResponse
    ```

This is a good local-before-global pattern: we add behavior only where the example actually needs it.

## API Key Authorization { #api-key }

For the broader HTTP client authorization model, see [Authorization](../documentation/http-client.md#authorization).

The advanced server guide protected `DataController` with a simple API-key check on the `Authorization` header.

At this point we already understand the advanced routes themselves, so now it makes sense to add one more reusable client concern: automatic authorization.

We do not want every caller to remember that header manually. That is exactly the kind of repeated transport rule that belongs in an interceptor.

Create the config contract:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/httpclient/client/ApiKeyAuthConfig.java"
    package ru.tinkoff.kora.guide.httpclient.client;

    import ru.tinkoff.kora.config.common.annotation.ConfigSource;

    @ConfigSource("auth.apiKey")
    public interface ApiKeyAuthConfig {
        String value();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/httpclient/client/ApiKeyAuthConfig.kt"
    package ru.tinkoff.kora.guide.httpclient.client

    import ru.tinkoff.kora.config.common.annotation.ConfigSource

    @ConfigSource("auth.apiKey")
    interface ApiKeyAuthConfig {
        fun value(): String
    }
    ```

Create the auth interceptor:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/httpclient/client/ApiKeyAuthInterceptor.java"
    package ru.tinkoff.kora.guide.httpclient.client;

    import java.util.concurrent.CompletionStage;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.Context;
    import ru.tinkoff.kora.http.client.common.interceptor.HttpClientInterceptor;
    import ru.tinkoff.kora.http.client.common.request.HttpClientRequest;
    import ru.tinkoff.kora.http.client.common.response.HttpClientResponse;

    @Component
    public final class ApiKeyAuthInterceptor implements HttpClientInterceptor {

        private final ApiKeyAuthConfig config;

        public ApiKeyAuthInterceptor(ApiKeyAuthConfig config) {
            this.config = config;
        }

        @Override
        public CompletionStage<HttpClientResponse> processRequest(Context ctx, InterceptChain chain, HttpClientRequest request)
                throws Exception {
            var authorizedRequest = request.toBuilder()
                    .header("Authorization", this.config.value())
                    .build();
            return chain.process(ctx, authorizedRequest);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/httpclient/client/ApiKeyAuthInterceptor.kt"
    package ru.tinkoff.kora.guide.httpclient.client

    import java.util.concurrent.CompletionStage
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.Context
    import ru.tinkoff.kora.http.client.common.interceptor.HttpClientInterceptor
    import ru.tinkoff.kora.http.client.common.request.HttpClientRequest
    import ru.tinkoff.kora.http.client.common.response.HttpClientResponse

    @Component
    class ApiKeyAuthInterceptor(
        private val config: ApiKeyAuthConfig
    ) : HttpClientInterceptor {

        override fun processRequest(
            ctx: Context,
            chain: HttpClientInterceptor.InterceptChain,
            request: HttpClientRequest
        ): CompletionStage<HttpClientResponse> {
            val authorizedRequest = request.toBuilder()
                .header("Authorization", config.value())
                .build()
            return chain.process(ctx, authorizedRequest)
        }
    }
    ```

Apply it to DataApiClient:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @InterceptWith(ApiKeyAuthInterceptor.class)
    @HttpClient(configPath = "httpClient.dataApi")
    public interface DataApiClient {
        // routes stay the same
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @InterceptWith(ApiKeyAuthInterceptor::class)
    @HttpClient(configPath = "httpClient.dataApi")
    interface DataApiClient {
        // routes stay the same
    }
    ```

This is a very common interceptor use case. Teams often use the same pattern for:

- `Authorization` headers
- cookies
- API keys
- other request metadata that should always be added automatically

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

    1. Configured value consumed by the guide component.
    2. Configured value consumed by the guide component. Optional override from `HTTP_ADVANCED_API_KEY`.

=== ":simple-yaml: `YAML`"

    ```yaml title="src/main/resources/application.yaml"
    auth:
      apiKey:
        value: ${?HTTP_ADVANCED_API_KEY:"MySecuredApiKey"} #(1)!
    ```

    1. Configured value consumed by the guide component. Uses the shown default and allows `HTTP_ADVANCED_API_KEY` to override it.

Both applications can share the same local default, while `HTTP_ADVANCED_API_KEY` keeps the example environment-friendly.

## Imperative Client { #imperative-client }

Declarative `@HttpClient` interfaces are the usual application-level style, but Kora also exposes the base `HttpClient` component. This is useful when you need to build a request dynamically, apply an
interceptor manually, or debug what the declarative client hides from you.

First add a small config contract for the same remote base URL used by `DataApiClient`:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/httpclient/client/dataApiConfig.java"
    package ru.tinkoff.kora.guide.httpclient.client;

    import ru.tinkoff.kora.config.common.annotation.ConfigSource;

    @ConfigSource("httpClient.dataApi")
    public interface dataApiConfig {
        String url();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/httpclient/client/dataApiConfig.kt"
    package ru.tinkoff.kora.guide.httpclient.client

    import ru.tinkoff.kora.config.common.annotation.ConfigSource

    @ConfigSource("httpClient.dataApi")
    interface dataApiConfig {
        fun url(): String
    }
    ```

Now add a small manual client. Notice that it does not put the authorization header directly on the request. It reuses the same auth interceptor through `this.httpClient.with(...)`.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/httpclient/client/ManualDataHttpClient.java"
    package ru.tinkoff.kora.guide.httpclient.client;

    import java.nio.charset.StandardCharsets;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.http.client.common.HttpClient;
    import ru.tinkoff.kora.http.client.common.request.HttpClientRequest;

    @Component
    public final class ManualDataHttpClient {

        private final HttpClient httpClient;
        private final dataApiConfig dataApiConfig;
        private final ApiKeyAuthInterceptor apiKeyAuthInterceptor;

        public ManualDataHttpClient(
                HttpClient httpClient,
                dataApiConfig dataApiConfig,
                ApiKeyAuthInterceptor apiKeyAuthInterceptor) {
            this.httpClient = httpClient;
            this.dataApiConfig = dataApiConfig;
            this.apiKeyAuthInterceptor = apiKeyAuthInterceptor;
        }

        public String pingManualHandler() {
            var request = HttpClientRequest.of("GET", this.dataApiConfig.url() + "/manual/data/ping")
                    .build();
            var response = this.httpClient.with(this.apiKeyAuthInterceptor)
                    .execute(request)
                    .toCompletableFuture()
                    .join();
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

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/httpclient/client/ManualDataHttpClient.kt"
    package ru.tinkoff.kora.guide.httpclient.client

    import java.nio.charset.StandardCharsets
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.http.client.common.HttpClient
    import ru.tinkoff.kora.http.client.common.request.HttpClientRequest

    @Component
    class ManualDataHttpClient(
        private val httpClient: HttpClient,
        private val dataApiConfig: dataApiConfig,
        private val apiKeyAuthInterceptor: ApiKeyAuthInterceptor
    ) {

        fun pingManualHandler(): String {
            val request = HttpClientRequest.of("GET", dataApiConfig.url() + "/manual/data/ping")
                .build()
            val response = httpClient.with(apiKeyAuthInterceptor)
                .execute(request)
                .toCompletableFuture()
                .join()
            if (response.code() != 200) {
                throw IllegalStateException("Manual HTTP call failed with status ${response.code()}")
            }
            response.body().asInputStream().use { body ->
                return String(body.readAllBytes(), StandardCharsets.UTF_8)
            }
        }
    }
    ```

This example is intentionally small, but it demonstrates three important details:

- `HttpClientRequest.of(...)` builds the outgoing request explicitly
- `HttpClient.with(...)` returns a client decorated with an interceptor
- `execute(...)` is the low-level operation behind higher-level declarative clients

After compilation, the generated application graph shows that Kora wires the base client, config, and interceptor into the manual client:

===! ":fontawesome-brands-java: `Java`"

    ```java
    component57 = graphDraw.addNode0(_type_of_component57, new Class<?>[]{}, g -> new ManualDataHttpClient(
          g.get(ApplicationGraph.holder0.component29),
          g.get(ApplicationGraph.holder0.component36),
          g.get(ApplicationGraph.holder0.component42)
        ), List.of(), component29, component36, component42);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    component62 = graphDraw.addNode0(map["component62"],
      { ManualDataHttpClient(
        it.get(holder0.component34),
        it.get(holder0.component41),
        it.get(holder0.component47)
      ) },
      component34, component41, component47
    )
    ```

That generated graph is a useful source of truth when you want to confirm which `HttpClient` implementation and interceptors are actually injected.

## Check Controller { #check-controller }

Now we wire the advanced client features into one aggregate scenario dedicated only to the `DataController` routes.

The base guide already has a user-oriented aggregate endpoint. We keep that separation:

- `testAllUserEndpoints()` belongs to the basic client guide
- `testAllDataEndpoints()` belongs to this advanced guide

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/httpclient/controller/ClientTestController.java"
    package ru.tinkoff.kora.guide.httpclient.controller;

    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.httpclient.client.DataApiClient;
    import ru.tinkoff.kora.guide.httpclient.client.ManualDataHttpClient;
    import ru.tinkoff.kora.http.common.HttpMethod;
    import ru.tinkoff.kora.http.common.annotation.HttpRoute;
    import ru.tinkoff.kora.http.common.form.FormUrlEncoded;
    import ru.tinkoff.kora.http.server.common.annotation.HttpController;
    import ru.tinkoff.kora.json.common.annotation.Json;

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

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/httpclient/controller/ClientTestController.kt"
    package ru.tinkoff.kora.guide.httpclient.controller

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.httpclient.client.DataApiClient
    import ru.tinkoff.kora.http.common.HttpMethod
    import ru.tinkoff.kora.http.common.annotation.HttpRoute
    import ru.tinkoff.kora.http.common.form.FormUrlEncoded
    import ru.tinkoff.kora.http.server.common.annotation.HttpController
    import ru.tinkoff.kora.json.common.annotation.Json

    @Component
    @HttpController
    class ClientTestController(
        private val dataApiClient: DataApiClient
    ) {
        @HttpRoute(method = HttpMethod.POST, path = "/client/test-all-data-endpoints")
        @Json
        fun testAllDataEndpoints(): TestResults {
            return try {
                val formResult = dataApiClient.processForm(form("name", "John"))
                val formProcessed = formResult == "Hello World, John"

                val uploadResult = dataApiClient.sampleUpload()
                val uploadProcessed = uploadResult.fileCount == 2

                val mappedRequestResult = dataApiClient.processMappedRequest(DataApiClient.PlainTextGreetingBody("Client Mapper"))
                val customRequestMapped = mappedRequestResult == "Received mapped body: Hello Client Mapper"

                val mappedSuccess = dataApiClient.getMappedByCode(200)
                val mappedFailure = dataApiClient.getMappedByCode(404)
                val responseMapped =
                    mappedSuccess is DataApiClient.MappedResponse.Payload &&
                        mappedSuccess.message == "Hello from response mapper" &&
                        mappedFailure is DataApiClient.MappedResponse.Error &&
                        mappedFailure.code == 404 &&
                        mappedFailure.message == "Request failed with code 404"

                val allTestsPassed = formProcessed && uploadProcessed && customRequestMapped && responseMapped
                TestResults(
                    formProcessed,
                    uploadProcessed,
                    customRequestMapped,
                    responseMapped,
                    allTestsPassed,
                    null
                )
            } catch (e: Exception) {
                TestResults(false, false, false, false, false, e.message)
            }
        }

        private fun form(vararg keyValues: String): FormUrlEncoded {
            val parts = Array(keyValues.size / 2) { index ->
                FormUrlEncoded.FormPart(keyValues[index * 2], keyValues[index * 2 + 1])
            }
            return FormUrlEncoded(parts)
        }

        @Json
        data class TestResults(
            val formProcessed: Boolean,
            val uploadProcessed: Boolean,
            val customRequestMapped: Boolean,
            val responseMapped: Boolean,
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

## Best Practices { #best-practices }

- Keep the basic HTTP client guide focused on the simplest JSON-first path, and move transport-heavy topics into an advanced follow-up.
- Use separate client interfaces for different remote API areas when that improves readability.
- Reach for `HttpClientRequestMapper` only when the built-in mapping styles are not enough.
- Use `@ResponseCodeMapper` when status-code-aware decoding is part of the contract.
- Use interceptors for repeated transport behavior like logging or authorization instead of repeating headers and boilerplate manually.

## Summary { #summary }

You extended the basic HTTP client application with:

- a separate `DataApiClient`
- form and multipart request support
- a custom request mapper
- response-code-aware decoding
- a method-level interceptor
- reusable API-key authorization

The result mirrors the spirit of `http-server-advanced.md`: one advanced transport concept at a time, each introduced only after the simpler path is already clear.

## Key Concepts { #key-concepts }

- `FormUrlEncoded` and `FormMultipart` are first-class client-side body types in Kora
- `HttpClientRequestMapper<T>` lets you control how a type becomes an HTTP request body
- `@ResponseCodeMapper` lets different status codes decode into different variants of one result type
- `HttpClientInterceptor` is a good place both for local logging and shared authorization behavior

## Troubleshooting { #troubleshooting }

**Protected calls return 403:**

- Check that the server and client use the same API key value.
- Check the `HTTP_ADVANCED_API_KEY` environment variable on both applications.
- Remember that the environment variable overrides the local default from `application.conf`.

**Form or multipart requests do not work:**

- Make sure the advanced server app is running, not only the basic server app.
- Check that `DataController` is exposed on the target server.

**Custom request mapper does not run:**

- Make sure the parameter uses `@Mapping(...)`.
- Make sure the mapper implements `HttpClientRequestMapper<T>`.

**Response-code mapping does not behave as expected:**

- Check the `@ResponseCodeMapper` entries carefully.
- Remember that `ResponseCodeMapper.DEFAULT` is the fallback for all unlisted codes.
- Make sure the server route returns the JSON shape your mapper expects for each branch.

**Interceptor logging does not appear:**

- Check `@InterceptWith(...)` on the specific client method.
- Make sure the interceptor class implements `HttpClientInterceptor`.

## What's Next? { #whats-next }

- [OpenAPI HTTP Server](openapi-http-server.md) if you have not completed the contract-first server path yet.
- [OpenAPI HTTP Client](openapi-http-client.md) after OpenAPI HTTP Server, to see how contract generation models similar transport behavior.
- [Resilient Patterns](resilient.md) to protect advanced outbound calls with retry, timeout, circuit breaker, and fallback.
- [Observability](observability.md) to trace interceptors, manual `HttpClient` calls, and mapped responses.

## Help { #help }

If you get stuck:

- compare with [Kora Java HTTP Client Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-http-client-advanced-app) and [Kora Kotlin HTTP Client Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-http-client-advanced-app)
- revisit [HTTP Client](http-client.md) for the basic declarative client shape
- revisit [HTTP Server Advanced](http-server-advanced.md) for the server endpoints this client calls
- check the [HTTP Client documentation](../documentation/http-client.md)
