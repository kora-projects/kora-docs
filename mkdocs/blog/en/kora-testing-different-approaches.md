---
title: Component vs Integration vs Black-Box Tests in the Kora Framework
date: 2026-08-06
description: How the Kora Framework separates component, integration, and black-box tests — what each layer proves, and how to place each test at the cheapest boundary that can prove it.
search:
  exclude: true
---

# Component vs Integration vs Black-Box Tests in Kora { #testing-layers }

**August 6, 2026**

Testing strategy is often reduced to labels. One team calls a test “unit” because it runs in JUnit. Another calls the same test “integration” because a dependency-injection container starts. A third
calls every HTTP test “end-to-end,” even when the application is running in the same process with half its dependencies mocked. Those labels do not tell us what the test proves.

The Kora Framework provides a more useful way to draw the boundaries. Its testing documentation treats component, integration, and black-box tests as distinct layers, each built for a different question. Component
tests run a selected part of the Kora application graph and may replace dependencies. Integration tests still run inside the test process and call graph-managed components directly, but keep a real
infrastructure boundary such as PostgreSQL. Black-box tests start the packaged application as an external process or container and interact with it only through its public API.

The difference is not merely how much code runs. It is where the test is allowed to observe and control the system.

A component test can inject `UserService` and a repository mock. An integration test can inject `UserService` and a real generated repository connected to a Testcontainers database. A black-box test
should know neither class. It sends `POST /users`, reads the HTTP response, and sees the service as a client sees it.

These layers form a practical pyramid:

```text
                 Black-box
                     few

                Integration
                   fewer

                 Component
                    many
```

The pyramid describes quantity and feedback cost, not importance. Component tests are numerous because they are fast and can cover many behavioral branches. Integration tests are fewer because
infrastructure makes them slower and more expensive to isolate. Black-box tests are few because each one boots and exercises the complete deployed boundary, but those few tests carry the strongest
authority over whether the application is usable from the outside.

That last point matters in Kora. The framework documentation recommends black-box testing as the primary source of truth for complete application correctness. This does not require an inverted pyramid
with hundreds of containerized scenarios. “Primary source of truth” describes confidence: when a component test and the packaged application disagree, the packaged application wins. The pyramid
describes economics: use the broadest boundary only for scenarios that need it.

## One Application Architecture, Three Observation Boundaries { #observation-boundaries }

Kora builds and validates its application graph at compile time. Components, modules, factory methods, tags, generated repositories, configuration mappers, controllers, clients, and lifecycle
relationships become one explicit structure. Production starts that generated graph. Kora's JUnit extension can also use it as the source for a smaller test graph.

Suppose a user-creation request follows this path:

```text
HTTP request
    |
UserController
    |
UserService
    |
UserRepository
    |
JdbcDatabase
    |
PostgreSQL
```

All three test types can exercise user creation, but they cut through this structure at different places.

The component test enters at `UserService`. It may replace `UserRepository` with a mock, so it verifies service decisions without SQL or HTTP. The integration test also enters at `UserService`, but
retains the real repository, JDBC pool, migrations, mapping, and PostgreSQL instance. The black-box test enters at the public HTTP port. It crosses routing, request mapping, validation, controller
behavior, service logic, repository code, database access, response mapping, and container configuration.

Moving upward through the pyramid increases the amount of reality included in the test. It also increases the number of possible failure causes. That is why the layers complement rather than replace
each other. A broad test is authoritative but can be slower to diagnose. A narrow test is precise but can only establish facts inside its boundary.

## Component Tests: Fast Feedback Through a Graph Slice { #component-tests }

