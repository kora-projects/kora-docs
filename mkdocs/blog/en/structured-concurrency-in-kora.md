---
title: Structured Concurrency in Kora Framework Applications
date: 2026-08-31
description: How Java structured concurrency (StructuredTaskScope) fits the Kora Framework's synchronous virtual-thread model — fan-out, failure domains, deadlines, cancellation, and keeping parallelism local.
search:
  exclude: true
---

# Structured Concurrency in Kora Applications { #structured-concurrency }

**August 31, 2026**

Modern backend services are rarely sequential. A single HTTP request may need to load a user profile, retrieve recent orders, calculate permissions, call one or more external services, and fetch
recommendations before it can construct the final response. When those operations are independent, executing them one after another creates avoidable latency. A profile request taking 40 milliseconds,
an order request taking 60 milliseconds, and a recommendation request taking 80 milliseconds produce roughly 180 milliseconds of waiting when executed sequentially. If they are started together, the
same operation can approach the latency of the slowest branch instead, roughly 80 milliseconds plus coordination overhead.

Starting several operations concurrently is not the difficult part. Java has provided executors, futures, parallel streams, `CompletableFuture`, and many other mechanisms for doing that for years. The
difficult part is defining the lifecycle of those concurrent operations. If the orders request fails, should recommendations continue running? If the HTTP request reaches its deadline, how are the
child operations stopped? If one child fails immediately while two others are blocked in I/O, who owns their cancellation? Can those tasks accidentally continue after the parent request has already
returned an error? How is the tracing context propagated into them?

Structured concurrency is designed to answer those questions. Instead of treating concurrent tasks as independent pieces of work submitted to some executor, it treats them as children of a larger
operation. Their lifetime, failure handling, cancellation, and completion are tied to the lexical scope that created them. For Kora Framework applications, this model fits particularly well because the
framework deliberately uses ordinary synchronous method signatures together with virtual threads. A controller or service remains synchronous from the caller's perspective, while a local section of
that operation can fan out into several concurrent virtual threads when parallelism is actually beneficial.

The result is a model where synchronous does not mean sequential. A method such as `Dashboard load(long userId)` can remain an ordinary blocking method while internally executing several independent
operations concurrently. The caller still gets a simple completion contract: when the method returns, the operation is complete; when it throws, the operation has failed. There is no need to expose
`Future`, `CompletionStage`, `Mono`, `Uni`, or another asynchronous abstraction throughout the application simply because one particular orchestration step benefits from parallel execution.

---

## Kora 2 and the Return to Synchronous Application Code { #kora-2-synchronous }

Kora 2 is designed around direct synchronous application code. HTTP controllers, repositories, clients, scheduled operations, and other framework contracts use ordinary Java and Kotlin method
signatures, while virtual threads provide the execution model underneath them. This allows application code to perform blocking JDBC, HTTP, gRPC, filesystem, or other I/O without requiring every layer
to be expressed as an asynchronous pipeline.

