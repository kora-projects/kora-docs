---
search:
  exclude: true
title: Contract-First HTTP Server Advanced Guide
summary: Continue the OpenAPI HTTP Server guide by adding a second generated contract for forms, multipart, response mapping, generated controller interceptors, API-key authorization, and spec-driven validation
description: "Advanced contract-first Kora HTTP server: a second OpenAPI contract and a second GenerateTask, generated form and multipart FormParam records, sealed response wrappers, controller interceptors declared through the extensions generator option, a custom ViolationExceptionHttpServerResponseMapper, JsonNullable model fields, and API-key authorization through ApiSecurity markers and HttpServerPrincipalExtractor."
agent:
  use_when: "Use this file for questions about advanced contract-first Kora HTTP servers: hosting several OpenAPI contracts and GenerateTask tasks in one application, generated <Api>Controller.<Op>FormParam records for application/x-www-form-urlencoded and multipart/form-data, enableServerValidation with a custom ViolationExceptionHttpServerResponseMapper, attaching an HttpServerInterceptor through the extensions configOption with interceptorType, generated ApiSecurity markers from components.securitySchemes, HttpServerPrincipalExtractor with @Tag, Principal and PrincipalWithScopes, and publishing several files through openapi.management.files."
tags: openapi, http-server, advanced, forms, multipart, auth, validation
---

# Advanced Contract-First HTTP Server Guide { #advanced-contract-first-http }

This guide introduces advanced contract-first HTTP server patterns with Kora and OpenAPI. It covers how multiple OpenAPI specifications can coexist in one application, how generated delegates handle
forms, multipart uploads, and typed response variants, and how shared error handling and API-key authorization fit around generated transport code. You will also see how new contracts can evolve
independently while handwritten services remain the place for application behavior.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java OpenAPI HTTP Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-openapi-http-server-advanced-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin OpenAPI HTTP Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-openapi-http-server-advanced-app).

## What You'll Build { #youll-build }

You will extend the OpenAPI HTTP server application with:

- the same user CRUD contract from [Contract-First HTTP Server with OpenAPI](openapi-http-server.md)
- a second OpenAPI contract called `data-http-server.yaml`
- generated endpoints for form, multipart, and response-mapping routes
- a generated-controller interceptor for consistent JSON error responses
- a custom validation-error mapper that speaks the same `ErrorResponseTO` contract
- simple API-key authorization for the data endpoints
- one combined `/openapi` and `/swagger-ui` exposure for both contracts

## What You'll Need { #youll-need }

- JDK 25 or later
- Gradle 9+
- A text editor or IDE
- Completed [Contract-First HTTP Server with OpenAPI](openapi-http-server.md)
- Completed [HTTP Server Advanced Guide](http-server-advanced.md)

## Prerequisites { #prerequisites }

!!! note "Required: Complete OpenAPI HTTP Server and Advanced HTTP Server Guides"

    This guide assumes you have completed **[Contract-First HTTP Server with OpenAPI](openapi-http-server.md)** and **[HTTP Server Advanced](http-server-advanced.md)**, and already understand the contract-first user CRUD flow plus the advanced HTTP concepts used by the data routes.

    If you haven't completed those guides yet, do that first, because this guide combines generated OpenAPI delegates with advanced HTTP features such as forms, multipart, shared errors, and security.

Instead of re-teaching those pieces, we focus on the next step: how to apply advanced HTTP ideas in a generated, contract-first HTTP server.

## Overview { #overview }

In this guide we move in a very deliberate order:

1. keep the generated user API unchanged
2. add a second OpenAPI contract only for the advanced data routes
3. configure a second Kora generation task just for that contract
4. inspect the new generated abstractions
5. implement `DataApiDelegate`
6. shape validation failures into the contract's own error model
7. attach a generated-controller interceptor for shared error mapping
8. add API-key authorization through the OpenAPI security contract
9. expose both contracts together through OpenAPI management

The key design idea is separation:

- the user API remains the stable contract from the previous guide
- the advanced data API evolves in its own contract

That makes the example easier to teach and much closer to how real services often grow.

### Different Contracts { #different-contracts }

At first glance, it might seem simpler to keep everything in one huge OpenAPI file.

Sometimes that is correct. But sometimes a separate contract is healthier:

- different endpoint groups evolve at different speeds
- one group may need extra generation features
- one group may have different security or validation requirements
- one group may exist mostly to demonstrate transport techniques rather than business CRUD

That is exactly our situation here.

The user CRUD contract is already good. We do not want to re-teach it or risk changing it accidentally while adding advanced HTTP examples.

So we split the advanced routes into a separate contract:

- `user-http-server.yaml` stays the source of truth for user CRUD
- `data-http-server.yaml` becomes the source of truth for forms, multipart, shared error handling, API-key auth, and one focused validation example

This is also why only the **data** generator task gets the `extensions` option that attaches a controller interceptor. The user generator stays exactly as it was in the previous guide.

Several `GenerateTask` tasks can live in one module. They can even write into the same `outputDir`; the only real requirement is that generated packages do not collide, so give every task its own
`apiPackage`, `modelPackage`, and `invokerPackage`.

## Old OpenAPI Contract { #old-contract }

The first important step is actually a non-step: do **not** rewrite the user side.

Reuse the same generator task and the same contract from [Contract-First HTTP Server with OpenAPI](openapi-http-server.md).

That detail matters a lot for the story of the guide.

We are **not** replacing the previous guide. We are extending it.

So the user-side pieces stay the same:

- `user-http-server.yaml`
- `UsersApiDelegate`
- `UserApiDelegateImpl`
- the familiar `UserService` and repository flow

All new work in this guide is about the advanced data endpoints.

## New OpenAPI Contract { #new-contract }

Now we move the advanced `DataController` ideas from [HTTP Server Advanced](http-server-advanced.md) into their own OpenAPI contract.

Create `src/main/resources/openapi/data-http-server.yaml`:

??? example "OpenAPI contract"

    ```yaml
    openapi: 3.0.3
    info:
      title: Advanced Data API
      description: Form and multipart endpoints generated from a dedicated OpenAPI contract
      version: 1.0.0
    tags:
      - name: data
        description: Form and multipart operations
    paths:
      /data/form:
        post:
          tags:
            - data
          operationId: processForm
          summary: Process a URL-encoded form
          requestBody:
            required: true
            content:
              application/x-www-form-urlencoded:
                schema:
                  $ref: '#/components/schemas/FormRequestTO'
          responses:
            '200':
              description: Form processed
              content:
                text/plain:
                  schema:
                    type: string
            '400':
              description: Invalid request
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/ErrorResponseTO'
            '403':
              description: Invalid API key
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/ErrorResponseTO'
            '500':
              description: Internal server error
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/ErrorResponseTO'
      /data/upload:
        post:
          tags:
            - data
          operationId: processUpload
          summary: Process a multipart upload
          requestBody:
            required: true
            content:
              multipart/form-data:
                schema:
                  $ref: '#/components/schemas/UploadRequestTO'
          responses:
            '200':
              description: Upload processed
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/UploadResponseTO'
            '400':
              description: Invalid request
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/ErrorResponseTO'
            '403':
              description: Invalid API key
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/ErrorResponseTO'
            '500':
              description: Internal server error
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/ErrorResponseTO'
      /data/mapping-by-code/{code}:
        get:
          tags:
            - data
          operationId: mappingByCode
          summary: Return different HTTP outcomes by code
          parameters:
            - name: code
              in: path
              required: true
              schema:
                type: integer
                minimum: 200
                maximum: 599
          responses:
            '200':
              description: Success payload
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/PayloadTO'
            '400':
              description: Invalid request
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/ErrorResponseTO'
            '403':
              description: Invalid API key
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/ErrorResponseTO'
            '500':
              description: Internal server error
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/ErrorResponseTO'
    security:
      - apiKeyAuth: []
    components:
      securitySchemes:
        apiKeyAuth:
          type: apiKey
          in: header
          name: Authorization
      schemas:
        ErrorResponseTO:
          type: object
          required:
            - message
          properties:
            message:
              type: string
            details:
              type: array
              nullable: true
              items:
                type: string
        FormRequestTO:
          type: object
          required:
            - name
          properties:
            name:
              type: string
        UploadRequestTO:
          type: object
          required:
            - description
            - file
          properties:
            description:
              type: string
            file:
              type: string
              format: binary
        UploadResponseTO:
          type: object
          required:
            - fileCount
            - fileNames
          properties:
            fileCount:
              type: integer
            fileNames:
              type: array
              items:
                type: string
        PayloadTO:
          type: object
          required:
            - message
          properties:
            message:
              type: string
    ```

