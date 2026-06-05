---
search:
  exclude: true
title: HTTP Client with Kora
summary: Build a separate Kora application that calls the user endpoints from the HTTP Server guide with declarative clients
tags: http-client, http-server, declarative-client, integration
---

# HTTP Client Guide { #http-client-guide }

This guide introduces declarative HTTP clients in Kora. It covers how annotated Java interfaces describe outbound HTTP calls, how JSON request and response bodies are mapped through the client
boundary, and how Kora wires the generated client implementation into a separate application graph. You will also see how a small service wraps the transport client so application code stays focused
on use cases instead of HTTP details.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java HTTP Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-http-client-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin HTTP Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-http-client-app).

## What You'll Build { #youll-build }

You will build a second Kora application that:

- declares a typed `UserApiClient`
- calls the `/users` endpoints from the HTTP Server guide
- exposes one aggregate endpoint, `POST /client/test-all-user-endpoints`, for easy manual verification
- can also be tested against a containerized copy of the server application

## What You'll Need { #youll-need }

- JDK 17 or later
- Gradle 7+
- Docker Desktop or another local Docker environment for container-based tests
- A text editor or IDE
- Two terminals if you want to run server and client manually

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
- parameters become path variables, query parameters, or JSON bodies
- return types describe the expected response
- Kora generates the implementation at compile time

The result is a typed client that can be injected like any other Kora component.

### Transport Boundary and Application Service { #transport-boundary-application-service }

Generated clients are transport-oriented. They know how to call HTTP endpoints, but they should not define every application use case by themselves. This guide wraps the generated client in a small
service so the rest of the app can call methods that match business intent rather than raw transport details.

That wrapper is also the right place to add application-level error handling, retries in later guides, or small adaptations between external DTOs and internal models.

### Configuration and Calls { #configuration-calls }

An HTTP client also needs runtime configuration: base URL, timeouts, and other transport settings. Kora keeps those settings in configuration and wires the configured client into the dependency graph.
That keeps code stable across local development, tests, and real environments.

The practical flow is:

1. define the remote API as an annotated interface
2. configure the client target in HOCON
3. let Kora generate and inject the implementation
4. wrap the generated client in an application service
5. expose local routes that exercise outbound calls

## Dependencies { #dependencies }

The client application needs:

- HTTP client dependencies, so Kora can generate and run declarative clients
- HTTP server dependencies, because this client app still exposes one small verification endpoint of its own

===! ":fontawesome-brands-java: `Java`"

    ```groovy title="build.gradle"
    dependencies {
        implementation("ru.tinkoff.kora:config-hocon")
        implementation("ru.tinkoff.kora:http-client-common")
        implementation("ru.tinkoff.kora:http-client-ok")
        implementation("ru.tinkoff.kora:http-server-undertow")
        implementation("ru.tinkoff.kora:json-module")
        implementation("ru.tinkoff.kora:logging-logback")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="build.gradle.kts"
    dependencies {
        implementation("ru.tinkoff.kora:config-hocon")
        implementation("ru.tinkoff.kora:http-client-common")
        implementation("ru.tinkoff.kora:http-client-ok")
        implementation("ru.tinkoff.kora:http-server-undertow")
        implementation("ru.tinkoff.kora:json-module")
        implementation("ru.tinkoff.kora:logging-logback")
    }
    ```

## Modules { #modules }

We use:

