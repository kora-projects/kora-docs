---
search:
  exclude: true
title: Продвинутый gRPC-клиент с Kora
summary: Build a streaming gRPC client with generated stubs, metadata auth, and client interceptors
tags: grpc-client, streaming, interceptors, authentication, protobuf
---

# Продвинутый gRPC-клиент с Kora { #advanced-grpc-client-kora }

В этом руководстве рассматриваются продвинутые приемы построения gRPC-клиента в Kora. Вы разберете серверные потоки, клиентские потоки, двунаправленные потоки, авторизацию на основе метаданных и
клиентские перехватчики для сгенерированных заглушек. Вы также увидите, как асинхронные наблюдатели, сигналы завершения и ошибки жизненного цикла потока отличают потоковые клиенты от обычного кода в
стиле «запрос-ответ».

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java gRPC Client Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-grpc-client-advanced-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin gRPC Client Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-grpc-client-advanced-app).

## Что вы создадите { #youll-build }

Вы расширите приложение gRPC-клиента и добавите:

- потоковый клиентский сервис для `UserStreamingService`
- серверные потоковые вызовы для `GetAllUsers`
- клиентские потоковые вызовы для `CreateUsers`
- двунаправленные потоковые вызовы для `UpdateUsers`
- HTTP-маршруты запуска, которые позволяют удобно выполнять каждый потоковый сценарий локально
- клиентский перехватчик журналирования
- клиентский перехватчик авторизации, который передает ключ API через метаданные gRPC
- быстрые внутрипроцессные тесты, которые проверяют потоковое поведение без сервера, запущенного вручную

## Что вам понадобится { #youll-need }

- JDK 17 или новее
- Gradle 7+
- текстовый редактор или среда разработки
- запущенный продвинутый gRPC-сервер для проверок во время выполнения

## Требования { #prerequisites }

!!! note "Обязательно: пройдите руководство по продвинутому gRPC-серверу"

    Это руководство предполагает, что вы уже прошли **[gRPC-клиент с Kora](grpc-client.md)** и **[Продвинутый gRPC-сервер с Kora](grpc-server-advanced.md)**, а также понимаете сгенерированные унарные заглушки, контракты protobuf и то, как Kora внедряет зависимости gRPC-клиента.

    Если вы еще не прошли руководство по продвинутому gRPC-серверу, сначала сделайте это, потому что здесь используется тот же потоковый контракт, а основное внимание уделяется потоковым вызовам на стороне клиента.

## Обзор { #overview }

Как и руководство по продвинутому серверу, руководство по продвинутому клиенту построено вокруг разделения ответственности.

Мы **не** перегружаем исходный унарный клиент всеми продвинутыми возможностями.

Вместо этого:

- базовый клиент остается сосредоточен на унарном CRUD через `UserService`
- продвинутый клиент сосредоточен на потоках через `UserStreamingService`

Такой подход делает оба руководства проще для изучения и соответствует устройству сопутствующих приложений.

На стороне клиента продвинутые возможности gRPC сильнее влияют на поток управления, чем на внедрение зависимостей. Kora по-прежнему предоставляет настроенный gRPC-клиент и компоненты приложения.
Сгенерированные заглушки по-прежнему выполняют RPC-вызовы. Меняется то, как код сервиса управляет временем жизни вызовов, потоками запросов, наблюдателями ответов, метаданными и ошибками.

В этом руководстве эти задачи остаются явными:

- потоковые сервисы оборачивают сгенерированные асинхронные заглушки, а не раскрывают их напрямую
- клиентские перехватчики добавляют сквозное поведение к исходящим вызовам
- авторизация через метаданные настраивается рядом с границей клиента
- HTTP-точки запуска являются только локальным способом проверить потоковый клиент

У продвинутого клиента также другая модель отказов по сравнению с унарным клиентом. В унарном вызове отказ обычно означает, что один запрос завершился ошибкой до получения одного ответа. В потоковом
вызове ошибка может произойти после того, как часть сообщений уже была отправлена или получена. Поэтому сервис-обертка должна рассматривать завершение потока как часть проектирования API, а не как
деталь, о которой вспоминают в конце.

Именно поэтому руководству вводит явные клиентские методы для каждой формы потоковой передачи:

- серверный поток ориентирован на чтение: один вызов, много полученных ответов
- клиентский поток ориентирован на запись: много отправленных запросов, один итоговый ответ
- двунаправленный поток похож на диалог: отправка и получение происходят независимо

Сгенерированная асинхронная заглушка дает большие возможности, но обычно это не та граница, которую стоит распространять по остальной части приложения. Она раскрывает механику обратных вызовов:
наблюдателей и сигналы завершения. Сервисная обертка Kora превращает эту механику в более компактный API, который можно вызывать из контроллеров, заданий или других сервисов, не разнося gRPC-код с
обратными вызовами по всему приложению.

Метаданные и перехватчики относятся к той же границе. Они полезны для авторизации, трассировки, идентификаторов запросов и журналирования, но подключать их нужно рядом со сгенерированным клиентом. Так
бизнес-код остается сосредоточен на выполняемой операции, а не на том, как каждый RPC-вызов оформляется при передаче по сети.

