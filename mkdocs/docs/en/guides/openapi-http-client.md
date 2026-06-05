---
search:
  exclude: true
title: Contract-First HTTP Client with OpenAPI
summary: Continue the HTTP Client guide by replacing the handwritten declarative client with an OpenAPI-generated client
tags: openapi, http-client, contract-first, code-generation, swagger
---

# Contract-First HTTP Client with OpenAPI { #contract-first-http-client }

This guide introduces contract-first HTTP clients with Kora and OpenAPI. It covers how an OpenAPI specification generates a typed client, how generated request and response models replace handwritten
transport interfaces, and how the client is wired into a Kora application service. You will also see how one API contract can describe both sides of an HTTP integration without duplicating method
signatures by hand.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java OpenAPI HTTP Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-openapi-http-client-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin OpenAPI HTTP Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-openapi-http-client-app).

## What You'll Build { #youll-build }

You will rebuild the client application from [HTTP Client with Kora](http-client.md), but in a contract-first style:

- the remote user API will be described by the same `user-http-server.yaml` contract from [openapi-http-server.md](openapi-http-server.md)
- Kora will generate a typed client interface from that contract
- generated request and response models will replace the handwritten client DTOs
- the client application will still expose one aggregate endpoint for easy manual verification
- tests will run the generated client against a containerized copy of the OpenAPI server application

## What You'll Need { #youll-need }

- JDK 17 or later
- Gradle 7+
- Docker Desktop or another local Docker environment for container-based tests
- A text editor or IDE
- Two terminals if you want to run the server and client manually

## Prerequisites { #prerequisites }

!!! note "Required: Complete OpenAPI HTTP Server Guide"

    This guide assumes you have completed **[HTTP Client with Kora](http-client.md)** and **[Contract-First HTTP Server with OpenAPI](openapi-http-server.md)**.

    If you haven't completed those guides yet, do that first, because they already cover the base HTTP client flow and the OpenAPI server contract that this generated client reuses.

## Overview { #overview }

In the basic HTTP client guide, the workflow looked like this:

1. define `UserApiClient` manually
2. add annotations that describe the remote contract
3. let Kora generate the implementation from that interface
4. inject the client and call the server

That is already a very productive model.

But once the server itself is contract-first, a better next step appears:

1. keep the OpenAPI contract as the source of truth
2. generate the server from that contract
3. generate the client from that same contract
4. let both applications evolve from one shared description

In this guide we will move gradually through that transition:

1. understand why a generated client is useful when you already have a generated server
2. bring the same `user-http-server.yaml` contract into the client-side workflow too
3. configure Kora OpenAPI client generation
4. inspect the generated `UsersApi` interface and generated models
5. replace the handwritten client with the generated one
6. keep the same aggregate verification flow from `http-client.md`
7. configure the generated client
8. run and verify the application
9. test the generated client against the OpenAPI server app

### What Is Contract-First Development? { #contract-first-development }

Before we generate anything, it helps to understand why teams choose this workflow in the first place.

In a traditional code-first approach, developers usually begin with controllers, endpoints, or client interfaces written directly in code, and only later try to document the API. That can work for
small systems, but over time it creates real friction between teams and between applications.

#### The Problem with Code-First APIs { #problem-code-first-apis }

When the contract is not the main source of truth, several problems appear:

- **Documentation drift**: API documentation becomes outdated as code evolves
- **Contract mismatches**: client and server teams build against slightly different understandings of the same API
- **Late validation**: design problems are discovered only during integration testing or after deployment
- **Manual maintenance**: documentation, SDKs, examples, and tests must all be updated separately
- **Communication gaps**: teams spend time clarifying behavior in chats, meetings, and tickets instead of relying on one shared contract

For a client application this is especially painful. A handwritten client may still compile even though the remote API has already changed in a subtle but breaking way.

#### The Contract-First Solution { #contract-first-solution }

Contract-first development inverts that process.

Instead of saying "the code defines the API," we say "the contract defines the code." The OpenAPI specification becomes the single source of truth that both the server and the client must follow.

That means:

- the server is generated from the contract or validated against it
- the client is generated from the same contract
- documentation is derived from that same contract too

So instead of maintaining several parallel descriptions of the API, you maintain one shared contract and let tooling do the repetitive synchronization work.

#### Team Workflow Changes { #team-workflow-changes }

Contract-first development is not only a build trick. It changes how teams collaborate.

1. **Design before implementation**
   API design happens at the specification level first, so the shape of the API can be reviewed before production code appears.
   That makes it easier to validate paths, payloads, statuses, and naming while the cost of change is still low.

