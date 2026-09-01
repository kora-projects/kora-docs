---
search:
  exclude: true
title: gRPC-клиент с Kora
summary: Build a Kora 2.0 gRPC client that consumes a unary CRUD service through injected generated stubs
description: "Step-by-step Kora gRPC client: the io.koraframework:grpc-client module and GrpcClientModule, the protobuf Gradle plugin, generated UserServiceGrpc stubs injected without a @Tag, the grpcClient.<Service> configuration path derived from the protobuf service name, the url scheme choosing plaintext or TLS, timeout applied as a call deadline, wrapping a BlockingStub in an application service, and in-process client tests."
agent:
  use_when: "Use this file for questions about calling a gRPC service from Kora step by step: GrpcClientModule, injecting UserServiceGrpc.UserServiceBlockingStub / FutureStub / async Stub / Kotlin coroutine stubs, the grpcClient.UserService configuration section, url, timeout and telemetry keys, StatusRuntimeException and Status.Code handling, the io.koraframework:grpc-client and io.grpc:grpc-protobuf dependencies, the protobuf Gradle plugin, and client tests with InProcessServerBuilder."
tags: grpc-client, protobuf, rpc, microservices
---

# gRPC-клиент с Kora { #grpc-client-kora }

Это руководство знакомит с унарными gRPC-клиентами в Kora. В нем показано, как один и тот же контракт `.proto` порождает клиентские заглушки и типы сообщений, как Kora создает канал на каждую службу и
внедряет готовые заглушки в граф приложения и как небольшая служба-обертка превращает вызовы заглушки в операции уровня приложения. Вы также увидите, почему gRPC-статусы, сроки выполнения и
сгенерированные построители запросов формируют клиентский код иначе, чем декларативные HTTP-клиенты.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java gRPC Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-grpc-client-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin gRPC Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-grpc-client-app).

## Что вы создадите { #youll-build }

Вы создадите отдельное приложение унарного gRPC-клиента с:

- тем же контрактом `user_service.proto`, что использует сервер
- сгенерированными protobuf-типами запросов и ответов
- внедренной клиентской gRPC-заглушкой Kora для `UserService`
- небольшой службой приложения, которая оборачивает `CreateUser`, `GetUser`, `GetUsers`, `UpdateUser` и `DeleteUser`
- HTTP-маршрутами-триггерами, которые позволяют легко проверить клиент локально
- проверками во время выполнения против работающего gRPC-сервера

## Что понадобится { #youll-need }

- JDK 25 или новее
- Gradle 9+ (эталонные приложения используют Gradle Wrapper `9.5.1`)
- текстовый редактор или среда разработки
- работающий gRPC-сервер из предыдущего руководства для проверок во время выполнения

Артефакты Kora собраны под Java 25, поэтому JDK, которым компилируется ваш код, должен быть версии 25 или новее.

## Требования { #prerequisites }

!!! note "Обязательно: пройдите руководство по gRPC-серверу"

    Это руководство предполагает, что вы уже прошли **[gRPC-сервер с Kora](grpc-server.md)** и **[HTTP-клиент с Kora](http-client.md)** и понимаете генерацию protobuf-кода, унарные RPC-методы и разделение на репозиторий и службу из предыдущих серверных руководств.

    Если вы еще не прошли руководство по gRPC-серверу, сначала сделайте это, потому что здесь переиспользуется тот же protobuf-контракт и показывается, как клиент вызывает этот сервер.

## Обзор { #overview }

В руководстве по серверу сгенерированный контракт использовался, чтобы реализовать службу.

В руководстве по клиенту тот же сгенерированный контракт используется, чтобы эту службу вызвать.

Это одна из сильнейших сторон gRPC:

- один общий контракт
- сгенерированный код с обеих сторон
- меньше риска расхождения транспорта

Клиентская архитектура состоит из трех слоев:

- protobuf-контракт описывает удаленный API
- сгенерированная gRPC-заглушка выполняет транспортный вызов
- ваш компонент Kora оборачивает заглушку в удобные для приложения методы

