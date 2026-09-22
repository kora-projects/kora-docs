# Compile-Time Is Not Enough: Why Kora Rethinks the Framework Model Itself

Moving dependency injection and AOP to compile time is one of the most important architectural improvements modern JVM frameworks have made. It reduces reflection, moves structural errors earlier, improves startup, lowers runtime metadata costs, and gives the compiler a larger role in validating the application before it ever runs. Frameworks such as Micronaut have demonstrated that this approach works at production scale and can preserve a familiar annotation-driven development model while substantially changing the cost profile underneath it.

But compile-time processing solves only one dimension of framework complexity.

A framework can move bean definitions, AOP proxies, query models, configuration metadata, and dependency wiring into the compiler and still preserve much of the conceptual structure inherited from an older container-centric model. The runtime becomes leaner, yet developers may still need to understand bean contexts, qualifiers, scopes, replacement semantics, proxy behavior, lifecycle abstractions, framework-specific annotations, multiple execution models, and a broad platform of framework-owned concepts.

That leads to the deeper question:

> **If you are already willing to redesign the runtime architecture, why preserve so much of the old framework programming model?**

Kora's most interesting design choice is not simply that it performs dependency injection, AOP, repositories, mappings, and HTTP infrastructure at compile time. Its more radical choice is that it also tries to reduce the amount of framework model that needs to exist at all.

That is the central thesis of this article:

> **Moving DI and AOP to compile time is a major improvement, but it does not automatically remove the architectural complexity inherited from a Spring-like programming model. Kora goes further: it does not only move framework work earlier — it also deliberately reduces the amount of framework model that exists in the first place.**

The distinction is easiest to express visually.

One modernization strategy is:

```text
old framework model
        ↓
move discovery to compile time
        ↓
generate metadata / proxies earlier
        ↓
faster and leaner runtime
```

A more radical strategy is:

```text
rethink framework model
        ↓
remove concepts that are no longer necessary
        ↓
choose one direct programming path
        ↓
generate only the infrastructure still needed
        ↓
compile-time implementation
```

Kora is interesting because it aims for the second model.

Its question is not only:

> How can we make the container faster?

It is also:

> **How much container do we need at all?**

## Compile-Time Is an Implementation Strategy, Not a Simplicity Guarantee { #compile-time-not-enough }

Compile-time processing is powerful because it changes when the framework makes decisions.

A runtime-oriented dependency-injection system might discover components, resolve relationships, construct proxies, analyze annotations, and validate contracts during startup. A compile-time system can move much of that work into annotation processing, KSP, or another compiler phase.

The result can be dramatically better:

```text
runtime-oriented model

source
  ↓
compile
  ↓
application starts
  ↓
scan / reflect / build metadata
  ↓
construct proxies / graph
  ↓
runtime
```

becomes:

```text
compile-time model

source
  ↓
processor / KSP
  ↓
generated metadata / source
  ↓
compiler validation
  ↓
runtime
```

That is a real architectural improvement.

The problem is that the second diagram says nothing about how many concepts the framework exposes to the application developer.

A framework can eliminate runtime reflection while still presenting a large conceptual system. It can precompute a dependency container without reducing the importance of container semantics. It can generate proxies ahead of time without changing the developer's proxy-based mental model. It can precompute metadata for several execution styles without reducing the number of styles the team must choose between.

This is why compile-time should not be treated as synonymous with simplicity.

It is possible to optimize the implementation of a complex model without simplifying the model itself.

That distinction matters because runtime cost and cognitive cost are different forms of complexity.

## Runtime Cost and Cognitive Cost Are Different { #runtime-vs-cognitive-cost }

A framework can be extremely efficient at runtime while remaining expensive to understand.

Runtime efficiency is about things such as startup, memory, reflection, allocations, classpath scanning, dynamic proxy generation, metadata construction, and per-request overhead.

Cognitive efficiency is about how many concepts developers must understand to predict the system.

These dimensions overlap, but they are not the same.

A developer may still need to understand:

- bean contexts;
- scope semantics;
- qualifiers;
- replacement rules;
- factory beans;
- conditional beans;
- proxy boundaries;
- interception semantics;
- lifecycle callbacks;
- multiple HTTP models;
- reactive and imperative execution;
- coroutine support;
- configuration layers;
- framework-specific test contexts;
- integration-specific annotation systems.

