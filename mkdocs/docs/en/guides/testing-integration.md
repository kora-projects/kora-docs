---
search:
  exclude: true
title: Integration Testing with Kora
summary: Learn comprehensive integration testing for Kora JDBC applications with real PostgreSQL, Flyway migrations, and KoraAppTest
tags: testing, integration-tests, testcontainers, postgres, flyway
---

# Integration Testing with Kora { #integration-testing-kora }

This guide introduces integration testing for Kora JDBC applications. It covers how to run the application graph against real PostgreSQL infrastructure, how Testcontainers supplies database connection
settings, and how repositories, migrations, configuration, and services are verified together. You will also see how integration tests catch wiring and persistence issues that unit tests intentionally
avoid.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java Testing Integration App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-testing-integration-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin Testing Integration App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-testing-integration-app).

## What You'll Build { #youll-build }

You'll create integration tests that cover:

- **Real Database Validation**: Run tests against a real PostgreSQL instance
- **Migration Verification**: Ensure Flyway migrations are applied correctly
- **Service + Repository Integration**: Verify complete persistence workflows
- **Configuration Override Testing**: Inject runtime configuration from containers
- **Deterministic Test Isolation**: Clean and repeatable test behavior

## What You'll Need { #youll-need }

- JDK 17 or later
- Gradle 7+
- Docker (for Testcontainers)
- A text editor or IDE
- Completed [Database Integration](database-jdbc.md) guide

## Prerequisites { #prerequisites }

!!! note "Required: Complete Database JDBC Guide"

    This guide assumes you have completed **[Database Integration](database-jdbc.md)** and already have a JDBC repository implementation, Flyway migrations in `db/migration`, `UserService` wired to the real JDBC repository, and working CRUD behavior in your database-backed application.

    If you haven't completed the database JDBC guide yet, do that first, because this guide verifies the real database-backed service flow with Testcontainers.

## Overview { #overview }

Integration testing validates how application code behaves when it works with real infrastructure. It sits between component tests and black-box tests: broader than a mocked service test, but narrower
than starting the entire application as an external process.

The key difference from a component test is that infrastructure is part of the behavior being tested. A repository method is not fully proven until its SQL runs against the same kind of database the
application uses.

### Integration Boundary { #integration-boundary }

