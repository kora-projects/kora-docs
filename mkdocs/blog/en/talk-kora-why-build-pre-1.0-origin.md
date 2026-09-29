---
title: "Why Kora Was Built: A Look Back at the Pre-1.0 Architecture, Benchmarks, and the Ideas That Survived Into Modern Kora"
date: 2023-03-06
description: This article is a written companion to a talk given before Kora 1.0. It covers the pre-1.0 architecture, the early benchmarks, and the ideas that survived into modern Kora.
search:
    exclude: true
---

# Why Kora Was Built: A Look Back at the Pre-1.0 Architecture, Benchmarks, and the Ideas That Survived Into Modern Kora { #why-kora-was-built }

**March 6, 2023**

This article is a written companion to a talk given before Kora 1.0. It covers the pre-1.0 architecture, the early benchmarks, and the ideas that survived into modern Kora.

<iframe width="100%" height="480" src="https://www.youtube.com/embed/padFJGPOvco" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

This talk captures Kora at a particularly interesting moment in its history. It is not a presentation about the mature Kora 1.2.x line, and it is certainly not a presentation about the much more
developed Kora 2.0 generation. The framework shown here is **pre-stable Kora, roughly from the 0.9-era before 1.0.0**, when APIs were still changing freely, backward compatibility was not yet
promised, several integrations that later disappeared or changed were still part of the stack, and the team was openly experimenting with what the framework should become. That historical context
matters throughout the entire article because many implementation details in the talk are no longer representative of current Kora, while the architectural principles are surprisingly recognizable.

The presentation begins not with Kora itself, but with Spring. The speaker, an engineer from the Tinkoff Core Tech team, explicitly acknowledges why Spring became so successful: it lets developers
assemble business applications quickly, it has an enormous ecosystem, it is actively developed, and almost every technology has an existing integration. The criticism is narrower and more technical.
The team was working with a growing number of small services and had become increasingly sensitive to startup cost, memory footprint, runtime indirection, dynamic proxies, bytecode generation, opaque
application wiring, and the amount of work a framework performs before the application's own business code is reached.

The question behind Kora was therefore not, “How can we invent a new Java framework?” It was closer to: **can we keep the productivity of a framework while making the runtime look much more like code
that engineers would write directly against Undertow, JDBC, Kafka, or another underlying library?** The early answer, visible in this pre-1.0 talk, was to move dependency wiring and repetitive
integration work into compile-time source generation, keep abstractions thin, and make the resulting code inspectable.

That basic direction later became much more polished. By the **1.2.x generation**, Kora had already accumulated significantly more integrations, fixes, testing support, OpenAPI capabilities, telemetry
options, configuration features, and a far more stable ecosystem than the one shown in this presentation. In the **2.0 line**, the same principles were pushed further: Kora presents a more
consolidated synchronous model, uses virtual threads throughout application code, rejects reactive and `suspend` contracts in framework modules, keeps compile-time DI and generated source as core
architectural mechanisms, and documents the framework as a much more mature production platform. The talk should therefore be read as the origin story of those ideas, not as a snapshot of current
Kora.

## Spring Solved the Productivity Problem, but Runtime Convenience Has a Cost { #spring-solved-the-productivity-problem-but-runtime-convenience-has-a-cost }

The speaker starts from a position that is deliberately balanced. Spring is productive because it removes a huge amount of manual composition work. A developer can create a service with a controller,
database access, configuration, and business logic very quickly, and Spring Boot makes this even easier by analyzing the classpath and automatically assembling what appears to be needed. For many
teams this is exactly the right trade, and the talk never argues otherwise.

The concern appears when the runtime mechanics become visible operationally. The simple demonstration service used in the talk required roughly **192 MB of memory merely to start** when built using
the normal Spring Boot path. Under CPU restrictions, startup stretched into tens of seconds. Those numbers were not intended to prove that Spring cannot be optimized lower; the speaker explicitly used
ordinary Boot modules rather than an aggressively stripped custom setup. The benchmark therefore measured the cost of the convenient default path developers are likely to use, which was precisely what
the team cared about.

