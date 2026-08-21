---
search:
  exclude: true
title: Advanced gRPC Client with Kora
summary: Build a streaming gRPC client with generated stubs, metadata auth, and client interceptors
tags: grpc-client, streaming, interceptors, authentication, protobuf
---

# Advanced gRPC Client with Kora { #advanced-grpc-client-kora }

This guide introduces advanced gRPC client patterns in Kora. It covers server streaming, client streaming, bidirectional streaming, metadata-based authentication, and client-side interceptors for
generated stubs. You will also see how asynchronous observers, completion signals, and stream lifecycle errors make streaming clients different from unary request-response code.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java gRPC Client Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-grpc-client-advanced-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin gRPC Client Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-grpc-client-advanced-app).

## What You'll Build { #youll-build }

You will extend the gRPC client application with:

- a streaming client service for `UserStreamingService`
- server-streaming calls for `GetAllUsers`
- client-streaming calls for `CreateUsers`
- bidirectional-streaming calls for `UpdateUsers`
- HTTP trigger routes that make each streaming flow easy to run locally
- a client-side logging interceptor
- a client-side auth interceptor that sends the API key through gRPC metadata
- fast in-process tests that verify streaming behavior without a manually started server

## What You'll Need { #youll-need }

- JDK 17 or later
- Gradle 7+
- A text editor or IDE
- A running advanced gRPC server for runtime checks

## Prerequisites { #prerequisites }

!!! note "Required: Complete Advanced gRPC Server Guide"

    This guide assumes you have completed **[gRPC Client with Kora](grpc-client.md)** and **[Advanced gRPC Server with Kora](grpc-server-advanced.md)**, and already understand generated unary stubs, protobuf contracts, and how Kora injects gRPC client dependencies.

    If you haven't completed the advanced gRPC server guide yet, do that first, because this guide reuses the same streaming contract and focuses on client-side streaming calls.

## Overview { #overview }

Just like the advanced server guide, the advanced client guide is built around separation.

We do **not** overload the original unary client with every advanced concern.

Instead:

- the base client stays focused on unary CRUD through `UserService`
- the advanced client focuses on streaming through `UserStreamingService`

That design keeps both guides easier to learn and matches the shape of the companion apps.

On the client side, advanced gRPC features affect control flow more than they affect dependency injection. Kora still provides the configured gRPC client and your application components. The generated
stubs still perform the RPC calls. What changes is how your service code manages call lifetimes, request streams, response observers, metadata, and failures.

This guide keeps those concerns explicit:

- streaming services wrap generated async stubs instead of exposing them directly
- client interceptors attach cross-cutting behavior to outbound calls
- metadata authorization is configured near the client boundary
- HTTP trigger endpoints are only a local way to exercise the streaming client

The advanced client also has a different failure model from the unary client. In a unary call, a failure usually means one request failed before producing one response. In a streaming call, failure
can happen after some messages have already been sent or received. That means the wrapper service must treat stream completion as part of the API design, not as an afterthought.

This is why the guide introduces explicit client-side methods for each streaming shape:

- server streaming is read-oriented: call once, consume many responses
- client streaming is write-oriented: send many requests, wait for one summary
- bidirectional streaming is conversation-oriented: send and receive independently

The generated async stub is powerful, but it is not the boundary you usually want across the rest of the application. It exposes callback-oriented mechanics such as observers and completion signals.
The Kora service wrapper turns those mechanics into a smaller API that can be called from controllers, jobs, or other services without spreading gRPC callback code everywhere.

Metadata and interceptors belong to the same boundary. They are useful for authentication, tracing, request IDs, and logging, but they should be attached near the generated client. That keeps business
code focused on the operation being performed instead of how every RPC is decorated on the wire.

### How Streams Change the Client { #streams-change-client }

Unary gRPC calls look pleasantly simple:

- create one request
- call one method
- get one response

Streaming changes that mental model.

### Server Stream { #server-stream }

With server streaming, the client sends one request and receives many responses.

That means client code must think about:

