---
title: Where Kora Framework Performance Comes From
description: The Kora Framework's performance as a budget across compile time, startup, and runtime — generated wiring, thin abstractions, virtual threads, and the costs it cannot remove.
search:
  exclude: true
---

# Where Kora Performance Comes From

Performance discussions around backend frameworks often collapse too quickly into benchmark tables. One framework produces more requests per second than another, a chart is published, and the number
becomes the explanation. That is useful as an external measurement, but it does not explain *why* a framework behaves the way it does, which costs it removes, which costs remain unavoidable, or
whether the same architectural advantages will still matter once the benchmark is replaced by a real application with JSON mapping, database access, telemetry, resilience policies, and business logic.

The Kora Framework is more interesting when viewed as a performance budget rather than as a benchmark result. The framework deliberately moves a large class of decisions out of the request path and into
compilation. Dependency resolution, application graph construction, generated repositories, JSON codecs, HTTP adapters, and aspect wiring are prepared before the service starts. At runtime, the
resulting application is much closer to ordinary compiled Java or Kotlin code calling deliberately chosen libraries through relatively thin framework adapters. The important idea is not that
compile-time generation somehow makes every individual instruction faster. The idea is that work performed once by the compiler does not need to be rediscovered, interpreted, reflected upon, or
synthesized repeatedly during startup and request processing.

A useful high-level model is:

```text
Performance budget
├── Compile time
│   ├── dependency graph resolution
│   ├── wiring generation
│   ├── JSON and data mappings
│   ├── HTTP routes and adapters
│   ├── repositories
│   └── aspects
│
├── Startup
│   ├── prebuilt application graph
│   ├── no classpath-wide runtime discovery
│   └── parallel component initialization
│
└── Runtime
    ├── ordinary compiled method calls
    ├── generated type-specific adapters
    ├── thin integration layers
    ├── fewer categories of framework-side runtime work
    ├── virtual-thread request execution
    └── selected high-performance libraries
```

The rest of this article breaks down that budget. The goal is not to argue that every Kora service will always outperform every service built with another framework; application design, database
behavior, network latency, logging, object allocation, GC configuration, SQL quality, serialization format, and deployment topology can easily dominate framework overhead. The more useful claim is
narrower: Kora intentionally reduces how much general-purpose framework machinery remains on the critical runtime path, and that architectural choice influences startup time, warm-up behavior,
throughput, latency, memory pressure, and operational efficiency.

---

## Performance Is an Architecture, Not a Benchmark Mode

Kora's documentation describes performance as a consequence of compile-time decisions, generated code, thin abstractions, and selected high-performance integrations. That wording is important because
it shifts the discussion away from a special "performance mode." There is no separate philosophy in which a normal Kora application uses a highly dynamic runtime and then production users have to
disable features, remove reflection, replace default servers, rewrite repositories, or discover a collection of tuning switches before the framework becomes efficient. The same mechanisms used for
normal application development are the mechanisms intended to keep runtime overhead small.

This matters because framework performance is usually cumulative. A server-side request can cross many boundaries before business logic finishes: network server, route selection, parameter extraction,
security, tracing, controller invocation, validation, service aspects, repository implementation, database mapping, response serialization, metrics, and finally the HTTP transport again. Even if each
layer adds only a modest amount of indirection or allocation, multiplying that cost by several layers and then by hundreds of thousands of requests can make framework architecture visible in CPU
profiles and allocation rates.

Kora attacks that problem less by optimizing one spectacular hotspot and more by eliminating or simplifying many small pieces of runtime machinery. A route can be represented by generated code rather
than discovered through reflection when the request arrives. A repository method can contain generated typed `PreparedStatement` binding rather than interpreting metadata about method parameters on
every call. A JSON codec can be generated for the concrete DTO shape rather than discovering fields reflectively at runtime. An annotation such as a resilience or validation aspect can be translated
into an ordinary generated class during compilation rather than requiring a generic dynamic-proxy mechanism around every invocation.

None of these decisions alone guarantees high throughput. Together, however, they change the baseline cost of the framework.

---

## The First Part of the Budget Is Paid at Compile Time

The central architectural choice in Kora is to make the compiler perform work that many dependency-injection and annotation-heavy frameworks traditionally perform at runtime. Kora's annotation
processors for Java and KSP processors for Kotlin read application declarations, validate them, and generate source code that is compiled together with the application. The documentation explicitly
states that the dependency graph, aspects, HTTP handlers, repositories, and other components become ordinary compiled code without runtime reflection.

