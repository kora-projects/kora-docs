---
search:
  exclude: true
title: Контрактный HTTP-сервер с OpenAPI
summary: Continue the HTTP Server guide by replacing the handwritten controller with OpenAPI-generated server code and a delegate
tags: openapi, http-server, swagger, code-generation, contract-first
---

# Контрактный HTTP-сервер с OpenAPI { #contract-first-http-server }

Это руководство знакомит с разработкой HTTP-сервера в Kora и OpenAPI в подходе «сначала контракт». В нем разбирается, как спецификация OpenAPI превращается в сгенерированные серверные интерфейсы и
модели, как реализация делегата соединяет этот сгенерированный транспортный слой с прикладными сервисами и как проверка данных и метаданные ответов управляются контрактом. Вы также увидите, как
сгенерированный код остается отделенным от рукописной бизнес-логики, чтобы описание API оставалось источником истины.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java OpenAPI HTTP Server App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-openapi-http-server-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin OpenAPI HTTP Server App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-openapi-http-server-app).

## Что вы создадите { #youll-build }

Вы пересоберете знакомый CRUD API из `http-server` в контрактном стиле:

- API пользователей будет описан в `user-http-server.yaml`
- Kora сгенерирует серверный слой в `build/generated/user-http-server`
- вы реализуете сгенерированный `UsersApiDelegate`
- `UserService`, `UserRepository` и `InMemoryUserRepository` останутся знакомыми
- приложение откроет `/openapi` и `/swagger-ui`

## Что вам понадобится { #youll-need }

- JDK 17 или новее
- Gradle 7+
- текстовый редактор или среда разработки
- пройденное руководство [HTTP-сервер](http-server.md)

## Требования { #prerequisites }

!!! note "Обязательно: сначала пройдите HTTP-сервер"

    Это руководство предполагает, что вы прошли **[HTTP-сервер](http-server.md)** и уже понимаете CRUD-приложение пользователей с `UserRequest`, `UserResponse`, `UserRepository`, `InMemoryUserRepository` и `UserService`.

    Мы сохраним эти идеи и заменим только рукописный слой HTTP-контроллера.

    Если вы еще не прошли руководство по HTTP-серверу, сначала сделайте это, потому что это руководство сосредоточено на контрактной генерации OpenAPI, а не на повторном построении CRUD-сервиса с нуля.

## Обзор { #overview }

В этом руководстве мы постепенно перейдем от ручного сервера к контрактному серверу:

1. поймем, что меняется, когда OpenAPI становится источником истины
2. опишем существующий CRUD API в файле OpenAPI
3. настроим генерацию Kora по OpenAPI
4. изучим сгенерированные делегат, контроллер, обертки ответов и модели
5. сохраним знакомые слои сервиса и репозитория
6. реализуем сгенерированный делегат вместо рукописного контроллера
7. откроем OpenAPI и Swagger UI
8. запустим и проверим приложение

### Контрактная разработка? { #contract-first-development }

В подходе «сначала код» разработчики обычно начинают с контроллера и только потом документируют, что этот контроллер делает. Это работает, но со временем часто создает трение:

- документация расходится с кодом
- потребители и поставщики API обсуждают поведение неформально, а не через один общий контракт
- формы ответов и правила проверки данных дублируются
- сгенерированным клиентам становится сложнее доверять, потому что контракт не является главным источником истины

Контрактная разработка меняет порядок.

Вместо того чтобы говорить «контроллер определяет API», мы говорим «контракт OpenAPI определяет API». Из этого контракта инструменты могут генерировать:

- серверные интерфейсы
- модели запросов и ответов
- подсказки для проверки данных
- документацию OpenAPI
- позже еще и HTTP-клиенты

Это особенно полезно, когда от одного API зависят несколько команд или несколько приложений. Все они могут смотреть на один и тот же файл контракта вместо того, чтобы восстанавливать поведение
контроллера по коду.

### HTTP-основы { #http-basics }

Руководство [HTTP-сервер](http-server.md) по-прежнему является местом, где стоит сначала изучить:

- `@HttpController`
- `@HttpRoute`
- `@Path`
- `@Query`
- `@Json`
- `HttpResponseEntity`

Здесь мы развиваем эти знания.

Мы не меняем предметную область и не меняем CRUD-поведение. Мы меняем **способ объявления HTTP-слоя**:

- раньше: рукописные методы контроллера
- теперь: контракт OpenAPI + сгенерированный серверный код + реализация делегата

Поэтому это руководство является естественным следующим шагом, а не отдельным несвязанным примером.

## Зависимости { #dependencies }

Сначала добавьте модули и инструменты сборки, необходимые для генерации OpenAPI и публикации документации.

