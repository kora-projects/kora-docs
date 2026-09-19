---
title: One Problem, One Solution — Why the Kora Framework Has Fewer Abstractions
date: 2026-08-23
description: Why the Kora Framework deliberately keeps a small solution space — one canonical path per problem — and what that means for maintainability, onboarding, upgrades, and AI agents.
search:
  exclude: true
---

# One Problem, One Solution: Why Kora Deliberately Has Fewer Abstractions { #one-problem-one-solution }

**August 23, 2026**

Modern backend frameworks are often evaluated by asking how much they can do. How many databases can they abstract? How many programming models can they support? How many ways can a controller be
declared, a dependency injected, a query expressed, or a remote service called?

The Kora Framework starts from a different question: **how many different ways should a team need to solve the same ordinary backend problem?**

That distinction is easy to miss. A framework with fewer abstractions can look less capable when judged by the size of its API surface. But API surface is not free. Every additional programming model,
compatibility layer, extension mechanism, and alternative abstraction becomes another branch in the decision tree that engineers have to understand. It becomes another convention a team has to choose,
document, review, preserve during refactoring, and eventually migrate.

Kora's design deliberately pushes in the opposite direction. Its landing page describes the framework as "Simple. Coherent. Familiar.", emphasizes a "coherent one approach across modules", and later
states the principle even more directly: **"one clear solution per problem."** The same page explains the broader philosophy: Kora does not pursue breadth for its own sake, does not try to wrap every
possible technology behind a framework-specific abstraction, and instead favors fewer competing styles, clearer contracts, and lower cognitive overhead.

This is not an argument that a broad framework such as Spring made the wrong trade-off. Spring's breadth is one of its greatest strengths. It has accumulated solutions for many architectures,
programming eras, deployment environments, libraries, and migration paths, and that flexibility is enormously valuable for a large ecosystem. Kora is optimizing for a different objective. Where Spring
often asks, *which of the supported approaches is appropriate here?*, Kora tries to make the normal answer obvious before that discussion begins.

The difference is not primarily about syntax. It is about the size of the solution space.

```text
Spring
many valid ways to solve X
        ↓
team chooses conventions
        ↓
project maintains those conventions

Kora
one recommended way to solve X
        ↓
framework conventions become team conventions
        ↓
exceptions stay explicit
```

The important word is **recommended**. Kora is not a framework with no escape hatches. Its HTTP modules expose low-level imperative APIs in addition to declarative controllers and clients. Its
dependency graph can be extended with explicit factories, modules, generic factories, and custom components. Integrations can be replaced. What Kora tries to avoid is turning every escape hatch into a
second equally prominent application programming model.

That difference has consequences far beyond aesthetics.

## Abstraction Has a Cognitive Cost { #cognitive-cost }

An abstraction usually enters a framework for a good reason. It can hide boilerplate, preserve compatibility, make several implementations interchangeable, support a different programming style, or
provide a more convenient API for a particular class of applications. Considered locally, each abstraction can be perfectly rational.

The cost appears when abstractions accumulate.

Suppose a new engineer needs to understand how an HTTP endpoint reaches a database. In a sufficiently flexible framework, the first question is not necessarily "what does this endpoint do?" It may be
a sequence of framework questions first. Is the application using the servlet stack or the reactive stack? Annotated controllers or functional routing? Blocking calls, futures, Reactor, or coroutines?
JPA, Spring Data repositories, JDBC abstractions, direct SQL, or another persistence integration? Is configuration injected through `@Value`, read from `Environment`, or mapped with
`@ConfigurationProperties`? Which injection style is used? Which conventions are local to this repository rather than inherent to the framework?

None of those options is inherently bad. Spring's own documentation makes this breadth explicit. Spring Framework maintains both Spring MVC and Spring WebFlux; WebFlux itself supports annotated
controllers and functional endpoints, while Kotlin can use coroutine APIs. Spring Boot configuration can be consumed through `@Value`, `Environment`, or type-safe `@ConfigurationProperties`. This
flexibility lets Spring fit an unusually wide range of applications and lets old and new approaches coexist.

