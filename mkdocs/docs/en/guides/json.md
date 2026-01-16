---
title: JSON Processing with Kora
summary: Learn how to handle JSON requests/responses in your Kora HTTP APIs
tags: json, http, api, serialization
---

# JSON Processing with Kora

This guide shows you how to handle JSON request and response data in your Kora HTTP APIs with automatic serialization and deserialization.

## What You'll Build

You'll build a simple HTTP API that handles JSON requests and responses:

- JSON request body parsing
- JSON response serialization
- Type-safe request/response objects
- Automatic content-type handling

## What You'll Need

- JDK 17 or later
- Gradle 7.0+
- A text editor or IDE
- Completed [Creating Your First Kora App](../getting-started.md) guide

## Prerequisites

!!! note "Required: Complete Basic Kora Setup"

    This guide assumes you have completed the **[Create Your First Kora App](../getting-started.md)** guide and have a working Kora project with basic setup.

    If you haven't completed the basic guide yet, please do so first as this guide builds upon that foundation.

## Add Dependencies

===! ":fontawesome-brands-java: `Java`"

    Add to the `dependencies` block in `build.gradle`:

    ```groovy
    dependencies {
        // ... existing dependencies ...

        implementation("ru.tinkoff.kora:json-module")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Add to the `dependencies` block in `build.gradle.kts`:

    ```kotlin
    dependencies {
        // ... existing dependencies ...

        implementation("ru.tinkoff.kora:json-module")
    }
    ```

## Add Modules

Update your existing `Application.java` or `Application.kt` to include the `JsonModule`:

===! ":fontawesome-brands-java: Java"

    Update `src/main/java/ru/tinkoff/kora/example/Application.java`:

    ```java
    package ru.tinkoff.kora.example;

    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule;
    import ru.tinkoff.kora.json.module.JsonModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
            UndertowHttpServerModule,
            JsonModule,
            LogbackModule {  // Add this line
    }
    ```

=== ":simple-kotlin: Kotlin"

    Update `src/main/kotlin/ru/tinkoff/kora/example/Application.kt`:

    ```kotlin
    package ru.tinkoff.kora.example

    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule
    import ru.tinkoff.kora.json.module.JsonModule
    import ru.tinkoff.kora.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        UndertowHttpServerModule,
        JsonModule,
        LogbackModule  // Add this line
    ```
## Creating Request/Response DTOs

**Data Transfer Objects (DTOs)** are simple objects that carry data between processes. In REST APIs, DTOs define the structure of request and response data, providing a clear contract between your API and its clients. They ensure type safety, make your API self-documenting, and handle JSON serialization automatically.

Create data transfer objects for your API:

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/example/dto/UserRequest.java`:

    ```java
    package ru.tinkoff.kora.example.dto;

    public record UserRequest(
        String name,
        String email
    ) {}
    ```

    Create `src/main/java/ru/tinkoff/kora/example/dto/UserResponse.java`:

    ```java
    package ru.tinkoff.kora.example.dto;

    import java.time.LocalDateTime;

    public record UserResponse(
        String id,
        String name,
        String email,
        LocalDateTime createdAt
    ) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/example/dto/UserRequest.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.dto

    data class UserRequest(
        val name: String,
        val email: String
    )
    ```

    Create `src/main/kotlin/ru/tinkoff/kora/example/dto/UserResponse.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.dto

    import java.time.LocalDateTime

    data class UserResponse(
        val id: String,
        val name: String,
        val email: String,
        val createdAt: LocalDateTime
    )
    ```

## Create User Service

