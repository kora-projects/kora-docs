---
title: Black Box Testing with Kora
summary: Learn comprehensive black box testing strategies for Kora applications using Testcontainers and HTTP APIs
tags: testing, black-box-tests, testcontainers, http-testing, end-to-end-testing
---

# Black Box Testing with Kora

This guide covers comprehensive black box testing strategies for Kora applications. Black box tests validate the complete application through its public HTTP APIs, providing the highest confidence that your application works correctly end-to-end.

!!! important "Continuation of JUnit Testing Guide"

    This guide is a continuation of the **[JUnit Testing](../testing-junit.md)** guide. It assumes you have completed the JUnit testing guide and are familiar with Kora's testing fundamentals, component tests, and integration tests.

    If you haven't completed the JUnit testing guide yet, please do so first as this guide builds upon that foundation.

## What You'll Build

You'll create comprehensive black box tests that cover:

- **Complete Application Testing**: Testing the full application through HTTP APIs
- **Containerized Testing**: Using Docker containers for realistic test environments
- **Database Integration**: Testing with real PostgreSQL databases
- **API Contract Validation**: Ensuring API behavior matches specifications
- **End-to-End Scenarios**: Testing complete user workflows

## What You'll Need

- JDK 17 or later
- Gradle 7.0+
- Docker (for Testcontainers)
- A text editor or IDE
- Completed [JUnit Testing](../testing-junit.md) guide

## Prerequisites

!!! note "Required: Complete JUnit Testing Guide"

    This guide assumes you have completed the **[JUnit Testing](../testing-junit.md)** guide and have:

    - A working Kora project with UserService and UserController
    - Testing dependencies configured (Kora test framework, Testcontainers, etc.)
    - Basic understanding of Kora's testing patterns

    If you haven't completed the JUnit testing guide yet, please do so first.

## Black Box Testing Overview

Black box testing represents the pinnacle of software testing confidence - testing your complete application exactly as users experience it, through its public HTTP APIs. Unlike component or integration tests that validate internal implementation details, black box tests treat your application as a complete black box, focusing solely on inputs and outputs without knowledge of internal workings.

### What Makes Black Box Testing the Gold Standard?

**Black box testing validates the complete user experience:**

- **User Perspective Testing**: Tests the application exactly as real users interact with it
- **API Contract Validation**: Ensures HTTP APIs behave correctly with proper request/response cycles
- **End-to-End Workflow Testing**: Validates complete business processes from start to finish
- **Integration Issue Detection**: Catches problems that only appear when all components work together
- **Production Readiness Assurance**: Provides highest confidence that the application works in production

### Why Kora Recommends Black Box Testing as Primary Approach

**Black box testing catches issues that other testing levels miss:**

- **Serialization/Deserialization Bugs**: JSON parsing, validation, and transformation issues
- **HTTP Layer Problems**: Headers, status codes, content types, and routing issues
- **Configuration Integration**: Environment variables, profiles, and runtime configuration
- **Middleware Issues**: Authentication, authorization, logging, and monitoring integration
- **Cross-Cutting Concerns**: Transactions, caching, and error handling across the full stack

Despite being slower than component tests, Kora strongly recommends black box testing as the primary approach because Kora applications have extremely fast startup times. This makes black box tests practical and not prohibitively slow, while providing the highest confidence that your application works correctly end-to-end.

### Black Box Testing vs Other Testing Approaches

| Testing Type | Scope | Infrastructure | Speed | Confidence | Catches |
|-------------|-------|----------------|-------|------------|---------|
| **Component Tests** | Component interactions | Mocked | ⚡ Fast | 🔧 Medium | Business logic bugs |
| **Integration Tests** | Infrastructure integration | Real (Testcontainers) | 🐌 Slow | 🔧 High | Data persistence issues |
| **Black Box Tests** | Complete application | Real (Containerized) | 🐌 Slowest | 🔧 Highest | User experience issues |

### When to Use Black Box Testing

**Black box tests are essential for:**

- **API Contract Verification**: Ensuring HTTP endpoints behave as specified
- **User Workflow Validation**: Testing complete user journeys and business processes
- **Regression Prevention**: Catching breaking changes in user-facing behavior
- **Production Readiness**: Final validation before deployment
- **Integration Issue Detection**: Finding problems between application layers