2. **Automated consistency**
   When both server and client are generated from the same specification, the chance of transport-level drift drops sharply.
   You do not need to manually keep route definitions, DTO fields, and expected responses synchronized in two different codebases.

3. **Better collaboration across roles**
   Backend engineers, frontend engineers, QA, and product stakeholders can all reason about the same contract.
   The OpenAPI file becomes a shared language instead of implementation details being hidden inside one application.

4. **Tooling ecosystem around one contract**
   The same contract can drive:
    - generated clients
    - generated servers
    - Swagger UI
    - validation behavior
    - mock servers
    - contract-driven tests

5. **Safer long-term evolution**
   When the contract changes, the impact becomes visible immediately.
   Breaking changes can be reviewed at the contract level instead of being discovered accidentally when another team updates too late.

#### Why This Matters for the Client { #matters-client }

In this guide, we are looking at contract-first development from the client perspective.

That changes the value proposition a little.

The goal here is not only "generate code because we can." The real goal is:

- to stop duplicating the same transport contract in a handwritten client interface
- to make the client follow the exact same OpenAPI document as the server
- to let generated models and response wrappers represent API behavior more explicitly

That is why this guide comes after both `http-client.md` and `openapi-http-server.md`.

You first learn:

- how a handwritten declarative client works
- how an OpenAPI-driven server works

and only then combine those ideas into one shared contract-first integration flow.

#### Kora's Contract-First Advantage { #koras-contract-first-advantage }

Kora makes this especially practical because the generated client is not a throwaway SDK. It integrates naturally with the rest of the framework:

- generated clients are wired through Kora dependency injection
- configuration is still handled through normal Kora config paths
- JSON mapping is still handled by Kora's generated mappers
- response-code mapping is generated explicitly through typed response wrappers
- the generated client still behaves like a normal Kora dependency in your application graph

So the result still feels like a Kora application, not like an external codegen tool bolted onto the side.

### Why One Contract { #one-contract }

The basic client guide already showed that a handwritten declarative client is much nicer than low-level HTTP request code. But handwritten declarative clients still have one long-term risk:

- the client and server contracts can slowly drift apart

For example, one side might change:

- a response status
- a DTO field name
- a path parameter
- a required request property

If that contract lives only in handwritten code, those mismatches are often discovered late, during integration testing or after deployment.

A contract-first workflow reduces that risk. The OpenAPI file becomes the shared contract, and both sides are generated from it.

That gives us several practical benefits:

- the server and client describe the same routes and models
- response wrappers are generated consistently
- request and response model changes start from one contract file
- the client no longer needs its own handwritten transport DTOs

So this guide is not about introducing a completely different architecture. It is about taking the client app from `http-client.md` and making it depend on the same contract the server already uses.

## OpenAPI Contract { #openapi-contract }

The most important decision in this guide is very simple:

- do **not** invent a second client-only contract
- do **not** duplicate the YAML by hand with small differences
- use the same `user-http-server.yaml` from [openapi-http-server.md](openapi-http-server.md)

That is exactly what the runnable guide app does. Its build points to the contract from the sibling server module:

```text
../guide-openapi-http-server-app/src/main/resources/openapi/user-http-server.yaml
```

That file already defines the user API:

- `POST /users`
- `GET /users/{userId}`
- `GET /users`
- `PUT /users/{userId}`
- `DELETE /users/{userId}`

and it already contains the same transport models:

- `UserRequestTO`
- `UserResponseTO`

This is the key lesson of the guide. Contract-first development works best when the client and server truly share one contract, not two almost-identical copies.

## Contract to Client { #contract-client }

Even though the OpenAPI file was already created in [openapi-http-server.md](openapi-http-server.md), it is worth pausing here and looking at it again from the client point of view.

We are not creating a new client-specific specification.

We are using the exact same HTTP OpenAPI contract that the server guide introduced. That is the whole point of the workflow:

- one shared contract
- one server generated from it
- one client generated from it

So in this guide, when we say "describe the API in OpenAPI", we really mean "reuse the same OpenAPI description that already became the source of truth in the server guide."

The shared contract looks like this:

??? example "OpenAPI contract"

    ```yaml title="src/main/resources/openapi/user-http-server.yaml"
    openapi: 3.0.3
    info:
        title: User Management API
        description: Contract-first version of the HTTP Server guide API
        version: 1.0.0
    tags:
        -   name: users
            description: User management operations
    paths:
        /users:
            get:
                tags:
                    - users
                operationId: getUsers
                summary: Get users
                parameters:
                    -   name: page
                        in: query
                        required: false
                        schema:
                            type: integer
                            minimum: 0
                            default: 0
                    -   name: size
                        in: query
                        required: false
                        schema:
                            type: integer
                            minimum: 1
                            maximum: 100
                            default: 10
                    -   name: sort
                        in: query
                        required: false
                        schema:
                            type: string
                            enum: [ name, email, createdAt ]
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
                    -   name: userId
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
                    -   name: userId
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
                    -   name: userId
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

From the client-side perspective, this contract already tells us almost everything we need:

- which operations exist
- which request model is sent
- which success model is returned
- which error model is returned for `404` and `500`

That is why the next generation step is so powerful. The generator is not inventing the client API. It is simply turning this shared contract into typed client abstractions.

## Dependencies { #dependencies }

The application still keeps the same overall shape as the basic client guide:

- it is a standalone Kora application
- it still exposes one small verification controller
- it still needs HTTP client support and HTTP server support

But now it also needs OpenAPI generation support.

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
        implementation("ru.tinkoff.kora:http-client-common")
        implementation("ru.tinkoff.kora:http-client-ok")
        implementation("ru.tinkoff.kora:http-server-undertow")
        implementation("ru.tinkoff.kora:json-module")
        implementation("ru.tinkoff.kora:logging-logback")
        implementation("ru.tinkoff.kora:validation-module")
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
        implementation("ru.tinkoff.kora:http-client-common")
        implementation("ru.tinkoff.kora:http-client-ok")
        implementation("ru.tinkoff.kora:http-server-undertow")
        implementation("ru.tinkoff.kora:json-module")
        implementation("ru.tinkoff.kora:logging-logback")
        implementation("ru.tinkoff.kora:validation-module")
    }
    ```

At this step, it helps to notice what changed relative to `http-client.md`:

- we removed the need for a handwritten `UserApiClient`
- we added the OpenAPI generator so the client interface can be created from the contract
- we keep the regular client and server dependencies because the application is still a real runnable Kora service

## HTTP Client Generation { #http-client-generation }

