---
title: HTTP Server Guide
summary: Learn how to build REST APIs with Kora's HTTP server, including routing, request handling, JSON serialization, and basic server configuration
tags: http-server, rest-api, json, routing, beginner
---

# HTTP Server Guide

This guide covers building REST APIs with Kora's HTTP server. Learn about HTTP routing, request/response handling, JSON serialization, and basic server configuration to create your first web services.

## What You'll Build

You'll create a complete REST API with:

- **HTTP Controllers**: Define API endpoints with proper routing
- **Request/Response Handling**: Process JSON data and return appropriate responses
- **Path Parameters**: Extract data from URL paths
- **Query Parameters**: Handle optional parameters for filtering and pagination
- **Request Body Processing**: Accept and validate JSON input
- **Error Handling**: Implement proper HTTP error responses
- **Basic Interceptors**: Add logging and error handling middleware

## What You'll Need

- JDK 17 or later
- Gradle 7.0+
- A text editor or IDE
- Completed [Creating Your First Kora App](../getting-started.md) guide

## Prerequisites

!!! note "Required: Complete Basic Kora Setup"

    This guide assumes you have completed the **[Create Your First Kora App](../getting-started.md)** guide and have a working Kora project with basic setup, and also that you completed the **[JSON Guide](../json.md)** and understand how to work with JSON serialization in Kora.

    If you haven't completed those guides yet, please do so first as this guide builds upon those concepts.

### Add Dependencies

Add the following dependencies to your existing Kora project:

===! ":fontawesome-brands-java: `Java`"

    ```gradle title="build.gradle"
    dependencies {
        // ... existing dependencies ...

        implementation("ru.tinkoff.kora:json-module")
    }
    ```

===! ":fontawesome-brands-kotlin: `Kotlin`"

    ```kotlin title="build.gradle.kts"
    dependencies {
        // ... existing dependencies ...

        implementation("ru.tinkoff.kora:json-module")
    }
    ```

## Add Modules

Update your Application interface to include all modules:

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/ru/tinkoff/kora/example/Application.java`:

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
            LogbackModule {
    }
    ```

===! ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/ru/tinkoff/kora/example/Application.kt`:

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
        LogbackModule
    ```

## Create Request/Response DTOs

Data Transfer Objects (DTOs) are simple objects that carry data between processes. In HTTP APIs, DTOs define the structure of request and response data, providing a clear contract between your API and its clients.

### Why Use DTOs?

**API Contract Definition**: DTOs serve as the official schema for your API endpoints, making it clear what data is expected and returned.

**Type Safety**: Strongly-typed objects prevent runtime errors and provide compile-time validation.

**Serialization Control**: DTOs give you full control over JSON serialization/deserialization, allowing you to customize field names, exclude sensitive data, and handle complex data transformations.

**Validation**: DTOs can be annotated with validation constraints to ensure data integrity.

**Documentation**: Well-designed DTOs make your API self-documenting and easier to understand.

### DTO Design Principles

**Request DTOs**: Should contain only the fields needed to process the request. Keep them minimal and focused.

**Response DTOs**: Should contain the data clients need, but avoid exposing internal implementation details or sensitive information.

**Naming Conventions**: Use clear, descriptive names that reflect the business domain.

**Immutability**: Use records (Java) or data classes (Kotlin) to ensure DTOs are immutable.

**Validation**: Include validation annotations where appropriate.

### Kora DTO Features

**Automatic JSON Serialization**: With the `@Json` annotation, Kora automatically handles JSON conversion.

**Record Support**: Java records provide concise, immutable DTO definitions.

**Null Safety**: Proper handling of nullable vs non-nullable fields.

**Custom Serialization**: Override default JSON behavior when needed.

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

===! ":simple-kotlin: `Kotlin`"

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

### DTO Analysis

**UserRequest DTO**:
- **Purpose**: Defines the data structure for creating new users
- **Fields**: `name` and `email` - the minimum required information to create a user
- **Design**: Simple and focused, containing only essential fields
- **Usage**: Used in POST `/users` endpoint for user creation

**UserResponse DTO**:
- **Purpose**: Defines the complete user data returned to clients
- **Fields**: `id`, `name`, `email`, `createdAt` - includes system-generated fields
- **Design**: Contains all user information including server-generated data like ID and timestamps
- **Usage**: Returned by GET endpoints and included in successful POST/PUT responses

**ErrorResponse DTO**:
- **Purpose**: Standardized error response format for consistent error handling
- **Fields**: `error` (error code), `message` (human-readable description), `details` (additional error context)
- **Design**: Flexible structure that can handle various error scenarios
- **Factory Methods**: Convenient `of()` methods for creating error responses
- **Usage**: Used by error interceptors and exception handlers throughout the application

### DTO Best Practices Demonstrated

**Separation of Concerns**: Request and response DTOs are separate, allowing different validation rules and field sets.

**Immutable Design**: All DTOs use records (Java) or data classes (Kotlin) for immutability.

**Factory Methods**: ErrorResponse includes static factory methods for convenient creation.

**Consistent Naming**: Clear, descriptive field names that match API documentation.

**Type Safety**: Strong typing prevents runtime errors and provides IDE support.

## Create User Service