**Black box tests are NOT ideal for:**

- **Fast Development Feedback**: Use component tests during active development
- **Algorithm Testing**: Use unit tests for complex mathematical logic
- **Performance Testing**: Requires specialized load testing tools
- **Debugging Internal Logic**: Use component/integration tests for internal validation

### How Black Box Testing Works in Practice

**Containerized Application Testing:**
1. **Application Packaging**: Your complete application runs in a Docker container
2. **Infrastructure Provisioning**: Real databases and services via Testcontainers
3. **HTTP API Testing**: Tests send real HTTP requests to the containerized application
4. **Response Validation**: Complete validation of HTTP responses, status codes, and data
5. **State Verification**: Database queries to verify data persistence and integrity

**Test Isolation and Realism:**
- **Fresh Environment**: Each test gets a clean application instance and database
- **Real HTTP Communication**: Actual network calls, not mocked HTTP clients
- **Production Configuration**: Tests with production-like settings and dependencies
- **Complete Stack Validation**: From HTTP request to database and back

### Black Box Testing Trade-offs

**Higher Resource Requirements:**
- **Slower Execution**: Container startup and HTTP calls take more time
- **Resource Intensive**: Requires Docker and more system resources
- **Complex Setup**: More infrastructure configuration than simpler tests

**But the confidence gained is worth it:**
- **Production Bug Prevention**: Catches issues before they reach production
- **User Experience Validation**: Ensures applications work as users expect
- **Integration Issue Detection**: Finds problems between components and layers
- **Contract Compliance**: Verifies API contracts are maintained across changes

!!! important "Kora's Primary Testing Strategy"

    Kora strongly recommends **black box testing** as the primary testing approach. While unit and integration tests are valuable for development feedback, black box tests validate the complete user experience and catch integration issues that other test types miss.

!!! note "AppContainer Pattern"

    Kora examples use the `AppContainer` pattern to run the complete application in a containerized environment for black box testing.

