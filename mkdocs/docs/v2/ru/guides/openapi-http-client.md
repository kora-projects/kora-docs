---
search:
  exclude: true
title: Контрактный HTTP-клиент с OpenAPI
summary: Continue the HTTP Client guide by replacing the handwritten declarative client with an OpenAPI-generated client
description: "Contract-first Kora HTTP client from an OpenAPI file: the org.openapi.generator Gradle plugin with generatorName kora, configOptions mode java-client / kotlin-client, clientConfig and clientConfigPrefix, the generated @HttpClient interface with @ResponseCodeMapper, sealed <Api>Responses wrappers, OptArgs holders for optional parameters, enum fromValue, and testing the generated client against a Testcontainers copy of the server."
agent:
  use_when: "Use this file for questions about generating a Kora HTTP client from an OpenAPI contract step by step: GenerateTask, generatorName kora, mode java-client and kotlin-client, clientConfig versus clientConfigPrefix and the httpClient.<prefix>.<api> configuration path with a lower-case first letter, the generated @HttpClient interface, @HttpRoute and @ResponseCodeMapper annotations, <Api>ClientResponseMappers, sealed <Api>Responses matching, <Api><Operation>OptArgs holders, generated enum fromValue, HttpClientResponseException, and KoraAppTestConfigModifier with Testcontainers."
tags: openapi, http-client, contract-first, code-generation, swagger
---

# Контрактный HTTP-клиент с OpenAPI { #contract-first-http-client }

Это руководство знакомит с контрактными HTTP-клиентами в Kora на основе OpenAPI. В нем разбирается, как спецификация OpenAPI порождает типизированный клиент, как сгенерированные модели запросов и
ответов заменяют написанные вручную транспортные интерфейсы, и как клиент подключается к приложению Kora. Вы также увидите, как один контракт API может описывать обе стороны HTTP-интеграции без
дублирования сигнатур методов.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java OpenAPI HTTP Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-openapi-http-client-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin OpenAPI HTTP Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-openapi-http-client-app).

## Что вы создадите { #youll-build }

Вы пересоберете клиентское приложение из руководства [HTTP-клиент в Kora](http-client.md), но в контрактном стиле:

- удаленное API пользователей будет описано тем же контрактом `user-http-server.yaml` из [Контрактного HTTP-сервера с OpenAPI](openapi-http-server.md)
- Kora сгенерирует типизированный интерфейс клиента по этому контракту
- сгенерированные модели запросов и ответов заменят написанные вручную DTO клиента
- клиентское приложение по-прежнему будет отдавать одну сводную конечную точку для удобной ручной проверки
- тесты будут гонять сгенерированный клиент против копии OpenAPI-сервера в контейнере

## Что вам понадобится { #youll-need }

- JDK 25 или новее
- Gradle 9+
- Docker Desktop или другое локальное окружение Docker для тестов на контейнерах
- Текстовый редактор или IDE
- Два терминала, если захотите запустить сервер и клиент вручную

## Требования { #prerequisites }

!!! note "Сначала пройдите руководство по OpenAPI HTTP-серверу"

    Руководство предполагает, что вы прошли **[HTTP-клиент в Kora](http-client.md)** и **[Контрактный HTTP-сервер с OpenAPI](openapi-http-server.md)**.

    Если эти руководства еще не пройдены, начните с них: они уже покрывают базовый поток HTTP-клиента и контракт OpenAPI-сервера, который переиспользует этот сгенерированный клиент.

## Обзор { #overview }

В базовом руководстве по HTTP-клиенту процесс выглядел так:

1. определить `UserApiClient` вручную
2. добавить аннотации, описывающие удаленный контракт
3. дать Kora сгенерировать реализацию по этому интерфейсу
4. внедрить клиент и вызвать сервер

Это уже очень продуктивная модель.

Но как только сам сервер становится контрактным, появляется более удачный следующий шаг:

1. держать контракт OpenAPI как источник истины
2. генерировать сервер по этому контракту
3. генерировать клиент по тому же контракту
4. позволить обоим приложениям развиваться от одного описания

В этом руководстве мы постепенно пройдем этот переход:

1. поймем, зачем нужен сгенерированный клиент, когда уже есть сгенерированный сервер
2. принесем тот же контракт `user-http-server.yaml` и в клиентский процесс
3. настроим генерацию клиента Kora по OpenAPI
4. изучим сгенерированный интерфейс `UsersApi` и сгенерированные модели
5. заменим написанный вручную клиент сгенерированным
6. сохраним тот же сводный поток проверки из [HTTP-клиента](http-client.md)
7. настроим сгенерированный клиент
8. запустим и проверим приложение
9. протестируем сгенерированный клиент против OpenAPI-сервера

### Контрактная разработка? { #contract-first-development }

Прежде чем что-то генерировать, полезно понять, почему команды вообще выбирают такой процесс.

При традиционном подходе «сначала код» разработчики обычно начинают с контроллеров, конечных точек или клиентских интерфейсов, написанных прямо в коде, и только потом пытаются задокументировать API. Для
небольших систем это работает, но со временем создает реальные трения между командами и между приложениями.

#### Проблема API, построенных от кода { #problem-code-first-apis }

Когда контракт не является главным источником истины, появляется несколько проблем:

- **Расхождение документации**: документация API устаревает по мере развития кода
- **Несовпадение контрактов**: команды клиента и сервера опираются на слегка разные представления об одном API
- **Поздняя проверка**: проблемы проектирования обнаруживаются только при интеграционном тестировании или после развертывания
- **Ручное сопровождение**: документацию, SDK, примеры и тесты приходится обновлять по отдельности
- **Пробелы в коммуникации**: команды тратят время на уточнение поведения в чатах, встречах и тикетах вместо опоры на один общий контракт

Для клиентского приложения это особенно болезненно. Написанный вручную клиент может успешно компилироваться, хотя удаленное API уже изменилось едва заметным, но ломающим образом.

#### Контрактное решение { #contract-first-solution }

Контрактная разработка переворачивает этот процесс.

Вместо «код определяет API» мы говорим «контракт определяет код». Спецификация OpenAPI становится единственным источником истины, которому обязаны следовать и сервер, и клиент.

Это значит, что:

- сервер генерируется по контракту или проверяется на соответствие ему
- клиент генерируется по тому же контракту
- документация выводится из того же контракта

Так вместо поддержки нескольких параллельных описаний API вы поддерживаете один общий контракт, а рутинную синхронизацию делают инструменты.

#### Изменение работы команды { #team-workflow-changes }

Контрактная разработка — это не только трюк сборки. Она меняет то, как команды взаимодействуют.

1. **Проектирование до реализации**
   Проектирование API происходит сначала на уровне спецификации, поэтому форму API можно обсудить до появления рабочего кода.
   Так проще проверить пути, полезные нагрузки, статусы и именование, пока стоимость изменения еще мала.

2. **Автоматическая согласованность**
   Когда и сервер, и клиент генерируются по одной спецификации, шанс транспортного расхождения резко падает.
   Не нужно вручную поддерживать в синхроне определения маршрутов, поля DTO и ожидаемые ответы в двух разных кодовых базах.

3. **Лучшее взаимодействие между ролями**
   Бэкенд-инженеры, фронтенд-инженеры, QA и продуктовые стейкхолдеры могут рассуждать об одном и том же контракте.
   Файл OpenAPI становится общим языком вместо деталей реализации, спрятанных внутри одного приложения.

4. **Экосистема инструментов вокруг одного контракта**
   Один и тот же контракт может порождать:
    - сгенерированные клиенты
    - сгенерированные серверы
    - Swagger UI и Scalar
    - поведение валидации
    - mock-серверы
    - тесты по контракту

5. **Более безопасное долгосрочное развитие**
   Когда контракт меняется, влияние видно сразу.
   Ломающие изменения можно обсудить на уровне контракта, а не обнаружить случайно, когда другая команда обновится слишком поздно.

#### Почему это важно для клиента { #matters-client }

В этом руководстве мы смотрим на контрактную разработку со стороны клиента.

Это немного меняет ценностное предложение.

