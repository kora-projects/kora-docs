---
search:
  exclude: true
title: Продвинутый gRPC-сервер с Kora
summary: Extend a Kora gRPC server with streaming RPCs, server interceptors, API-key auth, and reflection
tags: grpc-server, protobuf, streaming, interceptors, reflection, authentication
---

# Продвинутый gRPC-сервер с Kora { #advanced-grpc-server-kora }

Это руководство знакомит с продвинутыми возможностями gRPC-сервера в Kora. В нем рассматриваются серверная потоковая передача, клиентская потоковая передача, двунаправленная потоковая передача,
перехватчики на уровне службы, авторизация по метаданным и рефлексия для локальных инструментов. Вы также увидите, как потоковые обработчики используют наблюдателей и сигналы завершения, а унарные
службы при этом остаются доступными в том же графе приложения.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java gRPC Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-grpc-server-advanced-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin gRPC Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-grpc-server-advanced-app).

## Что вы создадите { #youll-build }

Вы расширите приложение gRPC-сервера:

- второй protobuf-службой `UserStreamingService`, отделенной от унарной CRUD-службы
- RPC `GetAllUsers` с серверной потоковой передачей
- RPC `CreateUsers` с клиентской потоковой передачей
- RPC `UpdateUsers` с двунаправленной потоковой передачей
- gRPC-обработчиком Kora, который использует наблюдателей, сигналы завершения и обработку ошибок потока
- серверным перехватчиком журналирования
- авторизацией по API-ключу из метаданных для потоковой службы
- включенной gRPC-рефлексией для локального изучения через инструменты вроде `grpcurl`

## Что понадобится { #youll-need }

- JDK 17 или новее
- Gradle 7+
- текстовый редактор или среда разработки
- необязательно: `grpcurl` для рефлексии и ручных проверок потоковой передачи

## Требования { #prerequisites }

!!! note "Обязательно: пройдите базовое руководство по gRPC-серверу"

    Это руководство предполагает, что вы уже прошли **[gRPC-сервер с Kora](grpc-server.md)** и **[Продвинутый HTTP-сервер](http-server-advanced.md)**, а также уже понимаете унарные gRPC-обработчики, генерацию protobuf-кода и разделение репозитория и службы, которое используется в руководствах.

    Если вы еще не прошли базовое руководство по gRPC-серверу, сначала сделайте это, потому что здесь унарная служба остается стабильной, а вокруг нее добавляются потоковая передача, рефлексия, перехватчики и авторизация по метаданным.

## Обзор { #overview }

Самое важное проектное решение в этом руководстве: мы **не перегружаем исходную унарную службу** всеми продвинутыми понятиями.

Вместо этого:

- `UserService` остается знакомой унарной CRUD-службой
- `UserStreamingService` становится отдельной продвинутой службой в `.proto`-договоре
- `UserStreamingServiceGrpcHandler` сосредоточен только на потоковых операциях

Такое разделение упрощает обучение и отражает распространенный промышленный подход: держать базовый синхронный API стабильным и добавлять специализированные потоковые API только там, где они
действительно помогают.

Kora по-прежнему отвечает за связывание компонентов и жизненный цикл. gRPC отвечает за RPC-протокол и сгенерированные договоры служб. Ваш код находится между ними: он реализует сгенерированные методы
служб, внедряет обычные компоненты Kora и переводит потоковые обратные вызовы в поведение приложения.

У продвинутых частей этого руководства разные ответственности:

- потоковая передача меняет форму и время жизни RPC-вызова
- перехватчики добавляют сквозное поведение вокруг вызовов
- рефлексия открывает метаданные служб для инструментов вроде `grpcurl`
- авторизация по метаданным читает метаданные запроса до запуска бизнес-логики

Все эти возможности относятся к транспортному уровню. Они важны, но не должны заставлять репозиторий или слой служб знать о внутренних деталях gRPC. Слой служб должен по-прежнему говорить в терминах
приложения: пользователи, запросы, ответы и бизнес-правила. gRPC-обработчик - это адаптер, который превращает сгенерированные protobuf-сообщения и потоковые обратные вызовы в операции приложения.