Spring Boot achieves much of its convenience through auto-configuration. Conditions such as `@ConditionalOnClass` and `@ConditionalOnMissingBean` allow the framework to inspect the environment and
decide which configuration should exist. Conceptually, the system performs work like this:

```text
Classpath
   ↓
Read auto-configuration metadata
   ↓
Evaluate conditions
   ↓
Determine which configurations apply
   ↓
Discover / create beans
   ↓
Build runtime application context
```

This machinery is extremely useful, but it executes somewhere. The speaker's point was that a microservice platform running many relatively small applications pays this cost repeatedly. Even
auto-configurations that are not ultimately activated still participate in classpath and metadata analysis. The same concern applies to runtime proxying and bytecode-generated infrastructure around
transactions, interceptors, repositories, and other framework behavior. Each layer may be individually cheap, but the resulting call path can become much larger than the business method developers see
in source.

The objection in the talk is therefore not “Spring uses proxies, therefore Spring is bad.” It is that the team wanted a stronger relationship between the source code they saw and the code the JVM
actually executed. They wanted fewer framework-only layers, earlier validation, faster startup, and a smaller operational footprint.

## Plain Spring Improved the Numbers but Removed the Main Convenience { #plain-spring-improved-the-numbers-but-removed-the-main-convenience }

The team next tried removing Spring Boot auto-configuration while keeping plain Spring. This was an important experiment because it isolated how much of the startup cost came from Boot's dynamic
convenience rather than from the core container itself. Once beans were registered manually and the application context became more explicit, memory and startup improved materially.

But this result created a different problem. If the team had to manually assemble nearly everything, they had given up a major reason for using the framework. The application became more predictable,
but configuration became more laborious, and most contemporary Spring documentation was oriented toward Spring Boot rather than this low-level style. Runtime proxying and bytecode-oriented behavior
also remained.

This experiment sharpened the target. The team did not want “Spring without Spring Boot.” They wanted the ergonomics of a framework with a runtime much closer to handwritten Java.

## Quarkus and Micronaut Solved Part of the Problem, Not the Whole One { #quarkus-and-micronaut-solved-part-of-the-problem-not-the-whole-one }

Quarkus and Micronaut naturally entered the comparison because both were designed with startup and build-time optimization in mind. In the speaker's view, they were important improvements over
conventional runtime-heavy approaches, but they still did not match the exact design constraints the team had set for itself. The team wanted to avoid not only slow startup but also opaque generated
bytecode and runtime structures that developers could not easily inspect.

The desired constraints were closer to this:

```text
Compile-time graph validation
        +
generated human-readable source
        +
minimal runtime abstractions
        +
no runtime bytecode dependency
        +
performance close to direct libraries
```

This is one of the areas where the historical nature of the presentation is essential. The talk reflects the competitive landscape and implementation details of that pre-1.0 Kora period. Quarkus,
Micronaut, Spring, the JDK, and Kora itself have all evolved substantially since then. The interesting part is not the exact criticism of each framework in that year; it is the architectural criterion
Kora was choosing for itself.

## The Real Baseline Was Handwritten Undertow + JDBC { #the-real-baseline-was-handwritten-undertow-jdbc }

Instead of treating another framework as the performance ceiling, the team created a baseline with no framework at all. The baseline used Undertow and JDBC directly. Routes, SQL, mappings, and
application assembly were written manually. This gave the team a reference point for what a low-abstraction JVM service could do if developer productivity were ignored.

That produced a useful target: Kora did not need to outperform handwritten Undertow/JDBC code. It needed to get close enough that a team could retain dependency injection, generated HTTP routing,
repositories, configuration, telemetry, lifecycle, and other framework capabilities without paying a large runtime tax.

The early benchmark graphs compared the baseline with Micronaut, Quarkus, and Spring. In the speaker's environment, the manual application was clearly ahead in throughput and response time and also
consumed fewer resources under equivalent load. The exact values in those early graphs are less important than the pattern: the more framework machinery existed around the same basic application, the
further the result moved from the baseline.

A primitive representation of the throughput relationship shown on the slide looks approximately like this:

```text
RPS, earlier baseline comparison
(higher is better; visualized approximately from the slide)

baseline-undertow-jdbc   ██████████████████████████████  ~3000
quarkus-vertx-jdbc       ███████████                     ~1100
micronaut-async-jdbc     ███████                         ~650
spring-java-jdbc         ████                            ~350
```

This is not a new benchmark reconstructed from raw data; it is a simplified visual summary of the graph shown in the presentation. The key point is the distance between the direct baseline and
framework implementations, which became the motivation for Kora's architecture.

## Why Another Framework Made Sense in a Microservice Environment { #why-another-framework-made-sense-in-a-microservice-environment }

The speaker's argument becomes much stronger when placed in the microservice context. A small service may contain very little business logic: receive an HTTP request, validate a model, execute a
query, call another service, publish a message, and return a result. When the business path is short, the relative cost of framework initialization and runtime abstractions becomes more visible.

The same applies at fleet scale. A few dozen megabytes of extra memory are trivial for one process and significant across hundreds or thousands of replicas. Startup that takes several seconds may be
unimportant for a long-lived singleton and important for autoscaling, rolling deployments, test environments, and rapidly rescheduled services. CPU overhead that looks small at one instance can become
large when multiplied across an entire platform.

This produced the original Kora objective:

```text
Framework convenience
        ↓
but compile application structure ahead of time
        ↓
generate ordinary source
        ↓
keep integrations thin
        ↓
make runtime resemble direct library usage
```

Again, this was **pre-stable Kora, around the 0.9-era**, not the later 1.2.x or 2.0 framework. The significance of the talk is that the core philosophy was already visible even while many concrete
modules and APIs were still experimental.

## The Resource-Constrained Benchmark { #the-resource-constrained-benchmark }

The more important benchmark in the talk used a newly written service inside a constrained environment. The conditions shown on the slide were:

```text
RAM limit        384 MB
CPU limit        0.5 CPU
Container image  Same base image
JDK              Same JDK version
Traffic          Alternating POST / GET / DELETE
Load tool        wrk
```

This matters because resource constraints make framework overhead easier to see. With abundant CPU and memory, startup and runtime differences can disappear into unused capacity. Under half a CPU and
a few hundred megabytes of RAM, framework behavior becomes part of the application's operating envelope.

The final comparison included several Spring configurations and Kora. The results were striking because progressively removing Spring infrastructure moved Spring closer to Kora, reinforcing the team's
original hypothesis that much of the gap came from framework machinery rather than business code.

## Startup Memory: the Clearest Difference { #startup-memory-the-clearest-difference }

The minimum memory needed to start was reported as:

| Variant                           | Minimum memory to start |
|-----------------------------------|------------------------:|
| Spring Boot                       |              **192 MB** |
| Spring without JPA                |              **160 MB** |
| Spring without auto-configuration |              **128 MB** |
| **Kora**                          |               **64 MB** |

The same data can be visualized very simply:

```text
Minimum memory required to start
(lower is better)

Spring Boot                 ████████████████████████  192 MB
Spring without JPA          ████████████████████      160 MB
Spring without autoconfig   ████████████████          128 MB
Kora                        ████████                   64 MB
```

For the service in this experiment, Kora needed one third of the startup memory of the regular Spring Boot version and half that of the manually simplified Spring configuration. This was exactly the
kind of result the team cared about for small services because memory required *during startup* can be higher than steady-state memory and therefore determines the minimum container limit.

It is worth repeating that these values describe **early, pre-1.0 Kora**, approximately the 0.9 generation. Modern Kora should not be judged by these exact historical figures. The 1.2.x family
subsequently matured the implementation, integration modules, tooling, and production support, while Kora 2.0 evolved the model much further. The historical result is useful because it shows why the
architecture was chosen, not because 64 MB should be treated as a current universal Kora requirement.

## Startup Time Followed the Same Pattern { #startup-time-followed-the-same-pattern }

The reported startup times were:

| Variant                           | Startup time |
|-----------------------------------|-------------:|
| Spring Boot                       |     **16 s** |
| Spring without JPA                |     **10 s** |
| Spring without auto-configuration |    **3.5 s** |
| **Kora**                          |    **3.2 s** |

An ASCII comparison makes the pattern obvious:

```text
Startup time
(lower is better)

Spring Boot                 ████████████████  16.0 s
Spring without JPA          ██████████        10.0 s
Spring without autoconfig   ███▌               3.5 s
Kora                        ███▏               3.2 s
```

The interesting observation is not merely that Kora started faster. Once Spring Boot and JPA machinery were stripped away and the application was manually configured, Spring moved very close to Kora.
In other words, the experiment did not show that the Spring core was inherently incapable of fast startup. It showed that convenience layers have measurable cost, and Kora attempted to offer
convenience through compilation rather than through runtime discovery.

## Steady-State CPU Was Much Closer { #steady-state-cpu-was-much-closer }

At a fixed **500 RPS**, CPU consumption was reported as:

| Variant            | CPU at 500 RPS |
|--------------------|---------------:|
| Spring Boot        |        **63%** |
| Spring without JPA |        **48%** |
| Spring             |        **42%** |
| **Kora**           |        **40%** |

```text
CPU consumption at 500 RPS
(lower is better)

Spring Boot                 ███████████████████████████████  63%
Spring without JPA          ████████████████████████         48%
Spring                      █████████████████████            42%
Kora                        ████████████████████             40%
```

This is one of the most important nuances in the talk. The early Kora team was not claiming that every request magically became several times cheaper than an optimized Spring request. Under steady
fixed load, Kora and stripped-down Spring were fairly close. The major gains were in startup footprint, startup behavior, maximum throughput, and the transparency of how the application was assembled.

That makes the benchmark more credible because the story is not “Kora wins every metric by a huge margin.” It is “removing runtime machinery changes some costs dramatically and other costs only
modestly.”

## Maximum Throughput Moved Kora Closer to the Baseline { #maximum-throughput-moved-kora-closer-to-the-baseline }

The reported maximum throughput was:

| Variant            |      RPS |
|--------------------|---------:|
| Spring Boot        |  **710** |
| Spring without JPA | **1034** |
| Spring             | **1367** |
| **Kora**           | **1657** |

```text
Maximum throughput
(higher is better)

Spring Boot                 ███████████                710
Spring without JPA          ████████████████          1034
Spring                      █████████████████████     1367
Kora                        █████████████████████████ 1657
```

Average response time showed a smaller difference:

| Variant            | Average response time |
|--------------------|----------------------:|
| Spring Boot        |           **2.39 ms** |
| Spring without JPA |           **2.21 ms** |
| Spring             |           **1.79 ms** |
| **Kora**           |           **1.70 ms** |

The conclusion was that Kora got closer to the direct baseline without requiring teams to give up framework capabilities. It still did not equal the handwritten Undertow/JDBC service, which was
expected. The goal was not zero abstraction cost; the goal was to make the abstraction cost small and visible.

## The Key Decision: Generate Source, Not Runtime Bytecode { #the-key-decision-generate-source-not-runtime-bytecode }

The most important implementation decision in the talk is Kora's use of generated source code. The team deliberately asked why the framework should manipulate bytecode itself when Java and Kotlin
already have compilers designed to turn source into bytecode. Instead of constructing the application dynamically at runtime, Kora processors generated ordinary code during the build.

The model was:

```text
Annotations / interfaces / modules
            ↓
Annotation processor / Kotlin processor
            ↓
Generated Java or Kotlin source
            ↓
Normal compiler
            ↓
Application bytecode
```

This gave the team several properties at once. Missing dependencies could become compilation errors. Generated behavior could be opened in the IDE. The framework was less exposed to JDK changes
affecting unsupported bytecode tricks. Performance-critical paths looked more like ordinary direct method calls.

This remains one of the clearest lines connecting the pre-1.0 Kora shown in the presentation with later versions. By the 1.2.x line, the surrounding ecosystem had matured substantially, and the 2.0
documentation still describes compile-time application graph generation, no runtime reflection, no dynamic proxies at runtime, and generated human-readable source as fundamental principles. Modern
Kora is much larger and more polished than the 0.9-era framework, but it did not abandon this core idea.

## Compile-Time Dependency Injection Made the Graph an Artifact { #compile-time-dependency-injection-made-the-graph-an-artifact }

