---
search:
  exclude: true
title: Контрактный HTTP-клиент с OpenAPI
summary: Continue the HTTP Client guide by replacing the handwritten declarative client with an OpenAPI-generated client
tags: openapi, http-client, contract-first, code-generation, swagger
---

# Контрактный HTTP-клиент с OpenAPI { #contract-first-http-client }

Это руководство знакомит с контрактными HTTP-клиентами в Kora и OpenAPI. В нем разбирается, как спецификация OpenAPI генерирует типизированный клиент, как сгенерированные модели запросов и ответов
заменяют рукописные транспортные интерфейсы и как клиент подключается к сервису приложения Kora. Вы также увидите, как один контракт API может описывать обе стороны HTTP-интеграции без ручного
дублирования сигнатур методов.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java OpenAPI HTTP Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-openapi-http-client-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin OpenAPI HTTP Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-openapi-http-client-app).

## Что вы создадите { #youll-build }

Вы пересоберете клиентское приложение из [HTTP-клиент с Kora](http-client.md), но в контрактном стиле:

- удаленный API пользователей будет описан тем же контрактом `user-http-server.yaml` из [openapi-http-server.md](openapi-http-server.md)
- Kora сгенерирует типизированный клиентский интерфейс из этого контракта
- сгенерированные модели запросов и ответов заменят рукописные DTO клиента
- клиентское приложение по-прежнему откроет одну агрегирующую конечную точку для удобной ручной проверки
- тесты будут запускать сгенерированный клиент против контейнеризованной копии OpenAPI-серверного приложения

## Что вам понадобится { #youll-need }

- JDK 17 или новее
- Gradle 7+
- Docker Desktop или другое локальное Docker-окружение для контейнерных тестов
- текстовый редактор или среда разработки
- два терминала, если вы хотите запускать сервер и клиент вручную

## Требования { #prerequisites }

!!! note "Обязательно: пройдите руководство по OpenAPI HTTP-серверу"

    Это руководство предполагает, что вы прошли **[HTTP-клиент с Kora](http-client.md)** и **[Контрактный HTTP-сервер с OpenAPI](openapi-http-server.md)**.

    Если вы еще не прошли эти руководства, сначала сделайте это, потому что они уже объясняют базовый поток HTTP-клиента и серверный контракт OpenAPI, который переиспользует этот сгенерированный клиент.

## Обзор { #overview }

В базовом руководстве по HTTP-клиенту рабочий процесс выглядел так:

1. вручную определить `UserApiClient`
2. добавить аннотации, которые описывают удаленный контракт
3. позволить Kora сгенерировать реализацию из этого интерфейса
4. внедрить клиент и вызвать сервер

Это уже очень продуктивная модель. Но когда сам сервер становится контрактным, появляется более правильный следующий шаг:

1. оставить контракт OpenAPI источником истины
2. сгенерировать сервер из этого контракта
3. сгенерировать клиент из того же контракта
4. позволить обоим приложениям развиваться из одного общего описания

В этом руководстве мы постепенно пройдем этот переход:

1. поймем, зачем полезен сгенерированный клиент, когда у вас уже есть сгенерированный сервер
2. подключим тот же контракт `user-http-server.yaml` к клиентскому процессу
3. настроим генерацию OpenAPI-клиента Kora
4. изучим сгенерированный интерфейс `UsersApi` и сгенерированные модели
5. заменим рукописный клиент сгенерированным
6. сохраним тот же агрегирующий поток проверки из `http-client.md`
7. настроим сгенерированный клиент
8. запустим и проверим приложение
9. протестируем сгенерированный клиент против приложения OpenAPI-сервера

### Контрактная разработка? { #contract-first-development }

Прежде чем что-либо генерировать, полезно понять, почему команды вообще выбирают этот рабочий процесс.

В традиционном подходе «сначала код» разработчики обычно начинают с контроллеров, конечных точек или клиентских интерфейсов, написанных прямо в коде, и только потом пытаются задокументировать API. Для
небольших систем это может работать, но со временем создает настоящее трение между командами и между приложениями.

#### Проблема API, построенных от кода { #problem-code-first-apis }

Когда контракт не является главным источником истины, появляются несколько проблем:

- **Расхождение документации**: документация API устаревает по мере развития кода
- **Несовпадения контракта**: команды клиента и сервера строят код на слегка разных представлениях об одном API
- **Поздняя проверка**: проблемы проектирования обнаруживаются только во время интеграционного тестирования или после развертывания
- **Ручное сопровождение**: документацию, клиентскую библиотеку, примеры и тесты нужно обновлять отдельно
- **Пробелы в общении**: команды тратят время на уточнение поведения в чатах, встречах и задачах вместо того, чтобы опираться на один общий контракт

Для клиентского приложения это особенно болезненно. Рукописный клиент может по-прежнему компилироваться, хотя удаленный API уже изменился незаметным, но ломающим образом.

#### Контрактное решение { #contract-first-solution }

Контрактная разработка переворачивает этот процесс.

Вместо того чтобы говорить «код определяет API», мы говорим «контракт определяет код». Спецификация OpenAPI становится единым источником истины, которому должны следовать и сервер, и клиент.

Это означает:

- сервер генерируется из контракта или проверяется по нему
- клиент генерируется из того же контракта
- документация также выводится из того же контракта

Поэтому вместо сопровождения нескольких параллельных описаний API вы сопровождаете один общий контракт и позволяете инструментам выполнять повторяющуюся работу по синхронизации.

