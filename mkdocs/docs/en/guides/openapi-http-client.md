---
title: Contract-First HTTP Client Development with OpenAPI
summary: Learn how to generate type-safe HTTP clients from OpenAPI specifications instead of writing manual clients
tags: openapi, contract-first, code-generation, http-client, type-safety
---

# Contract-First HTTP Client Development with OpenAPI

This guide shows you how to replace manual HTTP clients with automatically generated, type-safe clients using OpenAPI specifications. You'll transform your existing manual HTTP client from the HTTP Client guide into a contract-first client that generates both client code and ensures API contract compliance.

## What You'll Build

You'll convert your existing manual HTTP clients into:

- **OpenAPI Specification**: Contract-first API definition shared with server
- **Generated Client Code**: Type-safe request/response handling
- **Automatic Validation**: Request/response validation from the specification
- **Client SDK Generation**: Free API client for other services
- **Contract Testing**: Ensure client and server contracts match

## What You'll Need

- JDK 17 or later
- Gradle 7.0+
- A text editor or IDE
- Completed [HTTP Client Integration](../http-client.md) guide

## Prerequisites

!!! note "Required: Complete HTTP Client Guide"

    This guide assumes you have completed the **[HTTP Client Integration](../http-client.md)** guide and have a working manual HTTP client implementation.

    If you haven't completed the HTTP client guide yet, please do so first as this guide replaces the manual client implementation with generated code.

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

Kora takes contract-first development further by generating not just basic client code, but production-ready implementations with:
- Native integration with Kora's dependency injection system
- Built-in observability and monitoring hooks
- Comprehensive error handling patterns
- Type-safe request/response handling
- Automatic retry and circuit breaker integration

## Step-by-Step Implementation

### Use Existing OpenAPI Specification

Instead of creating a new specification, you'll use the same OpenAPI specification from the HTTP Server guide. This ensures your client and server contracts are perfectly aligned and demonstrates the power of contract-first development in action.

Copy the `src/main/resources/openapi/user-api.yaml` file from your HTTP Server project, or create it if it doesn't exist:

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

