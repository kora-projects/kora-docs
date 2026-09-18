---
title: Generated Code Makes Debugging More Transparent in the Kora Framework
description: Why the Kora Framework's generated Java and Kotlin sources are an inspectable escape hatch that makes framework behavior easier to debug, not harder.
search:
  exclude: true
---

# Generated Code Makes Debugging More Transparent, Not Harder

Generated code is often treated as a debugging smell.

The assumption is easy to understand. A developer writes a controller, service, repository interface, or method annotation, but the running application contains additional classes that were not
written directly by hand. From that observation it is tempting to conclude that debugging must become more difficult: the debugger will supposedly fall into generated wrappers, navigation will lead
into unfamiliar classes, stack traces will contain synthetic names, and understanding application behavior will require spending half the day inside `build/generated`.

That description sounds plausible, but it does not match how debugging normally works in Kora.

The Kora Framework does not replace the application with an opaque generated runtime. It moves framework work to compile time and produces ordinary Java or Kotlin source that is compiled together with the
application. Dependency wiring, HTTP handlers, repository implementations, mappings, and AOP wrappers become concrete classes rather than runtime reflection rules or dynamic proxy chains. IntelliJ can
navigate them, the JVM can debug them, the compiler validates them, breakpoints can be placed in them, and an AI agent can read them like any other source file.

The important distinction is therefore not whether generated code exists. The important distinction is what role it plays.

In normal development, the developer still works primarily with handwritten application code:

```text
Controller
   ↓
Service
   ↓
Repository
```

Breakpoints are placed in controllers, services, domain logic, mappers, integrations, and whichever part of the application is actually being investigated. The presence of a generated HTTP handler or
an AOP subclass does not force the debugger to stop there. Nor does the presence of a generated repository implementation mean that every database-related debugging session starts by reading generated
source.

Generated code becomes interesting when the question crosses the framework boundary. If the developer wants to know exactly which component was wired, exactly how a repository method executes its
query, exactly where validation occurs, or exactly how timeout, retry, circuit breaker, and fallback compose around a method, there is an additional artifact available: the code Kora actually
generated.

That is not a debugging burden. It is an escape hatch.

The central idea of this article is therefore simple:

> **Kora does not make developers debug generated code instead of their application. Developers debug their own code normally, while generated sources provide an additional transparent view into
framework behavior when they need it.**

Or, stated more strongly:

> **Generated code is not debugging noise by definition. In Kora it is the inspectable boundary between declarative application code and the JVM code that actually executes.**

---

## Debugging Does Not Mean Stepping Through Every Method

A large part of the fear around generated code comes from an imprecise mental model of how developers use a debugger.

