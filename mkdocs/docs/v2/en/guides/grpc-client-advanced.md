---
search:
  exclude: true
title: Advanced gRPC Client with Kora
summary: Build a Kora 2.0 streaming gRPC client with generated stubs, metadata auth, and tagged client interceptors
description: "Streaming Kora gRPC client: server, client and bidirectional streaming through the generated blocking and async stubs, StreamObserver lifecycles and completion signals, ClientInterceptor components scoped with @Tag(ServiceGrpc.class) for logging and metadata authorization, an API key read through @ConfigSource, the grpcClient.<Service> configuration section, and in-process streaming tests."
agent:
  use_when: "Use this file for questions about advanced Kora gRPC clients: server, client and bidirectional streaming with UserStreamingServiceGrpc stubs, StreamObserver with onCompleted and onError, @Tag(ServiceGrpc.class) on a ClientInterceptor, ForwardingClientCall and Metadata.Key authorization headers, interceptor ordering relative to telemetry and deadlines, Kotlin coroutine Flow stubs, and testing streaming clients with InProcessServerBuilder and ClientInterceptors.intercept."
tags: grpc-client, streaming, interceptors, authentication, protobuf
---

# Advanced gRPC Client with Kora { #advanced-grpc-client-kora }

This guide introduces advanced gRPC client patterns in Kora. It covers server streaming, client streaming, bidirectional streaming, metadata-based authentication, and client-side interceptors scoped
to one generated service. You will also see how asynchronous observers, completion signals, and stream lifecycle errors make streaming clients different from unary request-response code.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java gRPC Client Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-grpc-client-advanced-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin gRPC Client Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-grpc-client-advanced-app).

## What You'll Build { #youll-build }

You will extend the gRPC client application with:

- a streaming client service for `UserStreamingService`
- server-streaming calls for `GetAllUsers`
- client-streaming calls for `CreateUsers`
- bidirectional-streaming calls for `UpdateUsers`
- HTTP trigger routes that make each streaming flow easy to run locally
- a client-side logging interceptor tagged to one generated service
- a client-side auth interceptor that sends the API key through gRPC metadata
- fast in-process tests that verify streaming behavior without a manually started server

## What You'll Need { #youll-need }

- JDK 25 or later
- Gradle 9+ (the reference applications use Gradle Wrapper `9.5.1`)
- A text editor or IDE
- A running advanced gRPC server for runtime checks

Kora artifacts are compiled for Java 25, so the JDK that compiles your code must be 25 or newer.

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

On the client side, advanced gRPC features affect control flow more than they affect dependency injection. Kora still builds the channel and registers the configured stubs. The generated stubs still
perform the RPC calls. What changes is how your service code manages call lifetimes, request streams, response observers, metadata, and failures.

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

Streaming changes that mental model. It also changes which stub you need: in Java, unary and server-streaming calls are available on the `BlockingStub`, while client-streaming and bidirectional calls
exist **only** on the async `Stub`. That is why the streaming service below injects both.

### Server Stream { #server-stream }

With server streaming, the client sends one request and receives many responses.

That means client code must think about:

- iterating over a stream of messages
- partial progress
- when the stream finishes

On the blocking stub this shape is an `Iterator<T>` that blocks between messages, which makes it the easiest streaming style to consume.

### Client Stream Changes Data Creation { #client-stream-changes-data }

With client streaming, the client no longer sends one finished request object.

Instead, it gradually pushes multiple messages into the call and only later receives the final summary response.

The async stub hands you a `StreamObserver<Req>` to write into, and delivers the single response to the `StreamObserver<Resp>` you passed in. The call is not finished until you call `onCompleted()` on
the request observer.

### Bidirectional Stream { #bidirectional-stream }

With bidirectional streaming, the client and server can both keep talking on the same RPC.

That means the client must handle:

- asynchronous request sending
- asynchronous response handling
- stream lifecycle and completion

Because both directions are asynchronous, the wrapper needs an explicit place to collect responses and an explicit signal for "the server is done" — in this guide a `CompletableFuture` completed from
`onCompleted()`.

## Protobuf API { #protobuf-api }