Create a service layer to handle user operations:

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/example/service/UserService.java`:

    ```java
    package ru.tinkoff.kora.example.service;

    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.example.dto.UserRequest;
    import ru.tinkoff.kora.example.dto.UserResponse;

    import java.time.LocalDateTime;
    import java.util.*;
    import java.util.concurrent.ConcurrentHashMap;
    import java.util.concurrent.atomic.AtomicLong;

    @Component
    public final class UserService {

        private final Map<String, UserResponse> users = new ConcurrentHashMap<>();
        private final AtomicLong idGenerator = new AtomicLong(1);

        public UserResponse createUser(UserRequest request) {
            String id = String.valueOf(idGenerator.getAndIncrement());
            UserResponse user = new UserResponse(
                id,
                request.name(),
                request.email(),
                LocalDateTime.now()
            );
            users.put(id, user);
            return user;
        }

        public List<UserResponse> getAllUsers() {
            return new ArrayList<>(users.values());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/example/service/UserService.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.service

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.example.dto.UserRequest
    import ru.tinkoff.kora.example.dto.UserResponse
    import ru.tinkoff.kora.example.dto.UserResult
    import ru.tinkoff.kora.example.dto.UserSuccess
    import ru.tinkoff.kora.example.dto.UserError
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

        fun getAllUsers(): List<UserResponse> {
            return users.values.toList()
        }
    }
    ```

## Create User Controller

This section demonstrates how Kora handles JSON request and response processing automatically. The `@Json` annotation enables seamless JSON serialization and deserialization, while the JsonModule provides the underlying JSON processing capabilities.

### How JSON Processing Works in Kora

**Request Body Parsing with Compile-Time Code Generation**:
- When a method parameter is annotated with `@Json` and has a custom type (not a primitive), Kora generates a type-safe JSON reader at compile time
- This generated reader is injected into your controller through dependency injection
- At runtime, the injected reader parses the incoming JSON request body into your DTO objects
- Content-Type validation ensures the request contains valid JSON before parsing

**Response Body Serialization with Compile-Time Code Generation**:
- When a method is annotated with `@Json`, Kora generates a type-safe JSON writer at compile time
- This generated writer is injected into your controller through dependency injection
- At runtime, the injected writer serializes your return value to JSON format
- The response Content-Type is set to `application/json` and complex objects are handled seamlessly

**Type Safety Throughout**:
- Compile-time guarantees that your DTOs match the expected JSON structure
- Runtime validation ensures data integrity
- No manual JSON parsing or serialization code needed

### Key Annotations and Their Roles

**`@Json` on Method Parameters**:
- Enables JSON deserialization for request bodies
- Works with custom DTO classes (records/data classes)
- Automatically validates JSON structure against your type

**`@Json` on Methods**:
- Enables JSON serialization for response bodies
- Sets appropriate Content-Type headers
- Handles complex object graphs and collections

**`@HttpController` and `@HttpRoute`**:
- Define REST endpoints that can handle JSON
- Route HTTP requests to your handler methods
- Support standard HTTP methods (GET, POST, PUT, DELETE)

### JsonModule Integration

The JsonModule provides the foundational components for JSON processing:

**JsonReader<T> Components**:
- Basic and primitive JSON readers (String, Integer, Boolean, etc.) provided by JsonModule
- Used as building blocks by compile-time generated mappers for complex DTOs
- Handle fundamental JSON parsing operations for primitive types
- Include validation and error handling for malformed JSON

**JsonWriter<T> Components**:
- Basic and primitive JSON writers (String, Integer, Boolean, etc.) provided by JsonModule
- Used as building blocks by compile-time generated mappers for complex DTOs
- Handle fundamental JSON writing operations for primitive types
- Support complex object graphs, collections, and nested structures through generated mappers

**Content Negotiation & Error Handling**:
- Automatic handling of Accept/Content-Type headers
- Proper error responses for malformed JSON with detailed validation messages
- Integration with Kora's HTTP server for seamless request/response processing

Create a REST controller with JSON endpoints:

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/example/controller/UserController.java`:

    ```java
    package ru.tinkoff.kora.example.controller;

    import ru.tinkoff.kora.example.dto.UserRequest;
    import ru.tinkoff.kora.example.dto.UserResponse;
    import ru.tinkoff.kora.example.service.UserService;
    import ru.tinkoff.kora.http.common.annotation.HttpController;
    import ru.tinkoff.kora.http.common.annotation.HttpRoute;
    import ru.tinkoff.kora.http.common.annotation.Path;
    import ru.tinkoff.kora.json.common.annotation.Json;

    import java.util.Optional;

    @HttpController
    public final class UserController {

        private final UserService userService;

        public UserController(UserService userService) {
            this.userService = userService;
        }

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        public UserResponse createUser(UserRequest request) {
            return userService.createUser(request);
        }

        @HttpRoute(method = HttpMethod.GET, path = "/users")
        @Json
        public List<UserResponse> getAllUsers() {
            return userService.getAllUsers();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/example/controller/UserController.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.controller

    import ru.tinkoff.kora.example.dto.UserRequest
    import ru.tinkoff.kora.example.dto.UserResponse
    import ru.tinkoff.kora.example.service.UserService
    import ru.tinkoff.kora.http.common.annotation.HttpController
    import ru.tinkoff.kora.http.common.annotation.HttpRoute
    import ru.tinkoff.kora.http.common.annotation.Path
    import ru.tinkoff.kora.json.common.annotation.Json

    @HttpController
    class UserController(
        private val userService: UserService
    ) {

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        fun createUser(request: UserRequest): UserResponse {
            return userService.createUser(request)
        }

        @HttpRoute(method = HttpMethod.GET, path = "/users")
        @Json
        fun getAllUsers(): List<UserResponse> {
            return userService.getAllUsers()
        }
    }
    ```

## Creating Sealed Classes for Responses

Now that you have a basic API working, let's enhance it with type-safe discriminated unions using sealed classes. This pattern is useful when an endpoint can return different types of responses based on the outcome, providing better type safety and cleaner error handling.

### Why Use Sealed Classes for API Responses?

Sealed classes allow you to:
- **Type-safe responses**: The compiler ensures you handle all possible response types
- **Discriminated unions**: Different response structures based on a discriminator field
- **Clean error handling**: No more null checks or Optional unwrapping
- **Better API contracts**: Clear documentation of possible response variants

### How JSON Processing Works with Sealed Classes

Kora's JSON module provides sophisticated support for polymorphic JSON serialization and deserialization using sealed classes and discriminator fields:

**Automatic Type Resolution**: When deserializing JSON, Kora automatically reads the discriminator field (specified by `@JsonDiscriminatorField`) to determine which concrete class to instantiate. For example, if the JSON contains `"status": "OK"`, Kora will create a `UserSuccess` instance.

**Type-Safe Serialization**: During serialization, Kora automatically includes the discriminator field in the JSON output, ensuring that deserialization will correctly identify the response type.

**Compile-Time Safety**: The `sealed interface` ensures that only the permitted classes (`UserSuccess`, `UserError`) can implement `UserResult`, providing exhaustive pattern matching in your code.

**Discriminator Field Management**: The `@JsonDiscriminatorValue` annotation tells Kora which value to use for each concrete class, creating a clear mapping between JSON values and Java/Kotlin types.

### Understanding the Annotations

- **`@JsonDiscriminatorField("status")`**: Specifies which JSON field determines the response type
- **`@JsonDiscriminatorValue("OK")`**: Marks classes with their discriminator values
- **`sealed interface`**: Ensures only permitted classes can implement the interface

### Create Sealed Response Types

First, create the sealed interface and implementing classes:

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/example/dto/UserResult.java`:

    ```java
    package ru.tinkoff.kora.example.dto;

    import ru.tinkoff.kora.json.common.annotation.Json;
    import ru.tinkoff.kora.json.common.annotation.JsonDiscriminatorField;
    import ru.tinkoff.kora.json.common.annotation.JsonDiscriminatorValue;

    public enum Status {
        OK, ERROR
    }

    @Json
    @JsonDiscriminatorField("status")
    public sealed interface UserResult permits UserSuccess, UserError {
    }

    @JsonDiscriminatorValue("OK")
    public record UserSuccess(Status status, UserResponse user) implements UserResult {
    }

    @JsonDiscriminatorValue("ERROR")
    public record UserError(Status status, String message) implements UserResult {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/example/dto/UserResult.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.dto

    import ru.tinkoff.kora.json.common.annotation.Json
    import ru.tinkoff.kora.json.common.annotation.JsonDiscriminatorField
    import ru.tinkoff.kora.json.common.annotation.JsonDiscriminatorValue

    enum class Status {
        OK, ERROR
    }

    @Json
    @JsonDiscriminatorField("status")
    sealed interface UserResult

    @JsonDiscriminatorValue("OK")
    data class UserSuccess(val status: Status, val user: UserResponse) : UserResult

    @JsonDiscriminatorValue("ERROR")
    data class UserError(val status: Status, val message: String) : UserResult
    ```

### Add getUser Method to Service with Sealed Classes

Add a new `getUser` method to your UserService that returns UserResult:

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/java/ru/tinkoff/kora/example/service/UserService.java`:

    ```java
    // ... existing imports ...
    import ru.tinkoff.kora.example.dto.UserResult;
    import ru.tinkoff.kora.example.dto.UserSuccess;
    import ru.tinkoff.kora.example.dto.UserError;

    @Component
    public final class UserService {
        // ... existing fields and createUser method ...

        // NEW: Add getUser method with sealed classes
        public UserResult getUser(String id) {
            UserResponse user = users.get(id);
            if (user != null) {
                return new UserSuccess(Status.OK, user);
            } else {
                return new UserError(Status.ERROR, "User not found with id: " + id);
            }
        }

        // ... existing getAllUsers method ...
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update `src/main/kotlin/ru/tinkoff/kora/example/service/UserService.kt`:

    ```kotlin
    // ... existing imports ...
    import ru.tinkoff.kora.example.dto.UserResult
    import ru.tinkoff.kora.example.dto.UserSuccess
    import ru.tinkoff.kora.example.dto.UserError

    @Component
    class UserService {
        // ... existing fields and createUser method ...

        // NEW: Add getUser method with sealed classes
        fun getUser(id: String): UserResult {
            val user = users[id]
            return if (user != null) {
                UserSuccess(Status.OK, user)
            } else {
                UserError(Status.ERROR, "User not found with id: $id")
            }
        }

        // ... existing getAllUsers method ...
    }
    ```

### Add getUser Endpoint to Controller

Now let's add a new endpoint that demonstrates how Kora handles polymorphic JSON responses using our sealed classes.

### How JSON Processing Works in Controllers with Sealed Classes

When you return a sealed interface from a controller method, Kora's JSON module automatically handles the polymorphic serialization:

**Runtime Type Detection**: Kora inspects the actual runtime type of the returned object (`UserSuccess` or `UserError`) to determine which serialization strategy to use.

**Discriminator Field Injection**: The `@JsonDiscriminatorField("status")` annotation ensures that the appropriate discriminator value is included in the JSON output, allowing clients to distinguish between different response types.

**Type-Safe Deserialization**: When clients send requests that expect these responses, Kora can automatically deserialize the JSON back into the correct concrete type based on the discriminator field.

**No Manual Type Checking**: Unlike traditional approaches that might use enums or flags, sealed classes provide compile-time guarantees that all possible response types are handled.

Add a new `getUser` endpoint to your UserController:

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/java/ru/tinkoff/kora/example/controller/UserController.java`:

    ```java
    // ... existing imports ...
    import ru.tinkoff.kora.example.dto.UserResult;

    @HttpController
    public final class UserController {
        // ... existing constructor and createUser method ...

        // NEW: Add getUser endpoint with sealed classes
        @HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
        @Json
        public UserResult getUser(@Path("id") String id) {
            return userService.getUser(id);
        }

        // ... existing getAllUsers method ...
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update `src/main/kotlin/ru/tinkoff/kora/example/controller/UserController.kt`:

    ```kotlin
    // ... existing imports ...
    import ru.tinkoff.kora.example.dto.UserResult

    @HttpController
    class UserController(
        private val userService: UserService
    ) {
        // ... existing constructor and createUser method ...

        // NEW: Add getUser endpoint with sealed classes
        @HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
        @Json
        fun getUser(@Path("id") id: String): UserResult {
            return userService.getUser(id)
        }

        // ... existing getAllUsers method ...
    }
    ```

## Test the JSON API

Build and run your application:

```bash
./gradlew build
./gradlew run
```

Test creating a user with valid data:

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com"}'
```

You should see a response like:
```json
{
  "id": "1",
  "name": "John Doe",
  "email": "john@example.com",
  "createdAt": "2025-09-27T10:30:00"
}
```

Test getting all users:

```bash
curl http://localhost:8080/users
```

You should see a response like:
```json
[
  {
    "id": "1",
    "name": "John Doe",
    "email": "john@example.com",
    "createdAt": "2025-09-27T10:30:00"
  }
]
```

### Test the Enhanced API with Sealed Classes

Build and test your enhanced API with the new getUser endpoint:

```bash
./gradlew build
./gradlew run
```

Test the new getUser endpoint:

```bash
# Test successful user lookup
curl http://localhost:8080/users/1
```

You should see a response like:
```json
{
  "status": "OK",
  "user": {
    "id": "1",
    "name": "John Doe",
    "email": "john@example.com",
    "createdAt": "2025-09-27T10:30:00"
  }
}
```

```bash
# Test user not found
curl http://localhost:8080/users/999
```

You should see a response like:
```json
{
  "status": "ERROR",
  "message": "User not found with id: 999"
}
```

### Benefits of This Approach

**Type Safety**: The compiler ensures you handle both success and error cases when processing UserResult.

**No Null Checks**: Instead of checking for null or Optional, you use pattern matching or when expressions.

**Clear API Contracts**: The JSON schema clearly shows possible response variants.

**Better Error Handling**: Structured error responses instead of HTTP status codes alone.

**Client-Side Benefits**: API clients can generate type-safe code that handles all response variants.

## Key Concepts Learned

### JSON Processing in Kora

**Automatic Request Body Parsing**: When a controller method parameter is annotated with `@Json` or the method itself returns a type that needs JSON processing, Kora uses compile-time generated mappers that leverage JsonModule's basic readers to deserialize incoming JSON request bodies into your Java/Kotlin objects.

**Response Serialization**: Return objects from controller methods annotated with `@Json`, and Kora automatically serializes them to JSON responses. The framework handles content-type negotiation and proper HTTP headers.

**Type Safety Throughout**: Kora's JSON processing maintains full type safety - if your Java/Kotlin types don't match the JSON structure, you'll get clear compilation errors rather than runtime failures.

**JsonModule Integration**: The JsonModule provides basic JsonReader<T> and JsonWriter<T> components for primitive types and fundamental JSON operations, which are used by compile-time generated mappers for complex DTOs. These components are automatically configured through Kora's dependency injection system.

### JSON Processing
- **@Json annotation**: Triggers compile-time generation of type-safe JSON readers and writers
- **JsonModule**: Provides primitive and other basic JsonReader<T> and JsonWriter<T> to use them when building type generated mappers
- **Content-Type handling**: Automatic JSON content negotiation and proper HTTP headers
- **Type-safe mapping**: Compile-time generated mappers ensure JSON structure matches your types

### Type Safety
- **Record classes**: Immutable data structures for DTOs with built-in validation
- **Type-safe APIs**: Compile-time guarantees for data structures and API contracts
- **Null safety**: Proper handling of optional vs required fields with clear type distinctions

### Sealed Classes & Discriminated Unions
- **@JsonDiscriminatorField**: Specifies the discriminator field for polymorphic JSON serialization
- **@JsonDiscriminatorValue**: Marks implementing classes with their discriminator values for automatic type resolution
- **Type-safe responses**: Compile-time guarantees that all possible response types are handled
- **Polymorphic deserialization**: Automatic type detection based on discriminator fields in JSON
- **Clean error handling**: Structured error responses without null checks or Optional unwrapping

## What's Next?

- [Add Database Integration](../database-jdbc.md)
- [Add Validation](../validation.md)
- [Add Caching](../cache.md)
- [Add Observability & Monitoring](../observability.md)
- [Explore More Examples](../examples/kora-examples.md)

## Help

If you encounter issues:

- Check the [JSON Module Documentation](../../documentation/json.md)
- Check the [HTTP Server Documentation](../../documentation/http-server.md)
- Check the [HTTP Server Example](https://github.com/kora-projects/kora-examples/tree/master/kora-java-http-server)
- Ask questions on [GitHub Discussions](https://github.com/kora-projects/kora/discussions)