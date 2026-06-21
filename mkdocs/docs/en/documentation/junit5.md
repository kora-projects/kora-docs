---
description: "Explains Kora JUnit 5 testing support, application graph tests, component replacement, mocks, tags, test configuration, and initialization. Use when working with @KoraAppTest, @TestComponent, @MockComponent, @Tag, @TestConfig, @TestConfigSource, Graph, Mockito."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora JUnit 5 testing support, application graph tests, component replacement, mocks, tags, test configuration, and initialization; key triggers include @KoraAppTest, @TestComponent, @MockComponent, @Tag, @TestConfig, @TestConfigSource, Graph, Mockito."
---

Module provides an extension for [JUnit 5](https://junit.org/junit5/docs/current/user-guide/) that allows testing an application through the same component graph that is used at runtime.

The Kora extension for `JUnit 5` is intended for component and integration testing of the source code that will later run in the real application.
The test uses the dependency container of the main application: it can be limited to the required components,
extended with test components, or have individual parts replaced with mocks.

Module allows you to conduct:

- `Component tests` - testing of a single component.
- `Inter-component tests` - testing of several components and their interaction with each other.
- `Integration tests` - testing of components and interaction with external systems.

It is recommended to additionally test the service artifact packaged in the final image,
as a black box using the [Testcontainers library](https://java.testcontainers.org/).

For a step-by-step walkthrough before the reference details, see [Component Testing](../guides/testing-junit.md), [Integration Testing](../guides/testing-integration.md) and [Black-Box Testing](../guides/testing-black-box.md).

## Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    testImplementation "ru.tinkoff.kora:test-junit5"
    ```

    Setup [JUnit platform](https://docs.gradle.org/current/userguide/java_testing.html#using_junit5) `build.gradle`: 
    ```groovy
    test {
        useJUnitPlatform()
        testLogging {
            showStandardStreams(true)
            events("passed", "skipped", "failed")
            exceptionFormat("full")
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    testImplementation("ru.tinkoff.kora:test-junit5")
    ```

    Setup [JUnit platform](https://docs.gradle.org/current/userguide/java_testing.html#using_junit5) `build.gradle.kts`: 
    ```groovy
    tasks.test {
        useJUnitPlatform() 
        testLogging {
            showStandardStreams = true
            events("passed", "skipped", "failed")
            exceptionFormat = TestExceptionFormat.FULL
        }
    }
    ```

## Usage { #usage }

Examples will be shown relative to such an application:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {

        @Root
        default Supplier<String> supplier() {
            return () -> "1";
        }

        @Root
        @Tag(Supplier.class)
        default Supplier<String> supplierTagged() {
            return () -> "tag1";
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application {

        @Root
        fun supplier(): Supplier<String> {
            return Supplier<String> { "1" }
        }

        @Root
        fun supplierTagged(): @Tag(Supplier::class) Supplier<String> {
            return Supplier<String> { "tag1" }
        }
    }
    ```

### Test { #test }

To enable the Kora extension, annotate the test class with `@KoraAppTest`.
The annotation connects the `JUnit 5` extension, finds the generated graph of the specified `@KoraApp` application, and prepares the dependency container for the test.

Parameters of the `@KoraAppTest` annotation:

- `value` - class annotated with `@KoraApp` whose component graph will be used in the test (`required`, no default).
- `components` - additional component classes that should be included in the test graph in addition to components discovered through `@TestComponent` (default: `{}`).
- `modules` - additional modules with component factory methods that should be connected to the test graph (default: `{}`).

Only module interfaces can be specified in `modules`. If the whole graph needs to be tested, inject `KoraAppGraph` or do not limit the graph to individual `@TestComponent` components.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(value = Application.class, 
                 components = { SomeComponent.class }, 
                 modules = { SomeModule.class })
    class SomeTests {

    }
    ```
=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(value = Application::class, 
                 components = [SomeComponent::class], 
                 modules = [SomeModule::class])
    class SomeTests {

    }
    ```

### Component { #component }

To inject and select components for testing, use the `@TestComponent` annotation.
It allows injecting components into test method arguments, the constructor, and/or test class fields, and limits the dependency container to those components.

All components listed in the test fields and/or method/constructor arguments annotated `@TestComponent` will be injected as dependencies within the test.
The test dependency container will be limited to those components and their dependencies.

It is important that components within the test must be used by at least one [@Root component](container.md#root-component) that is also specified within the test.

An example of a test where components are injected in fields:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(Application.class)
    class SomeTests {

        @TestComponent
        private Supplier<String> component1;

        @Test
        void example() {
            assertEquals("1", component1.get());
        }
    }
    ```
=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(Application::class)
    class SomeTests {

        @TestComponent
        lateinit var component1: Supplier<String>

        @Test
        fun example() {
            assertEquals("1", component1.get())
        }
    }
    ```

Example of a test where components are injected in a constructor:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(Application.class)
    class SomeTests {

        private final Supplier<String> component1;

        SomeTests(@TestComponent Supplier<String> component1) {
            this.component1 = component1;
        }

        @Test
        void example() {
            assertEquals("1", component1.get());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(Application::class)
    class SomeTests(@TestComponent val component1: Supplier<String>) {

        @Test
        fun example() {
            assertEquals("1", component1.get())
        }
    }
    ```

Example of a test where components are injected in method arguments:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(Application.class)
    class SomeTests {

        @Test
        void example(@TestComponent Supplier<String> component1) {
            assertEquals("1", component1.get());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(Application::class)
    class SomeTests {

        @Test
        fun example(@TestComponent component1: Supplier<String>) {
            assertEquals("1", component1.get())
        }
    }
    ```

#### Injection Rules { #injection-rules }

Components can be injected in three ways: into a test class field, into the constructor, or into a test method parameter.
The chosen form affects when the Kora extension can access the test class instance and which additional mechanisms are available.

- Fields suit most tests and are compatible with `KoraAppTestConfigModifier`, `KoraAppTestGraphModifier`, `PER_METHOD`, and `PER_CLASS`.
- Constructor injection is convenient for immutable fields, but is incompatible with `KoraAppTestConfigModifier` and `KoraAppTestGraphModifier`, because the extension needs a test class instance to call `config()` or `graph()`, while that instance is still being created during constructor injection.
- Method parameters are convenient for dependencies local to a specific test; with `PER_METHOD`, the graph includes parameters of the current method, while with `PER_CLASS`, the extension collects `@TestComponent` parameters from all methods of the class in advance.
- If constructor injection is used, `@TestComponent`, `@Mock`, `@Spy`, `@MockK`, or `@SpyK` cannot also be injected into test method parameters.
- In `PER_CLASS` mode, `@Mock` / `@MockK` cannot be injected into test method parameters because method-level mocks live shorter than the shared test class graph.
- The same element cannot be declared as a regular `@TestComponent`, mock, and spy at the same time: the extension will fail the test with a configuration error.

If the test needs `KoraAppTestConfigModifier` or `KoraAppTestGraphModifier`, use field injection or method parameters.
If constructor injection is required, it is better to move configuration and graph modification into a separate test `@KoraApp` or connected module.

### Tag { #tag }

In order to inject a dependency/mock that has an `@Tag`, you must specify the appropriate `@Tag` annotation next to the argument for injection:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(Application.class)
    class SomeTests {

        @Test
        void example(@Tag(Supplier.class) @TestComponent Supplier<String> component1) {
            assertEquals("?", component1.get());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(Application::class)
    class SomeTests {

        @Test
        fun example(@Tag(Supplier::class) @TestComponent component1: Supplier<String>) {
            assertEquals("?", component1.get())
        }
    }
    ```

### Application Graph { #application-graph }

If a test needs direct access to the prepared graph, inject `KoraAppGraph` into a field, constructor, or test method argument.
It can retrieve one or several components by type and can also account for `@Tag`.

Main `KoraAppGraph` methods:

- `getFirst(Type type)` / `getFirst(Class<T> type)` - return the first found component or `null`.
- `getFirst(Type type, Class<?>... tags)` / `getFirst(Class<T> type, Class<?>... tags)` - return the first component with the specified tags or `null`.
- `findFirst(...)` - returns `Optional<T>` instead of `null`.
- `getAll(...)` - returns all components of the specified type, optionally accounting for tags.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(Application.class)
    class SomeTests {

        @Test
        void example(KoraAppGraph graph) {
            var component = graph.getFirst(Supplier.class, Supplier.class);

            assertNotNull(component);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(Application::class)
    class SomeTests {

        @Test
        fun example(graph: KoraAppGraph) {
            val component = graph.getFirst(Supplier::class.java, Supplier::class.java)

            assertNotNull(component)
        }
    }
    ```

`KoraAppGraph` cannot be used as a target for `@Mock`, `@Spy`, `@MockK`, or `@SpyK`, because it is a service object of the test extension, not an application component.

### Mock { #mock }

===! ":fontawesome-brands-java: `Java`"

    It is proposed to use annotations provided by the [Mockito](https://site.mockito.org/) library together with the `@TestComponent` annotation to create component mock in Java as part of a test.

    It is required to add the [Mockito](https://site.mockito.org/) library as a `build.gradle` dependency:
    ```groovy
    testImplementation "org.mockito:mockito-core:5.18.0"
    ```

    **Important**, it is assumed that `MockitoExtension` will not be used and will be disabled, you can't combine it together with `@KoraAppTest`.

    [@Mock](https://javadoc.io/doc/org.mockito/mockito-core/latest/org/mockito/Mock.html) and [@Spy](https://javadoc.io/doc/org.mockito/mockito-core/latest/org/mockito/Spy.html) annotations and all parameters of these annotations are supported.
    It is recommended to read more about how these annotations work in the [official Mockito library documentation](https://javadoc.io/doc/org.mockito/mockito-core/latest/org/mockito/Mockito.html).

    The [@Mock](https://javadoc.io/doc/org.mockito/mockito-core/latest/org/mockito/Mock.html) annotation allows you to make a class stub of a 
    annotated component and control the behavior of its methods with `Mockito` or the methods will return default values: `void`, default values for primitives, empty collections and `null` for all other objects. 

    The stub component will be injected as a dependency into the arguments and/or fields of the test class and into all components that required it as a dependency.
    All dependent components that are not required anywhere else within the test will be excluded as unnecessary.


    Example of a test using a `@Mock` component and injecting a mock in a field:

    ```java
    @KoraAppTest(Application.class)
    class SomeTests {

        @Mock
        @TestComponent
        private Supplier<String> component1;

        @BeforeEach
        void mock() {
            Mockito.when(component1.get()).thenReturn("?");
        }

        @Test
        void example() {
            assertEquals("?", component1.get());
        }
    }
    ```

    [@Spy](https://javadoc.io/doc/org.mockito/mockito-core/latest/org/mockito/Spy.html) annotation allows you to make a spy facade of a class implementation of a
    of a component from a dependency container that will have the original behavior of the component's methods by default,
    but as with stubs, their behavior can be overridden.

    The spy component will be implemented as a dependency in the arguments and/or fields of the test class and in all components that required it as a dependency.

    Example of a test using `@Spy` component and injecting the spy in a method argument:

    ```java
    @KoraAppTest(Application.class)
    class SomeTests {

        @Test
        void example(@Spy @TestComponent Supplier<String> component1) {
            Mockito.when(component1.get()).thenReturn("?");
            assertEquals("?", component1.get());
        }
    }
    ```

    You can also make a spy from the value of a test class field.

    The spy component will be injected as a dependency in the arguments and/or fields of the test class and in all components that required it as a dependency.
    All dependent components that are not required anywhere else within the test will be excluded as unnecessary.

    Example of a test using `@Spy` spy component:

    ```java
    @KoraAppTest(Application.class)
    class SomeTests {

        @Spy
        @TestComponent
        private Supplier<String> component1 = () -> "12345";

        @Test
        void example() {
            assertEquals("12345", component1.get());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    In order to mock components in Kotlin, it is suggested to use the annotations provided by the [MockK](https://mockk.io/) library together with the `@TestComponent` annotation.

    The [MockK](https://mockk.io/) library is required to be attached as a ``build.gradle.kts`` dependency:
    ```groovy
    testImplementation("io.mockk:mockk:1.13.11")
    ```

    **Important**, it is assumed that `MockkExtension` will not be used and will be disabled, you can't combine it together with `@KoraAppTest`.

    [@MockK](https://mockk.io/#annotations) and [@SpyK](https://mockk.io/#annotations) annotations and all parameters of these annotations are supported.

    It is also possible to use [Mockito](https://site.mockito.org/) if desired. 
    For a more detailed description of how Kora and [Mockito](https://site.mockito.org/) work, you should read the Java tab of this paragraph.
    In order to improve the interaction between Mockito and Kotlin you can use the [Mockito Kotlin](https://github.com/mockito/mockito-kotlin) library.
    ```groovy
    testImplementation("org.mockito.kotlin:mockito-kotlin:5.4.0")
    ```

    **Important**, it is assumed that `MockitoExtension` will not be used and will be disabled, you can't combine it together with `@KoraAppTest`.

    [@MockK](https://mockk.io/#annotations) annotation allows you to make a class mock
    annotated component and control the behavior of its methods using `MockK`. 

    Mock component will be injected as a dependency into the arguments and/or fields of the test class and into all components that required it as a dependency.
    All dependent components that are not required anywhere else within the test will be excluded as unnecessary.

    Example of a test using `@MockK` component and injecting a mock:

    ```kotlin
    @KoraAppTest(Application::class)
    class SomeTests(@MockK @TestComponent val component1: Supplier<String>) {

        @BeforeEach
        fun mock() {
            every { component1.get() } returns "?"
        }

        @Test
        fun example() {
            assertEquals("?", component1.get())
        }
    }
    ```

    [@SpyK](https://mockk.io/#annotations) annotation allows you to make a spy facade of a class implementation of a
    of a component from a dependency container that will have the original behavior of the component's methods by default,
    but as with stubs, their behavior can be overridden.

    The spy component will be implemented as a dependency in the arguments and/or fields of the test class and in all components that required it as a dependency.

    Example of a test using `@SpyK` component and embedding the spy in a method argument:

    ```kotlin
    @KoraAppTest(Application::class)
    class SomeTests {

        @Test
        fun example(@SpyK @TestComponent component1: Supplier<String>) {
            every { component1.get() } returns "?"
            assertEquals("?", component1.get())
        }
    }
    ```

    You can also make a spy from the value of a test class field.

    The spy component will be implemented as a dependency in the arguments and/or fields of the test class and in all components that required it as a dependency.
    All dependent components that are not required anywhere else within the test will be excluded as unnecessary.

    An example of a test using the `@SpyK` spy component:

    ```kotlin
    @KoraAppTest(Application::class)
    class SomeTests {

        @field:SpyK
        @TestComponent
        val component1: Supplier<String> = Supplier { "1" }

        @Test
        fun example() {
            assertEquals("?", component1.get())
        }
    }
    ```

#### Mock strictness { #mock-strictness }

`Mockito` mocks can be checked with the `@MockitoStrictness` annotation.
It sets the verification level for `Mockito` mocks created by the Kora extension within the test class.

The extension behaves similarly to `MockitoSession`: after the test completes, it passes the created mocks to `Mockito` verification and reports unused or suspicious stubbing.
If `@MockitoStrictness` is not specified, Kora uses `Strictness.WARN`: the test does not fail, but warnings are written to the log.

Supported levels:

- `Strictness.WARN` - default value; writes warnings to the log and does not fail the test.
- `Strictness.STRICT_STUBS` - strict mode; unused stubbing fails the test, for example with `UnnecessaryStubbingException`.
- `Strictness.LENIENT` - lenient mode; disables unused stubbing checks.

If a specific `@Mock` has its own `strictness` parameter, it applies to that mock's settings.
`@MockitoStrictness` is convenient as a common level for the whole test class, so the setting does not need to be duplicated on every mock.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @MockitoStrictness(Strictness.STRICT_STUBS)
    @KoraAppTest(Application.class)
    class SomeTests {

        @Mock
        @TestComponent
        private Supplier<String> component1;

        @BeforeEach
        void mock() {
            Mockito.when(component1.get()).thenReturn("?");
        }

        @Test
        void example() {
            // component1.get() usage required
        }
    }
    ```

In the example above, `Mockito.when(component1.get()).thenReturn("?")` must be used by the test.
If the `component1.get()` call is removed from the test method, `Strictness.STRICT_STUBS` will fail the test.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @MockitoStrictness(Strictness.STRICT_STUBS)
    @KoraAppTest(Application::class)
    class SomeTests(@Mock @TestComponent val component1: Supplier<String>) {

        @BeforeEach
        fun mock() {
            on { component1.get() } doReturn "?"
        }

        @Test
        fun example() {
            // component1.get() usage required
        }
    }
    ```

For Kotlin with `Mockito Kotlin`, the same mechanism applies because verification is performed by `Mockito`.
`@MockitoStrictness` does not apply to `MockK` mocks.

### Test graph { #test-graph }

Sometimes you may need to use an extended dependency container as part of your tests.
For example, a test application can extend the main application and add components that are only needed in tests.

This approach is useful when you have different Read API and Write API applications with common components,
which may be required as part of testing one and the other.
Or, you may need some save/delete/update functions just for testing as a quick test utility.

???+ warning "Recommendation"

    **Highly Recommend Testing** applications as a [black box](https://github.com/kora-projects/kora-examples/blob/master/kora-java-crud/src/test/java/ru/tinkoff/kora/example/crud/BlackBoxTests.java)
    and rely on this approach as the primary source of truth and correctness of the application.

    Application may work differently depending on the JVM flags,
    base image and native libraries, differences between partial and full configurations,
    differences in conversion at application entry points, use of schema registries, and so on.
    Only a prod-ready image can guarantee the closest possible testing environment.

Let's imagine that the application looks like this:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {

        @Root
        default String someComponent() {
            return "1";
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application {

        @Root
        fun someComponent(): String {
            return "1"
        }
    }
    ```

In tests, you can create a separate test `@KoraApp` that extends the main application and use that graph.
For this scenario, the generated submodule of the main application is required: without it, the test application cannot inherit and connect the main graph components.

===! ":fontawesome-brands-java: `Java`"

    First, enable the parameter that creates a submodule of the main application in `build.gradle`:

    ```groovy
    compileJava {
        options.compilerArgs += [
            "-Akora.app.submodule.enabled=true"
        ]
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    First, enable the parameter that creates a submodule of the main application in `build.gradle.kts`:

    ```groovy
    ksp {
        arg("kora.app.submodule.enabled", "true")
    }
    ```

Then it is required to create an extended test graph of the application in test source's directory.
Remember to label components as `@Root` since they are most likely not used by anyone,
but the tests and will not otherwise be included in the graph:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface TestApplication extends Application {

        @Root
        default Integer someOtherComponent() {
            return 1;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface TestApplication : Application {

        @Root
        fun someOtherComponent(): Integer {
            return 1
        }
    }
    ```

===! ":fontawesome-brands-java: `Java`"

    In order for the test application graph to be generated, we need to add processors as test dependencies in `build.gradle`:

    ```groovy
    dependencies {
        testAnnotationProcessor "ru.tinkoff.kora:annotation-processors"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    In order for the test application graph to be generated, we need to add processors as test dependencies in `build.gradle.kts`:

    ```groovy
    dependencies {
        kspTest("ru.tinkoff.kora:symbol-processors")
    }
    ```

It may be required to exclude scanning of Kora generated classes by JUnit (sometimes an error occurs during test search):

===! ":fontawesome-brands-java: `Java`"

    Classes start with `$` symbol, exclude them in `build.gradle`:

    ```java
    test {
        exclude("**/\$*")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Classes start with `$` symbol, exclude them in `build.gradle.kts`:

    ```kotlin
    tasks.test {
        exclude("**/\$*")
    }
    ```

You can now use the extended application graph in your tests:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(TestApplication.class)
    class SomeTests {

        @TestComponent
        private String component1;
        @TestComponent
        private Integer component2;

        @Test
        void testSame() {
            assertEquals(component1, String.valueOf(component2));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(TestApplication::class)
    class SomeTests(val component1: String, val component2: Integer) {

        @Test
        fun testSame() {
            assertEquals(component1, component2.toString());
        }
    }
    ```

If inheritance from the main `@KoraApp` is not needed and only factory methods from a separate module should be added,
use the `modules` parameter of `@KoraAppTest`.
`modules` accepts module interfaces, not component classes:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface TestModule {

        @Root
        default Integer testOnlyComponent() {
            return 1;
        }
    }

    @KoraAppTest(value = Application.class, modules = TestModule.class)
    class SomeTests {

        @Test
        void test(@TestComponent Integer component) {
            assertEquals(1, component);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface TestModule {

        @Root
        fun testOnlyComponent(): Int {
            return 1
        }
    }

    @KoraAppTest(value = Application::class, modules = [TestModule::class])
    class SomeTests {

        @Test
        fun test(@TestComponent component: Int) {
            assertEquals(1, component)
        }
    }
    ```

Summary:

- `kora.app.submodule.enabled=true` is needed when a test `@KoraApp` extends the main `@KoraApp`.
- `@KoraAppTest(modules = ...)` suits cases where additional modules simply need to be connected to the test graph.
- Components that should appear in the limited test graph must still be reachable from `@TestComponent`, `components`, or `KoraAppGraph`.

## Test configuration { #test-configuration }

By default, the basic configuration will be used, as in the case of running a real application.

To change or add configuration within tests, the test class should implement `KoraAppTestConfigModifier`,
and the `config()` method should return a `KoraConfigModification`.

`KoraAppTestConfigModifier` cannot be used together with component injection into the test class constructor:
the extension needs to obtain the configuration modification before creating the test graph, and for that the test instance must already exist.

#### Environment variables { #environment-variables }

In case the test needs to use the [default configuration](config.md#file) that would be used when the application is running,
and you only need to substitute environment variables, you can use the `SystemProperty` mechanism in `KoraConfigModification`:

===! ":material-code-json: `Hocon`"

    Suppose there is such a configuration `application.conf`:

    ```javascript
    db {
        jdbcUrl = ${POSTGRES_JDBC_URL}
        username = ${POSTGRES_USER}
        password = ${POSTGRES_PASS}
        maxPoolSize = 10
        poolName = "example"
    }
    ```

=== ":simple-yaml: `YAML`"

    Suppose there is such a configuration `application.yaml`:

    ```yaml
    db:
      jdbcUrl: ${POSTGRES_JDBC_URL}
      username: ${POSTGRES_USER}
      password: ${POSTGRES_PASS}
      maxPoolSize: 10
      poolName: "example"
    ```

In order to use such a config and pass only environment variables, you need to return such `KoraConfigModification`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(Application.class)
    class SomeTests implements KoraAppTestConfigModifier {

        @NotNull
        @Override
        public KoraConfigModification config() {
            return KoraConfigModification
                .ofSystemProperty("POSTGRES_JDBC_URL", "jdbc:postgresql://localhost:5432/postgres")
                .withSystemProperty("POSTGRES_USER", "postgres")
                .withSystemProperty("POSTGRES_PASS", "postgres");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(Application::class)
    class SomeTests : KoraAppTestConfigModifier {

        override fun config(): KoraConfigModification {
            return KoraConfigModification
                .ofSystemProperty("POSTGRES_JDBC_URL", "jdbc:postgresql://localhost:5432/postgres")
                .withSystemProperty("POSTGRES_USER", "postgres")
                .withSystemProperty("POSTGRES_PASS", "postgres")
        }
    }
    ```

If several values need to be passed at once, use `withSystemProperties(Map<String, String>)`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(Application.class)
    class SomeTests implements KoraAppTestConfigModifier {

        @NotNull
        @Override
        public KoraConfigModification config() {
            return KoraConfigModification
                .ofSystemProperty("POSTGRES_JDBC_URL", "jdbc:postgresql://localhost:5432/postgres")
                .withSystemProperties(Map.of(
                    "POSTGRES_USER", "postgres",
                    "POSTGRES_PASS", "postgres"
                ));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(Application::class)
    class SomeTests : KoraAppTestConfigModifier {

        override fun config(): KoraConfigModification {
            return KoraConfigModification
                .ofSystemProperty("POSTGRES_JDBC_URL", "jdbc:postgresql://localhost:5432/postgres")
                .withSystemProperties(
                    mapOf(
                        "POSTGRES_USER" to "postgres",
                        "POSTGRES_PASS" to "postgres"
                    )
                )
        }
    }
    ```

### Configuration file { #configuration-file }

An example of providing a configuration as a file:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(Application.class)
    class SomeTests implements KoraAppTestConfigModifier {

        @Override
        public @Nonnull KoraConfigModification config() {
            return KoraConfigModification.ofResourceFile("application-test.conf");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(Application::class)
    class SomeTests : KoraAppTestConfigModifier {

        override fun config(): KoraConfigModification {
            return KoraConfigModification.ofResourceFile("application-test.conf")
        }
    }
    ```

### Configuration text { #configuration-text }

An example of adding a configuration as a string would look like this,
in this case only this configuration will be used without any configuration files:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(Application.class)
    class SomeTests implements KoraAppTestConfigModifier {

        @Override
        public @Nonnull KoraConfigModification config() {
            return KoraConfigModification.ofString("""
                myconfig {
                    myproperty = 1
                }
                """);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(Application::class)
    class SomeTests : KoraAppTestConfigModifier {

        override fun config(): KoraConfigModification {
            return KoraConfigModification.ofString(
                """
                myconfig {
                    myproperty = 1
                }
                """.trimIndent()
            )
        }
    }
    ```

## Container modification { #container-modification }

To add, replace, or programmatically create mocks in the application container without annotations, implement `KoraAppTestGraphModifier`
and return a `KoraGraphModification` from the `graph()` method.

`KoraAppTestGraphModifier` cannot be used together with component injection into the test class constructor:
the extension needs to obtain the graph modification before creating the graph and injecting components.

`KoraGraphModification` supports these operations:

- `addComponent(...)` - adds a new component to the test graph.
- `replaceComponent(...)` - replaces an existing component, while its dependencies remain in the graph.
- `mockComponent(...)` - replaces an existing component with a mock and removes the replaced component's real dependencies from the graph if they are no longer needed by the test.

`addComponent(...)` and `replaceComponent(...)` have overloads with `Function<KoraAppGraph, T>` if the new component should be built from already initialized graph components.
For components with `@Tag`, use overloads with `List<Class<?>> tags`.

### Adding { #adding }

An example of adding a component to a graph:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(value = Application.class)
    class SomeTests implements KoraAppTestGraphModifier {

        @Override
        public @Nonnull KoraGraphModification graph() {
            return KoraGraphModification.create()
                .addComponent(TypeRef.of(Supplier.class, Integer.class), () -> (Supplier<Integer>) () -> 1);
        }

        @Test
        void example(@TestComponent Supplier<Integer> supplier) {
            assertEquals(1, supplier.get());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(value = Application::class)
    class SomeTests : KoraAppTestGraphModifier {

        override fun graph(): KoraGraphModification {
            return KoraGraphModification.create()
                .addComponent(TypeRef.of(Supplier::class.java, Int::class.java), Supplier { Supplier { 1 } })
        }

        @Test
        fun example(@TestComponent supplier: Supplier<Int>) {
            assertEquals(1, supplier.get())
        }
    }
    ```

In case it is required to add components using a real component from the graph, this is also available through another method signature:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(value = Application.class)
    class SomeTests implements KoraAppTestGraphModifier {

        @Override
        public @Nonnull KoraGraphModification graph() {
            return KoraGraphModification.create()
                    .addComponent(TypeRef.of(Supplier.class, String.class),
                            (graph) -> {
                                final Supplier<Integer> existingComponent = (Supplier<Integer>) graph.getFirst(TypeRef.of(Supplier.class, Integer.class));
                                return (Supplier<String>) () -> "1" + existingComponent.get();
                            });
        }

        @Test
        void example(@TestComponent Supplier<String> supplier) {
            assertEquals(1, supplier.get());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(value = Application::class)
    class SomeTests : KoraAppTestGraphModifier {

        @Nonnull
        override fun graph(): KoraGraphModification {
            return KoraGraphModification.create()
                .addComponent(TypeRef.of(Supplier::class.java, String::class.java))
                { graph ->
                    val existingComponent = graph.getFirst(TypeRef.of(Supplier::class.java, Int::class.java))
                            as Supplier<Int>
                    Supplier { "1" + existingComponent.get() }
                }
        }

        @Test
        fun example(@TestComponent supplier: Supplier<String>) {
            assertEquals(1, supplier.get())
        }
    }
    ```

### Replacement { #replacement }

An example of replacing a component in a dependency container, this mechanism can also be used to create custom mocks:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(value = Application.class)
    class SomeTests implements KoraAppTestGraphModifier {

        @Override
        public @Nonnull KoraGraphModification graph() {
            return KoraGraphModification.create()
                .replaceComponent(TypeRef.of(Supplier.class, String.class), List.of(Supplier.class), () -> (Supplier<String>) () -> "?");
        }

        @Test
        void example(@Tag(Supplier.class) @TestComponent Supplier<String> supplier) {
            assertEquals("?", supplier.get());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(value = Application::class)
    class SomeTests : KoraAppTestGraphModifier {

        override fun graph(): KoraGraphModification {
            return KoraGraphModification.create()
                .replaceComponent(TypeRef.of(Supplier::class.java, String::class.java), listOf(Supplier::class.java), Supplier { Supplier { "?" } })
        }

        @Test
        fun example(@Tag(Supplier::class) @TestComponent supplier: Supplier<String>) {
            assertEquals("?", supplier.get())
        }
    }
    ```

In case it is required to replace components using a real component from the graph, this is also available through another method signature:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(value = Application.class)
    class SomeTests implements KoraAppTestGraphModifier {

        @Override
        public @Nonnull KoraGraphModification graph() {
            return KoraGraphModification.create()
                    .replaceComponent(TypeRef.of(Supplier.class, Integer.class),
                            (graph) -> {
                                final Supplier<Integer> existingComponent = (Supplier<Integer>) graph.getFirst(TypeRef.of(Supplier.class, Integer.class));
                                return (Supplier<Integer>) () -> 1 + existingComponent.get();
                            });
        }

        @Test
        void example(@TestComponent Supplier<Integer> supplier) {
            assertEquals(1, supplier.get());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(value = Application::class)
    class SomeTests : KoraAppTestGraphModifier {

        @Nonnull
        override fun graph(): KoraGraphModification {
            return KoraGraphModification.create()
                .replaceComponent(TypeRef.of(Supplier::class.java, Int::class.java))
                { graph ->
                    val existingComponent = graph.getFirst(TypeRef.of(Supplier::class.java, Int::class.java))
                            as Supplier<Int>
                    Supplier { 1 + existingComponent.get() }
                }
        }

        @Test
        fun example(@TestComponent supplier: Supplier<Int>) {
            assertEquals(1, supplier.get())
        }
    }
    ```

### Programmatic Mock { #programmatic-mock }

If a component should be replaced specifically as a mock, use `mockComponent(...)`.
Unlike `replaceComponent(...)`, this method tells the extension that the real dependencies of the replaced component are not needed and can be excluded from the test graph.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(value = Application.class)
    class SomeTests implements KoraAppTestGraphModifier {

        @Override
        public @Nonnull KoraGraphModification graph() {
            return KoraGraphModification.create()
                .mockComponent(TypeRef.of(Supplier.class, String.class), () -> Mockito.mock(Supplier.class));
        }

        @Test
        void example(@TestComponent Supplier<String> supplier) {
            Mockito.when(supplier.get()).thenReturn("?");

            assertEquals("?", supplier.get());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(value = Application::class)
    class SomeTests : KoraAppTestGraphModifier {

        override fun graph(): KoraGraphModification {
            return KoraGraphModification.create()
                .mockComponent(TypeRef.of(Supplier::class.java, String::class.java), Supplier { mockk<Supplier<String>>() })
        }

        @Test
        fun example(@TestComponent supplier: Supplier<String>) {
            every { supplier.get() } returns "?"

            assertEquals("?", supplier.get())
        }
    }
    ```

## Initialization { #initialization }

By default, `JUnit 5` uses `TestInstance.Lifecycle.PER_METHOD`, so Kora creates and cleans up the test graph for each test method.
If the container should be initialized once for the whole test class, annotate the test class with `@TestInstance(TestInstance.Lifecycle.PER_CLASS)`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @TestInstance(TestInstance.Lifecycle.PER_CLASS)
    @KoraAppTest(Application.class)
    class SomeTests {

    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @TestInstance(TestInstance.Lifecycle.PER_CLASS)
    @KoraAppTest(Application::class)
    class SomeTests {

    }
    ```

With `PER_CLASS`, one graph instance is used by all test methods in the class, and cleanup runs after the whole class completes.
This speeds up heavy integration tests, but mutable component and mock state should be handled more carefully.

Lifecycle restrictions:

- When components are injected into the constructor, `@TestComponent` or mocks cannot also be injected into test method parameters.
- When components are injected into the constructor, `KoraAppTestConfigModifier` and `KoraAppTestGraphModifier` cannot be used.
- In `PER_CLASS` mode, `@Mock` / `@MockK` cannot be injected into test method parameters; use fields or the constructor.
- For `@Nested` classes, field injection into the inner class cannot be used if the outer test class runs in `PER_CLASS` mode; use method parameters or a separate lifecycle for the nested class.
