---
search:
  exclude: true
title: gRPC Client with Kora
summary: Build a Kora gRPC client that consumes a unary CRUD service through generated stubs
tags: grpc-client, protobuf, rpc, microservices
---

# gRPC Client with Kora { #grpc-client-kora }

This guide introduces unary gRPC clients with Kora. It covers how the same `.proto` contract generates client stubs and message types, how Kora injects configured gRPC clients into the application
graph, and how a small service wrapper turns stub calls into application-level operations. You will also see how gRPC statuses and generated request builders shape client code differently from
declarative HTTP clients.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java gRPC Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-grpc-client-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin gRPC Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-grpc-client-app).

## What You'll Build { #youll-build }

You will build a separate unary gRPC client application with:

- the same `user_service.proto` contract used by the server
- generated protobuf request and response types
- an injected Kora gRPC client stub for `UserService`
- a small application service that wraps `CreateUser`, `GetUser`, `GetUsers`, `UpdateUser`, and `DeleteUser`
- HTTP trigger routes that make the client easy to exercise locally
- runtime checks against a running gRPC server

## What You'll Need { #youll-need }

- JDK 17 or later
- Gradle 7+
- A text editor or IDE
- A running gRPC server from the previous guide for runtime checks

## Prerequisites { #prerequisites }

!!! note "Required: Complete gRPC Server Guide"

    This guide assumes you have completed **[gRPC Server with Kora](grpc-server.md)** and **[HTTP Client with Kora](http-client.md)**, and already understand protobuf code generation, unary RPC methods, and the repository/service layering from the earlier server guides.

    If you haven't completed the gRPC server guide yet, do that first, because this guide reuses the same protobuf contract and shows how a client calls that server.

## Overview { #overview }

In the server guide, the generated contract was used to implement a service.

In the client guide, the same generated contract is used to call that service.

This is one of the biggest strengths of gRPC:

- one shared contract
- generated code on both sides
- less risk of transport mismatch

The client-side architecture has three layers:

- the protobuf contract describes the remote API
- the generated gRPC stub performs the transport call
- your Kora component wraps the stub in application-friendly methods

That wrapper is important. Generated stubs are transport-oriented: they speak protobuf request and response types, deadlines, channels, and gRPC statuses. Application code usually wants clearer
methods such as `createUser(...)` or `getUsers(...)`, plus domain-level error handling. This guide keeps that boundary visible so the generated client does not leak everywhere in your codebase.

### How a gRPC Client Differs from HTTP { #grpc-client-differs-http }

A handwritten HTTP client usually starts from a URL and an HTTP exchange. The client code decides which path to call, which method to use, which headers to send, how to serialize JSON, and how to
interpret the response.

- URL paths
- JSON payload shapes
- response parsing
- error mapping

A gRPC client starts from a compiled service contract instead. The `.proto` file defines the available RPC methods and message types, and the generated stub exposes those methods as code. The client
does not need to remember that `GetUser` maps to a particular URL shape, because there is no resource path to assemble in application code. The generated stub already knows the RPC method name, the
service name, the message encoder, and the expected response type.

Instead of manually assembling requests, you typically:

- build a protobuf request object
- call a generated stub method
- receive a typed protobuf response

The strongest difference is not only binary encoding versus JSON. The stronger difference is that gRPC moves the client/server agreement into generated code:

- method names are part of the protobuf service definition
- request and response fields are part of protobuf messages
- missing or renamed fields are caught earlier by compilation and schema evolution rules
- client code calls a generated API instead of a hand-written path
- server code implements generated service methods instead of matching route annotations

HTTP clients often model failure around response status codes such as `404`, `409`, or `500`. gRPC clients usually model failure around gRPC statuses such
as `NOT_FOUND`, `INVALID_ARGUMENT`, `UNAVAILABLE`, or `DEADLINE_EXCEEDED`. That changes error handling: application code usually catches gRPC status exceptions or maps them at the wrapper boundary,
then exposes domain-friendly behavior to the rest of the service.

