---
description: "Explains Kora OpenAPI management module for serving generated OpenAPI specifications through the management HTTP server. Use when working with OpenApiManagementModule, OpenAPI, management endpoint, private HTTP server."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora OpenAPI management module for serving generated OpenAPI specifications through the management HTTP server; key triggers include OpenApiManagementModule, OpenAPI, management endpoint, private HTTP server."
---

The `openapi-management` module serves ready-made `OpenAPI` files from an application, along with [Swagger UI](https://swagger.io/tools/swagger-ui/) and [RapiDoc](https://rapidocweb.com/) pages for viewing them.
`OpenAPI` is a machine-readable HTTP API contract: it helps inspect available operations, data models, and request parameters.

The module does not create a contract from code; it only publishes existing files from application resources.
This is useful for local development, test environments, and operational access to API documentation without a separate documentation server.

For a step-by-step walkthrough before the reference details, see [OpenAPI HTTP Server](../guides/openapi-http-server.md).

## Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:openapi-management"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends OpenApiManagementModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:openapi-management")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : OpenApiManagementModule
    ```

Requires the [HTTP server](http-server.md) module because it registers its own `GET` handlers for serving files and viewer pages.

## Configuration { #configuration }

An example of the configuration described by the `OpenApiManagementConfig` class:

===! ":material-code-json: `Hocon`"

    ```javascript
    openapi {
        management {
            file = [ "my-openapi-1.yaml", "my-openapi-2.yaml" ] //(1)!
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

    1. Path to an `OpenAPI` file or a list of paths relative to application resources (required, default: not specified).
    2. Enables serving `OpenAPI` files through the HTTP handler (default: `false`).
    3. Path where `OpenAPI` files are available (default: `/openapi`).
        If one file is specified, it is available exactly at this path.
        If multiple files are specified, the path becomes a prefix of the `/openapi/{file}` form.
        The `{file}` value is taken from the file name without directories and without the `.json`, `.yml`, or `.yaml` extension: `someDirectory/my-openapi-1.yaml` will be available at `/openapi/my-openapi-1`.
    4. Enables the `Swagger UI` page (default: `false`).
    5. Path where the `Swagger UI` page is available (default: `/swagger-ui`).
    6. Enables the `RapiDoc` page (default: `false`).
    7. Path where the `RapiDoc` page is available (default: `/rapidoc`).

=== ":simple-yaml: `YAML`"

    ```yaml
    openapi:
      management:
        file: [ "my-openapi-1.yaml", "my-openapi-2.yaml" ] #(1)!
        enabled: false  #(2)!
        endpoint: "/openapi" #(3)!
        swaggerui:
          enabled: false #(4)!
          endpoint: "/swagger-ui" #(5)!
        rapidoc:
          enabled: false #(6)!
          endpoint: "/rapidoc" #(7)!
    ```

    1. Path to an `OpenAPI` file or a list of paths relative to application resources (required, default: not specified).
    2. Enables serving `OpenAPI` files through the HTTP handler (default: `false`).
    3. Path where `OpenAPI` files are available (default: `/openapi`).
        If one file is specified, it is available exactly at this path.
        If multiple files are specified, the path becomes a prefix of the `/openapi/{file}` form.
        The `{file}` value is taken from the file name without directories and without the `.json`, `.yml`, or `.yaml` extension: `someDirectory/my-openapi-1.yaml` will be available at `/openapi/my-openapi-1`.
    4. Enables the `Swagger UI` page (default: `false`).
    5. Path where the `Swagger UI` page is available (default: `/swagger-ui`).
    6. Enables the `RapiDoc` page (default: `false`).
    7. Path where the `RapiDoc` page is available (default: `/rapidoc`).

Files are read from application resources on the first request and then cached in memory.
Files with the `.json` extension use the `text/json; charset=utf-8` response type; all other files use `text/x-yaml; charset=utf-8`.

With multiple files, `Swagger UI` shows the list of available contracts.
`RapiDoc` opens the first file from the list.
When `Swagger UI` is enabled, an additional path for the `OAuth` redirect is registered.

## Recommendations { #recommendations }

???+ warning "Recommendation"

    We recommend creating the [contract first and then generating code from it](openapi-codegen.md).
    In this case, the module publishes the same contract file that is used for generation.

    If code is written first and the contract should be created from it, you can use the [Swagger Gradle Plugin](https://github.com/swagger-api/swagger-core/blob/master/modules/swagger-gradle-plugin/README.md)
    together with [Swagger annotations](https://github.com/swagger-api/swagger-core/wiki/Swagger-2.X---Annotations).