Эта обертка важна. Сгенерированные заглушки ориентированы на транспорт: они говорят на языке protobuf-типов запросов и ответов, сроков выполнения, каналов и gRPC-статусов. Коду приложения обычно
нужны более понятные методы вроде `createUser(...)` или `getUsers(...)` плюс обработка ошибок на уровне предметной области. Это руководство держит такую границу явной, чтобы сгенерированный клиент не
растекался по всей кодовой базе.

Перед началом стоит знать две детали времени выполнения — они объясняют, что именно Kora строит за вас:

- Kora создает один `ManagedChannel` на каждую protobuf-службу через `ManagedChannelLifecycle`, а транспортом служит **gRPC OkHttp**. Отдельный транспортный артефакт добавлять не нужно:
  `io.koraframework:grpc-client` уже приносит `grpc-okhttp` и `grpc-stub`.
- Любая сгенерированная заглушка внедряется **без** `@Tag`. Kora сама подставляет канал с нужным тегом, поэтому параметра конструктора типа `UserServiceGrpc.UserServiceBlockingStub` достаточно.

### Чем gRPC-клиент отличается от HTTP { #grpc-client-differs-http }

Написанный вручную HTTP-клиент обычно начинается с URL и HTTP-обмена. Код клиента решает, какой путь вызвать, какой метод использовать, какие заголовки отправить, как сериализовать JSON и как
интерпретировать ответ.

- пути URL
- формы JSON-нагрузки
- разбор ответа
- отображение ошибок

gRPC-клиент вместо этого начинается со скомпилированного контракта службы. Файл `.proto` определяет доступные RPC-методы и типы сообщений, а сгенерированная заглушка предоставляет эти методы как код.
Клиенту не нужно помнить, что `GetUser` соответствует какой-то форме URL, потому что собирать путь к ресурсу в коде приложения не требуется. Сгенерированная заглушка уже знает имя RPC-метода, имя
службы, кодировщик сообщений и ожидаемый тип ответа.

Вместо ручной сборки запросов вы обычно:

- строите protobuf-объект запроса
- вызываете метод сгенерированной заглушки
- получаете типизированный protobuf-ответ

Главное отличие не только в бинарной кодировке против JSON. Более сильное отличие в том, что gRPC переносит договоренность клиента и сервера в сгенерированный код:

- имена методов являются частью определения protobuf-службы
- поля запросов и ответов являются частью protobuf-сообщений
- отсутствующие или переименованные поля обнаруживаются раньше — при компиляции и по правилам эволюции схемы
- код клиента вызывает сгенерированный API, а не написанный вручную путь
- код сервера реализует сгенерированные методы службы, а не сопоставляет аннотации маршрутов

HTTP-клиенты часто моделируют сбои через коды ответа вроде `404`, `409` или `500`. gRPC-клиенты обычно моделируют сбои через gRPC-статусы вроде `NOT_FOUND`, `INVALID_ARGUMENT`, `UNAVAILABLE` или
`DEADLINE_EXCEEDED`. Это меняет обработку ошибок: код приложения обычно ловит `StatusRuntimeException` и ветвится по коду статуса либо отображает его на границе обертки, а остальной части службы
предоставляет поведение в терминах предметной области.

Поведение соединения тоже ощущается иначе. Клиенты HTTP/JSON часто считают каждый запрос независимым обращением к ресурсу. gRPC-клиенты строятся вокруг каналов и заглушек. Канал представляет цель
соединения и настройки транспорта, а заглушка — сгенерированный фасад клиента для выполнения вызовов. Именно поэтому руководство оборачивает сгенерированную заглушку в `UserClientService`: остальной
части приложения не нужно знать про каналы, protobuf-построители и детали gRPC-статусов.

Это не отменяет необходимость клиентского кода приложения. Это меняет его зону ответственности. Вместо ручной работы с низкоуровневыми деталями транспорта ваша клиентская служба становится адаптером
между сгенерированными транспортными типами и моделью приложения.

## Protobuf API { #protobuf-api }

