---
title: "Beyond “Spring Magic”: Why Kora Was Designed Around Transparency, Compile-Time Guarantees, and Lower Cognitive Load"
date: 2024-08-31
description: This article is a written companion to a talk given at JVM Day 2024 about transparency, compile-time guarantees, and cognitive load. It summarizes the talk's key ideas and how they map onto modern Kora.
search:
    exclude: true
---

# Beyond “Spring Magic”: Why Kora Was Designed Around Transparency, Compile-Time Guarantees, and Lower Cognitive Load { #beyond-spring-magic }

**August 31, 2024**

This article is a written companion to a talk given at JVM Day 2024 about transparency, compile-time guarantees, and cognitive load. It summarizes the talk's key ideas and how they map onto modern
Kora.

<iframe width="100%" height="480" src="https://www.youtube.com/embed/784mbUzs6vU" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

This talk approaches Kora from a different angle than a typical framework presentation. It is not primarily a benchmark talk, and it does not begin with a list of modules or performance numbers.
Instead, it asks a more uncomfortable question: **how much framework-specific knowledge should a backend engineer be required to carry in their head simply to use the framework correctly?**

The presentation was given at JVM Day 2024, so it reflects the Kora 1.x-era rather than today's Kora 2.0 line. That historical context matters. Some APIs, integrations, testing details, documentation
structure, and implementation choices have evolved since the talk, and Kora 2.0 is considerably more mature and opinionated than the version being discussed here. But the central ideas are directly
recognizable in modern Kora: compile-time dependency injection, generated readable source, one recommended path for common problems, explicit configuration, thin abstractions, direct SQL, fast test
startup, and a preference for ordinary Java and Kotlin language mechanisms over framework-specific runtime behavior.

The speaker's argument begins with Spring, but the talk is not simply an attack on Spring. Spring is used as the reference point because it is the dominant JVM backend framework and because its long
history makes it an excellent example of what happens when a framework accumulates many generations of features, compatibility layers, programming styles, conventions, and hidden rules. The thesis is
that some of this flexibility gradually becomes cognitive overhead for application developers.

Kora was created as an attempt to solve a narrower problem: give backend engineers a productive framework while reducing the amount of framework-specific knowledge they need to memorize.

The contrast can be summarized like this:

```text
Framework-specific expertise grows
        ↓
more conventions
more hidden rules
more runtime behavior
more edge cases
more "you just need to know this"
        ↓
developer attention moves away
from the business problem
```

Kora tries to push in the opposite direction:

```text
Java / Kotlin language rules
        +
compile-time generation
        +
explicit application graph
        +
inspectable source
        ↓
less framework-specific memory
        ↓
more attention available
for application engineering
```

That is the real subject of the talk.

## Dependency Injection Should Not Require a Style Guide to Stay Safe { #dependency-injection-should-not-require-a-style-guide-to-stay-safe }

The presentation begins with dependency injection because DI is one of the most basic framework capabilities and therefore a useful test of framework complexity.

In Spring, several injection models are historically possible. Constructor injection, field injection, setter injection, XML-based configuration, qualifier-based injection, bean-name-based resolution,
and other patterns have all existed across different generations of the ecosystem. Most modern Spring teams have converged on constructor injection as the preferred approach, but the framework itself
still has to understand and support the broader model.

The speaker's point is subtle: the fact that a team *chooses* constructor injection does not mean the framework guarantees constructor injection. The responsibility shifts to conventions, code review,
linters, team education, and senior developers who must prevent less desirable patterns from entering the codebase.

The theoretical flexibility looks like this:

```text
Spring DI
├── constructor injection
├── field injection
├── setter injection
├── name-based resolution
├── qualifier resolution
├── XML configuration
└── historical variations
```

But many production teams effectively want:

```text
Team standard
└── constructor injection
```

