---
search:
  exclude: true
title: Contract-First HTTP Server Advanced Guide
summary: Continue the OpenAPI HTTP Server guide by adding a second generated contract for forms, multipart, response mapping, generated controller interceptors, API-key authorization, and selective server validation
tags: openapi, http-server, advanced, forms, multipart, auth, validation
---

# Advanced Contract-First HTTP Server Guide { #advanced-contract-first-http }

This guide introduces advanced contract-first HTTP server patterns with Kora and OpenAPI. It covers how multiple OpenAPI specifications can coexist in one application, how generated delegates handle
forms, multipart uploads, and typed response variants, and how shared error handling and API-key authorization fit around generated transport code. You will also see how new contracts can evolve
independently while handwritten services remain the place for application behavior.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java OpenAPI HTTP Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-openapi-http-server-advanced-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin OpenAPI HTTP Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-openapi-http-server-advanced-app).

## What You'll Build { #youll-build }

You will extend the OpenAPI HTTP server application with:

- the same user CRUD contract from [openapi-http-server.md](openapi-http-server.md)
- a second OpenAPI contract called `data-http-server.yaml`
- generated endpoints for form, multipart, and response-mapping routes
- a generated-controller interceptor for consistent JSON error responses
- simple API-key authorization for the data endpoints
- server-side validation generated only for one path parameter
- one combined `/openapi` and `/swagger-ui` exposure for both contracts

## What You'll Need { #youll-need }

- JDK 17 or later
- Gradle 7+
- A text editor or IDE
- Completed [Contract-First HTTP Server with OpenAPI](openapi-http-server.md)
- Completed [HTTP Server Advanced Guide](http-server-advanced.md)

## Prerequisites { #prerequisites }

!!! note "Required: Complete OpenAPI HTTP Server and Advanced HTTP Server Guides"

    This guide assumes you have completed **[Contract-First HTTP Server with OpenAPI](openapi-http-server.md)** and **[HTTP Server Advanced](http-server-advanced.md)**, and already understand the contract-first user CRUD flow plus the advanced HTTP concepts used by the data routes.

    If you haven't completed those guides yet, do that first, because this guide combines generated OpenAPI delegates with advanced HTTP features such as forms, multipart, shared errors, and security.

Instead, we focus on the next step: how to apply those advanced HTTP ideas in a generated, contract-first HTTP server.

## Overview { #overview }

In this guide we move in a very deliberate order:

1. keep the generated user API unchanged
2. add a second OpenAPI contract only for the advanced data routes
3. configure a second Kora generation task just for that contract
4. inspect the new generated abstractions
5. implement `DataApiDelegate`
6. enable validation only for `mappingByCode(int code)`
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

This is also why only the **data** generator task gets:

- `interceptors`
- `enableServerValidation`

The user generator stays exactly as it was in the previous guide.

## Old OpenAPI Contract { #old-contract }

The first important step is actually a non-step: do **not** rewrite the user side.

Reuse the same generator task and the same contract from [openapi-http-server.md](openapi-http-server.md).

That detail matters a lot for the story of the guide.

We are **not** replacing the previous guide. We are extending it.

So the user-side pieces stay the same:

- `user-http-server.yaml`
- `UsersApiDelegate`
- `UserApiDelegateImpl`
- the familiar `UserService` and repository flow

All new work in this guide is about the advanced data endpoints.

## New OpenAPI Contract { #new-contract }

Now we move the advanced `DataController` ideas from [http-server-advanced.md](http-server-advanced.md) into their own OpenAPI contract.

Create:

`src/main/resources/openapi/data-http-server.yaml`

