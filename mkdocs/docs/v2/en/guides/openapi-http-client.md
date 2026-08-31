---
search:
  exclude: true
title: Contract-First HTTP Client with OpenAPI
summary: Continue the HTTP Client guide by replacing the handwritten declarative client with an OpenAPI-generated client
description: "Contract-first Kora HTTP client from an OpenAPI file: the org.openapi.generator Gradle plugin with generatorName kora, configOptions mode java-client / kotlin-client, clientConfig and clientConfigPrefix, the generated @HttpClient interface with @ResponseCodeMapper, sealed <Api>Responses wrappers, OptArgs holders for optional parameters, enum fromValue, and testing the generated client against a Testcontainers copy of the server."
agent:
  use_when: "Use this file for questions about generating a Kora HTTP client from an OpenAPI contract step by step: GenerateTask, generatorName kora, mode java-client and kotlin-client, clientConfig versus clientConfigPrefix and the httpClient.<prefix>.<api> configuration path with a lower-case first letter, the generated @HttpClient interface, @HttpRoute and @ResponseCodeMapper annotations, <Api>ClientResponseMappers, sealed <Api>Responses matching, <Api><Operation>OptArgs holders, generated enum fromValue, HttpClientResponseException, and KoraAppTestConfigModifier with Testcontainers."
tags: openapi, http-client, contract-first, code-generation, swagger
---

# Contract-First HTTP Client with OpenAPI { #contract-first-http-client }

This guide introduces contract-first HTTP clients with Kora and OpenAPI. It covers how an OpenAPI specification generates a typed client, how generated request and response models replace handwritten
transport interfaces, and how the client is wired into a Kora application service. You will also see how one API contract can describe both sides of an HTTP integration without duplicating method
signatures.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java OpenAPI HTTP Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-openapi-http-client-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin OpenAPI HTTP Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-openapi-http-client-app).

## What You'll Build { #youll-build }

You will rebuild the client application from [HTTP Client with Kora](http-client.md), but in a contract-first style:

- the remote user API will be described by the same `user-http-server.yaml` contract from [Contract-First HTTP Server with OpenAPI](openapi-http-server.md)
- Kora will generate a typed client interface from that contract
- generated request and response models will replace the handwritten client DTOs
- the client application will still expose one aggregate endpoint for easy manual verification
- tests will run the generated client against a containerized copy of the OpenAPI server application

## What You'll Need { #youll-need }

- JDK 25 or later
- Gradle 9+
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
6. keep the same aggregate verification flow from [HTTP Client](http-client.md)
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
    - Swagger UI and Scalar
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

That is why this guide comes after both [HTTP Client](http-client.md) and [OpenAPI HTTP Server](openapi-http-server.md).

You first learn how a handwritten declarative client works and how an OpenAPI-driven server works, and only then combine those ideas into one shared contract-first integration flow.

#### Kora's Contract-First Advantage { #koras-contract-first-advantage }

Kora makes this especially practical because the generated client is not a throwaway SDK. It integrates naturally with the rest of the framework:

- generated clients are wired through Kora dependency injection
- configuration is still handled through normal Kora config paths
- JSON mapping is still handled by Kora's generated mappers
- response-code mapping is generated explicitly through typed response wrappers
- the generated client still behaves like a normal Kora dependency in your application graph

So the result still feels like a Kora application, not like an external codegen tool bolted onto the side.

### Why One Contract { #one-contract }

The basic client guide already showed that a handwritten declarative client is much nicer than low-level HTTP request code. But handwritten declarative clients still have one long-term risk: the client
and server contracts can slowly drift apart.

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

So this guide is not about introducing a completely different architecture. It is about taking the client app from [HTTP Client](http-client.md) and making it depend on the same contract the server
already uses.

## OpenAPI Contract { #openapi-contract }

The most important decision in this guide is very simple:

- do **not** invent a second client-only contract
- do **not** duplicate the YAML by hand with small differences
- use the same `user-http-server.yaml` from [Contract-First HTTP Server with OpenAPI](openapi-http-server.md)

That is exactly what the runnable guide app does. Its build points to the contract from the sibling server module:

```text
../kora-java-guide-openapi-http-server-app/src/main/resources/openapi/user-http-server.yaml
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
- `ErrorResponseTO`

This is the key lesson of the guide. Contract-first development works best when the client and server truly share one contract, not two almost-identical copies.

In a real system, that sharing usually goes one step further: the contract is published as an artifact or a Git submodule, and both applications point their `inputSpec` at that shared copy. A relative
path to a sibling module works while the two applications live in the same repository, and it is exactly the arrangement the guide apps use.

## Contract to Client { #contract-client }

Even though the OpenAPI file was already created in [Contract-First HTTP Server with OpenAPI](openapi-http-server.md), it is worth pausing here and looking at it again from the client point of view.

We are not creating a new client-specific specification. We are using the exact same HTTP OpenAPI contract that the server guide introduced. That is the whole point of the workflow:

- one shared contract
- one server generated from it
- one client generated from it

The shared contract looks like this:

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

But now it also needs OpenAPI generation support. As on the server side, this comes in two pieces: the `org.openapi.generator` **Gradle plugin**, and the `io.koraframework:openapi-generator`
**library** on the `buildscript` classpath that teaches that plugin how to emit Kora code.

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
        koraBom platform("io.koraframework:kora-bom:2.0.0.RC1")

        annotationProcessor "io.koraframework:annotation-processors"

        implementation "io.koraframework:config-hocon"
        implementation "io.koraframework:http-client-common" //(4)!
        implementation "io.koraframework:http-client-ok" //(5)!
        implementation "io.koraframework:http-server-undertow" //(6)!
        implementation "io.koraframework:json-common"
        implementation "io.koraframework:logging-logback"
        implementation "io.koraframework:validation-module"

        testAnnotationProcessor "io.koraframework:annotation-processors"

        testImplementation platform("org.junit:junit-bom:$junitVersion")
        testImplementation "org.junit.jupiter:junit-jupiter"
        testImplementation "io.koraframework:test-junit5"
        testImplementation "org.testcontainers:testcontainers-junit-jupiter:2.0.5" //(7)!
        testImplementation "org.testcontainers:testcontainers:2.0.5"
    }
    ```

    1.  `GenerateTask` is the plugin task type used to declare a generation task.
    2.  Kora generator implementation, loaded by the `Gradle` JVM through the `buildscript` classpath.
    3.  `OpenAPI Generator` Gradle plugin, pinned to the version Kora 2.0 is compiled against.
    4.  Declarative HTTP client contracts and annotations.
    5.  The `OkHttp` transport implementation that actually executes requests.
    6.  Still needed, because this application also exposes its own aggregate verification endpoint.
    7.  Used only by the tests, to start the OpenAPI server app in a container.

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
        implementation(platform("io.koraframework:kora-bom:2.0.0.RC1"))

        ksp("io.koraframework:symbol-processors:2.0.0.RC1")

        implementation("io.koraframework:config-hocon")
        implementation("io.koraframework:http-client-common") //(4)!
        implementation("io.koraframework:http-client-ok") //(5)!
        implementation("io.koraframework:http-server-undertow") //(6)!
        implementation("io.koraframework:json-common")
        implementation("io.koraframework:logging-logback")
        implementation("io.koraframework:validation-module")

        testImplementation(platform("org.junit:junit-bom:${property("junitVersion")}"))
        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation("io.koraframework:test-junit5")
        testImplementation("org.testcontainers:testcontainers-junit-jupiter:2.0.5") //(7)!
        testImplementation("org.testcontainers:testcontainers:2.0.5")
    }
    ```

    1.  `GenerateTask` is the plugin task type used to declare a generation task.
    2.  Kora generator implementation, loaded by the `Gradle` JVM through the `buildscript` classpath.
    3.  `OpenAPI Generator` Gradle plugin, pinned to the version Kora 2.0 is compiled against.
    4.  Declarative HTTP client contracts and annotations.
    5.  The `OkHttp` transport implementation that actually executes requests.
    6.  Still needed, because this application also exposes its own aggregate verification endpoint.
    7.  Used only by the tests, to start the OpenAPI server app in a container.

!!! warning "The `Gradle` daemon must run on JDK 25 or newer"

    `io.koraframework:openapi-generator` is loaded by the `Gradle` JVM, not by the application, so the `Gradle` daemon itself must run on `JDK 25` or newer.
    A project `toolchain` alone is not enough, and a mismatch shows up as `UnsupportedClassVersionError` during the generation task, before any project code is compiled.

At this step, it helps to notice what changed relative to [HTTP Client](http-client.md):

- we removed the need for a handwritten `UserApiClient`
- we added the OpenAPI generator so the client interface can be created from the contract
- we keep the regular client and server dependencies because the application is still a real runnable Kora service

The application graph itself does not change at all: `OkHttpClientModule` provides the transport, `JsonModule` provides the mappers, and the generated client interface joins the graph on its own.

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/io/koraframework/guide/openapi/httpclient/Application.java`:

    ```java
    package io.koraframework.guide.openapi.httpclient;

    import io.koraframework.application.graph.KoraApplication;
    import io.koraframework.common.annotation.KoraApp;
    import io.koraframework.config.hocon.HoconConfigModule;
    import io.koraframework.http.client.ok.OkHttpClientModule;
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule;
    import io.koraframework.json.common.JsonModule;
    import io.koraframework.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            OkHttpClientModule,
            UndertowPublicHttpServerModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/io/koraframework/guide/openapi/httpclient/Application.kt`:

    ```kotlin
    package io.koraframework.guide.openapi.httpclient

    import io.koraframework.application.graph.KoraApplication
    import io.koraframework.common.annotation.KoraApp
    import io.koraframework.config.hocon.HoconConfigModule
    import io.koraframework.http.client.ok.OkHttpClientModule
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule
    import io.koraframework.json.common.JsonModule
    import io.koraframework.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        OkHttpClientModule,
        UndertowPublicHttpServerModule

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

## HTTP Client Generation { #http-client-generation }

The detailed client generation options are described in [OpenAPI Codegen: Client](../documentation/openapi-codegen.md#client).

Now we tell Gradle how to generate the client from that existing contract.

===! ":fontawesome-brands-java: `Java`"

    Update `build.gradle`:

    ```groovy
    def openApiGenerateUsersHttpClient = tasks.register("openApiGenerateUsersHttpClient", GenerateTask) {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = layout.projectDirectory.file("../kora-java-guide-openapi-http-server-app/src/main/resources/openapi/user-http-server.yaml") //(1)!
        outputDir = layout.buildDirectory.dir("generated/user-http-client")
        def corePackage = "io.koraframework.guide.openapi.httpclient.user"
        apiPackage = "${corePackage}.api"
        modelPackage = "${corePackage}.model"
        invokerPackage = "${corePackage}.invoker"
        configOptions = [
                mode              : "java-client", //(2)!
                clientConfigPrefix: "httpClient", //(3)!
        ]
    }

    sourceSets.main {
        java.srcDirs += openApiGenerateUsersHttpClient.get().outputDir
    }

    compileJava.dependsOn openApiGenerateUsersHttpClient
    ```

    1.  The exact same contract file the server generates from — not a copy.
    2.  Generation mode. `java-client` is one of the four supported modes: `java-client`, `java-server`, `kotlin-client`, `kotlin-server`.
    3.  Prefix of the configuration path for every generated client of this task.

=== ":simple-kotlin: `Kotlin`"

    Update `build.gradle.kts`:

    ```kotlin
    val openApiGenerateUsersHttpClient = tasks.register<GenerateTask>("openApiGenerateUsersHttpClient") {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec.set(layout.projectDirectory.file("../kora-kotlin-guide-openapi-http-server-app/src/main/resources/openapi/user-http-server.yaml")) //(1)!
        outputDir.set(layout.buildDirectory.dir("generated/user-http-client"))
        val corePackage = "io.koraframework.guide.openapi.httpclient.user"
        apiPackage = "${corePackage}.api"
        modelPackage = "${corePackage}.model"
        invokerPackage = "${corePackage}.invoker"
        configOptions = mapOf(
            "mode" to "kotlin-client", //(2)!
            "clientConfigPrefix" to "httpClient", //(3)!
        )
    }

    kotlin.sourceSets.main { kotlin.srcDir(openApiGenerateUsersHttpClient.get().outputDir) }

    tasks.matching { it.name.startsWith("ksp") }.configureEach {
        dependsOn(openApiGenerateUsersHttpClient)
    }
    ```

    1.  The exact same contract file the server generates from — not a copy.
    2.  Generation mode. `kotlin-client` is one of the four supported modes: `java-client`, `java-server`, `kotlin-client`, `kotlin-server`.
    3.  Prefix of the configuration path for every generated client of this task.

This configuration introduces a few ideas that are worth understanding slowly:

- `mode` selects a **client**, so the generator emits `@HttpClient` interfaces instead of controllers and delegates
- `inputSpec` points to the exact OpenAPI contract from the previous guide
- generated sources are placed in `build/generated/user-http-client`, which is build output and never gets committed
- `clientConfigPrefix` tells the generator where this client should read its runtime configuration

That last point is the one that trips people up, so it deserves its own note.

!!! warning "A client mode always needs a configuration path"

    Generated clients are real Kora HTTP clients, and a Kora HTTP client cannot exist without a config section that holds at least its `url`. That is why exactly one of two options is required:

    | Option               | Behavior                                                                                                                     |
    |----------------------|------------------------------------------------------------------------------------------------------------------------------|
    | `clientConfig`       | The complete path, used verbatim for every generated client of the task. Use it when the contract produces one API interface. |
    | `clientConfigPrefix` | A prefix; the generated interface name with a **lower-case first letter** is appended. Use it for several API classes.         |

    If neither is set for a client mode, generation fails with a message that even suggests a `clientConfig` value derived from the contract file name.

With `clientConfigPrefix = "httpClient"` and the tag `users` producing the interface `UsersApi`, the configuration path is therefore `httpClient.usersApi` — lower-case `u`. This matters more than it
looks: a config section written as `httpClient.UsersApi` is simply not read, the client comes up without a `url`, and every call hangs until the request timeout instead of failing fast at startup.

You do not have to guess the path. After a successful run the generator logs every generated client together with the exact configuration path it expects:

```text
Generated Kora OpenAPI HTTP clients and config paths:
  - UsersApi -> httpClient.usersApi (configPath)
