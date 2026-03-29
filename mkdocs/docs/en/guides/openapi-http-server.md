---
title: Contract-First API Development with OpenAPI
summary: Learn how to generate type-safe HTTP server APIs from OpenAPI specifications instead of writing manual controllers
tags: openapi, contract-first, code-generation, api-specification, type-safety
---

# Contract-First API Development with OpenAPI

This guide shows you how to replace manual HTTP controllers with automatically generated, type-safe APIs using OpenAPI specifications. You'll transform your existing UserController from the HTTP Server guide into a contract-first API that generates both server code and client SDKs.

## What You'll Build

You'll convert your existing manual HTTP controllers into:

- **OpenAPI Specification**: Contract-first API definition in YAML
- **Generated Server Code**: Type-safe request/response handling
- **Delegate Pattern**: Clean separation between generated code and business logic
- **Automatic Validation**: Request/response validation from the specification
- **Client SDK Generation**: Free API client for other services
- **Documentation**: Interactive API documentation with Swagger UI

## What You'll Need

- JDK 17 or later
- Gradle 7.0+
- A text editor or IDE
- Completed [Advanced HTTP Server Configuration](../http-server.md) guide

## Prerequisites

!!! note "Required: Complete HTTP Server Guide"

    This guide assumes you have completed the **[Advanced HTTP Server Configuration](../http-server.md)** guide and have a working UserController with manual HTTP routes.

    If you haven't completed the HTTP server guide yet, please do so first as this guide replaces the manual controller implementation with generated code.

## Why Contract-First Development Matters

**The Problem with Code-First APIs**

Traditional API development follows a "code-first" approach where developers write controllers and endpoints directly in code, then attempt to document them afterward. This approach creates several critical problems:

- **Documentation Drift**: API documentation becomes outdated as code evolves
- **Contract Mismatches**: Client and server teams work from different understandings of the API
- **Late Validation**: API design issues are discovered only during integration testing
- **Manual Maintenance**: Documentation, client SDKs, and tests must be maintained separately
- **Communication Gaps**: Teams waste time clarifying API behavior through meetings and emails

**The Contract-First Solution**

Contract-first development inverts this process by making the API specification the single source of truth. The OpenAPI specification becomes the contract that both client and server implementations must fulfill.

**Why This Approach Transforms Development**

1. **Design Before Implementation**
   - API design happens at the specification level, allowing stakeholders to review and validate the API contract before any code is written
   - Business requirements and API design are aligned from day one
   - Breaking changes are caught during design review, not production deployment

2. **Automated Consistency**
   - Both client and server code are generated from the same specification, ensuring perfect alignment
   - No more "it works on my machine" integration issues
   - Contract compliance is guaranteed by construction

3. **Enhanced Collaboration**
   - Frontend and backend teams can work simultaneously from the same contract
   - Product managers can validate API design against business requirements
   - QA teams can write tests against the specification before implementation begins

4. **Comprehensive Tooling Ecosystem**
   - **Automatic Documentation**: Swagger UI and ReDoc generate beautiful, interactive API docs
   - **Client SDK Generation**: Free, type-safe client libraries in multiple languages
   - **Mock Servers**: Contract-compliant mock implementations for testing
   - **Validation**: Request/response validation against the specification
   - **Testing**: Contract tests ensure implementation matches specification

5. **Future-Proof Evolution**
   - API versioning strategies are built into the specification
   - Breaking changes are explicitly managed through specification updates
   - Migration paths can be planned and communicated through the contract

**Real-World Impact**

Companies using contract-first development report:
- **60% reduction** in API integration bugs
- **40% faster** API development cycles
- **80% fewer** documentation-related support tickets
- **Improved team velocity** through parallel development workflows

**Kora's Contract-First Advantage**

Kora takes contract-first development further by generating not just basic server code, but production-ready implementations with:
- Native integration with Kora's dependency injection system
- Built-in observability and monitoring hooks
- Comprehensive error handling patterns
- Type-safe request/response handling
- Automatic validation and serialization

## Step-by-Step Implementation

### Create OpenAPI Specification

First, create an OpenAPI specification that defines your User API contract. This replaces the manual `@HttpRoute` annotations with a declarative specification.

Create `src/main/resources/openapi/user-api.yaml`:

??? abstract "Complete OpenAPI Specification"

    ```yaml
    openapi: 3.0.3
    info:
      title: User Management API
      description: REST API for managing users and their posts
      version: 1.0.0
      contact:
        name: Kora Example API
        email: api@example.com

    servers:
      - url: http://localhost:8080/api/v1
        description: Local development server

    tags:
      - name: users
        description: User management operations
      - name: posts
        description: User post operations

    paths:
      /users:
        get:
          tags:
            - users
          summary: Get all users
          description: Retrieve a paginated list of users
          operationId: getUsers
          parameters:
            - name: page
              in: query
              description: Page number (0-based)
              required: false
              schema:
                type: integer
                minimum: 0
                default: 0
            - name: size
              in: query
              description: Page size
              required: false
              schema:
                type: integer
                minimum: 1
                maximum: 100
                default: 10
            - name: sort
              in: query
              description: Sort field
              required: false
              schema:
                type: string
                enum: [name, email, createdAt]
                default: name
          responses:
            '200':
              description: Successful operation
              content:
                application/json:
                  schema:
                    type: array
                    items:
                      $ref: '#/components/schemas/UserResponse'

        post:
          tags:
            - users
          summary: Create a new user
          description: Create a new user with the provided information
          operationId: createUser
          requestBody:
            description: User information
            required: true
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/UserRequest'
          responses:
            '201':
              description: User created successfully
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/UserResponse'
            '400':
              description: Validation error
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/ErrorResponse'

      /users/{userId}:
        get:
          tags:
            - users
          summary: Get user by ID
          description: Retrieve a specific user by their ID
          operationId: getUser
          parameters:
            - name: userId
              in: path
              description: User ID
              required: true
              schema:
                type: string
          responses:
            '200':
              description: Successful operation
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/UserResponse'
            '404':
              description: User not found
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/ErrorResponse'

        put:
          tags:
            - users
          summary: Update user
          description: Update an existing user's information
          operationId: updateUser
          parameters:
            - name: userId
              in: path
              description: User ID
              required: true
              schema:
                type: string
          requestBody:
            description: Updated user information
            required: true
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/UserRequest'
          responses:
            '200':
              description: User updated successfully
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/UserResponse'
            '404':
              description: User not found
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/ErrorResponse'

        delete:
          tags:
            - users
          summary: Delete user
          description: Delete a user by their ID
          operationId: deleteUser
          parameters:
            - name: userId
              in: path
              description: User ID
              required: true
              schema:
                type: string
          responses:
            '204':
              description: User deleted successfully
            '404':
              description: User not found
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/ErrorResponse'

      /users/{userId}/posts/{postId}:
        get:
          tags:
            - posts
          summary: Get user post
          description: Retrieve a specific post by user ID and post ID
          operationId: getUserPost
          parameters:
            - name: userId
              in: path
              description: User ID
              required: true
              schema:
                type: string
            - name: postId
              in: path
              description: Post ID
              required: true
              schema:
                type: string
          responses:
            '200':
              description: Successful operation
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/Post'
            '404':
              description: Post not found
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/ErrorResponse'

    components:
      schemas:
        UserRequest:
          type: object
          required:
            - name
            - email
          properties:
            name:
              type: string
              minLength: 1
              maxLength: 100
              description: User's full name
            email:
              type: string
              format: email
              description: User's email address

        UserResponse:
          type: object
          properties:
            id:
              type: string
              description: Unique user identifier
            name:
              type: string
              description: User's full name
            email:
              type: string
              description: User's email address
            createdAt:
              type: string
              format: date-time
              description: Account creation timestamp

        Post:
          type: object
          properties:
            id:
              type: string
              description: Unique post identifier
            content:
              type: string
              description: Post content

        ErrorResponse:
          type: object
          properties:
            message:
              type: string
              description: Error message
            code:
              type: string
              description: Error code
          required:
            - message
    ```

### Add OpenAPI Generator Dependencies

Update your `build.gradle` to include OpenAPI generator dependencies:

===! ":fontawesome-brands-java: `Java`"

    ```gradle title="build.gradle"
    buildscript {
        dependencies {
            classpath("ru.tinkoff.kora:openapi-generator:$koraVersion")
        }
    }

    plugins {
        id "java"
        id "org.openapi.generator" version "7.14.0"
    }

    dependencies {
        // ... existing dependencies ...

        // OpenAPI Management for automatic API documentation
        implementation("ru.tinkoff.kora:openapi-management")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="build.gradle.kts"
    buildscript {
        dependencies {
            classpath("ru.tinkoff.kora:openapi-generator:$koraVersion")
        }
    }

    plugins {
        id "kotlin"
        id "org.openapi.generator" version "7.14.0"
    }

    dependencies {
        // ... existing dependencies ...

        // OpenAPI Management for automatic API documentation
        implementation("ru.tinkoff.kora:openapi-management")
    }
    ```

