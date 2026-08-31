---
search:
  exclude: true
title: HTTP Server Guide
summary: Learn how to build your first Kora HTTP API step by step, from one controller method to a full CRUD service
description: "Step-by-step Kora HTTP API: the io.koraframework:http-server-undertow module, UndertowPublicHttpServerModule, @HttpController and @HttpRoute routes, @Json request and response bodies, @Path and @Query binding, HttpResponseEntity and HttpServerResponse, HttpServerResponseException errors, a controller-service-repository split and the httpServer.port / httpServer.system.port configuration."
agent:
  use_when: "Use this file for questions about building a Kora REST API step by step: @HttpController, @HttpRoute, @Path, @Query, @Json DTOs, HttpResponseEntity, HttpServerResponse, HttpServerResponseException, UndertowPublicHttpServerModule, io.koraframework:http-server-undertow and json-common dependencies, httpServer.port and httpServer.system.port, readiness and liveness probes, and splitting a controller from a service and a repository."
tags: http-server, rest-api, json, routing, beginner
---

# HTTP Server Guide { #http-server-guide }

This guide introduces the core workflow for building HTTP APIs with Kora. It covers how `@HttpController` and `@HttpRoute` turn Java methods into HTTP endpoints, how `@Json`, `@Path`, and `@Query`
bind requests to typed application code, and how explicit response and exception APIs give each route clear HTTP behavior. You will also see how Kora's compile-time dependency graph connects
controllers, application services, repositories, JSON mappers, configuration, and the Undertow server into one runnable application.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java HTTP Server App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-http-server-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin HTTP Server App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-http-server-app).

## What You'll Build { #youll-build }

By the end of the guide, you will have:

- a `UserController` with CRUD routes
- request and response DTOs
- an in-memory `UserRepository`
- a `UserService` that holds application logic
- public API on port `8080`
- system API on port `8085`

## What You'll Need { #youll-need }

- JDK 25 or later
- Gradle 9+
- A text editor or IDE
- Completed [JSON Processing with Kora](json.md)

Kora 2.0 artifacts are compiled for Java 25, so the JDK that compiles the application must be 25 or newer.

## Prerequisites { #prerequisites }

!!! note "Required Foundation"

    This guide assumes you have completed **[JSON Processing with Kora](json.md)** and have a working Kora project with JSON DTO mapping available.

    If you haven't completed the JSON guide yet, do that first, because it already builds on the getting started guide and gives this HTTP API the JSON serialization patterns it needs.

## Overview { #overview }