Такое разделение в потоковом коде важнее, чем в унарном. Унарный обработчик получает один запрос, вызывает метод службы и возвращает один ответ. Потоковый обработчик владеет более долгим
взаимодействием:

- он может отправить несколько ответов перед завершением
- он может получить несколько запросов перед созданием итогового ответа
- он должен решить, когда вызывать `onNext`, `onCompleted` или `onError`
- он должен учитывать отмену, обратное давление и частичный отказ

Руководство намеренно сохраняет реализацию небольшой, но архитектура повторяет промышленный код: оставьте стабильный унарный API нетронутым, добавьте отдельную потоковую службу и разместите
продвинутую механику gRPC на краю приложения.

### Зачем существует потоковая передача gRPC { #grpc-streaming-exists }

Унарный RPC отлично подходит, когда один запрос естественно порождает один ответ.

Но иногда сам транспорт должен выражать другую форму диалога:

- один запрос, много ответов
- много запросов, один ответ
- много запросов, много ответов

Именно это и дает потоковая передача.

### Серверная потоковая передача { #server-streaming }

Клиент отправляет один запрос, а сервер возвращает много сообщений.

Это полезно, когда:

- нужно передавать большой набор результатов
- клиент может начать обрабатывать результаты сразу
- данные естественно приходят как последовательность

### Клиентская потоковая передача { #client-streaming }

Клиент отправляет много сообщений, а сервер отвечает один раз в конце.

Это полезно, когда:

- клиент группирует операции
- сервер должен накопить работу перед ответом
- один сводный ответ полезнее множества маленьких подтверждений

### Двунаправленная потоковая передача { #bidirectional-streaming }

Клиент и сервер обмениваются несколькими сообщениями в рамках одного вызова.

Это полезно, когда:

- диалог интерактивный
- обновления должны идти в обе стороны
- одна сторона не должна ждать, пока другая сначала отправит все

## Неизменяемое { #immutable }

Перед добавлением новых частей запомните, что **не меняется**:

- `UserRepository`
- `InMemoryUserRepository`
- `UserService`
- унарный `UserServiceGrpcHandler`

Это сделано намеренно. Продвинутые возможности должны расширять приложение, а не заставлять переписывать базовый путь, которому вы уже доверяете.

## API в Protobuf { #protobuf-api }

Теперь расширьте договор второй службой вместо того, чтобы смешивать все в исходной.

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

Такая форма важна для обучения:

- `UserService` по-прежнему похожа на HTTP CRUD API
- `UserStreamingService` становится явно продвинутой частью

## Потоковый сервис { #streaming-service }

Так же как мы разделили транспортный договор, мы разделяем и логику приложения.

Продвинутый модуль вводит:

- `UserStreamingService`

Эта служба отвечает за логику:

- возврата всех пользователей для серверной потоковой передачи
- создания многих пользователей для клиентской потоковой передачи
- обновления пользователей для двунаправленной потоковой передачи

Это сохраняет исходный `UserService` близким к HTTP-руководству и не дает ему превратиться в транспортно-специфичный огромный класс.

## Потоковый обработчик { #streaming-handler }

