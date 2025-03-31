Модуль для создания декларативных HTTP-обработчиков [HTTP сервера](http-server.md) 
либо создания декларативных [HTTP клиентов](http-client.md) из OpenAPI контрактов с использованием [OpenAPI Generator плагином](https://openapi-generator.tech/docs/plugins#gradle).

## Подключение

===! ":fontawesome-brands-java: `Java`"

    Зависимость генератора `build.gradle`:
    ```groovy
    buildscript {
        dependencies {
            classpath("ru.tinkoff.kora:openapi-generator:1.1.23")
        }
    }
    ```

    Зависимость плагина `build.gradle`:
    ```groovy
    plugins {
        id "org.openapi.generator" version "7.4.0"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#_4) `build.gradle.kts`:
    ```groovy
    buildscript {
        dependencies {
            classpath("ru.tinkoff.kora:openapi-generator:1.1.23")
        }
    }
    ```

    Зависимость плагина `build.gradle.kts`:
    ```groovy
    plugins {
        id("org.openapi.generator") version("7.4.0")
    }
    ```

Требует подключения [HTTP сервера](http-server.md) либо [HTTP клиента](http-client.md).

## Конфигурация

Конфигурировать требуется параметры [плагина OpenAPI Generator](https://openapi-generator.tech/docs/plugins#gradle):

- Настройка параметров Gradle плагина в [документации](https://github.com/OpenAPITools/openapi-generator/blob/v7.4.0/modules/openapi-generator-gradle-plugin/README.adoc).
- Настройка `configOptions` параметра плагина в [документации](https://openapi-generator.tech/docs/generators/java/#config-options).
- Настройка `openapiNormalizer` параметра плагина в [документации](https://openapi-generator.tech/docs/customization/#openapi-normalizer).

## Клиент

Минимальный пример настройки плагина для создания декларативного HTTP клиента:

===! ":fontawesome-brands-java: `Java`"

    Доступные Kora параметры плагина (`configOptions`):

    - `clientConfigPrefix` - префикс конфигурации созданных HTTP-клиентов
    - `tags` - возможность проставлять дополнительные теги на созданные HTTP-клиенты
    - `interceptors` - возможность указывать перехватчики для HTTP-клиентов
    - `primaryAuth` - указать какой [механизм авторизации](http-client.md#_30) использовать как основной если указано несколько [securitySchemes]((https://swagger.io/docs/specification/authentication/)) в OpenAPI
    - `securityConfigPrefix` - префикс конфигурации механизм авторизации [Basic](http-client.md#basic)/[ApiKey](http-client.md#apikey) (путь конфигурации будет заданный префикс + имя [securitySchemes]((https://swagger.io/docs/specification/authentication/)) в OpenAPI, либо просто имя в OpenAPI если префикс не задан)
    - `authAsMethodArgument` - возможность указывать авторизацию как аргумент метода HTTP клиента, а не через перехватчик
    - `additionalContractAnnotations` - возможность указывать дополнительные аннотации над методами HTTP-клиента
    - `enableJsonNullable` - обрабатывать `nullable=true` и `required=false` поля схем как [JsonNullable](json.md#jsonnullable) обертку
    - `mode` в каком режиме работать генератору, доступные значения:
        * `java-client` - создание синхронного клиента
        * `java-async-client` - создание [CompletionStage](https://www.baeldung.com/java-completablefuture) клиента
        * `java-reactive-client` - создание [реактивного](https://projectreactor.io/docs/core/release/reference/) клиента, требуется подключить [Project Reactor](https://mvnrepository.com/artifact/io.projectreactor/reactor-core) самостоятельно.

    ```groovy
    openApiGenerate {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/openapi.yaml" //(1)!
        outputDir = "$buildDir/generated/openapi" //(2)!  
        apiPackage = "ru.tinkoff.kora.example.openapi.api" //(3)!
        modelPackage = "ru.tinkoff.kora.example.openapi.model" //(4)!
        invokerPackage = "ru.tinkoff.kora.example.openapi.invoker" //(5)!
        openapiNormalizer = [
            DISABLE_ALL: "true"
        ]
        configOptions = [
            mode: "java-client", //(6)!
            clientConfigPrefix: "httpClient.myclient" //(7)!
        ]
    }
    ```

    1. Путь до OpenAPI файла из которого будут созданы классы
    2. Директория куда буду создаваться файлы
    3. Пакет от классов делегатов, контроллеров, преобразователей и тп.
    4. Пакет от классов моделей, DTO и тп.
    5. Пакет от классов вызова
    6. Режим работы плагина (создание Java клиента / Kotlin / Java сервера и тп)
    7. Префикс путь к файлу конфигурации клиента

=== ":simple-kotlin: `Kotlin`"

    Доступные Kora параметры плагина (`configOptions`):

    - `clientConfigPrefix` - префикс конфигурации созданных HTTP-клиентов
    - `tags` - возможность проставлять дополнительные теги на созданные HTTP-клиенты
    - `interceptors` - возможность указывать перехватчики для HTTP-клиентов
    - `primaryAuth` - указать какой [механизм авторизации](http-client.md#_30) использовать как основной если указано несколько [securitySchemes]((https://swagger.io/docs/specification/authentication/)) в OpenAPI
    - `securityConfigPrefix` - префикс конфигурации механизм авторизации [Basic](http-client.md#basic)/[ApiKey](http-client.md#apikey) (путь конфигурации будет заданный префикс + имя [securitySchemes]((https://swagger.io/docs/specification/authentication/)) в OpenAPI, либо просто имя в OpenAPI если префикс не задан)
    - `authAsMethodArgument` - возможность указывать авторизацию как аргумент метода HTTP клиента, а не через перехватчик
    - `additionalContractAnnotations` - возможность указывать дополнительные аннотации над методами HTTP-клиента
    - `enableJsonNullable` - обрабатывать `nullable=true` и `required=false` поля схем как [JsonNullable](json.md#jsonnullable) обертку
    - `mode` в каком режиме работать генератору, доступные значения:
        * `kotlin-client` - создание синхронного клиента
        * `kotlin-suspend-client` - создание suspend клиента

    ```groovy
    openApiGenerate {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/openapi.yaml" //(1)!
        outputDir = "$buildDir/generated/openapi" //(2)!
        apiPackage = "ru.tinkoff.kora.example.openapi.api" //(3)!
        modelPackage = "ru.tinkoff.kora.example.openapi.model" //(4)!
        invokerPackage = "ru.tinkoff.kora.example.openapi.invoker" //(5)!
        openapiNormalizer = mapOf(
            "DISABLE_ALL" to "true"
        )
        configOptions = mapOf(
            "mode" to "kotlin-client", //(6)!
            "clientConfigPrefix" to "httpClient.myclient" //(7)!
        )
    }
    ```

    1. Путь до OpenAPI файла из которого будут созданы классы
    2. Директория куда буду создаваться файлы
    3. Пакет от классов делегатов, контроллеров, преобразователей и тп.
    4. Пакет от классов моделей, DTO и тп.
    5. Пакет от классов вызова
    6. Режим работы плагина (создание Java клиента / Kotlin / Java сервера и тп)
    7. Префикс путь к файлу конфигурации клиента

После создания HTTP-клиент будет доступен для внедрения как зависимость по созданному интерфейсу.

### Перехватчики

Есть возможность на созданные клиенты с `@HttpClient` аннотацией поставить [перехватчики](http-client.md#_29).

Значение - Json объект, ключом которого выступает тег апи из контракта, а значением объект с полями `type` и `tag`, 
можно указывать как оба поля одновременно, так и опционально одно из них на выбор где:

- `type` - класс реализации конкретного перехватчика
- `tag` - теги перехватчика (можно указать как массив строк)

Для этого необходимо установить параметр `configOptions.interceptors`:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    openApiGenerate {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/openapi.yaml"
        outputDir = "$buildDir/generated/openapi"
        apiPackage = "ru.tinkoff.kora.example.openapi.api"
        modelPackage = "ru.tinkoff.kora.example.openapi.model"
        invokerPackage = "ru.tinkoff.kora.example.openapi.invoker"
        openapiNormalizer = [
            DISABLE_ALL: "true"
        ]
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
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    openApiGenerate {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/openapi.yaml"
        outputDir = "$buildDir/generated/openapi"
        apiPackage = "ru.tinkoff.kora.example.openapi.api"
        modelPackage = "ru.tinkoff.kora.example.openapi.model"
        invokerPackage = "ru.tinkoff.kora.example.openapi.invoker"
        openapiNormalizer = mapOf(
            "DISABLE_ALL" to "true"
        )
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
    }
    ```

### Теги

Есть возможность на созданные клиенты с `@HttpClient` аннотацией поставить параметры  `httpClientTag` и `telemetryTag`.
Значение - Json объект, ключом которого выступает тег апи из контракта, а значением объект с полями `httpClientTag` и `telemetryTag`.

Для этого необходимо установить параметр `configOptions.tags`:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    openApiGenerate {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/openapi.yaml"
        outputDir = "$buildDir/generated/openapi"
        apiPackage = "ru.tinkoff.kora.example.openapi.api"
        modelPackage = "ru.tinkoff.kora.example.openapi.model"
        invokerPackage = "ru.tinkoff.kora.example.openapi.invoker"
        openapiNormalizer = [
            DISABLE_ALL: "true"
        ]
        configOptions = [
            mode: "java-client",
            clientConfigPrefix: "httpClient.myclient",
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
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    openApiGenerate {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/openapi.yaml"
        outputDir = "$buildDir/generated/openapi"
        apiPackage = "ru.tinkoff.kora.example.openapi.api"
        modelPackage = "ru.tinkoff.kora.example.openapi.model"
        invokerPackage = "ru.tinkoff.kora.example.openapi.invoker"
        openapiNormalizer = mapOf(
            "DISABLE_ALL" to "true"
        )
        configOptions = mapOf(
            "mode" to "kotlin-client",
            "clientConfigPrefix" to "httpClient.myclient",
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
    }
    ```

## Сервер

Минимальный пример настройки плагина для создания обработчиков HTTP-сервера:

===! ":fontawesome-brands-java: `Java`"

    Доступные Kora параметры плагина (`configOptions`):

    - `enableServerValidation` - создавать ли валидаторы по описанию OpenAPI сецификации для сервера и включать ли валидацию на HTTP-обработчиках: `true, false`
    - `requestInDelegateParams` - прокидывать ли `HttpServerRequest` принудительно как аргумент метода: `true, false`
    - `interceptors` - возможность указывать перехватчики для HTTP-контроллеров
    - `additionalContractAnnotations` - возможность указывать дополнительные аннотации над методами контроллера
    - `enableJsonNullable` - обрабатывать `nullable=true` и `required=false` поля схем как [JsonNullable](json.md#jsonnullable) обертку
    - `mode` в каком режиме работать генератору, доступные значения:
        * `java-server` - создание синхронного сервера
        * `java-async-server` - создание [CompletionStage](https://www.baeldung.com/java-completablefuture) сервера
        * `java-reactive-server` - создание [реактивного](https://projectreactor.io/docs/core/release/reference/) сервера, требуется подключить [Project Reactor](https://mvnrepository.com/artifact/io.projectreactor/reactor-core) самостоятельно.

    ```groovy
    openApiGenerate {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/openapi.yaml" //(1)!
        outputDir = "$buildDir/generated/openapi" //(2)!  
        apiPackage = "ru.tinkoff.kora.example.openapi.api" //(3)!
        modelPackage = "ru.tinkoff.kora.example.openapi.model" //(4)!
        invokerPackage = "ru.tinkoff.kora.example.openapi.invoker" //(5)!
        openapiNormalizer = [
            DISABLE_ALL: "true"
        ]
        configOptions = [
            mode: "java-server" //(6)!
        ]
    }
    ```

    1. Путь до OpenAPI файла из которого будут созданы классы
    2. Директория куда буду создаваться файлы
    3. Пакет от классов делегатов, контроллеров, преобразователей и тп.
    4. Пакет от классов моделей, DTO и тп.
    5. Пакет от классов вызова
    6. Режим работы плагина (создание Java клиента / Kotlin / Java сервера и тп)

=== ":simple-kotlin: `Kotlin`"

    Доступные Kora параметры плагина (`configOptions`):

    - `enableServerValidation` - создавать ли валидаторы по описанию OpenAPI сецификации для сервера и включать ли валидацию на HTTP-обработчиках: `true, false`
    - `requestInDelegateParams` - прокидывать ли `HttpServerRequest` принудительно как аргумент метода: `true, false`
    - `interceptors` - возможность указывать перехватчики для HTTP-контроллеров
    - `additionalContractAnnotations` - возможность указывать дополнительные аннотации над методами контроллера
    - `enableJsonNullable` - обрабатывать `nullable=true` и `required=false` поля схем как [JsonNullable](json.md#jsonnullable) обертку
    - `mode` в каком режиме работать генератору, доступные значения:
        * `kotlin-server` - создание синхронного сервера
        * `kotlin-suspend-server` - создание suspend сервера

    ```groovy
    openApiGenerate {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/openapi.yaml" //(1)!
        outputDir = "$buildDir/generated/openapi" //(2)!
        apiPackage = "ru.tinkoff.kora.example.openapi.api" //(3)!
        modelPackage = "ru.tinkoff.kora.example.openapi.model" //(4)!
        invokerPackage = "ru.tinkoff.kora.example.openapi.invoker" //(5)!
        openapiNormalizer = mapOf(
            "DISABLE_ALL" to "true"
        )
        configOptions = mapOf(
            "mode" to "kotlin-server" //(6)!
        )
    }
    ```

    1. Путь до OpenAPI файла из которого будут созданы классы
    2. Директория куда буду создаваться файлы
    3. Пакет от классов делегатов, контроллеров, преобразователей и тп.
    4. Пакет от классов моделей, DTO и тп.
    5. Пакет от классов вызова
    6. Режим работы плагина (создание Java клиента / Kotlin / Java сервера и тп)

После создания обработчики будут автоматически зарегистрированы.

### Валидация

Для генерации моделей и контроллеров с аннотациями из модуля [валидации](validation.md) необходимо установить опцию `enableServerValidation`:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    openApiGenerate {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/openapi.yaml"
        outputDir = "$buildDir/generated/openapi"
        apiPackage = "ru.tinkoff.kora.example.openapi.api"
        modelPackage = "ru.tinkoff.kora.example.openapi.model"
        invokerPackage = "ru.tinkoff.kora.example.openapi.invoker"
        openapiNormalizer = [
            DISABLE_ALL: "true"
        ]
        configOptions = [
            mode: "java-server",
            enableServerValidation: "true"  //(1)!
        ]
    }
    ```

    1. Включение валидации на стороне контроллера HTTP сервера

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    openApiGenerate {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/openapi.yaml"
        outputDir = "$buildDir/generated/openapi"
        apiPackage = "ru.tinkoff.kora.example.openapi.api"
        modelPackage = "ru.tinkoff.kora.example.openapi.model"
        invokerPackage = "ru.tinkoff.kora.example.openapi.invoker"
        openapiNormalizer = mapOf(
            "DISABLE_ALL" to "true"
        )
        configOptions = mapOf(
            "mode" to "kotlin-server",
            "enableServerValidation" to "true" //(1)!
        )
    }
    ```

    1. Включение валидации на стороне контроллера HTTP сервера

### Перехватчики

Есть возможность на созданные контроллеры с `@HttpController` аннотацией поставить [перехватчики](http-server.md#_20).

Значение - Json объект, ключом которого выступает тег апи из контракта, а значением объект с полями `type` и `tag`,
можно указывать как оба поля одновременно, так и опционально одно из них на выбор где:

- `type` - класс реализации конкретного перехватчика
- `tag` - теги перехватчика (можно указать как массив строк)

Для этого необходимо установить параметр `configOptions.interceptors`:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    openApiGenerate {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/openapi.yaml"
        outputDir = "$buildDir/generated/openapi"
        apiPackage = "ru.tinkoff.kora.example.openapi.api"
        modelPackage = "ru.tinkoff.kora.example.openapi.model"
        invokerPackage = "ru.tinkoff.kora.example.openapi.invoker"
        openapiNormalizer = [
            DISABLE_ALL: "true"
        ]
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
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    openApiGenerate {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/openapi.yaml"
        outputDir = "$buildDir/generated/openapi"
        apiPackage = "ru.tinkoff.kora.example.openapi.api"
        modelPackage = "ru.tinkoff.kora.example.openapi.model"
        invokerPackage = "ru.tinkoff.kora.example.openapi.invoker"
        openapiNormalizer = mapOf(
            "DISABLE_ALL" to "true"
        )
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
    }
    ```

### Авторизация

Kora предоставляет интерфейс для извлечения авторизационной информации в рамках перехватчика, 
созданного для сервера из OpenAPI, можно вытаскивать любые типы авторизации [Basic/ApiKey/Bearer/OAuth](https://swagger.io/docs/specification/authentication/)

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

## Рекомендации

???+ warning "Совет"

    В случае если у вас что-то не создается посредствам плагина, либо поведение отличается от желаемого или других версий,
    требуется тщательно проверить настройки [конфигурации плагина](#_2) и изучить их, 
    так как они могут влиять на результаты того как создаются классы.

    Начиная с `7.0.0` версии плагина, включенное по умолчанию `SIMPLIFY_ONEOF_ANYOF` правило у параметра `openapiNormalizer` 
    может вести к некоторым не очевидным результатам генератора.
