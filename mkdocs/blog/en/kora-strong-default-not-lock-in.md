---
title: A Strong Default Is Not Lock-In — The Kora Framework Is Built to Be Extended
description: Why the Kora Framework's opinionated defaults are extensible — replace generated components and add integrations through the same application graph.
search:
  exclude: true
---
# A Strong Default Is Not Lock-In: Kora Is Built to Be Extended

Opinionated frameworks are often judged through a false binary.

Either the framework provides many competing ways to solve the same problem, in which case it is described as flexible, or it provides one recommended path, in which case it risks being described as
restrictive. The implication is that freedom comes from the number of visible alternatives and lock-in begins as soon as a framework says, "this is the way we recommend doing it."

That is not a useful definition of extensibility.

A framework can expose ten extension points and still be difficult to customize if the default implementation is deeply embedded in runtime internals. It can support several programming models and
still make a core component almost impossible to replace without understanding private bootstrap rules. It can advertise a broad plugin system while forcing custom code into a separate integration
layer that behaves differently from framework-owned code.

The inverse is also true.

A framework can provide one strong, opinionated default while remaining highly extensible if that default is simply one implementation inside a public application model. If an alternative
implementation can be added through the same dependency graph, if a generated component can yield to another implementation of the same contract, if modules are opt-in, and if custom components
participate in the same lifecycle, dependency validation, telemetry, and composition rules as built-in components, then the framework is opinionated without being closed.

That is the important distinction in the Kora Framework.

Kora deliberately tries to reduce the number of competing ways to solve common backend problems. Its philosophy of "one problem — one solution" is not intended to mean that alternative implementations
are forbidden. It means the framework wants one clear default path that teams can adopt without spending days choosing among overlapping internal APIs. The default is the recommended path, not the
boundary of what the application is allowed to do.

The architecture remains open.

A simplified view looks like this:

```text
Closed framework

default implementation
        ↓
framework internals
        ↓
hard to replace
        ↓
fork / workaround / deep extension API
```

Kora aims for a different model:

```text
Kora

default implementation
        ↓
public contract
        ↓
replace / extend / add module
        ↓
same explicit application graph
```

This leads to the central argument of the article:

> **A framework is not truly extensible because it has many extension points. It is extensible when custom code participates in the same model as built-in code.**

Kora's extensibility is strongest precisely because it does not create a separate world for extensions. A custom component does not enter through a hidden plugin registry. A custom integration does
not have to bypass dependency injection. A replacement implementation does not require a fork of the framework. A locally written module can be composed using the same mechanisms as the modules
shipped by Kora itself.

That is a much stronger form of extensibility than a large catalog of special hooks.

## Opinionated Does Not Mean Closed

There are two different ideas that are frequently confused:

```text
opinionated default
```

and:

```text
mandatory implementation
```

They are not the same.

An opinionated default says:

> We have chosen one approach that works well for the common case. It is documented, tested, integrated, and supported as the path most users should begin with.

A mandatory implementation says:

> The rest of the framework assumes this exact implementation exists, and replacing it requires fighting the framework.

The first can reduce cognitive load.

The second creates lock-in.

Kora's design philosophy is clearly closer to the first.

The framework tries to provide a coherent default for common backend concerns so that teams do not have to choose among multiple overlapping APIs for every layer. That is valuable because backend
systems already have enough real decisions: database topology, API design, consistency, concurrency, failure handling, scaling, schema ownership, observability, deployment, and security. A framework
does not necessarily make developers more productive by creating additional internal choices for all of those concerns.

If three framework APIs perform roughly the same job, teams now need another decision:

```text
Which framework abstraction should we use?
```

Then another:

```text
Which one is considered current?
```

Then another:

```text
Can modules written with different models interoperate?
```

Then another:

```text
Which model should new engineers learn?
```

The cost is not only documentation.

It is organizational fragmentation.

Kora's "one clear way" philosophy tries to remove this class of decision where possible. That makes the default path narrower, but the architecture can still remain open underneath it.

The distinction is:

```text
few preferred ways
≠
few possible integrations
```

This is the key to understanding Kora's extensibility model.

## The Application Graph Is the Extension Surface

Kora's dependency graph is not only a mechanism for wiring framework components.

It is the architectural surface through which application code, framework code, generated code, and third-party integrations meet.

That is important because it avoids a common framework problem: built-in components live in one privileged world while user extensions live in another.

A Kora application can contain:

```text
built-in Kora component
generated component
application @Component
factory from @Module
third-party library client
custom implementation
internal company integration
```

From the graph's perspective, those are all components.

Their origin is less important than their contract and dependencies.

That means a custom implementation can participate in the same structure:

```text
configuration
      ↓
custom module
      ↓
custom component
      ↓
service
      ↓
controller
```

just as a built-in implementation might participate in:

```text
configuration
      ↓
Kora module
      ↓
default component
      ↓
service
      ↓
controller
```

This symmetry is the heart of extensibility.

A custom component is not tolerated as an exception. It becomes part of the normal dependency model.

## Opt-In Modules Change the Meaning of "Framework"

Large frameworks often acquire gravitational pull.

You add one high-level framework dependency, and that dependency brings a large set of capabilities, transitive libraries, auto-configuration, discovery mechanisms, runtime infrastructure, and default
integrations. Even if the application uses only a fraction of them, the framework establishes a broad runtime environment.

