---
search:
  exclude: true
title: gRPC Client with Kora
summary: Build a Kora 2.0 gRPC client that consumes a unary CRUD service through injected generated stubs
description: "Step-by-step Kora gRPC client: the io.koraframework:grpc-client module and GrpcClientModule, the protobuf Gradle plugin, generated UserServiceGrpc stubs injected without a @Tag, the grpcClient.<Service> configuration path derived from the protobuf service name, the url scheme choosing plaintext or TLS, timeout applied as a call deadline, wrapping a BlockingStub in an application service, and in-process client tests."
agent:
  use_when: "Use this file for questions about calling a gRPC service from Kora step by step: GrpcClientModule, injecting UserServiceGrpc.UserServiceBlockingStub / FutureStub / async Stub / Kotlin coroutine stubs, the grpcClient.UserService configuration section, url, timeout and telemetry keys, StatusRuntimeException and Status.Code handling, the io.koraframework:grpc-client and io.grpc:grpc-protobuf dependencies, the protobuf Gradle plugin, and client tests with InProcessServerBuilder."
tags: grpc-client, protobuf, rpc, microservices
---

# gRPC Client with Kora { #grpc-client-kora }

This guide introduces unary gRPC clients with Kora. It covers how the same `.proto` contract generates client stubs and message types, how Kora builds a channel per service and injects ready-to-use
stubs into the application graph, and how a small service wrapper turns stub calls into application-level operations. You will also see how gRPC statuses, deadlines, and generated request builders
shape client code differently from declarative HTTP clients.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java gRPC Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-grpc-client-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin gRPC Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-grpc-client-app).

## What You'll Build { #youll-build }

You will build a separate unary gRPC client application with:

- the same `user_service.proto` contract used by the server
- generated protobuf request and response types
- an injected Kora gRPC client stub for `UserService`
- a small application service that wraps `CreateUser`, `GetUser`, `GetUsers`, `UpdateUser`, and `DeleteUser`
- HTTP trigger routes that make the client easy to exercise locally
- runtime checks against a running gRPC server

## What You'll Need { #youll-need }

- JDK 25 or later
- Gradle 9+ (the reference applications use Gradle Wrapper `9.5.1`)
- A text editor or IDE
- A running gRPC server from the previous guide for runtime checks

Kora artifacts are compiled for Java 25, so the JDK that compiles your code must be 25 or newer.

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

Two runtime details are worth knowing before you start, because they explain what Kora actually builds for you:

- Kora builds one `ManagedChannel` per protobuf service through `ManagedChannelLifecycle`, and the transport is **gRPC OkHttp**. You do not add a transport artifact yourself; `io.koraframework:grpc-client`
  already brings `grpc-okhttp` and `grpc-stub`.
- Every generated stub is injectable **without** a `@Tag`. Kora resolves the tagged `Channel` behind the scenes, so a constructor parameter of type `UserServiceGrpc.UserServiceBlockingStub` is enough.

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
as `NOT_FOUND`, `INVALID_ARGUMENT`, `UNAVAILABLE`, or `DEADLINE_EXCEEDED`. That changes error handling: application code usually catches `StatusRuntimeException` and branches on the status code, or
maps it at the wrapper boundary, then exposes domain-friendly behavior to the rest of the service.

Connection behavior also feels different. HTTP/JSON clients often treat each request as an independent resource call. gRPC clients are built around channels and stubs. A channel represents the
connection target and transport configuration, while a stub is the generated client facade used to make calls. This is why the guide wraps the generated stub inside `UserClientService`: the rest of
the application should not need to know about channels, protobuf builders, or gRPC status details.

That does not remove the need for client-side application code. It changes what that code is responsible for. Instead of manually handling low-level transport details, your client service becomes an
adapter between generated transport types and the application model.

## Protobuf API { #protobuf-api }

The first key idea is that the client does **not** invent a new contract.

It uses the same `user_service.proto` as the server:

??? example "Protobuf contract"

    ```protobuf title="src/main/proto/user_service.proto"
    syntax = "proto3";

    package io.koraframework.guide.grpcserver;
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
- the `proto` package stays `io.koraframework.guide.grpcserver`, so the generated classes keep the server's package even though this is the client application

## Dependencies { #dependencies }

Now add the client-side Kora module and protobuf support.

Versions of Kora modules come from the Kora BOM `io.koraframework:kora-bom`, so individual Kora artifacts are declared without a version:

```properties title="gradle.properties"
koraVersion=2.0.0.RC1
junitVersion=6.1.3
```

===! ":fontawesome-brands-java: `Java`"

    Update `build.gradle`:

    ```groovy title="build.gradle"
    plugins {
        id "application"
        id "com.google.protobuf" version "0.10.0"
    }

    configurations {
        koraBom
        compileOnly.extendsFrom(koraBom)
        annotationProcessor.extendsFrom(koraBom)
        implementation.extendsFrom(koraBom)
        testCompileOnly.extendsFrom(koraBom)
        testAnnotationProcessor.extendsFrom(koraBom)
        testImplementation.extendsFrom(koraBom)
    }

    dependencies {
        koraBom platform("io.koraframework:kora-bom:$koraVersion")

        compileOnly "javax.annotation:javax.annotation-api:1.3.2"
        annotationProcessor "io.koraframework:annotation-processors"

        implementation "io.koraframework:config-hocon"
        implementation "io.koraframework:grpc-client"
        implementation "io.koraframework:http-server-undertow"
        implementation "io.koraframework:json-common"
        implementation "io.koraframework:logging-logback"
        implementation "io.grpc:grpc-protobuf:1.83.1"

        testRuntimeOnly platform("org.junit:junit-bom:$junitVersion")
        testRuntimeOnly "org.junit.platform:junit-platform-launcher"
        testImplementation platform("org.junit:junit-bom:$junitVersion")
        testImplementation "io.grpc:grpc-inprocess:1.83.1"
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
        id("com.google.protobuf") version "0.10.0"
    }

    dependencies {
        implementation(platform("io.koraframework:kora-bom:${property("koraVersion")}"))

        compileOnly("javax.annotation:javax.annotation-api:1.3.2")
        ksp("io.koraframework:symbol-processors:${property("koraVersion")}")

        implementation("io.koraframework:config-hocon")
        implementation("io.koraframework:grpc-client")
        implementation("io.koraframework:http-server-undertow")
        implementation("io.koraframework:json-common")
        implementation("io.koraframework:logging-logback")
        implementation("io.grpc:grpc-protobuf:1.83.1")

        testRuntimeOnly(platform("org.junit:junit-bom:${property("junitVersion")}"))
        testRuntimeOnly("org.junit.platform:junit-platform-launcher")
        testImplementation(platform("org.junit:junit-bom:${property("junitVersion")}"))
        testImplementation("io.grpc:grpc-inprocess:1.83.1")
        testImplementation("org.junit.jupiter:junit-jupiter")
    }
    ```

Why these dependencies matter:

- `io.koraframework:grpc-client` replaces `io.koraframework:grpc-server` — it builds the channel, applies interceptors, and registers the generated stubs in the graph
- `io.grpc:grpc-protobuf` gives runtime support for protobuf message serialization
- `javax.annotation:javax.annotation-api` is needed only at compile time, because generated stubs reference `@javax.annotation.Generated`
- `io.koraframework:http-server-undertow` and `io.koraframework:json-common` are here only so the guide can expose a small HTTP endpoint that triggers the gRPC calls
- `io.grpc:grpc-inprocess` gives the tests an in-memory gRPC server and channel, with no ports and no Docker

!!! warning "Keep every `io.grpc` artifact on one version"

    The gRPC runtime shipped with `io.koraframework:grpc-client` is `1.83.1`. Every other `io.grpc` artifact you declare — `grpc-protobuf` and anything in test scope such as `grpc-inprocess` — must use
    exactly that version. A pinned older version compiles fine and fails only at runtime with
    `AbstractMethodError: ... does not define or inherit an implementation of the resolved method`.

## Code Generation { #code-generation }

Just like on the server side, Gradle must generate protobuf messages and gRPC types.

===! ":fontawesome-brands-java: `Java`"

    Add to `build.gradle`:

    ```groovy title="build.gradle"
    protobuf {
        protoc { artifact = "com.google.protobuf:protoc:4.35.1" }
        plugins {
            grpc { artifact = "io.grpc:protoc-gen-grpc-java:1.83.1" }
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
        protoc { artifact = "com.google.protobuf:protoc:4.35.1" }
        plugins {
            id("grpc") { artifact = "io.grpc:protoc-gen-grpc-java:1.83.1" }
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

The plugin emits **Java** classes even in a Kotlin project, which is why the generated directories are registered in the `java` source set in both variants.

### Kotlin Coroutine Stubs { #kotlin-coroutine-stubs }

The Java stubs above work in Kotlin exactly as they do in Java, and this guide uses them in both languages so the two variants stay comparable.

If you prefer idiomatic coroutines, add the [gRPC Kotlin generator](https://github.com/grpc/grpc-kotlin) on top of the setup above. Kora supports the generated coroutine stubs as first-class
injectable components:

```kotlin title="build.gradle.kts"
dependencies {
    implementation("io.grpc:grpc-kotlin-stub:1.5.0")
}

protobuf {
    plugins {
        id("grpckt") { artifact = "io.grpc:protoc-gen-grpc-kotlin:1.5.0:jdk8@jar" }
    }
    generateProtoTasks {
        all().forEach { task ->
            task.plugins { id("grpc"); id("grpckt") }
        }
    }
}

kotlin {
    sourceSets.main { kotlin.srcDir("build/generated/source/proto/main/grpckt") }
}
```

The generated `UserServiceGrpcKt.UserServiceCoroutineStub` is annotated with `@StubFor`, and the Kora symbol processor emits a `@Module` next to it that binds the stub to the same tagged `Channel` as
the Java stubs. Injecting it needs no extra wiring, and it exposes unary calls as `suspend` functions and streaming calls as `Flow<T>`. See
[gRPC Client: Stub types](../documentation/grpc-client.md#stub-types) for the full list.

## Modules { #modules }

For more on gRPC client services, configuration, and stubs, see [gRPC Client: Service](../documentation/grpc-client.md#service).

Now enable the Kora gRPC client runtime in the application graph.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/grpcclient/Application.java"
    package io.koraframework.guide.grpcclient;

    import io.koraframework.application.graph.KoraApplication;
    import io.koraframework.common.annotation.KoraApp;
    import io.koraframework.config.hocon.HoconConfigModule;
    import io.koraframework.grpc.client.GrpcClientModule;
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule;
    import io.koraframework.json.common.JsonModule;
    import io.koraframework.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        GrpcClientModule,  // <----- Connected module
        UndertowPublicHttpServerModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/grpcclient/Application.kt"
    package io.koraframework.guide.grpcclient

    import io.koraframework.application.graph.KoraApplication
    import io.koraframework.common.annotation.KoraApp
    import io.koraframework.config.hocon.HoconConfigModule
    import io.koraframework.grpc.client.GrpcClientModule
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule
    import io.koraframework.json.common.JsonModule
    import io.koraframework.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        GrpcClientModule,  // <----- Connected module
        UndertowPublicHttpServerModule

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

`GrpcClientModule` does not create a client by itself. It contributes the pieces every client needs — the channel factory, the telemetry factory, and the config value mapper — and the annotation
processor (or KSP) extension generates the channel and the stubs for each service you actually inject.

Notice that this app also includes a small HTTP server module. That is not because this is an HTTP tutorial. It is there so the companion app can expose a simple HTTP endpoint that exercises all gRPC
client operations in one place.

## Configuration { #config }

This application is a standalone Kora service, so it needs its own ports.

We will use:

- `8090` for the gRPC server app from `grpc-server.md`
- `8081` for the client app public HTTP server
- `8086` for the client app system HTTP server (probes, metrics)
- `grpcClient.UserService.url` as the target of the generated client

For the full configuration reference, see [HTTP Server](../documentation/http-server.md), [gRPC Client](../documentation/grpc-client.md) and [Logging SLF4J](../documentation/logging-slf4j.md).

===! ":material-code-json: `Hocon`"

    ```javascript title="src/main/resources/application.conf"
    httpServer {
      port = 8081 //(1)!
      system.port = 8086 //(2)!
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
        "io.koraframework": "INFO" //(8)!
        "io.koraframework.guide.grpcclient": "INFO" //(9)!
      }
    }
    ```

    1. Public HTTP server port used by the local guide endpoint (default: `8080`).
    2. System HTTP server port used by probes and metrics (default: `8085`).
    3. Enables request logging for the public HTTP server (default: `false`).
    4. Target URL of the gRPC server (required, no default).
    5. Optional override of the target URL from the `GRPC_SERVER_URL` environment variable.
    6. Enables gRPC call logging for this client (default: `false`).
    7. Log level for `ROOT`.
    8. Log level for `io.koraframework`.
    9. Log level for `io.koraframework.guide.grpcclient`.

=== ":simple-yaml: `YAML`"

    ```yaml title="src/main/resources/application.yaml"
    httpServer:
      port: 8081 #(1)!
      system:
        port: 8086 #(2)!
      telemetry:
        logging:
          enabled: true #(3)!
    grpcClient:
      UserService:
        url: ${GRPC_SERVER_URL:http://localhost:8090} #(4)!
        telemetry:
          logging:
            enabled: true #(5)!
    logging:
      levels:
        ROOT: "INFO" #(6)!
        "io.koraframework": "INFO" #(7)!
        "io.koraframework.guide.grpcclient": "INFO" #(8)!
    ```

    1. Public HTTP server port used by the local guide endpoint (default: `8080`).
    2. System HTTP server port used by probes and metrics (default: `8085`).
    3. Enables request logging for the public HTTP server (default: `false`).
    4. Target URL of the gRPC server (required, no default). Uses the shown default and allows `GRPC_SERVER_URL` to override it.
    5. Enables gRPC call logging for this client (default: `false`).
    6. Log level for `ROOT`.
    7. Log level for `io.koraframework`.
    8. Log level for `io.koraframework.guide.grpcclient`.

Three details matter here.

**The config path is derived from the protobuf service name.** Kora takes the generated `UserServiceGrpc.SERVICE_NAME` constant — the fully qualified name `io.koraframework.guide.grpcserver.UserService` —
and keeps only the part after the last dot. That is why the section is `grpcClient.UserService` and not `grpcClient.io.koraframework.guide.grpcserver.UserService`. Rename the service in the `.proto`
file and this path changes with it.

**The URL scheme selects the transport.** `http://` builds a plaintext channel (default port `80` if the port is omitted), `https://` builds a TLS channel (default port `443`). Any other scheme fails
the graph at startup with `Unsupported gRPC client URL scheme`. This guide talks to a local server, so plaintext `http://localhost:8090` is what we want.

**`url` is required, everything else is optional.** A missing `url` fails the graph on start. Timeouts (`timeout`), keepalive pings, and load balancing are all off unless you set them — see
[gRPC Client: Configuration](../documentation/grpc-client.md#configuration) for the complete list.

## Stub Types { #stub-types }

The protobuf plugin generates several stub classes for one service, and Kora can inject each of them directly. No `@Tag` is needed on the stub itself — Kora resolves the tagged `Channel` behind the
scenes:

| Stub type                        | Call model                                                                        | When to use                                      |
|----------------------------------|-----------------------------------------------------------------------------------|--------------------------------------------------|
| `UserServiceBlockingStub`        | Synchronous; returns the response directly (or an `Iterator` for server streaming) | Blocking code, simplest call style               |
| `UserServiceFutureStub`          | Asynchronous; returns a `ListenableFuture<T>` (unary only)                         | Non-blocking code built on `ListenableFuture`    |
| `UserServiceStub` (async)        | Asynchronous; delivers results through `StreamObserver<T>` callbacks               | Any streaming, callback-style asynchronous calls |
| `UserServiceCoroutineStub`       | `suspend` functions and `Flow<T>`                                                  | Idiomatic Kotlin coroutines                      |

This guide uses the blocking stub, because every RPC in the contract is unary and the calling code reads better without callbacks. The [advanced client guide](grpc-client-advanced.md) adds the async
stub, where it is required for client and bidirectional streaming.

Deadlines are worth understanding before you write the wrapper. If `grpcClient.UserService.timeout` is configured, Kora's always-on `GrpcClientConfigInterceptor` applies it as the call deadline —
but only when the call does not already carry one. A per-call `stub.withDeadlineAfter(2, TimeUnit.SECONDS)` is part of `CallOptions` before any interceptor runs, so it always wins. An expired deadline
surfaces as `StatusRuntimeException` with `Status.Code.DEADLINE_EXCEEDED`.

## Wrap the Stub in a Service { #wrap-stub-service }

Generated stubs are useful, but your application usually still wants a small client-side service layer.

That layer can:

- hide protobuf request construction
- map protobuf transport objects into app DTOs
- centralize client-side transport usage

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/grpcclient/service/UserClientService.java"
    package io.koraframework.guide.grpcclient.service;

    import java.time.LocalDateTime;
    import java.time.ZoneOffset;
    import java.util.List;

    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.grpcclient.dto.UserRequest;
    import io.koraframework.guide.grpcclient.dto.UserResponse;
    import io.koraframework.guide.grpcserver.CreateUserRequest;
    import io.koraframework.guide.grpcserver.DeleteUserRequest;
    import io.koraframework.guide.grpcserver.GetUserRequest;
    import io.koraframework.guide.grpcserver.GetUsersRequest;
    import io.koraframework.guide.grpcserver.UpdateUserRequest;
    import io.koraframework.guide.grpcserver.UserServiceGrpc;

    @Component
    public final class UserClientService {

        private final UserServiceGrpc.UserServiceBlockingStub userService; //(1)!

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

        private UserResponse toDto(io.koraframework.guide.grpcserver.UserResponse response) { //(2)!
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

    1. The generated stub is injected directly, with no `@Tag` and no manual channel construction.
    2. The fully qualified name disambiguates the generated protobuf `UserResponse` from the application DTO of the same name.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/grpcclient/service/UserClientService.kt"
    package io.koraframework.guide.grpcclient.service

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.grpcclient.dto.UserRequest
    import io.koraframework.guide.grpcclient.dto.UserResponse
    import io.koraframework.guide.grpcserver.*
    import java.time.LocalDateTime
    import java.time.ZoneOffset

    @Component
    class UserClientService(
        private val userService: UserServiceGrpc.UserServiceBlockingStub //(1)!
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

        private fun toDto(response: io.koraframework.guide.grpcserver.UserResponse): UserResponse { //(2)!
            return UserResponse(
                response.id,
                response.name,
                response.email,
                LocalDateTime.ofEpochSecond(response.createdAt.seconds, response.createdAt.nanos, ZoneOffset.UTC)
            )
        }
    }
    ```

    1. The generated stub is injected directly, with no `@Tag` and no manual channel construction.
    2. The fully qualified name disambiguates the generated protobuf `UserResponse` from the application DTO of the same name.

The application DTOs are ordinary records and data classes. They carry `@Json` because the check controller below returns them over HTTP — the generated protobuf messages never need JSON annotations:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/grpcclient/dto/UserRequest.java"
    package io.koraframework.guide.grpcclient.dto;

    import io.koraframework.json.common.annotation.Json;

    @Json
    public record UserRequest(String name, String email) {}
    ```

    ```java title="src/main/java/io/koraframework/guide/grpcclient/dto/UserResponse.java"
    package io.koraframework.guide.grpcclient.dto;

    import java.time.LocalDateTime;
    import io.koraframework.json.common.annotation.Json;

    @Json
    public record UserResponse(String id, String name, String email, LocalDateTime createdAt) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/grpcclient/dto/UserRequest.kt"
    package io.koraframework.guide.grpcclient.dto

    import io.koraframework.json.common.annotation.Json

    @Json
    data class UserRequest(val name: String, val email: String)
    ```

    ```kotlin title="src/main/kotlin/io/koraframework/guide/grpcclient/dto/UserResponse.kt"
    package io.koraframework.guide.grpcclient.dto

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

The important idea here is the same one we use in many other guides: generated transport code is useful, but the rest of your application should still consume a small, readable abstraction.

## Check Controller { #check-controller }

The companion app includes a tiny HTTP controller that calls the gRPC client and returns a summary.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/grpcclient/controller/ClientTestController.java"
    package io.koraframework.guide.grpcclient.controller;

    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.grpcclient.dto.UserRequest;
    import io.koraframework.guide.grpcclient.service.UserClientService;
    import io.koraframework.http.common.HttpMethod;
    import io.koraframework.http.common.annotation.HttpRoute;
    import io.koraframework.http.server.common.annotation.HttpController;
    import io.koraframework.json.common.annotation.Json;

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

    ```kotlin title="src/main/kotlin/io/koraframework/guide/grpcclient/controller/ClientTestController.kt"
    package io.koraframework.guide.grpcclient.controller

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.grpcclient.dto.UserRequest
    import io.koraframework.guide.grpcclient.service.UserClientService
    import io.koraframework.http.common.HttpMethod
    import io.koraframework.http.common.annotation.HttpRoute
    import io.koraframework.http.server.common.annotation.HttpController
    import io.koraframework.json.common.annotation.Json

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

This controller is not the "real" point of the guide. It is just a convenient harness that makes it easy to verify the client end-to-end. Catching `Exception` and reporting it as a field is fine for a
demo harness; production code should branch on `StatusRuntimeException.getStatus().getCode()` instead.

## Run Application { #run-app }

Build the generated sources and compile the app:

```bash
./gradlew clean classes
```

Start the server app from the previous guide first, then start the client app:

```bash
./gradlew run
```

Now call the local HTTP helper endpoint:

```bash
curl -X POST http://localhost:8081/client/test-all-user-endpoints
```

That HTTP call is only a trigger. Inside the app, the real work is being done through the generated gRPC client stub.

The channel does not fail the application when the server is down: `ManagedChannelLifecycle` logs a warning if its first connection probe fails, and the call reconnects later. A call made while the
server is unreachable fails with `Status.Code.UNAVAILABLE` instead.

## Testing { #testing }

The client module tests do not need Docker or a full external server process.

Instead, they use:

- `InProcessServerBuilder` to run a fake `UserServiceImplBase` in the same JVM
- `InProcessChannelBuilder` to build a channel to it
- `UserServiceGrpc.newBlockingStub(channel)` to construct the stub that `UserClientService` takes in its constructor

That is possible precisely because the wrapper takes a stub as a constructor parameter: the test builds the stub by hand and never starts the Kora graph. It keeps the tests fast, deterministic, and
focused on client behavior — including error paths, such as asserting `Status.Code.NOT_FOUND` for a missing user.

Run the tests with:

```bash
./gradlew test
```

## Best Practices { #best-practices }

- Reuse the exact same `.proto` contract between client and server.
- Wrap generated stubs in a small application service instead of leaking them everywhere.
- Keep protobuf message construction close to the gRPC client boundary.
- Branch on `StatusRuntimeException.getStatus().getCode()` rather than on exception types.
- Use `InProcessServer` for focused client tests when you want fast and deterministic feedback.
- Treat gRPC transport models as transport models, even if they look similar to your app DTOs.
- Keep every `io.grpc` artifact on the version that ships with `io.koraframework:grpc-client`.
- Annotate handwritten DTOs with `@Json` only when they cross an HTTP/JSON boundary; generated protobuf messages do not need JSON annotations.

## Summary { #summary }

In this guide you built a unary gRPC client that mirrors the server from the previous guide.

The key ideas were:

- reuse the shared protobuf contract
- inject generated gRPC stubs through Kora, with no manual channel wiring
- wrap them in a `UserClientService`
- test the client with in-process gRPC infrastructure

## Key Concepts { #key-concepts }

- how a Kora gRPC client is wired into the application graph
- how the `grpcClient.<Service>` config path is derived from the protobuf service name
- how the `url` scheme selects plaintext or TLS transport
- how generated blocking stubs are used for unary RPC calls
- why a small client-side service layer is still useful
- how the same protobuf contract can power both sides of the system
- why `InProcessServer` is a strong fit for gRPC client tests

## Troubleshooting { #troubleshooting }

**Client cannot connect (`UNAVAILABLE`):**

Verify that the server app is running and that the client `application.conf` points to the correct host and gRPC port. A plaintext/TLS mismatch shows up the same way — `http://` is plaintext,
`https://` is TLS.

**Application fails to start with `Unsupported gRPC client URL scheme`:**

The `url` uses a scheme other than `http` or `https` without an explicit port. Use `http://host:port` or `https://host:port`.

**Configuration is ignored:**

Check the config path. It is the *simple* protobuf service name — `grpcClient.UserService` — not the fully qualified one and not the Java class name.

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

- compare with [Kora Java gRPC Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-grpc-client-app) and [Kora Kotlin gRPC Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-grpc-client-app)
- check the [gRPC Client documentation](../documentation/grpc-client.md)
- verify the server from [gRPC Server](grpc-server.md) is running on port `8090`
- make sure client and server use the same `.proto` contract