#### Изменение работы команды { #team-workflow-changes }

Контрактная разработка — это не только прием сборки. Она меняет способ совместной работы команд.

1. **Проектирование до реализации**
   Проектирование API сначала происходит на уровне спецификации, поэтому форму API можно проверить до появления производственного кода.
   Так проще проверить пути, полезные нагрузки, статусы и именование, пока цена изменения еще низкая.

2. **Автоматическая согласованность**
   Когда и сервер, и клиент генерируются из одной спецификации, вероятность расхождения на транспортном уровне резко снижается.
   Вам не нужно вручную синхронизировать определения маршрутов, поля DTO и ожидаемые ответы в двух разных кодовых базах.

3. **Лучшее сотрудничество между ролями**
   Серверные разработчики, фронтенд-разработчики, QA и продуктовые участники могут рассуждать об одном и том же контракте.
   Файл OpenAPI становится общим языком, а не деталями реализации, спрятанными внутри одного приложения.

4. **Экосистема инструментов вокруг одного контракта**
   Один и тот же контракт может управлять:
    - сгенерированными клиентами
    - сгенерированными серверами
    - Swagger UI
    - поведением проверки данных
    - имитационными серверами
    - тестами, управляемыми контрактом

5. **Более безопасное долгосрочное развитие**
   Когда контракт меняется, влияние становится видно сразу.
   Ломающие изменения можно проверять на уровне контракта, а не случайно обнаруживать, когда другая команда обновится слишком поздно.

#### Почему это важно для клиента { #matters-client }

В этом руководстве мы смотрим на контрактную разработку со стороны клиента.

Это немного меняет ценность подхода.

Цель здесь не только «сгенерировать код, потому что мы можем». Настоящая цель:

- перестать дублировать один и тот же транспортный контракт в рукописном клиентском интерфейсе
- заставить клиент следовать ровно тому же документу OpenAPI, что и сервер
- позволить сгенерированным моделям и оберткам ответов явнее представлять поведение API

Именно поэтому это руководство идет после `http-client.md` и `openapi-http-server.md`.

Сначала вы изучаете:

- как работает рукописный декларативный клиент
- как работает сервер, управляемый OpenAPI

и только потом объединяете эти идеи в один общий контрактный поток интеграции.

#### Контрактное преимущество Kora { #koras-contract-first-advantage }

Kora делает это особенно практичным, потому что сгенерированный клиент не является одноразовой клиентской библиотекой. Он естественно встраивается в остальной фреймворк:

- сгенерированные клиенты подключаются через внедрение зависимостей Kora
- конфигурация по-прежнему обрабатывается через обычные пути конфигурации Kora
- сопоставление JSON по-прежнему выполняется сгенерированными преобразователями Kora
- сопоставление кодов ответов генерируется явно через типизированные обертки ответов
- сгенерированный клиент по-прежнему ведет себя как обычная зависимость Kora в графе приложения

Поэтому результат все еще ощущается как приложение Kora, а не как внешний генератор кода, прикрученный сбоку.

### Зачем один контракт { #one-contract }

Базовое руководство по клиенту уже показало, что рукописный декларативный клиент намного приятнее низкоуровневого кода HTTP-запросов. Но у рукописных декларативных клиентов все равно есть один
долгосрочный риск:

- контракты клиента и сервера могут постепенно разойтись

Например, одна сторона может изменить:

- статус ответа
- имя поля DTO
- параметр пути
- обязательное свойство запроса

Если этот контракт живет только в рукописном коде, такие несовпадения часто обнаруживаются поздно, во время интеграционного тестирования или после развертывания.

Контрактный рабочий процесс снижает этот риск. Файл OpenAPI становится общим контрактом, и обе стороны генерируются из него.

Это дает несколько практических преимуществ:

- сервер и клиент описывают одни и те же маршруты и модели
- обертки ответов генерируются согласованно
- изменения моделей запросов и ответов начинаются с одного файла контракта
- клиенту больше не нужны собственные рукописные транспортные DTO

Поэтому это руководство не вводит полностью другую архитектуру. Оно берет клиентское приложение из `http-client.md` и заставляет его зависеть от того же контракта, который уже использует сервер.

## OpenAPI-контракт { #openapi-contract }

Самое важное решение в этом руководстве очень простое:

- **не** придумывать второй контракт только для клиента
- **не** дублировать YAML вручную с небольшими отличиями
- использовать тот же `user-http-server.yaml` из [openapi-http-server.md](openapi-http-server.md)

Именно так устроено запускаемое приложение руководства. Его сборка указывает на контракт из соседнего серверного модуля:

```text
../guide-openapi-http-server-app/src/main/resources/openapi/user-http-server.yaml
```

Этот файл уже определяет API пользователей:

- `POST /users`
- `GET /users/{userId}`
- `GET /users`
- `PUT /users/{userId}`
- `DELETE /users/{userId}`

и уже содержит те же транспортные модели:

- `UserRequestTO`
- `UserResponseTO`

Это ключевой урок руководства. Контрактная разработка лучше всего работает, когда клиент и сервер действительно разделяют один контракт, а не две почти одинаковые копии.

## Контракт к клиенту { #contract-client }

Хотя файл OpenAPI уже был создан в [openapi-http-server.md](openapi-http-server.md), здесь стоит остановиться и снова посмотреть на него с точки зрения клиента.

