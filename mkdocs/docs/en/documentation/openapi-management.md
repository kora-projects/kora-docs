A module to provide an OpenAPI file from an application,
as well as [Swagger UI](https://swagger.io/tools/swagger-ui/) and [Rapidoc](https://rapidocweb.com/) for displaying OpenAPI.

## Dependency

=== ":fontawesome-brands-java: `Java`"

    Dependency `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:openapi-management"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends OpenApiManagementModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Dependency `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:openapi-management")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : OpenApiManagementModule
    ```

Requires [HTTP server](http-server.md) module.

## Configuration

An example of the configuration described in the `OpenApiManagementConfig` class:

===! ":material-code-json: `Hocon`"

    ```javascript
    openapi {
        management {
            file = "my-openapi.yaml" //(1)!
            enabled = false  //(2)!
            endpoint = "/openapi" //(3)!
            swaggerui {
                enabled = false //(4)!
                endpoint = "/swagger-ui" //(5)!
            }
            rapidoc {
                enabled = false //(6)!
                endpoint = "/rapidoc" //(7)!
            }
        }
    }
    ```

    1. Relative path to the OpenAPI file in the `resources` directory
    2. The on/off switch of the controller that gives the OpenAPI
    3. The path where the OpenAPI will be accessed
    4. On/Off of the controller that gives SwaggerUI
    5. The path where the SwaggerUI will be accessed
    6. On/Off of the controller that gives Rapidoc
    7. Path where Rapidoc will be available

=== ":simple-yaml: `YAML`"

    ```yaml
    openapi:
      management:
        file: "my-openapi.yaml" #(1)!
        enabled: false  #(2)!
        endpoint: "/openapi" #(3)!
        swaggerui:
          enabled: false #(4)!
          endpoint: "/swagger-ui" #(5)!
        rapidoc:
          enabled: false #(6)!
          endpoint: "/rapidoc" #(7)!
    ```

    1. Relative path to the OpenAPI file in the `resources` directory
    2. The on/off switch of the controller that gives the OpenAPI
    3. The path where the OpenAPI will be accessed
    4. On/Off of the controller that gives SwaggerUI
    5. The path where the SwaggerUI will be accessed
    6. On/Off of the controller that gives Rapidoc
    7. Path where Rapidoc will be available

## Recommendations

???+ warning "Tip"

    We recommend using [contract first approach](openapi-codegen.md) and generate code using this contract, 
    in this approach same contract file is displayed.

    In the case where the code is first and the contract file is supposed to be created from it, you can use the [Swagger Gradle Plugin](https://github.com/swagger-api/swagger-core/blob/master/modules/swagger-gradle-plugin/README.md).
    together with [Swagger annotation set](https://github.com/swagger-api/swagger-core/wiki/Swagger-2.X---Annotations), which will be used to create the contract file.
