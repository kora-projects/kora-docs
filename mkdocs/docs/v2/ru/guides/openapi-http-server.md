---
search:
  exclude: true
title: Контрактный HTTP-сервер с OpenAPI
summary: Continue the HTTP Server guide by replacing the handwritten controller with OpenAPI-generated server code and a delegate
description: "Contract-first Kora HTTP server from an OpenAPI file: the org.openapi.generator Gradle plugin with generatorName kora, configOptions mode java-server / kotlin-server, enableServerValidation, the generated UsersApiController, UsersApiDelegate and sealed UsersApiResponses wrappers, generated TO models, and openapi.management.files with /openapi, /swagger-ui and /scalar."
agent:
  use_when: "Use this file for questions about building a contract-first Kora HTTP server from an OpenAPI contract step by step: GenerateTask, generatorName kora, mode java-server and kotlin-server, enableServerValidation, apiPackage / modelPackage / invokerPackage, the generated <Api>Controller, <Api>Delegate, <Api>Responses and <Api>ServerRequestMappers, implementing a delegate with @Component, mapping generated TO models to internal DTOs, OpenApiManagementModule and the openapi.management.files, path, swaggerui and scalar configuration."
tags: openapi, http-server, swagger, code-generation, contract-first
---

# Контрактный HTTP-сервер с OpenAPI { #contract-first-http-server }

Это руководство знакомит с контрактной разработкой HTTP-сервера в Kora на основе OpenAPI. В нем разбирается, как спецификация OpenAPI превращается в сгенерированные серверные интерфейсы и модели, как
реализация делегата соединяет этот сгенерированный транспортный слой с прикладными сервисами, и как валидация и метаданные ответов задаются контрактом. Вы также увидите, как сгенерированный код
остается отделенным от написанной вручную бизнес-логики, благодаря чему описание API остается источником истины.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java OpenAPI HTTP Server App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-openapi-http-server-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin OpenAPI HTTP Server App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-openapi-http-server-app).

## Что вы создадите { #youll-build }

Вы пересоберете знакомое CRUD API из руководства `http-server` в контрактном стиле:

- API пользователей будет описано в `user-http-server.yaml`
- Kora сгенерирует серверный слой в `build/generated/user-http-server`
- вы реализуете сгенерированный `UsersApiDelegate`
- `UserService`, `UserRepository` и `InMemoryUserRepository` останутся прежними
- приложение будет отдавать `/openapi` и `/swagger-ui`

## Что вам понадобится { #youll-need }

- JDK 25 или новее
- Gradle 9+
- Текстовый редактор или IDE
- Пройденное руководство [HTTP-сервер](http-server.md)