Мы не создаем новую клиентскую спецификацию.

Мы используем ровно тот же HTTP-контракт OpenAPI, который был введен в серверном руководстве. В этом и заключается весь смысл рабочего процесса:

- один общий контракт
- один сервер, сгенерированный из него
- один клиент, сгенерированный из него

Поэтому в этом руководстве, когда мы говорим «описать API в OpenAPI», мы на самом деле имеем в виду «переиспользовать то же описание OpenAPI, которое уже стало источником истины в серверном
руководстве».

Общий контракт выглядит так:

??? example "OpenAPI-контракт"

    ```yaml title="src/main/resources/openapi/user-http-server.yaml"
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
            - name: userId
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
            - name: userId
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

С точки зрения клиента этот контракт уже сообщает почти все, что нам нужно:

- какие операции существуют
- какая модель запроса отправляется
- какая модель успеха возвращается
- какая модель ошибки возвращается для `404` и `500`

Именно поэтому следующий шаг генерации так силен. Генератор не придумывает клиентский API. Он просто превращает этот общий контракт в типизированные клиентские абстракции.

## Зависимости { #dependencies }

Приложение по-прежнему сохраняет ту же общую форму, что и в базовом руководстве по клиенту:

- это самостоятельное приложение Kora
- оно по-прежнему открывает один небольшой контроллер для проверки
- ему по-прежнему нужна поддержка HTTP-клиента и HTTP-сервера

Но теперь ему также нужна поддержка генерации OpenAPI.

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
        implementation("ru.tinkoff.kora:http-client-common")
        implementation("ru.tinkoff.kora:http-client-ok")
        implementation("ru.tinkoff.kora:http-server-undertow")
        implementation("ru.tinkoff.kora:json-module")
        implementation("ru.tinkoff.kora:logging-logback")
        implementation("ru.tinkoff.kora:validation-module")
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
        implementation("ru.tinkoff.kora:http-client-common")
        implementation("ru.tinkoff.kora:http-client-ok")
        implementation("ru.tinkoff.kora:http-server-undertow")
        implementation("ru.tinkoff.kora:json-module")
        implementation("ru.tinkoff.kora:logging-logback")
        implementation("ru.tinkoff.kora:validation-module")
    }
    ```

На этом шаге полезно заметить, что изменилось относительно `http-client.md`:

- мы убрали необходимость в рукописном `UserApiClient`
- мы добавили генератор OpenAPI, чтобы клиентский интерфейс можно было создать из контракта
- мы сохраняем обычные клиентские и серверные зависимости, потому что приложение все еще является настоящим запускаемым сервисом Kora

## Генерация HTTP-клиента { #http-client-generation }

