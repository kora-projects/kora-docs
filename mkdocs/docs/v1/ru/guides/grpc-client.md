---
search:
  exclude: true
title: gRPC-клиент с Kora
summary: Build a Kora gRPC client that consumes a unary CRUD service through generated stubs
tags: grpc-client, protobuf, rpc, microservices
---

# gRPC-клиент с Kora { #grpc-client-kora }

Это руководство знакомит с унарными gRPC-клиентами в Kora. В нем показано, как один и тот же контракт `.proto` порождает клиентские заглушки и типы сообщений, как Kora внедряет настроенные
gRPC-клиенты в граф приложения и как небольшой сервис-обертка превращает вызовы заглушки в операции уровня приложения. Вы также увидите, почему gRPC-статусы и сгенерированные построители запросов
делают клиентский код непохожим на декларативные HTTP-клиенты.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java gRPC Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-grpc-client-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin gRPC Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-grpc-client-app).

## Что вы соберете { #youll-build }

Вы соберете отдельное приложение унарного gRPC-клиента, в котором будут:

- тот же контракт `user_service.proto`, который использует сервер
- сгенерированные protobuf-типы запросов и ответов
- внедренная Kora заглушка gRPC-клиента для `UserService`
- небольшой прикладной сервис, который оборачивает `CreateUser`, `GetUser`, `GetUsers`, `UpdateUser` и `DeleteUser`
- HTTP-маршруты для запуска проверок клиента локально
- проверки времени выполнения против запущенного gRPC-сервера

## Что понадобится { #youll-need }

- JDK 17 или новее
- Gradle 7+
- текстовый редактор или среда разработки
- запущенный gRPC-сервер из предыдущего руководства для проверок времени выполнения

## Требования { #prerequisites }

!!! note "Обязательно: пройдите руководство по gRPC-серверу"

    Это руководство предполагает, что вы уже прошли **[gRPC Server with Kora](grpc-server.md)** и **[HTTP-клиент с Kora](http-client.md)**, а также понимаете генерацию protobuf-кода, унарные RPC-методы и разделение на репозиторий/сервис из предыдущих серверных руководств.

    Если вы еще не прошли руководство по gRPC-серверу, сделайте это сначала, потому что здесь переиспользуется тот же protobuf-контракт и показано, как клиент вызывает этот сервер.

## Обзор { #overview }

В руководстве по серверу сгенерированный контракт использовался для реализации сервиса.

В руководстве по клиенту тот же сгенерированный контракт используется для вызова этого сервиса.

Это одно из главных преимуществ gRPC:

- один общий контракт
- сгенерированный код на обеих сторонах
- меньше риска рассогласования транспорта

Клиентская архитектура состоит из трех слоев:

- protobuf-контракт описывает удаленный API
- сгенерированная gRPC-заглушка выполняет транспортный вызов
- ваш компонент Kora оборачивает заглушку в методы, удобные для приложения

Такая обертка важна. Сгенерированные заглушки ориентированы на транспорт: они работают с protobuf-типами запросов и ответов, крайними сроками выполнения, каналами и gRPC-статусами. Прикладной код
обычно хочет видеть более понятные методы вроде `createUser(...)` или `getUsers(...)`, а также обработку ошибок на уровне предметной области. В этом руководстве эта граница остается явной, чтобы
сгенерированный клиент не растекался по всей кодовой базе.

### Чем gRPC-клиент отличается от HTTP { #grpc-client-differs-http }

Рукописный HTTP-клиент обычно начинается с URL и HTTP-обмена. Клиентский код решает, какой путь вызвать, какой метод использовать, какие заголовки отправить, как сериализовать JSON и как
интерпретировать ответ.

- URL-пути
- формы JSON-тел
- разбор ответов
- сопоставление ошибок