===! ":fontawesome-brands-java: `Java`"

    First, create an application container:

    Create `src/test/java/ru/tinkoff/kora/example/AppContainer.java`:

    ```java
    package ru.tinkoff.kora.example;

    import java.net.URI;
    import java.nio.file.Paths;
    import java.time.Duration;
    import java.util.Map;
    import org.slf4j.LoggerFactory;
    import org.testcontainers.containers.GenericContainer;
    import org.testcontainers.containers.output.Slf4jLogConsumer;
    import org.testcontainers.containers.wait.strategy.Wait;
    import org.testcontainers.images.builder.ImageFromDockerfile;
    import org.testcontainers.utility.DockerImageName;

    public final class AppContainer extends GenericContainer<AppContainer> {

        private AppContainer() {
            super(new ImageFromDockerfile("kora-example")
                    .withDockerfile(Paths.get("Dockerfile").toAbsolutePath()));
        }

        private AppContainer(DockerImageName image) {
            super(image);
        }

        public static AppContainer build() {
            final String appImage = System.getenv("IMAGE_KORA_EXAMPLE");
            return (appImage != null && !appImage.isBlank())
                    ? new AppContainer(DockerImageName.parse(appImage))
                    : new AppContainer();
        }

        @Override
        protected void configure() {
            super.configure();
            withExposedPorts(8080, 8085); // 8080 for API, 8085 for health checks
            withStartupTimeout(Duration.ofSeconds(120));
            withLogConsumer(new Slf4jLogConsumer(LoggerFactory.getLogger(AppContainer.class)));
            waitingFor(Wait.forHttp("/system/readiness").forPort(8085).forStatusCode(200));
        }

        public int getPort() {
            return getMappedPort(8080);
        }

        public URI getURI() {
            return URI.create(String.format("http://%s:%s", getHost(), getPort()));
        }

        public URI getSystemURI() {
            return URI.create(String.format("http://%s:%s", getHost(), getMappedPort(8085)));
        }
    }
    ```

    Then create the black box test:

    Create `src/test/java/ru/tinkoff/kora/example/BlackBoxTests.java`:

    ```java
    package ru.tinkoff.kora.example;

    import static org.junit.jupiter.api.Assertions.*;
    import static org.skyscreamer.jsonassert.JSONAssert.*;
    import static org.skyscreamer.jsonassert.JSONCompareMode.*;

    import io.goodforgod.testcontainers.extensions.ContainerMode;
    import io.goodforgod.testcontainers.extensions.Network;
    import io.goodforgod.testcontainers.extensions.jdbc.ConnectionPostgreSQL;
    import io.goodforgod.testcontainers.extensions.jdbc.JdbcConnection;
    import io.goodforgod.testcontainers.extensions.jdbc.Migration;
    import io.goodforgod.testcontainers.extensions.jdbc.TestcontainersPostgreSQL;
    import java.net.http.HttpClient;
    import java.net.http.HttpRequest;
    import java.net.http.HttpResponse;
    import java.time.Duration;
    import java.util.Map;
    import org.json.JSONObject;
    import org.junit.jupiter.api.AfterAll;
    import org.junit.jupiter.api.BeforeAll;
    import org.junit.jupiter.api.Test;

    @TestcontainersPostgreSQL(
            network = @Network(shared = true),
            mode = ContainerMode.PER_RUN,
            migration = @Migration(
                    engine = Migration.Engines.FLYWAY,
                    apply = Migration.Mode.PER_METHOD,
                    drop = Migration.Mode.PER_METHOD))
    class BlackBoxTests {

        private static final AppContainer container = AppContainer.build()
                .withNetwork(org.testcontainers.containers.Network.SHARED);

        @ConnectionPostgreSQL
        private JdbcConnection connection;

        @BeforeAll
        public static void setup(@ConnectionPostgreSQL JdbcConnection connection) {
            var params = connection.paramsInNetwork().orElseThrow();
            container.withEnv(Map.of(
                    "POSTGRES_JDBC_URL", params.jdbcUrl(),
                    "POSTGRES_USER", params.username(),
                    "POSTGRES_PASS", params.password(),
                    "CACHE_MAX_SIZE", "0")); // Disable cache for testing

            container.start();
        }

        @AfterAll
        public static void cleanup() {
            container.stop();
        }

        @Test
        void createUser_ShouldCreateAndReturnUser() throws Exception {
            // Given
            var httpClient = HttpClient.newHttpClient();
            var requestBody = new JSONObject()
                    .put("name", "John Doe")
                    .put("email", "john@example.com");

            // When
            var request = HttpRequest.newBuilder()
                    .POST(HttpRequest.BodyPublishers.ofString(requestBody.toString()))
                    .uri(container.getURI().resolve("/users"))
                    .header("Content-Type", "application/json")
                    .build();

            var response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

            // Then
            assertEquals(200, response.statusCode());
            var responseBody = new JSONObject(response.body());
            assertNotNull(responseBody.optString("id"));
            assertEquals("John Doe", responseBody.getString("name"));
            assertEquals("john@example.com", responseBody.getString("email"));
        }

        @Test
        void getUser_ShouldReturnUser() throws Exception {
            // Given - Create a user first
            var httpClient = HttpClient.newHttpClient();
            var createRequestBody = new JSONObject()
                    .put("name", "Jane Doe")
                    .put("email", "jane@example.com");

            var createRequest = HttpRequest.newBuilder()
                    .POST(HttpRequest.BodyPublishers.ofString(createRequestBody.toString()))
                    .uri(container.getURI().resolve("/users"))
                    .header("Content-Type", "application/json")
                    .build();

            var createResponse = httpClient.send(createRequest, HttpResponse.BodyHandlers.ofString());
            assertEquals(200, createResponse.statusCode());
            var createResponseBody = new JSONObject(createResponse.body());
            var userId = createResponseBody.getString("id");

            // When - Get the user
            var getRequest = HttpRequest.newBuilder()
                    .GET()
                    .uri(container.getURI().resolve("/users/" + userId))
                    .build();

            var getResponse = httpClient.send(getRequest, HttpResponse.BodyHandlers.ofString());

            // Then
            assertEquals(200, getResponse.statusCode());
            var getResponseBody = new JSONObject(getResponse.body());
            assertEquals(userId, getResponseBody.getString("id"));
            assertEquals("Jane Doe", getResponseBody.getString("name"));
            assertEquals("jane@example.com", getResponseBody.getString("email"));
        }

        @Test
        void getUser_NotFound_ShouldReturn404() throws Exception {
            // Given
            var httpClient = HttpClient.newHttpClient();

            // When
            var request = HttpRequest.newBuilder()
                    .GET()
                    .uri(container.getURI().resolve("/users/non-existent-id"))
                    .build();

            var response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

            // Then
            assertEquals(404, response.statusCode());
        }

        @Test
        void updateUser_ShouldUpdateAndReturnUser() throws Exception {
            // Given - Create a user first
            var httpClient = HttpClient.newHttpClient();
            var createRequestBody = new JSONObject()
                    .put("name", "John")
                    .put("email", "john@example.com");

            var createRequest = HttpRequest.newBuilder()
                    .POST(HttpRequest.BodyPublishers.ofString(createRequestBody.toString()))
                    .uri(container.getURI().resolve("/users"))
                    .header("Content-Type", "application/json")
                    .build();

            var createResponse = httpClient.send(createRequest, HttpResponse.BodyHandlers.ofString());
            assertEquals(200, createResponse.statusCode());
            var createResponseBody = new JSONObject(createResponse.body());
            var userId = createResponseBody.getString("id");

            // When - Update the user
            var updateRequestBody = new JSONObject()
                    .put("name", "John Updated")
                    .put("email", "john.updated@example.com");

            var updateRequest = HttpRequest.newBuilder()
                    .PUT(HttpRequest.BodyPublishers.ofString(updateRequestBody.toString()))
                    .uri(container.getURI().resolve("/users/" + userId))
                    .header("Content-Type", "application/json")
                    .build();

            var updateResponse = httpClient.send(updateRequest, HttpResponse.BodyHandlers.ofString());

            // Then
            assertEquals(200, updateResponse.statusCode());
            var updateResponseBody = new JSONObject(updateResponse.body());
            assertEquals(userId, updateResponseBody.getString("id"));
            assertEquals("John Updated", updateResponseBody.getString("name"));
            assertEquals("john.updated@example.com", updateResponseBody.getString("email"));

            // Verify custom header
            assertTrue(updateResponse.headers().firstValue("X-Updated-At").isPresent());
        }

        @Test
        void deleteUser_ShouldRemoveUser() throws Exception {
            // Given - Create a user first
            var httpClient = HttpClient.newHttpClient();
            var createRequestBody = new JSONObject()
                    .put("name", "John")
                    .put("email", "john@example.com");

            var createRequest = HttpRequest.newBuilder()
                    .POST(HttpRequest.BodyPublishers.ofString(createRequestBody.toString()))
                    .uri(container.getURI().resolve("/users"))
                    .header("Content-Type", "application/json")
                    .build();

            var createResponse = httpClient.send(createRequest, HttpResponse.BodyHandlers.ofString());
            assertEquals(200, createResponse.statusCode());
            var createResponseBody = new JSONObject(createResponse.body());
            var userId = createResponseBody.getString("id");

            // When - Delete the user
            var deleteRequest = HttpRequest.newBuilder()
                    .DELETE()
                    .uri(container.getURI().resolve("/users/" + userId))
                    .build();

            var deleteResponse = httpClient.send(deleteRequest, HttpResponse.BodyHandlers.ofString());

            // Then
            assertEquals(204, deleteResponse.statusCode());

            // Verify user is deleted
            var getRequest = HttpRequest.newBuilder()
                    .GET()
                    .uri(container.getURI().resolve("/users/" + userId))
                    .build();

            var getResponse = httpClient.send(getRequest, HttpResponse.BodyHandlers.ofString());
            assertEquals(404, getResponse.statusCode());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    First, create an application container:

    Create `src/test/kotlin/ru/tinkoff/kora/example/AppContainer.kt`:

    ```kotlin
    package ru.tinkoff.kora.example

    import java.net.URI
    import java.nio.file.Paths
    import java.time.Duration
    import org.slf4j.LoggerFactory
    import org.testcontainers.containers.GenericContainer
    import org.testcontainers.containers.output.Slf4jLogConsumer
    import org.testcontainers.containers.wait.strategy.Wait
    import org.testcontainers.images.builder.ImageFromDockerfile
    import org.testcontainers.utility.DockerImageName

    class AppContainer : GenericContainer<AppContainer> {

        private constructor() : super(
            ImageFromDockerfile("kora-example")
                .withDockerfile(Paths.get("Dockerfile").toAbsolutePath())
        )

        private constructor(image: DockerImageName) : super(image)

        companion object {
            fun build(): AppContainer {
                val appImage = System.getenv("IMAGE_KORA_EXAMPLE")
                return if (!appImage.isNullOrBlank()) {
                    AppContainer(DockerImageName.parse(appImage))
                } else {
                    AppContainer()
                }
            }
        }

        override fun configure() {
            super.configure()
            withExposedPorts(8080, 8085) // 8080 for API, 8085 for health checks
            withStartupTimeout(Duration.ofSeconds(120))
            withLogConsumer(Slf4jLogConsumer(LoggerFactory.getLogger(AppContainer::class.java)))
            waitingFor(Wait.forHttp("/system/readiness").forPort(8085).forStatusCode(200))
        }

        fun getPort(): Int = getMappedPort(8080)

        fun getURI(): URI = URI.create("http://${host}:${getPort()}")

        fun getSystemURI(): URI = URI.create("http://${host}:${getMappedPort(8085)}")
    }
    ```

    Then create the black box test:

    Create `src/test/kotlin/ru/tinkoff/kora/example/BlackBoxTests.kt`:

    ```kotlin
    package ru.tinkoff.kora.example

    import io.goodforgod.testcontainers.extensions.ContainerMode
    import io.goodforgod.testcontainers.extensions.Network
    import io.goodforgod.testcontainers.extensions.jdbc.ConnectionPostgreSQL
    import io.goodforgod.testcontainers.extensions.jdbc.JdbcConnection
    import io.goodforgod.testcontainers.extensions.jdbc.Migration
    import io.goodforgod.testcontainers.extensions.jdbc.TestcontainersPostgreSQL
    import org.json.JSONObject
    import org.junit.jupiter.api.AfterAll
    import org.junit.jupiter.api.Assertions.*
    import org.junit.jupiter.api.BeforeAll
    import org.junit.jupiter.api.Test
    import org.skyscreamer.jsonassert.JSONAssert
    import org.skyscreamer.jsonassert.JSONCompareMode
    import java.net.http.HttpClient
    import java.net.http.HttpRequest
    import java.net.http.HttpResponse
    import java.time.Duration

    @TestcontainersPostgreSQL(
        network = Network(shared = true),
        mode = ContainerMode.PER_RUN,
        migration = Migration(
            engine = Migration.Engines.FLYWAY,
            apply = Migration.Mode.PER_METHOD,
            drop = Migration.Mode.PER_METHOD
        )
    )
    class BlackBoxTests {

        companion object {
            private val container = AppContainer.build()
                .withNetwork(org.testcontainers.containers.Network.SHARED)

            @ConnectionPostgreSQL
            private lateinit var connection: JdbcConnection

            @BeforeAll
            @JvmStatic
            fun setup() {
                val params = connection.paramsInNetwork().orElseThrow()
                container.withEnv(mapOf(
                    "POSTGRES_JDBC_URL" to params.jdbcUrl(),
                    "POSTGRES_USER" to params.username(),
                    "POSTGRES_PASS" to params.password(),
                    "CACHE_MAX_SIZE" to "0"
                ))
                container.start()
            }

            @AfterAll
            @JvmStatic
            fun cleanup() {
                container.stop()
            }
        }

        @Test
        fun `createUser should create user via API`() {
            // Given
            val httpClient = HttpClient.newHttpClient()
            val requestBody = JSONObject()
                .put("name", "John")
                .put("email", "john@example.com")

            // When
            val request = HttpRequest.newBuilder()
                .POST(HttpRequest.BodyPublishers.ofString(requestBody.toString()))
                .uri(container.getURI().resolve("/users"))
                .header("Content-Type", "application/json")
                .timeout(Duration.ofSeconds(5))
                .build()

            val response = httpClient.send(request, HttpResponse.BodyHandlers.ofString())

            // Then
            assertEquals(200, response.statusCode(), response.body())
            connection.assertCountsEquals(1, "users")

            val responseBody = JSONObject(response.body())
            assertNotNull(responseBody.optString("id"))
            assertEquals("John", responseBody.getString("name"))
            assertEquals("john@example.com", responseBody.getString("email"))
        }

        @Test
        fun `getUser should return user via API`() {
            // Given - Create user first
            val httpClient = HttpClient.newHttpClient()
            val createRequestBody = JSONObject()
                .put("name", "Jane")
                .put("email", "jane@example.com")

            val createRequest = HttpRequest.newBuilder()
                .POST(HttpRequest.BodyPublishers.ofString(createRequestBody.toString()))
                .uri(container.getURI().resolve("/users"))
                .header("Content-Type", "application/json")
                .timeout(Duration.ofSeconds(5))
                .build()

            val createResponse = httpClient.send(createRequest, HttpResponse.BodyHandlers.ofString())
            assertEquals(200, createResponse.statusCode())
            val createResponseBody = JSONObject(createResponse.body())
            val userId = createResponseBody.getString("id")

            // When - Get the user
            val getRequest = HttpRequest.newBuilder()
                .GET()
                .uri(container.getURI().resolve("/users/$userId"))
                .timeout(Duration.ofSeconds(5))
                .build()

            val getResponse = httpClient.send(getRequest, HttpResponse.BodyHandlers.ofString())

            // Then
            assertEquals(200, getResponse.statusCode(), getResponse.body())
            JSONAssert.assertEquals(createResponseBody.toString(), getResponse.body(), JSONCompareMode.LENIENT)
        }

        @Test
        fun `getUsers with pagination should return paginated results`() {
            // Given - Create multiple users
            val httpClient = HttpClient.newHttpClient()
            val users = arrayOf(
                arrayOf("Alice", "alice@example.com"),
                arrayOf("Bob", "bob@example.com"),
                arrayOf("Charlie", "charlie@example.com"),
                arrayOf("David", "david@example.com")
            )

            for (user in users) {
                val requestBody = JSONObject()
                    .put("name", user[0])
                    .put("email", user[1])

                val request = HttpRequest.newBuilder()
                    .POST(HttpRequest.BodyPublishers.ofString(requestBody.toString()))
                    .uri(container.getURI().resolve("/users"))
                    .header("Content-Type", "application/json")
                    .timeout(Duration.ofSeconds(5))
                    .build()

                val response = httpClient.send(request, HttpResponse.BodyHandlers.ofString())
                assertEquals(200, response.statusCode())
            }

            // When - Get paginated results
            val getRequest = HttpRequest.newBuilder()
                .GET()
                .uri(container.getURI().resolve("/users?page=1&size=2&sort=name"))
                .timeout(Duration.ofSeconds(5))
                .build()

            val getResponse = httpClient.send(getRequest, HttpResponse.BodyHandlers.ofString())

            // Then
            assertEquals(200, getResponse.statusCode(), getResponse.body())
            val responseBody = JSONObject(getResponse.body())
            val usersArray = responseBody.getJSONArray("users")
            assertEquals(2, usersArray.length())
            // Should return second page: Charlie, David (alphabetically sorted)
            assertEquals("Charlie", usersArray.getJSONObject(0).getString("name"))
            assertEquals("David", usersArray.getJSONObject(1).getString("name"))
        }

        @Test
        fun `updateUser should update user via API`() {
            // Given - Create user first
            val httpClient = HttpClient.newHttpClient()
            val createRequestBody = JSONObject()
                .put("name", "John")
                .put("email", "john@example.com")

            val createRequest = HttpRequest.newBuilder()
                .POST(HttpRequest.BodyPublishers.ofString(createRequestBody.toString()))
                .uri(container.getURI().resolve("/users"))
                .header("Content-Type", "application/json")
                .timeout(Duration.ofSeconds(5))
                .build()

            val createResponse = httpClient.send(createRequest, HttpResponse.BodyHandlers.ofString())
            assertEquals(200, createResponse.statusCode())
            val createResponseBody = JSONObject(createResponse.body())
            val userId = createResponseBody.getString("id")

            // When - Update the user
            val updateRequestBody = JSONObject()
                .put("name", "John Updated")
                .put("email", "john.updated@example.com")

            val updateRequest = HttpRequest.newBuilder()
                .PUT(HttpRequest.BodyPublishers.ofString(updateRequestBody.toString()))
                .uri(container.getURI().resolve("/users/$userId"))
                .header("Content-Type", "application/json")
                .timeout(Duration.ofSeconds(5))
                .build()

            val updateResponse = httpClient.send(updateRequest, HttpResponse.BodyHandlers.ofString())

            // Then
            assertEquals(200, updateResponse.statusCode(), updateResponse.body())
            val updateResponseBody = JSONObject(updateResponse.body())
            assertEquals(userId, updateResponseBody.getString("id"))
            assertEquals("John Updated", updateResponseBody.getString("name"))
            assertEquals("john.updated@example.com", updateResponseBody.getString("email"))

            // Verify custom header
            assertTrue(updateResponse.headers().firstValue("X-Updated-At").isPresent())
        }

        @Test
        fun `deleteUser should delete user via API`() {
            // Given - Create user first
            val httpClient = HttpClient.newHttpClient()
            val createRequestBody = JSONObject()
                .put("name", "John")
                .put("email", "john@example.com")

            val createRequest = HttpRequest.newBuilder()
                .POST(HttpRequest.BodyPublishers.ofString(createRequestBody.toString()))
                .uri(container.getURI().resolve("/users"))
                .header("Content-Type", "application/json")
                .timeout(Duration.ofSeconds(5))
                .build()

            val createResponse = httpClient.send(createRequest, HttpResponse.BodyHandlers.ofString())
            assertEquals(200, createResponse.statusCode())
            val createResponseBody = JSONObject(createResponse.body())
            val userId = createResponseBody.getString("id")

            // When - Delete the user
            val deleteRequest = HttpRequest.newBuilder()
                .DELETE()
                .uri(container.getURI().resolve("/users/$userId"))
                .timeout(Duration.ofSeconds(5))
                .build()

            val deleteResponse = httpClient.send(deleteRequest, HttpResponse.BodyHandlers.ofString())

            // Then
            assertEquals(204, deleteResponse.statusCode())

            // Verify user is deleted
            val getRequest = HttpRequest.newBuilder()
                .GET()
                .uri(container.getURI().resolve("/users/$userId"))
                .timeout(Duration.ofSeconds(5))
                .build()

            val getResponse = httpClient.send(getRequest, HttpResponse.BodyHandlers.ofString())
            assertEquals(404, getResponse.statusCode())
        }

        @Test
        fun `getUser not found should return 404`() {
            // Given
            val httpClient = HttpClient.newHttpClient()

            // When
            val request = HttpRequest.newBuilder()
                .GET()
                .uri(container.getURI().resolve("/users/999"))
                .timeout(Duration.ofSeconds(5))
                .build()

            val response = httpClient.send(request, HttpResponse.BodyHandlers.ofString())

            // Then
            assertEquals(404, response.statusCode())
        }
    }
    ```

!!! tip "Black Box Testing Benefits"

    **Why prioritize black box testing?**

    - **Real User Experience**: Tests actual HTTP APIs as users would use them
    - **Integration Validation**: Catches issues between components, serialization, etc.
    - **Contract Verification**: Ensures API contracts are maintained
    - **Deployment Confidence**: Validates complete application behavior
    - **Regression Prevention**: Catches breaking changes in user-facing behavior

!!! note "Container Management"

    The `AppContainer` pattern provides:

    - **Dockerfile-based Testing**: Tests your actual application image
    - **Environment Isolation**: Fresh container per test run
    - **Health Check Integration**: Waits for application readiness
    - **Port Management**: Automatic port mapping and URI construction
    - **Log Integration**: Application logs available in test output

## Running Black Box Tests

Run your black box tests using Gradle:

```bash
# Run all tests including black box tests
./gradlew test

