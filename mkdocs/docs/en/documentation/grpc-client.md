Module for gRPC client service support based on [grpc.io](https://grpc.io/docs/languages/java/basics/) functionality.

## Dependency

=== ":fontawesome-brands-java: `Java`"

    Dependency `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:grpc-client"
    implementation "io.grpc:grpc-protobuf:1.58.0"
    implementation "javax.annotation:javax.annotation-api:1.3.2"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends GrpcClientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Dependency `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:grpc-client")
    implementation("io.grpc:grpc-protobuf:1.58.0")
    implementation("javax.annotation:javax.annotation-api:1.3.2")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : GrpcClientModule
    ```

## Configuration

The parameters described in the `GrpcClientConfig` class and below shows an example configuration for a service named `UserService`:

===! ":material-code-json: `Hocon`"

    ```javascript
    grpcClient {
        UserService {
            url = "grpc://localhost:8090" //(1)!
            timeout = "10s"  //(2)!
            telemetry {
                logging {
                    enabled = true //(3)!
                }
                metrics {
                    enabled = true //(4)!
                    slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(5)!
                }
                telemetry {
                    enabled = true //(6)!
                }
            }
        }
    }
    ```

    1. URL of the server where to make requests
    2. Maximum request time
    3. Enables module logging
    4. Enables module metrics
    5. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    6. Enables module tracing

=== ":simple-yaml: `YAML`"

    ```yaml
    grpcClient:
      UserService:
        url: "grpc://localhost:8090" //(1)!
        timeout: "10s" //(2)!
        telemetry:
          logging:
            enabled: true #(1)!
          metrics:
            enabled: true #(2)!
            slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(3)!
          telemetry:
            enabled: true #(4)!
    ```

    1. URL of the server where to make requests
    2. Maximum request time
    3. Enables module logging
    4. Enables module metrics
    5. Configures [SLO](https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli) for [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) metrics
    6. Enables module tracing

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

## Service

Created gRPC services can be injected as dependency:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends HoconConfigModule, GrpcClientModule {

        default SomeService(UserServiceGrpc.UserServiceBlockingStub grpcService) {
            return new SomeService(grpcService);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : HoconConfigModule, GrpcClientModule {
        fun SomeService(grpcService: UserServiceGrpc.UserServiceBlockingStub?) {
            return SomeService(grpcService)
        }
    }
    ```
