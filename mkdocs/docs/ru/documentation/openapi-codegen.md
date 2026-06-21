---
description: "Explains Kora OpenAPI code generation for HTTP clients and servers, generator options, tags, validation, interceptors, authorization, and JsonNullable support. Use when working with openapi-generator, @HttpClient, @HttpController, @InterceptWith, @Tag, @Validate, JsonNullable, primaryAuth."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora OpenAPI code generation for HTTP clients and servers, generator options, tags, validation, interceptors, authorization, and JsonNullable support; key triggers include openapi-generator, @HttpClient, @HttpController, @InterceptWith, @Tag, @Validate, JsonNullable, primaryAuth."
---

Модуль генерирует код Kora по `OpenAPI`-контракту с помощью [OpenAPI Generator](https://openapi-generator.tech/docs/plugins#gradle).
Из одного описания API можно создать декларативные обработчики [HTTP-сервера](http-server.md) или декларативные [HTTP-клиенты](http-client.md),
а также модели запросов и ответов, преобразователи, обработку авторизации и дополнительные аннотации.
Такой подход удобен, когда `OpenAPI` является источником правды для транспортного контракта, а код приложения должен следовать ему автоматически.

Если нужен пошаговый разбор перед справочным описанием, смотрите [OpenAPI HTTP сервер](../guides/openapi-http-server.md), [OpenAPI HTTP сервер продвинутый](../guides/openapi-http-server-advanced.md) и [OpenAPI HTTP клиент](../guides/openapi-http-client.md).

## Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    Зависимость генератора `build.gradle`:
    ```groovy
    buildscript {
        dependencies {
            classpath("ru.tinkoff.kora:openapi-generator:1.2.16")
        }
    }
    ```

    Зависимость плагина `build.gradle`:
    ```groovy
    plugins {
        id "org.openapi.generator" version "7.14.0"
    }
    ```

    Использование других версий плагина не гарантируется, потому что API `OpenAPI Generator` может быть несовместимым на уровне кода.

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    buildscript {
        dependencies {
            classpath("ru.tinkoff.kora:openapi-generator:1.2.16")
        }
    }
    ```

    Зависимость плагина `build.gradle.kts`:
    ```groovy
    plugins {
        id("org.openapi.generator") version("7.14.0")
    }
    ```

    Использование других версий плагина не гарантируется, потому что API `OpenAPI Generator` может быть несовместимым на уровне кода.

Для сгенерированного кода также требуется подключить [HTTP-сервер](http-server.md) или [HTTP-клиент](http-client.md), в зависимости от выбранного режима генерации.

## Конфигурация { #configuration }

Конфигурировать требуется параметры [плагина OpenAPI Generator](https://openapi-generator.tech/docs/plugins#gradle):

- Настройка параметров `Gradle`-плагина в [документации](https://github.com/OpenAPITools/openapi-generator/blob/v7.14.0/modules/openapi-generator-gradle-plugin/README.adoc).
- Настройка `configOptions` параметра плагина в [документации](https://openapi-generator.tech/docs/configuration/).
- Настройка `openapiNormalizer` параметра плагина в [документации](https://openapi-generator.tech/docs/customization/#openapi-normalizer).

### Общие параметры `OpenAPI Generator` { #common-generator-options }

Помимо параметров Kora в `configOptions`, задача `GenerateTask` принимает общие параметры `OpenAPI Generator`.
Они управляют тем, откуда брать контракт, куда складывать результат, какие пакеты использовать и как предварительно обработать `OpenAPI`-описание.
Для Kora их обычно стоит задавать явно, потому что сгенерированный код затем подключается к обычной компиляции проекта.

| Параметр | Описание |
| -------- | -------- |
| `generatorName` | Имя генератора (`обязательная`, по умолчанию не указано). Для Kora всегда указывается `kora`. |
| `inputSpec` | Путь до `OpenAPI`-файла (`обязательная`, по умолчанию не указано). Обычно это файл внутри `src/main/resources/openapi`, например `$projectDir/src/main/resources/openapi/openapi.yaml`. |
| `outputDir` | Директория для сгенерированных файлов (по умолчанию не указано, необязательно). В проектах Kora обычно указывают директорию внутри `build`, например `$buildDir/generated/openapi`, и добавляют ее в исходный код основного набора исходников. |
| `apiPackage` | Пакет для сгенерированных API-интерфейсов, контроллеров, `delegate`-классов и преобразователей (по умолчанию: `org.openapitools.api`). Рекомендуется задавать явно, например `ru.tinkoff.kora.example.openapi.api`. |
| `modelPackage` | Пакет для моделей из схем `OpenAPI` (по умолчанию: `org.openapitools.model`). Рекомендуется задавать явно, например `ru.tinkoff.kora.example.openapi.model`. |
| `invokerPackage` | Вспомогательный пакет генератора (по умолчанию: `org.openapitools.api`). Рекомендуется задавать явно рядом с `apiPackage` и `modelPackage`, например `ru.tinkoff.kora.example.openapi.invoker`. |
| `configOptions` | Параметры конкретного генератора (по умолчанию: `{}`). Для Kora здесь указываются `mode`, `clientConfigPrefix`, `enableServerValidation`, `interceptors` и остальные параметры, описанные ниже в соответствующих разделах. |
| `globalProperties` | Ограничение набора создаваемых сущностей (по умолчанию: `{}`). Полезно, когда нужно сгенерировать только `apis`, только `models` или конкретные модели и операции. Используйте аккуратно: для рабочих клиентов и серверов Kora обычно нужны и API-классы, и модели, и преобразователи. |
| `openapiNormalizer` | Предварительная обработка `OpenAPI`-контракта перед генерацией (по умолчанию: `{}`). Часто используется для отключения стандартных преобразований через `DISABLE_ALL`, выборочной генерации через `FILTER` или управления правилами вроде `SIMPLIFY_ONEOF_ANYOF`. |
| `importMappings` | Сопоставление имени схемы с уже существующим классом (по умолчанию: `{}`). Полезно, когда модель уже написана вручную или приходит из отдельного модуля, например `Money: "com.example.Money"`. |
| `typeMappings` | Сопоставление типа `OpenAPI Generator` с типом языка (по умолчанию: `{}`). Используется для точечной замены типов, например `OffsetDateTime` на собственный тип времени. |
| `schemaMappings` | Сопоставление схемы `OpenAPI` с внешним типом без генерации модели (по умолчанию: `{}`). Близко к `importMappings`, но задается на уровне схем и удобно для повторного использования общих DTO. |
| `skipValidateSpec` | Пропустить проверку `OpenAPI`-контракта перед генерацией (по умолчанию: `false`). В обычной сборке лучше оставлять проверку включенной, а `true` использовать только временно для внешних контрактов, которые нельзя быстро исправить. |
| `cleanupOutput` | Очищать директорию `outputDir` перед генерацией (по умолчанию: `false`). Полезно, если контракт часто меняется и нужно убрать файлы от удаленных операций или моделей. Не направляйте `outputDir` в директорию с ручным кодом. |

Пример с общими параметрами:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    def openApiGenerateHttpClient = tasks.register("openApiGenerateHttpClient", GenerateTask) {
        generatorName = "kora"
        inputSpec = "$projectDir/src/main/resources/openapi/openapi.yaml"
        outputDir = "$buildDir/generated/openapi/client"

        def corePackage = "ru.tinkoff.kora.example.openapi"
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

        val corePackage = "ru.tinkoff.kora.example.openapi"
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

`globalProperties` лучше использовать только для узких задач генерации, например при выделении отдельных моделей в промежуточный модуль:

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

### Полезные правила `openapiNormalizer` { #openapi-normalizer }

`openapiNormalizer` изменяет входной `OpenAPI`-контракт перед генерацией. Это не параметр Kora, а общий механизм `OpenAPI Generator`,
но для Kora он особенно полезен, когда один большой контракт используется несколькими приложениями или в контракте есть неоднозначности для генерации кода.

| Правило | Описание |
| -------- | -------- |
| `DISABLE_ALL` | Отключает стандартные правила нормализации (по умолчанию: `false`). Начиная с `OpenAPI Generator 7`, часть правил включена по умолчанию, поэтому для предсказуемой генерации часто указывают `DISABLE_ALL: "true"` и затем включают только нужные правила явно. |
| `FILTER` | Оставляет в генерации только выбранные операции (по умолчанию не указано, необязательно). Поддерживает один фильтр за раз: `operationId:name1\|name2`, `method:get\|post` или `tag:public\|billing`. Операции, которые не подошли под фильтр, помечаются как `x-internal: true` и не генерируются. |
| `KEEP_ONLY_FIRST_TAG_IN_OPERATION` | Оставляет у операции только первый тег (по умолчанию: `false`). Полезно, когда операции имеют несколько тегов и из-за этого распадаются по нескольким API-классам не так, как ожидается. |
| `SET_TAGS_FOR_ALL_OPERATIONS` | Заменяет теги всех операций на одно указанное значение (по умолчанию не указано, необязательно). Удобно, если нужно принудительно получить один сгенерированный API-класс. |
| `SET_TAGS_TO_OPERATIONID` | Делает тег операции равным `operationId` или `default`, если `operationId` пустой (по умолчанию: `false`). Подходит для контрактов без нормальных тегов, когда нужно получить предсказуемое разбиение операций. |
| `SET_TAGS_TO_VENDOR_EXTENSION` | Берет теги операций из указанного расширения, например `x-tags` (по умолчанию не указано, необязательно). Полезно, когда внешний контракт нельзя менять, но в нем уже есть собственная группировка операций. |
| `FIX_DUPLICATED_OPERATIONID` | Добавляет числовой суффикс к повторяющимся `operationId` (по умолчанию: `false`). Лучше исправлять контракт, но правило помогает временно сгенерировать код для внешнего описания. |
| `SET_BEARER_AUTH_FOR_NAME` | Преобразует указанную схему авторизации в `bearerAuth` (по умолчанию не указано, необязательно). Полезно для внешних контрактов, где bearer-токен описан нестандартно, но в приложении должен обрабатываться как обычный bearer. |
| `REF_AS_PARENT_IN_ALLOF` | Помечает `$ref` внутри `allOf` как родительскую схему через `x-parent: true` (по умолчанию: `false`). Может помочь контрактам с наследованием через `allOf`. |
| `SIMPLIFY_ONEOF_ANYOF` | Упрощает часть конструкций `oneOf`/`anyOf`, например переносит `null`-вариант в `nullable: true` и убирает одиночные обертки (включено по умолчанию в `OpenAPI Generator 7`, если не указан `DISABLE_ALL`). Для Kora это может менять форму сгенерированных моделей, поэтому правило лучше включать осознанно. |
| `SIMPLIFY_ANYOF_STRING_AND_ENUM_STRING` | Упрощает `anyOf` из `string` и строкового перечисления до `string` (по умолчанию: `false`). Иногда помогает с контрактами, где ограничение перечисления не важно для кода. |
| `SIMPLIFY_BOOLEAN_ENUM` | Преобразует перечисление из булевых значений в обычный `boolean` (включено по умолчанию в `OpenAPI Generator 7`, если не указан `DISABLE_ALL`). |
| `REFACTOR_ALLOF_WITH_PROPERTIES_ONLY` | Переносит свойства из схемы с одновременными `allOf` и `properties` внутрь отдельной схемы в `allOf` (включено по умолчанию в `OpenAPI Generator 7`, если не указан `DISABLE_ALL`). Может помочь с наследованием, но для строгих контрактов лучше проверить результат генерации. |
| `NORMALIZE_31SPEC` | Нормализует часть конструкций `OpenAPI 3.1` к виду, который лучше понимает генератор (по умолчанию: `false`). Полезно для контрактов `3.1`, если генерация падает на новых формах схем. |
| `REMOVE_X_INTERNAL` | Удаляет `x-internal: true` из операций и моделей (по умолчанию: `false`). Используйте только если контракт уже содержит `x-internal`, но в конкретной генерации нужно принудительно вернуть такие операции. |
| `SET_CONTAINER_TO_NULLABLE` | Помечает контейнерные типы `array`, `set` или `map` как `nullable` (по умолчанию не указано, необязательно). Используйте только если внешний контракт системно не проставляет `nullable` для таких полей. |
| `SET_PRIMITIVE_TYPES_TO_NULLABLE` | Помечает примитивные типы `string`, `integer`, `number` или `boolean` как `nullable` (по умолчанию не указано, необязательно). Это сильно меняет сигнатуры моделей, поэтому правило лучше применять только к проблемным внешним контрактам. |

Пример выборочной генерации публичной части контракта:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    openapiNormalizer = [
        DISABLE_ALL: "true",
        FILTER: "tag:public|billing"
    ]
    configOptions = [
        mode: "java-client",
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
        "filterWithModels" to "true"
    )
    ```

`FILTER` сам исключает только операции. Если после фильтрации нужно также убрать неиспользуемые модели, включите параметр Kora `filterWithModels`.
Если нужна более сложная выборка, обычно заводят отдельные задачи генерации с разными `FILTER`, например одну по `tag:billing`, а другую по `operationId:createUser|getUser`.

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

### Общие параметры `JSON` и моделей { #common-model-options }

Kora также поддерживает несколько параметров `configOptions`, которые управляют `JSON`-преобразователями и общей генерацией моделей.
Они не зависят от того, создается клиент или сервер.

| Параметр | Описание |
| -------- | -------- |
| `jsonAnnotation` | Аннотация-тег для внедрения `JSON`-преобразователей в сгенерированные преобразователи запросов и ответов (по умолчанию: `ru.tinkoff.kora.json.common.annotation.Json`). |
| `objectType` | Тип для схем `type: object` без более точного описания. Для `Java` по умолчанию используется `java.lang.Object`, для `Kotlin` - `kotlin.Any`. Можно указать, например, `com.fasterxml.jackson.databind.JsonNode`, если приложение хочет работать с произвольным `JSON` как с деревом. |
| `disableHtmlEscaping` | Отключить экранирование HTML-символов в строках `JSON` (по умолчанию: `false`). Обычно оставляют значение по умолчанию. |
| `ignoreAnyOfInEnum` | Не учитывать `anyOf` при генерации перечислений (по умолчанию: `false`). Может помочь для контрактов, где перечисление описано через смешанные конструкции `anyOf`. |
| `additionalModelTypeAnnotations` | Дополнительные аннотации на типах моделей (по умолчанию не указано, необязательно). Несколько аннотаций разделяются `;`, например `@Deprecated;@MyAnnotation`. |
| `additionalEnumTypeAnnotations` | Дополнительные аннотации на типах перечислений (по умолчанию не указано, необязательно). Несколько аннотаций разделяются `;`. |

Пример:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    configOptions = [
        mode: "java-client",
        jsonAnnotation: "ru.tinkoff.kora.json.common.annotation.Json",
        objectType: "com.fasterxml.jackson.databind.JsonNode",
        additionalModelTypeAnnotations: "@Deprecated"
    ]
    ```

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    configOptions = mapOf(
        "mode" to "kotlin-client",
        "jsonAnnotation" to "ru.tinkoff.kora.json.common.annotation.Json",
        "objectType" to "com.fasterxml.jackson.databind.JsonNode",
        "additionalModelTypeAnnotations" to "@Deprecated"
    )
    ```

## Клиент { #client }

Минимальный пример настройки плагина для создания декларативного HTTP-клиента:

===! ":fontawesome-brands-java: `Java`"

    Для клиента в `configOptions.mode` доступны значения `java-client`, `java-async-client` и `java-reactive-client`.
    Остальные параметры клиента описаны в разделах про авторизацию, перехватчики, теги, модели и неявные заголовки ниже.

    ```groovy
    def openApiGenerateHttpClient = tasks.register("openApiGenerateHttpClient", GenerateTask) {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/openapi.yaml" //(1)!
        outputDir = "$buildDir/generated/openapi" //(2)!
        def corePackage = "ru.tinkoff.kora.example.openapi"
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

    1. Путь до `OpenAPI`-файла, из которого будут созданы классы
    2. Директория, в которую будут создаваться файлы
    3. Пакет классов делегатов, контроллеров и преобразователей
    4. Пакет классов моделей и DTO
    5. Пакет вспомогательных классов генератора
    6. Режим работы плагина
    7. Префикс пути конфигурации клиента
    8. Регистрируем созданные классы как исходный код проекта
    9. Делаем компиляцию кода, зависимой от генерации классов HTTP-клиента (сначала генерируем, потом компилируем)

=== ":simple-kotlin: `Kotlin`"

    Для клиента в `configOptions.mode` доступны значения `kotlin-client` и `kotlin-suspend-client`.
    Остальные параметры клиента описаны в разделах про авторизацию, перехватчики, теги, модели и неявные заголовки ниже.

    ```groovy
    val openApiGenerateHttpClient = tasks.register<GenerateTask>("openApiGenerateHttpClient") {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/openapi.yaml" //(1)!
        outputDir = "$buildDir/generated/openapi" //(2)!
        val corePackage = "ru.tinkoff.kora.example.openapi"
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
    tasks.withType<KspTask> { dependsOn(openApiGenerateHttpClient) } //(9)!
    ```

    1. Путь до `OpenAPI`-файла, из которого будут созданы классы
    2. Директория, в которую будут создаваться файлы
    3. Пакет классов делегатов, контроллеров и преобразователей
    4. Пакет классов моделей и DTO
    5. Пакет вспомогательных классов генератора
    6. Режим работы плагина
    7. Префикс пути конфигурации клиента
    8. Регистрируем созданные классы как исходный код проекта
    9. Делаем компиляцию кода, зависимой от генерации классов HTTP-клиента (сначала генерируем, потом компилируем)

После создания HTTP-клиент будет доступен для внедрения как зависимость по сгенерированному интерфейсу.

### Авторизация клиента { #client-authorization }

Если в `OpenAPI`-контракте описаны `securitySchemes`, генератор создаст модуль `ApiSecurity` с компонентами для авторизации клиента.
Для `apiKey` и `basic` будут сгенерированы компоненты чтения конфигурации; для `bearer` и `oauth` ожидается компонент `HttpClientTokenProvider`
с соответствующим тегом `ApiSecurity`.

`securityConfigPrefix` задает общий префикс конфигурации авторизации. Если префикс не указан, путь конфигурации совпадает с именем `securitySchemes`.
Если для операции указано несколько схем авторизации, можно указать `primaryAuth`; иначе генератор выберет одну из схем и запишет предупреждение в лог.
Если включить `authAllowMultiple`, генератор создаст составной перехватчик, который применит несколько схем авторизации последовательно.
Если включить `authAsMethodArgument`, данные авторизации будут добавлены в сигнатуру метода клиента вместо сгенерированного перехватчика.

### Дополнительные аннотации { #additional-contract-annotations }

Параметр `additionalContractAnnotations` позволяет добавить аннотации над методами сгенерированного клиента или серверного контроллера.
Значение — `JSON`-объект, где ключом выступает тег API из контракта или `*` для всех операций, а значением — массив объектов с полем `annotation`.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    configOptions = [
        mode: "java-client",
        additionalContractAnnotations: """
                {
                  "*": [
                    {
                      "annotation": "@ru.tinkoff.kora.common.Tag(ru.tinkoff.example.CommonTag.class)"
                    }
                  ],
                  "pet": [
                    {
                      "annotation": "@ru.tinkoff.example.PetOperation"
                    }
                  ]
                }
                """
    ]
    ```

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    configOptions = mapOf(
        "mode" to "kotlin-client",
        "additionalContractAnnotations" to """{
                  "*": [
                    {
                      "annotation": "@ru.tinkoff.kora.common.Tag(ru.tinkoff.example.CommonTag::class)"
                    }
                  ],
                  "pet": [
                    {
                      "annotation": "@ru.tinkoff.example.PetOperation"
                    }
                  ]
                }
                """
    )
    ```

### Перехватчики { #interceptors }

Есть возможность на созданные клиенты с `@HttpClient` аннотацией поставить [перехватчики](http-client.md#response-entity).

Значение — `JSON`-объект, ключом которого выступает тег API из контракта, а значением объект с полями `type` и `tag`.
Можно указывать оба поля одновременно или только одно из них:

- `type` - класс реализации конкретного перехватчика
- `tag` - теги перехватчика (можно указать как массив строк)

Для этого необходимо установить параметр `configOptions.interceptors`:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    configOptions = [
        mode: "java-client",
        interceptors: """
                {
                  "*": [
                    {
                      "tag": "ru.tinkoff.example.MyTag"
                    }
                  ],
                  "pet": [
                    {
                      "type": "ru.tinkoff.example.MyInterceptor"
                    }
                  ],
                  "shop": [
                    {
                      "type": "ru.tinkoff.example.MyInterceptor",
                      "tag": "ru.tinkoff.example.MyTag"
                    }
                  ]
                }
                """
    ]
    ```

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    configOptions = mapOf(
        "mode" to "kotlin-client",
        "interceptors" to """{
                  "*": [
                    {
                      "tag": "ru.tinkoff.example.MyTag"
                    }
                  ],
                  "pet": [
                    {
                      "type": "ru.tinkoff.example.MyInterceptor"
                    }
                  ],
                  "shop": [
                    {
                      "type": "ru.tinkoff.example.MyInterceptor",
                      "tag": "ru.tinkoff.example.MyTag"
                    }
                  ]
                }
                """
    )
    ```

### Теги { #tags }

Есть возможность на созданные клиенты с `@HttpClient` аннотацией поставить параметры  `httpClientTag` и `telemetryTag`.
Значение — `JSON`-объект, ключом которого выступает тег API из контракта, а значением объект с полями `httpClientTag` и `telemetryTag`.

Для этого необходимо установить параметр `configOptions.tags`:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    configOptions = [
        mode: "java-client",
        tags: """
              {
                "*": { // применится для всех тегов, кроме явно указанных (в данном случае instrument)
                  "httpClientTag": "some.tag.Common",
                  "telemetryTag": "some.tag.Common"
                },
                "instrument": { // применится для instrument
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
        "tags" to """{
                        "*": { // применится для всех тегов, кроме явно указанных (в данном случае instrument)
                          "httpClientTag": "some.tag.Common",
                          "telemetryTag": "some.tag.Common"
                        },
                        "instrument": { // применится для instrument
                          "httpClientTag": "some.tag.Instrument",
                          "telemetryTag": "some.tag.Instrument"
                        }
                     }
                     """
    )
    ```

## Неявные заголовки { #implicit-headers }

По умолчанию заголовки из `OpenAPI`-операции становятся аргументами сгенерированного метода.
Если часть заголовков должна задаваться инфраструктурой, а не пользователем метода, их можно сделать неявными.

- `implicitHeaders = true` делает неявными все заголовки из `OpenAPI`-операций.
- `implicitHeadersRegex` делает неявными только заголовки, имя которых подходит под регулярное выражение.

Неявный заголовок удаляется из сигнатуры метода, но остается в `OpenAPI`-аннотациях сгенерированного кода.
Так можно оставить заголовок в документации контракта, но не заставлять прикладной код передавать его вручную.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    configOptions = [
        mode: "java-client",
        implicitHeadersRegex: "X-Request-.*"
    ]
    ```

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    configOptions = mapOf(
        "mode" to "kotlin-client",
        "implicitHeadersRegex" to "X-Request-.*"
    )
    ```

## Модели { #models }

Генератор создает модели запросов и ответов из схем `OpenAPI`.
Для необязательных полей используется `@Nullable` в `Java` и nullable-тип `T?` в `Kotlin`.
Для схем с наследованием и дискриминатором в `Java` могут генерироваться `sealed interface`, а в `Kotlin` — `sealed interface` / классы в зависимости от схемы.

### Необязательные nullable-поля { #json-nullable }

Если поле одновременно `nullable: true` и отсутствует в списке `required`, по умолчанию оно генерируется как обычное необязательное поле.
Если нужно различать три состояния — поле отсутствует в `JSON`, поле присутствует со значением `null`, поле присутствует со значением — включите `enableJsonNullable`.
В этом случае поле будет сгенерировано как [JsonNullable](json.md#jsonnullable-wrapper).

`forceIncludeOptional` и `forceIncludeNonRequired` управляют сериализацией необязательных полей:

- `forceIncludeOptional` ставит `@JsonInclude(Always)` для полей `nullable: true` и `required: false` вместо использования `JsonNullable`.
- `forceIncludeNonRequired` ставит `@JsonInclude(Always)` для всех полей `required: false`.

`forceIncludeOptional` нельзя включать одновременно с `enableJsonNullable`, потому что эти режимы решают одну задачу разными способами.

### Фильтрация моделей { #filter-with-models }

`OpenAPI Generator` умеет фильтровать операции через параметр `openapiNormalizer.FILTER`.
Если дополнительно включить `filterWithModels`, генератор Kora попробует исключить из генерации неиспользуемые модели,
которые остались после фильтрации операций. Это полезно для больших контрактов, когда приложение генерирует только часть API.

## Сервер { #server }

Минимальный пример настройки плагина для создания обработчиков HTTP-сервера:

===! ":fontawesome-brands-java: `Java`"

    Для сервера в `configOptions.mode` доступны значения `java-server`, `java-async-server` и `java-reactive-server`.
    Остальные параметры сервера описаны в разделах про валидацию, `delegate`-классы, перехватчики, модели и неявные заголовки ниже.

    ```groovy
    def openApiGenerateHttpServer = tasks.register("openApiGenerateHttpServer", GenerateTask) {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/openapi.yaml" //(1)!
        outputDir = "$buildDir/generated/openapi" //(2)!
        def corePackage = "ru.tinkoff.kora.example.openapi"
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

    1. Путь до `OpenAPI`-файла, из которого будут созданы классы
    2. Директория, в которую будут создаваться файлы
    3. Пакет классов делегатов, контроллеров и преобразователей
    4. Пакет классов моделей и DTO
    5. Пакет вспомогательных классов генератора
    6. Режим работы плагина
    7. Регистрируем созданные классы как исходный код проекта
    8. Делаем компиляцию кода, зависимой от генерации классов HTTP-сервера (сначала генерируем, потом компилируем)

=== ":simple-kotlin: `Kotlin`"

    Для сервера в `configOptions.mode` доступны значения `kotlin-server` и `kotlin-suspend-server`.
    Остальные параметры сервера описаны в разделах про валидацию, `delegate`-классы, перехватчики, модели и неявные заголовки ниже.

    ```groovy
    val openApiGenerateHttpServer = tasks.register<GenerateTask>("openApiGenerateHttpServer") {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/openapi.yaml" //(1)!
        outputDir = "$buildDir/generated/openapi" //(2)!
        val corePackage = "ru.tinkoff.kora.example.openapi"
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
    tasks.withType<KspTask> { dependsOn(openApiGenerateHttpServer) } //(8)!
    ```

    1. Путь до `OpenAPI`-файла, из которого будут созданы классы
    2. Директория, в которую будут создаваться файлы
    3. Пакет классов делегатов, контроллеров и преобразователей
    4. Пакет классов моделей и DTO
    5. Пакет вспомогательных классов генератора
    6. Режим работы плагина
    7. Регистрируем созданные классы как исходный код проекта
    8. Делаем компиляцию кода, зависимой от генерации классов HTTP-сервера (сначала генерируем, потом компилируем)

После создания обработчики будут автоматически зарегистрированы.

### Валидация { #validation }

Для генерации моделей и контроллеров с аннотациями из модуля [валидации](validation.md) необходимо установить опцию `enableServerValidation`:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    configOptions = [
        mode: "java-server",
        enableServerValidation: "true"  //(1)!
    ]
    ```

    1. Включение валидации на стороне контроллера HTTP-сервера

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    configOptions = mapOf(
        "mode" to "kotlin-server",
        "enableServerValidation" to "true" //(1)!
    )
    ```

    1. Включение валидации на стороне контроллера HTTP-сервера

Если включен `enableServerValidation`, генератор добавляет аннотации валидации на модели и параметры серверных методов,
а также аннотацию `@Validate` на методы контроллера, где есть валидируемые параметры.
`enableServerValidationInterceptor` управляет добавлением `ValidationHttpServerInterceptor`, который преобразует ошибки валидации в HTTP-ответ.
Если `enableServerValidationInterceptor` явно не указан, при включенной серверной валидации он также считается включенным.
Если указать `enableServerValidationInterceptor = false`, аннотации валидации останутся, но стандартный перехватчик для ответа не будет добавлен.

### Реализация делегата { #delegate-method-body }

Серверный генератор создает контроллер и `delegate`-контракт, в котором пользователь реализует прикладную логику.
По умолчанию `delegateMethodBodyMode = none`, поэтому методы `delegate`-контракта не получают стандартное тело и должны быть реализованы приложением.

Если указать `delegateMethodBodyMode = throwException`, методы получат тело, которое бросает исключение, а генератор дополнительно создаст модуль
со стандартной реализацией `delegate`-контракта. Такой режим удобен, когда нужно собрать приложение до реализации всех операций или постепенно подключать собственные реализации.

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

### Перехватчики { #interceptors-2 }

Есть возможность на созданные контроллеры с `@HttpController` аннотацией поставить [перехватчики](http-server.md#custom-response).

Значение — `JSON`-объект, ключом которого выступает тег API из контракта, а значением объект с полями `type` и `tag`.
Можно указывать оба поля одновременно или только одно из них:

- `type` - класс реализации конкретного перехватчика
- `tag` - теги перехватчика (можно указать как массив строк)

Для этого необходимо установить параметр `configOptions.interceptors`:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    configOptions = [
        mode: "java-server",
        interceptors: """
                {
                  "*": [
                    {
                      "tag": "ru.tinkoff.example.MyTag"
                    }
                  ],
                  "pet": [
                    {
                      "type": "ru.tinkoff.example.MyInterceptor"
                    }
                  ],
                  "shop": [
                    {
                      "type": "ru.tinkoff.example.MyInterceptor",
                      "tag": "ru.tinkoff.example.MyTag"
                    }
                  ]
                }
                """
    ]
    ```

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    configOptions = mapOf(
        "mode" to "kotlin-server",
        "interceptors" to """{
                  "*": [
                    {
                      "tag": "ru.tinkoff.example.MyTag"
                    }
                  ],
                  "pet": [
                    {
                      "type": "ru.tinkoff.example.MyInterceptor"
                    }
                  ],
                  "shop": [
                    {
                      "type": "ru.tinkoff.example.MyInterceptor",
                      "tag": "ru.tinkoff.example.MyTag"
                    }
                  ]
                }
                """
    )
    ```

### Авторизация { #authorization }

Kora предоставляет интерфейс для извлечения авторизационной информации в рамках перехватчика,
созданного для сервера из `OpenAPI`. Можно обрабатывать разные типы авторизации: [Basic/ApiKey/Bearer/OAuth](https://swagger.io/docs/specification/authentication/).

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface AuthModule {

        @Tag(ApiSecurity.BearerAuth.class)
        default HttpServerPrincipalExtractor<Principal> bearerHttpServerPrincipalExtractor() {
            return (request, value) -> CompletableFuture.completedFuture(new MyPrincipal(request.headers().getFirst("Authorization")));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface AuthModule {

        @Tag(ApiSecurity.BearerAuth::class)
        fun bearerHttpServerPrincipalExtractor(): HttpServerPrincipalExtractor<Principal> {
            return HttpServerPrincipalExtractor<Principal> { request, value ->
                CompletableFuture.completedFuture<Principal>(
                    MyPrincipal(request.headers().getFirst("Authorization"))
                )
            }
        }
    }
    ```

## Совет { #recommendations }

???+ tip "Совет"

    Если что-то не создается посредством плагина либо поведение отличается от ожидаемого или от других версий,
    требуется тщательно проверить настройки [конфигурации плагина](#configuration) и изучить их,
    так как они могут влиять на результаты того как создаются классы.

    Начиная с `7.0.0` версии плагина, включенное по умолчанию `SIMPLIFY_ONEOF_ANYOF` правило у параметра `openapiNormalizer`
    может вести к некоторым не очевидным результатам генератора.