```

## Generated Output { #generated-output }

Run:

```bash
./gradlew openApiGenerateUsersHttpClient
```

After generation, inspect:

===! ":fontawesome-brands-java: `Java`"

    - `build/generated/user-http-client/io/koraframework/guide/openapi/httpclient/user/api/UsersApi.java`
    - `build/generated/user-http-client/io/koraframework/guide/openapi/httpclient/user/api/UsersApiResponses.java`
    - `build/generated/user-http-client/io/koraframework/guide/openapi/httpclient/user/api/UsersApiClientRequestMappers.java`
    - `build/generated/user-http-client/io/koraframework/guide/openapi/httpclient/user/api/UsersApiClientResponseMappers.java`
    - `build/generated/user-http-client/io/koraframework/guide/openapi/httpclient/user/api/UsersApiGetUsersOptArgs.java`
    - `build/generated/user-http-client/io/koraframework/guide/openapi/httpclient/user/model/UserRequestTO.java`
    - `build/generated/user-http-client/io/koraframework/guide/openapi/httpclient/user/model/UserResponseTO.java`
    - `build/generated/user-http-client/io/koraframework/guide/openapi/httpclient/user/model/ErrorResponseTO.java`

=== ":simple-kotlin: `Kotlin`"

    - `build/generated/user-http-client/io/koraframework/guide/openapi/httpclient/user/api/UsersApi.kt`
    - `build/generated/user-http-client/io/koraframework/guide/openapi/httpclient/user/api/UsersApiResponses.kt`
    - `build/generated/user-http-client/io/koraframework/guide/openapi/httpclient/user/api/UsersApiClientRequestMappers.kt`
    - `build/generated/user-http-client/io/koraframework/guide/openapi/httpclient/user/api/UsersApiClientResponseMappers.kt`
    - `build/generated/user-http-client/io/koraframework/guide/openapi/httpclient/user/api/UsersApiGetUsersOptArgs.kt`
    - `build/generated/user-http-client/io/koraframework/guide/openapi/httpclient/user/model/UserRequestTO.kt`
    - `build/generated/user-http-client/io/koraframework/guide/openapi/httpclient/user/model/UserResponseTO.kt`
    - `build/generated/user-http-client/io/koraframework/guide/openapi/httpclient/user/model/ErrorResponseTO.kt`

The generated client introduces three important new abstractions.

### 1. `UsersApi` { #1-usersapi }

This is the generated interface that replaces the handwritten `UserApiClient` from the basic client guide.

It already contains:

- HTTP method and path mappings
- query and path parameter annotations
- body annotations
- response mappers, one per declared status code

So instead of writing the transport contract ourselves, we now inherit it from the OpenAPI file. And because it is annotated with `@HttpClient`, it is a component of the graph like any other: you
inject `UsersApi` directly, with no registration step.

### 2. Generated Transport Models { #2-generated-transport-models }

The client now uses generated transport models:

- `UserRequestTO`
- `UserResponseTO`
- `ErrorResponseTO`

Those models belong to the OpenAPI contract layer. `Java` models are `record` types with generated `@Json` readers and writers, plus a `with<Field>` method per field; `Kotlin` models are `data class`
types with the usual `copy`.

In the basic guide, the client reused local DTO classes. Here we intentionally let the OpenAPI contract define the transport models too. That removes one more place where drift could happen.

!!! warning "Use named arguments for generated `Kotlin` models"

    Generated `Kotlin` constructors list required properties first and give every optional property a default value.
    Adding one property to the contract can therefore shift positions, and a positional call such as `UserRequestTO("john@example.com", "John")` still compiles while silently swapping two `String` values — the server then stores an email as a name.
    Construct generated models with named arguments: `UserRequestTO(name = "John Doe", email = "john@example.com")`.

If a schema declares an `enum`, the generated enum keeps the raw contract values in a nested `Constants` class, because contract values are frequently not valid identifiers. Convert wire values with
the static `fromValue` method and read them back with `getValue()` / `value`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var status = Pet.StatusEnum.fromValue("available"); //(1)!
    var wire = status.getValue(); //(2)!
    ```

    1.  Throws `IllegalArgumentException` for a value that is not in the contract.
    2.  Returns `"available"`, the value declared in the contract.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val status = Pet.StatusEnum.fromValue("available") //(1)!
    val wire = status.value //(2)!
    ```

    1.  Throws `IllegalArgumentException` for a value that is not in the contract.
    2.  Returns `"available"`, the value declared in the contract.

`Enum.valueOf` in `Java` and `enumValueOf` in `Kotlin` match the generated **constant name**, not the contract value, so they must never be used for parsing. That mistake compiles cleanly and fails
only at runtime, on the first payload where the two differ — a contract value of `available` against a constant named `AVAILABLE` is exactly that case.

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
    @HttpClient("httpClient.usersApi")
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
    @HttpClient("httpClient.usersApi")
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

`@HttpClient("httpClient.usersApi")`

This tells Kora that the generated interface is a real HTTP client dependency. Kora generates the runtime implementation, puts it into the dependency graph, and binds it to the corresponding config
section in `application.conf`. The path is the `value` of the annotation, and it is exactly `clientConfigPrefix` plus the interface name with a lower-case first letter.

`@HttpRoute(method = "GET", path = "/users/{userId}")`

The generator reads the OpenAPI operation and projects it into a Kora transport annotation. You no longer repeat the route by hand in a handwritten client interface. The OpenAPI contract remains the
source of truth, and the generated `Java` or `Kotlin` interface becomes a transport-specific view of that contract.

`@Path("userId") String userId`

The path parameter from the OpenAPI file becomes a normal typed method argument. Instead of manually assembling URLs, you work with a regular method signature and let the generated implementation
place the value into the request path.

`@ResponseCodeMapper(...)`

This is one of the most useful pieces of generated code. The contract says that `GET /users/{userId}` may produce `200` with a `UserResponseTO` body, and `404` / `500` with an `ErrorResponseTO` body.
Because those codes are present in the OpenAPI file, the generator creates a response mapper for each of them. At runtime, the client uses the real HTTP status code to decide which typed response
variant to construct.

This is also why adding `500` to the OpenAPI file matters. If the contract does not describe `500`, the generator has no reason to create a dedicated `GetUser500ApiResponse` abstraction for it — and a
status the contract never mentions has no mapper at all, so the client throws `HttpClientResponseException` instead of returning a wrapper.

`UsersApiResponses.GetUserApiResponse`

The return type is not just `UserResponseTO`. It is a sealed response family that models the whole transport contract of that endpoint. That makes the API outcomes explicit right at the call site, and
because the family is `sealed`, the compiler can check that a `switch` or `when` covers every declared outcome.

In practice, that leads to code like this:

===! ":fontawesome-brands-java: `Java`"

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
    return when (val response = usersApi.getUser(userId)) {
        is UsersApiResponses.GetUserApiResponse.GetUser200ApiResponse ->
            response.content.name
        is UsersApiResponses.GetUserApiResponse.GetUser404ApiResponse ->
            "Missing user: " + response.content.message
        is UsersApiResponses.GetUserApiResponse.GetUser500ApiResponse ->
            "Server error: " + response.content.message
    }
    ```