The advanced client reuses the exact same streaming-focused `.proto` contract from the advanced server guide.

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

The `stream` keyword is the whole difference. It appears on the request side, the response side, or both, and it is what makes the generator produce observer-based methods instead of plain
request/response methods.

## Dependencies { #dependencies }

The advanced client module uses the same core client stack as the base client.

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
        annotationProcessor.extendsFrom(koraBom)
        implementation.extendsFrom(koraBom)
        testCompileOnly.extendsFrom(koraBom)
        testAnnotationProcessor.extendsFrom(koraBom)
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

Nothing new is needed for streaming: `io.koraframework:grpc-client` already ships the `grpc-okhttp` transport and `grpc-stub`, and the async stubs come from the same generated code as the blocking ones.

!!! warning "Keep every `io.grpc` artifact on one version"

    The gRPC runtime shipped with `io.koraframework:grpc-client` is `1.83.1`. Every other `io.grpc` artifact you declare — `grpc-protobuf` and anything in test scope such as `grpc-inprocess` — must use
    exactly that version. A pinned older version compiles fine and fails only at runtime with
    `AbstractMethodError: ... does not define or inherit an implementation of the resolved method`.

## Code Generation { #code-generation }

The Gradle protobuf setup stays the same idea as in the base client guide:

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

What changes is not code generation itself, but the kinds of generated stubs we use:

- `UserStreamingServiceBlockingStub` for server-streaming reads, where the response arrives as an `Iterator`
- `UserStreamingServiceStub` (async) for client and bidirectional streaming, which have no blocking variant at all

Both are injectable directly, with no `@Tag` on the stub — Kora resolves the tagged `Channel` for `UserStreamingService` behind the scenes.

## Configuration { #config }

The advanced server protects the streaming service with an API key in gRPC metadata, so the advanced client must know two things:

- where the server lives
- which API key to send

For the full configuration reference, see [HTTP Server](../documentation/http-server.md), [Configuration](../documentation/config.md), [gRPC Client](../documentation/grpc-client.md)
and [Logging SLF4J](../documentation/logging-slf4j.md).

===! ":material-code-json: `Hocon`"

    ```javascript title="src/main/resources/application.conf"
    httpServer {
      port = 8081 //(1)!
      system.port = 8086 //(2)!
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
        "io.koraframework": "INFO" //(10)!
        "io.koraframework.guide.grpcclient.advanced": "INFO" //(11)!
      }
    }
    ```

    1. Public HTTP server port used by the local guide endpoint (default: `8080`).
    2. System HTTP server port used by probes and metrics (default: `8085`).
    3. Enables request logging for the public HTTP server (default: `false`).
    4. API key sent by the auth interceptor, read through a `@ConfigSource` interface.
    5. Optional override of the API key from the `GRPC_STREAMING_API_KEY` environment variable.
    6. Target URL of the advanced gRPC server (required, no default).
    7. Optional override of the target URL from the `GRPC_STREAMING_SERVER_URL` environment variable.
    8. Enables gRPC call logging for this client (default: `false`).
    9. Log level for `ROOT`.
    10. Log level for `io.koraframework`.
    11. Log level for `io.koraframework.guide.grpcclient.advanced`.

=== ":simple-yaml: `YAML`"

    ```yaml title="src/main/resources/application.yaml"
    httpServer:
      port: 8081 #(1)!
      system:
        port: 8086 #(2)!
      telemetry:
        logging:
          enabled: true #(3)!
    auth:
      apiKey:
        value: ${GRPC_STREAMING_API_KEY:test-api-key} #(4)!
    grpcClient:
      UserStreamingService:
        url: ${GRPC_STREAMING_SERVER_URL:http://localhost:8092} #(5)!
        telemetry:
          logging:
            enabled: true #(6)!
    logging:
      levels:
        ROOT: "INFO" #(7)!
        "io.koraframework": "INFO" #(8)!
        "io.koraframework.guide.grpcclient.advanced": "INFO" #(9)!
    ```

    1. Public HTTP server port used by the local guide endpoint (default: `8080`).
    2. System HTTP server port used by probes and metrics (default: `8085`).
    3. Enables request logging for the public HTTP server (default: `false`).
    4. API key sent by the auth interceptor, read through a `@ConfigSource` interface. Uses the shown default and allows `GRPC_STREAMING_API_KEY` to override it.
    5. Target URL of the advanced gRPC server (required, no default). Uses the shown default and allows `GRPC_STREAMING_SERVER_URL` to override it.
    6. Enables gRPC call logging for this client (default: `false`).
    7. Log level for `ROOT`.
    8. Log level for `io.koraframework`.
    9. Log level for `io.koraframework.guide.grpcclient.advanced`.