But flexibility moves part of framework design into every application.

A team has to decide which subset is allowed. Then it has to teach that subset. Code review has to enforce it. Architecture documentation has to explain it. Static analysis may need to police it. New
code generators and AI agents have to infer it. Upgrades have to consider not only what the framework supports now, but which historical combinations the codebase accumulated over time.

This is why the number of possible solutions matters even when every individual solution is good.

If a problem has five framework-supported solutions and a system contains hundreds of places where that problem occurs, the maintenance burden is not simply "five APIs instead of one." The real burden
is architectural entropy: different teams can make different choices, old code can preserve yesterday's recommendation while new code follows today's, and generic abstractions can be layered over
framework abstractions in an attempt to hide the differences.

Kora's answer is to reduce those branches before application development begins.

## A Canonical Path, Not an Artificially Closed Framework { #canonical-path }

"One problem, one solution" is easy to interpret too literally. Real systems contain edge cases, and a framework that allows only one physical mechanism for every task would quickly become
restrictive.

Kora's actual design is more pragmatic: **provide one clear high-level path for the common case, then keep lower-level control available without presenting it as an equally preferred architecture.**

The HTTP server is a good example. Kora supports declarative controllers with `@HttpController` and `@HttpRoute`, and it can also register an imperative `HttpServerRequestHandler`. The documentation
is explicit about the intended separation: the declarative model is appropriate for most APIs, while the imperative API exists for low-level or dynamic routes where manually processing the request is
useful.

The HTTP client follows the same pattern. Declarative clients cover the normal service-to-service contract; an imperative client remains available when a request must genuinely be assembled
dynamically.

That is a very different kind of flexibility from maintaining several peer programming models. The normal path remains recognizable across projects. The exception advertises itself as an exception.

The same principle applies to extension. Kora's landing page explicitly says that applications can use only the modules they need, replace components, or build first-class modules for external
libraries. Fewer framework abstractions do not mean fewer integration possibilities. They mean that integrations are expected to enter the same application model instead of bringing an entirely
separate model with them.

This distinction is central to understanding Kora. The framework is opinionated about **how application code should look**, not closed about **what application code is allowed to integrate with**.

## Concurrency: One Synchronous Model { #concurrency }

Concurrency is probably the clearest example of the philosophy in Kora 2.

Kora executes application code synchronously on virtual threads. Controllers, HTTP clients, repositories, and scheduled tasks use ordinary blocking signatures. Kora's documentation states that its
modules do not expose reactive or `suspend` contracts; unsupported signatures are rejected by processors at compile time. When an operation needs parallelism, the recommended direction is Java
structured concurrency rather than switching the whole application into another asynchronous programming model.

That choice removes a large category of architectural branching.

The application does not need one mental model for JDBC code, another for a reactive HTTP client, another for coroutine-aware Kotlin services, and a fourth set of rules for crossing boundaries between
them. A repository can return an entity. A client can return a response. A service can call both using ordinary control flow. Exceptions behave like exceptions. `try`/`catch`, loops, local variables,
stack traces, and familiar debugging techniques remain central rather than becoming adapters around an asynchronous pipeline.

This is not a claim that reactive programming is useless. Reactive streams solve real problems and remain the right model in systems that need their semantics. Spring's WebFlux documentation itself
makes a nuanced recommendation: reactive programming is not automatically beneficial for every application, and teams should evaluate whether a non-blocking stack is actually required.

Kora simply turns that evaluation into a framework-level decision for its own modules. It chooses synchronous Java and Kotlin on virtual threads as the standard server-side model.

That has an organizational consequence: teams do not repeatedly reopen the concurrency-model debate service by service.

## Dependency Injection: One Graph You Can Inspect { #dependency-injection }

Dependency injection often looks simple in application code while hiding a surprising amount of runtime machinery underneath. Kora moves most of that machinery into compilation.

