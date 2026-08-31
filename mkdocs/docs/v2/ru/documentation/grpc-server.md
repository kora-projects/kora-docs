---
description: "Explains the Kora gRPC server: protobuf Gradle plugin setup, GrpcServerConfig options, unary and streaming StreamObserver handlers, io.grpc.Status error handling, the virtual-thread execution model, ServerInterceptor interceptors and their order, TLS through ServerCredentials, builder tuning through Configurer, lifecycle and readiness, telemetry and reflection. Use when working with GrpcServerModule, GrpcServerConfig, Configurer, ServerCredentials, ServerInterceptor, StreamObserver, reflectionEnabled, Server Reflection."
agent:
  use_when: "Use this file for Kora docs or implementation questions about the Kora gRPC server: protobuf Gradle plugin setup, server configuration, unary and streaming handlers, io.grpc.Status error handling, the per-connection virtual-thread execution model, ServerInterceptor interceptors and their execution order, scoping and metadata authorization, TLS, lifecycle and readiness, telemetry and reflection; key triggers include GrpcServerModule, GrpcServerConfig, Configurer, ForwardingServerBuilder, ServerCredentials, ServerInterceptor, StreamObserver, reflectionEnabled, Server Reflection. Note: the server runs on the gRPC OkHttp transport, handlers are synchronous StreamObserver-based generated stubs, and interceptors are global io.grpc.ServerInterceptor components only — there is no @GrpcService or @InterceptWith annotation in this module."
---