- `HoconConfigModule` for `application.conf`
- `JsonModule` for request and response serialization
- `LogbackModule` for logs
- `OkHttpClientModule` for generated clients
- `UndertowHttpServerModule` because this client application exposes its own endpoint

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/httpclient/Application.java"
    package ru.tinkoff.kora.guide.httpclient;

    import ru.tinkoff.kora.application.graph.KoraApplication;
    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.config.hocon.HoconConfigModule;
    import ru.tinkoff.kora.http.client.ok.OkHttpClientModule;
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule;
    import ru.tinkoff.kora.json.module.JsonModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            OkHttpClientModule,  // <----- Connected module
            UndertowHttpServerModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/httpclient/Application.kt"
    package ru.tinkoff.kora.guide.httpclient

    import ru.tinkoff.kora.application.graph.KoraApplication
    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.config.hocon.HoconConfigModule
    import ru.tinkoff.kora.http.client.ok.OkHttpClientModule
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule
    import ru.tinkoff.kora.json.module.JsonModule
    import ru.tinkoff.kora.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        OkHttpClientModule,  // <----- Connected module
        UndertowHttpServerModule

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

## DTO Models { #dto-models }

The first client concept is not client-specific at all: the client still needs the same data shapes that the server sends and receives.

So we start by reusing the same `UserRequest` and `UserResponse` contract from the server guide. This keeps the client and server aligned and gives the generated client a typed interface to work with.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/httpclient/dto/UserRequest.java"
    package ru.tinkoff.kora.guide.httpclient.dto;

    import ru.tinkoff.kora.json.common.annotation.Json;

    @Json
    public record UserRequest(String name, String email) {}
    ```

    ```java title="src/main/java/ru/tinkoff/kora/guide/httpclient/dto/UserResponse.java"
    package ru.tinkoff.kora.guide.httpclient.dto;

    import java.time.LocalDateTime;
    import ru.tinkoff.kora.json.common.annotation.Json;

    @Json
    public record UserResponse(String id, String name, String email, LocalDateTime createdAt) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/httpclient/dto/UserRequest.kt"
    package ru.tinkoff.kora.guide.httpclient.dto

    import ru.tinkoff.kora.json.common.annotation.Json

    @Json
    data class UserRequest(val name: String, val email: String)
    ```

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/httpclient/dto/UserResponse.kt"
    package ru.tinkoff.kora.guide.httpclient.dto

    import java.time.LocalDateTime
    import ru.tinkoff.kora.json.common.annotation.Json

    @Json
    data class UserResponse(
        val id: String,
        val name: String,
        val email: String,
        val createdAt: LocalDateTime
    )
    ```

## HTTP Client { #http-client }

Now we describe the remote HTTP API as an interface.

This is the key abstraction of the guide. Instead of writing imperative client code, we declare the remote contract with annotations such as:

- `@HttpClient` to mark the whole interface as a declarative client
- `@HttpRoute` to describe the remote method and path
- `@Path`, `@Query`, `@Header`, and `@Cookie` to map individual arguments
- `@Json` to say that JSON mappers should be used for the body

