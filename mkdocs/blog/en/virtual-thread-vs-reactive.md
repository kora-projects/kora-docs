---
title: Virtual Threads vs Reactive — What Changes in Kora Framework Backend Architecture
description: How the Kora Framework's virtual-thread-first model compares to reactive programming across APIs, drivers, debugging, and backpressure.
search:
  exclude: true
---
# Virtual Threads vs Reactive: What Actually Changes in Backend Architecture

For most of the last decade, discussions about reactive programming and thread-per-request architectures were framed as performance arguments. One side would point to event loops, non-blocking I/O,
and the ability to serve many concurrent connections with a small number of operating-system threads. The other side would point to the simplicity of ordinary imperative code, familiar debugging, and
the cost of turning an entire application into chains of futures, publishers, callbacks, or suspending functions.

Virtual threads change the terms of that discussion. They do not make reactive programming obsolete, and they do not make asynchronous I/O unnecessary. What they do is remove one of the strongest
historical reasons for exposing asynchronous execution throughout ordinary application code: the scarcity of platform threads.

That distinction matters. Reactive programming and virtual threads are not two syntax choices for the same runtime. They place complexity in different parts of the architecture. A reactive application
typically models waiting explicitly in its APIs and composes asynchronous stages as data flows. A virtual-thread application can keep the application layer synchronous while the JVM suspends and
resumes lightweight threads underneath it. Both models can achieve high concurrency, but they make different trade-offs in APIs, drivers, context propagation, debugging, flow control, resource
management, and failure handling.

Kora 2 makes a clear architectural choice here. The Kora Framework's application-facing contracts are synchronous: controllers, HTTP clients, repositories, and scheduled tasks use ordinary Java or Kotlin signatures,
while Kora dispatches application work onto virtual threads. Reactive and Kotlin `suspend` contracts are not part of Kora modules. In the HTTP server, request handling is synchronous and each request
is dispatched to a virtual thread; JDBC repositories are synchronous as well. The point is not to imitate a reactive stack with different syntax, but to return to direct code while retaining a
concurrency model suitable for modern backend workloads.

This article compares the two approaches as engineering architectures rather than as benchmark contestants. The interesting question is not which model can produce the largest requests-per-second
number in a particular test. The interesting question is: **what changes in the shape of a backend when concurrency no longer has to be represented as asynchronous application code?**

---

## The historical problem reactive programming was solving

Traditional Java servers were usually built around a thread-per-request model. A request entered the server, a platform thread handled it, and the same thread walked through the controller, service,
database layer, HTTP clients, and other application code until the response was complete.

Conceptually, this model was excellent:

```text
request
  |
  v
controller()
  |
  v
service()
  |
  v
repository()
  |
  v
JDBC
```

The call stack described the request. Local variables stayed local. Exceptions propagated through ordinary language mechanisms. A debugger could stop inside a repository and show the complete route by
which execution arrived there.

The scalability problem was the platform thread itself. A platform thread is backed by an operating-system thread and is therefore relatively expensive. If a request spends most of its lifetime
waiting for a database, another HTTP service, a file, or a broker, the operating-system thread is still a scarce resource tied to that request unless the application switches to asynchronous I/O.

Reactive architectures attacked exactly this problem. Instead of dedicating one scarce thread to one request, they represented waiting as continuations. A small number of event-loop or worker threads
could process many logical operations because an operation that had nothing to do would return control to the runtime and be resumed when data became available.

The architecture therefore changed from this:

```text
request -> thread -> blocking call -> thread waits -> result -> continue
```

into something closer to this:

```text
request
  -> stage A
  -> register continuation
  -> return thread
  -> I/O completes
  -> schedule continuation
  -> stage B
  -> ...
```

That was a rational trade. If threads are expensive, waiting must be represented without holding them. The cost is that the execution model leaks upward into the API model.

A repository no longer naturally returns `User`; it may return `Mono<User>`, `Uni<User>`, `CompletionStage<User>`, `Future<User>`, or another asynchronous type. The service composes that type. The
controller composes another stage on top. Context has to survive scheduler hops. Exception propagation becomes part of the asynchronous abstraction. Database access often moves from JDBC to a reactive
driver so that the entire chain can remain non-blocking.

Reactive programming therefore solved a real systems problem, but it did so by making concurrency part of the application contract.

---

## What virtual threads change

A virtual thread is still a Java `Thread`, but it is not permanently tied to an operating-system thread. The JVM schedules many virtual threads onto a much smaller set of platform threads, commonly
called **carrier threads**. When a virtual thread reaches a supported blocking operation, such as blocking I/O, the JVM can suspend the virtual thread and free its carrier to run another virtual
thread.

This changes the economics of waiting. Waiting still exists. Database latency still exists. Network latency still exists. The application still has tens of thousands of operations that may
simultaneously be waiting on external systems. What becomes cheap is representing each waiting operation as its own thread.

The important mental model is therefore:

```text
logical request = virtual thread

Virtual Thread A ---- running ----- waiting JDBC ........ running ---- done
                         |                                 |
                         v                                 v
                    Carrier #1                        Carrier #3

Virtual Thread B -------- running ---- waiting HTTP ........ running --- done
                           |
                           v
                      Carrier #2
```

