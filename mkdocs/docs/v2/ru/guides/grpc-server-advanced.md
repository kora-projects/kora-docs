---
search:
  exclude: true
title: Продвинутый gRPC-сервер с Kora
summary: Extend a Kora 2.0 gRPC server with streaming RPCs, server interceptors, API-key auth, and reflection
description: "Advanced Kora gRPC server: a second protobuf service with server, client and bidirectional streaming handlers, global ServerInterceptor components scoped in code by SERVICE_NAME, API-key authorization read from gRPC Metadata through a @ConfigSource, gRPC reflection via io.grpc:grpc-services and grpcServer.reflectionEnabled, and @KoraAppTest streaming tests."
agent:
  use_when: "Use this file for questions about advanced Kora gRPC servers: streaming RPC handlers extending a generated ...ImplBase, StreamObserver request and response observers, the onNext / onCompleted / onError rules, ServerInterceptor registered as a plain @Component and scoped at runtime with getMethodDescriptor().getServiceName(), Status.UNAUTHENTICATED metadata authorization, grpcServer.port and grpcServer.reflectionEnabled, io.grpc:grpc-services for ProtoReflectionServiceV1, and grpc-netty in test scope."
tags: grpc-server, protobuf, streaming, interceptors, reflection, authentication
---

# Продвинутый gRPC-сервер с Kora { #advanced-grpc-server-kora }

Это руководство знакомит с продвинутыми возможностями gRPC-сервера в Kora. В нем рассматриваются серверная потоковая передача, клиентская потоковая передача, двунаправленная потоковая передача,
серверные перехватчики, авторизация по метаданным и рефлексия для локальных инструментов. Вы также увидите, как потоковые обработчики используют наблюдателей и сигналы завершения, а унарные службы
остаются доступными в том же графе приложения.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java gRPC Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-grpc-server-advanced-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin gRPC Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-grpc-server-advanced-app).

## Что вы создадите { #youll-build }

Вы расширите приложение gRPC-сервера:

- второй protobuf-службой `UserStreamingService`, отдельной от унарной CRUD-службы
- `GetAllUsers` как серверным потоковым RPC
- `CreateUsers` как клиентским потоковым RPC
- `UpdateUsers` как двунаправленным потоковым RPC
- gRPC-обработчиком Kora, который использует наблюдателей, сигналы завершения и обработку ошибок потока
- серверным перехватчиком логирования
- авторизацией по API-ключу в метаданных только для потоковой службы
- включенной gRPC-рефлексией для локального исследования инструментами вроде `grpcurl`

## Что понадобится { #youll-need }

- JDK 25 или новее
- Gradle 9+ (эталонные приложения используют Gradle Wrapper `9.5.1`)
- текстовый редактор или среда разработки
- необязательно: `grpcurl` для рефлексии и ручных потоковых проверок

Артефакты Kora собраны под Java 25, поэтому JDK, которым компилируется ваш код, должен быть версии 25 или новее.

## Требования { #prerequisites }

!!! note "Обязательно: пройдите базовое руководство по gRPC-серверу"

    Это руководство предполагает, что вы уже прошли **[gRPC-сервер с Kora](grpc-server.md)** и **[Продвинутый HTTP-сервер](http-server-advanced.md)** и понимаете унарные gRPC-обработчики, генерацию protobuf-кода и разделение на репозиторий и службу, используемое во всех руководствах.

    Если вы еще не прошли базовое руководство по gRPC-серверу, сначала сделайте это, потому что здесь унарная служба остается неизменной, а вокруг нее добавляются потоки, рефлексия, перехватчики и авторизация по метаданным.

## Обзор { #overview }

Самое важное решение в этом руководстве — мы **не перегружаем исходную унарную службу** всеми продвинутыми понятиями.

Вместо этого:

- `UserService` остается знакомой унарной CRUD-службой
- `UserStreamingService` становится отдельной продвинутой службой в `.proto`-контракте
- `UserStreamingServiceGrpcHandler` занимается только потоковыми операциями

Такое разделение упрощает изучение и повторяет распространенный продуктивный шаблон: держать базовый синхронный API стабильным, а специализированные потоковые API добавлять только там, где они
действительно помогают.

Kora по-прежнему владеет связыванием компонентов и жизненным циклом. gRPC владеет протоколом RPC и сгенерированными контрактами служб. Ваш код находится между ними: он реализует сгенерированные методы
службы, внедряет обычные компоненты Kora и переводит потоковые колбэки в поведение приложения.

У продвинутых частей этого руководства разные зоны ответственности:

- потоки меняют форму и время жизни RPC-вызова
- перехватчики добавляют сквозное поведение вокруг вызовов
- рефлексия открывает метаданные служб инструментам вроде `grpcurl`
- авторизация по метаданным читает метаданные запроса до запуска бизнес-логики

Все это — задачи транспортного уровня. Они важны, но не должны заставлять слой репозитория или службы знать о внутренностях gRPC. Слой службы должен по-прежнему говорить в терминах приложения:
пользователи, запросы, ответы и бизнес-правила. gRPC-обработчик — это адаптер, который превращает сгенерированные protobuf-сообщения и потоковые колбэки в такие операции приложения.

В потоковом коде это разделение важнее, чем в унарном. Унарный обработчик получает один запрос, вызывает метод службы и возвращает один ответ. Потоковый обработчик владеет более долгим
взаимодействием:

- он может отправить несколько ответов до завершения
- он может получить несколько запросов до формирования итогового ответа
- он должен решать, когда вызывать `onNext`, `onCompleted` или `onError`
- он должен помнить про отмену, встречное давление и частичные сбои

