---
search:
  exclude: true
title: gRPC Server with Kora
summary: Build a gRPC CRUD service with Protocol Buffers, generated handlers, and Kora modules
tags: grpc-server, protobuf, rpc, microservices
---

# gRPC Server with Kora { #grpc-server-kora }

This guide introduces unary gRPC servers with Kora. It covers how a Protocol Buffers service contract generates Java stubs and messages, how a Kora gRPC implementation connects those generated types
to application services, and how status errors, metadata, and Protobuf payloads differ from JSON-over-HTTP routes. You will also see how the gRPC server module joins the compile-time dependency graph
alongside repository and service components.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java gRPC Server App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-grpc-server-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin gRPC Server App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-grpc-server-app).

## What You'll Build { #youll-build }

You will build a unary gRPC server application with:

- a `user_service.proto` contract that defines request and response messages
- generated protobuf message classes and gRPC service base types
- a Kora gRPC handler that implements `CreateUser`, `GetUser`, `GetUsers`, `UpdateUser`, and `DeleteUser`
- an in-memory repository and service layer reused behind the gRPC transport
- status-based error handling for missing users
- server configuration and manual checks through `grpcurl`

## What You'll Need { #youll-need }

- JDK 17 or later
- Gradle 7+
- A text editor or IDE
- Optional: `grpcurl` for manual RPC checks

## Prerequisites { #prerequisites }

!!! note "Required: Complete HTTP Server Guide"

    This guide assumes you have completed **[Build an HTTP Server](http-server.md)** and are comfortable with Kora modules, `@Component`, and separating repository, service, and transport layers.

    If you haven't completed the HTTP server guide yet, do that first, because this guide keeps the same application model and replaces only the HTTP/JSON transport with gRPC and Protocol Buffers.

## Overview { #overview }

The guide keeps the repository and service responsibilities from the HTTP server guide, then replaces the HTTP controller with a generated gRPC handler.

That replacement changes the transport layer, not the business model. In HTTP/JSON APIs, a controller usually owns routing details such as paths, methods, request bodies, response codes, and JSON
serialization. In gRPC, the public contract moves into a `.proto` file, and the framework-generated classes become the bridge between network calls and your application service.

Kora fits into that model by wiring the generated gRPC service handler into the application graph. You still write ordinary Java or Kotlin components, but the request and response types come from
protobuf generation instead of handwritten DTOs. The practical flow is:

1. define the RPC contract in protobuf
2. generate Java classes and gRPC base types
3. implement a Kora component that handles the generated service calls
4. map protobuf messages to your existing service layer
5. expose the gRPC server through Kora configuration

### What Is gRPC? { #grpc }

**gRPC** is a remote procedure call protocol and toolchain for building typed service-to-service APIs.

The main idea is different from a typical HTTP API. With HTTP + JSON, you usually design resources and routes:

- `POST /users`
- `GET /users/{userId}`
- `PUT /users/{userId}`
- `DELETE /users/{userId}`

The contract is spread across HTTP methods, paths, status codes, headers, JSON request bodies, JSON response bodies, and documentation such as OpenAPI. That model is flexible and very friendly for
public APIs, browsers, manual debugging, and human-readable traffic.

With gRPC, you design a service interface instead:

```protobuf
service UserService {
  rpc CreateUser(CreateUserRequest) returns (UserResponse) {}
  rpc GetUser(GetUserRequest) returns (UserResponse) {}
}
```

The API looks more like calling methods on a remote service. The client does not assemble a URL path and parse arbitrary JSON by hand. It calls a generated method with a generated request type and
receives a generated response type.

The core difference is where the contract lives.

In HTTP + JSON, the wire format is usually simple and text-based, but the strong contract often lives outside the code unless you add code generation from OpenAPI. In gRPC, the `.proto` file is the
contract first, and both sides compile generated code from that same contract.

That contract-first model gives gRPC three important properties:

- you describe your API in a `.proto` file
- code is generated from that contract
- clients and servers exchange compact binary messages over HTTP/2

The transport is also different. gRPC uses HTTP/2 as the underlying protocol, but it does not feel like a normal JSON REST API:

- messages are serialized with Protocol Buffers instead of JSON
- calls are usually made through generated stubs instead of hand-written URL requests
- errors are represented with gRPC status codes instead of ordinary HTTP response codes in application code
- streaming is part of the RPC model, not an add-on protocol
- HTTP/2 features such as multiplexing and long-lived streams are central to how calls are carried

So gRPC is not "HTTP without JSON" and not just "REST with another serializer". It is a different API style built from these pieces:

- **Protocol Buffers** define the schema and binary encoding.
- **Service definitions** describe RPC methods and message types.
- **Generated code** creates request/response classes, server base types, and client stubs.
- **HTTP/2** carries the calls efficiently over the network.
- **gRPC status codes and metadata** carry errors and call-level context.

In practice, this gives you a very different developer experience from a handwritten REST controller:

- you design operations as RPC methods such as `CreateUser` or `GetUser`
- request and response messages are strongly typed
- the same contract is shared by both the server and the client
- generated code removes a lot of transport boilerplate

This makes gRPC especially useful for service-to-service communication inside distributed systems, where performance, type safety, and contract consistency matter more than human-readable JSON
payloads.

HTTP + JSON is often a better default for public APIs, browser-facing APIs, and endpoints that humans need to inspect directly. gRPC is usually strongest for internal APIs where both sides are
controlled by engineering teams, the schema is shared, and generated clients are acceptable or desirable.

### What Are Protocol Buffers? { #protocol-buffers }

**Protocol Buffers** are the schema language and binary serialization format used by gRPC.

A `.proto` file defines:

- services
- RPC methods
- request messages
- response messages

For example, instead of writing an HTTP controller method by hand, you define a service contract such as:

```protobuf
service UserService {
  rpc CreateUser(CreateUserRequest) returns (UserResponse) {}
}
```

From that contract, the protobuf compiler generates Java classes for:

- `CreateUserRequest`
- `UserResponse`
- `UserServiceGrpc`

Kora then uses those generated types as the basis for your server implementation.

### Why Build gRPC over HTTP? { #build-grpc-over-http }

The easiest way to understand a new transport is to keep the application model stable.

In the [HTTP Server guide](http-server.md), we already introduced:

- `UserRepository`
- `InMemoryUserRepository`
- `UserService`
- user CRUD operations

In this guide we reuse the same learning model, but replace HTTP-specific pieces with gRPC-specific ones:

- `@HttpController` becomes a gRPC handler
- JSON DTO exchange becomes protobuf message exchange
- HTTP status codes become gRPC `Status` errors

That keeps the guide beginner-friendly while still showing real gRPC architecture.

## Dependencies { #dependencies }