gRPC-клиент вместо этого начинается со скомпилированного сервисного контракта. Файл `.proto` определяет доступные RPC-методы и типы сообщений, а сгенерированная заглушка раскрывает эти методы как код.
Клиенту не нужно помнить, что `GetUser` соответствует какой-то форме URL, потому что в прикладном коде не собирается путь ресурса. Сгенерированная заглушка уже знает имя RPC-метода, имя сервиса,
кодировщик сообщений и ожидаемый тип ответа.

Вместо ручной сборки запросов вы обычно:

- строите protobuf-объект запроса
- вызываете сгенерированный метод заглушки
- получаете типизированный protobuf-ответ

Самое сильное отличие не только в двоичной кодировке вместо JSON. Более важное отличие в том, что gRPC переносит соглашение между клиентом и сервером в сгенерированный код:

- имена методов являются частью определения protobuf-сервиса
- поля запросов и ответов являются частью protobuf-сообщений
- отсутствующие или переименованные поля выявляются раньше благодаря компиляции и правилам развития схемы
- клиентский код вызывает сгенерированный API вместо рукописного пути
- серверный код реализует сгенерированные сервисные методы вместо сопоставления аннотаций маршрутов

HTTP-клиенты часто описывают отказ через коды ответа вроде `404`, `409` или `500`. gRPC-клиенты обычно описывают отказ через gRPC-статусы вроде `NOT_FOUND`, `INVALID_ARGUMENT`, `UNAVAILABLE`
или `DEADLINE_EXCEEDED`. Это меняет обработку ошибок: прикладной код обычно ловит исключения статуса gRPC или сопоставляет их на границе обертки, а затем предоставляет остальному сервису поведение,
удобное для предметной области.

Поведение соединений тоже ощущается иначе. HTTP/JSON-клиенты часто рассматривают каждый запрос как независимый вызов ресурса. gRPC-клиенты строятся вокруг каналов и заглушек. Канал представляет
целевой адрес соединения и настройки транспорта, а заглушка является сгенерированным клиентским фасадом для выполнения вызовов. Поэтому руководству оборачивает сгенерированную заглушку
в `UserGrpcClient`: остальной части приложения не нужно знать о каналах, protobuf-построителях или деталях gRPC-статусов.

Это не устраняет необходимость в прикладном коде на стороне клиента. Это меняет его ответственность. Вместо ручной работы с низкоуровневыми транспортными деталями ваш клиентский сервис становится
адаптером между сгенерированными транспортными типами и моделью приложения.

## API в Protobuf { #protobuf-api }

Первая ключевая мысль: клиент **не** придумывает новый контракт.

Он использует тот же `user_service.proto`, что и сервер:

??? example "Protobuf-контракт"

    ```protobuf title="src/main/proto/user_service.proto"
    syntax = "proto3";
    
    package ru.tinkoff.kora.guide.grpcserver;
    option java_multiple_files = true;
    
    import "google/protobuf/empty.proto";
    import "google/protobuf/timestamp.proto";
    
    service UserService {
      rpc CreateUser(CreateUserRequest) returns (UserResponse) {}
      rpc GetUser(GetUserRequest) returns (UserResponse) {}
      rpc GetUsers(GetUsersRequest) returns (GetUsersResponse) {}
      rpc UpdateUser(UpdateUserRequest) returns (UserResponse) {}
      rpc DeleteUser(DeleteUserRequest) returns (google.protobuf.Empty) {}
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
    
    message UpdateUserRequest {
      string user_id = 1;
      string name = 2;
      string email = 3;
    }
    
    message DeleteUserRequest {
      string user_id = 1;
    }
    
    message UserResponse {
      string id = 1;
      string name = 2;
      string email = 3;
      google.protobuf.Timestamp created_at = 4;
    }
    ```

В этом и состоит смысл общего контракта:

- сервер и клиент компилируются против одной транспортной модели
- вам не нужно вручную поддерживать дублирующие схемы запросов и ответов

## Зависимости { #dependencies }

Теперь добавьте клиентский модуль Kora и поддержку protobuf.

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

