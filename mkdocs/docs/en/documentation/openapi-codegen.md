---
description: "Explains Kora OpenAPI code generation for HTTP clients and servers, generator options, tags, validation, interceptors, authorization, and JsonNullable support. Use when working with openapi-generator, @HttpClient, @HttpController, @InterceptWith, @Tag, @Validate, JsonNullable, primaryAuth."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora OpenAPI code generation for HTTP clients and servers, generator options, tags, validation, interceptors, authorization, and JsonNullable support; key triggers include openapi-generator, @HttpClient, @HttpController, @InterceptWith, @Tag, @Validate, JsonNullable, primaryAuth."
---

This module generates Kora code from an `OpenAPI` contract using [OpenAPI Generator](https://openapi-generator.tech/docs/plugins#gradle).
From a single API description, it can create declarative [HTTP server](http-server.md) handlers or declarative [HTTP clients](http-client.md),
as well as request and response models, mappers, authorization handling, and additional annotations.
This approach is useful when `OpenAPI` is the source of truth for the transport contract and application code must follow it automatically.

For a step-by-step walkthrough before the reference documentation, see [OpenAPI HTTP Server](../guides/openapi-http-server.md), [Advanced OpenAPI HTTP Server](../guides/openapi-http-server-advanced.md), and [OpenAPI HTTP Client](../guides/openapi-http-client.md).

## Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    Generator dependency in `build.gradle`:
    ```groovy
    buildscript {
        dependencies {
            classpath("ru.tinkoff.kora:openapi-generator:1.2.16")
        }
    }
    ```

    Plugin dependency in `build.gradle`:
    ```groovy
    plugins {
        id "org.openapi.generator" version "7.14.0"
    }
    ```

    Other plugin versions are not guaranteed to work because the `OpenAPI Generator` API can be incompatible at code level.

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) in `build.gradle.kts`:
    ```groovy
    buildscript {
        dependencies {
            classpath("ru.tinkoff.kora:openapi-generator:1.2.16")
        }
    }
    ```

    Plugin dependency in `build.gradle.kts`:
    ```groovy
    plugins {
        id("org.openapi.generator") version("7.14.0")
    }
    ```

    Other plugin versions are not guaranteed to work because the `OpenAPI Generator` API can be incompatible at code level.

Generated code also requires the [HTTP server](http-server.md) or [HTTP client](http-client.md) module, depending on the selected generation mode.

## Configuration { #configuration }