None of these concepts becomes free simply because its implementation was moved to build time.

That gives us an important equation:

```text
compile-time optimization
≠
conceptual simplification
```

The two can reinforce each other, but one does not imply the other.

Kora's distinctive move is to pursue both.

## A Faster Container Is Still a Container { #faster-container }

Compile-time dependency injection can remove classpath scanning and runtime reflection, but it can still preserve container-oriented thinking.

The framework may still organize the application primarily around a bean context, bean definitions, qualifiers, scopes, replacement semantics, factories, lifecycle rules, and proxy-aware behavior.

Those concepts can be compiled earlier.

They are still concepts the developer must understand.

This is not inherently bad. A mature dependency model provides flexibility. It can support conditional components, environment-specific wiring, replacement in tests, custom scopes, lifecycle policies, third-party integrations, and a large extension ecosystem.

The architectural question is whether a greenfield backend needs all of that machinery as the default mental model.

Kora answers more aggressively.

Its application graph is described through constructors, interfaces, `@Component`, `@Module`, `@KoraApp`, and generated wiring. The framework still provides dependency injection, but the developer is encouraged to reason in terms of ordinary object relationships rather than primarily in terms of a dynamic container.

That changes the center of gravity.

Instead of:

```text
application
   ↓
container
   ↓
beans
   ↓
runtime resolution
```

the model becomes closer to:

```text
application types
      ↓
compile-time graph
      ↓
generated construction
      ↓
ordinary objects
```

The difference is not that Kora has no framework abstractions.

The difference is that the framework tries to collapse those abstractions back into ordinary language semantics wherever possible.

## Familiarity Can Preserve Accidental Complexity { #familiarity-cost }

Spring-like familiarity is a real adoption advantage.

Micronaut explicitly embraces this. Its documentation says many APIs are heavily inspired by Spring and Grails by design, helping developers become productive quickly. That is a rational product choice. A large population of JVM engineers already knows annotations such as `@Controller`, `@Singleton`, `@Value`, `@ConfigurationProperties`, repository-style APIs, bean concepts, AOP annotations, and familiar application-context patterns.

Preserving that vocabulary lowers migration friction.

But familiarity has a cost.

A familiar model can preserve concepts that were originally shaped by constraints no longer present in the modern JVM.

The adoption loop becomes:

```text
familiar model
      ↓
easy migration
      ↓
old mental model survives
```

This is not necessarily wrong. Migration compatibility is valuable.

But it is a different optimization target from greenfield simplicity.

Kora chooses another balance:

> **Familiar underlying technologies, not necessarily familiar framework machinery.**

The familiar layer should be Java and Kotlin, HTTP, JDBC, Kafka, gRPC, transactions, telemetry, SQL, concurrency, and standard JVM debugging.

The framework itself does not need to reproduce every familiar container concept merely because developers have seen it before.

That is a subtle but important distinction.

## Kora Optimizes for Backend Familiarity, Not Framework Familiarity { #backend-familiarity }

There are two different kinds of familiarity.

The first is framework familiarity.

A developer knows what a bean scope means, which annotation activates a component, how proxy replacement works, how environment conditions affect registration, how framework configuration binds, and how interception behaves.

The second is backend familiarity.

A developer understands HTTP, SQL, JDBC, Kafka, gRPC, transactions, retries, timeouts, OpenTelemetry, connection pools, resource limits, concurrency, and distributed failure.

The second category is more durable.

Kora tries to preserve that durability.

A repository should still feel like database access. Kafka should still behave like Kafka. HTTP should still be HTTP. gRPC contracts should remain gRPC contracts. Telemetry should remain aligned with OpenTelemetry. Virtual Threads should use normal Java control flow.

This means an experienced JVM engineer can bring more of their existing mental model directly into the framework.

The result is lower framework-specific cognitive overhead.

## Compile-Time Proxies Are Still Proxies { #compile-time-proxies }

Compile-time AOP is another major improvement modern frameworks have made.

Generating proxies or interception metadata during compilation avoids runtime proxy construction, reduces reflection, improves startup, and makes invalid interception contracts easier to catch early.

Micronaut was designed around exactly this idea. Its compiler generates bean definitions and AOP proxies before runtime.

That is a strong architecture.

But compile-time proxies are still proxies.

The developer may still need to think about proxy boundaries, interception, bean identity, replacement, method eligibility, execution order, and the relationship between the declared class and the object the framework actually exposes.

