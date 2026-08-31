---
search:
  exclude: true
title: Продвинутое руководство по контрактному HTTP-серверу
summary: Continue the OpenAPI HTTP Server guide by adding a second generated contract for forms, multipart, response mapping, generated controller interceptors, API-key authorization, and spec-driven validation
description: "Advanced contract-first Kora HTTP server: a second OpenAPI contract and a second GenerateTask, generated form and multipart FormParam records, sealed response wrappers, controller interceptors declared through the extensions generator option, a custom ViolationExceptionHttpServerResponseMapper, JsonNullable model fields, and API-key authorization through ApiSecurity markers and HttpServerPrincipalExtractor."
agent:
  use_when: "Use this file for questions about advanced contract-first Kora HTTP servers: hosting several OpenAPI contracts and GenerateTask tasks in one application, generated <Api>Controller.<Op>FormParam records for application/x-www-form-urlencoded and multipart/form-data, enableServerValidation with a custom ViolationExceptionHttpServerResponseMapper, attaching an HttpServerInterceptor through the extensions configOption with interceptorType, generated ApiSecurity markers from components.securitySchemes, HttpServerPrincipalExtractor with @Tag, Principal and PrincipalWithScopes, and publishing several files through openapi.management.files."
tags: openapi, http-server, advanced, forms, multipart, auth, validation
---

# Продвинутое руководство по контрактному HTTP-серверу { #advanced-contract-first-http }

Это руководство знакомит с продвинутыми контрактными приемами HTTP-сервера в Kora на основе OpenAPI. В нем разбирается, как несколько спецификаций OpenAPI уживаются в одном приложении, как
сгенерированные делегаты обрабатывают формы, multipart-загрузки и типизированные варианты ответов, и как общая обработка ошибок и авторизация по API-ключу встраиваются вокруг сгенерированного
транспортного кода. Вы также увидите, как новые контракты могут развиваться независимо, пока написанные вручную сервисы остаются местом для прикладного поведения.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java OpenAPI HTTP Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-openapi-http-server-advanced-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin OpenAPI HTTP Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-openapi-http-server-advanced-app).

## Что вы создадите { #youll-build }

Вы расширите OpenAPI HTTP-сервер:

- тем же контрактом CRUD пользователей из [Контрактного HTTP-сервера с OpenAPI](openapi-http-server.md)
- вторым контрактом OpenAPI с именем `data-http-server.yaml`
- сгенерированными конечными точками для форм, multipart и отображения ответов
- перехватчиком сгенерированного контроллера для единообразных JSON-ответов об ошибках
- собственным маппером ошибок валидации, говорящим на том же контракте `ErrorResponseTO`
- простой авторизацией по API-ключу для конечных точек данных
- одной общей публикацией `/openapi` и `/swagger-ui` для обоих контрактов

## Что вам понадобится { #youll-need }

- JDK 25 или новее
- Gradle 9+
- Текстовый редактор или IDE
- Пройденное руководство [Контрактный HTTP-сервер с OpenAPI](openapi-http-server.md)
- Пройденное руководство [Продвинутый HTTP-сервер](http-server-advanced.md)

## Требования { #prerequisites }

!!! note "Сначала пройдите руководства по OpenAPI HTTP-серверу и продвинутому HTTP-серверу"

    Руководство предполагает, что вы прошли **[Контрактный HTTP-сервер с OpenAPI](openapi-http-server.md)** и **[Продвинутый HTTP-сервер](http-server-advanced.md)** и уже разобрались с контрактным потоком CRUD пользователей и продвинутыми возможностями HTTP, которые используют маршруты данных.

    Если эти руководства еще не пройдены, начните с них: здесь мы соединяем сгенерированные делегаты OpenAPI с продвинутыми возможностями HTTP — формами, multipart, общими ошибками и безопасностью.

Вместо повторного объяснения этих частей мы сосредоточены на следующем шаге: как применить продвинутые идеи HTTP в сгенерированном контрактном HTTP-сервере.

## Обзор { #overview }

В этом руководстве мы двигаемся в строго заданном порядке:

1. оставляем сгенерированное API пользователей без изменений
2. добавляем второй контракт OpenAPI только для продвинутых маршрутов данных
3. настраиваем вторую задачу генерации Kora именно под этот контракт
4. изучаем новые сгенерированные абстракции
5. реализуем `DataApiDelegate`
6. приводим ошибки валидации к собственной модели ошибок контракта
7. подключаем перехватчик сгенерированного контроллера для общего отображения ошибок
8. добавляем авторизацию по API-ключу через контракт безопасности OpenAPI
9. публикуем оба контракта вместе через OpenAPI management

Ключевая идея дизайна — разделение:

- API пользователей остается стабильным контрактом из предыдущего руководства
- продвинутое API данных развивается в собственном контракте

Так пример проще объяснять, и он гораздо ближе к тому, как реальные сервисы обычно растут.

### Разные контракты { #different-contracts }

На первый взгляд кажется, что проще держать все в одном большом файле OpenAPI.

Иногда это верно. Но иногда отдельный контракт здоровее:

- разные группы конечных точек развиваются с разной скоростью
- одной группе могут понадобиться дополнительные возможности генерации
- у одной группы могут быть другие требования к безопасности или валидации
- одна группа может существовать в основном для демонстрации транспортных приемов, а не бизнес-CRUD

Именно это наша ситуация.

Контракт CRUD пользователей уже хорош. Мы не хотим ни объяснять его заново, ни случайно изменить его, добавляя продвинутые примеры HTTP.

Поэтому мы выносим продвинутые маршруты в отдельный контракт:

- `user-http-server.yaml` остается источником истины для CRUD пользователей
- `data-http-server.yaml` становится источником истины для форм, multipart, общей обработки ошибок, авторизации по API-ключу и одного точечного примера валидации

Именно поэтому опцию `extensions`, подключающую перехватчик контроллера, получает только задача генерации **данных**. Генератор пользователей остается ровно таким же, как в предыдущем руководстве.

В одном модуле может жить несколько задач `GenerateTask`. Они могут писать даже в один и тот же `outputDir`; единственное настоящее требование — чтобы сгенерированные пакеты не пересекались, поэтому
дайте каждой задаче собственные `apiPackage`, `modelPackage` и `invokerPackage`.

## Старый контракт OpenAPI { #old-contract }

Первый важный шаг — на самом деле не шаг: **не** переписывайте сторону пользователей.

Переиспользуйте ту же задачу генерации и тот же контракт из [Контрактного HTTP-сервера с OpenAPI](openapi-http-server.md).

Эта деталь очень важна для сюжета руководства.

Мы **не** заменяем предыдущее руководство. Мы его расширяем.

Поэтому части, относящиеся к пользователям, остаются прежними:

- `user-http-server.yaml`
- `UsersApiDelegate`
- `UserApiDelegateImpl`
- привычный поток `UserService` и репозитория

Вся новая работа в этом руководстве — про продвинутые конечные точки данных.

## Новый контракт OpenAPI { #new-contract }

Теперь перенесем идеи продвинутого `DataController` из [Продвинутого HTTP-сервера](http-server-advanced.md) в собственный контракт OpenAPI.

Создайте `src/main/resources/openapi/data-http-server.yaml`:

??? example "Контракт OpenAPI"

    ```yaml
    openapi: 3.0.3
    info:
      title: Advanced Data API
      description: Form and multipart endpoints generated from a dedicated OpenAPI contract
      version: 1.0.0
    tags:
      - name: data
        description: Form and multipart operations
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
            - name: code
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
    security:
      - apiKeyAuth: []
    components:
      securitySchemes:
        apiKeyAuth:
          type: apiKey
          in: header
          name: Authorization
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

Четыре вещи в этом контракте определяют все, что будет дальше:

- тела запросов `application/x-www-form-urlencoded` и `multipart/form-data`, которые генератор превращает в отдельные записи параметров формы, а не в JSON-модели
- `format: binary`, из-за которого `UploadRequestTO.file` становится частью файла, а не строкой
- `minimum: 200` / `maximum: 599` на path-параметре `code`, которые становятся настоящим ограничением валидации
- требование `security` верхнего уровня плюс запись в `components.securitySchemes`, из которых генерируются маркеры `ApiSecurity`

Свойство `details` в `ErrorResponseTO` заслуживает отдельного замечания. Оно `nullable: true` **и** отсутствует в `required`, поэтому у него три различимых состояния — отсутствует, явно равно `null` и
присутствует со значением. Kora генерирует такое поле как [`JsonNullable`](../documentation/json.md#jsonnullable-wrapper), поэтому маппер ниже оборачивает свой список в `JsonNullable.of(...)`.

## Генерация по OpenAPI { #openapi-generation }

Теперь настроим вторую задачу генерации.

Это самый важный сборочный шаг всего руководства, потому что именно здесь мы намеренно обращаемся с API данных иначе, чем с API пользователей.

===! ":fontawesome-brands-java: `Java`"

    Обновите `build.gradle`:

    ```groovy
    def openApiGenerateDataHttpServer = tasks.register("openApiGenerateDataHttpServer", GenerateTask) {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = layout.projectDirectory.file("src/main/resources/openapi/data-http-server.yaml")
        outputDir = layout.buildDirectory.dir("generated/data-http-server")
        def corePackage = "io.koraframework.guide.openapi.httpserver.data" //(1)!
        apiPackage = "${corePackage}.api"
        modelPackage = "${corePackage}.model"
        invokerPackage = "${corePackage}.invoker"
        configOptions = [
                mode                  : "java-server",
                enableServerValidation: "true", //(2)!
        ]
    }

    sourceSets.main {
        java.srcDirs += openApiGenerateUsersHttpServer.get().outputDir
        java.srcDirs += openApiGenerateDataHttpServer.get().outputDir //(3)!
    }

    compileJava.dependsOn openApiGenerateUsersHttpServer
    compileJava.dependsOn openApiGenerateDataHttpServer
    ```

    1.  Собственный пакет, чтобы два контракта не пересекались, хотя оба генерируют `ErrorResponseTO`.
    2.  Превращает ограничение `minimum` / `maximum` на `code` в настоящую аннотацию валидации на сгенерированном контроллере.
    3.  Регистрируются оба сгенерированных дерева; в задаче пользователей ничего не меняется.

=== ":simple-kotlin: `Kotlin`"

    Обновите `build.gradle.kts`:

    ```kotlin
    val openApiGenerateDataHttpServer = tasks.register<GenerateTask>("openApiGenerateDataHttpServer") {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec.set(layout.projectDirectory.file("src/main/resources/openapi/data-http-server.yaml"))
        outputDir.set(layout.buildDirectory.dir("generated/data-http-server"))
        val corePackage = "io.koraframework.guide.openapi.httpserver.data" //(1)!
        apiPackage = "${corePackage}.api"
        modelPackage = "${corePackage}.model"
        invokerPackage = "${corePackage}.invoker"
        configOptions = mapOf(
            "mode" to "kotlin-server",
            "enableServerValidation" to "true", //(2)!
        )
    }

    kotlin.sourceSets.main {
        kotlin.srcDir(openApiGenerateUsersHttpServer.get().outputDir)
        kotlin.srcDir(openApiGenerateDataHttpServer.get().outputDir) //(3)!
    }

    tasks.matching { it.name.startsWith("ksp") }.configureEach {
        dependsOn(openApiGenerateUsersHttpServer)
        dependsOn(openApiGenerateDataHttpServer)
    }
    ```

    1.  Собственный пакет, чтобы два контракта не пересекались, хотя оба генерируют `ErrorResponseTO`.
    2.  Превращает ограничение `minimum` / `maximum` на `code` в настоящую аннотацию валидации на сгенерированном контроллере.
    3.  Регистрируются оба сгенерированных дерева; в задаче пользователей ничего не меняется.

Почему это разделение так полезно:

- `openApiGenerateUsersHttpServer` остается простым и неизменным
- `openApiGenerateDataHttpServer` получает продвинутое поведение

И на этом раннем этапе мы намеренно держим конфигурацию генератора минимальной. Мы пока **не** настраиваем собственный перехватчик сгенерированного контроллера: сначала реализуем делегат, затем
приводим в порядок ошибки валидации, и только после появления `DataApiExceptionHandler` подключаем его. Так руководство идет в том же порядке, в котором эти классы реально появляются.

Это ровно тот случай разделения возможностей, который оправдывает второй контракт.

## Сгенерированные классы { #generated-classes }

Выполните:

```bash
./gradlew clean classes
```

Теперь изучите сгенерированные файлы:

===! ":fontawesome-brands-java: `Java`"

    - `build/generated/data-http-server/io/koraframework/guide/openapi/httpserver/data/api/DataApiController.java`
    - `build/generated/data-http-server/io/koraframework/guide/openapi/httpserver/data/api/DataApiDelegate.java`
    - `build/generated/data-http-server/io/koraframework/guide/openapi/httpserver/data/api/DataApiResponses.java`
    - `build/generated/data-http-server/io/koraframework/guide/openapi/httpserver/data/api/DataApiServerRequestMappers.java`
    - `build/generated/data-http-server/io/koraframework/guide/openapi/httpserver/data/api/ApiSecurity.java`
    - `build/generated/data-http-server/io/koraframework/guide/openapi/httpserver/data/model/UploadResponseTO.java`
    - `build/generated/data-http-server/io/koraframework/guide/openapi/httpserver/data/model/PayloadTO.java`
    - `build/generated/data-http-server/io/koraframework/guide/openapi/httpserver/data/model/ErrorResponseTO.java`

=== ":simple-kotlin: `Kotlin`"

    - `build/generated/data-http-server/io/koraframework/guide/openapi/httpserver/data/api/DataApiController.kt`
    - `build/generated/data-http-server/io/koraframework/guide/openapi/httpserver/data/api/DataApiDelegate.kt`
    - `build/generated/data-http-server/io/koraframework/guide/openapi/httpserver/data/api/DataApiResponses.kt`
    - `build/generated/data-http-server/io/koraframework/guide/openapi/httpserver/data/api/DataApiServerRequestMappers.kt`
    - `build/generated/data-http-server/io/koraframework/guide/openapi/httpserver/data/api/ApiSecurity.kt`
    - `build/generated/data-http-server/io/koraframework/guide/openapi/httpserver/data/model/UploadResponseTO.kt`
    - `build/generated/data-http-server/io/koraframework/guide/openapi/httpserver/data/model/PayloadTO.kt`
    - `build/generated/data-http-server/io/koraframework/guide/openapi/httpserver/data/model/ErrorResponseTO.kt`

Самые интересные сгенерированные абстракции здесь — `DataApiDelegate`, `DataApiController`, `DataApiResponses` и `ApiSecurity`.

`DataApiDelegate`:

Это контракт, который вы реализуете. Он играет ровно ту же архитектурную роль, что и `UsersApiDelegate`, но для новых продвинутых конечных точек.

Одна форма здесь новая. Тело запроса формы или multipart не является JSON-моделью, поэтому оно не передается как модель `*TO`. Генератор выпускает по одной записи на каждую операцию с формой, вложенной
в **контроллер**, и передает ее делегату через сгенерированный маппер запроса:

- `DataApiController.ProcessFormFormParam(String name)`
- `DataApiController.ProcessUploadFormParam(String description, FormMultipart.FormPart file)`

Заметьте, что `UploadRequestTO` нет в списке сгенерированных моделей выше: поскольку эта схема используется только как тело `multipart/form-data`, ее поля становятся записью формы.

Свойство `format: binary` становится `FormMultipart.FormPart` — запечатанным типом, у которого `name()` — это **имя поля формы**. Имя загруженного файла — другое значение: сопоставьте с
`FormMultipart.FormPart.MultipartFile` и прочитайте его `fileName()`, когда оно вам нужно.

`DataApiController`:

Это сгенерированный транспортный слой. Поскольку контракт включает вход form-url-encoded, вход multipart, явное моделирование статусов и требование безопасности, сгенерированный контроллер делает
заметно больше, чем в простом случае CRUD: он декодирует части формы через `DataApiServerRequestMappers`, применяет сгенерированные аннотации валидации и запускает сгенерированный перехватчик
безопасности до вызова вашего делегата.

`DataApiResponses`:

Эти обертки моделируют допустимые HTTP-исходы из спецификации: `200`, `400`, `403` и `500`. Значит, обработка ошибок теперь часть транспортного контракта, а не что-то, что мы импровизируем в коде.

Обратите внимание, что `processForm` объявляет успешное тело `text/plain`, поэтому `ProcessForm200ApiResponse` несет в `content` обычную `String` — обертки ответов следуют объявленному типу
содержимого, а не только JSON.

`ApiSecurity`:

Это генерируется из секции `securitySchemes` OpenAPI. Имя схемы приводится к PascalCase, поэтому `apiKeyAuth` превращается в класс-маркер `ApiSecurity.ApiKeyAuth`. Он служит мостом между контрактом
безопасности OpenAPI и извлекателем принципала, который вы зарегистрируете в `Application`.

Это одна из самых ценных идей руководства:

- безопасность объявлена в контракте
- генератор выпускает типы-маркеры
- ваше приложение подключает реальную проверку

## Делегат { #delegate }

Теперь соединим сгенерированный транспортный слой данных с прикладной логикой.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/io/koraframework/guide/openapi/httpserver/advanced/controller/DataApiDelegateImpl.java`:

    ```java
    package io.koraframework.guide.openapi.httpserver.advanced.controller;

    import java.util.List;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.openapi.httpserver.data.api.DataApiController;
    import io.koraframework.guide.openapi.httpserver.data.api.DataApiDelegate;
    import io.koraframework.guide.openapi.httpserver.data.api.DataApiResponses;
    import io.koraframework.guide.openapi.httpserver.data.model.PayloadTO;
    import io.koraframework.guide.openapi.httpserver.data.model.UploadResponseTO;
    import io.koraframework.http.server.common.response.HttpServerResponseException;

    @Component
    public final class DataApiDelegateImpl implements DataApiDelegate {

        @Override
        public DataApiResponses.ProcessFormApiResponse processForm(DataApiController.ProcessFormFormParam form) {
            if ("admin".equalsIgnoreCase(form.name())) {
                throw new RestrictedFormNameException(form.name()); //(1)!
            }
            return new DataApiResponses.ProcessFormApiResponse.ProcessForm200ApiResponse("Hello World, " + form.name());
        }

        @Override
        public DataApiResponses.ProcessUploadApiResponse processUpload(DataApiController.ProcessUploadFormParam form) {
            var response = new UploadResponseTO(
                    1,
                    List.of(form.file().name()) //(2)!
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
            throw HttpServerResponseException.of(code, "Request failed with code " + code); //(3)!
        }
    }
    ```

    1.  Доменное исключение, которое не описано ни одной сгенерированной оберткой; добавленный позже перехватчик превратит его в `500` из контракта.
    2.  `FormPart.name()` — это имя поля формы (здесь `file`); ручной разбор `HttpServerRequest` не нужен.
    3.  Бросать исключение правильно для статусов, выходящих за объявленное семейство ответов этой операции.

    И небольшой тип исключения, который он использует, `src/main/java/io/koraframework/guide/openapi/httpserver/advanced/controller/RestrictedFormNameException.java`:

    ```java
    package io.koraframework.guide.openapi.httpserver.advanced.controller;

    public final class RestrictedFormNameException extends RuntimeException {

        public RestrictedFormNameException(String name) {
            super("Form name '" + name + "' is restricted");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/io/koraframework/guide/openapi/httpserver/advanced/controller/DataApiDelegateImpl.kt`:

    ```kotlin
    package io.koraframework.guide.openapi.httpserver.advanced.controller

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.openapi.httpserver.data.api.DataApiController
    import io.koraframework.guide.openapi.httpserver.data.api.DataApiDelegate
    import io.koraframework.guide.openapi.httpserver.data.api.DataApiResponses
    import io.koraframework.guide.openapi.httpserver.data.model.PayloadTO
    import io.koraframework.guide.openapi.httpserver.data.model.UploadResponseTO
    import io.koraframework.http.server.common.response.HttpServerResponseException

    @Component
    class DataApiDelegateImpl : DataApiDelegate {

        override fun processForm(form: DataApiController.ProcessFormFormParam): DataApiResponses.ProcessFormApiResponse {
            if (form.name.equals("admin", ignoreCase = true)) {
                throw RestrictedFormNameException(form.name) //(1)!
            }

            return DataApiResponses.ProcessFormApiResponse.ProcessForm200ApiResponse("Hello World, ${form.name}")
        }

        override fun processUpload(form: DataApiController.ProcessUploadFormParam): DataApiResponses.ProcessUploadApiResponse {
            val response = UploadResponseTO(fileCount = 1, fileNames = listOf(form.file.name())) //(2)!
            return DataApiResponses.ProcessUploadApiResponse.ProcessUpload200ApiResponse(response)
        }

        override fun mappingByCode(code: Int): DataApiResponses.MappingByCodeApiResponse {
            if (code == 200) {
                return DataApiResponses.MappingByCodeApiResponse.MappingByCode200ApiResponse(
                    PayloadTO("Hello from response mapper")
                )
            }
            throw HttpServerResponseException.of(code, "Request failed with code $code") //(3)!
        }
    }
    ```

    1.  Доменное исключение, которое не описано ни одной сгенерированной оберткой; добавленный позже перехватчик превратит его в `500` из контракта.
    2.  `FormPart.name()` — это имя поля формы (здесь `file`); ручной разбор `HttpServerRequest` не нужен.
    3.  Бросать исключение правильно для статусов, выходящих за объявленное семейство ответов этой операции.

    И небольшой тип исключения, который он использует, `src/main/kotlin/io/koraframework/guide/openapi/httpserver/advanced/controller/RestrictedFormNameException.kt`:

    ```kotlin
    package io.koraframework.guide.openapi.httpserver.advanced.controller

    class RestrictedFormNameException(name: String) : RuntimeException("Form name '$name' is restricted")
    ```