That style is one of the biggest benefits of generated contract-first clients. The code you write reflects the full API contract, not only the happy path.

### Optional Arguments { #optional-arguments }

`getUsers` has three optional query parameters, and passing all three on every call is noisy. Besides the full method, the generator emits a small holder class named
`<Api><OperationId>OptArgs` — here `UsersApiGetUsersOptArgs` — plus two extra `default` overloads: one taking only the required parameters, and one taking the required parameters plus the holder.

===! ":fontawesome-brands-java: `Java`"

    ```java
    var allDefaults = usersApi.getUsers(); //(1)!

    var secondPage = usersApi.getUsers(UsersApiGetUsersOptArgs.defaults() //(2)!
        .withPage(1)); //(3)!
    ```

    1.  Every optional parameter is sent as `null`.
    2.  `defaults()` starts from the contract defaults (`page = 0`, `size = 10`, `sort = name`); `empty()` starts from all `null`.
    3.  `with...` mutates the holder and returns it, so calls can be chained.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val allDefaults = usersApi.getUsers() //(1)!

    val secondPage = usersApi.getUsers(UsersApiGetUsersOptArgs.defaults() //(2)!
        .withPage(1)) //(3)!
    ```

    1.  Every optional parameter is sent as `null`.
    2.  `defaults()` starts from the contract defaults (`page = 0`, `size = 10`, `sort = name`); `empty()` starts from all `null`.
    3.  `with...` mutates the holder and returns it, so calls can be chained.

Note the asymmetry with the server side: `defaults()` is where the OpenAPI `default` values actually get applied, and it is the **client** that applies them by sending explicit values. A generated
server still receives `null` for an absent parameter.

### Generator Layers { #generator-layers }

At first glance, the generated code can feel more verbose than a handwritten interface. But each generated layer has a clear role:

- `UsersApi` defines the callable client surface
- method parameters represent transport inputs such as path and query values
- generated models such as `UserRequestTO` and `UserResponseTO` represent the OpenAPI payloads
- generated response wrappers model the allowed HTTP outcomes
- `UsersApiClientRequestMappers` and `UsersApiClientResponseMappers` convert between raw HTTP and those typed variants

So the generator is not producing extra code just to be clever. It is turning the transport contract into explicit, typed abstractions that the compiler can help you work with.

The shared error model matters too. Because the contract defines `ErrorResponseTO(message)`, the generated client can treat error responses as structured transport data instead of only as status codes.

## Generated Client { #generated-client }

The client application still keeps the same overall teaching shape from [HTTP Client](http-client.md):

- one generated client
- one small aggregate controller
- one place to manually trigger the flow

But now `ClientTestController` depends on `UsersApi` instead of a handwritten `UserApiClient`.

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/io/koraframework/guide/openapi/httpclient/controller/ClientTestController.java`:

    ```java
    package io.koraframework.guide.openapi.httpclient.controller;

    import java.util.List;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.openapi.httpclient.user.api.UsersApi;
    import io.koraframework.guide.openapi.httpclient.user.api.UsersApiResponses;
    import io.koraframework.guide.openapi.httpclient.user.model.UserRequestTO;
    import io.koraframework.guide.openapi.httpclient.user.model.UserResponseTO;
    import io.koraframework.http.common.HttpMethod;
    import io.koraframework.http.common.annotation.HttpRoute;
    import io.koraframework.http.server.common.annotation.HttpController;
    import io.koraframework.json.common.annotation.Json;

    @Component
    @HttpController
    public final class ClientTestController {

        private final UsersApi usersApi; //(1)!

        public ClientTestController(UsersApi usersApi) {
            this.usersApi = usersApi;
        }

        @HttpRoute(method = HttpMethod.POST, path = "/client/test-all-user-endpoints")
        @Json
        public TestResults testAllUserEndpoints() {
            try {
                var created = this.usersApi.createUser(new UserRequestTO("Client Demo User", "client-demo@example.com"));
                var createdUser = created instanceof UsersApiResponses.CreateUserApiResponse.CreateUser201ApiResponse create201
                        ? create201.content()
                        : null;
                boolean userCreated = createdUser != null; //(2)!

                var getUserResponse = createdUser == null ? null : this.usersApi.getUser(createdUser.id());
                boolean userFetched = getUserResponse instanceof UsersApiResponses.GetUserApiResponse.GetUser200ApiResponse getUser200
                        && createdUser.id().equals(getUser200.content().id());

                var getUsersResponse = this.usersApi.getUsers(0, 10, "name");
                var users = getUsersResponse instanceof UsersApiResponses.GetUsersApiResponse.GetUsers200ApiResponse getUsers200
                        ? getUsers200.content()
                        : List.<UserResponseTO>of();
                boolean usersListed = createdUser != null && users.stream().anyMatch(user -> user.id().equals(createdUser.id()));

                var deleteResult = createdUser == null ? null : this.usersApi.deleteUser(createdUser.id());
                boolean userDeleted = deleteResult instanceof UsersApiResponses.DeleteUserApiResponse.DeleteUser204ApiResponse; //(3)!

                boolean allTestsPassed = userCreated && userFetched && usersListed && userDeleted;
                return new TestResults(userCreated, userFetched, usersListed, userDeleted, allTestsPassed, null);
            } catch (Exception exception) {
                return new TestResults(false, false, false, false, false, exception.getMessage()); //(4)!
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

    1.  The generated `@HttpClient` interface, injected directly — no registration and no handwritten transport interface.
    2.  A `201` is a distinct wrapper type, so "was it created" is a type check rather than a status-code comparison.
    3.  `204 No Content` is an empty record, so its presence alone is the assertion.
    4.  A transport failure, or a status the contract does not describe, still surfaces as an exception — `HttpClientResponseException` in the latter case.

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/io/koraframework/guide/openapi/httpclient/controller/ClientTestController.kt`:

    ```kotlin
    package io.koraframework.guide.openapi.httpclient.controller

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.openapi.httpclient.user.api.UsersApi
    import io.koraframework.guide.openapi.httpclient.user.api.UsersApiResponses
    import io.koraframework.guide.openapi.httpclient.user.model.UserRequestTO
    import io.koraframework.http.common.HttpMethod
    import io.koraframework.http.common.annotation.HttpRoute
    import io.koraframework.http.server.common.annotation.HttpController
    import io.koraframework.json.common.annotation.Json

    @Component
    @HttpController
    class ClientTestController(
        private val usersApi: UsersApi //(1)!
    ) {

        @HttpRoute(method = HttpMethod.POST, path = "/client/test-all-user-endpoints")
        @Json
        fun testAllUserEndpoints(): TestResults {
            return try {
                val created = usersApi.createUser(
                    UserRequestTO(name = "Client Demo User", email = "client-demo@example.com")
                )
                val createdUser =
                    if (created is UsersApiResponses.CreateUserApiResponse.CreateUser201ApiResponse) created.content else null
                val userCreated = createdUser != null //(2)!

                val getUserResponse = createdUser?.let { usersApi.getUser(it.id) }
                val userFetched =
                    getUserResponse is UsersApiResponses.GetUserApiResponse.GetUser200ApiResponse &&
                            createdUser.id == getUserResponse.content.id

                val getUsersResponse = usersApi.getUsers(0, 10, "name")
                val users =
                    if (getUsersResponse is UsersApiResponses.GetUsersApiResponse.GetUsers200ApiResponse) {
                        getUsersResponse.content
                    } else {
                        emptyList()
                    }
                val usersListed = createdUser != null && users.any { it.id == createdUser.id }

                val deleteResult = createdUser?.let { usersApi.deleteUser(it.id) }
                val userDeleted = deleteResult is UsersApiResponses.DeleteUserApiResponse.DeleteUser204ApiResponse //(3)!

                val allTestsPassed = userCreated && userFetched && usersListed && userDeleted
                TestResults(userCreated, userFetched, usersListed, userDeleted, allTestsPassed, null)
            } catch (e: Exception) {
                TestResults(false, false, false, false, false, e.message) //(4)!
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

    1.  The generated `@HttpClient` interface, injected directly — no registration and no handwritten transport interface.
    2.  A `201` is a distinct wrapper type, so "was it created" is a type check rather than a status-code comparison.
    3.  `204 No Content` is an empty class, so its presence alone is the assertion.
    4.  A transport failure, or a status the contract does not describe, still surfaces as an exception — `HttpClientResponseException` in the latter case.

Client calls are **synchronous**: `usersApi.getUser(...)` returns the response wrapper directly. There are no reactive or `suspend` client generation modes in Kora 2.0, and the controller method that
calls the client is itself synchronous, running on the Undertow virtual thread that carries the request.

## Configuration { #config }

Because the generated client was created with `clientConfigPrefix = "httpClient"` and the generated interface is named `UsersApi`, its runtime config lives under `httpClient.usersApi` — with a
lower-case first letter.

Update `src/main/resources/application.conf`:

For the full configuration reference, see [HTTP Server](../documentation/http-server.md#configuration), [HTTP Client](../documentation/http-client.md#configuration) and [Logging SLF4J](../documentation/logging-slf4j.md).

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
      port = 8081 //(1)!
      system.port = 8086 //(2)!
      telemetry.logging.enabled = true //(3)!
    }

    httpClient {
      usersApi { //(4)!
        url = "http://localhost:8080" //(5)!
        url = ${?PUBLIC_API_URL} //(6)!
        requestTimeout = 10s //(7)!
      }
      telemetry.logging.enabled = true //(8)!
    }

    logging {
      levels {
        "ROOT": "INFO" //(9)!
        "io.koraframework": "INFO" //(10)!
        "io.koraframework.guide.openapi.httpclient": "INFO" //(11)!
      }
    }
    ```

    1.  This app runs next to the server app, so it uses a different public port.
    2.  And a different system port, for the same reason.
    3.  Enables request logging for the public HTTP server (default: `false`).
    4.  The generated interface name with a **lower-case first letter**. `UsersApi` here would not be read.
    5.  Base URL of the OpenAPI server application.
    6.  Optional override from the `PUBLIC_API_URL` environment variable, which is what the container-based test sets.
    7.  Maximum time allowed for one client request.
    8.  Enables client request logging (default: `false`).
    9.  Log level for the root logger.
    10. Log level for Kora framework loggers.
    11. Log level for the application package.

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      port: 8081 #(1)!
      system:
        port: 8086 #(2)!
      telemetry:
        logging:
          enabled: true #(3)!
    httpClient:
      usersApi: #(4)!
        url: "http://localhost:8080" #(5)!
        requestTimeout: 10s #(6)!
      telemetry:
        logging:
          enabled: true #(7)!
    logging:
      levels:
        ROOT: "INFO" #(8)!
        "io.koraframework": "INFO" #(9)!
        "io.koraframework.guide.openapi.httpclient": "INFO" #(10)!
    ```

    1.  This app runs next to the server app, so it uses a different public port.
    2.  And a different system port, for the same reason.
    3.  Enables request logging for the public HTTP server (default: `false`).
    4.  The generated interface name with a **lower-case first letter**. `UsersApi` here would not be read.
    5.  Base URL of the OpenAPI server application.
    6.  Maximum time allowed for one client request.
    7.  Enables client request logging (default: `false`).
    8.  Log level for the root logger.
    9.  Log level for Kora framework loggers.
    10. Log level for the application package.

This step introduces a subtle but important idea.

In the handwritten client guide, you decided the config path yourself in `@HttpClient(...)`. Here, the generator decides that annotation for you from `clientConfigPrefix` and the generated API name. So
when something seems "missing" at runtime, the first thing to check is what config path the generated interface actually declares — or simply read it from the generator's log line.

The rest of the client options — per-operation blocks named after the `operationId`, connection settings, telemetry — behave exactly as for a handwritten client and are described in
[HTTP Client](../documentation/http-client.md#configuration).

## Check Application { #check-app }

If you want to verify the flow manually, run both applications in separate terminals.

### Terminal 1: OpenAPI Server { #terminal-1-openapi-server }

From the OpenAPI server app of the previous guide:

```bash
./gradlew run
```

This application exposes:

- the user API on `http://localhost:8080`
- `/openapi`
- `/swagger-ui`

