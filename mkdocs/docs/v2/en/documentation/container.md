---
description: "Explains Kora compile-time dependency injection container, components, modules, factory modules, tags, conditions, lifecycle, graph resolution, and dependency wrappers. Use when working with @KoraApp, @Component, @Module, @KoraSubmodule, @FactoryModule, @Root, @Tag, @DefaultComponent, @Conditional, ValueOf."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora compile-time dependency injection container, components, modules, factory modules, tags, conditions, lifecycle, graph resolution, and dependency wrappers; key triggers include @KoraApp, @Component, @Module, @KoraSubmodule, @FactoryModule, @Root, @Tag, @DefaultComponent, @Conditional, ValueOf, All, PromiseOf, GraphInterceptor, KoraApplication.run."
---

The dependency container is the core of the `Kora` framework. It builds the dependency graph, validates it,
injects components, initializes them, and releases them later.
Unlike containers that assemble an application at startup by scanning the classpath, `Kora` builds most of the graph
at compile time and generates regular `Java` code for application startup.

Container work in `Kora` is split into two parts: compile time and runtime.
At compile time, `Kora` checks that all dependencies can be found and connected. At runtime, the container creates
components, manages their lifecycle, and updates affected graph parts when changes happen.

All container annotations live in the `io.koraframework.common.annotation` package,
and all runtime graph contracts live in `io.koraframework.application.graph`.

For a step-by-step walkthrough before the reference details, see [Dependency Injection Introduction](../guides/dependency-injection-introduction.md) and [Dependency Injection](../guides/dependency-injection.md).

## Compile Time { #compile-time }

At compile time, components are discovered to build the dependency container for the whole application.
This allows the dependency container to be validated before the application actually starts.

### Container { #container }