That shifts cost in two directions. Build time becomes slightly more expensive because processors have to analyze the program and emit source. Runtime becomes simpler because the service starts with
far more information already resolved. This trade is particularly attractive for server applications because compilation happens comparatively rarely, while the generated artifact may start many times
and process millions or billions of requests. Paying a deterministic cost once during a build is often preferable to paying discovery and interpretation costs every time an instance starts or every
time a generic runtime adapter executes.

This does not mean compile-time work is free or universally superior. Very large generated applications can increase compilation time, and Kotlin symbol processing is generally more expensive than
Java annotation processing. Kora's documentation even calls out that Kotlin processing is usually slower. The performance argument is therefore not "generation has no cost." It is that the cost is
placed in a phase where it can be amortized over the lifetime of the deployed application.

That distinction becomes clearer when the application fleet is considered rather than a single developer run. A build may happen once in CI, while the resulting artifact can be deployed to dozens or
hundreds of instances, restarted during rolling releases, recreated after node failures, scaled out during peaks, and started repeatedly by integration tests. Runtime work is multiplied by every one
of those events. Compile-time work is not.

---

## Compile-Time Dependency Injection Removes Runtime Graph Discovery

Dependency injection is the most fundamental example of this design. The Kora container is divided explicitly into compile-time and runtime responsibilities. During compilation, Kora discovers
components in the declared application and submodule scopes, resolves dependencies, detects errors, validates graph relationships, and generates regular Java code for application startup. Runtime
still has work to do—the objects have to be instantiated and lifecycle methods have to run—but it does not have to reconstruct the application's dependency model from scratch.

In a highly dynamic container, startup may include classpath scanning, annotation discovery, reflective constructor inspection, bean-definition construction, proxy preparation, condition evaluation,
and dependency resolution. Different frameworks perform different subsets of that work and modern implementations can optimize it aggressively, so it would be misleading to claim that "runtime DI is
always slow." The architectural difference is nevertheless real: Kora already knows the graph because it built and checked it during compilation.

The generated graph also changes the shape of steady-state application code. Once a `UserService` receives a `UserRepository`, application logic calls the object it already holds. There is no reason
for every normal dependency access to perform a name lookup in a container or resolve a component dynamically. The application's object graph behaves like a graph of normal objects because that is
effectively what the generated container constructs.

This has another indirect performance effect: Kora includes only components that are roots or are actually required by other components, and external modules are connected explicitly instead of being
discovered automatically from every dependency on the classpath. The benefit is not simply philosophical explicitness. Avoiding unnecessary graph nodes means fewer objects to instantiate, fewer
lifecycle operations to execute, and less framework state to keep alive.

The compile-time graph therefore contributes to performance in three different phases. It reduces startup discovery work, keeps runtime dependency access direct, and makes it easier to avoid
initializing framework functionality the application never asked to use.

---

## Startup Performance Comes From Knowing the Graph in Advance

Fast startup is often discussed as a separate metric from throughput, but in cloud systems it belongs to the same efficiency story. An application instance that spends less time scanning, reflecting,
synthesizing runtime metadata, and constructing unused infrastructure can reach readiness sooner. That improves local feedback loops, integration-test duration, rolling-deployment behavior, and
autoscaling response.

Kora's container documentation adds another important detail: components are initialized in parallel as much as the dependency graph allows, with lifecycle initialization running on virtual threads.
That is possible because the graph is already known. If components `A`, `B`, and `C` are independent and component `D` depends on all three, the container does not need to initialize them artificially
in sequence:

```text
A ─┐
B ─┼──> D
C ─┘
```

The dependency graph itself provides the scheduling constraints. Independent nodes can start together, while dependent nodes wait for their prerequisites. Startup time therefore tends toward the
graph's critical path rather than the sum of every component's initialization duration.

This does not make slow initialization disappear. If a database pool needs several seconds to establish connections, or a component performs expensive synchronous work during `init()`, Kora cannot
make the external system faster. What the graph allows the framework to avoid is unnecessary serialization between independent startup operations.