The `@KoraApp` interface defines the application assembly point. Components come from explicit sources: `@Component` classes, factory methods, connected modules, generated extensions, or other
declared graph mechanisms. External modules are not silently discovered from arbitrary runtime classpath scanning; they are connected to the application explicitly. If a dependency cannot be resolved,
the build fails instead of allowing a partially understood container to discover the problem later.

The result is not that Kora DI has only one annotation. It has a capable graph model with modules, tags, conditional components, optional dependencies, lists of components, overrides, generic
factories, lifecycle handling, and other advanced features. The reduction happens at a different level: **all of those features describe the same dependency graph, and that graph is resolved through
the same compile-time model.**

There is no conceptual switch from "normal injection" to a separate runtime container model when an application becomes larger. There is no need to treat component scanning as an invisible source of
architecture. Generated source code represents the wiring, and the compiler validates whether the graph is coherent.

That matters for maintainability because dependency injection stops being merely a convenience for obtaining objects. It becomes a statically checked representation of application structure.

When a constructor changes, the graph has to remain valid. When two candidates become ambiguous, the build has to resolve the ambiguity. When a dependency disappears, the compiler points at the
missing edge. Architectural mistakes are pulled toward the edit that introduced them.

This changes the economics of complexity: errors become cheaper because they are discovered closer to their cause.

## HTTP: Prefer the Contract Over Framework-Specific Ceremony { #http }

Kora's HTTP modules make another strong recommendation: for server and client APIs, use an OpenAPI document as the primary contract and generate the framework code from it.

Again, this is not the only technically possible way to create an endpoint. Declarative controllers and clients can be written directly, and imperative APIs exist underneath. But the recommended
direction is contract-first.

That choice eliminates another recurring team-level debate. If OpenAPI is the source of truth, the question "is the Java interface, controller annotation, generated specification, gateway definition,
or client model the real contract?" has a straightforward answer. The same description can generate server-side contracts, client-side contracts, request and response models, mappers, and
authorization-related code.

The abstraction is intentionally close to something that exists outside Kora: OpenAPI itself.

This is characteristic of the framework. Kora often prefers a standard or underlying technology as the durable concept and uses generation to remove the repetitive integration code around it. The
framework adds tooling, validation, telemetry, and wiring without trying to make the external technology disappear behind a completely separate conceptual universe.

That approach also lowers migration risk. A service contract expressed as OpenAPI is not meaningful only inside Kora. It is understandable by gateways, documentation tools, test tools, generators for
other languages, and engineers who have never used the framework.

A thin abstraction preserves knowledge.

## Data Access: SQL Is Already the Query Language { #data-access }

The database layer makes the philosophy even more explicit. Kora's documentation says that the preferred way to communicate with a SQL database is through its native SQL language.

A repository is declared as an interface, methods use `@Query`, parameters are bound by name, and Kora generates the execution and mapping code at compile time. The repository abstraction removes
repetitive JDBC mechanics, but it does not attempt to replace SQL with a new universal query language.

This matters because database abstractions can easily become abstraction stacks. An engineer can end up reasoning about an ORM's object model, a repository derivation language, a criteria API,
framework transactions, the SQL eventually generated, and the database query planner—all for one operation.

Kora deliberately collapses several of those layers. The developer writes the query the database will execute; Kora generates safe parameter binding, mapping, telemetry integration, and infrastructure
code around it.

The same common repository model is used for Kora's supported JDBC and Cassandra modules while preserving the native query language of each database. That is an important distinction. "One solution"
does not mean pretending different databases are identical. It means keeping one recognizable repository model while allowing the underlying technology to remain visible.

The framework is reducing accidental variety, not essential differences.

## Configuration: Make It a Typed Dependency { #configuration }

Configuration is another area where mature ecosystems often offer many legitimate access paths. Spring Boot, for example, can inject individual values with `@Value`, expose the `Environment`, or bind
structured `@ConfigurationProperties` objects, in addition to a rich external property-source model.

Kora's recommended application style is narrower. Define a configuration type for an integration or subsystem, mark it with `@ConfigSource`, and inject the resulting typed object like any other
dependency. Required values, nullable values, defaults, and validation live in that contract. The mapper is generated at compile time, and invalid configuration can fail during application startup
before the affected component is used.