Create a service layer to handle user business logic:

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

        public Optional<UserResponse> getUser(String id) {
            return Optional.ofNullable(users.get(id));
        }

        public List<UserResponse> getAllUsers() {
            return new ArrayList<>(users.values());
        }

        public List<UserResponse> getUsers(int page, int size, String sort) {
            return users.values().stream()
                .sorted(this.getComparator(sort))
                .skip((long) page * size)
                .limit(size)
                .toList();
        }

        public Optional<UserResponse> updateUser(String id, UserRequest request) {
            return Optional.ofNullable(users.computeIfPresent(id, (k, v) ->
                new UserResponse(k, request.name(), request.email(), v.createdAt())
            ));
        }

        public boolean deleteUser(String id) {
            return users.remove(id) != null;
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

===! ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/example/service/UserService.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.service

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.example.dto.UserRequest
    import ru.tinkoff.kora.example.dto.UserResponse
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

        fun getUser(id: String): UserResponse? {
            return users[id]
        }

        fun getAllUsers(): List<UserResponse> {
            return users.values.toList()
        }

        fun getUsers(page: Int, size: Int, sort: String): List<UserResponse> {
            return users.values
                .sortedWith(getComparator(sort))
                .drop(page * size)
                .take(size)
        }

        fun updateUser(id: String, request: UserRequest): UserResponse? {
            return users.computeIfPresent(id) { _, existing ->
                existing.copy(name = request.name, email = request.email)
            }
        }

        fun deleteUser(id: String): Boolean {
            return users.remove(id) != null
        }

        private fun getComparator(sort: String): Comparator<UserResponse> {
            return when (sort.lowercase()) {
                "name" -> compareBy { it.name }
                "email" -> compareBy { it.email }
                "createdat" -> compareBy { it.createdAt }
                else -> compareBy { it.name }
            }
        }
    }
    ```

## Create Controller with Path Parameters

HTTP routing in Kora supports various parameter types to extract data from incoming requests. This section demonstrates basic routing features including path parameters, query parameters, and proper HTTP responses.

### Understanding Parameter Types

**Path Parameters** (`@Path`): Extract values from the URL path itself. These are required parameters that become part of the route pattern (e.g., `/users/{userId}`).

**Query Parameters** (`@Query`): Optional parameters passed in the URL query string (e.g., `?page=1&size=10`). These are typically used for filtering, pagination, and sorting.

**Header Parameters** (`@Header`): Extract values from HTTP request headers. Commonly used for authentication tokens, request IDs, and content negotiation.

**Cookie Parameters** (`@Cookie`): Access HTTP cookies sent by the client. Useful for session management and user preferences.

### HTTP Response Control

Kora provides two main ways to control HTTP responses:

1. **Direct Object Return**: Simply return your data object - Kora automatically returns HTTP 200 OK with JSON serialization
2. **HttpResponseEntity**: Full control over status codes, headers, and response body for complex scenarios

### Error Handling Patterns

Instead of returning `Optional<T>` and handling null checks manually, Kora encourages throwing `HttpServerResponseException` for HTTP error responses. This provides clean, declarative error handling that automatically maps to appropriate HTTP status codes.

### Implementation

Create a controller demonstrating routing features that uses the UserService:

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/example/controller/UserController.java`:

    ```java
    package ru.tinkoff.kora.example.controller;

    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.http.common.HttpMethod;
    import ru.tinkoff.kora.http.common.annotation.HttpController;
    import ru.tinkoff.kora.http.common.annotation.HttpRoute;
    import ru.tinkoff.kora.http.common.annotation.Path;
    import ru.tinkoff.kora.http.common.annotation.Query;
    import ru.tinkoff.kora.http.common.annotation.Header;
    import ru.tinkoff.kora.http.common.annotation.Cookie;
    import ru.tinkoff.kora.http.common.annotation.Mapping;
    import ru.tinkoff.kora.http.common.HttpResponseEntity;
    import ru.tinkoff.kora.http.common.header.HttpHeaders;
    import ru.tinkoff.kora.http.server.common.HttpServerRequest;
    import ru.tinkoff.kora.http.server.common.HttpServerRequestMapper;
    import ru.tinkoff.kora.json.common.annotation.Json;
    import ru.tinkoff.kora.example.service.UserService;
    import ru.tinkoff.kora.example.dto.UserRequest;
    import ru.tinkoff.kora.example.dto.UserResponse;

    import java.time.Instant;
    import java.util.List;
    import java.util.Optional;

    @Component
    @HttpController
    public final class UserController {

        private final UserService userService;

        public UserController(UserService userService) {
            this.userService = userService;
        }

        // Path parameter example
        @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}")
        @Json
        public UserResponse getUser(@Path String userId) {
            return userService.getUser(userId)
                .orElseThrow(() -> HttpServerResponseException.of(404, "User not found"));
        }

        // Query parameters with pagination
        @HttpRoute(method = HttpMethod.GET, path = "/users")
        @Json
        public List<UserResponse> getUsers(
            @Query("page") Optional<Integer> page,
            @Query("size") Optional<Integer> size,
            @Query("sort") Optional<String> sort
        ) {
            int pageNum = page.orElse(0);
            int pageSize = size.orElse(10);
            String sortBy = sort.orElse("name");
            return userService.getUsers(pageNum, pageSize, sortBy);
        }

        // Headers and cookies - Demonstrates proper HTTP 201 Created response
        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        public HttpResponseEntity<UserResponse> createUser(
            UserRequest request,
            @Header("X-Request-ID") Optional<String> requestId,
            @Header("User-Agent") Optional<String> userAgent,
            @Cookie("sessionId") Optional<String> sessionId
        ) {
            UserResponse user = userService.createUser(request);
            // HttpResponseEntity allows custom HTTP status codes and headers
            // 201 Created is the standard response for successful resource creation
            // This differs from returning UserResponse directly (which gives 200 OK)
            return HttpResponseEntity.of(201, HttpHeaders.of(), user);
        }

        // Custom response with headers
        @HttpRoute(method = HttpMethod.PUT, path = "/users/{userId}")
        @Json
        public HttpResponseEntity<UserResponse> updateUser(@Path String userId, UserRequest request) {
            Optional<UserResponse> updatedUser = userService.updateUser(userId, request);
            if (updatedUser.isEmpty()) {
                throw HttpServerResponseException.of(404, "User not found");
            }
            return HttpResponseEntity.of(200, HttpHeaders.of("X-Updated-At", Instant.now().toString()), updatedUser.get());
        }

        // Delete user
        @HttpRoute(method = HttpMethod.DELETE, path = "/users/{userId}")
        public HttpResponseEntity<Void> deleteUser(@Path String userId) {
            boolean deleted = userService.deleteUser(userId);
            if (!deleted) {
                throw HttpServerResponseException.of(404, "User not found");
            }
            return HttpResponseEntity.of(204, HttpHeaders.of(), null);
        }
    }
    ```

===! ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/example/controller/UserController.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.controller

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.http.common.HttpMethod
    import ru.tinkoff.kora.http.common.annotation.*
    import ru.tinkoff.kora.http.common.HttpResponseEntity
    import ru.tinkoff.kora.http.common.header.HttpHeaders
    import ru.tinkoff.kora.http.server.common.HttpServerRequest
    import ru.tinkoff.kora.json.common.annotation.Json
    import ru.tinkoff.kora.example.service.UserService
    import ru.tinkoff.kora.example.dto.UserRequest
    import ru.tinkoff.kora.example.dto.UserResponse
    import java.time.Instant

    @Component
    @HttpController
    class UserController(
        private val userService: UserService
    ) {

        // Path parameter example
        @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}")
        @Json
        fun getUser(@Path userId: String): UserResponse {
            return userService.getUser(userId)
                ?: throw HttpServerResponseException.of(404, "User not found")
        }

        // Query parameters with pagination
        @HttpRoute(method = HttpMethod.GET, path = "/users")
        @Json
        fun getUsers(
            @Query("page") page: Int? = 0,
            @Query("size") size: Int? = 10,
            @Query("sort") sort: String? = "name"
        ): List<UserResponse> {
            val pageNum = page ?: 0
            val pageSize = size ?: 10
            val sortBy = sort ?: "name"
            return userService.getUsers(pageNum, pageSize, sortBy)
        }

        // Headers and cookies - Demonstrates proper HTTP 201 Created response
        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        fun createUser(
            request: UserRequest,
            @Header("X-Request-ID") requestId: String?,
            @Header("User-Agent") userAgent: String?,
            @Cookie("sessionId") sessionId: String?
        ): HttpResponseEntity<UserResponse> {
            val user = userService.createUser(request)
            // HttpResponseEntity allows custom HTTP status codes and headers
            // 201 Created is the standard response for successful resource creation
            // This differs from returning UserResponse directly (which gives 200 OK)
            return HttpResponseEntity.of(201, HttpHeaders.of(), user)
        }

        // Custom response with headers
        @HttpRoute(method = HttpMethod.PUT, path = "/users/{userId}")
        @Json
        fun updateUser(@Path userId: String, request: UserRequest): HttpResponseEntity<UserResponse> {
            val updatedUser = userService.updateUser(userId, request)
            if (updatedUser == null) {
                throw HttpServerResponseException.of(404, "User not found")
            }
            return HttpResponseEntity.of(200, HttpHeaders.of("X-Updated-At", Instant.now().toString()), updatedUser)
        }

        // Delete user
        @HttpRoute(method = HttpMethod.DELETE, path = "/users/{userId}")
        fun deleteUser(@Path userId: String): HttpResponseEntity<Void> {
            val deleted = userService.deleteUser(userId)
            if (!deleted) {
                throw HttpServerResponseException.of(404, "User not found")
            }
            return HttpResponseEntity.of(204, HttpHeaders.of(), null)
        }
    }
    ```

### Controller Method Breakdown

**Path Parameter Method** (`getUser`):
- Uses `@Path("userId")` to extract the user ID from the URL
- Demonstrates proper error handling with `HttpServerResponseException.of(404, "User not found")`
- Returns `UserResponse` directly, which Kora automatically serializes to JSON with HTTP 200

**Query Parameters with Pagination** (`getUsers`):
- All query parameters are `Optional<Integer>` or `Optional<String>` since they're not required
- Provides default values (page=0, size=10, sort="name") when parameters aren't provided
- Implements server-side pagination and sorting for large datasets

**Headers and Cookies with Custom Response** (`createUser`):
- Extracts request metadata using `@Header` and `@Cookie` annotations
- Uses `HttpResponseEntity<UserResponse>` to return HTTP 201 Created (standard for resource creation)
- Demonstrates that `HttpResponseEntity.of(201, HttpHeaders.of(), user)` differs from returning `user` directly (which would be HTTP 200)

**Custom Response Headers** (`updateUser`):
- Shows how to add custom headers to responses using `HttpHeaders.of("X-Updated-At", timestamp)`
- Uses `HttpServerResponseException` for clean error handling instead of conditional returns
- Returns HTTP 200 with additional metadata headers

**DELETE with No Content Response** (`deleteUser`):
- Returns `HttpResponseEntity<Void>` with HTTP 204 No Content (standard for successful deletions)
- Demonstrates proper REST semantics for resource removal


## Create Custom Request Mappers

Custom request mappers allow you to extract complex parameter combinations from HTTP requests into structured objects. Instead of having many individual parameters in your controller methods, you can create a mapper that consolidates related request data into a single object.

### Why Use Custom Request Mappers?

**Code Organization**: Group related request parameters (headers, cookies, query params) into logical units
**Reusability**: Use the same parameter extraction logic across multiple endpoints
**Type Safety**: Strongly-typed objects instead of individual optional parameters
**Maintainability**: Centralized request parsing logic that's easier to test and modify
**Validation**: Apply complex validation rules to parameter combinations

### How Request Mappers Work?

1. **Implement `HttpServerRequestMapper<T>`**: Create a class that implements this interface
2. **Extract Data**: Use the `HttpServerRequest` object to access headers, cookies, query parameters, etc.
3. **Return Structured Object**: Transform the raw request data into your custom type
4. **Use with `@Mapping`**: Apply the mapper to controller method parameters

### Common Use Cases

- **Authentication Context**: Extract user ID, roles, and permissions from headers/cookies
- **Request Metadata**: Combine request ID, user agent, client IP, and tracing information
- **Pagination Parameters**: Group page, size, sort, and filter parameters
- **Search Criteria**: Complex search forms with multiple optional filters

### Implementation

Implement custom request parameter extraction using `HttpServerRequestMapper` to refactor existing methods:

===! ":fontawesome-brands-java: `Java`"

    Update your `UserController.java` to use custom request mappers:

    ```java
    // ...existing code...

    @Component
    @HttpController
    public final class UserController {

        // ...existing code...

        // Custom request mapper for request context
        public static final class RequestContextMapper implements HttpServerRequestMapper<RequestContext> {

            @Override
            public RequestContext apply(HttpServerRequest request) {
                String requestId = request.headers().getFirst("X-Request-ID");
                String userAgent = request.headers().getFirst("User-Agent");
                String sessionId = request.cookies().getFirst("sessionId");

                return new RequestContext(requestId, userAgent, sessionId);
            }
        }

        // BEFORE: Using individual parameters
        // @HttpRoute(method = HttpMethod.POST, path = "/users")
        // @Json
        // public HttpResponseEntity<UserResponse> createUser(
        //     UserRequest request,
        //     @Header("X-Request-ID") Optional<String> requestId,
        //     @Header("User-Agent") String userAgent,
        //     @Cookie("sessionId") Optional<String> sessionId
        // ) {
        //     UserResponse user = userService.createUser(request);
        //     return HttpResponseEntity.of(201, HttpHeaders.of(), user);
        // }

        // AFTER: Using custom request mapper
        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        public HttpResponseEntity<UserResponse> createUser(
            UserRequest request,
            @Mapping(RequestContextMapper.class) RequestContext context
        ) {
            // Access request context for logging/auditing
            System.out.printf("Creating user with request ID: %s, user agent: %s%n",
                context.requestId(), context.userAgent());

            UserResponse user = userService.createUser(request);
            // HttpResponseEntity allows custom HTTP status codes and headers
            // 201 Created is the standard response for successful resource creation
            return HttpResponseEntity.of(201, HttpHeaders.of(), user);
        }

        // ...existing code...

        @Json
        public record RequestContext(String requestId, String userAgent, String sessionId) {}
    }
    ```

===! ":simple-kotlin: `Kotlin`"

    Update your `UserController.kt` to use custom request mappers:

    ```kotlin
    // ...existing code...

    @Component
    @HttpController
    class UserController(
        private val userService: UserService
    ) {

        // ...existing code...

        // Custom request mapper for request context
        class RequestContextMapper : HttpServerRequestMapper<RequestContext> {
            override fun apply(request: HttpServerRequest): RequestContext {
                val requestId = request.headers().getFirst("X-Request-ID")
                val userAgent = request.headers().getFirst("User-Agent")
                val sessionId = request.cookies().getFirst("sessionId")

                return RequestContext(requestId, userAgent, sessionId)
            }
        }

        // BEFORE: Using individual parameters
        // @HttpRoute(method = HttpMethod.POST, path = "/users")
        // @Json
        // fun createUser(
        //     request: UserRequest,
        //     @Header("X-Request-ID") requestId: String?,
        //     @Header("User-Agent") userAgent: String,
        //     @Cookie("sessionId") sessionId: String?
        // ): HttpResponseEntity<UserResponse> {
        //     val user = userService.createUser(request)
        //     return HttpResponseEntity.of(201, HttpHeaders.of(), user)
        // }

        // AFTER: Using custom request mapper
        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        fun createUser(
            request: UserRequest,
            @Mapping(RequestContextMapper::class) context: RequestContext
        ): HttpResponseEntity<UserResponse> {
            // Access request context for logging/auditing
            println("Creating user with request ID: ${context.requestId}, user agent: ${context.userAgent}")

            val user = userService.createUser(request)
            // HttpResponseEntity allows custom HTTP status codes and headers
            // 201 Created is the standard response for successful resource creation
            return HttpResponseEntity.of(201, HttpHeaders.of(), user);
        }

        // ...existing code...
    }

    @Json
    data class RequestContext(val requestId: String?, val userAgent: String?, val sessionId: String?)
    ```

### Request Mapper Implementation Details

**RequestContextMapper Class**:
- **Implements `HttpServerRequestMapper<RequestContext>`**: This interface requires an `apply()` method that takes an `HttpServerRequest` and returns your custom type
- **Extracts Individual Values**: Uses `request.headers().getFirst()` and `request.cookies().getFirst()` to access specific header and cookie values
- **Returns Structured Data**: Combines related request metadata into a single `RequestContext` record

**Before vs After Comparison**:
- **Before**: Method signature had 4+ parameters, making it cluttered and hard to read
- **After**: Clean method signature with `@Mapping(RequestContextMapper.class) RequestContext context`

**Benefits Demonstrated**:
- **Cleaner Code**: The `createUser` method now focuses on business logic rather than parameter extraction
- **Logging/Auditing**: Request context is easily accessible for logging user actions
- **Type Safety**: `RequestContext` provides compile-time guarantees about available data
- **Testability**: Request mappers can be unit tested independently

**Advanced Patterns**:
- **Validation**: Add validation logic within the mapper (e.g., check required headers)
- **Transformation**: Convert string values to enums, dates, or other types
- **Caching**: Cache expensive parsing operations if needed
- **Composition**: Combine multiple mappers for complex scenarios

## Create Request Body Handling Controller

Modern web applications need to handle various content types and request formats. Kora provides comprehensive support for different request body formats including JSON, form data, multipart uploads, and raw content.

### Content Type Overview

**JSON (`application/json`)**: Most common for REST APIs. Automatically deserialized by Kora using the JsonModule.

**Form URL-Encoded (`application/x-www-form-urlencoded`)**: Traditional web form submission format. Key-value pairs encoded in the request body.

**Multipart Form Data (`multipart/form-data`)**: Used for file uploads and complex forms. Can contain multiple parts including files and text fields.

**Raw/Text Content**: Direct access to request body as string. Useful for custom formats, webhooks, or when you need full control over parsing.

### When to Use Each Format

- **JSON**: REST APIs, complex structured data, mobile app communication
- **Form Data**: Simple web forms, legacy system integration
- **Multipart**: File uploads, mixed content (files + form fields), large data transfers
- **Raw**: Webhooks, custom protocols, binary data processing

### File Upload Considerations

- **Memory Usage**: Large files should be streamed to avoid memory issues
- **Validation**: Always validate file types, sizes, and content
- **Storage**: Consider temporary storage vs direct processing
- **Security**: Implement proper file handling to prevent attacks

### Implementation

Demonstrate different request body formats:

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/example/controller/DataController.java`:

    ```java
    package ru.tinkoff.kora.example.controller;

    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.http.common.HttpMethod;
    import ru.tinkoff.kora.http.common.annotation.HttpController;
    import ru.tinkoff.kora.http.common.annotation.HttpRoute;
    import ru.tinkoff.kora.http.common.annotation.Form;
    import ru.tinkoff.kora.http.common.form.FormMultipart;
    import ru.tinkoff.kora.http.common.form.FormUrlEncoded;
    import ru.tinkoff.kora.json.common.annotation.Json;

    import java.util.List;

    @Component
    @HttpController
    public final class DataController {

        // JSON request body (automatic with JsonModule)
        @HttpRoute(method = HttpMethod.POST, path = "/data/json")
        public DataResponse processJson(DataRequest request) {
            return new DataResponse("Processed: " + request.message());
        }

        // Form URL-encoded data
        @HttpRoute(method = HttpMethod.POST, path = "/data/form")
        public FormResponse processForm(FormUrlEncoded form) {
            String name = form.getString("name").orElse("Unknown");
            String email = form.getString("email").orElse("Unknown");

            return new FormResponse(name, email);
        }

        // Multipart form data (file uploads)
        @HttpRoute(method = HttpMethod.POST, path = "/data/upload")
        public UploadResponse processUpload(FormMultipart multipart) {
            List<FormMultipart.FormPart> files = multipart.getParts("files");

            return new UploadResponse(
                files.size(),
                files.stream().map(FormMultipart.FormPart::getName).toList()
            );
        }

        // Raw request body
        @HttpRoute(method = HttpMethod.POST, path = "/data/raw")
        public RawResponse processRaw(String body) {
            return new RawResponse(body.length(), body.substring(0, Math.min(50, body.length())));
        }

        @Json
        public record DataRequest(String message) {}
        @Json
        public record DataResponse(String result) {}
        @Json
        public record FormResponse(String name, String email) {}
        @Json
        public record UploadResponse(int fileCount, List<String> fileNames) {}
        @Json
        public record RawResponse(int length, String preview) {}
    }
    ```

===! ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/example/controller/DataController.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.controller

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.http.common.HttpMethod
    import ru.tinkoff.kora.http.common.annotation.*
    import ru.tinkoff.kora.http.common.form.FormMultipart
    import ru.tinkoff.kora.http.common.form.FormUrlEncoded
    import ru.tinkoff.kora.json.common.annotation.Json

    @Component
    @HttpController
    class DataController {

        // JSON request body (automatic with JsonModule)
        @HttpRoute(method = HttpMethod.POST, path = "/data/json")
        fun processJson(request: DataRequest): DataResponse {
            return DataResponse("Processed: ${request.message}")
        }

        // Form URL-encoded data
        @HttpRoute(method = HttpMethod.POST, path = "/data/form")
        fun processForm(form: FormUrlEncoded): FormResponse {
            val name = form.getString("name").orElse("Unknown")
            val email = form.getString("email").orElse("Unknown")

            return FormResponse(name, email)
        }

        // Multipart form data (file uploads)
        @HttpRoute(method = HttpMethod.POST, path = "/data/upload")
        fun processUpload(multipart: FormMultipart): UploadResponse {
            val files = multipart.getParts("files")

            return UploadResponse(
                files.size,
                files.map { it.name }
            )
        }

        // Raw request body
        @HttpRoute(method = HttpMethod.POST, path = "/data/raw")
        fun processRaw(body: String): RawResponse {
            return RawResponse(body.length, body.take(50))
        }
    }

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