The root application interface in the presentation explicitly included infrastructure modules such as configuration, Undertow, JSON, JDBC, and logging. Exact module names and APIs evolved later, but
the architectural idea was already clear: the application's capabilities were declared explicitly, and Kora generated the final dependency graph from them.

That is a different mental model from runtime classpath discovery:

```text
Runtime discovery model

Classpath
   ↓
scan
   ↓
evaluate conditions
   ↓
build container
   ↓
discover missing pieces
```

versus:

```text
Kora compile-time model

Source + modules
   ↓
analyze graph
   ↓
generate graph source
   ↓
compile
   ↓
run predescribed graph
```

One of the slides shows the generated graph, and at first glance it looks intimidating because it is a large list of nodes, factories, dependencies, and lifecycle-managed objects. The speaker's
response is important: every DI container has an equivalent structure somewhere. Kora simply materializes it as generated code rather than keeping it inside runtime machinery.

The generated graph was never meant to be handwritten. It was meant to be inspectable.

## Controllers Became Ordinary Generated Handlers { #controllers-became-ordinary-generated-handlers }

Controllers followed the same pattern. The developer wrote a normal controller method with Kora's route annotations, and the processor generated the handler module that understood the route, request
decoding, parameter mapping, response mapping, and the controller invocation.

The effective path became:

```text
HTTP request
    ↓
generated handler
    ↓
request mapper
    ↓
controller method
    ↓
response mapper
```

That is much closer to the runtime structure developers would expect from reading the source. If something was unclear, the generated handler could be opened directly. There was no requirement to
infer which dynamic proxy or runtime-generated bytecode stood between the route and the application method.

This early implementation later evolved heavily. Modern Kora 2.0 uses a more mature synchronous HTTP model and dispatches application work onto virtual threads, which is a major evolution beyond what
this pre-stable 0.9-era talk describes. The historical point remains relevant: Kora wanted generated, readable adapters around ordinary application methods rather than an increasingly opaque runtime
execution model.

## Repositories Automated Boilerplate Without Hiding SQL { #repositories-automated-boilerplate-without-hiding-sql }

Repositories were another example of the same philosophy. Developers wrote repository contracts and SQL, while Kora generated the concrete implementation, driver calls, and mapping glue. The speaker
openly admits that developers accustomed to Hibernate or derived query methods might dislike having to write SQL manually, but the team considered explicit SQL an advantage for performance-sensitive
services.

The principle was that a repository should automate repetitive mechanics without making the actual database operation mysterious:

```text
Repository interface
      ↓
Explicit SQL
      ↓
Generated implementation
      ↓
Driver / JDBC
      ↓
Database
```

The talk mentions R2DBC and Vert.x database modules because those existed in the framework at that time. This is exactly the kind of detail that must be marked as historical. **This was pre-1.0 Kora
around the 0.9 generation.** The 1.2.x line changed and stabilized many parts of the framework, and the Kora 2.0 generation went further by removing reactive-style repository contracts and centering
the framework on synchronous code executed with virtual threads. The database philosophy—explicit contracts, generated repositories, thin integration—survived; the execution model changed
substantially.

## The Framework Was Intentionally Small and Incomplete { #the-framework-was-intentionally-small-and-incomplete }

One of the most valuable aspects of the talk is how openly the speaker describes the limitations of that early framework. Kora was still below 1.0.0, and when asked about backward compatibility, the
answer was essentially that there was none yet. APIs could change. Some integrations were missing. Security was being debated rather than rushed into the framework. ORM-like conveniences were
considered cautiously because the team did not want feature breadth to undermine the architecture.

That honesty is important when comparing the presentation with modern Kora. The framework shown here is not simply “old Kora with older version numbers.” It is a framework still discovering its stable
shape.

By **1.2.x**, Kora had already become much more complete and operationally mature: the release line accumulated significant work around OpenAPI, Redis, HTTP clients, testing, configuration, telemetry,
repositories, KSP, GraalVM support, and many bug fixes and compatibility improvements. By the **2.0 line**, the architectural surface became more coherent again rather than merely larger: direct
synchronous APIs, virtual threads, compile-time validation, updated HTTP contracts, a consolidated documentation set, and a more explicit production-oriented story around telemetry, lifecycle, probes,
resilience, and generated code.