The benefit is not that reading a string from configuration became technically easier. The benefit is that a team can answer "how do we consume configuration?" with a single pattern.

That improves locality. To understand an Orders client, an engineer can inspect `OrdersClientConfig` rather than search for string keys spread across constructors, fields, helper methods, and
environment lookups. Renaming and refactoring become type-aware. Tests can construct the configuration contract explicitly. Generated code and compiler diagnostics can participate in the same feedback
loop as the rest of the framework.

Most importantly, configuration stops being a global string-addressable side channel and becomes part of the component's declared dependency surface.

## Fewer Choices Become Team Conventions for Free { #team-conventions }

Framework flexibility and team autonomy are often treated as synonyms, but in a production codebase they are not the same thing.

Teams almost always impose conventions on top of a flexible framework:

- prefer constructor injection;
- do not use field injection;
- use `@ConfigurationProperties`, not scattered `@Value`;
- use Spring MVC unless there is a documented reason for WebFlux;
- use one HTTP client library;
- use one persistence style;
- do not introduce a second JSON mapper;
- expose contracts in one specific way;
- use one resilience library and one annotation pattern;
- avoid mixing coroutines, Reactor, and blocking code in the same call path.

These rules are sensible. The interesting question is why every organization has to rediscover and enforce them.

A framework with a smaller solution space effectively ships more of those decisions as part of the framework contract. That means less architecture has to live in a wiki, starter repository, internal
platform library, static-analysis rule set, code-review checklist, or senior engineer's memory.

This is especially valuable in organizations with many small services. Architectural inconsistency often does not hurt much inside one service. It hurts when a developer moves between twenty services
that solve the same problem differently.

If every Kora service uses the same broad shape—compile-time DI, synchronous virtual-thread execution, typed configuration, generated repositories around native queries, generated policies,
OpenAPI-first HTTP where appropriate—the cost of moving between repositories falls. Familiarity compounds.

The framework becomes part of the organization's standardization mechanism.

## Maintainability Is Mostly About Predictability { #maintainability }

Code is read much more often than it is initially written. That makes predictability more important than the convenience of having many elegant ways to express the same thing.

When there is one canonical pattern, the location of behavior becomes easier to infer. A dependency should be visible in the graph. Configuration should have a typed configuration contract. A database
operation should be in a repository and expose the native query. Cross-cutting behavior such as resilience, validation, caching, transactions, scheduling, or logging is generated through Kora's
compile-time mechanisms rather than hidden behind runtime proxies.

This narrows the amount of framework knowledge required to answer an operational question.

Where is the timeout applied? Which component provides this client? What query runs here? Where does this configuration value come from? Which code handles the HTTP request? What wraps this method?
How is the object constructed?

The more often those questions can be answered by following types and generated source instead of reconstructing runtime behavior, the cheaper maintenance becomes.

Kora's emphasis on generated human-readable source is important here. Compile-time code generation is not merely a performance optimization. It is also a transparency mechanism. Infrastructure
behavior that would otherwise live inside a reflective container, dynamic proxy, or generic runtime dispatcher can become code that an engineer can inspect.

Fewer abstractions reduce the number of concepts. Generated code reduces the amount of invisible behavior. Together they make the system easier to reason about.

## Onboarding: Learn the System Once { #onboarding }

Framework onboarding is usually described as learning an API. In practice, joining a mature project means learning two things: the framework and the team's chosen subset of the framework.

In a broad ecosystem, the second part can be larger than the first. An engineer may already know Spring and still need time to discover which Spring this organization uses: MVC or WebFlux, JPA or
JDBC, annotations or functional endpoints, which injection conventions, which testing style, which clients, which internal starters, which custom wrappers, and which legacy patterns are still present.

Kora tries to make framework knowledge and project conventions overlap much more strongly.

