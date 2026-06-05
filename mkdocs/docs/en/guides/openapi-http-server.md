---
search:
  exclude: true
title: Contract-First HTTP Server with OpenAPI
summary: Continue the HTTP Server guide by replacing the handwritten controller with OpenAPI-generated server code and a delegate
tags: openapi, http-server, swagger, code-generation, contract-first
---

# Contract-First HTTP Server with OpenAPI { #contract-first-http-server }

This guide introduces contract-first HTTP server development with Kora and OpenAPI. It covers how an OpenAPI specification becomes generated server interfaces and models, how a delegate implementation
connects that generated transport layer to application services, and how validation and response metadata are driven by the contract. You will also see how generated code stays separate from
handwritten business logic so the API description remains the source of truth.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java OpenAPI HTTP Server App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-openapi-http-server-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin OpenAPI HTTP Server App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-openapi-http-server-app).

## What You'll Build { #youll-build }

You will rebuild the familiar `http-server` CRUD API in a contract-first style:

- the user API will be described in `user-http-server.yaml`
- Kora will generate the server layer into `build/generated/user-http-server`
- you will implement the generated `UsersApiDelegate`
- `UserService`, `UserRepository`, and `InMemoryUserRepository` will stay familiar
- the application will expose `/openapi` and `/swagger-ui`

## What You'll Need { #youll-need }

- JDK 17 or later
- Gradle 7+
- A text editor or IDE
- Completed [HTTP Server](http-server.md)

## Prerequisites { #prerequisites }

!!! note "Required: Complete HTTP Server First"

    This guide assumes you have completed **[HTTP Server](http-server.md)** and already understand the user CRUD application with `UserRequest`, `UserResponse`, `UserRepository`, `InMemoryUserRepository`, and `UserService`.

    We will keep those ideas and replace only the handwritten HTTP controller layer.

    If you haven't completed the HTTP server guide yet, do that first, because this guide focuses on contract-first OpenAPI generation rather than rebuilding the CRUD service from scratch.

## Overview { #overview }

In this guide we will move gradually from the manual server to a contract-first server:

1. understand what changes when OpenAPI becomes the source of truth
2. describe the existing CRUD API in an OpenAPI file
3. configure Kora OpenAPI generation
4. inspect the generated delegate, controller, response wrappers, and models
5. keep the familiar service and repository layers
6. implement the generated delegate instead of a handwritten controller
7. expose OpenAPI and Swagger UI
8. run and verify the application

### What Is Contract-First Development? { #contract-first-development }

In a code-first workflow, developers usually start with a controller and only later document what that controller does. That works, but over time it often creates friction:

- documentation drifts away from the code
- consumers and producers discuss behavior informally instead of through one shared contract
- response shapes and validation rules get duplicated
- generated clients become harder to trust because the contract is not the main source of truth

Contract-first development changes the order.

Instead of saying "the controller defines the API," we say "the OpenAPI contract defines the API." From that contract, tools can generate:

- server interfaces
- request and response models
- validation hints
- OpenAPI documentation
- later, HTTP clients too

This is especially useful when several teams or several applications depend on the same API. They can all look at the same contract file instead of reverse-engineering controller behavior.

### HTTP Basics { #http-basics }

The [HTTP Server](http-server.md) guide is still where you should first learn:

- `@HttpController`
- `@HttpRoute`
- `@Path`
- `@Query`
- `@Json`
- `HttpResponseEntity`

Here we build on top of that knowledge.

We are not changing the domain and we are not changing the CRUD behavior. We are changing **how the HTTP layer is declared**:

- before: handwritten controller methods
- now: OpenAPI contract + generated server code + delegate implementation

That makes this guide a natural next step instead of a separate unrelated example.

## Dependencies { #dependencies }

First, add the modules and build tooling needed for OpenAPI generation and document exposure.

===! ":fontawesome-brands-java: `Java`"

    ```groovy title="build.gradle"
    import org.openapitools.generator.gradle.plugin.tasks.GenerateTask

    buildscript {
        dependencies {
            classpath("ru.tinkoff.kora:openapi-generator:$koraVersion")
        }
    }

    plugins {
        id "application"
        id "org.openapi.generator" version "7.14.0"
    }

    dependencies {
        implementation("ru.tinkoff.kora:config-hocon")
        implementation("ru.tinkoff.kora:http-server-undertow")
        implementation("ru.tinkoff.kora:json-module")
        implementation("ru.tinkoff.kora:logging-logback")
        implementation("ru.tinkoff.kora:openapi-management")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="build.gradle.kts"
    import org.openapitools.generator.gradle.plugin.tasks.GenerateTask

    buildscript {
        dependencies {
            classpath("ru.tinkoff.kora:openapi-generator:$koraVersion")
        }
    }

    plugins {
        id("application")
        id("org.openapi.generator") version "7.14.0"
    }

    dependencies {
        implementation("ru.tinkoff.kora:config-hocon")
        implementation("ru.tinkoff.kora:http-server-undertow")
        implementation("ru.tinkoff.kora:json-module")
        implementation("ru.tinkoff.kora:logging-logback")
        implementation("ru.tinkoff.kora:openapi-management")
    }
    ```