Kora [HTTP](https://www.rfc-editor.org/rfc/rfc9110) servers are built around a simple idea: ordinary methods can become HTTP endpoints when their transport contract is declared explicitly. You write
controller classes, annotate routes and parameters, and Kora generates the request handling code during compilation.

That means an HTTP API in Kora is not built from low-level request parsing. It is built from typed method signatures and annotations that describe how HTTP data maps to application code.

### Controllers as Transport Adapters { #controllers-transport-adapters }

A controller is the HTTP boundary of the application. It should understand routes, request bodies, path variables, query parameters, status codes, and headers. It should not become the place where
every storage or business rule lives forever. That is why this guide gradually separates controller, service, and repository responsibilities.

Kora annotations describe how HTTP data enters and leaves controller methods:

- `@HttpController` marks a class as an HTTP controller
- `@HttpRoute` declares an HTTP method and path
- `@Json` maps JSON request and response bodies
- `@Path` maps route placeholders into method parameters
- `@Query` maps query-string values into method parameters

Request handling is **synchronous**. Undertow dispatches every request onto a virtual thread before the generated handler calls your method, so a controller method may block freely: it returns its
result directly and never returns `CompletionStage`, `Mono`/`Flux`, or a `suspend` function.

### Explicit HTTP Behavior { #explicit-http-behavior }

Simple methods can return DTOs directly, but real APIs often need more control. `HttpResponseEntity<T>` lets a route return a body with a specific status code or headers. `HttpServerResponse` is
useful for responses without a JSON body, such as `204 No Content`. `HttpServerResponseException` provides a direct way to end a request with a clear HTTP error.

These types keep HTTP behavior visible in the controller instead of hiding status codes inside unrelated service code.

### Application Layers { #application-layers }

The guide starts with one controller method, then introduces storage and application logic as separate concerns. The repository owns data access. The service owns application behavior. The controller
owns HTTP presentation. This layering is intentionally small, but it is the same shape that later guides reuse for databases, validation, caching, resilience, and observability.

The practical flow is:

1. add the HTTP server and JSON modules
2. create request and response DTOs
3. expose the first JSON route
4. add path and query parameter mapping
5. introduce repository and service layers
6. return explicit statuses, headers, and HTTP errors

## Dependencies { #dependencies }

The HTTP server lives in the `http-server-undertow` module, and JSON support lives in `json-common`. Both are Kora modules, so their versions come from the `io.koraframework:kora-bom` platform
instead of being written on every line.

===! ":fontawesome-brands-java: `Java`"

    Update `build.gradle`:

    ```groovy
    dependencies {
        koraBom platform("io.koraframework:kora-bom:2.0.0.RC1") //(1)!

        annotationProcessor "io.koraframework:annotation-processors" //(2)!

        implementation "io.koraframework:config-hocon" //(3)!
        implementation "io.koraframework:http-server-undertow" //(4)!
        implementation "io.koraframework:json-common" //(5)!
        implementation "io.koraframework:logging-logback" //(6)!
    }
    ```

    1.  Kora BOM: aligns the versions of every Kora module and of the libraries Kora depends on.
    2.  Kora annotation processor: generates the application graph, the controller modules, and the JSON readers/writers during compilation.
    3.  HOCON configuration reader for `application.conf`.
    4.  Undertow HTTP server transport.
    5.  Compile-time JSON infrastructure.
    6.  Logback logging implementation wired into the Kora graph.

=== ":simple-kotlin: `Kotlin`"

    Update `build.gradle.kts`:

    ```kotlin
    dependencies {
        implementation(platform("io.koraframework:kora-bom:2.0.0.RC1")) //(1)!

        ksp("io.koraframework:symbol-processors:2.0.0.RC1") //(2)!

        implementation("io.koraframework:config-hocon") //(3)!
        implementation("io.koraframework:http-server-undertow") //(4)!
        implementation("io.koraframework:json-common") //(5)!
        implementation("io.koraframework:logging-logback") //(6)!
    }
    ```

    1.  Kora BOM: aligns the versions of every Kora module and of the libraries Kora depends on.
    2.  Kora KSP processor: generates the application graph, the controller modules, and the JSON readers/writers during compilation.
    3.  HOCON configuration reader for `application.conf`.
    4.  Undertow HTTP server transport.
    5.  Compile-time JSON infrastructure.
    6.  Logback logging implementation wired into the Kora graph.

## Modules { #modules }

`UndertowPublicHttpServerModule` is the module to connect for an application that serves business endpoints. It extends `UndertowSystemHttpServerModule`, so one `extends` clause gives you two
servers in the same process: the public one on `httpServer.port` and the system one on `httpServer.system.port` that answers readiness, liveness, and metrics requests.

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/java/io/koraframework/guide/httpserver/Application.java`:

    ```java
    package io.koraframework.guide.httpserver;

    import io.koraframework.application.graph.KoraApplication;
    import io.koraframework.common.annotation.KoraApp;
    import io.koraframework.config.hocon.HoconConfigModule;
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule;
    import io.koraframework.json.common.JsonModule;
    import io.koraframework.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            UndertowPublicHttpServerModule {  // <----- Connected module

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update `src/main/kotlin/io/koraframework/guide/httpserver/Application.kt`:

    ```kotlin
    package io.koraframework.guide.httpserver

    import io.koraframework.application.graph.KoraApplication
    import io.koraframework.common.annotation.KoraApp
    import io.koraframework.config.hocon.HoconConfigModule
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule
    import io.koraframework.json.common.JsonModule
    import io.koraframework.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        UndertowPublicHttpServerModule  // <----- Connected module

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

## DTO { #dto }

Before we add any route, we need the shapes of the data we want to receive and return.

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/io/koraframework/guide/httpserver/dto/UserRequest.java`:

    ```java
    package io.koraframework.guide.httpserver.dto;

    import io.koraframework.json.common.annotation.Json;

    @Json
    public record UserRequest(String name, String email) {}
    ```

    Create `src/main/java/io/koraframework/guide/httpserver/dto/UserResponse.java`:

    ```java
    package io.koraframework.guide.httpserver.dto;

    import java.time.LocalDateTime;
    import io.koraframework.json.common.annotation.Json;

    @Json
    public record UserResponse(String id, String name, String email, LocalDateTime createdAt) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/io/koraframework/guide/httpserver/dto/UserRequest.kt`:

    ```kotlin
    package io.koraframework.guide.httpserver.dto

    import io.koraframework.json.common.annotation.Json

    @Json
    data class UserRequest(
        val name: String,
        val email: String
    )
    ```

    Create `src/main/kotlin/io/koraframework/guide/httpserver/dto/UserResponse.kt`:

    ```kotlin
    package io.koraframework.guide.httpserver.dto

    import io.koraframework.json.common.annotation.Json
    import java.time.LocalDateTime

    @Json
    data class UserResponse(
        val id: String,
        val name: String,
        val email: String,
        val createdAt: LocalDateTime
    )
    ```

`UserRequest` represents incoming JSON from the client.

`UserResponse` represents the JSON your API sends back.

Starting with DTOs makes the next steps easier because the controller signature already has stable, named types instead of anonymous maps or raw strings.

## Create User { #create-user }

Now we create the first controller and the first route. At this point we will **not** save anything yet. The goal of this step is to understand how Kora maps an HTTP request to a controller method.

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/io/koraframework/guide/httpserver/controller/UserController.java`:

    ```java
    package io.koraframework.guide.httpserver.controller;

    import java.time.LocalDateTime;
    import java.util.UUID;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.httpserver.dto.UserRequest;
    import io.koraframework.guide.httpserver.dto.UserResponse;
    import io.koraframework.http.common.HttpMethod;
    import io.koraframework.http.common.annotation.HttpRoute;
    import io.koraframework.http.server.common.annotation.HttpController;
    import io.koraframework.json.common.annotation.Json;

    @Component
    @HttpController
    public final class UserController {

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        public UserResponse createUser(@Json UserRequest request) {
            System.out.printf("Received createUser request: name=%s, email=%s%n", request.name(), request.email());
            return new UserResponse(
                    UUID.randomUUID().toString(),
                    request.name(),
                    request.email(),
                    LocalDateTime.now());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/io/koraframework/guide/httpserver/controller/UserController.kt`:

    ```kotlin
    package io.koraframework.guide.httpserver.controller

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.httpserver.dto.UserRequest
    import io.koraframework.guide.httpserver.dto.UserResponse
    import io.koraframework.http.common.HttpMethod
    import io.koraframework.http.common.annotation.HttpRoute
    import io.koraframework.http.server.common.annotation.HttpController
    import io.koraframework.json.common.annotation.Json
    import java.time.LocalDateTime
    import java.util.UUID

    @Component
    @HttpController
    class UserController {

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        fun createUser(@Json request: UserRequest): UserResponse {
            println("Received createUser request: name=${request.name}, email=${request.email}")
            return UserResponse(
                UUID.randomUUID().toString(),
                request.name,
                request.email,
                LocalDateTime.now()
            )
        }
    }
    ```

Let's break down what is happening here:

- `@Component`
  Kora should create this class and put it into the dependency graph.

- `@HttpController`
  This class contains HTTP routes. Kora scans it and generates the HTTP handler wiring.

- `@HttpRoute(method = HttpMethod.POST, path = "/users")`
  This method should handle `POST /users`. `HttpMethod` holds the standard HTTP method names as string constants.

- `@Json` on the method
  Kora should use the data mapper with the special `@Json` tag to serialize the return value to JSON.

- `@Json` on the parameter
  Kora should use the data mapper with the special `@Json` tag to deserialize the request body from JSON into `UserRequest`.

At this point the route already feels like a real API, but it still does not remember anything. Every call creates a new response object and returns it immediately.

Try it:

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com"}'
```

## Get User { #get-user }

The next natural route is `getUser`. But as soon as we add it, we hit an important design question: where do users live after `createUser` returns?

For now, we will add the route and deliberately return `404` to show that the controller already knows how to express HTTP-level failure.

===! ":fontawesome-brands-java: `Java`"

    Update `UserController.java`:

    ```java
    package io.koraframework.guide.httpserver.controller;

    import java.time.LocalDateTime;
    import java.util.UUID;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.httpserver.dto.UserRequest;
    import io.koraframework.guide.httpserver.dto.UserResponse;
    import io.koraframework.http.common.HttpMethod;
    import io.koraframework.http.common.annotation.HttpRoute;
    import io.koraframework.http.common.annotation.Path;
    import io.koraframework.http.server.common.annotation.HttpController;
    import io.koraframework.http.server.common.response.HttpServerResponseException;
    import io.koraframework.json.common.annotation.Json;

    @Component
    @HttpController
    public final class UserController {

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        public UserResponse createUser(@Json UserRequest request) {
            System.out.printf("Received createUser request: name=%s, email=%s%n", request.name(), request.email());
            return new UserResponse(
                    UUID.randomUUID().toString(),
                    request.name(),
                    request.email(),
                    LocalDateTime.now());
        }

        @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}")
        @Json
        public UserResponse getUser(@Path String userId) {
            throw HttpServerResponseException.of(404, "User not found: " + userId);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update `UserController.kt`:

    ```kotlin
    package io.koraframework.guide.httpserver.controller

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.httpserver.dto.UserRequest
    import io.koraframework.guide.httpserver.dto.UserResponse
    import io.koraframework.http.common.HttpMethod
    import io.koraframework.http.common.annotation.HttpRoute
    import io.koraframework.http.common.annotation.Path
    import io.koraframework.http.server.common.annotation.HttpController
    import io.koraframework.http.server.common.response.HttpServerResponseException
    import io.koraframework.json.common.annotation.Json
    import java.time.LocalDateTime
    import java.util.UUID

    @Component
    @HttpController
    class UserController {

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        fun createUser(@Json request: UserRequest): UserResponse {
            println("Received createUser request: name=${request.name}, email=${request.email}")
            return UserResponse(
                UUID.randomUUID().toString(),
                request.name,
                request.email,
                LocalDateTime.now()
            )
        }

        @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}")
        @Json
        fun getUser(@Path userId: String): UserResponse {
            throw HttpServerResponseException.of(404, "User not found: $userId")
        }
    }
    ```

Two new ideas appear here:

- `@Path String userId`
  Kora takes the `{userId}` part from the route path and passes it into the method.

- `HttpServerResponseException`
  This is a simple way to say "this request should end with this HTTP error". The exception is itself an `HttpServerResponse`, so the server writes its status and body without any extra mapping.

This step is intentionally incomplete. We now have enough controller behavior to see why a separate storage abstraction is needed.

## User Repository { #user-repository }

Now we add a repository layer. A repository is responsible for storing and retrieving data. In this guide we use an in-memory map because it keeps the example easy to run, but the abstraction itself
will later let us switch to a real database.

At first we only need two operations:

- save a user
- get a user by ID

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/io/koraframework/guide/httpserver/repository/UserRepository.java`:

    ```java
    package io.koraframework.guide.httpserver.repository;

    import java.util.Optional;
    import io.koraframework.guide.httpserver.dto.UserResponse;

    public interface UserRepository {

        String save(String name, String email);

        Optional<UserResponse> findById(String id);
    }
    ```

    Create `src/main/java/io/koraframework/guide/httpserver/repository/InMemoryUserRepository.java`:

    ```java
    package io.koraframework.guide.httpserver.repository;

    import java.time.LocalDateTime;
    import java.util.Map;
    import java.util.Optional;
    import java.util.concurrent.ConcurrentHashMap;
    import java.util.concurrent.atomic.AtomicLong;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.httpserver.dto.UserResponse;

    @Component
    public final class InMemoryUserRepository implements UserRepository {

        private final Map<String, UserResponse> users = new ConcurrentHashMap<>();
        private final AtomicLong idGenerator = new AtomicLong(1);

        @Override
        public String save(String name, String email) {
            String id = String.valueOf(idGenerator.getAndIncrement());
            users.put(id, new UserResponse(id, name, email, LocalDateTime.now()));
            return id;
        }

        @Override
        public Optional<UserResponse> findById(String id) {
            return Optional.ofNullable(users.get(id));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/io/koraframework/guide/httpserver/repository/UserRepository.kt`:

    ```kotlin
    package io.koraframework.guide.httpserver.repository

    import io.koraframework.guide.httpserver.dto.UserResponse

    interface UserRepository {
        fun save(name: String, email: String): String
        fun findById(id: String): UserResponse?
    }
    ```

    Create `src/main/kotlin/io/koraframework/guide/httpserver/repository/InMemoryUserRepository.kt`:

    ```kotlin
    package io.koraframework.guide.httpserver.repository

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.httpserver.dto.UserResponse
    import java.time.LocalDateTime
    import java.util.concurrent.ConcurrentHashMap
    import java.util.concurrent.atomic.AtomicLong

    @Component
    class InMemoryUserRepository : UserRepository {

        private val users = ConcurrentHashMap<String, UserResponse>()
        private val idGenerator = AtomicLong(1)

        override fun save(name: String, email: String): String {
            val id = idGenerator.getAndIncrement().toString()
            users[id] = UserResponse(id, name, email, LocalDateTime.now())
            return id
        }

        override fun findById(id: String): UserResponse? = users[id]
    }
    ```

The repository does not know anything about HTTP. It only knows how to store and load user data. That separation is important because storage concerns and HTTP concerns change for different reasons.

Because every request runs on its own virtual thread, the in-memory storage is shared state: `ConcurrentHashMap` and `AtomicLong` are used deliberately instead of their non-thread-safe counterparts.

## Controller to Repository { #controller-repository }

Now that we have storage, we can go back to the controller and make `createUser` and `getUser` actually work together.

===! ":fontawesome-brands-java: `Java`"

    Update `UserController.java`:

    ```java
    package io.koraframework.guide.httpserver.controller;

    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.httpserver.dto.UserRequest;
    import io.koraframework.guide.httpserver.dto.UserResponse;
    import io.koraframework.guide.httpserver.repository.UserRepository;
    import io.koraframework.http.common.HttpMethod;
    import io.koraframework.http.common.annotation.HttpRoute;
    import io.koraframework.http.common.annotation.Path;
    import io.koraframework.http.server.common.annotation.HttpController;
    import io.koraframework.http.server.common.response.HttpServerResponseException;
    import io.koraframework.json.common.annotation.Json;

    @Component
    @HttpController
    public final class UserController {

        private final UserRepository userRepository;

        public UserController(UserRepository userRepository) {
            this.userRepository = userRepository;
        }

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        public UserResponse createUser(@Json UserRequest request) {
            String id = userRepository.save(request.name(), request.email());
            return userRepository.findById(id)
                    .orElseThrow(() -> new IllegalStateException("Saved user not found"));
        }

        @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}")
        @Json
        public UserResponse getUser(@Path String userId) {
            return userRepository.findById(userId)
                    .orElseThrow(() -> HttpServerResponseException.of(404, "User not found: " + userId));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update `UserController.kt`:

    ```kotlin
    package io.koraframework.guide.httpserver.controller

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.httpserver.dto.UserRequest
    import io.koraframework.guide.httpserver.dto.UserResponse
    import io.koraframework.guide.httpserver.repository.UserRepository
    import io.koraframework.http.common.HttpMethod
    import io.koraframework.http.common.annotation.HttpRoute
    import io.koraframework.http.common.annotation.Path
    import io.koraframework.http.server.common.annotation.HttpController
    import io.koraframework.http.server.common.response.HttpServerResponseException
    import io.koraframework.json.common.annotation.Json

    @Component
    @HttpController
    class UserController(
        private val userRepository: UserRepository
    ) {

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        fun createUser(@Json request: UserRequest): UserResponse {
            val id = userRepository.save(request.name, request.email)
            return userRepository.findById(id)
                ?: error("Saved user not found")
        }

        @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}")
        @Json
        fun getUser(@Path userId: String): UserResponse {
            return userRepository.findById(userId)
                ?: throw HttpServerResponseException.of(404, "User not found: $userId")
        }
    }
    ```

This is the first moment where the API becomes stateful. You can now call `createUser`, get an ID back, and then use that ID in `getUser`.

`UserRepository` is an interface, and `InMemoryUserRepository` is the `@Component` that implements it. The controller asks for the interface in its constructor, and Kora resolves that edge of the
graph during compilation — if the implementation were missing, the build would fail with `No component found for dependency` instead of failing at runtime.

## CRUD Repository { #crud-repository }

The API already works for create and get. Before adding more HTTP routes, we first make the storage abstraction capable of the full CRUD flow:

- list users
- update users
- delete users

This keeps the repository focused on storage operations only. The controller will start using these operations in the next section, after we introduce a service layer between HTTP routing and storage.

===! ":fontawesome-brands-java: `Java`"

    Expand `UserRepository.java`:

    ```java
    package io.koraframework.guide.httpserver.repository;

    import java.util.List;
    import java.util.Optional;
    import io.koraframework.guide.httpserver.dto.UserResponse;

    public interface UserRepository {

        List<UserResponse> findAll();

        Optional<UserResponse> findById(String id);

        String save(String name, String email);

        boolean update(String id, String name, String email);

        boolean deleteById(String id);
    }
    ```

    Expand `InMemoryUserRepository.java`:

    ```java
    package io.koraframework.guide.httpserver.repository;

    import java.time.LocalDateTime;
    import java.util.ArrayList;
    import java.util.List;
    import java.util.Map;
    import java.util.Optional;
    import java.util.concurrent.ConcurrentHashMap;
    import java.util.concurrent.atomic.AtomicLong;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.httpserver.dto.UserResponse;

    @Component
    public final class InMemoryUserRepository implements UserRepository {

        private final Map<String, UserResponse> users = new ConcurrentHashMap<>();
        private final AtomicLong idGenerator = new AtomicLong(1);

        @Override
        public List<UserResponse> findAll() {
            return new ArrayList<>(users.values());
        }

        @Override
        public Optional<UserResponse> findById(String id) {
            return Optional.ofNullable(users.get(id));
        }

        @Override
        public String save(String name, String email) {
            String id = String.valueOf(idGenerator.getAndIncrement());
            users.put(id, new UserResponse(id, name, email, LocalDateTime.now()));
            return id;
        }

        @Override
        public boolean update(String id, String name, String email) {
            return users.computeIfPresent(id,
                    (k, v) -> new UserResponse(k, name, email, v.createdAt())) != null;
        }

        @Override
        public boolean deleteById(String id) {
            return users.remove(id) != null;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Expand `UserRepository.kt`:

    ```kotlin
    package io.koraframework.guide.httpserver.repository

    import io.koraframework.guide.httpserver.dto.UserResponse

    interface UserRepository {
        fun findAll(): List<UserResponse>
        fun findById(id: String): UserResponse?
        fun save(name: String, email: String): String
        fun update(id: String, name: String, email: String): Boolean
        fun deleteById(id: String): Boolean
    }
    ```

    Expand `InMemoryUserRepository.kt`:

    ```kotlin
    package io.koraframework.guide.httpserver.repository

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.httpserver.dto.UserResponse
    import java.time.LocalDateTime
    import java.util.concurrent.ConcurrentHashMap
    import java.util.concurrent.atomic.AtomicLong

    @Component
    class InMemoryUserRepository : UserRepository {

        private val users = ConcurrentHashMap<String, UserResponse>()
        private val idGenerator = AtomicLong(1)

        override fun findAll(): List<UserResponse> = users.values.toList()

        override fun findById(id: String): UserResponse? = users[id]

        override fun save(name: String, email: String): String {
            val id = idGenerator.getAndIncrement().toString()
            users[id] = UserResponse(id, name, email, LocalDateTime.now())
            return id
        }

        override fun update(id: String, name: String, email: String): Boolean {
            return users.computeIfPresent(id) { key, current -> UserResponse(key, name, email, current.createdAt) } != null
        }

        override fun deleteById(id: String): Boolean = users.remove(id) != null
    }
    ```

At this stage the repository can store, list, update, and delete users, but the HTTP API still exposes only the routes from the previous section. Next we add a service layer and then connect the full
CRUD behavior to the controller.

## Service Layer { #service-layer }

In many applications the controller is treated as the presentation layer, while the service layer holds application logic. This is especially common in MVC-style applications and in services that
later grow more rules, integrations, and reuse points.

The repository now has every storage operation the API needs. The service layer turns those operations into application behavior:

- it creates users from request DTOs
- it sorts and pages the in-memory list
- it maps repository update/delete results to business errors

After that, the controller can stay focused on HTTP routing, request binding, response codes, and headers.

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/io/koraframework/guide/httpserver/service/UserService.java`:

    ```java
    package io.koraframework.guide.httpserver.service;

    import java.time.LocalDateTime;
    import java.util.Comparator;
    import java.util.List;
    import java.util.Optional;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.httpserver.dto.UserRequest;
    import io.koraframework.guide.httpserver.dto.UserResponse;
    import io.koraframework.guide.httpserver.repository.UserRepository;
    import io.koraframework.http.server.common.response.HttpServerResponseException;

    @Component
    public final class UserService {

        private final UserRepository userRepository;

        public UserService(UserRepository userRepository) {
            this.userRepository = userRepository;
        }

        public UserResponse createUser(UserRequest request) {
            var generatedId = userRepository.save(request.name(), request.email());
            return new UserResponse(generatedId, request.name(), request.email(), LocalDateTime.now());
        }

        public Optional<UserResponse> getUser(String id) {
            return userRepository.findById(id);
        }

        public List<UserResponse> getUsers(int page, int size, String sort) {
            return userRepository.findAll().stream()
                    .sorted(getComparator(sort))
                    .skip((long) page * size)
                    .limit(size)
                    .toList();
        }

        public UserResponse updateUser(String id, UserRequest request) {
            boolean updated = userRepository.update(id, request.name(), request.email());
            if (!updated) {
                throw HttpServerResponseException.of(404, "User not found: " + id);
            }
            return new UserResponse(id, request.name(), request.email(), LocalDateTime.now());
        }

        public void deleteUser(String id) {
            boolean deleted = userRepository.deleteById(id);
            if (!deleted) {
                throw HttpServerResponseException.of(404, "User not found: " + id);
            }
        }

        private Comparator<UserResponse> getComparator(String sort) {
            return switch (sort.toLowerCase()) {
                case "name" -> Comparator.comparing(UserResponse::name);
                case "email" -> Comparator.comparing(UserResponse::email);
                case "createdat" -> Comparator.comparing(UserResponse::createdAt);
                default -> Comparator.comparing(UserResponse::name);
            };
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/io/koraframework/guide/httpserver/service/UserService.kt`:

    ```kotlin
    package io.koraframework.guide.httpserver.service

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.httpserver.dto.UserRequest
    import io.koraframework.guide.httpserver.dto.UserResponse
    import io.koraframework.guide.httpserver.repository.UserRepository
    import io.koraframework.http.server.common.response.HttpServerResponseException
    import java.time.LocalDateTime

    @Component
    class UserService(
        private val userRepository: UserRepository
    ) {

        fun createUser(request: UserRequest): UserResponse {
            val generatedId = userRepository.save(request.name, request.email)
            return UserResponse(generatedId, request.name, request.email, LocalDateTime.now())
        }

        fun getUser(id: String): UserResponse? = userRepository.findById(id)

        fun getUsers(page: Int, size: Int, sort: String): List<UserResponse> =
            userRepository.findAll()
                .sortedWith(getComparator(sort))
                .drop(page * size)
                .take(size)

        fun updateUser(id: String, request: UserRequest): UserResponse {
            if (!userRepository.update(id, request.name, request.email)) {
                throw HttpServerResponseException.of(404, "User not found: $id")
            }
            return UserResponse(id, request.name, request.email, LocalDateTime.now())
        }

        fun deleteUser(id: String) {
            if (!userRepository.deleteById(id)) {
                throw HttpServerResponseException.of(404, "User not found: $id")
            }
        }

        private fun getComparator(sort: String): Comparator<UserResponse> = when (sort.lowercase()) {
            "name" -> compareBy { it.name }
            "email" -> compareBy { it.email }
            "createdat" -> compareBy { it.createdAt }
            else -> compareBy { it.name }
        }
    }
    ```

`UserService` throws `HttpServerResponseException` for "not found" so the guide stays short. In a larger application the service would usually throw a domain exception and one global interceptor would
translate it into an HTTP status — that is exactly what the [HTTP Server Advanced](http-server-advanced.md) guide builds next.

## Controller and Service { #controller-service }

Now the controller can expose the full CRUD API without owning storage or application logic. It receives HTTP requests, binds route and query parameters, delegates work to `UserService`, and chooses
the HTTP response shape for each route.

This step also adds the remaining HTTP-specific pieces:

- `@Query` maps query-string values such as `?page=0&size=10&sort=name` into controller parameters
- a nullable parameter type marks an optional query parameter
- `HttpResponseEntity<T>` returns a JSON body together with an explicit status code or headers
- `HttpServerResponse` returns responses without a JSON body, such as `204 No Content`

In Java, optional parameters are marked with JSpecify `@Nullable` from `org.jspecify.annotations`; in Kotlin the `?` on the parameter type is enough and no annotation is needed. A `@Query` parameter
that is neither nullable nor optional is required, and a request without it is answered with `400` before the controller method runs.

===! ":fontawesome-brands-java: `Java`"

    Rewrite `UserController.java` to delegate to the service:

    ```java
    package io.koraframework.guide.httpserver.controller;

    import org.jspecify.annotations.Nullable;
    import java.time.Instant;
    import java.util.List;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.httpserver.dto.UserRequest;
    import io.koraframework.guide.httpserver.dto.UserResponse;
    import io.koraframework.guide.httpserver.service.UserService;
    import io.koraframework.http.common.HttpMethod;
    import io.koraframework.http.common.HttpResponseEntity;
    import io.koraframework.http.common.annotation.HttpRoute;
    import io.koraframework.http.common.annotation.Path;
    import io.koraframework.http.common.annotation.Query;
    import io.koraframework.http.common.body.HttpBody;
    import io.koraframework.http.common.header.HttpHeaders;
    import io.koraframework.http.server.common.annotation.HttpController;
    import io.koraframework.http.server.common.response.HttpServerResponse;
    import io.koraframework.http.server.common.response.HttpServerResponseException;
    import io.koraframework.json.common.annotation.Json;

    @Component
    @HttpController
    public final class UserController {

        private final UserService userService;

        public UserController(UserService userService) {
            this.userService = userService;
        }

        @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}")
        @Json
        public UserResponse getUser(@Path String userId) {
            return userService.getUser(userId)
                    .orElseThrow(() -> HttpServerResponseException.of(404, "User not found: " + userId));
        }

        @HttpRoute(method = HttpMethod.GET, path = "/users")
        @Json
        public List<UserResponse> getUsers(
                @Nullable @Query("page") Integer page,
                @Nullable @Query("size") Integer size,
                @Nullable @Query("sort") String sort) {
            int pageNum = page == null ? 0 : page;
            int pageSize = size == null ? 10 : size;
            String sortBy = sort == null ? "name" : sort;
            return userService.getUsers(pageNum, pageSize, sortBy);
        }

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        public HttpResponseEntity<UserResponse> createUser(@Json UserRequest request) {
            UserResponse user = userService.createUser(request);
            return HttpResponseEntity.of(201, HttpHeaders.of(), user);
        }

        @HttpRoute(method = HttpMethod.PUT, path = "/users/{userId}")
        @Json
        public HttpResponseEntity<UserResponse> updateUser(@Path String userId, @Json UserRequest request) {
            UserResponse updated = userService.updateUser(userId, request);
            return HttpResponseEntity.of(200, HttpHeaders.of("X-Updated-At", Instant.now().toString()), updated);
        }

        @HttpRoute(method = HttpMethod.DELETE, path = "/users/{userId}")
        public HttpServerResponse deleteUser(@Path String userId) {
            userService.deleteUser(userId);
            return HttpServerResponse.of(204, HttpBody.empty());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Rewrite `UserController.kt` to delegate to the service:

    ```kotlin
    package io.koraframework.guide.httpserver.controller

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.httpserver.dto.UserRequest
    import io.koraframework.guide.httpserver.dto.UserResponse
    import io.koraframework.guide.httpserver.service.UserService
    import io.koraframework.http.common.HttpMethod
    import io.koraframework.http.common.HttpResponseEntity
    import io.koraframework.http.common.annotation.HttpRoute
    import io.koraframework.http.common.annotation.Path
    import io.koraframework.http.common.annotation.Query
    import io.koraframework.http.common.body.HttpBody
    import io.koraframework.http.common.header.HttpHeaders
    import io.koraframework.http.server.common.annotation.HttpController
    import io.koraframework.http.server.common.response.HttpServerResponse
    import io.koraframework.http.server.common.response.HttpServerResponseException
    import io.koraframework.json.common.annotation.Json
    import java.time.Instant

    @Component
    @HttpController
    class UserController(
        private val userService: UserService
    ) {

        @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}")
        @Json
        fun getUser(@Path userId: String): UserResponse =
            userService.getUser(userId) ?: throw HttpServerResponseException.of(404, "User not found: $userId")

        @HttpRoute(method = HttpMethod.GET, path = "/users")
        @Json
        fun getUsers(
            @Query("page") page: Int?,
            @Query("size") size: Int?,
            @Query("sort") sort: String?
        ): List<UserResponse> =
            userService.getUsers(page ?: 0, size ?: 10, sort ?: "name")

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        fun createUser(@Json request: UserRequest): HttpResponseEntity<UserResponse> =
            HttpResponseEntity.of(201, HttpHeaders.of(), userService.createUser(request))

        @HttpRoute(method = HttpMethod.PUT, path = "/users/{userId}")
        @Json
        fun updateUser(@Path userId: String, @Json request: UserRequest): HttpResponseEntity<UserResponse> =
            HttpResponseEntity.of(
                200,
                HttpHeaders.of("X-Updated-At", Instant.now().toString()),
                userService.updateUser(userId, request)
            )

        @HttpRoute(method = HttpMethod.DELETE, path = "/users/{userId}")
        fun deleteUser(@Path userId: String): HttpServerResponse {
            userService.deleteUser(userId)
            return HttpServerResponse.of(204, HttpBody.empty())
        }
    }
    ```

This is the final structure used by the runnable companion app. The behavior did not change, but the architecture became cleaner:

- controller = HTTP presentation
- repository = storage abstraction
- service = application logic

Note how the return type of each route decides which mapper Kora looks up at compile time:

- `UserResponse` and `List<UserResponse>` with `@Json` need a `JsonWriter` for the type, which `@Json` on the DTO generates
- `HttpResponseEntity<UserResponse>` reuses the same JSON writer and adds the status code and headers on top
- `HttpServerResponse` is returned as-is and needs no mapper at all

## Configuration { #config }

Now that the application structure is in place, we can wire the HTTP server configuration itself.

Create or update `src/main/resources/application.conf`:

For the full configuration reference, see [HTTP Server](../documentation/http-server.md#configuration) and [Logging SLF4J](../documentation/logging-slf4j.md).

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
      port = 8080 //(1)!
      system.port = 8085 //(2)!
      telemetry.logging.enabled = true //(3)!
    }

    logging {
      levels {
        "ROOT": "WARN" //(4)!
        "io.koraframework": "INFO" //(5)!
      }
    }
    ```

    1.  Public HTTP port used by application endpoints (default: `8080`).
    2.  System HTTP port used by probes, metrics, and management endpoints (default: `8085`).
    3.  Enables request logging for the public HTTP server (default: `false`).
    4.  Log level for the root logger.
    5.  Log level for Kora framework loggers.

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      port: 8080 #(1)!
      system:
        port: 8085 #(2)!
      telemetry:
        logging:
          enabled: true #(3)!
    logging:
      levels:
        ROOT: "WARN" #(4)!
        "io.koraframework": "INFO" #(5)!
    ```

    1.  Public HTTP port used by application endpoints (default: `8080`).
    2.  System HTTP port used by probes, metrics, and management endpoints (default: `8085`).
    3.  Enables request logging for the public HTTP server (default: `false`).
    4.  Log level for the root logger.
    5.  Log level for Kora framework loggers.

This gives you two ports:

- `8080` for the main application API
- `8085` for system endpoints such as readiness and liveness

That split is useful in real systems because health checks and operational endpoints are usually kept separate from public business traffic. Both keys already have those defaults, so the application
also starts without an `application.conf` at all; the file matters as soon as you need to move a port, raise a log level, or read a value from an environment variable.

## Check Applications { #check-app }

```bash
./gradlew clean classes
./gradlew test
./gradlew run
```

`classes` is the meaningful first check in Kora: it runs the annotation processor or KSP, generates the controller module and the application graph, and fails at compile time if a route or a
dependency cannot be wired.

Public API checks:

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com"}'

curl http://localhost:8080/users/1
curl "http://localhost:8080/users?page=0&size=10&sort=name"

curl -X PUT http://localhost:8080/users/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Name", "email": "updated@example.com"}'

curl -X DELETE http://localhost:8080/users/1
```

System API checks:

```bash
curl http://localhost:8085/system/readiness
# Expected output: OK
curl http://localhost:8085/system/liveness
# Expected output: OK
```

## Best Practices { #best-practices }

- Keep controller methods thin once the project grows beyond trivial handlers.
- Use repositories for storage concerns and services for application logic.
- Use `HttpResponseEntity` when you need explicit status codes or headers.
- Throw `HttpServerResponseException` when the controller or service needs to expose a clean HTTP error.
- Keep controller methods synchronous and let Undertow's virtual threads carry the blocking work.
- Guard any state shared between requests, because concurrent requests run on different threads.

## Summary { #summary }

You built a Kora HTTP API gradually:

- first one route without persistence
- then a second route that revealed the need for storage
- then a repository abstraction with an in-memory implementation
- then a repository contract expanded to support full CRUD
- and finally a service layer plus controller routes that expose the complete API

## Key Concepts { #key-concepts }

- Kora HTTP routing with `@HttpRoute`
- JSON request and response mapping with `@Json`
- request mapping with `@Path` and `@Query`
- response control with `HttpResponseEntity`
- HTTP error signaling with `HttpServerResponseException`
- the different responsibilities of controller, repository, and service
- one process, two HTTP servers: the public one and the system one

## Troubleshooting { #troubleshooting }

**Server does not start:**

- Check ports `8080` and `8085` availability.
- Verify `Application` includes `UndertowPublicHttpServerModule` and `HoconConfigModule`.

**Compilation fails with `No component found for dependency`:**

- The type listed in the message is not in the graph. Add `@Component` to its implementation, or provide it from a module method.
- A frequent case is forgetting `@Component` on `InMemoryUserRepository` or `UserService`.

**Compilation fails with `JsonWriter<T> was not found`:**

- The DTO returned by the route is not annotated with `@Json`, so no writer was generated for it.

**`getUser` always returns 404:**

- Check that `createUser` and `getUser` are already wired to the repository layer.
- Make sure you are calling `getUser` with an ID that was actually returned from `createUser`.

**Optional query parameters are not handled correctly:**

- In Java use nullable wrappers with `@Nullable @Query`, such as `Integer` and `String`, and import `@Nullable` from `org.jspecify.annotations`.
- In Kotlin declare the parameter type as nullable, for example `page: Int?`.
- A missing required query parameter is answered with `400` before the method is called.

**Kotlin build fails with `Suspend methods are not supported by the HTTP server controller generator`:**

- Remove `suspend` from the controller method. Kora HTTP handlers are synchronous and already run on a virtual thread.

**Build hangs or fails unexpectedly:**

- Run `./gradlew --stop`, then retry.

## What's Next? { #whats-next }

- [JSON Processing](json.md) to make HTTP request and response DTO mapping explicit.
- [Validation](validation.md) to add boundary checks around the same HTTP API.
- [Database JDBC](database-jdbc.md) or [Cassandra Database](database-cassandra.md) to replace the in-memory repository with real persistence.
- [HTTP Server Advanced](http-server-advanced.md) after the basic CRUD shape is comfortable.
- [HTTP Client](http-client.md) when you want another Kora application to call this API.

## Help { #help }

If you encounter issues:

- compare with [Kora Java HTTP Server App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-http-server-app) and [Kora Kotlin HTTP Server App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-http-server-app)
- check the [HTTP Server documentation](../documentation/http-server.md)
- check the [JSON documentation](../documentation/json.md)
