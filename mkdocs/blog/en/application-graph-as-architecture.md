---
title: The Application Graph as Architecture in the Kora Framework
date: 2026-09-02
description: Why the Kora Framework's compile-time application graph is not just DI wiring but an inspectable, validated map of the system's architecture.
search:
  exclude: true
---

# The Application Graph as Architecture { #application-graph-as-architecture }

**September 2, 2026**

Dependency injection is usually introduced as a convenience mechanism: instead of constructing objects manually, a framework constructs them and supplies their dependencies. That description is
correct, but in the Kora Framework it stops far too early.

In Kora, the application graph is not merely an implementation detail of dependency injection. It is a compact architectural model of the running service. The graph describes which parts of the
application exist, which parts depend on which others, which modules participate in the final service, which components own lifecycle, which parts may be initialized in parallel, which components must
be released first during shutdown, and how infrastructure such as telemetry is connected to the rest of the system.

That distinction matters because Kora builds and validates most of this graph at compile time. The framework does not wait for application startup to scan the classpath, discover definitions,
reconcile competing candidates, and only then learn whether the service can be assembled. The compiler and Kora's annotation processors already know enough about the application to generate ordinary
source code representing its wiring.

The result is a useful architectural property:

```text
Source code
   ↓
components + modules + explicit dependencies
   ↓
compile-time graph
   ↓
generated application wiring
   ↓
runtime lifecycle
```

The same model participates in all of those stages. The graph is therefore much closer to an executable architecture description than to a traditional runtime service locator.

This article looks at that idea from an architectural perspective. The point is not to repeat the Kora dependency-injection API, but to show what becomes possible when the application structure is
explicit, typed, generated, and validated before the process starts.

---

## A Service Is Already a Graph { #service-is-a-graph }

Any non-trivial backend service is naturally a directed graph whether the framework acknowledges it or not.

Consider a small HTTP service:

```text
HTTP Server
    ↓
Router
    ↓
PetController
    ↓
PetService
   ↙       ↘
PetRepository  AuditService
    ↓             ↓
DataSource      Kafka Producer
```

Each node has a role. Each edge says something stronger than “object A happens to have a field of type B.” The edge states that one part of the system requires another part in order to perform its
function.

Those edges encode several kinds of architecture simultaneously:

- **construction architecture** — what must exist before another component can be created;
- **behavioral architecture** — which capabilities a component delegates to other components;
- **lifecycle architecture** — which resources must be initialized before their consumers and released after those consumers stop;
- **module architecture** — which technology or domain modules become part of the service;
- **operational architecture** — how metrics, tracing, logging, probes, servers, databases, messaging clients, and other infrastructure become connected to application code.

Many frameworks eventually construct such a graph internally. The architectural difference is *when* the graph becomes known, *how explicitly* it is described, and *whether the developer can reason
about it before runtime*.

Kora's answer is to move as much of that work as possible into compilation.

---

## From Dependency Injection to an Executable Architecture Model { #from-di-to-executable-architecture }

A Kora application starts from an interface annotated with `@KoraApp`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends
        HoconConfigModule,
        LogbackModule,
        MetricsModule,
        UndertowPublicHttpServerModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application :
        HoconConfigModule,
        LogbackModule,
        MetricsModule,
        UndertowPublicHttpServerModule {

        companion object {
            @JvmStatic
            fun main(args: Array<String>) {
                KoraApplication.run(ApplicationGraph::graph)
            }
        }
    }
    ```

At first glance, this looks like a dependency-injection entry point. Architecturally, however, it says considerably more.

The application explicitly declares that configuration, logging, metrics, and the Undertow HTTP server belong to this service. If another integration is not connected, Kora does not silently discover
and initialize it merely because some dependency happens to be present on the classpath. External modules are connected deliberately through the application interface.

The business code adds another layer of structure:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class PetService {
        private final PetRepository repository;
        private final AuditService auditService;

        public PetService(PetRepository repository, AuditService auditService) {
            this.repository = repository;
            this.auditService = auditService;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class PetService(
        private val repository: PetRepository,
        private val auditService: AuditService
    )
    ```

The constructor expresses two graph edges:

```text
PetService ──→ PetRepository
PetService ──→ AuditService
```