Цель здесь не только «сгенерировать код, потому что мы можем». Настоящая цель:

- перестать дублировать один и тот же транспортный контракт в написанном вручную интерфейсе клиента
- заставить клиент следовать ровно тому же документу OpenAPI, что и сервер
- дать сгенерированным моделям и оберткам ответов представлять поведение API более явно

Поэтому это руководство идет после [HTTP-клиента](http-client.md) и [OpenAPI HTTP-сервера](openapi-http-server.md).

Сначала вы узнаете, как работает написанный вручную декларативный клиент и как работает сервер, управляемый OpenAPI, и только потом объединяете эти идеи в один контрактный процесс интеграции.

#### Контрактное преимущество Kora { #koras-contract-first-advantage }

Kora делает это особенно практичным, потому что сгенерированный клиент — не одноразовый SDK. Он естественно встраивается в остальной фреймворк:

- сгенерированные клиенты подключаются через внедрение зависимостей Kora
- конфигурация по-прежнему идет через обычные пути конфигурации Kora
- маппинг JSON по-прежнему выполняют сгенерированные мапперы Kora
- отображение кодов ответа генерируется явно через типизированные обертки ответов
- сгенерированный клиент остается обычной зависимостью Kora в графе вашего приложения

Так результат по-прежнему ощущается как приложение Kora, а не как внешний кодогенератор, прикрученный сбоку.

### Зачем один контракт { #one-contract }

Базовое руководство по клиенту уже показало, что написанный вручную декларативный клиент намного приятнее низкоуровневого кода HTTP-запросов. Но у ручных декларативных клиентов остается один
долгосрочный риск: контракты клиента и сервера могут постепенно разойтись.

Например, одна из сторон может изменить:

- статус ответа
- имя поля DTO
- path-параметр
- обязательное свойство запроса

Если этот контракт живет только в написанном вручную коде, такие несовпадения часто обнаруживаются поздно — при интеграционном тестировании или после развертывания.

Контрактный процесс снижает этот риск. Файл OpenAPI становится общим контрактом, и обе стороны генерируются по нему.

Это дает несколько практических преимуществ:

- сервер и клиент описывают одни и те же маршруты и модели
- обертки ответов генерируются согласованно
- изменения моделей запросов и ответов начинаются с одного файла контракта
- клиенту больше не нужны собственные транспортные DTO, написанные вручную

Так что это руководство не про совершенно другую архитектуру. Оно про то, чтобы взять клиентское приложение из [HTTP-клиента](http-client.md) и сделать его зависимым от того же контракта, который уже
использует сервер.

## OpenAPI-контракт { #openapi-contract }

Самое важное решение в этом руководстве очень простое:

- **не** изобретайте второй клиентский контракт
- **не** дублируйте YAML вручную с мелкими отличиями
- используйте тот же `user-http-server.yaml` из [Контрактного HTTP-сервера с OpenAPI](openapi-http-server.md)

Именно так делает запускаемое приложение из руководства. Его сборка указывает на контракт соседнего серверного модуля:

```text
../kora-java-guide-openapi-http-server-app/src/main/resources/openapi/user-http-server.yaml
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
- `ErrorResponseTO`

Это ключевой урок руководства. Контрактная разработка работает лучше всего, когда клиент и сервер действительно разделяют один контракт, а не две почти одинаковые копии.

В реальной системе это разделение обычно идет еще на шаг дальше: контракт публикуется как артефакт или Git-подмодуль, и оба приложения указывают свой `inputSpec` на эту общую копию. Относительный путь к
соседнему модулю работает, пока оба приложения живут в одном репозитории, и именно так устроены приложения из руководств.

## Контракт к клиенту { #contract-client }

Хотя файл OpenAPI уже был создан в [Контрактном HTTP-сервере с OpenAPI](openapi-http-server.md), здесь стоит остановиться и посмотреть на него со стороны клиента.

Мы не создаем новую клиентскую спецификацию. Мы используем ровно тот же HTTP-контракт OpenAPI, который ввело серверное руководство. В этом весь смысл процесса:

- один общий контракт
- один сервер, сгенерированный по нему
- один клиент, сгенерированный по нему

Общий контракт выглядит так:

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

Со стороны клиента этот контракт уже сообщает почти все, что нужно:

- какие операции существуют
- какая модель запроса отправляется
- какая модель успеха возвращается
- какая модель ошибки возвращается для `404` и `500`

Поэтому следующий шаг генерации так силен. Генератор не изобретает клиентское API. Он просто превращает этот общий контракт в типизированные клиентские абстракции.

## Зависимости { #dependencies }

Приложение сохраняет тот же общий вид, что и в базовом руководстве по клиенту:

- это самостоятельное приложение Kora
- оно по-прежнему отдает один небольшой контроллер проверки
- ему по-прежнему нужны поддержка HTTP-клиента и HTTP-сервера

Но теперь ему нужна и поддержка генерации по OpenAPI. Как и на стороне сервера, она состоит из двух частей: **Gradle-плагина** `org.openapi.generator` и **библиотеки**
`io.koraframework:openapi-generator` в classpath `buildscript`, которая учит этот плагин выпускать код Kora.

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
        koraBom platform("io.koraframework:kora-bom:2.0.0.RC1")

        annotationProcessor "io.koraframework:annotation-processors"

        implementation "io.koraframework:config-hocon"
        implementation "io.koraframework:http-client-common" //(4)!
        implementation "io.koraframework:http-client-ok" //(5)!
        implementation "io.koraframework:http-server-undertow" //(6)!
        implementation "io.koraframework:json-common"
        implementation "io.koraframework:logging-logback"
        implementation "io.koraframework:validation-module"

        testAnnotationProcessor "io.koraframework:annotation-processors"

        testImplementation platform("org.junit:junit-bom:$junitVersion")
        testImplementation "org.junit.jupiter:junit-jupiter"
        testImplementation "io.koraframework:test-junit5"
        testImplementation "org.testcontainers:testcontainers-junit-jupiter:2.0.5" //(7)!
        testImplementation "org.testcontainers:testcontainers:2.0.5"
    }
    ```

    1.  `GenerateTask` — тип задачи плагина, через который объявляется задача генерации.
    2.  Реализация генератора Kora, загружаемая JVM `Gradle` через classpath `buildscript`.
    3.  Gradle-плагин `OpenAPI Generator`, зафиксированный на версии, под которую собрана Kora 2.0.
    4.  Контракты и аннотации декларативного HTTP-клиента.
    5.  Реализация транспорта `OkHttp`, которая фактически выполняет запросы.
    6.  Все еще нужен, потому что это приложение также отдает собственную сводную конечную точку проверки.
    7.  Используется только тестами, чтобы поднять OpenAPI-сервер в контейнере.

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
        implementation(platform("io.koraframework:kora-bom:2.0.0.RC1"))

        ksp("io.koraframework:symbol-processors:2.0.0.RC1")

        implementation("io.koraframework:config-hocon")
        implementation("io.koraframework:http-client-common") //(4)!
        implementation("io.koraframework:http-client-ok") //(5)!
        implementation("io.koraframework:http-server-undertow") //(6)!
        implementation("io.koraframework:json-common")
        implementation("io.koraframework:logging-logback")
        implementation("io.koraframework:validation-module")

        testImplementation(platform("org.junit:junit-bom:${property("junitVersion")}"))
        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation("io.koraframework:test-junit5")
        testImplementation("org.testcontainers:testcontainers-junit-jupiter:2.0.5") //(7)!
        testImplementation("org.testcontainers:testcontainers:2.0.5")
    }
    ```

    1.  `GenerateTask` — тип задачи плагина, через который объявляется задача генерации.
    2.  Реализация генератора Kora, загружаемая JVM `Gradle` через classpath `buildscript`.
    3.  Gradle-плагин `OpenAPI Generator`, зафиксированный на версии, под которую собрана Kora 2.0.
    4.  Контракты и аннотации декларативного HTTP-клиента.
    5.  Реализация транспорта `OkHttp`, которая фактически выполняет запросы.
    6.  Все еще нужен, потому что это приложение также отдает собственную сводную конечную точку проверки.
    7.  Используется только тестами, чтобы поднять OpenAPI-сервер в контейнере.

!!! warning "Демон `Gradle` должен работать на JDK 25 или новее"

    `io.koraframework:openapi-generator` загружается JVM `Gradle`, а не приложением, поэтому сам демон `Gradle` должен работать на `JDK 25` или новее.
    Одного `toolchain` проекта недостаточно, а несоответствие проявляется как `UnsupportedClassVersionError` во время задачи генерации, еще до компиляции кода проекта.

На этом шаге полезно заметить, что изменилось относительно [HTTP-клиента](http-client.md):

- нам больше не нужен написанный вручную `UserApiClient`
- мы добавили генератор OpenAPI, чтобы интерфейс клиента создавался по контракту
- мы сохраняем обычные зависимости клиента и сервера, потому что приложение остается настоящим запускаемым сервисом Kora

Сам граф приложения вообще не меняется: `OkHttpClientModule` дает транспорт, `JsonModule` дает мапперы, а сгенерированный интерфейс клиента попадает в граф сам.

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/io/koraframework/guide/openapi/httpclient/Application.java`:

    ```java
    package io.koraframework.guide.openapi.httpclient;

    import io.koraframework.application.graph.KoraApplication;
    import io.koraframework.common.annotation.KoraApp;
    import io.koraframework.config.hocon.HoconConfigModule;
    import io.koraframework.http.client.ok.OkHttpClientModule;
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule;
    import io.koraframework.json.common.JsonModule;
    import io.koraframework.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            OkHttpClientModule,
            UndertowPublicHttpServerModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/io/koraframework/guide/openapi/httpclient/Application.kt`:

    ```kotlin
    package io.koraframework.guide.openapi.httpclient

    import io.koraframework.application.graph.KoraApplication
    import io.koraframework.common.annotation.KoraApp
    import io.koraframework.config.hocon.HoconConfigModule
    import io.koraframework.http.client.ok.OkHttpClientModule
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule
    import io.koraframework.json.common.JsonModule
    import io.koraframework.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        OkHttpClientModule,
        UndertowPublicHttpServerModule

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

## Генерация HTTP-клиента { #http-client-generation }

Подробные параметры генерации клиента описаны в разделе [OpenAPI Codegen: клиент](../documentation/openapi-codegen.md#client).

Теперь расскажем Gradle, как сгенерировать клиент по этому существующему контракту.

===! ":fontawesome-brands-java: `Java`"

    Обновите `build.gradle`:

    ```groovy
    def openApiGenerateUsersHttpClient = tasks.register("openApiGenerateUsersHttpClient", GenerateTask) {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = layout.projectDirectory.file("../kora-java-guide-openapi-http-server-app/src/main/resources/openapi/user-http-server.yaml") //(1)!
        outputDir = layout.buildDirectory.dir("generated/user-http-client")
        def corePackage = "io.koraframework.guide.openapi.httpclient.user"
        apiPackage = "${corePackage}.api"
        modelPackage = "${corePackage}.model"
        invokerPackage = "${corePackage}.invoker"
        configOptions = [
                mode              : "java-client", //(2)!
                clientConfigPrefix: "httpClient", //(3)!
        ]
    }

    sourceSets.main {
        java.srcDirs += openApiGenerateUsersHttpClient.get().outputDir
    }

    compileJava.dependsOn openApiGenerateUsersHttpClient
    ```

    1.  Ровно тот же файл контракта, по которому генерируется сервер, — не копия.
    2.  Режим генерации. `java-client` — один из четырех поддерживаемых режимов: `java-client`, `java-server`, `kotlin-client`, `kotlin-server`.
    3.  Префикс пути конфигурации для каждого клиента, сгенерированного этой задачей.

=== ":simple-kotlin: `Kotlin`"

    Обновите `build.gradle.kts`:

    ```kotlin
    val openApiGenerateUsersHttpClient = tasks.register<GenerateTask>("openApiGenerateUsersHttpClient") {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec.set(layout.projectDirectory.file("../kora-kotlin-guide-openapi-http-server-app/src/main/resources/openapi/user-http-server.yaml")) //(1)!
        outputDir.set(layout.buildDirectory.dir("generated/user-http-client"))
        val corePackage = "io.koraframework.guide.openapi.httpclient.user"
        apiPackage = "${corePackage}.api"
        modelPackage = "${corePackage}.model"
        invokerPackage = "${corePackage}.invoker"
        configOptions = mapOf(
            "mode" to "kotlin-client", //(2)!
            "clientConfigPrefix" to "httpClient", //(3)!
        )
    }

    kotlin.sourceSets.main { kotlin.srcDir(openApiGenerateUsersHttpClient.get().outputDir) }

    tasks.matching { it.name.startsWith("ksp") }.configureEach {
        dependsOn(openApiGenerateUsersHttpClient)
    }
    ```

    1.  Ровно тот же файл контракта, по которому генерируется сервер, — не копия.
    2.  Режим генерации. `kotlin-client` — один из четырех поддерживаемых режимов: `java-client`, `java-server`, `kotlin-client`, `kotlin-server`.
    3.  Префикс пути конфигурации для каждого клиента, сгенерированного этой задачей.

Эта конфигурация вводит несколько идей, которые стоит разобрать не спеша:

- `mode` выбирает **клиент**, поэтому генератор выпускает интерфейсы `@HttpClient`, а не контроллеры и делегаты
- `inputSpec` указывает на тот самый контракт OpenAPI из предыдущего руководства
- сгенерированные исходники кладутся в `build/generated/user-http-client` — это артефакт сборки, который никогда не коммитится
- `clientConfigPrefix` сообщает генератору, откуда этот клиент должен читать свою конфигурацию времени выполнения

Последний пункт спотыкает чаще всего, поэтому он заслуживает отдельного замечания.

!!! warning "Клиентскому режиму всегда нужен путь конфигурации"

    Сгенерированные клиенты — настоящие HTTP-клиенты Kora, а HTTP-клиент Kora не может существовать без секции конфигурации, содержащей как минимум его `url`. Поэтому ровно одна из двух опций обязательна:

    | Опция                | Поведение                                                                                                                                    |
    |----------------------|------------------------------------------------------------------------------------------------------------------------------------------------|
    | `clientConfig`       | Полный путь, используемый дословно для каждого клиента задачи. Подходит, когда контракт порождает один интерфейс API.                          |
    | `clientConfigPrefix` | Префикс; к нему добавляется имя сгенерированного интерфейса с **маленькой первой буквой**. Подходит для нескольких классов API.                |

    Если ни одна из них не задана для клиентского режима, генерация падает с сообщением, которое даже предлагает значение `clientConfig`, выведенное из имени файла контракта.

С `clientConfigPrefix = "httpClient"` и тегом `users`, порождающим интерфейс `UsersApi`, путь конфигурации получается `httpClient.usersApi` — со строчной `u`. Это важнее, чем кажется: секция
конфигурации, записанная как `httpClient.UsersApi`, просто не читается, клиент поднимается без `url`, и каждый вызов зависает до таймаута запроса вместо быстрого падения при старте.

Гадать путь не нужно. После успешного запуска генератор логирует каждый сгенерированный клиент вместе с точным путем конфигурации, который тот ожидает:

```text
Generated Kora OpenAPI HTTP clients and config paths:
  - UsersApi -> httpClient.usersApi (configPath)
