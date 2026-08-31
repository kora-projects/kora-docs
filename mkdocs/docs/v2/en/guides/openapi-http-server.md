---
search:
  exclude: true
title: Contract-First HTTP Server with OpenAPI
summary: Continue the HTTP Server guide by replacing the handwritten controller with OpenAPI-generated server code and a delegate
description: "Contract-first Kora HTTP server from an OpenAPI file: the org.openapi.generator Gradle plugin with generatorName kora, configOptions mode java-server / kotlin-server, enableServerValidation, the generated UsersApiController, UsersApiDelegate and sealed UsersApiResponses wrappers, generated TO models, and openapi.management.files with /openapi, /swagger-ui and /scalar."
agent:
  use_when: "Use this file for questions about building a contract-first Kora HTTP server from an OpenAPI contract step by step: GenerateTask, generatorName kora, mode java-server and kotlin-server, enableServerValidation, apiPackage / modelPackage / invokerPackage, the generated <Api>Controller, <Api>Delegate, <Api>Responses and <Api>ServerRequestMappers, implementing a delegate with @Component, mapping generated TO models to internal DTOs, OpenApiManagementModule and the openapi.management.files, path, swaggerui and scalar configuration."
tags: openapi, http-server, swagger, code-generation, contract-first
---

# Contract-First HTTP Server with OpenAPI { #contract-first-http-server }

This guide introduces contract-first HTTP server development with Kora and OpenAPI. It covers how an OpenAPI specification becomes generated server interfaces and models, how a delegate implementation
connects that generated transport layer to application services, and how validation and response metadata are driven by the contract. You will also see how generated code stays separate from
handwritten business logic so the API description remains the source of truth.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java OpenAPI HTTP Server App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-openapi-http-server-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin OpenAPI HTTP Server App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-openapi-http-server-app).

## What You'll Build { #youll-build }

You will rebuild the familiar `http-server` CRUD API in a contract-first style:

- the user API will be described in `user-http-server.yaml`
- Kora will generate the server layer into `build/generated/user-http-server`
- you will implement the generated `UsersApiDelegate`
- `UserService`, `UserRepository`, and `InMemoryUserRepository` will stay familiar
- the application will expose `/openapi` and `/swagger-ui`

## What You'll Need { #youll-need }

- JDK 25 or later
- Gradle 9+
- A text editor or IDE
- Completed [HTTP Server](http-server.md)

