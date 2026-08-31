---
description: "Explains Kora OpenAPI code generation for HTTP clients and servers, generator modes, configuration options, generator extensions, validation, authorization and JsonNullable models. Use when working with openapi-generator, mode, clientConfig, clientConfigPrefix, securityConfigPrefix, extensions, rawBodyMode, delegateMethodBodyMode, prefixPath, requestInDelegateParams, ApiSecurity, HttpClientTokenProvider, HttpServerPrincipalExtractor, PrincipalWithScopes."
agent:
    use_when: "Use this file for Kora docs or implementation questions about Kora OpenAPI code generation for HTTP clients and servers, the four generation modes, generator configOptions, generator extensions for annotations and interceptors, server validation, generated authorization and models; key triggers include openapi-generator, java-client, java-server, kotlin-client, kotlin-server, clientConfig, clientConfigPrefix, securityConfigPrefix, extensions, rawBodyMode, delegateMethodBodyMode, prefixPath, requestInDelegateParams, ApiSecurity, HttpClientTokenProvider, HttpServerPrincipalExtractor, PrincipalWithScopes, fromValue."
---

This module generates Kora code from an `OpenAPI` contract using [OpenAPI Generator](https://openapi-generator.tech/docs/plugins#gradle).
From a single API description, it can create declarative [HTTP server](http-server.md) handlers or declarative [HTTP clients](http-client.md),
as well as request and response models, mappers, authorization handling, and additional annotations.
This approach is useful when `OpenAPI` is the source of truth for the transport contract and application code must follow it automatically.

For a step-by-step walkthrough before the reference documentation,
see [OpenAPI HTTP Server](../guides/openapi-http-server.md), [Advanced OpenAPI HTTP Server](../guides/openapi-http-server-advanced.md), and [OpenAPI HTTP Client](../guides/openapi-http-client.md).

## Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    Generator dependency in `build.gradle`:
    ```groovy
    buildscript {
        dependencies {
            classpath("io.koraframework:openapi-generator:2.0.0.RC1")
        }
    }
    ```

    Plugin dependency in `build.gradle`:
    ```groovy
    plugins {
        id "org.openapi.generator" version "7.24.0"
    }
    ```

    Other plugin versions are not guaranteed to work because the `OpenAPI Generator` API can be incompatible at code level.

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) in `build.gradle.kts`:
    ```groovy
    buildscript {
        dependencies {
            classpath("io.koraframework:openapi-generator:2.0.0.RC1")
        }
    }
    ```

    Plugin dependency in `build.gradle.kts`:
    ```groovy
    plugins {
        id("org.openapi.generator") version("7.24.0")
    }
    ```

    Other plugin versions are not guaranteed to work because the `OpenAPI Generator` API can be incompatible at code level.

The `io.koraframework:openapi-generator` artifact is added to the **buildscript** classpath, so it is loaded by the `Gradle` JVM itself rather than by the compiled application.
Kora is compiled for `JDK 25`, therefore the `Gradle` daemon must also run on `JDK 25` or newer, otherwise generation fails with `UnsupportedClassVersionError` before any project code is compiled.
Setting only the project `toolchain` is not enough — the toolchain applies to compilation, not to the `Gradle` JVM.

Generated code also requires the [HTTP server](http-server.md) or [HTTP client](http-client.md) module, depending on the selected generation mode,
plus the [JSON](json.md) module, and the [validation](validation.md) module when server validation is enabled.

## Configuration { #configuration }