Update your `build.gradle` to include OpenAPI generator dependencies for client generation:

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

        // HTTP Client dependencies (from HTTP Client guide)
        implementation("ru.tinkoff.kora:http-client-common")
        implementation("ru.tinkoff.kora:http-client-jdk")
        implementation("ru.tinkoff.kora:json-module")
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

        // HTTP Client dependencies (from HTTP Client guide)
        implementation("ru.tinkoff.kora:http-client-common")
        implementation("ru.tinkoff.kora:http-client-jdk")
        implementation("ru.tinkoff.kora:json-module")
    }
    ```

### Configure OpenAPI Client Code Generation

Add the OpenAPI generation task to your `build.gradle` for client code generation:

===! ":fontawesome-brands-java: `Java`"

    ```gradle title="build.gradle"
    // Add this after the dependencies block
    def openApiGenerateUserApiClient = tasks.register("openApiGenerateUserApiClient", GenerateTask) {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/user-api.yaml"
        outputDir = "$buildDir/generated/openapi"
        def corePackage = "ru.tinkoff.kora.example.openapi.userapi"
        apiPackage = "${corePackage}.api"
        modelPackage = "${corePackage}.model"
        invokerPackage = "${corePackage}.invoker"
        configOptions = [
                mode: "java-client",
        ]
    }
    sourceSets.main { java.srcDirs += openApiGenerateUserApiClient.get().outputDir }
    compileJava.dependsOn openApiGenerateUserApiClient
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="build.gradle.kts"
    // Add this after the dependencies block
    val openApiGenerateUserApiClient = tasks.register<org.openapitools.generator.gradle.plugin.tasks.GenerateTask>("openApiGenerateUserApiClient") {
        generatorName = "kora"
        group = "openapi tools"
        inputSpec = "$projectDir/src/main/resources/openapi/user-api.yaml"
        outputDir = "$buildDir/generated/openapi"
        val corePackage = "ru.tinkoff.kora.example.openapi.userapi"
        apiPackage = "${corePackage}.api"
        modelPackage = "${corePackage}.model"
        invokerPackage = "${corePackage}.invoker"
        configOptions = mapOf(
            "mode" to "java-client"
        )
    }
    sourceSets.main { java.srcDirs(openApiGenerateUserApiClient.get().outputDir) }
    tasks.compileKotlin { dependsOn(openApiGenerateUserApiClient) }
    ```

### Generate the Client Code

Generate the OpenAPI client code by running the Gradle task:

```bash
./gradlew openApiGenerateUserApiClient
```

This will generate:
- **API interfaces** with type-safe method signatures for client calls
- **Model classes** for requests/responses (shared with server)
- **Client implementation** that handles HTTP communication
- **Validation annotations** from the OpenAPI spec

### Implement Client Usage

Instead of implementing manual HTTP clients, you'll use the generated client with dependency injection. Create a service that uses the generated client:

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/example/client/UserApiClientService.java`:

    ```java
    package ru.tinkoff.kora.example.client;

    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.example.openapi.userapi.api.UserApi;
    import ru.tinkoff.kora.example.openapi.userapi.model.*;

    import java.util.List;
    import java.util.concurrent.ExecutionException;

    @Component
    public final class UserApiClientService {

        private final UserApi userApi;

        public UserApiClientService(UserApi userApi) {
            this.userApi = userApi;
        }

        public List<UserResponse> getAllUsers() {
            return userApi.getUsers(null, null, null);
        }

        public List<UserResponse> getUsers(Integer page, Integer size, String sort) {
            return userApi.getUsers(page, size, sort);
        }

        public UserResponse createUser(String name, String email) {
            var request = new UserRequest();
            request.setName(name);
            request.setEmail(email);
            return userApi.createUser(request);
        }

        public UserResponse getUser(String userId) {
            return userApi.getUser(userId);
        }

        public UserResponse updateUser(String userId, String name, String email) {
            var request = new UserRequest();
            request.setName(name);
            request.setEmail(email);
            return userApi.updateUser(userId, request);
        }

        public void deleteUser(String userId) {
            userApi.deleteUser(userId);
        }

        public Post getUserPost(String userId, String postId) {
            return userApi.getUserPost(userId, postId);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/example/client/UserApiClientService.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.client

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.example.openapi.userapi.api.UserApi
    import ru.tinkoff.kora.example.openapi.userapi.model.*

    @Component
    class UserApiClientService(
        private val userApi: UserApi
    ) {

        fun getAllUsers(): List<UserResponse> {
            return userApi.getUsers(null, null, null)
        }

        fun getUsers(page: Int?, size: Int?, sort: String?): List<UserResponse> {
            return userApi.getUsers(page, size, sort)
        }

        fun createUser(name: String, email: String): UserResponse {
            val request = UserRequest()
            request.name = name
            request.email = email
            return userApi.createUser(request)
        }

        fun getUser(userId: String): UserResponse {
            return userApi.getUser(userId)
        }

        fun updateUser(userId: String, name: String, email: String): UserResponse {
            val request = UserRequest()
            request.name = name
            request.email = email
            return userApi.updateUser(userId, request)
        }

        fun deleteUser(userId: String) {
            userApi.deleteUser(userId)
        }

        fun getUserPost(userId: String, postId: String): Post {
            return userApi.getUserPost(userId, postId)
        }
    }
    ```

### Remove Manual Client Implementation

Now that you have generated client code, you can **remove your manual HTTP client implementations** from the HTTP Client guide. The generated OpenAPI client will handle all the HTTP communication automatically.

===! ":fontawesome-brands-java: `Java`"

    **Delete these files:**
    - `src/main/java/ru/tinkoff/kora/example/client/UserClient.java`
    - `src/main/java/ru/tinkoff/kora/example/client/UserServiceClient.java`