The virtual thread is the logical unit of execution. The carrier is an implementation resource used only while the virtual thread actually needs CPU or is otherwise mounted. A waiting virtual thread
normally does not need to monopolize its carrier.

This is why virtual threads restore the viability of thread-per-request architecture without simply returning to the old platform-thread cost model. The application can once again say:

===! ":fontawesome-brands-java: `Java`"

    ```java
    User user = repository.findById(id);
    RiskScore score = riskClient.calculate(user);
    return mapper.toResponse(user, score);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val user = repository.findById(id)
    val score = riskClient.calculate(user)
    return mapper.toResponse(user, score)
    ```

instead of encoding each wait in an asynchronous type:

===! ":fontawesome-brands-java: `Java`"

    ```java
    return repository.findById(id)
        .flatMap(user -> riskClient.calculate(user)
            .map(score -> mapper.toResponse(user, score)));
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    return repository.findById(id)
        .flatMap { user -> riskClient.calculate(user)
            .map { score -> mapper.toResponse(user, score) } }
    ```

The difference is not that the first program “blocks everything.” It blocks the **virtual thread representing that operation**. When the JVM can unmount that virtual thread during I/O, the carrier
remains available for other work.

Virtual threads therefore separate two concepts that were often coupled in older Java architectures:

- synchronous application semantics;
- expensive operating-system thread occupancy.

Reactive programming avoided expensive thread occupancy by changing the application semantics. Virtual threads attack the thread-cost problem lower in the stack.

---

## The architectural comparison at a glance

The useful comparison is not “blocking vs non-blocking” as a slogan. It is where concurrency semantics appear and who has to manage them.

| Concern               | Reactive architecture                                     | Virtual-thread architecture                                               |
|-----------------------|-----------------------------------------------------------|---------------------------------------------------------------------------|
| Application API       | Asynchronous values and stream types                      | Ordinary synchronous values                                               |
| Request model         | Continuation / pipeline                                   | Thread per request or task                                                |
| Call stack            | Split across asynchronous boundaries                      | Ordinary Java/Kotlin call stack                                           |
| Waiting               | Represented by async stages                               | Represented by a parked virtual thread                                    |
| Thread usage          | Small event-loop/worker pools                             | Many VTs multiplexed over carrier threads                                 |
| Database              | Usually reactive/non-blocking driver                      | JDBC fits naturally                                                       |
| HTTP clients          | Async/reactive clients fit naturally                      | Blocking facade fits naturally                                            |
| Context               | Usually explicitly propagated across stages/schedulers    | Can follow execution scope; Kora uses `ScopedValue` for telemetry context |
| Exceptions            | Reactive error channel / failed stage                     | Normal throw/catch semantics                                              |
| Cancellation          | Usually part of async/stream composition                  | Thread interruption / structured task cancellation / explicit APIs        |
| Backpressure          | First-class stream protocol                               | Must be enforced with explicit resource limits and admission control      |
| Debugging             | Requires understanding operators and scheduler boundaries | Familiar stepping, stacks, thread dumps                                   |
| CPU-bound work        | Must be moved away from event loop                        | Must still be bounded; VTs do not create more CPU                         |
| Streaming pipelines   | Natural fit                                               | Possible, but flow control is not automatically a stream protocol         |
| Ecosystem requirement | Best when the chain is non-blocking end to end            | Works naturally with blocking JVM libraries                               |

The table immediately shows why the decision affects architecture far beyond the HTTP server. If an HTTP endpoint is reactive but the database API is blocking, the application needs a bridge. If the
database is reactive but business logic assumes thread-bound context, context has to be bridged. If a library performs long blocking work on an event loop, it can damage the whole event-loop runtime.
A concurrency model becomes most coherent when it extends across the stack.

---

## API shape: concurrency in the type system vs concurrency in the runtime

The most visible difference is the method signature.

A reactive API exposes the fact that a result is not available yet:

===! ":fontawesome-brands-java: `Java`"

    ```java
    Mono<Order> findOrder(long id);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun findOrder(id: Long): Mono<Order>
    ```

or:

===! ":fontawesome-brands-java: `Java`"

    ```java
    CompletionStage<Order> findOrder(long id);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun findOrder(id: Long): CompletionStage<Order>
    ```

A virtual-thread-oriented API can expose the business contract directly:

===! ":fontawesome-brands-java: `Java`"

    ```java
    Order findOrder(long id);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun findOrder(id: Long): Order
    ```

This looks like a minor stylistic difference until it propagates through a real application. Once the repository returns an asynchronous type, every caller must either compose it or block on it. If
the service returns an asynchronous type, the controller must compose it. Cross-cutting concerns such as retries, transactions, metrics, tracing, authorization, and caching must all understand the
asynchronous lifecycle correctly.

In a reactive architecture, this propagation is desirable because it protects the non-blocking execution model. Accidentally blocking an event-loop thread is dangerous, so asynchronous types
communicate an important execution constraint.

In a virtual-thread architecture, that same propagation is often unnecessary. The runtime already has an inexpensive way to represent the waiting operation. The method signature can therefore describe
the domain rather than the scheduler.

This is one of the biggest architectural consequences of Loom: **concurrency can move out of ordinary service interfaces and back into the runtime.**