### Как потоки меняют клиент { #streams-change-client }

Унарные gRPC-вызовы выглядят приятно просто:

- создать один запрос
- вызвать один метод
- получить один ответ

Потоковая передача меняет эту модель мышления.

### Серверный поток { #server-stream }

При серверном потоке клиент отправляет один запрос и получает много ответов.

Значит, клиентский код должен учитывать:

- перебор потока сообщений
- частичный прогресс
- момент завершения потока

### Клиентский поток меняет создание данных { #client-stream-changes-data }

При клиентском потоке клиент больше не отправляет один полностью готовый объект запроса.

Вместо этого он постепенно отправляет несколько сообщений в вызов и только позже получает итоговый ответ.

### Двунаправленный поток { #bidirectional-stream }

При двунаправленном потоке клиент и сервер могут продолжать обмениваться сообщениями в рамках одного RPC.

Значит, клиент должен обрабатывать:

- асинхронную отправку запросов
- асинхронную обработку ответов
- жизненный цикл потока и его завершение

## API в Protobuf { #protobuf-api }

Продвинутый клиент повторно использует ровно тот же ориентированный на потоки `.proto`-контракт из руководства по продвинутому серверу.

??? example "Protobuf-контракт"

    ```protobuf title="src/main/proto/user_service.proto"
    syntax = "proto3";
    
    package ru.tinkoff.kora.guide.grpcserver.advanced;
    option java_multiple_files = true;
    
    import "google/protobuf/empty.proto";
    import "google/protobuf/timestamp.proto";
    
    service UserService {
      rpc CreateUser(CreateUserRequest) returns (UserResponse) {}
      rpc GetUser(GetUserRequest) returns (UserResponse) {}
      rpc GetUsers(GetUsersRequest) returns (GetUsersResponse) {}
      rpc UpdateUser(UpdateUserRequestUnary) returns (UserResponse) {}
      rpc DeleteUser(DeleteUserRequest) returns (google.protobuf.Empty) {}
    }
    
    service UserStreamingService {
      rpc GetAllUsers(google.protobuf.Empty) returns (stream UserResponse) {}
      rpc CreateUsers(stream CreateUserRequest) returns (CreateUsersResponse) {}
      rpc UpdateUsers(stream UpdateUserRequest) returns (stream UserResponse) {}
    }
    
    message CreateUserRequest {
      string name = 1;
      string email = 2;
    }
    
    message GetUserRequest {
      string user_id = 1;
    }
    
    message GetUsersRequest {
      int32 page = 1;
      int32 size = 2;
      string sort = 3;
    }
    
    message GetUsersResponse {
      repeated UserResponse users = 1;
    }
    
    message UpdateUserRequestUnary {
      string user_id = 1;
      string name = 2;
      string email = 3;
    }
    
    message DeleteUserRequest {
      string user_id = 1;
    }
    
    message UpdateUserRequest {
      string user_id = 1;
      string name = 2;
      string email = 3;
    }
    
    message CreateUsersResponse {
      int32 created_count = 1;
      repeated string user_ids = 2;
    }
    
    message UserResponse {
      string id = 1;
      string name = 2;
      string email = 3;
      google.protobuf.Timestamp created_at = 4;
    }
    ```

Снова обратите внимание на важное решение в моделировании:

- унарный `UserService` все еще присутствует в контракте
- работа продвинутого клиента сосредоточена на отдельном `UserStreamingService`

## Зависимости { #dependencies }

Модуль продвинутого клиента использует тот же основной клиентский набор, что и базовый клиент.

