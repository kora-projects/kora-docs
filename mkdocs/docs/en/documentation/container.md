---
description: "Explains Kora compile-time dependency injection container, components, modules, factories, tags, lifecycle, graph resolution, and dependency wrappers. Use when working with @KoraApp, @Component, @Module, @KoraSubmodule, @Root, @Tag, @DefaultComponent, ValueOf."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora compile-time dependency injection container, components, modules, factories, tags, lifecycle, graph resolution, and dependency wrappers; key triggers include @KoraApp, @Component, @Module, @KoraSubmodule, @Root, @Tag, @DefaultComponent, ValueOf, All, PromiseOf."
---

The dependency container is the core of the `Kora` framework. It builds the dependency graph, validates it,
injects components, initializes them, and releases them later.
Unlike containers that assemble an application at startup by scanning the classpath, `Kora` builds most of the graph
at compile time and generates regular `Java` code for application startup.

Container work in `Kora` is split into two parts: compile time and runtime.
At compile time, `Kora` checks that all dependencies can be found and connected. At runtime, the container creates
components, manages their lifecycle, and updates affected graph parts when changes happen.

For a step-by-step walkthrough before the reference details, see [Dependency Injection Introduction](../guides/dependency-injection-introduction.md) and [Dependency Injection](../guides/dependency-injection.md).

## Compile Time { #compile-time }

At compile time, components are discovered to build the dependency container for the whole application.
This allows the dependency container to be validated before the application actually starts.

### Container { #container }