That does not mean asynchronous APIs disappear entirely. If an operation is genuinely asynchronous by nature—event streams, callbacks from external systems, concurrent fan-out, background workflows,
or long-lived subscriptions—an asynchronous abstraction can still be the correct domain model. The point is that a simple request/response database call no longer needs to become asynchronous merely
to preserve server scalability.

---

## Call stacks and debugging

A synchronous call stack is more than a debugging convenience. It is an architectural representation of causality.

Consider a request that passes through five layers:

```text
OrderController.get()
  -> OrderService.load()
      -> PricingService.price()
          -> CustomerRepository.find()
              -> JDBC driver
```

With synchronous code, the runtime stack naturally captures this chain. An exception at the bottom can carry a stack trace that points through the same methods a developer reads in source code.

Reactive execution often breaks this physical stack at asynchronous boundaries. The logical operation still has causality, but the JVM stack may contain the current operator machinery rather than the
entire business path that led to it. Modern reactive libraries have substantially improved diagnostics with assembly tracing, checkpoints, operator debugging, and context-aware tooling, but the
developer still has to understand the distinction between the logical stream and the currently executing stack.

Virtual threads preserve the direct style. The thread may have been suspended and later resumed on a different carrier, but the virtual thread itself continues to represent the logical computation.
The business stack remains a normal stack.

This changes day-to-day incident response. A developer can inspect a thread dump, stop in a debugger, or read an exception and see ordinary application frames. There is less need to reconstruct
scheduler transitions mentally.

That does not make virtual-thread systems automatically easy to debug. Deadlocks, resource starvation, connection-pool exhaustion, excessive concurrency, pinned carriers, and bad timeout policies
remain real problems. What changes is that the execution representation is closer to the source-level control flow.

---

## Context propagation: the subtle difference

Context propagation is often presented too simplistically as “reactive requires explicit context, threads use `ThreadLocal`.” Modern Java makes the situation more nuanced.

Reactive pipelines frequently cross threads or schedulers. A value stored in a traditional `ThreadLocal` cannot be assumed to follow the logical operation, because different stages may run on
different threads. Reactive libraries therefore provide explicit context mechanisms or integrations that capture and restore telemetry, security, logging, or request metadata.

A virtual thread gives each logical task a thread identity, so ordinary thread-oriented APIs become easier to use. However, a framework still has to decide how request context should be represented,
inherited, bounded, and cleaned up. Blindly placing large mutable structures into `ThreadLocal` simply because virtual threads are threads is not a good architecture.

Kora 2 provides a useful example. Its tracing integration stores the current OpenTelemetry context using Java `ScopedValue`, not a traditional `ThreadLocal`. That context is available within the
dynamic scope Kora establishes for the operation, including on virtual threads. If application code explicitly hands work to another unrelated thread or executor, it must still propagate or rebind
that context.

This model illustrates a broader point: virtual threads simplify context propagation along the normal synchronous request path, but they do not eliminate the concept of execution scope. As soon as an
application creates detached asynchronous work, it has crossed a boundary and context must be handled intentionally.

Reactive programming makes these boundaries visible because the whole program is already composed through asynchronous stages. Virtual-thread applications make the common path simpler, but explicit
concurrency boundaries still deserve explicit treatment.

---

## Database architecture: reactive drivers vs JDBC

Database access is one of the places where the difference becomes concrete.

In a reactive stack, using JDBC directly from an event loop is normally incorrect because JDBC is a blocking API. A slow query, connection acquisition, network stall, or database pause would block the
event-loop thread and prevent unrelated requests assigned to the same loop from progressing. Reactive frameworks therefore use reactive database drivers or dispatch blocking JDBC work to a separate
worker pool.

This creates two coherent reactive strategies:

```text
A. fully reactive
HTTP event loop
  -> reactive service
  -> reactive DB driver
  -> continuation

B. reactive edge + blocking island
HTTP event loop
  -> worker pool
  -> JDBC
  -> event loop continuation
```

The second strategy can work well, but it introduces another scheduler, another queue, and another capacity boundary. The worker pool must be sized. Saturation has to be understood. Context must cross
the boundary. At that point the application is operating two concurrency models.

A virtual-thread architecture can use JDBC directly from the request virtual thread:

```text
HTTP transport
  -> request VT
      -> controller
          -> service
              -> repository
                  -> JDBC
```

The JDBC method remains blocking from the application’s perspective. The virtual thread waits. The carrier can usually be used elsewhere while the virtual thread is parked on supported I/O.

Kora 2 embraces this shape directly. Its JDBC repository contracts are synchronous, and its documentation explicitly states that there are no asynchronous or reactive repository signatures. The
generated repository implementation can therefore look and behave like ordinary JDBC code while still fitting a highly concurrent server architecture.

This has architectural consequences beyond readability. JDBC is one of the deepest and most mature ecosystems in Java. Connection pools, database observability, drivers, transaction semantics, vendor
features, tooling, and operational knowledge are abundant. A framework that can keep JDBC without dedicating one platform thread per waiting request can reuse that ecosystem instead of requiring a
parallel reactive database stack.

However, virtual threads do not make the database infinitely concurrent. The database still has finite connections, CPU, locks, memory, I/O bandwidth, and transaction capacity. A Hikari pool with 20
connections still allows roughly 20 simultaneously active database sessions regardless of whether 100 or 100,000 virtual threads are waiting to acquire them.

