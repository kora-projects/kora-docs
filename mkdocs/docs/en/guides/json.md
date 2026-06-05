---
search:
  exclude: true
title: JSON Processing with Kora
summary: Learn how to handle JSON requests and responses in a Kora HTTP API with type-safe DTOs and sealed polymorphic responses
tags: json, http, api, serialization
---

# Working with JSON in Kora { #working-json-kora }

This guide introduces JSON request and response mapping in Kora. It covers how `@Json` selects JSON mappers for HTTP bodies, how request and response DTOs become the typed boundary of an API, and how
Kora generates serialization code through annotation processing. You will also see how JSON mapping fits into the compile-time dependency graph that powers the application.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java JSON App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-json-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin JSON App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-json-app).

## What You'll Build { #youll-build }

You will build a JSON-first HTTP API with:

- JSON request parsing for `POST /users`
- JSON response serialization for `GET /users`
- Polymorphic JSON response for `GET /users/{id}` using sealed types
- Type-safe DTO contracts for request and response models

## What You'll Need { #youll-need }

- JDK 17 or later
- Gradle 7+
- A text editor or IDE
- Completed [Creating Your First Kora App](getting-started.md)

## Prerequisites { #prerequisites }

!!! note "Required: Complete Basic Kora Setup"

    This guide assumes you have completed **[Creating Your First Kora App](getting-started.md)** and have a working Kora application graph with the HTTP server baseline in place.

    If you haven't completed the getting started guide yet, do that first, because this guide adds JSON request and response mapping on top of that baseline.

## Overview { #overview }

