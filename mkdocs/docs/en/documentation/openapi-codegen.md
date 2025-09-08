Module for creating declarative HTTP handlers [HTTP server](http-server.md)
or create declarative [HTTP clients](http-client.md) from OpenAPI contracts using [OpenAPI Generator plugin](https://openapi-generator.tech/docs/plugins#gradle).

## Dependency

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    buildscript {
        dependencies {
            classpath("ru.tinkoff.kora:openapi-generator:1.2.2")
        }
    }
    ```

    Plugin dependency `build.gradle`:
    ```groovy
    plugins {
        id "org.openapi.generator" version "7.14.0"
    }

    Use of other versions of the plugin is not guaranteed as it may not be compatible at the code level.
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    buildscript {
        dependencies {
            classpath("ru.tinkoff.kora:openapi-generator:1.2.2")
        }
    }
    ```

    Plugin dependency `build.gradle.kts`:
    ```groovy
    plugins {
        id("org.openapi.generator") version("7.14.0")
    }

    Use of other versions of the plugin is not guaranteed as it may not be compatible at the code level.
    ```

Requires [HTTP server](http-server.md) or [HTTP client](http-client.md) module.

## Configuration

Configuration is required for [OpenAPI Generator plugin](https://openapi-generator.tech/docs/plugins#gradle) parameters:

- Configuring Gradle plugin parameters in [documentation](https://github.com/OpenAPITools/openapi-generator/blob/v7.14.0/modules/openapi-generator-gradle-plugin/README.adoc).
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
    - `authAsMethodArgument` - ability to specify authorization as an argument of an HTTP client method rather than through an interceptor
    - `additionalContractAnnotations` - ability to specify additional annotations over HTTP client methods
    - `enableJsonNullable` - Treat `nullable=true` and `required=false` schema fields as a [JsonNullable](json.md#jsonnullable-wrapper) wrapper
    - `forceIncludeOptional` - Force to set `@JsonInclude(Always)` for fields with `nullable=true` and `required=false` instead of `enableJsonNullable`. Values: `true`, `false`.
    - `filterWithModels` - filter and exclude also unnecessary models from generation when the [FILTER](https://openapi-generator.tech/docs/customization/#available-filters) option in `openapiNormalizer` is specified
    - `mode` in which mode the generator should operate, available values:
        * `java-client` - create synchronous client
        * `java-async-client` - create [CompletionStage](https://www.baeldung.com/java-completablefuture) client
        * `java-reactive-client` - create [reactive](https://projectreactor.io/docs/core/release/reference/) client, you need to connect [Project Reactor](https://mvnrepository.com/artifact/io.projectreactor/reactor-core) yourself.

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

    1. Path to OpenAPI file from which classes will be created
    2. Directory where the files will be created
    3. Package from classes of delegates, controllers, converters, etc.
    4. Package from classes of models, DTOs, etc.
    5. Package from calling classes
    6. Mode of plugin operation (creating Java client / Kotlin / Java server, etc.)
    7. Prefix path to client configuration file
    8. Register the generated classes as the source code of the project
    9. Make code compilation dependent on HTTP client class generation (first generate, then compile)

=== ":simple-kotlin: `Kotlin`"

    Kora's available plugin options:

    - `clientConfigPrefix` - configuration prefix of created HTTP clients
    - `tags` - possibility to put additional tags on created HTTP-clients
    - `interceptors` - ability to specify interceptors for HTTP clients
    - `primaryAuth` - specify which [authorization mechanism](http-client.md#authorization) to use as the primary one if several [securitySchemes]((https://swagger.io/docs/specification/authentication/)) are specified in OpenAPI
    - `securityConfigPrefix` - prefix of authorization mechanism configuration [Basic](http-client.md#basic)/[ApiKey](http-client.md#apikey) (configuration path will be specified prefix + name [securitySchemes]((https://swagger.io/docs/specification/authentication/)) in OpenAPI, or just name in OpenAPI if prefix is not specified).
    - `authAsMethodArgument` - ability to specify authorization as an argument of an HTTP client method rather than through an interceptor
    - `additionalContractAnnotations` - ability to specify additional annotations over HTTP client methods
    - `enableJsonNullable` - Treat `nullable=true` and `required=false` schema fields as a [JsonNullable](json.md#jsonnullable-wrapper) wrapper
    - `forceIncludeOptional` - Force to set `@JsonInclude(Always)` for fields with `nullable=true` and `required=false` instead of `enableJsonNullable`. Values: `true`, `false`.
    - `filterWithModels` - filter and exclude also unnecessary models from generation when the [FILTER](https://openapi-generator.tech/docs/customization/#available-filters) option in `openapiNormalizer` is specified
    - `mode` in which mode the generator should operate, available values:
        * `kotlin-client` - create synchronous client
        * `kotlin-suspend-client` - create suspend client

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

    1. Path to OpenAPI file from which classes will be created
    2. Directory where the files will be created
    3. Package from classes of delegates, controllers, converters, etc.
    4. Package from classes of models, DTOs, etc.
    5. Package from calling classes
    6. Mode of plugin operation (creating Java client / Kotlin / Java server, etc.)
    7. Prefix path to client configuration file
    8. Register the generated classes as the source code of the project
    9. Make code compilation dependent on HTTP client class generation (first generate, then compile)

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

### Tags

It is possible to put parameters `httpClientTag` and `telemetryTag` on created clients with `@HttpClient` annotation.
The value is a Json object, the key of which is the api tag from the contract, and the value is the object with the fields `httpClientTag` and `telemetryTag`.

For this purpose it is necessary to set the `configOptions.tags` parameter:

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

## Server

A minimal example of configuring a plugin to create HTTP server handlers:

===! ":fontawesome-brands-java: `Java`"

    Available Kora plugin parameters:

    - `enableServerValidation` - whether to create validators according to the OpenAPI secification description for the server and whether to enable validation on HTTP handlers: `true, false`.
    - `requestInDelegateParams` - whether to expected `HttpServerRequest` as a method argument: `true, false`
    - `interceptors` - ability to specify interceptors for HTTP controllers
    - `additionalContractAnnotations` - ability to specify additional annotations for controller methods
    - `enableJsonNullable` - Treat `nullable=true` and `required=false` schema fields as a [JsonNullable](json.md#jsonnullable-wrapper) wrapper
    - `forceIncludeOptional` - Force to set `@JsonInclude(Always)` for fields with `nullable=true` and `required=false` instead of `enableJsonNullable`. Values: `true`, `false`.
    - `filterWithModels` - filter and exclude also unnecessary models from generation when the [FILTER](https://openapi-generator.tech/docs/customization/#available-filters) option in `openapiNormalizer` is specified
    - `prefixPath` - path prefix for HTTP-server controllers
    - `delegateMethodBodyMode` - behavior for method body generation in delegate class. `none` - do not generate method body, `throw-exception` - throw exception in method body. For `throw-exception` additionally generates module with default Delegate class implementation if not exists another implementation in application graph
    - `mode` in which mode the generator should operate, available values:
        * `java-server` - create a synchronous server
        * `java-async-server` - create a [CompletionStage](https://www.baeldung.com/java-completablefuture) server
        * `java-reactive-server` - create a [reactive](https://projectreactor.io/docs/core/release/reference/) server, you need to connect [Project Reactor](https://mvnrepository.com/artifact/io.projectreactor/reactor-core) yourself.

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
            mode: "java-server" //(6)!
        ]
    }
    sourceSets.main { java.srcDirs += openApiGenerateHttpServer.get().outputDir } //(7)!
    compileJava.dependsOn openApiGenerateHttpServer //(8)!
    ```

    1. Path to OpenAPI file from which classes will be created
    2. Directory where the files will be created
    3. Package from classes of delegates, controllers, converters, etc.
    4. Package from classes of models, DTOs, etc.
    5. Package from calling classes
    6. Mode of plugin operation (creating Java client / Kotlin / Java server, etc.)
    7. Register the generated classes as the source code of the project
    8. Make code compilation dependent on HTTP client class generation (first generate, then compile)

=== ":simple-kotlin: `Kotlin`"

    Available Kora plugin parameters:

    - `enableServerValidation` - whether to create validators according to the OpenAPI secification description for the server and whether to enable validation on HTTP handlers: `true, false`.
    - `requestInDelegateParams` - whether to expected `HttpServerRequest` as a method argument: `true, false`
    - `interceptors` - ability to specify interceptors for HTTP controllers
    - `additionalContractAnnotations` - ability to specify additional annotations for controller methods
    - `enableJsonNullable` - Treat `nullable=true` and `required=false` schema fields as a [JsonNullable](json.md#jsonnullable-wrapper) wrapper
    - `forceIncludeOptional` - Force to set `@JsonInclude(Always)` for fields with `nullable=true` and `required=false` instead of `enableJsonNullable`. Values: `true`, `false`.
    - `filterWithModels` - filter and exclude also unnecessary models from generation when the [FILTER](https://openapi-generator.tech/docs/customization/#available-filters) option in `openapiNormalizer` is specified
    - `prefixPath` - path prefix for HTTP-server controllers
    - `delegateMethodBodyMode` - behavior for method body generation in delegate class. `none` - do not generate method body, `throw-exception` - throw exception in method body. For `throw-exception` additionally generates module with default Delegate class implementation if not exists another implementation in application graph
    - `mode` in which mode the generator should operate, available values:
        * `kotlin-server` - create synchronous server
        * `kotlin-suspend-server` - create suspend server

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

    1. Path to OpenAPI file from which classes will be created
    2. Directory where the files will be created
    3. Package from classes of delegates, controllers, converters, etc.
    4. Package from classes of models, DTOs, etc.
    5. Package from calling classes
    6. Mode of plugin operation (creating Java client / Kotlin / Java server, etc.)
    7. Register the generated classes as the source code of the project
    8. Make code compilation dependent on HTTP client class generation (first generate, then compile)

Once created, the handlers will be automatically registered.

### Validation

In order to generate models and controllers with annotations from the [validation](validation.md) module, the `enableServerValidation` option must be set:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    configOptions = [
        mode: "java-server",
        enableServerValidation: "true"  //(1)!
    ]
    ```

    1. Enabling validation on the HTTP server controller side

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    configOptions = mapOf(
        "mode" to "kotlin-server",
        "enableServerValidation" to "true" //(1)!
    )
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

### Authorization

Kora provides an interface to extract authorization information within the interceptor,
created for the server from OpenAPI, you can pull any type of authorization [Basic/ApiKey/Bearer/OAuth](https://swagger.io/docs/specification/authentication/)

===! ":fontawesome-brands-java: ``Java``"

    ```java
    @Module
    public interface AuthModule {
     
        @Tag(ApiSecurity.BearerAuth.class)
        default HttpServerPrincipalExtractor<Principal> bearerHttpServerPrincipalExtractor() {
            return (request, value) -> CompletableFuture.completedFuture(new MyPrincipal(request.headers().getFirst(“Authorization”)));
        }
    }
    ```

=== ":simple-kotlin: ``Kotlin``"

    ```kotlin
    @Module
    interface AuthModule {

        @Tag(ApiSecurity.BearerAuth::class)
        fun bearerHttpServerPrincipalExtractor(): HttpServerPrincipalExtractor<Principal> {
            return HttpServerPrincipalExtractor<Principal> { request, value ->
                CompletableFuture.completedFuture<Principal>(
                    MyPrincipal(request.headers().getFirst(“Authorization”)))
                )
            }
        }
    }
    ```

## Recommendations

????+ warning "Advice"

    In case you have something that is not created by the plugin, or the behavior is different from what you want or other versions,
    you should carefully check the [plugin configuration](#configuration) settings and examine them, 
    as they may affect the results of how classes are created.

    Starting with `7.0.0` version of the plugin, the `SIMPLIFY_ONEOF_ANYOF` rule enabled by default at the `openapiNormalizer` parameter 
    may lead to some not obvious generator results.