A Kora component test is not necessarily a classic isolated unit test. It sits between a hand-constructed class test and a full application context. The test asks Kora to build a selected slice of the
production graph, initialize its components, and inject the component under test.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(Application.class)
    class UserServiceComponentTest {

        @Mock
        @TestComponent
        private UserRepository userRepository;

        @TestComponent
        private UserService userService;

        @Test
        void returnsAnExistingUser() {
            var expected = new User("42", "Ada", "ada@example.com");
            when(userRepository.findById("42"))
                .thenReturn(Optional.of(expected));

            var result = userService.getUser("42");

            assertEquals(Optional.of(expected), result);
            verify(userRepository).findById("42");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(Application::class)
    class UserServiceComponentTest {

        @MockK
        @TestComponent
        lateinit var userRepository: UserRepository

        @TestComponent
        lateinit var userService: UserService

        @Test
        fun returnsAnExistingUser() {
            val expected = User("42", "Ada", "ada@example.com")
            every { userRepository.findById("42") } returns Optional.of(expected)

            val result = userService.getUser("42")

            assertEquals(Optional.of(expected), result)
            verify { userRepository.findById("42") }
        }
    }
    ```

`@KoraAppTest(Application.class)` selects the generated application graph. `@TestComponent` on `UserService` makes that component a root of the test graph, so Kora retains the service and the
dependencies required to create it. The repository field carries both Mockito's `@Mock` and Kora's `@TestComponent`. The resulting mock is not only available to the test; it replaces the repository
node used by `UserService`.

This is more faithful than calling `new UserService(repositoryMock)` in every test. Kora still proves that `UserService` belongs to the application graph, that its dependency can be resolved at the
expected graph position, and that the component is created through the production wiring model. At the same time, replacing the repository removes the real JDBC branch from the retained dependency
closure. The HTTP server and controller also remain outside the slice because the test did not request them.

Component tests are ideal when the interesting behavior belongs to one component or a small group of in-process components. They should carry the combinatorial burden of the suite: validation
decisions inside the service, authorization branches, mapping rules, fallback selection, retry eligibility, idempotency logic, state transitions, and error translation between application layers.
These scenarios benefit from deterministic dependency responses and precise interaction assertions.

They are also the best home for hard-to-create dependency outcomes. A payment provider can return a decline code, throw a timeout, produce malformed content, or accept a duplicate idempotency key
without requiring a real remote sandbox to behave that way on demand. A repository mock can return an empty result or a conflict without preparing database state for every branch.

Kora keeps such tests quick because only requested graph roots and their transitive dependencies are initialized. By default, JUnit's `PER_METHOD` lifecycle gives each test method a fresh graph, and
Kora releases lifecycle-managed components after the test. `PER_CLASS` can share one graph when initialization is expensive, but then mutable state must be cleaned explicitly and mocks are reset
before each method.

What a component test does not prove is just as important. A repository mock does not execute generated SQL. A mocked HTTP client does not prove header, path, body, or TLS behavior. Calling a service
directly bypasses HTTP routing, JSON conversion, controller validation, middleware, and status-code mapping. An inline test configuration does not prove that the packaged application receives its
environment correctly. Component tests give fast confidence in graph-managed behavior, not deployment confidence.

Use a component test when the answer would remain meaningful if external infrastructure were perfectly simulated. If the bug could exist only in SQL, wire protocol, serialization, process startup, or
packaging, the test belongs higher in the pyramid.

## Integration Tests: Real Infrastructure, Direct Component Access { #integration-tests }

An integration test keeps application code and one or more infrastructure boundaries real. In the Kora guides, the canonical example runs a PostgreSQL container, builds a Kora test graph containing
the real JDBC pool, Flyway migrations, generated repository, and `UserService`, then invokes those graph-managed components directly from JUnit.

```text
JUnit test
    |
    | direct method call
    v
UserService
    |
generated UserRepository
    |
JdbcDatabase
    |
PostgreSQLContainer
```

The HTTP layer is intentionally absent. The test is not asking whether a client can create a user. It is asking whether Kora application code behaves correctly with actual PostgreSQL semantics.

Testcontainers creates a disposable database. `KoraAppTestConfigModifier` supplies its runtime JDBC URL, username, and password before the graph is built. Kora then creates ordinary production
components from those values.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Testcontainers
    @KoraAppTest(TestApplication.class)
    class UserRepositoryIntegrationTest implements KoraAppTestConfigModifier {

        @Container
        static final PostgreSQLContainer<?> POSTGRES =
            new PostgreSQLContainer<>("postgres:16-alpine");

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
                    flyway.locations = "db/migration"
                    """)
                .withSystemProperty("POSTGRES_JDBC_URL", POSTGRES.getJdbcUrl())
                .withSystemProperty("POSTGRES_USER", POSTGRES.getUsername())
                .withSystemProperty("POSTGRES_PASS", POSTGRES.getPassword());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Testcontainers
    @KoraAppTest(TestApplication::class)
    class UserRepositoryIntegrationTest : KoraAppTestConfigModifier {

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
                flyway.locations = "db/migration"
                """.trimIndent()
            )
                .withSystemProperty("POSTGRES_JDBC_URL", POSTGRES.jdbcUrl)
                .withSystemProperty("POSTGRES_USER", POSTGRES.username)
                .withSystemProperty("POSTGRES_PASS", POSTGRES.password)
        }

        companion object {
            @Container
            @JvmStatic
            val POSTGRES = PostgreSQLContainer("postgres:16-alpine")
        }
    }
    ```

Because configuration is applied before graph initialization, the JDBC pool and migrations start against the container database rather than being patched afterward. Repository implementations are
generated and wired in the same way as in the application. Tests can therefore validate SQL execution, parameter binding, row mapping, constraints, transactions, sorting, pagination, updates, deletes,
and migration compatibility.

Integration tests are needed whenever infrastructure semantics are part of the expected behavior. A service that depends on a unique database constraint cannot be fully tested by programming a mock to
throw an exception that the real driver may never throw in that form. A pagination algorithm may look correct against a list but fail because SQL ordering is nondeterministic. A migration may create a
column with a type that the generated mapper cannot read. An HTTP client may construct the wrong URL or map a remote error body incorrectly. These are boundary facts, so the boundary must exist.

Kora's test graph lets an integration test remain narrower than the full application. The test can retain the database branch without binding the public HTTP server, joining a Kafka consumer group, or
starting unrelated background jobs. Direct access to `UserService` or `UserRepository` makes setup and assertions concise, and failures usually point toward the infrastructure boundary under
examination.

Test-only graph extensions are useful here. The integration guide declares a `TestApplication` that extends the production `Application` and adds a repository with `deleteAll()` for cleanup. Kora
generates this test graph in the test source set. That keeps administrative operations out of production repositories while allowing cleanup itself to use real database access. Such extensions should
contain capabilities whose wiring or lifecycle matters; ordinary assertion helpers and data builders do not need to become graph nodes.

Integration tests still do not prove the public contract. Calling `userService.createUser(...)` cannot reveal that `POST /users` is missing, that a JSON field has the wrong name, that validation
rejects a legitimate body, or that an exception maps to `500` instead of `409`. The test also runs application components inside the JUnit JVM rather than from the packaged distribution. Classpath,
JVM arguments, container user, exposed ports, environment variables, and startup command may differ from deployment.

Use an integration test when the central question contains the phrase “with the real database,” “over the real protocol,” “using actual migrations,” or “through the actual generated client or
repository,” but does not require the packaged service's public entry point.

## Black-Box Tests: The Packaged Application from the Outside { #black-box-tests }

A black-box test removes privileged access. It does not inject `UserService`, query `KoraAppGraph`, replace a dependency, or call a controller method. It starts the complete packaged application and
communicates over the public HTTP API.

The black-box guide builds the application's Gradle distribution, creates a Docker image from it, and starts that image through Testcontainers. PostgreSQL runs in a second container on the same Docker
network. Environment variables provide the application's normal runtime configuration. The test waits for Kora's system readiness endpoint before sending requests to the public port.

```text
JUnit process
    |
    | HTTP
    v
Kora application container ---- JDBC ----> PostgreSQL container
    |
    +-- public port: API under test
    |
    +-- system port: readiness, liveness, metrics
```

Readiness is more than a convenient delay. Waiting for `GET /system/readiness` to return `200` uses the same operational signal that an orchestrator can use in production. It avoids brittle sleeps and
log-message matching. A ready result establishes that the application graph initialized and its readiness probes permit traffic; it does not require the test to know how long startup should take.

===! ":fontawesome-brands-java: `Java`"

    ```java
    final class AppContainer extends GenericContainer<AppContainer> {

        AppContainer() {
            super(new ImageFromDockerfile("users-black-box")
                .withDockerfile(Path.of("../users-app/Dockerfile")));

            withExposedPorts(8080, 8085);
            waitingFor(
                Wait.forHttp("/system/readiness")
                    .forPort(8085)
                    .forStatusCode(200)
            );
        }

        URI publicUri() {
            return URI.create("http://" + getHost() + ":" + getMappedPort(8080));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class AppContainer : GenericContainer<AppContainer>(
        ImageFromDockerfile("users-black-box")
            .withDockerfile(Path.of("../users-app/Dockerfile"))
    ) {

        init {
            withExposedPorts(8080, 8085)
            waitingFor(
                Wait.forHttp("/system/readiness")
                    .forPort(8085)
                    .forStatusCode(200)
            )
        }

        fun publicUri(): URI {
            return URI.create("http://$host:${getMappedPort(8080)}")
        }
    }
    ```

Once ready, the test behaves like an external client:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Test
    void createsAndReturnsAUser() throws Exception {
        var request = HttpRequest.newBuilder()
            .uri(APP.publicUri().resolve("/users"))
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString("""
                {"name":"Ada","email":"ada@example.com"}
                """))
            .build();

        var response = HttpClient.newHttpClient()
            .send(request, HttpResponse.BodyHandlers.ofString());

        assertEquals(201, response.statusCode());
        assertTrue(response.body().contains("\"name\":\"Ada\""));
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Test
    fun createsAndReturnsAUser() {
        val request = HttpRequest.newBuilder()
            .uri(APP.publicUri().resolve("/users"))
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(
                """
                {"name":"Ada","email":"ada@example.com"}
                """.trimIndent()
            ))
            .build()

        val response = HttpClient.newHttpClient()
            .send(request, HttpResponse.BodyHandlers.ofString())

        assertEquals(201, response.statusCode())
        assertTrue(response.body().contains("\"name\":\"Ada\""))
    }
    ```

The strongest black-box tests avoid importing application DTOs. If both application and test serialize the same Java record, renaming a JSON field can change both sides and allow a broken public
contract to pass. Building the request and reading the response independently makes the test a genuine client. The application project can remain a build dependency so the distribution is produced
before the test, but its internal classes should not become the test's observation API.

This layer proves facts the lower layers cannot see together: the distribution is runnable; the Dockerfile contains and starts it correctly; ports are exposed and mapped; environment configuration
reaches the process; the complete graph starts; migrations run; routing selects the controller; request bodies deserialize; validation and middleware execute; services and repositories cooperate;
responses serialize with correct status codes, headers, and bodies; readiness reflects startup state.

Black-box tests are the right place for representative client journeys and production-critical contracts. A create-read-update-delete flow, authentication boundary, idempotent payment request, health
and readiness contract, or critical error response deserves outside-in verification. Tests should include successful behavior and a small set of high-value failure cases, particularly those whose HTTP
representation is part of the API.

They are poor tools for exhaustive branching. Starting containers to check twenty variations of a service-level threshold wastes time and makes failures harder to localize. They also require
disciplined data isolation. When the application and database containers are shared by a test class, each scenario must create unique data or clean state deliberately. Random mapped ports, explicit
request timeouts, container logs, liveness, readiness, and metrics make failures diagnosable without weakening the black-box boundary.

Use a black-box test when the question begins with “Can a real client…?”, “Will the packaged service…?”, or “Does the deployed contract…?”. If answering requires direct access to an application
object, it is not a black-box question.

## Following One Behavior Up the Pyramid { #one-behavior }

The cleanest way to understand the division is to follow one requirement through all three layers. Suppose duplicate email addresses must be rejected with HTTP status `409`.

At component level, `UserService` receives a mocked repository response indicating that the email already exists. The test verifies that the service selects the conflict outcome and does not call the
repository's insert method. Several related cases can run here: case normalization, whitespace handling, concurrent retry policy, audit behavior, and alternate repository failures. These tests are
fast and identify business-rule regressions precisely.

At integration level, real PostgreSQL contains an existing row protected by a unique constraint. The test calls the graph-managed service or repository and verifies the actual conflict behavior. This
proves that the schema constraint exists, migration and generated SQL agree, the driver exposes the violation in the expected form, and application code translates it correctly. One or two scenarios
can cover the important database semantics without repeating every service branch.

At black-box level, the test creates a user through `POST /users`, sends the same email again, and expects `409` with the public error body. This proves the entire contract, including JSON decoding,
controller mapping, database behavior, exception translation, and response serialization in the packaged service. One representative scenario is usually enough because lower layers already own the
permutations.

The three tests are not duplicates. They fail for different reasons and establish different claims. Removing the component cases loses cheap behavioral coverage. Removing the integration case replaces
database truth with a simulation. Removing the black-box case leaves the client contract inferred rather than observed.

## Choosing the Layer by the Failure You Want to Detect { #choosing-the-layer }

The best test boundary is the narrowest one that contains the possible defect.

If a discount calculation can be wrong with all dependencies behaving correctly, test the service component. If the calculation depends on data ordering or transaction visibility in PostgreSQL, add an
integration test. If the user can only trigger the discount through a particular request shape and the returned JSON is contractual, keep one black-box scenario.

If a generated repository query may bind the wrong field, mocking that repository removes the possible bug. Use integration. If an HTTP client must send a vendor-specific header and parse a
nonstandard error body, run it against a realistic protocol server in an integration test. If the concern is that the complete service receives the vendor endpoint from deployment configuration and
exposes the right failure to its own callers, use black-box.

If configuration changes which implementation enters the graph, a component test with `KoraAppTestConfigModifier` can verify the selected slice. If the concern is whether Testcontainers runtime
addresses create a usable JDBC pool, integration is appropriate. If the concern is whether the Docker environment variables, config file, startup command, and exposed port work together in the final
image, only black-box covers the whole claim.

This decision rule prevents two symmetrical mistakes. Testing too low produces false confidence because the relevant failure surface was mocked or bypassed. Testing too high produces slow, opaque
suites because every small rule is forced through infrastructure and HTTP.

## How Many Tests Belong at Each Level { #test-quantity }

No fixed percentage fits every Kora service. A calculation-heavy service with little infrastructure naturally has a wide component base. A thin database API may need proportionally more integration
coverage. A public gateway with complex routing and compatibility obligations may justify more black-box contracts. The pyramid is a pressure toward economical placement, not a quota.

“Many” component tests means that normal development feedback should not require Docker or a packaged application. Engineers should be able to cover new branches through small graph slices and receive
failures close to the changed code.

“Fewer” integration tests means that infrastructure behavior is sampled by capability, not repeated for every business permutation. One group can establish repository CRUD and mapping. Another can
establish transaction behavior. Another can establish a client protocol. Scenarios should justify their container and lifecycle cost by proving something mocks cannot.

“Few” black-box tests means that the suite selects critical public contracts and representative journeys. It does not mean one superficial health check. A useful black-box suite must prove startup and
readiness, at least one successful path through each critical API area, important error representations, and the production-risk behaviors that cross many layers. Its small size comes from choosing
high-information scenarios, not from lowering expectations.

Kora's fast startup can make black-box tests more practical than in frameworks with expensive runtime graph discovery. That is an opportunity to improve release confidence, but not a reason to move
all logic testing upward. Fast full startup reduces one cost; containers, networks, databases, image builds, data cleanup, and broad failure diagnosis still remain.

## Configuration and Lifecycle Change Across the Layers { #configuration-lifecycle }

All three layers need configuration, but they should receive it at their natural boundary.

Component tests use `KoraConfigModification` before the test graph is created. An inline HOCON fragment can express one scenario, a test resource can hold a reusable profile, and temporary system
properties can fill substitutions. Only components retained by the graph slice need usable configuration.

Integration tests also configure the in-process graph, but values usually come from real infrastructure getters. The PostgreSQL container owns its address and credentials; the test passes them into
the graph rather than assuming `localhost:5432`. Kora initializes pools, migrations, and repositories from those values and releases graph resources when the test context ends.

Black-box tests cannot call a graph modifier inside the packaged application. They set the container environment, mount files, join networks, and expose ports just as deployment infrastructure would.
The running process loads its normal application configuration. This boundary is deliberately less convenient because convenience would undermine the claim being tested.

Lifecycle follows the same progression. A component graph usually starts per method and contains few resources. An integration graph may share a static infrastructure container while rebuilding Kora
components, or use `PER_CLASS` when pool and migration startup dominate. A black-box class often shares application and database containers across scenarios, waits for readiness once, and enforces
data isolation inside that shared environment. Higher layers save more time through reuse, but they also accumulate more mutable state, so cleanup becomes more important.

## Common Ways to Distort the Pyramid { #pyramid-distortions }

A component test becomes misleading when every dependency is mocked even though cheap real components would strengthen the graph slice. Mock external boundaries and nondeterministic collaborators, not
every constructor parameter by reflex.

An integration test becomes a disguised component test when it starts PostgreSQL but mocks the repository whose SQL is supposedly under examination. It becomes a disguised black-box test when it
starts the full server but still reaches inside the graph for assertions. Name the boundary honestly and keep control points on one side of it.

A black-box test stops being black-box when it imports application DTOs, calls cleanup methods inside application repositories, replaces graph nodes, or reads generated graph internals. External
database inspection may be useful for diagnosis, but primary assertions should remain visible through public behavior unless persistence itself is part of the external contract.

Another distortion is treating the pyramid as execution order. Component tests should usually run on every local and CI change. Integration tests can run in the main CI pipeline when Docker is
available, perhaps grouped to reuse infrastructure. Black-box tests should run after the application artifact is built and before it is considered releasable. Faster smoke subsets may run during pull
requests, with the complete external suite at the release gate.

Flaky high-level tests are not an unavoidable price of realism. Fixed sleeps, hardcoded ports, shared identifiers, implicit startup ordering, and dependency on previous scenarios create most
instability. Testcontainers-managed lifecycle, random mapped ports, unique test data, explicit HTTP timeouts, and readiness-based waits make the environment deterministic without reaching into
application internals.

## A Balanced Kora Testing Strategy { #balanced-strategy }

For each feature, begin by identifying the public promise and the risky boundaries. Put business permutations into component tests using real graph-managed services and controlled replacements. Add
integration tests where generated code or external system semantics could invalidate the simulation. Add one or more black-box scenarios for the public journey and its most important externally
visible failure.

During development, component failures should explain logic regressions quickly. Integration failures should narrow attention to SQL, mapping, migrations, transactions, client protocols, or
infrastructure configuration. Black-box failures should answer the release question: the artifact may compile and its pieces may pass, but can the assembled service start, become ready, accept a real
request, use real infrastructure, and return the promised response?

This layered approach matches Kora's broader architecture. Compile-time graph validation removes many structural errors before runtime. Component graph slices give fast behavioral feedback without
recreating wiring by hand. Integration tests retain real infrastructure only where its semantics matter. Black-box tests run the complete package through the same public and operational boundaries
used in production.

The pyramid therefore remains simple:

```text
many component tests
    establish behavior quickly

fewer integration tests
    establish infrastructure truth

few black-box tests
    establish deployable, client-visible truth
```

Its purpose is not to rank tests from least to most valuable. It is to place each claim at the cheapest boundary capable of proving it. Kora makes those boundaries unusually coherent because all three
layers originate from the same application architecture, while each layer adds exactly the reality its question requires.