Теперь соедините сгенерированную потоковую службу с новой службой приложения.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/grpcserver/advanced/grpc/UserStreamingServiceGrpcHandler.java"
    package ru.tinkoff.kora.guide.grpcserver.advanced.grpc;

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
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.grpcserver.advanced.CreateUserRequest;
    import ru.tinkoff.kora.guide.grpcserver.advanced.CreateUsersResponse;
    import ru.tinkoff.kora.guide.grpcserver.advanced.UpdateUserRequest;
    import ru.tinkoff.kora.guide.grpcserver.advanced.UserResponse;
    import ru.tinkoff.kora.guide.grpcserver.advanced.UserStreamingServiceGrpc;
    import ru.tinkoff.kora.guide.grpcserver.advanced.dto.UserRequest;
    import ru.tinkoff.kora.guide.grpcserver.advanced.service.UserStreamingService;

    @Component
    public final class UserStreamingServiceGrpcHandler extends UserStreamingServiceGrpc.UserStreamingServiceImplBase {

        private static final Logger logger = LoggerFactory.getLogger(UserStreamingServiceGrpcHandler.class);

        private final UserStreamingService userStreamingService;

        public UserStreamingServiceGrpcHandler(UserStreamingService userStreamingService) {
            this.userStreamingService = userStreamingService;
        }

        @Override
        public void getAllUsers(Empty request, StreamObserver<UserResponse> responseObserver) {
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
        public StreamObserver<CreateUserRequest> createUsers(StreamObserver<CreateUsersResponse> responseObserver) {
            return new StreamObserver<>() {
                private final List<UserRequest> requests = new ArrayList<>();

                @Override
                public void onNext(CreateUserRequest value) {
                    requests.add(new UserRequest(value.getName(), value.getEmail()));
                }

                @Override
                public void onError(Throwable t) {
                    logger.error("Client streaming failed", t);
                    responseObserver.onError(t);
                }

                @Override
                public void onCompleted() {
                    try {
                        var createdUsers = userStreamingService.createUsers(requests);
                        responseObserver.onNext(CreateUsersResponse.newBuilder()
                                .setCreatedCount(createdUsers.size())
                                .addAllUserIds(createdUsers.stream().map(ru.tinkoff.kora.guide.grpcserver.advanced.dto.UserResponse::id).toList())
                                .build());
                        responseObserver.onCompleted();
                    } catch (Exception e) {
                        responseObserver.onError(Status.INTERNAL.withDescription("Failed to create users").withCause(e).asRuntimeException());
                    }
                }
            };
        }

        @Override
        public StreamObserver<UpdateUserRequest> updateUsers(StreamObserver<UserResponse> responseObserver) {
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

        private UserResponse toGrpcUser(ru.tinkoff.kora.guide.grpcserver.advanced.dto.UserResponse user) {
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

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/grpcserver/advanced/grpc/UserStreamingServiceGrpcHandler.kt"
    package ru.tinkoff.kora.guide.grpcserver.advanced.grpc

    import com.google.protobuf.Empty
    import io.grpc.Status
    import io.grpc.StatusRuntimeException
    import io.grpc.stub.StreamObserver
    import org.slf4j.LoggerFactory
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.grpcserver.advanced.CreateUserRequest
    import ru.tinkoff.kora.guide.grpcserver.advanced.CreateUsersResponse
    import ru.tinkoff.kora.guide.grpcserver.advanced.UpdateUserRequest
    import ru.tinkoff.kora.guide.grpcserver.advanced.UserStreamingServiceGrpc
    import ru.tinkoff.kora.guide.grpcserver.advanced.dto.UserRequest
    import ru.tinkoff.kora.guide.grpcserver.advanced.service.UserStreamingService

    @Component
    class UserStreamingServiceGrpcHandler(
        private val userStreamingService: UserStreamingService
    ) : UserStreamingServiceGrpc.UserStreamingServiceImplBase() {

        private val logger = LoggerFactory.getLogger(UserStreamingServiceGrpcHandler::class.java)

        override fun getAllUsers(
            request: Empty,
            responseObserver: StreamObserver<ru.tinkoff.kora.guide.grpcserver.advanced.UserResponse>
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

        override fun createUsers(responseObserver: StreamObserver<CreateUsersResponse>): StreamObserver<CreateUserRequest> {
            return object : StreamObserver<CreateUserRequest> {
                private val requests = mutableListOf<UserRequest>()

                override fun onNext(value: CreateUserRequest) {
                    requests += UserRequest(value.name, value.email)
                }

                override fun onError(t: Throwable) {
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

        override fun updateUsers(responseObserver: StreamObserver<ru.tinkoff.kora.guide.grpcserver.advanced.UserResponse>): StreamObserver<UpdateUserRequest> {
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

Один этот класс показывает все три формы потоковой передачи:

- `getAllUsers()` показывает серверную потоковую передачу
- `createUsers()` показывает клиентскую потоковую передачу
- `updateUsers()` показывает двунаправленную потоковую передачу

## Серверный перехватчик { #server-interceptor }

Подробнее о серверных gRPC-перехватчиках и их подключении смотрите в разделе [gRPC Server: перехватчики](../documentation/grpc-server.md#interceptors).

Перехватчики - это gRPC-аналог транспортного промежуточного слоя. Это хорошее место для задач, которые должны оставаться вне бизнес-логики:

- журналирование
- авторизация
- трассировка
- ограничение частоты запросов

Продвинутый модуль вводит простой перехватчик журналирования:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/grpcserver/advanced/grpc/LoggingInterceptor.java"
    package ru.tinkoff.kora.guide.grpcserver.advanced.grpc;

    import io.grpc.Metadata;
    import io.grpc.ServerCall;
    import io.grpc.ServerCallHandler;
    import io.grpc.ServerInterceptor;
    import org.slf4j.Logger;
    import org.slf4j.LoggerFactory;
    import ru.tinkoff.kora.common.Component;

    @Component
    public final class LoggingInterceptor implements ServerInterceptor {

        private static final Logger logger = LoggerFactory.getLogger(LoggingInterceptor.class);

        @Override
        public <ReqT, RespT> ServerCall.Listener<ReqT> interceptCall(
                ServerCall<ReqT, RespT> call,
                Metadata headers,
                ServerCallHandler<ReqT, RespT> next) {
            logger.info("Incoming gRPC request: method={}", call.getMethodDescriptor().getFullMethodName());
            return next.startCall(call, headers);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/grpcserver/advanced/grpc/LoggingInterceptor.kt"
    package ru.tinkoff.kora.guide.grpcserver.advanced.grpc

    import io.grpc.Metadata
    import io.grpc.ServerCall
    import io.grpc.ServerCallHandler
    import io.grpc.ServerInterceptor
    import org.slf4j.LoggerFactory
    import ru.tinkoff.kora.common.Component

    @Component
    class LoggingInterceptor : ServerInterceptor {

        private val logger = LoggerFactory.getLogger(LoggingInterceptor::class.java)

        override fun <ReqT : Any?, RespT : Any?> interceptCall(
            call: ServerCall<ReqT, RespT>,
            headers: Metadata,
            next: ServerCallHandler<ReqT, RespT>
        ): ServerCall.Listener<ReqT> {
            logger.info("Incoming gRPC request: method={}", call.methodDescriptor.fullMethodName)
            return next.startCall(call, headers)
        }
    }
    ```

Этот перехватчик живет только в продвинутом модуле, поэтому базовое руководство остается сфокусированным на первых принципах.

## Серверная рефлексия { #server-reflection }

Рефлексия полезна при разработке, потому что позволяет инструментам изучать gRPC-сервер без ручного подключения заранее сгенерированного клиента.

В Kora она включается просто конфигурацией:

Полный справочник по конфигурации смотрите в разделе [gRPC-сервер](../documentation/grpc-server.md).

===! ":material-code-json: `Hocon`"

    ```javascript title="src/main/resources/application.conf"
    grpcServer {
      port = 8092 //(1)!
      reflectionEnabled = true //(2)!
      telemetry.logging.enabled = true //(3)!
    }
    ```

    1. Сетевой порт, который использует этот сервер.
    2. Включает gRPC-рефлексию для инструментов вроде grpcurl.
    3. Включает возможность для этого раздела конфигурации.

=== ":simple-yaml: `YAML`"

    ```yaml title="src/main/resources/application.yaml"
    grpcServer:
      port: 8092 #(1)!
      reflectionEnabled: true #(2)!
      telemetry:
        logging:
          enabled: true #(3)!
    ```

    1. Сетевой порт, который использует этот сервер.
    2. Включает gRPC-рефлексию для инструментов вроде grpcurl.
    3. Включает возможность для этого раздела конфигурации.

Почему это важно:

- `grpcurl` может проще обнаруживать службы
- локальная отладка становится проще
- продвинутое руководство может показать настройку сервера, более удобную для инструментов

## Авторизация по ключу { #api-key }

Продвинутый модуль также вводит серверный перехватчик авторизации, но только для потоковой службы.

Это важно с педагогической точки зрения:

- сервисный CRUD остается простым для понимания
- защищенная область явно ограничена продвинутым API

Конфигурация:

Полный справочник по конфигурации смотрите в разделе [Конфигурация](../documentation/config.md).

===! ":material-code-json: `Hocon`"

    ```javascript title="src/main/resources/application.conf"
    auth.apiKey.value = ${?GRPC_STREAMING_API_KEY} //(1)!
    ```

    1. Настроенное значение, которое использует компонент руководства. Необязательное переопределение из `GRPC_STREAMING_API_KEY`.

=== ":simple-yaml: `YAML`"

    ```yaml title="src/main/resources/application.yaml"
    auth:
      apiKey:
        value: ${?GRPC_STREAMING_API_KEY} #(1)!
    ```

    1. Настроенное значение, которое использует компонент руководства. Необязательное переопределение из `GRPC_STREAMING_API_KEY`.

Перехватчик:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/grpcserver/advanced/grpc/UserStreamingAuthInterceptor.java"
    package ru.tinkoff.kora.guide.grpcserver.advanced.grpc;

    import io.grpc.Metadata;
    import io.grpc.ServerCall;
    import io.grpc.ServerCallHandler;
    import io.grpc.ServerInterceptor;
    import io.grpc.Status;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.grpcserver.advanced.UserStreamingServiceGrpc;

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
            if (!UserStreamingServiceGrpc.SERVICE_NAME.equals(call.getMethodDescriptor().getServiceName())) {
                return next.startCall(call, headers);
            }

            var authorization = headers.get(AUTHORIZATION_HEADER);
            if (!this.config.value().equals(authorization)) {
                call.close(Status.UNAUTHENTICATED.withDescription("Invalid API key"), new Metadata());
                return new ServerCall.Listener<>() {};
            }

            return next.startCall(call, headers);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/grpcserver/advanced/grpc/UserStreamingAuthInterceptor.kt"
    package ru.tinkoff.kora.guide.grpcserver.advanced.grpc

    import io.grpc.*
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.grpcserver.advanced.UserStreamingServiceGrpc

    @Component
    class UserStreamingAuthInterceptor(
        private val config: UserStreamingAuthConfig
    ) : ServerInterceptor {

        override fun <ReqT : Any?, RespT : Any?> interceptCall(
            call: ServerCall<ReqT, RespT>,
            headers: Metadata,
            next: ServerCallHandler<ReqT, RespT>
        ): ServerCall.Listener<ReqT> {
            if (UserStreamingServiceGrpc.SERVICE_NAME != call.methodDescriptor.serviceName) {
                return next.startCall(call, headers)
            }

            val authorization = headers.get(AUTHORIZATION_HEADER)
            if (config.value() != authorization) {
                call.close(Status.UNAUTHENTICATED.withDescription("Invalid API key"), Metadata())
                return object : ServerCall.Listener<ReqT>() {}
            }
            return next.startCall(call, headers)
        }

        companion object {
            private val AUTHORIZATION_HEADER: Metadata.Key<String> =
                Metadata.Key.of("authorization", Metadata.ASCII_STRING_MARSHALLER)
        }
    }
    ```

Это gRPC-аналог защищенных продвинутых конечных точек, которые мы ввели в продвинутом HTTP-руководстве.

## Запуск приложения { #run-app }

Скомпилируйте:

```bash
./gradlew clean classes
```

Запустите:

```bash
$env:GRPC_STREAMING_API_KEY="test-api-key"
./gradlew run
```

Теперь унарная служба доступна на порту `8092`, а потоковая служба дополнительно ожидает:

- заголовок метаданных `authorization`
- значение, равное `GRPC_STREAMING_API_KEY`

## Запуск тестов { #testing }

Запустите тесты модуля:

```bash
./gradlew test
```

Тесты сопутствующего приложения проверяют:

- сервисный CRUD
- серверную потоковую передачу
- клиентскую потоковую передачу
- двунаправленную потоковую передачу
- неавторизованный доступ к защищенной потоковой службе

## Лучшие практики { #best-practices }

- Держите продвинутые потоковые методы в отдельной службе, когда это повышает ясность.
- Не загоняйте каждую возможность в одну огромную protobuf-службу.
- Сохраняйте сервисный CRUD стабильным, добавляя вокруг него более продвинутые транспортные шаблоны.
- Используйте перехватчики для сквозных транспортных задач, а не для бизнес-логики.
- Ограничивайте область авторизации настолько узко, насколько возможно; не каждый метод обязан защищаться одинаково.
- Включайте рефлексию в модулях, ориентированных на разработку, где поддержка инструментов помогает.
- Помечайте написанные вручную DTO аннотацией `@Json` только тогда, когда они пересекают HTTP/JSON-границу; сгенерированным protobuf-сообщениям JSON-аннотации не нужны.

## Итоги { #summary }

В этом руководстве вы оставили исходную унарную gRPC-службу нетронутой и добавили поверх нее вторую, явно продвинутую потоковую службу.

Это дало более чистую архитектуру и лучший учебный поток:

- базовая служба для знакомого CRUD
- отдельная потоковая служба для продвинутых gRPC-шаблонов
- перехватчики, рефлексия и авторизация только там, где они дают реальную пользу

## Ключевые понятия { #key-concepts }

- почему потоковая передача во многих случаях заслуживает собственной границы службы
- как серверная, клиентская и двунаправленная потоковая передача выглядят в сгенерированных gRPC-обработчиках
- как серверные перехватчики работают в gRPC-приложениях Kora
- как защитить службу авторизацией по API-ключу из метаданных
- как рефлексия помогает локальному изучению и отладке

## Устранение неполадок { #troubleshooting }

**Потоковые методы не сгенерированы:**

Перегенерируйте исходники с помощью `./gradlew clean classes` после изменения `.proto`-файла и проверьте, что потоковая служба находится в том же наборе исходников.

**Защищенные вызовы всегда отклоняются:**

Убедитесь, что `GRPC_STREAMING_API_KEY` задан и что клиент отправляет заголовок метаданных `authorization`, который ожидает перехватчик.

**Рефлексия не работает:**

Проверьте `grpcServer.reflectionEnabled = true` в `application.conf` и подключите зависимость gRPC-служб в сборке.

## Что дальше? { #whats-next }

- [HTTP-клиент](http-client.md), если вы еще не проходили это руководство.
- [gRPC-клиент](grpc-client.md), если хотите сначала повторить базовый унарный клиент.
- [Продвинутый gRPC-клиент](grpc-client-advanced.md) после gRPC-клиента, чтобы вызывать потоковую службу и защищенные метаданными вызовы.
- [Наблюдаемость](observability.md), чтобы наблюдать за потоковыми RPC, перехватчиками и поведением сервера.
- [Шаблоны устойчивости](resilient.md), чтобы защитить клиентов, которые вызывают продвинутые gRPC-службы.

## Помощь { #help }

Если что-то не работает:

- сравните с [Kora Java gRPC Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-grpc-server-advanced-app) и [Kora Kotlin gRPC Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-grpc-server-advanced-app)
- проверьте [документацию gRPC-сервера](../documentation/grpc-server.md)
- убедитесь, что вы перегенерировали исходники после изменения `.proto`-договора
- убедитесь, что `GRPC_STREAMING_API_KEY` задан перед проверкой защищенных вызовов