=== ":simple-kotlin: `Kotlin`"

    **Delete these files:**
    - `src/main/kotlin/ru/tinkoff/kora/example/client/UserClient.kt`
    - `src/main/kotlin/ru/tinkoff/kora/example/client/UserServiceClient.kt`

### Update Configuration

Add HTTP client configuration to your `application.conf`:

```hocon
# ... existing configuration ...

# HTTP Client Configuration
httpClient {
  UserApi {
    url = ${USER_API_URL}
    timeout {
      connect = 10s
      read = 30s
    }
  }
}
```

### Test Your Generated Client

Testing your generated OpenAPI client is crucial to ensure it works correctly with the API contract. However, testing against a real server introduces several challenges that can make development slower and less reliable. Instead, we'll use **MockServer** - a powerful tool for creating isolated, contract-compliant API mocks that enable fast, reliable testing.

## Why MockServer? The Problem with Real Server Testing

When you first start building API clients, it's tempting to test against a real server. However, this approach has significant drawbacks:

- **Dependency on Server Availability**: Your tests fail if the server is down, being deployed, or has data issues
- **Slow Test Execution**: Network calls add latency, making test suites slow to run
- **Flaky Tests**: Network timeouts, server load, or connectivity issues cause intermittent failures
- **Shared State Issues**: Tests interfere with each other through shared database state
- **Limited Error Scenario Testing**: Hard to test error conditions without breaking the real server
- **Development Workflow Bottlenecks**: Client and server teams can't work independently

## What is MockServer?

**MockServer** is an open-source tool that creates realistic HTTP mock servers for testing purposes. It allows you to:

- **Simulate any HTTP API** with complete control over requests and responses
- **Define expectations** for specific requests and their corresponding responses
- **Run in isolated containers** using Testcontainers for clean test environments
- **Support advanced features** like request matching, response templating, and callback functions

In the context of contract-first development, MockServer becomes your **API contract enforcer** - it ensures your client code correctly implements the OpenAPI specification without needing a running server implementation.

## Why This Testing Approach is Superior

MockServer-based testing transforms how you develop and test API clients:

### **Speed and Reliability**
- **Sub-millisecond responses** instead of network round-trips
- **Zero external dependencies** - tests run anywhere, anytime
- **Predictable execution** - no more flaky network-related failures
- **Parallel test execution** without resource conflicts

### **Contract-First Validation**
- **Specification Compliance**: Test that your client correctly implements the OpenAPI contract
- **Request Validation**: Ensure requests match the API specification exactly
- **Response Handling**: Verify your client processes all defined response types
- **Error Scenarios**: Test error conditions safely without affecting real systems

### **Development Workflow Benefits**
- **Parallel Development**: Client and server teams work independently from the same contract
- **Fast Feedback**: Immediate test results during development
- **CI/CD Optimization**: Tests run consistently in any environment
- **Debugging Simplicity**: Full control over request/response cycles for troubleshooting

### **Comprehensive Testing Coverage**
- **Success Paths**: Test all happy-path scenarios
- **Error Conditions**: Simulate 4xx/5xx responses, timeouts, and network errors
- **Edge Cases**: Test boundary conditions and unusual response formats
- **Performance**: Validate client behavior under various response times

### **Professional Testing Practices**
- **Isolation**: Each test runs in its own container with clean state
- **Reproducibility**: Same test results across different environments
- **Maintainability**: Tests focus on client logic, not server implementation details
- **Documentation**: Tests serve as living documentation of expected API behavior

## MockServer in Contract-First Development

MockServer perfectly complements the contract-first approach:

1. **Specification as Source of Truth**: Your OpenAPI spec defines the contract
2. **MockServer as Contract Interpreter**: Translates the spec into runnable mock endpoints
3. **Client as Contract Implementer**: Your generated client must work with the mock
4. **Tests as Contract Validators**: Ensure client and mock (spec) interactions work correctly