Kora chooses to make the narrower model the framework model itself. Dependency injection is constructor-based. There is no need for the team to repeatedly teach developers which of several supported
mechanisms is considered acceptable internally.

This is one of the recurring themes of the presentation: **a framework can reduce cognitive load not only by adding capabilities, but also by refusing to expose unnecessary choices.**

The speaker is not arguing that setter injection is technically impossible to understand. The argument is organizational. Every framework-supported alternative becomes something a team may have to
discuss, prohibit, review, or explain.

## Type-Safe Qualification Instead of String-Level Knowledge { #type-safe-qualification-instead-of-string-level-knowledge }

The same argument is applied to qualified dependency injection.

Spring supports qualifiers, but the ecosystem also contains patterns where bean names or strings become part of resolution. Teams often solve this with custom qualifier annotations or constants. This
is workable, but it creates another framework-specific convention developers have to learn.

Kora uses typed tags to distinguish dependencies. The tag is represented through normal Java types rather than arbitrary names. This allows the IDE, compiler, refactoring tools, and navigation
features to participate naturally.

The difference is conceptually small:

```text
String-like framework identity
        ↓
"which name is this bean?"
```

versus:

```text
Type-level identity
        ↓
"which tagged component is this?"
```

But the effect compounds over time. Renames become safer. Navigation becomes easier. Refactoring requires less framework-specific tooling. Developers can use ordinary language and IDE capabilities
rather than memorizing another namespace controlled by the container.

This is one of the strongest examples of Kora's design philosophy: if a normal language feature can solve the problem, prefer the language feature over a framework-specific parallel mechanism.

## Lifecycle Is Where “Simple” Framework Features Become Hidden Knowledge { #lifecycle-is-where-simple-framework-features-become-hidden-knowledge }

The talk then moves to component lifecycle.

At first glance, lifecycle seems simple: construct an object, initialize it, use it, and eventually destroy it. Spring supports familiar mechanisms such as `@PostConstruct`, destruction callbacks,
lifecycle interfaces, and other extension points. The problem emerges when several of these mechanisms interact with inheritance, AOP, proxies, container callbacks, and framework-specific ordering.

At that point, even experienced Spring developers may not know the exact order in which initialization methods execute, whether a given aspect applies to a lifecycle callback, or which object—the
target or proxy—is involved at a specific phase.

The speaker's criticism is not that Spring has no lifecycle documentation. It is that understanding the complete behavior can require knowledge that is neither obvious from the Java source nor
naturally derived from the language.

This produces what the talk repeatedly calls "secret knowledge": rules that experienced developers know because they have already been burned by them, but which a new developer cannot infer simply by
reading the class.

Kora's lifecycle model tries to keep the structure closer to ordinary code. If a parent initialization method should run, normal inheritance and `super` calls can express that relationship. If an
AOP-generated subclass exists, the implementation is generated as readable source and can be opened directly.

The intended debugging path becomes:

```text
Question:
"Does this aspect run here?"

        ↓

Open generated subclass

        ↓

Read actual implementation

        ↓

Know the answer
```

Instead of:

```text
Question:
"Does this aspect run here?"

        ↓

remember framework lifecycle rules
        ↓
remember proxy rules
        ↓
remember version-specific behavior
        ↓
search documentation / article / issue
```

That distinction—**inspect instead of memorize**—is arguably the most important theme in the entire presentation.

## Generated Source Is Not an Implementation Detail { #generated-source-is-not-an-implementation-detail }

Kora's heavy use of annotation processors and code generation is often discussed as a performance feature. In this talk, however, the more important argument is transparency.

The framework generates ordinary Java or Kotlin source for dependency graphs, AOP wrappers, JSON readers and writers, repositories, HTTP adapters, and other infrastructure. That generated code is
intended to be understandable.

The speaker emphasizes that if a developer is unsure how something works, they can simply open the generated class.

This changes the relationship between application code and framework behavior:

```text
Runtime-heavy framework

source
  ↓
annotations
  ↓
framework internals
  ↓
runtime proxy / reflection / metadata
  ↓
behavior
```

versus:

```text
Kora

source
  ↓
annotations
  ↓
generated source
  ↓
normal compiler
  ↓
behavior
```

The generated layer acts as an executable explanation.

That is useful for debugging, but it also reduces the amount of framework knowledge developers must retain. The framework does not need to explain every interaction through prose if the exact
implementation for the current application is sitting in the generated-sources directory.

This principle remains central in modern Kora 2.0. The current framework has matured significantly beyond the 2024 version described in the talk, but readable generated source is still one of its
defining characteristics.

## Compile-Time DI Turns Container Errors Into Compiler Errors { #compile-time-di-turns-container-errors-into-compiler-errors }

The dependency graph itself is generated at compile time. This means missing dependencies are discovered during compilation rather than when the application starts.

The difference sounds small until it is placed into a development workflow:

```text
Runtime graph validation

write code
   ↓
compile
   ↓
package
   ↓
start application
   ↓
container builds graph
   ↓
missing bean
```

versus:

```text
Kora graph validation

write code
   ↓
compile
   ↓
graph cannot be built
   ↓
compiler error
```

The second model shortens the feedback loop and moves structural application errors into the same phase where ordinary type errors are detected.

The speaker also explicitly contrasts Kora with runtime dynamic proxies and bytecode generation. Kora's intent is to generate readable source at compile time rather than create opaque behavior later.
Again, performance is part of the motivation, but developer understanding is equally important.

## Modules Are Explicit Composition, Not Invisible Discovery { #modules-are-explicit-composition-not-invisible-discovery }

Kora modules are presented as interfaces containing factory methods that contribute components to the dependency graph. The application explicitly connects external modules through ordinary language
constructs.

This gives the developer direct control over what enters the application.

The composition model is roughly:

```text
Application
├── configuration module
├── HTTP module
├── JSON module
├── database module
├── telemetry module
└── application modules
```

If a capability is needed, its module is added. If it is not needed, it is not added.

The speaker contrasts this with broad runtime auto-discovery, where adding a library to the classpath may cause additional framework behavior to appear automatically.

The Kora philosophy is that explicit composition is not undesirable boilerplate if it makes the final application structure obvious.

This idea became even more developed after the talk. Kora 2.0 has a broader and more mature module surface than the 2024 framework, but the principle remains the same: modules are opt-in and the
application graph remains explicit.

## Configuration Should Make the Safe Case the Default { #configuration-should-make-the-safe-case-the-default }

The talk then examines application configuration.

In many frameworks, determining whether a configuration property is required can involve validation modules, annotations, binding conventions, and framework-specific rules. Developers must remember
which validation annotation is appropriate and how it behaves.

Kora uses configuration interfaces whose required values are represented naturally through method contracts. Defaults can be expressed with default interface methods.

The basic shape is:

```java
interface ClientConfig {
    String host();

    int port();

    default Duration timeout() {
        return Duration.ofSeconds(2);
    }
}
```

Conceptually:

```text
required method
    → required configuration

default method
    → default configuration value
```

The speaker's broader point is that the type system and language syntax should communicate as much as possible before framework-specific annotations are introduced.

This is a recurring pattern throughout the talk: use the language first, framework metadata second.

## HTTP: Generate From the Contract, Prefer OpenAPI as the Source { #http-generate-from-the-contract-prefer-openapi-as-the-source }

Kora supports declarative HTTP controllers and clients, but the speaker goes further and describes OpenAPI-first development as the preferred approach.

Instead of manually writing a controller contract and later trying to keep external clients synchronized with it, the team prefers:

```text
OpenAPI specification
        ↓
generate server contract
        ↓
implement application logic
        ↓
share specification
        ↓
generate clients
```

This has a different philosophy from treating OpenAPI as documentation generated after implementation.