### Request Body Processing Patterns

**JSON Processing** (`processJson`):
- **Automatic Deserialization**: Kora automatically converts JSON request body to `DataRequest` object
- **Type Safety**: Compile-time guarantees about the structure of incoming data
- **Validation**: Can be combined with Bean Validation for input validation
- **Performance**: Efficient parsing with Jackson/JsonModule

**Form Data Handling** (`processForm`):
- **Key-Value Extraction**: `FormUrlEncoded` provides `getString()` methods for field access
- **Optional Fields**: Use `orElse()` for default values when fields are missing
- **Multiple Values**: Forms can have multiple values for the same key
- **URL Decoding**: Automatic handling of URL-encoded characters

**File Upload Processing** (`processUpload`):
- **Multipart Parsing**: `FormMultipart` handles complex form data with file attachments
- **File Access**: `getParts()` returns list of `FormPart` objects containing file data
- **Metadata**: Each part has name, filename, content type, and data access methods
- **Memory Management**: Consider streaming large files instead of loading into memory

**Raw Body Access** (`processRaw`):
- **Direct String Access**: Request body as raw string for custom parsing
- **Content Type Agnostic**: Works with any content type
- **Size Limits**: Be aware of memory implications for large payloads
- **Custom Parsing**: Implement your own deserialization logic

### Best Practices for Request Body Handling

**Content Type Validation**: Always validate that the received content type matches your expectations
**Size Limits**: Implement reasonable limits to prevent DoS attacks
**Input Validation**: Validate and sanitize all input data
**Error Handling**: Provide meaningful error messages for malformed requests
**Performance**: Consider streaming for large files or data processing
**Security**: Implement proper file type validation and virus scanning for uploads

## Create Error Handling and Interceptors

Interceptors provide a powerful way to implement cross-cutting concerns in your HTTP server. They allow you to intercept, modify, or monitor requests and responses at a global level, separate from your business logic.

### Interceptor Pattern Overview

**What are Interceptors?**: Classes that implement `HttpServerInterceptor` and can process requests before they reach controllers and responses before they return to clients.

**Execution Order**: Interceptors form a chain where each interceptor can:
- Process the request before passing to the next interceptor
- Process the response after the next interceptor completes
- Handle exceptions thrown by downstream interceptors
- Short-circuit the request processing if needed

**Common Use Cases**:
- **Logging**: Request/response logging, performance monitoring
- **Authentication**: Token validation, user context setup
- **Authorization**: Permission checking, role-based access control
- **Error Handling**: Global exception processing, error response formatting
- **CORS**: Cross-origin resource sharing headers
- **Rate Limiting**: Request throttling and quota management
- **Caching**: Response caching, cache invalidation

### Global Error Handling

**ExceptionHandler Interceptor**: A special interceptor tagged with `@Tag(HttpServerModule.class)` that catches exceptions from the entire request processing chain.

**Exception Types**: Different exceptions can be mapped to appropriate HTTP status codes:
- `IllegalArgumentException` → 400 Bad Request
- `SecurityException` → 403 Forbidden
- `RuntimeException` → 500 Internal Server Error

**Response Formatting**: Centralized JSON error response creation using `JsonWriter` for consistent error formats.

