---
search:
  exclude: true
title: Продвинутое руководство по контрактному HTTP-серверу
summary: Continue the OpenAPI HTTP Server guide by adding a second generated contract for forms, multipart, response mapping, generated controller interceptors, API-key authorization, and selective server validation
tags: openapi, http-server, advanced, forms, multipart, auth, validation
---

# Продвинутое руководство по контрактному HTTP-серверу { #advanced-contract-first-http }

Это руководство знакомит с продвинутыми паттернами контрактного HTTP-сервера в Kora и OpenAPI. В нем разбирается, как несколько спецификаций OpenAPI могут сосуществовать в одном приложении, как
сгенерированные делегаты обрабатывают формы, multipart-загрузки и типизированные варианты ответов, а также как общая обработка ошибок и авторизация по ключу API встраиваются вокруг сгенерированного
транспортного кода. Вы также увидите, как новые контракты могут развиваться независимо, пока рукописные сервисы остаются местом для прикладного поведения.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java OpenAPI HTTP Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-openapi-http-server-advanced-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin OpenAPI HTTP Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-openapi-http-server-advanced-app).

## Что вы создадите { #youll-build }

Вы расширите приложение OpenAPI HTTP-сервер с помощью:

- того же CRUD-контракта пользователей из [openapi-http-server.md](openapi-http-server.md)
- второго OpenAPI-контракта с именем `data-http-server.yaml`
- сгенерированных конечных точек для form, multipart и маршрутов сопоставления ответов
- перехватчика сгенерированного контроллера для единообразных JSON-ответов об ошибках
- простой авторизации по ключу API для конечных точек данных
- серверной проверки данных, сгенерированной только для одного параметра пути
- общей публикации `/openapi` и `/swagger-ui` для обоих контрактов

## Что вам понадобится { #youll-need }

- JDK 17 или новее
- Gradle 7+
- текстовый редактор или среда разработки
- пройденное руководство [Контрактный HTTP-сервер с OpenAPI](openapi-http-server.md)
- пройденное руководство [Продвинутый HTTP-сервер Guide](http-server-advanced.md)

## Требования { #prerequisites }

!!! note "Обязательно: пройдите руководства OpenAPI HTTP-сервер и продвинутый HTTP-сервер"

    Это руководство предполагает, что вы прошли **[Контрактный HTTP-сервер с OpenAPI](openapi-http-server.md)** и **[Продвинутый HTTP-сервер](http-server-advanced.md)**, а также уже понимаете контрактный CRUD-поток пользователей и продвинутые HTTP-концепции, используемые маршрутами данных.

    Если вы еще не прошли эти руководства, сначала сделайте это, потому что это руководство объединяет сгенерированные OpenAPI-делегаты с продвинутыми HTTP-возможностями: формами, multipart, общими ошибками и безопасностью.

Вместо этого мы сосредоточимся на следующем шаге: как применить эти продвинутые HTTP-идеи в сгенерированном контрактном HTTP-сервере.

## Обзор { #overview }

В этом руководстве мы движемся в очень осознанном порядке:

1. оставляем сгенерированный API пользователей неизменным
2. добавляем второй OpenAPI-контракт только для продвинутых маршрутов данных
3. настраиваем вторую задачу генерации Kora только для этого контракта
4. изучаем новые сгенерированные абстракции
5. реализуем `DataApiDelegate`
6. включаем проверку данных только для `mappingByCode(int code)`
7. подключаем перехватчик сгенерированного контроллера для общего сопоставления ошибок
8. добавляем авторизацию по ключу API через контракт безопасности OpenAPI
9. публикуем оба контракта вместе через OpenAPI management

Ключевая идея проектирования — разделение:

- API пользователей остается стабильным контрактом из предыдущего руководства
- продвинутый API данных развивается в собственном контракте

Так пример проще объяснять, и он гораздо ближе к тому, как часто растут настоящие сервисы.

### Разные контракты { #different-contracts }

На первый взгляд может показаться, что проще держать все в одном огромном файле OpenAPI.

Иногда это правильно. Но иногда отдельный контракт здоровее:

- разные группы конечных точек развиваются с разной скоростью
- одной группе могут понадобиться дополнительные возможности генерации
- у одной группы могут быть другие требования к безопасности или проверке данных
- одна группа может существовать в основном для демонстрации транспортных приемов, а не бизнес-CRUD

Именно такая ситуация у нас здесь.

CRUD-контракт пользователей уже хорош. Мы не хотим повторно его объяснять или рисковать случайно изменить его, добавляя продвинутые HTTP-примеры.

Поэтому мы выделяем продвинутые маршруты в отдельный контракт:

- `user-http-server.yaml` остается источником истины для CRUD пользователей
- `data-http-server.yaml` становится источником истины для форм, multipart, общей обработки ошибок, авторизации по ключу API и одного сфокусированного примера проверки данных

Именно поэтому только задача генерации **data** получает:

- `interceptors`
- `enableServerValidation`

Генератор пользователей остается ровно таким, каким был в предыдущем руководстве.

## Старый контракт OpenAPI { #old-contract }

Первый важный шаг на самом деле является не-шагом: **не** переписывайте сторону пользователей.

Переиспользуйте ту же задачу генерации и тот же контракт из [openapi-http-server.md](openapi-http-server.md).

Эта деталь очень важна для истории руководства.

Мы **не** заменяем предыдущее руководство. Мы расширяем его.

Поэтому части на стороне пользователей остаются прежними:

- `user-http-server.yaml`
- `UsersApiDelegate`
- `UserApiDelegateImpl`
- знакомый поток `UserService` и репозитория

Вся новая работа в этом руководстве относится к продвинутым конечным точкам данных.

## Новый контракт OpenAPI { #new-contract }

Теперь перенесем идеи продвинутого `DataController` из [http-server-advanced.md](http-server-advanced.md) в собственный OpenAPI-контракт.

Создайте:

`src/main/resources/openapi/data-http-server.yaml`

??? example "OpenAPI-контракт"

    ```yaml title="src/main/resources/openapi/data-http-server.yaml"
    openapi: 3.0.3
    info:
        title: Advanced Data API
        description: Form and multipart endpoints generated from a dedicated OpenAPI contract
        version: 1.0.0
    tags:
        -   name: data
            description: Form and multipart operations
    security:
        -   apiKeyAuth: [ ]
    paths:
        /data/form:
            post:
                tags:
                    - data
                operationId: processForm
                summary: Process a URL-encoded form
                requestBody:
                    required: true
                    content:
                        application/x-www-form-urlencoded:
                            schema:
                                $ref: '#/components/schemas/FormRequestTO'
                responses:
                    '200':
                        description: Form processed
                        content:
                            text/plain:
                                schema:
                                    type: string
                    '400':
                        description: Invalid request
                        content:
                            application/json:
                                schema:
                                    $ref: '#/components/schemas/ErrorResponseTO'
                    '403':
                        description: Invalid API key
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
        /data/upload:
            post:
                tags:
                    - data
                operationId: processUpload
                summary: Process a multipart upload
                requestBody:
                    required: true
                    content:
                        multipart/form-data:
                            schema:
                                $ref: '#/components/schemas/UploadRequestTO'
                responses:
                    '200':
                        description: Upload processed
                        content:
                            application/json:
                                schema:
                                    $ref: '#/components/schemas/UploadResponseTO'
                    '400':
                        description: Invalid request
                        content:
                            application/json:
                                schema:
                                    $ref: '#/components/schemas/ErrorResponseTO'
                    '403':
                        description: Invalid API key
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
        /data/mapping-by-code/{code}:
            get:
                tags:
                    - data
                operationId: mappingByCode
                summary: Return different HTTP outcomes by code
                parameters:
                    -   name: code
                        in: path
                        required: true
                        schema:
                            type: integer
                            minimum: 200
                            maximum: 599
                responses:
                    '200':
                        description: Success payload
                        content:
                            application/json:
                                schema:
                                    $ref: '#/components/schemas/PayloadTO'
                    '400':
                        description: Invalid request
                        content:
                            application/json:
                                schema:
                                    $ref: '#/components/schemas/ErrorResponseTO'
                    '403':
                        description: Invalid API key
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
                    details:
                        type: array
                        nullable: true
                        items:
                            type: string
            FormRequestTO:
                type: object
                required:
                    - name
                properties:
                    name:
                        type: string
            UploadRequestTO:
                type: object
                required:
                    - description
                    - file
                properties:
                    description:
                        type: string
                    file:
                        type: string
                        format: binary
            UploadResponseTO:
                type: object
                required:
                    - fileCount
                    - fileNames
                properties:
                    fileCount:
                        type: integer
                    fileNames:
                        type: array
                        items:
                            type: string
            PayloadTO:
                type: object
                required:
                    - message
                properties:
                    message:
                        type: string
    ```