Здесь стоит отметить две приятные вещи.

Во-первых, делегат остается очень маленьким. Потому что сгенерированный слой уже сделал многое:

- декодирование запроса, включая части формы и multipart
- транспортную типизацию
- интеграцию с контрактом безопасности
- точки подключения валидации

Во-вторых, логика намеренно повторяет ручной `DataController` из [Продвинутого HTTP-сервера](http-server-advanced.md). Руководство не изобретает другое поведение. Оно показывает, как то же поведение
выглядит, когда транспортный слой генерируется по OpenAPI, а не пишется руками.

Есть и намеренный контраст между двумя путями ошибок, и именно из-за него существуют следующие два раздела:

- `mappingByCode` бросает `HttpServerResponseException`, который уже несет код статуса
- `processForm` бросает `RestrictedFormNameException`, который не несет ничего пригодного для HTTP-слоя

Обе ситуации сейчас дают ответ, который **не** соответствует форме `ErrorResponseTO`, обещанной контрактом. Исправить это — задача перехватчика, который мы добавим ниже.

## Серверная валидация { #server-validation }

Полные правила серверной валидации по OpenAPI описаны в разделе [OpenAPI Codegen: валидация](../documentation/openapi-codegen.md#validation).

`enableServerValidation` уже включен в задаче данных, поэтому валидация активна. В этом руководстве мы намеренно держим поверхность валидации очень маленькой — ограничен только один параметр:

- `code` в `/data/mapping-by-code/{code}`, допустимый диапазон `200..599`

Это полезно по двум причинам. Во-первых, наглядно демонстрирует валидацию по спецификации на одном точечном примере. Во-вторых, не превращает весь продвинутый контракт в учебник по валидации: шаги с
формой и multipart остаются про транспортные форматы.

Когда валидация включена, генератор также добавляет на контроллер `@InterceptWith(ValidationHttpServerInterceptor.class)`. Этот перехватчик ловит `ViolationException` и по умолчанию отвечает простым
`400`. Простой текст — не то, что обещает наш контракт, поэтому научим его форме `ErrorResponseTO`, предоставив компонент `ViolationExceptionHttpServerResponseMapper`:

===! ":fontawesome-brands-java: `Java`"

    Добавьте в `src/main/java/io/koraframework/guide/openapi/httpserver/advanced/Application.java`:

    ```java
    default ViolationExceptionHttpServerResponseMapper customViolationExceptionHttpServerResponseMapper(
            JsonWriter<ErrorResponseTO> errorResponseJsonWriter) { //(1)!
        return (request, exception) -> {
            var details = exception.getViolations().stream()
                    .map(v -> "Path " + v.path() + " violated: " + v.message())
                    .toList();

            var response = new ErrorResponseTO(
                    "Encountered '%s' validation violations".formatted(details.size()),
                    JsonNullable.of(details)); //(2)!
            return HttpServerResponse.of(
                    400,
                    HttpBody.json(errorResponseJsonWriter.toByteArray(response)));
        };
    }
    ```

    1.  Писатель для сгенерированной модели тоже сгенерирован, поэтому его достаточно внедрить.
    2.  `details` объявлено `nullable` и не `required`, поэтому сгенерированное поле имеет тип `JsonNullable<List<String>>`.

    Импорты, нужные этому методу:

    ```java
    import io.koraframework.guide.openapi.httpserver.data.model.ErrorResponseTO;
    import io.koraframework.http.common.body.HttpBody;
    import io.koraframework.http.server.common.response.HttpServerResponse;
    import io.koraframework.json.common.JsonNullable;
    import io.koraframework.json.common.JsonWriter;
    import io.koraframework.validation.module.http.server.ViolationExceptionHttpServerResponseMapper;
    ```

=== ":simple-kotlin: `Kotlin`"

    Добавьте в `src/main/kotlin/io/koraframework/guide/openapi/httpserver/advanced/Application.kt`:

    ```kotlin
    fun customViolationExceptionHttpServerResponseMapper(
        errorResponseJsonWriter: JsonWriter<ErrorResponseTO> //(1)!
    ): ViolationExceptionHttpServerResponseMapper {
        return ViolationExceptionHttpServerResponseMapper { _, exception ->
            val details = exception.violations.map { violation ->
                "Path ${violation.path()} violated: ${violation.message()}"
            }

            val response = ErrorResponseTO(
                message = "Encountered '${details.size}' validation violations",
                details = JsonNullable.of(details) //(2)!
            )
            HttpServerResponse.of(400, HttpBody.json(errorResponseJsonWriter.toByteArray(response)))
        }
    }
    ```

    1.  Писатель для сгенерированной модели тоже сгенерирован, поэтому его достаточно внедрить.
    2.  `details` объявлено `nullable` и не `required`, поэтому сгенерированное свойство имеет тип `JsonNullable<List<String>>`.

    Импорты, нужные этому методу:

    ```kotlin
    import io.koraframework.guide.openapi.httpserver.data.model.ErrorResponseTO
    import io.koraframework.http.common.body.HttpBody
    import io.koraframework.http.server.common.response.HttpServerResponse
    import io.koraframework.json.common.JsonNullable
    import io.koraframework.json.common.JsonWriter
    import io.koraframework.validation.module.http.server.ViolationExceptionHttpServerResponseMapper
    ```

Именно поэтому у `ErrorResponseTO` в этом контракте два уровня:

- `message` для общего описания проблемы
- `details` для сообщений валидации на уровне параметров, когда они есть

И поскольку ограничение живет в схеме OpenAPI, сгенерированный транспортный слой отклоняет значения вне диапазона **до** того, как их увидит ваш делегат.

!!! tip "Полностью ручное отображение нарушений"

    Если вы предпочитаете обрабатывать `ViolationException` в собственном перехватчике или мапере ответа вместо стандартного, задайте `enableServerValidationInterceptor = "false"` в задаче генерации.
    Аннотации валидации останутся, но `@InterceptWith(ValidationHttpServerInterceptor.class)` не будет сгенерирован. В этом руководстве мы оставляем стандартный перехватчик и заменяем только используемый им маппер.

## Перехватчик ошибок { #error-interceptor }

Перехватчики сгенерированных серверных контроллеров подробнее описаны в разделе [OpenAPI Codegen: серверные перехватчики](../documentation/openapi-codegen.md#interceptors-2).

Ошибки валидации уже становятся структурированным JSON. Теперь добавим еще один слой для **остальных** видов сбоев, которые мы хотим нормализовать, включая тот самый `RestrictedFormNameException` из
делегата.

В ручном продвинутом руководстве по серверу мы использовали глобальный `ExceptionHandler`. Здесь мы намеренно поступаем точечнее: для сгенерированного контроллера **данных** мы подключаем перехватчик
конкретного контракта через конфигурацию генератора.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/io/koraframework/guide/openapi/httpserver/advanced/controller/DataApiExceptionHandler.java`:

    ```java
    package io.koraframework.guide.openapi.httpserver.advanced.controller;

    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.openapi.httpserver.data.model.ErrorResponseTO;
    import io.koraframework.http.common.body.HttpBody;
    import io.koraframework.http.server.common.interceptor.HttpServerInterceptor;
    import io.koraframework.http.server.common.request.HttpServerRequest;
    import io.koraframework.http.server.common.response.HttpServerResponse;
    import io.koraframework.http.server.common.response.HttpServerResponseException;
    import io.koraframework.json.common.JsonWriter;
    import io.koraframework.validation.common.ViolationException;

    @Component //(1)!
    public final class DataApiExceptionHandler implements HttpServerInterceptor {

        private final JsonWriter<ErrorResponseTO> errorJsonWriter;

        public DataApiExceptionHandler(JsonWriter<ErrorResponseTO> errorJsonWriter) {
            this.errorJsonWriter = errorJsonWriter;
        }

        @Override
        public HttpServerResponse intercept(HttpServerRequest request, InterceptChain chain) throws Exception { //(2)!
            try {
                return chain.process(request);
            } catch (ViolationException e) {
                throw e; //(3)!
            } catch (HttpServerResponseException e) {
                return jsonResponse(e.code(), e.getMessage());
            } catch (IllegalArgumentException e) {
                return jsonResponse(400, "Invalid request parameters");
            } catch (SecurityException e) {
                return jsonResponse(403, e.getMessage() != null ? e.getMessage() : "Access denied"); //(4)!
            } catch (Exception e) {
                return jsonResponse(500, "An unexpected error occurred");
            }
        }

        private HttpServerResponse jsonResponse(int statusCode, String message) {
            return HttpServerResponse.of(statusCode, HttpBody.json(this.errorJsonWriter.toByteArray(new ErrorResponseTO(message))));
        }
    }
    ```

    1.  Перехватчик, на который ссылается `extensions`, должен быть компонентом графа.
    2.  Перехватчики в Kora 2.0 синхронные: принимают запрос и цепочку и возвращают ответ. Параметра `Context` и `CompletionStage` больше нет.
    3.  Оставляем `ViolationExceptionHttpServerResponseMapper`, который уже отрисовывает нарушения.
    4.  Извлекатель API-ключа, добавляемый в следующем разделе, сигнализирует об отклоненном ключе через `SecurityException`.

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/io/koraframework/guide/openapi/httpserver/advanced/controller/DataApiExceptionHandler.kt`:

    ```kotlin
    package io.koraframework.guide.openapi.httpserver.advanced.controller

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.openapi.httpserver.data.model.ErrorResponseTO
    import io.koraframework.http.common.body.HttpBody
    import io.koraframework.http.server.common.interceptor.HttpServerInterceptor
    import io.koraframework.http.server.common.request.HttpServerRequest
    import io.koraframework.http.server.common.response.HttpServerResponse
    import io.koraframework.http.server.common.response.HttpServerResponseException
    import io.koraframework.json.common.JsonWriter
    import io.koraframework.validation.common.ViolationException

    @Component //(1)!
    class DataApiExceptionHandler(
        private val errorJsonWriter: JsonWriter<ErrorResponseTO>
    ) : HttpServerInterceptor {

        override fun intercept(request: HttpServerRequest, chain: HttpServerInterceptor.InterceptChain): HttpServerResponse { //(2)!
            try {
                return chain.process(request)
            } catch (e: ViolationException) {
                throw e //(3)!
            } catch (e: HttpServerResponseException) {
                return jsonResponse(e.code(), e.message ?: "HTTP error")
            } catch (e: IllegalArgumentException) {
                return jsonResponse(400, "Invalid request parameters")
            } catch (e: SecurityException) {
                return jsonResponse(403, e.message ?: "Access denied") //(4)!
            } catch (e: Exception) {
                return jsonResponse(500, "An unexpected error occurred")
            }
        }

        private fun jsonResponse(statusCode: Int, message: String): HttpServerResponse {
            return HttpServerResponse.of(
                statusCode,
                HttpBody.json(errorJsonWriter.toByteArray(ErrorResponseTO(message)))
            )
        }
    }
    ```

    1.  Перехватчик, на который ссылается `extensions`, должен быть компонентом графа.
    2.  Перехватчики в Kora 2.0 синхронные: принимают запрос и цепочку и возвращают ответ. Параметра `Context` и `CompletionStage` больше нет.
    3.  Оставляем `ViolationExceptionHttpServerResponseMapper`, который уже отрисовывает нарушения.
    4.  Извлекатель API-ключа, добавляемый в следующем разделе, сигнализирует об отклоненном ключе через `SecurityException`.

Ключевое отличие от ручного руководства — область действия:

- в [Продвинутом HTTP-сервере](http-server-advanced.md) перехватчик был глобальным
- здесь он подключен только к **сгенерированному API данных**

Это тонкий, но мощный прием. Сгенерированные транспорты вовсе не обязаны разделять одно и то же сквозное поведение; к разным сгенерированным контрактам можно применять разные стратегии перехватчиков.

Ветка `ViolationException` намеренная. Мы уже решили, что ошибки валидации принадлежат `customViolationExceptionHttpServerResponseMapper`, поэтому этот обработчик пробрасывает их нетронутыми и дает
`ValidationHttpServerInterceptor` сформировать ответ. Теперь обязанности разделены чисто:

- `ValidationHttpServerInterceptor` обрабатывает сгенерированные сбои валидации и возвращает `ErrorResponseTO(message, details)`
- `DataApiExceptionHandler` обрабатывает остальные транспортные сбои, которые мы хотим нормализовать

Только теперь имеет смысл подключить перехватчик в конфигурации генератора. В Kora 2.0 это делается опцией `extensions` — одним JSON-документом с тремя необязательными секциями: `*` для всего, `tags` с
ключами по именам тегов OpenAPI и `operations` с ключами по `operationId`.

===! ":fontawesome-brands-java: `Java`"

    Обновите `build.gradle`:

    ```groovy
    def openApiGenerateDataHttpServer = tasks.register("openApiGenerateDataHttpServer", GenerateTask) {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = layout.projectDirectory.file("src/main/resources/openapi/data-http-server.yaml")
        outputDir = layout.buildDirectory.dir("generated/data-http-server")
        def corePackage = "io.koraframework.guide.openapi.httpserver.data"
        apiPackage = "${corePackage}.api"
        modelPackage = "${corePackage}.model"
        invokerPackage = "${corePackage}.invoker"
        configOptions = [
                mode                  : "java-server",
                enableServerValidation: "true",
                extensions            : """
                        {
                          "*": {
                            "interceptorType": "io.koraframework.guide.openapi.httpserver.advanced.controller.DataApiExceptionHandler"
                          }
                        }
                        """, //(1)!
        ]
    }
    ```

    1.  Выпускает `@InterceptWith(DataApiExceptionHandler.class)` на каждой сгенерированной операции этого контракта. Некорректный JSON здесь роняет генерацию с сообщением, показывающим ожидаемую форму.

=== ":simple-kotlin: `Kotlin`"

    Обновите `build.gradle.kts`:

    ```kotlin
    val openApiGenerateDataHttpServer = tasks.register<GenerateTask>("openApiGenerateDataHttpServer") {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec.set(layout.projectDirectory.file("src/main/resources/openapi/data-http-server.yaml"))
        outputDir.set(layout.buildDirectory.dir("generated/data-http-server"))
        val corePackage = "io.koraframework.guide.openapi.httpserver.data"
        apiPackage = "${corePackage}.api"
        modelPackage = "${corePackage}.model"
        invokerPackage = "${corePackage}.invoker"
        configOptions = mapOf(
            "mode" to "kotlin-server",
            "enableServerValidation" to "true",
            "extensions" to """
                {
                  "*": {
                    "interceptorType": "io.koraframework.guide.openapi.httpserver.advanced.controller.DataApiExceptionHandler"
                  }
                }
            """.trimIndent(), //(1)!
        )
    }
    ```

    1.  Выпускает `@InterceptWith(DataApiExceptionHandler::class)` на каждой сгенерированной операции этого контракта. Некорректный JSON здесь роняет генерацию с сообщением, показывающим ожидаемую форму.

`extensions` умеет больше, чем перехватчики — она также добавляет дополнительные аннотации на сгенерированные методы, модели и перечисления. Если нужно лишь выбрать существующий компонент по тегу,
укажите `interceptorTag` вместо `interceptorType`, и будет использован базовый тип `HttpServerInterceptor` с этим тегом.

## Авторизация по ключу { #api-key }

Отображение схем безопасности OpenAPI на компоненты Kora описано в разделе [OpenAPI Codegen: авторизация](../documentation/openapi-codegen.md#authorization).

Контракт `data-http-server.yaml` уже объявляет требование безопасности один раз на верхнем уровне, а саму схему — в `components`:

```yaml
security:
  - apiKeyAuth: []

components:
  securitySchemes:
    apiKeyAuth:
      type: apiKey
      in: header
      name: Authorization
```

Поскольку требование глобальное, повторять его на каждой отдельной операции не нужно. Из этого генератор выпускает `ApiSecurity.ApiKeyAuth` — класс-маркер, определяющий, какой извлекатель относится к
какой схеме.

Теперь подключим поведение времени выполнения. Сначала контракт конфигурации для ожидаемого ключа:

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/io/koraframework/guide/openapi/httpserver/advanced/controller/DataApiAuthConfig.java`:

    ```java
    package io.koraframework.guide.openapi.httpserver.advanced.controller;

    import io.koraframework.config.common.annotation.ConfigSource;

    @ConfigSource("auth.apiKey")
    public interface DataApiAuthConfig {

        String value();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/io/koraframework/guide/openapi/httpserver/advanced/controller/DataApiAuthConfig.kt`:

    ```kotlin
    package io.koraframework.guide.openapi.httpserver.advanced.controller

    import io.koraframework.config.common.annotation.ConfigSource

    @ConfigSource("auth.apiKey")
    interface DataApiAuthConfig {
        fun value(): String
    }
    ```

Затем тип принципала, представляющий аутентифицированного вызывающего:

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/io/koraframework/guide/openapi/httpserver/advanced/controller/DataApiPrincipal.java`:

    ```java
    package io.koraframework.guide.openapi.httpserver.advanced.controller;

    import io.koraframework.common.Principal;

    public record DataApiPrincipal(String name) implements Principal {}
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/io/koraframework/guide/openapi/httpserver/advanced/controller/DataApiPrincipal.kt`:

    ```kotlin
    package io.koraframework.guide.openapi.httpserver.advanced.controller

    import io.koraframework.common.Principal

    data class DataApiPrincipal(val name: String) : Principal
    ```

И, наконец, сам извлекатель, помеченный сгенерированным маркером:

===! ":fontawesome-brands-java: `Java`"

    Добавьте в `src/main/java/io/koraframework/guide/openapi/httpserver/advanced/Application.java`:

    ```java
    @Tag(ApiSecurity.ApiKeyAuth.class) //(1)!
    default HttpServerPrincipalExtractor<String, Principal> apiKeyHttpServerPrincipalExtractor(DataApiAuthConfig config) { //(2)!
        return (request, value) -> {
            if (value == null || !config.value().equals(value)) {
                throw new SecurityException("Invalid API key"); //(3)!
            }
            return new DataApiPrincipal("data-api-client"); //(4)!
        };
    }
    ```

    1.  Привязывает этот извлекатель к схеме `apiKeyAuth` из контракта.
    2.  `T` — учетные данные, которые сгенерированный контроллер достает из запроса; `P` — принципал, который вы из них строите.
    3.  Отклонение через исключение — это то, что `DataApiExceptionHandler` превращает в `403` из контракта.
    4.  Возвращенные принципалы публикуются на весь запрос и доступны где угодно через `Principal.current()`.

    Импорты, нужные этому методу:

    ```java
    import io.koraframework.common.Principal;
    import io.koraframework.common.annotation.Tag;
    import io.koraframework.guide.openapi.httpserver.advanced.controller.DataApiAuthConfig;
    import io.koraframework.guide.openapi.httpserver.advanced.controller.DataApiPrincipal;
    import io.koraframework.guide.openapi.httpserver.data.api.ApiSecurity;
    import io.koraframework.http.server.common.auth.HttpServerPrincipalExtractor;
    ```

=== ":simple-kotlin: `Kotlin`"

    Добавьте в `src/main/kotlin/io/koraframework/guide/openapi/httpserver/advanced/Application.kt`:

    ```kotlin
    @Tag(ApiSecurity.ApiKeyAuth::class) //(1)!
    fun apiKeyHttpServerPrincipalExtractor(config: DataApiAuthConfig): HttpServerPrincipalExtractor<String, Principal> { //(2)!
        return HttpServerPrincipalExtractor { _, value ->
            if (value == null || config.value() != value) {
                throw SecurityException("Invalid API key") //(3)!
            }
            DataApiPrincipal("data-api-client") //(4)!
        }
    }
    ```

    1.  Привязывает этот извлекатель к схеме `apiKeyAuth` из контракта.
    2.  `T` — учетные данные, которые сгенерированный контроллер достает из запроса; `P` — принципал, который вы из них строите.
    3.  Отклонение через исключение — это то, что `DataApiExceptionHandler` превращает в `403` из контракта.
    4.  Возвращенные принципалы публикуются на весь запрос и доступны где угодно через `Principal.current()`.

    Импорты, нужные этому методу:

    ```kotlin
    import io.koraframework.common.Principal
    import io.koraframework.common.annotation.Tag
    import io.koraframework.guide.openapi.httpserver.advanced.controller.DataApiAuthConfig
    import io.koraframework.guide.openapi.httpserver.advanced.controller.DataApiPrincipal
    import io.koraframework.guide.openapi.httpserver.data.api.ApiSecurity
    import io.koraframework.http.server.common.auth.HttpServerPrincipalExtractor
    ```

Это один из самых красивых контрактных приемов в руководстве.

Файл OpenAPI говорит: эта группа маршрутов требует авторизации по API-ключу. Генератор говорит: вот абстракция безопасности для этого требования. Ваше приложение говорит: вот как этот API-ключ реально
проверяется во время выполнения.

Это очень чистое разделение между контрактом, сгенерированной точкой интеграции и политикой времени выполнения.

!!! note "Отклонение через `null` против исключения"

    У извлекателя есть два способа отказать в учетных данных. Возврат `null` отклоняет только **это** требование безопасности, поэтому сгенерированный перехватчик переходит к следующей альтернативе, разрешенной контрактом, и отвечает `401 Unauthorized`, когда все альтернативы исчерпаны.
    Исключение, как выше, завершает запрос немедленно — что нам здесь и нужно, потому что схема одна и мы хотим свое тело `403`.

## Варианты авторизации { #authorization-options }

Пример в этом руководстве использует самый простой вариант: один API-ключ, одно глобальное требование безопасности, один `HttpServerPrincipalExtractor`.

Это отличная отправная точка. Но безопасность OpenAPI может моделировать несколько разных форм, и полезно понимать их различия, прежде чем выбирать одну для реального сервиса.

Этот раздел намеренно теоретический. Он не меняет запускаемое приложение из руководства. Вместо этого он показывает распространенные схемы, которые можно описать в OpenAPI и затем подключить к
извлекателям Kora.

### 1. Глобальный API-ключ { #1-global-api-key }

Это схема, которую мы используем в руководстве. Она хорошо работает, когда:

- все API относится к одной защищенной интеграционной поверхности
- каждый маршрут должен требовать один и тот же секрет
- вам нужен минимум обвязки безопасности

```yaml
security:
  - apiKeyAuth: []

components:
  securitySchemes:
    apiKeyAuth:
      type: apiKey
      in: header
      name: Authorization
```

Серверная безопасность поддерживает схемы `apiKey`, читаемые из заголовка, query-параметра или cookie, поэтому одна и та же обвязка покрывает все три размещения.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(ApiSecurity.ApiKeyAuth.class)
    default HttpServerPrincipalExtractor<String, Principal> apiKeyHttpServerPrincipalExtractor(MyAuthConfig config) {
        return (request, value) -> {
            if (value == null || !config.value().equals(value)) {
                throw new SecurityException("Invalid API key");
            }
            return new MyPrincipal("integration-client");
        };
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(ApiSecurity.ApiKeyAuth::class)
    fun apiKeyHttpServerPrincipalExtractor(config: MyAuthConfig): HttpServerPrincipalExtractor<String, Principal> {
        return HttpServerPrincipalExtractor { _, value ->
            if (value == null || config.value() != value) {
                throw SecurityException("Invalid API key")
            }
            MyPrincipal("integration-client")
        }
    }
    ```

Такой подход прост и практичен для внутренних вызовов между сервисами, административных конечных точек за инфраструктурными ограничениями и технических API, которыми пользуется небольшое число
доверенных клиентов.

### 2. Защита маршрутов { #2-route-protection }

Иногда не все маршруты должны защищаться одинаково: публичные конечные точки здоровья или входа могут оставаться открытыми, а один раздел API может использовать другую схему.

В этом случае опустите глобальный `security` и опишите его прямо на операциях:

```yaml
paths:
  /public/ping:
    get:
      security: []
      responses:
        '200':
          description: OK
  /users:
    get:
      security:
        - apiKeyAuth: []
      responses:
        '200':
          description: Protected
```

Это полезно, когда поверхность API смешанная: часть публичная, часть защищенная, часть защищена другими схемами.

### 3. Basic Authentication { #3-basic-authentication }

Basic-аутентификация — еще один распространенный вариант. Схемы `http` с `basic` или `bearer` читаются из заголовка `Authorization`:

```yaml
components:
  securitySchemes:
    basicAuth:
      type: http
      scheme: basic

security:
  - basicAuth: []
```

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(ApiSecurity.BasicAuth.class)
    default HttpServerPrincipalExtractor<String, Principal> basicHttpServerPrincipalExtractor() {
        return (request, credentials) -> {
            if (credentials == null) {
                throw new SecurityException("Missing credentials");
            }
            var parts = credentials.split(":", 2);
            if (parts.length != 2) {
                throw new SecurityException("Invalid basic auth format");
            }
            return new MyPrincipal(parts[0]);
        };
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(ApiSecurity.BasicAuth::class)
    fun basicHttpServerPrincipalExtractor(): HttpServerPrincipalExtractor<String, Principal> {
        return HttpServerPrincipalExtractor { _, credentials ->
            if (credentials == null) {
                throw SecurityException("Missing credentials")
            }
            val parts = credentials.split(":", limit = 2)
            if (parts.size != 2) {
                throw SecurityException("Invalid basic auth format")
            }
            MyPrincipal(parts[0])
        }
    }
    ```

Basic-аутентификация может быть приемлема для простых внутренних инструментов, демонстраций и legacy-интеграций. Использовать ее обычно стоит только поверх HTTPS, а во многих современных системах
Bearer/JWT — более гибкий выбор.

### 4. Bearer-токены и JWT { #4-bearer-tokens-jwt }

Если ваше API предназначено для браузеров, мобильных клиентов или пользовательских сессий, Bearer часто подходит лучше API-ключей.

```yaml
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

security:
  - bearerAuth: []
```

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(ApiSecurity.BearerAuth.class)
    default HttpServerPrincipalExtractor<String, Principal> bearerHttpServerPrincipalExtractor(JwtService jwtService) {
        return (request, token) -> {
            if (token == null || token.isBlank()) {
                throw new SecurityException("Missing bearer token");
            }
            return new UserPrincipal(jwtService.extractUserFromToken(token));
        };
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(ApiSecurity.BearerAuth::class)
    fun bearerHttpServerPrincipalExtractor(jwtService: JwtService): HttpServerPrincipalExtractor<String, Principal> {
        return HttpServerPrincipalExtractor { _, token ->
            if (token.isNullOrBlank()) {
                throw SecurityException("Missing bearer token")
            }
            UserPrincipal(jwtService.extractUserFromToken(token))
        }
    }
    ```

Это хорошо работает, когда вызывающий — конечный пользователь, когда нужен срок жизни токена и когда внутри токена важны claims, роли или информация о тенанте.

Схема `oauth2` или `openId` подключается так же, но ее операции объявляют **скоупы**. Для них принципал должен реализовывать `PrincipalWithScopes`, чтобы сгенерированный перехватчик мог сравнить
выданные скоупы с требуемыми операцией.

### 5. Несколько схем { #5-multiple-schemes }

OpenAPI умеет описывать случаи, когда маршрут принимает одну схему **или** другую. Это записывается как несколько объектов внутри массива `security`:

```yaml
security:
  - apiKeyAuth: []
  - basicAuth: []
```

Это значит, что вызывающий может аутентифицироваться через `apiKeyAuth` **или** через `basicAuth` — полезно в периоды миграции и для смешанных клиентов, когда машинные клиенты используют API-ключи, а
операторские инструменты — basic-аутентификацию.

На стороне Kora вы предоставляете извлекатели для обоих сгенерированных маркеров. Сгенерированный перехватчик перебирает альтернативы по очереди; извлекатель, вернувший `null`, отклоняет свое
требование, и пробуется следующее, и только когда все они отказали, запрос завершается с `401 Unauthorized`.

### 6. Комбинированные схемы { #6-combined-schemes }

OpenAPI также поддерживает комбинированные требования. Внутри одного объекта безопасности несколько схем трактуются **совместно**:

```yaml
security:
  - apiKeyAuth: []
    bearerAuth: []
```

Это не два извлекателя. Генератор выпускает **один** извлекатель для комбинации: его тип учетных данных — сгенерированная запись, содержащая по одной `String` на схему, а его тег объединяет имена схем
через `With`. Для схем `apiKeyAuth` и `bearerAuth` это `@Tag(ApiSecurity.ApiKeyAuthWithBearerAuth.class)` с типом учетных данных `ApiSecurity.ApiKeyAuthWithBearerAuthAuthData`.

На практике этот стиль реже встречается в простых API, но он оправдан, когда один токен идентифицирует пользователя, а другой секрет — вызывающее приложение.

### 7. Публичные маршруты { #7-public-routes }

Один тонкий, но важный прием OpenAPI — пустой список требований на конкретной операции:

```yaml
security: []
```

Он переопределяет глобальное требование безопасности и делает эту конечную точку публичной. Указание пустого объекта среди альтернатив — `security: [{}]` — дает похожий эффект: запрос пропускается без
аутентификации, если ни одна другая альтернатива не подошла.

Это особенно полезно, когда API в основном защищено, но несколько маршрутов должны оставаться открытыми, например `/auth/login`, `/auth/refresh` или `/public/ping`.

### 8. Выбор авторизации { #8-choosing-authorization }

Простое эмпирическое правило:

- Используйте глобальную защиту API-ключом для внутренних интеграционных API.
- Используйте безопасность на уровне маршрута, когда API смешивает публичные и защищенные конечные точки.
- Используйте basic-аутентификацию только для простых или legacy-сценариев.
- Используйте Bearer/JWT, когда важны пользователи, сессии, роли или claims.
- Используйте несколько альтернативных схем, когда нужен путь миграции или разные типы клиентов.
- Используйте комбинированные схемы, только когда многослойная аутентификация действительно нужна.

### 9. Поддержка в Kora { #9-kora-support }

Какую бы схему вы ни выбрали, контрактный процесс остается очень похожим:

1. описать схему в `components.securitySchemes`
2. подключить ее глобально или на маршрут через `security`
3. перегенерировать сервер
4. реализовать `HttpServerPrincipalExtractor<T, P>` с тегом сгенерированного маркера `ApiSecurity.*`
5. при необходимости нормализовать сбои авторизации через свой слой обработки исключений

Любой тип схемы, кроме `apiKey`, `http` `basic`/`bearer`, `oauth2` и `openId`, роняет генерацию с явным сообщением, а не выпускает молча незащищенные маршруты.

Главный вывод: OpenAPI описывает контракт безопасности, а Kora дает сгенерированную точку интеграции, чтобы применить его во время выполнения.

## Конфигурация { #configuration }

Теперь настроим приложение так, чтобы оно публиковало оба файла OpenAPI и знало значение ключа.

Обновите `src/main/resources/application.conf`:

Полное описание конфигурации смотрите в [HTTP-сервер](../documentation/http-server.md#configuration), [Конфигурация](../documentation/config.md), [OpenAPI Management](../documentation/openapi-management.md#configuration)
и [Логирование SLF4J](../documentation/logging-slf4j.md).

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
      port = 8080 //(1)!
      system.port = 8085 //(2)!
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
        enabled = true //(6)!
        files = [ "openapi/user-http-server.yaml", "openapi/data-http-server.yaml" ] //(7)!
        path = "/openapi" //(8)!
        swaggerui {
          enabled = true //(9)!
          path = "/swagger-ui" //(10)!
        }
      }
    }

    logging.levels {
      "root" = "WARN" //(11)!
      "io.koraframework" = "INFO" //(12)!
      "io.koraframework.guide.openapi.httpserver.advanced" = "INFO" //(13)!
    }
    ```

    1.  Публичный HTTP-порт для конечных точек приложения (по умолчанию: `8080`).
    2.  Системный HTTP-порт для проб, метрик и служебных конечных точек (по умолчанию: `8085`).
    3.  Включает логирование запросов публичного HTTP-сервера (по умолчанию: `false`).
    4.  API-ключ, который ожидает `DataApiAuthConfig`, читается из `auth.apiKey.value`.
    5.  Необязательное переопределение из переменной окружения `OPENAPI_HTTP_SERVER_ADVANCED_API_KEY` — так секрет прокидывают в реальном развертывании.
    6.  Включает публикацию OpenAPI (по умолчанию: `false`).
    7.  Оба контракта публикуются из одного приложения.
    8.  Базовый путь для контрактов. При нескольких файлах он становится префиксом, см. замечание ниже.
    9.  Включает страницу Swagger UI (по умолчанию: `false`).
    10. Путь страницы Swagger UI (по умолчанию: `/swagger-ui`).
    11. Уровень логирования корневого логгера.
    12. Уровень логирования логгеров фреймворка Kora.
    13. Уровень логирования пакета приложения.

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      port: 8080 #(1)!
      system:
        port: 8085 #(2)!
      telemetry:
        logging:
          enabled: true #(3)!
    auth:
      apiKey:
        value: "MySecuredApiKey" #(4)!
    openapi:
      management:
        enabled: true #(5)!
        files: [ "openapi/user-http-server.yaml", "openapi/data-http-server.yaml" ] #(6)!
        path: "/openapi" #(7)!
        swaggerui:
          enabled: true #(8)!
          path: "/swagger-ui" #(9)!
    logging:
      levels:
        root: "WARN" #(10)!
        "io.koraframework": "INFO" #(11)!
        "io.koraframework.guide.openapi.httpserver.advanced": "INFO" #(12)!
    ```

    1.  Публичный HTTP-порт для конечных точек приложения (по умолчанию: `8080`).
    2.  Системный HTTP-порт для проб, метрик и служебных конечных точек (по умолчанию: `8085`).
    3.  Включает логирование запросов публичного HTTP-сервера (по умолчанию: `false`).
    4.  API-ключ, который ожидает `DataApiAuthConfig`, читается из `auth.apiKey.value`.
    5.  Включает публикацию OpenAPI (по умолчанию: `false`).
    6.  Оба контракта публикуются из одного приложения.
    7.  Базовый путь для контрактов. При нескольких файлах он становится префиксом, см. замечание ниже.
    8.  Включает страницу Swagger UI (по умолчанию: `false`).
    9.  Путь страницы Swagger UI (по умолчанию: `/swagger-ui`).
    10. Уровень логирования корневого логгера.
    11. Уровень логирования логгеров фреймворка Kora.
    12. Уровень логирования пакета приложения.

!!! warning "При нескольких файлах `/openapi` становится префиксом"

    Когда в `files` ровно одна запись, контракт отдается прямо по `openapi.management.path`.
    Как только записей больше одной, зарегистрированный маршрут становится `path + "/{file}"`, где `{file}` — **имя файла** ресурса, поэтому два контракта выше читаются по
    `GET /openapi/user-http-server.yaml` и `GET /openapi/data-http-server.yaml`, а голый `GET /openapi` больше не совпадает.
    Страница Swagger UI справляется с этим сама и предлагает оба контракта в своем селекторе.

Так все приложение становится цельным: один рантайм, два контракта, одна общая публикация OpenAPI, один Swagger UI.

Именно так часто и растет реальный сервис. Разные области HTTP могут писаться по-разному или генерироваться с разными опциями, но поставляются они как одно приложение.

## Проверка приложения { #check-app }

```bash
./gradlew clean classes
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

Попробуйте конечную точку отображения JSON:

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

Попробуйте сбой валидации:

```bash
curl -X GET http://localhost:8080/data/mapping-by-code/700 \
  -H "Authorization: MySecuredApiKey"
```

Ожидаемый результат: `400` с `message` и `details`, сформированный собственным маппером нарушений еще до вызова делегата, потому что `700` выходит за допустимый диапазон `200..599`.

Попробуйте путь перехватчика:

```bash
curl -X POST http://localhost:8080/data/form \
  -H "Authorization: MySecuredApiKey" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "name=admin"
```

Ожидаемый результат: `500` с телом `ErrorResponseTO`, потому что `RestrictedFormNameException` доходит до `DataApiExceptionHandler`.

Попробуйте запрос без авторизации:

```bash
curl -X POST http://localhost:8080/data/form \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "name=Ivan"
```

Ожидаемый результат: `403` с телом `ErrorResponseTO`.

Прочитайте контракты:

```bash
curl http://localhost:8080/openapi/user-http-server.yaml
curl http://localhost:8080/openapi/data-http-server.yaml
```

Откройте:

```text
http://localhost:8080/swagger-ui
```

и убедитесь, что в общей документации видны и маршруты пользователей, и маршруты данных.

## Тестирование { #testing }

Поскольку сгенерированные делегаты — обычные компоненты, продвинутые маршруты тестируются ровно так же, как CRUD-овские, включая запись формы, которую вы конструируете напрямую, а не собираете
multipart-запрос.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/test/java/io/koraframework/guide/openapi/httpserver/advanced/OpenApiHttpServerAdvancedAppTest.java`:

    ```java
    package io.koraframework.guide.openapi.httpserver.advanced;

    import static org.junit.jupiter.api.Assertions.assertEquals;
    import static org.junit.jupiter.api.Assertions.assertInstanceOf;

    import org.junit.jupiter.api.Test;
    import io.koraframework.guide.openapi.httpserver.data.api.DataApiController;
    import io.koraframework.guide.openapi.httpserver.data.api.DataApiDelegate;
    import io.koraframework.guide.openapi.httpserver.data.api.DataApiResponses;
    import io.koraframework.test.extension.junit5.KoraAppTest;
    import io.koraframework.test.extension.junit5.TestComponent;

    @KoraAppTest(Application.class)
    class OpenApiHttpServerAdvancedAppTest {

        @TestComponent
        private DataApiDelegate dataApiDelegate;

        @Test
        void dataFormFlowWorksThroughGeneratedDelegate() throws Exception {
            var response = this.dataApiDelegate.processForm(new DataApiController.ProcessFormFormParam("Ivan")); //(1)!
            var form200 = assertInstanceOf(DataApiResponses.ProcessFormApiResponse.ProcessForm200ApiResponse.class, response);
            assertEquals("Hello World, Ivan", form200.content());
        }

        @Test
        void dataMappingByCodeReturnsPayloadFor200() throws Exception {
            var response = this.dataApiDelegate.mappingByCode(200);
            var mapping200 = assertInstanceOf(DataApiResponses.MappingByCodeApiResponse.MappingByCode200ApiResponse.class, response);
            assertEquals("Hello from response mapper", mapping200.content().message());
        }
    }
    ```

    1.  Сгенерированная запись формы — обычная запись, поэтому тест полностью обходится без multipart-кодирования.

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/test/kotlin/io/koraframework/guide/openapi/httpserver/advanced/OpenApiHttpServerAdvancedAppTest.kt`:

    ```kotlin
    package io.koraframework.guide.openapi.httpserver.advanced

    import org.junit.jupiter.api.Assertions.assertEquals
    import org.junit.jupiter.api.Assertions.assertInstanceOf
    import org.junit.jupiter.api.Test
    import io.koraframework.guide.openapi.httpserver.data.api.DataApiController
    import io.koraframework.guide.openapi.httpserver.data.api.DataApiDelegate
    import io.koraframework.guide.openapi.httpserver.data.api.DataApiResponses
    import io.koraframework.test.extension.junit5.KoraAppTest
    import io.koraframework.test.extension.junit5.TestComponent

    @KoraAppTest(Application::class)
    class OpenApiHttpServerAdvancedAppTest {

        @TestComponent
        lateinit var dataApiDelegate: DataApiDelegate

        @Test
        fun dataFormFlowWorksThroughGeneratedDelegate() {
            val response = dataApiDelegate.processForm(DataApiController.ProcessFormFormParam("Ivan")) //(1)!
            val form200 =
                assertInstanceOf(DataApiResponses.ProcessFormApiResponse.ProcessForm200ApiResponse::class.java, response)
            assertEquals("Hello World, Ivan", form200.content)
        }

        @Test
        fun dataMappingByCodeReturnsPayloadFor200() {
            val response = dataApiDelegate.mappingByCode(200)
            val mapping200 = assertInstanceOf(
                DataApiResponses.MappingByCodeApiResponse.MappingByCode200ApiResponse::class.java,
                response
            )
            assertEquals("Hello from response mapper", mapping200.content.message)
        }
    }
    ```

    1.  Сгенерированная запись формы — обычный data class, поэтому тест полностью обходится без multipart-кодирования.

Выполните:

```bash
./gradlew test
```

Обратите внимание, чего тест делегата **не** покрывает: валидация, перехватчик и проверка безопасности живут в сгенерированном контроллере и его цепочке перехватчиков, поэтому они срабатывают только на
настоящем HTTP. Для проверок этого используйте команды `curl` выше или [black-box тест](testing-black-box.md).

## Лучшие практики { #best-practices }

- Не меняйте существующий сгенерированный контракт, добавляя второй, более продвинутый.
- Разделяйте контракты, когда группам конечных точек нужны разные возможности генерации, и давайте каждой задаче собственные `apiPackage` и `modelPackage`.
- Считайте `securitySchemes` OpenAPI источником истины для требований авторизации.
- Используйте перехватчики конкретного сгенерированного контракта, когда особая обработка ошибок нужна только одной сгенерированной области.
- Держите отображение ошибок валидации в `ViolationExceptionHttpServerResponseMapper`, а все остальное — в своем перехватчике, чтобы они не боролись за одно и то же исключение.
- Держите реализации делегатов маленькими и сосредоточенными на прикладном поведении, а не на транспортной обвязке.
- Оставляйте `@Json` на любом написанном вручную DTO-классе, который сериализуется в JSON; сгенерированные модели OpenAPI `*TO` уже идут со своими мапперами, а ваши собственные DTO — нет.

## Итоги { #summary }

Вы расширили контрактный HTTP-сервер из [Контрактного HTTP-сервера с OpenAPI](openapi-http-server.md) вторым сгенерированным API для продвинутых HTTP-задач:

- `user-http-server.yaml` остался без изменений для CRUD пользователей
- `data-http-server.yaml` добавил конечные точки формы, multipart и отображения ответов
- только задача генерации данных получила перехватчик контроллера через `extensions`
- ошибки валидации были приведены к собственной модели `ErrorResponseTO` контракта
- авторизация по API-ключу управляется контрактом безопасности OpenAPI
- оба контракта опубликованы вместе через OpenAPI management

Теперь приложение показывает более реалистичный путь развития контрактного подхода: стабильные сгенерированные API остаются нетронутыми, а новые сгенерированные поверхности с более специализированным
поведением добавляются только там, где это нужно.

## Ключевые понятия { #key-concepts }

- одно приложение может содержать несколько сгенерированных серверных контрактов OpenAPI
- разные задачи генератора могут использовать разные опции
- `extensions` — единственная опция генератора для подключения перехватчиков и дополнительных аннотаций к сгенерированному коду
- тела формы и multipart становятся сгенерированными записями `<Api>Controller.<Operation>FormParam`, а не JSON-моделями
- поле схемы, объявленное `nullable` и не `required`, становится полем `JsonNullable`
- `securitySchemes` OpenAPI отображаются на маркеры `ApiSecurity` и компоненты `HttpServerPrincipalExtractor`
- валидацию по спецификации можно включать по контрактам, а форму ее ошибок определяете вы
- делегаты остаются главным местом отображения транспорта на приложение

## Устранение неполадок { #troubleshooting }

**Конечные точки данных отсутствуют в графе:**

Проверьте, что:

- задача `openApiGenerateDataHttpServer` зарегистрирована
- ее `outputDir` добавлен в основной source set
- компиляция (`compileJava`, а в `Kotlin` — каждая задача `ksp*`) зависит от этой задачи
- `DataApiDelegateImpl` размечен аннотацией `@Component`

**Генерация падает с «Invalid OpenAPI generator option `extensions`»:**

- Значение должно быть корректным JSON с необязательными секциями `*`, `tags` и `operations`. Сообщение об ошибке показывает ожидаемую форму и переданное значение.
- Старая опция v1 `interceptors` больше не существует. Неизвестный ключ `configOptions` не отвергается — он просто игнорируется, поэтому устаревший блок `interceptors` оставит контроллер вообще без перехватчика и не даст никакой ошибки сборки.

**Авторизация по API-ключу не работает:**

Проверьте, что:

- в `data-http-server.yaml` есть `components.securitySchemes.apiKeyAuth`
- контракт объявляет `security: - apiKeyAuth: []` глобально или на маршруте
- извлекатель принципала помечен маркером, названным по схеме, — `@Tag(ApiSecurity.ApiKeyAuth.class)`; тег берется из имени схемы в контракте, а не из порядкового номера
- настроенное значение совпадает с заголовком `Authorization`

**Валидация не срабатывает:**

Проверьте, что:

- `enableServerValidation = "true"` задан в задаче генерации **данных**
- ограничение действительно присутствует в схеме OpenAPI для `/data/mapping-by-code/{code}`
- вы проверяете значение вне допустимого диапазона `200..599`
- в `Application` подключен `ValidationModule`, иначе граф не сможет собрать перехватчик валидации

**Ошибки валидации приходят простым текстом:**

- Стандартный `ValidationHttpServerInterceptor` отвечает простым `400`, когда компонента `ViolationExceptionHttpServerResponseMapper` нет. Зарегистрируйте маппер, показанный выше.

**Ответы об ошибках не в JSON:**

Проверьте, что:

- задача генератора содержит конфигурацию `extensions` с `interceptorType`
- она указывает на полное имя `DataApiExceptionHandler`
- `DataApiExceptionHandler` размечен аннотацией `@Component`
- `ErrorResponseTO` объявлен в `data-http-server.yaml`

**Swagger UI показывает только один контракт:**

Проверьте `openapi.management.files` в `application.conf`. Это должен быть список, содержащий и `openapi/user-http-server.yaml`, и `openapi/data-http-server.yaml`, а ключ называется `files` — ключ v1 в
единственном числе `file` не читается вовсе.

**`GET /openapi` возвращает 404:**

Это ожидаемо, когда в `files` больше одного файла: маршрут становится `/openapi/{file}`. Запрашивайте `/openapi/data-http-server.yaml`.

## Что дальше? { #whats-next }

- [HTTP-клиент](http-client.md), если вы еще не собирали клиентское приложение.
- [OpenAPI HTTP-клиент](openapi-http-client.md) после HTTP-клиента, чтобы потреблять сгенерированные по контракту API с типизированными обертками ответов.
- [Продвинутый HTTP-клиент](http-client-advanced.md) после HTTP-клиента, чтобы сравнить сгенерированные клиенты с написанными вручную продвинутыми.
- [Наблюдаемость](observability.md), чтобы следить за сгенерированными контроллерами, сбоями валидации, проверками безопасности и перехватчиками.
- [Устойчивые паттерны](resilient.md), чтобы защитить клиентов, вызывающих эти сгенерированные конечные точки.

## Помощь { #help }

Если что-то не получается:

- сравните с [Kora Java OpenAPI HTTP Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-openapi-http-server-advanced-app) и [Kora Kotlin OpenAPI HTTP Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-openapi-http-server-advanced-app)
- перечитайте [OpenAPI HTTP-сервер](openapi-http-server.md) про базовую модель сгенерированного делегата
- перечитайте [Продвинутый HTTP-сервер](http-server-advanced.md) про ручную версию похожих возможностей HTTP
- посмотрите [документацию OpenAPI Codegen](../documentation/openapi-codegen.md)
- посмотрите [документацию OpenAPI Management](../documentation/openapi-management.md)
