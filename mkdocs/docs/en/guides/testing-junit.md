---
title: JUnit Testing with Kora
summary: Learn comprehensive component and integration testing strategies for Kora applications including dependency injection testing and database integration with Testcontainers
tags: testing, junit, testcontainers, integration-tests, component-tests
---

# JUnit Testing with Kora

This guide covers comprehensive testing strategies for Kora applications, including component tests, integration tests, and black box tests using Testcontainers. You'll learn how to test services, controllers, and full application behavior with proper isolation and realistic test environments.

## What You'll Build

You'll create a complete test suite that covers:

- **Component Tests**: Testing service interactions with real dependencies
- **Integration Tests**: Testing with real databases using Testcontainers
- **Test Utilities**: Reusable test infrastructure and helpers

!!! note "Black Box Testing"

    For end-to-end testing of complete applications through HTTP APIs, see the **[Black Box Testing](../testing-black-box.md)** guide, which builds upon the foundation established in this guide.

## What You'll Need

- JDK 17 or later
- Gradle 7.0+
- A text editor or IDE
- Completed [HTTP Server](../http-server.md) guide

## Prerequisites

!!! note "Required: Complete Advanced HTTP Server Guide"

    This guide assumes you have completed the **[HTTP Server](../http-server.md)** guide and have a working Kora project with the UserService and UserController.

    If you haven't completed the advanced HTTP server guide yet, please do so first as this guide builds upon that foundation.

## Add Testing Dependencies

