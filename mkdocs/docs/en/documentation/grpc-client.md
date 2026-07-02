---
description: "Explains Kora gRPC client generation, protobuf Gradle plugin setup, client configuration, generated services, interceptors, and mapping. Use when working with GrpcClientModule, @GrpcClient, @InterceptWith, GrpcClientConfig, GrpcClientInterceptor, protobuf plugin."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora gRPC client generation, protobuf Gradle plugin setup, client configuration, generated services, interceptors, and mapping; key triggers include GrpcClientModule, @GrpcClient, @InterceptWith, GrpcClientConfig, GrpcClientInterceptor, protobuf plugin."
---

The `gRPC client` calls remote services using a `protobuf` contract and the `HTTP/2` transport.
In Kora, the client is built on top of generated `grpc-java` `stub` classes: the module creates a `ManagedChannel`, attaches interceptors, and registers ready-to-use `stub` instances in the application graph.

For each service, Kora makes the generated stubs (`BlockingStub`, `FutureStub`, the async `Stub`, and the Kotlin coroutine stub),
the raw `io.grpc.Channel`, and the resolved `GrpcClientConfig` injectable, distinguishing every client by the generated service-class `@Tag`
(for example `@Tag(SimpleServiceGrpc.class)`).

The gRPC client transport uses Netty, so common `event loop` and transport settings can be configured in the [Netty](netty.md) section.

For a step-by-step walkthrough before the reference details, see [gRPC Client](../guides/grpc-client.md) and [Advanced gRPC Client](../guides/grpc-client-advanced.md).

## Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:grpc-client"
    implementation "io.grpc:grpc-protobuf:1.74.0"
    implementation "javax.annotation:javax.annotation-api:1.3.2"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends GrpcClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:grpc-client")
    implementation("io.grpc:grpc-protobuf:1.74.0")
    implementation("javax.annotation:javax.annotation-api:1.3.2")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : GrpcClientModule
    ```

### Plugin { #plugin }

The code for the `gRPC client` is created with the [protobuf Gradle plugin](https://github.com/google/protobuf-gradle-plugin).
The plugin generates Java message classes from the `protobuf` contract and gRPC `stub` classes that are then used by Kora.

===! ":fontawesome-brands-java: `Java`"

    Plugin `build.gradle`:
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

    Plugin `build.gradle.kts`:
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

A `gRPC client` for the `SimpleService` service will have the `grpcClient.SimpleService` configuration path.

Example of the complete configuration described by the `GrpcClientConfig` class:

===! ":material-code-json: `Hocon`"

    ```javascript
    grpcClient {
        SimpleService {
            url = "http://localhost:8090" //(1)!
            timeout = "10s"  //(2)!
            keepAliveTime = "0s" //(3)!
            keepAliveTimeout = "0s" //(4)!
            loadBalancingPolicy = "pick_first" //(5)!
            defaultServiceConfig { //(6)!
                loadBalancingConfig = [
                    {
                        round_robin = {}
                    }
                ]
            }
            telemetry {
                logging {
                    enabled = false //(7)!
                }
                metrics {
                    enabled = true //(8)!
                    slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(9)!
                    tags = { // (10)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
                tracing {
                    enabled = true //(11)!
                    attributes = { // (12)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
            }
        }
    }
    ```

    1. Server `URL` where requests will be sent (required, default: not specified).
    2. Maximum request execution time (default: not specified, optional). The value is applied as a `deadline` if the call does not already have its own `deadline`.
    3. Interval between gRPC `PING` frames (default: not specified, optional).
    4. Timeout for acknowledging a `PING` frame (default: not specified, optional). If the acknowledgement is not received within this time, the connection is closed.
    5. Load balancing policy for `ManagedChannelBuilder` (default: not specified, optional).
    6. Standard gRPC service configuration passed to `ManagedChannelBuilder.defaultServiceConfig` (default: not specified, optional).
    7. Enables module logging (default: `false`).
    8. Enables module metrics (default: `true`).
    9. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for the [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metric (default: `TelemetryConfig.MetricsConfig.DEFAULT_SLO`).
    10. Additional tags for metrics (default: `{}`).
    11. Enables module tracing (default: `true`).
    12. Additional attributes for tracing (default: `{}`).

=== ":simple-yaml: `YAML`"

    ```yaml
    grpcClient:
      SimpleService:
        url: "http://localhost:8090" #(1)!
        timeout: "10s" #(2)!
        keepAliveTime: "0s" #(3)!
        keepAliveTimeout: "0s" #(4)!
        loadBalancingPolicy: "pick_first" #(5)!
        defaultServiceConfig: #(6)!
          loadBalancingConfig:
            - round_robin: {}
        telemetry:
          logging:
            enabled: false #(7)!
          metrics:
            enabled: true #(8)!
            slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(9)!
            tags: #(10)!
              key1: value1
              key2: value2
          tracing:
            enabled: true #(11)!
            attributes: #(12)!
              key1: value1
              key2: value2
    ```

    1. Server `URL` where requests will be sent (required, default: not specified).
    2. Maximum request execution time (default: not specified, optional). The value is applied as a `deadline` if the call does not already have its own `deadline`.
    3. Interval between gRPC `PING` frames (default: not specified, optional).
    4. Timeout for acknowledging a `PING` frame (default: not specified, optional). If the acknowledgement is not received within this time, the connection is closed.
    5. Load balancing policy for `ManagedChannelBuilder` (default: not specified, optional).
    6. Standard gRPC service configuration passed to `ManagedChannelBuilder.defaultServiceConfig` (default: not specified, optional).
    7. Enables module logging (default: `false`).
    8. Enables module metrics (default: `true`).
    9. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for the [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metric (default: `TelemetryConfig.MetricsConfig.DEFAULT_SLO`).
    10. Additional tags for metrics (default: `{}`).
    11. Enables module tracing (default: `true`).
    12. Additional attributes for tracing (default: `{}`).

### Transport and TLS { #transport-tls }

The `url` scheme selects the transport when the `ManagedChannel` is created (`ManagedChannelLifecycle`):

- `http` — plaintext transport (`usePlaintext()` on the builder), default port `80` when the port is omitted.
- `https` — `TLS` transport, default port `443` when the port is omitted.
- any other scheme — the port must be specified explicitly, otherwise an `IllegalArgumentException` with the message `Unknown scheme '<scheme>'` is thrown at startup while resolving the default port. Plaintext is enabled only for the `http` scheme, so other schemes fall back to the default gRPC (`TLS`) transport unless a plaintext port is reachable.

===! ":material-code-json: `Hocon`"

    ```javascript
    grpcClient {
        SimpleService {
            url = "http://localhost:8090" // plaintext, default port 80
        }
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    grpcClient:
      SimpleService:
        url: "http://localhost:8090" # plaintext, default port 80
    ```

For custom `TLS` (`mTLS`, a custom trust store, or non-Netty transport) register your own `GrpcClientChannelFactory` component.
It builds the `ManagedChannelBuilder` and can pass an `io.grpc.ChannelCredentials`; the default implementation is `GrpcNettyClientChannelFactory`,
which binds the channel to Kora's shared Netty `EventLoopGroup`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class TlsGrpcClientChannelFactory implements GrpcClientChannelFactory {

        @Override
        public ManagedChannelBuilder<?> forAddress(SocketAddress serverAddress) {
            return NettyChannelBuilder.forAddress(serverAddress);
        }

        @Override
        public ManagedChannelBuilder<?> forAddress(SocketAddress serverAddress, ChannelCredentials creds) {
            return NettyChannelBuilder.forAddress(serverAddress, creds);
        }

        @Override
        public ManagedChannelBuilder<?> forTarget(String target) {
            return NettyChannelBuilder.forTarget(target);
        }

        @Override
        public ManagedChannelBuilder<?> forTarget(String target, ChannelCredentials creds) {
            return NettyChannelBuilder.forTarget(target, creds);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class TlsGrpcClientChannelFactory : GrpcClientChannelFactory {

        override fun forAddress(serverAddress: SocketAddress): ManagedChannelBuilder<*> {
            return NettyChannelBuilder.forAddress(serverAddress)
        }

        override fun forAddress(serverAddress: SocketAddress, creds: ChannelCredentials): ManagedChannelBuilder<*> {
            return NettyChannelBuilder.forAddress(serverAddress, creds)
        }

        override fun forTarget(target: String): ManagedChannelBuilder<*> {
            return NettyChannelBuilder.forTarget(target)
        }

        override fun forTarget(target: String, creds: ChannelCredentials): ManagedChannelBuilder<*> {
            return NettyChannelBuilder.forTarget(target, creds)
        }
    }
    ```

A production override should also bind the builder to Kora's shared Netty `EventLoopGroup` and `NettyChannelFactory`
the way `GrpcNettyClientChannelFactory` does, rather than letting Netty create its own event loop.

### Timeouts and deadlines { #timeouts }

The `timeout` value is applied by the always-on `GrpcClientConfigInterceptor` as a call `deadline`, but **only when the call has no deadline of its own**.
A per-call deadline set through the stub always wins over the configured `timeout`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // uses the configured grpcClient.SimpleService.timeout as the deadline
    var response = stub.createUser(request);

    // overrides the configured timeout for this single call
    var responseWithDeadline = stub.withDeadlineAfter(2, TimeUnit.SECONDS).createUser(request);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // uses the configured grpcClient.SimpleService.timeout as the deadline
    val response = stub.createUser(request)

    // overrides the configured timeout for this single call
    val responseWithDeadline = stub.withDeadlineAfter(2, TimeUnit.SECONDS).createUser(request)
    ```

When a deadline expires, the call fails with a `StatusRuntimeException` carrying `Status.DEADLINE_EXCEEDED`.

### Keep-alive, load balancing and service config { #keepalive-lb }

- `keepAliveTime` / `keepAliveTimeout` map to `ManagedChannelBuilder` `PING` settings. `keepAliveTime` is the interval between `HTTP/2` `PING` frames on an idle connection; `keepAliveTimeout` is how long to wait for the `PING` acknowledgement before closing the connection. Both are disabled unless set.
- `loadBalancingPolicy` maps to `ManagedChannelBuilder.defaultLoadBalancingPolicy`. The gRPC default is `pick_first` (a single connection to the first resolved address); `round_robin` distributes calls across all resolved addresses and is typically used with DNS targets that return multiple `A`/`AAAA` records.
- `defaultServiceConfig` is passed as-is to `ManagedChannelBuilder.defaultServiceConfig` and carries the native gRPC [service config](https://github.com/grpc/grpc/blob/master/doc/service_config.md) map (`loadBalancingConfig`, per-method `methodConfig` with retry/hedging policy, etc.). It is described by the `DefaultServiceConfig` wrapper over `Map<String, Object>`.

### Channel builder configurer { #builder-configurer }

If file-based configuration is not enough, you can register a `GrpcClientBuilderConfigurer` component.
It receives an already prepared `ManagedChannelBuilder` and lets you configure the channel in code before it is created.
Settings from `GrpcClientConfig` are applied first, then `GrpcClientBuilderConfigurer` is called.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class CustomGrpcClientBuilderConfigurer implements GrpcClientBuilderConfigurer {
        @Override
        public ManagedChannelBuilder<?> configure(ManagedChannelBuilder<?> builder) {
            return builder.maxInboundMessageSize(8 * 1024 * 1024);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class CustomGrpcClientBuilderConfigurer : GrpcClientBuilderConfigurer {
        override fun configure(builder: ManagedChannelBuilder<*>): ManagedChannelBuilder<*> {
            return builder.maxInboundMessageSize(8 * 1024 * 1024)
        }
    }
    ```

You can also configure [Netty transport](netty.md).

Module metrics are described in the [Metrics Reference](metrics.md#grpc-client) section.

## Service { #service }

Created gRPC `stub` instances can be injected as dependencies:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends HoconConfigModule, GrpcClientModule {

        default SomeService someService(SimpleServiceGrpc.SimpleServiceBlockingStub grpcService) {
            return new SomeService(grpcService);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : HoconConfigModule, GrpcClientModule {
        fun someService(grpcService: SimpleServiceGrpc.SimpleServiceBlockingStub): SomeService {
            return SomeService(grpcService)
        }
    }
    ```

A stub can also be injected straight into a `@Component` constructor:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final SimpleServiceGrpc.SimpleServiceBlockingStub grpcService;

        public SomeService(SimpleServiceGrpc.SimpleServiceBlockingStub grpcService) {
            this.grpcService = grpcService;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(private val grpcService: SimpleServiceGrpc.SimpleServiceBlockingStub)
    ```

### Stub types { #stub-types }

The `protobuf` plugin generates several stub classes for one service (`SimpleService`). Each is injectable by simply declaring the corresponding type;
no `@Tag` is required on the stub itself (Kora resolves the tagged `Channel` behind the scenes):

| Stub type                              | Call model                                                              | When to use                                          |
|----------------------------------------|------------------------------------------------------------------------|------------------------------------------------------|
| `SimpleServiceBlockingStub`            | Synchronous; returns the response directly (or an `Iterator` for server streaming) | Blocking code, simplest call style                   |
| `SimpleServiceFutureStub`              | Asynchronous; returns a `ListenableFuture<T>` (unary only)             | Non-blocking code using `ListenableFuture`           |
| `SimpleServiceStub` (async)            | Asynchronous; delivers results through `StreamObserver<T>` callbacks    | Any streaming, callback-style asynchronous calls     |
| Kotlin coroutine stub                  | `suspend` functions and `Flow<T>`                                      | Idiomatic Kotlin coroutines                          |

The `BlockingStub`, `FutureStub`, and async `Stub` are wired by the annotation-processor extension (`GrpcClientExtension`), which detects the `@GrpcGenerated`
stub types and calls the generated `newBlockingStub` / `newFutureStub` / `newStub` factory against the tagged `Channel`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends HoconConfigModule, GrpcClientModule {

        default BlockingCaller blockingCaller(SimpleServiceGrpc.SimpleServiceBlockingStub stub) {
            return new BlockingCaller(stub);
        }

        default FutureCaller futureCaller(SimpleServiceGrpc.SimpleServiceFutureStub stub) {
            return new FutureCaller(stub);
        }

        default AsyncCaller asyncCaller(SimpleServiceGrpc.SimpleServiceStub stub) {
            return new AsyncCaller(stub);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : HoconConfigModule, GrpcClientModule {

        fun blockingCaller(stub: SimpleServiceGrpc.SimpleServiceBlockingStub) = BlockingCaller(stub)

        fun futureCaller(stub: SimpleServiceGrpc.SimpleServiceFutureStub) = FutureCaller(stub)

        fun asyncCaller(stub: SimpleServiceGrpc.SimpleServiceStub) = AsyncCaller(stub)
    }
    ```

For Kotlin coroutine calls, generate the coroutine stub with the [gRPC Kotlin generator](https://github.com/grpc/grpc-kotlin)
(`io.grpc:protoc-gen-grpc-kotlin`). The generated stub extends `io.grpc.kotlin.AbstractCoroutineStub` and is annotated with `@StubFor`;
the KSP symbol processor then generates a Kora module that exposes it as a `@DefaultComponent` bound to the tagged `Channel`, so it is injected the same way:

===! ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : HoconConfigModule, GrpcClientModule {

        fun coroutineCaller(stub: SimpleServiceGrpcKt.SimpleServiceCoroutineStub) = CoroutineCaller(stub)
    }
    ```

### Call styles { #call-styles }

The `rpc` shape in the `.proto` contract (single vs `stream` request/response) determines the generated method signature.
The examples below extend the base contract with all four call styles:

```protobuf
service SimpleService {
  rpc unary(RequestEvent) returns (ResponseEvent) {}                     // unary
  rpc serverStream(RequestEvent) returns (stream ResponseEvent) {}       // server streaming
  rpc clientStream(stream RequestEvent) returns (ResponseEvent) {}       // client streaming
  rpc biDiStream(stream RequestEvent) returns (stream ResponseEvent) {}  // bidirectional streaming
}
```

Requests are built with the generated message builders (`RequestEvent.newBuilder()`).
For Java, unary and server-streaming calls are available on the `BlockingStub`, while client-streaming and bidirectional calls require the async `Stub`
(they have no blocking variant). The Kotlin coroutine stub expresses every style with `suspend` functions and `Flow<T>`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var request = RequestEvent.newBuilder().setName("bob").setCode("b1").build();

    // unary — BlockingStub
    ResponseEvent unary = blockingStub.unary(request);

    // unary — FutureStub
    ListenableFuture<ResponseEvent> future = futureStub.unary(request);

    // server streaming — BlockingStub returns an iterator
    Iterator<ResponseEvent> responses = blockingStub.serverStream(request);

    // server streaming — async Stub delivers results to a StreamObserver
    asyncStub.serverStream(request, new StreamObserver<>() {
        @Override public void onNext(ResponseEvent value) { /* ... */ }
        @Override public void onError(Throwable t) { /* ... */ }
        @Override public void onCompleted() { /* ... */ }
    });

    // client streaming — async Stub, write requests, read one response
    StreamObserver<ResponseEvent> responseObserver = new StreamObserver<>() {
        @Override public void onNext(ResponseEvent value) { /* single response */ }
        @Override public void onError(Throwable t) { /* ... */ }
        @Override public void onCompleted() { /* ... */ }
    };
    StreamObserver<RequestEvent> requestObserver = asyncStub.clientStream(responseObserver);
    requestObserver.onNext(request);
    requestObserver.onCompleted();

    // bidirectional streaming — async Stub, both sides stream
    StreamObserver<RequestEvent> bidi = asyncStub.biDiStream(responseObserver);
    bidi.onNext(request);
    bidi.onCompleted();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val request = RequestEvent.newBuilder().setName("bob").setCode("b1").build()

    // unary — suspend function
    val response: ResponseEvent = coroutineStub.unary(request)

    // server streaming — returns a Flow
    val serverFlow: Flow<ResponseEvent> = coroutineStub.serverStream(request)
    serverFlow.collect { event -> /* ... */ }

    // client streaming — accepts a Flow, returns a single response
    val clientResponse: ResponseEvent = coroutineStub.clientStream(flowOf(request))

    // bidirectional streaming — Flow in, Flow out
    val biDiFlow: Flow<ResponseEvent> = coroutineStub.biDiStream(flowOf(request))
    biDiFlow.collect { event -> /* ... */ }
    ```

### Injecting Channel and config { #inject-channel-config }

For advanced or manual stub construction you can inject the raw `io.grpc.Channel` and the resolved `GrpcClientConfig`
by tagging them with the generated service class. Both are provided by `GrpcClientExtension`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends HoconConfigModule, GrpcClientModule {

        default SomeService someService(@Tag(SimpleServiceGrpc.class) Channel channel,
                                        @Tag(SimpleServiceGrpc.class) GrpcClientConfig config) {
            return new SomeService(SimpleServiceGrpc.newBlockingStub(channel), config.url());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : HoconConfigModule, GrpcClientModule {

        fun someService(
            @Tag(SimpleServiceGrpc::class) channel: Channel,
            @Tag(SimpleServiceGrpc::class) config: GrpcClientConfig
        ): SomeService = SomeService(SimpleServiceGrpc.newBlockingStub(channel), config.url())
    }
    ```

## Interceptors { #interceptors }

[Interceptors](https://grpc.github.io/grpc-java/javadoc/io/grpc/ClientInterceptor.html) allow you to intercept requests before they are passed to services.

### Default { #default }

The following interceptors are used at client startup by default:

- `GrpcClientConfigInterceptor` — applies `timeout` as the call `deadline` when the call has none.
- `GrpcClientTelemetryInterceptor`, if telemetry is available for the client.

### Custom { #custom }

Unlike the [HTTP client](http-client.md#interceptors), gRPC interceptors have no method/class/global tiers.
Every interceptor is scoped **per client** by tagging the component with the generated service class (`@Tag(SimpleServiceGrpc.class)`).
Register the interceptor as a component with that tag:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(SimpleServiceGrpc.class)
    @Component
    public final class MyClientInterceptor implements ClientInterceptor {
        @Override
        public <ReqT, RespT> ClientCall<ReqT, RespT> interceptCall(MethodDescriptor<ReqT, RespT> method, CallOptions callOptions, Channel next) {
            LoggerFactory.getLogger(Application.class).info("INTERCEPTED");
            return next.newCall(method, callOptions);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(SimpleServiceGrpc::class)
    @Component
    class MyClientInterceptor : ClientInterceptor {
        override fun <ReqT : Any, RespT : Any> interceptCall(
            method: MethodDescriptor<ReqT, RespT>,
            callOptions: CallOptions,
            next: Channel
        ): ClientCall<ReqT, RespT> {
            return next.newCall(method, callOptions)
        }
    }
    ```

To apply one interceptor bean to several clients (a "shared" interceptor), give it multiple `@Tag` values — one generated service class per client:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag({SimpleServiceGrpc.class, OtherServiceGrpc.class})
    @Component
    public final class SharedInterceptor implements ClientInterceptor {
        @Override
        public <ReqT, RespT> ClientCall<ReqT, RespT> interceptCall(MethodDescriptor<ReqT, RespT> method, CallOptions callOptions, Channel next) {
            return next.newCall(method, callOptions);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(SimpleServiceGrpc::class, OtherServiceGrpc::class)
    @Component
    class SharedInterceptor : ClientInterceptor {
        override fun <ReqT : Any, RespT : Any> interceptCall(
            method: MethodDescriptor<ReqT, RespT>,
            callOptions: CallOptions,
            next: Channel
        ): ClientCall<ReqT, RespT> {
            return next.newCall(method, callOptions)
        }
    }
    ```

**Execution order:**

`ManagedChannelLifecycle` collects all interceptors tagged for the service as `All<ClientInterceptor>` and applies them in a fixed order:
your custom interceptors first, then the telemetry interceptor (if telemetry is enabled), then the config/deadline interceptor last.

```
Request → Custom interceptors → Telemetry interceptor → Config (deadline) interceptor → gRPC Server
```

Because the deadline interceptor runs last, a deadline that a custom interceptor sets on the `CallOptions` is preserved, and the configured `timeout`
is applied only when no earlier interceptor (or per-call `withDeadlineAfter`) provided one.

Alternatively, you can modify the `stub` with [GraphInterceptor](container.md#component-inspection).

## Authorization { #authorization }

gRPC has no dedicated authorization module: authorization is done with a `ClientInterceptor` tagged with the service class that attaches an
`Authorization` (or API-key) header to the outgoing call `Metadata`. The interceptor wraps the call in a `ForwardingClientCall.SimpleForwardingClientCall`
and puts the header in `start(...)`, before the request is sent.

### Bearer { #bearer }

A [Bearer](https://swagger.io/docs/specification/authentication/bearer-authentication/) interceptor reads a token from your own provider and
puts it on the `Authorization` header of every call. `TokenProvider` below is your own component:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(SimpleServiceGrpc.class)
    @Component
    public final class BearerAuthInterceptor implements ClientInterceptor {

        private static final Metadata.Key<String> AUTHORIZATION =
            Metadata.Key.of("Authorization", Metadata.ASCII_STRING_MARSHALLER);

        private final TokenProvider tokenProvider;

        public BearerAuthInterceptor(TokenProvider tokenProvider) {
            this.tokenProvider = tokenProvider;
        }

        @Override
        public <ReqT, RespT> ClientCall<ReqT, RespT> interceptCall(MethodDescriptor<ReqT, RespT> method, CallOptions callOptions, Channel next) {
            return new ForwardingClientCall.SimpleForwardingClientCall<>(next.newCall(method, callOptions)) {
                @Override
                public void start(Listener<RespT> responseListener, Metadata headers) {
                    headers.put(AUTHORIZATION, "Bearer " + tokenProvider.getToken());
                    super.start(responseListener, headers);
                }
            };
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(SimpleServiceGrpc::class)
    @Component
    class BearerAuthInterceptor(private val tokenProvider: TokenProvider) : ClientInterceptor {

        override fun <ReqT : Any, RespT : Any> interceptCall(
            method: MethodDescriptor<ReqT, RespT>,
            callOptions: CallOptions,
            next: Channel
        ): ClientCall<ReqT, RespT> {
            return object : ForwardingClientCall.SimpleForwardingClientCall<ReqT, RespT>(next.newCall(method, callOptions)) {
                override fun start(responseListener: Listener<RespT>, headers: Metadata) {
                    headers.put(AUTHORIZATION, "Bearer " + tokenProvider.getToken())
                    super.start(responseListener, headers)
                }
            }
        }

        companion object {
            private val AUTHORIZATION: Metadata.Key<String> =
                Metadata.Key.of("Authorization", Metadata.ASCII_STRING_MARSHALLER)
        }
    }
    ```

### ApiKey { #apikey }

An [API-key](https://swagger.io/docs/specification/authentication/api-keys/) interceptor puts a static key on a custom metadata header (for example `X-API-KEY`).
The key is read from a [`@ConfigSource`](config.md) interface injected into the interceptor:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(SimpleServiceGrpc.class)
    @Component
    public final class ApiKeyInterceptor implements ClientInterceptor {

        private static final Metadata.Key<String> API_KEY =
            Metadata.Key.of("X-API-KEY", Metadata.ASCII_STRING_MARSHALLER);

        private final String apiKey;

        public ApiKeyInterceptor(ApiKeyConfig config) { //(1)!
            this.apiKey = config.apiKey();
        }

        @Override
        public <ReqT, RespT> ClientCall<ReqT, RespT> interceptCall(MethodDescriptor<ReqT, RespT> method, CallOptions callOptions, Channel next) {
            return new ForwardingClientCall.SimpleForwardingClientCall<>(next.newCall(method, callOptions)) {
                @Override
                public void start(Listener<RespT> responseListener, Metadata headers) {
                    headers.put(API_KEY, apiKey);
                    super.start(responseListener, headers);
                }
            };
        }
    }
    ```

    1. Any `@ConfigSource` interface exposing the API key, for example `String apiKey();`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(SimpleServiceGrpc::class)
    @Component
    class ApiKeyInterceptor(config: ApiKeyConfig) : ClientInterceptor { //(1)!

        private val apiKey: String = config.apiKey()

        override fun <ReqT : Any, RespT : Any> interceptCall(
            method: MethodDescriptor<ReqT, RespT>,
            callOptions: CallOptions,
            next: Channel
        ): ClientCall<ReqT, RespT> {
            return object : ForwardingClientCall.SimpleForwardingClientCall<ReqT, RespT>(next.newCall(method, callOptions)) {
                override fun start(responseListener: Listener<RespT>, headers: Metadata) {
                    headers.put(API_KEY, apiKey)
                    super.start(responseListener, headers)
                }
            }
        }

        companion object {
            private val API_KEY: Metadata.Key<String> =
                Metadata.Key.of("X-API-KEY", Metadata.ASCII_STRING_MARSHALLER)
        }
    }
    ```

    1. Any `@ConfigSource` interface exposing the API key, for example `fun apiKey(): String`

## Error handling { #error-handling }

A failed gRPC call throws an `io.grpc.StatusRuntimeException`. Its `getStatus()` carries a `Status.Code`
([status codes](https://grpc.io/docs/guides/status-codes/)) such as `UNAVAILABLE` (server unreachable), `DEADLINE_EXCEEDED` (the `timeout`/deadline expired),
`UNAUTHENTICATED` (rejected credentials), or `INVALID_ARGUMENT`. Response metadata is available through `getTrailers()`.

**Causes:**

- `UNAVAILABLE` — wrong `url`, plaintext/TLS mismatch, or the server is down.
- `DEADLINE_EXCEEDED` — the configured `timeout` or a per-call `withDeadlineAfter` was exceeded.
- `UNAUTHENTICATED` / `PERMISSION_DENIED` — missing or invalid authorization metadata.

**Recommendations:**

- Branch on `e.getStatus().getCode()` instead of the exception type.
- Use [resilient](resilient.md) aspects (`@Retry`, `@CircuitBreaker`, `@Timeout`) on the wrapping service method for transient failures.

===! ":fontawesome-brands-java: `Java`"

    ```java
    try {
        var response = stub.createUser(request);
    } catch (StatusRuntimeException e) {
        var code = e.getStatus().getCode();
        if (code == Status.Code.DEADLINE_EXCEEDED) {
            // timeout / deadline exceeded
        } else if (code == Status.Code.UNAVAILABLE) {
            // server unreachable
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    try {
        val response = stub.createUser(request)
    } catch (e: StatusRuntimeException) {
        when (e.status.code) {
            Status.Code.DEADLINE_EXCEEDED -> { /* timeout / deadline exceeded */ }
            Status.Code.UNAVAILABLE -> { /* server unreachable */ }
            else -> throw e
        }
    }
    ```

## Testing { #testing }

A gRPC client is tested like any other Kora component with [`@KoraAppTest`](junit5.md).
Implement `KoraAppTestConfigModifier` to supply the `url` (for example through the `GRPC_URL` environment substitution used in the example),
inject the stub-backed service with `@TestComponent`, build a request with the generated builder, and assert on `StatusRuntimeException`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(Application.class)
    class GrpcClientTests implements KoraAppTestConfigModifier {

        @TestComponent
        private RootService service;

        @Override
        public KoraConfigModification config() {
            return KoraConfigModification.ofSystemProperty("GRPC_URL", "grpc://localhost:8090");
        }

        @Test
        void createUser() {
            var event = Message.RequestEvent.newBuilder()
                .setName("bob")
                .setCode("b1")
                .build();

            var stub = service.service();
            assertThrows(StatusRuntimeException.class, () -> stub.createUser(event));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(Application::class)
    class GrpcClientTests : KoraAppTestConfigModifier {

        @TestComponent
        lateinit var service: RootService

        override fun config(): KoraConfigModification =
            KoraConfigModification.ofSystemProperty("GRPC_URL", "grpc://localhost:8090")

        @Test
        fun createUser() {
            val event = Message.RequestEvent.newBuilder()
                .setName("bob")
                .setCode("b1")
                .build()

            val stub = service.service()
            assertThrows(StatusRuntimeException::class.java) { stub.createUser(event) }
        }
    }
    ```

## Telemetry { #telemetry }

Default logging, metrics, and tracing are configured through the `telemetry` block of the [configuration](#configuration) and
described in the [Metrics Reference](metrics.md#grpc-client) section.

To customize the collected signals, override the telemetry SPI factories as components: `GrpcClientTelemetryFactory`
(the whole telemetry), `GrpcClientLoggerFactory`, `GrpcClientMetricsFactory`, or `GrpcClientTracerFactory`.
The default implementations are wired by `GrpcClientModule`; providing your own component replaces the corresponding default.