Factories express the same thing explicitly through method parameters:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface PetModule {

        default PetService petService(
            PetRepository repository,
            AuditService auditService) {
            return new PetService(repository, auditService);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface PetModule {

        fun petService(
            repository: PetRepository,
            auditService: AuditService
        ): PetService {
            return PetService(repository, auditService)
        }
    }
    ```

The key architectural idea is that Kora does not need a separate architecture DSL to discover the basic structure of the service. Normal Java or Kotlin types, constructors, interfaces, modules, and
factory methods already carry enough information to describe much of it.

That keeps architectural declarations close to executable code. When the dependency changes, the architecture changes in the same edit.

---

## The Graph Is the Dependency Architecture { #graph-is-dependency-architecture }

Dependency architecture answers a simple question:

> What depends on what?

This sounds trivial until a system becomes large enough that the answer is no longer visible from a single file.

In a runtime-heavy container, understanding that structure can require reconstructing it mentally from several sources: annotations, component scans, configuration classes, conditional registrations,
runtime post-processors, framework conventions, auto-configuration rules, and sometimes dynamic proxies.

Kora deliberately narrows that space. Components have explicit providers. Dependencies are typed. External modules are explicitly connected. Missing providers, ambiguous providers, invalid tags, and
many cycles are graph-construction problems that surface during compilation.

Suppose a controller requires a service:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class PetController {
        private final PetService petService;

        public PetController(PetService petService) {
            this.petService = petService;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class PetController(private val petService: PetService)
    ```

and the service requires a repository:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class PetService {
        private final PetRepository repository;

        public PetService(PetRepository repository) {
            this.repository = repository;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class PetService(private val repository: PetRepository)
    ```

If `PetRepository` has no provider, that is not merely “DI configuration is broken.” Architecturally, the graph is incomplete:

```text
PetController
    ↓
PetService
    ↓
PetRepository  ← missing architectural node
```

Kora's compiler diagnostics can report the dependency-resolution path from a root down to the missing claim. That is important because the error is not only a type error; it is an explanation of *how
the broken architectural path was reached*.

A good compile-time graph turns failures such as these into architecture feedback:

```text
root
  ↓
HTTP route
  ↓
controller
  ↓
service
  ↓
repository [MISSING]
```

The same applies to ambiguity. If two implementations satisfy the same dependency and nothing distinguishes them, the architecture is underspecified. Tags, defaults, or explicit provider choices force
that ambiguity to be resolved in source code.

This is one reason compile-time DI has value beyond startup performance. It turns a set of architectural invariants into compiler-checkable properties.

---

## The Graph Is Also the Lifecycle { #graph-is-also-lifecycle }

Object graphs are often discussed as if they were static diagrams. Production applications are not static. They start, acquire resources, accept traffic, reload selected state, stop accepting work,
flush or release resources, and terminate.

Once components own resources, dependency direction becomes lifecycle direction.

Imagine this structure:

```text
PetController
    ↓
PetService
    ↓
PetRepository
    ↓
JdbcDataSource
```

The service cannot meaningfully become ready before the repository it needs is ready, and the repository cannot operate before its data source is usable.

Initialization therefore follows the graph:

```text
JdbcDataSource
      ↓
PetRepository
      ↓
 PetService
      ↓
PetController
```

Shutdown must reverse it:

```text
PetController
      ↓ release
 PetService
      ↓ release
PetRepository
      ↓ release
JdbcDataSource
```

Kora's runtime container uses the dependency graph to initialize components in dependency order while exploiting parallelism wherever independent branches allow it. Lifecycle-aware components
implement `Lifecycle`, while wrappers can attach lifecycle behavior to values produced by factories. On shutdown, components are released in reverse dependency order; framework integrations such as
HTTP servers and Kafka consumers use the same lifecycle machinery for graceful shutdown.

This makes the graph an execution plan for startup and shutdown.

Consider two independent branches:

```text
                 ┌─→ JdbcDataSource ─→ PetRepository ─┐
Application Root │                                     ├─→ PetService
                 └─→ Kafka Producer ─→ AuditService ──┘
```

The database branch and Kafka branch do not need to initialize serially merely because they belong to the same application. The graph already tells the runtime which nodes are independent. Kora can
therefore initialize as much as possible in parallel and synchronize only where dependency edges require it.

This is a subtle but important point: **the dependency graph is also a concurrency map for application initialization**.

A runtime does not have to guess which initialization steps are independent. The architecture already contains that information.

---

## Dependency Edges Have Lifecycle Semantics { #dependency-edges-lifecycle }

Kora makes the architectural meaning of edges even clearer through direct and indirect dependencies.

A normal dependency means more than “give me this object.” It also ties lifecycle changes together. If component `C` directly depends on component `B`, and the graph refreshes `B`, then `C` is part of
the affected dependency subtree and may also need to be rebuilt.

```text
A ──→ B ──→ C
```

A direct edge therefore means approximately:

```text
C requires the current B instance
and C participates in B's lifecycle changes
```

`ValueOf<T>` deliberately weakens that relationship. The consumer receives a live reference from which it can obtain the current graph value, but the consumer itself does not have to be recreated
merely because that referenced node changes.

```text
ServiceC ──direct──→ ServiceA
    │
    └──ValueOf────→ ServiceB
```

Architecturally, those are different edges.

That distinction is especially useful for long-lived infrastructure. An HTTP server owns a socket and should not be torn down every time a request-handler graph changes. The server can remain stable
while observing refreshed handlers through an indirect reference.

This turns the graph from a simple object-construction DAG into a richer model that expresses *propagation boundaries*.

A useful way to think about it is:

```text
Direct dependency
    = structural + lifecycle coupling

ValueOf / PromiseOf
    = structural reference with reduced lifecycle coupling
```

That gives architects a concrete mechanism for expressing which changes should propagate through the running system and which should not.

---

## The Graph Defines Initialization Order Without a Separate Startup Script { #graph-defines-init-order }

Traditional services often accumulate startup code over time:

```text
load config
initialize logging
create metrics
open database pool
run migrations
create repositories
start background workers
bind HTTP server
mark application ready
```

Eventually this becomes its own orchestration layer, with hand-written ordering rules and failure handling.

A dependency graph can encode much of that ordering naturally.

If the HTTP server depends on the router, the router depends on controllers, controllers depend on services, and services depend on databases or clients, then the graph already says what has to exist
before traffic can be processed.

Kora's lifecycle system uses this structure directly rather than requiring a parallel startup description.

That reduces the risk of two competing architectural models:

```text
Model A: dependency wiring
Model B: startup orchestration
```

When those models are separate, they can drift. A developer adds a new dependency but forgets to update startup ordering. A resource starts too early. A shutdown hook closes a dependency before its
consumer has stopped.

When dependency and lifecycle topology share the same graph, the amount of duplicated architectural knowledge decreases.

---

## Module Boundaries Become Visible in the Graph { #module-boundaries-visible }

The graph also describes where application capabilities come from.

Kora modules are ordinary interfaces that provide factories. External modules are not globally activated just because their JAR appears on the classpath; the application connects the ones it intends
to use.

For example:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends
        HoconConfigModule,
        JdbcDatabaseModule,
        PetModule,
        AuditModule,
        UndertowPublicHttpServerModule {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application :
        HoconConfigModule,
        JdbcDatabaseModule,
        PetModule,
        AuditModule,
        UndertowPublicHttpServerModule
    ```

That top-level interface is a concise architectural statement:

```text
Application
├── Configuration
├── JDBC database infrastructure
├── Pet domain
├── Audit domain
└── HTTP infrastructure
```

For larger codebases, `@KoraSubmodule` provides another useful boundary. A Gradle module can own a domain slice, collect its `@Component` and `@Module` definitions, and expose that slice to the final
application graph.

Conceptually:

```text
application
   │
   ├── PetSubmodule
   │      ├── PetController
   │      ├── PetService
   │      ├── PetRepository
   │      └── JDBC integration
   │
   └── VetSubmodule
          ├── VetController
          ├── VetService
          └── VetRepository
```

This is more than code organization. A module that is never connected to the application cannot quietly become part of the running service through broad classpath discovery.

That property helps maintain architectural boundaries because participation in the final application is explicit.

It also creates a useful review surface. A change such as:

```diff
 public interface Application extends
         PetModule,
         VetModule,
+        BillingModule,
         UndertowPublicHttpServerModule {
 }
```

is visibly an architectural change. The service has acquired an entire new capability. That is easier to notice in review than a transitive auto-configuration silently activating because a dependency
appeared in a build file.

---

## The Graph Includes Infrastructure, Not Only Business Services { #graph-includes-infrastructure }

A common mistake when drawing architecture diagrams is to show only business components:

```text
Controller → Service → Repository
```

The real production system contains much more:

```text
                    ┌─→ Metrics
                    ├─→ Tracing
HTTP Server → Route ├─→ Logging context
                    └─→ Controller → Service → Repository → DataSource

Kafka Consumer → Handler → Service

System Server → /metrics
              → /system/liveness
              → /system/readiness
```

Kora's graph includes these infrastructure components as ordinary parts of the application composition.

The observability stack is a good example. Connecting metrics, tracing, logging, and HTTP modules adds concrete objects and relationships to the graph: a metrics registry, metrics scraping, tracing
infrastructure, system endpoints, server components, and the application-specific services that emit business signals.

This is architecturally valuable because observability is not an invisible side channel bolted onto the application after the fact. It is part of the assembled system.

You can think of the graph as containing two intertwined architectures:

```text
Business architecture
---------------------
Controller
Service
Repository
Domain clients

Operational architecture
------------------------
HTTP server
Configuration
Metrics
Tracing
Logging
Probes
Schedulers
Kafka consumers
Database pools
```

Production behavior emerges from both.

A service whose business dependencies are correct but whose telemetry, readiness, shutdown, or configuration wiring is wrong is still architecturally broken. Treating infrastructure as first-class
graph nodes makes those relationships easier to reason about.

---

## Observability Wiring Is Architectural Wiring { #observability-wiring }

Kora's observability model demonstrates why the application graph is a better abstraction than “a bag of beans.”

A complete observable service may connect:

```text
LogbackModule
MetricsModule
OpentelemetryHttpExporterModule
UndertowPublicHttpServerModule
```

The resulting graph can contain relationships such as:

```text
MeterRegistry
    ↓
framework telemetry
    ↓
HTTP / database / messaging metrics

OTel exporter
    ↓
tracer
    ↓
request spans / client spans / business spans

system HTTP server
    ↓
metrics scraper + liveness + readiness
```

From an architectural point of view, this answers questions that are often absent from static diagrams:

- Where does the metrics registry come from?
- Which server exposes operational endpoints?
- Which telemetry implementation is injected into the database module?
- Which tracer is used by HTTP clients and business code?
- Which probes contribute to readiness?
- Which logging implementation carries trace correlation?

If these relationships live in the same graph as business dependencies, observability can be reasoned about structurally rather than treated as framework magic.

That also makes customization more local. Replacing a default telemetry factory or providing an application-specific component is a graph substitution, not an entirely different extension mechanism.

---

## Compile-Time Graph Validation Becomes Architecture Validation { #compile-time-graph-validation }

The strongest architectural consequence of Kora's approach is that some design errors become compilation errors.

This does not mean a compiler can prove that your architecture is *good*. It cannot tell whether a service has the correct bounded contexts, whether your domain model is elegant, or whether a
dependency is conceptually justified.

What it can do is validate structural invariants that are often prerequisites for a sound architecture.

### Missing dependencies { #missing-dependencies }

If a controller ultimately requires a repository that is not provided, the graph cannot be completed.

```text
HTTP root
  ↓
Controller
  ↓
Service
  ↓
Repository [missing]
```

This is detected before deployment.

### Ambiguous dependencies { #ambiguous-dependencies }

If two components implement the same contract and the injection point does not say which one it needs, the graph is ambiguous.

```text
                 ┌─→ StripePaymentGateway
CheckoutService ─┤
                 └─→ InternalPaymentGateway
```

Tags or another explicit choice resolve the architecture.

### Invalid or accidental cycles { #invalid-cycles }

Cycles often indicate tight coupling:

```text
ServiceA → ServiceB → ServiceC → ServiceA
```

Kora can detect graph cycles during compilation. Some interface-based cycles can be handled using generated promised proxies, and developers can deliberately weaken lifecycle coupling through
`ValueOf` or `PromiseOf`. The important part architecturally is that the cycle is visible as a graph property rather than surfacing as a mysterious runtime initialization failure.

### Missing roots { #missing-roots }

A graph with no root components effectively has no executable application surface. Kora can reject that shape rather than quietly constructing nothing useful.

### Tag mismatches { #tag-mismatches }

Tags are typed architectural qualifiers. If the graph contains the correct contract under a different tag than the one requested, the mismatch is visible to the compiler and diagnostics can point at
nearby candidates.

Each of these checks moves feedback earlier:

```text
architecture mistake
        ↓
compile
        ↓
precise graph error
```

instead of:

```text
architecture mistake
        ↓
build image
        ↓
deploy
        ↓
start application
        ↓
fail during runtime discovery
```

The practical benefit is not only reliability. It changes the economics of architectural experimentation. A refactoring that breaks graph invariants gives feedback while the developer is still in the
edit-compile loop.

---

## Diagnostics Become Paths Through Architecture { #diagnostics-as-paths }

A useful graph diagnostic should not merely say:

```text
PetRepository not found
```

The more useful question is:

> Why did the application need `PetRepository` in the first place?

Because the graph is known, diagnostics can explain a dependency-resolution path:

```text
Application Root
  ↓
PetController
  ↓
PetService
  ↓
PetRepository [MISSING]
```

That is effectively a small architecture trace.

For large applications, this matters considerably. The component that fails may be several layers away from the root that caused it to be included. A missing mapper can be required by a repository,
which is required by a service, which is required by an HTTP controller. Showing the path answers both *what is missing* and *why the compiler was trying to build it*.

The same principle applies to multiple candidates:

```text
PaymentService needs PaymentGateway

Candidates:
  StripeGateway
  InternalGateway
```

The diagnostic exposes an architectural decision that has not been made.

This style of feedback is one reason generated, compile-time wiring works well with both humans and coding agents: the compiler returns a concrete structural explanation that can be followed back into
source code.

---

## Generated Wiring Is an Architectural Debugging Surface { #generated-wiring-debugging }

Kora generates ordinary source code rather than hiding graph construction behind reflection or runtime bytecode generation.

That creates another useful property: the generated code is inspectable.

When behavior is unclear, a developer can move through the stack:

```text
business class
   ↓
constructor / factory
   ↓
generated graph wiring
   ↓
actual framework integration
```

This reduces the gap between the architecture you think you declared and the architecture the runtime actually executes.

Generated source can answer questions such as:

- Which factory creates this component?
- Which implementation satisfied this interface?
- Which tag resolved this dependency?
- Which generated adapter sits between the controller and HTTP server?
- Which concrete telemetry factory was wired into this integration?
- Why was a component included in the graph at all?

In a reflection-heavy runtime model, some of those answers exist only after the container has started and completed dynamic discovery. With generated wiring, much of the answer exists as code before
the service runs.

That is especially useful during framework upgrades. If generation changes, developers can inspect the new output and compare the actual wiring rather than treating the container as a black box.

---

## The Graph Is a Natural Basis for Visualization { #graph-visualization }

Once an application has a statically known graph, visualization becomes a data-projection problem rather than an exercise in runtime archaeology.

The conceptual transformation is straightforward:

```text
Kora graph
   ↓
node + edge metadata
   ↓
filter / group / annotate
   ↓
architecture diagram
```

For example, the raw component graph could be rendered as:

```text
UndertowServer
    ↓
HttpRouter
    ↓
PetController
    ↓
PetService
   ↙       ↘
PetRepository  AuditService
    ↓             ↓
JdbcDataSource   KafkaProducer
```

A more useful architecture view could group technical nodes:

```text
┌──────────────── HTTP ────────────────┐
│ Undertow → Router → PetController    │
└──────────────────┬───────────────────┘
                   ↓
┌────────────── Business ──────────────┐
│ PetService ─────────→ AuditService   │
└──────────────┬──────────────┬────────┘
               ↓              ↓
┌──────────── Data ────┐  ┌ Messaging ┐
│ Repository → JDBC    │  │ Kafka      │
└──────────────────────┘  └────────────┘
```

Another view could show lifecycle dependencies only. Another could highlight cross-module edges. Another could show roots and the transitive subgraphs reachable from them. Another could collapse
framework internals and leave only application components.

Kora's current documentation exposes graph access and generated graph structures, but the architectural point here is broader than any one built-in visualization command: **a compile-time graph gives
tooling a stable model to visualize**.

That opens the door to useful engineering tools such as:

- Graphviz or Mermaid export;
- IDE graph exploration;
- pull-request architecture diffs;
- module-boundary reports;
- detection of unexpectedly central components;
- lifecycle critical-path visualization;
- graph-size and fan-out analysis;
- dependency-policy checks in CI.

The important caveat is that not all of those are claims about features currently shipped by Kora. They are natural tooling opportunities enabled by having the graph explicitly available.

---

## Architectural Validation Can Go Beyond “Can the Graph Build?” { #architectural-validation-beyond-build }

Once architecture is represented as nodes and edges, validation can become richer than standard dependency resolution.

The first level is already present in Kora:

```text
provider exists?
provider unique?
tags compatible?
cycle resolvable?
root reachable?
component constructible?
```

But a graph can also support organization-specific rules.

Imagine a codebase with these architectural layers:

```text
HTTP
 ↓
Application
 ↓
Domain
 ↓
Data / Messaging
```

A team might decide that repositories must never depend on HTTP controllers, or that one domain module may not depend directly on another domain's persistence module.

Those policies are graph rules:

```text
allowed:   Controller → Service
allowed:   Service → Repository
forbidden: Repository → Controller
forbidden: DomainA → DomainBInternalRepository
```

Likewise, operational requirements can be phrased structurally:

```text
Every public HTTP server must have tracing.
Every database must have telemetry.
Every long-running consumer must participate in lifecycle.
No business component may depend directly on Graph.
Infrastructure modules may depend on common contracts,
but domain modules must not depend on framework-specific HTTP types.
```

A compile-time application graph makes such policies much easier to evaluate than a container whose final topology exists only dynamically after startup.

This is one of the most interesting long-term consequences of compile-time DI: the dependency container can become an architecture-analysis substrate.

---

## The Graph Can Reveal Architectural Smells { #graph-reveals-smells }

Even without sophisticated policy tooling, graph shape itself can expose problems.

### Excessive fan-in { #excessive-fan-in }

```text
A ─┐
B ─┤
C ─┤
D ─┼─→ MegaService
E ─┤
F ─┤
G ─┘
```

A component with an enormous number of dependencies may be doing too much or coordinating too many concerns.

### Excessive fan-out { #excessive-fan-out }

```text
                ┌→ A
                ├→ B
Controller ─────┼→ C
                ├→ D
                ├→ E
                └→ F
```

This may indicate that orchestration belongs in an application service rather than directly in an adapter.

### Cross-domain edges { #cross-domain-edges }

```text
OrdersService ─────────→ InternalBillingRepository
```

If the intended architecture says Orders should talk to Billing through a public contract, the graph can expose an accidental shortcut.

### Infrastructure leakage { #infrastructure-leakage }

```text
DomainService → Undertow-specific type
```

A graph can make framework leakage into domain code visible.

### Lifecycle hotspots { #lifecycle-hotspots }

If a frequently refreshed configuration node causes a very large direct-dependency subtree to rebuild, the graph reveals that a few `ValueOf` boundaries might isolate long-lived infrastructure from
volatile configuration.

These are architectural smells rather than universal errors. A framework should not blindly reject them. But an explicit graph makes them observable and measurable.

---

## Graph Slices Improve Testing { #graph-slices-testing }

The application graph also changes how component tests can be understood.

Instead of constructing an entirely different dependency universe for tests, Kora's test support can take the production application graph and retain the component under test together with the
transitive dependencies needed for that slice, while applying test replacements where necessary.

Conceptually:

```text
Production graph

HTTP Server
   ↓
Controller
   ↓
Service
  ↙   ↘
Repo   Audit
 ↓      ↓
DB     Kafka
```

A service-focused test can work with a smaller graph:

```text
Service
  ↙   ↘
Repo   Audit
 ↓      ↓
Test DB  Mock
```

This is architecturally stronger than manually assembling a test object graph that only approximates production wiring. The test is based on the same component relationships and lifecycle model, only
sliced and replaced where required.

That gives the graph another role:

> it becomes the common structural model shared by production startup and component testing.

When tests use the real graph structure, architectural refactorings are more likely to break tests in useful ways. If a service acquires a new required dependency, the test graph must account for it.
The test setup cannot silently drift as far from production wiring.

---

## Runtime Refresh Shows That the Graph Is Not Merely Static Metadata { #runtime-refresh-not-static }

Compile-time graph does not mean an application can never change after startup.

Kora separates two concerns:

```text
compile time: validate and generate graph structure
runtime: hold values, manage lifecycle, refresh affected nodes
```

The runtime graph can refresh a node and rebuild components that directly depend on it. The update is performed atomically: affected components are prepared in a temporary graph state, and only after
successful initialization does the new state replace the old one. If initialization fails, the temporary objects are released and the existing graph remains active.

Architecturally, this is interesting because the compile-time topology becomes the rule for runtime change propagation.

Suppose configuration changes:

```text
Config
  ↓
ClientConfig
  ↓
ExternalClient
  ↓
BusinessService
```

A refresh starting at `Config` can propagate through direct dependency edges.

But if a stable server uses `ValueOf<Handler>`:

```text
HandlerConfig → Handler
                  ↑
               ValueOf
                  │
              HTTP Server
```

then the handler can change without reconstructing the socket-owning server.

The graph therefore models not only architecture-at-rest but architecture-under-change.

---

## Why This Matters for Debugging { #why-matters-debugging }

Production debugging often begins with symptoms rather than structure:

```text
"The endpoint is returning 503."
"Kafka stopped consuming."
"Readiness never becomes healthy."
"The new configuration isn't taking effect."
"The service hangs during shutdown."
```

The graph gives each symptom a structural context.

For a failing endpoint:

```text
HTTP server
  ↓
route
  ↓
controller
  ↓
service
  ↓
repository
  ↓
database
```

For a telemetry problem:

```text
HTTP client
  ↓
telemetry factory
  ↓
tracer / metrics
  ↓
exporter / registry
```

For a shutdown problem:

```text
consumer
  ↓
handler
  ↓
service
  ↓
client
```

The graph tells you which components can still be using a resource when release begins and what the correct reverse dependency order should be.

For a refresh problem, it tells you whether the relationship is direct or mediated through `ValueOf`, which determines whether the consumer should be rebuilt or only observe the new value.

This is much more actionable than thinking of DI as a lookup mechanism. Debugging becomes navigation through a typed system topology.

---

## Why This Matters for AI-Assisted Development { #why-matters-ai-development }

The same properties that help engineers reason about the graph help coding agents.

An agent works best when it can answer deterministic questions from source code:

```text
Where is this component created?
What does it depend on?
Which implementation is selected?
What module adds it?
What is the path from an application root to this component?
What will restart if this node is refreshed?
What generated code performs the wiring?
```

A compile-time graph makes these questions comparatively concrete.

The feedback loop is also useful:

```text
agent edits architecture
       ↓
compiler builds graph
       ↓
Kora validates structure
       ↓
precise diagnostic
       ↓
agent fixes code
```

This is a much smaller search space than debugging a container whose final behavior depends on runtime discovery, reflection, configuration ordering, and hidden activation rules.

There is another advantage: generated sources can be inspected by the model. Instead of guessing what runtime proxies or reflection metadata will produce, the agent can read the code Kora generated
and follow actual constructor and factory calls.

In that sense, the graph becomes both an architecture model and a machine-readable explanation of the architecture.

---

## A Useful Mental Model: The Graph Is the Service Skeleton { #graph-is-service-skeleton }

A concise way to think about Kora is this:

```text
Business logic is the behavior.
The application graph is the skeleton.
```

The skeleton determines which parts connect, what supports what, where boundaries exist, and how the whole system can be assembled and disassembled safely.

More concretely:

```text
Application graph
├── dependency topology
├── provider selection
├── module composition
├── lifecycle ordering
├── initialization parallelism
├── shutdown ordering
├── refresh propagation
├── operational wiring
└── testable graph slices
```

That is far more architectural responsibility than the phrase “dependency injection container” usually suggests.

---

## Kora's Compile-Time Graph Changes the Role of DI { #compile-time-graph-changes-di }

Traditional dependency injection often feels like infrastructure that sits beside the application architecture.

You design the architecture first, then configure a container to instantiate it.

Kora moves toward a different model:

```text
architecture expressed in typed code
              ↓
       graph construction
              ↓
      compile-time validation
              ↓
       generated wiring
              ↓
        runtime lifecycle
```

The graph is the bridge connecting those stages.

This has several consequences.

First, dependency declarations become architectural declarations. Adding a constructor parameter is not just asking the container for another object; it changes the dependency topology and potentially
the lifecycle topology.

Second, module composition becomes visible at the application boundary. Adding an infrastructure module is an explicit architectural change.

Third, startup and shutdown are derived from the same structure as dependency wiring rather than maintained as a parallel orchestration model.

Fourth, diagnostics can describe broken architecture as dependency paths.

Fifth, generated code provides a concrete debugging surface.

Finally, the graph can become input to tools that validate, visualize, compare, and analyze architecture.

---

## What a Graph-Oriented Architecture Workflow Could Look Like { #graph-oriented-workflow }

Once teams begin treating the application graph as architecture, the development workflow can evolve beyond “does DI compile?”

A mature workflow could look like this:

```text
1. Developer changes components or modules
                 ↓
2. Kora builds the graph at compile time
                 ↓
3. Structural validation runs
                 ↓
4. Generated wiring is compiled
                 ↓
5. Architecture tooling analyzes the graph
                 ↓
6. Tests run against graph slices / full graph
                 ↓
7. CI compares architectural changes
```

The architecture-analysis stage could answer questions such as:

```text
Did this PR add a new cross-domain dependency?
Did a component become a dependency hub?
Did an infrastructure type leak into the domain layer?
Did the lifecycle critical path become longer?
Did a new module become part of the application?
Did a configuration refresh gain an unexpectedly large blast radius?
```

Again, not every item in that list is a built-in Kora feature today. The point is that Kora's compile-time graph makes this style of tooling practical because the architecture already exists in
structured form.

---

## The Difference Between an Architecture Diagram and an Executable Graph { #diagram-vs-executable-graph }

A conventional architecture diagram is useful but passive.

```text
Controller → Service → Repository → Database
```

Nothing forces the implementation to continue matching it.
An executable graph is different. If the implementation says:

```text
Controller → Repository
```

then that edge is not merely present in a diagram—it is present in code, graph construction, lifecycle topology, and generated wiring.

This does not eliminate the need for higher-level diagrams. The raw application graph may contain hundreds of infrastructure nodes and generated adapters that are too detailed for architectural
communication.

But it gives those higher-level diagrams a trustworthy source from which they can be derived.

The ideal relationship is:

```text
Executable graph
      ↓
filter / group / annotate
      ↓
Architecture views
```

rather than:

```text
Architecture diagram maintained manually
      ↕
Hope that source code still matches it
```

That is the larger architectural opportunity behind compile-time dependency graphs.

---

## Conclusion { #conclusion }

Kora's application graph should not be viewed only as the mechanism that replaces a runtime dependency-injection container.

It is the structural core of the application.

It describes dependencies. Those dependencies determine initialization order. The same topology determines release order. Direct and indirect edges define refresh propagation. Modules determine which
capabilities belong to the service. Observability integrations become explicit parts of the assembled system. Tests can operate on slices of the same graph. Generated wiring makes the structure
inspectable. Compile-time validation turns many structural defects into compiler feedback.

That gives the graph several simultaneous roles:

```text
dependency model
      +
lifecycle model
      +
module composition
      +
operational wiring
      +
diagnostic model
      +
tooling substrate
      =
application architecture
```

The important shift is conceptual. Dependency injection is not the interesting part by itself. The interesting part is having a typed, explicit, compile-time model of how the service is assembled.

Once that model exists, the compiler can validate it, the runtime can execute it, developers can inspect it, tests can slice it, tools can visualize it, and architecture rules can be evaluated against
it.

That is why the application graph is one of the most important architectural ideas in Kora: it turns application structure from something the framework discovers at runtime into something the
development toolchain can understand before the service ever starts.
