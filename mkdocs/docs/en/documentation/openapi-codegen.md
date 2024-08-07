Module for creating declarative HTTP handlers [HTTP server](http-server.md)
or create declarative [HTTP clients](http-client.md) from OpenAPI contracts using [OpenAPI Generator plugin](https://openapi-generator.tech/docs/plugins#gradle).

## Dependency

===! ":fontawesome-brands-java: `Java`"

    Dependency `build.gradle`:
    ```groovy
    buildscript {
        dependencies {
            classpath("ru.tinkoff.kora:openapi-generator:1.1.7")
        }
    }
    ```

    Plugin dependency `build.gradle`:
    ```groovy
    plugins {
        id "org.openapi.generator" version "7.4.0"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Dependency `build.gradle.kts`:
    ```groovy
    buildscript {
        dependencies {
            classpath("ru.tinkoff.kora:openapi-generator:1.1.7")
        }
    }
    ```

    Plugin dependency `build.gradle.kts`:
    ```groovy
    plugins {
        id("org.openapi.generator") version("7.4.0")
    }
    ```

Requires [HTTP server](http-server.md) or [HTTP client](http-client.md) module.

## Configuration

Configuration is required for [OpenAPI Generator plugin](https://openapi-generator.tech/docs/plugins#gradle) parameters:

- Configuring Gradle plugin parameters in [documentation](https://github.com/OpenAPITools/openapi-generator/blob/v7.4.0/modules/openapi-generator-gradle-plugin/README.adoc).
- Configuring `configOptions` plugin parameter in [documentation](https://openapi-generator.tech/docs/generators/java/#config-options).
- Configuring `openapiNormalizer` plugin parameter in [documentation](https://openapi-generator.tech/docs/customization/#openapi-normalizer).

## Client

A minimal example of configuring a plugin to create a declarative HTTP client:

===! ":fontawesome-brands-java: `Java`"

    Kora's available plugin options:

    - `clientConfigPrefix` - configuration prefix of created HTTP clients
    - `tags` - possibility to put additional tags on created HTTP-clients
    - `interceptors` - ability to specify interceptors for HTTP clients
    - `primaryAuth` - specify which [authorization mechanism](http-client.md#authorization) to use as the primary one if several [securitySchemes]((https://swagger.io/docs/specification/authentication/)) are specified in OpenAPI
    - `securityConfigPrefix` - prefix of authorization mechanism configuration [Basic](http-client.md#basic)/[ApiKey](http-client.md#apikey) (configuration path will be specified prefix + name [securitySchemes]((https://swagger.io/docs/specification/authentication/)) in OpenAPI, or just name in OpenAPI if prefix is not specified).
    - `mode` in which mode the generator should operate, available values:
        * `java-client` - create synchronous client
        * `java-async-client` - create [CompletionStage](https://www.baeldung.com/java-completablefuture) client
        * `java-reactive-client` - create [reactive](https://projectreactor.io/docs/core/release/reference/) client, you need to connect [Project Reactor](https://mvnrepository.com/artifact/io.projectreactor/reactor-core) yourself.

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

    1. Path to OpenAPI file from which classes will be created
    2. Directory where the files will be created
    3. Package from classes of delegates, controllers, converters, etc.
    4. Package from classes of models, DTOs, etc.
    5. Package from calling classes
    6. Mode of plugin operation (creating Java client / Kotlin / Java server, etc.)
    7. Prefix path to client configuration file

=== ":simple-kotlin: `Kotlin`"

    Kora's available plugin options:

    - `clientConfigPrefix` - configuration prefix of created HTTP clients
    - `tags` - possibility to put additional tags on created HTTP-clients
    - `interceptors` - ability to specify interceptors for HTTP clients
    - `primaryAuth` - specify which [authorization mechanism](http-client.md#authorization) to use as the primary one if several [securitySchemes]((https://swagger.io/docs/specification/authentication/)) are specified in OpenAPI
    - `securityConfigPrefix` - prefix of authorization mechanism configuration [Basic](http-client.md#basic)/[ApiKey](http-client.md#apikey) (configuration path will be specified prefix + name [securitySchemes]((https://swagger.io/docs/specification/authentication/)) in OpenAPI, or just name in OpenAPI if prefix is not specified).
    - `mode` in which mode the generator should operate, available values:
        * `kotlin-client` - create synchronous client
        * `kotlin-suspend-client` - create suspend client

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

    1. Path to OpenAPI file from which classes will be created
    2. Directory where the files will be created
    3. Package from classes of delegates, controllers, converters, etc.
    4. Package from classes of models, DTOs, etc.
    5. Package from calling classes
    6. Mode of plugin operation (creating Java client / Kotlin / Java server, etc.)
    7. Prefix path to client configuration file

Once created, the HTTP client will be available for deployment as a dependency on the created interface.

### Interceptors

It is possible to put [interceptors](http-client.md#interceptors) on created clients with `@HttpClient` annotation.

The value is a Json object whose key is the api tag from the contract, and the value is an object with `type` and `tag` fields,
it is possible to specify both fields at the same time, or optionally one of them:

- `type` - the implementation class of a particular interceptor
- `tag` - tags of the interceptor (can be specified as an array of strings).

In order to do this, set the `configOptions.interceptors` parameter:

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

### Tags

It is possible to put parameters `httpClientTag` and `telemetryTag` on created clients with `@HttpClient` annotation.
The value is a Json object, the key of which is the api tag from the contract, and the value is the object with the fields `httpClientTag` and `telemetryTag`.

For this purpose it is necessary to set the `configOptions.tags` parameter:

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
                    "*": { // applies to all tags except those explicitly specified (in this case, instrument)
                      "httpClientTag": "some.tag.Common.class",
                      "telemetryTag": "some.tag.Common.class"
                    },
                    "instrument": { // apply to instrument
                      "httpClientTag": "some.tag.Instrument.class",
                      "telemetryTag": "some.tag.Instrument.class"
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
                            "*": { // applies to all tags except those explicitly specified (in this case, instrument)
                              "httpClientTag": "some.tag.Common.class",
                              "telemetryTag": "some.tag.Common.class"
                            },
                            "instrument": { // apply to instrument
                              "httpClientTag": "some.tag.Instrument.class",
                              "telemetryTag": "some.tag.Instrument.class"
                            }
                         }
                         """
        )
    }
    ```

## Server

A minimal example of configuring a plugin to create HTTP server handlers:

===! ":fontawesome-brands-java: `Java`"

    Available Kora plugin parameters:

    - `enableServerValidation` - whether to create validators according to the OpenAPI secification description for the server and whether to enable validation on HTTP handlers: `true, false`.
    - `requestInDelegateParams` - whether to expected `HttpServerRequest` as a method argument: `true, false`
    - `interceptors` - ability to specify interceptors for HTTP controllers
    - `mode` in which mode the generator should operate, available values:
        * `java-server` - create a synchronous server
        * `java-async-server` - create a [CompletionStage](https://www.baeldung.com/java-completablefuture) server
        * `java-reactive-server` - create a [reactive](https://projectreactor.io/docs/core/release/reference/) server, you need to connect [Project Reactor](https://mvnrepository.com/artifact/io.projectreactor/reactor-core) yourself.

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

    1. Path to OpenAPI file from which classes will be created
    2. Directory where the files will be created
    3. Package from classes of delegates, controllers, converters, etc.
    4. Package from classes of models, DTOs, etc.
    5. Package from calling classes
    6. Mode of plugin operation (creating Java client / Kotlin / Java server, etc.)

=== ":simple-kotlin: `Kotlin`"

    Available Kora plugin parameters:

    - `enableServerValidation` - whether to create validators according to the OpenAPI secification description for the server and whether to enable validation on HTTP handlers: `true, false`.
    - `requestInDelegateParams` - whether to expected `HttpServerRequest` as a method argument: `true, false`
    - `interceptors` - ability to specify interceptors for HTTP controllers
    - `mode` in which mode the generator should operate, available values:
        * `kotlin-server` - create synchronous server
        * `kotlin-suspend-server` - create suspend server

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

    1. Path to OpenAPI file from which classes will be created
    2. Directory where the files will be created
    3. Package from classes of delegates, controllers, converters, etc.
    4. Package from classes of models, DTOs, etc.
    5. Package from calling classes
    6. Mode of plugin operation (creating Java client / Kotlin / Java server, etc.)

Once created, the handlers will be automatically registered.

### Validation

In order to generate models and controllers with annotations from the [validation](validation.md) module, the `enableServerValidation` option must be set:

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

    1. Enabling validation on the HTTP server controller side

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

    1. Enabling validation on the HTTP server controller side

### Interceptors

It is possible to put [interceptors](http-server.md#interceptors) on created controllers with `@HttpController` annotation.

The value is a Json object whose key is the api tag from the contract, and the value is an object with `type` and `tag` fields,
it is possible to specify both fields at the same time, or optionally one of them:

- `type` - the implementation class of a particular interceptor
- `tag` - tags of the interceptor (can be specified as an array of strings).

In order to do this, set the `configOptions.interceptors` parameter:

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

## Recommendations

????+ warning "Advice"

    In case you have something that is not created by the plugin, or the behavior is different from what you want or other versions,
    you should carefully check the [plugin configuration](#configuration) settings and examine them, 
    as they may affect the results of how classes are created.

    Starting with `7.0.0` version of the plugin, the `SIMPLIFY_ONEOF_ANYOF` rule enabled by default at the `openapiNormalizer` parameter 
    may lead to some not obvious generator results.