This is an important shift in thinking: **threads stop being the main concurrency limiter, so real resources must become the concurrency limiters.**

---

## Backpressure: where reactive still has a real structural advantage

Backpressure is the strongest area where reactive programming remains conceptually different rather than merely more complicated.

Reactive Streams was designed around asynchronous stream processing with non-blocking backpressure. The consumer communicates how much data it is prepared to receive, and demand propagates through the
stream. This is not just “limiting concurrency.” It is a protocol for coordinating producers and consumers across asynchronous boundaries.

Imagine a producer capable of emitting one million events per second and a consumer capable of processing only one hundred thousand. Without flow control, the difference must accumulate somewhere:
memory, an internal queue, a broker, a socket buffer, dropped messages, or increased latency. A reactive stream can make demand part of the composition itself.

Virtual threads do not automatically provide that protocol. If an application starts one virtual thread for every incoming unit of work, the JVM may be perfectly capable of representing all those
tasks, but the downstream database or remote API may not be capable of serving them.

A virtual-thread system therefore needs explicit capacity controls such as:

- bounded database connection pools;
- semaphores around scarce downstream services;
- bounded queues;
- rate limiters;
- admission control at HTTP or messaging boundaries;
- per-tenant concurrency limits;
- broker consumer limits;
- explicit streaming window sizes.

This is not necessarily worse. For request/response systems, these resource limits often correspond directly to the real bottleneck and can be easier to reason about than an end-to-end reactive graph.
If a partner service permits 50 concurrent calls, a semaphore of 50 expresses the rule precisely.

But for continuous streams, demand-driven graphs, or multi-stage pipelines in which production rates must adapt dynamically to consumption rates, Reactive Streams provides a richer native model. This
is one of the places where saying “virtual threads replace reactive” would be technically wrong.

---

## Event loops and the rule that does not change

Virtual threads do not make blocking safe on an event loop.

This distinction is essential because a server such as Undertow still uses network I/O threads. Those threads are responsible for moving bytes, accepting connections, parsing protocol events, and
driving the network layer efficiently. They are scarce by design.

Kora 2 therefore separates transport from application execution. Undertow has a configurable number of network I/O threads, but Kora dispatches request processing to virtual threads. Application code
can then block on JDBC or other supported blocking APIs without blocking the network thread.

The architecture is approximately:

```text
socket
  |
  v
Undertow / XNIO I/O thread
  |
  | dispatch
  v
Virtual Thread
  |
  +--> controller
  +--> service
  +--> JDBC / blocking HTTP client / filesystem
  +--> response mapping
  |
  v
Undertow writes response
```

The important rule remains: **do not perform arbitrary blocking application work on the event loop.**

A virtual-thread-first framework does not abolish event loops; it moves application code away from them. The event loop stays specialized for networking, while the virtual thread becomes the
application execution unit.

This is a cleaner separation of responsibilities than treating the event loop itself as the place where arbitrary business logic should run.

---

## CPU-bound work: neither model creates more cores

Both architectures are sometimes discussed as if their concurrency mechanisms improve all workloads. They do not.

Virtual threads are primarily useful when tasks spend significant time waiting. They do not make CPU-bound code execute faster. If 10,000 virtual threads simultaneously perform expensive JSON
transformations, image processing, compression, cryptography, or large in-memory sorts, the machine still has the same number of CPU cores.

Reactive programming has the same fundamental limitation. Moving CPU-heavy code through `map` operators on an event loop can be even more dangerous because a long computation monopolizes the
event-loop thread and delays many unrelated operations. Reactive frameworks therefore usually require CPU-heavy or blocking work to be moved to an appropriate scheduler or worker pool.

The correct architecture in either model is to bound CPU-intensive concurrency near the amount of actual parallel CPU capacity.

For virtual threads, that might mean a semaphore, a dedicated bounded executor for a specialized workload, or a service-level concurrency limit. For reactive systems, it commonly means switching from
an event-loop scheduler to a bounded worker scheduler.

Virtual threads remove the need to pool threads merely because threads are expensive. They do **not** remove the need to limit scarce resources.

That principle is central to using them correctly.

---

## Resource pools become more important, not less

In the old platform-thread model, a 200-thread request pool accidentally acted as a global concurrency limiter. Even if no one designed it as backpressure, only 200 requests could be actively
represented by those workers at a time. Everything else queued before entering the application.

Virtual threads remove that accidental limit. This is usually good, but it exposes the real capacity of downstream resources more directly.

Suppose a service can create 50,000 virtual threads but has:

- 30 database connections;
- 100 permitted concurrent calls to a payment provider;
- a Kafka producer with finite buffers;
- four CPU cores for encryption;
- 2 GiB of heap available for request bodies.

The application is not a 50,000-way concurrent system in any meaningful end-to-end sense. It is a system with several different capacity constraints.

A good virtual-thread architecture therefore replaces generic thread-pool tuning with resource-oriented limits:

```text
HTTP concurrency: potentially large
DB concurrency: 30
Payment API concurrency: 100
Encryption concurrency: ~CPU-sized
Large request bodies: explicitly bounded
Queue depths: bounded and observable
```

This is usually a more truthful model of the system.