So when the talk says “we may add this later,” “there is no compatibility yet,” or discusses integrations that current Kora no longer uses, those statements belong to the **pre-stable 0.9-era** and
should not be projected onto the 1.2.x or 2.0 framework.

## Java and Kotlin Were First-Class Goals From the Beginning { #java-and-kotlin-were-first-class-goals-from-the-beginning }

Even in this early stage, the team did not want Kora to be a Java-only framework with superficial Kotlin support. The talk describes separate generation approaches and frustration with relying on
imperfect generated Java stubs for Kotlin-specific language features. The intention was to understand Kotlin constructs such as nullability and default parameters properly rather than forcing Kotlin
through a Java-shaped model.

That investment became more important later. In the 1.2.x period, Kotlin/KSP support was significantly improved, and by the 2.0 line generated Java/Kotlin sources remain part of the normal development
experience. The modern documentation even encourages developers to inspect generated sources as a learning and debugging tool, which is a direct continuation of the philosophy shown in this talk.

## Explicit Modules Were About Control, Not Ceremony { #explicit-modules-were-about-control-not-ceremony }

During the Q&A, an audience member asks why the main application explicitly includes framework modules instead of relying entirely on annotations and automatic discovery. The answer is architectural
control. If an application needs a capability, it adds that module. If it does not need the capability, it does not bring it into the graph.

This is one of the most durable ideas in Kora:

```text
Need HTTP server?      add module
Need JDBC?             add module
Need telemetry?        add module
Need Kafka?            add module
Do not need it?        do not add it
```

The pre-1.0 syntax and module names changed later, but the principle survived and became much more polished in newer versions. Modern Kora 2 explicitly presents itself as a controlled stack where
services add only the modules they need.

## Testing Reflected the Original Target: Small Services { #testing-reflected-the-original-target-small-services }

The speaker describes an early preference for integration and black-box tests rather than extensive framework-specific mocking. The reasoning is connected directly to Kora's target: if services are
small and start cheaply, testing the real application becomes much more practical.

At the time of the presentation there was no rich dedicated mocking environment comparable to mature Spring testing infrastructure. Again, this is a historical limitation of the **pre-stable 0.9-era
**. Kora's test tooling expanded significantly later. The 1.2.x line already contained much more developed JUnit graph testing and replacement mechanisms, and Kora 2 documentation treats component,
integration, and black-box testing as first-class parts of the framework.

The philosophical continuity is more interesting than the old limitation. Kora prefers tests that remain close to the actual generated application graph rather than constructing a parallel testing
universe disconnected from production wiring.

## “We Hire Java Developers, Not Spring Developers” { #we-hire-java-developers-not-spring-developers }

One of the most memorable moments in the Q&A has little to do with benchmark numbers. An audience member asks whether engineers might be worried about working with an internal or less popular
framework because they want Spring and Hibernate on their résumés.

The speaker answers:

> **We hire Java developers, not Spring developers.**

The idea is that a backend engineer's primary skill should be solving engineering problems: understanding the JVM, concurrency, databases, networking, messaging, and system behavior. A framework is an
instrument, not a profession.

That statement also explains why Kora was designed to stay close to familiar Java/Kotlin concepts. If the framework requires years of proprietary knowledge to become productive, then the framework has
become too important relative to the underlying engineering discipline.

Modern Kora's evolution makes this point even stronger than the early talk did. The 2.0 generation deliberately uses ordinary synchronous Java/Kotlin signatures, JDBC-style data access,
HTTP/gRPC/Kafka concepts close to the underlying technologies, and compile-time generated code that can be inspected in the IDE. The framework has matured substantially since 0.9 without turning into
an isolated programming universe.

## Health, Metrics, Security, and Native Image Were Still Being Shaped { #health-metrics-security-and-native-image-were-still-being-shaped }

The Q&A also gives a useful picture of the framework's maturity level. Health checks and metrics existed as opt-in modules, but the speaker could not recall the exact default metric set during the
discussion. Security was not yet treated as a mandatory framework abstraction and was still under debate. Native image support existed as experiments rather than as the main runtime strategy. There
was explicit hesitation about adding features simply because other frameworks had them.