Configure the [OpenAPI Generator plugin](https://openapi-generator.tech/docs/plugins#gradle) parameters:

- `Gradle` plugin parameters are described in the [plugin documentation](https://github.com/OpenAPITools/openapi-generator/blob/v7.14.0/modules/openapi-generator-gradle-plugin/README.adoc).
- The `configOptions` plugin parameter is described in the [configuration documentation](https://openapi-generator.tech/docs/configuration/).
- The `openapiNormalizer` plugin parameter is described in the [customization documentation](https://openapi-generator.tech/docs/customization/#openapi-normalizer).

### Common `OpenAPI Generator` Options { #common-generator-options }

In addition to Kora-specific `configOptions`, `GenerateTask` accepts common `OpenAPI Generator` parameters.
They define where to read the contract from, where to put generated files, which packages to use, and how to preprocess the `OpenAPI` description.
For Kora projects, these parameters are usually set explicitly because generated code is then added to normal project compilation.

| Parameter | Description |
| -------- | -------- |
| `generatorName` | Generator name (`required`, no default). Always set it to `kora` for Kora. |
| `inputSpec` | Path to the `OpenAPI` file (`required`, no default). Usually this is a file under `src/main/resources/openapi`, for example `$projectDir/src/main/resources/openapi/openapi.yaml`. |
| `outputDir` | Directory for generated files (not specified by default, optional). In Kora projects, this is usually a directory under `build`, for example `$buildDir/generated/openapi`, and it is added to the main source set. |
| `apiPackage` | Package for generated API interfaces, controllers, `delegate` classes, and mappers (default: `org.openapitools.api`). It is recommended to set it explicitly, for example `ru.tinkoff.kora.example.openapi.api`. |
| `modelPackage` | Package for models generated from `OpenAPI` schemas (default: `org.openapitools.model`). It is recommended to set it explicitly, for example `ru.tinkoff.kora.example.openapi.model`. |
| `invokerPackage` | Auxiliary generator package (default: `org.openapitools.api`). It is recommended to set it explicitly next to `apiPackage` and `modelPackage`, for example `ru.tinkoff.kora.example.openapi.invoker`. |
| `configOptions` | Generator-specific parameters (default: `{}`). For Kora, this is where `mode`, `clientConfigPrefix`, `enableServerValidation`, `interceptors`, and the other parameters described below are set. |
| `globalProperties` | Limits which entities are generated (default: `{}`). Useful when you need to generate only `apis`, only `models`, or specific models and operations. Use carefully: normal Kora clients and servers usually need API classes, models, and mappers together. |
| `openapiNormalizer` | Preprocesses the `OpenAPI` contract before generation (default: `{}`). Often used to disable standard transformations with `DISABLE_ALL`, generate only selected operations with `FILTER`, or control rules such as `SIMPLIFY_ONEOF_ANYOF`. |
| `importMappings` | Maps a schema name to an existing class (default: `{}`). Useful when a model is written manually or comes from another module, for example `Money: "com.example.Money"`. |
| `typeMappings` | Maps an `OpenAPI Generator` type to a language type (default: `{}`). Used for targeted type replacement, for example replacing `OffsetDateTime` with a project-specific time type. |
| `schemaMappings` | Maps an `OpenAPI` schema to an external type without generating the model (default: `{}`). Similar to `importMappings`, but configured at schema level and useful for reusing shared DTOs. |
| `skipValidateSpec` | Skips `OpenAPI` contract validation before generation (default: `false`). In normal builds it is better to keep validation enabled; use `true` only temporarily for external contracts that cannot be fixed quickly. |
| `cleanupOutput` | Cleans `outputDir` before generation (default: `false`). Useful when the contract changes often and files from removed operations or models must disappear. Do not point `outputDir` to a directory with handwritten code. |

Example with common options:

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

Use `globalProperties` only for narrow generation tasks, for example when extracting a few models into an intermediate module:

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

### Useful `openapiNormalizer` Rules { #openapi-normalizer }

`openapiNormalizer` changes the input `OpenAPI` contract before generation. It is not a Kora parameter, but a general `OpenAPI Generator` mechanism.
For Kora, it is especially useful when one large contract is used by several applications or when the contract contains ambiguous shapes for code generation.

| Rule | Description |
| -------- | -------- |
| `DISABLE_ALL` | Disables standard normalization rules (default: `false`). Starting with `OpenAPI Generator 7`, some rules are enabled by default, so predictable generation often starts with `DISABLE_ALL: "true"` and then enables only the needed rules explicitly. |
| `FILTER` | Keeps only selected operations for generation (not specified by default, optional). Supports one filter at a time: `operationId:name1\|name2`, `method:get\|post`, or `tag:public\|billing`. Operations that do not match are marked as `x-internal: true` and are not generated. |
| `KEEP_ONLY_FIRST_TAG_IN_OPERATION` | Keeps only the first tag on an operation (default: `false`). Useful when operations have several tags and are split into several API classes differently from what you expect. |
| `SET_TAGS_FOR_ALL_OPERATIONS` | Replaces tags on all operations with one provided value (not specified by default, optional). Useful when you want to force one generated API class. |
| `SET_TAGS_TO_OPERATIONID` | Sets an operation tag to `operationId`, or to `default` when `operationId` is empty (default: `false`). Useful for contracts without usable tags when predictable operation grouping is needed. |
| `SET_TAGS_TO_VENDOR_EXTENSION` | Reads operation tags from the specified extension, for example `x-tags` (not specified by default, optional). Useful when an external contract cannot be changed but already has custom operation grouping. |
| `FIX_DUPLICATED_OPERATIONID` | Adds a numeric suffix to duplicated `operationId` values (default: `false`). It is better to fix the contract, but this rule helps generate code for an external description temporarily. |
| `SET_BEARER_AUTH_FOR_NAME` | Converts the specified security scheme to `bearerAuth` (not specified by default, optional). Useful for external contracts where a bearer token is described in a non-standard way but should be handled as a normal bearer scheme in the application. |
| `REF_AS_PARENT_IN_ALLOF` | Marks a `$ref` inside `allOf` as a parent schema with `x-parent: true` (default: `false`). Can help contracts that model inheritance through `allOf`. |
| `SIMPLIFY_ONEOF_ANYOF` | Simplifies some `oneOf`/`anyOf` constructs, for example by moving a `null` variant to `nullable: true` and removing single wrappers (enabled by default in `OpenAPI Generator 7` unless `DISABLE_ALL` is set). For Kora, this can change generated model shapes, so enable it deliberately. |
| `SIMPLIFY_ANYOF_STRING_AND_ENUM_STRING` | Simplifies `anyOf` made from `string` and a string enum to `string` (default: `false`). This can help with contracts where the enum restriction is not important for code. |
| `SIMPLIFY_BOOLEAN_ENUM` | Converts a boolean enum to a plain `boolean` (enabled by default in `OpenAPI Generator 7` unless `DISABLE_ALL` is set). |
| `REFACTOR_ALLOF_WITH_PROPERTIES_ONLY` | Moves properties from a schema that has both `allOf` and `properties` into a separate schema inside `allOf` (enabled by default in `OpenAPI Generator 7` unless `DISABLE_ALL` is set). This can help inheritance, but strict contracts should be checked after generation. |
| `NORMALIZE_31SPEC` | Normalizes some `OpenAPI 3.1` constructs into a form better understood by the generator (default: `false`). Useful for `3.1` contracts when generation fails on newer schema forms. |
| `REMOVE_X_INTERNAL` | Removes `x-internal: true` from operations and models (default: `false`). Use only when the contract already contains `x-internal`, but a specific generation task must force such operations back in. |
| `SET_CONTAINER_TO_NULLABLE` | Marks container types `array`, `set`, or `map` as `nullable` (not specified by default, optional). Use only when an external contract systematically misses `nullable` on such fields. |
| `SET_PRIMITIVE_TYPES_TO_NULLABLE` | Marks primitive types `string`, `integer`, `number`, or `boolean` as `nullable` (not specified by default, optional). This significantly changes model signatures, so apply it only to problematic external contracts. |

Example of generating only the public part of a contract:

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

`FILTER` excludes only operations by itself. If unused models should also be removed after filtering, enable the Kora `filterWithModels` parameter.
For more complex selection, usually create separate generation tasks with different `FILTER` values, for example one with `tag:billing` and another with `operationId:createUser|getUser`.

Example of normalizing tags for a contract without convenient grouping:

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

### Common `JSON` and Model Options { #common-model-options }

Kora also supports several `configOptions` that control `JSON` mappers and common model generation.
They do not depend on whether a client or a server is generated.

| Parameter | Description |
| -------- | -------- |
| `jsonAnnotation` | Annotation tag used to inject `JSON` mappers into generated request and response mappers (default: `ru.tinkoff.kora.json.common.annotation.Json`). |
| `objectType` | Type for `type: object` schemas without a more precise description. `Java` uses `java.lang.Object` by default, and `Kotlin` uses `kotlin.Any`. For example, set it to `com.fasterxml.jackson.databind.JsonNode` if the application wants to handle arbitrary `JSON` as a tree. |
| `disableHtmlEscaping` | Disables HTML character escaping in `JSON` strings (default: `false`). Usually the default value is kept. |
| `ignoreAnyOfInEnum` | Ignores `anyOf` when generating enums (default: `false`). Can help with contracts where an enum is described through mixed `anyOf` constructs. |
| `additionalModelTypeAnnotations` | Additional annotations on model types (not specified by default, optional). Several annotations are separated by `;`, for example `@Deprecated;@MyAnnotation`. |
| `additionalEnumTypeAnnotations` | Additional annotations on enum types (not specified by default, optional). Several annotations are separated by `;`. |

Example:

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

## Client { #client }

A minimal plugin configuration for creating a declarative HTTP client:

===! ":fontawesome-brands-java: `Java`"

    For clients, `configOptions.mode` supports `java-client`, `java-async-client`, and `java-reactive-client`.
    Other client parameters are described below in the authorization, interceptors, tags, models, and implicit headers sections.

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

    1. Path to the `OpenAPI` file used to create classes
    2. Directory where generated files are created
    3. Package for delegates, controllers, and mappers
    4. Package for models and DTOs
    5. Auxiliary generator package
    6. Plugin mode
    7. Client configuration path prefix
    8. Register generated classes as project source code
    9. Make code compilation depend on HTTP client class generation: generate first, compile after

=== ":simple-kotlin: `Kotlin`"

    For clients, `configOptions.mode` supports `kotlin-client` and `kotlin-suspend-client`.
    Other client parameters are described below in the authorization, interceptors, tags, models, and implicit headers sections.

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

    1. Path to the `OpenAPI` file used to create classes
    2. Directory where generated files are created
    3. Package for delegates, controllers, and mappers
    4. Package for models and DTOs
    5. Auxiliary generator package
    6. Plugin mode
    7. Client configuration path prefix
    8. Register generated classes as project source code
    9. Make code compilation depend on HTTP client class generation: generate first, compile after

After generation, the HTTP client is available for dependency injection through the generated interface.

### Client Authorization { #client-authorization }

If the `OpenAPI` contract describes `securitySchemes`, the generator creates an `ApiSecurity` module with components for client authorization.
For `apiKey` and `basic`, configuration-reading components are generated. For `bearer` and `oauth`, a matching tagged `HttpClientTokenProvider` component is expected.

`securityConfigPrefix` sets a common authorization configuration prefix. If the prefix is not specified, the configuration path is the `securitySchemes` name.
If an operation has several authorization schemes, `primaryAuth` can be specified; otherwise the generator picks one of the schemes and logs a warning.
If `authAllowMultiple` is enabled, the generator creates a composite interceptor that applies several authorization schemes sequentially.
If `authAsMethodArgument` is enabled, authorization data is added to the client method signature instead of a generated interceptor.

### Additional Annotations { #additional-contract-annotations }

The `additionalContractAnnotations` parameter adds annotations above generated client or server controller methods.
The value is a `JSON` object where the key is the API tag from the contract, or `*` for all operations, and the value is an array of objects with the `annotation` field.

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

### Interceptors { #interceptors }

Generated clients annotated with `@HttpClient` can also be annotated with [interceptors](http-client.md#interceptors).
The value is a `JSON` object where the key is an API tag from the contract and the value is an array of objects with `type` and `tag` fields.
Both fields can be specified together, or only one of them can be specified:

- `type` - implementation class of a concrete interceptor
- `tag` - interceptor tags, either a string or an array of strings

Set `configOptions.interceptors`:

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

### Tags { #tags }

Generated clients annotated with `@HttpClient` can receive `httpClientTag` and `telemetryTag` parameters.
The value is a `JSON` object where the key is an API tag from the contract and the value is an object with `httpClientTag` and `telemetryTag` fields.

Set `configOptions.tags`:

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

## Implicit Headers { #implicit-headers }

By default, headers from an `OpenAPI` operation become generated method arguments.
If some headers are supplied by infrastructure rather than application code, they can be made implicit.

- `implicitHeaders = true` makes all headers from `OpenAPI` operations implicit.
- `implicitHeadersRegex` makes only headers whose names match the regular expression implicit.

An implicit header is removed from the method signature but remains in `OpenAPI` annotations in generated code.
This keeps the header in contract documentation without requiring application code to pass it manually.

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

## Models { #models }

The generator creates request and response models from `OpenAPI` schemas.
Optional fields use `@Nullable` in `Java` and nullable type `T?` in `Kotlin`.
For schemas with inheritance and a discriminator, `Java` can generate `sealed interface`, and `Kotlin` can generate `sealed interface` / classes depending on the schema.

### Optional Nullable Fields { #json-nullable }

If a field is both `nullable: true` and absent from the `required` list, it is generated as a normal optional field by default.
If you need to distinguish three states - the field is absent in `JSON`, the field is present with `null`, and the field is present with a value - enable `enableJsonNullable`.
In that case, the field is generated as [JsonNullable](json.md#jsonnullable-wrapper).

`forceIncludeOptional` and `forceIncludeNonRequired` control serialization of optional fields:

- `forceIncludeOptional` sets `@JsonInclude(Always)` for fields with `nullable: true` and `required: false` instead of using `JsonNullable`.
- `forceIncludeNonRequired` sets `@JsonInclude(Always)` for all fields with `required: false`.

`forceIncludeOptional` cannot be enabled together with `enableJsonNullable` because both modes solve the same problem in different ways.

### Model Filtering { #filter-with-models }

`OpenAPI Generator` can filter operations through `openapiNormalizer.FILTER`.
If `filterWithModels` is additionally enabled, the Kora generator tries to exclude unused models that remain after operation filtering.
This is useful for large contracts where an application generates only part of the API.

## Server { #server }

A minimal plugin configuration for creating HTTP server handlers:

===! ":fontawesome-brands-java: `Java`"

    For servers, `configOptions.mode` supports `java-server`, `java-async-server`, and `java-reactive-server`.
    Other server parameters are described below in the validation, `delegate` classes, interceptors, models, and implicit headers sections.

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

    1. Path to the `OpenAPI` file used to create classes
    2. Directory where generated files are created
    3. Package for delegates, controllers, and mappers
    4. Package for models and DTOs
    5. Auxiliary generator package
    6. Plugin mode
    7. Register generated classes as project source code
    8. Make code compilation depend on HTTP server class generation: generate first, compile after

=== ":simple-kotlin: `Kotlin`"

    For servers, `configOptions.mode` supports `kotlin-server` and `kotlin-suspend-server`.
    Other server parameters are described below in the validation, `delegate` classes, interceptors, models, and implicit headers sections.

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

    1. Path to the `OpenAPI` file used to create classes
    2. Directory where generated files are created
    3. Package for delegates, controllers, and mappers
    4. Package for models and DTOs
    5. Auxiliary generator package
    6. Plugin mode
    7. Register generated classes as project source code
    8. Make code compilation depend on HTTP server class generation: generate first, compile after

After generation, handlers are registered automatically.

### Validation { #validation }

To generate models and controllers with annotations from the [validation](validation.md) module, set `enableServerValidation`:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    configOptions = [
        mode: "java-server",
        enableServerValidation: "true"  //(1)!
    ]
    ```

    1. Enables validation on the HTTP server controller side

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    configOptions = mapOf(
        "mode" to "kotlin-server",
        "enableServerValidation" to "true" //(1)!
    )
    ```

    1. Enables validation on the HTTP server controller side

When `enableServerValidation` is enabled, the generator adds validation annotations to models and server method parameters,
and also adds `@Validate` to controller methods with validated parameters.
`enableServerValidationInterceptor` controls adding `ValidationHttpServerInterceptor`, which converts validation errors to HTTP responses.
If `enableServerValidationInterceptor` is not specified explicitly, it is considered enabled when server validation is enabled.
If `enableServerValidationInterceptor = false` is specified, validation annotations remain, but the standard response interceptor is not added.

### Delegate Implementation { #delegate-method-body }

The server generator creates a controller and a `delegate` contract where the user implements application logic.
By default, `delegateMethodBodyMode = none`, so `delegate` contract methods do not get a standard body and must be implemented by the application.

If `delegateMethodBodyMode = throwException` is set, methods get a body that throws an exception, and the generator also creates a module
with a default `delegate` contract implementation. This mode is useful when the application must be built before all operations are implemented, or when custom implementations are connected gradually.

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

### Interceptors { #interceptors-2 }

Generated controllers annotated with `@HttpController` can also be annotated with [interceptors](http-server.md#interceptors).
The value is a `JSON` object where the key is an API tag from the contract and the value is an object with `type` and `tag` fields.
Both fields can be specified together, or only one of them can be specified:

- `type` - implementation class of a concrete interceptor
- `tag` - interceptor tags, either a string or an array of strings

Set `configOptions.interceptors`:

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

### Authorization { #authorization }

Kora provides an interface for extracting authorization information inside the interceptor created for the server from `OpenAPI`.
Different authorization types can be handled: [Basic/ApiKey/Bearer/OAuth](https://swagger.io/docs/specification/authentication/).

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

## Recommendations { #recommendations }

???+ tip "Advice"

    If something is not generated by the plugin, or behavior differs from expectations or from other versions,
    carefully check the [plugin configuration](#configuration) and study the settings,
    because they can affect how classes are generated.

    Starting with plugin version `7.0.0`, the `SIMPLIFY_ONEOF_ANYOF` rule enabled by default in `openapiNormalizer`
    can lead to some non-obvious generator results.
