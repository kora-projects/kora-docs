---
search:
  exclude: true
title: HTTP Client with Kora
summary: Build a separate Kora application that calls the user endpoints from the HTTP Server guide with declarative synchronous clients
description: "Step-by-step declarative HTTP client for a Kora 2.0 service: the io.koraframework:http-client-ok artifact and OkHttpClientModule, a @HttpClient interface whose @HttpRoute methods bind @Path, @Query, @Header and @Cookie parameters and @Json request and response DTOs, HttpResponseEntity returns and a custom HttpClientResponseMapper, HttpClientResponseException on non-2xx answers, the httpClient.userApi url, requestTimeout and telemetry configuration next to httpServer.port and httpServer.system.port, and a @KoraAppTest check of the client against the running server application."
agent:
  use_when: "Use this file for questions about calling another service from Kora 2.0 with a declarative client: io.koraframework:http-client-ok, OkHttpClientModule, @HttpClient with a config path, @HttpRoute with HttpMethod, @Path, @Query, @Header, @Cookie, @Json bodies, HttpResponseEntity, writing an HttpClientResponseMapper for a type Kora has no ready mapper for, HttpClientResponseException and its code, headers and bytes, the httpClient.userApi.url and requestTimeout keys versus the transport-wide httpClient.connectTimeout, readTimeout and proxy, why suspend and CompletionStage client methods are rejected, and running the client and server applications side by side."
tags: http-client, http-server, declarative-client, okhttp, integration
---

# HTTP Client Guide { #http-client-guide }

This guide introduces declarative HTTP clients in Kora. It covers how annotated Java and Kotlin interfaces describe outbound HTTP calls, how JSON request and response bodies are mapped through the
client boundary, and how Kora wires the generated client implementation into a separate application graph. You will also see how the client application keeps HTTP details near the transport boundary so
the rest of the code stays focused on use cases.

Kora HTTP clients are **synchronous**. A declarative method sends the request, waits for the response, and returns the mapped result directly. There are no `CompletionStage`, `Mono`, `Flux` or
`suspend` client methods to reason about: concurrency comes from running calls on virtual threads or from structured concurrency, not from the return type.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java HTTP Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-http-client-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin HTTP Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-http-client-app).

## What You'll Build { #youll-build }

You will build a second Kora application that:

- declares a typed `UserApiClient`
- calls the `/users` endpoints from the HTTP Server guide
- exposes one aggregate endpoint, `POST /client/test-all-user-endpoints`, for easy manual verification
- is covered by a JUnit 5 test that runs against a containerized copy of the server application

## What You'll Need { #youll-need }

- JDK 25 or later
- Gradle 9+ (the reference applications use Gradle Wrapper `9.5.1`)
- Docker Desktop or another local Docker environment for container-based tests
- A text editor or IDE
- Two terminals if you want to run server and client manually

Kora artifacts are compiled for Java 25, so the JDK that compiles your code must be 25 or newer.

## Prerequisites { #prerequisites }

!!! note "Required: Complete HTTP Server Guide"

    This guide assumes you have completed **[HTTP Server Guide](http-server.md)** and already understand the user CRUD API endpoints.

    If you haven't completed the HTTP server guide yet, do that first, because this guide builds a separate client application that calls that existing API.

## Overview { #overview }