Implement global error handling and request interceptors:

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/example/http/ExceptionHandler.java`:

    ```java
    package ru.tinkoff.kora.example.http;

    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.Context;
    import ru.tinkoff.kora.common.Tag;
    import ru.tinkoff.kora.http.server.common.*;
    import ru.tinkoff.kora.http.server.common.HttpServerModule;
    import ru.tinkoff.kora.http.common.body.HttpBody;
    import ru.tinkoff.kora.json.common.JsonWriter;
    import ru.tinkoff.kora.json.common.annotation.Json;

    import java.util.concurrent.CompletionStage;

    @Tag(HttpServerModule.class)
    @Component
    public final class ExceptionHandler implements HttpServerInterceptor {

        private final JsonWriter<ErrorResponse> errorJsonWriter;

        public ExceptionHandler(JsonWriter<ErrorResponse> errorJsonWriter) {
            this.errorJsonWriter = errorJsonWriter;
        }

        @Override
        public CompletionStage<HttpServerResponse> intercept(Context context, HttpServerRequest request, InterceptChain chain)
                throws Exception {
            return chain.process(context, request).exceptionally(throwable -> {
                // Handle different exception types
                if (throwable instanceof IllegalArgumentException) {
                    var body = HttpBody.json(errorJsonWriter.toByteArrayUnchecked(
                        new ErrorResponse("BAD_REQUEST", "Invalid request parameters")));
                    return HttpServerResponse.of(400, body);
                }

                if (throwable instanceof SecurityException) {
                    var body = HttpBody.json(errorJsonWriter.toByteArrayUnchecked(
                        new ErrorResponse("FORBIDDEN", "Access denied")));
                    return HttpServerResponse.of(403, body);
                }

                // Default error response
                var body = HttpBody.json(errorJsonWriter.toByteArrayUnchecked(
                    new ErrorResponse("INTERNAL_ERROR", "An unexpected error occurred")));
                return HttpServerResponse.of(500, body);
            });
        }
    }
    ```

===! ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/example/http/ExceptionHandler.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.http

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.Context
    import ru.tinkoff.kora.common.Tag
    import ru.tinkoff.kora.http.server.common.*
    import ru.tinkoff.kora.http.server.common.HttpServerModule
    import ru.tinkoff.kora.http.common.body.HttpBody
    import ru.tinkoff.kora.json.common.JsonWriter
    import ru.tinkoff.kora.json.common.annotation.Json

    @Tag(HttpServerModule::class)
    @Component
    class ExceptionHandler(
        private val errorJsonWriter: JsonWriter<ErrorResponse>
    ) : HttpServerInterceptor {

        override fun intercept(context: Context, request: HttpServerRequest, chain: InterceptChain): CompletionStage<HttpServerResponse> {
            return chain.process(context, request).exceptionally { throwable ->
                when (throwable) {
                    is IllegalArgumentException -> {
                        val body = HttpBody.json(errorJsonWriter.toByteArrayUnchecked(
                            ErrorResponse("BAD_REQUEST", "Invalid request parameters")))
                        HttpServerResponse.of(400, body)
                    }
                    is SecurityException -> {
                        val body = HttpBody.json(errorJsonWriter.toByteArrayUnchecked(
                            ErrorResponse("FORBIDDEN", "Access denied")))
                        HttpServerResponse.of(403, body)
                    }
                    else -> {
                        val body = HttpBody.json(errorJsonWriter.toByteArrayUnchecked(
                            ErrorResponse("INTERNAL_ERROR", "An unexpected error occurred")))
                        HttpServerResponse.of(500, body)
                    }
                }
            }
        }
    }

    @Json
    data class ErrorResponse(val code: String, val message: String)
    ```

### Interceptor Implementation Details

**ExceptionHandler Interceptor**:
- **Tagged with `@Tag(HttpServerModule.class)`**: This makes it a global interceptor that applies to all HTTP routes
- **Exceptionally Chain Processing**: Uses `chain.process().exceptionally()` to catch exceptions from all downstream processing
- **Type-Specific Error Handling**: Different exception types map to appropriate HTTP status codes
- **JSON Error Responses**: Uses `JsonWriter` to create consistent, structured error responses
- **Fallback Error Handling**: Default 500 error for unexpected exceptions

### Advanced Interceptor Patterns

Beyond the basic ExceptionHandler, Kora supports various advanced interceptor patterns for implementing cross-cutting concerns like authentication, authorization, CORS handling, rate limiting, and custom request/response processing.

**Authentication Interceptor**:

===! ":fontawesome-brands-java: `Java`"

```java
@Tag(HttpServerModule.class)
@Component
public class AuthInterceptor implements HttpServerInterceptor {
    @Override
    public CompletionStage<HttpServerResponse> intercept(Context context, HttpServerRequest request, InterceptChain chain) {
        String token = request.headers().getFirst("Authorization");
        if (token == null || !isValidToken(token)) {
            return CompletableFuture.completedFuture(HttpServerResponse.of(401, HttpBody.plaintext("Unauthorized")));
        }
        return chain.process(context, request);
    }
    
    private boolean isValidToken(String token) {
        // Token validation logic
        return true; // Simplified for example
    }
}
```

===! ":simple-kotlin: `Kotlin`"

```kotlin
@Tag(HttpServerModule::class)
@Component
class AuthInterceptor : HttpServerInterceptor {
    override fun intercept(context: Context, request: HttpServerRequest, chain: InterceptChain): CompletionStage<HttpServerResponse> {
        val token = request.headers().getFirst("Authorization")
        if (token == null || !isValidToken(token)) {
            return CompletableFuture.completedFuture(HttpServerResponse.of(401, HttpBody.plaintext("Unauthorized")))
        }
        return chain.process(context, request)
    }
    
    private fun isValidToken(token: String): Boolean {
        // Token validation logic
        return true // Simplified for example
    }
}
```

**CORS Interceptor**:

===! ":fontawesome-brands-java: `Java`"

```java
@Component
public class CorsInterceptor implements HttpServerInterceptor {
    @Override
    public CompletionStage<HttpServerResponse> intercept(Context context, HttpServerRequest request, InterceptChain chain) {
        if ("OPTIONS".equals(request.method())) {
            return CompletableFuture.completedFuture(HttpServerResponse.of(200, HttpHeaders.of(
                "Access-Control-Allow-Origin", "*",
                "Access-Control-Allow-Methods", "GET, POST, PUT, DELETE",
                "Access-Control-Allow-Headers", "Content-Type, Authorization"
            ), HttpBody.empty()));
        }
        return chain.process(context, request)
            .thenApply(response -> response.withHeader("Access-Control-Allow-Origin", "*"));
    }
}
```

===! ":simple-kotlin: `Kotlin`"

```kotlin
@Component
class CorsInterceptor : HttpServerInterceptor {
    override fun intercept(context: Context, request: HttpServerRequest, chain: InterceptChain): CompletionStage<HttpServerResponse> {
        if (request.method() == "OPTIONS") {
            return CompletableFuture.completedFuture(HttpServerResponse.of(200, HttpHeaders.of(
                "Access-Control-Allow-Origin" to "*",
                "Access-Control-Allow-Methods" to "GET, POST, PUT, DELETE",
                "Access-Control-Allow-Headers" to "Content-Type, Authorization"
            ), HttpBody.empty()))
        }
        return chain.process(context, request)
            .thenApply { response -> response.withHeader("Access-Control-Allow-Origin", "*") }
    }
}
```