Reactive architectures also need the same capacity model, but their execution machinery frequently embeds parts of flow control into publishers, subscriber demand, operator concurrency, and scheduler
queues. Virtual-thread systems tend to express these limits with familiar synchronization and resource-pool constructs.

Neither approach removes capacity engineering. They make it visible in different places.

---

## Failure handling and exceptions

Error handling is another place where source-level simplicity has operational consequences.

In synchronous Java or Kotlin, an operation can throw. A caller can catch. A transaction interceptor can roll back around the call. A retry aspect can invoke the method again. A debugger can stop at
the throw site.

Reactive systems represent failure as part of the asynchronous protocol. Instead of `throw`, the pipeline may produce an error signal or a failed future. Recovery becomes an operator:

===! ":fontawesome-brands-java: `Java`"

    ```java
    source
        .flatMap(this::callRemote)
        .retryWhen(...)
        .onErrorResume(...)
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    source
        .flatMap(this::callRemote)
        .retryWhen(...)
        .onErrorResume(...)
    ```

This model is powerful. It is especially expressive for streams because errors, completion, cancellation, and demand are all part of the stream lifecycle. But it also means every framework integration
must understand that lifecycle. A transaction cannot simply end when the method returns if the returned publisher has not executed yet. A tracing span cannot simply close at method exit if the
asynchronous operation is still running. A resource cannot be released merely because the publisher object was created.

That is why reactive integrations often have specialized transaction operators, context hooks, tracing instrumentation, and lifecycle-aware wrappers.

With synchronous virtual-thread code, method lifetime and operation lifetime usually coincide again. That simplifies cross-cutting framework code significantly.

This simplification is particularly important for compile-time frameworks such as Kora because generated decorators can often look like straightforward code a developer would have written by hand:
enter telemetry, invoke the method, handle exception, close telemetry, return result.

---

## Structured concurrency changes the fan-out story

One historical advantage of asynchronous composition is convenient fan-out. If a request has to call three independent services, an async API can start all three operations and combine their results
without allocating three platform threads.

Virtual threads make the imperative version viable as well. Instead of converting an entire service API to futures or publishers, the application can create child tasks for the few places where
concurrency is actually required, wait for them as a group, and then continue synchronously.

Conceptually:

```text
request VT
   |
   +---- child VT -> pricing service
   |
   +---- child VT -> inventory service
   |
   +---- child VT -> recommendations service
   |
   +---- join children
   |
   v
compose response
```

This localizes concurrency to the point where the business operation actually needs concurrency.

Kora 2 explicitly recommends Java structured concurrency for operations that need to perform several actions in parallel. At the time of its current documentation, `StructuredTaskScope` is still a
preview API, so build and runtime configuration must account for that. The architectural direction is nevertheless important: **ordinary sequential code by default, explicit structured parallelism
where needed.**

Reactive architectures often make the opposite default trade: asynchronous composition is ubiquitous, and sequential behavior is one special shape of the stream.

Neither is universally superior. The question is which default better matches the workload.

For CRUD-style business services, most methods are logically sequential even when they wait frequently. Virtual threads align well with that structure. For inherently concurrent dataflows, reactive
composition may align better.

---

## Pinning and carrier threads: what “blocking is cheap” does not mean

Virtual threads make many blocking operations cheap, but the phrase should not be interpreted as “every blocking operation is free.”

A virtual thread runs on a carrier thread while it is executing. When it encounters a blocking operation the JVM knows how to handle, it can unmount the virtual thread so that the carrier is available
for another virtual thread. If the virtual thread cannot unmount, it remains **pinned** to the carrier while blocked.

Modern JDK releases have reduced important sources of pinning, but native or foreign-function calls can still pin a virtual thread. Long-lived pinning matters because carrier threads are intentionally
limited. If many virtual threads simultaneously pin carriers while waiting, the architecture begins to lose the scalability advantage that made virtual threads attractive.

This leads to a practical rule: virtual-thread applications still need production diagnostics around carrier saturation, pinning, downstream latency, and concurrency spikes.

The correct comparison is therefore not:

```text
reactive = non-blocking
virtual threads = blocking
```

It is closer to:

```text
reactive:
application explicitly represents waits as async stages

virtual threads:
application uses blocking semantics;
JVM attempts to turn waits into virtual-thread suspension
```

Understanding that distinction prevents two mistakes: treating virtual threads as magic, and treating synchronous code as equivalent to blocking a scarce platform thread.

---

## Memory and concurrency shape

Reactive systems are often praised for having few threads, while virtual-thread systems may have enormous numbers of threads. Looking only at thread count is misleading because the units are
fundamentally different.

A reactive system represents pending work in publisher objects, callbacks, continuation state, queues, buffers, and operator graphs. A virtual-thread system represents much of that pending state in
virtual-thread stacks and scheduler metadata.

Both models need memory for outstanding work. Neither can accept infinite concurrency without consequences.

This matters when a service receives a spike. If 500,000 requests arrive and every request immediately creates a virtual thread, the system may avoid running out of platform threads, but it can still
run out of heap, sockets, request-body buffers, database waiters, or downstream capacity. Reactive systems face the same basic issue if an upstream producer outruns downstream demand or if unbounded
buffering is introduced into the pipeline.

The important architectural property is therefore **boundedness**, not thread count.

Ask:

- how many requests can be admitted?
- how much memory can each pending operation retain?
- which queues are bounded?
- which remote systems constrain concurrency?
- where does overload get rejected?
- how quickly does cancellation propagate?

Virtual threads make one resource—threads—much cheaper. They do not repeal queueing theory.

---

## Cancellation and timeouts

Reactive libraries tend to treat cancellation as a first-class signal. A subscriber can cancel a subscription, and well-designed operators propagate cancellation upstream. For streaming workloads this
is a major feature because stopping demand should stop unnecessary production.

In a synchronous thread-per-task model, cancellation is usually represented with thread interruption, task-scope cancellation, explicit timeout APIs, socket cancellation, or framework-specific request
cancellation. This can be simpler for isolated request/response calls but less compositional for complex streams.

The architectural requirement is the same in both cases: cancellation must reach the expensive operation.

A timeout that merely stops waiting at the outer HTTP layer while leaving a database query, HTTP call, or background computation running is not real resource cancellation. Reactive programming does
not guarantee correct cancellation automatically, and virtual threads do not guarantee it through interruption automatically; drivers and libraries must cooperate.

For ordinary service calls, structured concurrency plus bounded timeouts can provide a clear ownership model: child work belongs to the request and is cancelled when the scope fails or times out. For
long-lived streams, reactive cancellation semantics are often more natural because cancellation is already embedded in the stream protocol.

---

## Transactions become simpler in direct code

Transactions illustrate how concurrency style leaks into framework design.

In synchronous code, a transaction can often be modeled lexically:

===! ":fontawesome-brands-java: `Java`"

    ```java
    return transactionManager.inTx(() -> {
        var account = accounts.find(id);
        ledger.insert(...);
        accounts.update(...);
        return account;
    });
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    return transactionManager.inTx {
        val account = accounts.find(id)
        ledger.insert(...)
        accounts.update(...)
        account
    }
    ```

The transaction begins before the callback, remains active while the callback executes, and finishes when the callback returns or throws.

In a reactive system, the method may return a publisher immediately, while the actual database work happens later when someone subscribes. The transaction scope therefore cannot simply follow Java
method entry and exit. It has to follow subscription and asynchronous completion.

Reactive frameworks solve this, but the integration is more specialized because transaction lifetime is no longer equivalent to lexical method lifetime.

Virtual threads restore that equivalence for most ordinary code. This is one reason synchronous repositories and synchronous service contracts can simplify not only user code but framework internals.

---

## Observability: logical operations vs execution machinery

Both models can be fully observable with OpenTelemetry, but they require different instrumentation strategies.

Reactive tracing has to carry trace context through asynchronous operator chains and scheduler transitions. Instrumentation may need hooks into the reactive library so that the current span is
restored whenever a continuation runs.

With virtual threads, the logical operation naturally has a thread identity, but telemetry context still needs disciplined scoping. Kora 2 uses `ScopedValue`-backed OpenTelemetry context so that
`Span.current()` and `Context.current()` work inside framework-managed operations, including on virtual threads. When developers explicitly submit detached work to another executor, they must capture
and rebind the context.

This is a good example of what virtual threads simplify without making invisible. The common request path can behave like ordinary synchronous code, while unusual concurrency boundaries remain
explicit.

Operationally, virtual threads also improve the usefulness of traditional tools. A thread dump can represent logical tasks, a debugger can step through ordinary frames, and Java Flight Recorder can
expose virtual-thread events such as starts, ends, submissions, and problematic pinning.

Reactive systems have excellent observability tooling as well, but teams must learn to interpret operator graphs, scheduler names, assembly traces, and asynchronous causal chains. The cost is not
necessarily runtime performance; it is operational vocabulary and cognitive load.

---

## Where reactive programming is still objectively useful

The arrival of virtual threads does not eliminate the workloads Reactive Streams was designed for. There are several cases where reactive remains an objectively strong architectural fit.

###1 Continuous, demand-driven streams

If the application processes an ongoing stream whose size is unknown or effectively infinite, backpressure is not an incidental detail. It is part of the problem domain.

Examples include:

- market-data feeds;
- telemetry pipelines;
- change-data-capture streams;
- large event-processing graphs;
- continuously transformed broker streams;
- media or binary streaming;
- pipelines that join, buffer, window, debounce, sample, or merge live sources.

Reactive Streams gives these systems a standard vocabulary for demand, cancellation, completion, and errors. A virtual thread can certainly read and process a stream, but thread-per-task semantics
alone do not provide an equivalent demand protocol.

###2 End-to-end reactive ecosystems

If every important dependency already exposes reactive interfaces, forcing the application back into synchronous wrappers may add more complexity rather than remove it.

A system built around reactive database drivers, reactive messaging APIs, a reactive HTTP stack, and libraries whose composition primitives are publishers may be most coherent when it remains reactive
end to end.

Architecture should minimize semantic adapters. Converting publishers to blocking calls merely to claim a synchronous architecture is not inherently better.

###3 High-throughput stream transformation engines

Some applications are closer to dataflow engines than request/response services. Their natural abstraction is not “one thread handles one request”; it is “elements flow through a graph of operators.”

For these systems, operators such as merge, zip, window, buffer, throttle, sample, retry, concat, and switch may express the domain more directly than imperative loops and manually coordinated tasks.