### Terminal 2: OpenAPI Client { #terminal-2-openapi-client }

From this client app:

```bash
./gradlew run
```

This application exposes its own aggregate verification endpoint on `http://localhost:8081/client/test-all-user-endpoints`.

Now trigger the whole client scenario:

```bash
curl -X POST http://localhost:8081/client/test-all-user-endpoints
```

Expected result: a JSON object where `allTestsPassed` is `true`.

If instead the call hangs for `requestTimeout` and then reports an error, the config section name is the first suspect: a client whose config path does not match reads no `url` at all.

## Testing { #testing }

Manual two-terminal runs are fine for exploring, but the real check is automated. The guide app points the generated client at a containerized copy of the OpenAPI server application, so the test
exercises the actual contract on both sides.

First a small container definition that builds the server app's own `Dockerfile` and waits for its readiness probe:

===! ":fontawesome-brands-java: `Java`"

    Create `src/test/java/io/koraframework/guide/openapi/httpclient/AppContainer.java`:

    ```java
    package io.koraframework.guide.openapi.httpclient;

    import java.net.URI;
    import java.nio.file.Path;
    import java.time.Duration;
    import org.testcontainers.containers.GenericContainer;
    import org.testcontainers.containers.wait.strategy.Wait;
    import org.testcontainers.images.builder.ImageFromDockerfile;

    final class AppContainer extends GenericContainer<AppContainer> {

        AppContainer() {
            super(new ImageFromDockerfile("guide-openapi-http-server-black-box")
                    .withDockerfile(Path.of("../kora-java-guide-openapi-http-server-app/Dockerfile")));

            withExposedPorts(8080, 8085);
            withStartupTimeout(Duration.ofSeconds(30));
            waitingFor(Wait.forHttp("/system/readiness").forPort(8085).forStatusCode(200)); //(1)!
        }

        URI getURI() {
            return URI.create("http://" + getHost() + ":" + getMappedPort(8080));
        }
    }
    ```

    1.  The system port carries the readiness probe, so the test starts only once the graph is fully up.

    The image is built from the server module's distribution, so the test task must depend on it:

    ```groovy
    test {
        dependsOn ":guides:java:kora-java-guide-openapi-http-server-app:distTar"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/test/kotlin/io/koraframework/guide/openapi/httpclient/AppContainer.kt`:

    ```kotlin
    package io.koraframework.guide.openapi.httpclient

    import org.testcontainers.containers.GenericContainer
    import org.testcontainers.containers.wait.strategy.Wait
    import org.testcontainers.images.builder.ImageFromDockerfile
    import java.net.URI
    import java.nio.file.Path
    import java.time.Duration

    class AppContainer : GenericContainer<AppContainer>(
        ImageFromDockerfile("guide-kotlin-openapi-http-server-black-box")
            .withDockerfile(Path.of("../kora-kotlin-guide-openapi-http-server-app/Dockerfile"))
    ) {
        init {
            withExposedPorts(8080, 8085)
            withStartupTimeout(Duration.ofSeconds(30))
            waitingFor(Wait.forHttp("/system/readiness").forPort(8085).forStatusCode(200)) //(1)!
        }

        fun getURI(): URI = URI.create("http://$host:${getMappedPort(8080)}")
    }
    ```

    1.  The system port carries the readiness probe, so the test starts only once the graph is fully up.

    The image is built from the server module's distribution, so the test task must depend on it:

    ```kotlin
    tasks.test {
        dependsOn(":guides:kotlin:kora-kotlin-guide-openapi-http-server-app:distTar")
    }
    ```

