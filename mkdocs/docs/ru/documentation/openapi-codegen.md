---
description: "Explains Kora OpenAPI code generation for HTTP clients and servers, generator options, tags, validation, interceptors, authorization, and JsonNullable support. Use when working with openapi-generator, @HttpClient, @HttpController, @InterceptWith, @Tag, @Validate, JsonNullable, primaryAuth, prefixPath, requestInDelegateParams, HttpClientTokenProvider, PrincipalWithScopes, ApiSecurity."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora OpenAPI code generation for HTTP clients and servers, generator options, tags, validation, interceptors, authorization, and JsonNullable support; key triggers include openapi-generator, @HttpClient, @HttpController, @InterceptWith, @Tag, @Validate, JsonNullable, primaryAuth, prefixPath, requestInDelegateParams, HttpClientTokenProvider, PrincipalWithScopes, ApiSecurity."
---

Этот модуль генерирует код Kora из контракта `OpenAPI` с помощью [OpenAPI Generator](https://openapi-generator.tech/docs/plugins#gradle).
Из единого описания API можно создать декларативные обработчики [HTTP-сервера](http-server.md) или декларативные [HTTP-клиенты](http-client.md),
а также модели запросов и ответов, мапперы, обработку авторизации и дополнительные аннотации.
Такой подход полезен, когда `OpenAPI` является источником истины для транспортного контракта, а код приложения должен автоматически ему следовать.

Если нужен пошаговый разбор перед справочным описанием, смотрите [OpenAPI HTTP-сервер](../guides/openapi-http-server.md), [продвинутый OpenAPI HTTP-сервер](../guides/openapi-http-server-advanced.md) и [OpenAPI HTTP-клиент](../guides/openapi-http-client.md).

## Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    Зависимость генератора в `build.gradle`:
    ```groovy
    buildscript {
        dependencies {
            classpath("ru.tinkoff.kora:openapi-generator:1.2.18")
        }
    }
    ```

    Зависимость плагина в `build.gradle`:
    ```groovy
    plugins {
        id "org.openapi.generator" version "7.14.0"
    }
    ```

    Работоспособность других версий плагина не гарантируется, поскольку API `OpenAPI Generator` может быть несовместимо на уровне кода.

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) в `build.gradle.kts`:
    ```groovy
    buildscript {
        dependencies {
            classpath("ru.tinkoff.kora:openapi-generator:1.2.18")
        }
    }
    ```

    Зависимость плагина в `build.gradle.kts`:
    ```groovy
    plugins {
        id("org.openapi.generator") version("7.14.0")
    }
    ```

    Работоспособность других версий плагина не гарантируется, поскольку API `OpenAPI Generator` может быть несовместимо на уровне кода.

Сгенерированному коду также требуется модуль [HTTP-сервера](http-server.md) или [HTTP-клиента](http-client.md) в зависимости от выбранного режима генерации.

## Конфигурация { #configuration }

