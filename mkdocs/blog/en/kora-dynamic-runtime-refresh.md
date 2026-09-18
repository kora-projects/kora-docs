---
title: Do Production Services Really Need a Dynamic Application Graph? — Kora Framework
description: How the Kora Framework keeps the application graph static while supporting runtime refresh, feature flags, and dynamic routing where they belong.
search:
  exclude: true
---
# Do Production Services Really Need a Dynamic Application Graph?

The phrase *dynamic application* is used so loosely in backend engineering that it often hides several completely different requirements.

A production service is obviously dynamic. Requests arrive with different data. Feature flags change while the process is running. Credentials rotate. Tenants appear and disappear. Rate limits move. Remote endpoints fail over. Retry budgets change. Business rules depend on current state. Configuration may be reloaded. Traffic is routed differently according to headers, accounts, regions, experiments, or operational policy.

From that observation, it is tempting to make a much stronger claim: because application behavior changes at runtime, the dependency injection container must also discover components, choose implementations, assemble proxies, scan the classpath, and mutate the dependency topology at runtime.

Those two ideas are not the same.

```text
Dynamic application behavior
            ≠
Dynamic dependency graph
```

Kora's dependency-injection model is built around that distinction. The framework determines the application's component topology at compile time, validates that topology, and generates ordinary code for it. Yet the running application is not frozen. Component instances have lifecycle. Configuration can be watched and reloaded. Parts of the graph can be refreshed. Long-lived components can reference the current version of another component through `ValueOf<T>`. Collections of known implementations can be injected and selected at runtime. Tags distinguish implementations. Application logic can route between strategies based on configuration, feature flags, tenant data, request context, health, latency, or any other runtime signal.

The structural question and the behavioral question are simply separated.

For most backend services, that separation is not a limitation. It is a more accurate model of what actually changes.

A typical service has an architecture that looks approximately like this:

```text
HTTP controller
      ↓
application service
      ↓
repository
      ↓
database
```

or:

```text
Kafka consumer
      ↓
domain handler
      ↓
repository
      ↓
database
```

or:

```text
scheduler
      ↓
job
      ↓
HTTP client
      ↓
external service
```

The requests, records, SQL rows, feature flags, credentials, endpoints and policies may change constantly, but the fact that `OrderService` depends on `OrderRepository` usually does not become unknown at 14:37 on a Tuesday.

That difference is the foundation of the Kora Framework's approach.

> **Most backend applications are dynamic in data and configuration, not in their fundamental dependency structure. Kora deliberately keeps the application graph static while allowing runtime behavior where it actually belongs.**

The question is therefore not whether Kora supports runtime dynamism. It clearly does. The real question is where dynamism should live.

Kora's answer is that dependency topology should be explicit and checked ahead of time when it is known ahead of time, while changing policies, configuration, state and decisions should remain runtime concepts.

That is a surprisingly useful boundary.

---

## The Word "Dynamic" Hides Several Different Things

A useful discussion has to separate at least three levels:

```text
Compile-time topology
        ≠
Runtime component state
        ≠
Runtime application behavior
```

These layers answer different questions.

**Compile-time topology** answers:

- Which components may exist?
- Which component depends on which other component?
- Which implementation satisfies an interface?
- Which tags distinguish multiple implementations?
- Which factories construct components?
- Which lifecycle relationships exist?
- Does the graph contain missing or ambiguous dependencies?
- Does the graph contain an invalid cycle?

**Runtime component state** answers:

- What configuration values does a component currently use?
- Which endpoint is active?
- Which credentials are current?
- Which version of a refreshable component is currently installed?
- What cache contents exist?
- What connection is healthy?
- What current policy parameters are loaded?

**Runtime application behavior** answers:

- Which payment provider should this request use?
- Which tenant policy applies?
- Is a feature enabled for this account?
- Which replica should receive this read?
- Which retry policy applies to this operation?
- Should this request be rejected by a rate limit?
- Which business strategy should execute?

A runtime DI container is one way of implementing some of these concerns, but it is not the only way and often not the most natural way.

The important architectural question is whether the *set of possible components and their dependency relationships* is itself unknown until runtime.

For the majority of production services, it is not.

---

# The Typical Backend Is Structurally Predictable

Consider a payment service.

At build time, the team already knows that the application may use Stripe and Adyen:

```text
PaymentController
      ↓
PaymentService
      ↓
PaymentRouter
     ↙   ↘
Stripe  Adyen
```

At runtime, the chosen provider may depend on:

- country;
- merchant;
- currency;
- feature flag;
- provider health;
- experiment allocation;
- current routing policy.

That is highly dynamic behavior.

But no unknown Java class needs to appear from nowhere.

The set of strategies is known. The selection is dynamic.

