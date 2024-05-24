Module provides an `Extension` for [JUnit5](https://junit.org/junit5/docs/current/user-guide/) that allows you to easily test your application.

The concept of the JUnit 5 Kora extension is to test the source code that will eventually be used in production.
This implies that dependency container of the main application is involved in the test,
it can be limited or its parts can be replaced by stubs if the test requires.

## Dependency

=== ":fontawesome-brands-java: `Java`"

    Dependency `build.gradle`:
    ```groovy
    testImplementation "ru.tinkoff.kora:test-junit5"
    ```

    Setup [JUnit platform](https://docs.gradle.org/current/userguide/java_testing.html#using_junit5) `build.gradle`: 
    ```groovy
    test {
        useJUnitPlatform()
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Dependency `build.gradle.kts`:
    ```groovy
    testImplementation("ru.tinkoff.kora:test-junit5")
    ```

    Setup [JUnit platform](https://docs.gradle.org/current/userguide/java_testing.html#using_junit5) `build.gradle.kts`: 
    ```groovy
    tasks.test {
        useJUnitPlatform() 
    }
    ```

## Usage

Examples will be shown relative to such an application:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {

        @Root
        Supplier<String> supplier() {
            return () -> "1";
        }

        @Root
        @Tag(Supplier.class)
        Supplier<String> supplierTagged() {
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

### Test

The `@KoraAppTest` annotation is supposed to be used to annotate the test class.

Parameters of the `@KoraAppTest` annotation:

- `value` - required parameter that points to the class annotated by `@KoraApp`, representing a graph of all dependencies that will be available within the test.
- `components` - list of components to be initialized within the test,
  components that are not declared within the test are specified using special annotation `@TestComponent`.

### Component

In order to use components within a test, it is suggested to use the `@TestComponent` annotation
which allows injecting component dependencies into arguments and/or fields of the test class.

All components listed in the test fields and/or method/constructor arguments annotated `@TestComponent` will be injected as dependencies within the test.
Entire dependency container will be limited to just those components and their dependencies within the test.

It is important that components within the test must be used by at least one [@Root component](container.md#root-component) that is also specified within the test.

An example of a test where components are injected in fields:

=== ":fontawesome-brands-java: `Java`"

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

=== ":fontawesome-brands-java: `Java`"

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

=== ":fontawesome-brands-java: `Java`"

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

#### Tag

In order to inject a dependency/mock that has an `@Tag`, you must specify the appropriate `@Tag` annotation next to the argument for injection:

=== ":fontawesome-brands-java: `Java`"

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
        fun example(@Tag(Supplier.class) @TestComponent component1: Supplier<String>) {
            assertEquals("?", component1.get())
        }
    }
    ```

#### Mock

=== ":fontawesome-brands-java: `Java`"

    It is proposed to use annotations provided by the [Mockito](https://site.mockito.org/) library together with the `@TestComponent` annotation to create component mock in Java as part of a test.

    It is required to add the [Mockito](https://site.mockito.org/) library as a `build.gradle` dependency:
    ```groovy
    testImplementation "org.mockito:mockito-core:5.7.0"
    ```

    [@Mock](https://javadoc.io/doc/org.mockito/mockito-core/latest/org/mockito/Mock.html) and [@Spy](https://javadoc.io/doc/org.mockito/mockito-core/latest/org/mockito/Spy.html) annotations and all parameters of these annotations are supported.
    It is recommended to read more about how these annotations work in the [official Mockito library documentation](https://javadoc.io/doc/org.mockito/mockito-core/latest/org/mockito/Mockito.html).

    The [@Mock](https://javadoc.io/doc/org.mockito/mockito-core/latest/org/mockito/Mock.html) annotation allows you to make a class stub of a 
    annotated component and control the behavior of its methods with `Mockito` or the methods will return default values: `void`, default values for primitives, empty collections and `null` for all other objects. 

    The stub component will be injected as a dependency into the arguments and/or fields of the test class and into all components that required it as a dependency.
    All dependent components that are not required anywhere else within the test will be excluded for non-necessity.

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
        void example(@MSpy @TestComponent Supplier<String> component1) {
            Mockito.when(component1.get()).thenReturn("?");
            assertEquals("?", component1.get());
        }
    }
    ```

    You can also make a spy from the value of a test class field.

    The spy component will be injected as a dependency in the arguments and/or fields of the test class and in all components that required it as a dependency.
    All dependent components that are not required anywhere else within the test will be excluded for non-necessity.

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
    testImplementation("io.mockk:mockk:1.13.8")
    ```

    [@MockK](https://mockk.io/#annotations) and [@SpyK](https://mockk.io/#annotations) annotations and all parameters of these annotations are supported.

    It is also possible to use [Mockito](https://site.mockito.org/) if desired. 
    For a more detailed description of how Kora and [Mockito](https://site.mockito.org/) work, you should read the Java tab of this paragraph.
    To improve the interaction between Mockito and Kotlin you can use the [Mockito Kotlin](https://github.com/mockito/mockito-kotlin) library.

    [@MockK](https://mockk.io/#annotations) annotation allows you to make a class mock
    annotated component and control the behavior of its methods using `MockK`. 

    Mock component will be injected as a dependency into the arguments and/or fields of the test class and into all components that required it as a dependency.
    All dependent components that are not required anywhere else within the test will be excluded for non-necessity.

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
    All dependent components that are not required anywhere else within the test will be excluded for non-necessity.

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

## Configuration setting

By default, the basic configuration will be used, as in the case of running a real application.

For configuration changes/additions within tests, it is assumed that the test class implements the `KoraAppTestConfigModifier` interface,
where it is required to implement the `KoraConfigModification` method of providing config modification.

It is forbidden to use `KoraAppTestConfigModifier` and implementation in the constructor, because in this case it is impossible to get the configuration before implementation.

#### Environment variables

In case the test needs to use the [default configuration](config.md#_3) that would be used when the application is running,
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

=== ":fontawesome-brands-java: `Java`"

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

### Configuration file

An example of providing a configuration as a file:

=== ":fontawesome-brands-java: `Java`"

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

### Configuration text

An example of adding a configuration as a string would look like this,
in this case only this configuration will be used without any configuration files:

=== ":fontawesome-brands-java: `Java`"

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

## Container modification

In order to add/replace/mock components within an unannotated application dependency container requires implementing the `KoraAppTestGraphModifier` interface and
Implement a method to provide a dependency container modifier.

It is forbidden to use `KoraAppTestGraphModifier` and embedding in the constructor because then you cannot get the graph before embedding.

### Adding

An example of adding a component to a graph:

=== ":fontawesome-brands-java: `Java`"

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

=== ":fontawesome-brands-java: `Java`"

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

### Replacement

An example of replacing a component in a dependency container:

=== ":fontawesome-brands-java: `Java`"

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

In case it is required to add components using a real component from the graph, this is also available through another method signature:

=== ":fontawesome-brands-java: `Java`"

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

## Initialization

In case you want to initialize the dependency container once within the entire test class, you should annotate the test class with `@TestInstance(TestInstance.Lifecycle.PER_CLASS)`:

=== ":fontawesome-brands-java: `Java`"

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

The default behavior is to initialize the container every time of every test method.