Kora 2.0 artifacts are compiled for Java 25, so the JDK that compiles the application must be 25 or newer. The OpenAPI generator adds one more requirement, described in
[Dependencies](#dependencies): the `Gradle` JVM itself must also be 25 or newer.

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

- server controllers and delegate contracts
- request and response models
- validation annotations
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

Request handling stays **synchronous**, exactly as in the handwritten server. Undertow dispatches every request onto a virtual thread, the generated controller calls your delegate method directly, and
the delegate returns its result. There are no reactive or `suspend` generation modes in Kora 2.0 — the generator supports exactly four modes: `java-client`, `java-server`, `kotlin-client`, and
`kotlin-server`.

That makes this guide a natural next step instead of a separate unrelated example.

## Dependencies { #dependencies }

Contract-first generation needs two different kinds of build wiring, and it is worth separating them in your head from the start:

- the `org.openapi.generator` **Gradle plugin**, which provides the `GenerateTask` type
- the `io.koraframework:openapi-generator` **library**, which teaches that plugin how to emit Kora code

The library goes on the `buildscript` classpath, not into `dependencies`, because it must be loaded by `Gradle` itself before your project is compiled.

===! ":fontawesome-brands-java: `Java`"

    Update `build.gradle`:

    ```groovy
    import org.openapitools.generator.gradle.plugin.tasks.GenerateTask //(1)!

    buildscript {
        repositories {
            mavenCentral()
        }
        dependencies {
            classpath("io.koraframework:openapi-generator:2.0.0.RC1") //(2)!
        }
    }

    plugins {
        id "application"
        id "org.openapi.generator" version "7.24.0" //(3)!
    }

    dependencies {
        koraBom platform("io.koraframework:kora-bom:2.0.0.RC1") //(4)!

        annotationProcessor "io.koraframework:annotation-processors" //(5)!

        implementation "io.koraframework:config-hocon"
        implementation "io.koraframework:http-server-undertow"
        implementation "io.koraframework:json-common"
        implementation "io.koraframework:logging-logback"
        implementation "io.koraframework:openapi-management" //(6)!
        implementation "io.koraframework:validation-module" //(7)!
    }
    ```

    1.  `GenerateTask` is the plugin task type used to declare a generation task.
    2.  Kora generator implementation, loaded by the `Gradle` JVM through the `buildscript` classpath.
    3.  `OpenAPI Generator` Gradle plugin. Kora 2.0 is compiled against `OpenAPI Generator 7.24.0`, so pin the plugin to the same version — other versions are not guaranteed to work because the generator API can be incompatible at code level.
    4.  Kora BOM: aligns the versions of every Kora module and of the libraries Kora depends on.
    5.  Kora annotation processor: generates the application graph, the controller modules, and the JSON readers/writers during compilation.
    6.  Publishes the contract file and the Swagger UI / Scalar pages from the running application.
    7.  Validation runtime, required because we generate the server with `enableServerValidation`.

=== ":simple-kotlin: `Kotlin`"

    Update `build.gradle.kts`:

    ```kotlin
    import org.openapitools.generator.gradle.plugin.tasks.GenerateTask //(1)!

    buildscript {
        repositories {
            mavenCentral()
        }
        dependencies {
            classpath("io.koraframework:openapi-generator:2.0.0.RC1") //(2)!
        }
    }

    plugins {
        id("org.jetbrains.kotlin.jvm")
        id("com.google.devtools.ksp")
        id("application")
        id("org.openapi.generator") version "7.24.0" //(3)!
    }

    dependencies {
        implementation(platform("io.koraframework:kora-bom:2.0.0.RC1")) //(4)!

        ksp("io.koraframework:symbol-processors:2.0.0.RC1") //(5)!

        implementation("io.koraframework:config-hocon")
        implementation("io.koraframework:http-server-undertow")
        implementation("io.koraframework:json-common")
        implementation("io.koraframework:logging-logback")
        implementation("io.koraframework:openapi-management") //(6)!
        implementation("io.koraframework:validation-module") //(7)!
    }
    ```

    1.  `GenerateTask` is the plugin task type used to declare a generation task.
    2.  Kora generator implementation, loaded by the `Gradle` JVM through the `buildscript` classpath.
    3.  `OpenAPI Generator` Gradle plugin. Kora 2.0 is compiled against `OpenAPI Generator 7.24.0`, so pin the plugin to the same version — other versions are not guaranteed to work because the generator API can be incompatible at code level.
    4.  Kora BOM: aligns the versions of every Kora module and of the libraries Kora depends on.
    5.  Kora KSP processor: generates the application graph, the controller modules, and the JSON readers/writers during compilation.
    6.  Publishes the contract file and the Swagger UI / Scalar pages from the running application.
    7.  Validation runtime, required because we generate the server with `enableServerValidation`.

!!! warning "The `Gradle` daemon must run on JDK 25 or newer"

    Because `io.koraframework:openapi-generator` lands on the **buildscript** classpath, it is loaded by the `Gradle` JVM rather than by the compiled application.
    Kora is compiled for `JDK 25`, so the `Gradle` daemon must also run on `JDK 25` or newer, otherwise generation fails with `UnsupportedClassVersionError` before any project code is compiled.
    Setting only the project `toolchain` is not enough — the toolchain applies to compilation, not to the `Gradle` JVM itself.

## Modules { #modules }

`OpenApiManagementModule` is what exposes the contract from the running application, and `ValidationModule` supplies the runtime that the generated validation annotations rely on.

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/java/io/koraframework/guide/openapi/httpserver/Application.java`:

    ```java
    package io.koraframework.guide.openapi.httpserver;

    import io.koraframework.application.graph.KoraApplication;
    import io.koraframework.common.annotation.KoraApp;
    import io.koraframework.config.hocon.HoconConfigModule;
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule;
    import io.koraframework.json.common.JsonModule;
    import io.koraframework.logging.logback.LogbackModule;
    import io.koraframework.openapi.management.OpenApiManagementModule;
    import io.koraframework.validation.module.ValidationModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            UndertowPublicHttpServerModule,
            JsonModule,
            LogbackModule,
            ValidationModule,          // <----- Connected module
            OpenApiManagementModule {  // <----- Connected module

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update `src/main/kotlin/io/koraframework/guide/openapi/httpserver/Application.kt`:

    ```kotlin
    package io.koraframework.guide.openapi.httpserver

    import io.koraframework.application.graph.KoraApplication
    import io.koraframework.common.annotation.KoraApp
    import io.koraframework.config.hocon.HoconConfigModule
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule
    import io.koraframework.json.common.JsonModule
    import io.koraframework.logging.logback.LogbackModule
    import io.koraframework.openapi.management.OpenApiManagementModule
    import io.koraframework.validation.module.ValidationModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        UndertowPublicHttpServerModule,
        JsonModule,
        LogbackModule,
        ValidationModule,        // <----- Connected module
        OpenApiManagementModule  // <----- Connected module

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

Notice what is **not** here: there is no module to connect for the generated controller. The generator emits the controller already annotated with `@Component` and `@HttpController`, so it joins the
application graph on its own as soon as its source directory is compiled.

So after this step, we have prepared the application for a contract-first server, but we have not generated anything yet.

## OpenAPI Contract { #openapi-contract }

Now we move the API contract out of Java or Kotlin annotations and into a shared OpenAPI file.

Create `src/main/resources/openapi/user-http-server.yaml`:

??? example "OpenAPI contract"

    ```yaml
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
            '200':
              description: Users returned
              content:
                application/json:
                  schema:
                    type: array
                    items:
                      $ref: '#/components/schemas/UserResponseTO'
            '500':
              description: Internal server error
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/ErrorResponseTO'
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
                  $ref: '#/components/schemas/UserRequestTO'
          responses:
            '201':
              description: User created
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/UserResponseTO'
            '500':
              description: Internal server error
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/ErrorResponseTO'
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
            '200':
              description: User returned
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/UserResponseTO'
            '404':
              description: User not found
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
                  $ref: '#/components/schemas/UserRequestTO'
          responses:
            '200':
              description: User updated
              headers:
                X-Updated-At:
                  required: true
                  schema:
                    type: string
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/UserResponseTO'
            '404':
              description: User not found
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
            '204':
              description: User deleted
            '404':
              description: User not found
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

Two details in this contract will show up directly in the generated code, so they are worth noticing now:

- every operation has an `operationId`, and that value becomes the generated method name and the prefix of every generated response type
- every operation carries the `users` tag, and that tag becomes the `Users` part of `UsersApiController`, `UsersApiDelegate`, and `UsersApiResponses`

That is an important teaching point. Contract-first development is not about changing the business idea. It is about moving the transport contract into a formal, shareable source of truth.

## OpenAPI Code Generation { #openapi-codegen }

The detailed server generation options are described in [OpenAPI Codegen: Server](../documentation/openapi-codegen.md#server).

Now tell Gradle how to generate the server code from that contract.

===! ":fontawesome-brands-java: `Java`"

    Update `build.gradle`:

    ```groovy
    def openApiGenerateUsersHttpServer = tasks.register("openApiGenerateUsersHttpServer", GenerateTask) {
        generatorName = "kora" //(1)!
        group = "openapi tools"
        inputSpec = layout.projectDirectory.file("src/main/resources/openapi/user-http-server.yaml") //(2)!
        outputDir = layout.buildDirectory.dir("generated/user-http-server") //(3)!
        def corePackage = "io.koraframework.guide.openapi.httpserver.user"
        apiPackage = "${corePackage}.api" //(4)!
        modelPackage = "${corePackage}.model" //(5)!
        invokerPackage = "${corePackage}.invoker" //(6)!
        configOptions = [
                mode                  : "java-server", //(7)!
                enableServerValidation: "true", //(8)!
        ]
    }

    sourceSets.main {
        java.srcDirs += openApiGenerateUsersHttpServer.get().outputDir //(9)!
    }

    compileJava.dependsOn openApiGenerateUsersHttpServer //(10)!
    ```

    1.  Selects the Kora generator instead of one of the stock `OpenAPI Generator` generators.
    2.  Path to the OpenAPI file used to create classes.
    3.  Directory where generated files are created.
    4.  Package for the generated controller, delegate, response wrappers, and mappers.
    5.  Package for the generated models.
    6.  Auxiliary generator package.
    7.  Generation mode. `java-server` is one of the four supported modes: `java-client`, `java-server`, `kotlin-client`, `kotlin-server`.
    8.  Translates the schema constraints (`minLength`, `maxLength`, `minimum`, `maximum`, `pattern`) into Kora validation annotations on the generated models and controller.
    9.  Register generated classes as project source code.
    10. Make compilation depend on generation: generate first, compile after.

=== ":simple-kotlin: `Kotlin`"

    Update `build.gradle.kts`:

    ```kotlin
    val openApiGenerateUsersHttpServer = tasks.register<GenerateTask>("openApiGenerateUsersHttpServer") {
        generatorName = "kora" //(1)!
        group = "openapi tools"
        inputSpec.set(layout.projectDirectory.file("src/main/resources/openapi/user-http-server.yaml")) //(2)!
        outputDir.set(layout.buildDirectory.dir("generated/user-http-server")) //(3)!
        val corePackage = "io.koraframework.guide.openapi.httpserver.user"
        apiPackage = "${corePackage}.api" //(4)!
        modelPackage = "${corePackage}.model" //(5)!
        invokerPackage = "${corePackage}.invoker" //(6)!
        configOptions = mapOf(
            "mode" to "kotlin-server", //(7)!
            "enableServerValidation" to "true", //(8)!
        )
    }

    kotlin.sourceSets.main { kotlin.srcDir(openApiGenerateUsersHttpServer.get().outputDir) } //(9)!

    tasks.matching { it.name.startsWith("ksp") }.configureEach { //(10)!
        dependsOn(openApiGenerateUsersHttpServer)
    }
    ```

    1.  Selects the Kora generator instead of one of the stock `OpenAPI Generator` generators.
    2.  Path to the OpenAPI file used to create classes.
    3.  Directory where generated files are created.
    4.  Package for the generated controller, delegate, response wrappers, and mappers.
    5.  Package for the generated models.
    6.  Auxiliary generator package.
    7.  Generation mode. `kotlin-server` is one of the four supported modes: `java-client`, `java-server`, `kotlin-client`, `kotlin-server`.
    8.  Translates the schema constraints (`minLength`, `maxLength`, `minimum`, `maximum`, `pattern`) into Kora validation annotations on the generated models and controller.
    9.  Register generated classes as project source code.
    10. `KSP` must see generated sources, so every `ksp*` task depends on generation: generate first, process and compile after.

At this step, four details matter most:

- generated code will be written into `build/generated/user-http-server`
- generated types will live under `io.koraframework.guide.openapi.httpserver.user`
- generation happens automatically before compilation
- generated code is **build output**, so it never goes into version control and never gets edited by hand

This is the build step that turns a static YAML contract into real server-side code.

## Generated Output { #generated-output }

Run:

```bash
./gradlew clean classes
```

Now look at the generated files:

===! ":fontawesome-brands-java: `Java`"

    - `build/generated/user-http-server/io/koraframework/guide/openapi/httpserver/user/api/UsersApiController.java`
    - `build/generated/user-http-server/io/koraframework/guide/openapi/httpserver/user/api/UsersApiDelegate.java`
    - `build/generated/user-http-server/io/koraframework/guide/openapi/httpserver/user/api/UsersApiResponses.java`
    - `build/generated/user-http-server/io/koraframework/guide/openapi/httpserver/user/api/UsersApiServerRequestMappers.java`
    - `build/generated/user-http-server/io/koraframework/guide/openapi/httpserver/user/api/UsersApiServerResponseMappers.java`
    - `build/generated/user-http-server/io/koraframework/guide/openapi/httpserver/user/model/UserRequestTO.java`
    - `build/generated/user-http-server/io/koraframework/guide/openapi/httpserver/user/model/UserResponseTO.java`
    - `build/generated/user-http-server/io/koraframework/guide/openapi/httpserver/user/model/ErrorResponseTO.java`

=== ":simple-kotlin: `Kotlin`"

    - `build/generated/user-http-server/io/koraframework/guide/openapi/httpserver/user/api/UsersApiController.kt`
    - `build/generated/user-http-server/io/koraframework/guide/openapi/httpserver/user/api/UsersApiDelegate.kt`
    - `build/generated/user-http-server/io/koraframework/guide/openapi/httpserver/user/api/UsersApiResponses.kt`
    - `build/generated/user-http-server/io/koraframework/guide/openapi/httpserver/user/api/UsersApiServerRequestMappers.kt`
    - `build/generated/user-http-server/io/koraframework/guide/openapi/httpserver/user/api/UsersApiServerResponseMappers.kt`
    - `build/generated/user-http-server/io/koraframework/guide/openapi/httpserver/user/model/UserRequestTO.kt`
    - `build/generated/user-http-server/io/koraframework/guide/openapi/httpserver/user/model/UserResponseTO.kt`
    - `build/generated/user-http-server/io/koraframework/guide/openapi/httpserver/user/model/ErrorResponseTO.kt`

The generated server introduces several important abstractions, and it helps a lot to inspect them one by one instead of treating generation as a black box.

### 1. `UsersApiDelegate` { #1-usersapidelegate }

This is the interface you implement in your own application code.

Here is a shortened version of the generated delegate:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface UsersApiDelegate {

        @HttpRoute(method = "POST", path = "/users")
        UsersApiResponses.CreateUserApiResponse createUser(
            UserRequestTO userRequestTO
        ) throws Exception;

        @HttpRoute(method = "GET", path = "/users/{userId}")
        UsersApiResponses.GetUserApiResponse getUser(
            String userId
        ) throws Exception;

        @HttpRoute(method = "GET", path = "/users")
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

        @HttpRoute(method = "POST", path = "/users")
        fun createUser(
            userRequestTO: UserRequestTO
        ): UsersApiResponses.CreateUserApiResponse

        @HttpRoute(method = "GET", path = "/users/{userId}")
        fun getUser(
            userId: String
        ): UsersApiResponses.GetUserApiResponse

        @HttpRoute(method = "GET", path = "/users")
        fun getUsers(
            page: Int?,
            size: Int?,
            sort: String?
        ): UsersApiResponses.GetUsersApiResponse
    }
    ```

This is the first big conceptual shift relative to [HTTP Server](http-server.md).

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

Two signature details are easy to miss and easy to get wrong later:

- delegate methods are declared `throws Exception` in `Java`, so an implementation may throw freely; narrowing the `throws` clause in your `@Override` is allowed and usually cleaner
- optional query parameters arrive as `null`, **not** as the `default` written in the contract — an OpenAPI `default` documents the value for readers of the contract, it does not make the generated
  server substitute it. Applying `page = 0`, `size = 10`, and `sort = "name"` is the delegate's job

### 2. `UsersApiController` { #2-usersapicontroller }

This is the generated HTTP controller that Kora puts into the application graph.

You do not edit it manually, and you usually do not need to understand every line inside it. What matters is its responsibility:

- receive the HTTP request
- validate and map transport data according to the contract
- call the corresponding delegate method
- turn the returned generated response wrapper into an actual HTTP response

The class is generated with `@Component` and `@HttpController`, so it registers itself in the graph without any module wiring on your side. Its only constructor dependency is `UsersApiDelegate`, which
is why the build fails at compile time — not at startup — if you forget to implement the delegate.

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

The OpenAPI contract says that `GET /users/{userId}` may produce:

- `200` with a `UserResponseTO` body
- `404` with an `ErrorResponseTO` body
- `500` with an `ErrorResponseTO` body

So the generator creates one sealed response family that models those three outcomes.

Three naming rules explain every wrapper you will meet:

- the family is `<OperationId>ApiResponse`, so `getUser` gives `GetUserApiResponse`
- each variant is `<OperationId><Code>ApiResponse`, so `404` gives `GetUser404ApiResponse`
- a response body becomes the `content` component; declared response **headers** become extra components, which is why `updateUser` produces `UpdateUser200ApiResponse(content, xUpdatedAt)`

A `204` response has no body, so `DeleteUser204ApiResponse` is simply an empty record. And when an operation declares only one response, there is no sealed wrapper at all — `<OperationId>ApiResponse`
is that single record directly.

That is important because the contract is not only about request and success payloads. It also describes the allowed error shapes, and the server-side generated code preserves that information as real
`Java` or `Kotlin` types.

### 4. Generated Models { #4-generated-models }

The generator also creates contract-layer transport models such as:

- `UserRequestTO`
- `UserResponseTO`
- `ErrorResponseTO`

`Java` models are `record` types with generated `@Json` readers and writers; `Kotlin` models are `data class` types. Because `enableServerValidation` is on, the contract constraints travel with them —
`minLength: 1` / `maxLength: 100` on `UserRequestTO.name` becomes a `@Size` annotation, and the model itself is marked `@Valid`.

These generated models belong to the OpenAPI boundary, not to your internal domain or service layer.

That is why the guide still keeps internal DTOs like `UserRequest` and `UserResponse` inside the application code. The delegate is the place where those two worlds meet:

- generated OpenAPI transport models on one side
- internal application models on the other

Keeping those layers separate makes future refactoring much safer. You can evolve internal code without pretending that generated transport types are your whole domain model.

Your own handwritten DTOs that cross a JSON boundary still need `@Json`, because they are not produced by the generator and Kora has to be told to build their mappers during normal annotation
processing.

!!! warning "Use named arguments for generated `Kotlin` models"

    Generated `Kotlin` constructors list required properties first and give every optional property a default value.
    Adding one property to the contract can therefore shift positions, and a positional call such as `UserRequestTO("john@example.com", "John")` still compiles while silently swapping two `String` values.
    Construct generated models with named arguments: `UserRequestTO(name = "John Doe", email = "john@example.com")`.

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

This is the main "aha" moment of the guide: OpenAPI generation does not just save typing. It turns the HTTP contract into a set of explicit server-side abstractions that guide your implementation.

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

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/io/koraframework/guide/openapi/httpserver/controller/UserApiDelegateImpl.java`:

    ```java
    package io.koraframework.guide.openapi.httpserver.controller;

    import java.time.Instant;
    import java.time.ZoneOffset;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.openapi.httpserver.user.api.UsersApiDelegate;
    import io.koraframework.guide.openapi.httpserver.user.api.UsersApiResponses;
    import io.koraframework.guide.openapi.httpserver.user.model.ErrorResponseTO;
    import io.koraframework.guide.openapi.httpserver.user.model.UserRequestTO;
    import io.koraframework.guide.openapi.httpserver.user.model.UserResponseTO;
    import io.koraframework.guide.openapi.httpserver.dto.UserRequest;
    import io.koraframework.guide.openapi.httpserver.dto.UserResponse;
    import io.koraframework.guide.openapi.httpserver.service.UserService;

    @Component //(1)!
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
            return new UsersApiResponses.DeleteUserApiResponse.DeleteUser204ApiResponse(); //(2)!
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
            int effectivePage = page == null ? 0 : page; //(3)!
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
                    Instant.now().toString() //(4)!
            );
        }

        private UserResponseTO toGenerated(UserResponse user) { //(5)!
            return new UserResponseTO(
                    user.id(),
                    user.name(),
                    user.email(),
                    user.createdAt().atOffset(ZoneOffset.UTC)
            );
        }

        private ErrorResponseTO notFound(String userId) {
            return new ErrorResponseTO("User with id '" + userId + "' was not found");
        }
    }
    ```

    1.  The delegate is an ordinary Kora component; the generated controller receives it through constructor injection.
    2.  `204 No Content` has no body in the contract, so the generated record has no components.
    3.  An OpenAPI `default` is documentation, not server behavior: absent query parameters arrive as `null` and the delegate applies the defaults.
    4.  The declared `X-Updated-At` response header becomes the second component of the `200` wrapper.
    5.  `format: date-time` maps to `OffsetDateTime`, so the internal `LocalDateTime` is converted at the boundary.

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/io/koraframework/guide/openapi/httpserver/controller/UserApiDelegateImpl.kt`:

    ```kotlin
    package io.koraframework.guide.openapi.httpserver.controller

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.openapi.httpserver.dto.UserRequest
    import io.koraframework.guide.openapi.httpserver.dto.UserResponse
    import io.koraframework.guide.openapi.httpserver.service.UserService
    import io.koraframework.guide.openapi.httpserver.user.api.UsersApiDelegate
    import io.koraframework.guide.openapi.httpserver.user.api.UsersApiResponses
    import io.koraframework.guide.openapi.httpserver.user.model.ErrorResponseTO
    import io.koraframework.guide.openapi.httpserver.user.model.UserRequestTO
    import io.koraframework.guide.openapi.httpserver.user.model.UserResponseTO
    import java.time.Instant
    import java.time.ZoneOffset

    @Component //(1)!
    class UserApiDelegateImpl(
        private val userService: UserService
    ) : UsersApiDelegate {

        override fun createUser(userRequest: UserRequestTO): UsersApiResponses.CreateUserApiResponse {
            val created = userService.createUser(UserRequest(userRequest.name, userRequest.email))
            return UsersApiResponses.CreateUserApiResponse.CreateUser201ApiResponse(toGenerated(created))
        }

        override fun deleteUser(userId: String): UsersApiResponses.DeleteUserApiResponse {
            if (userService.getUser(userId) == null) {
                return UsersApiResponses.DeleteUserApiResponse.DeleteUser404ApiResponse(
                    notFound(userId)
                )
            }

            userService.deleteUser(userId)
            return UsersApiResponses.DeleteUserApiResponse.DeleteUser204ApiResponse() //(2)!
        }

        override fun getUser(userId: String): UsersApiResponses.GetUserApiResponse {
            val user = userService.getUser(userId)
            return if (user == null) {
                UsersApiResponses.GetUserApiResponse.GetUser404ApiResponse(notFound(userId))
            } else {
                UsersApiResponses.GetUserApiResponse.GetUser200ApiResponse(toGenerated(user))
            }
        }

        override fun getUsers(page: Int?, size: Int?, sort: String?): UsersApiResponses.GetUsersApiResponse {
            val effectivePage = page ?: 0 //(3)!
            val effectiveSize = size ?: 10
            val effectiveSort = sort ?: "name"
            val users = userService.getUsers(effectivePage, effectiveSize, effectiveSort)
                .map(::toGenerated)
            return UsersApiResponses.GetUsersApiResponse.GetUsers200ApiResponse(users)
        }

        override fun updateUser(userId: String, userRequest: UserRequestTO): UsersApiResponses.UpdateUserApiResponse {
            if (userService.getUser(userId) == null) {
                return UsersApiResponses.UpdateUserApiResponse.UpdateUser404ApiResponse(
                    notFound(userId)
                )
            }

            val updated = userService.updateUser(userId, UserRequest(userRequest.name, userRequest.email))
            return UsersApiResponses.UpdateUserApiResponse.UpdateUser200ApiResponse(
                toGenerated(updated),
                Instant.now().toString() //(4)!
            )
        }

        private fun toGenerated(user: UserResponse): UserResponseTO { //(5)!
            return UserResponseTO(
                id = user.id,
                name = user.name,
                email = user.email,
                createdAt = user.createdAt.atOffset(ZoneOffset.UTC)
            )
        }

        private fun notFound(userId: String): ErrorResponseTO {
            return ErrorResponseTO("User with id '$userId' was not found")
        }
    }
    ```

    1.  The delegate is an ordinary Kora component; the generated controller receives it through constructor injection.
    2.  `204 No Content` has no body in the contract, so the generated class has no properties.
    3.  An OpenAPI `default` is documentation, not server behavior: absent query parameters arrive as `null` and the delegate applies the defaults.
    4.  The declared `X-Updated-At` response header becomes the second component of the `200` wrapper.
    5.  `format: date-time` maps to `OffsetDateTime`, so the internal `LocalDateTime` is converted at the boundary — and named arguments keep the four `String`-ish values from being swapped.

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

For the full configuration reference, see [HTTP Server](../documentation/http-server.md#configuration), [OpenAPI Management](../documentation/openapi-management.md#configuration)
and [Logging SLF4J](../documentation/logging-slf4j.md).

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
      port = 8080 //(1)!
      system.port = 8085 //(2)!
      telemetry.logging.enabled = true //(3)!
    }

    openapi {
      management {
        enabled = true //(4)!
        files = [ "openapi/user-http-server.yaml" ] //(5)!
        path = "/openapi" //(6)!
        swaggerui {
          enabled = true //(7)!
          path = "/swagger-ui" //(8)!
        }
      }
    }

    logging.levels {
      "root" = "WARN" //(9)!
      "io.koraframework" = "INFO" //(10)!
      "io.koraframework.guide.openapi.httpserver" = "INFO" //(11)!
    }
    ```

    1.  Public HTTP port used by application endpoints (default: `8080`).
    2.  System HTTP port used by probes, metrics, and management endpoints (default: `8085`).
    3.  Enables request logging for the public HTTP server (default: `false`).
    4.  Enables OpenAPI publishing (default: `false`).
    5.  Classpath resources to publish. This is a **list**, even for one file.
    6.  Path where the contract is served (default: `/openapi`).
    7.  Enables the Swagger UI page (default: `false`).
    8.  Path of the Swagger UI page (default: `/swagger-ui`).
    9.  Log level for the root logger.
    10. Log level for Kora framework loggers.
    11. Log level for the application package.

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      port: 8080 #(1)!
      system:
        port: 8085 #(2)!
      telemetry:
        logging:
          enabled: true #(3)!
    openapi:
      management:
        enabled: true #(4)!
        files: [ "openapi/user-http-server.yaml" ] #(5)!
        path: "/openapi" #(6)!
        swaggerui:
          enabled: true #(7)!
          path: "/swagger-ui" #(8)!
    logging:
      levels:
        root: "WARN" #(9)!
        "io.koraframework": "INFO" #(10)!
        "io.koraframework.guide.openapi.httpserver": "INFO" #(11)!
    ```

    1.  Public HTTP port used by application endpoints (default: `8080`).
    2.  System HTTP port used by probes, metrics, and management endpoints (default: `8085`).
    3.  Enables request logging for the public HTTP server (default: `false`).
    4.  Enables OpenAPI publishing (default: `false`).
    5.  Classpath resources to publish. This is a **list**, even for one file.
    6.  Path where the contract is served (default: `/openapi`).
    7.  Enables the Swagger UI page (default: `false`).
    8.  Path of the Swagger UI page (default: `/swagger-ui`).
    9.  Log level for the root logger.
    10. Log level for Kora framework loggers.
    11. Log level for the application package.

This gives us two very practical endpoints:

- `/openapi` returns the OpenAPI document
- `/swagger-ui` gives an interactive UI for exploring and testing the API

Both are served by the **public** HTTP server on `httpServer.port`, not on the system port, because the management module registers ordinary request handlers. If you prefer a lighter viewer page,
`openapi.management.scalar.enabled = true` publishes [Scalar](https://scalar.com/) on `/scalar` from the same contract; both pages ship inside the module as self-contained resources, so neither needs
internet access or a CDN.

This is one of the biggest benefits of contract-first development. The documentation is not something you write later. It is part of the same build that generates the server layer.

## Check Application { #check-app }

```bash
./gradlew clean classes
./gradlew test
./gradlew run
```

`classes` is the meaningful first check here: it runs OpenAPI generation, then the annotation processor or KSP, and fails at compile time if the delegate does not match the contract.

Public API checks:

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com"}'

curl http://localhost:8080/users/1
curl "http://localhost:8080/users?page=0&size=10&sort=name"

curl -i -X PUT http://localhost:8080/users/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Name", "email": "updated@example.com"}'

curl -X DELETE http://localhost:8080/users/1
```

The `-i` flag on the update call is worth keeping: it shows the `X-Updated-At` response header that the contract declares and the delegate fills in.

Contract checks:

```bash
curl http://localhost:8080/openapi
```

Open in your browser:

```text
http://localhost:8080/swagger-ui
```

System API checks:

```bash
curl http://localhost:8085/system/readiness
# Expected output: OK
curl http://localhost:8085/system/liveness
# Expected output: OK
```

At this point, the application behaves like the familiar `http-server` CRUD service, but the HTTP layer is now driven by the OpenAPI contract.

## Delegate Test { #delegate-test }

Because the delegate is an ordinary component, it can be tested without starting an HTTP client at all — `@KoraAppTest` builds the real graph and injects the generated interface.

===! ":fontawesome-brands-java: `Java`"

    Create `src/test/java/io/koraframework/guide/openapi/httpserver/OpenApiHttpServerAppTest.java`:

    ```java
    package io.koraframework.guide.openapi.httpserver;

    import static org.junit.jupiter.api.Assertions.assertEquals;
    import static org.junit.jupiter.api.Assertions.assertInstanceOf;
    import static org.junit.jupiter.api.Assertions.assertNotNull;

    import org.junit.jupiter.api.Test;
    import io.koraframework.guide.openapi.httpserver.user.api.UsersApiDelegate;
    import io.koraframework.guide.openapi.httpserver.user.api.UsersApiResponses;
    import io.koraframework.guide.openapi.httpserver.user.model.UserRequestTO;
    import io.koraframework.test.extension.junit5.KoraAppTest;
    import io.koraframework.test.extension.junit5.TestComponent;

    @KoraAppTest(Application.class)
    class OpenApiHttpServerAppTest {

        @TestComponent
        private UsersApiDelegate usersApiDelegate; //(1)!

        @Test
        void crudFlowWorksThroughDelegate() throws Exception {
            var createResponse = this.usersApiDelegate.createUser(new UserRequestTO("John Doe", "john@example.com"));
            var create201 = assertInstanceOf(UsersApiResponses.CreateUserApiResponse.CreateUser201ApiResponse.class, createResponse); //(2)!
            assertNotNull(create201.content());
            assertEquals("John Doe", create201.content().name());

            var getUserResponse = this.usersApiDelegate.getUser(create201.content().id());
            var getUser200 = assertInstanceOf(UsersApiResponses.GetUserApiResponse.GetUser200ApiResponse.class, getUserResponse);
            assertEquals("john@example.com", getUser200.content().email());

            var getUsersResponse = this.usersApiDelegate.getUsers(0, 10, "name");
            var getUsers200 = assertInstanceOf(UsersApiResponses.GetUsersApiResponse.GetUsers200ApiResponse.class, getUsersResponse);
            assertEquals(1, getUsers200.content().size());

            var updateResponse = this.usersApiDelegate.updateUser(create201.content().id(), new UserRequestTO("John Updated", "john.updated@example.com"));
            var update200 = assertInstanceOf(UsersApiResponses.UpdateUserApiResponse.UpdateUser200ApiResponse.class, updateResponse);
            assertEquals("John Updated", update200.content().name());
            assertNotNull(update200.xUpdatedAt()); //(3)!

            var deleteResponse = this.usersApiDelegate.deleteUser(create201.content().id());
            assertInstanceOf(UsersApiResponses.DeleteUserApiResponse.DeleteUser204ApiResponse.class, deleteResponse);

            var getAfterDeleteResponse = this.usersApiDelegate.getUser(create201.content().id());
            assertInstanceOf(UsersApiResponses.GetUserApiResponse.GetUser404ApiResponse.class, getAfterDeleteResponse);
        }
    }
    ```

    1.  Injects the generated interface, so the test resolves your `@Component` implementation through the real graph.
    2.  Asserting on the response subtype is the server-side equivalent of asserting on a status code.
    3.  The declared `X-Updated-At` header is a component of the wrapper, so it is assertable like any other value.

=== ":simple-kotlin: `Kotlin`"

    Create `src/test/kotlin/io/koraframework/guide/openapi/httpserver/OpenApiHttpServerAppTest.kt`:

    ```kotlin
    package io.koraframework.guide.openapi.httpserver

    import org.junit.jupiter.api.Assertions.assertEquals
    import org.junit.jupiter.api.Assertions.assertInstanceOf
    import org.junit.jupiter.api.Assertions.assertNotNull
    import org.junit.jupiter.api.Test
    import io.koraframework.guide.openapi.httpserver.user.api.UsersApiDelegate
    import io.koraframework.guide.openapi.httpserver.user.api.UsersApiResponses
    import io.koraframework.guide.openapi.httpserver.user.model.UserRequestTO
    import io.koraframework.test.extension.junit5.KoraAppTest
    import io.koraframework.test.extension.junit5.TestComponent

    @KoraAppTest(Application::class)
    class OpenApiHttpServerAppTest {

        @TestComponent
        lateinit var usersApiDelegate: UsersApiDelegate //(1)!

        @Test
        fun crudFlowWorksThroughDelegate() {
            val createResponse = usersApiDelegate.createUser(UserRequestTO(name = "John Doe", email = "john@example.com"))
            val create201 = assertInstanceOf(
                UsersApiResponses.CreateUserApiResponse.CreateUser201ApiResponse::class.java,
                createResponse
            ) //(2)!
            assertNotNull(create201.content)
            assertEquals("John Doe", create201.content.name)

            val getUserResponse = usersApiDelegate.getUser(create201.content.id)
            val getUser200 =
                assertInstanceOf(UsersApiResponses.GetUserApiResponse.GetUser200ApiResponse::class.java, getUserResponse)
            assertEquals("john@example.com", getUser200.content.email)

            val getUsersResponse = usersApiDelegate.getUsers(0, 10, "name")
            val getUsers200 =
                assertInstanceOf(UsersApiResponses.GetUsersApiResponse.GetUsers200ApiResponse::class.java, getUsersResponse)
            assertEquals(1, getUsers200.content.size)

            val updateResponse = usersApiDelegate.updateUser(
                create201.content.id,
                UserRequestTO(name = "John Updated", email = "john.updated@example.com")
            )
            val update200 = assertInstanceOf(
                UsersApiResponses.UpdateUserApiResponse.UpdateUser200ApiResponse::class.java,
                updateResponse
            )
            assertEquals("John Updated", update200.content.name)
            assertNotNull(update200.xUpdatedAt) //(3)!

            val deleteResponse = usersApiDelegate.deleteUser(create201.content.id)
            assertInstanceOf(UsersApiResponses.DeleteUserApiResponse.DeleteUser204ApiResponse::class.java, deleteResponse)

            val getAfterDeleteResponse = usersApiDelegate.getUser(create201.content.id)
            assertInstanceOf(UsersApiResponses.GetUserApiResponse.GetUser404ApiResponse::class.java, getAfterDeleteResponse)
        }
    }
    ```

    1.  Injects the generated interface, so the test resolves your `@Component` implementation through the real graph.
    2.  Asserting on the response subtype is the server-side equivalent of asserting on a status code.
    3.  The declared `X-Updated-At` header is a property of the wrapper, so it is assertable like any other value.

Run:

```bash
./gradlew test
```

That test validates create, get by id, list, update, delete, and `404` after delete. This is a useful checkpoint because it proves that the generated API layer and your delegate implementation are
wired together correctly.

## Best Practices { #best-practices }

- Keep the OpenAPI contract close to the real behavior of the application. The contract should describe reality, not future ideas.
- Keep generated code as build output only. Do not edit or commit files under `build/generated/user-http-server`.
- Keep business logic in services, not in generated classes.
- Use delegates as the transport boundary between generated API types and internal application models.
- Regenerate server code as part of normal builds so the contract and compiled application cannot drift apart.
- Give every operation a stable `operationId`: it is what names the delegate method and every generated response type, so renaming it is a source-level breaking change.
- Apply the OpenAPI `default` values yourself in the delegate, because generated servers hand you `null` for absent optional parameters.

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
- Kora generates server code from OpenAPI in exactly two server modes: `java-server` and `kotlin-server`
- generated controllers and delegates separate transport wiring from application logic
- delegates are a good place to map between generated contract models and internal DTOs
- adding new status codes such as `500` to OpenAPI changes the generated response wrappers too
- `enableServerValidation` turns schema constraints into real validation annotations on generated models
- Swagger UI, Scalar, and the OpenAPI document become a natural part of the application when the contract is built into the project

## Troubleshooting { #troubleshooting }

**Generation fails with `UnsupportedClassVersionError`:**

- The `Gradle` daemon runs on an older JDK than the one Kora is compiled for. The generator is on the buildscript classpath, so the `Gradle` JVM itself must be `JDK 25` or newer.
- Run `./gradlew --stop`, point `org.gradle.java.home` at a JDK 25 installation, then retry.

**Generation fails with "Invalid OpenAPI generator `mode`":**

- Kora 2.0 supports exactly four modes: `java-client`, `java-server`, `kotlin-client`, `kotlin-server`.
- The reactive and `suspend` modes from earlier versions no longer exist; generated server and client code is synchronous.

**Code generation does not run:**

Check that:

- `org.openapi.generator` is applied and `GenerateTask` is imported
- `generatorName = "kora"` is set on the task
- in `Java`, `compileJava.dependsOn openApiGenerateUsersHttpServer` is configured
- in `Kotlin`, every `ksp*` task depends on the generation task

**The application cannot find generated classes:**

Check that the generated source directory is added to the main source set:

- `build/generated/user-http-server`

Also verify that your package settings match your imports:

- `io.koraframework.guide.openapi.httpserver.user.api`
- `io.koraframework.guide.openapi.httpserver.user.model`

**Swagger UI is not available:**

Make sure that:

- `OpenApiManagementModule` is included in `Application`
- `openapi.management.enabled = true` and `openapi.management.swaggerui.enabled = true`
- `openapi.management.files` lists the contract, and the value is a **list** — the key is `files`, not `file`
- you are calling the **public** port `8080`, not the system port `8085`

**Delegate is not discovered by Kora:**

Make sure that:

- the delegate is annotated with `@Component`
- it implements the generated `UsersApiDelegate`
- it imports the generated package you configured in the build file

**The manual controller conflicts with the generated server:**

In this application variant, the handwritten user controller should not be kept alongside the generated server controller. Two handlers on the same method and path is a graph-build failure. Once you
move to the OpenAPI-generated transport layer, the delegate becomes the main implementation point for HTTP behavior.

**A response wrapper variant is missing:**

Generated response variants only exist for status codes that are explicitly listed in the OpenAPI contract.

So if you expect a generated `500` abstraction such as `GetUser500ApiResponse`, make sure that `500` is present in the `responses` section of that operation in `user-http-server.yaml`.

**Paging and sorting behave as if the contract defaults were ignored:**

They were. An OpenAPI `default` on a query parameter is documentation for readers of the contract; the generated server passes `null` for an absent parameter, so the delegate must apply the default.

## What's Next? { #whats-next }

- [HTTP Client](http-client.md) if you have not built a client app yet.
- [OpenAPI HTTP Client](openapi-http-client.md) after HTTP Client, to generate a client from the same contract.
- [HTTP Server Advanced](http-server-advanced.md) before [OpenAPI HTTP Server Advanced](openapi-http-server-advanced.md), because the advanced OpenAPI guide combines both tracks.
- [Validation](validation.md) to compare handwritten validation with spec-driven validation.

## Help { #help }

If you get stuck:

- compare with [Kora Java OpenAPI HTTP Server App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-openapi-http-server-app) and [Kora Kotlin OpenAPI HTTP Server App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-openapi-http-server-app)
- compare with [HTTP Server](http-server.md) to see what the generated controller replaced
- check the [OpenAPI Codegen documentation](../documentation/openapi-codegen.md)
- check the [OpenAPI Management documentation](../documentation/openapi-management.md)
