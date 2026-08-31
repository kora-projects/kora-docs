---
search:
  exclude: true
title: Advanced gRPC Server with Kora
summary: Extend a Kora 2.0 gRPC server with streaming RPCs, server interceptors, API-key auth, and reflection
description: "Advanced Kora gRPC server: a second protobuf service with server, client and bidirectional streaming handlers, global ServerInterceptor components scoped in code by SERVICE_NAME, API-key authorization read from gRPC Metadata through a @ConfigSource, gRPC reflection via io.grpc:grpc-services and grpcServer.reflectionEnabled, and @KoraAppTest streaming tests."
agent:
  use_when: "Use this file for questions about advanced Kora gRPC servers: streaming RPC handlers extending a generated ...ImplBase, StreamObserver request and response observers, the onNext / onCompleted / onError rules, ServerInterceptor registered as a plain @Component and scoped at runtime with getMethodDescriptor().getServiceName(), Status.UNAUTHENTICATED metadata authorization, grpcServer.port and grpcServer.reflectionEnabled, io.grpc:grpc-services for ProtoReflectionServiceV1, and grpc-netty in test scope."
tags: grpc-server, protobuf, streaming, interceptors, reflection, authentication
---

# Advanced gRPC Server with Kora { #advanced-grpc-server-kora }

This guide introduces advanced gRPC server capabilities in Kora. It covers server streaming, client streaming, bidirectional streaming, server interceptors, metadata-based authorization, and
reflection for local tooling. You will also see how streaming handlers use observers and completion signals while unary services remain available in the same application graph.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java gRPC Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-grpc-server-advanced-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin gRPC Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-grpc-server-advanced-app).

## What You'll Build { #youll-build }

You will extend the gRPC server application with:

- a second protobuf service, `UserStreamingService`, separate from the unary CRUD service
- `GetAllUsers` as a server-streaming RPC
- `CreateUsers` as a client-streaming RPC
- `UpdateUsers` as a bidirectional-streaming RPC
- a Kora gRPC handler that uses observers, completion signals, and stream error handling
- a server-side logging interceptor
- metadata-based API-key authorization for the streaming service only
- gRPC reflection enabled for local exploration with tools such as `grpcurl`

## What You'll Need { #youll-need }

- JDK 25 or later
- Gradle 9+ (the reference applications use Gradle Wrapper `9.5.1`)
- A text editor or IDE
- Optional: `grpcurl` for reflection and manual streaming checks

Kora artifacts are compiled for Java 25, so the JDK that compiles your code must be 25 or newer.

## Prerequisites { #prerequisites }

!!! note "Required: Complete Base gRPC Server Guide"

    This guide assumes you have completed **[gRPC Server with Kora](grpc-server.md)** and **[HTTP Server Advanced](http-server-advanced.md)**, and already understand unary gRPC handlers, protobuf code generation, and the repository/service separation used across the guides.

    If you haven't completed the base gRPC server guide yet, do that first, because this guide keeps the unary service stable and adds streaming, reflection, interceptors, and metadata authorization around it.

## Overview { #overview }

The most important design choice in this guide is that we **do not overload the original unary service** with every advanced concept.

Instead:

- `UserService` stays the familiar unary CRUD service
- `UserStreamingService` becomes a separate advanced service in the `.proto` contract
- `UserStreamingServiceGrpcHandler` focuses only on streaming operations

That separation makes the guide easier to learn and mirrors a common production pattern: keep the basic synchronous API stable, and add specialized streaming APIs only where they actually help.

Kora still owns component wiring and lifecycle. gRPC owns the RPC protocol and generated service contracts. Your code sits between them: it implements generated service methods, injects ordinary Kora
components, and translates streaming callbacks into application behavior.

The advanced pieces in this guide have different responsibilities:

- streaming changes the shape and lifetime of an RPC call
- interceptors add cross-cutting behavior around calls
- reflection exposes service metadata to tools such as `grpcurl`
- metadata authorization reads request metadata before business logic runs

Those features are all transport-level concerns. They are important, but they should not force the repository or service layer to become aware of gRPC internals. The service layer should still talk in
application terms: users, requests, responses, and business rules. The gRPC handler is the adapter that turns generated protobuf messages and streaming callbacks into those application operations.

That separation matters more in streaming code than in unary code. A unary handler receives one request, calls a service method, and returns one response. A streaming handler owns a longer-lived
interaction:

- it can send several responses before completing
- it can receive several requests before producing a final answer
- it must decide when to call `onNext`, `onCompleted`, or `onError`
- it must keep cancellation, backpressure, and partial failure in mind

One Kora-specific detail shapes how these handlers may be written: every client connection gets a dedicated single-threaded executor backed by a **virtual thread**, and all interceptor and handler
callbacks for the calls on that connection run on it, one at a time and in arrival order. Blocking inside a handler is safe — the carrier thread is released — but it delays the other calls on the
*same* connection. That is why every handler in this guide is plain synchronous code with no thread pools of its own.

The guide keeps the implementation intentionally small, but the architecture mirrors production code: keep the stable unary API intact, add a separate streaming service, and place advanced gRPC
mechanics at the edge of the application.

### Why gRPC Streaming Exists { #grpc-streaming-exists }

