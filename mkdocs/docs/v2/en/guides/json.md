---
search:
  exclude: true
title: JSON Processing with Kora
summary: Learn how to handle JSON requests and responses in a Kora HTTP API with type-safe DTOs and sealed polymorphic responses
description: "Step-by-step JSON request and response mapping for a Kora 2.0 HTTP API: the io.koraframework:json-common artifact, JsonModule, @Json on DTOs and on controller parameters and return values, compile-time generated JsonReader and JsonWriter classes, sealed polymorphic responses with @JsonDiscriminatorField and @JsonDiscriminatorValue, the nullable JsonReader.read contract, JsonWriter.toByteArray and toString, and reading the generated JSON sources."
agent:
  use_when: "Use this file for questions about handling JSON in a Kora 2.0 HTTP API: io.koraframework:json-common, JsonModule, @Json on records and data classes, @Json on @HttpRoute parameters and return values, generated $Type_JsonReader and $Type_JsonWriter sources, sealed responses with @JsonDiscriminatorField and @JsonDiscriminatorValue, JsonReader.read returning null, JsonWriter.toByteArray / toString / toPrettyString, StreamReadException parse errors, and why @Json belongs on the DTO type itself."
tags: json, http, api, serialization
---

# Working with JSON in Kora { #working-json-kora }

This guide introduces JSON request and response mapping in Kora. It covers how `@Json` selects JSON mappers for HTTP bodies, how request and response DTOs become the typed boundary of an API, and how
Kora generates serialization code through annotation processing. You will also see how JSON mapping fits into the compile-time dependency graph that powers the application.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java JSON App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-json-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin JSON App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-json-app).

## What You'll Build { #youll-build }

You will build a JSON-first HTTP API with:

- JSON request parsing for `POST /users`
- JSON response serialization for `GET /users`
- Polymorphic JSON response for `GET /users/{id}` using sealed types
- Type-safe DTO contracts for request and response models

## What You'll Need { #youll-need }

- JDK 25 or later
- Gradle 9+
- A text editor or IDE
- Completed [Creating Your First Kora App](getting-started.md)

Kora 2.0 artifacts are compiled for Java 25, so the JDK that compiles the application must be 25 or newer.

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

