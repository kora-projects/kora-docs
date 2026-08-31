---
search:
  exclude: true
title: Integration Testing with Kora
summary: Learn comprehensive integration testing for Kora JDBC applications with real PostgreSQL, Flyway migrations, and KoraAppTest
description: "Integration testing for Kora 2.0 JDBC applications: a test-scope @KoraApp that extends the production application, io.koraframework:test-junit5 with @KoraAppTest and @TestComponent, Testcontainers 2.0 PostgreSQLContainer, KoraAppTestConfigModifier feeding the jdbc and flyway configuration sections through withSystemProperty, Flyway dialect artifacts and the kora.app.submodule.enabled processor option."
agent:
  use_when: "Use this file for questions about running Kora 2.0 components against a real database in tests: a test-scope @KoraApp extending the application graph, @KoraAppTest with a Testcontainers PostgreSQLContainer, KoraConfigModification.ofString with the jdbc section and ${PLACEHOLDER} substitutions, org.testcontainers:testcontainers-postgresql and testcontainers-junit-jupiter coordinates, flyway-database-postgresql, kspTest and testAnnotationProcessor, and the 'Expected @KoraApp as SubModule' warning."
tags: testing, integration-tests, testcontainers, postgres, flyway
---

# Integration Testing with Kora { #integration-testing-kora }

This guide introduces integration testing for Kora JDBC applications. It covers how to run the application graph against real PostgreSQL infrastructure, how Testcontainers supplies database connection
settings, and how repositories, migrations, configuration, and services are verified together. You will also see how integration tests catch wiring and persistence issues that unit tests intentionally
avoid.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java Testing Integration App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-testing-integration-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin Testing Integration App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-testing-integration-app).

## What You'll Build { #youll-build }

You'll create integration tests that cover:

- **Real Database Validation**: Run tests against a real PostgreSQL instance
- **Migration Verification**: Ensure Flyway migrations are applied correctly
- **Service + Repository Integration**: Verify complete persistence workflows
- **Configuration Override Testing**: Inject runtime configuration from containers
- **Deterministic Test Isolation**: Clean and repeatable test behavior

## What You'll Need { #youll-need }

- JDK 25 or later
- Gradle 9+ (the reference applications use Gradle Wrapper `9.5.1`)
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

Kora 2.0 JDBC repositories are synchronous: a `@Query` method returns the mapped value, a `List`, an `Optional`, or an `UpdateCount`, and the calling thread blocks until the statement finishes. An
integration test therefore reads like ordinary code — call the service, then query the database and assert — with no awaiting, no reactive subscription, and no coroutine builder.

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

Two coordinates deserve attention. Testcontainers `2.0` renamed its modules: the JUnit 5 extension is `org.testcontainers:testcontainers-junit-jupiter` and the PostgreSQL module is
`org.testcontainers:testcontainers-postgresql`, both carrying the Testcontainers version and not the JUnit one. And `org.flywaydb:flyway-core` `13` no longer bundles database dialects, so the
PostgreSQL dialect artifact has to be added at the same version, otherwise migrations fail on startup with `Unsupported Database: PostgreSQL`.

