Module for gRPC server handlers support based on [grpc.io](https://grpc.io/docs/languages/java/basics/) functionality.

## Dependency

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:grpc-server"
    implementation "io.grpc:grpc-protobuf:1.62.2"
    implementation "javax.annotation:javax.annotation-api:1.3.2"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends GrpcServerModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:grpc-server")
    implementation "io.grpc:grpc-protobuf:1.62.2"
    implementation("javax.annotation:javax.annotation-api:1.3.2")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : GrpcServerModule
    ```

### Plugin

The code for the gRPC server is created with [protobuf gradle plugin](https://github.com/google/protobuf-gradle-plugin).

===! ":fontawesome-brands-java: `Java`"

    Plugin `build.gradle`:
    ```groovy
    plugins {
        id "com.google.protobuf" version "0.9.4"
    }

    protobuf {
        protoc { artifact = "com.google.protobuf:protoc:3.25.3" }
        plugins {
            grpc { artifact = "io.grpc:protoc-gen-grpc-java:1.62.2" }
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
            id("grpc") { artifact = "io.grpc:protoc-gen-grpc-java:1.62.2" }
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

## Configuration

Example of a complete configuration described in the `GrpcServerConfig` class (example values or default values are indicated):

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
            }
            tracing {
                enabled = true //(12)!
            }
        }
    }
    ```

    1. gRPC server port
    2. Maximum size of the incoming message (specified as a number in bytes / or as `4MiB` / `4MB` / `1000Kb` etc.)
    3. Enables [gRPC Server Reflection](#reflection) service
    4. Time to wait for processing before shutting down the server in case of [graceful shutdown](container.md#graceful-shutdown)
    5. Sets a custom max connection age, connection lasting longer than which will be gracefully terminated. An unreasonably small value might be increased. A random jitter of +/-10% will be added to it.
    6. Sets a custom grace time for the graceful connection termination. Once the max connection age is reached, RPCs have the grace time to complete. RPCs that do not complete in time will be cancelled, allowing the connection to terminate.
    7. Sets the interval in milliseconds between PING frames
    8. Sets the timeout in milliseconds for a PING frame to be acknowledged. If sender does not receive an acknowledgment within this time, it will close the connection
    9. Enables module logging (default `false`)
    10. Enables module metrics (default `true`)
    11. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    12. Enables module tracing (default `true`)

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
        telemetry:
          enabled: true #(12)!
    ```

    1. gRPC server port
    2. Maximum size of the incoming message (specified as a number in bytes / or as `4MiB` / `4MB` / `1000Kb` etc.)
    3. Enables [gRPC Server Reflection](#reflection) service
    4. Time to wait for processing before shutting down the server in case of [graceful shutdown](container.md#graceful-shutdown)
    5. Sets a custom max connection age, connection lasting longer than which will be gracefully terminated. An unreasonably small value might be increased. A random jitter of +/-10% will be added to it.
    6. Sets a custom grace time for the graceful connection termination. Once the max connection age is reached, RPCs have the grace time to complete. RPCs that do not complete in time will be cancelled, allowing the connection to terminate.
    7. Sets the interval in milliseconds between PING frames
    8. Sets the timeout in milliseconds for a PING frame to be acknowledged. If sender does not receive an acknowledgment within this time, it will close the connection
    9. Enables module logging (default `false`)
    10. Enables module metrics (default `true`)
    11. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    12. Enables module tracing (default `true`)

You can also configure [Netty transport](netty.md).

Module metrics are described in the [Metrics Reference](metrics.md#grpc-server) section.

## Handlers

Created gRPC service handlers are required to be tagged with the `@Component` annotation:

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

## Interceptors

[Interceptors](https://grpc.github.io/grpc-java/javadoc/io/grpc/ServerInterceptor.html) allow you to intercept requests before they are passed to handlers.

### Default

The following interceptors are used at server startup by default:

- `ContextServerInterceptor`.
- `CoroutineContextInjectInterceptor`.
- `MetricCollectorServerInterceptor`
- `LoggingServerInterceptor`.

To override the default interceptor list, you can override the `serverBuilder` method from the `GrpcModule` class

### Custom

Adding your custom interceptor requires creating an inheritor of `ServerInterceptor` with the `@Component` annotation:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class GrpcExceptionHandlerServerInterceptor implements ServerInterceptor {

        @Override
        public <ReqT, RespT> ServerCall.Listener<ReqT> interceptCall(ServerCall<ReqT, RespT> serverCall, 
                                                                     Metadata metadata,
                                                                     ServerCallHandler<ReqT, RespT> serverCallHandler) {
            // do something
            
            return serverCallHandler.startCall(serverCall, metadata):
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

## Reflection

Supported by [gRPC Server Reflection](https://github.com/grpc/grpc/blob/master/doc/server-reflection.md)
which provides information about publicly available gRPC services on the server
and helps clients at runtime build RPC requests and responses without pre-compiled service information.
It is used by the gRPC command line tool (gRPC CLI), which can be used to examine server proto-files and send/receive test RPCs.
Reflection is only supported for proto-based services.

You can learn more about working with gRPC Server Reflection [here](https://github.com/grpc/grpc-java/blob/master/documentation/server-reflection-tutorial.md#enable-server-reflection).

### Dependency

An optional gRPC Server Reflection dependency is required.

===! ":fontawesome-brands-java: `Java`"

    Зависимость `build.gradle`:
    ```groovy
    implementation "io.grpc:grpc-services:1.62.2"
    ```

=== ":simple-kotlin: `Kotlin`"

    Зависимость `build.gradle.kts`:
    ```groovy
    implementation("io.grpc:grpc-services:1.62.2")
    ```

### Configuration

You must also enable the gRPC Server Reflection service in the configuration:

===! ":material-code-json: `Hocon`"

    ```javascript
    grpcServer {
        reflectionEnabled = false //(1)!
    }
    ```

    1.  Enables gRPC Server Reflection service

=== ":simple-yaml: `YAML`"

    ```yaml
    grpcServer:
      reflectionEnabled: false #(1)!
    ```

    1.  Enables gRPC Server Reflection service