Moving the proxy earlier changes its cost profile.

It does not automatically remove proxy semantics from the mental model.

That suggests a deeper question:

> **Should cross-cutting behavior still be modeled primarily as a proxy/container concern?**

Kora's generated AOP model is interesting because it emphasizes the concrete generated implementation as part of the application graph.

Conceptually:

```text
application contract
      ↓
generated wrapper/subclass
      ↓
ordinary method calls
      ↓
business method
```

The generated code may technically be a subclass or wrapper, but the debugging model becomes less abstract because the exact implementation is available as source.

The emphasis is not only on *when* the proxy is created.

It is on whether the proxy remains an important piece of framework magic the developer must reconstruct mentally.

## Generated Code Can Collapse Framework Semantics Into Language Semantics { #generated-language-semantics }

Readable generated source is one of Kora's strongest architectural tools because it can turn framework behavior into ordinary Java or Kotlin.

A retry and timeout composition can become something conceptually equivalent to:

```java
return retry.retry(() ->
    timeout.execute(() ->
        super.call()
    )
);
```

Dependency injection can become:

```java
var repository = new UserRepositoryImpl(database, telemetry);
var service = new UserService(repository);
```

A repository interface can become a concrete implementation containing direct database calls and mapping logic.

The important property is not that generated code is always elegant.

It may be verbose.

The important property is that framework semantics become language semantics.

This reduces the number of invisible rules developers must carry.

The framework can remain declarative at the top level while still providing an explicit execution model underneath.

## A Modern Framework Should Question Every Inherited Abstraction { #question-inherited-abstractions }

The JVM platform has changed enough that modern frameworks should revisit assumptions inherited from earlier generations.

Java now has Virtual Threads, records, sealed types, stronger pattern matching, improved concurrency, more mature standard APIs, and a much richer ecosystem of external infrastructure standards.

That creates an architectural obligation:

> **Do we still need the same abstractions that were designed around Java 8-era constraints?**

The answer will not always be no.

Some abstractions remain valuable regardless of JVM improvements.

Dependency injection still solves composition.

AOP still reduces repetitive cross-cutting code.

Configuration still needs structure.

Persistence still needs mapping.

HTTP frameworks still need routing.

But a modern framework can often use simpler mechanisms.

Kora's design philosophy reflects this willingness to remove rather than merely optimize.

## Virtual Threads Change the Concurrency Decision { #virtual-threads }

Virtual Threads are the clearest example of a platform feature changing framework design.

Before Loom, highly concurrent blocking applications faced a real trade-off. Platform threads were expensive enough that reactive programming, callback models, asynchronous APIs, event loops, and coroutine-based approaches could provide substantial scalability benefits.

Those models remain valuable in some workloads.

But Virtual Threads change the default economics for mainstream I/O-bound backend services.

A request can now remain synchronous:

```text
request
  ↓
controller
  ↓
service
  ↓
repository
  ↓
JDBC
```

without consuming an expensive platform thread while blocked on every I/O operation.

This means a new framework can reasonably ask whether it still needs several equal-status programming models for common backend work.

Kora's answer is generally no.

It chooses straightforward synchronous code on Virtual Threads as the baseline.

That is conceptual simplification, not merely runtime optimization.

## Too Many Fast Programming Models Are Still Too Many Models { #too-many-models }

A framework can support imperative, reactive, async, coroutine, and several client/server execution styles efficiently.

That breadth can be useful.

It is still breadth.

Every programming model creates additional choices:

- Which one is preferred?
- Which libraries are compatible with it?
- Which context propagation model applies?
- How are transactions handled?
- How does telemetry flow?
- How do tests execute?
- Can models be mixed?
- What happens at boundaries?

Even if every path is fast, the team still pays the conceptual cost.

This gives us another important equation:

```text
performance optimization
≠
conceptual simplification
```

Kora's stronger position is that if the platform now provides a sufficiently strong default concurrency model for mainstream backend work, supporting many competing models may no longer be worth the cognitive cost.

That is a different design philosophy from frameworks that optimize multiple models equally.

## One Recommended Path Is an Architectural Feature { #one-path }

Framework flexibility is often treated as an unconditional advantage.

In practice, every additional supported approach increases the space of possible application designs.

Large teams eventually respond by writing internal rules.

