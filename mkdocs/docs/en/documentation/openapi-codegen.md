Module for creating declarative HTTP handlers [HTTP server](http-server.md)
or create declarative [HTTP clients](http-client.md) from OpenAPI contracts using [OpenAPI Generator plugin](https://openapi-generator.tech/docs/plugins/).

## Dependency

=== ":fontawesome-brands-java: `Java`"

    Dependency `build.gradle`:
    ```groovy
    buildscript {
        dependencies {
            classpath("ru.tinkoff.kora:openapi-generator:1.0.4")
        }
    }
    ```

    Plugin dependency `build.gradle`:
    ```groovy
    plugins {
        id "org.openapi.generator" version "7.1.0"
    }
    ```

    ??? abstract "Maven"

        For maven, you need to add a dependency with a generator for the plugin and configure it the same way:
        ```xml
        <plugin>
            <groupId>org.openapitools</groupId>
            <artifactId>openapi-generator-maven-plugin</artifactId>
            <version>7.1.0</version>
            <executions>
                <execution>
                    <goals>
                        <goal>generate</goal>
                    </goals>
                    <configuration>
                        <inputSpec>${project.basedir}/src/main/resources/petstoreV2.yaml</inputSpec>
                        <output>${project.basedir}/target/generated-sources/openapi/petstoreV2</output>
                        <generatorName>kora</generatorName>
                        <configOptions>
                            <mode>java-client</mode>
                            <sourceFolder>.</sourceFolder>
                        </configOptions>
                    </configuration>
                </execution>
            </executions>
            <dependencies>
                <dependency>
                    <groupId>ru.tinkoff.kora</groupId>
                    <artifactId>openapi-generator</artifactId>
                    <version>1.0.4</version>
                </dependency>
            </dependencies>
        </plugin>
        ```

        See more [here](https://github.com/OpenAPITools/openapi-generator/tree/master/modules/openapi-generator-maven-plugin).


=== ":simple-kotlin: `Kotlin`"

    Dependency `build.gradle.kts`:
    ```groovy
    buildscript {
        dependencies {
            classpath("ru.tinkoff.kora:openapi-generator:1.0.4")
        }
    }
    ```

    Plugin dependency `build.gradle.kts`:
    ```groovy
    plugins {
        id("org.openapi.generator") version("7.1.0")
    }
    ```

Requires connection of [HTTP server](http-server.md) or [HTTP client](http-client.md).

## Configuration

Configuration is required for [OpenAPI Generator plugin](https://openapi-generator.tech/docs/plugins/) parameters:

- Configuring Gradle plugin parameters in [documentation](https://github.com/OpenAPITools/openapi-generator/blob/v7.1.0/modules/openapi-generator-gradle-plugin/README.adoc).
- Configuring `configOptions` plugin parameter in [documentation](https://openapi-generator.tech/docs/generators/java/#config-options).
- Configuring `openapiNormalizer` plugin parameter in [documentation](https://openapi-generator.tech/docs/customization/#openapi-normalizer).

## Client

A minimal example of configuring a plugin to create a declarative HTTP client:

=== ":fontawesome-brands-java: `Java`"

    Kora's available plugin options:

    - `clientConfigPrefix` - configuration prefix of created HTTP clients
    - `tags` - possibility to put additional tags on created HTTP-clients
    - `primaryAuth` - specify which authorization mechanism to use as the primary one
    - `securityConfigPrefix` - security configuration prefix
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
    - `primaryAuth` - specify which authorization mechanism to use as the primary one
    - `securityConfigPrefix` - security configuration prefix
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

### Tags

It is possible to put parameters `httpClientTag` and `telemetryTag` on created clients with `@HttpClient` annotation.
The value is a Json object, the key of which is the api tag from the contract, and the value is the object with the fields `httpClientTag` and `telemetryTag`.

For this purpose it is necessary to set the `configOptions.tags` parameter:

=== ":fontawesome-brands-java: `Java`"

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

=== ":fontawesome-brands-java: `Java`"

    Available Kora plugin parameters:

    - `enableServerValidation` - whether to create validators according to the OpenAPI secification description for the server and whether to enable validation on HTTP handlers: `true, false`.
    - `requestInDelegateParams` - whether to expected `HttpServerRequest` as a method argument: `true, false`
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

=== ":fontawesome-brands-java: `Java`"

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