Одна специфичная для Kora деталь определяет, как можно писать такие обработчики: каждое клиентское соединение получает выделенный однопоточный исполнитель на **виртуальном потоке**, и все колбэки
перехватчиков и обработчиков для вызовов этого соединения выполняются на нем — по одному за раз и в порядке поступления. Блокироваться внутри обработчика безопасно (несущий поток освобождается), но это
задерживает другие вызовы *того же* соединения. Поэтому все обработчики в этом руководстве — обычный синхронный код без собственных пулов потоков.

Реализация намеренно оставлена небольшой, но архитектура повторяет продуктивный код: сохранить стабильный унарный API, добавить отдельную потоковую службу и разместить продвинутую механику gRPC на краю
приложения.

### Зачем нужна потоковая передача в gRPC { #grpc-streaming-exists }

Унарный RPC хорош, когда один запрос естественно порождает один ответ.

Но иногда сам транспорт должен выражать другую форму диалога:

- один запрос, много ответов
- много запросов, один ответ
- много запросов, много ответов

Именно это дают потоки. В `.proto`-контракте задействован единственный синтаксис — ключевое слово `stream` со стороны запроса, со стороны ответа или с обеих.

### Серверная потоковая передача { #server-streaming }

Клиент отправляет один запрос, а сервер отправляет обратно много сообщений.

Это полезно, когда:

- нужно передавать большой результирующий набор
- клиент может начать потреблять результаты сразу
- данные естественно приходят последовательностью

Сгенерированная сигнатура остается `void method(Req request, StreamObserver<Resp> responseObserver)` — меняется то, что обработчик вызывает `onNext` несколько раз перед `onCompleted`.

### Клиентская потоковая передача { #client-streaming }

Клиент отправляет много сообщений, а сервер отвечает один раз в конце.

Это полезно, когда:

- клиент группирует операции в пакет
- сервер должен агрегировать работу перед ответом
- один сводный ответ полезнее множества мелких подтверждений

Здесь сгенерированная сигнатура инвертируется: метод *возвращает* `StreamObserver<Req>`, в который gRPC подает входящие сообщения, а единственный ответ отправляется через переданный наблюдатель.

### Двунаправленная потоковая передача { #bidirectional-streaming }

Клиент и сервер обмениваются множеством сообщений в рамках одного вызова.

Это полезно, когда:

- диалог интерактивный
- обновления должны идти в обе стороны
- одна сторона не должна ждать, пока другая закончит отправлять все

Сигнатура та же, что у клиентского потока, но ничто не мешает обработчику отвечать на каждое входящее сообщение сразу, не дожидаясь `onCompleted`.

## Неизменное { #immutable }

Прежде чем добавлять что-то новое, держите в голове, что **не** меняется:

- `UserRepository`
- `InMemoryUserRepository`
- `UserService`
- унарный `UserServiceGrpcHandler`

Это намеренно. Продвинутые возможности должны расширять приложение, а не заставлять переписывать базовый путь, которому вы уже доверяете.

## Зависимости { #dependencies }

Сборка — та же, что в базовом руководстве по gRPC-серверу, плюс артефакты, нужные рефлексии и тестам.

Версии модулей Kora берутся из BOM Kora `io.koraframework:kora-bom`, поэтому отдельные артефакты Kora объявляются без версии:

```properties title="gradle.properties"
koraVersion=2.0.0.RC1
junitVersion=6.1.3
```

===! ":fontawesome-brands-java: `Java`"

    Обновите `build.gradle`:

    ```groovy title="build.gradle"
    dependencies {
        koraBom platform("io.koraframework:kora-bom:$koraVersion")

        compileOnly "javax.annotation:javax.annotation-api:1.3.2"
        annotationProcessor "io.koraframework:annotation-processors"

        implementation "io.koraframework:config-hocon"
        implementation "io.koraframework:grpc-server"
        implementation "io.koraframework:logging-logback"
        implementation "io.grpc:grpc-protobuf:1.83.1"
        implementation "io.grpc:grpc-services:1.83.1"

        testCompileOnly "javax.annotation:javax.annotation-api:1.3.2"
        testAnnotationProcessor "io.koraframework:annotation-processors"

        testImplementation platform("org.junit:junit-bom:$junitVersion")
        testImplementation "io.grpc:grpc-netty:1.83.1"
        testImplementation "org.junit.jupiter:junit-jupiter"
        testImplementation "io.koraframework:test-junit5"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите `build.gradle.kts`:

    ```kotlin title="build.gradle.kts"
    dependencies {
        implementation(platform("io.koraframework:kora-bom:${property("koraVersion")}"))

        compileOnly("javax.annotation:javax.annotation-api:1.3.2")
        ksp("io.koraframework:symbol-processors:${property("koraVersion")}")

        implementation("io.koraframework:config-hocon")
        implementation("io.koraframework:grpc-server")
        implementation("io.koraframework:logging-logback")
        implementation("io.grpc:grpc-protobuf:1.83.1")
        implementation("io.grpc:grpc-services:1.83.1")

        testCompileOnly("javax.annotation:javax.annotation-api:1.3.2")

        testImplementation(platform("org.junit:junit-bom:${property("junitVersion")}"))
        testImplementation("io.grpc:grpc-netty:1.83.1")
        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation("io.koraframework:test-junit5")
    }
    ```

Две из них заслуживают пояснения:

- `io.grpc:grpc-services` несет `ProtoReflectionServiceV1`. Kora добавляет службу рефлексии, только если этот класс есть в classpath, поэтому одного `reflectionEnabled = true` без него недостаточно.
- `io.grpc:grpc-netty` нужен только тестам. `@KoraAppTest` поднимает настоящий сервер, а тест выступает обычным gRPC-клиентом, которому нужен клиентский транспорт в тестовом classpath.

Блок Gradle-плагина protobuf не меняется по сравнению с [базовым руководством](grpc-server.md#code-generation) — новая потоковая служба генерируется из того же `.proto`-файла той же задачей.

!!! warning "Держите все артефакты `io.grpc` на одной версии"

    Среда выполнения gRPC, поставляемая с `io.koraframework:grpc-server`, — это `1.83.1`. Любой другой объявленный вами артефакт `io.grpc` — `grpc-protobuf`, `grpc-services` и все, что в тестовой
    области, например `grpc-netty`, — должен использовать ровно эту версию. Зафиксированная более старая версия прекрасно компилируется и падает только во время выполнения с
    `AbstractMethodError: ... does not define or inherit an implementation of the resolved method 'buildClientTransportServers(List, MetricRecorder)'`.

## Protobuf API { #protobuf-api }

Контракт получает вторую службу. Унарная остается нетронутой, если не считать переименования ее сообщения обновления, чтобы унарные и потоковые обновления со временем могли иметь разную форму.

??? example "Protobuf-контракт"

    ```protobuf title="src/main/proto/user_service.proto"
    syntax = "proto3";

    package io.koraframework.guide.grpcserver.advanced;
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