They define which HTTP client is approved, which persistence API is preferred, whether reactive code is allowed, which test style is canonical, how configuration should be written, and which integrations are considered standard.

The framework offers many paths.

The organization narrows them again.

Kora tries to perform some of that narrowing upstream.

The framework landing documentation explicitly emphasizes one clear solution per problem.

This creates a simpler organizational relationship:

```text
framework gives one strong default
        ↓
teams converge naturally
        ↓
less internal governance
```

rather than:

```text
framework gives many valid choices
        ↓
teams diverge
        ↓
platform team writes rules
        ↓
organization recreates one path internally
```

For a greenfield service estate, that can be a major advantage.

## Framework Size Matters as Much as Runtime Speed { #framework-size }

A framework can be compile-time-first and still become a very broad platform.

Micronaut 5 is a good example. Its own release material describes a platform refresh spanning more than seventy Micronaut modules. That breadth covers data, cloud integration, messaging, languages, testing, security, serverless, GraalVM, configuration, and many other capabilities.

That is a strength for teams that want a broad managed ecosystem.

It also reveals a different design center.

A large framework platform naturally creates more integration surfaces, more modules, more concepts, and more framework-specific knowledge.

Kora deliberately chooses a smaller target:

```text
focused backend surface
      ↓
fewer concepts
      ↓
one recommended path
      ↓
lower cognitive overhead
```

This does not make Kora automatically better.

It makes it optimized for a different job.

## STEP: Simple, Transparent, Efficient, Predictable { #step }

Kora's design can be summarized through four properties:

> **Simple. Transparent. Efficient. Predictable.**

These are useful because they separate conceptual architecture from raw performance.

**Simple** means the framework tries to minimize competing programming models, framework-specific abstractions, and internal governance requirements.

**Transparent** means important framework behavior becomes generated source, explicit graph structure, strong contracts, and readable execution paths.

**Efficient** means work that can be performed once at build time should not be repeated at runtime. Startup, memory, allocations, testing cost, and fleet overhead all matter.

**Predictable** means structural errors fail early, the graph is explicit, execution paths are inspectable, and there are fewer hidden runtime decisions.

Compile-time DI alone primarily improves efficiency and predictability.

Kora's larger bet is to improve all four.

## Spring-Compatible Thinking Can Become a Design Constraint { #spring-compatible-thinking }

Compatibility with a familiar mental model is useful during migration.

It lowers training cost, makes framework adoption easier, and reduces the number of concepts developers need to relearn immediately.

But familiarity can also constrain first-principles design.

If a new framework begins with the question:

> How do we make Spring-like development faster?

then Spring-like concepts naturally survive.

The implementation changes.

The conceptual architecture may not change as much.

A different starting question is:

> **What is the most direct way to build this service today?**

That question can produce a very different framework.

Kora is interesting because it leans closer to the second formulation.

It still uses familiar high-level ideas—components, modules, repositories, controllers, configuration, annotations—but does not treat Spring compatibility as an architectural requirement.

This gives it more freedom to remove concepts rather than merely optimize them.

## Directness Is a Different Optimization Target From Migration Familiarity { #directness }

Migration-friendly frameworks optimize for continuity.

Direct frameworks optimize for minimal distance between application intent and execution.

These goals can conflict.

A migration-friendly API may intentionally preserve familiar container concepts because they help developers transition.

A direct API may prefer simpler language constructs even if they are less familiar to framework specialists.

Kora's design center is closer to directness.

The familiar things should be backend concepts.

Java developers should understand constructors, interfaces, records, exceptions, Virtual Threads, HTTP, SQL, JDBC, Kafka, gRPC, telemetry, and transactions.

The framework should not require expertise in a large historical runtime model merely to compose those technologies.

This is why Kora's “familiarity” should be interpreted differently.

It aims for familiar JVM development, not necessarily familiar Spring-style machinery.

## Data Access Shows the Difference Clearly { #data-access }

Compile-time repositories are a good example of the distinction between optimizing an old model and simplifying it.

Micronaut Data uses ahead-of-time compilation to precompute repository queries and explicitly positions itself as removing the runtime metamodel and query translation costs associated with older data abstractions.

That is a significant improvement.

But the broader framework still offers a rich repository and persistence ecosystem inspired by Spring Data and GORM.

Kora's data model is narrower.

Its repository abstraction is intentionally thin, with generated implementations around JDBC or Cassandra and explicit control over queries and mappings.