Артефакты Kora 2.0 собраны под Java 25, поэтому JDK, которым компилируется приложение, должен быть версии 25 или новее. Генератор OpenAPI добавляет еще одно требование, описанное в разделе
[Зависимости](#dependencies): сама JVM, на которой работает `Gradle`, тоже должна быть версии 25 или новее.

## Требования { #prerequisites }

!!! note "Сначала пройдите руководство по HTTP-серверу"

    Руководство предполагает, что вы прошли **[HTTP-сервер](http-server.md)** и уже разобрались с CRUD-приложением пользователей: `UserRequest`, `UserResponse`, `UserRepository`, `InMemoryUserRepository` и `UserService`.

    Мы сохраним эти идеи и заменим только написанный вручную слой HTTP-контроллера.

    Если руководство по HTTP-серверу еще не пройдено, начните с него: здесь мы сосредоточены на контрактной генерации по OpenAPI, а не на повторной сборке CRUD-сервиса с нуля.

## Обзор { #overview }

В этом руководстве мы постепенно перейдем от ручного сервера к контрактному:

1. поймем, что меняется, когда источником истины становится OpenAPI
2. опишем существующее CRUD API в файле OpenAPI
3. настроим генерацию Kora по OpenAPI
4. изучим сгенерированные делегат, контроллер, обертки ответов и модели
5. сохраним привычные слои сервиса и репозитория
6. реализуем сгенерированный делегат вместо ручного контроллера
7. опубликуем OpenAPI и Swagger UI
8. запустим и проверим приложение

### Контрактная разработка? { #contract-first-development }

При подходе «сначала код» разработчики обычно начинают с контроллера и документируют его поведение уже потом. Это работает, но со временем часто создает трения:

- документация расходится с кодом
- потребители и поставщики обсуждают поведение неформально, а не через один общий контракт
- формы ответов и правила валидации дублируются
- сгенерированным клиентам становится сложнее доверять, потому что контракт не является главным источником истины

Контрактная разработка меняет порядок.

Вместо «контроллер определяет API» мы говорим «контракт OpenAPI определяет API». Из этого контракта инструменты могут сгенерировать:

- серверные контроллеры и контракты делегатов
- модели запросов и ответов
- аннотации валидации
- документацию OpenAPI
- а позже и HTTP-клиентов

Это особенно полезно, когда от одного и того же API зависят несколько команд или несколько приложений. Все они могут смотреть в один файл контракта, а не восстанавливать поведение контроллера по коду.

### HTTP-основы { #http-basics }

Руководство [HTTP-сервер](http-server.md) по-прежнему остается местом, где стоит впервые изучить:

- `@HttpController`
- `@HttpRoute`
- `@Path`
- `@Query`
- `@Json`
- `HttpResponseEntity`

Здесь мы опираемся на эти знания.

Мы не меняем предметную область и не меняем поведение CRUD. Мы меняем **способ объявления HTTP-слоя**:

- было: написанные вручную методы контроллера
- стало: контракт OpenAPI + сгенерированный серверный код + реализация делегата

Обработка запросов остается **синхронной**, ровно как и в написанном вручную сервере. Undertow отправляет каждый запрос на виртуальный поток, сгенерированный контроллер напрямую вызывает метод вашего
делегата, а делегат возвращает результат. Реактивных и `suspend`-режимов генерации в Kora 2.0 нет — генератор поддерживает ровно четыре режима: `java-client`, `java-server`, `kotlin-client` и
`kotlin-server`.

Поэтому это руководство — естественный следующий шаг, а не отдельный несвязанный пример.

## Зависимости { #dependencies }

Контрактной генерации нужны два разных вида сборочной обвязки, и их стоит сразу разделить в голове:

- **Gradle-плагин** `org.openapi.generator`, который дает тип задачи `GenerateTask`
- **библиотека** `io.koraframework:openapi-generator`, которая учит этот плагин выпускать код Kora

Библиотека подключается в classpath `buildscript`, а не в `dependencies`, потому что ее должен загрузить сам `Gradle` до компиляции вашего проекта.

===! ":fontawesome-brands-java: `Java`"

    Обновите `build.gradle`:

    ```groovy
    import org.openapitools.generator.gradle.plugin.tasks.GenerateTask //(1)!

    buildscript {
        repositories {
            mavenCentral()
        }
        dependencies {
            classpath("io.koraframework:openapi-generator:2.0.0.RC1") //(2)!
        }
    }

    plugins {
        id "application"
        id "org.openapi.generator" version "7.24.0" //(3)!
    }

    dependencies {
        koraBom platform("io.koraframework:kora-bom:2.0.0.RC1") //(4)!

        annotationProcessor "io.koraframework:annotation-processors" //(5)!

        implementation "io.koraframework:config-hocon"
        implementation "io.koraframework:http-server-undertow"
        implementation "io.koraframework:json-common"
        implementation "io.koraframework:logging-logback"
        implementation "io.koraframework:openapi-management" //(6)!
        implementation "io.koraframework:validation-module" //(7)!
    }
    ```

    1.  `GenerateTask` — тип задачи плагина, через который объявляется задача генерации.
    2.  Реализация генератора Kora, загружаемая JVM `Gradle` через classpath `buildscript`.
    3.  Gradle-плагин `OpenAPI Generator`. Kora 2.0 собрана под `OpenAPI Generator 7.24.0`, поэтому зафиксируйте ту же версию плагина — другие версии не гарантируют работоспособность, так как API генератора может быть несовместимым на уровне кода.
    4.  Kora BOM: согласует версии всех модулей Kora и библиотек, от которых зависит Kora.
    5.  Аннотационный процессор Kora: во время компиляции создает граф приложения, модули контроллеров и читатели/писатели JSON.
    6.  Публикует файл контракта и страницы Swagger UI / Scalar из работающего приложения.
    7.  Рантайм валидации, необходимый потому, что сервер генерируется с `enableServerValidation`.

=== ":simple-kotlin: `Kotlin`"

    Обновите `build.gradle.kts`:

    ```kotlin
    import org.openapitools.generator.gradle.plugin.tasks.GenerateTask //(1)!

    buildscript {
        repositories {
            mavenCentral()
        }
        dependencies {
            classpath("io.koraframework:openapi-generator:2.0.0.RC1") //(2)!
        }
    }

    plugins {
        id("org.jetbrains.kotlin.jvm")
        id("com.google.devtools.ksp")
        id("application")
        id("org.openapi.generator") version "7.24.0" //(3)!
    }

    dependencies {
        implementation(platform("io.koraframework:kora-bom:2.0.0.RC1")) //(4)!

        ksp("io.koraframework:symbol-processors:2.0.0.RC1") //(5)!

        implementation("io.koraframework:config-hocon")
        implementation("io.koraframework:http-server-undertow")
        implementation("io.koraframework:json-common")
        implementation("io.koraframework:logging-logback")
        implementation("io.koraframework:openapi-management") //(6)!
        implementation("io.koraframework:validation-module") //(7)!
    }
    ```

    1.  `GenerateTask` — тип задачи плагина, через который объявляется задача генерации.
    2.  Реализация генератора Kora, загружаемая JVM `Gradle` через classpath `buildscript`.
    3.  Gradle-плагин `OpenAPI Generator`. Kora 2.0 собрана под `OpenAPI Generator 7.24.0`, поэтому зафиксируйте ту же версию плагина — другие версии не гарантируют работоспособность, так как API генератора может быть несовместимым на уровне кода.
    4.  Kora BOM: согласует версии всех модулей Kora и библиотек, от которых зависит Kora.
    5.  KSP-процессор Kora: во время компиляции создает граф приложения, модули контроллеров и читатели/писатели JSON.
    6.  Публикует файл контракта и страницы Swagger UI / Scalar из работающего приложения.
    7.  Рантайм валидации, необходимый потому, что сервер генерируется с `enableServerValidation`.

!!! warning "Демон `Gradle` должен работать на JDK 25 или новее"

    Поскольку `io.koraframework:openapi-generator` попадает в classpath **buildscript**, его загружает JVM `Gradle`, а не скомпилированное приложение.
    Kora собрана под `JDK 25`, поэтому демон `Gradle` тоже должен работать на `JDK 25` или новее, иначе генерация упадет с `UnsupportedClassVersionError` еще до компиляции кода проекта.
    Указать только `toolchain` проекта недостаточно — toolchain относится к компиляции, а не к самой JVM `Gradle`.

## Модули { #modules }

`OpenApiManagementModule` публикует контракт из работающего приложения, а `ValidationModule` дает рантайм, на который опираются сгенерированные аннотации валидации.

===! ":fontawesome-brands-java: `Java`"

    Обновите `src/main/java/io/koraframework/guide/openapi/httpserver/Application.java`:

    ```java
    package io.koraframework.guide.openapi.httpserver;

    import io.koraframework.application.graph.KoraApplication;
    import io.koraframework.common.annotation.KoraApp;
    import io.koraframework.config.hocon.HoconConfigModule;
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule;
    import io.koraframework.json.common.JsonModule;
    import io.koraframework.logging.logback.LogbackModule;
    import io.koraframework.openapi.management.OpenApiManagementModule;
    import io.koraframework.validation.module.ValidationModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            UndertowPublicHttpServerModule,
            JsonModule,
            LogbackModule,
            ValidationModule,          // <----- Подключенный модуль
            OpenApiManagementModule {  // <----- Подключенный модуль

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Обновите `src/main/kotlin/io/koraframework/guide/openapi/httpserver/Application.kt`:

    ```kotlin
    package io.koraframework.guide.openapi.httpserver

    import io.koraframework.application.graph.KoraApplication
    import io.koraframework.common.annotation.KoraApp
    import io.koraframework.config.hocon.HoconConfigModule
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule
    import io.koraframework.json.common.JsonModule
    import io.koraframework.logging.logback.LogbackModule
    import io.koraframework.openapi.management.OpenApiManagementModule
    import io.koraframework.validation.module.ValidationModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        UndertowPublicHttpServerModule,
        JsonModule,
        LogbackModule,
        ValidationModule,        // <----- Подключенный модуль
        OpenApiManagementModule  // <----- Подключенный модуль

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

Обратите внимание на то, чего здесь **нет**: подключать модуль для сгенерированного контроллера не нужно. Генератор выпускает контроллер уже размеченным `@Component` и `@HttpController`, поэтому он сам
попадает в граф приложения, как только его каталог с исходниками будет скомпилирован.

Итак, после этого шага приложение подготовлено к контрактному серверу, но пока ничего не сгенерировано.

## Контракт как OpenAPI { #openapi-contract }

Теперь мы выносим контракт API из аннотаций Java или Kotlin в общий файл OpenAPI.

Создайте `src/main/resources/openapi/user-http-server.yaml`:

??? example "Контракт OpenAPI"

    ```yaml
    openapi: 3.0.3
    info:
      title: User Management API
      description: Contract-first version of the HTTP Server guide API
      version: 1.0.0
    tags:
      - name: users
        description: User management operations
    paths:
      /users:
        get:
          tags:
            - users
          operationId: getUsers
          summary: Get users
          parameters:
            - name: page
              in: query
              required: false
              schema:
                type: integer
                minimum: 0
                default: 0
            - name: size
              in: query
              required: false
              schema:
                type: integer
                minimum: 1
                maximum: 100
                default: 10
            - name: sort
              in: query
              required: false
              schema:
                type: string
                enum: [name, email, createdAt]
                default: name
          responses:
            '200':
              description: Users returned
              content:
                application/json:
                  schema:
                    type: array
                    items:
                      $ref: '#/components/schemas/UserResponseTO'
            '500':
              description: Internal server error
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/ErrorResponseTO'
        post:
          tags:
            - users
          operationId: createUser
          summary: Create user
          requestBody:
            required: true
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/UserRequestTO'
          responses:
            '201':
              description: User created
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/UserResponseTO'
            '500':
              description: Internal server error
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/ErrorResponseTO'
      /users/{userId}:
        get:
          tags:
            - users
          operationId: getUser
          summary: Get user by id
          parameters:
            - name: userId
              in: path
              required: true
              schema:
                type: string
          responses:
            '200':
              description: User returned
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/UserResponseTO'
            '404':
              description: User not found
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/ErrorResponseTO'
            '500':
              description: Internal server error
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/ErrorResponseTO'
        put:
          tags:
            - users
          operationId: updateUser
          summary: Update user
          parameters:
            - name: userId
              in: path
              required: true
              schema:
                type: string
          requestBody:
            required: true
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/UserRequestTO'
          responses:
            '200':
              description: User updated
              headers:
                X-Updated-At:
                  required: true
                  schema:
                    type: string
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/UserResponseTO'
            '404':
              description: User not found
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/ErrorResponseTO'
            '500':
              description: Internal server error
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/ErrorResponseTO'
        delete:
          tags:
            - users
          operationId: deleteUser
          summary: Delete user
          parameters:
            - name: userId
              in: path
              required: true
              schema:
                type: string
          responses:
            '204':
              description: User deleted
            '404':
              description: User not found
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/ErrorResponseTO'
            '500':
              description: Internal server error
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/ErrorResponseTO'
    components:
      schemas:
        ErrorResponseTO:
          type: object
          required:
            - message
          properties:
            message:
              type: string
        UserRequestTO:
          type: object
          required:
            - name
            - email
          properties:
            name:
              type: string
              minLength: 1
              maxLength: 100
            email:
              type: string
              format: email
        UserResponseTO:
          type: object
          required:
            - id
            - name
            - email
            - createdAt
          properties:
            id:
              type: string
            name:
              type: string
            email:
              type: string
            createdAt:
              type: string
              format: date-time
    ```

Этот файл намеренно выглядит знакомо.

Мы не изобретаем новое API. Мы описываем то же CRUD API пользователей, которое уже есть в руководстве `http-server`:

- те же маршруты `/users` и `/users/{userId}`
- те же query-параметры для списка
- те же формы запроса и ответа
- то же поведение `404` и `204`, теперь с явным телом `ErrorResponseTO` для ошибок
- тот же заголовок обновления `X-Updated-At`

Две детали этого контракта проявятся прямо в сгенерированном коде, поэтому их стоит заметить уже сейчас:

- у каждой операции есть `operationId`, и это значение становится именем сгенерированного метода и префиксом каждого сгенерированного типа ответа
- каждая операция помечена тегом `users`, и этот тег становится частью `Users` в именах `UsersApiController`, `UsersApiDelegate` и `UsersApiResponses`

Это важная мысль. Контрактная разработка не про изменение бизнес-идеи. Она про перенос транспортного контракта в формальный общий источник истины.

## OpenAPI кодогенерация { #openapi-codegen }

Подробные параметры серверной генерации описаны в разделе [OpenAPI Codegen: сервер](../documentation/openapi-codegen.md#server).

Теперь расскажем Gradle, как сгенерировать серверный код по этому контракту.

===! ":fontawesome-brands-java: `Java`"

    Обновите `build.gradle`:

    ```groovy
    def openApiGenerateUsersHttpServer = tasks.register("openApiGenerateUsersHttpServer", GenerateTask) {
        generatorName = "kora" //(1)!
        group = "openapi tools"
        inputSpec = layout.projectDirectory.file("src/main/resources/openapi/user-http-server.yaml") //(2)!
        outputDir = layout.buildDirectory.dir("generated/user-http-server") //(3)!
        def corePackage = "io.koraframework.guide.openapi.httpserver.user"
        apiPackage = "${corePackage}.api" //(4)!
        modelPackage = "${corePackage}.model" //(5)!
        invokerPackage = "${corePackage}.invoker" //(6)!
        configOptions = [
                mode                  : "java-server", //(7)!
                enableServerValidation: "true", //(8)!
        ]
    }

    sourceSets.main {
        java.srcDirs += openApiGenerateUsersHttpServer.get().outputDir //(9)!
    }

    compileJava.dependsOn openApiGenerateUsersHttpServer //(10)!
    ```

    1.  Выбирает генератор Kora вместо штатных генераторов `OpenAPI Generator`.
    2.  Путь к файлу OpenAPI, по которому создаются классы.
    3.  Каталог, в который складываются сгенерированные файлы.
    4.  Пакет для сгенерированных контроллера, делегата, оберток ответов и мапперов.
    5.  Пакет для сгенерированных моделей.
    6.  Вспомогательный пакет генератора.
    7.  Режим генерации. `java-server` — один из четырех поддерживаемых режимов: `java-client`, `java-server`, `kotlin-client`, `kotlin-server`.
    8.  Переводит ограничения схемы (`minLength`, `maxLength`, `minimum`, `maximum`, `pattern`) в аннотации валидации Kora на сгенерированных моделях и контроллере.
    9.  Регистрирует сгенерированные классы как исходный код проекта.
    10. Ставит компиляцию в зависимость от генерации: сначала генерируем, потом компилируем.

=== ":simple-kotlin: `Kotlin`"

    Обновите `build.gradle.kts`:

    ```kotlin
    val openApiGenerateUsersHttpServer = tasks.register<GenerateTask>("openApiGenerateUsersHttpServer") {
        generatorName = "kora" //(1)!
        group = "openapi tools"
        inputSpec.set(layout.projectDirectory.file("src/main/resources/openapi/user-http-server.yaml")) //(2)!
        outputDir.set(layout.buildDirectory.dir("generated/user-http-server")) //(3)!
        val corePackage = "io.koraframework.guide.openapi.httpserver.user"
        apiPackage = "${corePackage}.api" //(4)!
        modelPackage = "${corePackage}.model" //(5)!
        invokerPackage = "${corePackage}.invoker" //(6)!
        configOptions = mapOf(
            "mode" to "kotlin-server", //(7)!
            "enableServerValidation" to "true", //(8)!
        )
    }

    kotlin.sourceSets.main { kotlin.srcDir(openApiGenerateUsersHttpServer.get().outputDir) } //(9)!

    tasks.matching { it.name.startsWith("ksp") }.configureEach { //(10)!
        dependsOn(openApiGenerateUsersHttpServer)
    }
    ```

    1.  Выбирает генератор Kora вместо штатных генераторов `OpenAPI Generator`.
    2.  Путь к файлу OpenAPI, по которому создаются классы.
    3.  Каталог, в который складываются сгенерированные файлы.
    4.  Пакет для сгенерированных контроллера, делегата, оберток ответов и мапперов.
    5.  Пакет для сгенерированных моделей.
    6.  Вспомогательный пакет генератора.
    7.  Режим генерации. `kotlin-server` — один из четырех поддерживаемых режимов: `java-client`, `java-server`, `kotlin-client`, `kotlin-server`.
    8.  Переводит ограничения схемы (`minLength`, `maxLength`, `minimum`, `maximum`, `pattern`) в аннотации валидации Kora на сгенерированных моделях и контроллере.
    9.  Регистрирует сгенерированные классы как исходный код проекта.
    10. `KSP` должен видеть сгенерированные исходники, поэтому каждая задача `ksp*` зависит от генерации: сначала генерируем, потом обрабатываем и компилируем.

На этом шаге важнее всего четыре детали:

- сгенерированный код попадет в `build/generated/user-http-server`
- сгенерированные типы окажутся в `io.koraframework.guide.openapi.httpserver.user`
- генерация выполняется автоматически перед компиляцией
- сгенерированный код — это **артефакт сборки**, поэтому он не попадает в систему контроля версий и не правится руками

Именно этот шаг сборки превращает статический YAML-контракт в настоящий серверный код.

## Что создает генератор { #generated-output }

Выполните:

```bash
./gradlew clean classes
```

Теперь посмотрите на сгенерированные файлы:

===! ":fontawesome-brands-java: `Java`"

    - `build/generated/user-http-server/io/koraframework/guide/openapi/httpserver/user/api/UsersApiController.java`
    - `build/generated/user-http-server/io/koraframework/guide/openapi/httpserver/user/api/UsersApiDelegate.java`
    - `build/generated/user-http-server/io/koraframework/guide/openapi/httpserver/user/api/UsersApiResponses.java`
    - `build/generated/user-http-server/io/koraframework/guide/openapi/httpserver/user/api/UsersApiServerRequestMappers.java`
    - `build/generated/user-http-server/io/koraframework/guide/openapi/httpserver/user/api/UsersApiServerResponseMappers.java`
    - `build/generated/user-http-server/io/koraframework/guide/openapi/httpserver/user/model/UserRequestTO.java`
    - `build/generated/user-http-server/io/koraframework/guide/openapi/httpserver/user/model/UserResponseTO.java`
    - `build/generated/user-http-server/io/koraframework/guide/openapi/httpserver/user/model/ErrorResponseTO.java`

=== ":simple-kotlin: `Kotlin`"

    - `build/generated/user-http-server/io/koraframework/guide/openapi/httpserver/user/api/UsersApiController.kt`
    - `build/generated/user-http-server/io/koraframework/guide/openapi/httpserver/user/api/UsersApiDelegate.kt`
    - `build/generated/user-http-server/io/koraframework/guide/openapi/httpserver/user/api/UsersApiResponses.kt`
    - `build/generated/user-http-server/io/koraframework/guide/openapi/httpserver/user/api/UsersApiServerRequestMappers.kt`
    - `build/generated/user-http-server/io/koraframework/guide/openapi/httpserver/user/api/UsersApiServerResponseMappers.kt`
    - `build/generated/user-http-server/io/koraframework/guide/openapi/httpserver/user/model/UserRequestTO.kt`
    - `build/generated/user-http-server/io/koraframework/guide/openapi/httpserver/user/model/UserResponseTO.kt`
    - `build/generated/user-http-server/io/koraframework/guide/openapi/httpserver/user/model/ErrorResponseTO.kt`

Сгенерированный сервер вводит несколько важных абстракций, и гораздо полезнее разобрать их по одной, чем воспринимать генерацию как черный ящик.

### 1. `UsersApiDelegate` { #1-usersapidelegate }

Это интерфейс, который вы реализуете в коде своего приложения.

Вот сокращенная версия сгенерированного делегата:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface UsersApiDelegate {

        @HttpRoute(method = "POST", path = "/users")
        UsersApiResponses.CreateUserApiResponse createUser(
            UserRequestTO userRequestTO
        ) throws Exception;

        @HttpRoute(method = "GET", path = "/users/{userId}")
        UsersApiResponses.GetUserApiResponse getUser(
            String userId
        ) throws Exception;

        @HttpRoute(method = "GET", path = "/users")
        UsersApiResponses.GetUsersApiResponse getUsers(
            @Nullable Integer page,
            @Nullable Integer size,
            @Nullable String sort
        ) throws Exception;
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface UsersApiDelegate {

        @HttpRoute(method = "POST", path = "/users")
        fun createUser(
            userRequestTO: UserRequestTO
        ): UsersApiResponses.CreateUserApiResponse

        @HttpRoute(method = "GET", path = "/users/{userId}")
        fun getUser(
            userId: String
        ): UsersApiResponses.GetUserApiResponse

        @HttpRoute(method = "GET", path = "/users")
        fun getUsers(
            page: Int?,
            size: Int?,
            sort: String?
        ): UsersApiResponses.GetUsersApiResponse
    }
    ```

Это первый крупный концептуальный сдвиг относительно руководства [HTTP-сервер](http-server.md).

В руководстве по ручному серверу вы сами определяли методы контроллера и размечали их транспортными аннотациями. Здесь транспортный слой уже определен контрактом, поэтому генератор дает вам интерфейс,
который нужно реализовать.

Это значит, что ваш код больше не говорит:

- какой HTTP-путь существует
- какой метод `GET`, а какой `POST`
- какое тело запроса относится к какому маршруту

Вместо этого ваш код говорит:

- как реализовать поведение, описанное контрактом
- как отображать сгенерированные транспортные модели на внутренние DTO приложения
- какой вариант ответа вернуть для каждого исхода

Две детали сигнатуры легко пропустить и потом на них наткнуться:

- методы делегата в `Java` объявлены с `throws Exception`, поэтому реализация может свободно бросать исключения; сузить `throws` в вашем `@Override` разрешено и обычно чище
- опциональные query-параметры приходят как `null`, а **не** как `default` из контракта — `default` в OpenAPI документирует значение для читателей контракта, но не заставляет сгенерированный сервер
  его подставлять. Применить `page = 0`, `size = 10` и `sort = "name"` — задача делегата

### 2. `UsersApiController` { #2-usersapicontroller }

Это сгенерированный HTTP-контроллер, который Kora помещает в граф приложения.

Вы не правите его вручную и обычно вам не нужно понимать каждую его строку. Важна его зона ответственности:

- принять HTTP-запрос
- провалидировать и отобразить транспортные данные согласно контракту
- вызвать соответствующий метод делегата
- превратить возвращенную сгенерированную обертку ответа в настоящий HTTP-ответ

Класс генерируется с `@Component` и `@HttpController`, поэтому он регистрируется в графе без какой-либо обвязки с вашей стороны. Единственная зависимость его конструктора — `UsersApiDelegate`, из-за
чего сборка падает во время компиляции, а не при старте, если вы забыли реализовать делегат.

Так сгенерированный контроллер становится транспортным адаптером, а ваш делегат — границей реализации.

Это разделение — одна из самых полезных частей контрактной серверной генерации. Механика HTTP-протокола остается в сгенерированном коде, а поведение приложения — в вашем.

### 3. `UsersApiResponses` { #3-usersapiresponses }

Этот файл — один из самых полезных сгенерированных артефактов, потому что делает транспортный контракт явным.

Вот сокращенная версия сгенерированного семейства ответов `getUser`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface UsersApiResponses {

        sealed interface GetUserApiResponse {

            record GetUser200ApiResponse(
                UserResponseTO content
            ) implements GetUserApiResponse {}

            record GetUser404ApiResponse(
                ErrorResponseTO content
            ) implements GetUserApiResponse {}

            record GetUser500ApiResponse(
                ErrorResponseTO content
            ) implements GetUserApiResponse {}
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface UsersApiResponses {

        sealed interface GetUserApiResponse {

            data class GetUser200ApiResponse(
                val content: UserResponseTO
            ) : GetUserApiResponse

            data class GetUser404ApiResponse(
                val content: ErrorResponseTO
            ) : GetUserApiResponse

            data class GetUser500ApiResponse(
                val content: ErrorResponseTO
            ) : GetUserApiResponse
        }
    }
    ```

Контракт OpenAPI говорит, что `GET /users/{userId}` может вернуть:

- `200` с телом `UserResponseTO`
- `404` с телом `ErrorResponseTO`
- `500` с телом `ErrorResponseTO`

Поэтому генератор создает одно запечатанное семейство ответов, моделирующее эти три исхода.

Три правила именования объясняют любую обертку, которая вам встретится:

- семейство называется `<OperationId>ApiResponse`, поэтому `getUser` дает `GetUserApiResponse`
- каждый вариант — `<OperationId><Code>ApiResponse`, поэтому `404` дает `GetUser404ApiResponse`
- тело ответа становится компонентом `content`; объявленные **заголовки** ответа становятся дополнительными компонентами, поэтому `updateUser` дает `UpdateUser200ApiResponse(content, xUpdatedAt)`

У ответа `204` тела нет, поэтому `DeleteUser204ApiResponse` — просто пустая запись. А если операция объявляет всего один ответ, запечатанной обертки не будет вовсе — `<OperationId>ApiResponse` будет
сразу этой единственной записью.

Это важно, потому что контракт описывает не только запрос и успешные полезные нагрузки. Он описывает и допустимые формы ошибок, а сгенерированный серверный код сохраняет эту информацию как настоящие
типы `Java` или `Kotlin`.

### 4. Сгенерированные модели { #4-generated-models }

Генератор также создает транспортные модели контрактного слоя:

- `UserRequestTO`
- `UserResponseTO`
- `ErrorResponseTO`

Модели `Java` — это `record` со сгенерированными читателями и писателями `@Json`; модели `Kotlin` — это `data class`. Поскольку включен `enableServerValidation`, ограничения контракта переезжают вместе
с ними: `minLength: 1` / `maxLength: 100` на `UserRequestTO.name` превращаются в аннотацию `@Size`, а сама модель помечается `@Valid`.

Эти сгенерированные модели относятся к границе OpenAPI, а не к вашей предметной области или сервисному слою.

Поэтому в руководстве по-прежнему сохраняются внутренние DTO вроде `UserRequest` и `UserResponse`. Делегат — то место, где встречаются эти два мира:

- сгенерированные транспортные модели OpenAPI с одной стороны
- внутренние модели приложения с другой

Явное разделение этих слоев делает будущий рефакторинг значительно безопаснее. Вы можете развивать внутренний код, не делая вид, что сгенерированные транспортные типы — это вся ваша доменная модель.

Ваши собственные DTO, написанные руками и пересекающие границу JSON, по-прежнему требуют `@Json`, потому что генератор их не создает и Kora нужно сказать построить для них мапперы во время обычной
аннотационной обработки.

!!! warning "Используйте именованные аргументы для сгенерированных моделей `Kotlin`"

    В сгенерированных конструкторах `Kotlin` обязательные свойства идут первыми, а каждое опциональное получает значение по умолчанию.
    Добавление одного свойства в контракт может сдвинуть позиции, и позиционный вызов вида `UserRequestTO("john@example.com", "John")` все еще компилируется, молча меняя местами два значения `String`.
    Создавайте сгенерированные модели именованными аргументами: `UserRequestTO(name = "John Doe", email = "john@example.com")`.

### Разбор сгенерированного `getUser()` { #generated-getuser-walkthrough }

Проще всего понять происходящее, проследив одну операцию от контракта до сгенерированного кода.

Файл OpenAPI объявляет:

- маршрут `GET /users/{userId}`
- один path-параметр `userId`
- три ответа: `200`, `404`, `500`

Из этого генератор создает:

- метод `getUser(String userId)` в `UsersApiDelegate`
- запечатанное семейство ответов `GetUserApiResponse`
- метод сгенерированного контроллера, который вызовет ваш делегат и сериализует выбранную обертку

Это значит, что реализация делегата может сосредоточиться на бизнес-смысле:

- если пользователь есть, вернуть `GetUser200ApiResponse`
- если пользователя нет, вернуть `GetUser404ApiResponse(new ErrorResponseTO(...))`
- если случился настоящий внутренний сбой, транспортный слой все равно знает, что `500` объявлен контрактом

Это главный «ага»-момент руководства: генерация по OpenAPI не просто экономит набор текста. Она превращает HTTP-контракт в набор явных серверных абстракций, которые направляют вашу реализацию.

## Сервис и репозиторий { #service-repository }

Одна из самых приятных сторон этого перехода в том, что большую часть приложения переделывать **не** нужно.

Бизнес-сторона остается прежней:

- `UserRepository`
- `InMemoryUserRepository`
- `UserService`

Эти классы сохраняют те же обязанности, что и в руководстве `http-server`:

- репозиторий хранит и достает пользователей
- сервис координирует поведение CRUD
- меняется только точка входа HTTP

Такое разделение полезно и в реальных проектах. Если доменная логика живет в сервисном слое, а не внутри контроллера, заменить один транспортный стиль другим становится намного проще.

Поэтому в этом руководстве мы **не** переписываем все приложение. Мы заменяем только написанный вручную слой контроллера на сгенерированный.

## Делегат { #delegate }

Теперь создадим класс, соединяющий сгенерированный HTTP-код с нашим существующим сервисным слоем.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/io/koraframework/guide/openapi/httpserver/controller/UserApiDelegateImpl.java`:

    ```java
    package io.koraframework.guide.openapi.httpserver.controller;

    import java.time.Instant;
    import java.time.ZoneOffset;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.openapi.httpserver.user.api.UsersApiDelegate;
    import io.koraframework.guide.openapi.httpserver.user.api.UsersApiResponses;
    import io.koraframework.guide.openapi.httpserver.user.model.ErrorResponseTO;
    import io.koraframework.guide.openapi.httpserver.user.model.UserRequestTO;
    import io.koraframework.guide.openapi.httpserver.user.model.UserResponseTO;
    import io.koraframework.guide.openapi.httpserver.dto.UserRequest;
    import io.koraframework.guide.openapi.httpserver.dto.UserResponse;
    import io.koraframework.guide.openapi.httpserver.service.UserService;

    @Component //(1)!
    public final class UserApiDelegateImpl implements UsersApiDelegate {

        private final UserService userService;

        public UserApiDelegateImpl(UserService userService) {
            this.userService = userService;
        }

        @Override
        public UsersApiResponses.CreateUserApiResponse createUser(UserRequestTO userRequest) {
            var created = this.userService.createUser(new UserRequest(userRequest.name(), userRequest.email()));
            return new UsersApiResponses.CreateUserApiResponse.CreateUser201ApiResponse(this.toGenerated(created));
        }

        @Override
        public UsersApiResponses.DeleteUserApiResponse deleteUser(String userId) {
            if (this.userService.getUser(userId).isEmpty()) {
                return new UsersApiResponses.DeleteUserApiResponse.DeleteUser404ApiResponse(
                        this.notFound(userId)
                );
            }

            this.userService.deleteUser(userId);
            return new UsersApiResponses.DeleteUserApiResponse.DeleteUser204ApiResponse(); //(2)!
        }

        @Override
        public UsersApiResponses.GetUserApiResponse getUser(String userId) {
            return this.userService.getUser(userId)
                    .<UsersApiResponses.GetUserApiResponse>map(user -> new UsersApiResponses.GetUserApiResponse.GetUser200ApiResponse(this.toGenerated(user)))
                    .orElseGet(() -> new UsersApiResponses.GetUserApiResponse.GetUser404ApiResponse(
                            this.notFound(userId)
                    ));
        }

        @Override
        public UsersApiResponses.GetUsersApiResponse getUsers(Integer page, Integer size, String sort) {
            int effectivePage = page == null ? 0 : page; //(3)!
            int effectiveSize = size == null ? 10 : size;
            String effectiveSort = sort == null ? "name" : sort;
            var users = this.userService.getUsers(effectivePage, effectiveSize, effectiveSort).stream()
                    .map(this::toGenerated)
                    .toList();
            return new UsersApiResponses.GetUsersApiResponse.GetUsers200ApiResponse(users);
        }

        @Override
        public UsersApiResponses.UpdateUserApiResponse updateUser(String userId, UserRequestTO userRequest) {
            if (this.userService.getUser(userId).isEmpty()) {
                return new UsersApiResponses.UpdateUserApiResponse.UpdateUser404ApiResponse(
                        this.notFound(userId)
                );
            }

            var updated = this.userService.updateUser(userId, new UserRequest(userRequest.name(), userRequest.email()));
            return new UsersApiResponses.UpdateUserApiResponse.UpdateUser200ApiResponse(
                    this.toGenerated(updated),
                    Instant.now().toString() //(4)!
            );
        }

        private UserResponseTO toGenerated(UserResponse user) { //(5)!
            return new UserResponseTO(
                    user.id(),
                    user.name(),
                    user.email(),
                    user.createdAt().atOffset(ZoneOffset.UTC)
            );
        }

        private ErrorResponseTO notFound(String userId) {
            return new ErrorResponseTO("User with id '" + userId + "' was not found");
        }
    }
    ```

    1.  Делегат — обычный компонент Kora; сгенерированный контроллер получает его через конструктор.
    2.  У `204 No Content` в контракте нет тела, поэтому у сгенерированной записи нет компонентов.
    3.  `default` в OpenAPI — это документация, а не поведение сервера: отсутствующие query-параметры приходят как `null`, и значения по умолчанию подставляет делегат.
    4.  Объявленный заголовок ответа `X-Updated-At` становится вторым компонентом обертки `200`.
    5.  `format: date-time` отображается на `OffsetDateTime`, поэтому внутренний `LocalDateTime` конвертируется на границе.

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/io/koraframework/guide/openapi/httpserver/controller/UserApiDelegateImpl.kt`:

    ```kotlin
    package io.koraframework.guide.openapi.httpserver.controller

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.openapi.httpserver.dto.UserRequest
    import io.koraframework.guide.openapi.httpserver.dto.UserResponse
    import io.koraframework.guide.openapi.httpserver.service.UserService
    import io.koraframework.guide.openapi.httpserver.user.api.UsersApiDelegate
    import io.koraframework.guide.openapi.httpserver.user.api.UsersApiResponses
    import io.koraframework.guide.openapi.httpserver.user.model.ErrorResponseTO
    import io.koraframework.guide.openapi.httpserver.user.model.UserRequestTO
    import io.koraframework.guide.openapi.httpserver.user.model.UserResponseTO
    import java.time.Instant
    import java.time.ZoneOffset

    @Component //(1)!
    class UserApiDelegateImpl(
        private val userService: UserService
    ) : UsersApiDelegate {

        override fun createUser(userRequest: UserRequestTO): UsersApiResponses.CreateUserApiResponse {
            val created = userService.createUser(UserRequest(userRequest.name, userRequest.email))
            return UsersApiResponses.CreateUserApiResponse.CreateUser201ApiResponse(toGenerated(created))
        }

        override fun deleteUser(userId: String): UsersApiResponses.DeleteUserApiResponse {
            if (userService.getUser(userId) == null) {
                return UsersApiResponses.DeleteUserApiResponse.DeleteUser404ApiResponse(
                    notFound(userId)
                )
            }

            userService.deleteUser(userId)
            return UsersApiResponses.DeleteUserApiResponse.DeleteUser204ApiResponse() //(2)!
        }

        override fun getUser(userId: String): UsersApiResponses.GetUserApiResponse {
            val user = userService.getUser(userId)
            return if (user == null) {
                UsersApiResponses.GetUserApiResponse.GetUser404ApiResponse(notFound(userId))
            } else {
                UsersApiResponses.GetUserApiResponse.GetUser200ApiResponse(toGenerated(user))
            }
        }

        override fun getUsers(page: Int?, size: Int?, sort: String?): UsersApiResponses.GetUsersApiResponse {
            val effectivePage = page ?: 0 //(3)!
            val effectiveSize = size ?: 10
            val effectiveSort = sort ?: "name"
            val users = userService.getUsers(effectivePage, effectiveSize, effectiveSort)
                .map(::toGenerated)
            return UsersApiResponses.GetUsersApiResponse.GetUsers200ApiResponse(users)
        }

        override fun updateUser(userId: String, userRequest: UserRequestTO): UsersApiResponses.UpdateUserApiResponse {
            if (userService.getUser(userId) == null) {
                return UsersApiResponses.UpdateUserApiResponse.UpdateUser404ApiResponse(
                    notFound(userId)
                )
            }

            val updated = userService.updateUser(userId, UserRequest(userRequest.name, userRequest.email))
            return UsersApiResponses.UpdateUserApiResponse.UpdateUser200ApiResponse(
                toGenerated(updated),
                Instant.now().toString() //(4)!
            )
        }

        private fun toGenerated(user: UserResponse): UserResponseTO { //(5)!
            return UserResponseTO(
                id = user.id,
                name = user.name,
                email = user.email,
                createdAt = user.createdAt.atOffset(ZoneOffset.UTC)
            )
        }

        private fun notFound(userId: String): ErrorResponseTO {
            return ErrorResponseTO("User with id '$userId' was not found")
        }
    }
    ```

    1.  Делегат — обычный компонент Kora; сгенерированный контроллер получает его через конструктор.
    2.  У `204 No Content` в контракте нет тела, поэтому у сгенерированного класса нет свойств.
    3.  `default` в OpenAPI — это документация, а не поведение сервера: отсутствующие query-параметры приходят как `null`, и значения по умолчанию подставляет делегат.
    4.  Объявленный заголовок ответа `X-Updated-At` становится вторым компонентом обертки `200`.
    5.  `format: date-time` отображается на `OffsetDateTime`, поэтому внутренний `LocalDateTime` конвертируется на границе — а именованные аргументы не дают перепутать четыре строковых значения.

Этот шаг вводит ключевую абстракцию руководства.

В ручной версии `http-server` контроллер сам решал:

- как принять HTTP-вход
- какой статус вернуть
- как построить ответ

В OpenAPI-версии эта ответственность переезжает в реализацию делегата.

Сгенерированный контроллер занимается низкоуровневым HTTP-транспортом. Ваш делегат занимается:

- вызовом сервисного слоя
- выбором правильной сгенерированной обертки ответа
- отображением между сгенерированными моделями OpenAPI и внутренними DTO приложения

Поскольку контракт OpenAPI теперь дает ответам `404` и `500` общее тело `ErrorResponseTO`, делегат может возвращать типизированные полезные нагрузки ошибок, а не только пустые варианты статусов. Это
делает сгенерированные обертки полезнее и для серверного, и для клиентского кода, потому что ответы с ошибками тоже становятся частью контракта.

Этот слой отображения появился не случайно. Это здоровое разделение:

- сгенерированные модели принадлежат контракту API
- внутренние DTO принадлежат вашему приложению

Явная граница делает приложение проще в развитии.

## Конфигурация { #config }

Теперь опубликуем контракт и интерактивную документацию из работающего приложения.

Обновите `src/main/resources/application.conf`:

Полное описание конфигурации смотрите в [HTTP-сервер](../documentation/http-server.md#configuration), [OpenAPI Management](../documentation/openapi-management.md#configuration)
и [Логирование SLF4J](../documentation/logging-slf4j.md).

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
      port = 8080 //(1)!
      system.port = 8085 //(2)!
      telemetry.logging.enabled = true //(3)!
    }

    openapi {
      management {
        enabled = true //(4)!
        files = [ "openapi/user-http-server.yaml" ] //(5)!
        path = "/openapi" //(6)!
        swaggerui {
          enabled = true //(7)!
          path = "/swagger-ui" //(8)!
        }
      }
    }

    logging.levels {
      "root" = "WARN" //(9)!
      "io.koraframework" = "INFO" //(10)!
      "io.koraframework.guide.openapi.httpserver" = "INFO" //(11)!
    }
    ```

    1.  Публичный HTTP-порт для конечных точек приложения (по умолчанию: `8080`).
    2.  Системный HTTP-порт для проб, метрик и служебных конечных точек (по умолчанию: `8085`).
    3.  Включает логирование запросов публичного HTTP-сервера (по умолчанию: `false`).
    4.  Включает публикацию OpenAPI (по умолчанию: `false`).
    5.  Ресурсы classpath для публикации. Это **список**, даже для одного файла.
    6.  Путь, по которому отдается контракт (по умолчанию: `/openapi`).
    7.  Включает страницу Swagger UI (по умолчанию: `false`).
    8.  Путь страницы Swagger UI (по умолчанию: `/swagger-ui`).
    9.  Уровень логирования корневого логгера.
    10. Уровень логирования логгеров фреймворка Kora.
    11. Уровень логирования пакета приложения.

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      port: 8080 #(1)!
      system:
        port: 8085 #(2)!
      telemetry:
        logging:
          enabled: true #(3)!
    openapi:
      management:
        enabled: true #(4)!
        files: [ "openapi/user-http-server.yaml" ] #(5)!
        path: "/openapi" #(6)!
        swaggerui:
          enabled: true #(7)!
          path: "/swagger-ui" #(8)!
    logging:
      levels:
        root: "WARN" #(9)!
        "io.koraframework": "INFO" #(10)!
        "io.koraframework.guide.openapi.httpserver": "INFO" #(11)!
    ```

    1.  Публичный HTTP-порт для конечных точек приложения (по умолчанию: `8080`).
    2.  Системный HTTP-порт для проб, метрик и служебных конечных точек (по умолчанию: `8085`).
    3.  Включает логирование запросов публичного HTTP-сервера (по умолчанию: `false`).
    4.  Включает публикацию OpenAPI (по умолчанию: `false`).
    5.  Ресурсы classpath для публикации. Это **список**, даже для одного файла.
    6.  Путь, по которому отдается контракт (по умолчанию: `/openapi`).
    7.  Включает страницу Swagger UI (по умолчанию: `false`).
    8.  Путь страницы Swagger UI (по умолчанию: `/swagger-ui`).
    9.  Уровень логирования корневого логгера.
    10. Уровень логирования логгеров фреймворка Kora.
    11. Уровень логирования пакета приложения.

Это дает две очень практичные конечные точки:

- `/openapi` возвращает документ OpenAPI
- `/swagger-ui` дает интерактивный интерфейс для изучения и тестирования API

Обе обслуживаются **публичным** HTTP-сервером на `httpServer.port`, а не на системном порту, потому что модуль управления регистрирует обычные обработчики запросов. Если вам ближе более легкая страница
просмотра, `openapi.management.scalar.enabled = true` публикует [Scalar](https://scalar.com/) на `/scalar` из того же контракта; обе страницы поставляются внутри модуля как самодостаточные ресурсы,
поэтому ни одной из них не нужен доступ в интернет или CDN.

Это одно из главных преимуществ контрактной разработки. Документация — не то, что пишут потом. Она часть той же сборки, которая генерирует серверный слой.

## Проверка приложения { #check-app }

```bash
./gradlew clean classes
./gradlew test
./gradlew run
```

`classes` здесь — осмысленная первая проверка: она запускает генерацию по OpenAPI, затем аннотационный процессор или KSP, и падает на этапе компиляции, если делегат не соответствует контракту.

Проверки публичного API:

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com"}'

curl http://localhost:8080/users/1
curl "http://localhost:8080/users?page=0&size=10&sort=name"

curl -i -X PUT http://localhost:8080/users/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Name", "email": "updated@example.com"}'

curl -X DELETE http://localhost:8080/users/1
```

Флаг `-i` на вызове обновления стоит оставить: он показывает заголовок ответа `X-Updated-At`, объявленный контрактом и заполняемый делегатом.

Проверки контракта:

```bash
curl http://localhost:8080/openapi
```

Откройте в браузере:

```text
http://localhost:8080/swagger-ui
```

Проверки системного API:

```bash
curl http://localhost:8085/system/readiness
# Expected output: OK
curl http://localhost:8085/system/liveness
# Expected output: OK
```

На этом этапе приложение ведет себя как знакомый CRUD-сервис из `http-server`, но HTTP-слоем теперь управляет контракт OpenAPI.

## Тест делегата { #delegate-test }

Поскольку делегат — обычный компонент, его можно тестировать вообще без HTTP-клиента: `@KoraAppTest` собирает настоящий граф и внедряет сгенерированный интерфейс.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/test/java/io/koraframework/guide/openapi/httpserver/OpenApiHttpServerAppTest.java`:

    ```java
    package io.koraframework.guide.openapi.httpserver;

    import static org.junit.jupiter.api.Assertions.assertEquals;
    import static org.junit.jupiter.api.Assertions.assertInstanceOf;
    import static org.junit.jupiter.api.Assertions.assertNotNull;

    import org.junit.jupiter.api.Test;
    import io.koraframework.guide.openapi.httpserver.user.api.UsersApiDelegate;
    import io.koraframework.guide.openapi.httpserver.user.api.UsersApiResponses;
    import io.koraframework.guide.openapi.httpserver.user.model.UserRequestTO;
    import io.koraframework.test.extension.junit5.KoraAppTest;
    import io.koraframework.test.extension.junit5.TestComponent;

    @KoraAppTest(Application.class)
    class OpenApiHttpServerAppTest {

        @TestComponent
        private UsersApiDelegate usersApiDelegate; //(1)!

        @Test
        void crudFlowWorksThroughDelegate() throws Exception {
            var createResponse = this.usersApiDelegate.createUser(new UserRequestTO("John Doe", "john@example.com"));
            var create201 = assertInstanceOf(UsersApiResponses.CreateUserApiResponse.CreateUser201ApiResponse.class, createResponse); //(2)!
            assertNotNull(create201.content());
            assertEquals("John Doe", create201.content().name());

            var getUserResponse = this.usersApiDelegate.getUser(create201.content().id());
            var getUser200 = assertInstanceOf(UsersApiResponses.GetUserApiResponse.GetUser200ApiResponse.class, getUserResponse);
            assertEquals("john@example.com", getUser200.content().email());

            var getUsersResponse = this.usersApiDelegate.getUsers(0, 10, "name");
            var getUsers200 = assertInstanceOf(UsersApiResponses.GetUsersApiResponse.GetUsers200ApiResponse.class, getUsersResponse);
            assertEquals(1, getUsers200.content().size());

            var updateResponse = this.usersApiDelegate.updateUser(create201.content().id(), new UserRequestTO("John Updated", "john.updated@example.com"));
            var update200 = assertInstanceOf(UsersApiResponses.UpdateUserApiResponse.UpdateUser200ApiResponse.class, updateResponse);
            assertEquals("John Updated", update200.content().name());
            assertNotNull(update200.xUpdatedAt()); //(3)!

            var deleteResponse = this.usersApiDelegate.deleteUser(create201.content().id());
            assertInstanceOf(UsersApiResponses.DeleteUserApiResponse.DeleteUser204ApiResponse.class, deleteResponse);

            var getAfterDeleteResponse = this.usersApiDelegate.getUser(create201.content().id());
            assertInstanceOf(UsersApiResponses.GetUserApiResponse.GetUser404ApiResponse.class, getAfterDeleteResponse);
        }
    }
    ```

    1.  Внедряет сгенерированный интерфейс, поэтому тест разрешает вашу реализацию с `@Component` через настоящий граф.
    2.  Проверка подтипа ответа — серверный аналог проверки кода статуса.
    3.  Объявленный заголовок `X-Updated-At` является компонентом обертки, поэтому проверяется как любое другое значение.

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/test/kotlin/io/koraframework/guide/openapi/httpserver/OpenApiHttpServerAppTest.kt`:

    ```kotlin
    package io.koraframework.guide.openapi.httpserver

    import org.junit.jupiter.api.Assertions.assertEquals
    import org.junit.jupiter.api.Assertions.assertInstanceOf
    import org.junit.jupiter.api.Assertions.assertNotNull
    import org.junit.jupiter.api.Test
    import io.koraframework.guide.openapi.httpserver.user.api.UsersApiDelegate
    import io.koraframework.guide.openapi.httpserver.user.api.UsersApiResponses
    import io.koraframework.guide.openapi.httpserver.user.model.UserRequestTO
    import io.koraframework.test.extension.junit5.KoraAppTest
    import io.koraframework.test.extension.junit5.TestComponent

    @KoraAppTest(Application::class)
    class OpenApiHttpServerAppTest {

        @TestComponent
        lateinit var usersApiDelegate: UsersApiDelegate //(1)!

        @Test
        fun crudFlowWorksThroughDelegate() {
            val createResponse = usersApiDelegate.createUser(UserRequestTO(name = "John Doe", email = "john@example.com"))
            val create201 = assertInstanceOf(
                UsersApiResponses.CreateUserApiResponse.CreateUser201ApiResponse::class.java,
                createResponse
            ) //(2)!
            assertNotNull(create201.content)
            assertEquals("John Doe", create201.content.name)

            val getUserResponse = usersApiDelegate.getUser(create201.content.id)
            val getUser200 =
                assertInstanceOf(UsersApiResponses.GetUserApiResponse.GetUser200ApiResponse::class.java, getUserResponse)
            assertEquals("john@example.com", getUser200.content.email)

            val getUsersResponse = usersApiDelegate.getUsers(0, 10, "name")
            val getUsers200 =
                assertInstanceOf(UsersApiResponses.GetUsersApiResponse.GetUsers200ApiResponse::class.java, getUsersResponse)
            assertEquals(1, getUsers200.content.size)

            val updateResponse = usersApiDelegate.updateUser(
                create201.content.id,
                UserRequestTO(name = "John Updated", email = "john.updated@example.com")
            )
            val update200 = assertInstanceOf(
                UsersApiResponses.UpdateUserApiResponse.UpdateUser200ApiResponse::class.java,
                updateResponse
            )
            assertEquals("John Updated", update200.content.name)
            assertNotNull(update200.xUpdatedAt) //(3)!

            val deleteResponse = usersApiDelegate.deleteUser(create201.content.id)
            assertInstanceOf(UsersApiResponses.DeleteUserApiResponse.DeleteUser204ApiResponse::class.java, deleteResponse)

            val getAfterDeleteResponse = usersApiDelegate.getUser(create201.content.id)
            assertInstanceOf(UsersApiResponses.GetUserApiResponse.GetUser404ApiResponse::class.java, getAfterDeleteResponse)
        }
    }
    ```

    1.  Внедряет сгенерированный интерфейс, поэтому тест разрешает вашу реализацию с `@Component` через настоящий граф.
    2.  Проверка подтипа ответа — серверный аналог проверки кода статуса.
    3.  Объявленный заголовок `X-Updated-At` является свойством обертки, поэтому проверяется как любое другое значение.

Выполните:

```bash
./gradlew test
```

Тест проверяет создание, получение по идентификатору, список, обновление, удаление и `404` после удаления. Это полезная контрольная точка: она доказывает, что сгенерированный слой API и ваша реализация
делегата корректно связаны.

## Лучшие практики { #best-practices }

- Держите контракт OpenAPI близким к реальному поведению приложения. Контракт должен описывать реальность, а не будущие планы.
- Считайте сгенерированный код только артефактом сборки. Не правьте и не коммитьте файлы из `build/generated/user-http-server`.
- Держите бизнес-логику в сервисах, а не в сгенерированных классах.
- Используйте делегаты как транспортную границу между сгенерированными типами API и внутренними моделями приложения.
- Перегенерируйте серверный код в рамках обычных сборок, чтобы контракт и скомпилированное приложение не могли разойтись.
- Давайте каждой операции стабильный `operationId`: именно он именует метод делегата и все сгенерированные типы ответов, поэтому его переименование — ломающее изменение на уровне исходников.
- Подставляйте значения `default` из OpenAPI сами в делегате, потому что сгенерированные серверы отдают `null` для отсутствующих опциональных параметров.

## Итоги { #summary }

Вы взяли CRUD-сервер пользователей из руководства [HTTP-сервер](http-server.md) и пересобрали его HTTP-слой в контрактном стиле:

- API теперь описано в `user-http-server.yaml`
- Kora генерирует серверный слой в `build/generated/user-http-server`
- приложение реализует `UsersApiDelegate`
- привычные слои сервиса и репозитория остались на месте
- приложение отдает `/openapi` и `/swagger-ui`

Поведение осталось знакомым, но транспортным слоем теперь управляет контракт, а не написанный вручную контроллер.

## Ключевые понятия { #key-concepts }

- контрактная разработка начинается с общей спецификации API
- Kora генерирует серверный код по OpenAPI ровно в двух серверных режимах: `java-server` и `kotlin-server`
- сгенерированные контроллеры и делегаты разделяют транспортную обвязку и прикладную логику
- делегаты — удачное место для отображения между моделями контракта и внутренними DTO
- добавление новых статусов вроде `500` в OpenAPI меняет и сгенерированные обертки ответов
- `enableServerValidation` превращает ограничения схемы в настоящие аннотации валидации на сгенерированных моделях
- Swagger UI, Scalar и документ OpenAPI становятся естественной частью приложения, когда контракт встроен в проект

## Устранение неполадок { #troubleshooting }

**Генерация падает с `UnsupportedClassVersionError`:**

- Демон `Gradle` работает на более старой JDK, чем та, под которую собрана Kora. Генератор находится в classpath buildscript, поэтому сама JVM `Gradle` должна быть `JDK 25` или новее.
- Выполните `./gradlew --stop`, укажите `org.gradle.java.home` на установку JDK 25 и повторите.

**Генерация падает с «Invalid OpenAPI generator `mode`»:**

- Kora 2.0 поддерживает ровно четыре режима: `java-client`, `java-server`, `kotlin-client`, `kotlin-server`.
- Реактивных и `suspend`-режимов из прежних версий больше нет; сгенерированный серверный и клиентский код синхронный.

**Кодогенерация не запускается:**

Проверьте, что:

- плагин `org.openapi.generator` применен, а `GenerateTask` импортирован
- на задаче установлен `generatorName = "kora"`
- в `Java` настроен `compileJava.dependsOn openApiGenerateUsersHttpServer`
- в `Kotlin` каждая задача `ksp*` зависит от задачи генерации

**Приложение не находит сгенерированные классы:**

Проверьте, что каталог сгенерированных исходников добавлен в основной source set:

- `build/generated/user-http-server`

Также убедитесь, что настройки пакетов совпадают с вашими импортами:

- `io.koraframework.guide.openapi.httpserver.user.api`
- `io.koraframework.guide.openapi.httpserver.user.model`

**Swagger UI недоступен:**

Убедитесь, что:

- `OpenApiManagementModule` подключен в `Application`
- заданы `openapi.management.enabled = true` и `openapi.management.swaggerui.enabled = true`
- в `openapi.management.files` перечислен контракт, и значение является **списком** — ключ называется `files`, а не `file`
- вы обращаетесь к **публичному** порту `8080`, а не к системному `8085`

**Kora не находит делегат:**

Убедитесь, что:

- делегат размечен аннотацией `@Component`
- он реализует сгенерированный `UsersApiDelegate`
- он импортирует сгенерированный пакет, настроенный в файле сборки

**Ручной контроллер конфликтует со сгенерированным сервером:**

В этом варианте приложения написанный вручную контроллер пользователей не должен оставаться рядом со сгенерированным контроллером. Два обработчика на один метод и путь — это ошибка сборки графа. После
перехода на сгенерированный транспортный слой основной точкой реализации HTTP-поведения становится делегат.

**Отсутствует вариант обертки ответа:**

Сгенерированные варианты ответов существуют только для тех кодов статуса, которые явно перечислены в контракте OpenAPI.

Поэтому если вы ждете сгенерированную абстракцию для `500` вида `GetUser500ApiResponse`, убедитесь, что `500` присутствует в секции `responses` этой операции в `user-http-server.yaml`.

**Пагинация и сортировка ведут себя так, будто значения по умолчанию из контракта проигнорированы:**

Так и есть. `default` на query-параметре в OpenAPI — это документация для читателей контракта; сгенерированный сервер передает `null` для отсутствующего параметра, поэтому значение по умолчанию должен
подставить делегат.

## Что дальше? { #whats-next }

- [HTTP-клиент](http-client.md), если вы еще не собирали клиентское приложение.
- [OpenAPI HTTP-клиент](openapi-http-client.md) после HTTP-клиента, чтобы сгенерировать клиент по тому же контракту.
- [Продвинутый HTTP-сервер](http-server-advanced.md) перед [Продвинутым OpenAPI HTTP-сервером](openapi-http-server-advanced.md), потому что продвинутое OpenAPI-руководство объединяет обе ветки.
- [Валидация](validation.md), чтобы сравнить ручную валидацию с валидацией по спецификации.

## Помощь { #help }

Если что-то не получается:

- сравните с [Kora Java OpenAPI HTTP Server App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-openapi-http-server-app) и [Kora Kotlin OpenAPI HTTP Server App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-openapi-http-server-app)
- сравните с [HTTP-сервер](http-server.md), чтобы увидеть, что заменил сгенерированный контроллер
- посмотрите [документацию OpenAPI Codegen](../documentation/openapi-codegen.md)
- посмотрите [документацию OpenAPI Management](../documentation/openapi-management.md)