The core of the dependency container is the interface marked with the `@KoraApp` annotation.
This annotation should be used on the interface that contains factory methods for creating components
and connects [external modules](#external-module-factory).
There can be only one such interface within an application.

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

    * The class must not be abstract
    * A class should have only one public constructor
    * The class must be `final` (only if it has no aspects)
    
    ```java
    @Component
    public final class SomeService {

        private OtherService otherService;

        public SomeService(OtherService otherService) {
            this.otherService = otherService;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    * The class must not be abstract
    * A class should have only one public constructor
    * The class must not be `open` (only if it has no aspects)

    ```kotlin
    @Component
    class SomeService(val otherService: OtherService) { }
    ```

#### Method factory { #basic-factory }

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

The factory method **should not provide** a `null` value as a component.

#### Module factory { #module-factory }

Components for a dependency container can also be located in modules within an application project.
A module refers to an interface that contains the factory methods.
The `@Module` annotation marks the interface as a module to be injected into the application container at compile time.
The module must be within the same source code directory as the class marked with `@KoraApp`.

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

An inheritor interface will be generated for the interface. It will inherit all interfaces marked with `@Module`
and create factory methods for classes marked as `@Component`.

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

#### Extension mechanism { #extension-mechanism }

In case none of the factories were able to provide a component, `Kora` can try to create that dependency at compile time itself.
The extensions mechanism is provided for this purpose. Each extension is able to tell if it can create a component of the desired type.
If the extension can do this, it performs the required code generation and reports how to obtain that component.

For example, there are extensions that know how to create optimal `JsonReader` and `JsonWriter` components, repositories, and other components.
Available extensions are discovered through the `ServiceLocator` mechanism from all dependencies provided in the annotation processor scope.

This mechanism is system-level and is most often used by internal `Kora` modules.

#### Standard factory { #standard-factory }

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

#### Auto creation { #auto-creation }

If none of the methods above were able to provide a component,
then `Kora` can try to create a component on its own if it meets the requirements similar to [auto factory](#auto-factory):

===! ":fontawesome-brands-java: `Java`"

    * The class must not be abstract
    * A class should have only one public constructor
    * The class must be `final` (only if it has no aspects)

    ```java
    public final class SomeService {

        private OtherService otherService;

        public SomeService(OtherService otherService) {
            this.otherService = otherService;
        }
    }

    @KoraApp
    public interface Application {

        default SomeOtherService someOtherService(SomeService someService) {
            return new SomeOtherService(someService);
        }

        default OtherService otherService() {
            return new OtherService();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    * The class must not be abstract
    * A class should have only one public constructor
    * The class must not be `open` (only if it has no aspects)

    ```kotlin
    class SomeService(val otherService: OtherService) { }

    @KoraApp
    interface Application {

        fun someOtherService(someService: SomeService): SomeOtherService {
            return SomeOtherService(someService)
        }

        fun otherService(): OtherService = OtherService()
    }
    ```

### Component override { #component-override }

In case a component is provided by the library as a default dependency,
it is possible to create a factory in an application without the `@DefaultComponent` annotation and such a dependency will override it.

Since all external modules are connected as interfaces to the `@KoraApp` container core and their factories are available,
you can simply override them as a method and provide your custom implementation.

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

### Optional dependencies { #optional-dependencies }

===! ":fontawesome-brands-java: `Java`"

    If you want to introduce an optional dependency that may not exist, then
    it is supposed to mark such a component with any `@Nullable` annotation,
    then the dependency container will not crash at compile time due to the absence of the component:

    ```java
    @Component
    public final class SomeService {

        private OtherService otherService;

        public SomeService(@Nullable OtherService otherService) { //(1)!
            this.otherService = otherService;
        }
    }
    ```

    1.  Any `@Nullable` annotation will do, for example `javax.annotation.Nullable` / `jakarta.annotation.Nullable` / `org.jetbrains.annotations.Nullable`.

=== ":simple-kotlin: `Kotlin`"

    If you want to inject an optional dependency that may be absent, use the [`Kotlin` null-safety syntax](https://kotlinlang.org/docs/null-safety.html)
    and mark that component as allowing `null`,
    then the dependency container will not crash at compile time due to the absence of the component:

    ```kotlin
    @Component
    class SomeService(val otherService: OtherService?) { }
    ```

Optionality can be combined with container wrappers: `ValueOf<Optional<T>>`, `Optional<ValueOf<T>>`,
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
public interface All<T> extends List<T> {}
```

This is a token type that extends `List` and can be given to constructors that expect `List`.
If you need to collect references to components instead of the components themselves, the container also supports
`All<ValueOf<T>>` and `All<PromiseOf<T>>`.

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

        default ServiceC serviceA(@Tag(MyTag1.class) SomeService service) {
            return new ServiceA(service);
        }

        default ServiceD serviceB(@Tag(MyTag2.class) SomeService service) {
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
Tags also work on constructor parameters, in conjunction with `@Component` or final classes.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(MyTag1.class)
    class SomeService1 implements SomeService {

    }

    @Tag(MyTag2.class)
    final class SomeService2 implements SomeService {

    }

    final class ServiceA {

        private final SomeService service;

        public ServiceA(@Tag(MyTag1.class) SomeService service) {
            this.service = service;
        }
    }

    final class ServiceB {

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
    class SomeService1 : SomeService

    @Tag(MyTag2::class)
    class SomeService2 : SomeService

    class ServiceA(private val service: @Tag(MyTag1::class) SomeService)

    class ServiceB(private val service: @Tag(MyTag2::class) SomeService)
    ```

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

## Runtime { #runtime }

The dependency container uses as much parallelism as possible within the graph that has been built.

During application execution, the container does the following:

* Initializes all components in the dependency container
* Tracks changes in the dependency container
* Atomically updates the dependency container when changes are made
* Performs a [graceful shutdown](#graceful-shutdown) when a `SIGTERM` signal is received

All components use eager initialization, which means they are initialized immediately upon application startup.

### Entrypoint { #entrypoint }

The application entry point should call `KoraApplication.run` using the dependency container created at compile time.

If the interface marked with `@KoraApp` is named `Application`, then during compilation a class named `ApplicationGraph`
will be generated in the same package. It represents the dependency container implementation, and the entry point
in the same package will look like this:

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
        KoraApplication.run { ApplicationGraph.graph() }
    }
    ```

### Container lifecycle { #container-lifecycle }

The dependency container knows how to initialize all components in the correct order, and it does so in as much parallel as possible, in order to achieve the fastest possible startup time.

When the container is no longer needed, it starts the mechanism to release the components in the reverse order.

In the middle of the lifecycle, a component may be updated and then the container updates all components,
that depend on the changed component. This happens atomically: at the beginning of the process, a transaction is opened,
which closes only if all components are successfully initialized and rolls back if at least one error occurs.

### Component lifecycle { #component-lifecycle }

By default, all components are created as singletons through a constructor or a factory method during initialization.
If you need to do some actions when the component is initialized, or before it is released, you must implement `Lifecycle` interface:

```java
public interface Lifecycle {
    
    void init() throws Exception;

    void release() throws Exception;
}
```

In a dependency container, all components are initialized asynchronously and in parallel as much as possible.

If you need to provide a component with a lifecycle from a factory method, you can use the `LifecycleWrapper` class.
It implements two contracts at once:

* `Lifecycle` — the container will call `init()` on startup and `release()` when releasing the component
* `Wrapped<T>` — the container will inject the `T` value returned by the `value()` method

===! ":fontawesome-brands-java: `Java`"

    ```java
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

### Graceful shutdown { #graceful-shutdown }

All integrations that `Kora` provides, such as [HTTP server](http-server.md) and [Kafka consumer](kafka.md),
support [graceful shutdown](https://www.techtarget.com/whatis/definition/graceful-shutdown-and-hard-shutdown) out of the box using
[component lifecycle](#component-lifecycle).

All components that implement `AutoCloseable` will also be automatically closed by the dependency container before release.

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

Component refresh is possible if the `ValueOf` wrapper is used for dependency injection:

```java
public interface ValueOf<T> {
    
    T get();

    void refresh();
}
```

The `get()` method returns the current component state in the container.
This mechanism is used in components that cannot be reloaded while the application is running.
For example, this applies to various servers that listen on sockets (`HTTP`, `gRPC`): request handlers that may change
are supplied to them through `ValueOf`.

With the `refresh()` method, you can initiate a component refresh. This mechanism is used, for example, by a component
that tracks configuration file changes on disk.
When the file content changes, it initiates a refresh of the configuration component, and then all changes propagate
through the chain of components connected by direct dependencies.

`ValueOf` also has additional methods for convenient work with the wrapped value:

* `map(...)` — transforms the value inside `ValueOf` without changing the connection to the source component
* `optional()` — converts `ValueOf<T>` to `ValueOf<Optional<T>>`

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
you can use `Wrapped.UnwrappedValue.unwrap(...)`. This is useful for wrappers that add lifecycle or other behavior
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

### Component inspection { #component-inspection }

There are situations where a component in the container needs to be additionally modified or initialized,
but no one should start working with this component before those actions are complete.
For this case, there is a component interception mechanism. Put an object implementing the `GraphInterceptor` interface into the container.

```java
public interface GraphInterceptor<T> {

    T init(T value);

    T release(T value);
}
```

For example, this mechanism can be used to warm up the cache based on `JdbcDatabase`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class CacheWarmupInterceptor implements GraphInterceptor<JdbcDatabase> {

        @Override
        public JdbcDatabase init(JdbcDatabase value) {
            // warm up cache
        }

        @Override
        public JdbcDatabase release(JdbcDatabase value) {
            return value;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class CacheWarmupInterceptor : GraphInterceptor<JdbcDatabase> {

        override fun init(value: JdbcDatabase): JdbcDatabase {
            // warm up cache
        }

        override fun release(value: JdbcDatabase): JdbcDatabase {
            return value
        }
    }
    ```

The `GraphInterceptor` interface is almost the same as the `Lifecycle` contract, except for the return type.
The `init(T value)` method receives an already fully initialized component. The method may return a modified or completely different
instance of the given type, and that object will be used as a dependency by other components.
The `release(T value)` method receives the component before release, meaning it is still a working and not yet cleaned-up instance.
