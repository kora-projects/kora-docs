---
description: "Explains Kora gRPC client generation, protobuf Gradle plugin setup, client configuration, generated services, interceptors, and mapping. Use when working with GrpcClientModule, @GrpcClient, @InterceptWith, GrpcClientConfig, GrpcClientInterceptor, protobuf plugin."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora gRPC client generation, protobuf Gradle plugin setup, client configuration, generated services, interceptors, and mapping; key triggers include GrpcClientModule, @GrpcClient, @InterceptWith, GrpcClientConfig, GrpcClientInterceptor, protobuf plugin."
---

The `gRPC client` calls remote services using a `protobuf` contract and the `HTTP/2` transport.
In Kora, the client is built on top of generated `grpc-java` `stub` classes: the module creates a `ManagedChannel`, attaches interceptors, and registers ready-to-use `stub` instances in the application graph.

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

When creating a channel, the `http` scheme enables plaintext mode through `usePlaintext()`.
If the port is not specified explicitly, `http` uses port `80`, and `https` uses port `443`.

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

## Interceptors { #interceptors }

[Interceptors](https://grpc.github.io/grpc-java/javadoc/io/grpc/ClientInterceptor.html) allow you to intercept requests before they are passed to services.

### Default { #default }

The following interceptors are used at client startup by default:

- `GrpcClientConfigInterceptor`.
- `GrpcClientTelemetryInterceptor`, if telemetry is available for the client.

### Custom { #custom }

In order to add your custom interceptor, you need to register the interceptor as a component with the service tag:

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
        fun <ReqT, RespT> interceptCall(
            method: MethodDescriptor<ReqT, RespT>,
            callOptions: CallOptions,
            next: Channel
        ): ClientCall<ReqT, RespT> {
            return next.newCall(method, callOptions)
        }
    }
    ```

Alternatively, you can modify the `stub` with [GraphInterceptor](container.md#component-inspection).