??? example "OpenAPI contract"

    ```yaml title="src/main/resources/openapi/data-http-server.yaml"
    openapi: 3.0.3
    info:
        title: Advanced Data API
        description: Form and multipart endpoints generated from a dedicated OpenAPI contract
        version: 1.0.0
    tags:
        -   name: data
            description: Form and multipart operations
    security:
        -   apiKeyAuth: [ ]
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
                    -   name: code
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
    components:
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

This contract introduces several new ideas at once, so it is worth reading it slowly.

What is new compared with the base OpenAPI server guide:

- `application/x-www-form-urlencoded`
- `multipart/form-data`
- a small JSON route that returns different responses by code
- explicit `400`, `403`, and `500` error bodies
- one path parameter with an explicit numeric range

The contract now describes not only the happy-path payloads, but also:

- what structured error body clients should expect, including optional validation details
- where the generated server should apply validation

That is a major advantage of contract-first design. More behavior becomes explicit before we even write the delegate.

## OpenAPI Generation { #openapi-generation }

Now configure a second generation task.

This is the most important build step in the whole guide, because this is where we intentionally treat the data API differently from the user API.

===! ":fontawesome-brands-java: `Java`"

    ```groovy title="build.gradle"
    def openApiGenerateDataHttpServer = tasks.register("openApiGenerateDataHttpServer", GenerateTask) {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/data-http-server.yaml"
        outputDir = "$buildDir/generated/data-http-server"
        def corePackage = "ru.tinkoff.kora.guide.openapi.httpserver.data"
        apiPackage = "${corePackage}.api"
        modelPackage = "${corePackage}.model"
        invokerPackage = "${corePackage}.invoker"
        configOptions = [
                mode: "java-server",
        ]
    }

    sourceSets.main {
        java.srcDirs += openApiGenerateUsersHttpServer.get().outputDir
        java.srcDirs += openApiGenerateDataHttpServer.get().outputDir
    }

    compileJava.dependsOn openApiGenerateUsersHttpServer
    compileJava.dependsOn openApiGenerateDataHttpServer
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="build.gradle.kts"
    val openApiGenerateDataHttpServer = tasks.register<GenerateTask>("openApiGenerateDataHttpServer") {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/data-http-server.yaml"
        outputDir = "$buildDir/generated/data-http-server"
        val corePackage = "ru.tinkoff.kora.guide.openapi.httpserver.data"
        apiPackage = "$corePackage.api"
        modelPackage = "$corePackage.model"
        invokerPackage = "$corePackage.invoker"
        configOptions = mapOf(
            "mode" to "java-server"
        )
    }

    sourceSets.main {
        java.srcDir(openApiGenerateUsersHttpServer.get().outputDir)
        java.srcDir(openApiGenerateDataHttpServer.get().outputDir)
    }

    tasks.compileJava {
        dependsOn(openApiGenerateUsersHttpServer)
        dependsOn(openApiGenerateDataHttpServer)
    }
    ```

Why this split is so useful:

- `openApiGenerateUsersHttpServer` stays simple and unchanged
- `openApiGenerateDataHttpServer` gets the advanced behavior

And at this early stage, we intentionally keep the generator configuration minimal.

At this point we are intentionally **not** configuring:

- server-side validation
- custom generated-controller interceptors

First we implement the delegate, then turn on validation, and only after that introduce `DataApiExceptionHandler`. This keeps the guide aligned with the order in which those classes actually appear.

This is exactly the kind of feature separation that a second contract justifies.

## Generated Classes { #generated-classes }

Run:

```bash
./gradlew clean classes
```

Now inspect the generated files:

===! ":fontawesome-brands-java: `Java`"

    - `build/generated/data-http-server/ru/tinkoff/kora/guide/openapi/httpserver/data/api/DataApiDelegate.java`
    - `build/generated/data-http-server/ru/tinkoff/kora/guide/openapi/httpserver/data/api/DataApiController.java`
    - `build/generated/data-http-server/ru/tinkoff/kora/guide/openapi/httpserver/data/api/DataApiResponses.java`
    - `build/generated/data-http-server/ru/tinkoff/kora/guide/openapi/httpserver/data/api/ApiSecurity.java`
    - `build/generated/data-http-server/ru/tinkoff/kora/guide/openapi/httpserver/data/model/UploadResponseTO.java`
    - `build/generated/data-http-server/ru/tinkoff/kora/guide/openapi/httpserver/data/model/PayloadTO.java`
    - `build/generated/data-http-server/ru/tinkoff/kora/guide/openapi/httpserver/data/model/ErrorResponseTO.java`

=== ":simple-kotlin: `Kotlin`"

    - `build/generated/data-http-server/ru/tinkoff/kora/guide/openapi/httpserver/data/api/DataApiDelegate.kt`
    - `build/generated/data-http-server/ru/tinkoff/kora/guide/openapi/httpserver/data/api/DataApiController.kt`
    - `build/generated/data-http-server/ru/tinkoff/kora/guide/openapi/httpserver/data/api/DataApiResponses.kt`
    - `build/generated/data-http-server/ru/tinkoff/kora/guide/openapi/httpserver/data/api/ApiSecurity.kt`
    - `build/generated/data-http-server/ru/tinkoff/kora/guide/openapi/httpserver/data/model/UploadResponseTO.kt`
    - `build/generated/data-http-server/ru/tinkoff/kora/guide/openapi/httpserver/data/model/PayloadTO.kt`
    - `build/generated/data-http-server/ru/tinkoff/kora/guide/openapi/httpserver/data/model/ErrorResponseTO.kt`

The most interesting generated abstractions here are:

- `DataApiDelegate`
- `DataApiController`
- `DataApiResponses`
- `ApiSecurity`

`DataApiDelegate`:

This is the contract you implement.

It plays exactly the same architectural role as `UsersApiDelegate`, but for the new advanced endpoints.

`DataApiController`:

This is the generated transport layer.

Because the contract includes:

- form-url-encoded input
- multipart input
- explicit transport status modeling

the generated controller now does more than in the simpler CRUD case.

`DataApiResponses`:

These wrappers model the allowed HTTP outcomes from the spec:

- `200`
- `400`
- `403`
- `500`

That means error handling is now part of the transport contract, not just something we improvise in code.

For `mappingByCode`, the generated response family also gives us a clean place to separate:

- the successful JSON payload
- the error JSON body

`ApiSecurity`:

This is generated from the OpenAPI `securitySchemes` section.

It is the bridge between the OpenAPI security contract and the principal extractor you will register in `Application`.

This is one of the most valuable ideas in the guide:

- security is declared in the contract
- the generator produces the marker types
- your app plugs in the actual runtime check

## Delegate { #delegate }

Now connect the generated data transport layer to application logic.

Create:

`src/main/java/ru/tinkoff/kora/guide/openapi/httpserver/advanced/controller/DataApiDelegateImpl.java`

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/openapi/httpserver/advanced/controller/DataApiDelegateImpl.java"
    package ru.tinkoff.kora.guide.openapi.httpserver.advanced.controller;

    import java.util.List;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.openapi.httpserver.data.api.DataApiController;
    import ru.tinkoff.kora.guide.openapi.httpserver.data.api.DataApiDelegate;
    import ru.tinkoff.kora.guide.openapi.httpserver.data.api.DataApiResponses;
    import ru.tinkoff.kora.guide.openapi.httpserver.data.model.PayloadTO;
    import ru.tinkoff.kora.guide.openapi.httpserver.data.model.UploadResponseTO;
    import ru.tinkoff.kora.http.server.common.HttpServerResponseException;

    @Component
    public final class DataApiDelegateImpl implements DataApiDelegate {

        @Override
        public DataApiResponses.ProcessFormApiResponse processForm(DataApiController.ProcessFormFormParam form) {
            return new DataApiResponses.ProcessFormApiResponse.ProcessForm200ApiResponse("Hello World, " + form.name());
        }

        @Override
        public DataApiResponses.ProcessUploadApiResponse processUpload(DataApiController.ProcessUploadFormParam form) {
            var response = new UploadResponseTO(
                    1,
                    List.of(form.file().name())
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
            throw HttpServerResponseException.of(code, "Request failed with code " + code);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/openapi/httpserver/advanced/controller/DataApiDelegateImpl.kt"
    package ru.tinkoff.kora.guide.openapi.httpserver.advanced.controller

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.openapi.httpserver.data.api.DataApiController
    import ru.tinkoff.kora.guide.openapi.httpserver.data.api.DataApiDelegate
    import ru.tinkoff.kora.guide.openapi.httpserver.data.api.DataApiResponses
    import ru.tinkoff.kora.guide.openapi.httpserver.data.model.PayloadTO
    import ru.tinkoff.kora.guide.openapi.httpserver.data.model.UploadResponseTO
    import ru.tinkoff.kora.http.server.common.HttpServerResponseException

    @Component
    class DataApiDelegateImpl : DataApiDelegate {

        override fun processForm(form: DataApiController.ProcessFormFormParam): DataApiResponses.ProcessFormApiResponse {
            return DataApiResponses.ProcessFormApiResponse.ProcessForm200ApiResponse("Hello World, ${form.name()}")
        }

        override fun processUpload(form: DataApiController.ProcessUploadFormParam): DataApiResponses.ProcessUploadApiResponse {
            val response = UploadResponseTO(1, listOf(form.file().name()))
            return DataApiResponses.ProcessUploadApiResponse.ProcessUpload200ApiResponse(response)
        }

        override fun mappingByCode(code: Int): DataApiResponses.MappingByCodeApiResponse {
            if (code == 200) {
                return DataApiResponses.MappingByCodeApiResponse.MappingByCode200ApiResponse(
                    PayloadTO("Hello from response mapper")
                )
            }
            throw HttpServerResponseException.of(code, "Request failed with code $code")
        }
    }
    ```