The same architecture helps explain why Kora can have a relatively small warm-up footprint. A runtime that performs less framework discovery after process start has less initialization code to execute
and less metadata to populate before useful traffic arrives. JIT compilation and application-specific warm-up still exist—Kora is still a JVM framework—but the framework can avoid adding a large
dynamic bootstrapping phase on top of the JVM's own startup behavior.

---

## Generated Wiring Turns Framework Decisions Into Ordinary Code

"Generated code" can sound like a vague optimization until it is translated into execution mechanics. The practical benefit is that a decision made from application metadata can become a statically
compiled branch, constructor call, field access, or method invocation rather than remaining an abstract description that must be interpreted later.

Imagine that a framework knows at compile time that a controller requires a service, the service requires a repository, and the repository requires a JDBC executor. Kora can generate code that
constructs precisely those relationships. The JVM then sees normal bytecode resulting from normal source code. This gives the JIT compiler familiar material to optimize: concrete call sites, known
classes, ordinary control flow, and regular field references.

That should not be exaggerated into a guarantee that every call will be inlined or every abstraction will disappear. JVM optimization depends on profiling, call-site shape, code size, polymorphism,
and many other factors. But generated ordinary code is generally friendly to the JIT because the framework has not intentionally hidden the execution path behind opaque reflective operations or
runtime-generated generic dispatch.

The performance advantage is therefore as much about *shape* as raw instruction count. Kora tries to present the JVM with execution paths that resemble hand-written application infrastructure. The
compiler performs architectural reasoning; the runtime executes the result.

---

## Routes Are Prepared Before Requests Arrive

HTTP routing is another place where frameworks can either retain metadata for runtime interpretation or generate request-handling code ahead of time. Kora's HTTP infrastructure is based on explicit
controller and route declarations, with generated controller modules and adapters connecting request parameters, mappings, interceptors, and controller methods.

The important runtime consequence is that request handling does not need to rediscover what a controller method means. Parameter bindings, required mapper dependencies, and route-level infrastructure
are already represented in generated code and the application graph. When a request arrives, the framework can move quickly from the selected route to the relevant generated adapter and then into
application code.

There will always be routing work. A server still has to parse an HTTP request, match a method and path, decode parameters, execute interceptors, produce a response, and write bytes to the network.
Kora does not eliminate these fundamental costs. The optimization is to avoid adding a large generic introspection layer on top of them.

This is an important pattern throughout Kora: necessary runtime work remains runtime work, while predictable framework interpretation is pushed earlier.

---

## Mapping Is a Major Part of Real Backend Cost

Synthetic plaintext benchmarks are useful for understanding the lower bound of framework overhead, but real services spend significant time converting data between representations. JSON bytes become
DTOs, database rows become domain objects, method arguments become SQL parameters, configuration text becomes typed settings, and application objects become network payloads. Mapping is therefore a
substantial part of the framework performance budget.

Kora uses compile-time generation heavily in this area. Its JSON module can generate `JsonReader<T>` and `JsonWriter<T>` implementations for concrete types. These generated codecs become normal
components in the application graph. Field naming strategies, nullability rules, inclusion behavior, enum handling, and custom mappers can be resolved into generated type-specific code rather than
requiring a generic reflective object mapper for every operation.

The benefit is not that parsing JSON itself becomes free; parsing still has to examine every relevant token and writing still has to encode output. The savings come from reducing the amount of dynamic
type discovery and generic property handling surrounding that parsing. When a codec already knows the DTO's shape, it can execute the mapping logic directly.

Kora also allows Jackson-based mapping when an application needs it, which is an important reminder that performance design should not become dogma. Generated codecs are a tool, not a requirement that
every integration abandon the ecosystem. The framework allows generated and Jackson mapping to coexist, letting applications choose the right trade-off for a particular boundary.

---

## JDBC Repositories Move Query Plumbing Out of the Hot Path

Database access demonstrates the same principle even more concretely. A Kora JDBC repository describes a query declaratively, but the implementation is generated. The documentation states that
parameter binding is emitted as typed JDBC calls. A `String name` parameter, for example, can become generated code equivalent to `statement.setString(index, name)`.

