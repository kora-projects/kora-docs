---
date: 2026-08-27
description: How the Kora Framework attaches resilience, caching, validation, and scheduling policy declaratively through compile-time generation.
search:
  exclude: true
---
# Policy-Driven Infrastructure in Kora: Resilience, Caching, Validation, and Scheduling { #policy-driven-infrastructure }

**August 27, 2026**

Modern backend frameworks are often evaluated by the number of features they expose: circuit breakers, retries, caches, validators, schedulers, metrics, and so on. That comparison is useful, but it
misses a more important architectural question: **where does the policy live, and how visible is it to the application?** The same retry primitive can be either a clear part of the service contract or
an invisible loop buried inside an HTTP client. The same cache can be an explicit acceleration layer or an opaque source of stale data. The same validation rule can protect an API boundary or leak
deep into business code. The same scheduler can be a convenient timer or a distributed execution system with persistence, leases, recovery, and idempotency requirements.

The Kora Framework is interesting because it tries to keep these policies declarative without turning them into runtime magic. Resilience annotations, cache annotations, validation annotations, and scheduling
annotations are not merely syntactic conveniences. They describe infrastructure policy at the point where that policy belongs, while Kora generates the implementation around application code at
compile time. The resulting model is different from a framework that discovers annotations at runtime, reflects over objects, constructs generic interceptor chains, and hides control flow behind
dynamic proxies. In Kora, the application still uses explicit types, generated code is inspectable, configuration remains visible, and the framework tends to preserve the shape of the underlying
technology instead of replacing it with a large proprietary abstraction.

This article looks at four concerns that are usually treated as independent framework features: resilience, caching, validation, and scheduling. They are related by a common design problem. Each is
fundamentally about **policy around application work**. The method that talks to a remote service needs a failure policy. The method that reads expensive data needs a reuse policy. The controller that
accepts external input needs a validity policy. The method that must run periodically needs an execution policy. The technical mechanism differs, but the architectural question is the same: how can we
attach policy without hiding the application itself?

Kora's answer is largely compile-time generation plus explicit configuration. That answer has practical consequences for performance and startup, but the more important consequences are architectural.
Policies become easier to review, composition becomes visible, generated code can be inspected, errors can move toward build time, and application code remains close to the Java and Kotlin programming
model.

---

## Resilience Is a Policy, Not a Library Call { #resilience-policy }

A resilient system is not created by calling `retry()` around a block of code. Resilience is a set of decisions about failure semantics: which failures are temporary, which are terminal, how long the
caller is willing to wait, whether repeated failures should stop reaching the dependency, what result should be produced when the primary path is unavailable, and how those decisions interact with the
latency and capacity budgets of the whole system.

That is why resilience works best when treated as policy rather than as scattered library calls. If every developer manually writes a retry loop, each call site tends to invent its own interpretation
of attempts, delays, exception filters, timeout handling, and fallback behavior. Over time the service no longer has a coherent resilience model. One dependency may retry five times with a fixed
delay, another may retry indefinitely, and a third may retry operations that are not safe to repeat. The code technically contains resilience primitives, but the system has no resilience policy.

Kora exposes the familiar building blocks: circuit breaker, retry, timeout, and fallback. They can be used imperatively through manager components, which is important when control flow is dynamic, but
they are especially useful declaratively as generated AOP around methods. The declarative form does more than reduce boilerplate. It turns resilience into metadata attached to a well-defined
operation, while configuration gives that metadata operational parameters.