The design question is not simply whether query generation happens at compile time.

It is how much persistence framework the application needs in the first place.

If explicit SQL and predictable database behavior are priorities, a thinner repository model can be easier to reason about than a broad data platform even when both compile their metadata ahead of time.

## HTTP Shows the Same Pattern { #http }

The same distinction appears in HTTP.

A compile-time framework can precompute routes, request mappings, reflection metadata, and controller information while still maintaining a broad annotation universe and multiple server/client programming models.

Kora can take a narrower path: generated handlers, direct request/response contracts, declarative clients, OpenAPI generation, telemetry, and one primary execution model.

Again, the difference is not merely when metadata is created.

It is how much framework semantics exist between an HTTP declaration and the code that runs.

Kora tries to keep that distance small.

## Build-Time Work Is Valuable Only If It Simplifies the Runtime and the Model { #build-time-value }

Moving work into the build is not automatically valuable.

A framework could theoretically perform enormous amounts of compilation, generate large metadata graphs, and produce complicated machinery that remains difficult to understand.

The useful build-time work is work that buys something concrete:

- fewer runtime decisions;
- stronger compiler diagnostics;
- simpler execution;
- inspectable generated code;
- faster startup;
- less runtime state;
- smaller conceptual surface.

Kora's compile-time model is strongest when viewed through those outcomes.

The build is not the goal.

A simpler runtime and simpler mental model are the goal.

## AI Makes the Difference Between Familiarity and Simplicity More Important { #ai-era }

AI-assisted development changes the economics of framework familiarity.

Historically, familiarity mattered enormously because humans had to remember APIs, search documentation, read tutorials, and accumulate framework-specific experience.

An AI agent can learn an unfamiliar API quickly if the framework provides good documentation and explicit contracts.

That reduces the value of “this looks like Spring” as a standalone advantage.

What remains difficult for both humans and agents is architectural complexity.

An agent still has to reason about which execution model is active, which bean scope applies, how proxies interact, what gets replaced, which annotation generation path is used, and which competing pattern the project expects.

This leads to a very modern principle:

> **Framework familiarity matters less when an agent can learn an API instantly; architectural simplicity matters more because both humans and agents must still reason about the system.**

Kora benefits from this shift.

## STEP Becomes an Agent Advantage { #step-agent }

The STEP model translates almost perfectly into AI-assisted development.

```text
Simple
→ less ambiguity

Transparent
→ inspectable behavior

Efficient
→ short iteration loop

Predictable
→ deterministic validation
```

A smaller conceptual surface gives the agent fewer patterns to mix incorrectly.

Generated code provides concrete evidence.

Compiler diagnostics turn wrong assumptions into deterministic repair tasks.

Fast startup and testing shorten the feedback loop.

Canonical documentation and examples reduce reliance on probabilistic memory.

The result is not that AI makes framework design irrelevant.

It makes framework design more important.

Poor abstractions are easier to generate code for than to reason about.

Kora's advantage is that its architecture is designed around explicitness and small solution spaces.

## Compiler Feedback Is More Valuable Than Framework Similarity { #compiler-feedback }

An AI agent can be wrong confidently.

A compiler cannot.

That makes compile-time validation extremely valuable in agentic workflows.

The loop becomes:

```text
agent writes code
      ↓
compiler validates graph/contracts
      ↓
precise diagnostic
      ↓
agent repairs
      ↓
tests verify behavior
```

The agent does not need perfect prior knowledge of Kora.

It can learn through deterministic feedback.

Generated source adds another layer when the diagnostic alone is insufficient.

The model can inspect what Kora actually produced for the current application instead of inferring hidden runtime state.

This is a more durable advantage than API familiarity alone.

## Fewer Concepts Reduce Organizational Governance { #governance }

Broad frameworks create organizational work.

As frameworks gain modules, execution models, data abstractions, testing styles, and integration surfaces, platform teams often need to define an internal subset.

They create:

- approved patterns;
- architecture guides;
- internal starters;
- wrappers;
- conventions;
- linting rules;
- framework-specific training;
- migration policies.

This is not a failure of the framework.

It is the natural cost of breadth.

Kora's focused model can reduce this governance burden because the framework already makes stronger decisions.

One recommended path means fewer decisions need to be re-litigated inside each organization.

That is especially important when scaling teams.

