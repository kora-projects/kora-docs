---
description: "Explains Kora OpenAPI management module for serving generated OpenAPI specifications, Swagger UI, and RapiDoc pages through the public HTTP server. Use when working with OpenApiManagementModule, OpenApiManagementConfig, OpenAPI endpoint, Swagger UI, RapiDoc."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora OpenAPI management module for serving generated OpenAPI specifications, Swagger UI, and RapiDoc pages through the public HTTP server; key triggers include OpenApiManagementModule, OpenApiManagementConfig, OpenAPI endpoint, Swagger UI, RapiDoc, /openapi, /swagger-ui, /rapidoc."
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
These are ordinary `HttpServerRequestHandler` beans collected by the **public** HTTP server, so `/openapi`, `/swagger-ui`, and `/rapidoc` are exposed on the public HTTP port, not on the private (management) port.

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

Files are read from application resources on the first request and then cached in memory (subsequent requests return the cached bytes).
Files with the `.json` extension use the `text/json; charset=utf-8` response type; all other files use `text/x-yaml; charset=utf-8`.

With multiple files, `Swagger UI` shows the list of available contracts, and `RapiDoc` opens the first file from the list.

When multiple files are configured, a request to `/openapi/{file}` with an unknown `{file}` name returns `404` (`OpenAPI file not registered`), and a request with an empty `{file}` value returns `400` (`OpenAPI file not specified`).
If a configured resource cannot be located or read at request time, the handler returns `404` or `500` respectively; otherwise it responds with `200` and the file content.

## Endpoints { #endpoints }

With serving enabled, the module registers the following `GET` routes on the public HTTP server (paths shown with default `endpoint` values):

| Route | Backing handler | Enabled by |
|-------|-----------------|------------|
| `GET /openapi` (single file) or `GET /openapi/{file}` (multiple files) | `OpenApiHttpServerHandler` | `enabled = true` |
| `GET /swagger-ui` | `SwaggerUIHttpServerHandler` | `swaggerui.enabled = true` |
| `GET /swagger-ui/oauth2-redirect` | `SwaggerOauthHttpServerHandler` | registered automatically together with `Swagger UI` |
| `GET /rapidoc` | `RapidocHttpServerHandler` | `rapidoc.enabled = true` |

Each route uses the `endpoint` value from its configuration section, so overriding an `endpoint` moves the corresponding route.
The `OAuth2` redirect path is always `swaggerui.endpoint` plus the `/oauth2-redirect` suffix.

## Recommendations { #recommendations }

???+ warning "Recommendation"

    We recommend creating the [contract first and then generating code from it](openapi-codegen.md).
    In this case, the module publishes the same contract file that is used for generation.

    If code is written first and the contract should be created from it, you can use the [Swagger Gradle Plugin](https://github.com/swagger-api/swagger-core/blob/master/modules/swagger-gradle-plugin/README.md)
    together with [Swagger annotations](https://github.com/swagger-api/swagger-core/wiki/Swagger-2.X---Annotations).