Kora takes a more modular approach.

The application explicitly connects the modules it needs.

A small application might look roughly like:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends
        HoconConfigModule,
        JsonModule,
        UndertowHttpServerModule {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        UndertowHttpServerModule
    ```

If the service later needs metrics:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends
        HoconConfigModule,
        JsonModule,
        MetricsModule,
        UndertowHttpServerModule {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        MetricsModule,
        UndertowHttpServerModule
    ```

If it needs an OpenTelemetry exporter, that module is added explicitly.

If it needs Kafka, gRPC, JDBC, S3, scheduling, caching, or another integration, those capabilities enter the application because the project chooses them.

This changes the mental model from:

```text
framework platform
      ↓
disable what you do not want
```

to:

```text
minimal application
      ↓
add what you need
      ↓
compose final graph
```

That is an important form of extensibility because the easiest component to replace is often the component that was never forced into the application in the first place.

## Minimal Core, Incremental Stack

A good framework should let the service architecture grow according to actual requirements.

Kora's module model supports this.

An early service may only need:

```text
configuration
HTTP
JSON
logging
```

Later it may add:

```text
PostgreSQL
telemetry
Kafka
resilience
```

Later still:

```text
gRPC
cache
scheduling
custom internal SDK
```

The framework does not require the application to commit to an enormous platform footprint on day one.

The resulting growth pattern is:

```text
service requirements
        ↓
choose module
        ↓
add to graph
        ↓
compile-time validation
```

That has two architectural benefits.

First, the dependency surface remains intentional. A technology enters the application because somebody added it.

Second, extensibility does not require replacing a monolithic runtime. The application is already composed from modules, so a custom module naturally fits the same shape.

## Built-In Modules Are Examples of the Same Model

The strongest extension model is one in which framework authors use essentially the same public composition mechanisms they expect application developers to use.

Kora's module architecture comes close to this ideal.

A framework integration typically provides components through module interfaces. Application code connects those modules to `@KoraApp`. A custom integration can also expose components through a module
interface and be connected to the same application.

Conceptually:

```text
Built-in module

FrameworkModule
    ├── configuration
    ├── default component
    ├── telemetry
    └── lifecycle
          ↓
      application graph
```

A custom module can look like:

```text
CustomModule
    ├── configuration
    ├── custom client
    ├── telemetry
    └── lifecycle
          ↓
      application graph
```

The important part is what does **not** appear between them:

```text
special extension runtime
plugin manager
service locator
reflection registry
custom bootstrap API
```

That absence makes the architecture easier to reason about.

## `@Module` Is More Powerful Than a Plugin API

A traditional plugin system often provides a framework-specific interface:

===! ":fontawesome-brands-java: `Java`"

    ```java
    interface FrameworkPlugin {
        void register(FrameworkRegistry registry);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface FrameworkPlugin {
        fun register(registry: FrameworkRegistry)
    }
    ```

The custom code now has to understand:

- when registration occurs;
- how the registry resolves dependencies;
- what order plugins execute in;
- how lifecycle is managed;
- whether registered objects are visible to normal DI;
- how configuration is accessed;
- how testing works;
- whether compiler validation still applies.

This creates a second composition model.

A Kora `@Module` factory is much simpler conceptually.

It says:

```text
given these dependencies
produce this component
```

For example:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface SearchModule {

        default SearchClient searchClient(
            SearchConfig config,
            SearchTelemetry telemetry) {

            return new SearchClient(
                config.endpoint(),
                telemetry
            );
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface SearchModule {

        fun searchClient(
            config: SearchConfig,
            telemetry: SearchTelemetry): SearchClient {

            return SearchClient(
                config.endpoint(),
                telemetry
            )
        }
    }
    ```

The component enters the same graph as everything else.

The compiler can validate whether `SearchConfig` and `SearchTelemetry` exist.

A service can inject `SearchClient`.

A different component can decorate or depend on it.

Tests can replace it.

Lifecycle can be attached.

The extension is not a side channel.

It is dependency injection.

That simplicity is what makes the mechanism powerful.

## Custom and Built-In Components Share the Same Status

This is one of the most important properties of a truly extensible framework.

Suppose an application contains:

```text
Kora HTTP server
generated repository
custom fraud client
built-in metrics implementation
custom feature flag implementation
generated OpenAPI client
internal audit module
```

A framework with privileged built-in components may represent this internally as:

```text
framework components
        +
user extensions
```

Kora's graph allows a cleaner model:

```text
Application Graph
├── HTTP server
├── repository
├── fraud client
├── metrics
├── feature flags
├── OpenAPI client
└── audit service
```

The source of a component is secondary.

What matters is:

- its type;
- its tags where relevant;
- its dependencies;
- its lifecycle;
- its place in the graph.

This is why the phrase "first-class custom integration" is meaningful.

First-class does not mean there is an annotation called `@Extension`.

It means custom code does not have to leave the normal application model.

## Strong Defaults Should Be Replaceable at the Contract Boundary

The most useful default implementation is one selected behind a stable contract.

Kora uses `@DefaultComponent` in several modules for exactly this kind of behavior.

A default component is available when the application has not supplied a stronger alternative. Application code can provide another implementation of the same required contract and allow that
implementation to become the selected component.

The important architectural shape is:

```text
contract
   ↑
   │
default implementation
```

and:

```text
contract
   ↑
   │
custom implementation
```

The consumer depends on the contract.

It should not care which implementation won.

This is very different from a default that is wired deep inside framework internals.

Consider telemetry tag generation. Kora's metrics documentation exposes default tag-provider components for HTTP, gRPC, Kafka, and other integrations. Applications can provide their own implementation
of the corresponding provider contract when the standard tag mapping is not suitable.

That is a concrete example of the broader extensibility principle.

The framework has a default.

The default is not the only possible implementation.

## Why `@DefaultComponent` Is an Important Design Signal

The value of `@DefaultComponent` is larger than the annotation itself.

It encodes an architectural relationship:

> The framework is willing to provide this implementation, but it acknowledges that the application owns the final graph.

That is a healthy ownership model.

The framework may say:

```text
Here is a sensible metrics tag provider.
```

The application can say:

```text
Our organization requires a different cardinality policy.
```

The application should not have to fork the metrics module.

It should provide another component implementing the public contract.

The same pattern is applicable wherever a framework can cleanly separate policy from mechanism.

This reduces the risk that framework defaults become organizational constraints.

## Generated Code Should Not Mean Generated Lock-In

Compile-time code generation can create a different kind of lock-in if generated implementations are treated as untouchable internals.

That does not have to be the case.

Generated code is most flexible when the generated class implements or satisfies a normal contract that the rest of the graph consumes.

Imagine:

```text
Repository interface
        ↓
generated implementation
        ↓
application service
```

The key design question is not whether the implementation was generated.

The key question is whether application code depends on:

```text
Repository interface
```

or:

```text
framework-generated concrete implementation
```

If the contract is the boundary, another implementation can be supplied.

That gives:

```text
Repository interface
       ▲
       ├── generated repository
       └── custom repository
```

The application service still depends on the same interface.

Generation is therefore a convenience and optimization, not necessarily a cage.

This distinction is important because code generation is sometimes described as making frameworks rigid. In practice, generated code can actually increase flexibility if it creates ordinary typed
implementations rather than hidden runtime objects.

## Replace the Implementation, Keep the Graph

A powerful extensibility pattern is replacing one part of an application without changing the rest of its architecture.

Suppose a service begins with a standard implementation:

```text
OrderService
    ↓
PaymentClient
    ↓
default transport
```

Later the organization needs a specialized transport.

A closed framework might force:

```text
new transport
      ↓
custom bootstrap
      ↓
bypass framework client stack
      ↓
manual lifecycle
```

A graph-oriented framework should allow:

```text
OrderService
    ↓
PaymentClient contract
    ↓
custom transport implementation
```

The rest of the graph does not care.

This is the essence of inversion of control.

The framework should not own the concrete object merely because it supplied the first one.

## Extensibility Is Strongest When Validation Still Works

A hidden escape hatch usually weakens guarantees.

For example, if a framework validates application wiring at compile time but custom extensions enter through a runtime registry, those extensions may bypass the main safety model.

That creates two levels of confidence:

```text
built-in graph
    → compile-time validated

custom plugin
    → runtime validated
```

The application now has a weak seam exactly where customization occurs.

Kora's graph model avoids this in many cases because custom components are still graph components.

If a custom `@Module` factory requires dependencies that cannot be resolved, the graph processor can reject the application.

If a custom implementation creates an ambiguous contract, that ambiguity can be reported.

If a dependency cycle appears through custom code, the graph can still reason about it.

The extension therefore remains inside the framework's strongest validation boundary.

This is much better than a plugin system that says:

> You can extend anything, but once you do, you are on your own.

## Extensibility Should Preserve Lifecycle

Dependency construction is only one part of a production framework.

A custom component may own:

- threads;
- connections;
- sockets;
- pools;
- background workers;
- watchers;
- channels.

If extensions are first-class, they should be able to participate in application startup and shutdown.

Kora's lifecycle model allows custom components to do this.

A custom client can be constructed through a module and wrapped in lifecycle behavior if necessary.

Conceptually:

```text
configuration
      ↓
custom module
      ↓
client
      ↓
initialize
      ↓
application use
      ↓
graceful release
```

This matters because many frameworks are easy to extend at object creation time but difficult to extend operationally.

The object can be registered.

But shutdown ordering is private.

Readiness is separate.

Telemetry is separate.

Testing uses another model.

True extensibility includes operational behavior.

## Extensibility Should Preserve Observability

A custom component is only truly first-class in production if it can be observed.

Kora's application model allows custom integrations to consume or expose the same telemetry infrastructure used by built-in components.

A custom database-like client might depend on:

```text
MeterRegistry
Tracer
structured logger
```

or on a project-specific telemetry abstraction.

The custom module can attach those during construction.

A custom component can also provide readiness or liveness probes if that dependency affects application availability.

This gives a consistent operational shape:

```text
built-in integration
  ├── config
  ├── lifecycle
  ├── telemetry
  └── graph component

custom integration
  ├── config
  ├── lifecycle
  ├── telemetry
  └── graph component
```

That symmetry matters more than the number of explicit extension APIs.

## The Difference Between Extensibility and Escape Hatches

Framework documentation often lists "extension points" as evidence of flexibility.

But an extension point can mean many things.

A healthy extension point looks like:

```text
public contract
      ↓
your implementation
      ↓
normal framework composition
```

An unhealthy escape hatch looks like:

```text
unsupported use case
      ↓
special registry
      ↓
framework internal hook
      ↓
undocumented ordering
      ↓
hope upgrades do not break it
```

Both technically allow customization.

Only one is sustainable.

The strongest argument for Kora's approach is that many customizations are not extensions in the exotic sense at all.

They are ordinary components.

That drastically reduces the amount of special framework knowledge required.

## Custom Modules Are Architecture, Not Framework Plumbing

Suppose a company has an internal feature flag service.

It could be integrated like this:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface FeatureFlagsModule {

        default FeatureFlagsClient featureFlagsClient(
            FeatureFlagsConfig config,
            Telemetry telemetry) {

            return new FeatureFlagsClient(
                config.endpoint(),
                telemetry
            );
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface FeatureFlagsModule {

        fun featureFlagsClient(
            config: FeatureFlagsConfig,
            telemetry: Telemetry): FeatureFlagsClient {

            return FeatureFlagsClient(
                config.endpoint(),
                telemetry
            )
        }
    }
    ```

Application code injects the client.

If several services use the same integration, the module can move into an internal library.

The result might become:

```text
company-kora-feature-flags
```

This is not a hack around the framework.

It is architecture expressed using the framework's native composition model.

That distinction matters because internal platform teams often need dozens of company-specific integrations no public framework can reasonably ship.

The right framework does not need to know those systems in advance.

It needs to make integrating them ordinary.

## Extension Through Composition Is More Stable Than Extension Through Internals

Framework internals change.

Private bootstrap classes change.

Reflection registries change.

Lifecycle internals change.

Compiler implementations change.

An extension that depends on those details has high upgrade cost.

Composition through public contracts is more stable.

If a custom component depends only on:

```text
public configuration contract
public graph contract
public lifecycle contract
public telemetry contract
```

then framework internals can evolve without forcing the extension to evolve at the same rate.

That is one reason explicit dependency injection is such a strong extension model.

Dependencies are visible at the type level.

The extension is coupled to what it actually uses.

## One Problem — One Solution Is an Organizational Optimization

The phrase "one problem — one solution" can sound dogmatic if interpreted literally.

A better interpretation is organizational.

Imagine a framework supporting three official HTTP client models:

```text
HTTP Client A
HTTP Client B
HTTP Client C
```

Each has:

- its own annotations;
- its own configuration;
- its own telemetry behavior;
- its own error handling;
- its own testing story;
- its own lifecycle;
- its own documentation.

Teams now make local choices.

After several years:

```text
Team A → Client A
Team B → Client B
Team C → Client C
Legacy service → Client A v1
New service → Client C
```

The organization no longer has one framework model.

It has several sub-frameworks.

The maintenance surface multiplies.

Kora's preference for one recommended model reduces this entropy.

But if the chosen model truly cannot solve a requirement, the graph should still allow another implementation.

That balance is important:

```text
default path
    → narrow

extension boundary
    → open
```

This is arguably a better definition of an opinionated framework than simply providing fewer APIs.

## Lock-In Is About Exit Cost

A useful way to evaluate lock-in is to ask:

> What is the cost of saying no to the framework's default?

If the answer is:

```text
rewrite application architecture
```

that is strong lock-in.

If the answer is:

```text
fork framework
```

that is strong lock-in.

If the answer is:

```text
use undocumented internal SPI
```

that is fragile lock-in.

If the answer is:

```text
provide another implementation of a public contract
```

that is relatively weak lock-in.

If the answer is:

```text
do not add that module in the first place
```

that is weaker still.

Kora's modular design improves this exit cost.

A framework feature that is never connected to the application graph does not need to be disabled.

A default component that can be overridden does not need to be patched.

A missing integration can be added through `@Module`.

This does not mean Kora creates zero lock-in. Any framework introduces conventions, annotations, generated code, configuration shapes, and build tooling that create switching cost.

The meaningful claim is narrower:

> Kora tries to prevent its defaults from becoming mandatory architectural dependencies when normal composition can remain open.

That is a more defensible and useful definition.

## NIH Is Not About Whether the Framework Implements Something

The "Not Invented Here" criticism is often applied too broadly.

If a framework provides its own repository abstraction, HTTP annotations, resilience layer, scheduler integration, or configuration model, someone may say:

> Why implement this at all? Another library already exists.

But the mere existence of framework-owned code is not the real danger.

The real NIH risk appears when a framework says:

```text
our implementation
=
the only implementation the architecture can tolerate
```

That creates a closed world.

A healthier model is:

```text
our implementation
=
recommended default
```

with:

```text
your implementation
=
equally valid graph component
```

The risk of NIH is therefore not simply that a framework implements functionality itself.

The risk appears when that implementation becomes mandatory, opaque, or expensive to replace.

Kora's module and graph design explicitly tries to avoid that trap.

## Native Libraries Remain an Option

This becomes particularly important when integrating third-party technologies.

A framework does not need an official wrapper for every library if a native client can become a normal graph component.

Suppose a service needs a library Kora does not officially support.

The extension path can be:

```text
native library
      ↓
configuration
      ↓
@Module factory
      ↓
optional lifecycle / telemetry
      ↓
application graph
```

There is no requirement that the library become a Kora-specific abstraction first.

This is another way strong defaults avoid becoming lock-in.

The framework can provide preferred integrations for common technologies while leaving the rest of the JVM ecosystem accessible.

## You Can Extend Vertically or Horizontally

Kora's composition model supports two broad kinds of extension.

### Vertical extension

Replace or customize a piece of an existing integration.

Examples might include:

- a custom telemetry tag provider;
- a custom mapper;
- a custom interceptor;
- a custom security handler;
- a custom serializer;
- an alternative client factory.

The surrounding module stays.

Only one policy or component changes.

The shape is:

```text
existing module
   ├── default A
   ├── default B
   ├── default C
   └── replace B
```

### Horizontal extension

Add an entirely new capability.

For example:

```text
custom feature flags
custom vendor SDK
custom internal RPC client
custom workflow engine
custom audit system
```

The shape is:

```text
existing application graph
          +
new module
          ↓
larger application graph
```

A healthy framework should support both.

Vertical extension prevents default behavior from becoming rigid.

Horizontal extension prevents the official module catalog from becoming the boundary of the ecosystem.

## Explicit Graphs Make Replacement Understandable

Runtime auto-discovery can make replacement surprisingly difficult.

If the framework creates an object because:

- a class is present;
- a property has a value;
- another bean is missing;
- an annotation was detected;
- a conditional configuration matched;
- an ordering rule selected one candidate;

then replacing the object may require understanding the entire discovery process.

An explicit graph reduces the number of hidden conditions.

The application composition tells you which modules participate.

The contracts tell you what dependencies are required.

The compiler tells you if the graph is invalid.

This is particularly valuable during customization.

The question:

> Why did my replacement not win?

should ideally be answerable from type relationships and graph rules rather than from hidden runtime state.

## Compile-Time Validation Makes Extensibility Safer

Extensibility often increases risk because more combinations become possible.

The typical trade is:

```text
more flexible
      ↓
more runtime combinations
      ↓
more possible startup failures
```

Compile-time validation changes this trade.

If custom components use the same graph model, the framework can validate many custom compositions before the application runs.

This lets Kora support an open graph without giving up strong structural guarantees.

For example, a custom module may create:

```text
CustomClient
```

which requires:

```text
CustomConfig
Telemetry
Credentials
```

If one of those dependencies is unavailable, the graph should fail during compilation rather than after deployment.

Extensibility remains explicit and typed.

That is a much better model than dynamically loading arbitrary plugins and discovering incompatibilities at startup.

## A Single Graph Prevents "Extension Islands"

Some frameworks accumulate subsystems that effectively behave like separate containers.

The main DI system manages application services.

A security subsystem manages its own providers.

A persistence framework manages repositories.

A messaging library has a registry.

An extension framework manages plugins.

A scheduler has another lifecycle.

The application becomes a federation of hidden object graphs.

That can work, but it complicates reasoning.

Kora's architectural ideal is that these concerns feed into one application graph as far as practical.

This matters because dependencies can cross integration boundaries naturally.

A custom component can depend on framework telemetry.

A framework component can depend on application configuration.

A generated component can depend on a custom implementation.

The graph remains one system.

This is the practical meaning of:

> **Custom and built-in components participate in the same model.**

## Testing Reveals Whether Extensibility Is Real

A framework's test support is a good place to inspect whether custom components are truly first-class.

Kora's test graph can replace components, add components, and keep real graph dependencies around them.

That means a test can take:

```text
real UserService
```

and replace:

```text
UserRepository
```

with a mock while still letting Kora assemble the rest of the required graph.

The same principle generalizes beyond mocks.

Testing demonstrates that graph components are replaceable units rather than hard-coded runtime objects.

A framework that makes components easy to replace in tests often has a healthier inversion-of-control model in production too.

## Replacement Is Different from Mutation

There is another subtle but important design distinction.

A framework can support customization by allowing users to mutate an existing internal object:

```text
framework creates object
        ↓
application callback mutates it
```

or by allowing the application to provide a replacement:

```text
contract
   ↓
application provides implementation
```

Mutation can be convenient for small tweaks.

Replacement is usually architecturally cleaner because ownership is explicit.

The application knows what object it created.

The framework knows only the contract.

There is less hidden state and fewer ordering assumptions.

Kora's component model naturally supports replacement-oriented design.

## Extensibility Without Multiple Programming Models

Another way frameworks pursue flexibility is by supporting several programming paradigms simultaneously.

For example:

```text
blocking
reactive
coroutines
callbacks
```

This creates flexibility, but it also expands the framework surface dramatically.

Every major integration may need multiple variants.

Telemetry has to work across all of them.

Context propagation differs.

Transactions differ.

Testing differs.

Documentation branches.

Kora 2 deliberately narrows this by returning to ordinary synchronous Java and Kotlin APIs on virtual threads for application code.

This is a useful example of the distinction between **programming-model breadth** and **architectural extensibility**.

Kora can support a narrower programming model while remaining open to custom components.

The framework does not need three ways to express every service method in order to be extensible.

It needs a public composition model that accepts different implementations.

## Extensibility Should Reduce Fork Pressure

One of the strongest indicators of a closed framework is how often serious users need to fork it.

Forks happen for many reasons, and some are unavoidable. But frequent forks often indicate that critical policies are embedded in framework internals.

A better extension model allows:

```text
default implementation
      ↓
override
```

instead of:

```text
default implementation
      ↓
patch source
      ↓
maintain fork
```

Forking has a high long-term cost.

You now own:

- upstream merge conflicts;
- security fixes;
- release synchronization;
- compatibility testing;
- build publishing;
- internal documentation;
- migration responsibility.

A small custom module is dramatically cheaper.

That is why replaceability is not an academic property. It directly affects maintenance economics.

## The Best Extension Point Is Often a Normal Interface

Frameworks sometimes create elaborate SPIs for capabilities that Java interfaces could already express.

There are valid cases for a formal SPI, especially when discovery, versioning, isolation, or plugin loading are required.

But inside one application, a public interface plus dependency injection is often sufficient.

For example:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface TenantResolver {
        Tenant resolve(RequestContext context);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface TenantResolver {
        fun resolve(context: RequestContext): Tenant
    }
    ```

A default implementation can exist.

An application can provide another implementation.

The consumer depends on `TenantResolver`.

Nothing else is required.

This is a useful design principle:

> **Do not invent a framework extension system when ordinary dependency inversion already solves the problem.**

Kora's graph-oriented architecture benefits from this principle.

## Extending Kora With a Custom Integration

Consider a service that needs an internal document store unavailable as an official Kora integration.

The native client might look like:

===! ":fontawesome-brands-java: `Java`"

    ```java
    DocumentStoreClient.connect(endpoint, credentials);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    DocumentStoreClient.connect(endpoint, credentials)
    ```

A custom configuration contract can represent the required settings:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @ConfigSource("documentStore")
    public interface DocumentStoreConfig {
        String endpoint();

        Duration timeout();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @ConfigSource("documentStore")
    interface DocumentStoreConfig {
        fun endpoint(): String

        fun timeout(): Duration
    }
    ```

The custom module can construct the client:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface DocumentStoreModule {

        default DocumentStoreClient documentStoreClient(
            DocumentStoreConfig config,
            Credentials credentials) {

            return DocumentStoreClient.builder()
                .endpoint(config.endpoint())
                .credentials(credentials)
                .timeout(config.timeout())
                .build();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface DocumentStoreModule {

        fun documentStoreClient(
            config: DocumentStoreConfig,
            credentials: Credentials): DocumentStoreClient {

            return DocumentStoreClient.builder()
                .endpoint(config.endpoint())
                .credentials(credentials)
                .timeout(config.timeout())
                .build()
        }
    }
    ```

Now the application can inject it:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class ArchiveService {

        private final DocumentStoreClient client;

        public ArchiveService(DocumentStoreClient client) {
            this.client = client;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ArchiveService(private val client: DocumentStoreClient)
    ```

If the client owns resources, add lifecycle behavior.

If it needs telemetry, connect telemetry during construction.

If availability matters, add a readiness probe.

If several services use it, extract the module into a shared library.

At no point does the integration need to bypass Kora.

That is the practical test of extensibility.

## The Custom Module Can Become Part of Your Platform

This becomes particularly valuable for large organizations.

Most enterprises have infrastructure no public framework will ever ship:

```text
internal auth
internal service discovery
internal secret store
internal RPC
internal audit
internal feature flags
internal deployment metadata
internal configuration service
```

A framework that assumes all useful integrations must come from its official ecosystem is a poor fit for these environments.

Kora's module model lets a platform team create internal modules using the same graph mechanics.

For example:

```text
company-kora-auth
company-kora-observability
company-kora-feature-flags
company-kora-audit
company-kora-service-discovery
```

Application teams then compose them exactly as they compose framework modules.

The organization's platform becomes an extension of Kora without requiring a private fork of Kora.

This is one of the strongest real-world advantages of a simple module model.

## Strong Defaults Improve Extension Quality

There is an interesting paradox here.

A framework with fewer built-in choices can sometimes make custom extensions easier to design.

Why?

Because the extension author only has one framework model to integrate with.

If the framework supports:

```text
three HTTP models
two DI modes
two telemetry systems
blocking and reactive repositories
multiple config systems
```

a reusable extension may need to decide which combinations it supports.

If Kora provides one coherent model, a custom module has a clearer target.

The integration question becomes:

```text
How do I expose this capability into the Kora graph?
```

rather than:

```text
Which Kora programming model should I support?
```

Strong defaults reduce the dimensionality of extension.

## The Cost of Extensibility Is Often Combinatorial

Suppose a framework offers:

- 3 HTTP models;
- 2 persistence models;
- 3 async models;
- 2 telemetry APIs.

That does not create twelve choices.

It creates potentially dozens of interactions.

A framework maintainer has to reason about compatibility.

An extension author has to decide which combinations matter.

Users have to debug combinations that may not be equally mature.

A narrower framework can avoid much of this combinatorial explosion.

This is one reason "many extension points" is not automatically a sign of superior extensibility.

Sometimes it is a sign that the framework has many internal dimensions that require extension points.

## A Good Default Reduces Decision Cost

For most teams, the default path matters much more often than the extension path.

A framework should therefore optimize both:

```text
common case
    → extremely clear

uncommon case
    → still possible
```

These goals are compatible.

The common path should not require a design committee.

The uncommon path should not require a framework fork.

Kora's philosophy can be summarized in exactly those terms.

The framework wants to be opinionated where repeated choices create little value.

It wants to remain composable where real requirements differ.

## The Application Owns the Final Composition

One of the most important consequences of an explicit `@KoraApp` composition root is that the application—not the framework—describes the final graph.

That means the application's architecture is visible at the top level.

A root might compose:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends
        HoconConfigModule,
        JsonModule,
        UndertowHttpServerModule,
        MetricsModule,
        InternalFeatureFlagsModule,
        CompanyAuditModule {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        UndertowHttpServerModule,
        MetricsModule,
        InternalFeatureFlagsModule,
        CompanyAuditModule
    ```

This is valuable because the application can answer:

> Which framework capabilities have we chosen?

> Which internal integrations participate?

> Which modules are ours?

> Where is the composition boundary?

This is much clearer than a system where the classpath implicitly determines application architecture.

Explicit composition is therefore both an extensibility mechanism and a governance mechanism.

## There Is Still Such a Thing as Bad Extension Design

Kora's open graph does not automatically make every customization wise.

A team can still create:

- too many wrappers;
- conflicting implementations;
- overly broad shared modules;
- deep dependency cycles;
- internal abstractions that duplicate upstream libraries;
- custom replacements that break expected telemetry or lifecycle semantics.

Extensibility creates responsibility.

The correct lesson is not:

> Everything should be replaced.

It is:

> Replacement should be possible when requirements justify it.

Defaults exist because they encode useful decisions.

Replacing them should be driven by a clear need, not by a reflex to customize.

## When the Default Should Usually Win

The built-in implementation is normally the right choice when:

- it meets functional requirements;
- its performance is sufficient;
- it follows the desired observability model;
- it has correct lifecycle behavior;
- it is actively maintained;
- the team has no meaningful differentiating requirement.

Replacing a working default creates ownership.

The team now owns:

- implementation behavior;
- upgrades;
- testing;
- edge cases;
- documentation.

Extensibility is valuable because it gives an option.

It does not mean every option should be exercised.

## When Replacement Is Justified

A custom implementation becomes reasonable when there is a clear mismatch.

For example:

- organization-specific security policy;
- custom telemetry cardinality rules;
- vendor-specific client behavior;
- internal infrastructure;
- performance requirements;
- compatibility with a legacy system;
- migration between technologies;
- regulatory behavior;
- custom serialization;
- specialized failure policy.

The important point is that Kora does not require those requirements to become framework patches.

They can remain application or platform code.

## The Graph Is a Better Extension Boundary Than Global Configuration

Another common customization technique is global configuration.

A framework may expose hundreds of properties:

```text
framework.feature.mode=x
framework.feature.strategy=y
framework.feature.provider=z
```

This can make the framework configurable without making it truly extensible.

Configuration only allows choices the framework authors anticipated.

Composition allows application-defined behavior.

This distinction is fundamental.

Configuration says:

> Pick among my options.

Dependency injection says:

> Provide an implementation of this contract.

The second is more open-ended.

Kora uses configuration heavily where configuration is appropriate, but the graph provides a stronger escape from predefined options.

## Explicit Composition Helps Migration

Replaceability becomes especially valuable during migrations.

Suppose an organization is moving from one client implementation to another.

A rigid framework encourages a flag day:

```text
old integration
      ↓
remove
      ↓
new integration
```

An explicit graph can support a staged approach.

For example:

```text
OldSearchClient
NewSearchClient
      ↓
SearchGateway
```

or:

```text
@Tag(Old.class) SearchClient
@Tag(New.class) SearchClient
```

The application can run both temporarily.

Traffic can be shifted.

Results can be compared.

The old implementation can eventually disappear.

This is a practical form of extensibility: the architecture can represent transition states.

Real systems need those states frequently.

## Explicit Tags Help Multiple Implementations Coexist

Kora's tags provide another mechanism for controlled customization.

Sometimes the application legitimately needs several components of the same base type.

For example:

```text
primary database
analytics database

internal HTTP client
external HTTP client

old provider
new provider
```

A DI system that assumes one global component per type can make such designs awkward.

Tagged dependencies allow the graph to distinguish implementations explicitly.

This is valuable during:

- migrations;
- multi-tenant architecture;
- multi-region integrations;
- specialized clients;
- testing.

The broader lesson is that strong defaults do not require pretending there can only ever be one instance of a concept.

They require the common case to be simple while advanced cases remain representable.

## Compile-Time Extensibility Is Different From Runtime Plugin Loading

Kora is not primarily a runtime plugin platform.

That is an important distinction.

If an application must load unknown plugins dynamically after compilation, a compile-time application graph is not the same tool as a runtime plugin registry.

But most backend service extensibility does not require unknown runtime plugins.

It requires:

- application-specific implementations;
- internal modules;
- alternative clients;
- adapters;
- custom telemetry;
- policy overrides.

Those are known when the application is built.

Compile-time composition is extremely well suited to this class of extension because it keeps the resulting graph validated and explicit.

A framework should not be criticized for lacking dynamic plugin loading when the use case does not require it.

## Extensibility Should Be Evaluated Against Real Change Scenarios

The best way to test a framework's extensibility is not to count SPIs.

Ask concrete questions.

Can we replace the default metrics tag policy?

Can we integrate an internal client?

Can we use another implementation of a contract?

Can we add a component with lifecycle requirements?

Can a custom module depend on built-in telemetry?

Can built-in components depend on our implementation?

Can we test the graph with a replacement component?

Can we avoid pulling modules we do not need?

Can we migrate between two implementations without rewriting business logic?

Can we extract our custom integration into a reusable library?

If the answer is yes through ordinary composition, the framework is meaningfully extensible.

## Strong Defaults and Extensibility Reinforce Each Other

It may seem that opinionated defaults and extensibility pull in opposite directions.

In a well-designed framework they reinforce each other.

Strong defaults create:

```text
consistent codebases
predictable onboarding
simpler documentation
shared conventions
lower cognitive load
```

Extensibility creates:

```text
adaptability
migration paths
organization-specific integrations
escape from unsuitable defaults
long-term viability
```

The best framework architecture combines them:

```text
                 ┌─────────────────────┐
                 │  strong default     │
                 │  one clear path     │
                 └─────────┬───────────┘
                           │
                           ▼
                 ┌─────────────────────┐
                 │ public contract     │
                 │ explicit graph      │
                 └─────────┬───────────┘
                           │
               ┌───────────┴───────────┐
               ▼                       ▼
        default implementation   custom implementation
               │                       │
               └───────────┬───────────┘
                           ▼
                    application graph
```

The default reduces everyday decision cost.

The public contract protects the application from lock-in.

## Why This Matters More as a Framework Ages

A young framework can often make large design changes.

A mature framework accumulates compatibility obligations.

If defaults are deeply embedded in internals, every future change becomes harder.

If defaults sit behind replaceable contracts, the framework has more room to evolve.

Applications can continue using old behavior through a custom implementation.

Organizations can migrate gradually.

Experimental integrations can live outside the framework core until they prove useful.

This creates healthier long-term evolution.

An extensible graph is therefore not only a feature for users.

It is a sustainability mechanism for the framework itself.

## The Real Measure of Extensibility

A useful equation is:

```text
extensibility
≠
number of hooks
```

A better approximation is:

```text
extensibility
≈
how much of the framework can be changed
without leaving the framework's normal model
```

By that measure, Kora has a strong story.

Modules are explicit.

Components are typed.

Custom factories are ordinary.

Defaults can be modeled as replaceable components.

Generated code can satisfy public contracts.

Custom integrations can use the same graph.

The compiler still validates the result.

Tests can replace pieces of the graph.

Lifecycle and telemetry remain available.

The application remains one system.

## Conclusion

A strong default is not lock-in.

Lock-in begins when the default becomes inseparable from the framework's architecture.

An opinionated framework can remain open if the default is simply the recommended implementation of a public contract, if modules are opt-in, if custom components participate in the same dependency
graph, and if applications can replace or extend behavior without crossing into private framework internals.

That is the important distinction in Kora.

Kora deliberately tries to provide one clear path for common backend problems. This reduces decision fatigue, keeps teams aligned, simplifies documentation, and avoids a framework ecosystem where
several competing programming models solve the same problem in subtly different ways.

But "one clear way" does not mean "one implementation forever."

The application graph remains explicit and composable.

Built-in modules enter because the application chooses them.

Custom modules can enter through the same model.

A third-party client can become a normal component.

A default implementation can yield to another implementation of the same contract.

Generated code can remain behind normal interfaces.

Custom components can participate in lifecycle, telemetry, testing, and dependency validation.

The application does not need to fork Kora simply because one requirement differs from the framework's default.

This is why a large catalog of SPIs is not the best measure of extensibility.

A framework can have dozens of extension hooks and still treat extensions as second-class code.

The stronger model is the opposite:

> **A framework is not truly extensible because it has many extension points. It is extensible when custom code participates in the same model as built-in code.**

Kora's architecture is built around that idea.

Its defaults are there to make the common path obvious, not to close the uncommon path.

Its module system is there to let services start small and add only the capabilities they actually need.

Its dependency graph is there to give built-in and custom components the same compositional language.

Its compile-time validation is there to keep customization safe rather than pushing extensions into an unchecked runtime escape hatch.

And its use of public contracts and ordinary Java/Kotlin composition means teams can extend the framework without first becoming experts in framework internals.

The same perspective also gives a more precise answer to the NIH criticism.

The risk of "Not Invented Here" is not merely that a framework provides its own implementation of something that could have been obtained elsewhere. Framework-owned implementations can be useful when
they provide better integration, compile-time validation, observability, performance, or a clearer programming model.

The real risk begins when the framework-owned implementation becomes mandatory, opaque, or difficult to replace.

That is the trap Kora's application model is designed to avoid.

A good default should make the common case easier.

A good extension model should make the uncommon case possible.

A strong framework should do both.

Kora's philosophy can therefore be summarized in one sentence:

> **Use the default when it fits, replace it when it does not, and keep both inside the same explicit, compile-time-validated application graph.**
