---
description: "Explains the Kora OpenAPI management module that publishes OpenAPI contract files and the Swagger UI and Scalar viewer pages through the public HTTP server. Use when working with OpenApiManagementModule, OpenApiManagementConfig, openapi.management.files, CacheMode, Swagger UI, Scalar."
agent:
  use_when: "Use this file for Kora docs or implementation questions about the Kora OpenAPI management module that publishes OpenAPI contract files and the Swagger UI and Scalar viewer pages through the public HTTP server; key triggers include OpenApiManagementModule, OpenApiManagementConfig, OpenApiHttpServerHandler, SwaggerUIHttpServerHandler, ScalarHttpServerHandler, openapi.management.files, openapi.management.path, swaggerui, scalar, CacheMode, /openapi, /swagger-ui, /scalar."
---

The `openapi-management` module publishes ready-made `OpenAPI` files from an application, along with the [Swagger UI](https://swagger.io/tools/swagger-ui/) and [Scalar](https://scalar.com/) pages for viewing them.
`OpenAPI` is a machine-readable HTTP API contract: it helps inspect available operations, data models, and request parameters.

The module does not create a contract from code; it only publishes existing files from application resources.
This is useful for local development, test environments, and operational access to API documentation without a separate documentation server.

Both viewer pages ship inside the module as fully self-contained resources, so `Swagger UI` and `Scalar` render without internet access and without any `CDN`.

For a step-by-step walkthrough before the reference details, see [OpenAPI HTTP Server](../guides/openapi-http-server.md).

## Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:openapi-management"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends OpenApiManagementModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:openapi-management")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : OpenApiManagementModule
    ```

Requires the [HTTP server](http-server.md) module because it registers its own `GET` handlers for serving files and viewer pages.
These are ordinary `HttpServerRequestHandler` components declared without the system tag, so they are collected by the **public** HTTP server: `/openapi`, `/swagger-ui`, and `/scalar` are exposed on `httpServer.port`, not on the system port `httpServer.system.port`.

## Configuration { #configuration }

Configuration is read from the `openapi.management` section and is described by the `OpenApiManagementConfig` class:

===! ":material-code-json: `Hocon`"

    ```javascript
    openapi {
        management {
            enabled = true //(1)!
            files = [ "openapi/my-openapi-1.yaml", "openapi/my-openapi-2.yaml" ] //(2)!
            path = "/openapi" //(3)!
            cache = "GZIP" //(4)!
            swaggerui {
                enabled = true //(5)!
                path = "/swagger-ui" //(6)!
                withCredentials = true //(7)!
                cache = "GZIP" //(8)!
                options { //(9)!
                    layout = "StandaloneLayout"
                    validatorUrl = "null"
                    defaultModelsExpandDepth = "0"
                    deepLinking = "true"
                    persistAuthorization = "true"
                    displayOperationId = "true"
                    filter = "true"
                }
            }
            scalar {
                enabled = true //(10)!
                path = "/scalar" //(11)!
                cache = "GZIP" //(12)!
            }
        }
    }
    ```

    1.  Enables serving `OpenAPI` files through the HTTP handler (default: `false`).
    2.  List of paths to `OpenAPI` files relative to application resources (required, no default), see [Contract files](#files).
    3.  Path where `OpenAPI` files are available (default: `/openapi`).
        If one file is specified, it is available exactly at this path.
        If more than one file is specified, the path becomes a prefix of the `/openapi/{file}` form.
    4.  Response caching mode for `OpenAPI` files: `NONE`, `GZIP`, or `FULL` (default: `GZIP`), see [Caching](#cache).
    5.  Enables the `Swagger UI` page (default: `false`).
    6.  Path where the `Swagger UI` page is available (default: `/swagger-ui`).
    7.  Sends browser credentials (cookies, `Authorization` header) with requests issued from `Swagger UI` (default: `true`).
    8.  Response caching mode for the `Swagger UI` page: `NONE`, `GZIP`, or `FULL` (default: `GZIP`), see [Caching](#cache).
    9.  `Swagger UI` initialization options, see [Swagger UI options](#swagger-ui-options) (default: the seven values shown above).
    10. Enables the `Scalar` page (default: `false`).
    11. Path where the `Scalar` page is available (default: `/scalar`).
    12. Response caching mode for the `Scalar` page: `NONE`, `GZIP`, or `FULL` (default: `GZIP`), see [Caching](#cache).

=== ":simple-yaml: `YAML`"

    ```yaml
    openapi:
      management:
        enabled: true #(1)!
        files: [ "openapi/my-openapi-1.yaml", "openapi/my-openapi-2.yaml" ] #(2)!
        path: "/openapi" #(3)!
        cache: "GZIP" #(4)!
        swaggerui:
          enabled: true #(5)!
          path: "/swagger-ui" #(6)!
          withCredentials: true #(7)!
          cache: "GZIP" #(8)!
          options: #(9)!
            layout: "StandaloneLayout"
            validatorUrl: "null"
            defaultModelsExpandDepth: "0"
            deepLinking: "true"
            persistAuthorization: "true"
            displayOperationId: "true"
            filter: "true"
        scalar:
          enabled: true #(10)!
          path: "/scalar" #(11)!
          cache: "GZIP" #(12)!
    ```

    1.  Enables serving `OpenAPI` files through the HTTP handler (default: `false`).
    2.  List of paths to `OpenAPI` files relative to application resources (required, no default), see [Contract files](#files).
    3.  Path where `OpenAPI` files are available (default: `/openapi`).
        If one file is specified, it is available exactly at this path.
        If more than one file is specified, the path becomes a prefix of the `/openapi/{file}` form.
    4.  Response caching mode for `OpenAPI` files: `NONE`, `GZIP`, or `FULL` (default: `GZIP`), see [Caching](#cache).
    5.  Enables the `Swagger UI` page (default: `false`).
    6.  Path where the `Swagger UI` page is available (default: `/swagger-ui`).
    7.  Sends browser credentials (cookies, `Authorization` header) with requests issued from `Swagger UI` (default: `true`).
    8.  Response caching mode for the `Swagger UI` page: `NONE`, `GZIP`, or `FULL` (default: `GZIP`), see [Caching](#cache).
    9.  `Swagger UI` initialization options, see [Swagger UI options](#swagger-ui-options) (default: the seven values shown above).
    10. Enables the `Scalar` page (default: `false`).
    11. Path where the `Scalar` page is available (default: `/scalar`).
    12. Response caching mode for the `Scalar` page: `NONE`, `GZIP`, or `FULL` (default: `GZIP`), see [Caching](#cache).

`cache` values are matched against the enum constants exactly, so they must be written in upper case.

A minimal working configuration only needs `files` plus the flags of what should be exposed:

===! ":material-code-json: `Hocon`"

    ```javascript
    openapi {
        management {
            enabled = true
            files = "openapi/http-server.yaml"
            swaggerui.enabled = true
            scalar.enabled = true
        }
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    openapi:
      management:
        enabled: true
        files: "openapi/http-server.yaml"
        swaggerui:
          enabled: true
        scalar:
          enabled: true
    ```

### Contract files { #files }

`files` is the only required option of the section: it has no default, so an application that includes `OpenApiManagementModule` but leaves `openapi.management.files` unset fails at graph build with a `ConfigValueException` pointing at that path.
The check happens regardless of `enabled` — the configuration is mapped before any flag is inspected.

A list of paths is expected, but a plain string is also accepted and is split by `,`, so all three forms below are equivalent to a two-element list:

===! ":material-code-json: `Hocon`"

    ```javascript
    files = [ "openapi/user.yaml", "openapi/data.yaml" ]
    files = "openapi/user.yaml,openapi/data.yaml"
    files = "openapi/user.yaml, openapi/data.yaml"
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    files: [ "openapi/user.yaml", "openapi/data.yaml" ]
    files: "openapi/user.yaml,openapi/data.yaml"
    files: "openapi/user.yaml, openapi/data.yaml"
    ```

Each path is resolved as a classpath resource, first as written and then with a leading `/` prepended, so `openapi/user.yaml` and `/openapi/user.yaml` address the same resource.

When more than one file is configured, the public name of a file in the URL is derived from the file name: directories are stripped, and a trailing `.json`, `.yml`, or `.yaml` extension is removed.
So `someDirectory/my-openapi-1.yaml` is available at `/openapi/my-openapi-1`.

The response content type depends on the extension: files ending with `.json` are served as `text/json; charset=utf-8`, all other files as `text/x-yaml; charset=utf-8`.

Failure modes of the file route:

| Situation | Response |
|-----------|----------|
| More than one file configured, `{file}` is empty | `400`, `OpenAPI file not specified` |
| `{file}` does not match any configured file | `404`, `OpenAPI file not registered: <name>` |
| The configured resource is not found on the classpath | `404`, `OpenAPI file not found while reading: <path>` |
| The resource exists but cannot be read | `500`, `Can't read OpenAPI file: <path>` |

Because resources are read lazily on the first request, a typo in `files` does not break application startup — it surfaces as a `404` on the route.

### Caching { #cache }

Every served resource — each `OpenAPI` file, the `Swagger UI` page, and the `Scalar` page — has its own `cache` option that controls what is kept in memory after the first read:

| Mode | Request with `gzip` | Request without `gzip` |
|------|---------------------|------------------------|
| `NONE` | resource is read and compressed on every request | resource is read on every request |
| `GZIP` | resource is read and compressed once, then reused | resource is read on every request |
| `FULL` | resource is read and compressed once, then reused | resource is read once, then reused |

`GZIP` is the default and covers the normal case, where browsers and API clients announce `gzip` support.
`FULL` additionally caches the uncompressed form, and `NONE` disables caching entirely, which is convenient while a contract file is still being edited.

Compression is applied only when the request advertises it: `Accept-Encoding` must list `gzip` without a `q=0` quality value.
A compressed response carries `Content-Encoding: gzip`; both compressed and uncompressed responses carry `Vary: Accept-Encoding`, so intermediate caches do not mix the two representations.

The `Swagger UI` `OAuth2` redirect page is an exception: it is never compressed and is always cached in memory after the first request.

### Swagger UI options { #swagger-ui-options }

`swaggerui.options` is a map of `Swagger UI` initialization options that is inlined into the generated page.
The defaults are:

| Option | Configured value | Value in the page |
|--------|------------------|-------------------|
| `layout` | `"StandaloneLayout"` | `"StandaloneLayout"` |
| `validatorUrl` | `"null"` | `null` |
| `defaultModelsExpandDepth` | `"0"` | `0` |
| `deepLinking` | `"true"` | `true` |
| `persistAuthorization` | `"true"` | `true` |
| `displayOperationId` | `"true"` | `true` |
| `filter` | `"true"` | `true` |

Values are stored as strings, but they are inserted into the page as raw `JavaScript` when, after trimming, they are `null`, `true`, `false`, a number, or start with `{`, `[`, `function`, or `(`.
Everything else is inserted as a quoted `JavaScript` string, and an empty value becomes `""`.
This makes it possible to pass objects and functions through configuration:

===! ":material-code-json: `Hocon`"

    ```javascript
    openapi.management.swaggerui.options {
        layout = "BaseLayout" //(1)!
        defaultModelsExpandDepth = "-1"
        syntaxHighlight = "{ activated: false }" //(2)!
        onComplete = "() => window.swaggerReady = true" //(3)!
    }
    ```

    1. Rendered as a `JavaScript` string.
    2. Rendered as a `JavaScript` object, because the value starts with `{`.
    3. Rendered as a `JavaScript` arrow function, because the value starts with `(`.

=== ":simple-yaml: `YAML`"

    ```yaml
    openapi:
      management:
        swaggerui:
          options:
            layout: "BaseLayout" #(1)!
            defaultModelsExpandDepth: "-1"
            syntaxHighlight: "{ activated: false }" #(2)!
            onComplete: "() => window.swaggerReady = true" #(3)!
    ```

    1. Rendered as a `JavaScript` string.
    2. Rendered as a `JavaScript` object, because the value starts with `{`.
    3. Rendered as a `JavaScript` arrow function, because the value starts with `(`.

???+ warning "Options replace the defaults"

    The map is not merged with the built-in defaults: as soon as `options` is present in configuration, only the keys written there reach the page.
    If a single option needs to change, list the defaults that must be kept alongside it.

`withCredentials` is configured separately from `options` because it affects two things at once: it is passed to `Swagger UI` as the `withCredentials` flag, and when it is `true` the page also installs a request interceptor that sets `credentials = "include"` on every request made from the "Try it out" button.
Turn it off when the API is called from `Swagger UI` on another origin and browser credentials must not be attached.

The page also understands a `contextPath` value, taken from the `contextPath` cookie or, if the cookie is absent, from the query string of the page (`/swagger-ui?contextPath=/api`).
When it is set, every path of the displayed contract is shown with that prefix, which is convenient when the service is published behind a path prefix.

### Scalar { #scalar }

`Scalar` is the second bundled viewer and is enabled independently of `Swagger UI` — both pages may be exposed at the same time over the same contract files.
It receives the same list of contracts, so with more than one file the document switcher lists every file by its public name.

Both viewers resolve the contract `URL` in the browser: they take the current page address and replace the `swaggerui.path` or `scalar.path` segment with `path`.
Nothing has to be configured for a specific host or port, but if a reverse proxy publishes the page under a path that differs from the configured one, the substitution finds nothing and the contract is not loaded.

## Endpoints { #endpoints }

With serving enabled, the module registers the following `GET` routes on the public HTTP server (paths shown with default `path` values):

| Route | Backing handler | Enabled by |
|-------|-----------------|------------|
| `GET /openapi` (one file) or `GET /openapi/{file}` (more than one file) | `OpenApiHttpServerHandler` | `enabled = true` |
| `GET /swagger-ui` | `SwaggerUIHttpServerHandler` | `swaggerui.enabled = true` |
| `GET /swagger-ui/oauth2-redirect` | `SwaggerOauthHttpServerHandler` | registered automatically together with `Swagger UI` |
| `GET /scalar` | `ScalarHttpServerHandler` | `scalar.enabled = true` |

Each route uses the `path` value from its configuration section, so overriding a `path` moves the corresponding route.
The `OAuth2` redirect path is always `swaggerui.path` plus the `/oauth2-redirect` suffix.

A route whose section is disabled is not added to the router at all, so it answers like any unknown path.
Because of that, enabling a viewer page without `enabled = true` produces a page that loads but cannot fetch its contract — the file route simply does not exist.

## Recommendations { #recommendations }

???+ warning "Recommendation"

    We recommend creating the [contract first and then generating code from it](openapi-codegen.md).
    In this case, the module publishes the same contract file that is used for generation.

    If code is written first and the contract should be created from it, you can use the [Swagger Gradle Plugin](https://github.com/swagger-api/swagger-core/blob/master/modules/swagger-gradle-plugin/README.md)
    together with [Swagger annotations](https://github.com/swagger-api/swagger-core/wiki/Swagger-2.X---Annotations).

???+ warning "Do not expose the contract publicly by accident"

    All three routes live on the public HTTP server, so anything enabled here is reachable by every client that can reach the service.
    `enabled`, `swaggerui.enabled`, and `scalar.enabled` all default to `false`; keep the viewer pages turned on only in environments where the API description may be read freely.
