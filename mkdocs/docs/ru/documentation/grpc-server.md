---
description: "Explains Kora gRPC server generation, protobuf Gradle plugin setup, server configuration, handlers, interceptors, reflection, and debugging. Use when working with GrpcServerModule, @GrpcService, @InterceptWith, GrpcServerConfig, GrpcServerInterceptor, Server Reflection."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora gRPC server generation, protobuf Gradle plugin setup, server configuration, handlers, interceptors, reflection, and debugging; key triggers include GrpcServerModule, @GrpcService, @InterceptWith, GrpcServerConfig, GrpcServerInterceptor, Server Reflection."
---

Модуль поднимает `gRPC-сервер` на основе [`grpc-java`](https://grpc.io/docs/languages/java/basics/) и подключает к нему обработчики из графа приложения.
Обработчик представляет собой `BindableService`, обычно это класс, наследующийся от сгенерированного `...ImplBase`.

Kora создает `NettyServerBuilder`, добавляет серверные службы, пользовательские и стандартные `ServerInterceptor`, управляет жизненным циклом сервера и участвует в проверке готовности приложения.
Если конфигурации недостаточно, итоговый `NettyServerBuilder` можно дополнительно настроить кодом через `GrpcServerBuilderConfigurer`.

Если нужен пошаговый разбор перед справочным описанием, смотрите [gRPC-сервер](../guides/grpc-server.md) и [продвинутый gRPC-сервер](../guides/grpc-server-advanced.md).

## Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:grpc-server"
    implementation "io.grpc:grpc-protobuf:1.74.0"
    implementation "javax.annotation:javax.annotation-api:1.3.2"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends GrpcServerModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:grpc-server")
    implementation("io.grpc:grpc-protobuf:1.74.0")
    implementation("javax.annotation:javax.annotation-api:1.3.2")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : GrpcServerModule
    ```

### Плагин { #plugin }

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

    Плагин `build.gradle.kts`:
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

## Конфигурация { #configuration }

Пример полной конфигурации, описанной в классе `GrpcServerConfig`:

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

    1.  Порт `gRPC-сервера` (по умолчанию: `8090`)
    2.  Максимальный размер входящего сообщения (по умолчанию: `4MiB`). Указывается как число в байтах либо как `4MiB`, `4MB`, `1000Kb` и т.п.
    3.  Включает сервис [`gRPC Server Reflection`](#reflection) (по умолчанию: `false`)
    4.  Время ожидания обработки перед выключением сервера в случае [штатного завершения](container.md#component-lifecycle) (по умолчанию: `30s`)
    5.  Устанавливает пользовательский максимальный возраст соединения, при превышении которого соединение будет штатно прервано (по умолчанию не указано, необязательно). К значению будет добавлен случайный коэффициент +/-10%.
    6.  Устанавливает дополнительное время для штатного завершения соединения после достижения максимального возраста соединения (по умолчанию не указано, необязательно). `RPC`, не завершившиеся вовремя, будут отменены, чтобы соединение могло завершиться.
    7.  Устанавливает интервал времени между `PING`-кадрами (по умолчанию не указано, необязательно)
    8.  Время ожидания подтверждения `PING`-кадра (по умолчанию не указано, необязательно). Если подтверждение не получено за это время, соединение будет закрыто.
    9.  Включает логирование модуля (по умолчанию: `false`)
    10.  Включает метрики модуля (по умолчанию: `true`)
    11.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрики [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    12.  Теги метрик (по умолчанию: `{}`)
    13.  Включает трассировку модуля (по умолчанию: `true`)
    14.  Атрибуты трассировки (по умолчанию: `{}`)

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

    1.  Порт `gRPC-сервера` (по умолчанию: `8090`)
    2.  Максимальный размер входящего сообщения (по умолчанию: `4MiB`). Указывается как число в байтах либо как `4MiB`, `4MB`, `1000Kb` и т.п.
    3.  Включает сервис [`gRPC Server Reflection`](#reflection) (по умолчанию: `false`)
    4.  Время ожидания обработки перед выключением сервера в случае [штатного завершения](container.md#component-lifecycle) (по умолчанию: `30s`)
    5.  Устанавливает пользовательский максимальный возраст соединения, при превышении которого соединение будет штатно прервано (по умолчанию не указано, необязательно). К значению будет добавлен случайный коэффициент +/-10%.
    6.  Устанавливает дополнительное время для штатного завершения соединения после достижения максимального возраста соединения (по умолчанию не указано, необязательно). `RPC`, не завершившиеся вовремя, будут отменены, чтобы соединение могло завершиться.
    7.  Устанавливает интервал времени между `PING`-кадрами (по умолчанию не указано, необязательно)
    8.  Время ожидания подтверждения `PING`-кадра (по умолчанию не указано, необязательно). Если подтверждение не получено за это время, соединение будет закрыто.
    9.  Включает логирование модуля (по умолчанию: `false`)
    10.  Включает метрики модуля (по умолчанию: `true`)
    11.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрики [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
    12.  Теги метрик (по умолчанию: `{}`)
    13.  Включает трассировку модуля (по умолчанию: `true`)
    14.  Атрибуты трассировки (по умолчанию: `{}`)

Можно также настроить [Netty транспорт](netty.md).

### Настройка через код { #builder-configurer }

Если параметров конфигурации недостаточно, можно зарегистрировать компонент `GrpcServerBuilderConfigurer` и донастроить `NettyServerBuilder` кодом.
Такой компонент вызывается после применения конфигурации, добавления служб, пользовательских и стандартных `ServerInterceptor`.

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

Предоставляемые метрики модуля описаны в разделе [Справочник метрик](metrics.md#grpc-server).

## Обработчики { #handlers }

Созданные `gRPC-сервисы` нужно добавить в граф приложения с помощью аннотации `@Component`.
Обычно обработчик наследуется от класса `...ImplBase`, который сгенерировал `protobuf gradle plugin` из `proto`-описания.

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

## Перехватчики { #interceptors }

[Перехватчики](https://grpc.github.io/grpc-java/javadoc/io/grpc/ServerInterceptor.html) позволяют обрабатывать запросы до передачи в `gRPC-сервис`.
Они подходят для сквозной логики: логирования, авторизации, трассировки, работы с `Metadata` и преобразования ошибок.

### Стандартные { #default }

При запуске сервера Kora добавляет стандартные перехватчики:

- `TelemetryInterceptor`
- `ContextServerInterceptor`
- `CoroutineContextInjectInterceptor`

`TelemetryInterceptor` включает телеметрию сервера: логирование, метрики и трассировку в зависимости от подключенных модулей и настроек `grpcServer.telemetry`.
`ContextServerInterceptor` переносит контекст Kora в обработку вызова, а `CoroutineContextInjectInterceptor` добавляет поддержку `CoroutineContext` для `Kotlin`.

Пользовательские `ServerInterceptor` из графа приложения добавляются в `NettyServerBuilder` до стандартных перехватчиков.
Для полной настройки `NettyServerBuilder` используйте [GrpcServerBuilderConfigurer](#builder-configurer).

### Собственные { #custom }

Для добавления собственного перехватчика требуется создать реализацию `ServerInterceptor` с аннотацией `@Component`:

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

## Отладка { #reflection }

Поддерживается [`gRPC Server Reflection`](https://github.com/grpc/grpc/blob/master/doc/server-reflection.md), который предоставляет информацию о доступных `gRPC-сервисах` на сервере.
Рефлексия помогает клиентам и инструментам во время выполнения строить `RPC`-запросы без заранее скомпилированной информации о сервисе.
Например, ее использует `gRPC CLI`, с помощью которого можно исследовать `proto`-описания сервера и отправлять тестовые `RPC`.
`gRPC Server Reflection` поддерживается только для сервисов, основанных на `proto`.

Подробнее о работе с `gRPC Server Reflection` можно прочитать в [руководстве grpc-java](https://github.com/grpc/grpc-java/blob/master/documentation/server-reflection-tutorial.md#enable-server-reflection).

### Подключение { #dependency-2 }

Требуется дополнительно подключить зависимость [`gRPC Server Reflection`](https://mvnrepository.com/artifact/io.grpc/grpc-services).

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.grpc:grpc-services:1.74.0"
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.grpc:grpc-services:1.74.0")
    ```

### Конфигурация { #configuration-2 }

Требуется также включить сервис `gRPC Server Reflection` в конфигурации.
Kora добавит его в сервер только если в приложении есть класс `io.grpc.protobuf.services.ProtoReflectionService`, поэтому одной настройки без зависимости недостаточно.

===! ":material-code-json: `Hocon`"

    ```javascript
    grpcServer {
        reflectionEnabled = false //(1)!
    }
    ```

    1.  Включает сервис `gRPC Server Reflection` (по умолчанию: `false`)

=== ":simple-yaml: `YAML`"

    ```yaml
    grpcServer:
      reflectionEnabled: false #(1)!
    ```

    1.  Включает сервис `gRPC Server Reflection` (по умолчанию: `false`)
