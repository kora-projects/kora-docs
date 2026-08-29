---
description: "Explains Kora OpenAPI code generation for HTTP clients and servers, generator modes, configuration options, generator extensions, validation, authorization and JsonNullable models. Use when working with openapi-generator, mode, clientConfig, clientConfigPrefix, securityConfigPrefix, extensions, rawBodyMode, delegateMethodBodyMode, prefixPath, requestInDelegateParams, ApiSecurity, HttpClientTokenProvider, HttpServerPrincipalExtractor, PrincipalWithScopes."
agent:
    use_when: "Use this file for Kora docs or implementation questions about Kora OpenAPI code generation for HTTP clients and servers, the four generation modes, generator configOptions, generator extensions for annotations and interceptors, server validation, generated authorization and models; key triggers include openapi-generator, java-client, java-server, kotlin-client, kotlin-server, clientConfig, clientConfigPrefix, securityConfigPrefix, extensions, rawBodyMode, delegateMethodBodyMode, prefixPath, requestInDelegateParams, ApiSecurity, HttpClientTokenProvider, HttpServerPrincipalExtractor, PrincipalWithScopes, fromValue."
---

Этот модуль генерирует код Kora из контракта `OpenAPI` с помощью [OpenAPI Generator](https://openapi-generator.tech/docs/plugins#gradle).
Из единого описания API можно создать декларативные обработчики [HTTP-сервера](http-server.md) или декларативные [HTTP-клиенты](http-client.md),
а также модели запросов и ответов, мапперы, обработку авторизации и дополнительные аннотации.
Такой подход полезен, когда `OpenAPI` является источником истины для транспортного контракта, а код приложения должен автоматически ему следовать.

Если нужен пошаговый разбор перед справочным описанием,
смотрите [OpenAPI HTTP-сервер](../guides/openapi-http-server.md), [продвинутый OpenAPI HTTP-сервер](../guides/openapi-http-server-advanced.md) и [OpenAPI HTTP-клиент](../guides/openapi-http-client.md).

## Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    Зависимость генератора в `build.gradle`:
    ```groovy
    buildscript {
        dependencies {
            classpath("io.koraframework:openapi-generator:2.0.0.RC1")
        }
    }
    ```

    Зависимость плагина в `build.gradle`:
    ```groovy
    plugins {
        id "org.openapi.generator" version "7.24.0"
    }
    ```

    Работоспособность других версий плагина не гарантируется, поскольку API `OpenAPI Generator` может быть несовместимо на уровне кода.

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) в `build.gradle.kts`:
    ```groovy
    buildscript {
        dependencies {
            classpath("io.koraframework:openapi-generator:2.0.0.RC1")
        }
    }
    ```

    Зависимость плагина в `build.gradle.kts`:
    ```groovy
    plugins {
        id("org.openapi.generator") version("7.24.0")
    }
    ```

    Работоспособность других версий плагина не гарантируется, поскольку API `OpenAPI Generator` может быть несовместимо на уровне кода.

Артефакт `io.koraframework:openapi-generator` добавляется в classpath **buildscript**, поэтому его загружает сама JVM `Gradle`, а не скомпилированное приложение.
Kora собирается под `JDK 25`, поэтому демон `Gradle` тоже должен работать на `JDK 25` или новее, иначе генерация упадёт с `UnsupportedClassVersionError` ещё до компиляции кода проекта.
Указать только `toolchain` проекта недостаточно — toolchain применяется к компиляции, а не к JVM `Gradle`.

Сгенерированному коду также требуется модуль [HTTP-сервера](http-server.md) или [HTTP-клиента](http-client.md) в зависимости от выбранного режима генерации,
а кроме того модуль [JSON](json.md) и модуль [валидации](validation.md), если включена валидация на стороне сервера.

## Конфигурация { #configuration }