We start by adding the gRPC server module and the protobuf Gradle plugin.

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
        implementation "ru.tinkoff.kora:grpc-server"
        implementation "ru.tinkoff.kora:logging-logback"
        implementation "io.grpc:grpc-protobuf:1.74.0"
        implementation "io.grpc:grpc-services:1.74.0"

        testCompileOnly "javax.annotation:javax.annotation-api:1.3.2"
        testAnnotationProcessor "ru.tinkoff.kora:annotation-processors"

        testImplementation platform("org.junit:junit-bom:$junitVersion")
        testImplementation "io.grpc:grpc-netty:1.74.0"
        testImplementation "org.junit.jupiter:junit-jupiter"
        testImplementation "ru.tinkoff.kora:test-junit5"
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
        implementation("ru.tinkoff.kora:grpc-server")
        implementation("ru.tinkoff.kora:logging-logback")
        implementation("io.grpc:grpc-protobuf:1.74.0")
        implementation("io.grpc:grpc-services:1.74.0")

        testCompileOnly("javax.annotation:javax.annotation-api:1.3.2")
        kspTest("ru.tinkoff.kora:symbol-processors")

        testImplementation(platform("org.junit:junit-bom:${property("junitVersion")}"))
        testImplementation("io.grpc:grpc-netty:1.74.0")
        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation("ru.tinkoff.kora:test-junit5")
    }
    ```

Why these dependencies matter:

- `ru.tinkoff.kora:grpc-server` integrates a gRPC server into the Kora application graph
- `io.grpc:grpc-protobuf` gives runtime support for protobuf message serialization
- `io.grpc:grpc-services` is useful for standard gRPC services and reflection-related support
- the protobuf Gradle plugin generates the Java classes from `.proto` files

## Code Generation { #code-generation }

Now we teach Gradle how to turn `.proto` files into Java code.

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

This generates two groups of code:

- protobuf message classes such as `CreateUserRequest`
- gRPC service classes such as `UserServiceGrpc`

That generated code becomes part of your normal application sources.

## Modules { #modules }

Next we enable the gRPC server in the Kora app itself.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/grpcserver/Application.java"
    package ru.tinkoff.kora.guide.grpcserver;

    import ru.tinkoff.kora.application.graph.KoraApplication;
    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.config.hocon.HoconConfigModule;
    import ru.tinkoff.kora.grpc.server.GrpcServerModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
        HoconConfigModule,
        GrpcServerModule,  // <----- Connected module
        LogbackModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/grpcserver/Application.kt"
    package ru.tinkoff.kora.guide.grpcserver

    import ru.tinkoff.kora.application.graph.KoraApplication
    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.config.hocon.HoconConfigModule
    import ru.tinkoff.kora.grpc.server.GrpcServerModule
    import ru.tinkoff.kora.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        LogbackModule,
        GrpcServerModule  // <----- Connected module

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

At this point Kora knows that this application should start a gRPC server.

## Protobuf API { #protobuf-api }

Now we define the transport contract itself.

Create:

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

This contract intentionally mirrors the familiar CRUD API from the HTTP guide:

- create one user
- get one user
- list users
- update one user
- delete one user

That is why this is a good first gRPC example: the business meaning is already familiar, so we can focus on the transport.

## Service Layer { #service-layer }

We still want the same application architecture as in the HTTP guide:

- repository stores users
- service owns business logic
- transport layer only adapts requests and responses

So we keep:

- `UserRepository`
- `InMemoryUserRepository`
- `UserService`
- `UserNotFoundException`

The important point is not to move business logic into the gRPC handler. The handler should stay focused on:

- reading protobuf requests
- calling the service layer
- converting service results into protobuf responses

## gRPC Handler { #grpc-handler }

This is the point where gRPC replaces the HTTP controller.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/grpcserver/grpc/UserServiceGrpcHandler.java"
    package ru.tinkoff.kora.guide.grpcserver.grpc;

    import com.google.protobuf.Empty;
    import com.google.protobuf.Timestamp;
    import io.grpc.Status;
    import io.grpc.stub.StreamObserver;

    import java.time.ZoneOffset;

    import org.slf4j.Logger;
    import org.slf4j.LoggerFactory;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.grpcserver.CreateUserRequest;
    import ru.tinkoff.kora.guide.grpcserver.DeleteUserRequest;
    import ru.tinkoff.kora.guide.grpcserver.GetUserRequest;
    import ru.tinkoff.kora.guide.grpcserver.GetUsersRequest;
    import ru.tinkoff.kora.guide.grpcserver.GetUsersResponse;
    import ru.tinkoff.kora.guide.grpcserver.UpdateUserRequest;
    import ru.tinkoff.kora.guide.grpcserver.UserResponse;
    import ru.tinkoff.kora.guide.grpcserver.UserServiceGrpc;
    import ru.tinkoff.kora.guide.grpcserver.dto.UserRequest;
    import ru.tinkoff.kora.guide.grpcserver.service.UserNotFoundException;
    import ru.tinkoff.kora.guide.grpcserver.service.UserService;

    @Component
    public final class UserServiceGrpcHandler extends UserServiceGrpc.UserServiceImplBase {

        private static final Logger logger = LoggerFactory.getLogger(UserServiceGrpcHandler.class);

        private final UserService userService;

        public UserServiceGrpcHandler(UserService userService) {
            this.userService = userService;
        }

        @Override
        public void createUser(CreateUserRequest request, StreamObserver<UserResponse> responseObserver) {
            try {
                logger.info("Creating user: name={}, email={}", request.getName(), request.getEmail());
                var user = userService.createUser(new UserRequest(request.getName(), request.getEmail()));
                responseObserver.onNext(toGrpcUser(user));
                responseObserver.onCompleted();
            } catch (Exception e) {
                responseObserver.onError(Status.INTERNAL
                    .withDescription("Failed to create user")
                    .withCause(e)
                    .asRuntimeException());
            }
        }

        @Override
        public void getUser(GetUserRequest request, StreamObserver<UserResponse> responseObserver) {
            try {
                var user = userService.getUser(request.getUserId())
                    .orElseThrow(() -> Status.NOT_FOUND
                        .withDescription("User not found: " + request.getUserId())
                        .asRuntimeException());
                responseObserver.onNext(toGrpcUser(user));
                responseObserver.onCompleted();
            } catch (RuntimeException e) {
                responseObserver.onError(e);
            }
        }

        @Override
        public void getUsers(GetUsersRequest request, StreamObserver<GetUsersResponse> responseObserver) {
            try {
                int page = request.getPage();
                int size = request.getSize() == 0 ? 10 : request.getSize();
                String sort = request.getSort().isBlank() ? "name" : request.getSort();

                var response = GetUsersResponse.newBuilder()
                    .addAllUsers(userService.getUsers(page, size, sort).stream().map(this::toGrpcUser).toList())
                    .build();

                responseObserver.onNext(response);
                responseObserver.onCompleted();
            } catch (Exception e) {
                responseObserver.onError(Status.INTERNAL.withDescription("Failed to get users").withCause(e).asRuntimeException());
            }
        }

        @Override
        public void updateUser(UpdateUserRequest request, StreamObserver<UserResponse> responseObserver) {
            try {
                var updated = userService.updateUser(request.getUserId(), new UserRequest(request.getName(), request.getEmail()));
                responseObserver.onNext(toGrpcUser(updated));
                responseObserver.onCompleted();
            } catch (UserNotFoundException e) {
                responseObserver.onError(Status.NOT_FOUND.withDescription(e.getMessage()).asRuntimeException());
            }
        }

        @Override
        public void deleteUser(DeleteUserRequest request, StreamObserver<Empty> responseObserver) {
            try {
                userService.deleteUser(request.getUserId());
                responseObserver.onNext(Empty.getDefaultInstance());
                responseObserver.onCompleted();
            } catch (UserNotFoundException e) {
                responseObserver.onError(Status.NOT_FOUND.withDescription(e.getMessage()).asRuntimeException());
            }
        }

        private UserResponse toGrpcUser(ru.tinkoff.kora.guide.grpcserver.dto.UserResponse user) {
            return UserResponse.newBuilder()
                .setId(user.id())
                .setName(user.name())
                .setEmail(user.email())
                .setCreatedAt(Timestamp.newBuilder()
                    .setSeconds(user.createdAt().toEpochSecond(ZoneOffset.UTC))
                    .setNanos(user.createdAt().getNano())
                    .build())
                .build();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/grpcserver/grpc/UserServiceGrpcHandler.kt"
    package ru.tinkoff.kora.guide.grpcserver.grpc

    import com.google.protobuf.Empty
    import com.google.protobuf.Timestamp
    import io.grpc.Status
    import io.grpc.stub.StreamObserver
    import org.slf4j.LoggerFactory
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.grpcserver.*
    import ru.tinkoff.kora.guide.grpcserver.dto.UserRequest
    import ru.tinkoff.kora.guide.grpcserver.dto.UserResponse
    import ru.tinkoff.kora.guide.grpcserver.service.UserNotFoundException
    import ru.tinkoff.kora.guide.grpcserver.service.UserService
    import java.time.ZoneOffset

    @Component
    class UserServiceGrpcHandler(
        private val userService: UserService
    ) : UserServiceGrpc.UserServiceImplBase() {

        private val logger = LoggerFactory.getLogger(UserServiceGrpcHandler::class.java)

        override fun createUser(
            request: CreateUserRequest,
            responseObserver: StreamObserver<ru.tinkoff.kora.guide.grpcserver.UserResponse>
        ) {
            try {
                logger.info("Creating user: name={}, email={}", request.name, request.email)
                val user = userService.createUser(UserRequest(request.name, request.email))
                responseObserver.onNext(toGrpcUser(user))
                responseObserver.onCompleted()
            } catch (e: Exception) {
                logger.error("Failed to create user", e)
                responseObserver.onError(
                    Status.INTERNAL.withDescription("Failed to create user").withCause(e).asRuntimeException()
                )
            }
        }

        override fun getUser(
            request: GetUserRequest,
            responseObserver: StreamObserver<ru.tinkoff.kora.guide.grpcserver.UserResponse>
        ) {
            try {
                logger.info("Getting user: id={}", request.userId)
                val user = userService.getUser(request.userId)
                    ?: throw Status.NOT_FOUND.withDescription("User not found: ${request.userId}").asRuntimeException()
                responseObserver.onNext(toGrpcUser(user))
                responseObserver.onCompleted()
            } catch (e: RuntimeException) {
                logger.error("Failed to get user", e)
                responseObserver.onError(e)
            }
        }

        override fun getUsers(request: GetUsersRequest, responseObserver: StreamObserver<GetUsersResponse>) {
            try {
                val page = request.page
                val size = if (request.size == 0) 10 else request.size
                val sort = request.sort.ifBlank { "name" }
                val response = GetUsersResponse.newBuilder()
                    .addAllUsers(userService.getUsers(page, size, sort).map(::toGrpcUser))
                    .build()
                responseObserver.onNext(response)
                responseObserver.onCompleted()
            } catch (e: Exception) {
                logger.error("Failed to get users", e)
                responseObserver.onError(
                    Status.INTERNAL.withDescription("Failed to get users").withCause(e).asRuntimeException()
                )
            }
        }

        override fun updateUser(
            request: UpdateUserRequest,
            responseObserver: StreamObserver<ru.tinkoff.kora.guide.grpcserver.UserResponse>
        ) {
            try {
                val updated = userService.updateUser(request.userId, UserRequest(request.name, request.email))
                responseObserver.onNext(toGrpcUser(updated))
                responseObserver.onCompleted()
            } catch (e: UserNotFoundException) {
                logger.error("Failed to update user", e)
                responseObserver.onError(Status.NOT_FOUND.withDescription(e.message).asRuntimeException())
            }
        }

        override fun deleteUser(request: DeleteUserRequest, responseObserver: StreamObserver<Empty>) {
            try {
                userService.deleteUser(request.userId)
                responseObserver.onNext(Empty.getDefaultInstance())
                responseObserver.onCompleted()
            } catch (e: UserNotFoundException) {
                logger.error("Failed to delete user", e)
                responseObserver.onError(Status.NOT_FOUND.withDescription(e.message).asRuntimeException())
            }
        }

        private fun toGrpcUser(user: UserResponse): ru.tinkoff.kora.guide.grpcserver.UserResponse {
            return ru.tinkoff.kora.guide.grpcserver.UserResponse.newBuilder()
                .setId(user.id)
                .setName(user.name)
                .setEmail(user.email)
                .setCreatedAt(
                    Timestamp.newBuilder()
                        .setSeconds(user.createdAt.toEpochSecond(ZoneOffset.UTC))
                        .setNanos(user.createdAt.nano)
                        .build()
                )
                .build()
        }
    }
    ```

