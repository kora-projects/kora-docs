---
search:
  exclude: true
title: gRPC-сервер с Kora
summary: Build a gRPC CRUD service with Protocol Buffers, generated handlers, and Kora modules
tags: grpc-server, protobuf, rpc, microservices
---

# gRPC-сервер с Kora { #grpc-server-kora }

Это руководство знакомит с унарными gRPC-серверами в Kora. В нем рассматривается, как договор службы Protocol Buffers генерирует Java-заглушки и сообщения, как реализация gRPC в Kora соединяет эти
сгенерированные типы со службами приложения, и чем ошибки статуса, метаданные и полезная нагрузка Protobuf отличаются от маршрутов JSON-поверх-HTTP. Вы также увидите, как модуль gRPC-сервера входит в
граф зависимостей времени компиляции вместе с компонентами репозитория и службы.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java gRPC Server App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-grpc-server-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin gRPC Server App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-grpc-server-app).

## Что вы создадите { #youll-build }

Вы создадите приложение унарного gRPC-сервера с:

- договором `user_service.proto`, который определяет сообщения запросов и ответов
- сгенерированными классами protobuf-сообщений и базовыми типами gRPC-службы
- gRPC-обработчиком Kora, который реализует `CreateUser`, `GetUser`, `GetUsers`, `UpdateUser` и `DeleteUser`
- репозиторием в памяти и слоем службы, переиспользуемыми за gRPC-транспортом
- обработкой ошибок на основе статусов для отсутствующих пользователей
- конфигурацией сервера и ручными проверками через `grpcurl`

## Что понадобится { #youll-need }

- JDK 17 или новее
- Gradle 7+
- текстовый редактор или среда разработки
- необязательно: `grpcurl` для ручных RPC-проверок

## Требования { #prerequisites }

!!! note "Обязательно: пройдите руководство по HTTP-серверу"

    Это руководство предполагает, что вы уже прошли **[Создание HTTP-сервера](http-server.md)** и уверенно работаете с модулями Kora, `@Component` и разделением слоев репозитория, службы и транспорта.

    Если вы еще не прошли руководство по HTTP-серверу, сначала сделайте это, потому что здесь сохраняется та же модель приложения, а заменяется только транспорт HTTP/JSON на gRPC и Protocol Buffers.

## Обзор { #overview }

Руководство сохраняет ответственности репозитория и службы из руководства по HTTP-серверу, а затем заменяет HTTP-контроллер сгенерированным gRPC-обработчиком.

Такая замена меняет транспортный слой, а не бизнес-модель. В HTTP/JSON API контроллер обычно владеет деталями маршрутизации: путями, методами, телами запросов, кодами ответов и JSON-сериализацией. В
gRPC открытый договор переезжает в `.proto`-файл, а сгенерированные фреймворком классы становятся мостом между сетевыми вызовами и службой приложения.

Kora встраивается в эту модель, связывая сгенерированный обработчик gRPC-службы с графом приложения. Вы по-прежнему пишете обычные Java- или Kotlin-компоненты, но типы запросов и ответов приходят из
protobuf-генерации, а не из написанных вручную DTO. Практический ход такой:

1. определить RPC-договор в protobuf
2. сгенерировать Java-классы и базовые gRPC-типы
3. реализовать компонент Kora, который обрабатывает сгенерированные вызовы службы
4. сопоставить protobuf-сообщения с существующим слоем службы
5. открыть gRPC-сервер через конфигурацию Kora

### Что такое gRPC? { #grpc }

**gRPC** - это протокол удаленного вызова процедур и набор инструментов для создания типизированных API между службами.

Основная идея отличается от типичного HTTP API. В HTTP + JSON обычно проектируют ресурсы и маршруты:

- `POST /users`
- `GET /users/{userId}`
- `PUT /users/{userId}`
- `DELETE /users/{userId}`

Договор распределен между HTTP-методами, путями, кодами статуса, заголовками, JSON-телами запросов, JSON-телами ответов и документацией вроде OpenAPI. Эта модель гибкая и очень удобная для открытых
API, браузеров, ручной отладки и человекочитаемого трафика.