Connection behavior also feels different. HTTP/JSON clients often treat each request as an independent resource call. gRPC clients are built around channels and stubs. A channel represents the
connection target and transport configuration, while a stub is the generated client facade used to make calls. This is why the guide wraps the generated stub inside `UserGrpcClient`: the rest of the
application should not need to know about channels, protobuf builders, or gRPC status details.

That does not remove the need for client-side application code. It changes what that code is responsible for. Instead of manually handling low-level transport details, your client service becomes an
adapter between generated transport types and the application model.

## Protobuf API { #protobuf-api }

The first key idea is that the client does **not** invent a new contract.

It uses the same `user_service.proto` as the server:

??? example "Protobuf contract"

    ```protobuf title="src/main/proto/user_service.proto"
    syntax = "proto3";
    
    package ru.tinkoff.kora.guide.grpcserver;
    option java_multiple_files = true;
    
    import "google/protobuf/empty.proto";
    import "google/protobuf/timestamp.proto";
    
    service UserService {
      rpc CreateUser(CreateUserRequest) returns (UserResponse) {}
      rpc GetUser(GetUserRequest) returns (UserResponse) {}
      rpc GetUsers(GetUsersRequest) returns (GetUsersResponse) {}
      rpc UpdateUser(UpdateUserRequest) returns (UserResponse) {}
      rpc DeleteUser(DeleteUserRequest) returns (google.protobuf.Empty) {}
    }
    
    message CreateUserRequest {
      string name = 1;
      string email = 2;
    }
    
    message GetUserRequest {
      string user_id = 1;
    }
    
    message GetUsersRequest {
      int32 page = 1;
      int32 size = 2;
      string sort = 3;
    }
    
    message GetUsersResponse {
      repeated UserResponse users = 1;
    }
    
    message UpdateUserRequest {
      string user_id = 1;
      string name = 2;
      string email = 3;
    }
    
    message DeleteUserRequest {
      string user_id = 1;
    }
    
    message UserResponse {
      string id = 1;
      string name = 2;
      string email = 3;
      google.protobuf.Timestamp created_at = 4;
    }
    ```

That shared contract is the whole point:

- the server and the client are compiled against the same transport model
- you do not hand-maintain duplicate request and response schemas

## Dependencies { #dependencies }

Now add the client-side Kora module and protobuf support.

