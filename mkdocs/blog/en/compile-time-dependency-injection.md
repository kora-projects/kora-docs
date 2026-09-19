---
title: Compile-Time Dependency Injection — How the Kora Framework Builds an Application
date: 2026-08-04
description: How the Kora Framework resolves, validates, and generates the application graph at compile time — components, modules, tags, All<T>, ValueOf<T>, lifecycle, and refreshable subgraphs.
search:
  exclude: true
---

# Compile-Time Dependency Injection: How Kora Builds an Application { #compile-time-dependency-injection }

**August 4, 2026**

Dependency injection is often introduced as a convenience mechanism: instead of constructing every object manually, a class declares what it needs and the container provides it. That description is
useful, but it hides the more interesting architectural question: **when does the container decide what the application actually is?**

In many JVM frameworks, a significant part of that work happens at runtime. The container starts, discovers components, inspects constructors and factory methods, resolves dependencies, applies
qualifiers, checks for cycles, creates internal definitions, and only then assembles the object graph. The Kora Framework deliberately moves most of that reasoning into compilation.

Its dependency injection engine is best understood as a **compile-time graph compiler backed by a small runtime graph executor**. During compilation, Kora discovers providers, resolves dependency
claims, checks ambiguity, verifies tags and cycles, generates missing framework components, and produces the application graph. At runtime, the container executes that already known graph: it creates
objects, initializes lifecycle-aware components, manages references, refreshes affected nodes when necessary, and shuts everything down in dependency order.

That separation is the key to understanding Kora DI.

---

## DI as Graph Compilation { #di-as-graph-compilation }

