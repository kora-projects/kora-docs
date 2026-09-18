---
title: How an HTTP Request Travels Through the Kora Framework on Virtual Threads
description: The two concurrency domains behind an HTTP request in the Kora Framework (Kora 2) — Undertow I/O threads and virtual threads — why blocking JDBC is fine, and where the carrier thread fits.
search:
  exclude: true
---

# How an HTTP Request Travels Through Kora on Virtual Threads

A typical Kora Framework HTTP endpoint can look almost deceptively simple:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
    public User getUser(long id) {
        return repository.findById(id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
    fun getUser(id: Long): User {
        return repository.findById(id)
    }
    ```

There is no `Mono<User>`, no `CompletionStage<User>`, no callback, no coroutine boundary, and no explicit executor handoff. The repository can call JDBC synchronously and wait for the database. From
the application's point of view, the request follows ordinary sequential Java control flow.

Yet underneath that simple method there are two very different concurrency domains.

At the edge of the application, Undertow uses a small number of network I/O threads to accept connections, parse HTTP traffic, and react to socket readiness. Once Kora is ready to execute application
code, the request leaves that constrained network thread and continues on a Java virtual thread. The controller, service, repository, JDBC driver, interceptors, request mappers, and other
application-level code then execute using the familiar thread-per-request programming model.

Conceptually, the path looks like this:

```text
Socket
  ↓
Undertow / XNIO I/O thread
  ↓
Kora HTTP routing
  ↓
dispatch
  ↓
Virtual Thread
  ↓
generated Kora handler
  ↓
interceptors / request mapping
  ↓
Controller
  ↓
Service
  ↓
Repository
  ↓
JDBC
  ↓
Database
```

The return trip follows roughly the same path in reverse:

```text
Database result
  ↓
JDBC
  ↓
Repository
  ↓
Service
  ↓
Controller
  ↓
response mapper / serialization
  ↓
Kora HTTP response
  ↓
Undertow
  ↓
Socket
```

Understanding where the transition between those worlds happens explains most of Kora 2's concurrency model: why blocking JDBC is acceptable, why application code does not need reactive signatures,
what a carrier thread actually is, and why blocking an Undertow I/O thread is fundamentally different from blocking a virtual thread.

Kora 2 explicitly embraces this model. Its documentation describes application code as synchronous and states that HTTP requests are dispatched onto virtual threads. Controllers, HTTP clients,
repositories, and scheduled tasks use ordinary blocking signatures, while reactive and Kotlin `suspend` contracts have been removed from Kora modules.

---

## The Request Has More Than One Thread

The easiest mistake when discussing virtual-thread servers is to say:

> "The request runs on a virtual thread."

That is directionally correct, but incomplete.

The TCP connection does not magically arrive directly inside a virtual thread. There is still a network stack underneath the application, and Kora's HTTP server implementation uses Undertow. Undertow
itself is built on asynchronous NIO through XNIO and handles network events using a relatively small number of I/O threads. Kora's HTTP documentation exposes this separation directly:
`httpServer.undertow.ioThreads` controls the number of network I/O threads, while application request handling does not use a traditional bounded blocking worker pool.

So there are at least three concepts to distinguish:

```text
Undertow I/O thread
        │
        │ dispatches request
        ▼
Virtual thread
        │
        │ JVM schedules execution
        ▼
Carrier platform thread
```

These are not three names for the same thing.

The **Undertow I/O thread** belongs to the HTTP transport architecture. It reacts to network readiness and multiplexes many connections.

The **virtual thread** represents the logical application execution of a request.

The **carrier thread** is a JVM-managed platform thread on which a virtual thread happens to execute while it is runnable.

This distinction is fundamental.

---

## Stage 1: The Packet Reaches Undertow

Imagine a client sends:

```http
GET /users/42 HTTP/1.1
Host: api.example.com
```

The operating system receives TCP packets and eventually signals that data is available on the socket. Undertow's XNIO infrastructure uses Java NIO selectors and a relatively small group of I/O
threads to react to those events.

The relevant architecture is approximately:

```text
         connections
        /    |    \
       /     |     \
      ▼      ▼      ▼

   socket  socket  socket
      \      |      /
       \     |     /
        ▼    ▼    ▼

      XNIO Selector
            │
            ▼
     Undertow I/O Thread
```

One I/O thread can therefore participate in handling events for many connections.

That is precisely why blocking here is dangerous.

Suppose one I/O thread is responsible for events from hundreds or thousands of active connections. If some handler running directly on that thread performs:

===! ":fontawesome-brands-java: `Java`"

    ```java
    Thread.sleep(5000);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    Thread.sleep(5000)
    ```

or:

===! ":fontawesome-brands-java: `Java`"

    ```java
    jdbcTemplate.query(...);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    jdbcTemplate.query(...)
    ```

or:

===! ":fontawesome-brands-java: `Java`"

    ```java
    socket.read();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    socket.read()
    ```

and waits synchronously for five seconds, the problem is not merely that "one thread is blocked."

The problem is that one of the small number of threads responsible for progressing many network connections has stopped progressing them.

Undertow's own documentation explicitly warns that I/O threads perform non-blocking tasks and should not execute blocking operations because doing so prevents other connections associated with that
thread from making progress. Historically, Undertow solved this by dispatching blocking handlers from the I/O thread to its worker pool.

Kora 2 keeps the same architectural rule but changes the destination of that dispatch.

Instead of moving ordinary application work to a large bounded platform-thread pool, it moves it to virtual threads.

---

## Stage 2: Undertow Does the Network Work

Before your controller executes, Undertow still has transport work to perform.

Conceptually, it handles concerns such as:

```text
TCP connection
     ↓
HTTP protocol parsing
     ↓
method / URI / headers
     ↓
HttpServerExchange
     ↓
Kora root HTTP handler
```

The exact implementation contains more machinery than this simplified diagram, but the architectural boundary matters more than every internal class.

At this point Kora has enough information to begin request processing. The URL exists, the HTTP method exists, the connection is represented by Undertow's exchange abstractions, and routing can
proceed.

The important rule remains:

```text
Undertow I/O thread
=
network coordination thread

NOT
=
application worker thread
```

Kora deliberately prevents the rest of your normal application stack from depending on that distinction.

---

## Stage 3: Kora Dispatches the Request to a Virtual Thread

This is the decisive transition.

Kora 2's HTTP documentation states:

> Request handling is synchronous. Every request is dispatched onto a virtual thread.

There is consequently no `blockingThreads` setting and no switch equivalent to the old optional `virtualThreadsEnabled` mode. The Kora 2 Undertow configuration retains network-oriented settings such
as `ioThreads`, but normal request execution itself uses virtual threads directly.

Conceptually:

```text
Undertow I/O thread
        │
        │ HTTP request discovered
        │
        │ dispatch
        ▼
┌────────────────────────────┐
│ Virtual Thread             │
│                            │
│ request processing begins  │
└────────────────────────────┘
```

This is where blocking semantics change completely.

Blocking on the I/O thread is dangerous because the thread is scarce and multiplexes unrelated connections.

Blocking on a virtual thread is normally expected because the virtual thread is the logical request context and is cheap enough to create in very large numbers.

The same operation therefore has radically different implications depending on where it executes.

```text
Network I/O thread:

request A
request B ─┐
request C  ├── one scarce thread
request D ─┘

BLOCK → several connections may stop progressing
```

versus:

```text
Virtual threads:

request A → VT-A
request B → VT-B
request C → VT-C
request D → VT-D

VT-B BLOCKS → VT-B waits
             other VTs continue
```

That separation is the basis of Kora's synchronous programming model.

---

## Stage 4: The Virtual Thread Needs a Carrier

A virtual thread is still a thread from the programmer's perspective, but it is not permanently mapped to an operating-system thread.

When a virtual thread actually executes Java instructions, the JVM mounts it onto a platform thread.

That platform thread is called its **carrier**.

```text
Virtual Thread A
       │
       │ mounted on
       ▼
Carrier Thread 3
       │
       ▼
CPU
```

There may be thousands, hundreds of thousands, or potentially millions of virtual threads, while the JVM needs only a relatively small number of carrier threads executing runnable work at any given
moment.

For example:

```text
VT-1  ─┐
VT-2   │
VT-3   │
VT-4   │
VT-5   ├──── JVM scheduler ──── Carrier-1 ── CPU
VT-6   │                     ├─ Carrier-2 ── CPU
VT-7   │                     ├─ Carrier-3 ── CPU
...    │                     └─ Carrier-4 ── CPU
VT-N  ─┘
```

Only runnable virtual threads need CPU execution.

This is why it is inaccurate to imagine a carrier thread as "the OS thread belonging to the request."

There is no permanent relationship:

```text
Request 42
    ≠
Carrier thread 7 forever
```

Instead:

```text
Request 42
    =
Virtual Thread 42

Virtual Thread 42
    may run on
Carrier 7

then wait

then later resume on
Carrier 3
```

The carrier is an execution resource, not the identity of the request.

OpenJDK describes exactly this mount/unmount model: the scheduler mounts a virtual thread on a platform thread when it is runnable and can unmount it when the virtual thread blocks, freeing the
carrier to execute another virtual thread.

---

## Stage 5: Kora's Generated Handler Executes

After the dispatch, Kora's generated HTTP infrastructure takes over on the virtual thread.

A controller such as:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class UserController {

        private final UserService service;

        public UserController(UserService service) {
            this.service = service;
        }

        @HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
        public User get(@Path long id) {
            return service.get(id);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class UserController(private val service: UserService) {

        @HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
        fun get(@Path id: Long): User {
            return service.get(id)
        }
    }
    ```

does not depend on runtime reflective discovery.

Kora processes HTTP annotations at compilation time and generates handler code corresponding to that contract. The handler performs the necessary transport work around the method: route binding,
parameter conversion, request mapping, interceptors, invocation, response mapping, exception handling, and telemetry.

Kora's broader design follows the same pattern for dependency injection, repositories, mappers, and AOP: framework metadata becomes ordinary generated source code rather than a runtime reflective
engine.

A more detailed request pipeline therefore looks approximately like:

```text
Virtual Thread
    ↓
Kora generated HTTP handler
    ↓
telemetry
    ↓
HTTP interceptors
    ↓
path / query / header mapping
    ↓
request body mapper
    ↓
controller method
```

From this point forward, ordinary synchronous Java execution can continue down the stack.

---

## Stage 6: The Controller Is Just Normal Java

The controller runs on the request virtual thread.

That means this is completely normal:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
    public User get(@Path long id) {
        return service.getUser(id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
    fun get(@Path id: Long): User {
        return service.getUser(id)
    }
    ```

There is no need for:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public CompletionStage<User> get(...)
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun get(...): CompletionStage<User>
    ```

or:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public Mono<User> get(...)
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun get(...): Mono<User>
    ```

or Kotlin:

```kotlin
suspend fun get(...): User
```

Kora 2 intentionally removes these framework contracts. Its documentation states that controller, client, repository, and scheduler methods use direct synchronous signatures, while processors reject
unsupported reactive or `suspend` contracts.

The call stack can therefore remain exactly what the source suggests:

```text
UserController.get()
        ↓
UserService.getUser()
        ↓
UserRepository.findById()
```

This property is more important than merely saving a few operators from a reactive pipeline. The runtime control flow and the source-code control flow become close to identical.

A debugger can show:

```text
UserController.get
UserService.getUser
_UserRepository_Impl.findById
...
```

rather than forcing the developer to reconstruct logical execution from asynchronous continuations distributed across publishers, callbacks, schedulers, and event loops.

---

## Stage 7: The Service Does Not Need to Know About Threads

Consider:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class UserService {

        private final UserRepository repository;

        public UserService(UserRepository repository) {
            this.repository = repository;
        }

        public User getUser(long id) {
            return repository.findById(id)
                .orElseThrow(() -> new UserNotFoundException(id));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class UserService(private val repository: UserRepository) {

        fun getUser(id: Long): User {
            return repository.findById(id)
                .orElseThrow { UserNotFoundException(id) }
        }
    }
    ```

There is intentionally nothing concurrency-specific here.

The service does not need to know:

- which Undertow I/O thread accepted the request;
- which carrier currently executes the virtual thread;
- which carrier will execute it after a blocking operation;
- which selector owns the underlying client socket;
- which executor should contain JDBC operations.

The service owns business logic.

Thread scheduling belongs to the infrastructure.

This is one of the architectural benefits of virtual threads that is easy to underestimate. Loom does not merely make threads cheaper. It allows concurrency mechanics to retreat from application APIs.

Before virtual threads, high-concurrency architecture often leaked scheduling decisions upward:

```text
Controller
   ↓ Publisher
Service
   ↓ Publisher
Repository
   ↓ Publisher
Driver
```

The asynchronous nature of the lowest layer propagated through nearly every API above it.

With Kora 2:

```text
Controller
   ↓ User
Service
   ↓ User
Repository
   ↓ User
JDBC
```

Concurrency still exists.

It simply no longer dominates the application's type system.

---

## Stage 8: The Repository Calls JDBC

Now the request reaches the database layer.

A Kora repository might look like:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface UserRepository extends JdbcRepository {

        @Query("""
            SELECT id, name, email
            FROM users
            WHERE id = :id
            """)
        @Nullable
        User findById(long id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface UserRepository : JdbcRepository {

        @Query("""
            SELECT id, name, email
            FROM users
            WHERE id = :id
            """)
        fun findById(id: Long): User?
    }
    ```

Kora generates its implementation at compile time. The generated implementation obtains a database connection, prepares the statement, binds parameters, executes the query, reads the result set, and
maps the row into the return type.

Again, the contract is synchronous:

===! ":fontawesome-brands-java: `Java`"

    ```java
    User findById(long id);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun findById(id: Long): User
    ```

not:

===! ":fontawesome-brands-java: `Java`"

    ```java
    Mono<User> findById(long id);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun findById(id: Long): Mono<User>
    ```

Kora 2's JDBC documentation makes this explicit: repository contracts are synchronous, and a repository call blocks the calling thread until the database responds. Because server request handling is
running on virtual threads, that waiting does not ordinarily consume a platform thread for the entire wait.

This is where the virtual-thread model pays off most visibly.

---

## What Actually Happens When JDBC Blocks?

Suppose PostgreSQL takes 20 milliseconds to answer.

From the application's perspective:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var user = repository.findById(id);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val user = repository.findById(id)
    ```

simply waits.

The virtual thread cannot continue because there is no result yet.

Conceptually:

```text
VT-42
  │
  │ execute SQL
  ▼
PostgreSQL socket
  │
  │ no data yet
  ▼
WAIT
```

The important question is what happens to the carrier.

With Loom-compatible blocking operations, the virtual thread can park and unmount:

```text
BEFORE WAIT

VT-42
  │
  ▼
Carrier-3
  │
  ▼
CPU
```

then:

```text
DATABASE WAIT

VT-42
  │
  └── parked / unmounted

Carrier-3
  │
  └── available for other virtual threads
```

Carrier-3 can now run another request:

```text
VT-57
  │
  ▼
Carrier-3
  │
  ▼
CPU
```

When the database result becomes available, VT-42 becomes runnable again.

It might resume on the same carrier:

```text
VT-42 → Carrier-3
```

but there is no requirement for that. It might instead resume as:

```text
VT-42 → Carrier-1
```

The virtual thread preserves the logical execution state. The carrier is interchangeable.

This is the central scalability property of virtual threads.

---

## Blocking a Virtual Thread Is Not Blocking Its Carrier

This distinction deserves to be stated precisely because "blocking" became almost synonymous with "bad" during the reactive era.

There are two different statements:

```text
The virtual thread is blocked.
```

and:

```text
The platform thread is blocked.
```

They are not equivalent.

A virtual thread waiting for I/O may look logically blocked:

===! ":fontawesome-brands-java: `Java`"

    ```java
    ResultSet rs = statement.executeQuery();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val rs: ResultSet = statement.executeQuery()
    ```

but internally the JVM can suspend that virtual thread and release its carrier.

So:

```text
VT blocked
≠
carrier blocked
```

The application retains the natural semantics of blocking code while the runtime can recover the scarce platform-thread resource.

That is why this code becomes reasonable again:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public Order getOrder(long id) {
        var order = repository.findOrder(id);
        var customer = customerClient.get(order.customerId());
        return enrich(order, customer);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun getOrder(id: Long): Order {
        val order = repository.findOrder(id)
        val customer = customerClient.get(order.customerId)
        return enrich(order, customer)
    }
    ```

The method still waits for external systems, but waiting no longer implies reserving an expensive OS-backed thread throughout every network stall.

---

## What the Carrier Does During the Request

A useful mental model is to follow a single request over time.

Suppose the request spends:

- 500 μs doing CPU work;
- 8 ms waiting for PostgreSQL;
- 300 μs mapping rows;
- 12 ms waiting for another HTTP service;
- 200 μs serializing JSON.

The virtual thread conceptually experiences:

```text
VT request lifetime

CPU     DB WAIT     CPU      HTTP WAIT     CPU
███───────────────███─────────────────────██
```

But a carrier might experience something more like:

```text
Carrier-1

VT-42   VT-11  VT-63  VT-8   VT-42   VT-91 ...
█████   █████  █████  ████   █████   █████
```

When VT-42 waits, the carrier does not need to wait with it. It can execute other runnable virtual threads.

This changes the resource model dramatically.

With one traditional platform thread per request:

```text
10,000 waiting requests
≈
10,000 platform threads
```

which is generally impractical.

With virtual threads:

```text
10,000 waiting requests
=
10,000 virtual threads

but only a relatively small carrier population
needs to execute runnable code
```

Virtual threads therefore restore the conceptual thread-per-request model without restoring the old one-OS-thread-per-request resource cost.

---

## Java 25 Changes the Old Pinning Story

A lot of virtual-thread material on the internet still describes an important Java 21 limitation: a virtual thread could remain pinned to its carrier when blocking inside a `synchronized` method or
block.

That advice is historically accurate but should not be repeated unqualified for Kora 2.

Kora 2 targets Java 25. Java 24 delivered JEP 491, **Synchronize Virtual Threads without Pinning**, which changed JVM monitor handling so that virtual threads can generally unmount while holding Java
monitors. The old recommendation to broadly replace `synchronized` with `ReentrantLock` purely because of virtual-thread pinning is therefore no longer appropriate for normal Java 25 code.

The simplified modern picture is:

```text
Java 21–23

synchronized
     +
blocking operation

could pin VT to carrier
```

versus:

```text
Java 24+
       
synchronized
     +
ordinary blocking operation

can generally unmount normally
```

This does not mean carrier capture has become impossible. Native code, VM-level operations, unusual library behavior, and some other cases can still cause a virtual thread to hold a carrier longer
than expected. These are operational concerns worth observing under load, particularly when integrating native libraries or legacy components.

But for ordinary Kora 2 service code on Java 25, the correct mental model is no longer "every synchronized block is suspicious."

The Java runtime has evolved alongside the programming model.

---

## Blocking Is Fine. Unlimited Concurrency Is Not.

Virtual threads remove thread scarcity.

They do **not** remove resource scarcity.

Consider a JDBC pool:

```text
HikariCP maxPoolSize = 20
```

and suddenly 10,000 requests execute:

===! ":fontawesome-brands-java: `Java`"

    ```java
    repository.findById(id);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    repository.findById(id)
    ```

Kora can support 10,000 request virtual threads waiting efficiently.

But PostgreSQL still has only twenty checked-out connections available through that pool.

Conceptually:

```text
10,000 Virtual Threads
          │
          ▼
   Hikari connection pool
          │
          │ 20 connections
          ▼
      PostgreSQL
```

The remaining requests wait.

That can be perfectly acceptable from a thread-management perspective, but it does not make the database infinitely scalable.

The same applies to:

- JDBC connection pools;
- HTTP connection pools;
- Kafka brokers;
- rate-limited external APIs;
- Redis connections;
- file descriptors;
- CPU;
- memory;
- downstream concurrency limits.

Virtual threads solve a specific problem:

> **Waiting should not require one expensive platform thread per concurrent operation.**

They do not solve:

> **Every resource may now be used without limits.**

A virtual-thread-first application still needs backpressure at the architecture level where scarce resources actually exist.

That often means connection-pool limits, rate limiters, semaphores, queue limits, deadlines, circuit breakers, or explicit concurrency budgets.

---

## CPU-Bound Work Is Different

Virtual threads are especially effective for workloads that spend substantial time waiting:

```text
HTTP calls
database calls
message brokers
remote storage
network sockets
locks
timers
```

They do not create additional CPU capacity.

Suppose every request performs:

===! ":fontawesome-brands-java: `Java`"

    ```java
    calculateSHA256TenMillionTimes();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    calculateSHA256TenMillionTimes()
    ```

and never waits.

Then the virtual thread remains runnable and needs a carrier to execute instructions.

For a machine with eight effective CPU cores:

```text
10,000 CPU-heavy virtual threads
        ↓
     scheduler
        ↓
 ~8 useful CPU execution slots
```

Creating ten thousand virtual threads cannot turn eight cores into ten thousand cores.

The scheduler will simply rotate runnable work over the available execution resources.

Virtual threads make **concurrency** cheap.

They do not make **parallel CPU execution** unlimited.

This distinction is particularly important when moving application code off event loops. Blocking I/O becomes natural on virtual threads, but expensive CPU work still has to be treated as expensive
CPU work.

---

## Why You Must Not Block an Event Loop

The phrase "blocking is fine with virtual threads" therefore needs a qualifier:

> Blocking is fine **after the request has moved onto a virtual thread**.

Blocking is still wrong on a multiplexed network event loop.

Compare the two architectures.

### Blocking an Undertow I/O thread

```text
                I/O Thread 1
                    │
     ┌──────────────┼───────────────┐
     │              │               │
 connection A  connection B   connection C
     │              │               │
     └──────────────┼───────────────┘
                    │
                 BLOCKED
                    │
                5 seconds
```

Several connections may stop making progress.

### Blocking a Kora request virtual thread

```text
connection A → VT-A → waiting on JDBC
connection B → VT-B → running
connection C → VT-C → waiting on HTTP
connection D → VT-D → running
```

When VT-A waits, its carrier can run VT-B.

The blocking operation belongs to the logical request instead of the networking infrastructure.

This is the rule worth remembering:

```text
Event loop / I/O thread:
    never perform application blocking work

Virtual request thread:
    blocking I/O is the intended programming model
```

Undertow's documentation explains the same fundamental distinction: its I/O threads are responsible for multiple connections and should not perform blocking work; blocking processing must first be
dispatched away from the I/O thread.

Kora 2 makes that dispatch part of the framework's request model.

---

## Why Kora Does Not Expose the Event Loop to Controllers

A framework could expose low-level transport semantics directly:

===! ":fontawesome-brands-java: `Java`"

    ```java
    void handle(HttpExchange exchange) {
        if (exchange.isInIoThread()) {
            exchange.dispatch(...);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun handle(exchange: HttpExchange) {
        if (exchange.isInIoThread) {
            exchange.dispatch(...)
        }
    }
    ```

Undertow supports programming at approximately this level, and its API explicitly exposes concepts such as `isInIoThread()` and `dispatch()`.

But that is usually the wrong abstraction for application controllers.

Imagine requiring every endpoint author to reason about:

```text
Am I on I/O thread?
Should this operation dispatch?
Which executor?
Is this library blocking?
Will this callback return to the event loop?
Where should JSON serialization run?
What scheduler is this publisher using?
```

Kora instead puts that decision in the HTTP infrastructure.

The developer receives the simpler contract:

===! ":fontawesome-brands-java: `Java`"

    ```java
    User getUser(long id);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun getUser(id: Long): User
    ```

The framework guarantees the appropriate execution environment before application logic is invoked.

That is exactly the kind of concern a framework should own: a cross-cutting runtime invariant that should be solved once rather than repeatedly inside every endpoint.

---

## Request Mapping Also Runs in the Application Context

A real endpoint usually does more than call a controller.

For example:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpRoute(method = HttpMethod.POST, path = "/users")
    public User create(@Json CreateUserRequest request) {
        return service.create(request);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpRoute(method = HttpMethod.POST, path = "/users")
    fun create(@Json request: CreateUserRequest): User {
        return service.create(request)
    }
    ```

The request has to pass through several pieces of infrastructure:

```text
HTTP request
    ↓
route lookup
    ↓
path / query / header extraction
    ↓
body reading
    ↓
JSON deserialization
    ↓
interceptors
    ↓
controller
```

Kora describes request handling as synchronous and includes handlers, interceptors, and mappers in this direct execution model.

This matters because transformations such as JSON deserialization are application work too. They should not unexpectedly execute a long CPU-heavy operation on a network event loop merely because the
transport itself uses NIO.

The external I/O architecture can remain asynchronous while the user-facing programming model remains synchronous.

Those models are not contradictory.

They operate at different layers.

---

## The Response Travels Back

Eventually the controller returns:

===! ":fontawesome-brands-java: `Java`"

    ```java
    return new User(id, name, email);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    return User(id, name, email)
    ```

The call stack unwinds:

```text
Repository
    ↑
Service
    ↑
Controller
    ↑
generated handler
```

Kora then maps the result into an HTTP response.

For JSON this may involve a generated mapper:

```text
User
 ↓
JSON mapper
 ↓
response body
 ↓
HttpServerResponse
```

Telemetry can finalize request metrics and tracing information around the same operation, while Undertow eventually takes responsibility for transferring the response bytes to the network.

Conceptually:

```text
Virtual Thread
      │
      │ build response
      ▼
Kora response handling
      │
      ▼
Undertow
      │
      ▼
socket write
```

The fact that the controller executed synchronously does not imply that the server must perform every physical network operation using blocking OS calls.

That is another common source of confusion.

Application programming model:

```text
synchronous
```

Transport implementation:

```text
NIO / asynchronous
```

JVM execution model:

```text
virtual threads scheduled over carriers
```

All three can coexist.

---

## Synchronous API Does Not Mean Synchronous Kernel Architecture

This distinction is central to Kora 2.

A synchronous application API says:

===! ":fontawesome-brands-java: `Java`"

    ```java
    User user = repository.findById(id);
    return user;
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val user = repository.findById(id)
    return user
    ```

It says nothing about whether the network server underneath is implemented using:

- epoll;
- kqueue;
- NIO selectors;
- io_uring;
- asynchronous channels;
- blocking sockets;
- some combination of them.

The framework can use efficient asynchronous mechanisms internally while presenting a sequential API externally.

That gives us:

```text
              APPLICATION

Controller → Service → Repository
      synchronous call stack

                  │
                  ▼

              RUNTIME

           Virtual Thread
              ↓   ↑
         park / resume

                  │
                  ▼

              JVM / OS

NIO selectors / sockets / carrier threads
```

Reactive programming historically forced some of those lower-level mechanics into application types because platform threads were too expensive to dedicate to waiting.

Virtual threads change the economics.

When waiting no longer requires permanently occupying a platform thread, the argument for propagating asynchronous types across every architectural layer becomes much weaker for ordinary
request/response services.

---

## What Happens with 100,000 Concurrent Requests?

Consider a simplified service:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Get
    User get(long id) {
        return repository.findById(id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Get
    fun get(id: Long): User {
        return repository.findById(id)
    }
    ```

Assume the database is deliberately slow and every query takes one second.

With 100,000 concurrent requests, the conceptual state may look like:

```text
100,000 requests
       ↓
100,000 virtual threads
       ↓
most are waiting
       ↓
small carrier pool executes runnable VTs
```

That does **not** imply:

```text
100,000 platform threads
```

Most virtual threads are simply parked while waiting for something.

However, another limit quickly becomes visible:

```text
100,000 VT requests
       ↓
JDBC pool: 32 connections
       ↓
32 database queries at once
```

So perhaps:

```text
32 requests:
    waiting on PostgreSQL

99,968 requests:
    waiting for JDBC connection
```

This can still be relatively inexpensive in terms of thread resources because those waits can park virtual threads.

But latency may become catastrophic.

Virtual threads therefore allow the runtime to survive levels of concurrency that would previously exhaust a platform-thread pool, but survival is not the same as good capacity planning.

The correct architecture still asks:

```text
How many requests should reach this resource concurrently?
```

rather than:

```text
How many threads can Java create?
```

---

## Little's Law Still Applies

Virtual threads do not repeal queueing theory.

If a service receives:

```text
10,000 requests / second
```

and the average request takes:

```text
500 ms
```

then roughly:

```text
concurrency ≈ throughput × latency

            ≈ 10,000 × 0.5

            ≈ 5,000 in-flight requests
```

Virtual threads make representing those 5,000 in-flight requests cheap.

They do not reduce the fact that there are 5,000 requests consuming memory, holding request state, competing for pools, and placing demand on downstream systems.

This difference is important because traditional thread pools accidentally acted as a crude concurrency limiter.

For example:

```text
worker pool = 200
```

automatically meant that only about 200 requests could execute blocking application code simultaneously.

Virtual threads remove that accidental limitation.

That is generally desirable, but capacity control should then be implemented deliberately at the resource boundary instead of emerging accidentally from thread scarcity.

---

## Virtual Threads Restore the Meaning of a Stack Trace

There is also an observability advantage.

Consider the synchronous stack:

```text
UserController.get()
    UserService.getUser()
        UserRepository.findById()
            PreparedStatement.executeQuery()
                Socket.read()
```

This is not merely aesthetically pleasing.

It preserves the causal structure of the operation.

A request entered the controller.

The controller called the service.

The service called the repository.

The repository called JDBC.

JDBC waited for the database.

The thread stack says exactly that.

Reactive systems frequently represent the same logical operation through a chain such as:

```text
controller
  ↓
flatMap
  ↓
service
  ↓
flatMap
  ↓
repository
  ↓
publisher
  ↓
scheduler
  ↓
callback
```

Tooling has improved enormously, and reactive stacks can certainly be observed, but the runtime execution structure remains more abstract than ordinary sequential control flow.

Virtual threads allow the JVM's existing thread-oriented observability model — stack traces, debuggers, thread dumps, profiling, context propagation — to remain directly useful at high concurrency.

That is an important reason Loom is more than a performance feature.

It is a complexity feature.

---

## One Request, One Logical Thread

The cleanest model for a Kora 2 HTTP request is therefore:

```text
one request
    =
one logical virtual thread
```

The request can call:

```text
controller
service
repository
JDBC
HTTP clients
resilience aspects
validation
cache
logging
```

without changing concurrency abstractions between layers.

That thread may repeatedly:

```text
run
↓
wait
↓
unmount
↓
become runnable
↓
mount
↓
run
```

during a single request.

From the application's perspective, however, none of those transitions need to appear in the source.

The source remains:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var user = repository.findById(id);
    var profile = profileClient.get(user.profileId());
    return mapper.map(user, profile);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val user = repository.findById(id)
    val profile = profileClient.get(user.profileId)
    return mapper.map(user, profile)
    ```

That is the abstraction Loom was built to recover.

---

## Why This Is Different from the Old Thread-per-Request Model

It is tempting to describe Kora 2 as simply returning to traditional thread-per-request servers.

Conceptually, yes.

Mechanically, no.

The old model looked approximately like:

```text
Request
   ↓
Platform Thread
   ↓
Controller
   ↓
JDBC
   ↓
block OS thread
```

If 5,000 requests simultaneously waited on external systems:

```text
≈ 5,000 platform threads
```

That model ran into stack-memory costs, scheduler overhead, context switching, and practical thread-count limits.

The virtual-thread model is:

```text
Request
   ↓
Virtual Thread
   ↓
Controller
   ↓
JDBC
   ↓
park VT
   ↓
release carrier
```

The programming model resembles old thread-per-request Java.

The runtime resource model does not.

So the historical progression is not really a circle:

```text
platform thread per request
        ↓
reactive/event-loop application model
        ↓
virtual thread per request
```

It is more accurately:

```text
simple synchronous model
        │
        │ scalability problem:
        │ platform threads are expensive
        ▼
asynchronous application model
        │
        │ Loom changes thread economics
        ▼
simple synchronous model
with lightweight runtime threads
```

The API came back.

The implementation underneath it changed.

---

## Where Structured Concurrency Fits

Synchronous request handling does not mean that every request must perform all independent operations sequentially.

Suppose an endpoint needs three independent calls:

```text
user repository
orders service
recommendation service
```

Sequential execution would produce approximately:

```text
DB 20 ms
+
orders 40 ms
+
recommendations 60 ms
=
~120 ms
```

When appropriate, these operations can run concurrently.

Kora's documentation points toward Java structured concurrency for such cases rather than introducing framework-specific reactive contracts.

Conceptually:

```text
Request VT
   │
   ├── child VT → user repository
   │
   ├── child VT → orders service
   │
   └── child VT → recommendations service
            │
            ▼
          join
            │
            ▼
         response
```

The important architectural distinction is that concurrency remains explicit where concurrency is actually needed.

You do not have to make every method asynchronous merely because one endpoint occasionally needs parallel work.

Most code can remain:

===! ":fontawesome-brands-java: `Java`"

    ```java
    T method();
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun method(): T
    ```

while genuinely parallel orchestration can say, explicitly:

```text
these three operations should execute concurrently
```

That keeps concurrency local instead of infecting the entire call graph.

---

## A Complete Request Timeline

Putting everything together, consider:

```http
GET /users/42
```

and this application:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class UserController {

        private final UserService service;

        @HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
        public UserResponse get(@Path long id) {
            return service.get(id);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class UserController(private val service: UserService) {

        @HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
        fun get(@Path id: Long): UserResponse {
            return service.get(id)
        }
    }
    ```

with:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class UserService {

        private final UserRepository repository;

        public UserResponse get(long id) {
            var user = repository.findById(id);
            return new UserResponse(user.id(), user.name());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class UserService(private val repository: UserRepository) {

        fun get(id: Long): UserResponse {
            val user = repository.findById(id)
            return UserResponse(user.id, user.name)
        }
    }
    ```

and:

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

The complete conceptual timeline is:

```text
1. Client sends HTTP request
       │
       ▼
2. Operating system receives TCP data
       │
       ▼
3. XNIO detects socket readiness
       │
       ▼
4. Undertow I/O thread processes network event
       │
       ▼
5. Undertow constructs / updates HTTP exchange
       │
       ▼
6. Kora HTTP infrastructure matches route
       │
       ▼
7. Request is dispatched away from I/O thread
       │
       ▼
8. Virtual thread executes Kora generated handler
       │
       ▼
9. Request telemetry / interceptors execute
       │
       ▼
10. Path parameter "42" is mapped to long
       │
       ▼
11. UserController.get(42)
       │
       ▼
12. UserService.get(42)
       │
       ▼
13. UserRepository.findById(42)
       │
       ▼
14. Generated JDBC repository obtains connection
       │
       ▼
15. SQL query is executed
       │
       ▼
16. Virtual thread waits for DB
       │
       ├──── virtual thread parks
       │
       └──── carrier can execute another VT
       │
       ▼
17. Database response arrives
       │
       ▼
18. Virtual thread becomes runnable
       │
       ▼
19. JVM mounts it on an available carrier
       │
       ▼
20. JDBC maps ResultSet → User
       │
       ▼
21. Repository returns User
       │
       ▼
22. Service maps User → UserResponse
       │
       ▼
23. Controller returns UserResponse
       │
       ▼
24. Kora response mapper serializes JSON
       │
       ▼
25. Telemetry completes
       │
       ▼
26. Undertow writes response
       │
       ▼
27. Client receives HTTP response
```

The striking property of this pipeline is how much concurrency machinery is absent from the application's own code.

Steps 11 through 23 can look almost exactly like Java code written twenty years ago.

The sophistication has moved underneath the API.

---

## The Thread Map

Another useful way to visualize the lifecycle is to separate thread domains explicitly:

```text
                     NETWORK DOMAIN
                     ==============

Client
  │
  ▼
TCP socket
  │
  ▼
XNIO selector
  │
  ▼
Undertow I/O thread
  │
  │  DO:
  │  - network events
  │  - protocol processing
  │  - lightweight transport work
  │
  │  DON'T:
  │  - run JDBC
  │  - call slow services
  │  - sleep
  │  - execute blocking business logic
  │
  ▼
dispatch


                   APPLICATION DOMAIN
                   ==================

Virtual Thread
  │
  ├─ Kora handler
  │
  ├─ interceptor
  │
  ├─ mapper
  │
  ├─ controller
  │
  ├─ service
  │
  ├─ repository
  │
  └─ JDBC
       │
       ▼
     block / wait
       │
       ▼
   VT may unmount


                     JVM DOMAIN
                     ==========

Virtual Threads
   │
   ▼
VT scheduler
   │
   ▼
Carrier platform threads
   │
   ▼
OS scheduler
   │
   ▼
CPU cores
```

Keeping these domains separate prevents most misconceptions about Kora's concurrency model.

---

## What Should Run Where?

A practical rule of thumb is:

| Operation                  | Undertow I/O thread |   Kora request virtual thread |
|----------------------------|--------------------:|------------------------------:|
| Socket readiness handling  |                 Yes |                            No |
| HTTP protocol mechanics    |                 Yes |  Sometimes framework boundary |
| Routing handoff            |                 Yes |            Yes after dispatch |
| Controller                 |                  No |                           Yes |
| Interceptor business logic |                  No |                           Yes |
| JSON mapping               |    Avoid heavy work |                           Yes |
| JDBC                       |              **No** |                       **Yes** |
| Blocking HTTP client       |              **No** |                       **Yes** |
| `Thread.sleep()`           |              **No** |              Technically safe |
| Waiting for lock           |              **No** |                           Yes |
| Business logic             |                  No |                           Yes |
| CPU-heavy computation      |               Avoid | Possible, but still CPU-bound |

The point is not that virtual threads make every operation cheap.

The point is that application code belongs on application threads, while network event loops should remain dedicated to progressing network activity.

---

## The Architecture Kora 2 Is Choosing

Kora 2's concurrency model can ultimately be reduced to a fairly strong architectural opinion:

```text
Use asynchronous I/O where asynchronous I/O
is an implementation advantage.

Do not force asynchronous programming
into application APIs merely because
the transport uses asynchronous I/O.
```

Undertow can remain NIO-based.

The JVM can dynamically schedule virtual threads.

JDBC can remain blocking.

Controllers can remain ordinary methods.

Repositories can remain ordinary methods.

Services can remain ordinary methods.

That gives Kora a stack such as:

```text
              HTTP / NIO
                  ↓
               Kora
                  ↓
           Virtual Thread
                  ↓
          synchronous Java
                  ↓
          blocking JDBC
```

rather than requiring:

```text
              HTTP / NIO
                  ↓
              event loop
                  ↓
             Publisher
                  ↓
               flatMap
                  ↓
             Publisher
                  ↓
               flatMap
                  ↓
          reactive driver
```

Both architectures can be made fast.

The difference is where they place concurrency complexity.

Kora 2 deliberately pushes that complexity down into the framework, JVM, and transport layer instead of making it part of every application method signature.

---

## The Important Boundary

If there is one diagram to keep, it is this:

```text
               DON'T BLOCK
                   │
                   ▼
┌──────────────────────────────────────┐
│ Undertow / XNIO I/O thread           │
│                                      │
│ Socket → protocol → request          │
└──────────────────┬───────────────────┘
                   │
                   │ dispatch
                   ▼
════════════════════════════════════════
          CONCURRENCY BOUNDARY
════════════════════════════════════════
                   │
                   ▼
┌──────────────────────────────────────┐
│ Virtual Thread                       │
│                                      │
│ Kora handler                         │
│   ↓                                  │
│ interceptor                          │
│   ↓                                  │
│ controller                           │
│   ↓                                  │
│ service                              │
│   ↓                                  │
│ repository                           │
│   ↓                                  │
│ JDBC                                 │
│                                      │
│ Blocking is expected here.           │
└──────────────────────────────────────┘
```

Above the boundary, threads are scarce infrastructure resources shared by network connections.

Below the boundary, the virtual thread represents one logical request, and waiting is part of the intended programming model.

The JVM then multiplexes those logical request threads over carrier platform threads.

---

## Final Perspective

Kora 2 does not make the network synchronous.

It makes **application programming synchronous again**.

Undertow still uses efficient asynchronous NIO at the edge. The JVM still schedules work across a limited number of platform threads. JDBC still waits for databases. HTTP clients still wait for remote
services. The system remains highly concurrent.

What changes is who has to manage that concurrency.

Instead of requiring every controller, service, and repository API to encode asynchronous execution, Kora establishes the correct execution boundary once:

```text
Socket
   ↓
Undertow I/O thread
   ↓
Kora dispatch
   ↓
Virtual Thread
   ↓
Controller
   ↓
Service
   ↓
Repository
   ↓
JDBC
```

Once the request crosses that boundary, ordinary blocking Java becomes the normal model.

When JDBC waits, the **virtual thread** waits.

The **carrier** can usually go somewhere else.

When the database responds, the virtual thread becomes runnable and continues its ordinary call stack.

That gives Kora 2 an interesting combination:

```text
asynchronous network infrastructure

             +

lightweight virtual-thread scheduling

             +

synchronous application code
```

The result is not a rejection of asynchronous I/O. It is a separation of concerns.

The network server can be event-driven where event-driven architecture is useful.

The JVM can multiplex execution where multiplexing is useful.

And application developers can write:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var user = repository.findById(id);
    return user;
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val user = repository.findById(id)
    return user
    ```

where straightforward sequential code is useful.

That is the real request lifecycle in a virtual-thread-first Kora application: asynchronous at the transport edge, virtualized at the runtime layer, and deliberately synchronous where business code
begins.
