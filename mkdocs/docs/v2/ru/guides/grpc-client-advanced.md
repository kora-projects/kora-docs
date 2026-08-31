---
search:
  exclude: true
title: Продвинутый gRPC-клиент с Kora
summary: Build a Kora 2.0 streaming gRPC client with generated stubs, metadata auth, and tagged client interceptors
description: "Streaming Kora gRPC client: server, client and bidirectional streaming through the generated blocking and async stubs, StreamObserver lifecycles and completion signals, ClientInterceptor components scoped with @Tag(ServiceGrpc.class) for logging and metadata authorization, an API key read through @ConfigSource, the grpcClient.<Service> configuration section, and in-process streaming tests."
agent:
  use_when: "Use this file for questions about advanced Kora gRPC clients: server, client and bidirectional streaming with UserStreamingServiceGrpc stubs, StreamObserver with onCompleted and onError, @Tag(ServiceGrpc.class) on a ClientInterceptor, ForwardingClientCall and Metadata.Key authorization headers, interceptor ordering relative to telemetry and deadlines, Kotlin coroutine Flow stubs, and testing streaming clients with InProcessServerBuilder and ClientInterceptors.intercept."
tags: grpc-client, streaming, interceptors, authentication, protobuf
---

# Продвинутый gRPC-клиент с Kora { #advanced-grpc-client-kora }

В этом руководстве рассматриваются продвинутые приемы построения gRPC-клиента в Kora. Вы разберете серверные потоки, клиентские потоки, двунаправленные потоки, аутентификацию на основе метаданных и
клиентские перехватчики, ограниченные одной сгенерированной службой. Вы также увидите, как асинхронные наблюдатели, сигналы завершения и ошибки жизненного цикла потока отличают потоковые клиенты от
обычного кода «запрос-ответ».

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java gRPC Client Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-grpc-client-advanced-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin gRPC Client Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-grpc-client-advanced-app).

## Что вы создадите { #youll-build }

Вы расширите приложение gRPC-клиента:

- клиентской потоковой службой для `UserStreamingService`
- серверными потоковыми вызовами для `GetAllUsers`
- клиентскими потоковыми вызовами для `CreateUsers`
- двунаправленными потоковыми вызовами для `UpdateUsers`
- HTTP-маршрутами-триггерами, которые позволяют легко запустить каждый потоковый сценарий локально
- клиентским перехватчиком логирования, привязанным тегом к одной сгенерированной службе
- клиентским перехватчиком аутентификации, который отправляет API-ключ через gRPC-метаданные
- быстрыми in-process тестами, которые проверяют потоковое поведение без вручную запущенного сервера

## Что понадобится { #youll-need }

- JDK 25 или новее
- Gradle 9+ (эталонные приложения используют Gradle Wrapper `9.5.1`)
- текстовый редактор или среда разработки
- работающий продвинутый gRPC-сервер для проверок во время выполнения

Артефакты Kora собраны под Java 25, поэтому JDK, которым компилируется ваш код, должен быть версии 25 или новее.

## Требования { #prerequisites }

!!! note "Обязательно: пройдите руководство по продвинутому gRPC-серверу"

    Это руководство предполагает, что вы уже прошли **[gRPC-клиент с Kora](grpc-client.md)** и **[Продвинутый gRPC-сервер с Kora](grpc-server-advanced.md)** и понимаете сгенерированные унарные заглушки, protobuf-контракты и то, как Kora внедряет зависимости gRPC-клиента.

    Если вы еще не прошли руководство по продвинутому gRPC-серверу, сначала сделайте это, потому что здесь переиспользуется тот же потоковый контракт, а внимание сосредоточено на потоковых вызовах со стороны клиента.

## Обзор { #overview }

Как и продвинутое руководство по серверу, продвинутое руководство по клиенту построено вокруг разделения.

Мы **не** перегружаем исходный унарный клиент всеми продвинутыми задачами.

Вместо этого:

- базовый клиент остается сфокусированным на унарном CRUD через `UserService`
- продвинутый клиент сосредоточен на потоках через `UserStreamingService`

Такой подход упрощает оба руководства и совпадает с устройством сопровождающих приложений.

На стороне клиента продвинутые возможности gRPC влияют на поток управления сильнее, чем на внедрение зависимостей. Kora по-прежнему строит канал и регистрирует настроенные заглушки. Сгенерированные
заглушки по-прежнему выполняют RPC-вызовы. Меняется то, как код вашей службы управляет временем жизни вызова, потоками запросов, наблюдателями ответов, метаданными и сбоями.

Это руководство держит такие задачи явными:

- потоковые службы оборачивают сгенерированные асинхронные заглушки, а не выставляют их напрямую
- клиентские перехватчики добавляют сквозное поведение к исходящим вызовам
- авторизация по метаданным настраивается рядом с границей клиента
- HTTP-эндпоинты-триггеры — лишь локальный способ проверить потоковый клиент