Обе службы лежат в одном файле и обслуживаются одним приложением Kora на одном порту. Разделены они только в контракте, в обработчике и — как вы увидите ниже — в том, что защищает перехватчик
авторизации.

## Потоковая служба { #streaming-service }

Так же как мы разделили транспортный контракт, мы разделяем и логику приложения.

Продвинутый модуль вводит `UserStreamingService` — тонкую службу приложения перед существующим `UserService`:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/grpcserver/advanced/service/UserStreamingService.java"
    package io.koraframework.guide.grpcserver.advanced.service;

    import java.util.List;
    import java.util.Optional;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.grpcserver.advanced.dto.UserRequest;
    import io.koraframework.guide.grpcserver.advanced.dto.UserResponse;

    @Component
    public final class UserStreamingService {

        private final UserService userService;

        public UserStreamingService(UserService userService) {
            this.userService = userService;
        }

        public List<UserResponse> getAllUsers() {
            return userService.getUsers(0, Integer.MAX_VALUE, "name");
        }

        public List<UserResponse> createUsers(List<UserRequest> requests) {
            return requests.stream()
                .map(userService::createUser)
                .toList();
        }

        public Optional<UserResponse> tryUpdateUser(String id, UserRequest request) { //(1)!
            try {
                return Optional.of(userService.updateUser(id, request));
            } catch (UserNotFoundException e) {
                return Optional.empty();
            }
        }
    }
    ```

    1. Двунаправленный обработчик обновляет пользователей по одному сообщению и не должен обрывать весь поток из-за одного промаха, поэтому случай «не найдено» становится пустым результатом, а не исключением.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/grpcserver/advanced/service/UserStreamingService.kt"
    package io.koraframework.guide.grpcserver.advanced.service

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.grpcserver.advanced.dto.UserRequest
    import io.koraframework.guide.grpcserver.advanced.dto.UserResponse

    @Component
    class UserStreamingService(
        private val userService: UserService
    ) {

        fun getAllUsers(): List<UserResponse> = userService.getUsers(0, Int.MAX_VALUE, "name")

        fun createUsers(requests: List<UserRequest>): List<UserResponse> = requests.map(userService::createUser)

        fun tryUpdateUser(id: String, request: UserRequest): UserResponse? { //(1)!
            return try {
                userService.updateUser(id, request)
            } catch (e: UserNotFoundException) {
                null
            }
        }
    }
    ```

    1. Двунаправленный обработчик обновляет пользователей по одному сообщению и не должен обрывать весь поток из-за одного промаха, поэтому случай «не найдено» становится результатом `null`, а не исключением.

Эта служба владеет логикой:

- возврата всех пользователей для серверного потока
- создания множества пользователей для клиентского потока
- обновления пользователей для двунаправленного потока

Так исходный `UserService` остается близким к руководству по HTTP и не превращается в специфичный для транспорта класс-бог.

## Потоковый обработчик { #streaming-handler }