- iterating over a stream of messages
- partial progress
- when the stream finishes

### Client Stream Changes Data Creation { #client-stream-changes-data }

With client streaming, the client no longer sends one finished request object.

Instead, it gradually pushes multiple messages into the call and only later receives the final summary response.

### Bidirectional Stream { #bidirectional-stream }

With bidirectional streaming, the client and server can both keep talking on the same RPC.

That means the client must handle:

- asynchronous request sending
- asynchronous response handling
- stream lifecycle and completion

## Protobuf API { #protobuf-api }

The advanced client reuses the exact same streaming-focused `.proto` contract from the advanced server guide.

??? example "Protobuf contract"

    ```protobuf title="src/main/proto/user_service.proto"
    syntax = "proto3";
    
    package ru.tinkoff.kora.guide.grpcserver.advanced;
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

Notice the important modeling choice again:

- unary `UserService` still exists in the contract
- advanced client work is focused on the separate `UserStreamingService`

## Dependencies { #dependencies }

The advanced client module uses the same core client stack as the base client.

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

## Code Generation { #code-generation }

The Gradle protobuf setup stays the same idea as in the base client guide:

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

What changes is not code generation itself, but the kinds of generated stubs we use:

- blocking stubs for server streaming reads
- async stubs for client and bidirectional streaming

## Configuration { #config }

The advanced server protects the streaming service with an API key in gRPC metadata, so the advanced client must know two things:

- where the server lives
- which API key to send

For the full configuration reference, see [HTTP Server](../documentation/http-server.md), [Configuration](../documentation/config.md), [gRPC Client](../documentation/grpc-client.md)
and [Logging SLF4J](../documentation/logging-slf4j.md).

===! ":material-code-json: `Hocon`"

    ```javascript title="src/main/resources/application.conf"
    httpServer {
      publicApiHttpPort = 8081 //(1)!
      privateApiHttpPort = 8086 //(2)!
      telemetry.logging.enabled = true //(3)!
    }

    auth.apiKey.value = "test-api-key" //(4)!
    auth.apiKey.value = ${?GRPC_STREAMING_API_KEY} //(5)!

    grpcClient {
      UserStreamingService {
        url = "http://localhost:8092" //(6)!
        url = ${?GRPC_STREAMING_SERVER_URL} //(7)!
        telemetry.logging.enabled = true //(8)!
      }
    }

    logging {
      levels {
        "ROOT": "INFO" //(9)!
        "ru.tinkoff.kora": "INFO" //(10)!
        "ru.tinkoff.kora.guide.grpcclient.advanced": "INFO" //(11)!
      }
    }
    ```

    1. Default public HTTP port used by application endpoints.
    2. Default private HTTP port used by probes, metrics, and management endpoints.
    3. Enables the feature for this configuration section.
    4. Configured value consumed by the guide component.
    5. Configured value consumed by the guide component. Optional override from `GRPC_STREAMING_API_KEY`.
    6. Base URL used by the configured client.
    7. Base URL used by the configured client. Optional override from `GRPC_STREAMING_SERVER_URL`.
    8. Enables the feature for this configuration section.
    9. Log level for `ROOT`.
    10. Log level for `ru.tinkoff.kora`.
    11. Log level for `ru.tinkoff.kora.guide.grpcclient.advanced`.

=== ":simple-yaml: `YAML`"

    ```yaml title="src/main/resources/application.yaml"
    httpServer:
      publicApiHttpPort: 8081 #(1)!
      privateApiHttpPort: 8086 #(2)!
      telemetry:
        logging:
          enabled: true #(3)!
    auth:
      apiKey:
        value: ${?GRPC_STREAMING_API_KEY:"test-api-key"} #(4)!
    grpcClient:
      UserStreamingService:
        url: ${?GRPC_STREAMING_SERVER_URL:"http://localhost:8092"} #(5)!
        telemetry:
          logging:
            enabled: true #(6)!
    logging:
      levels:
        ROOT: "INFO" #(7)!
        "ru.tinkoff.kora": "INFO" #(8)!
        "ru.tinkoff.kora.guide.grpcclient.advanced": "INFO" #(9)!
    ```

    1. Default public HTTP port used by application endpoints.
    2. Default private HTTP port used by probes, metrics, and management endpoints.
    3. Enables the feature for this configuration section.
    4. Configured value consumed by the guide component. Uses the shown default and allows `GRPC_STREAMING_API_KEY` to override it.
    5. Base URL used by the configured client. Uses the shown default and allows `GRPC_STREAMING_SERVER_URL` to override it.
    6. Enables the feature for this configuration section.
    7. Log level for `ROOT`.
    8. Log level for `ru.tinkoff.kora`.
    9. Log level for `ru.tinkoff.kora.guide.grpcclient.advanced`.

Just like in the base client guide, the local URL uses `http://...` so the gRPC client runs in plaintext mode for this demo setup.

