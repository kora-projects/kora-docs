Модуль для подключения gRPC серверных обработчиков на основе функционала [grpc.io](https://grpc.io/docs/languages/java/basics/)

## Подключение

=== ":fontawesome-brands-java: `Java`"

    Зависимость `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:grpc-server"
    implementation "io.grpc:grpc-protobuf:1.58.0"
    implementation "javax.annotation:javax.annotation-api:1.3.2"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends GrpcServerModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Зависимость `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:grpc-server")
    implementation("io.grpc:grpc-protobuf:1.58.0")
    implementation("javax.annotation:javax.annotation-api:1.3.2")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : GrpcServerModule
    ```

## Конфигурация

Параметры, описанные в классе `GrpcServerConfig`:

===! ":material-code-json: `Hocon`"

    ```javascript
    grpcServer {
        port = 8090
        telemetry {
            logging {
                enabled = true //(1)!
            }
            metrics {
                enabled = true //(2)!
                slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(3)!
            }
            telemetry {
                enabled = true //(4)!
            }
        }
    }
    ```

    1.  Включает логгирование модуля
    2.  Включает метрики модуля
    3.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    4.  Включает трассировку модуля

=== ":simple-yaml: `YAML`"

    ```yaml
    grpcServer:
      port: 8090
      telemetry:
        logging:
          enabled: true #(1)!
        metrics:
          enabled: true #(2)!
          slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(3)!
        telemetry:
          enabled: true #(4)!
    ```

    1.  Включает логгирование модуля
    2.  Включает метрики модуля
    3.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    4.  Включает трассировку модуля

## Плагин

Код для gRPC-сервера можно создать с помощью [protobuf gradle plugin](https://github.com/google/protobuf-gradle-plugin).

=== ":fontawesome-brands-java: `Java`"

    Плагин `build.gradle`:
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

    Плагин `build.gradle.kts`:
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

## Обработчики

Созданные gRPC сервисы требуется пометить аннотацией `@Component`:

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

## Перехватчики

[Перехватчики](https://grpc.github.io/grpc-java/javadoc/io/grpc/ServerInterceptor.html) позволяют перехватывать запросы перед тем, как они будут переданы обработчикам.

### Стандартные

При запуске сервера по-умолчанию используются следующие перехватчики:

- `ContextServerInterceptor`
- `CoroutineContextInjectInterceptor`
- `MetricCollectorServerInterceptor`
- `LoggingServerInterceptor`

Для переопределения списка перехватчиков по умолчанию можно переопределить метод `serverBuilder` из класса `GrpcModule`

### Собственные

Для добавления собственного перехватчика требуется создать наследника `ServerInterceptor` с аннотацией `@Component`:

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
