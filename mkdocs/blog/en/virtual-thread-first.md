---
title: Virtual Threads First — Why the Kora Framework Is Synchronous Again
description: Why the Kora Framework is virtual-thread-first — synchronous controllers, HTTP clients, and JDBC repositories without reactive types.
search:
  exclude: true
---
# Virtual Threads First: Why Kora 2 Is Synchronous Again

For more than a decade, high-concurrency server development on the JVM appeared to move in one direction: away from blocking code and toward asynchronous, reactive, event-driven programming. The argument was compelling. Traditional Java servers frequently assigned one operating-system thread to each active request. Threads were relatively expensive, thread pools were necessarily bounded, and blocking a thread while waiting for a database or another service meant that an expensive resource was doing no useful work. If a service needed to keep tens of thousands of requests in flight, the conventional thread-per-request model could become the limiting factor.

Reactive programming attacked that constraint by changing the programming model. Instead of letting a request occupy a thread while it waited, applications expressed work as callbacks, futures, streams, continuations, or coroutine state machines. A small number of event-loop or worker threads could then multiplex a much larger number of concurrent operations.

Project Loom changed the trade-off.

Virtual threads make it possible to retain the direct, sequential programming model of ordinary Java while allowing very large numbers of concurrent tasks. The important shift is not that blocking suddenly became free. It is that **blocking a virtual thread usually no longer means blocking the scarce operating-system thread that happens to execute it**.

The Kora Framework builds its concurrency model in Kora 2 around that distinction.

Its application-facing APIs are deliberately synchronous again. HTTP controllers return ordinary values. HTTP clients return responses directly. JDBC repositories use normal blocking JDBC contracts. Scheduled methods are ordinary methods. Kora's documentation explicitly states that application code is executed synchronously on virtual threads and that Kora modules do not expose reactive or Kotlin `suspend` contracts. For HTTP specifically, every request is dispatched to a virtual thread, so controllers, interceptors, mappers, client calls, and database calls can be written in a direct style without forcing asynchronous types through the entire application.

That does not mean Kora is returning to the old platform-thread-per-request architecture. It means Kora is returning to the **thread-per-request programming model** while replacing the expensive execution primitive underneath it.

The historical arc is therefore better described as:

```text
platform thread per request
        ↓
asynchronous / reactive multiplexing
        ↓
virtual threads
        ↓
thread per request programming model again
without platform thread per request cost
```

This distinction is the key to understanding why Kora 2 can be synchronous without simply repeating the scalability limitations that pushed the industry toward reactive programming in the first place.

---

## The original thread-per-request model was conceptually excellent

Traditional Java web programming was easy to understand because the execution model matched the structure of the business operation.

