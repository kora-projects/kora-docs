---
search:
  exclude: true
title: JUnit Testing with Kora
summary: Learn comprehensive component and integration testing strategies for Kora applications including dependency injection testing and database integration with Testcontainers
description: "Component testing for Kora 2.0 with JUnit 5: the io.koraframework:test-junit5 artifact, @KoraAppTest and @TestComponent from io.koraframework.test.extension.junit5, Mockito @Mock and MockK @MockK inside the application graph, KoraAppTestConfigModifier with KoraConfigModification, test graph lifecycle and the Gradle test setup with JUnit 6.1.3 and byte-buddy alignment."
agent:
  use_when: "Use this file for questions about writing JUnit 5 component tests for a Kora 2.0 service: io.koraframework:test-junit5, @KoraAppTest, @TestComponent, injecting graph components into a test, replacing a dependency with a Mockito @Mock or MockK @MockK, MockitoStrictness, KoraAppTestConfigModifier and KoraConfigModification.ofString, testAnnotationProcessor and kspTest in a test module, and test-scope Gradle configuration."
tags: testing, junit, testcontainers, integration-tests, component-tests
---

# Component Testing with Kora { #component-testing-kora }

This guide introduces the main testing workflow for Kora applications with JUnit. It covers how Kora test annotations build controlled application graphs, how mocks and graph modifications isolate
components, and how Testcontainers-backed tests validate behavior against realistic infrastructure. You will also see how service, controller, integration, and black-box tests fit into one practical
testing strategy.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java Testing JUnit App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-testing-junit-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin Testing JUnit App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-testing-junit-app).

## What You'll Build { #youll-build }

You'll create a complete test suite that covers:

- **Component Tests**: Testing service interactions with real dependencies
- **Integration Tests**: Testing with real databases using Testcontainers
- **Test Utilities**: Reusable test infrastructure and helpers

## What You'll Need { #youll-need }

- JDK 25 or later
- Gradle 9+ (the reference applications use Gradle Wrapper `9.5.1`)
- A text editor or IDE
- Completed [HTTP Server](http-server.md) guide

## Prerequisites { #prerequisites }

!!! note "Required: Complete HTTP Server Guide"

    This guide assumes you have completed **[HTTP Server](http-server.md)** and have a working Kora project with `UserService`, `UserController`, DTOs, and the in-memory repository flow.

    If you haven't completed the HTTP server guide yet, do that first, because this guide tests the existing service and controller behavior rather than creating the application from scratch.

## Overview { #overview }