Настройте параметры [плагина OpenAPI Generator](https://openapi-generator.tech/docs/plugins#gradle):

- Параметры `Gradle`-плагина описаны в [документации плагина](https://github.com/OpenAPITools/openapi-generator/blob/v7.14.0/modules/openapi-generator-gradle-plugin/README.adoc).
- Параметр плагина `configOptions` описан в [документации по конфигурации](https://openapi-generator.tech/docs/configuration/).
- Параметр плагина `openapiNormalizer` описан в [документации по настройке](https://openapi-generator.tech/docs/customization/#openapi-normalizer).

### Общие параметры `OpenAPI Generator` { #common-generator-options }

Помимо специфичных для Kora `configOptions`, `GenerateTask` принимает общие параметры `OpenAPI Generator`.
Они определяют, откуда читать контракт, куда помещать сгенерированные файлы, какие пакеты использовать и как предобрабатывать описание `OpenAPI`.
В проектах Kora эти параметры обычно задаются явно, поскольку сгенерированный код затем добавляется в обычную компиляцию проекта.

| Параметр | Описание |
| -------- | -------- |
| `generatorName` | Имя генератора (`обязательный`, без значения по умолчанию). Для Kora всегда указывайте `kora`. |
| `inputSpec` | Путь к файлу `OpenAPI` (`обязательный`, без значения по умолчанию). Обычно это файл в `src/main/resources/openapi`, например `$projectDir/src/main/resources/openapi/openapi.yaml`. |
| `outputDir` | Каталог для сгенерированных файлов (по умолчанию не указан, необязательный). В проектах Kora это обычно каталог в `build`, например `$buildDir/generated/openapi`, который добавляется в основной набор исходного кода (source set). |
| `apiPackage` | Пакет для сгенерированных интерфейсов API, контроллеров, классов `delegate` и мапперов (по умолчанию: `org.openapitools.api`). Рекомендуется указывать его явно, например `ru.tinkoff.kora.example.openapi.api`. |
| `modelPackage` | Пакет для моделей, сгенерированных из схем `OpenAPI` (по умолчанию: `org.openapitools.model`). Рекомендуется указывать его явно, например `ru.tinkoff.kora.example.openapi.model`. |
| `invokerPackage` | Вспомогательный пакет генератора (по умолчанию: `org.openapitools.api`). Рекомендуется указывать его явно рядом с `apiPackage` и `modelPackage`, например `ru.tinkoff.kora.example.openapi.invoker`. |
| `configOptions` | Специфичные для генератора параметры (по умолчанию: `{}`). Для Kora здесь задаются `mode`, `clientConfigPrefix`, `enableServerValidation`, `interceptors` и другие параметры, описанные ниже. |
| `globalProperties` | Ограничивает, какие сущности генерируются (по умолчанию: `{}`). Полезно, когда нужно сгенерировать только `apis`, только `models` или отдельные модели и операции. Используйте осторожно: обычным клиентам и серверам Kora, как правило, нужны классы API, модели и мапперы вместе. |
| `openapiNormalizer` | Предобрабатывает контракт `OpenAPI` перед генерацией (по умолчанию: `{}`). Часто используется, чтобы отключить стандартные преобразования через `DISABLE_ALL`, сгенерировать только выбранные операции через `FILTER` или управлять правилами вроде `SIMPLIFY_ONEOF_ANYOF`. |
| `importMappings` | Сопоставляет имя схемы с существующим классом (по умолчанию: `{}`). Полезно, когда модель написана вручную или приходит из другого модуля, например `Money: "com.example.Money"`. |
| `typeMappings` | Сопоставляет тип `OpenAPI Generator` с типом языка (по умолчанию: `{}`). Используется для точечной замены типов, например замены `OffsetDateTime` на специфичный для проекта тип времени. |
| `schemaMappings` | Сопоставляет схему `OpenAPI` с внешним типом без генерации модели (по умолчанию: `{}`). Аналогично `importMappings`, но настраивается на уровне схемы и полезно для переиспользования общих DTO. |
| `skipValidateSpec` | Пропускает валидацию контракта `OpenAPI` перед генерацией (по умолчанию: `false`). В обычных сборках валидацию лучше оставлять включённой; используйте `true` только временно для внешних контрактов, которые нельзя быстро исправить. |
| `cleanupOutput` | Очищает `outputDir` перед генерацией (по умолчанию: `false`). Полезно, когда контракт часто меняется и файлы удалённых операций или моделей должны исчезать. Не указывайте в `outputDir` каталог с написанным вручную кодом. |

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

### Полезные правила `openapiNormalizer` { #openapi-normalizer }

`openapiNormalizer` изменяет входной контракт `OpenAPI` перед генерацией. Это не параметр Kora, а общий механизм `OpenAPI Generator`.
Для Kora он особенно полезен, когда один большой контракт используется несколькими приложениями или когда контракт содержит неоднозначные для генерации кода конструкции.

| Правило | Описание |
| -------- | -------- |
| `DISABLE_ALL` | Отключает стандартные правила нормализации (по умолчанию: `false`). Начиная с `OpenAPI Generator 7` некоторые правила включены по умолчанию, поэтому предсказуемая генерация часто начинается с `DISABLE_ALL: "true"`, а затем явно включаются только нужные правила. |
| `FILTER` | Оставляет для генерации только выбранные операции (по умолчанию не указано, необязательно). Поддерживает один фильтр за раз: `operationId:name1\|name2`, `method:get\|post` или `tag:public\|billing`. Операции, которые не подходят, помечаются как `x-internal: true` и не генерируются. |
| `KEEP_ONLY_FIRST_TAG_IN_OPERATION` | Оставляет у операции только первый тег (по умолчанию: `false`). Полезно, когда у операций несколько тегов и они разбиваются на несколько классов API не так, как вы ожидаете. |
| `SET_TAGS_FOR_ALL_OPERATIONS` | Заменяет теги всех операций одним переданным значением (по умолчанию не указано, необязательно). Полезно, когда нужно принудительно получить один сгенерированный класс API. |
| `SET_TAGS_TO_OPERATIONID` | Устанавливает тег операции равным `operationId`, либо `default`, если `operationId` пуст (по умолчанию: `false`). Полезно для контрактов без пригодных тегов, когда нужна предсказуемая группировка операций. |
| `SET_TAGS_TO_VENDOR_EXTENSION` | Читает теги операций из указанного расширения, например `x-tags` (по умолчанию не указано, необязательно). Полезно, когда внешний контракт нельзя изменить, но в нём уже есть собственная группировка операций. |
| `FIX_DUPLICATED_OPERATIONID` | Добавляет числовой суффикс к повторяющимся значениям `operationId` (по умолчанию: `false`). Лучше исправить контракт, но это правило помогает временно сгенерировать код по внешнему описанию. |
| `SET_BEARER_AUTH_FOR_NAME` | Преобразует указанную схему безопасности в `bearerAuth` (по умолчанию не указано, необязательно). Полезно для внешних контрактов, где bearer-токен описан нестандартно, но в приложении его нужно обрабатывать как обычную схему bearer. |
| `REF_AS_PARENT_IN_ALLOF` | Помечает `$ref` внутри `allOf` как родительскую схему через `x-parent: true` (по умолчанию: `false`). Может помочь контрактам, которые моделируют наследование через `allOf`. |
| `SIMPLIFY_ONEOF_ANYOF` | Упрощает некоторые конструкции `oneOf`/`anyOf`, например переносит вариант `null` в `nullable: true` и убирает одиночные обёртки (включено по умолчанию в `OpenAPI Generator 7`, если не задан `DISABLE_ALL`). Для Kora это может менять форму сгенерированных моделей, поэтому включайте его осознанно. |
| `SIMPLIFY_ANYOF_STRING_AND_ENUM_STRING` | Упрощает `anyOf`, составленный из `string` и строкового перечисления, до `string` (по умолчанию: `false`). Это может помочь с контрактами, где ограничение перечисления не важно для кода. |
| `SIMPLIFY_BOOLEAN_ENUM` | Преобразует булево перечисление в обычный `boolean` (включено по умолчанию в `OpenAPI Generator 7`, если не задан `DISABLE_ALL`). |
| `REFACTOR_ALLOF_WITH_PROPERTIES_ONLY` | Переносит свойства из схемы, содержащей одновременно `allOf` и `properties`, в отдельную схему внутри `allOf` (включено по умолчанию в `OpenAPI Generator 7`, если не задан `DISABLE_ALL`). Это может помочь наследованию, но строгие контракты стоит проверять после генерации. |
| `NORMALIZE_31SPEC` | Нормализует некоторые конструкции `OpenAPI 3.1` в форму, которую генератор понимает лучше (по умолчанию: `false`). Полезно для контрактов `3.1`, когда генерация не удаётся на новых формах схем. |
| `REMOVE_X_INTERNAL` | Удаляет `x-internal: true` из операций и моделей (по умолчанию: `false`). Используйте, только когда контракт уже содержит `x-internal`, но конкретная задача генерации должна принудительно вернуть такие операции. |
| `SET_CONTAINER_TO_NULLABLE` | Помечает типы-контейнеры `array`, `set` или `map` как `nullable` (по умолчанию не указано, необязательно). Используйте, только когда во внешнем контракте систематически отсутствует `nullable` у таких полей. |
| `SET_PRIMITIVE_TYPES_TO_NULLABLE` | Помечает примитивные типы `string`, `integer`, `number` или `boolean` как `nullable` (по умолчанию не указано, необязательно). Это существенно меняет сигнатуры моделей, поэтому применяйте его только к проблемным внешним контрактам. |

Пример генерации только публичной части контракта:

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

### Общие параметры `JSON` и моделей { #common-model-options }

Kora также поддерживает несколько `configOptions`, управляющих мапперами `JSON` и общей генерацией моделей.
Они не зависят от того, генерируется клиент или сервер.

| Параметр | Описание |
| -------- | -------- |
| `jsonAnnotation` | Аннотация-тег, используемая для внедрения мапперов `JSON` в сгенерированные мапперы запросов и ответов (по умолчанию: `ru.tinkoff.kora.json.common.annotation.Json`). |
| `objectType` | Тип для схем `type: object` без более точного описания. `Java` по умолчанию использует `java.lang.Object`, а `Kotlin` — `kotlin.Any`. Например, укажите `com.fasterxml.jackson.databind.JsonNode`, если приложение хочет обрабатывать произвольный `JSON` как дерево. |
| `disableHtmlEscaping` | Отключает экранирование HTML-символов в строках `JSON` (по умолчанию: `false`). Обычно значение по умолчанию оставляют. |
| `ignoreAnyOfInEnum` | Игнорирует `anyOf` при генерации перечислений (по умолчанию: `false`). Может помочь с контрактами, где перечисление описано через смешанные конструкции `anyOf`. |
| `discriminatorCaseSensitive` | Управляет чувствительностью к регистру при поиске значения дискриминатора для полиморфных (`oneOf`) моделей с дискриминатором (по умолчанию: `true`). Установите `false`, когда входящие значения дискриминатора могут отличаться регистром от определения в схеме. |
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

### Несколько задач генерации { #multiple-generation-tasks }

В одном модуле можно зарегистрировать несколько задач `GenerateTask`, например чтобы сгенерировать два независимых контракта
или сгенерировать клиент для одного контракта и сервер для другого. Каждая задача пишет в один и тот же `outputDir` и добавляется в один и тот же набор исходного кода (source set),
поэтому единственное требование — чтобы сгенерированные пакеты не пересекались. Задайте каждой задаче собственные `apiPackage`/`modelPackage`/`invokerPackage`.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    def openApiGeneratePetV2 = tasks.register("openApiGeneratePetV2", GenerateTask) {
        generatorName = "kora"
        inputSpec = "$projectDir/src/main/resources/openapi/petstoreV2.yaml"
        outputDir = "$buildDir/generated/openapi"
        def corePackage = "ru.tinkoff.kora.example.openapi.petV2" //(1)!
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
        def corePackage = "ru.tinkoff.kora.example.openapi.petV3" //(2)!
        apiPackage = "${corePackage}.api"
        modelPackage = "${corePackage}.model"
        invokerPackage = "${corePackage}.invoker"
        configOptions = [mode: "java-reactive-client", clientConfigPrefix: "httpClient.petV3"]
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
        outputDir = "$buildDir/generated/openapi"
        val corePackage = "ru.tinkoff.kora.example.openapi.petV2" //(1)!
        apiPackage = "${corePackage}.api"
        modelPackage = "${corePackage}.model"
        invokerPackage = "${corePackage}.invoker"
        configOptions = mapOf("mode" to "kotlin-client", "clientConfigPrefix" to "httpClient.petV2")
    }
    kotlin.sourceSets.main { kotlin.srcDir(openApiGeneratePetV2.get().outputDir) }
    tasks.withType<KspTask> { dependsOn(openApiGeneratePetV2) }

    val openApiGeneratePetV3 = tasks.register<GenerateTask>("openApiGeneratePetV3") {
        generatorName = "kora"
        inputSpec = "$projectDir/src/main/resources/openapi/petstoreV3.yaml"
        outputDir = "$buildDir/generated/openapi"
        val corePackage = "ru.tinkoff.kora.example.openapi.petV3" //(2)!
        apiPackage = "${corePackage}.api"
        modelPackage = "${corePackage}.model"
        invokerPackage = "${corePackage}.invoker"
        configOptions = mapOf("mode" to "kotlin-suspend-client", "clientConfigPrefix" to "httpClient.petV3")
    }
    kotlin.sourceSets.main { kotlin.srcDir(openApiGeneratePetV3.get().outputDir) }
    tasks.withType<KspTask> { dependsOn(openApiGeneratePetV3) }
    ```

    1. Изолированный пакет для первого контракта
    2. Другой пакет для второго контракта, чтобы имена классов не конфликтовали

## Клиент { #client }

Минимальная конфигурация плагина для создания декларативного HTTP-клиента:

===! ":fontawesome-brands-java: `Java`"

    Для клиентов `configOptions.mode` поддерживает `java-client`, `java-async-client` и `java-reactive-client`.
    Остальные параметры клиента описаны ниже в разделах про авторизацию, перехватчики, теги, модели и неявные заголовки.

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

    Для клиентов `configOptions.mode` поддерживает `kotlin-client` и `kotlin-suspend-client`.
    Остальные параметры клиента описаны ниже в разделах про авторизацию, перехватчики, теги, модели и неявные заголовки.

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

### Использование сгенерированного клиента { #client-usage }

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

    1. Сгенерированный интерфейс `@HttpClient`, внедряется напрямую

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class RootService(
        private val petApi: PetApi, //(1)!
    )
    ```

    1. Сгенерированный интерфейс `@HttpClient`, внедряется напрямую

Сгенерированный клиент читает конфигурацию по пути, заданному `clientConfigPrefix`, за которым следует имя сгенерированного интерфейса.
Для `clientConfigPrefix = "httpClient.petV2"` и интерфейса `PetApi` блок конфигурации — `httpClient.petV2.PetApi`.
Полный набор параметров клиента (`url`, `requestTimeout`, блоки для отдельных операций, `telemetry`) описан в документации по [HTTP-клиенту](http-client.md#configuration):

===! ":material-code-json: `Hocon`"

    ```javascript
    httpClient.petV2.PetApi {
        url = "https://localhost:8443" //(1)!
        requestTimeout = "10s" //(2)!
        getValuesConfig { //(3)!
            requestTimeout = "20s"
        }
        telemetry.logging.enabled = true
    }
    ```

    1. Базовый URL целевой службы
    2. Таймаут запроса по умолчанию для всех операций
    3. Блок переопределения для отдельной операции, названный по `operationId` (здесь `getValues`)

=== ":simple-yaml: `YAML`"

    ```yaml
    httpClient:
      petV2:
        PetApi:
          url: "https://localhost:8443" #(1)!
          requestTimeout: "10s" #(2)!
          getValuesConfig: #(3)!
            requestTimeout: "20s"
          telemetry:
            logging:
              enabled: true
    ```

    1. Базовый URL целевой службы
    2. Таймаут запроса по умолчанию для всех операций
    3. Блок переопределения для отдельной операции, названный по `operationId` (здесь `getValues`)

Сигнатуры методов клиента зависят от выбранного `mode`:

| Режим | Пример возвращаемого типа |
| -------- | -------- |
| `java-client` | `PetApiResponses.GetPetByIdApiResponse` (блокирующее значение) |
| `java-async-client` | `CompletionStage<PetApiResponses.GetPetByIdApiResponse>` |
| `java-reactive-client` | `Mono<PetApiResponses.GetPetByIdApiResponse>` (требует `reactor-core`) |
| `kotlin-client` | `PetApiResponses.GetPetByIdApiResponse` (блокирующее значение) |
| `kotlin-suspend-client` | `suspend fun ...: PetApiResponses.GetPetByIdApiResponse` |

Каждый метод возвращает запечатанную (`sealed`) обёртку `*ApiResponses`, подтипы которой кодируют HTTP-статус, так же как это делают [делегаты сервера](#delegate-response-types).

### Авторизация клиента { #client-authorization }

Если контракт `OpenAPI` описывает `securitySchemes`, генератор создаёт модуль `ApiSecurity` с компонентами для авторизации клиента.
Для `apiKey` и `basic` генерируются компоненты, читающие конфигурацию. Для `bearer` и `oauth` ожидается соответствующий помеченный тегом компонент `HttpClientTokenProvider`.

`securityConfigPrefix` задаёт общий префикс конфигурации авторизации. Если префикс не указан, путём конфигурации становится имя из `securitySchemes`.
Если у операции несколько схем авторизации, можно указать `primaryAuth`; иначе генератор выбирает одну из схем и пишет предупреждение в лог.
Если включён `authAllowMultiple`, генератор создаёт составной перехватчик, применяющий несколько схем авторизации последовательно.
Если включён `authAsMethodArgument`, данные авторизации добавляются в сигнатуру метода клиента вместо сгенерированного перехватчика.

#### apiKey и basic { #client-authorization-config }

Для схем `apiKey` и `basic` генератор создаёт читатели конфигурации `@DefaultComponent` и перехватчики, поэтому не требуется никаких компонентов — только значения конфигурации.
Путь конфигурации — это `securityConfigPrefix`, за которым следует имя схемы (или просто имя схемы, если `securityConfigPrefix` не задан).
Схема `apiKey` читает одну строку; схема `basic` читает объект `username`/`password`:

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

    1. Схема `apiKey` `apiKeyAuth`: значение, отправляемое сгенерированным `ApiKeyHttpClientInterceptor` в заголовке/параметре запроса/куки, объявленных схемой
    2. Схема `basic` `basicAuth`: учётные данные, оборачиваемые сгенерированным `BasicAuthHttpClientInterceptor`

=== ":simple-yaml: `YAML`"

    ```yaml
    openapiAuth:
      apiKeyAuth: "MyAuthApiKey" #(1)!
      basicAuth: #(2)!
        username: "user"
        password: "password"
    ```

    1. Схема `apiKey` `apiKeyAuth`: значение, отправляемое сгенерированным `ApiKeyHttpClientInterceptor` в заголовке/параметре запроса/куки, объявленных схемой
    2. Схема `basic` `basicAuth`: учётные данные, оборачиваемые сгенерированным `BasicAuthHttpClientInterceptor`

#### bearer и oauth { #client-authorization-token }

Для схем `bearer` и `oauth` генератор ожидает компонент [`HttpClientTokenProvider`](http-client.md#token-provider), помеченный сгенерированным классом-маркером `ApiSecurity`
(например `ApiSecurity.BearerAuth`). Генератор автоматически оборачивает его в `BearerAuthHttpClientInterceptor`, поэтому предоставить нужно только провайдер токенов:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface ClientAuthModule {

        @Tag(ApiSecurity.BearerAuth.class) //(1)!
        default HttpClientTokenProvider bearerTokenProvider() {
            return request -> CompletableFuture.completedFuture("my-token"); //(2)!
        }
    }
    ```

    1. Тег должен совпадать со сгенерированным классом-маркером для схемы
    2. Реальные реализации обычно здесь получают или обновляют токен

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface ClientAuthModule {

        @Tag(ApiSecurity.BearerAuth::class) //(1)!
        fun bearerTokenProvider(): HttpClientTokenProvider {
            return HttpClientTokenProvider { CompletableFuture.completedFuture("my-token") } //(2)!
        }
    }
    ```

    1. Тег должен совпадать со сгенерированным классом-маркером для схемы
    2. Реальные реализации обычно здесь получают или обновляют токен

#### Несколько схем { #client-authorization-multiple }

Когда операция объявляет несколько схем безопасности, `primaryAuth` выбирает, какую из них применять; иначе генератор выбирает одну и пишет предупреждение в лог.
Чтобы применить несколько схем к одному запросу, включите `authAllowMultiple` — генератор построит составной перехватчик, выполняющий каждую схему последовательно.
Чтобы передавать учётные данные явно на каждый вызов вместо перехватчика, включите `authAsMethodArgument` — значение авторизации станет аргументом метода клиента:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    configOptions = [
        mode: "java-client",
        securityConfigPrefix: "openapiAuth",
        primaryAuth: "apiKeyAuth", //(1)!
        authAllowMultiple: "false", //(2)!
        authAsMethodArgument: "false" //(3)!
    ]
    ```

    1. Схема, применяемая, когда у операции их перечислено несколько
    2. Применять каждую объявленную схему через составной перехватчик
    3. Добавить значение авторизации как аргумент метода вместо перехватчика

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    configOptions = mapOf(
        "mode" to "kotlin-client",
        "securityConfigPrefix" to "openapiAuth",
        "primaryAuth" to "apiKeyAuth", //(1)!
        "authAllowMultiple" to "false", //(2)!
        "authAsMethodArgument" to "false" //(3)!
    )
    ```

    1. Схема, применяемая, когда у операции их перечислено несколько
    2. Применять каждую объявленную схему через составной перехватчик
    3. Добавить значение авторизации как аргумент метода вместо перехватчика

### Дополнительные аннотации { #additional-contract-annotations }

Параметр `additionalContractAnnotations` добавляет аннотации над сгенерированными методами клиента или контроллера сервера.
Значение — это объект `JSON`, где ключ — тег API из контракта или `*` для всех операций, а значение — массив объектов с полем `annotation`.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    configOptions = [
        mode: "java-client",
        additionalContractAnnotations: """
            {
              "*": [
                { "annotation": "ru.tinkoff.example.CommonAnnotation" }
              ],
              "pet": [
                { "annotation": "ru.tinkoff.example.PetAnnotation" }
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
                { "annotation": "ru.tinkoff.example.CommonAnnotation" }
              ],
              "pet": [
                { "annotation": "ru.tinkoff.example.PetAnnotation" }
              ]
            }
            """
    )
    ```

### Перехватчики { #interceptors }

Сгенерированные клиенты, аннотированные `@HttpClient`, можно также аннотировать [перехватчиками](http-client.md#interceptors).
Значение — это объект `JSON`, где ключ — тег API из контракта, а значение — массив объектов с полями `type` и `tag`.
Оба поля можно указать вместе или указать только одно из них:

- `type` — класс реализации конкретного перехватчика
- `tag` — теги перехватчика: строка или массив строк

Задайте `configOptions.interceptors`:

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

Сгенерированным клиентам, аннотированным `@HttpClient`, можно передать параметры `httpClientTag` и `telemetryTag`.
Значение — это объект `JSON`, где ключ — тег API из контракта, а значение — объект с полями `httpClientTag` и `telemetryTag`.

Задайте `configOptions.tags`:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    configOptions = [
        mode: "java-client",
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

Неявный заголовок убирается из сигнатуры метода, но остаётся в аннотациях `OpenAPI` в сгенерированном коде.
Это сохраняет заголовок в документации контракта, не требуя от кода приложения передавать его вручную.

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

Генератор создаёт модели запросов и ответов из схем `OpenAPI`.
Необязательные поля используют `@Nullable` в `Java` и nullable-тип `T?` в `Kotlin`.
Для схем с наследованием и дискриминатором `Java` может генерировать `sealed interface`, а `Kotlin` — `sealed interface` / классы в зависимости от схемы.

### Необязательные nullable-поля { #json-nullable }

Если поле одновременно имеет `nullable: true` и отсутствует в списке `required`, по умолчанию оно генерируется как обычное необязательное поле.
Если нужно различать три состояния — поле отсутствует в `JSON`, поле присутствует со значением `null` и поле присутствует со значением — включите `enableJsonNullable`.
В этом случае поле генерируется как [JsonNullable](json.md#jsonnullable-wrapper).

`forceIncludeOptional` и `forceIncludeNonRequired` управляют сериализацией необязательных полей:

- `forceIncludeOptional` устанавливает `@JsonInclude(Always)` для полей с `nullable: true` и `required: false` вместо использования `JsonNullable`.
- `forceIncludeNonRequired` устанавливает `@JsonInclude(Always)` для всех полей с `required: false`.

`forceIncludeOptional` нельзя включить вместе с `enableJsonNullable`, поскольку оба режима решают одну и ту же задачу разными способами.

### Фильтрация моделей { #filter-with-models }

`OpenAPI Generator` может фильтровать операции через `openapiNormalizer.FILTER`.
Если дополнительно включён `filterWithModels`, генератор Kora пытается исключить неиспользуемые модели, оставшиеся после фильтрации операций.
Это полезно для больших контрактов, где приложение генерирует только часть API.

## Сервер { #server }

Минимальная конфигурация плагина для создания обработчиков HTTP-сервера:

===! ":fontawesome-brands-java: `Java`"

    Для серверов `configOptions.mode` поддерживает `java-server`, `java-async-server` и `java-reactive-server`.
    Остальные параметры сервера описаны ниже в разделах про валидацию, классы `delegate`, перехватчики, модели и неявные заголовки.

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

    1. Путь к файлу `OpenAPI`, по которому создаются классы
    2. Каталог, где создаются сгенерированные файлы
    3. Пакет для делегатов, контроллеров и мапперов
    4. Пакет для моделей и DTO
    5. Вспомогательный пакет генератора
    6. Режим плагина
    7. Регистрирует сгенерированные классы как исходный код проекта
    8. Ставит компиляцию кода в зависимость от генерации классов HTTP-сервера: сначала генерация, затем компиляция

=== ":simple-kotlin: `Kotlin`"

    Для серверов `configOptions.mode` поддерживает `kotlin-server` и `kotlin-suspend-server`.
    Остальные параметры сервера описаны ниже в разделах про валидацию, классы `delegate`, перехватчики, модели и неявные заголовки.

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

    1. Путь к файлу `OpenAPI`, по которому создаются классы
    2. Каталог, где создаются сгенерированные файлы
    3. Пакет для делегатов, контроллеров и мапперов
    4. Пакет для моделей и DTO
    5. Вспомогательный пакет генератора
    6. Режим плагина
    7. Регистрирует сгенерированные классы как исходный код проекта
    8. Ставит компиляцию кода в зависимость от генерации классов HTTP-сервера: сначала генерация, затем компиляция

После генерации обработчики регистрируются автоматически.

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

Когда `enableServerValidation` включён, генератор добавляет аннотации валидации к моделям и параметрам методов сервера,
а также добавляет `@Validate` к методам контроллера с валидируемыми параметрами.
`enableServerValidationInterceptor` управляет добавлением `ValidationHttpServerInterceptor`, который преобразует ошибки валидации в HTTP-ответы.
Если `enableServerValidationInterceptor` не указан явно, он считается включённым, когда включена валидация сервера.
Если указано `enableServerValidationInterceptor = false`, аннотации валидации остаются, но стандартный перехватчик ответа не добавляется.

### Реализация делегата { #delegate-method-body }

Генератор сервера создаёт контроллер и контракт `delegate`, в котором пользователь реализует логику приложения.
По умолчанию `delegateMethodBodyMode = none`, поэтому методы контракта `delegate` не получают стандартного тела и должны быть реализованы приложением.

Если задано `delegateMethodBodyMode = throwException`, методы получают тело, выбрасывающее исключение, и генератор также создаёт модуль
с реализацией контракта `delegate` по умолчанию. Этот режим полезен, когда приложение нужно собрать до того, как реализованы все операции, или когда собственные реализации подключаются постепенно.

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

#### Типы ответов делегата { #delegate-response-types }

Каждый сгенерированный метод `delegate` возвращает запечатанную (`sealed`) обёртку `*ApiResponses`, подтипы которой кодируют HTTP-статус, объявленный в контракте.
Для операции `getPetById` с ответами `200` и `404` генератор создаёт `PetApiResponses.GetPetByIdApiResponse` с подтипами
`GetPetById200ApiResponse` (несущим тело через `content()`) и `GetPetById404ApiResponse`. Реализация возвращает подтип, соответствующий результату:

===! ":fontawesome-brands-java: `Java`"

    Возвращаемый тип зависит от `mode`: `java-server` возвращает значение напрямую (показано здесь), `java-async-server` возвращает `CompletionStage<...>`, `java-reactive-server` возвращает `Mono<...>`:

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

    Возвращаемый тип зависит от `mode`: `kotlin-server` возвращает значение напрямую (показано здесь), `kotlin-suspend-server` использует `suspend`-метод:

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

    1. Путь контракта `/pet/{id}` становится `/api/v1/pet/{id}`

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    configOptions = mapOf(
        "mode" to "kotlin-server",
        "prefixPath" to "/api/v1" //(1)!
    )
    ```

    1. Путь контракта `/pet/{id}` становится `/api/v1/pet/{id}`

### Перехватчики { #interceptors-2 }

Сгенерированные контроллеры, аннотированные `@HttpController`, можно также аннотировать [перехватчиками](http-server.md#interceptors).
Значение — это объект `JSON`, где ключ — тег API из контракта, а значение — объект с полями `type` и `tag`.
Оба поля можно указать вместе или указать только одно из них:

- `type` — класс реализации конкретного перехватчика
- `tag` — теги перехватчика: строка или массив строк

Задайте `configOptions.interceptors`:

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

Когда контракт `OpenAPI` описывает `securitySchemes`, генератор сервера создаёт модуль `ApiSecurity` с одним классом-маркером на каждую схему:
`ApiSecurity.BearerAuth`, `ApiSecurity.BasicAuth`, `ApiSecurity.ApiKeyAuth` и `ApiSecurity.OAuth`
(обрабатывающие [Basic/ApiKey/Bearer/OAuth](https://swagger.io/docs/specification/authentication/)).
Для каждой схемы приложение должно предоставить компонент `HttpServerPrincipalExtractor`, помеченный соответствующим классом-маркером.
Извлекатель получает запрос и разобранное значение учётных данных и возвращает аутентифицированный `Principal`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface AuthModule {

        @Tag(ApiSecurity.BearerAuth.class)
        default HttpServerPrincipalExtractor<Principal> bearerHttpServerPrincipalExtractor() {
            return (request, value) -> CompletableFuture.completedFuture(new UserPrincipal("name"));
        }

        @Tag(ApiSecurity.BasicAuth.class)
        default HttpServerPrincipalExtractor<Principal> basicHttpServerPrincipalExtractor() {
            return (request, value) -> CompletableFuture.completedFuture(new UserPrincipal("name"));
        }

        @Tag(ApiSecurity.ApiKeyAuth.class)
        default HttpServerPrincipalExtractor<Principal> apiKeyHttpServerPrincipalExtractor() {
            return (request, value) -> CompletableFuture.completedFuture(new UserPrincipal("name"));
        }

        @Tag(ApiSecurity.OAuth.class)
        default HttpServerPrincipalExtractor<PrincipalWithScopes> oauthHttpServerPrincipalExtractor() { //(1)!
            return (request, value) -> CompletableFuture.completedFuture(new UserPrincipal("name"));
        }
    }
    ```

    1. Схемы `OAuth` объявляют области доступа (scopes), поэтому извлекатель возвращает `PrincipalWithScopes`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface AuthModule {

        @Tag(ApiSecurity.BearerAuth::class)
        fun bearerHttpServerPrincipalExtractor(): HttpServerPrincipalExtractor<Principal> {
            return HttpServerPrincipalExtractor { _, _ -> CompletableFuture.completedFuture(UserPrincipal("name")) }
        }

        @Tag(ApiSecurity.BasicAuth::class)
        fun basicHttpServerPrincipalExtractor(): HttpServerPrincipalExtractor<Principal> {
            return HttpServerPrincipalExtractor { _, _ -> CompletableFuture.completedFuture(UserPrincipal("name")) }
        }

        @Tag(ApiSecurity.ApiKeyAuth::class)
        fun apiKeyHttpServerPrincipalExtractor(): HttpServerPrincipalExtractor<Principal> {
            return HttpServerPrincipalExtractor { _, _ -> CompletableFuture.completedFuture(UserPrincipal("name")) }
        }

        @Tag(ApiSecurity.OAuth::class)
        fun oauthHttpServerPrincipalExtractor(): HttpServerPrincipalExtractor<PrincipalWithScopes> { //(1)!
            return HttpServerPrincipalExtractor { _, _ -> CompletableFuture.completedFuture(UserPrincipal("name")) }
        }
    }
    ```

    1. Схемы `OAuth` объявляют области доступа (scopes), поэтому извлекатель возвращает `PrincipalWithScopes`

Для `OAuth` возвращаемый principal должен реализовывать `PrincipalWithScopes`, чтобы сгенерированный контроллер мог проверять области доступа, объявленные для каждой операции.
Извлекатель нужен только тем схемам, которые контракт действительно использует; класс-маркер существует для каждой объявленной схемы:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record UserPrincipal(String name) implements PrincipalWithScopes {

        @Override
        public Collection<String> scopes() {
            return List.of("read", "write"); //(1)!
        }
    }
    ```

    1. Области доступа, предоставленные этому principal, сверяются с областями, требуемыми операцией

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class UserPrincipal(val name: String) : PrincipalWithScopes {

        override fun scopes(): Collection<String> {
            return listOf("read", "write") //(1)!
        }
    }
    ```

    1. Области доступа, предоставленные этому principal, сверяются с областями, требуемыми операцией

## Рекомендации { #recommendations }

???+ tip "Совет"

    Если что-то не генерируется плагином или поведение отличается от ожидаемого либо от других версий,
    внимательно проверьте [конфигурацию плагина](#configuration) и изучите настройки,
    поскольку они могут влиять на то, как генерируются классы.

    Начиная с версии плагина `7.0.0`, правило `SIMPLIFY_ONEOF_ANYOF`, включённое по умолчанию в `openapiNormalizer`,
    может приводить к некоторым неочевидным результатам генератора.