The core of the dependency container is the interface marked with the `@KoraApp` annotation.
This annotation should be used on the interface that contains factory methods for creating components
and connects [external modules](#external-module-factory).
There can be only one such interface within an application.

`@KoraApp` can only be applied to an interface. Applying it to a class fails compilation.

`Kora` annotation processors analyze source code in the compilation module where `@KoraApp` is declared,
and in modules where [`@KoraSubmodule`](#submodule-factory) is declared. Regular project modules without
`@KoraApp` or `@KoraSubmodule` do not become component discovery scopes automatically.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application { }
    ```

### Components { #components }

A component is a dependency in a dependency container.
All components in `Kora` are created as a single instance (`Singleton`).
Components are injected only if they are [root components](#root-component) or if other components need them as dependencies.

Components that do not meet these requirements are not included in the dependency container.

#### Auto factory { #auto-factory }

The `@Component` annotation marks the class as accessible via the container. The class has the following requirements:

===! ":fontawesome-brands-java: `Java`"

    * The class must not be abstract (`@Component` on an abstract class or an interface is ignored)
    * The class must have exactly one public constructor
    * The class must be `final` (only if it has no aspects)

    ```java
    @Component
    public final class SomeService {

        private final OtherService otherService;

        public SomeService(OtherService otherService) {
            this.otherService = otherService;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    * The class must not be abstract (`@Component` on an abstract class or an interface is ignored)
    * The class must have exactly one public constructor
    * The class must not be `open` (only if it has no aspects)

    ```kotlin
    @Component
    class SomeService(val otherService: OtherService)
    ```

#### Method factory { #method-factory }

A factory method is a method with the `default` modifier that returns a component.
The method can take other dependency components as arguments.

The dependency container below describes two factories, where the `otherService` factory requires a component created by the `someService` factory.
This is the most basic way in which components can be registered in a container:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {

        default SomeService someService() {
            return new SomeService();
        }

        default OtherService otherService(SomeService someService) {
            return new OtherService(someService);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application {

        fun someService(): SomeService = SomeService()

        fun otherService(someService: SomeService): OtherService {
            return OtherService(someService)
        }
    }
    ```

The factory method **should not provide** a `null` value as a component,
and it must return a reference type: a factory that returns a primitive or `void` fails compilation.

#### Module factory { #module-factory }

Components for a dependency container can also be located in modules within an application project.
A module refers to an interface that contains the factory methods.
The `@Module` annotation marks the interface as a module to be injected into the application container at compile time.
The module must be within the same compilation module as the interface marked with `@KoraApp`.

`@Module` is only supported on interfaces.

All factory methods within the module become available to the dependency container:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface SomeModule {

        default SomeService someService() {
            return new SomeService();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface SomeModule {

        fun someService(): SomeService = SomeService()
    }
    ```

#### External module factory { #external-module-factory }

Components for a dependency container can also be looked up in external modules from third-party dependencies.
A module refers to the interface that contains the factory methods.
`Kora` does not automatically search for modules from external dependencies as some other DI solutions do.
This lets the developer precisely control which dependencies are used in the application and avoid
initializing unnecessary components.

All required external modules from dependencies must be connected explicitly in the interface marked with the `@KoraApp` annotation through inheritance:

Such a module can be declared in any interface: in a third-party library, in a separate project module, or next to `@KoraApp` itself.
The important part is that the `@KoraApp` interface explicitly connects it through inheritance.
An external module does not need the `@Module` annotation — inheritance is what connects it.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends LogbackModule, JsonModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : LogbackModule, JsonModule
    ```

#### Submodule factory { #submodule-factory }

The `@KoraSubmodule` annotation marks the interface for which a module should be built for the current compilation module.
It will contain all components marked with the `@Module` and `@Component` annotations.
This annotation is useful when you split a project into a [multi-project application](https://docs.gradle.org/current/userguide/multi_project_builds.html)
from the `Gradle` build tool point of view, where each module is responsible for its own part of functionality,
and the application with `@KoraApp` is assembled in a separate compilation module.
This approach helps structure a large project by domain areas and improve build time:
changes in one project module do not force the annotation processor to analyze the entire application code again.

An inheritor interface named `<InterfaceName>SubmoduleImpl` will be generated for the interface. It will inherit all interfaces marked with `@Module`
and create factory methods for classes marked as `@Component`. The application connects the annotated interface itself,
and `Kora` resolves the generated implementation for it.

For example, you have a separate application module that contains this `@KoraSubmodule`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface SomeSmallModule {

        default SomeService someService() {
            return new SomeService();
        }
    }

    @KoraSubmodule
    public interface SomeSubModule {

        default OtherService otherService(SomeService someService) {
            return new OtherService(someService);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface SomeModule {

        fun someService(): SomeService = SomeService()
    }

    @KoraSubmodule
    interface SomeSubModule {

        fun otherService(someService: SomeService): OtherService {
            return OtherService(someService)
        }
    }
    ```

And there is the main application module with the assembly point for the whole application:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends SomeSubModule {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : SomeSubModule
    ```

This will connect the `SomeModule` module found through `SomeSubModule` to the final application container.

A common real-world use of `@KoraSubmodule` is a separate `Gradle` module that owns one domain area and simply
aggregates the [external modules](#external-module-factory) it needs (databases, caches, and so on) by extending them,
together with its own `@Component` classes and `@Module` interfaces. The application module then connects the
generated submodules the same way it connects any other module:

===! ":fontawesome-brands-java: `Java`"

    ```java
    // in the "pet" Gradle module
    @KoraSubmodule
    public interface PetModule extends JdbcDatabaseModule, CaffeineCacheModule { }

    // in the application Gradle module
    @KoraApp
    public interface Application extends PetModule, VetModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // in the "pet" Gradle module
    @KoraSubmodule
    interface PetModule : JdbcDatabaseModule, CaffeineCacheModule

    // in the application Gradle module
    @KoraApp
    interface Application : PetModule, VetModule
    ```

#### Factory module { #factory-module }

The `@FactoryModule` annotation marks a module method whose **return value is itself a module**.
The returned object is registered in the container as a regular component, and its public methods are
processed as component factories.

This makes it possible to build a module whose behavior is parameterized by ordinary constructor arguments,
which a plain `interface` module cannot do. `Kora` itself uses this: `JdbcDatabaseModule` provides its components
through `new JdbcDatabaseFactoryModule("jdbc")`, where the string is the configuration path the module reads.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public class InnerModule {

        private final Config config;

        public InnerModule(Config config) {
            this.config = config;
        }

        public SomeService someService() {
            return new SomeService(config);
        }
    }

    @Module
    public interface OuterModule {

        @FactoryModule
        default InnerModule inner(Config config) { //(1)!
            return new InnerModule(config);
        }
    }
    ```

    1.  The method may take any graph components as arguments, just like a regular factory method.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class InnerModule(private val config: Config) {

        fun someService(): SomeService = SomeService(config)
    }

    @Module
    interface OuterModule {

        @FactoryModule
        fun inner(config: Config): InnerModule { //(1)!
            return InnerModule(config)
        }
    }
    ```

    1.  The method may take any graph components as arguments, just like a regular factory method.

The graph in the example above contains two nodes: `InnerModule` and the `SomeService` it produces.
Methods inherited by the returned type from its supertypes are processed as factories too.
`@FactoryModule` also works on methods declared directly in the `@KoraApp` interface,
and the annotated method must return a class or an interface type.

##### Factory module tag { #factory-module-tag }

A `@Tag` placed on the `@FactoryModule` method tags the **module instance**.
Inside the module class, `@Tag(Tag.Factory.class)` means "use the tag of the enclosing factory module".
This is how one factory module type can be declared several times with different tags and produce several
independently configured sets of components:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public class DataSourceModule {

        private final String configPath;

        public DataSourceModule(String configPath) {
            this.configPath = configPath;
        }

        @Tag(Tag.Factory.class) //(1)!
        public DataSourceConfig config(Config config, ConfigValueMapper<DataSourceConfig> mapper) {
            return mapper.mapOrThrow(config.get(this.configPath));
        }

        @Tag(Tag.Factory.class)
        public DataSource dataSource(@Tag(Tag.Factory.class) DataSourceConfig config) { //(2)!
            return new DataSource(config);
        }
    }

    @KoraApp
    public interface Application {

        @Tag(MainDb.class)
        @FactoryModule
        default DataSourceModule mainDb() {
            return new DataSourceModule("db.main");
        }

        @Tag(ReplicaDb.class)
        @FactoryModule
        default DataSourceModule replicaDb() {
            return new DataSourceModule("db.replica");
        }
    }
    ```

    1.  The produced component gets the tag of the factory module method, so `@Tag(MainDb.class)` and `@Tag(ReplicaDb.class)` respectively.
    2.  On a parameter, `@Tag(Tag.Factory.class)` requests the component that was produced by the **same** factory module instance.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class DataSourceModule(private val configPath: String) {

        @Tag(Tag.Factory::class) //(1)!
        fun config(config: Config, mapper: ConfigValueMapper<DataSourceConfig>): DataSourceConfig {
            return mapper.mapOrThrow(config.get(configPath))
        }

        @Tag(Tag.Factory::class)
        fun dataSource(@Tag(Tag.Factory::class) config: DataSourceConfig): DataSource { //(2)!
            return DataSource(config)
        }
    }

    @KoraApp
    interface Application {

        @Tag(MainDb::class)
        @FactoryModule
        fun mainDb(): DataSourceModule = DataSourceModule("db.main")

        @Tag(ReplicaDb::class)
        @FactoryModule
        fun replicaDb(): DataSourceModule = DataSourceModule("db.replica")
    }
    ```

    1.  The produced component gets the tag of the factory module method, so `@Tag(MainDb::class)` and `@Tag(ReplicaDb::class)` respectively.
    2.  On a parameter, `@Tag(Tag.Factory::class)` requests the component that was produced by the **same** factory module instance.

If the factory module method has no tag, `@Tag(Tag.Factory)` resolves to "no tag" and the produced components are untagged.
Using `@Tag(Tag.Factory)` outside a factory module is a compile-time error.

#### Generic factory { #generic-factory }

If the dependency container could not find a factory for a particular type, the `Kora` container can try to find
methods with generic parameters at compile time and use such a method to create an instance of the required class.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface SomeModule {

        default <T> GenericValidator<T> genericValidator(SomeValidationEntity<T> entity) {
            return new GenericValidator<>(entity);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface SomeModule {

        fun <T> genericValidator(entity: SomeValidationEntity<T>): GenericValidator<T> {
            return GenericValidator(entity)
        }
    }
    ```

Now, if some component needs `GenericValidator` as a dependency, this factory will be used to create it.

##### Generic Type Information { #type-ref }

If a factory method needs to know the exact generic type currently requested by the container, it can inject `TypeRef<T>`.
This is useful for infrastructure components that create a dependency by the shape of the type, not only by the raw class.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface SomeModule {

        default <T> Validator<List<T>> listValidator(Validator<T> validator, TypeRef<T> typeRef) {
            return new ListValidator<>(validator, typeRef);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface SomeModule {

        fun <T> listValidator(validator: Validator<T>, typeRef: TypeRef<T>): Validator<List<T>> {
            return ListValidator(validator, typeRef)
        }
    }
    ```

`TypeRef<T>` carries generic type information through `Java` type erasure. Most application components do not need it,
but it is useful for universal factories, mappers, and container extensions.
`TypeRef<T>` is not a graph node: the container fills it in from the resolved type of the claim, so
requesting it never fails with a missing dependency.

#### Extension mechanism { #extension-mechanism }

In case none of the factories were able to provide a component, `Kora` can try to create that dependency at compile time itself.
The extensions mechanism is provided for this purpose. Each extension is able to tell if it can create a component of the desired type.
If the extension can do this, it performs the required code generation and reports how to obtain that component.

For example, there are extensions that know how to create optimal `JsonReader` and `JsonWriter` components, repositories,
declarative `HTTP` clients, `gRPC` stubs, configuration mappers, validators, and `MapStruct`/`Konvert` mappers.
Available extensions are discovered through the `ServiceLoader` mechanism from all dependencies provided in the annotation processor scope.

This mechanism is system-level and is most often used by internal `Kora` modules.

#### Standard factory { #default-factory }

In order to provide default components by factory methods, which it is assumed that the user can override,
it is required to use the `@DefaultComponent` annotation.
If the dependency container finds any component of the same type and with the same tags at compile time, but without `@DefaultComponent`,
the user component will be preferred during injection.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface SomeModule {

        @DefaultComponent
        default SomeService someService() {
            return new SomeService();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface SomeModule {

        @DefaultComponent
        fun someService(): SomeService = SomeService()
    }
    ```

`@DefaultComponent` can be placed both on a factory method and on a `@Component` class.
A `@DefaultComponent` candidate is also skipped when a [list of components](#list-of-components) is collected
and at least one non-default candidate of the same type exists.

#### Explicit registration { #explicit-registration }

Every component in the graph comes from an explicit declaration: a [`@Component`](#auto-factory) class,
a [factory method](#method-factory) in the `@KoraApp` interface or in a connected [module](#module-factory),
a [factory module](#factory-module), a [generic factory](#generic-factory), or the [extension mechanism](#extension-mechanism).

`Kora` does not instantiate a class that was never registered. If a class is used as a dependency but is not
declared anywhere, compilation fails with a `No component found for dependency` error rather than silently
constructing the class. See [graph build errors](#graph-build-errors) for the exact diagnostics.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component //(1)!
    public final class SomeService {

        private final OtherService otherService;

        public SomeService(OtherService otherService) {
            this.otherService = otherService;
        }
    }

    @KoraApp
    public interface Application {

        default SomeOtherService someOtherService(SomeService someService) {
            return new SomeOtherService(someService);
        }

        default OtherService otherService() { //(2)!
            return new OtherService();
        }
    }
    ```

    1.  Without `@Component` (or a factory method returning `SomeService`) the graph does not build.
    2.  `OtherService` is registered by a factory method, so `SomeService` can be constructed.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component //(1)!
    class SomeService(val otherService: OtherService)

    @KoraApp
    interface Application {

        fun someOtherService(someService: SomeService): SomeOtherService {
            return SomeOtherService(someService)
        }

        fun otherService(): OtherService = OtherService() //(2)!
    }
    ```

    1.  Without `@Component` (or a factory method returning `SomeService`) the graph does not build.
    2.  `OtherService` is registered by a factory method, so `SomeService` can be constructed.

There is one deliberate exception to this rule. Types that `Kora` builds itself — mappers, converters, cache key mappers
and similar contracts referenced through `@Mapping` — must **not** be annotated with `@Component` when they have no
constructor dependencies, because `Kora` already instantiates them directly and a second declaration produces a
`Multiple components match dependency` error. Decide by the constructor:

* the class takes constructor dependencies — it must be a graph component (`@Component` or a factory method)
* the class has no constructor dependencies — leave it unannotated

### Component override { #component-override }

In case a component is provided by the library as a default dependency,
it is possible to create a factory in an application without the `@DefaultComponent` annotation and such a dependency will override it.

Since all external modules are connected as interfaces to the `@KoraApp` container core and their factories are available,
you can simply override them as a method and provide your custom implementation.
Any [tags](#tags) declared on the original factory method have to be repeated on the override,
because the tag is what identifies the component in the graph:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface EmailModule {

        final class EmailTag {
            private EmailTag() {}
        }

        @Tag(EmailTag.class)
        @DefaultComponent
        default Supplier<String> emailNotifierHeaderSupplier() {
            return () -> "[EMAIL DEFAULT] ";
        }
    }

    @KoraApp
    public interface Application extends EmailModule {

        @Tag(EmailModule.EmailTag.class)
        @Override
        default Supplier<String> emailNotifierHeaderSupplier() {
            return () -> "[EMAIL OVERRIDDEN] ";
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface EmailModule {

        class EmailTag private constructor()

        @Tag(EmailTag::class)
        @DefaultComponent
        fun emailNotifierHeaderSupplier(): Supplier<String> {
            return Supplier { "[EMAIL DEFAULT] " }
        }
    }

    @KoraApp
    interface Application : EmailModule {

        @Tag(EmailModule.EmailTag::class)
        override fun emailNotifierHeaderSupplier(): Supplier<String> {
            return Supplier { "[EMAIL OVERRIDDEN] " }
        }
    }
    ```

### Root component { #root-component }

When a component is required to always be initialized with application startup, even if it is not a dependency of other components,
it is expected to use the `@Root` annotation over a factory method or class annotated with `@Component`.

An example of such a component might be an `HTTP` server, a `Kafka` consumer, a cache warming component, or a runnable background task handler.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {

        @Root
        default SomeService someService() {
            return new SomeService();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application {

        @Root
        fun someService(): SomeService = SomeService()
    }
    ```

Roots are the entry points of graph resolution: everything that is not reachable from a root is dropped from the container.
An application that declares no root at all fails to compile:

```
@KoraApp has no root components.

Fix:
  - Check that modules with @Root components are plugged-in.
  - Annotate at least one component or module method with @Root.
  - Check that root component is visible from this @KoraApp module set.
```

This is also the reason why a [`Lifecycle`](#component-lifecycle) component that only prepares external state,
and that nobody depends on, needs `@Root` — otherwise it silently disappears from the graph together with everything it pulled in.

### Conditional components { #conditional-component }

A component can be excluded from the container at startup based on a condition evaluated at runtime.
The condition itself is a component implementing `GraphCondition`, registered under a `@Tag` that names it,
and the component that depends on it is marked with `@Conditional(tag = ...)`.

```java
public interface GraphCondition {

    ConditionResult eval();

    sealed interface ConditionResult {

        record Matched(String reason) implements ConditionResult {}

        record Failed(String reason) implements ConditionResult {}
    }
}
```

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class OnPrimaryNode implements GraphCondition {

        @Override
        public ConditionResult eval() {
            return "primary".equals(System.getenv("NODE_ROLE"))
                    ? ConditionResult.matched("NODE_ROLE is primary")
                    : ConditionResult.failed("NODE_ROLE is not primary");
        }
    }

    @KoraApp
    public interface Application {

        @Tag(OnPrimaryNode.class) //(1)!
        default GraphCondition onPrimaryNode() {
            return new OnPrimaryNode();
        }

        @Root
        @Conditional(tag = OnPrimaryNode.class) //(2)!
        default LeaderElectionJob leaderElectionJob() {
            return new LeaderElectionJob();
        }
    }
    ```

    1.  The condition is an ordinary component of type `GraphCondition`, identified by its tag.
    2.  Exactly one `GraphCondition` component must exist for the tag, otherwise compilation fails.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class OnPrimaryNode : GraphCondition {

        override fun eval(): GraphCondition.ConditionResult {
            return if (System.getenv("NODE_ROLE") == "primary") {
                GraphCondition.ConditionResult.matched("NODE_ROLE is primary")
            } else {
                GraphCondition.ConditionResult.failed("NODE_ROLE is not primary")
            }
        }
    }

    @KoraApp
    interface Application {

        @Tag(OnPrimaryNode::class) //(1)!
        fun onPrimaryNode(): GraphCondition = OnPrimaryNode()

        @Root
        @Conditional(tag = OnPrimaryNode::class) //(2)!
        fun leaderElectionJob(): LeaderElectionJob = LeaderElectionJob()
    }
    ```

    1.  The condition is an ordinary component of type `GraphCondition`, identified by its tag.
    2.  Exactly one `GraphCondition` component must exist for the tag, otherwise compilation fails.

Conditions are evaluated when the graph is initialized, and again on every graph refresh:

* if the condition is `Matched`, the component is created as usual
* if the condition is `Failed`, the node stays empty and reading it throws `Graph node value was not initialized because condition failed: <reason>`
* a [list of components](#list-of-components) silently skips components whose condition failed
* `@Conditional` is also allowed on `@Root` components, in which case the whole subtree behind that root is not created

When several candidates of one type compete for the same injection point and **all** of them are conditional,
`Kora` does not fail at compile time: it picks the one whose condition matched at runtime.
If none matched, or more than one matched, the graph fails to initialize.

`GraphCondition` also provides `GraphCondition.and(...)` and `GraphCondition.or(...)` for composing conditions.

### Optional dependencies { #optional-dependencies }

===! ":fontawesome-brands-java: `Java`"

    If you want to introduce an optional dependency that may not exist, then
    it is supposed to mark such a component with a `@Nullable` annotation,
    then the dependency container will not crash at compile time due to the absence of the component:

    ```java
    @Component
    public final class SomeService {

        private final OtherService otherService;

        public SomeService(@Nullable OtherService otherService) { //(1)!
            this.otherService = otherService;
        }
    }
    ```

    1.  `Kora` recognizes any annotation whose simple name is `Nullable`; the one shipped with `Kora` is
        [JSpecify](https://jspecify.dev) `org.jspecify.annotations.Nullable`, available transitively from the framework core.
        JSpecify annotations are **type-use** annotations, so their position matters in qualified and generic types
        (`Outer.@Nullable Inner`, `List<@Nullable String>`).

=== ":simple-kotlin: `Kotlin`"

    If you want to inject an optional dependency that may be absent, use the [`Kotlin` null-safety syntax](https://kotlinlang.org/docs/null-safety.html)
    and mark that component as allowing `null`,
    then the dependency container will not crash at compile time due to the absence of the component:

    ```kotlin
    @Component
    class SomeService(val otherService: OtherService?)
    ```

An absent dependency can also be requested as `java.util.Optional<T>`, in which case the container injects an empty
`Optional` instead of failing. Optionality can be combined with container wrappers: `ValueOf<Optional<T>>`, `Optional<ValueOf<T>>`,
`PromiseOf<Optional<T>>`, and `Optional<PromiseOf<T>>`. This is useful when a dependency may be absent,
but the component still needs deferred access or the ability to refresh it through the container.

### List of components { #list-of-components }

There can be many instances of the same type in a container, and if you want to collect them all in one place, you should use the special type `All`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface SomeModule {

        default HandlerA handlerA() {
            return new HandlerA();
        }

        default HandlerB handlerB() {
            return new HandlerB();
        }

        default SomeProcessor someProcessor(All<Handler> handlers) {
            return new SomeProcessor(handlers);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface SomeModule {

        fun handlerA(): HandlerA = HandlerA()

        fun handlerB(): HandlerB = HandlerB()

        fun someProcessor(handlers: All<Handler>): SomeProcessor {
            return SomeProcessor(handlers)
        }
    }
    ```

For example, we have some entity `Handler` and it is injected by N different types in a container.
`SomeProcessor` while consuming all possible implementations of that type.
**Important**: the example above takes all `Handler` instances without tags.

The `All` type itself has the following contract:

```java
public sealed interface All<T> extends Iterable<T> { }
```

`All<T>` is an `Iterable<T>`, not a `List<T>`: iterate it with a `for` loop, or copy it into a collection if you need
random access. If you need to collect references to components instead of the components themselves, the container also supports
`All<ValueOf<T>>` and `All<PromiseOf<T>>`. Requesting `All<T>` for a type that nothing provides is not an error —
the collection is simply empty. `All.of(...)` builds a static instance, which is convenient in tests.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Root
    @Component
    public final class NotifyRunner {

        private final All<Notifier> notifiers;

        public NotifyRunner(All<Notifier> notifiers) {
            this.notifiers = notifiers;
        }

        public void notifyAll(String user, String message) {
            for (var notifier : notifiers) {
                notifier.notify(user, message);
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Root
    @Component
    class NotifyRunner(private val notifiers: All<Notifier>) {

        fun notifyAll(user: String, message: String) {
            for (notifier in notifiers) {
                notifier.notify(user, message)
            }
        }
    }
    ```

### Tags { #tags }

Sometimes there is a need to provide different instances of the same type to different components. For this purpose, they can be differentiated by tags.
In order to do this, there is an `@Tag` annotation that takes a tag class as input.
A mapping linkage is expected, where a component is registered with a particular tag and at the injection point it is declared with exactly the same tag.

It is the class that is used, not the string literal, because it is easier to navigate through the code and easier to refactor.

This is how you can inject different instances of a class with a common interface to different injection points:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface SomeModule {

        @Tag(MyTag1.class)
        default SomeService someService1() {
            return new SomeService1();
        }

        @Tag(MyTag2.class)
        default SomeService someService2() {
            return new SomeService2();
        }

        default ServiceA serviceA(@Tag(MyTag1.class) SomeService service) {
            return new ServiceA(service);
        }

        default ServiceB serviceB(@Tag(MyTag2.class) SomeService service) {
            return new ServiceB(service);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface SomeModule {

        @Tag(MyTag1::class)
        fun someService1(): SomeService = SomeService1()

        @Tag(MyTag2::class)
        fun someService2(): SomeService = SomeService2()

        fun serviceA(@Tag(MyTag1::class) service: SomeService): ServiceA {
            return ServiceA(service)
        }

        fun serviceB(@Tag(MyTag2::class) service: SomeService): ServiceB {
            return ServiceB(service)
        }
    }
    ```

Tags above the method tell you which tag to register the component with, and tags at injection points tell you which tagged component to expect.
Tags also work on `@Component` classes and their constructor parameters.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(MyTag1.class)
    @Component
    public final class SomeService1 implements SomeService { }

    @Tag(MyTag2.class)
    @Component
    public final class SomeService2 implements SomeService { }

    @Component
    public final class ServiceA {

        private final SomeService service;

        public ServiceA(@Tag(MyTag1.class) SomeService service) {
            this.service = service;
        }
    }

    @Component
    public final class ServiceB {

        private final SomeService service;

        public ServiceB(@Tag(MyTag2.class) SomeService service) {
            this.service = service;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface SomeService

    @Tag(MyTag1::class)
    @Component
    class SomeService1 : SomeService

    @Tag(MyTag2::class)
    @Component
    class SomeService2 : SomeService

    @Component
    class ServiceA(@Tag(MyTag1::class) private val service: SomeService)

    @Component
    class ServiceB(@Tag(MyTag2::class) private val service: SomeService)
    ```

In `Kotlin` the annotation is placed on the constructor **parameter**, before the parameter name, not inside the type.

#### Tag custom { #tag-custom }

You can also create your own tag annotations and work with them. One example is the [`@Json` annotation](json.md).

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(MyTag.class)
    @interface MyTag { }

    public interface SomeModule {

        @MyTag
        default SomeService someService() {
            return new SomeService();
        }

        default OtherService otherService(@MyTag SomeService service) {
            return new OtherService(service);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(MyTag::class)
    annotation class MyTag

    interface SomeModule {

        @MyTag
        fun someService(): SomeService = SomeService()

        fun otherService(@MyTag service: SomeService): OtherService {
            return OtherService(service)
        }
    }
    ```

#### Tag all { #tag-all }

You can also use a tag to get a list of all components by a specific tag:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface SomeModule {

        @Tag(MyTag.class)
        default HandlerA handlerA() {
            return new HandlerA();
        }

        @Tag(MyTag.class)
        default HandlerB handlerB() {
            return new HandlerB();
        }

        default SomeProcessor someProcessor(@Tag(MyTag.class) All<Handler> handlers) {
            return new SomeProcessor(handlers);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface SomeModule {

        @Tag(MyTag::class)
        fun handlerA(): HandlerA = HandlerA()

        @Tag(MyTag::class)
        fun handlerB(): HandlerB = HandlerB()

        fun someProcessor(@Tag(MyTag::class) handlers: All<Handler>): SomeProcessor {
            return SomeProcessor(handlers)
        }
    }
    ```

#### Tag any { #tag-any }

To get a list of all components with and without a tag, you need to use a special tag type `@Tag.Any`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface SomeModule {

        @Tag(MyTag.class)
        default HandlerA handlerA() {
            return new HandlerA();
        }

        default HandlerB handlerB() {
            return new HandlerB();
        }

        default SomeProcessor someProcessor(@Tag(Tag.Any.class) All<Handler> handlers) {
            return new SomeProcessor(handlers);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface SomeModule {

        @Tag(MyTag::class)
        fun handlerA(): HandlerA = HandlerA()

        fun handlerB(): HandlerB = HandlerB()

        fun someProcessor(@Tag(Tag.Any::class) handlers: All<Handler>): SomeProcessor {
            return SomeProcessor(handlers)
        }
    }
    ```

`@Tag.Any` only makes sense at the injection point: it declares that any tag is acceptable there.
An injection point without a tag matches only components registered without a tag.

### Circular dependencies { #circular-dependencies }

Because `Kora` builds and validates the whole dependency graph at compile time, a dependency cycle
(component `A` needs `B`, `B` needs `A`, possibly through more components in between) is detected during compilation
rather than blowing up at runtime. How such a cycle is handled depends on how the dependency inside the cycle is declared.

**Direct dependency on a `final` class (or any non-interface type).**
Such a cycle cannot be resolved and compilation fails. The error names the type that closes the cycle, prints the cycle,
and suggests the ways out:

```
Circular dependency found:
  io.koraframework.example.ServiceA (no tags)

  Dependency cycle:
    @--- component  io.koraframework.example.ServiceB
    ^--- component  io.koraframework.example.ServiceA [CYCLE]

Fix:
  - Break the cycle with ValueOf<T> or PromiseOf<T> where lazy access is valid.
  - Move shared state into a separate component.
  - Do not create dependency cycles in io.koraframework.application.graph.Lifecycle.
```

**Dependency declared through an interface (or a non-`final` class).**
`Kora` breaks the cycle automatically: for the interface-typed dependency it generates a lazy proxy that implements
`io.koraframework.common.PromisedProxy<T>` and injects the proxy instead of the real component. The proxy resolves the
actual component from the graph on first access (and re-resolves it after a graph refresh), so both components can be
constructed. No action is required from the developer, but keep in mind that the proxied side becomes usable only after
the graph is fully bound, so it must not be called from a constructor.

In the example below `ServiceAImpl` and `ServiceBImpl` reference each other through interfaces, so the cycle is broken
by an auto-generated `PromisedProxy` and the graph resolves successfully:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface ServiceA { }

    public interface ServiceB { }

    @Component
    public final class ServiceAImpl implements ServiceA {

        public ServiceAImpl(ServiceB serviceB) { }
    }

    @Component
    public final class ServiceBImpl implements ServiceB {

        public ServiceBImpl(ServiceA serviceA) { }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface ServiceA

    interface ServiceB

    @Component
    class ServiceAImpl(serviceB: ServiceB) : ServiceA

    @Component
    class ServiceBImpl(serviceA: ServiceA) : ServiceB
    ```

The reliable way to break a cycle deliberately is to inject one side through [`ValueOf<T>`](#indirect-dependency)
or [`PromiseOf<T>`](#updating-components) instead of a direct dependency. This decouples the consumer from the other
component's lifecycle, so the container no longer treats the two as a hard cycle:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class ServiceAImpl implements ServiceA {

        public ServiceAImpl(ValueOf<ServiceB> serviceB) { }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ServiceAImpl(serviceB: ValueOf<ServiceB>) : ServiceA
    ```

### Graph build errors { #graph-build-errors }

All graph errors are compile-time errors reported on the exact source element that caused them.
Each message states what failed, where it was required from, and a `Fix:` block with the possible resolutions.

**A dependency has no provider.** The message prints the whole path from the root down to the missing claim:

```
No component found for dependency:
  io.koraframework.example.PetRepository (no tags)

Required at:
  io.koraframework.example.Application#petService(io.koraframework.example.PetRepository)
  parameter: io.koraframework.example.PetRepository repository

Dependency resolution path:
  ^--- factory  io.koraframework.example.Application#petController(...)
  ^--- factory  io.koraframework.example.Application#petService(...)
  ^--- io.koraframework.example.PetRepository    [MISSING]

Fix:
  - Add @Component to an implementation of io.koraframework.example.PetRepository.
  - Add a module method that returns io.koraframework.example.PetRepository.
  - Include a module that provides io.koraframework.example.PetRepository in @KoraApp.
```

The message can carry two extra blocks:

* a `Note:` block listing components of the same type registered under a **different** tag — the usual sign of a forgotten or mismatched `@Tag`
* a `Hint:` block for well-known types, for example telling you to annotate a model with `@Json` when a `JsonWriter` is missing

**Several providers match one injection point.** The candidates are listed with the factory or component that declared them:

```
Multiple components match dependency:
  io.koraframework.example.PetService (no tags)

Required at:
  petController(io.koraframework.example.PetService)
  parameter: io.koraframework.example.PetService petService

  Candidates:
  - factory  io.koraframework.example.Application#petServicePrimary()
  - factory  io.koraframework.example.Application#petServiceSecondary()

Fix:
  - Add different @Tag(...) annotations to candidates and request the needed tag.
  - Mark fallback candidate with @DefaultComponent.
  - Remove one duplicate provider.
```

**Other frequent build failures:**

* `@KoraApp has no root components.` — nothing in the graph is annotated with [`@Root`](#root-component)
* `Circular dependency found:` — see [circular dependencies](#circular-dependencies)
* `Component condition cannot be resolved:` — a [`@Conditional`](#conditional-component) tag has no `GraphCondition` component
* `@Component class must have exactly one public constructor.` — see [auto factory](#auto-factory)
* `Kora submodule was not generated yet:` — the [`@KoraSubmodule`](#submodule-factory) module was compiled without the `Kora` annotation processor

## Runtime { #runtime }

The dependency container uses as much parallelism as possible within the graph that has been built.
Each node is created, initialized, and released on its own virtual thread, in dependency order.

During application execution, the container does the following:

* Initializes all components in the dependency container
* Tracks changes in the dependency container
* Atomically updates the dependency container when changes are made
* Performs a [graceful shutdown](#graceful-shutdown) when a `SIGTERM` signal is received

All components use eager initialization, which means they are initialized immediately upon application startup.

### Entrypoint { #entrypoint }

The application entry point should call `KoraApplication.run` using the dependency container created at compile time.

If the interface marked with `@KoraApp` is named `Application`, then during compilation a class named `ApplicationGraph`
will be generated in the same package. It implements `Supplier<ApplicationGraphDraw>` and exposes a static `graph()` method,
so the entry point in the same package will look like this:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

`KoraApplication.run` has the signature `public static void run(Supplier<ApplicationGraphDraw> supplier)`.
It builds the graph, logs how long initialization took, registers a shutdown hook that releases the graph,
and then blocks the calling thread until shutdown. If initialization fails, the error is logged and the JVM exits with code `-1`.

If you need the graph object itself — in tests or in advanced flows where you look up a component or trigger a refresh
manually — call `ApplicationGraph.graph().init()`, which returns an `InitializedGraph` (a `RefreshableGraph` with
`init()` and `release()`).

### Container lifecycle { #container-lifecycle }

The dependency container knows how to initialize all components in the correct order, and it does so in as much parallel as possible, in order to achieve the fastest possible startup time.

When the container is no longer needed, it starts the mechanism to release the components in the reverse order.

In the middle of the lifecycle, a component may be updated and then the container updates all components,
that depend on the changed component. This happens atomically: the container builds the affected part of the graph
into a temporary copy, and only when every component in it has been initialized successfully does it swap the copy in
and release the replaced objects. If at least one component fails, the temporary objects are released and the old graph stays in place.

### Component lifecycle { #component-lifecycle }

By default, all components are created as singletons through a constructor or a factory method during initialization.
If you need to do some actions when the component is initialized, or before it is released, you must implement `Lifecycle` interface:

```java
public interface Lifecycle {

    void init() throws Exception;

    void release() throws Exception;
}
```

In a dependency container, all components are initialized in parallel as much as the graph allows,
each on its own virtual thread.

If you need to provide a component with a lifecycle from a factory method, you can use the `LifecycleWrapper` class.
It implements two contracts at once:

* `Lifecycle` — the container will call `init()` on startup and `release()` when releasing the component
* `Wrapped<T>` — the container will inject the `T` value returned by the `value()` method

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface SomeModule {

        default Wrapped<SomeService> someService() {
            return new LifecycleWrapper<>(new SomeService(),
                    (component) -> {
                        // initialize logic
                    },
                    (component) -> {
                        // release logic
                    });
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface SomeModule {

        fun someService(): Wrapped<SomeService> {
            return LifecycleWrapper(SomeService(),
                { component ->
                    // initialize logic
                },
                { component ->
                    // release logic
                }
            )
        }
    }
    ```

If you need to return a custom wrapper, it must implement `Wrapped<T>`:

```java
public interface Wrapped<T> {

    T value();
}
```

A component provided as `Wrapped<T>` can be injected both as `T` (the container unwraps it) and as `Wrapped<T>` itself,
including through the `ValueOf`, `PromiseOf`, and `All` wrappers.

### Graceful shutdown { #graceful-shutdown }

All integrations that `Kora` provides, such as [HTTP server](http-server.md) and [Kafka consumer](kafka.md),
support [graceful shutdown](https://www.techtarget.com/whatis/definition/graceful-shutdown-and-hard-shutdown) out of the box using
[component lifecycle](#component-lifecycle).

Components are released in reverse dependency order. For each component the container first runs the
[graph interceptors](#component-inspection) `beforeRelease`, then `Lifecycle.release()`, and finally `AutoCloseable.close()`,
so a component that implements `AutoCloseable` is closed automatically even without implementing `Lifecycle`.

### Indirect dependency { #indirect-dependency }

Consider the following example:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface SomeModule {

        default ServiceA serviceA() {
            return new ServiceA();
        }

        default ServiceB serviceB() {
            return new ServiceB();
        }

        default ServiceC serviceC(ServiceA serviceA, ValueOf<ServiceB> serviceB) {
            return new ServiceC(serviceA, serviceB);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface SomeModule {
        fun serviceA(): ServiceA = ServiceA()

        fun serviceB(): ServiceB = ServiceB()

        fun serviceC(serviceA: ServiceA, serviceB: ValueOf<ServiceB>): ServiceC {
            return ServiceC(serviceA, serviceB)
        }
    }
    ```

We have two services, and a third service that depends on them. But there is a difference in the lifecycle.
If we take the type as a dependency directly, then we tell the container that when we update the `ServiceA` component, we need to update the `ServiceC` component in the same way.
But when we use the `ValueOf` type wrapper, we tell the container
that `ServiceC` is not connected to the lifecycle of `ServiceB`, and if `ServiceB` changes, `ServiceC` does not need to be updated.

#### Updating components { #updating-components }

The `ValueOf` wrapper gives a component a live reference to another component instead of a fixed instance:

```java
public interface ValueOf<T> {

    T get();
}
```

The `get()` method returns the current component state in the container.
This mechanism is used in components that cannot be reloaded while the application is running.
For example, this applies to various servers that listen on sockets (`HTTP`, `gRPC`): request handlers that may change
are supplied to them through `ValueOf`.

`ValueOf` also has additional methods for convenient work with the wrapped value:

* `map(...)` — transforms the value inside `ValueOf` without changing the connection to the source component
* `optional()` — converts `ValueOf<T>` to `ValueOf<Optional<T>>`

A refresh itself is initiated through the graph, by passing the `Node<T>` of the component that changed:

```java
public interface RefreshableGraph extends Graph {

    void refresh(Node<?> fromNode);
}
```

Everything that depends on that node through a **direct** dependency is rebuilt; everything that is connected only
through `ValueOf` or `PromiseOf` keeps its instance and just observes the new value.
This is how the built-in configuration file watcher works: it injects `RefreshableGraph` together with the
`Node<ConfigOrigin>` of the application config, and calls `graph.refresh(node)` when the file on disk changes.

If a component needs a deferred reference, it can use `PromiseOf<T>`.
The `get()` method returns `Optional<T>`: before graph binding it is empty, and after binding it receives the current component from the container.

```java
public interface PromiseOf<T> {

    Optional<T> get();
}
```

Like `ValueOf`, `PromiseOf` supports `map(...)` and `optional()`.
Most business code only needs a direct dependency or `ValueOf`; `PromiseOf` is intended for lower-level scenarios
where a component needs deferred access to another graph part.

If a component received through `ValueOf<Wrapped<T>>` needs to be passed further as a regular `ValueOf<T>`,
you can use `Wrapped.unwrap(...)`. This is useful for wrappers that add lifecycle or other behavior
but should expose a regular value outward.

#### Refresh listeners { #refresh-listener }

If a component needs to know that the graph was successfully refreshed, it can implement `RefreshListener`:

```java
public interface RefreshListener {

    void graphRefreshed() throws Exception;
}
```

The container calls `graphRefreshed()` after a successful graph refresh. If a component is both a value wrapper and a refresh listener,
it can implement the combined `WrappedRefreshListener<T>` interface.

`RefreshListener` is only needed to receive a notification after refresh completion. It is not required for the container
to recreate a component. If a refresh affects a component or its dependencies, and other components injected it directly,
without `ValueOf` or `PromiseOf`, those dependent components will also be refreshed automatically.

### Graph access { #graph-access }

Infrastructure components sometimes need the container itself rather than a particular dependency.
Three types can be injected for that:

* `Graph` — read-only access: `get(Node<T>)`, `valueOf(Node<T>)`, `promiseOf(Node<T>)`
* `RefreshableGraph` — the same plus `refresh(Node<?>)`
* `Node<T>` — the handle of a specific component in the graph, resolved by type and tag exactly like a normal dependency

`Graph` and `RefreshableGraph` are not components themselves: the container passes itself in, so requesting them
never adds a node and never fails. `Node<T>`, on the contrary, resolves a real component and pulls it into the graph.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Root
    @Component
    public final class ConfigReloader implements Lifecycle {

        private final RefreshableGraph graph;
        private final Node<AppConfig> configNode;

        public ConfigReloader(RefreshableGraph graph, Node<AppConfig> configNode) {
            this.graph = graph;
            this.configNode = configNode;
        }

        public void reload() {
            graph.refresh(configNode);
        }

        @Override
        public void init() { }

        @Override
        public void release() { }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Root
    @Component
    class ConfigReloader(
        private val graph: RefreshableGraph,
        private val configNode: Node<AppConfig>
    ) : Lifecycle {

        fun reload() {
            graph.refresh(configNode)
        }

        override fun init() { }

        override fun release() { }
    }
    ```

`Node<T>` cannot be requested for a nullable type; inject the dependency directly if nullable access is required.

### Component inspection { #component-inspection }

There are situations where a component in the container needs to be additionally modified or initialized,
but no one should start working with this component before those actions are complete.
For this case, there is a component interception mechanism. Put an object implementing the `GraphInterceptor` interface into the container.

```java
public interface GraphInterceptor<T> {

    T afterInit(T value);

    T beforeRelease(T value);
}
```

For example, this mechanism can be used to warm up the cache based on `JdbcDataSource`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class CacheWarmupInterceptor implements GraphInterceptor<JdbcDataSource> {

        @Override
        public JdbcDataSource afterInit(JdbcDataSource value) {
            // warm up cache
            return value;
        }

        @Override
        public JdbcDataSource beforeRelease(JdbcDataSource value) {
            return value;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class CacheWarmupInterceptor : GraphInterceptor<JdbcDataSource> {

        override fun afterInit(value: JdbcDataSource): JdbcDataSource {
            // warm up cache
            return value
        }

        override fun beforeRelease(value: JdbcDataSource): JdbcDataSource {
            return value
        }
    }
    ```

An interceptor is an ordinary component: it can be declared with `@Component` or by a factory method,
and it may take dependencies of its own.

The `GraphInterceptor` interface is almost the same as the `Lifecycle` contract, except for the return type.
The `afterInit(T value)` method is called after the component has been created and its own `Lifecycle.init()` has finished.
The method may return a modified or completely different
instance of the given type, and that object will be used as a dependency by other components.
The `beforeRelease(T value)` method receives the component before release, meaning it is still a working and not yet cleaned-up instance,
and it runs before `Lifecycle.release()` and `AutoCloseable.close()`.

An interceptor is bound to a component by the **exact** declared type of that component — `GraphInterceptor<JdbcDataSource>`
intercepts a component declared as `JdbcDataSource`, not its subtypes — and by tag: an untagged interceptor intercepts
untagged components, and `@Tag(Tag.Any.class)` on the interceptor makes it intercept components with any tag.