At this step, it helps to understand why each dependency exists:

- `openapi-generator` lets Gradle generate Kora server code from the contract
- `openapi-management` exposes OpenAPI and Swagger UI

We also need the management module in the application graph:

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/openapi/httpserver/Application.java"
    package ru.tinkoff.kora.guide.openapi.httpserver;

    import ru.tinkoff.kora.application.graph.KoraApplication;
    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.config.hocon.HoconConfigModule;
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule;
    import ru.tinkoff.kora.json.module.JsonModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;
    import ru.tinkoff.kora.openapi.management.OpenApiManagementModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            UndertowHttpServerModule,
            JsonModule,
            LogbackModule,
            OpenApiManagementModule {  // <----- Connected module

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/openapi/httpserver/Application.kt"
    package ru.tinkoff.kora.guide.openapi.httpserver

    import ru.tinkoff.kora.application.graph.KoraApplication
    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.config.hocon.HoconConfigModule
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule
    import ru.tinkoff.kora.json.module.JsonModule
    import ru.tinkoff.kora.logging.logback.LogbackModule
    import ru.tinkoff.kora.openapi.management.OpenApiManagementModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        UndertowHttpServerModule,
        JsonModule,
        LogbackModule,
        OpenApiManagementModule  // <----- Connected module

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

So after this step, we have prepared the application for a contract-first server, but we have not generated anything yet.

## OpenAPI Contract { #openapi-contract }

Now we move the API contract out of Java or Kotlin annotations and into a shared OpenAPI file.

Create:

`src/main/resources/openapi/user-http-server.yaml`

??? example "OpenAPI contract"

    ```yaml title="src/main/resources/openapi/user-http-server.yaml"
    openapi: 3.0.3
    info:
      title: User Management API
      description: Contract-first version of the HTTP Server guide API
      version: 1.0.0
    tags:
      - name: users
        description: User management operations
    paths:
      /users:
        get:
          tags:
            - users
          operationId: getUsers
          summary: Get users
          parameters:
            - name: page
              in: query
              required: false
              schema:
                type: integer
                minimum: 0
                default: 0
            - name: size
              in: query
              required: false
              schema:
                type: integer
                minimum: 1
                maximum: 100
                default: 10
            - name: sort
              in: query
              required: false
              schema:
                type: string
                enum: [name, email, createdAt]
                default: name
          responses:
            "200":
              description: Users returned
              content:
                application/json:
                  schema:
                    type: array
                    items:
                      $ref: "#/components/schemas/UserResponseTO"
            "500":
              description: Internal server error
              content:
                application/json:
                  schema:
                    $ref: "#/components/schemas/ErrorResponseTO"
        post:
          tags:
            - users
          operationId: createUser
          summary: Create user
          requestBody:
            required: true
            content:
              application/json:
                schema:
                  $ref: "#/components/schemas/UserRequestTO"
          responses:
            "201":
              description: User created
              content:
                application/json:
                  schema:
                    $ref: "#/components/schemas/UserResponseTO"
            "500":
              description: Internal server error
              content:
                application/json:
                  schema:
                    $ref: "#/components/schemas/ErrorResponseTO"
      /users/{userId}:
        get:
          tags:
            - users
          operationId: getUser
          summary: Get user by id
          parameters:
            - name: userId
              in: path
              required: true
              schema:
                type: string
          responses:
            "200":
              description: User returned
              content:
                application/json:
                  schema:
                    $ref: "#/components/schemas/UserResponseTO"
            "404":
              description: User not found
              content:
                application/json:
                  schema:
                    $ref: "#/components/schemas/ErrorResponseTO"
            "500":
              description: Internal server error
              content:
                application/json:
                  schema:
                    $ref: "#/components/schemas/ErrorResponseTO"
        put:
          tags:
            - users
          operationId: updateUser
          summary: Update user
          parameters:
            - name: userId
              in: path
              required: true
              schema:
                type: string
          requestBody:
            required: true
            content:
              application/json:
                schema:
                  $ref: "#/components/schemas/UserRequestTO"
          responses:
            "200":
              description: User updated
              headers:
                X-Updated-At:
                  required: true
                  schema:
                    type: string
              content:
                application/json:
                  schema:
                    $ref: "#/components/schemas/UserResponseTO"
            "404":
              description: User not found
              content:
                application/json:
                  schema:
                    $ref: "#/components/schemas/ErrorResponseTO"
            "500":
              description: Internal server error
              content:
                application/json:
                  schema:
                    $ref: "#/components/schemas/ErrorResponseTO"
        delete:
          tags:
            - users
          operationId: deleteUser
          summary: Delete user
          parameters:
            - name: userId
              in: path
              required: true
              schema:
                type: string
          responses:
            "204":
              description: User deleted
            "404":
              description: User not found
              content:
                application/json:
                  schema:
                    $ref: "#/components/schemas/ErrorResponseTO"
            "500":
              description: Internal server error
              content:
                application/json:
                  schema:
                    $ref: "#/components/schemas/ErrorResponseTO"
    components:
      schemas:
        ErrorResponseTO:
          type: object
          required:
            - message
          properties:
            message:
              type: string
        UserRequestTO:
          type: object
          required:
            - name
            - email
          properties:
            name:
              type: string
              minLength: 1
              maxLength: 100
            email:
              type: string
              format: email
        UserResponseTO:
          type: object
          required:
            - id
            - name
            - email
            - createdAt
          properties:
            id:
              type: string
            name:
              type: string
            email:
              type: string
            createdAt:
              type: string
              format: date-time
    ```

This file is intentionally familiar.

We are not inventing a new API here. We are describing the same user CRUD API that already exists in the `http-server` guide:

- same `/users` and `/users/{userId}` routes
- same query parameters for listing
- same request and response shapes
- same `404` and `204` behaviors, now with an explicit `ErrorResponseTO` body for error cases
- the same update header `X-Updated-At`

That is an important teaching point. Contract-first development is not about changing the business idea. It is about moving the transport contract into a formal, shareable source of truth.

## OpenAPI Code Generation { #openapi-codegen }

The detailed server generation options, `mode = server`, `delegateMethodBodyMode` are described in [OpenAPI Codegen: Server](../documentation/openapi-codegen.md#server).

Now tell Gradle how to generate the server code from that contract.

===! ":fontawesome-brands-java: `Java`"

    ```groovy title="build.gradle"
    def openApiGenerateUsersHttpServer = tasks.register("openApiGenerateUsersHttpServer", GenerateTask) {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/user-http-server.yaml"
        outputDir = "$buildDir/generated/user-http-server"
        def corePackage = "ru.tinkoff.kora.guide.openapi.httpserver.user"
        apiPackage = "${corePackage}.api"
        modelPackage = "${corePackage}.model"
        invokerPackage = "${corePackage}.invoker"
        configOptions = [
                mode                  : "java-server",
        ]
    }

    sourceSets.main {
        java.srcDirs += openApiGenerateUsersHttpServer.get().outputDir
    }

    compileJava.dependsOn openApiGenerateUsersHttpServer
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="build.gradle.kts"
    val openApiGenerateUsersHttpServer = tasks.register<GenerateTask>("openApiGenerateUsersHttpServer") {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/user-http-server.yaml"
        outputDir = "$buildDir/generated/user-http-server"
        val corePackage = "ru.tinkoff.kora.guide.openapi.httpserver.user"
        apiPackage = "$corePackage.api"
        modelPackage = "$corePackage.model"
        invokerPackage = "$corePackage.invoker"
        configOptions = mapOf(
            "mode" to "java-server",
        )
    }

    sourceSets.main {
        java.srcDir(openApiGenerateUsersHttpServer.get().outputDir)
    }

    tasks.compileJava {
        dependsOn(openApiGenerateUsersHttpServer)
    }
    ```

At this step, three details matter most:

- generated code will be written into `build/generated/user-http-server`
- generated types will live under `ru.tinkoff.kora.guide.openapi.httpserver.user`
- generation happens automatically before compilation

This is the build step that turns a static YAML contract into real server-side Java code.

## Generated Output { #generated-output }

Run:

```bash
./gradlew clean classes
```

Now look at the generated files:

===! ":fontawesome-brands-java: `Java`"

    - `build/generated/user-http-server/ru/tinkoff/kora/guide/openapi/httpserver/user/api/UsersApiDelegate.java`
    - `build/generated/user-http-server/ru/tinkoff/kora/guide/openapi/httpserver/user/api/UsersApiController.java`
    - `build/generated/user-http-server/ru/tinkoff/kora/guide/openapi/httpserver/user/api/UsersApiResponses.java`
    - `build/generated/user-http-server/ru/tinkoff/kora/guide/openapi/httpserver/user/model/UserRequestTO.java`
    - `build/generated/user-http-server/ru/tinkoff/kora/guide/openapi/httpserver/user/model/UserResponseTO.java`
    - `build/generated/user-http-server/ru/tinkoff/kora/guide/openapi/httpserver/user/model/ErrorResponseTO.java`

=== ":simple-kotlin: `Kotlin`"

    - `build/generated/user-http-server/ru/tinkoff/kora/guide/openapi/httpserver/user/api/UsersApiDelegate.kt`
    - `build/generated/user-http-server/ru/tinkoff/kora/guide/openapi/httpserver/user/api/UsersApiController.kt`
    - `build/generated/user-http-server/ru/tinkoff/kora/guide/openapi/httpserver/user/api/UsersApiResponses.kt`
    - `build/generated/user-http-server/ru/tinkoff/kora/guide/openapi/httpserver/user/model/UserRequestTO.kt`
    - `build/generated/user-http-server/ru/tinkoff/kora/guide/openapi/httpserver/user/model/UserResponseTO.kt`
    - `build/generated/user-http-server/ru/tinkoff/kora/guide/openapi/httpserver/user/model/ErrorResponseTO.kt`

The generated server introduces several important abstractions, and it helps a lot to inspect them one by one instead of treating generation as a black box.

### 1. `UsersApiDelegate` { #1-usersapidelegate }

This is the interface you implement in your own application code.

Here is a shortened version of the generated delegate:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface UsersApiDelegate {

        UsersApiResponses.CreateUserApiResponse createUser(
            UserRequestTO userRequestTO
        ) throws Exception;

        UsersApiResponses.GetUserApiResponse getUser(
            String userId
        ) throws Exception;

        UsersApiResponses.GetUsersApiResponse getUsers(
            @Nullable Integer page,
            @Nullable Integer size,
            @Nullable String sort
        ) throws Exception;
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface UsersApiDelegate {

        fun createUser(
            userRequestTO: UserRequestTO
        ): UsersApiResponses.CreateUserApiResponse

        fun getUser(
            userId: String
        ): UsersApiResponses.GetUserApiResponse

        fun getUsers(
            page: Int?,
            size: Int?,
            sort: String?
        ): UsersApiResponses.GetUsersApiResponse
    }
    ```

This is the first big conceptual shift relative to `http-server.md`.

In the handwritten server guide, you defined the controller methods yourself and decorated them with transport annotations. Here, the contract already defines the transport layer, so the generator
gives you the interface that must be implemented.

That means your code no longer says:

- which HTTP path exists
- which method is `GET` or `POST`
- which request body belongs to which route

Instead, your code says:

- how to implement the behavior described by the contract
- how to map between generated transport models and your internal application DTOs
- which response variant should be returned for each outcome

### 2. `UsersApiController` { #2-usersapicontroller }

This is the generated HTTP controller that Kora puts into the application graph.

You do not edit it manually, and you usually do not need to understand every line inside it. What matters is its responsibility:

- receive the HTTP request
- validate and map transport data according to the contract
- call the corresponding delegate method
- turn the returned generated response wrapper into an actual HTTP response

So the generated controller becomes the transport adapter, while your delegate becomes the implementation boundary.

That split is one of the healthiest parts of contract-first server generation. It keeps HTTP protocol mechanics in generated code and keeps application behavior in your own code.

### 3. `UsersApiResponses` { #3-usersapiresponses }

This file is one of the most useful generated artifacts because it makes the transport contract explicit.

Here is a shortened version of the generated `getUser` response family:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface UsersApiResponses {

        sealed interface GetUserApiResponse {

            record GetUser200ApiResponse(
                UserResponseTO content
            ) implements GetUserApiResponse {}

            record GetUser404ApiResponse(
                ErrorResponseTO content
            ) implements GetUserApiResponse {}

            record GetUser500ApiResponse(
                ErrorResponseTO content
            ) implements GetUserApiResponse {}
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface UsersApiResponses {

        sealed interface GetUserApiResponse {

            data class GetUser200ApiResponse(
                val content: UserResponseTO
            ) : GetUserApiResponse

            data class GetUser404ApiResponse(
                val content: ErrorResponseTO
            ) : GetUserApiResponse

            data class GetUser500ApiResponse(
                val content: ErrorResponseTO
            ) : GetUserApiResponse
        }
    }
    ```

This is the same idea we explored in the OpenAPI client guide, but now from the server side.

The OpenAPI contract says that `GET /users/{userId}` may produce:

- `200` with a `UserResponseTO` body
- `404` with an `ErrorResponseTO` body
- `500` with an `ErrorResponseTO` body

So the generator creates one sealed response family that models those three outcomes.

That is important because the contract is not only about request and success payloads. It also describes the allowed error shapes, and the server-side generated code preserves that information as real
Java or Kotlin types, depending on the guide application you build.

### 4. Generated Models { #4-generated-models }

The generator also creates contract-layer transport models such as:

- `UserRequestTO`
- `UserResponseTO`
- `ErrorResponseTO`

These generated models belong to the OpenAPI boundary, not to your internal domain or service layer.

That is why the guide still keeps internal DTOs like `UserRequest` and `UserResponse` inside the application code. The delegate is the place where those two worlds meet:

- generated OpenAPI transport models on one side
- internal application models on the other

Keeping those layers separate makes future refactoring much safer. You can evolve internal code without pretending that generated transport types are your whole domain model.

In the companion app, handwritten internal DTOs that can cross a JSON boundary are still annotated with `@Json`. Generated OpenAPI models already come from the generator, but your own request and
response DTO classes should declare the JSON contract explicitly so Kora can generate their mappers during the normal annotation-processing phase.

### Generated `getUser()` Walkthrough { #generated-getuser-walkthrough }

The easiest way to understand what is happening is to follow one operation from the contract into the generated code.

The OpenAPI file declares:

- a `GET /users/{userId}` route
- one path parameter `userId`
- three responses: `200`, `404`, `500`

From that, the generator creates:

- a `getUser(String userId)` method in `UsersApiDelegate`
- a `GetUserApiResponse` sealed response family
- a generated controller method that will call your delegate and serialize the selected wrapper

That means your delegate implementation can stay focused on business meaning:

- if the user exists, return `GetUser200ApiResponse`
- if the user is missing, return `GetUser404ApiResponse(new ErrorResponseTO(...))`
- if a real internal failure happens, the transport layer still knows that `500` is part of the declared contract

This is the main â€œahaâ€ moment of the guide: OpenAPI generation does not just save typing. It turns the HTTP contract into a set of explicit server-side abstractions that guide your implementation.

## Service and Repository { #service-repository }

One of the nicest parts of this migration is that most of your application does **not** need to be redesigned.

The business side remains familiar:

- `UserRepository`
- `InMemoryUserRepository`
- `UserService`

Those classes can keep the same responsibilities they had in the `http-server` guide:

- repository stores and retrieves users
- service coordinates CRUD behavior
- only the HTTP entry point changes

That separation is useful in real projects. If your domain logic lives in a service layer instead of inside the controller, it becomes much easier to replace one transport style with another.

So in this guide, we do **not** rewrite the whole application. We only replace the handwritten controller layer with a generated one.

## Delegate { #delegate }

Now we create the class that connects generated HTTP code to our existing service layer.

Create:

`src/main/java/ru/tinkoff/kora/guide/openapi/httpserver/controller/UserApiDelegateImpl.java`

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/openapi/httpserver/controller/UserApiDelegateImpl.java"
    package ru.tinkoff.kora.guide.openapi.httpserver.controller;

    import java.time.Instant;
    import java.time.ZoneOffset;
    import ru.tinkoff.kora.guide.openapi.httpserver.user.model.ErrorResponseTO;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.openapi.httpserver.user.api.UsersApiDelegate;
    import ru.tinkoff.kora.guide.openapi.httpserver.user.api.UsersApiResponses;
    import ru.tinkoff.kora.guide.openapi.httpserver.user.model.UserRequestTO;
    import ru.tinkoff.kora.guide.openapi.httpserver.user.model.UserResponseTO;
    import ru.tinkoff.kora.guide.openapi.httpserver.dto.UserRequest;
    import ru.tinkoff.kora.guide.openapi.httpserver.dto.UserResponse;
    import ru.tinkoff.kora.guide.openapi.httpserver.service.UserService;

    @Component
    public final class UserApiDelegateImpl implements UsersApiDelegate {

        private final UserService userService;

        public UserApiDelegateImpl(UserService userService) {
            this.userService = userService;
        }

        @Override
        public UsersApiResponses.CreateUserApiResponse createUser(UserRequestTO userRequest) {
            var created = this.userService.createUser(new UserRequest(userRequest.name(), userRequest.email()));
            return new UsersApiResponses.CreateUserApiResponse.CreateUser201ApiResponse(this.toGenerated(created));
        }

        @Override
        public UsersApiResponses.DeleteUserApiResponse deleteUser(String userId) {
            if (this.userService.getUser(userId).isEmpty()) {
                return new UsersApiResponses.DeleteUserApiResponse.DeleteUser404ApiResponse(
                        this.notFound(userId)
                );
            }

            this.userService.deleteUser(userId);
            return new UsersApiResponses.DeleteUserApiResponse.DeleteUser204ApiResponse();
        }

        @Override
        public UsersApiResponses.GetUserApiResponse getUser(String userId) {
            return this.userService.getUser(userId)
                    .<UsersApiResponses.GetUserApiResponse>map(user -> new UsersApiResponses.GetUserApiResponse.GetUser200ApiResponse(this.toGenerated(user)))
                    .orElseGet(() -> new UsersApiResponses.GetUserApiResponse.GetUser404ApiResponse(
                            this.notFound(userId)
                    ));
        }

        @Override
        public UsersApiResponses.GetUsersApiResponse getUsers(Integer page, Integer size, String sort) {
            int effectivePage = page == null ? 0 : page;
            int effectiveSize = size == null ? 10 : size;
            String effectiveSort = sort == null ? "name" : sort;
            var users = this.userService.getUsers(effectivePage, effectiveSize, effectiveSort).stream()
                    .map(this::toGenerated)
                    .toList();
            return new UsersApiResponses.GetUsersApiResponse.GetUsers200ApiResponse(users);
        }

        @Override
        public UsersApiResponses.UpdateUserApiResponse updateUser(String userId, UserRequestTO userRequest) {
            if (this.userService.getUser(userId).isEmpty()) {
                return new UsersApiResponses.UpdateUserApiResponse.UpdateUser404ApiResponse(
                        this.notFound(userId)
                );
            }

            var updated = this.userService.updateUser(userId, new UserRequest(userRequest.name(), userRequest.email()));
            return new UsersApiResponses.UpdateUserApiResponse.UpdateUser200ApiResponse(
                    this.toGenerated(updated),
                    Instant.now().toString()
            );
        }

        private UserResponseTO toGenerated(UserResponse user) {
            return new UserResponseTO(
                    user.id(),
                    user.name(),
                    user.email(),
                    user.createdAt().atOffset(ZoneOffset.UTC)
            );
        }

        private ErrorResponseTO notFound(String userId) {
            return new ErrorResponseTO("User with id "" + userId + "" was not found");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/openapi/httpserver/controller/UserApiDelegateImpl.kt"
    package ru.tinkoff.kora.guide.openapi.httpserver.controller

    import java.time.Instant
    import java.time.ZoneOffset
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.openapi.httpserver.user.api.UsersApiDelegate
    import ru.tinkoff.kora.guide.openapi.httpserver.user.api.UsersApiResponses
    import ru.tinkoff.kora.guide.openapi.httpserver.user.model.ErrorResponseTO
    import ru.tinkoff.kora.guide.openapi.httpserver.user.model.UserRequestTO
    import ru.tinkoff.kora.guide.openapi.httpserver.user.model.UserResponseTO
    import ru.tinkoff.kora.guide.openapi.httpserver.dto.UserRequest
    import ru.tinkoff.kora.guide.openapi.httpserver.dto.UserResponse
    import ru.tinkoff.kora.guide.openapi.httpserver.service.UserService

    @Component
    class UserApiDelegateImpl(
        private val userService: UserService
    ) : UsersApiDelegate {

        override fun createUser(userRequest: UserRequestTO): UsersApiResponses.CreateUserApiResponse {
            val created = userService.createUser(UserRequest(userRequest.name(), userRequest.email()))
            return UsersApiResponses.CreateUserApiResponse.CreateUser201ApiResponse(toGenerated(created))
        }

        override fun deleteUser(userId: String): UsersApiResponses.DeleteUserApiResponse {
            if (userService.getUser(userId).isEmpty) {
                return UsersApiResponses.DeleteUserApiResponse.DeleteUser404ApiResponse(
                    notFound(userId)
                )
            }

            userService.deleteUser(userId)
            return UsersApiResponses.DeleteUserApiResponse.DeleteUser204ApiResponse()
        }

        override fun getUser(userId: String): UsersApiResponses.GetUserApiResponse {
            return userService.getUser(userId)
                .map<UsersApiResponses.GetUserApiResponse> { user ->
                    UsersApiResponses.GetUserApiResponse.GetUser200ApiResponse(toGenerated(user))
                }
                .orElseGet {
                    UsersApiResponses.GetUserApiResponse.GetUser404ApiResponse(
                        notFound(userId)
                    )
                }
        }

        override fun getUsers(page: Int?, size: Int?, sort: String?): UsersApiResponses.GetUsersApiResponse {
            val effectivePage = page ?: 0
            val effectiveSize = size ?: 10
            val effectiveSort = sort ?: "name"
            val users = userService.getUsers(effectivePage, effectiveSize, effectiveSort)
                .map(::toGenerated)
            return UsersApiResponses.GetUsersApiResponse.GetUsers200ApiResponse(users)
        }

        override fun updateUser(userId: String, userRequest: UserRequestTO): UsersApiResponses.UpdateUserApiResponse {
            if (userService.getUser(userId).isEmpty) {
                return UsersApiResponses.UpdateUserApiResponse.UpdateUser404ApiResponse(
                    notFound(userId)
                )
            }

            val updated = userService.updateUser(userId, UserRequest(userRequest.name(), userRequest.email()))
            return UsersApiResponses.UpdateUserApiResponse.UpdateUser200ApiResponse(
                toGenerated(updated),
                Instant.now().toString()
            )
        }

        private fun toGenerated(user: UserResponse): UserResponseTO {
            return UserResponseTO(
                user.id(),
                user.name(),
                user.email(),
                user.createdAt().atOffset(ZoneOffset.UTC)
            )
        }

        private fun notFound(userId: String): ErrorResponseTO {
            return ErrorResponseTO("User with id "$userId" was not found")
        }
    }
    ```

This step introduces the core abstraction of the guide.

In the manual `http-server` version, the controller itself decided:

- how to receive HTTP input
- which status code to return
- how to build the response

In this OpenAPI version, that responsibility moves into the delegate implementation.

The generated controller handles the low-level HTTP transport. Your delegate handles:

- calling the service layer
- selecting the correct generated response wrapper
- mapping between generated OpenAPI models and internal application DTOs

Because the OpenAPI contract now gives `404` and `500` responses a shared `ErrorResponseTO` body, the delegate can also return typed error payloads instead of only empty status variants. That makes
the generated wrappers more useful for both server and client code, because error responses become part of the contract too.

That mapping layer is not accidental. It is a healthy separation:

- generated models belong to the API contract
- internal DTOs belong to your application

Keeping that boundary explicit makes the application easier to evolve later.

## Configuration { #config }

Now we expose the contract and interactive documentation from the running application.

Update `src/main/resources/application.conf`:

For the full configuration reference, see [HTTP Server](../documentation/http-server.md), [OpenAPI Management](../documentation/openapi-management.md)
and [Logging SLF4J](../documentation/logging-slf4j.md).

===! ":material-code-json: `Hocon`"

    ```javascript title="src/main/resources/application.conf"
    httpServer {
      publicApiHttpPort = 8080 //(1)!
      privateApiHttpPort = 8085 //(2)!
      telemetry.logging.enabled = true //(3)!
    }

    openapi {
      management {
        enabled = true //(4)!
        endpoint = "/openapi" //(5)!
        swaggerui {
          enabled = true //(6)!
          endpoint = "/swagger-ui" //(7)!
        }
      }
    }

    logging.level {
      "root" = "WARN" //(8)!
      "ru.tinkoff.kora" = "INFO" //(9)!
      "ru.tinkoff.kora.guide.openapi.httpserver" = "INFO" //(10)!
    }
    ```

    1. Default public HTTP port used by application endpoints.
    2. Default private HTTP port used by probes, metrics, and management endpoints.
    3. Enables the feature for this configuration section.
    4. Enables the feature for this configuration section.
    5. Telemetry exporter endpoint.
    6. Enables the feature for this configuration section.
    7. Telemetry exporter endpoint.
    8. Value for `logging.level.root`.
    9. Value for `logging.level.ru.tinkoff.kora`.
    10. Value for `logging.level.ru.tinkoff.kora.guide.openapi.httpserver`.

=== ":simple-yaml: `YAML`"

    ```yaml title="src/main/resources/application.yaml"
    httpServer:
      publicApiHttpPort: 8080 #(1)!
      privateApiHttpPort: 8085 #(2)!
      telemetry:
        logging:
          enabled: true #(3)!
    openapi:
      management:
        enabled: true #(4)!
        endpoint: "/openapi" #(5)!
        swaggerui:
          enabled: true #(6)!
          endpoint: "/swagger-ui" #(7)!
    logging:
      level:
        root: "WARN" #(8)!
        "ru.tinkoff.kora": "INFO" #(9)!
        "ru.tinkoff.kora.guide.openapi.httpserver": "INFO" #(10)!
    ```

    1. Default public HTTP port used by application endpoints.
    2. Default private HTTP port used by probes, metrics, and management endpoints.
    3. Enables the feature for this configuration section.
    4. Enables the feature for this configuration section.
    5. Telemetry exporter endpoint.
    6. Enables the feature for this configuration section.
    7. Telemetry exporter endpoint.
    8. Value for `logging.level.root`.
    9. Value for `logging.level.ru.tinkoff.kora`.
    10. Value for `logging.level.ru.tinkoff.kora.guide.openapi.httpserver`.

This gives us two very practical endpoints:

- `/openapi` returns the OpenAPI document
- `/swagger-ui` gives an interactive UI for exploring and testing the API

This is one of the biggest benefits of contract-first development. The documentation is not something you write later. It is part of the same build that generates the server layer.

## Check Application { #check-app }

Build the module:

```bash
./gradlew :guides-apps:guide-openapi-http-server-app:clean :guides-apps:guide-openapi-http-server-app:classes
```

Run the application:

```bash
./gradlew run
```

Then verify the API:

```bash
curl http://localhost:8080/users
```

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com"}'
```

```bash
curl http://localhost:8080/openapi
```

Open in your browser:

```text
http://localhost:8080/swagger-ui
```

At this point, the application behaves like the familiar `http-server` CRUD service, but the HTTP layer is now driven by the OpenAPI contract.

## Delegate Test { #delegate-test }

The guide application also includes a test that verifies CRUD behavior through the generated delegate.

Run:

```bash
./gradlew test
```

That test validates:

- create
- get by id
- list
- update
- delete
- `404` after delete

This is a useful checkpoint because it proves that the generated API layer and your delegate implementation are wired together correctly.

## Best Practices { #best-practices }

- Keep the OpenAPI contract close to the real behavior of the application. The contract should describe reality, not future ideas.
- Keep generated code as build output only. Do not edit files under `build/generated/user-http-server`.
- Keep business logic in services, not in generated classes.
- Use delegates as the transport boundary between generated API types and internal application models.
- Regenerate server code as part of normal builds so the contract and compiled application cannot drift apart.

## Summary { #summary }

You took the user CRUD server from the [HTTP Server](http-server.md) guide and rebuilt its HTTP layer in a contract-first style:

- the API is now described in `user-http-server.yaml`
- Kora generates the server layer into `build/generated/user-http-server`
- the application implements `UsersApiDelegate`
- the familiar service and repository layers remain in place
- the app exposes `/openapi` and `/swagger-ui`

So the behavior stays familiar, but the contract now drives the transport layer instead of a handwritten controller.

## Key Concepts { #key-concepts }

- contract-first development starts from a shared API specification
- Kora can generate server code from OpenAPI
- generated controllers and delegates separate transport wiring from application logic
- delegates are a good place to map between generated contract models and internal DTOs
- adding new status codes such as `500` to OpenAPI changes the generated response wrappers too
- Swagger UI and OpenAPI become a natural part of the application when the contract is built into the project

## Troubleshooting { #troubleshooting }

**Code generation does not run:**

Check that:

- `org.openapi.generator` is applied
- `GenerateTask` is imported
- `compileJava.dependsOn openApiGenerateUsersHttpServer` is configured

**The application cannot find generated classes:**

Check that the generated source directory is added to `sourceSets.main`:

- `build/generated/user-http-server`

Also verify that your package settings match your imports:

- `ru.tinkoff.kora.guide.openapi.httpserver.user.api`
- `ru.tinkoff.kora.guide.openapi.httpserver.user.model`

**Swagger UI is not available:**

Make sure that:

- `OpenApiManagementModule` is included in `Application`
- `openapi.management.enabled = true`
- `swaggerui.enabled = true`

**Delegate is not discovered by Kora:**

Make sure that:

- the delegate is annotated with `@Component`
- it implements the generated `UsersApiDelegate`
- it imports the generated package you configured in `build.gradle`

**The manual controller conflicts with the generated server:**

In this application variant, the handwritten user controller should not be kept alongside the generated server controller. Once you move to the OpenAPI-generated transport layer, the delegate becomes
the main implementation point for HTTP behavior.

**A response wrapper variant is missing:**

Generated response variants only exist for status codes that are explicitly listed in the OpenAPI contract.

So if you expect a generated `500` abstraction such as `GetUser500ApiResponse`, make sure that `500` is present in the `responses` section of that operation in `user-http-server.yaml`.

## What's Next? { #whats-next }

- [HTTP Client](http-client.md) if you have not built a client app yet.
- [OpenAPI HTTP Client](openapi-http-client.md) after HTTP Client, to generate a client from the same kind of contract.
- [HTTP Server Advanced](http-server-advanced.md) before [OpenAPI HTTP Server Advanced](openapi-http-server-advanced.md), because the advanced OpenAPI guide combines both tracks.
- [Validation](validation.md) to compare handwritten validation with spec-driven validation.

## Help { #help }

If you get stuck:

- compare with [Kora Java OpenAPI HTTP Server App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-openapi-http-server-app) and [Kora Kotlin OpenAPI HTTP Server App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-openapi-http-server-app)
- compare with [HTTP Server](http-server.md) to see what the generated controller replaced
- check the [OpenAPI Codegen documentation](../documentation/openapi-codegen.md)
- check the [OpenAPI Management documentation](../documentation/openapi-management.md)