Four things in this contract drive everything that follows:

- `application/x-www-form-urlencoded` and `multipart/form-data` request bodies, which the generator turns into dedicated form parameter records instead of JSON models
- `format: binary`, which makes `UploadRequestTO.file` a file part rather than a string
- `minimum: 200` / `maximum: 599` on the `code` path parameter, which becomes a real validation constraint
- a top-level `security` requirement plus a `components.securitySchemes` entry, which is what generates the `ApiSecurity` markers

The `details` property of `ErrorResponseTO` deserves a separate note. It is `nullable: true` **and** absent from `required`, so it has three distinguishable states — missing, explicitly `null`, and
present with a value. Kora generates such a field as [`JsonNullable`](../documentation/json.md#jsonnullable-wrapper), which is why the mapper below wraps its list with `JsonNullable.of(...)`.

## OpenAPI Generation { #openapi-generation }

Now configure a second generation task.

This is the most important build step in the whole guide, because this is where we intentionally treat the data API differently from the user API.

===! ":fontawesome-brands-java: `Java`"

    Update `build.gradle`:

    ```groovy
    def openApiGenerateDataHttpServer = tasks.register("openApiGenerateDataHttpServer", GenerateTask) {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = layout.projectDirectory.file("src/main/resources/openapi/data-http-server.yaml")
        outputDir = layout.buildDirectory.dir("generated/data-http-server")
        def corePackage = "io.koraframework.guide.openapi.httpserver.data" //(1)!
        apiPackage = "${corePackage}.api"
        modelPackage = "${corePackage}.model"
        invokerPackage = "${corePackage}.invoker"
        configOptions = [
                mode                  : "java-server",
                enableServerValidation: "true", //(2)!
        ]
    }

    sourceSets.main {
        java.srcDirs += openApiGenerateUsersHttpServer.get().outputDir
        java.srcDirs += openApiGenerateDataHttpServer.get().outputDir //(3)!
    }

    compileJava.dependsOn openApiGenerateUsersHttpServer
    compileJava.dependsOn openApiGenerateDataHttpServer
    ```

    1.  A package of its own, so the two contracts never collide even though both generate an `ErrorResponseTO`.
    2.  Turns the `minimum` / `maximum` constraint on `code` into a real validation annotation on the generated controller.
    3.  Both generated trees are registered; nothing about the user task changes.

=== ":simple-kotlin: `Kotlin`"

    Update `build.gradle.kts`:

    ```kotlin
    val openApiGenerateDataHttpServer = tasks.register<GenerateTask>("openApiGenerateDataHttpServer") {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec.set(layout.projectDirectory.file("src/main/resources/openapi/data-http-server.yaml"))
        outputDir.set(layout.buildDirectory.dir("generated/data-http-server"))
        val corePackage = "io.koraframework.guide.openapi.httpserver.data" //(1)!
        apiPackage = "${corePackage}.api"
        modelPackage = "${corePackage}.model"
        invokerPackage = "${corePackage}.invoker"
        configOptions = mapOf(
            "mode" to "kotlin-server",
            "enableServerValidation" to "true", //(2)!
        )
    }

    kotlin.sourceSets.main {
        kotlin.srcDir(openApiGenerateUsersHttpServer.get().outputDir)
        kotlin.srcDir(openApiGenerateDataHttpServer.get().outputDir) //(3)!
    }

    tasks.matching { it.name.startsWith("ksp") }.configureEach {
        dependsOn(openApiGenerateUsersHttpServer)
        dependsOn(openApiGenerateDataHttpServer)
    }
    ```

    1.  A package of its own, so the two contracts never collide even though both generate an `ErrorResponseTO`.
    2.  Turns the `minimum` / `maximum` constraint on `code` into a real validation annotation on the generated controller.
    3.  Both generated trees are registered; nothing about the user task changes.

Why this split is so useful:

- `openApiGenerateUsersHttpServer` stays simple and unchanged
- `openApiGenerateDataHttpServer` gets the advanced behavior

And at this early stage, we intentionally keep the generator configuration minimal. We are **not** yet configuring the custom generated-controller interceptor: first we implement the delegate, then we
shape validation errors, and only after `DataApiExceptionHandler` exists do we attach it. That keeps the guide aligned with the order in which those classes actually appear.

This is exactly the kind of feature separation that a second contract justifies.

## Generated Classes { #generated-classes }

Run:

```bash
./gradlew clean classes
```

Now inspect the generated files:

===! ":fontawesome-brands-java: `Java`"

    - `build/generated/data-http-server/io/koraframework/guide/openapi/httpserver/data/api/DataApiController.java`
    - `build/generated/data-http-server/io/koraframework/guide/openapi/httpserver/data/api/DataApiDelegate.java`
    - `build/generated/data-http-server/io/koraframework/guide/openapi/httpserver/data/api/DataApiResponses.java`
    - `build/generated/data-http-server/io/koraframework/guide/openapi/httpserver/data/api/DataApiServerRequestMappers.java`
    - `build/generated/data-http-server/io/koraframework/guide/openapi/httpserver/data/api/ApiSecurity.java`
    - `build/generated/data-http-server/io/koraframework/guide/openapi/httpserver/data/model/UploadResponseTO.java`
    - `build/generated/data-http-server/io/koraframework/guide/openapi/httpserver/data/model/PayloadTO.java`
    - `build/generated/data-http-server/io/koraframework/guide/openapi/httpserver/data/model/ErrorResponseTO.java`

=== ":simple-kotlin: `Kotlin`"

    - `build/generated/data-http-server/io/koraframework/guide/openapi/httpserver/data/api/DataApiController.kt`
    - `build/generated/data-http-server/io/koraframework/guide/openapi/httpserver/data/api/DataApiDelegate.kt`
    - `build/generated/data-http-server/io/koraframework/guide/openapi/httpserver/data/api/DataApiResponses.kt`
    - `build/generated/data-http-server/io/koraframework/guide/openapi/httpserver/data/api/DataApiServerRequestMappers.kt`
    - `build/generated/data-http-server/io/koraframework/guide/openapi/httpserver/data/api/ApiSecurity.kt`
    - `build/generated/data-http-server/io/koraframework/guide/openapi/httpserver/data/model/UploadResponseTO.kt`
    - `build/generated/data-http-server/io/koraframework/guide/openapi/httpserver/data/model/PayloadTO.kt`
    - `build/generated/data-http-server/io/koraframework/guide/openapi/httpserver/data/model/ErrorResponseTO.kt`

The most interesting generated abstractions here are `DataApiDelegate`, `DataApiController`, `DataApiResponses`, and `ApiSecurity`.

`DataApiDelegate`:

This is the contract you implement. It plays exactly the same architectural role as `UsersApiDelegate`, but for the new advanced endpoints.

One shape is new. A form or multipart request body is not a JSON model, so it is not passed as a `*TO` model. The generator emits one record per form operation, nested inside the **controller**, and
passes it to the delegate through a generated request mapper:

- `DataApiController.ProcessFormFormParam(String name)`
- `DataApiController.ProcessUploadFormParam(String description, FormMultipart.FormPart file)`

Notice `UploadRequestTO` is not in the generated model list above: because that schema is only ever used as a `multipart/form-data` body, its fields become the form record instead.

A `format: binary` property becomes `FormMultipart.FormPart`, a sealed type whose `name()` is the **form field name**. The uploaded file name is a different value: match on
`FormMultipart.FormPart.MultipartFile` and read its `fileName()` when you need it.

`DataApiController`:

This is the generated transport layer. Because the contract includes form-url-encoded input, multipart input, explicit status modeling, and a security requirement, the generated controller now does
considerably more than in the simple CRUD case: it decodes form parts through `DataApiServerRequestMappers`, applies the generated validation annotations, and runs the generated security interceptor
before your delegate is called.

`DataApiResponses`:

These wrappers model the allowed HTTP outcomes from the spec: `200`, `400`, `403`, and `500`. That means error handling is now part of the transport contract, not just something we improvise in code.

Note that `processForm` declares a `text/plain` success body, so `ProcessForm200ApiResponse` carries a plain `String` as its `content` — response wrappers follow the declared media type, not only JSON.

`ApiSecurity`:

This is generated from the OpenAPI `securitySchemes` section. The scheme name is PascalCased, so `apiKeyAuth` becomes the marker class `ApiSecurity.ApiKeyAuth`. It is the bridge between the OpenAPI
security contract and the principal extractor you will register in `Application`.

This is one of the most valuable ideas in the guide:

- security is declared in the contract
- the generator produces the marker types
- your app plugs in the actual runtime check

## Delegate { #delegate }

Now connect the generated data transport layer to application logic.

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/io/koraframework/guide/openapi/httpserver/advanced/controller/DataApiDelegateImpl.java`:

    ```java
    package io.koraframework.guide.openapi.httpserver.advanced.controller;

    import java.util.List;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.openapi.httpserver.data.api.DataApiController;
    import io.koraframework.guide.openapi.httpserver.data.api.DataApiDelegate;
    import io.koraframework.guide.openapi.httpserver.data.api.DataApiResponses;
    import io.koraframework.guide.openapi.httpserver.data.model.PayloadTO;
    import io.koraframework.guide.openapi.httpserver.data.model.UploadResponseTO;
    import io.koraframework.http.server.common.response.HttpServerResponseException;

    @Component
    public final class DataApiDelegateImpl implements DataApiDelegate {

        @Override
        public DataApiResponses.ProcessFormApiResponse processForm(DataApiController.ProcessFormFormParam form) {
            if ("admin".equalsIgnoreCase(form.name())) {
                throw new RestrictedFormNameException(form.name()); //(1)!
            }
            return new DataApiResponses.ProcessFormApiResponse.ProcessForm200ApiResponse("Hello World, " + form.name());
        }

        @Override
        public DataApiResponses.ProcessUploadApiResponse processUpload(DataApiController.ProcessUploadFormParam form) {
            var response = new UploadResponseTO(
                    1,
                    List.of(form.file().name()) //(2)!
            );
            return new DataApiResponses.ProcessUploadApiResponse.ProcessUpload200ApiResponse(response);
        }

        @Override
        public DataApiResponses.MappingByCodeApiResponse mappingByCode(int code) {
            if (code == 200) {
                return new DataApiResponses.MappingByCodeApiResponse.MappingByCode200ApiResponse(
                        new PayloadTO("Hello from response mapper")
                );
            }
            throw HttpServerResponseException.of(code, "Request failed with code " + code); //(3)!
        }
    }
    ```

    1.  A domain exception that no generated wrapper describes; the interceptor added later turns it into the contract's `500`.
    2.  `FormPart.name()` is the form field name (`file` here); no manual `HttpServerRequest` parsing is needed.
    3.  Throwing is the right move for statuses that are outside this operation's declared response family.

    And the small exception type it uses, `src/main/java/io/koraframework/guide/openapi/httpserver/advanced/controller/RestrictedFormNameException.java`:

    ```java
    package io.koraframework.guide.openapi.httpserver.advanced.controller;

    public final class RestrictedFormNameException extends RuntimeException {

        public RestrictedFormNameException(String name) {
            super("Form name '" + name + "' is restricted");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/io/koraframework/guide/openapi/httpserver/advanced/controller/DataApiDelegateImpl.kt`:

    ```kotlin
    package io.koraframework.guide.openapi.httpserver.advanced.controller

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.openapi.httpserver.data.api.DataApiController
    import io.koraframework.guide.openapi.httpserver.data.api.DataApiDelegate
    import io.koraframework.guide.openapi.httpserver.data.api.DataApiResponses
    import io.koraframework.guide.openapi.httpserver.data.model.PayloadTO
    import io.koraframework.guide.openapi.httpserver.data.model.UploadResponseTO
    import io.koraframework.http.server.common.response.HttpServerResponseException

    @Component
    class DataApiDelegateImpl : DataApiDelegate {

        override fun processForm(form: DataApiController.ProcessFormFormParam): DataApiResponses.ProcessFormApiResponse {
            if (form.name.equals("admin", ignoreCase = true)) {
                throw RestrictedFormNameException(form.name) //(1)!
            }

            return DataApiResponses.ProcessFormApiResponse.ProcessForm200ApiResponse("Hello World, ${form.name}")
        }

        override fun processUpload(form: DataApiController.ProcessUploadFormParam): DataApiResponses.ProcessUploadApiResponse {
            val response = UploadResponseTO(fileCount = 1, fileNames = listOf(form.file.name())) //(2)!
            return DataApiResponses.ProcessUploadApiResponse.ProcessUpload200ApiResponse(response)
        }

        override fun mappingByCode(code: Int): DataApiResponses.MappingByCodeApiResponse {
            if (code == 200) {
                return DataApiResponses.MappingByCodeApiResponse.MappingByCode200ApiResponse(
                    PayloadTO("Hello from response mapper")
                )
            }
            throw HttpServerResponseException.of(code, "Request failed with code $code") //(3)!
        }
    }
    ```

    1.  A domain exception that no generated wrapper describes; the interceptor added later turns it into the contract's `500`.
    2.  `FormPart.name()` is the form field name (`file` here); no manual `HttpServerRequest` parsing is needed.
    3.  Throwing is the right move for statuses that are outside this operation's declared response family.

    And the small exception type it uses, `src/main/kotlin/io/koraframework/guide/openapi/httpserver/advanced/controller/RestrictedFormNameException.kt`:

    ```kotlin
    package io.koraframework.guide.openapi.httpserver.advanced.controller

    class RestrictedFormNameException(name: String) : RuntimeException("Form name '$name' is restricted")
    ```

There are two nice things to notice here.

First, the delegate stays very small. That is because the generated layer already handled a lot:

- request decoding, including form and multipart parts
- transport typing
- security contract integration
- validation hooks

Second, the logic intentionally mirrors the manual `DataController` from [HTTP Server Advanced](http-server-advanced.md). The guide is not inventing different behavior. It is showing how the same
behavior looks when the transport layer is generated from OpenAPI instead of handwritten.

There is also a deliberate contrast between the two failure paths, and it is the reason the next two sections exist:

- `mappingByCode` throws `HttpServerResponseException`, which already carries a status code
- `processForm` throws `RestrictedFormNameException`, which carries nothing an HTTP layer can use

Both currently produce a response that does **not** match the `ErrorResponseTO` shape the contract promises. Fixing that is the job of the interceptor we add below.

## Server Validation { #server-validation }

The full server OpenAPI validation rules are covered in [OpenAPI Codegen: Validation](../documentation/openapi-codegen.md#validation).

`enableServerValidation` is already set on the data task, so validation is active. In this guide we intentionally keep that validation surface very small — only one parameter is constrained:

- `code` in `/data/mapping-by-code/{code}`, allowed range `200..599`

This is useful for two reasons. First, it demonstrates spec-driven validation clearly on one focused example. Second, it avoids turning the whole advanced contract into a validation tutorial: the form
and multipart steps stay focused on transport formats.

When validation is enabled, the generator also adds `@InterceptWith(ValidationHttpServerInterceptor.class)` to the controller. That interceptor catches `ViolationException` and, by default, answers
with a plain `400`. Plain text is not what our contract promises, so we teach it the `ErrorResponseTO` shape by providing a `ViolationExceptionHttpServerResponseMapper` component:

===! ":fontawesome-brands-java: `Java`"

    Add to `src/main/java/io/koraframework/guide/openapi/httpserver/advanced/Application.java`:

    ```java
    default ViolationExceptionHttpServerResponseMapper customViolationExceptionHttpServerResponseMapper(
            JsonWriter<ErrorResponseTO> errorResponseJsonWriter) { //(1)!
        return (request, exception) -> {
            var details = exception.getViolations().stream()
                    .map(v -> "Path " + v.path() + " violated: " + v.message())
                    .toList();

            var response = new ErrorResponseTO(
                    "Encountered '%s' validation violations".formatted(details.size()),
                    JsonNullable.of(details)); //(2)!
            return HttpServerResponse.of(
                    400,
                    HttpBody.json(errorResponseJsonWriter.toByteArray(response)));
        };
    }
    ```

    1.  The writer for a generated model is itself generated, so it is simply injected.
    2.  `details` is `nullable` and not `required`, so the generated field is `JsonNullable<List<String>>`.

    The imports this method needs:

    ```java
    import io.koraframework.guide.openapi.httpserver.data.model.ErrorResponseTO;
    import io.koraframework.http.common.body.HttpBody;
    import io.koraframework.http.server.common.response.HttpServerResponse;
    import io.koraframework.json.common.JsonNullable;
    import io.koraframework.json.common.JsonWriter;
    import io.koraframework.validation.module.http.server.ViolationExceptionHttpServerResponseMapper;
    ```

=== ":simple-kotlin: `Kotlin`"

    Add to `src/main/kotlin/io/koraframework/guide/openapi/httpserver/advanced/Application.kt`:

    ```kotlin
    fun customViolationExceptionHttpServerResponseMapper(
        errorResponseJsonWriter: JsonWriter<ErrorResponseTO> //(1)!
    ): ViolationExceptionHttpServerResponseMapper {
        return ViolationExceptionHttpServerResponseMapper { _, exception ->
            val details = exception.violations.map { violation ->
                "Path ${violation.path()} violated: ${violation.message()}"
            }

            val response = ErrorResponseTO(
                message = "Encountered '${details.size}' validation violations",
                details = JsonNullable.of(details) //(2)!
            )
            HttpServerResponse.of(400, HttpBody.json(errorResponseJsonWriter.toByteArray(response)))
        }
    }
    ```

    1.  The writer for a generated model is itself generated, so it is simply injected.
    2.  `details` is `nullable` and not `required`, so the generated property is `JsonNullable<List<String>>`.

    The imports this method needs:

    ```kotlin
    import io.koraframework.guide.openapi.httpserver.data.model.ErrorResponseTO
    import io.koraframework.http.common.body.HttpBody
    import io.koraframework.http.server.common.response.HttpServerResponse
    import io.koraframework.json.common.JsonNullable
    import io.koraframework.json.common.JsonWriter
    import io.koraframework.validation.module.http.server.ViolationExceptionHttpServerResponseMapper
    ```

That is also why `ErrorResponseTO` has two layers in this contract:

- `message` for the top-level problem summary
- `details` for parameter-level validation messages when they exist

And because the constraint lives in the OpenAPI schema, the generated transport layer rejects out-of-range values **before** your delegate ever sees them.

!!! tip "Mapping violations entirely by hand"

    If you would rather handle `ViolationException` in your own interceptor or response mapper instead of the standard one, set `enableServerValidationInterceptor = "false"` on the generation task.
    The validation annotations stay, but `@InterceptWith(ValidationHttpServerInterceptor.class)` is not generated. In this guide we keep the standard interceptor and only replace the mapper it uses.

## Error Interceptor { #error-interceptor }

Generated server controller interceptors are described in more detail in [OpenAPI Codegen: server interceptors](../documentation/openapi-codegen.md#interceptors-2).

Validation failures already become structured JSON. Now we add one more layer for the **other** kinds of failures we want to normalize — including that `RestrictedFormNameException` from the delegate.

In the manual advanced server guide we used a global `ExceptionHandler`. Here we do something deliberately narrower: for the generated **data** controller we attach a contract-specific interceptor
through the generator configuration.

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/io/koraframework/guide/openapi/httpserver/advanced/controller/DataApiExceptionHandler.java`:

    ```java
    package io.koraframework.guide.openapi.httpserver.advanced.controller;

    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.openapi.httpserver.data.model.ErrorResponseTO;
    import io.koraframework.http.common.body.HttpBody;
    import io.koraframework.http.server.common.interceptor.HttpServerInterceptor;
    import io.koraframework.http.server.common.request.HttpServerRequest;
    import io.koraframework.http.server.common.response.HttpServerResponse;
    import io.koraframework.http.server.common.response.HttpServerResponseException;
    import io.koraframework.json.common.JsonWriter;
    import io.koraframework.validation.common.ViolationException;

    @Component //(1)!
    public final class DataApiExceptionHandler implements HttpServerInterceptor {

        private final JsonWriter<ErrorResponseTO> errorJsonWriter;

        public DataApiExceptionHandler(JsonWriter<ErrorResponseTO> errorJsonWriter) {
            this.errorJsonWriter = errorJsonWriter;
        }

        @Override
        public HttpServerResponse intercept(HttpServerRequest request, InterceptChain chain) throws Exception { //(2)!
            try {
                return chain.process(request);
            } catch (ViolationException e) {
                throw e; //(3)!
            } catch (HttpServerResponseException e) {
                return jsonResponse(e.code(), e.getMessage());
            } catch (IllegalArgumentException e) {
                return jsonResponse(400, "Invalid request parameters");
            } catch (SecurityException e) {
                return jsonResponse(403, e.getMessage() != null ? e.getMessage() : "Access denied"); //(4)!
            } catch (Exception e) {
                return jsonResponse(500, "An unexpected error occurred");
            }
        }

        private HttpServerResponse jsonResponse(int statusCode, String message) {
            return HttpServerResponse.of(statusCode, HttpBody.json(this.errorJsonWriter.toByteArray(new ErrorResponseTO(message))));
        }
    }
    ```

    1.  An interceptor referenced from `extensions` must be a component of the graph.
    2.  Kora 2.0 interceptors are synchronous: they take the request and the chain and return the response. There is no `Context` parameter and no `CompletionStage`.
    3.  Left to `ViolationExceptionHttpServerResponseMapper`, which already renders the violations.
    4.  The API-key extractor added in the next section signals a rejected key with `SecurityException`.

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/io/koraframework/guide/openapi/httpserver/advanced/controller/DataApiExceptionHandler.kt`:

    ```kotlin
    package io.koraframework.guide.openapi.httpserver.advanced.controller

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.openapi.httpserver.data.model.ErrorResponseTO
    import io.koraframework.http.common.body.HttpBody
    import io.koraframework.http.server.common.interceptor.HttpServerInterceptor
    import io.koraframework.http.server.common.request.HttpServerRequest
    import io.koraframework.http.server.common.response.HttpServerResponse
    import io.koraframework.http.server.common.response.HttpServerResponseException
    import io.koraframework.json.common.JsonWriter
    import io.koraframework.validation.common.ViolationException

    @Component //(1)!
    class DataApiExceptionHandler(
        private val errorJsonWriter: JsonWriter<ErrorResponseTO>
    ) : HttpServerInterceptor {

        override fun intercept(request: HttpServerRequest, chain: HttpServerInterceptor.InterceptChain): HttpServerResponse { //(2)!
            try {
                return chain.process(request)
            } catch (e: ViolationException) {
                throw e //(3)!
            } catch (e: HttpServerResponseException) {
                return jsonResponse(e.code(), e.message ?: "HTTP error")
            } catch (e: IllegalArgumentException) {
                return jsonResponse(400, "Invalid request parameters")
            } catch (e: SecurityException) {
                return jsonResponse(403, e.message ?: "Access denied") //(4)!
            } catch (e: Exception) {
                return jsonResponse(500, "An unexpected error occurred")
            }
        }

        private fun jsonResponse(statusCode: Int, message: String): HttpServerResponse {
            return HttpServerResponse.of(
                statusCode,
                HttpBody.json(errorJsonWriter.toByteArray(ErrorResponseTO(message)))
            )
        }
    }
    ```

    1.  An interceptor referenced from `extensions` must be a component of the graph.
    2.  Kora 2.0 interceptors are synchronous: they take the request and the chain and return the response. There is no `Context` parameter and no `CompletionStage`.
    3.  Left to `ViolationExceptionHttpServerResponseMapper`, which already renders the violations.
    4.  The API-key extractor added in the next section signals a rejected key with `SecurityException`.

The key difference from the manual guide is scope:

- in [HTTP Server Advanced](http-server-advanced.md), the interceptor was global
- here, it is attached only to the **generated data API**

That is a subtle but powerful pattern. Generated transports do not all have to share the same cross-cutting behavior; you can apply different interceptor strategies to different generated contracts.

The `ViolationException` branch is deliberate. We already decided that validation errors belong to `customViolationExceptionHttpServerResponseMapper`, so this handler rethrows them untouched and lets
`ValidationHttpServerInterceptor` produce the response. Responsibilities are now split cleanly:

- `ValidationHttpServerInterceptor` handles generated validation failures and returns `ErrorResponseTO(message, details)`
- `DataApiExceptionHandler` handles the rest of the transport-level failures we want to normalize

Only now does it make sense to attach the interceptor in the generator configuration. In Kora 2.0 this is done with the `extensions` option — one JSON document with three optional sections: `*` for
everything, `tags` keyed by OpenAPI tag name, and `operations` keyed by `operationId`.

===! ":fontawesome-brands-java: `Java`"

    Update `build.gradle`:

    ```groovy
    def openApiGenerateDataHttpServer = tasks.register("openApiGenerateDataHttpServer", GenerateTask) {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = layout.projectDirectory.file("src/main/resources/openapi/data-http-server.yaml")
        outputDir = layout.buildDirectory.dir("generated/data-http-server")
        def corePackage = "io.koraframework.guide.openapi.httpserver.data"
        apiPackage = "${corePackage}.api"
        modelPackage = "${corePackage}.model"
        invokerPackage = "${corePackage}.invoker"
        configOptions = [
                mode                  : "java-server",
                enableServerValidation: "true",
                extensions            : """
                        {
                          "*": {
                            "interceptorType": "io.koraframework.guide.openapi.httpserver.advanced.controller.DataApiExceptionHandler"
                          }
                        }
                        """, //(1)!
        ]
    }
    ```

    1.  Emits `@InterceptWith(DataApiExceptionHandler.class)` on every generated operation of this contract. Invalid JSON here fails generation with a message showing the expected shape.

=== ":simple-kotlin: `Kotlin`"

    Update `build.gradle.kts`:

    ```kotlin
    val openApiGenerateDataHttpServer = tasks.register<GenerateTask>("openApiGenerateDataHttpServer") {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec.set(layout.projectDirectory.file("src/main/resources/openapi/data-http-server.yaml"))
        outputDir.set(layout.buildDirectory.dir("generated/data-http-server"))
        val corePackage = "io.koraframework.guide.openapi.httpserver.data"
        apiPackage = "${corePackage}.api"
        modelPackage = "${corePackage}.model"
        invokerPackage = "${corePackage}.invoker"
        configOptions = mapOf(
            "mode" to "kotlin-server",
            "enableServerValidation" to "true",
            "extensions" to """
                {
                  "*": {
                    "interceptorType": "io.koraframework.guide.openapi.httpserver.advanced.controller.DataApiExceptionHandler"
                  }
                }
            """.trimIndent(), //(1)!
        )
    }
    ```

    1.  Emits `@InterceptWith(DataApiExceptionHandler::class)` on every generated operation of this contract. Invalid JSON here fails generation with a message showing the expected shape.

`extensions` can do more than interceptors — it also injects additional annotations onto generated methods, models, and enums. If you only want to select an existing component by tag, give
`interceptorTag` instead of `interceptorType` and the base `HttpServerInterceptor` type is used with that tag.

## API Key Authorization { #api-key }

The mapping from OpenAPI security schemes to Kora components is described in [OpenAPI Codegen: Authorization](../documentation/openapi-codegen.md#authorization).

The `data-http-server.yaml` contract already declares the security requirement once at the top level, and the scheme itself under `components`:

```yaml
security:
  - apiKeyAuth: []

components:
  securitySchemes:
    apiKeyAuth:
      type: apiKey
      in: header
      name: Authorization
```

Because the requirement is global, you do not have to repeat it on every individual operation. From this, the generator produces `ApiSecurity.ApiKeyAuth` — the marker class that identifies which
extractor belongs to which scheme.

Now we plug in the runtime behavior. First, the config contract for the expected key:

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/io/koraframework/guide/openapi/httpserver/advanced/controller/DataApiAuthConfig.java`:

    ```java
    package io.koraframework.guide.openapi.httpserver.advanced.controller;

    import io.koraframework.config.common.annotation.ConfigSource;

    @ConfigSource("auth.apiKey")
    public interface DataApiAuthConfig {

        String value();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/io/koraframework/guide/openapi/httpserver/advanced/controller/DataApiAuthConfig.kt`:

    ```kotlin
    package io.koraframework.guide.openapi.httpserver.advanced.controller

    import io.koraframework.config.common.annotation.ConfigSource

    @ConfigSource("auth.apiKey")
    interface DataApiAuthConfig {
        fun value(): String
    }
    ```

Then the principal type that represents an authenticated caller:

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/io/koraframework/guide/openapi/httpserver/advanced/controller/DataApiPrincipal.java`:

    ```java
    package io.koraframework.guide.openapi.httpserver.advanced.controller;

    import io.koraframework.common.Principal;

    public record DataApiPrincipal(String name) implements Principal {}
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/io/koraframework/guide/openapi/httpserver/advanced/controller/DataApiPrincipal.kt`:

    ```kotlin
    package io.koraframework.guide.openapi.httpserver.advanced.controller

    import io.koraframework.common.Principal

    data class DataApiPrincipal(val name: String) : Principal
    ```

And finally the extractor itself, tagged with the generated marker:

===! ":fontawesome-brands-java: `Java`"

    Add to `src/main/java/io/koraframework/guide/openapi/httpserver/advanced/Application.java`:

    ```java
    @Tag(ApiSecurity.ApiKeyAuth.class) //(1)!
    default HttpServerPrincipalExtractor<String, Principal> apiKeyHttpServerPrincipalExtractor(DataApiAuthConfig config) { //(2)!
        return (request, value) -> {
            if (value == null || !config.value().equals(value)) {
                throw new SecurityException("Invalid API key"); //(3)!
            }
            return new DataApiPrincipal("data-api-client"); //(4)!
        };
    }
    ```

    1.  Binds this extractor to the `apiKeyAuth` scheme of the contract.
    2.  `T` is the credential the generated controller pulls out of the request; `P` is the principal you build from it.
    3.  Rejecting with an exception is what `DataApiExceptionHandler` turns into the contract's `403`.
    4.  Returned principals are published for the whole request and readable anywhere through `Principal.current()`.

    The imports this method needs:

    ```java
    import io.koraframework.common.Principal;
    import io.koraframework.common.annotation.Tag;
    import io.koraframework.guide.openapi.httpserver.advanced.controller.DataApiAuthConfig;
    import io.koraframework.guide.openapi.httpserver.advanced.controller.DataApiPrincipal;
    import io.koraframework.guide.openapi.httpserver.data.api.ApiSecurity;
    import io.koraframework.http.server.common.auth.HttpServerPrincipalExtractor;
    ```

=== ":simple-kotlin: `Kotlin`"

    Add to `src/main/kotlin/io/koraframework/guide/openapi/httpserver/advanced/Application.kt`:

    ```kotlin
    @Tag(ApiSecurity.ApiKeyAuth::class) //(1)!
    fun apiKeyHttpServerPrincipalExtractor(config: DataApiAuthConfig): HttpServerPrincipalExtractor<String, Principal> { //(2)!
        return HttpServerPrincipalExtractor { _, value ->
            if (value == null || config.value() != value) {
                throw SecurityException("Invalid API key") //(3)!
            }
            DataApiPrincipal("data-api-client") //(4)!
        }
    }
    ```

    1.  Binds this extractor to the `apiKeyAuth` scheme of the contract.
    2.  `T` is the credential the generated controller pulls out of the request; `P` is the principal you build from it.
    3.  Rejecting with an exception is what `DataApiExceptionHandler` turns into the contract's `403`.
    4.  Returned principals are published for the whole request and readable anywhere through `Principal.current()`.

    The imports this method needs:

    ```kotlin
    import io.koraframework.common.Principal
    import io.koraframework.common.annotation.Tag
    import io.koraframework.guide.openapi.httpserver.advanced.controller.DataApiAuthConfig
    import io.koraframework.guide.openapi.httpserver.advanced.controller.DataApiPrincipal
    import io.koraframework.guide.openapi.httpserver.data.api.ApiSecurity
    import io.koraframework.http.server.common.auth.HttpServerPrincipalExtractor
    ```

This is one of the nicest contract-first patterns in the guide.

The OpenAPI file says: this route group requires API key auth. The generator says: here is the security abstraction for that requirement. Your application says: here is how that API key is actually
validated at runtime.

That is a very clean separation between contract, generated integration point, and runtime policy.

!!! note "Rejecting with `null` versus throwing"

    An extractor has two ways to refuse a credential. Returning `null` rejects only **this** security requirement, so the generated interceptor moves on to the next alternative the contract allows, and answers `401 Unauthorized` when every alternative is exhausted.
    Throwing, as above, ends the request immediately — which is what we want here, because there is only one scheme and we want our own `403` body.

## Authorization Options { #authorization-options }

The example in this guide uses the simplest possible option: one API key, one global security requirement, one `HttpServerPrincipalExtractor`.

That is a great starting point. But OpenAPI security can model several different shapes, and it helps to know how they differ before you choose one for a real service.

This section is intentionally theoretical. It does not change the runnable application from this guide. Instead, it shows common patterns you can describe in OpenAPI and then connect to Kora runtime
extractors.

### 1. Global API Key { #1-global-api-key }

This is the pattern we use in this guide. It works well when:

- the whole API belongs to one protected integration surface
- every route should require the same secret
- you want the smallest possible amount of security wiring

```yaml
security:
  - apiKeyAuth: []

components:
  securitySchemes:
    apiKeyAuth:
      type: apiKey
      in: header
      name: Authorization
```

Server security supports `apiKey` schemes read from a header, a query parameter, or a cookie, so the same wiring covers all three placements.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(ApiSecurity.ApiKeyAuth.class)
    default HttpServerPrincipalExtractor<String, Principal> apiKeyHttpServerPrincipalExtractor(MyAuthConfig config) {
        return (request, value) -> {
            if (value == null || !config.value().equals(value)) {
                throw new SecurityException("Invalid API key");
            }
            return new MyPrincipal("integration-client");
        };
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(ApiSecurity.ApiKeyAuth::class)
    fun apiKeyHttpServerPrincipalExtractor(config: MyAuthConfig): HttpServerPrincipalExtractor<String, Principal> {
        return HttpServerPrincipalExtractor { _, value ->
            if (value == null || config.value() != value) {
                throw SecurityException("Invalid API key")
            }
            MyPrincipal("integration-client")
        }
    }
    ```

This approach is simple and practical for internal service-to-service calls, admin endpoints behind infrastructure controls, and technical APIs consumed by a small number of trusted clients.

### 2. Route Protection { #2-route-protection }

Sometimes not every route should be protected the same way: public health or login endpoints may stay open, and one section of the API may use a different scheme.

In that case, omit global `security` and describe it directly on operations:

```yaml
paths:
  /public/ping:
    get:
      security: []
      responses:
        '200':
          description: OK
  /users:
    get:
      security:
        - apiKeyAuth: []
      responses:
        '200':
          description: Protected
```

This is useful when the API surface is mixed: part public, part protected, part protected by different schemes.

### 3. Basic Authentication { #3-basic-authentication }

Basic auth is another common option. `http` schemes with `basic` or `bearer` are read from the `Authorization` header:

```yaml
components:
  securitySchemes:
    basicAuth:
      type: http
      scheme: basic

security:
  - basicAuth: []
```

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(ApiSecurity.BasicAuth.class)
    default HttpServerPrincipalExtractor<String, Principal> basicHttpServerPrincipalExtractor() {
        return (request, credentials) -> {
            if (credentials == null) {
                throw new SecurityException("Missing credentials");
            }
            var parts = credentials.split(":", 2);
            if (parts.length != 2) {
                throw new SecurityException("Invalid basic auth format");
            }
            return new MyPrincipal(parts[0]);
        };
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(ApiSecurity.BasicAuth::class)
    fun basicHttpServerPrincipalExtractor(): HttpServerPrincipalExtractor<String, Principal> {
        return HttpServerPrincipalExtractor { _, credentials ->
            if (credentials == null) {
                throw SecurityException("Missing credentials")
            }
            val parts = credentials.split(":", limit = 2)
            if (parts.size != 2) {
                throw SecurityException("Invalid basic auth format")
            }
            MyPrincipal(parts[0])
        }
    }
    ```

Basic auth can be acceptable for simple internal tools, demos, and legacy integrations. It should usually be used only over HTTPS, and in many modern systems Bearer/JWT is the more flexible choice.

### 4. Bearer Tokens and JWT { #4-bearer-tokens-jwt }

If your API is meant for browsers, mobile clients, or user-facing sessions, Bearer auth is often a better fit than API keys.

```yaml
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

security:
  - bearerAuth: []
```

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(ApiSecurity.BearerAuth.class)
    default HttpServerPrincipalExtractor<String, Principal> bearerHttpServerPrincipalExtractor(JwtService jwtService) {
        return (request, token) -> {
            if (token == null || token.isBlank()) {
                throw new SecurityException("Missing bearer token");
            }
            return new UserPrincipal(jwtService.extractUserFromToken(token));
        };
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(ApiSecurity.BearerAuth::class)
    fun bearerHttpServerPrincipalExtractor(jwtService: JwtService): HttpServerPrincipalExtractor<String, Principal> {
        return HttpServerPrincipalExtractor { _, token ->
            if (token.isNullOrBlank()) {
                throw SecurityException("Missing bearer token")
            }
            UserPrincipal(jwtService.extractUserFromToken(token))
        }
    }
    ```

This works well when the caller is an end user, when you want token expiration, and when you need claims, roles, or tenant information inside the token.

An `oauth2` or `openId` scheme is wired the same way, but its operations declare **scopes**. For those, the principal must implement `PrincipalWithScopes` so the generated interceptor can compare the
granted scopes against the ones the operation requires.

### 5. Multiple Schemes { #5-multiple-schemes }

OpenAPI can describe cases where a route accepts one scheme **or** another. This is written as multiple objects inside the `security` array:

```yaml
security:
  - apiKeyAuth: []
  - basicAuth: []
```

This means the caller may authenticate with `apiKeyAuth` **or** with `basicAuth` — useful during migration periods and for mixed clients, where machine clients use API keys and operator tools use
basic auth.

On the Kora side you provide extractors for both generated markers. The generated interceptor tries the alternatives in turn; an extractor that returns `null` declines its requirement and the next one
is attempted, and only when all of them decline does the request end with `401 Unauthorized`.

### 6. Combined Schemes { #6-combined-schemes }

OpenAPI also supports combined requirements. Inside one security object, multiple schemes are interpreted **together**:

```yaml
security:
  - apiKeyAuth: []
    bearerAuth: []
```

This is not two extractors. The generator produces **one** extractor for the combination: its credential type is a generated record holding one `String` per scheme, and its tag joins the scheme names
with `With`. For schemes `apiKeyAuth` and `bearerAuth` that is `@Tag(ApiSecurity.ApiKeyAuthWithBearerAuth.class)` with the credential type `ApiSecurity.ApiKeyAuthWithBearerAuthAuthData`.

In practice this style is less common for simple APIs, but it makes sense when one token identifies the user and another secret identifies the calling application.

### 7. Public Routes { #7-public-routes }

One subtle but important OpenAPI trick is an empty requirement list on a specific operation:

```yaml
security: []
```

It overrides a global security requirement and makes that endpoint public. Listing an empty object among the alternatives — `security: [{}]` — has a related effect: the request is allowed through
unauthenticated when no other alternative matches.

This is especially useful when the API is mostly protected but a few routes must stay open, such as `/auth/login`, `/auth/refresh`, or `/public/ping`.

### 8. Choosing Authorization { #8-choosing-authorization }

A simple rule of thumb:

- Use global API key security for internal integration APIs.
- Use per-route security when the API mixes public and protected endpoints.
- Use Basic auth only for simple or legacy scenarios.
- Use Bearer/JWT when users, sessions, roles, or claims matter.
- Use multiple alternative schemes when you need a transition path or different client types.
- Use combined schemes only when you truly need layered authentication.

### 9. Kora Support { #9-kora-support }

No matter which scheme you choose, the contract-first flow stays very similar:

1. describe the scheme in `components.securitySchemes`
2. attach it globally or per-route through `security`
3. regenerate the server
4. implement `HttpServerPrincipalExtractor<T, P>` tagged with the generated `ApiSecurity.*` marker
5. optionally normalize auth failures through your exception handling layer

Any scheme type other than `apiKey`, `http` `basic`/`bearer`, `oauth2`, and `openId` fails generation with an explicit message rather than producing silently unprotected routes.

That is the main takeaway: OpenAPI describes the security contract, while Kora gives you a generated integration point to enforce it at runtime.

## Configuration { #configuration }

Now configure the app to expose both OpenAPI files and the auth value.

Update `src/main/resources/application.conf`:

For the full configuration reference, see [HTTP Server](../documentation/http-server.md#configuration), [Configuration](../documentation/config.md), [OpenAPI Management](../documentation/openapi-management.md#configuration)
and [Logging SLF4J](../documentation/logging-slf4j.md).

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
      port = 8080 //(1)!
      system.port = 8085 //(2)!
      telemetry.logging.enabled = true //(3)!
    }

    auth {
      apiKey {
        value = "MySecuredApiKey" //(4)!
        value = ${?OPENAPI_HTTP_SERVER_ADVANCED_API_KEY} //(5)!
      }
    }

    openapi {
      management {
        enabled = true //(6)!
        files = [ "openapi/user-http-server.yaml", "openapi/data-http-server.yaml" ] //(7)!
        path = "/openapi" //(8)!
        swaggerui {
          enabled = true //(9)!
          path = "/swagger-ui" //(10)!
        }
      }
    }

    logging.levels {
      "root" = "WARN" //(11)!
      "io.koraframework" = "INFO" //(12)!
      "io.koraframework.guide.openapi.httpserver.advanced" = "INFO" //(13)!
    }
    ```

    1.  Public HTTP port used by application endpoints (default: `8080`).
    2.  System HTTP port used by probes, metrics, and management endpoints (default: `8085`).
    3.  Enables request logging for the public HTTP server (default: `false`).
    4.  The API key expected by `DataApiAuthConfig`, read from `auth.apiKey.value`.
    5.  Optional override from the `OPENAPI_HTTP_SERVER_ADVANCED_API_KEY` environment variable, which is how a real deployment injects the secret.
    6.  Enables OpenAPI publishing (default: `false`).
    7.  Both contracts are published from one application.
    8.  Base path for the contracts. With more than one file this becomes a prefix, see the note below.
    9.  Enables the Swagger UI page (default: `false`).
    10. Path of the Swagger UI page (default: `/swagger-ui`).
    11. Log level for the root logger.
    12. Log level for Kora framework loggers.
    13. Log level for the application package.

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      port: 8080 #(1)!
      system:
        port: 8085 #(2)!
      telemetry:
        logging:
          enabled: true #(3)!
    auth:
      apiKey:
        value: "MySecuredApiKey" #(4)!
    openapi:
      management:
        enabled: true #(5)!
        files: [ "openapi/user-http-server.yaml", "openapi/data-http-server.yaml" ] #(6)!
        path: "/openapi" #(7)!
        swaggerui:
          enabled: true #(8)!
          path: "/swagger-ui" #(9)!
    logging:
      levels:
        root: "WARN" #(10)!
        "io.koraframework": "INFO" #(11)!
        "io.koraframework.guide.openapi.httpserver.advanced": "INFO" #(12)!
    ```

    1.  Public HTTP port used by application endpoints (default: `8080`).
    2.  System HTTP port used by probes, metrics, and management endpoints (default: `8085`).
    3.  Enables request logging for the public HTTP server (default: `false`).
    4.  The API key expected by `DataApiAuthConfig`, read from `auth.apiKey.value`.
    5.  Enables OpenAPI publishing (default: `false`).
    6.  Both contracts are published from one application.
    7.  Base path for the contracts. With more than one file this becomes a prefix, see the note below.
    8.  Enables the Swagger UI page (default: `false`).
    9.  Path of the Swagger UI page (default: `/swagger-ui`).
    10. Log level for the root logger.
    11. Log level for Kora framework loggers.
    12. Log level for the application package.

!!! warning "With several files, `/openapi` becomes a prefix"

    With exactly one entry in `files`, the contract is served directly at `openapi.management.path`.
    As soon as there is more than one, the registered route becomes `path + "/{file}"`, where `{file}` is the **file name** of the resource — so the two contracts above are read from
    `GET /openapi/user-http-server.yaml` and `GET /openapi/data-http-server.yaml`, and a bare `GET /openapi` no longer matches.
    The Swagger UI page handles this on its own and offers both contracts in its selector.

This makes the whole application feel coherent: one runtime app, two contracts, one combined OpenAPI exposure, one Swagger UI.

That is often exactly how a real service grows. Different HTTP areas may be authored differently or generated with different options, but they still ship as one application.

## Check Application { #check-app }

```bash
./gradlew clean classes
./gradlew run
```

Try the form endpoint:

```bash
curl -X POST http://localhost:8080/data/form \
  -H "Authorization: MySecuredApiKey" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "name=Ivan"
```

Expected result:

```text
Hello World, Ivan
```

Try the multipart endpoint:

```bash
curl -X POST http://localhost:8080/data/upload \
  -H "Authorization: MySecuredApiKey" \
  -F "description=My test file" \
  -F "file=@README.md"
```

Expected result: JSON with `fileCount` and `fileNames`.

Try the JSON mapping endpoint:

```bash
curl -X GET http://localhost:8080/data/mapping-by-code/200 \
  -H "Authorization: MySecuredApiKey"
```

Expected result:

```json
{
  "message": "Hello from response mapper"
}
```

Try a validation failure:

```bash
curl -X GET http://localhost:8080/data/mapping-by-code/700 \
  -H "Authorization: MySecuredApiKey"
```

Expected result: `400` with `message` and `details`, produced by the custom violation mapper before the delegate is ever called, because `700` is outside the allowed `200..599` range.

Try the interceptor path:

```bash
curl -X POST http://localhost:8080/data/form \
  -H "Authorization: MySecuredApiKey" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "name=admin"
```

Expected result: `500` with an `ErrorResponseTO` body, because `RestrictedFormNameException` reaches `DataApiExceptionHandler`.

Try a request without authorization:

```bash
curl -X POST http://localhost:8080/data/form \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "name=Ivan"
```

Expected result: `403` with an `ErrorResponseTO` body.

Read the contracts:

```bash
curl http://localhost:8080/openapi/user-http-server.yaml
curl http://localhost:8080/openapi/data-http-server.yaml
```

Open:

```text
http://localhost:8080/swagger-ui
```

and verify that both the user and data routes are visible in the combined documentation.

## Testing { #testing }

Because generated delegates are ordinary components, the advanced routes are testable exactly like the CRUD ones — including the form record, which you construct directly instead of building a
multipart request.

===! ":fontawesome-brands-java: `Java`"

    Create `src/test/java/io/koraframework/guide/openapi/httpserver/advanced/OpenApiHttpServerAdvancedAppTest.java`:

    ```java
    package io.koraframework.guide.openapi.httpserver.advanced;

    import static org.junit.jupiter.api.Assertions.assertEquals;
    import static org.junit.jupiter.api.Assertions.assertInstanceOf;

    import org.junit.jupiter.api.Test;
    import io.koraframework.guide.openapi.httpserver.data.api.DataApiController;
    import io.koraframework.guide.openapi.httpserver.data.api.DataApiDelegate;
    import io.koraframework.guide.openapi.httpserver.data.api.DataApiResponses;
    import io.koraframework.test.extension.junit5.KoraAppTest;
    import io.koraframework.test.extension.junit5.TestComponent;

    @KoraAppTest(Application.class)
    class OpenApiHttpServerAdvancedAppTest {

        @TestComponent
        private DataApiDelegate dataApiDelegate;

        @Test
        void dataFormFlowWorksThroughGeneratedDelegate() throws Exception {
            var response = this.dataApiDelegate.processForm(new DataApiController.ProcessFormFormParam("Ivan")); //(1)!
            var form200 = assertInstanceOf(DataApiResponses.ProcessFormApiResponse.ProcessForm200ApiResponse.class, response);
            assertEquals("Hello World, Ivan", form200.content());
        }

        @Test
        void dataMappingByCodeReturnsPayloadFor200() throws Exception {
            var response = this.dataApiDelegate.mappingByCode(200);
            var mapping200 = assertInstanceOf(DataApiResponses.MappingByCodeApiResponse.MappingByCode200ApiResponse.class, response);
            assertEquals("Hello from response mapper", mapping200.content().message());
        }
    }
    ```

    1.  The generated form record is a normal record, so the test skips multipart encoding entirely.

=== ":simple-kotlin: `Kotlin`"

    Create `src/test/kotlin/io/koraframework/guide/openapi/httpserver/advanced/OpenApiHttpServerAdvancedAppTest.kt`:

    ```kotlin
    package io.koraframework.guide.openapi.httpserver.advanced

    import org.junit.jupiter.api.Assertions.assertEquals
    import org.junit.jupiter.api.Assertions.assertInstanceOf
    import org.junit.jupiter.api.Test
    import io.koraframework.guide.openapi.httpserver.data.api.DataApiController
    import io.koraframework.guide.openapi.httpserver.data.api.DataApiDelegate
    import io.koraframework.guide.openapi.httpserver.data.api.DataApiResponses
    import io.koraframework.test.extension.junit5.KoraAppTest
    import io.koraframework.test.extension.junit5.TestComponent

    @KoraAppTest(Application::class)
    class OpenApiHttpServerAdvancedAppTest {

        @TestComponent
        lateinit var dataApiDelegate: DataApiDelegate

        @Test
        fun dataFormFlowWorksThroughGeneratedDelegate() {
            val response = dataApiDelegate.processForm(DataApiController.ProcessFormFormParam("Ivan")) //(1)!
            val form200 =
                assertInstanceOf(DataApiResponses.ProcessFormApiResponse.ProcessForm200ApiResponse::class.java, response)
            assertEquals("Hello World, Ivan", form200.content)
        }

        @Test
        fun dataMappingByCodeReturnsPayloadFor200() {
            val response = dataApiDelegate.mappingByCode(200)
            val mapping200 = assertInstanceOf(
                DataApiResponses.MappingByCodeApiResponse.MappingByCode200ApiResponse::class.java,
                response
            )
            assertEquals("Hello from response mapper", mapping200.content.message)
        }
    }
    ```

    1.  The generated form record is a normal data class, so the test skips multipart encoding entirely.

Run:

```bash
./gradlew test
```

Note what a delegate test does **not** cover: validation, the interceptor, and the security check all live in the generated controller and its interceptor chain, so they only run over real HTTP. Use
the `curl` checks above, or a [black-box test](testing-black-box.md), when you want to assert on those.

## Best Practices { #best-practices }

- Keep an existing generated contract unchanged when adding a second, more advanced contract.
- Split contracts when endpoint groups need different generation features, and give each task its own `apiPackage` and `modelPackage`.
- Use OpenAPI `securitySchemes` as the source of truth for authorization requirements.
- Use generated-contract-specific interceptors when only one generated area needs special error handling.
- Keep validation-error mapping in `ViolationExceptionHttpServerResponseMapper` and everything else in your own interceptor, so the two never fight over the same exception.
- Keep delegate implementations small and focused on application behavior, not transport plumbing.
- Keep `@Json` on any handwritten DTO class that is serialized as JSON; generated OpenAPI `*TO` models already come with their mappers, but your own DTOs do not.

## Summary { #summary }

You extended the contract-first HTTP server from [Contract-First HTTP Server with OpenAPI](openapi-http-server.md) with a second generated API for advanced HTTP concerns:

- `user-http-server.yaml` stayed unchanged for user CRUD
- `data-http-server.yaml` introduced form, multipart, and response-mapping endpoints
- only the data generator task got a controller interceptor through `extensions`
- validation errors were reshaped into the contract's own `ErrorResponseTO`
- API-key authorization was driven from the OpenAPI security contract
- both contracts were exposed together through OpenAPI management

So the application now shows a more realistic contract-first evolution path: keep stable generated APIs intact, and add new generated surfaces with more specialized behavior only where needed.

## Key Concepts { #key-concepts }

- one application can host multiple generated OpenAPI server contracts
- different generator tasks can use different options
- `extensions` is the single generator option for attaching interceptors and extra annotations to generated code
- form and multipart bodies become generated `<Api>Controller.<Operation>FormParam` records, not JSON models
- a `nullable` and non-`required` schema field becomes a `JsonNullable` model field
- OpenAPI `securitySchemes` map to `ApiSecurity` markers and runtime `HttpServerPrincipalExtractor` components
- spec-driven validation can be enabled per contract, and its error shape is yours to define
- delegates remain the main place for transport-to-application mapping

## Troubleshooting { #troubleshooting }

**The data endpoints are missing from the graph:**

Check that:

- `openApiGenerateDataHttpServer` is registered
- its `outputDir` is added to the main source set
- compilation (`compileJava`, or every `ksp*` task in `Kotlin`) depends on the task
- `DataApiDelegateImpl` is annotated with `@Component`

**Generation fails with "Invalid OpenAPI generator option `extensions`":**

- The value must be valid JSON with the optional `*`, `tags`, and `operations` sections. The failure message shows the expected shape and the value that was provided.
- The old v1 `interceptors` option no longer exists. An unknown `configOptions` key is not rejected — it is simply ignored — so a stale `interceptors` block leaves the controller with no interceptor at all and produces no build error.

**API-key auth does not work:**

Check that:

- `data-http-server.yaml` contains `components.securitySchemes.apiKeyAuth`
- the contract declares `security: - apiKeyAuth: []` globally or per route
- the principal extractor is tagged with the marker named after the scheme, `@Tag(ApiSecurity.ApiKeyAuth.class)` — the tag comes from the scheme name in the contract, not from a positional index
- the configured value matches the `Authorization` header

**Validation does not trigger:**

Check that:

- `enableServerValidation = "true"` is set on the **data** generator task
- the constraint is really present in the OpenAPI schema for `/data/mapping-by-code/{code}`
- you are testing a value outside the allowed `200..599` range
- `ValidationModule` is connected in `Application`, otherwise the graph cannot build the validation interceptor

**Validation errors come back as plain text:**

- The default `ValidationHttpServerInterceptor` answers with a plain `400` when no `ViolationExceptionHttpServerResponseMapper` component exists. Register the mapper shown above.

**Error responses are not JSON:**

Check that:

- the generator task includes the `extensions` config with `interceptorType`
- it points at the fully qualified `DataApiExceptionHandler`
- `DataApiExceptionHandler` is annotated with `@Component`
- `ErrorResponseTO` is declared in `data-http-server.yaml`

**Swagger UI shows only one contract:**

Check `openapi.management.files` in `application.conf`. It must be a list containing both `openapi/user-http-server.yaml` and `openapi/data-http-server.yaml`, and the key is `files` — the v1 singular
`file` is not read at all.

**`GET /openapi` returns 404:**

That is expected with more than one file in `files`: the route becomes `/openapi/{file}`. Request `/openapi/data-http-server.yaml` instead.

## What's Next? { #whats-next }

- [HTTP Client](http-client.md) if you have not built a client app yet.
- [OpenAPI HTTP Client](openapi-http-client.md) after HTTP Client, to consume contract-generated APIs with typed response wrappers.
- [HTTP Client Advanced](http-client-advanced.md) after HTTP Client, to compare generated clients with handwritten advanced clients.
- [Observability](observability.md) to monitor generated controllers, validation failures, security checks, and interceptors.
- [Resilient Patterns](resilient.md) to protect clients that call these generated endpoints.

## Help { #help }

If you get stuck:

- compare with [Kora Java OpenAPI HTTP Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-openapi-http-server-advanced-app) and [Kora Kotlin OpenAPI HTTP Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-openapi-http-server-advanced-app)
- revisit [OpenAPI HTTP Server](openapi-http-server.md) for the base generated delegate model
- revisit [HTTP Server Advanced](http-server-advanced.md) for the handwritten version of similar HTTP features
- check the [OpenAPI Codegen documentation](../documentation/openapi-codegen.md)
- check the [OpenAPI Management documentation](../documentation/openapi-management.md)
