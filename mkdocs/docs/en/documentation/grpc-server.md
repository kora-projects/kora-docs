---
description: "Explains Kora gRPC server: protobuf Gradle plugin setup, server configuration, unary and streaming handlers, io.grpc.Status error handling, ServerInterceptor interceptors and their execution order, lifecycle and readiness, telemetry, and reflection. Use when working with GrpcServerModule, GrpcServerConfig, GrpcServerBuilderConfigurer, ServerInterceptor, StreamObserver, reflectionEnabled, Server Reflection."
agent:
  use_when: "Use this file for Kora docs or implementation questions about the Kora gRPC server: protobuf Gradle plugin setup, server configuration, unary and streaming handlers, io.grpc.Status error handling, ServerInterceptor interceptors and their execution order, scoping and metadata authorization, lifecycle and readiness, telemetry, and reflection; key triggers include GrpcServerModule, GrpcServerConfig, GrpcServerBuilderConfigurer, ServerInterceptor, StreamObserver, reflectionEnabled, Server Reflection. Note: gRPC server interceptors are global io.grpc.ServerInterceptor beans only; there is no @GrpcService or @InterceptWith annotation in this module."
---

The module starts a `gRPC server` based on [`grpc-java`](https://grpc.io/docs/languages/java/basics/) and connects handlers from the application graph to it.
A handler is a `BindableService`, usually a class that extends a generated `...ImplBase` and implements unary or streaming `RPC` methods.

Kora creates a `NettyServerBuilder`, adds server services, user-defined and standard `ServerInterceptor`, manages the server lifecycle, and participates in application readiness checks.
If configuration parameters are not enough, the resulting `NettyServerBuilder` can be additionally configured in code through `GrpcServerBuilderConfigurer`.

For a step-by-step walkthrough before the reference details, see [gRPC Server](../guides/grpc-server.md) and [Advanced gRPC Server](../guides/grpc-server-advanced.md).

## Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) in `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:grpc-server"
    implementation "io.grpc:grpc-protobuf:1.74.0"
    implementation "javax.annotation:javax.annotation-api:1.3.2"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends GrpcServerModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) in `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:grpc-server")
    implementation("io.grpc:grpc-protobuf:1.74.0")
    implementation("javax.annotation:javax.annotation-api:1.3.2")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : GrpcServerModule
    ```

### Plugin { #plugin }