A developer who understands the Kora application graph, modules, generated code, typed configuration, repositories, HTTP contracts, and virtual-thread execution model can transfer that model to
another Kora service with relatively little reinterpretation. The business domain changes; the application skeleton should not change dramatically with it.

This is one reason a smaller framework can sometimes be easier to learn than a framework with more tutorials, more integrations, and more historical knowledge available. Learning cost is not only
about documentation volume. It is also about the number of mutually valid concepts a developer must distinguish.

A small decision tree can be more valuable than a large answer database.

## Upgrade Cost: Every Supported Style Is a Migration Surface { #upgrade-cost }

Framework upgrades are usually discussed in terms of binary compatibility and breaking API changes. There is another dimension: the number of programming models that an application has accumulated.

Every additional style creates another migration surface.

If one codebase uses several generations of configuration APIs, two HTTP stacks, multiple persistence abstractions, several clients, runtime proxy behavior, and adapters between blocking and reactive
code, an upgrade has to preserve or migrate all of those interactions. Even when the framework maintains backward compatibility, the application carries historical architecture forward.

A narrower model reduces the combinatorial part of upgrade work.

Kora 2 illustrates this aggressively with concurrency. Rather than carry several asynchronous contracts indefinitely, the framework standardizes its modules around synchronous virtual-thread
execution. That is a breaking philosophical choice, but once a codebase is on that model, future work happens in a smaller space. There are fewer combinations to test and fewer boundaries where
programming models meet.

Compile-time validation also moves some upgrade failures earlier. If generated contracts, injection edges, signatures, or mappings no longer fit, compilation can expose the problem before deployment
and often before tests run.

This does not make upgrades free. It makes them more mechanical.

That is an underrated framework property. The best upgrade is not necessarily the one with zero source changes; it is often the one where required source changes are explicit, searchable,
type-checked, and repetitive enough to automate.

## Why This Matters Even More for AI Agents { #ai-agents }

The same characteristics that reduce cognitive load for engineers also reduce uncertainty for AI coding agents.

An LLM working in a large framework ecosystem faces a peculiar problem: it may know several correct answers to the same question. That is useful in conversation, but dangerous in a repository. The
model has to infer which answer belongs to this particular codebase.

Should it create a Spring MVC controller or a WebFlux controller? Use `RestClient`, `WebClient`, an HTTP service interface, or a project-specific wrapper? Use `@Value` or `@ConfigurationProperties`?
Return a value, `CompletableFuture`, `Mono`, `Flux`, or a coroutine type? Add a Spring Data repository, write JDBC code, or follow an internal persistence abstraction? The model may generate valid
framework code that is architecturally wrong for the project.

More valid choices create more opportunities for locally plausible mistakes.

Kora's narrower programming model reduces that ambiguity. A repository looks like a Kora repository. Application components belong to one compile-time graph. Configuration is represented as typed
configuration. Framework modules use synchronous signatures. HTTP contracts have a preferred OpenAPI-first path. Generated source exposes what the framework actually created.

The compiler then acts as a second layer of guidance.

This is particularly important for autonomous iteration. An agent can make a change, compile, receive precise structural feedback, inspect generated code, start a fast application context, run
component or integration tests, and repeat. The Kora landing page explicitly frames this short feedback loop as useful to both newcomers and AI tools.

In other words, Kora reduces two things an agent struggles with most: **choice ambiguity** and **hidden runtime behavior**.

This does not mean an AI agent will automatically write good architecture. It means the framework supplies stronger constraints. Constraints are valuable to generative systems because they turn a
large open-ended search problem into a smaller correction loop.

For human teams, we call that convention.

For agents, it is search-space reduction.

They are the same design advantage viewed from two sides.

## The Trade-Off: Breadth Is Valuable Too { #trade-off }

A philosophy of fewer abstractions has real costs, and pretending otherwise would make the comparison unhelpful.

Spring's many programming models exist because the ecosystem has to accommodate many kinds of systems and many generations of Java applications. A team may need JPA because its domain genuinely
benefits from an ORM. It may need WebFlux because reactive streams are part of the architecture. It may need a specific library with first-class Spring integration. It may be modernizing a large
system incrementally and depend on the ability to mix old and new styles during migration.