Generation produces two contracts per type, `JsonReader<T>` and `JsonWriter<T>`, and both are ordinary untagged components in the dependency graph. Nothing is discovered
through reflection at runtime, and the streaming layer underneath is [Jackson](https://github.com/FasterXML/jackson) in its `tools.jackson.core` form.

That means the controller can work with typed DTOs:

- request DTOs describe what the API accepts
- response DTOs describe what the API returns
- generated JSON mappers handle the transport representation

### DTOs as API Contracts { #dtos-api-contracts }

DTOs are not just convenience classes. They are the public shape of your API. A `UserRequest` says which fields a client must send, while `UserResponse` says which fields the service returns. Keeping
that boundary explicit makes later guides easier: validation can attach rules to DTOs, HTTP routes can reuse them, and tests can assert stable response shapes.

By default every declared field is required. A field becomes optional when it is marked nullable — with the [JSpecify](https://jspecify.dev/) `@Nullable` annotation in Java, or with a nullable type in
Kotlin. A missing required field fails the read with a `StreamReadException` that names the field, which keeps a broken client request a `400` instead of a `null` deep inside application code.

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

    Add to the `dependencies` block in `build.gradle`:

    ```groovy
    dependencies {
        // ... existing dependencies ...

        implementation "io.koraframework:json-common"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Add to the `dependencies` block in `build.gradle.kts`:

    ```kotlin
    dependencies {
        // ... existing dependencies ...

        implementation("io.koraframework:json-common")
    }
    ```

The artifact version comes from the `io.koraframework:kora-bom` platform the application already imports, so no explicit version is needed here. `json-common` brings the `JsonReader` and `JsonWriter`
contracts plus the built-in codecs; the readers and writers for your own types are produced by the Kora annotation processor (`annotation-processors` for Java, `symbol-processors` for Kotlin) that the
getting started guide already wired in.

## Modules { #modules }

Update your application graph to include JSON support.

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/java/io/koraframework/guide/json/Application.java`:

    ```java
    package io.koraframework.guide.json;

    import io.koraframework.application.graph.KoraApplication;
    import io.koraframework.common.annotation.KoraApp;
    import io.koraframework.config.hocon.HoconConfigModule;
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule;
    import io.koraframework.json.common.JsonModule;
    import io.koraframework.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,  // <----- Connected module
            LogbackModule,
            UndertowPublicHttpServerModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update `src/main/kotlin/io/koraframework/guide/json/Application.kt`:

    ```kotlin
    package io.koraframework.guide.json

    import io.koraframework.application.graph.KoraApplication
    import io.koraframework.common.annotation.KoraApp
    import io.koraframework.config.hocon.HoconConfigModule
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule
    import io.koraframework.json.common.JsonModule
    import io.koraframework.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,  // <----- Connected module
        LogbackModule,
        UndertowPublicHttpServerModule

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

`JsonModule` contributes the default codecs for standard types — numbers, strings, booleans, `UUID`, the `java.time` types, collections, and maps. Your own types get their codecs from the annotation
processor, and the two sets are combined by the graph.

## DTO { #dto }

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/io/koraframework/guide/json/dto/UserRequest.java`:

    ```java
    package io.koraframework.guide.json.dto;

    import io.koraframework.json.common.annotation.Json;

    @Json
    public record UserRequest(String name, String email) {}
    ```

    Create `src/main/java/io/koraframework/guide/json/dto/UserResponse.java`:

    ```java
    package io.koraframework.guide.json.dto;

    import java.time.LocalDateTime;
    import io.koraframework.json.common.annotation.Json;

    @Json
    public record UserResponse(String id, String name, String email, LocalDateTime createdAt) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/io/koraframework/guide/json/dto/UserRequest.kt`:

    ```kotlin
    package io.koraframework.guide.json.dto

    import io.koraframework.json.common.annotation.Json

    @Json
    data class UserRequest(
        val name: String,
        val email: String
    )
    ```

    Create `src/main/kotlin/io/koraframework/guide/json/dto/UserResponse.kt`:

    ```kotlin
    package io.koraframework.guide.json.dto

    import java.time.LocalDateTime
    import io.koraframework.json.common.annotation.Json

    @Json
    data class UserResponse(
        val id: String,
        val name: String,
        val email: String,
        val createdAt: LocalDateTime
    )
    ```

Annotating the DTO classes themselves is intentional. It tells Kora to generate the JSON reader and writer for the DTO during normal annotation processing, which avoids late-phase mapper generation
when the same type is later used through an HTTP body, cache value, Kafka payload, or another JSON boundary.

After compilation, Kora generates JSON readers and writers for these DTOs:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/java/kora-java-guide-json-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/json/dto/$UserRequest_JsonReader.java
    guides/java/kora-java-guide-json-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/json/dto/$UserResponse_JsonWriter.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/kora-kotlin-guide-json-app/build/generated/ksp/main/kotlin/io/koraframework/guide/json/dto/$UserRequest_JsonReader.kt
    guides/kotlin/kora-kotlin-guide-json-app/build/generated/ksp/main/kotlin/io/koraframework/guide/json/dto/$UserResponse_JsonWriter.kt
    ```

The generated request reader checks JSON tokens and required fields before constructing the record:

===! ":fontawesome-brands-java: `Java`"

    ```java
    private static String read_name(JsonParser __parser, int[] __receivedFields) {
      var __token = __parser.nextToken();
      __receivedFields[0] = __receivedFields[0] | (1 << 0);
      if (__token == JsonToken.VALUE_STRING) {
        return __parser.getText();
      } else {
        throw new StreamReadException(__parser, "Expecting [VALUE_STRING] token for field 'name', got " + __token);
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
      throw StreamReadException(__parser, "Expecting [VALUE_STRING] token for field 'name', got " + __token)
    }

    return UserRequest(
      name!!,
      email!!,
    )
    ```

Both fields of `UserRequest` are required, so the reader keeps a received-fields bitmask and reports every missing field at once:

```text
Some of required json fields were not received: name(name) email(email)
```

The generated response writer writes exactly the DTO fields that form the HTTP response contract:

===! ":fontawesome-brands-java: `Java`"

    ```java
    _gen.writeStartObject(_object);
    if (_object.id() != null) {
      _gen.writeName(_id_optimized_field_name);
      _gen.writeString(_object.id());
    }
    if (_object.createdAt() != null) {
      _gen.writeName(_createdAt_optimized_field_name);
      createdAtWriter.write(_gen, _object.createdAt());
    }
    _gen.writeEndObject();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    _gen.writeStartObject(_object)
    _object.id.let {
      _gen.writeName(_id_optimized_field_name)
      _gen.writeString(it)
    }
    _object.createdAt.let {
      _gen.writeName(_createdAt_optimized_field_name)
      createdAtWriter.write(_gen, it)
    }
    _gen.writeEndObject()
    ```

Notice that `createdAt` is not written inline: the generated writer takes a `JsonWriter<LocalDateTime>` as a constructor dependency and delegates to it. That delegate comes from `JsonModule`, which is
why the module has to be connected to the graph — and why swapping the representation of a value type is a matter of replacing one component rather than editing every DTO.

This is the first place where `@Json` becomes concrete: request DTOs get generated readers, response DTOs get generated writers, and unsupported shapes fail at compile time instead of being discovered
through runtime reflection.

## Service { #service }

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/io/koraframework/guide/json/service/UserService.java`:

    ```java
    package io.koraframework.guide.json.service;

    import java.time.LocalDateTime;
    import java.util.List;
    import java.util.Map;
    import java.util.concurrent.ConcurrentHashMap;
    import java.util.concurrent.atomic.AtomicLong;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.json.dto.UserRequest;
    import io.koraframework.guide.json.dto.UserResponse;
    import io.koraframework.guide.json.dto.UserResult;

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

    Create `src/main/kotlin/io/koraframework/guide/json/service/UserService.kt`:

    ```kotlin
    package io.koraframework.guide.json.service

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.json.dto.UserRequest
    import io.koraframework.guide.json.dto.UserResponse
    import io.koraframework.guide.json.dto.UserResult
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

The service deals only with typed objects. It never sees a `JsonParser`, a `JsonGenerator`, or a string of JSON, which is exactly the separation this guide is building.

## Sealed Response Model { #sealed-response-model }

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/io/koraframework/guide/json/dto/UserResult.java`:

    ```java
    package io.koraframework.guide.json.dto;

    import io.koraframework.json.common.annotation.Json;
    import io.koraframework.json.common.annotation.JsonDiscriminatorField;
    import io.koraframework.json.common.annotation.JsonDiscriminatorValue;

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

    Create `src/main/kotlin/io/koraframework/guide/json/dto/UserResult.kt`:

    ```kotlin
    package io.koraframework.guide.json.dto

    import io.koraframework.json.common.annotation.Json
    import io.koraframework.json.common.annotation.JsonDiscriminatorField
    import io.koraframework.json.common.annotation.JsonDiscriminatorValue

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

Here the discriminator is also a real field of every subtype, so it is written as a normal property and no synthetic key appears in the payload. That is a deliberate choice: a discriminator does not
have to exist in the model, but when it does, the same value drives both the JSON shape and the `when`/`switch` branches in application code.

After compilation, the generated sealed reader and writer show how Kora uses the discriminator field:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/java/kora-java-guide-json-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/json/dto/$UserResult_JsonReader.java
    guides/java/kora-java-guide-json-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/json/dto/$UserResult_JsonWriter.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/kora-kotlin-guide-json-app/build/generated/ksp/main/kotlin/io/koraframework/guide/json/dto/$UserResult_JsonReader.kt
    guides/kotlin/kora-kotlin-guide-json-app/build/generated/ksp/main/kotlin/io/koraframework/guide/json/dto/$UserResult_JsonWriter.kt
    ```

The writer chooses the concrete subtype by runtime type:

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
    var bufferingParser = new BufferingJsonParser(__parser);
    var discriminator = DiscriminatorHelper.readStringDiscriminator(bufferingParser, "status");
    if (discriminator == null) throw new StreamReadException(__parser, "Discriminator required, but not provided, expected one of: [OK, ERROR]");
    var bufferedParser = JsonParserSequence.createFlattened(false, bufferingParser.reset(), __parser);
    bufferedParser.nextToken();
    return switch(discriminator) {
      case "OK" -> userSuccessReader.read(bufferedParser);
      case "ERROR" -> userErrorReader.read(bufferedParser);
      default -> throw new StreamReadException(__parser, "Unknown discriminator: '" + discriminator + "'");
    };
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val bufferingParser = BufferingJsonParser(__parser)
    val discriminator = DiscriminatorHelper.readStringDiscriminator(bufferingParser, "status")
    if (discriminator == null) throw StreamReadException(__parser, "Discriminator required, but not provided, expected one of: [ERROR, OK]")
    val bufferedParser = JsonParserSequence.createFlattened(false, bufferingParser.reset(), __parser)
    bufferedParser.nextToken()
    return when(discriminator) {
      "ERROR" -> userErrorReader.read(bufferedParser)
      "OK" -> userSuccessReader.read(bufferedParser)
      else -> throw StreamReadException(__parser, "Unknown discriminator")
    }
    ```

The `BufferingJsonParser` in that code is what makes the discriminator position-independent: Kora buffers the tokens it consumed while looking for `status`, then replays them into the subtype reader.
A client may therefore send `status` last and the payload still decodes.

If a payload may legitimately omit the discriminator, give `@JsonDiscriminatorField` a fallback with its `defaultValue` attribute instead of letting the read fail.

This generated code explains polymorphic JSON without guessing: `@JsonDiscriminatorField("status")` becomes an actual discriminator lookup, and each subtype has its own generated reader and writer.

## Controller { #controller }

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/io/koraframework/guide/json/controller/UserController.java`:

    ```java
    package io.koraframework.guide.json.controller;

    import java.util.List;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.json.dto.UserRequest;
    import io.koraframework.guide.json.dto.UserResponse;
    import io.koraframework.guide.json.dto.UserResult;
    import io.koraframework.guide.json.service.UserService;
    import io.koraframework.http.common.HttpMethod;
    import io.koraframework.http.common.annotation.HttpRoute;
    import io.koraframework.http.common.annotation.Path;
    import io.koraframework.http.server.common.annotation.HttpController;
    import io.koraframework.json.common.annotation.Json;

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

    Create `src/main/kotlin/io/koraframework/guide/json/controller/UserController.kt`:

    ```kotlin
    package io.koraframework.guide.json.controller

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.json.dto.UserRequest
    import io.koraframework.guide.json.dto.UserResponse
    import io.koraframework.guide.json.dto.UserResult
    import io.koraframework.guide.json.service.UserService
    import io.koraframework.http.common.HttpMethod
    import io.koraframework.http.common.annotation.HttpRoute
    import io.koraframework.http.common.annotation.Path
    import io.koraframework.http.server.common.annotation.HttpController
    import io.koraframework.json.common.annotation.Json

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

`@Json` appears in two different roles here. On a parameter it selects the JSON request body mapper; on the method it selects the JSON response body mapper. `getAllUsers` returns `List<UserResponse>`
and needs no extra declaration, because `JsonModule` provides a `JsonWriter<List<T>>` that composes with the generated `JsonWriter<UserResponse>`.

## Generated JSON Code { #json-code }

`@Json` is compile-time code generation, not runtime reflection.

After you run:

```bash
./gradlew clean classes
```

inspect the generated JSON readers and writers:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/java/kora-java-guide-json-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/json/dto/$UserRequest_JsonReader.java
    guides/java/kora-java-guide-json-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/json/dto/$UserResponse_JsonWriter.java
    guides/java/kora-java-guide-json-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/json/dto/$UserResult_JsonReader.java
    guides/java/kora-java-guide-json-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/json/dto/$UserResult_JsonWriter.java
    guides/java/kora-java-guide-json-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/json/dto/$UserResult_UserSuccess_JsonWriter.java
    guides/java/kora-java-guide-json-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/json/dto/$UserResult_Status_JsonWriter.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/kora-kotlin-guide-json-app/build/generated/ksp/main/kotlin/io/koraframework/guide/json/dto/$UserRequest_JsonReader.kt
    guides/kotlin/kora-kotlin-guide-json-app/build/generated/ksp/main/kotlin/io/koraframework/guide/json/dto/$UserResponse_JsonWriter.kt
    guides/kotlin/kora-kotlin-guide-json-app/build/generated/ksp/main/kotlin/io/koraframework/guide/json/dto/$UserResult_JsonReader.kt
    guides/kotlin/kora-kotlin-guide-json-app/build/generated/ksp/main/kotlin/io/koraframework/guide/json/dto/$UserResult_JsonWriter.kt
    guides/kotlin/kora-kotlin-guide-json-app/build/generated/ksp/main/kotlin/io/koraframework/guide/json/dto/$UserResult_UserSuccess_JsonWriter.kt
    guides/kotlin/kora-kotlin-guide-json-app/build/generated/ksp/main/kotlin/io/koraframework/guide/json/dto/$UserResult_Status_JsonWriter.kt
    ```

Note that a reader and a writer are generated for every `@Json` type in the hierarchy, including the nested `Status` enum and each sealed subtype. The controller only asks for `JsonWriter<UserResult>`,
and the graph assembles the rest.

The DTO and sealed-response chapters showed the generated fragments next to the model that produced them. Generated JSON classes are also excellent context for AI assistants: they show the exact field
names, discriminator values, null handling, and subtype mapping Kora compiled from your DTOs.

## Reading and Writing JSON Directly { #read-write-directly }

The HTTP layer uses the generated codecs for you, but the same components can be injected anywhere — a Kafka consumer, a migration job, or a test. Ask for `JsonReader<T>` or `JsonWriter<T>` by type
and use them directly.

===! ":fontawesome-brands-java: `Java`"

    ```java
    package io.koraframework.guide.json.service;

    import io.koraframework.common.annotation.Component;
    import io.koraframework.guide.json.dto.UserRequest;
    import io.koraframework.json.common.JsonReader;
    import io.koraframework.json.common.JsonWriter;

    @Component
    public final class UserCodec {

        private final JsonReader<UserRequest> reader;
        private final JsonWriter<UserRequest> writer;

        public UserCodec(JsonReader<UserRequest> reader, JsonWriter<UserRequest> writer) {
            this.reader = reader;
            this.writer = writer;
        }

        public byte[] encode(UserRequest request) {
            return this.writer.toByteArray(request); //(1)!
        }

        public UserRequest decode(byte[] payload) {
            UserRequest request = this.reader.read(payload); //(2)!
            if (request == null) {
                throw new IllegalArgumentException("Expected a user request, but got JSON null");
            }
            return request;
        }
    }
    ```

    1.  `toByteArray(...)`, `toString(...)`, and `toPrettyString(...)` do not declare a checked exception, so no `try`/`catch` is required. A malformed value fails with an unchecked `JacksonException`.
    2.  `read(...)` is annotated `@Nullable`: a literal JSON `null` document decodes to `null` rather than to an object.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package io.koraframework.guide.json.service

    import io.koraframework.common.annotation.Component
    import io.koraframework.guide.json.dto.UserRequest
    import io.koraframework.json.common.JsonReader
    import io.koraframework.json.common.JsonWriter

    @Component
    class UserCodec(
        private val reader: JsonReader<UserRequest>,
        private val writer: JsonWriter<UserRequest>
    ) {

        fun encode(request: UserRequest): ByteArray = writer.toByteArray(request) //(1)!

        fun decode(payload: ByteArray): UserRequest =
            requireNotNull(reader.read(payload)) { "Expected a user request, but got JSON null" } //(2)!
    }
    ```

    1.  `toByteArray(...)`, `toString(...)`, and `toPrettyString(...)` do not declare a checked exception, so no `try`/`catch` is required. A malformed value fails with an unchecked `JacksonException`.
    2.  `read(...)` returns `UserRequest?`, so Kotlin forces you to decide what a JSON `null` document means. `requireNotNull(...)` turns it into a clear error.

Both contracts also accept a `String`, an `InputStream`, and a `byte[]` slice, so the same component works for an in-memory payload and for a stream.

???+ warning "Attention"

    A parse failure is signalled with `StreamReadException`, which extends the unchecked `JacksonException`. Nothing forces you to handle it, so decide explicitly where a malformed payload should be
    caught. Inside an HTTP route Kora already does that for you and answers `400`.

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

The application listens on port `8080` by default, because nothing in `application.conf` overrides `httpServer.port`.

## Check Application { #check-app }

Create user:

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com"}'
```

```json
{"id":"1","name":"John Doe","email":"john@example.com","createdAt":"2026-01-15T10:30:00.123"}
```

Get all users:

```bash
curl http://localhost:8080/users
```

```json
[{"id":"1","name":"John Doe","email":"john@example.com","createdAt":"2026-01-15T10:30:00.123"}]
```

Get user by id (success):

```bash
curl http://localhost:8080/users/1
```

```json
{"status":"OK","user":{"id":"1","name":"John Doe","email":"john@example.com","createdAt":"2026-01-15T10:30:00.123"}}
```

Get user by id (not found):

```bash
curl http://localhost:8080/users/999
```

```json
{"status":"ERROR","message":"User not found with id: 999"}
```

Both responses come from one route and one return type. The `status` field tells a client which branch of the sealed hierarchy it received.

Send a request that is missing a required field to see the generated validation:

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe"}'
```

The read fails before the controller method is entered, and the server answers `400`.

## Best Practices { #best-practices }

- Keep request/response DTOs simple and immutable.
- Use sealed responses when endpoint outcomes have different payload shapes.
- Keep business logic in service layer, not in controller methods.
- Use compile-time generated JSON mapping (`@Json`) instead of manual parsing.
- Put `@Json` on request/response DTO classes that are serialized or deserialized as JSON, not only on controller parameters and return values.
- Mark a field nullable only when the API really allows it to be absent; everything else stays required and fails fast.
- Inspect generated readers and writers when JSON shape or polymorphic decoding is unclear.

## Summary { #summary }

You implemented JSON request/response handling in Kora with:

- DTO-based API contracts
- automatic JSON mapping
- polymorphic sealed JSON responses with discriminator field
- generated JSON readers and writers for DTO and sealed response contracts

## Key Concepts { #key-concepts }

- `json-common` enables JSON processing in Kora HTTP apps, and `JsonModule` supplies the codecs for standard types.
- `@Json` handles request deserialization and response serialization, and registers the generated codecs in the graph as ordinary untagged components.
- Every declared field is required unless it is nullable; a missing required field fails the read with `StreamReadException`.
- Sealed types with `@JsonDiscriminatorField` and `@JsonDiscriminatorValue` provide type-safe polymorphic API responses.
- `JsonReader<T>.read(...)` may return `null`, while `JsonWriter<T>.toByteArray(...)` and `toString(...)` need no checked exception handling.
- Generated JSON source shows the exact serialization and deserialization behavior.

## Troubleshooting { #troubleshooting }

**Request body is not deserialized**

- Ensure `io.koraframework:json-common` is added to dependencies and `JsonModule` is connected to the `@KoraApp` interface.
- Ensure controller request parameter is annotated with `@Json`.

**Build fails with a missing `JsonReader` or `JsonWriter` component**

- Put `@Json` on the DTO type itself, not only on the controller signature.
- Check that the Kora processor is wired: `annotationProcessor "io.koraframework:annotation-processors"` for Java, `ksp("io.koraframework:symbol-processors")` for Kotlin.

**Request fails with `Some of required json fields were not received`**

- The listed fields are declared non-nullable. Either send them, or make them optional with `@Nullable` in Java or a nullable type in Kotlin.

**Polymorphic response does not serialize as expected**

- Check `@JsonDiscriminatorField` on sealed type.
- Check every subtype has `@JsonDiscriminatorValue`.
- For an incoming payload without a discriminator, set `@JsonDiscriminatorField(value = "status", defaultValue = "OK")`.

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

- compare with [Kora Java JSON App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-json-app) and [Kora Kotlin JSON App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-json-app)
- check the [JSON documentation](../documentation/json.md)
- check the [HTTP Server documentation](../documentation/http-server.md)
- check the [JSON example](https://github.com/kora-projects/kora-examples/tree/master/examples/java/kora-java-json)