```

## Что создает генератор { #generated-output }

Выполните:

```bash
./gradlew openApiGenerateUsersHttpClient
```

После генерации изучите:

===! ":fontawesome-brands-java: `Java`"

    - `build/generated/user-http-client/io/koraframework/guide/openapi/httpclient/user/api/UsersApi.java`
    - `build/generated/user-http-client/io/koraframework/guide/openapi/httpclient/user/api/UsersApiResponses.java`
    - `build/generated/user-http-client/io/koraframework/guide/openapi/httpclient/user/api/UsersApiClientRequestMappers.java`
    - `build/generated/user-http-client/io/koraframework/guide/openapi/httpclient/user/api/UsersApiClientResponseMappers.java`
    - `build/generated/user-http-client/io/koraframework/guide/openapi/httpclient/user/api/UsersApiGetUsersOptArgs.java`
    - `build/generated/user-http-client/io/koraframework/guide/openapi/httpclient/user/model/UserRequestTO.java`
    - `build/generated/user-http-client/io/koraframework/guide/openapi/httpclient/user/model/UserResponseTO.java`
    - `build/generated/user-http-client/io/koraframework/guide/openapi/httpclient/user/model/ErrorResponseTO.java`

=== ":simple-kotlin: `Kotlin`"

    - `build/generated/user-http-client/io/koraframework/guide/openapi/httpclient/user/api/UsersApi.kt`
    - `build/generated/user-http-client/io/koraframework/guide/openapi/httpclient/user/api/UsersApiResponses.kt`
    - `build/generated/user-http-client/io/koraframework/guide/openapi/httpclient/user/api/UsersApiClientRequestMappers.kt`
    - `build/generated/user-http-client/io/koraframework/guide/openapi/httpclient/user/api/UsersApiClientResponseMappers.kt`
    - `build/generated/user-http-client/io/koraframework/guide/openapi/httpclient/user/api/UsersApiGetUsersOptArgs.kt`
    - `build/generated/user-http-client/io/koraframework/guide/openapi/httpclient/user/model/UserRequestTO.kt`
    - `build/generated/user-http-client/io/koraframework/guide/openapi/httpclient/user/model/UserResponseTO.kt`
    - `build/generated/user-http-client/io/koraframework/guide/openapi/httpclient/user/model/ErrorResponseTO.kt`

Сгенерированный клиент вводит три важные новые абстракции.

### 1. `UsersApi` { #1-usersapi }

Это сгенерированный интерфейс, который заменяет написанный вручную `UserApiClient` из базового руководства по клиенту.

Он уже содержит:

- отображение HTTP-метода и пути
- аннотации query- и path-параметров
- аннотации тела
- мапперы ответов, по одному на каждый объявленный код статуса

Поэтому вместо того, чтобы писать транспортный контракт самим, мы наследуем его из файла OpenAPI. А поскольку он размечен `@HttpClient`, он является компонентом графа как любой другой: вы внедряете
`UsersApi` напрямую, без шага регистрации.

### 2. Сгенерированные транспортные модели { #2-generated-transport-models }

Клиент теперь использует сгенерированные транспортные модели:

- `UserRequestTO`
- `UserResponseTO`
- `ErrorResponseTO`

Эти модели относятся к контрактному слою OpenAPI. Модели `Java` — это `record` со сгенерированными читателями и писателями `@Json` плюс метод `with<Field>` на каждое поле; модели `Kotlin` — это
`data class` с обычным `copy`.

В базовом руководстве клиент переиспользовал локальные DTO. Здесь мы намеренно даем контракту OpenAPI определять и транспортные модели. Так исчезает еще одно место, где могло возникнуть расхождение.

!!! warning "Используйте именованные аргументы для сгенерированных моделей `Kotlin`"

    В сгенерированных конструкторах `Kotlin` обязательные свойства идут первыми, а каждое опциональное получает значение по умолчанию.
    Добавление одного свойства в контракт может сдвинуть позиции, и позиционный вызов вида `UserRequestTO("john@example.com", "John")` все еще компилируется, молча меняя местами два значения `String`, — и сервер сохранит email как имя.
    Создавайте сгенерированные модели именованными аргументами: `UserRequestTO(name = "John Doe", email = "john@example.com")`.

Если схема объявляет `enum`, сгенерированное перечисление хранит сырые значения контракта во вложенном классе `Constants`, потому что значения контракта часто не являются корректными идентификаторами.
Преобразуйте значения из формата передачи статическим методом `fromValue` и читайте их обратно через `getValue()` / `value`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var status = Pet.StatusEnum.fromValue("available"); //(1)!
    var wire = status.getValue(); //(2)!
    ```

    1.  Бросает `IllegalArgumentException` для значения, которого нет в контракте.
    2.  Возвращает `"available"` — значение, объявленное в контракте.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val status = Pet.StatusEnum.fromValue("available") //(1)!
    val wire = status.value //(2)!
    ```

    1.  Бросает `IllegalArgumentException` для значения, которого нет в контракте.
    2.  Возвращает `"available"` — значение, объявленное в контракте.

`Enum.valueOf` в `Java` и `enumValueOf` в `Kotlin` сопоставляют **имя сгенерированной константы**, а не значение контракта, поэтому их нельзя использовать для разбора. Эта ошибка компилируется без
проблем и падает только во время выполнения, на первой же полезной нагрузке, где значения различаются, — значение контракта `available` против константы с именем `AVAILABLE` — ровно такой случай.

### 3. `UsersApiResponses` { #3-usersapiresponses }

Это одна из самых полезных частей сгенерированного клиента.

Вместо того чтобы сводить все исходы к исключениям или одному типу тела, генератор создает типизированные обертки ответов, например:

- `CreateUserApiResponse`
- `GetUserApiResponse`
- `DeleteUserApiResponse`
- `UpdateUserApiResponse`

Значит, клиент может явно моделировать разные HTTP-исходы. Например, `getUser()` может вернуть:

- `GetUser200ApiResponse`
- `GetUser404ApiResponse`
- `GetUser500ApiResponse`

Это описательнее, чем написанный вручную клиент, который просто предполагает одно тело счастливого пути для каждого вызова.

### Как выглядит сгенерированный код { #generated-code-shape }

Здесь стоит остановиться и открыть сгенерированные файлы напрямую. После этого контрактный процесс становится гораздо конкретнее.

Вот сокращенная версия сгенерированного метода `UsersApi` для `getUser()`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient("httpClient.usersApi")
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
    @HttpClient("httpClient.usersApi")
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

Разберем, что создал генератор и почему.

`@HttpClient("httpClient.usersApi")`

Это говорит Kora, что сгенерированный интерфейс — настоящая зависимость HTTP-клиента. Kora генерирует реализацию времени выполнения, кладет ее в граф зависимостей и связывает с соответствующей секцией
конфигурации в `application.conf`. Путь — это `value` аннотации, и он в точности равен `clientConfigPrefix` плюс имя интерфейса с маленькой первой буквой.

`@HttpRoute(method = "GET", path = "/users/{userId}")`

Генератор читает операцию OpenAPI и проецирует ее в транспортную аннотацию Kora. Вам больше не нужно повторять маршрут вручную в интерфейсе клиента. Контракт OpenAPI остается источником истины, а
сгенерированный интерфейс `Java` или `Kotlin` становится транспортным представлением этого контракта.

`@Path("userId") String userId`

Path-параметр из файла OpenAPI становится обычным типизированным аргументом метода. Вместо ручной сборки URL вы работаете с нормальной сигнатурой метода, а сгенерированная реализация подставляет
значение в путь запроса.

`@ResponseCodeMapper(...)`

Это одна из самых полезных частей сгенерированного кода. Контракт говорит, что `GET /users/{userId}` может вернуть `200` с телом `UserResponseTO` и `404` / `500` с телом `ErrorResponseTO`. Поскольку
эти коды есть в файле OpenAPI, генератор создает маппер ответа для каждого из них. Во время выполнения клиент по реальному коду статуса решает, какой типизированный вариант ответа сконструировать.

Именно поэтому важно добавить `500` в файл OpenAPI. Если контракт не описывает `500`, у генератора нет причин создавать отдельную абстракцию `GetUser500ApiResponse` — а у статуса, который контракт не
упоминает, вообще нет маппера, поэтому клиент бросит `HttpClientResponseException` вместо возврата обертки.

`UsersApiResponses.GetUserApiResponse`

Тип возврата — не просто `UserResponseTO`. Это запечатанное семейство ответов, моделирующее весь транспортный контракт этой конечной точки. Так исходы API становятся явными прямо в месте вызова, а
поскольку семейство `sealed`, компилятор может проверить, что `switch` или `when` покрывает все объявленные исходы.

На практике это дает такой код:

===! ":fontawesome-brands-java: `Java`"

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
    return when (val response = usersApi.getUser(userId)) {
        is UsersApiResponses.GetUserApiResponse.GetUser200ApiResponse ->
            response.content.name
        is UsersApiResponses.GetUserApiResponse.GetUser404ApiResponse ->
            "Missing user: " + response.content.message
        is UsersApiResponses.GetUserApiResponse.GetUser500ApiResponse ->
            "Server error: " + response.content.message
    }
    ```