This creates a **virtuous cycle** where:
- The specification drives both client generation and test mocking
- Tests validate that generated clients work with the specification
- Any specification changes are immediately reflected in tests
- Client updates are verified against the contract before integration

## Setting Up MockServer for Testing

Instead of testing against a running server, we'll use MockServer to create proper integration tests. Add Testcontainers and MockServer dependencies:

===! ":fontawesome-brands-java: `Java`"

    ```gradle title="build.gradle"
    dependencies {
        // ... existing dependencies ...

        testImplementation("org.testcontainers:mockserver:1.19.8")
        testImplementation("org.testcontainers:junit-jupiter:1.19.8")
        testImplementation("org.mock-server:mockserver-client-java:5.15.0")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="build.gradle.kts"
    dependencies {
        // ... existing dependencies ...

        testImplementation("org.testcontainers:mockserver:1.19.8")
        testImplementation("org.testcontainers:junit-jupiter:1.19.8")
        testImplementation("org.mock-server:mockserver-client-java:5.15.0")
    }
    ```

Create a proper integration test using MockServer:

===! ":fontawesome-brands-java: `Java`"

    Create `src/test/java/ru/tinkoff/kora/example/client/UserApiClientTest.java`:

    ```java
    package ru.tinkoff.kora.example.client;

    import org.junit.jupiter.api.AfterAll;
    import org.junit.jupiter.api.BeforeAll;
    import org.junit.jupiter.api.Test;
    import org.mockserver.client.MockServerClient;
    import org.mockserver.model.HttpRequest;
    import org.mockserver.model.HttpResponse;
    import org.testcontainers.containers.MockServerContainer;
    import org.testcontainers.junit.jupiter.Container;
    import org.testcontainers.junit.jupiter.Testcontainers;
    import org.testcontainers.utility.DockerImageName;
    import ru.tinkoff.kora.example.openapi.userapi.model.UserResponse;
    import ru.tinkoff.kora.test.KoraAppTest;
    import ru.tinkoff.kora.test.KoraConfigModifier;

    import java.util.List;
    import java.util.concurrent.ExecutionException;

    import static org.junit.jupiter.api.Assertions.*;

    @Testcontainers
    @KoraAppTest(Application.class)
    public class UserApiClientTest {

        @Container
        private static final MockServerContainer mockServer = new MockServerContainer(
            DockerImageName.parse("mockserver/mockserver:5.15.0")
        );

        private static MockServerClient mockServerClient;

        @BeforeAll
        static void setup() {
            mockServerClient = new MockServerClient(mockServer.getHost(), mockServer.getServerPort());
        }

        @AfterAll
        static void teardown() {
            if (mockServerClient != null) {
                mockServerClient.close();
            }
        }

        @Test
        void testCreateUser(UserApiClientService userApiClientService) {
            // Mock the create user response
            mockServerClient
                .when(HttpRequest.request()
                    .withMethod("POST")
                    .withPath("/api/v1/users")
                    .withBody("{\"name\":\"John Doe\",\"email\":\"john@example.com\"}"))
                .respond(HttpResponse.response()
                    .withStatusCode(201)
                    .withHeader("Content-Type", "application/json")
                    .withBody("""
                        {
                          "id": "123",
                          "name": "John Doe",
                          "email": "john@example.com",
                          "createdAt": "2024-01-01T10:00:00Z"
                        }
                        """));

            // Test the client
            UserResponse result = userApiClientService.createUser("John Doe", "john@example.com");

            assertNotNull(result);
            assertEquals("123", result.getId());
            assertEquals("John Doe", result.getName());
            assertEquals("john@example.com", result.getEmail());
        }

        @Test
        void testGetUsers(UserApiClientService userApiClientService) {
            // Mock the get users response
            mockServerClient
                .when(HttpRequest.request()
                    .withMethod("GET")
                    .withPath("/api/v1/users"))
                .respond(HttpResponse.response()
                    .withStatusCode(200)
                    .withHeader("Content-Type", "application/json")
                    .withBody("""
                        [
                          {
                            "id": "123",
                            "name": "John Doe",
                            "email": "john@example.com",
                            "createdAt": "2024-01-01T10:00:00Z"
                          }
                        ]
                        """));

            // Test the client
            List<UserResponse> result = userApiClientService.getAllUsers();

            assertNotNull(result);
            assertEquals(1, result.size());
            assertEquals("123", result.get(0).getId());
            assertEquals("John Doe", result.get(0).getName());
        }

        @Test
        void testGetUser(UserApiClientService userApiClientService) {
            // Mock the get user response
            mockServerClient
                .when(HttpRequest.request()
                    .withMethod("GET")
                    .withPath("/api/v1/users/123"))
                .respond(HttpResponse.response()
                    .withStatusCode(200)
                    .withHeader("Content-Type", "application/json")
                    .withBody("""
                        {
                          "id": "123",
                          "name": "John Doe",
                          "email": "john@example.com",
                          "createdAt": "2024-01-01T10:00:00Z"
                        }
                        """));

            // Test the client
            UserResponse result = userApiClientService.getUser("123");

            assertNotNull(result);
            assertEquals("123", result.getId());
            assertEquals("John Doe", result.getName());
        }

        @Test
        void testUpdateUser(UserApiClientService userApiClientService) {
            // Mock the update user response
            mockServerClient
                .when(HttpRequest.request()
                    .withMethod("PUT")
                    .withPath("/api/v1/users/123")
                    .withBody("{\"name\":\"John Updated\",\"email\":\"john.updated@example.com\"}"))
                .respond(HttpResponse.response()
                    .withStatusCode(200)
                    .withHeader("Content-Type", "application/json")
                    .withBody("""
                        {
                          "id": "123",
                          "name": "John Updated",
                          "email": "john.updated@example.com",
                          "createdAt": "2024-01-01T10:00:00Z"
                        }
                        """));

            // Test the client
            UserResponse result = userApiClientService.updateUser("123", "John Updated", "john.updated@example.com");

            assertNotNull(result);
            assertEquals("123", result.getId());
            assertEquals("John Updated", result.getName());
            assertEquals("john.updated@example.com", result.getEmail());
        }

        @Test
        void testDeleteUser(UserApiClientService userApiClientService) {
            // Mock the delete user response
            mockServerClient
                .when(HttpRequest.request()
                    .withMethod("DELETE")
                    .withPath("/api/v1/users/123"))
                .respond(HttpResponse.response()
                    .withStatusCode(204));

            // Test the client - should not throw exception
            userApiClientService.deleteUser("123");
        }

        @KoraConfigModifier
        static KoraConfigModifier configModifier() {
            return config -> config
                .withSystemProperty("USER_API_URL", "http://localhost:" + mockServer.getServerPort());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/test/kotlin/ru/tinkoff/kora/example/client/UserApiClientTest.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.client

    import org.junit.jupiter.api.AfterAll
    import org.junit.jupiter.api.BeforeAll
    import org.junit.jupiter.api.Test
    import org.mockserver.client.MockServerClient
    import org.mockserver.model.HttpRequest
    import org.mockserver.model.HttpResponse
    import org.testcontainers.containers.MockServerContainer
    import org.testcontainers.junit.jupiter.Container
    import org.testcontainers.junit.jupiter.Testcontainers
    import org.testcontainers.utility.DockerImageName
    import ru.tinkoff.kora.example.openapi.userapi.model.UserResponse
    import ru.tinkoff.kora.test.KoraAppTest
    import ru.tinkoff.kora.test.KoraConfigModifier
    import kotlin.test.assertEquals
    import kotlin.test.assertNotNull

    @Testcontainers
    @KoraAppTest(Application::class)
    class UserApiClientTest {

        companion object {
            @Container
            private val mockServer = MockServerContainer(
                DockerImageName.parse("mockserver/mockserver:5.15.0")
            )

            private lateinit var mockServerClient: MockServerClient

            @BeforeAll
            @JvmStatic
            fun setup() {
                mockServerClient = MockServerClient(mockServer.host, mockServer.serverPort)
            }

            @AfterAll
            @JvmStatic
            fun teardown() {
                mockServerClient.close()
            }
        }

        @Test
        fun testCreateUser(userApiClientService: UserApiClientService) {
            // Mock the create user response
            mockServerClient
                .`when`(HttpRequest.request()
                    .withMethod("POST")
                    .withPath("/api/v1/users")
                    .withBody("{\"name\":\"John Doe\",\"email\":\"john@example.com\"}"))
                .respond(HttpResponse.response()
                    .withStatusCode(201)
                    .withHeader("Content-Type", "application/json")
                    .withBody("""
                        {
                          "id": "123",
                          "name": "John Doe",
                          "email": "john@example.com",
                          "createdAt": "2024-01-01T10:00:00Z"
                        }
                        """))

            // Test the client
            val result = userApiClientService.createUser("John Doe", "john@example.com")

            assertNotNull(result)
            assertEquals("123", result.id)
            assertEquals("John Doe", result.name)
            assertEquals("john@example.com", result.email)
        }

        @Test
        fun testGetUsers(userApiClientService: UserApiClientService) {
            // Mock the get users response
            mockServerClient
                .`when`(HttpRequest.request()
                    .withMethod("GET")
                    .withPath("/api/v1/users"))
                .respond(HttpResponse.response()
                    .withStatusCode(200)
                    .withHeader("Content-Type", "application/json")
                    .withBody("""
                        [
                          {
                            "id": "123",
                            "name": "John Doe",
                            "email": "john@example.com",
                            "createdAt": "2024-01-01T10:00:00Z"
                          }
                        ]
                        """))

            // Test the client
            val result = userApiClientService.getAllUsers()

            assertNotNull(result)
            assertEquals(1, result.size)
            assertEquals("123", result[0].id)
            assertEquals("John Doe", result[0].name)
        }

        @Test
        fun testGetUser(userApiClientService: UserApiClientService) {
            // Mock the get user response
            mockServerClient
                .`when`(HttpRequest.request()
                    .withMethod("GET")
                    .withPath("/api/v1/users/123"))
                .respond(HttpResponse.response()
                    .withStatusCode(200)
                    .withHeader("Content-Type", "application/json")
                    .withBody("""
                        {
                          "id": "123",
                          "name": "John Doe",
                          "email": "john@example.com",
                          "createdAt": "2024-01-01T10:00:00Z"
                        }
                        """))

            // Test the client
            val result = userApiClientService.getUser("123")

            assertNotNull(result)
            assertEquals("123", result.id)
            assertEquals("John Doe", result.name)
        }

        @Test
        fun testUpdateUser(userApiClientService: UserApiClientService) {
            // Mock the update user response
            mockServerClient
                .`when`(HttpRequest.request()
                    .withMethod("PUT")
                    .withPath("/api/v1/users/123")
                    .withBody("{\"name\":\"John Updated\",\"email\":\"john.updated@example.com\"}"))
                .respond(HttpResponse.response()
                    .withStatusCode(200)
                    .withHeader("Content-Type", "application/json")
                    .withBody("""
                        {
                          "id": "123",
                          "name": "John Updated",
                          "email": "john.updated@example.com",
                          "createdAt": "2024-01-01T10:00:00Z"
                        }
                        """))

            // Test the client
            val result = userApiClientService.updateUser("123", "John Updated", "john.updated@example.com")

            assertNotNull(result)
            assertEquals("123", result.id)
            assertEquals("John Updated", result.name)
            assertEquals("john.updated@example.com", result.email)
        }

        @Test
        fun testDeleteUser(userApiClientService: UserApiClientService) {
            // Mock the delete user response
            mockServerClient
                .`when`(HttpRequest.request()
                    .withMethod("DELETE")
                    .withPath("/api/v1/users/123"))
                .respond(HttpResponse.response()
                    .withStatusCode(204))

            // Test the client - should not throw exception
            userApiClientService.deleteUser("123")
        }

        @KoraConfigModifier
        fun configModifier(): KoraConfigModifier {
            return KoraConfigModifier { config ->
                config.withSystemProperty("USER_API_URL", "http://localhost:${mockServer.serverPort}")
            }
        }
    }
    ```