The API contract becomes a source artifact rather than a side effect.

This approach reduces semantic drift between server and clients and gives other teams a machine-readable description they can consume directly.

Modern Kora has expanded its OpenAPI generator significantly since this JVM Day 2024 talk, but the conceptual preference remains recognizable.

## JSON Without Runtime Reflection { #json-without-runtime-reflection }

JSON serialization is another example where the talk connects transparency and performance.

A reflection-based JSON mapper needs to inspect model structure dynamically. Kora instead generates typed JSON readers and writers during compilation.

For a model:

```text
User
├── id
├── name
└── email
```

the processor can generate code that directly reads and writes the known fields without rediscovering the structure at runtime.

The talk claims that even a relatively simple operation can produce a meaningful performance improvement, and that the benefit grows as models become larger because serialization and deserialization
are CPU-bound work.

The important architectural point is not the exact percentage quoted in the presentation. It is that the framework already knows the model structure during compilation, so it can generate specialized
code rather than repeatedly interpreting metadata at runtime.

The same logic appears throughout Kora:

```text
known at compile time?
        ↓ yes
generate specialized code
        ↓
do less generic work at runtime
```

## Database Access: Keep SQL Visible { #database-access-keep-sql-visible }

The database section reinforces the same preference for transparency.

Kora supports generated repositories but deliberately avoids making ORM the central persistence model. Repository interfaces contain explicit SQL, and Kora generates the repetitive execution and
mapping code.

The speaker acknowledges the obvious objection: if a model has many fields, manually writing every column becomes unpleasant. Kora addresses this with SQL macros that expand model fields during
compilation.

So the desired result is not:

```text
write all boilerplate manually
```

It is:

```text
write actual database intent explicitly
        +
generate repetitive mapping mechanics
```

The model becomes:

```text
Repository contract
      ↓
explicit SQL + compile-time macros
      ↓
generated repository
      ↓
database driver
```

Developers still know which indexes, joins, columns, predicates, and database-specific features their code uses.

The talk explicitly presents this as an alternative to ORM opacity. The speaker's position is that database behavior is too important to production performance to hide behind a sophisticated object
model that may generate queries developers did not expect.

Whether every team agrees with that position is another question, but it is internally consistent with Kora's broader philosophy.

## Compile-Time Macros Preserve Explicit SQL Without Repetitive Lists { #compile-time-macros-preserve-explicit-sql-without-repetitive-lists }

The macro system is particularly important because it shows how Kora tries to avoid turning transparency into boilerplate.

A naive explicit SQL model might require:

```sql
INSERT INTO users (id,
                   first_name,
                   last_name,
                   email,
    ...)
```

for every repository.

With large models, this becomes unpleasant and error-prone.

Kora's macros expand parts of the SQL based on the method's parameter or return types during compilation. This keeps the resulting SQL explicit while removing repetition.

The speaker also notes that teams can define reusable abstract repository contracts for common CRUD-style operations and inherit from them, with macros still being resolved during compilation.

This is an important pattern:

> automate repetition without moving the important behavior into an opaque runtime layer.

## Telemetry Is Treated as a Production Baseline { #telemetry-is-treated-as-a-production-baseline }

The presentation briefly covers telemetry, but the inclusion itself is revealing.

Kora supports logging, metrics, tracing, and readiness/liveness probes through dedicated modules. The speaker mentions Prometheus-compatible metrics and OpenTelemetry-based tracing as part of the
expected production environment.

The framework model is intentionally modular: teams add the telemetry modules they need, and instrumentation for major integrations participates in the same application graph.

At the time of this 2024 talk, Kora's telemetry stack was already considerably more mature than in the very early pre-1.0 presentations. Since then, the 1.2.x line continued to improve telemetry
configuration and tags, and Kora 2.0 further consolidated observability as part of the production runtime model.

## Testing Is Where Cognitive Load Becomes Expensive { #testing-is-where-cognitive-load-becomes-expensive }