Такой стиль — одно из главных преимуществ сгенерированных контрактных клиентов. Код, который вы пишете, отражает весь контракт API, а не только счастливый путь.

### Опциональные аргументы { #optional-arguments }

У `getUsers` три опциональных query-параметра, и передавать все три при каждом вызове шумно. Кроме полного метода генератор выпускает небольшой класс-держатель с именем `<Api><OperationId>OptArgs` —
здесь `UsersApiGetUsersOptArgs` — плюс две дополнительные перегрузки `default`: одну только с обязательными параметрами и одну с обязательными параметрами плюс держателем.

===! ":fontawesome-brands-java: `Java`"

    ```java
    var allDefaults = usersApi.getUsers(); //(1)!

    var secondPage = usersApi.getUsers(UsersApiGetUsersOptArgs.defaults() //(2)!
        .withPage(1)); //(3)!
    ```

    1.  Каждый опциональный параметр отправляется как `null`.
    2.  `defaults()` стартует со значений по умолчанию из контракта (`page = 0`, `size = 10`, `sort = name`); `empty()` стартует со всех `null`.
    3.  `with...` изменяет держатель и возвращает его, поэтому вызовы можно чередовать.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val allDefaults = usersApi.getUsers() //(1)!

    val secondPage = usersApi.getUsers(UsersApiGetUsersOptArgs.defaults() //(2)!
        .withPage(1)) //(3)!
    ```

    1.  Каждый опциональный параметр отправляется как `null`.
    2.  `defaults()` стартует со значений по умолчанию из контракта (`page = 0`, `size = 10`, `sort = name`); `empty()` стартует со всех `null`.
    3.  `with...` изменяет держатель и возвращает его, поэтому вызовы можно чередовать.

Обратите внимание на асимметрию с серверной стороной: `defaults()` — это то место, где значения `default` из OpenAPI действительно применяются, и применяет их именно **клиент**, отправляя явные
значения. Сгенерированный сервер по-прежнему получает `null` для отсутствующего параметра.

### Слои генератора { #generator-layers }

На первый взгляд сгенерированный код может казаться более многословным, чем ручной интерфейс. Но у каждого сгенерированного слоя есть четкая роль:

- `UsersApi` определяет вызываемую поверхность клиента
- параметры методов представляют транспортные входы — path- и query-значения
- сгенерированные модели вроде `UserRequestTO` и `UserResponseTO` представляют полезные нагрузки OpenAPI
- сгенерированные обертки ответов моделируют допустимые HTTP-исходы
- `UsersApiClientRequestMappers` и `UsersApiClientResponseMappers` преобразуют между сырым HTTP и этими типизированными вариантами

Так что генератор выпускает лишний код не ради красоты. Он превращает транспортный контракт в явные типизированные абстракции, с которыми вам помогает работать компилятор.

Общая модель ошибок тоже важна. Поскольку контракт определяет `ErrorResponseTO(message)`, сгенерированный клиент может обращаться с ответами об ошибках как со структурированными транспортными данными,
а не только как с кодами статусов.

## Сгенерированный клиент { #generated-client }

Клиентское приложение сохраняет ту же учебную форму, что и в [HTTP-клиенте](http-client.md):

- один сгенерированный клиент
- один небольшой сводный контроллер
- одно место для ручного запуска потока

Но теперь `ClientTestController` зависит от `UsersApi`, а не от написанного вручную `UserApiClient`.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/io/koraframework/guide/openapi/httpclient/controller/ClientTestController.java`:

    ```java
    package io.koraframework.guide.openapi.httpclient.controller;

    import java.util.List;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.openapi.httpclient.user.api.UsersApi;
    import io.koraframework.guide.openapi.httpclient.user.api.UsersApiResponses;
    import io.koraframework.guide.openapi.httpclient.user.model.UserRequestTO;
    import io.koraframework.guide.openapi.httpclient.user.model.UserResponseTO;
    import io.koraframework.http.common.HttpMethod;
    import io.koraframework.http.common.annotation.HttpRoute;
    import io.koraframework.http.server.common.annotation.HttpController;
    import io.koraframework.json.common.annotation.Json;

    @Component
    @HttpController
    public final class ClientTestController {

        private final UsersApi usersApi; //(1)!

        public ClientTestController(UsersApi usersApi) {
            this.usersApi = usersApi;
        }

        @HttpRoute(method = HttpMethod.POST, path = "/client/test-all-user-endpoints")
        @Json
        public TestResults testAllUserEndpoints() {
            try {
                var created = this.usersApi.createUser(new UserRequestTO("Client Demo User", "client-demo@example.com"));
                var createdUser = created instanceof UsersApiResponses.CreateUserApiResponse.CreateUser201ApiResponse create201
                        ? create201.content()
                        : null;
                boolean userCreated = createdUser != null; //(2)!

                var getUserResponse = createdUser == null ? null : this.usersApi.getUser(createdUser.id());
                boolean userFetched = getUserResponse instanceof UsersApiResponses.GetUserApiResponse.GetUser200ApiResponse getUser200
                        && createdUser.id().equals(getUser200.content().id());

                var getUsersResponse = this.usersApi.getUsers(0, 10, "name");
                var users = getUsersResponse instanceof UsersApiResponses.GetUsersApiResponse.GetUsers200ApiResponse getUsers200
                        ? getUsers200.content()
                        : List.<UserResponseTO>of();
                boolean usersListed = createdUser != null && users.stream().anyMatch(user -> user.id().equals(createdUser.id()));

                var deleteResult = createdUser == null ? null : this.usersApi.deleteUser(createdUser.id());
                boolean userDeleted = deleteResult instanceof UsersApiResponses.DeleteUserApiResponse.DeleteUser204ApiResponse; //(3)!

                boolean allTestsPassed = userCreated && userFetched && usersListed && userDeleted;
                return new TestResults(userCreated, userFetched, usersListed, userDeleted, allTestsPassed, null);
            } catch (Exception exception) {
                return new TestResults(false, false, false, false, false, exception.getMessage()); //(4)!
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

    1.  Сгенерированный интерфейс `@HttpClient`, внедряемый напрямую — без регистрации и без ручного транспортного интерфейса.
    2.  `201` — отдельный тип обертки, поэтому «создан ли пользователь» проверяется типом, а не сравнением кода статуса.
    3.  `204 No Content` — пустая запись, поэтому само ее наличие и есть утверждение.
    4.  Транспортный сбой или статус, не описанный контрактом, все равно проявляется исключением — во втором случае `HttpClientResponseException`.

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/io/koraframework/guide/openapi/httpclient/controller/ClientTestController.kt`:

    ```kotlin
    package io.koraframework.guide.openapi.httpclient.controller

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.openapi.httpclient.user.api.UsersApi
    import io.koraframework.guide.openapi.httpclient.user.api.UsersApiResponses
    import io.koraframework.guide.openapi.httpclient.user.model.UserRequestTO
    import io.koraframework.http.common.HttpMethod
    import io.koraframework.http.common.annotation.HttpRoute
    import io.koraframework.http.server.common.annotation.HttpController
    import io.koraframework.json.common.annotation.Json

    @Component
    @HttpController
    class ClientTestController(
        private val usersApi: UsersApi //(1)!
    ) {

        @HttpRoute(method = HttpMethod.POST, path = "/client/test-all-user-endpoints")
        @Json
        fun testAllUserEndpoints(): TestResults {
            return try {
                val created = usersApi.createUser(
                    UserRequestTO(name = "Client Demo User", email = "client-demo@example.com")
                )
                val createdUser =
                    if (created is UsersApiResponses.CreateUserApiResponse.CreateUser201ApiResponse) created.content else null
                val userCreated = createdUser != null //(2)!

                val getUserResponse = createdUser?.let { usersApi.getUser(it.id) }
                val userFetched =
                    getUserResponse is UsersApiResponses.GetUserApiResponse.GetUser200ApiResponse &&
                            createdUser.id == getUserResponse.content.id

                val getUsersResponse = usersApi.getUsers(0, 10, "name")
                val users =
                    if (getUsersResponse is UsersApiResponses.GetUsersApiResponse.GetUsers200ApiResponse) {
                        getUsersResponse.content
                    } else {
                        emptyList()
                    }
                val usersListed = createdUser != null && users.any { it.id == createdUser.id }

                val deleteResult = createdUser?.let { usersApi.deleteUser(it.id) }
                val userDeleted = deleteResult is UsersApiResponses.DeleteUserApiResponse.DeleteUser204ApiResponse //(3)!

                val allTestsPassed = userCreated && userFetched && usersListed && userDeleted
                TestResults(userCreated, userFetched, usersListed, userDeleted, allTestsPassed, null)
            } catch (e: Exception) {
                TestResults(false, false, false, false, false, e.message) //(4)!
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

    1.  Сгенерированный интерфейс `@HttpClient`, внедряемый напрямую — без регистрации и без ручного транспортного интерфейса.
    2.  `201` — отдельный тип обертки, поэтому «создан ли пользователь» проверяется типом, а не сравнением кода статуса.
    3.  `204 No Content` — пустой класс, поэтому само его наличие и есть утверждение.
    4.  Транспортный сбой или статус, не описанный контрактом, все равно проявляется исключением — во втором случае `HttpClientResponseException`.

Вызовы клиента **синхронные**: `usersApi.getUser(...)` возвращает обертку ответа напрямую. Реактивных и `suspend`-режимов генерации клиента в Kora 2.0 нет, а метод контроллера, вызывающий клиент, сам
синхронный и выполняется на виртуальном потоке Undertow, который несет запрос.

## Конфигурация { #config }

Поскольку сгенерированный клиент создан с `clientConfigPrefix = "httpClient"`, а сгенерированный интерфейс называется `UsersApi`, его конфигурация времени выполнения живет по пути
`httpClient.usersApi` — с маленькой первой буквой.

Обновите `src/main/resources/application.conf`:

Полное описание конфигурации смотрите в [HTTP-сервер](../documentation/http-server.md#configuration), [HTTP-клиент](../documentation/http-client.md#configuration) и [Логирование SLF4J](../documentation/logging-slf4j.md).

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
      port = 8081 //(1)!
      system.port = 8086 //(2)!
      telemetry.logging.enabled = true //(3)!
    }

    httpClient {
      usersApi { //(4)!
        url = "http://localhost:8080" //(5)!
        url = ${?PUBLIC_API_URL} //(6)!
        requestTimeout = 10s //(7)!
      }
      telemetry.logging.enabled = true //(8)!
    }

    logging {
      levels {
        "ROOT": "INFO" //(9)!
        "io.koraframework": "INFO" //(10)!
        "io.koraframework.guide.openapi.httpclient": "INFO" //(11)!
      }
    }
    ```

    1.  Это приложение работает рядом с серверным, поэтому использует другой публичный порт.
    2.  И другой системный порт по той же причине.
    3.  Включает логирование запросов публичного HTTP-сервера (по умолчанию: `false`).
    4.  Имя сгенерированного интерфейса с **маленькой первой буквой**. `UsersApi` здесь читаться не будет.
    5.  Базовый URL приложения OpenAPI-сервера.
    6.  Необязательное переопределение из переменной окружения `PUBLIC_API_URL`, которую задает тест на контейнерах.
    7.  Максимальное время на один запрос клиента.
    8.  Включает логирование запросов клиента (по умолчанию: `false`).
    9.  Уровень логирования корневого логгера.
    10. Уровень логирования логгеров фреймворка Kora.
    11. Уровень логирования пакета приложения.

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      port: 8081 #(1)!
      system:
        port: 8086 #(2)!
      telemetry:
        logging:
          enabled: true #(3)!
    httpClient:
      usersApi: #(4)!
        url: "http://localhost:8080" #(5)!
        requestTimeout: 10s #(6)!
      telemetry:
        logging:
          enabled: true #(7)!
    logging:
      levels:
        ROOT: "INFO" #(8)!
        "io.koraframework": "INFO" #(9)!
        "io.koraframework.guide.openapi.httpclient": "INFO" #(10)!
    ```

    1.  Это приложение работает рядом с серверным, поэтому использует другой публичный порт.
    2.  И другой системный порт по той же причине.
    3.  Включает логирование запросов публичного HTTP-сервера (по умолчанию: `false`).
    4.  Имя сгенерированного интерфейса с **маленькой первой буквой**. `UsersApi` здесь читаться не будет.
    5.  Базовый URL приложения OpenAPI-сервера.
    6.  Максимальное время на один запрос клиента.
    7.  Включает логирование запросов клиента (по умолчанию: `false`).
    8.  Уровень логирования корневого логгера.
    9.  Уровень логирования логгеров фреймворка Kora.
    10. Уровень логирования пакета приложения.

Этот шаг вводит тонкую, но важную идею.

В руководстве по ручному клиенту вы сами решали, какой путь конфигурации указать в `@HttpClient(...)`. Здесь эту аннотацию за вас решает генератор, исходя из `clientConfigPrefix` и имени
сгенерированного API. Поэтому если во время выполнения что-то «не находится», первым делом стоит посмотреть, какой путь конфигурации на самом деле объявлен в сгенерированном интерфейсе — или просто
прочитать его в логе генератора.

Остальные опции клиента — блоки по операциям, названные по `operationId`, настройки соединения, телеметрия — ведут себя ровно так же, как для написанного вручную клиента, и описаны в
[HTTP-клиенте](../documentation/http-client.md#configuration).

## Проверка приложения { #check-app }

Если хотите проверить поток вручную, запустите оба приложения в разных терминалах.

### Терминал 1: OpenAPI-сервер { #terminal-1-openapi-server }

Из приложения OpenAPI-сервера предыдущего руководства:

```bash
./gradlew run
```

Это приложение отдает:

- API пользователей на `http://localhost:8080`
- `/openapi`
- `/swagger-ui`