Run your tests:

```bash
./gradlew test --tests UserApiClientTest
```

You should see all tests pass, demonstrating that your generated OpenAPI client correctly handles all CRUD operations with proper request/response mapping.

## Key Concepts Learned

### Contract-First Client Development
- **Shared Specifications**: Same OpenAPI spec for both client and server ensures contract compliance
- **Type Safety**: Compile-time guarantees for request/response structures
- **Automatic Validation**: Built-in request/response validation from the specification
- **Error Handling**: Proper exception mapping for HTTP errors

### Generated Client Benefits
- **Consistency**: All API calls follow the same patterns
- **Productivity**: No manual request construction or response parsing
- **Reliability**: Generated code is less error-prone than manual implementations
- **Maintainability**: API changes start with specification updates

### Client vs Server Generation

| Aspect | Client Generation | Server Generation |
|--------|-------------------|-------------------|
| **Mode** | `java-client` | `java-server` |
| **Output** | HTTP client interfaces | HTTP route handlers |
| **Usage** | Call external APIs | Handle incoming requests |
| **Validation** | Request validation | Request + response validation |
| **Dependencies** | HTTP client modules | HTTP server modules |

## Next Steps

Continue your API development journey:

- **Next Guide**: [Database Integration](../database-jdbc.md) - Add persistence to your APIs
- **Complete the Contract**: [OpenAPI HTTP Server](../openapi-http-server.md) - Generate servers from the same specification (already available)
- **Related Guides**:
  - [Observability & Monitoring](../observability.md) - Add comprehensive monitoring
  - [Resilience Patterns](../resilient.md) - Add fault tolerance to your clients