У продвинутого клиента еще и другая модель сбоев по сравнению с унарным. В унарном вызове сбой обычно означает, что один запрос не дошел до одного ответа. В потоковом вызове сбой может произойти после
того, как часть сообщений уже отправлена или получена. Значит, служба-обертка должна считать завершение потока частью дизайна API, а не второстепенной деталью.

Поэтому в руководстве появляются явные клиентские методы для каждой формы потока:

- серверный поток ориентирован на чтение: вызвал один раз, потребляешь много ответов
- клиентский поток ориентирован на запись: отправил много запросов, дождался одной сводки
- двунаправленный поток ориентирован на диалог: отправляешь и получаешь независимо

Сгенерированная асинхронная заглушка мощная, но обычно она не та граница, которую хочется видеть во всем приложении. Она выставляет механику на колбэках: наблюдатели и сигналы завершения. Служба-обертка
Kora превращает эту механику в меньший API, который можно вызывать из контроллеров, заданий или других служб, не растаскивая gRPC-колбэки повсюду.

Метаданные и перехватчики относятся к той же границе. Они полезны для аутентификации, трассировки, идентификаторов запросов и логирования, но подключать их следует рядом со сгенерированным клиентом.
Так бизнес-код сосредоточен на выполняемой операции, а не на том, чем украшен каждый RPC на проводе.

### Как потоки меняют клиент { #streams-change-client }

Унарные gRPC-вызовы выглядят приятно просто:

- создать один запрос
- вызвать один метод
- получить один ответ

Потоки меняют эту модель. Они меняют и то, какая заглушка вам нужна: в Java унарные и серверные потоковые вызовы доступны на `BlockingStub`, а клиентские и двунаправленные существуют **только** на
асинхронной заглушке `Stub`. Поэтому потоковая служба ниже внедряет обе.

### Серверный поток { #server-stream }

При серверной потоковой передаче клиент отправляет один запрос и получает много ответов.

Значит, клиентский код должен думать про:

- обход потока сообщений
- частичный прогресс
- момент, когда поток завершился

На блокирующей заглушке эта форма выглядит как `Iterator<T>`, который блокируется между сообщениями, — самый простой для потребления потоковый стиль.

### Клиентский поток меняет создание данных { #client-stream-changes-data }

При клиентской потоковой передаче клиент больше не отправляет один готовый объект запроса.

Вместо этого он постепенно проталкивает в вызов несколько сообщений и только потом получает итоговый сводный ответ.

Асинхронная заглушка отдает вам `StreamObserver<Req>` для записи и доставляет единственный ответ в переданный вами `StreamObserver<Resp>`. Вызов не считается завершенным, пока вы не вызовете
`onCompleted()` у наблюдателя запросов.

### Двунаправленный поток { #bidirectional-stream }

При двунаправленной потоковой передаче и клиент, и сервер могут продолжать общаться в рамках одного RPC.

Значит, клиент должен обрабатывать:

- асинхронную отправку запросов
- асинхронную обработку ответов
- жизненный цикл и завершение потока

Поскольку оба направления асинхронны, обертке нужно явное место для сбора ответов и явный сигнал «сервер закончил» — в этом руководстве это `CompletableFuture`, завершаемый из `onCompleted()`.

## Protobuf API { #protobuf-api }

Продвинутый клиент переиспользует ровно тот же ориентированный на потоки контракт `.proto` из руководства по продвинутому серверу.

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

Вся разница — в ключевом слове `stream`. Оно появляется со стороны запроса, со стороны ответа или с обеих, и именно оно заставляет генератор выпускать методы на наблюдателях вместо обычных методов
«запрос-ответ».

## Зависимости { #dependencies }

Продвинутый клиентский модуль использует тот же базовый клиентский стек, что и обычный клиент.

Версии модулей Kora берутся из BOM Kora `io.koraframework:kora-bom`, поэтому отдельные артефакты Kora объявляются без версии:

```properties title="gradle.properties"
koraVersion=2.0.0.RC1
junitVersion=6.1.3
```