There are two especially important ideas here:

- the handler extends the generated `UserServiceGrpc.UserServiceImplBase`
- transport errors are expressed through gRPC `Status`, not HTTP exceptions

That second point matters a lot. This is not an HTTP application anymore, so the transport language must be gRPC-native.

## Configuration { #config }

The full model for gRPC handlers, server configuration, and reflection is covered in [Handlers](../documentation/grpc-server.md#handlers) and [Reflection](../documentation/grpc-server.md#reflection).

Add a small `application.conf`:

For the full configuration reference, see [gRPC Server](../documentation/grpc-server.md) and [Logging SLF4J](../documentation/logging-slf4j.md).

===! ":material-code-json: `Hocon`"

    ```javascript title="src/main/resources/application.conf"
    grpcServer {
      port = 8090 //(1)!
      telemetry.logging.enabled = true //(2)!
    }

    logging {
      levels {
        "ROOT": "WARN" //(3)!
        "ru.tinkoff.kora": "INFO" //(4)!
        "ru.tinkoff.kora.guide.grpcserver": "INFO" //(5)!
      }
    }
    ```

    1. Default gRPC server port used by this guide.
    2. Enables the feature for this configuration section.
    3. Log level for `ROOT`.
    4. Log level for `ru.tinkoff.kora`.
    5. Log level for `ru.tinkoff.kora.guide.grpcserver`.

=== ":simple-yaml: `YAML`"

    ```yaml title="src/main/resources/application.yaml"
    grpcServer:
      port: 8090 #(1)!
      telemetry:
        logging:
          enabled: true #(2)!
    logging:
      levels:
        ROOT: "WARN" #(3)!
        "ru.tinkoff.kora": "INFO" #(4)!
        "ru.tinkoff.kora.guide.grpcserver": "INFO" #(5)!
    ```

    1. Default gRPC server port used by this guide.
    2. Enables the feature for this configuration section.
    3. Log level for `ROOT`.
    4. Log level for `ru.tinkoff.kora`.
    5. Log level for `ru.tinkoff.kora.guide.grpcserver`.

This gives us:

- gRPC server on port `8090`
- Kora gRPC request logging
- readable logs for the demo module

## Run Application { #run-app }

Build the generated sources and compile the app:

```bash
./gradlew clean classes
```

Run it:

```bash
./gradlew run
```

Then call it with `grpcurl`:

```bash
grpcurl -plaintext -d "{\"name\":\"Alice\",\"email\":\"alice@example.com\"}" \
  localhost:8090 ru.tinkoff.kora.guide.grpcserver.UserService/CreateUser
```

```bash
grpcurl -plaintext -d "{\"page\":0,\"size\":10,\"sort\":\"name\"}" \
  localhost:8090 ru.tinkoff.kora.guide.grpcserver.UserService/GetUsers
```

## Testing { #testing }

The companion app includes JUnit tests that use a real gRPC channel against the application.

Run them with:

```bash
./gradlew test
```

The tests verify the unary CRUD flow separately, not as one giant scenario. That keeps failures easier to understand.

## Best Practices { #best-practices }

- Keep protobuf contracts focused on transport concerns, not domain implementation details.
- Keep business logic in `UserService`, not in the gRPC handler.
- Map missing resources to `Status.NOT_FOUND`, not to generic internal errors.
- Reuse the same application architecture across transports whenever possible.
- Treat generated protobuf code as transport types, not as domain models.
- Annotate handwritten DTOs with `@Json` only when they cross an HTTP/JSON boundary; generated protobuf messages do not need JSON annotations.

## Summary { #summary }

In this guide you built a unary gRPC server that mirrors the CRUD application from the HTTP server guide.

The key idea was simple:

- keep repository and service layers familiar
- define the transport in `.proto`
- implement a generated gRPC handler on top of the same business logic

## Key Concepts { #key-concepts }

- what gRPC is and why it is useful for service-to-service communication
- how Protocol Buffers define a shared RPC contract
- how Kora starts and wires a gRPC server
- how unary RPC methods map to familiar CRUD operations
- how gRPC `Status` errors replace HTTP-style transport errors

## Troubleshooting { #troubleshooting }

**Generated classes are missing:**

Run `./gradlew clean classes` after changing the `.proto` file and verify the protobuf Gradle plugin is configured.

**Server does not start:**

Check that the gRPC port in `application.conf` is free and that `GrpcServerModule` is included in the application graph.

**RPC returns `UNIMPLEMENTED`:**

Verify that the generated service name and method names match the `.proto` contract used by the client.

## What's Next? { #whats-next }

- [HTTP Client](http-client.md) if you have not completed it yet; the gRPC client guide assumes that client-side application structure.
- [gRPC Client](grpc-client.md) after HTTP Client, to consume this unary service through generated stubs.
- [HTTP Server Advanced](http-server-advanced.md) before [Advanced gRPC Server](grpc-server-advanced.md), because the advanced gRPC guide reuses advanced server concepts.
- [Observability](observability.md) to monitor gRPC services alongside HTTP services.

## Help { #help }

If something does not work:

- compare with [Kora Java gRPC Server App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-grpc-server-app) and [Kora Kotlin gRPC Server App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-grpc-server-app)
- check the [gRPC Server documentation](../documentation/grpc-server.md)
- check the [gRPC Client documentation](../documentation/grpc-client.md) when client/server contracts disagree
- make sure you regenerated code after changing the `.proto` file