In this guide, the integration boundary is the service and repository layer backed by a real [PostgreSQL](https://www.postgresql.org/docs/) database. The test still runs inside
the [JUnit](https://junit.org/junit5/docs/current/user-guide/) process and uses the Kora test graph, but the database is not mocked. That lets the test validate behavior that only exists when SQL,
migrations, connection configuration, and row mapping all work together.

Integration tests are especially valuable for:

- real SQL execution against PostgreSQL
- record and column mapping
- Flyway migration compatibility with repository code
- pagination, sorting, update, and delete behavior against real data
- service logic that depends on persistence semantics

### Tests and Testcontainers { #tests-plus-testcontainers }

For more on extended test graphs, component replacement, and container modification, see [Test graph](../documentation/junit5.md#test-graph) and [Container modification](../documentation/junit5.md#container-modification).

Kora provides the application graph; [Testcontainers](https://java.testcontainers.org/) provides disposable infrastructure. The test starts a PostgreSQL container, passes its connection values into
the graph, and then exercises application components with real database state.

This combination is powerful because the repository code is generated and wired the same way it is in the application, while the database is isolated per test run. You get realistic persistence
behavior without requiring a manually prepared local database.

### Integration or Black Box { #integration-black-box-tests }

Integration tests usually call components directly. Black-box tests call the public API of the running application. That means integration tests are better for focused persistence feedback, while
black-box tests are better for proving the full request path.

Use integration tests when the question is "does this application logic work with real infrastructure?" Use black-box tests when the question is "does the deployed application behave correctly from a
client's point of view?"

The practical flow is:

1. add Kora test and Testcontainers dependencies
2. start PostgreSQL with Testcontainers
3. pass container connection settings into the Kora graph
4. run migrations against the test database
5. call graph-managed services and repositories
6. verify persistence behavior with real database state

## Dependencies { #dependencies }

In this guide, tests live in a separate Gradle module instead of the application module itself. That is why the dependency list is longer than it would be for a usual `src/test` placed next to
production code: the test module must explicitly depend on the application and on the Kora modules required to build the test graph, read configuration, use JDBC, run Flyway, work with JSON, include
HTTP modules, and initialize logging.

These dependencies do not arrive transitively from the service as a complete test runtime. The service module exposes its API and compiled code, but a separate test module still declares which parts
should be present in the test runtime. If these integration tests lived directly inside the application module, most of these dependencies would already be available from the main `build.gradle`, so
you would not need to repeat them in this amount.

===! ":fontawesome-brands-java: `Java`"

    Add the following test dependencies to your `build.gradle`:

    ```groovy title="build.gradle"
    dependencies {
        testImplementation platform("org.junit:junit-bom:5.14.3")

        testRuntimeOnly "org.postgresql:postgresql:42.7.7"

        testImplementation "org.junit.jupiter:junit-jupiter"
        testImplementation project(":guide-database-jdbc-app")
        testImplementation "ru.tinkoff.kora:config-hocon"
        testImplementation "ru.tinkoff.kora:database-flyway"
        testImplementation "ru.tinkoff.kora:database-jdbc"
        testImplementation "ru.tinkoff.kora:http-client-common"
        testImplementation "ru.tinkoff.kora:http-server-undertow"
        testImplementation "ru.tinkoff.kora:json-module"
        testImplementation "ru.tinkoff.kora:logging-logback"
        testImplementation "ru.tinkoff.kora:test-junit5"
        testImplementation "org.testcontainers:junit-jupiter:1.21.4"
        testImplementation "org.testcontainers:postgresql:1.21.4"
    }

    test {
        useJUnitPlatform()
        filter {
            excludeTestsMatching '*$*'
            excludeTestsMatching "*TestApplication"
        }
        testLogging {
            showStandardStreams(true)
            events("passed", "skipped", "failed")
            exceptionFormat("full")
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Add the following test dependencies to your `build.gradle.kts`:

    ```kotlin title="build.gradle.kts"
    dependencies {
        testImplementation(platform("org.junit:junit-bom:5.14.3"))

        testRuntimeOnly("org.postgresql:postgresql:42.7.7")

        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation(project(":guide-database-jdbc-app"))
        testImplementation("ru.tinkoff.kora:config-hocon")
        testImplementation("ru.tinkoff.kora:database-flyway")
        testImplementation("ru.tinkoff.kora:database-jdbc")
        testImplementation("ru.tinkoff.kora:http-client-common")
        testImplementation("ru.tinkoff.kora:http-server-undertow")
        testImplementation("ru.tinkoff.kora:json-module")
        testImplementation("ru.tinkoff.kora:logging-logback")
        testImplementation("ru.tinkoff.kora:test-junit5")
        testImplementation("org.testcontainers:junit-jupiter:1.21.4")
        testImplementation("org.testcontainers:postgresql:1.21.4")
    }

    tasks.test {
        useJUnitPlatform()
        filter {
            excludeTestsMatching('*$*')
            excludeTestsMatching("*TestApplication")
        }
        testLogging {
            showStandardStreams = true
            events("passed", "skipped", "failed")
            exceptionFormat = org.gradle.api.tasks.testing.logging.TestExceptionFormat.FULL
        }
    }
    ```

!!! note "Enable Submodule Generation In JDBC Application"

    Add submodule generation to the **real application graph** (`guide-database-jdbc-app`), not to test compilation.

    ===! ":fontawesome-brands-java: `Java`"

        Add to `guide-database-jdbc-app/build.gradle`:

        ```groovy title="guide-database-jdbc-app/build.gradle"
        tasks.named("compileJava", JavaCompile) {
            options.compilerArgs += ['-Akora.app.submodule.enabled=true']
        }
        ```

    === ":simple-kotlin: `Kotlin`"

        Add to `guide-kotlin-database-jdbc-app/build.gradle.kts`:

        ```kotlin title="guide-kotlin-database-jdbc-app/build.gradle.kts"
        ksp {
            arg("kora.app.submodule.enabled", "true")
        }
        ```

## Test Graph { #test-graph }

Before writing integration test methods, create a dedicated `TestApplication`.
It extends your production `Application`, but adds a **test-only repository** with `deleteAll()` for cleanup.
This keeps production `UserRepository` focused on application behavior and moves test utilities into test scope.

===! ":fontawesome-brands-java: `Java`"

    Create `src/test/java/ru/tinkoff/kora/guide/testingintegration/TestApplication.java`:

    ```java
    package ru.tinkoff.kora.guide.testingintegration;

    import java.util.List;
    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.common.Tag;
    import ru.tinkoff.kora.common.annotation.Root;
    import ru.tinkoff.kora.database.common.annotation.Query;
    import ru.tinkoff.kora.database.common.annotation.Repository;
    import ru.tinkoff.kora.database.jdbc.JdbcRepository;
    import ru.tinkoff.kora.guide.databasejdbc.Application;
    import ru.tinkoff.kora.guide.databasejdbc.repository.UserDAO;

    @KoraApp
    public interface TestApplication extends Application {

        @Repository
        interface TestUserRepository extends JdbcRepository {

            @Query("SELECT id, name, email, created_at FROM users ORDER BY id")
            List<UserDAO> findAll();

            @Query("DELETE FROM users")
            void deleteAll();
        }

        @Tag(TestApplication.class)
        @Root
        default String testRoot(TestUserRepository ignored) {
            return "test-root";
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/test/kotlin/ru/tinkoff/kora/guide/testingintegration/TestApplication.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.testingintegration

    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.common.Tag
    import ru.tinkoff.kora.common.annotation.Root
    import ru.tinkoff.kora.database.common.annotation.Query
    import ru.tinkoff.kora.database.common.annotation.Repository
    import ru.tinkoff.kora.database.jdbc.JdbcRepository
    import ru.tinkoff.kora.guide.databasejdbc.Application
    import ru.tinkoff.kora.guide.databasejdbc.repository.UserDAO

    @KoraApp
    interface TestApplication : Application {

        @Repository
        interface TestUserRepository : JdbcRepository {

            @Query("SELECT id, name, email, created_at FROM users ORDER BY id")
            fun findAll(): List<UserDAO>

            @Query("DELETE FROM users")
            fun deleteAll()
        }

        @Tag(TestApplication::class)
        @Root
        fun testRoot(ignored: TestUserRepository): String = "test-root"
    }
    ```

Now create the integration test foundation with:

- `@Testcontainers` to manage container lifecycle
- `PostgreSQLContainer` as a real database for integration checks
- explicit startup timeout and container log consumer for easier debugging
- `@KoraAppTest(TestApplication...)` for bootstrapping the test graph
- runtime config override using container JDBC values

===! ":fontawesome-brands-java: `Java`"

    Create `src/test/java/ru/tinkoff/kora/guide/testingintegration/UserServiceIntegrationPostgresTest.java`:

    ```java
    package ru.tinkoff.kora.guide.testingintegration;

    import java.time.Duration;
    import org.jetbrains.annotations.NotNull;
    import org.junit.jupiter.api.BeforeEach;
    import org.slf4j.LoggerFactory;
    import org.testcontainers.containers.PostgreSQLContainer;
    import org.testcontainers.containers.output.Slf4jLogConsumer;
    import org.testcontainers.junit.jupiter.Container;
    import org.testcontainers.junit.jupiter.Testcontainers;
    import ru.tinkoff.kora.guide.databasejdbc.service.UserService;
    import ru.tinkoff.kora.guide.testingintegration.TestApplication.TestUserRepository;
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTest;
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTestConfigModifier;
    import ru.tinkoff.kora.test.extension.junit5.KoraConfigModification;
    import ru.tinkoff.kora.test.extension.junit5.TestComponent;

    @Testcontainers
    @KoraAppTest(TestApplication.class)
    class UserServiceIntegrationPostgresTest implements KoraAppTestConfigModifier {

        @Container
        static final PostgreSQLContainer<?> POSTGRES =
                new PostgreSQLContainer<>("postgres:16-alpine")
                        .withStartupTimeout(Duration.ofSeconds(30))
                        .withLogConsumer(new Slf4jLogConsumer(LoggerFactory.getLogger(PostgreSQLContainer.class)));

        @TestComponent
        private UserService userService;

        @TestComponent
        private TestUserRepository testUserRepository;

        @NotNull
        @Override
        public KoraConfigModification config() {
            return KoraConfigModification.ofString("""
                    db {
                      jdbcUrl = ${POSTGRES_JDBC_URL}
                      username = ${POSTGRES_USER}
                      password = ${POSTGRES_PASS}
                      poolName = "kora-test"
                    }
                    flyway {
                      locations = "db/migration"
                    }
                    """)
                    .withSystemProperty("POSTGRES_JDBC_URL", POSTGRES.getJdbcUrl())
                    .withSystemProperty("POSTGRES_USER", POSTGRES.getUsername())
                    .withSystemProperty("POSTGRES_PASS", POSTGRES.getPassword());
        }

        @BeforeEach
        void cleanup() {
            testUserRepository.deleteAll();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/test/kotlin/ru/tinkoff/kora/guide/testingintegration/UserServiceIntegrationPostgresTest.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.testingintegration

    import java.time.Duration
    import org.junit.jupiter.api.BeforeEach
    import org.slf4j.LoggerFactory
    import org.testcontainers.containers.PostgreSQLContainer
    import org.testcontainers.containers.output.Slf4jLogConsumer
    import org.testcontainers.junit.jupiter.Container
    import org.testcontainers.junit.jupiter.Testcontainers
    import ru.tinkoff.kora.guide.databasejdbc.service.UserService
    import ru.tinkoff.kora.guide.testingintegration.TestApplication.TestUserRepository
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTest
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTestConfigModifier
    import ru.tinkoff.kora.test.extension.junit5.KoraConfigModification
    import ru.tinkoff.kora.test.extension.junit5.TestComponent

    @Testcontainers
    @KoraAppTest(TestApplication::class)
    class UserServiceIntegrationPostgresTest : KoraAppTestConfigModifier {

        companion object {
            @Container
            @JvmStatic
            val POSTGRES = PostgreSQLContainer("postgres:16-alpine")
                .withStartupTimeout(Duration.ofSeconds(30))
                .withLogConsumer(Slf4jLogConsumer(LoggerFactory.getLogger(PostgreSQLContainer::class.java)))
        }

        @TestComponent
        lateinit var userService: UserService

        @TestComponent
        lateinit var testUserRepository: TestUserRepository

        override fun config(): KoraConfigModification {
            return KoraConfigModification.ofString(
                """
                db {
                  jdbcUrl = \${POSTGRES_JDBC_URL}
                  username = \${POSTGRES_USER}
                  password = \${POSTGRES_PASS}
                  poolName = "kora-test"
                }
                flyway {
                  locations = "db/migration"
                }
                """.trimIndent()
            )
                .withSystemProperty("POSTGRES_JDBC_URL", POSTGRES.jdbcUrl)
                .withSystemProperty("POSTGRES_USER", POSTGRES.username)
                .withSystemProperty("POSTGRES_PASS", POSTGRES.password)
        }

        @BeforeEach
        fun cleanup() {
            testUserRepository.deleteAll()
        }
    }
    ```

`config()` in this test replaces configuration, not application code. `KoraConfigModification.ofString(...)` first adds a small HOCON fragment with the `db` and `flyway` settings required by the JDBC
pool and migrations. The connection values are not hardcoded into the config string; they are expressed as `${POSTGRES_JDBC_URL}`, `${POSTGRES_USER}`, and `${POSTGRES_PASS}` placeholders.

Then `withSystemProperty(...)` provides real values from the running `PostgreSQLContainer`. Testcontainers may allocate a different port, username, or password for each run, so the test should not
assume a fixed `localhost:5432`. When Kora reads configuration, these placeholders are resolved through system properties, and the graph receives a normal `JdbcDatabase` connected to the disposable
database of this specific test run.

This is useful in several ways: production configuration does not change for tests, tests do not depend on a developer's local database, and the same application code is verified against real
PostgreSQL and real migrations. At the same time, you can override only the settings that matter without rewriting the entire configuration file.

## Write tests { #tests }

Now add real integration test methods to the same `UserServiceIntegrationPostgresTest` class.
The container is intentionally configured with explicit startup timeout and attached logs to make startup issues diagnosable.
These methods validate service behavior and persisted state against real PostgreSQL.

===! ":fontawesome-brands-java: `Java`"

    Add imports:

    ```java
    import static org.junit.jupiter.api.Assertions.assertEquals;
    import static org.junit.jupiter.api.Assertions.assertTrue;

    import java.util.List;
    import org.junit.jupiter.api.Test;
    import ru.tinkoff.kora.guide.databasejdbc.dto.UserRequest;
    ```

    Add test methods:

    ```java
    @Test
    void createUser_ShouldPersistUserInDatabase() {
        var result = userService.createUser(new UserRequest("John", "john@example.com"));

        assertEquals("John", result.name());
        assertTrue(Long.parseLong(result.id()) > 0);
        assertEquals(1, testUserRepository.findAll().size());
    }

    @Test
    void getUsers_WithPagination_ShouldReturnCorrectPage() {
        List.of(
                        new UserRequest("Alice", "alice@example.com"),
                        new UserRequest("Bob", "bob@example.com"),
                        new UserRequest("Charlie", "charlie@example.com"),
                        new UserRequest("David", "david@example.com"))
                .forEach(userService::createUser);

        var result = userService.getUsers(1, 2, "name");

        assertEquals(2, result.size());
        assertEquals("Charlie", result.get(0).name());
        assertEquals("David", result.get(1).name());
    }

    @Test
    void updateUser_ShouldUpdateUserInDatabase() {
        var created = userService.createUser(new UserRequest("John", "john@example.com"));

        var updated = userService.updateUser(created.id(), new UserRequest("John Updated", "john.updated@example.com"));

        assertEquals("John Updated", updated.name());
    }

    @Test
    void deleteUser_ShouldRemoveUserFromDatabase() {
        var created = userService.createUser(new UserRequest("John", "john@example.com"));

        userService.deleteUser(created.id());

        assertEquals(0, testUserRepository.findAll().size());
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Add imports:

    ```kotlin
    import org.junit.jupiter.api.Assertions.assertEquals
    import org.junit.jupiter.api.Assertions.assertTrue
    import org.junit.jupiter.api.Test
    import ru.tinkoff.kora.guide.databasejdbc.dto.UserRequest
    ```

    Add test methods:

    ```kotlin
    @Test
    fun createUserShouldPersistUserInDatabase() {
        val result = userService.createUser(UserRequest("John", "john@example.com"))

        assertEquals("John", result.name())
        assertTrue(result.id().toLong() > 0)
        assertEquals(1, testUserRepository.findAll().size)
    }

    @Test
    fun getUsersWithPaginationShouldReturnCorrectPage() {
        listOf(
            UserRequest("Alice", "alice@example.com"),
            UserRequest("Bob", "bob@example.com"),
            UserRequest("Charlie", "charlie@example.com"),
            UserRequest("David", "david@example.com")
        ).forEach(userService::createUser)

        val result = userService.getUsers(1, 2, "name")

        assertEquals(2, result.size)
        assertEquals("Charlie", result[0].name())
        assertEquals("David", result[1].name())
    }

    @Test
    fun updateUserShouldUpdateUserInDatabase() {
        val created = userService.createUser(UserRequest("John", "john@example.com"))

        val updated = userService.updateUser(created.id(), UserRequest("John Updated", "john.updated@example.com"))

        assertEquals("John Updated", updated.name())
    }

    @Test
    fun deleteUserShouldRemoveUserFromDatabase() {
        val created = userService.createUser(UserRequest("John", "john@example.com"))

        userService.deleteUser(created.id())

        assertEquals(0, testUserRepository.findAll().size)
    }
    ```

## Testing { #testing }

Run your integration tests using Gradle:

```bash
# Run all tests
./gradlew test

# Run with detailed logs
./gradlew test --info
```

!!! tip "Execution Notes"

    - Docker must be running before test start.
    - The first run is usually slower due to image pulls.
    - Keep test logging enabled to simplify startup and migration diagnostics.

## Test Coverage { #coverage }

Use standard Gradle reporting for integration test diagnostics:

```bash
# Execute tests and generate reports
./gradlew test

# Generate JaCoCo coverage report
./gradlew jacocoTestReport
```

Integration failures are typically easiest to debug from:

- `build/reports/tests/test/index.html`
- container startup logs in Gradle output
- SQL/migration logs from Flyway and JDBC components

!!! tip "Flyway Migrations in Tests"

    You can run Flyway migrations directly in test lifecycle instead of relying on Flyway startup inside the application.
    This approach is useful when you want stricter control over schema setup per test suite or per test class.
    In this guide we keep Flyway migration in application startup for simplicity, but both approaches are valid.

## Best Practices { #best-practices }

**Integration Test Design:**

- Keep test scenarios business-focused (create, read, update, delete, pagination)
- Validate both service response and database state
- Use deterministic ordering fields for pagination checks
- Avoid hidden coupling between tests

**Data Isolation:**

- Clean test data in `@BeforeEach`
- Use unique test records where collisions are possible
- Do not depend on IDs from previous test methods
- Keep each test independently executable

**Infrastructure Stability:**

- Use explicit startup timeouts for containers
- Always inject JDBC URL/user/password from container getters
- Keep Flyway locations explicit in test config
- Prefer container defaults over hardcoded DB credentials

## Summary { #summary }

Integration testing gives high confidence that your Kora JDBC application behaves correctly with real PostgreSQL and real migrations. It validates the persistence layer, DI wiring, and service
behavior under realistic conditions while remaining faster and narrower than full black box API testing.

In this guide you configured:

- Testcontainers-based PostgreSQL setup
- Kora configuration overrides for runtime container values
- Real `UserService` integration validation with test-only repository helpers
- Repeatable cleanup and deterministic test execution

## Key Concepts { #key-concepts }

**Integration Testing Scope:**

- Real infrastructure, real SQL, real migrations
- Focus on service + repository + DB behavior
- Strong confidence for persistence workflows

**Kora Test Infrastructure:**

- `@KoraAppTest` for bootstrapping real application graph
- `@TestComponent` for injecting tested components
- `KoraAppTestConfigModifier` for runtime configuration overrides

**Container-Driven Configuration:**

- Pull connection details from `PostgreSQLContainer`
- Provide values via `withSystemProperty(...)`
- Keep config portable across environments

## Troubleshooting { #troubleshooting }

**Container Startup Fails:**

- Ensure Docker daemon is running
- Check port/resource conflicts in container logs
- Increase startup timeout if environment is slow

**Migration Errors:**

- Verify migrations are under `src/main/resources/db/migration`
- Ensure `flyway.locations = "db/migration"` is present in test config
- Check Flyway output in Gradle logs

**Database Connectivity Issues:**

- Use JDBC URL/credentials from container getters only
- Avoid hardcoded localhost credentials in test config
- Ensure PostgreSQL driver is available in test runtime
- Add explicit database-jdbc and database-flyway test dependencies when TestApplication extends another module's app graph

**Flaky or Hanging Tests:**

- Keep `testLogging` with `showStandardStreams(true)`
- Use your IDE's test runner for focused debugging when needed
- Validate cleanup logic and test isolation assumptions

**`Expected @KoraApp as SubModule` Warning:**

If your test module extends `Application` from another module and you see warnings like:

- `Expected @KoraApp as SubModule, but Submodule implementation not found`

enable submodule generation on the **source application module**:

===! ":fontawesome-brands-java: `Java`"

    Add to `guide-database-jdbc-app/build.gradle`:

    ```groovy title="guide-database-jdbc-app/build.gradle"
    tasks.named("compileJava", JavaCompile) {
        options.compilerArgs += ["-Akora.app.submodule.enabled=true"]
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Add to `guide-kotlin-database-jdbc-app/build.gradle.kts`:

    ```kotlin title="guide-kotlin-database-jdbc-app/build.gradle.kts"
    ksp {
        arg("kora.app.submodule.enabled", "true")
    }
    ```

**JUnit Discovers Generated `$TestApplicationImpl`:**

If test discovery fails before execution (for example with `NoClassDefFoundError` coming from generated classes), exclude generated classes using Gradle test filter:

===! ":fontawesome-brands-java: `Java`"

    Add to `build.gradle`:

    ```groovy title="build.gradle"
    test {
        useJUnitPlatform()
        filter {
            excludeTestsMatching '*$*'
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Add to `build.gradle.kts`:

    ```kotlin title="build.gradle.kts"
    tasks.test {
        useJUnitPlatform()
        filter {
            excludeTestsMatching("*${'$'}*")
        }
    }
    ```

**AccessDeniedException in Gradle Cache:**

On Windows this may happen when cached JARs are temporarily locked by another process.

Try in order:

1. Stop daemons: `./gradlew --stop`
2. Re-run build: `./gradlew test`
3. If lock persists, run with isolated cache for the session:
   `GRADLE_USER_HOME=.gradle-user-home ./gradlew test`

## What's Next? { #whats-next }

- [Black Box Testing](testing-black-box.md) to move from graph-level integration tests to packaged application tests.
- [Observability](observability.md) to monitor the same database-backed app with metrics, traces, logs, and probes.
- [Advanced JDBC](database-jdbc-advanced.md) if you want more repository, transaction, mapper, and projection scenarios to test.
- [Caching](cache.md) when repeated database reads need a performance layer.

## Help { #help }

If you encounter issues:

- compare integration tests with [Kora Java Database JDBC App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-database-jdbc-app) and [Kora Kotlin Database JDBC App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-database-jdbc-app)
- check the [JUnit5 documentation](../documentation/junit5.md)
- check the [Database JDBC documentation](../documentation/database-jdbc.md)
- check the [Database Migration documentation](../documentation/database-migration.md)
- read the [Testcontainers documentation](https://www.testcontainers.org/)
