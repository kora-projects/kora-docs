---
title: Compile-Time AOP Without Dynamic Proxies — Kora Framework
description: How the Kora Framework implements aspect-oriented programming with generated compile-time subclasses instead of runtime dynamic proxies.
search:
  exclude: true
---
# Compile-Time AOP Without Dynamic Proxies

Aspect-oriented programming has a reputation problem in the Java ecosystem. The underlying idea is useful: some behavior genuinely belongs around a method call rather than inside the business method
itself. Transactions, validation, retries, circuit breakers, caching, tracing, authorization, metrics, and logging all fit that description. The problem is not the idea of interception. The problem is
how interception has traditionally been implemented.

In many Java frameworks, an annotation that appears harmless in source code can activate a surprisingly large runtime mechanism. A container discovers the annotation, decides that the object needs
interception, creates a proxy, stores metadata describing the advice chain, resolves interceptors, and routes method calls through that machinery. The application may compile even if part of that
model is invalid, because the final object graph and interception strategy are resolved only when the application starts. The annotation looks declarative and simple, while the execution path becomes
indirect.

The Kora Framework takes a different approach. Its AOP model is built around compile-time generation. Instead of waiting until runtime to discover that a component requires interception, Kora processes the relevant
annotations during compilation and generates a concrete class containing the interception logic. For Java this happens through annotation processing; for Kotlin, through KSP. The generated source is
ordinary Java or Kotlin source code. It becomes part of the application graph like other generated Kora components, and the JVM executes it as ordinary compiled code.

That difference sounds like an implementation detail until we follow it through the whole engineering model. Moving AOP from runtime to compile time changes when errors are detected, what kind of code
runs in production, how a developer debugs an intercepted method, how the JVM optimizes the call path, how startup behaves, how much metadata must be retained, and even how the classic self-invocation
problem should be understood.

The important comparison is therefore not simply:

```text
AOP
vs
no AOP
```

It is:

```text
Runtime proxy
vs
generated subclass / wrapper
```

Both approaches can provide declarative interception. Both can make an annotation trigger behavior around a method call. Both can implement the same cross-cutting concerns. But they place complexity
in very different parts of the system. Kora deliberately pays more of that complexity during compilation so that less remains in the runtime application.

---

## AOP Is Really About Transforming a Call Path