Подробные параметры клиентской генерации, `mode = client` и `clientConfigPrefix` описаны в разделе [OpenAPI Codegen: клиент](../documentation/openapi-codegen.md#client).

Теперь сообщим Gradle, как генерировать клиент из уже существующего контракта.

===! ":fontawesome-brands-java: `Java`"

    ```groovy title="build.gradle"
    def openApiGenerateUsersHttpClient = tasks.register("openApiGenerateUsersHttpClient", GenerateTask) {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/../guide-openapi-http-server-app/src/main/resources/openapi/user-http-server.yaml"
        outputDir = "$buildDir/generated/user-http-client"
        def corePackage = "ru.tinkoff.kora.guide.openapi.httpclient.user"
        apiPackage = "${corePackage}.api"
        modelPackage = "${corePackage}.model"
        invokerPackage = "${corePackage}.invoker"
        configOptions = [
                mode              : "java-client",
                clientConfigPrefix: "httpClient",
        ]
    }

    sourceSets.main {
        java.srcDirs += openApiGenerateUsersHttpClient.get().outputDir
    }

    compileJava.dependsOn openApiGenerateUsersHttpClient
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="build.gradle.kts"
    val openApiGenerateUsersHttpClient = tasks.register<GenerateTask>("openApiGenerateUsersHttpClient") {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/../guide-openapi-http-server-app/src/main/resources/openapi/user-http-server.yaml"
        outputDir = "$buildDir/generated/user-http-client"
        val corePackage = "ru.tinkoff.kora.guide.openapi.httpclient.user"
        apiPackage = "$corePackage.api"
        modelPackage = "$corePackage.model"
        invokerPackage = "$corePackage.invoker"
        configOptions = mapOf(
            "mode" to "java-client",
            "clientConfigPrefix" to "httpClient"
        )
    }

    sourceSets.main {
        java.srcDir(openApiGenerateUsersHttpClient.get().outputDir)
    }

    tasks.compileJava {
        dependsOn(openApiGenerateUsersHttpClient)
    }
    ```

Эта конфигурация вводит несколько идей, которые стоит спокойно понять:

- `mode = "java-client"` означает, что мы генерируем синхронный Java-клиент
- `inputSpec` указывает на точный контракт OpenAPI из предыдущего руководства
- сгенерированные исходники будут помещены в `build/generated/user-http-client`
- `clientConfigPrefix = "httpClient"` сообщает генератору, откуда этот клиент должен читать конфигурацию времени выполнения

Последний пункт особенно важен. Сгенерированный клиент — это не просто набор DTO. Это настоящий HTTP-клиент Kora, который будет подключен к графу приложения и настроен через `application.conf`.

## Что создает генератор { #generated-output }

Запустите:

```bash
./gradlew :guides-apps:guide-openapi-http-client-app:openApiGenerateUsersHttpClient
```

После генерации изучите:

===! ":fontawesome-brands-java: `Java`"

    - `build/generated/user-http-client/ru/tinkoff/kora/guide/openapi/httpclient/user/api/UsersApi.java`
    - `build/generated/user-http-client/ru/tinkoff/kora/guide/openapi/httpclient/user/api/UsersApiResponses.java`
    - `build/generated/user-http-client/ru/tinkoff/kora/guide/openapi/httpclient/user/model/UserRequestTO.java`
    - `build/generated/user-http-client/ru/tinkoff/kora/guide/openapi/httpclient/user/model/UserResponseTO.java`
    - `build/generated/user-http-client/ru/tinkoff/kora/guide/openapi/httpclient/user/model/ErrorResponseTO.java`

=== ":simple-kotlin: `Kotlin`"

    - `build/generated/user-http-client/ru/tinkoff/kora/guide/openapi/httpclient/user/api/UsersApi.kt`
    - `build/generated/user-http-client/ru/tinkoff/kora/guide/openapi/httpclient/user/api/UsersApiResponses.kt`
    - `build/generated/user-http-client/ru/tinkoff/kora/guide/openapi/httpclient/user/model/UserRequestTO.kt`
    - `build/generated/user-http-client/ru/tinkoff/kora/guide/openapi/httpclient/user/model/UserResponseTO.kt`
    - `build/generated/user-http-client/ru/tinkoff/kora/guide/openapi/httpclient/user/model/ErrorResponseTO.kt`

Сгенерированный клиент вводит три важные новые абстракции.

### 1. `UsersApi` { #1-usersapi }

Это сгенерированный интерфейс, который заменяет рукописный `UserApiClient` из базового руководства по клиенту.

Он уже содержит:

- сопоставления HTTP-методов и путей
- аннотации параметров строки запроса и пути
- аннотации тела
- преобразователи ответов

Поэтому вместо того, чтобы писать транспортный контракт самостоятельно, мы теперь наследуем его из файла OpenAPI.

### 2. Сгенерированные транспортные модели { #2-generated-transport-models }

Теперь клиент использует сгенерированные транспортные модели:

- `UserRequestTO`
- `UserResponseTO`

Эти модели принадлежат слою контракта OpenAPI.

В базовом руководстве клиент переиспользовал локальные DTO-классы. Здесь мы намеренно позволяем контракту OpenAPI определять и транспортные модели. Это убирает еще одно место, где могло бы возникнуть
расхождение.

### 3. `UsersApiResponses` { #3-usersapiresponses }

Это одна из самых полезных частей сгенерированного клиента.

Вместо того чтобы сводить все исходы к исключениям или одному типу тела, генератор создает типизированные обертки ответов, такие как:

- `CreateUserApiResponse`
- `GetUserApiResponse`
- `DeleteUserApiResponse`
- `UpdateUserApiResponse`

Это означает, что клиент может явно моделировать разные HTTP-исходы. Например, `getUser()` может вернуть:

- `GetUser200ApiResponse`
- `GetUser404ApiResponse`
- `GetUser500ApiResponse`

Это выразительнее, чем рукописный клиент, который просто предполагает одно тело счастливого пути для каждого вызова.

### Как выглядит сгенерированный код { #generated-code-shape }

Здесь стоит остановиться и открыть сгенерированные файлы напрямую. Как только вы это сделаете, контрактный рабочий процесс становится намного конкретнее.

Вот сокращенная версия сгенерированного метода `UsersApi` для `getUser()`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient(configPath = "httpClient.UsersApi")
    public interface UsersApi {

        @HttpRoute(method = "GET", path = "/users/{userId}")
        @ResponseCodeMapper(code = 200, mapper = UsersApiClientResponseMappers.GetUser200ApiResponseMapper.class)
        @ResponseCodeMapper(code = 404, mapper = UsersApiClientResponseMappers.GetUser404ApiResponseMapper.class)
        @ResponseCodeMapper(code = 500, mapper = UsersApiClientResponseMappers.GetUser500ApiResponseMapper.class)
        UsersApiResponses.GetUserApiResponse getUser(
            @Path("userId") String userId
        );
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient(configPath = "httpClient.UsersApi")
    interface UsersApi {

        @HttpRoute(method = "GET", path = "/users/{userId}")
        @ResponseCodeMapper(code = 200, mapper = UsersApiClientResponseMappers.GetUser200ApiResponseMapper::class)
        @ResponseCodeMapper(code = 404, mapper = UsersApiClientResponseMappers.GetUser404ApiResponseMapper::class)
        @ResponseCodeMapper(code = 500, mapper = UsersApiClientResponseMappers.GetUser500ApiResponseMapper::class)
        fun getUser(
            @Path("userId") userId: String
        ): UsersApiResponses.GetUserApiResponse
    }
    ```

А вот соответствующая часть `UsersApiResponses`:

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

Этот небольшой фрагмент сгенерированного кода уже показывает большинство важных абстракций.

### Разбор сгенерированного `getUser()` { #generated-getuser-walkthrough }

Давайте разберем, что создал генератор и почему.

`@HttpClient(configPath = "httpClient.UsersApi")`

Это сообщает Kora, что сгенерированный интерфейс является настоящей зависимостью HTTP-клиента. Kora генерирует реализацию времени выполнения, помещает ее в граф зависимостей и привязывает к
соответствующему разделу конфигурации в `application.conf`.

`@HttpRoute(method = "GET", path = "/users/{userId}")`

Генератор читает операцию OpenAPI и проецирует ее в транспортную аннотацию Kora. Вам больше не нужно повторять маршрут вручную в рукописном интерфейсе клиента. Контракт OpenAPI остается источником
истины, а сгенерированный интерфейс Java или Kotlin становится транспортно-специфичным представлением этого контракта.

`@Path("userId") String userId`

Параметр пути из файла OpenAPI становится обычным типизированным аргументом метода. Вместо ручной сборки URL вы работаете с обычной сигнатурой метода и позволяете сгенерированной реализации поместить
значение в путь запроса.

`@ResponseCodeMapper(...)`

Это одна из самых полезных частей сгенерированного кода. Контракт говорит, что `GET /users/{userId}` может произвести:

- `200` с телом `UserResponseTO`
- `404` с телом `ErrorResponseTO`
- `500` с телом `ErrorResponseTO`

Поскольку эти коды присутствуют в файле OpenAPI, генератор создает преобразователи ответов для каждого из них. Во время выполнения клиент использует настоящий HTTP-код состояния, чтобы решить, какой
типизированный вариант ответа создать.

Именно поэтому добавление `500` в файл OpenAPI имеет значение. Если контракт не описывает `500`, у генератора нет причины создавать отдельную абстракцию `GetUser500ApiResponse` для него.

`UsersApiResponses.GetUserApiResponse`

Возвращаемый тип — это не просто `UserResponseTO`. Это запечатанное семейство ответов, которое моделирует весь транспортный контракт этой конечной точки. Благодаря этому исходы API становятся явными
прямо в месте вызова.

На практике это приводит к такому коду:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var response = usersApi.getUser(userId);

    if (response instanceof UsersApiResponses.GetUserApiResponse.GetUser200ApiResponse ok) {
        return ok.content();
    }
    if (response instanceof UsersApiResponses.GetUserApiResponse.GetUser404ApiResponse notFound) {
        // notFound.content().message() describes the error
    }
    if (response instanceof UsersApiResponses.GetUserApiResponse.GetUser500ApiResponse internalError) {
        // internalError.content().message() describes the error
    }
    ```

    Если вам ближе стиль выражений:
    ```java
    return switch (usersApi.getUser(userId)) {
        case UsersApiResponses.GetUserApiResponse.GetUser200ApiResponse ok ->
                ok.content().name();
        case UsersApiResponses.GetUserApiResponse.GetUser404ApiResponse notFound ->
                "Missing user: " + notFound.content().message();
        case UsersApiResponses.GetUserApiResponse.GetUser500ApiResponse internalError ->
                "Server error: " + internalError.content().message();
    };
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val response = usersApi.getUser(userId)

    when (response) {
        is UsersApiResponses.GetUserApiResponse.GetUser200ApiResponse ->
            return response.content()
        is UsersApiResponses.GetUserApiResponse.GetUser404ApiResponse -> {
            // response.content().message() describes the error
        }
        is UsersApiResponses.GetUserApiResponse.GetUser500ApiResponse -> {
            // response.content().message() describes the error
        }
    }
    ```

Такой стиль является одним из главных преимуществ сгенерированных контрактных клиентов. Код, который вы пишете, отражает полный контракт API, а не только счастливый путь.

### Слои генератора { #generator-layers }

На первый взгляд сгенерированный код может казаться более многословным, чем рукописный интерфейс. Но у каждого сгенерированного слоя есть четкая роль:

- `UsersApi` определяет вызываемую поверхность клиента
- параметры методов представляют транспортные входные данные, такие как значения пути и строки запроса
- сгенерированные модели, такие как `UserRequestTO` и `UserResponseTO`, представляют полезные нагрузки OpenAPI
- сгенерированные обертки ответов моделируют допустимые HTTP-исходы
- сгенерированные преобразователи ответов превращают сырые HTTP-ответы в типизированные варианты

Генератор создает дополнительный код не ради хитрости. Он превращает транспортный контракт в явные типизированные абстракции, с которыми помогает работать компилятор.

Общая модель ошибки тоже важна. Поскольку контракт теперь определяет `ErrorResponseTO(message)`, сгенерированный клиент может воспринимать ответы с ошибками как структурированные транспортные данные,
а не только как коды состояния.

## Сгенерированный клиент { #generated-client }

Клиентское приложение по-прежнему сохраняет ту же общую учебную форму из `http-client.md`:

- один сгенерированный клиент
- один небольшой агрегирующий контроллер
- одно место для ручного запуска потока

Но теперь `ClientTestController` зависит от `UsersApi`, а не от рукописного `UserApiClient`.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/openapi/httpclient/controller/ClientTestController.java"
    package ru.tinkoff.kora.guide.openapi.httpclient.controller;

    import java.util.List;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.openapi.httpclient.user.api.UsersApi;
    import ru.tinkoff.kora.guide.openapi.httpclient.user.api.UsersApiResponses;
    import ru.tinkoff.kora.guide.openapi.httpclient.user.model.UserRequestTO;
    import ru.tinkoff.kora.guide.openapi.httpclient.user.model.UserResponseTO;
    import ru.tinkoff.kora.http.common.HttpMethod;
    import ru.tinkoff.kora.http.common.annotation.HttpRoute;
    import ru.tinkoff.kora.http.server.common.annotation.HttpController;
    import ru.tinkoff.kora.json.common.annotation.Json;

    @Component
    @HttpController
    public final class ClientTestController {

        private final UsersApi usersApi;

        public ClientTestController(UsersApi usersApi) {
            this.usersApi = usersApi;
        }

        @HttpRoute(method = HttpMethod.POST, path = "/client/test-all-user-endpoints")
        @Json
        public TestResults testAllUserEndpoints() {
            try {
                var created = this.usersApi.createUser(new UserRequestTO("Client Demo User", "client-demo@example.com"));
                boolean userCreated = created instanceof UsersApiResponses.CreateUserApiResponse.CreateUser201ApiResponse create201
                        && create201.content() != null;
                var createdUser = created instanceof UsersApiResponses.CreateUserApiResponse.CreateUser201ApiResponse create201
                        ? create201.content()
                        : null;

                var getUserResponse = createdUser == null ? null : this.usersApi.getUser(createdUser.id());
                boolean userFetched = getUserResponse instanceof UsersApiResponses.GetUserApiResponse.GetUser200ApiResponse getUser200
                        && createdUser.id().equals(getUser200.content().id());

                var getUsersResponse = this.usersApi.getUsers(0, 10, "name");
                List<UserResponseTO> users = getUsersResponse instanceof UsersApiResponses.GetUsersApiResponse.GetUsers200ApiResponse getUsers200
                        ? getUsers200.content()
                        : List.of();
                boolean usersListed = createdUser != null && users.stream().anyMatch(user -> user.id().equals(createdUser.id()));

                var deleteResult = createdUser == null ? null : this.usersApi.deleteUser(createdUser.id());
                boolean userDeleted = deleteResult instanceof UsersApiResponses.DeleteUserApiResponse.DeleteUser204ApiResponse;

                boolean allTestsPassed = userCreated && userFetched && usersListed && userDeleted;
                return new TestResults(userCreated, userFetched, usersListed, userDeleted, allTestsPassed, null);
            } catch (Exception exception) {
                return new TestResults(false, false, false, false, false, exception.getMessage());
            }
        }

        @Json
        public record TestResults(
                boolean userCreated,
                boolean userFetched,
                boolean usersListed,
                boolean userDeleted,
                boolean allTestsPassed,
                String error) {}
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/openapi/httpclient/controller/ClientTestController.kt"
    package ru.tinkoff.kora.guide.openapi.httpclient.controller

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.openapi.httpclient.user.api.UsersApi
    import ru.tinkoff.kora.guide.openapi.httpclient.user.api.UsersApiResponses
    import ru.tinkoff.kora.guide.openapi.httpclient.user.model.UserRequestTO
    import ru.tinkoff.kora.http.common.HttpMethod
    import ru.tinkoff.kora.http.common.annotation.HttpRoute
    import ru.tinkoff.kora.http.server.common.annotation.HttpController
    import ru.tinkoff.kora.json.common.annotation.Json

    @Component
    @HttpController
    class ClientTestController(
        private val usersApi: UsersApi
    ) {
        @HttpRoute(method = HttpMethod.POST, path = "/client/test-all-user-endpoints")
        @Json
        fun testAllUserEndpoints(): TestResults {
            return try {
                val created = usersApi.createUser(UserRequestTO("Client Demo User", "client-demo@example.com"))
                val userCreated =
                    created is UsersApiResponses.CreateUserApiResponse.CreateUser201ApiResponse &&
                        created.content() != null
                val createdUser =
                    if (created is UsersApiResponses.CreateUserApiResponse.CreateUser201ApiResponse) created.content() else null

                val getUserResponse = createdUser?.let { usersApi.getUser(it.id()) }
                val userFetched =
                    getUserResponse is UsersApiResponses.GetUserApiResponse.GetUser200ApiResponse &&
                        createdUser != null &&
                        createdUser.id() == getUserResponse.content().id()

                val getUsersResponse = usersApi.getUsers(0, 10, "name")
                val users =
                    if (getUsersResponse is UsersApiResponses.GetUsersApiResponse.GetUsers200ApiResponse) {
                        getUsersResponse.content()
                    } else {
                        emptyList()
                    }
                val usersListed = createdUser != null && users.any { it.id() == createdUser.id() }

                val deleteResult = createdUser?.let { usersApi.deleteUser(it.id()) }
                val userDeleted = deleteResult is UsersApiResponses.DeleteUserApiResponse.DeleteUser204ApiResponse

                val allTestsPassed = userCreated && userFetched && usersListed && userDeleted
                TestResults(userCreated, userFetched, usersListed, userDeleted, allTestsPassed, null)
            } catch (e: Exception) {
                TestResults(false, false, false, false, false, e.message)
            }
        }

        @Json
        data class TestResults(
            val userCreated: Boolean,
            val userFetched: Boolean,
            val usersListed: Boolean,
            val userDeleted: Boolean,
            val allTestsPassed: Boolean,
            val error: String?
        )
    }
    ```

Именно на этом шаге руководство становится по-настоящему конкретным.

Мы **не** переписали все клиентское приложение.

Мы сохранили тот же пользовательский поток из `http-client.md`:

- создать пользователя
- получить его
- вывести список пользователей
- удалить его

Мы заменили только слой транспортного контракта:

- раньше: рукописный `UserApiClient`
- теперь: сгенерированный `UsersApi`

Именно такие постепенные изменения команды часто делают в реальных проектах.

## Конфигурация { #config }

Поскольку сгенерированный клиент был создан с:

```text
clientConfigPrefix = "httpClient"
```

а имя сгенерированного интерфейса — `UsersApi`, его конфигурация времени выполнения находится в:

```text
httpClient.UsersApi
```

Обновите `src/main/resources/application.conf`:

Полный справочник по конфигурации смотрите в [HTTP-сервер](../documentation/http-server.md), [HTTP-клиент](../documentation/http-client.md) и [журналирование SLF4J](../documentation/logging-slf4j.md).

===! ":material-code-json: `Hocon`"

    ```javascript title="src/main/resources/application.conf"
    httpServer {
      publicApiHttpPort = 8081 //(1)!
      privateApiHttpPort = 8086 //(2)!
      telemetry.logging.enabled = true //(3)!
    }

    httpClient {
      UsersApi {
        url = "http://localhost:8080" //(4)!
        url = ${?USER_API_URL} //(5)!
        requestTimeout = 10s //(6)!
      }
      telemetry.logging.enabled = true //(7)!
    }

    logging {
      levels {
        "ROOT": "INFO" //(8)!
        "ru.tinkoff.kora": "INFO" //(9)!
        "ru.tinkoff.kora.guide.openapi.httpclient": "INFO" //(10)!
      }
    }
    ```

    1. Публичный HTTP-порт по умолчанию, используемый конечными точками приложения.
    2. Приватный HTTP-порт по умолчанию, используемый пробами, метриками и конечными точками управления.
    3. Включает возможность для этого раздела конфигурации.
    4. Базовый URL, используемый настроенным клиентом.
    5. Базовый URL, используемый настроенным клиентом. Необязательное переопределение из `USER_API_URL`.
    6. Максимальное время, разрешенное для клиентского запроса.
    7. Включает возможность для этого раздела конфигурации.
    8. Уровень логирования для `ROOT`.
    9. Уровень логирования для `ru.tinkoff.kora`.
    10. Уровень логирования для `ru.tinkoff.kora.guide.openapi.httpclient`.

=== ":simple-yaml: `YAML`"

    ```yaml title="src/main/resources/application.yaml"
    httpServer:
      publicApiHttpPort: 8081 #(1)!
      privateApiHttpPort: 8086 #(2)!
      telemetry:
        logging:
          enabled: true #(3)!
    httpClient:
      UsersApi:
        url: ${?USER_API_URL:"http://localhost:8080"} #(4)!
        requestTimeout: 10s #(5)!
      telemetry:
        logging:
          enabled: true #(6)!
    logging:
      levels:
        ROOT: "INFO" #(7)!
        "ru.tinkoff.kora": "INFO" #(8)!
        "ru.tinkoff.kora.guide.openapi.httpclient": "INFO" #(9)!
    ```

    1. Публичный HTTP-порт по умолчанию, используемый конечными точками приложения.
    2. Приватный HTTP-порт по умолчанию, используемый пробами, метриками и конечными точками управления.
    3. Включает возможность для этого раздела конфигурации.
    4. Базовый URL, используемый настроенным клиентом. Использует показанное значение по умолчанию и позволяет `USER_API_URL` переопределить его.
    5. Максимальное время, разрешенное для клиентского запроса.
    6. Включает возможность для этого раздела конфигурации.
    7. Уровень логирования для `ROOT`.
    8. Уровень логирования для `ru.tinkoff.kora`.
    9. Уровень логирования для `ru.tinkoff.kora.guide.openapi.httpclient`.

Этот шаг вводит тонкую, но важную идею.

В руководстве с рукописным клиентом вы сами выбирали путь конфигурации в `@HttpClient(configPath = ...)`.

Здесь генератор выбирает клиентскую аннотацию за вас на основе:

- `clientConfigPrefix`
- имени сгенерированного API

Поэтому когда во время выполнения что-то выглядит «отсутствующим», часто стоит проверить, какой путь конфигурации на самом деле использует сгенерированный интерфейс.

## Проверка приложения { #check-app }

Если вы хотите проверить поток вручную, запустите оба приложения в отдельных терминалах.

### Терминал 1: OpenAPI-сервер { #terminal-1-openapi-server }

```bash
./gradlew run
```

Это приложение открывает:

- API пользователей на `http://localhost:8080`
- `/openapi`
- `/swagger-ui`

### Терминал 2: OpenAPI-клиент { #terminal-2-openapi-client }

```bash
./gradlew run
```

Это приложение открывает собственную агрегирующую конечную точку проверки на:

- `http://localhost:8081/client/test-all-user-endpoints`

Теперь запустите весь клиентский сценарий:

```bash
curl -X POST http://localhost:8081/client/test-all-user-endpoints
```

Ожидаемый результат: JSON-объект, где `allTestsPassed` равен `true`.

## Тестирование { #testing }

Запускаемое приложение руководства также включает набор тестов, который направляет сгенерированный клиент на контейнеризованную копию `guide-openapi-http-server-app`.

Запустите:

```bash
./gradlew test
```

Эти тесты проверяют тот же базовый поток, что и руководство с рукописным клиентом:

- создать пользователя
- получить пользователя
- отсутствующий пользователь
- список пользователей с постраничным выводом и сортировкой
- удалить пользователя

Так сравнение между двумя руководствами легко понять:

- `http-client.md` доказывает поток с рукописным декларативным клиентом
- это руководство доказывает тот же поток со сгенерированным OpenAPI-клиентом

## Лучшие практики { #best-practices }

- По возможности переиспользуйте один и тот же контракт OpenAPI между сервером и клиентом.
- Относитесь к сгенерированному коду как к результату сборки, а не как к коду приложения, который редактируют вручную.
- Держите прикладную логику вне сгенерированного клиента, в собственных контроллерах или сервисных классах.
- Изучайте сгенерированный интерфейс и обертки ответов, когда поведение времени выполнения непонятно.
- Для учебных сценариев держите одну небольшую агрегирующую конечную точку проверки, вместо того чтобы пересобирать полный сервер внутри клиентского приложения.

## Итоги { #summary }

Вы взяли самостоятельное клиентское приложение из [HTTP-клиент с Kora](http-client.md) и пересобрали его транспортный слой в контрактном стиле:

- клиент теперь использует тот же контракт `user-http-server.yaml`, что и руководство по OpenAPI-серверу
- Kora генерирует `UsersApi` из этого общего контракта
- сгенерированные транспортные модели заменяют рукописные DTO клиента
- сгенерированные обертки ответов делают несколько HTTP-исходов явными
- клиентское приложение по-прежнему сохраняет тот же простой агрегирующий поток проверки

Так общее клиентское приложение остается знакомым, но транспортный контракт теперь общий с сервером, а не написан отдельно вручную.

## Ключевые понятия { #key-concepts }

- контрактный клиент лучше всего работает, когда переиспользует ровно тот же файл OpenAPI, что и сервер
- Kora может генерировать типизированный HTTP-клиент из OpenAPI
- сгенерированные обертки ответов, такие как `GetUserApiResponse` и `DeleteUserApiResponse`, делают HTTP-исходы явными
- добавление `500` в файл OpenAPI также генерирует отдельные варианты ответов `500`
- сгенерированные транспортные модели могут заменить рукописные DTO клиента
- `clientConfigPrefix` управляет тем, откуда сгенерированный клиент читает конфигурацию времени выполнения

## Устранение неполадок { #troubleshooting }

**Сгенерированный клиент отсутствует в графе:**

Проверьте, что:

- задача генерации OpenAPI запускается до компиляции
- сгенерированный выходной каталог добавлен в `sourceSets.main`
- приложение включает модуль HTTP-клиента, например `OkHttpClientModule`

**Во время выполнения сказано, что конфигурация клиента отсутствует:**

Изучите сгенерированный интерфейс и посмотрите на его аннотацию `@HttpClient(configPath = ...)`.

В этом руководстве сгенерированный клиент ожидает:

```text
httpClient.UsersApi
```

а не просто:

```text
httpClient
```

**Модели клиента и сервера выглядят похожими, но не одинаковыми:**

Это часто означает, что клиент больше не использует рукописные DTO и теперь использует сгенерированные транспортные модели из контракта OpenAPI. Убедитесь, что код приложения импортирует:

- `UserRequestTO`
- `UserResponseTO`

из сгенерированного пакета.

**Сборка успешна, но импорты не совпадают:**

Проверьте настройки генерации в `build.gradle`:

- `outputDir`
- `apiPackage`
- `modelPackage`
- `invokerPackage`

Если они меняются, импорты контроллера тоже должны измениться.

**Сгенерированный клиент не открывает вариант ответа `500`:**

Сначала изучите файл OpenAPI.

Сгенерированные варианты ответов появляются только для кодов состояния, которые действительно описаны в контракте. Если вам нужна явная обработка `500`, он должен присутствовать в разделе `responses`
этой операции в общем файле OpenAPI.

**Контейнерные тесты не могут достучаться до серверного приложения:**

Проверьте, что:

- Docker запущен
- тест зависит от `guide-openapi-http-server-app:distTar`
- Dockerfile серверного модуля указывает на собственный сгенерированный дистрибутив
- `USER_API_URL` переопределяется из URI контейнера в тестовой конфигурации

## Что дальше? { #whats-next }

- [Шаблоны устойчивости](resilient.md), чтобы сделать сгенерированные клиенты устойчивее к медленным или нестабильным зависимостям.
- [Наблюдаемость](observability.md), чтобы трассировать вызовы сгенерированного клиента и измерять исходы по статусам.
- [Продвинутый HTTP-сервер](http-server-advanced.md), а затем [Продвинутый HTTP-клиент](http-client-advanced.md), если вы хотите сравнить сгенерированные по контракту клиенты с рукописными продвинутыми
  клиентами.
- [gRPC Server](grpc-server.md), если хотите изучить строго типизированный бинарный контракт после OpenAPI.

## Помощь { #help }

Если вы застряли:

- сравните с [Kora Java OpenAPI HTTP Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-openapi-http-client-app) и [Kora Kotlin OpenAPI HTTP Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-openapi-http-client-app)
- вернитесь к [HTTP-клиент](http-client.md) как к базовой версии рукописного клиента
- вернитесь к [OpenAPI HTTP-сервер](openapi-http-server.md), чтобы посмотреть серверный контракт, который использует этот клиент
- проверьте [документацию по генерации OpenAPI-кода](../documentation/openapi-codegen.md)
- проверьте [документацию HTTP-клиента](../documentation/http-client.md)