## Client Interceptor { #client-interceptor }

For more on client-side gRPC interceptors and metadata, see [gRPC Client: Interceptors](../documentation/grpc-client.md#interceptors).

Client interceptors are the client-side equivalent of transport middleware. They are useful for concerns that should happen for outgoing calls in one place:

- logging
- authentication
- deadlines
- tracing

The advanced client adds a simple logging interceptor:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/grpcclient/advanced/grpc/LoggingInterceptor.java"
    package ru.tinkoff.kora.guide.grpcclient.advanced.grpc;

    import io.grpc.CallOptions;
    import io.grpc.Channel;
    import io.grpc.ClientCall;
    import io.grpc.ClientInterceptor;
    import io.grpc.MethodDescriptor;
    import org.slf4j.Logger;
    import org.slf4j.LoggerFactory;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.Tag;
    import ru.tinkoff.kora.guide.grpcserver.advanced.UserStreamingServiceGrpc;

    @Tag(UserStreamingServiceGrpc.class)
    @Component
    public final class LoggingInterceptor implements ClientInterceptor {

        private static final Logger logger = LoggerFactory.getLogger(LoggingInterceptor.class);

        @Override
        public <ReqT, RespT> ClientCall<ReqT, RespT> interceptCall(
                MethodDescriptor<ReqT, RespT> method,
                CallOptions callOptions,
                Channel next) {
            logger.info("Calling gRPC method {}", method.getFullMethodName());
            return next.newCall(method, callOptions);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/grpcclient/advanced/grpc/LoggingInterceptor.kt"
    package ru.tinkoff.kora.guide.grpcclient.advanced.grpc

    import io.grpc.*
    import org.slf4j.LoggerFactory
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.Tag
    import ru.tinkoff.kora.guide.grpcserver.advanced.UserStreamingServiceGrpc

    @Tag(UserStreamingServiceGrpc::class)
    @Component
    class LoggingInterceptor : ClientInterceptor {

        private val logger = LoggerFactory.getLogger(LoggingInterceptor::class.java)

        override fun <ReqT : Any?, RespT : Any?> interceptCall(
            method: MethodDescriptor<ReqT, RespT>,
            callOptions: CallOptions,
            next: Channel
        ): ClientCall<ReqT, RespT> {
            logger.info("Calling gRPC method {}", method.fullMethodName)
            return next.newCall(method, callOptions)
        }
    }
    ```

The `@Tag(UserStreamingServiceGrpc.class)` is important: it scopes this interceptor to the advanced streaming service client.

## Authorization Interceptor { #authorization-interceptor }

Now we make the client automatically send the API key expected by the advanced server.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/grpcclient/advanced/grpc/UserStreamingAuthInterceptor.java"
    package ru.tinkoff.kora.guide.grpcclient.advanced.grpc;

    import io.grpc.CallOptions;
    import io.grpc.Channel;
    import io.grpc.ClientCall;
    import io.grpc.ClientInterceptor;
    import io.grpc.ForwardingClientCall;
    import io.grpc.Metadata;
    import io.grpc.MethodDescriptor;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.Tag;
    import ru.tinkoff.kora.guide.grpcserver.advanced.UserStreamingServiceGrpc;

    @Tag(UserStreamingServiceGrpc.class)
    @Component
    public final class UserStreamingAuthInterceptor implements ClientInterceptor {

        private static final Metadata.Key<String> AUTHORIZATION_HEADER =
                Metadata.Key.of("authorization", Metadata.ASCII_STRING_MARSHALLER);

        private final UserStreamingAuthConfig authConfig;

        public UserStreamingAuthInterceptor(UserStreamingAuthConfig authConfig) {
            this.authConfig = authConfig;
        }

        @Override
        public <ReqT, RespT> ClientCall<ReqT, RespT> interceptCall(
                MethodDescriptor<ReqT, RespT> method,
                CallOptions callOptions,
                Channel next) {
            return new ForwardingClientCall.SimpleForwardingClientCall<>(next.newCall(method, callOptions)) {
                @Override
                public void start(Listener<RespT> responseListener, Metadata headers) {
                    headers.put(AUTHORIZATION_HEADER, authConfig.value());
                    super.start(responseListener, headers);
                }
            };
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/grpcclient/advanced/grpc/UserStreamingAuthInterceptor.kt"
    package ru.tinkoff.kora.guide.grpcclient.advanced.grpc

    import io.grpc.*
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.Tag
    import ru.tinkoff.kora.guide.grpcserver.advanced.UserStreamingServiceGrpc

    @Tag(UserStreamingServiceGrpc::class)
    @Component
    class UserStreamingAuthInterceptor(
        private val authConfig: UserStreamingAuthConfig
    ) : ClientInterceptor {

        override fun <ReqT : Any?, RespT : Any?> interceptCall(
            method: MethodDescriptor<ReqT, RespT>,
            callOptions: CallOptions,
            next: Channel
        ): ClientCall<ReqT, RespT> {
            return object :
                ForwardingClientCall.SimpleForwardingClientCall<ReqT, RespT>(next.newCall(method, callOptions)) {
                override fun start(responseListener: Listener<RespT>, headers: Metadata) {
                    headers.put(AUTHORIZATION_HEADER, authConfig.value())
                    super.start(responseListener, headers)
                }
            }
        }

        companion object {
            private val AUTHORIZATION_HEADER: Metadata.Key<String> =
                Metadata.Key.of("authorization", Metadata.ASCII_STRING_MARSHALLER)
        }
    }
    ```

This is the gRPC equivalent of automatically attaching auth headers in an advanced HTTP client.

## Streaming Client { #streaming-client }

Now we can wrap the generated streaming stubs in a small client-side service.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/grpcclient/advanced/service/UserStreamingClientService.java"
    package ru.tinkoff.kora.guide.grpcclient.advanced.service;

    import com.google.protobuf.Empty;
    import io.grpc.stub.StreamObserver;
    import java.time.LocalDateTime;
    import java.time.ZoneOffset;
    import java.util.ArrayList;
    import java.util.List;
    import java.util.concurrent.CompletableFuture;
    import java.util.concurrent.CopyOnWriteArrayList;
    import java.util.concurrent.TimeUnit;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.grpcclient.advanced.dto.UserRequest;
    import ru.tinkoff.kora.guide.grpcclient.advanced.dto.UserResponse;
    import ru.tinkoff.kora.guide.grpcclient.advanced.dto.UserUpdateRequest;
    import ru.tinkoff.kora.guide.grpcserver.advanced.CreateUserRequest;
    import ru.tinkoff.kora.guide.grpcserver.advanced.CreateUsersResponse;
    import ru.tinkoff.kora.guide.grpcserver.advanced.UpdateUserRequest;
    import ru.tinkoff.kora.guide.grpcserver.advanced.UserStreamingServiceGrpc;

    @Component
    public final class UserStreamingClientService {

        private final UserStreamingServiceGrpc.UserStreamingServiceBlockingStub blockingStub;
        private final UserStreamingServiceGrpc.UserStreamingServiceStub asyncStub;

        public UserStreamingClientService(
                UserStreamingServiceGrpc.UserStreamingServiceBlockingStub blockingStub,
                UserStreamingServiceGrpc.UserStreamingServiceStub asyncStub) {
            this.blockingStub = blockingStub;
            this.asyncStub = asyncStub;
        }

        public CreateUsersResult createUsers(List<UserRequest> requests) {
            var future = new CompletableFuture<CreateUsersResult>();
            var responseObserver = new StreamObserver<CreateUsersResponse>() {
                @Override
                public void onNext(CreateUsersResponse value) {
                    future.complete(new CreateUsersResult(value.getCreatedCount(), List.copyOf(value.getUserIdsList())));
                }

                @Override
                public void onError(Throwable t) {
                    future.completeExceptionally(t);
                }

                @Override
                public void onCompleted() {
                }
            };

            var requestObserver = this.asyncStub.createUsers(responseObserver);
            try {
                for (var request : requests) {
                    requestObserver.onNext(CreateUserRequest.newBuilder()
                            .setName(request.name())
                            .setEmail(request.email())
                            .build());
                }
                requestObserver.onCompleted();
                return future.get(5, TimeUnit.SECONDS);
            } catch (Exception e) {
                requestObserver.onError(e);
                throw new RuntimeException("Failed to create users over gRPC streaming", e);
            }
        }

        public List<UserResponse> getAllUsers() {
            var users = new ArrayList<UserResponse>();
            var iterator = this.blockingStub.getAllUsers(Empty.getDefaultInstance());
            iterator.forEachRemaining(user -> users.add(toDto(user)));
            return users;
        }

        public List<UserResponse> updateUsers(List<UserUpdateRequest> updates) {
            var future = new CompletableFuture<List<UserResponse>>();
            var responses = new CopyOnWriteArrayList<UserResponse>();
            var responseObserver = new StreamObserver<ru.tinkoff.kora.guide.grpcserver.advanced.UserResponse>() {
                @Override
                public void onNext(ru.tinkoff.kora.guide.grpcserver.advanced.UserResponse value) {
                    responses.add(toDto(value));
                }

                @Override
                public void onError(Throwable t) {
                    future.completeExceptionally(t);
                }

                @Override
                public void onCompleted() {
                    future.complete(List.copyOf(responses));
                }
            };

            var requestObserver = this.asyncStub.updateUsers(responseObserver);
            try {
                for (var update : updates) {
                    requestObserver.onNext(UpdateUserRequest.newBuilder()
                            .setUserId(update.userId())
                            .setName(update.name())
                            .setEmail(update.email())
                            .build());
                }
                requestObserver.onCompleted();
                return future.get(5, TimeUnit.SECONDS);
            } catch (Exception e) {
                requestObserver.onError(e);
                throw new RuntimeException("Failed to update users over gRPC streaming", e);
            }
        }

        private UserResponse toDto(ru.tinkoff.kora.guide.grpcserver.advanced.UserResponse response) {
            return new UserResponse(
                    response.getId(),
                    response.getName(),
                    response.getEmail(),
                    LocalDateTime.ofEpochSecond(
                            response.getCreatedAt().getSeconds(),
                            response.getCreatedAt().getNanos(),
                            ZoneOffset.UTC));
        }

        public record CreateUsersResult(int createdCount, List<String> userIds) {}
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/grpcclient/advanced/service/UserStreamingClientService.kt"
    package ru.tinkoff.kora.guide.grpcclient.advanced.service

    import com.google.protobuf.Empty
    import io.grpc.stub.StreamObserver
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.grpcclient.advanced.dto.UserRequest
    import ru.tinkoff.kora.guide.grpcclient.advanced.dto.UserResponse
    import ru.tinkoff.kora.guide.grpcclient.advanced.dto.UserUpdateRequest
    import ru.tinkoff.kora.guide.grpcserver.advanced.CreateUserRequest
    import ru.tinkoff.kora.guide.grpcserver.advanced.CreateUsersResponse
    import ru.tinkoff.kora.guide.grpcserver.advanced.UpdateUserRequest
    import ru.tinkoff.kora.guide.grpcserver.advanced.UserStreamingServiceGrpc
    import java.time.LocalDateTime
    import java.time.ZoneOffset
    import java.util.concurrent.CompletableFuture
    import java.util.concurrent.CopyOnWriteArrayList
    import java.util.concurrent.TimeUnit

    @Component
    class UserStreamingClientService(
        private val blockingStub: UserStreamingServiceGrpc.UserStreamingServiceBlockingStub,
        private val asyncStub: UserStreamingServiceGrpc.UserStreamingServiceStub
    ) {

        fun createUsers(requests: List<UserRequest>): CreateUsersResult {
            val future = CompletableFuture<CreateUsersResult>()
            val responseObserver = object : StreamObserver<CreateUsersResponse> {
                override fun onNext(value: CreateUsersResponse) {
                    future.complete(CreateUsersResult(value.createdCount, value.userIdsList.toList()))
                }

                override fun onError(t: Throwable) {
                    future.completeExceptionally(t)
                }

                override fun onCompleted() = Unit
            }

            val requestObserver = asyncStub.createUsers(responseObserver)
            try {
                requests.forEach { request ->
                    requestObserver.onNext(
                        CreateUserRequest.newBuilder()
                            .setName(request.name)
                            .setEmail(request.email)
                            .build()
                    )
                }
                requestObserver.onCompleted()
                return future.get(5, TimeUnit.SECONDS)
            } catch (e: Exception) {
                requestObserver.onError(e)
                throw RuntimeException("Failed to create users over gRPC streaming", e)
            }
        }

        fun getAllUsers(): List<UserResponse> {
            val users = mutableListOf<UserResponse>()
            val iterator = blockingStub.getAllUsers(Empty.getDefaultInstance())
            iterator.forEachRemaining { user -> users += toDto(user) }
            return users
        }

        fun updateUsers(updates: List<UserUpdateRequest>): List<UserResponse> {
            val future = CompletableFuture<List<UserResponse>>()
            val responses = CopyOnWriteArrayList<UserResponse>()
            val responseObserver = object : StreamObserver<ru.tinkoff.kora.guide.grpcserver.advanced.UserResponse> {
                override fun onNext(value: ru.tinkoff.kora.guide.grpcserver.advanced.UserResponse) {
                    responses += toDto(value)
                }

                override fun onError(t: Throwable) {
                    future.completeExceptionally(t)
                }

                override fun onCompleted() {
                    future.complete(responses.toList())
                }
            }

            val requestObserver = asyncStub.updateUsers(responseObserver)
            try {
                updates.forEach { update ->
                    requestObserver.onNext(
                        UpdateUserRequest.newBuilder()
                            .setUserId(update.userId)
                            .setName(update.name)
                            .setEmail(update.email)
                            .build()
                    )
                }
                requestObserver.onCompleted()
                return future.get(5, TimeUnit.SECONDS)
            } catch (e: Exception) {
                requestObserver.onError(e)
                throw RuntimeException("Failed to update users over gRPC streaming", e)
            }
        }

        private fun toDto(response: ru.tinkoff.kora.guide.grpcserver.advanced.UserResponse): UserResponse {
            return UserResponse(
                response.id,
                response.name,
                response.email,
                LocalDateTime.ofEpochSecond(response.createdAt.seconds, response.createdAt.nanos, ZoneOffset.UTC)
            )
        }

        data class CreateUsersResult(val createdCount: Int, val userIds: List<String>)
    }
    ```

This single service now demonstrates all three streaming shapes from the client side.

## Check Controller { #check-controller }

The companion app includes a small helper endpoint that exercises the streaming client.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/grpcclient/advanced/controller/ClientTestController.java"
    package ru.tinkoff.kora.guide.grpcclient.advanced.controller;

    import java.util.List;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.grpcclient.advanced.dto.UserRequest;
    import ru.tinkoff.kora.guide.grpcclient.advanced.dto.UserUpdateRequest;
    import ru.tinkoff.kora.guide.grpcclient.advanced.service.UserStreamingClientService;
    import ru.tinkoff.kora.http.common.HttpMethod;
    import ru.tinkoff.kora.http.common.annotation.HttpRoute;
    import ru.tinkoff.kora.http.server.common.annotation.HttpController;
    import ru.tinkoff.kora.json.common.annotation.Json;

    @Component
    @HttpController
    public final class ClientTestController {

        private final UserStreamingClientService userStreamingClientService;

        public ClientTestController(UserStreamingClientService userStreamingClientService) {
            this.userStreamingClientService = userStreamingClientService;
        }

        @HttpRoute(method = HttpMethod.POST, path = "/client/test-all-streaming-endpoints")
        @Json
        public TestResults testAllStreamingEndpoints() {
            try {
                var created = this.userStreamingClientService.createUsers(List.of(
                        new UserRequest("Alice Streaming", "alice-streaming@example.com"),
                        new UserRequest("Bob Streaming", "bob-streaming@example.com")));
                boolean usersCreated = created.createdCount() == 2;

                var streamed = this.userStreamingClientService.getAllUsers();
                boolean usersStreamed = created.userIds().stream()
                        .allMatch(userId -> streamed.stream().anyMatch(user -> user.id().equals(userId)));

                var updated = this.userStreamingClientService.updateUsers(List.of(
                        new UserUpdateRequest(created.userIds().get(0), "Updated Alice Streaming", "updated-alice@example.com"),
                        new UserUpdateRequest(created.userIds().get(1), "Updated Bob Streaming", "updated-bob@example.com")));
                boolean usersUpdated = updated.stream().anyMatch(user -> "Updated Alice Streaming".equals(user.name()))
                        && updated.stream().anyMatch(user -> "Updated Bob Streaming".equals(user.name()));

                boolean allTestsPassed = usersCreated && usersStreamed && usersUpdated;
                return new TestResults(usersCreated, usersStreamed, usersUpdated, allTestsPassed, null);
            } catch (Exception exception) {
                return new TestResults(false, false, false, false, exception.getMessage());
            }
        }

        @Json
        public record TestResults(
                boolean usersCreated,
                boolean usersStreamed,
                boolean usersUpdated,
                boolean allTestsPassed,
                String error) {}
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/grpcclient/advanced/controller/ClientTestController.kt"
    package ru.tinkoff.kora.guide.grpcclient.advanced.controller

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.grpcclient.advanced.dto.UserRequest
    import ru.tinkoff.kora.guide.grpcclient.advanced.dto.UserUpdateRequest
    import ru.tinkoff.kora.guide.grpcclient.advanced.service.UserStreamingClientService
    import ru.tinkoff.kora.http.common.HttpMethod
    import ru.tinkoff.kora.http.common.annotation.HttpRoute
    import ru.tinkoff.kora.http.server.common.annotation.HttpController
    import ru.tinkoff.kora.json.common.annotation.Json

    @Component
    @HttpController
    class ClientTestController(
        private val userStreamingClientService: UserStreamingClientService
    ) {

        @HttpRoute(method = HttpMethod.POST, path = "/client/test-all-streaming-endpoints")
        @Json
        fun testAllStreamingEndpoints(): TestResults {
            return try {
                val created = userStreamingClientService.createUsers(
                    listOf(
                        UserRequest("Alice Streaming", "alice-streaming@example.com"),
                        UserRequest("Bob Streaming", "bob-streaming@example.com")
                    )
                )
                val usersCreated = created.createdCount == 2

                val streamed = userStreamingClientService.getAllUsers()
                val usersStreamed = created.userIds.all { userId -> streamed.any { user -> user.id == userId } }

                val updated = userStreamingClientService.updateUsers(
                    listOf(
                        UserUpdateRequest(created.userIds[0], "Updated Alice Streaming", "updated-alice@example.com"),
                        UserUpdateRequest(created.userIds[1], "Updated Bob Streaming", "updated-bob@example.com")
                    )
                )
                val usersUpdated = updated.any { it.name == "Updated Alice Streaming" } &&
                        updated.any { it.name == "Updated Bob Streaming" }

                val allTestsPassed = usersCreated && usersStreamed && usersUpdated
                TestResults(usersCreated, usersStreamed, usersUpdated, allTestsPassed, null)
            } catch (exception: Exception) {
                TestResults(false, false, false, false, exception.message)
            }
        }

        @Json
        data class TestResults(
            val usersCreated: Boolean,
            val usersStreamed: Boolean,
            val usersUpdated: Boolean,
            val allTestsPassed: Boolean,
            val error: String?
        )
    }
    ```

Again, the HTTP endpoint is just a local harness. The real subject of the guide is the streaming gRPC client underneath it.

## Run Application { #run-app }

Start the advanced server first:

```bash
$env:GRPC_STREAMING_API_KEY="test-api-key"
./gradlew run
```

Then start the advanced client:

```bash
$env:GRPC_STREAMING_API_KEY="test-api-key"
./gradlew run
```

Now call:

```bash
curl -X POST http://localhost:8081/client/test-all-streaming-endpoints
```

That one helper endpoint internally verifies:

- client streaming
- server streaming
- bidirectional streaming

## Testing { #testing }

The advanced client tests also use the in-process gRPC approach.

That is especially useful here because it lets the tests simulate:

- successful streaming interactions
- rejected calls without an API key
- interceptor behavior

Run them with:

```bash
./gradlew test
```

## Best Practices { #best-practices }

- Keep advanced streaming work in a dedicated client service instead of bloating the unary client.
- Scope interceptors with tags when they should only affect one generated service.
- Use client interceptors for metadata-based auth instead of repeating header logic in every call site.
- Keep stream lifecycle handling close to the transport boundary.
- Prefer in-process gRPC servers for fast client-side streaming tests.
- Annotate handwritten DTOs with `@Json` only when they cross an HTTP/JSON boundary; generated protobuf messages do not need JSON annotations.

## Summary { #summary }

In this guide you built a streaming gRPC client that mirrors the advanced server guide.

The important idea was not only "how to call streaming RPCs", but also "how to structure the client cleanly":

- separate unary and streaming concerns
- add auth and logging through interceptors
- wrap generated stubs in a focused service layer

## Key Concepts { #key-concepts }

- how advanced gRPC clients differ from unary gRPC clients
- how blocking and async stubs are used for different streaming patterns
- how client interceptors add logging and metadata auth
- how to consume server, client, and bidirectional streaming methods
- how to test advanced gRPC client behavior with `InProcessServer`

## Troubleshooting { #troubleshooting }

**Streaming call never completes:**

Check that the request stream is completed on the client side and that the test/server implementation sends completion signals.

**Calls are rejected as unauthenticated:**

Verify that the client and server use the same API key value and that the auth interceptor is tagged to the generated streaming client.

**In-process tests pass but runtime calls fail:**

Compare the runtime `application.conf` with the in-process test wiring, especially gRPC host, port, and interceptor tags.

## What's Next? { #whats-next }

- [Resilient Patterns](resilient.md) to protect streaming and unary RPC calls against slow or unavailable services.
- [Observability](observability.md) to trace gRPC client calls, streaming lifecycles, and interceptor behavior.
- [Messaging with Kafka](messaging-kafka.md) to compare RPC-style integration with asynchronous event-driven integration.
- [HTTP Client Advanced](http-client-advanced.md) to compare advanced gRPC and advanced HTTP client boundaries.

## Help { #help }

If something does not work:

- compare with [Kora Java gRPC Client Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-grpc-client-advanced-app) and [Kora Kotlin gRPC Client Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-grpc-client-advanced-app)
- check the [gRPC Client documentation](../documentation/grpc-client.md)
- verify the advanced server from [Advanced gRPC Server](grpc-server-advanced.md) is running on port `8092`
- make sure the client and server use the same API key value
