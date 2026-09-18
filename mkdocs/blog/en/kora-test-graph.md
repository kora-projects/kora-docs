---
title: Testing the Same Graph You Run in Production — Kora Framework
description: How the Kora Framework's JUnit extension derives a test graph from the production application graph — component slices, in-graph replacements, typed configuration, and lifecycle.
search:
  exclude: true
---

# Testing the Same Graph You Run in Production

The most dangerous difference between production code and test code is often not the data. It is the wiring.

A service may pass an isolated test in which its constructor is called by hand, two mocks are supplied in the order the test author expects, and configuration is represented by a convenient constant.
The deployed application does something else. A dependency-injection container selects the implementation, generated adapters sit between layers, configuration is mapped from external values,
resources are initialized in dependency order, and lifecycle callbacks decide when the component is ready and when it is safe to stop. The test proves the class. It does not prove that the class
belongs to the application that will actually run.

The Kora Framework approaches this problem through its application graph. The graph built from `@KoraApp`, components, modules, factory methods, tags, and constructor dependencies is not only a production bootstrap
mechanism. The JUnit extension can take that application definition, select the part needed by a test, replace chosen nodes, initialize the result, and inject graph-managed components into the test.
This makes the production graph the starting point for component and integration testing instead of something recreated independently in test code.

That is the architectural meaning behind Kora's promise of simple and fast testing. “Simple” does not mean that every test is trivial, and “fast” does not mean replacing every dependency with a mock.
It means that the framework gives tests a direct way to reuse application structure while paying only for the part of that structure that matters to the current question.

## What “the Same Graph” Actually Means

The phrase needs to be precise. A component test does not necessarily start the complete process, bind every server port, connect every client, and run every background consumer. Nor does it reuse the
same object instances as a production process. It uses the same generated application graph as its source of truth: the same component definitions, dependency edges, tags, generated implementations,
and lifecycle contracts. The test extension then derives a test graph from that definition.

This distinction is important. The value is not that a component test becomes a miniature deployment. The value is that it stops inventing an unrelated dependency universe.

Consider a checkout path:

```text
HTTP server
    |
CheckoutController
    |
CheckoutService
   /       |        \
OrderRepository  PaymentGateway  AuditPublisher
      |             |                 |
  JDBC pool      HTTP client      Kafka producer
```

A hand-built test might instantiate `CheckoutService` directly. Such a test can be useful for an algorithm, but it does not establish that Kora can find `CheckoutService`, resolve the intended
`PaymentGateway`, preserve the correct `@Tag`, create the generated repository implementation, or supply the typed configuration expected by a client factory.

A Kora component test starts from the graph that contains those facts. If it requests `CheckoutService`, the extension follows its transitive dependencies. If `PaymentGateway` and `AuditPublisher` are
replaced with mocks, the real client and Kafka branches no longer need to be initialized. If `OrderRepository` stays real, its branch remains. The result is a partial application whose retained
relationships still come from the production application definition.

The claim should therefore be read as: test the same graph model that production runs, narrowed and modified deliberately for the test boundary.

## The Production Graph Is the Testable Architecture

Kora discovers and validates the application dependency container at compile time. An interface annotated with `@KoraApp` defines the application boundary and connects framework or application
modules. `@Component` classes and factory methods provide nodes. Constructor parameters and factory parameters create edges. `@Root` marks entry points that must exist when the application starts.
Anything unreachable from a root is removed.

At runtime, generated code materializes that already-resolved structure. Components are singletons within one graph instance. They are initialized eagerly in dependency order, with independent
branches initialized in parallel where possible. When the graph is released, components are closed in reverse dependency order. Components implementing `Lifecycle`, values wrapped in
`LifecycleWrapper`, and `AutoCloseable` resources participate in that process.

These properties are not incidental to testing. They explain why the graph is a stronger test boundary than a set of manually constructed objects. A dependency edge states both how a component is
constructed and what must be ready before it. A replacement changes one node at the same position in the structure. A graph slice preserves the upstream path necessary to build the requested
component. Graph initialization exercises lifecycle behavior before the test method begins, and graph release exercises cleanup afterward.