Модуль запускает `gRPC-сервер` на основе [`grpc-java`](https://grpc.io/docs/languages/java/basics/) и подключает к нему обработчики из графа приложения.
Обработчик — это `BindableService`, обычно класс, который наследует сгенерированный `...ImplBase` и реализует унарные или потоковые методы `RPC`.

Kora строит сервер на транспорте `gRPC OkHttp`, добавляет сервисы и реализации `ServerInterceptor` из графа вместе со своим перехватчиком телеметрии,
управляет жизненным циклом сервера и участвует в проверках готовности приложения.
Если параметров конфигурации недостаточно, итоговый билдер можно дополнительно настроить в коде через компонент `Configurer`.

Если нужен пошаговый разбор перед справочным описанием, смотрите [gRPC-сервер](../guides/grpc-server.md) и [продвинутый gRPC-сервер](../guides/grpc-server-advanced.md).

## Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:grpc-server"
    implementation "io.grpc:grpc-protobuf:1.83.1"
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
    implementation("io.koraframework:grpc-server")
    implementation("io.grpc:grpc-protobuf:1.83.1")
    implementation("javax.annotation:javax.annotation-api:1.3.2")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : GrpcServerModule
    ```

Вместе с `io.koraframework:grpc-server` приходит рантайм `gRPC` версии `1.83.1`.
Все остальные артефакты `io.grpc` — `grpc-protobuf`, `grpc-services` и всё, что подключается в тестовой области, — должны быть той же версии, смотрите [Тестирование](#testing).

### Плагин { #plugin }

Код для `gRPC-сервера` генерируется с помощью [gradle-плагина protobuf](https://github.com/google/protobuf-gradle-plugin).

===! ":fontawesome-brands-java: `Java`"

    Плагин в `build.gradle`:
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
        main {
            java {
                srcDirs "build/generated/source/proto/main/grpc"
                srcDirs "build/generated/source/proto/main/java"
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Плагин в `build.gradle.kts`:
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
            all().forEach { task -> task.plugins { id("grpc") } }
        }
    }

    sourceSets.main {
        java.srcDir(layout.buildDirectory.dir("generated/source/proto/main/grpc"))
        java.srcDir(layout.buildDirectory.dir("generated/source/proto/main/java"))
    }
    ```

Плагин генерирует классы на `Java`, поэтому в проекте на `Kotlin` сгенерированные исходники всё равно подключаются к набору исходников `java`.

## Конфигурация { #configuration }

Обычно нужно задать только `port`; все остальные параметры имеют значения по умолчанию.
Минимальная конфигурация, которая привязывает порт и включает логирование:

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

Основные параметры конфигурации:

===! ":material-code-json: `Hocon`"

    ```javascript
    grpcServer {
        port = 8090 //(1)!
        maxMessageSize = "4MiB" //(2)!
        reflectionEnabled = false //(3)!
    }
    ```

    1. Порт `gRPC-сервера` (по умолчанию: `8090`).
    2. Максимальный размер входящего сообщения (по умолчанию: `4MiB`).
    3. Включает сервис [`gRPC Server Reflection`](#reflection) (по умолчанию: `false`).

=== ":simple-yaml: `YAML`"

    ```yaml
    grpcServer:
      port: 8090 #(1)!
      maxMessageSize: "4MiB" #(2)!
      reflectionEnabled: false #(3)!
    ```

    1. Порт `gRPC-сервера` (по умолчанию: `8090`).
    2. Максимальный размер входящего сообщения (по умолчанию: `4MiB`).
    3. Включает сервис [`gRPC Server Reflection`](#reflection) (по умолчанию: `false`).

??? note "Полная конфигурация"

    Пример полной конфигурации, описанной в `GrpcServerConfig`:

    ===! ":material-code-json: `Hocon`"

        ```javascript
        grpcServer {
            port = 8090 //(1)!
            maxMessageSize = "4MiB" //(2)!
            reflectionEnabled = false //(3)!
            shutdownWait = "30s" //(4)!
            maxConnectionAge = "5m" //(5)!
            maxConnectionAgeGrace = "30s" //(6)!
            keepAliveTime = "30s" //(7)!
            keepAliveTimeout = "10s" //(8)!
            telemetry {
                logging {
                    enabled = false //(9)!
                }
                metrics {
                    enabled = false //(10)!
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
        4. Время ожидания завершения выполняющихся вызовов перед выключением сервера при [штатном завершении](container.md#graceful-shutdown) (по умолчанию: `30s`).
        5. Максимальное время жизни соединения, после которого соединение штатно завершается (опционально, без значения по умолчанию). К значению добавляется случайное отклонение +/-10%.
        6. Дополнительное время на штатное завершение соединения после достижения максимального времени жизни (опционально, без значения по умолчанию). Вызовы `RPC`, которые не успевают завершиться, отменяются, чтобы соединение могло закрыться.
        7. Интервал между кадрами `PING` (опционально, без значения по умолчанию).
        8. Тайм-аут подтверждения кадра `PING` (опционально, без значения по умолчанию). Если подтверждение не получено за это время, соединение закрывается.
        9. Включает логирование модуля (по умолчанию: `false`).
        10. Включает метрики модуля (по умолчанию: `false`). Метрики пишутся только если модуль [метрик](metrics.md) также предоставляет `MeterRegistry`.
        11. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрики [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
        12. Теги метрик (по умолчанию: `{}`).
        13. Включает трассировку модуля (по умолчанию: `true`). Спаны экспортируются только если модуль [трассировки](tracing.md) также предоставляет `Tracer`.
        14. Атрибуты трассировки (по умолчанию: `{}`).

    === ":simple-yaml: `YAML`"

        ```yaml
        grpcServer:
          port: 8090 #(1)!
          maxMessageSize: "4MiB" #(2)!
          reflectionEnabled: false #(3)!
          shutdownWait: "30s" #(4)!
          maxConnectionAge: "5m" #(5)!
          maxConnectionAgeGrace: "30s" #(6)!
          keepAliveTime: "30s" #(7)!
          keepAliveTimeout: "10s" #(8)!
          telemetry:
            logging:
              enabled: false #(9)!
            metrics:
              enabled: false #(10)!
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
        4. Время ожидания завершения выполняющихся вызовов перед выключением сервера при [штатном завершении](container.md#graceful-shutdown) (по умолчанию: `30s`).
        5. Максимальное время жизни соединения, после которого соединение штатно завершается (опционально, без значения по умолчанию). К значению добавляется случайное отклонение +/-10%.
        6. Дополнительное время на штатное завершение соединения после достижения максимального времени жизни (опционально, без значения по умолчанию). Вызовы `RPC`, которые не успевают завершиться, отменяются, чтобы соединение могло закрыться.
        7. Интервал между кадрами `PING` (опционально, без значения по умолчанию).
        8. Тайм-аут подтверждения кадра `PING` (опционально, без значения по умолчанию). Если подтверждение не получено за это время, соединение закрывается.
        9. Включает логирование модуля (по умолчанию: `false`).
        10. Включает метрики модуля (по умолчанию: `false`). Метрики пишутся только если модуль [метрик](metrics.md) также предоставляет `MeterRegistry`.
        11. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрики [Timer](https://docs.micrometer.io/micrometer/reference/concepts/timers.html) (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
        12. Теги метрик (по умолчанию: `{}`).
        13. Включает трассировку модуля (по умолчанию: `true`). Спаны экспортируются только если модуль [трассировки](tracing.md) также предоставляет `Tracer`.
        14. Атрибуты трассировки (по умолчанию: `{}`).

Всё, что не покрыто конфигурацией, доступно через [настройку в коде](#builder-configurer).

### Настройка в коде { #builder-configurer }

Если параметров конфигурации недостаточно, зарегистрируйте компонент `Configurer<ForwardingServerBuilder<?>>` и донастройте билдер сервера в коде.
Компонент вызывается последним: после применения конфигурации и после того, как добавлены сервисы, пользовательские реализации `ServerInterceptor` и стандартный перехватчик.
Сервер собирается из того билдера, который вернул компонент.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MyGrpcServerConfigurer implements Configurer<ForwardingServerBuilder<?>> {

        @Override
        public ForwardingServerBuilder<?> configure(ForwardingServerBuilder<?> builder) {
            builder.maxInboundMetadataSize(16 * 1024); //(1)!
            builder.handshakeTimeout(10, TimeUnit.SECONDS);

            if (builder instanceof OkHttpServerBuilder okHttpBuilder) { //(2)!
                okHttpBuilder.permitKeepAliveWithoutCalls(true);
                okHttpBuilder.maxConcurrentCallsPerConnection(200);
            }

            return builder; //(3)!
        }
    }
    ```

    1. Опции, объявленные в `io.grpc.ServerBuilder`, доступны прямо на делегирующем билдере
    2. Настройки конкретного транспорта требуют конкретного билдера: Kora поднимает сервер на транспорте `gRPC OkHttp`, поэтому это `io.grpc.okhttp.OkHttpServerBuilder`
    3. Билдеры `gRPC` мутируют себя и возвращают самих себя, поэтому наружу отдаётся тот же экземпляр

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyGrpcServerConfigurer : Configurer<ForwardingServerBuilder<*>> {

        override fun configure(builder: ForwardingServerBuilder<*>): ForwardingServerBuilder<*> {
            builder.maxInboundMetadataSize(16 * 1024) //(1)!
            builder.handshakeTimeout(10, TimeUnit.SECONDS)

            if (builder is OkHttpServerBuilder) { //(2)!
                builder.permitKeepAliveWithoutCalls(true)
                builder.maxConcurrentCallsPerConnection(200)
            }

            return builder //(3)!
        }
    }
    ```

    1. Опции, объявленные в `io.grpc.ServerBuilder`, доступны прямо на делегирующем билдере
    2. Настройки конкретного транспорта требуют конкретного билдера: Kora поднимает сервер на транспорте `gRPC OkHttp`, поэтому это `io.grpc.okhttp.OkHttpServerBuilder`
    3. Билдеры `gRPC` мутируют себя и возвращают самих себя, поэтому наружу отдаётся тот же экземпляр

Метрики модуля описаны в разделе [Справочник метрик](metrics.md#grpc-server).

### Защита транспорта { #tls }

По умолчанию сервер принимает соединения без шифрования: если в графе нет `io.grpc.ServerCredentials`, Kora использует `InsecureServerCredentials`.
Чтобы терминировать `TLS` на самом сервере, предоставьте `ServerCredentials` компонентом — например, через `io.grpc.TlsServerCredentials`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends GrpcServerModule {

        default ServerCredentials grpcServerCredentials() throws IOException { //(1)!
            return TlsServerCredentials.create(
                new File("/etc/certs/server.crt"), //(2)!
                new File("/etc/certs/server.key"));
        }
    }
    ```

    1. Фабричный метод графа приложения: учётные данные подхватываются при создании билдера `gRPC-сервера`
    2. Цепочка сертификатов в формате `PEM` и незашифрованный приватный ключ `PKCS#8`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : GrpcServerModule {

        fun grpcServerCredentials(): ServerCredentials { //(1)!
            return TlsServerCredentials.create(
                File("/etc/certs/server.crt"), //(2)!
                File("/etc/certs/server.key"))
        }
    }
    ```

    1. Фабричный метод графа приложения: учётные данные подхватываются при создании билдера `gRPC-сервера`
    2. Цепочка сертификатов в формате `PEM` и незашифрованный приватный ключ `PKCS#8`

Для взаимного `TLS` и собственного хранилища доверенных сертификатов собирайте учётные данные через `TlsServerCredentials.newBuilder()`.

## Обработчики { #handlers }

Обработчик — это класс, который наследует сгенерированный `...ImplBase` и регистрируется в графе приложения с помощью аннотации `@Component`.
Класс `...ImplBase` создается из контракта `proto` с помощью [gradle-плагина protobuf](#plugin); вы переопределяете его методы `RPC`, чтобы реализовать поведение сервера.
Обычные компоненты Kora, такие как сервисы и репозитории, можно внедрить в обработчик через его конструктор.

Рассмотрим контракт `proto` с единственным унарным методом:

```protobuf title="src/main/proto/message.proto"
syntax = "proto3";

package io.koraframework.generated.grpc;

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
и соответствующим образом записывает логирование, метрики и трассировку.

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

    Сгенерированный метод возвращает `void` (или `StreamObserver` для запроса), поэтому результаты доставляются через колбэки `StreamObserver`,
    а не через возвращаемое значение.

=== ":simple-kotlin: `Kotlin`"

    Под `Req` и `Resp` подразумеваются сгенерированные типы сообщений запроса и ответа.

    - Унарный: `myMethod(request: Req, responseObserver: StreamObserver<Resp>)`
    - Серверная потоковая передача: `myMethod(request: Req, responseObserver: StreamObserver<Resp>)` (несколько `onNext`, один `onCompleted`)
    - Клиентская потоковая передача: `myMethod(responseObserver: StreamObserver<Resp>): StreamObserver<Req>`
    - Двунаправленная потоковая передача: `myMethod(responseObserver: StreamObserver<Resp>): StreamObserver<Req>`

    Сгенерированный метод возвращает `Unit` (или `StreamObserver` для запроса), поэтому результаты доставляются через колбэки `StreamObserver`,
    а не через возвращаемое значение.

Обработчики блокирующие: из метода обработчика можно напрямую обращаться к базе данных, [HTTP-клиенту](http-client.md) или [gRPC-клиенту](grpc-client.md).
Асинхронных, реактивных и `suspend`-сигнатур обработчиков нет — сервер выполняет обработчики на виртуальных потоках, смотрите [Модель выполнения](#execution-model).

### Модель выполнения { #execution-model }

Каждому клиентскому соединению выделяется собственный однопоточный исполнитель на виртуальном потоке с именем `grpc-<адрес клиента>`.
Исполнитель создается, когда транспорт готов, и останавливается, когда транспорт завершается.

- Все колбэки перехватчиков и обработчиков для вызовов одного соединения выполняются на этом единственном виртуальном потоке — по одному за раз и в порядке поступления.
- Блокироваться внутри обработчика безопасно: несущий поток освобождается. Но блокировка задерживает остальные вызовы **того же** соединения. Клиенту, которому нужны параллельные вызовы, следует открыть несколько соединений.
- На время каждого колбэка Kora привязывает к этому потоку свой [`MDC`](logging-slf4j.md) и контекст `OpenTelemetry`, поэтому контекст логирования доступен внутри обработчика.

## Перехватчики { #interceptors }

[`io.grpc.ServerInterceptor`](https://grpc.github.io/grpc-java/javadoc/io/grpc/ServerInterceptor.html) обрабатывает вызов до того, как он будет передан в `gRPC-сервис`.
Перехватчики подходят для сквозной логики: логирования, авторизации, трассировки, работы с `Metadata` и сопоставления ошибок.

В отличие от [HTTP-сервера](http-server.md#interceptors), модуль gRPC-сервера **не** имеет аннотаций `@GrpcService` или `@InterceptWith`:
каждый `ServerInterceptor`, зарегистрированный как `@Component`, применяется **глобально** ко всем сервисам на сервере.
Чтобы ограничить перехватчик одним сервисом или методом, анализируйте вызов во время выполнения — смотрите [Ограничение области и авторизация](#authorization).

### Стандартные { #default }

При запуске сервера Kora добавляет один стандартный перехватчик:

- `TelemetryInterceptor` — открывает `GrpcServerObservation` на каждый вызов, привязывает текущее наблюдение и контекст `OpenTelemetry` на время вызова и по его закрытию записывает логирование, метрики и трассировку в зависимости от подключенных модулей и настроек `grpcServer.telemetry`

Пользовательские компоненты `ServerInterceptor` из графа приложения добавляются в билдер перед стандартным перехватчиком.
Для полной настройки билдера используйте [настройку в коде](#builder-configurer).

Компоненты перехватчиков читаются через обновляемый граф, поэтому перехватчик, пересозданный при обновлении конфигурации, подхватывается без перезапуска сервера.

### Порядок выполнения { #execution-order }

gRPC вызывает перехватчики в **обратном** порядке их регистрации, поэтому последний добавленный перехватчик выполняется первым (самый внешний).
Поскольку Kora регистрирует пользовательские перехватчики первыми, а стандартный — последним, входящий вызов обрабатывается в таком порядке:

```
TelemetryInterceptor -> user interceptors -> handler
```

Следствия такого порядка:

- `TelemetryInterceptor` оборачивает ваши перехватчики и обработчик, поэтому он наблюдает финальный `Status` — включая ошибки, выброшенные вашими перехватчиками или переданные через observer ответа.
- Текущее наблюдение и контекст `OpenTelemetry` устанавливаются вокруг ваших перехватчиков и обработчика, поэтому они доступны внутри колбэков слушателя обработчика.
- Когда пользовательских перехватчиков несколько, они выполняются в порядке, обратном порядку их регистрации в графе; не полагайтесь на конкретный порядок между ними для корректности.

### Пользовательские { #custom }

Чтобы добавить пользовательский перехватчик, создайте реализацию `ServerInterceptor` с аннотацией `@Component`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class LoggingServerInterceptor implements ServerInterceptor {

        private static final Logger logger = LoggerFactory.getLogger(LoggingServerInterceptor.class);

        @Override
        public <ReqT, RespT> ServerCall.Listener<ReqT> interceptCall(ServerCall<ReqT, RespT> call,
                                                                     Metadata headers,
                                                                     ServerCallHandler<ReqT, RespT> next) {
            logger.info("Incoming gRPC call: {}", call.getMethodDescriptor().getFullMethodName()); //(1)!

            return next.startCall(call, headers); //(2)!
        }
    }
    ```

    1. `getFullMethodName()` возвращает `service/method` для перехватываемого вызова
    2. Передает вызов дальше; если вернуться, не вызвав `startCall`, вызов придется закрыть самостоятельно

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class LoggingServerInterceptor : ServerInterceptor {

        private val logger = LoggerFactory.getLogger(LoggingServerInterceptor::class.java)

        override fun <ReqT : Any, RespT : Any> interceptCall(
            call: ServerCall<ReqT, RespT>,
            headers: Metadata,
            next: ServerCallHandler<ReqT, RespT>
        ): ServerCall.Listener<ReqT> {
            logger.info("Incoming gRPC call: {}", call.methodDescriptor.fullMethodName) //(1)!

            return next.startCall(call, headers) //(2)!
        }
    }
    ```

    1. `fullMethodName` возвращает `service/method` для перехватываемого вызова
    2. Передает вызов дальше; если вернуться, не вызвав `startCall`, вызов придется закрыть самостоятельно

### Ограничение области и авторизация { #authorization }

Поскольку перехватчик глобальный, ограничьте его конкретным сервисом или методом, анализируя `call.getMethodDescriptor()`:
`getServiceName()` возвращает имя сервиса (сгенерированную константу `...Grpc.SERVICE_NAME`), а `getFullMethodName()` возвращает `service/method`.

Заголовки запроса поступают в виде [`Metadata`](https://grpc.github.io/grpc-java/javadoc/io/grpc/Metadata.html).
Читайте заголовок с помощью `Metadata.Key`, а отклоняйте вызов, закрывая его с помощью `Status` и возвращая пустой слушатель, чтобы обработчик никогда не вызывался.
Пример ниже применяет авторизацию по API-ключу только к одному сервису:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @ConfigSource("auth.apiKey")
    public interface ApiKeyConfig {

        String value();
    }
    ```

    ```java
    @Component
    public final class ApiKeyServerInterceptor implements ServerInterceptor {

        private static final Metadata.Key<String> AUTHORIZATION =
            Metadata.Key.of("authorization", Metadata.ASCII_STRING_MARSHALLER); //(1)!

        private final ApiKeyConfig config;

        public ApiKeyServerInterceptor(ApiKeyConfig config) {
            this.config = config;
        }

        @Override
        public <ReqT, RespT> ServerCall.Listener<ReqT> interceptCall(ServerCall<ReqT, RespT> call,
                                                                     Metadata headers,
                                                                     ServerCallHandler<ReqT, RespT> next) {
            if (!UserServiceGrpc.SERVICE_NAME.equals(call.getMethodDescriptor().getServiceName())) { //(2)!
                return next.startCall(call, headers);
            }

            var apiKey = headers.get(AUTHORIZATION); //(3)!
            if (!config.value().equals(apiKey)) {
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
    @ConfigSource("auth.apiKey")
    interface ApiKeyConfig {

        fun value(): String
    }
    ```

    ```kotlin
    @Component
    class ApiKeyServerInterceptor(private val config: ApiKeyConfig) : ServerInterceptor {

        override fun <ReqT : Any, RespT : Any> interceptCall(
            call: ServerCall<ReqT, RespT>,
            headers: Metadata,
            next: ServerCallHandler<ReqT, RespT>
        ): ServerCall.Listener<ReqT> {
            if (UserServiceGrpc.SERVICE_NAME != call.methodDescriptor.serviceName) { //(2)!
                return next.startCall(call, headers)
            }

            val apiKey = headers.get(AUTHORIZATION) //(3)!
            if (config.value() != apiKey) {
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

Сервером управляет компонент `GrpcServer`, который создается как компонент [`@Root`](container.md#root-component)
и следует [жизненному циклу приложения](container.md#component-lifecycle):

- При запуске он собирает и стартует сервер на настроенном `port`. Если порт уже занят, запуск завершается ошибкой
  `gRPC server failed to start on port '8090': port is already in use; stop the other process or configure a different port`.
- При выключении он выполняет [штатное завершение](container.md#graceful-shutdown): перестает принимать новые вызовы и ждет до `shutdownWait` завершения выполняющихся вызовов, затем принудительно завершает оставшиеся вызовы.

`GrpcServer` также реализует [пробу готовности](probes.md): сервер сообщает о **неготовности** во время запуска или выключения
и о **готовности** только во время работы. В развертывании `Kubernetes` это позволяет пробе готовности отражать реальное состояние сервера и сливать трафик во время штатного завершения.

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
    implementation "io.grpc:grpc-services:1.83.1"
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.grpc:grpc-services:1.83.1")
    ```

### Конфигурация { #configuration-2 }

Также необходимо включить сервис `gRPC Server Reflection` в конфигурации.
Kora добавляет его на сервер только при наличии в приложении класса `io.grpc.protobuf.services.ProtoReflectionServiceV1`, поэтому одной конфигурации без зависимости недостаточно.

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
grpcurl -plaintext localhost:8090 describe io.koraframework.generated.grpc.UserService #(2)!
grpcurl -plaintext -d '{"name": "Bob", "code": "123"}' \
    localhost:8090 io.koraframework.generated.grpc.UserService/createUser #(3)!
```

1. Выводит список сервисов, предоставляемых сервером
2. Описывает сервис и его методы
3. Отправляет унарный `RPC`; `-plaintext` используется, потому что у сервера из примера нет `TLS`

## Телеметрия { #telemetry }

Наблюдаемость сервера обеспечивается `TelemetryInterceptor` через фасад `GrpcServerTelemetry` и настраивается в [`grpcServer.telemetry`](#configuration).
Точки расширения находятся в `io.koraframework.grpc.server.telemetry`.

На каждый gRPC-вызов создается `GrpcServerObservation`: он собирает заголовки, отправленные и полученные сообщения, финальный `Status`
и ошибку, а закрывается по завершении вызова.
Фабрика `GrpcServerTelemetryFactory` по умолчанию зарегистрирована как `@DefaultComponent`, поэтому ее можно заменить целиком; либо отдельные части
можно переопределить, зарегистрировав компонентом наследника `DefaultGrpcServerLoggerFactory`, `DefaultGrpcServerMetricsFactory` или `DefaultGrpcServerBodyConverter`.
Если логирование, метрики и трассировка выключены все сразу, фабрика возвращает пустую реализацию телеметрии и вызовы не несут накладных расходов на наблюдаемость.

В логах, метриках и спанах сервер представляется именем `kora-grpc`.

### Логирование { #telemetry-logging }

Логирование вызовов включается через `grpcServer.telemetry.logging.enabled` и пишется двумя логгерами:

- `io.koraframework.grpc.server.GrpcServer.request` — `GrpcCall received` со структурированным полем `grpcRequest`
- `io.koraframework.grpc.server.GrpcServer.response` — `GrpcCall responded` со структурированным полем `grpcResponse`

Структурированные поля содержат `serverName`, `serverPort`, `serviceName` и `operation` (`service/method`);
в ответе дополнительно есть `processingTime` в миллисекундах, код `Status` в поле `status` и, для неудачного вызова, `exceptionType`.
Вызов, завершившийся ошибкой, логируется на уровне `WARN` с приложенным исключением, успешный — на уровне `INFO`.

Уровень логгера добавляет детализацию сверх этого: `DEBUG` на логгере запроса добавляет `Metadata` запроса в поле `headers`,
а `TRACE` добавляет тело сообщения, отрендеренное через `DefaultGrpcServerBodyConverter`.

===! ":material-code-json: `Hocon`"

    ```javascript
    logging.levels {
        "io.koraframework.grpc.server.GrpcServer.request" = "DEBUG"
        "io.koraframework.grpc.server.GrpcServer.response" = "TRACE"
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    logging:
      levels:
        "io.koraframework.grpc.server.GrpcServer.request": "DEBUG"
        "io.koraframework.grpc.server.GrpcServer.response": "TRACE"
    ```

### Метрики { #telemetry-metrics }

Метрикам нужен `grpcServer.telemetry.metrics.enabled` **и** `MeterRegistry`, который предоставляет модуль [метрик](metrics.md).
Модуль пишет единственный таймер `rpc.server.duration` с корзинами из `grpcServer.telemetry.metrics.slo` и тегами
`server.name`, `server.port`, `rpc.system` (всегда `grpc`), `rpc.service`, `rpc.method` и `rpc.grpc.status_code`,
плюс всё, что объявлено в `grpcServer.telemetry.metrics.tags`.

Метрики описаны в разделе [Справочник метрик](metrics.md#grpc-server).

### Трассировка { #telemetry-tracing }

Трассировке нужен `grpcServer.telemetry.tracing.enabled` **и** `Tracer`, который предоставляет модуль [трассировки](tracing.md).
На каждый вызов создается спан вида `SERVER` с именем `<service>/<method>`; его родитель извлекается из `Metadata` запроса
пропагатором `W3C Trace Context`, поэтому трасса, начатая вызывающей стороной, продолжается на сервере.

Спан несет атрибуты `server.port`, `server.name`, `rpc.system`, `rpc.service`, `rpc.method` и `network.peer.address`,
плюс всё, что объявлено в `grpcServer.telemetry.tracing.attributes`; при закрытии добавляется `rpc.grpc.status_code`.
Каждое отправленное и полученное сообщение добавляет событие `rpc.message` с атрибутом `rpc.message.type`.
Статус `Status`, отличный от OK, или исключение переводят статус спана в `ERROR`.

## Тестирование { #testing }

`gRPC-сервер` занимает настоящий порт, поэтому [`@KoraAppTest`](junit5.md) поднимает его, а тест обращается к нему через обычный `ManagedChannel`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(Application.class)
    class UserServiceTests {

        @Test
        void createUser() {
            var channel = ManagedChannelBuilder.forAddress("localhost", 8090) //(1)!
                .usePlaintext()
                .build();

            try {
                var stub = UserServiceGrpc.newBlockingStub(channel); //(2)!
                var response = stub.createUser(Message.RequestEvent.newBuilder()
                    .setName("Bob")
                    .setCode("123")
                    .build());

                assertFalse(response.getId().isEmpty());
            } finally {
                channel.shutdownNow();
            }
        }
    }
    ```

    1. Порт, на котором поднят сервер, то есть `grpcServer.port` из тестовой конфигурации
    2. Блокирующая заглушка, сгенерированная из контракта `proto`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(Application::class)
    class UserServiceTests {

        @Test
        fun createUser() {
            val channel = ManagedChannelBuilder.forAddress("localhost", 8090) //(1)!
                .usePlaintext()
                .build()

            try {
                val stub = UserServiceGrpc.newBlockingStub(channel) //(2)!
                val response = stub.createUser(
                    Message.RequestEvent.newBuilder()
                        .setName("Bob")
                        .setCode("123")
                        .build()
                )

                assertFalse(response.id.isEmpty)
            } finally {
                channel.shutdownNow()
            }
        }
    }
    ```

    1. Порт, на котором поднят сервер, то есть `grpcServer.port` из тестовой конфигурации
    2. Блокирующая заглушка, сгенерированная из контракта `proto`

**Согласование версий**: клиентской стороне теста нужен транспорт `gRPC` в тестовом classpath, и его версия должна совпадать с рантаймом `gRPC`,
который приходит с `io.koraframework:grpc-server`, — `1.83.1`.
Закрепленная более старая версия компилируется без замечаний и падает только в рантайме с
`AbstractMethodError: ... does not define or inherit an implementation of the resolved method 'buildClientTransportServers(List, MetricRecorder)'`.

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    testImplementation "io.koraframework:test-junit5"
    testImplementation "io.grpc:grpc-netty:1.83.1"
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    testImplementation("io.koraframework:test-junit5")
    testImplementation("io.grpc:grpc-netty:1.83.1")
    ```
