---
title: HTTP Client Integration with Kora - Testing HTTP Server
summary: Master HTTP client development by creating comprehensive tests for the HTTP Server guide endpoints
tags: http-client, rest, api-client, declarative-client, testing, integration
---

# HTTP Client Integration with Kora - Testing HTTP Server

This guide shows you how to create comprehensive HTTP clients in Kora that test all the advanced features from the **[HTTP Server](../http-server.md)** guide. You'll learn to consume REST APIs declaratively with compile-time safety while testing multi-port architecture, advanced routing, request body handling, and custom responses.

## What You'll Build

You'll create comprehensive HTTP clients that test all features from the HTTP Server guide:

- **User CRUD Operations**: Test GET, POST, PUT, DELETE endpoints with proper HTTP status codes
- **Advanced Routing**: Path parameters (`/users/{userId}`), query parameters (pagination, sorting)
- **Request Body Handling**: JSON, Form URL-encoded, Multipart file uploads, raw text bodies
- **Custom Responses**: Handle `HttpResponseEntity` with custom headers and status codes
- **Error Handling**: Proper exception mapping for 404s and other HTTP errors
- **Headers & Cookies**: Send custom headers and handle response metadata

## What You'll Need

- JDK 17 or later
- Gradle 7.0+
- A text editor or IDE
- Completed [Creating Your First Kora App](../getting-started.md) guide
- Completed [JSON Processing with Kora](../json.md) guide
- Completed [HTTP Server](../http-server.md) guide (running on port 8080)

## Prerequisites

!!! note "Required: Complete Basic Kora Setup and HTTP Server"

    This guide assumes you have completed the **[Create Your First Kora App](../getting-started.md)** guide and have a working Kora project with basic setup.

    **Critical**: You must also have completed the **[HTTP Server](../http-server.md)** guide and have it running. This HTTP client guide is designed to test all the endpoints from that server guide.

    **Important**: Create a **new application** for this HTTP client guide. Do not modify your existing HTTP Server application. Start fresh with the basic getting-started application and add HTTP client functionality to it.

    If you haven't completed the basic guide yet, please do so first as this guide builds upon that foundation.

    For testing the HTTP clients in this guide, you should have the **[HTTP Server](../http-server.md)** guide running in another terminal on port 8080 (public API).

## Add Dependencies

Add the HTTP client dependencies to your project:

===! ":fontawesome-brands-java: `Java`"

    ```gradle title="build.gradle"
    dependencies {
        // ... existing dependencies ...

        implementation("ru.tinkoff.kora:http-client-common")
        implementation("ru.tinkoff.kora:http-client-jdk")  // or http-client-okhttp
        implementation("ru.tinkoff.kora:json-module")
    }
    ```

===! ":fontawesome-brands-kotlin: `Kotlin`"

    ```kotlin title="build.gradle.kts"
    dependencies {
        // ... existing dependencies ...

        implementation("ru.tinkoff.kora:http-client-common")
        implementation("ru.tinkoff.kora:http-client-jdk")  // or http-client-okhttp
        implementation("ru.tinkoff.kora:json-module")
    }
    ```

## Add Modules

