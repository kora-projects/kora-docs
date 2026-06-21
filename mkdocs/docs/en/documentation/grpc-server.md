---
description: "Explains Kora gRPC server generation, protobuf Gradle plugin setup, server configuration, handlers, interceptors, reflection, and debugging. Use when working with GrpcServerModule, @GrpcService, @InterceptWith, GrpcServerConfig, GrpcServerInterceptor, Server Reflection."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora gRPC server generation, protobuf Gradle plugin setup, server configuration, handlers, interceptors, reflection, and debugging; key triggers include GrpcServerModule, @GrpcService, @InterceptWith, GrpcServerConfig, GrpcServerInterceptor, Server Reflection."
---

The module starts a `gRPC server` based on [`grpc-java`](https://grpc.io/docs/languages/java/basics/) and connects handlers from the application graph to it.
A handler is a `BindableService`, usually a class that extends a generated `...ImplBase`.

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

Created `gRPC services` must be added to the application graph with the `@Component` annotation.
Usually, a handler extends the `...ImplBase` class generated from the `proto` description by the `protobuf gradle plugin`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class ExampleService extends ExampleGrpc.ExampleImplBase {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ExampleService : ExampleGrpc.ExampleImplBase {}
    ```

## Interceptors { #interceptors }

[Interceptors](https://grpc.github.io/grpc-java/javadoc/io/grpc/ServerInterceptor.html) allow processing requests before they are passed to a `gRPC service`.
They are suitable for cross-cutting logic: logging, authorization, tracing, working with `Metadata`, and error mapping.

### Default { #default }

When the server starts, Kora adds standard interceptors:

- `TelemetryInterceptor`
- `ContextServerInterceptor`
- `CoroutineContextInjectInterceptor`

`TelemetryInterceptor` enables server telemetry: logging, metrics, and tracing depending on connected modules and `grpcServer.telemetry` settings.
`ContextServerInterceptor` propagates the Kora context into call processing, and `CoroutineContextInjectInterceptor` adds `CoroutineContext` support for `Kotlin`.

User-defined `ServerInterceptor` from the application graph are added to `NettyServerBuilder` before the standard interceptors.
For full `NettyServerBuilder` configuration, use [GrpcServerBuilderConfigurer](#builder-configurer).

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