Then the test itself. The container's port is random, so `KoraAppTestConfigModifier` feeds the real URI into the `PUBLIC_API_URL` override that `application.conf` already reads:

===! ":fontawesome-brands-java: `Java`"

    Create `src/test/java/io/koraframework/guide/openapi/httpclient/OpenApiHttpClientAppTest.java`:

    ```java
    package io.koraframework.guide.openapi.httpclient;

    import static org.junit.jupiter.api.Assertions.assertEquals;
    import static org.junit.jupiter.api.Assertions.assertInstanceOf;
    import static org.junit.jupiter.api.Assertions.assertNotNull;

    import java.util.UUID;
    import org.junit.jupiter.api.Test;
    import org.testcontainers.junit.jupiter.Container;
    import org.testcontainers.junit.jupiter.Testcontainers;
    import io.koraframework.guide.openapi.httpclient.user.api.UsersApi;
    import io.koraframework.guide.openapi.httpclient.user.api.UsersApiResponses;
    import io.koraframework.guide.openapi.httpclient.user.model.UserRequestTO;
    import io.koraframework.test.extension.junit5.KoraAppTest;
    import io.koraframework.test.extension.junit5.KoraAppTestConfigModifier;
    import io.koraframework.test.extension.junit5.KoraConfigModification;
    import io.koraframework.test.extension.junit5.TestComponent;

    @Testcontainers
    @KoraAppTest(Application.class)
    class OpenApiHttpClientAppTest implements KoraAppTestConfigModifier {

        @Container
        static final AppContainer APP = new AppContainer();

        @TestComponent
        private UsersApi usersApi; //(1)!

        @Override
        public KoraConfigModification config() {
            return KoraConfigModification.ofResourceFile("application.conf")
                    .withSystemProperty("PUBLIC_API_URL", APP.getURI().toString()); //(2)!
        }

        @Test
        void createUserReturnsCreatedUserFromContainerizedOpenApiHttpServerApp() {
            String unique = UUID.randomUUID().toString().substring(0, 8);
            var response = this.usersApi.createUser(new UserRequestTO("Client User " + unique, "client-" + unique + "@example.com"));
            var create201 = assertInstanceOf(UsersApiResponses.CreateUserApiResponse.CreateUser201ApiResponse.class, response);

            assertNotNull(create201.content());
            assertEquals("Client User " + unique, create201.content().name());
        }

        @Test
        void getMissingUserReturnsNotFoundResponseFromContainerizedOpenApiHttpServerApp() {
            var response = this.usersApi.getUser("999999");
            assertInstanceOf(UsersApiResponses.GetUserApiResponse.GetUser404ApiResponse.class, response); //(3)!
        }
    }
    ```

    1.  The generated client is resolved from the real graph, so the test covers configuration binding too.
    2.  The container port is assigned at runtime, so the URL is injected rather than hard-coded.
    3.  A `404` is a normal return value here, not an exception — which is exactly what makes generated wrappers pleasant to assert on.

