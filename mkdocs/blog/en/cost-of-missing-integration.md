---
title: The Cost of the First Missing Integration — Why the Kora Framework Does Not Need a Starter for Everything
date: 2026-09-04
description: How the Kora Framework keeps unsupported-library integration cheap using typed config, module factories, lifecycle, and probes.
search:
  exclude: true
---
# The Cost of the First Missing Integration: Why Kora Does Not Need a Starter for Everything { #cost-of-missing-integration }

**September 4, 2026**

Framework ecosystems are often compared by counting integrations.

One framework has a starter for a particular database, another has an official module for a cloud queue, another has a wrapper around a vendor SDK, and another has several competing abstractions for
the same category of technology. The resulting comparison looks objective because the numbers are easy to collect: more modules, more starters, more supported products, larger ecosystem.

That metric is useful, but it is incomplete.

A framework is not weak because it lacks a prebuilt starter for every niche Java library. The more important question is what happens when the first missing integration appears. If connecting an
unsupported library requires internal framework knowledge, undocumented extension points, reflection tricks, custom bootstrap phases, or a second container hidden inside the first one, then the
missing starter is genuinely expensive. If the integration is simply a normal Java or Kotlin client that can be configured, constructed, placed into the application graph, observed, health-checked,
and shut down using ordinary framework primitives, then the absence of a dedicated starter is much less significant.

This is where the Kora Framework has an interesting ecosystem story.

Kora does provide first-class modules for the technologies that appear repeatedly in production backend services: HTTP servers and clients, OpenAPI, JDBC, Cassandra, Kafka, gRPC, configuration,
caching, resilience, scheduling, validation, telemetry, probes, and other infrastructure. But its design does not depend on the idea that every technology in the JVM ecosystem must first be translated
into a Kora-specific DSL before an application can use it.

Instead, the extension path is deliberately small.

```text
Need technology X
      ↓
Use its native Java/Kotlin client
      ↓
Add typed configuration
      ↓
Expose the client through @Module
      ↓
Wire lifecycle / telemetry / probes if required
      ↓
Inject and use it normally
```

That flow matters because it changes what an ecosystem means.

An ecosystem is not only the set of integrations published by the framework maintainers. It is also the cost of making the next integration yourself.

A framework with five hundred integrations but an expensive extension model can still create serious friction when application requirements leave the catalog. A framework with a smaller but
well-targeted built-in surface can be more flexible if unsupported technologies fit naturally into the same application model as built-in ones.

The useful metric, therefore, is not simply:

```text
How many starters exist?
```

It is:

```text
How expensive is the first starter that does not exist?
```

For Kora, that question leads directly into its broader philosophy: it is not trying to become a framework-specific universe around every technology a backend engineer might use. It is trying to make
the common production path first-class while keeping the path to an uncommon technology short, explicit, and ordinary.

## The Hidden Cost Behind a Huge Starter Catalog { #hidden-cost }

A large integration catalog is a real advantage. It would be wrong to pretend otherwise.

A mature starter can save hours or days of engineering. It can encode correct defaults, integrate with configuration, attach metrics and tracing, expose health signals, coordinate lifecycle, translate
exceptions, support testing, and handle subtle vendor behavior that application teams should not have to rediscover.

For common and difficult technologies, that is extremely valuable.

But integration count is not a free variable. Every framework-specific integration introduces another layer that somebody has to design, document, version, test, release, and eventually migrate.

A typical starter-heavy path looks something like this:

```text
Library
   ↓
Framework starter
   ↓
Framework abstraction
   ↓
Framework configuration model
   ↓
Application
```

Each arrow can be useful. Each arrow can also create semantic distance from the underlying technology.

Suppose a Java library already has a good client API:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var client = VendorClient.builder()
        .endpoint(endpoint)
        .credentials(credentials)
        .timeout(timeout)
        .build();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val client = VendorClient.builder()
        .endpoint(endpoint)
        .credentials(credentials)
        .timeout(timeout)
        .build()
    ```

Now imagine a framework decides that applications should never see this API directly. It introduces:

- its own properties hierarchy;
- an auto-configuration class;
- a framework wrapper interface;
- a framework-specific exception model;
- a framework-specific lifecycle adapter;
- a separate observability customization API;
- conditional activation rules;
- version compatibility logic;
- test fixtures;
- perhaps a second DSL for advanced options.

The application may become easier for the happy path, but the total system becomes larger.

The developer now has to understand both the underlying technology and the framework's interpretation of it.

When something unusual happens, the debugging path can become:

```text
application configuration
        ↓
framework binding
        ↓
starter conditions
        ↓
framework adapter
        ↓
framework wrapper
        ↓
vendor client
        ↓
actual network behavior
```

That is not inherently bad. For technologies with difficult configuration or dangerous defaults, the wrapper may provide enormous value. The problem appears when this becomes the default philosophy
for everything.

At sufficient scale, a framework ecosystem can become a framework inside the framework: hundreds of adapters, overlapping conventions, compatibility tables, lifecycle rules, and configuration dialects
that exist mainly because the framework has decided to mediate every relationship between application code and external libraries.

Kora takes a more selective approach.

## Kora Does Not Need to Own the Library to Use It { #own-the-library }

One of the most important properties of Kora's dependency-injection model is that a component does not have to be implemented by Kora.

It just has to become a component in the graph.

That distinction sounds obvious, but it is architecturally important.

Suppose an application needs an SDK for a product Kora has never heard of. Perhaps it is a search appliance, a proprietary rules engine, a new vector store, an internal company SDK, a niche message
broker, or a vendor-specific API client.

If the library already has a normal Java client, the integration can begin with that client.

The Kora-specific part is simply the boundary between construction and use.

For example:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface SearchVendorModule {

        default SearchVendorClient searchVendorClient(SearchVendorConfig config) {
            return SearchVendorClient.builder()
                .endpoint(config.endpoint())
                .apiKey(config.apiKey())
                .timeout(config.timeout())
                .build();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface SearchVendorModule {

        fun searchVendorClient(config: SearchVendorConfig): SearchVendorClient {
            return SearchVendorClient.builder()
                .endpoint(config.endpoint())
                .apiKey(config.apiKey())
                .timeout(config.timeout())
                .build()
        }
    }
    ```