===! ":fontawesome-brands-java: `Java`"

    Обновите `build.gradle`:

    ```groovy title="build.gradle"
    plugins {
        id "application"
        id "com.google.protobuf" version "0.10.0"
    }

    configurations {
        koraBom
        compileOnly.extendsFrom(koraBom)
        annotationProcessor.extendsFrom(koraBom)
        implementation.extendsFrom(koraBom)
        testCompileOnly.extendsFrom(koraBom)
        testAnnotationProcessor.extendsFrom(koraBom)
        testImplementation.extendsFrom(koraBom)
    }

    dependencies {
        koraBom platform("io.koraframework:kora-bom:$koraVersion")

        compileOnly "javax.annotation:javax.annotation-api:1.3.2"
        annotationProcessor "io.koraframework:annotation-processors"

        implementation "io.koraframework:config-hocon"
        implementation "io.koraframework:grpc-client"
        implementation "io.koraframework:http-server-undertow"
        implementation "io.koraframework:json-common"
        implementation "io.koraframework:logging-logback"
        implementation "io.grpc:grpc-protobuf:1.83.1"

        testRuntimeOnly platform("org.junit:junit-bom:$junitVersion")
        testRuntimeOnly "org.junit.platform:junit-platform-launcher"
        testImplementation platform("org.junit:junit-bom:$junitVersion")
        testImplementation "io.grpc:grpc-inprocess:1.83.1"
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
        id("com.google.protobuf") version "0.10.0"
    }

    dependencies {
        implementation(platform("io.koraframework:kora-bom:${property("koraVersion")}"))

        compileOnly("javax.annotation:javax.annotation-api:1.3.2")
        ksp("io.koraframework:symbol-processors:${property("koraVersion")}")

        implementation("io.koraframework:config-hocon")
        implementation("io.koraframework:grpc-client")
        implementation("io.koraframework:http-server-undertow")
        implementation("io.koraframework:json-common")
        implementation("io.koraframework:logging-logback")
        implementation("io.grpc:grpc-protobuf:1.83.1")

        testRuntimeOnly(platform("org.junit:junit-bom:${property("junitVersion")}"))
        testRuntimeOnly("org.junit.platform:junit-platform-launcher")
        testImplementation(platform("org.junit:junit-bom:${property("junitVersion")}"))
        testImplementation("io.grpc:grpc-inprocess:1.83.1")
        testImplementation("org.junit.jupiter:junit-jupiter")
    }
    ```

Для потоков ничего нового не нужно: `io.koraframework:grpc-client` уже поставляет транспорт `grpc-okhttp` и `grpc-stub`, а асинхронные заглушки берутся из того же сгенерированного кода, что и блокирующие.

!!! warning "Держите все артефакты `io.grpc` на одной версии"

    Среда выполнения gRPC, поставляемая с `io.koraframework:grpc-client`, — это `1.83.1`. Любой другой объявленный вами артефакт `io.grpc` — `grpc-protobuf` и все, что в тестовой области, например
    `grpc-inprocess`, — должен использовать ровно эту версию. Зафиксированная более старая версия прекрасно компилируется и падает только во время выполнения с
    `AbstractMethodError: ... does not define or inherit an implementation of the resolved method`.

## Генерация кода { #code-generation }

Настройка Gradle-плагина protobuf остается той же, что и в базовом руководстве по клиенту:

===! ":fontawesome-brands-java: `Java`"

    Добавьте в `build.gradle`:

    ```groovy title="build.gradle"
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

    Добавьте в `build.gradle.kts`:

    ```kotlin title="build.gradle.kts"
    protobuf {
        protoc { artifact = "com.google.protobuf:protoc:4.35.1" }
        plugins {
            id("grpc") { artifact = "io.grpc:protoc-gen-grpc-java:1.83.1" }
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

Меняется не сама генерация кода, а то, какие сгенерированные заглушки мы используем:

- `UserStreamingServiceBlockingStub` для серверного потокового чтения, где ответ приходит как `Iterator`
- `UserStreamingServiceStub` (асинхронная) для клиентских и двунаправленных потоков, у которых блокирующего варианта нет вообще

Обе внедряются напрямую, без `@Tag` на самой заглушке: Kora сама подставляет канал с тегом `UserStreamingService`.

## Конфигурация { #config }

Продвинутый сервер защищает потоковую службу API-ключом в gRPC-метаданных, поэтому продвинутый клиент должен знать две вещи:

- где находится сервер
- какой API-ключ отправлять

Полный справочник по конфигурации смотрите в [HTTP-сервере](../documentation/http-server.md), [Конфигурации](../documentation/config.md), [gRPC-клиенте](../documentation/grpc-client.md)
и [Logging SLF4J](../documentation/logging-slf4j.md).

===! ":material-code-json: `Hocon`"

    ```javascript title="src/main/resources/application.conf"
    httpServer {
      port = 8081 //(1)!
      system.port = 8086 //(2)!
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
        "io.koraframework": "INFO" //(10)!
        "io.koraframework.guide.grpcclient.advanced": "INFO" //(11)!
      }
    }
    ```

    1. Порт публичного HTTP-сервера, используемый локальным эндпоинтом руководства (по умолчанию: `8080`).
    2. Порт системного HTTP-сервера, используемый пробами и метриками (по умолчанию: `8085`).
    3. Включает логирование запросов публичного HTTP-сервера (по умолчанию: `false`).
    4. API-ключ, который отправляет перехватчик аутентификации; читается через интерфейс `@ConfigSource`.
    5. Необязательное переопределение API-ключа из переменной окружения `GRPC_STREAMING_API_KEY`.
    6. Целевой URL продвинутого gRPC-сервера (обязательный, значения по умолчанию нет).
    7. Необязательное переопределение целевого URL из переменной окружения `GRPC_STREAMING_SERVER_URL`.
    8. Включает логирование gRPC-вызовов для этого клиента (по умолчанию: `false`).
    9. Уровень логирования для `ROOT`.
    10. Уровень логирования для `io.koraframework`.
    11. Уровень логирования для `io.koraframework.guide.grpcclient.advanced`.

=== ":simple-yaml: `YAML`"

    ```yaml title="src/main/resources/application.yaml"
    httpServer:
      port: 8081 #(1)!
      system:
        port: 8086 #(2)!
      telemetry:
        logging:
          enabled: true #(3)!
    auth:
      apiKey:
        value: ${GRPC_STREAMING_API_KEY:test-api-key} #(4)!
    grpcClient:
      UserStreamingService:
        url: ${GRPC_STREAMING_SERVER_URL:http://localhost:8092} #(5)!
        telemetry:
          logging:
            enabled: true #(6)!
    logging:
      levels:
        ROOT: "INFO" #(7)!
        "io.koraframework": "INFO" #(8)!
        "io.koraframework.guide.grpcclient.advanced": "INFO" #(9)!
    ```

    1. Порт публичного HTTP-сервера, используемый локальным эндпоинтом руководства (по умолчанию: `8080`).
    2. Порт системного HTTP-сервера, используемый пробами и метриками (по умолчанию: `8085`).
    3. Включает логирование запросов публичного HTTP-сервера (по умолчанию: `false`).
    4. API-ключ, который отправляет перехватчик аутентификации; читается через интерфейс `@ConfigSource`. Использует показанное значение и позволяет `GRPC_STREAMING_API_KEY` его переопределить.
    5. Целевой URL продвинутого gRPC-сервера (обязательный, значения по умолчанию нет). Использует показанное значение и позволяет `GRPC_STREAMING_SERVER_URL` его переопределить.
    6. Включает логирование gRPC-вызовов для этого клиента (по умолчанию: `false`).
    7. Уровень логирования для `ROOT`.
    8. Уровень логирования для `io.koraframework`.
    9. Уровень логирования для `io.koraframework.guide.grpcclient.advanced`.

Здесь стоит обратить внимание на две вещи.

Секция конфигурации — `grpcClient.UserStreamingService`, а не `grpcClient.UserService`. Kora выводит путь из *простого* имени protobuf-службы той заглушки, которую вы внедряете, поэтому две службы из
этого контракта настраиваются — и подключаются — независимо, даже если они лежат в одном `.proto`-файле и на одном порту сервера.

Как и в базовом руководстве по клиенту, локальный URL использует `http://...`, поэтому gRPC-клиент работает в режиме без шифрования для этой демонстрационной установки. Замените на `https://...`, и тот
же канал будет построен поверх TLS; для `mTLS` или частного удостоверяющего центра добавьте компонент `ChannelCredentials` с тегом сгенерированного класса службы, как описано в
[gRPC-клиент: транспорт и TLS](../documentation/grpc-client.md#transport-tls).

## Клиентский перехватчик { #client-interceptor }

Подробнее о клиентских gRPC-перехватчиках и метаданных — в разделе [gRPC-клиент: перехватчики](../documentation/grpc-client.md#interceptors).

Клиентские перехватчики — это клиентский аналог транспортного промежуточного слоя. Они полезны для задач, которые должны выполняться для исходящих вызовов в одном месте:

- логирование
- аутентификация
- сроки выполнения
- трассировка

В отличие от [HTTP-клиента](../documentation/http-client.md#interceptors), у gRPC-перехватчиков нет уровней метода, класса или приложения. Каждый перехватчик действует **в рамках одного клиента** — за
счет тега компонента со сгенерированным классом службы.

Продвинутый клиент добавляет простой перехватчик логирования:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/grpcclient/advanced/grpc/LoggingInterceptor.java"
    package io.koraframework.guide.grpcclient.advanced.grpc;

    import io.grpc.CallOptions;
    import io.grpc.Channel;
    import io.grpc.ClientCall;
    import io.grpc.ClientInterceptor;
    import io.grpc.MethodDescriptor;
    import org.slf4j.Logger;
    import org.slf4j.LoggerFactory;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.common.annotation.Tag;
    import io.koraframework.guide.grpcserver.advanced.UserStreamingServiceGrpc;

    @Tag(UserStreamingServiceGrpc.class) //(1)!
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

    1. Ограничивает перехватчик только клиентом `UserStreamingService`.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/grpcclient/advanced/grpc/LoggingInterceptor.kt"
    package io.koraframework.guide.grpcclient.advanced.grpc

    import io.grpc.*
    import org.slf4j.LoggerFactory
    import io.koraframework.common.annotation.Component
    import io.koraframework.common.annotation.Tag
    import io.koraframework.guide.grpcserver.advanced.UserStreamingServiceGrpc

    @Tag(UserStreamingServiceGrpc::class) //(1)!
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

    1. Ограничивает перехватчик только клиентом `UserStreamingService`.

`@Tag(UserStreamingServiceGrpc.class)` здесь не украшение, а *единственная* проводка. При создании канала `ManagedChannelLifecycle` собирает `All<ClientInterceptor>` именно с этим тегом. Уберите тег —
и перехватчик не применится ни к одному клиенту; смените его на другой класс службы — и перехватчик переедет к тому клиенту.

Поскольку у компонента ровно один `@Tag`, один экземпляр перехватчика не может обслуживать несколько клиентов. Чтобы переиспользовать одну реализацию для нескольких клиентов, объявите класс без
`@Component` и публикуйте его по разу на клиента из модуля приложения, каждый раз со своим тегом — смотрите [Общие для нескольких клиентов](../documentation/grpc-client.md#shared-interceptors).

Kora регистрирует сначала ваши перехватчики, затем свой перехватчик телеметрии, затем перехватчик сроков выполнения. gRPC вызывает перехватчики в обратном порядке регистрации, поэтому вызов проходит так:

```
Call -> Config (deadline) interceptor -> Telemetry interceptor -> Your interceptors -> gRPC Server
```

Отсюда два практических следствия: ваши перехватчики уже видят итоговый `deadline` в `CallOptions`, а все, что они делают, происходит внутри span телеметрии и измеряемой длительности вызова.

## Перехватчик авторизации { #authorization-interceptor }

Теперь сделаем так, чтобы клиент автоматически отправлял API-ключ, которого ждет продвинутый сервер.

Сам ключ приходит из конфигурации через небольшой интерфейс `@ConfigSource`:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/grpcclient/advanced/grpc/UserStreamingAuthConfig.java"
    package io.koraframework.guide.grpcclient.advanced.grpc;

    import io.koraframework.config.common.annotation.ConfigSource;

    @ConfigSource("auth.apiKey")
    public interface UserStreamingAuthConfig {

        String value();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/grpcclient/advanced/grpc/UserStreamingAuthConfig.kt"
    package io.koraframework.guide.grpcclient.advanced.grpc

    import io.koraframework.config.common.annotation.ConfigSource

    @ConfigSource("auth.apiKey")
    interface UserStreamingAuthConfig {
        fun value(): String
    }
    ```

Перехватчик внедряет эту конфигурацию и кладет ключ в `Metadata` исходящего вызова:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/grpcclient/advanced/grpc/UserStreamingAuthInterceptor.java"
    package io.koraframework.guide.grpcclient.advanced.grpc;

    import io.grpc.CallOptions;
    import io.grpc.Channel;
    import io.grpc.ClientCall;
    import io.grpc.ClientInterceptor;
    import io.grpc.ForwardingClientCall;
    import io.grpc.Metadata;
    import io.grpc.MethodDescriptor;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.common.annotation.Tag;
    import io.koraframework.guide.grpcserver.advanced.UserStreamingServiceGrpc;

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
                public void start(Listener<RespT> responseListener, Metadata headers) { //(1)!
                    headers.put(AUTHORIZATION_HEADER, authConfig.value());
                    super.start(responseListener, headers);
                }
            };
        }
    }
    ```

    1. `start(...)` — единственное место, где заголовки еще можно изменить: он выполняется один раз за вызов, прямо перед отправкой запроса.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/grpcclient/advanced/grpc/UserStreamingAuthInterceptor.kt"
    package io.koraframework.guide.grpcclient.advanced.grpc

    import io.grpc.*
    import io.koraframework.common.annotation.Component
    import io.koraframework.common.annotation.Tag
    import io.koraframework.guide.grpcserver.advanced.UserStreamingServiceGrpc

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
                override fun start(responseListener: Listener<RespT>, headers: Metadata) { //(1)!
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

    1. `start(...)` — единственное место, где заголовки еще можно изменить: он выполняется один раз за вызов, прямо перед отправкой запроса.

Это gRPC-аналог автоматического добавления заголовков аутентификации в продвинутом HTTP-клиенте. Заголовок добавляется один раз на вызов, поэтому он покрывает и долгоживущие потоковые вызовы: учетные
данные едут в начальных метаданных вызова, а не с каждым сообщением.

## Потоковый клиент { #streaming-client }

Теперь можно обернуть сгенерированные потоковые заглушки в небольшую клиентскую службу.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/grpcclient/advanced/service/UserStreamingClientService.java"
    package io.koraframework.guide.grpcclient.advanced.service;

    import com.google.protobuf.Empty;
    import io.grpc.stub.StreamObserver;
    import java.time.LocalDateTime;
    import java.time.ZoneOffset;
    import java.util.ArrayList;
    import java.util.List;
    import java.util.concurrent.CompletableFuture;
    import java.util.concurrent.CopyOnWriteArrayList;
    import java.util.concurrent.TimeUnit;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.grpcclient.advanced.dto.UserRequest;
    import io.koraframework.guide.grpcclient.advanced.dto.UserResponse;
    import io.koraframework.guide.grpcclient.advanced.dto.UserUpdateRequest;
    import io.koraframework.guide.grpcserver.advanced.CreateUserRequest;
    import io.koraframework.guide.grpcserver.advanced.CreateUsersResponse;
    import io.koraframework.guide.grpcserver.advanced.UpdateUserRequest;
    import io.koraframework.guide.grpcserver.advanced.UserStreamingServiceGrpc;

    @Component
    public final class UserStreamingClientService {

        private final UserStreamingServiceGrpc.UserStreamingServiceBlockingStub blockingStub; //(1)!
        private final UserStreamingServiceGrpc.UserStreamingServiceStub asyncStub; //(2)!

        public UserStreamingClientService(
                UserStreamingServiceGrpc.UserStreamingServiceBlockingStub blockingStub,
                UserStreamingServiceGrpc.UserStreamingServiceStub asyncStub) {
            this.blockingStub = blockingStub;
            this.asyncStub = asyncStub;
        }

        public CreateUsersResult createUsers(List<UserRequest> requests) { //(3)!
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
                requestObserver.onCompleted(); //(4)!
                return future.get(5, TimeUnit.SECONDS);
            } catch (Exception e) {
                requestObserver.onError(e);
                throw new RuntimeException("Failed to create users over gRPC streaming", e);
            }
        }

        public List<UserResponse> getAllUsers() { //(5)!
            var users = new ArrayList<UserResponse>();
            var iterator = this.blockingStub.getAllUsers(Empty.getDefaultInstance());
            iterator.forEachRemaining(user -> users.add(toDto(user)));
            return users;
        }

        public List<UserResponse> updateUsers(List<UserUpdateRequest> updates) { //(6)!
            var future = new CompletableFuture<List<UserResponse>>();
            var responses = new CopyOnWriteArrayList<UserResponse>();
            var responseObserver = new StreamObserver<io.koraframework.guide.grpcserver.advanced.UserResponse>() {
                @Override
                public void onNext(io.koraframework.guide.grpcserver.advanced.UserResponse value) {
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

        private UserResponse toDto(io.koraframework.guide.grpcserver.advanced.UserResponse response) {
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

    1. Серверная потоковая передача — блокирующая заглушка возвращает `Iterator`.
    2. Клиентская и двунаправленная потоковая передача — эти методы есть только у асинхронной заглушки.
    3. Клиентский поток: много запросов внутрь, один сводный ответ наружу.
    4. Завершение потока запросов — это то, что сообщает серверу об окончании пакета; без него вызов висит до истечения срока.
    5. Серверный поток: один запрос внутрь, много ответов наружу.
    6. Двунаправленный поток: обе стороны передают независимо, а `onCompleted` у наблюдателя ответов — сигнал, что сервер закончил.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/grpcclient/advanced/service/UserStreamingClientService.kt"
    package io.koraframework.guide.grpcclient.advanced.service

    import com.google.protobuf.Empty
    import io.grpc.stub.StreamObserver
    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.grpcclient.advanced.dto.UserRequest
    import io.koraframework.guide.grpcclient.advanced.dto.UserResponse
    import io.koraframework.guide.grpcclient.advanced.dto.UserUpdateRequest
    import io.koraframework.guide.grpcserver.advanced.CreateUserRequest
    import io.koraframework.guide.grpcserver.advanced.CreateUsersResponse
    import io.koraframework.guide.grpcserver.advanced.UpdateUserRequest
    import io.koraframework.guide.grpcserver.advanced.UserStreamingServiceGrpc
    import java.time.LocalDateTime
    import java.time.ZoneOffset
    import java.util.concurrent.CompletableFuture
    import java.util.concurrent.CopyOnWriteArrayList
    import java.util.concurrent.TimeUnit

    @Component
    class UserStreamingClientService(
        private val blockingStub: UserStreamingServiceGrpc.UserStreamingServiceBlockingStub, //(1)!
        private val asyncStub: UserStreamingServiceGrpc.UserStreamingServiceStub //(2)!
    ) {

        fun createUsers(requests: List<UserRequest>): CreateUsersResult { //(3)!
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
                requestObserver.onCompleted() //(4)!
                return future.get(5, TimeUnit.SECONDS)
            } catch (e: Exception) {
                requestObserver.onError(e)
                throw RuntimeException("Failed to create users over gRPC streaming", e)
            }
        }

        fun getAllUsers(): List<UserResponse> { //(5)!
            val users = mutableListOf<UserResponse>()
            val iterator = blockingStub.getAllUsers(Empty.getDefaultInstance())
            iterator.forEachRemaining { user -> users += toDto(user) }
            return users
        }

        fun updateUsers(updates: List<UserUpdateRequest>): List<UserResponse> { //(6)!
            val future = CompletableFuture<List<UserResponse>>()
            val responses = CopyOnWriteArrayList<UserResponse>()
            val responseObserver = object : StreamObserver<io.koraframework.guide.grpcserver.advanced.UserResponse> {
                override fun onNext(value: io.koraframework.guide.grpcserver.advanced.UserResponse) {
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

        private fun toDto(response: io.koraframework.guide.grpcserver.advanced.UserResponse): UserResponse {
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

    1. Серверная потоковая передача — блокирующая заглушка возвращает `Iterator`.
    2. Клиентская и двунаправленная потоковая передача — эти методы есть только у асинхронной заглушки.
    3. Клиентский поток: много запросов внутрь, один сводный ответ наружу.
    4. Завершение потока запросов — это то, что сообщает серверу об окончании пакета; без него вызов висит до истечения срока.
    5. Серверный поток: один запрос внутрь, много ответов наружу.
    6. Двунаправленный поток: обе стороны передают независимо, а `onCompleted` у наблюдателя ответов — сигнал, что сервер закончил.

Форма всех методов одна и та же, и именно ее вы будете переиспользовать в своем коде:

1. создать `CompletableFuture` под результат, которого ждет вызывающая сторона
2. создать `StreamObserver`, который наполняет его из `onNext` / `onCompleted` и роняет из `onError`
3. передать этого наблюдателя асинхронной заглушке и получить обратно наблюдателя запросов
4. записать запросы, затем вызвать `onCompleted()`
5. дождаться результата на future с ограниченным таймаутом

Ограниченный `future.get(5, TimeUnit.SECONDS)` важен. У потокового вызова нет неявного конца: если сервер никогда не завершит поток ответов, а срок выполнения не настроен, неограниченный `get()` будет
висеть вечно. Заданный `grpcClient.UserStreamingService.timeout` дает ту же защиту на уровне транспорта, и тогда зависший вызов падает с `DEADLINE_EXCEEDED`.

### Вариант с корутинами { #coroutine-alternative }

Обвязка с наблюдателями выше существует потому, что это Java-заглушки. Если дополнительно сгенерировать корутинные заглушки Kotlin — смотрите
[Корутинные заглушки Kotlin](grpc-client.md#kotlin-coroutine-stubs) — те же три формы схлопываются в обычный код на `suspend` и `Flow`:

```kotlin
val users: Flow<UserResponse> = coroutineStub.getAllUsers(Empty.getDefaultInstance())          // server streaming
val summary: CreateUsersResponse = coroutineStub.createUsers(flowOf(request1, request2))       // client streaming
val updated: Flow<UserResponse> = coroutineStub.updateUsers(flowOf(update1, update2))          // bidirectional
```

Корутинная заглушка внедряется точно так же, как Java-заглушки, и перехватчики с тегом выше применяются и к ней, потому что оба семейства заглушек используют один и тот же канал с тегом. В этом
руководстве в обоих языковых вариантах оставлены Java-заглушки, чтобы листинги Java и Kotlin оставались напрямую сопоставимыми.

## Контроллер проверки { #check-controller }

Сопровождающее приложение выставляет один HTTP-эндпоинт, который по очереди выполняет все три формы потоков.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/grpcclient/advanced/controller/ClientTestController.java"
    package io.koraframework.guide.grpcclient.advanced.controller;

    import java.util.List;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.grpcclient.advanced.dto.UserRequest;
    import io.koraframework.guide.grpcclient.advanced.dto.UserUpdateRequest;
    import io.koraframework.guide.grpcclient.advanced.service.UserStreamingClientService;
    import io.koraframework.http.common.HttpMethod;
    import io.koraframework.http.common.annotation.HttpRoute;
    import io.koraframework.http.server.common.annotation.HttpController;
    import io.koraframework.json.common.annotation.Json;

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
            String error) {
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/grpcclient/advanced/controller/ClientTestController.kt"
    package io.koraframework.guide.grpcclient.advanced.controller

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.grpcclient.advanced.dto.UserRequest
    import io.koraframework.guide.grpcclient.advanced.dto.UserUpdateRequest
    import io.koraframework.guide.grpcclient.advanced.service.UserStreamingClientService
    import io.koraframework.http.common.HttpMethod
    import io.koraframework.http.common.annotation.HttpRoute
    import io.koraframework.http.server.common.annotation.HttpController
    import io.koraframework.json.common.annotation.Json

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

Контроллеру нужен еще один DTO по сравнению с базовым клиентом — `UserUpdateRequest`, потому что двунаправленное обновление несет идентификатор пользователя рядом с новыми значениями:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/grpcclient/advanced/dto/UserUpdateRequest.java"
    package io.koraframework.guide.grpcclient.advanced.dto;

    import io.koraframework.json.common.annotation.Json;

    @Json
    public record UserUpdateRequest(String userId, String name, String email) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/grpcclient/advanced/dto/UserUpdateRequest.kt"
    package io.koraframework.guide.grpcclient.advanced.dto

    import io.koraframework.json.common.annotation.Json

    @Json
    data class UserUpdateRequest(val userId: String, val name: String, val email: String)
    ```

## Запуск приложения { #run-app }

Соберите сгенерированные исходники и скомпилируйте приложение:

```bash
./gradlew clean classes
```

Сначала запустите продвинутый сервер с API-ключом, которого он ждет:

```bash
GRPC_STREAMING_API_KEY=test-api-key ./gradlew run
```

Затем запустите продвинутый клиент с тем же ключом:

```bash
GRPC_STREAMING_API_KEY=test-api-key ./gradlew run
```

Теперь вызовите:

```bash
curl -X POST http://localhost:8081/client/test-all-streaming-endpoints
```

Этот единственный вспомогательный эндпоинт внутри проверяет:

- клиентскую потоковую передачу
- серверную потоковую передачу
- двунаправленную потоковую передачу

## Тестирование { #testing }

Тесты продвинутого клиента тоже используют in-process подход: `InProcessServerBuilder` поднимает фиктивный `UserStreamingServiceImplBase`, а `ClientInterceptors.intercept(channel, ...)` применяет те же
перехватчики аутентификации и логирования, что применил бы граф. Тестируемая служба затем создается вручную из `newBlockingStub(interceptedChannel)` и `newStub(interceptedChannel)`.

Здесь это особенно полезно, потому что позволяет тестам смоделировать:

- успешные потоковые взаимодействия
- отклоненные вызовы без API-ключа — фиктивный сервер закрывает вызов со `Status.UNAUTHENTICATED`, и тест проверяет именно этот код
- поведение перехватчиков, собирая одну заглушку с перехватчиками, а другую без них

Запустите их:

```bash
./gradlew test
```

## Лучшие практики { #best-practices }

- Держите продвинутую потоковую работу в отдельной клиентской службе, а не раздувайте унарный клиент.
- Помечайте тегом со сгенерированным классом службы каждый перехватчик: `ClientInterceptor` без тега не применяется ни к одному клиенту.
- Используйте клиентские перехватчики для аутентификации по метаданным вместо повторения логики заголовков в каждом месте вызова.
- Всегда завершайте поток запросов и всегда ограничивайте ожидание потока ответов.
- Держите обработку жизненного цикла потока рядом с границей транспорта.
- Предпочитайте in-process gRPC-серверы для быстрых потоковых тестов на стороне клиента.
- Держите все артефакты `io.grpc` на той версии, которая поставляется с `io.koraframework:grpc-client`.
- Помечайте написанные вручную DTO аннотацией `@Json` только тогда, когда они пересекают HTTP/JSON-границу; сгенерированным protobuf-сообщениям JSON-аннотации не нужны.

## Итоги { #summary }

В этом руководстве вы создали потоковый gRPC-клиент, который повторяет руководство по продвинутому серверу.

Важной идеей было не только «как вызывать потоковые RPC», но и «как чисто структурировать клиент»:

- разделить унарные и потоковые задачи
- добавить аутентификацию и логирование через перехватчики с тегом одной сгенерированной службы
- обернуть сгенерированные заглушки в сфокусированный слой службы

## Ключевые понятия { #key-concepts }

- чем продвинутые gRPC-клиенты отличаются от унарных
- как блокирующие и асинхронные заглушки используются для разных потоковых шаблонов
- как `@Tag(ServiceGrpc.class)` ограничивает `ClientInterceptor` одним клиентом
- как цепочка перехватчиков упорядочивает ваши перехватчики относительно телеметрии и сроков выполнения
- как клиентские перехватчики добавляют логирование и аутентификацию по метаданным
- как потреблять серверные, клиентские и двунаправленные потоковые методы
- как тестировать поведение продвинутого gRPC-клиента с `InProcessServer`

## Устранение неполадок { #troubleshooting }

**Потоковый вызов никогда не завершается:**

Проверьте, что поток запросов завершается на стороне клиента вызовом `onCompleted()` и что сервер отправляет сигналы завершения. Ограничьте ожидание — таймаутом на future либо через
`grpcClient.<Служба>.timeout`.

**Перехватчик не срабатывает:**

Проверьте `@Tag`. Компонент `ClientInterceptor` без тега не собирается ни одним клиентом, а тег с другим сгенерированным классом службы переносит его к тому клиенту.

**Вызовы отклоняются как `UNAUTHENTICATED`:**

Проверьте, что клиент и сервер используют одно и то же значение API-ключа и что перехватчик аутентификации помечен тегом сгенерированного потокового клиента.

**Кажется, что конфигурация игнорируется:**

Путь конфигурации — это *простое* имя protobuf-службы: `grpcClient.UserStreamingService`. Секция `grpcClient.UserService` настраивает другого клиента.

**In-process тесты проходят, а вызовы во время выполнения падают:**

Сравните рабочий `application.conf` с in-process тестовой обвязкой — особенно gRPC-хост, порт и теги перехватчиков.

## Что дальше? { #whats-next }

- [Устойчивые шаблоны](resilient.md), чтобы защитить потоковые и унарные RPC-вызовы от медленных или недоступных служб.
- [Наблюдаемость](observability.md), чтобы трассировать вызовы gRPC-клиента, жизненные циклы потоков и поведение перехватчиков.
- [Обмен сообщениями с Kafka](messaging-kafka.md), чтобы сравнить интеграцию в стиле RPC с асинхронной событийной интеграцией.
- [Продвинутый HTTP-клиент](http-client-advanced.md), чтобы сравнить границы продвинутого gRPC- и продвинутого HTTP-клиента.

## Помощь { #help }

Если что-то не работает:

- сравните с [Kora Java gRPC Client Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-grpc-client-advanced-app) и [Kora Kotlin gRPC Client Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-grpc-client-advanced-app)
- проверьте [документацию gRPC-клиента](../documentation/grpc-client.md)
- убедитесь, что продвинутый сервер из [Продвинутого gRPC-сервера](grpc-server-advanced.md) работает на порту `8092`
- убедитесь, что клиент и сервер используют одно и то же значение API-ключа