Главное отличие от серверного модуля:

- `ru.tinkoff.kora:grpc-client` вместо `ru.tinkoff.kora:grpc-server`

## Генерация кода { #code-generation }

Как и на стороне сервера, Gradle должен сгенерировать protobuf-сообщения и gRPC-типы.

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

Это генерирует:

- protobuf-сообщения, например `CreateUserRequest`
- типы клиентских заглушек, например `UserServiceGrpc.UserServiceBlockingStub`

## Модули { #modules }

Подробнее о клиентском gRPC-сервисе, конфигурации и заглушках смотрите в разделе [gRPC Client: Service](../documentation/grpc-client.md#service).

Теперь включите среду выполнения gRPC-клиента Kora в граф приложения.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/grpcclient/Application.java"
    package ru.tinkoff.kora.guide.grpcclient;

    import ru.tinkoff.grpc.client.GrpcClientModule;
    import ru.tinkoff.kora.application.graph.KoraApplication;
    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.config.hocon.HoconConfigModule;
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule;
    import ru.tinkoff.kora.json.module.JsonModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        GrpcClientModule,  // <----- Подключили модуль
        UndertowHttpServerModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/grpcclient/Application.kt"
    package ru.tinkoff.kora.guide.grpcclient

    import ru.tinkoff.grpc.client.GrpcClientModule
    import ru.tinkoff.kora.application.graph.KoraApplication
    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.config.hocon.HoconConfigModule
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule
    import ru.tinkoff.kora.json.module.JsonModule
    import ru.tinkoff.kora.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        GrpcClientModule,  // <----- Подключили модуль
        UndertowHttpServerModule

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

Обратите внимание, что это приложение также включает небольшой модуль HTTP-сервера. Он нужен не потому, что это руководство по HTTP. Он нужен, чтобы сопутствующее приложение могло открыть простую
HTTP-точку входа, которая запускает все операции gRPC
клиента в одном месте.

## Конфигурация { #config }

Добавьте конфигурацию gRPC-клиента:

Полный справочник по конфигурации смотрите в [HTTP-сервер](../documentation/http-server.md), [gRPC Client](../documentation/grpc-client.md) и [журналирование SLF4J](../documentation/logging-slf4j.md).

===! ":material-code-json: `Hocon`"

    ```javascript title="src/main/resources/application.conf"
    httpServer {
      publicApiHttpPort = 8081 //(1)!
      privateApiHttpPort = 8086 //(2)!
      telemetry.logging.enabled = true //(3)!
    }

    grpcClient {
      UserService {
        url = "http://localhost:8090" //(4)!
        url = ${?GRPC_SERVER_URL} //(5)!
        telemetry.logging.enabled = true //(6)!
      }
    }

    logging {
      levels {
        "ROOT": "INFO" //(7)!
        "ru.tinkoff.kora": "INFO" //(8)!
        "ru.tinkoff.kora.guide.grpcclient": "INFO" //(9)!
      }
    }
    ```

    1. Открытый HTTP-порт по умолчанию, который используют прикладные конечные точки.
    2. Закрытый HTTP-порт по умолчанию, который используют пробы, метрики и управляющие конечные точки.
    3. Включает возможность для этого раздела конфигурации.
    4. Базовый URL, который использует настроенный клиент.
    5. Базовый URL, который использует настроенный клиент. Необязательное переопределение из `GRPC_SERVER_URL`.
    6. Включает возможность для этого раздела конфигурации.
    7. Уровень логирования для `ROOT`.
    8. Уровень логирования для `ru.tinkoff.kora`.
    9. Уровень логирования для `ru.tinkoff.kora.guide.grpcclient`.

=== ":simple-yaml: `YAML`"

    ```yaml title="src/main/resources/application.yaml"
    httpServer:
      publicApiHttpPort: 8081 #(1)!
      privateApiHttpPort: 8086 #(2)!
      telemetry:
        logging:
          enabled: true #(3)!
    grpcClient:
      UserService:
        url: ${?GRPC_SERVER_URL:"http://localhost:8090"} #(4)!
        telemetry:
          logging:
            enabled: true #(5)!
    logging:
      levels:
        ROOT: "INFO" #(6)!
        "ru.tinkoff.kora": "INFO" #(7)!
        "ru.tinkoff.kora.guide.grpcclient": "INFO" #(8)!
    ```

    1. Открытый HTTP-порт по умолчанию, который используют прикладные конечные точки.
    2. Закрытый HTTP-порт по умолчанию, который используют пробы, метрики и управляющие конечные точки.
    3. Включает возможность для этого раздела конфигурации.
    4. Базовый URL, который использует настроенный клиент. Использует показанное значение по умолчанию и позволяет `GRPC_SERVER_URL` переопределить его.
    5. Включает возможность для этого раздела конфигурации.
    6. Уровень логирования для `ROOT`.
    7. Уровень логирования для `ru.tinkoff.kora`.
    8. Уровень логирования для `ru.tinkoff.kora.guide.grpcclient`.

Здесь важны две детали:

- клиент настроен в разделе `grpcClient.UserService`
- URL использует `http://...`, поэтому gRPC-клиент Kora работает в открытом режиме без TLS для локальной учебной настройки

## Оберните stub в сервис { #wrap-stub-service }

Сгенерированные заглушки полезны, но приложению обычно все равно нужен небольшой клиентский сервисный слой.

Такой слой может:

- скрывать построение protobuf-запросов
- преобразовывать protobuf-объекты транспорта в DTO приложения
- централизовать использование клиентского транспорта

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/grpcclient/service/UserClientService.java"
    package ru.tinkoff.kora.guide.grpcclient.service;

    import java.time.LocalDateTime;
    import java.time.ZoneOffset;
    import java.util.List;

    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.grpcclient.dto.UserRequest;
    import ru.tinkoff.kora.guide.grpcclient.dto.UserResponse;
    import ru.tinkoff.kora.guide.grpcserver.CreateUserRequest;
    import ru.tinkoff.kora.guide.grpcserver.DeleteUserRequest;
    import ru.tinkoff.kora.guide.grpcserver.GetUserRequest;
    import ru.tinkoff.kora.guide.grpcserver.GetUsersRequest;
    import ru.tinkoff.kora.guide.grpcserver.UpdateUserRequest;
    import ru.tinkoff.kora.guide.grpcserver.UserServiceGrpc;

    @Component
    public final class UserClientService {

        private final UserServiceGrpc.UserServiceBlockingStub userService;

        public UserClientService(UserServiceGrpc.UserServiceBlockingStub userService) {
            this.userService = userService;
        }

        public UserResponse createUser(UserRequest request) {
            return toDto(this.userService.createUser(CreateUserRequest.newBuilder()
                .setName(request.name())
                .setEmail(request.email())
                .build()));
        }

        public UserResponse getUser(String userId) {
            return toDto(this.userService.getUser(GetUserRequest.newBuilder()
                .setUserId(userId)
                .build()));
        }

        public List<UserResponse> getUsers(int page, int size, String sort) {
            return this.userService.getUsers(GetUsersRequest.newBuilder()
                    .setPage(page)
                    .setSize(size)
                    .setSort(sort)
                    .build())
                .getUsersList().stream()
                .map(this::toDto)
                .toList();
        }

        public UserResponse updateUser(String userId, UserRequest request) {
            return toDto(this.userService.updateUser(UpdateUserRequest.newBuilder()
                .setUserId(userId)
                .setName(request.name())
                .setEmail(request.email())
                .build()));
        }

        public void deleteUser(String userId) {
            this.userService.deleteUser(DeleteUserRequest.newBuilder()
                .setUserId(userId)
                .build());
        }

        private UserResponse toDto(ru.tinkoff.kora.guide.grpcserver.UserResponse response) {
            return new UserResponse(
                response.getId(),
                response.getName(),
                response.getEmail(),
                LocalDateTime.ofEpochSecond(
                    response.getCreatedAt().getSeconds(),
                    response.getCreatedAt().getNanos(),
                    ZoneOffset.UTC));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/grpcclient/service/UserClientService.kt"
    package ru.tinkoff.kora.guide.grpcclient.service

    import java.time.LocalDateTime
    import java.time.ZoneOffset
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.grpcclient.dto.UserRequest
    import ru.tinkoff.kora.guide.grpcclient.dto.UserResponse
    import ru.tinkoff.kora.guide.grpcserver.CreateUserRequest
    import ru.tinkoff.kora.guide.grpcserver.DeleteUserRequest
    import ru.tinkoff.kora.guide.grpcserver.GetUserRequest
    import ru.tinkoff.kora.guide.grpcserver.GetUsersRequest
    import ru.tinkoff.kora.guide.grpcserver.UpdateUserRequest
    import ru.tinkoff.kora.guide.grpcserver.UserServiceGrpc

    @Component
    class UserClientService(
        private val userService: UserServiceGrpc.UserServiceBlockingStub
    ) {

        fun createUser(request: UserRequest): UserResponse {
            return toDto(
                userService.createUser(
                    CreateUserRequest.newBuilder()
                        .setName(request.name)
                        .setEmail(request.email)
                        .build()
                )
            )
        }

        fun getUser(userId: String): UserResponse {
            return toDto(userService.getUser(GetUserRequest.newBuilder().setUserId(userId).build()))
        }

        fun getUsers(page: Int, size: Int, sort: String): List<UserResponse> {
            return userService.getUsers(
                GetUsersRequest.newBuilder()
                    .setPage(page)
                    .setSize(size)
                    .setSort(sort)
                    .build()
            ).usersList.map(::toDto)
        }

        fun updateUser(userId: String, request: UserRequest): UserResponse {
            return toDto(
                userService.updateUser(
                    UpdateUserRequest.newBuilder()
                        .setUserId(userId)
                        .setName(request.name)
                        .setEmail(request.email)
                        .build()
                )
            )
        }

        fun deleteUser(userId: String) {
            userService.deleteUser(DeleteUserRequest.newBuilder().setUserId(userId).build())
        }

        private fun toDto(response: ru.tinkoff.kora.guide.grpcserver.UserResponse): UserResponse {
            return UserResponse(
                response.id,
                response.name,
                response.email,
                LocalDateTime.ofEpochSecond(response.createdAt.seconds, response.createdAt.nanos, ZoneOffset.UTC)
            )
        }
    }
    ```

Главная мысль здесь такая же, как во многих других руководствах: сгенерированный транспортный код полезен, но остальная часть приложения все равно должна потреблять небольшую и читаемую абстракцию.

## Контроллер проверки { #check-controller }

Сопутствующее приложение содержит маленький HTTP-контроллер, который вызывает gRPC-клиент и возвращает сводку.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/grpcclient/controller/ClientTestController.java"
    package ru.tinkoff.kora.guide.grpcclient.controller;

    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.grpcclient.dto.UserRequest;
    import ru.tinkoff.kora.guide.grpcclient.service.UserClientService;
    import ru.tinkoff.kora.http.common.HttpMethod;
    import ru.tinkoff.kora.http.common.annotation.HttpRoute;
    import ru.tinkoff.kora.http.server.common.annotation.HttpController;
    import ru.tinkoff.kora.json.common.annotation.Json;

    @Component
    @HttpController
    public final class ClientTestController {

        private final UserClientService userClientService;

        public ClientTestController(UserClientService userClientService) {
            this.userClientService = userClientService;
        }

        @HttpRoute(method = HttpMethod.POST, path = "/client/test-all-user-endpoints")
        @Json
        public TestResults testAllUserEndpoints() {
            try {
                var created = this.userClientService.createUser(new UserRequest("Client Demo User", "client-demo@example.com"));
                boolean userCreated = created != null;

                var fetched = this.userClientService.getUser(created.id());
                boolean userFetched = created.id().equals(fetched.id());

                var users = this.userClientService.getUsers(0, 10, "name");
                boolean usersListed = users.stream().anyMatch(user -> user.id().equals(created.id()));

                var updated = this.userClientService.updateUser(created.id(),
                    new UserRequest("Updated Client Demo User", "updated-client-demo@example.com"));
                boolean userUpdated = "Updated Client Demo User".equals(updated.name());

                this.userClientService.deleteUser(created.id());
                boolean userDeleted = true;

                boolean allTestsPassed = userCreated && userFetched && usersListed && userUpdated && userDeleted;
                return new TestResults(userCreated, userFetched, usersListed, userUpdated, userDeleted, allTestsPassed, null);
            } catch (Exception exception) {
                return new TestResults(false, false, false, false, false, false, exception.getMessage());
            }
        }

        @Json
        public record TestResults(
            boolean userCreated,
            boolean userFetched,
            boolean usersListed,
            boolean userUpdated,
            boolean userDeleted,
            boolean allTestsPassed,
            String error) {
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/grpcclient/controller/ClientTestController.kt"
    package ru.tinkoff.kora.guide.grpcclient.controller

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.grpcclient.dto.UserRequest
    import ru.tinkoff.kora.guide.grpcclient.service.UserClientService
    import ru.tinkoff.kora.http.common.HttpMethod
    import ru.tinkoff.kora.http.common.annotation.HttpRoute
    import ru.tinkoff.kora.http.server.common.annotation.HttpController
    import ru.tinkoff.kora.json.common.annotation.Json

    @Component
    @HttpController
    class ClientTestController(
        private val userClientService: UserClientService
    ) {

        @HttpRoute(method = HttpMethod.POST, path = "/client/test-all-user-endpoints")
        @Json
        fun testAllUserEndpoints(): TestResults {
            return try {
                val created = userClientService.createUser(UserRequest("Client Demo User", "client-demo@example.com"))
                val fetched = userClientService.getUser(created.id)
                val users = userClientService.getUsers(0, 10, "name")
                val updated = userClientService.updateUser(
                    created.id,
                    UserRequest("Updated Client Demo User", "updated-client-demo@example.com")
                )
                userClientService.deleteUser(created.id)

                val userCreated = true
                val userFetched = created.id == fetched.id
                val usersListed = users.any { it.id == created.id }
                val userUpdated = updated.name == "Updated Client Demo User"
                val userDeleted = true
                val allTestsPassed = userCreated && userFetched && usersListed && userUpdated && userDeleted
                TestResults(userCreated, userFetched, usersListed, userUpdated, userDeleted, allTestsPassed, null)
            } catch (exception: Exception) {
                TestResults(false, false, false, false, false, false, exception.message)
            }
        }

        @Json
        data class TestResults(
            val userCreated: Boolean,
            val userFetched: Boolean,
            val usersListed: Boolean,
            val userUpdated: Boolean,
            val userDeleted: Boolean,
            val allTestsPassed: Boolean,
            val error: String?
        )
    }
    ```

Этот контроллер не является настоящей целью руководства. Это просто удобная проверочная обвязка, с которой легко проверить клиента от начала до конца.

## Запуск приложения { #run-app }

Сначала запустите серверное приложение из предыдущего руководства:

```bash
./gradlew run
```

Затем запустите клиентское приложение:

```bash
./gradlew run
```

Теперь вызовите локальную вспомогательную HTTP-точку входа:

```bash
curl -X POST http://localhost:8081/client/test-all-user-endpoints
```

Этот HTTP-вызов является только триггером. Внутри приложения настоящая работа выполняется через сгенерированную заглушку gRPC-клиента.

## Тестирование { #testing }

Тестам клиентского модуля не нужен Docker или полноценный внешний серверный процесс.

Вместо этого они используют:

- `InProcessServerBuilder`
- `InProcessChannelBuilder`

Такой подход особенно хорошо подходит для тестов gRPC-клиента, потому что он позволяет:

- имитировать точные ответы сервера
- сохранять тесты быстрыми
- сосредоточиться на поведении клиента, а не на внешней инфраструктуре

Запустите тесты:

```bash
./gradlew test
```

## Лучшие практики { #best-practices }

- Переиспользуйте один и тот же `.proto`-контракт между клиентом и сервером.
- Оборачивайте сгенерированные заглушки в небольшой прикладной сервис, вместо того чтобы протаскивать их повсюду.
- Держите построение protobuf-сообщений рядом с границей gRPC-клиента.
- Используйте `InProcessServer` для сфокусированных клиентских тестов, когда нужна быстрая и детерминированная обратная связь.
- Относитесь к транспортным моделям gRPC как к транспортным моделям, даже если они похожи на DTO вашего приложения.
- Аннотируйте рукописные DTO через `@Json` только тогда, когда они пересекают границу HTTP/JSON; сгенерированным protobuf-сообщениям JSON-аннотации не нужны.

## Итоги { #summary }

В этом руководстве вы собрали унарный gRPC-клиент, который отражает сервер из предыдущего руководства.

Ключевые идеи:

- переиспользовать общий protobuf-контракт
- внедрять сгенерированные gRPC-заглушки через Kora
- оборачивать их в `UserClientService`
- тестировать клиент через внутрипроцессную gRPC-инфраструктуру

## Ключевые понятия { #key-concepts }

- как gRPC-клиент Kora подключается к графу приложения
- как сгенерированные блокирующие заглушки используются для унарных RPC-вызовов
- почему небольшой клиентский сервисный слой все равно полезен
- как один protobuf-контракт может обслуживать обе стороны системы
- почему `InProcessServer` хорошо подходит для тестов gRPC-клиента

## Устранение неполадок { #troubleshooting }

**Клиент не может подключиться:**

Проверьте, что серверное приложение запущено и что клиентский `application.conf` указывает на правильный хост и gRPC-порт.

**Сгенерированная заглушка отсутствует:**

Запустите `./gradlew clean classes` после изменения `user_service.proto` и проверьте настройку набора исходников protobuf.

**Запрос проходит в тестах, но не во время выполнения:**

Сравните внутрипроцессную настройку теста с настоящей конфигурацией клиента, особенно хост, порт и имена пакетов сервиса.

## Что дальше? { #whats-next }

- [Продвинутый HTTP-сервер](http-server-advanced.md), если вы еще не прошли его.
- [Продвинутый gRPC Server](grpc-server-advanced.md) после продвинутый HTTP-сервер, чтобы добавить потоковые конечные точки, которые сможет вызывать более богатый клиент.
- [Продвинутый gRPC Client](grpc-client-advanced.md) после продвинутый gRPC Server, чтобы поработать с потоками, авторизацией через метаданные и клиентскими перехватчиками.
- [Шаблоны устойчивости](resilient.md), чтобы защитить RPC-вызовы повторными попытками, ограничением времени, автоматическим выключателем и резервным поведением.
- [Наблюдаемость](observability.md), чтобы трассировать gRPC-вызовы и измерять поведение клиента.

## Помощь { #help }

Если что-то не работает:

- сравните с [Kora Java gRPC Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-grpc-client-app) и [Kora Kotlin gRPC Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-grpc-client-app)
- проверьте [документацию gRPC Client](../documentation/grpc-client.md)
- убедитесь, что сервер из [gRPC Server](grpc-server.md) запущен на порту `8090`
- убедитесь, что клиент и сервер используют один и тот же `.proto`-контракт