In those situations, breadth is not accidental complexity. It is capability.

Spring also has an enormous ecosystem, vast community knowledge, long-lived compatibility expectations, and integrations for problems Kora may deliberately choose not to solve. A framework that aims
to be a tool for almost every enterprise Java situation necessarily makes different trade-offs from one that explicitly says it is "not a tool for every situation."

Kora's argument is therefore not that fewer choices are universally superior.

The argument is that **for the class of backend services Kora targets, the cost of supporting several peer solutions to the same routine problem is often higher than the value of that choice.**

That is a narrower claim, and a much more interesting one.

## Fewer Abstractions Does Not Mean Lower Level { #lower-level }

There is another misconception worth addressing. Reducing abstractions can sound like pushing boilerplate back onto application developers.

Kora generally tries to do the opposite.

It keeps high-level concepts—controllers, clients, repositories, components, configuration, resilience policies—but generates the repetitive implementation behind them. The framework is not asking
developers to manually wire every object, decode every HTTP body, bind every JDBC parameter, emit every telemetry signal, or implement every retry loop.

The difference is where complexity goes.

Instead of solving complexity with another runtime abstraction, Kora often solves it with compile-time generation.

That lets the source-level API stay small without forcing the runtime to become magical. The application expresses intent through normal types and a focused set of annotations; processors validate
that intent and generate ordinary code.

This is why Kora can simultaneously argue for high-level productivity and thin abstractions. Those goals are not contradictory if much of the adaptation work happens before the application starts.

The framework is doing work for you. It is simply trying not to make you imagine that the work does not exist.

## One Solution as an Architectural Budget { #architectural-budget }

A useful way to think about Kora's philosophy is as an **architectural budget**.

Every new abstraction spends some of that budget. To justify itself, it should solve a meaningfully different problem, not merely provide another fashionable spelling for a problem that already has a
good solution.

Every new programming model creates documentation cost. Every interchangeable API creates testing combinations. Every transparent wrapper creates another place behavior can hide. Every compatibility
layer makes removal harder later. Every alternative makes project conventions more important.

Large frameworks can afford that complexity because breadth is part of their mission.

Kora deliberately spends the budget elsewhere: compile-time analysis, generated code, strong typing, virtual-thread execution, production telemetry, OpenAPI generation, repositories, resilience, and a
focused set of integrations. The goal is not to maximize the number of concepts exposed to application developers. It is to cover the common backend path with as few concepts as possible and make
those concepts compose consistently.

That is what "one problem, one solution" means in practice.

Not that an engineer is forbidden from doing something unusual.

Not that every technology is reduced to the same generic interface.

Not that the framework can anticipate every architecture.

It means the framework should not make ordinary development a repeated architecture meeting.

For the common path, the answer should already be clear.

## Conclusion { #conclusion }

Framework design is often measured by capability: what can I build with it?

Kora adds another metric: **how many decisions does the framework force me to make before I can build it consistently?**

Spring demonstrates the power of breadth. Its ecosystem can support an extraordinary range of architectures precisely because it gives developers multiple programming models and long-lived migration
paths. Kora deliberately occupies a different point on that spectrum. It accepts less breadth in exchange for a smaller solution space.

That trade changes the day-to-day economics of a codebase. Lower cognitive load means engineers keep fewer framework branches in their heads. Strong conventions emerge without every team reinventing
them. Maintenance becomes more predictable because similar problems look similar. Onboarding becomes faster because project style and framework style overlap. Upgrades touch fewer programming models.
AI agents have fewer plausible-but-wrong choices and a compiler-generated feedback loop that can correct them quickly.

The result is not minimalism for its own sake.

It is an attempt to make framework complexity proportional to the problem being solved.

A backend framework does not need to provide every possible way to do something in order to be powerful. Sometimes the more useful form of power is to provide one very good path, make that path fast,
observable, extensible, and easy to understand—and then get out of the way.

That is the bet Kora is making.