A service method can therefore express that a particular operation participates in a named policy:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class CatalogService {

        @Fallback(value = "catalog", method = "fallback(arg1)")
        @CircuitBreaker("catalog")
        @Retry("catalog")
        @Timeout("catalog")
        public CatalogItem getItem(String id) {
            return client.getItem(id);
        }

        protected CatalogItem fallback(String id) {
            return CatalogItem.unavailable(id);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    open class CatalogService(private val client: CatalogClient) {

        @Fallback(value = "catalog", method = "fallback(arg1)")
        @CircuitBreaker("catalog")
        @Retry("catalog")
        @Timeout("catalog")
        open fun getItem(id: String): CatalogItem {
            return client.getItem(id)
        }

        protected fun fallback(id: String): CatalogItem {
            return CatalogItem.unavailable(id)
        }
    }
    ```

The important part is not the annotation syntax. The important part is that the method has become the unit around which the policy is defined. The application says, in effect, "this operation has a
bounded execution time, some failures are retryable, repeated failures influence a circuit state, and exhausted failure can degrade to a fallback." The concrete timing thresholds and predicates can
then live in configuration rather than being compiled into arbitrary loops.

### Why declarative resilience is architecturally useful { #declarative-resilience }

Resilience usually cuts across application code. It is not part of the business algorithm for fetching a catalog item, but it is part of the production behavior of that operation. Putting it directly
inside the method mixes concerns: the method becomes responsible for domain logic, remote invocation, exception classification, waiting, retry bookkeeping, breaker state, timeout measurement, and
metrics. Extracting the mechanics into helper libraries helps, but if every call site still composes those helpers manually, the policy remains duplicated and difficult to audit.

A declarative model gives a team a common vocabulary. A method is protected by a named `catalog` policy. That policy can be inspected in configuration, tested as a unit of operational behavior, and
changed without rewriting the service algorithm. The same name can carry consistent thresholds across environments while still allowing production to use different values from local development.

This also improves code review. A reviewer can see immediately that a method has retry or circuit-breaker semantics. That visibility matters because resilience changes correctness, not just
availability. A retry can execute a write more than once. A timeout can return failure while the remote operation continues. A fallback can replace fresh data with stale data. A circuit breaker can
intentionally reject calls that might have succeeded. Those are behavior changes and should be visible at the call boundary.

Kora's compile-time AOP model also makes the mechanism less mysterious. The framework generates the wrapper that applies the policy. There is no need to imagine an invisible runtime interceptor
registry or dynamic proxy graph. The generated subclass can be inspected, which is valuable when debugging ordering, exception propagation, or why a fallback did or did not execute.

### Ordering policies is part of the design { #ordering-policies }

Once multiple resilience mechanisms are used together, ordering becomes as important as the individual mechanisms. `Timeout(Retry(call))` is not equivalent to `Retry(Timeout(call))`. A circuit breaker
around the entire retry process observes a different failure stream from a circuit breaker around every attempt. A fallback outside a breaker behaves differently from a fallback inside it.

A common and useful composition is conceptually:

```text
Fallback
  └── Circuit Breaker
        └── Retry
              └── Timeout
                    └── application call
```

In that arrangement, timeout bounds one concrete attempt. Retry may repeat the bounded attempt. The circuit breaker sees the final outcome of the retry sequence. Fallback sees the failure after the
inner mechanisms have been exhausted or short-circuited. Kora's aspect ordering follows the declared annotation order, so the order is not merely documentation; it determines the generated call
structure.

Consider the meaning of placing timeout innermost. Suppose each attempt has a `200 ms` timeout and retry permits three attempts. The caller is not getting a `200 ms` end-to-end guarantee. In the worst
case, it may spend close to `600 ms` executing attempts plus retry delays, scheduler overhead, and surrounding work. If the retry delay is `50 ms` and there are two delays between three attempts, the
resilience layer alone can approach `700 ms` before fallback or final error handling.

If instead timeout wraps the complete retry sequence, the semantics change. The total retry process must finish within one budget. That can be useful when an external request already has a strict
deadline, but it also means later attempts may have much less time available than earlier ones. There is no universally correct order. The correct order depends on whether timeout means "maximum
duration of one dependency attempt" or "maximum duration of this whole application operation."

The same is true for the circuit breaker. If the breaker wraps the retry sequence, one incoming request generally contributes one final success or failure to breaker statistics. If the breaker is
inside retry, each failed attempt can affect breaker state. The second design can open the breaker much faster because retries amplify observations as well as load.

The key principle is that policy order should be designed, not accumulated. Adding another annotation to a method is not harmless. It changes a state machine.

### Retry amplification: the failure mechanism that looks like reliability { #retry-amplification }

Retry is the easiest resilience mechanism to understand and one of the easiest to misuse. Its local logic sounds safe: if a call fails because of a transient problem, try again. The problem appears
when many callers make that same decision simultaneously.

Imagine a service receiving 10,000 requests per second. Each request performs one call to a downstream service. Under normal conditions, that downstream also sees approximately 10,000 requests per
second. Now suppose the downstream becomes overloaded and begins failing half its requests. If every failed request is retried twice, load does not remain at 10,000 requests per second. The system
starts generating additional work precisely while the dependency has reduced capacity.

The simple upper bound is easy to miss:

```text
incoming rate × attempts
```

With three total attempts, 10,000 incoming requests per second can generate as many as 30,000 downstream attempts per second. Real behavior depends on success probability and timing, but the direction
is clear: retries can multiply load.

Amplification becomes worse in service chains. Suppose Service A retries Service B three times, B retries Service C three times, and C retries a database operation three times. A single top-level
request can potentially generate a large tree of attempts. The exact number depends on where failures occur, but independent retry policies at every layer can create exponential-looking pressure
during an incident.

This is why retry must be governed by several constraints at once. The operation should be safe to repeat, failures should be classified by a predicate rather than treating every exception as
transient, attempts should be small, delays should usually include some backoff or jitter at system boundaries, and the overall time budget should remain bounded. Most importantly, retry should
cooperate with circuit breaking and load shedding rather than operate as an unconditional persistence mechanism.

Idempotency deserves special emphasis. A `GET`-like read can often be repeated safely. A payment submission, inventory decrement, email send, or message publication may not be safe unless the
underlying protocol provides an idempotency key or exactly-once effect at the business level. Retrying a write because the client saw a timeout can duplicate side effects even when the first attempt
actually succeeded remotely.

Declarative resilience helps here because the presence of retry is obvious. It becomes possible to establish code-review rules such as: any retry on a mutating operation must document idempotency
semantics; retries must use a named predicate; and retry attempts must fit inside the operation's deadline budget.

### Circuit breaker windows are statistical policy { #circuit-breaker-windows }

A circuit breaker is often explained as a three-state machine: closed, open, half-open. That is correct but incomplete. In production, the difficult part is not understanding the states. The difficult
part is deciding what evidence is sufficient to conclude that a dependency is unhealthy.

Kora's circuit breaker configuration exposes the important parameters: a sliding window, a minimum number of calls before evaluation, a failure-rate threshold, the number of trial calls allowed in
half-open state, and the duration the breaker remains open before probing recovery. These parameters define a statistical policy.

A very small window reacts quickly but is noisy. If the window contains only a few calls, two unusual failures can open a breaker for a mostly healthy dependency. A very large window is stable but
slow to react. It may continue sending substantial traffic to a failing dependency before the failure rate crosses the threshold.

`minimumRequiredCalls` is particularly important for low-traffic operations. Without a minimum sample size, a breaker could open after the first failure. With an excessively high minimum, an endpoint
that receives only a few calls per minute may never gather enough observations to react. The correct value depends on traffic volume, expected error rate, and how costly a failed call is.

The failure predicate is equally important. Not every exception means the dependency is unhealthy. A `404` for an absent entity, a validation rejection, a business conflict, or an authorization denial
should normally not poison infrastructure health statistics. Circuit breakers work best when their failure signal represents *dependency instability*, not merely any non-successful business outcome.

That distinction is another reason policy belongs near architectural boundaries. The team should be able to answer: what does a circuit-breaker failure actually mean for this operation? If the
predicate is "every thrown exception," the breaker may become a crude error-rate limiter rather than a health mechanism.

### A timeout is a budget, not a stopwatch { #timeout-budget }

Timeouts are often configured independently: HTTP client timeout, database query timeout, service-method timeout, ingress timeout, load balancer timeout. When those numbers are chosen separately, the
resulting system has contradictory latency semantics. A service may be willing to wait longer than the caller is. A retry may begin after the upstream request has already been abandoned. A database
query may continue consuming resources even though the application has timed out the request.

A better model is a latency budget that flows from the outer request inward.

Suppose an API has a `500 ms` service-level objective for most requests. The infrastructure around the application consumes some of that time, and the service itself needs time for mapping and
business logic. If the request makes two downstream calls, neither call can safely receive a `500 ms` timeout. Their budgets must fit within the remaining deadline, including retries if retries are
allowed.

Conceptually:

```text
500 ms request budget
├── 40 ms ingress / framework / serialization allowance
├── 60 ms local processing allowance
├── 250 ms primary dependency budget
├── 100 ms secondary dependency budget
└── 50 ms safety margin
```

The numbers are illustrative, but the principle is fundamental. A timeout is not "how long this library should wait." It is one allocation from an end-to-end latency budget.

Retries consume that budget. If one attempt is allowed `200 ms` and three attempts are configured, the operation needs enough budget for those attempts plus delay. If not, later retries are
mathematically guaranteed to finish after the caller no longer cares about the result. That is not resilience; it is wasted work.

Virtual threads make blocking code inexpensive from a thread-management perspective, but they do not remove the need for timeout budgets. A virtual thread waiting on a slow downstream may be cheap
compared with a platform thread, yet the downstream connection, database connection, socket, memory, and upstream request are still real resources. Concurrency that is cheap to represent can still be
expensive to serve.

### Fallback is a business decision disguised as infrastructure { #fallback-business-decision }

Fallback is frequently grouped with circuit breaker and retry, but it is qualitatively different. Circuit breaker, retry, and timeout mainly change how an operation fails or how long it is attempted.
Fallback changes *what the application returns*.

Returning a stale catalog price, an empty recommendation list, a default feature configuration, or a "temporarily unavailable" object can be a good degraded mode. Returning an empty account balance or
fabricated authorization decision would be unacceptable. Therefore fallback should never be treated as a universal technical reaction to exceptions.

A declarative fallback is useful because it makes the degraded path explicit and testable. But the fallback method still belongs to application semantics. Teams should define which fields may be
stale, how stale they may be, whether the response is marked as degraded, and whether clients can distinguish fallback data from fresh data.

Fallback should also be observable. A system that successfully returns fallback responses while the primary dependency is broken may look healthy if dashboards only count HTTP 200 responses.
Operationally, that is dangerous. Degradation must be measurable as degradation.

### Observability is part of resilience correctness { #observability-resilience }

A resilience policy that cannot be observed cannot be tuned safely. At minimum, teams need to understand attempt counts, retry exhaustion, timeout frequency, breaker transitions, calls rejected by an
open breaker, fallback invocation, and operation latency.

The most useful metrics are not just raw counters. They should answer operational questions. Is the retry success rate high enough to justify the extra load? Are timeouts clustered around one
dependency? Is the circuit breaker oscillating between open and half-open? Are most successful responses currently coming from fallback? Did a configuration change reduce latency but sharply increase
false timeouts?

Tracing adds another dimension. When retry creates multiple dependency calls for one incoming request, those attempts should be visible as related work rather than appearing as unrelated network
traffic. A trace should make it possible to see that one service operation performed three attempts and then fell back. Without that context, downstream teams may see a traffic spike without
understanding that it was generated by upstream retry behavior.

Logging should focus on state transitions and actionable events rather than emit a warning for every expected retry. A breaker moving to open is operationally meaningful. A fallback beginning to serve
significant traffic is meaningful. A single transient failure that succeeds on retry may not deserve a high-severity log if metrics already capture it.

The broader point is that observability is not an attachment to resilience. It is how the policy is validated against reality.

---

## Caching Without Hiding the Application { #caching }

Caching is another feature that looks trivial in API form and difficult in production semantics. The API seems to be `get`, `put`, and `invalidate`. The actual design problem involves key identity,
staleness, ownership, multi-instance consistency, warm-up, invalidation ordering, failure modes, stampedes, memory limits, serialization, and telemetry.

A framework can make caching convenient by making it invisible, but invisibility is often the wrong goal. When a cached value is wrong, engineers need to know exactly which cache participated, which
key was used, whether the value came from local memory or a remote store, which write path should have invalidated it, and what happens when the cache itself is unavailable.

Kora's caching model is useful because it can remain declarative without turning the cache into an anonymous global mechanism. Cache contracts are typed components. Declarative aspects such as
`@Cacheable`, `@CachePut`, and `@CacheInvalidate` can wrap methods, while application code can still inject the cache and call it imperatively when the lifecycle requires explicit control.

A typical contract can describe both key and value types:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Cache("cache.users")
    public interface UserCache extends CaffeineCache<String, UserResponse> {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Cache("cache.users")
    interface UserCache : CaffeineCache<String, UserResponse>
    ```

That type is part of the application graph. The key type is visible. The value type is visible. Tests can inject or replace the cache. Service code can explicitly warm or invalidate it. The cache is
infrastructure, but it has not disappeared behind a generic framework dictionary.

### Generated cache aspects keep the method readable { #generated-cache-aspects }

For a classic read-through case, the service method can remain about the real source of data:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Cacheable(UserCache.class)
    public UserResponse getUser(String userId) {
        return repository.findById(userId);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Cacheable(UserCache::class)
    open fun getUser(userId: String): UserResponse {
        return repository.findById(userId)
    }
    ```

The generated aspect performs the surrounding policy: derive the key, check the cache, call the original method on a miss, and store the result according to the cache contract. Application code does
not need to repeat that plumbing.

The same idea applies to write paths:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @CachePut(UserCache.class)
    public UserResponse updateUser(String userId, UserRequest request) {
        return repository.update(userId, request);
    }

    @CacheInvalidate(UserCache.class)
    public void deleteUser(String userId) {
        repository.delete(userId);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @CachePut(UserCache::class)
    open fun updateUser(userId: String, request: UserRequest): UserResponse {
        return repository.update(userId, request)
    }

    @CacheInvalidate(UserCache::class)
    open fun deleteUser(userId: String) {
        repository.delete(userId)
    }
    ```

This is a good use of declarative AOP because the policy is tightly coupled to the method boundary. The method is still the authoritative operation, and cache behavior is attached around it. The
generated implementation can be inspected, which matters when debugging key derivation or the order between cache and other aspects.

The goal is not to remove caching from architecture diagrams. The goal is to remove repetitive cache plumbing from methods while keeping the caching model explicit.

### Cache keys are part of the data model { #cache-keys }

Many cache incidents are key-design incidents. If key identity is wrong, no eviction policy can fix the semantic bug.

The simplest case is a method with one scalar argument where that argument uniquely identifies the cached result. Real methods are often more complicated:

===! ":fontawesome-brands-java: `Java`"

    ```java
    ProductPage getProducts(
        String tenantId,
        String category,
        int page,
        int pageSize,
        Sort sort,
        Locale locale
    )
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun getProducts(
        tenantId: String,
        category: String,
        page: Int,
        pageSize: Int,
        sort: Sort,
        locale: Locale
    ): ProductPage
    ```

What is the cache key? If `tenantId` is omitted, data can leak between tenants. If `locale` is omitted, users can receive content in the wrong language. If `pageSize` is omitted, the same key can
represent different result shapes. If `Sort` has unstable string serialization, semantically equivalent requests may generate different keys and destroy hit ratio.

A key mapper therefore should be treated as schema. It maps method arguments to cache identity. That mapping should be deterministic, versionable, and testable. Composite keys are often better
represented by a dedicated record than by concatenated strings:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record ProductPageKey(
        String tenantId,
        String category,
        int page,
        int pageSize,
        Sort sort,
        String locale
    ) {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class ProductPageKey(
        val tenantId: String,
        val category: String,
        val page: Int,
        val pageSize: Int,
        val sort: Sort,
        val locale: String
    )
    ```

The explicit key object improves several properties at once. Equality semantics are clear. Tests can construct expected keys. Refactoring is safer. Distributed caches can serialize the key in a
controlled way. Telemetry can attach selected dimensions without parsing ad-hoc strings.

The same principle applies when one method argument should not participate in identity. A tracing context, request object, or authentication wrapper may be necessary for execution but irrelevant to
the cached value. Declarative key mapping lets the cache policy state exactly which information defines the result.

### Multi-level caching is not "more cache" { #multi-level-caching }

A common production topology combines a very fast local cache with a shared remote cache:

```text
request
  ↓
L1 local cache
  ↓ miss
L2 distributed cache
  ↓ miss
source of truth
```

This design can produce excellent latency and reduce load on the distributed store, but it introduces a consistency hierarchy. L1 belongs to one process. L2 is shared. The source of truth is
authoritative. These layers do not fail or invalidate in the same way.

A local Caffeine cache is extremely fast because it is in-process memory. In Kubernetes, however, every replica has its own contents. Updating the cache in Pod A does not magically update Pod B.
Restarting a pod produces an empty local cache. This is not a flaw; it is simply the semantics of local memory.

A distributed cache such as Redis provides shared state but costs a network hop, connection capacity, serialization, and its own operational complexity. Putting L1 in front of L2 changes the trade-off
again. Most hot reads may never reach Redis, but stale L1 entries can survive even after L2 has been refreshed unless invalidation reaches every replica or TTL bounds the inconsistency.

This is why multi-level caching should be designed in terms of authority and staleness. The application needs answers to questions such as:

- Is L1 allowed to be stale for 5 seconds, 30 seconds, or 5 minutes?
- Does a write invalidate only the local process or publish invalidation to all replicas?
- If L2 is unavailable, may the service continue serving L1 values?
- If a value is missing in L1 but present in L2, should L1 be repopulated?
- If both caches miss simultaneously on many replicas, who is allowed to load from the source?

The abstraction should help implement those decisions, not make them disappear.

### Invalidation is where cache architecture becomes visible { #invalidation }

The familiar statement that "cache invalidation is hard" is correct because invalidation crosses ownership boundaries. The code performing the write may not be the code performing the reads. The same
entity may be cached under several keys. A write may affect aggregate queries, lists, counts, or search results in addition to the direct entity key.

Suppose a service caches both:

```text
user:{id}
users:page:{page}:{size}:{sort}
```

Updating one user can invalidate the direct user key easily, but which list pages contain that user? If sorting changed, the user may move from one page to another. If filters exist, the update may
change membership in many result sets. Declarative invalidation is still useful for simple relationships, but it cannot remove the data-model problem.

There are several legitimate strategies:

1. **Precise invalidation.** Track every affected key and evict it. This provides good freshness but can become complex for derived data.
2. **Namespace or broad invalidation.** Evict a larger group of keys after a write. This is simpler but causes more misses.
3. **TTL-based convergence.** Accept bounded staleness and allow entries to expire. This is often practical for read-heavy derived data.
4. **Versioned keys.** Include a version or generation in the key so old entries become unreachable after a write.
5. **Event-driven invalidation.** Publish change events so other replicas or services can evict their local entries.

The important architectural rule is that invalidation should be specified alongside cache creation. A cache whose invalidation policy is "we will decide later" is usually a future consistency
incident.

### Cache stampede is a concurrency problem { #cache-stampede }

A cache can reduce load during normal operation and increase load catastrophically during synchronized expiration. This is the cache stampede problem.

Imagine an expensive value receives 20,000 reads per second and has a 60-second TTL. While the entry exists, the source sees almost no load. At expiration, thousands of requests can observe the miss
at nearly the same time and all begin recomputing or fetching the value. The cache has converted a stable read stream into a burst against the source.

The risk is worse across replicas because each process may experience the same expiration boundary. Multi-level caches can shift the burst from the database to Redis or from Redis to the database, but
the concurrency problem remains.

Several techniques can mitigate stampedes:

- **Single-flight loading:** one caller loads a missing key while concurrent callers wait for the same result.
- **Refresh-ahead:** refresh hot entries before they expire rather than waiting for a miss.
- **TTL jitter:** randomize expiration so large key populations do not expire simultaneously.
- **Stale-while-revalidate:** serve a slightly stale value while one worker refreshes it.
- **Distributed locking:** coordinate loaders across replicas when the source operation is very expensive.
- **Capacity limits:** bound how many cache misses may concurrently hit a constrained dependency.

These mechanisms belong in cache policy or loadable-cache design rather than being rediscovered independently by every service method.

Virtual threads again change the cost of waiting but not the capacity of the source. Allowing 10,000 virtual threads to load the same missing database record is not a meaningful cache strategy. The
database connection pool may still contain 50 connections. A correct cache design controls duplicate work, not merely thread allocation.

### Telemetry should explain cache effectiveness, not just activity { #cache-telemetry }

A cache is useful only if it improves the system. Counting `get()` calls is not enough. Teams need to know hit ratio, miss rate, load latency, eviction frequency, cache size, remote-cache latency,
serialization errors, stale-serving rate when applicable, and the source load generated by misses.

The most informative metric is usually not a single global hit ratio. A 95% hit ratio can still hide one extremely expensive key family with poor performance. Metrics should be segmented by cache name
and sometimes operation. High-cardinality business keys themselves should generally not become metric labels, but tracing or structured logging can sample them when diagnosis requires more detail.

For multi-level caching, L1 and L2 should be distinguished. A 99% combined hit rate may sound excellent while 80% of traffic is missing L1 and going across the network to L2. The system is
functionally cached but may still pay substantial latency and infrastructure cost.

Evictions also need interpretation. High eviction counts can mean healthy turnover in a bounded cache, or they can mean the cache is undersized and constantly throwing away hot entries. Memory usage,
maximum size, hit ratio, and eviction reason must be read together.

Finally, telemetry should include cache failures. A distributed cache is a dependency. If it becomes slow, the service needs a defined policy: fail the request, bypass the cache, fall back to local
data, or degrade in another controlled way. That decision connects caching back to resilience. A cache is not outside the dependency graph just because it is called a cache.

## Declarative Validation at Compile Time { #declarative-validation }

Validation is frequently treated as input hygiene: add annotations to a DTO, let the framework reject bad values, and move on. In architecture terms, validation is more important. It defines the
transition from untrusted external representation to data that the application is willing to reason about.

A clean request path looks like this:

```text
HTTP request
    ↓
DTO / transport representation
    ↓
structural validation
    ↓
business operation
    ↓
domain invariants and persistence
```

The boundary matters because every layer below it becomes simpler when basic assumptions have already been established. If `email` cannot be blank, `pageSize` must be between 1 and 100, and a request
body must satisfy a defined shape, those facts should be established before business logic starts executing.

Kora's validation model uses declarative constraints together with generated validators and generated AOP for method validation. `@Valid` marks nested objects that should be traversed, while
`@Validate` enables method-level argument and return-value validation around the method call. This keeps validation visible in source while moving repetitive checking code into compile-time
generation.

### Validation is a boundary concern, but not all validation belongs at the boundary { #validation-boundary }

The phrase "validate at the boundary" is useful only if we distinguish categories of validation.

**Structural validation** asks whether the input is well formed enough for the operation. Examples include required fields, string length, number ranges, allowed formats, collection sizes, and nested
object constraints. These checks are ideal at the HTTP boundary.

**Business validation** asks whether the requested action is valid given current domain state. Examples include whether an email is already registered, whether an account has enough balance, whether
an order may still be cancelled, or whether a state transition is allowed. These checks belong in business logic because they require domain knowledge and often persistence.

**Authorization** asks whether the caller may perform the operation. It is related to validation but should not be collapsed into the same mechanism. An input can be structurally valid and still
unauthorized.

**Persistence constraints** are the final integrity layer. Unique keys, foreign keys, check constraints, and transactional invariants protect the source of truth even when application logic races or
another writer bypasses the API.

A robust service uses these layers together. DTO validation should not attempt to replace database constraints, and database constraints should not be used as the primary user-facing validation
experience.

### Generated validators shift errors left { #generated-validators }

A reflection-driven validation framework can discover constraints at runtime and invoke validators dynamically. Kora instead generates validation code. That difference is consistent with the rest of
the framework: do work during compilation when the relevant types and annotations are already known.

The immediate benefit is not merely runtime speed. Generated validation improves failure locality. Unsupported shapes, missing validation components, or invalid wiring can fail during the build rather
than becoming a production-only code path.

For a DTO, the generated validator can perform direct checks against fields and nested values. For a method marked with `@Validate`, Kora generates the AOP wrapper that validates arguments before
invoking the actual method and can validate the return value afterward when required. The controller source remains concise, but the generated code makes the boundary concrete.

A controller might look like:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpRoute(method = HttpMethod.POST, path = "/users")
    @Json
    @Validate
    public HttpResponseEntity<UserResponse> createUser(
        @Valid @Json UserRequest request
    ) {
        return HttpResponseEntity.of(
            201,
            HttpHeaders.of(),
            userService.createUser(request)
        );
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpRoute(method = HttpMethod.POST, path = "/users")
    @Json
    @Validate
    open fun createUser(
        @Valid @Json request: UserRequest
    ): HttpResponseEntity<UserResponse> {
        return HttpResponseEntity.of(
            201,
            HttpHeaders.of(),
            userService.createUser(request)
        )
    }
    ```

The conceptual flow is then:

```text
HTTP decoding
   ↓
UserRequest created
   ↓
generated validation wrapper
   ↓
field constraints checked
   ↓
UserController.createUser(...)
   ↓
UserService
```

This detail matters. Validation is not hidden inside JSON parsing. Parsing answers whether bytes can become a Java or Kotlin object. Validation answers whether that object is acceptable input to the
application.

### Parse errors and validation errors are different contracts { #parse-vs-validation-errors }

Suppose an API expects:

```json
{
    "name": "Alice",
    "age": 30
}
```

These failures are different:

```json
{
    "name": "Alice",
    "age": "old"
}
```

and:

```json
{
    "name": "",
    "age": -5
}
```

The first is a representation or decoding problem: `age` cannot be converted to the expected numeric type. The second can be decoded perfectly, but the resulting values violate constraints.

Clients benefit when the API distinguishes them consistently. A malformed JSON document, a type mismatch, a constraint violation, and a domain conflict should not all collapse into one generic `400`
message with an implementation stack trace.

A stable validation error contract can include a machine-readable code, a field or path, and a human-readable explanation:

```json
{
    "code": "VALIDATION_FAILED",
    "violations": [
        {
            "path": "name",
            "message": "must not be blank"
        },
        {
            "path": "age",
            "message": "must be greater than or equal to 0"
        }
    ]
}
```

The exact format is an API design choice. What matters is that it is intentional and stable. Kora can map validation violations through HTTP response mapping/interception so the public contract does
not depend on an accidental exception string.

### Validation should strengthen internal assumptions { #validation-assumptions }

A useful way to evaluate boundary validation is to ask what code becomes unnecessary below it.

Without a strong boundary, service code often contains defensive repetition:

===! ":fontawesome-brands-java: `Java`"

    ```java
    if (request == null) { ... }
    if (request.name() == null) { ... }
    if (request.name().isBlank()) { ... }
    if (request.age() < 0) { ... }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    if (request == null) { ... }
    if (request.name == null) { ... }
    if (request.name.isBlank()) { ... }
    if (request.age < 0) { ... }
    ```

The repository may repeat some of the same checks because it cannot trust the service. Utility methods may repeat them again. Eventually the application contains dozens of partial validators with
slightly different behavior.

When the boundary establishes structural validity, deeper layers can work with stronger assumptions. That does not mean blindly trusting every object from every source. It means each ingress path
should have an explicit transition into validated application data.

This is especially relevant when services accept inputs from multiple transports. HTTP may not be the only boundary. Kafka messages, scheduled job payloads, CLI inputs, or gRPC requests can each
require validation. Generated validators are reusable beyond HTTP; the HTTP integration is one place where they are invoked.

### Nested validation and object graphs { #nested-validation }

Real DTOs contain nested structures:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record CreateOrderRequest(
        String customerId,
        Address shippingAddress,
        List<OrderLine> lines
    ) {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class CreateOrderRequest(
        val customerId: String,
        val shippingAddress: Address,
        val lines: List<OrderLine>
    )
    ```

Validating only the top-level object is insufficient. The request may be non-null while `shippingAddress.postcode` is invalid or one `OrderLine.quantity` is zero. `@Valid` exists to express traversal
into nested objects using the corresponding generated validators.

This creates an explicit validation graph that parallels the data graph. Each type owns constraints about its own structure, and containing types can request recursive validation rather than manually
duplicating child rules.

The error path becomes important for nested failures. A violation like:

```text
lines[3].quantity
```

is much more useful than "order invalid." Good validation is not only about rejection; it is about returning enough structure for clients and operators to understand the rejection.

### Validation errors are data, not log emergencies { #validation-errors-data }

A malformed user request is normally not a server incident. If validation failures are logged at error level with stack traces, normal client behavior can flood logs and obscure real failures.
Validation telemetry should distinguish expected rejection from framework or application malfunction.

Useful metrics include validation-failure counts by endpoint and perhaps constraint category, but care is required to avoid high-cardinality labels. The invalid user-supplied value should generally
not become a metric label and may not belong in logs at all if it can contain sensitive data.

Tracing can record that a request failed validation and ended before business logic, while the HTTP response returns a controlled client error. This is a good example of observability following
architectural boundaries: the trace should make it obvious that the database or downstream service was never called.

A sudden increase in validation failures can still be operationally important. It might indicate a broken client release, contract drift, an OpenAPI mismatch, or abuse traffic. The difference is that
the application should observe the aggregate pattern without treating every individual invalid request as an exception requiring investigation.

### Compile-time validation fits Kora's transparency goal { #compile-time-validation }

The main value of Kora's generated validation is not that developers can write fewer `if` statements. It is that the framework can enforce a declarative boundary while preserving an inspectable
execution model. The application declares constraints, Kora generates validators, `@Validate` generates the wrapper, and a mapper/interceptor turns violations into the HTTP contract.

That model is easy to reason about:

```text
constraints in source
        ↓
compile-time generation
        ↓
explicit validator components
        ↓
generated method wrapper
        ↓
stable error mapping
```

There is little incentive to hide validation deeper than necessary. The boundary remains visible in code and in generated output.

---

## Scheduling in Production: From `@Schedule` to Distributed Jobs { #scheduling }

Scheduling is perhaps the clearest example of a feature whose surface syntax can hide radically different guarantees. A method that runs every minute is easy to implement. A job that must run once
across ten replicas, survive restarts, recover after node failure, avoid duplicate side effects, handle missed executions, support retries, and expose operational state is a distributed-systems
problem.

Those are not the same feature.

Kora's scheduling support makes local scheduled execution straightforward. The JDK-based scheduler maps naturally to `ScheduledExecutorService`, with fixed-rate, fixed-delay, and one-shot execution.
Quartz adds cron expressions, custom triggers, concurrency controls, and richer scheduling behavior. Kora generates task components at compile time and connects them to the selected scheduler, keeping
the declarative API consistent with the framework's broader generation model.

That is an excellent fit for many jobs. It is also important to know when the problem has outgrown an in-process scheduler.

### Local scheduling means one scheduler per process { #local-scheduling }

Consider:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class CleanupJob {

        @ScheduleWithFixedDelay(
            initialDelay = 10,
            delay = 60,
            unit = ChronoUnit.SECONDS
        )
        void cleanup() {
            // remove expired local state
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class CleanupJob {

        @ScheduleWithFixedDelay(
            initialDelay = 10,
            delay = 60,
            unit = ChronoUnit.SECONDS
        )
        fun cleanup() {
            // remove expired local state
        }
    }
    ```

In one application instance, the semantics are intuitive. The process starts, the scheduler registers the task, and the method executes according to the configured delay.

Now deploy five replicas. Unless the scheduling mechanism provides cluster coordination, there are five schedulers. Each replica runs the same job. If the work is "refresh this pod's local cache,"that
is exactly what you want. If the work is "charge all subscriptions due today," it may be catastrophic.

This is the first scheduling design question:

> Is the job **per-instance** or **cluster-wide**?

Per-instance jobs include local cache cleanup, local metrics aggregation, heartbeat emission, process-specific refresh, or periodic checks whose duplication is harmless and intentional. Cluster-wide
jobs include business processes where one logical execution should be owned by one worker at a time.

The annotation does not answer that question. Architecture must answer it.

### Fixed rate and fixed delay express different load models { #fixed-rate-fixed-delay }

Even before distribution, the choice between fixed rate and fixed delay matters.

Fixed rate targets a schedule independent of task duration. If execution takes longer than expected, invocations may overlap depending on scheduler semantics and available threads. That can be
appropriate for measurements or polling where wall-clock cadence matters, but it can also produce pileups when the task slows down.

Fixed delay waits for completion and then waits an additional delay before starting the next execution. The throughput adapts to task duration and avoids overlapping executions of the same scheduled
sequence.

This distinction is capacity policy. If a job takes 20 seconds normally but occasionally takes 90 seconds, scheduling it every 30 seconds at fixed rate can create concurrent work precisely when the
system is already slow. Fixed delay naturally applies backpressure to that one job because the next execution cannot begin until the current one completes.

Quartz adds additional controls such as non-concurrent execution and cron semantics, but the same architectural question remains: what should happen when execution duration exceeds the schedule
interval?

### Misfires are decisions about lost time { #misfires }

Production processes stop. Pods restart. Nodes disappear. Deployments roll. A scheduler may be unavailable at the exact time a cron expression says a job should run. When the process comes back, what
should happen to executions that were missed?

That is the misfire problem.

For some jobs, the correct answer is "skip it." If a metrics snapshot was supposed to run every minute and the service was down for ten minutes, executing ten historical snapshots after restart may be
useless.

For other jobs, the correct answer is "catch up once." A daily reconciliation that did not run at midnight still needs to run after the service recovers, but probably only once rather than once for
every missed polling interval.

For event-generating jobs, every missed logical execution might matter. A scheduler may need to persist each due occurrence separately.

Misfire behavior is therefore business semantics, not merely scheduler configuration. Cron syntax tells you when work is intended to become due. Misfire policy tells you what missed time means.

In-memory scheduling cannot provide strong recovery after complete process loss because the process itself was holding the schedule state. A persistent scheduler stores enough information outside the
process to determine that work was due and still needs execution.

### Persistent DB scheduling changes the ownership model { #persistent-db-scheduling }

A database-backed scheduler stores task instances and execution metadata in shared persistence. Multiple service replicas can then compete for work while the database coordinates which worker owns a
particular execution.

The conceptual architecture is:

```text
                    ┌──────────────────┐
                    │   shared DB       │
                    │ scheduled tasks   │
                    │ execution state   │
                    └────────┬─────────┘
                             │
                 claim / lock / renew
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
     service A          service B          service C
     worker              worker              worker
```

Kora 2's database-scheduling work follows this model by integrating a persistent `db-scheduler`-style engine, adding generated scheduling support and bounded virtual-thread execution for jobs. The
important architectural shift is not the annotation name. It is that the database becomes the coordination point for job state.

A task can survive the death of the process that created it because the task is not merely an in-memory timer. Another replica can later observe the persistent task and execute it according to the
scheduler's locking and recovery rules.

This model is suitable for jobs such as delayed email delivery, retryable business workflows, reconciliation, scheduled account operations, or any task where restart survival and multi-replica
coordination matter.

Where the database-backed scheduling module is not part of the Kora version being deployed, the same distinction still applies architecturally: local JDK/Quartz scheduling and persistent distributed
job execution solve different problems and should not be treated as interchangeable.

### Leases and locks answer "who owns the job now?" { #leases-locks }

In a distributed scheduler, selecting a job is not enough. Two workers can discover the same due row concurrently. The scheduler needs an atomic claim mechanism, usually based on database locking,
compare-and-set state transition, or a lease with expiration.

A lease means that a worker owns the job for a bounded period. If the worker completes, it updates or removes the execution. If the worker crashes and stops renewing ownership, the lease eventually
expires and another worker can recover the job.

This is fundamentally different from holding an in-memory mutex. The failure model includes process death and network partitions. Ownership must be represented in shared state.

Lease duration is a trade-off. A long lease reduces renewal overhead but slows recovery after failure. A short lease recovers quickly but requires reliable renewal and can cause duplicate execution if
a healthy worker is delayed long enough for the lease to expire.

Long-running jobs complicate the issue further. If the scheduler assumes a fixed lock duration while a job can run for hours, the worker may need heartbeat-based extension. Operational metrics should
reveal jobs approaching lease expiry, repeated recoveries, and ownership contention.

### Retries belong to jobs too, but their semantics are different { #job-retries }

A scheduled job can fail for the same reasons as an HTTP request: network errors, database contention, temporary remote failures. Retry is therefore natural, but distributed job retries differ from
in-request retries.

An HTTP retry is usually constrained by the caller's latency budget and measured in milliseconds or seconds. A durable job retry can be rescheduled minutes later because no client is holding the
connection open. Persistence allows retry policy to become temporal rather than merely immediate.

For example:

```text
attempt 1 → fail
retry in 10 seconds
attempt 2 → fail
retry in 1 minute
attempt 3 → fail
retry in 10 minutes
attempt 4 → dead-letter / manual review
```

This is often safer than spinning in an in-process retry loop. The worker releases resources between attempts, the task survives restarts, and operators can inspect pending or failed jobs.

However, retry still requires idempotency. A worker may crash after performing the external side effect but before marking the task complete in the database. The scheduler sees an unfinished task and
executes it again. From the scheduler's perspective, that is correct recovery. From the business perspective, it is a duplicate attempt.

This leads to the central rule of distributed scheduling:

> At-least-once execution is easy to achieve. Exactly-once business effect requires application design.

### Idempotency is the real exactly-once mechanism { #idempotency }

Suppose a job sends a payment request and then records completion:

```text
1. call payment provider
2. payment succeeds
3. process crashes
4. completion state is not persisted
5. lease expires
6. another worker executes job again
```

No scheduler can infer whether step 2 happened if the remote side effect and local completion record are not part of one atomic transaction. Distributed transactions across arbitrary external systems
are usually undesirable or unavailable.

The practical solution is idempotency. The job has a stable business operation identifier. Repeating the operation with the same identifier either returns the existing result or is rejected as a
duplicate without repeating the side effect.

Examples include:

```text
payment-idempotency-key = orderId
email-deduplication-key  = campaignId + userId
generation-key           = reportType + businessDate
ledger-entry-id          = deterministic operation id
```

Database writes can often enforce idempotency with a unique constraint. External APIs may provide idempotency-key support. For systems without such support, the application may need a local outbox,
deduplication table, or state machine.

This is why a scheduled method should not be judged only by whether it "runs once" in testing. Production correctness depends on what happens when the process dies at every point between claiming,
executing, and acknowledging the job.

### Multiple replicas require bounded execution, even with virtual threads { #bounded-execution }

Database-backed schedulers often become highly efficient at finding work. That creates another problem: a replica can fetch more jobs than its downstream dependencies can execute safely.

Virtual threads are an excellent execution model for blocking scheduled jobs because each job can use straightforward synchronous JDBC, HTTP, or file APIs. But an unbounded virtual-thread-per-task
executor is not automatically a correct scheduler worker. The database connection pool, remote API quotas, CPU, heap, and storage throughput remain bounded.

Kora's scheduling-db work includes bounded virtual-thread execution and configurable parallelism/prefetch behavior. That design reflects an important production principle: cheap task representation
must still be coupled to resource limits.

Suppose a pod can maintain 100,000 virtual threads but has a JDBC pool of 30 connections. Fetching 10,000 database-heavy jobs into running virtual threads does not increase throughput. It creates
9,970 waiting tasks, consumes memory, extends queueing latency, and makes shutdown/rebalance harder.

A better model is:

```text
persistent ready jobs
       ↓
bounded prefetch
       ↓
bounded execution concurrency
       ↓
resource pools
```

The scheduler should not move more work into a process than the process can realistically make progress on.

### Scheduling telemetry should describe the job lifecycle { #scheduling-telemetry }

Basic scheduler metrics often report execution duration and count. Distributed jobs need a richer lifecycle model:

```text
scheduled
  ↓
due
  ↓
claimed
  ↓
started
  ↓
succeeded / failed
  ↓
rescheduled / completed / dead-lettered
```

Useful measurements include:

- schedule-to-start delay;
- due queue depth;
- claim conflicts;
- active leases;
- execution duration;
- success and failure counts;
- retry count and retry age;
- oldest pending job;
- recovery after expired lease;
- jobs abandoned or terminally failed;
- worker concurrency and saturation.

Tracing is valuable when a job performs downstream operations. The job execution should become a trace root or a well-defined span carrying the job type and execution identifier. That makes a
scheduled workflow as diagnosable as an HTTP request.

Logging should include stable job identifiers but avoid dumping arbitrary payloads, especially when payloads can contain personal or secret data. A persistent scheduler often stores serialized job
payloads, so schema evolution and payload compatibility also become operational concerns.

### Choosing the right scheduling level { #choosing-scheduling-level }

A useful decision table is:

| Requirement                              | Local JDK scheduler              | Quartz in-process                               | Persistent DB scheduler            |
|------------------------------------------|----------------------------------|-------------------------------------------------|------------------------------------|
| Per-pod periodic maintenance             | Excellent                        | Good                                            | Usually unnecessary                |
| Simple fixed delay/rate                  | Excellent                        | Good                                            | Good but heavier                   |
| Cron expressions                         | Limited depending on API/version | Excellent                                       | Excellent when supported           |
| Survive process restart                  | No durable guarantee             | Only with persistent job store/configuration    | Yes by design                      |
| Exactly one active owner across replicas | No                               | Requires cluster-aware persistent configuration | Yes through shared DB coordination |
| Delayed one-off business task            | Weak                             | Possible                                        | Strong fit                         |
| Durable retries                          | Weak                             | Possible with configuration                     | Strong fit                         |
| Recovery after worker crash              | Process-specific                 | Depends on job store                            | Core capability                    |
| Typed persistent payload                 | Not applicable                   | Custom                                          | Natural fit                        |

The goal is not to use the most sophisticated scheduler everywhere. It is to use the simplest mechanism whose failure semantics match the job.

A cache cleanup task does not need a distributed lease. A financial reconciliation job should not rely on a per-pod timer. Architecture becomes clearer when those categories are named explicitly.

---

## One Pattern Across Four Features { #one-pattern }

Resilience, caching, validation, and scheduling look like different framework modules, but they demonstrate the same Kora design idea: application code should stay close to the operation being
performed, while infrastructure policy is attached declaratively and implemented through generated code or explicit components.

For resilience, the application method remains the operation while generated aspects apply timeout, retry, circuit breaking, and fallback according to named configuration. For caching, the method
remains the authoritative load or mutation path while generated aspects apply read-through, update, or invalidation using typed cache contracts. For validation, the controller method remains the
request boundary while generated validators and AOP enforce structural rules before business logic executes. For scheduling, the method remains the job body while generated task components connect it
to an execution mechanism.

The shared architecture can be summarized as:

```text
application method
       +
declarative policy
       +
compile-time generation
       +
explicit configuration
       ↓
production behavior
```

That is a substantially different model from building application behavior out of ad-hoc utility calls. Utility calls are easy to add but difficult to govern. Declarative policy can be reviewed,
named, configured, instrumented, and generated consistently.

The model also has limits, and those limits are healthy. An annotation cannot decide whether a payment is idempotent. A cache aspect cannot invent a correct invalidation model. A validation annotation
cannot determine whether a state transition is legal in the domain. A scheduler annotation cannot provide exactly-once business effects. Framework infrastructure can enforce mechanics, but semantics
still belong to the application.

This is where "thin abstractions" become more than a performance preference. A thin abstraction exposes enough of the underlying problem that engineers are forced to confront the real semantics. A
circuit breaker still has a window and threshold. A cache still has keys, locality, and invalidation. Validation still has a boundary and error contract. Scheduling still has ownership, persistence,
leases, and duplicate execution.

Frameworks become dangerous when convenience erases those distinctions. Kora's stronger approach is to make common policy concise without pretending the policy is simple.

## Composition Is Where Production Bugs Hide { #composition }

Another shared lesson is that infrastructure policies compose, and composition changes semantics.

A cached resilient call raises questions such as whether failures are cached, whether fallback results are cached, whether a cache hit should bypass the circuit breaker, and whether a distributed
cache outage participates in the same breaker as the original dependency.

A validated cached method raises a different question: validation must generally run before cache lookup if invalid arguments should be rejected consistently rather than transformed into keys.

A scheduled resilient job must decide whether in-process retries happen inside one scheduler attempt or failure is returned to the persistent scheduler for durable retry later. Doing both blindly can
multiply attempts.

A scheduled cached refresh must decide how multiple replicas coordinate cache regeneration and whether stale data can be served while the refresh job is recovering.

These are not unusual edge cases. They are normal outcomes of combining cross-cutting concerns. Compile-time AOP makes the ordering visible, but engineers must still reason about it.

A useful practice is to draw the wrapper structure explicitly during design review:

```text
Validation
  └── Cache
        └── Circuit Breaker
              └── Retry
                    └── Timeout
                          └── Repository / Client
```

Then ask what each layer observes as success or failure. Does cache see fallback as a successful value? Does breaker see individual attempts or only retry exhaustion? Does validation run before an
expensive cache key mapper? The diagram is simple, but it prevents a surprising number of production mistakes.

## Configuration Is Executable Architecture { #configuration }

Kora makes many policy parameters configurable, and that should be treated with the same seriousness as source code. A change from two retry attempts to five can triple downstream pressure. A breaker
threshold change can alter outage behavior. A cache TTL change can shift source load. A scheduler concurrency increase can saturate the database.

Configuration therefore deserves review, version control, rollout discipline, and observability. The safest policy parameters are those tied to measurable system budgets rather than arbitrary
intuition.

For example:

- timeout values should derive from end-to-end deadlines and observed latency percentiles;
- retry attempts should derive from transient-failure behavior and capacity headroom;
- circuit-breaker windows should derive from traffic rate and acceptable reaction time;
- cache TTL should derive from allowed staleness and source cost;
- scheduler parallelism should derive from downstream capacity, not available virtual-thread count.

This turns configuration from "ops tuning" into architecture that can be reasoned about quantitatively.

## Operational Simplicity Comes From Explicit Semantics { #operational-simplicity }

The purpose of these policies is not to maximize the number of infrastructure features used by a service. It is to reduce the number of uncontrolled failure modes.

A retry policy is successful when it absorbs genuinely transient faults without amplifying incidents. A circuit breaker is successful when it protects a failing dependency without blocking healthy
traffic unnecessarily. A timeout is successful when it enforces an end-to-end budget rather than producing random premature failures. A fallback is successful when degradation is safe and visible.

A cache is successful when it reduces cost or latency without making correctness unknowable. Validation is successful when invalid external data is rejected consistently before it contaminates deeper
layers. A scheduler is successful when its execution guarantees match the business operation under restart, replication, and partial failure.

None of those outcomes can be achieved by calling a library method alone.

They require policy.

And policy works best when it is close enough to the code to be reviewed, far enough from the algorithm to avoid repetition, generated where the compiler can verify structure, configurable where
operations need control, and observable where production can prove whether the assumptions were correct.

That combination is where Kora's approach is strongest. It does not eliminate the difficult parts of resilience, caching, validation, or scheduling. It gives those difficult parts a more explicit
place in the architecture.