These answers would sound incomplete if presented as a description of current Kora. They make sense when understood as **pre-1.0 Kora around 0.9+**. By 1.2.x the production surface had expanded
materially, and the 2.0 line now documents telemetry, structured logging, probes, lifecycle, graceful shutdown, resilience, HTTP, OpenAPI, gRPC, data access, messaging, configuration, and other
production concerns as part of a much more mature framework.

The useful lesson is not that early Kora lacked features. It is that the team was deliberately selective about which abstractions deserved to become framework concepts.

## A Primitive View of the Evolution { #a-primitive-view-of-the-evolution }

The historical progression can be summarized like this:

```text
Pre-1.0 / ~0.9-era Kora
│
├─ core compile-time DI idea already present
├─ generated controllers / repositories / graph
├─ Java + Kotlin focus
├─ multiple experimental integrations
├─ no stable compatibility promise yet
└─ small ecosystem, strong architectural direction
        │
        ▼
Kora 1.2.x
│
├─ significantly more stable framework
├─ broader integration and tooling surface
├─ stronger OpenAPI / testing / telemetry / config support
├─ improved KSP and Kotlin path
├─ many production fixes and compatibility improvements
└─ architecture proven across a much larger real surface
        │
        ▼
Kora 2.0 line
│
├─ much more mature and consolidated model
├─ synchronous application contracts
├─ virtual threads as the standard execution model
├─ no reactive / suspend contracts in framework modules
├─ refined compile-time graph processing
├─ stronger docs / guides / runnable examples
└─ broader cloud-production story around OTel, probes,
   lifecycle, graceful shutdown, resilience and testing
```

This is why the talk remains worth reading today. Many APIs are historical. The architectural direction is not.

## What the Benchmarks Actually Proved { #what-the-benchmarks-actually-proved }

The benchmark did not prove that Kora would always outperform Spring, Quarkus, or Micronaut. It proved something narrower and more useful: **the team's architectural assumptions were measurable**.
Removing auto-configuration lowered startup cost. Removing runtime discovery and reducing abstraction layers moved performance closer to the manual baseline. Generating source and the application
graph at compile time allowed a framework-level programming model without recreating the same runtime machinery the team was trying to avoid.

The benchmark summary can be read as three separate findings:

```text
Startup memory:
Kora had the largest advantage.

Startup time:
Kora and manually stripped Spring were close,
while ordinary Spring Boot was much slower.

Steady-state runtime:
Differences narrowed under fixed throughput,
but Kora still reached higher maximum RPS.
```

This is a much more useful interpretation than “Kora was X times faster.” It shows where the cost was actually being paid.

## The Most Important Artifact Was Not a Benchmark Graph but Generated Code { #the-most-important-artifact-was-not-a-benchmark-graph-but-generated-code }

The presentation spends significant time showing generated controllers, generated repositories, and the generated dependency graph. That emphasis is deliberate. The team was not only trying to reduce
CPU consumption; it was trying to make framework behavior explainable.

A traditional runtime container can be conceptually summarized as:

```text
Source code
   ↓
runtime framework machinery
   ↓
dynamic graph / proxy behavior
   ↓
actual execution
```

Kora attempted to turn that into:

```text
Source code
   ↓
generated source code
   ↓
normal compiler
   ↓
actual execution
```

That additional generated-source layer is visible rather than hidden. If developers wonder why a controller behaves a certain way, they can inspect the generated handler. If they wonder which mapper
is used, they can inspect the repository implementation. If they wonder how the graph is assembled, they can open the graph itself.

Modern Kora 2 has made this idea even more explicit. Generated code is not merely an implementation detail; the current documentation treats it as a normal debugging and learning surface. In that
sense, one of the strongest ideas from the 0.9-era did not just survive—it became more central as the framework matured.

## What Changed the Most by Kora 2 { #what-changed-the-most-by-kora-2 }