Suppose a service method calls a repository:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public User loadUser(long id) {
        return userRepository.findById(id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun loadUser(id: Long): User {
        return userRepository.findById(id)
    }
    ```

If the developer places a breakpoint inside `loadUser`, presses **Step Over** on the repository call, and the repository returns successfully, the debugger typically executes the invoked method and
stops at the next line in the current frame. `Step Over` does not normally mean “walk through every implementation class involved in this call.” If the developer intentionally chooses **Step Into**,
uses smart step-into functionality, places a breakpoint inside the callee, or navigates through the stack frames after a failure, then the implementation becomes visible.

This distinction matters because claims such as “generated frameworks force you to walk through generated wrappers constantly” often conflate very different debugger operations.

The normal workflow remains familiar. A developer places a breakpoint where the interesting business state exists, inspects variables, evaluates expressions, steps over calls that are not relevant,
steps into calls that are relevant, and navigates through stack frames only when the execution path itself is part of the problem.

Generated code does not alter that basic model.

Consider a typical request:

```text
HTTP request
    ↓
generated Kora handler
    ↓
Controller
    ↓
Service
    ↓
generated AOP wrapper, if applicable
    ↓
Repository interface call
    ↓
generated repository implementation
    ↓
JDBC
```

The full path contains generated elements, but the developer does not need to visit every node simply because they exist. If the bug is in business validation inside the service, the debugger can stay
in the service. If the bug is an incorrect SQL predicate, the developer can inspect the repository contract and SQL. If the problem is transaction ordering, retry composition, parameter mapping, or
dependency wiring, then the generated layer becomes useful.

This is the same principle that applies to the JDK itself. Developers do not step through every `ArrayList`, socket, executor, or JDBC driver method during ordinary debugging merely because those
implementations are present in the call chain. They cross into lower layers when the lower layer becomes relevant to the investigation.

Generated code should be treated the same way.

---

## Application Source Remains the Primary Development Surface

Kora's generated source is useful precisely because it is optional most of the time.

The primary development model is still handwritten application code. Developers write controllers, services, domain objects, repository contracts, configuration declarations, integration code, and
tests. They work in those files, review those files, and reason about the behavior expressed there.

A normal feedback loop looks like this:

```text
source
  ↓
compiler diagnostics
  ↓
tests
  ↓
debugger
```

Only when the developer wants to understand what the framework added does another layer become interesting:

```text
generated source
```

That distinction is important because generated source can be misrepresented in two opposite ways. One extreme pretends it does not exist and treats every framework abstraction as magic. The other
extreme implies that developers must constantly read generated files to understand basic application behavior.

Neither is accurate.

Kora's model is closer to this:

```text
Handwritten source
        │
        ├── sufficient for ordinary feature development
        │
        ├── compiler catches structural mistakes
        │
        ├── tests verify behavior
        │
        └── debugger inspects application state
                    │
                    └── generated source available
                        when framework mechanics matter
```

The generated layer is additional evidence. It is not the center of every development task.

A good way to phrase the contract is:

> **Generated code is not code developers must understand to use Kora. It is code they can inspect when ordinary debugging is not enough.**

That is a significant difference from a framework whose machinery is equally complex but whose final runtime composition is much harder to inspect.

---

## Kora Generates Source, Not an Opaque Runtime Model

Not all framework abstraction is equally inspectable.

A runtime-heavy framework can derive behavior from a combination of classpath scanning, reflection, runtime metadata, dynamic proxies, post-processors, interceptor registries, container state, and
conditional configuration. None of those mechanisms is inherently bad. Mature frameworks use them successfully, and experienced developers learn how to debug them. The point is simply that the
executable behavior can be distributed across several runtime mechanisms rather than represented directly in one application-specific source artifact.

Conceptually, the path may look like this:

```text
Runtime-heavy model

your source
    ↓
framework runtime
    ↓
reflection
    ↓
dynamic proxies
    ↓
container metadata
    ↓
interceptor chain
    ↓
actual behavior
```

Kora deliberately moves much of that work earlier:

```text
Kora

your source
    ↓
compile-time processors
    ↓
generated source
    ↓
ordinary JVM bytecode
    ↓
actual behavior
```

This difference has consequences for debugging.

If a Kora application contains a generated graph class, a generated HTTP handler, a generated repository implementation, or a generated AOP wrapper, the developer can inspect that class as the
concrete result of framework processing. Instead of reconstructing what the runtime container must have done, the engineer can often inspect what the compiler produced.

That generated artifact becomes a form of ground truth.

This is particularly useful for questions whose answer depends on the exact application rather than on generic framework documentation. Which dependency did this component receive? Which mapper was
selected? Which aspect wraps which method? Which handler invokes this controller? Which repository implementation performs this query? What order do several cross-cutting policies execute in?

The answer does not have to remain conceptual. It can be represented in code.

---

## Generated Source Is an Escape Hatch

The most useful way to understand generated code in Kora is as an escape hatch from abstraction.

Abstractions are useful because they let developers work at a higher level. A repository interface is easier to reason about than repetitive JDBC ceremony. An annotation for retry or validation is
easier to maintain than rewriting the same wrapper logic in every service. Declarative HTTP routing is more concise than manually assembling every handler.

The problem begins only when abstraction removes the ability to inspect what actually happens.

Kora's approach is to keep the high-level abstraction while preserving a path downward.

A developer can remain here:

```text
@Repository
interface UserRepository {
    ...
}
```

for nearly all feature work.

But when a specific question arises, the path continues:

```text
UserRepository
      ↓
generated implementation
      ↓
database API calls
```

Likewise, a developer can remain at an annotated service method until the ordering of cross-cutting behavior becomes relevant:

```text
@Retry(...)
@Timeout(...)
public Result call() { ... }
```

Then the path continues into the generated wrapper where the call sequence is explicit.

This is what makes generated source an escape hatch rather than a burden. It preserves the abstraction for ordinary work but leaves the implementation visible when the abstraction needs to be
questioned.

That is a strong debugging property.

---

## Go to Implementation Should Sometimes Show Generated Code

IDE navigation into generated code is sometimes described as though the IDE has failed to understand the framework.

In many cases, the opposite is true.

Suppose the application declares:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Repository
    public interface UserRepository {
        ...
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Repository
    interface UserRepository {
        ...
    }
    ```

and Kora generates an implementation during compilation. If a developer invokes **Go to Implementation** on `UserRepository`, then the generated repository class is a valid answer because it is the
implementation that the application actually executes.

The relationship is straightforward:

```text
UserRepository
       ↓
$UserRepository_Impl
```

Seeing that class is not broken navigation. It is precise navigation into the executable implementation of the declared contract.

That can be extremely useful. If the developer wants to know how a parameter is bound, which mapper is called, which database component is injected, or how a query result becomes a domain object, the
generated implementation is exactly the right file to inspect.

The crucial point is intent.

When doing business development, developers often care primarily about the repository contract and the service that uses it. When investigating framework behavior, they may care about the generated
implementation. Those are different navigation goals, and a framework-aware IDE plugin can make the distinction more convenient, but the generated implementation itself is not an error.

The stronger way to frame it is:

> **Seeing the generated implementation is not broken navigation. It is precise navigation into the code that actually runs.**

---

## IDE Tooling Improves Convenience, Not Comprehensibility

Framework-aware IDE tooling is valuable because it can optimize navigation for common intentions. A Kora-specific plugin can help developers jump between declarations and generated components,
understand configuration, or surface framework-specific relationships more conveniently.

But there is an architectural distinction worth preserving: the plugin improves the experience; it is not what makes debugging possible.

Without framework-specific IDE support, developers still have ordinary Java and Kotlin navigation. Generated sources still exist. The compiler still produces diagnostics. The debugger still
understands compiled classes. Breakpoints still work. Stack frames still exist. Tests still exercise the same application code.

With additional Kora-aware tooling, navigation and framework UX can become more convenient:

```text
Without framework-specific plugin

normal Java/Kotlin navigation
generated sources available
compiler diagnostics available
debugger available
tests available
```

```text
With framework-specific plugin

all of the above
+
Kora-aware navigation
+
framework-specific IDE conveniences
```

This distinction matters because it demonstrates that Kora's transparency is architectural rather than dependent on proprietary tooling.

The IDE plugin can make an already-inspectable system nicer to use. It does not create inspectability from nothing.

---

## Generated Repositories Turn an Interface Into a Concrete Debugging Target

Repositories are one of the clearest examples of why generated code can improve transparency.

At the declaration level, the developer usually wants a compact contract. A repository method says what data is needed and often exposes the SQL directly. That is the appropriate level for most code
review and application development.

At runtime, however, something must still perform the actual work. Parameters must be mapped, a query must be executed, a result must be read, and values must be converted into application types.

Kora generates that implementation at compile time.

This gives the developer two useful representations of the same behavior.

The first is the concise application-level declaration:

```text
repository contract
    +
query
    +
return type
```

The second is the execution-level implementation:

```text
database component
    ↓
parameter mapping
    ↓
query execution
    ↓
result mapping
    ↓
return value
```

Most of the time the first representation is sufficient. When the second becomes relevant, it is available as ordinary source.

This is better than forcing every developer to write JDBC boilerplate manually, and it is also better than making the implementation inaccessible.

The generated repository is therefore not simply compiler output. It is a debugging artifact that explains how the higher-level contract becomes database work.

---

## Generated HTTP Handlers Expose the Real Request Path

HTTP handling follows the same principle.

A developer writes a controller because that is the useful abstraction for application code. The application should not require every business developer to manually write low-level request routing,
parameter extraction, body mapping, response mapping, telemetry hooks, and execution plumbing for every endpoint.

Kora generates the infrastructure.

For ordinary work, the developer sees:

```text
HTTP route declaration
      ↓
controller method
      ↓
business logic
```

When deeper inspection is necessary, the full path can be traced:

```text
request
   ↓
generated HTTP handler
   ↓
parameter extraction / request mapping
   ↓
interceptors
   ↓
controller
   ↓
response mapping
   ↓
response
```

That generated handler can answer very concrete debugging questions. Was the expected mapper selected? Which route parameter is being read? Which interceptor runs? Is the controller method actually
reached? Which response mapper is responsible for the final output?

The developer does not need to infer all of this from framework metadata. The generated handler is the executable bridge.

Again, the important point is not that developers should routinely browse every generated HTTP class. The point is that when an HTTP boundary behaves unexpectedly, the final framework interpretation
is visible.

---

## Generated AOP Is One of the Strongest Debugging Arguments

AOP is where compile-time generation produces one of the clearest transparency benefits.

Cross-cutting behavior is conceptually simple at the annotation level. A method might declare validation, retry, timeout, circuit breaker, fallback, transaction, cache, logging, or another policy. The
complexity appears when several policies interact.

A runtime interceptor model must assemble a chain somehow. Experienced framework users may know the ordering rules, proxy rules, self-invocation rules, and registration mechanics. But when a difficult
interaction appears, the developer may have to reconstruct the effective chain from configuration, metadata, framework conventions, and runtime objects.

Kora generates the wrapper as source.

Conceptually, the result may resemble:

```text
Generated AOP proxy
        ↓
fallback
        ↓
circuit breaker
        ↓
retry
        ↓
timeout
        ↓
super.businessMethod()
```

The exact sequence depends on the annotations and framework rules, but the important property is that the sequence becomes code.

A developer can open the generated class and inspect the actual method.

This changes the debugging question from:

> “How did the framework assemble its interceptor chain at runtime?”

to:

> “What does this generated method do?”

The second question is an ordinary programming question.

That is why a readable generated wrapper can be easier to debug than an interceptor chain assembled dynamically from runtime metadata.

> **A generated wrapper you can read line by line is usually easier to debug than an interceptor chain you first have to reconstruct.**

---

## Validation Becomes Explicit Code

Validation illustrates the same point at a smaller scale.

At the application level, validation is declarative because the developer wants to state constraints rather than manually orchestrate every validator. But when validation behaves unexpectedly, the
developer may want to know which validators were selected, how parameters were passed, what order checks occur in, and where a violation becomes an exception.

Generated code provides that answer.

Instead of treating “validation happened” as an invisible framework event, the developer can inspect the wrapper that performs it. The generated class reveals the concrete validators and the path into
the original method.

This can be particularly useful when inferred generic types, nested validation, mapping, or annotation composition creates a non-obvious result. The generated source becomes a precise representation
of the framework's interpretation of the declarations.

It is also an excellent artifact for AI-assisted debugging because a model can inspect the wrapper and answer focused questions without asking the developer to read an entire generated class manually.

---

## Generated Resilience Code Makes Policy Composition Visible

Resilience policies are especially sensitive to ordering.

Timeout inside retry behaves differently from retry inside timeout. A circuit breaker outside retry observes different failures than a circuit breaker inside retry. Fallback placement changes which
exceptions it can see. These are not cosmetic differences; they affect latency, load amplification, failure classification, and user-visible behavior.

In a declarative API, the developer wants the policy to remain concise:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Fallback(...)
    @CircuitBreaker(...)
    @Retry(...)
    @Timeout(...)
    public Result call() {
        ...
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Fallback(...)
    @CircuitBreaker(...)
    @Retry(...)
    @Timeout(...)
    fun call(): Result {
        ...
    }
    ```

But when the exact composition matters, the generated AOP class provides a concrete representation of what the framework does.

That means production debugging can move from abstract questions to executable ones. The engineer can ask which layer sees a timeout exception, whether retry wraps the timeout, whether the circuit
breaker observes exhausted retries or individual attempts, and whether fallback handles the outermost failure. Those relationships are represented directly in generated control flow.

This is a strong example of why code generation can improve rather than reduce debuggability.

---

## Generated Code Is Valuable Because It Is Readable

There is an important qualification to everything above: not all generated code is equally useful.

Generated source can be technically available and still be practically unreadable. A code generator could emit giant state machines, deeply nested synthetic names, meaningless temporary variables, or
structures optimized entirely for the compiler rather than for human inspection.

In that case, saying “the generated source is there” would not be much of a debugging argument.

Kora's architectural goal is different. The framework explicitly presents generated code as something developers can inspect, debug, and review. The generated graph looks like component construction
logic. Generated repositories look like concrete database integrations. Generated AOP wrappers look like sequential method calls around the original implementation. Generated HTTP infrastructure
reflects the request path.

The useful question is therefore not:

> “Does the framework generate code?”

but:

> **“Is the generated code readable enough to explain what the framework does?”**

That is the relevant debugging criterion.

Generated code is valuable when it acts as a human-readable intermediate representation between high-level declarations and bytecode.

---

## The Generated Graph Is the Application Wiring Made Concrete

Dependency injection is another area where compile-time generation can turn an abstract container model into inspectable application code.

Developers generally do not want to construct every service manually. A DI framework should manage construction, lifecycle, reuse, modules, configuration, and dependency resolution. The developer
wants to describe the dependency structure, not hand-write the full bootstrap sequence.

Kora builds and validates that graph during compilation.

The generated graph therefore represents the framework's answer to questions such as:

- Which component satisfies this dependency?
- Which module factory creates this object?
- Which implementation was selected?
- In which direction do dependencies flow?
- Which components participate in lifecycle?
- Which dependency caused a graph error?

Most of the time, the developer does not need to inspect the graph source because constructor signatures and compiler diagnostics already provide enough information. When a wiring question becomes
subtle, however, the generated graph can be opened.

That is a much more concrete debugging surface than an invisible runtime container assembled from reflective scanning.

The developer can move from:

```text
“What did the container decide?”
```

to:

```text
“Show me the generated construction path.”
```

This is exactly the kind of escape hatch that makes an abstraction easier to trust.

---

## Compile-Time Generation Removes Entire Categories of Runtime Debugging

Generated source helps when debugging is necessary, but the larger benefit is that many structural problems never reach runtime debugging at all.

A missing dependency, ambiguous dependency, cycle, invalid mapping, invalid repository contract, or incorrect AOP usage can often fail during compilation. Kora's graph processing and generated code
are checked before the application starts.

This changes the debugging economics.

Framework comparisons often focus only on the question:

```text
How easy is it to debug a failure once it happens?
```

A better comparison also asks:

```text
How many failures become runtime bugs in the first place?
```

The easiest runtime bug to debug is the one that compilation prevented from becoming a runtime bug.

Consider a missing dependency. In a runtime-heavy model, the application may discover the problem during context initialization or when a particular path is activated. In Kora, graph resolution can
reject the application during compilation.

Consider an invalid generated repository contract. Instead of waiting for the application to execute the method and discover an incompatibility, annotation processing and compilation can expose the
problem earlier.

Consider malformed AOP usage. If the generator cannot produce a valid wrapper, the build itself can fail.

The feedback loop is therefore:

```text
edit
  ↓
compile
  ↓
graph / processors / type system validate
  ↓
precise error
  ↓
fix
```

Only behavior that survives this structural validation moves on to runtime tests and debugging.

This does not mean Kora prevents all runtime bugs. Business logic errors, concurrency issues, network failures, incorrect SQL semantics, resource exhaustion, and many other problems remain runtime
concerns. But reducing the number of framework-structural failures that reach runtime is itself a debugging advantage.

---

## Compiler Errors Are Part of the Debugging Story

It is useful to broaden the definition of debugging beyond the interactive debugger.

In modern development, debugging means finding the cause of incorrect behavior. Sometimes the tool is a breakpoint. Sometimes it is a stack trace. Sometimes it is a test failure. Sometimes it is a
compiler diagnostic.

Kora intentionally pushes framework mistakes toward the last category.

This creates a shorter path from mistake to explanation. Instead of launching an application, reproducing a request, entering a specific path, and inspecting a runtime failure, the developer may
receive a direct compilation error describing a missing or ambiguous dependency.

That is not merely compile-time safety. It is debugging shifted earlier in the lifecycle.

For experienced engineers, this is valuable because the feedback is deterministic. For new engineers, it is valuable because the diagnostic helps teach the framework's structural rules. For AI agents,
it is valuable because the model receives a precise signal it can use to correct the generated code.

The compile-time architecture therefore influences debugging long before the JVM debugger starts.

---

## Stack Traces May Be More Explicit Without Being Prettier

There is one point where generated code can legitimately add noise: stack traces.

If a generated handler or AOP wrapper participates in execution, its frame may appear in the stack trace. A business-only stack would obviously be shorter if framework infrastructure did not exist,
but the framework infrastructure does exist in every non-trivial system. The useful question is whether its representation provides information.

A generated frame can be very informative because it may be application-specific.

Instead of seeing only generic runtime machinery such as:

```text
Proxy.invoke()
MethodInterceptor.invoke()
ReflectiveMethodInvocation.proceed()
...
```

a stack trace may include a concrete generated class associated with the specific service or component whose call is being wrapped.

That is not necessarily prettier. It can still add frames. But “more frames” and “less debuggable” are not the same thing.

The generated class can tell the developer where in the actual executable path the failure occurred. If the stack crosses `$UserService__AopProxy`, that may reveal that an aspect was involved. If it
crosses a generated repository implementation, the database boundary is visible. If it crosses a generated handler, the route infrastructure is visible.

The honest position is therefore nuanced:

> Generated classes can make stack traces longer, but those frames often expose the real execution path rather than hiding it.

For diagnosis, explicitness can be more valuable than aesthetic cleanliness.

---

## Debugging a Framework Boundary Is Different From Debugging Business Logic

A recurring mistake in discussions about debuggability is to treat all debugging as one activity.

There are at least two distinct cases.

The first is business debugging:

```text
Why did this order receive the wrong price?
Why was this user considered inactive?
Why did this state transition occur?
```

The relevant code is usually application code. Generated framework infrastructure is mostly irrelevant.

The second is framework-boundary debugging:

```text
Why was this mapper selected?
Why does this repository return this type?
Why is this dependency wired here?
Why did validation run before retry?
Why does this endpoint use this handler?
Why is this interceptor executing?
```

Here the framework's interpretation matters.

Kora's generated source is valuable primarily in the second case.

The architecture therefore preserves a clean separation:

```text
Business problem
    ↓
debug handwritten code

Framework-boundary problem
    ↓
inspect generated code when useful
```

This prevents generated source from becoming part of every debugging session while still making it available exactly where it provides the most value.

---

## Breakpoints in Generated Code Are Sometimes the Best Breakpoints

Because generated source is ordinary source, developers can place breakpoints in it when that is useful.

Suppose an HTTP parameter is being mapped incorrectly. A breakpoint in the controller may show only the already-wrong value. A breakpoint in the generated handler can reveal where the value was
extracted and which mapper converted it.

Suppose retry behavior is surprising. A breakpoint in the business method reveals how many times the method was entered, but a breakpoint in the generated resilience wrapper can reveal why another
attempt was scheduled or why an exception was classified as non-retryable.

Suppose a repository returns a mapping error. A breakpoint in the generated repository can reveal the exact call that invokes the mapper and the values coming from the database layer.

These are not examples of generated code becoming mandatory. They are examples of generated code increasing the number of useful observation points.

A framework that exposes more concrete observation points gives engineers more debugging options.

---

## Navigation Into Generated Code Can Be More Precise Than Runtime Proxy Navigation

Dynamic proxy systems can also be debugged, but navigation may be less application-specific. The proxy class may be created at runtime, the interceptor chain may be assembled from metadata, and the
user-visible source declaration may not map directly to a single concrete source file representing the full behavior.

Kora's generated implementation provides that mapping.

A repository interface can have a generated repository class.

A service with aspects can have a generated AOP subclass.

A route declaration can have a generated handler.

An application graph declaration can have generated wiring.

This means **Go to Implementation** can often land in something meaningful and stable: the code that represents this application's processed declaration.

The value is not that generated code is inherently superior to every runtime mechanism. The value is that the relationship between declaration and execution is explicit and source-addressable.

---

## Source Generation Gives Reviewers a Second View

Generated source is also useful outside interactive debugging.

During difficult code review, a reviewer may want to verify what a declaration implies. If a change adds several aspects, the reviewer can inspect the generated wrapper after compilation. If a
repository contract changes, the generated implementation can reveal the effective mapping. If a graph change produces an unexpected dependency, generated wiring can help explain it.

This creates two levels of review:

```text
Intent
  ↓
handwritten declaration

Implementation
  ↓
generated source
```

The reviewer usually focuses on intent. The implementation layer is available when verification is necessary.

This is a useful property because it keeps application code concise without forcing reviewers to trust hidden machinery blindly.

---

## Generated Code Also Improves Incident Analysis

The same transparency matters in production incident work.

Suppose telemetry suggests that retry behavior is amplifying latency. The team can inspect the generated resilience wrapper to verify the actual composition order around the affected service method.

Suppose a route appears to bypass an expected interceptor. The generated handler can help establish whether the interceptor was actually wired.

Suppose a repository unexpectedly uses a mapper the team did not expect. The generated implementation can show which component was selected.

Suppose an application starts with a dependency configuration that seems wrong. The generated graph can reveal the concrete construction path.

This does not replace runtime telemetry, logs, traces, metrics, or heap and CPU profiling. Those remain essential. Generated source simply provides another layer of evidence when the incident crosses
into framework behavior.

---

## Generated Code Is a Better Ground Truth Than Memory

Framework expertise often contains a large amount of memorized behavior: aspect ordering rules, proxy rules, injection conventions, lifecycle assumptions, mapping conventions, and special cases.
Experienced developers become productive partly because they know these rules without looking them up.

But memory is not always the best debugging source.

It can be outdated. It can come from another framework version. It can be confused with another project. It can overlook configuration specific to the current application.

Generated code reflects the current build.

That gives it a useful epistemic property: it is local evidence.

The engineer can compare assumptions against what this exact application produced.

This is especially important in large teams where not every developer is a framework specialist. Instead of asking someone to remember the right internal rule, the team can inspect the artifact
generated from the current codebase.

---

## AI Makes Generated Source More Valuable Than Before

AI coding agents change the economics of inspectable code.

Historically, the strongest criticism of generated source was that although it might technically be readable, developers would not want to spend time reading a large generated class. That criticism
was often reasonable. A 300-line generated wrapper may contain only twenty lines relevant to the current question.

An AI agent can perform that filtering.

The developer can ask:

- Why is this dependency recreated?
- Which graph component produces this object?
- Show me where retry wraps timeout.
- Which mapper is selected for this repository method?
- Trace this HTTP request from handler to controller.
- Why is this validator invoked here?
- Which generated class implements this repository?
- Explain only the frames involved in this stack trace.
- Compare the annotations on this method with the generated call order.

The workflow becomes:

```text
generated source
       ↓
AI agent
       ↓
focused explanation
       ↓
developer verifies the relevant behavior
```

This is a significant change.

The value of generated source no longer depends on every developer being willing to read every generated line manually. What matters is that the executable behavior exists in a form that humans and
machines can inspect.

> **Humans do not need to read every generated line themselves anymore. What matters is that the executable behavior exists in a form both humans and machines can inspect.**

That makes transparency more valuable in the AI era, not less.

---

## AI Can Follow the Exact Application Instead of Guessing the Framework

This is particularly important for framework debugging because AI models are prone to plausible generalization.

If a developer asks how a framework probably orders several aspects, a model may answer from general knowledge, another version, or a similar framework. The answer can sound convincing while being
wrong for the current application.

Generated code changes the task.

Instead of asking:

```text
“How does Kora usually do this?”
```

the agent can inspect:

```text
“What did this build generate for this method?”
```

That turns an inference problem into a code-reading problem.

AI is more useful when it can ground explanations in concrete local source. The same applies to dependency wiring, mappings, repository implementations, and HTTP handlers.

Kora's generated artifacts therefore reduce the amount of framework behavior that a model has to guess.

---

## The Compiler, Debugger, Tests, and AI Form One Diagnostic Stack

The strongest debugging story is not any one tool in isolation. It is the interaction between several tools.

Kora's compile-time architecture creates a useful progression:

```text
1. compiler
   catches structural errors

2. tests
   verify expected behavior

3. debugger
   inspects application state and control flow

4. generated source
   exposes framework interpretation

5. AI agent
   explains and connects the evidence
```

A problem can stop at the earliest layer capable of explaining it.

A missing dependency may never require a test.

A wrong business rule may never require generated source.

A mapper problem may be revealed by a test and explained by a generated repository.

An unexpected aspect interaction may require a debugger plus the generated AOP wrapper.

This layered approach is more useful than arguing about whether one debugging technique is universally best.

---

## The Easiest Bug to Debug Is the One That Never Reaches Runtime

One of the strongest consequences of Kora's architecture deserves to be stated directly.

Framework discussions frequently compare stack traces, debugger ergonomics, or proxy navigation while ignoring how many failures each model permits to survive until runtime.

Compile-time DI and generation change that boundary.

If the compiler rejects a missing dependency, there is no runtime missing-bean incident to debug.

If an invalid graph cycle prevents compilation, no startup debugging session is necessary.

If repository generation fails because the declared contract cannot be processed, the problem appears before deployment.

If AOP generation cannot produce valid code, the build fails before the service starts.

This leads to a useful principle:

> **The easiest runtime bug to debug is the one the compiler prevented from becoming a runtime bug.**

This does not eliminate debugging, but it changes the population of bugs that survive into runtime. The remaining debugging work is more likely to involve business semantics, integration behavior,
real infrastructure, concurrency, or other genuinely runtime concerns.

That is a better place to spend debugging time.

---

## There Is Still a Cost to Generated Code

A credible argument should acknowledge the trade-offs.

Generated code introduces more files into the build output. Class names may be unfamiliar at first. Stack traces can contain generated frames. IDE search results may include classes developers did not
write. Go-to-implementation can sometimes lead into generated files when the developer was thinking at the declaration level. Build tooling must register generated source roots correctly. Incremental
compilation and processor behavior become part of the build system.

These are real costs.

The argument is not that generation is free.

The argument is that these costs should be compared with the alternatives. Framework behavior must live somewhere. If it is not represented in generated application-specific source, it may live in
runtime metadata, reflective logic, proxy infrastructure, configuration rules, container state, or framework internals.

The relevant question is not:

```text
generated code
vs
no framework machinery
```

It is:

```text
generated, inspectable machinery
vs
runtime-composed machinery
```

Once the comparison is framed correctly, the debugging trade-off looks different.

---

## Generated Classes Should Not Be Confused With Handwritten Ownership

Another concern is maintenance responsibility.

Developers should not edit generated classes by hand. They should change the declaration that produced them. If a generated repository is wrong because the repository contract is wrong, the fix
belongs in the repository source or mapping declaration. If an AOP wrapper has the wrong behavior because annotations are ordered incorrectly, the fix belongs in the handwritten method declaration. If
graph wiring is wrong because a component was provided incorrectly, the fix belongs in the module or component definition.

Generated code is an observation surface, not the ownership surface.

That distinction prevents a common anti-pattern where teams start patching generated output directly.

A useful model is:

```text
Handwritten source
    = intent and ownership

Generated source
    = framework interpretation and evidence
```

Debugging may inspect both. Maintenance should normally modify the first.

---

## Readable Generation Strengthens Abstraction Rather Than Weakening It

There is a common misconception that if developers ever need to inspect an abstraction's implementation, then the abstraction has failed.

That is too strict.

Good abstractions reduce the need to understand implementation details during ordinary work. They do not necessarily prohibit inspection.

In fact, an abstraction can be more trustworthy when its implementation remains available.

Kora's generated source follows this principle. Controllers remain controllers, repositories remain repositories, and resilience policies remain declarative. The developer is not required to abandon
these abstractions. But the framework does not insist that the implementation remain invisible.

This creates a useful combination:

```text
high-level API for productivity
        +
inspectable low-level implementation
        =
abstraction without opacity
```

For debugging, this is often the ideal balance.

---

## Framework Transparency Is More Important Than Framework Minimalism

A framework can be small and still be difficult to debug if its behavior is implicit.

Conversely, a framework can generate substantial infrastructure and still be easy to reason about if that infrastructure is explicit, regular, and inspectable.

Therefore the useful metric is not simply how many framework classes exist or how much code is generated.

The more relevant questions are:

- Can the developer trace a declaration to execution?
- Can the actual wiring be inspected?
- Can the effective AOP order be seen?
- Can repository execution be understood?
- Can HTTP request handling be traced?
- Can compiler diagnostics catch structural errors?
- Can breakpoints be placed at framework boundaries?
- Can an AI agent explain the current generated path from evidence?

Kora performs well on these dimensions because code generation is part of its transparency model rather than merely an optimization technique.

---

## Generated Code Can Improve Onboarding

The same property that helps debugging also helps new engineers.

A developer learning Kora may understand controllers and services immediately but be unfamiliar with compile-time DI or generated AOP. Instead of learning only from conceptual documentation, they can
inspect what the framework generated for a small example.

The learning sequence becomes:

```text
declaration
   ↓
generated implementation
   ↓
debugger
   ↓
observed behavior
```

This is especially useful for engineers coming from runtime proxy frameworks because they can see the contrast directly. A Kora aspect is not merely described as compile-time AOP; the generated
subclass demonstrates what that means.

The framework becomes easier to learn because the abstraction has a visible implementation.

---

## Generated Code Helps Separate Framework Bugs From Application Bugs

Another practical debugging benefit is fault localization.

When behavior is unexpected, the team often needs to determine whether the problem belongs to application logic, framework interpretation, or the underlying integration.

Generated source can help establish that boundary.

Suppose the application declares a repository method and receives unexpected data. The developer can inspect the generated implementation. If the generated parameter mapping matches the declaration,
the next suspect may be SQL or database state. If the generated mapping is clearly not what the declaration implies, the framework processor or mapping configuration becomes a stronger suspect.

Suppose an aspect order behaves unexpectedly. The generated wrapper reveals whether Kora produced the expected call sequence. If it did, the issue may be the policy semantics rather than generation.
If it did not, the problem moves toward annotation interpretation or framework behavior.

Suppose an HTTP route maps a parameter incorrectly. The generated handler can show whether extraction and conversion follow the intended contract.

This ability to inspect the framework boundary can dramatically narrow debugging search space.

---

## Ground Truth Matters Most in Difficult Bugs

Simple bugs rarely need framework internals.

The generated layer becomes most valuable precisely when the problem is difficult.

Difficult bugs often involve disagreement between assumptions and reality. The code looks correct, the configuration looks correct, the framework is supposed to behave a certain way, yet the
application does something unexpected.

At that point, another explanatory document is less useful than concrete evidence.

Generated source is concrete evidence.

It represents the framework's interpretation of the declarations used in that build.

This is why code generation should not be judged only as a developer-experience cost. Under difficult conditions, it can be the most useful debugging artifact in the system.

---

## A More Accurate Debugging Model

The debugging story can therefore be summarized as a layered decision process rather than as “developers debug generated code.”

Start with the application:

```text
Is the bug in business logic?
        ↓ yes
debug handwritten code
```

If not, ask whether the build already explains the issue:

```text
Is there a compiler / graph / processor diagnostic?
        ↓ yes
fix structural problem
```

If the behavior appears only at runtime:

```text
Can a test reproduce it?
        ↓ yes
use test + debugger
```

If the question crosses the framework boundary:

```text
Need exact wiring / mapping / AOP / handler behavior?
        ↓ yes
inspect generated source
```

If the generated class is large or unfamiliar:

```text
AI agent
   ↓
extract and explain relevant path
```

This is a much more realistic description of Kora development than the idea that every debugging session begins in `build/generated`.

---

## The Real Comparison Is Inspectable Mechanism vs Hidden Mechanism

The debate around generated code often starts from the wrong baseline.

Developers compare:

```text
handwritten application code
```

with:

```text
handwritten application code + generated code
```

and conclude that the latter is more complex.

But a framework needs machinery in both cases.

The real comparison is closer to:

```text
Framework A

handwritten source
+
runtime reflection
+
dynamic proxies
+
container metadata
+
interceptor registries
+
runtime wiring
```

versus:

```text
Kora

handwritten source
+
generated application-specific source
+
ordinary compiled classes
```

Both systems have framework behavior. The difference is where it is materialized and how easy it is to inspect.

This is why generated code can improve debuggability even though it increases the number of source files.

Complexity represented explicitly can be easier to debug than complexity represented implicitly.

---

## Transparency Is Not the Same as Simplicity

It is also useful to distinguish transparency from simplicity.

Generated AOP around several resilience policies can still be complex. A large application graph can still contain many components. A generated HTTP handler can still coordinate several mappings and
interceptors. Code generation does not magically make complex behavior simple.

What it does is make the complexity visible.

That matters because debugging complex systems requires accurate representations.

An explicit complex program is often easier to analyze than an implicit complex runtime state.

Kora's debugging advantage therefore should not be described as “there is no complexity.” The more defensible claim is:

> The framework tries to turn framework complexity into ordinary source code that existing JVM tools can inspect.

That is a much stronger and more technically precise argument.

---

## Generated Source Works With the Existing JVM Toolchain

Another benefit of generating ordinary Java and Kotlin source is tool compatibility.

The source passes through the regular compiler.

The resulting classes participate in ordinary stack traces.

The debugger can understand line mappings and methods.

The IDE can index symbols.

Static analysis can inspect the generated types.

Build tools can treat them as source sets.

Tests execute the same compiled classes.

AI tools can parse them as programming language source.

This matters because Kora does not require a separate proprietary debugger to make framework behavior visible.

The framework reuses the mature JVM tooling ecosystem.

That keeps the debugging model familiar even when the generated implementation is new to the developer.

---

## Why the Distinction Matters for Kora's Broader Design

Generated code is not an isolated implementation trick in Kora. It is connected to several broader framework principles.

Compile-time dependency injection means wiring can be validated and generated.

Thin abstractions mean the generated code can remain close to JDBC, HTTP, Kafka, gRPC, and other familiar technologies.

One recommended approach reduces the number of competing runtime models that a developer must reconstruct.

Strong typing increases the amount of structure the compiler can validate.

Readable generated source externalizes framework context that would otherwise have to live in documentation, runtime metadata, or developer memory.

Fast testing provides another cheap way to verify the generated application model.

AI assistance benefits because the framework's behavior is represented in source.

These properties reinforce one another.

The debugging argument therefore fits naturally into Kora's overall architecture: move hidden runtime work into explicit compile-time artifacts, then let the standard JVM toolchain inspect those
artifacts.

---

## What Generated Code Does Not Solve

A balanced view should also be clear about the limits.

Generated source will not diagnose a bad SQL query plan.

It will not explain why a remote service is overloaded.

It will not determine whether a retry policy is architecturally appropriate.

It will not find every race condition.

It will not replace distributed tracing.

It will not replace heap analysis, CPU profiling, database observability, network diagnostics, or production metrics.

It will not make poorly designed business logic easy to understand.

Generated code helps primarily at the boundary where framework declarations become executable behavior.

That is an important boundary, but it is only one part of production debugging.

The correct argument is therefore not “generated code solves debugging.” It is “generated code makes framework behavior more inspectable.”

---

## A Generated Wrapper Is Often Easier to Explain Than a Runtime Chain

This distinction becomes particularly visible when teaching or reviewing cross-cutting behavior.

Suppose a developer sees an unexpected timeout after several retries.

In a runtime interceptor model, the explanation may require understanding interceptor registration, precedence rules, proxy construction, metadata, and the framework's invocation pipeline.

In Kora, the generated wrapper can reveal the concrete composition for that exact method.

An engineer can reason about it like ordinary nested calls:

```text
fallback(
    circuitBreaker(
        retry(
            timeout(
                businessMethod()
            )
        )
    )
)
```

The real generated code may be more detailed, but the control structure is inspectable.

That allows reviewers, debuggers, and AI agents to reason from the actual execution path instead of from general framework folklore.

---

## The Generated Implementation Can Be Better Documentation Than a Generic Diagram

Documentation must remain generic because it describes a framework feature across many possible applications.

Generated source is application-specific.

That means it can answer questions documentation cannot answer directly.

Documentation can explain how repository generation works. The generated repository shows which mapper this repository uses.

Documentation can explain AOP ordering rules. The generated wrapper shows the order for this particular method.

Documentation can explain dependency injection. The generated graph shows the selected dependencies in this build.

Documentation can explain request mapping. The generated handler shows the actual route and mappers.

This gives generated source a unique debugging role: it is framework documentation specialized automatically to the current application.

That is a powerful way to think about it.

---

## AI Turns Application-Specific Documentation Into a Conversation

Once an AI agent can read those generated artifacts, the developer can interact with that application-specific documentation conversationally.

Instead of opening a large generated graph and manually tracing constructors, the engineer can ask:

> “Why does `UserService` receive this implementation?”

Instead of scanning an AOP wrapper:

> “Show me where retry wraps timeout and explain which exception the circuit breaker observes.”

Instead of reading a generated handler:

> “Trace `POST /users/{id}` from route matching to the controller parameter.”

Instead of searching a repository implementation:

> “Which mapper converts the second result column, and where is it provided?”

The AI agent is not inventing the answer. It is interpreting the generated source.

That is the ideal relationship between AI and framework transparency.

---

## Generated Source Reduces Dependence on Tribal Knowledge

Framework debugging often becomes difficult when correct behavior depends on rules that experienced developers know but the codebase does not expose directly.

These rules become tribal knowledge:

- this annotation is intercepted only in certain situations;
- this proxy does not apply to self-invocation;
- this component is created because a classpath condition activated something;
- this interceptor has a particular precedence;
- this mapper is selected through a convention hidden elsewhere.

Kora cannot eliminate all framework knowledge, but generated source moves many decisions from memory into code.

The generated artifact can answer what happened.

That reduces the need to remember invisible runtime state.

This is useful for onboarding, code review, incident response, and AI-assisted development alike.

---

## An Explicit Extra Frame Can Be Better Than an Invisible Decision

One of the strongest objections to generated code is aesthetic: stack traces and navigation feel less clean because there are extra generated classes.

That objection is understandable, but the alternative should be considered.

A generated frame is explicit evidence that the call passed through a specific wrapper.

An invisible runtime decision may produce a cleaner-looking application stack but require deeper framework knowledge to reconstruct what happened.

For debugging, explicit evidence is often preferable to invisible elegance.

The right optimization target is therefore not “fewest visible framework frames.” It is “fastest path to understanding actual execution.”

Kora's generated code is designed around the latter.

---

## Code Generation Moves Complexity Earlier

Another way to describe Kora's model is that it shifts framework complexity from runtime to build time.

At build time, processors resolve dependencies, validate graph structure, analyze declarations, and generate classes.

At runtime, the JVM executes those compiled classes.

This has a debugging consequence beyond performance.

Build-time complexity produces build-time artifacts and build-time diagnostics. Runtime complexity produces runtime state.

Neither disappears, but one is often easier to inspect deterministically.

The generated code can be versioned conceptually against the exact build, reproduced locally, and analyzed without reproducing a specific runtime container state.

That is especially useful for difficult framework interactions.

---

## The Best Debugging Surface Is the One You Can Ignore Until You Need It

A good diagnostic mechanism should not impose itself on every task.

Generated source works best when it has exactly this property.

During routine feature work, developers can ignore it.

During code review, they can ignore it unless a framework interaction matters.

During testing, they can ignore it unless the test reveals a boundary issue.

During debugging, they can stay in application code unless the behavior becomes unclear.

When necessary, the generated implementation is available.

That is a strong ergonomics model because it combines abstraction with inspectability.

---

## A Practical Example: Debugging a Repository

Imagine that a repository method unexpectedly returns an object with one field missing.

A reasonable investigation might proceed as follows.

First, inspect the SQL and the declared return type. If the problem is obvious there, fix it.

Second, run the relevant test and reproduce the issue.

Third, place a breakpoint in the service or repository caller and inspect the returned value.

If the mapping remains unexplained, navigate to the generated repository implementation. There the developer can inspect which result mapper is called and which values are supplied.

If the mapper itself is generated or injected, follow that component.

At no point was the developer forced to begin in generated source. The generated implementation became relevant only when the repository abstraction no longer explained the behavior.

That is the pattern Kora enables.

---

## A Practical Example: Debugging Resilience

Imagine that a service method is annotated with timeout, retry, circuit breaker, and fallback, and production traces show longer latency than expected.

The first step is not necessarily to open generated code. The team may begin with metrics, tracing, logs, configuration, and a focused test.

If the remaining question is the exact policy nesting, then the generated AOP wrapper becomes the strongest source of truth.

The developer can inspect the method and determine whether retry re-enters timeout for every attempt, whether the circuit breaker observes individual failures or the final retry result, and where
fallback catches the resulting exception.

This is much faster than debating from memory about annotation order.

---

## A Practical Example: Debugging DI

Suppose a developer expects one implementation of an interface but compilation reports ambiguity.

The error itself may already be sufficient. Kora has prevented the issue from becoming a runtime mystery.

If the developer still wants to understand the graph, the component declarations, modules, tags, and generated wiring can be inspected.

Again, generated code is secondary evidence. The primary advantage is that the problem was detected before runtime.

This demonstrates why the full debugging story must include compile-time validation, not just debugger navigation.

---

## A Practical Example: Debugging an HTTP Mapping

Suppose a controller receives an unexpected parameter value even though the route declaration appears correct.

A breakpoint in the controller confirms the bad value.

The developer can then inspect the generated handler to see how the path, query, header, or body parameter is extracted and which mapper performs conversion.

If the generated code matches expectations, attention can move to the incoming request or mapper implementation. If it does not, the boundary is localized immediately.

The generated handler therefore functions as a precise boundary between HTTP declaration and controller execution.

---

## A Better Vocabulary for Generated Code

The phrase “generated code” covers too many different things.

It can mean opaque compiler internals.

It can mean source emitted by a schema generator.

It can mean optimized state machines.

It can mean repetitive application glue.

It can mean runtime bytecode generated dynamically.

These have very different debugging properties.

Kora's model is best described as **generated application infrastructure in ordinary source form**.

That wording is more precise because it captures why the code is useful: it represents infrastructure that would otherwise need to be created somewhere else, but it remains accessible through normal
language tooling.

This distinction prevents unproductive arguments where all code generation is treated as equivalent.

---

## Kora's Model Is Closer to Generated Glue Than a Generated Runtime

The phrase “generated runtime” can also be misleading.

Kora does have runtime libraries, of course. HTTP servers, database drivers, Kafka clients, gRPC libraries, telemetry components, and resilience implementations all exist at runtime.

But the application-specific composition of those pieces is generated as source rather than being discovered and assembled primarily through runtime reflection.

The generated layer is therefore closer to glue code:

```text
your components
   +
framework libraries
   +
generated glue
   =
running application
```

That is an important distinction because glue code is naturally inspectable.

The engineer can see how one part connects to another.

---

## Transparency Scales Better Than Memorized Framework Rules

As a framework grows, developers inevitably encounter features they use infrequently.

A person may know the HTTP layer very well but rarely touch scheduling. Another may know database repositories but not resilience composition. A third may maintain Kafka consumers but rarely inspect
AOP.

If debugging depends on remembering the internal rules of every subsystem, expertise becomes difficult to scale across a team.

Inspectable generated source changes this.

Developers can reconstruct unfamiliar behavior from current artifacts instead of relying entirely on memory.

AI strengthens this further because the agent can read the relevant generated class and explain the mechanics in context.

This allows a broader group of engineers to diagnose framework interactions without becoming experts in every module.

---

## Transparency Also Helps Framework Maintainers

Generated source is useful not only to application developers.

Framework maintainers can use generated output to verify that processors emit the intended structure. Regression tests can compare behavior. Bug reports can include generated artifacts. A problem can
be reproduced by inspecting what the processor produced for a particular declaration.

This improves communication between users and maintainers because both sides can discuss the concrete generated class rather than only the high-level annotation.

The generated artifact becomes a shared debugging language.

---

## The Right Trade-Off Is Explicitness for Build-Time Complexity

Kora pays for some of this transparency during compilation.

Annotation processing and code generation perform work before the application starts. Generated sources increase build output. Processor bugs can exist. Developers may occasionally need to clean and
rebuild to inspect fresh output.

This is a real trade-off.

But the framework receives several things in exchange:

- structural validation before runtime;
- explicit application-specific wiring;
- ordinary source for framework-generated behavior;
- reduced reliance on runtime reflection;
- reduced reliance on dynamic proxies;
- better inspectability;
- fast runtime startup;
- deterministic artifacts for humans and AI.

From a debugging perspective, this is a reasonable trade: more work happens where the compiler and build system can validate it, and less framework composition remains hidden in runtime state.

---

## Generated Code Does Not Eliminate Abstraction Leaks

No framework can completely prevent abstractions from leaking.

A database abstraction eventually meets database behavior. An HTTP abstraction eventually meets HTTP. A retry abstraction eventually meets time and failure. A DI abstraction eventually meets object
lifecycle and dependency structure.

Kora's approach is not to pretend these leaks never occur. It makes the boundary visible when they do.

This is important because experienced engineers do not need perfect abstractions. They need abstractions whose failure modes can be understood.

Generated source contributes directly to that property.

---

## What Good Debugging Looks Like in Kora

A productive Kora debugging workflow is therefore ordinary most of the time.

Start with the failing behavior.

Reproduce it with a test if possible.

Inspect the handwritten code.

Use normal breakpoints.

Read the compiler error if the problem is structural.

Check logs, metrics, and traces if the issue is operational.

Only cross into generated source when the unresolved question is specifically about what Kora generated or how framework behavior composes.

At that point, generated code provides a concrete answer.

This is very different from a workflow where developers are required to understand generated files before they can use the framework at all.

---

## A Simple Diagnostic Hierarchy

The overall strategy can be summarized compactly:

```text
1. Handwritten source
       ↓
   Is the bug here?

2. Compiler diagnostics
       ↓
   Did Kora reject the structure?

3. Tests
       ↓
   Can behavior be reproduced?

4. Debugger / traces / logs
       ↓
   What happened at runtime?

5. Generated source
       ↓
   What exactly did Kora generate?

6. Framework source
       ↓
   Why does Kora generate it that way?
```

Most bugs stop before the last two stages.

That is exactly how it should be.

Generated source exists to make the deeper stages possible without making them mandatory.

---

## The Debugger Story Is Better When the Execution Path Has a Source File

One of the most practical benefits of source generation is simply that the relevant execution path can be associated with a source file.

If the JVM is executing a generated AOP subclass, the developer can open the class.

If it is executing a generated repository, the developer can open the class.

If an HTTP handler participates in the request path, the developer can inspect the handler.

This sounds simple, but it is powerful.

The debugging experience becomes a sequence of concrete code locations rather than an attempt to reconstruct invisible framework decisions.

That is the essence of transparency.

---

## Generated Code Is Especially Valuable for Rare Problems

Routine development does not justify studying internals constantly.

Rare problems do.

A framework may work correctly for months before an unusual combination of configuration, mappings, multiple aspects, or dependency resolution creates a subtle issue. Those are exactly the cases where
generic documentation and memory are least reliable.

Generated source provides application-specific evidence at the moment it matters most.

This is why the argument should not be evaluated based on how often developers open generated files. Low frequency does not mean low value.

A crash dump is rarely inspected during normal development, but it is invaluable during the right incident. Generated source has a similar optional diagnostic role.

---

## The AI Era Changes the Cost of Deep Inspection

Before coding agents, the cost of deep inspection was mostly human attention. If the answer required tracing a long generated class, a developer had to decide whether the time investment was
justified.

Today an agent can read that class quickly, extract the relevant control flow, compare it with the declaration, and explain the result.

This effectively lowers the cost of transparency.

Frameworks that expose behavior as source benefit disproportionately because machines can consume that source directly.

A hidden runtime model forces the agent to infer.

A generated source model gives the agent something to read.

That is an increasingly important difference.

---

## Inspectable Behavior Is Becoming an Architectural Asset

The broader implication extends beyond debugging.

Inspectable behavior helps onboarding, review, migration, incident analysis, AI assistance, and long-term maintenance. It lowers dependence on folklore and reduces the amount of framework state
developers must carry mentally.

Kora's generated-source approach therefore should not be understood only as a performance optimization.

It is an architectural choice about where framework knowledge lives.

Instead of storing a large share of application-specific framework behavior only in runtime state, Kora materializes much of it as source.

That makes the system easier to reason about after the compiler has done its work.

---

## The Strongest Comparison Is Not “Codegen vs No Codegen”

The strongest comparison is:

```text
Inspectable compile-time representation
```

versus:

```text
runtime behavior that must be reconstructed
```

Every framework performs work on behalf of the developer.

The question is whether that work leaves behind an understandable representation.

Kora does.

That is the core of the debugging argument.

---

## Conclusion

Generated code does not automatically make debugging harder.

What matters is whether the generated code replaces normal development, whether it is readable, whether it corresponds clearly to the application's declarations, whether standard tooling can inspect
it, and whether it gives engineers useful evidence when framework behavior becomes relevant.

Kora's model is designed around exactly those properties.

Developers still debug their own controller, service, and business logic as ordinary Java or Kotlin. `Step Over` does not force them through every generated implementation. They enter generated
classes only when they intentionally step into them, place a breakpoint there, navigate to an implementation, inspect a stack frame, or ask a deeper question about the framework boundary.

Most of the time, the normal workflow remains:

```text
source
  ↓
compiler
  ↓
tests
  ↓
debugger
```

Generated source is the optional next layer.

When that layer is needed, it provides something valuable: application-specific ground truth. The generated dependency graph shows real wiring. The generated repository shows the implementation that
actually executes the query. The generated HTTP handler shows how the request reaches the controller. The generated AOP subclass shows the exact composition of validation, resilience, transactions,
caching, or other cross-cutting behavior.

This can make framework behavior easier to reason about than a model assembled dynamically from reflection, runtime metadata, and interceptor chains.

The trade-off is not free. Generated classes can add stack frames, appear in navigation, and increase build output. But those visible artifacts should be compared with the runtime machinery they
replace, not with an imaginary framework that has no machinery at all.

Kora's approach is to make that machinery explicit.

The result is not that developers spend their days in `build/generated`. The result is that when a difficult question appears, they have somewhere concrete to look.

And increasingly, even that inspection does not have to be manual. An AI agent can read the generated source, trace the execution path, identify the selected mapper, explain aspect ordering, or show
exactly how a dependency was wired. The important thing is that the behavior exists in a form that can be inspected rather than guessed.

That leads to the most useful way to describe Kora's debugging model:

> **Kora does not make developers debug generated code instead of their application. Developers debug their own code normally, while generated sources provide an additional transparent view into
framework behavior when they need it.**

And the broader conclusion is even stronger:

> **Generated code is not debugging noise by definition. In Kora it is the inspectable boundary between declarative application code and the JVM code that actually executes.**
