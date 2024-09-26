The dependency container is the core of the Kora framework and is responsible for building the dependency container, validating them,
injecting and then parallel initialization.

The work of the container in Kora is divided into two parts: what is done at runtime and what is done at compile time.

## Compile Time

At compile time, components are searched building the dependency container of the entire application.
This allows validation of the dependency container at compile time, before the application actually starts.

### Container

The core of the dependency container is the interface labeled with the `@KoraApp` annotation.
This annotation should be used to label the interface within which the factory methods for creating components and [modules](#module-factory) dependencies are attached.
There can be only one such interface within an application.

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

### Components

A component is a dependency in a dependency container.
All components in Kora are Singletons. A Singleton is a class that has an instance created only once.
Components are injected only if they are [root component](#root-component), or if they are required in other components as dependencies.

Components that do not meet these requirements are not included in the dependency container.

#### Auto factory

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

#### Basic factory

A factory method is a method with the `default` modifier that returns a component, the method can take
arguments to other components as dependencies.

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

#### Module factory

Components for a dependency container can also be searched for in modules in an application project.
A module refers to an interface that contains the factory methods.
The `@Module` annotation marks the interface as a module to be injected in our container at compile time.
Module must be within the same source code directory as the class labeled `@KoraApp`.

All factory methods within module become available to the dependency container:

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

#### External module factory

Components for a dependency container can also be looked up in external modules from third-party dependencies.
A module refers to the interface that contains the factory methods.
Kora does not automatically search for modules from external dependencies as some other DI solutions do.
This allows the developer to precisely control and realize which dependencies are used in their application and to avoid
from initializing a lot of unnecessary dependencies and thus degrading the application's performance.

All required external modules from dependencies must be connected explicitly in the interface marked with the `@KoraApp` annotation through inheritance:

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

#### Submodule factory

The `@KoraSubmodule` annotation marks the interface for which to build a module for the current compilation module,
it will contain all components marked with the `@Module` and `@Component` annotations.
Annotation is useful if you are breaking your project into [multi-modules application](https://docs.gradle.org/current/userguide/multi_project_builds.html)
in terms of your `Gradle/etc.` build tool, where
each is responsible for some piece of functionality, and the `@KoraApp` application itself is built in a separate module from the logic.

An inheritor interface will be created for the interface, where all interfaces labeled `@Module` will be inherited and default-methods for classes labeled as `@Component` will be created.

For example, you have application-module that contains submodule with module:

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

And there's core application build module with application entrypoint:

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

This will plug both `SomeSubModule` and `SomeModule` modules.

#### Generic factory

If the dependency container could not find a generic factory for a particular type, the Kora container at compile time can try looking for
methods with [Generic](https://docs.oracle.com/javase/tutorial/java/generics/types.html) parameters, and use that method to create an instance of the desired class.

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

Now if some component needs GenericValidator as a dependency, this factory will be used to create it.

#### Extension mechanism

In case none of the factories were able to provide a component, Kora can try to create that dependency at compile time itself.
The extensions mechanism is provided for this purpose. Each extension is able to tell if it can create a component of the desired type.
If the extension can do this, it does the necessary codogeneration and tells you how to get that component.

For example, there are extensions that know how to create optimal Json readers and writers, JDBC repositories, and other components.
The available extensions are searched thanks to the `ServiceLocator` mechanism from all dependencies provided in the Annotation Processor scope.

The mechanism is rather system specific and is often used by internal Kora modules.

#### Standard factory

In order to provide default components by factory methods, which it is assumed that the user can override,
it is required to use the `@DefaultComponent` annotation.
If any component that does not use this annotation is found in the dependency container at compile time,
it will be given preference during injection.

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

#### Auto creation

If none of the methods above were able to provide a component,
then Kora can try to create a component on its own if it meets the requirements similar to [auto factory](#auto-factory):

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

### Component override

In case a component is provided by the library as a default dependency,
it is possible to create a factory in an application without the `@DefaultComponent` annotation and such a dependency will override it.

Since all external modules are plugged as interfaces into the core `@KoraApp` container and their factories are available,
you can simply override them as a method and provide your custom implementation.

### Root component

When a component is required to always be initialized with application startup, even if it is not a dependency of other components,
it is expected to use the `@Root` annotation over a factory method or class annotated with `@Component`.

An example of such a component might be HTTP server, Kafka consumer, cache warming component.

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

### Optional dependencies

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

    1.  Any `@Nullable` annotation will do, such as `javax.annotation.Nullable` / `jakarta.annotation.Nullable` / `org.jetbrains.annotations.Nullable` / etc.

=== ":simple-kotlin: `Kotlin`"

    If you want to introduce an optional dependency that may not exist, you should use [Kotlin Nullability]() syntax and mark such a component as Nullable.
    you should use the [Kotlin Nullability](https://kotlinlang.org/docs/null-safety.html) syntax and mark such a component as Nullable,
    then the dependency container will not crash at compile time due to the absence of the component:

    ```kotlin
    @Component
    class SomeService(val otherService: OtherService?) { }
    ```

### List of components

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

The `All` type itself has the following contract:

```java
public interface All<T> extends List<T> {}
```

This is a token type that extends `List` and can be given to constructors that expect `List`.

### Tags

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
        fun someService1(): SomeService = SomeService2()

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

#### Tag all

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

#### Tag any

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

## Runtime

The dependency container is initialized as parallel as possible within the dependency container that has been constructed.

During the execution phase of the application, the following things are done:

* Initializes all components in the dependency container
* Track changes in the dependency container
* Atomically updates the dependency container when changes are made.
* Performs a [Graceful Shutdown](#graceful-shutdown) when a SIGTERM signal is received.

All components use eager initialization, which means they are initialized immediately upon application startup.

### Entrypoint

The application entry point should cause `KoraApplication.run` to run using the dependency container created at compile time.

In case the interface labeled `@KoraApp` is called `Application`, the same package will create an `Application` class at compile time
class `ApplicationGraph` will be created in the same package to represent the dependency container implementation, and then the entry point
within the same package will look like this:

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

### Container lifecycle

The dependency container knows how to initialize all components in the correct order, and it does so in as much parallel as possible, in order to achieve the fastest possible startup time.

When the container is no longer needed, it starts the mechanism to release the components in the reverse order.

In the middle of the lifecycle, a component may be updated and then the container updates all components,
that depend on the changed component. This happens atomically: at the beginning of the process, a transaction is opened,
which closes only if all components are successfully initialized and rolls back if at least one error occurs.

### Component lifecycle

By default, all components are singletons through the constructor.
If you need to do some actions when the component is initialized, or before it is released, you must implement `Lifecycle` interface:

```java
public interface Lifecycle {
    
    void init() throws Exception;

    void release() throws Exception;
}
```

In a dependency container, all components are initialized asynchronously and in parallel as much as possible.

If you need to provide a component in a factory method with a lifecycle, you can use the `LifecycleWrapper` class:

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
                    // initialize logic
                }
            )
        }
    }
    ```

### Graceful shutdown

All integrations that Kora provides such as [HTTP server](http-server.md), [Kafka-consumer](kafka.md),
etc., support [graceful shutdown](https://www.techtarget.com/whatis/definition/graceful-shutdown-and-hard-shutdown) out of the box using
[component lifecycle](#component-lifecycle).

### Indirect dependency

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
But when we use the type wrapper `ValueOf`, we tell the container,
that `ServiceC` is in no way related to the life cycle of `ServiceB` and if `ServiceB` changes, we don't need to update `ServiceC`.

#### Updating components

Updating of components is possible if the `ValueOf` wrapper is used to inject dependencies:

```java
public interface ValueOf<T> {
    
    T get();

    void refresh();
}
```

We can get the actual state of the component in the container using the `get` method.
This mechanism is used in such components that cannot be reloaded during the execution of the application.
For example, this is the case for various servers that listen to sockets (http, grpc) - for them, request handlers are supplied via `ValueOf`, which may be subject to changes.

With the `refresh` function we can initiate a component refresh. This mechanism is for example used in a component that tracks changes to a configuration file on disk.
When the content of the file changes, it initiates a refresh of the configuration component, and further all changes are propagated through the chain of components linked by a direct link.

### Component inspection

There are situations where there is some component in a dependency container that needs to be further modified or initialized,
but we need to make sure that nobody starts working with this component before we do these actions.  
For this case there is a mechanism of component interception. You need to put an object implementing the `GraphInterceptor` interface into the container.

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
Here we expect that the method may return a modified or a different instance of an object of the given type,
and this object will be used as a dependency by other components.