This interface mirrors the user endpoints from `http-server.md`.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/httpclient/client/UserApiClient.java"
    package ru.tinkoff.kora.guide.httpclient.client;

    import jakarta.annotation.Nullable;
    import java.util.List;
    import ru.tinkoff.kora.guide.httpclient.dto.UserRequest;
    import ru.tinkoff.kora.guide.httpclient.dto.UserResponse;
    import ru.tinkoff.kora.http.client.common.annotation.HttpClient;
    import ru.tinkoff.kora.http.common.HttpMethod;
    import ru.tinkoff.kora.http.common.HttpResponseEntity;
    import ru.tinkoff.kora.http.common.annotation.Cookie;
    import ru.tinkoff.kora.http.common.annotation.Header;
    import ru.tinkoff.kora.http.common.annotation.HttpRoute;
    import ru.tinkoff.kora.http.common.annotation.Path;
    import ru.tinkoff.kora.http.common.annotation.Query;
    import ru.tinkoff.kora.json.common.annotation.Json;

    @HttpClient(configPath = "httpClient.userApi")
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
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/httpclient/client/UserApiClient.kt"
    package ru.tinkoff.kora.guide.httpclient.client

    import ru.tinkoff.kora.guide.httpclient.dto.UserRequest
    import ru.tinkoff.kora.guide.httpclient.dto.UserResponse
    import ru.tinkoff.kora.http.client.common.annotation.HttpClient
    import ru.tinkoff.kora.http.common.HttpMethod
    import ru.tinkoff.kora.http.common.HttpResponseEntity
    import ru.tinkoff.kora.http.common.annotation.Cookie
    import ru.tinkoff.kora.http.common.annotation.Header
    import ru.tinkoff.kora.http.common.annotation.HttpRoute
    import ru.tinkoff.kora.http.common.annotation.Path
    import ru.tinkoff.kora.http.common.annotation.Query
    import ru.tinkoff.kora.json.common.annotation.Json

    @HttpClient(configPath = "httpClient.userApi")
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
    }
    ```

## Configuration { #config }

This application is a standalone Kora service, so it needs its own ports.

We will use:

- `8080` for the server app from `http-server.md`
- `8081` for the client app public API
- `8086` for the client app private API
- `httpClient.userApi.url` as the base URL for the generated client

For the full configuration reference, see [HTTP Server](../documentation/http-server.md), [HTTP Client](../documentation/http-client.md) and [Logging SLF4J](../documentation/logging-slf4j.md).

===! ":material-code-json: `Hocon`"

    ```javascript title="src/main/resources/application.conf"
    httpServer {
      userApiHttpPort = 8081 //(1)!
      privateApiHttpPort = 8086 //(2)!
      telemetry.logging.enabled = true //(3)!
    }

    httpClient {
      userApi {
        url = "http://localhost:8080" //(4)!
        url = ${?USER_API_URL} //(5)!
        requestTimeout = 10s //(6)!
      }
      telemetry.logging.enabled = true //(7)!
    }

    logging {
      levels {
        "ROOT": "INFO" //(8)!
        "ru.tinkoff.kora": "INFO" //(9)!
      }
    }
    ```

    1. Named public HTTP port used by the local guide endpoint.
    2. Default private HTTP port used by probes, metrics, and management endpoints.
    3. Enables the feature for this configuration section.
    4. Base URL used by the configured client.
    5. Base URL used by the configured client. Optional override from `USER_API_URL`.
    6. Maximum time allowed for a client request.
    7. Enables the feature for this configuration section.
    8. Log level for `ROOT`.
    9. Log level for `ru.tinkoff.kora`.

=== ":simple-yaml: `YAML`"

    ```yaml title="src/main/resources/application.yaml"
    httpServer:
      userApiHttpPort: 8081 #(1)!
      privateApiHttpPort: 8086 #(2)!
      telemetry:
        logging:
          enabled: true #(3)!
    httpClient:
      userApi:
        url: ${?USER_API_URL:"http://localhost:8080"} #(4)!
        requestTimeout: 10s #(5)!
      telemetry:
        logging:
          enabled: true #(6)!
    logging:
      levels:
        ROOT: "INFO" #(7)!
        "ru.tinkoff.kora": "INFO" #(8)!
    ```

    1. Named public HTTP port used by the local guide endpoint.
    2. Default private HTTP port used by probes, metrics, and management endpoints.
    3. Enables the feature for this configuration section.
    4. Base URL used by the configured client. Uses the shown default and allows `USER_API_URL` to override it.
    5. Maximum time allowed for a client request.
    6. Enables the feature for this configuration section.
    7. Log level for `ROOT`.
    8. Log level for `ru.tinkoff.kora`.

The optional `USER_API_URL` override is especially useful in tests, where the target server may be running inside a container on a random mapped port.

## Check Controller { #check-controller }

The client application does not need to mirror the whole server again. We already have the server app for that. Instead, we expose one small controller that runs a complete scenario through the
generated client.

This is useful for two reasons:

- it gives us one manual endpoint to trigger while learning
- it keeps the generated client interfaces as the main subject of the guide

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/httpclient/controller/ClientTestController.java"
    package ru.tinkoff.kora.guide.httpclient.controller;

    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.httpclient.client.UserApiClient;
    import ru.tinkoff.kora.guide.httpclient.dto.UserRequest;
    import ru.tinkoff.kora.http.common.HttpMethod;
    import ru.tinkoff.kora.http.common.annotation.HttpRoute;
    import ru.tinkoff.kora.http.server.common.annotation.HttpController;
    import ru.tinkoff.kora.json.common.annotation.Json;

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

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/httpclient/controller/ClientTestController.kt"
    package ru.tinkoff.kora.guide.httpclient.controller

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.httpclient.client.UserApiClient
    import ru.tinkoff.kora.guide.httpclient.dto.UserRequest
    import ru.tinkoff.kora.http.common.HttpMethod
    import ru.tinkoff.kora.http.common.annotation.HttpRoute
    import ru.tinkoff.kora.http.server.common.annotation.HttpController
    import ru.tinkoff.kora.json.common.annotation.Json

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

## Best Practices { #best-practices }

- Keep client interfaces small and organized by remote API area.
- Reuse the DTO contract from the server guide where possible so client and server stay aligned.
- Prefer `HttpResponseEntity<T>` only when you need status codes or headers; otherwise return the DTO directly.
- Use one small aggregate controller for manual learning scenarios instead of rebuilding the full server inside the client app.
- Add advanced client features only when the base contract is already easy to understand.

## Summary { #summary }

You built a standalone Kora client application that consumes the user API from the HTTP Server guide.

Along the way, you:

- reused the server DTO contract
- declared a compile-time generated `UserApiClient`
- configured the remote base URL
- exposed one aggregate endpoint for easy manual verification

## Key Concepts { #key-concepts }

- `@HttpClient(configPath = ...)` binds a declarative client to a specific config section
- `@HttpRoute`, `@Path`, `@Query`, `@Header`, and `@Cookie` describe the remote contract in a type-safe way
- `HttpResponseEntity<T>` is useful when you need both the body and HTTP metadata
- a small aggregate controller is enough for a basic tutorial client application

## Troubleshooting { #troubleshooting }

**Client cannot connect to the server:**

- Confirm the server app is running on `8080` for manual checks
- Confirm `httpClient.userApi.url` points to the real server URL
- If you override `USER_API_URL`, make sure it still points to the server app public API

**Gradle build hangs or keeps file locks on Windows:**

- Run `./gradlew --stop` and retry
- If you see `AccessDeniedException` around the Gradle cache or `build/` directories, close any running Java processes, terminals, or editors that still hold file handles

**Client telemetry logs are too noisy:**

- Disable or tune `httpClient.telemetry.logging.enabled` in `application.conf` once you finish debugging

**Private API readiness checks do not work:**

- This guide uses `8086` as the client app private API port so it stays separate from the server app ports
- The standard readiness path is `/system/readiness`
- If you change either value, update the wait strategy and troubleshooting notes consistently

## What's Next? { #whats-next }

- [HTTP Server Advanced](http-server-advanced.md) if you want to prepare the advanced server routes used by the advanced client guide.
- [HTTP Client Advanced](http-client-advanced.md) after HTTP Server Advanced, to add forms, multipart, interceptors, custom mapping, and manual low-level calls.
- [OpenAPI HTTP Server](openapi-http-server.md) before [OpenAPI HTTP Client](openapi-http-client.md), because the generated client needs a generated server contract to follow.
- [Resilient Patterns](resilient.md) to make outbound calls safer against slow or unstable services.
- [Observability](observability.md) to trace and measure service-to-service calls.

## Help { #help }

If you get stuck:

- compare with [Kora Java HTTP Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-http-client-app) and [Kora Kotlin HTTP Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-http-client-app)
- revisit [HTTP Server](http-server.md) and run the server app before starting the client
- check the [HTTP Client documentation](../documentation/http-client.md)
- check the [HTTP Server documentation](../documentation/http-server.md)