The code for the `gRPC server` is generated with the [protobuf gradle plugin](https://github.com/google/protobuf-gradle-plugin).

===! ":fontawesome-brands-java: `Java`"

    Plugin in `build.gradle`:
    ```groovy
    plugins {
        id "com.google.protobuf" version "0.9.4"
    }

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
        main.java {
            srcDirs "build/generated/source/proto/main/grpc"
            srcDirs "build/generated/source/proto/main/java"
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Plugin in `build.gradle.kts`:
    ```groovy
    import com.google.protobuf.gradle.id

    plugins {
        id("com.google.protobuf") version ("0.9.4")
    }

    protobuf {
        protoc { artifact = "com.google.protobuf:protoc:3.25.3" }
        plugins {
            id("grpc") { artifact = "io.grpc:protoc-gen-grpc-java:1.74.0" }
        }
        generateProtoTasks {
            ofSourceSet("main").forEach { it.plugins { id("grpc") { } } }
        }
    }

    kotlin {
        sourceSets.main {
            kotlin.srcDir("build/generated/source/proto/main/grpc")
            kotlin.srcDir("build/generated/source/proto/main/java")
        }
    }
    ```

## Configuration { #configuration }

Only `port` typically needs to be set; all other parameters have defaults.
A minimal configuration that binds a port from an environment variable and enables logging looks like this:

===! ":material-code-json: `Hocon`"

    ```javascript
    grpcServer {
        port = 8090
        telemetry.logging.enabled = true
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    grpcServer:
      port: 8090
      telemetry:
        logging:
          enabled: true
    ```

Basic configuration parameters:

===! ":material-code-json: `Hocon`"

    ```javascript
    grpcServer {
        port = 8090 //(1)!
        maxMessageSize = "4MiB" //(2)!
        reflectionEnabled = false //(3)!
    }
    ```

    1. `gRPC server` port (default: `8090`).
    2. Maximum incoming message size (default: `4MiB`).
    3. Enables [`gRPC Server Reflection`](#reflection) service (default: `false`).

=== ":simple-yaml: `YAML`"

    ```yaml
    grpcServer:
      port: 8090 #(1)!
      maxMessageSize: "4MiB" #(2)!
      reflectionEnabled: false #(3)!
    ```

    1. `gRPC server` port (default: `8090`).
    2. Maximum incoming message size (default: `4MiB`).
    3. Enables [`gRPC Server Reflection`](#reflection) service (default: `false`).

??? note "Full Configuration"

    Example of a complete configuration described by `GrpcServerConfig`:

    ===! ":material-code-json: `Hocon`"

        ```javascript
        grpcServer {
            port = 8090 //(1)!
            maxMessageSize = "4MiB" //(2)!
            reflectionEnabled = false //(3)!
            shutdownWait = "30s" //(4)!
            maxConnectionAge = "0s" //(5)!
            maxConnectionAgeGrace = "0s" //(6)!
            keepAliveTime = "0s" //(7)!
            keepAliveTimeout = "0s" //(8)!
            telemetry {
                logging {
                    enabled = false //(9)!
                }
                metrics {
                    enabled = true //(10)!
                    slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(11)!
                    tags = { // (12)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
                tracing {
                    enabled = true //(13)!
                    attributes = { // (14)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
            }
        }
        ```

        1. `gRPC server` port (default: `8090`).
        2. Maximum size of an incoming message (default: `4MiB`). It can be specified as a number of bytes or as `4MiB`, `4MB`, `1000Kb`, and similar values.
        3. Enables the [`gRPC Server Reflection`](#reflection) service (default: `false`).
        4. Time to wait for processing before shutting down the server during [graceful shutdown](container.md#graceful-shutdown) (default: `30s`).
        5. Sets a custom maximum connection age after which the connection is gracefully terminated (default: not specified, optional). A random jitter of +/-10% is added to the value.
        6. Sets additional time for graceful connection termination after the maximum connection age is reached (default: not specified, optional). `RPC` calls that do not finish in time are cancelled so the connection can terminate.
        7. Sets the interval between `PING` frames (default: not specified, optional).
        8. Timeout for acknowledging a `PING` frame (default: not specified, optional). If no acknowledgement is received within this time, the connection is closed.
        9. Enables module logging (default: `false`).
        10. Enables module metrics (default: `true`).
        11. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for the [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metric (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
        12. Metric tags (default: `{}`).
        13. Enables module tracing (default: `true`).
        14. Tracing attributes (default: `{}`).

    === ":simple-yaml: `YAML`"

        ```yaml
        grpcServer:
          port: 8090 #(1)!
          maxMessageSize: "4MiB" #(2)!
          reflectionEnabled: false #(3)!
          shutdownWait: "30s" #(4)!
          maxConnectionAge: "0s" #(5)!
          maxConnectionAgeGrace: "0s" #(6)!
          keepAliveTime: "0s" #(7)!
          keepAliveTimeout: "0s" #(8)!
          telemetry:
            logging:
              enabled: false #(9)!
            metrics:
              enabled: true #(10)!
              slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(11)!
              tags: #(12)!
                key1: value1
                key2: value2
            tracing:
              enabled: true #(13)!
              attributes: #(14)!
                key1: value1
                key2: value2
        ```

        1. `gRPC server` port (default: `8090`).
        2. Maximum size of an incoming message (default: `4MiB`). It can be specified as a number of bytes or as `4MiB`, `4MB`, `1000Kb`, and similar values.
        3. Enables the [`gRPC Server Reflection`](#reflection) service (default: `false`).
        4. Time to wait for processing before shutting down the server during [graceful shutdown](container.md#graceful-shutdown) (default: `30s`).
        5. Sets a custom maximum connection age after which the connection is gracefully terminated (default: not specified, optional). A random jitter of +/-10% is added to the value.
        6. Sets additional time for graceful connection termination after the maximum connection age is reached (default: not specified, optional). `RPC` calls that do not finish in time are cancelled so the connection can terminate.
        7. Sets the interval between `PING` frames (default: not specified, optional).
        8. Timeout for acknowledging a `PING` frame (default: not specified, optional). If no acknowledgement is received within this time, the connection is closed.
        9. Enables module logging (default: `false`).
        10. Enables module metrics (default: `true`).
        11. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for the [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metric (default: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
        12. Metric tags (default: `{}`).
        13. Enables module tracing (default: `true`).
        14. Tracing attributes (default: `{}`).

You can also configure [Netty transport](netty.md).

### Configuration In Code { #builder-configurer }

If configuration parameters are not enough, register a `GrpcServerBuilderConfigurer` component and additionally configure `NettyServerBuilder` in code.
This component is called after configuration has been applied and after services, user-defined `ServerInterceptor`, and standard `ServerInterceptor` have been added.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MyGrpcServerBuilderConfigurer implements GrpcServerBuilderConfigurer {

        @Override
        public NettyServerBuilder configure(NettyServerBuilder builder) {
            return builder.permitKeepAliveWithoutCalls(true);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyGrpcServerBuilderConfigurer : GrpcServerBuilderConfigurer {

        override fun configure(builder: NettyServerBuilder): NettyServerBuilder {
            return builder.permitKeepAliveWithoutCalls(true)
        }
    }
    ```

Module metrics are described in the [Metrics Reference](metrics.md#grpc-server) section.

## Handlers { #handlers }

A handler is a class that extends the generated `...ImplBase` and is registered in the application graph with the `@Component` annotation.
The `...ImplBase` class is produced from the `proto` contract by the [protobuf gradle plugin](#plugin); you override its `RPC` methods to implement server behavior.
Ordinary Kora components such as services and repositories can be injected into a handler through its constructor.

Consider a `proto` contract with a single unary method:

```protobuf title="src/main/proto/message.proto"
syntax = "proto3";

package ru.tinkoff.kora.generated.grpc;

service UserService {
  rpc createUser(RequestEvent) returns (ResponseEvent) {} //(1)!
}

message RequestEvent {
  string name = 1;
  string code = 2;
}

message ResponseEvent {
  bytes id = 1;
}
```

1. A unary `RPC`: one request message produces one response message.

The plugin generates `UserServiceGrpc.UserServiceImplBase`, and the handler overrides the generated method.
The generated method receives the request message and a [`StreamObserver`](https://grpc.github.io/grpc-java/javadoc/io/grpc/stub/StreamObserver.html)
that is used to send responses back to the client:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class UserService extends UserServiceGrpc.UserServiceImplBase {

        @Override
        public void createUser(Message.RequestEvent request, StreamObserver<Message.ResponseEvent> responseObserver) { //(1)!
            var response = Message.ResponseEvent.newBuilder()
                .setId(ByteString.copyFromUtf8(UUID.randomUUID().toString()))
                .build();

            responseObserver.onNext(response); //(2)!
            responseObserver.onCompleted(); //(3)!
        }
    }
    ```

    1. The generated method receives the request message and a `StreamObserver` for sending the response
    2. Sends a single response message to the client
    3. Signals that the call is complete; for a unary method it is called exactly once, after a single `onNext`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class UserService : UserServiceGrpc.UserServiceImplBase() {

        override fun createUser(request: Message.RequestEvent, responseObserver: StreamObserver<Message.ResponseEvent>) { //(1)!
            val response = Message.ResponseEvent.newBuilder()
                .setId(ByteString.copyFromUtf8(UUID.randomUUID().toString()))
                .build()

            responseObserver.onNext(response) //(2)!
            responseObserver.onCompleted() //(3)!
        }
    }
    ```

    1. The generated method receives the request message and a `StreamObserver` for sending the response
    2. Sends a single response message to the client
    3. Signals that the call is complete; for a unary method it is called exactly once, after a single `onNext`

### Server streaming { #server-streaming }

For a server-streaming `RPC` (`returns (stream ...)` in the `proto`), the client sends one request and the server sends back many messages.
Call `onNext` for each message, then `onCompleted` once at the end:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Override
    public void getAllUsers(Message.RequestEvent request, StreamObserver<Message.ResponseEvent> responseObserver) {
        for (var user : userService.findAll()) {
            responseObserver.onNext(toResponse(user)); //(1)!
        }
        responseObserver.onCompleted(); //(2)!
    }
    ```

    1. Sends one of several response messages
    2. Completes the response stream after the last message

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    override fun getAllUsers(request: Message.RequestEvent, responseObserver: StreamObserver<Message.ResponseEvent>) {
        userService.findAll().forEach { responseObserver.onNext(toResponse(it)) } //(1)!
        responseObserver.onCompleted() //(2)!
    }
    ```

    1. Sends one of several response messages
    2. Completes the response stream after the last message

### Client streaming { #client-streaming }

For a client-streaming `RPC` (`rpc method(stream ...)`), the client sends many messages and the server answers once at the end.
The generated method **returns** a `StreamObserver` that receives the incoming request messages; the final response is produced from `onCompleted`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Override
    public StreamObserver<Message.RequestEvent> createUsers(StreamObserver<Message.ResponseEvent> responseObserver) {
        return new StreamObserver<>() {
            private final List<Message.RequestEvent> received = new ArrayList<>();

            @Override
            public void onNext(Message.RequestEvent value) {
                received.add(value); //(1)!
            }

            @Override
            public void onError(Throwable t) {
                responseObserver.onError(t); //(2)!
            }

            @Override
            public void onCompleted() {
                responseObserver.onNext(aggregate(received)); //(3)!
                responseObserver.onCompleted();
            }
        };
    }
    ```

    1. Collects each incoming request message
    2. Propagates a client-side stream error
    3. Produces the single aggregated response once the client has finished sending

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    override fun createUsers(responseObserver: StreamObserver<Message.ResponseEvent>): StreamObserver<Message.RequestEvent> {
        return object : StreamObserver<Message.RequestEvent> {
            private val received = mutableListOf<Message.RequestEvent>()

            override fun onNext(value: Message.RequestEvent) {
                received += value //(1)!
            }

            override fun onError(t: Throwable) {
                responseObserver.onError(t) //(2)!
            }

            override fun onCompleted() {
                responseObserver.onNext(aggregate(received)) //(3)!
                responseObserver.onCompleted()
            }
        }
    }
    ```

    1. Collects each incoming request message
    2. Propagates a client-side stream error
    3. Produces the single aggregated response once the client has finished sending

### Bidirectional streaming { #bidirectional-streaming }

For a bidirectional-streaming `RPC` (`rpc method(stream ...) returns (stream ...)`), both sides exchange many messages on the same call.
The method returns a `StreamObserver` for the incoming requests and can send responses at any time through `responseObserver`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Override
    public StreamObserver<Message.RequestEvent> updateUsers(StreamObserver<Message.ResponseEvent> responseObserver) {
        return new StreamObserver<>() {
            @Override
            public void onNext(Message.RequestEvent value) {
                responseObserver.onNext(process(value)); //(1)!
            }

            @Override
            public void onError(Throwable t) {
                responseObserver.onError(t);
            }

            @Override
            public void onCompleted() {
                responseObserver.onCompleted(); //(2)!
            }
        };
    }
    ```

    1. Responds to each incoming message as it arrives
    2. Completes the response stream when the client stops sending

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    override fun updateUsers(responseObserver: StreamObserver<Message.ResponseEvent>): StreamObserver<Message.RequestEvent> {
        return object : StreamObserver<Message.RequestEvent> {
            override fun onNext(value: Message.RequestEvent) {
                responseObserver.onNext(process(value)) //(1)!
            }

            override fun onError(t: Throwable) {
                responseObserver.onError(t)
            }

            override fun onCompleted() {
                responseObserver.onCompleted() //(2)!
            }
        }
    }
    ```

    1. Responds to each incoming message as it arrives
    2. Completes the response stream when the client stops sending

### Error handling { #error-handling }

**Description**: gRPC represents call errors with an [`io.grpc.Status`](https://grpc.github.io/grpc-java/javadoc/io/grpc/Status.html)
code and an optional description rather than with HTTP response codes.
To fail a call, complete the response observer with `responseObserver.onError(status.asRuntimeException())`,
or throw a `StatusRuntimeException` from the handler.
The auto-registered [`TelemetryInterceptor`](#default) observes the terminal `Status` when the call is closed
(on `close`, `onHalfClose`, `onCancel`, and `onComplete`) and records logging, metrics, and tracing accordingly.

**Causes**: choose the `Status` code that matches the failure — for example `Status.NOT_FOUND` for a missing entity,
`Status.INVALID_ARGUMENT` for invalid input, `Status.UNAUTHENTICATED` or `Status.PERMISSION_DENIED` for authorization failures,
and `Status.INTERNAL` for unexpected server errors.

**Recommendations**:

- Attach a human-readable message with `withDescription(...)` and keep the original exception with `withCause(...)` so telemetry can record it.
- Complete a call exactly once: never call `onError` after `onCompleted`, and never call either twice.
- Do not leak internal exception details to clients; map them to an appropriate `Status` first.

**Handling example**: a unary handler that returns `NOT_FOUND` when an entity is missing and maps unexpected failures to `INTERNAL`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Override
    public void getUser(Message.RequestEvent request, StreamObserver<Message.ResponseEvent> responseObserver) {
        try {
            var user = userService.getUser(request.getName())
                .orElseThrow(() -> Status.NOT_FOUND
                    .withDescription("User not found: " + request.getName())
                    .asRuntimeException()); //(1)!
            responseObserver.onNext(toResponse(user));
            responseObserver.onCompleted();
        } catch (StatusRuntimeException e) {
            responseObserver.onError(e); //(2)!
        } catch (Exception e) {
            responseObserver.onError(Status.INTERNAL
                .withDescription("Failed to get user")
                .withCause(e) //(3)!
                .asRuntimeException());
        }
    }
    ```

    1. Builds a `NOT_FOUND` error with a description
    2. Forwards an already-mapped `Status` error to the client
    3. Keeps the original exception as the cause so telemetry can record it

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    override fun getUser(request: Message.RequestEvent, responseObserver: StreamObserver<Message.ResponseEvent>) {
        try {
            val user = userService.getUser(request.name)
                ?: throw Status.NOT_FOUND
                    .withDescription("User not found: ${request.name}")
                    .asRuntimeException() //(1)!
            responseObserver.onNext(toResponse(user))
            responseObserver.onCompleted()
        } catch (e: StatusRuntimeException) {
            responseObserver.onError(e) //(2)!
        } catch (e: Exception) {
            responseObserver.onError(
                Status.INTERNAL
                    .withDescription("Failed to get user")
                    .withCause(e) //(3)!
                    .asRuntimeException()
            )
        }
    }
    ```

    1. Builds a `NOT_FOUND` error with a description
    2. Forwards an already-mapped `Status` error to the client
    3. Keeps the original exception as the cause so telemetry can record it

### Signatures { #signatures }

The shape of a handler method is fixed by the `proto` contract and the generated `...ImplBase`:

===! ":fontawesome-brands-java: `Java`"

    By `Req` and `Resp` we mean the generated request and response message types.

    - Unary: `void myMethod(Req request, StreamObserver<Resp> responseObserver)`
    - Server streaming: `void myMethod(Req request, StreamObserver<Resp> responseObserver)` (multiple `onNext`, one `onCompleted`)
    - Client streaming: `StreamObserver<Req> myMethod(StreamObserver<Resp> responseObserver)`
    - Bidirectional streaming: `StreamObserver<Req> myMethod(StreamObserver<Resp> responseObserver)`

    The generated method returns `void` (or the request `StreamObserver`), so results are delivered asynchronously through the `StreamObserver` callbacks;
    responses may be completed from another thread.

=== ":simple-kotlin: `Kotlin`"

    By `Req` and `Resp` we mean the generated request and response message types.

    - Unary: `myMethod(request: Req, responseObserver: StreamObserver<Resp>)`
    - Server streaming: `myMethod(request: Req, responseObserver: StreamObserver<Resp>)` (multiple `onNext`, one `onCompleted`)
    - Client streaming: `myMethod(responseObserver: StreamObserver<Resp>): StreamObserver<Req>`
    - Bidirectional streaming: `myMethod(responseObserver: StreamObserver<Resp>): StreamObserver<Req>`

    When you generate coroutine stubs with the [`grpc-kotlin`](https://github.com/grpc/grpc-kotlin) plugin (`io.grpc:protoc-gen-grpc-kotlin`)
    and extend the generated `...CoroutineImplBase`, handler methods can be `suspend` functions (and streaming methods can use `Flow`).
    Kora auto-registers [`CoroutineContextInjectInterceptor`](#default), which injects the Kora `Context` into the handler's `CoroutineContext`;
    it activates only when `kotlinx-coroutines` is on the classpath.

## Interceptors { #interceptors }

An [`io.grpc.ServerInterceptor`](https://grpc.github.io/grpc-java/javadoc/io/grpc/ServerInterceptor.html) processes a call before it is passed to a `gRPC service`.
Interceptors are suitable for cross-cutting logic: logging, authorization, tracing, working with `Metadata`, and error mapping.

Unlike the [HTTP server](http-server.md#interceptors), the gRPC server module has **no** `@GrpcService` or `@InterceptWith` annotation:
every `ServerInterceptor` registered as a `@Component` is applied **globally** to all services on the server.
To limit an interceptor to a single service or method, inspect the call at runtime — see [Scoping and authorization](#authorization).

### Default { #default }

When the server starts, Kora adds standard interceptors:

- `TelemetryInterceptor` — enables server telemetry (logging, metrics, tracing) depending on connected modules and `grpcServer.telemetry` settings, and maps the terminal `Status`/exception when the call closes
- `ContextServerInterceptor` — propagates the Kora `Context` into call processing so it is available inside the handler
- `CoroutineContextInjectInterceptor` — adds `CoroutineContext` support for `Kotlin` coroutine handlers (active only when `kotlinx-coroutines` is on the classpath)

User-defined `ServerInterceptor` beans from the application graph are added to `NettyServerBuilder` before the standard interceptors.
For full `NettyServerBuilder` configuration, use [GrpcServerBuilderConfigurer](#builder-configurer).

### Execution order { #execution-order }

gRPC invokes interceptors in the **reverse** order of registration, so the last interceptor added runs first (outermost).
Because Kora registers user interceptors first and the standard interceptors last, an incoming call is processed in this order:

```
CoroutineContextInjectInterceptor -> ContextServerInterceptor -> TelemetryInterceptor -> user interceptors -> handler
```

Consequences of this order:

- The Kora `Context` and Kotlin `CoroutineContext` are established around your interceptors and the handler, so they are available inside the handler's listener callbacks.
- `TelemetryInterceptor` wraps your interceptors and the handler, so it observes the final `Status` (including errors thrown or reported through the response observer).
- When several user interceptors exist, they run in the reverse of their graph registration order; do not rely on a specific order between them for correctness.

### Custom { #custom }

To add a custom interceptor, create a `ServerInterceptor` implementation with the `@Component` annotation:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class GrpcExceptionHandlerServerInterceptor implements ServerInterceptor {

        @Override
        public <ReqT, RespT> ServerCall.Listener<ReqT> interceptCall(ServerCall<ReqT, RespT> serverCall, 
                                                                     Metadata metadata,
                                                                     ServerCallHandler<ReqT, RespT> serverCallHandler) {
            // do something
            
            return serverCallHandler.startCall(serverCall, metadata);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class GrpcExceptionHandlerServerInterceptor : ServerInterceptor {

        override fun <ReqT, RespT> interceptCall(
            serverCall: ServerCall<ReqT, RespT>,
            metadata: Metadata,
            serverCallHandler: ServerCallHandler<ReqT, RespT>
        ): ServerCall.Listener<ReqT> {
            // do something
            
            return serverCallHandler.startCall(serverCall, metadata)
        }
    }
    ```

### Scoping and authorization { #authorization }

Because an interceptor is global, scope it to a specific service or method by inspecting `call.getMethodDescriptor()`:
`getServiceName()` returns the service name (the generated constant `...Grpc.SERVICE_NAME`), and `getFullMethodName()` returns `service/method`.

Request headers arrive as [`Metadata`](https://grpc.github.io/grpc-java/javadoc/io/grpc/Metadata.html).
Read a header with a `Metadata.Key`, and reject a call by closing it with a `Status` and returning an empty listener so the handler is never invoked.
The example below applies API-key authorization to a single service only:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class ApiKeyServerInterceptor implements ServerInterceptor {

        private static final Metadata.Key<String> AUTHORIZATION =
            Metadata.Key.of("authorization", Metadata.ASCII_STRING_MARSHALLER); //(1)!

        @Override
        public <ReqT, RespT> ServerCall.Listener<ReqT> interceptCall(ServerCall<ReqT, RespT> call,
                                                                     Metadata headers,
                                                                     ServerCallHandler<ReqT, RespT> next) {
            if (!UserServiceGrpc.SERVICE_NAME.equals(call.getMethodDescriptor().getServiceName())) { //(2)!
                return next.startCall(call, headers);
            }

            var apiKey = headers.get(AUTHORIZATION); //(3)!
            if (apiKey == null || !apiKey.equals("secret")) {
                call.close(Status.UNAUTHENTICATED.withDescription("Invalid API key"), new Metadata()); //(4)!
                return new ServerCall.Listener<>() {}; //(5)!
            }

            return next.startCall(call, headers);
        }
    }
    ```

    1. `Metadata.Key` for reading the `authorization` header as an ASCII string
    2. Applies the interceptor only to `UserService`; other services pass through untouched
    3. Reads the header value from the request `Metadata`
    4. Rejects the call with an `UNAUTHENTICATED` status
    5. Returns an empty listener so the handler is never called

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ApiKeyServerInterceptor : ServerInterceptor {

        override fun <ReqT : Any?, RespT : Any?> interceptCall(
            call: ServerCall<ReqT, RespT>,
            headers: Metadata,
            next: ServerCallHandler<ReqT, RespT>
        ): ServerCall.Listener<ReqT> {
            if (UserServiceGrpc.SERVICE_NAME != call.methodDescriptor.serviceName) { //(2)!
                return next.startCall(call, headers)
            }

            val apiKey = headers.get(AUTHORIZATION) //(3)!
            if (apiKey != "secret") {
                call.close(Status.UNAUTHENTICATED.withDescription("Invalid API key"), Metadata()) //(4)!
                return object : ServerCall.Listener<ReqT>() {} //(5)!
            }

            return next.startCall(call, headers)
        }

        companion object {
            private val AUTHORIZATION: Metadata.Key<String> =
                Metadata.Key.of("authorization", Metadata.ASCII_STRING_MARSHALLER) //(1)!
        }
    }
    ```

    1. `Metadata.Key` for reading the `authorization` header as an ASCII string
    2. Applies the interceptor only to `UserService`; other services pass through untouched
    3. Reads the header value from the request `Metadata`
    4. Rejects the call with an `UNAUTHENTICATED` status
    5. Returns an empty listener so the handler is never called

## Lifecycle and readiness { #lifecycle }

The server is managed by the `GrpcNettyServer` component, which is created as a [`@Root`](container.md#root-component) component
and follows the [application lifecycle](container.md#component-lifecycle):

- On startup it builds and starts the `Netty` server on the configured `port`. If the port is already in use, startup fails with a clear error.
- On shutdown it performs a [graceful shutdown](container.md#graceful-shutdown): it stops accepting new calls and waits up to `shutdownWait` for in-flight calls to finish, then forcibly terminates any remaining calls.

`GrpcNettyServer` also implements a [readiness probe](probes.md): the server reports **not ready** while it is starting up or shutting down,
and **ready** only while it is running. In a `Kubernetes` deployment this lets the readiness probe reflect the real server state and drain traffic during graceful shutdown.

## Reflection { #reflection }

[`gRPC Server Reflection`](https://github.com/grpc/grpc/blob/master/doc/server-reflection.md) is supported and provides information about available `gRPC services` on the server.
Reflection helps clients and tools build `RPC` requests at runtime without precompiled service information.
For example, it is used by `gRPC CLI`, which can inspect server `proto` descriptions and send test `RPC` calls.
`gRPC Server Reflection` is supported only for `proto`-based services.

You can learn more about `gRPC Server Reflection` in the [grpc-java guide](https://github.com/grpc/grpc-java/blob/master/documentation/server-reflection-tutorial.md#enable-server-reflection).

### Dependency { #dependency-2 }

You must additionally add the [`gRPC Server Reflection`](https://mvnrepository.com/artifact/io.grpc/grpc-services) dependency.

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) in `build.gradle`:
    ```groovy
    implementation "io.grpc:grpc-services:1.74.0"
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) in `build.gradle.kts`:
    ```groovy
    implementation("io.grpc:grpc-services:1.74.0")
    ```

### Configuration { #configuration-2 }

You must also enable the `gRPC Server Reflection` service in the configuration.
Kora adds it to the server only if the application has the `io.grpc.protobuf.services.ProtoReflectionService` class, so configuration alone is not enough without the dependency.

===! ":material-code-json: `Hocon`"

    ```javascript
    grpcServer {
        reflectionEnabled = false //(1)!
    }
    ```

    1. Enables the `gRPC Server Reflection` service (default: `false`).

=== ":simple-yaml: `YAML`"

    ```yaml
    grpcServer:
      reflectionEnabled: false #(1)!
    ```

    1. Enables the `gRPC Server Reflection` service (default: `false`).

### Usage { #reflection-usage }

With reflection enabled, tools such as [`grpcurl`](https://github.com/fullstorydev/grpcurl) can discover services and send `RPC` calls without a precompiled client.
For a server listening on port `8090`:

```bash
grpcurl -plaintext localhost:8090 list #(1)!
grpcurl -plaintext localhost:8090 describe ru.tinkoff.kora.generated.grpc.UserService #(2)!
grpcurl -plaintext -d '{"name": "Bob", "code": "123"}' \
    localhost:8090 ru.tinkoff.kora.generated.grpc.UserService/createUser #(3)!
```

1. Lists the services exposed by the server
2. Describes a service and its methods
3. Sends a unary `RPC`; `-plaintext` is used because the example server has no `TLS`

## Telemetry { #telemetry }

gRPC Server uses a telemetry contract for logging, metrics, and tracing of calls.
Telemetry configuration (section `telemetry { logging / metrics / tracing }`) is described in the [Configuration](#configuration) section.
Extension points are located in `ru.tinkoff.kora.grpc.server.common.telemetry`.

Server observability is driven by the `TelemetryInterceptor` through the `GrpcServerTelemetry` facade and is configured under [`grpcServer.telemetry`](#configuration).

For each gRPC call, a `GrpcServerTelemetry.GrpcServerTelemetryContext` is created, which is closed upon call completion.
The call is described through telemetry handler parameters, including service, method, response status, and duration.

The default factory `DefaultGrpcServerTelemetryFactory` combines three factories:
- `GrpcServerLoggerFactory` builds `GrpcServerLogger` for logging call start/end;
- `GrpcServerMetricsFactory` builds `GrpcServerMetrics` for writing call metrics;
- `GrpcServerTracerFactory` builds `GrpcServerTracer` for distributed tracing.

Metrics and tracing are described in the [Metrics Reference](metrics.md#grpc-server) section.