### Терминал 2: OpenAPI-клиент { #terminal-2-openapi-client }

Из этого клиентского приложения:

```bash
./gradlew run
```

Это приложение отдает свою сводную конечную точку проверки на `http://localhost:8081/client/test-all-user-endpoints`.

Теперь запустите весь клиентский сценарий:

```bash
curl -X POST http://localhost:8081/client/test-all-user-endpoints
```

Ожидаемый результат: JSON-объект, в котором `allTestsPassed` равно `true`.

Если вместо этого вызов зависает на время `requestTimeout` и затем сообщает об ошибке, первым подозреваемым становится имя секции конфигурации: клиент, чей путь конфигурации не совпал, вообще не читает
`url`.

## Тестирование { #testing }

Ручные запуски в двух терминалах хороши для изучения, но настоящая проверка — автоматическая. Приложение из руководства направляет сгенерированный клиент на копию OpenAPI-сервера в контейнере, поэтому
тест прогоняет реальный контракт с обеих сторон.

Сначала небольшое описание контейнера, который собирает собственный `Dockerfile` серверного приложения и ждет его пробу готовности:

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/test/java/io/koraframework/guide/openapi/httpclient/AppContainer.java`:

    ```java
    package io.koraframework.guide.openapi.httpclient;

    import java.net.URI;
    import java.nio.file.Path;
    import java.time.Duration;
    import org.testcontainers.containers.GenericContainer;
    import org.testcontainers.containers.wait.strategy.Wait;
    import org.testcontainers.images.builder.ImageFromDockerfile;

    final class AppContainer extends GenericContainer<AppContainer> {

        AppContainer() {
            super(new ImageFromDockerfile("guide-openapi-http-server-black-box")
                    .withDockerfile(Path.of("../kora-java-guide-openapi-http-server-app/Dockerfile")));

            withExposedPorts(8080, 8085);
            withStartupTimeout(Duration.ofSeconds(30));
            waitingFor(Wait.forHttp("/system/readiness").forPort(8085).forStatusCode(200)); //(1)!
        }

        URI getURI() {
            return URI.create("http://" + getHost() + ":" + getMappedPort(8080));
        }
    }
    ```

    1.  Проба готовности находится на системном порту, поэтому тест стартует только после полного подъема графа.

    Образ собирается из дистрибутива серверного модуля, поэтому задача тестов должна от него зависеть:

    ```groovy
    test {
        dependsOn ":guides:java:kora-java-guide-openapi-http-server-app:distTar"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/test/kotlin/io/koraframework/guide/openapi/httpclient/AppContainer.kt`:

    ```kotlin
    package io.koraframework.guide.openapi.httpclient

    import org.testcontainers.containers.GenericContainer
    import org.testcontainers.containers.wait.strategy.Wait
    import org.testcontainers.images.builder.ImageFromDockerfile
    import java.net.URI
    import java.nio.file.Path
    import java.time.Duration

    class AppContainer : GenericContainer<AppContainer>(
        ImageFromDockerfile("guide-kotlin-openapi-http-server-black-box")
            .withDockerfile(Path.of("../kora-kotlin-guide-openapi-http-server-app/Dockerfile"))
    ) {
        init {
            withExposedPorts(8080, 8085)
            withStartupTimeout(Duration.ofSeconds(30))
            waitingFor(Wait.forHttp("/system/readiness").forPort(8085).forStatusCode(200)) //(1)!
        }

        fun getURI(): URI = URI.create("http://$host:${getMappedPort(8080)}")
    }
    ```

    1.  Проба готовности находится на системном порту, поэтому тест стартует только после полного подъема графа.

    Образ собирается из дистрибутива серверного модуля, поэтому задача тестов должна от него зависеть:

    ```kotlin
    tasks.test {
        dependsOn(":guides:kotlin:kora-kotlin-guide-openapi-http-server-app:distTar")
    }
    ```

Затем сам тест. Порт контейнера случайный, поэтому `KoraAppTestConfigModifier` подставляет реальный URI в переопределение `PUBLIC_API_URL`, которое `application.conf` уже читает:

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/test/java/io/koraframework/guide/openapi/httpclient/OpenApiHttpClientAppTest.java`:

    ```java
    package io.koraframework.guide.openapi.httpclient;

    import static org.junit.jupiter.api.Assertions.assertEquals;
    import static org.junit.jupiter.api.Assertions.assertInstanceOf;
    import static org.junit.jupiter.api.Assertions.assertNotNull;

    import java.util.UUID;
    import org.junit.jupiter.api.Test;
    import org.testcontainers.junit.jupiter.Container;
    import org.testcontainers.junit.jupiter.Testcontainers;
    import io.koraframework.guide.openapi.httpclient.user.api.UsersApi;
    import io.koraframework.guide.openapi.httpclient.user.api.UsersApiResponses;
    import io.koraframework.guide.openapi.httpclient.user.model.UserRequestTO;
    import io.koraframework.test.extension.junit5.KoraAppTest;
    import io.koraframework.test.extension.junit5.KoraAppTestConfigModifier;
    import io.koraframework.test.extension.junit5.KoraConfigModification;
    import io.koraframework.test.extension.junit5.TestComponent;

    @Testcontainers
    @KoraAppTest(Application.class)
    class OpenApiHttpClientAppTest implements KoraAppTestConfigModifier {

        @Container
        static final AppContainer APP = new AppContainer();

        @TestComponent
        private UsersApi usersApi; //(1)!

        @Override
        public KoraConfigModification config() {
            return KoraConfigModification.ofResourceFile("application.conf")
                    .withSystemProperty("PUBLIC_API_URL", APP.getURI().toString()); //(2)!
        }

        @Test
        void createUserReturnsCreatedUserFromContainerizedOpenApiHttpServerApp() {
            String unique = UUID.randomUUID().toString().substring(0, 8);
            var response = this.usersApi.createUser(new UserRequestTO("Client User " + unique, "client-" + unique + "@example.com"));
            var create201 = assertInstanceOf(UsersApiResponses.CreateUserApiResponse.CreateUser201ApiResponse.class, response);

            assertNotNull(create201.content());
            assertEquals("Client User " + unique, create201.content().name());
        }

        @Test
        void getMissingUserReturnsNotFoundResponseFromContainerizedOpenApiHttpServerApp() {
            var response = this.usersApi.getUser("999999");
            assertInstanceOf(UsersApiResponses.GetUserApiResponse.GetUser404ApiResponse.class, response); //(3)!
        }
    }
    ```

    1.  Сгенерированный клиент разрешается из настоящего графа, поэтому тест покрывает и привязку конфигурации.
    2.  Порт контейнера назначается во время выполнения, поэтому URL подставляется, а не задается жестко.
    3.  `404` здесь — обычное возвращаемое значение, а не исключение; именно это делает сгенерированные обертки приятными для проверок.

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/test/kotlin/io/koraframework/guide/openapi/httpclient/OpenApiHttpClientAppTest.kt`:

    ```kotlin
    package io.koraframework.guide.openapi.httpclient

    import org.junit.jupiter.api.Assertions.assertEquals
    import org.junit.jupiter.api.Assertions.assertInstanceOf
    import org.junit.jupiter.api.Assertions.assertNotNull
    import org.junit.jupiter.api.Test
    import org.testcontainers.junit.jupiter.Container
    import org.testcontainers.junit.jupiter.Testcontainers
    import io.koraframework.guide.openapi.httpclient.user.api.UsersApi
    import io.koraframework.guide.openapi.httpclient.user.api.UsersApiResponses
    import io.koraframework.guide.openapi.httpclient.user.model.UserRequestTO
    import io.koraframework.test.extension.junit5.KoraAppTest
    import io.koraframework.test.extension.junit5.KoraAppTestConfigModifier
    import io.koraframework.test.extension.junit5.KoraConfigModification
    import io.koraframework.test.extension.junit5.TestComponent
    import java.util.UUID

    @Testcontainers
    @KoraAppTest(Application::class)
    class OpenApiHttpClientAppTest : KoraAppTestConfigModifier {

        @TestComponent
        lateinit var usersApi: UsersApi //(1)!

        override fun config(): KoraConfigModification =
            KoraConfigModification.ofResourceFile("application.conf")
                .withSystemProperty("PUBLIC_API_URL", APP.getURI().toString()) //(2)!

        @Test
        fun createUserReturnsCreatedUserFromContainerizedOpenApiHttpServerApp() {
            val unique = UUID.randomUUID().toString().substring(0, 8)
            val response = usersApi.createUser(
                UserRequestTO(name = "Client User $unique", email = "client-$unique@example.com")
            )
            val create201 =
                assertInstanceOf(UsersApiResponses.CreateUserApiResponse.CreateUser201ApiResponse::class.java, response)

            assertNotNull(create201.content)
            assertEquals("Client User $unique", create201.content.name)
        }

        @Test
        fun getMissingUserReturnsNotFoundResponseFromContainerizedOpenApiHttpServerApp() {
            val response = usersApi.getUser("999999")
            assertInstanceOf(UsersApiResponses.GetUserApiResponse.GetUser404ApiResponse::class.java, response) //(3)!
        }

        companion object {
            @Container
            @JvmStatic
            val APP: AppContainer = AppContainer()
        }
    }
    ```

    1.  Сгенерированный клиент разрешается из настоящего графа, поэтому тест покрывает и привязку конфигурации.
    2.  Порт контейнера назначается во время выполнения, поэтому URL подставляется, а не задается жестко.
    3.  `404` здесь — обычное возвращаемое значение, а не исключение; именно это делает сгенерированные обертки приятными для проверок.

Выполните:

```bash
./gradlew test
```

Эти тесты проверяют тот же базовый поток, что и руководство по ручному клиенту, — создание пользователя, получение пользователя, отсутствующий пользователь, список с пагинацией и сортировкой, удаление
пользователя. Так сравнение двух руководств становится наглядным:

- [HTTP-клиент](http-client.md) доказывает поток написанным вручную декларативным клиентом
- это руководство доказывает тот же поток сгенерированным клиентом OpenAPI

## Лучшие практики { #best-practices }

- По возможности переиспользуйте один и тот же контракт OpenAPI между сервером и клиентом; публикуйте его как общий артефакт, как только приложения окажутся в разных репозиториях.
- Считайте сгенерированный код артефактом сборки, а не кодом приложения, который вы правите или коммитите.
- Держите прикладную логику вне сгенерированного клиента — в своих классах контроллеров или сервисов.
- Читайте лог генератора, чтобы подтвердить путь конфигурации клиента, а не угадывать регистр букв.
- Преобразуйте значения перечислений через `fromValue`, никогда через `Enum.valueOf` / `enumValueOf`.
- В `Kotlin` всегда создавайте сгенерированные модели именованными аргументами.
- Оставляйте одну небольшую сводную конечную точку проверки для учебных сценариев вместо пересборки полноценного сервера внутри клиентского приложения.

## Итоги { #summary }

Вы взяли самостоятельное клиентское приложение из [HTTP-клиента в Kora](http-client.md) и пересобрали его транспортный слой в контрактном стиле:

- клиент теперь использует тот же контракт `user-http-server.yaml`, что и руководство по OpenAPI-серверу
- Kora генерирует `UsersApi` по этому общему контракту
- сгенерированные транспортные модели заменили написанные вручную DTO клиента
- сгенерированные обертки ответов сделали множественные HTTP-исходы явными
- клиентское приложение сохранило тот же простой сводный поток проверки

Так само приложение осталось знакомым, но транспортный контракт теперь общий с сервером, а не написан отдельно вручную.

## Ключевые понятия { #key-concepts }

- контрактный клиент лучше всего работает, когда переиспользует ровно тот же файл OpenAPI, что и сервер
- Kora генерирует типизированный HTTP-клиент по OpenAPI в двух клиентских режимах: `java-client` и `kotlin-client`
- клиентскому режиму нужен `clientConfig` или `clientConfigPrefix`, и форма с префиксом делает первую букву имени API строчной
- сгенерированные обертки вроде `GetUserApiResponse` и `DeleteUserApiResponse` делают HTTP-исходы явными
- добавление `500` в файл OpenAPI порождает и отдельные варианты `500`; необъявленный статус приводит к `HttpClientResponseException`
- держатели `<Api><Operation>OptArgs` сохраняют читаемость вызовов, когда у операции много опциональных параметров
- сгенерированные перечисления разбираются через `fromValue`, а сгенерированные модели `Kotlin` безопаснее создавать именованными аргументами

## Устранение неполадок { #troubleshooting }

**Генерация падает с «Missing OpenAPI generator `clientConfig`»:**

- Клиентскому режиму нужен путь конфигурации. Задайте в `configOptions` либо `clientConfigPrefix`, либо `clientConfig`.
- Сообщение об ошибке предлагает значение `clientConfig`, выведенное из имени файла контракта, и обычно это правильная форма.

**Генерация падает с «Invalid OpenAPI generator `mode`»:**

- Kora 2.0 поддерживает ровно четыре режима: `java-client`, `java-server`, `kotlin-client`, `kotlin-server`.
- Реактивных и `suspend`-режимов клиента из прежних версий больше нет; сгенерированный клиентский код синхронный.

**Сгенерированного клиента нет в графе:**

Проверьте, что:

- задача генерации по OpenAPI выполняется до компиляции
- каталог сгенерированного вывода добавлен в основной source set
- приложение подключает транспортный модуль HTTP-клиента, например `OkHttpClientModule`

**Каждый вызов зависает до таймаута запроса:**

Это классический симптом несовпадения пути конфигурации: ни одна секция не подошла, поэтому у клиента нет `url`.

Сравните имя секции в `application.conf` со значением `@HttpClient(...)` в сгенерированном интерфейсе. С `clientConfigPrefix = "httpClient"` сгенерированный клиент ожидает:

```text
httpClient.usersApi
```

а не `httpClient.UsersApi` и не `httpClient`. Строка лога генератора после успешного запуска печатает точный ожидаемый путь.

**Значение перечисления падает во время выполнения с `IllegalArgumentException` или `no enum constant`:**

- `Enum.valueOf` / `enumValueOf` сопоставляет имя сгенерированной константы, а не значение контракта. Используйте сгенерированный метод `fromValue`.
- Поэтому сбой проявляется только на реальных полезных нагрузках: `AVAILABLE` и `available` компилируются одинаково хорошо, но по проводу приходит только одно из них.

**Вызов на `Kotlin` отправляет правильные значения не в те поля:**

В сгенерированных конструкторах `Kotlin` обязательные свойства идут первыми, поэтому позиционный вызов может скомпилироваться и все равно поменять местами два значения одного типа. Переведите такой
вызов на именованные аргументы.

**Модели клиента и сервера похожи, но не идентичны:**

Часто это означает, что клиент больше не использует написанные вручную DTO и перешел на сгенерированные транспортные модели из контракта OpenAPI. Убедитесь, что код приложения импортирует
`UserRequestTO` и `UserResponseTO` из сгенерированного пакета.

**Сборка проходит, но импорты не совпадают:**

Проверьте настройки генерации в файле сборки: `outputDir`, `apiPackage`, `modelPackage`, `invokerPackage`. Если они меняются, импорты в вашем контроллере тоже должны измениться.

**Сгенерированный клиент не отдает вариант ответа `500`:**

Сначала посмотрите в файл OpenAPI. Сгенерированные варианты ответов появляются только для кодов статусов, реально описанных в контракте. Если нужна явная обработка `500`, он должен присутствовать в
секции `responses` этой операции в общем файле OpenAPI.

**Вызов бросает `HttpClientResponseException` вместо возврата обертки:**

Сервер ответил статусом, который контракт не объявляет, поэтому ни один маппер ответа не подошел. Либо добавьте статус в контракт, либо добавьте ответ `default`, чтобы генератор сводил несовпавшие коды
в один вариант.

**Тесты на контейнерах не достучатся до серверного приложения:**

Проверьте, что:

- Docker запущен
- задача тестов зависит от `distTar` серверного модуля
- `Dockerfile` серверного модуля указывает на собственный сгенерированный дистрибутив
- `PUBLIC_API_URL` переопределяется из URI контейнера в конфигурации теста

## Что дальше? { #whats-next }

- [Устойчивые паттерны](resilient.md), чтобы сделать сгенерированные клиенты безопаснее при медленных или нестабильных зависимостях.
- [Наблюдаемость](observability.md), чтобы трассировать вызовы сгенерированного клиента и измерять исходы по статусам.
- [Продвинутый HTTP-сервер](http-server-advanced.md), а затем [Продвинутый HTTP-клиент](http-client-advanced.md), если хотите сравнить сгенерированные по контракту клиенты с написанными вручную продвинутыми.
- [Продвинутый OpenAPI HTTP-сервер](openapi-http-server-advanced.md), чтобы увидеть формы, multipart, перехватчики и авторизацию по контракту на стороне сервера.
- [gRPC-сервер](grpc-server.md), если после OpenAPI хочется изучить строго типизированный бинарный контракт.

## Помощь { #help }

Если что-то не получается:

- сравните с [Kora Java OpenAPI HTTP Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-openapi-http-client-app) и [Kora Kotlin OpenAPI HTTP Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-openapi-http-client-app)
- перечитайте [HTTP-клиент](http-client.md) про базовый ручной клиент
- перечитайте [OpenAPI HTTP-сервер](openapi-http-server.md) про контракт сервера, который потребляет этот клиент
- посмотрите [документацию OpenAPI Codegen](../documentation/openapi-codegen.md)
- посмотрите [документацию HTTP-клиента](../documentation/http-client.md)