Before comparing implementations, it helps to remove some historical terminology and look at the mechanical problem. Suppose an application contains a service:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class PaymentService {

        public PaymentReceipt pay(Payment payment) {
            return executePayment(payment);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    open class PaymentService {

        open fun pay(payment: Payment): PaymentReceipt {
            return executePayment(payment)
        }
    }
    ```

Now imagine that the method needs validation, tracing, and retry behavior. Conceptually, the call should no longer mean only:

```text
caller
  |
  v
PaymentService.pay()
```

It should mean something closer to:

```text
caller
  |
  v
validate input
  |
  v
start trace
  |
  v
retry policy
  |
  v
PaymentService.pay()
  |
  v
finish trace
```

The business developer could write all of that manually, but then infrastructure policy would be mixed into every service method. AOP exists to separate those orthogonal concerns from business logic.
The central engineering question is not whether interception is useful; it is **when and how the framework turns the declarative annotation into an executable call path**.

A runtime-proxy framework answers: at runtime, by inserting an intermediary object and routing calls through an interceptor mechanism.

Kora answers: at compile time, by generating the intermediary class as source code.

That choice is the foundation for everything else in this article.

---

## The Traditional Runtime Proxy Model

A runtime proxy is an object created while the application is starting or running. The framework usually inspects some combination of class metadata, annotations, interfaces, bean definitions, and
configuration, then decides that calls to a component must be intercepted.

A simplified architecture looks like this:

```text
Application code
      |
      v
Runtime proxy
      |
      v
Interceptor chain
      |
      v
Target object
```

The proxy is not normally written by the application developer. Depending on the framework and configuration, it may be implemented using a JDK dynamic proxy, runtime-generated bytecode, a subclass
created by a library such as Byte Buddy or CGLIB, or another invocation mechanism. The exact technology varies, but the runtime responsibilities are similar: determine which methods are advised,
create or configure the proxy, associate interceptors with each invocation, retain enough metadata to execute the advice correctly, and ensure that dependency injection exposes the proxy where
interception is expected.

A generic invocation API may conceptually look like this:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public Object invoke(
        Object proxy,
        Method method,
        Object[] args
    ) throws Throwable {
        return interceptorChain.invoke(method, args, target);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun invoke(
        proxy: Any,
        method: Method,
        args: Array<Any>
    ): Any {
        return interceptorChain.invoke(method, args, target)
    }
    ```

That is extremely flexible. The framework can make decisions using runtime information and can apply general interception infrastructure to many classes without generating application-specific source
in advance. The trade-off is that the execution model remains dynamic. A normal-looking method call can enter a generic invocation handler, inspect metadata, select interceptors, allocate invocation
state, and eventually reach the target.

Modern JVMs are very good at optimizing code, and well-engineered proxy frameworks can make many of these paths fast. It would be wrong to reduce the comparison to an outdated claim that all runtime
proxies are slow because they use `Method.invoke`. The more important distinction is architectural: runtime proxying keeps part of the framework's decision-making machinery alive in the production
process.

Kora asks whether that machinery needs to remain dynamic when the relevant structure is already available during compilation.

---

## Kora's Compile-Time AOP Model

Kora moves the interception decision into its annotation-processing pipeline. The compiler sees the component, sees the AOP annotations, validates whether the method can be intercepted, resolves the
required aspect support, and generates a concrete class around the original component.

Conceptually, a generated class can look like this:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class $PaymentService__AopProxy
        extends PaymentService {

        private final PaymentValidator validator;
        private final Retry paymentRetry;
        private final Tracer tracer;

        public $PaymentService__AopProxy(
            PaymentValidator validator,
            Retry paymentRetry,
            Tracer tracer
        ) {
            this.validator = validator;
            this.paymentRetry = paymentRetry;
            this.tracer = tracer;
        }

        @Override
        public PaymentReceipt pay(Payment payment) {
            validator.validate(payment);

            var span = tracer.startSpan("payment");
            try {
                return paymentRetry.execute(
                    () -> super.pay(payment)
                );
            } finally {
                span.end();
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class `$PaymentService__AopProxy`(
        private val validator: PaymentValidator,
        private val paymentRetry: Retry,
        private val tracer: Tracer
    ) : PaymentService() {

        override fun pay(payment: Payment): PaymentReceipt {
            validator.validate(payment)

            val span = tracer.startSpan("payment")
            try {
                return paymentRetry.execute {
                    super.pay(payment)
                }
            } finally {
                span.end()
            }
        }
    }
    ```

This is a conceptual example, not a promise that every Kora aspect emits exactly that source shape. The important point is that there is no need for a generic runtime invocation handler to discover
what should happen for this method. The compiler has already produced a method body that expresses the required behavior.

At runtime, the path is much closer to:

```text
caller
  |
  v
$PaymentService__AopProxy.pay()
  |
  +--> validation
  |
  +--> tracing
  |
  +--> retry
  |
  v
super.pay()
```

The generated class may still reasonably be called a proxy because it stands between the caller and the original method implementation. Kora's generated classes themselves use AOP-proxy naming. The
decisive difference is that this proxy is not discovered and constructed as a late runtime mechanism. It is generated before the application runs, compiled with the application, wired into the
application graph, and shipped as part of the deployment artifact.

The runtime is executing pre-generated code, not interpreting an AOP model.

---

## Runtime Proxy vs Generated Subclass

The architectural contrast can be summarized as follows:

| Concern              | Runtime proxy                                     | Kora generated subclass/wrapper             |
|----------------------|---------------------------------------------------|---------------------------------------------|
| Discovery            | Usually runtime/container startup                 | Compile time                                |
| Interception plan    | Built or resolved dynamically                     | Materialized in generated source            |
| Invalid method shape | Can be discovered late                            | Can be rejected during compilation          |
| Runtime metadata     | Usually required                                  | Less generic runtime metadata needed        |
| Invocation path      | Generic proxy/interceptor machinery               | Generated method body                       |
| Reflection           | Common in runtime infrastructure                  | Kora aims to avoid runtime reflection       |
| Startup work         | Proxy discovery/construction may occur            | Proxy code already exists                   |
| Debugging            | Often crosses generic framework internals         | Generated class can be opened and read      |
| Optimization surface | Generic/dynamic                                   | Specialized bytecode per method             |
| Self invocation      | Often problematic for external proxy/target pairs | Follows subclass virtual-dispatch semantics |
| Static analysis      | More runtime behavior to reconstruct              | More final structure exists in the artifact |

The table is useful, but the deeper consequence is that Kora changes where abstraction lives. A runtime AOP framework keeps the abstraction as a runtime abstraction. Kora uses the abstraction in
handwritten source, then lowers it into explicit implementation code during compilation.

That pattern appears across Kora, not only in AOP. Dependency wiring, repositories, HTTP handlers, mappers, and other infrastructure follow the same compile-time philosophy. AOP is therefore not an
isolated optimization. It is one expression of the framework's general architecture.

---

## Method Interception as Generated Code

Method interception is the core mechanism behind AOP. If we understand that mechanism in Kora, most other differences follow naturally.

Imagine a service with a retry annotation:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class CatalogService {

        @Retry("catalog")
        public Product loadProduct(long id) {
            return loadFromRemoteSystem(id);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    open class CatalogService {

        @Retry("catalog")
        open fun loadProduct(id: Long): Product {
            return loadFromRemoteSystem(id)
        }
    }
    ```

A runtime AOP framework may effectively execute something like:

```text
invoke proxy
  |
  v
find method metadata
  |
  v
find retry interceptor
  |
  v
create invocation context
  |
  v
retryInterceptor.invoke(context)
  |
  v
context.proceed()
  |
  v
target.loadProduct(id)
```

A compile-time generator can instead emit a dedicated override:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Override
    public Product loadProduct(long id) {
        return this.retry.execute(
            () -> super.loadProduct(id)
        );
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    override fun loadProduct(id: Long): Product {
        return this.retry.execute {
            super.loadProduct(id)
        }
    }
    ```

The high-level behavior is the same. The execution model is not. There is no fundamental need for an object representing "the current method invocation" if the compiler can express the operation as
normal code. There is no need to look up the retry policy from generic method metadata if the generated class already has the correct dependency. There is no need to discover which target method
should run next if the generated method can call it directly.

The generated method becomes the interceptor chain.

This is one of the most important ideas behind compile-time AOP: **the chain does not have to remain a data structure at runtime; it can become control flow**.

Instead of representing:

```text
[
  ValidationInterceptor,
  TracingInterceptor,
  RetryInterceptor
]
```

and interpreting that list, a generator can lower the chain into nested code:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Override
    public Result operation(Request request) {
        validator.validate(request);

        return tracing.trace("operation", () ->
            retry.execute(() ->
                super.operation(request)
            )
        );
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    override fun operation(request: Request): Result {
        validator.validate(request)

        return tracing.trace("operation") {
            retry.execute {
                super.operation(request)
            }
        }
    }
    ```

The exact shape depends on the aspects, but mechanically this is what compile-time lowering enables. The difference resembles interpreting an expression tree versus compiling it into executable
control flow. Both can represent the same semantics; one preserves a generic model at runtime, while the other produces specialized code in advance.

---


Java developers often associate annotations with the sequence:

```text
annotations
  ->
reflection
  ->
runtime framework behavior
```

That association is historical, not fundamental. Annotations can also be inputs to compile-time code generation. Kora treats them primarily as compiler-visible declarations from which source can be
generated.

An annotation that activates validation, caching, resilience, transactions, security, or logging tells the processor that a method needs additional behavior. The generated class contains the code
needed to attach that behavior. The running application does not need to rediscover the annotation and ask what it means every time the process starts.

This makes an important distinction between two kinds of declarative programming:

```text
annotation
  ->
hidden runtime interpretation
```

and:

```text
annotation
  ->
generated source
  ->
ordinary bytecode
```

The first asks developers to trust framework machinery that materializes later. The second gives them an implementation artifact that can be inspected before the application runs.

Kora still provides a declarative API. Developers do not hand-write every retry, transaction, or validation wrapper. But the declaration has a visible compilation product.

---


Real methods often have more than one cross-cutting concern. A service operation can be validated, cached, retried, traced, logged, and transactional at the same time. Once multiple aspects are
involved, ordering becomes semantically important.

Consider:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Validate
    @Cacheable("users")
    @Retry("users")
    public User getUser(long id) {
        return repository.findById(id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Validate
    @Cacheable("users")
    @Retry("users")
    open fun getUser(id: Long): User {
        return repository.findById(id)
    }
    ```

These structures are not equivalent:

```text
cache
  -> retry
      -> method
```

and:

```text
retry
  -> cache
      -> method
```

Likewise, a transaction outside a retry loop behaves differently from a transaction created for every retry attempt. Validation before a cache lookup may behave differently from validation only on
cache misses. Tracing around the entire operation differs from tracing each attempt individually.

A runtime interceptor model commonly represents composition as a chain of objects that each call something like `proceed()`. Compile-time AOP can resolve the same composition while generating the
class. The generator can determine the order and materialize it as nested control flow.

Conceptually:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Override
    public User getUser(long id) {
        validator.validate(id);

        return cache.computeIfAbsent(id, () ->
            retry.execute(() ->
                super.getUser(id)
            )
        );
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    override fun getUser(id: Long): User {
        validator.validate(id)

        return cache.computeIfAbsent(id) {
            retry.execute {
                super.getUser(id)
            }
        }
    }
    ```

The generated source is therefore more than an implementation artifact. It is also a diagnostic representation of aspect composition. When developers ask, "Which aspect is outside which?", there is a
concrete place to look.

That matters because aspect-ordering bugs are among the hardest AOP problems to diagnose when the effective chain is assembled indirectly from configuration, priorities, runtime container rules, and
proxy metadata. Compile-time generation cannot eliminate semantic complexity, but it can make the final result inspectable.

---

## Compile-Time Validation Changes the Failure Model

The strongest advantage of compile-time AOP is not raw speed. It is moving an entire class of failures earlier in the development lifecycle.

Consider the stages at which an error can be discovered:

```text
editor
  ->
compile
  ->
test startup
  ->
integration test
  ->
deployment
  ->
first production request
```

The later the error appears, the more expensive it becomes. A runtime framework may accept source that is syntactically and type-correct even though the requested AOP behavior cannot actually be
applied in the intended way. The failure can then emerge when the container creates the bean, when a proxy factory tries to subclass the class, when an interceptor resolves dependencies, or only when
a particular method is invoked.

Compile-time AOP has access to the program structure while compilation is already happening. That allows unsupported combinations to be rejected before the application artifact is produced.

Kora's subclass-based AOP imposes concrete structural requirements. A Java class that must be subclassed cannot be `final`. In Kotlin, where classes and methods are final by default, the intercepted
class and relevant methods need to be open so generated overrides are possible. This is not incidental syntax; it follows directly from the implementation model.

If the generator needs to produce a shape like:

===! ":fontawesome-brands-java: `Java`"

    ```java
    final class $Service__AopProxy extends Service {
        @Override
        public Result operation() {
            // aspect logic
            return super.operation();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class `$Service__AopProxy` : Service() {
        override fun operation(): Result {
            // aspect logic
            return super.operation()
        }
    }
    ```

then a final `Service` or final `operation()` cannot participate in that model. Kora exposes the constraint rather than hiding it behind runtime bytecode tricks. The compiler can then explain the
problem while the developer is still editing the code.

That is a fundamentally better point in time to fail.

---


Suppose a Kotlin service is written like this:

```kotlin
@Component
class UserService {

    @Retry("users")
    fun load(id: Long): User {
        // ...
    }
}
```

Kotlin classes and methods are final unless declared otherwise. A generated subclass cannot override `load`. The corrected class makes the interception requirement explicit:

```kotlin
@Component
open class UserService {

    @Retry("users")
    open fun load(id: Long): User {
        // ...
    }
}
```

This constraint can be described as a downside of subclass-based AOP, and it is a real trade-off. But it also makes the mechanism honest. The class is open because the framework will generate a
subclass. The method is open because the framework will override it. The source reflects the dispatch semantics required by the framework.

Runtime frameworks can sometimes relax similar restrictions through instrumentation, weaving, or other bytecode techniques, but every additional mechanism increases the distance between source-level
semantics and runtime behavior. Kora chooses a narrower model that is easier to reason about and validate.

---


Compile-time validation is not limited to checking whether a method can technically be overridden. An aspect can validate its own contract. It may require a non-empty policy name, a supported return
type, parameters that can form a cache key, a supported method shape, or dependencies that can be resolved from the application graph.

A runtime framework can validate those conditions too, but it must do so later. A compile-time processor can validate everything already knowable from source while it has the type model in hand.

This changes the role of the compiler. In an ordinary Java application, compilation checks language rules and static types. In a compile-time framework, the compiler also becomes an architectural
validation stage. The build can answer questions such as:

```text
Can this class be proxied?
Can this method be overridden?
Is this annotation supported here?
Can the aspect dependencies be resolved?
Can the generated class be constructed?
Can the application graph contain the generated component?
```

The generated source then goes through normal Java or Kotlin compilation as another correctness layer. Kora does not merely emit opaque metadata. It emits source that must satisfy the same language
compiler as handwritten code.

That gives the framework a powerful property: generated AOP code is type-checked as ordinary application code.

---

## The Application Graph and AOP Are Connected

AOP does not exist outside dependency injection. Generated proxies need dependencies. A validation aspect may require validator objects. A retry aspect needs resilience infrastructure. A transaction
aspect needs transaction or database components. A cache aspect needs cache components. Logging and telemetry aspects require their own collaborators.

With runtime proxies, these relationships can be hidden inside container machinery. Compile-time generation can make them ordinary constructor dependencies.

Conceptually:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class $OrderService__AopProxy
        extends OrderService {

        private final OrderValidator validator;
        private final TransactionManager txManager;
        private final Retry retry;

        public $OrderService__AopProxy(
            OrderRepository repository,
            OrderValidator validator,
            TransactionManager txManager,
            Retry retry
        ) {
            super(repository);
            this.validator = validator;
            this.txManager = txManager;
            this.retry = retry;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class `$OrderService__AopProxy`(
        repository: OrderRepository,
        private val validator: OrderValidator,
        private val txManager: TransactionManager,
        private val retry: Retry
    ) : OrderService(repository)
    ```

The AOP proxy is therefore part of the application graph, not a mysterious shell added after dependency resolution. If an aspect requires infrastructure, that infrastructure can participate in the
same graph and lifecycle rules as other components.

The graph Kora generates is not simply constructing a target and then asking a second runtime phase whether that target should be proxied. The generated proxied form can itself be the component that
callers receive.

This reduces the conceptual split between bean definition, target instance, proxy factory, interceptor chain, and exposed object.

---


There are two related compile-time interception strategies worth distinguishing. A generated subclass uses inheritance:

```text
GeneratedService
    extends
OriginalService
```

A generated wrapper uses composition:

```text
GeneratedService
    has a
OriginalService
```

A wrapper can look like:

===! ":fontawesome-brands-java: `Java`"

    ```java
    final class GeneratedService implements Service {
        private final Service delegate;

        @Override
        public Result call(Request request) {
            // before
            var result = delegate.call(request);
            // after
            return result;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class GeneratedService(private val delegate: Service) : Service {

        override fun call(request: Request): Result {
            // before
            val result = delegate.call(request)
            // after
            return result
        }
    }
    ```

A subclass looks like:

===! ":fontawesome-brands-java: `Java`"

    ```java
    final class GeneratedService extends Service {
        @Override
        public Result call(Request request) {
            // before
            var result = super.call(request);
            // after
            return result;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class GeneratedService : Service() {
        override fun call(request: Request): Result {
            // before
            val result = super.call(request)
            // after
            return result
        }
    }
    ```

At a high architectural level, both are statically generated alternatives to runtime proxy construction. For self invocation, however, subclass semantics matter enormously. Kora's generated AOP model
is documented in terms of generated proxy subclasses, which is why Java `final` and Kotlin `open` rules matter and why internal virtual calls behave differently from the classic wrapper/target proxy
model.

---

## Self Invocation: The Classic Runtime Proxy Problem

Self invocation is one of the most famous traps in proxy-based AOP. Consider this service:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public class BillingService {

        public void processInvoice(Invoice invoice) {
            charge(invoice);
        }

        @Retry("payments")
        public void charge(Invoice invoice) {
            // remote payment call
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    open class BillingService {

        open fun processInvoice(invoice: Invoice) {
            charge(invoice)
        }

        @Retry("payments")
        open fun charge(invoice: Invoice) {
            // remote payment call
        }
    }
    ```

Now imagine a traditional external proxy:

```text
BillingServiceProxy
      |
      v
BillingService target
```

A call from another component goes through the proxy:

```text
other component
      |
      v
proxy.charge()
      |
      v
retry interceptor
      |
      v
target.charge()
```

But when `processInvoice()` runs on the target and calls `this.charge(invoice)`, the call happens inside the target object. It does not leave the target, travel outward to the external proxy, and then
come back in.

The path is:

```text
target.processInvoice()
      |
      v
target.charge()
```

rather than:

```text
target.processInvoice()
      |
      v
proxy.charge()
      |
      v
interceptor
      |
      v
target.charge()
```

As a result, annotations on the internally called method may be bypassed. This is the classic self-invocation problem associated with an external proxy that wraps a separate target instance.

Developers often work around it by extracting the method into another bean, injecting a self-reference proxy, asking the container for the proxied self, or switching to weaving. Those workarounds
exist because the proxy is not actually the object whose internal `this` calls are executing.

---

## Why Generated Subclass Interception Changes Self Invocation

Subclass-based interception has different dispatch semantics. Consider an original class:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public class BillingService {

        public void processInvoice(Invoice invoice) {
            charge(invoice);
        }

        public void charge(Invoice invoice) {
            doCharge(invoice);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    open class BillingService {

        open fun processInvoice(invoice: Invoice) {
            charge(invoice)
        }

        open fun charge(invoice: Invoice) {
            doCharge(invoice)
        }
    }
    ```

Now generate:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class $BillingService__AopProxy
        extends BillingService {

        @Override
        public void charge(Invoice invoice) {
            retry.execute(() -> {
                super.charge(invoice);
                return null;
            });
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class `$BillingService__AopProxy` : BillingService() {

        override fun charge(invoice: Invoice) {
            retry.execute {
                super.charge(invoice)
                null
            }
        }
    }
    ```

Suppose the actual object in the application graph is an instance of `$BillingService__AopProxy`. When the caller invokes `service.processInvoice(invoice)`, the subclass inherits `processInvoice()`
from `BillingService`. Inside that inherited method, the call to `charge(invoice)` is a virtual call on `this`. But `this` is the generated subclass instance.

Normal JVM virtual dispatch therefore looks for the most specific override of `charge()`, finds the generated proxy override, and enters the retry logic.

The path becomes:

```text
$BillingService__AopProxy instance
      |
      v
BillingService.processInvoice()
      |
      v
virtual call: this.charge()
      |
      v
$BillingService__AopProxy.charge()
      |
      v
retry
      |
      v
super.charge()
```

This is an important difference from the classic "proxy contains target" arrangement. The generated subclass is not merely an external object surrounding a separate target for ordinary dispatch. It is
the runtime object.

Because ordinary virtual dispatch remains in effect, many same-instance calls to overridable methods naturally reach generated overrides. The blanket statement "AOP proxies cannot intercept self
invocation" is therefore too broad. It describes a common external-proxy architecture, not all proxy mechanisms.

---

## The Limits of Self Invocation

Compile-time subclass generation does not make every internal call interceptable. Normal Java and Kotlin dispatch rules still apply.

A private method cannot be overridden:

===! ":fontawesome-brands-java: `Java`"

    ```java
    private void charge(Invoice invoice) {
        // ...
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    private fun charge(invoice: Invoice) {
        // ...
    }
    ```

A final method cannot be overridden:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final void charge(Invoice invoice) {
        // ...
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun charge(invoice: Invoice) {
        // ...
    }
    ```

A static method is not virtual instance dispatch:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public static void charge(Invoice invoice) {
        // ...
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    companion object {
        fun charge(invoice: Invoice) {
            // ...
        }
    }
    ```

An explicit `super.method()` call intentionally bypasses an override. Constructors also have special semantics and cannot be intercepted like ordinary overridable methods.

The correct mental model is therefore not:

```text
compile-time AOP magically intercepts every call
```

It is:

```text
generated subclass AOP follows ordinary virtual dispatch
```

If an internal method call is virtual and the generated subclass overrides that method, normal dispatch can reach the aspect. If the call cannot participate in overriding, subclass-based interception
cannot insert itself into that call.

This is one of the strongest transparency properties of the model: the same language rules developers already know continue to matter.

---


The self-invocation problem appears in transactions, caching, retries, validation, security, and many other practical cases.

Consider transactions:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public void importOrders(List<Order> orders) {
        for (var order : orders) {
            saveOrder(order);
        }
    }

    @Transactional
    public void saveOrder(Order order) {
        repository.save(order);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    open fun importOrders(orders: List<Order>) {
        for (order in orders) {
            saveOrder(order)
        }
    }

    @Transactional
    open fun saveOrder(order: Order) {
        repository.save(order)
    }
    ```

With an external target proxy, `importOrders()` calling `saveOrder()` internally may bypass the transaction interceptor. With subclass-based interception, if `saveOrder()` is overridable and the
actual instance is the generated subclass, ordinary virtual dispatch can route the internal call through the generated transaction override.

The same reasoning applies to retry:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public Result orchestrate() {
        return unstableRemoteCall();
    }

    @Retry("remote")
    public Result unstableRemoteCall() {
        // ...
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    open fun orchestrate(): Result {
        return unstableRemoteCall()
    }

    @Retry("remote")
    open fun unstableRemoteCall(): Result {
        // ...
    }
    ```

and caching:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public User loadAndTransform(long id) {
        return transform(loadUser(id));
    }

    @Cacheable("users")
    public User loadUser(long id) {
        // ...
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    open fun loadAndTransform(id: Long): User {
        return transform(loadUser(id))
    }

    @Cacheable("users")
    open fun loadUser(id: Long): User {
        // ...
    }
    ```

The behavior can be reasoned about using ordinary dispatch instead of memorizing a framework-specific rule that annotations stop working when a neighboring method calls them.

This does not mean every internal method should become an AOP boundary. Clear component boundaries are still easier to maintain. The important point is that the mechanism is coherent with the object
model.

---


The use of `super` in generated overrides is worth understanding precisely. When the generated proxy's override finishes applying aspects, it must eventually reach the original implementation.
Calling:

===! ":fontawesome-brands-java: `Java`"

    ```java
    super.load(id)
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    super.load(id)
    ```

does exactly that. It intentionally bypasses the current override so the method does not recurse forever.

The two relevant paths are therefore:

### External call

```text
proxy.load
  ->
aspect
  ->
super.load
```

### Internal virtual call from original code to another intercepted method

```text
original method executing on proxy instance
  ->
this.otherMethod
  ->
proxy.otherMethod override
  ->
other aspect
  ->
super.otherMethod
```

These are normal inheritance semantics. No special self-proxy lookup is required. Understanding virtual dispatch and `super` explains much of subclass-based AOP without any framework folklore.

---

## Performance Is a Whole-System Question

AOP performance discussions often collapse into microbenchmarks of one proxy call. That is too narrow. The relevant performance budget includes at least four stages:

```text
build time
startup
steady-state invocation
optimization / warm-up
```

Kora intentionally moves work from the second and third stages toward the first. At build time, processors inspect source structure and generate classes. At startup, the application does not need to
perform the same level of reflective discovery or runtime proxy planning. At steady state, intercepted methods execute concrete generated bytecode.

That does not mean an aspect has zero overhead. A retry policy checks state and may loop. A cache performs a lookup. Validation executes validators. A transaction starts or joins transactional state.
Tracing creates or updates telemetry context. Those costs are real because the behavior itself is real.

The meaningful claim is narrower: **Kora minimizes framework overhead around the behavior that the aspect actually needs to perform**.

The framework cannot remove the essential cost of a database transaction, but it can avoid layering a general-purpose runtime invocation engine on top of it.

---


A generic runtime interceptor mechanism often needs some combination of an invocation object, a method descriptor, an argument array, chain position state, metadata lookup, indirect target invocation,
and exception adaptation. A sophisticated framework can cache or optimize much of this, and HotSpot can inline stable paths. Runtime proxying is not automatically slow.

But generic machinery exists because the runtime must preserve flexibility.

If the compiler already knows:

```text
method = UserService.load(long)
aspects = validation -> cache -> retry
dependencies = validator, userCache, retry
target call = super.load(id)
```

then the production process does not need a generic representation of those facts. The generator can emit the exact sequence.

That can lead to fewer metadata lookups, fewer framework objects on the hot path, fewer dynamic dispatch points, fewer temporary allocations, and easier JIT specialization. The degree of benefit
depends on the workload, but the architectural direction is straightforward: remove flexibility that the running application no longer needs.

---

## Concrete Bytecode Is Friendly to the JIT

HotSpot optimizes concrete code extremely well. Consider a generated method:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Override
    public User find(long id) {
        return this.cache.get(id, () ->
            super.find(id)
        );
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    override fun find(id: Long): User {
        return this.cache.get(id) {
            super.find(id)
        }
    }
    ```

The bytecode corresponds to normal field access, normal calls, and normal control flow. The JIT can profile those call sites like any other application code.

A highly generic runtime AOP engine may introduce shared invocation abstractions across many unrelated methods. Those paths can also optimize, but they present a more generic structure. Generated code
has a natural specialization advantage: instead of one mechanism supporting every bean, every method, and every interceptor combination, there is a small generated method supporting this exact method
with these exact aspects.

The same reason makes code generation attractive for serializers, database mappers, HTTP routing, and dependency injection. If the structure is knowable ahead of time, specialization can turn a
general problem into straightforward code.

Kora applies that principle consistently.

---


Generic runtime interception can create short-lived objects, especially if every invocation is represented by an object containing the method, arguments, target, and continuation state. Modern garbage
collectors handle short-lived allocation very well, so this should not be exaggerated, but eliminating avoidable allocation is still useful on high-throughput paths.

Generated interception can keep method arguments as normal locals:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Override
    public Result update(long id, UpdateRequest request) {
        validator.validate(request);
        return super.update(id, request);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    override fun update(id: Long, request: UpdateRequest): Result {
        validator.validate(request)
        return super.update(id, request)
    }
    ```

rather than conceptually erasing them into a universal representation:

===! ":fontawesome-brands-java: `Java`"

    ```java
    Object[] args = {id, request};
    InvocationContext context =
        new InvocationContext(method, args, target);
    return chain.proceed(context);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val args = arrayOf<Any>(id, request)
    val context =
        InvocationContext(method, args, target)
    return chain.proceed(context)
    ```

Not every runtime framework literally allocates those exact objects, but the architectural distinction remains. A compile-time generator has no requirement to erase a typed call into a universal
invocation model. It can preserve the original signature through the interception layer.

Typed directness helps performance and debuggability at the same time.

---


A framework can have a very fast steady-state proxy call and still impose cost elsewhere. Proxy discovery and construction happen during startup. Reflection metadata may increase initialization work.
Runtime-generated classes need to be created and loaded. Interceptor metadata caches consume memory. Generic infrastructure increases warm-up surface.

Kora's compile-time AOP reduces the amount of AOP-specific decision-making performed by the live process. That aligns with the framework's broader startup philosophy: prepare the application structure
before production starts.

For cloud services, startup is not only a developer convenience. Instances start during deployments, autoscaling, node replacement, spot recovery, integration tests, local development, disaster
recovery, and scale-from-zero workflows. Even small pieces of runtime discovery multiply across a fleet.

Compile-time AOP is one part of reducing that repeated cost.

---


It would be misleading to claim that compile-time AOP automatically makes every Kora service faster than every runtime-proxy service. Real performance depends on database latency, serialization,
network calls, connection pools, logging, telemetry, concurrency limits, GC behavior, and many other factors.

The stronger argument is architectural. Compile-time AOP removes categories of runtime work that do not need to remain dynamic. That lowers the framework-overhead floor. If the business operation
takes milliseconds, the difference may be invisible. If the method is extremely cheap and called millions of times, interception overhead may matter. If startup is critical, eliminating runtime proxy
planning matters. If memory is constrained, reducing metadata and generic infrastructure matters.

This is why Kora's AOP design should be understood as part of a performance budget rather than as a one-call benchmark story.


---

## Debuggability: Open the Generated Class

One of the strongest practical properties of Kora's AOP design is that developers can inspect the generated source. Kora's documentation explicitly encourages looking at generated AOP proxy classes
for features such as validation, caching, and resilience. That recommendation reveals an important framework philosophy: generated code is not treated as an embarrassing implementation detail that
users should never see. It is part of the debugging surface.

If a retry annotation behaves unexpectedly, the developer can inspect the generated override. If cache invalidation happens in the wrong place, the generated method shows where it is performed. If
multiple resilience annotations interact strangely, the generated proxy exposes their nesting. If an injected dependency looks surprising, the generated constructor can reveal what the proxy actually
requires.

The generated code acts as an executable explanation of what the framework understood from the annotations.

This is a major difference from a runtime proxy model, where the effective execution path may exist only as the combination of runtime metadata, proxy type, interceptor registration, ordering rules,
and target resolution.

---


A breakpoint on a runtime-proxied service can enter a generated class that is not part of the source tree and then move through generic framework infrastructure:

```text
proxy invocation handler
framework method interceptor
interceptor chain
method invocation abstraction
reflection / method handle
actual target
```

Modern IDEs can handle these stacks, and mature frameworks provide good tooling. The problem is not that debugging is impossible. The problem is that understanding one intercepted method can require
understanding the framework's generic runtime engine.

The debugging question becomes:

> What is the framework doing to my method at runtime?

With generated source, the question is different:

> What code did the framework generate for my method?

That is a significant shift. The first requires reconstructing dynamic behavior. The second gives the developer a concrete artifact.

---

## Generated Code Narrows the Semantic Gap

The semantic gap is the distance between what source code appears to mean and what the runtime actually does. A plain Java call has a relatively small semantic gap:

===! ":fontawesome-brands-java: `Java`"

    ```java
    service.load(id);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    service.load(id)
    ```

An AOP framework necessarily adds behavior that is not written inside `load()`. In a highly dynamic model, the real path may be:

```text
service.load(id)
  -> proxy
  -> security interceptor
  -> transaction interceptor
  -> metrics interceptor
  -> retry interceptor
  -> target.load(id)
```

Compile-time generation cannot eliminate the semantic gap because declarative AOP intentionally adds behavior. What it can do is materialize the missing layer as source.

Conceptually:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Override
    public User load(long id) {
        metrics.start();
        try {
            return transactionManager.inTransaction(
                () -> retry.execute(
                    () -> super.load(id)
                )
            );
        } finally {
            metrics.stop();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    override fun load(id: Long): User {
        metrics.start()
        try {
            return transactionManager.inTransaction {
                retry.execute {
                    super.load(id)
                }
            }
        } finally {
            metrics.stop()
        }
    }
    ```

Now there is a bridge between annotation and runtime behavior. The business class remains concise, while the generated class explains the actual execution path.

That is a strong compromise between declarative ergonomics and operational transparency.

---


Generated AOP does not guarantee beautiful stack traces. Aspects introduce additional frames because additional code really executes. Retry, tracing, caching, validation, and transaction components
appear in the stack because they are part of the call path.

The important difference is that generated proxy frames can map to real generated classes and methods. A stack can conceptually contain:

```text
$UserService__AopProxy.load
RetryImpl.execute
UserService.load
```

This is easier to connect to application code than a generic sequence of invocation handlers whose relationship to the intercepted method must be reconstructed. If generated sources are available to
the IDE, developers can step through those methods like ordinary code.

The same helps when analyzing production stack traces after the fact. The generated class name communicates that the AOP layer is involved, and the method name identifies the intercepted operation.

Transparency does not mean the framework disappears. It means the framework leaves understandable evidence of what it is doing.

---


The same properties that help human debugging also help static analysis and AI coding tools. A dynamic framework can require a tool to infer behavior from several layers at once:

- source annotations;
- framework conventions;
- runtime proxy rules;
- interceptor ordering;
- container configuration;
- generated runtime bytecode;
- metadata registries.

A compile-time framework exposes much more of that behavior as source. A tool investigating a problem can inspect the business method, generated proxy, generated application graph, and the direct
dependencies used by the aspect. It can follow an actual code path instead of guessing what runtime machinery will be assembled.

This matters in large codebases where automated tools increasingly perform refactoring, diagnostics, code review, test generation, and incident analysis. Static and explicit structures are easier to
reason about than behavior that exists only after application startup.

---

## Runtime Magic vs Compile-Time Machinery

It is tempting to summarize compile-time code generation as "no magic." That captures the developer experience but is technically imprecise. Annotation processing is machinery. KSP is machinery.
Aspect resolution is machinery. Source generation is machinery. Graph generation is machinery.

The meaningful distinction is:

```text
runtime hidden mechanism
vs
compile-time materialized mechanism
```

Kora still performs sophisticated framework work. The difference is that much of the result becomes source code before the application runs. The framework implementation may be complex while the
generated runtime model remains simple.

Complexity has not vanished. It has been moved to a phase where it can run once, produce diagnostics, generate typed code, and leave a smaller production runtime behind.

---


Some developers hear "generated subclass" and conclude that this is not really AOP, only code generation. That distinction is not useful. AOP is about modularizing cross-cutting concerns and applying
behavior at defined join points. Method execution is the join point here. Annotations define where aspects apply. Generated overrides weave behavior around those method executions.

Whether the weaving happens during source generation, compilation, class loading, container startup, or runtime invocation changes the implementation strategy, not the architectural purpose.

Kora's model is properly described as compile-time AOP because aspect application is determined and materialized while the program is being built rather than dynamically assembled during normal
application execution.

---

## Compile-Time AOP vs Bytecode Weaving

Generated subclasses are also different from compile-time bytecode weaving. A bytecode weaver can modify the original class itself. Conceptually:

```text
Original method bytecode:

load()
  -> business code
```

becomes:

```text
Woven method bytecode:

load()
  -> aspect before
  -> business code
  -> aspect after
```

That can intercept cases subclassing cannot, because the original method body itself is changed. Depending on the weaving technology, it may be able to affect private methods, constructors, field
access, and other join points.

The trade-off is that the class no longer behaves exactly like the source file suggests unless the developer understands the weaving process. Debugging and build tooling can become more complicated
because bytecode is transformed after ordinary source compilation.

Kora's subclass generation is narrower. The original class is not rewritten. A separate generated class extends it and overrides interceptable methods. That limitation contributes directly to
transparency.

The framework gives up some theoretical interception power in exchange for a model that is easier to inspect and explain.

---


Java agents can instrument classes at load time or redefine them while the application is running. They are powerful tools for profilers, observability platforms, debugging, and some AOP systems. But
an agent introduces another runtime transformation stage:

```text
class file
  |
  v
class loader
  |
  v
agent transformer
  |
  v
modified bytecode
  |
  v
JVM
```

For infrastructure that genuinely must attach to arbitrary applications without source changes, this is an excellent capability. For framework-owned concerns whose structure is already known at build
time, it is often unnecessary complexity.

Kora does not need a runtime agent merely to apply standard framework aspects to managed application methods. That reduces the number of moving pieces between source code and executed code.

The recurring question is simple:

> If the answer can be known at compile time, why postpone it until runtime?

---

## The Cost of Giving Up Runtime Dynamism

Compile-time AOP has trade-offs. A runtime proxy framework can make decisions using information that does not exist during compilation. It can attach interceptors based on runtime plugin discovery,
dynamic registration, deployment environment, or components that are loaded after the main application artifact has been built.

Compile-time generation prefers a more closed-world view of application structure. That is ideal for most backend services, where code and annotations define the component model before deployment. It
is less natural for systems whose primary requirement is runtime extensibility.

Suppose an application loads arbitrary third-party plugins from a directory and applies newly discovered interceptors to types that did not exist during the main build. Runtime proxying or
instrumentation may fit that problem better.

Kora optimizes for a different environment:

```text
known service code
known framework contracts
known annotations
known application graph
known deployment artifact
```

For ordinary microservices and backend applications, that is usually the actual operating model.

---


Most services do not invent new business-service classes after deployment. Their controllers are known. Repositories are known. Transaction boundaries are known. Retry and cache annotations are known.
Validation annotations are known. The artifact is built in CI and deployed immutably.

That environment strongly favors compile-time decisions. If the service is redeployed whenever its code changes anyway, requiring a rebuild to change AOP structure is not a meaningful limitation. The
deployment unit is already the compiled application.

Kora therefore aligns framework architecture with the operational reality of modern immutable deployments. The service is not a general-purpose runtime container. It is a specific program, and a
specific program benefits from specific generated code.

---


Java developers often prefer final classes because finality communicates that inheritance is not part of the class's public design. Kotlin goes further and makes classes final by default.
Subclass-based AOP creates tension with that principle because intercepted components must allow framework-generated inheritance.

This is a real trade-off. The component is open not because application developers are expected to subclass it manually, but because code generation uses inheritance as an implementation mechanism.

Alternative interception mechanisms have their own costs. Runtime subclass proxies may still require non-final methods. Instrumentation rewrites behavior invisibly. Interface proxies require
interface-oriented boundaries. Wrappers introduce separate delegate instances and can change self-invocation behavior.

No AOP implementation is free. Kora's choice has the advantage that the constraint is explicit, statically checkable, and easy to explain.

---


A natural question is why compile-time AOP does not always avoid inheritance and generate wrappers. For example:

===! ":fontawesome-brands-java: `Java`"

    ```java
    final class UserServiceAopWrapper
        implements UserServiceApi {

        private final UserService delegate;

        @Override
        public User load(long id) {
            return retry.execute(
                () -> delegate.load(id)
            );
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class UserServiceAopWrapper(
        private val delegate: UserService
    ) : UserServiceApi {

        override fun load(id: Long): User {
            return retry.execute {
                delegate.load(id)
            }
        }
    }
    ```

This works well when the application is entirely designed around interfaces. But wrappers have trade-offs. They do not automatically preserve the concrete-class API. They introduce a separate delegate
instance. Internal calls happen on the delegate and do not travel back through the wrapper, recreating the classic self-invocation problem. Injection by concrete type can become less natural, and
every exposed method must be forwarded.

Subclassing preserves more of the original object model. Most importantly for self invocation, inherited methods execute on the same generated subclass instance that contains the interception
overrides.

That gives subclass-based AOP a particularly coherent dispatch model.

---


Compile-time subclass AOP does not make interfaces irrelevant. Interfaces remain valuable architectural boundaries for services, clients, repositories, and testing. They separate contracts from
implementations and reduce coupling.

What should be separated conceptually is:

```text
interface-based architecture
```

from:

```text
JDK dynamic-proxy implementation
```

A service can expose an interface while Kora still generates concrete implementation or proxy classes at compile time. Likewise, a repository interface can act as a compile-time code-generation
contract rather than something implemented through a runtime invocation handler.

This is a recurring Kora pattern: keep familiar Java abstractions while avoiding unnecessary runtime interpretation of those abstractions.

---

## Example: Validation

Validation is a useful example because the semantics are straightforward.

Business code:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class RegistrationService {

        @Validate
        public User register(CreateUserRequest request) {
            return createUser(request);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    open class RegistrationService {

        @Validate
        open fun register(request: CreateUserRequest): User {
            return createUser(request)
        }
    }
    ```

The conceptual generated path is:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Override
    public User register(CreateUserRequest request) {
        requestValidator.validate(request);
        return super.register(request);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    override fun register(request: CreateUserRequest): User {
        requestValidator.validate(request)
        return super.register(request)
    }
    ```

The AOP layer knows the method parameters statically. It can generate typed calls. If the annotation is applied to an unsupported shape, the build can fail. If the required validator dependency cannot
be resolved, the generated graph can expose that during compilation.

When validation fails at runtime, it then fails because the input violates a validation rule, not because the framework discovered too late that it could not construct the validation mechanism.

That cleanly separates structural framework errors from actual business-input errors.

---

## Example: Caching

Caching demonstrates how compile-time AOP can encode branching logic.

Business method:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Cacheable("users")
    public User loadUser(long id) {
        return repository.findById(id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Cacheable("users")
    open fun loadUser(id: Long): User {
        return repository.findById(id)
    }
    ```

The generated behavior conceptually resembles:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Override
    public User loadUser(long id) {
        var cached = userCache.get(id);

        if (cached != null) {
            return cached;
        }

        var value = super.loadUser(id);
        userCache.put(id, value);
        return value;
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    override fun loadUser(id: Long): User {
        val cached = userCache.get(id)

        if (cached != null) {
            return cached
        }

        val value = super.loadUser(id)
        userCache.put(id, value)
        return value
    }
    ```

Real cache code must account for nullability, key composition, backend semantics, telemetry, and concurrency, but the structural point is the same: the method-specific cache flow can be emitted
directly.

Now consider invalidation:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @CacheInvalidate("users")
    public void updateUser(
        long id,
        UpdateUserRequest request
    ) {
        repository.update(id, request);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @CacheInvalidate("users")
    open fun updateUser(
        id: Long,
        request: UpdateUserRequest
    ) {
        repository.update(id, request)
    }
    ```

The generated method can express exactly whether invalidation happens before or after `super.updateUser()`, whether it occurs only on success, and which cache/key is used. Those details are visible in
code rather than hidden in generic interceptor state.

---

## Example: Retry and Circuit Breaker

Resilience aspects are more complex because the control flow is more complex. A retry may involve attempt counters, backoff, exception classification, delays, cancellation, and metrics. A circuit
breaker has state transitions, permissions, success/failure recording, half-open behavior, and possibly fallback.

The business method should not contain all of that:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Retry("inventory")
    @CircuitBreaker("inventory")
    public Inventory loadInventory(String sku) {
        return inventoryClient.load(sku);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Retry("inventory")
    @CircuitBreaker("inventory")
    open fun loadInventory(sku: String): Inventory {
        return inventoryClient.load(sku)
    }
    ```

Compile-time AOP can generate the glue that connects the method to reusable resilience components:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Override
    public Inventory loadInventory(String sku) {
        return circuitBreaker.execute(() ->
            retry.execute(() ->
                super.loadInventory(sku)
            )
        );
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    override fun loadInventory(sku: String): Inventory {
        return circuitBreaker.execute {
            retry.execute {
                super.loadInventory(sku)
            }
        }
    }
    ```

The resilience components themselves remain runtime objects because their state is genuinely dynamic. The circuit breaker's current state cannot be compiled away. Retry decisions depend on actual
failures. Timeouts depend on real time.

Compile-time AOP does not move runtime state into the compiler. It moves static interception structure into the compiler.

---


This division is fundamental:

```text
Compile time:
- which method is intercepted
- which aspect applies
- how aspects are ordered
- which dependencies implement them
- whether the method can be overridden
- how the proxy is wired into the graph

Runtime:
- cache contents
- circuit-breaker state
- retry attempt outcome
- current transaction
- current trace/span
- validation input
- security principal
```

The compiler does not need to know whether the next remote call will fail. It only needs to know which retry component should receive the call. It does not need to know whether a cache key will be
present. It only needs to generate the lookup path.

Kora is not "compile-time everything." It is compile time for things that can actually be decided at compile time.

---

## Example: Transactions

Transactions are an archetypal AOP concern because they surround a business operation.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Transactional
    public void transfer(
        AccountId from,
        AccountId to,
        BigDecimal amount
    ) {
        debit(from, amount);
        credit(to, amount);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Transactional
    open fun transfer(
        from: AccountId,
        to: AccountId,
        amount: BigDecimal
    ) {
        debit(from, amount)
        credit(to, amount)
    }
    ```

Conceptually, the generated method can be understood as:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Override
    public void transfer(
        AccountId from,
        AccountId to,
        BigDecimal amount
    ) {
        transactionManager.inTransaction(() -> {
            super.transfer(from, to, amount);
            return null;
        });
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    override fun transfer(
        from: AccountId,
        to: AccountId,
        amount: BigDecimal
    ) {
        transactionManager.inTransaction {
            super.transfer(from, to, amount)
            null
        }
    }
    ```

The important point is not the exact transaction API. It is that the transaction boundary becomes a concrete call in generated code.

When debugging a transaction problem, the generated override can answer direct questions: where does the transaction start, which manager is used, which original method call is inside the boundary,
and whether another aspect sits inside or outside the transaction.

A declarative transaction annotation is valuable because the boilerplate is repetitive. Compile-time AOP preserves the convenience without requiring the transaction boundary to exist only as runtime
proxy metadata.

---

## Aspect Ordering Becomes Architecture

As soon as multiple aspects are applied, ordering is no longer a framework implementation detail. It is application architecture.

Consider:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Retry("orders")
    @Transactional
    public void process(Order order) {
        // ...
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Retry("orders")
    @Transactional
    open fun process(order: Order) {
        // ...
    }
    ```

Two possible structures are:

```text
transaction
  |
  +--> retry attempt 1
  +--> retry attempt 2
  +--> retry attempt 3
```

and:

```text
retry
  |
  +--> transaction attempt 1
  +--> transaction attempt 2
  +--> transaction attempt 3
```

Those can produce very different database semantics. Similar questions arise for timeout and retry, cache and transaction, tracing and retry, validation and caching, or circuit breaker and fallback.

A good AOP system must define deterministic ordering. A compile-time system gains an additional advantage: once the order is resolved, the generated source exposes the answer. Generated code therefore
becomes a way to audit aspect composition.

---


Framework upgrades are often difficult because annotations stay unchanged while behavior changes underneath them. Imagine a method that remains:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Cacheable("users")
    @Retry("users")
    public User load(long id) {
        // ...
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Cacheable("users")
    @Retry("users")
    open fun load(id: Long): User {
        // ...
    }
    ```

If the framework's aspect ordering changes, the business source might show no diff. Generated source can still reveal a change from:

```text
cache
  -> retry
      -> method
```

to:

```text
retry
  -> cache
      -> method
```

Teams do not need to commit all generated sources to version control to benefit from this. Generated output can be inspected during migrations, captured in CI artifacts, or compared in focused
regression tests.

The important point is that the final interception structure exists as text that can be compared.

---

## Testing the Raw Class vs Testing the Generated Component

AOP complicates testing whenever a unit test directly constructs a service:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var service = new UserService(repository);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val service = UserService(repository)
    ```

That instance is the raw class, not the generated AOP subclass. If the test expects retry, validation, caching, transaction, or security behavior that Kora applies through AOP, manual construction
bypasses the aspect layer.

This is not unique to Kora. Runtime-proxy frameworks have the same distinction between testing the raw target and testing a managed/proxied component.

Kora's generated model makes the two layers conceptually clear:

```text
UserService
    = business implementation

$UserService__AopProxy
    = business implementation + generated aspects
```

A pure unit test can intentionally exercise the first. A component or integration test can intentionally exercise the second through the Kora application graph.

That distinction helps teams write tests that are explicit about what they verify instead of accidentally depending on container behavior.

---


Suppose a refactoring makes an intercepted Java class final or removes `open` from an intercepted Kotlin method. In a runtime model, the problem may appear only when a test starts the relevant
application context. If no test creates that configuration, the issue can travel even farther.

In a compile-time model, the processor sees that the required subclass or override cannot be generated. The build fails before packaging.

This is powerful because compilation is usually the earliest universal stage in CI. Even teams with imperfect integration-test coverage generally compile every changed module. Compile-time AOP
therefore turns structural framework correctness into something enforced by the most fundamental build step.

That reduces dependence on "did we happen to run the test that starts this component?"

---


The economics are straightforward. A compile error is usually seen immediately by the developer who introduced it. A startup error may be seen by a test runner, CI system, staging deployment, or
operations team. A production behavior error may be seen by customers.

Every later stage adds elapsed time, infrastructure, logs, people, uncertainty, and rollback cost. Moving an error from runtime to compilation therefore has multiplicative value.

This is why compile-time validation should be treated as a reliability feature rather than only as developer ergonomics. Kora's AOP design creates opportunities to move structural misuse into the
cheapest possible failure domain.

---


When framework errors appear quickly and precisely, experimentation becomes cheaper. A developer can add an annotation, compile, read the diagnostic, fix the method shape, and continue. If the same
mistake requires packaging, starting the whole application, waiting for the container, and interpreting a proxy-construction stack trace, the feedback loop is longer and more cognitively expensive.

Backend development consists of hundreds of such loops. Small delays compound.

Compile-time frameworks use the compiler as an interactive design partner. The compiler is not only checking Java syntax; it is checking whether the framework can actually build the requested
application structure.

AOP is one of the places where that feedback is particularly valuable because proxy constraints are otherwise easy to discover late.

---

## Build-Time Cost Is Real

Moving work to compile time does not make work disappear. Annotation processors consume CPU. KSP processing consumes CPU. Generated source must be compiled. Large applications can generate many files.
Processor design can affect incremental builds.

The trade can be described as:

```text
more work once per build
for
less structural work on every process startup and invocation
```

Whether that trade is worthwhile depends on how well generation is engineered. For backend services, it often is. A CI build happens once per artifact. The artifact may then start dozens, hundreds, or
thousands of times across replicas and environments, and its runtime paths may execute billions of times.

The build pipeline is also a safer place to spend CPU than the latency-sensitive production process.

---


A compile-time framework cannot dismiss build performance. Developer productivity depends heavily on incremental compilation. If changing one method regenerates an unnecessarily large part of the
application, the editing loop can become unpleasant even if production performance is excellent.

Good compile-time framework engineering therefore requires deterministic generation, sensible dependency tracking, effective build caching, and limited invalidation where possible. Kora's compile-time
approach should be evaluated not only by startup and throughput but also by clean-build and cached-build behavior.

Framework cost has not disappeared. It has moved, and the new location still needs to be optimized.

---


A generated override preserves the original method signature:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Override
    public User load(long id) {
        // ...
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    override fun load(id: Long): User {
        // ...
    }
    ```

The compiler retains full type information. The generated code cannot accidentally pass a `String` where a `long` is expected. Return values remain typed. Generic bounds must compile. Checked
exceptions must obey Java rules. Aspect dependencies can expose typed APIs.

Compare that with a universal invocation shape:

===! ":fontawesome-brands-java: `Java`"

    ```java
    Object invoke(
        Object proxy,
        Method method,
        Object[] args
    )
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun invoke(
        proxy: Any,
        method: Method,
        args: Array<Any>
    ): Any
    ```

Such an API deliberately erases method-specific types so it can represent every invocation. Framework code must then reconstruct meaning through metadata, casts, conventions, or generated helpers.

Compile-time generation can stay in the typed world longer. This is not only a performance property. It delegates more correctness checking to the language compiler.

---


A generic proxy API often views parameters as an `Object[]`. That representation is flexible but loses structure. Primitives may need boxing. Parameter identity moves into metadata. The runtime sees a
generic collection instead of individual strongly typed locals.

Generated code can preserve:

===! ":fontawesome-brands-java: `Java`"

    ```java
    long id
    UpdateRequest request
    boolean force
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    id: Long
    request: UpdateRequest
    force: Boolean
    ```

as exactly those variables.

This mirrors generated serializers and mappers that access fields directly instead of reflecting over them at runtime. When the structure is static, preserving that structure is usually better than
erasing it and rediscovering it later.

---


Cross-cutting behavior is sometimes described as though it were ambient magic. In reality, every aspect depends on concrete things.

Caching depends on a cache. Validation depends on validators. Transactions depend on transaction infrastructure. Resilience depends on policy and state objects. Telemetry depends on meters, tracers,
and loggers. Security depends on authentication and authorization state.

Compile-time AOP encourages framework authors and application developers to think about these as normal dependencies. A transaction annotation means generated code will call a transaction component. A
retry annotation means generated code will call resilience infrastructure. Once those relationships are represented as fields, constructor parameters, and method calls, AOP becomes much easier to
reason about.

The application graph can then validate and wire those dependencies like any others.

---

## What the Developer Should Inspect

When debugging Kora AOP, four layers are especially useful.

First, inspect the handwritten business class. Confirm the annotation, method signature, visibility, and whether the class/method can be overridden.

Second, inspect the generated `$...__AopProxy` class and find the override for the method. This reveals the actual generated aspect chain.

Third, follow the fields or constructor parameters used by that generated method. These identify the concrete retry, cache, validation, transaction, security, or telemetry components involved.

Fourth, if the wrong component seems to be wired, inspect the generated application graph to see how the proxy itself is constructed and injected.

This path is remarkably concrete:

```text
business method
  ->
generated override
  ->
aspect dependency
  ->
generated graph wiring
```

It turns framework debugging into code navigation.

---


One of the hardest properties of large runtime frameworks is non-local reasoning. A method behaves differently because of a global registry, a configuration file, classpath scanning, proxy mode,
auto-configuration, or an ordering rule defined elsewhere.

Kora's generated AOP reduces some of that distance. To understand one intercepted method, a developer can often look at the method, its annotations, the generated override, and its direct
dependencies.

That is local reasoning.

The whole framework still has configuration and shared infrastructure, but the critical interception path is materialized nearby as code. Local reasoning scales better across teams because engineers
can understand one service boundary without reconstructing the entire runtime container state.

---


Framework bugs happen. A generator may mishandle a generic signature, annotation propagation, Kotlin override, aspect combination, or edge-case method shape. When the failing behavior is represented
in generated source, a bug report can include that source.

A minimal reproducer can show:

```text
input class
processor version
generated proxy
compiler error or runtime behavior
```

That is often easier to diagnose than a bug that depends on runtime proxy-factory state, classloader behavior, or metadata assembled only after startup.

Generated code turns part of the framework's internal decision into a reproducible text artifact. That helps framework maintainers as much as application developers.

---


Once a framework encourages users to inspect generated code, readability becomes an informal contract. Variable naming matters. Method structure matters. Generated class naming matters. Unnecessary
indirection becomes visible.

That creates healthy pressure. If generated AOP code is absurdly complicated, users notice. If the generated path allocates unnecessary objects, performance engineers can inspect it. If aspect order
is surprising, the nesting is visible.

Transparency therefore acts as a quality mechanism. The generated code is not merely compiler output. It is evidence of what the framework decided.

---


If generated AOP code is readable and fairly straightforward, a reasonable question is: why not write it manually?

Because the value of generation is precisely that humans do not need to maintain repetitive infrastructure. A service with twenty methods and combinations of validation, logging, tracing, caching,
transactions, and retries would accumulate large amounts of wrapper code. Method signatures would need to be synchronized manually. Aspect order could drift. Telemetry could be forgotten. Error
handling could become inconsistent.

Generation gives the application the runtime simplicity of explicit wrappers without imposing the maintenance cost of handwritten wrappers.

The intended division is:

```text
developer writes:
concise declarative intent

compiler creates:
explicit repetitive implementation

runtime executes:
ordinary code
```

Humans keep the abstraction. The JVM receives the specialized implementation.

---


Good generated infrastructure should be boring. It should look like something a competent developer could have written manually:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Override
    public Result execute(Request request) {
        validator.validate(request);
        return retry.execute(() ->
            super.execute(request)
        );
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    override fun execute(request: Request): Result {
        validator.validate(request)
        return retry.execute {
            super.execute(request)
        }
    }
    ```

Boring code is valuable because it is predictable. It does not require a mental model of a mini-language interpreter. It does not hide control flow in a runtime metadata graph. It does not make
developers learn a second execution model alongside Java.

Kora's emphasis on human-readable generated source is therefore not cosmetic. Readability is a design constraint on the framework architecture.

---

## Compile-Time AOP and Native Images

Static, reflection-light infrastructure generally fits ahead-of-time compilation better than highly dynamic runtime machinery. Native-image systems need to understand which classes, methods,
constructors, resources, and reflective accesses remain reachable. Dynamic proxies and reflection can require extra metadata so the image builder does not remove code needed later.

Generated AOP classes are ordinary classes. Their constructor dependencies are explicit. Their method calls are visible in bytecode. Their relationship to the application graph is static.

That makes them easier for static analysis to understand. It does not mean every Kora application becomes trivial to compile natively—libraries can still use reflection, resources, native code, or
other dynamic behavior—but compile-time AOP removes one common source of runtime dynamism.

Even on HotSpot, the same static structure benefits startup and transparency.

---


Security is not the headline reason for compile-time AOP, but earlier validation can reduce dangerous misconfiguration. If a security annotation requires an aspect and the aspect cannot be generated,
compilation can fail. If an intercepted method shape is unsupported, the framework can reject it rather than silently running without the intended advice.

This matters because the most dangerous framework failure is not a visible exception. It is a method that appears protected because an annotation is present while the actual execution path bypasses
the security control.

Compile-time validation reduces the space for that mismatch. It cannot prevent bad authorization rules or business-logic vulnerabilities, but it can verify more of the structural attachment of the
security behavior before deployment.

For security controls, failing closed during compilation is an attractive property.

---


AOP can subtly change exception behavior. An interceptor may wrap, translate, retry, suppress, record, or trigger fallback for an exception. Reflective invocation historically also introduced wrappers
such as `InvocationTargetException`, requiring framework code to unwrap the real failure.

Generated direct calls can avoid some incidental exception machinery because `super.method()` is a normal call. Retry and fallback still intentionally change control flow, but the generated source can
show where that happens.

Conceptually:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Override
    public Result call() {
        try {
            return retry.execute(() -> super.call());
        } catch (RemoteSystemException e) {
            return fallback();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    override fun call(): Result {
        try {
            return retry.execute { super.call() }
        } catch (e: RemoteSystemException) {
            return fallback()
        }
    }
    ```

A developer can reason from ordinary Java exception semantics instead of tracing through several generic reflection wrappers.

---


Profilers group CPU samples by methods and classes. Stable generated classes make attribution easier. A hot method such as:

```text
$PricingService__AopProxy.calculate
```

immediately communicates that AOP participates in the path. A flame graph may conceptually look like:

```text
HTTP handler
  UserController
    $OrderService__AopProxy.place
      TransactionManager
        Retry
          OrderService.place
            Repository
```

The generated proxy frame carries application meaning. Generic runtime interceptor stacks can concentrate samples in shared infrastructure used by many unrelated methods, depending on the
implementation and JIT inlining.

Generated specialization naturally preserves more application identity in profiling data.

---


Every runtime subsystem is another thing that can fail after deployment. Dynamic proxy factories can hit classloader edge cases. Runtime class generation can fail. Reflection can interact with module
boundaries. Proxy metadata can be inconsistent. Interceptor lookup can select the wrong path.

By generating and compiling the proxy before deployment, Kora reduces the amount of AOP-specific machinery that must succeed in production. The processor can still have bugs, but those bugs are more
likely to surface during build, code generation, or tests.

A useful operational principle is:

```text
prefer failure in CI over failure in the pod
```

Compile-time AOP embodies that principle.

---


The Java module system strengthened encapsulation around reflective access. Frameworks that depend heavily on reflection sometimes require `opens` directives so they can access members at runtime.

Generated subclass code operates through normal Java access and inheritance rules. That does not eliminate all module-system concerns, but it aligns them with compilation. If generated source cannot
legally access a type or member, the compiler can say so.

This is preferable to discovering an illegal reflective-access problem after the application has already started.

---


Compile-time interception does not prevent runtime configuration. The generated proxy can depend on a retry component whose attempts and delay come from configuration. A generated cache aspect can use
a cache whose size or expiration differs between environments. A transaction aspect can use runtime connection pools and database settings.

Build time can decide:

```text
this method uses retry policy "catalog"
```

while runtime configuration decides:

```text
maxAttempts = 4
backoff = 50 ms
```

Compile-time generation fixes topology, not every operational value. That balance is important: static structure, dynamic tuning.

---


Because Kora puts AOP behavior in a generated subclass rather than rewriting every handwritten method body, the original class remains recognizable as business code. A unit test can instantiate it
directly. A developer can inspect domain logic without reading framework plumbing. A migration tool can sometimes reuse it without the aspect layer if that is intentional.

This separation is valuable:

```text
handwritten business code
vs
generated infrastructure code
```

Both are readable. Neither pretends to be the other.

The trade-off is that the handwritten class is not the whole runtime story when annotations are present. The generated subclass completes that story.

---


Suppose a service normally managed by Kora has AOP annotations. If production code manually does:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var service = new UserService(...);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val service = UserService(...)
    ```

then that instance is the raw class, not the generated proxy subclass. Its methods execute without generated AOP behavior.

This rule is straightforward:

```text
Kora graph instance:
generated subclass -> aspects active

manual raw instance:
base class -> aspects absent
```

For unit tests, manual construction can be intentional. For production code, components that rely on framework behavior should normally be constructed through the application graph.

---

## AOP Belongs at Clear Component Boundaries

Compile-time subclass semantics make internal interception more coherent than classic external proxies, but that does not mean every helper method should become an AOP join point. Cross-cutting
concerns are easiest to reason about at meaningful component boundaries.

For example:

```text
Controller
  ->
Service
  ->
Repository
```

A transaction or resilience boundary on a service operation is understandable. A retry around an external client call is understandable. A cache around a read service is understandable. Dozens of tiny
annotated internal helpers can still create a fragmented control model even if interception technically works.

Compile-time AOP improves the mechanism. Good architecture still determines where the mechanism belongs.

---


Not every concern belongs in an aspect. AOP is strongest for behavior that is genuinely orthogonal and reusable: transactions, standard validation, resilience policies, caching, authorization checks,
telemetry, and standardized logging.

Business workflows whose ordering defines domain semantics should generally remain explicit. For example:

```text
reserve inventory
charge payment
publish event
send notification
```

is usually clearer as ordinary orchestration code than as four custom annotations whose ordering determines business behavior.

Compile-time generation makes AOP safer and more transparent, but it does not change the fundamental design rule: use AOP to remove infrastructure boilerplate, not to hide the domain.

---


A method such as:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Audit
    @Measure
    @Secure
    @Validate
    @Retry
    @CircuitBreaker
    @Timeout
    @Cacheable
    @Transactional
    public Result execute(...) {
        // ...
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Audit
    @Measure
    @Secure
    @Validate
    @Retry
    @CircuitBreaker
    @Timeout
    @Cacheable
    @Transactional
    open fun execute(...): Result {
        // ...
    }
    ```

may be technically valid yet difficult to reason about. Even if generated code makes the result inspectable, the source declaration carries a large semantic load.

Compile-time AOP is not a license to maximize annotation density. Annotations should represent standardized infrastructure policies with clear semantics. When behavior becomes unique to one workflow,
ordinary code is usually better.

Generated transparency helps identify the boundary because developers can see how much behavior is actually attached to a seemingly small method.

---


If multiple aspects can appear on one method, their composition rules are effectively part of the framework's public API. Developers need answers to questions such as:

```text
Does validation run before retry?
Does cache run inside or outside transaction?
Does tracing include cache hits?
Does logging record every retry attempt or one logical call?
Does timeout wrap retry or each attempt?
Does fallback execute inside the circuit breaker?
```

These are not implementation details. They change production behavior.

Compile-time AOP gives Kora a particularly good way to make composition deterministic and inspectable. Applications should still test critical combinations, while generated source provides the
implementation-level explanation when something behaves unexpectedly.


---


Generated AOP also improves predictability. Dynamic systems can have phase changes during early execution: first-use metadata initialization, proxy creation, reflective accessor resolution,
interceptor cache population, or runtime class generation. Generated code starts from a more stable structural shape.

There is still JIT warm-up. There are still lazy libraries. Database pools still establish connections. Caches still begin cold. Remote systems still have real latency. Compile-time AOP does not
abolish warm-up. It removes one category of framework-specific late binding from that warm-up surface.

For latency-sensitive services, this can matter more than a tiny steady-state throughput gain. Tail latency punishes unexpected initialization work more severely than average latency does. Reducing
runtime structural discovery makes the application's early-life behavior easier to reason about.

---


Operations teams rarely care whether a framework uses proxies in an abstract design-pattern sense. They care about startup time, memory, CPU, latency, failure modes, stack traces, and diagnosability.

Compile-time AOP contributes to all of those dimensions by removing runtime work where possible. The effect of one proxy is small. The effect across validation, caching, resilience, transactions,
security, logging, and other framework concerns can be meaningful when multiplied across every component and every service instance.

This is why Kora's AOP architecture should be understood in the context of the whole framework. AOP follows the same pattern as compile-time dependency injection, repositories, mappings, and other
generated infrastructure:

```text
move structure into compile time
keep runtime direct
```

When many subsystems follow the same rule, the benefits reinforce each other.

---


Kora's annotation processors are not trivial. AOP generation itself is not trivial. Correctly handling Java and Kotlin, generic signatures, annotation propagation, multiple aspects, method visibility,
dependencies, and generated source requires substantial framework engineering.

That does not contradict the goal of a simpler application runtime.

Framework developers absorb complexity so that application developers and production processes do not have to. The framework can contain sophisticated compiler machinery while producing
straightforward generated classes.

A framework is not simple because its own source code is small. It is simple for users when it produces predictable programs with understandable behavior. Compile-time AOP deliberately concentrates
complexity in the toolchain to reduce complexity in the deployed service.

---


Static validation also gives framework maintainers a cleaner way to evolve APIs. If an annotation combination becomes unsupported, the processor can reject it with a targeted error. If an aspect
requires a new dependency, application-graph resolution can expose missing wiring. If a method return type no longer satisfies an aspect contract, compilation can identify the exact method.

Without compile-time validation, incompatible behavior is more likely to emerge as a startup exception or runtime mismatch whose connection to a framework upgrade may be less obvious.

Strong diagnostics turn the compiler into a migration assistant. This matters in organizations that maintain many services and need framework upgrades to fail quickly and predictably across a large
codebase.

---


Compiler terminology provides a precise mental model for Kora AOP. The developer writes a high-level construct:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Retry("catalog")
    public Product load(...) {
        ...
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Retry("catalog")
    open fun load(...): Product {
        ...
    }
    ```

The framework processor lowers that declaration into a more explicit implementation:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Override
    public Product load(...) {
        return retry.execute(
            () -> super.load(...)
        );
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    override fun load(...): Product {
        return retry.execute {
            super.load(...)
        }
    }
    ```

This resembles compiler lowering. A high-level construct is transformed into lower-level language constructs while preserving intended semantics. The generated form then goes through ordinary
compilation.

Thinking of AOP this way removes much of the mystery. The annotation is input to a transformation. The generated proxy is the lowered representation. The JVM executes that representation.

This model also explains why compile-time errors are natural: if the framework cannot legally lower the declaration into a valid subclass and override, the build should fail.

---


A fair comparison must acknowledge that runtime proxying solved real problems extremely well and still does. It enabled declarative transactions, security, caching, and other infrastructure long
before modern code-generation ecosystems became common. It supports applications with dynamic extension models. It can create interception for types that were not available when the main application
was compiled. Mature proxy frameworks also have extensive tooling and highly optimized implementations.

Kora's argument is not that runtime proxying is fundamentally invalid. It is that the constraints of ordinary modern backend services allow a different trade-off.

When the structure is already known before deployment, Kora prefers to compile that structure into the application. Runtime proxying optimizes for dynamism. Generated compile-time AOP optimizes for
static predictability.

Those are different engineering priorities.

---


Flexibility always has a cost, even when the cost is not primarily CPU. Runtime flexibility requires metadata, indirection, late validation, dynamic type creation, proxy identity rules, invocation
infrastructure, and more possible runtime states.

Those costs buy something valuable: the ability to decide later.

The correct question is therefore not:

> Are runtime proxies bad?

It is:

> Does this service actually need to decide later?

For most Kora components, the answer is no. The developer already decided in source code that the method has `@Retry`, `@Cacheable`, `@Transactional`, or another aspect annotation. The method
signature is fixed. The class is known. The application graph is being compiled. The service is redeployed when those facts change.

Preserving a general-purpose runtime proxy engine provides little benefit when the deployment model is already static.

Compile-time AOP removes flexibility the application did not need.

---


A cold start includes much more than loading the JVM. Frameworks may scan classpaths, inspect annotations, create component definitions, build proxies, resolve interceptor metadata, and initialize
internal registries before the application becomes ready.

Kora's generated AOP means the proxy class is already present. The service does not need to discover at startup that a method is annotated and then decide how to intercept it. The application graph
already knows the generated component type.

AOP is not the only factor in startup, but architectural consistency matters. If dependency injection, mapping, repositories, HTTP bindings, and AOP all avoid repeated runtime discovery, the aggregate
effect can be significant.

This is why compile-time AOP belongs in discussions of readiness and scaling, not only in proxy-call microbenchmarks.

---


Runtime metadata occupies memory. Proxy factories, method descriptors, interceptor-chain descriptions, reflection caches, and container structures may remain reachable for the lifetime of the
application. Generated code also consumes memory when its classes are loaded, so there is no magical zero-cost representation.

The difference is that static program structure can often be represented more directly as bytecode than as a general-purpose runtime data model. A concrete generated method does not need a separate
object saying:

```text
for method M, invoke A -> B -> C
```

because the method body itself encodes that sequence.

Across many components, specialization can reduce the amount of generic runtime metadata necessary to describe the same program. The exact savings depend on implementation and workload, but the
structural advantage is clear.

---


Modern runtime frameworks may use `MethodHandle`, `invokedynamic`, generated bytecode, or other techniques rather than slow reflective invocation. That can make runtime proxy calls very efficient.

The meaningful comparison is therefore not:

```text
reflection
vs
direct call
```

It is:

```text
runtime-resolved interception model
vs
build-resolved interception model
```

A runtime system using excellent bytecode generation is still resolving some application-specific structure after compilation. A compile-time system resolves that structure before deployment.

This stronger argument survives modern proxy implementations and avoids outdated performance folklore.

---


There are two broad categories of failures around an intercepted method.

Structural failures include:

```text
method cannot be overridden
aspect dependency is missing
annotation use is invalid
generated code cannot compile
application graph is inconsistent
```

Operational failures include:

```text
database transaction fails
remote call times out
circuit breaker opens
validation rejects real input
cache backend becomes unavailable
authorization denies access
```

Compile-time AOP tries to eliminate the first category before deployment. Production is then left primarily with failures that genuinely depend on runtime state.

That is a strong reliability property. The system does not pretend runtime uncertainty can be eliminated; it removes structural uncertainty that never needed to reach runtime in the first place.

---


During an incident, engineers need concrete answers quickly. Suppose latency spikes around a method with retry and timeout behavior. These structures have different worst-case latency:

```text
timeout
  -> retry
      -> remote call
```

and:

```text
retry
  -> timeout
      -> remote call
```

In the first case, one timeout may bound the whole retry sequence. In the second, each attempt may receive its own timeout budget, multiplying total latency.

Generated source can reveal which structure was actually deployed. Incident responders can inspect the concrete proxy instead of reconstructing version-specific runtime ordering rules from memory.

Under operational pressure, static evidence is valuable.

---


A generated proxy is an ordinary compile-time type. It has a deterministic superclass, concrete fields, a constructor, overridden methods, and bytecode produced by the normal compiler.

That matters for tools. Static analyzers can inspect it. Profilers can report it. Stack traces can name it. Build systems can cache its compilation. IDEs can navigate it when generated sources are
configured correctly. A decompiler can recover it from the built artifact.

Runtime-generated proxies also have classes at execution time, but those classes may not exist in the deployment artifact and can be harder to connect back to source.

Kora intentionally preserves that connection.

---


With runtime proxy generation, an artifact can contain the application class and the framework engine while the final proxy type comes into existence only after startup. Static inspection of the JAR
therefore does not necessarily show the full runtime structure.

With Kora compile-time AOP, the artifact contains more of the final answer:

```text
application class
generated AOP proxy
generated application wiring
runtime aspect implementations
```

This helps reproducibility, debugging, static analysis, security scanning, ahead-of-time compilation, and production artifact inspection.

The deployment unit is closer to the actual program that will execute.

---


Compile-time AOP becomes especially powerful when paired with compile-time dependency injection. The two static mechanisms reinforce each other:

```text
AOP processing
  ->
generated proxy type

DI graph processing
  ->
generated construction and wiring
```

The proxy's collaborators become graph edges. The graph can be checked. The generated proxy can be constructed through ordinary generated wiring. There is no need for a second runtime phase that says:

```text
"We already created the bean; now determine whether we should replace it with a proxy."
```

The proxied/generated type can already be the component the graph understands.

This avoids much of the conceptual split between target object, proxy factory, proxy instance, interceptor chain, and exposed bean.

---


Runtime proxy systems can create identity surprises. `getClass()` may reveal an unexpected generated type. Interface proxies may not be castable to the concrete implementation. Equality or exact-class
checks can behave differently. Annotations on implementation methods may interact differently with interface-based proxying.

A generated subclass is still a different concrete class, so exact `getClass()` assumptions remain a bad idea. But the subtype relationship is natural:

```text
$UserService__AopProxy
        is a
UserService
```

The object model stays close to ordinary inheritance. That reduces some of the friction that comes from proxy and target being conceptually separate objects.

---


Imagine a developer reports that `@Retry` is present but no retry occurs. In a traditional runtime proxy framework, the debugging checklist can include:

```text
Is the object container-managed?
Was a proxy created?
Which proxy strategy is active?
Is the caller holding the proxy or raw target?
Is the method interceptable?
Is the annotation visible where the proxy expects it?
Is self invocation bypassing the proxy?
Is the interceptor registered?
Is the policy resolved?
```

With compile-time AOP, several of those questions move earlier. If the class cannot be proxied, compilation should fail. If the generated method exists, the developer can open it and see whether retry
logic is present.

The runtime problem becomes narrower:

```text
Was the generated component injected?
Which retry object was injected?
What did that retry object observe at runtime?
```

Earlier validation reduces the dimensionality of production debugging.

---


Suppose a cache entry remains after an update. The generated proxy can answer concrete questions:

```text
Does the method contain invalidation logic?
Is invalidation before or after super.update()?
Which cache instance is used?
Which key is derived?
Does invalidation happen only after success?
```

Those questions correspond to actual source code. Breakpoints can be placed in the generated method. The runtime path can be stepped through.

Readable generated code turns framework internals into ordinary debugging targets. For a large engineering team, that can save more time than a micro-optimization in invocation overhead.

---


Transactions are particularly sensitive to self invocation and aspect ordering. Suppose:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public void batch() {
        processOne();
    }

    @Transactional
    public void processOne() {
        // ...
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    open fun batch() {
        processOne()
    }

    @Transactional
    open fun processOne() {
        // ...
    }
    ```

In an external wrapper/target model, the first question is often whether `processOne()` is being called through the transactional proxy.

With a generated subclass, the developer can reason from dispatch rules. If `batch()` executes on the generated subclass instance and calls an overridable `processOne()`, the virtual call can reach
the generated transactional override. If the method is private or final, it cannot.

The rule follows Java/Kotlin semantics rather than an external proxy escape-and-reentry model.

---


Subclass dispatch gives self invocation more coherent behavior, but teams should still test important boundaries. Real code can involve inherited methods, bridge methods, generics, interface defaults,
explicit `super` calls, visibility differences, and language-specific details.

The safe engineering principle is not:

> Compile-time subclass AOP always intercepts every internal call.

It is:

> Interception follows the generated subclass and normal dispatch semantics; important behavior should still be verified by tests.

That statement is less dramatic and more accurate.

---


Kotlin's final-by-default model makes subclass-based AOP impossible to ignore. A Java developer may forget that a class is subclassable because Java classes are open unless marked final. A Kotlin
developer must explicitly write:

```kotlin
open class UserService
```

and, where required:

```kotlin
open fun load(...)
```

That extra syntax can feel inconvenient, but it also communicates the mechanism. The source tells the reader that something is expected to subclass the component. In Kora AOP, that something is
generated code.

The relationship between source declaration and framework behavior is therefore unusually explicit.

---


Java continues to evolve: stronger encapsulation, modules, records, sealed types, virtual threads, better AOT tooling, improved JITs, and richer compiler APIs all change the framework landscape.
Techniques built around normal language semantics tend to adapt well because generated code is still just code.

If HotSpot learns a new optimization, generated methods can benefit. If static analysis improves, the generated call graph is easier to inspect. If IDE support for generated sources improves,
debugging gets better. If ahead-of-time compilation becomes more common, static classes and calls are already a good fit.

Frameworks that create a completely separate runtime execution model have to maintain that model alongside every platform evolution. Compile-time generation can lean more heavily on the language and
compiler ecosystem.

---


Modern Java and Kotlin encourage immutability, final classes, and sealed hierarchies. Subclass-based AOP should coexist with those design choices rather than forcing every class open.

A good architecture can keep domain models final while placing AOP on service boundaries designed for interception:

```text
Final domain/value types
        ^
        |
Open managed service boundary with AOP
        ^
        |
Controller / entry point
```

Domain objects do not need AOP. Infrastructure-facing service components can deliberately allow generated inheritance. This keeps framework mechanics at architectural boundaries rather than spreading
them across the whole model.

Compile-time constraints can therefore encourage clearer layering.

---


Cross-cutting concerns are clearest at boundaries with real architectural meaning. A transaction on a service method says, "this operation is atomic." A retry around an external call says, "this
integration is resilient to transient failure." A cache on a read operation says, "this result can be reused under this policy."

Those meanings are easier to understand than aspects scattered across low-level helpers.

The fact that Kora can technically intercept internal virtual calls should not encourage teams to turn every method into an aspect boundary. The goal of AOP is to remove repetitive infrastructure, not
to fragment ordinary control flow.

---


Readable generated code is powerful, but it should not become an excuse for undocumented behavior. Developers still need documentation for annotation contracts, supported method shapes, ordering
rules, configuration, transaction propagation, retry classification, cache semantics, security rules, and error behavior.

Generated source answers:

> How did this build implement the declared behavior?

Documentation answers:

> What behavior does the framework promise and why?

The two complement each other. Kora's generated proxies are most useful when the public contract is already clear and the developer wants to inspect the concrete realization.

---


Framework design contains a productive tension. Business code should not be polluted with repetitive infrastructure details, but infrastructure should not become so hidden that engineers cannot
understand it.

Compile-time AOP balances those goals.

Business code remains concise:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Transactional
    @Retry("payment")
    public Receipt charge(Payment payment) {
        // business logic
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Transactional
    @Retry("payment")
    open fun charge(payment: Payment): Receipt {
        // business logic
    }
    ```

The generated infrastructure remains visible when needed:

```text
$PaymentService__AopProxy.charge
  -> transaction boundary
  -> retry execution
  -> super.charge
```

Developers do not maintain the generated class, but they can inspect it. That is a stronger transparency model than either extreme: writing every wrapper by hand or hiding everything inside a runtime
proxy engine.

---

## A Practical Side-by-Side Comparison

Consider the same service under two conceptual implementations.

### Runtime proxy

Handwritten class:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public class OrderService {

        @Retry("orders")
        public Order load(long id) {
            return client.load(id);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    open class OrderService {

        @Retry("orders")
        open fun load(id: Long): Order {
            return client.load(id)
        }
    }
    ```

Runtime path:

```text
OrderServiceProxy
  |
  v
InvocationHandler / interceptor machinery
  |
  v
RetryInterceptor
  |
  v
method metadata
  |
  v
target OrderService
```

Typical debugging questions include:

```text
Was the proxy created?
Which proxy strategy is active?
Which interceptor matched?
What metadata did it read?
Am I calling the proxy or the target?
Does self invocation bypass it?
```

### Kora compile-time proxy

Handwritten class:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public class OrderService {

        @Retry("orders")
        public Order load(long id) {
            return client.load(id);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    open class OrderService {

        @Retry("orders")
        open fun load(id: Long): Order {
            return client.load(id)
        }
    }
    ```

Generated shape:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class $OrderService__AopProxy
        extends OrderService {

        private final Retry retry;

        @Override
        public Order load(long id) {
            return retry.execute(
                () -> super.load(id)
            );
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class `$OrderService__AopProxy`(
        private val retry: Retry
    ) : OrderService() {

        override fun load(id: Long): Order {
            return retry.execute {
                super.load(id)
            }
        }
    }
    ```

Debugging questions become more concrete:

```text
What did the generator emit?
Which Retry object was injected?
What did that Retry object do at runtime?
```

That reduction in hidden state is the practical value of compile-time AOP.

---


One of the best ways to understand Kora is to stop treating generated files as temporary compiler debris. The generated AOP proxy is part of the program. The generated DI graph is part of the program.
Generated repository implementations and mappers are part of the program.

Developers may not edit those files, but production executes them.

Once that mindset is adopted, many Kora design choices become intuitive. The framework is not trying to hide itself. It is generating the implementation layer that a more dynamic framework would
reconstruct at runtime.

---

## Compile-Time AOP Fits Kora's Broader Philosophy

Kora's overall engineering pattern can be summarized as:

```text
high-level declaration
  ->
compile-time validation
  ->
generated explicit code
  ->
thin runtime
```

AOP follows exactly that path. The developer gets concise annotations. The compiler gets enough information to validate structure. The generator creates readable source. The runtime executes direct
typed code. The application avoids unnecessary reflection and runtime proxy construction.

This consistency matters. A framework becomes easier to learn when the same mental model applies across modules. Once a developer understands generated repositories, mappers, or application wiring,
generated AOP feels like another use of the same compile-time architecture rather than a separate magical subsystem.

---


Runtime proxy behavior becomes difficult when several axes interact:

```text
interface proxy
vs
class proxy

external call
vs
self invocation

annotation on interface
vs
annotation on implementation

proxy identity
vs
target identity

ordered interceptor
vs
unordered interceptor

runtime condition true
vs
runtime condition false
```

Each axis is manageable on its own. The cross-product is not. Teams eventually accumulate framework folklore such as "that annotation works only when called from another bean" or "this method needs to
be on the interface" or "that transaction is missing because you constructed the class directly."

Compile-time generation cannot eliminate every rule, but it collapses many of them into one concrete class. If the generated override exists, interception exists. If it cannot be generated, the build
should explain why.

That is a much stronger debugging invariant.

---


A framework could perform compile-time AOP by generating bytecode directly. That might avoid one source-compilation step, but source generation has a unique transparency advantage.

Developers can read the result without a decompiler. IDE navigation can show it. Compiler errors can point into it. Framework documentation can teach with it. Diff tools can compare it. AI tools can
analyze it as ordinary Java or Kotlin.

For a framework whose core values include transparency, source generation is therefore more than an implementation convenience. It turns compiler output into documentation.

---


It is easy to overstate generated AOP by saying everything becomes a direct call. The generated method may still call interfaces. Retry may delegate to a resilience abstraction. Telemetry may call
OpenTelemetry APIs. Cache code may delegate to Caffeine or Redis. Transaction code may invoke a driver or pool abstraction.

The important property is that the **application-specific interception topology** is explicit and generated. The framework does not need a universal runtime proxy dispatcher to decide which aspects
apply to the method.

Calls inside that generated method then use the ordinary APIs of the relevant components.

This is consistent with Kora's broader preference for thin abstractions rather than building a giant framework-specific runtime world around every technology.

---


Cross-cutting concerns contain both policy and mechanism.

For retry:

```text
policy:
which failures retry?
how many attempts?
what delay?

attachment mechanism:
wrap this method call with retry execution
```

For caching:

```text
policy:
expiration, size, backend

attachment mechanism:
lookup before call, store after call
```

For transactions:

```text
policy:
isolation, propagation, connection behavior

attachment mechanism:
execute this method inside a transaction boundary
```

Compile-time AOP primarily generates the attachment mechanism. The policy can remain a runtime-configurable component. This keeps the generated structure static while preserving operational tuning.

---


Generated source provides an intuitive visual representation of aspect nesting. Suppose the generated method resembles:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Override
    public Result call(Request request) {
        validator.validate(request);

        return cache.get(request.id(), () ->
            retry.execute(() ->
                super.call(request)
            )
        );
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    override fun call(request: Request): Result {
        validator.validate(request)

        return cache.get(request.id) {
            retry.execute {
                super.call(request)
            }
        }
    }
    ```

The nesting immediately communicates:

```text
validation
  then
cache
  then, on miss,
retry
  then
business method
```

That is often easier to understand than reading several ordering numbers or container logs. Generated code turns ordering into ordinary control flow, and developers already know how to read control
flow.

---


Static generation works well with refactoring. Suppose a method changes from:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public User load(long id)
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun load(id: Long): User
    ```

to:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public User load(UserId id)
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun load(id: UserId): User
    ```

The generated proxy must be regenerated with the new signature. If the aspect can no longer support the parameter type, compilation can fail. There is no stale runtime metadata describing the old
method shape.

The handwritten method and its generated infrastructure are rebuilt together. The compiler becomes a structural verification pass over all generated integration points after every refactoring.

This is particularly valuable in large codebases where method signatures evolve frequently.

---


In regulated or tightly controlled environments, engineers sometimes need to answer a precise question:

> What code actually executes around this business method in this build?

With dynamic AOP, answering can require documenting framework configuration and proving how the runtime resolver behaves. With compile-time AOP, the generated source can be retained as part of the
build evidence.

A reproducible build can preserve:

```text
application source
Kora version
generated source
compiler version
dependency locks
final artifact
```

The generated proxy records the framework's interpretation of annotations for that build. It is not formal verification, but it is a concrete bridge between declarative intent and executable code.

---

## Method Interception: Final Assessment

For method interception, the generated-subclass model has a clear engineering profile. The intercepted method keeps its original typed signature. Aspect dependencies can become normal fields. The
original implementation is reached through a normal `super` call. Multiple aspects can become nested control flow. The runtime does not need to represent every invocation as a generic
`Method + Object[] + InvocationContext` structure.

The price is equally clear: interception follows ordinary subclassing rules. Final, private, static, or otherwise non-overridable methods cannot be intercepted by subclass overriding. The model trades
some flexibility for explicit language-level semantics.

That is a reasonable trade for backend services where application structure is known during the build.

---

## Compile-Time Validation: Final Assessment

Compile-time validation changes AOP from something the container tries to make work after startup begins into something the build proves structurally possible before packaging.

Unsupported final classes or methods can be rejected. Invalid annotation usage can be rejected. Missing dependencies can surface during graph construction. Generated source must itself compile.
Diagnostics can point to the original source element.

This reduces late surprises and makes framework correctness part of the ordinary compilation contract.

For a large service fleet, that reliability benefit is often more important than small differences in proxy-call latency.

---

## Self Invocation: Final Assessment

Self invocation is where generated subclass AOP most clearly differs from the classic external proxy mental model.

With an external proxy wrapping a distinct target, an internal target call often never returns through the proxy. Advice is bypassed.

With a generated subclass, inherited code executes on the subclass instance. A virtual call to another overridable method can therefore dispatch to the generated override and activate the aspect. The
behavior follows normal object-oriented dispatch.

Private, final, and static methods remain outside that override mechanism. Explicit `super` calls intentionally bypass overrides. Constructors have their own rules.

The result is not magical universal interception. It is something better: interception whose behavior can be explained with standard Java/Kotlin semantics.

---

## Performance: Final Assessment

Compile-time AOP improves performance primarily by reducing unnecessary framework runtime work. It can remove or reduce runtime annotation discovery, generic invocation contexts, metadata lookups,
proxy construction, reflective dispatch, temporary invocation objects, and generic interceptor traversal.

The aspect's essential behavior remains. A transaction is still a transaction. A retry still performs retries. A cache still performs lookups. Validation still evaluates rules.

The gain is that Kora can attach those behaviors to methods through specialized generated code rather than through a universal dynamic invocation engine. This can benefit startup, steady-state
efficiency, allocation pressure, JIT optimization, warm-up, and runtime predictability.

The magnitude depends on the workload, but the architectural direction is clear.

---

## Debuggability: Final Assessment

Debuggability may be the most tangible advantage for everyday engineering work. A generated proxy can be opened. Its override can be read. Its constructor reveals dependencies. Its nesting reveals
aspect order. Its class and method names can appear in production diagnostics. Its source can be compared between framework versions.

This changes the relationship between developer and framework.

The framework is no longer saying:

> Trust that this annotation will be interpreted correctly by runtime machinery.

It is saying:

> Here is the code produced from this annotation.

That is a stronger transparency model.

---


Kora is not merely optimizing the nanoseconds around a proxy call. It is optimizing the lifecycle of information.

Information available during compilation should be used during compilation. Errors detectable during compilation should fail during compilation. Structure that can be generated during compilation
should not be rediscovered at startup. Method topology that can be expressed as code should not remain generic runtime metadata. Dependencies that can be wired statically should not require runtime
discovery.

AOP fits naturally into this philosophy because aspect placement is usually known from source annotations.

Kora treats those annotations as instructions to the compiler rather than requests to a runtime container.

---


The deeper pattern is:

```text
abstraction at authoring time
specificity at runtime
```

Developers want high-level abstractions because writing repetitive infrastructure by hand is wasteful. Machines benefit from specific code because generic runtime interpretation has costs. Code
generation bridges the two needs.

A Kora developer writes:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Retry("payment")
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Retry("payment")
    ```

because that is the right level of intent.

The compiler creates a specific retry-wrapped method because that is the right level of execution.

The developer does not maintain repetitive wrappers. The JVM does not need a general AOP interpreter for every call. Both sides get the representation that suits them best.

---

## Conclusion

Aspect-oriented programming is often criticized for making control flow invisible. That criticism is justified when a small annotation activates a large runtime mechanism that developers cannot easily
inspect. The problem is not cross-cutting behavior itself. Transactions, validation, retries, caching, security, tracing, and logging genuinely belong around business operations. The problem is
allowing the implementation of those concerns to become a permanent layer of runtime mystery.

Kora's compile-time AOP model takes another route. Annotations remain declarative, but the declaration is resolved while the application is built. Kora generates a concrete proxy subclass around an
interceptable component, overrides the relevant methods, wires the required aspect dependencies, and places the surrounding behavior into ordinary source code. That generated class then participates
in the application graph and executes like normal compiled Java or Kotlin.

This changes method interception from generic runtime interpretation into specialized control flow. It changes proxy-shape errors from potential startup failures into compiler diagnostics. It changes
the self-invocation story because inherited code executes on the generated subclass itself and therefore follows ordinary virtual dispatch. It reduces the amount of runtime machinery needed merely to
decide which aspects apply. It gives the JIT concrete methods to optimize. And it gives developers a source file they can open whenever behavior is unclear.

The comparison is therefore not simply between proxies and no proxies. Kora still uses proxy-like generated classes in the architectural sense. The decisive distinction is when the proxy comes into
existence and what form it takes.

A runtime proxy is part of the live framework machinery.

A Kora AOP proxy is part of the compiled program.

That shift from runtime construction to compile-time generation changes the failure model, performance model, debugging model, and mental model of AOP.

For most backend services, the structure of cross-cutting concerns is not genuinely dynamic. The source already says which methods are transactional, validated, cached, retried, secured, or logged.
The deployment artifact is rebuilt whenever that source changes. In that environment, preserving a general-purpose runtime proxy engine often buys flexibility that the application does not use.

Kora chooses to resolve what it can while the compiler still has the richest information and while failure is still cheap.

The developer gets the annotation.

The compiler gets the complexity.

Production gets the code.