===! ":fontawesome-brands-java: `Java`"

    Add the following test dependencies to your `build.gradle`:

    ```groovy title="build.gradle"
    dependencies {
        testAnnotationProcessor "io.koraframework:annotation-processors" //(1)!

        testImplementation platform("org.junit:junit-bom:6.1.3")

        testRuntimeOnly "org.postgresql:postgresql:42.7.13" //(2)!

        testImplementation "org.junit.jupiter:junit-jupiter"
        testImplementation project(":guide-database-jdbc-app") //(3)!
        testImplementation "io.koraframework:config-hocon"
        testImplementation "io.koraframework:database-flyway"
        testImplementation "org.flywaydb:flyway-database-postgresql:13.3.0" //(4)!
        testImplementation "io.koraframework:database-jdbc"
        testImplementation "io.koraframework:http-client-common"
        testImplementation "io.koraframework:http-server-undertow"
        testImplementation "io.koraframework:json-common"
        testImplementation "io.koraframework:logging-logback"
        testImplementation "io.koraframework:test-junit5"
        testImplementation "org.testcontainers:testcontainers-junit-jupiter:2.0.5" //(5)!
        testImplementation "org.testcontainers:testcontainers-postgresql:2.0.5"
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

    1.  Required here, unlike in the component testing guide: the test sources declare their own `@KoraApp` and their own `@Repository`, so the Kora annotation processor has to run over the test source set.
    2.  PostgreSQL JDBC driver, needed at runtime only.
    3.  The application module whose graph the test extends.
    4.  Flyway dialect artifact, kept at the same version as `flyway-core` shipped by the Kora BOM.
    5.  Testcontainers `2.0` module names. The old `org.testcontainers:junit-jupiter` and `org.testcontainers:postgresql` coordinates stopped at `1.21.x`.

=== ":simple-kotlin: `Kotlin`"

    Add the following test dependencies to your `build.gradle.kts`:

    ```kotlin title="build.gradle.kts"
    dependencies {
        kspTest("io.koraframework:symbol-processors:2.0.0.RC1") //(1)!

        testImplementation(platform("org.junit:junit-bom:6.1.3"))

        testRuntimeOnly("org.postgresql:postgresql:42.7.13") //(2)!

        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation(project(":guide-database-jdbc-app")) //(3)!
        testImplementation("io.koraframework:config-hocon")
        testImplementation("io.koraframework:database-flyway")
        testImplementation("org.flywaydb:flyway-database-postgresql:13.3.0") //(4)!
        testImplementation("io.koraframework:database-jdbc")
        testImplementation("io.koraframework:http-client-common")
        testImplementation("io.koraframework:http-server-undertow")
        testImplementation("io.koraframework:json-common")
        testImplementation("io.koraframework:logging-logback")
        testImplementation("io.koraframework:test-junit5")
        testImplementation("org.testcontainers:testcontainers-junit-jupiter:2.0.5") //(5)!
        testImplementation("org.testcontainers:testcontainers-postgresql:2.0.5")
    }

    kotlin {
        sourceSets.test { kotlin.srcDir("build/generated/ksp/test/kotlin") } //(6)!
    }

    tasks.test {
        useJUnitPlatform()
        filter {
            excludeTestsMatching("*${'$'}*")
            excludeTestsMatching("*TestApplication")
        }
        testLogging {
            showStandardStreams = true
            events("passed", "skipped", "failed")
            exceptionFormat = org.gradle.api.tasks.testing.logging.TestExceptionFormat.FULL
        }
    }
    ```

    1.  Required here, unlike in the component testing guide: the test sources declare their own `@KoraApp` and their own `@Repository`, so KSP has to run over the test source set. `ksp` covers only the main source set.
    2.  PostgreSQL JDBC driver, needed at runtime only.
    3.  The application module whose graph the test extends.
    4.  Flyway dialect artifact, kept at the same version as `flyway-core` shipped by the Kora BOM.
    5.  Testcontainers `2.0` module names. The old `org.testcontainers:junit-jupiter` and `org.testcontainers:postgresql` coordinates stopped at `1.21.x`.
    6.  Where KSP writes the generated test graph. Without this line the compiler and the IDE do not see `TestApplicationGraph`.

!!! note "Enable Submodule Generation In JDBC Application"

    Add submodule generation to the **real application graph** (`guide-database-jdbc-app`), not to test compilation. It makes the application's `@KoraApp` reusable as a module, which is exactly what a
    test-scope `@KoraApp` needs when it extends it.

    ===! ":fontawesome-brands-java: `Java`"

        Add to `guide-database-jdbc-app/build.gradle`:

        ```groovy title="guide-database-jdbc-app/build.gradle"
        tasks.named("compileJava", JavaCompile) {
            options.compilerArgs += ["-Akora.app.submodule.enabled=true"]
        }
        ```

    === ":simple-kotlin: `Kotlin`"

        Add to `guide-database-jdbc-app/build.gradle.kts`:

        ```kotlin title="guide-database-jdbc-app/build.gradle.kts"
        ksp {
            arg("kora.app.submodule.enabled", "true")
        }
        ```

## Test Graph { #test-graph }

Before writing integration test methods, create a dedicated `TestApplication`.
It extends your production `Application`, but adds a **test-only repository** with `deleteAll()` for cleanup.
This keeps production `UserRepository` focused on application behavior and moves test utilities into test scope.

`TestApplication` is itself annotated with `@KoraApp`, so the Kora processor generates a second graph for the test source set. Everything the production application declares is inherited; the test adds
only what it needs. The `@Root` method exists so that `TestUserRepository` is built even though no other component depends on it — without a root, Kora would prune it from the graph as unreachable. The
`@Tag(TestApplication.class)` marker keeps that root distinguishable from application components of the same `String` type.

===! ":fontawesome-brands-java: `Java`"

    Create `src/test/java/io/koraframework/guide/testingintegration/TestApplication.java`:

    ```java
    package io.koraframework.guide.testingintegration;

    import java.util.List;
    import io.koraframework.common.annotation.KoraApp;
    import io.koraframework.common.annotation.Root;
    import io.koraframework.common.annotation.Tag;
    import io.koraframework.database.common.annotation.Query;
    import io.koraframework.database.common.annotation.Repository;
    import io.koraframework.database.jdbc.JdbcRepository;
    import io.koraframework.guide.databasejdbc.Application;
    import io.koraframework.guide.databasejdbc.repository.UserDAO;

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

    Create `src/test/kotlin/io/koraframework/guide/testingintegration/TestApplication.kt`:

    ```kotlin
    package io.koraframework.guide.testingintegration

    import io.koraframework.common.annotation.KoraApp
    import io.koraframework.common.annotation.Root
    import io.koraframework.common.annotation.Tag
    import io.koraframework.database.common.annotation.Query
    import io.koraframework.database.common.annotation.Repository
    import io.koraframework.database.jdbc.JdbcRepository
    import io.koraframework.guide.databasejdbc.Application
    import io.koraframework.guide.databasejdbc.repository.UserDAO

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

    Create `src/test/java/io/koraframework/guide/testingintegration/UserServiceIntegrationPostgresTest.java`:

    ```java
    package io.koraframework.guide.testingintegration;

    import java.time.Duration;
    import org.junit.jupiter.api.BeforeEach;
    import org.slf4j.LoggerFactory;
    import org.testcontainers.containers.PostgreSQLContainer;
    import org.testcontainers.containers.output.Slf4jLogConsumer;
    import org.testcontainers.junit.jupiter.Container;
    import org.testcontainers.junit.jupiter.Testcontainers;
    import io.koraframework.guide.databasejdbc.service.UserService;
    import io.koraframework.guide.testingintegration.TestApplication.TestUserRepository;
    import io.koraframework.test.extension.junit5.KoraAppTest;
    import io.koraframework.test.extension.junit5.KoraAppTestConfigModifier;
    import io.koraframework.test.extension.junit5.KoraConfigModification;
    import io.koraframework.test.extension.junit5.TestComponent;

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

        @Override
        public KoraConfigModification config() {
            return KoraConfigModification.ofString("""
                    jdbc {
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

    Create `src/test/kotlin/io/koraframework/guide/testingintegration/UserServiceIntegrationPostgresTest.kt`:

    ```kotlin
    package io.koraframework.guide.testingintegration

    import org.junit.jupiter.api.BeforeEach
    import org.slf4j.LoggerFactory
    import org.testcontainers.containers.PostgreSQLContainer
    import org.testcontainers.containers.output.Slf4jLogConsumer
    import org.testcontainers.junit.jupiter.Container
    import org.testcontainers.junit.jupiter.Testcontainers
    import io.koraframework.guide.databasejdbc.service.UserService
    import io.koraframework.guide.testingintegration.TestApplication.TestUserRepository
    import io.koraframework.test.extension.junit5.KoraAppTest
    import io.koraframework.test.extension.junit5.KoraAppTestConfigModifier
    import io.koraframework.test.extension.junit5.KoraConfigModification
    import io.koraframework.test.extension.junit5.TestComponent
    import java.time.Duration

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
                jdbc {
                  jdbcUrl = ${'$'}{POSTGRES_JDBC_URL}
                  username = ${'$'}{POSTGRES_USER}
                  password = ${'$'}{POSTGRES_PASS}
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

`config()` in this test replaces configuration, not application code. `KoraConfigModification.ofString(...)` first adds a small HOCON fragment with the `jdbc` and `flyway` settings required by the JDBC
pool and migrations. The connection values are not hardcoded into the config string; they are expressed as `${POSTGRES_JDBC_URL}`, `${POSTGRES_USER}`, and `${POSTGRES_PASS}` placeholders.

The section name matters: in Kora 2.0 the JDBC pool is configured under `jdbc`, because `JdbcDatabaseModule` builds its factory with that path. In a Kotlin raw string, `$` starts a template expression,
so a HOCON substitution has to be written as `${'$'}{POSTGRES_JDBC_URL}` for the placeholder to survive into the configuration text.

Then `withSystemProperty(...)` provides real values from the running `PostgreSQLContainer`. Testcontainers may allocate a different port, username, or password for each run, so the test should not
assume a fixed `localhost:5432`. When Kora reads configuration, these placeholders are resolved through system properties, and the graph receives a normal `JdbcDatabase` connected to the disposable
database of this specific test run.

This is useful in several ways: production configuration does not change for tests, tests do not depend on a developer's local database, and the same application code is verified against real
PostgreSQL and real migrations. At the same time, you can override only the settings that matter without rewriting the entire configuration file.

## Write tests { #tests }

Now add real integration test methods to the same `UserServiceIntegrationPostgresTest` class.
The container is intentionally configured with explicit startup timeout and attached logs to make startup issues diagnosable.
These methods validate service behavior and persisted state against real PostgreSQL.

Every method uses both control points the test has: `userService` runs the real application logic, and `testUserRepository` reads the resulting rows straight from the database. Asserting on both sides
is what separates an integration test from a component test — the second half proves that the data actually reached PostgreSQL and survived the mapping.

===! ":fontawesome-brands-java: `Java`"

    Add imports:

    ```java
    import static org.junit.jupiter.api.Assertions.assertEquals;
    import static org.junit.jupiter.api.Assertions.assertTrue;

    import java.util.List;
    import org.junit.jupiter.api.Test;
    import io.koraframework.guide.databasejdbc.dto.UserRequest;
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
    import io.koraframework.guide.databasejdbc.dto.UserRequest
    ```

    Add test methods:

    ```kotlin
    @Test
    fun createUserShouldPersistUserInDatabase() {
        val result = userService.createUser(UserRequest("John", "john@example.com"))

        assertEquals("John", result.name)
        assertTrue(result.id.toLong() > 0)
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
        assertEquals("Charlie", result[0].name)
        assertEquals("David", result[1].name)
    }

    @Test
    fun updateUserShouldUpdateUserInDatabase() {
        val created = userService.createUser(UserRequest("John", "john@example.com"))

        val updated = userService.updateUser(created.id, UserRequest("John Updated", "john.updated@example.com"))

        assertEquals("John Updated", updated.name)
    }

    @Test
    fun deleteUserShouldRemoveUserFromDatabase() {
        val created = userService.createUser(UserRequest("John", "john@example.com"))

        userService.deleteUser(created.id)

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
- A test-scope `@KoraApp` with `@Root` for components no application code depends on

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
- Add `org.flywaydb:flyway-database-postgresql` at the same version as `flyway-core`, otherwise startup fails with `Unsupported Database: PostgreSQL`
- Check Flyway output in Gradle logs

**Database Connectivity Issues:**

- Use JDBC URL/credentials from container getters only
- Configure the pool under the `jdbc` section; a fragment written under any other section is simply ignored and the graph fails on a missing `jdbcUrl`
- Avoid hardcoded localhost credentials in test config
- Ensure PostgreSQL driver is available in test runtime
- Add explicit database-jdbc and database-flyway test dependencies when TestApplication extends another module's app graph

**Placeholders Are Not Substituted:**

- Every `${NAME}` in the fragment needs a matching `withSystemProperty("NAME", ...)`
- In Kotlin, write the placeholder as `${'$'}{NAME}`; a plain `${NAME}` is a Kotlin template expression and `\${NAME}` is not an escape sequence in a raw string

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

    Add to `guide-database-jdbc-app/build.gradle.kts`:

    ```kotlin title="guide-database-jdbc-app/build.gradle.kts"
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

- compare integration tests with [Kora Java Database JDBC App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-database-jdbc-app) and [Kora Kotlin Database JDBC App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-database-jdbc-app)
- check the [JUnit5 documentation](../documentation/junit5.md)
- check the [Database JDBC documentation](../documentation/database-jdbc.md)
- check the [Database Migration documentation](../documentation/database-migration.md)
- read the [Testcontainers documentation](https://www.testcontainers.org/)