Этот контракт вводит сразу несколько новых идей, поэтому его стоит читать медленно.

Что нового по сравнению с базовым руководством по OpenAPI-серверу:

- `application/x-www-form-urlencoded`
- `multipart/form-data`
- небольшой JSON-маршрут, который возвращает разные ответы по коду
- явные тела ошибок `400`, `403` и `500`
- один параметр пути с явным числовым диапазоном

Теперь контракт описывает не только полезные нагрузки счастливого пути, но и:

- какое структурированное тело ошибки должны ожидать клиенты, включая необязательные детали проверки данных
- где сгенерированный сервер должен применить проверку данных

Это важное преимущество контрактного проектирования. Больше поведения становится явным еще до того, как мы напишем делегат.

## Генерация по OpenAPI { #openapi-generation }

Теперь настройте вторую задачу генерации.

Это самый важный шаг сборки во всем руководстве, потому что именно здесь мы намеренно обрабатываем API данных иначе, чем API пользователей.

===! ":fontawesome-brands-java: `Java`"

    ```groovy title="build.gradle"
    def openApiGenerateDataHttpServer = tasks.register("openApiGenerateDataHttpServer", GenerateTask) {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/data-http-server.yaml"
        outputDir = "$buildDir/generated/data-http-server"
        def corePackage = "ru.tinkoff.kora.guide.openapi.httpserver.data"
        apiPackage = "${corePackage}.api"
        modelPackage = "${corePackage}.model"
        invokerPackage = "${corePackage}.invoker"
        configOptions = [
                mode: "java-server",
        ]
    }

    sourceSets.main {
        java.srcDirs += openApiGenerateUsersHttpServer.get().outputDir
        java.srcDirs += openApiGenerateDataHttpServer.get().outputDir
    }

    compileJava.dependsOn openApiGenerateUsersHttpServer
    compileJava.dependsOn openApiGenerateDataHttpServer
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="build.gradle.kts"
    val openApiGenerateDataHttpServer = tasks.register<GenerateTask>("openApiGenerateDataHttpServer") {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/data-http-server.yaml"
        outputDir = "$buildDir/generated/data-http-server"
        val corePackage = "ru.tinkoff.kora.guide.openapi.httpserver.data"
        apiPackage = "$corePackage.api"
        modelPackage = "$corePackage.model"
        invokerPackage = "$corePackage.invoker"
        configOptions = mapOf(
            "mode" to "java-server"
        )
    }

    sourceSets.main {
        java.srcDir(openApiGenerateUsersHttpServer.get().outputDir)
        java.srcDir(openApiGenerateDataHttpServer.get().outputDir)
    }

    tasks.compileJava {
        dependsOn(openApiGenerateUsersHttpServer)
        dependsOn(openApiGenerateDataHttpServer)
    }
    ```

Почему такое разделение так полезно:

- `openApiGenerateUsersHttpServer` остается простой и неизменной
- `openApiGenerateDataHttpServer` получает продвинутое поведение

И на этом раннем этапе мы намеренно оставляем конфигурацию генератора минимальной.

Сейчас мы намеренно **не** настраиваем:

- серверную проверку данных
- пользовательские перехватчики сгенерированного контроллера

Сначала реализуем делегат, затем включим проверку данных и только после этого введем `DataApiExceptionHandler`. Так руководство остается согласованным с порядком, в котором эти классы действительно
появляются.

Именно такое разделение возможностей оправдывает второй контракт.

## Сгенерированные классы { #generated-classes }

Запустите:

```bash
./gradlew clean classes
```

Теперь изучите сгенерированные файлы:

===! ":fontawesome-brands-java: `Java`"

    - `build/generated/data-http-server/ru/tinkoff/kora/guide/openapi/httpserver/data/api/DataApiDelegate.java`
    - `build/generated/data-http-server/ru/tinkoff/kora/guide/openapi/httpserver/data/api/DataApiController.java`
    - `build/generated/data-http-server/ru/tinkoff/kora/guide/openapi/httpserver/data/api/DataApiResponses.java`
    - `build/generated/data-http-server/ru/tinkoff/kora/guide/openapi/httpserver/data/api/ApiSecurity.java`
    - `build/generated/data-http-server/ru/tinkoff/kora/guide/openapi/httpserver/data/model/UploadResponseTO.java`
    - `build/generated/data-http-server/ru/tinkoff/kora/guide/openapi/httpserver/data/model/PayloadTO.java`
    - `build/generated/data-http-server/ru/tinkoff/kora/guide/openapi/httpserver/data/model/ErrorResponseTO.java`

=== ":simple-kotlin: `Kotlin`"

    - `build/generated/data-http-server/ru/tinkoff/kora/guide/openapi/httpserver/data/api/DataApiDelegate.kt`
    - `build/generated/data-http-server/ru/tinkoff/kora/guide/openapi/httpserver/data/api/DataApiController.kt`
    - `build/generated/data-http-server/ru/tinkoff/kora/guide/openapi/httpserver/data/api/DataApiResponses.kt`
    - `build/generated/data-http-server/ru/tinkoff/kora/guide/openapi/httpserver/data/api/ApiSecurity.kt`
    - `build/generated/data-http-server/ru/tinkoff/kora/guide/openapi/httpserver/data/model/UploadResponseTO.kt`
    - `build/generated/data-http-server/ru/tinkoff/kora/guide/openapi/httpserver/data/model/PayloadTO.kt`
    - `build/generated/data-http-server/ru/tinkoff/kora/guide/openapi/httpserver/data/model/ErrorResponseTO.kt`

Самые интересные сгенерированные абстракции здесь:

- `DataApiDelegate`
- `DataApiController`
- `DataApiResponses`
- `ApiSecurity`

`DataApiDelegate`:

Это контракт, который вы реализуете.

Он играет ровно ту же архитектурную роль, что и `UsersApiDelegate`, но для новых продвинутых конечных точек.

`DataApiController`:

Это сгенерированный транспортный слой.

Поскольку контракт включает:

- `form-url-encoded` ввод
- multipart ввод
- явное моделирование транспортных статусов

сгенерированный контроллер теперь делает больше, чем в более простом CRUD-случае.

`DataApiResponses`:

Эти обертки моделируют допустимые HTTP-исходы из спецификации:

- `200`
- `400`
- `403`
- `500`

Это означает, что обработка ошибок теперь является частью транспортного контракта, а не тем, что мы импровизируем в коде.

Для `mappingByCode` сгенерированное семейство ответов также дает чистое место, где можно разделить:

- успешную JSON-полезную нагрузку
- JSON-тело ошибки

`ApiSecurity`:

Он генерируется из раздела OpenAPI `securitySchemes`.

Это мост между контрактом безопасности OpenAPI и извлекателем principal, который вы зарегистрируете в `Application`.

Это одна из самых ценных идей в руководстве:

- безопасность объявлена в контракте
- генератор создает маркерные типы
- ваше приложение подключает настоящую проверку времени выполнения

## Делегат { #delegate }

Теперь соедините сгенерированный транспортный слой данных с прикладной логикой.

Создайте:

`src/main/java/ru/tinkoff/kora/guide/openapi/httpserver/advanced/controller/DataApiDelegateImpl.java`

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/openapi/httpserver/advanced/controller/DataApiDelegateImpl.java"
    package ru.tinkoff.kora.guide.openapi.httpserver.advanced.controller;

    import java.util.List;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.openapi.httpserver.data.api.DataApiController;
    import ru.tinkoff.kora.guide.openapi.httpserver.data.api.DataApiDelegate;
    import ru.tinkoff.kora.guide.openapi.httpserver.data.api.DataApiResponses;
    import ru.tinkoff.kora.guide.openapi.httpserver.data.model.PayloadTO;
    import ru.tinkoff.kora.guide.openapi.httpserver.data.model.UploadResponseTO;
    import ru.tinkoff.kora.http.server.common.HttpServerResponseException;

    @Component
    public final class DataApiDelegateImpl implements DataApiDelegate {

        @Override
        public DataApiResponses.ProcessFormApiResponse processForm(DataApiController.ProcessFormFormParam form) {
            return new DataApiResponses.ProcessFormApiResponse.ProcessForm200ApiResponse("Hello World, " + form.name());
        }

        @Override
        public DataApiResponses.ProcessUploadApiResponse processUpload(DataApiController.ProcessUploadFormParam form) {
            var response = new UploadResponseTO(
                    1,
                    List.of(form.file().name())
            );
            return new DataApiResponses.ProcessUploadApiResponse.ProcessUpload200ApiResponse(response);
        }

        @Override
        public DataApiResponses.MappingByCodeApiResponse mappingByCode(int code) {
            if (code == 200) {
                return new DataApiResponses.MappingByCodeApiResponse.MappingByCode200ApiResponse(
                        new PayloadTO("Hello from response mapper")
                );
            }
            throw HttpServerResponseException.of(code, "Request failed with code " + code);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/openapi/httpserver/advanced/controller/DataApiDelegateImpl.kt"
    package ru.tinkoff.kora.guide.openapi.httpserver.advanced.controller

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.openapi.httpserver.data.api.DataApiController
    import ru.tinkoff.kora.guide.openapi.httpserver.data.api.DataApiDelegate
    import ru.tinkoff.kora.guide.openapi.httpserver.data.api.DataApiResponses
    import ru.tinkoff.kora.guide.openapi.httpserver.data.model.PayloadTO
    import ru.tinkoff.kora.guide.openapi.httpserver.data.model.UploadResponseTO
    import ru.tinkoff.kora.http.server.common.HttpServerResponseException

    @Component
    class DataApiDelegateImpl : DataApiDelegate {

        override fun processForm(form: DataApiController.ProcessFormFormParam): DataApiResponses.ProcessFormApiResponse {
            return DataApiResponses.ProcessFormApiResponse.ProcessForm200ApiResponse("Hello World, ${form.name()}")
        }

        override fun processUpload(form: DataApiController.ProcessUploadFormParam): DataApiResponses.ProcessUploadApiResponse {
            val response = UploadResponseTO(1, listOf(form.file().name()))
            return DataApiResponses.ProcessUploadApiResponse.ProcessUpload200ApiResponse(response)
        }

        override fun mappingByCode(code: Int): DataApiResponses.MappingByCodeApiResponse {
            if (code == 200) {
                return DataApiResponses.MappingByCodeApiResponse.MappingByCode200ApiResponse(
                    PayloadTO("Hello from response mapper")
                )
            }
            throw HttpServerResponseException.of(code, "Request failed with code $code")
        }
    }
    ```

Здесь приятно заметить две вещи.

Во-первых, делегат остается очень небольшим.

Потому что сгенерированный слой уже обработал многое:

- декодирование запроса
- транспортную типизацию
- интеграцию контракта безопасности
- точки подключения проверки данных

Во-вторых, логика намеренно повторяет ручной `DataController` из [http-server-advanced.md](http-server-advanced.md).

Это важно для согласованности обучения. Руководство не придумывает другое поведение. Оно показывает, как то же поведение выглядит, когда транспортный слой сгенерирован из OpenAPI, а не написан
вручную.

Новый маршрут `mappingByCode()` особенно полезен, потому что дает одну компактную JSON-конечную точку для:

- сгенерированных оберток ответов
- сгенерированного сопоставления ошибок
- одного сфокусированного примера проверки данных

## Серверная валидация { #server-validation }

Полные правила серверной OpenAPI-валидации и выбора операций описаны в разделе [валидации OpenAPI Codegen](../documentation/openapi-codegen.md#validation).

Теперь обновите задачу генерации данных и явно включите проверку:

===! ":fontawesome-brands-java: `Java`"

    ```groovy title="build.gradle"
    def openApiGenerateDataHttpServer = tasks.register("openApiGenerateDataHttpServer", GenerateTask) {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/data-http-server.yaml"
        outputDir = "$buildDir/generated/data-http-server"
        def corePackage = "ru.tinkoff.kora.guide.openapi.httpserver.data"
        apiPackage = "${corePackage}.api"
        modelPackage = "${corePackage}.model"
        invokerPackage = "${corePackage}.invoker"
        configOptions = [
                mode                  : "java-server",
                enableServerValidation: "true",
        ]
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="build.gradle.kts"
    val openApiGenerateDataHttpServer = tasks.register<GenerateTask>("openApiGenerateDataHttpServer") {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/data-http-server.yaml"
        outputDir = "$buildDir/generated/data-http-server"
        val corePackage = "ru.tinkoff.kora.guide.openapi.httpserver.data"
        apiPackage = "$corePackage.api"
        modelPackage = "$corePackage.model"
        invokerPackage = "$corePackage.invoker"
        configOptions = mapOf(
            "mode" to "java-server",
            "enableServerValidation" to "true"
        )
    }
    ```

Поскольку `enableServerValidation` включен только на `openApiGenerateDataHttpServer`, поведение проверки данных меняется только для сгенерированных конечных точек данных.

В этом руководстве мы намеренно держим поверхность проверки данных очень маленькой.

Ограничен только один параметр:

- `code` в `/data/mapping-by-code/{code}`

Его допустимый диапазон:

- минимум `200`
- максимум `599`

Это полезно по двум причинам.

Во-первых, это ясно демонстрирует проверку данных по спецификации на одном сфокусированном примере.

Во-вторых, это не превращает весь продвинутый контракт в руководство по проверке данных. Шаги с form и multipart остаются сфокусированными на транспортных форматах, а шаг проверки данных — на одном
параметре пути.

Чтобы такие ошибки проверки данных возвращали тот же JSON-контракт, что и остальной API данных, зарегистрируйте пользовательский `ViolationExceptionHttpServerResponseMapper`.

`ValidationModule` уже предоставляет `ValidationHttpServerInterceptor`, и сгенерированный сервер использует его автоматически, потому что `enableServerValidation` включен. Единственная наша настройка
здесь — преобразователь, который превращает `ViolationException` в `ErrorResponseTO`.

Именно поэтому у `ErrorResponseTO` теперь два слоя:

- `message` для верхнеуровневого описания проблемы
- `details` для сообщений проверки данных на уровне поля или параметра, когда они есть

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/openapi/httpserver/advanced/Application.java"
    package ru.tinkoff.kora.guide.openapi.httpserver.advanced;

    import ru.tinkoff.kora.guide.openapi.httpserver.data.model.ErrorResponseTO;
    import ru.tinkoff.kora.http.common.body.HttpBody;
    import ru.tinkoff.kora.http.server.common.HttpServerResponse;
    import ru.tinkoff.kora.json.common.JsonWriter;
    import ru.tinkoff.kora.validation.module.http.server.ViolationExceptionHttpServerResponseMapper;

    default ViolationExceptionHttpServerResponseMapper customViolationExceptionHttpServerResponseMapper(
            JsonWriter<ErrorResponseTO> errorResponseJsonWriter) {
        return (request, exception) -> {
            var details = exception.getViolations().stream()
                    .map(v -> "Path " + v.path() + " violated: " + v.message())
                    .toList();

            var response = new ErrorResponseTO(
                    "Encountered '%s' validation violations".formatted(exception.getViolations().size()),
                    details
            );
            return HttpServerResponse.of(
                    400,
                    HttpBody.json(errorResponseJsonWriter.toByteArrayUnchecked(response)));
        };
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/openapi/httpserver/advanced/Application.kt"
    import ru.tinkoff.kora.guide.openapi.httpserver.data.model.ErrorResponseTO
    import ru.tinkoff.kora.http.common.body.HttpBody
    import ru.tinkoff.kora.http.server.common.HttpServerResponse
    import ru.tinkoff.kora.json.common.JsonWriter
    import ru.tinkoff.kora.validation.module.http.server.ViolationExceptionHttpServerResponseMapper

    fun customViolationExceptionHttpServerResponseMapper(
        errorResponseJsonWriter: JsonWriter<ErrorResponseTO>
    ): ViolationExceptionHttpServerResponseMapper {
        return ViolationExceptionHttpServerResponseMapper { _, exception ->
            val details = exception.violations
                .map { violation -> "Path ${violation.path()} violated: ${violation.message()}" }

            val response = ErrorResponseTO(
                "Encountered '${exception.violations.size}' validation violations",
                details
            )
            HttpServerResponse.of(
                400,
                HttpBody.json(errorResponseJsonWriter.toByteArrayUnchecked(response))
            )
        }
    }
    ```

Это еще один пример того, почему разделение контрактов было хорошим проектным решением.

Одно и то же `Application` может размещать:

- один сгенерированный сервер без проверки данных по спецификации
- другой сгенерированный сервер с проверкой данных по спецификации

А поскольку ограничение живет в схеме OpenAPI, сгенерированный транспортный слой может отклонить значения вне диапазона до того, как ваш делегат решит, как отвечать.

## Перехватчик ошибок { #error-interceptor }

Перехватчики сгенерированных серверных контроллеров подробнее описаны в разделе [OpenAPI Codegen: перехватчики сервера](../documentation/openapi-codegen.md#interceptors-2).

Теперь, когда ошибки проверки данных уже превращаются в структурированный JSON, можно добавить еще один слой для **других** видов транспортных ошибок, которые мы хотим нормализовать.

В ручном продвинутом руководстве по серверу мы использовали глобальный `ExceptionHandler`.

Здесь мы намеренно делаем немного иначе.

Для сгенерированного контроллера **data** мы подключаем перехватчик, привязанный к конкретному контракту, через конфигурацию генератора OpenAPI.

Создайте:

`src/main/java/ru/tinkoff/kora/guide/openapi/httpserver/advanced/controller/DataApiExceptionHandler.java`

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/openapi/httpserver/advanced/controller/DataApiExceptionHandler.java"
    package ru.tinkoff.kora.guide.openapi.httpserver.advanced.controller;

    import java.util.concurrent.CompletionException;
    import java.util.concurrent.CompletionStage;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.Context;
    import ru.tinkoff.kora.guide.openapi.httpserver.data.model.ErrorResponseTO;
    import ru.tinkoff.kora.http.common.body.HttpBody;
    import ru.tinkoff.kora.http.server.common.HttpServerInterceptor;
    import ru.tinkoff.kora.http.server.common.HttpServerRequest;
    import ru.tinkoff.kora.http.server.common.HttpServerResponse;
    import ru.tinkoff.kora.http.server.common.HttpServerResponseException;
    import ru.tinkoff.kora.json.common.JsonWriter;
    import ru.tinkoff.kora.validation.common.ViolationException;

    @Component
    public final class DataApiExceptionHandler implements HttpServerInterceptor {

        private final JsonWriter<ErrorResponseTO> errorJsonWriter;

        public DataApiExceptionHandler(JsonWriter<ErrorResponseTO> errorJsonWriter) {
            this.errorJsonWriter = errorJsonWriter;
        }

        @Override
        public CompletionStage<HttpServerResponse> intercept(Context context, HttpServerRequest request, InterceptChain chain)
                throws Exception {
            return chain.process(context, request).exceptionally(throwable -> {
                var cause = unwrap(throwable);
                if (cause instanceof ViolationException violationException) {
                    throw new CompletionException(violationException);
                }
                if (cause instanceof HttpServerResponseException responseException) {
                    return jsonResponse(responseException.code(), responseException.getMessage());
                }
                if (cause instanceof IllegalArgumentException) {
                    return jsonResponse(400, "Invalid request parameters");
                }
                if (cause instanceof SecurityException) {
                    return jsonResponse(403, cause.getMessage() != null ? cause.getMessage() : "Access denied");
                }
                return jsonResponse(500, "An unexpected error occurred");
            });
        }

        private HttpServerResponse jsonResponse(int statusCode, String message) {
            return HttpServerResponse.of(
                statusCode,
                HttpBody.json(this.errorJsonWriter.toByteArrayUnchecked(new ErrorResponseTO(message, null)))
            );
        }

        private static Throwable unwrap(Throwable throwable) {
            var current = throwable;
            while (current instanceof CompletionException && current.getCause() != null) {
                current = current.getCause();
            }
            return current;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/openapi/httpserver/advanced/controller/DataApiExceptionHandler.kt"
    package ru.tinkoff.kora.guide.openapi.httpserver.advanced.controller

    import java.util.concurrent.CompletionException
    import java.util.concurrent.CompletionStage
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.Context
    import ru.tinkoff.kora.guide.openapi.httpserver.data.model.ErrorResponseTO
    import ru.tinkoff.kora.http.common.body.HttpBody
    import ru.tinkoff.kora.http.server.common.HttpServerInterceptor
    import ru.tinkoff.kora.http.server.common.HttpServerRequest
    import ru.tinkoff.kora.http.server.common.HttpServerResponse
    import ru.tinkoff.kora.http.server.common.HttpServerResponseException
    import ru.tinkoff.kora.json.common.JsonWriter
    import ru.tinkoff.kora.validation.common.ViolationException

    @Component
    class DataApiExceptionHandler(
        private val errorJsonWriter: JsonWriter<ErrorResponseTO>
    ) : HttpServerInterceptor {

        override fun intercept(
            context: Context,
            request: HttpServerRequest,
            chain: HttpServerInterceptor.InterceptChain
        ): CompletionStage<HttpServerResponse> {
            return chain.process(context, request).exceptionally { throwable ->
                val cause = unwrap(throwable)
                when (cause) {
                    is ViolationException -> throw CompletionException(cause)
                    is HttpServerResponseException -> jsonResponse(cause.code(), cause.message ?: "HTTP error")
                    is IllegalArgumentException -> jsonResponse(400, "Invalid request parameters")
                    is SecurityException -> jsonResponse(403, cause.message ?: "Access denied")
                    else -> jsonResponse(500, "An unexpected error occurred")
                }
            }
        }

        private fun jsonResponse(statusCode: Int, message: String): HttpServerResponse {
            return HttpServerResponse.of(
                statusCode,
                HttpBody.json(errorJsonWriter.toByteArrayUnchecked(ErrorResponseTO(message, null)))
            )
        }

        private fun unwrap(throwable: Throwable): Throwable {
            var current = throwable
            while (current is CompletionException && current.cause != null) {
                current = current.cause!!
            }
            return current
        }
    }
    ```

Ключевое отличие от ручного руководства — область действия:

- в [http-server-advanced.md](http-server-advanced.md) перехватчик был глобальным
- здесь он подключен только к **сгенерированному API данных**

Это тонкий, но сильный паттерн.

Сгенерированные транспорты не обязаны все разделять одно и то же сквозное поведение. Вы можете применять разные стратегии перехватчиков к разным сгенерированным контрактам.

Важная деталь — ветка `ViolationException`.

Мы намеренно **не** преобразуем ошибки проверки данных здесь, потому что уже решили: ошибки проверки данных принадлежат `customViolationExceptionHttpServerResponseMapper`
и `ValidationHttpServerInterceptor`.

Теперь ответственности разделены чисто:

- `ValidationHttpServerInterceptor` обрабатывает сгенерированные ошибки проверки данных и возвращает `ErrorResponseTO(message, details)`
- `DataApiExceptionHandler` обрабатывает остальные транспортные сбои, которые мы хотим нормализовать

Только после появления `DataApiExceptionHandler` имеет смысл подключить его в конфигурации генератора.

Обновите задачу генерации данных:

===! ":fontawesome-brands-java: `Java`"

    ```groovy title="build.gradle"
    def openApiGenerateDataHttpServer = tasks.register("openApiGenerateDataHttpServer", GenerateTask) {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/data-http-server.yaml"
        outputDir = "$buildDir/generated/data-http-server"
        def corePackage = "ru.tinkoff.kora.guide.openapi.httpserver.data"
        apiPackage = "${corePackage}.api"
        modelPackage = "${corePackage}.model"
        invokerPackage = "${corePackage}.invoker"
        configOptions = [
                mode                  : "java-server",
                enableServerValidation: "true",
                interceptors          : """
                        {
                          "*": [
                            {
                              "type": "ru.tinkoff.kora.guide.openapi.httpserver.advanced.controller.DataApiExceptionHandler"
                            }
                          ]
                        }
                        """,
        ]
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="build.gradle.kts"
    val openApiGenerateDataHttpServer = tasks.register<GenerateTask>("openApiGenerateDataHttpServer") {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/data-http-server.yaml"
        outputDir = "$buildDir/generated/data-http-server"
        val corePackage = "ru.tinkoff.kora.guide.openapi.httpserver.data"
        apiPackage = "$corePackage.api"
        modelPackage = "$corePackage.model"
        invokerPackage = "$corePackage.invoker"
        configOptions = mapOf(
            "mode" to "java-server",
            "enableServerValidation" to "true",
            "interceptors" to """
                {
                  "*": [
                    {
                      "type": "ru.tinkoff.kora.guide.openapi.httpserver.advanced.controller.DataApiExceptionHandler"
                    }
                  ]
                }
            """.trimIndent()
        )
    }
    ```

## Авторизация по ключу { #api-key }

Механизм сопоставления OpenAPI security-схем с Kora-компонентами описан в разделе [авторизации OpenAPI Codegen](../documentation/openapi-codegen.md#authorization).

До этого момента контракт данных был сосредоточен только на полезных нагрузках, кодах состояния и проверке данных.

Теперь расширим этот контракт явной аутентификацией по ключу API.

Поскольку каждый маршрут в этом контракте должен требовать один и тот же ключ API, добавьте требование безопасности один раз на верхнем уровне файла OpenAPI:

```yaml
security:
    -   apiKeyAuth: [ ]
```

И объявите общую схему безопасности внутри `components`:

```yaml
components:
    securitySchemes:
        apiKeyAuth:
            type: apiKey
            in: header
            name: Authorization
```

После этого изменения `data-http-server.yaml` должен один раз определить глобальную безопасность, а затем объявить саму схему:

```yaml
security:
    -   apiKeyAuth: [ ]

components:
    securitySchemes:
        apiKeyAuth:
            type: apiKey
            in: header
            name: Authorization
```

Это означает, что этот шаг — первый момент, когда контракт данных начинает описывать, кому разрешено вызывать эти маршруты, а не только какими полезными нагрузками они обмениваются. А поскольку
требование глобальное, его не нужно повторять на каждой отдельной операции.

Теперь подключим поведение времени выполнения для этого сгенерированного контракта безопасности.

Создайте контракт конфигурации:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/openapi/httpserver/advanced/controller/DataApiAuthConfig.java"
    package ru.tinkoff.kora.guide.openapi.httpserver.advanced.controller;

    import ru.tinkoff.kora.config.common.annotation.ConfigSource;

    @ConfigSource("auth.apiKey")
    public interface DataApiAuthConfig {
        String value();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/openapi/httpserver/advanced/controller/DataApiAuthConfig.kt"
    package ru.tinkoff.kora.guide.openapi.httpserver.advanced.controller

    import ru.tinkoff.kora.config.common.annotation.ConfigSource

    @ConfigSource("auth.apiKey")
    interface DataApiAuthConfig {
        fun value(): String
    }
    ```

И подключите сгенерированный маркер безопасности в `Application`:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/openapi/httpserver/advanced/Application.java"
    package ru.tinkoff.kora.guide.openapi.httpserver.advanced;

    import java.util.concurrent.CompletableFuture;
    import ru.tinkoff.kora.common.Principal;
    import ru.tinkoff.kora.common.Tag;
    import ru.tinkoff.kora.guide.openapi.httpserver.advanced.controller.DataApiAuthConfig;
    import ru.tinkoff.kora.guide.openapi.httpserver.advanced.controller.DataApiPrincipal;
    import ru.tinkoff.kora.guide.openapi.httpserver.data.api.ApiSecurity;
    import ru.tinkoff.kora.http.server.common.auth.HttpServerPrincipalExtractor;

    @Tag(ApiSecurity.ApiKeyAuth.class)
    default HttpServerPrincipalExtractor<Principal> apiKeyHttpServerPrincipalExtractor(DataApiAuthConfig config) {
        return (request, value) -> {
            if (value == null || !config.value().equals(value)) {
                throw new SecurityException("Invalid API key");
            }
            return CompletableFuture.completedFuture(new DataApiPrincipal("data-api-client"));
        };
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/openapi/httpserver/advanced/Application.kt"
    import java.util.concurrent.CompletableFuture
    import ru.tinkoff.kora.common.Principal
    import ru.tinkoff.kora.common.Tag
    import ru.tinkoff.kora.guide.openapi.httpserver.advanced.controller.DataApiAuthConfig
    import ru.tinkoff.kora.guide.openapi.httpserver.advanced.controller.DataApiPrincipal
    import ru.tinkoff.kora.guide.openapi.httpserver.data.api.ApiSecurity
    import ru.tinkoff.kora.http.server.common.auth.HttpServerPrincipalExtractor

    @Tag(ApiSecurity.ApiKeyAuth::class)
    fun apiKeyHttpServerPrincipalExtractor(config: DataApiAuthConfig): HttpServerPrincipalExtractor<Principal> {
        return HttpServerPrincipalExtractor { _, value ->
            if (value == null || config.value() != value) {
                throw SecurityException("Invalid API key")
            }
            CompletableFuture.completedFuture(DataApiPrincipal("data-api-client"))
        }
    }
    ```

Это один из самых приятных контрактных паттернов в руководстве.

Файл OpenAPI говорит:

- этой группе маршрутов требуется авторизация по ключу API

Генератор говорит:

- вот абстракция безопасности для этого требования

Ваше приложение говорит:

- вот как этот ключ API на самом деле проверяется во время выполнения

Это очень чистое разделение между:

- контрактом
- сгенерированной точкой интеграции
- политикой времени выполнения

## Варианты авторизации { #authorization-options }

Пример в этом руководстве использует самый простой возможный вариант:

- один ключ API
- одно глобальное требование безопасности
- один `HttpServerPrincipalExtractor`

Это отличная отправная точка. Но безопасность OpenAPI может моделировать несколько разных форм, и полезно понимать, чем они отличаются, прежде чем выбирать вариант для настоящего сервиса.

Этот раздел намеренно теоретический. Он не меняет запускаемое приложение из руководства. Вместо этого он показывает распространенные паттерны, которые можно описать в OpenAPI, а затем соединить с
извлекателями времени выполнения Kora.

### 1. Глобальный API-ключ { #1-global-api-key }

Именно этот паттерн мы используем в руководстве.

Он хорошо подходит, когда:

- весь API принадлежит одной защищенной интеграционной поверхности
- каждый маршрут должен требовать один и тот же секрет
- вам нужен минимальный объем связки безопасности

Пример:

```yaml
security:
    -   apiKeyAuth: [ ]

components:
    securitySchemes:
        apiKeyAuth:
            type: apiKey
            in: header
            name: Authorization
```

А в Kora это обычно означает один извлекатель, помеченный сгенерированным маркером безопасности:

```java

@Tag(ApiSecurity.ApiKeyAuth.class)
default HttpServerPrincipalExtractor<Principal> apiKeyHttpServerPrincipalExtractor(MyAuthConfig config) {
    return (request, value) -> {
        if (value == null || !config.value().equals(value)) {
            throw new SecurityException("Invalid API key");
        }
        return CompletableFuture.completedFuture(new MyPrincipal("integration-client"));
    };
}
```

Этот подход прост и практичен для:

- внутренних вызовов между сервисами
- административных конечных точек за инфраструктурными ограничениями
- технических API, которые потребляет небольшое число доверенных клиентов

### 2. Защита маршрутов { #2-route-protection }

Иногда не каждый маршрут должен защищаться одинаково.

Например:

- публичные health или login конечные точки могут оставаться открытыми
- часть маршрутов может требовать авторизацию, а часть оставаться публичной
- один раздел API может использовать другую схему

В этом случае можно не указывать глобальный `security`, а описать его прямо на операциях:

```yaml
paths:
    /public/ping:
        get:
            security: [ ]
            responses:
                '200':
                    description: OK

    /users:
        get:
            security:
                -   apiKeyAuth: [ ]
            responses:
                '200':
                    description: Protected
```

Это полезно, когда поверхность API смешанная:

- часть публичная
- часть защищенная
- часть защищена разными схемами

### 3. Basic Authentication { #3-basic-authentication }

Basic auth — еще один распространенный вариант, описанный в разделе безопасности [генерацию OpenAPI-кода](../documentation/openapi-codegen.md).

Пример:

```yaml
components:
    securitySchemes:
        basicAuth:
            type: http
            scheme: basic

security:
    -   basicAuth: [ ]
```

А сторона Kora обычно выглядит так:

```java

@Tag(ApiSecurity.BasicAuth.class)
default HttpServerPrincipalExtractor<Principal> basicHttpServerPrincipalExtractor() {
    return (request, credentials) -> {
        if (credentials == null) {
            throw new SecurityException("Missing credentials");
        }
        var parts = credentials.split(":", 2);
        if (parts.length != 2) {
            throw new SecurityException("Invalid basic auth format");
        }
        return CompletableFuture.completedFuture(new MyPrincipal(parts[0]));
    };
}
```

Basic auth может быть допустим для:

- простых внутренних инструментов
- демонстраций
- устаревших интеграций

Но обычно его стоит использовать только поверх HTTPS, а во многих современных системах Bearer/JWT является более гибким выбором.

### 4. Bearer-токены и JWT { #4-bearer-tokens-jwt }

Если ваш API предназначен для браузеров, мобильных клиентов или пользовательских сессий, Bearer auth часто подходит лучше, чем ключи API.

Пример:

```yaml
components:
    securitySchemes:
        bearerAuth:
            type: http
            scheme: bearer
            bearerFormat: JWT

security:
    -   bearerAuth: [ ]
```

В Kora извлекатель помечается сгенерированным bearer-маркером:

```java

@Tag(ApiSecurity.BearerAuth.class)
default HttpServerPrincipalExtractor<Principal> bearerHttpServerPrincipalExtractor(JwtService jwtService) {
    return (request, token) -> {
        if (token == null || token.isBlank()) {
            throw new SecurityException("Missing bearer token");
        }
        var user = jwtService.extractUserFromToken(token);
        return CompletableFuture.completedFuture(new UserPrincipal(user));
    };
}
```

Это хорошо работает, когда:

- вызывающий субъект — конечный пользователь, а не только другой сервис
- вам нужно истечение срока действия токена
- внутри токена нужны claims, роли или информация о tenant
- нужны потоки login и refresh-token

Более глубокий справочник по этому стилю смотрите в вариантах безопасности и авторизации в [генерацию OpenAPI-кода](../documentation/openapi-codegen.md).

### 5. Несколько схем { #5-multiple-schemes }

OpenAPI может описывать случаи, когда маршрут принимает одну схему **или** другую.

Это записывается несколькими объектами внутри массива `security`.

Пример:

```yaml
security:
    -   apiKeyAuth: [ ]
    -   basicAuth: [ ]
```

Это означает:

- вызывающий код может аутентифицироваться через `apiKeyAuth`
- или через `basicAuth`

Это полезно в периоды миграции и для смешанных клиентов:

- машинные клиенты могут использовать ключи API
- операторские инструменты могут использовать basic auth

На стороне Kora вы предоставляете извлекатели для обоих сгенерированных маркеров безопасности, а сгенерированный сервер выбирает схему, которая соответствует запросу.

### 6. Комбинированные схемы { #6-combined-schemes }

OpenAPI также поддерживает Комбинированные схемы.

Внутри одного объекта security несколько схем трактуются вместе.

Пример:

```yaml
security:
    -   apiKeyAuth: [ ]
        bearerAuth: [ ]
```

Концептуально это означает, что маршрут ожидает оба требования вместе.

На практике этот стиль менее распространен для простых API, но может иметь смысл, когда:

- один токен идентифицирует пользователя
- другой секрет идентифицирует вызывающее приложение
- инфраструктура требует многоуровневых проверок доверия

Этот паттерн более продвинутый, и его стоит использовать только тогда, когда дополнительная сложность действительно оправдана.

### 7. Публичные маршруты { #7-public-routes }

Один тонкий, но важный прием OpenAPI:

```yaml
security: [ ]
```

Когда он используется на конкретной операции, он может переопределить глобальное требование безопасности и сделать эту конечную точку публичной.

Это особенно полезно, когда API в основном защищен, но несколько маршрутов должны оставаться открытыми, например:

- `/auth/login`
- `/auth/refresh`
- `/public/ping`
- `/public/openapi-download`

Так вы получаете хороший вариант по умолчанию без необходимости повторять объявления безопасности везде.

### 8. Выбор авторизации { #8-choosing-authorization }

Простое практическое правило:

- Используйте глобальную безопасность по ключу API для внутренних интеграционных API.
- Используйте безопасность на уровне маршрута, когда API смешивает публичные и защищенные конечные точки.
- Используйте Basic auth только для простых или устаревших сценариев.
- Используйте Bearer/JWT, когда важны пользователи, сессии, роли или claims.
- Используйте несколько альтернативных схем, когда нужен путь миграции или разные типы клиентов.
- Используйте комбинированные схемы только когда действительно нужна многоуровневая аутентификация.

### 9. Поддержка в Kora { #9-kora-support }

Какую бы схему вы ни выбрали, контрактный поток остается очень похожим:

1. описать схему в `components.securitySchemes`
2. подключить ее глобально или на уровне маршрутов через `security`
3. заново сгенерировать сервер
4. реализовать `HttpServerPrincipalExtractor<Principal>`, помеченный сгенерированным маркером `ApiSecurity.*`
5. при необходимости нормализовать ошибки авторизации через слой обработки исключений

Главный вывод: OpenAPI описывает контракт безопасности, а Kora дает сгенерированную точку интеграции, чтобы enforce it at runtime.

## Конфигурация { #configuration }

Теперь настройте приложение так, чтобы оно публиковало оба файла OpenAPI и значение авторизации.

Обновите `src/main/resources/application.conf`:

Полный справочник по конфигурации смотрите в [HTTP-сервер](../documentation/http-server.md), [Configuration](../documentation/config.md), [OpenAPI Management](../documentation/openapi-management.md)
и [журналирование SLF4J](../documentation/logging-slf4j.md).

===! ":material-code-json: `Hocon`"

    ```javascript title="src/main/resources/application.conf"
    httpServer {
      publicApiHttpPort = 8080 //(1)!
      privateApiHttpPort = 8085 //(2)!
      telemetry.logging.enabled = true //(3)!
    }

    auth {
      apiKey {
        value = "MySecuredApiKey" //(4)!
        value = ${?OPENAPI_HTTP_SERVER_ADVANCED_API_KEY} //(5)!
      }
    }

    openapi {
      management {
        file = [ "openapi/user-http-server.yaml", "openapi/data-http-server.yaml" ] //(6)!
        enabled = true //(7)!
        endpoint = "/openapi" //(8)!
        swaggerui {
          enabled = true //(9)!
          endpoint = "/swagger-ui" //(10)!
        }
      }
    }

    logging.level {
      "root" = "WARN" //(11)!
      "ru.tinkoff.kora" = "INFO" //(12)!
      "ru.tinkoff.kora.guide.openapi.httpserver.advanced" = "INFO" //(13)!
    }
    ```

    1. Публичный HTTP-порт по умолчанию, используемый конечными точками приложения.
    2. Приватный HTTP-порт по умолчанию, используемый пробами, метриками и конечными точками управления.
    3. Включает возможность для этого раздела конфигурации.
    4. Настроенное значение, которое использует компонент руководства.
    5. Настроенное значение, которое использует компонент руководства. Необязательное переопределение из `OPENAPI_HTTP_SERVER_ADVANCED_API_KEY`.
    6. Значение для `openapi.management.file`.
    7. Включает возможность для этого раздела конфигурации.
    8. Конечная точка экспортера телеметрии.
    9. Включает возможность для этого раздела конфигурации.
    10. Конечная точка экспортера телеметрии.
    11. Значение для `logging.level.root`.
    12. Значение для `logging.level.ru.tinkoff.kora`.
    13. Значение для `logging.level.ru.tinkoff.kora.guide.openapi.httpserver.advanced`.

=== ":simple-yaml: `YAML`"

    ```yaml title="src/main/resources/application.yaml"
    httpServer:
      publicApiHttpPort: 8080 #(1)!
      privateApiHttpPort: 8085 #(2)!
      telemetry:
        logging:
          enabled: true #(3)!
    auth:
      apiKey:
        value: ${?OPENAPI_HTTP_SERVER_ADVANCED_API_KEY:"MySecuredApiKey"} #(4)!
    openapi:
      management:
        file: [ "openapi/user-http-server.yaml", "openapi/data-http-server.yaml" ] #(5)!
        enabled: true #(6)!
        endpoint: "/openapi" #(7)!
        swaggerui:
          enabled: true #(8)!
          endpoint: "/swagger-ui" #(9)!
    logging:
      level:
        root: "WARN" #(10)!
        "ru.tinkoff.kora": "INFO" #(11)!
        "ru.tinkoff.kora.guide.openapi.httpserver.advanced": "INFO" #(12)!
    ```

    1. Публичный HTTP-порт по умолчанию, используемый конечными точками приложения.
    2. Приватный HTTP-порт по умолчанию, используемый пробами, метриками и конечными точками управления.
    3. Включает возможность для этого раздела конфигурации.
    4. Настроенное значение, которое использует компонент руководства. Использует показанное значение по умолчанию и позволяет `OPENAPI_HTTP_SERVER_ADVANCED_API_KEY` переопределить его.
    5. Значение для `openapi.management.file`.
    6. Включает возможность для этого раздела конфигурации.
    7. Конечная точка экспортера телеметрии.
    8. Включает возможность для этого раздела конфигурации.
    9. Конечная точка экспортера телеметрии.
    10. Значение для `logging.level.root`.
    11. Значение для `logging.level.ru.tinkoff.kora`.
    12. Значение для `logging.level.ru.tinkoff.kora.guide.openapi.httpserver.advanced`.

Это делает все приложение целостным:

- одно приложение времени выполнения
- два контракта
- одна общая публикация OpenAPI
- один Swagger UI

Именно так часто растет настоящий сервис. Разные HTTP-области могут создаваться по-разному или генерироваться с разными параметрами, но все равно поставляться как одно приложение.

## Проверка приложения { #check-app }

Соберите:

```bash
./gradlew :guides-apps:guide-openapi-http-server-advanced-app:clean :guides-apps:guide-openapi-http-server-advanced-app:classes
```

Запустите:

```bash
./gradlew run
```

Попробуйте конечную точку формы:

```bash
curl -X POST http://localhost:8080/data/form \
  -H "Authorization: MySecuredApiKey" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "name=Ivan"
```

Ожидаемый результат:

```text
Hello World, Ivan
```

Попробуйте конечную точку multipart:

```bash
curl -X POST http://localhost:8080/data/upload \
  -H "Authorization: MySecuredApiKey" \
  -F "description=My test file" \
  -F "file=@README.md"
```

Ожидаемый результат: JSON с `fileCount` и `fileNames`.

Попробуйте конечную точку JSON-сопоставления:

```bash
curl -X GET http://localhost:8080/data/mapping-by-code/200 \
  -H "Authorization: MySecuredApiKey"
```

Ожидаемый результат:

```json
{
    "message": "Hello from response mapper"
}
```

Попробуйте ошибку проверки данных:

```bash
curl -X GET http://localhost:8080/data/mapping-by-code/700 \
  -H "Authorization: MySecuredApiKey"
```

Ожидаемый результат: ошибка `400` до того, как делегат примет значение, потому что `700` находится вне допустимого диапазона `200..599`.

Попробуйте запрос без авторизации:

```bash
curl -X POST http://localhost:8080/data/form \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "name=Ivan"
```

Ожидаемый результат: `403` со сгенерированным `ErrorResponseTO`.

Откройте:

```text
http://localhost:8080/swagger-ui
```

и убедитесь, что в объединенной документации видны и маршруты пользователей, и маршруты данных.

## Тестирование { #testing }

Запустите:

```bash
./gradlew test
```

Тесты запускаемого приложения проверяют два ключевых потока:

- существующий сгенерированный CRUD-делегат пользователей все еще работает
- новые сгенерированные делегаты данных тоже работают, включая `mappingByCode(200)`

Это соответствует учебной цели руководства:

- сохранить предыдущий OpenAPI-поток пользователей
- добавить продвинутое сгенерированное поведение данных постепенно

## Лучшие практики { #best-practices }

- Оставляйте существующий сгенерированный контракт неизменным, когда добавляете второй, более продвинутый контракт.
- Разделяйте контракты, когда группам конечных точек нужны разные возможности генерации.
- Используйте OpenAPI `securitySchemes` как источник истины для требований авторизации.
- Используйте перехватчики, привязанные к конкретному сгенерированному контракту, когда особая обработка ошибок нужна только одной сгенерированной области.
- Вводите проверку данных по спецификации постепенно на одном маршруте, когда так история понятнее.
- Держите реализации делегатов маленькими и сосредоточенными на прикладном поведении, а не на транспортной связке.
- Оставляйте `@Json` на любом рукописном DTO-классе, который сериализуется или десериализуется как JSON; сгенерированные OpenAPI-модели `*TO` создаются для контракта, но ваши собственные DTO все равно
  должны явно включать генерацию JSON-преобразователей.

## Итоги { #summary }

Вы расширили контрактный HTTP-сервер из [openapi-http-server.md](openapi-http-server.md) вторым сгенерированным API для продвинутых HTTP-задач:

- `user-http-server.yaml` остался неизменным для CRUD пользователей
- `data-http-server.yaml` ввел конечные точки form, multipart и сопоставления ответов
- только задача генерации данных получила перехватчики контроллера и проверку данных
- проверка данных была показана на одном сгенерированном параметре пути, `code`
- авторизация по ключу API управлялась контрактом безопасности OpenAPI
- оба контракта были опубликованы вместе через OpenAPI management

Теперь приложение показывает более реалистичный путь контрактного развития: сохранять стабильные сгенерированные API нетронутыми и добавлять новые сгенерированные поверхности с более
специализированным поведением только там, где это нужно.

## Ключевые понятия { #key-concepts }

- одно приложение может размещать несколько сгенерированных серверных контрактов OpenAPI
- разные задачи генерации могут использовать разные параметры
- `controllerInterceptors` — мощный способ формировать поведение сгенерированного контроллера
- OpenAPI `securitySchemes` естественно сопоставляются с извлекателями principal времени выполнения
- проверку данных по спецификации можно включать выборочно для каждого контракта
- сгенерированную проверку данных можно вводить постепенно на одном маршруте, а не везде сразу
- делегаты остаются главным местом для сопоставления транспорта с приложением

## Устранение неполадок { #troubleshooting }

**Конечные точки данных отсутствуют в графе:**

Проверьте, что:

- `openApiGenerateDataHttpServer` зарегистрирована
- ее `outputDir` добавлен в `sourceSets.main`
- `compileJava` зависит от задачи
- `DataApiDelegateImpl` аннотирован `@Component`

**Авторизация по ключу API не работает:**

Проверьте, что:

- `data-http-server.yaml` содержит `securitySchemes.apiKeyAuth`
- маршруты включают `security: - apiKeyAuth: []`
- извлекатель principal помечен `@Tag(ApiSecurity.ApiKeyAuth.class)`
- настроенное значение совпадает с заголовком `Authorization`

**Проверка данных не срабатывает:**

Проверьте, что:

- `enableServerValidation = "true"` задан на задаче генерации **data**
- ограничение действительно присутствует в схеме OpenAPI для `/data/mapping-by-code/{code}`
- вы проверяете значение вне допустимого диапазона `200..599`

**Ответы об ошибках не являются JSON:**

Проверьте, что:

- задача генерации включает конфигурацию `interceptors`
- она указывает на `DataApiExceptionHandler`
- `DataApiExceptionHandler` является компонентом
- `ErrorResponseTO` объявлен в `data-http-server.yaml`

**Swagger UI показывает только один контракт:**

Проверьте `openapi.management.file` в `application.conf`.

Он должен включать оба:

- `openapi/user-http-server.yaml`
- `openapi/data-http-server.yaml`

## Что дальше? { #whats-next }

- [HTTP-клиент](http-client.md), если вы еще не создавали клиентское приложение.
- [OpenAPI HTTP-клиент](openapi-http-client.md) после HTTP-клиента, чтобы потреблять API, сгенерированные по контракту, с типизированными обертками ответов.
- [Продвинутый HTTP-клиент](http-client-advanced.md) после HTTP-клиента, чтобы сравнить сгенерированные клиенты с рукописными продвинутыми клиентами.
- [Наблюдаемость](observability.md), чтобы наблюдать за сгенерированными контроллерами, ошибками проверки данных, проверками безопасности и перехватчиками.
- [Шаблоны устойчивости](resilient.md), чтобы защитить клиентов, которые вызывают эти сгенерированные конечные точки.

## Помощь { #help }

Если вы застряли:

- сравните с [Kora Java OpenAPI HTTP Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-openapi-http-server-advanced-app) и [Kora Kotlin OpenAPI HTTP Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-openapi-http-server-advanced-app)
- вернитесь к [OpenAPI HTTP-сервер](openapi-http-server.md) для базовой модели сгенерированного делегата
- вернитесь к [Продвинутый HTTP-сервер](http-server-advanced.md) для рукописной версии похожих HTTP-возможностей
- проверьте [документацию по генерации OpenAPI-кода](../documentation/openapi-codegen.md)
- проверьте [документацию OpenAPI Management](../documentation/openapi-management.md)
