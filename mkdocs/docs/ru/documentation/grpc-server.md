---
description: "Explains Kora gRPC server: protobuf Gradle plugin setup, server configuration, unary and streaming handlers, io.grpc.Status error handling, ServerInterceptor interceptors and their execution order, lifecycle and readiness, telemetry, and reflection. Use when working with GrpcServerModule, GrpcServerConfig, GrpcServerBuilderConfigurer, ServerInterceptor, StreamObserver, reflectionEnabled, Server Reflection."
agent:
  use_when: "Use this file for Kora docs or implementation questions about the Kora gRPC server: protobuf Gradle plugin setup, server configuration, unary and streaming handlers, io.grpc.Status error handling, ServerInterceptor interceptors and their execution order, scoping and metadata authorization, lifecycle and readiness, telemetry, and reflection; key triggers include GrpcServerModule, GrpcServerConfig, GrpcServerBuilderConfigurer, ServerInterceptor, StreamObserver, reflectionEnabled, Server Reflection. Note: gRPC server interceptors are global io.grpc.ServerInterceptor beans only; there is no @GrpcService or @InterceptWith annotation in this module."
---

Модуль запускает `gRPC-сервер` на основе [`grpc-java`](https://grpc.io/docs/languages/java/basics/) и подключает к нему обработчики из графа приложения.
Обработчик — это `BindableService`, обычно класс, который наследует сгенерированный `...ImplBase` и реализует унарные или потоковые методы `RPC`.

Kora создает `NettyServerBuilder`, добавляет сервисы сервера, пользовательские и стандартные `ServerInterceptor`, управляет жизненным циклом сервера и участвует в проверках готовности приложения.
Если параметров конфигурации недостаточно, итоговый `NettyServerBuilder` можно дополнительно настроить в коде через `GrpcServerBuilderConfigurer`.

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

Код для `gRPC-сервера` генерируется с помощью [gradle-плагина protobuf](https://github.com/google/protobuf-gradle-plugin).

===! ":fontawesome-brands-java: `Java`"

    Плагин в `build.gradle`:
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

    Плагин в `build.gradle.kts`:
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

Обычно нужно задать только `port`; все остальные параметры имеют значения по умолчанию.
Минимальная конфигурация, которая привязывает порт из переменной окружения и включает логирование, выглядит так:

===! ":material-code-json: `Hocon`"

    ```javascript
    grpcServer {
        port = 8090
        telemetry.logging.enabled = true
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    grpcServer:
      port: 8090
      telemetry:
        logging:
          enabled: true
    ```

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

    1. Порт `gRPC-сервера` (по умолчанию: `8090`).
    2. Максимальный размер входящего сообщения (по умолчанию: `4MiB`). Может быть указан в виде числа байт или как `4MiB`, `4MB`, `1000Kb` и подобных значений.
    3. Включает сервис [`gRPC Server Reflection`](#reflection) (по умолчанию: `false`).
    4. Время ожидания обработки перед выключением сервера при [штатном завершении](container.md#graceful-shutdown) (по умолчанию: `30s`).
    5. Задает пользовательское максимальное время жизни соединения, после которого соединение штатно завершается (по умолчанию: не задано, опционально). К значению добавляется случайное отклонение +/-10%.
    6. Задает дополнительное время для штатного завершения соединения после достижения максимального времени жизни соединения (по умолчанию: не задано, опционально). Вызовы `RPC`, которые не успевают завершиться, отменяются, чтобы соединение могло завершиться.
    7. Задает интервал между кадрами `PING` (по умолчанию: не задано, опционально).
    8. Тайм-аут подтверждения кадра `PING` (по умолчанию: не задано, опционально). Если подтверждение не получено за это время, соединение закрывается.
    9. Включает логирование модуля (по умолчанию: `false`).
    10. Включает метрики модуля (по умолчанию: `true`).
    11. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрики [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
    12. Теги метрик (по умолчанию: `{}`).
    13. Включает трассировку модуля (по умолчанию: `true`).
    14. Атрибуты трассировки (по умолчанию: `{}`).

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

    1. Порт `gRPC-сервера` (по умолчанию: `8090`).
    2. Максимальный размер входящего сообщения (по умолчанию: `4MiB`). Может быть указан в виде числа байт или как `4MiB`, `4MB`, `1000Kb` и подобных значений.
    3. Включает сервис [`gRPC Server Reflection`](#reflection) (по умолчанию: `false`).
    4. Время ожидания обработки перед выключением сервера при [штатном завершении](container.md#graceful-shutdown) (по умолчанию: `30s`).
    5. Задает пользовательское максимальное время жизни соединения, после которого соединение штатно завершается (по умолчанию: не задано, опционально). К значению добавляется случайное отклонение +/-10%.
    6. Задает дополнительное время для штатного завершения соединения после достижения максимального времени жизни соединения (по умолчанию: не задано, опционально). Вызовы `RPC`, которые не успевают завершиться, отменяются, чтобы соединение могло завершиться.
    7. Задает интервал между кадрами `PING` (по умолчанию: не задано, опционально).
    8. Тайм-аут подтверждения кадра `PING` (по умолчанию: не задано, опционально). Если подтверждение не получено за это время, соединение закрывается.
    9. Включает логирование модуля (по умолчанию: `false`).
    10. Включает метрики модуля (по умолчанию: `true`).
    11. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрики [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
    12. Теги метрик (по умолчанию: `{}`).
    13. Включает трассировку модуля (по умолчанию: `true`).
    14. Атрибуты трассировки (по умолчанию: `{}`).

Также можно настроить [транспорт Netty](netty.md).

### Конфигурация в коде { #builder-configurer }

Если параметров конфигурации недостаточно, зарегистрируйте компонент `GrpcServerBuilderConfigurer` и дополнительно настройте `NettyServerBuilder` в коде.
Этот компонент вызывается после применения конфигурации и после добавления сервисов, пользовательских `ServerInterceptor` и стандартных `ServerInterceptor`.

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

Метрики модуля описаны в разделе [Справочник метрик](metrics.md#grpc-server).

## Обработчики { #handlers }

Обработчик — это класс, который наследует сгенерированный `...ImplBase` и регистрируется в графе приложения с помощью аннотации `@Component`.
Класс `...ImplBase` создается из контракта `proto` с помощью [gradle-плагина protobuf](#plugin); вы переопределяете его методы `RPC`, чтобы реализовать поведение сервера.
Обычные компоненты Kora, такие как сервисы и репозитории, можно внедрить в обработчик через его конструктор.

Рассмотрим контракт `proto` с единственным унарным методом:

```protobuf title="src/main/proto/message.proto"
syntax = "proto3";

package ru.tinkoff.kora.generated.grpc;

service UserService {
  rpc createUser(RequestEvent) returns (ResponseEvent) {} //(1)!
}

message RequestEvent {
  string name = 1;
  string code = 2;
}

message ResponseEvent {
  bytes id = 1;
}
```

1. Унарный `RPC`: одно сообщение запроса порождает одно сообщение ответа.

Плагин генерирует `UserServiceGrpc.UserServiceImplBase`, а обработчик переопределяет сгенерированный метод.
Сгенерированный метод получает сообщение запроса и [`StreamObserver`](https://grpc.github.io/grpc-java/javadoc/io/grpc/stub/StreamObserver.html),
который используется для отправки ответов обратно клиенту:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class UserService extends UserServiceGrpc.UserServiceImplBase {

        @Override
        public void createUser(Message.RequestEvent request, StreamObserver<Message.ResponseEvent> responseObserver) { //(1)!
            var response = Message.ResponseEvent.newBuilder()
                .setId(ByteString.copyFromUtf8(UUID.randomUUID().toString()))
                .build();

            responseObserver.onNext(response); //(2)!
            responseObserver.onCompleted(); //(3)!
        }
    }
    ```

    1. Сгенерированный метод получает сообщение запроса и `StreamObserver` для отправки ответа
    2. Отправляет клиенту одно сообщение ответа
    3. Сигнализирует о завершении вызова; для унарного метода вызывается ровно один раз, после единственного `onNext`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class UserService : UserServiceGrpc.UserServiceImplBase() {

        override fun createUser(request: Message.RequestEvent, responseObserver: StreamObserver<Message.ResponseEvent>) { //(1)!
            val response = Message.ResponseEvent.newBuilder()
                .setId(ByteString.copyFromUtf8(UUID.randomUUID().toString()))
                .build()

            responseObserver.onNext(response) //(2)!
            responseObserver.onCompleted() //(3)!
        }
    }
    ```

    1. Сгенерированный метод получает сообщение запроса и `StreamObserver` для отправки ответа
    2. Отправляет клиенту одно сообщение ответа
    3. Сигнализирует о завершении вызова; для унарного метода вызывается ровно один раз, после единственного `onNext`

### Серверная потоковая передача { #server-streaming }

Для серверного потокового `RPC` (`returns (stream ...)` в `proto`) клиент отправляет один запрос, а сервер возвращает много сообщений.
Вызывайте `onNext` для каждого сообщения, а затем один раз `onCompleted` в конце:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Override
    public void getAllUsers(Message.RequestEvent request, StreamObserver<Message.ResponseEvent> responseObserver) {
        for (var user : userService.findAll()) {
            responseObserver.onNext(toResponse(user)); //(1)!
        }
        responseObserver.onCompleted(); //(2)!
    }
    ```

    1. Отправляет одно из нескольких сообщений ответа
    2. Завершает поток ответа после последнего сообщения

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    override fun getAllUsers(request: Message.RequestEvent, responseObserver: StreamObserver<Message.ResponseEvent>) {
        userService.findAll().forEach { responseObserver.onNext(toResponse(it)) } //(1)!
        responseObserver.onCompleted() //(2)!
    }
    ```

    1. Отправляет одно из нескольких сообщений ответа
    2. Завершает поток ответа после последнего сообщения

### Клиентская потоковая передача { #client-streaming }

Для клиентского потокового `RPC` (`rpc method(stream ...)`) клиент отправляет много сообщений, а сервер отвечает один раз в конце.
Сгенерированный метод **возвращает** `StreamObserver`, который получает входящие сообщения запроса; итоговый ответ формируется в `onCompleted`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Override
    public StreamObserver<Message.RequestEvent> createUsers(StreamObserver<Message.ResponseEvent> responseObserver) {
        return new StreamObserver<>() {
            private final List<Message.RequestEvent> received = new ArrayList<>();

            @Override
            public void onNext(Message.RequestEvent value) {
                received.add(value); //(1)!
            }

            @Override
            public void onError(Throwable t) {
                responseObserver.onError(t); //(2)!
            }

            @Override
            public void onCompleted() {
                responseObserver.onNext(aggregate(received)); //(3)!
                responseObserver.onCompleted();
            }
        };
    }
    ```

    1. Собирает каждое входящее сообщение запроса
    2. Пробрасывает ошибку потока со стороны клиента
    3. Формирует единственный агрегированный ответ после того, как клиент завершил отправку

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    override fun createUsers(responseObserver: StreamObserver<Message.ResponseEvent>): StreamObserver<Message.RequestEvent> {
        return object : StreamObserver<Message.RequestEvent> {
            private val received = mutableListOf<Message.RequestEvent>()

            override fun onNext(value: Message.RequestEvent) {
                received += value //(1)!
            }

            override fun onError(t: Throwable) {
                responseObserver.onError(t) //(2)!
            }

            override fun onCompleted() {
                responseObserver.onNext(aggregate(received)) //(3)!
                responseObserver.onCompleted()
            }
        }
    }
    ```

    1. Собирает каждое входящее сообщение запроса
    2. Пробрасывает ошибку потока со стороны клиента
    3. Формирует единственный агрегированный ответ после того, как клиент завершил отправку

### Двунаправленная потоковая передача { #bidirectional-streaming }

Для двунаправленного потокового `RPC` (`rpc method(stream ...) returns (stream ...)`) обе стороны обмениваются множеством сообщений в рамках одного вызова.
Метод возвращает `StreamObserver` для входящих запросов и может отправлять ответы в любой момент через `responseObserver`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Override
    public StreamObserver<Message.RequestEvent> updateUsers(StreamObserver<Message.ResponseEvent> responseObserver) {
        return new StreamObserver<>() {
            @Override
            public void onNext(Message.RequestEvent value) {
                responseObserver.onNext(process(value)); //(1)!
            }

            @Override
            public void onError(Throwable t) {
                responseObserver.onError(t);
            }

            @Override
            public void onCompleted() {
                responseObserver.onCompleted(); //(2)!
            }
        };
    }
    ```

    1. Отвечает на каждое входящее сообщение по мере его поступления
    2. Завершает поток ответа, когда клиент прекращает отправку

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    override fun updateUsers(responseObserver: StreamObserver<Message.ResponseEvent>): StreamObserver<Message.RequestEvent> {
        return object : StreamObserver<Message.RequestEvent> {
            override fun onNext(value: Message.RequestEvent) {
                responseObserver.onNext(process(value)) //(1)!
            }

            override fun onError(t: Throwable) {
                responseObserver.onError(t)
            }

            override fun onCompleted() {
                responseObserver.onCompleted() //(2)!
            }
        }
    }
    ```

    1. Отвечает на каждое входящее сообщение по мере его поступления
    2. Завершает поток ответа, когда клиент прекращает отправку

### Обработка ошибок { #error-handling }

**Описание**: gRPC представляет ошибки вызова с помощью кода [`io.grpc.Status`](https://grpc.github.io/grpc-java/javadoc/io/grpc/Status.html)
и необязательного описания, а не с помощью кодов ответа HTTP.
Чтобы завершить вызов с ошибкой, завершите observer ответа вызовом `responseObserver.onError(status.asRuntimeException())`
или выбросьте `StatusRuntimeException` из обработчика.
Автоматически зарегистрированный [`TelemetryInterceptor`](#default) наблюдает финальный `Status` при закрытии вызова
(в `close`, `onHalfClose`, `onCancel` и `onComplete`) и соответствующим образом записывает логирование, метрики и трассировку.

**Причины**: выбирайте код `Status`, соответствующий сбою, — например, `Status.NOT_FOUND` для отсутствующей сущности,
`Status.INVALID_ARGUMENT` для некорректных входных данных, `Status.UNAUTHENTICATED` или `Status.PERMISSION_DENIED` для сбоев авторизации
и `Status.INTERNAL` для непредвиденных ошибок сервера.

**Рекомендации**:

- Прикрепляйте понятное человеку сообщение через `withDescription(...)` и сохраняйте исходное исключение через `withCause(...)`, чтобы телеметрия могла его записать.
- Завершайте вызов ровно один раз: никогда не вызывайте `onError` после `onCompleted` и не вызывайте ни один из них дважды.
- Не раскрывайте клиентам внутренние детали исключений; сначала сопоставьте их с подходящим `Status`.

**Пример обработки**: унарный обработчик, который возвращает `NOT_FOUND`, когда сущность отсутствует, и сопоставляет непредвиденные сбои с `INTERNAL`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Override
    public void getUser(Message.RequestEvent request, StreamObserver<Message.ResponseEvent> responseObserver) {
        try {
            var user = userService.getUser(request.getName())
                .orElseThrow(() -> Status.NOT_FOUND
                    .withDescription("User not found: " + request.getName())
                    .asRuntimeException()); //(1)!
            responseObserver.onNext(toResponse(user));
            responseObserver.onCompleted();
        } catch (StatusRuntimeException e) {
            responseObserver.onError(e); //(2)!
        } catch (Exception e) {
            responseObserver.onError(Status.INTERNAL
                .withDescription("Failed to get user")
                .withCause(e) //(3)!
                .asRuntimeException());
        }
    }
    ```

    1. Строит ошибку `NOT_FOUND` с описанием
    2. Передает клиенту уже сопоставленную ошибку `Status`
    3. Сохраняет исходное исключение в качестве причины, чтобы телеметрия могла его записать

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    override fun getUser(request: Message.RequestEvent, responseObserver: StreamObserver<Message.ResponseEvent>) {
        try {
            val user = userService.getUser(request.name)
                ?: throw Status.NOT_FOUND
                    .withDescription("User not found: ${request.name}")
                    .asRuntimeException() //(1)!
            responseObserver.onNext(toResponse(user))
            responseObserver.onCompleted()
        } catch (e: StatusRuntimeException) {
            responseObserver.onError(e) //(2)!
        } catch (e: Exception) {
            responseObserver.onError(
                Status.INTERNAL
                    .withDescription("Failed to get user")
                    .withCause(e) //(3)!
                    .asRuntimeException()
            )
        }
    }
    ```

    1. Строит ошибку `NOT_FOUND` с описанием
    2. Передает клиенту уже сопоставленную ошибку `Status`
    3. Сохраняет исходное исключение в качестве причины, чтобы телеметрия могла его записать

### Сигнатуры { #signatures }

Форма метода обработчика определяется контрактом `proto` и сгенерированным `...ImplBase`:

===! ":fontawesome-brands-java: `Java`"

    Под `Req` и `Resp` подразумеваются сгенерированные типы сообщений запроса и ответа.

    - Унарный: `void myMethod(Req request, StreamObserver<Resp> responseObserver)`
    - Серверная потоковая передача: `void myMethod(Req request, StreamObserver<Resp> responseObserver)` (несколько `onNext`, один `onCompleted`)
    - Клиентская потоковая передача: `StreamObserver<Req> myMethod(StreamObserver<Resp> responseObserver)`
    - Двунаправленная потоковая передача: `StreamObserver<Req> myMethod(StreamObserver<Resp> responseObserver)`

    Сгенерированный метод возвращает `void` (или `StreamObserver` для запроса), поэтому результаты доставляются асинхронно через колбэки `StreamObserver`;
    ответы могут завершаться из другого потока.

=== ":simple-kotlin: `Kotlin`"

    Под `Req` и `Resp` подразумеваются сгенерированные типы сообщений запроса и ответа.

    - Унарный: `myMethod(request: Req, responseObserver: StreamObserver<Resp>)`
    - Серверная потоковая передача: `myMethod(request: Req, responseObserver: StreamObserver<Resp>)` (несколько `onNext`, один `onCompleted`)
    - Клиентская потоковая передача: `myMethod(responseObserver: StreamObserver<Resp>): StreamObserver<Req>`
    - Двунаправленная потоковая передача: `myMethod(responseObserver: StreamObserver<Resp>): StreamObserver<Req>`

    Когда вы генерируете корутинные заглушки с помощью плагина [`grpc-kotlin`](https://github.com/grpc/grpc-kotlin) (`io.grpc:protoc-gen-grpc-kotlin`)
    и наследуете сгенерированный `...CoroutineImplBase`, методы обработчика могут быть `suspend`-функциями (а потоковые методы могут использовать `Flow`).
    Kora автоматически регистрирует [`CoroutineContextInjectInterceptor`](#default), который внедряет `Context` Kora в `CoroutineContext` обработчика;
    он активируется только при наличии `kotlinx-coroutines` в classpath.

## Перехватчики { #interceptors }

[`io.grpc.ServerInterceptor`](https://grpc.github.io/grpc-java/javadoc/io/grpc/ServerInterceptor.html) обрабатывает вызов до того, как он будет передан в `gRPC-сервис`.
Перехватчики подходят для сквозной логики: логирования, авторизации, трассировки, работы с `Metadata` и сопоставления ошибок.

В отличие от [HTTP-сервера](http-server.md#interceptors), модуль gRPC-сервера **не** имеет аннотаций `@GrpcService` или `@InterceptWith`:
каждый `ServerInterceptor`, зарегистрированный как `@Component`, применяется **глобально** ко всем сервисам на сервере.
Чтобы ограничить перехватчик одним сервисом или методом, анализируйте вызов во время выполнения — смотрите [Ограничение области и авторизация](#authorization).

### Стандартные { #default }

При запуске сервера Kora добавляет стандартные перехватчики:

- `TelemetryInterceptor` — включает телеметрию сервера (логирование, метрики, трассировку) в зависимости от подключенных модулей и настроек `grpcServer.telemetry`, а также сопоставляет финальный `Status`/исключение при закрытии вызова
- `ContextServerInterceptor` — пробрасывает `Context` Kora в обработку вызова, чтобы он был доступен внутри обработчика
- `CoroutineContextInjectInterceptor` — добавляет поддержку `CoroutineContext` для корутинных обработчиков на `Kotlin` (активен только при наличии `kotlinx-coroutines` в classpath)

Пользовательские бины `ServerInterceptor` из графа приложения добавляются в `NettyServerBuilder` перед стандартными перехватчиками.
Для полной настройки `NettyServerBuilder` используйте [GrpcServerBuilderConfigurer](#builder-configurer).

### Порядок выполнения { #execution-order }

gRPC вызывает перехватчики в **обратном** порядке их регистрации, поэтому последний добавленный перехватчик выполняется первым (самый внешний).
Поскольку Kora регистрирует пользовательские перехватчики первыми, а стандартные — последними, входящий вызов обрабатывается в таком порядке:

```
CoroutineContextInjectInterceptor -> ContextServerInterceptor -> TelemetryInterceptor -> user interceptors -> handler
```

Следствия такого порядка:

- `Context` Kora и `CoroutineContext` Kotlin устанавливаются вокруг ваших перехватчиков и обработчика, поэтому они доступны внутри колбэков слушателя обработчика.
- `TelemetryInterceptor` оборачивает ваши перехватчики и обработчик, поэтому он наблюдает финальный `Status` (включая ошибки, выброшенные или переданные через observer ответа).
- Когда пользовательских перехватчиков несколько, они выполняются в порядке, обратном порядку их регистрации в графе; не полагайтесь на конкретный порядок между ними для корректности.

### Пользовательские { #custom }

Чтобы добавить пользовательский перехватчик, создайте реализацию `ServerInterceptor` с аннотацией `@Component`:

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

### Ограничение области и авторизация { #authorization }

Поскольку перехватчик глобальный, ограничьте его конкретным сервисом или методом, анализируя `call.getMethodDescriptor()`:
`getServiceName()` возвращает имя сервиса (сгенерированную константу `...Grpc.SERVICE_NAME`), а `getFullMethodName()` возвращает `service/method`.

Заголовки запроса поступают в виде [`Metadata`](https://grpc.github.io/grpc-java/javadoc/io/grpc/Metadata.html).
Читайте заголовок с помощью `Metadata.Key`, а отклоняйте вызов, закрывая его с помощью `Status` и возвращая пустой слушатель, чтобы обработчик никогда не вызывался.
Пример ниже применяет авторизацию по API-ключу только к одному сервису:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class ApiKeyServerInterceptor implements ServerInterceptor {

        private static final Metadata.Key<String> AUTHORIZATION =
            Metadata.Key.of("authorization", Metadata.ASCII_STRING_MARSHALLER); //(1)!

        @Override
        public <ReqT, RespT> ServerCall.Listener<ReqT> interceptCall(ServerCall<ReqT, RespT> call,
                                                                     Metadata headers,
                                                                     ServerCallHandler<ReqT, RespT> next) {
            if (!UserServiceGrpc.SERVICE_NAME.equals(call.getMethodDescriptor().getServiceName())) { //(2)!
                return next.startCall(call, headers);
            }

            var apiKey = headers.get(AUTHORIZATION); //(3)!
            if (apiKey == null || !apiKey.equals("secret")) {
                call.close(Status.UNAUTHENTICATED.withDescription("Invalid API key"), new Metadata()); //(4)!
                return new ServerCall.Listener<>() {}; //(5)!
            }

            return next.startCall(call, headers);
        }
    }
    ```

    1. `Metadata.Key` для чтения заголовка `authorization` как ASCII-строки
    2. Применяет перехватчик только к `UserService`; другие сервисы проходят без изменений
    3. Читает значение заголовка из `Metadata` запроса
    4. Отклоняет вызов со статусом `UNAUTHENTICATED`
    5. Возвращает пустой слушатель, чтобы обработчик никогда не вызывался

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ApiKeyServerInterceptor : ServerInterceptor {

        override fun <ReqT : Any?, RespT : Any?> interceptCall(
            call: ServerCall<ReqT, RespT>,
            headers: Metadata,
            next: ServerCallHandler<ReqT, RespT>
        ): ServerCall.Listener<ReqT> {
            if (UserServiceGrpc.SERVICE_NAME != call.methodDescriptor.serviceName) { //(2)!
                return next.startCall(call, headers)
            }

            val apiKey = headers.get(AUTHORIZATION) //(3)!
            if (apiKey != "secret") {
                call.close(Status.UNAUTHENTICATED.withDescription("Invalid API key"), Metadata()) //(4)!
                return object : ServerCall.Listener<ReqT>() {} //(5)!
            }

            return next.startCall(call, headers)
        }

        companion object {
            private val AUTHORIZATION: Metadata.Key<String> =
                Metadata.Key.of("authorization", Metadata.ASCII_STRING_MARSHALLER) //(1)!
        }
    }
    ```

    1. `Metadata.Key` для чтения заголовка `authorization` как ASCII-строки
    2. Применяет перехватчик только к `UserService`; другие сервисы проходят без изменений
    3. Читает значение заголовка из `Metadata` запроса
    4. Отклоняет вызов со статусом `UNAUTHENTICATED`
    5. Возвращает пустой слушатель, чтобы обработчик никогда не вызывался

## Жизненный цикл и готовность { #lifecycle }

Сервером управляет компонент `GrpcNettyServer`, который создается как компонент [`@Root`](container.md#root-component)
и следует [жизненному циклу приложения](container.md#component-lifecycle):

- При запуске он создает и стартует сервер `Netty` на настроенном `port`. Если порт уже занят, запуск завершается с понятной ошибкой.
- При выключении он выполняет [штатное завершение](container.md#graceful-shutdown): перестает принимать новые вызовы и ждет до `shutdownWait` завершения выполняющихся вызовов, затем принудительно завершает оставшиеся вызовы.

`GrpcNettyServer` также реализует [пробу готовности](probes.md): сервер сообщает о **неготовности** во время запуска или выключения
и о **готовности** только во время работы. В развертывании `Kubernetes` это позволяет пробе готовности отражать реальное состояние сервера и сливать трафик во время штатного завершения.

## Телеметрия { #telemetry }

Наблюдаемость сервера обеспечивается `TelemetryInterceptor` через фасад `GrpcServerTelemetry` и настраивается в [`grpcServer.telemetry`](#configuration).
Метрики описаны в разделе [Справочник метрик](metrics.md#grpc-server).

Каждая часть телеметрии — это заменяемый компонент: значения по умолчанию регистрируются как компоненты по умолчанию, поэтому предоставление собственного `@Component` переопределяет их:

- `GrpcServerTelemetry` — агрегирующий фасад телеметрии (`createContext`, возвращающий контекст с `sendMessage`/`receiveMessage`/`close`)
- `GrpcServerLogger` — логирование вызовов (`logBegin`/`logEnd`/`logSendMessage`/`logReceiveMessage`); по умолчанию используется `Slf4jGrpcServerLogger`
- `GrpcServerTracer` — спаны трассировки вокруг вызовов
- `GrpcServerMetricsFactory` — сбор метрик по каждому вызову

Например, чтобы полностью настроить логирование, зарегистрируйте `@Component`, реализующий `GrpcServerLogger`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface GrpcServerLogger {

        boolean isEnabled();

        void logBegin(ServerCall<?, ?> call, Metadata headers, String serviceName, String methodName);

        void logEnd(String serviceName, String methodName, @Nullable Status status, @Nullable Throwable exception, long processingTime);

        void logSendMessage(String serviceName, String methodName, Object message);

        void logReceiveMessage(String serviceName, String methodName, Object message);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface GrpcServerLogger {

        fun isEnabled(): Boolean

        fun logBegin(call: ServerCall<*, *>, headers: Metadata, serviceName: String, methodName: String)

        fun logEnd(serviceName: String, methodName: String, status: Status?, exception: Throwable?, processingTime: Long)

        fun logSendMessage(serviceName: String, methodName: String, message: Any)

        fun logReceiveMessage(serviceName: String, methodName: String, message: Any)
    }
    ```

## Рефлексия { #reflection }

Поддерживается [`gRPC Server Reflection`](https://github.com/grpc/grpc/blob/master/doc/server-reflection.md), которая предоставляет информацию о доступных `gRPC-сервисах` на сервере.
Рефлексия помогает клиентам и инструментам формировать запросы `RPC` во время выполнения без предварительно скомпилированной информации о сервисах.
Например, ее использует `gRPC CLI`, который может исследовать описания `proto` сервера и отправлять тестовые вызовы `RPC`.
`gRPC Server Reflection` поддерживается только для сервисов на основе `proto`.

Подробнее о `gRPC Server Reflection` можно узнать в [руководстве grpc-java](https://github.com/grpc/grpc-java/blob/master/documentation/server-reflection-tutorial.md#enable-server-reflection).

### Зависимость { #dependency-2 }

Необходимо дополнительно добавить зависимость [`gRPC Server Reflection`](https://mvnrepository.com/artifact/io.grpc/grpc-services).

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

Также необходимо включить сервис `gRPC Server Reflection` в конфигурации.
Kora добавляет его на сервер только при наличии в приложении класса `io.grpc.protobuf.services.ProtoReflectionService`, поэтому одной конфигурации без зависимости недостаточно.

===! ":material-code-json: `Hocon`"

    ```javascript
    grpcServer {
        reflectionEnabled = false //(1)!
    }
    ```

    1. Включает сервис `gRPC Server Reflection` (по умолчанию: `false`).

=== ":simple-yaml: `YAML`"

    ```yaml
    grpcServer:
      reflectionEnabled: false #(1)!
    ```

    1. Включает сервис `gRPC Server Reflection` (по умолчанию: `false`).

### Использование { #reflection-usage }

При включенной рефлексии инструменты вроде [`grpcurl`](https://github.com/fullstorydev/grpcurl) могут обнаруживать сервисы и отправлять вызовы `RPC` без предварительно скомпилированного клиента.
Для сервера, слушающего порт `8090`:

```bash
grpcurl -plaintext localhost:8090 list #(1)!
grpcurl -plaintext localhost:8090 describe ru.tinkoff.kora.generated.grpc.UserService #(2)!
grpcurl -plaintext -d '{"name": "Bob", "code": "123"}' \
    localhost:8090 ru.tinkoff.kora.generated.grpc.UserService/createUser #(3)!
```

1. Выводит список сервисов, предоставляемых сервером
2. Описывает сервис и его методы
3. Отправляет унарный `RPC`; `-plaintext` используется, потому что у сервера из примера нет `TLS`

## Телеметрия { #telemetry }

gRPC Server использует контракт телеметрии для логирования, метрик и трассировки вызовов.
Конфигурация телеметрии (секция `telemetry { logging / metrics / tracing }`) описана в разделе [Конфигурация](#configuration).
Точки расширения находятся в `ru.tinkoff.kora.grpc.server.common.telemetry`.

Для каждого gRPC-вызова создаётся `GrpcServerTelemetry.GrpcServerTelemetryContext`, который закрывается по завершении вызова.
Вызов описывается через параметры обработчика телеметрии, включая сервис, метод, статус ответа и длительность.

Фабрика по умолчанию `DefaultGrpcServerTelemetryFactory` объединяет три фабрики:
- `GrpcServerLoggerFactory` строит `GrpcServerLogger` для логирования начала/конца вызова;
- `GrpcServerMetricsFactory` строит `GrpcServerMetrics` для записи метрик вызовов;
- `GrpcServerTracerFactory` строит `GrpcServerTracer` для распределённой трассировки.

Метрики и трассировка описаны в разделе [Справочник метрик](metrics.md#grpc-server).