===! ":fontawesome-brands-java: `Java`"

    ```groovy title="build.gradle"
    import org.openapitools.generator.gradle.plugin.tasks.GenerateTask

    buildscript {
        dependencies {
            classpath("ru.tinkoff.kora:openapi-generator:$koraVersion")
        }
    }

    plugins {
        id "application"
        id "org.openapi.generator" version "7.14.0"
    }

    dependencies {
        implementation("ru.tinkoff.kora:config-hocon")
        implementation("ru.tinkoff.kora:http-server-undertow")
        implementation("ru.tinkoff.kora:json-module")
        implementation("ru.tinkoff.kora:logging-logback")
        implementation("ru.tinkoff.kora:openapi-management")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="build.gradle.kts"
    import org.openapitools.generator.gradle.plugin.tasks.GenerateTask

    buildscript {
        dependencies {
            classpath("ru.tinkoff.kora:openapi-generator:$koraVersion")
        }
    }

    plugins {
        id("application")
        id("org.openapi.generator") version "7.14.0"
    }

    dependencies {
        implementation("ru.tinkoff.kora:config-hocon")
        implementation("ru.tinkoff.kora:http-server-undertow")
        implementation("ru.tinkoff.kora:json-module")
        implementation("ru.tinkoff.kora:logging-logback")
        implementation("ru.tinkoff.kora:openapi-management")
    }
    ```

На этом шаге полезно понимать, зачем нужна каждая зависимость:

- `openapi-generator` позволяет Gradle генерировать серверный код Kora из контракта
- `openapi-management` открывает OpenAPI и Swagger UI

