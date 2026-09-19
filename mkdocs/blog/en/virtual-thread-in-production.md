---
title: Virtual Threads in Production — Pinning, Carriers, and Load Spikes in the Kora Framework
date: 2026-09-10
description: How virtual threads behave under production load in the Kora Framework — pinning, carrier starvation, connection pools, and overload control.
search:
  exclude: true
---
# Virtual Threads in Production: Pinning, Carrier Threads and Load Spikes { #virtual-threads-in-production }

**September 10, 2026**

Virtual threads make blocking Java dramatically more scalable, but they do not make concurrency free.

That distinction is easy to miss. Once an application can create hundreds of thousands of virtual threads without creating hundreds of thousands of operating-system threads, it is tempting to think
that the traditional limits around thread pools have disappeared and that the application can simply accept as much concurrent work as clients can send. In reality, virtual threads remove one
important bottleneck: the scarcity and cost of platform threads. They do not remove CPU limits, database capacity, connection pools, remote-service quotas, memory pressure, socket limits, native-code
behavior, or queueing effects.

Kora 2 makes this distinction especially important because virtual threads are not an optional programming model layered on top of reactive APIs. They are part of the Kora Framework's normal execution
model. Kora application code is synchronous: controllers, HTTP clients, repositories, and scheduled jobs use ordinary blocking signatures, and the framework executes application work on virtual
threads. Kora's HTTP documentation explicitly says that every request is dispatched onto a virtual thread and that handlers may block normally.

That gives Kora applications a very attractive programming model:

```text
HTTP request
    ↓
virtual thread
    ↓
controller
    ↓
service
    ↓
JDBC / HTTP client / filesystem / other blocking API
```

The code looks much like traditional thread-per-request Java, while the JVM can multiplex a very large number of these request threads over a comparatively small number of operating-system threads.

The production question therefore changes. Instead of asking whether blocking code will exhaust a 200-thread worker pool, we need to ask which resources actually bound concurrency, when a virtual
thread can release its carrier, what happens when it cannot, and how a traffic spike propagates through the system.

Those questions matter far more than the raw number of virtual threads.

## Virtual Threads Do Not Execute by Themselves { #virtual-threads-execution }

A virtual thread is still a Java `Thread`, but it is not permanently associated with an operating-system thread. When it is executing Java code, the JVM mounts it onto a platform thread known as a *
*carrier thread**. The carrier is what the operating system actually schedules onto a CPU.

Conceptually, execution looks like this:

```text
Virtual Thread A ─┐
Virtual Thread B ─┼── JVM scheduler ──> Carrier 1 ──> CPU
Virtual Thread C ─┤                 └─> Carrier 2 ──> CPU
Virtual Thread D ─┘                 └─> Carrier 3 ──> CPU
```

At any particular instant, only the virtual threads mounted on carriers are actually executing. Thousands of other virtual threads may exist but be suspended while waiting for sockets, database
responses, timers, locks, or other events.

This is where the scalability advantage comes from. With a traditional platform-thread-per-request architecture, a request blocked on database I/O still owns its operating-system thread. If 500
requests are waiting on PostgreSQL, the process can easily require roughly 500 application threads merely to represent that waiting.

With virtual threads, a blocking operation that the JVM understands can normally suspend the virtual thread and unmount it from the carrier:

```text
VT-42 executes application code
        ↓
mounted on Carrier-3
        ↓
JDBC read blocks
        ↓
VT-42 is suspended
        ↓
Carrier-3 becomes available
        ↓
VT-193 runs on Carrier-3
```

Oracle describes this as the central mechanism of virtual threads: when a virtual thread blocks on supported I/O, the runtime can suspend it and free the underlying carrier for another virtual thread.
Virtual threads are therefore intended to improve throughput of applications that spend substantial time waiting, not to make individual operations execute faster.

This is why synchronous JDBC suddenly becomes architecturally reasonable again in highly concurrent Java services. Blocking the **virtual thread** is usually cheap. Blocking the **carrier** is a
different matter.

## Blocking a Virtual Thread Is Not the Same as Blocking a Carrier { #blocking-vs-carrier }

The easiest mental model is to separate logical concurrency from physical execution capacity.

A virtual thread represents a unit of application work:

```text
request → controller → service → repository → response
```

A carrier represents scarce physical execution capacity.

Suppose a server has eight effective CPU cores. It may have 50,000 virtual threads alive, but that does not mean 50,000 pieces of Java code execute simultaneously. Only a relatively small number can
execute CPU instructions at any instant.

This means ordinary blocking is usually harmless only when the JVM can park or suspend the virtual thread and reuse the carrier.