## Cognitive Overhead Compounds Over Time { #cognitive-overhead }

Framework complexity is often measured at project creation.

That is the least important moment.

The real cost appears over years.

Every framework-specific concept becomes something future engineers may need during onboarding, debugging, incident response, migrations, refactoring, and upgrades.

One concept seems harmless.

Fifty concepts repeated across hundreds of services become institutional knowledge.

This is why conceptual simplicity compounds.

A useful greenfield principle is:

> **The best framework model is often the one future engineers can reconstruct with the least specialized knowledge.**

Kora's generated source, explicit graph, thin abstractions, and narrow execution model all support that goal.

## Broad Platforms and Focused Frameworks Optimize Different Things { #broad-vs-focused }

Micronaut's broad platform is not an accident.

It is a deliberate strategy.

A managed ecosystem across many modules reduces library selection work, integrates features consistently, supports multiple languages and environments, and gives teams a large ready-made surface.

Kora's narrower scope is also deliberate.

It prioritizes mainstream production backend concerns and expects external technologies to remain visible.

The comparison is therefore:

```text
broad platform

many capabilities
     ↓
many managed integrations
     ↓
many concepts
     ↓
high ecosystem convenience
```

versus:

```text
focused framework

core backend capabilities
     ↓
fewer concepts
     ↓
one recommended path
     ↓
lower framework overhead
```

Neither model is universally superior.

The important thing is to recognize that compile-time architecture does not determine which model a framework chooses.

## Performance Without Conceptual Simplification Is Only Half the Win { #performance-half-win }

Removing reflection and runtime scanning is valuable.

Reducing startup time is valuable.

Lowering memory usage is valuable.

Generating queries ahead of time is valuable.

But if the application team still has to maintain a broad framework mental model, only one category of cost has been reduced.

The runtime gets cheaper.

The architecture may remain expensive to understand.

Kora's stronger proposition is that performance and simplicity should reinforce each other.

Use compile time to remove runtime work.

Use modern JVM features to remove obsolete abstractions.

Use one recommended path to reduce design entropy.

Use generated code to expose the implementation.

Use thin integrations to preserve backend knowledge.

That is a more complete modernization strategy.

## The Runtime Should Do Less, and the Developer Should Need to Know Less { #less-runtime-less-knowledge }

The ideal compile-time framework does not merely produce a faster runtime.

It also produces a smaller explanation.

A developer should be able to answer:

- what components exist;
- how they are wired;
- what code handles a request;
- what implementation executes a repository query;
- how cross-cutting behavior is ordered;
- which resource model applies.

without reconstructing a large invisible container.

Kora's architectural choices align around that goal.

The runtime does less.

The developer needs to know less framework-specific machinery.

These two properties reinforce each other.

## When the Spring-Like Model Is the Right Choice { #when-spring-like-is-right }

The argument should not be read as a claim that Spring-inspired models are mistakes.

They have strong advantages.

Familiarity accelerates adoption.

Broad ecosystems reduce integration work.

Multiple programming models support diverse workloads.

Container abstractions provide flexible composition.

Framework-managed platforms give organizations a coherent stack.

Migration compatibility can be strategically important.

Micronaut's success demonstrates that a Spring-familiar programming model can coexist with excellent compile-time performance characteristics.

For organizations migrating large Spring estates or teams that value a broad managed ecosystem, preserving familiar concepts can be the correct choice.

The point is narrower:

greenfield framework design should not assume that familiarity is always worth preserving.

## When Kora's More Radical Model Is Attractive { #when-kora }

Kora becomes particularly attractive when the application is greenfield and the team is free to optimize around modern JVM capabilities.

If the service primarily needs HTTP, JDBC or direct database access, Kafka, gRPC, configuration, resilience, telemetry, validation, scheduling, and testing, Kora can provide that surface without introducing a large container-centric mental model.

It is especially compelling when the team values:

- one primary synchronous execution model;
- Virtual Threads;
- explicit graph construction;
- compile-time failure;
- readable generated code;
- direct SQL;
- thin protocol abstractions;
- limited framework-specific knowledge;
- strong AI-assisted workflows.

In that context, Kora's refusal to reproduce familiar framework complexity can be an advantage.

## Decision Matrix { #decision-matrix }

The architectural difference can be made explicit.