## Create Controller-Only Interceptors

While global interceptors apply to all HTTP routes, controller-only interceptors can be applied to specific controllers or even individual routes. This provides fine-grained control over request processing for particular endpoints.

### When to Use Controller-Only Interceptors

**Selective Logging**: Apply logging only to sensitive or high-traffic endpoints
**Endpoint-Specific Validation**: Custom validation logic for specific controllers
**Performance Monitoring**: Monitor only certain business-critical operations
**Rate Limiting**: Apply rate limits to specific controllers without affecting others
**Custom Headers**: Add headers only for certain API versions or endpoints

### Implementation

Controller-only interceptors are regular `@Component` classes that implement `HttpServerInterceptor`. They are not tagged with `@Tag(HttpServerModule.class)`, which keeps them from being applied globally.

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/example/http/LoggingInterceptor.java`:

    This LoggingInterceptor is an example of a controller-only interceptor. Note that Kora provides comprehensive telemetry and monitoring capabilities out of the box for the HTTP server module, including built-in logging, metrics, and tracing. This custom interceptor is shown for educational purposes only.

    ```java
    package ru.tinkoff.kora.example.http;

    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.Context;
    import ru.tinkoff.kora.http.server.common.*;

    import java.util.concurrent.CompletionStage;

    // Controller-only interceptor example
    @Component
    public final class LoggingInterceptor implements HttpServerInterceptor {

        @Override
        public CompletionStage<HttpServerResponse> intercept(Context context, HttpServerRequest request, InterceptChain chain) {
            long startTime = System.nanoTime();

            return chain.process(context, request)
                .whenComplete((response, throwable) -> {
                    long duration = System.nanoTime() - startTime;
                    int statusCode = response != null ? response.statusCode() : 500;
                    System.out.printf("Request: %s %s -> %d (%d ms)%n",
                        request.method(),
                        request.path(),
                        statusCode,
                        duration / 1_000_000
                    );
                });
        }
    }
    ```

    Now apply this interceptor to a specific controller:

    ```java
    package ru.tinkoff.kora.example.controller;

    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.http.common.HttpMethod;
    import ru.tinkoff.kora.http.common.annotation.HttpController;
    import ru.tinkoff.kora.http.common.annotation.HttpRoute;
    import ru.tinkoff.kora.http.common.annotation.InterceptWith;
    import ru.tinkoff.kora.json.common.annotation.Json;
    import ru.tinkoff.kora.example.service.UserService;
    import ru.tinkoff.kora.example.dto.UserRequest;
    import ru.tinkoff.kora.example.dto.UserResponse;

    @Component
    @HttpController
    @InterceptWith(LoggingInterceptor.class)  // Apply interceptor to entire controller
    public final class UserController {

        private final UserService userService;

        public UserController(UserService userService) {
            this.userService = userService;
        }

        @HttpRoute(method = HttpMethod.GET, path = "/users")
        @Json
        public List<UserResponse> getUsers() {
            return userService.getUsers();
        }

        // This method will also be intercepted due to controller-level @InterceptWith
        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        public UserResponse createUser(UserRequest request) {
            return userService.createUser(request);
        }

        // Method-level interceptor (overrides controller-level if specified)
        @HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
        @InterceptWith(LoggingInterceptor.class)  // Explicit method-level interceptor
        // Note: All server-level, controller-level, and method-level interceptors will apply here
        @Json
        public UserResponse getUser(@Path String id) {
            return userService.getUser(id);
        }
    }
    ```

===! ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/example/http/LoggingInterceptor.kt`:

    This LoggingInterceptor is an example of a controller-only interceptor. Note that Kora provides comprehensive telemetry and monitoring capabilities out of the box for the HTTP server module, including built-in logging, metrics, and tracing. This custom interceptor is shown for educational purposes only.

    ```kotlin
    package ru.tinkoff.kora.example.http

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.Context
    import ru.tinkoff.kora.http.server.common.*

    // Controller-only interceptor example
    @Component
    class LoggingInterceptor : HttpServerInterceptor {

        override fun intercept(context: Context, request: HttpServerRequest, chain: InterceptChain): CompletionStage<HttpServerResponse> {
            val startTime = System.nanoTime()

            return chain.process(context, request)
                .whenComplete { response, throwable ->
                    val duration = System.nanoTime() - startTime
                    val statusCode = response?.statusCode() ?: 500
                    println("Request: ${request.method()} ${request.path()} -> $statusCode (${duration / 1_000_000} ms)")
                }
        }
    }
    ```

    Now apply this interceptor to a specific controller:

    ```kotlin
    package ru.tinkoff.kora.example.controller

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.http.common.HttpMethod
    import ru.tinkoff.kora.http.common.annotation.*
    import ru.tinkoff.kora.json.common.annotation.Json
    import ru.tinkoff.kora.example.service.UserService
    import ru.tinkoff.kora.example.dto.UserRequest
    import ru.tinkoff.kora.example.dto.UserResponse

    @Component
    @HttpController
    @InterceptWith(LoggingInterceptor::class)  // Apply interceptor to entire controller
    class UserController(
        private val userService: UserService
    ) {

        @HttpRoute(method = HttpMethod.GET, path = "/users")
        @Json
        fun getUsers(): List<UserResponse> {
            return userService.getUsers()
        }

        // This method will also be intercepted due to controller-level @InterceptWith
        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Json
        fun createUser(request: UserRequest): UserResponse {
            return userService.createUser(request)
        }

        // Method-level interceptor (overrides controller-level if specified)
        @HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
        @InterceptWith(LoggingInterceptor::class)  // Explicit method-level interceptor
        @Json
        fun getUser(@Path id: String): UserResponse {
            return userService.getUser(id)
        }
    }
    ```

### Controller-Only Interceptor Details

**@InterceptWith Annotation**:
- **Controller Level**: `@InterceptWith(LoggingInterceptor.class)` on the controller class applies the interceptor to all routes in that controller
- **Method Level**: `@InterceptWith(LoggingInterceptor.class)` on individual methods applies the interceptor only to that specific route
- **Multiple Interceptors**: You can apply multiple interceptors by using `@InterceptWith` multiple times or with an array