Configure the [OpenAPI Generator plugin](https://openapi-generator.tech/docs/plugins#gradle) parameters:

- `Gradle` plugin parameters are described in the [plugin documentation](https://github.com/OpenAPITools/openapi-generator/blob/v7.24.0/modules/openapi-generator-gradle-plugin/README.adoc).
- The `configOptions` plugin parameter is described in the [configuration documentation](https://openapi-generator.tech/docs/configuration/).
- The `openapiNormalizer` plugin parameter is described in the [customization documentation](https://openapi-generator.tech/docs/customization/#normalizer-opts).

The Kora generator is selected with `generatorName = "kora"` and the target artifact is selected with `configOptions.mode`.
Kora supports exactly four modes:

| Mode            | Generates                                                                          |
|-----------------|------------------------------------------------------------------------------------|
| `java-client`   | `Java` declarative [HTTP client](http-client.md) interfaces, models and mappers      |
| `java-server`   | `Java` [HTTP server](http-server.md) controllers, `delegate` contracts and mappers   |
| `kotlin-client` | `Kotlin` declarative [HTTP client](http-client.md) interfaces, models and mappers    |
| `kotlin-server` | `Kotlin` [HTTP server](http-server.md) controllers, `delegate` contracts and mappers |

Generated code is synchronous: client methods return the response value, and `delegate` methods return the response value.
An unknown `mode` value fails generation with a message listing the supported modes.

### Common `OpenAPI Generator` Options { #common-opts }

In addition to Kora-specific `configOptions`, `GenerateTask` accepts common `OpenAPI Generator` parameters.
They define where to read the contract from, where to put generated files, which packages to use, and how to preprocess the `OpenAPI` description.
For Kora projects, these parameters are usually set explicitly because generated code is then added to normal project compilation.

| Parameter           | Description                                                                                                                                                                                                                                                 |
|---------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `generatorName`     | Generator name (`required`, no default). Always set it to `kora` for Kora.                                                                                                                                                                                  |
| `inputSpec`         | Path to the `OpenAPI` file (`required`, no default). Usually this is a file under `src/main/resources/openapi`, for example `$projectDir/src/main/resources/openapi/openapi.yaml`.                                                                          |
| `outputDir`         | Directory for generated files (not specified by default, optional). In Kora projects, this is usually a directory under `build`, for example `$buildDir/generated/openapi`, and it is added to the main source set.                                         |
| `apiPackage`        | Package for generated API interfaces, controllers, `delegate` classes, and mappers (default: `org.openapitools.api`). It is recommended to set it explicitly, for example `io.koraframework.example.openapi.api`.                                           |
| `modelPackage`      | Package for models generated from `OpenAPI` schemas (default: `org.openapitools.model`). It is recommended to set it explicitly, for example `io.koraframework.example.openapi.model`.                                                                      |
| `invokerPackage`    | Auxiliary generator package (default: `org.openapitools.api`). It is recommended to set it explicitly next to `apiPackage` and `modelPackage`, for example `io.koraframework.example.openapi.invoker`.                                                      |
| `configOptions`     | Generator-specific parameters (default: `{}`). For Kora, this is where `mode`, `clientConfigPrefix`, `enableServerValidation`, `extensions`, and the other parameters described below are set.                                                              |
| `globalProperties`  | Limits which entities are generated (default: `{}`). Useful when you need to generate only `apis`, only `models`, or specific models and operations. Use carefully: normal Kora clients and servers usually need API classes, models, and mappers together. |
| `openapiNormalizer` | Preprocesses the `OpenAPI` contract before generation (default: `{}`). Often used to disable standard transformations with `DISABLE_ALL`, generate only selected operations with `FILTER`, or control rules such as `SIMPLIFY_ONEOF_ANYOF`.                 |
| `importMappings`    | Maps a schema name to an existing class (default: `{}`). Useful when a model is written manually or comes from another module, for example `Money: "com.example.Money"`.                                                                                    |
| `typeMappings`      | Maps an `OpenAPI Generator` type to a language type (default: `{}`). Used for targeted type replacement, for example replacing `OffsetDateTime` with a project-specific time type.                                                                          |
| `schemaMappings`    | Maps an `OpenAPI` schema to an external type without generating the model (default: `{}`). Similar to `importMappings`, but configured at schema level and useful for reusing shared DTOs.                                                                  |
| `skipValidateSpec`  | Skips `OpenAPI` contract validation before generation (default: `false`). In normal builds it is better to keep validation enabled; use `true` only temporarily for external contracts that cannot be fixed quickly.                                        |
| `cleanupOutput`     | Cleans `outputDir` before generation (default: `false`). Useful when the contract changes often and files from removed operations or models must disappear. Do not point `outputDir` to a directory with handwritten code.                                  |

Example with common options:

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

### Useful `openapiNormalizer` Rules { #normalizer-opts }

`openapiNormalizer` changes the input `OpenAPI` contract before generation. It is not a Kora parameter, but a general `OpenAPI Generator` mechanism.
For Kora, it is especially useful when one large contract is used by several applications or when the contract contains ambiguous shapes for code generation.

| Rule                                    | Description                                                                                                                                                                                                                                                                                 |
|-----------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `DISABLE_ALL`                           | Disables standard normalization rules (default: `false`). Starting with `OpenAPI Generator 7`, some rules are enabled by default, so predictable generation often starts with `DISABLE_ALL: "true"` and then enables only the needed rules explicitly.                                      |
| `FILTER`                                | Keeps only selected operations for generation (not specified by default, optional). Supports one filter at a time: `operationId:name1\|name2`, `method:get\|post`, or `tag:public\|billing`. Operations that do not match are marked as `x-internal: true` and are not generated.           |
| `KEEP_ONLY_FIRST_TAG_IN_OPERATION`      | Keeps only the first tag on an operation (default: `false`). Useful when operations have several tags and are split into several API classes differently from what you expect.                                                                                                              |
| `SET_TAGS_FOR_ALL_OPERATIONS`           | Replaces tags on all operations with one provided value (not specified by default, optional). Useful when you want to force one generated API class.                                                                                                                                        |
| `SET_TAGS_TO_OPERATIONID`               | Sets an operation tag to `operationId`, or to `default` when `operationId` is empty (default: `false`). Useful for contracts without usable tags when predictable operation grouping is needed.                                                                                             |
| `SET_TAGS_TO_VENDOR_EXTENSION`          | Reads operation tags from the specified extension, for example `x-tags` (not specified by default, optional). Useful when an external contract cannot be changed but already has custom operation grouping.                                                                                 |
| `FIX_DUPLICATED_OPERATIONID`            | Adds a numeric suffix to duplicated `operationId` values (default: `false`). It is better to fix the contract, but this rule helps generate code for an external description temporarily.                                                                                                   |
| `SET_BEARER_AUTH_FOR_NAME`              | Converts the specified security scheme to `bearerAuth` (not specified by default, optional). Useful for external contracts where a bearer token is described in a non-standard way but should be handled as a normal bearer scheme in the application.                                      |
| `REF_AS_PARENT_IN_ALLOF`                | Marks a `$ref` inside `allOf` as a parent schema with `x-parent: true` (default: `false`). Can help contracts that model inheritance through `allOf`.                                                                                                                                       |
| `SIMPLIFY_ONEOF_ANYOF`                  | Simplifies some `oneOf`/`anyOf` constructs, for example by moving a `null` variant to `nullable: true` and removing single wrappers (enabled by default in `OpenAPI Generator 7` unless `DISABLE_ALL` is set). For Kora, this can change generated model shapes, so enable it deliberately. |
| `SIMPLIFY_ANYOF_STRING_AND_ENUM_STRING` | Simplifies `anyOf` made from `string` and a string enum to `string` (default: `false`). This can help with contracts where the enum restriction is not important for code.                                                                                                                  |
| `SIMPLIFY_BOOLEAN_ENUM`                 | Converts a boolean enum to a plain `boolean` (enabled by default in `OpenAPI Generator 7` unless `DISABLE_ALL` is set).                                                                                                                                                                     |
| `REFACTOR_ALLOF_WITH_PROPERTIES_ONLY`   | Moves properties from a schema that has both `allOf` and `properties` into a separate schema inside `allOf` (enabled by default in `OpenAPI Generator 7` unless `DISABLE_ALL` is set). This can help inheritance, but strict contracts should be checked after generation.                  |
| `NORMALIZE_31SPEC`                      | Normalizes some `OpenAPI 3.1` constructs into a form better understood by the generator (default: `false`). Useful for `3.1` contracts when generation fails on newer schema forms.                                                                                                         |
| `REMOVE_X_INTERNAL`                     | Removes `x-internal: true` from operations and models (default: `false`). Use only when the contract already contains `x-internal`, but a specific generation task must force such operations back in.                                                                                      |
| `SET_CONTAINER_TO_NULLABLE`             | Marks container types `array`, `set`, or `map` as `nullable` (not specified by default, optional). Use only when an external contract systematically misses `nullable` on such fields.                                                                                                      |
| `SET_PRIMITIVE_TYPES_TO_NULLABLE`       | Marks primitive types `string`, `integer`, `number`, or `boolean` as `nullable` (not specified by default, optional). This significantly changes model signatures, so apply it only to problematic external contracts.                                                                      |

Example of generating only the public part of a contract:

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

### Model and Body Options { #model-opts }

These `configOptions` shape the generated models and the handling of untyped request and response bodies.
They do not depend on whether a client or a server is generated.

| Parameter          | Description                                                                                                                                                                                                                                                                                     |
|--------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `rawBodyMode`      | Type used for a request or response body described as a bare `type: object` without properties (default: `BYTES`). `BYTES` generates `byte[]` / `ByteArray`, `BODY` generates streaming `HttpBodyOutput` / `HttpBodyInput`, `OBJECT` generates `Object` / `Any` serialized as `JSON`.           |
| `filterWithModels` | Removes models that became unused after `openapiNormalizer.FILTER` (default: `false`). See [Model Filtering](#filter-with-models).                                                                                                                                                              |
| `extensions`       | `JSON` object with additional model, enum, method and type annotations and with interceptors (not specified by default, optional). See [Generator Extensions](#extensions).                                                                                                                     |

`JSON` mappers are always bound with `io.koraframework.json.common.annotation.Json` and are generated by the [JSON](json.md) annotation processor,
so no annotation-name option is needed.
A bare `type: object` used as a *model property* is always generated as `Object` / `Any` regardless of `rawBodyMode`, which only affects request and response bodies.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    configOptions = [
        mode: "java-client",
        clientConfigPrefix: "httpClient.billing",
        rawBodyMode: "BODY" //(1)!
    ]
    ```

    1. `POST /report` with `content: {application/octet-stream: {schema: {type: object}}}` becomes `report(HttpHeaders additionalHeaders, HttpBodyOutput body)`

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    configOptions = mapOf(
        "mode" to "kotlin-client",
        "clientConfigPrefix" to "httpClient.billing",
        "rawBodyMode" to "BODY" //(1)!
    )
    ```

    1. `POST /report` with `content: {application/octet-stream: {schema: {type: object}}}` becomes `report(additionalHeaders: HttpHeaders, body: HttpBodyOutput)`

When a bare-object body is generated as `BYTES` or `BODY`, the generator also adds an `@Header HttpHeaders` argument in front of the body,
so the caller can set `Content-Type` and any other transport headers that are no longer derivable from the contract.

### Generator Extensions { #extensions }

`extensions` is a single `JSON` option that attaches annotations and interceptors to generated code.
It has three sections, all optional:

- `*` — applied to every operation and to every generated model and enum type
- `tags` — keyed by the `OpenAPI` tag name, applied to the operations of that tag
- `operations` — keyed by `operationId`, applied to that single operation

Every section accepts the same fields:

| Field                            | Description                                                                                                                                                                                            |
|----------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `additionalMethodAnnotations`    | Annotations added above generated client methods and server controller methods. A string or an array of strings. Supports the `%{configPath}` placeholder.                                             |
| `additionalTypeAnnotations`      | Annotations added to generated model types and enum types. Only the `*` section is used for type annotations.                                                                                          |
| `additionalModelTypeAnnotations` | Annotations added to generated model types only. Only the `*` section is used.                                                                                                                        |
| `additionalEnumTypeAnnotations`  | Annotations added to generated enum types only. Only the `*` section is used.                                                                                                                         |
| `interceptorType`                | Interceptor implementation class placed in `@InterceptWith`. When omitted but a tag is given, the base `HttpClientInterceptor` / `HttpServerInterceptor` type is used and the tag selects the instance. |
| `interceptorTag`                 | Interceptor tag class or array of tag classes for `@InterceptWith(tag = ...)`.                                                                                                                         |
| `clientMapping`                  | Object with a `type` field. Replaces the generated per-status response mappers of a client method with `@Mapping(type)`. Client mode only.                                                             |

An annotation value is written exactly as it appears in source, with a fully qualified type: `@io.koraframework.resilient.retry.annotation.Retryable(MyRetry.class)`.
The leading `@` is optional.

`%{configPath}` is replaced by the configuration path of the generated component:

- for a client, the `@HttpClient` config path of that API (see [Generated Client Usage](#client-usage))
- for a server, `serverConfigPrefix` with `%{ControllerTypeNameInCamelCase}` replaced by the controller class name with a lower-case first letter
  (default `serverConfigPrefix` is `httpServer.controller.%{ControllerTypeNameInCamelCase}`, so `PetApiController` gives `httpServer.controller.petApiController`)

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

Generated server controllers are `final` unless `enableServerValidation` is enabled or `additionalMethodAnnotations` are configured;
adding a method annotation that relies on [aspects](general.md#terminology) automatically makes the controller non-`final` so the aspect can be woven.

Invalid `JSON` in `extensions` (or in `tags`) fails generation with a message showing the expected shape and the provided value.

### Multiple Generation Tasks { #multiple-gens }

Several `GenerateTask` tasks can be registered in one module, for example to generate two independent contracts,
or to generate a client for one contract and a server for another. Each task writes into the same `outputDir` and is added to the same source set,
so the only requirement is that generated packages do not collide. Give every task its own `apiPackage`/`modelPackage`/`invokerPackage`.

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

    1. Isolated package for the first contract
    2. Different package for the second contract, so class names cannot clash

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

    1. Isolated package for the first contract
    2. Different package for the second contract, so class names cannot clash
    3. Both `KSP` and `Kotlin` compilation must run after generation

## Client { #client }

A minimal plugin configuration for creating a declarative HTTP client:

===! ":fontawesome-brands-java: `Java`"

    For clients, `configOptions.mode` is `java-client`.
    Other client parameters are described below in the authorization, interceptors, tags, models, and implicit headers sections.

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

    For clients, `configOptions.mode` is `kotlin-client`.
    Other client parameters are described below in the authorization, interceptors, tags, models, and implicit headers sections.

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

Client generation always needs a configuration path, so exactly one of these two options is required:

| Parameter            | Description                                                                                                                                                                        |
|----------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `clientConfig`       | Complete configuration path used verbatim for every generated client of the task (not specified by default, optional). Use it when the contract produces a single API interface.    |
| `clientConfigPrefix` | Prefix to which the generated interface name with a lower-case first letter is appended (not specified by default, optional). Use it when the contract produces several API classes. |

If neither is set for a client mode, generation fails with a message suggesting a `clientConfig` value derived from the contract file name.

### Generated Client Usage { #client-usage }

For every API tag, the generator produces an interface annotated with [`@HttpClient`](http-client.md), named after the tag (for example `PetApi`).
It is injected into components like any other Kora client, without extra registration:

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

    1. The generated `@HttpClient` interface, injected directly

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class RootService(
        private val petApi: PetApi, //(1)!
    )
    ```

    1. The generated `@HttpClient` interface, injected directly

With `clientConfigPrefix`, the configuration path is the prefix followed by the generated interface name **with a lower-case first letter**.
For `clientConfigPrefix = "httpClient.petV2"` and interface `PetApi`, the configuration block is `httpClient.petV2.petApi`.
With `clientConfig`, the value is used exactly as written and the interface name is not appended.
After a successful run the generator logs every generated client together with its configuration path, which is the quickest way to check the exact key.

The full set of client options (`url`, `requestTimeout`, per-operation blocks, `telemetry`) is described in the [HTTP client](http-client.md#configuration) documentation:

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

    1. Base URL of the target service
    2. Default request timeout for all operations
    3. Per-operation override block, named after the `operationId` (here `getValues`)

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

    1. Base URL of the target service
    2. Default request timeout for all operations
    3. Per-operation override block, named after the `operationId` (here `getValues`)

Every client method returns the `*ApiResponses` envelope of that operation, so the outcome is matched on the response subtype:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var response = petApi.getPetById(1L);
    if (response instanceof PetApiResponses.GetPetByIdApiResponse.GetPetById200ApiResponse r) {
        return r.content(); //(1)!
    }
    return null;
    ```

    1. `content()` is the deserialized response body of status `200`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val response = petApi.getPetById(1L)
    return if (response is PetApiResponses.GetPetByIdApiResponse.GetPetById200ApiResponse) {
        response.content //(1)!
    } else {
        null
    }
    ```

    1. `content` is the deserialized response body of status `200`

### Optional Arguments { #client-optional-args }

When an operation has optional query, header or cookie parameters, listing them all on every call is noisy.
Besides the full method, the generator produces a mutable holder class named `<Api><OperationId>OptArgs` and two extra `default` overloads:
one that takes only the required parameters, and one that takes the required parameters plus the holder.

===! ":fontawesome-brands-java: `Java`"

    ```java
    var onlyRequired = petsApi.listPets(); //(1)!

    var withOptional = petsApi.listPets(PetsApiListPetsOptArgs.defaults() //(2)!
        .withLimit(50)); //(3)!
    ```

    1. Every optional parameter is passed as `null`
    2. `defaults()` starts from the contract defaults, `empty()` starts from all `null`
    3. `with...` mutates the holder and returns it, so calls can be chained

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val onlyRequired = petsApi.listPets() //(1)!

    val withOptional = petsApi.listPets(PetsApiListPetsOptArgs.defaults() //(2)!
        .withLimit(50)) //(3)!
    ```

    1. Every optional parameter is passed as `null`
    2. `defaults()` starts from the contract defaults, `empty()` starts from all `null`
    3. `with...` mutates the holder and returns it, so calls can be chained

### Client Authorization { #client-authorization }

If the `OpenAPI` contract describes `securitySchemes`, the generator creates an `ApiSecurity` module in `apiPackage` with:

- one marker class per security scheme, named after the scheme in `components.securitySchemes` with an upper-case first letter
  (`apiKeyAuth` becomes `ApiSecurity.ApiKeyAuth`, `bearerAuth` becomes `ApiSecurity.BearerAuth`)
- one marker class and one `@DefaultComponent` `HttpClientInterceptor` per distinct security requirement used by the operations
- a `SecurityConfig` record with `@DefaultComponent` configuration readers for the `apiKey` and `basic` schemes
- `@InterceptWith(value = HttpClientInterceptor.class, tag = ApiSecurity.<Requirement>.class)` on every secured client method

A security requirement that lists several schemes at once produces one combined marker joined with `And` (`ApiSecurity.Sec1AndSec2`),
and an operation that accepts several alternative requirements produces one marker joined with `_` (`ApiSecurity.BearerAuth_ApiKeyAuth`).
The generated interceptor tries the alternatives in order and uses the first one for which every scheme provided a non-`null` token;
if none did, the request is sent unauthorized and a warning is logged, unless the contract also allows anonymous access.

`securityConfigPrefix` sets the configuration prefix of the generated `SecurityConfig`.
When it is not set, the prefix falls back to `clientConfigPrefix + ".security"`, then to `clientConfig + ".security"`, and finally to `security`.

| Parameter                     | Description                                                                                                                                                                        |
|-------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `securityConfigPrefix`        | Configuration prefix for the generated `SecurityConfig` (not specified by default, optional). See the fallbacks above.                                                              |
| `authAsMethodArgument`        | Passes the credential as a client method argument instead of generating interceptors (default: `false`). The whole `ApiSecurity` module is then not generated.                       |
| `primaryAuth`                 | Name of the security scheme turned into a method argument when an operation declares several (not specified by default, optional). Only meaningful with `authAsMethodArgument`.      |
| `useSecurityDeclarationOrder` | Keeps the declaration order of schemes inside a security requirement (default: `false`). By default schemes are ordered alphabetically, so `{a, b}` and `{b, a}` share one interceptor. |

#### apiKey and basic { #client-authorization-config }

For `apiKey` and `basic` schemes, the generator produces `@DefaultComponent` config readers and token providers, so no beans are required — only configuration values.
An `apiKey` scheme reads a single string; a `basic` scheme reads a `username`/`password` object.
Both values are optional: when they are absent the scheme simply provides no token.

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

    1. `apiKey` scheme `apiKeyAuth`: value sent in the header, query parameter or cookie declared by the scheme
    2. `basic` scheme `basicAuth`: credentials wrapped by the generated `BasicAuthHttpClientTokenProvider`

=== ":simple-yaml: `YAML`"

    ```yaml
    openapiAuth:
      apiKeyAuth: "MyAuthApiKey" #(1)!
      basicAuth: #(2)!
        username: "user"
        password: "password"
    ```

    1. `apiKey` scheme `apiKeyAuth`: value sent in the header, query parameter or cookie declared by the scheme
    2. `basic` scheme `basicAuth`: credentials wrapped by the generated `BasicAuthHttpClientTokenProvider`

The path above corresponds to `securityConfigPrefix = "openapiAuth"`:

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

#### bearer and oauth { #client-authorization-token }

For `bearer`, `oauth2` and `openId` schemes the generator does not know where the token comes from, so it expects an
[`HttpClientTokenProvider`](http-client.md#token-provider) component tagged with the generated marker class for that scheme.
The returned value is sent as the whole `Authorization` header, so it must include the `Bearer ` prefix when the scheme requires it:

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

    1. Tag must match the generated marker class for the scheme
    2. Real implementations usually fetch or refresh the token here, and return `null` when no token is available

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

    1. Tag must match the generated marker class for the scheme
    2. Real implementations usually fetch or refresh the token here, and return `null` when no token is available

???+ warning "Every scheme needs a provider"

    The generated `ApiSecurity` module requires an `HttpClientTokenProvider` for **every** `bearer`, `oauth2` or `openId` scheme
    declared in `components.securitySchemes`, even for schemes the application never uses — otherwise the graph fails to build.
    Such an unused scheme must return `null`, because the interceptor applies the first requirement whose providers all returned a token
    and a stray non-`null` value would override the scheme you actually wanted.

#### Multiple schemes { #client-authorization-multiple }

When an operation declares several alternative security requirements, the generator builds one interceptor covering all of them
and applies the first requirement whose schemes all returned a token — no option is needed for this.

To pass the credentials explicitly per call instead of through an interceptor, enable `authAsMethodArgument`.
The authorization value then becomes a `@Nullable String` client method argument annotated with `@Header`, `@Query` or `@Cookie` according to the scheme,
and `ApiSecurity` is not generated at all. `primaryAuth` picks which scheme becomes that argument when an operation lists several:

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    configOptions = [
        mode: "java-client",
        clientConfigPrefix: "httpClient.petV3",
        authAsMethodArgument: "true", //(1)!
        primaryAuth: "apiKeyAuth" //(2)!
    ]
    ```

    1. Add the auth value as a method argument instead of generating interceptors
    2. Scheme turned into the argument when an operation lists several

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    configOptions = mapOf(
        "mode" to "kotlin-client",
        "clientConfigPrefix" to "httpClient.petV3",
        "authAsMethodArgument" to "true", //(1)!
        "primaryAuth" to "apiKeyAuth" //(2)!
    )
    ```

    1. Add the auth value as a method argument instead of generating interceptors
    2. Scheme turned into the argument when an operation lists several

If the selected scheme maps to the `Authorization` header but the operation already declares an explicit `Authorization` header parameter,
generation fails with a message asking to rename that parameter or to disable `authAsMethodArgument`.

### Additional Annotations { #additional-contract-annotations }

`extensions.additionalMethodAnnotations` adds annotations above generated client or server controller methods.
It is set globally under `*`, per contract tag under `tags`, or per `operationId` under `operations`, and the three levels are combined.

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

Model and enum annotations use `additionalModelTypeAnnotations`, `additionalEnumTypeAnnotations`, or `additionalTypeAnnotations` for both,
and are only read from the `*` section because a generated model is not bound to a single operation.

### Interceptors { #interceptors }

Generated client methods can be annotated with [interceptors](http-client.md#interceptors) through `extensions`.
`interceptorType` sets the implementation class and `interceptorTag` sets the tags. Both may be used together, or only one of them:

- only `interceptorType` — `@InterceptWith(MyInterceptor.class)`
- only `interceptorTag` — `@InterceptWith(value = HttpClientInterceptor.class, tag = MyTag.class)`, so the instance is picked from the graph by tag
- both — `@InterceptWith(value = MyInterceptor.class, tag = MyTag.class)`

`interceptorTag` accepts a single class name or an array of class names; an array produces one `@InterceptWith` per tag.

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

### Tags { #tags }

Generated clients annotated with `@HttpClient` can receive `httpClientTag` and `telemetryTag` parameters.
The value is a `JSON` object where the key is an API tag from the contract, or `*` for all of them, and the value is an object with `httpClientTag` and `telemetryTag` fields.

Set `configOptions.tags`:

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

## Implicit Headers { #implicit-headers }

By default, headers from an `OpenAPI` operation become generated method arguments.
If some headers are supplied by infrastructure rather than application code, they can be made implicit.

- `implicitHeaders = true` makes all headers from `OpenAPI` operations implicit.
- `implicitHeadersRegex` makes only headers whose names match the regular expression implicit.

An implicit header is removed from the method signature but remains in `OpenAPI` annotations in generated code
(`@io.swagger.v3.oas.annotations.Parameter(in = ParameterIn.HEADER)`).
This keeps the header in contract documentation without requiring application code to pass it manually.

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

## Models { #models }

The generator creates request and response models from `OpenAPI` schemas.
`Java` models are `record` types annotated with [`@Json`](json.md) writers and readers; `Kotlin` models are `data class` types.
Schemas with a discriminator produce a `sealed interface` with the mapped models as permitted subtypes.

`Java` records also get a `with<Field>` method per field that returns a new instance, or the same instance when the value did not change:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var updated = pet.withName("Rex"); //(1)!
    ```

    1. Returns `pet` itself if `name` is already `"Rex"`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val updated = pet.copy(name = "Rex") //(1)!
    ```

    1. `Kotlin` models are `data class` types, so the standard `copy` is used

???+ warning "Use named arguments in `Kotlin`"

    Generated `Kotlin` constructors list required properties first and give every optional property a default value.
    Adding a property to the contract can therefore shift positions, so construct models with named arguments:
    `Pet(id = 1L, name = "name", status = Pet.StatusEnum.AVAILABLE)`.

### Enums { #enums }

A schema `enum` becomes a generated enum whose constants keep the raw contract values in a nested `Constants` class.
Because contract values are frequently not valid identifiers (`Dingo-Don`, `5`), the enum is converted from its wire value with the static `fromValue` method,
and `getValue()` returns the wire value back. `Enum.valueOf` works on the generated constant name, not on the contract value, and must not be used for parsing:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var status = Pet.StatusEnum.fromValue("available"); //(1)!
    var wire = status.getValue(); //(2)!
    ```

    1. Throws `IllegalArgumentException` for a value that is not in the contract
    2. Returns `"available"`, the value declared in the contract

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val status = Pet.StatusEnum.fromValue("available") //(1)!
    val wire = status.value //(2)!
    ```

    1. Throws `IllegalArgumentException` for a value that is not in the contract
    2. Returns `"available"`, the value declared in the contract

For every generated enum the generator also emits a `@Module` with `@DefaultComponent` `JsonReader`, `JsonWriter` and HTTP parameter converters,
so enums work as request bodies, query parameters, path parameters and headers without any manual mapper.

### Optional Nullable Fields { #json-nullable }

A field that is both `nullable: true` and absent from the `required` list has three distinguishable states:
the field is absent from `JSON`, the field is present with `null`, and the field is present with a value.
Such a field is generated as [`JsonNullable`](json.md#jsonnullable-wrapper) so the three states remain distinguishable:

===! ":fontawesome-brands-java: `Java`"

    ```java
    if (request.comment().isDefined()) { //(1)!
        update(request.comment().value()); //(2)!
    }
    ```

    1. `false` when the field was absent from the request body
    2. May still be `null` when the field was explicitly sent as `null`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    if (request.comment.isDefined) { //(1)!
        update(request.comment.value()) //(2)!
    }
    ```

    1. `false` when the field was absent from the request body
    2. May still be `null` when the field was explicitly sent as `null`

The other combinations are simpler:

- `required` and not `nullable` — a plain non-null field
- not `required` and not `nullable` — a `@Nullable` field in `Java`, a `T?` field in `Kotlin`
- `required` and `nullable` — a `@Nullable` / `T?` field annotated with `@JsonInclude(ALWAYS)`, so `null` is always serialized

### Model Filtering { #filter-with-models }

`OpenAPI Generator` can filter operations through `openapiNormalizer.FILTER`.
If `filterWithModels` is additionally enabled, the Kora generator also excludes the models that became unused after operation filtering.
This is useful for large contracts where an application generates only part of the API.

## Responses { #responses }

For every operation the generator produces a `<Api>Responses` interface containing one response type per operation.
When an operation declares several responses, that type is a `sealed interface` with one `record` / `data class` per declared status code,
named `<OperationId><Code>ApiResponse`. A response with a body carries it as `content`; declared response headers become extra components.
When an operation declares exactly one response, `<OperationId>ApiResponse` is that record directly, without a sealed wrapper.

Status ranges (`1XX`, `2XX`, `3XX`, `4XX`, `5XX`) and the `default` response cannot be represented as a fixed `int`,
so their records carry a runtime `int statusCode` as the first component:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var response = petsApi.listPets();
    return switch (response) {
        case PetsApiResponses.ListPetsApiResponse.ListPets200ApiResponse r -> r.content();
        case PetsApiResponses.ListPetsApiResponse.ListPets4XXApiResponse r -> throw new IllegalStateException("Client error " + r.statusCode()); //(1)!
        case PetsApiResponses.ListPetsApiResponse.ListPets5XXApiResponse r -> throw new IllegalStateException("Server error " + r.statusCode());
    };
    ```

    1. The real status code, because `4XX` covers a whole range

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val response = petsApi.listPets()
    return when (response) {
        is PetsApiResponses.ListPetsApiResponse.ListPets200ApiResponse -> response.content
        is PetsApiResponses.ListPetsApiResponse.ListPets4XXApiResponse -> throw IllegalStateException("Client error " + response.statusCode) //(1)!
        is PetsApiResponses.ListPetsApiResponse.ListPets5XXApiResponse -> throw IllegalStateException("Server error " + response.statusCode)
    }
    ```

    1. The real status code, because `4XX` covers a whole range

On the client side exact codes are registered with `@ResponseCodeMapper(code = N)`, while ranges and `default` are funnelled through one
`@ResponseCodeMapper(code = ResponseCodeMapper.DEFAULT)` mapper that dispatches on the real status code.
If the contract declares no `default` response and the received status matches nothing, the client throws `HttpClientResponseException`.

For a client, when several responses of one operation share the same body type, the generator additionally emits a shared `sealed interface`
`<OperationId><Type>ApiResponse` exposing `content()` and `statusCode()`, so all error variants of one model can be handled in one branch.

## Server { #server }

A minimal plugin configuration for creating HTTP server handlers:

===! ":fontawesome-brands-java: `Java`"

    For servers, `configOptions.mode` is `java-server`.
    Other server parameters are described below in the validation, `delegate` classes, interceptors, models, and implicit headers sections.

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

    1. Path to the `OpenAPI` file used to create classes
    2. Directory where generated files are created
    3. Package for delegates, controllers, and mappers
    4. Package for models and DTOs
    5. Auxiliary generator package
    6. Plugin mode
    7. Register generated classes as project source code
    8. Make code compilation depend on HTTP server class generation: generate first, compile after

=== ":simple-kotlin: `Kotlin`"

    For servers, `configOptions.mode` is `kotlin-server`.
    Other server parameters are described below in the validation, `delegate` classes, interceptors, models, and implicit headers sections.

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

    1. Path to the `OpenAPI` file used to create classes
    2. Directory where generated files are created
    3. Package for delegates, controllers, and mappers
    4. Package for models and DTOs
    5. Auxiliary generator package
    6. Plugin mode
    7. Register generated classes as project source code
    8. Make code compilation depend on HTTP server class generation: generate first, compile after

For every API tag, the generator produces a `<Api>Controller` annotated with `@Component` and `@HttpController`, so handlers are registered automatically.
The controller only unpacks the request and delegates to the `<Api>Delegate` contract that the application implements.

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

When `enableServerValidation` is enabled, the generator marks models with `@Valid`, translates the schema constraints into Kora validation annotations,
and adds `@Validate` to controller methods with validated parameters.
`minimum`/`maximum` become `@Min`, `@Max` or `@Range(from, to, boundary)` depending on how many bounds the schema declares;
`minLength`/`maxLength` and `minItems`/`maxItems` become `@Size`; `pattern` becomes `@Pattern`.

`enableServerValidationInterceptor` controls adding `@InterceptWith(ValidationHttpServerInterceptor.class)`, which converts validation errors to HTTP responses.
It defaults to enabled whenever server validation is enabled.
Setting `enableServerValidationInterceptor = "false"` keeps the validation annotations but does not add the standard interceptor,
which is what you want when `ViolationException` is mapped by your own [response mapper](http-server.md#custom-response).

Both options are read only in server modes.

### Delegate Implementation { #delegate-method-body }

The server generator creates a controller and a `delegate` contract where the user implements application logic.
By default, `delegateMethodBodyMode = none`, so `delegate` contract methods are abstract and must be implemented by the application.

If `delegateMethodBodyMode = throwException` is set, methods become `default` and throw `UnsupportedOperationException("Not yet implemented")`,
and the generator additionally creates a `<Api>Module` module with a default `delegate` implementation.
This mode is useful when the application must be built before all operations are implemented, or when custom implementations are connected gradually.

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

Add the generated `<Api>Module` to the application graph so the default implementation is available:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends UndertowPublicHttpServerModule, JsonModule, PetApiModule { //(1)!

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

    1. Remove the generated module once the application supplies its own `@Component PetApiDelegate`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : UndertowPublicHttpServerModule, JsonModule, PetApiModule //(1)!

    fun main() {
        KoraApplication.run { ApplicationGraph.graph() }
    }
    ```

    1. Remove the generated module once the application supplies its own `@Component PetApiDelegate`

#### Delegate Response Types { #delegate-response-types }

Each generated `delegate` method returns the sealed `<Api>Responses` envelope of the operation, described in [Responses](#responses).
For an operation `getPetById` with responses `200` and `404`, the generator produces `PetApiResponses.GetPetByIdApiResponse` with subtypes
`GetPetById200ApiResponse` (carrying the body) and `GetPetById404ApiResponse`. The implementation returns the subtype matching the outcome:

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

    1. Status `404` subtype, no body
    2. Status `200` subtype carrying the response body

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

    1. Status `404` subtype, no body
    2. Status `200` subtype carrying the response body

`Java` `delegate` methods declare `throws Exception`, so an implementation may propagate checked exceptions
and let an [interceptor](http-server.md#interceptors) or an exception [response mapper](http-server.md#custom-response) turn them into a response.

#### Raw Request in Delegate { #request-in-delegate }

By default, a `delegate` method receives only the parameters declared in the contract. If an implementation needs access to the raw request
(for example to read an infrastructure header or the remote address), enable `requestInDelegateParams`. The generator then adds an
`HttpServerRequest` as the first parameter of every `delegate` method. This is a server-only option.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    configOptions = [
        mode: "java-server",
        requestInDelegateParams: "true" //(1)!
    ]
    ```

    1. Adds `HttpServerRequest _serverRequest` as the first argument of each delegate method

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    configOptions = mapOf(
        "mode" to "kotlin-server",
        "requestInDelegateParams" to "true" //(1)!
    )
    ```

    1. Adds `HttpServerRequest _serverRequest` as the first argument of each delegate method

#### Controller Path Prefix { #prefix-path }

`prefixPath` prepends a base path to every generated HTTP server controller route. It is useful when all operations should be served under a common
segment (for example `/api/v1`) that is not part of the `OpenAPI` paths.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    configOptions = [
        mode: "java-server",
        prefixPath: "/api/v1" //(1)!
    ]
    ```

    1. A contract path `/pet/{id}` becomes `/api/v1/pet/{id}`

=== ":simple-kotlin: `Kotlin`"

    ```groovy
    configOptions = mapOf(
        "mode" to "kotlin-server",
        "prefixPath" to "/api/v1" //(1)!
    )
    ```

    1. A contract path `/pet/{id}` becomes `/api/v1/pet/{id}`

### Interceptors { #interceptors-2 }

Generated controllers annotated with `@HttpController` can also be annotated with [interceptors](http-server.md#interceptors) through `extensions`,
using exactly the same fields as [client interceptors](#interceptors).
When only `interceptorTag` is given, the base type is `HttpServerInterceptor` and the instance is resolved from the graph by tag:

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

An interceptor referenced by `interceptorType` must be a component of the graph, so declare it with `@Component` or as a module method.

### Authorization { #authorization }

When the `OpenAPI` contract describes `securitySchemes`, the server generator creates an `ApiSecurity` module with one marker class per scheme,
named after the scheme name in `components.securitySchemes` with an upper-case first letter — for the usual
[Basic/ApiKey/Bearer/OAuth](https://swagger.io/docs/specification/authentication/) contract these are
`ApiSecurity.BasicAuth`, `ApiSecurity.ApiKeyAuth`, `ApiSecurity.BearerAuth` and `ApiSecurity.OAuth`.

For each scheme, the application must provide an `HttpServerPrincipalExtractor<T, P>` component tagged with the matching marker class.
`T` is the extracted credential and `P` is the resulting principal.
The extractor receives the request and the credential value, and returns the authenticated principal or `null` when the credential is not accepted:

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

    1. Returning `null` rejects this security requirement, and the generated interceptor tries the next one
    2. `OAuth` schemes declare scopes, so the extractor returns a `PrincipalWithScopes`

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

    1. Returning `null` rejects this security requirement, and the generated interceptor tries the next one
    2. `OAuth` schemes declare scopes, so the extractor returns a `PrincipalWithScopes`

For `OAuth`, the returned principal must implement `PrincipalWithScopes` so the generated interceptor can enforce the scopes declared on each operation.
The authenticated principal is published for the whole request through `Principal.current()`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record UserPrincipal(String name) implements PrincipalWithScopes {

        @Override
        public Collection<String> scopes() {
            return List.of("read", "write"); //(1)!
        }
    }
    ```

    1. Scopes granted to this principal, matched against the operation's required scopes

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class UserPrincipal(val name: String) : PrincipalWithScopes {

        override fun scopes(): Collection<String> {
            return listOf("read", "write") //(1)!
        }
    }
    ```

    1. Scopes granted to this principal, matched against the operation's required scopes

An operation that requires several schemes at once gets one extractor whose credential type is a generated `<Tag>AuthData` record
holding one `String` per scheme, and whose tag joins the scheme names with `With` — for schemes `headerAuth1` and `queryAuth` this is
`@Tag(ApiSecurity.HeaderAuth1WithQueryAuth.class)` and `ApiSecurity.HeaderAuth1WithQueryAuthAuthData`.

When no security requirement of an operation is satisfied, the generated interceptor throws `HttpServerResponseException.of(401, "Unauthorized")`.
If the contract lists an empty requirement (`security: [{}]`) as one of the alternatives, the request is passed through unauthenticated instead.

Server security supports `apiKey` schemes in a header, a query parameter or a cookie, and `http` `basic`/`bearer` plus `oauth2`/`openId`
schemes read from the `Authorization` header. Any other scheme type fails generation with an explicit message.

## Recommendations { #recommendations }

???+ tip "Advice"

    If something is not generated by the plugin, or behavior differs from expectations or from other versions,
    carefully check the [plugin configuration](#configuration) and study the settings,
    because they can affect how classes are generated.

    Starting with plugin version `7.0.0`, the `SIMPLIFY_ONEOF_ANYOF` rule enabled by default in `openapiNormalizer`
    can lead to some non-obvious generator results, so contracts with `oneOf`/`anyOf` are usually generated with `DISABLE_ALL: "true"`.

    If a generated client cannot find its configuration, check the log line the generator prints after a successful run:
    it lists every generated client together with the exact configuration path it expects.

    The generator runs on the `Gradle` JVM, so a `UnsupportedClassVersionError` during the generation task means the `Gradle` daemon
    runs on an older `JDK` than the one Kora is compiled for — see [Dependency](#dependency).