There are two nice things to notice here.

First, the delegate stays very small.

That is because the generated layer already handled a lot:

- request decoding
- transport typing
- security contract integration
- validation hooks

Second, the logic intentionally mirrors the manual `DataController` from [http-server-advanced.md](http-server-advanced.md).

That is important for teaching consistency. The guide is not inventing a different behavior. It is showing how the same behavior looks when the transport layer is generated from OpenAPI instead of
handwritten.

The new `mappingByCode()` route is especially useful because it gives us one compact JSON endpoint for:

- generated response wrappers
- generated error mapping
- one focused validation example

## Server Validation { #server-validation }

The full server OpenAPI validation rules and operation selection options are covered in [OpenAPI Codegen validation](../documentation/openapi-codegen.md#validation).

Now update the data generator task and turn on validation explicitly:

===! ":fontawesome-brands-java: `Java`"

    ```groovy title="build.gradle"
    def openApiGenerateDataHttpServer = tasks.register("openApiGenerateDataHttpServer", GenerateTask) {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/data-http-server.yaml"
        outputDir = "$buildDir/generated/data-http-server"
        def corePackage = "ru.tinkoff.kora.guide.openapi.httpserver.data"
        apiPackage = "${corePackage}.api"
        modelPackage = "${corePackage}.model"
        invokerPackage = "${corePackage}.invoker"
        configOptions = [
                mode                  : "java-server",
                enableServerValidation: "true",
        ]
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="build.gradle.kts"
    val openApiGenerateDataHttpServer = tasks.register<GenerateTask>("openApiGenerateDataHttpServer") {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/data-http-server.yaml"
        outputDir = "$buildDir/generated/data-http-server"
        val corePackage = "ru.tinkoff.kora.guide.openapi.httpserver.data"
        apiPackage = "$corePackage.api"
        modelPackage = "$corePackage.model"
        invokerPackage = "$corePackage.invoker"
        configOptions = mapOf(
            "mode" to "java-server",
            "enableServerValidation" to "true"
        )
    }
    ```

Because `enableServerValidation` is enabled only on `openApiGenerateDataHttpServer`, validation behavior changes only for the generated data endpoints.

In this guide, we intentionally keep that validation surface very small.

Only one parameter is constrained:

- `code` in `/data/mapping-by-code/{code}`

And its allowed range is:

- minimum `200`
- maximum `599`

This is useful for two reasons.

First, it demonstrates spec-driven validation clearly on one focused example.

Second, it avoids turning the whole advanced contract into a validation tutorial. The form and multipart steps stay focused on transport formats, while the validation step stays focused on one path
parameter.

To make those validation failures return the same JSON contract as the rest of the data API, register a custom `ViolationExceptionHttpServerResponseMapper`.

`ValidationModule` already provides `ValidationHttpServerInterceptor`, and the generated server uses it automatically because `enableServerValidation` is enabled. Our only customization here is the
mapper that turns `ViolationException` into `ErrorResponseTO`.

That is also why `ErrorResponseTO` has two layers now:

- `message` for the top-level problem summary
- `details` for field- or parameter-level validation messages when they exist

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/openapi/httpserver/advanced/Application.java"
    package ru.tinkoff.kora.guide.openapi.httpserver.advanced;

    import ru.tinkoff.kora.guide.openapi.httpserver.data.model.ErrorResponseTO;
    import ru.tinkoff.kora.http.common.body.HttpBody;
    import ru.tinkoff.kora.http.server.common.HttpServerResponse;
    import ru.tinkoff.kora.json.common.JsonWriter;
    import ru.tinkoff.kora.validation.module.http.server.ViolationExceptionHttpServerResponseMapper;

    default ViolationExceptionHttpServerResponseMapper customViolationExceptionHttpServerResponseMapper(
            JsonWriter<ErrorResponseTO> errorResponseJsonWriter) {
        return (request, exception) -> {
            var details = exception.getViolations().stream()
                    .map(v -> "Path " + v.path() + " violated: " + v.message())
                    .toList();

            var response = new ErrorResponseTO(
                    "Encountered '%s' validation violations".formatted(exception.getViolations().size()),
                    details
            );
            return HttpServerResponse.of(
                    400,
                    HttpBody.json(errorResponseJsonWriter.toByteArrayUnchecked(response)));
        };
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/openapi/httpserver/advanced/Application.kt"
    import ru.tinkoff.kora.guide.openapi.httpserver.data.model.ErrorResponseTO
    import ru.tinkoff.kora.http.common.body.HttpBody
    import ru.tinkoff.kora.http.server.common.HttpServerResponse
    import ru.tinkoff.kora.json.common.JsonWriter
    import ru.tinkoff.kora.validation.module.http.server.ViolationExceptionHttpServerResponseMapper

    fun customViolationExceptionHttpServerResponseMapper(
        errorResponseJsonWriter: JsonWriter<ErrorResponseTO>
    ): ViolationExceptionHttpServerResponseMapper {
        return ViolationExceptionHttpServerResponseMapper { _, exception ->
            val details = exception.violations
                .map { violation -> "Path ${violation.path()} violated: ${violation.message()}" }

            val response = ErrorResponseTO(
                "Encountered '${exception.violations.size}' validation violations",
                details
            )
            HttpServerResponse.of(
                400,
                HttpBody.json(errorResponseJsonWriter.toByteArrayUnchecked(response))
            )
        }
    }
    ```

This is another example of why splitting the contracts was a good design choice.

The same `Application` can host:

- one generated server without spec-driven validation
- another generated server with spec-driven validation

And because the constraint lives in the OpenAPI schema, the generated transport layer can reject out-of-range values before your delegate decides how to respond.

## Error Interceptor { #error-interceptor }

Generated server controller interceptors are described in more detail in [OpenAPI Codegen: server interceptors](../documentation/openapi-codegen.md#interceptors-2).

Now that validation failures already become structured JSON, we can add one more layer for the **other** kinds of transport errors we want to normalize.

In the manual advanced server guide, we used a global `ExceptionHandler`.

Here we do something a little different on purpose.

For the generated **data** controller, we attach a contract-specific interceptor through OpenAPI generator configuration.

Create:

`src/main/java/ru/tinkoff/kora/guide/openapi/httpserver/advanced/controller/DataApiExceptionHandler.java`

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/openapi/httpserver/advanced/controller/DataApiExceptionHandler.java"
    package ru.tinkoff.kora.guide.openapi.httpserver.advanced.controller;

    import java.util.concurrent.CompletionException;
    import java.util.concurrent.CompletionStage;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.Context;
    import ru.tinkoff.kora.guide.openapi.httpserver.data.model.ErrorResponseTO;
    import ru.tinkoff.kora.http.common.body.HttpBody;
    import ru.tinkoff.kora.http.server.common.HttpServerInterceptor;
    import ru.tinkoff.kora.http.server.common.HttpServerRequest;
    import ru.tinkoff.kora.http.server.common.HttpServerResponse;
    import ru.tinkoff.kora.http.server.common.HttpServerResponseException;
    import ru.tinkoff.kora.json.common.JsonWriter;
    import ru.tinkoff.kora.validation.common.ViolationException;

    @Component
    public final class DataApiExceptionHandler implements HttpServerInterceptor {

        private final JsonWriter<ErrorResponseTO> errorJsonWriter;

        public DataApiExceptionHandler(JsonWriter<ErrorResponseTO> errorJsonWriter) {
            this.errorJsonWriter = errorJsonWriter;
        }

        @Override
        public CompletionStage<HttpServerResponse> intercept(Context context, HttpServerRequest request, InterceptChain chain)
                throws Exception {
            return chain.process(context, request).exceptionally(throwable -> {
                var cause = unwrap(throwable);
                if (cause instanceof ViolationException violationException) {
                    throw new CompletionException(violationException);
                }
                if (cause instanceof HttpServerResponseException responseException) {
                    return jsonResponse(responseException.code(), responseException.getMessage());
                }
                if (cause instanceof IllegalArgumentException) {
                    return jsonResponse(400, "Invalid request parameters");
                }
                if (cause instanceof SecurityException) {
                    return jsonResponse(403, cause.getMessage() != null ? cause.getMessage() : "Access denied");
                }
                return jsonResponse(500, "An unexpected error occurred");
            });
        }

        private HttpServerResponse jsonResponse(int statusCode, String message) {
            return HttpServerResponse.of(
                statusCode,
                HttpBody.json(this.errorJsonWriter.toByteArrayUnchecked(new ErrorResponseTO(message, null)))
            );
        }

        private static Throwable unwrap(Throwable throwable) {
            var current = throwable;
            while (current instanceof CompletionException && current.getCause() != null) {
                current = current.getCause();
            }
            return current;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/openapi/httpserver/advanced/controller/DataApiExceptionHandler.kt"
    package ru.tinkoff.kora.guide.openapi.httpserver.advanced.controller

    import java.util.concurrent.CompletionException
    import java.util.concurrent.CompletionStage
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.Context
    import ru.tinkoff.kora.guide.openapi.httpserver.data.model.ErrorResponseTO
    import ru.tinkoff.kora.http.common.body.HttpBody
    import ru.tinkoff.kora.http.server.common.HttpServerInterceptor
    import ru.tinkoff.kora.http.server.common.HttpServerRequest
    import ru.tinkoff.kora.http.server.common.HttpServerResponse
    import ru.tinkoff.kora.http.server.common.HttpServerResponseException
    import ru.tinkoff.kora.json.common.JsonWriter
    import ru.tinkoff.kora.validation.common.ViolationException

    @Component
    class DataApiExceptionHandler(
        private val errorJsonWriter: JsonWriter<ErrorResponseTO>
    ) : HttpServerInterceptor {

        override fun intercept(
            context: Context,
            request: HttpServerRequest,
            chain: HttpServerInterceptor.InterceptChain
        ): CompletionStage<HttpServerResponse> {
            return chain.process(context, request).exceptionally { throwable ->
                val cause = unwrap(throwable)
                when (cause) {
                    is ViolationException -> throw CompletionException(cause)
                    is HttpServerResponseException -> jsonResponse(cause.code(), cause.message ?: "HTTP error")
                    is IllegalArgumentException -> jsonResponse(400, "Invalid request parameters")
                    is SecurityException -> jsonResponse(403, cause.message ?: "Access denied")
                    else -> jsonResponse(500, "An unexpected error occurred")
                }
            }
        }

        private fun jsonResponse(statusCode: Int, message: String): HttpServerResponse {
            return HttpServerResponse.of(
                statusCode,
                HttpBody.json(errorJsonWriter.toByteArrayUnchecked(ErrorResponseTO(message, null)))
            )
        }

        private fun unwrap(throwable: Throwable): Throwable {
            var current = throwable
            while (current is CompletionException && current.cause != null) {
                current = current.cause!!
            }
            return current
        }
    }
    ```

The key difference from the manual guide is scope:

- in [http-server-advanced.md](http-server-advanced.md), the interceptor was global
- here, it is attached only to the **generated data API**

That is a subtle but powerful pattern.

Generated transports do not all have to share the same cross-cutting behavior. You can apply different interceptor strategies to different generated contracts.

The important detail is the `ViolationException` branch.

We deliberately **do not** convert validation failures here, because we already decided that validation errors belong to `customViolationExceptionHttpServerResponseMapper`
and `ValidationHttpServerInterceptor`.

So the responsibilities are now split cleanly:

- `ValidationHttpServerInterceptor` handles generated validation failures and returns `ErrorResponseTO(message, details)`
- `DataApiExceptionHandler` handles the rest of the transport-level failures we want to normalize

Only after `DataApiExceptionHandler` exists does it make sense to attach it in the generator configuration.

Update the data generator task:

===! ":fontawesome-brands-java: `Java`"

    ```groovy title="build.gradle"
    def openApiGenerateDataHttpServer = tasks.register("openApiGenerateDataHttpServer", GenerateTask) {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/data-http-server.yaml"
        outputDir = "$buildDir/generated/data-http-server"
        def corePackage = "ru.tinkoff.kora.guide.openapi.httpserver.data"
        apiPackage = "${corePackage}.api"
        modelPackage = "${corePackage}.model"
        invokerPackage = "${corePackage}.invoker"
        configOptions = [
                mode                  : "java-server",
                enableServerValidation: "true",
                interceptors          : """
                        {
                          "*": [
                            {
                              "type": "ru.tinkoff.kora.guide.openapi.httpserver.advanced.controller.DataApiExceptionHandler"
                            }
                          ]
                        }
                        """,
        ]
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="build.gradle.kts"
    val openApiGenerateDataHttpServer = tasks.register<GenerateTask>("openApiGenerateDataHttpServer") {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/data-http-server.yaml"
        outputDir = "$buildDir/generated/data-http-server"
        val corePackage = "ru.tinkoff.kora.guide.openapi.httpserver.data"
        apiPackage = "$corePackage.api"
        modelPackage = "$corePackage.model"
        invokerPackage = "$corePackage.invoker"
        configOptions = mapOf(
            "mode" to "java-server",
            "enableServerValidation" to "true",
            "interceptors" to """
                {
                  "*": [
                    {
                      "type": "ru.tinkoff.kora.guide.openapi.httpserver.advanced.controller.DataApiExceptionHandler"
                    }
                  ]
                }
            """.trimIndent()
        )
    }
    ```

## API Key Authorization { #api-key }

The mapping from OpenAPI security schemes to Kora components is described in [OpenAPI Codegen authorization](../documentation/openapi-codegen.md#authorization).

Until this point, the data contract was focused only on payloads, status codes, and validation.

Now we extend that contract with explicit API-key authentication.

Because every route in this contract should require the same API key, add the security requirement once at the top level of the OpenAPI file:

```yaml
security:
    -   apiKeyAuth: [ ]
```

And declare the shared security scheme under `components`:

```yaml
components:
    securitySchemes:
        apiKeyAuth:
            type: apiKey
            in: header
            name: Authorization
```

After this change, `data-http-server.yaml` should define global security once and then declare the scheme itself:

```yaml
security:
    -   apiKeyAuth: [ ]

components:
    securitySchemes:
        apiKeyAuth:
            type: apiKey
            in: header
            name: Authorization
```

That means this step is the first moment when the data contract starts describing who is allowed to call those routes, not just what payloads they exchange. And because the requirement is global, you
do not have to repeat it on every individual operation.

Now we plug in the runtime behavior for that generated security contract.

Create the config contract:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/openapi/httpserver/advanced/controller/DataApiAuthConfig.java"
    package ru.tinkoff.kora.guide.openapi.httpserver.advanced.controller;

    import ru.tinkoff.kora.config.common.annotation.ConfigSource;

    @ConfigSource("auth.apiKey")
    public interface DataApiAuthConfig {
        String value();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/openapi/httpserver/advanced/controller/DataApiAuthConfig.kt"
    package ru.tinkoff.kora.guide.openapi.httpserver.advanced.controller

    import ru.tinkoff.kora.config.common.annotation.ConfigSource

    @ConfigSource("auth.apiKey")
    interface DataApiAuthConfig {
        fun value(): String
    }
    ```

And wire the generated security marker in `Application`:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/openapi/httpserver/advanced/Application.java"
    package ru.tinkoff.kora.guide.openapi.httpserver.advanced;

    import java.util.concurrent.CompletableFuture;
    import ru.tinkoff.kora.common.Principal;
    import ru.tinkoff.kora.common.Tag;
    import ru.tinkoff.kora.guide.openapi.httpserver.advanced.controller.DataApiAuthConfig;
    import ru.tinkoff.kora.guide.openapi.httpserver.advanced.controller.DataApiPrincipal;
    import ru.tinkoff.kora.guide.openapi.httpserver.data.api.ApiSecurity;
    import ru.tinkoff.kora.http.server.common.auth.HttpServerPrincipalExtractor;

    @Tag(ApiSecurity.ApiKeyAuth.class)
    default HttpServerPrincipalExtractor<Principal> apiKeyHttpServerPrincipalExtractor(DataApiAuthConfig config) {
        return (request, value) -> {
            if (value == null || !config.value().equals(value)) {
                throw new SecurityException("Invalid API key");
            }
            return CompletableFuture.completedFuture(new DataApiPrincipal("data-api-client"));
        };
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/openapi/httpserver/advanced/Application.kt"
    import java.util.concurrent.CompletableFuture
    import ru.tinkoff.kora.common.Principal
    import ru.tinkoff.kora.common.Tag
    import ru.tinkoff.kora.guide.openapi.httpserver.advanced.controller.DataApiAuthConfig
    import ru.tinkoff.kora.guide.openapi.httpserver.advanced.controller.DataApiPrincipal
    import ru.tinkoff.kora.guide.openapi.httpserver.data.api.ApiSecurity
    import ru.tinkoff.kora.http.server.common.auth.HttpServerPrincipalExtractor

    @Tag(ApiSecurity.ApiKeyAuth::class)
    fun apiKeyHttpServerPrincipalExtractor(config: DataApiAuthConfig): HttpServerPrincipalExtractor<Principal> {
        return HttpServerPrincipalExtractor { _, value ->
            if (value == null || config.value() != value) {
                throw SecurityException("Invalid API key")
            }
            CompletableFuture.completedFuture(DataApiPrincipal("data-api-client"))
        }
    }
    ```

This is one of the nicest contract-first patterns in the guide.

The OpenAPI file says:

- this route group requires API key auth

The generator says:

- here is the security abstraction for that requirement

Your application says:

- here is how that API key is actually validated at runtime

That is a very clean separation between:

- contract
- generated integration point
- runtime policy

## Authorization Options { #authorization-options }

The example in this guide uses the simplest possible option:

- one API key
- one global security requirement
- one `HttpServerPrincipalExtractor`

That is a great starting point. But OpenAPI security can model several different shapes, and it helps to know how they differ before you choose one for a real service.

This section is intentionally theoretical. It does not change the runnable application from this guide. Instead, it shows common patterns you can describe in OpenAPI and then connect to Kora runtime
extractors.

### 1. Global API Key { #1-global-api-key }

This is the pattern we use in this guide.

It works well when:

- the whole API belongs to one protected integration surface
- every route should require the same secret
- you want the smallest possible amount of security wiring

Example:

```yaml
security:
    -   apiKeyAuth: [ ]

components:
    securitySchemes:
        apiKeyAuth:
            type: apiKey
            in: header
            name: Authorization
```

And in Kora, that usually means one extractor tagged with the generated security marker:

```java

@Tag(ApiSecurity.ApiKeyAuth.class)
default HttpServerPrincipalExtractor<Principal> apiKeyHttpServerPrincipalExtractor(MyAuthConfig config) {
    return (request, value) -> {
        if (value == null || !config.value().equals(value)) {
            throw new SecurityException("Invalid API key");
        }
        return CompletableFuture.completedFuture(new MyPrincipal("integration-client"));
    };
}
```

This approach is simple and practical for:

- internal service-to-service calls
- admin endpoints behind infrastructure controls
- technical APIs consumed by a small number of trusted clients

### 2. Route Protection { #2-route-protection }

Sometimes not every route should be protected the same way.

For example:

- public health or login endpoints may stay open
- some routes may require auth while others stay public
- one section of the API may use a different scheme

In that case, you can omit global `security` and describe it directly on operations:

```yaml
paths:
    /public/ping:
        get:
            security: [ ]
            responses:
                '200':
                    description: OK

    /users:
        get:
            security:
                -   apiKeyAuth: [ ]
            responses:
                '200':
                    description: Protected
```

This is useful when the API surface is mixed:

- part public
- part protected
- part protected by different schemes

### 3. Basic Authentication { #3-basic-authentication }

Basic auth is another common option described in the security section of [OpenAPI Codegen](../documentation/openapi-codegen.md).

Example:

```yaml
components:
    securitySchemes:
        basicAuth:
            type: http
            scheme: basic

security:
    -   basicAuth: [ ]
```

And the Kora side usually looks like:

```java

@Tag(ApiSecurity.BasicAuth.class)
default HttpServerPrincipalExtractor<Principal> basicHttpServerPrincipalExtractor() {
    return (request, credentials) -> {
        if (credentials == null) {
            throw new SecurityException("Missing credentials");
        }
        var parts = credentials.split(":", 2);
        if (parts.length != 2) {
            throw new SecurityException("Invalid basic auth format");
        }
        return CompletableFuture.completedFuture(new MyPrincipal(parts[0]));
    };
}
```

Basic auth can be acceptable for:

- simple internal tools
- demos
- legacy integrations

But it should usually be used only over HTTPS, and in many modern systems Bearer/JWT is the more flexible choice.

### 4. Bearer Tokens and JWT { #4-bearer-tokens-jwt }

If your API is meant for browsers, mobile clients, or user-facing sessions, Bearer auth is often a better fit than API keys.

Example:

```yaml
components:
    securitySchemes:
        bearerAuth:
            type: http
            scheme: bearer
            bearerFormat: JWT

security:
    -   bearerAuth: [ ]
```

In Kora, the extractor is tagged with the generated bearer marker:

```java

@Tag(ApiSecurity.BearerAuth.class)
default HttpServerPrincipalExtractor<Principal> bearerHttpServerPrincipalExtractor(JwtService jwtService) {
    return (request, token) -> {
        if (token == null || token.isBlank()) {
            throw new SecurityException("Missing bearer token");
        }
        var user = jwtService.extractUserFromToken(token);
        return CompletableFuture.completedFuture(new UserPrincipal(user));
    };
}
```

This works well when:

- the caller is an end user, not just another service
- you want token expiration
- you need claims, roles, or tenant information inside the token
- you want login and refresh-token flows

For a deeper reference on that style, see the security and authorization options in [OpenAPI Codegen](../documentation/openapi-codegen.md).

### 5. Multiple Schemes { #5-multiple-schemes }

OpenAPI can describe cases where a route accepts one scheme **or** another.

This is written as multiple objects inside the `security` array.

Example:

```yaml
security:
    -   apiKeyAuth: [ ]
    -   basicAuth: [ ]
```

This means:

- the caller may authenticate with `apiKeyAuth`
- or with `basicAuth`

This is useful for migration periods and mixed clients:

- machine clients can use API keys
- operator tools can use basic auth

On the Kora side, you provide extractors for both generated security markers, and the generated server chooses the scheme that matches the request.

### 6. Combined Schemes { #6-combined-schemes }

OpenAPI also supports combined requirements.

Inside one security object, multiple schemes are interpreted together.

Example:

```yaml
security:
    -   apiKeyAuth: [ ]
        bearerAuth: [ ]
```

Conceptually, this means the route expects both requirements together.

In practice, this style is less common for simple APIs, but it can make sense when:

- one token identifies the user
- another secret identifies the calling application
- infrastructure requires layered trust checks

This pattern is more advanced, and it should be used only when the extra complexity is really justified.

### 7. Public Routes { #7-public-routes }

One subtle but important OpenAPI trick is:

```yaml
security: [ ]
```

When used on a specific operation, it can override a global security requirement and make that endpoint public.

This is especially useful when the API is mostly protected, but a few routes must stay open, for example:

- `/auth/login`
- `/auth/refresh`
- `/public/ping`
- `/public/openapi-download`

That gives you a good default without forcing repetitive security declarations everywhere.

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
4. implement `HttpServerPrincipalExtractor<Principal>` tagged with the generated `ApiSecurity.*` marker
5. optionally normalize auth failures through your exception handling layer

That is the main takeaway: OpenAPI describes the security contract, while Kora gives you a generated integration point to enforce it at runtime.

## Configuration { #configuration }

Now configure the app to expose both OpenAPI files and the auth value.

Update `src/main/resources/application.conf`:

For the full configuration reference, see [HTTP Server](../documentation/http-server.md), [Configuration](../documentation/config.md), [OpenAPI Management](../documentation/openapi-management.md)
and [Logging SLF4J](../documentation/logging-slf4j.md).

===! ":material-code-json: `Hocon`"

    ```javascript title="src/main/resources/application.conf"
    httpServer {
      publicApiHttpPort = 8080 //(1)!
      privateApiHttpPort = 8085 //(2)!
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
        file = [ "openapi/user-http-server.yaml", "openapi/data-http-server.yaml" ] //(6)!
        enabled = true //(7)!
        endpoint = "/openapi" //(8)!
        swaggerui {
          enabled = true //(9)!
          endpoint = "/swagger-ui" //(10)!
        }
      }
    }

    logging.level {
      "root" = "WARN" //(11)!
      "ru.tinkoff.kora" = "INFO" //(12)!
      "ru.tinkoff.kora.guide.openapi.httpserver.advanced" = "INFO" //(13)!
    }
    ```

    1. Default public HTTP port used by application endpoints.
    2. Default private HTTP port used by probes, metrics, and management endpoints.
    3. Enables the feature for this configuration section.
    4. Configured value consumed by the guide component.
    5. Configured value consumed by the guide component. Optional override from `OPENAPI_HTTP_SERVER_ADVANCED_API_KEY`.
    6. Value for `openapi.management.file`.
    7. Enables the feature for this configuration section.
    8. Telemetry exporter endpoint.
    9. Enables the feature for this configuration section.
    10. Telemetry exporter endpoint.
    11. Value for `logging.level.root`.
    12. Value for `logging.level.ru.tinkoff.kora`.
    13. Value for `logging.level.ru.tinkoff.kora.guide.openapi.httpserver.advanced`.

=== ":simple-yaml: `YAML`"

    ```yaml title="src/main/resources/application.yaml"
    httpServer:
      publicApiHttpPort: 8080 #(1)!
      privateApiHttpPort: 8085 #(2)!
      telemetry:
        logging:
          enabled: true #(3)!
    auth:
      apiKey:
        value: ${?OPENAPI_HTTP_SERVER_ADVANCED_API_KEY:"MySecuredApiKey"} #(4)!
    openapi:
      management:
        file: [ "openapi/user-http-server.yaml", "openapi/data-http-server.yaml" ] #(5)!
        enabled: true #(6)!
        endpoint: "/openapi" #(7)!
        swaggerui:
          enabled: true #(8)!
          endpoint: "/swagger-ui" #(9)!
    logging:
      level:
        root: "WARN" #(10)!
        "ru.tinkoff.kora": "INFO" #(11)!
        "ru.tinkoff.kora.guide.openapi.httpserver.advanced": "INFO" #(12)!
    ```

    1. Default public HTTP port used by application endpoints.
    2. Default private HTTP port used by probes, metrics, and management endpoints.
    3. Enables the feature for this configuration section.
    4. Configured value consumed by the guide component. Uses the shown default and allows `OPENAPI_HTTP_SERVER_ADVANCED_API_KEY` to override it.
    5. Value for `openapi.management.file`.
    6. Enables the feature for this configuration section.
    7. Telemetry exporter endpoint.
    8. Enables the feature for this configuration section.
    9. Telemetry exporter endpoint.
    10. Value for `logging.level.root`.
    11. Value for `logging.level.ru.tinkoff.kora`.
    12. Value for `logging.level.ru.tinkoff.kora.guide.openapi.httpserver.advanced`.

This makes the whole application feel coherent:

- one runtime app
- two contracts
- one combined OpenAPI exposure
- one Swagger UI

That is often exactly how a real service grows. Different HTTP areas may be authored differently or generated with different options, but they still ship as one application.

## Check Application { #check-app }

Build:

```bash
./gradlew :guides-apps:guide-openapi-http-server-advanced-app:clean :guides-apps:guide-openapi-http-server-advanced-app:classes
```

Run:

```bash
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

Expected result: a `400` error before the delegate accepts the value, because `700` is outside the allowed `200..599` range.

Try a request without authorization:

```bash
curl -X POST http://localhost:8080/data/form \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "name=Ivan"
```

Expected result: `403` with generated `ErrorResponseTO`.

Open:

```text
http://localhost:8080/swagger-ui
```

and verify that both the user and data routes are visible in the combined documentation.

## Testing { #testing }

Run:

```bash
./gradlew test
```

The runnable app tests verify two key flows:

- the existing generated user CRUD delegate still works
- the new generated data delegates work too, including `mappingByCode(200)`

That matches the teaching goal of the guide:

- preserve the previous OpenAPI user flow
- add advanced generated data behavior incrementally

## Best Practices { #best-practices }

- Keep an existing generated contract unchanged when adding a second, more advanced contract.
- Split contracts when endpoint groups need different generation features.
- Use OpenAPI `securitySchemes` as the source of truth for authorization requirements.
- Use generated-contract-specific interceptors when only one generated area needs special error handling.
- Introduce spec-driven validation gradually on one route when that tells the story more clearly.
- Keep delegate implementations small and focused on application behavior, not transport plumbing.
- Keep `@Json` on any handwritten DTO class that is serialized or deserialized as JSON; generated OpenAPI `*TO` models are generated for the contract, but your own DTOs should still make JSON mapper
  generation explicit.

## Summary { #summary }

You extended the contract-first HTTP server from [openapi-http-server.md](openapi-http-server.md) with a second generated API for advanced HTTP concerns:

- `user-http-server.yaml` stayed unchanged for user CRUD
- `data-http-server.yaml` introduced form, multipart, and response-mapping endpoints
- only the data generator task got controller interceptors and validation
- validation was demonstrated on one generated path parameter, `code`
- API-key authorization was driven from the OpenAPI security contract
- both contracts were exposed together through OpenAPI management

So the application now shows a more realistic contract-first evolution path: keep stable generated APIs intact, and add new generated surfaces with more specialized behavior only where needed.

## Key Concepts { #key-concepts }

- one application can host multiple generated OpenAPI server contracts
- different generator tasks can use different options
- `controllerInterceptors` are a powerful way to shape generated controller behavior
- OpenAPI `securitySchemes` map naturally to runtime principal extractors
- spec-driven validation can be enabled selectively per contract
- generated validation can be introduced gradually on a single route instead of everywhere at once
- delegates remain the main place for transport-to-application mapping

## Troubleshooting { #troubleshooting }

**The data endpoints are missing from the graph:**

Check that:

- `openApiGenerateDataHttpServer` is registered
- its `outputDir` is added to `sourceSets.main`
- `compileJava` depends on the task
- `DataApiDelegateImpl` is annotated with `@Component`

**API-key auth does not work:**

Check that:

- `data-http-server.yaml` contains `securitySchemes.apiKeyAuth`
- routes include `security: - apiKeyAuth: []`
- the principal extractor is tagged with `@Tag(ApiSecurity.ApiKeyAuth.class)`
- the configured value matches the `Authorization` header

**Validation does not trigger:**

Check that:

- `enableServerValidation = "true"` is set on the **data** generator task
- the constraint is really present in the OpenAPI schema for `/data/mapping-by-code/{code}`
- you are testing a value outside the allowed `200..599` range

**Error responses are not JSON:**

Check that:

- the generator task includes the `interceptors` config
- it points at `DataApiExceptionHandler`
- `DataApiExceptionHandler` is a component
- `ErrorResponseTO` is declared in `data-http-server.yaml`

**Swagger UI shows only one contract:**

Check `openapi.management.file` in `application.conf`.

It must include both:

- `openapi/user-http-server.yaml`
- `openapi/data-http-server.yaml`

## What's Next? { #whats-next }

- [HTTP Client](http-client.md) if you have not built a client app yet.
- [OpenAPI HTTP Client](openapi-http-client.md) after HTTP Client, to consume contract-generated APIs with typed response wrappers.
- [HTTP Client Advanced](http-client-advanced.md) after HTTP Client, to compare generated clients with handwritten advanced clients.
- [Observability](observability.md) to monitor generated controllers, validation failures, security checks, and interceptors.
- [Resilient Patterns](resilient.md) to protect clients that call these generated endpoints.

## Help { #help }

If you get stuck:

- compare with [Kora Java OpenAPI HTTP Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-openapi-http-server-advanced-app) and [Kora Kotlin OpenAPI HTTP Server Advanced App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-openapi-http-server-advanced-app)
- revisit [OpenAPI HTTP Server](openapi-http-server.md) for the base generated delegate model
- revisit [HTTP Server Advanced](http-server-advanced.md) for the handwritten version of similar HTTP features
- check the [OpenAPI Codegen documentation](../documentation/openapi-codegen.md)
- check the [OpenAPI Management documentation](../documentation/openapi-management.md)
