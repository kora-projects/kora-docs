---
title: Kora Framework Blog
description: Articles about the Kora Framework — its design, compile-time approach, practical backend development, integrations, performance, and operating JVM services in production.
search:
  exclude: true
---

# Kora Blog

Articles about the Kora Framework, its design, practical backend development, integrations, performance, and operating JVM services in production.

The blog is shared by every documentation version. Articles describe ideas and practices that apply across Kora versions; when an article depends on a particular release, it will say so explicitly.

## Articles

- [You Don't Need Kora Developers — You Need Good JVM Engineers](you-need-good-jvm-engineers.md) — why "there are no Kora developers" is the wrong objection — Kora builds on the JDBC, SQL, HTTP, and
  Java/Kotlin skills that strong JVM engineers already have.
- [You Don't Need Kora Developers — Framework Skills vs Vendor Lock-In](you-dont-need-kora-developers.md) — why the "no Kora developers on the market" objection misunderstands hiring — strong JVM
  engineers become productive in Kora quickly without framework lock-in.
- [Why Kora Instead of the Jakarta EE Model](kora-instead-of-jakarta-ee.md) — how Kora and Jakarta EE optimize for different goals: standardized portability across implementations versus direct,
  explicit, and predictable JVM backend development.
- [Why Choose Kora Over Spring for a New JVM Backend](kora-over-spring-for-backend.md) — why Kora's thinner architecture, compile-time guarantees, Virtual Thread-first model, and lower framework
  overhead make it a stronger engineering default for greenfield services.
- [Why Kora — a Compile-Time Framework for the Modern JVM](why-kora-compile-time-framework.md) — why Kora moves dependency injection, HTTP adapters, repositories, and AOP into compilation, and what
  compile-time certainty means for startup, overhead, and debugging.
- [Compile-Time Is Not Enough: Why Kora Rethinks the Framework Model](kora-rethinks-framework-model-itself.md) — why moving DI and AOP to compile time is not enough, and Kora goes further by reducing
  the amount of framework model that needs to exist at all.
- [Why Kora May Be the Right Default for Your Next JVM Backend](kora-right-default-for-backend.md) — a pragmatic argument for choosing Kora as the default JVM backend framework — compile-time
  validation, explicit architecture, Virtual Threads, thin abstractions, and low framework-specific overhead.
- [Why Kora Doesn't Need an ORM for Most Services](kora-dont-need-orm.md) — why a Kora repository over native SQL covers most backend services better than an ORM, and when an ORM is still the right
  tool.
- [Why Compile-Time Frameworks Work Well With AI Coding Agents](neuro-agent-and-kora.md) — why Kora's compile-time graph, strong typing, and generated source make it unusually well matched to AI
  coding agents.
- [Why Compile-Time Diagnostics Are a Kora Feature](compile-time-diagnostics.md) — an in-depth case for why Kora's compile-time diagnostics — validated graph, generated code, precise errors — are a
  feature, not added build complexity.
- [Where Kora Performance Comes From](kora-performance.md) — Kora's performance as a budget across compile time, startup, and runtime — generated wiring, thin abstractions, virtual threads, and the
  costs it cannot remove.
- [Virtual Threads vs Reactive](virtual-thread-vs-reactive.md) — how Kora's virtual-thread-first model compares to reactive programming across APIs, drivers, debugging, and backpressure.
- [Virtual Threads in Production](virtual-thread-in-production.md) — how virtual threads behave under production load — pinning, carrier starvation, connection pools, and overload control.
- [Virtual Threads First](virtual-thread-first.md) — why Kora is virtual-thread-first — synchronous controllers, HTTP clients, and JDBC repositories without reactive types.
- [Thin Abstractions](kora-abstractions.md) — how Kora keeps its abstractions thin — removing repetitive integration while preserving the SQL, Kafka records, gRPC stubs, and HTTP semantics you already
  know.
- [The Myth of the "Large Ecosystem"](myth-of-large-community.md) — why a large community and abundant Stack Overflow answers are not framework features, and what actually matters when evaluating a
  backend framework.
- [The Kora Framework Is Easier to Learn](kora-easier-to-learn.md) — why Kora stays close to JDBC, SQL, HTTP, and plain Java/Kotlin, so existing JVM knowledge transfers instead of being replaced.
- [The Ecosystem You Can Build](kora-extending-framework-ecosystem.md) — how Kora's thin abstractions and module model let teams integrate any Java library through the same application graph.
- [The Cost of the First Missing Integration](cost-of-missing-integration.md) — how Kora keeps unsupported-library integration cheap using typed config, module factories, lifecycle, and probes.
- [The Best Framework for AI Agents Might Be the One With the Least Magic](neuro-agent-best-native-kora-framework.md) — why the least-magic, most-explicit framework wins for AI agents — and how Kora's
  compile-time design fits that model.
- [The Application Graph as Architecture](application-graph-as-architecture.md) — why Kora's compile-time application graph is not just DI wiring but an inspectable, validated map of the system's
  architecture.
- [Testing the Same Graph You Run in Production](kora-test-graph.md) — how Kora's JUnit extension derives a test graph from the production application graph — component slices, in-graph replacements,
  typed configuration, and lifecycle.
- [Structured Concurrency in Kora Applications](structured-concurrency-in-kora.md) — how Java structured concurrency (`StructuredTaskScope`) fits Kora's synchronous virtual-thread model — fan-out,
  failure domains, deadlines, cancellation, and keeping parallelism local.
- [Kora vs Spring: A Modern JVM Backend Through the STEP Lens](kora-vs-spring-through-step-lens.md) — comparing Kora and Spring through the STEP lens — why Kora's focused, compile-time,
  Virtual-Thread-oriented model is compelling for greenfield services while Spring's breadth remains decisive for established ecosystems.
- [STEP — Simple, Transparent, Efficient, Predictable](kora-step.md) — how the STEP principles tie Kora's individual features — compile-time DI, generated code, virtual threads, telemetry — into one
  coherent design.
- [Startup vs Build Time — Why Kora Moves Work Left](kora-startup-vs-build-time.md) — why Kora shifts framework work from every startup into the build, and what that trade means for deployments,
  tests, and autoscaling.
- [Production Knowledge Is Built Into Kora](kora-production-knowledge-built-in.md) — how Kora bakes operational practice — telemetry, resilience, readiness, lifecycle — into the framework instead of
  leaving teams to assemble it.
- [Policy-Driven Infrastructure in Kora](kora-infra-and-funcs.md) — how Kora attaches resilience, caching, validation, and scheduling policy declaratively through compile-time generation.
- [Performance You Don't Need Still Saves Money and Time](kora-save-money-and-time.md) — why Kora efficiency matters even when you don't need maximum throughput — lower CPU, faster startup, smaller
  fleets, and cheaper operation.
- [OpenAPI-First Development with Kora](kora-openapi-development.md) — why contract-first OpenAPI development in Kora generates typed servers, clients, and errors from one source of truth.
- [One STEP at a Time](neuro-agents-kora-step.md) — why Kora's explicit, inspectable, fast-to-validate design makes each AI-agent iteration produce useful information instead of guesswork.
- [One Problem, One Solution](one-problem-one-solution.md) — why Kora deliberately keeps a small solution space — one canonical path per problem — and what that means for maintainability, onboarding,
  upgrades, and AI agents.
- [Observability by Design](kora-observability.md) — how Kora threads logging, metrics, and tracing through one request end to end, with consistent context across HTTP, database, clients, and
  messaging.
- [No Runtime Magic — What Kora Actually Generates](no-runtime-magic.md) — a walk through the Java and Kotlin sources Kora generates from annotations — the application graph, HTTP handlers, JSON
  codecs, repositories, and AOP proxies you can open and read.
- [Learning a Framework in the AI Era](neuro-era-learning-framework.md) — how learning shifted from memorizing framework lore to reasoning from evidence, and why Kora fits the new model.
- [Kora Skill — the Missing Layer Between Documentation and AI Agents](kora-skill-between-docs-and-agent.md) — how a Kora "skill" bridges human documentation and AI coding agents, giving agents an
  authoritative, executable view of the framework.
- [Kora Framework — Accidentally AI-Native](neuro-native-framework-kora-became.md) — why Kora's compile-time, explicit, inspectable design makes it unusually easy for AI coding agents to understand,
  modify, and verify.
- [In the AI Era, Framework Expertise Matters More Than Community Size](neuro-era-framework-matters-more-community.md) — why an explicit, inspectable framework helps AI coding agents more than a large
  community and abundant forum answers.
- [When a Million Answers Are a Warning Sign](million-answers-a-warning-sign.md) — why a huge framework Q&A corpus can be both a valuable ecosystem asset and evidence that too much framework behavior
  is difficult to derive from the system itself, and why Kora aims to reduce the number of ordinary questions.
- [How to Build Your Own First-Class Kora Module](kora-build-your-module.md) — a step-by-step guide to building a first-class Kora module with typed config, lifecycle, telemetry, and compile-time DI.
- [How an HTTP Request Travels Through Kora on Virtual Threads](http-request-throught-kora.md) — the two concurrency domains behind an HTTP request — Undertow I/O threads and virtual threads — and why
  blocking JDBC is fine.
- [Generated Code Makes Debugging More Transparent](generated-code-transparent-debugging.md) — why Kora's generated Java and Kotlin sources are an inspectable escape hatch that makes framework
  behavior easier to debug, not harder.
- [Focused Engineering Is Not NIH](kora-focused-engineering-is-not-nih.md) — why building Kora internals is not "Not Invented Here" when it fits requirements better than wrapping mature external
  libraries.
- [Fast Startup Is Not Just Developer Convenience](fast-startup-not-convenience.md) — why fast startup and time-to-readiness are production capacity properties, not just developer convenience.
- [Enterprise-Ready Without a Framework Universe](kora-enterprise-ready-without-universe.md) — why Kora can be production-ready — observability, resilience, lifecycle, security — without recreating
  every project in the Spring universe.
- [Does Compile-Time Code Generation Really Make Development Slower?](kora-compile-time-and-development-speed.md) — whether compile-time DI, repository, and mapper generation actually slow
  development, and how incremental builds and submodules keep feedback fast.
- [Documentation Maturity Is About Coverage, Structure, and Signal](kora-documentation-maturity.md) — why documentation quality depends on coverage, structure, and signal — not framework age or page
  count.
- [Documentation in the AI Era](kora-documentation-in-the-ai-era.md) — why documentation, generated source, and compiler feedback form one explainable system in Kora for the AI era.
- [Do Production Services Really Need a Dynamic Application Graph?](kora-dynamic-runtime-refresh.md) — how Kora keeps the application graph static while supporting runtime refresh, feature flags, and
  dynamic routing where they belong.
- [Component vs Integration vs Black-Box Tests](kora-testing-different-approaches.md) — what each test layer proves, and how to place each test at the cheapest boundary that can prove it.
- [Compile-Time DI at Scale](compile-time-di-at-scale-kora.md) — how Kora uses `@KoraSubmodule` and Gradle modularization to keep compile-time dependency injection fast in large codebases.
- [Compile-Time Dependency Injection](compile-time-dependency-injection.md) — how Kora resolves, validates, and generates the application graph at compile time — components, modules, tags, `All<T>`,
  `ValueOf<T>`, lifecycle, and refreshable subgraphs.
- [Compile-Time AOP Without Dynamic Proxies](kora-aop.md) — how Kora implements aspect-oriented programming with generated compile-time subclasses instead of runtime dynamic proxies.
- [A Strong Default Is Not Lock-In](kora-strong-default-not-lock-in.md) — why Kora's opinionated defaults are extensible — replace generated components and add integrations through the same
  application graph.
- [Why Kora May Be the Best Kind of Framework for Kotlin](kora-may-be-best-for-kotlin.md) — why Kora combines Kotlin's strongest language features with KSP-based compile-time processing, synchronous framework contracts, and Virtual Threads — keeping Kotlin as Kotlin instead of adding a Kotlin-specific backend universe.
- [A Compile-Time Framework Does Not Mean Compile-Time-Only Libraries](compile-time-not-libraries.md) — why Kora's compile-time model does not forbid ordinary JVM libraries that use reflection,
  proxies, or runtime metadata.
- [The Price of a "PhD in Spring": What Kora Tries to Remove From the JVM Framework Experience](talk-joker-phd-in-spring-talk.md) — a written companion to a talk challenging how much
  framework-specific knowledge a developer should be expected to carry.
- [Kora in Practice: What a Real JVM Framework Benchmark Revealed](talk-benchmark-others-and-kora.md) — a written companion to a talk in which a developer with no prior Kora experience benchmarked
  Kora against familiar JVM frameworks.
- [Beyond "Spring Magic": Why Kora Was Designed Around Transparency, Compile-Time Guarantees, and Lower Cognitive Load](talk-jvm-day-cognitive-load.md) — a written companion to a JVM Day 2024 talk
  about transparency, compile-time guarantees, and cognitive load.
- [Why Kora Was Built: A Look Back at the Pre-1.0 Architecture, Benchmarks, and the Ideas That Survived Into Modern Kora](talk-kora-why-build-pre-1.0-origin.md) — a written companion to a pre-1.0 talk
  covering the early architecture, the benchmarks, and the ideas that survived into modern Kora.
