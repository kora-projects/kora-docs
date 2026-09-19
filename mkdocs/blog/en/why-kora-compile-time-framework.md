---
title: Why the Kora Framework — a Compile-Time Framework for the Modern JVM
date: 2026-09-16
description: Why the Kora Framework moves dependency injection, HTTP adapters, repositories, and AOP into compilation, and what compile-time certainty means for startup, overhead, and debugging.
search:
  exclude: true
---

# Why Kora: Compile-Time Framework for the Modern JVM { #why-kora }

**September 16, 2026**

Modern JVM frameworks are remarkably productive. With a few annotations, you can create an HTTP endpoint, inject dependencies, start a transaction, call a database, add retries, expose metrics, validate input, and secure a method.

Historically, however, that convenience has often come with a trade-off: a meaningful part of the application is assembled and interpreted only after the process starts. Classpaths are scanned, metadata is discovered, dependency graphs are constructed, annotations are interpreted, proxies are created, and reflective or dynamic machinery connects abstractions that looked simple in source code.

This approach works well and has powered a huge part of the JVM ecosystem. The Kora Framework starts from a different question:

> If the compiler already has the classes, annotations, method signatures, generic types, and dependency declarations in front of it, why postpone so much work until runtime?

Kora's answer is to move framework work into compilation. The application graph is built and validated during compilation. Framework adapters are generated as source code. Controllers become concrete request handlers, repository interfaces receive concrete implementations, and AOP annotations are transformed into generated classes containing the required behavior.

By the time the application starts, considerably less remains to be discovered. This is the central architectural idea behind Kora: **do as much framework work as possible before the application starts**.

Kora describes this as compile-time certainty: application structure is checked during compilation and the resulting framework machinery is represented as generated source rather than hidden runtime state.

---

## The Runtime Framework Model { #runtime-framework-model }

A traditional runtime-oriented framework usually starts with intentionally incomplete application code.