Теперь подключим сгенерированную потоковую службу к новой службе приложения.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/grpcserver/advanced/grpc/UserStreamingServiceGrpcHandler.java"
    package io.koraframework.guide.grpcserver.advanced.grpc;

    import com.google.protobuf.Empty;
    import com.google.protobuf.Timestamp;
    import io.grpc.Status;
    import io.grpc.StatusRuntimeException;
    import io.grpc.stub.StreamObserver;
    import java.time.ZoneOffset;
    import java.util.ArrayList;
    import java.util.List;
    import org.slf4j.Logger;
    import org.slf4j.LoggerFactory;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.grpcserver.advanced.CreateUserRequest;
    import io.koraframework.guide.grpcserver.advanced.CreateUsersResponse;
    import io.koraframework.guide.grpcserver.advanced.UpdateUserRequest;
    import io.koraframework.guide.grpcserver.advanced.UserResponse;
    import io.koraframework.guide.grpcserver.advanced.UserStreamingServiceGrpc;
    import io.koraframework.guide.grpcserver.advanced.dto.UserRequest;
    import io.koraframework.guide.grpcserver.advanced.service.UserStreamingService;

    @Component
    public final class UserStreamingServiceGrpcHandler extends UserStreamingServiceGrpc.UserStreamingServiceImplBase {

        private static final Logger logger = LoggerFactory.getLogger(UserStreamingServiceGrpcHandler.class);

        private final UserStreamingService userStreamingService;

        public UserStreamingServiceGrpcHandler(UserStreamingService userStreamingService) {
            this.userStreamingService = userStreamingService;
        }

        @Override
        public void getAllUsers(Empty request, StreamObserver<UserResponse> responseObserver) { //(1)!
            try {
                for (var user : userStreamingService.getAllUsers()) {
                    responseObserver.onNext(toGrpcUser(user));
                }
                responseObserver.onCompleted();
            } catch (Exception e) {
                responseObserver.onError(Status.INTERNAL.withDescription("Failed to stream users").withCause(e).asRuntimeException());
            }
        }

        @Override
        public StreamObserver<CreateUserRequest> createUsers(StreamObserver<CreateUsersResponse> responseObserver) { //(2)!
            return new StreamObserver<>() {
                private final List<UserRequest> requests = new ArrayList<>();

                @Override
                public void onNext(CreateUserRequest value) {
                    requests.add(new UserRequest(value.getName(), value.getEmail()));
                }

                @Override
                public void onError(Throwable t) { //(3)!
                    logger.error("Client streaming failed", t);
                    responseObserver.onError(t);
                }

                @Override
                public void onCompleted() {
                    try {
                        var createdUsers = userStreamingService.createUsers(requests);
                        responseObserver.onNext(CreateUsersResponse.newBuilder()
                            .setCreatedCount(createdUsers.size())
                            .addAllUserIds(createdUsers.stream().map(io.koraframework.guide.grpcserver.advanced.dto.UserResponse::id).toList())
                            .build());
                        responseObserver.onCompleted();
                    } catch (Exception e) {
                        responseObserver.onError(Status.INTERNAL.withDescription("Failed to create users").withCause(e).asRuntimeException());
                    }
                }
            };
        }

        @Override
        public StreamObserver<UpdateUserRequest> updateUsers(StreamObserver<UserResponse> responseObserver) { //(4)!
            return new StreamObserver<>() {
                @Override
                public void onNext(UpdateUserRequest value) {
                    try {
                        var user = userStreamingService.tryUpdateUser(value.getUserId(), new UserRequest(value.getName(), value.getEmail()))
                            .orElseThrow(() -> Status.NOT_FOUND.withDescription("User not found: " + value.getUserId()).asRuntimeException());
                        responseObserver.onNext(toGrpcUser(user));
                    } catch (StatusRuntimeException e) {
                        responseObserver.onError(e);
                    }
                }

                @Override
                public void onError(Throwable t) {
                    logger.error("Bidirectional streaming failed", t);
                    responseObserver.onError(t);
                }

                @Override
                public void onCompleted() {
                    responseObserver.onCompleted();
                }
            };
        }

        private UserResponse toGrpcUser(io.koraframework.guide.grpcserver.advanced.dto.UserResponse user) {
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

    1. Серверный поток: много `onNext`, затем ровно один `onCompleted`.
    2. Клиентский поток: метод возвращает наблюдателя, в которого gRPC будет проталкивать запросы; ответ формируется только в `onCompleted`.
    3. `onError` у наблюдателя *запросов* означает, что клиент прервал вызов, — обработчик должен остановиться и закрыть сторону ответов тоже.
    4. Двунаправленный поток: на каждое входящее сообщение отвечают сразу, поэтому ответы чередуются с запросами.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/grpcserver/advanced/grpc/UserStreamingServiceGrpcHandler.kt"
    package io.koraframework.guide.grpcserver.advanced.grpc

    import com.google.protobuf.Empty
    import io.grpc.Status
    import io.grpc.StatusRuntimeException
    import io.grpc.stub.StreamObserver
    import org.slf4j.LoggerFactory
    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.grpcserver.advanced.CreateUserRequest
    import io.koraframework.guide.grpcserver.advanced.CreateUsersResponse
    import io.koraframework.guide.grpcserver.advanced.UpdateUserRequest
    import io.koraframework.guide.grpcserver.advanced.UserStreamingServiceGrpc
    import io.koraframework.guide.grpcserver.advanced.dto.UserRequest
    import io.koraframework.guide.grpcserver.advanced.service.UserStreamingService

    @Component
    class UserStreamingServiceGrpcHandler(
        private val userStreamingService: UserStreamingService
    ) : UserStreamingServiceGrpc.UserStreamingServiceImplBase() {

        private val logger = LoggerFactory.getLogger(UserStreamingServiceGrpcHandler::class.java)

        override fun getAllUsers( //(1)!
            request: Empty,
            responseObserver: StreamObserver<io.koraframework.guide.grpcserver.advanced.UserResponse>
        ) {
            try {
                userStreamingService.getAllUsers().forEach { responseObserver.onNext(it.toGrpcUser()) }
                responseObserver.onCompleted()
            } catch (e: Exception) {
                responseObserver.onError(
                    Status.INTERNAL.withDescription("Failed to stream users").withCause(e).asRuntimeException()
                )
            }
        }

        override fun createUsers(responseObserver: StreamObserver<CreateUsersResponse>): StreamObserver<CreateUserRequest> { //(2)!
            return object : StreamObserver<CreateUserRequest> {
                private val requests = mutableListOf<UserRequest>()

                override fun onNext(value: CreateUserRequest) {
                    requests += UserRequest(value.name, value.email)
                }

                override fun onError(t: Throwable) { //(3)!
                    logger.error("Client streaming failed", t)
                    responseObserver.onError(t)
                }

                override fun onCompleted() {
                    try {
                        val createdUsers = userStreamingService.createUsers(requests)
                        responseObserver.onNext(
                            CreateUsersResponse.newBuilder()
                                .setCreatedCount(createdUsers.size)
                                .addAllUserIds(createdUsers.map { it.id })
                                .build()
                        )
                        responseObserver.onCompleted()
                    } catch (e: Exception) {
                        responseObserver.onError(
                            Status.INTERNAL.withDescription("Failed to create users").withCause(e).asRuntimeException()
                        )
                    }
                }
            }
        }

        override fun updateUsers(responseObserver: StreamObserver<io.koraframework.guide.grpcserver.advanced.UserResponse>): StreamObserver<UpdateUserRequest> { //(4)!
            return object : StreamObserver<UpdateUserRequest> {
                override fun onNext(value: UpdateUserRequest) {
                    try {
                        val user = userStreamingService.tryUpdateUser(value.userId, UserRequest(value.name, value.email))
                            ?: throw Status.NOT_FOUND.withDescription("User not found: ${value.userId}")
                                .asRuntimeException()
                        responseObserver.onNext(user.toGrpcUser())
                    } catch (e: StatusRuntimeException) {
                        responseObserver.onError(e)
                    }
                }

                override fun onError(t: Throwable) {
                    logger.error("Bidirectional streaming failed", t)
                    responseObserver.onError(t)
                }

                override fun onCompleted() {
                    responseObserver.onCompleted()
                }
            }
        }
    }
    ```

    1. Серверный поток: много `onNext`, затем ровно один `onCompleted`.
    2. Клиентский поток: метод возвращает наблюдателя, в которого gRPC будет проталкивать запросы; ответ формируется только в `onCompleted`.
    3. `onError` у наблюдателя *запросов* означает, что клиент прервал вызов, — обработчик должен остановиться и закрыть сторону ответов тоже.
    4. Двунаправленный поток: на каждое входящее сообщение отвечают сразу, поэтому ответы чередуются с запросами.

    Теперь одно и то же преобразование DTO в protobuf нужно двум обработчикам, поэтому в Kotlin-варианте оно выносится из класса в одну internal-функцию-расширение:

    ```kotlin title="src/main/kotlin/io/koraframework/guide/grpcserver/advanced/grpc/GrpcMappers.kt"
    package io.koraframework.guide.grpcserver.advanced.grpc

    import com.google.protobuf.Timestamp
    import io.koraframework.guide.grpcserver.advanced.dto.UserResponse
    import java.time.ZoneOffset

    internal fun UserResponse.toGrpcUser(): io.koraframework.guide.grpcserver.advanced.UserResponse {
        return io.koraframework.guide.grpcserver.advanced.UserResponse.newBuilder()
            .setId(id)
            .setName(name)
            .setEmail(email)
            .setCreatedAt(
                Timestamp.newBuilder()
                    .setSeconds(createdAt.toEpochSecond(ZoneOffset.UTC))
                    .setNanos(createdAt.nano)
                    .build()
            )
            .build()
    }
    ```

Регистрация работает ровно как в базовом руководстве: обработчик — обычный `@Component`, наследующий сгенерированный `...ImplBase`, поэтому в графе он является `BindableService`, а Kora добавляет на
сервер каждый найденный `BindableService`. Ни аннотации `@GrpcService`, ни ручного `addService` нет, и никаких особых действий, чтобы вторая служба ужилась с первой, не требуется.

Правила, которые делают потоковые обработчики корректными, стоит назвать явно:

- ровно один завершающий сигнал на вызов — либо `onCompleted()`, либо `onError(...)`, никогда оба и никогда ни одного
- исключение, вышедшее наружу без сообщения через наблюдателя, закрывается gRPC как `UNKNOWN`, что ничего полезного вызывающей стороне не говорит
- `onError` у наблюдателя запросов — это прерывание со стороны клиента, а не сбой сервера; залогируйте его и закройте свою сторону

## Серверный перехватчик { #server-interceptor }

Подробнее о серверных gRPC-перехватчиках и о том, как они связываются, — в разделе [gRPC-сервер: перехватчики](../documentation/grpc-server.md#interceptors).

Перехватчики — это gRPC-аналог транспортного промежуточного слоя. Это хорошее место для задач, которые должны оставаться вне бизнес-логики:

- логирование
- аутентификация
- трассировка
- ограничение частоты

В отличие от [HTTP-сервера](../documentation/http-server.md#interceptors), у модуля gRPC-сервера **нет** аннотации `@InterceptWith` и нет тега на службу. Каждый `ServerInterceptor`, зарегистрированный
как `@Component`, применяется **глобально** ко всем службам сервера.

Продвинутый модуль вводит простой перехватчик логирования:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/grpcserver/advanced/grpc/LoggingInterceptor.java"
    package io.koraframework.guide.grpcserver.advanced.grpc;

    import io.grpc.Metadata;
    import io.grpc.ServerCall;
    import io.grpc.ServerCallHandler;
    import io.grpc.ServerInterceptor;
    import org.slf4j.Logger;
    import org.slf4j.LoggerFactory;
    import io.koraframework.common.annotation.Component;

    @Component //(1)!
    public final class LoggingInterceptor implements ServerInterceptor {

        private static final Logger logger = LoggerFactory.getLogger(LoggingInterceptor.class);

        @Override
        public <ReqT, RespT> ServerCall.Listener<ReqT> interceptCall(
                ServerCall<ReqT, RespT> call,
                Metadata headers,
                ServerCallHandler<ReqT, RespT> next) {
            logger.info("Incoming gRPC request: method={}", call.getMethodDescriptor().getFullMethodName());
            return next.startCall(call, headers); //(2)!
        }
    }
    ```

    1. Ни тега, ни аннотации — достаточно обычного компонента, и он применяется ко всем службам сервера.
    2. Передает вызов дальше; если вернуться, не вызвав `startCall`, вы обязаны закрыть вызов сами.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/grpcserver/advanced/grpc/LoggingInterceptor.kt"
    package io.koraframework.guide.grpcserver.advanced.grpc

    import io.grpc.Metadata
    import io.grpc.ServerCall
    import io.grpc.ServerCallHandler
    import io.grpc.ServerInterceptor
    import org.slf4j.LoggerFactory
    import io.koraframework.common.annotation.Component

    @Component //(1)!
    class LoggingInterceptor : ServerInterceptor {

        private val logger = LoggerFactory.getLogger(LoggingInterceptor::class.java)

        override fun <ReqT : Any?, RespT : Any?> interceptCall(
            call: ServerCall<ReqT, RespT>,
            headers: Metadata,
            next: ServerCallHandler<ReqT, RespT>
        ): ServerCall.Listener<ReqT> {
            logger.info("Incoming gRPC request: method={}", call.methodDescriptor.fullMethodName)
            return next.startCall(call, headers) //(2)!
        }
    }
    ```

    1. Ни тега, ни аннотации — достаточно обычного компонента, и он применяется ко всем службам сервера.
    2. Передает вызов дальше; если вернуться, не вызвав `startCall`, вы обязаны закрыть вызов сами.

Kora регистрирует у построителя сначала ваши перехватчики, а свой перехватчик телеметрии — последним. gRPC вызывает перехватчики в обратном порядке регистрации, поэтому входящий вызов обрабатывается так:

```
TelemetryInterceptor -> your interceptors -> handler
```

Такой порядок означает, что телеметрия наблюдает финальный `Status` вызова, включая ошибки, порожденные вашими перехватчиками, а наблюдение и контекст `OpenTelemetry` уже установлены, когда выполняется
ваш код. Если ваших перехватчиков несколько, они выполняются в порядке, обратном их регистрации в графе, — не стройте на этом логику.

Этот перехватчик живет только в продвинутом модуле, поэтому базовое руководство остается сфокусированным на основах.

## Рефлексия сервера { #server-reflection }

Рефлексия полезна при разработке, потому что позволяет инструментам исследовать gRPC-сервер без предварительной ручной сборки заранее сгенерированного клиента.

В Kora для нее нужны две вещи: добавленная выше зависимость `io.grpc:grpc-services` и один флаг конфигурации. Kora добавляет службу рефлексии, только когда в classpath присутствует
`io.grpc.protobuf.services.ProtoReflectionServiceV1`, поэтому одной конфигурации недостаточно.

Полный справочник по конфигурации смотрите в [gRPC-сервере](../documentation/grpc-server.md).

===! ":material-code-json: `Hocon`"

    ```javascript title="src/main/resources/application.conf"
    grpcServer {
      port = 8092 //(1)!
      reflectionEnabled = true //(2)!
      telemetry.logging.enabled = true //(3)!
    }

    logging {
      levels {
        "ROOT": "WARN" //(4)!
        "io.koraframework": "INFO" //(5)!
        "io.koraframework.guide.grpcserver.advanced": "INFO" //(6)!
      }
    }
    ```

    1. Порт gRPC-сервера (по умолчанию: `8090`); продвинутое приложение использует `8092`, чтобы работать рядом с сервером из базового руководства.
    2. Включает службу gRPC Server Reflection (по умолчанию: `false`).
    3. Включает логирование gRPC-вызовов для этого сервера (по умолчанию: `false`).
    4. Уровень логирования для `ROOT`.
    5. Уровень логирования для `io.koraframework`.
    6. Уровень логирования для `io.koraframework.guide.grpcserver.advanced`.

=== ":simple-yaml: `YAML`"

    ```yaml title="src/main/resources/application.yaml"
    grpcServer:
      port: 8092 #(1)!
      reflectionEnabled: true #(2)!
      telemetry:
        logging:
          enabled: true #(3)!
    logging:
      levels:
        ROOT: "WARN" #(4)!
        "io.koraframework": "INFO" #(5)!
        "io.koraframework.guide.grpcserver.advanced": "INFO" #(6)!
    ```

    1. Порт gRPC-сервера (по умолчанию: `8090`); продвинутое приложение использует `8092`, чтобы работать рядом с сервером из базового руководства.
    2. Включает службу gRPC Server Reflection (по умолчанию: `false`).
    3. Включает логирование gRPC-вызовов для этого сервера (по умолчанию: `false`).
    4. Уровень логирования для `ROOT`.
    5. Уровень логирования для `io.koraframework`.
    6. Уровень логирования для `io.koraframework.guide.grpcserver.advanced`.

Все остальное имеет рабочие значения по умолчанию: размер входящего сообщения ограничен `4MiB`, мягкое завершение ждет `30s`, а ограничения возраста соединения и keepalive выключены, пока не заданы.

С включенной рефлексией `grpcurl` больше не нужны `-import-path`/`-proto`:

```bash
grpcurl -plaintext localhost:8092 list
grpcurl -plaintext localhost:8092 describe io.koraframework.guide.grpcserver.advanced.UserStreamingService
```

Почему это важно:

- `grpcurl` проще обнаруживает службы
- локальная отладка становится проще
- продвинутое руководство может показать более дружественную к инструментам настройку сервера

Рефлексия описывает *все* службы сервера — именно то, что нужно локально, и обычно не то, что нужно на публичном продуктивном порту.

## Авторизация по API-ключу { #api-key }

Продвинутый модуль вводит еще и серверный перехватчик аутентификации, но только для потоковой службы.

Это важно с методической точки зрения:

- унарный CRUD остается простым для понимания
- защищенная область четко ограничена продвинутым API

Поскольку каждый `ServerInterceptor` глобален, «только для потоковой службы» — это решение, которое перехватчик принимает во время выполнения, анализируя
`call.getMethodDescriptor().getServiceName()` и сравнивая его со сгенерированной константой `UserStreamingServiceGrpc.SERVICE_NAME`.

Конфигурация — она попадает в тот же `application.conf`, что и блок выше:

===! ":material-code-json: `Hocon`"

    ```javascript title="src/main/resources/application.conf"
    auth.apiKey.value = ${?GRPC_STREAMING_API_KEY} //(1)!
    ```

    1. API-ключ, которого требует потоковая служба; читается из переменной окружения `GRPC_STREAMING_API_KEY`. Значения по умолчанию нет намеренно: приложение лучше не стартует, чем поднимется незащищенным.

=== ":simple-yaml: `YAML`"

    ```yaml title="src/main/resources/application.yaml"
    auth:
      apiKey:
        value: ${?GRPC_STREAMING_API_KEY} #(1)!
    ```

    1. API-ключ, которого требует потоковая служба; читается из переменной окружения `GRPC_STREAMING_API_KEY`. Значения по умолчанию нет намеренно: приложение лучше не стартует, чем поднимется незащищенным.

Значение читается через небольшой интерфейс `@ConfigSource`:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/grpcserver/advanced/grpc/UserStreamingAuthConfig.java"
    package io.koraframework.guide.grpcserver.advanced.grpc;

    import io.koraframework.config.common.annotation.ConfigSource;

    @ConfigSource("auth.apiKey")
    public interface UserStreamingAuthConfig {

        String value();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/grpcserver/advanced/grpc/UserStreamingAuthConfig.kt"
    package io.koraframework.guide.grpcserver.advanced.grpc

    import io.koraframework.config.common.annotation.ConfigSource

    @ConfigSource("auth.apiKey")
    interface UserStreamingAuthConfig {
        fun value(): String
    }
    ```

Перехватчик:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/grpcserver/advanced/grpc/UserStreamingAuthInterceptor.java"
    package io.koraframework.guide.grpcserver.advanced.grpc;

    import io.grpc.Metadata;
    import io.grpc.ServerCall;
    import io.grpc.ServerCallHandler;
    import io.grpc.ServerInterceptor;
    import io.grpc.Status;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.grpcserver.advanced.UserStreamingServiceGrpc;

    @Component
    public final class UserStreamingAuthInterceptor implements ServerInterceptor {

        private static final Metadata.Key<String> AUTHORIZATION_HEADER =
                Metadata.Key.of("authorization", Metadata.ASCII_STRING_MARSHALLER);

        private final UserStreamingAuthConfig config;

        public UserStreamingAuthInterceptor(UserStreamingAuthConfig config) {
            this.config = config;
        }

        @Override
        public <ReqT, RespT> ServerCall.Listener<ReqT> interceptCall(
                ServerCall<ReqT, RespT> call,
                Metadata headers,
                ServerCallHandler<ReqT, RespT> next) {
            if (!UserStreamingServiceGrpc.SERVICE_NAME.equals(call.getMethodDescriptor().getServiceName())) { //(1)!
                return next.startCall(call, headers);
            }

            var authorization = headers.get(AUTHORIZATION_HEADER);
            if (!this.config.value().equals(authorization)) {
                call.close(Status.UNAUTHENTICATED.withDescription("Invalid API key"), new Metadata()); //(2)!
                return new ServerCall.Listener<>() {}; //(3)!
            }

            return next.startCall(call, headers);
        }
    }
    ```

    1. Ограничение области происходит здесь, во время выполнения: унарные вызовы `UserService` проходят насквозь.
    2. Отклонить вызов — значит закрыть его со `Status`; обработчик не вызывается вовсе.
    3. Пустого слушателя все равно нужно вернуть: gRPC требует слушателя даже для только что закрытого вызова.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/grpcserver/advanced/grpc/UserStreamingAuthInterceptor.kt"
    package io.koraframework.guide.grpcserver.advanced.grpc

    import io.grpc.*
    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.grpcserver.advanced.UserStreamingServiceGrpc

    @Component
    class UserStreamingAuthInterceptor(
        private val config: UserStreamingAuthConfig
    ) : ServerInterceptor {

        override fun <ReqT : Any?, RespT : Any?> interceptCall(
            call: ServerCall<ReqT, RespT>,
            headers: Metadata,
            next: ServerCallHandler<ReqT, RespT>
        ): ServerCall.Listener<ReqT> {
            if (UserStreamingServiceGrpc.SERVICE_NAME != call.methodDescriptor.serviceName) { //(1)!
                return next.startCall(call, headers)
            }

            val authorization = headers.get(AUTHORIZATION_HEADER)
            if (config.value() != authorization) {
                call.close(Status.UNAUTHENTICATED.withDescription("Invalid API key"), Metadata()) //(2)!
                return object : ServerCall.Listener<ReqT>() {} //(3)!
            }
            return next.startCall(call, headers)
        }

        companion object {
            private val AUTHORIZATION_HEADER: Metadata.Key<String> =
                Metadata.Key.of("authorization", Metadata.ASCII_STRING_MARSHALLER)
        }
    }
    ```

    1. Ограничение области происходит здесь, во время выполнения: унарные вызовы `UserService` проходят насквозь.
    2. Отклонить вызов — значит закрыть его со `Status`; обработчик не вызывается вовсе.
    3. Пустого слушателя все равно нужно вернуть: gRPC требует слушателя даже для только что закрытого вызова.

Это gRPC-аналог защищенных продвинутых эндпоинтов, которые мы вводили в продвинутом руководстве по HTTP. Учетные данные едут в начальных `Metadata` вызова, которые читаются один раз при его старте, —
поэтому та же проверка покрывает и долгоживущий потоковый вызов, и унарный.

## Запуск приложения { #run-app }

Скомпилируйте:

```bash
./gradlew clean classes
```

Запустите, передав API-ключ, которого требует потоковая служба:

```bash
GRPC_STREAMING_API_KEY=test-api-key ./gradlew run
```

Теперь унарная служба доступна на порту `8092` без учетных данных, а потоковая служба дополнительно ожидает:

- заголовок метаданных `authorization`
- значение, равное `GRPC_STREAMING_API_KEY`

С включенной рефлексией быстрая ручная проверка не требует `.proto`-файла:

```bash
grpcurl -plaintext -H "authorization: test-api-key" \
  localhost:8092 io.koraframework.guide.grpcserver.advanced.UserStreamingService/GetAllUsers
```

## Тестирование { #testing }

Сопровождающее приложение использует `@KoraAppTest`, который поднимает весь граф — включая настоящий gRPC-сервер на настоящем порту — и затем обращается к нему через обычный `ManagedChannel`. API-ключ
приходит из тестового `application.conf`, поэтому тест не зависит от окружения разработчика.

Запустите тесты модуля:

```bash
./gradlew test
```

Тесты покрывают:

- унарный CRUD
- серверную потоковую передачу
- клиентскую потоковую передачу
- двунаправленную потоковую передачу
- неавторизованный доступ к защищенной потоковой службе с проверкой `Status.Code.UNAUTHENTICATED`

Авторизованные потоковые вызовы добавляют ключ через `MetadataUtils.newAttachHeadersInterceptor(metadata)` — это клиентское зеркало серверного перехватчика выше.

## Лучшие практики { #best-practices }

- Держите продвинутые потоковые методы в отдельной службе, когда это улучшает ясность.
- Не запихивайте каждую возможность в одну гигантскую protobuf-службу.
- Держите унарный CRUD стабильным, добавляя вокруг него более продвинутые транспортные шаблоны.
- Используйте перехватчики для сквозных транспортных задач, а не для бизнес-логики.
- Помните, что любой `ServerInterceptor` глобален; ограничивайте его область в коде через `getMethodDescriptor().getServiceName()`.
- Отправляйте ровно один завершающий сигнал на потоковый вызов и всегда отображайте сбои на явный `Status`.
- Включайте рефлексию в модулях, ориентированных на разработку, где помогает поддержка инструментов, и дважды подумайте о публичном продуктивном порту.
- Держите все артефакты `io.grpc` на той версии, которая поставляется с `io.koraframework:grpc-server`.
- Помечайте написанные вручную DTO аннотацией `@Json` только тогда, когда они пересекают HTTP/JSON-границу; сгенерированным protobuf-сообщениям JSON-аннотации не нужны.

## Итоги { #summary }

В этом руководстве вы сохранили исходную унарную gRPC-службу нетронутой и добавили поверх нее вторую, явно продвинутую потоковую службу.

Это дало более чистую архитектуру и лучший ход обучения:

- базовая служба для знакомого CRUD
- отдельная потоковая служба для продвинутых шаблонов gRPC
- перехватчики, рефлексия и аутентификация только там, где они приносят реальную пользу

## Ключевые понятия { #key-concepts }

- почему потокам во многих случаях стоит выделить собственную границу службы
- как серверная, клиентская и двунаправленная потоковая передача выглядят в сгенерированных gRPC-обработчиках
- почему каждому потоковому вызову нужен ровно один завершающий сигнал
- как серверные перехватчики регистрируются в приложениях Kora глобально и ограничиваются в коде
- как цепочка перехватчиков упорядочивает ваши перехватчики относительно телеметрии
- как защитить службу аутентификацией по API-ключу в метаданных
- как рефлексия помогает локальному исследованию и отладке

## Устранение неполадок { #troubleshooting }

**Потоковые методы не генерируются:**

Перегенерируйте исходники через `./gradlew clean classes` после правки `.proto`-файла и проверьте, что потоковая служба находится в том же исходном наборе.

**Потоковый вызов зависает:**

Скорее всего, обработчик так и не отправил завершающий сигнал. Каждая ветка должна заканчиваться ровно одним `onCompleted()` или `onError(...)`.

**Защищенные вызовы всегда отклоняются:**

Убедитесь, что `GRPC_STREAMING_API_KEY` задан и что клиент отправляет заголовок метаданных `authorization`, которого ждет перехватчик.

**Перехватчик блокирует и унарные вызовы:**

Компоненты `ServerInterceptor` глобальны. Проверьте сравнение с `SERVICE_NAME` — без него перехватчик охраняет все службы сервера.

**Рефлексия не работает:**

Проверьте `grpcServer.reflectionEnabled = true` и наличие `io.grpc:grpc-services` в classpath компиляции. Без этого артефакта Kora молча пропускает службу рефлексии.

**Тесты падают с `AbstractMethodError` и упоминанием `buildClientTransportServers`:**

Артефакт gRPC в тестовой области зафиксирован на версии, отличной от среды выполнения из `io.koraframework:grpc-server`. Приведите все зависимости `io.grpc` к версии `1.83.1`.

## Что дальше? { #whats-next }

- [HTTP-клиент](http-client.md), если вы еще его не проходили.
- [gRPC-клиент](grpc-client.md), если хочется сначала вспомнить базовый унарный клиент.
- [Продвинутый gRPC-клиент](grpc-client-advanced.md) после gRPC-клиента, чтобы потреблять потоковую службу и защищенные метаданными вызовы.
- [Наблюдаемость](observability.md), чтобы наблюдать за потоковыми RPC, перехватчиками и поведением сервера.
- [Устойчивые шаблоны](resilient.md), чтобы защитить клиентов, вызывающих продвинутые gRPC-службы.

## Помощь { #help }

Если что-то не работает:

- сравните с [Kora Java gRPC Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-grpc-server-advanced-app) и [Kora Kotlin gRPC Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-grpc-server-advanced-app)
- проверьте [документацию gRPC-сервера](../documentation/grpc-server.md)
- убедитесь, что вы перегенерировали исходники после изменения `.proto`-контракта
- убедитесь, что `GRPC_STREAMING_API_KEY` задан перед тестированием защищенных вызовов