From the perspective of the rest of the application, `SearchVendorClient` is now a normal graph dependency.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class ProductSearchService {

        private final SearchVendorClient client;

        public ProductSearchService(SearchVendorClient client) {
            this.client = client;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ProductSearchService(private val client: SearchVendorClient)
    ```

There is no requirement to invent `KoraSearchVendorClient`, no requirement to wrap every client method, and no need for application code to retrieve the client from some generic registry.

The integration boundary is a factory method.

That gives us the simpler topology:

```text
Library
   ↓
small integration module
   ↓
Application
```

The important word is **small**.

A custom module may eventually become sophisticated, but it can begin with almost no framework ceremony. The integration only needs to add the concerns that the application actually requires.

## `@Module` Is the Essential Extension Mechanism { #module-extension }

In Kora, an `@Module` is an interface containing component factory methods. Those factory methods can depend on other graph components and return new components to the container.

This is enough to adapt a very large portion of the Java ecosystem.

A module can take:

```text
typed configuration
credentials
HTTP client
serializer
telemetry objects
executors
other application services
```

and return:

```text
vendor client
connection pool
SDK service object
registry
adapter
listener
worker
```

The mechanism is intentionally close to ordinary construction.

A module is not a plugin runtime. It is not a service locator. It is not a metadata language.

It is essentially a typed declaration of:

```text
Given these graph dependencies,
construct this component.
```

For example:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface AcmeModule {

        default AcmeClient acmeClient(
            AcmeConfig config,
            Credentials credentials) {

            return AcmeClient.builder()
                .url(config.url())
                .credentials(credentials)
                .build();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface AcmeModule {

        fun acmeClient(
            config: AcmeConfig,
            credentials: Credentials): AcmeClient {

            return AcmeClient.builder()
                .url(config.url())
                .credentials(credentials)
                .build()
        }
    }
    ```

The graph can validate those dependencies at compile time. If `AcmeConfig` or `Credentials` cannot be provided, the application does not wait until startup to discover that the integration is
incomplete.

This makes custom integration structurally similar to built-in integration.

That is important because extension mechanisms often fail when framework authors provide a clean model for official modules but a completely different escape hatch for user-defined ones. The official
ecosystem is elegant; custom code lives in factories, registries, bootstrap hooks, or manual singleton holders.

Kora's model does not require that split.

The same graph that holds framework components can hold an arbitrary third-party client.

## Configuration Is Not a Separate Side Channel { #configuration }

A third-party integration needs configuration, but that does not require inventing a new configuration system.

Kora can map a configuration section into a typed interface using `@ConfigSource`.

For example:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @ConfigSource("clients.acme")
    public interface AcmeConfig {

        String endpoint();

        String apiKey();

        Duration timeout();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @ConfigSource("clients.acme")
    interface AcmeConfig {

        fun endpoint(): String

        fun apiKey(): String

        fun timeout(): Duration
    }
    ```

Now the configuration object itself is part of the graph.

The factory becomes:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface AcmeModule {

        default AcmeClient acmeClient(AcmeConfig config) {
            return AcmeClient.builder()
                .endpoint(config.endpoint())
                .apiKey(config.apiKey())
                .timeout(config.timeout())
                .build();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface AcmeModule {

        fun acmeClient(config: AcmeConfig): AcmeClient {
            return AcmeClient.builder()
                .endpoint(config.endpoint())
                .apiKey(config.apiKey())
                .timeout(config.timeout())
                .build()
        }
    }
    ```

This has several useful properties.

The integration configuration is explicit.

The client constructor is explicit.

The relationship between configuration and client is explicit.

The application does not need a framework-specific translation layer that converts Kora configuration into another abstraction and then finally into the native client.

The path is simply:

```text
application.conf
      ↓
AcmeConfig
      ↓
AcmeClient.builder(...)
      ↓
AcmeClient
```

The vendor documentation remains useful because the final construction still uses the vendor's own concepts.

If the vendor documentation says:

> set request timeout to five seconds

the application developer does not first need to discover what a framework wrapper renamed that property to.

Thin integration keeps the semantic gap small.

## Why Native Documentation Remaining Applicable Is a Major Advantage { #native-documentation }

One of the hidden costs of deep framework wrappers is documentation substitution.

If the framework owns an abstraction, developers can no longer rely exclusively on the upstream library documentation. They need to understand which parts the framework exposes, which it changes,
which it configures automatically, and which version of the underlying library the framework module currently supports.

The real documentation stack becomes:

```text
vendor documentation
        +
framework integration documentation
        +
framework configuration documentation
        +
compatibility notes
        +
possibly migration notes
```

Sometimes that complexity is justified.

But when the upstream Java API is already good, an adapter can preserve most of the original mental model.

For a thin Kora integration:

```text
How do I configure compression?
        ↓
Read vendor documentation.

How do I create the client?
        ↓
Use vendor builder API.

How do I put it in Kora DI?
        ↓
One @Module factory.

How do I close it?
        ↓
Use lifecycle / AutoCloseable integration.

How do I expose readiness?
        ↓
Add a probe component if useful.
```

The integration-specific knowledge is small and local.

This creates a valuable organizational property: teams can hire or move developers based on Java ecosystem knowledge rather than framework-specific adapter knowledge.

A developer who already understands the native client is most of the way to understanding the Kora integration.

## Lifecycle Is Explicit Instead of Hidden in a Starter { #lifecycle }

Construction is only part of production integration.

Many clients own resources:

- connection pools;
- event loops;
- file handles;
- worker threads;
- background refreshers;
- persistent channels.

They need to be started and, more importantly, released correctly during shutdown.

Kora's graph has a lifecycle model for exactly this.

If a third-party component itself implements `AutoCloseable`, Kora's container can close it when the component is released. If more explicit initialization and release behavior is required, the
integration can use Kora's `Lifecycle` model or wrap a value with `LifecycleWrapper`.

Conceptually:

```text
create client
    ↓
initialize if needed
    ↓
application uses client
    ↓
graceful shutdown begins
    ↓
release / close client
```

For example, an integration might look like:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface VendorModule {

        default Wrapped<VendorClient> vendorClient(VendorConfig config) {
            var client = new VendorClient(config.endpoint());

            return new LifecycleWrapper<>(
                client,
                VendorClient::start,
                VendorClient::stop
            );
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface VendorModule {

        fun vendorClient(config: VendorConfig): Wrapped<VendorClient> {
            val client = VendorClient(config.endpoint())

            return LifecycleWrapper(
                client,
                VendorClient::start,
                VendorClient::stop
            )
        }
    }
    ```

The rest of the application still injects `VendorClient`.

The lifecycle adapter remains at the boundary where it belongs.

This is an important contrast with a starter-heavy ecosystem, where lifecycle behavior may be implicit inside auto-configuration. Implicit lifecycle is convenient until an application needs to
understand startup order, graceful shutdown, or why a resource remains alive.

Kora's approach encourages the integration author to make ownership visible.

## Telemetry Can Be Added Without Replacing the Client { #telemetry }

Observability is another reason official integrations can be valuable.

A production client should ideally provide useful metrics, tracing, and logging. An official framework module can standardize those concerns across applications.

But a missing official integration does not automatically require a complete client wrapper.

There are several ways to instrument a native library while keeping it native.

If the library already supports OpenTelemetry, Micrometer, interceptors, listeners, request filters, event hooks, or metrics callbacks, the integration module can connect those directly during client
construction.

Conceptually:

```text
Kora telemetry components
          ↓
native library hooks
          ↓
native client
```

For example:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface VendorModule {

        default VendorClient vendorClient(
            VendorConfig config,
            OpenTelemetry openTelemetry,
            MeterRegistry meterRegistry) {

            return VendorClient.builder()
                .endpoint(config.endpoint())
                .tracer(openTelemetry.getTracer("vendor-client"))
                .metrics(meterRegistry)
                .build();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface VendorModule {

        fun vendorClient(
            config: VendorConfig,
            openTelemetry: OpenTelemetry,
            meterRegistry: MeterRegistry): VendorClient {

            return VendorClient.builder()
                .endpoint(config.endpoint())
                .tracer(openTelemetry.getTracer("vendor-client"))
                .metrics(meterRegistry)
                .build()
        }
    }
    ```

If the vendor API has no useful hooks, then an adapter or decorator may be justified.

The important architectural principle is that instrumentation should be added at the narrowest useful boundary. The framework does not need to replace the entire client API just to record latency.

This is part of what thin abstractions mean in practice: add framework integration where there is actual framework value, not everywhere simply because a technology entered the application.

## Health and Readiness Are Ordinary Graph Components { #health-readiness }

Operational integration often needs more than telemetry.

A service may need to report that a component is ready, alive, initialized, or temporarily unavailable. Kora's probe model allows readiness and liveness checks to be ordinary components.

That means an unsupported vendor client can participate in the same operational model as built-in infrastructure.

For example:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class VendorReadinessProbe implements ReadinessProbe {

        private final VendorClient client;

        public VendorReadinessProbe(VendorClient client) {
            this.client = client;
        }

        @Override
        public ReadinessProbeFailure probe() {
            if (client.isReady()) {
                return null;
            }

            return new ReadinessProbeFailure("Vendor client is not ready");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class VendorReadinessProbe(private val client: VendorClient) : ReadinessProbe {

        override fun probe(): ReadinessProbeFailure? {
            if (client.isReady) {
                return null
            }

            return ReadinessProbeFailure("Vendor client is not ready")
        }
    }
    ```

Kora aggregates registered readiness probes.

The integration does not need a special "starter contract" to become visible to Kubernetes or to a deployment smoke test. It only needs to provide a component using the same operational contract as
the rest of the application.

Again, the extension surface remains small:

```text
native client
   +
Kora ReadinessProbe
   =
production-aware integration
```

This is the recurring pattern throughout Kora's model.

A third-party library does not need to be transformed into a Kora-specific universe. It needs a few explicit bridges into the application graph.

## An Integration Can Grow in Layers { #integration-layers }

One useful way to understand this approach is to imagine an integration maturing over time.

At first, the application only needs the client.

### Stage 1: Construction { #stage-1 }

```text
configuration
     ↓
@Module
     ↓
native client
```

Then the application goes to production and needs graceful shutdown.

### Stage 2: Lifecycle { #stage-2 }

```text
configuration
     ↓
@Module
     ↓
native client
     ↓
Lifecycle / AutoCloseable
```

Then operations wants metrics and traces.

### Stage 3: Observability { #stage-3 }

```text
configuration
     ↓
@Module
     ↓
telemetry hooks
     ↓
native client
```

Then the deployment platform needs readiness.

### Stage 4: Operational Integration { #stage-4 }

```text
configuration
     ↓
@Module
     ↓
native client
  ↙       ↘
telemetry  readiness probe
```

Then three other services need the same integration.

### Stage 5: Reusable Module { #stage-5 }

```text
company-vendor-kora-module
        ↓
service A
service B
service C
service D
```

Nothing requires the integration to begin at Stage 5.

This matters because large framework ecosystems often encourage teams to think in all-or-nothing terms: either an official starter exists, or somebody has to build something starter-sized before the
technology feels properly supported.

Kora allows a much more incremental path.

Build only the integration surface the application actually needs.

## From Local Adapter to Reusable Ecosystem Module { #reusable-module }

If a custom integration becomes broadly useful, it can be extracted into its own module.

That can be an internal company library:

```text
platform/
└── kora-vendor-client/
```

or an open-source integration.

The module can expose a normal Kora module interface that applications explicitly connect.

For example:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface VendorClientModule {

        default VendorClient vendorClient(
            VendorConfig config,
            VendorTelemetry telemetry) {
            // ...
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface VendorClientModule {

        fun vendorClient(
            config: VendorConfig,
            telemetry: VendorTelemetry): VendorClient {
            // ...
        }
    }
    ```

The application then adds the dependency and connects the module to its application graph.

This creates a different model of ecosystem growth.

Instead of requiring every integration to be blessed and implemented centrally by the framework team, integration knowledge can move outward:

```text
one service
    ↓
local module
    ↓
shared internal module
    ↓
community/open-source module
```

The important property is that the application model does not change as the integration matures.

The local factory and the reusable module use the same DI concepts.

There is no migration from "manual integration mode" to "framework integration mode."

That continuity lowers the cost of experimentation.

## The Right Comparison Is the Cost of the First Missing Integration { #right-comparison }

Imagine two frameworks.

Framework A has 400 official integrations.

Framework B has 80.

It is tempting to conclude immediately that Framework A has the stronger ecosystem.

But suppose an application needs integration number 401.

In Framework A, the missing technology requires:

```text
custom bootstrap hook
custom property binder
runtime bean registry access
wrapper abstraction
manual lifecycle registration
custom health contributor
framework-specific tracing bridge
```

In Framework B, the missing technology requires:

```text
native client dependency
typed config
one module factory
optional lifecycle wrapper
optional probe
```

Which ecosystem is stronger for this application?

The answer is no longer obvious.

A better ecosystem metric could be written as:

```text
Ecosystem strength
≈
coverage of common needs
+
quality of built-in integrations
+
cost of unsupported integration
+
transparency of extension model
+
reuse potential
```

Integration count measures only the first term.

Kora's strategy is particularly interesting because it tries to keep the unsupported-integration cost low.

That does not eliminate the advantage of having an official module. It changes how damaging the absence of one is.

## Not Every Library Deserves a Framework Abstraction { #not-every-library }

There is a tendency in framework design to assume that integration equals abstraction.

That is not always true.

Sometimes the best integration is simply construction plus lifecycle.

Consider a hypothetical image-processing library:

===! ":fontawesome-brands-java: `Java`"

    ```java
    ImageProcessor processor = ImageProcessor.builder()
        .threads(4)
        .quality(HIGH)
        .build();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val processor = ImageProcessor.builder()
        .threads(4)
        .quality(HIGH)
        .build()
    ```

What would a framework wrapper add?

If the answer is mostly:

```text
rename builder methods
move configuration keys
wrap exceptions
expose the same operations under new names
```

then the abstraction may not be creating meaningful value.

It may only create a second vocabulary.

A useful framework abstraction should usually add something substantial:

- compile-time validation;
- generated code;
- unified telemetry semantics;
- transactional behavior;
- retry or resilience semantics;
- lifecycle coordination;
- protocol integration;
- consistent mapping;
- major reduction in repetitive boilerplate;
- a safer or simpler domain model.

If it does not, using the native library directly can be the cleaner architecture.

This distinction helps explain why Kora's philosophy of thin abstractions matters. The framework should intervene where it can make the system materially better, not simply because it can place
another interface in front of a library.

## Why Fewer Wrappers Can Mean Less Semantic Drift { #semantic-drift }

Every wrapper creates the possibility that the abstraction and the underlying technology evolve at different speeds.

A vendor releases version 7.

It adds:

- a new authentication mode;
- a new retry policy;
- a new compression algorithm;
- a new async transport;
- a new routing option.

If an application uses the native client, those capabilities are available when the client dependency is upgraded.

If the application uses a framework abstraction, the framework integration may need to expose each capability deliberately.

The version path becomes:

```text
vendor releases feature
        ↓
framework updates dependency
        ↓
framework updates abstraction
        ↓
framework updates configuration
        ↓
framework releases integration
        ↓
application upgrades framework module
```

Again, this delay can be worthwhile when the framework provides substantial additional value. But it is still a cost.

Thin integration reduces that compatibility surface.

If the Kora module mostly constructs the native client, the application can often move with the native client API much more directly.

That can be particularly valuable for vendor SDKs and fast-moving infrastructure libraries.

## Built-In Modules Still Matter { #built-in-modules }

It would be easy to take the previous argument too far.

If custom integration is easy, why should a framework ship any integrations at all?

Because repeated infrastructure problems deserve shared solutions.

A good official module can encode years of operational experience. It can make telemetry consistent across hundreds of services. It can ensure graceful shutdown works correctly. It can generate
repetitive code. It can provide compile-time validation. It can standardize error handling and make testing easier.

Kora itself clearly follows this principle in its core production surface.

Its built-in stack covers the categories that appear again and again in backend systems:

```text
HTTP
Data Access
Messaging
Configuration
Resilience
Telemetry
Integrations
```

The point is not "starters are bad."

The point is:

> **A framework should spend its abstraction budget where the abstraction provides durable value.**

This leads naturally to a more nuanced distinction between integrations that benefit strongly from first-class framework support and integrations where a thin local adapter is perfectly adequate.

## Where a Ready-Made Module Is Especially Valuable { #ready-made-module }

There are categories where "just use the native client" can underestimate the complexity.

### Security { #security }

Security integration is rarely only object construction.

Authentication and authorization often interact with:

- HTTP routing;
- request context;
- identities;
- role mapping;
- token validation;
- key rotation;
- error responses;
- propagation;
- tracing;
- testing;
- policy evaluation.

A well-designed framework security module can prevent subtle and dangerous inconsistencies.

This is a strong case for first-class support.

### Distributed Configuration { #distributed-configuration }

A distributed configuration client may look simple at first, but production behavior can involve:

- bootstrap ordering;
- watch semantics;
- reconnection;
- versioning;
- dynamic refresh;
- consistency;
- graph updates;
- failure policy.

An official integration can coordinate these concerns with the framework's own configuration and component lifecycle.

### Service Discovery { #service-discovery }

Service discovery is not merely a client.

It affects:

- endpoint resolution;
- load balancing;
- connection reuse;
- health state;
- retries;
- topology refresh;
- DNS or registry semantics;
- client configuration.

A mature framework integration can provide real value by making these layers coherent.

### Distributed Tracing Semantics { #distributed-tracing }

Adding a span is easy.

Getting trace propagation, parent/child relationships, semantic attributes, error recording, sampling behavior, and context boundaries right across an entire technology is harder.

An official telemetry integration can provide consistency that a small application adapter may miss.

### Vendor SDKs with Complex Runtime Behavior { #vendor-sdks }

Some vendor SDKs hide:

- background thread pools;
- connection multiplexing;
- refresh workers;
- credential rotation;
- internal retries;
- topology polling;
- shutdown constraints.

A well-maintained integration module can encode correct production lifecycle.

These cases reinforce rather than contradict Kora's model.

The framework should have strong modules where the integration problem is genuinely cross-cutting or operationally subtle.

It simply does not follow that every usable Java library needs a Kora-specific wrapper before it belongs in a Kora application.

## Not a Framework for Everything — the Right Framework for Production Backends { #not-a-framework-for-everything }

This extension model reveals something larger about Kora's positioning.

Kora does not appear to be trying to win by maximizing the number of boxes it can check in an ecosystem spreadsheet.

Its philosophy is closer to:

> **Not a tool for every possible situation. An excellent tool for a clearly defined class of problems.**

That class is production JVM backend services.

The framework focuses its strongest first-class abstractions around the path that a large proportion of such services repeatedly need.

```text
HTTP
 ↓
application logic
 ↓
data access / messaging / RPC
 ↓
resilience
 ↓
telemetry
 ↓
production lifecycle
```

This is narrower than "everything developers might ever build with Java."

That narrowness can be a strength.

## What a Production Backend Usually Needs { #production-backend }

A typical service needs some combination of:

- an HTTP server;
- an HTTP client;
- OpenAPI;
- JDBC or another database client;
- repositories and mappings;
- Kafka or another messaging system;
- gRPC;
- configuration;
- validation;
- resilience;
- caching;
- scheduling;
- logging;
- metrics;
- tracing;
- readiness and liveness;
- graceful shutdown;
- testing support.

Kora puts first-class effort into these categories.

The framework home page groups its focus similarly: HTTP, data access, messaging, configuration, resilience, telemetry, and integrations. Its module documentation covers concrete infrastructure such
as Kafka, gRPC, S3, JDBC, Cassandra, scheduling, cache, and observability.

It would be tempting to summarize this with a claim such as:

> Kora covers 90 percent of typical enterprise backend integration needs.

That may even be directionally reasonable for many organizations, but it is not a useful engineering statement without a defined workload sample.

What is "typical"?

What counts as an integration?

Which industries?

Which deployment environments?

Which databases?

Which cloud platforms?

Instead of relying on an arbitrary percentage, a stronger argument is observable:

> Kora deliberately covers the categories that recur across production backend services and leaves uncommon technology choices accessible through the same graph model.

That claim can be inspected directly.

## Focus Is Different from Incompleteness { #focus }

There is an important difference between a framework being incomplete and a framework being focused.

An incomplete framework says:

```text
We do not support X,
and there is no clean way to add X.
```

A focused framework says:

```text
X is not part of our built-in surface,
but the application model lets you integrate it directly.
```

Those are very different situations.

Kora's explicit module system, component factories, configuration mapping, lifecycle model, probes, and graph composition make the second model plausible.

The framework does not have to own technology X.

It has to provide enough integration surface for technology X to become a well-behaved participant in the application.

This is why the phrase "small ecosystem" can be misleading.

A framework can have a smaller **catalog** without having a small **reachable ecosystem**.

If virtually any ordinary JVM library can be made a graph component with a few lines of factory code, then the practical ecosystem includes much of the Java ecosystem itself.

The important question is how much impedance exists at the boundary.

## The Java Ecosystem Is Already an Ecosystem { #java-ecosystem }

Java frameworks do not exist in a vacuum.

The JVM already has mature libraries for almost every infrastructure category imaginable.

There are native clients and SDKs for:

- databases;
- caches;
- queues;
- cloud services;
- observability systems;
- feature flags;
- search engines;
- payment providers;
- secret stores;
- identity providers;
- object stores;
- workflow systems;
- AI services;
- internal company platforms.

A framework can respond to this ecosystem in two broad ways.

### Model A: Framework Mediation { #model-a }

```text
Java ecosystem
      ↓
framework-specific adapters
      ↓
framework-specific abstractions
      ↓
application
```

The advantage is uniformity.

The cost is another abstraction and compatibility layer.

### Model B: Framework Composition { #model-b }

```text
Java ecosystem
      ↓
explicit composition into application graph
      ↓
application
```

The advantage is proximity to the native technology.

The cost is that the application or platform team sometimes has to write the small integration layer itself.

Kora leans strongly toward composition when a first-class abstraction is not justified.

That is a sensible position for a framework that emphasizes transparency.

## One Application Model for Built-In and Custom Components { #one-application-model }

A particularly important property is that custom integrations do not need to live outside the normal Kora model.

Imagine a service with:

```text
Kora HTTP server
Kora JDBC repository
Kora Kafka consumer
custom FeatureFlagClient
custom PaymentRiskClient
custom InternalSearchClient
```

A badly designed framework extension model would make this architecture look like two systems:

```text
framework world
├── HTTP
├── JDBC
└── Kafka

manual world
├── feature flags
├── risk
└── search
```

Kora can instead represent them in one graph:

```text
Application Graph
├── HTTP server
├── repositories
├── Kafka consumers
├── FeatureFlagClient
├── PaymentRiskClient
├── InternalSearchClient
├── telemetry
├── probes
└── lifecycle
```

The difference matters operationally.

The custom clients can participate in dependency ordering.

They can participate in lifecycle.

They can consume typed configuration.

They can be dependencies of other components.

They can expose probes.

They can be decorated or instrumented.

They can be replaced in tests.

They are not second-class merely because Kora did not publish them.

## A Framework Should Not Replace Middleware { #middleware }

Another useful boundary in Kora's philosophy is the distinction between framework and infrastructure.

A framework should help an application use Kafka.

It should not try to become Kafka.

It should help an application use a database.

It should not invent an entirely new database semantics unless the abstraction earns its complexity.

It should help an application call an HTTP service.

It does not need to replace the concepts of HTTP with a proprietary networking model.

This seems obvious, but frameworks can gradually accumulate enough abstraction that underlying technologies become implementation details developers are discouraged from understanding.

That can make simple use cases elegant while making unusual behavior difficult to debug.

Kora's thin-abstraction philosophy keeps the underlying technology visible.

JDBC remains recognizably JDBC.

Kafka remains recognizably Kafka.

gRPC remains recognizably gRPC.

A custom library can remain recognizably itself.

This reduces semantic distance between production behavior and the code developers inspect.

## Fewer Programming Models Reduce Integration Surface { #fewer-programming-models }

Breadth is also expensive when a framework supports several competing ways to solve the same class of problem.

For example, a framework might support:

```text
blocking HTTP
reactive HTTP
coroutine HTTP

JDBC
reactive SQL
ORM
reactive ORM

several DI styles
several configuration styles
several client abstractions
```

Every additional programming model multiplies integration obligations.

A database integration may need blocking and reactive variants.

Telemetry needs to propagate across all execution models.

Security needs adapters for each model.

Transactions may behave differently.

Testing support expands.

Documentation branches.

AOP semantics branch.

Kora 2 deliberately narrows this surface by using ordinary synchronous Java and Kotlin signatures on virtual threads rather than maintaining parallel reactive and suspend contracts across modules.

That choice is relevant to ecosystem size.

A focused programming model means new integrations have fewer framework dimensions to support.

A custom client does not need:

```text
blocking adapter
reactive adapter
coroutine adapter
context bridge between all three
```

It can often just be a normal synchronous component.

Reducing the number of programming models is therefore not only a readability decision. It reduces the combinatorial cost of ecosystem growth.

## The Swiss Army Knife Trade-Off { #swiss-army-knife }

The classic metaphor is useful.

A Swiss Army knife wins because it contains many tools.

If you need a blade, screwdriver, bottle opener, scissors, file, corkscrew, tweezers, and saw, it is convenient to have all of them in one object.

But the metaphor has another side.

Each built-in tool has to fit the physical constraints of the knife. A specialized screwdriver may be better for serious screwdriving. A dedicated saw is better for serious cutting. The advantage of
the knife is availability and breadth, not necessarily the optimum design for every task.

Framework ecosystems have a similar tension.

A breadth-first framework tends toward:

```text
more integrations
more wrappers
more configuration models
more compatibility surface
more overlapping paths
```

A focus-first framework can instead aim for:

```text
common production needs
        ↓
carefully designed first-class modules
        ↓
thin abstractions
        ↓
simple custom integrations
```

This does not prove the focused framework is always better.

It clarifies the trade.

Kora is making a particular bet: backend teams gain more from an optimized, coherent core plus cheap extensibility than from attempting to wrap every possible technology.

## The Abstraction Budget { #abstraction-budget }

A useful way to discuss this design is with the idea of an **abstraction budget**.

Every abstraction costs something:

```text
concepts to learn
documentation to maintain
compatibility to preserve
bugs to fix
versions to coordinate
behavior to debug
migration paths to support
```

A framework should spend that budget where it provides enough return.

For example, generated repositories can justify an abstraction because they eliminate repetitive mapping and query plumbing while retaining explicit SQL.

Declarative HTTP clients can justify an abstraction because the framework can generate request construction, mapping, telemetry, and error handling.

Resilience annotations can justify an abstraction because retry, timeout, circuit breaker, and fallback policies are cross-cutting concerns that benefit from a consistent model.

A one-to-one wrapper around a perfectly usable vendor client may not justify the same cost.

The result is a framework whose surface grows according to leverage rather than according to catalog completeness.

That is a more disciplined ecosystem strategy.

## The Test of a Good Custom Integration { #test-of-integration }

How do we know whether the custom integration path is genuinely good?

A useful test is whether a developer can explain the entire integration on one screen.

For a normal client, the answer should often be close to:

```text
1. Add dependency.
2. Define typed config.
3. Construct client in @Module.
4. Add lifecycle behavior if client owns resources.
5. Attach telemetry through native hooks.
6. Add readiness/liveness only if operationally meaningful.
7. Inject client.
```

If that is enough, the missing starter is not a major framework deficiency.

If the process instead requires learning internal compiler APIs, container mutation, reflective registration, undocumented ordering rules, or private framework classes, then the ecosystem really is
harder to extend than its catalog suggests.

The distinction is practical and measurable.

## A Concrete Example: Integrating an Unsupported Client { #concrete-example }

Imagine Kora has no official integration for a hypothetical `NimbusClient`.

The native Java API is:

===! ":fontawesome-brands-java: `Java`"

    ```java
    NimbusClient.builder()
        .endpoint(...)
        .token(...)
        .connectTimeout(...)
        .build();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    NimbusClient.builder()
        .endpoint(...)
        .token(...)
        .connectTimeout(...)
        .build()
    ```

A small Kora integration can start with typed configuration:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @ConfigSource("clients.nimbus")
    public interface NimbusConfig {

        String endpoint();

        String token();

        Duration connectTimeout();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @ConfigSource("clients.nimbus")
    interface NimbusConfig {

        fun endpoint(): String

        fun token(): String

        fun connectTimeout(): Duration
    }
    ```

Then construction:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface NimbusModule {

        default NimbusClient nimbusClient(NimbusConfig config) {
            return NimbusClient.builder()
                .endpoint(config.endpoint())
                .token(config.token())
                .connectTimeout(config.connectTimeout())
                .build();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface NimbusModule {

        fun nimbusClient(config: NimbusConfig): NimbusClient {
            return NimbusClient.builder()
                .endpoint(config.endpoint())
                .token(config.token())
                .connectTimeout(config.connectTimeout())
                .build()
        }
    }
    ```

Now application code uses it:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class RecommendationService {

        private final NimbusClient nimbus;

        public RecommendationService(NimbusClient nimbus) {
            this.nimbus = nimbus;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class RecommendationService(private val nimbus: NimbusClient)
    ```

If the client is `AutoCloseable`, normal graph release can close it.

If it needs explicit startup:

===! ":fontawesome-brands-java: `Java`"

    ```java
    default Wrapped<NimbusClient> nimbusClient(NimbusConfig config) {
        var client = createNimbus(config);

        return new LifecycleWrapper<>(
            client,
            NimbusClient::start,
            NimbusClient::stop
        );
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun nimbusClient(config: NimbusConfig): Wrapped<NimbusClient> {
        val client = createNimbus(config)

        return LifecycleWrapper(
            client,
            NimbusClient::start,
            NimbusClient::stop
        )
    }
    ```

If readiness matters:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class NimbusReadinessProbe implements ReadinessProbe {

        private final NimbusClient client;

        public NimbusReadinessProbe(NimbusClient client) {
            this.client = client;
        }

        @Override
        public ReadinessProbeFailure probe() {
            return client.ready()
                ? null
                : new ReadinessProbeFailure("Nimbus is not ready");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class NimbusReadinessProbe(private val client: NimbusClient) : ReadinessProbe {

        override fun probe(): ReadinessProbeFailure? {
            return if (client.ready()) {
                null
            } else {
                ReadinessProbeFailure("Nimbus is not ready")
            }
        }
    }
    ```

If tracing matters, use Nimbus's native interceptor or request hook when creating the client.

That is already a production-quality integration pattern.

No starter was required.

## What Should Become a Shared Module? { #shared-module }

Not every local integration should be published.

A useful rule is to extract it when the integration contains knowledge rather than merely wiring.

For example, a module is a good reuse candidate when it standardizes:

- required timeouts;
- authentication;
- retries;
- tracing semantics;
- metrics;
- connection pooling;
- graceful shutdown;
- readiness rules;
- configuration schema;
- company-wide defaults;
- test fixtures.

At that point, the integration is no longer just:

```text
new Client(config)
```

It contains operational policy.

That policy deserves one implementation.

The module can then be consumed by every service that needs the technology.

This is how an ecosystem grows organically from production experience rather than from speculative wrappers.

## Internal Ecosystems Matter Too { #internal-ecosystems }

Public Maven artifacts are only one kind of ecosystem.

Large companies often have more relevant internal integrations than public ones.

They may have internal libraries for:

- identity;
- service discovery;
- secrets;
- feature flags;
- internal RPC;
- audit logging;
- compliance;
- deployment metadata;
- company-specific telemetry.

A framework whose custom module model is simple makes it easier to build an internal platform ecosystem.

The organization can create:

```text
company-kora-security
company-kora-telemetry
company-kora-feature-flags
company-kora-service-discovery
company-kora-audit
```

These modules can remain thin and specific to the organization's needs.

The framework does not need to anticipate every company-specific infrastructure system.

It only needs an application model that those integrations can join cleanly.

This may be more important in enterprise environments than the raw count of public starters.

## Explicit Integration Also Improves Ownership { #ownership }

There is another subtle advantage to local modules: ownership is obvious.

Suppose an application includes:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface FraudProviderModule { ...
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface FraudProviderModule { ...
    }
    ```

A developer can find:

- how the client is created;
- which configuration it uses;
- which telemetry is attached;
- how it shuts down;
- which probe represents readiness.

The operational contract of the dependency is located in one place.

In a highly automated starter model, that behavior may be distributed across:

- a dependency;
- auto-configuration;
- environment properties;
- conditional beans;
- transitive configuration;
- hidden defaults;
- framework-specific instrumentation.

Automation is convenient, but explicit local ownership can make unusual production failures easier to reason about.

Kora's broader emphasis on generated and inspectable code fits naturally with this integration style.

## The Framework Should Make the Escape Hatch Better Than the Happy Path in Other Frameworks { #escape-hatch }

A mature framework is not judged only by its ideal path.

Real systems eventually need something unusual.

A proprietary SDK.

An old client library.

An internal protocol.

A library released last month.

A vendor whose official framework adapter lags behind.

A migration where two technologies coexist temporarily.

The quality of the escape hatch becomes important.

In Kora, the escape hatch is not really an escape hatch at all.

It is normal graph composition.

That is arguably one of the strongest properties a framework can have.

The unusual case still uses:

```text
typed config
factories
DI
lifecycle
telemetry
probes
testing
```

It remains inside the application's architecture rather than bypassing it.

## What Kora Is Optimizing For { #optimizing-for }

Putting all of this together, Kora's apparent target is not maximum theoretical applicability.

It is a narrower optimization problem:

```text
Production JVM backend
        ↓
common infrastructure
        ↓
compile-time validated graph
        ↓
generated code
        ↓
thin integrations
        ↓
virtual-thread synchronous model
        ↓
observability and lifecycle
```

The framework tries to make this path exceptionally direct.

That focus has consequences.

It means Kora may not always have the longest integration list.

It means some niche technology may require a small application-owned module.

It means teams occasionally need to understand the native Java client rather than only a Kora wrapper.

But those are acceptable costs if the framework keeps the integration boundary simple.

The payoff is fewer framework-specific concepts between the developer and the technology actually running in production.

## A Better Way to Evaluate Framework Ecosystems { #evaluate-ecosystems }

When evaluating a backend framework, count integrations if you want—but do not stop there.

Ask a broader set of questions.

How many of our common technologies have mature first-class support?

How good are those integrations operationally?

Can we use the native Java client when no official module exists?

How many framework concepts are required to expose that client to DI?

Can configuration be typed?

Can resource lifecycle be managed?

Can the client participate in tracing and metrics?

Can it expose readiness?

Can we override or customize framework components?

Can a local integration be extracted into a reusable module later?

Can developers continue using upstream library documentation?

Does the framework force us to wrap the native API?

How much framework-specific compatibility surface are we creating?

Those questions produce a much more realistic picture than counting starter names.

## The Real Ecosystem Is Framework Plus JVM { #real-ecosystem }

Kora's effective ecosystem is not only:

```text
official Kora modules
```

It is closer to:

```text
official Kora modules
        +
native JVM libraries
        +
small Kora integration modules
        +
internal reusable modules
        +
community integrations
```

That is a much larger reachable surface.

The key is that the bridge between those layers remains cheap.

If the bridge were expensive, the distinction would be theoretical.

Because `@Module`, typed configuration, component lifecycle, probes, and explicit DI are general-purpose mechanisms, the bridge can often remain only a small amount of code.

## Conclusion { #conclusion }

A framework ecosystem should not be judged only by the number of technologies for which somebody has already published a starter.

That number measures breadth, and breadth matters. Mature first-class integrations are valuable because they can encode good defaults, observability, lifecycle, testing, failure semantics, and years
of production experience.

But breadth is only half of the ecosystem story.

The other half begins when the catalog ends.

When an application needs a technology the framework does not officially support, does the framework become an obstacle? Does the team need internal extension APIs, complex bootstrap hooks, wrapper
hierarchies, or a separate DI mechanism?

Or can the team use the Java or Kotlin library directly, construct it with typed configuration, expose it through a small module, attach lifecycle and telemetry, add a probe where useful, and inject
it like any other component?

Kora is designed around the second model.

Its built-in modules focus on the common production backend surface: HTTP, data access, messaging, RPC, configuration, resilience, telemetry, caching, scheduling, validation, and operational
lifecycle. It does not need to wrap every possible SDK or library because its application graph is open to ordinary components.

That produces a useful distinction:

```text
Missing official integration
        ≠
unsupported technology
```

Often it simply means:

```text
native library
      +
small explicit integration module
```

If the integration becomes important across several services, that module can mature into shared infrastructure. The same model works at both stages.

This is why the strength of an ecosystem should not be measured only by how many integrations already exist, but by how cheaply and transparently developers can create the next one.

Kora does not try to own every technology you use. It tries to make using those technologies inside the application graph straightforward.

And that principle also explains its broader identity.

Kora is not attempting to be a framework for every possible application, programming model, vendor SDK, middleware product, or abstraction style. It focuses on a clearly defined class of work:
production Java and Kotlin backend services.

A Swiss Army knife wins by having a tool for almost everything.

Kora takes the opposite approach: fewer carefully chosen tools, optimized for the jobs backend engineers perform repeatedly, plus a simple and explicit way to add the next tool when they actually need
it.

That is not an absence of ecosystem.

It is a different definition of one.