That can be expressed directly:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class PaymentRouter {

        private final StripePaymentProvider stripe;
        private final AdyenPaymentProvider adyen;
        private final PaymentRoutingConfig config;

        public PaymentRouter(
            StripePaymentProvider stripe,
            AdyenPaymentProvider adyen,
            PaymentRoutingConfig config
        ) {
            this.stripe = stripe;
            this.adyen = adyen;
            this.config = config;
        }

        public PaymentProvider providerFor(Payment payment) {
            return switch (config.providerFor(payment.country())) {
                case STRIPE -> stripe;
                case ADYEN -> adyen;
            };
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class PaymentRouter(
        private val stripe: StripePaymentProvider,
        private val adyen: AdyenPaymentProvider,
        private val config: PaymentRoutingConfig
    ) {

        fun providerFor(payment: Payment): PaymentProvider {
            return when (config.providerFor(payment.country())) {
                Provider.STRIPE -> stripe
                Provider.ADYEN -> adyen
            }
        }
    }
    ```

The graph is static:

```text
StripePaymentProvider
AdyenPaymentProvider
PaymentRouter
```

The behavior is dynamic:

```text
request
   ↓
runtime policy
   ↓
choose provider
```

Nothing is lost by knowing the possible providers at compile time.

In fact, something is gained: the compiler can verify that both providers exist and are constructible before deployment.

---

# Static Graph Does Not Mean Static Behavior

This is the misconception worth eliminating first.

A static dependency graph says:

> The framework knows the set of components and their dependency relationships.

It does **not** say:

> The values, decisions and state inside those components can never change.

A web server has a stable place in the graph while serving millions of different requests.

A repository has a stable type while reading continuously changing data.

A feature-flag client has a stable dependency relationship while flag values change continuously.

A credentials provider can be a stable component while credentials rotate.

A routing service can remain the same instance while its routing table changes.

A rate limiter can remain wired to the same service while quotas change.

A `ValueOf<T>` can remain a stable graph edge while the current `T` instance is refreshed.

This can be summarized as:

```text
Stable structure
      ↓
dynamic state
      ↓
dynamic decisions
      ↓
dynamic behavior
```

The service does not need a mutable type topology to be dynamic.

---

# What Kora Actually Makes Static

Kora's compile-time model determines dependency structure before the application starts.

A component can come from:

- an explicitly annotated component;
- a factory method;
- a module;
- an external module explicitly connected to the application;
- a factory module;
- a generic factory;
- a compile-time extension.

The framework then resolves those declarations into the application graph.

If a dependency is missing, compilation fails.

If multiple candidates make injection ambiguous, compilation fails.

If the graph contains an invalid cycle, compilation fails.

If a required module is not connected, compilation fails.

The point is not that components are literally instantiated at compile time. They are not. Runtime still creates components and manages lifecycle.

The static part is the *valid topology*.

Conceptually:

```text
Compile time

Controller
   ↓
Service
   ↓
Repository
   ↓
DataSource

✓ every node known
✓ every edge known
✓ graph validated
```

Runtime then creates the actual instances.

That is a much narrower meaning of static than the phrase "static application" suggests.

---

# What Kora Keeps Dynamic

At runtime, Kora still manages several forms of change.

The container creates and releases component instances.

Lifecycle-aware components initialize and shut down.

Configuration may change.

Affected parts of the graph can be rebuilt.

A component can hold an indirect reference to another component so that it observes its newest version without being recreated itself.

Runtime application logic can choose among multiple known implementations.

Collections of components can act as strategy registries.

External state can change arbitrarily.

Remote feature flag systems can drive decisions.

The graph therefore behaves more like a typed structural skeleton than an immutable object snapshot.

That distinction becomes especially clear once configuration refresh enters the picture.

---

# Compile-Time Topology, Runtime Refresh

Kora 2 has an explicit runtime graph refresh mechanism.

The core contract is conceptually simple:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface RefreshableGraph extends Graph {
        void refresh(Node<?> fromNode);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface RefreshableGraph : Graph {
        fun refresh(fromNode: Node<*>)
    }
    ```

A refresh begins from a node whose underlying value has changed.

Everything downstream through **direct dependency edges** is rebuilt because those components were constructed using the old value.

Components connected through an **indirect dependency** such as `ValueOf<T>` do not need to be rebuilt. They retain their own identity and read the current dependency when needed.

This creates a useful distinction between two graph relationships.

A direct dependency says:

```text
I was constructed from this instance.
If it changes, I should change too.
```

An indirect dependency says:

```text
I need access to whichever instance is current.
I do not need to be reconstructed when it changes.
```

That is a real runtime dynamic graph mechanism, but it preserves compile-time topology.

The set of nodes and possible edges was validated in advance.

The runtime operation changes *instances along known edges*.

It does not discover an arbitrary new application architecture.

---

# `ValueOf<T>` Is the Key Abstraction

Suppose we have:

```text
ServiceA
ServiceB
ServiceC
```

and `ServiceC` directly depends on both `ServiceA` and `ServiceB`.

Conceptually:

===! ":fontawesome-brands-java: `Java`"

    ```java
    ServiceC serviceC(ServiceA a, ServiceB b)
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun serviceC(a: ServiceA, b: ServiceB): ServiceC
    ```

If `ServiceB` is refreshed, `ServiceC` must normally be reconstructed because its constructor received the old `ServiceB`.

Now change the relationship:

===! ":fontawesome-brands-java: `Java`"

    ```java
    ServiceC serviceC(ServiceA a, ValueOf<ServiceB> b)
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun serviceC(a: ServiceA, b: ValueOf<ServiceB>): ServiceC
    ```

`ServiceC` no longer owns a fixed `ServiceB` reference.

It owns access to the current `ServiceB`.

At runtime:

```text
initial state

ServiceC
   │
   └──── ValueOf ────→ ServiceB₁
```

after refresh:

```text
ServiceC
   │
   └──── ValueOf ────→ ServiceB₂
```

`ServiceC` remains stable.

That gives Kora a controlled form of runtime dynamism without giving up graph validation.

The compiler still knows that `ServiceC` can depend on `ServiceB`.

The runtime can change which `ServiceB` instance is current.

---

# Why Long-Lived Servers Need This

The distinction is especially useful for components that should not be restarted merely because one logical dependency changed.

An HTTP server may own:

- a listening socket;
- acceptor state;
- transport resources;
- connection state.

Restarting the server because a request handler changed would be unnecessary and potentially disruptive.

Kora can instead make the server depend indirectly on its current handlers.

Conceptually:

```text
HTTP server instance
       │
       │ stays alive
       ↓
ValueOf<Handlers>
       │
       ├── before refresh → Handlers v1
       │
       └── after refresh  → Handlers v2
```

The infrastructure instance remains stable while the application behavior it dispatches to can change.

This is a more precise kind of dynamism than throwing away the entire container.

---

# Configuration Refresh Is a Concrete Example

Kora's configuration watcher demonstrates that this is not merely a theoretical API.

For file-based configuration, Kora can monitor the source file and trigger a graph refresh when it changes.

The process is approximately:

```text
application.conf changes
        ↓
ConfigWatcher detects change
        ↓
configuration source is reread
        ↓
RefreshableGraph.refresh(config node)
        ↓
affected configuration components recreated
        ↓
direct dependents recreated
        ↓
ValueOf dependents keep identity
        ↓
application continues
```

The default watcher checks periodically while the process is running.

For HOCON, included files can participate too.

A replaced symlink can also be observed, which is important for environments where mounted configuration or secrets are updated atomically by switching the target.

This is operationally meaningful runtime reconfiguration.

It is not static configuration baked into the artifact.

---

# Logging Levels Show the Model in Practice

Logging is an especially easy example to understand.

The framework knows at compile time that logging infrastructure exists.

It does not need to rediscover logging components when a level changes.

The actual level policy is runtime state.

When the configuration is refreshed, logging levels can be reapplied without restarting the application.

That gives:

```text
Compile time:
logging components and dependencies known

Runtime:
INFO → DEBUG → WARN
```

No dependency topology changed.

Yet application behavior changed materially.

This is exactly the distinction Kora is designed around.

---

# A Better Mental Model for Config Refresh

Developers sometimes imagine configuration refresh as requiring a mutable container whose whole meaning is recomputed after each change.

Kora's model can be visualized more narrowly.

Suppose:

```text
Config
  ↓
DatabaseConfig
  ↓
DatabaseClient
  ↓
OrderRepository
  ↓
OrderService
```

If `DatabaseConfig` changes and each dependency is direct, a refresh can rebuild the affected path.

Conceptually:

```text
before

Config₁
  ↓
DatabaseConfig₁
  ↓
DatabaseClient₁
  ↓
OrderRepository₁
  ↓
OrderService₁
```

after refresh:

```text
Config₂
  ↓
DatabaseConfig₂
  ↓
DatabaseClient₂
  ↓
OrderRepository₂
  ↓
OrderService₂
```

The topology is identical.

The instances are new.

This is analogous to replacing values in a validated dataflow graph.

---

# `ValueOf<T>` Lets You Control Refresh Boundaries

Rebuilding every downstream component is not always desirable.

Suppose the top-level request router should remain alive and simply observe the newest policy.

Use:

```text
Config
  ↓
RoutingConfig
  ↓
RoutingPolicy
  ↓
ValueOf<RoutingPolicy>
  ↓
RequestRouter
```

After refresh:

```text
RoutingPolicy₁
       ↓ refresh
RoutingPolicy₂

RequestRouter stays alive
and reads the current value.
```

This makes refresh boundaries explicit in types.

A direct dependency means lifecycle coupling.

`ValueOf<T>` means live reference without lifecycle coupling.

That is a sophisticated runtime model, but it remains understandable because the relationship appears in the constructor signature instead of hidden container metadata.

---

# Runtime Dynamism Should Have an Owner

This leads to a broader architectural point.

Every dynamic decision should have an owner.

If provider selection is business logic, `PaymentRouter` should own it.

If endpoint selection is client policy, a routing client or endpoint provider should own it.

If flag evaluation is product policy, a feature-flag client should own it.

If tenant-specific behavior is needed, a tenant registry should own it.

If configuration refresh changes component state, the graph refresh mechanism should own lifecycle propagation.

A DI container should not become the universal owner of every changing choice merely because it can.

That tends to blur architecture.

Kora's model encourages a more explicit answer:

```text
dependency topology → framework
runtime policy       → application/domain component
runtime configuration→ configuration subsystem
runtime state         → component
runtime refresh       → graph lifecycle
```

Each concern has a place.

---

# Feature Flags Do Not Require Dynamic DI

Feature flags are a classic example of runtime dynamism being mistaken for dynamic wiring.

Suppose a service has two implementations:

===! ":fontawesome-brands-java: `Java`"

    ```java
    interface RecommendationStrategy {
        Recommendations recommend(User user);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface RecommendationStrategy {
        fun recommend(user: User): Recommendations
    }
    ```

with:

```text
ClassicRecommendationStrategy
AiRecommendationStrategy
```

A feature flag decides which one to use.

A dynamic-container interpretation might attempt to register or unregister implementations as flags change.

That is unnecessary.

Use a router:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class RecommendationRouter implements RecommendationStrategy {

        private final ClassicRecommendationStrategy classic;
        private final AiRecommendationStrategy ai;
        private final FeatureFlags flags;

        public RecommendationRouter(
            ClassicRecommendationStrategy classic,
            AiRecommendationStrategy ai,
            FeatureFlags flags
        ) {
            this.classic = classic;
            this.ai = ai;
            this.flags = flags;
        }

        @Override
        public Recommendations recommend(User user) {
            if (flags.enabled("ai-recommendations", user.id())) {
                return ai.recommend(user);
            }

            return classic.recommend(user);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class RecommendationRouter(
        private val classic: ClassicRecommendationStrategy,
        private val ai: AiRecommendationStrategy,
        private val flags: FeatureFlags
    ) : RecommendationStrategy {

        override fun recommend(user: User): Recommendations {
            if (flags.enabled("ai-recommendations", user.id)) {
                return ai.recommend(user)
            }

            return classic.recommend(user)
        }
    }
    ```

The graph is:

```text
Classic strategy ─┐
                  ├── RecommendationRouter
AI strategy ──────┤
                  │
FeatureFlags ─────┘
```

Every request can choose differently.

Static topology has not reduced runtime flexibility at all.

---

# OpenFeature Fits Naturally Into This Model

Kora does not need a giant framework-specific feature-flag abstraction to support dynamic flags.

An OpenFeature client or another provider can be integrated like any ordinary Java library:

```text
configuration
      ↓
provider
      ↓
OpenFeature client
      ↓
FeatureFlags adapter
      ↓
application routing
```

The provider and client are known graph components.

Flag values are runtime data.

Evaluation is runtime behavior.

A remote flag change can affect the next request without changing the DI graph.

That is exactly the sort of dynamism that belongs outside container topology.

---

# Dynamic Configuration Does Not Mean Dynamic Classes

Remote configuration systems create the same distinction.

Consider an application reading:

```text
payment.defaultProvider = "stripe"
payment.retry.maxAttempts = 3
limits.checkout = 200
search.endpoint = "https://..."
```

All of those values can change.

But the Java types involved remain:

```text
PaymentRouter
RetryPolicy
RateLimiter
SearchClient
```

The configuration values are runtime variables.

The classes and dependency edges are architecture.

Treating a changed integer or endpoint as a reason to mutate the component-definition registry confuses two very different levels.

---

# Credentials Are Dynamic State

Credential rotation is another common argument for runtime flexibility.

Suppose a cloud SDK needs rotating credentials.

The wrong conclusion is:

```text
credentials change
→ recreate dependency graph definition
```

A cleaner model is:

```text
CredentialProvider
      ↓
current credentials
```

The provider remains a stable graph component.

Its returned credential material changes.

If the native SDK requires recreating the client when credentials change, then the affected client component can participate in refresh.

Again, the topology can remain the same:

```text
CredentialConfig
      ↓
CredentialProvider
      ↓
CloudClient
```

Only the instances or values change.

---

# Dynamic Endpoints Are Usually Routing State

Service discovery provides another example.

An HTTP client may need to call a changing set of upstream nodes.

That does not imply a changing set of Java dependency definitions.

A stable component can own dynamic endpoint state:

```text
ServiceDiscovery
       ↓
EndpointRegistry
       ↓
HttpClient
```

At 10:00:

```text
A, B, C
```

At 10:05:

```text
B, C, D
```

The endpoint registry changes.

The application architecture does not.

---

# Multi-Tenancy Rarely Requires One DI Graph Per Tenant

Multi-tenancy is often cited as a reason for dynamic dependency injection.

Sometimes tenant-specific object graphs really are useful, but many systems can model the requirement more directly.

Suppose different tenants have:

- database identifiers;
- credentials;
- rate limits;
- feature flags;
- payment policies.

A runtime registry can hold tenant state:

```text
TenantRegistry
      ↓
TenantContext
      ↓
request handling
```

or:

===! ":fontawesome-brands-java: `Java`"

    ```java
    TenantConfiguration configurationFor(TenantId id)
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun configurationFor(id: TenantId): TenantConfiguration
    ```

The application still contains the same controller, service and repository abstractions.

The tenant is data.

Generating one framework object graph per tenant may be unnecessary complexity.

---

# Lists of Implementations Are a Built-In Strategy Mechanism

Kora can inject collections of known implementations through `All<T>`.

This is useful when application logic needs a registry.

Suppose several handlers implement:

===! ":fontawesome-brands-java: `Java`"

    ```java
    interface EventHandler {
        String type();
        void handle(Event event);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface EventHandler {
        fun type(): String
        fun handle(event: Event)
    }
    ```

The graph can contain:

```text
UserCreatedHandler
OrderPaidHandler
InvoiceFailedHandler
```

and a registry can receive all of them:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class EventHandlerRegistry {

        private final Map<String, EventHandler> handlers;

        public EventHandlerRegistry(All<EventHandler> handlers) {
            this.handlers = handlers.stream()
                .collect(Collectors.toMap(EventHandler::type, Function.identity()));
        }

        public EventHandler handler(String type) {
            return handlers.get(type);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class EventHandlerRegistry(handlers: All<EventHandler>) {

        private val handlers: Map<String, EventHandler> =
            handlers.associateBy { it.type() }

        fun handler(type: String): EventHandler? {
            return handlers[type]
        }
    }
    ```

Runtime selection is now dynamic by event type.

The graph remains validated.

This pattern covers:

- serializers;
- payment providers;
- command handlers;
- event handlers;
- policy engines;
- exporters;
- protocol adapters;
- tenant strategies;
- validators.

A dynamic registry does not require dynamic DI registration.

---

# Tags Make Multiple Known Implementations Explicit

Sometimes multiple components have the same Java type but different roles.

For example:

```text
primary database
replica database
```

or:

```text
internal HTTP client
external HTTP client
```

or:

```text
main object store
archive object store
```

Kora tags make those roles explicit at compile time.

The runtime may still decide which one to use for a particular operation.

The important property is that ambiguity is resolved structurally instead of being left to classpath order, naming conventions or conditional runtime registration.

---

# Factories Are Static Definitions With Dynamic Inputs

A factory method is sometimes misunderstood as a compile-time constant.

It is not.

The *factory definition* is known at compile time.

Its arguments are runtime component instances.

The factory can construct a component from runtime configuration.

Conceptually:

===! ":fontawesome-brands-java: `Java`"

    ```java
    default SearchClient searchClient(SearchConfig config) {
        return new SearchClient(config.endpoint(), config.timeout());
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun searchClient(config: SearchConfig): SearchClient {
        return SearchClient(config.endpoint(), config.timeout())
    }
    ```

Compile time knows:

```text
SearchClient depends on SearchConfig
```

Runtime supplies:

```text
endpoint = current configured endpoint
timeout  = current configured timeout
```

If `SearchConfig` changes and the graph is refreshed, `SearchClient` can be recreated.

Static dependency topology and runtime factories coexist naturally.

---

# `@FactoryModule` Extends This to Parameterized Component Families

Kora's factory modules allow reusable module behavior to be parameterized.

For example, the same client-module structure can be instantiated twice:

```text
MainDb module
ArchiveDb module
```

with different config paths and tags.

That means the compile-time graph can contain structured families of components while still deriving their configuration at runtime.

Again:

```text
known shape
+
runtime values
```

not:

```text
unknown shape
```

---

# Conditionality Can Also Be Compile-Time

Kora supports conditional components as part of graph construction.

That is useful for build-time or environment-independent architectural conditions where the set of valid graph components can be decided before runtime.

But runtime policy should not automatically be forced into those conditions.

There is value in asking:

> Is this truly a different application architecture, or merely a runtime choice?

If a feature flag can change every minute, it belongs in application behavior.

If one deployment flavor permanently includes a component and another does not, conditional graph composition may be appropriate.

The distinction keeps dynamic behavior from leaking unnecessarily into dependency definition.

---

# Why Runtime Classpath Scanning Is Usually Not a Business Requirement

Runtime scanning is often treated as an inherent property of sophisticated frameworks.

But ask what business problem scanning solves.

For a conventional service, the product requirement is rarely:

> At process startup, search the classpath for previously unknown classes and infer which ones should become application components.

The product requirement is more likely:

> Serve orders.

> Process Kafka records.

> Call a payment provider.

> Run scheduled jobs.

> Query a database.

> Expose gRPC endpoints.

Classpath scanning is one implementation technique for assembling those capabilities.

It is not the capability itself.

Kora chooses a different implementation technique: compile-time discovery and generated wiring.

If the set of source components is already known while building the artifact, runtime rediscovery adds flexibility that many services never use.

---

# Static Graph Gives You Earlier Failure

One of the strongest benefits of compile-time topology is that invalid architecture fails before deployment.

Suppose two `PaymentProvider` components satisfy one untagged dependency.

A runtime container may detect the ambiguity during startup.

Kora can detect it during compilation.

Suppose a repository dependency is missing.

Compile-time graph construction fails.

Suppose a dependency cycle cannot be resolved safely.

Compilation fails.

Suppose an external module was forgotten.

Compilation fails.

This moves structural correctness into the build.

The benefit is not only faster startup.

It changes when uncertainty is removed.

---

# Production-Only Wiring Surprises Become Harder

Runtime dependency systems can support conditionals based on:

- environment properties;
- classpath presence;
- profiles;
- bean names;
- conditional annotations;
- external modules;
- ordering;
- auto-configuration.

That flexibility is useful, but it also creates the possibility that the graph assembled in production differs from the graph a developer mentally reconstructed locally.

Kora reduces this class of surprise because component definitions and dependencies are explicit and validated.

Runtime values can differ.

The topology is not silently rediscovered from a new classpath.

This makes the deployed artifact easier to reason about.

---

# Startup Becomes More Predictable

Classpath scanning and runtime graph assembly are not merely performance costs. They are sources of variability.

Startup work may depend on:

- classpath size;
- reflection metadata;
- proxy generation;
- conditional evaluation;
- environment state;
- component discovery;
- dynamic registry processing.

Kora performs most structural resolution before the process starts.

Runtime startup still has real work:

- instantiate components;
- open connections;
- initialize servers;
- run lifecycle hooks;
- contact external systems where required.

But the framework is not simultaneously asking what the application architecture is.

That improves startup predictability.

---

# Ownership Becomes Easier to See

A static graph represented in source answers architectural questions more directly.

Where is this component created?

Look at the constructor or factory.

Why does this service exist?

Follow the dependency path.

Which modules are connected?

Look at `@KoraApp` and submodules.

Which implementation satisfies this interface?

Follow compile-time resolution, tags and factories.

Which components will refresh if this config changes?

Look at direct versus `ValueOf<T>` dependencies.

This is useful for code review and incident investigation because architecture is less dependent on runtime container state.

---

# Testing Becomes More Structural

A validated graph also improves testing.

Component tests can request a known graph slice.

Dependencies can be replaced explicitly.

The test can reason about which components are needed because relationships are static and typed.

Runtime behavior remains testable through normal inputs:

- different configuration;
- different flags;
- different request context;
- different tenant data;
- different registry state.

This separates two test dimensions cleanly:

```text
Structural correctness
      ↓
compiler + graph validation

Behavioral correctness
      ↓
tests
```

The test suite does not need to rediscover every wiring mistake.

---

# AI Agents Benefit From the Same Boundary

An AI coding agent has an easier time with a system when architecture can be reconstructed from source rather than runtime metadata.

With Kora, an agent can inspect:

- constructors;
- factory methods;
- modules;
- tags;
- generated graph code;
- `ValueOf<T>` relationships.

It can then distinguish:

```text
structural dependency
```

from:

```text
runtime decision
```

That distinction is extremely useful during automated edits.

An agent changing payment routing logic does not need to mutate the DI topology.

An agent adding a dependency receives a compiler error if the graph is invalid.

An agent investigating configuration refresh can trace the refresh edge explicitly.

Less mutable framework state means less invisible context to infer.

---

# Mutable Framework State Is a Cost

A highly dynamic container needs internal mutable state describing:

- registered definitions;
- aliases;
- active conditions;
- scopes;
- current proxies;
- child contexts;
- refreshed contexts;
- post-processors;
- lifecycle callbacks;
- discovered extensions.

That state can be useful.

But it is also another subsystem that developers must understand.

Kora deliberately keeps runtime container state narrower.

The framework still tracks component instances and supports refresh.

What it avoids is treating application architecture as an open-ended runtime registry by default.

This reduces the number of moving parts involved in ordinary application execution.

---

# Dynamic Selection Belongs in Application Code When It Is Business Logic

Consider a shipping system with several carriers.

```text
DHL
UPS
FedEx
LocalCourier
```

Carrier choice depends on:

- destination;
- parcel size;
- SLA;
- current outage;
- price;
- merchant configuration.

That choice is domain logic.

Representing it as dynamic bean registration would hide a business rule inside infrastructure.

A normal strategy router is clearer:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class ShippingRouter {

        private final Map<Carrier, ShippingProvider> providers;
        private final ShippingPolicy policy;

        public ShippingProvider choose(Shipment shipment) {
            var carrier = policy.carrierFor(shipment);
            return providers.get(carrier);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class ShippingRouter(
        private val providers: Map<Carrier, ShippingProvider>,
        private val policy: ShippingPolicy
    ) {

        fun choose(shipment: Shipment): ShippingProvider? {
            val carrier = policy.carrierFor(shipment)
            return providers[carrier]
        }
    }
    ```

The DI framework provides the possible strategies.

The application owns the decision.

That is the boundary Kora encourages.

---

# Runtime Routing Is More Expressive Than Container Conditions

Container conditions are usually coarse.

They answer questions such as:

```text
Should this component definition exist?
```

Business routing can answer richer questions:

```text
Which implementation for this request?
Which implementation for this tenant?
Which implementation at this moment?
Which implementation after checking health?
Which implementation for 5% of users?
```

Once selection becomes request-dependent, container mutation is usually the wrong abstraction anyway.

A stable router with dynamic policy is simpler and more expressive.

---

# Dynamic Retry Policies Do Not Require Dynamic AOP Definitions

Retry is another instructive case.

A retry policy may change at runtime:

```text
max attempts
delay
jitter
retryable errors
budget
```

That does not mean the framework needs to generate a new interceptor graph each time.

A retry component or aspect can consult current configuration.

The structural relationship:

```text
Service
   ↓
retry policy
   ↓
HTTP client
```

can remain stable.

The policy parameters are runtime state.

This is a recurring pattern:

```text
stable mechanism
+
dynamic policy
```

---

# Rate Limits Are Data

Rate limiting is even clearer.

A service may have different limits per:

- tenant;
- endpoint;
- account;
- region;
- subscription;
- time of day.

The limiter implementation remains one component.

The current limit table is data.

Making one DI definition per limit would be absurd.

The dynamic nature of production applications already depends heavily on explicit runtime data structures.

DI topology is only one part of the system.

---

# Business Rules Have Always Been Dynamic

It is worth stepping back.

Java applications were dynamic long before dependency injection frameworks existed.

They used:

- polymorphism;
- strategy objects;
- maps;
- registries;
- state machines;
- configuration;
- databases;
- rules engines;
- queues;
- function objects;
- routing tables.

Runtime DI did not invent application dynamism.

It introduced a convenient runtime composition mechanism.

That mechanism is valuable in the use cases that actually need it.

But it should not be confused with runtime programming itself.

---

# The Graph Can Refresh Without Becoming Unknown

This is perhaps Kora's most interesting middle ground.

At first glance, frameworks are often described as either:

```text
static compile-time container
```

or:

```text
dynamic runtime container
```

Kora does not fit that binary cleanly.

Its *graph description* is compile-time validated.

Its *graph instances* can change at runtime.

A more accurate representation is:

```text
Compile time:
validated graph topology

Runtime:
instance set v1
      ↓ refresh
instance set v2
      ↓ refresh
instance set v3
```

The topology constrains valid transitions.

That is different from arbitrary runtime registration.

---

# Refresh Propagation Is More Predictable Because Edges Are Known

If a component changes, Kora can rebuild its direct dependents because dependency edges are known.

Conceptually:

```text
A
↓
B
↓
C

refresh A
→ rebuild B
→ rebuild C
```

Now add an indirect dependency:

```text
A
↓
B

ValueOf<B>
    ↓
    C
```

refreshing `B` does not require rebuilding `C`.

This turns refresh behavior into a graph property that can be reasoned about from types.

A dynamic runtime registry may support more arbitrary mutation, but it also has to recompute more of the meaning at runtime.

---

# Lifecycle Matters During Refresh

Refreshing instances is not just assignment.

Components may own resources.

Replacing a database client, HTTP client or consumer requires lifecycle semantics:

```text
construct replacement
initialize replacement
switch dependency state
release old instance
```

Kora's graph runtime already owns component lifecycle, so refresh can remain lifecycle-aware.

This is important because "dynamic reconfiguration" is often presented as if changing an object reference were enough.

Production components need safe transitions.

Static topology helps because the container already understands dependency order.

---

# Stable Components Can Observe New Dependencies

The `ValueOf<T>` mechanism is powerful because it avoids cascading refresh farther than necessary.

Consider:

```text
Config
  ↓
TlsConfig
  ↓
ExternalClient
  ↓
ValueOf<ExternalClient>
  ↓
RequestProcessor
```

The external client can be recreated after certificate rotation.

The request processor can remain alive.

On its next operation it accesses the current client.

That is operational dynamism with a controlled blast radius.

---

# Refresh Is Not a Replacement for Every Dynamic Pattern

Graph refresh is useful, but it should not become the answer to every changing value.

If a feature flag changes thousands of times per second, do not refresh the application graph thousands of times per second.

If a routing table changes frequently, keep it in a runtime registry.

If market data changes continuously, it is data.

If a tenant configuration lookup is request-scoped, query the tenant configuration service.

Graph refresh is appropriate when component instances should genuinely be reconstructed because their configuration changed.

This distinction keeps refresh from becoming a hidden runtime programming model.

---

# Three Levels of Change

A useful decision framework is:

## Level 1: Data changes

Examples:

- orders;
- users;
- prices;
- flags;
- routing entries;
- quotas.

Use normal runtime state.

```text
same components
different data
```

## Level 2: Component configuration changes

Examples:

- endpoint;
- credentials;
- pool size;
- TLS material;
- static policy config.

Use dynamic configuration, refreshable components, `ValueOf<T>`, or stateful providers.

```text
same topology
new component state or instance
```

## Level 3: Component types/topology change

Examples:

- load a previously unknown plugin JAR;
- discover a new implementation class;
- register a new framework definition;
- mutate the set of component types.

This is true dynamic-container territory.

```text
new topology
```

Most backend systems live overwhelmingly in Levels 1 and 2.

---

# The True Dynamic Plugin Use Case Is Real

There are applications where Kora's static graph is genuinely less natural.

Consider an IDE.

The product may load third-party plugins after installation.

Those plugins can contribute:

- actions;
- editors;
- language services;
- menus;
- project types;
- inspections;
- tool windows.

The host cannot know every plugin class when it is compiled.

The extension graph is part of the product.

That is real runtime topology.

---

# Application Servers Are Another Example

A general-purpose application server may deploy arbitrary applications after the server itself is installed.

The server's role is explicitly to host unknown code.

Runtime discovery and classloader isolation are core requirements.

A static compile-time graph for the host cannot describe applications that do not exist yet.

That is a fundamentally different problem from a deployable REST service.

---

# Plugin Marketplaces Need Unknown Extensions

Desktop platforms with plugin marketplaces also need dynamic extension discovery.

The workflow may be:

```text
download plugin
      ↓
load JAR
      ↓
inspect manifest/classes
      ↓
register extension points
      ↓
instantiate plugin services
```

Here the dependency graph itself is genuinely runtime data.

A runtime plugin architecture, OSGi-style system, custom classloader platform or dynamic DI container may be appropriate.

---

# Some Workflow Engines May Need Dynamic Code

A workflow engine that can load arbitrary user-provided code modules at runtime can have similar requirements.

If a customer uploads a new handler implementation that did not exist when the service artifact was built, the set of executable component types changes.

That is true dynamic extensibility.

The distinction remains:

```text
dynamic workflow data
```

does not require runtime topology,

but:

```text
dynamically loaded workflow code
```

may.

---

# Containers Whose Product Is Extensibility Are Different

The central rule can be phrased this way:

> **Runtime DI flexibility is valuable when the dependency graph itself is part of the product. For most backend services, it is not.**

An IDE sells extensibility.

A plugin host sells extensibility.

An application server exists to load unknown applications.

A traditional service exists to implement a known application architecture against dynamic data.

These are different categories of software.

---

# REST Services Rarely Need Unknown Components

Take a normal REST service.

The routes may be data-driven.

Authentication policy may change.

Feature flags may change.

Tenants may change.

The database contents obviously change.

But the deployment artifact usually contains the complete set of controllers, services, repositories and integrations it can execute.

When the architecture changes, the team builds and deploys a new artifact.

That is already the operational model of most containerized backend systems.

Compile-time topology fits that lifecycle naturally.

---

# Kafka Consumers Are Structurally Stable Too

A Kafka service may subscribe to dynamic partition assignments and process unbounded event data.

That is extremely dynamic operationally.

But its structure is typically:

```text
Kafka consumer
      ↓
record handler
      ↓
domain service
      ↓
repository
```

Partition assignment changes are runtime state.

Consumer records are runtime data.

Offsets move continuously.

No dependency graph mutation is required.

---

# API Gateways Are Dynamic Without Dynamic DI

An API gateway can route based on configuration loaded from a control plane.

The route table may change every second.

Yet the architecture can remain:

```text
HTTP server
      ↓
RouteRegistry
      ↓
ProxyHandler
      ↓
HTTP client
```

`RouteRegistry` is the dynamic component.

Registering one DI bean per route would be an unnecessary representation of data as architecture.

---

# Workers and Schedulers Follow the Same Pattern

A worker may receive dynamically defined jobs.

A scheduler may execute database-backed tasks whose schedule changes continuously.

Again, the component model is stable:

```text
scheduler
   ↓
task registry
   ↓
executor
```

The scheduled entries are data.

A mutable runtime graph is not inherently useful.

---

# Compile-Time Structure Improves Architecture Analysis

A static graph has another advantage: it can be analyzed before runtime.

Because dependencies are known, tools can reason about:

- reachable components;
- unused components;
- dependency chains;
- cycles;
- lifecycle order;
- module boundaries;
- architecture diagrams;
- component ownership.

Generated graph code can also be inspected.

This gives dependency injection a role closer to architectural validation than runtime service location.

---

# Dynamic Containers Trade Early Knowledge for Runtime Freedom

This is not inherently bad.

A dynamic container offers a broader set of runtime possibilities:

```text
discover
register
replace
condition
decorate
reconfigure definitions
```

But those possibilities have a cost.

Some relationships become knowable only after startup.

Some errors move from compile time to runtime.

The framework may need reflection, metadata scanning, condition evaluation or mutable registries.

Developers may need to understand not only source code but also the container's assembled state.

The trade is justified when the application uses that freedom.

If it does not, the flexibility may be mostly latent complexity.

---

# Flexibility Has an Option Cost

Engineers often evaluate flexibility as if more were automatically better.

But unused flexibility still has costs:

- larger conceptual model;
- more runtime states;
- more failure modes;
- later error detection;
- more diagnostics needed;
- more hidden configuration interactions;
- more mutable framework state.

A compile-time graph rejects some possibilities deliberately.

In return, it turns assumptions into guarantees.

That can be a very good trade for production services whose structure changes through deployments rather than runtime plugin loading.

---

# "But What About Profiles?"

Profiles are often used to assemble different dependency graphs for development, testing or deployment environments.

That is convenient, but many differences do not actually require dynamic topology.

For example:

```text
production database URL
staging database URL
local database URL
```

is configuration.

Different credentials are configuration.

Different timeouts are configuration.

Different external endpoints are configuration.

If a test genuinely needs a different component implementation, Kora's testing facilities can replace components explicitly.

This keeps deployment configuration from becoming an implicit architecture language.

---

# Deployment Is Already a Topology-Change Mechanism

There is a larger operational observation here.

In modern backend systems, changing application structure usually means:

```text
modify code
↓
compile
↓
test
↓
build artifact
↓
deploy new version
```

Kubernetes, rolling deploys and immutable images reinforce this model.

If the service needs a new repository, handler or integration, teams generally deploy a new artifact.

They do not inject a new class definition into the running process.

Compile-time graph construction aligns with that reality.

---

# Runtime Configuration Should Not Replace Deployment Either

The opposite mistake also exists.

Because Kora can refresh graph components, teams should not treat every architectural change as runtime configuration.

If enabling a feature introduces entirely new resource ownership, migrations, security boundaries or operational semantics, a deployment may still be the safer change mechanism.

Dynamic capability should be used where dynamic change genuinely reduces operational cost.

The same discipline that rejects unnecessary runtime DI should reject unnecessary live refresh.

---

# Static Graphs Improve Reproducibility

A compiled graph contributes to reproducibility because two processes running the same artifact have the same structural component model.

Runtime data may differ.

Configuration may differ.

But the possible dependency topology is constrained by the artifact.

That helps answer questions such as:

> Could this production instance have loaded a component type that staging never saw?

In Kora's normal model, not without that type having been part of the compiled application structure.

This reduces one dimension of environmental drift.

---

# Configuration Can Still Cause Different Instances

Structural reproducibility does not imply identical instances.

Two deployments can use:

```text
different endpoints
different credentials
different database pools
different telemetry settings
different routing policies
```

The same graph can therefore behave very differently according to its runtime configuration.

That is desirable.

Architecture and environment remain separate concerns.

---

# Static Topology Makes Security Easier to Reason About

Runtime extension loading has security consequences.

If arbitrary code can register new application components, the trust boundary of the process expands.

A static graph means the executable component types are determined by the built artifact.

This does not make the application automatically secure, but it reduces the need for plugin trust, classloader isolation and runtime extension authorization.

For ordinary backend services, that is usually a simplification.

---

# Observability Benefits From Explicit Components Too

When component roles are known, observability can map more clearly to architecture.

A database client is a known graph component.

An HTTP server is a known graph component.

A consumer is a known graph component.

A refresh event can be associated with known nodes.

The system is easier to describe than one where an unknown set of runtime definitions may appear.

Again, runtime data remains dynamic.

The framework architecture remains legible.

---

# What Happens During a Configuration Refresh?

It is worth examining the mechanics conceptually.

Suppose:

```text
ConfigOrigin
    ↓
Config
    ↓
SearchConfig
    ↓
SearchClient
    ↓
SearchService
```

The file watcher observes a configuration-source change.

It initiates refresh from the relevant node.

The refreshed configuration is read.

Kora determines downstream direct dependents.

Those components are rebuilt according to their factories.

Lifecycle applies where relevant.

If `SearchService` depends directly on `SearchClient`, it can be rebuilt.

If instead it receives `ValueOf<SearchClient>`, it can remain stable.

The topology is not re-discovered.

The existing topology determines refresh propagation.

That is why compile-time structure and runtime refresh are complementary rather than contradictory.

---

# A Runtime Refresh Example

Imagine this simplified module:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface SearchModule {

        default SearchConfig searchConfig(Config config) {
            return readSearchConfig(config);
        }

        default SearchClient searchClient(SearchConfig config) {
            return new SearchClient(config.endpoint());
        }

        default SearchService searchService(ValueOf<SearchClient> client) {
            return new SearchService(client);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface SearchModule {

        fun searchConfig(config: Config): SearchConfig {
            return readSearchConfig(config)
        }

        fun searchClient(config: SearchConfig): SearchClient {
            return SearchClient(config.endpoint())
        }

        fun searchService(client: ValueOf<SearchClient>): SearchService {
            return SearchService(client)
        }
    }
    ```

At startup:

```text
SearchConfig(endpoint=A)
      ↓
SearchClient(A)
      ↓
ValueOf
      ↓
SearchService
```

After a config change:

```text
SearchConfig(endpoint=B)
      ↓
SearchClient(B)
      ↓
ValueOf
      ↓
same SearchService
```

`SearchService` can call:

===! ":fontawesome-brands-java: `Java`"

    ```java
    client.get()
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    client.get()
    ```

and receive the current client.

This is a concrete example of:

> **Compile-time topology does not imply immutable runtime instances.**

---

# Do Not Inject Raw Config Everywhere

Kora's configuration guidance reinforces this model.

If every component depends directly on the root `Config`, then a configuration refresh can invalidate a large portion of the graph.

A better approach is typed configuration:

```text
Config
 ├── DatabaseConfig
 ├── HttpClientConfig
 ├── FeatureConfig
 └── CacheConfig
```

Then each subsystem depends only on its relevant configuration.

This gives refresh more precise boundaries.

It also makes configuration ownership explicit.

Runtime dynamism becomes easier to control because it is typed and localized.

---

# `ValueOf<Config>` Exists for Truly Dynamic Reads

Sometimes a component genuinely needs generic or dynamic config access.

In that case an indirect reference can avoid rebuilding the component every time configuration changes.

This is another example of the model being deliberately flexible:

```text
compile-time known dependency:
ValueOf<Config>

runtime behavior:
read current config dynamically
```

Again, the framework does not prohibit runtime configuration logic.

It makes the relationship explicit.

---

# `PromiseOf<T>` Covers Deferred Access

Kora also has `PromiseOf<T>` for lower-level cases where a component needs deferred access to another graph part.

Unlike an ordinary direct dependency, the value may not yet be available at the earliest point.

This is useful for infrastructure scenarios and cycle breaking.

The existence of `ValueOf<T>` and `PromiseOf<T>` illustrates that compile-time graph validation does not mean every runtime reference must be eagerly fixed.

The graph can represent different dependency semantics.

---

# Direct Edges Carry Lifecycle Meaning

The most interesting way to think about this is that graph edges are not only about lookup.

They encode lifecycle coupling.

```text
A → B
```

means more than:

```text
A can find B
```

It can mean:

```text
A was created using B
therefore B changing may require A to change
```

`ValueOf<B>` weakens that lifecycle coupling.

This makes dependency declarations semantically richer than a service locator.

---

# Dynamic Registries Are Often Better Than Dynamic DI

Suppose a system supports 100 tenant-defined notification templates.

A dynamic DI interpretation might create components for each template.

A simpler model is:

```text
NotificationTemplateRegistry
         ↓
Map<TenantId, Template>
```

The registry can update from a database or remote control plane.

The graph remains small.

Data stays data.

This principle applies widely:

```text
routes       → RouteRegistry
tenants      → TenantRegistry
policies     → PolicyRegistry
endpoints    → EndpointRegistry
models       → ModelRegistry
handlers     → known handler list + runtime map
```

The DI container does not need to model every piece of runtime state as a component definition.

---

# Why This Is Easier to Test

Runtime registries and strategy routers are normal objects.

They can be tested with normal unit tests.

For example:

```text
given feature flag OFF
expect classic provider

given feature flag ON
expect AI provider
```

or:

```text
given tenant A
choose endpoint X

given tenant B
choose endpoint Y
```

If these choices are implemented as runtime container mutation, tests must exercise framework state transitions instead of plain application logic.

Moving dynamism into explicit components therefore improves testability.

---

# Why This Is Easier to Debug

Suppose a request unexpectedly went to Adyen instead of Stripe.

With explicit routing logic, inspect:

```text
PaymentRouter
routing config
feature flags
request context
```

With runtime DI mutation, the question may become:

```text
Which provider component was registered?
Which condition activated?
When did the container refresh?
Which definition won?
Which profile was active?
```

The first model keeps business decisions closer to business code.

That is usually easier to diagnose.

---

# Why This Is Easier for Code Review

A code reviewer seeing:

===! ":fontawesome-brands-java: `Java`"

    ```java
    switch (config.provider()) {
        case STRIPE -> stripeProvider;
        case ADYEN -> adyenProvider;
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    when (config.provider()) {
        Provider.STRIPE -> stripeProvider
        Provider.ADYEN -> adyenProvider
    }
    ```

can understand the runtime choice immediately.

A reviewer seeing a set of conditional component-definition annotations may need framework-specific knowledge to infer the same behavior.

Kora's philosophy favors explicit application logic when runtime selection is genuinely application logic.

---

# Compile-Time Graphs Are Not "Less Enterprise"

Dynamic containers became associated with enterprise capability partly because large application servers historically needed runtime extensibility.

Modern containerized services have different constraints.

They are usually:

- independently built;
- independently deployed;
- immutable as artifacts;
- scaled horizontally;
- restarted rather than patched in place;
- owned by one team;
- designed around explicit APIs.

For such systems, compile-time assembly can be a better fit than a generic runtime component platform.

---

# Microservices Strengthen the Case

A monolithic application server hosting unknown applications benefits from runtime discovery.

A microservice usually has the opposite property: each deployable unit is intentionally narrow.

The artifact already exists precisely to define one service.

That makes compile-time graph generation particularly natural.

The service boundary itself has reduced the need for an open-ended runtime container.

---

# But Microservices Still Need Runtime Reconfiguration

None of this means "rebuild for every value change."

A production service may need live changes because restart cost is nonzero.

Examples:

- logging levels;
- traffic routing;
- feature flags;
- credentials;
- endpoints;
- timeout policies;
- pool parameters;
- tenant configuration.

Kora can support those requirements either through normal mutable state or through configuration-driven graph refresh.

This is why the simplistic opposition:

```text
compile-time = immutable
runtime DI   = dynamic
```

is inaccurate.

---

# The Better Comparison Is Structural vs Behavioral Dynamism

A more useful matrix is:

| Requirement | Needs Dynamic Graph? |
| --- | --- |
| Feature flag evaluation | Usually no |
| Remote config | Usually no |
| Endpoint failover | Usually no |
| Credential rotation | Usually no |
| Tenant routing | Usually no |
| Rate-limit changes | Usually no |
| Retry-policy changes | Usually no |
| Business rule changes from data | Usually no |
| Refreshing configured client instances | No, if graph refresh is supported |
| Choosing among known strategies | No |
| Loading unknown classes from a new JAR | Yes, potentially |
| Runtime plugin marketplace | Yes, potentially |
| Hosting arbitrary applications | Yes, potentially |

The right-hand column is much narrower than the word *dynamic* initially suggests.

---

# The Specialized Boundary Should Be Stated Honestly

Kora's model is not universally better.

If an application's requirements say:

> Download a JAR that did not exist when this artifact was compiled.

then:

```text
compile-time graph
```

cannot magically know its classes.

If the application then needs to:

```text
discover arbitrary implementations
      ↓
register component definitions
      ↓
resolve new dependencies
      ↓
create scopes/proxies
      ↓
mutate topology
```

a dynamic plugin system is appropriate.

A runtime DI container may help.

OSGi may help.

A dedicated plugin architecture may be better still.

The important point is that this is a specialized architectural requirement, not a default property of server applications.

---

# The Boundary Can Be Drawn Precisely

Kora handles this class of system well:

```text
Known component types
        +
dynamic configuration
        +
runtime graph refresh
        +
runtime strategy selection
        +
feature flags
        +
dynamic data
        +
dynamic external state
```

A different architecture may be preferable for:

```text
Download unknown JAR at runtime
        ↓
discover unknown classes
        ↓
register new component definitions
        ↓
change dependency topology
```

These are genuinely different problem domains.

---

# Static Graph Is a Constraint, and Constraints Can Be Valuable

Kora deliberately removes one degree of runtime freedom.

The application cannot casually discover arbitrary undeclared components and add them to the main graph after deployment.

That is a constraint.

But constraints are not automatically deficiencies.

Java's static type system is also a constraint.

Database schemas are constraints.

API schemas are constraints.

Module boundaries are constraints.

They trade some flexibility for earlier guarantees.

The right question is whether the rejected flexibility was needed.

For most services, arbitrary runtime topology mutation is not.

---

# Compile-Time Validation Turns Architecture Into a Contract

Once the graph is built ahead of time, it becomes part of the compiled application's contract.

The compiler can assert:

```text
every required dependency exists
every selected implementation is unambiguous
cycles follow valid rules
tags match
factories are valid
```

This is stronger than hoping the production environment assembles the same graph the developer expected.

The architecture has been checked.

Runtime can then focus on state.

---

# This Reduces the Number of Runtime Failure Classes

Kora cannot remove runtime failures.

Databases go down.

Configuration can be invalid.

Credentials expire.

Networks partition.

Code throws exceptions.

But some failures no longer need to exist at runtime:

```text
missing dependency
ambiguous dependency
invalid structural cycle
undeclared component
```

They become build errors.

That is a concrete reliability benefit of static topology.

---

# Dynamic Behavior Still Fails Dynamically, as It Should

If Stripe is unavailable, that is a runtime failure.

If a feature flag service times out, that is a runtime failure.

If a tenant does not exist, that is a runtime condition.

If remote config contains a bad endpoint, that may be a runtime configuration failure.

Compile-time DI should not pretend it can eliminate uncertainty that genuinely exists only at runtime.

Kora's model is strongest precisely because it does not need to.

It validates what can be known.

It leaves the rest dynamic.

---

# The Architecture Becomes More Explainable

This produces a useful property: the application can be explained in layers.

```text
Architecture:
compile-time graph

Current deployment:
runtime configuration

Current component state:
graph instances

Current request behavior:
business logic + state + data
```

Each question has a different source of truth.

That is easier to reason about than treating all four as one container state.

---

# Runtime Graph Refresh Is Controlled Mutation

It would also be wrong to describe Kora as having no mutable framework state whatsoever.

The runtime graph stores component instances.

Refresh can replace them.

Lifecycle runs.

Indirect references expose current values.

The distinction is that mutation happens inside a topology whose structure is already known.

This is controlled mutation rather than open-ended structural discovery.

That is a more precise claim.

---

# Why This Model Fits Kubernetes Well

Kubernetes already treats application artifacts as disposable units.

Structural changes commonly arrive through new images.

Runtime operational state arrives through:

- ConfigMaps;
- Secrets;
- service discovery;
- environment variables;
- remote control planes;
- APIs.

Kora's split maps naturally onto that world:

```text
image
→ known architecture

runtime config/control plane
→ current state and behavior
```

File watching and symlink-aware configuration refresh can also align with mounted configuration updates.

The framework does not need runtime classpath discovery to participate in cloud-native reconfiguration.

---

# A ConfigMap Change Is Not a New Application Architecture

This sounds obvious when phrased directly.

If a Kubernetes ConfigMap changes:

```text
timeout = 2s
```

to:

```text
timeout = 5s
```

the application did not gain a new architectural component.

A timeout policy changed.

Likewise, rotating a Secret did not create a new repository type.

Changing a log level did not require a new logger implementation.

Once this distinction is stated clearly, static graph design looks much less restrictive.

---

# Runtime Reconfiguration Should Have Defined Blast Radius

One advantage of graph refresh with direct and indirect dependencies is that a team can reason about the blast radius of changes.

If a configuration node changes:

```text
which components are rebuilt?
which components stay alive?
which resources restart?
```

Those are meaningful production questions.

`ValueOf<T>` provides a tool for intentionally stopping refresh propagation where a stable component should observe the new value instead.

This is more controlled than globally refreshing an opaque context.

---

# Refresh Design Becomes Part of Architecture

For a refreshable application, dependency shape therefore communicates more than construction.

It communicates runtime update behavior.

Compare:

===! ":fontawesome-brands-java: `Java`"

    ```java
    SearchService(SearchClient client)
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    SearchService(client: SearchClient)
    ```

with:

===! ":fontawesome-brands-java: `Java`"

    ```java
    SearchService(ValueOf<SearchClient> client)
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    SearchService(client: ValueOf<SearchClient>)
    ```

The first says:

> SearchService's lifecycle follows SearchClient.

The second says:

> SearchService survives SearchClient replacement and uses whichever client is current.

That is explicit architecture.

---

# This Model Encourages Deliberate Live Reconfiguration

Live reconfiguration can be dangerous when every dependency automatically becomes hot-reloadable.

Some objects are safe to replace.

Some are not.

Some long-running operations must drain.

Some clients need graceful shutdown.

Some servers should remain stable.

Some stateful components should not be recreated automatically.

By making refresh relationships visible, Kora encourages teams to think about those transitions deliberately.

---

# Runtime Selection Can Be Per-Request

Another reason dynamic DI is often unnecessary is granularity.

Container-level selection is usually application-wide or context-wide.

Business routing is often per-request.

Suppose half of traffic should go to provider A and half to B.

A runtime container cannot simply switch the global implementation without affecting concurrent requests.

A router can choose per call:

```text
request 1 → A
request 2 → B
request 3 → A
request 4 → B
```

Static graph + runtime selection is actually *more* dynamic at the behavior level.

---

# Known Implementations Are Often a Feature

Knowing all possible strategies at compile time is not a limitation when those strategies are code maintained by the service team.

It lets the compiler verify them.

It lets tests enumerate them.

It lets observability name them.

It lets code review see them.

The runtime then chooses from a validated set.

That is often exactly what teams want.

---

# Unknown Data and Unknown Code Are Different Risks

Backend systems routinely accept unknown data.

That is the point of a server.

Accepting unknown executable code is a much stronger requirement.

The two should not be conflated.

```text
unknown request JSON
```

is normal.

```text
unknown JAR loaded into process
```

is a plugin system.

Most services need the first.

Few need the second.

A static application graph is fully compatible with the first.

---

# Dynamic Graphs Can Be Valuable Inside Frameworks, Not Applications

There is also an architectural layering point.

A general-purpose framework may need dynamic facilities internally because it supports many application shapes.

But an individual application built on that framework may still have completely fixed topology.

Kora chooses to specialize more aggressively for application construction.

It lets the compiler perform the assembly for the concrete application instead of preserving generic assembly machinery at runtime.

This is one reason its runtime can remain smaller.

---

# The Cost of Generic Runtime Assembly Is Paid by Every Service

A generic runtime container needs to carry capabilities that a particular service may never use.

That can include:

- scanning;
- metadata;
- conditional resolution;
- proxy machinery;
- mutable bean registries;
- generic lifecycle coordination.

A compile-time system can specialize the result to the service.

The generated graph contains the wiring that application actually needs.

This is analogous to partial evaluation: known structural decisions are resolved early.

---

# The Runtime Still Has a Container, Just a Different Job

It would be inaccurate to say Kora has no runtime graph machinery at all.

The runtime:

- creates instances;
- initializes them;
- releases them;
- exposes graph access;
- supports refresh;
- manages lifecycle;
- maintains indirect references.

What it does not need to do is rediscover the application definition from scratch.

The runtime container's job is execution and lifecycle, not architectural inference.

---

# That Separation Is the Core Design Choice

The cleanest summary is:

```text
Compiler:
What can exist?
How is it connected?
Is the structure valid?

Runtime:
What are the current instances?
What is the current configuration?
Which behavior should execute now?
```

The two phases cooperate.

They do not compete.

---

# What About A/B Experiments?

A/B experiments are sometimes treated as proof that applications must dynamically swap components.

But experiments are normally request-level decisions.

Suppose:

```text
AlgorithmA
AlgorithmB
ExperimentAllocator
```

The graph contains all three.

At runtime:

```text
user 123 → variant A
user 456 → variant B
```

This is better represented explicitly than by rebuilding the DI container every time the experiment assignment differs.

---

# What About Blue/Green External Systems?

Suppose a service migrates from database A to database B.

Both clients can exist simultaneously:

```text
DatabaseA
DatabaseB
MigrationRouter
```

The router can:

- read from A;
- dual write;
- compare reads;
- shift percentages;
- eventually route to B.

This migration is inherently dynamic.

Yet a static graph handles it well because the dynamic part is routing policy.

When migration is complete, remove A in the next deployment.

No runtime topology mutation was required.

---

# What About Runtime Client Replacement?

If an endpoint or TLS configuration changes and a native client must be recreated, graph refresh handles a different case.

Instead of keeping two known implementations and routing between them, the application needs a new instance of the same component type.

That is:

```text
Client₁
  ↓ refresh
Client₂
```

The topology remains:

```text
Service → Client
```

This is exactly what instance refresh is for.

---

# Selection and Refresh Are Different Tools

It helps to keep two mechanisms distinct.

**Runtime selection:**

```text
ProviderA ─┐
           ├─ Router → choose one per operation
ProviderB ─┘
```

**Runtime refresh:**

```text
Config v1 → Client₁
              ↓
           refresh
              ↓
Config v2 → Client₂
```

Both preserve topology.

They solve different dynamic requirements.

---

# Registries Add a Third Tool

A registry handles a changing set of *data-defined entries*:

```text
Registry
├── tenant A → policy
├── tenant B → policy
└── tenant C → policy
```

The registry component is static.

Its contents are dynamic.

Between routers, refreshable instances and registries, a huge proportion of production dynamism can be expressed without dynamic component-definition mutation.

---

# Static Topology Is Particularly Friendly to Observability

Because the set of component types is bounded, metrics and traces can be designed around stable categories.

Runtime labels can represent:

- provider;
- tenant class;
- route;
- result;
- region.

The architecture does not need to invent telemetry identities for arbitrary newly loaded component types.

This is not the biggest benefit, but it contributes to operational predictability.

---

# A Smaller Runtime State Space Is Easier to Operate

Production reliability is partly about limiting state space.

A system where:

```text
code
configuration
data
component definitions
loaded plugins
conditional registrations
```

can all independently change at runtime has more possible states.

Sometimes that flexibility is required.

When it is not, constraining one dimension helps.

Kora constrains component topology.

Data, configuration and application state remain dynamic.

This can make incidents easier to reproduce.

---

# "Static" Is the Wrong Word Emotionally

The word *static* often sounds like:

```text
inflexible
hardcoded
cannot reload
must restart
```

That is not what compile-time graph means here.

A more accurate phrase would be:

> **prevalidated structural topology**

The application can still have:

- mutable state;
- live configuration;
- refreshable components;
- runtime routing;
- external control planes;
- dynamic registries;
- feature flags.

The static property is narrower and more useful than the label suggests.

---

# Kora's Model Is Closer to a Typed Dataflow Graph

One way to think about the application graph is as a typed dataflow.

Factories define transformations:

```text
Config
  ↓
DatabaseConfig
  ↓
DataSource
  ↓
Repository
  ↓
Service
```

At compile time, Kora validates that the transformations can connect.

At runtime, values flow through those nodes.

When an upstream refresh occurs, dependent values can be recomputed.

`ValueOf<T>` creates an indirect reference that observes the current result without forcing downstream recomputation.

This mental model explains runtime refresh more accurately than the phrase "static container."

---

# There Is a Parallel With Functional Reactive Systems

Without claiming Kora is a functional reactive framework, the refresh semantics have a familiar shape:

```text
known dependency graph
+
changing upstream value
→ recompute affected downstream values
```

The graph structure remains known.

Values change.

That is a common engineering pattern because it allows efficient, predictable propagation.

Kora applies a related idea to component lifecycle.

---

# Why This Matters for Framework Complexity

A runtime discovery container must answer:

```text
What components exist?
```

during runtime.

Kora answers that earlier.

The runtime can therefore focus on:

```text
What instances are current?
```

and:

```text
Which known nodes are affected by this change?
```

Those are narrower problems.

Narrower runtime responsibilities often mean less machinery.

---

# Do You Need to Refresh Everything?

No.

This is where typed config and indirect dependencies matter.

A well-designed graph should localize updates.

For example:

```text
Config
├── LoggingConfig → Logging
├── DbConfig → DataSource → Repository
└── SearchConfig → SearchClient
```

A logging-level change should not recreate the database client.

A search-endpoint change should not recreate unrelated business components unless they hold direct construction-time dependencies on the client.

Graph design therefore influences refresh cost.

---

# Runtime Refresh Is Not "Magic Hot Reload"

It is also important not to oversell the feature.

Kora does not mean:

> Change arbitrary Java source code and the running process transparently becomes a new application.

Graph refresh operates on known factories and dependencies.

If source structure changes, rebuild and redeploy.

If runtime configuration changes, affected instances can refresh.

That boundary is clear and operationally sane.

---

# Source-Code Change and Configuration Change Are Different

This distinction is worth making explicit:

```text
Change Java/Kotlin architecture
→ compile
→ deploy

Change supported runtime configuration
→ refresh/re-evaluate
→ continue
```

Trying to erase that boundary entirely usually requires complex hot-code-reload systems.

Most production teams do not need them.

---

# This Also Helps AI-Assisted Operations

An AI agent debugging a live system can reason from a stable architecture.

It can ask:

```text
Which config node changed?
Which direct dependents refresh?
Which ValueOf edges stop propagation?
Which component instance is current?
```

That is a bounded problem.

If the container can contain arbitrary runtime-discovered definitions, the agent must first reconstruct the container's current definition state.

Explicitness helps machine reasoning for the same reason it helps humans.

---

# Static Graph Is Not a Rejection of Dependency Injection

Kora still uses dependency injection extensively.

The difference is that injection is treated as compile-time composition rather than runtime discovery.

This preserves DI benefits:

- inversion of control;
- testable constructor dependencies;
- modular factories;
- implementation replacement;
- lifecycle management;
- configuration integration.

It simply moves validation and graph construction earlier.

---

# The Main Trade-Off

The trade can be stated plainly.

Kora gives up:

```text
arbitrary runtime registration of unknown dependency definitions
```

to gain:

```text
compile-time graph validation
predictable startup
explicit architecture
smaller runtime discovery surface
readable generated wiring
controlled runtime refresh
```

Whether that trade is good depends on the product.

For a plugin host, perhaps not.

For a REST service, usually yes.

---

# A Decision Checklist

Before concluding that a service needs dynamic DI, ask:

1. Will the process load implementation classes that were not present when the artifact was built?
2. Must users install executable plugins without rebuilding the service?
3. Must those plugins contribute arbitrary dependency definitions?
4. Is the dependency graph itself user-controlled product state?
5. Would a runtime registry, strategy router or feature flag solve the problem more directly?
6. Is the changing thing actually data or configuration?
7. Does a client simply need to be recreated when config changes?
8. Could `ValueOf<T>` keep long-lived components stable during that refresh?
9. Could `All<T>` or tags represent the known set of strategies?
10. Could deployment remain the mechanism for structural code changes?

If the first four answers are no, a dynamic application graph may not be solving a real requirement.

---

# A More Precise Architecture Vocabulary

Teams can improve design discussions by using more exact terms.

Instead of:

> We need the application to be dynamic.

say:

> We need runtime feature evaluation.

or:

> We need endpoint refresh.

or:

> We need credential rotation.

or:

> We need provider selection per request.

or:

> We need to load unknown plugin bytecode.

Those requirements lead to very different architectures.

Only the last one clearly implies unknown runtime component topology.

---

# The Biggest Myth: Compile-Time Means Everything Is Frozen

The strongest misconception about Kora is that once the graph is compiled, the running application becomes a frozen set of objects with immutable configuration.

That is simply the wrong model.

Kora compiles the structural relationship.

Runtime still owns instance lifecycle.

Configuration can change.

The graph can refresh affected nodes.

`ValueOf<T>` can expose current instances to components that should not themselves restart.

Application routers can choose strategies dynamically.

Registries can change contents.

External state can evolve arbitrarily.

Feature flags can change behavior instantly.

The set of possible components can be fixed without fixing the world around them.

---

# A Complete Example

Consider a checkout service.

Its compile-time graph contains:

```text
CheckoutController
        ↓
CheckoutService
        ↓
PaymentRouter
     ↙         ↘
Stripe       Adyen
        ↓
FeatureFlags

CheckoutService
        ↓
OrderRepository
        ↓
DataSource

CheckoutService
        ↓
ValueOf<FraudClient>
```

At runtime:

- an experiment switches some users from Stripe to Adyen;
- feature flags change remotely;
- tenant-specific payment policy changes;
- the fraud endpoint changes in configuration;
- `FraudClient` is rebuilt;
- `CheckoutService` remains alive because it uses `ValueOf<FraudClient>`;
- database rows change continuously;
- credentials rotate;
- logging is temporarily raised to DEBUG.

The graph topology has not changed.

The system is nevertheless highly dynamic.

This is a realistic production model.

---

# Now Compare the Truly Dynamic Case

Imagine instead that merchants can upload payment-provider plugins as JARs.

A new plugin may contain:

```text
NewPaymentProvider.class
PluginFraudChecker.class
PluginSerializer.class
```

and the running server must:

```text
load classes
↓
discover extension metadata
↓
register new services
↓
resolve new dependencies
↓
activate plugin
```

Now the dependency topology truly is runtime data.

Kora's compile-time application graph is not naturally designed for that job.

That is the honest boundary.

And it is much narrower than saying "Kora applications cannot be dynamic."

---

# The Right Final Distinction

The debate should therefore not be:

```text
static framework
vs
dynamic framework
```

It should be:

```text
prevalidated structure
+
dynamic runtime state
```

versus:

```text
runtime-defined structure
+
dynamic runtime state
```

Most backend services need the first.

A specialized class of extensible platforms needs the second.

---

# Conclusion: Put Dynamism Where It Belongs

Production services are dynamic by nature.

They process unpredictable data. They react to changing configuration. They evaluate flags. They rotate credentials. They route between providers. They apply tenant-specific rules. They retry according to current policy. They talk to endpoints that appear and disappear. They continuously change their state as the world changes around them.

None of that proves that their dependency topology must also be discovered or mutated at runtime.

For the majority of backend applications, the structural architecture is known when the artifact is built:

```text
controller
   ↓
service
   ↓
repository
   ↓
database
```

What changes is everything flowing through and around that structure.

Kora embraces that reality by separating structural certainty from runtime flexibility.

At compile time, it determines which components may exist, how they depend on one another, which implementations satisfy which contracts, and whether the graph is valid. That gives the framework compile-time diagnostics, explicit ownership, predictable assembly and readable generated wiring.

At runtime, Kora still creates and manages component instances. Configuration can be watched and reloaded. `RefreshableGraph` can rebuild the portion of the graph affected by a changed node. `ValueOf<T>` lets a stable component observe the current version of a dependency without being recreated itself. Feature flags, strategy routers, component collections, tags, registries and ordinary application logic can select behavior dynamically per request or per tenant.

The result is not a static application.

It is a statically validated architecture with dynamic runtime behavior.

That is a much more useful distinction.

```text
Compile time

Component A
    ↓
Component B
    ↓
Component C

Topology is known and validated
```

while runtime can still do:

```text
config v1
   ↓
Component B₁

        refresh

config v2
   ↓
Component B₂

Component C can either:
- rebuild if it directly depends on B
- stay alive and read current B through ValueOf<B>
```

That is not the absence of dynamism. It is controlled dynamism.

The honest limitation appears only when the application itself is a runtime extension platform: an IDE, an application server, a plugin marketplace, a container for arbitrary user code, or another system that must download unknown bytecode, discover new types and mutate the dependency topology after deployment.

For those systems, dynamic discovery is not incidental framework flexibility. It is part of the product.

For a REST or gRPC service, Kafka consumer, API gateway, worker, scheduler or database-backed business service, it usually is not.

That leads to the central architectural principle:

> **If the structure of your service changes unpredictably at runtime, that is a specialized architectural requirement — not the default requirement of server-side applications.**

And it explains Kora's design more accurately than the phrase "static DI":

> **Kora does not remove runtime dynamism. It moves dynamism out of framework wiring and into explicit application logic, where it is easier to understand, test and control.**

The same idea can be stated even more precisely:

> **Kora makes the set of possible dependencies explicit at compile time while allowing their configuration, state, selection and lifecycle to evolve at runtime.**

Compile-time safety and runtime flexibility are not opposites.

They apply to different things.

The real design question is not whether an application should be dynamic.

It is whether the dependency graph itself needs to be part of that dynamism.

For most production backend services, the answer is no.