A large portion of the talk is devoted to testing because testing amplifies framework complexity.

Application code may be written once and read occasionally. Tests are created, modified, executed, debugged, and maintained continuously. If framework test infrastructure is difficult to reason about,
the cost is multiplied across every developer and CI run.

The speaker criticizes Spring's testing model not because Spring lacks testing tools, but because it has many of them. Developers must reason about test context caching, configuration discovery,
mocks, transactions, application context reuse, annotations, and the interaction between different test slices.

The central complaint is that a test can begin to require substantial knowledge about the test framework rather than the behavior under test.

Kora's test philosophy is intentionally simpler.

The talk describes the test container as being derived from what the test explicitly declares. If a component appears in the test, it participates. If a dependency is declared as a stub, it is a stub.
Test configuration is the configuration explicitly provided for that test.

Conceptually:

```text
What the test declares
        =
what the test graph contains
```

The speaker calls this essentially a "what you see is what you test" model.

By default, the application graph is recreated for each test method, giving tests an isolated container. If context reuse is actually needed, JUnit lifecycle configuration can be used deliberately
rather than relying on complex implicit caching rules.

The rationale depends heavily on Kora's fast startup. If constructing an application graph is cheap, aggressive context caching becomes less necessary.

This is another area where modern Kora has matured further since the talk. The current testing model provides graph modification and component replacement while preserving the same core principle:
tests operate on the real Kora graph rather than on an unrelated hidden test container.

## Fast Integration Tests Change the Testing Trade-Off { #fast-integration-tests-change-the-testing-trade-off }

The speaker argues that when a framework starts quickly, integration testing becomes cheaper.

A traditional reason to mock aggressively is that bringing up a real application context is expensive. If startup is cheap, teams can use Testcontainers and black-box or integration-style testing more
frequently without making the feedback loop intolerable.

The intended progression is:

```text
fast framework startup
        ↓
cheap real application graph
        ↓
more realistic integration tests
        ↓
less framework-specific test setup
```

This does not mean every test should be an integration test. The point is that framework startup should not force developers into artificial test architecture.

## The Talk's Real Enemy Is Cognitive Load { #the-talk-s-real-enemy-is-cognitive-load }

After discussing concrete Kora features, the presentation becomes more philosophical.

The speaker argues that long-lived frameworks accumulate not only features but also historical behavior. Old APIs remain for compatibility. Several ways to solve the same problem coexist. Some are
technically supported but no longer recommended. Others have subtle interactions. Senior engineers gradually learn these patterns and then teach them to newer developers.

The problem is not that any single rule is impossible to learn.

The problem is the total context.

A developer working with a mature framework may need to remember:

```text
which injection style is acceptable
which lifecycle callback runs first
when a proxy exists
whether self-invocation crosses the proxy
how @Transactional behaves
which configuration mechanism is current
which test context is cached
which annotation combination is safe
which workaround applies to this version
```

Each item is manageable.

Together they become a parallel body of knowledge that competes with the business problem for attention.

Kora's stated goal is to remove as much of that knowledge as possible.

## “Magic” Is Often Another Name for Hidden Rules { #magic-is-often-another-name-for-hidden-rules }

One of the most provocative sections examines the word "magic."

Framework communities often use "magic" positively to describe behavior that appears automatically. The speaker asks what that word really means in an engineering context.

If developers cannot derive behavior from the source and must simply remember how the framework works, "magic" may be a friendly name for hidden rules.

The talk's argument is deliberately rhetorical, but the underlying point is serious:

```text
"magic"
   often means
"behavior not obvious from local code"
```

and therefore:

```text
hidden behavior
        ↓
must be documented or memorized
        ↓
framework-specific expertise
```

Kora tries to replace this with code that can be followed.

If something is unclear, inspect generated source. If a component is missing, let the compiler complain. If a dependency is required, put it in the constructor. If a lifecycle relationship exists,
express it through ordinary code where possible.