Первая ключевая мысль в том, что клиент **не** изобретает новый контракт.

Он использует тот же `user_service.proto`, что и сервер:

??? example "Protobuf-контракт"

    ```protobuf title="src/main/proto/user_service.proto"
    syntax = "proto3";

    package io.koraframework.guide.grpcserver;
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

В этом общем контракте и весь смысл:

- сервер и клиент компилируются против одной и той же транспортной модели
- вам не нужно вручную поддерживать дублирующиеся схемы запросов и ответов
- `proto`-пакет остается `io.koraframework.guide.grpcserver`, поэтому сгенерированные классы сохраняют пакет сервера, хотя это клиентское приложение

## Зависимости { #dependencies }

Теперь добавим клиентский модуль Kora и поддержку protobuf.

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
        annotationProcessor.extendsFrom(koraBom)
        implementation.extendsFrom(koraBom)
        testCompileOnly.extendsFrom(koraBom)
        testAnnotationProcessor.extendsFrom(koraBom)
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

Зачем нужны эти зависимости:

- `io.koraframework:grpc-client` заменяет `io.koraframework:grpc-server` — он строит канал, подключает перехватчики и регистрирует сгенерированные заглушки в графе
- `io.grpc:grpc-protobuf` дает поддержку сериализации protobuf-сообщений во время выполнения
- `javax.annotation:javax.annotation-api` нужен только на этапе компиляции, потому что сгенерированные заглушки ссылаются на `@javax.annotation.Generated`
- `io.koraframework:http-server-undertow` и `io.koraframework:json-common` нужны только для того, чтобы руководство могло выставить небольшой HTTP-эндпоинт, запускающий gRPC-вызовы
- `io.grpc:grpc-inprocess` дает тестам gRPC-сервер и канал в памяти — без портов и без Docker

!!! warning "Держите все артефакты `io.grpc` на одной версии"

    Среда выполнения gRPC, поставляемая с `io.koraframework:grpc-client`, — это `1.83.1`. Любой другой объявленный вами артефакт `io.grpc` — `grpc-protobuf` и все, что в тестовой области, например
    `grpc-inprocess`, — должен использовать ровно эту версию. Зафиксированная более старая версия прекрасно компилируется и падает только во время выполнения с
    `AbstractMethodError: ... does not define or inherit an implementation of the resolved method`.

## Генерация кода { #code-generation }

Так же как и на стороне сервера, Gradle должен сгенерировать protobuf-сообщения и gRPC-типы.

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

Так генерируются:

- protobuf-сообщения вроде `CreateUserRequest`
- типы клиентских заглушек вроде `UserServiceGrpc.UserServiceBlockingStub`

Плагин выпускает **Java**-классы даже в Kotlin-проекте, поэтому в обоих вариантах сгенерированные каталоги регистрируются в исходном наборе `java`.

### Корутинные заглушки Kotlin { #kotlin-coroutine-stubs }

Java-заглушки выше работают в Kotlin ровно так же, как в Java, и это руководство использует их в обоих языках, чтобы варианты оставались сопоставимыми.

Если вам ближе идиоматичные корутины, добавьте поверх описанной настройки [генератор gRPC Kotlin](https://github.com/grpc/grpc-kotlin). Kora поддерживает сгенерированные корутинные заглушки как
полноценно внедряемые компоненты:

```kotlin title="build.gradle.kts"
dependencies {
    implementation("io.grpc:grpc-kotlin-stub:1.5.0")
}

protobuf {
    plugins {
        id("grpckt") { artifact = "io.grpc:protoc-gen-grpc-kotlin:1.5.0:jdk8@jar" }
    }
    generateProtoTasks {
        all().forEach { task ->
            task.plugins { id("grpc"); id("grpckt") }
        }
    }
}