This matters because a repository abstraction can be high-level without requiring a high-level runtime interpreter. The developer writes:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface UserRepository extends JdbcRepository {

        @Query("SELECT id, name FROM users WHERE id = :id")
        User findById(long id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface UserRepository : JdbcRepository {

        @Query("SELECT id, name FROM users WHERE id = :id")
        fun findById(id: Long): User
    }
    ```

but the runtime does not have to parse Java method metadata on every call to determine that `id` should be bound to a particular statement position. That relationship was known during compilation and
can be encoded in the generated implementation.

Again, the dominant cost of a real database request may be the database itself. A 3-millisecond network round trip and query execution will dwarf dozens of nanoseconds of framework call overhead. Yet
framework efficiency still matters at high throughput, on very fast local databases, and in the CPU budget surrounding every query. More importantly, the same design improves predictability: there is
less hidden mapping machinery to appear unexpectedly in profiles.

Kora's repository layer is therefore a good example of a "thin abstraction." It gives application developers a concise repository contract while still producing code close to the underlying JDBC
operation instead of constructing an entirely separate persistence runtime with its own execution model.

---

## Compile-Time AOP Avoids a Generic Runtime Proxy Layer

Annotations for validation, caching, resilience, transactions, scheduling, security, and logging are convenient, but annotation-driven frameworks often pay for that convenience by introducing runtime
proxying. Kora's approach is different: aspects are processed and source code is generated at compile time. The landing documentation explicitly describes production aspects as generated without
runtime proxies.

This does not mean an aspect has zero runtime cost. A circuit breaker still has to inspect state. A retry still has to execute retry logic. Metrics still need to record measurements. Validation still
has to check data. A transaction still needs begin/commit/rollback behavior. What "free aspects" means architecturally is that the *framework mechanism used to attach the behavior* does not need an
additional dynamic-proxy system to decide how to intercept the call at runtime.

That distinction is important. Suppose a circuit breaker protects a method. The circuit breaker algorithm necessarily adds branches and state access around that invocation. Kora cannot eliminate those
because they *are the feature*. What it can eliminate is avoidable framework work required merely to discover that the method has a circuit breaker and route the invocation through a generic
reflective interceptor.

This is a recurring Kora performance principle: optimize the mechanism, not away the semantics. Observability, resilience, transactions, and validation are production requirements, and disabling them
to win a benchmark would not demonstrate useful framework performance. The goal is to implement those capabilities with as little incidental overhead as practical.

---

## Direct Method Calls Are More Important Than They Sound

"Direct method calls" can sound too trivial to deserve a section. On the JVM, however, architecture influences what the JIT compiler can see and optimize. A normal Java call through a stable, often
monomorphic call site is a pattern HotSpot has spent decades optimizing. It can profile it, devirtualize it in many situations, inline it when profitable, and optimize code across the resulting
boundary.

A framework that expresses most of its runtime behavior as ordinary generated Java or Kotlin therefore benefits from the optimization model the JVM already understands. It does not need a special
execution engine for application code.

This is also why thin abstractions and code generation reinforce each other. A generated controller adapter calls a controller. A generated repository calls JDBC APIs. A generated JSON writer calls
parser or generator operations for known fields. A generated AOP subclass calls the original method plus the required aspect logic. Each layer can remain relatively small and explicit.

Calling something "direct" does not mean there is literally only one machine instruction between HTTP bytes and business logic. There are still layers, interfaces, telemetry hooks, transport code, and
library calls. The useful comparison is between a path whose layers mostly compile down to ordinary typed calls and a path that repeatedly consults runtime metadata to determine what those calls
should be.

---

## Thin Abstractions Reduce the Semantic and Runtime Distance

Kora deliberately stays close to JDBC, Kafka, gRPC, HTTP, and other underlying technologies. This is usually presented as a transparency and maintainability advantage, but it also has a performance
dimension. Every framework abstraction potentially introduces extra objects, conversion layers, state machines, queues, schedulers, or semantic translation. None of those things are automatically bad;
some abstractions provide enormous value. The problem appears when a framework creates a parallel world even though the underlying library already exposes the semantics the application needs.

A thin abstraction tries to add only the missing ergonomics: configuration, generated glue, lifecycle management, observability, and type-safe declarative APIs. It avoids reimplementing the entire
technology behind a framework-specific runtime unless doing so solves a concrete problem.

That approach reduces opportunities for accidental overhead. A JDBC call remains recognizably JDBC. A gRPC integration remains built around gRPC. The HTTP server is still Undertow underneath Kora's
server module. Engineers can therefore reason about performance using knowledge of the underlying technology instead of first reverse-engineering a large framework execution model.

Thinness also helps performance debugging. When a CPU profile shows time in the JDBC driver, JSON parser, Undertow, or business logic, the result is easier to interpret than a profile dominated by
framework-internal adapters whose relationship to the underlying operation is unclear. Performance is not only about being fast; it is also about being diagnosable when something becomes slow.

---

## Selected Libraries Are Part of the Performance Story

Compile-time generation cannot compensate for a poor transport or database client. Kora therefore treats library selection as part of framework design. Its HTTP server implementation is based on
Undertow, a lightweight asynchronous NIO server, while Kora dispatches request handling to virtual threads rather than a bounded blocking worker pool. The documentation explicitly notes that there are
no `blockingThreads` or `virtualThreadsEnabled` switches because request handling uses that model directly.

This illustrates a useful division of responsibilities. Undertow handles efficient network I/O. Virtual threads give application code a simple synchronous model for blocking operations. Kora provides
generated routing, lifecycle, telemetry, and integration between those pieces. Performance comes from composing specialized mechanisms rather than requiring one framework runtime to reinvent all of
them.

The same philosophy applies to other modules. A framework integration should use an implementation that is already good at its own domain and avoid wrapping it in unnecessary machinery. This is why
library choice belongs in the runtime performance budget alongside generated code.

There is still no universal "fastest library" for every workload. TLS configuration, HTTP/2 behavior, payload size, database driver versions, Kafka batching, socket buffers, GC, and kernel behavior
can all change the result. The relevant Kora design principle is that efficient integration selection is treated as a framework responsibility rather than left entirely to every application team to
rediscover.

---

## Virtual Threads Change Concurrency Overhead, Not Resource Limits

Kora 2 executes application code synchronously on virtual threads. Controllers, clients, repositories, and scheduled tasks use ordinary blocking signatures, and HTTP request handling is dispatched
onto virtual threads. This is central to runtime performance because it allows Kora to preserve straightforward thread-per-operation code without requiring a large platform-thread pool for every
blocking request.

The key performance property of virtual threads is not that they make CPU computation faster. They make large numbers of blocking operations much cheaper to represent. When a virtual thread waits in
supported blocking I/O, its carrier platform thread can execute other virtual threads instead of remaining occupied for the duration of the wait.

This allows Kora to avoid an architectural trade that dominated JVM backend design for years. A framework no longer has to choose between simple blocking application code with a limited
platform-thread pool and an asynchronous/reactive application model designed to keep those platform threads from blocking. Virtual threads let Kora keep direct synchronous APIs while still supporting
high I/O concurrency.

They do not, however, create unlimited capacity. A service may have hundreds of thousands of virtual threads and still have only 50 JDBC connections, a finite number of CPU cores, a limited
remote-service quota, and bounded network bandwidth. If application code fans out aggressively, virtual threads can actually make those downstream limits easier to hit because thread scarcity is no
longer acting as accidental backpressure.

Kora's virtual-thread model should therefore be understood as the removal of one bottleneck—the cost of waiting platform threads—not as the removal of concurrency management itself.

---

## "Minimal Allocations" Needs a Precise Definition

It is tempting to summarize Kora runtime performance as "minimal allocations," but that phrase needs care. A normal request necessarily allocates in many circumstances. HTTP request state exists. JSON
may create DTOs, strings, collections, and byte buffers. Database drivers allocate protocol and result objects. OpenTelemetry can create observation state. Application business logic constructs its
own data. Response serialization may allocate or use pooled buffers depending on the path.

Kora's architecture is better described as trying to avoid *unnecessary framework-side allocations and runtime metadata structures*. If a mapping is generated, the framework does not need to construct
a generic property model every time it maps a DTO. If dependency wiring is generated, startup does not need to manufacture a large reflective representation of the same relationships. If an aspect is
compiled into a generated subclass, runtime does not need an additional general-purpose dynamic proxy object to represent how the annotation should behave.

Whether this materially reduces allocation rate in a specific endpoint must still be measured. Allocation behavior is highly workload-dependent, and a single careless business operation can allocate
more than the whole framework path. Large JSON documents, temporary collections, regex processing, logging arguments, ORM entity graphs, or copying buffers can easily dominate GC pressure.

The important engineering principle is therefore not "Kora allocates almost nothing." It is "Kora tries not to allocate framework machinery for decisions the compiler already knows."

---

## Fewer Runtime Abstractions Can Improve JIT Warm-Up

Steady-state throughput is only one dimension of JVM performance. Services also pass through an early period in which HotSpot collects profiling information and compiles frequently executed methods. A
framework with a smaller and more direct runtime path gives the JIT less framework machinery to warm up before request execution resembles steady state.

This does not remove JIT warm-up. Generated Kora classes, Undertow, JDBC drivers, JSON code, business logic, and every other hot method still need normal JVM optimization. The claim should be modest:
fewer dynamic framework layers generally mean fewer framework execution paths competing for profiling and compilation attention.

That can matter operationally during rolling deployments and autoscaling. If an instance becomes ready quickly but then exhibits a long period of poor tail latency while large amounts of framework
infrastructure warm up, readiness alone does not solve the problem. Kora's compile-time bias helps narrow the gap between "process started" and "application executing its normal hot path," although
real production behavior should still be verified under load.

---

## Performance Budget: What Kora Removes and What It Cannot Remove

A useful way to reason about Kora is to separate avoidable framework overhead from unavoidable application work.

Kora can reduce or move costs such as runtime dependency discovery, reflective mapping, dynamic proxy creation, generic method interpretation, route metadata analysis, repository parameter
interpretation, and unnecessary initialization of modules that were never connected. Those are framework choices.

Kora cannot eliminate the cost of parsing an HTTP message, copying bytes when a protocol requires it, parsing JSON tokens, constructing application objects, executing SQL, waiting for a remote server,
encrypting TLS traffic, recording telemetry, running a circuit-breaker algorithm, computing business rules, or performing garbage collection for objects the application genuinely creates. Those are
intrinsic workload or feature costs.

This boundary is important because it prevents unrealistic expectations. If an endpoint spends 85% of its wall-clock time waiting on PostgreSQL, replacing framework-level reflection with generated
code cannot make the database query ten times faster. What it can do is reduce the CPU and latency consumed by the remaining 15%, lower per-request overhead at high concurrency, improve startup and
memory behavior, and avoid adding another large source of variability around the dominant dependency.

Framework efficiency is most valuable precisely because application teams cannot eliminate all of their real work. The framework should consume as little of the remaining budget as practical.

---

## A Request Path Through the Performance Budget

Consider a representative Kora endpoint that receives JSON, validates it, calls a service protected by a circuit breaker, executes a JDBC repository query, and returns JSON. The runtime path contains
real work at every layer, but much of the framework configuration has already been transformed into code:

```text
HTTP bytes
   ↓
Undertow network layer
   ↓
generated / prewired route adapter
   ↓
generated request mapping
   ↓
controller method
   ↓
compile-time attached validation / resilience logic
   ↓
service method
   ↓
generated JDBC repository
   ↓
typed PreparedStatement binding
   ↓
database
   ↓
generated result mapping
   ↓
service / controller
   ↓
generated JSON writer
   ↓
HTTP response
```

The point of this diagram is not that every arrow has zero overhead. The point is that the framework rarely needs to stop and ask a runtime metadata system, "What does this annotation mean?", "Which
constructor should I call?", "Which property corresponds to this JSON field?", "Which method parameter maps to this SQL placeholder?", or "Which interceptor should exist for this method?" Those
questions were largely answered earlier.

A high-level declarative programming model and a low-overhead runtime are therefore not opposites. Code generation is the bridge between them.

---

## Why Benchmark Results Can Reflect the Architecture

Kora's landing page currently cites an external TechEmpower "Single query" snapshot in which Kora JDBC Repository is among the highest-throughput JVM entries shown. That is useful evidence that the
architecture can translate into high throughput under a controlled workload. It is not proof that every production Kora application will have the same relative advantage.

The Single Query test is intentionally narrow. It emphasizes HTTP handling, one database query, serialization, and framework overhead. It does not reproduce a production topology with network-distance
databases, complicated authorization, several remote dependencies, large payloads, logging, caches, event publishing, or substantial business computation. In a real application, those costs can dwarf
the difference between framework runtimes.

That does not make the benchmark irrelevant. A narrow benchmark is useful precisely because it exposes the framework floor. If two applications perform almost the same business operation and one
spends materially more CPU inside framework machinery, a microservice fleet eventually pays for that difference. The mistake is using the benchmark as the entire performance argument instead of
treating it as one measurement consistent with the architecture.

The strongest performance story for Kora is therefore not "look at this requests-per-second number." It is "look at which work exists at compile time, which work remains at startup, which work
executes per request, and then use benchmarks to verify the consequences."

---

## Throughput Is Only One Output of Efficiency

A framework can be efficient even when an application does not need maximum throughput. Lower per-request CPU means more headroom for traffic spikes or fewer cores for the same workload. Lower startup
overhead means faster integration tests and faster horizontal scaling. A smaller baseline object graph means less memory retained before the application even processes a request. A shorter warm-up
path can reduce tail-latency turbulence during deployments.

These effects become more important at fleet scale. A single service running four instances may not justify architectural decisions based on a few percent of CPU. Hundreds of services replicated
across availability zones, development environments, CI pipelines, and disaster-recovery capacity change the arithmetic. Small per-instance differences multiply.

This is why Kora's performance design is closely connected to its cloud-oriented positioning. The optimization target is not simply "win a benchmark on one machine." It is to avoid framework overhead
that has to be provisioned, started, warmed, and paid for on every instance.

---

## Compile-Time Work Has a Cost, and That Cost Should Be Visible

A balanced discussion has to include the cost Kora chooses to pay. Annotation processing and KSP generation add build work. Generated source increases the amount of code the compiler must compile.
Large application graphs require processor analysis. Kotlin projects pay additional KSP overhead, and the Kora documentation explicitly notes that Kotlin processing is usually slower than Java
annotation processing.

This can matter in large monorepos or during rapid local iteration. Kora mitigates some of the problem structurally with submodules: `@KoraSubmodule` lets application areas be processed independently,
and the documentation notes that changes in one project module then do not force processors to analyze the entire application again. Gradle incremental compilation and build caching also become
important.

The correct trade-off depends on deployment economics. Kora intentionally accepts some additional build-time work in exchange for less runtime work. For a long-running service deployed many times from
one artifact, that trade is attractive. For unusual workloads where compilation speed dominates and runtime cost is irrelevant, the balance might be different.

Performance engineering is always about where the cost is paid, not whether cost exists.

---

## Thin Runtime Does Not Mean Featureless Runtime

A common way to make a benchmark fast is to remove production features. Disable tracing, skip metrics, bypass validation, avoid resilience, use a hand-written router, and compare the resulting minimal
loop with a full application stack. That tells little about production engineering.

Kora's more interesting objective is to retain production features while keeping their framework attachment inexpensive. HTTP telemetry is a normal part of the server design. Metrics, tracing,
logging, probes, lifecycle management, graceful shutdown, resilience, and other capabilities are treated as first-class modules. The runtime cost of the *feature itself* remains, but the framework
attempts to avoid unnecessary mechanisms around it.

This distinction also helps teams reason about optimization correctly. If tracing causes measurable cost, the answer is not automatically to blame dependency injection or routing. Profiling can show
whether the time is in span creation, exporter pressure, JSON serialization, logging, database calls, or application logic. Thin framework paths make that attribution easier.

A performant production framework should not merely be fast when nothing is enabled. It should make the cost of enabled capabilities visible and proportionate.

---

## Performance Predictability May Matter More Than Peak Numbers

There is another advantage to compile-time generation that is harder to express in benchmark charts: predictability. Dynamic framework behavior can introduce costs that appear only for particular
classes, annotations, proxy shapes, classloader conditions, or rarely used paths. Compile-time validation and generation reduce the number of runtime decisions that can surprise the application.

Predictability matters for tail latency. A service rarely fails its SLO because average latency moved from 2.1 to 2.2 milliseconds; it fails because some path suddenly allocates heavily, blocks a
critical pool, performs lazy initialization, hits a cold reflective cache, or triggers expensive runtime setup. Moving more framework preparation to build and startup time reduces some categories of
first-use and lazy-discovery behavior.

It would be wrong to claim that Kora eliminates latency outliers. Databases stall, networks retransmit, GC pauses, downstream services degrade, CPUs become saturated, and application code still has
cold branches. What Kora can do is avoid making framework dynamism another major source of unpredictability.

That is a meaningful form of performance.

---

## Where the Real Bottleneck Moves

Once framework overhead becomes small, bottlenecks move toward the application and its dependencies. This is a good outcome, but it changes what engineers should optimize.

A Kora service using JDBC may be limited by the database connection pool long before virtual threads become a problem. A JSON-heavy endpoint may be limited by serialization and allocation. A gRPC
aggregator may be limited by remote latency. A cryptographic endpoint may be CPU-bound. A Kafka producer may be dominated by batching and broker acknowledgements. At that point, squeezing another
small percentage from DI or route dispatch will not materially change the service.

The framework's job is to get out of the way enough that profiles point toward those genuine costs. The application's job is then to size pools, choose query plans, design caching, control
concurrency, reduce payloads, batch efficiently, and choose appropriate data structures.

This is also why Kora's synchronous virtual-thread model should not be interpreted as "performance without engineering." It removes one class of complexity. Capacity planning, Little's Law,
backpressure, pool sizing, tail-latency analysis, and downstream protection still apply.

---

## How to Measure Whether Kora's Architecture Helps Your Service

The correct way to evaluate a performance-oriented framework is not to trust either marketing claims or one public benchmark. Build a workload that resembles the service you care about and decompose
the result.

Measure startup separately from steady-state throughput. Measure p50, p95, p99, and maximum latency rather than average latency alone. Record CPU consumption for a fixed throughput level instead of
testing only maximum requests per second. Track allocation rate and GC pause behavior. Observe RSS and heap occupancy after startup and under load. Verify database pool saturation, remote
connection-pool behavior, and carrier-thread health. Run with production telemetry enabled because that is the system you will actually operate.

Profiles are especially valuable. If Kora's design works as intended, much of the CPU should be attributable to concrete technology and application work: Undertow, JSON processing, the JDBC driver,
cryptography, telemetry, and business logic. Generated Kora classes may appear, but they should generally represent useful glue rather than a large runtime interpretation engine.

A good framework benchmark therefore answers two questions. First, "How much work can this stack do?" Second, and more importantly, "Where did the CPU, allocations, and latency go?" The second
question explains whether the result will generalize to a different workload.

---

## The Performance Budget in One View

The complete Kora performance model can be summarized without reducing it to a slogan.

At **compile time**, the framework resolves the application graph, validates dependencies, generates wiring, builds type-specific mappings, generates repositories and HTTP adapters, and applies
aspects through generated source. Build time becomes the place where the framework reasons about application structure.

At **startup**, the runtime begins with that prebuilt structural knowledge. It creates the required graph rather than discovering the application from scratch, initializes independent graph nodes
concurrently when possible, and avoids initializing modules that were never connected.

At **request time**, generated adapters and ordinary JVM calls connect the transport to application logic. The framework uses thin wrappers around established technologies, generated mapping where
appropriate, typed repository implementations, compile-time AOP, and virtual threads for synchronous high-concurrency execution.

At **the infrastructure boundary**, Kora still depends on real libraries and real resources. Undertow must process sockets, PostgreSQL must execute SQL, the JDBC pool must provide connections,
OpenTelemetry must record observations, and the JVM must allocate and collect application objects. Kora's performance design does not deny those costs; it tries to avoid adding unnecessary framework
cost around them.

That is a much more useful explanation than "Kora is fast because it has no reflection." Reflection is only one visible symptom of the larger architectural decision.

---

## Conclusion

Kora performance comes primarily from deciding *when* framework work should happen and *how much* framework machinery should remain after that work is done. The framework pushes structural reasoning
into compilation: dependency wiring, generated mappings, repository implementations, routes, and aspects become source code before the application starts. Startup operates on a graph that already
exists and initializes independent components in parallel. Runtime then consists largely of ordinary typed calls through thin adapters into specialized libraries, with virtual threads providing a
simple synchronous concurrency model.

The result is not zero overhead, zero allocations, or automatic performance regardless of application design. A Kora service can still be slow because of poor SQL, excessive allocation, enormous
payloads, unbounded fan-out, saturated connection pools, expensive tracing, blocking native code, or inefficient business algorithms. No framework architecture can remove those costs.

What Kora tries to remove is a different category of cost: framework work that does not need to happen at runtime in the first place.

That distinction is the key to understanding its performance model. Instead of asking only how many requests per second a benchmark produced, inspect the budget:

```text
Compile time
├── resolve
├── validate
├── generate
└── compile

Startup
├── instantiate known graph
└── initialize independent nodes in parallel

Runtime
├── receive request
├── execute generated adapters
├── call business code directly
├── call thin integrations
└── pay only for the features and real work actually used
```

A benchmark is the measurement at the end of that chain. The architecture is the explanation.