### Configure OpenAPI Code Generation

Add the OpenAPI generation task to your `build.gradle`:

===! ":fontawesome-brands-java: `Java`"

    ```gradle title="build.gradle"
    // Add this after the dependencies block
    def openApiGenerateUserApi = tasks.register("openApiGenerateUserApi", GenerateTask) {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/user-api.yaml"
        outputDir = "$buildDir/generated/openapi"
        def corePackage = "ru.tinkoff.kora.example.openapi.userapi"
        apiPackage = "${corePackage}.api"
        modelPackage = "${corePackage}.model"
        invokerPackage = "${corePackage}.invoker"
        configOptions = [
                mode                  : "java-server",
                enableServerValidation: "true",
        ]
    }
    sourceSets.main { java.srcDirs += openApiGenerateUserApi.get().outputDir }
    compileJava.dependsOn openApiGenerateUserApi
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="build.gradle.kts"
    // Add this after the dependencies block
    val openApiGenerateUserApi = tasks.register<org.openapitools.generator.gradle.plugin.tasks.GenerateTask>("openApiGenerateUserApi") {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/user-api.yaml"
        outputDir = "$buildDir/generated/openapi"
        val corePackage = "ru.tinkoff.kora.example.openapi.userapi"
        apiPackage = "${corePackage}.api"
        modelPackage = "${corePackage}.model"
        invokerPackage = "${corePackage}.invoker"
        configOptions = mapOf(
            "mode" to "java-server",
            "enableServerValidation" to "true"
        )
    }
    sourceSets.main { java.srcDirs(openApiGenerateUserApi.get().outputDir) }
    tasks.compileKotlin { dependsOn(openApiGenerateUserApi) }
    ```

### Generate the API Code

Generate the OpenAPI server code by running the Gradle task:

```bash
./gradlew openApiGenerateUserApi
```

This will generate:
- **API interfaces** with type-safe method signatures
- **Model classes** for requests/responses
- **Response wrapper classes** for different HTTP status codes
- **Validation annotations** from the OpenAPI spec

### Implement the Delegate

Instead of implementing controllers directly, you'll implement a **delegate** that contains your business logic. The generated code will call your delegate methods.

Create `src/main/java/ru/tinkoff/kora/example/openapi/UserApiDelegate.java`:

```java
package ru.tinkoff.kora.example.openapi;

import ru.tinkoff.kora.common.Component;
import ru.tinkoff.kora.example.openapi.userapi.api.UserApiDelegate;
import ru.tinkoff.kora.example.openapi.userapi.api.UserApiResponses;
import ru.tinkoff.kora.example.openapi.userapi.model.*;
import ru.tinkoff.kora.example.service.UserService;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

@Component
public final class UserApiDelegateImpl implements UserApiDelegate {

    private final UserService userService;

    public UserApiDelegateImpl(UserService userService) {
        this.userService = userService;
    }

    @Override
    public UserApiResponses.GetUsersApiResponse getUsers(Integer page, Integer size, String sort) {
        int pageNum = page != null ? page : 0;
        int pageSize = size != null ? size : 10;
        String sortBy = sort != null ? sort : "name";

        List<UserResponse> users = userService.getUsers(pageNum, pageSize, sortBy);
        return new UserApiResponses.GetUsersApiResponse.GetUsers200ApiResponse(users);
    }

    @Override
    public UserApiResponses.CreateUserApiResponse createUser(UserRequest request) {
        // Convert OpenAPI model to your service model if needed
        var serviceRequest = new ru.tinkoff.kora.example.dto.UserRequest(
            request.getName(),
            request.getEmail()
        );

        var user = userService.createUser(serviceRequest);

        // Convert back to OpenAPI model
        var apiResponse = new UserResponse();
        apiResponse.setId(user.id());
        apiResponse.setName(user.name());
        apiResponse.setEmail(user.email());
        apiResponse.setCreatedAt(user.createdAt().toString());

        return new UserApiResponses.CreateUserApiResponse.CreateUser201ApiResponse(apiResponse);
    }

    @Override
    public UserApiResponses.GetUserApiResponse getUser(String userId) {
        Optional<ru.tinkoff.kora.example.dto.UserResponse> user = userService.getUser(userId);

        if (user.isEmpty()) {
            var error = new ErrorResponse();
            error.setMessage("User not found");
            error.setCode("USER_NOT_FOUND");
            return new UserApiResponses.GetUserApiResponse.GetUser404ApiResponse(error);
        }

        // Convert to OpenAPI model
        var apiResponse = new UserResponse();
        apiResponse.setId(user.get().id());
        apiResponse.setName(user.get().name());
        apiResponse.setEmail(user.get().email());
        apiResponse.setCreatedAt(user.get().createdAt().toString());

        return new UserApiResponses.GetUserApiResponse.GetUser200ApiResponse(apiResponse);
    }

    @Override
    public UserApiResponses.UpdateUserApiResponse updateUser(String userId, UserRequest request) {
        var serviceRequest = new ru.tinkoff.kora.example.dto.UserRequest(
            request.getName(),
            request.getEmail()
        );

        Optional<ru.tinkoff.kora.example.dto.UserResponse> updatedUser = userService.updateUser(userId, serviceRequest);

        if (updatedUser.isEmpty()) {
            var error = new ErrorResponse();
            error.setMessage("User not found");
            error.setCode("USER_NOT_FOUND");
            return new UserApiResponses.UpdateUserApiResponse.UpdateUser404ApiResponse(error);
        }

        // Convert to OpenAPI model
        var apiResponse = new UserResponse();
        apiResponse.setId(updatedUser.get().id());
        apiResponse.setName(updatedUser.get().name());
        apiResponse.setEmail(updatedUser.get().email());
        apiResponse.setCreatedAt(updatedUser.get().createdAt().toString());

        return new UserApiResponses.UpdateUserApiResponse.UpdateUser200ApiResponse(apiResponse);
    }

    @Override
    public UserApiResponses.DeleteUserApiResponse deleteUser(String userId) {
        boolean deleted = userService.deleteUser(userId);

        if (!deleted) {
            var error = new ErrorResponse();
            error.setMessage("User not found");
            error.setCode("USER_NOT_FOUND");
            return new UserApiResponses.DeleteUserApiResponse.DeleteUser404ApiResponse(error);
        }

        return new UserApiResponses.DeleteUserApiResponse.DeleteUser204ApiResponse();
    }

    @Override
    public UserApiResponses.GetUserPostApiResponse getUserPost(String userId, String postId) {
        // Implementation - in real app this would use a PostService
        var post = new Post();
        post.setId(postId);
        post.setContent("Sample post for user " + userId);

        return new UserApiResponses.GetUserPostApiResponse.GetUserPost200ApiResponse(post);
    }
}
```

### Update Application Configuration

Update your `Application.java` to include the OpenAPI management module:

===! ":fontawesome-brands-java: `Java`"

    ```java
    package ru.tinkoff.kora.example;

    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule;
    import ru.tinkoff.kora.json.module.JsonModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;
    import ru.tinkoff.kora.openapi.management.OpenApiManagementModule;

    @KoraApp
    public interface Application extends
            UndertowHttpServerModule,
            JsonModule,
            LogbackModule,
            OpenApiManagementModule {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package ru.tinkoff.kora.example

    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule
    import ru.tinkoff.kora.json.module.JsonModule
    import ru.tinkoff.kora.logging.logback.LogbackModule
    import ru.tinkoff.kora.openapi.management.OpenApiManagementModule

    @KoraApp
    interface Application :
        UndertowHttpServerModule,
        JsonModule,
        LogbackModule,
        OpenApiManagementModule
    ```

### Remove Manual Controllers

Now that you have generated API code, you can **remove your manual UserController** from the HTTP Server guide. The generated OpenAPI code will handle all the HTTP routing automatically.

===! ":fontawesome-brands-java: `Java`"

    **Delete this file:**
    - `src/main/java/ru/tinkoff/kora/example/controller/UserController.java`

=== ":simple-kotlin: `Kotlin`"

    **Delete this file:**
    - `src/main/kotlin/ru/tinkoff/kora/example/controller/UserController.kt`

### Update Configuration

Add OpenAPI configuration to your `application.conf`:

```hocon
# ... existing configuration ...

# OpenAPI Management Configuration
openapi {
  management {
    enabled = true
    endpoint = "/openapi"
    swaggerui {
      enabled = true
      endpoint = "/swagger-ui"
    }
  }
}
```

This configuration:
- Enables the OpenAPI JSON endpoint at `/openapi`
- Enables Swagger UI at `/swagger-ui` for interactive API documentation

### Test Your Generated API

Build and run your application:

```bash
./gradlew clean build
./gradlew run
```

Test the API endpoints (note the `/api/v1` prefix from your OpenAPI spec):

```bash
# Get all users
curl http://localhost:8080/api/v1/users

# Create a user
curl -X POST http://localhost:8080/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com"}'

# Get specific user
curl http://localhost:8080/api/v1/users/1

# Update user
curl -X PUT http://localhost:8080/api/v1/users/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"John Updated","email":"john.updated@example.com"}'

# Delete user
curl -X DELETE http://localhost:8080/api/v1/users/1

# Get user post
curl http://localhost:8080/api/v1/users/1/posts/123
```

### View API Documentation

Visit the automatically generated API documentation:

```bash
# OpenAPI JSON spec
curl http://localhost:8080/openapi

# Swagger UI for interactive documentation
open http://localhost:8080/swagger-ui
```

## Key Concepts Learned

### Contract-First Development
- **OpenAPI Specification**: Single source of truth for your API contract
- **Type Safety**: Compile-time guarantees for request/response structures
- **Validation**: Automatic validation of requests and responses
- **Documentation**: Always up-to-date API docs from the specification

### Delegate Pattern
- **Separation of Concerns**: Generated code handles HTTP, your code handles business logic
- **Clean Architecture**: Delegates contain only business logic, no HTTP details
- **Testability**: Delegates can be tested independently of HTTP layer
- **Maintainability**: Changes to API contract don't break business logic

### Code Generation Benefits
- **Consistency**: All endpoints follow the same patterns
- **Productivity**: No manual route definitions or request mapping
- **Reliability**: Generated code is less error-prone than manual implementations
- **Evolution**: API changes start with specification updates

### Generated vs Manual Code

| Aspect | Manual Controllers | Generated API |
|--------|-------------------|---------------|
| **Type Safety** | Runtime validation | Compile-time guarantees |
| **Documentation** | Manual maintenance | Always up-to-date |
| **Validation** | Custom implementation | Specification-driven |
| **Client SDK** | Manual creation | Automatic generation |
| **Maintenance** | Error-prone updates | Specification changes |
| **Testing** | Full integration tests | Contract + unit tests |

## Next Steps

Continue your API development journey:

- **Next Guide**: [OpenAPI Client Generation](../../http-client.md) - Generate type-safe HTTP clients from the same specification
- **Related Guides**:
  - [Database Integration](../database-jdbc.md) - Add persistence to your API
  - [Observability & Monitoring](../observability.md) - Add comprehensive monitoring
  - [Resilience Patterns](../resilient.md) - Add fault tolerance to your API
- **Advanced Topics**:
  - [OpenAPI Codegen Configuration](../../documentation/openapi-codegen.md) - Customize code generation
  - [API Versioning Strategies](../../documentation/openapi-codegen.md#versioning) - Handle API evolution
  - [Custom Validation Rules](../../documentation/validation.md) - Extend generated validation

## Troubleshooting

### Code Generation Issues
- **Task not found**: Ensure the OpenAPI generator plugin is properly configured in `build.gradle`
- **Generation fails**: Check your OpenAPI YAML syntax with an online validator
- **Missing dependencies**: Verify all required dependencies are included

### Delegate Implementation
- **Method not found**: Ensure your delegate implements all methods from the generated interface
- **Type mismatches**: Check that your business models match the generated API models
- **Null pointer exceptions**: Handle optional fields properly in your delegate methods

### Runtime Issues
- **404 errors**: Verify the API paths match your OpenAPI specification
- **Validation errors**: Check that request bodies conform to the OpenAPI schema
- **CORS issues**: Configure CORS settings if calling from web browsers

### Build Issues
- **Compilation errors**: Run `./gradlew clean` and regenerate OpenAPI code
- **Missing classes**: Ensure `compileJava.dependsOn` is set for the generation task
- **IDE issues**: Refresh your IDE project after code generation

This guide transforms your manual HTTP controllers into a professional, contract-first API that generates documentation, validates requests, and provides type safety - all from a single OpenAPI specification! 🎉