===! ":fontawesome-brands-java: `Java`"

    Обновите `build.gradle`:

    ```groovy title="build.gradle"
    plugins {
        id "application"
        id "com.google.protobuf" version "0.9.4"
    }

    dependencies {
        compileOnly "javax.annotation:javax.annotation-api:1.3.2"
        annotationProcessor "ru.tinkoff.kora:annotation-processors"

        implementation "ru.tinkoff.kora:config-hocon"
        implementation "ru.tinkoff.kora:grpc-client"
        implementation "ru.tinkoff.kora:http-server-undertow"
        implementation "ru.tinkoff.kora:json-module"
        implementation "ru.tinkoff.kora:logging-logback"
        implementation "io.grpc:grpc-protobuf:1.74.0"

        testRuntimeOnly platform("org.junit:junit-bom:$junitVersion")
        testRuntimeOnly "org.junit.platform:junit-platform-launcher"
        testImplementation platform("org.junit:junit-bom:$junitVersion")
        testImplementation "io.grpc:grpc-inprocess:1.74.0"
        testImplementation "org.junit.jupiter:junit-jupiter"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите `build.gradle.kts`:

    ```kotlin title="build.gradle.kts"
    import com.google.protobuf.gradle.id

    plugins {
        id("org.jetbrains.kotlin.jvm")
        id("com.google.devtools.ksp")
        id("application")
        id("com.google.protobuf") version "0.9.4"
    }

    dependencies {
        compileOnly("javax.annotation:javax.annotation-api:1.3.2")
        ksp("ru.tinkoff.kora:symbol-processors")

        implementation("ru.tinkoff.kora:config-hocon")
        implementation("ru.tinkoff.kora:grpc-client")
        implementation("ru.tinkoff.kora:http-server-undertow")
        implementation("ru.tinkoff.kora:json-module")
        implementation("ru.tinkoff.kora:logging-logback")
        implementation("io.grpc:grpc-protobuf:1.74.0")

        testRuntimeOnly(platform("org.junit:junit-bom:${property("junitVersion")}"))
        testRuntimeOnly("org.junit.platform:junit-platform-launcher")
        testImplementation(platform("org.junit:junit-bom:${property("junitVersion")}"))
        testImplementation("io.grpc:grpc-inprocess:1.74.0")
        testImplementation("org.junit.jupiter:junit-jupiter")
    }
    ```

## Генерация кода { #code-generation }

Настройка Gradle для protobuf остается по смыслу такой же, как в руководстве по базовому клиенту:

===! ":fontawesome-brands-java: `Java`"

    Добавьте в `build.gradle`:

    ```groovy title="build.gradle"
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
        main {
            java {
                srcDirs "build/generated/source/proto/main/grpc"
                srcDirs "build/generated/source/proto/main/java"
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Добавьте в `build.gradle.kts`:

    ```kotlin title="build.gradle.kts"
    protobuf {
        protoc { artifact = "com.google.protobuf:protoc:3.25.3" }
        plugins {
            id("grpc") { artifact = "io.grpc:protoc-gen-grpc-java:1.74.0" }
        }
        generateProtoTasks {
            all().forEach { task ->
                task.plugins { id("grpc") }
            }
        }
    }

    sourceSets {
        main {
            java {
                srcDirs("build/generated/source/proto/main/grpc", "build/generated/source/proto/main/java")
            }
        }
    }
    ```

Меняется не сама генерация кода, а типы сгенерированных заглушек, которые мы используем:

- блокирующие заглушки для чтения серверных потоков
- асинхронные заглушки для клиентских и двунаправленных потоков

## Конфигурация { #config }

Продвинутый сервер защищает потоковый сервис с помощью ключа API в метаданных gRPC, поэтому продвинутый клиент должен знать две вещи:

- где находится сервер
- какой ключ API нужно отправлять

Полное описание настроек смотрите в разделах [HTTP-сервер](../documentation/http-server.md), [Конфигурация](../documentation/config.md), [gRPC-клиент](../documentation/grpc-client.md)
и [Журналирование SLF4J](../documentation/logging-slf4j.md).

===! ":material-code-json: `Hocon`"

    ```javascript title="src/main/resources/application.conf"
    httpServer {
      publicApiHttpPort = 8081 //(1)!
      privateApiHttpPort = 8086 //(2)!
      telemetry.logging.enabled = true //(3)!
    }

    auth.apiKey.value = "test-api-key" //(4)!
    auth.apiKey.value = ${?GRPC_STREAMING_API_KEY} //(5)!

    grpcClient {
      UserStreamingService {
        url = "http://localhost:8092" //(6)!
        url = ${?GRPC_STREAMING_SERVER_URL} //(7)!
        telemetry.logging.enabled = true //(8)!
      }
    }

    logging {
      levels {
        "ROOT": "INFO" //(9)!
        "ru.tinkoff.kora": "INFO" //(10)!
        "ru.tinkoff.kora.guide.grpcclient.advanced": "INFO" //(11)!
      }
    }
    ```

    1. Общедоступный HTTP-порт по умолчанию, который используют конечные точки приложения.
    2. Служебный HTTP-порт по умолчанию для проб, метрик и конечных точек управления.
    3. Включает возможность для этого раздела конфигурации.
    4. Настроенное значение, которое использует компонент руководства.
    5. Настроенное значение, которое использует компонент руководства. Необязательное переопределение через `GRPC_STREAMING_API_KEY`.
    6. Базовый URL, который использует настроенный клиент.
    7. Базовый URL, который использует настроенный клиент. Необязательное переопределение через `GRPC_STREAMING_SERVER_URL`.
    8. Включает возможность для этого раздела конфигурации.
    9. Уровень журналирования для `ROOT`.
    10. Уровень журналирования для `ru.tinkoff.kora`.
    11. Уровень журналирования для `ru.tinkoff.kora.guide.grpcclient.advanced`.

=== ":simple-yaml: `YAML`"

    ```yaml title="src/main/resources/application.yaml"
    httpServer:
      publicApiHttpPort: 8081 #(1)!
      privateApiHttpPort: 8086 #(2)!
      telemetry:
        logging:
          enabled: true #(3)!
    auth:
      apiKey:
        value: ${?GRPC_STREAMING_API_KEY:"test-api-key"} #(4)!
    grpcClient:
      UserStreamingService:
        url: ${?GRPC_STREAMING_SERVER_URL:"http://localhost:8092"} #(5)!
        telemetry:
          logging:
            enabled: true #(6)!
    logging:
      levels:
        ROOT: "INFO" #(7)!
        "ru.tinkoff.kora": "INFO" #(8)!
        "ru.tinkoff.kora.guide.grpcclient.advanced": "INFO" #(9)!
    ```

    1. Общедоступный HTTP-порт по умолчанию, который используют конечные точки приложения.
    2. Служебный HTTP-порт по умолчанию для проб, метрик и конечных точек управления.
    3. Включает возможность для этого раздела конфигурации.
    4. Настроенное значение, которое использует компонент руководства. Использует показанное значение по умолчанию и позволяет `GRPC_STREAMING_API_KEY` переопределить его.
    5. Базовый URL, который использует настроенный клиент. Использует показанное значение по умолчанию и позволяет `GRPC_STREAMING_SERVER_URL` переопределить его.
    6. Включает возможность для этого раздела конфигурации.
    7. Уровень журналирования для `ROOT`.
    8. Уровень журналирования для `ru.tinkoff.kora`.
    9. Уровень журналирования для `ru.tinkoff.kora.guide.grpcclient.advanced`.

Как и в руководстве по базовому клиенту, локальный URL использует `http://...`, чтобы gRPC-клиент работал в режиме без шифрования для этой демонстрационной настройки.

## Клиентский перехватчик { #client-interceptor }

Подробнее о клиентских gRPC-перехватчиках и metadata смотрите в разделе [gRPC Client: перехватчики](../documentation/grpc-client.md#interceptors).

Клиентские перехватчики являются клиентским аналогом промежуточного слоя транспорта. Они полезны для задач, которые должны выполняться для исходящих вызовов в одном месте:

- журналирование
- авторизация
- предельные сроки
- трассировка

Продвинутый клиент добавляет простой перехватчик журналирования:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/grpcclient/advanced/grpc/LoggingInterceptor.java"
    package ru.tinkoff.kora.guide.grpcclient.advanced.grpc;

    import io.grpc.CallOptions;
    import io.grpc.Channel;
    import io.grpc.ClientCall;
    import io.grpc.ClientInterceptor;
    import io.grpc.MethodDescriptor;
    import org.slf4j.Logger;
    import org.slf4j.LoggerFactory;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.Tag;
    import ru.tinkoff.kora.guide.grpcserver.advanced.UserStreamingServiceGrpc;

    @Tag(UserStreamingServiceGrpc.class)
    @Component
    public final class LoggingInterceptor implements ClientInterceptor {

        private static final Logger logger = LoggerFactory.getLogger(LoggingInterceptor.class);

        @Override
        public <ReqT, RespT> ClientCall<ReqT, RespT> interceptCall(
                MethodDescriptor<ReqT, RespT> method,
                CallOptions callOptions,
                Channel next) {
            logger.info("Calling gRPC method {}", method.getFullMethodName());
            return next.newCall(method, callOptions);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/grpcclient/advanced/grpc/LoggingInterceptor.kt"
    package ru.tinkoff.kora.guide.grpcclient.advanced.grpc

    import io.grpc.*
    import org.slf4j.LoggerFactory
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.Tag
    import ru.tinkoff.kora.guide.grpcserver.advanced.UserStreamingServiceGrpc

    @Tag(UserStreamingServiceGrpc::class)
    @Component
    class LoggingInterceptor : ClientInterceptor {

        private val logger = LoggerFactory.getLogger(LoggingInterceptor::class.java)

        override fun <ReqT : Any?, RespT : Any?> interceptCall(
            method: MethodDescriptor<ReqT, RespT>,
            callOptions: CallOptions,
            next: Channel
        ): ClientCall<ReqT, RespT> {
            logger.info("Calling gRPC method {}", method.fullMethodName)
            return next.newCall(method, callOptions)
        }
    }
    ```

`@Tag(UserStreamingServiceGrpc.class)` важен: он ограничивает действие этого перехватчика клиентом продвинутого потокового сервиса.

## Перехватчик авторизации { #authorization-interceptor }

Теперь сделаем так, чтобы клиент автоматически отправлял ключ API, который ожидает продвинутый сервер.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/grpcclient/advanced/grpc/UserStreamingAuthInterceptor.java"
    package ru.tinkoff.kora.guide.grpcclient.advanced.grpc;

    import io.grpc.CallOptions;
    import io.grpc.Channel;
    import io.grpc.ClientCall;
    import io.grpc.ClientInterceptor;
    import io.grpc.ForwardingClientCall;
    import io.grpc.Metadata;
    import io.grpc.MethodDescriptor;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.Tag;
    import ru.tinkoff.kora.guide.grpcserver.advanced.UserStreamingServiceGrpc;

    @Tag(UserStreamingServiceGrpc.class)
    @Component
    public final class UserStreamingAuthInterceptor implements ClientInterceptor {

        private static final Metadata.Key<String> AUTHORIZATION_HEADER =
                Metadata.Key.of("authorization", Metadata.ASCII_STRING_MARSHALLER);

        private final UserStreamingAuthConfig authConfig;

        public UserStreamingAuthInterceptor(UserStreamingAuthConfig authConfig) {
            this.authConfig = authConfig;
        }

        @Override
        public <ReqT, RespT> ClientCall<ReqT, RespT> interceptCall(
                MethodDescriptor<ReqT, RespT> method,
                CallOptions callOptions,
                Channel next) {
            return new ForwardingClientCall.SimpleForwardingClientCall<>(next.newCall(method, callOptions)) {
                @Override
                public void start(Listener<RespT> responseListener, Metadata headers) {
                    headers.put(AUTHORIZATION_HEADER, authConfig.value());
                    super.start(responseListener, headers);
                }
            };
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/grpcclient/advanced/grpc/UserStreamingAuthInterceptor.kt"
    package ru.tinkoff.kora.guide.grpcclient.advanced.grpc

    import io.grpc.*
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.Tag
    import ru.tinkoff.kora.guide.grpcserver.advanced.UserStreamingServiceGrpc

    @Tag(UserStreamingServiceGrpc::class)
    @Component
    class UserStreamingAuthInterceptor(
        private val authConfig: UserStreamingAuthConfig
    ) : ClientInterceptor {

        override fun <ReqT : Any?, RespT : Any?> interceptCall(
            method: MethodDescriptor<ReqT, RespT>,
            callOptions: CallOptions,
            next: Channel
        ): ClientCall<ReqT, RespT> {
            return object :
                ForwardingClientCall.SimpleForwardingClientCall<ReqT, RespT>(next.newCall(method, callOptions)) {
                override fun start(responseListener: Listener<RespT>, headers: Metadata) {
                    headers.put(AUTHORIZATION_HEADER, authConfig.value())
                    super.start(responseListener, headers)
                }
            }
        }

        companion object {
            private val AUTHORIZATION_HEADER: Metadata.Key<String> =
                Metadata.Key.of("authorization", Metadata.ASCII_STRING_MARSHALLER)
        }
    }
    ```

Это gRPC-аналог автоматического добавления заголовков авторизации в продвинутом HTTP-клиенте.

## Потоковый клиентский { #streaming-client }

Теперь можно обернуть сгенерированные потоковые заглушки в небольшой клиентский сервис.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/grpcclient/advanced/service/UserStreamingClientService.java"
    package ru.tinkoff.kora.guide.grpcclient.advanced.service;

    import com.google.protobuf.Empty;
    import io.grpc.stub.StreamObserver;
    import java.time.LocalDateTime;
    import java.time.ZoneOffset;
    import java.util.ArrayList;
    import java.util.List;
    import java.util.concurrent.CompletableFuture;
    import java.util.concurrent.CopyOnWriteArrayList;
    import java.util.concurrent.TimeUnit;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.grpcclient.advanced.dto.UserRequest;
    import ru.tinkoff.kora.guide.grpcclient.advanced.dto.UserResponse;
    import ru.tinkoff.kora.guide.grpcclient.advanced.dto.UserUpdateRequest;
    import ru.tinkoff.kora.guide.grpcserver.advanced.CreateUserRequest;
    import ru.tinkoff.kora.guide.grpcserver.advanced.CreateUsersResponse;
    import ru.tinkoff.kora.guide.grpcserver.advanced.UpdateUserRequest;
    import ru.tinkoff.kora.guide.grpcserver.advanced.UserStreamingServiceGrpc;

    @Component
    public final class UserStreamingClientService {

        private final UserStreamingServiceGrpc.UserStreamingServiceBlockingStub blockingStub;
        private final UserStreamingServiceGrpc.UserStreamingServiceStub asyncStub;

        public UserStreamingClientService(
                UserStreamingServiceGrpc.UserStreamingServiceBlockingStub blockingStub,
                UserStreamingServiceGrpc.UserStreamingServiceStub asyncStub) {
            this.blockingStub = blockingStub;
            this.asyncStub = asyncStub;
        }

        public CreateUsersResult createUsers(List<UserRequest> requests) {
            var future = new CompletableFuture<CreateUsersResult>();
            var responseObserver = new StreamObserver<CreateUsersResponse>() {
                @Override
                public void onNext(CreateUsersResponse value) {
                    future.complete(new CreateUsersResult(value.getCreatedCount(), List.copyOf(value.getUserIdsList())));
                }

                @Override
                public void onError(Throwable t) {
                    future.completeExceptionally(t);
                }

                @Override
                public void onCompleted() {
                }
            };

            var requestObserver = this.asyncStub.createUsers(responseObserver);
            try {
                for (var request : requests) {
                    requestObserver.onNext(CreateUserRequest.newBuilder()
                            .setName(request.name())
                            .setEmail(request.email())
                            .build());
                }
                requestObserver.onCompleted();
                return future.get(5, TimeUnit.SECONDS);
            } catch (Exception e) {
                requestObserver.onError(e);
                throw new RuntimeException("Failed to create users over gRPC streaming", e);
            }
        }

        public List<UserResponse> getAllUsers() {
            var users = new ArrayList<UserResponse>();
            var iterator = this.blockingStub.getAllUsers(Empty.getDefaultInstance());
            iterator.forEachRemaining(user -> users.add(toDto(user)));
            return users;
        }

        public List<UserResponse> updateUsers(List<UserUpdateRequest> updates) {
            var future = new CompletableFuture<List<UserResponse>>();
            var responses = new CopyOnWriteArrayList<UserResponse>();
            var responseObserver = new StreamObserver<ru.tinkoff.kora.guide.grpcserver.advanced.UserResponse>() {
                @Override
                public void onNext(ru.tinkoff.kora.guide.grpcserver.advanced.UserResponse value) {
                    responses.add(toDto(value));
                }

                @Override
                public void onError(Throwable t) {
                    future.completeExceptionally(t);
                }

                @Override
                public void onCompleted() {
                    future.complete(List.copyOf(responses));
                }
            };

            var requestObserver = this.asyncStub.updateUsers(responseObserver);
            try {
                for (var update : updates) {
                    requestObserver.onNext(UpdateUserRequest.newBuilder()
                            .setUserId(update.userId())
                            .setName(update.name())
                            .setEmail(update.email())
                            .build());
                }
                requestObserver.onCompleted();
                return future.get(5, TimeUnit.SECONDS);
            } catch (Exception e) {
                requestObserver.onError(e);
                throw new RuntimeException("Failed to update users over gRPC streaming", e);
            }
        }

        private UserResponse toDto(ru.tinkoff.kora.guide.grpcserver.advanced.UserResponse response) {
            return new UserResponse(
                    response.getId(),
                    response.getName(),
                    response.getEmail(),
                    LocalDateTime.ofEpochSecond(
                            response.getCreatedAt().getSeconds(),
                            response.getCreatedAt().getNanos(),
                            ZoneOffset.UTC));
        }

        public record CreateUsersResult(int createdCount, List<String> userIds) {}
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/grpcclient/advanced/service/UserStreamingClientService.kt"
    package ru.tinkoff.kora.guide.grpcclient.advanced.service

    import com.google.protobuf.Empty
    import io.grpc.stub.StreamObserver
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.grpcclient.advanced.dto.UserRequest
    import ru.tinkoff.kora.guide.grpcclient.advanced.dto.UserResponse
    import ru.tinkoff.kora.guide.grpcclient.advanced.dto.UserUpdateRequest
    import ru.tinkoff.kora.guide.grpcserver.advanced.CreateUserRequest
    import ru.tinkoff.kora.guide.grpcserver.advanced.CreateUsersResponse
    import ru.tinkoff.kora.guide.grpcserver.advanced.UpdateUserRequest
    import ru.tinkoff.kora.guide.grpcserver.advanced.UserStreamingServiceGrpc
    import java.time.LocalDateTime
    import java.time.ZoneOffset
    import java.util.concurrent.CompletableFuture
    import java.util.concurrent.CopyOnWriteArrayList
    import java.util.concurrent.TimeUnit

    @Component
    class UserStreamingClientService(
        private val blockingStub: UserStreamingServiceGrpc.UserStreamingServiceBlockingStub,
        private val asyncStub: UserStreamingServiceGrpc.UserStreamingServiceStub
    ) {

        fun createUsers(requests: List<UserRequest>): CreateUsersResult {
            val future = CompletableFuture<CreateUsersResult>()
            val responseObserver = object : StreamObserver<CreateUsersResponse> {
                override fun onNext(value: CreateUsersResponse) {
                    future.complete(CreateUsersResult(value.createdCount, value.userIdsList.toList()))
                }

                override fun onError(t: Throwable) {
                    future.completeExceptionally(t)
                }

                override fun onCompleted() = Unit
            }

            val requestObserver = asyncStub.createUsers(responseObserver)
            try {
                requests.forEach { request ->
                    requestObserver.onNext(
                        CreateUserRequest.newBuilder()
                            .setName(request.name)
                            .setEmail(request.email)
                            .build()
                    )
                }
                requestObserver.onCompleted()
                return future.get(5, TimeUnit.SECONDS)
            } catch (e: Exception) {
                requestObserver.onError(e)
                throw RuntimeException("Failed to create users over gRPC streaming", e)
            }
        }

        fun getAllUsers(): List<UserResponse> {
            val users = mutableListOf<UserResponse>()
            val iterator = blockingStub.getAllUsers(Empty.getDefaultInstance())
            iterator.forEachRemaining { user -> users += toDto(user) }
            return users
        }

        fun updateUsers(updates: List<UserUpdateRequest>): List<UserResponse> {
            val future = CompletableFuture<List<UserResponse>>()
            val responses = CopyOnWriteArrayList<UserResponse>()
            val responseObserver = object : StreamObserver<ru.tinkoff.kora.guide.grpcserver.advanced.UserResponse> {
                override fun onNext(value: ru.tinkoff.kora.guide.grpcserver.advanced.UserResponse) {
                    responses += toDto(value)
                }

                override fun onError(t: Throwable) {
                    future.completeExceptionally(t)
                }

                override fun onCompleted() {
                    future.complete(responses.toList())
                }
            }

            val requestObserver = asyncStub.updateUsers(responseObserver)
            try {
                updates.forEach { update ->
                    requestObserver.onNext(
                        UpdateUserRequest.newBuilder()
                            .setUserId(update.userId)
                            .setName(update.name)
                            .setEmail(update.email)
                            .build()
                    )
                }
                requestObserver.onCompleted()
                return future.get(5, TimeUnit.SECONDS)
            } catch (e: Exception) {
                requestObserver.onError(e)
                throw RuntimeException("Failed to update users over gRPC streaming", e)
            }
        }

        private fun toDto(response: ru.tinkoff.kora.guide.grpcserver.advanced.UserResponse): UserResponse {
            return UserResponse(
                response.id,
                response.name,
                response.email,
                LocalDateTime.ofEpochSecond(response.createdAt.seconds, response.createdAt.nanos, ZoneOffset.UTC)
            )
        }

        data class CreateUsersResult(val createdCount: Int, val userIds: List<String>)
    }
    ```

Этот один сервис теперь показывает все три формы потоковой передачи со стороны клиента.

## Контроллер проверки { #check-controller }

Сопутствующее приложение содержит небольшую вспомогательную конечную точку, которая запускает потоковый клиент.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/grpcclient/advanced/controller/ClientTestController.java"
    package ru.tinkoff.kora.guide.grpcclient.advanced.controller;

    import java.util.List;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.grpcclient.advanced.dto.UserRequest;
    import ru.tinkoff.kora.guide.grpcclient.advanced.dto.UserUpdateRequest;
    import ru.tinkoff.kora.guide.grpcclient.advanced.service.UserStreamingClientService;
    import ru.tinkoff.kora.http.common.HttpMethod;
    import ru.tinkoff.kora.http.common.annotation.HttpRoute;
    import ru.tinkoff.kora.http.server.common.annotation.HttpController;
    import ru.tinkoff.kora.json.common.annotation.Json;

    @Component
    @HttpController
    public final class ClientTestController {

        private final UserStreamingClientService userStreamingClientService;

        public ClientTestController(UserStreamingClientService userStreamingClientService) {
            this.userStreamingClientService = userStreamingClientService;
        }

        @HttpRoute(method = HttpMethod.POST, path = "/client/test-all-streaming-endpoints")
        @Json
        public TestResults testAllStreamingEndpoints() {
            try {
                var created = this.userStreamingClientService.createUsers(List.of(
                        new UserRequest("Alice Streaming", "alice-streaming@example.com"),
                        new UserRequest("Bob Streaming", "bob-streaming@example.com")));
                boolean usersCreated = created.createdCount() == 2;

                var streamed = this.userStreamingClientService.getAllUsers();
                boolean usersStreamed = created.userIds().stream()
                        .allMatch(userId -> streamed.stream().anyMatch(user -> user.id().equals(userId)));

                var updated = this.userStreamingClientService.updateUsers(List.of(
                        new UserUpdateRequest(created.userIds().get(0), "Updated Alice Streaming", "updated-alice@example.com"),
                        new UserUpdateRequest(created.userIds().get(1), "Updated Bob Streaming", "updated-bob@example.com")));
                boolean usersUpdated = updated.stream().anyMatch(user -> "Updated Alice Streaming".equals(user.name()))
                        && updated.stream().anyMatch(user -> "Updated Bob Streaming".equals(user.name()));

                boolean allTestsPassed = usersCreated && usersStreamed && usersUpdated;
                return new TestResults(usersCreated, usersStreamed, usersUpdated, allTestsPassed, null);
            } catch (Exception exception) {
                return new TestResults(false, false, false, false, exception.getMessage());
            }
        }

        @Json
        public record TestResults(
                boolean usersCreated,
                boolean usersStreamed,
                boolean usersUpdated,
                boolean allTestsPassed,
                String error) {}
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/grpcclient/advanced/controller/ClientTestController.kt"
    package ru.tinkoff.kora.guide.grpcclient.advanced.controller

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.grpcclient.advanced.dto.UserRequest
    import ru.tinkoff.kora.guide.grpcclient.advanced.dto.UserUpdateRequest
    import ru.tinkoff.kora.guide.grpcclient.advanced.service.UserStreamingClientService
    import ru.tinkoff.kora.http.common.HttpMethod
    import ru.tinkoff.kora.http.common.annotation.HttpRoute
    import ru.tinkoff.kora.http.server.common.annotation.HttpController
    import ru.tinkoff.kora.json.common.annotation.Json

    @Component
    @HttpController
    class ClientTestController(
        private val userStreamingClientService: UserStreamingClientService
    ) {

        @HttpRoute(method = HttpMethod.POST, path = "/client/test-all-streaming-endpoints")
        @Json
        fun testAllStreamingEndpoints(): TestResults {
            return try {
                val created = userStreamingClientService.createUsers(
                    listOf(
                        UserRequest("Alice Streaming", "alice-streaming@example.com"),
                        UserRequest("Bob Streaming", "bob-streaming@example.com")
                    )
                )
                val usersCreated = created.createdCount == 2

                val streamed = userStreamingClientService.getAllUsers()
                val usersStreamed = created.userIds.all { userId -> streamed.any { user -> user.id == userId } }

                val updated = userStreamingClientService.updateUsers(
                    listOf(
                        UserUpdateRequest(created.userIds[0], "Updated Alice Streaming", "updated-alice@example.com"),
                        UserUpdateRequest(created.userIds[1], "Updated Bob Streaming", "updated-bob@example.com")
                    )
                )
                val usersUpdated = updated.any { it.name == "Updated Alice Streaming" } &&
                        updated.any { it.name == "Updated Bob Streaming" }

                val allTestsPassed = usersCreated && usersStreamed && usersUpdated
                TestResults(usersCreated, usersStreamed, usersUpdated, allTestsPassed, null)
            } catch (exception: Exception) {
                TestResults(false, false, false, false, exception.message)
            }
        }

        @Json
        data class TestResults(
            val usersCreated: Boolean,
            val usersStreamed: Boolean,
            val usersUpdated: Boolean,
            val allTestsPassed: Boolean,
            val error: String?
        )
    }
    ```

И снова HTTP-конечная точка является только локальной обвязкой. Настоящая тема руководства находится ниже нее: потоковый gRPC-клиент.

## Запуск приложения { #run-app }

Сначала запустите продвинутый сервер:

```bash
$env:GRPC_STREAMING_API_KEY="test-api-key"
./gradlew run
```

Затем запустите продвинутый клиент:

```bash
$env:GRPC_STREAMING_API_KEY="test-api-key"
./gradlew run
```

Теперь выполните вызов:

```bash
curl -X POST http://localhost:8081/client/test-all-streaming-endpoints
```

Эта одна вспомогательная конечная точка внутри проверяет:

- клиентский поток
- серверный поток
- двунаправленный поток

## Запуск тестов { #testing }

Тесты продвинутого клиента также используют подход с внутрипроцессным gRPC.

Здесь это особенно полезно, потому что позволяет тестам имитировать:

- успешные потоковые взаимодействия
- отклоненные вызовы без ключа API
- поведение перехватчиков

Запустите их командой:

```bash
./gradlew test
```

## Лучшие практики { #best-practices }

- Держите продвинутую потоковую работу в отдельном клиентском сервисе, а не раздувайте унарный клиент.
- Ограничивайте область действия перехватчиков тегами, когда они должны влиять только на один сгенерированный сервис.
- Используйте клиентские перехватчики для авторизации на основе метаданных, а не повторяйте логику заголовков в каждом месте вызова.
- Держите обработку жизненного цикла потока рядом с транспортной границей.
- Предпочитайте внутрипроцессные gRPC-серверы для быстрых тестов потоков на стороне клиента.
- Аннотируйте рукописные DTO с помощью `@Json` только тогда, когда они пересекают HTTP/JSON-границу; сгенерированным protobuf-сообщениям JSON-аннотации не нужны.

## Итоги { #summary }

В этом руководстве вы создали потоковый gRPC-клиент, который отражает руководство по продвинутому серверу.

Важная идея состояла не только в том, «как вызывать потоковые RPC», но и в том, «как чисто организовать клиент»:

- разделить унарные и потоковые задачи
- добавить авторизацию и журналирование через перехватчики
- обернуть сгенерированные заглушки в сфокусированный сервисный слой

## Ключевые понятия { #key-concepts }

- чем продвинутые gRPC-клиенты отличаются от унарных gRPC-клиентов
- как блокирующие и асинхронные заглушки используются для разных потоковых шаблонов
- как клиентские перехватчики добавляют журналирование и авторизацию через метаданные
- как потреблять серверные, клиентские и двунаправленные потоковые методы
- как тестировать продвинутое поведение gRPC-клиента с `InProcessServer`

## Устранение неполадок { #troubleshooting }

**Потоковый вызов никогда не завершается:**

Проверьте, что поток запросов завершается на стороне клиента, а тестовая или серверная реализация отправляет сигналы завершения.

**Вызовы отклоняются как не прошедшие авторизацию:**

Проверьте, что клиент и сервер используют одно и то же значение ключа API, а перехватчик авторизации помечен тегом для сгенерированного потокового клиента.

**Внутрипроцессные тесты проходят, а вызовы во время выполнения завершаются ошибкой:**

Сравните рабочий `application.conf` с настройкой внутрипроцессного теста, особенно узел gRPC, порт и теги перехватчиков.

## Что дальше? { #whats-next }

- [Шаблоны отказоустойчивости](resilient.md), чтобы защищать потоковые и унарные RPC-вызовы от медленных или недоступных сервисов.
- [Наблюдаемость](observability.md), чтобы трассировать вызовы gRPC-клиента, жизненные циклы потоков и поведение перехватчиков.
- [Обмен сообщениями с Kafka](messaging-kafka.md), чтобы сравнить интеграцию в стиле RPC с асинхронной событийной интеграцией.
- [Продвинутый HTTP-клиент](http-client-advanced.md), чтобы сравнить границы продвинутого gRPC-клиента и продвинутого HTTP-клиента.

## Помощь { #help }

Если что-то не работает:

- сравните с [Kora Java gRPC Client Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-grpc-client-advanced-app) и [Kora Kotlin gRPC Client Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-grpc-client-advanced-app)
- проверьте [документацию по gRPC-клиенту](../documentation/grpc-client.md)
- проверьте, что продвинутый сервер из [Продвинутого gRPC-сервера](grpc-server-advanced.md) запущен на порту `8092`
- убедитесь, что клиент и сервер используют одно и то же значение ключа API