kotlin {
    sourceSets.main { kotlin.srcDir("build/generated/source/proto/main/grpckt") }
}
```

Сгенерированный `UserServiceGrpcKt.UserServiceCoroutineStub` помечен аннотацией `@StubFor`, а символьный процессор Kora выпускает рядом `@Module`, который связывает заглушку с тем же каналом с тегом,
что и Java-заглушки. Внедрение не требует дополнительной проводки, а унарные вызовы становятся `suspend`-функциями, потоковые — `Flow<T>`. Полный список смотрите в
[gRPC-клиент: типы заглушек](../documentation/grpc-client.md#stub-types).

## Модули { #modules }

Подробнее о клиентских gRPC-службах, конфигурации и заглушках — в разделе [gRPC-клиент: служба](../documentation/grpc-client.md#service).

Теперь включим среду выполнения gRPC-клиента Kora в граф приложения.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/grpcclient/Application.java"
    package io.koraframework.guide.grpcclient;

    import io.koraframework.application.graph.KoraApplication;
    import io.koraframework.common.annotation.KoraApp;
    import io.koraframework.config.hocon.HoconConfigModule;
    import io.koraframework.grpc.client.GrpcClientModule;
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule;
    import io.koraframework.json.common.JsonModule;
    import io.koraframework.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        GrpcClientModule,  // <----- Connected module
        UndertowPublicHttpServerModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/grpcclient/Application.kt"
    package io.koraframework.guide.grpcclient

    import io.koraframework.application.graph.KoraApplication
    import io.koraframework.common.annotation.KoraApp
    import io.koraframework.config.hocon.HoconConfigModule
    import io.koraframework.grpc.client.GrpcClientModule
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule
    import io.koraframework.json.common.JsonModule
    import io.koraframework.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        GrpcClientModule,  // <----- Connected module
        UndertowPublicHttpServerModule

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

`GrpcClientModule` сам по себе клиента не создает. Он предоставляет части, нужные каждому клиенту, — фабрику каналов, фабрику телеметрии и преобразователь значений конфигурации, — а расширение
обработчика аннотаций (или KSP) генерирует канал и заглушки для каждой службы, которую вы действительно внедряете.

Обратите внимание, что это приложение включает еще и небольшой модуль HTTP-сервера. Не потому, что это руководство про HTTP. Он нужен, чтобы сопровождающее приложение могло выставить простой
HTTP-эндпоинт, который в одном месте выполняет все операции gRPC-клиента.

## Конфигурация { #config }

Это приложение — самостоятельная служба Kora, поэтому ему нужны собственные порты.

Мы будем использовать:

- `8090` — приложение gRPC-сервера из `grpc-server.md`
- `8081` — публичный HTTP-сервер клиентского приложения
- `8086` — системный HTTP-сервер клиентского приложения (пробы, метрики)
- `grpcClient.UserService.url` — цель сгенерированного клиента

Полный справочник по конфигурации смотрите в [HTTP-сервере](../documentation/http-server.md), [gRPC-клиенте](../documentation/grpc-client.md) и [Logging SLF4J](../documentation/logging-slf4j.md).

===! ":material-code-json: `Hocon`"

    ```javascript title="src/main/resources/application.conf"
    httpServer {
      port = 8081 //(1)!
      system.port = 8086 //(2)!
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
        "io.koraframework": "INFO" //(8)!
        "io.koraframework.guide.grpcclient": "INFO" //(9)!
      }
    }
    ```

    1. Порт публичного HTTP-сервера, используемый локальным эндпоинтом руководства (по умолчанию: `8080`).
    2. Порт системного HTTP-сервера, используемый пробами и метриками (по умолчанию: `8085`).
    3. Включает логирование запросов публичного HTTP-сервера (по умолчанию: `false`).
    4. Целевой URL gRPC-сервера (обязательный, значения по умолчанию нет).
    5. Необязательное переопределение целевого URL из переменной окружения `GRPC_SERVER_URL`.
    6. Включает логирование gRPC-вызовов для этого клиента (по умолчанию: `false`).
    7. Уровень логирования для `ROOT`.
    8. Уровень логирования для `io.koraframework`.
    9. Уровень логирования для `io.koraframework.guide.grpcclient`.

=== ":simple-yaml: `YAML`"

    ```yaml title="src/main/resources/application.yaml"
    httpServer:
      port: 8081 #(1)!
      system:
        port: 8086 #(2)!
      telemetry:
        logging:
          enabled: true #(3)!
    grpcClient:
      UserService:
        url: ${GRPC_SERVER_URL:http://localhost:8090} #(4)!
        telemetry:
          logging:
            enabled: true #(5)!
    logging:
      levels:
        ROOT: "INFO" #(6)!
        "io.koraframework": "INFO" #(7)!
        "io.koraframework.guide.grpcclient": "INFO" #(8)!
    ```

    1. Порт публичного HTTP-сервера, используемый локальным эндпоинтом руководства (по умолчанию: `8080`).
    2. Порт системного HTTP-сервера, используемый пробами и метриками (по умолчанию: `8085`).
    3. Включает логирование запросов публичного HTTP-сервера (по умолчанию: `false`).
    4. Целевой URL gRPC-сервера (обязательный, значения по умолчанию нет). Использует показанное значение и позволяет `GRPC_SERVER_URL` его переопределить.
    5. Включает логирование gRPC-вызовов для этого клиента (по умолчанию: `false`).
    6. Уровень логирования для `ROOT`.
    7. Уровень логирования для `io.koraframework`.
    8. Уровень логирования для `io.koraframework.guide.grpcclient`.

Здесь важны три детали.

**Путь конфигурации выводится из имени protobuf-службы.** Kora берет сгенерированную константу `UserServiceGrpc.SERVICE_NAME` — полное имя `io.koraframework.guide.grpcserver.UserService` — и оставляет
только часть после последней точки. Поэтому секция называется `grpcClient.UserService`, а не `grpcClient.io.koraframework.guide.grpcserver.UserService`. Переименуйте службу в `.proto`-файле, и этот
путь изменится вместе с ней.

**Схема URL выбирает транспорт.** `http://` создает канал без шифрования (порт по умолчанию `80`, если порт не указан), `https://` создает TLS-канал (порт по умолчанию `443`). Любая другая схема
останавливает сборку графа при запуске с ошибкой `Unsupported gRPC client URL scheme`. В этом руководстве мы обращаемся к локальному серверу, поэтому нужен именно plaintext `http://localhost:8090`.

**`url` обязателен, все остальное — нет.** Отсутствующий `url` роняет граф при запуске. Таймауты (`timeout`), keepalive-пинги и балансировка нагрузки выключены, пока вы их не зададите, — полный
список смотрите в [gRPC-клиент: конфигурация](../documentation/grpc-client.md#configuration).

## Типы заглушек { #stub-types }

Плагин protobuf генерирует для одной службы несколько классов заглушек, и Kora может внедрить каждый из них напрямую. `@Tag` на самой заглушке не нужен — Kora сама подставляет канал с нужным тегом:

| Тип заглушки                     | Модель вызова                                                                            | Когда использовать                                     |
|----------------------------------|-------------------------------------------------------------------------------------------|--------------------------------------------------------|
| `UserServiceBlockingStub`        | Синхронная; возвращает ответ напрямую (или `Iterator` для серверной потоковой передачи)     | Блокирующий код, простейший стиль вызова               |
| `UserServiceFutureStub`          | Асинхронная; возвращает `ListenableFuture<T>` (только унарные)                              | Неблокирующий код на `ListenableFuture`                |
| `UserServiceStub` (async)        | Асинхронная; отдает результаты через колбэки `StreamObserver<T>`                             | Любая потоковая передача, асинхронные вызовы с колбэками |
| `UserServiceCoroutineStub`       | `suspend`-функции и `Flow<T>`                                                               | Идиоматичные корутины Kotlin                           |

Это руководство использует блокирующую заглушку, потому что все RPC в контракте унарные, а вызывающий код читается лучше без колбэков. [Продвинутое руководство по клиенту](grpc-client-advanced.md)
добавляет асинхронную заглушку, где она обязательна для клиентской и двунаправленной потоковой передачи.

Перед написанием обертки стоит разобраться со сроками выполнения. Если задан `grpcClient.UserService.timeout`, всегда включенный `GrpcClientConfigInterceptor` применяет его как `deadline` вызова — но
только если у вызова еще нет собственного. Заданный для конкретного вызова `stub.withDeadlineAfter(2, TimeUnit.SECONDS)` попадает в `CallOptions` до запуска перехватчиков, поэтому всегда имеет
приоритет. Истекший срок проявляется как `StatusRuntimeException` с `Status.Code.DEADLINE_EXCEEDED`.

## Обертка заглушки в службу { #wrap-stub-service }

Сгенерированные заглушки полезны, но приложению обычно все равно нужен небольшой клиентский слой службы.

Этот слой может:

- скрывать построение protobuf-запросов
- отображать транспортные protobuf-объекты в DTO приложения
- централизовать использование транспорта на стороне клиента

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/grpcclient/service/UserClientService.java"
    package io.koraframework.guide.grpcclient.service;

    import java.time.LocalDateTime;
    import java.time.ZoneOffset;
    import java.util.List;

    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.grpcclient.dto.UserRequest;
    import io.koraframework.guide.grpcclient.dto.UserResponse;
    import io.koraframework.guide.grpcserver.CreateUserRequest;
    import io.koraframework.guide.grpcserver.DeleteUserRequest;
    import io.koraframework.guide.grpcserver.GetUserRequest;
    import io.koraframework.guide.grpcserver.GetUsersRequest;
    import io.koraframework.guide.grpcserver.UpdateUserRequest;
    import io.koraframework.guide.grpcserver.UserServiceGrpc;

    @Component
    public final class UserClientService {

        private final UserServiceGrpc.UserServiceBlockingStub userService; //(1)!

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

        private UserResponse toDto(io.koraframework.guide.grpcserver.UserResponse response) { //(2)!
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

    1. Сгенерированная заглушка внедряется напрямую, без `@Tag` и без ручного создания канала.
    2. Полное имя различает сгенерированный protobuf-класс `UserResponse` и одноименный DTO приложения.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/grpcclient/service/UserClientService.kt"
    package io.koraframework.guide.grpcclient.service

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.grpcclient.dto.UserRequest
    import io.koraframework.guide.grpcclient.dto.UserResponse
    import io.koraframework.guide.grpcserver.*
    import java.time.LocalDateTime
    import java.time.ZoneOffset

    @Component
    class UserClientService(
        private val userService: UserServiceGrpc.UserServiceBlockingStub //(1)!
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

        private fun toDto(response: io.koraframework.guide.grpcserver.UserResponse): UserResponse { //(2)!
            return UserResponse(
                response.id,
                response.name,
                response.email,
                LocalDateTime.ofEpochSecond(response.createdAt.seconds, response.createdAt.nanos, ZoneOffset.UTC)
            )
        }
    }
    ```

    1. Сгенерированная заглушка внедряется напрямую, без `@Tag` и без ручного создания канала.
    2. Полное имя различает сгенерированный protobuf-класс `UserResponse` и одноименный DTO приложения.

DTO приложения — это обычные записи и data-классы. Они помечены `@Json`, потому что контроллер проверки ниже возвращает их по HTTP; сгенерированным protobuf-сообщениям JSON-аннотации не нужны никогда:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/grpcclient/dto/UserRequest.java"
    package io.koraframework.guide.grpcclient.dto;

    import io.koraframework.json.common.annotation.Json;

    @Json
    public record UserRequest(String name, String email) {}
    ```

    ```java title="src/main/java/io/koraframework/guide/grpcclient/dto/UserResponse.java"
    package io.koraframework.guide.grpcclient.dto;

    import java.time.LocalDateTime;
    import io.koraframework.json.common.annotation.Json;

    @Json
    public record UserResponse(String id, String name, String email, LocalDateTime createdAt) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/io/koraframework/guide/grpcclient/dto/UserRequest.kt"
    package io.koraframework.guide.grpcclient.dto

    import io.koraframework.json.common.annotation.Json

    @Json
    data class UserRequest(val name: String, val email: String)
    ```

    ```kotlin title="src/main/kotlin/io/koraframework/guide/grpcclient/dto/UserResponse.kt"
    package io.koraframework.guide.grpcclient.dto

    import io.koraframework.json.common.annotation.Json
    import java.time.LocalDateTime

    @Json
    data class UserResponse(
        val id: String,
        val name: String,
        val email: String,
        val createdAt: LocalDateTime
    )
    ```

Ключевая мысль здесь та же, что и во многих других руководствах: сгенерированный транспортный код полезен, но остальная часть приложения должна работать с небольшой и читаемой абстракцией.

## Контроллер проверки { #check-controller }

Сопровождающее приложение включает крошечный HTTP-контроллер, который вызывает gRPC-клиент и возвращает сводку.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/io/koraframework/guide/grpcclient/controller/ClientTestController.java"
    package io.koraframework.guide.grpcclient.controller;

    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.grpcclient.dto.UserRequest;
    import io.koraframework.guide.grpcclient.service.UserClientService;
    import io.koraframework.http.common.HttpMethod;
    import io.koraframework.http.common.annotation.HttpRoute;
    import io.koraframework.http.server.common.annotation.HttpController;
    import io.koraframework.json.common.annotation.Json;

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

    ```kotlin title="src/main/kotlin/io/koraframework/guide/grpcclient/controller/ClientTestController.kt"
    package io.koraframework.guide.grpcclient.controller

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.grpcclient.dto.UserRequest
    import io.koraframework.guide.grpcclient.service.UserClientService
    import io.koraframework.http.common.HttpMethod
    import io.koraframework.http.common.annotation.HttpRoute
    import io.koraframework.http.server.common.annotation.HttpController
    import io.koraframework.json.common.annotation.Json

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

Этот контроллер — не «настоящая» цель руководства. Это просто удобная обвязка, которая позволяет легко проверить клиент от начала до конца. Ловить `Exception` и возвращать его текст полем нормально
для демонстрационной обвязки; в продуктивном коде следует ветвиться по `StatusRuntimeException.getStatus().getCode()`.

## Запуск приложения { #run-app }

Соберите сгенерированные исходники и скомпилируйте приложение:

```bash
./gradlew clean classes
```

Сначала запустите серверное приложение из предыдущего руководства, затем запустите клиентское:

```bash
./gradlew run
```

Теперь вызовите локальный вспомогательный HTTP-эндпоинт:

```bash
curl -X POST http://localhost:8081/client/test-all-user-endpoints
```

Этот HTTP-вызов — только триггер. Внутри приложения настоящая работа выполняется через сгенерированную клиентскую gRPC-заглушку.

Канал не роняет приложение, когда сервер недоступен: `ManagedChannelLifecycle` пишет предупреждение, если первая проба соединения не удалась, а вызов переподключается позже. Вызов, сделанный при
недоступном сервере, падает со `Status.Code.UNAVAILABLE`.

## Тестирование { #testing }

Тестам клиентского модуля не нужны ни Docker, ни полноценный внешний серверный процесс.

Вместо этого они используют:

- `InProcessServerBuilder`, чтобы поднять фиктивный `UserServiceImplBase` в той же JVM
- `InProcessChannelBuilder`, чтобы построить к нему канал
- `UserServiceGrpc.newBlockingStub(channel)`, чтобы создать заглушку, которую `UserClientService` принимает в конструкторе

Это возможно именно потому, что обертка принимает заглушку параметром конструктора: тест создает заглушку вручную и вообще не запускает граф Kora. Тесты остаются быстрыми, детерминированными и
сфокусированными на поведении клиента, включая пути с ошибками — например, проверку `Status.Code.NOT_FOUND` для отсутствующего пользователя.

Запустите тесты:

```bash
./gradlew test
```

## Лучшие практики { #best-practices }

- Переиспользуйте ровно один и тот же `.proto`-контракт между клиентом и сервером.
- Оборачивайте сгенерированные заглушки в небольшую службу приложения, а не растаскивайте их повсюду.
- Держите построение protobuf-сообщений рядом с границей gRPC-клиента.
- Ветвитесь по `StatusRuntimeException.getStatus().getCode()`, а не по типам исключений.
- Используйте `InProcessServer` для сфокусированных клиентских тестов, когда нужна быстрая и детерминированная обратная связь.
- Считайте транспортные модели gRPC именно транспортными моделями, даже если они похожи на DTO приложения.
- Держите все артефакты `io.grpc` на той версии, которая поставляется с `io.koraframework:grpc-client`.
- Помечайте написанные вручную DTO аннотацией `@Json` только тогда, когда они пересекают HTTP/JSON-границу; сгенерированным protobuf-сообщениям JSON-аннотации не нужны.

## Итоги { #summary }

В этом руководстве вы создали унарный gRPC-клиент, который повторяет сервер из предыдущего руководства.

Ключевые идеи были такими:

- переиспользовать общий protobuf-контракт
- внедрять сгенерированные gRPC-заглушки через Kora, без ручной проводки канала
- обернуть их в `UserClientService`
- тестировать клиент на in-process инфраструктуре gRPC

## Ключевые понятия { #key-concepts }

- как gRPC-клиент Kora подключается к графу приложения
- как путь конфигурации `grpcClient.<Служба>` выводится из имени protobuf-службы
- как схема `url` выбирает транспорт без шифрования или TLS
- как сгенерированные блокирующие заглушки используются для унарных RPC-вызовов
- почему небольшой клиентский слой службы все равно полезен
- как один protobuf-контракт может обслуживать обе стороны системы
- почему `InProcessServer` хорошо подходит для тестов gRPC-клиента

## Устранение неполадок { #troubleshooting }

**Клиент не может подключиться (`UNAVAILABLE`):**

Проверьте, что серверное приложение запущено и что `application.conf` клиента указывает на правильный хост и gRPC-порт. Несовпадение plaintext/TLS выглядит точно так же: `http://` — без шифрования,
`https://` — TLS.

**Приложение не стартует с ошибкой `Unsupported gRPC client URL scheme`:**

В `url` используется схема, отличная от `http` или `https`, без явно указанного порта. Используйте `http://host:port` или `https://host:port`.

**Конфигурация игнорируется:**

Проверьте путь конфигурации. Это *простое* имя protobuf-службы — `grpcClient.UserService`, — а не полное и не имя Java-класса.

**Сгенерированная заглушка отсутствует:**

Запустите `./gradlew clean classes` после изменения `user_service.proto` и проверьте настройку исходного набора protobuf.

**Запрос проходит в тестах, но не во время выполнения:**

Сравните in-process тестовую обвязку с реальной конфигурацией клиента — особенно хост, порт и имена пакетов службы.

## Что дальше? { #whats-next }

- [Продвинутый HTTP-сервер](http-server-advanced.md), если вы еще его не проходили.
- [Продвинутый gRPC-сервер](grpc-server-advanced.md) после продвинутого HTTP-сервера, чтобы добавить потоковые эндпоинты, которые сможет использовать более богатый клиент.
- [Продвинутый gRPC-клиент](grpc-client-advanced.md) после продвинутого gRPC-сервера, чтобы работать с потоками, авторизацией по метаданным и клиентскими перехватчиками.
- [Устойчивые шаблоны](resilient.md), чтобы защитить RPC-вызовы повторами, таймаутами, предохранителем и запасным вариантом.
- [Наблюдаемость](observability.md), чтобы трассировать gRPC-вызовы и измерять поведение клиента.

## Помощь { #help }

Если что-то не работает:

- сравните с [Kora Java gRPC Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-grpc-client-app) и [Kora Kotlin gRPC Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-grpc-client-app)
- проверьте [документацию gRPC-клиента](../documentation/grpc-client.md)
- убедитесь, что сервер из [gRPC-сервера](grpc-server.md) работает на порту `8090`
- убедитесь, что клиент и сервер используют один и тот же `.proto`-контракт
