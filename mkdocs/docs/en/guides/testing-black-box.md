---
search:
  exclude: true
title: Black Box Testing with Kora
summary: Learn comprehensive black box testing strategies for Kora applications using Testcontainers and HTTP APIs
tags: testing, black-box-tests, testcontainers, http-testing, end-to-end-testing
---

# Black Box Testing with Kora { #black-box-testing-kora }

This guide introduces black-box testing for Kora HTTP applications. It covers how to start the full application as a test target, call it only through public HTTP endpoints, and verify behavior
without reaching into services, repositories, or generated graph internals. You will also see how Testcontainers and HTTP clients make these tests close to real runtime usage.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java Testing Black Box App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-testing-black-box-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin Testing Black Box App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-testing-black-box-app).

## What You'll Build { #youll-build }

You'll create comprehensive black box tests that cover:

- **Complete Application Testing**: Testing the full application through HTTP APIs
- **Containerized Testing**: Using Docker containers for realistic test environments
- **Database Integration**: Testing with real PostgreSQL databases
- **API Contract Validation**: Ensuring API behavior matches specifications
- **End-to-End Scenarios**: Testing complete user workflows

## What You'll Need { #youll-need }

- JDK 17 or later
- Gradle 7+
- Docker (for Testcontainers)
- A text editor or IDE
- Completed [Database Integration](database-jdbc.md) guide

## Prerequisites { #prerequisites }

!!! note "Required: Complete Database JDBC Guide"

    This guide assumes you have completed **[Database Integration](database-jdbc.md)** and have a working Kora project with JDBC repository, Flyway migrations, `UserService`, `UserController`, and basic Kora testing dependencies.

    If you haven't completed the database JDBC guide yet, do that first, because this guide runs the full application in containers and checks the API from the outside.

## Overview { #overview }

Black-box testing treats the application as an external system. The test does not call services, repositories, generated graph classes, or controller methods directly. It starts the application, sends
real HTTP requests, and verifies real HTTP responses.

### Why Black Box First { #black-box-first }

Kora applications start quickly because dependency graphs are generated at compile time and most wiring work is already known before runtime. That changes the usual testing trade-off. In many
frameworks, black-box tests are so expensive that teams reserve them only for a small smoke suite. In Kora, running the whole application is often practical enough to make black-box tests the main
source of confidence for user-facing behavior.

The reason is not that component or integration tests are unimportant. They are still useful for focused feedback. The reason is that many real bugs live between layers:

- a controller route is wired differently than a service test assumed
- JSON mapping or validation fails before service code runs
- configuration works in a unit test but not in the packaged application
- migrations and runtime database settings do not match
- an error response has the wrong status code or body shape

Black-box tests catch those problems because they exercise the same public boundary a real client uses. They are slower than component tests, but they validate the behavior that matters most to API
consumers.

### What External Tests Prove { #external-tests-prove }

Black-box tests are valuable because they include the whole runtime path:

- HTTP routing and status codes
- JSON serialization and deserialization
- validation and error responses
- configuration loading
- dependency graph startup
- database connectivity and migrations
- cross-cutting behavior such as logging, probes, or middleware

That makes them the best test type for user-facing behavior. If a black-box test passes, a client can call the application in the same way the test did.

### Containers as the Test Environment { #containers-test-environment }