The detailed client generation options, `mode = client`, and `clientConfigPrefix` are described in [OpenAPI Codegen: Client](../documentation/openapi-codegen.md#client).

Now we tell Gradle how to generate the client from that existing contract.

===! ":fontawesome-brands-java: `Java`"

    ```groovy title="build.gradle"
    def openApiGenerateUsersHttpClient = tasks.register("openApiGenerateUsersHttpClient", GenerateTask) {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/../guide-openapi-http-server-app/src/main/resources/openapi/user-http-server.yaml"
        outputDir = "$buildDir/generated/user-http-client"
        def corePackage = "ru.tinkoff.kora.guide.openapi.httpclient.user"
        apiPackage = "${corePackage}.api"
        modelPackage = "${corePackage}.model"
        invokerPackage = "${corePackage}.invoker"
        configOptions = [
                mode              : "java-client",
                clientConfigPrefix: "httpClient",
        ]
    }

    sourceSets.main {
        java.srcDirs += openApiGenerateUsersHttpClient.get().outputDir
    }

    compileJava.dependsOn openApiGenerateUsersHttpClient
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="build.gradle.kts"
    val openApiGenerateUsersHttpClient = tasks.register<GenerateTask>("openApiGenerateUsersHttpClient") {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/../guide-openapi-http-server-app/src/main/resources/openapi/user-http-server.yaml"
        outputDir = "$buildDir/generated/user-http-client"
        val corePackage = "ru.tinkoff.kora.guide.openapi.httpclient.user"
        apiPackage = "$corePackage.api"
        modelPackage = "$corePackage.model"
        invokerPackage = "$corePackage.invoker"
        configOptions = mapOf(
            "mode" to "java-client",
            "clientConfigPrefix" to "httpClient"
        )
    }

    sourceSets.main {
        java.srcDir(openApiGenerateUsersHttpClient.get().outputDir)
    }

    tasks.compileJava {
        dependsOn(openApiGenerateUsersHttpClient)
    }
    ```

This configuration introduces a few ideas that are worth understanding slowly:

- `mode = "java-client"` means we are generating a synchronous Java client
- `inputSpec` points to the exact OpenAPI contract from the previous guide
- generated sources will be placed in `build/generated/user-http-client`
- `clientConfigPrefix = "httpClient"` tells the generator where this client should read its runtime configuration

That last point is especially important. The generated client is not just a set of DTOs. It is a real Kora HTTP client that will be wired into the application graph and configured
through `application.conf`.

## Generated Output { #generated-output }

Run:

```bash
./gradlew :guides-apps:guide-openapi-http-client-app:openApiGenerateUsersHttpClient
```

After generation, inspect:

===! ":fontawesome-brands-java: `Java`"

    - `build/generated/user-http-client/ru/tinkoff/kora/guide/openapi/httpclient/user/api/UsersApi.java`
    - `build/generated/user-http-client/ru/tinkoff/kora/guide/openapi/httpclient/user/api/UsersApiResponses.java`
    - `build/generated/user-http-client/ru/tinkoff/kora/guide/openapi/httpclient/user/model/UserRequestTO.java`
    - `build/generated/user-http-client/ru/tinkoff/kora/guide/openapi/httpclient/user/model/UserResponseTO.java`
    - `build/generated/user-http-client/ru/tinkoff/kora/guide/openapi/httpclient/user/model/ErrorResponseTO.java`

=== ":simple-kotlin: `Kotlin`"

    - `build/generated/user-http-client/ru/tinkoff/kora/guide/openapi/httpclient/user/api/UsersApi.kt`
    - `build/generated/user-http-client/ru/tinkoff/kora/guide/openapi/httpclient/user/api/UsersApiResponses.kt`
    - `build/generated/user-http-client/ru/tinkoff/kora/guide/openapi/httpclient/user/model/UserRequestTO.kt`
    - `build/generated/user-http-client/ru/tinkoff/kora/guide/openapi/httpclient/user/model/UserResponseTO.kt`
    - `build/generated/user-http-client/ru/tinkoff/kora/guide/openapi/httpclient/user/model/ErrorResponseTO.kt`

The generated client introduces three important new abstractions.

### 1. `UsersApi` { #1-usersapi }

This is the generated interface that replaces the handwritten `UserApiClient` from the basic client guide.

It already contains:

- HTTP method and path mappings
- query and path parameter annotations
- body annotations
- response mappers

So instead of writing the transport contract ourselves, we now inherit it from the OpenAPI file.

### 2. Generated Transport Models { #2-generated-transport-models }

The client now uses generated transport models:

- `UserRequestTO`
- `UserResponseTO`

Those models belong to the OpenAPI contract layer.

In the basic guide, the client reused local DTO classes. Here we intentionally let the OpenAPI contract define the transport models too. That removes one more place where drift could happen.

### 3. `UsersApiResponses` { #3-usersapiresponses }

This is one of the most useful parts of the generated client.

Instead of flattening all outcomes into exceptions or one body type, the generator creates typed response wrappers such as:

- `CreateUserApiResponse`
- `GetUserApiResponse`
- `DeleteUserApiResponse`
- `UpdateUserApiResponse`

That means the client can model different HTTP outcomes explicitly. For example, `getUser()` can return either:

- `GetUser200ApiResponse`
- `GetUser404ApiResponse`
- `GetUser500ApiResponse`

This is more descriptive than a handwritten client that simply assumes one happy-path body for every call.

### Generated Code Shape { #generated-code-shape }

It is worth pausing here and opening the generated files directly. Once you do that, the contract-first workflow becomes much more concrete.

Here is a shortened version of the generated `UsersApi` method for `getUser()`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient(configPath = "httpClient.UsersApi")
    public interface UsersApi {

        @HttpRoute(method = "GET", path = "/users/{userId}")
        @ResponseCodeMapper(code = 200, mapper = UsersApiClientResponseMappers.GetUser200ApiResponseMapper.class)
        @ResponseCodeMapper(code = 404, mapper = UsersApiClientResponseMappers.GetUser404ApiResponseMapper.class)
        @ResponseCodeMapper(code = 500, mapper = UsersApiClientResponseMappers.GetUser500ApiResponseMapper.class)
        UsersApiResponses.GetUserApiResponse getUser(
            @Path("userId") String userId
        );
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient(configPath = "httpClient.UsersApi")
    interface UsersApi {

        @HttpRoute(method = "GET", path = "/users/{userId}")
        @ResponseCodeMapper(code = 200, mapper = UsersApiClientResponseMappers.GetUser200ApiResponseMapper::class)
        @ResponseCodeMapper(code = 404, mapper = UsersApiClientResponseMappers.GetUser404ApiResponseMapper::class)
        @ResponseCodeMapper(code = 500, mapper = UsersApiClientResponseMappers.GetUser500ApiResponseMapper::class)
        fun getUser(
            @Path("userId") userId: String
        ): UsersApiResponses.GetUserApiResponse
    }
    ```

And here is the corresponding part of `UsersApiResponses`:

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

This small slice of generated code already shows most of the important abstractions.

### Generated `getUser()` Walkthrough { #generated-getuser-walkthrough }

Let us unpack what the generator created and why.

`@HttpClient(configPath = "httpClient.UsersApi")`

This tells Kora that the generated interface is a real HTTP client dependency. Kora generates the runtime implementation, puts it into the dependency graph, and binds it to the corresponding config
section in `application.conf`.

`@HttpRoute(method = "GET", path = "/users/{userId}")`

The generator reads the OpenAPI operation and projects it into a Kora transport annotation. You no longer repeat the route by hand in a handwritten client interface. The OpenAPI contract remains the
source of truth, and the generated Java or Kotlin interface becomes a transport-specific view of that contract.

`@Path("userId") String userId`

The path parameter from the OpenAPI file becomes a normal typed method argument. Instead of manually assembling URLs, you work with a regular method signature and let the generated implementation
place the value into the request path.

`@ResponseCodeMapper(...)`

This is one of the most useful pieces of generated code. The contract says that `GET /users/{userId}` may produce:

- `200` with a `UserResponseTO` body
- `404` with an `ErrorResponseTO` body
- `500` with an `ErrorResponseTO` body

Because those codes are present in the OpenAPI file, the generator creates response mappers for each of them. At runtime, the client uses the real HTTP status code to decide which typed response
variant to construct.

This is also why adding `500` to the OpenAPI file matters. If the contract does not describe `500`, the generator has no reason to create a dedicated `GetUser500ApiResponse` abstraction for it.

`UsersApiResponses.GetUserApiResponse`

The return type is not just `UserResponseTO`. It is a sealed response family that models the whole transport contract of that endpoint. That makes the API outcomes explicit right at the call site.

In practice, that leads to code like this:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var response = usersApi.getUser(userId);

    if (response instanceof UsersApiResponses.GetUserApiResponse.GetUser200ApiResponse ok) {
        return ok.content();
    }
    if (response instanceof UsersApiResponses.GetUserApiResponse.GetUser404ApiResponse notFound) {
        // notFound.content().message() describes the error
    }
    if (response instanceof UsersApiResponses.GetUserApiResponse.GetUser500ApiResponse internalError) {
        // internalError.content().message() describes the error
    }
    ```

    If you prefer a more expression-oriented style:
    ```java
    return switch (usersApi.getUser(userId)) {
        case UsersApiResponses.GetUserApiResponse.GetUser200ApiResponse ok ->
                ok.content().name();
        case UsersApiResponses.GetUserApiResponse.GetUser404ApiResponse notFound ->
                "Missing user: " + notFound.content().message();
        case UsersApiResponses.GetUserApiResponse.GetUser500ApiResponse internalError ->
                "Server error: " + internalError.content().message();
    };
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val response = usersApi.getUser(userId)

    when (response) {
        is UsersApiResponses.GetUserApiResponse.GetUser200ApiResponse ->
            return response.content()
        is UsersApiResponses.GetUserApiResponse.GetUser404ApiResponse -> {
            // response.content().message() describes the error
        }
        is UsersApiResponses.GetUserApiResponse.GetUser500ApiResponse -> {
            // response.content().message() describes the error
        }
    }
    ```

That style is one of the biggest benefits of generated contract-first clients. The code you write reflects the full API contract, not only the happy path.

### Generator Layers { #generator-layers }

At first glance, the generated code can feel more verbose than a handwritten interface. But each generated layer has a clear role:

- `UsersApi` defines the callable client surface
- method parameters represent transport inputs such as path and query values
- generated models such as `UserRequestTO` and `UserResponseTO` represent the OpenAPI payloads
- generated response wrappers model the allowed HTTP outcomes
- generated response mappers convert raw HTTP responses into typed variants

So the generator is not producing extra code just to be clever. It is turning the transport contract into explicit, typed abstractions that the compiler can help you work with.

The shared error model matters too. Because the contract now defines `ErrorResponseTO(message)`, the generated client can treat error responses as structured transport data instead of only as status
codes.

## Generated Client { #generated-client }

The client application still keeps the same overall teaching shape from `http-client.md`:

- one generated client
- one small aggregate controller
- one place to manually trigger the flow

But now `ClientTestController` depends on `UsersApi` instead of a handwritten `UserApiClient`.

===! ":fontawesome-brands-java: `Java`"

    ```java title="src/main/java/ru/tinkoff/kora/guide/openapi/httpclient/controller/ClientTestController.java"
    package ru.tinkoff.kora.guide.openapi.httpclient.controller;

    import java.util.List;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.openapi.httpclient.user.api.UsersApi;
    import ru.tinkoff.kora.guide.openapi.httpclient.user.api.UsersApiResponses;
    import ru.tinkoff.kora.guide.openapi.httpclient.user.model.UserRequestTO;
    import ru.tinkoff.kora.guide.openapi.httpclient.user.model.UserResponseTO;
    import ru.tinkoff.kora.http.common.HttpMethod;
    import ru.tinkoff.kora.http.common.annotation.HttpRoute;
    import ru.tinkoff.kora.http.server.common.annotation.HttpController;
    import ru.tinkoff.kora.json.common.annotation.Json;

    @Component
    @HttpController
    public final class ClientTestController {

        private final UsersApi usersApi;

        public ClientTestController(UsersApi usersApi) {
            this.usersApi = usersApi;
        }

        @HttpRoute(method = HttpMethod.POST, path = "/client/test-all-user-endpoints")
        @Json
        public TestResults testAllUserEndpoints() {
            try {
                var created = this.usersApi.createUser(new UserRequestTO("Client Demo User", "client-demo@example.com"));
                boolean userCreated = created instanceof UsersApiResponses.CreateUserApiResponse.CreateUser201ApiResponse create201
                        && create201.content() != null;
                var createdUser = created instanceof UsersApiResponses.CreateUserApiResponse.CreateUser201ApiResponse create201
                        ? create201.content()
                        : null;

                var getUserResponse = createdUser == null ? null : this.usersApi.getUser(createdUser.id());
                boolean userFetched = getUserResponse instanceof UsersApiResponses.GetUserApiResponse.GetUser200ApiResponse getUser200
                        && createdUser.id().equals(getUser200.content().id());

                var getUsersResponse = this.usersApi.getUsers(0, 10, "name");
                List<UserResponseTO> users = getUsersResponse instanceof UsersApiResponses.GetUsersApiResponse.GetUsers200ApiResponse getUsers200
                        ? getUsers200.content()
                        : List.of();
                boolean usersListed = createdUser != null && users.stream().anyMatch(user -> user.id().equals(createdUser.id()));

                var deleteResult = createdUser == null ? null : this.usersApi.deleteUser(createdUser.id());
                boolean userDeleted = deleteResult instanceof UsersApiResponses.DeleteUserApiResponse.DeleteUser204ApiResponse;

                boolean allTestsPassed = userCreated && userFetched && usersListed && userDeleted;
                return new TestResults(userCreated, userFetched, usersListed, userDeleted, allTestsPassed, null);
            } catch (Exception exception) {
                return new TestResults(false, false, false, false, false, exception.getMessage());
            }
        }

        @Json
        public record TestResults(
                boolean userCreated,
                boolean userFetched,
                boolean usersListed,
                boolean userDeleted,
                boolean allTestsPassed,
                String error) {}
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="src/main/kotlin/ru/tinkoff/kora/guide/openapi/httpclient/controller/ClientTestController.kt"
    package ru.tinkoff.kora.guide.openapi.httpclient.controller

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.openapi.httpclient.user.api.UsersApi
    import ru.tinkoff.kora.guide.openapi.httpclient.user.api.UsersApiResponses
    import ru.tinkoff.kora.guide.openapi.httpclient.user.model.UserRequestTO
    import ru.tinkoff.kora.http.common.HttpMethod
    import ru.tinkoff.kora.http.common.annotation.HttpRoute
    import ru.tinkoff.kora.http.server.common.annotation.HttpController
    import ru.tinkoff.kora.json.common.annotation.Json

    @Component
    @HttpController
    class ClientTestController(
        private val usersApi: UsersApi
    ) {
        @HttpRoute(method = HttpMethod.POST, path = "/client/test-all-user-endpoints")
        @Json
        fun testAllUserEndpoints(): TestResults {
            return try {
                val created = usersApi.createUser(UserRequestTO("Client Demo User", "client-demo@example.com"))
                val userCreated =
                    created is UsersApiResponses.CreateUserApiResponse.CreateUser201ApiResponse &&
                        created.content() != null
                val createdUser =
                    if (created is UsersApiResponses.CreateUserApiResponse.CreateUser201ApiResponse) created.content() else null

                val getUserResponse = createdUser?.let { usersApi.getUser(it.id()) }
                val userFetched =
                    getUserResponse is UsersApiResponses.GetUserApiResponse.GetUser200ApiResponse &&
                        createdUser != null &&
                        createdUser.id() == getUserResponse.content().id()

                val getUsersResponse = usersApi.getUsers(0, 10, "name")
                val users =
                    if (getUsersResponse is UsersApiResponses.GetUsersApiResponse.GetUsers200ApiResponse) {
                        getUsersResponse.content()
                    } else {
                        emptyList()
                    }
                val usersListed = createdUser != null && users.any { it.id() == createdUser.id() }

                val deleteResult = createdUser?.let { usersApi.deleteUser(it.id()) }
                val userDeleted = deleteResult is UsersApiResponses.DeleteUserApiResponse.DeleteUser204ApiResponse

                val allTestsPassed = userCreated && userFetched && usersListed && userDeleted
                TestResults(userCreated, userFetched, usersListed, userDeleted, allTestsPassed, null)
            } catch (e: Exception) {
                TestResults(false, false, false, false, false, e.message)
            }
        }

        @Json
        data class TestResults(
            val userCreated: Boolean,
            val userFetched: Boolean,
            val usersListed: Boolean,
            val userDeleted: Boolean,
            val allTestsPassed: Boolean,
            val error: String?
        )
    }
    ```

This step is where the guide really becomes concrete.

We did **not** rewrite the whole client application.

We kept the same user-facing flow from `http-client.md`:

- create a user
- fetch it
- list users
- delete it

The only thing we replaced was the transport contract layer:

- before: handwritten `UserApiClient`
- now: generated `UsersApi`

That is exactly the kind of incremental change teams often make in real projects.

## Configuration { #config }

Because the generated client was created with:

```text
clientConfigPrefix = "httpClient"
```

and the generated interface name is `UsersApi`, its runtime config lives under:

```text
httpClient.UsersApi
```

Update `src/main/resources/application.conf`:

For the full configuration reference, see [HTTP Server](../documentation/http-server.md), [HTTP Client](../documentation/http-client.md) and [Logging SLF4J](../documentation/logging-slf4j.md).

===! ":material-code-json: `Hocon`"

    ```javascript title="src/main/resources/application.conf"
    httpServer {
      publicApiHttpPort = 8081 //(1)!
      privateApiHttpPort = 8086 //(2)!
      telemetry.logging.enabled = true //(3)!
    }

    httpClient {
      UsersApi {
        url = "http://localhost:8080" //(4)!
        url = ${?USER_API_URL} //(5)!
        requestTimeout = 10s //(6)!
      }
      telemetry.logging.enabled = true //(7)!
    }

    logging {
      levels {
        "ROOT": "INFO" //(8)!
        "ru.tinkoff.kora": "INFO" //(9)!
        "ru.tinkoff.kora.guide.openapi.httpclient": "INFO" //(10)!
      }
    }
    ```

    1. Default public HTTP port used by application endpoints.
    2. Default private HTTP port used by probes, metrics, and management endpoints.
    3. Enables the feature for this configuration section.
    4. Base URL used by the configured client.
    5. Base URL used by the configured client. Optional override from `USER_API_URL`.
    6. Maximum time allowed for a client request.
    7. Enables the feature for this configuration section.
    8. Log level for `ROOT`.
    9. Log level for `ru.tinkoff.kora`.
    10. Log level for `ru.tinkoff.kora.guide.openapi.httpclient`.

=== ":simple-yaml: `YAML`"

    ```yaml title="src/main/resources/application.yaml"
    httpServer:
      publicApiHttpPort: 8081 #(1)!
      privateApiHttpPort: 8086 #(2)!
      telemetry:
        logging:
          enabled: true #(3)!
    httpClient:
      UsersApi:
        url: ${?USER_API_URL:"http://localhost:8080"} #(4)!
        requestTimeout: 10s #(5)!
      telemetry:
        logging:
          enabled: true #(6)!
    logging:
      levels:
        ROOT: "INFO" #(7)!
        "ru.tinkoff.kora": "INFO" #(8)!
        "ru.tinkoff.kora.guide.openapi.httpclient": "INFO" #(9)!
    ```

    1. Default public HTTP port used by application endpoints.
    2. Default private HTTP port used by probes, metrics, and management endpoints.
    3. Enables the feature for this configuration section.
    4. Base URL used by the configured client. Uses the shown default and allows `USER_API_URL` to override it.
    5. Maximum time allowed for a client request.
    6. Enables the feature for this configuration section.
    7. Log level for `ROOT`.
    8. Log level for `ru.tinkoff.kora`.
    9. Log level for `ru.tinkoff.kora.guide.openapi.httpclient`.

This step introduces a subtle but important idea.

In the handwritten client guide, you decided the config path yourself in `@HttpClient(configPath = ...)`.

Here, the generator decides the client annotation for you from:

- the `clientConfigPrefix`
- the generated API name

So when something seems "missing" at runtime, it is often worth checking what config path the generated interface actually uses.

## Check Application { #check-app }

If you want to verify the flow manually, run both applications in separate terminals.

### Terminal 1: OpenAPI Server { #terminal-1-openapi-server }

```bash
./gradlew run
```

This application exposes:

- the user API on `http://localhost:8080`
- `/openapi`
- `/swagger-ui`

### Terminal 2: OpenAPI Client { #terminal-2-openapi-client }

```bash
./gradlew run
```

This application exposes its own aggregate verification endpoint on:

- `http://localhost:8081/client/test-all-user-endpoints`

Now trigger the whole client scenario:

```bash
curl -X POST http://localhost:8081/client/test-all-user-endpoints
```

Expected result: a JSON object where `allTestsPassed` is `true`.

## Testing { #testing }

The runnable guide app also includes a test suite that points the generated client at a containerized copy of `guide-openapi-http-server-app`.

Run:

```bash
./gradlew test
```

These tests verify the same basic flow as the handwritten client guide:

- create user
- get user
- missing user
- list users with paging and sorting
- delete user

That makes the comparison between the two guides easy to understand:

- `http-client.md` proves the flow with a handwritten declarative client
- this guide proves the same flow with a generated OpenAPI client

## Best Practices { #best-practices }

- Reuse the exact same OpenAPI contract between server and client whenever possible.
- Treat generated code as build output, not as application code you edit manually.
- Keep application logic outside the generated client, in your own controller or service classes.
- Inspect the generated interface and response wrappers when the runtime behavior is unclear.
- Keep one small aggregate verification endpoint for learning scenarios instead of rebuilding the full server inside the client app.

## Summary { #summary }

You took the standalone client app from [HTTP Client with Kora](http-client.md) and rebuilt its transport layer in a contract-first style:

- the client now uses the same `user-http-server.yaml` contract as the OpenAPI server guide
- Kora generates `UsersApi` from that shared contract
- generated transport models replace the handwritten client DTOs
- generated response wrappers make multiple HTTP outcomes explicit
- the client application still keeps the same simple aggregate verification flow

So the overall client application stays familiar, but the transport contract is now shared with the server instead of being handwritten separately.

## Key Concepts { #key-concepts }

- a contract-first client works best when it reuses the exact same OpenAPI file as the server
- Kora can generate a typed HTTP client from OpenAPI
- generated response wrappers such as `GetUserApiResponse` and `DeleteUserApiResponse` make HTTP outcomes explicit
- adding `500` to the OpenAPI file generates dedicated `500` response variants too
- generated transport models can replace handwritten client DTOs
- `clientConfigPrefix` controls where the generated client reads its runtime configuration

## Troubleshooting { #troubleshooting }

**The generated client is missing from the graph:**

Check that:

- the OpenAPI generation task runs before compilation
- the generated output directory is added to `sourceSets.main`
- the application includes the HTTP client module, such as `OkHttpClientModule`

**Runtime says the client config is missing:**

Inspect the generated interface and look at its `@HttpClient(configPath = ...)` annotation.

In this guide, the generated client expects:

```text
httpClient.UsersApi
```

not just:

```text
httpClient
```

**The client and server models look similar but not identical:**

That often means the client is no longer using handwritten DTOs and is now using generated transport models from the OpenAPI contract. Make sure your application code imports:

- `UserRequestTO`
- `UserResponseTO`

from the generated package.

**The build succeeds but imports do not match:**

Check your generation settings in `build.gradle`:

- `outputDir`
- `apiPackage`
- `modelPackage`
- `invokerPackage`

If those change, your controller imports must change too.

**The generated client does not expose a `500` response variant:**

Inspect the OpenAPI file first.

Generated response variants only appear for status codes that are actually described in the contract. If you want explicit handling for `500`, it must be present in the `responses` section of that
operation in the shared OpenAPI file.

**Container-based tests cannot reach the server app:**

Check that:

- Docker is running
- the test depends on `guide-openapi-http-server-app:distTar`
- the server module Dockerfile points at its own generated distribution
- `USER_API_URL` is overridden from the container URI in the test config

## What's Next? { #whats-next }

- [Resilient Patterns](resilient.md) to make generated clients safer against slow or unstable dependencies.
- [Observability](observability.md) to trace generated client calls and measure status-specific outcomes.
- [HTTP Server Advanced](http-server-advanced.md) and then [HTTP Client Advanced](http-client-advanced.md) if you want to compare contract-generated clients with handwritten advanced clients.
- [gRPC Server](grpc-server.md) if you want to explore a strongly typed binary contract after OpenAPI.

## Help { #help }

If you get stuck:

- compare with [Kora Java OpenAPI HTTP Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-openapi-http-client-app) and [Kora Kotlin OpenAPI HTTP Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-openapi-http-client-app)
- revisit [HTTP Client](http-client.md) for the handwritten client baseline
- revisit [OpenAPI HTTP Server](openapi-http-server.md) for the server contract this client consumes
- check the [OpenAPI Codegen documentation](../documentation/openapi-codegen.md)
- check the [HTTP Client documentation](../documentation/http-client.md)