**Interceptor Scope**:
- **Controller-Only**: Without `@Tag(HttpServerModule.class)`, the interceptor is only applied where explicitly requested via `@InterceptWith`
- **Selective Application**: Choose which controllers or methods need the interceptor based on business requirements
- **Performance**: Only intercept relevant requests instead of all HTTP traffic

**Key Differences from Global Interceptors**:
- **No Global Tag**: Missing `@Tag(HttpServerModule.class)` prevents automatic application to all routes
- **Explicit Application**: Must use `@InterceptWith` to apply the interceptor
- **Fine-Grained Control**: Apply to specific controllers, methods, or groups of endpoints
- **Reduced Overhead**: Only processes requests for targeted endpoints

**Best Practices for Controller-Only Interceptors**:
- **Business Logic Focus**: Use for endpoint-specific concerns like audit logging or custom validation
- **Performance Critical**: Apply only where needed to minimize overhead
- **Testing**: Test interceptor behavior with specific controllers in isolation
- **Composition**: Combine controller-level and method-level interceptors as needed

### Best Practices for Interceptors

**Order Matters**: Interceptors execute in dependency injection order. Critical interceptors (auth, rate limiting) should come first.

**Performance**: Keep interceptor logic lightweight. Heavy operations should be in controllers or services.

**Error Handling**: Always handle exceptions within interceptors to prevent request processing interruption.

**Testing**: Unit test interceptors independently and integration test the interceptor chain.

**Configuration**: Make interceptor behavior configurable through application properties.

## Test HTTP Server Features

Build and test your HTTP server:

```bash
./gradlew build
./gradlew run
```

Test public API endpoints:

```bash
# Create a user (test POST with JSON body and headers - should return 201 Created)
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: test-123" \
  -H "User-Agent: curl-test" \
  -d '{"name": "John Doe", "email": "john@example.com"}'

# Test path parameters (get user by ID)
curl http://localhost:8080/users/1

# Test query parameters (get all users)
curl "http://localhost:8080/users?page=0&size=10&sort=name"

# Test custom response headers (update user)
curl -X PUT http://localhost:8080/users/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Name", "email": "updated@example.com"}' \
  -v

# Test DELETE endpoint
curl -X DELETE http://localhost:8080/users/1
```

Test private API monitoring endpoints:

```bash
# Health checks
curl http://localhost:8085/system/readiness
curl http://localhost:8085/system/liveness

# Metrics
curl http://localhost:8085/metrics

# Test graceful shutdown (in another terminal)
curl http://localhost:8080/users &
kill %1  # Send SIGTERM to trigger graceful shutdown
```

## Key Concepts Learned

### Configuration Parameters
- **Threading**: IO threads for network, blocking threads for work, virtual threads for Java 21+
- **Timeouts**: Socket read/write timeouts prevent hanging connections
- **Graceful Shutdown**: `shutdownWait` allows active requests to complete
- **Connection Pooling**: Keep-alive settings for performance

### Routing Features
- **Path Parameters**: Type-safe URL parameter extraction (`/users/{id}`)
- **Query Parameters**: Optional pagination, sorting, filtering
- **Headers & Cookies**: Request metadata, session management
- **Custom Responses**: Status codes, headers, content negotiation

### Custom HTTP Responses

Kora provides `HttpResponseEntity<T>` for complete control over HTTP responses:

```java
// Returns 200 OK by default
public UserResponse getUser(String id) {
    return userService.getUser(id);
}

// Returns custom status code and headers
public HttpResponseEntity<UserResponse> createUser(UserRequest request) {
    UserResponse user = userService.createUser(request);
    return HttpResponseEntity.of(201, HttpHeaders.of(), user); // 201 Created
}
```

**HttpServerResponseException for Error Handling:**

Kora provides `HttpServerResponseException` for throwing HTTP error responses:

```java
// Throw exception for error responses
public HttpResponseEntity<UserResponse> updateUser(String userId, UserRequest request) {
    Optional<UserResponse> updatedUser = userService.updateUser(userId, request);
    if (updatedUser.isEmpty()) {
        throw HttpServerResponseException.of(404, "User not found");
    }
    return HttpResponseEntity.of(200, HttpHeaders.of("X-Updated-At", Instant.now().toString()), updatedUser.get());
}
```

**Key Differences:**
- **Return Object Directly**: Automatic 200 OK response with JSON body
- **Return HttpResponseEntity**: Full control over status code, headers, and body
- **Throw HttpServerResponseException**: Clean error handling without conditional returns
- **Use Cases**: Custom status codes (201 Created, 204 No Content), custom headers, error responses

### Request Body Handling
- **JSON**: Automatic serialization with JsonModule
- **Form Data**: URL-encoded and multipart forms
- **File Uploads**: Multipart handling for file uploads
- **Raw Bodies**: Direct string/binary access when needed

### Production Features
- **Telemetry Integration**: Built-in logging, metrics, tracing
- **Error Handling**: Global exception handlers with custom responses
- **Request Interceptors**: Cross-cutting concerns like logging
- **Health Checks**: Kubernetes-ready readiness/liveness probes

### Performance Tuning
- **Thread Pools**: Optimize for your workload characteristics
- **Connection Settings**: Balance responsiveness vs resource usage
- **Monitoring**: Use metrics to identify bottlenecks
- **Virtual Threads**: Consider for high-concurrency workloads (Java 21+)

## Troubleshooting

### Server Won't Start
- Check port conflicts (8080, 8085)
- Verify configuration syntax in `application.conf`
- Ensure all required modules are included in Application interface

### Requests Hanging
- Check `socketReadTimeout` and `socketWriteTimeout` values
- Verify thread pool sizes aren't exhausted
- Monitor with `/metrics` endpoint for thread pool stats

### High Memory Usage
- Reduce `blockingThreads` if using virtual threads
- Adjust `shutdownWait` to prevent request accumulation
- Monitor garbage collection with JVM metrics

### Private API Not Accessible
- Verify `privateApiHttpPort` is different from `publicApiHttpPort`
- Check firewall rules allow access to private port
- Ensure infrastructure allows access to management endpoints

This guide covers building REST APIs with Kora's HTTP server. You've learned how to create controllers, handle requests and responses, work with JSON data, and implement basic routing and error handling. These fundamentals provide a solid foundation for building web services with Kora.