In this guide, the application itself runs in a container and [PostgreSQL](https://www.postgresql.org/docs/) runs in another [Testcontainers](https://java.testcontainers.org/)-managed container. The
test communicates with the application over HTTP, not through in-process objects. This makes the setup closer to deployment than component or integration tests.

The practical black-box flow is:

1. build or start the application container
2. start required infrastructure containers
3. pass runtime configuration into the application
4. call public endpoints through HTTP
5. assert response status codes, headers, bodies, and persisted behavior

### Trade-Offs { #trade-offs }

Black-box tests are slower and require [Docker](https://docs.docker.com/), but they catch classes of problems that narrower tests cannot see: wrong ports, broken packaging, missing runtime
configuration, invalid container environment, HTTP contract drift, and wiring problems that only appear when the full application starts.

They should not replace every focused test. Use component tests for quick feedback on business logic, integration tests for persistence boundaries, and black-box tests as the strongest check that the
complete application works from a client's point of view.

The practical flow is:

1. package the application so it can run in a container
2. start PostgreSQL and the application with Testcontainers
3. inject runtime configuration through container environment variables
4. call the public HTTP API from the test
5. assert response codes, JSON bodies, and persistent state

## Dependencies { #dependencies }

Add testing dependencies for black-box tests in your black-box module.

===! ":fontawesome-brands-java: `Java`"

    Add to `build.gradle`:

    ```groovy
    dependencies {
        testImplementation platform("org.junit:junit-bom:5.14.3")

        testImplementation "org.junit.jupiter:junit-jupiter"
        testImplementation project(":guide-database-jdbc-app")
        testImplementation "ru.tinkoff.kora:test-junit5"
        testImplementation "org.json:json:20231013"
        testImplementation "org.testcontainers:junit-jupiter:1.21.4"
        testImplementation "org.testcontainers:testcontainers:1.21.4"
        testImplementation "org.testcontainers:postgresql:1.21.4"
    }

    test {
        dependsOn ":guide-database-jdbc-app:distTar"
        inputs.file("../guide-database-jdbc-app/Dockerfile")
        inputs.file("../guide-database-jdbc-app/build/distributions/application.tar")

        useJUnitPlatform()
        testLogging {
            showStandardStreams(true)
            events("passed", "skipped", "failed")
            exceptionFormat("full")
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Add to `build.gradle.kts`:

    ```kotlin
    dependencies {
        testImplementation(platform("org.junit:junit-bom:5.14.3"))

        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation(project(":guide-database-jdbc-app"))
        testImplementation("ru.tinkoff.kora:test-junit5")
        testImplementation("org.json:json:20231013")
        testImplementation("org.testcontainers:junit-jupiter:1.21.4")
        testImplementation("org.testcontainers:testcontainers:1.21.4")
        testImplementation("org.testcontainers:postgresql:1.21.4")
    }

    tasks.test {
        dependsOn(":guide-database-jdbc-app:distTar")
        inputs.file("../guide-database-jdbc-app/Dockerfile")
        inputs.file(project(":guide-database-jdbc-app").tasks.named("distTar").flatMap { it.archiveFile })

        useJUnitPlatform()
        testLogging {
            showStandardStreams = true
            events("passed", "skipped", "failed")
            exceptionFormat = org.gradle.api.tasks.testing.logging.TestExceptionFormat.FULL
        }
    }
    ```

## Dockerfile Setup { #dockerfile-setup }

Before creating `AppContainer`, add Docker packaging for the JDBC application from [Database Integration](database-jdbc.md).

Create `guides/guide-database-jdbc-app/Dockerfile`:

```dockerfile
FROM eclipse-temurin:17-jre-jammy

ARG TARGET_DIR=/opt/app

COPY build/distributions/application.tar /application.tar
RUN mkdir -p ${TARGET_DIR}
RUN tar -xf /application.tar -C ${TARGET_DIR}
RUN rm /application.tar

ARG DOCKER_USER=app
RUN groupadd -r ${DOCKER_USER} && useradd -rg ${DOCKER_USER} ${DOCKER_USER}
USER ${DOCKER_USER}

EXPOSE 8080/tcp
EXPOSE 8085/tcp
CMD ["/opt/app/application/bin/application"]
```

In black-box module `build.gradle`, make tests depend on distribution archive:

```groovy
test {
    dependsOn ":guide-database-jdbc-app:distTar"
    inputs.file("../guide-database-jdbc-app/Dockerfile")
    inputs.file("../guide-database-jdbc-app/build/distributions/application.tar")
}
```

## Application Container { #application-container }

`AppContainer` is a reusable wrapper around your application Docker image.
It encapsulates startup details so your test class stays focused on scenarios, not container plumbing.

What happens inside `AppContainer`:

- builds image from JDBC guide Dockerfile
- exposes public (`8080`) and private (`8085`) ports
- waits for `/system/readiness` on private port before tests run
- exposes helper methods to build HTTP base URI

===! ":fontawesome-brands-java: `Java`"

    Create `src/test/java/ru/tinkoff/kora/guide/testingblackbox/AppContainer.java`:

    ```java
    package ru.tinkoff.kora.guide.testingblackbox;

    import java.net.URI;
    import java.nio.file.Path;
    import java.time.Duration;
    import org.slf4j.LoggerFactory;
    import org.testcontainers.containers.GenericContainer;
    import org.testcontainers.containers.output.Slf4jLogConsumer;
    import org.testcontainers.containers.wait.strategy.Wait;
    import org.testcontainers.images.builder.ImageFromDockerfile;

    final class AppContainer extends GenericContainer<AppContainer> {

        AppContainer() {
            super(new ImageFromDockerfile("guide-database-jdbc-black-box")
                    .withDockerfile(Path.of("../guide-database-jdbc-app/Dockerfile")));

            withExposedPorts(8080, 8085);
            withStartupTimeout(Duration.ofMinutes(1));
            waitingFor(Wait.forHttp("/system/readiness").forPort(8085).forStatusCode(200));
            withLogConsumer(new Slf4jLogConsumer(LoggerFactory.getLogger(AppContainer.class)));
        }

        URI getURI() {
            return URI.create("http://" + getHost() + ":" + getMappedPort(8080));
        }

        URI getSystemURI() {
            return URI.create("http://" + getHost() + ":" + getMappedPort(8085));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/test/kotlin/ru/tinkoff/kora/guide/testingblackbox/AppContainer.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.testingblackbox

    import java.net.URI
    import java.nio.file.Path
    import java.time.Duration
    import org.slf4j.LoggerFactory
    import org.testcontainers.containers.GenericContainer
    import org.testcontainers.containers.output.Slf4jLogConsumer
    import org.testcontainers.containers.wait.strategy.Wait
    import org.testcontainers.images.builder.ImageFromDockerfile

    class AppContainer : GenericContainer<AppContainer>(
        ImageFromDockerfile("guide-database-jdbc-black-box")
            .withDockerfile(Path.of("../guide-database-jdbc-app/Dockerfile"))
    ) {

        init {
            withExposedPorts(8080, 8085)
            withStartupTimeout(Duration.ofMinutes(1))
            waitingFor(Wait.forHttp("/system/readiness").forPort(8085).forStatusCode(200))
            withLogConsumer(Slf4jLogConsumer(LoggerFactory.getLogger(AppContainer::class.java)))
        }

        fun getURI(): URI = URI.create("http://$host:${getMappedPort(8080)}")

        fun getSystemURI(): URI = URI.create("http://$host:${getMappedPort(8085)}")
    }
    ```

## Testcontainers { #testcontainers }

In a black-box test, the application has already been built as a separate Docker artifact. The test does not modify its Kora graph and does not add test components into the application: the container
runs the same code that was packaged during the build.

What the test can change is the container runtime environment: environment variables, network, ports, startup order, and external infrastructure. In this guide, the test starts PostgreSQL next to the
application and passes connection settings to the application through `withEnv(...)`. From the application's point of view, this is ordinary production-style configuration from the environment; the
values are simply provided by Testcontainers for the duration of the test.

Now define infrastructure lifecycle in your test class.
`@Testcontainers` enables automatic container lifecycle handling, and `@Container` marks managed containers.

In this step:

- `PostgreSQLContainer` provides a real DB
- `AppContainer` depends on Postgres startup
- app DB env values are injected from Postgres container getters
- shared network is used for container-to-container hostname access

===! ":fontawesome-brands-java: `Java`"

    Start `src/test/java/ru/tinkoff/kora/guide/testingblackbox/BlackBoxTests.java` with:

    ```java
    package ru.tinkoff.kora.guide.testingblackbox;

    import java.time.Duration;
    import org.junit.jupiter.api.Test;
    import org.slf4j.LoggerFactory;
    import org.testcontainers.containers.Network;
    import org.testcontainers.containers.PostgreSQLContainer;
    import org.testcontainers.containers.output.Slf4jLogConsumer;
    import org.testcontainers.junit.jupiter.Container;
    import org.testcontainers.junit.jupiter.Testcontainers;

    @Testcontainers
    class BlackBoxTests {

        @Container
        private static final PostgreSQLContainer<?> POSTGRES = new PostgreSQLContainer<>("postgres:16-alpine")
                .withNetwork(Network.SHARED)
                .withNetworkAliases("postgres")
                .withStartupTimeout(Duration.ofSeconds(30))
                .withLogConsumer(new Slf4jLogConsumer(LoggerFactory.getLogger(PostgreSQLContainer.class)));

        @Container
        private static final AppContainer APP = new AppContainer()
                .withNetwork(Network.SHARED)
                .dependsOn(POSTGRES)
                .withEnv("POSTGRES_JDBC_URL", "jdbc:postgresql://postgres:5432/" + POSTGRES.getDatabaseName())
                .withEnv("POSTGRES_USER", POSTGRES.getUsername())
                .withEnv("POSTGRES_PASS", POSTGRES.getPassword());
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Start `src/test/kotlin/ru/tinkoff/kora/guide/testingblackbox/BlackBoxTests.kt` with:

    ```kotlin
    package ru.tinkoff.kora.guide.testingblackbox

    import java.time.Duration
    import org.junit.jupiter.api.Test
    import org.slf4j.LoggerFactory
    import org.testcontainers.containers.Network
    import org.testcontainers.containers.PostgreSQLContainer
    import org.testcontainers.containers.output.Slf4jLogConsumer
    import org.testcontainers.junit.jupiter.Container
    import org.testcontainers.junit.jupiter.Testcontainers

    @Testcontainers
    class BlackBoxTests {

        companion object {

            @Container
            @JvmStatic
            private val POSTGRES = PostgreSQLContainer("postgres:16-alpine")
                .withNetwork(Network.SHARED)
                .withNetworkAliases("postgres")
                .withStartupTimeout(Duration.ofSeconds(30))
                .withLogConsumer(Slf4jLogConsumer(LoggerFactory.getLogger(PostgreSQLContainer::class.java)))

            @Container
            @JvmStatic
            private val APP = AppContainer()
                .withNetwork(Network.SHARED)
                .dependsOn(POSTGRES)
                .withEnv("POSTGRES_JDBC_URL", "jdbc:postgresql://postgres:5432/${POSTGRES.databaseName}")
                .withEnv("POSTGRES_USER", POSTGRES.username)
                .withEnv("POSTGRES_PASS", POSTGRES.password)
        }
    }
    ```

## Write tests { #tests }

After container wiring is ready, add HTTP scenario tests to the same `BlackBoxTests` class.
These tests verify API behavior end-to-end through the running application container.

===! ":fontawesome-brands-java: `Java`"

    Add imports:

    ```java
    import static org.junit.jupiter.api.Assertions.assertEquals;
    import static org.junit.jupiter.api.Assertions.assertTrue;

    import java.net.http.HttpClient;
    import java.net.http.HttpRequest;
    import java.net.http.HttpResponse;
    import java.util.UUID;
    import org.json.JSONArray;
    import org.json.JSONObject;
    ```

    Add test methods and helpers:

    ```java
    @Test
    void createUser_ShouldCreateAndReturnUser() throws Exception {
        var response = sendJson("POST", "/users", new JSONObject()
                .put("name", "John Doe")
                .put("email", uniqueEmail("john")));

        assertEquals(201, response.statusCode());
        var responseBody = new JSONObject(response.body());
        assertTrue(responseBody.has("id"));
        assertEquals("John Doe", responseBody.getString("name"));
    }

    @Test
    void getUser_ShouldReturnUser() throws Exception {
        var createResponse = sendJson("POST", "/users", new JSONObject()
                .put("name", "Jane Doe")
                .put("email", uniqueEmail("jane")));
        var userId = new JSONObject(createResponse.body()).getString("id");

        var getRequest = HttpRequest.newBuilder()
                .GET()
                .uri(APP.getURI().resolve("/users/" + userId))
                .timeout(Duration.ofSeconds(10))
                .build();
        var getResponse = HttpClient.newHttpClient().send(getRequest, HttpResponse.BodyHandlers.ofString());

        assertEquals(200, getResponse.statusCode());
        var body = new JSONObject(getResponse.body());
        assertEquals(userId, body.getString("id"));
        assertEquals("Jane Doe", body.getString("name"));
    }

    @Test
    void getUser_NotFound_ShouldReturn404() throws Exception {
        var request = HttpRequest.newBuilder()
                .GET()
                .uri(APP.getURI().resolve("/users/999999"))
                .timeout(Duration.ofSeconds(10))
                .build();

        var response = HttpClient.newHttpClient().send(request, HttpResponse.BodyHandlers.ofString());

        assertEquals(404, response.statusCode());
    }

    @Test
    void getUsers_WithPagination_ShouldReturnSizedResult() throws Exception {
        sendJson("POST", "/users", new JSONObject().put("name", "Alice").put("email", uniqueEmail("alice")));
        sendJson("POST", "/users", new JSONObject().put("name", "Bob").put("email", uniqueEmail("bob")));
        sendJson("POST", "/users", new JSONObject().put("name", "Charlie").put("email", uniqueEmail("charlie")));

        var request = HttpRequest.newBuilder()
                .GET()
                .uri(APP.getURI().resolve("/users?page=0&size=2&sort=name"))
                .timeout(Duration.ofSeconds(10))
                .build();
        var response = HttpClient.newHttpClient().send(request, HttpResponse.BodyHandlers.ofString());

        assertEquals(200, response.statusCode());
        var users = new JSONArray(response.body());
        assertEquals(2, users.length());
    }

    @Test
    void updateUser_ShouldUpdateAndReturnUser() throws Exception {
        var createResponse = sendJson("POST", "/users", new JSONObject()
                .put("name", "John")
                .put("email", uniqueEmail("upd")));
        var userId = new JSONObject(createResponse.body()).getString("id");

        var updateRequest = HttpRequest.newBuilder()
                .PUT(HttpRequest.BodyPublishers.ofString(new JSONObject()
                        .put("name", "John Updated")
                        .put("email", uniqueEmail("updated"))
                        .toString()))
                .uri(APP.getURI().resolve("/users/" + userId))
                .header("Content-Type", "application/json")
                .timeout(Duration.ofSeconds(10))
                .build();
        var updateResponse = HttpClient.newHttpClient().send(updateRequest, HttpResponse.BodyHandlers.ofString());

        assertEquals(200, updateResponse.statusCode());
        var body = new JSONObject(updateResponse.body());
        assertEquals("John Updated", body.getString("name"));
    }

    @Test
    void deleteUser_ShouldRemoveUser() throws Exception {
        var createResponse = sendJson("POST", "/users", new JSONObject()
                .put("name", "John")
                .put("email", uniqueEmail("del")));
        var userId = new JSONObject(createResponse.body()).getString("id");

        var deleteRequest = HttpRequest.newBuilder()
                .DELETE()
                .uri(APP.getURI().resolve("/users/" + userId))
                .timeout(Duration.ofSeconds(10))
                .build();
        var deleteResponse = HttpClient.newHttpClient().send(deleteRequest, HttpResponse.BodyHandlers.ofString());
        assertEquals(204, deleteResponse.statusCode());

        var getRequest = HttpRequest.newBuilder()
                .GET()
                .uri(APP.getURI().resolve("/users/" + userId))
                .timeout(Duration.ofSeconds(10))
                .build();
        var getResponse = HttpClient.newHttpClient().send(getRequest, HttpResponse.BodyHandlers.ofString());
        assertEquals(404, getResponse.statusCode());
    }

    private HttpResponse<String> sendJson(String method, String path, JSONObject payload) throws Exception {
        var request = HttpRequest.newBuilder()
                .uri(APP.getURI().resolve(path))
                .header("Content-Type", "application/json")
                .timeout(Duration.ofSeconds(10));

        if ("POST".equals(method)) {
            request.POST(HttpRequest.BodyPublishers.ofString(payload.toString()));
        } else if ("PUT".equals(method)) {
            request.PUT(HttpRequest.BodyPublishers.ofString(payload.toString()));
        } else {
            throw new IllegalArgumentException("Unsupported method: " + method);
        }

        return HttpClient.newHttpClient().send(request.build(), HttpResponse.BodyHandlers.ofString());
    }

    private String uniqueEmail(String prefix) {
        return prefix + "-" + UUID.randomUUID() + "@example.com";
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Add imports:

    ```kotlin
    import java.net.http.HttpClient
    import java.net.http.HttpRequest
    import java.net.http.HttpResponse
    import java.util.UUID
    import org.json.JSONArray
    import org.json.JSONObject
    import org.junit.jupiter.api.Assertions.assertEquals
    import org.junit.jupiter.api.Assertions.assertTrue
    ```

    Add test methods and helpers:

    ```kotlin
    @Test
    fun createUserShouldCreateAndReturnUser() {
        val response = sendJson("POST", "/users", JSONObject()
            .put("name", "John Doe")
            .put("email", uniqueEmail("john")))

        assertEquals(201, response.statusCode())
        val body = JSONObject(response.body())
        assertTrue(body.has("id"))
        assertEquals("John Doe", body.getString("name"))
    }

    @Test
    fun getUserShouldReturnUser() {
        val createResponse = sendJson("POST", "/users", JSONObject()
            .put("name", "Jane Doe")
            .put("email", uniqueEmail("jane")))
        val userId = JSONObject(createResponse.body()).getString("id")

        val getRequest = HttpRequest.newBuilder()
            .GET()
            .uri(APP.getURI().resolve("/users/$userId"))
            .timeout(Duration.ofSeconds(10))
            .build()
        val getResponse = HttpClient.newHttpClient().send(getRequest, HttpResponse.BodyHandlers.ofString())

        assertEquals(200, getResponse.statusCode())
        val body = JSONObject(getResponse.body())
        assertEquals(userId, body.getString("id"))
        assertEquals("Jane Doe", body.getString("name"))
    }

    @Test
    fun getUserNotFoundShouldReturn404() {
        val request = HttpRequest.newBuilder()
            .GET()
            .uri(APP.getURI().resolve("/users/999999"))
            .timeout(Duration.ofSeconds(10))
            .build()

        val response = HttpClient.newHttpClient().send(request, HttpResponse.BodyHandlers.ofString())
        assertEquals(404, response.statusCode())
    }

    @Test
    fun getUsersWithPaginationShouldReturnSizedResult() {
        sendJson("POST", "/users", JSONObject().put("name", "Alice").put("email", uniqueEmail("alice")))
        sendJson("POST", "/users", JSONObject().put("name", "Bob").put("email", uniqueEmail("bob")))
        sendJson("POST", "/users", JSONObject().put("name", "Charlie").put("email", uniqueEmail("charlie")))

        val request = HttpRequest.newBuilder()
            .GET()
            .uri(APP.getURI().resolve("/users?page=0&size=2&sort=name"))
            .timeout(Duration.ofSeconds(10))
            .build()
        val response = HttpClient.newHttpClient().send(request, HttpResponse.BodyHandlers.ofString())

        assertEquals(200, response.statusCode())
        val users = JSONArray(response.body())
        assertEquals(2, users.length())
    }

    @Test
    fun updateUserShouldUpdateAndReturnUser() {
        val createResponse = sendJson("POST", "/users", JSONObject()
            .put("name", "John")
            .put("email", uniqueEmail("upd")))
        val userId = JSONObject(createResponse.body()).getString("id")

        val updateRequest = HttpRequest.newBuilder()
            .PUT(HttpRequest.BodyPublishers.ofString(JSONObject()
                .put("name", "John Updated")
                .put("email", uniqueEmail("updated"))
                .toString()))
            .uri(APP.getURI().resolve("/users/$userId"))
            .header("Content-Type", "application/json")
            .timeout(Duration.ofSeconds(10))
            .build()
        val updateResponse = HttpClient.newHttpClient().send(updateRequest, HttpResponse.BodyHandlers.ofString())

        assertEquals(200, updateResponse.statusCode())
        val body = JSONObject(updateResponse.body())
        assertEquals("John Updated", body.getString("name"))
    }

    @Test
    fun deleteUserShouldRemoveUser() {
        val createResponse = sendJson("POST", "/users", JSONObject()
            .put("name", "John")
            .put("email", uniqueEmail("del")))
        val userId = JSONObject(createResponse.body()).getString("id")

        val deleteRequest = HttpRequest.newBuilder()
            .DELETE()
            .uri(APP.getURI().resolve("/users/$userId"))
            .timeout(Duration.ofSeconds(10))
            .build()
        val deleteResponse = HttpClient.newHttpClient().send(deleteRequest, HttpResponse.BodyHandlers.ofString())
        assertEquals(204, deleteResponse.statusCode())

        val getRequest = HttpRequest.newBuilder()
            .GET()
            .uri(APP.getURI().resolve("/users/$userId"))
            .timeout(Duration.ofSeconds(10))
            .build()
        val getResponse = HttpClient.newHttpClient().send(getRequest, HttpResponse.BodyHandlers.ofString())
        assertEquals(404, getResponse.statusCode())
    }

    private fun sendJson(method: String, path: String, payload: JSONObject): HttpResponse<String> {
        val requestBuilder = HttpRequest.newBuilder()
            .uri(APP.getURI().resolve(path))
            .header("Content-Type", "application/json")
            .timeout(Duration.ofSeconds(10))

        when (method) {
            "POST" -> requestBuilder.POST(HttpRequest.BodyPublishers.ofString(payload.toString()))
            "PUT" -> requestBuilder.PUT(HttpRequest.BodyPublishers.ofString(payload.toString()))
            else -> throw IllegalArgumentException("Unsupported method: $method")
        }

        return HttpClient.newHttpClient().send(requestBuilder.build(), HttpResponse.BodyHandlers.ofString())
    }

    private fun uniqueEmail(prefix: String): String = "$prefix-${UUID.randomUUID()}@example.com"
    ```

!!! tip "Black Box Testing Benefits"

    Why prioritize black box testing?

    - Real User Experience: Tests actual HTTP APIs as users would use them
    - Integration Validation: Catches issues between components, serialization, etc.
    - Contract Verification: Ensures API contracts are maintained
    - Deployment Confidence: Validates complete application behavior
    - Regression Prevention: Catches breaking changes in user-facing behavior

!!! note "Container Management"

    The `AppContainer` pattern provides:

    - Dockerfile-based Testing: Tests your actual application image
    - Environment Isolation: Fresh container per test run
    - Health Check Integration: Waits for application readiness
    - Port Management: Automatic port mapping and URI construction
    - Log Integration: Application logs available in test output

## Testing { #testing }

Run your black box tests using Gradle:

```bash
# Run all tests including black box tests
./gradlew test

# Run with verbose output
./gradlew test --info
```

!!! tip "Test Execution Tips"

    - Docker Required: Black box tests require Docker to run containers
    - Network Access: Tests may take longer due to container startup
    - Resource Intensive: Consider running black box tests separately from unit tests
    - Parallel Execution: Black box tests typically run sequentially due to container conflicts

## Best Practices { #best-practices }

Test Organization:

- API Contract Tests: Test each endpoint's contract (request/response format)
- Business Logic Tests: Test complete user workflows and business rules
- Error Scenario Tests: Test error conditions and edge cases
- Integration Tests: Test interactions between services

Test Data Management:

- Isolated Test Data: Each test should create its own test data
- Cleanup Strategy: Use database cleanup or fresh containers between tests
- Realistic Data: Use realistic test data that matches production patterns
- Data Validation: Verify data persistence and retrieval

Performance Considerations:

- Container Reuse: Consider reusing containers when possible to reduce startup time
- Parallel Execution: Run black box tests in parallel when containers allow it
- Resource Limits: Set appropriate resource limits for test containers
- Timeout Management: Configure appropriate timeouts for HTTP requests

Debugging Black Box Tests:

- Container Logs: Access container logs for debugging application issues
- Network Inspection: Use tools like Wireshark to inspect HTTP traffic
- Database Inspection: Query test databases directly for data validation
- Application Metrics: Monitor application metrics during test execution

## Summary { #summary }

Black box testing provides the highest confidence in your Kora application's correctness by testing the complete user experience through HTTP APIs. By using the `AppContainer` pattern with
Testcontainers, you can create realistic, isolated test environments that validate your application's behavior end-to-end.

Key takeaways:

- Black Box First: Kora recommends black box testing as the primary testing strategy
- Containerized Testing: Use Docker containers for realistic test environments
- API Contract Validation: Test complete HTTP API contracts
- End-to-End Validation: Test complete user workflows and business logic
- Isolation: Each test gets a fresh environment with proper cleanup

Black box tests complement component and integration tests by providing the final validation that your application works correctly from the user's perspective.

## Key Concepts { #key-concepts }

Black Box Testing Strategy:

- Black Box First: Kora's recommended primary testing approach for highest confidence
- End-to-End Validation: Test complete user workflows through HTTP APIs
- API Contract Testing: Validate complete request/response cycles
- User Perspective Testing: Test application behavior as users experience it

AppContainer Pattern:

- Containerized Applications: Run complete applications in Docker containers
- Realistic Environments: Test with actual infrastructure and dependencies
- Network Isolation: Each test gets dedicated ports and network configuration
- Automatic Lifecycle: Containers start/stop automatically with test execution

HTTP API Testing:

- Complete Request Flow: Test from HTTP request to database and back
- Status Code Validation: Verify correct HTTP response codes
- Response Content Validation: Check JSON responses and data correctness
- Error Handling: Test error scenarios and proper error responses

Test Isolation and Performance:

- Fresh Environments: Each test starts with clean database and application state
- Resource Cleanup: Automatic cleanup of containers and connections
- Parallel Execution: Tests can run concurrently for faster execution
- Realistic Load: Test with actual network calls and database operations

## Troubleshooting { #troubleshooting }

AppContainer Not Starting:

- Ensure Docker is running and accessible
- Check that application JAR is built and available
- Verify Docker image configuration and base images
- Check container logs for startup errors

HTTP Connection Issues:

- Ensure application container is fully started before tests run
- Check that HTTP port is correctly exposed and mapped
- Verify network configuration between test and application containers
- Check application logs for HTTP server startup issues

Port Conflicts:

- Ensure each test uses unique ports for application containers
- Check that ports are not already in use by other processes
- Use dynamic port allocation to avoid conflicts
- Verify port cleanup after test completion

!!! tip "Flyway Migrations in Tests"

    You can execute Flyway migrations from test setup code instead of relying on Flyway auto-run inside the application container.
    This is useful when you want explicit migration control in test lifecycle (for example, schema reset per suite).
    In this guide we use application startup migrations to keep black-box setup straightforward, but test-driven migrations are also a valid approach.

Database Setup Problems:

- Ensure database container starts before application container
- Check database connection configuration in application
- Verify database schema initialization scripts run correctly
- Check database container logs for startup or connection errors

Test Timeouts:

- Increase timeout values for slow-starting containers
- Check application startup time and adjust wait strategies
- Verify network connectivity between containers
- Monitor resource usage (CPU/memory) during test execution

Container Cleanup Issues:

- Ensure proper cleanup in test teardown methods
- Check for hanging processes after test completion
- Verify Docker daemon has sufficient resources
- Use Testcontainers' automatic cleanup features

## What's Next? { #whats-next }

- [Observability](observability.md) to expose probes, metrics, traces, and logs for the packaged application you now test end to end.
- [Resilient Patterns](resilient.md) to verify failure handling through HTTP-facing scenarios.
- [OpenAPI HTTP Server](openapi-http-server.md) to move from handwritten endpoints to contract-first generated transport.
- [HTTP Client](http-client.md) to test service-to-service calls against a running server.

## Help { #help }

If you encounter issues:

- compare black-box tests with [Kora Java Database JDBC App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-database-jdbc-app) and [Kora Kotlin Database JDBC App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-database-jdbc-app)
- check the [JUnit5 documentation](../documentation/junit5.md)
- check the [Database Migration documentation](../documentation/database-migration.md)
- read the [Testcontainers documentation](https://www.testcontainers.org/)