===! ":fontawesome-brands-java: `Java`"

    Add the following test dependencies to your `build.gradle`:

    ```gradle title="build.gradle"
    dependencies {
        // ... existing dependencies ...

        // Kora testing framework with JUnit 5 integration
        testImplementation("ru.tinkoff.kora:test-junit5")

        // Mocking framework for component testing
        testImplementation("org.mockito:mockito-core:5.18.0")

        // JSON processing for HTTP API testing
        testImplementation("org.json:json:20231013")
        testImplementation("org.skyscreamer:jsonassert:1.5.1")

        // Testcontainers for integration and black box testing
        testImplementation("org.testcontainers:junit-jupiter:1.19.8")

        // PostgreSQL Testcontainers extension (if using PostgreSQL)
        testImplementation("io.goodforgod:testcontainers-extensions-postgres:0.12.2")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Add the following test dependencies to your `build.gradle.kts`:

    ```kotlin title="build.gradle.kts"
    dependencies {
        // ... existing dependencies ...

        // Kora testing framework with JUnit 5 integration
        testImplementation("ru.tinkoff.kora:test-junit5")

        // Mocking framework for component testing
        testImplementation("org.mockito:mockito-core:5.18.0")

        // JSON processing for HTTP API testing
        testImplementation("org.json:json:20231013")
        testImplementation("org.skyscreamer:jsonassert:1.5.1")

        // Testcontainers for integration and black box testing
        testImplementation("org.testcontainers:junit-jupiter:1.19.8")

        // PostgreSQL Testcontainers extension (if using PostgreSQL)
        testImplementation("io.goodforgod:testcontainers-extensions-postgres:0.12.2")
    }
    ```

!!! note "Testcontainers Extensions"

    Kora examples use `io.goodforgod:testcontainers-extensions` for enhanced Testcontainers integration. These extensions provide:

    - Automatic database migration support (Flyway)
    - Simplified connection management
    - Network sharing between containers
    - Per-method container lifecycle management

    Choose the appropriate extension based on your database:
    - `testcontainers-extensions-postgres` for PostgreSQL
    - `testcontainers-extensions-mysql` for MySQL
    - `testcontainers-extensions-mongodb` for MongoDB

## Testing Strategy Overview

Kora follows a testing pyramid approach with an emphasis on **black box testing** as the primary testing strategy. This approach ensures your application works correctly end-to-end while maintaining fast feedback through component and integration tests.

### Testing Levels

1. **Black Box Tests** ⭐ **(Recommended Primary Approach)**
   - Test the complete application through its public APIs
   - Use real infrastructure (databases, external services)
   - Highest confidence level, tests actual user behavior
   - Slower but most realistic

   Despite being slower than component tests, Kora strongly recommends black box testing as the primary approach because Kora applications have extremely fast startup times. This makes black box tests practical and not prohibitively slow, while providing the highest confidence that your application works correctly end-to-end.

2. **Component Tests**
   - Test component interactions using Kora's dependency injection
   - Mock external dependencies, use real internal components
   - Fast feedback with good coverage of business logic
   - Use `@KoraAppTest` with `@TestComponent` and `@Mock`

3. **Integration Tests**
   - Test with real databases and infrastructure
   - Use Testcontainers for isolated, realistic environments
   - Validate data persistence and complex interactions
   - Use `@KoraAppTest` with Testcontainers extensions

### Kora Testing Principles

- **Black Box First**: Kora strongly recommends black box testing as the primary testing approach
- **Realistic Environments**: Use Testcontainers to test with real infrastructure
- **Dependency Injection**: Leverage Kora's DI framework for component testing
- **Configuration Overrides**: Easily override configuration for different test scenarios
- **Test Applications**: Extend your main application with test-specific components

!!! tip "Kora's Recommendation"

    While all testing levels are valuable, Kora examples and documentation emphasize **black box testing** as the most reliable approach for ensuring application correctness. Component and integration tests provide fast feedback during development, but black box tests validate the complete user experience.

## Component Tests: Testing with Kora DI

Component testing is a sophisticated testing approach that validates the interactions between multiple components within your application while maintaining controlled isolation. Unlike traditional unit tests that focus on individual methods or classes in isolation, component tests verify that groups of related components work together correctly, catching integration issues early while providing faster feedback than full integration tests.

### What Makes Component Testing Special?

**Component testing bridges the gap between unit testing and integration testing:**

- **Real Component Interactions**: Tests use actual implementations of your business logic components
- **Controlled Isolation**: External dependencies (databases, external APIs, file systems) are mocked or stubbed
- **Dependency Injection Validation**: Ensures your DI configuration works correctly
- **Business Logic Focus**: Validates the core application logic without infrastructure concerns
- **Fast Execution**: Much faster than integration tests while providing better coverage than unit tests

### How Component Testing Works in Kora

Kora's component testing leverages its powerful dependency injection framework to create a "mini-application" for testing. Instead of manually creating and wiring mock objects, Kora automatically:

1. **Bootstraps a DI Container**: Creates a complete dependency injection context for your test
2. **Injects Real Components**: Uses actual implementations for your business logic components
3. **Provides Mock Injection Points**: Allows you to inject mocks for external dependencies
4. **Manages Component Lifecycle**: Handles component creation, initialization, and cleanup
5. **Supports Configuration Overrides**: Enables test-specific configuration without code changes

### Component Testing vs Other Testing Approaches

| Testing Type | Scope | Speed | Confidence | Use Case |
|-------------|-------|-------|------------|----------|
| **Unit Tests** | Single method/class | ⚡ Very Fast | 🔧 Low | Algorithm testing, edge cases |
| **Component Tests** | Component interactions | ⚡ Fast | 🔧 Medium-High | Business logic validation |
| **Integration Tests** | Full infrastructure | 🐌 Slow | 🔧 High | Data persistence, real DB |
| **Black Box Tests** | Complete application | 🐌 Slowest | 🔧 Highest | End-to-end user scenarios |

### When to Use Component Testing

**Component tests are ideal for:**

- **Business Logic Validation**: Testing complex interactions between services, repositories, and utilities
- **Dependency Injection Verification**: Ensuring your DI configuration works correctly
- **Fast Feedback Development**: Quick validation during development without database setup
- **Component Integration**: Catching issues where components don't work together properly
- **Configuration Testing**: Validating different configuration scenarios
- **Error Handling**: Testing exception scenarios and error propagation

**Component tests are NOT ideal for:**

- **Algorithm Testing**: Use unit tests for complex mathematical or algorithmic logic
- **Infrastructure Validation**: Use integration tests for database operations, file I/O, etc.
- **End-to-End Scenarios**: Use black box tests for complete user workflows
- **Performance Testing**: Requires specialized performance testing tools

### Kora's Component Testing Advantages

**Automatic Dependency Management:**
- No manual mock creation and wiring
- DI container handles component instantiation
- Automatic cleanup and lifecycle management

**Real Implementation Testing:**
- Tests actual component implementations, not interfaces
- Catches implementation bugs missed by interface-only testing
- Validates component interactions as they occur in production

**Configuration Flexibility:**
- Easy configuration overrides for different test scenarios
- Environment-specific behavior testing
- Feature flag validation

**Test Isolation with Realism:**
- External dependencies mocked for speed
- Internal components tested with real implementations
- Balances isolation with realistic testing

!!! note "Kora Component Testing"

    Kora's `@KoraAppTest` provides a powerful testing approach that combines the benefits of integration testing with the isolation of unit testing. Instead of manually wiring dependencies, you let Kora's DI container manage component creation while using `@TestComponent` and `@Mock` for precise test control.

===! ":fontawesome-brands-java: `Java`"

    Create `src/test/java/ru/tinkoff/kora/example/UserServiceComponentTest.java`:

    ```java
    package ru.tinkoff.kora.example;

    import static org.junit.jupiter.api.Assertions.*;
    import static org.mockito.ArgumentMatchers.*;
    import static org.mockito.Mockito.*;

    import java.util.List;
    import java.util.Optional;
    import org.jetbrains.annotations.NotNull;
    import org.junit.jupiter.api.Test;
    import org.mockito.Mock;
    import ru.tinkoff.kora.example.dto.UserRequest;
    import ru.tinkoff.kora.example.dto.UserResponse;
    import ru.tinkoff.kora.example.repository.UserRepository;
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTest;
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTestConfigModifier;
    import ru.tinkoff.kora.test.extension.junit5.KoraConfigModification;
    import ru.tinkoff.kora.test.extension.junit5.TestComponent;

    @KoraAppTest(Application.class)
    class UserServiceComponentTest implements KoraAppTestConfigModifier {

        @Mock
        @TestComponent
        private UserRepository userRepository;

        @TestComponent
        private UserService userService;

        @NotNull
        @Override
        public KoraConfigModification config() {
            return KoraConfigModification.ofString("""
                # Disable external dependencies for component testing if needed for components inside test
                some.dependency.enabled = false
                """);
        }

        @Test
        void createUser_ShouldCreateAndReturnUser() {
            // Given
            var request = new UserRequest("John", "john@example.com");
            var expectedResponse = new UserResponse("1", "John", "john@example.com");

            when(userRepository.save(any(UserRequest.class))).thenReturn(expectedResponse);

            // When
            var result = userService.createUser(request);

            // Then
            assertNotNull(result);
            assertEquals("John", result.name());
            assertEquals("john@example.com", result.email());
            verify(userRepository).save(request);
        }

        @Test
        void getUser_ShouldReturnUserWhenExists() {
            // Given
            var userId = "1";
            var expectedUser = new UserResponse(userId, "John", "john@example.com");

            when(userRepository.findById(userId)).thenReturn(Optional.of(expectedUser));

            // When
            var result = userService.getUser(userId);

            // Then
            assertTrue(result.isPresent());
            assertEquals(expectedUser, result.get());
            verify(userRepository).findById(userId);
        }

        @Test
        void getAllUsers_ShouldReturnAllUsers() {
            // Given
            var users = List.of(
                new UserResponse("1", "John", "john@example.com"),
                new UserResponse("2", "Jane", "jane@example.com")
            );

            when(userRepository.findAll()).thenReturn(users);

            // When
            var result = userService.getAllUsers();

            // Then
            assertEquals(2, result.size());
            assertEquals(users, result);
            verify(userRepository).findAll();
        }

        @Test
        void updateUser_ShouldUpdateAndReturnUserWhenExists() {
            // Given
            var userId = "1";
            var existingUser = new UserResponse(userId, "John", "john@example.com");
            var updateRequest = new UserRequest("John Updated", "john.updated@example.com");
            var updatedUser = new UserResponse(userId, "John Updated", "john.updated@example.com");

            when(userRepository.findById(userId)).thenReturn(Optional.of(existingUser));
            when(userRepository.save(any(UserRequest.class))).thenReturn(updatedUser);

            // When
            var result = userService.updateUser(userId, updateRequest);

            // Then
            assertTrue(result.isPresent());
            assertEquals("John Updated", result.get().name());
            assertEquals("john.updated@example.com", result.get().email());
            verify(userRepository).findById(userId);
            verify(userRepository).save(updateRequest);
        }

        @Test
        void deleteUser_ShouldReturnTrueWhenUserExists() {
            // Given
            var userId = "1";
            when(userRepository.existsById(userId)).thenReturn(true);

            // When
            var result = userService.deleteUser(userId);

            // Then
            assertTrue(result);
            verify(userRepository).existsById(userId);
            verify(userRepository).deleteById(userId);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/test/kotlin/ru/tinkoff/kora/example/UserServiceComponentTest.kt`:

    ```kotlin
    package ru.tinkoff.kora.example

    import org.junit.jupiter.api.Assertions.*
    import org.junit.jupiter.api.Test
    import org.mockito.Mockito.*
    import ru.tinkoff.kora.example.dto.UserRequest
    import ru.tinkoff.kora.example.dto.UserResponse
    import ru.tinkoff.kora.example.repository.UserRepository
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTest
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTestConfigModifier
    import ru.tinkoff.kora.test.extension.junit5.KoraConfigModification
    import ru.tinkoff.kora.test.extension.junit5.TestComponent

    @KoraAppTest(Application::class)
    class UserServiceComponentTest : KoraAppTestConfigModifier {

        @org.mockito.Mock
        @TestComponent
        private lateinit var userRepository: UserRepository

        @TestComponent
        private lateinit var userService: UserService

        override fun config(): KoraConfigModification {
            return KoraConfigModification.ofString("""
                # Disable external dependencies for component testing
                http-server.enabled = false
                db.enabled = false
                """)
        }

        @Test
        fun `createUser should create and return user`() {
            // Given
            val request = UserRequest("John", "john@example.com")
            val expectedResponse = UserResponse("1", "John", "john@example.com")

            `when`(userRepository.save(any(UserRequest::class.java))).thenReturn(expectedResponse)

            // When
            val result = userService.createUser(request)

            // Then
            assertNotNull(result)
            assertEquals("John", result.name)
            assertEquals("john@example.com", result.email)
            verify(userRepository).save(request)
        }

        @Test
        fun `getUser should return user when exists`() {
            // Given
            val userId = "1"
            val expectedUser = UserResponse(userId, "John", "john@example.com")

            `when`(userRepository.findById(userId)).thenReturn(expectedUser)

            // When
            val result = userService.getUser(userId)

            // Then
            assertNotNull(result)
            assertEquals(expectedUser, result)
            verify(userRepository).findById(userId)
        }

        @Test
        fun `getAllUsers should return all users`() {
            // Given
            val users = listOf(
                UserResponse("1", "John", "john@example.com"),
                UserResponse("2", "Jane", "jane@example.com")
            )

            `when`(userRepository.findAll()).thenReturn(users)

            // When
            val result = userService.getAllUsers()

            // Then
            assertEquals(2, result.size)
            assertEquals(users, result)
            verify(userRepository).findAll()
        }

        @Test
        fun `updateUser should update and return user when exists`() {
            // Given
            val userId = "1"
            val existingUser = UserResponse(userId, "John", "john@example.com")
            val updateRequest = UserRequest("John Updated", "john.updated@example.com")
            val updatedUser = UserResponse(userId, "John Updated", "john.updated@example.com")

            `when`(userRepository.findById(userId)).thenReturn(existingUser)
            `when`(userRepository.save(any(UserRequest::class.java))).thenReturn(updatedUser)

            // When
            val result = userService.updateUser(userId, updateRequest)

            // Then
            assertNotNull(result)
            assertEquals("John Updated", result.name)
            assertEquals("john.updated@example.com", result.email)
            verify(userRepository).findById(userId)
            verify(userRepository).save(updateRequest)
        }

        @Test
        fun `deleteUser should return true when user exists`() {
            // Given
            val userId = "1"
            `when`(userRepository.existsById(userId)).thenReturn(true)

            // When
            val result = userService.deleteUser(userId)

            // Then
            assertTrue(result)
            verify(userRepository).existsById(userId)
            verify(userRepository).deleteById(userId)
        }
    }
    ```

!!! tip "Benefits of Kora Component Testing"

    **Why use @KoraAppTest for component testing?**

    - **Real Dependencies**: Tests use actual component implementations, not mocks
    - **DI Validation**: Ensures dependency injection works correctly
    - **Configuration**: Easy configuration overrides for different test scenarios
    - **Integration Ready**: Same pattern works for integration tests
    - **Less Boilerplate**: No manual dependency wiring

    For testing complex algorithms or edge cases with full isolation, traditional mocking approaches can still be useful, but for most Kora applications, component tests provide better coverage with less maintenance.

## Integration Tests: Testing with Testcontainers

Integration testing is a critical testing approach that validates how your application components interact with real external infrastructure and services. Unlike component tests that mock external dependencies, integration tests use actual databases, message queues, and other infrastructure to ensure your application works correctly in realistic environments.

### What Makes Integration Testing Essential?

**Integration testing fills the critical gap between isolated component testing and end-to-end black box testing:**

- **Real Infrastructure Validation**: Tests use actual databases, caches, and external services
- **Data Persistence Verification**: Ensures data is correctly stored, retrieved, and manipulated
- **Infrastructure Integration**: Validates connection pooling, transaction management, and error handling
- **Complex Interactions**: Tests multi-component workflows and data flow between systems
- **Production Readiness**: Catches issues that only appear with real infrastructure

### How Integration Testing Works with Testcontainers

Testcontainers revolutionizes integration testing by providing lightweight, disposable containers for each test:

1. **Automatic Container Lifecycle**: Containers start automatically before tests and stop after
2. **Fresh Environment Per Test**: Each test gets a clean, isolated infrastructure instance
3. **Real Implementations**: Uses actual PostgreSQL, Redis, Kafka, etc., not in-memory fakes
4. **Network Configuration**: Automatic connection string injection and network setup
5. **Migration Support**: Applies database schema migrations automatically

### Integration Testing vs Other Testing Approaches

| Testing Type | Infrastructure | Speed | Confidence | Use Case |
|-------------|----------------|-------|------------|----------|
| **Component Tests** | Mocked | ⚡ Fast | 🔧 Medium | Business logic validation |
| **Integration Tests** | Real (Testcontainers) | 🐌 Slow | 🔧 High | Infrastructure integration |
| **Black Box Tests** | Real (Production-like) | 🐌 Slowest | 🔧 Highest | End-to-end workflows |

### When to Use Integration Testing

**Integration tests are crucial for:**

- **Database Operations**: Validating CRUD operations, transactions, and data integrity
- **Infrastructure Integration**: Testing connections to databases, caches, message queues
- **Data Migrations**: Ensuring schema changes work correctly
- **Complex Queries**: Testing advanced SQL queries, joins, and aggregations
- **Connection Pooling**: Validating connection management and error recovery
- **Cross-Service Communication**: Testing interactions between microservices

!!! note "TestApplication Pattern"

    For integration testing, create a `TestApplication` that extends your main application and adds test-specific components like repositories with additional helper methods.

===! ":fontawesome-brands-java: `Java`"

    First, create a test application with test-specific repositories that do not exist in our application but will help us to test it:

    Create `src/test/java/ru/tinkoff/kora/example/TestApplication.java`:

    ```java
    package ru.tinkoff.kora.example;

    import java.util.List;
    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.common.Tag;
    import ru.tinkoff.kora.common.annotation.Root;
    import ru.tinkoff.kora.database.common.annotation.Query;
    import ru.tinkoff.kora.database.common.annotation.Repository;
    import ru.tinkoff.kora.database.jdbc.JdbcRepository;
    import ru.tinkoff.kora.example.model.dao.User;

    /**
     * Test application that extends the main application and adds test-specific components.
     * This allows adding helper repositories for testing without modifying the main application.
     */
    @KoraApp
    public interface TestApplication extends Application {

        @Root
        @Repository
        interface TestUserRepository extends JdbcRepository {

            @Query("SELECT %{return#selects} FROM %{return#table}")
            List<User> findAll();

            @Query("DELETE FROM users")
            void deleteAll();
        }
    }
    ```

    Then create the integration test:

    Create `src/test/java/ru/tinkoff/kora/example/UserServiceIntegrationTest.java`:

    ```java
    package ru.tinkoff.kora.example;

    import static org.junit.jupiter.api.Assertions.*;

    import io.goodforgod.testcontainers.extensions.ContainerMode;
    import io.goodforgod.testcontainers.extensions.Network;
    import io.goodforgod.testcontainers.extensions.jdbc.ConnectionPostgreSQL;
    import io.goodforgod.testcontainers.extensions.jdbc.JdbcConnection;
    import io.goodforgod.testcontainers.extensions.jdbc.Migration;
    import io.goodforgod.testcontainers.extensions.jdbc.TestcontainersPostgreSQL;
    import java.util.List;
    import org.jetbrains.annotations.NotNull;
    import org.junit.jupiter.api.Test;
    import ru.tinkoff.kora.example.TestApplication.TestUserRepository;
    import ru.tinkoff.kora.example.dto.UserRequest;
    import ru.tinkoff.kora.example.dto.UserResponse;
    import ru.tinkoff.kora.example.service.UserService;
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTest;
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTestConfigModifier;
    import ru.tinkoff.kora.test.extension.junit5.KoraConfigModification;
    import ru.tinkoff.kora.test.extension.junit5.TestComponent;

    @TestcontainersPostgreSQL(
            network = @Network(shared = true),
            mode = ContainerMode.PER_RUN,
            migration = @Migration(
                    engine = Migration.Engines.FLYWAY,
                    apply = Migration.Mode.PER_METHOD,
                    drop = Migration.Mode.PER_METHOD))
    @KoraAppTest(TestApplication.class)
    class UserServiceIntegrationTest implements KoraAppTestConfigModifier {

        @ConnectionPostgreSQL
        private JdbcConnection connection;

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
                """)
                .withSystemProperty("POSTGRES_JDBC_URL", connection.params().jdbcUrl())
                .withSystemProperty("POSTGRES_USER", connection.params().username())
                .withSystemProperty("POSTGRES_PASS", connection.params().password());
        }

        @Test
        void createUser_ShouldPersistUserInDatabase() {
            // Given
            var request = new UserRequest("John", "john@example.com");

            // When
            var result = userService.createUser(request);

            // Then
            assertNotNull(result);
            assertNotNull(result.id());
            assertEquals("John", result.name());
            assertEquals("john@example.com", result.email());

            // Verify data was persisted
            var allUsers = testUserRepository.findAll();
            assertEquals(1, allUsers.size());
            assertEquals("John", allUsers.get(0).name());
        }

        @Test
        void getUsers_WithPagination_ShouldReturnCorrectPage() {
            // Given - Create multiple users
            var users = List.of(
                new UserRequest("Alice", "alice@example.com"),
                new UserRequest("Bob", "bob@example.com"),
                new UserRequest("Charlie", "charlie@example.com"),
                new UserRequest("David", "david@example.com")
            );

            users.forEach(userService::createUser);
            assertEquals(4, testUserRepository.findAll().size());

            // When - Get second page with size 2
            var result = userService.getUsers(1, 2, "name");

            // Then
            assertEquals(2, result.size());
            // Should be sorted alphabetically: Alice, Bob, Charlie, David
            // Page 1 (0-indexed) with size 2 should return Charlie, David
            assertEquals("Charlie", result.get(0).name());
            assertEquals("David", result.get(1).name());
        }

        @Test
        void updateUser_ShouldUpdateUserInDatabase() {
            // Given
            var originalRequest = new UserRequest("John", "john@example.com");
            var createdUser = userService.createUser(originalRequest);
            var updateRequest = new UserRequest("John Updated", "john.updated@example.com");

            // When
            var updatedUser = userService.updateUser(createdUser.id(), updateRequest);

            // Then
            assertTrue(updatedUser.isPresent());
            assertEquals("John Updated", updatedUser.get().name());
            assertEquals("john.updated@example.com", updatedUser.get().email());

            // Verify in database
            var allUsers = testUserRepository.findAll();
            assertEquals(1, allUsers.size());
            assertEquals("John Updated", allUsers.get(0).name());
        }

        @Test
        void deleteUser_ShouldRemoveUserFromDatabase() {
            // Given
            var request = new UserRequest("John", "john@example.com");
            var createdUser = userService.createUser(request);
            assertEquals(1, testUserRepository.findAll().size());

            // When
            var result = userService.deleteUser(createdUser.id());

            // Then
            assertTrue(result);
            assertEquals(0, testUserRepository.findAll().size());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    First, create a test application:

    Create `src/test/kotlin/ru/tinkoff/kora/example/TestApplication.kt`:

    ```kotlin
    package ru.tinkoff.kora.example

    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.common.Tag
    import ru.tinkoff.kora.common.annotation.Root
    import ru.tinkoff.kora.database.common.annotation.Query
    import ru.tinkoff.kora.database.common.annotation.Repository
    import ru.tinkoff.kora.database.jdbc.JdbcRepository
    import ru.tinkoff.kora.example.model.dao.User

    /**
     * Test application that extends the main application and adds test-specific components.
     */
    @KoraApp
    interface TestApplication : Application {

        @Repository
        interface TestUserRepository : JdbcRepository {

            @Query("SELECT %{return#selects} FROM %{return#table}")
            fun findAll(): List<User>

            @Query("DELETE FROM users")
            fun deleteAll()
        }

        // Need any fake root to require components to include them in graph
        @Tag(TestApplication::class)
        @Root
        fun testRoot(testUserRepository: TestUserRepository): String = "test-root"
    }
    ```

    Then create the integration test:

    Create `src/test/kotlin/ru/tinkoff/kora/example/UserServiceIntegrationTest.kt`:

    ```kotlin
    package ru.tinkoff.kora.example

    import io.goodforgod.testcontainers.extensions.ContainerMode
    import io.goodforgod.testcontainers.extensions.Network
    import io.goodforgod.testcontainers.extensions.jdbc.ConnectionPostgreSQL
    import io.goodforgod.testcontainers.extensions.jdbc.JdbcConnection
    import io.goodforgod.testcontainers.extensions.jdbc.Migration
    import io.goodforgod.testcontainers.extensions.jdbc.TestcontainersPostgreSQL
    import org.junit.jupiter.api.Assertions.*
    import org.junit.jupiter.api.Test
    import ru.tinkoff.kora.example.TestApplication.TestUserRepository
    import ru.tinkoff.kora.example.dto.UserRequest
    import ru.tinkoff.kora.example.dto.UserResponse
    import ru.tinkoff.kora.example.service.UserService
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTest
    import ru.tinkoff.kora.test.extension.junit5.KoraAppTestConfigModifier
    import ru.tinkoff.kora.test.extension.junit5.KoraConfigModification
    import ru.tinkoff.kora.test.extension.junit5.TestComponent

    @TestcontainersPostgreSQL(
        network = Network(shared = true),
        mode = ContainerMode.PER_RUN,
        migration = Migration(
            engine = Migration.Engines.FLYWAY,
            apply = Migration.Mode.PER_METHOD,
            drop = Migration.Mode.PER_METHOD
        )
    )
    @KoraAppTest(TestApplication::class)
    class UserServiceIntegrationTest : KoraAppTestConfigModifier {

        @ConnectionPostgreSQL
        private lateinit var connection: JdbcConnection

        @TestComponent
        private lateinit var userService: UserService

        @TestComponent
        private lateinit var testUserRepository: TestUserRepository

        override fun config(): KoraConfigModification {
            return KoraConfigModification.ofString("""
                db {
                  jdbcUrl = \${POSTGRES_JDBC_URL}
                  username = \${POSTGRES_USER}
                  password = \${POSTGRES_PASS}
                  poolName = "kora-test"
                }
                http-server.enabled = false
                """)
                .withSystemProperty("POSTGRES_JDBC_URL", connection.params().jdbcUrl())
                .withSystemProperty("POSTGRES_USER", connection.params().username())
                .withSystemProperty("POSTGRES_PASS", connection.params().password())
        }

        @Test
        fun `createUser should persist user in database`() {
            // Given
            val request = UserRequest("John", "john@example.com")

            // When
            val result = userService.createUser(request)

            // Then
            assertNotNull(result)
            assertNotNull(result.id)
            assertEquals("John", result.name)
            assertEquals("john@example.com", result.email)

            // Verify data was persisted
            val allUsers = testUserRepository.findAll()
            assertEquals(1, allUsers.size)
            assertEquals("John", allUsers[0].name)
        }

        @Test
        fun `getUsers with pagination should return correct page`() {
            // Given - Create multiple users
            val users = listOf(
                UserRequest("Alice", "alice@example.com"),
                UserRequest("Bob", "bob@example.com"),
                UserRequest("Charlie", "charlie@example.com"),
                UserRequest("David", "david@example.com")
            )

            users.forEach { userService.createUser(it) }
            assertEquals(4, testUserRepository.findAll().size)

            // When - Get second page with size 2
            val result = userService.getUsers(1, 2, "name")

            // Then
            assertEquals(2, result.size)
            // Should be sorted alphabetically: Alice, Bob, Charlie, David
            // Page 1 (0-indexed) with size 2 should return Charlie, David
            assertEquals("Charlie", result[0].name)
            assertEquals("David", result[1].name)
        }

        @Test
        fun `updateUser should update user in database`() {
            // Given
            val originalRequest = UserRequest("John", "john@example.com")
            val createdUser = userService.createUser(originalRequest)
            val updateRequest = UserRequest("John Updated", "john.updated@example.com")

            // When
            val updatedUser = userService.updateUser(createdUser.id, updateRequest)

            // Then
            assertNotNull(updatedUser)
            assertEquals("John Updated", updatedUser.name)
            assertEquals("john.updated@example.com", updatedUser.email)

            // Verify in database
            val allUsers = testUserRepository.findAll()
            assertEquals(1, allUsers.size)
            assertEquals("John Updated", allUsers[0].name)
        }

        @Test
        fun `deleteUser should remove user from database`() {
            // Given
            val request = UserRequest("John", "john@example.com")
            val createdUser = userService.createUser(request)
            assertEquals(1, testUserRepository.findAll().size)

            // When
            val result = userService.deleteUser(createdUser.id)

            // Then
            assertTrue(result)
            assertEquals(0, testUserRepository.findAll().size)
        }
    }
    ```

!!! tip "Testcontainers Extensions Features"

    The `@TestcontainersPostgreSQL` annotation provides:

    - **Automatic Container Management**: Starts PostgreSQL container per test method
    - **Database Migration**: Applies Flyway migrations automatically
    - **Network Sharing**: Containers can communicate with each other
    - **Per-Method Lifecycle**: Fresh database for each test method
    - **Connection Injection**: Provides ready-to-use database connections

!!! warning "Test Isolation"

    Each integration test gets a fresh database with migrations applied. This ensures test isolation but requires proper cleanup if tests share state.

## TestApplication Pattern: Extending Applications for Testing

The `TestApplication` pattern allows you to extend your main application with test-specific components without modifying the production code.

!!! note "When to Use TestApplication"

    Use `TestApplication` when you need:

    - Additional repositories for test data verification
    - Test-specific services or utilities
    - Components that help with test assertions
    - Helper methods for test data cleanup

## Configuration Overrides for Testing

Kora provides powerful configuration override capabilities for different test scenarios.

!!! tip "Configuration Override Patterns"

    **Common override patterns:**

    - Disable external services for component tests
    - Use in-memory databases for faster tests
    - Override connection settings for test infrastructure
    - Disable caching or background tasks during testing
    - Configure different ports or endpoints

## Running Tests

Run your tests using Gradle:

```bash
# Run all tests
./gradlew test

# Run specific test class
./gradlew test --tests "*UserServiceComponentTest*"

# Run with detailed output
./gradlew test --info

# Run tests in parallel
./gradlew test --parallel
```

## Test Reporting and Coverage

Kora projects include built-in test reporting and coverage:

```bash
# Generate test reports
./gradlew test

# Generate coverage reports
./gradlew jacocoTestReport

# View HTML coverage report
open build/jacocoHtml/index.html
```

## Best Practices

### Testing Strategy

1. **Prioritize Black Box Tests**: They provide the highest confidence
2. **Use Component Tests for Logic**: Fast feedback during development
3. **Integration Tests for Infrastructure**: Validate real database interactions
4. **Algorithm Testing**: Complex business logic with focused isolation when needed

### Test Organization

- **One Test Class per Production Class**: `UserService` → `UserServiceComponentTest`
- **Descriptive Test Names**: `createUser_ShouldCreateAndReturnUser`
- **Given-When-Then Structure**: Clear test phases
- **Test Data Builders**: Consistent test data creation

### Test Isolation

- **Fresh Database per Test**: Use Testcontainers with per-method lifecycle
- **No Test Interdependencies**: Tests should run independently
- **Clean State**: Reset state between tests
- **Resource Cleanup**: Proper container and connection cleanup

### Performance Considerations

- **Parallel Execution**: Run tests in parallel when possible
- **Shared Containers**: Use container sharing for faster startup
- **Selective Testing**: Run only relevant tests during development
- **Fast Feedback**: Component tests for quick validation

## Summary

You've learned comprehensive testing strategies for Kora applications:

- **Component Tests**: Test component interactions using Kora's DI framework
- **Integration Tests**: Test with real databases using Testcontainers
- **Black Box Tests**: Test complete application behavior through HTTP APIs

Each testing level provides different confidence and helps catch different types of bugs. Start with component tests for fast feedback, add integration tests for infrastructure validation, and rely on black box tests for end-to-end confidence.

The testing framework leverages Kora's dependency injection for easy mocking and configuration, Testcontainers for realistic infrastructure testing, and standard JUnit 5 patterns for familiar test structure.

## Key Concepts Learned

### Testing Strategy Overview
- **Component Tests**: Fast, isolated testing of individual components using Kora's dependency injection
- **Integration Tests**: Realistic testing with actual infrastructure using Testcontainers
- **Black Box Tests**: End-to-end testing of complete application behavior

### Kora Testing Framework
- **@KoraAppTest**: Annotation that bootstraps Kora's dependency injection for testing
- **TestApplication Pattern**: Custom application class for test-specific configuration
- **Configuration Overrides**: Environment variables and system properties for test configuration

### Testcontainers Integration
- **Real Infrastructure**: PostgreSQL, Redis, and other services in Docker containers
- **Automatic Lifecycle**: Containers start/stop automatically with test execution
- **Network Configuration**: Automatic connection string injection

### Best Practices
- **Test Isolation**: Each test runs in complete isolation with fresh containers
- **Fast Feedback**: Component tests for quick validation during development
- **Resource Cleanup**: Automatic cleanup of containers and connections
- **Parallel Execution**: Tests can run in parallel for faster execution

## Next Steps

Continue your learning journey:

- **Next Guide**: [Black Box Testing](../testing-black-box.md) - Learn end-to-end testing of complete HTTP APIs
- **Related Guides**:
  - [HTTP Server](../http-server.md) - Build APIs to test with black box testing
  - [Database JDBC](../database-jdbc.md) - Test database operations with integration tests
  - [Observability](../observability.md) - Monitor and debug your applications
- **Advanced Topics**:
  - [Testcontainers Advanced Features](../../documentation/test.md#testcontainers)
  - [Custom Test Annotations](../../documentation/test.md#custom-annotations)
  - [Performance Testing](../../documentation/test.md#performance-testing)

## Troubleshooting

### Testcontainers Not Starting
- Ensure Docker is running and accessible
- Check that Testcontainers dependencies are included
- Verify Docker image names are correct and images are available

### @KoraAppTest Not Working
- Ensure annotation processor is configured in build.gradle
- Check that Application interface includes TestModule
- Verify test class is properly annotated with @KoraAppTest

### Database Connection Issues
- Ensure PostgreSQL container is started before test execution
- Check database connection configuration in test properties
- Verify database schema matches entity definitions

### Configuration Overrides Not Applied
- Ensure environment variables are set before test execution
- Check that system properties are passed to test JVM
- Verify configuration property names match application expectations

### Test Execution Problems
- Check test logs for detailed error messages
- Ensure all dependencies are properly injected
- Verify test isolation (no shared state between tests)

## Help

- [Testing Documentation](../../documentation/test.md)
- [Kora GitHub Repository](https://github.com/kora-projects/kora)
- [GitHub Discussions](https://github.com/kora-projects/kora/discussions)
- [Testcontainers Documentation](https://www.testcontainers.org/)