| Dimension | Compile-time Spring-like model | Kora model |
|---|---|---|
| Primary goal | Preserve familiar framework model with lower runtime cost | Reduce runtime cost and framework model together |
| DI | Compile-time bean definitions/context | Compile-time explicit application graph |
| AOP | Proxies generated ahead of time | Generated wrappers/subclasses exposed as source |
| Familiarity | Spring/Grails-style concepts reduce migration friction | Standard JVM/backend concepts remain familiar |
| Execution styles | Often multiple supported models | One primary synchronous Virtual-Thread path |
| Data | Broad repository/persistence platform | Thin generated repositories with explicit control |
| Framework surface | Broad managed ecosystem | Focused backend surface |
| Cognitive model | Container concepts remain important | Ordinary types and generated code emphasized |
| Runtime | Lean and precomputed | Lean and precomputed |
| AI advantage | Familiar APIs plus compiler metadata | Smaller solution space plus inspectable generated code |
| Governance | Teams may still define preferred subset | Framework already narrows the default path |

The table shows why “both are compile-time” is not the end of the comparison.

The implementation strategy may be similar.

The conceptual architecture can still be very different.

## The Real Question Is What Survives After Optimization { #what-survives }

Once runtime scanning, reflection, and dynamic proxy creation are removed, a framework has an opportunity to ask what remains.

Do multiple execution models still need equal status?

Do all container semantics still justify their cognitive cost?

Should application composition still revolve around a bean context?

Should broad framework abstractions continue to sit between developers and standard backend technologies?

Should migration familiarity outrank directness for greenfield systems?

These questions are harder than optimizing startup.

They require removing things.

Frameworks are naturally good at adding capabilities.

Kora's more unusual characteristic is that it treats omission as part of architecture.

## The Next Step After Optimization Is Subtraction { #optimization-to-subtraction }

The history of framework engineering often follows a predictable pattern.

First, a useful abstraction is created.

Then more use cases appear.

The framework adds flexibility.

The ecosystem grows.

Performance problems emerge.

The framework optimizes the implementation.

That cycle can continue indefinitely without revisiting the original abstraction.

A newer framework has an advantage: it can ask whether the abstraction itself still deserves to exist.

This is the deeper meaning of Kora's design.

Compile-time DI is not the final goal.

Compile-time AOP is not the final goal.

Generated repositories are not the final goal.

They are tools that support a simpler application model.

The larger strategy is subtraction.

## Conclusion { #conclusion }

Compile-time dependency injection and AOP are major improvements over runtime-heavy framework architectures.

They move work earlier.

They reduce reflection.

They improve startup.

They lower runtime metadata overhead.

They catch errors sooner.

They produce a better environment for GraalVM, serverless workloads, containerized deployment, and AI-assisted iteration.

Micronaut and other modern frameworks have demonstrated the value of that approach convincingly.

But compile-time processing is not the end state.

A framework can eliminate runtime reflection and still preserve a large amount of historical framework complexity. It can generate proxies ahead of time while keeping proxy semantics central. It can precompute dependency metadata while preserving container-oriented thinking. It can support many execution models efficiently while still forcing teams to choose between them. It can become extremely fast while remaining conceptually broad.

Kora's more radical bet is that modern JVM backends no longer need much of that complexity at all.

It chooses familiar Java and Kotlin over framework-specific execution models.

It chooses Virtual Threads as the primary concurrency foundation.

It chooses an explicit compile-time graph rather than making a bean container the center of the mental model.

It chooses generated wrappers that can be inspected as ordinary source.

It chooses thin abstractions around JDBC, Kafka, HTTP, gRPC, and telemetry.

It chooses one recommended path instead of many equally valid framework styles.

It chooses a focused backend surface rather than a very broad application platform.

Those choices matter because runtime optimization and conceptual simplification solve different problems.

The best modern framework should ideally solve both.

That is why the strongest conclusion is not:

> Kora compiles more things.

It is:

> **Kora deliberately leaves fewer framework concepts for the application to carry after compilation is finished.**

And that leads to the final architectural question:

> **If you are already willing to redesign the runtime architecture, why preserve so much of the old framework programming model?**

Compile-time DI and AOP solve an important part of the problem, but they are not the end state. A framework can eliminate reflection and still preserve a large amount of historical framework complexity. Kora's more radical bet is that modern JVM backends no longer need much of that complexity at all.

The next step after making the old model faster is asking whether you still need the old model.