Настройте параметры [плагина OpenAPI Generator](https://openapi-generator.tech/docs/plugins#gradle):

- Параметры `Gradle`-плагина описаны в [документации плагина](https://github.com/OpenAPITools/openapi-generator/blob/v7.24.0/modules/openapi-generator-gradle-plugin/README.adoc).
- Параметр плагина `configOptions` описан в [документации по конфигурации](https://openapi-generator.tech/docs/configuration/).
- Параметр плагина `openapiNormalizer` описан в [документации по настройке](https://openapi-generator.tech/docs/customization/#normalizer-opts).

Генератор Kora выбирается через `generatorName = "kora"`, а целевой артефакт — через `configOptions.mode`.
Kora поддерживает ровно четыре режима:

| Режим           | Что генерируется                                                                    |
|-----------------|------------------------------------------------------------------------------------|
| `java-client`   | Декларативные интерфейсы [HTTP-клиента](http-client.md), модели и мапперы на `Java`  |
| `java-server`   | Контроллеры [HTTP-сервера](http-server.md), контракты `delegate` и мапперы на `Java` |
| `kotlin-client` | Декларативные интерфейсы [HTTP-клиента](http-client.md), модели и мапперы на `Kotlin` |
| `kotlin-server` | Контроллеры [HTTP-сервера](http-server.md), контракты `delegate` и мапперы на `Kotlin` |

Сгенерированный код синхронный: методы клиента возвращают значение ответа, методы `delegate` — тоже.
Неизвестное значение `mode` останавливает генерацию сообщением со списком поддерживаемых режимов.

### Общие параметры `OpenAPI Generator` { #common-opts }

Помимо специфичных для Kora `configOptions`, `GenerateTask` принимает общие параметры `OpenAPI Generator`.
Они определяют, откуда читать контракт, куда помещать сгенерированные файлы, какие пакеты использовать и как предобрабатывать описание `OpenAPI`.
В проектах Kora эти параметры обычно задаются явно, поскольку сгенерированный код затем добавляется в обычную компиляцию проекта.

| Параметр            | Описание                                                                                                                                                                                                                                                                            |
|---------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `generatorName`     | Имя генератора (`обязательный`, без значения по умолчанию). Для Kora всегда указывайте `kora`.                                                                                                                                                                                      |
| `inputSpec`         | Путь к файлу `OpenAPI` (`обязательный`, без значения по умолчанию). Обычно это файл в `src/main/resources/openapi`, например `$projectDir/src/main/resources/openapi/openapi.yaml`.                                                                                                 |
| `outputDir`         | Каталог для сгенерированных файлов (по умолчанию не указан, необязательный). В проектах Kora это обычно каталог в `build`, например `$buildDir/generated/openapi`, который добавляется в основной набор исходного кода (source set).                                                |
| `apiPackage`        | Пакет для сгенерированных интерфейсов API, контроллеров, классов `delegate` и мапперов (по умолчанию: `org.openapitools.api`). Рекомендуется указывать его явно, например `io.koraframework.example.openapi.api`.                                                                   |
| `modelPackage`      | Пакет для моделей, сгенерированных из схем `OpenAPI` (по умолчанию: `org.openapitools.model`). Рекомендуется указывать его явно, например `io.koraframework.example.openapi.model`.                                                                                                 |
| `invokerPackage`    | Вспомогательный пакет генератора (по умолчанию: `org.openapitools.api`). Рекомендуется указывать его явно рядом с `apiPackage` и `modelPackage`, например `io.koraframework.example.openapi.invoker`.                                                                               |
| `configOptions`     | Специфичные для генератора параметры (по умолчанию: `{}`). Для Kora здесь задаются `mode`, `clientConfigPrefix`, `enableServerValidation`, `extensions` и другие параметры, описанные ниже.                                                                                         |
| `globalProperties`  | Ограничивает, какие сущности генерируются (по умолчанию: `{}`). Полезно, когда нужно сгенерировать только `apis`, только `models` или отдельные модели и операции. Используйте осторожно: обычным клиентам и серверам Kora, как правило, нужны классы API, модели и мапперы вместе. |
| `openapiNormalizer` | Предобрабатывает контракт `OpenAPI` перед генерацией (по умолчанию: `{}`). Часто используется, чтобы отключить стандартные преобразования через `DISABLE_ALL`, сгенерировать только выбранные операции через `FILTER` или управлять правилами вроде `SIMPLIFY_ONEOF_ANYOF`.         |
| `importMappings`    | Сопоставляет имя схемы с существующим классом (по умолчанию: `{}`). Полезно, когда модель написана вручную или приходит из другого модуля, например `Money: "com.example.Money"`.                                                                                                   |
| `typeMappings`      | Сопоставляет тип `OpenAPI Generator` с типом языка (по умолчанию: `{}`). Используется для точечной замены типов, например замены `OffsetDateTime` на специфичный для проекта тип времени.                                                                                           |
| `schemaMappings`    | Сопоставляет схему `OpenAPI` с внешним типом без генерации модели (по умолчанию: `{}`). Аналогично `importMappings`, но настраивается на уровне схемы и полезно для переиспользования общих DTO.                                                                                    |
| `skipValidateSpec`  | Пропускает валидацию контракта `OpenAPI` перед генерацией (по умолчанию: `false`). В обычных сборках валидацию лучше оставлять включённой; используйте `true` только временно для внешних контрактов, которые нельзя быстро исправить.                                              |
| `cleanupOutput`     | Очищает `outputDir` перед генерацией (по умолчанию: `false`). Полезно, когда контракт часто меняется и файлы удалённых операций или моделей должны исчезать. Не указывайте в `outputDir` каталог с написанным вручную кодом.                                                        |

Пример с общими параметрами:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    def openApiGenerateHttpClient = tasks.register("openApiGenerateHttpClient", GenerateTask) {
        generatorName = "kora"
        inputSpec = "$projectDir/src/main/resources/openapi/openapi.yaml"
        outputDir = "$buildDir/generated/openapi/client"

        def corePackage = "io.koraframework.example.openapi"
        apiPackage = "${corePackage}.api"
        modelPackage = "${corePackage}.model"
        invokerPackage = "${corePackage}.invoker"

        skipValidateSpec = false
        cleanupOutput = true
        openapiNormalizer = [
            DISABLE_ALL: "true",
            FILTER: "tag:public|billing"
        ]
        configOptions = [
            mode: "java-client",
            clientConfigPrefix: "httpClient.billing",
            filterWithModels: "true"
        ]
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    val openApiGenerateHttpClient = tasks.register<GenerateTask>("openApiGenerateHttpClient") {
        generatorName = "kora"
        inputSpec = "$projectDir/src/main/resources/openapi/openapi.yaml"
        outputDir = "$buildDir/generated/openapi/client"

        val corePackage = "io.koraframework.example.openapi"
        apiPackage = "${corePackage}.api"
        modelPackage = "${corePackage}.model"
        invokerPackage = "${corePackage}.invoker"

        skipValidateSpec = false
        cleanupOutput = true
        openapiNormalizer = mapOf(
            "DISABLE_ALL" to "true",
            "FILTER" to "tag:public|billing"
        )
        configOptions = mapOf(
            "mode" to "kotlin-client",
            "clientConfigPrefix" to "httpClient.billing",
            "filterWithModels" to "true"
        )
    }
    ```

Используйте `globalProperties` только для узких задач генерации, например при извлечении нескольких моделей в промежуточный модуль:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    globalProperties = [
        models: "User,Order",
        apis: "false",
        supportingFiles: "false"
    ]
    ```

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    globalProperties = mapOf(
        "models" to "User,Order",
        "apis" to "false",
        "supportingFiles" to "false"
    )
    ```

### Полезные правила `openapiNormalizer` { #normalizer-opts }

`openapiNormalizer` изменяет входной контракт `OpenAPI` перед генерацией. Это не параметр Kora, а общий механизм `OpenAPI Generator`.
Для Kora он особенно полезен, когда один большой контракт используется несколькими приложениями или когда контракт содержит неоднозначные для генерации кода конструкции.

| Правило                                 | Описание                                                                                                                                                                                                                                                                                                 |
|-----------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `DISABLE_ALL`                           | Отключает стандартные правила нормализации (по умолчанию: `false`). Начиная с `OpenAPI Generator 7` некоторые правила включены по умолчанию, поэтому предсказуемая генерация часто начинается с `DISABLE_ALL: "true"`, а затем явно включаются только нужные правила.                                    |
| `FILTER`                                | Оставляет для генерации только выбранные операции (по умолчанию не указано, необязательно). Поддерживает один фильтр за раз: `operationId:name1\|name2`, `method:get\|post` или `tag:public\|billing`. Операции, которые не подходят, помечаются как `x-internal: true` и не генерируются.               |
| `KEEP_ONLY_FIRST_TAG_IN_OPERATION`      | Оставляет у операции только первый тег (по умолчанию: `false`). Полезно, когда у операций несколько тегов и они разбиваются на несколько классов API не так, как вы ожидаете.                                                                                                                            |
| `SET_TAGS_FOR_ALL_OPERATIONS`           | Заменяет теги всех операций одним переданным значением (по умолчанию не указано, необязательно). Полезно, когда нужно принудительно получить один сгенерированный класс API.                                                                                                                             |
| `SET_TAGS_TO_OPERATIONID`               | Устанавливает тег операции равным `operationId`, либо `default`, если `operationId` пуст (по умолчанию: `false`). Полезно для контрактов без пригодных тегов, когда нужна предсказуемая группировка операций.                                                                                            |
| `SET_TAGS_TO_VENDOR_EXTENSION`          | Читает теги операций из указанного расширения, например `x-tags` (по умолчанию не указано, необязательно). Полезно, когда внешний контракт нельзя изменить, но в нём уже есть собственная группировка операций.                                                                                          |
| `FIX_DUPLICATED_OPERATIONID`            | Добавляет числовой суффикс к повторяющимся значениям `operationId` (по умолчанию: `false`). Лучше исправить контракт, но это правило помогает временно сгенерировать код по внешнему описанию.                                                                                                           |
| `SET_BEARER_AUTH_FOR_NAME`              | Преобразует указанную схему безопасности в `bearerAuth` (по умолчанию не указано, необязательно). Полезно для внешних контрактов, где bearer-токен описан нестандартно, но в приложении его нужно обрабатывать как обычную схему bearer.                                                                 |
| `REF_AS_PARENT_IN_ALLOF`                | Помечает `$ref` внутри `allOf` как родительскую схему через `x-parent: true` (по умолчанию: `false`). Может помочь контрактам, которые моделируют наследование через `allOf`.                                                                                                                            |
| `SIMPLIFY_ONEOF_ANYOF`                  | Упрощает некоторые конструкции `oneOf`/`anyOf`, например переносит вариант `null` в `nullable: true` и убирает одиночные обёртки (включено по умолчанию в `OpenAPI Generator 7`, если не задан `DISABLE_ALL`). Для Kora это может менять форму сгенерированных моделей, поэтому включайте его осознанно. |
| `SIMPLIFY_ANYOF_STRING_AND_ENUM_STRING` | Упрощает `anyOf`, составленный из `string` и строкового перечисления, до `string` (по умолчанию: `false`). Это может помочь с контрактами, где ограничение перечисления не важно для кода.                                                                                                               |
| `SIMPLIFY_BOOLEAN_ENUM`                 | Преобразует булево перечисление в обычный `boolean` (включено по умолчанию в `OpenAPI Generator 7`, если не задан `DISABLE_ALL`).                                                                                                                                                                        |
| `REFACTOR_ALLOF_WITH_PROPERTIES_ONLY`   | Переносит свойства из схемы, содержащей одновременно `allOf` и `properties`, в отдельную схему внутри `allOf` (включено по умолчанию в `OpenAPI Generator 7`, если не задан `DISABLE_ALL`). Это может помочь наследованию, но строгие контракты стоит проверять после генерации.                         |
| `NORMALIZE_31SPEC`                      | Нормализует некоторые конструкции `OpenAPI 3.1` в форму, которую генератор понимает лучше (по умолчанию: `false`). Полезно для контрактов `3.1`, когда генерация не удаётся на новых формах схем.                                                                                                        |
| `REMOVE_X_INTERNAL`                     | Удаляет `x-internal: true` из операций и моделей (по умолчанию: `false`). Используйте, только когда контракт уже содержит `x-internal`, но конкретная задача генерации должна принудительно вернуть такие операции.                                                                                      |
| `SET_CONTAINER_TO_NULLABLE`             | Помечает типы-контейнеры `array`, `set` или `map` как `nullable` (по умолчанию не указано, необязательно). Используйте, только когда во внешнем контракте систематически отсутствует `nullable` у таких полей.                                                                                           |
| `SET_PRIMITIVE_TYPES_TO_NULLABLE`       | Помечает примитивные типы `string`, `integer`, `number` или `boolean` как `nullable` (по умолчанию не указано, необязательно). Это существенно меняет сигнатуры моделей, поэтому применяйте его только к проблемным внешним контрактам.                                                                  |

Пример генерации только публичной части контракта:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    openapiNormalizer = [
        DISABLE_ALL: "true",
        FILTER: "tag:public|billing"
    ]
    configOptions = [
        mode: "java-client",
        clientConfigPrefix: "httpClient.billing",
        filterWithModels: "true"
    ]
    ```

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    openapiNormalizer = mapOf(
        "DISABLE_ALL" to "true",
        "FILTER" to "tag:public|billing"
    )
    configOptions = mapOf(
        "mode" to "kotlin-client",
        "clientConfigPrefix" to "httpClient.billing",
        "filterWithModels" to "true"
    )
    ```

Сам по себе `FILTER` исключает только операции. Если после фильтрации нужно также удалить неиспользуемые модели, включите параметр Kora `filterWithModels`.
Для более сложного отбора обычно создают отдельные задачи генерации с разными значениями `FILTER`, например одну с `tag:billing`, а другую с `operationId:createUser|getUser`.

Пример нормализации тегов для контракта без удобной группировки:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    openapiNormalizer = [
        DISABLE_ALL: "true",
        SET_TAGS_TO_VENDOR_EXTENSION: "x-kora-tag",
        FIX_DUPLICATED_OPERATIONID: "true"
    ]
    ```

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    openapiNormalizer = mapOf(
        "DISABLE_ALL" to "true",
        "SET_TAGS_TO_VENDOR_EXTENSION" to "x-kora-tag",
        "FIX_DUPLICATED_OPERATIONID" to "true"
    )
    ```

### Параметры моделей и тела { #model-opts }

Эти `configOptions` определяют форму сгенерированных моделей и способ обработки нетипизированных тел запроса и ответа.
Они не зависят от того, генерируется клиент или сервер.

| Параметр           | Описание                                                                                                                                                                                                                                                                                        |
|--------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `rawBodyMode`      | Тип для тела запроса или ответа, описанного как голый `type: object` без свойств (по умолчанию: `BYTES`). `BYTES` генерирует `byte[]` / `ByteArray`, `BODY` — потоковые `HttpBodyOutput` / `HttpBodyInput`, `OBJECT` — `Object` / `Any`, сериализуемый как `JSON`.                              |
| `filterWithModels` | Удаляет модели, ставшие неиспользуемыми после `openapiNormalizer.FILTER` (по умолчанию: `false`). Смотрите [Фильтрация моделей](#filter-with-models).                                                                                                                                           |
| `extensions`       | Объект `JSON` с дополнительными аннотациями моделей, перечислений, методов и типов, а также с перехватчиками (по умолчанию не указано, необязательно). Смотрите [Расширения генератора](#extensions).                                                                                           |

Мапперы `JSON` всегда связываются через `io.koraframework.json.common.annotation.Json` и генерируются процессором аннотаций [JSON](json.md),
поэтому параметр с именем аннотации не нужен.
Голый `type: object`, использованный как *свойство модели*, всегда генерируется как `Object` / `Any` независимо от `rawBodyMode` — этот параметр влияет только на тела запросов и ответов.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    configOptions = [
        mode: "java-client",
        clientConfigPrefix: "httpClient.billing",
        rawBodyMode: "BODY" //(1)!
    ]
    ```

    1. `POST /report` с `content: {application/octet-stream: {schema: {type: object}}}` превращается в `report(HttpHeaders additionalHeaders, HttpBodyOutput body)`

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    configOptions = mapOf(
        "mode" to "kotlin-client",
        "clientConfigPrefix" to "httpClient.billing",
        "rawBodyMode" to "BODY" //(1)!
    )
    ```

    1. `POST /report` с `content: {application/octet-stream: {schema: {type: object}}}` превращается в `report(additionalHeaders: HttpHeaders, body: HttpBodyOutput)`

Когда тело-голый-объект генерируется как `BYTES` или `BODY`, генератор дополнительно добавляет перед телом аргумент `@Header HttpHeaders`,
чтобы вызывающий код мог задать `Content-Type` и любые другие транспортные заголовки, которые больше нельзя вывести из контракта.

### Расширения генератора { #extensions }

`extensions` — это единый параметр в формате `JSON`, который навешивает на сгенерированный код аннотации и перехватчики.
У него три секции, все необязательные:

- `*` — применяется к каждой операции и к каждому сгенерированному типу модели и перечисления
- `tags` — ключом является имя тега `OpenAPI`, применяется к операциям этого тега
- `operations` — ключом является `operationId`, применяется к одной конкретной операции

Каждая секция принимает один и тот же набор полей:

| Поле                             | Описание                                                                                                                                                                                               |
|----------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `additionalMethodAnnotations`    | Аннотации над сгенерированными методами клиента и методами контроллера сервера. Строка или массив строк. Поддерживает подстановку `%{configPath}`.                                                     |
| `additionalTypeAnnotations`      | Аннотации на сгенерированных типах моделей и перечислений. Для аннотаций типов используется только секция `*`.                                                                                         |
| `additionalModelTypeAnnotations` | Аннотации только на сгенерированных типах моделей. Используется только секция `*`.                                                                                                                     |
| `additionalEnumTypeAnnotations`  | Аннотации только на сгенерированных типах перечислений. Используется только секция `*`.                                                                                                                |
| `interceptorType`                | Класс реализации перехватчика, подставляемый в `@InterceptWith`. Если он не указан, но задан тег, используется базовый тип `HttpClientInterceptor` / `HttpServerInterceptor`, а экземпляр выбирается по тегу. |
| `interceptorTag`                 | Класс-тег перехватчика или массив классов-тегов для `@InterceptWith(tag = ...)`.                                                                                                                        |
| `clientMapping`                  | Объект с полем `type`. Заменяет сгенерированные постатусные мапперы ответа метода клиента на `@Mapping(type)`. Только для режима клиента.                                                              |

Значение аннотации пишется ровно так, как оно выглядит в исходном коде, с полностью квалифицированным типом: `@io.koraframework.resilient.retry.annotation.Retryable(MyRetry.class)`.
Ведущий символ `@` необязателен.

`%{configPath}` заменяется на путь конфигурации сгенерированного компонента:

- для клиента — путь конфигурации `@HttpClient` этого API (смотрите [Использование клиента](#client-usage))
- для сервера — `serverConfigPrefix`, в котором `%{ControllerTypeNameInCamelCase}` заменяется на имя класса контроллера со строчной первой буквой
  (значение `serverConfigPrefix` по умолчанию — `httpServer.controller.%{ControllerTypeNameInCamelCase}`, поэтому `PetApiController` даёт `httpServer.controller.petApiController`)

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    configOptions = [
        mode: "java-server",
        extensions: """
            {
              "*": {
                "additionalModelTypeAnnotations": "@java.lang.Deprecated",
                "interceptorType": "io.koraframework.example.MyServerInterceptor"
              },
              "tags": {
                "pet": {
                  "interceptorTag": ["io.koraframework.example.PetTag"]
                }
              },
              "operations": {
                "getPetById": {
                  "additionalMethodAnnotations": "@io.koraframework.example.Audited(\\"%{configPath}\\")"
                }
              }
            }
            """
    ]
    ```

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    configOptions = mapOf(
        "mode" to "kotlin-server",
        "extensions" to """
            {
              "*": {
                "additionalModelTypeAnnotations": "@java.lang.Deprecated",
                "interceptorType": "io.koraframework.example.MyServerInterceptor"
              },
              "tags": {
                "pet": {
                  "interceptorTag": ["io.koraframework.example.PetTag"]
                }
              },
              "operations": {
                "getPetById": {
                  "additionalMethodAnnotations": "@io.koraframework.example.Audited(\"%{configPath}\")"
                }
              }
            }
            """
    )
    ```

Сгенерированные контроллеры сервера объявляются `final`, если не включён `enableServerValidation` и не заданы `additionalMethodAnnotations`;
добавление аннотации метода, опирающейся на [аспекты](general.md#terminology), автоматически делает контроллер не-`final`, чтобы аспект можно было вплести.

Некорректный `JSON` в `extensions` (или в `tags`) останавливает генерацию сообщением, показывающим ожидаемую форму и переданное значение.

### Несколько задач генерации { #multiple-gens }

В одном модуле можно зарегистрировать несколько задач `GenerateTask`, например чтобы сгенерировать два независимых контракта
или сгенерировать клиент для одного контракта и сервер для другого. Каждая задача пишет в один и тот же `outputDir` и добавляется в один и тот же набор исходного кода (source set),
поэтому единственное требование — чтобы сгенерированные пакеты не пересекались. Задайте каждой задаче собственные `apiPackage`/`modelPackage`/`invokerPackage`.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    def openApiGeneratePetV2 = tasks.register("openApiGeneratePetV2", GenerateTask) {
        generatorName = "kora"
        inputSpec = "$projectDir/src/main/resources/openapi/petstoreV2.yaml"
        outputDir = "$buildDir/generated/openapi"
        def corePackage = "io.koraframework.example.openapi.petV2" //(1)!
        apiPackage = "${corePackage}.api"
        modelPackage = "${corePackage}.model"
        invokerPackage = "${corePackage}.invoker"
        configOptions = [mode: "java-client", clientConfigPrefix: "httpClient.petV2"]
    }
    sourceSets.main { java.srcDirs += openApiGeneratePetV2.get().outputDir }
    compileJava.dependsOn openApiGeneratePetV2

    def openApiGeneratePetV3 = tasks.register("openApiGeneratePetV3", GenerateTask) {
        generatorName = "kora"
        inputSpec = "$projectDir/src/main/resources/openapi/petstoreV3.yaml"
        outputDir = "$buildDir/generated/openapi"
        def corePackage = "io.koraframework.example.openapi.petV3" //(2)!
        apiPackage = "${corePackage}.api"
        modelPackage = "${corePackage}.model"
        invokerPackage = "${corePackage}.invoker"
        configOptions = [mode: "java-client", clientConfigPrefix: "httpClient.petV3"]
    }
    sourceSets.main { java.srcDirs += openApiGeneratePetV3.get().outputDir }
    compileJava.dependsOn openApiGeneratePetV3
    ```

    1. Изолированный пакет для первого контракта
    2. Другой пакет для второго контракта, чтобы имена классов не конфликтовали

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    val openApiGeneratePetV2 = tasks.register<GenerateTask>("openApiGeneratePetV2") {
        generatorName = "kora"
        inputSpec = "$projectDir/src/main/resources/openapi/petstoreV2.yaml"
        outputDir = "$buildDir/generated/openapi/petV2"
        val corePackage = "io.koraframework.example.openapi.petV2" //(1)!
        apiPackage = "${corePackage}.api"
        modelPackage = "${corePackage}.model"
        invokerPackage = "${corePackage}.invoker"
        configOptions = mapOf("mode" to "kotlin-client", "clientConfigPrefix" to "httpClient.petV2")
    }

    val openApiGeneratePetV3 = tasks.register<GenerateTask>("openApiGeneratePetV3") {
        generatorName = "kora"
        inputSpec = "$projectDir/src/main/resources/openapi/petstoreV3.yaml"
        outputDir = "$buildDir/generated/openapi/petV3"
        val corePackage = "io.koraframework.example.openapi.petV3" //(2)!
        apiPackage = "${corePackage}.api"
        modelPackage = "${corePackage}.model"
        invokerPackage = "${corePackage}.invoker"
        configOptions = mapOf("mode" to "kotlin-client", "clientConfigPrefix" to "httpClient.petV3")
    }

    kotlin.sourceSets.main {
        kotlin.srcDir(openApiGeneratePetV2.get().outputDir)
        kotlin.srcDir(openApiGeneratePetV3.get().outputDir)
    }
    tasks.matching { it.name.startsWith("ksp") }.configureEach { //(3)!
        dependsOn(openApiGeneratePetV2, openApiGeneratePetV3)
    }
    tasks.compileKotlin { dependsOn(openApiGeneratePetV2, openApiGeneratePetV3) }
    ```

    1. Изолированный пакет для первого контракта
    2. Другой пакет для второго контракта, чтобы имена классов не конфликтовали
    3. И `KSP`, и компиляция `Kotlin` должны выполняться после генерации

## Клиент { #client }

Минимальная конфигурация плагина для создания декларативного HTTP-клиента:

===! ":fontawesome-brands-java: `Java`"

    Для клиентов `configOptions.mode` равен `java-client`.
    Остальные параметры клиента описаны ниже в разделах про авторизацию, перехватчики, теги, модели и неявные заголовки.

    ```groovy
    def openApiGenerateHttpClient = tasks.register("openApiGenerateHttpClient", GenerateTask) {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/openapi.yaml" //(1)!
        outputDir = "$buildDir/generated/openapi" //(2)!
        def corePackage = "io.koraframework.example.openapi"
        apiPackage = "${corePackage}.api" //(3)!
        modelPackage = "${corePackage}.model" //(4)!
        invokerPackage = "${corePackage}.invoker" //(5)!
        openapiNormalizer = [
            DISABLE_ALL: "true"
        ]
        configOptions = [
            mode: "java-client", //(6)!
            clientConfigPrefix: "httpClient.myclient" //(7)!
        ]
    }
    sourceSets.main { java.srcDirs += openApiGenerateHttpClient.get().outputDir } //(8)!
    compileJava.dependsOn openApiGenerateHttpClient //(9)!
    ```

    1. Путь к файлу `OpenAPI`, по которому создаются классы
    2. Каталог, где создаются сгенерированные файлы
    3. Пакет для делегатов, контроллеров и мапперов
    4. Пакет для моделей и DTO
    5. Вспомогательный пакет генератора
    6. Режим плагина
    7. Префикс пути конфигурации клиента
    8. Регистрирует сгенерированные классы как исходный код проекта
    9. Ставит компиляцию кода в зависимость от генерации классов HTTP-клиента: сначала генерация, затем компиляция

=== ":simple-kotlin: `Kotlin`"

    Для клиентов `configOptions.mode` равен `kotlin-client`.
    Остальные параметры клиента описаны ниже в разделах про авторизацию, перехватчики, теги, модели и неявные заголовки.

    ```groovy
    val openApiGenerateHttpClient = tasks.register<GenerateTask>("openApiGenerateHttpClient") {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/openapi.yaml" //(1)!
        outputDir = "$buildDir/generated/openapi" //(2)!
        val corePackage = "io.koraframework.example.openapi"
        apiPackage = "${corePackage}.api" //(3)!
        modelPackage = "${corePackage}.model" //(4)!
        invokerPackage = "${corePackage}.invoker" //(5)!
        openapiNormalizer = mapOf(
            "DISABLE_ALL" to "true"
        )
        configOptions = mapOf(
            "mode" to "kotlin-client", //(6)!
            "clientConfigPrefix" to "httpClient.myclient" //(7)!
        )
    }
    kotlin.sourceSets.main { kotlin.srcDir(openApiGenerateHttpClient.get().outputDir) } //(8)!
    tasks.matching { it.name.startsWith("ksp") }.configureEach { dependsOn(openApiGenerateHttpClient) } //(9)!
    tasks.compileKotlin { dependsOn(openApiGenerateHttpClient) }
    ```

    1. Путь к файлу `OpenAPI`, по которому создаются классы
    2. Каталог, где создаются сгенерированные файлы
    3. Пакет для делегатов, контроллеров и мапперов
    4. Пакет для моделей и DTO
    5. Вспомогательный пакет генератора
    6. Режим плагина
    7. Префикс пути конфигурации клиента
    8. Регистрирует сгенерированные классы как исходный код проекта
    9. Ставит компиляцию кода в зависимость от генерации классов HTTP-клиента: сначала генерация, затем компиляция

После генерации HTTP-клиент доступен для внедрения зависимостей через сгенерированный интерфейс.

Генерации клиента всегда нужен путь конфигурации, поэтому ровно один из этих двух параметров обязателен:

| Параметр             | Описание                                                                                                                                                                            |
|----------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `clientConfig`       | Полный путь конфигурации, используемый дословно для каждого сгенерированного клиента задачи (по умолчанию не указано, необязательно). Используйте, когда контракт даёт один интерфейс API. |
| `clientConfigPrefix` | Префикс, к которому дописывается имя сгенерированного интерфейса со строчной первой буквой (по умолчанию не указано, необязательно). Используйте, когда контракт даёт несколько классов API. |

Если для режима клиента не задан ни один из них, генерация останавливается сообщением, предлагающим значение `clientConfig`, выведенное из имени файла контракта.

### Использование клиента { #client-usage }

Для каждого тега API генератор создаёт интерфейс, аннотированный [`@HttpClient`](http-client.md), с именем по тегу (например `PetApi`).
Он внедряется в компоненты как любой другой клиент Kora, без дополнительной регистрации:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class RootService {

        private final PetApi petApi; //(1)!

        public RootService(PetApi petApi) {
            this.petApi = petApi;
        }
    }
    ```

    1. Сгенерированный интерфейс `@HttpClient`, внедряемый напрямую

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class RootService(
        private val petApi: PetApi, //(1)!
    )
    ```

    1. Сгенерированный интерфейс `@HttpClient`, внедряемый напрямую

При использовании `clientConfigPrefix` путь конфигурации — это префикс, за которым следует имя сгенерированного интерфейса **со строчной первой буквой**.
Для `clientConfigPrefix = "httpClient.petV2"` и интерфейса `PetApi` блок конфигурации — `httpClient.petV2.petApi`.
При использовании `clientConfig` значение берётся ровно так, как написано, и имя интерфейса к нему не дописывается.
После успешного запуска генератор пишет в лог каждого сгенерированного клиента вместе с его путём конфигурации — это самый быстрый способ проверить точный ключ.

Полный набор параметров клиента (`url`, `requestTimeout`, блоки для отдельных операций, `telemetry`) описан в документации по [HTTP-клиенту](http-client.md#configuration):

===! ":material-code-json: `Hocon`"

    ```javascript
    httpClient.petV2.petApi {
        url = "https://localhost:8443" //(1)!
        requestTimeout = "10s" //(2)!
        getValuesConfig { //(3)!
            requestTimeout = "20s"
        }
        telemetry.logging.enabled = true
    }
    ```

    1. Базовый URL целевого сервиса
    2. Таймаут запроса по умолчанию для всех операций
    3. Блок переопределения для отдельной операции, названный по `operationId` (здесь `getValues`)

=== ":simple-yaml: `YAML`"

    ```yaml
    httpClient:
      petV2:
        petApi:
          url: "https://localhost:8443" #(1)!
          requestTimeout: "10s" #(2)!
          getValuesConfig: #(3)!
            requestTimeout: "20s"
          telemetry:
            logging:
              enabled: true
    ```

    1. Базовый URL целевого сервиса
    2. Таймаут запроса по умолчанию для всех операций
    3. Блок переопределения для отдельной операции, названный по `operationId` (здесь `getValues`)

Каждый метод клиента возвращает обёртку `*ApiResponses` своей операции, поэтому результат разбирается по подтипу ответа:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var response = petApi.getPetById(1L);
    if (response instanceof PetApiResponses.GetPetByIdApiResponse.GetPetById200ApiResponse r) {
        return r.content(); //(1)!
    }
    return null;
    ```

    1. `content()` — это десериализованное тело ответа со статусом `200`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val response = petApi.getPetById(1L)
    return if (response is PetApiResponses.GetPetByIdApiResponse.GetPetById200ApiResponse) {
        response.content //(1)!
    } else {
        null
    }
    ```

    1. `content` — это десериализованное тело ответа со статусом `200`

### Необязательные аргументы { #client-optional-args }

Когда у операции есть необязательные параметры запроса, заголовка или cookie, перечислять их все при каждом вызове неудобно.
Помимо полного метода генератор создаёт изменяемый класс-контейнер `<Api><OperationId>OptArgs` и две дополнительные перегрузки `default`:
одну, принимающую только обязательные параметры, и одну — обязательные параметры плюс контейнер.

===! ":fontawesome-brands-java: `Java`"

    ```java
    var onlyRequired = petsApi.listPets(); //(1)!

    var withOptional = petsApi.listPets(PetsApiListPetsOptArgs.defaults() //(2)!
        .withLimit(50)); //(3)!
    ```

    1. Каждый необязательный параметр передаётся как `null`
    2. `defaults()` начинает со значений по умолчанию из контракта, `empty()` — со всех `null`
    3. `with...` изменяет контейнер и возвращает его, поэтому вызовы можно объединять в цепочку

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val onlyRequired = petsApi.listPets() //(1)!

    val withOptional = petsApi.listPets(PetsApiListPetsOptArgs.defaults() //(2)!
        .withLimit(50)) //(3)!
    ```

    1. Каждый необязательный параметр передаётся как `null`
    2. `defaults()` начинает со значений по умолчанию из контракта, `empty()` — со всех `null`
    3. `with...` изменяет контейнер и возвращает его, поэтому вызовы можно объединять в цепочку

### Авторизация клиента { #client-authorization }

Если контракт `OpenAPI` описывает `securitySchemes`, генератор создаёт в `apiPackage` модуль `ApiSecurity`, содержащий:

- по одному классу-маркеру на схему безопасности, названному по схеме из `components.securitySchemes` с заглавной первой буквой
  (`apiKeyAuth` даёт `ApiSecurity.ApiKeyAuth`, `bearerAuth` — `ApiSecurity.BearerAuth`)
- по одному классу-маркеру и одному `@DefaultComponent` `HttpClientInterceptor` на каждое различное требование безопасности, используемое операциями
- record `SecurityConfig` с читателями конфигурации `@DefaultComponent` для схем `apiKey` и `basic`
- `@InterceptWith(value = HttpClientInterceptor.class, tag = ApiSecurity.<Requirement>.class)` на каждом защищённом методе клиента

Требование безопасности, перечисляющее сразу несколько схем, даёт один общий маркер, склеенный через `And` (`ApiSecurity.Sec1AndSec2`),
а операция, допускающая несколько альтернативных требований, — один маркер, склеенный через `_` (`ApiSecurity.BearerAuth_ApiKeyAuth`).
Сгенерированный перехватчик перебирает альтернативы по порядку и использует первую, для которой каждая схема вернула непустой токен;
если ни одна не подошла, запрос отправляется без авторизации и в лог пишется предупреждение — кроме случая, когда контракт допускает анонимный доступ.

`securityConfigPrefix` задаёт префикс конфигурации сгенерированного `SecurityConfig`.
Если он не задан, префикс определяется как `clientConfigPrefix + ".security"`, затем как `clientConfig + ".security"` и в последнюю очередь как `security`.

| Параметр                      | Описание                                                                                                                                                                            |
|-------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `securityConfigPrefix`        | Префикс конфигурации сгенерированного `SecurityConfig` (по умолчанию не указано, необязательно). Смотрите порядок подстановки выше.                                                  |
| `authAsMethodArgument`        | Передаёт учётные данные аргументом метода клиента вместо генерации перехватчиков (по умолчанию: `false`). Модуль `ApiSecurity` при этом не генерируется вовсе.                        |
| `primaryAuth`                 | Имя схемы безопасности, которая становится аргументом метода, когда операция объявляет несколько (по умолчанию не указано, необязательно). Осмысленно только вместе с `authAsMethodArgument`. |
| `useSecurityDeclarationOrder` | Сохраняет порядок объявления схем внутри требования безопасности (по умолчанию: `false`). По умолчанию схемы упорядочиваются по алфавиту, поэтому `{a, b}` и `{b, a}` делят один перехватчик. |

#### apiKey и basic { #client-authorization-config }

Для схем `apiKey` и `basic` генератор создаёт читатели конфигурации `@DefaultComponent` и провайдеры токенов, поэтому не требуется никаких компонентов — только значения конфигурации.
Схема `apiKey` читает одну строку; схема `basic` читает объект `username`/`password`.
Оба значения необязательны: когда их нет, схема просто не предоставляет токен.

===! ":material-code-json: `Hocon`"

    ```javascript
    openapiAuth {
        apiKeyAuth = "MyAuthApiKey" //(1)!
        basicAuth { //(2)!
            username = "user"
            password = "password"
        }
    }
    ```

    1. Схема `apiKey` `apiKeyAuth`: значение отправляется в заголовке, параметре запроса или cookie, объявленных схемой
    2. Схема `basic` `basicAuth`: учётные данные, оборачиваемые сгенерированным `BasicAuthHttpClientTokenProvider`

=== ":simple-yaml: `YAML`"

    ```yaml
    openapiAuth:
      apiKeyAuth: "MyAuthApiKey" #(1)!
      basicAuth: #(2)!
        username: "user"
        password: "password"
    ```

    1. Схема `apiKey` `apiKeyAuth`: значение отправляется в заголовке, параметре запроса или cookie, объявленных схемой
    2. Схема `basic` `basicAuth`: учётные данные, оборачиваемые сгенерированным `BasicAuthHttpClientTokenProvider`

Путь выше соответствует `securityConfigPrefix = "openapiAuth"`:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    configOptions = [
        mode: "java-client",
        clientConfigPrefix: "httpClient.petV3",
        securityConfigPrefix: "openapiAuth"
    ]
    ```

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    configOptions = mapOf(
        "mode" to "kotlin-client",
        "clientConfigPrefix" to "httpClient.petV3",
        "securityConfigPrefix" to "openapiAuth"
    )
    ```

#### bearer и oauth { #client-authorization-token }

Для схем `bearer`, `oauth2` и `openId` генератор не знает, откуда берётся токен, поэтому ожидает компонент
[`HttpClientTokenProvider`](http-client.md#token-provider), помеченный сгенерированным классом-маркером этой схемы.
Возвращённое значение отправляется как весь заголовок `Authorization` целиком, поэтому оно должно включать префикс `Bearer `, если этого требует схема:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface ClientAuthModule {

        @Tag(ApiSecurity.BearerAuth.class) //(1)!
        default HttpClientTokenProvider bearerTokenProvider() {
            return request -> "Bearer my-token"; //(2)!
        }
    }
    ```

    1. Тег должен совпадать со сгенерированным классом-маркером схемы
    2. В реальных реализациях здесь обычно получают или обновляют токен и возвращают `null`, когда токена нет

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface ClientAuthModule {

        @Tag(ApiSecurity.BearerAuth::class) //(1)!
        fun bearerTokenProvider(): HttpClientTokenProvider {
            return HttpClientTokenProvider { "Bearer my-token" } //(2)!
        }
    }
    ```

    1. Тег должен совпадать со сгенерированным классом-маркером схемы
    2. В реальных реализациях здесь обычно получают или обновляют токен и возвращают `null`, когда токена нет

???+ warning "Провайдер нужен каждой схеме"

    Сгенерированный модуль `ApiSecurity` требует `HttpClientTokenProvider` для **каждой** схемы `bearer`, `oauth2` или `openId`,
    объявленной в `components.securitySchemes`, — даже для схем, которые приложение никогда не использует, иначе граф не соберётся.
    Такая неиспользуемая схема должна возвращать `null`, потому что перехватчик применяет первое требование, все провайдеры которого вернули токен,
    и случайное непустое значение перекрыло бы нужную вам схему.

#### Несколько схем { #client-authorization-multiple }

Когда операция объявляет несколько альтернативных требований безопасности, генератор строит один перехватчик, покрывающий их все,
и применяет первое требование, все схемы которого вернули токен — никакой отдельный параметр для этого не нужен.

Чтобы передавать учётные данные явно на каждый вызов вместо перехватчика, включите `authAsMethodArgument`.
Значение авторизации тогда становится аргументом метода клиента типа `@Nullable String` с аннотацией `@Header`, `@Query` или `@Cookie` в соответствии со схемой,
а `ApiSecurity` не генерируется вовсе. `primaryAuth` выбирает, какая схема станет этим аргументом, когда операция перечисляет несколько:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    configOptions = [
        mode: "java-client",
        clientConfigPrefix: "httpClient.petV3",
        authAsMethodArgument: "true", //(1)!
        primaryAuth: "apiKeyAuth" //(2)!
    ]
    ```

    1. Добавляет значение авторизации аргументом метода вместо генерации перехватчиков
    2. Схема, превращаемая в аргумент, когда операция перечисляет несколько

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    configOptions = mapOf(
        "mode" to "kotlin-client",
        "clientConfigPrefix" to "httpClient.petV3",
        "authAsMethodArgument" to "true", //(1)!
        "primaryAuth" to "apiKeyAuth" //(2)!
    )
    ```

    1. Добавляет значение авторизации аргументом метода вместо генерации перехватчиков
    2. Схема, превращаемая в аргумент, когда операция перечисляет несколько

Если выбранная схема отображается в заголовок `Authorization`, но операция уже объявляет явный параметр-заголовок `Authorization`,
генерация останавливается сообщением с просьбой переименовать этот параметр или отключить `authAsMethodArgument`.

### Дополнительные аннотации { #additional-contract-annotations }

`extensions.additionalMethodAnnotations` добавляет аннотации над сгенерированными методами клиента или контроллера сервера.
Их задают глобально в секции `*`, на тег контракта в секции `tags` или на `operationId` в секции `operations`, и все три уровня объединяются.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    configOptions = [
        mode: "java-client",
        clientConfigPrefix: "httpClient.petV3",
        extensions: """
            {
              "*": {
                "additionalMethodAnnotations": "@io.koraframework.example.CommonAnnotation"
              },
              "tags": {
                "pet": {
                  "additionalMethodAnnotations": ["@io.koraframework.example.PetAnnotation"]
                }
              }
            }
            """
    ]
    ```

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    configOptions = mapOf(
        "mode" to "kotlin-client",
        "clientConfigPrefix" to "httpClient.petV3",
        "extensions" to """
            {
              "*": {
                "additionalMethodAnnotations": "@io.koraframework.example.CommonAnnotation"
              },
              "tags": {
                "pet": {
                  "additionalMethodAnnotations": ["@io.koraframework.example.PetAnnotation"]
                }
              }
            }
            """
    )
    ```

Аннотации моделей и перечислений задаются через `additionalModelTypeAnnotations`, `additionalEnumTypeAnnotations` или `additionalTypeAnnotations` сразу для обоих
и читаются только из секции `*`, поскольку сгенерированная модель не привязана к одной операции.

### Перехватчики { #interceptors }

Сгенерированным методам клиента можно навесить [перехватчики](http-client.md#interceptors) через `extensions`.
`interceptorType` задаёт класс реализации, а `interceptorTag` — теги. Их можно указать вместе или указать только один из них:

- только `interceptorType` — `@InterceptWith(MyInterceptor.class)`
- только `interceptorTag` — `@InterceptWith(value = HttpClientInterceptor.class, tag = MyTag.class)`, то есть экземпляр выбирается из графа по тегу
- оба — `@InterceptWith(value = MyInterceptor.class, tag = MyTag.class)`

`interceptorTag` принимает одно имя класса или массив имён классов; массив даёт по одной аннотации `@InterceptWith` на каждый тег.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    configOptions = [
        mode: "java-client",
        clientConfigPrefix: "httpClient.petV3",
        extensions: """
            {
              "*": {
                "interceptorTag": "io.koraframework.example.MyTag"
              },
              "tags": {
                "pet": {
                  "interceptorType": "io.koraframework.example.MyInterceptor"
                },
                "shop": {
                  "interceptorType": "io.koraframework.example.MyInterceptor",
                  "interceptorTag": ["io.koraframework.example.MyTag"]
                }
              }
            }
            """
    ]
    ```

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    configOptions = mapOf(
        "mode" to "kotlin-client",
        "clientConfigPrefix" to "httpClient.petV3",
        "extensions" to """
            {
              "*": {
                "interceptorTag": "io.koraframework.example.MyTag"
              },
              "tags": {
                "pet": {
                  "interceptorType": "io.koraframework.example.MyInterceptor"
                },
                "shop": {
                  "interceptorType": "io.koraframework.example.MyInterceptor",
                  "interceptorTag": ["io.koraframework.example.MyTag"]
                }
              }
            }
            """
    )
    ```

### Теги { #tags }

Сгенерированным клиентам, аннотированным `@HttpClient`, можно передать параметры `httpClientTag` и `telemetryTag`.
Значение — это объект `JSON`, где ключ — тег API из контракта или `*` для всех сразу, а значение — объект с полями `httpClientTag` и `telemetryTag`.

Задайте `configOptions.tags`:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    configOptions = [
        mode: "java-client",
        clientConfigPrefix: "httpClient.petV3",
        tags: """
              {
                "*": {
                  "httpClientTag": "some.tag.Common",
                  "telemetryTag": "some.tag.Common"
                },
                "instrument": {
                  "httpClientTag": "some.tag.Instrument",
                  "telemetryTag": "some.tag.Instrument"
                }
              }
              """
    ]
    ```

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    configOptions = mapOf(
        "mode" to "kotlin-client",
        "clientConfigPrefix" to "httpClient.petV3",
        "tags" to """{
                        "*": {
                          "httpClientTag": "some.tag.Common",
                          "telemetryTag": "some.tag.Common"
                        },
                        "instrument": {
                          "httpClientTag": "some.tag.Instrument",
                          "telemetryTag": "some.tag.Instrument"
                        }
                     }
                     """
    )
    ```

## Неявные заголовки { #implicit-headers }

По умолчанию заголовки из операции `OpenAPI` становятся аргументами сгенерированного метода.
Если некоторые заголовки предоставляются инфраструктурой, а не кодом приложения, их можно сделать неявными.

- `implicitHeaders = true` делает неявными все заголовки из операций `OpenAPI`.
- `implicitHeadersRegex` делает неявными только заголовки, имена которых соответствуют регулярному выражению.

Неявный заголовок убирается из сигнатуры метода, но остаётся в аннотациях `OpenAPI` в сгенерированном коде
(`@io.swagger.v3.oas.annotations.Parameter(in = ParameterIn.HEADER)`).
Это сохраняет заголовок в документации контракта, не требуя от кода приложения передавать его вручную.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    configOptions = [
        mode: "java-client",
        clientConfigPrefix: "httpClient.petV3",
        implicitHeadersRegex: "X-Request-.*"
    ]
    ```

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    configOptions = mapOf(
        "mode" to "kotlin-client",
        "clientConfigPrefix" to "httpClient.petV3",
        "implicitHeadersRegex" to "X-Request-.*"
    )
    ```

## Модели { #models }

Генератор создаёт модели запросов и ответов из схем `OpenAPI`.
Модели `Java` — это типы `record` с аннотациями [`@Json`](json.md) для читателей и писателей; модели `Kotlin` — типы `data class`.
Схемы с дискриминатором дают `sealed interface`, разрешёнными подтипами которого становятся модели из маппинга.

Записи `Java` дополнительно получают по методу `with<Field>` на каждое поле, возвращающему новый экземпляр либо тот же самый, если значение не изменилось:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var updated = pet.withName("Rex"); //(1)!
    ```

    1. Возвращает сам `pet`, если `name` уже равно `"Rex"`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val updated = pet.copy(name = "Rex") //(1)!
    ```

    1. Модели `Kotlin` — это типы `data class`, поэтому используется стандартный `copy`

???+ warning "Используйте именованные аргументы в `Kotlin`"

    В сгенерированных конструкторах `Kotlin` обязательные свойства идут первыми, а каждое необязательное получает значение по умолчанию.
    Добавление свойства в контракт поэтому может сдвинуть позиции, так что создавайте модели с именованными аргументами:
    `Pet(id = 1L, name = "name", status = Pet.StatusEnum.AVAILABLE)`.

### Перечисления { #enums }

Схема `enum` превращается в сгенерированное перечисление, хранящее исходные значения контракта во вложенном классе `Constants`.
Поскольку значения контракта часто не являются корректными идентификаторами (`Dingo-Don`, `5`), перечисление создаётся из значения на проводе статическим методом `fromValue`,
а `getValue()` возвращает это значение обратно. `Enum.valueOf` работает с именем сгенерированной константы, а не со значением контракта, и для разбора использоваться не должен:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var status = Pet.StatusEnum.fromValue("available"); //(1)!
    var wire = status.getValue(); //(2)!
    ```

    1. Выбрасывает `IllegalArgumentException` для значения, которого нет в контракте
    2. Возвращает `"available"` — значение, объявленное в контракте

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val status = Pet.StatusEnum.fromValue("available") //(1)!
    val wire = status.value //(2)!
    ```

    1. Выбрасывает `IllegalArgumentException` для значения, которого нет в контракте
    2. Возвращает `"available"` — значение, объявленное в контракте

Для каждого сгенерированного перечисления генератор также создаёт `@Module` с `@DefaultComponent` `JsonReader`, `JsonWriter` и конвертерами HTTP-параметров,
поэтому перечисления работают как тела запросов, параметры запроса, параметры пути и заголовки без единого написанного вручную маппера.

### Необязательные nullable-поля { #json-nullable }

Поле, которое одновременно имеет `nullable: true` и отсутствует в списке `required`, имеет три различимых состояния:
поле отсутствует в `JSON`, поле присутствует со значением `null` и поле присутствует со значением.
Такое поле генерируется как [`JsonNullable`](json.md#jsonnullable-wrapper), чтобы эти три состояния оставались различимыми:

===! ":fontawesome-brands-java: `Java`"

    ```java
    if (request.comment().isDefined()) { //(1)!
        update(request.comment().value()); //(2)!
    }
    ```

    1. `false`, когда поле отсутствовало в теле запроса
    2. Всё ещё может быть `null`, когда поле было явно отправлено как `null`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    if (request.comment.isDefined) { //(1)!
        update(request.comment.value()) //(2)!
    }
    ```

    1. `false`, когда поле отсутствовало в теле запроса
    2. Всё ещё может быть `null`, когда поле было явно отправлено как `null`

Остальные сочетания проще:

- `required` и не `nullable` — обычное поле, не допускающее `null`
- не `required` и не `nullable` — поле с `@Nullable` в `Java`, поле типа `T?` в `Kotlin`
- `required` и `nullable` — поле `@Nullable` / `T?` с аннотацией `@JsonInclude(ALWAYS)`, поэтому `null` всегда сериализуется

### Фильтрация моделей { #filter-with-models }

`OpenAPI Generator` может фильтровать операции через `openapiNormalizer.FILTER`.
Если дополнительно включён `filterWithModels`, генератор Kora также исключает модели, ставшие неиспользуемыми после фильтрации операций.
Это полезно для больших контрактов, где приложение генерирует только часть API.

## Ответы { #responses }

Для каждой операции генератор создаёт интерфейс `<Api>Responses`, содержащий по одному типу ответа на операцию.
Когда операция объявляет несколько ответов, этот тип — `sealed interface` с одним `record` / `data class` на каждый объявленный код статуса,
названным `<OperationId><Code>ApiResponse`. Ответ с телом несёт его в `content`; объявленные заголовки ответа становятся дополнительными компонентами.
Когда операция объявляет ровно один ответ, `<OperationId>ApiResponse` сам является этой записью, без запечатанной обёртки.

Диапазоны статусов (`1XX`, `2XX`, `3XX`, `4XX`, `5XX`) и ответ `default` нельзя представить фиксированным `int`,
поэтому их записи несут первым компонентом реальный `int statusCode`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var response = petsApi.listPets();
    return switch (response) {
        case PetsApiResponses.ListPetsApiResponse.ListPets200ApiResponse r -> r.content();
        case PetsApiResponses.ListPetsApiResponse.ListPets4XXApiResponse r -> throw new IllegalStateException("Client error " + r.statusCode()); //(1)!
        case PetsApiResponses.ListPetsApiResponse.ListPets5XXApiResponse r -> throw new IllegalStateException("Server error " + r.statusCode());
    };
    ```

    1. Реальный код статуса, поскольку `4XX` покрывает целый диапазон

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val response = petsApi.listPets()
    return when (response) {
        is PetsApiResponses.ListPetsApiResponse.ListPets200ApiResponse -> response.content
        is PetsApiResponses.ListPetsApiResponse.ListPets4XXApiResponse -> throw IllegalStateException("Client error " + response.statusCode) //(1)!
        is PetsApiResponses.ListPetsApiResponse.ListPets5XXApiResponse -> throw IllegalStateException("Server error " + response.statusCode)
    }
    ```

    1. Реальный код статуса, поскольку `4XX` покрывает целый диапазон

На стороне клиента точные коды регистрируются через `@ResponseCodeMapper(code = N)`, а диапазоны и `default` направляются в один
маппер `@ResponseCodeMapper(code = ResponseCodeMapper.DEFAULT)`, который разбирается по реальному коду статуса.
Если контракт не объявляет ответ `default` и полученный статус ничему не соответствует, клиент выбрасывает `HttpClientResponseException`.

Для клиента, когда несколько ответов одной операции имеют одинаковый тип тела, генератор дополнительно создаёт общий `sealed interface`
`<OperationId><Type>ApiResponse` с `content()` и `statusCode()`, чтобы все варианты ошибок одной модели можно было обработать в одной ветке.

## Сервер { #server }

Минимальная конфигурация плагина для создания обработчиков HTTP-сервера:

===! ":fontawesome-brands-java: `Java`"

    Для серверов `configOptions.mode` равен `java-server`.
    Остальные параметры сервера описаны ниже в разделах про валидацию, классы `delegate`, перехватчики, модели и неявные заголовки.

    ```groovy
    def openApiGenerateHttpServer = tasks.register("openApiGenerateHttpServer", GenerateTask) {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/openapi.yaml" //(1)!
        outputDir = "$buildDir/generated/openapi" //(2)!
        def corePackage = "io.koraframework.example.openapi"
        apiPackage = "${corePackage}.api" //(3)!
        modelPackage = "${corePackage}.model" //(4)!
        invokerPackage = "${corePackage}.invoker" //(5)!
        openapiNormalizer = [
            DISABLE_ALL: "true"
        ]
        configOptions = [
            mode: "java-server", //(6)!
        ]
    }
    sourceSets.main { java.srcDirs += openApiGenerateHttpServer.get().outputDir } //(7)!
    compileJava.dependsOn openApiGenerateHttpServer //(8)!
    ```

    1. Путь к файлу `OpenAPI`, по которому создаются классы
    2. Каталог, где создаются сгенерированные файлы
    3. Пакет для делегатов, контроллеров и мапперов
    4. Пакет для моделей и DTO
    5. Вспомогательный пакет генератора
    6. Режим плагина
    7. Регистрирует сгенерированные классы как исходный код проекта
    8. Ставит компиляцию кода в зависимость от генерации классов HTTP-сервера: сначала генерация, затем компиляция

=== ":simple-kotlin: `Kotlin`"

    Для серверов `configOptions.mode` равен `kotlin-server`.
    Остальные параметры сервера описаны ниже в разделах про валидацию, классы `delegate`, перехватчики, модели и неявные заголовки.

    ```groovy
    val openApiGenerateHttpServer = tasks.register<GenerateTask>("openApiGenerateHttpServer") {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/openapi.yaml" //(1)!
        outputDir = "$buildDir/generated/openapi" //(2)!
        val corePackage = "io.koraframework.example.openapi"
        apiPackage = "${corePackage}.api" //(3)!
        modelPackage = "${corePackage}.model" //(4)!
        invokerPackage = "${corePackage}.invoker" //(5)!
        openapiNormalizer = mapOf(
            "DISABLE_ALL" to "true"
        )
        configOptions = mapOf(
            "mode" to "kotlin-server" //(6)!
        )
    }
    kotlin.sourceSets.main { kotlin.srcDir(openApiGenerateHttpServer.get().outputDir) } //(7)!
    tasks.matching { it.name.startsWith("ksp") }.configureEach { dependsOn(openApiGenerateHttpServer) } //(8)!
    tasks.compileKotlin { dependsOn(openApiGenerateHttpServer) }
    ```

    1. Путь к файлу `OpenAPI`, по которому создаются классы
    2. Каталог, где создаются сгенерированные файлы
    3. Пакет для делегатов, контроллеров и мапперов
    4. Пакет для моделей и DTO
    5. Вспомогательный пакет генератора
    6. Режим плагина
    7. Регистрирует сгенерированные классы как исходный код проекта
    8. Ставит компиляцию кода в зависимость от генерации классов HTTP-сервера: сначала генерация, затем компиляция

Для каждого тега API генератор создаёт `<Api>Controller` с аннотациями `@Component` и `@HttpController`, поэтому обработчики регистрируются автоматически.
Контроллер только разбирает запрос и делегирует его контракту `<Api>Delegate`, который реализует приложение.

### Валидация { #validation }

Чтобы генерировать модели и контроллеры с аннотациями из модуля [валидации](validation.md), задайте `enableServerValidation`:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    configOptions = [
        mode: "java-server",
        enableServerValidation: "true"  //(1)!
    ]
    ```

    1. Включает валидацию на стороне контроллера HTTP-сервера

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    configOptions = mapOf(
        "mode" to "kotlin-server",
        "enableServerValidation" to "true" //(1)!
    )
    ```

    1. Включает валидацию на стороне контроллера HTTP-сервера

Когда `enableServerValidation` включён, генератор помечает модели аннотацией `@Valid`, переводит ограничения схемы в аннотации валидации Kora
и добавляет `@Validate` к методам контроллера с валидируемыми параметрами.
`minimum`/`maximum` превращаются в `@Min`, `@Max` или `@Range(from, to, boundary)` в зависимости от того, сколько границ объявляет схема;
`minLength`/`maxLength` и `minItems`/`maxItems` превращаются в `@Size`; `pattern` — в `@Pattern`.

`enableServerValidationInterceptor` управляет добавлением `@InterceptWith(ValidationHttpServerInterceptor.class)`, который преобразует ошибки валидации в HTTP-ответы.
По умолчанию он считается включённым всякий раз, когда включена валидация сервера.
Значение `enableServerValidationInterceptor = "false"` сохраняет аннотации валидации, но не добавляет стандартный перехватчик —
именно это нужно, когда `ViolationException` обрабатывается вашим собственным [маппером ответа](http-server.md#custom-response).

Оба параметра читаются только в режимах сервера.

### Реализация делегата { #delegate-method-body }

Генератор сервера создаёт контроллер и контракт `delegate`, в котором пользователь реализует логику приложения.
По умолчанию `delegateMethodBodyMode = none`, поэтому методы контракта `delegate` абстрактны и должны быть реализованы приложением.

Если задано `delegateMethodBodyMode = throwException`, методы становятся `default` и выбрасывают `UnsupportedOperationException("Not yet implemented")`,
а генератор дополнительно создаёт модуль `<Api>Module` с реализацией `delegate` по умолчанию.
Этот режим полезен, когда приложение нужно собрать до того, как реализованы все операции, или когда собственные реализации подключаются постепенно.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    configOptions = [
        mode: "java-server",
        delegateMethodBodyMode: "throwException"
    ]
    ```

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    configOptions = mapOf(
        "mode" to "kotlin-server",
        "delegateMethodBodyMode" to "throwException"
    )
    ```

Добавьте сгенерированный модуль `<Api>Module` в граф приложения, чтобы реализация по умолчанию стала доступна:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends UndertowPublicHttpServerModule, JsonModule, PetApiModule { //(1)!

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

    1. Уберите сгенерированный модуль, как только приложение предоставит собственный `@Component PetApiDelegate`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : UndertowPublicHttpServerModule, JsonModule, PetApiModule //(1)!

    fun main() {
        KoraApplication.run { ApplicationGraph.graph() }
    }
    ```

    1. Уберите сгенерированный модуль, как только приложение предоставит собственный `@Component PetApiDelegate`

#### Ответы делегата { #delegate-response-types }

Каждый сгенерированный метод `delegate` возвращает запечатанную обёртку `<Api>Responses` своей операции, описанную в разделе [Ответы](#responses).
Для операции `getPetById` с ответами `200` и `404` генератор создаёт `PetApiResponses.GetPetByIdApiResponse` с подтипами
`GetPetById200ApiResponse` (несущим тело) и `GetPetById404ApiResponse`. Реализация возвращает подтип, соответствующий результату:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class PetDelegate implements PetApiDelegate {

        private final Map<Long, Pet> petMap = new ConcurrentHashMap<>();

        @Override
        public PetApiResponses.GetPetByIdApiResponse getPetById(long petId) {
            var pet = petMap.get(petId);
            if (pet == null) {
                return new PetApiResponses.GetPetByIdApiResponse.GetPetById404ApiResponse(); //(1)!
            }
            return new PetApiResponses.GetPetByIdApiResponse.GetPetById200ApiResponse(pet); //(2)!
        }

        @Override
        public PetApiResponses.AddPetApiResponse addPet(Pet body) {
            petMap.put(body.id(), body);
            return new PetApiResponses.AddPetApiResponse.AddPet200ApiResponse(body);
        }
    }
    ```

    1. Подтип статуса `404`, без тела
    2. Подтип статуса `200`, несущий тело ответа

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class PetDelegate : PetApiDelegate {

        private val petMap = ConcurrentHashMap<Long, Pet>()

        override fun getPetById(petId: Long): PetApiResponses.GetPetByIdApiResponse {
            val pet = petMap[petId]
            return if (pet == null) {
                PetApiResponses.GetPetByIdApiResponse.GetPetById404ApiResponse() //(1)!
            } else {
                PetApiResponses.GetPetByIdApiResponse.GetPetById200ApiResponse(pet) //(2)!
            }
        }

        override fun addPet(pet: Pet): PetApiResponses.AddPetApiResponse {
            petMap[pet.id] = pet
            return PetApiResponses.AddPetApiResponse.AddPet200ApiResponse(pet)
        }
    }
    ```

    1. Подтип статуса `404`, без тела
    2. Подтип статуса `200`, несущий тело ответа

Методы `delegate` в `Java` объявляют `throws Exception`, поэтому реализация может пробрасывать проверяемые исключения
и позволить [перехватчику](http-server.md#interceptors) или [мапперу ответа](http-server.md#custom-response) для исключений превратить их в ответ.

#### Исходный запрос в делегате { #request-in-delegate }

По умолчанию метод `delegate` получает только параметры, объявленные в контракте. Если реализации нужен доступ к исходному запросу
(например, чтобы прочитать инфраструктурный заголовок или удалённый адрес), включите `requestInDelegateParams`. Тогда генератор добавляет
`HttpServerRequest` первым параметром каждого метода `delegate`. Это параметр только для сервера.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    configOptions = [
        mode: "java-server",
        requestInDelegateParams: "true" //(1)!
    ]
    ```

    1. Добавляет `HttpServerRequest _serverRequest` первым аргументом каждого метода делегата

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    configOptions = mapOf(
        "mode" to "kotlin-server",
        "requestInDelegateParams" to "true" //(1)!
    )
    ```

    1. Добавляет `HttpServerRequest _serverRequest` первым аргументом каждого метода делегата

#### Префикс пути контроллера { #prefix-path }

`prefixPath` добавляет базовый путь в начало каждого маршрута сгенерированного контроллера HTTP-сервера. Это полезно, когда все операции должны обслуживаться под общим
сегментом (например `/api/v1`), которого нет в путях `OpenAPI`.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    configOptions = [
        mode: "java-server",
        prefixPath: "/api/v1" //(1)!
    ]
    ```

    1. Путь контракта `/pet/{id}` превращается в `/api/v1/pet/{id}`

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    configOptions = mapOf(
        "mode" to "kotlin-server",
        "prefixPath" to "/api/v1" //(1)!
    )
    ```

    1. Путь контракта `/pet/{id}` превращается в `/api/v1/pet/{id}`

### Перехватчики { #interceptors-2 }

Сгенерированные контроллеры, аннотированные `@HttpController`, можно также аннотировать [перехватчиками](http-server.md#interceptors) через `extensions`,
используя ровно те же поля, что и [перехватчики клиента](#interceptors).
Когда задан только `interceptorTag`, базовым типом становится `HttpServerInterceptor`, а экземпляр берётся из графа по тегу:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    configOptions = [
        mode: "java-server",
        extensions: """
            {
              "*": {
                "interceptorTag": "io.koraframework.example.MyTag"
              },
              "tags": {
                "pet": {
                  "interceptorType": "io.koraframework.example.MyInterceptor"
                },
                "shop": {
                  "interceptorType": "io.koraframework.example.MyInterceptor",
                  "interceptorTag": ["io.koraframework.example.MyTag"]
                }
              }
            }
            """
    ]
    ```

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    configOptions = mapOf(
        "mode" to "kotlin-server",
        "extensions" to """
            {
              "*": {
                "interceptorTag": "io.koraframework.example.MyTag"
              },
              "tags": {
                "pet": {
                  "interceptorType": "io.koraframework.example.MyInterceptor"
                },
                "shop": {
                  "interceptorType": "io.koraframework.example.MyInterceptor",
                  "interceptorTag": ["io.koraframework.example.MyTag"]
                }
              }
            }
            """
    )
    ```

Перехватчик, указанный через `interceptorType`, должен быть компонентом графа, поэтому объявите его через `@Component` или методом модуля.

### Авторизация { #authorization }

Когда контракт `OpenAPI` описывает `securitySchemes`, генератор сервера создаёт модуль `ApiSecurity` с одним классом-маркером на каждую схему,
названным по имени схемы из `components.securitySchemes` с заглавной первой буквой — для привычного контракта
[Basic/ApiKey/Bearer/OAuth](https://swagger.io/docs/specification/authentication/) это
`ApiSecurity.BasicAuth`, `ApiSecurity.ApiKeyAuth`, `ApiSecurity.BearerAuth` и `ApiSecurity.OAuth`.

Для каждой схемы приложение должно предоставить компонент `HttpServerPrincipalExtractor<T, P>`, помеченный соответствующим классом-маркером.
`T` — это извлекаемые учётные данные, `P` — получаемый principal.
Извлекатель получает запрос и значение учётных данных и возвращает аутентифицированный principal либо `null`, если учётные данные не приняты:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface AuthModule {

        @Tag(ApiSecurity.BearerAuth.class)
        default HttpServerPrincipalExtractor<String, Principal> bearerHttpServerPrincipalExtractor() {
            return (request, value) -> new UserPrincipal("name"); //(1)!
        }

        @Tag(ApiSecurity.BasicAuth.class)
        default HttpServerPrincipalExtractor<String, Principal> basicHttpServerPrincipalExtractor() {
            return (request, value) -> new UserPrincipal("name");
        }

        @Tag(ApiSecurity.ApiKeyAuth.class)
        default HttpServerPrincipalExtractor<String, Principal> apiKeyHttpServerPrincipalExtractor() {
            return (request, value) -> new UserPrincipal("name");
        }

        @Tag(ApiSecurity.OAuth.class)
        default HttpServerPrincipalExtractor<String, PrincipalWithScopes> oauthHttpServerPrincipalExtractor() { //(2)!
            return (request, value) -> new UserPrincipal("name");
        }
    }
    ```

    1. Возврат `null` отклоняет это требование безопасности, и сгенерированный перехватчик пробует следующее
    2. Схемы `OAuth` объявляют области доступа, поэтому извлекатель возвращает `PrincipalWithScopes`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface AuthModule {

        @Tag(ApiSecurity.BearerAuth::class)
        fun bearerHttpServerPrincipalExtractor(): HttpServerPrincipalExtractor<String, Principal> {
            return HttpServerPrincipalExtractor { _, _ -> UserPrincipal("name") } //(1)!
        }

        @Tag(ApiSecurity.BasicAuth::class)
        fun basicHttpServerPrincipalExtractor(): HttpServerPrincipalExtractor<String, Principal> {
            return HttpServerPrincipalExtractor { _, _ -> UserPrincipal("name") }
        }

        @Tag(ApiSecurity.ApiKeyAuth::class)
        fun apiKeyHttpServerPrincipalExtractor(): HttpServerPrincipalExtractor<String, Principal> {
            return HttpServerPrincipalExtractor { _, _ -> UserPrincipal("name") }
        }

        @Tag(ApiSecurity.OAuth::class)
        fun oauthHttpServerPrincipalExtractor(): HttpServerPrincipalExtractor<String, PrincipalWithScopes> { //(2)!
            return HttpServerPrincipalExtractor { _, _ -> UserPrincipal("name") }
        }
    }
    ```

    1. Возврат `null` отклоняет это требование безопасности, и сгенерированный перехватчик пробует следующее
    2. Схемы `OAuth` объявляют области доступа, поэтому извлекатель возвращает `PrincipalWithScopes`

Для `OAuth` возвращаемый principal должен реализовывать `PrincipalWithScopes`, чтобы сгенерированный перехватчик мог проверять области доступа, объявленные для каждой операции.
Аутентифицированный principal публикуется на весь запрос через `Principal.current()`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record UserPrincipal(String name) implements PrincipalWithScopes {

        @Override
        public Collection<String> scopes() {
            return List.of("read", "write"); //(1)!
        }
    }
    ```

    1. Области доступа, выданные этому principal, сверяются с областями, требуемыми операцией

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class UserPrincipal(val name: String) : PrincipalWithScopes {

        override fun scopes(): Collection<String> {
            return listOf("read", "write") //(1)!
        }
    }
    ```

    1. Области доступа, выданные этому principal, сверяются с областями, требуемыми операцией

Операция, требующая несколько схем одновременно, получает один извлекатель, типом учётных данных которого является сгенерированный record `<Tag>AuthData`,
хранящий по одной строке `String` на схему, а тег склеивает имена схем через `With` — для схем `headerAuth1` и `queryAuth` это
`@Tag(ApiSecurity.HeaderAuth1WithQueryAuth.class)` и `ApiSecurity.HeaderAuth1WithQueryAuthAuthData`.

Когда ни одно требование безопасности операции не выполнено, сгенерированный перехватчик выбрасывает `HttpServerResponseException.of(401, "Unauthorized")`.
Если контракт перечисляет среди альтернатив пустое требование (`security: [{}]`), запрос вместо этого пропускается без аутентификации.

Безопасность сервера поддерживает схемы `apiKey` в заголовке, параметре запроса или cookie, а также схемы `http` `basic`/`bearer` плюс `oauth2`/`openId`,
читаемые из заголовка `Authorization`. Любой другой тип схемы останавливает генерацию явным сообщением.

## Рекомендации { #recommendations }

???+ tip "Совет"

    Если что-то не генерируется плагином либо поведение отличается от ожидаемого или от других версий,
    внимательно проверьте [конфигурацию плагина](#configuration) и изучите настройки,
    поскольку они могут влиять на то, как генерируются классы.

    Начиная с версии плагина `7.0.0` правило `SIMPLIFY_ONEOF_ANYOF`, включённое в `openapiNormalizer` по умолчанию,
    может приводить к неочевидным результатам генерации, поэтому контракты с `oneOf`/`anyOf` обычно генерируют с `DISABLE_ALL: "true"`.

    Если сгенерированный клиент не находит свою конфигурацию, посмотрите строку лога, которую генератор печатает после успешного запуска:
    в ней перечислен каждый сгенерированный клиент вместе с точным путём конфигурации, который он ожидает.

    Генератор работает на JVM `Gradle`, поэтому `UnsupportedClassVersionError` во время задачи генерации означает, что демон `Gradle`
    запущен на более старой `JDK`, чем та, под которую собрана Kora — смотрите [Подключение](#dependency).