Consider a request:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public User getUser(long id) {
        return repository.findById(id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun getUser(id: Long): User {
        return repository.findById(id)
    }
    ```

If the JDBC driver waits 20 ms for PostgreSQL, the virtual thread can spend most of that interval suspended. The carrier can do useful work elsewhere.

A simplified timeline could look like this:

```text
Request VT-1

CPU       JDBC wait                 CPU
│──────│  │──────────────────────│  │────│
        ↑                         ↑
      unmount                   remount


Carrier-1

VT-1      VT-7   VT-12   VT-91      VT-1
│──────│  │───│  │────│  │──────│   │────│
```

The logical request lasts perhaps 25 ms, but it occupies a carrier only during the comparatively short intervals in which Java code is actually running.

This distinction is the foundation of the virtual-thread programming model. It also explains why pinning deserves attention.

## What Pinning Actually Means { #pinning }

A virtual thread is **pinned** when the JVM cannot unmount it from its current carrier even though the virtual thread reaches an operation that blocks.

Instead of this:

```text
virtual thread blocks
        ↓
virtual thread unmounts
        ↓
carrier becomes reusable
```

we get:

```text
virtual thread blocks
        ↓
virtual thread remains mounted
        ↓
carrier blocks with it
```

The virtual thread itself is still lightweight, but that no longer helps because it has temporarily captured one of the scarce platform threads underneath the virtual-thread scheduler.

A few short pinning events usually do not matter. Production problems appear when pinning is both frequent and sufficiently long-lived that many carriers become unavailable at the same time.

Imagine eight effective carriers:

```text
Carrier 1 → pinned 800 ms
Carrier 2 → pinned 600 ms
Carrier 3 → pinned 1.2 s
Carrier 4 → pinned 700 ms
Carrier 5 → pinned 900 ms
Carrier 6 → pinned 500 ms
Carrier 7 → runnable work
Carrier 8 → runnable work
```

The application may have thousands of runnable virtual threads, but only two carriers are available to execute them. From the outside, the service can suddenly appear CPU-starved even though the CPU
itself may not be fully utilized.

That is **carrier starvation**: runnable virtual-thread work exists, but insufficient carriers are available to execute it.

The important production observation is therefore not merely "we have many virtual threads." It is whether those virtual threads spend their time either running briefly or being efficiently unmounted
while waiting.

## The `synchronized` Pinning Advice Has Changed { #synchronized-pinning-advice }

Many early virtual-thread articles contain a rule similar to:

> Do not perform blocking operations inside `synchronized`, because the virtual thread will pin its carrier.

That was correct for the virtual-thread implementation delivered in Java 21. JEP 444 documented two principal pinning situations: executing inside a `synchronized` block or method, and executing
native or foreign code. It also warned that the scheduler did not compensate for carrier loss caused by pinning.

That advice is now version-dependent.

JDK 24 delivered JEP 491, **Synchronize Virtual Threads without Pinning**. The JVM was changed so that virtual threads can normally unmount while holding Java monitors, while waiting to enter
`synchronized`, and while waiting through monitor operations. Oracle explicitly lists this as a significant JDK 24 change.

For modern Kora deployments on JDK 24 or JDK 25, this means code such as:

===! ":fontawesome-brands-java: `Java`"

    ```java
    synchronized (lock) {
        var result = client.call();
        updateState(result);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    synchronized(lock) {
        val result = client.call()
        updateState(result)
    }
    ```

should not automatically be classified as a Loom pinning problem simply because `client.call()` blocks.

That does **not** mean the code is necessarily good. Holding a monitor across network I/O can still serialize callers for hundreds of milliseconds, cause lock contention, increase tail latency, and
produce convoy effects. The semantic concurrency problem remains even though the JVM-level carrier-pinning problem has been largely removed.

That distinction is important:

```text
Java 21–23
synchronized + blocking operation
→ possible carrier pinning
→ virtual-thread scalability problem

Java 24+
synchronized + blocking operation
→ generally no monitor-induced carrier pinning
→ but ordinary lock contention may still be disastrous
```

A production review therefore has to consider the JDK version before applying Loom-era recommendations mechanically.

## Native Code Is Still Different { #native-code }

Native and foreign code remain a more fundamental problem because the JVM cannot always safely detach a continuation from the underlying native call stack.

Current Oracle documentation still describes a virtual thread as pinned when it runs a native method or foreign function.

This matters because Java applications frequently execute native code indirectly. An application might never declare a `native` method itself while still using libraries that eventually cross into JNI
or foreign functions.

Conceptually:

```text
Kora controller
    ↓
Java library
    ↓
JNI / FFM / native library
    ↓
blocking syscall or native operation
```

If a virtual thread becomes blocked while it cannot unmount, its carrier may remain occupied for the duration.

Not every native call is dangerous. A short native operation lasting microseconds is irrelevant in practice. What deserves investigation is a native boundary around something that may wait for a long
or unpredictable period: filesystem operations in unusual libraries, native database clients, compression libraries with internal blocking, security modules, native DNS implementations, hardware
integrations, or third-party libraries whose threading model was designed long before virtual threads existed.

The production question is therefore not "does this dependency use JNI?" but:

```text
Can it block while the virtual thread cannot unmount?
×
How frequently does that happen?
×
How long can it last?
```

A rare 100 μs pin is noise. Thousands of simultaneous 500 ms pins can become an outage.

## Carrier Starvation Is Not the Only Way to Lose { #carrier-starvation-not-only }

It would be a mistake to make pinning the center of every virtual-thread production investigation. On modern JDKs, particularly after JEP 491, ordinary resource saturation is likely to matter more
often.

Consider a service where every request performs one JDBC query:

```text
Client
  ↓
Kora HTTP request virtual thread
  ↓
Service
  ↓
JDBC repository
  ↓
Hikari connection pool
  ↓
PostgreSQL
```

Kora can easily create enough virtual threads to represent 20,000 concurrent requests. PostgreSQL probably cannot execute 20,000 queries from one application instance efficiently, and the connection
pool will not permit it anyway.

Kora's JDBC module deliberately keeps this resource bounded. In Kora 2, JDBC is backed by a Hikari connection pool; `maxPoolSize` defaults to `10`, while `connectionTimeout` controls how long callers
may wait to acquire a connection. The JDBC telemetry can also expose pool-level metrics such as connection acquisition time.

Suppose:

```text
20,000 request virtual threads
             ↓
       10 DB connections
             ↓
         PostgreSQL
```

At most roughly ten connection-holding database operations from this pool can proceed concurrently. The other database-bound requests wait.

Virtual threads make that waiting cheap from the JVM-thread perspective, which is excellent. But they do not make it disappear.

The queue has merely moved.

## Virtual Threads Remove a Thread Limit, Not a Concurrency Limit { #thread-limit-vs-concurrency }

Before virtual threads, the worker pool often served two purposes at once.

It was an execution mechanism:

```text
200 worker threads
```

but it was also an accidental admission-control mechanism:

```text
at most ~200 request tasks actively occupy workers
```

Once the application switches to one virtual thread per request, that accidental concurrency bound can vanish.

This is usually desirable because platform-thread availability is a poor way to express business or infrastructure capacity. But the application must then become explicit about the limits that
actually matter.

For example:

```text
Virtual threads        effectively abundant
CPU                     bounded
JDBC connections        bounded
PostgreSQL capacity     bounded
remote API concurrency  bounded
Kafka partitions        bounded
file descriptors        bounded
memory                   bounded
```

Oracle's virtual-thread guidance makes the same distinction: virtual threads should generally not be pooled merely to restrict their count. When access to a limited resource must be constrained, use
an explicit concurrency mechanism such as a semaphore rather than turning virtual threads back into a traditional fixed thread pool.

A virtual-thread executor therefore answers:

> How should I represent concurrent tasks?

It does not answer:

> How many operations should my database, payment provider, GPU, filesystem, or downstream service receive simultaneously?

Those are different problems.

## The Connection Pool Becomes an Explicit Backpressure Boundary { #connection-pool-backpressure }

A JDBC connection pool is more than an optimization that avoids opening TCP connections repeatedly. It is a concurrency boundary between the application and the database.

With ten connections:

```text
                  ┌─ connection 1 ─┐
                  ├─ connection 2  │
requests ───────> │       ...      ├──> database
                  └─ connection 10 ┘
```

Only ten callers can own connections at once.

With platform threads, requests waiting for those connections consumed worker threads, so thread-pool exhaustion often appeared shortly after connection-pool exhaustion.

With virtual threads, thousands of callers can wait cheaply:

```text
5000 virtual threads waiting
            ↓
     Hikari pool (10)
            ↓
       PostgreSQL
```

This can be a major improvement because application execution capacity is no longer wasted just because requests are waiting for a scarce resource.

But it also creates a new failure mode: an enormous cheap queue.

Cheap does not mean harmless. Every waiting request still has associated objects, request state, tracing state, buffers, deadlines, socket state, and possibly upstream callers waiting for a response.
More importantly, a long queue increases latency and can preserve work that should already have been rejected.

Assume a database can sustainably complete 1,000 requests per second while 10,000 requests suddenly arrive.

Allowing all 10,000 to become virtual threads does not increase database throughput:

```text
arrival rate        10,000 req/s
database capacity    1,000 req/s
difference          +9,000 req/s
```

The queue grows by roughly 9,000 requests every second while overload continues.

Virtual threads make it possible for the JVM to hold that queue longer. They do not make the system stable.

This is why timeouts, bulkheads, rate limits, load shedding, bounded queues, and explicit concurrency controls remain first-class production concerns in a virtual-thread architecture.

## Little's Law Still Wins { #littles-law }

One of the most useful formulas for reasoning about these systems is Little's Law:

```text
L = λ × W
```

where:

```text
L = average number of operations in the system
λ = throughput / arrival rate
W = average time each operation spends in the system
```

In practical backend terminology:

```text
concurrency ≈ throughput × latency
```

Suppose a service handles 2,000 requests per second with an average end-to-end latency of 50 ms:

```text
L = 2,000 × 0.050
L = 100
```

On average, roughly 100 requests must be in flight.

Virtual threads make representing those 100 requests easy. They also make representing 1,000 or 10,000 requests technically possible. But Little's Law tells us something more important: concurrency
rises automatically when latency rises.

Suppose the arrival rate remains 2,000 RPS but the database slows down and end-to-end latency becomes 500 ms:

```text
L = 2,000 × 0.500
L = 1,000
```

The service now needs roughly ten times as many requests in flight to sustain the same throughput.

Nothing about client traffic changed.

Only latency changed.

This is one of the mechanisms behind cascading overload:

```text
downstream slows
      ↓
request latency grows
      ↓
in-flight concurrency grows
      ↓
pools and queues fill
      ↓
waiting time grows
      ↓
latency grows further
      ↓
timeouts / retries
      ↓
even more work
```

Virtual threads solve the "we ran out of OS-backed Java threads" step. They cannot solve the queueing system itself.

## Little's Law Applied to the Database Pool { #littles-law-db-pool }

Little's Law becomes even more useful if we apply it specifically to the interval during which a request owns a database connection.

Assume:

```text
request rate requiring DB = 1,500 req/s
average connection hold   = 8 ms
```

Then the average connection concurrency is approximately:

```text
L = 1,500 × 0.008
L = 12
```

That suggests approximately 12 connections are simultaneously required on average for that workload, before accounting for variance, burstiness, transactions, tail latency, and operational headroom.

Now suppose a database regression increases connection hold time from 8 ms to 40 ms:

```text
L = 1,500 × 0.040
L = 60
```

The required concurrency has increased fivefold even though traffic has not changed.

If the pool contains 20 connections, requests start waiting for connection acquisition. Once they wait, end-to-end latency rises. If callers have aggressive retries, additional traffic may arrive. The
system can move rapidly from normal operation into an overload regime.

This illustrates why blindly changing:

===! ":material-code-json: Hocon"

    ```hocon
    jdbc {
        maxPoolSize = 10
    }
    ```

=== ":simple-yaml: YAML"

    ```yaml
    jdbc:
      maxPoolSize: 10
    ```

to:

===! ":material-code-json: Hocon"

    ```hocon
    jdbc {
        maxPoolSize = 200
    }
    ```

=== ":simple-yaml: YAML"

    ```yaml
    jdbc:
      maxPoolSize: 200
    ```

is not necessarily a fix.

It may merely transfer the queue from the application into PostgreSQL. If the database can efficiently execute only 30 concurrent queries for this workload, giving it 200 connections can increase CPU
contention, memory usage, lock contention, cache pressure, and query latency.

The correct pool size is therefore not "as large as virtual-thread concurrency."

It is a controlled interface to database capacity.

## A Load Spike Through a Kora Service { #load-spike-kora-service }

Consider a Kora service receiving a sudden traffic spike.

Under normal conditions:

```text
2,000 RPS
   ↓
~100 in-flight virtual threads
   ↓
20 JDBC connections
   ↓
PostgreSQL
```

Everything is healthy.

Traffic then jumps to 6,000 RPS.

Because Kora can create virtual threads cheaply, accepting the requests does not immediately exhaust a conventional HTTP worker pool:

```text
6,000 RPS
   ↓
many request virtual threads
   ↓
20 JDBC connections
   ↓
PostgreSQL
```

If PostgreSQL and the pool can actually sustain the new throughput, the system may scale beautifully. This is the scenario virtual threads are designed for: many requests spend much of their lifetime
waiting, and carriers remain available for useful Java execution.

Now assume PostgreSQL can sustainably deliver only 2,500 of those operations per second.

The architecture becomes:

```text
arrival: 6,000/s
     ↓
virtual-thread requests
     ↓
queue for connections
     ↓
capacity: 2,500/s
```

Approximately 3,500 more requests arrive each second than the database path can finish. After ten seconds, the system may have tens of thousands of additional requests waiting somewhere in the request
path.

The JVM may still look surprisingly healthy. There may be no 10,000-platform-thread explosion. CPU may not initially look catastrophic. This is precisely why virtual-thread production monitoring must
include resource queues rather than merely thread counts.

The application can be overloaded while the virtual-thread machinery is working perfectly.

## What Carrier Starvation Looks Like During a Spike { #carrier-starvation-spike }

A different scenario occurs if a request path enters a blocking native operation that pins carriers.

Imagine an application with eight useful carrier threads and an external native library call:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public Result process(Request request) {
        return nativeClient.execute(request);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun process(request: Request): Result {
        return nativeClient.execute(request)
    }
    ```

During ordinary traffic only one or two requests use this path concurrently, so nothing unusual happens.

During a spike, eight calls block inside native code:

```text
Carrier 1 → native call → blocked
Carrier 2 → native call → blocked
Carrier 3 → native call → blocked
Carrier 4 → native call → blocked
Carrier 5 → native call → blocked
Carrier 6 → native call → blocked
Carrier 7 → native call → blocked
Carrier 8 → native call → blocked
```

Meanwhile:

```text
VT-101 runnable
VT-102 runnable
VT-103 runnable
...
VT-5000 runnable
```

The system now has application work ready to execute but insufficient carrier capacity.

Symptoms can include sharply increasing response latency, unexpectedly low useful throughput, runnable virtual threads accumulating, and behavior that looks inconsistent with normal CPU saturation.

This is the scenario where pinning analysis is justified.

But it is fundamentally different from:

```text
5000 VTs parked waiting for 20 JDBC connections
```

In the latter case, the scheduler is doing exactly what it should. The bottleneck is the database concurrency boundary, not the carriers.

Distinguishing those two situations is critical during incident response.

## CPU-Bound Work Has the Same Fundamental Limit { #cpu-bound-work }

Virtual threads are optimized for workloads containing waiting. They do not increase the amount of CPU available.

Suppose a request performs 100 ms of pure CPU computation:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public Result calculate(Input input) {
        return expensiveCalculation(input);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun calculate(input: Input): Result {
        return expensiveCalculation(input)
    }
    ```

With eight cores, creating 10,000 virtual threads running this computation does not produce 10,000-way useful parallelism.

It produces contention for approximately eight cores:

```text
10,000 runnable VTs
        ↓
limited carriers
        ↓
8 CPU cores
```

Throughput remains governed primarily by CPU capacity.

If one request consumes 100 ms of one core, a rough idealized upper bound is:

```text
8 cores / 0.1 CPU-seconds
≈ 80 operations/s
```

Creating more virtual threads cannot change the arithmetic.

In fact, uncontrolled CPU-bound virtual-thread creation can make tail latency worse because more runnable tasks compete for the same fixed execution capacity. This is another case where explicit
concurrency limiting may be appropriate.

The correct conceptual model is:

```text
Virtual threads scale waiting.

They do not scale silicon.
```

## Request Concurrency and Resource Concurrency Should Be Separated { #request-vs-resource-concurrency }

A useful virtual-thread architecture separates two questions.

The first is how many logical requests may exist:

```text
HTTP requests
→ one virtual thread per request
```

The second is how much concurrency each scarce subsystem should receive:

```text
database             → connection pool
remote partner API   → semaphore / bulkhead
CPU-heavy algorithm  → concurrency limit
GPU                   → explicit queue
filesystem           → workload-specific limit
```

This is more precise than using one global worker pool to control everything.

Traditional systems often had:

```text
200 HTTP workers
```

and accidentally used that number as the limit for database requests, HTTP calls, CPU work, filesystem operations, and every other downstream dependency.

Virtual threads encourage a better architecture:

```text
many logical request VTs

        ├── DB bulkhead:         20
        ├── payment API:         50
        ├── search backend:     100
        └── CPU-heavy work:       8
```

Each boundary can now reflect the capacity of the resource it protects.

That is a significant architectural advantage, but only if those limits are actually designed.

## Connection Pools Are Still Pools for a Reason { #connection-pools-reason }

A common question is whether JDBC connection pools should become much larger now that virtual threads make blocking cheap.

Usually, no general rule like that exists.

Virtual threads change the cost of **waiting for a connection**. They do not change the cost of the connection itself or make the database infinitely parallel.

A PostgreSQL connection still represents real server-side state and execution capacity. A transaction can still hold locks. Long-running queries can still consume CPU. Too many active sessions can
still compete for caches and memory.

The pool therefore remains useful for several reasons:

```text
reuse expensive database connections
+
bound database concurrency
+
create a queue in front of the database
+
provide acquisition timeouts
+
expose saturation metrics
```

Kora's JDBC defaults make these controls explicit. The Kora 2 JDBC configuration exposes `maxPoolSize`, `connectionTimeout`, validation settings, lifetime settings, leak detection, and driver metrics.

Virtual threads simply make the caller waiting behind that pool much cheaper than a platform thread would have been.

That is an improvement in implementation efficiency, not permission to ignore capacity planning.

## Timeouts Become More Important, Not Less { #timeouts }

Because virtual threads make it inexpensive to wait, systems can tolerate much larger numbers of waiting operations before JVM thread exhaustion forces the problem into view.

That makes deadlines and timeouts more important.

Consider:

```text
DB capacity temporarily collapses
        ↓
10,000 virtual threads wait
        ↓
DB recovers
        ↓
all surviving requests compete to continue
```

If those requests are already useless because upstream clients gave up several seconds earlier, continuing them merely generates stale work.

A production system should therefore define how long work remains valuable at each boundary.

For JDBC, connection acquisition should not wait forever. Kora exposes `connectionTimeout` for that purpose.

For HTTP clients, request deadlines should reflect the caller's end-to-end budget rather than an arbitrary very large socket timeout.

For structured fan-out, child operations should remain bounded by the request deadline.

Timeouts are not just failure handling. They are part of overload control because they determine how quickly obsolete work leaves queues.

## Retries Can Turn Latency Into an Outage { #retries-latency-outage }

Virtual threads also make retry loops syntactically harmless:

===! ":fontawesome-brands-java: `Java`"

    ```java
    for (int attempt = 0; attempt < 3; attempt++) {
        try {
            return client.call();
        } catch (IOException e) {
            // retry
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    for (attempt in 0 until 3) {
        try {
            return client.call()
        } catch (e: IOException) {
            // retry
        }
    }
    ```

The thread cost may be low, but the downstream cost is not.

If a service already receives 5,000 RPS and its dependency begins timing out, three immediate retries can transform the attempted workload into something approaching:

```text
5,000 original calls
+
5,000 retry #1
+
5,000 retry #2
=
15,000 attempted calls/s
```

The dependency becomes slower, Little's Law increases in-flight concurrency, more requests time out, and even more retry traffic appears.

Virtual threads have nothing to do with preventing this feedback loop.

Resilience policies still need bounded retries, backoff, jitter, deadlines, circuit breaking, and load shedding.

The broader lesson is that virtual threads improve the mechanics of waiting without changing the economics of the resources being waited on.

## Diagnosing Pinning Instead of Guessing { #diagnosing-pinning }

When a production service shows unexpected virtual-thread scalability behavior, pinning should be measured rather than inferred from code style.

The JDK provides virtual-thread-aware diagnostics through Java Flight Recorder and thread dumps. Oracle documents JFR events for virtual threads and `jcmd Thread.dump_to_file`, which can show both
platform and virtual threads.

On older JDKs, pinning diagnostics were particularly important for locating blocking operations executed while holding monitors. On current JDKs, native or foreign frames deserve more attention
because ordinary monitor-based pinning has been removed from the normal locking implementation.

A production investigation should correlate thread information with resource telemetry. The useful question is not simply whether many virtual threads exist, but what state they are in and what
resource they are waiting for.

For example:

```text
many parked VTs
+ JDBC pool active = max
+ JDBC acquire latency rising
→ database/pool saturation

many runnable VTs
+ CPU near 100%
→ CPU saturation

many runnable VTs
+ carriers blocked in native frames
+ CPU unexpectedly low
→ possible carrier starvation / pinning

many waiting VTs
+ remote HTTP p99 exploding
→ downstream saturation

many VTs
+ normal latency
+ normal queues
→ probably entirely healthy
```

The raw virtual-thread count by itself is therefore a weak operational signal.

## What to Monitor in a Kora Service { #monitoring-kora-service }

A virtual-thread-first Kora service should be observed as a chain of queues and resource boundaries rather than as one giant thread pool.

The most useful operational picture combines:

- HTTP request rate, active requests, p50/p95/p99 latency, timeouts, and rejected work; virtual-thread and carrier diagnostics when scheduler problems are suspected; CPU utilization and runnable
  pressure; JDBC active, idle, pending, acquisition-time, and timeout metrics; database query latency and database-side CPU/lock/session metrics; downstream HTTP latency and concurrency; resilience
  events such as timeouts, retries, circuit-breaker openings, and bulkhead saturation; JVM heap, allocation rate, GC, and socket/file-descriptor pressure.

Kora already integrates metrics and tracing throughout its modules, and its JDBC integration can expose Hikari pool statistics such as pool size and connection acquisition time.

The important shift is to stop treating "number of threads" as the primary capacity metric. In a virtual-thread service, a large thread count can be completely normal.

Queue depth and saturation tell a much more useful story.

## Why Unlimited Virtual Threads Must Not Mean Unlimited Admission { #unlimited-vt-admission }

One of the best properties of virtual threads is that developers no longer need to conserve threads as if they were database connections.

One of the most dangerous misunderstandings of virtual threads is concluding that no concurrency limit is required anywhere.

The two ideas are compatible:

```text
virtual threads:
create freely for logical tasks

scarce resources:
bound deliberately
```

A server can therefore accept an HTTP request into a virtual thread without reserving a heavyweight operating-system thread, while still refusing or delaying operations when a specific subsystem
reaches its safe concurrency limit.

For example:

===! ":fontawesome-brands-java: `Java`"

    ```java
    private final Semaphore paymentConcurrency = new Semaphore(40);

    public PaymentResult charge(Payment payment) throws InterruptedException {
        paymentConcurrency.acquire();
        try {
            return paymentClient.charge(payment);
        } finally {
            paymentConcurrency.release();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    private val paymentConcurrency = Semaphore(40)

    fun charge(payment: Payment): PaymentResult {
        paymentConcurrency.acquire()
        try {
            return paymentClient.charge(payment)
        } finally {
            paymentConcurrency.release()
        }
    }
    ```

The semaphore is not compensating for expensive Java threads. It is expressing a real domain constraint:

```text
the payment service should see at most 40 concurrent calls
```

That distinction is exactly what Oracle recommends conceptually: do not pool virtual threads simply to limit their number; use explicit controls when a scarce resource requires bounded concurrency.

This produces a cleaner architecture because concurrency limits live next to the resources whose capacity they describe.

## Kora Makes the Resource Boundaries Easier to See { #kora-resource-boundaries }

Kora 2's synchronous model is particularly suitable for this style of reasoning because the execution path stays direct.

A repository call looks like a repository call:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var user = repository.findById(id);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val user = repository.findById(id)
    ```

An HTTP client call looks like an HTTP client call:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var profile = profileClient.getProfile(id);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val profile = profileClient.getProfile(id)
    ```

A transaction looks like synchronous transactional work.

The framework does not require every blocking boundary to be translated into a chain of publishers, callbacks, or suspended functions. Kora explicitly describes its controllers, clients, repositories,
and schedulers as ordinary synchronous APIs executed on virtual threads.

As a result, the production architecture can be reasoned about in the same shape as the source code:

```text
request VT
   ↓
controller
   ↓
service
   ├── JDBC → Hikari pool → PostgreSQL
   ├── HTTP → remote-service bulkhead → remote service
   └── CPU work → CPU
```

The concurrency model is not hidden. Each operation blocks naturally, while each truly scarce resource retains its own explicit capacity boundary.

That is arguably a more important consequence of virtual threads than simply "Java can create lots of threads."

## A Better Mental Model for Load Spikes { #mental-model-load-spikes }

The wrong model is:

```text
Virtual threads are cheap
→ we can process unlimited concurrent requests
```

A better model is:

```text
Virtual threads are cheap
→ requests can wait without consuming one platform thread each
→ the application can represent much more concurrency
→ therefore real resource limits become more visible and more important
```

During a spike, trace the request through each capacity boundary:

```text
Incoming traffic
      ↓
HTTP admission
      ↓
Virtual thread
      ↓
CPU
      ↓
DB connection pool
      ↓
Database
      ↓
Remote dependency
```

At every stage ask two questions:

```text
What is the sustainable throughput?

How much queueing are we willing to permit before rejecting work?
```

If arrivals exceed sustainable departures, a queue grows somewhere. Virtual threads can make that queue cheap in terms of operating-system threads, but queueing theory has not changed.

Eventually one of four things must happen:

```text
capacity increases
work completes faster
new work is rejected
or latency grows without bound
```

There is no fifth outcome in which virtual threads somehow absorb an unlimited overload.

## Production Example: Healthy Virtual-Thread Scaling { #example-healthy-scaling }

Consider a Kora service deployed on eight cores.

Normal load:

```text
3,000 RPS
average latency: 40 ms
```

Little's Law gives:

```text
L = 3,000 × 0.040
  = 120 in-flight requests
```

Each request performs about 2 ms of CPU work and waits approximately 30 ms on network or database I/O.

This is an excellent virtual-thread workload. Most of the lifetime of each request is waiting, so virtual threads frequently unmount and carriers remain available.

Traffic doubles:

```text
6,000 RPS
```

If the database and downstream services can handle the increase, expected average concurrency becomes approximately:

```text
6,000 × 0.040 = 240
```

Representing 240 request threads is trivial for virtual threads. No large platform-thread pool is required, and synchronous code can continue to scale efficiently.

This is the success case.

## Production Example: Database Saturation { #example-db-saturation }

Now use the same service but assume the database can sustain only about 3,500 operations per second.

Traffic reaches 6,000 RPS.

Virtual-thread creation is still fine. Carrier behavior is still fine. There may be zero problematic pinning.

Nevertheless:

```text
incoming DB demand: 6,000/s
DB completion rate: 3,500/s
```

A queue forms around the connection pool.

Connection acquisition latency rises from:

```text
1 ms
```

to:

```text
20 ms
100 ms
500 ms
2 s
...
```

End-to-end latency rises with it. Little's Law then predicts more in-flight requests. More request state remains resident in memory. Eventually acquisition deadlines expire.

This is not a Loom failure.

It is ordinary database overload expressed through a virtual-thread architecture.

The fix could involve reducing query cost, adding database capacity, caching, reducing DB operations per request, adjusting pool sizing within the database's real capacity, adding load shedding, or
scaling application/database topology.

Increasing the number of virtual threads would accomplish nothing because virtual-thread availability was never the bottleneck.

## Production Example: Carrier Starvation { #example-carrier-starvation }

Finally, consider a native library that occasionally blocks for two seconds.

Under normal traffic:

```text
1 pinned operation
→ negligible
```

During a burst:

```text
many pinned native operations
→ many carriers unavailable
```

Runnable virtual threads begin accumulating even though downstream pools are not saturated.

This is where replacing or isolating the native operation may matter. Depending on the library and workload, it may be appropriate to update the dependency, change the API being used, move problematic
work behind a bounded dedicated executor, redesign the integration, or otherwise prevent the blocking native section from capturing the carriers used for normal request processing.

The important point is that the mitigation should target the actual pinned operation rather than introducing a general fixed worker pool around all application code and thereby discarding the benefits
of virtual threads.

## Do Not Rebuild the Old Thread-Pool Architecture { #no-old-thread-pool }

A common migration mistake looks like this:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var executor = Executors.newFixedThreadPool(200);

    executor.submit(() -> {
        repository.findById(id);
    });
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val executor = Executors.newFixedThreadPool(200)

    executor.submit {
        repository.findById(id)
    }
    ```

inside an application that is already executing the request on a virtual thread.

The intention is often safety: "we should bound the virtual threads."

But if the real resource being protected is PostgreSQL, a 200-thread executor is an indirect and inaccurate way to express that constraint.

The better boundary is usually the database connection pool or another explicit concurrency mechanism.

Similarly, if only one CPU-intensive subsystem should run eight tasks concurrently, there is little reason to restrict unrelated HTTP waiting, cache access, or JDBC waits to those same eight slots.

Virtual threads let us stop using worker-thread scarcity as a universal traffic-control mechanism.

That is a feature worth preserving.

## The Practical Rules { #practical-rules }

For production Kora applications, a useful operating model is to keep request code synchronous and allow Kora's virtual-thread model to do what it was designed to do, while treating every scarce
external or physical resource as a separate capacity problem. Blocking JDBC and HTTP calls are not inherently suspicious. Long native blocking deserves investigation. `synchronized` deserves normal
lock-design scrutiny, but on JDK 24+ it should no longer automatically be treated as the Loom pinning hazard described in Java 21-era material. Database pools should be sized according to workload and
database capacity rather than virtual-thread count, and overload controls should prevent cheap virtual-thread queues from growing without useful bounds.

Most importantly, observe queueing and saturation instead of counting threads. If latency doubles while arrival rate stays constant, Little's Law says concurrency pressure doubles too. That remains
true whether the implementation uses platform threads, virtual threads, coroutines, an event loop, or reactive streams.

## Conclusion { #conclusion }

Virtual threads fundamentally improve the economics of blocking Java.

They allow Kora 2 to use a simple synchronous programming model without returning to the old scalability limit where every blocked request monopolized an expensive operating-system thread. A Kora
controller can call a repository, the repository can execute JDBC, and the request virtual thread can wait naturally while its carrier is reused for other work. That brings thread-per-request
programming back to high-concurrency backend systems without requiring application code to be organized around asynchronous control flow.

But virtual threads solve a very specific resource problem.

They make **threads** abundant.

They do not make **CPU cycles, database connections, database execution slots, remote-service capacity, memory, sockets, native execution, or time** abundant.

Pinning is one way this abstraction can leak. On Java 21 through 23, blocking while holding a monitor could pin a virtual thread to its carrier; since JDK 24, JEP 491 has removed that monitor-induced
pinning from the normal locking implementation, making much older Loom advice obsolete. Native and foreign operations can still pin, so long-running native blocking remains something worth finding and
measuring.

For most production services, however, the more important challenge is likely to be ordinary resource saturation. A Kora application may be perfectly capable of creating another 50,000 virtual threads
while its ten JDBC connections are already busy and PostgreSQL is at its useful concurrency limit. In that situation, more concurrency is not additional capacity. It is additional queueing.

That is the central production lesson:

```text
Virtual threads remove the thread-per-request scalability ceiling.

They do not remove the system's capacity ceiling.
```

A well-designed virtual-thread service therefore combines abundant logical concurrency with deliberately bounded physical concurrency. Kora supplies the simple execution model; connection pools,
deadlines, resilience policies, bulkheads, database capacity planning, and queueing theory define how that model survives real traffic.

Once that distinction is clear, virtual threads become much easier to reason about in production. The question is no longer whether blocking itself is dangerous.

The question is **what resource the request is waiting for, how much concurrency that resource can safely sustain, and what the system does when demand exceeds it**.