Unary RPC is great when one request naturally produces one response.

But sometimes the transport itself should express a different conversation shape:

- one request, many responses
- many requests, one response
- many requests, many responses

That is exactly what streaming gives you. In the `.proto` contract the only syntax involved is the `stream` keyword on the request side, the response side, or both.

### Server Streaming { #server-streaming }

The client sends one request, and the server sends back many messages.

This is useful when:

- you want to stream a large result set
- the client can start consuming results immediately
- the data naturally arrives as a sequence

The generated signature stays `void method(Req request, StreamObserver<Resp> responseObserver)` — what changes is that the handler calls `onNext` several times before `onCompleted`.

### Client Streaming { #client-streaming }

The client sends many messages, and the server answers once at the end.

This is useful when:

- the client is batching operations
- the server should aggregate work before replying
- one summary response is more useful than many small acknowledgements

Here the generated signature inverts: the method *returns* a `StreamObserver<Req>` that gRPC feeds with incoming messages, and the single response is sent through the observer passed in.

### Bidirectional Streaming { #bidirectional-streaming }

The client and server both exchange multiple messages on the same call.

This is useful when:

- the conversation is interactive
- updates should flow both ways
- one side should not wait for the other to finish sending everything first

The signature is the same as client streaming, but nothing stops the handler from answering each incoming message immediately instead of waiting for `onCompleted`.

## Immutable { #immutable }

Before adding anything new, keep in mind what does **not** change:

- `UserRepository`
- `InMemoryUserRepository`
- `UserService`
- unary `UserServiceGrpcHandler`

That is intentional. Advanced features should extend the application, not force you to rewrite the basic path you already trust.

## Dependencies { #dependencies }

The build is the one from the base gRPC server guide plus the artifacts reflection and the tests need.

Versions of Kora modules come from the Kora BOM `io.koraframework:kora-bom`, so individual Kora artifacts are declared without a version:

```properties title="gradle.properties"
koraVersion=2.0.0.RC1
junitVersion=6.1.3
```