###4 Network gateways and protocol proxies

A gateway that mostly moves bytes between sockets, performs lightweight routing, and manages huge numbers of long-lived connections can fit naturally on a non-blocking event-driven architecture. There
may be very little business call stack to preserve in the first place.

Virtual threads can also handle large connection counts, so this is not an automatic reactive win. But where the application is fundamentally a network state machine, event-driven programming may map
cleanly to the workload.

###5 Fine-grained demand propagation across many stages

If a downstream stage must dynamically tell multiple upstream stages how much more work it can accept, Reactive Streams already defines the mechanism. Rebuilding equivalent behavior manually with
semaphores and queues may produce a less composable system.

###6 Existing expertise and mature production systems

Architecture has migration cost. A mature reactive service with proven libraries, diagnostics, operational tooling, and a team fluent in the model should not be rewritten merely because virtual
threads exist.

Virtual threads change the default choice for new request/response services more strongly than they justify rewrites of healthy reactive systems.

---

## Where virtual threads are usually the simpler default

Virtual threads are particularly compelling when the application is a conventional backend service whose work is mostly request/response and I/O-bound:

- HTTP CRUD services;
- business APIs;
- services dominated by JDBC;
- orchestration services calling multiple downstream HTTP/gRPC systems;
- applications using mature blocking Java libraries;
- transactional services;
- applications where debuggability and straightforward control flow are high priorities;
- teams that do not otherwise need stream semantics.

These applications historically adopted reactive programming mainly because they needed concurrency without one expensive platform thread per request. When that constraint disappears, the asynchronous
type system can become optional rather than foundational.

This is the category Kora 2 is designed around.

Its HTTP request handlers use direct synchronous signatures. Request processing is placed on virtual threads. JDBC repositories remain synchronous. HTTP, data access, resilience, telemetry, and other
framework features are designed around the same direct programming model. Instead of supporting several competing concurrency styles, Kora chooses one application model and makes the framework
responsible for executing it efficiently.

That coherence matters more than whether any individual API is one line shorter.

---

## Kora 2 as a concrete virtual-thread-first architecture

Kora 2's architecture can be summarized as a separation between the network runtime and the application runtime.

At the transport layer, Undertow/XNIO uses a small number of I/O threads. These threads should stay focused on networking. Kora dispatches application request handling to a virtual thread. From that
point, controllers, service code, repositories, mappers, interceptors, and blocking clients can execute using direct synchronous semantics.

A simplified request path looks like this:

```text
Socket
  |
  v
Undertow / XNIO I/O thread
  |
  | dispatch
  v
Request Virtual Thread
  |
  v
Kora generated HTTP handler
  |
  v
Controller
  |
  v
Service
  |
  +------> JDBC repository
  |
  +------> blocking HTTP/gRPC integration
  |
  +------> resilience / telemetry / validation
  |
  v
Response
```

Several design choices reinforce the model.

First, controller handlers return ordinary values rather than `CompletionStage`, `Future`, or reactive `Publisher` types. Second, JDBC repository contracts are synchronous and contain no reactive
signatures. Third, Kora's general documentation explicitly states that its application code is executed synchronously on virtual threads and that framework modules do not expose reactive or `suspend`
contracts. Fourth, telemetry context is integrated with `ScopedValue`, so the synchronous execution scope remains observable without relying on a traditional platform-thread identity.

The result is not simply “blocking Kora.” It is a framework where **blocking is an application-level semantic and virtual-thread parking is a runtime-level optimization**.

That distinction is the core of the architecture.

---

## Reactive and virtual threads can coexist—but boundaries matter

Real systems are rarely ideologically pure. A virtual-thread service may consume a reactive library. A reactive application may need a blocking SDK. Both are possible.

The danger is uncontrolled mixing.

### Reactive calling blocking code

If reactive code calls blocking code on an event loop, the event loop can stall. The blocking work must be moved to a worker scheduler or another execution mechanism.

```text
event loop
  -> dispatch to worker / VT
      -> blocking SDK
  -> continue reactive pipeline
```

This is a legitimate boundary, but it should be explicit and observable.

### Virtual-thread code calling reactive code

A virtual thread can subscribe to an asynchronous source and wait for completion, but doing so merely to convert every reactive API into a blocking one may destroy useful streaming or cancellation
semantics. If the dependency naturally produces a stream, preserving the stream may be better.

The engineering principle is to choose a dominant model and isolate adapters at clear boundaries. A codebase where every layer repeatedly converts between synchronous and reactive types gets the
complexity of both models and the conceptual clarity of neither.

Kora 2 deliberately avoids that ambiguity at the framework-contract level by making synchronous virtual-thread execution the default application model.

---

## The real trade-off: explicit control flow vs explicit flow control

The deepest comparison can be expressed as a trade between two kinds of explicitness.