The biggest conceptual change from the talk to modern Kora is the execution model. The early framework experimented with several database and asynchronous technologies, including R2DBC and
Vert.x-oriented paths. By the 2.0 line, Kora is far more opinionated: framework application code is synchronous, virtual threads are the normal execution mechanism, and reactive or Kotlin `suspend`
signatures are no longer framework contracts.

That is a major maturation step because it reduces the number of parallel programming models the framework has to support. Instead of growing into a broader framework that supports every concurrency
style, Kora 2 became narrower and more coherent.

The resulting modern model is closer to:

```text
HTTP request
      ↓
virtual thread
      ↓
ordinary controller method
      ↓
ordinary service method
      ↓
JDBC / HTTP / gRPC / Kafka
      ↓
response
```

This was not the shape of the pre-stable 0.9-era framework in the talk. It is the later conclusion reached after several generations of development.

## Why the Historical Talk Still Matters { #why-the-historical-talk-still-matters }

The presentation is useful precisely because it predates the polished framework.

It shows the constraints before they became slogans.

It shows the baseline benchmark before Kora had years of optimization.

It shows the team debating whether Security, ORM-style convenience, native images, and other features belonged in the framework at all.

It shows a project with no compatibility guarantees explaining why generated source and compile-time DI were worth pursuing.

Most framework documentation tells you what exists.

This talk explains why Kora exists.

That distinction makes it valuable even though the concrete API belongs to the **pre-1.0, roughly 0.9+ period**.

## Conclusion { #conclusion }

This presentation should be read as an engineering origin story for Kora, not as current documentation. The version being demonstrated is **pre-stable Kora, around the 0.9-era before 1.0.0**, with
experimental modules, evolving APIs, no stable compatibility promise, and a much smaller ecosystem than the framework has today. Several technologies mentioned in the talk later changed or
disappeared, and some limitations discussed in the Q&A were addressed in subsequent generations.

What matters is that the foundational ideas were already present.

The team wanted a framework that could approach direct Undertow/JDBC performance without forcing every service to be handwritten. It wanted dependency errors during compilation rather than deployment,
generated source rather than hidden runtime bytecode, explicit modules rather than broad classpath-driven auto-configuration, visible SQL rather than opaque ORM behavior, and a runtime path with as
few framework-specific layers as possible.

The resource-constrained benchmark supported that direction. In the specific environment shown in the talk, Kora needed **64 MB** as the minimum startup memory compared with **192 MB** for the regular
Spring Boot configuration, started in roughly **3.2 seconds**, consumed about **40% CPU at 500 RPS**, reached about **1657 RPS**, and produced an average response time around **1.7 ms**. More
importantly, progressively removing Spring Boot and Spring infrastructure moved the Spring variants closer to Kora, which reinforced the central thesis: a meaningful part of the cost came from runtime
framework machinery rather than from the business logic itself.

From there Kora matured substantially. The **1.2.x line** was already a very different framework from this 0.9-era snapshot, with a broader production surface, stronger testing, configuration,
telemetry, OpenAPI, KSP, repository, and integration support. The **2.0 generation** goes much further: the framework is more coherent, more documented, more production-oriented, and more opinionated
around synchronous Java/Kotlin application code on virtual threads while preserving compile-time DI, thin abstractions, generated source, and inspectability.

The best way to summarize the evolution is therefore not:

```text
Kora 0.9
   ↓
more features
   ↓
Kora 2.0
```

It is:

```text
Kora 0.9-era idea
compile-time graph + generated source + thin runtime
        ↓
Kora 1.2.x
stabilize, expand, productionize
        ↓
Kora 2.0
simplify again around a mature,
coherent virtual-thread-first model
```

The speaker's most memorable statement still fits that modern framework:

> **We hire Java developers, not Spring developers.**

Kora's long-term direction follows the same idea. The framework should provide useful defaults, generated infrastructure, and production integrations, but the engineer should still be working with
Java, Kotlin, SQL, HTTP, Kafka, gRPC, databases, concurrency, and ordinary application code rather than learning a proprietary runtime universe.

That is the real story this early talk captures: Kora did not begin as an attempt to build a larger framework. It began as an attempt to make the framework smaller at runtime, more explicit to the
developer, and closer to the code the JVM actually executes.