The framework should reduce the number of things that must be accepted on faith.

## The Quantity of Community Knowledge Is Not Automatically Documentation Quality { #the-quantity-of-community-knowledge-is-not-automatically-documentation-quality }

The speaker then challenges another common assumption: a huge community and millions of answers automatically mean a framework is easier to use.

Spring unquestionably has enormous community knowledge. But the talk asks why so many basic questions still require searching external articles, Baeldung, Stack Overflow, conference talks, source
code, or old GitHub issues if the framework is supposedly simple.

The provocative conclusion is that community knowledge can be both a strength and evidence of complexity.

A large ecosystem means someone has probably solved the problem before.

But needing to search for trivial framework behavior repeatedly is not necessarily desirable.

The speaker argues that official documentation should contain enough information for normal usage, while deeper behavior should remain inspectable from code.

The desired developer journey is:

```text
official docs
     ↓
working example
     ↓
generated source if necessary
```

rather than:

```text
official docs
     ↓
search engine
     ↓
Stack Overflow
     ↓
blog from another version
     ↓
GitHub issue
     ↓
try five answers
```

This argument strongly anticipates the documentation philosophy Kora later developed. Modern Kora now has substantially broader English and Russian documentation, guides, runnable examples, and
generated-source transparency compared with the 2024 state reflected in the talk.

## More Articles About a Framework Can Mean More Framework-Specific Complexity { #more-articles-about-a-framework-can-mean-more-framework-specific-complexity }

The presentation intentionally questions the assumption that a vast number of "Spring internals" talks is purely positive.

If developers need entire conference sessions to explain the surprising behavior of one annotation such as `@Transactional`, the speaker asks whether this should really be viewed as evidence of
simplicity.

This is not a claim that deep technical talks are bad. The point is that **the amount of explanation a framework requires is itself a cost**.

The ideal framework does not need a separate body of folklore for ordinary operations.

It should be possible to understand common behavior from the application source, official documentation, and generated implementation.

## IDE Plugins Are Another Signal of Hidden Complexity { #ide-plugins-are-another-signal-of-hidden-complexity }

The talk also points to specialized IDE support.

A framework can become complex enough that developers rely on dedicated plugins or commercial IDE features to understand wiring, navigation, or runtime behavior.

Good tooling is valuable, but the speaker asks whether the tooling is compensating for a model that is difficult to follow with standard language constructs.

Kora tries to make ordinary IDE capabilities more useful by representing relationships as types and generated source.

If dependency identity is expressed through Java types rather than strings, navigation works. If the implementation is generated as source, "Go to definition" works. If the graph is compiled, compiler
diagnostics work.

The framework leverages the language toolchain rather than building a parallel semantic universe.

## Kora's Goal Is Not to Be Discussed Everywhere { #kora-s-goal-is-not-to-be-discussed-everywhere }

One of the most interesting philosophical claims in the talk is that Kora's maintainers do not necessarily want millions of questions, articles, and troubleshooting discussions.

From a marketing perspective, a large amount of community content is usually considered an unquestioned success.

The speaker offers a different objective:

> the best outcome is that developers can use the framework effectively without needing to talk about the framework very much.

In other words, Kora should be boring.

The developer should solve business problems rather than spend time mastering framework puzzles.

The desired interaction is:

```text
need feature
    ↓
read concise docs / example
    ↓
write obvious code
    ↓
continue with business task
```

That is a very different success metric from maximizing framework mindshare.

## This Matters Especially for Junior Developers and Interns { #this-matters-especially-for-junior-developers-and-interns }

The team operates in an organization that hires and trains many junior engineers and interns. The speaker therefore treats onboarding cost as a real platform metric.

A framework that requires experienced developers to repeatedly teach unwritten rules consumes the time of both the new engineer and the senior engineer.

Kora tries to use the compiler, types, and one recommended programming model to guide less experienced developers toward acceptable code.