=== ":simple-kotlin: `Kotlin`"

    Create `src/test/kotlin/io/koraframework/guide/openapi/httpclient/OpenApiHttpClientAppTest.kt`:

    ```kotlin
    package io.koraframework.guide.openapi.httpclient

    import org.junit.jupiter.api.Assertions.assertEquals
    import org.junit.jupiter.api.Assertions.assertInstanceOf
    import org.junit.jupiter.api.Assertions.assertNotNull
    import org.junit.jupiter.api.Test
    import org.testcontainers.junit.jupiter.Container
    import org.testcontainers.junit.jupiter.Testcontainers
    import io.koraframework.guide.openapi.httpclient.user.api.UsersApi
    import io.koraframework.guide.openapi.httpclient.user.api.UsersApiResponses
    import io.koraframework.guide.openapi.httpclient.user.model.UserRequestTO
    import io.koraframework.test.extension.junit5.KoraAppTest
    import io.koraframework.test.extension.junit5.KoraAppTestConfigModifier
    import io.koraframework.test.extension.junit5.KoraConfigModification
    import io.koraframework.test.extension.junit5.TestComponent
    import java.util.UUID

    @Testcontainers
    @KoraAppTest(Application::class)
    class OpenApiHttpClientAppTest : KoraAppTestConfigModifier {

        @TestComponent
        lateinit var usersApi: UsersApi //(1)!

        override fun config(): KoraConfigModification =
            KoraConfigModification.ofResourceFile("application.conf")
                .withSystemProperty("PUBLIC_API_URL", APP.getURI().toString()) //(2)!

        @Test
        fun createUserReturnsCreatedUserFromContainerizedOpenApiHttpServerApp() {
            val unique = UUID.randomUUID().toString().substring(0, 8)
            val response = usersApi.createUser(
                UserRequestTO(name = "Client User $unique", email = "client-$unique@example.com")
            )
            val create201 =
                assertInstanceOf(UsersApiResponses.CreateUserApiResponse.CreateUser201ApiResponse::class.java, response)

            assertNotNull(create201.content)
            assertEquals("Client User $unique", create201.content.name)
        }

        @Test
        fun getMissingUserReturnsNotFoundResponseFromContainerizedOpenApiHttpServerApp() {
            val response = usersApi.getUser("999999")
            assertInstanceOf(UsersApiResponses.GetUserApiResponse.GetUser404ApiResponse::class.java, response) //(3)!
        }

        companion object {
            @Container
            @JvmStatic
            val APP: AppContainer = AppContainer()
        }
    }
    ```

    1.  The generated client is resolved from the real graph, so the test covers configuration binding too.
    2.  The container port is assigned at runtime, so the URL is injected rather than hard-coded.
    3.  A `404` is a normal return value here, not an exception — which is exactly what makes generated wrappers pleasant to assert on.