Также нам нужен модуль управления в графе приложения:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/openapi/httpserver/Application.java"
    package ru.tinkoff.kora.guide.openapi.httpserver;

    import ru.tinkoff.kora.application.graph.KoraApplication;
    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.config.hocon.HoconConfigModule;
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule;
    import ru.tinkoff.kora.json.module.JsonModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;
    import ru.tinkoff.kora.openapi.management.OpenApiManagementModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            UndertowHttpServerModule,
            JsonModule,
            LogbackModule,
            OpenApiManagementModule {  // <----- Подключили модуль

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/openapi/httpserver/Application.kt"
    package ru.tinkoff.kora.guide.openapi.httpserver

    import ru.tinkoff.kora.application.graph.KoraApplication
    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.config.hocon.HoconConfigModule
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule
    import ru.tinkoff.kora.json.module.JsonModule
    import ru.tinkoff.kora.logging.logback.LogbackModule
    import ru.tinkoff.kora.openapi.management.OpenApiManagementModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        UndertowHttpServerModule,
        JsonModule,
        LogbackModule,
        OpenApiManagementModule  // <----- Подключили модуль

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

После этого шага мы подготовили приложение к контрактному серверу, но еще ничего не сгенерировали.

## Контракт как OpenAPI { #openapi-contract }

Теперь мы выносим контракт API из аннотаций Java или Kotlin в общий файл OpenAPI.

Создайте:

`src/main/resources/openapi/user-http-server.yaml`

??? example "OpenAPI-контракт"

    ```yaml title="src/main/resources/openapi/user-http-server.yaml"
    openapi: 3.0.3
    info:
        title: User Management API
        description: Contract-first version of the HTTP Server guide API
        version: 1.0.0
    tags:
        -   name: users
            description: User management operations
    paths:
        /users:
            get:
                tags:
                    - users
                operationId: getUsers
                summary: Get users
                parameters:
                    -   name: page
                        in: query
                        required: false
                        schema:
                            type: integer
                            minimum: 0
                            default: 0
                    -   name: size
                        in: query
                        required: false
                        schema:
                            type: integer
                            minimum: 1
                            maximum: 100
                            default: 10
                    -   name: sort
                        in: query
                        required: false
                        schema:
                            type: string
                            enum: [ name, email, createdAt ]
                            default: name
                responses:
                    "200":
                        description: Users returned
                        content:
                            application/json:
                                schema:
                                    type: array
                                    items:
                                        $ref: "#/components/schemas/UserResponseTO"
                    "500":
                        description: Internal server error
                        content:
                            application/json:
                                schema:
                                    $ref: "#/components/schemas/ErrorResponseTO"
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
                                $ref: "#/components/schemas/UserRequestTO"
                responses:
                    "201":
                        description: User created
                        content:
                            application/json:
                                schema:
                                    $ref: "#/components/schemas/UserResponseTO"
                    "500":
                        description: Internal server error
                        content:
                            application/json:
                                schema:
                                    $ref: "#/components/schemas/ErrorResponseTO"
        /users/{userId}:
            get:
                tags:
                    - users
                operationId: getUser
                summary: Get user by id
                parameters:
                    -   name: userId
                        in: path
                        required: true
                        schema:
                            type: string
                responses:
                    "200":
                        description: User returned
                        content:
                            application/json:
                                schema:
                                    $ref: "#/components/schemas/UserResponseTO"
                    "404":
                        description: User not found
                        content:
                            application/json:
                                schema:
                                    $ref: "#/components/schemas/ErrorResponseTO"
                    "500":
                        description: Internal server error
                        content:
                            application/json:
                                schema:
                                    $ref: "#/components/schemas/ErrorResponseTO"
            put:
                tags:
                    - users
                operationId: updateUser
                summary: Update user
                parameters:
                    -   name: userId
                        in: path
                        required: true
                        schema:
                            type: string
                requestBody:
                    required: true
                    content:
                        application/json:
                            schema:
                                $ref: "#/components/schemas/UserRequestTO"
                responses:
                    "200":
                        description: User updated
                        headers:
                            X-Updated-At:
                                required: true
                                schema:
                                    type: string
                        content:
                            application/json:
                                schema:
                                    $ref: "#/components/schemas/UserResponseTO"
                    "404":
                        description: User not found
                        content:
                            application/json:
                                schema:
                                    $ref: "#/components/schemas/ErrorResponseTO"
                    "500":
                        description: Internal server error
                        content:
                            application/json:
                                schema:
                                    $ref: "#/components/schemas/ErrorResponseTO"
            delete:
                tags:
                    - users
                operationId: deleteUser
                summary: Delete user
                parameters:
                    -   name: userId
                        in: path
                        required: true
                        schema:
                            type: string
                responses:
                    "204":
                        description: User deleted
                    "404":
                        description: User not found
                        content:
                            application/json:
                                schema:
                                    $ref: "#/components/schemas/ErrorResponseTO"
                    "500":
                        description: Internal server error
                        content:
                            application/json:
                                schema:
                                    $ref: "#/components/schemas/ErrorResponseTO"
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

Здесь мы не придумываем новый API. Мы описываем тот же CRUD API пользователей, который уже существует в руководстве `http-server`:

- те же маршруты `/users` и `/users/{userId}`
- те же параметры запроса для получения списка
- те же формы запросов и ответов
- то же поведение `404` и `204`, теперь с явным телом `ErrorResponseTO` для случаев ошибки
- тот же заголовок обновления `X-Updated-At`

Это важный учебный момент. Контрактная разработка не меняет бизнес-идею. Она переносит транспортный контракт в формальный общий источник истины.

## OpenAPI кодогенерация { #openapi-codegen }

Подробные параметры серверной генерации, `mode = server`, `delegateMethodBodyMode` описаны в разделе [OpenAPI Codegen: сервер](../documentation/openapi-codegen.md#server).

Теперь сообщите Gradle, как генерировать серверный код из этого контракта.

===! ":fontawesome-brands-java: `Java`"

    ```groovy title="build.gradle"
    def openApiGenerateUsersHttpServer = tasks.register("openApiGenerateUsersHttpServer", GenerateTask) {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/user-http-server.yaml"
        outputDir = "$buildDir/generated/user-http-server"
        def corePackage = "ru.tinkoff.kora.guide.openapi.httpserver.user"
        apiPackage = "${corePackage}.api"
        modelPackage = "${corePackage}.model"
        invokerPackage = "${corePackage}.invoker"
        configOptions = [
                mode                  : "java-server",
        ]
    }

    sourceSets.main {
        java.srcDirs += openApiGenerateUsersHttpServer.get().outputDir
    }

    compileJava.dependsOn openApiGenerateUsersHttpServer
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="build.gradle.kts"
    val openApiGenerateUsersHttpServer = tasks.register<GenerateTask>("openApiGenerateUsersHttpServer") {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/user-http-server.yaml"
        outputDir = "$buildDir/generated/user-http-server"
        val corePackage = "ru.tinkoff.kora.guide.openapi.httpserver.user"
        apiPackage = "$corePackage.api"
        modelPackage = "$corePackage.model"
        invokerPackage = "$corePackage.invoker"
        configOptions = mapOf(
            "mode" to "java-server",
        )
    }

    sourceSets.main {
        java.srcDir(openApiGenerateUsersHttpServer.get().outputDir)
    }

    tasks.compileJava {
        dependsOn(openApiGenerateUsersHttpServer)
    }
    ```

На этом шаге важнее всего три детали:

- сгенерированный код будет записан в `build/generated/user-http-server`
- сгенерированные типы будут находиться внутри `ru.tinkoff.kora.guide.openapi.httpserver.user`
- генерация автоматически выполняется перед компиляцией

Это шаг сборки, который превращает статический YAML-контракт в настоящий серверный Java-код.

## Что создает генератор { #generated-output }

Запустите:

```bash
./gradlew clean classes
```

Теперь посмотрите на сгенерированные файлы:

===! ":fontawesome-brands-java: `Java`"

    - `build/generated/user-http-server/ru/tinkoff/kora/guide/openapi/httpserver/user/api/UsersApiDelegate.java`
    - `build/generated/user-http-server/ru/tinkoff/kora/guide/openapi/httpserver/user/api/UsersApiController.java`
    - `build/generated/user-http-server/ru/tinkoff/kora/guide/openapi/httpserver/user/api/UsersApiResponses.java`
    - `build/generated/user-http-server/ru/tinkoff/kora/guide/openapi/httpserver/user/model/UserRequestTO.java`
    - `build/generated/user-http-server/ru/tinkoff/kora/guide/openapi/httpserver/user/model/UserResponseTO.java`
    - `build/generated/user-http-server/ru/tinkoff/kora/guide/openapi/httpserver/user/model/ErrorResponseTO.java`

=== ":simple-kotlin: `Kotlin`"

    - `build/generated/user-http-server/ru/tinkoff/kora/guide/openapi/httpserver/user/api/UsersApiDelegate.kt`
    - `build/generated/user-http-server/ru/tinkoff/kora/guide/openapi/httpserver/user/api/UsersApiController.kt`
    - `build/generated/user-http-server/ru/tinkoff/kora/guide/openapi/httpserver/user/api/UsersApiResponses.kt`
    - `build/generated/user-http-server/ru/tinkoff/kora/guide/openapi/httpserver/user/model/UserRequestTO.kt`
    - `build/generated/user-http-server/ru/tinkoff/kora/guide/openapi/httpserver/user/model/UserResponseTO.kt`
    - `build/generated/user-http-server/ru/tinkoff/kora/guide/openapi/httpserver/user/model/ErrorResponseTO.kt`

Сгенерированный сервер вводит несколько важных абстракций, и очень полезно изучать их по одной, а не относиться к генерации как к черному ящику.

### 1. `UsersApiDelegate` { #1-usersapidelegate }

Это интерфейс, который вы реализуете в собственном коде приложения.

Вот сокращенная версия сгенерированного делегата:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface UsersApiDelegate {

        UsersApiResponses.CreateUserApiResponse createUser(
            UserRequestTO userRequestTO
        ) throws Exception;

        UsersApiResponses.GetUserApiResponse getUser(
            String userId
        ) throws Exception;

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

        fun createUser(
            userRequestTO: UserRequestTO
        ): UsersApiResponses.CreateUserApiResponse

        fun getUser(
            userId: String
        ): UsersApiResponses.GetUserApiResponse

        fun getUsers(
            page: Int?,
            size: Int?,
            sort: String?
        ): UsersApiResponses.GetUsersApiResponse
    }
    ```

Это первый большой концептуальный сдвиг относительно `http-server.md`.

В руководстве по рукописному серверу вы сами определяли методы контроллера и украшали их транспортными аннотациями. Здесь транспортный слой уже определен контрактом, поэтому генератор дает интерфейс,
который нужно реализовать.

Это означает, что ваш код больше не говорит:

- какой HTTP-путь существует
- какой метод является `GET` или `POST`
- какое тело запроса относится к какому маршруту

Вместо этого ваш код говорит:

- как реализовать поведение, описанное контрактом
- как сопоставлять сгенерированные транспортные модели и внутренние DTO приложения
- какой вариант ответа вернуть для каждого исхода

### 2. `UsersApiController` { #2-usersapicontroller }

Это сгенерированный HTTP-контроллер, который Kora помещает в граф приложения.

Вы не редактируете его вручную, и обычно вам не нужно понимать каждую строку внутри него. Важна его ответственность:

- принять HTTP-запрос
- проверить и сопоставить транспортные данные согласно контракту
- вызвать соответствующий метод делегата
- превратить возвращенную сгенерированную обертку ответа в настоящий HTTP-ответ

Так сгенерированный контроллер становится транспортным адаптером, а ваш делегат становится границей реализации.

Такое разделение является одной из самых здоровых частей контрактной серверной генерации. Оно оставляет механику протокола HTTP в сгенерированном коде, а поведение приложения — в вашем собственном
коде.

### 3. `UsersApiResponses` { #3-usersapiresponses }

Этот файл является одним из самых полезных сгенерированных артефактов, потому что он делает транспортный контракт явным.

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

Это та же идея, которую мы исследовали в руководстве по OpenAPI-клиенту, но теперь со стороны сервера.

Контракт OpenAPI говорит, что `GET /users/{userId}` может произвести:

- `200` с телом `UserResponseTO`
- `404` с телом `ErrorResponseTO`
- `500` с телом `ErrorResponseTO`

Поэтому генератор создает одно запечатанное семейство ответов, которое моделирует эти три исхода.

Это важно, потому что контракт описывает не только запросы и успешные полезные нагрузки. Он также описывает допустимые формы ошибок, а сгенерированный серверный код сохраняет эту информацию как
настоящие типы Java или Kotlin, в зависимости от приложения руководства, которое вы создаете.

### 4. Сгенерированные модели { #4-generated-models }

Генератор также создает транспортные модели слоя контракта, такие как:

- `UserRequestTO`
- `UserResponseTO`
- `ErrorResponseTO`

Эти сгенерированные модели принадлежат границе OpenAPI, а не вашей внутренней предметной области или сервисному слою.

Именно поэтому руководству по-прежнему сохраняет внутренние DTO вроде `UserRequest` и `UserResponse` внутри кода приложения. Делегат — это место, где встречаются эти два мира:

- сгенерированные транспортные модели OpenAPI с одной стороны
- внутренние модели приложения с другой

Если держать эти слои отдельно, будущие переработки становятся намного безопаснее. Вы можете развивать внутренний код, не делая вид, что сгенерированные транспортные типы являются всей вашей
предметной моделью.

В сопровождающем приложении рукописные внутренние DTO, которые могут пересекать границу JSON, по-прежнему аннотированы `@Json`. Сгенерированные модели OpenAPI уже приходят из генератора, но ваши
собственные классы DTO запросов и ответов должны явно объявлять JSON-контракт, чтобы Kora могла сгенерировать их преобразователи во время обычной фазы обработки аннотаций.

### Разбор сгенерированного `getUser()` { #generated-getuser-walkthrough }

Проще всего понять происходящее, если пройти одну операцию от контракта до сгенерированного кода.

Файл OpenAPI объявляет:

- маршрут `GET /users/{userId}`
- один параметр пути `userId`
- три ответа: `200`, `404`, `500`

Из этого генератор создает:

- метод `getUser(String userId)` в `UsersApiDelegate`
- запечатанное семейство ответов `GetUserApiResponse`
- сгенерированный метод контроллера, который вызовет ваш делегат и сериализует выбранную обертку

Это означает, что реализация делегата может оставаться сосредоточенной на бизнес-смысле:

- если пользователь существует, вернуть `GetUser200ApiResponse`
- если пользователя нет, вернуть `GetUser404ApiResponse(new ErrorResponseTO(...))`
- если произошел настоящий внутренний сбой, транспортный слой все равно знает, что `500` является частью объявленного контракта

Это главный момент, когда идея становится очевидной: генерация OpenAPI не просто экономит набор текста. Она превращает HTTP-контракт в набор явных серверных абстракций, которые направляют вашу
реализацию.

## Сервис и репозиторий { #service-repository }

Одна из самых приятных частей такой миграции в том, что большую часть приложения **не** нужно проектировать заново.

Бизнес-часть остается знакомой:

- `UserRepository`
- `InMemoryUserRepository`
- `UserService`

Эти классы могут сохранять те же обязанности, которые были у них в руководстве `http-server`:

- репозиторий хранит и извлекает пользователей
- сервис координирует CRUD-поведение
- меняется только HTTP-точка входа

Такое разделение полезно в настоящих проектах. Если предметная логика живет в сервисном слое, а не внутри контроллера, становится намного проще заменить один транспортный стиль другим.

Поэтому в этом руководстве мы **не** переписываем все приложение. Мы заменяем только слой рукописного контроллера на сгенерированный.

## Делегат { #delegate }

Теперь создадим класс, который соединяет сгенерированный HTTP-код с существующим сервисным слоем.

Создайте:

`src/main/java/ru/tinkoff/kora/guide/openapi/httpserver/controller/UserApiDelegateImpl.java`

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/openapi/httpserver/controller/UserApiDelegateImpl.java"
    package ru.tinkoff.kora.guide.openapi.httpserver.controller;

    import java.time.Instant;
    import java.time.ZoneOffset;
    import ru.tinkoff.kora.guide.openapi.httpserver.user.model.ErrorResponseTO;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.openapi.httpserver.user.api.UsersApiDelegate;
    import ru.tinkoff.kora.guide.openapi.httpserver.user.api.UsersApiResponses;
    import ru.tinkoff.kora.guide.openapi.httpserver.user.model.UserRequestTO;
    import ru.tinkoff.kora.guide.openapi.httpserver.user.model.UserResponseTO;
    import ru.tinkoff.kora.guide.openapi.httpserver.dto.UserRequest;
    import ru.tinkoff.kora.guide.openapi.httpserver.dto.UserResponse;
    import ru.tinkoff.kora.guide.openapi.httpserver.service.UserService;

    @Component
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
            return new UsersApiResponses.DeleteUserApiResponse.DeleteUser204ApiResponse();
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
            int effectivePage = page == null ? 0 : page;
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
                    Instant.now().toString()
            );
        }

        private UserResponseTO toGenerated(UserResponse user) {
            return new UserResponseTO(
                    user.id(),
                    user.name(),
                    user.email(),
                    user.createdAt().atOffset(ZoneOffset.UTC)
            );
        }

        private ErrorResponseTO notFound(String userId) {
            return new ErrorResponseTO("User with id "" + userId + "" was not found");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/openapi/httpserver/controller/UserApiDelegateImpl.kt"
    package ru.tinkoff.kora.guide.openapi.httpserver.controller

    import java.time.Instant
    import java.time.ZoneOffset
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.openapi.httpserver.user.api.UsersApiDelegate
    import ru.tinkoff.kora.guide.openapi.httpserver.user.api.UsersApiResponses
    import ru.tinkoff.kora.guide.openapi.httpserver.user.model.ErrorResponseTO
    import ru.tinkoff.kora.guide.openapi.httpserver.user.model.UserRequestTO
    import ru.tinkoff.kora.guide.openapi.httpserver.user.model.UserResponseTO
    import ru.tinkoff.kora.guide.openapi.httpserver.dto.UserRequest
    import ru.tinkoff.kora.guide.openapi.httpserver.dto.UserResponse
    import ru.tinkoff.kora.guide.openapi.httpserver.service.UserService

    @Component
    class UserApiDelegateImpl(
        private val userService: UserService
    ) : UsersApiDelegate {

        override fun createUser(userRequest: UserRequestTO): UsersApiResponses.CreateUserApiResponse {
            val created = userService.createUser(UserRequest(userRequest.name(), userRequest.email()))
            return UsersApiResponses.CreateUserApiResponse.CreateUser201ApiResponse(toGenerated(created))
        }

        override fun deleteUser(userId: String): UsersApiResponses.DeleteUserApiResponse {
            if (userService.getUser(userId).isEmpty) {
                return UsersApiResponses.DeleteUserApiResponse.DeleteUser404ApiResponse(
                    notFound(userId)
                )
            }

            userService.deleteUser(userId)
            return UsersApiResponses.DeleteUserApiResponse.DeleteUser204ApiResponse()
        }

        override fun getUser(userId: String): UsersApiResponses.GetUserApiResponse {
            return userService.getUser(userId)
                .map<UsersApiResponses.GetUserApiResponse> { user ->
                    UsersApiResponses.GetUserApiResponse.GetUser200ApiResponse(toGenerated(user))
                }
                .orElseGet {
                    UsersApiResponses.GetUserApiResponse.GetUser404ApiResponse(
                        notFound(userId)
                    )
                }
        }

        override fun getUsers(page: Int?, size: Int?, sort: String?): UsersApiResponses.GetUsersApiResponse {
            val effectivePage = page ?: 0
            val effectiveSize = size ?: 10
            val effectiveSort = sort ?: "name"
            val users = userService.getUsers(effectivePage, effectiveSize, effectiveSort)
                .map(::toGenerated)
            return UsersApiResponses.GetUsersApiResponse.GetUsers200ApiResponse(users)
        }

        override fun updateUser(userId: String, userRequest: UserRequestTO): UsersApiResponses.UpdateUserApiResponse {
            if (userService.getUser(userId).isEmpty) {
                return UsersApiResponses.UpdateUserApiResponse.UpdateUser404ApiResponse(
                    notFound(userId)
                )
            }

            val updated = userService.updateUser(userId, UserRequest(userRequest.name(), userRequest.email()))
            return UsersApiResponses.UpdateUserApiResponse.UpdateUser200ApiResponse(
                toGenerated(updated),
                Instant.now().toString()
            )
        }

        private fun toGenerated(user: UserResponse): UserResponseTO {
            return UserResponseTO(
                user.id(),
                user.name(),
                user.email(),
                user.createdAt().atOffset(ZoneOffset.UTC)
            )
        }

        private fun notFound(userId: String): ErrorResponseTO {
            return ErrorResponseTO("User with id "$userId" was not found")
        }
    }
    ```

Этот шаг вводит главную абстракцию руководства.

В ручной версии `http-server` сам контроллер решал:

- как принять HTTP-ввод
- какой код состояния вернуть
- как построить ответ

В этой OpenAPI-версии такая ответственность переходит в реализацию делегата.

Сгенерированный контроллер обрабатывает низкоуровневый HTTP-транспорт. Ваш делегат отвечает за:

- вызов сервисного слоя
- выбор правильной сгенерированной обертки ответа
- сопоставление сгенерированных моделей OpenAPI и внутренних DTO приложения

Поскольку контракт OpenAPI теперь задает для ответов `404` и `500` общее тело `ErrorResponseTO`, делегат также может возвращать типизированные полезные нагрузки ошибок, а не только пустые варианты
состояния. Это делает сгенерированные обертки полезнее и для серверного, и для клиентского кода, потому что ответы с ошибками тоже становятся частью контракта.

Этот слой сопоставления не случаен. Это здоровое разделение:

- сгенерированные модели принадлежат контракту API
- внутренние DTO принадлежат вашему приложению

Если держать эту границу явной, приложение будет проще развивать позже.

## Конфигурация { #config }

Теперь мы публикуем контракт и интерактивную документацию из запущенного приложения.

Обновите `src/main/resources/application.conf`:

Полный справочник по конфигурации смотрите в [HTTP-сервер](../documentation/http-server.md), [OpenAPI Management](../documentation/openapi-management.md)
и [журналирование SLF4J](../documentation/logging-slf4j.md).

===! ":material-code-json: `Hocon`"

    ```javascript title="src/main/resources/application.conf"
    httpServer {
      publicApiHttpPort = 8080 //(1)!
      privateApiHttpPort = 8085 //(2)!
      telemetry.logging.enabled = true //(3)!
    }

    openapi {
      management {
        enabled = true //(4)!
        endpoint = "/openapi" //(5)!
        swaggerui {
          enabled = true //(6)!
          endpoint = "/swagger-ui" //(7)!
        }
      }
    }

    logging.level {
      "root" = "WARN" //(8)!
      "ru.tinkoff.kora" = "INFO" //(9)!
      "ru.tinkoff.kora.guide.openapi.httpserver" = "INFO" //(10)!
    }
    ```

    1. Публичный HTTP-порт по умолчанию, используемый конечными точками приложения.
    2. Приватный HTTP-порт по умолчанию, используемый пробами, метриками и конечными точками управления.
    3. Включает возможность для этого раздела конфигурации.
    4. Включает возможность для этого раздела конфигурации.
    5. Конечная точка экспортера телеметрии.
    6. Включает возможность для этого раздела конфигурации.
    7. Конечная точка экспортера телеметрии.
    8. Значение для `logging.level.root`.
    9. Значение для `logging.level.ru.tinkoff.kora`.
    10. Значение для `logging.level.ru.tinkoff.kora.guide.openapi.httpserver`.

=== ":simple-yaml: `YAML`"

    ```yaml title="src/main/resources/application.yaml"
    httpServer:
      publicApiHttpPort: 8080 #(1)!
      privateApiHttpPort: 8085 #(2)!
      telemetry:
        logging:
          enabled: true #(3)!
    openapi:
      management:
        enabled: true #(4)!
        endpoint: "/openapi" #(5)!
        swaggerui:
          enabled: true #(6)!
          endpoint: "/swagger-ui" #(7)!
    logging:
      level:
        root: "WARN" #(8)!
        "ru.tinkoff.kora": "INFO" #(9)!
        "ru.tinkoff.kora.guide.openapi.httpserver": "INFO" #(10)!
    ```

    1. Публичный HTTP-порт по умолчанию, используемый конечными точками приложения.
    2. Приватный HTTP-порт по умолчанию, используемый пробами, метриками и конечными точками управления.
    3. Включает возможность для этого раздела конфигурации.
    4. Включает возможность для этого раздела конфигурации.
    5. Конечная точка экспортера телеметрии.
    6. Включает возможность для этого раздела конфигурации.
    7. Конечная точка экспортера телеметрии.
    8. Значение для `logging.level.root`.
    9. Значение для `logging.level.ru.tinkoff.kora`.
    10. Значение для `logging.level.ru.tinkoff.kora.guide.openapi.httpserver`.

Это дает две очень практичные конечные точки:

- `/openapi` возвращает документ OpenAPI
- `/swagger-ui` дает интерактивный интерфейс для изучения и проверки API

Это одно из главных преимуществ контрактной разработки. Документация не является тем, что вы пишете позже. Она является частью той же сборки, которая генерирует серверный слой.

## Проверка приложения { #check-app }

Соберите модуль:

```bash
./gradlew :guides-apps:guide-openapi-http-server-app:clean :guides-apps:guide-openapi-http-server-app:classes
```

Запустите приложение:

```bash
./gradlew run
```

Затем проверьте API:

```bash
curl http://localhost:8080/users
```

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com"}'
```

```bash
curl http://localhost:8080/openapi
```

Откройте в браузере:

```text
http://localhost:8080/swagger-ui
```

На этом этапе приложение ведет себя как знакомый CRUD-сервис `http-server`, но HTTP-слой теперь управляется контрактом OpenAPI.

## Тест делегата { #delegate-test }

Приложение руководства также включает тест, который проверяет CRUD-поведение через сгенерированный делегат.

Запустите:

```bash
./gradlew test
```

Этот тест проверяет:

- создание
- получение по идентификатору
- список
- обновление
- удаление
- `404` после удаления

Это полезная контрольная точка, потому что она доказывает, что сгенерированный слой API и ваша реализация делегата правильно связаны.

## Лучшие практики { #best-practices }

- Держите контракт OpenAPI близко к реальному поведению приложения. Контракт должен описывать действительность, а не будущие идеи.
- Держите сгенерированный код только как результат сборки. Не редактируйте файлы внутри `build/generated/user-http-server`.
- Держите бизнес-логику в сервисах, а не в сгенерированных классах.
- Используйте делегаты как транспортную границу между сгенерированными типами API и внутренними моделями приложения.
- Регенерируйте серверный код как часть обычных сборок, чтобы контракт и скомпилированное приложение не расходились.

## Итоги { #summary }

Вы взяли CRUD-сервер пользователей из руководства [HTTP-сервер](http-server.md) и пересобрали его HTTP-слой в контрактном стиле:

- API теперь описан в `user-http-server.yaml`
- Kora генерирует серверный слой в `build/generated/user-http-server`
- приложение реализует `UsersApiDelegate`
- знакомые слои сервиса и репозитория остаются на месте
- приложение открывает `/openapi` и `/swagger-ui`

Поведение остается знакомым, но теперь транспортным слоем управляет контракт, а не рукописный контроллер.

## Ключевые понятия { #key-concepts }

- контрактная разработка начинается с общей спецификации API
- Kora может генерировать серверный код из OpenAPI
- сгенерированные контроллеры и делегаты разделяют транспортную связку и прикладную логику
- делегаты являются хорошим местом для сопоставления сгенерированных моделей контракта и внутренних DTO
- добавление новых кодов состояния, таких как `500`, в OpenAPI меняет и сгенерированные обертки ответов
- Swagger UI и OpenAPI становятся естественной частью приложения, когда контракт встроен в проект

## Устранение неполадок { #troubleshooting }

**Генерация кода не запускается:**

Проверьте, что:

- подключен `org.openapi.generator`
- импортирован `GenerateTask`
- настроено `compileJava.dependsOn openApiGenerateUsersHttpServer`

**Приложение не находит сгенерированные классы:**

Проверьте, что сгенерированный каталог исходников добавлен в `sourceSets.main`:

- `build/generated/user-http-server`

Также убедитесь, что настройки пакетов совпадают с вашими импортами:

- `ru.tinkoff.kora.guide.openapi.httpserver.user.api`
- `ru.tinkoff.kora.guide.openapi.httpserver.user.model`

**Swagger UI недоступен:**

Убедитесь, что:

- `OpenApiManagementModule` включен в `Application`
- `openapi.management.enabled = true`
- `swaggerui.enabled = true`

**Делегат не обнаруживается Kora:**

Убедитесь, что:

- делегат аннотирован `@Component`
- он реализует сгенерированный `UsersApiDelegate`
- он импортирует сгенерированный пакет, который вы настроили в `build.gradle`

**Ручной контроллер конфликтует со сгенерированным сервером:**

В этом варианте приложения рукописный контроллер пользователей не должен оставаться рядом со сгенерированным серверным контроллером. После перехода на сгенерированный по OpenAPI транспортный слой
делегат становится главной точкой реализации HTTP-поведения.

**Вариант обертки ответа отсутствует:**

Сгенерированные варианты ответов существуют только для кодов состояния, явно перечисленных в контракте OpenAPI.

Поэтому, если вы ожидаете сгенерированную абстракцию `500`, такую как `GetUser500ApiResponse`, убедитесь, что `500` присутствует в разделе `responses` этой операции в `user-http-server.yaml`.

## Что дальше? { #whats-next }

- [HTTP-клиент](http-client.md), если вы еще не создавали клиентское приложение.
- [OpenAPI HTTP-клиент](openapi-http-client.md) после HTTP-клиента, чтобы сгенерировать клиент из контракта того же типа.
- [Продвинутый HTTP-сервер](http-server-advanced.md) перед [Продвинутый OpenAPI HTTP-сервер](openapi-http-server-advanced.md), потому что продвинутое руководство по OpenAPI объединяет обе ветки.
- [Валидация](validation.md), чтобы сравнить рукописную проверку данных с проверкой на основе спецификации.

## Помощь { #help }

Если вы застряли:

- сравните с [Kora Java OpenAPI HTTP Server App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-openapi-http-server-app) и [Kora Kotlin OpenAPI HTTP Server App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-openapi-http-server-app)
- сравните с [HTTP-сервер](http-server.md), чтобы увидеть, что заменил сгенерированный контроллер
- проверьте [документацию по генерации OpenAPI-кода](../documentation/openapi-codegen.md)
- проверьте [документацию OpenAPI Management](../documentation/openapi-management.md)