- **Advanced Topics**:
  - [OpenAPI Codegen Configuration](../../documentation/openapi-codegen.md) - Customize client generation
  - [API Versioning Strategies](../../documentation/openapi-codegen.md#versioning) - Handle API evolution
  - [Custom Client Configuration](../../documentation/http-client.md) - Advanced HTTP client setup

## Troubleshooting

### Code Generation Issues
- **Task not found**: Ensure the OpenAPI generator plugin is properly configured in `build.gradle`
- **Generation fails**: Check your OpenAPI YAML syntax with an online validator
- **Missing dependencies**: Verify all required dependencies are included

### Client Implementation
- **Method not found**: Ensure your client service uses the correct generated API interface
- **Type mismatches**: Check that your request models match the generated API models
- **Connection errors**: Verify the server is running and the base URL is correct

### Runtime Issues
- **404 errors**: Verify the API paths match your OpenAPI specification
- **Validation errors**: Check that request bodies conform to the OpenAPI schema
- **Timeout errors**: Configure appropriate timeout settings in `application.conf`

### Build Issues
- **Compilation errors**: Run `./gradlew clean` and regenerate OpenAPI client code
- **Missing classes**: Ensure `compileJava.dependsOn` is set for the client generation task
- **IDE issues**: Refresh your IDE project after client code generation

This guide transforms your manual HTTP clients into professional, contract-first clients that generate type-safe API calls from a single OpenAPI specification! 🎉