Update your Application interface to include HTTP client modules:

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/ru/tinkoff/kora/example/Application.java`:

    ```java
    package ru.tinkoff.kora.example;

    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.http.client.common.HttpClientModule;
    import ru.tinkoff.kora.http.client.jdk.JdkHttpClientModule;
    import ru.tinkoff.kora.json.module.JsonModule;

    @KoraApp
    public interface Application extends
            JdkHttpClientModule,
            HttpClientModule,
            JsonModule {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/ru/tinkoff/kora/example/Application.kt`:

    ```kotlin
    package ru.tinkoff.kora.example

    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.http.client.common.HttpClientModule
    import ru.tinkoff.kora.http.client.jdk.JdkHttpClientModule
    import ru.tinkoff.kora.json.module.JsonModule

    @KoraApp
    interface Application :
        JdkHttpClientModule,
        HttpClientModule,
        JsonModule
    ```

## Create Request/Response DTOs

Create data transfer objects that match the server API:

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

## Create HTTP Client Interface

This section demonstrates Kora's declarative HTTP client approach, which provides compile-time type safety and automatic code generation for REST API consumption. Unlike traditional HTTP clients that require manual request building and response parsing, Kora's declarative clients offer a contract-first approach where you define the API interface and let the framework handle the implementation details.

### Declarative HTTP Client Architecture

Kora's HTTP client system is built around several key concepts that work together to provide type-safe, efficient API communication:

**Interface-Driven Design**: You define HTTP client interfaces using annotations, and Kora generates the implementation at compile time. This approach ensures that API contracts are verified at compile time rather than runtime.

**Annotation-Based Configuration**: 
- `@HttpClient("name")`: Marks an interface as an HTTP client and associates it with configuration
- `@HttpRoute(method = HttpMethod.GET, path = "/endpoint")`: Defines the HTTP method and path pattern
- `@Json`: Enables automatic JSON serialization/deserialization for request/response bodies

**Path Parameter Binding**: URL path parameters like `{userId}` are automatically extracted from method parameters and substituted into the URL template. This provides type-safe URL construction without string concatenation.

**Automatic Content Negotiation**: The framework automatically sets appropriate `Content-Type` and `Accept` headers based on the request/response types and annotations used.

**Type-Safe Response Handling**: Return types are strongly typed, and the framework ensures that JSON responses are properly deserialized into your DTOs. HTTP status codes and headers are also accessible when needed.

### How HTTP Client Code Generation Works

When you annotate an interface with `@HttpClient`, Kora's annotation processor generates a concrete implementation class at compile time. This generated class:

1. **Implements the Interface**: Creates a class that implements your HTTP client interface
2. **Handles HTTP Communication**: Uses the configured HTTP client (JDK or OkHttp) to make actual HTTP requests
3. **Manages Serialization**: Automatically serializes method parameters to request bodies and deserializes responses
4. **Provides Error Handling**: Converts HTTP errors into appropriate exceptions or mapped response types

The generated implementation is injected through Kora's dependency injection system, so you can simply inject the interface and use it like any other service.

Create comprehensive HTTP client interfaces that mirror all the endpoints from the HTTP Server guide:

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/example/client/PublicApiClient.java` (for public API endpoints):

    ```java
    package ru.tinkoff.kora.example.client;

    import ru.tinkoff.kora.http.client.common.annotation.HttpClient;
    import ru.tinkoff.kora.http.client.common.annotation.HttpClientConfig;
    import ru.tinkoff.kora.http.client.common.annotation.HttpRoute;
    import ru.tinkoff.kora.http.client.common.annotation.ResponseCodeMapper;
    import ru.tinkoff.kora.http.common.HttpMethod;
    import ru.tinkoff.kora.http.common.HttpResponseEntity;
    import ru.tinkoff.kora.json.common.annotation.Json;
    import ru.tinkoff.kora.example.dto.UserRequest;
    import ru.tinkoff.kora.example.dto.UserResponse;
    import ru.tinkoff.kora.example.dto.UserResult;
    import ru.tinkoff.kora.example.dto.UpdateUserResult;

    import java.util.List;
    import java.util.Optional;

    @HttpClient("public-api")
    public interface PublicApiClient {

        // User CRUD operations mirroring server endpoints
        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        HttpResponseEntity<UserResponse> createUser(UserRequest request);

        @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}")
        @Json
        UserResult getUser(String userId);

        @HttpRoute(method = HttpMethod.GET, path = "/users")
        @Json
        List<UserResponse> getUsers();

        @HttpRoute(method = HttpMethod.DELETE, path = "/users/{userId}")
        HttpResponseEntity<Void> deleteUser(String userId);

        // Advanced routing - multiple path parameters
        @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}/posts/{postId}")
        @Json
        Post getUserPost(String userId, String postId);

        // DTOs for advanced routing
        @Json
        record Post(String id, String content) {}
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/example/client/PublicApiClient.kt` (for public API endpoints):

    ```kotlin
    package ru.tinkoff.kora.example.client

    import ru.tinkoff.kora.http.client.common.annotation.HttpClient
    import ru.tinkoff.kora.http.client.common.annotation.HttpRoute
    import ru.tinkoff.kora.http.client.common.annotation.ResponseCodeMapper
    import ru.tinkoff.kora.http.common.HttpMethod
    import ru.tinkoff.kora.http.common.HttpResponseEntity
    import ru.tinkoff.kora.json.common.annotation.Json
    import ru.tinkoff.kora.example.dto.UserRequest
    import ru.tinkoff.kora.example.dto.UserResponse
    import ru.tinkoff.kora.example.dto.UserResult
    import ru.tinkoff.kora.example.dto.UpdateUserResult
    import ru.tinkoff.kora.http.common.form.FormMultipart
    import ru.tinkoff.kora.http.common.form.FormUrlEncoded

    @HttpClient("public-api")
    interface PublicApiClient {

        // User CRUD operations mirroring server endpoints
        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        fun createUser(request: UserRequest): HttpResponseEntity<UserResponse>

        @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}")
        @Json
        fun getUser(userId: String): UserResult

        @HttpRoute(method = HttpMethod.GET, path = "/users")
        @Json
        fun getUsers(): List<UserResponse>

        @HttpRoute(method = HttpMethod.DELETE, path = "/users/{userId}")
        fun deleteUser(userId: String): HttpResponseEntity<Void>

        // Advanced routing - multiple path parameters
        @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}/posts/{postId}")
        @Json
        fun getUserPost(userId: String, postId: String): Post
    }
    ```

## Configure HTTP Client

Configure the public API client in your `application.conf`:

```hocon
# Public API Client Configuration (connects to HTTP Server on port 8080)
httpClient {
  public-api {
    url = "http://localhost:8080"
    timeout = 30s
  }
}
```

## Advanced Response Mapping with @ResponseCodeMapper

Kora provides `@ResponseCodeMapper` for sophisticated HTTP response handling based on status codes. This allows you to map different HTTP status codes to different response types, providing type-safe error handling.

### Creating ErrorResponse DTO

First, create the `ErrorResponse` DTO that will be used in the error case of our response mapping:

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/example/dto/ErrorResponse.java`:

    ```java
    package ru.tinkoff.kora.example.dto;

    import java.util.Map;

    public record ErrorResponse(
        String error,
        String message,
        Map<String, String> details
    ) {

        public static ErrorResponse of(String error, String message) {
            return new ErrorResponse(error, message, Map.of());
        }

        public static ErrorResponse of(String error, String message, Map<String, String> details) {
            return new ErrorResponse(error, message, details);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/example/dto/ErrorResponse.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.dto

    data class ErrorResponse(
        val error: String,
        val message: String,
        val details: Map<String, String> = emptyMap()
    ) {

        companion object {
            fun of(error: String, message: String) = ErrorResponse(error, message)
            fun of(error: String, message: String, details: Map<String, String>) =
                ErrorResponse(error, message, details)
        }
    }
    ```

### Creating UpdateUserResult DTO and Mappers

This section introduces advanced HTTP response handling using `@ResponseCodeMapper`, which allows different HTTP status codes to be mapped to different response types. This pattern is essential for handling REST APIs that return different response structures based on success or failure conditions.

### Understanding @ResponseCodeMapper

The `@ResponseCodeMapper` annotation enables sophisticated response handling by allowing you to specify different mapper classes for different HTTP status codes:

- **Status-Specific Mapping**: You can define different response types for different HTTP status codes (e.g., 200 for success, 404 for not found)
- **Default Mapping**: The `ResponseCodeMapper.DEFAULT` constant handles all unmapped status codes (typically errors)
- **Type Safety**: Each mapper produces a specific response type, ensuring compile-time type safety

### Custom Response Mappers

Kora allows you to create custom response mappers by implementing the `HttpClientResponseMapper<T>` interface. These mappers:

**Receive Raw HTTP Response**: Mappers receive the complete `HttpResponseEntity<byte[]>` containing status code, headers, and raw body bytes

**Perform Custom Logic**: You can implement any response processing logic - JSON deserialization, header extraction, status code validation, etc.

**Return Typed Results**: Each mapper returns a specific type, allowing different mappers to return different response structures

**Dependency Injection**: Mappers can inject `JsonReader<T>` instances for type-safe JSON deserialization

### Sealed Interfaces for Response Types

Using sealed interfaces for response types provides:
- **Exhaustive Pattern Matching**: The compiler ensures you handle all possible response variants
- **Type Safety**: No runtime casting or type checking needed
- **Clean Error Handling**: Success and error cases are clearly separated at the type level

Before adding the `updateUser` method, create the `UpdateUserResult` sealed interface and its mappers:

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/example/dto/UpdateUserResult.java`:

    ```java
    package ru.tinkoff.kora.example.dto;

    import ru.tinkoff.kora.http.client.common.response.HttpClientResponseMapper;
    import ru.tinkoff.kora.http.common.HttpResponseEntity;
    import ru.tinkoff.kora.json.common.JsonReader;
    import ru.tinkoff.kora.json.common.JsonWriter;

    import java.io.IOException;

    public sealed interface UpdateUserResult permits UpdateUserResult.Success, UpdateUserResult.Error {

        @Json
        record Success(UserResponse user) implements UpdateUserResult {}
        
        @Json
        record Error(ErrorResponse error) implements UpdateUserResult {}

        class UpdateUserSuccessMapper implements HttpClientResponseMapper<UpdateUserResult.Success> {
            private final JsonReader<UserResponse> userReader;

            public UpdateUserSuccessMapper(JsonReader<UserResponse> userReader) {
                this.userReader = userReader;
            }

            @Override
            public UpdateUserResult.Success apply(HttpResponseEntity<byte[]> response) throws IOException {
                var user = userReader.read(response.body());
                return new UpdateUserResult.Success(user);
            }
        }

        class UpdateUserErrorMapper implements HttpClientResponseMapper<UpdateUserResult.Error> {
            private final JsonReader<ErrorResponse> errorReader;

            public UpdateUserErrorMapper(JsonReader<ErrorResponse> errorReader) {
                this.errorReader = errorReader;
            }

            @Override
            public UpdateUserResult.Error apply(HttpResponseEntity<byte[]> response) throws IOException {
                var error = errorReader.read(response.body());
                return new UpdateUserResult.Error(error);
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/example/dto/UpdateUserResult.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.dto

    import ru.tinkoff.kora.http.client.common.response.HttpClientResponseMapper
    import ru.tinkoff.kora.http.common.HttpResponseEntity
    import ru.tinkoff.kora.json.common.JsonReader
    import ru.tinkoff.kora.json.common.JsonWriter

    sealed interface UpdateUserResult {
        @Json
        data class Success(val user: UserResponse) : UpdateUserResult
        
        @Json
        data class Error(val error: ErrorResponse) : UpdateUserResult

        class UpdateUserSuccessMapper(private val userReader: JsonReader<UserResponse>) : HttpClientResponseMapper<UpdateUserResult.Success> {
            override fun apply(response: HttpResponseEntity<ByteArray>): UpdateUserResult.Success {
                val user = userReader.read(response.body())
                return UpdateUserResult.Success(user)
            }
        }

        class UpdateUserErrorMapper(private val errorReader: JsonReader<ErrorResponse>) : HttpClientResponseMapper<UpdateUserResult.Error> {
            override fun apply(response: HttpResponseEntity<ByteArray>): UpdateUserResult.Error {
                val error = errorReader.read(response.body())
                return UpdateUserResult.Error(error)
            }
        }
    }
    ```

### Adding @ResponseCodeMapper to Update User Endpoint

Add the `updateUser` method with `@ResponseCodeMapper` annotations to handle both success (200) and error responses:

===! ":fontawesome-brands-java: `Java`"

    Add to `src/main/java/ru/tinkoff/kora/example/client/PublicApiClient.java`:

    ```java
    // ... existing PublicApiClient interface ...

    @HttpRoute(method = HttpMethod.PUT, path = "/users/{userId}")
    @ResponseCodeMapper(code = 200, mapper = UpdateUserSuccessMapper.class)
    @ResponseCodeMapper(code = ResponseCodeMapper.DEFAULT, mapper = UpdateUserErrorMapper.class)
    UpdateUserResult updateUser(String userId, UserRequest request);

    // ... existing code ...
    ```

=== ":simple-kotlin: `Kotlin`"

    Add to `src/main/kotlin/ru/tinkoff/kora/example/client/PublicApiClient.kt`:

    ```kotlin
    // ... existing PublicApiClient interface ...

    @HttpRoute(method = HttpMethod.PUT, path = "/users/{userId}")
    @ResponseCodeMapper(code = 200, mapper = UpdateUserResult.UpdateUserSuccessMapper::class)
    @ResponseCodeMapper(code = ResponseCodeMapper.DEFAULT, mapper = UpdateUserResult.UpdateUserErrorMapper::class)
    fun updateUser(userId: String, request: UserRequest): UpdateUserResult

    // ... existing code ...
    ```

### How UpdateUserResult and Custom Mappers Work

The `UpdateUserResult` sealed interface and its custom mappers demonstrate advanced HTTP client response handling where different HTTP status codes produce different response types. This pattern provides type-safe error handling without runtime type checking.

**Sealed Interface Design**:
- `UpdateUserResult.Success`: Contains the updated `UserResponse` for successful updates (HTTP 200)
- `UpdateUserResult.Error`: Contains an `ErrorResponse` for all error cases (4xx, 5xx status codes)
- The `@Json` annotations enable automatic JSON serialization/deserialization for both success and error cases

**Custom Response Mappers**:
- `UpdateUserSuccessMapper`: Handles HTTP 200 responses by deserializing the JSON body into a `UserResponse` and wrapping it in `UpdateUserResult.Success`
- `UpdateUserErrorMapper`: Handles all other status codes by deserializing error JSON into an `ErrorResponse` and wrapping it in `UpdateUserResult.Error`

**Mapper Implementation Details**:
- Mappers receive `HttpResponseEntity<byte[]>` containing the raw HTTP response (status, headers, body bytes)
- They inject `JsonReader<T>` instances for type-safe JSON deserialization
- The `apply()` method performs the actual response transformation
- Dependency injection provides the necessary `JsonReader` instances automatically

**@ResponseCodeMapper Configuration**:
- `@ResponseCodeMapper(code = 200, mapper = UpdateUserSuccessMapper.class)`: Maps HTTP 200 to success responses
- `@ResponseCodeMapper(code = ResponseCodeMapper.DEFAULT, mapper = UpdateUserErrorMapper.class)`: Maps all other codes to error responses

This approach provides:
- **Type-safe success handling**: 200 responses automatically map to `UpdateUserResult.Success`
- **Unified error handling**: All error status codes (404, 400, 500, etc.) map to `UpdateUserResult.Error`
- **Compile-time safety**: No runtime casting or type checking needed
- **Clean API**: Single method returns a sealed interface with exhaustive handling
- **Type-safe success handling**: 200 responses automatically map to `UpdateUserResult.Success`
- **Unified error handling**: All error status codes (404, 400, 500, etc.) map to `UpdateUserResult.Error`
- **Compile-time safety**: No runtime casting or type checking needed
- **Clean API**: Single method returns a sealed interface with exhaustive handling

## Improving the Client Interface - Step by Step

Following the same iterative approach as the HTTP Server guide, let's improve our client interface to use `UserResult` for better error handling.

### Step 0: Create UserResult DTO

First, let's create the `UserResult` sealed interface that provides structured error handling:

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

### Step 1: Update the Client Interface Method Signature

First, let's change the `getUser` method to return `UserResult` instead of `Optional<UserResponse>`:

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/java/ru/tinkoff/kora/example/client/PublicApiClient.java`:

    ```java
    // ... existing code ...

    @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}")
    @Json
    UserResult getUser(String userId);

    // ... existing code ...
    ```

=== ":simple-kotlin: `Kotlin`"

    Update `src/main/kotlin/ru/tinkoff/kora/example/client/PublicApiClient.kt`:

    ```kotlin
    // ... existing code ...

    @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}")
    @Json
    fun getUser(userId: String): UserResult

    // ... existing code ...
    ```

### Step 2: Update the Controller to Handle UserResult

Now update the controller method to work with the new `UserResult` return type:

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/java/ru/tinkoff/kora/example/controller/ClientTestController.java`:

    ```java
    // ... existing code ...

    @HttpRoute(method = HttpMethod.GET, path = "/client/users/{userId}")
    @Json
    public UserResult getUserViaClient(String userId) {
        return publicApiClient.getUser(userId);
    }

    // ... existing code ...
    ```

=== ":simple-kotlin: `Kotlin`"

    Update `src/main/kotlin/ru/tinkoff/kora/example/controller/ClientTestController.kt`:

    ```kotlin
    // ... existing code ...

    @HttpRoute(method = HttpMethod.GET, path = "/client/users/{userId}")
    @Json
    fun getUserViaClient(userId: String): UserResult {
        return publicApiClient.getUser(userId)
    }

    // ... existing code ...
    ```

### Request Body Handling Endpoints

Kora HTTP clients support various request body formats to match different server API requirements. This section demonstrates how to send different types of request bodies to test the corresponding server endpoints:

- **JSON Bodies**: Automatic serialization using `@Json` annotation and JsonModule
- **Form URL-Encoded**: Key-value pairs encoded as `application/x-www-form-urlencoded` using `FormUrlEncoded`
- **Multipart Form Data**: File uploads and complex form data using `FormMultipart` for `multipart/form-data`
- **Raw Text Bodies**: Plain text or binary data sent as raw strings

These request body types correspond to the server endpoints in the HTTP Server guide that handle different content types and demonstrate Kora's flexible HTTP client capabilities for comprehensive API testing.

===! ":fontawesome-brands-java: `Java`"

    Add to `src/main/java/ru/tinkoff/kora/example/client/PublicApiClient.java`:

    ```java
    // ... existing PublicApiClient interface ...

    // Request body handling endpoints
    @HttpRoute(method = HttpMethod.POST, path = "/data/json")
    @Json
    DataResponse processJson(DataRequest request);

    @HttpRoute(method = HttpMethod.POST, path = "/data/form")
    @Json
    FormResponse processForm(FormUrlEncoded form);

    @HttpRoute(method = HttpMethod.POST, path = "/data/upload")
    @Json
    UploadResponse processUpload(FormMultipart multipart);

    @HttpRoute(method = HttpMethod.POST, path = "/data/raw")
    @Json
    RawResponse processRaw(String body);

    // DTOs for request body handling
    @Json
    record DataRequest(String message) {}
    @Json
    record DataResponse(String result) {}
    @Json
    record FormResponse(String name, String email) {}
    @Json
    record UploadResponse(int fileCount, List<String> fileNames) {}
    @Json
    record RawResponse(int length, String preview) {}
    ```

=== ":simple-kotlin: `Kotlin`"

    Add to `src/main/kotlin/ru/tinkoff/kora/example/client/PublicApiClient.kt`:

    ```kotlin
    // ... existing PublicApiClient interface ...

    // Request body handling endpoints
    @HttpRoute(method = HttpMethod.POST, path = "/data/json")
    @Json
    fun processJson(request: DataRequest): DataResponse

    @HttpRoute(method = HttpMethod.POST, path = "/data/form")
    @Json
    fun processForm(form: FormUrlEncoded): FormResponse

    @HttpRoute(method = HttpMethod.POST, path = "/data/upload")
    @Json
    fun processUpload(multipart: FormMultipart): UploadResponse

    @HttpRoute(method = HttpMethod.POST, path = "/data/raw")
    @Json
    fun processRaw(body: String): RawResponse

    // DTOs for request body handling
    @Json
    data class DataRequest(val message: String)
    @Json
    data class DataResponse(val result: String)
    @Json
    data class FormResponse(val name: String, val email: String)
    @Json
    data class UploadResponse(val fileCount: Int, val fileNames: List<String>)
    @Json
    data class RawResponse(val length: Int, val preview: String)
    ```

## Create Controller for Testing

Create a comprehensive controller that tests all endpoints from the HTTP Server guide:

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/example/controller/ClientTestController.java`:

    ```java
    package ru.tinkoff.kora.example.controller;

    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.http.common.annotation.HttpController;
    import ru.tinkoff.kora.http.common.annotation.HttpRoute;
    import ru.tinkoff.kora.http.common.HttpMethod;
    import ru.tinkoff.kora.json.common.annotation.Json;
    import ru.tinkoff.kora.example.client.PublicApiClient;
    import ru.tinkoff.kora.example.dto.UserRequest;
    import ru.tinkoff.kora.example.dto.UserResponse;
    import ru.tinkoff.kora.http.common.HttpResponseEntity;
    import ru.tinkoff.kora.http.common.form.FormMultipart;
    import ru.tinkoff.kora.http.common.form.FormUrlEncoded;

    import java.util.List;
    import java.util.Map;
    import java.util.Optional;

    @Component
    @HttpController
    public final class ClientTestController {

        private final PublicApiClient publicApiClient;

        public ClientTestController(PublicApiClient publicApiClient) {
            this.publicApiClient = publicApiClient;
        }

        // ===== USER CRUD OPERATIONS =====

        @HttpRoute(method = HttpMethod.POST, path = "/client/users")
        @Json
        public HttpResponseEntity<UserResponse> createUserViaClient(UserRequest request) {
            return publicApiClient.createUser(request);
        }

        @HttpRoute(method = HttpMethod.GET, path = "/client/users/{userId}")
        @Json
        public UserResult getUserViaClient(String userId) {
            return publicApiClient.getUser(userId);
        }

        @HttpRoute(method = HttpMethod.GET, path = "/client/users")
        @Json
        public List<UserResponse> getAllUsersViaClient() {
            return publicApiClient.getUsers();
        }

        @HttpRoute(method = HttpMethod.PUT, path = "/client/users/{userId}")
        @Json
        public UpdateUserResult updateUserViaClient(String userId, UserRequest request) {
            return publicApiClient.updateUser(userId, request);
        }

        @HttpRoute(method = HttpMethod.DELETE, path = "/client/users/{userId}")
        public HttpResponseEntity<Void> deleteUserViaClient(String userId) {
            return publicApiClient.deleteUser(userId);
        }

        // ===== ADVANCED ROUTING =====

        @HttpRoute(method = HttpMethod.GET, path = "/client/users/{userId}/posts/{postId}")
        @Json
        public PublicApiClient.Post getUserPostViaClient(String userId, String postId) {
            return publicApiClient.getUserPost(userId, postId);
        }

        // ===== REQUEST BODY HANDLING =====

        @HttpRoute(method = HttpMethod.POST, path = "/client/data/json")
        @Json
        public PublicApiClient.DataResponse processJsonViaClient(PublicApiClient.DataRequest request) {
            return publicApiClient.processJson(request);
        }

        @HttpRoute(method = HttpMethod.POST, path = "/client/data/form")
        @Json
        public PublicApiClient.FormResponse processFormViaClient(FormUrlEncoded form) {
            return publicApiClient.processForm(form);
        }

        @HttpRoute(method = HttpMethod.POST, path = "/client/data/upload")
        @Json
        public PublicApiClient.UploadResponse processUploadViaClient(FormMultipart multipart) {
            return publicApiClient.processUpload(multipart);
        }

        @HttpRoute(method = HttpMethod.POST, path = "/client/data/raw")
        @Json
        public PublicApiClient.RawResponse processRawViaClient(String body) {
            return publicApiClient.processRaw(body);
        }

        // ===== COMPREHENSIVE TEST ENDPOINT =====

        @HttpRoute(method = HttpMethod.POST, path = "/client/test-all")
        @Json
        public TestResults testAllEndpoints() {
            var results = new TestResults();

            try {
                // Test user creation
                var createResponse = publicApiClient.createUser(new UserRequest("Test User", "test@example.com"));
                results.userCreated = createResponse.code() == 201;

                // Test user retrieval
                var userId = "1"; // Assuming server creates user with ID 1
                var user = publicApiClient.getUser(userId);
                results.userRetrieved = user.isPresent;

                // Test data processing
                var jsonResponse = publicApiClient.processJson(new PublicApiClient.DataRequest("Hello from client"));
                results.jsonProcessed = jsonResponse.result().contains("Hello from client");

                results.allTestsPassed = results.userCreated && results.userRetrieved && results.jsonProcessed;

            } catch (Exception e) {
                results.error = e.getMessage();
                results.allTestsPassed = false;
            }

            return results;
        }

        @Json
        public record TestResults(
            boolean userCreated,
            boolean userRetrieved,
            boolean jsonProcessed,
            boolean allTestsPassed,
            String error
        ) {
            public TestResults() {
                this(false, false, false, false, null);
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/example/controller/ClientTestController.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.controller

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.http.common.annotation.*
    import ru.tinkoff.kora.http.common.HttpMethod
    import ru.tinkoff.kora.http.common.HttpResponseEntity
    import ru.tinkoff.kora.json.common.annotation.Json
    import ru.tinkoff.kora.example.client.PublicApiClient
    import ru.tinkoff.kora.example.dto.UserRequest
    import ru.tinkoff.kora.example.dto.UserResponse
    import ru.tinkoff.kora.http.common.form.FormMultipart
    import ru.tinkoff.kora.http.common.form.FormUrlEncoded

    @Component
    @HttpController
    class ClientTestController(
        private val publicApiClient: PublicApiClient
    ) {

        // ===== USER CRUD OPERATIONS =====

        @HttpRoute(method = HttpMethod.POST, path = "/client/users")
        @Json
        fun createUserViaClient(request: UserRequest): HttpResponseEntity<UserResponse> {
            return publicApiClient.createUser(request)
        }

        @HttpRoute(method = HttpMethod.GET, path = "/client/users/{userId}")
        @Json
        fun getUserViaClient(userId: String): UserResult {
            return publicApiClient.getUser(userId)
        }

        @HttpRoute(method = HttpMethod.GET, path = "/client/users")
        @Json
        fun getAllUsersViaClient(): List<UserResponse> {
            return publicApiClient.getUsers()
        }

        @HttpRoute(method = HttpMethod.PUT, path = "/client/users/{userId}")
        @Json
        fun updateUserViaClient(userId: String, request: UserRequest): UpdateUserResult {
            return publicApiClient.updateUser(userId, request)
        }

        @HttpRoute(method = HttpMethod.DELETE, path = "/client/users/{userId}")
        fun deleteUserViaClient(userId: String): HttpResponseEntity<Void> {
            return publicApiClient.deleteUser(userId)
        }

        // ===== ADVANCED ROUTING =====

        @HttpRoute(method = HttpMethod.GET, path = "/client/users/{userId}/posts/{postId}")
        @Json
        fun getUserPostViaClient(userId: String, postId: String): PublicApiClient.Post {
            return publicApiClient.getUserPost(userId, postId)
        }

        // ===== REQUEST BODY HANDLING =====

        @HttpRoute(method = HttpMethod.POST, path = "/client/data/json")
        @Json
        fun processJsonViaClient(request: PublicApiClient.DataRequest): PublicApiClient.DataResponse {
            return publicApiClient.processJson(request)
        }

        @HttpRoute(method = HttpMethod.POST, path = "/client/data/form")
        @Json
        fun processFormViaClient(form: FormUrlEncoded): PublicApiClient.FormResponse {
            return publicApiClient.processForm(form)
        }

        @HttpRoute(method = HttpMethod.POST, path = "/client/data/upload")
        @Json
        fun processUploadViaClient(multipart: FormMultipart): PublicApiClient.UploadResponse {
            return publicApiClient.processUpload(multipart)
        }

        @HttpRoute(method = HttpMethod.POST, path = "/client/data/raw")
        @Json
        fun processRawViaClient(body: String): PublicApiClient.RawResponse {
            return publicApiClient.processRaw(body)
        }

        // ===== COMPREHENSIVE TEST ENDPOINT =====

        @HttpRoute(method = HttpMethod.POST, path = "/client/test-all")
        @Json
        fun testAllEndpoints(): TestResults {
            return try {
                // Test user creation
                val createResponse = publicApiClient.createUser(UserRequest("Test User", "test@example.com"))
                val userCreated = createResponse.code() == 201

                // Test user retrieval
                val user = publicApiClient.getUser("1") // Assuming server creates user with ID 1
                val userRetrieved = user.isPresent

                // Test data processing
                val jsonResponse = publicApiClient.processJson(PublicApiClient.DataRequest("Hello from client"))
                val jsonProcessed = jsonResponse.result.contains("Hello from client")

                val allTestsPassed = userCreated && userRetrieved && jsonProcessed

                TestResults(userCreated, userRetrieved, jsonProcessed, allTestsPassed, null)

            } catch (e: Exception) {
                TestResults(false, false, false, false, e.message)
            }
        }

        @Json
        data class TestResults(
            val userCreated: Boolean,
            val userRetrieved: Boolean,
            val jsonProcessed: Boolean,
            val allTestsPassed: Boolean,
            val error: String?
        )
    }
    ```

## Port Configuration

    This HTTP client guide runs as a separate application from the HTTP Server guide. To avoid conflicts:

    - **HTTP Server** should run on port 8080 (public API)
    - **HTTP Client** should run on port 8081 (public API)

    ```hocon
    http-server {
      publicApiHttpPort = 8081
    }
    ```

    **Testing Setup**: Run HTTP Server first on port 8080, then run HTTP Client on port 8081.

## Running the Application

```bash
./gradlew run
```

## Testing HTTP Client

Test the HTTP client by calling endpoints that mirror the HTTP Server guide:

### Setup Testing Environment

1. **Start HTTP Server** (in terminal 1):
   ```bash
   cd /path/to/http-server-advanced
   ./gradlew run
   ```
   Server runs on port 8080 (public API)

2. **Start HTTP Client** (in terminal 2):
   ```bash
   cd /path/to/http-client
   ./gradlew run
   ```
   Client runs on port 8081 (public API)

### Test User CRUD Operations

```bash
# Create a user via HTTP client (should return 201 Created)
curl -X POST http://localhost:8081/client/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Client User", "email": "client@example.com"}'

# Get user by ID via HTTP client
curl http://localhost:8081/client/users/1

# Get all users via HTTP client
curl http://localhost:8081/client/users

# Update user via HTTP client (should return custom headers)
curl -X PUT http://localhost:8081/client/users/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Client User", "email": "updated@example.com"}' \
  -v

# Delete user via HTTP client (should return 204 No Content)
curl -X DELETE http://localhost:8081/client/users/1
```

### Test Advanced Routing

```bash
# Test multiple path parameters
curl http://localhost:8081/client/users/1/posts/456
```

### Test Request Body Handling

```bash
# Test JSON request body
curl -X POST http://localhost:8081/client/data/json \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello from HTTP client"}'

# Test Form URL-encoded data
curl -X POST http://localhost:8081/client/data/form \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "name=John&email=john@example.com"

# Test Multipart form data (file upload)
curl -X POST http://localhost:8081/client/data/upload \
  -F "files=@test.txt" \
  -F "files=@test2.txt"

# Test raw text body
curl -X POST http://localhost:8081/client/data/raw \
  -H "Content-Type: text/plain" \
  -d "This is raw text content"
```

### Comprehensive Integration Test

```bash
# Run all tests at once (tests public API endpoints)
curl -X POST http://localhost:8081/client/test-all \
  -H "Content-Type: application/json" \
  -d '{}'
```

!!! tip "Expected Results"

    - **User Creation**: Should return HTTP 201 with user data
    - **User Retrieval**: Should return user data or empty for non-existent users
    - **User Update**: Should return HTTP 200 with `X-Updated-At` header
    - **User Deletion**: Should return HTTP 204 (no content)
    - **Data Processing**: Should return processed data in expected format
    - **Integration Test**: Should return JSON with all test results

## Key Concepts Learned

### Declarative HTTP Clients
- **`@HttpClient`**: Marks interfaces as HTTP client contracts with named configurations
- **`@HttpRoute`**: Defines HTTP method, path, and parameters for type-safe API calls
- **`@Json`**: Enables automatic JSON serialization/deserialization for request/response bodies
- **Type Safety**: Compile-time verification of API contracts and data structures

### HTTP Client Architecture
- **Client Configuration**: Named client configurations for different environments
- **Type Safety**: Compile-time verification of API contracts and data structures
- **Error Handling**: Proper exception mapping for HTTP errors

### Advanced Request Handling
- **Path Parameters**: Type-safe URL parameter extraction (`/users/{userId}`)
- **Query Parameters**: Optional pagination, sorting, and filtering
- **Request Body Types**: JSON, Form URL-encoded, Multipart uploads, raw text
- **Custom Mappers**: Flexible request/response transformation

### Response Processing
- **HttpResponseEntity**: Access to HTTP status codes, headers, and response bodies
- **Optional Responses**: Proper handling of nullable/optional API responses
- **Error Handling**: Automatic exception mapping for HTTP errors
- **Custom Response Types**: Support for complex response structures

### Integration Testing
- **End-to-End Testing**: Client-to-server integration validation
- **Health Check Testing**: Monitoring endpoint verification
- **Comprehensive Test Suites**: Automated testing of all API features
- **Multi-Application Setup**: Running client and server applications simultaneously

## What's Next?

- [JUnit Testing Guide](../junit-testing.md)
- [OpenAPI Client Generator](../openapi-client-generator.md)
- [Kafka Messaging](../kafka-messaging.md)

## Help

If you encounter issues:

- Check the [HTTP Client Documentation](../../documentation/http-client.md)
- Verify `application.conf` client configuration
- Ensure the target server is running and accessible
- Check the [HTTP Client Example](https://github.com/kora-projects/kora-examples/tree/master/kora-java-http-client)
- Ask questions on [GitHub Discussions](https://github.com/kora-projects/kora/discussions)

## Troubleshooting

### Connection Issues
- Verify target server URL in `application.conf`
- Check network connectivity and firewall settings
- Test direct connection: `curl http://target-server:port/health`

### Serialization Errors
- Ensure DTO classes match server API contract
- Check `@Json` annotations on client interface methods
- Verify JSON structure matches server expectations

### Timeout Issues
- Adjust timeout settings in client configuration
- Consider server response times and network latency
- Implement proper error handling for timeout scenarios