The ideal framework becomes an architectural constraint that reduces the number of bad choices rather than a toolbox containing many choices that the team must police manually.

This is the same "one problem — one solution" principle that appears elsewhere in Kora's design.

## There Is No Single “Kora Feature” { #there-is-no-single-kora-feature }

Toward the end of the talk, the speaker addresses the common question: what is Kora's killer feature?

The answer is that there is no single one.

Kora is presented as an accumulation of improvements across many dimensions:

```text
less framework-specific knowledge
+ simpler DI
+ generated source
+ compile-time validation
+ explicit configuration
+ direct SQL
+ generated mappings
+ fast startup
+ efficient runtime
+ simpler testing
+ integrated telemetry
+ better resource utilization
```

No single item necessarily justifies changing a technology stack.

Together they change the developer and operational experience.

This is an important positioning point. Kora does not claim that compile-time DI alone is revolutionary or that generated JSON serialization alone changes backend development. The value comes from
consistency across the framework.

## Kora Does Not Claim to Replace Spring Everywhere { #kora-does-not-claim-to-replace-spring-everywhere }

The speaker explicitly rejects the idea that Kora must become a universal Spring replacement.

If Spring works well for an application and the team does not experience the problems discussed in the presentation, there is no reason to migrate merely because Kora exists.

Kora's goal is narrower: efficiently solve a defined class of backend service problems with a transparent model and low framework overhead.

This is also why the team did not simply select Micronaut or Quarkus. In their assessment, those frameworks solved some dimensions—such as startup and build-time optimization—but not the entire
combination of concerns they wanted to address.

That combination mattered more than any individual benchmark or feature.

## Production Adoption Was Already Significant { #production-adoption-was-already-significant }

One of the most concrete claims near the end of the talk is about internal adoption.

At the time of the presentation, the speaker says there were **more than 400 Kora services** in the company's infrastructure and that approximately **two new Kora services were being created each day
**.

Those numbers should be understood as historical figures reported during the JVM Day 2024 talk, not as current fleet statistics. But they are important because they counter the idea that Kora was
merely an experimental framework developed by a central platform team.

According to the speaker, adoption was largely developer-driven. Teams came to Kora because they were dissatisfied with the complexity or resource profile of their existing tooling or because they
believed they could improve engineering efficiency.

The adoption pattern described in the talk can be visualized simply:

```text
Reported internal Kora adoption at the time of the talk

Existing services   > 400
New services/day    ~ 2

400+ services
████████████████████████████████████████

Daily growth
Day 1   ++
Day 2   ++
Day 3   ++
...
```

The numbers are not presented as a global market-share claim. They show that Kora had already moved beyond the "internal experiment" stage inside the organization.

## The Framework Was Already Being Chosen, Not Merely Mandated { #the-framework-was-already-being-chosen-not-merely-mandated }

The speaker is also careful to address a predictable criticism: perhaps developers were forced to use an internal framework.

His claim is the opposite. Teams were selecting Kora because they saw practical benefits.

That claim is important to the narrative because it supports the broader thesis that developer experience matters as much as benchmark performance. A framework that saves CPU but frustrates developers
would not spread voluntarily.

The Kora proposition is that compile-time restrictions and fewer programming models actually make development easier once the team becomes familiar with the framework.

## A Note on the Historical Version: This Is Kora 1.x, Not Kora 2.0 { #a-note-on-the-historical-version-this-is-kora-1-x-not-kora-2-0 }

Because the talk dates to JVM Day 2024, it predates the current Kora 2.0 generation. The framework being discussed is already much more mature than the pre-1.0 Kora shown in earlier talks, but it is
still not modern Kora 2.0.

Several principles survived unchanged:

```text
compile-time DI
generated readable code
thin abstractions
explicit SQL
typed configuration
Java + Kotlin
OpenTelemetry
opt-in modules
fast startup
transparent tests
```