Consider something conceptually similar to:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Service
    public class PaymentService {

        private final PaymentRepository repository;

        public PaymentService(PaymentRepository repository) {
            this.repository = repository;
        }

        @Transactional
        @Retryable
        public Payment create(PaymentRequest request) {
            return repository.save(request);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Service
    class PaymentService(private val repository: PaymentRepository) {

        @Transactional
        @Retryable
        fun create(request: PaymentRequest): Payment {
            return repository.save(request)
        }
    }
    ```

The source already tells us quite a lot, but it may not fully describe what eventually executes. The framework still needs to determine how `PaymentService` is discovered, which implementation of `PaymentRepository` should be injected, how the dependency graph is constructed, whether `@Transactional` requires a proxy, whether `@Retryable` wraps that proxy or vice versa, and how all of those objects participate in lifecycle management.

In a runtime-centric architecture, many of these questions are resolved while the application is starting:

```text
source code
    ↓
compile
    ↓
classes
    ↓
start application
    ↓
scan / inspect metadata
    ↓
discover components
    ↓
resolve dependencies
    ↓
create proxies
    ↓
build runtime container
    ↓
start serving traffic
```

There is nothing inherently wrong with this model. It gives frameworks a great deal of flexibility and enabled years of highly productive JVM development. The architectural consequence, however, is that part of the application exists as runtime framework state rather than as ordinary program structure.

Kora makes a different trade-off.

---

## Move the Work Left { #move-the-work-left }

Kora shifts framework work toward the compiler:

```text
source code
    ↓
annotation processing / KSP
    ↓
validate contracts
    ↓
resolve dependencies
    ↓
generate implementations
    ↓
generate application graph
    ↓
compile generated source
    ↓
start application
```

The runtime model consequently becomes much simpler:

```text
generated application graph
    ↓
instantiate components
    ↓
initialize lifecycle
    ↓
serve traffic
```

The application still has dependency injection, controllers, repositories, lifecycle management, and AOP-style capabilities such as resilience, transactions, validation, caching, and security. The difference is not that those abstractions disappear, but **when the framework decides how they work**.

In Kora, many of those decisions have already been resolved by the time compilation finishes. The v2 architecture builds and validates the dependency container from `@KoraApp`, `@Component`, `@Module`, and related declarations during compilation. Missing or ambiguous dependencies can therefore become build-time errors instead of application-startup surprises.

That changes the relationship between application code and framework code in a fairly fundamental way.

---

## Compile Time Becomes Part of the Architecture { #compile-time-architecture }

Java developers already rely heavily on compile-time guarantees. If a method expects a `Payment`, you cannot accidentally pass a `Customer`. If a type disappears or a class no longer implements a required method, compilation fails.

Kora extends the same philosophy into areas that traditional frameworks often delegate to runtime machinery.

For example:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class PaymentService {

        private final PaymentRepository repository;

        public PaymentService(PaymentRepository repository) {
            this.repository = repository;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class PaymentService(private val repository: PaymentRepository)
    ```

The constructor is not merely a hint for a runtime dependency injector. It becomes part of a dependency graph that Kora can analyze during compilation. If `PaymentRepository` cannot be resolved, the framework does not have to boot the application to discover that fact because the compiler already has enough information.

The same principle applies to dependency cycles, ambiguous candidates, invalid mappings, and other framework-level contracts. This gives development a different feedback loop:

```text
write code
    ↓
compile
    ↓
framework verifies architecture
    ↓
fix structural problems
    ↓
run
```

instead of:

```text
write code
    ↓
compile
    ↓
start application
    ↓
framework discovers architecture
    ↓
something fails
```

As applications become larger, the distinction becomes increasingly valuable. The more architecture the compiler can verify, the less invisible framework state developers need to reconstruct mentally.

---

## Dependency Injection Is Generated { #dependency-injection }

Dependency injection is one of the clearest examples of Kora's approach.

A Kora application begins with an application graph:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application
    ```

Components and modules contribute nodes to that graph:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class OrderService {

        private final OrderRepository repository;

        public OrderService(OrderRepository repository) {
            this.repository = repository;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class OrderService(private val repository: OrderRepository)
    ```

Kora's annotation processors analyze those declarations and generate the application graph. The v2 documentation shows this explicitly: an interface annotated with `@KoraApp` results in generated graph code that describes the dependency relationships used when the application starts.

The important architectural point is not the exact name or shape of the generated class. It is that **dependency resolution becomes source generation**.

Conceptually, the result is close to ordinary object construction:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var repository = createOrderRepository(...);
    var service = new OrderService(repository);
    var controller = new OrderController(service);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val repository = createOrderRepository(...)
    val service = OrderService(repository)
    val controller = OrderController(service)
    ```

The real graph naturally handles more than this simplified example: lifecycle, dependency ordering, modules, optional values, tags, graph refreshes, and framework integrations. But the relationships themselves are still represented concretely rather than being rediscovered from scratch every time the JVM starts.

---

## Controllers Become Request Handlers { #controllers-request-handlers }

The same principle applies at the HTTP boundary.

A developer should be able to write an expressive controller:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class UserController {

        @HttpRoute(method = GET, path = "/users/{id}")
        public User get(@Path("id") long id) {
            // ...
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class UserController {

        @HttpRoute(method = GET, path = "/users/{id}")
        fun get(@Path("id") id: Long): User {
            // ...
        }
    }
    ```

A runtime-oriented framework can inspect this method when the application starts, analyze its annotations and parameters, determine converters and response mappers, and then construct the machinery needed to invoke it.

Kora can perform most of that analysis during compilation instead. It knows the route, method parameters, path bindings, argument types, return type, and available mappers, so it can generate the adapter that connects the HTTP server to the controller.

Conceptually, the generated handler performs something like:

```text
read path parameter
→ parse long
→ invoke controller.get(id)
→ map User to HTTP response
```

This is an important distinction. `@HttpRoute` is not merely runtime metadata that the framework repeatedly interprets. It acts much more like **input to a compiler**: the annotation describes intent, and the generated source implements it.

---

## Repositories Become Implementations { #repositories-implementations }

Database access follows the same model.

Consider:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface UserRepository extends JdbcRepository {

        @Query("""
            SELECT id, name, email
            FROM users
            WHERE id = :id
            """)
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
        fun findById(id: Long): User
    }
    ```

The developer describes the database contract, while the framework generates the implementation. During compilation Kora already knows the repository method, its parameter and return types, the SQL query, the selected database abstraction, and the available parameter and result mappers.

That gives the compiler enough information to generate repetitive plumbing while leaving the important part—the database operation itself—explicit.

The architectural pattern is the same:

```text
declaration
+
types
+
compile-time metadata
=
ordinary implementation
```

This is substantially different from treating repository interfaces primarily as runtime objects backed by dynamic invocation machinery.

---

## AOP Becomes Code Too { #aop-becomes-code }

Cross-cutting behavior is one of the places where runtime framework machinery can become particularly difficult to see.

Consider:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Retry("payments")
    @CircuitBreaker("payments")
    public Payment callProvider() {
        // ...
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Retry("payments")
    @CircuitBreaker("payments")
    fun callProvider(): Payment {
        // ...
    }
    ```

A runtime-oriented framework may create one or more proxies around this component and dynamically construct an invocation chain. Kora instead has enough information to generate the required subclass or wrapper during compilation.

Conceptually, the result may resemble:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class PaymentService__AopProxy extends PaymentService {

        @Override
        public Payment callProvider() {
            return retry.execute(() ->
                circuitBreaker.execute(() ->
                    super.callProvider()
                )
            );
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class `PaymentService__AopProxy` : PaymentService() {

        override fun callProvider(): Payment {
            return retry.execute {
                circuitBreaker.execute {
                    super.callProvider()
                }
            }
        }
    }
    ```

The real generated code depends on the aspects involved, but the architectural principle remains the same: **the behavior eventually becomes normal code**.

Kora uses compile-time AOP for capabilities such as resilience, transactions, validation, caching, and other infrastructure concerns instead of requiring runtime dynamic proxies to construct those chains after startup.

This also has a practical debugging benefit. If you need to understand what surrounds a method call, there is actual generated implementation code that can be inspected.

---

## Reflection Is Not the Enemy { #reflection }

It would be tempting to summarize Kora as "a framework that is fast because it does not use reflection." That description is too shallow.

Reflection is simply a JVM capability, and there are perfectly legitimate situations where it is useful. Removing a few reflective method calls would also not explain most of Kora's architecture.

The deeper objective is to **reduce runtime interpretation and hidden runtime machinery whenever the same decision can be made safely during compilation**.

Avoiding reflection, runtime bytecode generation, and large amounts of dynamic proxy machinery often follows naturally from that architecture, but those are consequences rather than the primary goal.

The important transformation is this:

```text
runtime discovery
runtime analysis
runtime wiring
runtime adaptation
```

into this:

```text
compile-time analysis
compile-time validation
source generation
normal execution
```

This shifts the discussion away from microbenchmarks about the cost of reflective invocation and toward a more meaningful question: **how much work does the framework still need to perform after the application has already started?**

---

## Startup Is an Architectural Property { #startup-architectural-property }

Startup time is sometimes treated as a cosmetic benchmark metric, but for backend infrastructure it is much more than that.

When a runtime-oriented container starts, it may need to perform a substantial amount of framework work before the service is ready. Kora has already moved much of that work into the build. The application graph exists, dependencies have been validated, and framework adapters have already been generated.

The remaining graph can then be instantiated and initialized, including parallel initialization where dependencies allow it.

This matters in production because the meaningful metric is not how quickly Java can enter `main()`. The useful question is how quickly a new instance can become production capacity.

For example:

```text
traffic spike
    ↓
autoscaler requests new instances
    ↓
containers start
    ↓
applications become ready
    ↓
new capacity serves traffic
```

The same consideration applies during rolling deployments. If every replacement instance spends longer performing runtime framework work, the cluster spends more time with reduced effective capacity.

Fast startup also affects integration tests, component tests, local development, ephemeral environments, scheduled jobs, low-traffic services, and scale-to-zero architectures. Kora deliberately pays part of the framework cost during compilation so that each later startup has less work to perform.

For long-running backend systems, that can be a very attractive trade.

---

## Runtime Overhead Is More Than CPU Cycles { #runtime-overhead }

Framework overhead is often reduced to benchmark numbers, but runtime overhead has several dimensions: CPU, memory, allocation pressure, startup work, metadata, proxy layers, generated runtime state, and additional call paths.

There is also another form of overhead that is harder to benchmark: **cognitive overhead**.

Suppose this line executes:

===! ":fontawesome-brands-java: `Java`"

    ```java
    orderService.create(order);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    orderService.create(order)
    ```

When debugging a heavily runtime-driven framework, an engineer may still need to determine whether `orderService` is the real object or a proxy, which interceptors apply, whether the proxy is interface-based or subclass-based, how self-invocation behaves, where the implementation was selected, which mapper was discovered, and when the object was registered.

Those are not CPU costs, but they are engineering costs.

Kora's compile-time model attacks both categories at once. Generated code can reduce unnecessary runtime machinery, but it also makes framework behavior visible. That second property is arguably just as important as the first.

---

## Predictability Over Magic { #predictability-over-magic }

Framework magic is attractive while everything works. The difficult part begins when it does not.

An annotation that turns ten lines of repetitive infrastructure into one line is useful. An annotation whose actual behavior requires understanding several layers of hidden runtime machinery is much less useful.

Kora tries to preserve declarative convenience without making the resulting behavior opaque. Annotations such as:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    ```

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpController
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpController
    ```

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    ```

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Retry
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Retry
    ```

remain concise, but they primarily act as declarations that participate in compilation. The generated source represents what those declarations mean.

That produces a comparatively direct path:

```text
annotation
    ↓
processor
    ↓
generated implementation
    ↓
compiler
    ↓
runtime
```

There is less runtime interpretation between declaration and execution, which makes framework behavior more deterministic. Predictability in this sense is not merely a performance feature; it is a maintainability feature.

---

## Generated Code Should Be Boring { #generated-code-boring }

Code generation sometimes has a poor reputation because developers associate it with enormous, unreadable files filled with cryptic implementation details.

That is not what generated framework infrastructure has to look like.

Kora treats generated source as part of its transparency model. Ideally, generated code should be relatively boring: request parameters are read, a method is called, a mapper is applied, a component is instantiated, or an AOP wrapper delegates through the required infrastructure.

Conceptually:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var request = requestMapper.apply(...);
    var result = controller.create(request);
    return responseMapper.apply(result);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val request = requestMapper.apply(...)
    val result = controller.create(request)
    return responseMapper.apply(result)
    ```

or:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var repository = module.repository(connectionFactory, mapper);
    var service = new Service(repository);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val repository = module.repository(connectionFactory, mapper)
    val service = Service(repository)
    ```

The goal is not for developers to spend their days reading generated source. In normal development they should not need to. The important property is that **they can inspect it when necessary**.

There is a significant difference between saying, "the framework probably wraps this method somehow," and being able to open the generated class and see exactly what executes.

---

## Framework Code Should Eventually Become JVM Code { #framework-becomes-jvm-code }

This leads to one of the simplest ways to describe Kora's philosophy.

Frameworks begin with convenient abstractions:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    ```

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpController
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpController
    ```

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    ```

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Cacheable
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Cacheable
    ```

Those abstractions are useful because nobody wants to repeatedly write infrastructure plumbing by hand. Eventually, however, the machine needs concrete operations: object construction, method calls, parameter parsing, response mapping, database driver calls, retries, and cache lookups.

Kora tries to make the transformation between these two levels explicit:

```text
high-level declaration
        ↓
compiler
        ↓
ordinary Java / Kotlin implementation
```

The framework therefore behaves less like an interpreter permanently sitting inside the application and more like a compiler that helps produce the application.

That is a subtle but important shift.

---

## Not Less Abstraction — Earlier Abstraction { #earlier-abstraction }

Compile-time frameworks are sometimes misunderstood as attempts to remove abstraction and force developers closer to low-level infrastructure code.

That is not the goal.

Writing this manually:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var id = Long.parseLong(request.pathParams().get("id"));
    var user = service.findById(id);
    var json = serializer.write(user);

    return HttpResponse.of(
        200,
        "application/json",
        json
    );
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val id = request.pathParams()["id"]!!.toLong()
    val user = service.findById(id)
    val json = serializer.write(user)

    return HttpResponse.of(
        200,
        "application/json",
        json
    )
    ```

is not inherently better than writing:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpRoute(method = GET, path = "/users/{id}")
    @Json
    public User get(@Path long id) {
        return service.findById(id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpRoute(method = GET, path = "/users/{id}")
    @Json
    fun get(@Path id: Long): User {
        return service.findById(id)
    }
    ```

The second version communicates intent more clearly, and repetitive transport plumbing should absolutely be automated.

Kora's answer is not to eliminate the high-level API, but to compile it into a lower-level explicit implementation. Developers get a concise programming model, while runtime execution gets direct code.

In other words, Kora does not try to remove abstraction. It tries to **move much of the abstraction cost away from runtime**.

---

## Thin Abstractions Matter { #thin-abstractions }

Compile-time generation alone is not sufficient. A framework could generate enormous abstraction stacks just as easily as it could construct them dynamically.

Kora combines generation with another design choice: stay relatively close to the underlying technologies. The project uses familiar JVM concepts around Java and Kotlin, JDBC, Cassandra, HTTP, Kafka, gRPC, OpenTelemetry, and other infrastructure rather than trying to replace each technology with a completely separate conceptual model.

That matters because every framework abstraction has a learning cost. Developers need to understand the technology itself, the framework's model of that technology, and the mapping between the two.

Thin abstractions try to keep that mapping small. The result is not zero abstraction, but abstraction focused on removing repetitive work without hiding the technology behind a completely different mental model.

---

## Why This Matters for Large Systems { #large-systems }

For a single small service, many of these differences can look academic. Modern hardware can comfortably run applications built with many different JVM architectures.

Organizations, however, rarely operate one service.

A small per-instance framework cost is multiplied across instances per service, availability zones, services, teams, environments, and scaling headroom. What appears insignificant on a developer laptop can become real infrastructure cost when repeated thousands of times.

The same multiplication happens with engineering complexity. One obscure runtime convention may be manageable for a framework expert, but that convention is eventually multiplied across hundreds of services, dozens of developers, new hires, upgrades, and production incidents.

Kora therefore treats efficiency and transparency as related concerns. Less framework machinery means fewer resources consumed by each application, while more explicit machinery means less runtime state engineers need to keep in their heads.

---

## Compile-Time Errors Are a Feature { #compile-time-errors }

One consequence of this architecture is that Kora can be stricter during compilation.

Suppose a component requires:

===! ":fontawesome-brands-java: `Java`"

    ```java
    PaymentGateway
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    PaymentGateway
    ```

but no valid implementation exists. A runtime framework may allow the project to compile successfully, build a container image, start a deployment, and only then fail while constructing its application context.

Kora would rather detect that problem while compiling.

The same applies to ambiguous dependencies, invalid mappings, dependency cycles, and many other framework contracts.

Compare the two failure modes:

```text
build successful
container image created
deployment starts
application starts
framework constructs context
context creation fails
deployment fails
```

versus:

```text
compile
error
```

The second failure is cheaper.

A strict compiler can therefore act as another architecture test rather than merely as a syntax checker.

---

## Build-Time Cost Is Not Free { #build-time-cost }

Compile-time generation naturally has a cost. Annotation processors and KSP processors need to run, generated source needs to be compiled, and graph analysis takes time.

Kora's architecture does not make framework work disappear. It **relocates that work**.

Instead of paying a larger part of the cost during every application startup, the framework pays it during the build. For backend applications this is often favorable because one artifact may be started repeatedly across developer machines, tests, CI environments, staging, production, rolling deployments, autoscaling events, and machine failures.

Compilation occurs before all of those runs.

The relevant trade is therefore not "work versus no work." It is **where that work belongs**.

---

## Why Not Generate Everything? { #why-not-generate-everything }

There is also an important boundary to compile-time generation.

Some information is inherently dynamic. Configuration values change, database results change, remote systems become healthy or unhealthy, requests carry different data, and resilience state evolves while the process is running.

Kora is not trying to turn a server application into a completely static program. Instead, it separates architecture that is already knowable during compilation from state that genuinely belongs to runtime.

Compile-time questions include:

```text
Which components exist?
What depends on what?
How should this controller method map its arguments?
How should this repository method execute its query?
Which aspects surround this method?
Which mapper converts this type?
```

Runtime questions include:

```text
What is the configured timeout?
Which request arrived?
What did the database return?
Is the remote service healthy?
Has the circuit breaker opened?
What is the current trace context?
```

The goal is not to make everything static. The goal is to avoid repeatedly discovering at runtime things that were already knowable during compilation.

---

## A Framework You Can Reason About { #framework-you-can-reason-about }

The practical result is not simply a framework that can start quickly or consume fewer resources. It is a framework whose behavior is intended to remain understandable.

Given an HTTP request, an engineer should be able to conceptually follow a path such as:

```text
HTTP request
    ↓
generated HTTP handler
    ↓
controller
    ↓
service
    ↓
generated AOP wrapper
    ↓
generated repository
    ↓
JDBC
```

without crossing a large opaque runtime container whose internal state must first be reconstructed.

That makes debugging, architecture reviews, and onboarding easier because concrete relationships remain visible in code.

There is also a useful side effect for modern development tooling. AI-assisted coding tools reason much more reliably about explicit Java or Kotlin classes, method calls, generated implementations, and typed contracts than about behavior that exists only as runtime container state. Generated source therefore benefits not only human inspection but also machine-assisted reasoning.

---

## The Broader Philosophy { #broader-philosophy }

Compile-time generation is ultimately one expression of a broader Kora principle: move knowledge out of hidden framework runtime state and into things that can be inspected directly—types, source code, generated source, compiler diagnostics, and explicit configuration.

That principle influences several parts of Kora's design:

* compile-time dependency injection;
* generated HTTP adapters;
* generated repositories;
* generated mappings;
* compile-time AOP;
* strongly typed OpenAPI generation;
* explicit modules;
* thin integrations;
* direct Java and Kotlin programming models.

The resulting framework is deliberately less dynamic in some places than traditional runtime-oriented frameworks. That is not accidental. Kora favors certainty over runtime flexibility that many backend applications never actually need, generated implementation over implicit runtime interpretation, and compiler errors over runtime surprises.

---

## The Framework Should Disappear { #framework-should-disappear }

A useful way to think about the end goal is that a framework should help developers express intent and then get out of the way.

Developers write declarations such as:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    interface UserRepository { ... }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface UserRepository { ... }
    ```

===! ":fontawesome-brands-java: `Java`"

    ```java
    @HttpController
    class UserController { ... }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @HttpController
    class UserController { ... }
    ```

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    class UserService { ... }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class UserService { ... }
    ```

The framework generates the plumbing required to make those declarations real. After that, as much as possible, what remains should look unsurprising to a JVM engineer: objects, method calls, interfaces, generated classes, database drivers, HTTP handlers, executors, virtual threads, and ordinary JVM code.

This is why generated source is so central to Kora's architecture. It represents the point where a framework abstraction becomes a concrete program implementation.

The framework no longer needs to remain a permanent interpreter between business code and the JVM.

---

## Compile-Time Certainty { #compile-time-certainty }

Kora is sometimes introduced through performance numbers. Those numbers matter: fast startup, low memory consumption, and low runtime overhead are all desirable properties.

But they are consequences of a deeper architectural decision.

Kora asks a more fundamental question:

> How much of the framework can become part of the compiled application instead of remaining part of the runtime environment?

Dependency injection can. HTTP adapters can. Repositories can. Mappers can. AOP can. Large parts of application wiring can.

Once those decisions move into compilation, several useful properties emerge together:

```text
more compile-time validation
        ↓
fewer runtime surprises

less runtime discovery
        ↓
faster startup

less runtime machinery
        ↓
lower overhead

generated source
        ↓
greater transparency

explicit graph
        ↓
greater predictability
```

That combination is what makes the compile-time model interesting.

It is not reflection avoidance by itself, code generation by itself, or benchmark performance by itself. The important idea is that the framework turns high-level declarations into concrete, typed, inspectable JVM code **before production ever sees the application**.

That is the architecture behind Kora, and it can be summarized in one principle:

> **If the framework can know something at compile time, there should be a very good reason to discover it again at runtime.**