An [HTTP](https://www.rfc-editor.org/rfc/rfc9110) client is the outbound boundary of an application. It represents another service's API inside your codebase. Kora's declarative client model lets you
describe that remote API as a Java or Kotlin interface instead of manually assembling URLs, headers, request bodies, and response parsing logic.

That is similar to how a controller describes an inbound HTTP API, but the direction is reversed. A controller adapts incoming HTTP requests into application calls. A client adapts application calls
into outgoing HTTP requests.

### Declarative Clients { #declarative-clients }

For the full declarative client model, `@HttpClient`, routes, and configuration, see [Declarative HTTP client](../documentation/http-client.md#client-declarative).

Declarative clients use the same general idea as server controllers, but in the opposite direction:

- method annotations describe the remote HTTP method and path
- parameters become path variables, query parameters, headers, cookies, or bodies
- return types describe the expected response
- Kora generates the implementation at compile time

The result is a typed client that can be injected like any other Kora component. Nothing is resolved by reflection at runtime: the annotation processor writes a plain class that builds the request and
maps the response.

### Transport Boundary and Application Service { #transport-boundary-application-service }

Generated clients are transport-oriented. They know how to call HTTP endpoints, but they should not define every application use case by themselves. Keep the generated interface close to the remote
contract, and let application components call it the way they would call any other dependency.

That boundary is also the right place for application-level error handling, resilience annotations in later guides, or small adaptations between external DTOs and internal models.

### Configuration and Calls { #configuration-calls }

An HTTP client also needs runtime configuration: base URL, timeouts, and telemetry settings. Kora keeps those settings in configuration and wires the configured client into the dependency graph.
That keeps code stable across local development, tests, and real environments.

The practical flow is:

1. define the remote API as an annotated interface
2. configure the client target in HOCON
3. let Kora generate and inject the implementation
4. call the generated client from application components
5. expose local routes that exercise outbound calls

## Dependencies { #dependencies }

The client application needs:

- an HTTP client transport, so Kora can generate and run declarative clients
- HTTP server dependencies, because this client app still exposes one small verification endpoint of its own

Kora 2.0 ships three transports, and exactly one of them must be on the classpath:

| Artifact | Transport |
|---|---|
| `io.koraframework:http-client-ok` | [OkHttp](https://square.github.io/okhttp/) |
| `io.koraframework:http-client-apache` | [Apache HttpClient](https://hc.apache.org/) |
| `io.koraframework:http-client-jdk` | `java.net.http.HttpClient` from the JDK |

This guide uses OkHttp.

Versions come from the Kora BOM `io.koraframework:kora-bom`, so individual Kora modules are declared without a version:

```properties title="gradle.properties"
koraVersion=2.0.0.RC1
junitVersion=6.1.3
```

===! ":fontawesome-brands-java: `Java`"

    ```groovy title="build.gradle"
    configurations {
        koraBom
        annotationProcessor.extendsFrom(koraBom)
        implementation.extendsFrom(koraBom)
        testAnnotationProcessor.extendsFrom(koraBom)
    }

    dependencies {
        koraBom platform("io.koraframework:kora-bom:$koraVersion")

        annotationProcessor "io.koraframework:annotation-processors"

        implementation "io.koraframework:config-hocon"
        implementation "io.koraframework:http-client-common"
        implementation "io.koraframework:http-client-ok"
        implementation "io.koraframework:http-server-undertow"
        implementation "io.koraframework:json-common"
        implementation "io.koraframework:logging-logback"

        testAnnotationProcessor "io.koraframework:annotation-processors"

        testImplementation platform("org.junit:junit-bom:$junitVersion")
        testImplementation "org.junit.jupiter:junit-jupiter"
        testImplementation "io.koraframework:test-junit5"
        testImplementation "org.testcontainers:testcontainers-junit-jupiter:2.0.5"
        testImplementation "org.testcontainers:testcontainers:2.0.5"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="build.gradle.kts"
    dependencies {
        implementation(platform("io.koraframework:kora-bom:${property("koraVersion")}"))

        ksp("io.koraframework:symbol-processors:${property("koraVersion")}")

        implementation("io.koraframework:config-hocon")
        implementation("io.koraframework:http-client-common")
        implementation("io.koraframework:http-client-ok")
        implementation("io.koraframework:http-server-undertow")
        implementation("io.koraframework:json-common")
        implementation("io.koraframework:logging-logback")

        testImplementation(platform("org.junit:junit-bom:${property("junitVersion")}"))
        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation("io.koraframework:test-junit5")
        testImplementation("org.testcontainers:testcontainers-junit-jupiter:2.0.5")
        testImplementation("org.testcontainers:testcontainers:2.0.5")
    }
    ```

Java code generation runs through the `io.koraframework:annotation-processors` annotation processor; Kotlin code generation runs through the `io.koraframework:symbol-processors` KSP processor. Without
one of them the `@HttpClient` interface stays an interface and the graph never finds an implementation.

## Modules { #modules }

We use:

- `HoconConfigModule` for `application.conf`
- `JsonModule` for request and response serialization
- `LogbackModule` for logs
- `OkHttpClientModule` for the client transport
- `UndertowPublicHttpServerModule` because this client application exposes its own endpoint

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/httpclient/Application.java"
    package io.koraframework.guide.httpclient;

    import io.koraframework.application.graph.KoraApplication;
    import io.koraframework.common.annotation.KoraApp;
    import io.koraframework.config.hocon.HoconConfigModule;
    import io.koraframework.http.client.ok.OkHttpClientModule;
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule;
    import io.koraframework.json.common.JsonModule;
    import io.koraframework.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            OkHttpClientModule,  // <----- Connected module
            UndertowPublicHttpServerModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/httpclient/Application.kt"
    package io.koraframework.guide.httpclient

    import io.koraframework.application.graph.KoraApplication
    import io.koraframework.common.annotation.KoraApp
    import io.koraframework.config.hocon.HoconConfigModule
    import io.koraframework.http.client.ok.OkHttpClientModule
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule
    import io.koraframework.json.common.JsonModule
    import io.koraframework.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        OkHttpClientModule,  // <----- Connected module
        UndertowPublicHttpServerModule

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

`OkHttpClientModule` contributes the transport `HttpClient` component plus the request and response mappers every generated client relies on. Swapping it for `ApacheHttpClientModule` or
`JdkHttpClientModule` changes the transport without touching a single client interface.

## DTO Models { #dto-models }

The first client concept is not client-specific at all: the client still needs the same data shapes that the server sends and receives.

So we start by reusing the same `UserRequest` and `UserResponse` contract from the server guide. This keeps the client and server aligned and gives the generated client a typed interface to work with.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/httpclient/dto/UserRequest.java"
    package io.koraframework.guide.httpclient.dto;

    import io.koraframework.json.common.annotation.Json;

    @Json
    public record UserRequest(String name, String email) {}
    ```

    ```java title="src/main/java/io/koraframework/guide/httpclient/dto/UserResponse.java"
    package io.koraframework.guide.httpclient.dto;

    import java.time.LocalDateTime;
    import io.koraframework.json.common.annotation.Json;

    @Json
    public record UserResponse(String id, String name, String email, LocalDateTime createdAt) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/httpclient/dto/UserRequest.kt"
    package io.koraframework.guide.httpclient.dto

    import io.koraframework.json.common.annotation.Json

    @Json
    data class UserRequest(val name: String, val email: String)
    ```

    ```kotlin title="src/main/kotlin/io/koraframework/guide/httpclient/dto/UserResponse.kt"
    package io.koraframework.guide.httpclient.dto

    import io.koraframework.json.common.annotation.Json
    import java.time.LocalDateTime

    @Json
    data class UserResponse(
        val id: String,
        val name: String,
        val email: String,
        val createdAt: LocalDateTime
    )
    ```

`@Json` makes the compiler generate a `JsonReader` and a `JsonWriter` for each type, and those are exactly the components the generated client asks for when a method or parameter is annotated with
`@Json`.

## HTTP Client { #http-client }

Now we describe the remote HTTP API as an interface.

This is the key abstraction of the guide. Instead of writing imperative client code, we declare the remote contract with annotations such as:

- `@HttpClient` to mark the whole interface as a declarative client, with the configuration path as its value
- `@HttpRoute` to describe the remote method and path
- `@Path`, `@Query`, `@Header`, and `@Cookie` to map individual arguments
- `@Json` to say that JSON mappers should be used for the body

This interface mirrors the user endpoints from `http-server.md`.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/httpclient/client/UserApiClient.java"
    package io.koraframework.guide.httpclient.client;

    import java.io.IOException;
    import java.util.List;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.httpclient.dto.UserRequest;
    import io.koraframework.guide.httpclient.dto.UserResponse;
    import io.koraframework.http.client.common.annotation.HttpClient;
    import io.koraframework.http.client.common.response.HttpClientResponse;
    import io.koraframework.http.client.common.response.HttpClientResponseMapper;
    import io.koraframework.http.common.HttpMethod;
    import io.koraframework.http.common.HttpResponseEntity;
    import io.koraframework.http.common.annotation.Cookie;
    import io.koraframework.http.common.annotation.Header;
    import io.koraframework.http.common.annotation.HttpRoute;
    import io.koraframework.http.common.annotation.Path;
    import io.koraframework.http.common.annotation.Query;
    import io.koraframework.json.common.annotation.Json;
    import org.jspecify.annotations.Nullable;

    @HttpClient("httpClient.userApi")
    public interface UserApiClient {

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        HttpResponseEntity<UserResponse> createUser(
                @Json UserRequest request,
                @Nullable @Header("X-Request-ID") String requestId,
                @Nullable @Header("User-Agent") String userAgent,
                @Nullable @Cookie("sessionId") String sessionId);

        @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}")
        @Json
        UserResponse getUser(@Path String userId);

        @HttpRoute(method = HttpMethod.GET, path = "/users")
        @Json
        List<UserResponse> getUsers(
                @Nullable @Query("page") Integer page,
                @Nullable @Query("size") Integer size,
                @Nullable @Query("sort") String sort);

        @HttpRoute(method = HttpMethod.DELETE, path = "/users/{userId}")
        HttpResponseEntity<Void> deleteUser(@Path String userId);

        @Component
        final class VoidResponseMapper implements HttpClientResponseMapper<Void> {

            @Override
            public Void apply(HttpClientResponse response) throws IOException {
                try (var body = response.body()) {
                    body.asInputStream().readAllBytes();
                }
                return null;
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/httpclient/client/UserApiClient.kt"
    package io.koraframework.guide.httpclient.client

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.httpclient.dto.UserRequest
    import io.koraframework.guide.httpclient.dto.UserResponse
    import io.koraframework.http.client.common.annotation.HttpClient
    import io.koraframework.http.client.common.response.HttpClientResponse
    import io.koraframework.http.client.common.response.HttpClientResponseMapper
    import io.koraframework.http.common.HttpMethod
    import io.koraframework.http.common.HttpResponseEntity
    import io.koraframework.http.common.annotation.Cookie
    import io.koraframework.http.common.annotation.Header
    import io.koraframework.http.common.annotation.HttpRoute
    import io.koraframework.http.common.annotation.Path
    import io.koraframework.http.common.annotation.Query
    import io.koraframework.json.common.annotation.Json

    @HttpClient("httpClient.userApi")
    interface UserApiClient {

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        fun createUser(
            @Json request: UserRequest,
            @Header("X-Request-ID") requestId: String?,
            @Header("User-Agent") userAgent: String?,
            @Cookie("sessionId") sessionId: String?
        ): HttpResponseEntity<UserResponse>

        @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}")
        @Json
        fun getUser(@Path userId: String): UserResponse

        @HttpRoute(method = HttpMethod.GET, path = "/users")
        @Json
        fun getUsers(
            @Query("page") page: Int?,
            @Query("size") size: Int?,
            @Query("sort") sort: String?
        ): List<UserResponse>

        @HttpRoute(method = HttpMethod.DELETE, path = "/users/{userId}")
        fun deleteUser(@Path userId: String): HttpResponseEntity<Void>

        @Component
        class VoidResponseMapper : HttpClientResponseMapper<Void> {

            override fun apply(response: HttpClientResponse): Void? {
                response.body().use { body ->
                    body.asInputStream().readAllBytes()
                }
                return null
            }
        }
    }
    ```

Several details in this interface are worth reading slowly.

**The configuration path is the annotation value.** `@HttpClient("httpClient.userApi")` binds this client to the `httpClient.userApi` configuration section. The value is positional; the annotation
only declares `value`, `telemetryTag` and `httpClientTag`. If the value is omitted, Kora derives the path from the interface name: `UserApiClient` becomes `httpClient.userApiClient`.

**Nullable parameters are optional.** A `@Nullable` header, query parameter, or cookie is simply skipped when the argument is `null`. In Kotlin the nullable type `String?` carries the same meaning, so
no annotation is needed. A non-nullable parameter is always written into the request.

**Methods are synchronous.** `getUser` returns `UserResponse`, not a future. Kotlin `suspend` functions are rejected by the symbol processor with a compilation error, and Java clients that return
`CompletionStage` produce the warning `Method has async signature, this might not work correctly`. Write plain blocking signatures.

**Success and failure are separated by status code.** For a method that returns a plain body, Kora maps the response only for `2xx` statuses; anything else throws `HttpClientResponseException`. When
you need the status code itself, return `HttpResponseEntity<T>` instead, as `createUser` and `deleteUser` do.

**`HttpResponseEntity<Void>` needs its own mapper.** Kora provides ready response mappers for `String`, `byte[]`, `ByteBuffer` and `HttpBodyInput`, and a template factory that wraps any
`HttpClientResponseMapper<T>` into `HttpClientResponseMapper<HttpResponseEntity<T>>`. There is no built-in mapper for `Void`, so `deleteUser` would fail the graph build with
`No component found for dependency:` unless the application supplies one. `VoidResponseMapper` is that component: it drains the body and returns `null`, and the framework wraps it into the entity
itself. Note that it is registered as a `@Component` and is **not** referenced with `@Mapping` — `@Mapping` would require the mapper to produce the whole `HttpResponseEntity<Void>` rather than just the
payload.

!!! tip "Simpler alternative"

    If you do not need the status code of a body-less response, declare `void deleteUser(@Path String userId)`. A `void` method needs no response mapper at all, and a non-`2xx` status still raises
    `HttpClientResponseException`.

## Configuration { #config }

This application is a standalone Kora service, so it needs its own ports.

We will use:

- `8080` for the server app from `http-server.md`
- `8081` for the client app public HTTP server
- `8086` for the client app system HTTP server (probes, metrics)
- `httpClient.userApi.url` as the base URL for the generated client

For the full configuration reference, see [HTTP Server](../documentation/http-server.md), [HTTP Client](../documentation/http-client.md) and [Logging SLF4J](../documentation/logging-slf4j.md).

===! ":material-code-json: `Hocon`"

    ```javascript title="src/main/resources/application.conf"
    httpServer {
      port = 8081 //(1)!
      system.port = 8086 //(2)!
      telemetry.logging.enabled = true //(3)!
    }

    httpClient {
      userApi {
        url = "http://localhost:8080" //(4)!
        url = ${?USER_API_URL} //(5)!
        requestTimeout = 10s //(6)!
        telemetry.logging.enabled = true //(7)!
      }
    }

    logging {
      levels {
        "ROOT": "INFO" //(8)!
        "io.koraframework": "INFO" //(9)!
      }
    }
    ```

    1. Public HTTP server port used by the local guide endpoint (default: `8080`).
    2. System HTTP server port used by probes and metrics (default: `8085`).
    3. Enables request logging for the public HTTP server (default: `false`).
    4. Base URL used by the configured client (required, no default).
    5. Optional override of the base URL from the `USER_API_URL` environment variable.
    6. Maximum time allowed for one client request (optional, no default).
    7. Enables request logging for this client (default: `false`).
    8. Log level for `ROOT`.
    9. Log level for `io.koraframework`.

=== ":simple-yaml: `YAML`"

    ```yaml title="src/main/resources/application.yaml"
    httpServer:
      port: 8081 #(1)!
      system:
        port: 8086 #(2)!
      telemetry:
        logging:
          enabled: true #(3)!
    httpClient:
      userApi:
        url: ${USER_API_URL:http://localhost:8080} #(4)!
        requestTimeout: 10s #(5)!
        telemetry:
          logging:
            enabled: true #(6)!
    logging:
      levels:
        ROOT: "INFO" #(7)!
        "io.koraframework": "INFO" #(8)!
    ```

    1. Public HTTP server port used by the local guide endpoint (default: `8080`).
    2. System HTTP server port used by probes and metrics (default: `8085`).
    3. Enables request logging for the public HTTP server (default: `false`).
    4. Base URL used by the configured client (required, no default). Uses the shown default and allows `USER_API_URL` to override it.
    5. Maximum time allowed for one client request (optional, no default).
    6. Enables request logging for this client (default: `false`).
    7. Log level for `ROOT`.
    8. Log level for `io.koraframework`.

Telemetry belongs to the client section, not to the shared `httpClient` root: the declarative client reads exactly the subtree named by `@HttpClient`, so `httpClient.userApi.telemetry` is the path that
affects `UserApiClient`. Transport-wide settings such as `httpClient.connectTimeout`, `httpClient.readTimeout` and `httpClient.proxy` do live at the root, because they configure the shared transport.

The optional `USER_API_URL` override is especially useful in tests, where the target server may be running inside a container on a random mapped port.

## Check Controller { #check-controller }

The client application does not need to mirror the whole server again. We already have the server app for that. Instead, we expose one small controller that runs a complete scenario through the
generated client.

This is useful for two reasons:

- it gives us one manual endpoint to trigger while learning
- it keeps the generated client interfaces as the main subject of the guide

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/httpclient/controller/ClientTestController.java"
    package io.koraframework.guide.httpclient.controller;

    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.httpclient.client.UserApiClient;
    import io.koraframework.guide.httpclient.dto.UserRequest;
    import io.koraframework.http.common.HttpMethod;
    import io.koraframework.http.common.annotation.HttpRoute;
    import io.koraframework.http.server.common.annotation.HttpController;
    import io.koraframework.json.common.annotation.Json;

    @Component
    @HttpController
    public final class ClientTestController {

        private final UserApiClient userApiClient;

        public ClientTestController(UserApiClient userApiClient) {
            this.userApiClient = userApiClient;
        }

        @HttpRoute(method = HttpMethod.POST, path = "/client/test-all-user-endpoints")
        @Json
        public TestResults testAllUserEndpoints() {
            try {
                var created = this.userApiClient.createUser(
                        new UserRequest("Client Demo User", "client-demo@example.com"),
                        "client-test-request",
                        "guide-http-client-app",
                        "client-test-session");

                boolean userCreated = created.code() == 201 && created.body() != null;
                var createdUser = created.body();
                var fetched = createdUser == null ? null : this.userApiClient.getUser(createdUser.id());
                boolean userFetched = fetched != null && createdUser != null && fetched.id().equals(createdUser.id());
                var users = this.userApiClient.getUsers(0, 10, "name");
                boolean usersListed = createdUser != null && users.stream().anyMatch(user -> user.id().equals(createdUser.id()));
                var deleteResult = createdUser == null ? null : this.userApiClient.deleteUser(createdUser.id());
                boolean userDeleted = deleteResult != null && deleteResult.code() == 204;

                boolean allTestsPassed = userCreated && userFetched && usersListed && userDeleted;
                return new TestResults(userCreated, userFetched, usersListed, userDeleted, allTestsPassed, null);
            } catch (Exception exception) {
                return new TestResults(false, false, false, false, false, exception.getMessage());
            }
        }

        @Json
        public record TestResults(
                boolean userCreated,
                boolean userFetched,
                boolean usersListed,
                boolean userDeleted,
                boolean allTestsPassed,
                String error) {}
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/httpclient/controller/ClientTestController.kt"
    package io.koraframework.guide.httpclient.controller

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.httpclient.client.UserApiClient
    import io.koraframework.guide.httpclient.dto.UserRequest
    import io.koraframework.http.common.HttpMethod
    import io.koraframework.http.common.annotation.HttpRoute
    import io.koraframework.http.server.common.annotation.HttpController
    import io.koraframework.json.common.annotation.Json

    @Component
    @HttpController
    class ClientTestController(
        private val userApiClient: UserApiClient
    ) {
        @HttpRoute(method = HttpMethod.POST, path = "/client/test-all-user-endpoints")
        @Json
        fun testAllUserEndpoints(): TestResults {
            return try {
                val created = userApiClient.createUser(
                    UserRequest("Client Demo User", "client-demo@example.com"),
                    "client-test-request",
                    "guide-http-client-app",
                    "client-test-session"
                )

                val userCreated = created.code() == 201 && created.body() != null
                val createdUser = created.body()
                val fetched = createdUser?.let { userApiClient.getUser(it.id) }
                val userFetched = fetched != null && createdUser != null && fetched.id == createdUser.id
                val users = userApiClient.getUsers(0, 10, "name")
                val usersListed = createdUser != null && users.any { it.id == createdUser.id }
                val deleteResult = createdUser?.let { userApiClient.deleteUser(it.id) }
                val userDeleted = deleteResult != null && deleteResult.code() == 204

                val allTestsPassed = userCreated && userFetched && usersListed && userDeleted
                TestResults(userCreated, userFetched, usersListed, userDeleted, allTestsPassed, null)
            } catch (e: Exception) {
                TestResults(false, false, false, false, false, e.message)
            }
        }

        @Json
        data class TestResults(
            val userCreated: Boolean,
            val userFetched: Boolean,
            val usersListed: Boolean,
            val userDeleted: Boolean,
            val allTestsPassed: Boolean,
            val error: String?
        )
    }
    ```

Notice how ordinary the calling code looks. Because the client is synchronous, the scenario reads top to bottom: create, fetch, list, delete. The only client-specific detail is `HttpResponseEntity`,
which exposes `code()` and `body()` when the status code matters.

## Check Application { #check-app }

If you want to verify the scenario manually, run both apps in separate terminals.

### Terminal 1: Server { #terminal-1-server }

```bash
./gradlew clean classes
./gradlew run
```

The server app should expose its public API on `http://localhost:8080`.

### Terminal 2: Client { #terminal-2-client }

```bash
./gradlew clean classes
./gradlew run
```

The client app should expose its public API on `http://localhost:8081`.

### Client Scenario { #client-scenario }

```bash
curl -X POST http://localhost:8081/client/test-all-user-endpoints
```

Expected result: a JSON object where `allTestsPassed` is `true`.

### Container Test { #container-test }

Manual checks are fine while learning, but the same scenario is easy to automate. `@KoraAppTest` starts the client application graph inside JUnit 5, `@TestComponent` injects the generated client, and
`KoraAppTestConfigModifier` points `USER_API_URL` at a containerized copy of the server application.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/test/java/io/koraframework/guide/httpclient/HttpClientAppTest.java"
    package io.koraframework.guide.httpclient;

    import static org.junit.jupiter.api.Assertions.assertEquals;
    import static org.junit.jupiter.api.Assertions.assertNotNull;
    import static org.junit.jupiter.api.Assertions.assertThrows;

    import java.util.UUID;
    import org.junit.jupiter.api.Test;
    import org.testcontainers.junit.jupiter.Container;
    import org.testcontainers.junit.jupiter.Testcontainers;
    import io.koraframework.guide.httpclient.client.UserApiClient;
    import io.koraframework.guide.httpclient.dto.UserRequest;
    import io.koraframework.http.client.common.exception.HttpClientResponseException;
    import io.koraframework.test.extension.junit5.KoraAppTest;
    import io.koraframework.test.extension.junit5.KoraAppTestConfigModifier;
    import io.koraframework.test.extension.junit5.KoraConfigModification;
    import io.koraframework.test.extension.junit5.TestComponent;

    @Testcontainers
    @KoraAppTest(Application.class)
    class HttpClientAppTest implements KoraAppTestConfigModifier {

        @Container
        static final AppContainer APP = new AppContainer();

        @TestComponent
        private UserApiClient userApiClient;

        @Override
        public KoraConfigModification config() {
            return KoraConfigModification.ofResourceFile("application.conf")
                    .withSystemProperty("USER_API_URL", APP.getURI().toString());
        }

        @Test
        void createUserReturnsCreatedUser() {
            String unique = UUID.randomUUID().toString().substring(0, 8);

            var response = this.userApiClient.createUser(
                    new UserRequest("Client User " + unique, "client-" + unique + "@example.com"),
                    "request-1",
                    "test-agent",
                    "session-1");

            assertEquals(201, response.code());
            assertNotNull(response.body());
        }

        @Test
        void getMissingUserThrows() {
            assertThrows(HttpClientResponseException.class, () -> this.userApiClient.getUser("999999"));
        }

        @Test
        void deleteUserReturnsNoContent() {
            String unique = UUID.randomUUID().toString().substring(0, 8);
            var created = this.userApiClient.createUser(
                    new UserRequest("Delete Me " + unique, "delete-" + unique + "@example.com"),
                    "request-3",
                    "test-agent",
                    "session-3").body();

            var response = this.userApiClient.deleteUser(created.id());

            assertEquals(204, response.code());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/test/kotlin/io/koraframework/guide/httpclient/HttpClientAppTest.kt"
    package io.koraframework.guide.httpclient

    import org.junit.jupiter.api.Assertions.assertEquals
    import org.junit.jupiter.api.Assertions.assertNotNull
    import org.junit.jupiter.api.Assertions.assertThrows
    import org.junit.jupiter.api.Test
    import org.testcontainers.junit.jupiter.Container
    import org.testcontainers.junit.jupiter.Testcontainers
    import io.koraframework.guide.httpclient.client.UserApiClient
    import io.koraframework.guide.httpclient.dto.UserRequest
    import io.koraframework.http.client.common.exception.HttpClientResponseException
    import io.koraframework.test.extension.junit5.KoraAppTest
    import io.koraframework.test.extension.junit5.KoraAppTestConfigModifier
    import io.koraframework.test.extension.junit5.KoraConfigModification
    import io.koraframework.test.extension.junit5.TestComponent
    import java.util.UUID

    @Testcontainers
    @KoraAppTest(Application::class)
    class HttpClientAppTest : KoraAppTestConfigModifier {

        @TestComponent
        lateinit var userApiClient: UserApiClient

        override fun config(): KoraConfigModification =
            KoraConfigModification.ofResourceFile("application.conf")
                .withSystemProperty("USER_API_URL", APP.getURI().toString())

        @Test
        fun createUserReturnsCreatedUser() {
            val unique = UUID.randomUUID().toString().substring(0, 8)

            val response = userApiClient.createUser(
                UserRequest("Client User $unique", "client-$unique@example.com"),
                "request-1",
                "test-agent",
                "session-1"
            )

            assertEquals(201, response.code())
            assertNotNull(response.body())
        }

        @Test
        fun getMissingUserThrows() {
            assertThrows(HttpClientResponseException::class.java) { userApiClient.getUser("999999") }
        }

        @Test
        fun deleteUserReturnsNoContent() {
            val unique = UUID.randomUUID().toString().substring(0, 8)
            val created = userApiClient.createUser(
                UserRequest("Delete Me $unique", "delete-$unique@example.com"),
                "request-3",
                "test-agent",
                "session-3"
            ).body()!!

            val response = userApiClient.deleteUser(created.id)

            assertEquals(204, response.code())
        }

        companion object {
            @Container
            @JvmStatic
            val APP: AppContainer = AppContainer()
        }
    }
    ```

`AppContainer` is an ordinary Testcontainers `GenericContainer` that builds the server application image from the server guide's `Dockerfile`, exposes `8080` and `8085`, and waits for
`/system/readiness` on the system port before the test starts. The container mechanics are covered in detail in [Integration Testing](testing-integration.md).

## Best Practices { #best-practices }

- Keep client interfaces small and organized by remote API area.
- Reuse the DTO contract from the server guide where possible so client and server stay aligned.
- Prefer `HttpResponseEntity<T>` only when you need status codes or headers; otherwise return the DTO directly.
- Keep client methods blocking. If you need parallel calls, run the blocking calls on virtual threads or in a structured task scope instead of changing the return type.
- Give every client its own configuration section so timeouts and telemetry can be tuned per remote service.
- Use one small aggregate controller for manual learning scenarios instead of rebuilding the full server inside the client app.
- Add advanced client features only when the base contract is already easy to understand.

## Summary { #summary }

You built a standalone Kora client application that consumes the user API from the HTTP Server guide.

Along the way, you:

- reused the server DTO contract
- declared a compile-time generated `UserApiClient`
- supplied the `HttpClientResponseMapper<Void>` that a body-less `HttpResponseEntity<Void>` response needs
- configured the remote base URL, request timeout and client telemetry
- exposed one aggregate endpoint for easy manual verification
- covered the client with a JUnit 5 test against a containerized server

## Key Concepts { #key-concepts }

- `@HttpClient("httpClient.userApi")` binds a declarative client to a specific configuration section through its positional value
- `@HttpRoute`, `@Path`, `@Query`, `@Header`, and `@Cookie` describe the remote contract in a type-safe way
- declarative client methods are synchronous and return the mapped result directly
- `HttpResponseEntity<T>` is useful when you need both the body and HTTP metadata
- non-`2xx` responses raise `HttpClientResponseException` unless the method explicitly models them
- the transport is chosen by the module (`OkHttpClientModule`, `ApacheHttpClientModule`, `JdkHttpClientModule`), not by the client interface

## Troubleshooting { #troubleshooting }

**Client cannot connect to the server:**

- Confirm the server app is running on `8080` for manual checks
- Confirm `httpClient.userApi.url` points to the real server URL
- If you override `USER_API_URL`, make sure it still points to the server app public API

**The build fails with `No component found for dependency:` and an `HttpClientResponseMapper` type:**

- A method returns a type Kora has no ready mapper for. Add a `@Component` implementing `HttpClientResponseMapper<T>` for the payload type, as `VoidResponseMapper` does for `Void`
- For JSON payloads, make sure the DTO is annotated with `@Json` and the method or parameter is annotated with `@Json` too

**Kotlin compilation fails with `Suspend methods are not supported by the HTTP client generator`:**

- Remove `suspend` from the client method. Kora HTTP clients are blocking by design

**The Java build prints `Method has async signature, this might not work correctly`:**

- The method returns `CompletionStage` or `Mono`. Change it to a plain synchronous return type

**Calls fail with `HttpClientResponseException`:**

- The remote service answered with a non-`2xx` status. `getCode()`, `getHeaders()` and `getBytes()` on the exception carry the response details
- If a non-`2xx` status is a normal part of the contract, return `HttpResponseEntity<T>` or model both branches, as shown in [HTTP Client Advanced](http-client-advanced.md#response-code-mapping)

**Gradle build hangs or keeps file locks on Windows:**

- Run `./gradlew --stop` and retry
- If you see `AccessDeniedException` around the Gradle cache or `build/` directories, close any running Java processes, terminals, or editors that still hold file handles

**Client telemetry logs are too noisy:**

- Disable or tune `httpClient.userApi.telemetry.logging.enabled` in `application.conf` once you finish debugging
- Sensitive headers are already masked: `authorization`, `cookie` and `set-cookie` are replaced with `***` by default

**System endpoints do not answer:**

- This guide uses `8086` as the client app system HTTP port so it stays separate from the server app ports
- The standard readiness path is `/system/readiness`, and liveness is `/system/liveness`
- If you change either value, update the wait strategy and troubleshooting notes consistently

## What's Next? { #whats-next }

- [HTTP Server Advanced](http-server-advanced.md) if you want to prepare the advanced server routes used by the advanced client guide.
- [HTTP Client Advanced](http-client-advanced.md) after HTTP Server Advanced, to add forms, multipart, interceptors, custom mapping, and manual low-level calls.
- [OpenAPI HTTP Server](openapi-http-server.md) before [OpenAPI HTTP Client](openapi-http-client.md), because the generated client needs a generated server contract to follow.
- [Resilient Patterns](resilient.md) to make outbound calls safer against slow or unstable services.
- [Observability](observability.md) to trace and measure service-to-service calls.

## Help { #help }

If you get stuck:

- compare with [Kora Java HTTP Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-http-client-app) and [Kora Kotlin HTTP Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-http-client-app)
- revisit [HTTP Server](http-server.md) and run the server app before starting the client
- check the [HTTP Client documentation](../documentation/http-client.md)
- check the [HTTP Server documentation](../documentation/http-server.md)