Compile-time validation also changes when failures appear. Missing components, ambiguous bindings, cycles, tag mismatches, and unreachable roots are application-definition problems, so they can fail
the build instead of waiting for a test context or deployed process to start. The test suite then concentrates on behavior, boundary substitutions, infrastructure compatibility, and lifecycle effects
rather than repeatedly rediscovering basic wiring errors at runtime.

## A Test Graph Begins with a Question

Kora's JUnit support lives in `io.koraframework:test-junit5`. A test selects an application with `@KoraAppTest` and selects components with `@TestComponent`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(Application.class)
    class CheckoutServiceTest {

        @TestComponent
        private CheckoutService checkoutService;

        @Test
        void createsAnOrder() {
            var result = checkoutService.checkout(request());

            assertEquals(OrderStatus.CREATED, result.status());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(Application::class)
    class CheckoutServiceTest {

        @TestComponent
        lateinit var checkoutService: CheckoutService

        @Test
        fun createsAnOrder() {
            val result = checkoutService.checkout(request())

            assertEquals(OrderStatus.CREATED, result.status)
        }
    }
    ```

`@KoraAppTest(Application.class)` tells the extension which generated application graph to use. `@TestComponent` does two jobs: it asks for a component to be injected, and it makes that component a
root of the limited test graph. Kora retains `CheckoutService` and everything needed to construct it. Unrelated controllers, schedulers, consumers, and servers are not initialized merely because they
exist in the application.

This is the central speed mechanism. The test does not gain speed by abandoning dependency injection; it gains speed by using graph reachability to avoid irrelevant work. A small service slice can
start quickly even when the full application contains expensive infrastructure branches.

Components can be injected into fields, constructor parameters, or test method parameters. Field injection is the most flexible choice when the test also changes configuration or modifies the graph
programmatically, because those modifications must be read from the test instance before graph construction. Constructor injection is useful for immutable test fields, but it cannot be combined with
`KoraAppTestConfigModifier` or `KoraAppTestGraphModifier`. Method parameters are useful when a dependency belongs to one scenario rather than the whole test class. Tagged components must be requested
with the matching `@Tag`; an untagged injection point matches an untagged component rather than any component of the same raw type.

The `components` and `modules` attributes of `@KoraAppTest` cover nodes that must be retained even though no field or parameter requests them directly. They do not turn arbitrary, disconnected modules
into part of the production application. A module listed in the annotation must already belong to the tested graph. The attributes influence the limited test graph; they are not a second
module-discovery system.

If a test needs broad inspection instead of a narrow injected component, it can inject `KoraAppGraph`. That object can find components by type and tag, with `TypeRef` used for parameterized types.
Direct graph access is valuable for infrastructure assertions and diagnostic tests, but routine behavior tests are clearer when their graph boundary is visible in typed `@TestComponent` fields or
parameters.

## Replacement Happens Inside the Graph

Focused tests need controlled boundaries. Kora treats a mock as a replacement graph node, not merely as a field owned by the test class.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(Application.class)
    class CheckoutServiceTest {

        @Mock
        @TestComponent
        private PaymentGateway paymentGateway;

        @Mock
        @TestComponent
        private AuditPublisher auditPublisher;

        @TestComponent
        private CheckoutService checkoutService;

        @Test
        void declinesAnOrderWhenPaymentIsRejected() {
            when(paymentGateway.authorize(any()))
                .thenReturn(PaymentResult.declined("insufficient-funds"));

            var result = checkoutService.checkout(request());

            assertEquals(OrderStatus.DECLINED, result.status());
            verify(auditPublisher).paymentDeclined(result.id());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(Application::class)
    class CheckoutServiceTest {

        @MockK
        @TestComponent
        lateinit var paymentGateway: PaymentGateway

        @MockK
        @TestComponent
        lateinit var auditPublisher: AuditPublisher

        @TestComponent
        lateinit var checkoutService: CheckoutService

        @Test
        fun declinesAnOrderWhenPaymentIsRejected() {
            every { paymentGateway.authorize(any()) } returns
                PaymentResult.declined("insufficient-funds")

            val result = checkoutService.checkout(request())

            assertEquals(OrderStatus.DECLINED, result.status)
            verify { auditPublisher.paymentDeclined(result.id) }
        }
    }
    ```

The same mock instance is injected into the test field and into every retained graph component that depends on `PaymentGateway`. `CheckoutService` remains a real production component created by Kora,
but its constructor receives the replacement. Dependencies used only to create the real gateway become unreachable and can be omitted. The test controls the boundary while preserving the construction
of the component under test.

Java tests can use Mockito's `@Mock` and `@Spy`; Kotlin tests can use MockK's `@MockK` and `@SpyK`. The Kora extension owns creation, insertion, reset, and cleanup of these mocks, so the separate
`MockitoExtension` or `MockKExtension` should not be added to the same test. Two extensions managing the same fields would make mock identity and lifecycle ambiguous. Kora's synchronous service,
repository, and HTTP contracts also keep stubbing direct: Java returns ordinary values, and Kotlin normally uses `every`, not coroutine-specific stubbing.

Mocks are best used where determinism and focus matter more than protocol realism. They work well for decline paths, timeout decisions, conditional publishing, authorization outcomes, and other logic
above an external boundary. They cannot prove SQL syntax, row mapping, migration compatibility, HTTP serialization, broker semantics, TLS configuration, or container packaging. The graph makes
replacement easy; it does not make a replacement equivalent to the real system.

Not every replacement should be a mocking-framework object. A deterministic fake may express behavior more clearly and maintain state useful to the assertion. Programmatic graph modification supports
that case.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(Application.class)
    class CheckoutWithFakeClockTest implements KoraAppTestGraphModifier {

        @TestComponent
        private CheckoutService checkoutService;

        @Override
        public KoraGraphModification graph() {
            return KoraGraphModification.create()
                .replaceComponent(
                    Clock.class,
                    () -> Clock.fixed(
                        Instant.parse("2026-04-12T10:15:30Z"),
                        ZoneOffset.UTC
                    )
                );
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(Application::class)
    class CheckoutWithFakeClockTest : KoraAppTestGraphModifier {

        @TestComponent
        lateinit var checkoutService: CheckoutService

        override fun graph(): KoraGraphModification {
            return KoraGraphModification.create()
                .replaceComponent(Clock::class.java) {
                    Clock.fixed(
                        Instant.parse("2026-04-12T10:15:30Z"),
                        ZoneOffset.UTC
                    )
                }
        }
    }
    ```

`KoraAppTestGraphModifier` returns a `KoraGraphModification`. It can add a component, replace an existing component, or create a mock programmatically. Type and tag identify the target, which matters
when several graph nodes share an interface.

Replacement factories have a useful architectural consequence. A replacement supplied independently can allow the original node's dependency branch to be pruned. A replacement built with
`Function<KoraAppGraph, T>` depends on initialized graph values, so those values must remain. That choice should be intentional: a standalone fake isolates a boundary; a graph-aware decorator
preserves part of the real boundary and changes behavior around it. A replacement factory must not request the same node it is replacing, or initialization has no valid base case.

## Configuration Is a Dependency, Not Test Scaffolding

Configuration often causes otherwise realistic tests to drift. Production reads HOCON or YAML, maps sections into typed interfaces, resolves substitutions, and passes resulting objects through the
graph. A test that bypasses this path by constructing a config object manually may miss wrong paths, missing values, mapping errors, and interactions between configuration and component creation.

Kora lets a test change configuration before it builds the graph. The test implements `KoraAppTestConfigModifier` and returns a `KoraConfigModification`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(Application.class)
    class CheckoutConfigurationTest implements KoraAppTestConfigModifier {

        @TestComponent
        private CheckoutService checkoutService;

        @Override
        public KoraConfigModification config() {
            return KoraConfigModification.ofString("""
                checkout {
                  maximumOrderValue = 1000
                  fraudChecksEnabled = true
                }
                """);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(Application::class)
    class CheckoutConfigurationTest : KoraAppTestConfigModifier {

        @TestComponent
        lateinit var checkoutService: CheckoutService

        override fun config(): KoraConfigModification {
            return KoraConfigModification.ofString(
                """
                checkout {
                  maximumOrderValue = 1000
                  fraudChecksEnabled = true
                }
                """.trimIndent()
            )
        }
    }
    ```

An inline string is useful when the scenario should declare its entire relevant configuration beside the test. `ofResourceFile(...)` is better for a larger reusable test profile.
`ofSystemProperty(...)`, `withSystemProperty(...)`, and `withSystemProperties(...)` are useful when the normal application file should remain in force or when values are known only after test
infrastructure starts. System properties applied this way exist while the graph is built and are restored afterward.

The timing is the crucial part: `config()` runs before component creation. Typed config mappers, client factories, pools, migrations, and any other config-dependent components see the test values
during normal graph initialization. Configuration is therefore one of the graph's controlled inputs, not a mutation applied after the application has already started.

This pattern fits Testcontainers particularly well. A database container chooses a host port at runtime. The test can put `${POSTGRES_JDBC_URL}`, `${POSTGRES_USER}`, and `${POSTGRES_PASS}` in an
inline HOCON fragment and populate them from container getters through `withSystemProperty(...)`. The graph then creates the real JDBC pool and repository against that disposable database. Production
configuration remains unchanged, but the production mapping and factory path are exercised.

Configuration overrides should remain narrow enough to expose accidental dependencies. Copying the entire production configuration into every test creates another configuration tree that can drift.
Prefer a small complete fragment for the retained graph slice, or keep the default application configuration and override only runtime values. If a supposedly focused component test suddenly requires
unrelated Kafka, HTTP server, or telemetry configuration, that is evidence that the selected graph slice or component boundary deserves inspection.

## A Partial Application Is More Than a Smaller Context

The phrase “partial application” can sound like an optimization detail. It is more useful to treat it as an explicit testing architecture.

The selected `@TestComponent` nodes are test roots. Kora computes their dependency closure after applying replacements. The resulting graph states exactly which production relationships the scenario
trusts and which boundaries it controls. That gives a test a meaningful structural scope.

For a pure component test, the retained graph may contain a real service, typed configuration, a validator, and two mocked ports. For an inter-component test, it may keep a controller, service,
mapper, and in-memory repository. For an integration test, it may keep real repositories, migrations, a JDBC pool, and a service while omitting the HTTP server and messaging consumer. Each test uses
the same selection mechanism but answers a different question.

This design avoids two common extremes. The first is the isolated test that reconstructs every constructor manually and proves nothing about framework wiring. The second is the full-context test that
starts every server, consumer, scheduler, and external client for every small behavior check. Graph slicing occupies the useful middle: production topology with a deliberate, observable boundary.

There are cases where the production graph needs a test-only extension rather than a replacement. An integration test may require a cleanup repository, a fixture loader, or an administrative operation
that should not exist in production code. A test source set can declare a separate `@KoraApp` that extends the main application and adds those components. Kora then generates a test application graph.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface TestApplication extends Application {

        @Repository
        interface TestOrderRepository extends JdbcRepository {
            @Query("DELETE FROM orders")
            void deleteAll();
        }

        @Root
        default TestSupport testSupport(TestOrderRepository repository) {
            return new TestSupport(repository);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface TestApplication : Application {

        @Repository
        interface TestOrderRepository : JdbcRepository {
            @Query("DELETE FROM orders")
            fun deleteAll()
        }

        @Root
        fun testSupport(repository: TestOrderRepository): TestSupport {
            return TestSupport(repository)
        }
    }
    ```

This technique preserves the production application declaration and adds capability in test scope. Because the test graph itself is generated, the annotation processor must be connected to the test
source set. The main application must also generate the submodule needed for inheritance. Test-only components that nobody consumes must be reachable from a test root or they will be pruned like any
other unreachable graph node.

An extended `TestApplication` should be used for genuine graph capabilities, not as a dumping ground for arbitrary test helpers. Object mothers, assertion utilities, and random-data builders do not
need to become application components. Cleanup repositories, embedded protocol adapters, and fixtures whose own dependencies and lifecycle matter are stronger candidates.

## Lifecycle Is Part of the Assertion Surface

Production resources have beginnings and endings. A database pool opens and closes connections. A server binds and releases a port. A consumer joins and leaves a group. A background worker starts and
must stop accepting work before its dependencies disappear. Testing a graph without respecting lifecycle would recreate the same mismatch that graph-based testing is intended to prevent.

Before a test method runs, the Kora extension builds the selected graph, applies configuration and graph modifications, creates nodes, and initializes lifecycle-aware components. The injected
component is ready, not merely constructed. After the test context ends, the extension releases the graph-managed resources. Dependency order governs initialization; reverse dependency order governs
release. Independent branches may initialize concurrently, exactly because their lack of dependency edges makes parallel work safe.

JUnit uses `TestInstance.Lifecycle.PER_METHOD` by default. Under that lifecycle, Kora creates and releases a fresh test graph for every test method. This gives strong state isolation and makes
lifecycle bugs visible, but it can be expensive when a graph owns a database pool, migration engine, broker client, or another heavy resource.

`@TestInstance(TestInstance.Lifecycle.PER_CLASS)` creates one graph for the class and releases it after all methods complete. This can materially reduce integration-test cost, but it changes the
test's obligations. Mutable component state is shared. Database rows and caches need explicit cleanup. The Kora extension resets mocks and spies before each method, so stubbing must be established
again for each scenario. Method-level mock injection is restricted because a method-scoped mock cannot safely inhabit a class-scoped graph.

Lifecycle choice should follow resource ownership, not habit. Use `PER_METHOD` when clean graph state is cheap and isolation is valuable. Use `PER_CLASS` when initialization dominates runtime and the
test can enforce deterministic cleanup. A static Testcontainers database combined with a per-method Kora graph shares the external process but recreates graph-owned connections; a per-class graph
shares both. Those are different isolation and performance trade-offs, and the test should make the decision visible.

Lifecycle testing also benefits from real rather than mocked boundaries. If a component's correctness depends on `init()` registering a listener or `release()` draining work, replacing it with a mock
removes the behavior under examination. Keep that component real, replace only its external side effects if necessary, and let the graph call its lifecycle methods. Conversely, a focused service test
should mock a heavy lifecycle boundary when resource startup is irrelevant to the question. Graph slicing makes both choices possible without changing production code.

## From Component Confidence to Production Confidence

Reusing the graph does not collapse all testing levels into one. It gives them a shared structural foundation.

A component test asks whether a real graph-managed component behaves correctly with controlled dependencies. It is fast, deterministic, and well suited to business branching. An integration test asks
whether a retained part of the graph works with real infrastructure. It can verify generated repositories, SQL, migrations, mapping, configuration, and resource lifecycle without paying for unrelated
application entry points. A black-box test starts the packaged service and communicates through its public API. It verifies routing, serialization, complete configuration, process flags, container
image, native libraries, networking, readiness, and the behavior of the final artifact.

No component graph test can prove that the container image contains the right files or that its entrypoint passes the intended JVM options. No mock can prove a database dialect. No black-box suite
should carry every combinatorial branch of service logic through expensive infrastructure. Confidence comes from placing each question at the narrowest boundary that can answer it honestly.

Kora's graph helps the layers agree. The component test uses the production component definition. The integration test keeps that definition and swaps a mocked port for a real container-backed
implementation. The black-box test runs the assembled artifact built from the same application declaration. Moving outward adds runtime surface rather than replacing one wiring model with another.

## Failure Modes Worth Avoiding

Graph-based testing is most valuable when the test boundary stays intentional. Several practices weaken it.

Requesting the whole graph for every test hides accidental dependencies and sacrifices the speed gained from reachability. Ask for the component that represents the behavior under test, then add other
roots only when the scenario truly observes them.

Mocking every constructor parameter turns the graph into an expensive way to reproduce an isolated unit test. Keep cheap, deterministic components real. Replace boundaries whose cost, nondeterminism,
or side effects interfere with the question.

Using mocks to represent protocols creates false confidence. A mocked repository can drive service branches, but it cannot verify a query. A mocked HTTP client can simulate status handling, but it
cannot prove request encoding. Promote those questions to integration tests with real infrastructure or a realistic protocol server.

Overriding configuration after initialization is too late. Use `KoraAppTestConfigModifier` so config-dependent nodes are built from scenario values. Avoid constructor injection when the test
implements config or graph modifiers, because the extension needs the test instance before it can construct that graph.

Ignoring tags can replace or request the wrong component when several implementations share a type. Treat type plus tag as the component identity. Use `TypeRef` for parameterized nodes rather than
relying on an erased raw class.

Sharing a graph without resetting all other mutable state makes tests order-dependent. `PER_CLASS` is a performance tool, not automatic isolation. Clean database state, caches, fake servers, and
application-owned buffers explicitly.

Finally, treating “same graph” as “production-equivalent environment” overstates what the test proves. A sliced and modified graph validates application structure and selected runtime behavior. Only a
black-box run of the production-ready image can cover the complete packaging and process boundary.

## A Practical Architecture for a Kora Test Suite

A productive suite starts with many small graph slices around business components. These tests request real services, validators, mappers, and policy objects, while replacing remote systems and
expensive infrastructure. They run with `PER_METHOD` unless lifecycle cost demonstrates a reason to share the graph.

Around infrastructure boundaries, narrower integration classes retain real generated repositories, clients, migrations, and typed configuration. Testcontainers supplies disposable PostgreSQL, Kafka,
Redis, or compatible services. Runtime addresses flow into the graph through `KoraConfigModification`, so factories and lifecycle operate normally. Test-only graph extensions provide cleanup or
fixture capabilities without polluting production interfaces.

A smaller black-box suite starts the built application image, waits for readiness, and exercises public contracts. These tests focus on representative critical paths, startup configuration, management
endpoints, and deployment assumptions rather than duplicating every service branch.

This architecture keeps feedback fast because most tests initialize only a small transitive closure. It keeps wiring honest because those closures are derived from the generated application graph. It
keeps integration realistic because selected external boundaries remain real. It keeps production claims bounded because the final image still receives its own independent verification.

## The Deeper Payoff

Kora's testing model follows from a broader design choice: application structure is explicit enough to be generated, inspected, validated, sliced, modified, initialized, and released as a graph.
Testing is not a separate subsystem layered over runtime dependency injection. It is another way of executing the same architectural model.

That reduces drift in several directions. Constructor changes affect production and tests together. New required dependencies appear in the graph slice instead of being forgotten in a hand-written
fixture. Replacements occupy the same node consumed by real dependents. Typed configuration reaches factories before construction. Lifecycle belongs to the retained components and is cleaned up by the
same dependency order that governs production shutdown.

The result is not the elimination of mocks, test configuration, or special test components. It is a disciplined place for each of them. A mock is a graph replacement. Test configuration is an input
applied before graph construction. A partial application is a reachable production slice. A test-only application is an explicit extension compiled in test scope. Lifecycle is part of setup and
teardown, not an afterthought.

This is why simple and fast testing can be a core framework principle rather than a collection of helper APIs. Once the production application is an explicit executable graph, a test no longer has to
choose between speed and faithful wiring. It can keep the wiring, cut the graph at an honest boundary, and initialize only the application it needs to answer one precise question.