В gRPC вместо этого проектируют интерфейс службы:

```protobuf
service UserService {
  rpc CreateUser(CreateUserRequest) returns (UserResponse) {}
  rpc GetUser(GetUserRequest) returns (UserResponse) {}
}
```

API больше похож на вызов методов удаленной службы. Клиент не собирает URL-путь и не разбирает произвольный JSON вручную. Он вызывает сгенерированный метод со сгенерированным типом запроса и получает
сгенерированный тип ответа.

Ключевое отличие в том, где живет договор.

В HTTP + JSON формат передачи обычно простой и текстовый, но строгий договор часто живет вне кода, если только вы не добавите генерацию кода из OpenAPI. В gRPC `.proto`-файл сначала является
договором, а обе стороны компилируют сгенерированный код из одного и того же договора.

Такая contract-first модель дает gRPC три важных свойства:

- вы описываете API в `.proto`-файле
- код генерируется из этого договора
- клиенты и серверы обмениваются компактными бинарными сообщениями поверх HTTP/2

Транспорт тоже отличается. gRPC использует HTTP/2 как нижележащий протокол, но не ощущается как обычный JSON REST API:

- сообщения сериализуются через Protocol Buffers вместо JSON
- вызовы обычно выполняются через сгенерированные заглушки, а не через написанные вручную URL-запросы
- ошибки представлены gRPC-кодами статуса вместо обычных HTTP-кодов ответа в коде приложения
- потоковая передача является частью RPC-модели, а не дополнительным протоколом
- возможности HTTP/2, такие как мультиплексирование и долгоживущие потоки, являются центральными для передачи вызовов

Поэтому gRPC - это не "HTTP без JSON" и не просто "REST с другим сериализатором". Это другой стиль API, построенный из таких частей:

- **Protocol Buffers** определяет схему и бинарное кодирование.
- **Определения служб** описывают RPC-методы и типы сообщений.
- **Сгенерированный код** создает классы запросов/ответов, базовые серверные типы и клиентские заглушки.
- **HTTP/2** эффективно переносит вызовы по сети.
- **gRPC-коды статуса и метаданные** переносят ошибки и контекст уровня вызова.

На практике это дает совсем другой опыт разработки по сравнению с написанным вручную REST-контроллером:

- вы проектируете операции как RPC-методы, например `CreateUser` или `GetUser`
- сообщения запросов и ответов строго типизированы
- один и тот же договор разделяется сервером и клиентом
- сгенерированный код убирает много транспортного шаблонного кода

Это делает gRPC особенно полезным для взаимодействия служба-с-службой внутри распределенных систем, где производительность, типобезопасность и согласованность договора важнее человекочитаемой
JSON-нагрузки.

HTTP + JSON часто является лучшим вариантом по умолчанию для открытых API, API для браузеров и конечных точек, которые людям нужно напрямую изучать. gRPC обычно сильнее для внутренних API, где обе
стороны контролируются инженерными командами, схема общая, а сгенерированные клиенты приемлемы или желательны.

### Что такое Protocol Buffers? { #protocol-buffers }

**Protocol Buffers** - это язык схем и бинарный формат сериализации, который используется gRPC.

Файл `.proto` определяет:

- службы
- RPC-методы
- сообщения запросов
- сообщения ответов

Например, вместо написания метода HTTP-контроллера вручную вы определяете договор службы:

```protobuf
service UserService {
  rpc CreateUser(CreateUserRequest) returns (UserResponse) {}
}
```

Из этого договора компилятор protobuf генерирует Java-классы для:

- `CreateUserRequest`
- `UserResponse`
- `UserServiceGrpc`

Затем Kora использует эти сгенерированные типы как основу для вашей серверной реализации.

### Зачем строить gRPC поверх HTTP? { #build-grpc-over-http }

Проще всего понять новый транспорт, если сохранить модель приложения стабильной.

В [руководстве по HTTP-серверу](http-server.md) мы уже ввели:

- `UserRepository`
- `InMemoryUserRepository`
- `UserService`
- пользовательские CRUD-операции

В этом руководстве мы переиспользуем ту же учебную модель, но заменяем HTTP-специфичные части на gRPC-специфичные:

- `@HttpController` становится gRPC-обработчиком
- обмен JSON DTO становится обменом protobuf-сообщениями
- HTTP-коды статуса становятся ошибками gRPC `Status`

Так руководство остается дружелюбным для новичков и при этом показывает настоящую gRPC-архитектуру.

## Зависимости { #dependencies }

Мы начинаем с добавления модуля gRPC-сервера и Gradle-плагина protobuf.

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
        implementation "ru.tinkoff.kora:grpc-server"
        implementation "ru.tinkoff.kora:logging-logback"
        implementation "io.grpc:grpc-protobuf:1.74.0"
        implementation "io.grpc:grpc-services:1.74.0"

        testCompileOnly "javax.annotation:javax.annotation-api:1.3.2"
        testAnnotationProcessor "ru.tinkoff.kora:annotation-processors"

        testImplementation platform("org.junit:junit-bom:$junitVersion")
        testImplementation "io.grpc:grpc-netty:1.74.0"
        testImplementation "org.junit.jupiter:junit-jupiter"
        testImplementation "ru.tinkoff.kora:test-junit5"
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
        implementation("ru.tinkoff.kora:grpc-server")
        implementation("ru.tinkoff.kora:logging-logback")
        implementation("io.grpc:grpc-protobuf:1.74.0")
        implementation("io.grpc:grpc-services:1.74.0")

        testCompileOnly("javax.annotation:javax.annotation-api:1.3.2")
        kspTest("ru.tinkoff.kora:symbol-processors")

        testImplementation(platform("org.junit:junit-bom:${property("junitVersion")}"))
        testImplementation("io.grpc:grpc-netty:1.74.0")
        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation("ru.tinkoff.kora:test-junit5")
    }
    ```

Зачем нужны эти зависимости:

- `ru.tinkoff.kora:grpc-server` встраивает gRPC-сервер в граф приложения Kora
- `io.grpc:grpc-protobuf` дает поддержку времени выполнения для сериализации protobuf-сообщений
- `io.grpc:grpc-services` полезна для стандартных gRPC-служб и поддержки, связанной с рефлексией
- Gradle-плагин protobuf генерирует Java-классы из `.proto`-файлов

## Генерация кода { #code-generation }

Теперь мы учим Gradle превращать `.proto`-файлы в Java-код.

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

Это генерирует две группы кода:

- классы protobuf-сообщений, например `CreateUserRequest`
- классы gRPC-службы, например `UserServiceGrpc`

Этот сгенерированный код становится частью обычных исходников приложения.

## Модули { #modules }

Дальше включаем gRPC-сервер в самом приложении Kora.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/grpcserver/Application.java"
    package ru.tinkoff.kora.guide.grpcserver;

    import ru.tinkoff.kora.application.graph.KoraApplication;
    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.config.hocon.HoconConfigModule;
    import ru.tinkoff.kora.grpc.server.GrpcServerModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
        HoconConfigModule,
        GrpcServerModule,  // <----- Подключили модуль
        LogbackModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/grpcserver/Application.kt"
    package ru.tinkoff.kora.guide.grpcserver

    import ru.tinkoff.kora.application.graph.KoraApplication
    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.config.hocon.HoconConfigModule
    import ru.tinkoff.kora.grpc.server.GrpcServerModule
    import ru.tinkoff.kora.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        LogbackModule,
        GrpcServerModule  // <----- Подключили модуль

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

На этом этапе Kora знает, что приложение должно запустить gRPC-сервер.

## API в Protobuf { #protobuf-api }

Теперь определяем сам транспортный договор.

Создайте:

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

Этот договор намеренно повторяет знакомый CRUD API из HTTP-руководства:

- создать одного пользователя
- получить одного пользователя
- вывести список пользователей
- обновить одного пользователя
- удалить одного пользователя

Поэтому это хороший первый пример gRPC: бизнес-смысл уже знаком, и мы можем сосредоточиться на транспорте.

## Слой сервиса { #service-layer }

Мы по-прежнему хотим сохранить ту же архитектуру приложения, что и в HTTP-руководстве:

- репозиторий хранит пользователей
- служба владеет бизнес-логикой
- транспортный слой только адаптирует запросы и ответы

Поэтому мы сохраняем:

- `UserRepository`
- `InMemoryUserRepository`
- `UserService`
- `UserNotFoundException`

Важный момент: не переносите бизнес-логику в gRPC-обработчик. Обработчик должен оставаться сосредоточенным на:

- чтении protobuf-запросов
- вызове слоя службы
- преобразовании результатов службы в protobuf-ответы

## gRPC-обработчик { #grpc-handler }

В этой точке gRPC заменяет HTTP-контроллер.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/grpcserver/grpc/UserServiceGrpcHandler.java"
    package ru.tinkoff.kora.guide.grpcserver.grpc;

    import com.google.protobuf.Empty;
    import com.google.protobuf.Timestamp;
    import io.grpc.Status;
    import io.grpc.stub.StreamObserver;

    import java.time.ZoneOffset;

    import org.slf4j.Logger;
    import org.slf4j.LoggerFactory;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.grpcserver.CreateUserRequest;
    import ru.tinkoff.kora.guide.grpcserver.DeleteUserRequest;
    import ru.tinkoff.kora.guide.grpcserver.GetUserRequest;
    import ru.tinkoff.kora.guide.grpcserver.GetUsersRequest;
    import ru.tinkoff.kora.guide.grpcserver.GetUsersResponse;
    import ru.tinkoff.kora.guide.grpcserver.UpdateUserRequest;
    import ru.tinkoff.kora.guide.grpcserver.UserResponse;
    import ru.tinkoff.kora.guide.grpcserver.UserServiceGrpc;
    import ru.tinkoff.kora.guide.grpcserver.dto.UserRequest;
    import ru.tinkoff.kora.guide.grpcserver.service.UserNotFoundException;
    import ru.tinkoff.kora.guide.grpcserver.service.UserService;

    @Component
    public final class UserServiceGrpcHandler extends UserServiceGrpc.UserServiceImplBase {

        private static final Logger logger = LoggerFactory.getLogger(UserServiceGrpcHandler.class);

        private final UserService userService;

        public UserServiceGrpcHandler(UserService userService) {
            this.userService = userService;
        }

        @Override
        public void createUser(CreateUserRequest request, StreamObserver<UserResponse> responseObserver) {
            try {
                logger.info("Creating user: name={}, email={}", request.getName(), request.getEmail());
                var user = userService.createUser(new UserRequest(request.getName(), request.getEmail()));
                responseObserver.onNext(toGrpcUser(user));
                responseObserver.onCompleted();
            } catch (Exception e) {
                responseObserver.onError(Status.INTERNAL
                    .withDescription("Failed to create user")
                    .withCause(e)
                    .asRuntimeException());
            }
        }

        @Override
        public void getUser(GetUserRequest request, StreamObserver<UserResponse> responseObserver) {
            try {
                var user = userService.getUser(request.getUserId())
                    .orElseThrow(() -> Status.NOT_FOUND
                        .withDescription("User not found: " + request.getUserId())
                        .asRuntimeException());
                responseObserver.onNext(toGrpcUser(user));
                responseObserver.onCompleted();
            } catch (RuntimeException e) {
                responseObserver.onError(e);
            }
        }

        @Override
        public void getUsers(GetUsersRequest request, StreamObserver<GetUsersResponse> responseObserver) {
            try {
                int page = request.getPage();
                int size = request.getSize() == 0 ? 10 : request.getSize();
                String sort = request.getSort().isBlank() ? "name" : request.getSort();

                var response = GetUsersResponse.newBuilder()
                    .addAllUsers(userService.getUsers(page, size, sort).stream().map(this::toGrpcUser).toList())
                    .build();

                responseObserver.onNext(response);
                responseObserver.onCompleted();
            } catch (Exception e) {
                responseObserver.onError(Status.INTERNAL.withDescription("Failed to get users").withCause(e).asRuntimeException());
            }
        }

        @Override
        public void updateUser(UpdateUserRequest request, StreamObserver<UserResponse> responseObserver) {
            try {
                var updated = userService.updateUser(request.getUserId(), new UserRequest(request.getName(), request.getEmail()));
                responseObserver.onNext(toGrpcUser(updated));
                responseObserver.onCompleted();
            } catch (UserNotFoundException e) {
                responseObserver.onError(Status.NOT_FOUND.withDescription(e.getMessage()).asRuntimeException());
            }
        }

        @Override
        public void deleteUser(DeleteUserRequest request, StreamObserver<Empty> responseObserver) {
            try {
                userService.deleteUser(request.getUserId());
                responseObserver.onNext(Empty.getDefaultInstance());
                responseObserver.onCompleted();
            } catch (UserNotFoundException e) {
                responseObserver.onError(Status.NOT_FOUND.withDescription(e.getMessage()).asRuntimeException());
            }
        }

        private UserResponse toGrpcUser(ru.tinkoff.kora.guide.grpcserver.dto.UserResponse user) {
            return UserResponse.newBuilder()
                .setId(user.id())
                .setName(user.name())
                .setEmail(user.email())
                .setCreatedAt(Timestamp.newBuilder()
                    .setSeconds(user.createdAt().toEpochSecond(ZoneOffset.UTC))
                    .setNanos(user.createdAt().getNano())
                    .build())
                .build();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/grpcserver/grpc/UserServiceGrpcHandler.kt"
    package ru.tinkoff.kora.guide.grpcserver.grpc

    import com.google.protobuf.Empty
    import com.google.protobuf.Timestamp
    import io.grpc.Status
    import io.grpc.stub.StreamObserver
    import org.slf4j.LoggerFactory
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.grpcserver.*
    import ru.tinkoff.kora.guide.grpcserver.dto.UserRequest
    import ru.tinkoff.kora.guide.grpcserver.dto.UserResponse
    import ru.tinkoff.kora.guide.grpcserver.service.UserNotFoundException
    import ru.tinkoff.kora.guide.grpcserver.service.UserService
    import java.time.ZoneOffset

    @Component
    class UserServiceGrpcHandler(
        private val userService: UserService
    ) : UserServiceGrpc.UserServiceImplBase() {

        private val logger = LoggerFactory.getLogger(UserServiceGrpcHandler::class.java)

        override fun createUser(
            request: CreateUserRequest,
            responseObserver: StreamObserver<ru.tinkoff.kora.guide.grpcserver.UserResponse>
        ) {
            try {
                logger.info("Creating user: name={}, email={}", request.name, request.email)
                val user = userService.createUser(UserRequest(request.name, request.email))
                responseObserver.onNext(toGrpcUser(user))
                responseObserver.onCompleted()
            } catch (e: Exception) {
                logger.error("Failed to create user", e)
                responseObserver.onError(
                    Status.INTERNAL.withDescription("Failed to create user").withCause(e).asRuntimeException()
                )
            }
        }

        override fun getUser(
            request: GetUserRequest,
            responseObserver: StreamObserver<ru.tinkoff.kora.guide.grpcserver.UserResponse>
        ) {
            try {
                logger.info("Getting user: id={}", request.userId)
                val user = userService.getUser(request.userId)
                    ?: throw Status.NOT_FOUND.withDescription("User not found: ${request.userId}").asRuntimeException()
                responseObserver.onNext(toGrpcUser(user))
                responseObserver.onCompleted()
            } catch (e: RuntimeException) {
                logger.error("Failed to get user", e)
                responseObserver.onError(e)
            }
        }

        override fun getUsers(request: GetUsersRequest, responseObserver: StreamObserver<GetUsersResponse>) {
            try {
                val page = request.page
                val size = if (request.size == 0) 10 else request.size
                val sort = request.sort.ifBlank { "name" }
                val response = GetUsersResponse.newBuilder()
                    .addAllUsers(userService.getUsers(page, size, sort).map(::toGrpcUser))
                    .build()
                responseObserver.onNext(response)
                responseObserver.onCompleted()
            } catch (e: Exception) {
                logger.error("Failed to get users", e)
                responseObserver.onError(
                    Status.INTERNAL.withDescription("Failed to get users").withCause(e).asRuntimeException()
                )
            }
        }

        override fun updateUser(
            request: UpdateUserRequest,
            responseObserver: StreamObserver<ru.tinkoff.kora.guide.grpcserver.UserResponse>
        ) {
            try {
                val updated = userService.updateUser(request.userId, UserRequest(request.name, request.email))
                responseObserver.onNext(toGrpcUser(updated))
                responseObserver.onCompleted()
            } catch (e: UserNotFoundException) {
                logger.error("Failed to update user", e)
                responseObserver.onError(Status.NOT_FOUND.withDescription(e.message).asRuntimeException())
            }
        }

        override fun deleteUser(request: DeleteUserRequest, responseObserver: StreamObserver<Empty>) {
            try {
                userService.deleteUser(request.userId)
                responseObserver.onNext(Empty.getDefaultInstance())
                responseObserver.onCompleted()
            } catch (e: UserNotFoundException) {
                logger.error("Failed to delete user", e)
                responseObserver.onError(Status.NOT_FOUND.withDescription(e.message).asRuntimeException())
            }
        }

        private fun toGrpcUser(user: UserResponse): ru.tinkoff.kora.guide.grpcserver.UserResponse {
            return ru.tinkoff.kora.guide.grpcserver.UserResponse.newBuilder()
                .setId(user.id)
                .setName(user.name)
                .setEmail(user.email)
                .setCreatedAt(
                    Timestamp.newBuilder()
                        .setSeconds(user.createdAt.toEpochSecond(ZoneOffset.UTC))
                        .setNanos(user.createdAt.nano)
                        .build()
                )
                .build()
        }
    }
    ```