Run:

```bash
./gradlew test
```

These tests verify the same basic flow as the handwritten client guide — create user, get user, missing user, list users with paging and sorting, delete user. That makes the comparison between the two
guides easy to understand:

- [HTTP Client](http-client.md) proves the flow with a handwritten declarative client
- this guide proves the same flow with a generated OpenAPI client

## Best Practices { #best-practices }

- Reuse the exact same OpenAPI contract between server and client whenever possible; publish it as a shared artifact once the two applications live in different repositories.
- Treat generated code as build output, not as application code you edit or commit.
- Keep application logic outside the generated client, in your own controller or service classes.
- Read the generator's log line to confirm the client configuration path instead of guessing at capitalization.
- Convert enum wire values with `fromValue`, never with `Enum.valueOf` / `enumValueOf`.
- In `Kotlin`, always construct generated models with named arguments.
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
- Kora generates a typed HTTP client from OpenAPI in two client modes: `java-client` and `kotlin-client`
- a client mode requires `clientConfig` or `clientConfigPrefix`, and the prefix form lower-cases the first letter of the API name
- generated response wrappers such as `GetUserApiResponse` and `DeleteUserApiResponse` make HTTP outcomes explicit
- adding `500` to the OpenAPI file generates dedicated `500` response variants too; an undeclared status raises `HttpClientResponseException`
- `<Api><Operation>OptArgs` holders keep calls readable when an operation has many optional parameters
- generated enums are parsed with `fromValue`, and generated `Kotlin` models are safest with named arguments

## Troubleshooting { #troubleshooting }

**Generation fails with "Missing OpenAPI generator `clientConfig`":**

- A client mode needs a configuration path. Set either `clientConfigPrefix` or `clientConfig` in `configOptions`.
- The failure message suggests a `clientConfig` value derived from the contract file name, which is usually the right shape.

**Generation fails with "Invalid OpenAPI generator `mode`":**

- Kora 2.0 supports exactly four modes: `java-client`, `java-server`, `kotlin-client`, `kotlin-server`.
- The reactive and `suspend` client modes from earlier versions no longer exist; generated client code is synchronous.

**The generated client is missing from the graph:**

Check that:

- the OpenAPI generation task runs before compilation
- the generated output directory is added to the main source set
- the application includes an HTTP client transport module, such as `OkHttpClientModule`

**Every call hangs until the request timeout:**

That is the classic symptom of a configuration path mismatch: no section matched, so the client has no `url`.

Compare the section name in `application.conf` with the `@HttpClient(...)` value in the generated interface. With `clientConfigPrefix = "httpClient"` the generated client expects:

```text
httpClient.usersApi
```

not `httpClient.UsersApi` and not `httpClient`. The generator's log line after a successful run prints the exact path it expects.

**An enum value fails at runtime with `IllegalArgumentException` or `no enum constant`:**

- `Enum.valueOf` / `enumValueOf` matches the generated constant name, not the contract value. Use the generated `fromValue` method instead.
- This is why the failure only appears on real payloads: `AVAILABLE` and `available` compile identically well, but only one of them arrives over the wire.

**A `Kotlin` call sends the right values in the wrong fields:**

Generated `Kotlin` constructors put required properties first, so a positional call can compile and still swap two same-typed values. Switch that call to named arguments.

**The client and server models look similar but not identical:**

That often means the client is no longer using handwritten DTOs and is now using generated transport models from the OpenAPI contract. Make sure your application code imports `UserRequestTO` and
`UserResponseTO` from the generated package.

**The build succeeds but imports do not match:**

Check your generation settings in the build file: `outputDir`, `apiPackage`, `modelPackage`, `invokerPackage`. If those change, your controller imports must change too.

**The generated client does not expose a `500` response variant:**

Inspect the OpenAPI file first. Generated response variants only appear for status codes that are actually described in the contract. If you want explicit handling for `500`, it must be present in the
`responses` section of that operation in the shared OpenAPI file.

**A call throws `HttpClientResponseException` instead of returning a wrapper:**

The server answered with a status the contract does not declare, so no response mapper matched. Either add the status to the contract, or add a `default` response so the generator funnels unmatched
codes into one variant.

**Container-based tests cannot reach the server app:**

Check that:

- Docker is running
- the test task depends on the server module's `distTar`
- the server module `Dockerfile` points at its own generated distribution
- `PUBLIC_API_URL` is overridden from the container URI in the test config

## What's Next? { #whats-next }

- [Resilient Patterns](resilient.md) to make generated clients safer against slow or unstable dependencies.
- [Observability](observability.md) to trace generated client calls and measure status-specific outcomes.
- [HTTP Server Advanced](http-server-advanced.md) and then [HTTP Client Advanced](http-client-advanced.md) if you want to compare contract-generated clients with handwritten advanced clients.
- [OpenAPI HTTP Server Advanced](openapi-http-server-advanced.md) to see forms, multipart, interceptors, and contract-driven authorization on the server side.
- [gRPC Server](grpc-server.md) if you want to explore a strongly typed binary contract after OpenAPI.

## Help { #help }

If you get stuck:

- compare with [Kora Java OpenAPI HTTP Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-openapi-http-client-app) and [Kora Kotlin OpenAPI HTTP Client App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-openapi-http-client-app)
- revisit [HTTP Client](http-client.md) for the handwritten client baseline
- revisit [OpenAPI HTTP Server](openapi-http-server.md) for the server contract this client consumes
- check the [OpenAPI Codegen documentation](../documentation/openapi-codegen.md)
- check the [HTTP Client documentation](../documentation/http-client.md)