Consider a small application:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class OrderController {

        public OrderController(OrderService service) {
        }
    }

    @Component
    public final class OrderService {

        public OrderService(OrderRepository repository) {
        }
    }

    @Component
    public final class OrderRepository {

        public OrderRepository(DataSource dataSource) {
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class OrderController(service: OrderService)

    @Component
    class OrderService(repository: OrderRepository)

    @Component
    class OrderRepository(dataSource: DataSource)
    ```

From the DI engine's perspective, these constructors describe a graph:

```text
OrderController → OrderService → OrderRepository → DataSource
```

Each constructible component becomes a node, and each constructor or factory parameter becomes a dependency requirement that has to be resolved to another node.

For example:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public OrderService(OrderRepository repository)
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class OrderService(repository: OrderRepository)
    ```

can be read as a request for exactly one component compatible with `OrderRepository`.

A tagged dependency:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public OrderService(
        @Tag(MainDb.class) OrderRepository repository) {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class OrderService(
        @Tag(MainDb::class) repository: OrderRepository
    )
    ```

asks for exactly one matching `OrderRepository` with the required tag.

A collection-like dependency:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public Dispatcher(All<Handler> handlers) {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class Dispatcher(handlers: All<Handler>)
    ```

changes the request again: instead of exactly one provider, the constructor asks for all matching `Handler` components.

The compile-time container repeatedly resolves these requirements until it has constructed the reachable application graph. If a required provider does not exist, if several equally valid providers
compete for a single injection point, or if a hard dependency cycle makes construction impossible, Kora stops compilation rather than postponing the error until startup.

This makes dependency injection less like runtime lookup and more like static graph resolution.

---

## `@KoraApp`: The Root of the Application Graph { #kora-app }

Every Kora application starts with an interface annotated with `@KoraApp`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application
    ```

That interface defines the root assembly boundary of the application. It may contain factory methods directly, or it may inherit modules that contribute infrastructure and application-level providers.

A more realistic application might look like:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends
        HoconConfigModule,
        LogbackModule,
        JsonModule,
        UndertowPublicHttpServerModule {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application :
        HoconConfigModule,
        LogbackModule,
        JsonModule,
        UndertowPublicHttpServerModule
    ```

This is not merely organizational syntax. It tells the compiler which external modules are part of the application's dependency universe.

Kora deliberately avoids a model where every classpath dependency is scanned and arbitrary framework definitions are attached implicitly. Components and modules from the current compilation scope can
participate directly, while external modules are connected through explicit inheritance from the application interface. For multi-module builds, `@KoraSubmodule` provides an additional compile-time
boundary.

During annotation processing, Kora uses the `@KoraApp` interface as the starting point for generating `ApplicationGraph`. Startup then references that generated graph directly:

===! ":fontawesome-brands-java: `Java`"

    ```java
    KoraApplication.run(ApplicationGraph::graph);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    KoraApplication.run(ApplicationGraph::graph)
    ```

The graph is therefore not a runtime-discovered structure. It is a compiled representation of how the application should be assembled.

---

## `@Component`: Declaring a Constructible Node { #component }

The simplest way to make an application class available to DI is `@Component`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class PaymentService {

        private final PaymentRepository repository;

        public PaymentService(PaymentRepository repository) {
            this.repository = repository;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class PaymentService(private val repository: PaymentRepository)
    ```

This declaration gives Kora two pieces of information. First, `PaymentService` is allowed to become a graph node. Second, its constructor tells the compiler which other nodes are required to create
it.

Kora keeps this model intentionally straightforward. A Java component has a public constructor, and its constructor parameters describe its dependencies. The framework does not generally try to
instantiate arbitrary classes merely because they happen to be constructible.

That distinction matters. Suppose we write:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class PaymentService {

        public PaymentService(PaymentRepository repository) {
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class PaymentService(repository: PaymentRepository)
    ```

but no component, module factory, generic provider, or compile-time extension ever supplies `PaymentRepository`. Kora does not silently decide to instantiate some matching class. The dependency graph
is incomplete, so compilation fails.

This explicit registration model makes every node traceable to a concrete provider mechanism rather than allowing the container to invent application structure from incidental classpath contents.

---

## Factory Methods: Providers Without `@Component` { #factory-methods }

Not every object can or should be annotated.

Third-party libraries are the obvious case. You may need an `ExecutorService`, a client from an external SDK, or some resource created through a builder API. Kora handles those through factory
methods:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {

        default ExecutorService executor() {
            return Executors.newVirtualThreadPerTaskExecutor();
        }

        default JobService jobService(ExecutorService executor) {
            return new JobService(executor);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application {

        fun executor(): ExecutorService {
            return Executors.newVirtualThreadPerTaskExecutor()
        }

        fun jobService(executor: ExecutorService): JobService {
            return JobService(executor)
        }
    }
    ```

To the graph compiler, these factory methods behave just like constructor-based providers. The first one contributes an `ExecutorService` node with no dependencies. The second contributes a
`JobService` node that depends on that executor.

Factory parameters are resolved using the same rules as constructor parameters, so the DI engine does not need a separate conceptual model for application classes and externally created objects.

This is one of the reasons Kora's container remains relatively easy to reason about: construction logic is expressed as ordinary Java or Kotlin methods, and the graph compiler uses those methods as
provider definitions.

---

## `@Module`: Grouping Related Providers { #module }

As applications grow, putting every factory method directly on `@KoraApp` becomes unwieldy. `@Module` allows related providers to be grouped:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface PaymentModule {

        default PaymentClient paymentClient(
            HttpClient httpClient,
            PaymentConfig config) {
            return new PaymentClient(httpClient, config);
        }

        default PaymentGateway paymentGateway(
            PaymentClient client) {
            return new PaymentGateway(client);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface PaymentModule {

        fun paymentClient(
            httpClient: HttpClient,
            config: PaymentConfig
        ): PaymentClient {
            return PaymentClient(httpClient, config)
        }

        fun paymentGateway(client: PaymentClient): PaymentGateway {
            return PaymentGateway(client)
        }
    }
    ```

These methods remain normal component providers. The module simply gives them a coherent boundary.

An application can then compose modules explicitly:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends
        PaymentModule,
        JsonModule,
        UndertowPublicHttpServerModule {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application :
        PaymentModule,
        JsonModule,
        UndertowPublicHttpServerModule
    ```

This makes module composition itself compile-time information. A library can publish provider modules, and the application chooses which ones become part of its graph without relying on runtime
registration hooks or global discovery.

That matters for transparency. Looking at the `@KoraApp` interface tells you a meaningful part of the application's architectural composition before the service ever starts.

---

## Reachability: Not Every Provider Becomes a Runtime Component { #reachability }

Kora's graph is not necessarily a registry of every component declaration it can discover. What ultimately matters is which nodes are reachable from the application's roots.

Consider:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class DebugReporter {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class DebugReporter
    ```

If no root or reachable component depends on `DebugReporter`, there is no strong reason to instantiate it. Merely existing in source code does not automatically imply that it must participate in
runtime initialization.

Infrastructure that needs to start independently can instead be marked as a root:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Root
    @Component
    public final class EventConsumer implements Lifecycle {
        // ...
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Root
    @Component
    class EventConsumer : Lifecycle {
        // ...
    }
    ```

HTTP servers, background workers, consumers, schedulers, and similar components often behave like graph roots because they represent active entry points into the running system.

This gives Kora DI a reachability-oriented model rather than a simple global bean registry. The resulting graph contains what the application actually needs to run.

---

## Dependency Resolution as Exact Matching { #dependency-resolution }

Once Kora has discovered possible providers, the real resolution work begins.

Suppose we have:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class CheckoutService {

        public CheckoutService(PaymentGateway gateway) {
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class CheckoutService(gateway: PaymentGateway)
    ```

The compiler effectively sees a dependency requirement described by type, tags, and cardinality. In this case the requirement is simple: resolve exactly one `PaymentGateway`.

If there is one valid provider, Kora creates the edge. If there are none, compilation fails. If there are several equally valid candidates, the dependency is ambiguous and compilation also fails.

For example:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class StripeGateway implements PaymentGateway {
    }

    @Component
    public final class InternalGateway implements PaymentGateway {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class StripeGateway : PaymentGateway

    @Component
    class InternalGateway : PaymentGateway
    ```

combined with:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class CheckoutService {

        public CheckoutService(PaymentGateway gateway) {
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class CheckoutService(gateway: PaymentGateway)
    ```

does not contain enough information to identify the intended provider.

Kora does not guess based on declaration order, classpath order, naming conventions, or some implicit ranking. The application has expressed an ambiguous architecture, so the compiler reports it.

This is an important design choice. Dependency injection remains deterministic because ambiguity has to be modeled explicitly instead of being hidden behind container heuristics.

---

## Tags Are Part of Dependency Identity { #tags }

Tags solve cases where several components share the same Java type but serve different roles.

Suppose there are two gateways:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(Primary.class)
    @Component
    public final class StripeGateway implements PaymentGateway {
    }

    @Tag(Backup.class)
    @Component
    public final class BackupGateway implements PaymentGateway {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(Primary::class)
    @Component
    class StripeGateway : PaymentGateway

    @Tag(Backup::class)
    @Component
    class BackupGateway : PaymentGateway
    ```

A consumer can state which one it requires:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class CheckoutService {

        public CheckoutService(
            @Tag(Primary.class) PaymentGateway gateway) {
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class CheckoutService(
        @Tag(Primary::class) gateway: PaymentGateway
    )
    ```

Architecturally, Kora is no longer resolving only a Java type. It is resolving a type together with a tag set.

That makes tags more than cosmetic qualifiers. They are part of the identity of the dependency request.

Using classes as tags instead of string names also keeps these distinctions within the normal Java type system. Tags can be navigated, renamed, and refactored through ordinary tooling instead of
becoming fragile string identifiers.

One detail is especially important: an untagged injection point does not mean “any component of this type.” It asks specifically for the untagged variant. If the application deliberately wants to
ignore tag distinctions, Kora exposes `Tag.Any` for that purpose.

This keeps semantic boundaries explicit. A client configured for one database, tenant, region, or transport should not accidentally satisfy an unrelated injection point simply because the raw Java
type matches.

---

## `All<T>`: When More Than One Match Is Correct { #all-t }

Ambiguity is only an error when a dependency expects a single component.

Sometimes the application genuinely wants every implementation.

Imagine:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface NotificationChannel {
        void send(Notification notification);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface NotificationChannel {
        fun send(notification: Notification)
    }
    ```

with several implementations:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class EmailChannel implements NotificationChannel {
    }

    @Component
    public final class SmsChannel implements NotificationChannel {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class EmailChannel : NotificationChannel

    @Component
    class SmsChannel : NotificationChannel
    ```

A dispatcher can request all of them:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class NotificationDispatcher {

        private final All<NotificationChannel> channels;

        public NotificationDispatcher(
            All<NotificationChannel> channels) {
            this.channels = channels;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class NotificationDispatcher(
        private val channels: All<NotificationChannel>
    )
    ```

This changes the dependency from singular to plural.

A plain `NotificationChannel` requires exactly one compatible provider. `All<NotificationChannel>` resolves every matching provider and exposes them through an iterable collection.

===! ":fontawesome-brands-java: `Java`"

    ```java
    for (var channel : channels) {
        channel.send(notification);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    for (channel in channels) {
        channel.send(notification)
    }
    ```

Unlike a normal singular dependency, `All<T>` can also validly be empty. That makes it useful for optional extension points, plugin-like patterns, event handlers, validators, interceptors, or any
other scenario where the application wants to collect zero or more implementations.

Tags combine naturally with `All<T>`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public Dispatcher(
        @Tag(External.class)
        All<NotificationChannel> channels) {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class Dispatcher(
        @Tag(External::class)
        channels: All<NotificationChannel>
    )
    ```

while `@Tag(Tag.Any.class)` allows the collection to deliberately span tagged and untagged implementations.

The DI model therefore has a small but expressive cardinality vocabulary: normal dependencies mean exactly one, nullable or optional dependencies mean zero or one, and `All<T>` means zero to many.

---

## Defaults and Application Overrides { #defaults-and-overrides }

Libraries often need to provide a default implementation without preventing applications from replacing it.

Kora models this with `@DefaultComponent`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface ClientModule {

        @DefaultComponent
        default RetryPolicy retryPolicy() {
            return new DefaultRetryPolicy();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface ClientModule {

        @DefaultComponent
        fun retryPolicy(): RetryPolicy {
            return DefaultRetryPolicy()
        }
    }
    ```

An application can then provide another component with the same type and tags. The graph builder treats the default as a fallback rather than an equal candidate, so an explicit application-level
implementation wins.

This avoids turning customization into a runtime bean-replacement mechanism. A module can ship reasonable defaults, while overriding them remains ordinary source-level composition.

---

## Missing Dependencies Become Compile Errors { #missing-dependencies }

One of the clearest consequences of compile-time DI is the location of failure.

Suppose:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class PetService {

        public PetService(PetRepository repository) {
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class PetService(repository: PetRepository)
    ```

but the application does not provide `PetRepository`.

In a runtime DI model, that mistake may survive compilation, packaging, image creation, deployment, and process startup before the container finally reports that the graph cannot be built.

Kora already knows during annotation processing that no valid provider exists. Compilation therefore stops.

More importantly, the compiler has enough graph information to explain *why* the dependency was needed. It can report the missing type, the injection point, and the dependency path leading from a
graph root to the unresolved node.

Conceptually, the failure can be understood as:

```text
PetController
    ↓
PetService
    ↓
PetRepository   ← unresolved
```

That graph path is useful because the place where resolution fails may be several dependencies away from the root that made the node reachable in the first place.

Compile-time DI therefore improves not only when the error happens, but also the context available to explain it.

---

## Cycles Are Detected as Graph Structure { #cycles }

Cycles are a natural graph problem.

A valid dependency chain might look like:

```text
A → B → C
```

while an accidental cycle looks like:

```text
A → B → C → A
```

For example:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class ServiceA {

        public ServiceA(ServiceB b) {
        }
    }

    @Component
    public final class ServiceB {

        public ServiceB(ServiceA a) {
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ServiceA(b: ServiceB)

    @Component
    class ServiceB(a: ServiceA)
    ```

Because Kora resolves the graph during compilation, it can detect this structure before the application starts.

For hard dependencies that cannot be proxied or deferred, the cycle is a compile-time error. Kora can report the actual cycle path rather than allowing the service to fail only after object creation
has already begun.

The framework can resolve some interface-based cycles through generated lazy proxies, but that does not change the underlying architectural point: cycles are visible to the graph compiler.

In many cases, the cleaner solution is not to rely on proxying at all, but to change the nature of one of the edges. That is where `ValueOf<T>` becomes important.

---

## `ValueOf<T>` Changes the Meaning of a Dependency Edge { #value-of-t }

`ValueOf<T>` may initially look like a provider abstraction:

===! ":fontawesome-brands-java: `Java`"

    ```java
    ValueOf<PaymentConfig>
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    ValueOf<PaymentConfig>
    ```

which can later be dereferenced:

===! ":fontawesome-brands-java: `Java`"

    ```java
    PaymentConfig config = paymentConfig.get();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val config: PaymentConfig = paymentConfig.get()
    ```

But in Kora's graph model it represents something more important: an indirect dependency that does not participate in lifecycle propagation in the same way as a direct dependency.

Consider:

===! ":fontawesome-brands-java: `Java`"

    ```java
    ServiceC(ServiceB serviceB)
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class ServiceC(serviceB: ServiceB)
    ```

A direct dependency means that `ServiceC` is built against a specific `ServiceB` instance. If the graph later refreshes `ServiceB`, downstream components that directly depend on it may also need to be
rebuilt.

Now change the constructor to:

===! ":fontawesome-brands-java: `Java`"

    ```java
    ServiceC(ValueOf<ServiceB> serviceB)
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class ServiceC(serviceB: ValueOf<ServiceB>)
    ```

`ServiceC` now keeps a reference to the graph node rather than a fixed `ServiceB` instance. Calling `serviceB.get()` resolves the current value. If `ServiceB` is refreshed, `ServiceC` itself can
remain alive.

That makes `ValueOf<T>` useful at architectural boundaries where one component should observe changes in another without sharing its lifecycle.

A long-running HTTP server is a good example. The server owns a listening socket and should not need to restart merely because some downstream handler structure has changed. Holding a `ValueOf` to
that changing dependency allows the server to remain stable while still observing the latest graph value.

The same mechanism can break a hard cycle:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class ServiceA {

        public ServiceA(ValueOf<ServiceB> serviceB) {
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ServiceA(serviceB: ValueOf<ServiceB>)
    ```

The relationship still exists semantically, but it is no longer a hard construction edge in the same sense.

This shows that Kora's graph models more than object references. It also models lifecycle propagation.

---

## The Graph Can Be Refreshed at Runtime { #graph-refresh }

Compile-time DI does not mean that every graph value is permanently frozen after compilation.

The **shape** of the graph is known ahead of time, but some nodes can be refreshed at runtime.

Kora's refreshable graph can rebuild a node and the directly affected downstream portion of the graph. The replacement subgraph is created and initialized first, and only then swapped into the running
application. If initialization fails, the temporary graph is released and the previous graph remains active.

This transactional refresh model makes `ValueOf<T>` particularly important because it defines where refresh propagation stops.

Suppose we have:

```text
Config
  ↓
DatabaseConfig
  ↓
DatabaseClient
  ↓
Repository
  ↓
Service
```

If every edge is direct, refreshing the configuration may require rebuilding several downstream nodes.

If a long-lived component instead depends on:

===! ":fontawesome-brands-java: `Java`"

    ```java
    ValueOf<Repository>
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    ValueOf<Repository>
    ```

that component can survive while observing the refreshed repository instance.

The graph is therefore static in structure but not necessarily static in value. Kora validates the topology at compile time and then lets runtime operations act within that validated topology.

---

## Lifecycle Follows the Dependency Graph { #lifecycle }

The same graph used for injection also tells Kora how the application should start and stop.

Consider:

```text
HTTP Server
    ↓
Controller
    ↓
Service
    ↓
Repository
    ↓
Database
```

The database must be ready before the repository, the repository before the service, and the service before the server begins accepting traffic. During shutdown, the order should be reversed.

Kora can derive this naturally from graph dependencies.

Components that own resources can implement:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface Lifecycle {
        void init() throws Exception;

        void release() throws Exception;
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface Lifecycle {
        fun init()

        fun release()
    }
    ```

For example:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class EventLoop implements Lifecycle {

        @Override
        public void init() {
            // acquire resources
        }

        @Override
        public void release() {
            // release resources
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class EventLoop : Lifecycle {

        override fun init() {
            // acquire resources
        }

        override fun release() {
            // release resources
        }
    }
    ```

The container initializes dependencies before their dependents and releases them in reverse order. `AutoCloseable` integrates with shutdown as well, and factory-created objects can be wrapped when the
original type cannot implement Kora's lifecycle interface directly.

This makes lifecycle a property of the application graph rather than a completely separate startup subsystem.

---

## Parallel Initialization Falls Out Naturally { #parallel-initialization }

Once the graph is known, Kora also knows which branches are independent.

Suppose the startup graph looks like:

```text
               ┌─ Database ─ Repository ─┐
Application ───┤                        ├─ HTTP Server
               └─ Kafka Client ─────────┘
```

The database branch and Kafka branch do not depend on each other, so they can initialize concurrently until they reach a node that requires both.

Because dependency ordering is explicit, runtime startup can schedule ready nodes in parallel instead of initializing the whole application serially.

This is an understated benefit of compile-time graph construction. The graph is not only a DI lookup structure; it is also an execution plan for initialization and shutdown.

Kora can therefore initialize independent lifecycle nodes on virtual threads while still preserving dependency correctness.

---

## `@KoraSubmodule`: Scaling DI Across Build Modules { #kora-submodule }

Large applications often span several Gradle modules:

```text
application
├── payments
├── orders
├── catalog
└── users
```

Kora's `@KoraSubmodule` provides a compile-time boundary for these cases.

A module can declare:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraSubmodule
    public interface PaymentsModule {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraSubmodule
    interface PaymentsModule
    ```

Kora processes the components and modules inside that compilation unit and generates the submodule interface needed by the application.

The main application then composes them:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends
        PaymentsModule,
        OrdersModule,
        CatalogModule {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application :
        PaymentsModule,
        OrdersModule,
        CatalogModule
    ```

At runtime there is still one application graph, but discovery work is organized around compilation boundaries.

That is important for incremental builds because changes inside one project module do not necessarily require rediscovering every component in the entire codebase. The module boundary therefore helps
not only code organization but also DI compilation scalability.

---

## Framework Features Use the Same DI Engine { #framework-features }

The container is not limited to handwritten application classes.

Many Kora integrations participate in the same resolution process.

Suppose a generated HTTP handler requires:

===! ":fontawesome-brands-java: `Java`"

    ```java
    JsonWriter<OrderResponse>
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    JsonWriter<OrderResponse>
    ```

but the application has not declared such a component explicitly.

A Kora compile-time extension can recognize that the requested dependency is generatable, create the necessary JSON writer, and feed the resulting provider back into the DI graph.

Conceptually:

```text
need JsonWriter<OrderResponse>
        ↓
no explicit provider
        ↓
ask compile-time extensions
        ↓
JSON processor can generate it
        ↓
generate $OrderResponse_JsonWriter
        ↓
register generated provider
        ↓
continue graph resolution
```

The same pattern is used by repositories, declarative HTTP clients, configuration mappings, validation, gRPC, and other generated features.

This is one of the most important architectural details in Kora. The DI compiler and the code-generation subsystems cooperate. Generated framework infrastructure becomes ordinary graph nodes, and
those nodes are resolved with the same type-and-tag rules as handwritten components.

---

## Compile-Time DI as Architecture Validation { #architecture-validation }

Once all of these mechanisms are combined, compilation becomes more than syntax and type checking.

Kora can verify questions such as whether every dependency has a provider, whether a dependency is ambiguous, whether tags match, whether graph roots are constructible, whether hard cycles exist,
whether required generated infrastructure can be produced, and whether the application can form a valid lifecycle graph.

These are architectural properties.

A traditional runtime DI framework may not answer them until the application context is created. Kora answers much of them while the compiler is already processing source.

The failure boundary therefore moves earlier:

```text
runtime-oriented model:

compile
→ package
→ build image
→ deploy
→ start JVM
→ build DI container
→ fail
```

becomes:

```text
Kora model:

compile
→ graph resolution fails
→ diagnostic
```

That is why compile-time DI should not be reduced to a startup optimization.

Faster startup is valuable, but the deeper benefit is that an invalid application graph is treated much more like invalid source code.

---

## What the Runtime Container Still Does { #runtime-container }

Kora does still have a runtime dependency container.

Its job is simply different.

At compile time, Kora determines which providers exist, how dependencies resolve, how tags and cardinalities match, which components are reachable, where cycles exist, and how the final graph is
wired.

At runtime, the graph executor creates singleton values, initializes lifecycle-aware components, stores node state, serves indirect references such as `ValueOf<T>`, performs graph refreshes, swaps
refreshed subgraphs into the live application, and releases components in the correct order.

A useful way to summarize the split is:

```text
compile time:
determine and validate the application graph

runtime:
execute and manage that graph
```

This keeps runtime dynamic where runtime state genuinely matters without requiring the application to rediscover its own architecture every time it starts.

---

## The Application Is the Graph { #application-is-graph }

A small Kora application can look deceptively simple:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {
    }

    @Component
    public final class Controller {

        public Controller(Service service) {
        }
    }

    @Component
    public final class Service {

        public Service(Repository repository) {
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application

    @Component
    class Controller(service: Service)

    @Component
    class Service(repository: Repository)
    ```

But that source already encodes a substantial amount of architecture.

`@KoraApp` defines the graph boundary. `@Component` declarations introduce providers. Constructor and factory parameters define dependency requirements. Tags refine identity. `All<T>` changes
cardinality. `ValueOf<T>` changes lifecycle coupling. `@Root` defines active graph entry points. `Lifecycle` gives nodes startup and shutdown behavior. Modules contribute additional providers.
Compile-time extensions generate infrastructure that satisfies otherwise unresolved dependencies.

Kora then validates those relationships and emits the resulting application graph.

The complete process looks roughly like this:

```text
source declarations
        ↓
discover providers
        ↓
identify graph roots
        ↓
resolve dependency requirements
        ↓
apply types, tags, defaults, and cardinality
        ↓
generate framework-provided components
        ↓
detect missing, ambiguous, or cyclic dependencies
        ↓
generate ApplicationGraph
        ↓
compile
        ↓
runtime initializes and manages the graph
```

Traditional dependency injection is often described as a container that finds objects for you.

Kora's model is more precise than that.

> **The compiler proves how the application can be assembled, generates that assembly graph, and the runtime executes it.**

That is the architectural difference behind Kora's compile-time dependency injection.