[JUnit](https://junit.org/junit5/docs/current/user-guide/) testing for a Kora application is about choosing the right boundary for the question you want to answer. A service test can answer whether
business logic behaves correctly. An integration test can answer whether the service works with real infrastructure. A black-box test can answer whether the complete application behaves correctly
through its public API.

The important shift from isolated class testing is that Kora code is often shaped by the application graph. Constructors, generated components, configuration, and framework modules all influence
behavior, so tests should be explicit about which part of the graph they are exercising.

### Testing Levels { #testing-levels }

This guide introduces the main testing levels used across the Kora guides:

- component tests build part of the Kora graph and replace selected dependencies with mocks
- integration tests keep more real components and add infrastructure such as [PostgreSQL](https://www.postgresql.org/docs/) through [Testcontainers](https://java.testcontainers.org/)
- black-box tests run the complete application and interact with it only through public HTTP APIs

These levels are not competitors. They trade speed, isolation, and confidence. Component tests are useful for fast feedback and focused behavior. Integration tests are useful when SQL, configuration,
migrations, or real clients matter. Black-box tests provide the strongest user-facing confidence because they include routing, serialization, configuration, framework wiring, and infrastructure.

### Kora Test Graphs { #kora-test-graphs }

Kora's compile-time graph is a major testing tool. `@KoraAppTest` can start an application graph for a test, and graph modification annotations can replace components, inject mocks, or add test-only
components. This keeps tests close to the real application wiring without forcing every test to start the entire runtime.

The important concept is that a Kora test is often testing a graph shape, not just a class. That is useful when behavior depends on dependency injection, generated components, configuration, or
framework modules.

Kora 2.0 contracts for HTTP controllers, HTTP clients, and JDBC repositories are synchronous. That directly simplifies tests: a component test calls a service method and asserts on the returned value,
with no `CompletionStage`, no reactive publisher, and no coroutine builder wrapped around the call. In Kotlin this means test methods stay ordinary `fun`, and MockK stubs use `every { ... } returns ...`
rather than the coroutine-aware `coEvery`.

### Testcontainers and Realism { #testcontainers-realism }

Mocks are fast, but they cannot prove that SQL runs, migrations match code, or external protocols are configured correctly. Testcontainers gives tests isolated real infrastructure, such as PostgreSQL,
while still keeping the environment disposable and repeatable.

This guide sets the foundation for the later dedicated testing guides: use component tests for focused feedback, integration tests for infrastructure boundaries, and black-box tests as the strongest
check of complete application behavior.

The practical flow is:

1. add JUnit, Mockito for Java, MockK for Kotlin, and the Kora test dependencies
2. declare a Kora test graph
3. replace selected dependencies with mocks
4. test service behavior through graph-managed components
5. add configuration overrides for test scenarios
6. prepare the project for deeper integration and black-box testing

## Dependencies { #dependencies }

The Kora JUnit 5 extension lives in `io.koraframework:test-junit5`. Its version comes from the `io.koraframework:kora-bom` platform, so the test configurations must see the BOM as well, not only
`implementation`.

===! ":fontawesome-brands-java: `Java`"

    Add the following test dependencies to your `build.gradle`:

    ```groovy title="build.gradle"
    dependencies {
        // ... existing dependencies ...

        testAnnotationProcessor "io.koraframework:annotation-processors" //(1)!

        testImplementation platform("org.junit:junit-bom:6.1.3") //(2)!
        testImplementation "org.junit.jupiter:junit-jupiter"
        testImplementation project(":guide-http-server-app") //(3)!
        testImplementation "io.koraframework:http-server-undertow"

        // Kora testing framework with JUnit 5 integration
        testImplementation "io.koraframework:test-junit5" //(4)!

        // Mocking framework for component testing
        testImplementation "org.mockito:mockito-core:5.23.0" //(5)!
    }

    test {
        useJUnitPlatform()
        testLogging {
            showStandardStreams(true)
            events("passed", "skipped", "failed")
            exceptionFormat("full")
        }
    }
    ```

    1.  Kora annotation processor in test scope. It only generates code once test sources declare Kora annotations of their own, such as a test-scope `@KoraApp` or `@Repository`. Test sources are
        compiled by a separate task, so the `annotationProcessor` entry of the main source set does not apply to them.
    2.  JUnit 6 BOM. Kora 2.0 is built and tested against JUnit `6.1.3`; the `org.junit.jupiter.api` packages are unchanged from JUnit 5.
    3.  The module that owns the `@KoraApp` you want to test. Without it there is no application graph to build.
    4.  Kora JUnit 5 extension: `@KoraAppTest`, `@TestComponent`, the config and graph modifiers.
    5.  Mockito. `test-junit5` depends on neither Mockito nor MockK, so the mocking framework you use has to be declared by the test module.

=== ":simple-kotlin: `Kotlin`"

    Add the following test dependencies to your `build.gradle.kts`:

    ```kotlin title="build.gradle.kts"
    dependencies {
        // ... existing dependencies ...

        testImplementation(platform("org.junit:junit-bom:6.1.3")) //(1)!
        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation(project(":guide-http-server-app")) //(2)!
        testImplementation("io.koraframework:http-server-undertow")

        // Kora testing framework with JUnit 5 integration
        testImplementation("io.koraframework:test-junit5") //(3)!

        // Mocking framework for Kotlin component testing
        testImplementation("io.mockk:mockk:1.14.11") //(4)!
    }

    tasks.test {
        useJUnitPlatform()
        testLogging {
            showStandardStreams = true
            events("passed", "skipped", "failed")
            exceptionFormat = org.gradle.api.tasks.testing.logging.TestExceptionFormat.FULL
        }
    }
    ```

    1.  JUnit 6 BOM. Kora 2.0 is built and tested against JUnit `6.1.3`; the `org.junit.jupiter.api` packages are unchanged from JUnit 5.
    2.  The module that owns the `@KoraApp` you want to test. Without it there is no application graph to build.
    3.  Kora JUnit 5 extension: `@KoraAppTest`, `@TestComponent`, the config and graph modifiers.
    4.  MockK. `test-junit5` depends on neither MockK nor Mockito, so the mocking framework you use has to be declared by the test module. Mockito works in Kotlin too, and the reference application uses
        it; MockK is shown here because its DSL avoids the escaped `` `when` `` call.

    There is no `kspTest("io.koraframework:symbol-processors")` line in this module. KSP has nothing to process here: the test class only consumes `Application` and its components, and `ApplicationGraph`
    was already generated when the HTTP server module was compiled. Add `kspTest` only when the test sources themselves declare Kora annotations, which is exactly what the
    [Integration Testing](testing-integration.md) guide does with its own `@KoraApp`.

!!! warning "Byte Buddy and the Java 25 toolchain"

    Mockito `5.23.0` resolves `net.bytebuddy:byte-buddy` `1.17.7` transitively, while Kora 2.0 builds and tests against `1.18.11`. Mocks are generated by Byte Buddy against classes compiled by a Java 25
    toolchain, so pin the newer version in the test module and keep it aligned with the framework. The same applies to MockK, which uses Byte Buddy through `mockk-agent`. See
    [Troubleshooting](#troubleshooting) for the Gradle snippet.

## Component Tests { #kora-di-component-tests }

A Kora component test sits between an isolated class test and a full application run. You do not create `UserService` by hand with `new`, and you do not manually assemble its dependencies. Instead, the
test asks Kora to build a small test graph, take the required component from that graph, and inject it into the test class.

That matters for two reasons:

- the test exercises the same dependency wiring style used by the application
- the graph can be limited to only the components required by this particular test
- this trimmed graph is built very quickly because `@KoraAppTest` does not initialize unrelated application branches
- by default, the test graph is initialized again for every test method unless you explicitly choose another JUnit lifecycle

In this guide, we first connect a real `UserService` as a test component. Then we replace its `UserRepository` dependency with a mock and look at how that replacement enters the graph.

### Test Component { #test-component }

Start with the simplest version: ask Kora to give the test a real `UserService` component.

`@KoraAppTest(Application.class)` tells the Kora JUnit extension which `@KoraApp` should be used as the graph source. This does not mean the test must start the whole application. The test graph is
limited to the components explicitly requested with `@TestComponent` and the dependencies required by those components.

`@TestComponent` on the `userService` field means two things at once:

- this component should be found in the application graph and injected into the test field
- this component becomes one of the root points of the test graph

So Kora starts from `UserService`, looks at its constructor, finds the required dependencies, and adds only the necessary part of the graph. If `UserService` depends on `UserRepository`, the repository
also enters the test graph. If the HTTP server, controllers, or other components are not required to create `UserService`, they do not have to be initialized in this component test.

`@KoraAppTest` has two more attributes for the cases where field types are not enough: `components()` forces extra components into the graph even when nothing in the test refers to them, and `modules()`
adds modules to the ones discovered from the `@KoraApp` type. Both are useful for components that only exist to run at startup and are not injected anywhere.

===! ":fontawesome-brands-java: `Java`"

    Create `src/test/java/io/koraframework/guide/testingjunit/UserServiceComponentTest.java`:

    ```java
    package io.koraframework.guide.testingjunit;

    import static org.junit.jupiter.api.Assertions.assertEquals;
    import static org.junit.jupiter.api.Assertions.assertNotNull;

    import org.junit.jupiter.api.Test;
    import io.koraframework.guide.httpserver.Application;
    import io.koraframework.guide.httpserver.dto.UserRequest;
    import io.koraframework.guide.httpserver.service.UserService;
    import io.koraframework.test.extension.junit5.KoraAppTest;
    import io.koraframework.test.extension.junit5.TestComponent;

    @KoraAppTest(Application.class)
    class UserServiceComponentTest {

        @TestComponent
        private UserService userService;

        @Test
        void createUserWithRealGraph() {
            var request = new UserRequest("John", "john@example.com");

            var result = userService.createUser(request);

            assertNotNull(result);
            assertEquals("John", result.name());
            assertEquals("john@example.com", result.email());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/test/kotlin/io/koraframework/guide/testingjunit/UserServiceComponentTest.kt`:

    ```kotlin
    package io.koraframework.guide.testingjunit

    import org.junit.jupiter.api.Assertions.assertEquals
    import org.junit.jupiter.api.Assertions.assertNotNull
    import org.junit.jupiter.api.Test
    import io.koraframework.guide.httpserver.Application
    import io.koraframework.guide.httpserver.dto.UserRequest
    import io.koraframework.guide.httpserver.service.UserService
    import io.koraframework.test.extension.junit5.KoraAppTest
    import io.koraframework.test.extension.junit5.TestComponent

    @KoraAppTest(Application::class)
    class UserServiceComponentTest {

        @TestComponent
        lateinit var userService: UserService

        @Test
        fun createUserWithRealGraph() {
            val request = UserRequest("John", "john@example.com")

            val result = userService.createUser(request)

            assertNotNull(result)
            assertEquals("John", result.name)
            assertEquals("john@example.com", result.email)
        }
    }
    ```

There is no mock at this step. `UserService` is real, and its dependencies are real too if Kora can build them from the application. This kind of test is useful when the dependency is cheap and fully
local: for example, the repository from the HTTP guide stores data in memory and does not require an external database.

### Test Graph Lifecycle { #test-graph-lifecycle }

When JUnit runs a test class annotated with `@KoraAppTest`, the Kora extension does several things before the test method is executed:

1. reads `Application` from `@KoraAppTest`
2. builds a test version of the application graph
3. keeps the components requested with `@TestComponent` and their dependencies
4. applies test replacements if they are declared
5. initializes the required graph components
6. injects ready components into test fields, constructor parameters, or test method parameters

After that, the ordinary JUnit test method runs. For the test method, `userService` is already not `null`; it is a ready component from the Kora graph.

In practice, this means:

- the `UserService` constructor is called by Kora, not by the test
- `UserService` dependencies come from the same application description used by the production graph
- components that are not required by the requested graph slice are not created just because the test exists
- if a component has lifecycle logic, it runs as part of test graph initialization
- when the test context finishes, Kora closes the graph-managed components it created
- by default, the container is initialized from scratch for every test method; the `@KoraAppTest` documentation points at `@TestInstance(TestInstance.Lifecycle.PER_CLASS)` when one graph per class is enough

This test answers the question: "Can Kora build the needed part of the application, and does the real component behave correctly?" But sometimes a real dependency gets in the way of a focused check.
For example, you may want to test sorting, `404` handling, or a repository call without depending on repository state. That is where a replacement is useful.

### Mock Component { #mock-component }

A mock is a test replacement for a real component. To the graph, it looks like an ordinary component of the required type, but its behavior is controlled by the test.

The concrete mocking framework depends on the language, but the replacement has the same role:

- the mocking framework annotation creates a mock of the required type
- `@TestComponent` tells Kora that this mock is a component of the test graph
- the field type `UserRepository` tells Kora which application component should be replaced

The key point: the mock is not only injected into the test class field. Kora also injects the same mock into every graph component that needs `UserRepository`. So `UserService` remains real, but its
constructor receives a test replacement instead of the real in-memory repository.

The graph for this test can be pictured like this:

```text
test field userRepository
        |
        | same mock instance
        v
UserService ---depends on--- UserRepository
   ^                         ^
   |                         |
@TestComponent          mock @TestComponent
real component          replacement component
```

As a result, the test gets two control points:

- through `userRepository`, it can define dependency responses
- through `userService`, it can call real service code and assert the result

The Kora extension recognizes the mocking annotations by name: `@Mock` and `@Spy` from Mockito, `@MockK` and `@SpyK` from MockK. Both frameworks can be used from either language; pick one per module and
stay with it. Mockito mocks created this way run with `Strictness.WARN` by default, and `@MockitoStrictness` from `io.koraframework.test.extension.junit5.mockito` raises or lowers that for the whole
test class. See [Mock strictness](../documentation/junit5.md#mock-strictness) for the details.

===! ":fontawesome-brands-java: `Java`"

    In Java, use Mockito: `@Mock` creates the `UserRepository` mock, and `when(...).thenReturn(...)` defines a response for a specific dependency call.

    Update the test class:

    ```java
    package io.koraframework.guide.testingjunit;

    import static org.junit.jupiter.api.Assertions.assertEquals;
    import static org.mockito.Mockito.verify;
    import static org.mockito.Mockito.when;

    import java.time.LocalDateTime;
    import java.util.Optional;
    import org.junit.jupiter.api.Test;
    import org.mockito.Mock;
    import io.koraframework.guide.httpserver.Application;
    import io.koraframework.guide.httpserver.dto.UserResponse;
    import io.koraframework.guide.httpserver.repository.UserRepository;
    import io.koraframework.guide.httpserver.service.UserService;
    import io.koraframework.test.extension.junit5.KoraAppTest;
    import io.koraframework.test.extension.junit5.TestComponent;

    @KoraAppTest(Application.class)
    class UserServiceComponentTest {

        @Mock
        @TestComponent
        private UserRepository userRepository;

        @TestComponent
        private UserService userService;

        @Test
        void getUserUsesRepositoryMock() {
            var expected = new UserResponse("1", "John", "john@example.com", LocalDateTime.now());
            when(userRepository.findById("1")).thenReturn(Optional.of(expected));

            var result = userService.getUser("1");

            assertEquals(Optional.of(expected), result);
            verify(userRepository).findById("1");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    In Kotlin, use MockK: `@MockK` creates the `UserRepository` mock, and `every { ... } returns ...` defines a response for a specific dependency call without escaping Kotlin keywords.

    Update the test class:

    ```kotlin
    package io.koraframework.guide.testingjunit

    import org.junit.jupiter.api.Assertions.assertEquals
    import org.junit.jupiter.api.Test
    import io.mockk.every
    import io.mockk.impl.annotations.MockK
    import io.mockk.verify
    import io.koraframework.guide.httpserver.Application
    import io.koraframework.guide.httpserver.dto.UserResponse
    import io.koraframework.guide.httpserver.repository.UserRepository
    import io.koraframework.guide.httpserver.service.UserService
    import io.koraframework.test.extension.junit5.KoraAppTest
    import io.koraframework.test.extension.junit5.TestComponent
    import java.time.LocalDateTime

    @KoraAppTest(Application::class)
    class UserServiceComponentTest {

        @MockK
        @TestComponent
        lateinit var userRepository: UserRepository

        @TestComponent
        lateinit var userService: UserService

        @Test
        fun getUserUsesRepositoryMock() {
            val expected = UserResponse("1", "John", "john@example.com", LocalDateTime.now())
            every { userRepository.findById("1") } returns expected

            val result = userService.getUser("1")

            assertEquals(expected, result)
            verify { userRepository.findById("1") }
        }
    }
    ```

Now the test is not testing the repository. It is testing `UserService` behavior for a known repository response. That is the main value of a mock: you fix dependency behavior and check how the
component above it reacts.

Note the shape of the stubbed call. `UserRepository.findById` is a synchronous method that returns `Optional<UserResponse>` in Java and `UserResponse?` in Kotlin, so the stub returns a plain value.
Kora 2.0 repository and HTTP contracts have no asynchronous variants, so there is nothing to await and no coroutine scope to open in the test.

### What Gets Initialized { #what-is-initialized }

With a mocked `UserRepository`, the graph becomes smaller and easier to reason about:

- `UserService` is created as a real application component
- `UserRepository` is replaced with a test mock
- components needed only by the real `UserRepository` are no longer required and do not enter the test graph
- the HTTP server and controllers are not created unless you request them as `@TestComponent`
- the test class receives references to both components: the real `userService` and the mocked `userRepository`

This differs from a regular hand-wired component test with mocks and without Kora. In such a test, you often write `new UserService(userRepository)` by hand. In a Kora test, the graph does that. So the
test checks all of these at once:

- `UserService` really is a graph component
- Kora can assemble it with the required dependency
- the replacement is applied in the same place where the production graph would use the real component
- the service business logic works for the dependency responses configured by the test

Do not use a separate JUnit extension from the mocking framework together with `@KoraAppTest`. `@KoraAppTest` manages the lifecycle of mocks and injects them into the graph. If a second JUnit extension
is attached, it becomes unclear who creates the mock, who resets its state, and which instance enters the graph.

### Write Tests { #write-tests }

Now add assertions for core service behavior using the mocked repository. Each test has three parts: first you define dependency behavior, then you call the real `UserService`, and after that you check
the result and the repository interaction.

Take the first test as an example. `assertNotNull(result)` checks that the service returned a response instead of `null`. `assertEquals("1", result.id())`, `assertEquals("John", result.name())`, and
the email assertion lock down the response contract: the id comes from the repository, while the name and email are copied from the request without distortion. Repository call verification complements
the assertions: it checks the interaction with a dependency rather than the returned data.

The examples below use standard JUnit Jupiter assertions: `assertEquals`, `assertNotNull`, `assertTrue`, and `assertThrows`. In real projects, you can also use AssertJ for more expressive checks such
as `assertThat(result.name()).isEqualTo("John")`, `assertThat(result).isNotNull()`, or `assertThatThrownBy { ... }`.

The `404` case is worth a second look. `UserService.deleteUser` reports a missing user by throwing `HttpServerResponseException`, which lives in `io.koraframework.http.server.common.response`. Its
`code()` accessor returns the HTTP status the application would have answered with, so a component test can assert the transport-level outcome without starting the HTTP server.

===! ":fontawesome-brands-java: `Java`"

    In the Java version, Mockito defines mock behavior with `when(...).thenReturn(...)`: it tells the repository mock what to return for a specific call. `verify(userRepository).save(...)` checks that
    the real `UserService` actually called the repository with the expected arguments. This is useful when the method result matters, but you also want to prove that the service used the right
    dependency and did not skip the required action.

    Add imports:

    ```java
    import static org.junit.jupiter.api.Assertions.assertEquals;
    import static org.junit.jupiter.api.Assertions.assertNotNull;
    import static org.junit.jupiter.api.Assertions.assertThrows;
    import static org.junit.jupiter.api.Assertions.assertTrue;

    import java.util.List;
    import io.koraframework.guide.httpserver.dto.UserRequest;
    import io.koraframework.http.server.common.response.HttpServerResponseException;
    ```

    Add test methods:

    ```java
    @Test
    void createUser_ShouldCreateAndReturnUser() {
        var request = new UserRequest("John", "john@example.com");

        when(userRepository.save("John", "john@example.com")).thenReturn("1");

        var result = userService.createUser(request);

        assertNotNull(result);
        assertEquals("1", result.id());
        assertEquals("John", result.name());
        assertEquals("john@example.com", result.email());
        verify(userRepository).save("John", "john@example.com");
    }

    @Test
    void getUser_ShouldReturnUserWhenExists() {
        var expected = new UserResponse("1", "John", "john@example.com", LocalDateTime.now());
        when(userRepository.findById("1")).thenReturn(Optional.of(expected));

        var result = userService.getUser("1");

        assertTrue(result.isPresent());
        assertEquals(expected, result.get());
        verify(userRepository).findById("1");
    }

    @Test
    void getUsers_ShouldReturnPagedUsers() {
        var users = List.of(
                new UserResponse("2", "Jane", "jane@example.com", LocalDateTime.now()),
                new UserResponse("1", "John", "john@example.com", LocalDateTime.now()));
        when(userRepository.findAll()).thenReturn(users);

        var result = userService.getUsers(0, 10, "name");

        assertEquals(2, result.size());
        assertEquals("Jane", result.get(0).name());
        assertEquals("John", result.get(1).name());
        verify(userRepository).findAll();
    }

    @Test
    void updateUser_ShouldUpdateAndReturnUserWhenExists() {
        var request = new UserRequest("John Updated", "john.updated@example.com");
        when(userRepository.update("1", request.name(), request.email())).thenReturn(true);

        var result = userService.updateUser("1", request);

        assertEquals("1", result.id());
        assertEquals("John Updated", result.name());
        assertEquals("john.updated@example.com", result.email());
        verify(userRepository).update("1", request.name(), request.email());
    }

    @Test
    void deleteUser_ShouldCallRepositoryWhenUserExists() {
        when(userRepository.deleteById("1")).thenReturn(true);

        userService.deleteUser("1");

        verify(userRepository).deleteById("1");
    }

    @Test
    void deleteUser_ShouldThrow404WhenUserMissing() {
        when(userRepository.deleteById("missing")).thenReturn(false);

        var exception = assertThrows(HttpServerResponseException.class, () -> userService.deleteUser("missing"));

        assertEquals(404, exception.code());
        verify(userRepository).deleteById("missing");
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    In the Kotlin version, MockK is used. Mock behavior is defined with the `every { ... } returns ...` DSL: the block describes the dependency call, and `returns` defines the response for that call.
    Interaction verification is written as `verify { userRepository.save(...) }`. This syntax fits Kotlin well: there is no need for escaped calls such as `` `when` ``, and the checked call remains
    ordinary Kotlin code inside the block.

    Add imports:

    ```kotlin
    import org.junit.jupiter.api.Assertions.assertNotNull
    import org.junit.jupiter.api.Assertions.assertThrows
    import io.koraframework.guide.httpserver.dto.UserRequest
    import io.koraframework.http.server.common.response.HttpServerResponseException
    ```

    Add test methods:

    ```kotlin
    @Test
    fun createUserShouldCreateAndReturnUser() {
        val request = UserRequest("John", "john@example.com")

        every { userRepository.save("John", "john@example.com") } returns "1"

        val result = userService.createUser(request)

        assertNotNull(result)
        assertEquals("1", result.id)
        assertEquals("John", result.name)
        assertEquals("john@example.com", result.email)
        verify { userRepository.save("John", "john@example.com") }
    }

    @Test
    fun getUserShouldReturnUserWhenExists() {
        val expected = UserResponse("1", "John", "john@example.com", LocalDateTime.now())
        every { userRepository.findById("1") } returns expected

        val result = userService.getUser("1")

        assertEquals(expected, result)
        verify { userRepository.findById("1") }
    }

    @Test
    fun getUsersShouldReturnPagedUsers() {
        val users = listOf(
            UserResponse("2", "Jane", "jane@example.com", LocalDateTime.now()),
            UserResponse("1", "John", "john@example.com", LocalDateTime.now())
        )
        every { userRepository.findAll() } returns users

        val result = userService.getUsers(0, 10, "name")

        assertEquals(2, result.size)
        assertEquals("Jane", result[0].name)
        assertEquals("John", result[1].name)
        verify { userRepository.findAll() }
    }

    @Test
    fun updateUserShouldUpdateAndReturnUserWhenExists() {
        val request = UserRequest("John Updated", "john.updated@example.com")
        every { userRepository.update("1", request.name, request.email) } returns true

        val result = userService.updateUser("1", request)

        assertEquals("1", result.id)
        assertEquals("John Updated", result.name)
        assertEquals("john.updated@example.com", result.email)
        verify { userRepository.update("1", request.name, request.email) }
    }

    @Test
    fun deleteUserShouldCallRepositoryWhenUserExists() {
        every { userRepository.deleteById("1") } returns true

        userService.deleteUser("1")

        verify { userRepository.deleteById("1") }
    }

    @Test
    fun deleteUserShouldThrow404WhenUserMissing() {
        every { userRepository.deleteById("missing") } returns false

        val exception = assertThrows(HttpServerResponseException::class.java) {
            userService.deleteUser("missing")
        }

        assertEquals(404, exception.code())
        verify { userRepository.deleteById("missing") }
    }
    ```

## Integration Tests { #integration-testing }

Integration testing with real PostgreSQL, `TestApplication`, and `UserServiceIntegrationPostgresTest` is covered in a dedicated guide: [Integration Testing](testing-integration.md).

This JUnit guide focuses on component testing with `@KoraAppTest`, `@TestComponent`, `@Mock` for Java, and `@MockK` for Kotlin.

## Configuration Overrides { #config-overrides }

The full rules for Kora test configuration are described in [Test configuration](../documentation/junit5.md#test-configuration).

A test class can implement `KoraAppTestConfigModifier` and return a `KoraConfigModification` from `config()`. That replaces the configuration the graph reads, without touching `application.conf` and
without touching application code. The most common builders are:

- `KoraConfigModification.ofString(...)` for an inline HOCON fragment
- `KoraConfigModification.ofResourceFile(...)` for a file from test `resources`
- `KoraConfigModification.ofSystemProperty(key, value)` when only system properties matter
- `withSystemProperty(...)` and `withSystemProperties(...)` to fill `${PLACEHOLDER}` substitutions inside the fragment

Configuration written here must use Kora 2.0 keys. Ports are `httpServer.port` for the public server and `httpServer.system.port` for the system server that serves probes and metrics; the JDBC pool is
configured under `jdbc`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(Application.class)
    class UserServiceConfigTest implements KoraAppTestConfigModifier {

        @TestComponent
        private UserService userService;

        @Override
        public KoraConfigModification config() {
            return KoraConfigModification.ofString("""
                    httpServer {
                      port = 0
                      system.port = 0
                      telemetry.logging.enabled = true
                    }
                    """);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(Application::class)
    class UserServiceConfigTest : KoraAppTestConfigModifier {

        @TestComponent
        lateinit var userService: UserService

        override fun config(): KoraConfigModification {
            return KoraConfigModification.ofString(
                """
                httpServer {
                  port = 0
                  system.port = 0
                  telemetry.logging.enabled = true
                }
                """.trimIndent()
            )
        }
    }
    ```

Port `0` asks the operating system for a free port, which keeps parallel test runs from colliding on `8080` and `8085`. That only matters when the test graph actually starts an HTTP server; a component
test that requests only `UserService` never binds a port at all.

!!! tip "Configuration Override Patterns"

    **Common override patterns:**

    - Disable external services for component tests
    - Use in-memory databases for faster tests
    - Override connection settings for test infrastructure
    - Disable caching or background tasks during testing
    - Configure different ports or endpoints

## Testing { #testing }

Run your tests using Gradle:

```bash
# Run all tests
./gradlew test

# Run with detailed output
./gradlew test --info

# Run tests in parallel
./gradlew test --parallel
```

## Test Coverage { #coverage }

Kora projects include built-in test reporting and coverage:

```bash
# Generate test reports
./gradlew test

# Generate coverage reports
./gradlew jacocoTestReport

# View HTML coverage report
open build/jacocoHtml/index.html
```

## Best Practices { #best-practices }

Testing Strategy:

1. Prioritize Black Box Tests: They provide the highest confidence
2. Use Component Tests for Logic: Fast feedback during development
3. Integration Tests for Infrastructure: Validate real database interactions
4. Algorithm Testing: Complex business logic with focused isolation when needed

Test Organization:

- One Test Class per Production Class: `UserService` → `UserServiceComponentTest`
- Descriptive Test Names: `createUser_ShouldCreateAndReturnUser`
- Given-When-Then Structure: Clear test phases
- Test Data Builders: Consistent test data creation

Test Isolation:

- Fresh Database per Test: Use Testcontainers with per-method lifecycle
- No Test Interdependencies: Tests should run independently
- Clean State: Reset state between tests
- Resource Cleanup: Proper container and connection cleanup

Performance Considerations:

- Parallel Execution: Run tests in parallel when possible
- Shared Containers: Use container sharing for faster startup
- Selective Testing: Run only relevant tests during development
- Fast Feedback: Component tests for quick validation

## Summary { #summary }

You've learned comprehensive testing strategies for Kora applications:

- Component Tests: Test component interactions using Kora's DI framework
- Integration Tests: Test with real databases using Testcontainers
- Black Box Tests: Test complete application behavior through HTTP APIs

Each testing level provides different confidence and helps catch different types of bugs. Start with component tests for fast feedback, add integration tests for infrastructure validation, and rely on
black box tests for end-to-end confidence.

The testing framework leverages Kora's dependency injection for easy mocking and configuration, Testcontainers for realistic infrastructure testing, and standard JUnit 5 patterns for familiar test
structure.

## Key Concepts { #key-concepts }

Testing Strategy Overview:

- Component Tests: Fast, isolated testing of individual components using Kora's dependency injection
- Integration Tests: Realistic testing with actual infrastructure using Testcontainers
- Black Box Tests: End-to-end testing of complete application behavior

Kora Testing Framework:

- `@KoraAppTest`: annotation that bootstraps the Kora dependency graph for a test, with optional `components()` and `modules()`
- `@TestComponent`: marks a field or parameter that should be taken from the graph, and makes it a root of the test graph
- `KoraAppTestConfigModifier` and `KoraAppTestGraphModifier`: entry points for configuration and graph changes
- `KoraConfigModification` and `KoraGraphModification`: builders for those changes

Testcontainers Integration:

- Real Infrastructure: PostgreSQL, Redis, and other services in Docker containers
- Automatic Lifecycle: Containers start/stop automatically with test execution
- Network Configuration: Automatic connection string injection

Best Practices:

- Test Isolation: Each test runs in complete isolation with fresh containers
- Fast Feedback: Component tests for quick validation during development
- Resource Cleanup: Automatic cleanup of containers and connections
- Parallel Execution: Tests can run in parallel for faster execution

## Troubleshooting { #troubleshooting }

**Mock Creation Fails on a Java 25 Toolchain:**

Mockito and MockK both generate mocks through Byte Buddy. Kora 2.0 pins `net.bytebuddy:byte-buddy` and `net.bytebuddy:byte-buddy-agent` to `1.18.11`, while Mockito `5.23.0` still resolves `1.17.7`
transitively. Force the aligned version in the test module:

===! ":fontawesome-brands-java: `Java`"

    ```groovy title="build.gradle"
    configurations.testRuntimeClasspath {
        resolutionStrategy {
            force "net.bytebuddy:byte-buddy:1.18.11"
            force "net.bytebuddy:byte-buddy-agent:1.18.11"
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin title="build.gradle.kts"
    configurations.testRuntimeClasspath {
        resolutionStrategy {
            force("net.bytebuddy:byte-buddy:1.18.11")
            force("net.bytebuddy:byte-buddy-agent:1.18.11")
        }
    }
    ```

**`@KoraAppTest` Cannot Find a Component:**

- Check that the `@KoraApp` type passed to `@KoraAppTest` really declares or inherits the module that provides the component
- Check that the test module depends on the module that owns the `@KoraApp`, otherwise the generated `ApplicationGraph` is not on the test classpath
- Add the component to `@KoraAppTest(components = ...)` when nothing in the test refers to it directly
- Remember that a component with a `@Tag` is only found when the test field carries the same `@Tag`

**Annotation Processing Does Not Run for Test Sources:**

- In Java, use `testAnnotationProcessor`, not `annotationProcessor`: test sources are compiled by a separate task
- In Kotlin, use `kspTest`, not `ksp`, and register `build/generated/ksp/test/kotlin` as a test source directory
- Both are only needed when the test sources themselves declare Kora annotations

**Mock Is Created but the Graph Uses the Real Component:**

- Make sure the field carries both the mocking annotation and `@TestComponent`
- Make sure no second JUnit extension from the mocking framework is attached to the class
- Check the declared field type: Kora matches the replacement by type, so a field typed as the implementation class does not replace a component published as an interface

**Unused Stubbing Errors:**

- Mockito mocks default to `Strictness.WARN` under `@KoraAppTest`
- Raise it with `@MockitoStrictness(Strictness.STRICT_STUBS)` when unused stubs should fail the test, or lower it to `Strictness.LENIENT` for shared setup

**Configuration Overrides Not Applied:**

- The test class must implement `KoraAppTestConfigModifier`; a `config()` method alone is not picked up
- `${PLACEHOLDER}` substitutions inside `ofString(...)` are resolved from system properties, so every placeholder needs a matching `withSystemProperty(...)`
- Verify the key names against Kora 2.0 configuration: `httpServer.port`, `httpServer.system.port`, `jdbc`

**Test Execution Problems:**

- Check test logs for detailed error messages
- Ensure all dependencies are properly injected
- Verify test isolation (no shared state between tests)

## What's Next? { #whats-next }

- [Database JDBC](database-jdbc.md) if you want to continue into tests that require PostgreSQL, Flyway, and repository migrations.
- [Integration Testing](testing-integration.md) after Database JDBC, to test repositories, migrations, and external dependencies with Testcontainers.
- [Black Box Testing](testing-black-box.md) after Database JDBC, to validate the packaged HTTP application end to end.
- [Observability](observability.md) to add metrics, traces, logs, and probes that can also be verified in tests.
- [Resilient Patterns](resilient.md) to practice testing failure and fallback behavior.

## Help { #help }

If you encounter issues:

- compare with the test classes in the relevant `guides/*` module
- check the [JUnit5 documentation](../documentation/junit5.md)
- revisit [HTTP Server](http-server.md) for the base graph shape
- read the [Testcontainers documentation](https://www.testcontainers.org/) for container lifecycle issues