Здесь есть две особенно важные идеи:

- обработчик расширяет сгенерированный `UserServiceGrpc.UserServiceImplBase`
- транспортные ошибки выражаются через gRPC `Status`, а не через HTTP-исключения

Второй пункт очень важен. Это уже не HTTP-приложение, поэтому язык транспорта должен быть родным для gRPC.

## Конфигурация { #config }

Полная модель gRPC-обработчиков, конфигурации сервера и reflection описана в разделах [обработчиков](../documentation/grpc-server.md#handlers) и [reflection](../documentation/grpc-server.md#reflection).

Добавьте небольшой `application.conf`:

Полный справочник по конфигурации смотрите в разделах [gRPC-сервер](../documentation/grpc-server.md) и [Журналирование SLF4J](../documentation/logging-slf4j.md).

===! ":material-code-json: `Hocon`"

    ```javascript title="src/main/resources/application.conf"
    grpcServer {
      port = 8090 //(1)!
      telemetry.logging.enabled = true //(2)!
    }

    logging {
      levels {
        "ROOT": "WARN" //(3)!
        "ru.tinkoff.kora": "INFO" //(4)!
        "ru.tinkoff.kora.guide.grpcserver": "INFO" //(5)!
      }
    }
    ```

    1. Порт gRPC-сервера по умолчанию, который используется в этом руководстве.
    2. Включает возможность для этого раздела конфигурации.
    3. Уровень журналирования для `ROOT`.
    4. Уровень журналирования для `ru.tinkoff.kora`.
    5. Уровень журналирования для `ru.tinkoff.kora.guide.grpcserver`.

=== ":simple-yaml: `YAML`"

    ```yaml title="src/main/resources/application.yaml"
    grpcServer:
      port: 8090 #(1)!
      telemetry:
        logging:
          enabled: true #(2)!
    logging:
      levels:
        ROOT: "WARN" #(3)!
        "ru.tinkoff.kora": "INFO" #(4)!
        "ru.tinkoff.kora.guide.grpcserver": "INFO" #(5)!
    ```

    1. Порт gRPC-сервера по умолчанию, который используется в этом руководстве.
    2. Включает возможность для этого раздела конфигурации.
    3. Уровень журналирования для `ROOT`.
    4. Уровень журналирования для `ru.tinkoff.kora`.
    5. Уровень журналирования для `ru.tinkoff.kora.guide.grpcserver`.

Это дает нам:

- gRPC-сервер на порту `8090`
- журналирование gRPC-запросов Kora
- читаемые журналы для демонстрационного модуля

## Запуск приложения { #run-app }

Соберите сгенерированные исходники и скомпилируйте приложение:

```bash
./gradlew clean classes
```

Запустите его:

```bash
./gradlew run
```

Затем вызовите его через `grpcurl`:

```bash
grpcurl -plaintext -d "{\"name\":\"Alice\",\"email\":\"alice@example.com\"}" \
  localhost:8090 ru.tinkoff.kora.guide.grpcserver.UserService/CreateUser
```

```bash
grpcurl -plaintext -d "{\"page\":0,\"size\":10,\"sort\":\"name\"}" \
  localhost:8090 ru.tinkoff.kora.guide.grpcserver.UserService/GetUsers
```

## Запуск тестов { #testing }

Сопутствующее приложение включает JUnit-тесты, которые используют настоящий gRPC-канал к приложению.

Запустите их:

```bash
./gradlew test
```

Тесты проверяют сервисный CRUD по отдельности, а не как один огромный сценарий. Так сбои проще понимать.

## Лучшие практики { #best-practices }

- Держите protobuf-договоры сфокусированными на транспортных задачах, а не на деталях реализации предметной области.
- Держите бизнес-логику в `UserService`, а не в gRPC-обработчике.
- Сопоставляйте отсутствующие ресурсы с `Status.NOT_FOUND`, а не с общими внутренними ошибками.
- Переиспользуйте одну и ту же архитектуру приложения между транспортами, когда это возможно.
- Рассматривайте сгенерированный protobuf-код как транспортные типы, а не как доменные модели.
- Помечайте написанные вручную DTO аннотацией `@Json` только тогда, когда они пересекают HTTP/JSON-границу; сгенерированным protobuf-сообщениям JSON-аннотации не нужны.

## Итоги { #summary }

В этом руководстве вы создали унарный gRPC-сервер, который повторяет CRUD-приложение из руководства по HTTP-серверу.

Ключевая идея была простой:

- сохранить знакомые слои репозитория и службы
- определить транспорт в `.proto`
- реализовать сгенерированный gRPC-обработчик поверх той же бизнес-логики

## Ключевые понятия { #key-concepts }

- что такое gRPC и почему он полезен для взаимодействия служба-с-службой
- как Protocol Buffers определяет общий RPC-договор
- как Kora запускает и связывает gRPC-сервер
- как унарные RPC-методы сопоставляются со знакомыми CRUD-операциями
- как ошибки gRPC `Status` заменяют транспортные ошибки в HTTP-стиле

## Устранение неполадок { #troubleshooting }

**Сгенерированные классы отсутствуют:**

Запустите `./gradlew clean classes` после изменения `.proto`-файла и проверьте, что Gradle-плагин protobuf настроен.

**Сервер не запускается:**

Проверьте, что gRPC-порт в `application.conf` свободен и что `GrpcServerModule` включен в граф приложения.

**RPC возвращает `UNIMPLEMENTED`:**

Проверьте, что сгенерированное имя службы и имена методов соответствуют `.proto`-договору, который использует клиент.

## Что дальше? { #whats-next }

- [HTTP-клиент](http-client.md), если вы еще его не проходили; руководство по gRPC-клиенту предполагает эту структуру клиентского приложения.
- [gRPC-клиент](grpc-client.md) после HTTP-клиента, чтобы вызывать эту унарную службу через сгенерированные заглушки.
- [Продвинутый HTTP-сервер](http-server-advanced.md) перед [продвинутым gRPC-сервером](grpc-server-advanced.md), потому что продвинутое руководство по gRPC переиспользует продвинутые серверные
  понятия.
- [Наблюдаемость](observability.md), чтобы наблюдать gRPC-службы вместе с HTTP-службами.

## Помощь { #help }

Если что-то не работает:

- сравните с [Kora Java gRPC Server App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-grpc-server-app) и [Kora Kotlin gRPC Server App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-grpc-server-app)
- проверьте [документацию gRPC-сервера](../documentation/grpc-server.md)
- проверьте [документацию gRPC-клиента](../documentation/grpc-client.md), когда договоры клиента и сервера расходятся
- убедитесь, что вы перегенерировали код после изменения `.proto`-файла
