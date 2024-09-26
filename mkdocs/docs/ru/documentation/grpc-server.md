Модуль для подключения gRPC серверных обработчиков на основе функционала [grpc.io](https://grpc.io/docs/languages/java/basics/)

## Подключение

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#_4) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:grpc-server"
    implementation "io.grpc:grpc-protobuf:1.62.2"
    implementation "javax.annotation:javax.annotation-api:1.3.2"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends GrpcServerModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#_4) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:grpc-server")
    implementation("io.grpc:grpc-protobuf:1.62.2")
    implementation("javax.annotation:javax.annotation-api:1.3.2")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : GrpcServerModule
    ```

### Плагин

Код для gRPC-сервера создается с помощью [protobuf gradle plugin](https://github.com/google/protobuf-gradle-plugin).

===! ":fontawesome-brands-java: `Java`"

    Плагин `build.gradle`:
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

    Плагин `build.gradle.kts`:
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

## Конфигурация

Пример полной конфигурации, описанной в классе `GrpcServerConfig` (указаны примеры значений или значения по умолчанию):

===! ":material-code-json: `Hocon`"

    ```javascript
    grpcServer {
        port = 8090 //(1)!
        maxMessageSize = "4MiB" //(2)!
        reflectionEnabled = false //(3)!
        telemetry {
            logging {
                enabled = false //(4)!
            }
            metrics {
                enabled = true //(5)!
                slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(6)!
            }
            tracing {
                enabled = true //(7)!
            }
        }
    }
    ```

    1.  Порт gRPC сервера
    2.  Максимальный размер входящего сообщения (указывается как число в байтах / либо как `4MiB` / `4MB` / `1000Kb` и тп)
    3.  Включает сервис [gRPC Server Reflection](#_8)
    4.  Включает логгирование модуля (по умолчанию `false`)
    5.  Включает метрики модуля (по умолчанию `true`)
    6.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    7.  Включает трассировку модуля (по умолчанию `true`)

=== ":simple-yaml: `YAML`"

    ```yaml
    grpcServer:
      port: 8090 #(1)!
      maxMessageSize = "4MiB" #(2)!
      reflectionEnabled = false #(3)!
      telemetry:
        logging:
          enabled: false #(4)!
        metrics:
          enabled: true #(5)!
          slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(6)!
        telemetry:
          enabled: true #(7)!
    ```

    1.  Порт gRPC сервера
    2.  Максимальный размер входящего сообщения (указывается как число в байтах / либо как `4MiB` / `4MB` / `1000Kb` и тп)
    3.  Включает сервис [gRPC Server Reflection](#_8)
    4.  Включает логгирование модуля (по умолчанию `false`)
    5.  Включает метрики модуля (по умолчанию `true`)
    6.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    7.  Включает трассировку модуля (по умолчанию `true`)

Можно также настроить [Netty транспорт](netty.md).

## Обработчики

Созданные gRPC сервисы требуется пометить аннотацией `@Component`:

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

## Отладка

Поддерживается [gRPC Server Reflection](https://github.com/grpc/grpc/blob/master/doc/server-reflection.md)
который предоставляет информацию об общедоступных gRPC-сервисах на сервере 
и помогает клиентам во время выполнения строить запросы и ответы RPC без предварительно скомпилированной информации о сервисе.
Он используется инструментом командной строки gRPC (gRPC CLI), с помощью которого можно исследовать proto-файлы сервера и отправлять/получать тестовые RPC.
Reflection поддерживается только для сервисов, основанных на proto.

Подробнее о работе с gRPC Server Reflection можно ознакомится [тут](https://github.com/grpc/grpc-java/blob/master/documentation/server-reflection-tutorial.md#enable-server-reflection).

### Подключение

Требуется дополнительно подключить зависимость [gRPC Server Reflection](https://mvnrepository.com/artifact/io.grpc/grpc-services).

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#_4) `build.gradle`:
    ```groovy
    implementation "io.grpc:grpc-services:1.62.2"
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#_4) `build.gradle.kts`:
    ```groovy
    implementation("io.grpc:grpc-services:1.62.2")
    ```

### Конфигурация

Требуется также включить сервис gRPC Server Reflection в конфигурации:

===! ":material-code-json: `Hocon`"

    ```javascript
    grpcServer {
        reflectionEnabled = false //(1)!
    }
    ```

    1.  Включает сервис gRPC Server Reflection

=== ":simple-yaml: `YAML`"

    ```yaml
    grpcServer:
      reflectionEnabled: false #(1)!
    ```

    1.  Включает сервис gRPC Server Reflection