Virtual-thread architectures make **control flow** explicit:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var user = users.find(id);
    var balance = balances.get(user.accountId());
    var risk = riskClient.check(user);
    return buildResponse(user, balance, risk);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val user = users.find(id)
    val balance = balances.get(user.accountId)
    val risk = riskClient.check(user)
    return buildResponse(user, balance, risk)
    ```

The order of operations is visible directly in the language.

Reactive architectures make **flow control** explicit:

===! ":fontawesome-brands-java: `Java`"

    ```java
    users.find(id)
        .flatMap(user ->
            Mono.zip(
                balances.get(user.accountId()),
                riskClient.check(user)
            ).map(tuple -> buildResponse(user, tuple.getT1(), tuple.getT2()))
        );
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    users.find(id)
        .flatMap { user ->
            Mono.zip(
                balances.get(user.accountId),
                riskClient.check(user)
            ).map { tuple -> buildResponse(user, tuple.t1, tuple.t2) }
        }
    ```

The pipeline explicitly models asynchronous composition and can naturally carry demand and cancellation.

For ordinary business services, control flow is usually the more important abstraction. For streaming systems, flow control may be the more important abstraction.

That is a better basis for architecture selection than “reactive is faster” or “virtual threads are simpler.”

---

## A decision framework for backend teams

When choosing between a reactive architecture and a virtual-thread-first architecture, ask questions about the workload rather than the fashion of the stack.

### Choose virtual threads as the default when:

1. The service is primarily request/response.
2. Most waits are JDBC, HTTP, RPC, filesystem, or other blocking-style I/O.
3. The domain is naturally expressed with ordinary method calls.
4. Backpressure is mostly resource-level concurrency control rather than stream-level demand propagation.
5. You benefit from the mature blocking Java ecosystem.
6. Transactions and exception propagation should remain lexical and direct.
7. Debugging, stack traces, and operational simplicity are important.
8. The team wants concurrency to be explicit only where actual parallelism is required.

### Prefer reactive when:

1. The domain is an ongoing stream rather than a finite request.
2. Demand propagation is a first-class requirement.
3. The application already has an end-to-end reactive dependency chain.
4. Operator-based stream transformations map directly to the business problem.
5. Cancellation must propagate through long-lived asynchronous pipelines.
6. The system is fundamentally an event-processing or network state machine.
7. The team already operates the reactive model successfully and a rewrite would bring little architectural benefit.

### Be cautious with both models when:

1. The workload is CPU-bound.
2. Concurrency is unbounded.
3. Downstream capacity is not explicitly modeled.
4. Timeouts exist only at the outermost layer.
5. Queues and buffers are unbounded.
6. Context disappears when work is handed to detached executors.
7. Blocking code accidentally runs on network event loops.
8. Virtual-thread pinning or reactive scheduler starvation is not monitored.

Those are system-design problems, not API-style problems.

---

## What does not change after Loom

Virtual threads are a major JVM change, but many backend engineering rules remain exactly the same.

You still need sensible timeouts. You still need bounded queues. You still need database connection limits. You still need bulkheads around fragile downstream systems. You still need to protect
CPU-heavy work. You still need cancellation. You still need overload behavior. You still need metrics around latency and saturation. You still need to understand what your libraries do under load.

What changes is that **a thread no longer has to be treated as the scarce resource around which the entire application architecture is designed**.

That is a profound shift because much of the complexity of reactive business applications came from preserving scarce threads across I/O waits. When a lightweight thread can represent a waiting
request directly, the architecture can move many concerns back to the level where they naturally belong:

- database capacity is controlled by the database pool;
- downstream concurrency is controlled at the downstream boundary;
- CPU work is controlled by CPU capacity;
- request execution is represented by a request thread;
- parallelism is introduced where the business operation is actually parallel;
- streaming uses streaming abstractions where streaming is actually the domain.

The concurrency model becomes less global.

---

## Conclusion

Reactive programming was not a mistake. It solved a real limitation of the pre-Loom JVM: large numbers of concurrently waiting operations could not economically be represented by large numbers of
platform threads. The reactive answer was to encode waiting, continuation, cancellation, and demand into asynchronous APIs and stream composition.

Virtual threads solve a large part of the same scalability problem at a different layer. Instead of asking every application API to expose asynchronous execution, the JVM can suspend a lightweight
thread while it waits and reuse the carrier for other work. That makes direct synchronous code viable again for high-concurrency I/O-bound services.

The architectural consequence is larger than replacing `Mono<T>` with `T`.

It changes repository design. It changes transaction boundaries. It changes stack traces. It changes context propagation. It changes how framework aspects are implemented. It changes where capacity
limits live. It changes how teams debug production failures. Most importantly, it allows **concurrency representation to stop dominating ordinary business APIs**.

Kora 2 takes that idea to its logical conclusion. Its framework contracts are synchronous, HTTP application work runs on virtual threads, JDBC remains a first-class direct database model, and reactive
or `suspend` signatures are intentionally absent from Kora modules. The network layer can remain asynchronous where asynchronous networking is useful, while the application layer stays synchronous
where direct control flow is useful.

Reactive programming still has a strong place: continuous streams, demand-driven pipelines, event-processing graphs, long-lived asynchronous flows, and systems whose ecosystem is already reactive end
to end. In those domains, backpressure and asynchronous composition are not implementation workarounds; they are useful abstractions in their own right.

The practical conclusion is therefore not “virtual threads beat reactive.” It is more precise:

> **Virtual threads remove the need to make ordinary request/response business code reactive merely to achieve high I/O concurrency. Reactive programming remains valuable when the problem itself is
reactive.**

That distinction is likely to define the next generation of JVM backend architecture more accurately than any benchmark chart.