===! ":fontawesome-brands-java: `Java`"

    Update `build.gradle`:

    ```groovy title="build.gradle"
    plugins {
        id "application"
        id "com.google.protobuf" version "0.9.4"
    }

    dependencies {
        compileOnly "javax.annotation:javax.annotation-api:1.3.2"
        annotationProcessor "ru.tinkoff.kora:annotation-processors"

        implementation "ru.tinkoff.kora:config-hocon"
        implementation "ru.tinkoff.kora:grpc-client"
        implementation "ru.tinkoff.kora:http-server-undertow"
        implementation "ru.tinkoff.kora:json-module"
        implementation "ru.tinkoff.kora:logging-logback"
        implementation "io.grpc:grpc-protobuf:1.74.0"

        testRuntimeOnly platform("org.junit:junit-bom:$junitVersion")
        testRuntimeOnly "org.junit.platform:junit-platform-launcher"
        testImplementation platform("org.junit:junit-bom:$junitVersion")
        testImplementation "io.grpc:grpc-inprocess:1.74.0"
        testImplementation "org.junit.jupiter:junit-jupiter"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update `build.gradle.kts`:

    ```kotlin title="build.gradle.kts"
    import com.google.protobuf.gradle.id

    plugins {
        id("org.jetbrains.kotlin.jvm")
        id("com.google.devtools.ksp")
        id("application")
        id("com.google.protobuf") version "0.9.4"
    }

    dependencies {
        compileOnly("javax.annotation:javax.annotation-api:1.3.2")
        ksp("ru.tinkoff.kora:symbol-processors")

        implementation("ru.tinkoff.kora:config-hocon")
        implementation("ru.tinkoff.kora:grpc-client")
        implementation("ru.tinkoff.kora:http-server-undertow")
        implementation("ru.tinkoff.kora:json-module")
        implementation("ru.tinkoff.kora:logging-logback")
        implementation("io.grpc:grpc-protobuf:1.74.0")

        testRuntimeOnly(platform("org.junit:junit-bom:${property("junitVersion")}"))
        testRuntimeOnly("org.junit.platform:junit-platform-launcher")
        testImplementation(platform("org.junit:junit-bom:${property("junitVersion")}"))
        testImplementation("io.grpc:grpc-inprocess:1.74.0")
        testImplementation("org.junit.jupiter:junit-jupiter")
    }
    ```

The important difference from the server module is:

- `ru.tinkoff.kora:grpc-client` instead of `ru.tinkoff.kora:grpc-server`

## Code Generation { #code-generation }

Just like on the server side, Gradle must generate protobuf messages and gRPC types.

===! ":fontawesome-brands-java: `Java`"

    Add to `build.gradle`:

    ```groovy title="build.gradle"
    protobuf {
        protoc { artifact = "com.google.protobuf:protoc:3.25.3" }
        plugins {
            grpc { artifact = "io.grpc:protoc-gen-grpc-java:1.74.0" }
        }
        generateProtoTasks {
            all()*.plugins { grpc {} }
        }
    }

    sourceSets {
        main {
            java {
                srcDirs "build/generated/source/proto/main/grpc"
                srcDirs "build/generated/source/proto/main/java"
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Add to `build.gradle.kts`:

    ```kotlin title="build.gradle.kts"
    protobuf {
        protoc { artifact = "com.google.protobuf:protoc:3.25.3" }
        plugins {
            id("grpc") { artifact = "io.grpc:protoc-gen-grpc-java:1.74.0" }
        }
        generateProtoTasks {
            all().forEach { task ->
                task.plugins { id("grpc") }
            }
        }
    }

    sourceSets {
        main {
            java {
                srcDirs("build/generated/source/proto/main/grpc", "build/generated/source/proto/main/java")
            }
        }
    }
    ```

This generates:

- protobuf messages such as `CreateUserRequest`
- client stub types such as `UserServiceGrpc.UserServiceBlockingStub`

## Modules { #modules }

For more on gRPC client services, configuration, and stubs, see [gRPC Client: Service](../documentation/grpc-client.md#service).

Now enable the Kora gRPC client runtime in the application graph.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/grpcclient/Application.java"
    package ru.tinkoff.kora.guide.grpcclient;

    import ru.tinkoff.grpc.client.GrpcClientModule;
    import ru.tinkoff.kora.application.graph.KoraApplication;
    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.config.hocon.HoconConfigModule;
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule;
    import ru.tinkoff.kora.json.module.JsonModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        GrpcClientModule,  // <----- Connected module
        UndertowHttpServerModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/grpcclient/Application.kt"
    package ru.tinkoff.kora.guide.grpcclient

    import ru.tinkoff.grpc.client.GrpcClientModule
    import ru.tinkoff.kora.application.graph.KoraApplication
    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.config.hocon.HoconConfigModule
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule
    import ru.tinkoff.kora.json.module.JsonModule
    import ru.tinkoff.kora.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        GrpcClientModule,  // <----- Connected module
        UndertowHttpServerModule

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

Notice that this app also includes a small HTTP server module. That is not because this is an HTTP tutorial. It is there so the companion app can expose a simple HTTP endpoint that exercises all gRPC
client operations in one place.

## Configuration { #config }

Add the gRPC client configuration:

For the full configuration reference, see [HTTP Server](../documentation/http-server.md), [gRPC Client](../documentation/grpc-client.md) and [Logging SLF4J](../documentation/logging-slf4j.md).

===! ":material-code-json: `Hocon`"

    ```javascript title="src/main/resources/application.conf"
    httpServer {
      publicApiHttpPort = 8081 //(1)!
      privateApiHttpPort = 8086 //(2)!
      telemetry.logging.enabled = true //(3)!
    }

    grpcClient {
      UserService {
        url = "http://localhost:8090" //(4)!
        url = ${?GRPC_SERVER_URL} //(5)!
        telemetry.logging.enabled = true //(6)!
      }
    }

    logging {
      levels {
        "ROOT": "INFO" //(7)!
        "ru.tinkoff.kora": "INFO" //(8)!
        "ru.tinkoff.kora.guide.grpcclient": "INFO" //(9)!
      }
    }
    ```

    1. Default public HTTP port used by application endpoints.
    2. Default private HTTP port used by probes, metrics, and management endpoints.
    3. Enables the feature for this configuration section.
    4. Base URL used by the configured client.
    5. Base URL used by the configured client. Optional override from `GRPC_SERVER_URL`.
    6. Enables the feature for this configuration section.
    7. Log level for `ROOT`.
    8. Log level for `ru.tinkoff.kora`.
    9. Log level for `ru.tinkoff.kora.guide.grpcclient`.

=== ":simple-yaml: `YAML`"

    ```yaml title="src/main/resources/application.yaml"
    httpServer:
      publicApiHttpPort: 8081 #(1)!
      privateApiHttpPort: 8086 #(2)!
      telemetry:
        logging:
          enabled: true #(3)!
    grpcClient:
      UserService:
        url: ${?GRPC_SERVER_URL:"http://localhost:8090"} #(4)!
        telemetry:
          logging:
            enabled: true #(5)!
    logging:
      levels:
        ROOT: "INFO" #(6)!
        "ru.tinkoff.kora": "INFO" #(7)!
        "ru.tinkoff.kora.guide.grpcclient": "INFO" #(8)!
    ```

    1. Default public HTTP port used by application endpoints.
    2. Default private HTTP port used by probes, metrics, and management endpoints.
    3. Enables the feature for this configuration section.
    4. Base URL used by the configured client. Uses the shown default and allows `GRPC_SERVER_URL` to override it.
    5. Enables the feature for this configuration section.
    6. Log level for `ROOT`.
    7. Log level for `ru.tinkoff.kora`.
    8. Log level for `ru.tinkoff.kora.guide.grpcclient`.

Two details matter here:

- the client is configured under `grpcClient.UserService`
- the URL uses `http://...` so the Kora gRPC client runs in plaintext mode for this local guide setup

## Wrap the Stub in a Service { #wrap-stub-service }

Generated stubs are useful, but your application usually still wants a small client-side service layer.

That layer can:

- hide protobuf request construction
- map protobuf transport objects into app DTOs
- centralize client-side transport usage

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/grpcclient/service/UserClientService.java"
    package ru.tinkoff.kora.guide.grpcclient.service;

    import java.time.LocalDateTime;
    import java.time.ZoneOffset;
    import java.util.List;

    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.grpcclient.dto.UserRequest;
    import ru.tinkoff.kora.guide.grpcclient.dto.UserResponse;
    import ru.tinkoff.kora.guide.grpcserver.CreateUserRequest;
    import ru.tinkoff.kora.guide.grpcserver.DeleteUserRequest;
    import ru.tinkoff.kora.guide.grpcserver.GetUserRequest;
    import ru.tinkoff.kora.guide.grpcserver.GetUsersRequest;
    import ru.tinkoff.kora.guide.grpcserver.UpdateUserRequest;
    import ru.tinkoff.kora.guide.grpcserver.UserServiceGrpc;

    @Component
    public final class UserClientService {

        private final UserServiceGrpc.UserServiceBlockingStub userService;

        public UserClientService(UserServiceGrpc.UserServiceBlockingStub userService) {
            this.userService = userService;
        }

        public UserResponse createUser(UserRequest request) {
            return toDto(this.userService.createUser(CreateUserRequest.newBuilder()
                .setName(request.name())
                .setEmail(request.email())
                .build()));
        }

        public UserResponse getUser(String userId) {
            return toDto(this.userService.getUser(GetUserRequest.newBuilder()
                .setUserId(userId)
                .build()));
        }

        public List<UserResponse> getUsers(int page, int size, String sort) {
            return this.userService.getUsers(GetUsersRequest.newBuilder()
                    .setPage(page)
                    .setSize(size)
                    .setSort(sort)
                    .build())
                .getUsersList().stream()
                .map(this::toDto)
                .toList();
        }

        public UserResponse updateUser(String userId, UserRequest request) {
            return toDto(this.userService.updateUser(UpdateUserRequest.newBuilder()
                .setUserId(userId)
                .setName(request.name())
                .setEmail(request.email())
                .build()));
        }

        public void deleteUser(String userId) {
            this.userService.deleteUser(DeleteUserRequest.newBuilder()
                .setUserId(userId)
                .build());
        }

        private UserResponse toDto(ru.tinkoff.kora.guide.grpcserver.UserResponse response) {
            return new UserResponse(
                response.getId(),
                response.getName(),
                response.getEmail(),
                LocalDateTime.ofEpochSecond(
                    response.getCreatedAt().getSeconds(),
                    response.getCreatedAt().getNanos(),
                    ZoneOffset.UTC));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/grpcclient/service/UserClientService.kt"
    package ru.tinkoff.kora.guide.grpcclient.service

    import java.time.LocalDateTime
    import java.time.ZoneOffset
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.grpcclient.dto.UserRequest
    import ru.tinkoff.kora.guide.grpcclient.dto.UserResponse
    import ru.tinkoff.kora.guide.grpcserver.CreateUserRequest
    import ru.tinkoff.kora.guide.grpcserver.DeleteUserRequest
    import ru.tinkoff.kora.guide.grpcserver.GetUserRequest
    import ru.tinkoff.kora.guide.grpcserver.GetUsersRequest
    import ru.tinkoff.kora.guide.grpcserver.UpdateUserRequest
    import ru.tinkoff.kora.guide.grpcserver.UserServiceGrpc

    @Component
    class UserClientService(
        private val userService: UserServiceGrpc.UserServiceBlockingStub
    ) {

        fun createUser(request: UserRequest): UserResponse {
            return toDto(
                userService.createUser(
                    CreateUserRequest.newBuilder()
                        .setName(request.name)
                        .setEmail(request.email)
                        .build()
                )
            )
        }

        fun getUser(userId: String): UserResponse {
            return toDto(userService.getUser(GetUserRequest.newBuilder().setUserId(userId).build()))
        }

        fun getUsers(page: Int, size: Int, sort: String): List<UserResponse> {
            return userService.getUsers(
                GetUsersRequest.newBuilder()
                    .setPage(page)
                    .setSize(size)
                    .setSort(sort)
                    .build()
            ).usersList.map(::toDto)
        }

        fun updateUser(userId: String, request: UserRequest): UserResponse {
            return toDto(
                userService.updateUser(
                    UpdateUserRequest.newBuilder()
                        .setUserId(userId)
                        .setName(request.name)
                        .setEmail(request.email)
                        .build()
                )
            )
        }

        fun deleteUser(userId: String) {
            userService.deleteUser(DeleteUserRequest.newBuilder().setUserId(userId).build())
        }

        private fun toDto(response: ru.tinkoff.kora.guide.grpcserver.UserResponse): UserResponse {
            return UserResponse(
                response.id,
                response.name,
                response.email,
                LocalDateTime.ofEpochSecond(response.createdAt.seconds, response.createdAt.nanos, ZoneOffset.UTC)
            )
        }
    }
    ```

The important idea here is the same one we use in many other guides: generated transport code is useful, but the rest of your application should still consume a small, readable abstraction.

## Check Controller { #check-controller }

The companion app includes a tiny HTTP controller that calls the gRPC client and returns a summary.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/grpcclient/controller/ClientTestController.java"
    package ru.tinkoff.kora.guide.grpcclient.controller;

    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.grpcclient.dto.UserRequest;
    import ru.tinkoff.kora.guide.grpcclient.service.UserClientService;
    import ru.tinkoff.kora.http.common.HttpMethod;
    import ru.tinkoff.kora.http.common.annotation.HttpRoute;
    import ru.tinkoff.kora.http.server.common.annotation.HttpController;
    import ru.tinkoff.kora.json.common.annotation.Json;

    @Component
    @HttpController
    public final class ClientTestController {

        private final UserClientService userClientService;

        public ClientTestController(UserClientService userClientService) {
            this.userClientService = userClientService;
        }

        @HttpRoute(method = HttpMethod.POST, path = "/client/test-all-user-endpoints")
        @Json
        public TestResults testAllUserEndpoints() {
            try {
                var created = this.userClientService.createUser(new UserRequest("Client Demo User", "client-demo@example.com"));
                boolean userCreated = created != null;

                var fetched = this.userClientService.getUser(created.id());
                boolean userFetched = created.id().equals(fetched.id());

                var users = this.userClientService.getUsers(0, 10, "name");
                boolean usersListed = users.stream().anyMatch(user -> user.id().equals(created.id()));

                var updated = this.userClientService.updateUser(created.id(),
                    new UserRequest("Updated Client Demo User", "updated-client-demo@example.com"));
                boolean userUpdated = "Updated Client Demo User".equals(updated.name());

                this.userClientService.deleteUser(created.id());
                boolean userDeleted = true;

                boolean allTestsPassed = userCreated && userFetched && usersListed && userUpdated && userDeleted;
                return new TestResults(userCreated, userFetched, usersListed, userUpdated, userDeleted, allTestsPassed, null);
            } catch (Exception exception) {
                return new TestResults(false, false, false, false, false, false, exception.getMessage());
            }
        }

        @Json
        public record TestResults(
            boolean userCreated,
            boolean userFetched,
            boolean usersListed,
            boolean userUpdated,
            boolean userDeleted,
            boolean allTestsPassed,
            String error) {
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/grpcclient/controller/ClientTestController.kt"
    package ru.tinkoff.kora.guide.grpcclient.controller

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.grpcclient.dto.UserRequest
    import ru.tinkoff.kora.guide.grpcclient.service.UserClientService
    import ru.tinkoff.kora.http.common.HttpMethod
    import ru.tinkoff.kora.http.common.annotation.HttpRoute
    import ru.tinkoff.kora.http.server.common.annotation.HttpController
    import ru.tinkoff.kora.json.common.annotation.Json

    @Component
    @HttpController
    class ClientTestController(
        private val userClientService: UserClientService
    ) {

        @HttpRoute(method = HttpMethod.POST, path = "/client/test-all-user-endpoints")
        @Json
        fun testAllUserEndpoints(): TestResults {
            return try {
                val created = userClientService.createUser(UserRequest("Client Demo User", "client-demo@example.com"))
                val fetched = userClientService.getUser(created.id)
                val users = userClientService.getUsers(0, 10, "name")
                val updated = userClientService.updateUser(
                    created.id,
                    UserRequest("Updated Client Demo User", "updated-client-demo@example.com")
                )
                userClientService.deleteUser(created.id)

                val userCreated = true
                val userFetched = created.id == fetched.id
                val usersListed = users.any { it.id == created.id }
                val userUpdated = updated.name == "Updated Client Demo User"
                val userDeleted = true
                val allTestsPassed = userCreated && userFetched && usersListed && userUpdated && userDeleted
                TestResults(userCreated, userFetched, usersListed, userUpdated, userDeleted, allTestsPassed, null)
            } catch (exception: Exception) {
                TestResults(false, false, false, false, false, false, exception.message)
            }
        }

        @Json
        data class TestResults(
            val userCreated: Boolean,
            val userFetched: Boolean,
            val usersListed: Boolean,
            val userUpdated: Boolean,
            val userDeleted: Boolean,
            val allTestsPassed: Boolean,
            val error: String?
        )
    }
    ```

This controller is not the “real” point of the guide. It is just a convenient harness that makes it easy to verify the client end-to-end.

## Run Application { #run-app }

Start the server app from the previous guide first:

```bash
./gradlew run
```

Then start the client app:

```bash
./gradlew run
```

Now call the local HTTP helper endpoint:

```bash
curl -X POST http://localhost:8081/client/test-all-user-endpoints
```

That HTTP call is only a trigger. Inside the app, the real work is being done through the generated gRPC client stub.

## Testing { #testing }

The client module tests do not need Docker or a full external server process.

Instead, they use:

- `InProcessServerBuilder`
- `InProcessChannelBuilder`

That approach is especially good for gRPC client tests because it lets you:

- simulate exact server responses
- keep the tests fast
- focus on client behavior instead of external infrastructure

Run the tests with:

```bash
./gradlew test
```

## Best Practices { #best-practices }

- Reuse the exact same `.proto` contract between client and server.
- Wrap generated stubs in a small application service instead of leaking them everywhere.
- Keep protobuf message construction close to the gRPC client boundary.
- Use `InProcessServer` for focused client tests when you want fast and deterministic feedback.
- Treat gRPC transport models as transport models, even if they look similar to your app DTOs.
- Annotate handwritten DTOs with `@Json` only when they cross an HTTP/JSON boundary; generated protobuf messages do not need JSON annotations.

## Summary { #summary }

In this guide you built a unary gRPC client that mirrors the server from the previous guide.

The key ideas were:

- reuse the shared protobuf contract
- inject generated gRPC stubs through Kora
- wrap them in a `UserClientService`
- test the client with in-process gRPC infrastructure

## Key Concepts { #key-concepts }

- how a Kora gRPC client is wired into the application graph
- how generated blocking stubs are used for unary RPC calls
- why a small client-side service layer is still useful
- how the same protobuf contract can power both sides of the system
- why `InProcessServer` is a strong fit for gRPC client tests

## Troubleshooting { #troubleshooting }

**Client cannot connect:**

Verify that the server app is running and that the client `application.conf` points to the correct host and gRPC port.

**Generated stub is missing:**

Run `./gradlew clean classes` after changing `user_service.proto` and check the protobuf source set configuration.

**Request succeeds in tests but not at runtime:**

Compare the in-process test setup with the real client configuration, especially host, port, and service package names.

## What's Next? { #whats-next }

- [HTTP Server Advanced](http-server-advanced.md) if you have not completed it yet.
- [Advanced gRPC Server](grpc-server-advanced.md) after HTTP Server Advanced, to add streaming endpoints that a richer client can consume.
- [Advanced gRPC Client](grpc-client-advanced.md) after Advanced gRPC Server, to work with streaming, metadata auth, and client interceptors.
- [Resilient Patterns](resilient.md) to protect RPC calls with retry, timeout, circuit breaker, and fallback.
- [Observability](observability.md) to trace gRPC calls and measure client behavior.

## Help { #help }

If something does not work:

- compare with [Kora Java gRPC Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-grpc-client-app) and [Kora Kotlin gRPC Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-grpc-client-app)
- check the [gRPC Client documentation](../documentation/grpc-client.md)
- verify the server from [gRPC Server](grpc-server.md) is running on port `8090`
- make sure client and server use the same `.proto` contract
