Module for gRPC server handlers support based on [grpc.io](https://grpc.io/docs/languages/java/basics/) functionality.

## Dependency

=== ":fontawesome-brands-java: `Java`"

    Dependency `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:grpc-server"
    implementation "io.grpc:grpc-protobuf:1.58.0"
    implementation "javax.annotation:javax.annotation-api:1.3.2"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends GrpcServerModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Dependency `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:grpc-server")
    implementation "io.grpc:grpc-protobuf:1.58.0"
    implementation("javax.annotation:javax.annotation-api:1.3.2")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : GrpcServerModule
    ```

## Configuration

Parameters described in the `GrpcServerConfig` class:

===! ":material-code-json: `Hocon`"

    ```javascript
    grpcServer {
        port = 9090 //(1)!
        telemetry {
            logging {
                enabled = true //(2)!
            }
            metrics {
                enabled = true //(3)!
                slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(4)!
            }
            telemetry {
                enabled = true //(5)!
            }
        }
    }
    ```

    1. gRPC server port
    2. Enables module logging
    3. Enables module metrics
    4. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    5. Enables module tracing

=== ":simple-yaml: `YAML`"

    ```yaml
    grpcServer:
      port: 9090 #(1)!
      telemetry:
        logging:
          enabled: true #(2)!
        metrics:
          enabled: true #(3)!
          slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(4)!
        telemetry:
          enabled: true #(5)!
    ```

    1. gRPC server port
    2. Enables module logging
    3. Enables module metrics
    4. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    5. Enables module tracing

## Plugin

The code for the gRPC server can be created with [protobuf gradle plugin](https://github.com/google/protobuf-gradle-plugin).

=== ":fontawesome-brands-java: `Java`"

    Plugin `build.gradle`:
    ```groovy
    plugins {
        id "com.google.protobuf" version "0.9.4"
    }

    protobuf {
        protoc { artifact = "com.google.protobuf:protoc:3.24.4" }
        plugins {
            grpc { artifact = "io.grpc:protoc-gen-grpc-java:1.58.0" }
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

    Plugin `build.gradle.kts`:
    ```groovy
    import com.google.protobuf.gradle.id

    plugins {
        id("com.google.protobuf") version ("0.9.4")
    }

    protobuf {
        protoc { artifact = "com.google.protobuf:protoc:3.24.4" }
        plugins {
            id("grpc") { artifact = "io.grpc:protoc-gen-grpc-java:1.58.0" }
        }

        generateProtoTasks {
            ofSourceSet("main").forEach {
                it.plugins { id("grpc") { } }
            }
        }
    }

    kotlin {
        sourceSets.main {
            kotlin.srcDir("build/generated/source/proto/main/grpc")
            kotlin.srcDir("build/generated/source/proto/main/java")
        }
    }
    ```

## Handlers

Created gRPC service handlers are required to be tagged with the `@Component` annotation:

=== ":fontawesome-brands-java: `Java`"

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

Adding your own interceptor requires creating an inheritor of `ServerInterceptor` with the `@Component` annotation:

=== ":fontawesome-brands-java: `Java`"

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