A normal Kora service can therefore remain straightforward:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class UserService {

        private final UserRepository repository;

        public UserService(UserRepository repository) {
            this.repository = repository;
        }

        public User get(long id) {
            return repository.findById(id);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class UserService(private val repository: UserRepository) {

        fun get(id: Long): User {
            return repository.findById(id)
        }
    }
    ```

Most code should stay exactly like this. Structured concurrency is not intended to replace normal method calls or to make every operation parallel. It becomes useful when one logical operation
contains several independent pieces of work whose latency can overlap.

Consider a service that builds a dashboard:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public Dashboard getDashboard(long userId) {
        var profile = profileClient.get(userId);
        var orders = orderClient.getRecent(userId);
        var recommendations = recommendationClient.get(userId);

        return new Dashboard(profile, orders, recommendations);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun getDashboard(userId: Long): Dashboard {
        val profile = profileClient.get(userId)
        val orders = orderClient.getRecent(userId)
        val recommendations = recommendationClient.get(userId)

        return Dashboard(profile, orders, recommendations)
    }
    ```

The code is simple, but the calls are sequential. If the three operations take 40, 70, and 90 milliseconds respectively, the service spends roughly 200 milliseconds waiting for them even though none
depends on the result of another. The dependency graph is parallel, but the implementation is sequential.

Structured concurrency allows the implementation to match the actual dependency graph without changing the surrounding synchronous API.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public Dashboard getDashboard(long userId) throws InterruptedException {
        try (var scope = StructuredTaskScope.open()) {
            var profile = scope.fork(() -> profileClient.get(userId));
            var orders = scope.fork(() -> orderClient.getRecent(userId));
            var recommendations = scope.fork(() -> recommendationClient.get(userId));

            scope.join();

            return new Dashboard(
                profile.get(),
                orders.get(),
                recommendations.get()
            );
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun getDashboard(userId: Long): Dashboard {
        StructuredTaskScope.open<Any>().use { scope ->
            val profile = scope.fork { profileClient.get(userId) }
            val orders = scope.fork { orderClient.getRecent(userId) }
            val recommendations = scope.fork { recommendationClient.get(userId) }

            scope.join()

            return Dashboard(
                profile.get(),
                orders.get(),
                recommendations.get()
            )
        }
    }
    ```

The important point is not merely that three virtual threads can execute at the same time. The important point is that all three tasks belong to the same scope. The scope establishes a structural
relationship between the parent operation and its children, and that relationship determines when the parent may complete and what happens when something fails or is cancelled.

---

## Structured Concurrency Is Primarily About Ownership { #ownership }

It is easy to mistake structured concurrency for a more convenient syntax for submitting tasks. Its main advantage, however, is not shorter code but explicit ownership.

With an executor, an application can submit several tasks:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var profile =
        executor.submit(() -> profileClient.get(userId));

    var orders =
        executor.submit(() -> orderClient.getRecent(userId));

    var recommendations =
        executor.submit(() -> recommendationClient.get(userId));
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val profile =
        executor.submit(Callable { profileClient.get(userId) })

    val orders =
        executor.submit(Callable { orderClient.getRecent(userId) })

    val recommendations =
        executor.submit(Callable { recommendationClient.get(userId) })
    ```

At that point, the application has created several independent pieces of work and received handles to them. The lifecycle relationship between those tasks and the original request exists only because
the developer remembers to maintain it. If the orders task fails, recommendations may continue running unless the application explicitly cancels it. If the parent method exits early, another task may
still be consuming a connection, generating telemetry, performing remote I/O, or even producing side effects.

Structured concurrency makes that relationship part of the program structure. A request-scoped operation conceptually becomes a tree:

```text
Request
└── Dashboard operation
    ├── Profile
    ├── Orders
    └── Recommendations
```

The children exist as part of the dashboard operation and are not conceptually detached from it. The parent cannot silently complete while structured children continue running indefinitely elsewhere.
When the lexical scope ends, the application has a clear completion boundary.

This is similar to why structured resource management is easier to reason about than manually tracking resources. A `try-with-resources` block makes it clear where a file, stream, or connection
belongs and when it must be closed. Structured concurrency applies the same principle to concurrent tasks. The scope is not just where tasks happen to be started; it is the owner of their lifetime.

---

## Fan-Out as a Local Orchestration Pattern { #fan-out }

The most obvious use case for `StructuredTaskScope` is fan-out. An incoming request reaches an orchestration layer where several independent dependencies can be queried simultaneously, and their
results are combined before returning the response. Typical examples include API aggregation endpoints, dashboards, search enrichment, pricing aggregation, permission loading, or retrieving
independent sections of a user page.

A useful rule is to parallelize independent latency rather than arbitrary code. If two calls are independent, such as retrieving a profile and loading recent orders, they are natural candidates for
fan-out. If the second call needs data produced by the first, the operations form a dependency chain and should remain sequential at that point.

For example:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var customer = customerClient.get(customerId);

    try (var scope = StructuredTaskScope.open()) {
        var orders = scope.fork(() -> orderClient.get(customer.id()));
        var permissions = scope.fork(() -> permissionsClient.get(customer.id()));
        var loyalty = scope.fork(() -> loyaltyClient.get(customer.id()));

        scope.join();

        return build(
            customer,
            orders.get(),
            permissions.get(),
            loyalty.get()
        );
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val customer = customerClient.get(customerId)

    StructuredTaskScope.open<Any>().use { scope ->
        val orders = scope.fork { orderClient.get(customer.id) }
        val permissions = scope.fork { permissionsClient.get(customer.id) }
        val loyalty = scope.fork { loyaltyClient.get(customer.id) }

        scope.join()

        return build(
            customer,
            orders.get(),
            permissions.get(),
            loyalty.get()
        )
    }
    ```

Here, loading the customer is necessarily the first stage because the following operations depend on the resolved customer identifier or other customer data. Once that dependency is satisfied, several
independent branches can start in parallel. This produces a concurrency structure that mirrors the actual domain graph instead of flattening the entire request into one large batch.

That distinction matters. Virtual threads make creating concurrent tasks inexpensive, but cheap threads are not a reason to introduce parallelism where no real concurrency exists. The structured scope
should describe genuine independence between operations.

---

## Failure Propagation as Part of the Operation { #failure-propagation }

Concurrent execution becomes much more interesting when one branch fails. Suppose profile loading succeeds, order loading fails, and recommendations are still running. If all three results are
required to construct the response, continuing the recommendations request no longer provides value. The overall logical operation has already become impossible to complete successfully.

This is where structured concurrency provides semantics that are much stronger than simple task submission. Instead of treating every branch as an unrelated future, the parent scope can treat them as
one failure domain. When a mandatory child fails, the parent operation can fail and the remaining unnecessary work can be cancelled.

Conceptually, the execution may look like this:

```text
             profile -------- SUCCESS
            /
request ---+--- orders ------- FAILURE
            \
             recommendations - CANCELLED
```

The important architectural question is whether the children really belong to the same failure domain. If all results are mandatory, a fail-together policy is natural. If some results are optional,
the application should model that intentionally instead of applying fail-fast semantics blindly.

Consider a product page where the product itself and its price are mandatory but recommendations are optional. A recommendation failure does not necessarily justify failing the entire request. In that
case, the optional branch can degrade locally:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var recommendations = scope.fork(() -> {
        try {
            return recommendationClient.get(userId);
        } catch (RecommendationUnavailableException e) {
            return List.of();
        }
    });
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val recommendations = scope.fork {
        try {
            recommendationClient.get(userId)
        } catch (e: RecommendationUnavailableException) {
            emptyList()
        }
    }
    ```

This makes the business rule explicit: recommendation unavailability is an acceptable degraded result. The scope can still represent the mandatory success semantics of the overall request while
optional dependencies translate their failures into domain-level fallback values.

The key is that failure policy belongs to the logical operation, not to the concurrency primitive itself. Structured concurrency makes it easier to express that policy, but the application still has
to decide whether one failing child invalidates the whole result.

---

## Cancellation and Cooperative Termination { #cancellation }

Cancellation is one of the strongest reasons to prefer structured concurrency over casual executor usage. When the parent no longer needs a child task, the child can be cancelled as part of the same
structured operation. This prevents requests from leaving behind unnecessary work after failure or timeout.

In Java, cancellation is usually cooperative. A running task is not forcibly destroyed; interruption is used to signal that the operation should stop. This means the effectiveness of cancellation
depends on the code being executed. If a child is blocked in an interruptible operation, it can often terminate promptly. If it ignores interruption or uses an underlying API that cannot be cancelled
effectively, scope cancellation may not immediately stop the work.

That is why structured cancellation should not be confused with transport-level timeout management. Suppose an HTTP request has a 500-millisecond budget, but one child uses a remote HTTP client
configured with a 30-second socket timeout. Even if the parent scope decides the child is no longer useful, the behavior of the underlying I/O still matters. Structured concurrency coordinates task
lifetime, while socket, connection, database, and client timeouts control the underlying resource interactions.

A robust system therefore combines both levels. The structured scope defines the parent operation and cancellation semantics, while each dependency has sensible I/O-level timeouts appropriate to the
overall request budget.

Code running inside structured subtasks should also avoid swallowing interruption unintentionally. A pattern such as this defeats cooperative cancellation:

===! ":fontawesome-brands-java: `Java`"

    ```java
    try {
        doBlockingWork();
    } catch (InterruptedException e) {
        // ignored
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    try {
        doBlockingWork()
    } catch (e: InterruptedException) {
        // ignored
    }
    ```

If interruption must be caught, it should generally be propagated or restored:

===! ":fontawesome-brands-java: `Java`"

    ```java
    try {
        doBlockingWork();
    } catch (InterruptedException e) {
        Thread.currentThread().interrupt();
        throw e;
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    try {
        doBlockingWork()
    } catch (e: InterruptedException) {
        Thread.currentThread().interrupt()
        throw e
    }
    ```

The structured scope can provide a clean cancellation model only when the code underneath participates in that model.

---

## Deadlines and Request Budgets { #deadlines }

Timeouts and deadlines are closely related but conceptually different. A timeout answers how long an individual operation may wait. A deadline answers how much time the parent request has left before
it is no longer useful.

The distinction becomes especially important in fan-out scenarios. If the entire request has 300 milliseconds available, it makes little sense for every child to independently use a one-second
timeout. The parent request needs authority over the lifetime of all its children.

Java 25 allows a structured task scope to be configured with a timeout:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var timeout = Duration.ofMillis(250);

    try (var scope = StructuredTaskScope.open(
            StructuredTaskScope.Joiner.awaitAllSuccessfulOrThrow(),
            config -> config.withName("user-dashboard").withTimeout(timeout))) {

        var profile = scope.fork(() -> profileClient.get(userId));
        var orders = scope.fork(() -> orderClient.getRecent(userId));
        var recommendations = scope.fork(() -> recommendationClient.get(userId));

        scope.join();

        return new Dashboard(
            profile.get(),
            orders.get(),
            recommendations.get()
        );
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val timeout = Duration.ofMillis(250)

    StructuredTaskScope.open(
        StructuredTaskScope.Joiner.awaitAllSuccessfulOrThrow(),
        { config -> config.withName("user-dashboard").withTimeout(timeout) }
    ).use { scope ->
        val profile = scope.fork { profileClient.get(userId) }
        val orders = scope.fork { orderClient.getRecent(userId) }
        val recommendations = scope.fork { recommendationClient.get(userId) }

        scope.join()

        return Dashboard(
            profile.get(),
            orders.get(),
            recommendations.get()
        )
    }
    ```

Once the scope reaches its timeout, the structured operation is no longer allowed to continue indefinitely. Remaining children can be cancelled because the parent result is already too late to be
useful.

In distributed systems, it is even better to propagate a remaining budget rather than repeatedly assigning a fresh timeout at every service boundary. If a gateway starts with a 1-second deadline and
250 milliseconds are already consumed before a service begins its own fan-out, the children should not act as if they have another full second. They effectively have around 750 milliseconds remaining.

The same principle applies inside one process. A nested operation should derive its timeout from the parent request's remaining budget rather than reset the timer. This produces a temporal hierarchy
that mirrors the task hierarchy: parent operations own the deadline, and child operations consume the remaining time.

---

## Request Scope as an Execution Tree { #request-scope }

Structured concurrency becomes particularly intuitive when the task scope is viewed as part of the HTTP request itself. Kora already executes synchronous request handling on a virtual thread. When a
service needs internal parallelism, that root virtual thread can create a structured subtree of child virtual threads and wait for them before continuing.

Conceptually:

```text
HTTP request
      |
      v
request Virtual Thread
      |
      v
Controller
      |
      v
Service
      |
      v
StructuredTaskScope
      |
      +--> profile
      |
      +--> orders
      |
      +--> recommendations
      |
      v
     join
      |
      v
assemble response
      |
      v
HTTP response
```

This is stronger than simply saying that a request uses multiple threads. The task hierarchy now mirrors the logical hierarchy of the operation. The request begins, the service opens a concurrent
region, the child operations run, they complete or fail, the scope closes, and only then does the request continue toward serialization and response writing.

That lifecycle is particularly useful for observability and debugging because the execution tree has a clear owner at every level. A child operation exists because a parent operation needs it, and the
parent cannot casually abandon that child without explicitly ending or cancelling the scope.

---

## Scoped Context and Observability { #observability }

Concurrent execution becomes much harder to use safely when child tasks lose request context. Backend requests often carry tracing information, authentication data, tenant identifiers, request
metadata, locale, or logging correlation values. Historically, executor-based concurrency required frameworks and libraries to capture and restore this context manually because an arbitrary executor
thread did not naturally inherit the contextual state of the request thread.

Kora 2's tracing model aligns well with structured concurrency because its OpenTelemetry integration uses Java `ScopedValue` for context storage. Structured task scopes inherit scoped-value bindings
into their child tasks, which means the tracing context associated with the parent request can flow naturally into structured child virtual threads.

This is important because the tracing tree can then mirror the execution tree. A request span may contain child spans for profile loading, order loading, and recommendations, producing a trace that
reflects the actual parallel structure of the request. Instead of seeing unrelated spans or having to manually capture and restore telemetry context around executor submissions, the request's context
remains structurally associated with its children.

The resulting trace also makes latency analysis much clearer. In a sequential implementation, downstream spans appear one after another and total latency approaches their sum. In a structured fan-out
implementation, the spans overlap, and the critical path becomes approximately the duration of the slowest mandatory branch. Observability therefore becomes an important tool for verifying that
fan-out actually improved latency rather than merely increasing downstream load.

---

## The Critical Path Matters More Than the Number of Tasks { #critical-path }

Parallel execution reduces avoidable serialization, but it does not remove the concept of a critical path. If profile loading takes 40 milliseconds, orders take 60 milliseconds, and recommendations
take 90 milliseconds, parallel execution can reduce the combined waiting time from roughly 190 milliseconds to around 90 milliseconds. If recommendations suddenly take 900 milliseconds, however, the
complete operation will still take approximately 900 milliseconds as long as recommendations remain mandatory.

This means structured concurrency should not be treated as a general latency optimizer. It eliminates waiting that exists only because independent work was executed sequentially. It does not make the
slowest mandatory dependency faster.

The same reasoning applies to multi-stage request graphs. Suppose one branch takes 70 milliseconds and then starts another dependent operation that takes 100 milliseconds. Even if several other
branches finish in 40 or 80 milliseconds, the critical path may still be 170 milliseconds. Optimizing a branch that is not on that path may have almost no impact on end-to-end latency.

This is why structured concurrency combines well with distributed tracing. Once the request is represented as a structured execution tree, engineers can identify which branches overlap, which ones
dominate the critical path, and where optimization work will actually affect user-visible latency.

---

## Fail-Fast, Wait-for-All, and First-Success Policies { #policies }

Not every concurrent operation has the same completion semantics. Some operations require all children to succeed, while others may need only the first successful result.

A dashboard that requires profile, permissions, and orders is naturally an all-success operation. If one mandatory component fails, the complete result cannot be constructed. A redundant provider
lookup is different. If several equivalent providers can supply the same information, the application may want whichever one succeeds first and cancel the remaining work.

Java 25 represents these policies through `Joiner`. For example, a first-success operation can conceptually be expressed as:

===! ":fontawesome-brands-java: `Java`"

    ```java
    try (var scope = StructuredTaskScope.open(
            StructuredTaskScope.Joiner.<Price>anySuccessfulResultOrThrow())) {

        scope.fork(() -> providerA.getPrice(productId));
        scope.fork(() -> providerB.getPrice(productId));
        scope.fork(() -> providerC.getPrice(productId));

        return scope.join();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    StructuredTaskScope.open(
        StructuredTaskScope.Joiner.anySuccessfulResultOrThrow<Price>()
    ).use { scope ->
        scope.fork { providerA.getPrice(productId) }
        scope.fork { providerB.getPrice(productId) }
        scope.fork { providerC.getPrice(productId) }

        return scope.join()
    }
    ```

Once one provider succeeds, the results of the other branches may no longer matter, so they can be cancelled. This is another example of why structured concurrency is more than simply starting
threads. The scope expresses a completion policy for a logical operation.

The correct join policy should therefore be chosen from business semantics. The application should decide whether all results are required, whether the first successful result is sufficient, or
whether partial failure is acceptable, and then use the concurrency model that matches that decision.

---

## Keep Parallelism at the Orchestration Layer { #orchestration-layer }

One of the most useful architectural properties of structured concurrency is that it allows concurrency to remain local. A repository does not need to return a future simply because one caller may
eventually want to run it in parallel with another repository. An HTTP client does not need an asynchronous return type merely because some orchestration layer wants to issue several independent
requests at once.

Instead of exposing:

===! ":fontawesome-brands-java: `Java`"

    ```java
    CompletionStage<Profile> getProfile(long id);

    CompletionStage<List<Order>> getOrders(long id);

    CompletionStage<List<Product>> getRecommendations(long id);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun getProfile(id: Long): CompletionStage<Profile>

    fun getOrders(id: Long): CompletionStage<List<Order>>

    fun getRecommendations(id: Long): CompletionStage<List<Product>>
    ```

the components can keep direct contracts:

===! ":fontawesome-brands-java: `Java`"

    ```java
    Profile getProfile(long id);

    List<Order> getOrders(long id);

    List<Product> getRecommendations(long id);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun getProfile(id: Long): Profile

    fun getOrders(id: Long): List<Order>

    fun getRecommendations(id: Long): List<Product>
    ```

The service that actually understands the dependency graph decides when those calls should run concurrently.

This localizes concurrency where it belongs. The orchestration layer knows which operations are independent, which failures are mandatory, which branches are optional, and what deadline applies to the
overall result. Lower-level components should generally remain unaware of whether a caller invokes them sequentially or inside a structured scope.

This approach also prevents concurrency abstractions from propagating through unrelated parts of the codebase. A single endpoint needing fan-out does not force the repository, client, service,
controller, and test layers to become asynchronous end to end.

---

## Structured Scope Is Not Application Scope { #scope-vs-app }

A `StructuredTaskScope` should normally be short-lived and tied to a specific operation. It is not a replacement for an application-wide executor or worker pool.

The intended lifecycle looks like this:

```text
request
  |
  +-- scope
      |
      +-- child
      +-- child
      +-- child
```

The scope is opened close to the point where independent work appears and closed before that operation returns. Kora's dependency injection graph manages long-lived application components such as
clients, repositories, pools, and services. Structured task scopes manage temporary relationships between concurrent tasks.

These two lifecycles should not be mixed. An application-wide structured scope would largely defeat the purpose of structured concurrency because tasks would no longer have a clear lexical owner or
completion boundary.

---

## Cheap Threads Do Not Mean Unlimited Concurrency { #cheap-threads }

Virtual threads make blocked threads inexpensive compared with platform threads, but they do not remove downstream bottlenecks. A service may be able to create thousands of virtual threads, while its
database still has a 50-connection pool and its remote dependency still accepts only a few hundred requests per second.

This distinction becomes especially important with fan-out. Suppose an endpoint forks 20 JDBC operations per request and the service receives 1,000 concurrent requests. The application may create
demand for 20,000 database operations even though the pool contains only 50 connections. The virtual threads themselves are not the limiting resource; they simply wait for access to a much scarcer
resource.

The same applies to HTTP connection pools, rate-limited APIs, Kafka partitions, CPU cores, file descriptors, storage throughput, or external services. Structured concurrency improves how tasks are
organized but does not increase the capacity of the systems they depend on.

Fan-out can also amplify traffic dramatically. A service receiving 5,000 requests per second and performing five downstream calls per request can generate roughly 25,000 downstream calls per second
before retries are considered. If every dependency then retries aggressively during an incident, traffic can multiply further. Parallel execution may reduce individual request latency while
simultaneously increasing instantaneous pressure on downstream systems.

For that reason, introducing fan-out should be treated as an architectural capacity decision rather than a purely local code optimization.

---

## Database Work Requires Additional Care { #database-work }

JDBC works naturally with virtual threads because blocking on a JDBC operation no longer implies dedicating one expensive platform thread per request. However, this does not mean every database
operation should be parallelized.

A particularly important case is a transaction using one connection. If several operations are part of the same transaction and depend on sequential database state, executing them in separate child
tasks is usually incorrect. Structured concurrency does not change transaction semantics and does not make one JDBC connection safely concurrent.

Parallel database work is more appropriate when operations are genuinely independent and can acquire independent connections, such as unrelated read-only queries. Even then, the cost to the connection
pool and database must be considered carefully.

The right question is therefore not whether `StructuredTaskScope` can run several repository calls at once. It can. The relevant question is whether the operations are semantically independent and
whether the resources underneath them can safely and efficiently support the additional concurrency.

---

## CPU-Bound Work Has a Different Cost Model { #cpu-bound }

Structured concurrency is particularly attractive for I/O-heavy backend workloads because virtual threads can cheaply block while waiting for network, database, or filesystem operations. CPU-bound
work behaves differently.

If three child tasks are all performing substantial computation, the machine still has a finite number of processor cores. Forking thousands of CPU-heavy virtual threads does not create additional
compute capacity. It simply creates more runnable work that must compete for the same CPUs.

Structured concurrency can still be useful for expressing the relationship between CPU-bound tasks, but bounded parallelism becomes much more important. The presence of virtual threads should not be
interpreted as permission to remove all concurrency limits from compute-heavy operations.

This distinction is fundamental: virtual threads primarily improve the economics of waiting, not the economics of computation.

---

## Nested Structured Concurrency { #nested }

Real request graphs are often hierarchical rather than flat. A request may load a profile, commerce information, and personalization data in parallel. The commerce branch may itself load orders and
refunds concurrently, while personalization may concurrently retrieve recommendations and experiment assignments.

That produces a tree such as:

```text
request
├── profile
├── commerce
│   ├── orders
│   └── refunds
└── personalization
    ├── recommendations
    └── experiments
```

Structured concurrency handles this naturally because a child operation can open its own nested scope. A `loadCommerce()` method can remain synchronous to its caller while internally running orders
and refunds concurrently.

===! ":fontawesome-brands-java: `Java`"

    ```java
    CommerceData loadCommerce(long id) throws InterruptedException {
        try (var scope = StructuredTaskScope.open()) {
            var orders = scope.fork(() -> orders(id));
            var refunds = scope.fork(() -> refunds(id));

            scope.join();

            return new CommerceData(
                orders.get(),
                refunds.get()
            );
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun loadCommerce(id: Long): CommerceData {
        StructuredTaskScope.open<Any>().use { scope ->
            val orders = scope.fork { orders(id) }
            val refunds = scope.fork { refunds(id) }

            scope.join()

            return CommerceData(
                orders.get(),
                refunds.get()
            )
        }
    }
    ```

The parent operation does not need to know how `loadCommerce()` achieves its result. It simply sees an ordinary synchronous method call. This preserves encapsulation while still allowing concurrency
at multiple levels of the request graph.

Nested structures also reinforce the importance of deadline propagation. If the root request begins with a 500-millisecond budget and spends 80 milliseconds before invoking a nested scope, the nested
operation should not receive a fresh 500 milliseconds. It has approximately 420 milliseconds left. Any deeper children should work from the remaining budget again.

---

## Partial Results and Graceful Degradation { #partial-results }

Some endpoints should return useful data even when optional dependencies fail. Structured concurrency does not require every branch to share the same error policy.

Imagine a page containing an account balance, recent transactions, recommendations, and a marketing banner. The balance and transaction history may be mandatory, while recommendations and the banner
are optional. If the optional calls fail, returning the rest of the page may be preferable to failing the request.

This behavior should be represented explicitly. An optional branch can convert its dependency failure into an empty value, fallback object, or a typed result describing unavailability. The important
point is that degraded behavior is intentional and visible in the domain model rather than emerging accidentally from swallowed exceptions.

For more complex cases, an application might use an explicit result type:

===! ":fontawesome-brands-java: `Java`"

    ```java
    sealed interface DependencyResult<T> {

        record Success<T>(T value)
            implements DependencyResult<T> {
        }

        record Unavailable<T>(Throwable cause)
            implements DependencyResult<T> {
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    sealed interface DependencyResult<T> {

        data class Success<T>(val value: T) : DependencyResult<T>

        data class Unavailable<T>(val cause: Throwable) : DependencyResult<T>
    }
    ```

This allows the orchestration layer to distinguish between successful data and an unavailable optional dependency without turning every local problem into a global request failure.

Structured concurrency provides the lifecycle and coordination mechanism. The business layer still defines which failures matter.

---

## Structured Concurrency and Kora Resilience { #resilience }

Kora already provides resilience mechanisms such as timeout, retry, circuit breaker, and fallback. Structured concurrency complements these mechanisms rather than replacing them.

A circuit breaker answers whether a dependency call should be attempted at all. A retry policy decides whether a failed dependency operation should be attempted again. A dependency timeout limits how
long one call may take. Structured concurrency answers a different question: how several related dependency calls should live and terminate as part of one parent operation.

A typical request can therefore have a structure such as:

```text
Structured request operation
|
+-- Profile client
|   +-- circuit breaker
|   +-- timeout
|   +-- optional retry
|
+-- Order client
|   +-- circuit breaker
|   +-- timeout
|
+-- Recommendation client
    +-- circuit breaker
    +-- fallback
```

The structured scope coordinates the orchestration layer. Each dependency retains its own resilience policy.

Retries deserve special attention because fan-out can magnify them. If one request forks five dependencies and each may retry three times, that single request can potentially create around fifteen
downstream attempts. Under load, this can become a significant amplification factor. Retry policy should therefore consider the parent deadline, remaining budget, circuit-breaker state, idempotency,
and downstream capacity.

A child operation should not keep retrying for two seconds when the request that owns it has only 100 milliseconds remaining.

---

## Cancellation Does Not Mean Rollback { #cancellation-rollback }

Structured concurrency is easiest to reason about for read operations because cancelling a read usually means abandoning unnecessary work. Side-effecting operations are more complicated.

Suppose a service forks `chargeCard`, `createOrder`, and `sendMessage`. If `createOrder` fails and the scope cancels the other children, that cancellation does not guarantee the card charge has not
already been committed. A task may be cancelled before a side effect, during it, or after the external system has already accepted it.

Structured cancellation is therefore not a distributed transaction mechanism. It does not provide rollback semantics across remote systems. Side-effecting workflows may still require idempotency keys,
database transactions, a transactional outbox, sagas, compensation logic, or a durable workflow engine.

The role of structured concurrency is to manage execution lifetime. It ensures tasks belong to a parent operation and makes cancellation possible. It does not reverse effects that have already
happened outside the JVM.

---

## Structured Concurrency and `CompletableFuture` { #completablefuture }

It is tempting to treat `StructuredTaskScope` as a nicer syntax for `CompletableFuture`, but the two abstractions have different semantics.

`CompletableFuture` represents an asynchronous result whose lifetime is not inherently bounded by the lexical scope where it was created. A method can return a future while the computation continues
elsewhere. That behavior is useful when asynchronous values are genuinely part of the API or when work intentionally outlives the current call.

A structured task scope deliberately imposes a stronger relationship. The parent owns its children and establishes a clear boundary around them. When the structured operation ends, its child tasks
should also have completed, failed, or been cancelled.

That restriction is useful because it makes task lifetime easier to reason about. For request-scoped orchestration, the stronger ownership semantics are usually exactly what the application wants.

`CompletableFuture` and other asynchronous constructs remain appropriate for workloads whose lifetime intentionally exceeds the current method, such as event-driven APIs, long-lived pipelines,
framework integration points, or work transferred to another subsystem. If background work must survive an HTTP request, it should generally be handed to a durable queue, scheduler, or worker system
rather than detached from the request as an untracked virtual thread.

---

## Structured Concurrency Is Not `parallelStream()` { #parallelstream }

Parallel streams also execute work concurrently, but they solve a different class of problem. A parallel stream primarily represents data parallelism: apply the same transformation to many elements of
a collection.

Backend fan-out is usually task parallelism. The branches frequently have different return types, different dependencies, and different error semantics. One branch may load a profile, another may
retrieve orders, and a third may query an external recommendation system.

`StructuredTaskScope` maps much more directly to that kind of heterogeneous task relationship. It represents several child operations that together form one parent operation rather than applying one
operation uniformly across a collection.

---

## Choosing What to Parallelize { #choosing }

Good candidates for structured fan-out usually share several characteristics. The operations are genuinely independent, their latency is large enough that overlapping it matters, the downstream
systems can absorb the extra concurrency, and the operations share a coherent parent lifecycle.

Parallelizing three remote calls taking tens of milliseconds each may significantly reduce response time. Parallelizing a few microsecond-scale transformations usually adds complexity without
meaningful benefit.

Operations should generally remain sequential when one depends on the result of another, when they mutate shared state, when they share a transactional or otherwise stateful resource, or when parallel
execution simply moves contention to a smaller downstream pool.

The default should still be simple sequential code. Structured concurrency is valuable precisely because it can be introduced locally where real concurrency exists rather than becoming the default
shape of the entire application.

---

## A Production-Oriented Kora Pattern { #production-pattern }

A typical Kora aggregation endpoint can therefore use a structure like this:

```text
HTTP request
|
+-- authentication
|
+-- validation
|
+-- determine remaining deadline
|
+-- StructuredTaskScope
|      |
|      +-- profile client
|      |      +-- timeout
|      |      +-- circuit breaker
|      |
|      +-- orders client
|      |      +-- timeout
|      |      +-- circuit breaker
|      |
|      +-- recommendations client
|             +-- timeout
|             +-- fallback
|
+-- join
|
+-- assemble response
|
+-- serialize
|
HTTP response
```

This architecture keeps responsibilities separated cleanly. The HTTP layer remains synchronous. The service contract remains synchronous. Individual dependencies own their resilience policies. The
orchestration layer owns parallelism. The structured scope owns the lifetime of child tasks. The request deadline constrains the whole operation. Tracing follows the execution tree.

Most importantly, no asynchronous return type has to escape the service merely because several calls happen concurrently inside it.

---

## Java 25 and Preview API Considerations { #java-25-preview }

Kora 2.0 targets modern Java, and the structured concurrency API available in Java 25 is still a preview API. That has practical consequences for build and deployment configuration because preview
features must be enabled both during compilation and when running the JVM.

For Gradle, the configuration will typically include:

```groovy
tasks.withType(JavaCompile).configureEach {
    options.compilerArgs += "--enable-preview"
}

tasks.withType(Test).configureEach {
    jvmArgs += "--enable-preview"
}

tasks.withType(JavaExec).configureEach {
    jvmArgs += "--enable-preview"
}
```

The production JVM must also start with:

```text
--enable-preview
```

This needs to be reflected consistently across local development, tests, integration tests, IDE configurations, application distributions, Docker images, and Kubernetes launch commands.

The API itself has also evolved across several JDK previews. Older articles frequently show `ShutdownOnFailure` and related earlier APIs, while Java 25 uses `StructuredTaskScope.open(...)`, `Joiner`,
and scope configuration. When writing Kora 2 code, examples should therefore be aligned with the exact JDK version used by the application rather than copied from older Project Loom material.

---

## Kotlin Applications { #kotlin }

The same architectural model applies to Kotlin applications running on Kora 2. The framework-level API does not need to become coroutine-based merely because I/O is involved. A service can expose an
ordinary synchronous function such as:

```kotlin
fun getDashboard(userId: Long): Dashboard
```

and execute on a virtual thread. When the implementation reaches a point where several independent operations should run concurrently, it can use the JVM structured-concurrency API locally.

The architectural principle remains the same: keep normal synchronous contracts at component boundaries and introduce explicit concurrency only in the orchestration layer where the dependency graph is
known.

---

## Common Mistakes { #common-mistakes }

Several mistakes are worth avoiding when structured concurrency is introduced into an existing Kora application.

The first is creating scopes around every method. Most operations do not contain useful parallelism, and wrapping them in a concurrency construct only obscures otherwise simple code.

The second is assuming virtual threads remove capacity limits. They reduce the cost of waiting threads, but database pools, CPUs, remote services, and connection limits remain finite.

Another common mistake is introducing one enormous fan-out because creating child virtual threads is cheap. A request that starts hundreds of remote calls can easily overload its dependencies even if
the JVM itself handles the threads without difficulty.

Timeout design is another source of problems. Giving every nested operation a fresh large timeout can make end-to-end latency far exceed the original request budget. Deadlines should usually narrow as
work moves deeper into the task tree.

Transaction semantics must also be respected. Structured concurrency does not make a single JDBC transaction safely parallel, and cancellation does not provide rollback for remote side effects.

Finally, background work should not simply be detached from the request. If an operation must survive the request lifecycle, it belongs in a durable background-processing model rather than in the
request's structured scope.

---

## A Practical Design Checklist { #design-checklist }

Before converting sequential code into a structured fan-out, it is useful to answer a small set of architectural questions. Are the operations genuinely independent? Is enough latency involved for
overlap to matter? Are all results mandatory, or can some dependencies degrade gracefully? What should happen when one branch fails? Can other branches be safely cancelled? Do the underlying libraries
respond properly to interruption? Are transport-level timeouts configured appropriately? What is the remaining request deadline? Can downstream systems tolerate the increased concurrency? Are any
operations sharing a transaction or another stateful resource? Are there side effects that cancellation cannot undo? Does the work belong to the current request or should it outlive it?

If those questions have clear answers, `StructuredTaskScope` is probably being introduced at the correct architectural boundary.

---

## From Thread-per-Request to Structured Task Trees { #thread-per-request }

The most interesting consequence of virtual threads is not simply that Java can return to the old thread-per-request model. The newer model is richer than that because one request can become a
structured tree of related virtual threads.

A request might begin on one virtual thread, fork profile and order operations into two child virtual threads, and then have the order branch itself fork fraud and shipping calculations. All of those
tasks still belong to one logical request.

```text
request VT
|
+-- profile VT
|
+-- order VT
|   |
|   +-- fraud-check VT
|   +-- shipping VT
|
+-- recommendation VT
```

Traditional thread-per-request systems offered a straightforward synchronous programming model but struggled when very large numbers of blocking platform threads were required. Reactive systems solved
the thread-scaling problem by representing execution through callbacks, publishers, operators, and asynchronous state machines, but this often made control flow, stack traces, context propagation, and
debugging more complicated.

Virtual threads recover inexpensive synchronous waiting. Structured concurrency then restores explicit hierarchy when one synchronous operation needs internal parallelism. The result is not merely a
return to the architecture of twenty years ago. It is a model where one logical request is represented by one root virtual thread and a structured tree of child virtual threads whose lifetime remains
bound to that request.

---

## Why Structured Concurrency Fits Kora { #why-kora }

This model matches Kora's broader design philosophy particularly well. Kora tries to keep framework abstractions thin and to stay close to standard Java and the underlying technologies it integrates
with. Dependency injection is generated at compile time, repositories expose direct typed methods, HTTP controllers and clients use ordinary signatures, and virtual threads allow blocking APIs to
remain practical at high concurrency.

Structured concurrency follows the same pattern. Kora does not need a proprietary task abstraction or a framework-specific parallel DSL. The JDK already provides the primitive needed to express
request-local concurrency.

The conceptual stack remains small:

```text
Business code
     |
StructuredTaskScope
     |
Virtual Threads
     |
JDK
```

That has benefits beyond aesthetics. Standard JDK concurrency tools are easier to debug, profile, reason about, and reuse across libraries. They also reduce the semantic gap between application code
and the runtime behavior underneath it.

---

## The Architectural Shift: Synchronous Does Not Mean Sequential { #architectural-shift }

For a long time, backend development often treated synchronous and concurrent programming as opposites. Synchronous usually implied blocking and sequential execution, while asynchronous APIs were the
primary way to express large amounts of concurrency.

Virtual threads break that relationship because blocking no longer requires dedicating a heavyweight platform thread to every waiting operation. Structured concurrency breaks it further because a
synchronous method can internally manage several concurrent child tasks while still presenting one simple completion boundary to its caller.

A method such as:

```java
Dashboard load(long userId)
```

can internally represent:

```text
load
├── profile
├── orders
└── recommendations
```

without changing its external contract. The caller does not have to understand how the work is scheduled or how many child threads exist. It only needs the semantic guarantee that when `load()`
returns, the work associated with that operation is complete.

This is one of the most important architectural consequences of structured concurrency. Synchronous API design no longer implies sequential execution. It means that the operation has a clear boundary.

---

## Conclusion { #conclusion }

Structured concurrency is a natural continuation of Kora 2's virtual-thread-first execution model. Virtual threads solve the scalability problem of blocking I/O by making waiting threads inexpensive.
Structured concurrency solves the lifecycle problem that appears when one logical operation needs several concurrent children.

In a Kora HTTP request, the model remains straightforward. The request executes on a virtual thread, the controller calls a normal synchronous service, and that service can open a
`StructuredTaskScope` when it reaches a point where independent operations should run concurrently. Those child tasks execute in parallel, share a clear parent, inherit relevant scoped context, and
are joined before the service returns.

Fan-out reduces avoidable sequential latency. Failure propagation allows related tasks to fail as one operation when appropriate. Cancellation prevents unnecessary sibling work from continuing after
failure or timeout. Deadlines constrain the whole concurrent region. Request scope gives child tasks a clear owner. Tracing can follow the same execution tree that the application actually uses.

The important lesson is therefore not simply to replace:

```text
profile()
orders()
recommendations()
```

with:

```text
fork(profile)
fork(orders)
fork(recommendations)
join()
```

The deeper idea is to model concurrent work as a structured tree in which lifetime, failure, cancellation, deadline, and context belong to the operation that created the tasks.

That is what makes `StructuredTaskScope` fundamentally different from simply submitting work to an executor, and it is why the model fits Kora 2 so naturally. The framework already provides
synchronous application code on virtual threads; structured concurrency adds a disciplined way to express parallelism without giving up that simplicity.