# Run only black box tests
./gradlew test --tests "*BlackBoxTests*"

# Run with verbose output
./gradlew test --info
```

!!! tip "Test Execution Tips"

    - **Docker Required**: Black box tests require Docker to run containers
    - **Network Access**: Tests may take longer due to container startup
    - **Resource Intensive**: Consider running black box tests separately from unit tests
    - **Parallel Execution**: Black box tests typically run sequentially due to container conflicts

## Best Practices for Black Box Testing

### Test Organization

- **API Contract Tests**: Test each endpoint's contract (request/response format)
- **Business Logic Tests**: Test complete user workflows and business rules
- **Error Scenario Tests**: Test error conditions and edge cases
- **Integration Tests**: Test interactions between services

### Test Data Management

- **Isolated Test Data**: Each test should create its own test data
- **Cleanup Strategy**: Use database cleanup or fresh containers between tests
- **Realistic Data**: Use realistic test data that matches production patterns
- **Data Validation**: Verify data persistence and retrieval

### Performance Considerations

- **Container Reuse**: Consider reusing containers when possible to reduce startup time
- **Parallel Execution**: Run black box tests in parallel when containers allow it
- **Resource Limits**: Set appropriate resource limits for test containers
- **Timeout Management**: Configure appropriate timeouts for HTTP requests

### Debugging Black Box Tests

- **Container Logs**: Access container logs for debugging application issues
- **Network Inspection**: Use tools like Wireshark to inspect HTTP traffic
- **Database Inspection**: Query test databases directly for data validation
- **Application Metrics**: Monitor application metrics during test execution

## Summary

Black box testing provides the highest confidence in your Kora application's correctness by testing the complete user experience through HTTP APIs. By using the `AppContainer` pattern with Testcontainers, you can create realistic, isolated test environments that validate your application's behavior end-to-end.

Key takeaways:

- **Black Box First**: Kora recommends black box testing as the primary testing strategy
- **Containerized Testing**: Use Docker containers for realistic test environments
- **API Contract Validation**: Test complete HTTP API contracts
- **End-to-End Validation**: Test complete user workflows and business logic
- **Isolation**: Each test gets a fresh environment with proper cleanup

Black box tests complement component and integration tests by providing the final validation that your application works correctly from the user's perspective.

## What's Next?

- Explore [Configuration Overrides](../testing-junit.md#configuration-overrides-for-testing) for advanced test scenarios
- Learn about [Test Reporting and Coverage](../testing-junit.md#test-reporting-and-coverage)
- Study [Testing Best Practices](../testing-junit.md#best-practices) for comprehensive testing strategies

## Key Concepts Learned

### Black Box Testing Strategy
- **Black Box First**: Kora's recommended primary testing approach for highest confidence
- **End-to-End Validation**: Test complete user workflows through HTTP APIs
- **API Contract Testing**: Validate complete request/response cycles
- **User Perspective Testing**: Test application behavior as users experience it

### AppContainer Pattern
- **Containerized Applications**: Run complete applications in Docker containers
- **Realistic Environments**: Test with actual infrastructure and dependencies
- **Network Isolation**: Each test gets dedicated ports and network configuration
- **Automatic Lifecycle**: Containers start/stop automatically with test execution

### HTTP API Testing
- **Complete Request Flow**: Test from HTTP request to database and back
- **Status Code Validation**: Verify correct HTTP response codes
- **Response Content Validation**: Check JSON responses and data correctness
- **Error Handling**: Test error scenarios and proper error responses

### Test Isolation and Performance
- **Fresh Environments**: Each test starts with clean database and application state
- **Resource Cleanup**: Automatic cleanup of containers and connections
- **Parallel Execution**: Tests can run concurrently for faster execution
- **Realistic Load**: Test with actual network calls and database operations

## Troubleshooting

### AppContainer Not Starting
- Ensure Docker is running and accessible
- Check that application JAR is built and available
- Verify Docker image configuration and base images
- Check container logs for startup errors

### HTTP Connection Issues
- Ensure application container is fully started before tests run
- Check that HTTP port is correctly exposed and mapped
- Verify network configuration between test and application containers
- Check application logs for HTTP server startup issues

### Port Conflicts
- Ensure each test uses unique ports for application containers
- Check that ports are not already in use by other processes
- Use dynamic port allocation to avoid conflicts
- Verify port cleanup after test completion

### Database Setup Problems
- Ensure database container starts before application container
- Check database connection configuration in application
- Verify database schema initialization scripts run correctly
- Check database container logs for startup or connection errors

### Test Timeouts
- Increase timeout values for slow-starting containers
- Check application startup time and adjust wait strategies
- Verify network connectivity between containers
- Monitor resource usage (CPU/memory) during test execution

### Container Cleanup Issues
- Ensure proper cleanup in test teardown methods
- Check for hanging processes after test completion
- Verify Docker daemon has sufficient resources
- Use Testcontainers' automatic cleanup features

## Help

- [Testing Documentation](../../documentation/test.md)
- [Kora GitHub Repository](https://github.com/kora-projects/kora)
- [GitHub Discussions](https://github.com/kora-projects/kora/discussions)
- [Testcontainers Documentation](https://www.testcontainers.org/)