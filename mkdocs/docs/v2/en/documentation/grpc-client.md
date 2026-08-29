---
description: "Explains the Kora gRPC client: the grpc-client module, protobuf Gradle plugin setup, the grpcClient configuration section, injecting generated stubs, per-client interceptors, TLS credentials, channel tuning and telemetry. Use when working with GrpcClientModule, GrpcClientConfig, GrpcClientChannelFactory, ManagedChannelLifecycle, ChannelCredentials, protobuf plugin."
agent:
  use_when: "Use this file for Kora docs or implementation questions about the Kora gRPC client: injecting BlockingStub / FutureStub / async Stub / Kotlin coroutine stubs, the grpcClient.<Service> configuration section, url scheme and TLS, deadlines, keepAlive and load balancing, per-client ClientInterceptor tagging, authorization metadata, error handling and telemetry; key triggers include GrpcClientModule, GrpcClientConfig, GrpcClientChannelFactory, GrpcOkHttpClientChannelFactory, ManagedChannelLifecycle, Configurer, ChannelCredentials, protobuf plugin."
---

The `gRPC client` calls remote services using a `protobuf` contract and the `HTTP/2` transport.
In Kora, the client is built on top of generated `grpc-java` `stub` classes: the module creates a `ManagedChannel`, attaches interceptors, and registers ready-to-use `stub` instances in the application graph.

For each service, Kora makes the generated stubs (`BlockingStub`, `FutureStub`, the async `Stub`, and the Kotlin coroutine stub),
the raw `io.grpc.Channel`, and the resolved `GrpcClientConfig` injectable, distinguishing every client by the generated service-class `@Tag`
(for example `@Tag(SimpleServiceGrpc.class)`).

The gRPC client transport is `grpc-okhttp`: for every client Kora builds an `OkHttpChannelBuilder` through `GrpcOkHttpClientChannelFactory`,
so channel tuning is done through configuration or a builder configurer rather than through a shared transport module.

For a step-by-step walkthrough before the reference details, see [gRPC Client](../guides/grpc-client.md) and [Advanced gRPC Client](../guides/grpc-client-advanced.md).

## Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:grpc-client"
    implementation "io.grpc:grpc-protobuf:1.83.1"
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
    implementation("io.koraframework:grpc-client")
    implementation("io.grpc:grpc-protobuf:1.83.1")
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
        id "com.google.protobuf" version "0.10.0"
    }

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
        id("com.google.protobuf") version ("0.10.0")
    }

    protobuf {
        protoc { artifact = "com.google.protobuf:protoc:4.35.1" }
        plugins {
            id("grpc") { artifact = "io.grpc:protoc-gen-grpc-java:1.83.1" }
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

    Add the [gRPC Kotlin generator](https://github.com/grpc/grpc-kotlin) on top of it only if coroutine stubs are needed:
    ```groovy
    dependencies {
        implementation("io.grpc:grpc-kotlin-stub:1.5.0")
    }

    protobuf {
        plugins {
            id("grpckt") { artifact = "io.grpc:protoc-gen-grpc-kotlin:1.5.0:jdk8@jar" }
        }
        generateProtoTasks {
            ofSourceSet("main").forEach { it.plugins { id("grpc") { }; id("grpckt") { } } }
        }
    }

    kotlin {
        sourceSets.main {
            kotlin.srcDir("build/generated/source/proto/main/grpckt")
        }
    }
    ```

## Configuration { #configuration }

A `gRPC client` for the `SimpleService` service will have the `grpcClient.SimpleService` configuration path.

The path segment is the *simple* name of the `protobuf` service: Kora takes the generated `SERVICE_NAME` constant
(the fully qualified name, `proto` package included) and keeps only the part after the last dot.
A service declared as `package my.company.api; service SimpleService` is therefore configured under `grpcClient.SimpleService`.

Basic configuration parameters:

===! ":material-code-json: `Hocon`"

    ```javascript
    grpcClient {
        SimpleService {
            url = "http://localhost:8090" //(1)!
            timeout = "10s"  //(2)!
        }
    }
    ```

    1. Server `URL` where requests will be sent (`required`, no default).
    2. Maximum request execution time (default: not specified, optional). The value is applied as a `deadline` if the call does not already have its own `deadline`.

=== ":simple-yaml: `YAML`"

    ```yaml
    grpcClient:
      SimpleService:
        url: "http://localhost:8090" #(1)!
        timeout: "10s" #(2)!
    ```

    1. Server `URL` where requests will be sent (`required`, no default).
    2. Maximum request execution time (default: not specified, optional). The value is applied as a `deadline` if the call does not already have its own `deadline`.

??? note "Full Configuration"

    Example of the complete configuration described by the `GrpcClientConfig` class:

    ===! ":material-code-json: `Hocon`"

        ```javascript
        grpcClient {
            SimpleService {
                url = "http://localhost:8090" //(1)!
                timeout = "10s"  //(2)!
                keepAliveTime = "30s" //(3)!
                keepAliveTimeout = "10s" //(4)!
                loadBalancingPolicy = "round_robin" //(5)!
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
                        enabled = false //(8)!
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

        1. Server `URL` where requests will be sent (required, no default).
        2. Maximum request execution time (default: not specified, optional). The value is applied as a `deadline` if the call does not already have its own `deadline`.
        3. Interval between gRPC `PING` frames (default: not specified, optional).
        4. Timeout for acknowledging a `PING` frame (default: not specified, optional). If the acknowledgement is not received within this time, the connection is closed.
        5. Load balancing policy for `ManagedChannelBuilder` (default: not specified, optional).
        6. Standard gRPC service configuration passed to `ManagedChannelBuilder.defaultServiceConfig` (default: not specified, optional).
        7. Enables module logging (default: `false`).
        8. Enables module metrics (default: `false`).
        9. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for the [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metric (default: `TelemetryConfig.MetricsConfig.DEFAULT_SLO`). Plain numbers are read as milliseconds.
        10. Additional tags for metrics (default: `{}`).
        11. Enables module tracing (default: `true`).
        12. Additional attributes for tracing (default: `{}`).

    === ":simple-yaml: `YAML`"

        ```yaml
        grpcClient:
          SimpleService:
            url: "http://localhost:8090" #(1)!
            timeout: "10s" #(2)!
            keepAliveTime: "30s" #(3)!
            keepAliveTimeout: "10s" #(4)!
            loadBalancingPolicy: "round_robin" #(5)!
            defaultServiceConfig: #(6)!
              loadBalancingConfig:
                - round_robin: {}
            telemetry:
              logging:
                enabled: false #(7)!
              metrics:
                enabled: false #(8)!
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

        1. Server `URL` where requests will be sent (required, no default).
        2. Maximum request execution time (default: not specified, optional). The value is applied as a `deadline` if the call does not already have its own `deadline`.
        3. Interval between gRPC `PING` frames (default: not specified, optional).
        4. Timeout for acknowledging a `PING` frame (default: not specified, optional). If the acknowledgement is not received within this time, the connection is closed.
        5. Load balancing policy for `ManagedChannelBuilder` (default: not specified, optional).
        6. Standard gRPC service configuration passed to `ManagedChannelBuilder.defaultServiceConfig` (default: not specified, optional).
        7. Enables module logging (default: `false`).
        8. Enables module metrics (default: `false`).
        9. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for the [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metric (default: `TelemetryConfig.MetricsConfig.DEFAULT_SLO`). Plain numbers are read as milliseconds.
        10. Additional tags for metrics (default: `{}`).
        11. Enables module tracing (default: `true`).
        12. Additional attributes for tracing (default: `{}`).

### Transport and TLS { #transport-tls }

The `url` scheme selects the transport when the `ManagedChannel` is created (`ManagedChannelLifecycle`):

- `http` — plaintext transport (`usePlaintext()` on the builder), default port `80` when the port is omitted.
- `https` — `TLS` transport, default port `443` when the port is omitted.
- any other scheme — the port must be specified explicitly, otherwise the application fails to start with
  `IllegalArgumentException: Unsupported gRPC client URL scheme '<scheme>' in '<url>'; use http://host[:port] or https://host[:port]`.
  Plaintext is enabled only for the `http` scheme, so a different scheme with an explicit port still uses the `TLS` transport.

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

For custom `TLS` (`mTLS`, a private certificate authority) register an `io.grpc.ChannelCredentials` component tagged with the generated service class.
`ManagedChannelLifecycle` picks it up per client and builds the channel with those credentials instead of the transport defaults:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends HoconConfigModule, GrpcClientModule {

        @Tag(SimpleServiceGrpc.class)
        default ChannelCredentials simpleServiceCredentials() {
            try {
                return TlsChannelCredentials.newBuilder()
                    .trustManager(new File("/etc/certs/ca.pem")) //(1)!
                    .keyManager(new File("/etc/certs/client.pem"), new File("/etc/certs/client.key")) //(2)!
                    .build();
            } catch (IOException e) {
                throw new IllegalStateException("Failed to read gRPC client TLS certificates", e);
            }
        }
    }
    ```

    1. Trusted certificate authority in `PEM` format, used to validate the server certificate.
    2. Client certificate and private key in `PEM` format — required only for `mTLS`.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : HoconConfigModule, GrpcClientModule {

        @Tag(SimpleServiceGrpc::class)
        fun simpleServiceCredentials(): ChannelCredentials = TlsChannelCredentials.newBuilder()
            .trustManager(File("/etc/certs/ca.pem")) //(1)!
            .keyManager(File("/etc/certs/client.pem"), File("/etc/certs/client.key")) //(2)!
            .build()
    }
    ```

    1. Trusted certificate authority in `PEM` format, used to validate the server certificate.
    2. Client certificate and private key in `PEM` format — required only for `mTLS`.

Credentials are optional: without such a component the channel is created from the `url` alone.
Keep the `https` scheme (or an explicit port) in the `url` when credentials are supplied — `http` forces `usePlaintext()` and disables them.

To replace the transport itself, register your own `GrpcClientChannelFactory` component. It is a single global component for all gRPC clients,
and it overrides the default `GrpcOkHttpClientChannelFactory`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class CustomGrpcClientChannelFactory implements GrpcClientChannelFactory {

        @Override
        public ManagedChannelBuilder<?> forTarget(String target) {
            return OkHttpChannelBuilder.forTarget(target);
        }

        @Override
        public ManagedChannelBuilder<?> forTarget(String target, ChannelCredentials creds) {
            return OkHttpChannelBuilder.forTarget(target, creds);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class CustomGrpcClientChannelFactory : GrpcClientChannelFactory {

        override fun forTarget(target: String): ManagedChannelBuilder<*> {
            return OkHttpChannelBuilder.forTarget(target)
        }

        override fun forTarget(target: String, creds: ChannelCredentials): ManagedChannelBuilder<*> {
            return OkHttpChannelBuilder.forTarget(target, creds)
        }
    }
    ```

Only `forTarget` has to be implemented — the `forAddress(host, port)` overloads have default implementations that build a `host:port` authority and delegate to `forTarget`.
Override `forAddress` as well if the target string is not what the transport expects.

### Timeouts { #timeouts }

The `timeout` value is applied by the always-on `GrpcClientConfigInterceptor` as a call `deadline`, but **only when the call has no deadline of its own**.
A per-call deadline set through the stub is part of the `CallOptions` before any interceptor runs, so it always wins over the configured `timeout`:

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

### Channel config { #channel-config }

- `keepAliveTime` / `keepAliveTimeout` map to `ManagedChannelBuilder` `PING` settings. `keepAliveTime` is the interval between `HTTP/2` `PING` frames on an idle connection; `keepAliveTimeout` is how long to wait for the `PING` acknowledgement before closing the connection. Both are disabled unless set.
- `loadBalancingPolicy` maps to `ManagedChannelBuilder.defaultLoadBalancingPolicy`. The gRPC default is `pick_first` (a single connection to the first resolved address); `round_robin` distributes calls across all resolved addresses and is typically used with DNS targets that return multiple `A`/`AAAA` records.
- `defaultServiceConfig` is passed as-is to `ManagedChannelBuilder.defaultServiceConfig` and carries the native gRPC [service config](https://github.com/grpc/grpc/blob/master/doc/service_config.md) map (`loadBalancingConfig`, per-method `methodConfig` with retry/hedging policy, etc.). It is described by the `DefaultServiceConfig` wrapper over `Map<String, Object>`, and all numbers in it are read as `double` values, as the gRPC service config format requires.

### Channel builder configurer { #builder-configurer }

If file-based configuration is not enough, you can register a `Configurer<ManagedChannelBuilder<?>>` component.
It receives an already prepared `ManagedChannelBuilder` and lets you configure the channel in code before it is created.

The component can be registered at two levels:

- **tagged with the generated service class** — applied to that one client, after everything from `GrpcClientConfig` (interceptors, `keepAlive`, `loadBalancingPolicy`, `defaultServiceConfig`), so it can override any of them;
- **without a tag** — passed to the default `GrpcOkHttpClientChannelFactory` and applied to the builder of every gRPC client at creation time, before the configuration values.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(SimpleServiceGrpc.class)
    @Component
    public final class SimpleServiceChannelConfigurer implements Configurer<ManagedChannelBuilder<?>> { //(1)!

        @Override
        public ManagedChannelBuilder<?> configure(ManagedChannelBuilder<?> builder) {
            return builder.maxInboundMessageSize(8 * 1024 * 1024);
        }
    }

    @Component
    public final class CommonChannelConfigurer implements Configurer<ManagedChannelBuilder<?>> { //(2)!

        @Override
        public ManagedChannelBuilder<?> configure(ManagedChannelBuilder<?> builder) {
            return builder.userAgent("my-service");
        }
    }
    ```

    1. Applied to the `SimpleService` client only, last of all.
    2. Applied to every gRPC client of the application.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(SimpleServiceGrpc::class)
    @Component
    class SimpleServiceChannelConfigurer : Configurer<ManagedChannelBuilder<*>> { //(1)!

        override fun configure(builder: ManagedChannelBuilder<*>): ManagedChannelBuilder<*> {
            return builder.maxInboundMessageSize(8 * 1024 * 1024)
        }
    }

    @Component
    class CommonChannelConfigurer : Configurer<ManagedChannelBuilder<*>> { //(2)!

        override fun configure(builder: ManagedChannelBuilder<*>): ManagedChannelBuilder<*> {
            return builder.userAgent("my-service")
        }
    }
    ```

    1. Applied to the `SimpleService` client only, last of all.
    2. Applied to every gRPC client of the application.

The untagged configurer is a parameter of the default `GrpcClientChannelFactory`, so it is ignored if you replace that factory with your own component —
wire it yourself in that case.

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

The `BlockingStub`, `FutureStub`, and async `Stub` are wired by the annotation-processor (or KSP) extension `GrpcClientExtension`, which detects the `@GrpcGenerated`
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

        fun coroutineCaller(stub: SimpleServiceGrpcKt.SimpleServiceCoroutineStub) = CoroutineCaller(stub) //(1)!
    }
    ```

    1. Requires the [gRPC Kotlin generator](#plugin). The generated stub extends `io.grpc.kotlin.AbstractCoroutineStub` and is annotated with `@StubFor`;
       the KSP symbol processor emits a Kora `@Module` next to it that exposes the stub as a `@DefaultComponent` bound to the tagged `Channel`.
       Kora picks that module up automatically, so nothing has to be extended manually, and the component can be overridden by declaring your own.

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

Java stubs work exactly the same way in Kotlin, so the async `Stub` with `StreamObserver` remains available there when the coroutine generator is not used.

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

The following interceptors are registered for every client:

- `GrpcClientTelemetryInterceptor` — opens a telemetry observation for the call. It is always registered and becomes a pass-through when logging, metrics, and tracing are all disabled.
- `GrpcClientConfigInterceptor` — applies `timeout` as the call `deadline` when the call has none.

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

### Shared across clients { #shared-interceptors }

A component carries exactly one `@Tag`, so one interceptor instance cannot serve several clients.
To reuse one implementation, declare the class without `@Component` and publish it once per client from the application module, each time with its own tag:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class SharedInterceptor implements ClientInterceptor {
        @Override
        public <ReqT, RespT> ClientCall<ReqT, RespT> interceptCall(MethodDescriptor<ReqT, RespT> method, CallOptions callOptions, Channel next) {
            return next.newCall(method, callOptions);
        }
    }

    @KoraApp
    public interface Application extends HoconConfigModule, GrpcClientModule {

        @Tag(SimpleServiceGrpc.class)
        default ClientInterceptor simpleServiceSharedInterceptor() {
            return new SharedInterceptor();
        }

        @Tag(OtherServiceGrpc.class)
        default ClientInterceptor otherServiceSharedInterceptor() {
            return new SharedInterceptor();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class SharedInterceptor : ClientInterceptor {
        override fun <ReqT : Any, RespT : Any> interceptCall(
            method: MethodDescriptor<ReqT, RespT>,
            callOptions: CallOptions,
            next: Channel
        ): ClientCall<ReqT, RespT> {
            return next.newCall(method, callOptions)
        }
    }

    @KoraApp
    interface Application : HoconConfigModule, GrpcClientModule {

        @Tag(SimpleServiceGrpc::class)
        fun simpleServiceSharedInterceptor(): ClientInterceptor = SharedInterceptor()

        @Tag(OtherServiceGrpc::class)
        fun otherServiceSharedInterceptor(): ClientInterceptor = SharedInterceptor()
    }
    ```

**Execution order:**

`ManagedChannelLifecycle` collects all interceptors tagged for the service as `All<ClientInterceptor>` and registers them on the channel builder
in the order: your custom interceptors, then the telemetry interceptor, then the config/deadline interceptor.
gRPC runs registered interceptors in the reverse order of registration, so a call travels:

```
Call → Config (deadline) interceptor → Telemetry interceptor → Custom interceptors → gRPC Server
```

Two practical consequences: your interceptors already see the effective `deadline` on the `CallOptions` and can replace it with `withDeadlineAfter`,
and everything they do happens inside the telemetry span and the measured call duration.
The relative order of several custom interceptors follows the graph declaration order reversed — do not build logic that depends on it.

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
            this.apiKey = config.value();
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

    1. Any `@ConfigSource` interface exposing the API key, for example `@ConfigSource("auth.apiKey") public interface ApiKeyConfig { String value(); }`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(SimpleServiceGrpc::class)
    @Component
    class ApiKeyInterceptor(config: ApiKeyConfig) : ClientInterceptor { //(1)!

        private val apiKey: String = config.value()

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

    1. Any `@ConfigSource` interface exposing the API key, for example `@ConfigSource("auth.apiKey") interface ApiKeyConfig { fun value(): String }`

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
- Use [resilient](resilient.md) aspects (`@Retryable`, `@CircuitBreakable`, `@Timeout`) on the wrapping service method for transient failures.

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

Channel startup itself does not fail the application: `ManagedChannelLifecycle` logs a warning if the first `getState(true)` probe fails,
and the call retries the connection later. Configuration errors, on the other hand, do fail the graph — a missing `url` or an unsupported scheme aborts the start.

## Testing { #testing }

A gRPC client is tested like any other Kora component with [`@KoraAppTest`](junit5.md).
Implement `KoraAppTestConfigModifier` to supply the `url` (via the environment-variable substitution the application config uses),
inject the stub-based service with `@TestComponent`, build the request with the generated builder and assert on `StatusRuntimeException`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(Application.class)
    class GrpcClientTests implements KoraAppTestConfigModifier {

        @TestComponent
        private RootService service;

        @Override
        public KoraConfigModification config() {
            return KoraConfigModification.ofSystemProperty("GRPC_URL", "http://localhost:8090");
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
            KoraConfigModification.ofSystemProperty("GRPC_URL", "http://localhost:8090")

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

gRPC Client uses a telemetry contract for logging, metrics, and tracing of calls.
Telemetry configuration (section `telemetry { logging / metrics / tracing }`) is described in the [Configuration](#configuration) section.
Extension points are located in `io.koraframework.grpc.client.telemetry` and `io.koraframework.grpc.client.telemetry.impl`.

`GrpcClientTelemetryFactory` builds one `GrpcClientTelemetry` per client from the `GrpcClientTelemetryConfig`, the `ServiceDescriptor`, and the target `URI`.
For each gRPC call `GrpcClientTelemetry.observe(...)` creates a `GrpcClientObservation`, which receives `observeStart`, `observeSend`, `observeReceive`,
`observeClose`, and `observeError` events and is closed with `end()` when the call completes.

The default factory `DefaultGrpcClientTelemetryFactory` combines:

- an OpenTelemetry `Tracer` — a `CLIENT` span per call, named after the full gRPC method, with `rpc.system`, `rpc.service`, `rpc.method`, `server.address`, and `server.port` attributes;
- a Micrometer `MeterRegistry` — the `rpc.client.duration` timer with the configured `slo` buckets;
- `DefaultGrpcClientLoggerFactory` — start/end logs written to the `<serviceName>.request` and `<serviceName>.response` loggers, where `serviceName` is the fully qualified `protobuf` service name. Request/response headers are added at the `DEBUG` level;
- `DefaultGrpcClientMetricsFactory` — the metric implementation itself.

When logging, metrics, and tracing are all disabled for a client, the factory returns `NoopGrpcClientTelemetry` and the telemetry interceptor becomes a pass-through.
Metrics additionally require a `MeterRegistry` in the graph and tracing a `Tracer`; without them the corresponding part stays off regardless of the configuration.

Metrics and tracing are described in the [Metrics Reference](metrics.md#grpc-client) section.