A request arrived, a thread was assigned to it, and the code executed from top to bottom:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public Order getOrder(long id) {
        var customer = customerRepository.findById(id);
        var order = orderRepository.findByCustomer(customer.id());
        var pricing = pricingClient.calculate(order);
        return order.withPricing(pricing);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun getOrder(id: Long): Order {
        val customer = customerRepository.findById(id)
        val order = orderRepository.findByCustomer(customer.id)
        val pricing = pricingClient.calculate(order)
        return order.withPricing(pricing)
    }
    ```

The stack told the story of the request. Exceptions propagated naturally. Local variables represented local state. `try/finally` expressed cleanup. Transactions could be scoped around ordinary method calls. Debuggers could stop on a line and show the entire logical operation. Profilers and thread dumps mapped reasonably well to what developers thought the program was doing.

The problem was not this programming model.

The problem was the implementation of `Thread`.

Historically, a Java `Thread` was essentially tied to an operating-system thread for its lifetime. Operating-system threads are not impossibly expensive, but they are expensive enough that creating hundreds of thousands of them is not a practical concurrency strategy. Each thread consumes memory for its stack and runtime metadata, the operating system must schedule it, and large runnable thread sets create context-switching and scheduling overhead.

Server frameworks therefore used thread pools.

Instead of creating unlimited threads, a server might have a few dozen or a few hundred worker threads:

```text
incoming requests
       ↓
+--------------------+
| worker thread pool |
|  T1 T2 T3 ... T200 |
+--------------------+
       ↓
business logic
```

That works very well until many of those workers spend their time waiting.

Consider a service that performs three network operations:

```text
request
  ↓
JDBC query       8 ms waiting
  ↓
HTTP call       40 ms waiting
  ↓
JDBC update      5 ms waiting
  ↓
response
```

The request may need only a small amount of actual CPU time, yet its worker thread remains occupied during every blocking call. If all 200 workers are waiting for remote systems, request 201 cannot begin application processing even if the CPU is almost idle.

This is the classic scalability problem summarized by Little's Law:

```text
concurrency ≈ throughput × latency
```

If a service processes 10,000 requests per second and each request remains in flight for 100 ms, roughly 1,000 requests must exist concurrently.

With slow downstream systems, long-tail latency, large fan-out, or many simultaneous connections, concurrency requirements can quickly exceed a comfortably sized platform-thread pool.

The direct programming model was attractive. The resource model underneath it was not.

---

## Reactive programming solved a real problem

It is easy to caricature reactive programming as unnecessary complexity introduced by framework authors. Historically, that is unfair.

Reactive and asynchronous server architectures addressed a concrete limitation: **waiting should not require holding one operating-system thread per operation**.

The basic idea is straightforward. Instead of writing:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var response = client.call();
    process(response);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val response = client.call()
    process(response)
    ```

and leaving the current thread blocked until the network responds, an asynchronous API initiates the operation and arranges for the continuation to run later:

```text
start request
    ↓
register continuation
    ↓
return thread to event loop
    ↓
network response arrives
    ↓
schedule continuation
```

A small number of threads can therefore manage a much larger number of concurrent sockets and requests.

This model is particularly natural at the transport level. Modern web servers, operating systems, and networking libraries already use readiness-based or completion-based I/O internally. Netty, Vert.x, Undertow, asynchronous HTTP clients, and database drivers can all avoid dedicating a platform thread to a socket that is merely waiting for bytes.

At sufficient concurrency, this is dramatically more resource-efficient than assigning a platform thread to every active operation.

The problem is that application code also had to become asynchronous.

Once a controller cannot block, everything below it must respect the same rule:

```text
HTTP handler
   ↓
service
   ↓
repository
   ↓
HTTP client
   ↓
driver
```

If the HTTP handler runs on an event loop and the repository performs a conventional blocking JDBC call, the database call blocks the event-loop thread itself. That can stall many unrelated requests handled by the same loop.

As a result, asynchronous execution semantics tend to propagate through API boundaries.

A Java application that once looked like this:

===! ":fontawesome-brands-java: `Java`"

    ```java
    User loadUser(long id)
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun loadUser(id: Long): User
    ```

might become:

===! ":fontawesome-brands-java: `Java`"

    ```java
    CompletionStage<User> loadUser(long id)
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun loadUser(id: Long): CompletionStage<User>
    ```

or:

===! ":fontawesome-brands-java: `Java`"

    ```java
    Mono<User> loadUser(long id)
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun loadUser(id: Long): Mono<User>
    ```

while Kotlin might use:

```kotlin
suspend fun loadUser(id: Long): User
```

That propagation is not accidental. It is how the type system tells the caller that the operation does not complete synchronously.

Reactive systems therefore solved platform-thread scarcity by making **asynchrony part of the programming model**.

---

## The cost of encoding concurrency into every API

Reactive programming can be elegant when the problem itself is naturally a stream or asynchronous pipeline. But for ordinary request/response business logic, the asynchronous type often describes the execution mechanism more than the domain.

Compare these contracts:

===! ":fontawesome-brands-java: `Java`"

    ```java
    Order findOrder(long id);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun findOrder(id: Long): Order
    ```

===! ":fontawesome-brands-java: `Java`"

    ```java
    CompletionStage<Order> findOrder(long id);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun findOrder(id: Long): CompletionStage<Order>
    ```

===! ":fontawesome-brands-java: `Java`"

    ```java
    Mono<Order> findOrder(long id);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun findOrder(id: Long): Mono<Order>
    ```

The first contract says what the method does.

The second and third also expose how completion is represented.

That difference spreads.

A synchronous call chain is ordinary composition:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var user = users.find(id);
    var account = accounts.find(user.accountId());
    return mapper.toResponse(user, account);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val user = users.find(id)
    val account = accounts.find(user.accountId)
    return mapper.toResponse(user, account)
    ```

A reactive chain may become something like:

===! ":fontawesome-brands-java: `Java`"

    ```java
    return users.find(id)
        .flatMap(user ->
            accounts.find(user.accountId())
                .map(account -> mapper.toResponse(user, account))
        );
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    return users.find(id)
        .flatMap { user ->
            accounts.find(user.accountId)
                .map { account -> mapper.toResponse(user, account) }
        }
    ```

For simple examples this is manageable. Real applications add error handling, tracing context, retries, transactions, timeouts, conditional branches, fan-out, partial failures, cleanup, and framework-specific operators. The execution model becomes another abstraction that every developer must understand.

The result can be a semantic gap between the business algorithm and its representation in code.

The synchronous algorithm is:

```text
load user
load account
combine
return
```

The reactive implementation may instead require reasoning about:

```text
subscription
publisher execution
scheduler selection
operator semantics
context propagation
cancellation
backpressure
error channels
thread hopping
```

None of those concepts are inherently bad. They are valuable when the application actually needs them. The architectural question is whether every repository lookup, HTTP client call, controller, and service method should be forced to express them merely because blocking an operating-system thread is too expensive.

Project Loom's answer is: increasingly, no.

---

## Loom changes the unit of concurrency

Virtual threads were finalized in JDK 21 by JEP 444. A virtual thread is still a `java.lang.Thread`, but unlike a platform thread it is not permanently tied to one operating-system thread.

The JVM can run many virtual threads on a much smaller set of platform threads called **carrier threads**.

Conceptually:

```text
Virtual threads

V1   V2   V3   V4   V5   V6   V7   V8   ...   V100000
 \    |   /     \    |   /     \    |
  \   |  /       \   |  /       \   |
   +------+       +------+       +------+
   | C1   |       | C2   |       | C3   |   carrier threads
   +------+       +------+       +------+
        \             |             /
         +-------------------------+
              operating system
```

A virtual thread is **mounted** on a carrier when it is executing Java code.

When the virtual thread reaches a supported blocking operation, the runtime can suspend that virtual thread, preserve its state, and unmount it from the carrier. The carrier is then available to run some other virtual thread.

Later, when the blocked operation can continue, the original virtual thread becomes runnable again and may be mounted on the same carrier or on a different one.

The application does not have to manually encode the continuation.

It can simply write:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var result = socket.read();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val result = socket.read()
    ```

The source code still looks blocking.

The **virtual thread** is blocked.

But the **carrier thread** can usually continue doing useful work elsewhere.

That is the central idea behind Loom.

---

## Blocking a virtual thread is not the same as blocking a carrier

The word *blocking* became overloaded during the reactive era, and this creates confusion when discussing virtual threads.

There are at least two different questions:

1. Is the **logical task** waiting?
2. Is the **platform thread executing that task** also forced to wait?

In the traditional model, these were normally the same thing.

```text
Platform thread T1
    ↓
blocking socket read
    ↓
T1 cannot execute anything else
```

With virtual threads, they can be separated:

```text
Virtual thread V1
    ↓
blocking socket read
    ↓
V1 waits

Carrier C1
    ↓
V1 unmounts
    ↓
C1 executes V2
```

So this statement is completely reasonable in a Loom application:

> This JDBC or HTTP operation blocks the request thread.

The important follow-up is:

> The request thread is a virtual thread.

Blocking the logical request is expected. The request cannot make progress until the database answers anyway. What matters for scalability is whether that waiting operation unnecessarily monopolizes a scarce carrier thread.

This distinction lets Java recover a useful property of the original thread-per-request model: **one logical concurrent activity can once again be represented by one thread**.

The thread becomes the continuation.

The stack becomes the state machine.

The JVM performs the multiplexing.

Application code no longer needs to manually transform the control flow into callbacks or publishers solely to avoid wasting operating-system threads.

---

## Loom did not make blocking free

Virtual threads remove one important cost of blocking, not every cost.

If 50,000 requests are simultaneously waiting for a database, the application still has 50,000 outstanding database operations conceptually. The database cannot necessarily execute them. The connection pool cannot necessarily support them. Memory is still consumed. Queues can still grow. Downstream systems can still collapse.

Virtual threads are therefore a **concurrency mechanism**, not a capacity-management mechanism.

This distinction matters enormously.

A platform-thread pool historically performed two jobs at once:

```text
1. execution
2. implicit concurrency limiting
```

A pool of 100 threads meant that no more than roughly 100 blocking operations could execute through that pool simultaneously.

Virtual threads intentionally remove the need for such a small execution pool. Creating 100,000 virtual threads can be entirely reasonable. But if all 100,000 immediately attempt a database query, the database is still finite.

Concurrency therefore needs to be limited at the resource that actually has limited capacity.

For JDBC, a connection pool already does this:

```text
100,000 virtual threads
          ↓
     Hikari pool
       50 connections
          ↓
       database
```

Only the available connections can issue queries concurrently. Other virtual threads can wait cheaply.

For an external service, the constraint may instead be:

- an HTTP connection pool;
- a semaphore;
- a rate limiter;
- a bulkhead;
- a queue;
- a circuit breaker;
- the downstream service's own concurrency limit.

This is a healthier conceptual model because execution capacity and resource capacity are no longer accidentally represented by the same thread pool.

---

## CPU-bound work is still CPU-bound

Virtual threads are designed primarily to improve the scalability of workloads that spend substantial time waiting.

They do not create additional CPU cores.

If 10,000 virtual threads all begin expensive JSON transformations, image processing, cryptography, compression, or numerical computation, the JVM still has only the actual available processors on which to execute them.

For CPU-bound workloads:

```text
more virtual threads ≠ more CPU
```

The carrier scheduler will multiplex runnable virtual threads over the available processors, but total CPU capacity is unchanged. Excess runnable work can increase latency through scheduling and contention.

This is why the correct mental model is not:

> Virtual threads make unlimited concurrency safe.

It is:

> Virtual threads make a very large number of mostly waiting concurrent tasks practical while preserving the ordinary thread programming model.

A well-designed Kora application should still understand which resources are scarce, which operations are CPU-heavy, and where explicit concurrency control is required.

---

## What Kora 2 actually chooses

Kora 2 does not merely support virtual threads as an optional optimization. Its public programming model is designed around them.

The Kora 2 documentation states:

> Kora executes application code synchronously on virtual threads.

It then makes the consequences explicit: controllers, HTTP clients, repositories, and scheduled tasks use ordinary blocking signatures, while reactive and `suspend` contracts are absent from Kora modules.

That design appears consistently across the framework.

### HTTP server

Kora's HTTP server documentation says request handling is synchronous and that every request is dispatched onto a virtual thread. Controllers, interceptors, and mappers return values directly rather than returning `CompletionStage`, Reactor types, or Kotlin `suspend` functions.

A controller therefore looks like ordinary Java:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class OrderController {

        private final OrderService service;

        public OrderController(OrderService service) {
            this.service = service;
        }

        @HttpRoute(method = HttpMethod.GET, path = "/orders/{id}")
        public Order get(@Path long id) {
            return service.get(id);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class OrderController(private val service: OrderService) {

        @HttpRoute(method = HttpMethod.GET, path = "/orders/{id}")
        fun get(@Path id: Long): Order {
            return service.get(id)
        }
    }
    ```

There is no asynchronous wrapper in the API because the framework provides concurrency by choosing the execution thread.

Kora uses Undertow underneath, and Undertow itself is built on asynchronous non-blocking I/O. Kora therefore does not reject event-driven transport internals. It places an important boundary between **transport implementation** and **application programming model**.

That separation can be illustrated as:

```text
socket / NIO / Undertow internals
            ↓
      request dispatch
            ↓
       virtual thread
            ↓
    synchronous handler
            ↓
   synchronous application
```

The networking layer can remain optimized around NIO while application code gets a direct blocking model.

Kora 2's Undertow configuration reflects this architecture. The old choice between a bounded blocking worker pool and optional virtual-thread execution is gone. The documentation notes that request handling no longer uses a bounded blocking pool; connections are dispatched to virtual threads, so the old `blockingThreads` and `virtualThreadsEnabled` settings are no longer present.

Virtual threads are not a mode layered beside another programming model. They are the execution assumption.

### HTTP clients

Kora 2's HTTP client contract is also synchronous:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpClient
    public interface PricingClient {

        @HttpRoute(method = HttpMethod.GET, path = "/prices/{id}")
        Price getPrice(@Path long id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpClient
    interface PricingClient {

        @HttpRoute(method = HttpMethod.GET, path = "/prices/{id}")
        fun getPrice(@Path id: Long): Price
    }
    ```

The result is returned directly.

The documentation explicitly states that all Kora HTTP client calls are synchronous and blocking and that concurrency is expected to come from virtual threads rather than from reactive or coroutine return types.

A `suspend` HTTP client method is rejected by the generator.

This is a major architectural statement. The framework is saying that asynchronous return types are no longer the default mechanism by which application code communicates scalability.

### JDBC repositories

The same idea appears in data access.

Kora 2 uses JDBC repositories with ordinary synchronous signatures:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface UserRepository extends JdbcRepository {

        @Query("SELECT id, name FROM users WHERE id = :id")
        @Nullable
        User findById(long id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface UserRepository : JdbcRepository {

        @Query("SELECT id, name FROM users WHERE id = :id")
        fun findById(id: Long): User?
    }
    ```

The documentation says directly that JDBC repository contracts are synchronous and that there are no asynchronous or reactive repository signatures.

Historically, a reactive architecture often pushed teams toward R2DBC or another non-blocking database API because JDBC would block an event-loop thread.

With a virtual-thread application model, conventional JDBC becomes architecturally viable again because waiting for JDBC no longer necessarily means consuming one platform worker for the entire wait.

This has significant consequences. JDBC is mature, extremely well understood, supported by a huge ecosystem, and maps directly onto the relational database interaction model used by most Java teams. Kora can therefore keep the thin abstraction it wants around JDBC rather than introducing a reactive data-access model merely to preserve event-loop liveness.

### Scheduling

Kora's scheduling APIs follow the same direction. Scheduled methods are ordinary methods, and Kotlin scheduled methods must not be `suspend`.

Again, the framework does not ask the application to encode asynchronous execution in the method signature.

---

## Kora is synchronous at the API boundary, not naive about I/O

Calling Kora 2 "blocking" without qualification can be misleading.

A better description is:

> Kora uses synchronous application contracts on top of a runtime designed to make waiting scalable.

The framework can use efficient transport implementations internally while deliberately presenting direct APIs to application code.

This is an important architectural separation.

Consider an HTTP request:

```text
network event
    ↓
Undertow / NIO
    ↓
Kora generated handler
    ↓
virtual thread
    ↓
controller
    ↓
service
    ↓
JDBC
    ↓
HTTP client
```

At several levels the implementation may use non-blocking I/O, readiness events, connection pools, or internal asynchronous machinery.

But the business operation remains one sequential call stack.

That is not a contradiction. It is exactly what virtual threads are intended to enable.

The runtime and libraries can optimize *how waiting is implemented* without requiring every business method to expose that mechanism.

---

## Why a blocking API becomes a good API again

Before Loom, a blocking API carried an implicit architectural warning:

> Calling this method may consume one scarce platform thread until completion.

That warning justified asynchronous APIs even when the domain operation itself was naturally request/response.

With virtual threads, the meaning changes.

A blocking method now primarily says:

> The current logical operation cannot continue until this result exists.

For many business operations, that is exactly the truth.

If an order cannot be priced until the pricing service responds, then the business flow is sequential:

```text
load order
    ↓
request price
    ↓
wait for price
    ↓
construct response
```

There is no conceptual benefit in pretending the dependency does not exist.

A synchronous signature expresses the dependency directly:

===! ":fontawesome-brands-java: `Java`"

    ```java
    Price getPrice(OrderId id);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun getPrice(id: OrderId): Price
    ```

The JVM can handle the scheduling consequence.

This restores several useful properties of ordinary Java.

### Control flow is visible in source code

A developer can read:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var user = users.find(id);
    var limits = limitsClient.get(user.id());
    var account = accounts.find(user.accountId());
    return decisionEngine.evaluate(user, limits, account);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val user = users.find(id)
    val limits = limitsClient.get(user.id)
    val account = accounts.find(user.accountId)
    return decisionEngine.evaluate(user, limits, account)
    ```

and understand the order of execution immediately.

There is less accidental framework vocabulary between the business algorithm and its implementation.

### Exceptions use the normal Java model

Failures can propagate through the stack naturally:

===! ":fontawesome-brands-java: `Java`"

    ```java
    try {
        return paymentClient.charge(command);
    } catch (PaymentRejectedException e) {
        ...
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    try {
        return paymentClient.charge(command)
    } catch (e: PaymentRejectedException) {
        ...
    }
    ```

There is no separate reactive error channel and no need to remember which operator transforms, resumes, wraps, or delays an error.

### Resource cleanup stays lexical

`try-with-resources` works exactly as intended:

===! ":fontawesome-brands-java: `Java`"

    ```java
    try (var resource = acquire()) {
        return use(resource);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    acquire().use { resource ->
        return use(resource)
    }
    ```

The code that acquires a resource and the code that releases it remain structurally connected.

### Transactions remain intuitive

A synchronous transaction can map onto an ordinary call scope:

===! ":fontawesome-brands-java: `Java`"

    ```java
    return executor.inTx(ctx -> {
        repository.updateBalance(...);
        repository.insertTransfer(...);
        return result;
    });
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    return executor.inTx { ctx ->
        repository.updateBalance(...)
        repository.insertTransfer(...)
        result
    }
    ```

There is no need to ensure that transaction context survives scheduler changes or reactive subscription boundaries.

### Debuggers see a logical stack

When a request is suspended in a blocking operation, its virtual-thread stack still represents the logical call chain.

This is one of Loom's most important engineering benefits. The runtime provides scalable concurrency without forcing the application to erase the stack that explains what it is doing.

---

## The stack is a feature, not overhead to eliminate

Reactive architectures often replace a deep blocking stack with an explicit continuation graph.

Loom takes a different position: a suspended stack can be an efficient representation of a suspended computation.

This has major consequences for observability and debugging.

Suppose a request is stuck waiting for a downstream service. In a thread-oriented model, the logical stack can look approximately like:

```text
OrderController.get()
  OrderService.load()
    PricingService.price()
      PricingHttpClient.getPrice()
        socketRead()
```

That stack answers a valuable question immediately:

> Why is this request waiting?

In callback-driven systems, the same logical causality may be split across tasks, queues, operators, or scheduler boundaries. Modern reactive tooling can reconstruct much of that context, but the application requires specialized observability to restore information that the original call stack provided naturally.

Virtual threads make thread-oriented diagnostics useful again even at high concurrency.

This aligns well with Kora's broader philosophy: generated code, direct contracts, explicit application structure, and minimal hidden runtime behavior.

---

## Virtual threads and structured concurrency

Removing reactive return types raises an obvious question:

> What if one request needs to perform several independent operations concurrently?

Sequential blocking code:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var profile = profileClient.get(userId);
    var recommendations = recommendationClient.get(userId);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val profile = profileClient.get(userId)
    val recommendations = recommendationClient.get(userId)
    ```

does not become parallel merely because each call runs on a virtual thread. The second call still starts after the first finishes.

The natural Loom-era answer is **structured concurrency**.

Kora's own documentation points to `StructuredTaskScope` for cases where several independent operations should run in parallel.

Conceptually:

===! ":fontawesome-brands-java: `Java`"

    ```java
    try (var scope = StructuredTaskScope.open(
            StructuredTaskScope.Joiner.<Object>awaitAllSuccessfulOrThrow())) {

        var profile = scope.fork(() -> profileClient.get(userId));
        var recommendations = scope.fork(() -> recommendationClient.get(userId));

        scope.join();

        return new Dashboard(
            profile.get(),
            recommendations.get()
        );
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    StructuredTaskScope.open(
        StructuredTaskScope.Joiner.awaitAllSuccessfulOrThrow<Any>()
    ).use { scope ->

        val profile = scope.fork<Any> { profileClient.get(userId) }
        val recommendations = scope.fork<Any> { recommendationClient.get(userId) }

        scope.join()

        return Dashboard(
            profile.get(),
            recommendations.get()
        )
    }
    ```

The important idea is not the exact API version—structured concurrency is still evolving in the JDK—but the model.

The parent operation creates child tasks:

```text
request
   |
   +---- profile call
   |
   +---- recommendations call
   |
   +---- wait for both
   |
 response
```

The concurrent work remains lexically scoped to the request.

That is fundamentally different from turning the entire service layer into an unstructured collection of futures.

Structured concurrency attempts to make concurrent code obey the same reasoning principles as structured programming:

- child tasks belong to a parent scope;
- lifetime is bounded by that scope;
- cancellation can propagate coherently;
- failure handling is centralized;
- the parent waits for the children according to an explicit policy.

In other words, Kora's preferred model is not "everything must be sequential." It is:

> Keep the default API synchronous. Introduce concurrency explicitly where the business operation actually contains parallel work.

That is a much smaller conceptual surface than making every potentially waiting operation asynchronous.

---

## Reactive programming and virtual threads optimize different layers

It would be a mistake to claim that virtual threads make reactive programming obsolete.

They solve overlapping but not identical problems.

Reactive programming is not only about avoiding blocked platform threads. Reactive Streams also defines demand signaling and backpressure between producers and consumers. Event-stream processing, infinite streams, high-volume pipelines, and systems where backpressure is a first-class domain requirement can still benefit from reactive abstractions.

Similarly, UI event systems, message pipelines, and some network infrastructure are naturally callback- or stream-oriented.

Virtual threads are especially compelling for **task-oriented server workloads**:

```text
receive request
perform finite sequence of operations
produce response
```

That describes a large fraction of backend business services.

Kora is deliberately optimized for that class of software.

The design decision is therefore not:

```text
reactive = bad
virtual threads = good
```

It is closer to:

```text
Do not force a stream-oriented or asynchronous programming model
onto ordinary request/response business code merely to solve
platform-thread scarcity.
```

When the problem really is a stream, a stream abstraction may still be appropriate.

When the problem is a transaction, RPC call, repository lookup, or request handler, a normal method is often the more faithful abstraction.

---

## Kora 2 removes the dual-programming-model problem

Frameworks that evolved through the reactive transition often support several execution models simultaneously.

A single ecosystem may offer:

```text
blocking MVC
reactive HTTP
JDBC
reactive SQL
Future / CompletionStage
Reactor
Kotlin suspend
Kotlin Flow
worker pools
event loops
virtual threads
```

Supporting multiple styles can be valuable for compatibility, but it also expands the architectural state space.

Teams must decide:

- Which controller model should we use?
- Can this repository be called from this thread?
- Is this interceptor allowed to block?
- Which scheduler is active here?
- Do we need `publishOn` or `subscribeOn`?
- Is the transaction context preserved?
- Can this library be called from a coroutine?
- Are we on an event loop or worker thread?
- Should this method return `Mono<T>`, `CompletionStage<T>`, `T`, or be `suspend`?
- What happens when blocking and reactive components meet?

Kora 2 chooses to collapse much of that matrix.

For ordinary framework modules, the answer is synchronous:

```text
HTTP controller     → T
HTTP client         → T
repository          → T
scheduled method    → ordinary method
```

The execution platform supplies virtual threads.

This matters beyond syntax. A framework with one concurrency model can make stronger assumptions throughout its generated code, telemetry, interceptors, transactions, tests, documentation, and examples.

The framework becomes more coherent because application code does not need to choose a concurrency dialect at every boundary.

---

## Kotlin becomes simpler too

Kotlin coroutines provide an excellent concurrency model, especially in ecosystems designed around suspending APIs. But they also introduce a second concurrency abstraction alongside Java threads.

A Kotlin backend can otherwise end up reasoning simultaneously about:

```text
Java platform threads
virtual threads
coroutines
CoroutineContext
Dispatchers
suspend boundaries
structured coroutine scopes
ThreadLocal propagation
blocking libraries
```

Kora 2 deliberately avoids requiring that dual model in its framework contracts.

A Kotlin controller remains:

```kotlin
@Component
@HttpController
class OrderController(
    private val service: OrderService
) {

    @HttpRoute(method = HttpMethod.GET, path = "/orders/{id}")
    fun get(@Path id: Long): Order {
        return service.get(id)
    }
}
```

An HTTP client remains:

```kotlin
@HttpClient
interface PricingClient {

    @HttpRoute(method = HttpMethod.GET, path = "/prices/{id}")
    fun getPrice(@Path id: Long): Price
}
```

The runtime concurrency primitive is the JVM thread abstraction that Java and Kotlin already share.

This has a practical organizational advantage: Java and Kotlin services can follow the same architecture. A Java developer does not need to learn a coroutine-specific version of every framework module, and a Kotlin developer does not need to decide whether each boundary should be thread-blocking or suspending.

Kotlin remains useful for its language features without requiring coroutines to become the framework's execution model.

---

## Why this fits Kora's "thin abstractions" philosophy

Kora's landing page emphasizes thin abstractions around familiar technologies such as JDBC, HTTP, Kafka, and gRPC.

Virtual threads reinforce that philosophy.

Without Loom, a framework targeting very high concurrency had an incentive to wrap technologies in asynchronous framework-specific representations:

```text
your code
   ↓
framework async type
   ↓
framework operators
   ↓
adapter
   ↓
underlying technology
```

With virtual threads, Kora can stay closer to the original API:

```text
your code
   ↓
small Kora abstraction
   ↓
JDBC / HTTP / library
```

That reduces the semantic distance between the application and the technology underneath it.

A JDBC problem can be investigated as a JDBC problem.

An HTTP problem can be investigated as an HTTP problem.

A stack trace usually resembles the source code.

A generated client or repository is still ordinary Java/Kotlin code.

The concurrency strategy does not need to infect every abstraction.

This is especially important for a framework whose stated goals include transparency and compile-time generation. Virtual threads let Kora simplify the runtime model at the same time that compile-time processing simplifies the framework machinery.

---

## Why it fits compile-time generation

Kora performs dependency wiring, HTTP handler generation, repository generation, mapping, AOP, and other framework work at compile time.

Its virtual-thread-first approach complements that architecture because both decisions remove runtime indirection for different reasons.

Compile-time generation removes framework machinery such as:

- runtime reflection;
- dynamic proxies;
- runtime graph discovery;
- generic reflective dispatch.

Virtual threads remove application-level concurrency machinery that would otherwise be required to avoid blocking platform threads:

- callback plumbing;
- reactive wrappers around ordinary calls;
- scheduler switching for basic request processing;
- coroutine contracts across every framework boundary.

The result is an application whose runtime path can be surprisingly conventional:

```text
generated HTTP handler
        ↓
controller method
        ↓
service method
        ↓
generated JDBC repository
        ↓
JDBC driver
```

The important runtime sophistication is still present, but it has moved into the JVM and the generated infrastructure instead of being expressed repeatedly in business code.

That is a recurring Kora design pattern:

> Put complexity where it can be implemented once and understood clearly, rather than requiring every application method to participate in it.

---

## Carrier threads: the detail developers must understand

Virtual threads simplify application code, but developers should still understand the carrier model because it explains the remaining failure modes.

A virtual thread executes while mounted on a carrier.

If the virtual thread performs a supported blocking operation, it can usually unmount:

```text
V1 mounted on C1
       ↓
blocking I/O
       ↓
V1 parked
       ↓
V1 unmounted
       ↓
C1 free
```

This is the desirable case.

However, not every kind of blocking can always be transformed into a cheap virtual-thread park. Operations involving native code, foreign-function calls, some operating-system interactions, or JVM internals may keep the carrier occupied.

That is why the correct production question is not merely:

> Are we using virtual threads?

It is:

> Do the libraries and blocking operations used by our hot paths behave well on virtual threads?

This is particularly important when integrating native libraries or unusual drivers.

The JDK provides JFR events and virtual-thread diagnostics to help investigate situations where virtual threads remain pinned to carriers.

---

## An important JDK 24+ correction: `synchronized` is no longer the old Loom trap

Many early virtual-thread articles repeat this rule:

> Never block inside `synchronized`, because the virtual thread will pin its carrier.

That advice described the early Loom implementation but is outdated for Kora 2's JDK baseline.

JEP 491, delivered in JDK 24, changed the JVM so virtual threads can generally unmount while holding Java monitors or waiting to acquire them. Kora 2 RC1 requires JDK 25, so ordinary `synchronized` usage is not automatically the virtual-thread scalability hazard it was on JDK 21.

This is an important example of why virtual-thread guidance must be tied to a concrete JDK version.

On JDK 25, the remaining pinning concern is primarily around native methods and foreign-function calls rather than ordinary Java monitor ownership.

That does not mean synchronization cannot hurt scalability. Lock contention is still lock contention. If thousands of virtual threads contend for the same monitor, they still serialize around that resource.

The distinction is:

```text
contention problem
        ≠
carrier pinning problem
```

Virtual threads do not remove bad locking architecture. JEP 491 removes an implementation limitation that previously made certain synchronized blocking regions consume carriers unnecessarily.

---

## Database pools become clearer, not unnecessary

A common misconception is that virtual threads make connection pools obsolete.

They do not.

A database connection is not merely a workaround for thread cost. It is a scarce database-side resource.

Suppose an application can create 100,000 virtual threads but the database is healthy with only 50 active connections.

The correct architecture can be:

```text
100,000 possible request virtual threads
               ↓
        connection pool
          max = 50
               ↓
           database
```

A virtual thread that waits for a connection can park cheaply.

This is actually a clean separation of concerns:

- virtual threads represent concurrent application tasks;
- the connection pool represents database capacity.

Under the old model, teams sometimes tuned a worker pool partly to prevent too many calls from reaching the database. With virtual threads, resource-specific controls become more explicit.

Kora's JDBC-first design fits naturally into this model because JDBC connection pooling remains a meaningful form of backpressure even though request execution no longer needs a small worker-thread pool.

---

## HTTP connection pools still matter

The same rule applies to outbound HTTP.

Virtual threads make it cheap to have many callers waiting for responses, but they do not grant an external service infinite capacity.

If a Kora service suddenly launches 20,000 parallel requests to the same dependency, possible bottlenecks include:

- available TCP connections;
- HTTP/2 stream limits;
- remote server worker capacity;
- network bandwidth;
- TLS cost;
- rate limits;
- queueing latency;
- retry amplification.

A well-designed client stack therefore still needs connection management, timeouts, retries used carefully, circuit breakers, and sometimes explicit concurrency limits.

Virtual threads remove the need for **thread scarcity to be the main concurrency control**.

They do not remove the need for concurrency control itself.

---

## Timeouts become even more important

Cheap waiting can make it easier to tolerate many blocked operations, but cheap waiting is still waiting.

A virtual thread stuck forever on a broken downstream call consumes less execution capacity than a platform thread would, but it still represents:

- an unfinished request;
- retained application state;
- retained buffers or objects;
- a client connection;
- possibly a database transaction;
- telemetry state;
- user-visible latency.

Timeouts therefore remain a first-class production requirement.

Virtual threads should change this mental model:

```text
blocking is expensive because threads are expensive
```

into:

```text
blocking is acceptable when waiting is semantically necessary,
but waiting must still be bounded by system policy
```

That is a much more accurate way to reason about distributed systems.

---

## Retries can still create concurrency explosions

Reactive or synchronous, retries are dangerous when a dependency is already failing.

Virtual threads can make the execution cost of a large number of waiting retries smaller, which is useful, but that does not protect the dependency.

Imagine:

```text
10,000 requests
× 3 retry attempts
= up to 30,000 downstream attempts
```

The fact that those attempts use lightweight virtual threads does not make the downstream system capable of serving them.

Kora's resilience mechanisms—timeouts, retries, circuit breakers, fallbacks—remain essential because Loom solves local scheduling overhead, not distributed-system failure dynamics.

Virtual threads simplify the code that uses these policies. They do not replace the policies.

---

## ThreadLocals become useful again—but should still be used deliberately

Reactive systems complicated `ThreadLocal` because a logical request could move across many worker threads. Frameworks therefore introduced explicit context propagation mechanisms.

Virtual threads restore a stronger relationship between a logical operation and its `Thread`.

Each virtual thread has its own thread-local state, independent of the carrier thread. A request can move between carriers while preserving the identity and thread-local state of the virtual thread itself.

This makes familiar thread-scoped techniques more viable again.

However, virtual threads can exist in very large numbers, so storing heavy objects in thread-local state can become expensive. A design that was harmless with 100 worker threads may be costly with 100,000 virtual threads.

The rule becomes:

> Thread-local context is semantically convenient again, but its per-thread memory cost matters more.

Modern Java also offers scoped values as a structured alternative for some context-propagation use cases.

The broader point remains: Loom lets request context follow the logical thread without requiring an application-wide reactive context abstraction.

---

## "Do not pool virtual threads"

Platform threads are expensive enough that applications historically reused them in pools.

Virtual threads are intended to be cheap enough that they are generally created per task.

This difference is fundamental.

The old model:

```text
requests
   ↓
fixed pool of reusable worker threads
   ↓
tasks queue behind workers
```

The Loom model:

```text
request
   ↓
new virtual thread
   ↓
task lifetime
   ↓
virtual thread ends
```

A virtual thread is closer to a request object than to a scarce worker.

Pooling virtual threads can accidentally reintroduce the very artificial concurrency bottleneck that Loom removes.

Resource limits should instead be expressed where the resource is actually finite: connection pools, semaphores, rate limits, queues, or service policies.

Kora's HTTP design follows this idea by dispatching requests to virtual threads rather than maintaining the old bounded pool of blocking request workers.

---

## What "Virtual Threads First" means architecturally

For Kora, virtual threads are more than a performance option. They shape API design.

A framework that treats virtual threads as an optional executor may retain all of its old reactive and blocking variants:

```text
blocking API
reactive API
coroutine API
virtual-thread mode
```

Kora 2 instead uses virtual threads as a reason to simplify the public model.

That produces a stronger architectural statement:

```text
Concurrency mechanism:
    virtual threads

Default application contract:
    synchronous methods

Parallel composition:
    explicit structured concurrency

Resource protection:
    pools / timeouts / resilience / limits

Transport internals:
    may remain asynchronous / NIO based
```

Each concern has a clear location.

That is arguably more important than the raw performance characteristics of virtual threads.

---

## The historical cycle is not actually a circle

At first glance the industry appears to have returned to where it started:

```text
thread per request
→ reactive
→ thread per request
```

But the final architecture is materially different from the first.

### Old thread-per-request

```text
1 request
≈
1 Java Thread
≈
1 OS thread
```

Scalability was bounded by operating-system threads.

### Reactive

```text
many requests
≈
small set of OS threads
+
explicit continuations
```

Scalability improved, but application code had to participate in multiplexing.

### Virtual-thread request model

```text
1 request
≈
1 virtual Java Thread

many virtual threads
≈
small set of carrier OS threads
```

The application regains the one-request-one-thread abstraction without returning to one-request-one-OS-thread resource cost.

So the trajectory is not a reversal.

It is an abstraction improvement.

The programming model returns to something simple because the runtime became sophisticated enough to support it efficiently.

---

## Why this matters for framework design

Before Loom, framework authors had to choose between two unattractive options for high concurrency.

### Option A: keep synchronous APIs

Advantages:

- simple Java;
- easy debugging;
- mature blocking libraries;
- straightforward transactions.

Disadvantage:

- every waiting request consumes a platform worker thread.

### Option B: expose asynchronous APIs

Advantages:

- excellent I/O scalability;
- small platform-thread footprint.

Disadvantages:

- concurrency model propagates throughout application APIs;
- blocking libraries require special handling;
- debugging and context propagation become more complex;
- teams must learn framework-specific asynchronous composition.

Virtual threads create a third option:

### Option C: synchronous APIs on lightweight threads

Advantages:

- direct code;
- large I/O concurrency;
- conventional library ecosystem;
- ordinary exceptions and stacks;
- easier integration with JDBC and blocking clients.

Trade-offs still exist, but the old forced choice between simple blocking code and scalable I/O is much weaker.

Kora 2 is designed around Option C.

---

## Why this can reduce framework code

Reactive support is not free for the framework either.

If every module supports several execution models, the framework may need variants for:

- synchronous handlers;
- future-based handlers;
- Reactor handlers;
- Kotlin coroutine handlers;
- context propagation;
- telemetry adapters;
- transactional wrappers;
- resilience wrappers;
- cache wrappers;
- generated code paths;
- test utilities.

AOP is especially affected. A timeout, retry, cache, tracing, or circuit-breaker aspect must understand the completion semantics of every supported return type.

With a synchronous baseline, an aspect can often remain conceptually simple:

```text
before
  ↓
call method
  ↓
after / catch
```

Virtual threads therefore have the potential to simplify framework implementation as well as application code.

This aligns with Kora's "one clear way" philosophy. A smaller set of execution models means fewer combinations to implement, document, test, and maintain.

---

## Why this can reduce application test complexity

Synchronous methods are easy to call in tests.

A service test can simply write:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var result = service.calculate(input);

    assertEquals(expected, result);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val result = service.calculate(input)

    assertEquals(expected, result)
    ```

There is no need to:

- subscribe;
- await a future;
- run a coroutine test scope;
- configure a scheduler;
- use a reactive test subscriber;
- reason about lazy versus eager execution.

Integration tests also resemble production code more closely because the same synchronous call path is exercised.

Kora already emphasizes rapid component and integration testing enabled by fast application startup. A synchronous execution model reinforces that feedback loop.

The value is not that asynchronous code is untestable. It is that asynchronous infrastructure no longer has to appear in tests for operations whose domain semantics are fundamentally synchronous.

---

## Why this can improve debugging

Consider an exception from a deeply nested service call.

In a synchronous call chain, the stack trace naturally records causality:

```text
Controller
  → Service
    → Repository
      → Driver
```

In asynchronous systems, logical causality may cross task boundaries. Libraries have invested heavily in assembly traces, coroutine stack recovery, context propagation, and debugger support to improve this situation, but these are compensating mechanisms.

Virtual threads let the JVM preserve the conventional stack-oriented model at much larger concurrency.

For Kora, that combines with generated source code in an especially useful way:

```text
request
  ↓
generated handler
  ↓
controller
  ↓
service
  ↓
generated repository/client
  ↓
real integration library
```

A developer can step through ordinary code rather than reconstructing hidden runtime machinery.

That is exactly the kind of transparency Kora's compile-time architecture is designed to provide.

---

## Why this can improve observability

Observability is fundamentally about reconstructing causality.

Tracing asks:

```text
what operation caused this operation?
```

Logs ask:

```text
what happened during this request?
```

Metrics ask:

```text
where is time and capacity being consumed?
```

A thread-per-task model gives observability systems a natural execution unit.

This does not eliminate the need for OpenTelemetry context propagation—distributed calls still cross process boundaries, and concurrent child tasks still need context—but local control flow becomes easier to associate with a logical request.

Kora's observability modules can therefore instrument direct synchronous calls without needing a separate instrumentation strategy for Reactor chains, futures, and coroutine continuations in every module.

Again, the benefit comes from reducing the number of concurrency dialects the framework must understand.

---

## Virtual threads make familiar Java libraries more strategically valuable

The Java ecosystem contains decades of mature blocking APIs.

Examples include:

- JDBC drivers;
- classic HTTP clients;
- file APIs;
- many SDKs;
- database libraries;
- RPC clients;
- enterprise integrations.

During the reactive era, using such libraries inside an event-loop architecture often required:

```text
event loop
   ↓
dispatch to worker pool
   ↓
blocking library
   ↓
return to event loop
```

or replacing the library with a non-blocking equivalent.

Virtual threads change the cost/benefit calculation.

If the blocking library behaves well with virtual threads, the application may be able to use it directly while retaining high request concurrency.

That makes ecosystem maturity valuable again.

Kora's decision to center JDBC rather than maintain parallel JDBC and reactive database worlds is a good example. Instead of asking whether every integration has a bespoke reactive driver, the framework can ask whether the established Java API works correctly and efficiently on virtual threads.

This can significantly reduce integration complexity.

---

## But compatibility must be measured, not assumed

"Blocking API" does not automatically mean "virtual-thread friendly."

A library might:

- perform long native calls;
- hold global locks;
- hide its own small blocking pool;
- use thread-local caches with large memory footprints;
- serialize work internally;
- depend on thread identity in unexpected ways;
- perform CPU-heavy work while callers assume it is I/O-bound.

Virtual threads cannot repair those architectural constraints.

This makes production diagnostics important.

Teams should measure:

- carrier-thread utilization;
- virtual-thread pinning events;
- downstream queueing;
- database-pool wait time;
- HTTP-pool saturation;
- CPU saturation;
- allocation rate;
- tail latency;
- retry volume.

The virtual-thread model simplifies application code, but it does not absolve the system from performance engineering.

---

## Blocking can be the more honest abstraction

One of the strongest arguments for Kora's design is semantic rather than performance-related.

A method that performs an RPC often *is* a blocking dependency in the business operation.

Suppose this code cannot produce a result until fraud scoring completes:

===! ":fontawesome-brands-java: `Java`"

    ```java
    FraudScore score = fraudClient.score(payment);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val score: FraudScore = fraudClient.score(payment)
    ```

Representing the call as:

===! ":fontawesome-brands-java: `Java`"

    ```java
    Mono<FraudScore>
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    Mono<FraudScore>
    ```

does not make the business dependency asynchronous. It only changes how the waiting is represented.

The payment operation still cannot complete until the fraud score exists.

Virtual threads let the implementation express that truth directly without necessarily paying one platform thread for the wait.

This is why Loom can be viewed as an abstraction repair.

It lets the source code describe logical dependencies rather than scheduling mechanics.

---

## The effect on service-layer API design

Once framework boundaries are synchronous, service APIs become much cleaner.

A Kora service can expose domain-oriented methods:

===! ":fontawesome-brands-java: `Java`"

    ```java
    interface CheckoutService {
        Receipt checkout(CartId cartId);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface CheckoutService {
        fun checkout(cartId: CartId): Receipt
    }
    ```

rather than transport-oriented concurrency types:

===! ":fontawesome-brands-java: `Java`"

    ```java
    interface CheckoutService {
        Mono<Receipt> checkout(CartId cartId);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface CheckoutService {
        fun checkout(cartId: CartId): Mono<Receipt>
    }
    ```

or:

===! ":fontawesome-brands-java: `Java`"

    ```java
    interface CheckoutService {
        CompletionStage<Receipt> checkout(CartId cartId);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface CheckoutService {
        fun checkout(cartId: CartId): CompletionStage<Receipt>
    }
    ```

This creates a stronger separation between domain contracts and execution mechanics.

It also makes services easier to reuse from:

- HTTP controllers;
- Kafka consumers;
- scheduled jobs;
- tests;
- command-line tools;
- other components.

The service method does not care whether its caller came from an HTTP request or a scheduled task. It is simply invoked on a thread appropriate to the surrounding runtime.

That is classic application architecture, made scalable again by the JVM.

---

## The effect on code review and maintenance

A direct call chain is easier to review because control flow is explicit.

A reviewer can ask:

```text
What can fail?
What can block?
What is sequential?
What is parallel?
Where is the transaction?
Where is the timeout?
```

without simultaneously interpreting a chain of scheduler and composition operators.

This is especially useful for large teams where not every developer is an expert in the concurrency framework.

It also reduces the chance of accidental errors such as:

- performing blocking work on an event loop;
- forgetting to subscribe;
- switching schedulers incorrectly;
- losing context;
- composing nested reactive types incorrectly;
- using the wrong coroutine dispatcher;
- mixing incompatible cancellation semantics.

Kora's compiler already validates framework structure aggressively. A simpler execution model further reduces the number of runtime mistakes that the compiler cannot easily detect.

---

## The effect on onboarding

A Java developer joining a Kora 2 service can rely heavily on ordinary JVM knowledge.

They need to understand virtual threads, but they do not need to learn an entirely separate programming style before reading basic business code.

The conceptual path is:

```text
Java/Kotlin methods
        ↓
ordinary call stacks
        ↓
virtual threads provide concurrency
```

rather than:

```text
Java/Kotlin
   +
reactive stream model
   +
scheduler model
   +
framework integration rules
```

For organizations with many services and developer rotation between teams, that reduction in required context can be more valuable than small benchmark differences.

A concurrency model is not only a runtime choice. It is a training and maintenance cost paid by every engineer who touches the system.

---

## The effect on AI-assisted development

The same properties that help human developers also help code-generating and code-analyzing agents.

An AI model is more likely to reason correctly about:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var user = users.find(id);
    var account = accounts.find(user.accountId());
    return mapper.map(user, account);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val user = users.find(id)
    val account = accounts.find(user.accountId)
    return mapper.map(user, account)
    ```

than about a framework-specific chain whose correctness depends on subtle scheduler, subscription, context, and lifecycle semantics.

This does not mean an AI cannot write reactive code. It means the search space is larger.

Kora 2 narrows the execution model:

```text
ordinary method
ordinary return type
ordinary exception
ordinary generated source
virtual thread underneath
```

The compiler then checks the structural parts that Kora can validate.

That combination—simple source semantics plus strong compile-time feedback—is particularly suitable for iterative agent-driven development.

---

## When should Kora developers still think explicitly about concurrency?

Virtual threads allow developers to ignore many scheduling details, but not all concurrency.

There are several cases where concurrency should still be designed explicitly.

### Parallel fan-out

If a request needs three independent remote calls and latency matters, execute them concurrently using structured concurrency rather than sequentially.

### Shared mutable state

Virtual threads are still threads. Data races, visibility rules, locks, and atomicity still matter.

### Scarce downstream resources

Use connection pools, rate limits, semaphores, bulkheads, and other capacity controls.

### CPU-heavy work

Do not assume more virtual threads increase CPU throughput.

### Long native calls

Investigate carrier pinning and native integration behavior.

### Streaming

If a problem is fundamentally an unbounded or demand-driven stream, a streaming abstraction may still be better than collecting everything into a blocking request/response API.

### Cancellation

Distributed cancellation remains a system concern. Structured concurrency and interruption can help locally, but external calls and libraries must cooperate correctly.

The goal is not to eliminate concurrency reasoning.

It is to ensure that concurrency appears where the system genuinely needs it rather than being encoded into every method signature.

---

## A better mental model for blocking in Kora 2

In older high-concurrency Java architectures, developers were often taught:

> Blocking is bad.

That rule was useful but imprecise.

A better Kora 2 rule is:

> **Blocking a virtual thread is usually fine. Blocking a scarce carrier or an event-loop thread is not. Overloading a finite downstream resource is still not fine.**

That separates three different problems:

```text
logical waiting
    ↓
usually acceptable on virtual threads

carrier / event-loop occupation
    ↓
can reduce runtime scalability

resource saturation
    ↓
can overload the database / service / CPU
```

Once these are separated, system design becomes clearer.

---

## Kora's concurrency stack

The Kora 2 architecture can be summarized in layers.

```text
┌──────────────────────────────────────────────┐
│              Application Code                │
│ controllers / services / repositories        │
│ ordinary synchronous Java/Kotlin             │
├──────────────────────────────────────────────┤
│            Kora Generated Layer              │
│ handlers / clients / repositories / AOP      │
│ compile-time generated, strongly typed       │
├──────────────────────────────────────────────┤
│             Virtual Threads                  │
│ one lightweight thread per logical task      │
├──────────────────────────────────────────────┤
│              Carrier Threads                 │
│ small set of platform threads scheduled      │
│ by the JVM                                   │
├──────────────────────────────────────────────┤
│          Transport / Driver Layer            │
│ Undertow / NIO / JDBC / HTTP libraries       │
├──────────────────────────────────────────────┤
│            Operating System                  │
└──────────────────────────────────────────────┘
```

The key design boundary is between the application layer and the execution machinery.

Application code sees direct methods.

The runtime handles multiplexing.

---

## From colored functions back to ordinary functions

Asynchronous ecosystems sometimes use the term **function coloring** to describe APIs where asynchronous functions have a different type and composition model from synchronous functions.

For example:

```text
T
Future<T>
Mono<T>
suspend T
```

Once one function becomes "colored," callers often need to adopt the same color.

A reactive repository encourages a reactive service, which encourages a reactive controller.

A suspending client encourages a suspending service, which encourages a suspending controller.

Loom reduces this pressure because a waiting call can remain an ordinary call.

Kora 2 takes advantage of that possibility aggressively.

Its position is effectively:

> If a function conceptually returns `T`, let it return `T`. Let the execution environment solve the waiting problem.

That is one of the deepest architectural consequences of virtual threads.

---

## What Kora gives up by making this choice

Every architectural simplification removes options.

By not exposing reactive and `suspend` contracts across its core modules, Kora 2 is less suitable for teams that specifically want their whole application architecture to be built around Reactor or coroutine APIs.

A team may prefer reactive composition because:

- its domain is heavily stream-oriented;
- it already has a large Reactor codebase;
- backpressure is central to its application design;
- it relies on reactive libraries end-to-end;
- its developers are deeply experienced with that model.

Likewise, a Kotlin organization may intentionally standardize on coroutines as its universal concurrency abstraction.

Kora 2's design does not attempt to satisfy every such preference.

That is consistent with Kora's broader philosophy: fewer programming models, fewer competing abstractions, and one opinionated path optimized for ordinary server-side services.

The benefit is coherence.

The cost is reduced pluralism.

That is a deliberate framework trade-off rather than an accidental limitation.

---

## Why "synchronous again" is the important phrase

The word **again** matters because Kora 2's synchronous design is not based on ignoring the history of reactive systems.

It is based on the fact that the underlying JVM changed.

Before Loom:

```text
simple synchronous code
        ↕
high I/O concurrency
```

was often a real trade-off.

After Loom, that trade-off is significantly reduced.

Kora can therefore revisit the original direct programming model with a different execution substrate.

The framework is not arguing that the industry wasted time exploring asynchronous systems. Those systems identified a genuine runtime limitation and demonstrated the value of multiplexing many concurrent operations over few OS threads.

Loom internalizes much of that multiplexing into the JVM.

What used to require an application-level state machine can often become a JVM-managed virtual thread.

That is progress precisely because the lessons of reactive systems have moved down the stack.

---

## The deeper architectural lesson

The history of server concurrency can be read as a sequence of where the continuation lives.

### Platform-thread era

The continuation is represented by an OS-backed Java thread.

```text
continuation = platform thread + stack
```

### Reactive era

The continuation is represented explicitly in application/library objects.

```text
continuation = callback / future / publisher state
```

### Loom era

The continuation is represented again by a Java thread and stack, but the JVM can suspend it cheaply.

```text
continuation = virtual thread + stack
```

This explains why source code becomes synchronous again without forfeiting scalable multiplexing.

The continuation never disappeared. It simply moved between layers.

Kora 2 chooses the version where the JVM owns that complexity.

---

## A practical Kora 2 request

Consider a typical endpoint:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class OrderService {

        private final OrderRepository orders;
        private final CustomerClient customers;
        private final FraudClient fraud;

        public OrderService(
            OrderRepository orders,
            CustomerClient customers,
            FraudClient fraud
        ) {
            this.orders = orders;
            this.customers = customers;
            this.fraud = fraud;
        }

        public OrderView get(long orderId) {
            var order = orders.findById(orderId);
            var customer = customers.get(order.customerId());
            var score = fraud.score(customer, order);

            return new OrderView(order, customer, score);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class OrderService(
        private val orders: OrderRepository,
        private val customers: CustomerClient,
        private val fraud: FraudClient
    ) {

        fun get(orderId: Long): OrderView {
            val order = orders.findById(orderId)
            val customer = customers.get(order.customerId)
            val score = fraud.score(customer, order)

            return OrderView(order, customer, score)
        }
    }
    ```

At the source level, this is conventional blocking Java.

At runtime, the request may behave approximately like:

```text
virtual thread V42 starts
        ↓
orders.findById()
        ↓
wait for JDBC
        ↓
V42 parks / carrier reused
        ↓
database responds
        ↓
V42 resumes
        ↓
customers.get()
        ↓
wait for HTTP
        ↓
V42 parks / carrier reused
        ↓
response arrives
        ↓
V42 resumes
        ↓
fraud.score()
        ↓
...
        ↓
return response
        ↓
V42 ends
```

The application sees one sequential operation.

The JVM sees multiple periods during which the carrier can be used for other work.

That is the practical meaning of Kora's virtual-thread-first model.

---

## And when the calls are independent

If customer data and fraud metadata can be loaded independently, the service can introduce concurrency deliberately:

===! ":fontawesome-brands-java: `Java`"

    ```java
    try (var scope = StructuredTaskScope.open(
            StructuredTaskScope.Joiner.<Object>awaitAllSuccessfulOrThrow())) {

        var customerTask =
            scope.fork(() -> customers.get(order.customerId()));

        var fraudTask =
            scope.fork(() -> fraud.metadata(order.id()));

        scope.join();

        return combine(
            order,
            customerTask.get(),
            fraudTask.get()
        );
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    StructuredTaskScope.open(
        StructuredTaskScope.Joiner.awaitAllSuccessfulOrThrow<Any>()
    ).use { scope ->

        val customerTask =
            scope.fork<Any> { customers.get(order.customerId) }

        val fraudTask =
            scope.fork<Any> { fraud.metadata(order.id) }

        scope.join()

        return combine(
            order,
            customerTask.get(),
            fraudTask.get()
        )
    }
    ```

Now the source code visibly says:

```text
these operations are parallel
```

rather than forcing every individual client method to advertise asynchronous execution.

This is arguably a more precise use of concurrency in the type and control-flow model.

---

## Performance is not only requests per second

The value of this architecture should not be reduced to benchmark throughput.

A concurrency model affects:

- implementation complexity;
- debugging time;
- incident response;
- onboarding;
- test readability;
- library choice;
- code generation;
- observability;
- upgrade cost;
- cognitive load.

Reactive systems can deliver excellent throughput, but if an ordinary service does not need stream semantics, forcing every developer to reason about a reactive execution graph can be an organizational cost.

Virtual threads let a framework trade JVM sophistication for application simplicity.

Kora 2 explicitly chooses that trade.

The performance benefit is therefore not just that the service may handle many concurrent requests efficiently. It is that the framework can obtain that concurrency **without making concurrency syntax dominate the application**.

---

## The real meaning of "Virtual Threads First"

"Virtual Threads First" should not be interpreted as:

> Kora uses `Thread.ofVirtual()` somewhere internally.

It is more fundamental.

It means Kora is willing to design its APIs under the assumption that lightweight thread-per-task execution is the normal JVM model.

That assumption leads to:

- synchronous controllers;
- synchronous HTTP clients;
- synchronous JDBC repositories;
- ordinary scheduled methods;
- no framework-wide reactive contract;
- no framework-wide `suspend` contract;
- explicit structured concurrency for real parallelism;
- resource-specific capacity limits rather than small worker pools;
- direct Java/Kotlin call stacks for diagnostics.

The virtual thread is not an implementation detail added after the API was designed.

It is one of the reasons the API can be designed this way at all.

---

## Conclusion

The story of server concurrency on the JVM is often told as a contest between blocking and non-blocking programming. That framing is now too simplistic.

The real historical constraint was the coupling between a logical thread and an expensive operating-system thread.

Reactive programming broke that coupling by moving continuations into application-level abstractions.

Project Loom breaks it inside the JVM.

That lets Kora 2 recover the strongest property of the traditional Java server model: **business code can be written as ordinary sequential code whose call stack mirrors the logical operation**.

But it recovers that model without returning to the old assumption that every concurrent request requires a dedicated operating-system thread.

The result is not the old thread-per-request architecture.

It is a new version of it:

```text
one request
    ↓
one virtual thread
    ↓
ordinary synchronous code
    ↓
blocking when the business operation must wait
    ↓
carrier released whenever the runtime can release it
```

Reactive programming was a rational response to platform-thread scarcity. Loom moves much of the machinery required to solve that problem into the JVM. Kora 2 takes the next architectural step and removes that machinery from its application contracts.

That is why Kora 2 is synchronous again.

Not because scalability stopped mattering.

Because the JVM finally made the simple programming model scalable enough to become the default again.