[JSON](https://www.json.org/json-en.html) is usually the first real data boundary in an HTTP API. A plain string response is enough to prove the server works, but real endpoints exchange structured
request and response objects. This guide shows how Kora turns those objects into JSON without making controller code manually parse or build JSON strings.

The important shift is that JSON becomes a transport representation, not the application model itself. Application code should work with typed objects, while the framework handles how those objects
are encoded on the wire.

### JSON Mapping in Kora { #json-mapping-kora }

Kora JSON support is based on generated mappers. When you add the JSON module and annotate HTTP bodies with `@Json`, Kora knows that the request body should be deserialized into a Java or Kotlin type
and the response value should be serialized back to JSON. The mapper code is generated at compile time, so missing or unsupported mappings are caught early.

That means the controller can work with typed DTOs:

- request DTOs describe what the API accepts
- response DTOs describe what the API returns
- generated JSON mappers handle the transport representation

### DTOs as API Contracts { #dtos-api-contracts }

DTOs are not just convenience classes. They are the public shape of your API. A `UserRequest` says which fields a client must send, while `UserResponse` says which fields the service returns. Keeping
that boundary explicit makes later guides easier: validation can attach rules to DTOs, HTTP routes can reuse them, and tests can assert stable response shapes.

### Type-Safe Results { #type-safe-results }

This guide also introduces a sealed result model. A sealed result is useful when one operation can produce several known outcomes, such as success or an error state. Instead of returning loose maps or
throwing exceptions for every branch, the code can express those outcomes as a closed set of types.

The important idea is that JSON mapping should support your application model, not replace it. Application code works with typed request, response, and result objects; Kora handles the JSON boundary.

The practical flow is:

1. add the JSON module and annotation processor support
2. create request and response DTOs
3. annotate controller inputs and outputs with `@Json`
4. let Kora generate JSON mappers at compile time
5. use a sealed result model to keep success and error outcomes typed

## Dependencies { #dependencies }

===! ":fontawesome-brands-java: `Java`"

    Add to `build.gradle`:

    ```groovy
    dependencies {
        // ... existing dependencies ...

        implementation("ru.tinkoff.kora:json-module")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Add to `build.gradle.kts`:

    ```kotlin
    dependencies {
        // ... existing dependencies ...

        implementation("ru.tinkoff.kora:json-module")
    }
    ```

## Modules { #modules }

Update your application graph to include JSON support.

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/java/ru/tinkoff/kora/guide/json/Application.java`:

    ```java
    package ru.tinkoff.kora.guide.json;

    import ru.tinkoff.kora.application.graph.KoraApplication;
    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.config.hocon.HoconConfigModule;
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule;
    import ru.tinkoff.kora.json.module.JsonModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,  // <----- Connected module
            LogbackModule,
            UndertowHttpServerModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update `src/main/kotlin/ru/tinkoff/kora/guide/json/Application.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.json

    import ru.tinkoff.kora.application.graph.KoraApplication
    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.config.hocon.HoconConfigModule
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule
    import ru.tinkoff.kora.json.module.JsonModule
    import ru.tinkoff.kora.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,  // <----- Connected module
        LogbackModule,
        UndertowHttpServerModule

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

## DTO { #dto }

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/guide/json/dto/UserRequest.java`:

    ```java
    package ru.tinkoff.kora.guide.json.dto;

    import ru.tinkoff.kora.json.common.annotation.Json;

    @Json
    public record UserRequest(String name, String email) {}
    ```

    Create `src/main/java/ru/tinkoff/kora/guide/json/dto/UserResponse.java`:

    ```java
    package ru.tinkoff.kora.guide.json.dto;

    import java.time.LocalDateTime;
    import ru.tinkoff.kora.json.common.annotation.Json;

    @Json
    public record UserResponse(String id, String name, String email, LocalDateTime createdAt) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/guide/json/dto/UserRequest.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.json.dto

    import ru.tinkoff.kora.json.common.annotation.Json

    @Json
    data class UserRequest(
        val name: String,
        val email: String
    )
    ```

    Create `src/main/kotlin/ru/tinkoff/kora/guide/json/dto/UserResponse.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.json.dto

    import java.time.LocalDateTime
    import ru.tinkoff.kora.json.common.annotation.Json

    @Json
    data class UserResponse(
        val id: String,
        val name: String,
        val email: String,
        val createdAt: LocalDateTime
    )
    ```

Annotating the DTO classes themselves is intentional. It tells Kora to generate the JSON reader and writer for the DTO during normal annotation processing, which avoids late-phase mapper generation
warnings when the same type is later used through an HTTP body, cache value, Kafka payload, or another JSON boundary.

After compilation, Kora generates JSON readers and writers for these DTOs:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-json-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/json/dto/$UserRequest_JsonReader.java
    guides/guide-json-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/json/dto/$UserResponse_JsonWriter.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-json-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/json/dto/$UserRequest_JsonReader.kt
    guides/kotlin/guide-kotlin-json-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/json/dto/$UserResponse_JsonWriter.kt
    ```

The generated request reader checks JSON tokens and required fields before constructing the record:

===! ":fontawesome-brands-java: `Java`"

    ```java
    private static String read_name(JsonParser __parser, int[] __receivedFields) throws IOException {
        var __token = __parser.nextToken();
        __receivedFields[0] = __receivedFields[0] | (1 << 0);
        if (__token == JsonToken.VALUE_STRING) {
            return __parser.getText();
        } else {
            throw new JsonParseException(__parser, "Expecting [VALUE_STRING] token for field 'name', got " + __token);
        }
    }

    return new UserRequest(name, email);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    private fun read_name(__parser: JsonParser, __receivedFields: IntArray): String {
      val __token = __parser.nextToken()
      __receivedFields[0] = __receivedFields[0] or (1 shl 0)
      if (__token == JsonToken.VALUE_STRING) {
        return __parser.text
      }
      throw JsonParseException(__parser, "Expecting [VALUE_STRING] token for field 'name', got " + __token)
    }

    return UserRequest(name!!, email!!)
    ```

The generated response writer writes exactly the DTO fields that form the HTTP response contract:

===! ":fontawesome-brands-java: `Java`"

    ```java
    _gen.writeStartObject(_object);
    if (_object.id() != null) {
        _gen.writeFieldName(_id_optimized_field_name);
        _gen.writeString(_object.id());
    }
    if (_object.createdAt() != null) {
        _gen.writeFieldName(_createdAt_optimized_field_name);
        createdAtWriter.write(_gen, _object.createdAt());
    }
    _gen.writeEndObject();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    _gen.writeStartObject(_object)
    _object.id.let {
      _gen.writeFieldName(_id_optimized_field_name)
      _gen.writeString(it)
    }
    _object.createdAt.let {
      _gen.writeFieldName(_createdAt_optimized_field_name)
      createdAtWriter.write(_gen, it)
    }
    _gen.writeEndObject()
    ```

This is the first place where `@Json` becomes concrete: request DTOs get generated readers, response DTOs get generated writers, and unsupported shapes fail at compile time instead of being discovered
through runtime reflection.

## Service { #service }

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/guide/json/service/UserService.java`:

    ```java
    package ru.tinkoff.kora.guide.json.service;

    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.json.dto.UserRequest;
    import ru.tinkoff.kora.guide.json.dto.UserResponse;
    import ru.tinkoff.kora.guide.json.dto.UserResult;

    import java.time.LocalDateTime;
    import java.util.List;
    import java.util.Map;
    import java.util.concurrent.ConcurrentHashMap;
    import java.util.concurrent.atomic.AtomicLong;

    @Component
    public final class UserService {

        private final Map<String, UserResponse> users = new ConcurrentHashMap<>();
        private final AtomicLong idGenerator = new AtomicLong(1);

        public UserResponse createUser(UserRequest request) {
            String id = String.valueOf(idGenerator.getAndIncrement());
            UserResponse user = new UserResponse(id, request.name(), request.email(), LocalDateTime.now());
            users.put(id, user);
            return user;
        }

        public List<UserResponse> getAllUsers() {
            return users.values().stream().toList();
        }

        public UserResult getUser(String id) {
            UserResponse user = users.get(id);
            if (user != null) {
                return new UserResult.UserSuccess(UserResult.Status.OK, user);
            }
            return new UserResult.UserError(UserResult.Status.ERROR, "User not found with id: " + id);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/guide/json/service/UserService.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.json.service

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.json.dto.UserRequest
    import ru.tinkoff.kora.guide.json.dto.UserResponse
    import ru.tinkoff.kora.guide.json.dto.UserResult
    import java.time.LocalDateTime
    import java.util.concurrent.ConcurrentHashMap
    import java.util.concurrent.atomic.AtomicLong

    @Component
    class UserService {

        private val users = ConcurrentHashMap<String, UserResponse>()
        private val idGenerator = AtomicLong(1)

        fun createUser(request: UserRequest): UserResponse {
            val id = idGenerator.getAndIncrement().toString()
            val user = UserResponse(
                id = id,
                name = request.name,
                email = request.email,
                createdAt = LocalDateTime.now()
            )
            users[id] = user
            return user
        }

        fun getAllUsers(): List<UserResponse> = users.values.toList()

        fun getUser(id: String): UserResult {
            val user = users[id]
            return if (user != null) {
                UserResult.UserSuccess(UserResult.Status.OK, user)
            } else {
                UserResult.UserError(UserResult.Status.ERROR, "User not found with id: $id")
            }
        }
    }
    ```

## Sealed Response Model { #sealed-response-model }

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/guide/json/dto/UserResult.java`:

    ```java
    package ru.tinkoff.kora.guide.json.dto;

    import ru.tinkoff.kora.json.common.annotation.Json;
    import ru.tinkoff.kora.json.common.annotation.JsonDiscriminatorField;
    import ru.tinkoff.kora.json.common.annotation.JsonDiscriminatorValue;

    @Json
    @JsonDiscriminatorField("status")
    public sealed interface UserResult permits UserResult.UserSuccess, UserResult.UserError {

        @Json
        enum Status {
            OK,
            ERROR
        }

        Status status();

        @Json
        @JsonDiscriminatorValue("OK")
        record UserSuccess(Status status, UserResponse user) implements UserResult {}

        @Json
        @JsonDiscriminatorValue("ERROR")
        record UserError(Status status, String message) implements UserResult {}
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/guide/json/dto/UserResult.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.json.dto

    import ru.tinkoff.kora.json.common.annotation.Json
    import ru.tinkoff.kora.json.common.annotation.JsonDiscriminatorField
    import ru.tinkoff.kora.json.common.annotation.JsonDiscriminatorValue

    @Json
    @JsonDiscriminatorField("status")
    sealed interface UserResult {

        @Json
        enum class Status {
            OK,
            ERROR
        }

        val status: Status

        @Json
        @JsonDiscriminatorValue("OK")
        data class UserSuccess(
            override val status: Status,
            val user: UserResponse
        ) : UserResult

        @Json
        @JsonDiscriminatorValue("ERROR")
        data class UserError(
            override val status: Status,
            val message: String
        ) : UserResult
    }
    ```

After compilation, the generated sealed reader and writer show how Kora uses the discriminator field:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-json-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/json/dto/$UserResult_JsonReader.java
    guides/guide-json-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/json/dto/$UserResult_JsonWriter.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-json-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/json/dto/$UserResult_JsonReader.kt
    guides/kotlin/guide-kotlin-json-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/json/dto/$UserResult_JsonWriter.kt
    ```

The writer chooses the concrete subtype by Java type:

===! ":fontawesome-brands-java: `Java`"

    ```java
    if (_object == null) {
        _gen.writeNull();
    } else if (_object instanceof UserResult.UserSuccess _o) {
        userSuccessWriter.write(_gen, _o);
    } else if (_object instanceof UserResult.UserError _o) {
        userErrorWriter.write(_gen, _o);
    } else {
        throw new IllegalStateException("Unsupported class");
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    when (_object) {
      null -> _gen.writeNull()
      is UserResult.UserError -> userErrorWriter.write(_gen, _object)
      is UserResult.UserSuccess -> userSuccessWriter.write(_gen, _object)
    }
    ```

The reader performs the opposite operation by reading the `status` discriminator:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var discriminator = DiscriminatorHelper.readStringDiscriminator(bufferingParser, "status");
    if (discriminator == null) {
        throw new JsonParseException(__parser, "Discriminator required, but not provided");
    }
    return switch(discriminator) {
        case "OK" -> userSuccessReader.read(bufferedParser);
        case "ERROR" -> userErrorReader.read(bufferedParser);
        default -> throw new JsonParseException(__parser, "Unknown discriminator: '" + discriminator + "'");
    };
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val discriminator = DiscriminatorHelper.readStringDiscriminator(bufferingParser, "status")
    if (discriminator == null) throw JsonParseException(__parser, "Discriminator required, but not provided")
    return when(discriminator) {
      "ERROR" -> userErrorReader.read(bufferedParser)
      "OK" -> userSuccessReader.read(bufferedParser)
      else -> throw JsonParseException(__parser, "Unknown discriminator")
    }
    ```

This generated code explains polymorphic JSON without guessing: `@JsonDiscriminatorField("status")` becomes an actual discriminator lookup, and each subtype has its own generated reader and writer.

## Controller { #controller }

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/guide/json/controller/UserController.java`:

    ```java
    package ru.tinkoff.kora.guide.json.controller;

    import java.util.List;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.guide.json.dto.UserRequest;
    import ru.tinkoff.kora.guide.json.dto.UserResponse;
    import ru.tinkoff.kora.guide.json.dto.UserResult;
    import ru.tinkoff.kora.guide.json.service.UserService;
    import ru.tinkoff.kora.http.common.HttpMethod;
    import ru.tinkoff.kora.http.common.annotation.HttpRoute;
    import ru.tinkoff.kora.http.common.annotation.Path;
    import ru.tinkoff.kora.http.server.common.annotation.HttpController;
    import ru.tinkoff.kora.json.common.annotation.Json;

    @Component
    @HttpController
    public final class UserController {

        private final UserService userService;

        public UserController(UserService userService) {
            this.userService = userService;
        }

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        public UserResponse createUser(@Json UserRequest request) {
            return userService.createUser(request);
        }

        @HttpRoute(method = HttpMethod.GET, path = "/users")
        @Json
        public List<UserResponse> getAllUsers() {
            return userService.getAllUsers();
        }

        @HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
        @Json
        public UserResult getUser(@Path String id) {
            return userService.getUser(id);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/guide/json/controller/UserController.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.json.controller

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.guide.json.dto.UserRequest
    import ru.tinkoff.kora.guide.json.dto.UserResponse
    import ru.tinkoff.kora.guide.json.dto.UserResult
    import ru.tinkoff.kora.guide.json.service.UserService
    import ru.tinkoff.kora.http.common.HttpMethod
    import ru.tinkoff.kora.http.common.annotation.HttpRoute
    import ru.tinkoff.kora.http.common.annotation.Path
    import ru.tinkoff.kora.http.server.common.annotation.HttpController
    import ru.tinkoff.kora.json.common.annotation.Json

    @Component
    @HttpController
    class UserController(
        private val userService: UserService
    ) {

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        fun createUser(@Json request: UserRequest): UserResponse {
            return userService.createUser(request)
        }

        @HttpRoute(method = HttpMethod.GET, path = "/users")
        @Json
        fun getAllUsers(): List<UserResponse> {
            return userService.getAllUsers()
        }

        @HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
        @Json
        fun getUser(@Path id: String): UserResult {
            return userService.getUser(id)
        }
    }
    ```

## Generated JSON Code { #json-code }

`@Json` is compile-time code generation, not runtime reflection.

After you run:

```bash
./gradlew clean classes
```

inspect the generated JSON readers and writers:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-json-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/json/dto/$UserRequest_JsonReader.java
    guides/guide-json-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/json/dto/$UserResponse_JsonWriter.java
    guides/guide-json-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/json/dto/$UserResult_JsonReader.java
    guides/guide-json-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/json/dto/$UserResult_JsonWriter.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-json-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/json/dto/$UserRequest_JsonReader.kt
    guides/kotlin/guide-kotlin-json-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/json/dto/$UserResponse_JsonWriter.kt
    guides/kotlin/guide-kotlin-json-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/json/dto/$UserResult_JsonReader.kt
    guides/kotlin/guide-kotlin-json-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/json/dto/$UserResult_JsonWriter.kt
    ```

The DTO and sealed-response chapters showed the generated fragments next to the model that produced them. Generated JSON classes are also excellent context for AI assistants: they show the exact field
names, discriminator values, null handling, and subtype mapping Kora compiled from your DTOs.

## Run Application { #run-app }

First verify compilation and tests:

```bash
./gradlew clean classes
./gradlew test
```

Then run the app:

```bash
./gradlew run
```

## Check Application { #check-app }

Create user:

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com"}'
```

Get all users:

```bash
curl http://localhost:8080/users
```

Get user by id (success):

```bash
curl http://localhost:8080/users/1
```

Get user by id (not found):

```bash
curl http://localhost:8080/users/999
```

## Best Practices { #best-practices }

- Keep request/response DTOs simple and immutable.
- Use sealed responses when endpoint outcomes have different payload shapes.
- Keep business logic in service layer, not in controller methods.
- Use compile-time generated JSON mapping (`@Json`) instead of manual parsing.
- Put `@Json` on request/response DTO classes that are serialized or deserialized as JSON, not only on controller parameters and return values.
- Inspect generated readers and writers when JSON shape or polymorphic decoding is unclear.

## Summary { #summary }

You implemented JSON request/response handling in Kora with:

- DTO-based API contracts
- automatic JSON mapping
- polymorphic sealed JSON responses with discriminator field
- generated JSON readers and writers for DTO and sealed response contracts

## Key Concepts { #key-concepts }

- `json-module` enables JSON processing in Kora HTTP apps.
- `@Json` handles request deserialization and response serialization.
- Sealed types with `@JsonDiscriminatorField` and `@JsonDiscriminatorValue` provide type-safe polymorphic API responses.
- Generated JSON source shows the exact serialization and deserialization behavior.

## Troubleshooting { #troubleshooting }

**Request body is not deserialized**

- Ensure `json-module` is added to dependencies.
- Ensure controller request parameter is annotated with `@Json`.

**Polymorphic response does not serialize as expected**

- Check `@JsonDiscriminatorField` on sealed type.
- Check every subtype has `@JsonDiscriminatorValue`.

**HTTP routes are not found**

- Verify `@HttpController` and `@HttpRoute` annotations.
- Verify path patterns (`/users`, `/users/{id}`) and HTTP methods.

## What's Next? { #whats-next }

- [Build an HTTP Server](http-server.md) to use these JSON DTO patterns in a full CRUD API.
- [Validation](validation.md) after HTTP Server, because validation assumes the finished CRUD controller/service/repository flow.
- [Database JDBC](database-jdbc.md) or [Cassandra Database](database-cassandra.md) after HTTP Server, when you are ready to replace the in-memory repository.
- [OpenAPI HTTP Server](openapi-http-server.md) after HTTP Server, to compare handwritten JSON DTOs with contract-generated transport models.

## Help { #help }

If you encounter issues:

- compare with [Kora Java JSON App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-json-app) and [Kora Kotlin JSON App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-json-app)
- check the [JSON documentation](../documentation/json.md)
- check the [HTTP Server documentation](../documentation/http-server.md)
- check the [HTTP Server example](https://github.com/kora-projects/kora-examples/tree/master/kora-java-http-server)