===! ":fontawesome-brands-java: `Java`"

    Update `build.gradle`:

    ```groovy title="build.gradle"
    dependencies {
        koraBom platform("io.koraframework:kora-bom:$koraVersion")

        compileOnly "javax.annotation:javax.annotation-api:1.3.2"
        annotationProcessor "io.koraframework:annotation-processors"

        implementation "io.koraframework:config-hocon"
        implementation "io.koraframework:grpc-server"
        implementation "io.koraframework:logging-logback"
        implementation "io.grpc:grpc-protobuf:1.83.1"
        implementation "io.grpc:grpc-services:1.83.1"

        testCompileOnly "javax.annotation:javax.annotation-api:1.3.2"
        testAnnotationProcessor "io.koraframework:annotation-processors"

        testImplementation platform("org.junit:junit-bom:$junitVersion")
        testImplementation "io.grpc:grpc-netty:1.83.1"
        testImplementation "org.junit.jupiter:junit-jupiter"
        testImplementation "io.koraframework:test-junit5"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update `build.gradle.kts`:

    ```kotlin title="build.gradle.kts"
    dependencies {
        implementation(platform("io.koraframework:kora-bom:${property("koraVersion")}"))

        compileOnly("javax.annotation:javax.annotation-api:1.3.2")
        ksp("io.koraframework:symbol-processors:${property("koraVersion")}")

        implementation("io.koraframework:config-hocon")
        implementation("io.koraframework:grpc-server")
        implementation("io.koraframework:logging-logback")
        implementation("io.grpc:grpc-protobuf:1.83.1")
        implementation("io.grpc:grpc-services:1.83.1")

        testCompileOnly("javax.annotation:javax.annotation-api:1.3.2")

        testImplementation(platform("org.junit:junit-bom:${property("junitVersion")}"))
        testImplementation("io.grpc:grpc-netty:1.83.1")
        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation("io.koraframework:test-junit5")
    }
    ```

Two of these deserve a note:

- `io.grpc:grpc-services` carries `ProtoReflectionServiceV1`. Kora adds the reflection service only if that class is on the classpath, so `reflectionEnabled = true` alone does nothing without it.
- `io.grpc:grpc-netty` is test-only. `@KoraAppTest` starts the real server, and the test acts as an ordinary gRPC client, which needs a client transport on the test classpath.

The protobuf Gradle plugin block is unchanged from the [base guide](grpc-server.md#code-generation) — the new streaming service is generated from the same `.proto` file by the same task.

!!! warning "Keep every `io.grpc` artifact on one version"

    The gRPC runtime shipped with `io.koraframework:grpc-server` is `1.83.1`. Every other `io.grpc` artifact you declare — `grpc-protobuf`, `grpc-services`, and anything in test scope such as
    `grpc-netty` — must use exactly that version. A pinned older version compiles fine and fails only at runtime with
    `AbstractMethodError: ... does not define or inherit an implementation of the resolved method 'buildClientTransportServers(List, MetricRecorder)'`.

## Protobuf API { #protobuf-api }

The contract gains a second service. The unary one is untouched, apart from renaming its update request message so that unary and streaming updates can carry different shapes over time.

??? example "Protobuf contract"

    ```protobuf title="src/main/proto/user_service.proto"
    syntax = "proto3";

    package io.koraframework.guide.grpcserver.advanced;
    option java_multiple_files = true;

    import "google/protobuf/empty.proto";
    import "google/protobuf/timestamp.proto";

    service UserService {
      rpc CreateUser(CreateUserRequest) returns (UserResponse) {}
      rpc GetUser(GetUserRequest) returns (UserResponse) {}
      rpc GetUsers(GetUsersRequest) returns (GetUsersResponse) {}
      rpc UpdateUser(UpdateUserRequestUnary) returns (UserResponse) {}
      rpc DeleteUser(DeleteUserRequest) returns (google.protobuf.Empty) {}
    }

    service UserStreamingService {
      rpc GetAllUsers(google.protobuf.Empty) returns (stream UserResponse) {}
      rpc CreateUsers(stream CreateUserRequest) returns (CreateUsersResponse) {}
      rpc UpdateUsers(stream UpdateUserRequest) returns (stream UserResponse) {}
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

    message UpdateUserRequestUnary {
      string user_id = 1;
      string name = 2;
      string email = 3;
    }

    message DeleteUserRequest {
      string user_id = 1;
    }

    message UpdateUserRequest {
      string user_id = 1;
      string name = 2;
      string email = 3;
    }

    message CreateUsersResponse {
      int32 created_count = 1;
      repeated string user_ids = 2;
    }

    message UserResponse {
      string id = 1;
      string name = 2;
      string email = 3;
      google.protobuf.Timestamp created_at = 4;
    }
    ```

Both services live in one file and are served by one Kora application on one port. They are separate only in the contract, in the handler, and — as you will see below — in what the authorization
interceptor protects.

## Streaming Service { #streaming-service }

Just like we split the transport contract, we also split the application logic.

The advanced module introduces `UserStreamingService`, a thin application service in front of the existing `UserService`:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/grpcserver/advanced/service/UserStreamingService.java"
    package io.koraframework.guide.grpcserver.advanced.service;

    import java.util.List;
    import java.util.Optional;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.grpcserver.advanced.dto.UserRequest;
    import io.koraframework.guide.grpcserver.advanced.dto.UserResponse;

    @Component
    public final class UserStreamingService {

        private final UserService userService;

        public UserStreamingService(UserService userService) {
            this.userService = userService;
        }

        public List<UserResponse> getAllUsers() {
            return userService.getUsers(0, Integer.MAX_VALUE, "name");
        }

        public List<UserResponse> createUsers(List<UserRequest> requests) {
            return requests.stream()
                .map(userService::createUser)
                .toList();
        }

        public Optional<UserResponse> tryUpdateUser(String id, UserRequest request) { //(1)!
            try {
                return Optional.of(userService.updateUser(id, request));
            } catch (UserNotFoundException e) {
                return Optional.empty();
            }
        }
    }
    ```

    1. The bidirectional handler updates users one message at a time and must not abort the whole stream on a single miss, so the "not found" case becomes an empty result instead of an exception.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/grpcserver/advanced/service/UserStreamingService.kt"
    package io.koraframework.guide.grpcserver.advanced.service

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.grpcserver.advanced.dto.UserRequest
    import io.koraframework.guide.grpcserver.advanced.dto.UserResponse

    @Component
    class UserStreamingService(
        private val userService: UserService
    ) {

        fun getAllUsers(): List<UserResponse> = userService.getUsers(0, Int.MAX_VALUE, "name")

        fun createUsers(requests: List<UserRequest>): List<UserResponse> = requests.map(userService::createUser)

        fun tryUpdateUser(id: String, request: UserRequest): UserResponse? { //(1)!
            return try {
                userService.updateUser(id, request)
            } catch (e: UserNotFoundException) {
                null
            }
        }
    }
    ```

    1. The bidirectional handler updates users one message at a time and must not abort the whole stream on a single miss, so the "not found" case becomes a `null` result instead of an exception.

This service owns the logic behind:

- returning all users for server streaming
- creating many users for client streaming
- updating users for bidirectional streaming

That keeps the original `UserService` close to the HTTP guide and prevents it from turning into a transport-specific god class.

## Streaming Handler { #streaming-handler }

Now connect the generated streaming service to the new application service.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/grpcserver/advanced/grpc/UserStreamingServiceGrpcHandler.java"
    package io.koraframework.guide.grpcserver.advanced.grpc;

    import com.google.protobuf.Empty;
    import com.google.protobuf.Timestamp;
    import io.grpc.Status;
    import io.grpc.StatusRuntimeException;
    import io.grpc.stub.StreamObserver;
    import java.time.ZoneOffset;
    import java.util.ArrayList;
    import java.util.List;
    import org.slf4j.Logger;
    import org.slf4j.LoggerFactory;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.grpcserver.advanced.CreateUserRequest;
    import io.koraframework.guide.grpcserver.advanced.CreateUsersResponse;
    import io.koraframework.guide.grpcserver.advanced.UpdateUserRequest;
    import io.koraframework.guide.grpcserver.advanced.UserResponse;
    import io.koraframework.guide.grpcserver.advanced.UserStreamingServiceGrpc;
    import io.koraframework.guide.grpcserver.advanced.dto.UserRequest;
    import io.koraframework.guide.grpcserver.advanced.service.UserStreamingService;

    @Component
    public final class UserStreamingServiceGrpcHandler extends UserStreamingServiceGrpc.UserStreamingServiceImplBase {

        private static final Logger logger = LoggerFactory.getLogger(UserStreamingServiceGrpcHandler.class);

        private final UserStreamingService userStreamingService;

        public UserStreamingServiceGrpcHandler(UserStreamingService userStreamingService) {
            this.userStreamingService = userStreamingService;
        }

        @Override
        public void getAllUsers(Empty request, StreamObserver<UserResponse> responseObserver) { //(1)!
            try {
                for (var user : userStreamingService.getAllUsers()) {
                    responseObserver.onNext(toGrpcUser(user));
                }
                responseObserver.onCompleted();
            } catch (Exception e) {
                responseObserver.onError(Status.INTERNAL.withDescription("Failed to stream users").withCause(e).asRuntimeException());
            }
        }

        @Override
        public StreamObserver<CreateUserRequest> createUsers(StreamObserver<CreateUsersResponse> responseObserver) { //(2)!
            return new StreamObserver<>() {
                private final List<UserRequest> requests = new ArrayList<>();

                @Override
                public void onNext(CreateUserRequest value) {
                    requests.add(new UserRequest(value.getName(), value.getEmail()));
                }

                @Override
                public void onError(Throwable t) { //(3)!
                    logger.error("Client streaming failed", t);
                    responseObserver.onError(t);
                }

                @Override
                public void onCompleted() {
                    try {
                        var createdUsers = userStreamingService.createUsers(requests);
                        responseObserver.onNext(CreateUsersResponse.newBuilder()
                            .setCreatedCount(createdUsers.size())
                            .addAllUserIds(createdUsers.stream().map(io.koraframework.guide.grpcserver.advanced.dto.UserResponse::id).toList())
                            .build());
                        responseObserver.onCompleted();
                    } catch (Exception e) {
                        responseObserver.onError(Status.INTERNAL.withDescription("Failed to create users").withCause(e).asRuntimeException());
                    }
                }
            };
        }

        @Override
        public StreamObserver<UpdateUserRequest> updateUsers(StreamObserver<UserResponse> responseObserver) { //(4)!
            return new StreamObserver<>() {
                @Override
                public void onNext(UpdateUserRequest value) {
                    try {
                        var user = userStreamingService.tryUpdateUser(value.getUserId(), new UserRequest(value.getName(), value.getEmail()))
                            .orElseThrow(() -> Status.NOT_FOUND.withDescription("User not found: " + value.getUserId()).asRuntimeException());
                        responseObserver.onNext(toGrpcUser(user));
                    } catch (StatusRuntimeException e) {
                        responseObserver.onError(e);
                    }
                }

                @Override
                public void onError(Throwable t) {
                    logger.error("Bidirectional streaming failed", t);
                    responseObserver.onError(t);
                }

                @Override
                public void onCompleted() {
                    responseObserver.onCompleted();
                }
            };
        }

        private UserResponse toGrpcUser(io.koraframework.guide.grpcserver.advanced.dto.UserResponse user) {
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

    1. Server streaming: many `onNext`, then exactly one `onCompleted`.
    2. Client streaming: the method returns the observer gRPC will push requests into; the response is produced only in `onCompleted`.
    3. `onError` on the *request* observer means the client aborted — the handler must stop and close the response side too.
    4. Bidirectional streaming: each incoming message is answered immediately, so responses interleave with requests.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/grpcserver/advanced/grpc/UserStreamingServiceGrpcHandler.kt"
    package io.koraframework.guide.grpcserver.advanced.grpc

    import com.google.protobuf.Empty
    import io.grpc.Status
    import io.grpc.StatusRuntimeException
    import io.grpc.stub.StreamObserver
    import org.slf4j.LoggerFactory
    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.grpcserver.advanced.CreateUserRequest
    import io.koraframework.guide.grpcserver.advanced.CreateUsersResponse
    import io.koraframework.guide.grpcserver.advanced.UpdateUserRequest
    import io.koraframework.guide.grpcserver.advanced.UserStreamingServiceGrpc
    import io.koraframework.guide.grpcserver.advanced.dto.UserRequest
    import io.koraframework.guide.grpcserver.advanced.service.UserStreamingService

    @Component
    class UserStreamingServiceGrpcHandler(
        private val userStreamingService: UserStreamingService
    ) : UserStreamingServiceGrpc.UserStreamingServiceImplBase() {

        private val logger = LoggerFactory.getLogger(UserStreamingServiceGrpcHandler::class.java)

        override fun getAllUsers( //(1)!
            request: Empty,
            responseObserver: StreamObserver<io.koraframework.guide.grpcserver.advanced.UserResponse>
        ) {
            try {
                userStreamingService.getAllUsers().forEach { responseObserver.onNext(it.toGrpcUser()) }
                responseObserver.onCompleted()
            } catch (e: Exception) {
                responseObserver.onError(
                    Status.INTERNAL.withDescription("Failed to stream users").withCause(e).asRuntimeException()
                )
            }
        }

        override fun createUsers(responseObserver: StreamObserver<CreateUsersResponse>): StreamObserver<CreateUserRequest> { //(2)!
            return object : StreamObserver<CreateUserRequest> {
                private val requests = mutableListOf<UserRequest>()

                override fun onNext(value: CreateUserRequest) {
                    requests += UserRequest(value.name, value.email)
                }

                override fun onError(t: Throwable) { //(3)!
                    logger.error("Client streaming failed", t)
                    responseObserver.onError(t)
                }

                override fun onCompleted() {
                    try {
                        val createdUsers = userStreamingService.createUsers(requests)
                        responseObserver.onNext(
                            CreateUsersResponse.newBuilder()
                                .setCreatedCount(createdUsers.size)
                                .addAllUserIds(createdUsers.map { it.id })
                                .build()
                        )
                        responseObserver.onCompleted()
                    } catch (e: Exception) {
                        responseObserver.onError(
                            Status.INTERNAL.withDescription("Failed to create users").withCause(e).asRuntimeException()
                        )
                    }
                }
            }
        }

        override fun updateUsers(responseObserver: StreamObserver<io.koraframework.guide.grpcserver.advanced.UserResponse>): StreamObserver<UpdateUserRequest> { //(4)!
            return object : StreamObserver<UpdateUserRequest> {
                override fun onNext(value: UpdateUserRequest) {
                    try {
                        val user = userStreamingService.tryUpdateUser(value.userId, UserRequest(value.name, value.email))
                            ?: throw Status.NOT_FOUND.withDescription("User not found: ${value.userId}")
                                .asRuntimeException()
                        responseObserver.onNext(user.toGrpcUser())
                    } catch (e: StatusRuntimeException) {
                        responseObserver.onError(e)
                    }
                }

                override fun onError(t: Throwable) {
                    logger.error("Bidirectional streaming failed", t)
                    responseObserver.onError(t)
                }

                override fun onCompleted() {
                    responseObserver.onCompleted()
                }
            }
        }
    }
    ```

    1. Server streaming: many `onNext`, then exactly one `onCompleted`.
    2. Client streaming: the method returns the observer gRPC will push requests into; the response is produced only in `onCompleted`.
    3. `onError` on the *request* observer means the client aborted — the handler must stop and close the response side too.
    4. Bidirectional streaming: each incoming message is answered immediately, so responses interleave with requests.

    Two handlers now need the same DTO-to-protobuf conversion, so in the Kotlin variant it moves out of the class into one internal extension function:

    ```kotlin title="src/main/kotlin/io/koraframework/guide/grpcserver/advanced/grpc/GrpcMappers.kt"
    package io.koraframework.guide.grpcserver.advanced.grpc

    import com.google.protobuf.Timestamp
    import io.koraframework.guide.grpcserver.advanced.dto.UserResponse
    import java.time.ZoneOffset

    internal fun UserResponse.toGrpcUser(): io.koraframework.guide.grpcserver.advanced.UserResponse {
        return io.koraframework.guide.grpcserver.advanced.UserResponse.newBuilder()
            .setId(id)
            .setName(name)
            .setEmail(email)
            .setCreatedAt(
                Timestamp.newBuilder()
                    .setSeconds(createdAt.toEpochSecond(ZoneOffset.UTC))
                    .setNanos(createdAt.nano)
                    .build()
            )
            .build()
    }
    ```

Registration works exactly as in the base guide: the handler is a plain `@Component` extending the generated `...ImplBase`, so it is a `BindableService` in the graph, and Kora adds every
`BindableService` it finds to the server. There is no `@GrpcService` annotation and no manual `addService` call, and nothing special is needed to make the second service coexist with the first.

The rules that make streaming handlers correct are worth stating explicitly:

- exactly one terminal signal per call — either `onCompleted()` or `onError(...)`, never both, never neither
- an exception that escapes without being reported through the observer is closed by gRPC as `UNKNOWN`, which tells the caller nothing useful
- `onError` on the request observer is a client-side abort, not a server failure; log it and close your side

## Server Interceptor { #server-interceptor }

For more on server-side gRPC interceptors and how they are wired, see [gRPC Server: Interceptors](../documentation/grpc-server.md#interceptors).

Interceptors are the gRPC equivalent of transport middleware. They are a good place for concerns that should stay outside business logic:

- logging
- auth
- tracing
- rate limiting

Unlike the [HTTP server](../documentation/http-server.md#interceptors), the gRPC server module has **no** `@InterceptWith` annotation and no per-service tag. Every `ServerInterceptor` registered as a
`@Component` is applied **globally** to every service on the server.

The advanced module introduces a simple logging interceptor:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/grpcserver/advanced/grpc/LoggingInterceptor.java"
    package io.koraframework.guide.grpcserver.advanced.grpc;

    import io.grpc.Metadata;
    import io.grpc.ServerCall;
    import io.grpc.ServerCallHandler;
    import io.grpc.ServerInterceptor;
    import org.slf4j.Logger;
    import org.slf4j.LoggerFactory;
    import io.koraframework.common.annotation.Component;

    @Component //(1)!
    public final class LoggingInterceptor implements ServerInterceptor {

        private static final Logger logger = LoggerFactory.getLogger(LoggingInterceptor.class);

        @Override
        public <ReqT, RespT> ServerCall.Listener<ReqT> interceptCall(
                ServerCall<ReqT, RespT> call,
                Metadata headers,
                ServerCallHandler<ReqT, RespT> next) {
            logger.info("Incoming gRPC request: method={}", call.getMethodDescriptor().getFullMethodName());
            return next.startCall(call, headers); //(2)!
        }
    }
    ```

    1. No tag and no annotation — a plain component is enough, and it applies to every service on the server.
    2. Passes the call on; if you return without calling `startCall`, you must close the call yourself.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/grpcserver/advanced/grpc/LoggingInterceptor.kt"
    package io.koraframework.guide.grpcserver.advanced.grpc

    import io.grpc.Metadata
    import io.grpc.ServerCall
    import io.grpc.ServerCallHandler
    import io.grpc.ServerInterceptor
    import org.slf4j.LoggerFactory
    import io.koraframework.common.annotation.Component

    @Component //(1)!
    class LoggingInterceptor : ServerInterceptor {

        private val logger = LoggerFactory.getLogger(LoggingInterceptor::class.java)

        override fun <ReqT : Any?, RespT : Any?> interceptCall(
            call: ServerCall<ReqT, RespT>,
            headers: Metadata,
            next: ServerCallHandler<ReqT, RespT>
        ): ServerCall.Listener<ReqT> {
            logger.info("Incoming gRPC request: method={}", call.methodDescriptor.fullMethodName)
            return next.startCall(call, headers) //(2)!
        }
    }
    ```

    1. No tag and no annotation — a plain component is enough, and it applies to every service on the server.
    2. Passes the call on; if you return without calling `startCall`, you must close the call yourself.

Kora registers your interceptors on the builder first and its own telemetry interceptor last. gRPC invokes interceptors in the reverse order of registration, so an incoming call is processed as:

```
TelemetryInterceptor -> your interceptors -> handler
```

That order means telemetry observes the final `Status` of the call, including errors your interceptors produce, and the observation and `OpenTelemetry` context are already established when your code
runs. When several of your interceptors exist, they run in the reverse of their graph registration order — do not build logic that depends on it.

This interceptor lives only in the advanced module, so the basic guide stays focused on first principles.

## Server Reflection { #server-reflection }

Reflection is useful in development because it lets tools inspect the gRPC server without manually wiring a pre-generated client first.

In Kora it takes two things: the `io.grpc:grpc-services` dependency added above, and one configuration flag. Kora adds the reflection service only when `io.grpc.protobuf.services.ProtoReflectionServiceV1`
is present on the classpath, so configuration alone is not enough.

For the full configuration reference, see [gRPC Server](../documentation/grpc-server.md).

===! ":material-code-json: `Hocon`"

    ```javascript title="src/main/resources/application.conf"
    grpcServer {
      port = 8092 //(1)!
      reflectionEnabled = true //(2)!
      telemetry.logging.enabled = true //(3)!
    }

    logging {
      levels {
        "ROOT": "WARN" //(4)!
        "io.koraframework": "INFO" //(5)!
        "io.koraframework.guide.grpcserver.advanced": "INFO" //(6)!
      }
    }
    ```

    1. gRPC server port (default: `8090`); the advanced app uses `8092` so it can run next to the base guide's server.
    2. Enables the gRPC Server Reflection service (default: `false`).
    3. Enables gRPC call logging for this server (default: `false`).
    4. Log level for `ROOT`.
    5. Log level for `io.koraframework`.
    6. Log level for `io.koraframework.guide.grpcserver.advanced`.

=== ":simple-yaml: `YAML`"

    ```yaml title="src/main/resources/application.yaml"
    grpcServer:
      port: 8092 #(1)!
      reflectionEnabled: true #(2)!
      telemetry:
        logging:
          enabled: true #(3)!
    logging:
      levels:
        ROOT: "WARN" #(4)!
        "io.koraframework": "INFO" #(5)!
        "io.koraframework.guide.grpcserver.advanced": "INFO" #(6)!
    ```

    1. gRPC server port (default: `8090`); the advanced app uses `8092` so it can run next to the base guide's server.
    2. Enables the gRPC Server Reflection service (default: `false`).
    3. Enables gRPC call logging for this server (default: `false`).
    4. Log level for `ROOT`.
    5. Log level for `io.koraframework`.
    6. Log level for `io.koraframework.guide.grpcserver.advanced`.

Everything else keeps a working default: the incoming message size is capped at `4MiB`, graceful shutdown waits `30s`, and connection age and keepalive limits are off unless set.

With reflection on, `grpcurl` no longer needs `-import-path`/`-proto`:

```bash
grpcurl -plaintext localhost:8092 list
grpcurl -plaintext localhost:8092 describe io.koraframework.guide.grpcserver.advanced.UserStreamingService
```

Why this matters:

- `grpcurl` can discover services more easily
- local debugging gets simpler
- the advanced guide can show a more tooling-friendly server setup

Reflection describes *every* service on the server, which is exactly what you want locally and usually not what you want on a public production port.

## API Key Authorization { #api-key }

The advanced module also introduces a server-side auth interceptor, but only for the streaming service.

That is important pedagogically:

- unary CRUD stays easy to understand
- the protected area is clearly limited to the advanced API

Since every `ServerInterceptor` is global, "only for the streaming service" is a decision the interceptor makes at runtime by inspecting `call.getMethodDescriptor().getServiceName()` and comparing it
with the generated `UserStreamingServiceGrpc.SERVICE_NAME` constant.

Configuration — this goes into the same `application.conf` as the block above:

===! ":material-code-json: `Hocon`"

    ```javascript title="src/main/resources/application.conf"
    auth.apiKey.value = ${?GRPC_STREAMING_API_KEY} //(1)!
    ```

    1. API key the streaming service requires, read from the `GRPC_STREAMING_API_KEY` environment variable. There is no default on purpose: the application fails to start rather than come up unprotected.

=== ":simple-yaml: `YAML`"

    ```yaml title="src/main/resources/application.yaml"
    auth:
      apiKey:
        value: ${?GRPC_STREAMING_API_KEY} #(1)!
    ```

    1. API key the streaming service requires, read from the `GRPC_STREAMING_API_KEY` environment variable. There is no default on purpose: the application fails to start rather than come up unprotected.

The value is read through a small `@ConfigSource` interface:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/grpcserver/advanced/grpc/UserStreamingAuthConfig.java"
    package io.koraframework.guide.grpcserver.advanced.grpc;

    import io.koraframework.config.common.annotation.ConfigSource;

    @ConfigSource("auth.apiKey")
    public interface UserStreamingAuthConfig {

        String value();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/grpcserver/advanced/grpc/UserStreamingAuthConfig.kt"
    package io.koraframework.guide.grpcserver.advanced.grpc

    import io.koraframework.config.common.annotation.ConfigSource

    @ConfigSource("auth.apiKey")
    interface UserStreamingAuthConfig {
        fun value(): String
    }
    ```

Interceptor:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/grpcserver/advanced/grpc/UserStreamingAuthInterceptor.java"
    package io.koraframework.guide.grpcserver.advanced.grpc;

    import io.grpc.Metadata;
    import io.grpc.ServerCall;
    import io.grpc.ServerCallHandler;
    import io.grpc.ServerInterceptor;
    import io.grpc.Status;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.grpcserver.advanced.UserStreamingServiceGrpc;

    @Component
    public final class UserStreamingAuthInterceptor implements ServerInterceptor {

        private static final Metadata.Key<String> AUTHORIZATION_HEADER =
                Metadata.Key.of("authorization", Metadata.ASCII_STRING_MARSHALLER);

        private final UserStreamingAuthConfig config;

        public UserStreamingAuthInterceptor(UserStreamingAuthConfig config) {
            this.config = config;
        }

        @Override
        public <ReqT, RespT> ServerCall.Listener<ReqT> interceptCall(
                ServerCall<ReqT, RespT> call,
                Metadata headers,
                ServerCallHandler<ReqT, RespT> next) {
            if (!UserStreamingServiceGrpc.SERVICE_NAME.equals(call.getMethodDescriptor().getServiceName())) { //(1)!
                return next.startCall(call, headers);
            }

            var authorization = headers.get(AUTHORIZATION_HEADER);
            if (!this.config.value().equals(authorization)) {
                call.close(Status.UNAUTHENTICATED.withDescription("Invalid API key"), new Metadata()); //(2)!
                return new ServerCall.Listener<>() {}; //(3)!
            }

            return next.startCall(call, headers);
        }
    }
    ```

    1. Scoping happens here, at runtime: unary `UserService` calls pass straight through.
    2. Rejecting a call means closing it with a `Status` — the handler is never invoked.
    3. An empty listener must still be returned; gRPC requires a listener even for a call that was just closed.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/grpcserver/advanced/grpc/UserStreamingAuthInterceptor.kt"
    package io.koraframework.guide.grpcserver.advanced.grpc

    import io.grpc.*
    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.grpcserver.advanced.UserStreamingServiceGrpc

    @Component
    class UserStreamingAuthInterceptor(
        private val config: UserStreamingAuthConfig
    ) : ServerInterceptor {

        override fun <ReqT : Any?, RespT : Any?> interceptCall(
            call: ServerCall<ReqT, RespT>,
            headers: Metadata,
            next: ServerCallHandler<ReqT, RespT>
        ): ServerCall.Listener<ReqT> {
            if (UserStreamingServiceGrpc.SERVICE_NAME != call.methodDescriptor.serviceName) { //(1)!
                return next.startCall(call, headers)
            }

            val authorization = headers.get(AUTHORIZATION_HEADER)
            if (config.value() != authorization) {
                call.close(Status.UNAUTHENTICATED.withDescription("Invalid API key"), Metadata()) //(2)!
                return object : ServerCall.Listener<ReqT>() {} //(3)!
            }
            return next.startCall(call, headers)
        }

        companion object {
            private val AUTHORIZATION_HEADER: Metadata.Key<String> =
                Metadata.Key.of("authorization", Metadata.ASCII_STRING_MARSHALLER)
        }
    }
    ```

    1. Scoping happens here, at runtime: unary `UserService` calls pass straight through.
    2. Rejecting a call means closing it with a `Status` — the handler is never invoked.
    3. An empty listener must still be returned; gRPC requires a listener even for a call that was just closed.

This is the gRPC counterpart of the protected advanced endpoints we introduced in the HTTP advanced guide. The credential travels in the call's initial `Metadata`, which is read once when the call
starts — so the same check covers a long-lived streaming call as well as a unary one.

## Run Application { #run-app }

Compile:

```bash
./gradlew clean classes
```

Run, providing the API key the streaming service requires:

```bash
GRPC_STREAMING_API_KEY=test-api-key ./gradlew run
```

Now the unary service is available on port `8092` without credentials, and the streaming service additionally expects:

- metadata header `authorization`
- value equal to `GRPC_STREAMING_API_KEY`

With reflection on, a quick manual check needs no `.proto` file:

```bash
grpcurl -plaintext -H "authorization: test-api-key" \
  localhost:8092 io.koraframework.guide.grpcserver.advanced.UserStreamingService/GetAllUsers
```

## Testing { #testing }

The companion app uses `@KoraAppTest`, which starts the whole graph — including the real gRPC server on a real port — and then talks to it through an ordinary `ManagedChannel`. The API key comes from a
test-scoped `application.conf` so the test does not depend on the developer's environment.

Run the module tests with:

```bash
./gradlew test
```

The tests cover:

- unary CRUD
- server streaming
- client streaming
- bidirectional streaming
- unauthorized access to the protected streaming service, asserting `Status.Code.UNAUTHENTICATED`

Authorized streaming calls attach the key with `MetadataUtils.newAttachHeadersInterceptor(metadata)`, which is the client-side mirror of the server interceptor above.

## Best Practices { #best-practices }

- Keep advanced streaming methods in a separate service when that improves clarity.
- Do not force every feature into one giant protobuf service.
- Keep unary CRUD stable while adding more advanced transport patterns around it.
- Use interceptors for cross-cutting transport concerns, not for business logic.
- Remember that every `ServerInterceptor` is global; scope it in code with `getMethodDescriptor().getServiceName()`.
- Send exactly one terminal signal per streaming call, and always map failures to an explicit `Status`.
- Turn on reflection in development-oriented modules where tooling support helps, and think twice about a public production port.
- Keep every `io.grpc` artifact on the version that ships with `io.koraframework:grpc-server`.
- Annotate handwritten DTOs with `@Json` only when they cross an HTTP/JSON boundary; generated protobuf messages do not need JSON annotations.

## Summary { #summary }

In this guide you kept the original unary gRPC service intact and added a second, clearly advanced streaming service on top of it.

That gave you a cleaner architecture and a better teaching flow:

- base service for familiar CRUD
- separate streaming service for advanced gRPC patterns
- interceptors, reflection, and auth only where they add real value

## Key Concepts { #key-concepts }

- why streaming deserves its own service boundary in many cases
- how server, client, and bidirectional streaming look in generated gRPC handlers
- why every streaming call needs exactly one terminal signal
- how server interceptors are registered globally in Kora gRPC applications and scoped in code
- how the interceptor chain orders your interceptors relative to telemetry
- how to protect a service with metadata-based API-key auth
- how reflection helps local exploration and debugging

## Troubleshooting { #troubleshooting }

**Streaming methods are not generated:**

Regenerate sources with `./gradlew clean classes` after editing the `.proto` file and check that the streaming service is in the same source set.

**A streaming call hangs:**

The handler probably never sent a terminal signal. Every path must end in `onCompleted()` or `onError(...)` exactly once.

**Protected calls are always rejected:**

Make sure `GRPC_STREAMING_API_KEY` is set and that the client sends the `authorization` metadata header expected by the interceptor.

**The interceptor also blocks unary calls:**

`ServerInterceptor` components are global. Check the `SERVICE_NAME` comparison — without it, the interceptor guards every service on the server.

**Reflection does not work:**

Verify `grpcServer.reflectionEnabled = true` and that `io.grpc:grpc-services` is on the compile classpath. Without that artifact Kora silently skips the reflection service.

**Tests fail with `AbstractMethodError` mentioning `buildClientTransportServers`:**

A gRPC artifact in test scope is pinned to a different version than the runtime that ships with `io.koraframework:grpc-server`. Align every `io.grpc` dependency on `1.83.1`.

## What's Next? { #whats-next }

- [HTTP Client](http-client.md) if you have not completed it yet.
- [gRPC Client](grpc-client.md) if you want to revisit the unary client baseline first.
- [Advanced gRPC Client](grpc-client-advanced.md) after gRPC Client, to consume the streaming service and metadata-protected calls.
- [Observability](observability.md) to monitor streaming RPCs, interceptors, and server behavior.
- [Resilient Patterns](resilient.md) to protect clients that call advanced gRPC services.

## Help { #help }

If something does not work:

- compare with [Kora Java gRPC Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-grpc-server-advanced-app) and [Kora Kotlin gRPC Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-grpc-server-advanced-app)
- check the [gRPC Server documentation](../documentation/grpc-server.md)
- verify that you regenerated sources after changing the `.proto` contract
- make sure `GRPC_STREAMING_API_KEY` is set before testing protected calls