Two things are worth noticing.

The config section is `grpcClient.UserStreamingService`, not `grpcClient.UserService`. Kora derives the path from the *simple* protobuf service name of the stub you inject, so the two services in this
contract are configured — and connected — independently, even though they live in the same `.proto` file and on the same server port.

Just like in the base client guide, the local URL uses `http://...` so the gRPC client runs in plaintext mode for this demo setup. Switch it to `https://...` and the same channel is built over TLS; for
`mTLS` or a private certificate authority, add a `ChannelCredentials` component tagged with the generated service class, as described in
[gRPC Client: Transport and TLS](../documentation/grpc-client.md#transport-tls).

## Client Interceptor { #client-interceptor }

For more on client-side gRPC interceptors and metadata, see [gRPC Client: Interceptors](../documentation/grpc-client.md#interceptors).

Client interceptors are the client-side equivalent of transport middleware. They are useful for concerns that should happen for outgoing calls in one place:

- logging
- authentication
- deadlines
- tracing

Unlike the [HTTP client](../documentation/http-client.md#interceptors), gRPC interceptors have no method, class, or global tiers. Every interceptor is scoped **per client** by tagging the component
with the generated service class.

The advanced client adds a simple logging interceptor:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/grpcclient/advanced/grpc/LoggingInterceptor.java"
    package io.koraframework.guide.grpcclient.advanced.grpc;

    import io.grpc.CallOptions;
    import io.grpc.Channel;
    import io.grpc.ClientCall;
    import io.grpc.ClientInterceptor;
    import io.grpc.MethodDescriptor;
    import org.slf4j.Logger;
    import org.slf4j.LoggerFactory;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.common.annotation.Tag;
    import io.koraframework.guide.grpcserver.advanced.UserStreamingServiceGrpc;

    @Tag(UserStreamingServiceGrpc.class) //(1)!
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

    1. Scopes the interceptor to the `UserStreamingService` client only.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/grpcclient/advanced/grpc/LoggingInterceptor.kt"
    package io.koraframework.guide.grpcclient.advanced.grpc

    import io.grpc.*
    import org.slf4j.LoggerFactory
    import io.koraframework.common.annotation.Component
    import io.koraframework.common.annotation.Tag
    import io.koraframework.guide.grpcserver.advanced.UserStreamingServiceGrpc

    @Tag(UserStreamingServiceGrpc::class) //(1)!
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

    1. Scopes the interceptor to the `UserStreamingService` client only.

The `@Tag(UserStreamingServiceGrpc.class)` is not decoration — it is the *only* wiring. `ManagedChannelLifecycle` collects `All<ClientInterceptor>` carrying that tag when it builds the channel. Drop
the tag and the interceptor is never applied to any client; change it to another service class and it moves to that client instead.

Because a component carries exactly one `@Tag`, one interceptor instance cannot serve several clients. To reuse one implementation across clients, declare the class without `@Component` and publish it
once per client from the application module, each time with its own tag — see [Shared across clients](../documentation/grpc-client.md#shared-interceptors).

Kora registers your interceptors first, then its telemetry interceptor, then the deadline interceptor. gRPC invokes interceptors in reverse registration order, so a call travels:

```
Call -> Config (deadline) interceptor -> Telemetry interceptor -> Your interceptors -> gRPC Server
```

Two practical consequences: your interceptors already see the effective deadline in `CallOptions`, and everything they do happens inside the telemetry span and the measured call duration.

## Authorization Interceptor { #authorization-interceptor }

Now we make the client automatically send the API key expected by the advanced server.

The key itself comes from configuration through a small `@ConfigSource` interface:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/grpcclient/advanced/grpc/UserStreamingAuthConfig.java"
    package io.koraframework.guide.grpcclient.advanced.grpc;

    import io.koraframework.config.common.annotation.ConfigSource;

    @ConfigSource("auth.apiKey")
    public interface UserStreamingAuthConfig {

        String value();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/grpcclient/advanced/grpc/UserStreamingAuthConfig.kt"
    package io.koraframework.guide.grpcclient.advanced.grpc

    import io.koraframework.config.common.annotation.ConfigSource

    @ConfigSource("auth.apiKey")
    interface UserStreamingAuthConfig {
        fun value(): String
    }
    ```

The interceptor injects that config and puts the key on the outgoing call `Metadata`:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/grpcclient/advanced/grpc/UserStreamingAuthInterceptor.java"
    package io.koraframework.guide.grpcclient.advanced.grpc;

    import io.grpc.CallOptions;
    import io.grpc.Channel;
    import io.grpc.ClientCall;
    import io.grpc.ClientInterceptor;
    import io.grpc.ForwardingClientCall;
    import io.grpc.Metadata;
    import io.grpc.MethodDescriptor;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.common.annotation.Tag;
    import io.koraframework.guide.grpcserver.advanced.UserStreamingServiceGrpc;

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
                public void start(Listener<RespT> responseListener, Metadata headers) { //(1)!
                    headers.put(AUTHORIZATION_HEADER, authConfig.value());
                    super.start(responseListener, headers);
                }
            };
        }
    }
    ```

    1. `start(...)` is the only place where headers can still be modified — it runs once per call, right before the request is sent.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/grpcclient/advanced/grpc/UserStreamingAuthInterceptor.kt"
    package io.koraframework.guide.grpcclient.advanced.grpc

    import io.grpc.*
    import io.koraframework.common.annotation.Component
    import io.koraframework.common.annotation.Tag
    import io.koraframework.guide.grpcserver.advanced.UserStreamingServiceGrpc

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
                override fun start(responseListener: Listener<RespT>, headers: Metadata) { //(1)!
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

    1. `start(...)` is the only place where headers can still be modified — it runs once per call, right before the request is sent.

This is the gRPC equivalent of automatically attaching auth headers in an advanced HTTP client. The header is attached once per call, so it also covers long-lived streaming calls: the credential travels
in the call's initial metadata, not with every message.

## Streaming Client { #streaming-client }

Now we can wrap the generated streaming stubs in a small client-side service.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/grpcclient/advanced/service/UserStreamingClientService.java"
    package io.koraframework.guide.grpcclient.advanced.service;

    import com.google.protobuf.Empty;
    import io.grpc.stub.StreamObserver;
    import java.time.LocalDateTime;
    import java.time.ZoneOffset;
    import java.util.ArrayList;
    import java.util.List;
    import java.util.concurrent.CompletableFuture;
    import java.util.concurrent.CopyOnWriteArrayList;
    import java.util.concurrent.TimeUnit;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.grpcclient.advanced.dto.UserRequest;
    import io.koraframework.guide.grpcclient.advanced.dto.UserResponse;
    import io.koraframework.guide.grpcclient.advanced.dto.UserUpdateRequest;
    import io.koraframework.guide.grpcserver.advanced.CreateUserRequest;
    import io.koraframework.guide.grpcserver.advanced.CreateUsersResponse;
    import io.koraframework.guide.grpcserver.advanced.UpdateUserRequest;
    import io.koraframework.guide.grpcserver.advanced.UserStreamingServiceGrpc;

    @Component
    public final class UserStreamingClientService {

        private final UserStreamingServiceGrpc.UserStreamingServiceBlockingStub blockingStub; //(1)!
        private final UserStreamingServiceGrpc.UserStreamingServiceStub asyncStub; //(2)!

        public UserStreamingClientService(
                UserStreamingServiceGrpc.UserStreamingServiceBlockingStub blockingStub,
                UserStreamingServiceGrpc.UserStreamingServiceStub asyncStub) {
            this.blockingStub = blockingStub;
            this.asyncStub = asyncStub;
        }

        public CreateUsersResult createUsers(List<UserRequest> requests) { //(3)!
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
                requestObserver.onCompleted(); //(4)!
                return future.get(5, TimeUnit.SECONDS);
            } catch (Exception e) {
                requestObserver.onError(e);
                throw new RuntimeException("Failed to create users over gRPC streaming", e);
            }
        }

        public List<UserResponse> getAllUsers() { //(5)!
            var users = new ArrayList<UserResponse>();
            var iterator = this.blockingStub.getAllUsers(Empty.getDefaultInstance());
            iterator.forEachRemaining(user -> users.add(toDto(user)));
            return users;
        }

        public List<UserResponse> updateUsers(List<UserUpdateRequest> updates) { //(6)!
            var future = new CompletableFuture<List<UserResponse>>();
            var responses = new CopyOnWriteArrayList<UserResponse>();
            var responseObserver = new StreamObserver<io.koraframework.guide.grpcserver.advanced.UserResponse>() {
                @Override
                public void onNext(io.koraframework.guide.grpcserver.advanced.UserResponse value) {
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

        private UserResponse toDto(io.koraframework.guide.grpcserver.advanced.UserResponse response) {
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

    1. Server streaming — the blocking stub returns an `Iterator`.
    2. Client and bidirectional streaming — only the async stub has these methods.
    3. Client streaming: many requests in, one summary response out.
    4. Completing the request stream is what tells the server the batch is finished; without it the call hangs until the deadline.
    5. Server streaming: one request in, many responses out.
    6. Bidirectional streaming: both sides stream independently, and `onCompleted` on the response observer is the signal that the server is done.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/grpcclient/advanced/service/UserStreamingClientService.kt"
    package io.koraframework.guide.grpcclient.advanced.service

    import com.google.protobuf.Empty
    import io.grpc.stub.StreamObserver
    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.grpcclient.advanced.dto.UserRequest
    import io.koraframework.guide.grpcclient.advanced.dto.UserResponse
    import io.koraframework.guide.grpcclient.advanced.dto.UserUpdateRequest
    import io.koraframework.guide.grpcserver.advanced.CreateUserRequest
    import io.koraframework.guide.grpcserver.advanced.CreateUsersResponse
    import io.koraframework.guide.grpcserver.advanced.UpdateUserRequest
    import io.koraframework.guide.grpcserver.advanced.UserStreamingServiceGrpc
    import java.time.LocalDateTime
    import java.time.ZoneOffset
    import java.util.concurrent.CompletableFuture
    import java.util.concurrent.CopyOnWriteArrayList
    import java.util.concurrent.TimeUnit

    @Component
    class UserStreamingClientService(
        private val blockingStub: UserStreamingServiceGrpc.UserStreamingServiceBlockingStub, //(1)!
        private val asyncStub: UserStreamingServiceGrpc.UserStreamingServiceStub //(2)!
    ) {

        fun createUsers(requests: List<UserRequest>): CreateUsersResult { //(3)!
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
                requestObserver.onCompleted() //(4)!
                return future.get(5, TimeUnit.SECONDS)
            } catch (e: Exception) {
                requestObserver.onError(e)
                throw RuntimeException("Failed to create users over gRPC streaming", e)
            }
        }

        fun getAllUsers(): List<UserResponse> { //(5)!
            val users = mutableListOf<UserResponse>()
            val iterator = blockingStub.getAllUsers(Empty.getDefaultInstance())
            iterator.forEachRemaining { user -> users += toDto(user) }
            return users
        }

        fun updateUsers(updates: List<UserUpdateRequest>): List<UserResponse> { //(6)!
            val future = CompletableFuture<List<UserResponse>>()
            val responses = CopyOnWriteArrayList<UserResponse>()
            val responseObserver = object : StreamObserver<io.koraframework.guide.grpcserver.advanced.UserResponse> {
                override fun onNext(value: io.koraframework.guide.grpcserver.advanced.UserResponse) {
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

        private fun toDto(response: io.koraframework.guide.grpcserver.advanced.UserResponse): UserResponse {
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

    1. Server streaming — the blocking stub returns an `Iterator`.
    2. Client and bidirectional streaming — only the async stub has these methods.
    3. Client streaming: many requests in, one summary response out.
    4. Completing the request stream is what tells the server the batch is finished; without it the call hangs until the deadline.
    5. Server streaming: one request in, many responses out.
    6. Bidirectional streaming: both sides stream independently, and `onCompleted` on the response observer is the signal that the server is done.

The shape of every method is the same, and it is the shape you will reuse in your own code:

1. create a `CompletableFuture` for the result the caller is waiting for
2. create a `StreamObserver` that fills it from `onNext` / `onCompleted` and fails it from `onError`
3. hand that observer to the async stub and get a request observer back
4. write requests, then call `onCompleted()`
5. block on the future with a bounded timeout

The bounded `future.get(5, TimeUnit.SECONDS)` matters. A streaming call has no implicit end: if the server never completes the response stream and no deadline is configured, an unbounded `get()` would
hang forever. Configuring `grpcClient.UserStreamingService.timeout` gives the same protection at the transport level, and then a stalled call fails with `DEADLINE_EXCEEDED`.

### Coroutine Alternative { #coroutine-alternative }

The observer plumbing above exists because these are Java stubs. If you generate the Kotlin coroutine stubs as well — see
[Kotlin Coroutine Stubs](grpc-client.md#kotlin-coroutine-stubs) — the same three shapes collapse into ordinary suspend and `Flow` code:

```kotlin
val users: Flow<UserResponse> = coroutineStub.getAllUsers(Empty.getDefaultInstance())          // server streaming
val summary: CreateUsersResponse = coroutineStub.createUsers(flowOf(request1, request2))       // client streaming
val updated: Flow<UserResponse> = coroutineStub.updateUsers(flowOf(update1, update2))          // bidirectional
```

The coroutine stub is injectable exactly like the Java ones, and the interceptors tagged above apply to it too, because both stub families share the same tagged `Channel`. This guide keeps the Java
stubs in both language variants so the Java and Kotlin listings stay directly comparable.

## Check Controller { #check-controller }

The companion app exposes one HTTP endpoint that exercises all three streaming shapes in order.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/grpcclient/advanced/controller/ClientTestController.java"
    package io.koraframework.guide.grpcclient.advanced.controller;

    import java.util.List;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.grpcclient.advanced.dto.UserRequest;
    import io.koraframework.guide.grpcclient.advanced.dto.UserUpdateRequest;
    import io.koraframework.guide.grpcclient.advanced.service.UserStreamingClientService;
    import io.koraframework.http.common.HttpMethod;
    import io.koraframework.http.common.annotation.HttpRoute;
    import io.koraframework.http.server.common.annotation.HttpController;
    import io.koraframework.json.common.annotation.Json;

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
            String error) {
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/grpcclient/advanced/controller/ClientTestController.kt"
    package io.koraframework.guide.grpcclient.advanced.controller

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.grpcclient.advanced.dto.UserRequest
    import io.koraframework.guide.grpcclient.advanced.dto.UserUpdateRequest
    import io.koraframework.guide.grpcclient.advanced.service.UserStreamingClientService
    import io.koraframework.http.common.HttpMethod
    import io.koraframework.http.common.annotation.HttpRoute
    import io.koraframework.http.server.common.annotation.HttpController
    import io.koraframework.json.common.annotation.Json

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

The controller needs one more DTO than the base client — `UserUpdateRequest`, because a bidirectional update carries the user id alongside the new values:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/grpcclient/advanced/dto/UserUpdateRequest.java"
    package io.koraframework.guide.grpcclient.advanced.dto;

    import io.koraframework.json.common.annotation.Json;

    @Json
    public record UserUpdateRequest(String userId, String name, String email) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/grpcclient/advanced/dto/UserUpdateRequest.kt"
    package io.koraframework.guide.grpcclient.advanced.dto

    import io.koraframework.json.common.annotation.Json

    @Json
    data class UserUpdateRequest(val userId: String, val name: String, val email: String)
    ```

## Run Application { #run-app }

Build the generated sources and compile the app:

```bash
./gradlew clean classes
```

Start the advanced server first, with the API key it expects:

```bash
GRPC_STREAMING_API_KEY=test-api-key ./gradlew run
```

Then start the advanced client with the same key:

```bash
GRPC_STREAMING_API_KEY=test-api-key ./gradlew run
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

The advanced client tests also use the in-process gRPC approach: an `InProcessServerBuilder` runs a fake `UserStreamingServiceImplBase`, and `ClientInterceptors.intercept(channel, ...)` applies the
same auth and logging interceptors the graph would apply. The service under test is then constructed by hand from `newBlockingStub(interceptedChannel)` and `newStub(interceptedChannel)`.

That is especially useful here because it lets the tests simulate:

- successful streaming interactions
- rejected calls without an API key — the fake server closes the call with `Status.UNAUTHENTICATED`, and the test asserts that exact code
- interceptor behavior, by building one stub with interceptors and one without

Run them with:

```bash
./gradlew test
```

## Best Practices { #best-practices }

- Keep advanced streaming work in a dedicated client service instead of bloating the unary client.
- Tag every interceptor with the generated service class; an untagged `ClientInterceptor` is applied to no client at all.
- Use client interceptors for metadata-based auth instead of repeating header logic in every call site.
- Always complete the request stream, and always bound the wait for the response stream.
- Keep stream lifecycle handling close to the transport boundary.
- Prefer in-process gRPC servers for fast client-side streaming tests.
- Keep every `io.grpc` artifact on the version that ships with `io.koraframework:grpc-client`.
- Annotate handwritten DTOs with `@Json` only when they cross an HTTP/JSON boundary; generated protobuf messages do not need JSON annotations.

## Summary { #summary }

In this guide you built a streaming gRPC client that mirrors the advanced server guide.

The important idea was not only "how to call streaming RPCs", but also "how to structure the client cleanly":

- separate unary and streaming concerns
- add auth and logging through interceptors tagged to one generated service
- wrap generated stubs in a focused service layer

## Key Concepts { #key-concepts }

- how advanced gRPC clients differ from unary gRPC clients
- how blocking and async stubs are used for different streaming patterns
- how `@Tag(ServiceGrpc.class)` scopes a `ClientInterceptor` to one client
- how the interceptor chain orders your interceptors relative to telemetry and deadlines
- how client interceptors add logging and metadata auth
- how to consume server, client, and bidirectional streaming methods
- how to test advanced gRPC client behavior with `InProcessServer`

## Troubleshooting { #troubleshooting }

**Streaming call never completes:**

Check that the request stream is completed on the client side with `onCompleted()` and that the server sends completion signals. Bound the wait — either with a timeout on the future or with
`grpcClient.<Service>.timeout`.

**Interceptor never runs:**

Verify the `@Tag`. An untagged `ClientInterceptor` component is not collected by any client, and a tag naming another generated service moves it to that client.

**Calls are rejected as `UNAUTHENTICATED`:**

Verify that the client and server use the same API key value and that the auth interceptor is tagged to the generated streaming client.

**Configuration seems to be ignored:**

The config path is the *simple* protobuf service name — `grpcClient.UserStreamingService`. The base `grpcClient.UserService` section configures a different client.

**In-process tests pass but runtime calls fail:**

Compare the runtime `application.conf` with the in-process test wiring, especially gRPC host, port, and interceptor tags.

## What's Next? { #whats-next }

- [Resilient Patterns](resilient.md) to protect streaming and unary RPC calls against slow or unavailable services.
- [Observability](observability.md) to trace gRPC client calls, streaming lifecycles, and interceptor behavior.
- [Messaging with Kafka](messaging-kafka.md) to compare RPC-style integration with asynchronous event-driven integration.
- [HTTP Client Advanced](http-client-advanced.md) to compare advanced gRPC and advanced HTTP client boundaries.

## Help { #help }

If something does not work:

- compare with [Kora Java gRPC Client Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-grpc-client-advanced-app) and [Kora Kotlin gRPC Client Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-grpc-client-advanced-app)
- check the [gRPC Client documentation](../documentation/grpc-client.md)
- verify the advanced server from [Advanced gRPC Server](grpc-server-advanced.md) is running on port `8092`
- make sure the client and server use the same API key value