Other areas evolved considerably.

Kora 2.0 consolidated the programming model around ordinary synchronous Java/Kotlin contracts executed on virtual threads and removed reactive/suspend framework contracts. The HTTP, repository,
scheduling, testing, documentation, and application graph models have all undergone further refinement. The current documentation and examples are much broader than what was available at the time of
this talk.

A useful historical progression is:

```text
Early Kora
    ↓
prove compile-time / generated-source architecture

Kora 1.x
    ↓
expand production surface
stabilize integrations
grow internal adoption
improve tests / OpenAPI / telemetry / tooling

Kora 2.0
    ↓
simplify again around a mature
virtual-thread-first synchronous model
```

The 2024 presentation is therefore best understood as a mature explanation of *why* Kora's architecture exists, even though the framework has continued to change.

## The Deeper Message: Framework Knowledge Should Be Disposable { #the-deeper-message-framework-knowledge-should-be-disposable }

The strongest idea in the talk is larger than Spring or Kora.

Framework knowledge has low transfer value when it consists of accidental rules.

Knowing HTTP is transferable.

Knowing SQL is transferable.

Knowing the JVM memory model is transferable.

Knowing Kafka group rebalancing is transferable.

Knowing how transactions behave is transferable.

Knowing exactly which combination of framework annotations creates a proxy in one version of one framework is far less transferable.

Kora tries to bias engineering knowledge toward the first category.

This does not mean Kora has no concepts of its own. Of course it does. Developers still need to understand modules, graph components, generated code, configuration, tags, telemetry, repositories, and
test facilities.

The ambition is that these concepts remain small and predictable enough that they do not become a separate profession.

## Conclusion { #conclusion }

This JVM Day 2024 talk is less about Kora's feature list than about the cost of framework complexity.

Spring is used throughout the presentation because it is a powerful example of what twenty years of evolution can produce: extraordinary capability, enormous community knowledge, extensive integration
coverage, and at the same time a large amount of historical behavior that developers must understand to use the framework confidently.

The speaker's criticism is not that this history makes Spring unusable. The criticism is that framework complexity consumes developer attention. Constructor injection conventions, lifecycle ordering,
qualifier rules, proxy behavior, transaction semantics, context caching, testing annotations, configuration binding, and other framework details each add a small amount of cognitive load. Over years
of development, the total can become substantial.

Kora's answer is to make the framework smaller conceptually even when the feature surface is broad.

Use constructor injection only.

Use typed tags rather than string identity.

Use language inheritance where inheritance is needed.

Generate AOP subclasses rather than hiding proxy behavior.

Generate the dependency graph and fail compilation when it cannot be satisfied.

Generate JSON readers and writers rather than rediscovering model structure at runtime.

Generate repository implementations while keeping SQL explicit.

Prefer OpenAPI as a shared contract.

Make test graphs reflect exactly what the test declares.

Keep telemetry and production modules opt-in.

And when developers want to know what the framework did, let them open the generated code.

This creates a very different optimization target:

```text
Not:
"How much can the framework do automatically?"

But:
"How much can the framework do
without forcing the developer
to memorize how it did it?"
```

That distinction is the foundation of the talk.

The presentation also shows that by 2024 Kora was no longer merely an architectural experiment. The speaker reported more than 400 internal services and roughly two new services being created each
day. Those are historical figures from the talk, but they indicate that the model had been validated well beyond small demos.

The most important statement in the presentation is therefore not about performance. It is about developer attention.

A backend engineer should spend most of their mental energy on the application: HTTP semantics, data models, SQL, consistency, concurrency, messaging, failures, observability, and business rules. The
framework should reduce repetitive work without creating a second body of knowledge that competes with those concerns.

That is what Kora was trying to optimize in the 1.x-era described here, and it remains one of the clearest threads connecting this 2024 talk with the substantially more mature Kora 2.0 framework
today.

