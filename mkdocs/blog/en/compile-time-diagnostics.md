---
title: Why Compile-Time Diagnostics Are a Kora Framework Feature (In Depth)
date: 2026-09-13
description: An in-depth case for why the Kora Framework's compile-time diagnostics — validated graph, generated code, precise errors — are a feature, not added build complexity.
search:
  exclude: true
---

# Compile-Time Diagnostics Are a Feature, Not Extra Build Complexity { #compile-time-diagnostics }

**September 13, 2026**

Compile-time frameworks are often criticized for moving too much work into the build. The criticism usually sounds reasonable at first: annotation processors run, Kotlin Symbol Processing runs,
generated source appears under build directories, IDEs need to understand those outputs, Gradle gains more tasks, and compilation does more than simply turn handwritten Java or Kotlin into bytecode.
From that perspective, a runtime-oriented framework can appear simpler because the visible development pipeline looks short:

```text
write source
  ↓
compile source
  ↓
framework handles the rest at runtime
```

while a compile-time framework appears to insert another layer:

```text
write source
  ↓
processor / KSP
  ↓
generated source
  ↓
compile
  ↓
application
```

That picture is accurate as far as build phases go, but misleading as an architectural conclusion. The complexity does not disappear in the runtime-oriented model. Dependency graphs still need to be
resolved, repositories still need implementations, routes still need handlers, mappings still need executable logic, AOP still needs interception machinery, and validation, transactions, retries,
caching, and configuration still need to be wired into the application somehow. The real architectural question is not whether that work exists, but **when it happens, where errors surface, whether
the result is deterministic, and whether developers can inspect what the framework decided to do**.

The Kora Framework is a useful example because compile-time graph construction, annotation processing, Kotlin Symbol Processing, and source generation are not secondary implementation details. They are central to
the way the framework works. The framework attempts to validate dependencies, injections, graph structure, AOP contracts, mappings, repository declarations, and generated application infrastructure
before the application starts. In a runtime-oriented architecture, the path to a structural error may look like this:

```text
source
  ↓
build succeeds
  ↓
application starts
  ↓
container / proxy / reflection work
  ↓
failure appears
```

Kora deliberately tries to move a large class of those failures into an earlier loop:

```text
source
  ↓
processor / KSP
  ↓
compiler diagnostic
  ↓
build stops
```

The point is not that compile-time processing eliminates complexity. The point is that **the complexity exists either way. Kora chooses to expose more of it where the compiler can validate it instead
of postponing the same structural decisions until startup or runtime.**

---

## Compile-Time Processing Is Part of the Toolchain, Not a Second Runtime { #toolchain-not-runtime }

The phrase *annotation processor* can make the mechanism sound more exotic than it is. Java annotation processing is part of the standard compiler toolchain. A processor receives a structured
representation of source declarations, validates them, and may generate additional source or resources. Java developers have relied on this mechanism for years through dependency-injection generators,
mapping libraries, serializers, immutable-value generators, configuration tooling, and API generators. Kotlin Symbol Processing serves a similar role for Kotlin by exposing a Kotlin-oriented model of
declarations and allowing tools to validate and generate code during the build.

The architectural distinction is important: neither the Java processor nor KSP remains alive inside the production request path. They are not interpreters that sit between business code and the JVM.
They run while the application is being built, and their output becomes ordinary compiled classes. From the runtime application's point of view, the processor is gone. What remains is the code it
produced.

That means build-time and runtime complexity should not be counted as though they were equivalent. Suppose a framework needs to determine which implementation satisfies an interface, whether a
dependency graph contains a cycle, how repository parameters are mapped, whether a DTO can be converted, whether an AOP method can be overridden, or how an HTTP handler should invoke a controller.
Those questions must be answered somewhere. The available choices are essentially to answer them during compilation, during startup, during first use, or through some mixture of those phases. Moving a
decision earlier does not invent the decision; it changes its timing and the quality of the feedback around it.

This matters because failure distance matters. If a constructor dependency is invalid and the compiler rejects it immediately, the distance between cause and observation is short:

```text
bad dependency declaration
        ↓
compiler diagnostic
```

If the same mistake survives compilation and is discovered only after packaging, process startup, container initialization, graph resolution, and perhaps a particular lazy path, the distance is much
longer:

```text
bad dependency declaration
        ↓
source compiles
        ↓
artifact built
        ↓
application launches
        ↓
container resolves graph
        ↓
failure
```

The longer the distance, the more unrelated system state exists between the edit that caused the problem and the signal that reports it. That increases diagnostic noise and often turns a structural
mistake into what feels like an operational failure. Kora's compile-time model deliberately reduces that distance wherever the necessary information is already available.

---

## Earlier Failure Is Usually Cheaper Failure { #earlier-failure }

A missing dependency is the simplest example. If the framework discovers it during compilation, the developer is already in the edit-build loop. The build fails, the diagnostic points to the missing
type or unresolved component, and the developer fixes the declaration. If the same problem is discovered during startup, the developer has already paid for compilation, packaging, JVM launch,
framework initialization, graph construction, and perhaps test or deployment setup before receiving essentially the same information. If it appears only on a lazy path, the correction loop becomes
longer still.

The same reasoning applies to ambiguous dependencies and cycles. An application graph has structural rules: required dependencies must exist, ambiguity must be resolved, cycles must be rejected or
handled explicitly, types must match, and tags or qualifiers must be coherent. Runtime dependency-injection systems can validate these rules while building an application context; Kora chooses to
validate them earlier and make the build fail when the graph is structurally invalid. The value is not that Kora invented stronger rules. The value is that invalid architecture is rejected closer to
the code change that introduced it.

This principle extends naturally beyond DI. If a mapper is generated from types known during compilation and a model changes from `String` to `Instant` without a valid conversion, there is little
benefit in postponing discovery until a reflective mapper executes at runtime. If a repository method has a signature, query declaration, parameter set, return type, and mapping requirements that are
all visible during compilation, the framework can generate the implementation and let the Java or Kotlin compiler validate a large portion of that contract before a real database is ever touched. That
does not prove the SQL is semantically correct against a production schema, and it does not remove the need for integration tests. It simply creates a clean boundary between what can be checked
statically and what requires real infrastructure.

The same division applies to AOP. If a method must be overridable for a generated subclass to wrap it, method finality and visibility are structural facts. Discovering that constraint during
compilation is more useful than discovering it while a runtime proxy is being created. HTTP routing follows the same pattern: path templates, methods, controller signatures, request and response
mappings, and route contracts contain a large amount of static information. Some route errors will always require runtime verification, but those that can be rejected while handlers are generated
should be rejected there.

A compile-time framework is therefore not trying to turn every possible problem into a compiler error. It is trying to avoid postponing errors that are already knowable.

---

## Static and Dynamic Validation Should Complement Each Other { #static-dynamic-validation }

Compile-time validation is strongest when it is understood as one layer in a larger validation stack rather than as a replacement for testing or runtime observability. A successful build can prove
that the application is structurally coherent according to the information available during compilation. It cannot prove that PostgreSQL is reachable, a Kafka topic exists, credentials are valid, a
remote API behaves correctly, production data satisfies business assumptions, or concurrency will remain safe under load.

A healthy model looks like this:

```text
compiler
  → validates static architecture

component tests
  → validate framework integration

integration tests
  → validate real external systems

runtime telemetry
  → validate production behavior
```

Kora strengthens the first layer. It does not remove the later ones.

This distinction is important because “shift left” can otherwise become a slogan. The useful version of the idea is much more precise: move **structural checks** left and leave genuinely dynamic facts
where they belong. A dependency graph is structural. Method overridability is structural. Many mapping requirements are structural. Database availability is dynamic. Kafka broker state is dynamic.
Business data is dynamic. A good framework should not confuse those categories.

When static mistakes are removed earlier, runtime failures become more interesting because they are more likely to represent genuine runtime concerns: network behavior, database state, resource
exhaustion, configuration supplied at deployment time, or business logic. Startup also becomes more focused. Instead of mixing graph validation, proxy creation, metadata discovery, application
initialization, and resource connection into one large phase, more structural work has already been completed. A successful build can therefore provide stronger confidence that what remains at startup
is actually runtime work.

This narrowing of the problem space has operational value. If the build already proved that the graph is valid and generated code compiles, then a startup failure while connecting to PostgreSQL is
easier to classify. The team is not simultaneously wondering whether the dependency graph itself is malformed.

---

## CI Becomes a Stronger Gate { #ci-gate }

Moving framework validation into compilation has a particularly important effect on CI. A pull request pipeline already compiles code, runs tests, and packages artifacts. If DI graph construction,
mappings, repository contracts, AOP structure, and HTTP handler generation participate in compilation, then CI can reject structurally invalid applications before a container image is built or a
deployment begins.

Without that validation, the path can look like this:

```text
PR merges
  ↓
image builds
  ↓
deployment starts
  ↓
application initializes
  ↓
framework discovers structural problem
```

With compile-time validation, the same class of error can stop much earlier:

```text
PR build
  ↓
compiler / processor rejects structure
  ↓
nothing deployable is produced
```

That changes the economics of failure. Containerization can create a false sense of progress: if an application can be packaged but cannot construct its dependency graph, then the package was never
useful. A stronger build artifact is one where language types are valid, generated framework code compiles, known static contracts are satisfied, and tests have passed. Deployment can then focus on
environment-specific concerns instead of rediscovering structural mistakes that were already visible in source.

Earlier rejection also matters in ephemeral CI and agent workflows. A compile failure costs a build attempt. A deployment failure may cost image creation, registry upload, scheduler time, startup, log
collection, cleanup, and rollback. The earlier an invalid change is rejected, the cheaper the failed experiment becomes.

That is especially important once AI agents start producing many candidate changes. A machine can iterate quickly only if feedback arrives quickly and deterministically. A compile-time framework gives
the agent a short repair loop: generate code, compile, read the diagnostic, correct the change, and continue.

---

## Deterministic Failures Are Easier to Reproduce { #deterministic-failures }

Compile-time diagnostics also tend to reduce the number of environmental variables involved in structural failures. Given the same source, classpath, processor version, and compiler inputs, the result
should be the same. A missing component fails consistently. A mapping that cannot be generated fails consistently. Invalid generated source is reproducible from build inputs.

Runtime failures can depend on many more dimensions: profiles, environment variables, startup ordering, external resources, lazy initialization, traffic paths, or runtime metadata. Not every runtime
failure is nondeterministic, of course, and deterministic runtime systems exist. The point is simply that compile-time structural validation narrows the reproduction surface.

Compare two bug reports:

```text
The build fails when OrderService depends on PriceMapper.
```

and:

```text
The service sometimes fails during startup
when these two auto-configurations are present
under the production profile.
```

The first issue can often be reproduced by checking out the source and compiling it. The second may require reconstructing a larger portion of the environment. That difference matters for application
teams, framework maintainers, open-source bug reports, remote teams, and automated agents.

Processor bugs still exist, and they should be treated as framework bugs. A cryptic processor stack trace, an internal exception, or invalid generated code is not somehow made acceptable because it
happened during compilation. But runtime containers, proxy factories, reflection-based mappers, and startup processors can also contain defects. The fair comparison is not “processor can fail versus
runtime framework never fails.” The meaningful comparison is where defects occur, how observable they are, and how reproducible the failure is.

---

## Generated Source Is Ground Truth, Not a Second Codebase { #generated-source }

One of the most misunderstood aspects of Kora is the role of generated source. Developers sometimes see `build/generated` and assume that the framework has created another codebase they now need to
understand and maintain. That is not the intended model.

Generated code is derived build output. Developers do not normally edit it, review it as handwritten design, or maintain it directly. The ownership relationship is simple:

```text
handwritten source
      ↓
generator
      ↓
derived source
```

Delete the build directory and the generated files can be recreated. In that sense they resemble bytecode or generated resources. The difference is that generated source has a useful hybrid property:
it is disposable like build output but readable like application code.

That makes it an unusually effective inspection surface.

If a generated repository binds the wrong parameter, the binding is visible. If an AOP wrapper nests retry and timeout in an unexpected order, the control flow is visible. If a graph node selects a
surprising provider, the wiring is visible. If an HTTP handler chooses an unexpected mapper, the generated code can reveal which one was selected.

This does not mean developers should routinely inspect generated source. Most application development should remain at the high-level API. The point is that when the abstraction needs to be understood
precisely, the framework leaves behind something concrete to inspect.

The right analogy is the compiler itself. Java developers do not need to understand `javac` internals to write Java, and they do not inspect bytecode for every method. Yet bytecode, disassemblers, JIT
tooling, and compiler diagnostics are available when deeper analysis is needed. Kora's generated source plays a similar role at the framework boundary. You do not need to understand it to use Kora,
but it is available when you need to inspect the exact behavior the framework produced.

That is why generated source should be thought of as an **escape hatch from abstraction**, not as mandatory knowledge.

---

## Readable Generation Converts Framework Semantics Into Language Semantics { #readable-generation }

Generated code becomes particularly valuable when it reduces specialized framework behavior to ordinary Java or Kotlin control flow.

Imagine an AOP wrapper that effectively becomes:

===! ":fontawesome-brands-java: `Java`"

    ```java
    return retry.retry(() ->
        timeout.execute(() ->
            super.load(id)
        )
    );
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    return retry.retry {
        timeout.execute {
            super.load(id)
        }
    }
    ```

Aspect ordering is now ordinary nesting. The developer no longer needs to reconstruct an abstract runtime interceptor chain from container metadata. Or consider generated DI wiring:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var repository = new UserRepositoryImpl(database, telemetry);
    var service = new UserService(repository);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val repository = UserRepositoryImpl(database, telemetry)
    val service = UserService(repository)
    ```

Graph construction has become ordinary object construction.

The generated source may be verbose, repetitive, or expose internal names, but its control flow is concrete. A developer can place a breakpoint, follow a method call, inspect a field, or compare
output between framework versions. That concreteness is often easier to reason about than runtime behavior assembled from proxies, reflection, metadata, and container state.

This also makes generated source useful during framework upgrades. Release notes and tests remain the primary tools for evaluating change, but generated output can provide additional evidence. If a
new Kora version changes wrapping order, telemetry placement, query binding, or component construction, the generated source may reveal that difference directly. Framework behavior becomes diffable in
a code-oriented way.

The same property helps performance analysis. If a generated path contains direct calls rather than reflection, temporary arrays, boxing, or generic invocation, the developer can inspect that fact
rather than taking a performance claim entirely on trust. This makes source generation a transparency mechanism, not just an implementation technique.

---

## Compiler Diagnostics Become Part of Developer Experience { #developer-experience }

In a compile-time framework, compiler diagnostics are not incidental. They are one of the primary ways the framework communicates with developers, which means their quality becomes part of the
framework's user experience.

A useful diagnostic should answer several questions at once: what failed, where it failed, which declaration caused the problem, what type or component was expected, and why the framework cannot
proceed. A message such as:

```text
No component of type Database is available for UserRepository.
```

is valuable because it immediately identifies the problem domain. A message such as:

```text
Method is final and cannot be wrapped by generated AOP subclass.
```

does more than reject code; it teaches the interception model.

This matters because the processor should be invisible when everything works. A well-designed compile-time framework does not require application developers to understand processor internals. The
normal experience should be to write application code, compile, and run. Developers notice the processor primarily when it catches an invalid declaration or when they intentionally inspect generated
output.

There are therefore several distinct levels of knowledge:

```text
Level 1
use Kora's public API

Level 2
inspect generated source when debugging

Level 3
inspect processor implementation when contributing to Kora itself
```

Most application developers should remain at Level 1 most of the time. Experienced developers may occasionally use Level 2. Level 3 belongs primarily to framework contributors. Confusing these levels
makes compile-time frameworks look much more complex than they are.

Runtime frameworks have similar levels. They simply place Level 2 somewhere else: container diagnostics, runtime proxies, bean graphs, debug logging, actuator-style tooling, or framework-specific
inspection APIs. Compile-time frameworks do not invent an additional layer of complexity; they expose one of those deeper layers as source code.

---

## IDEs, Gradle, CI, and AI Can Share the Same Feedback Surface { #shared-feedback-surface }

Another benefit of compiler diagnostics is that they are already understood by the surrounding development ecosystem. IDEs understand files, lines, columns, symbols, and messages. Gradle understands
failed compilation tasks. CI understands build failures. AI coding agents can parse the same diagnostics and use them as repair signals.

Generated sources fit naturally into the same ecosystem. Modern Java and Kotlin development already uses source generation through Protocol Buffers, OpenAPI generators, MapStruct, Dagger-like DI
systems, schema tooling, and annotation processors. IDEs index generated code, navigate to generated implementations, display compiler errors, and mark generated directories appropriately. Gradle
models generated source as task output consumed by later compilation tasks, and deterministic outputs can participate in incremental builds and caching.

The result is a useful common truth surface:

```text
developer IDE
     +
Gradle
     +
CI
     +
AI coding agent
     ↓
same compilation result
```

There is no need for a separate framework health protocol just to explain structural errors. The framework can use the compiler pipeline developers already trust.

This is especially valuable for AI. An agent may invent a wrong annotation, unsupported method signature, missing component, invalid mapper, or impossible AOP target. In a compile-time framework,
those hallucinations become repair tasks rather than latent runtime failures. The compiler rejects the proposed structure, the agent receives a precise signal, and the next iteration can correct it.

Generated source provides the next level of evidence when the diagnostic alone is not enough. Language models are strong at reading ordinary source code and weaker at reconstructing invisible runtime
state. If the agent can open a generated repository, AOP wrapper, graph provider, or HTTP handler, it can reason about the concrete Java or Kotlin that actually exists.

That means Kora's compile-time transparency is not only a human debugging feature. It is also a machine-reasoning feature.

---

## Build Cost Is Real, but It Must Be Evaluated End to End { #build-cost }

A fair discussion of compile-time diagnostics has to acknowledge the cost. Annotation processing and KSP consume build time. Generated source increases compiler work. Large application graphs can make
processing more expensive. Incremental processing quality matters. Gradle configuration matters. IDE indexing can become heavier. Generated-code volume can affect disk usage, compilation, artifact
size, and class loading.

Compile-time architecture is not free.

The relevant question is where the cost pays back.

If a processor adds time to a build but removes runtime scanning, proxy construction, reflection metadata, startup graph assembly, and late validation from every process launch, the trade may still be
favorable. One build can produce an artifact that starts repeatedly in developer tests, CI tests, staging, production rollouts, autoscaling events, restarts, and spot-instance replacement. Build-time
work can therefore be amortized across many runtime launches.

Even if runtime performance were identical, earlier diagnostics can justify some build cost because the build produces a stronger artifact and CI rejects structurally invalid applications earlier. The
benefit is not only speed; it is certainty.

The right performance metric is also not clean processor time in isolation. For both humans and agents, the important loop is usually:

```text
edit one file
  ↓
incremental compile
  ↓
run targeted test
  ↓
verified behavior
```

A compile-time framework needs strong incremental behavior to make this loop fast. If every tiny edit causes the entire graph to regenerate and recompile, developer experience suffers regardless of
how elegant the runtime architecture is. Processor design, cache-friendly outputs, stable task inputs, and multi-module boundaries therefore matter.

The full comparison should consider developer mental model, clean and incremental build time, startup, runtime memory, failure timing, debuggability, CI reproducibility, generated artifact size, and
operational complexity. Compile-time frameworks intentionally move cost among these categories. Kora's bet is that the total system becomes easier to operate and reason about when more structural work
is completed before runtime.

---

## Runtime Complexity Is Not Free Just Because It Is Less Visible { #runtime-complexity }

One reason compile-time systems can feel more complicated is that build-time machinery is visible. Developers can see processor dependencies, KSP plugins, generated directories, and Gradle tasks.
Runtime machinery is often less visible because it happens inside framework startup, container initialization, reflection, proxy factories, metadata registries, or classpath scanning.

Visible complexity can psychologically feel larger than hidden complexity, but visibility is not the same as quantity.

Runtime scanning consumes startup time. Reflection metadata consumes memory. Proxy generation consumes initialization work. Runtime validation consumes part of the failure budget. Container state
introduces another debugging surface. The fact that these mechanisms are not listed as explicit Gradle tasks does not make them free.

The correct comparison is therefore not “simple runtime framework versus complicated compile-time framework.” It is a total-system comparison of **where the same architectural work is performed and
what form it takes once performed**.

Kora deliberately makes more of that work visible and deterministic during compilation.

---

## Startup Becomes More About Starting Than Discovering Architecture { #startup }

The compile-time diagnostic model is closely related to startup behavior.

A runtime-oriented container may spend startup time scanning, discovering components, resolving dependencies, validating graph structure, creating proxies, and building metadata. A compile-time
application can move some of that work earlier so that runtime startup is closer to loading a prebuilt graph, constructing components, initializing resources, and becoming ready.

This is why the diagnostic model and the startup-performance model reinforce one another. Moving graph resolution and code generation into the build does not merely produce earlier errors; it also
means less structural interpretation remains to be performed every time the service starts.

For statically deployed backend services, that split is natural. Most services do not dynamically add arbitrary repository implementations while running. Their architecture changes through the
familiar cycle:

```text
commit
  ↓
build
  ↓
deploy
```

If controller structure, repository implementations, mapper requirements, and AOP applicability are already known when the artifact is built, there is little value in rediscovering those facts during
every startup.

The runtime should spend most of its time on things that are genuinely runtime concerns: loading deployment-time configuration, opening network resources, connecting to databases and brokers, starting
servers, and processing traffic.

---

## Compile-Time Architecture Is Best Understood as Architecture Compilation { #architecture-compilation }

A useful mental model is that Kora compiles more than language syntax. It compiles part of the application architecture.

The build pipeline takes types, annotations, modules, repository contracts, HTTP declarations, and other static information and produces graph wiring, repositories, mappings, handlers, and AOP
wrappers. Seen this way, annotation processing is not ancillary build magic. It is the framework's architecture compiler.

That idea is not unusual in modern development. Protocol Buffers take a schema and produce language types. OpenAPI generators take an API contract and produce clients or server interfaces. Schema
tools derive strongly typed models from data definitions. Native-image tooling performs ahead-of-time analysis. The shared idea is to use information that is already known earlier in order to produce
stronger artifacts.

Kora applies that principle to framework infrastructure.

This also explains why annotation processing should not be described as an extra runtime abstraction layer. It does not sit in the production request path. It does not intercept every controller
invocation. It does not interpret framework metadata while the service is handling traffic. It ran earlier and produced code.

A more accurate pipeline is:

```text
declarative application source
        ↓
Kora processor / KSP
        ↓
ordinary generated Java/Kotlin
        ↓
ordinary compilation
        ↓
runtime with less framework interpretation
```

The build becomes more sophisticated so that runtime execution can become more concrete.

---

## The Best Failure Is the One That Prevents an Invalid Artifact { #best-failure }

There is a qualitative difference between producing an application artifact that cannot start and refusing to produce the artifact at all.

If a dependency graph is structurally invalid, a mapper cannot be generated, or an AOP target cannot satisfy the framework's rules, then “the code does not build” is often the cleanest possible
outcome. CI stops immediately. Nothing is packaged. Nothing is deployed. Nothing appears healthy before failing. The invalid state never becomes a release candidate.

This is one of the strongest arguments for compile-time diagnostics because it turns framework errors into normal build errors.

A missing DI component becomes a build failure. An invalid mapping becomes a build failure. An impossible AOP target becomes a build failure. Known structural invalidity belongs exactly there.

This also improves team communication. A pull request that fails because `PaymentClient` is ambiguous is easier to discuss than a deployment that starts failing under a particular environment with a
long initialization stack trace. Moving structural errors into CI reduces coordination cost between developers, reviewers, and operations.

The closer detection is to the edit that introduced the mistake, the cheaper the correction loop becomes.

---

## Compile-Time Validation Improves Onboarding { #onboarding }

Early diagnostics also make the framework easier to learn.

A newcomer does not need to memorize every graph rule before making the first change. They can learn through the build. If they wire something incorrectly, the compiler rejects it. If a method cannot
be used as an AOP target, the error reveals part of the framework model. If a required mapper is unavailable, the failure points directly at the missing structural element.

The framework becomes a guided system rather than a body of rules that must be memorized in advance.

This matters for human onboarding and AI-assisted development for the same reason: both work best when an invalid path is short.

```text
invalid source
    ↓
clear rejection
```

is a much stronger feedback loop than:

```text
invalid source
    ↓
successful build
    ↓
packaging
    ↓
deployment
    ↓
startup
    ↓
runtime failure
```

The alternative to compile-time complexity is often not less complexity. It is delayed complexity.

---

## Generated Source and Diagnostics Form a Layered Debugging Model { #layered-debugging }

Kora's compile-time architecture is easiest to understand as a layered debugging model rather than as a demand that developers read processor internals.

The first signal is the compiler diagnostic. If the problem is a missing component, invalid mapping, or impossible AOP target, the build may already explain it. The next layer is the application
declaration itself. If deeper inspection is required, generated source shows what the framework produced. Framework source is only necessary when the generated output appears wrong or a framework
defect is suspected. Component and integration tests validate behavior against real dependencies, while runtime telemetry handles production-only concerns.

A practical hierarchy looks like this:

```text
1. Read compiler diagnostic.
2. Read application declaration.
3. Inspect generated source if needed.
4. Inspect framework source only for deeper framework analysis.
5. Run component/integration tests.
6. Inspect runtime telemetry for dynamic failures.
```

Most application developers should rarely reach the deepest levels. This is a healthy layering of complexity.

The important principle is that generated source and diagnostics answer different questions. The diagnostic answers, “Why did the build fail?” Generated source answers, “What does the framework do
when the build succeeds?” Together they make the framework unusually inspectable without forcing every developer to become a framework contributor.

---

## AI Agents Benefit Disproportionately From This Model { #ai-agents }

Compile-time diagnostics align particularly well with AI coding agents because the natural agent loop already looks like a compiler-driven repair cycle:

```text
agent writes code
  ↓
compile
  ↓
read diagnostic
  ↓
edit
  ↓
compile again
```

Compiler diagnostics are concise, local, deterministic, and machine-readable. If the agent invents the wrong annotation, an unsupported method signature, a missing component, an invalid mapper, or an
impossible AOP target, the framework rejects the proposal and turns the hallucination into a concrete repair task.

Generated source strengthens the loop further because it gives the model exact framework behavior when the diagnostic alone is insufficient. The agent can inspect the generated repository, graph
provider, AOP wrapper, or HTTP handler and reason about ordinary Java or Kotlin rather than trying to infer invisible runtime state from general framework knowledge.

This is an important distinction. AI models are very good at reading code and much less reliable when they have to reconstruct dynamic container state they cannot directly observe. Kora's compile-time
architecture therefore happens to be highly compatible with agentic development without requiring a special AI runtime. The normal toolchain—Gradle, Java/Kotlin compilation, annotation processing or
KSP, generated source, and tests—is enough.

Humans and agents consume the same signals. The developer sees the compiler error; the agent sees the same error. The developer can open generated source; the agent can inspect the same source. The
developer runs a component test; the agent can run the same test. There is no separate explanatory system for machines.

That is a powerful architectural property.

---

## Runtime Flexibility Still Has Legitimate Uses { #runtime-flexibility }

None of this means compile-time composition is universally superior.

Dynamic plugin systems may need to discover implementations after build time. Applications may intentionally load unknown classes or scripts at runtime. Highly configurable platforms may need
composition decisions to remain open until deployment or even until execution. In those environments, runtime discovery and reflection can be the correct engineering choice.

Kora is optimized for a different context: statically built backend services whose architecture changes through source, build, and deployment. For that model, compile-time graph resolution is a
natural fit because the service's component structure is already known when the artifact is built.

The right question is therefore not whether compile-time processing is always better. It is whether the architecture matches the deployment model. For ordinary cloud backend services, the answer is
often yes.

---

## The Real Question Is Total-System Complexity { #total-system-complexity }

Framework architecture should not be judged by counting Gradle tasks, generated files, or runtime proxies in isolation. The meaningful comparison is the total system.

A runtime-oriented framework may have a lighter structural build but perform more scanning, reflection, proxy construction, validation, and graph assembly during startup or invocation. A compile-time
framework may spend more CPU during the build in exchange for earlier diagnostics, stronger artifacts, faster startup, simpler runtime paths, deterministic generated code, and better inspectability.

The trade can be summarized like this:

```text
Compile-time approach

more structural work during build
        ↓
stronger artifact
        ↓
less structural discovery at startup
        ↓
earlier failures
```

versus:

```text
Runtime-oriented approach

lighter structural build
        ↓
more framework work during startup/runtime
        ↓
later structural validation
```

Neither architecture is universally correct. Kora deliberately prefers the first for statically deployed backend services.

The strongest version of the argument is therefore not that compile-time diagnostics are free, nor that generated code eliminates all debugging. It is that **the same architectural complexity has to
exist somewhere, and Kora chooses to materialize more of it in a phase where it can be validated, reproduced, cached, inspected, and rejected before deployment**.

---

## Conclusion { #conclusion }

Compile-time diagnostics are often framed as the price developers pay for a framework that does too much during the build. That framing misses the architectural payoff.

Dependency injection still has to be resolved somewhere. Mappings still need executable implementations. Repositories still need real code. AOP still needs wrappers. HTTP routes still need handlers.
Validation still needs logic. A runtime-oriented framework can assemble much of this while the application starts or runs. Kora chooses to assemble and validate more of it while the application is
built.

That changes failure timing, and failure timing matters.

For a statically deployed backend service, a structural mistake is usually cheapest when it is discovered near the source edit that caused it. The compiler can reject the application before packaging.
CI can stop before creating a deployable artifact. The same source and classpath can reproduce the failure consistently. Generated output can be inspected as ground truth. Startup can focus more
heavily on real runtime work because more of the architecture has already been decided.

None of this means developers need to understand processor internals. They normally do not. Just as Java developers do not debug `javac` every time the compiler rejects a method call, Kora users
should normally see an actionable diagnostic and fix application code. Generated source is optional depth, not mandatory knowledge. It exists so that when a framework abstraction needs to be
understood precisely, the answer is not hidden entirely in runtime state.

The trade-off is real. Builds do more work. Processor performance matters. Incremental compilation matters. Generated-code volume matters. Build caches matter. But those costs buy stronger artifacts,
earlier errors, deterministic diagnostics, less runtime discovery, faster startup, and inspectable behavior.

For humans, that produces a shorter feedback loop. For CI, it creates a stronger gate. For AI agents, it creates an unusually effective repair cycle because the compiler can reject bad assumptions and
generated source can expose the framework's exact interpretation.

The architectural point is ultimately simple:

> **The complexity exists either way. Kora chooses to expose it where the compiler can validate it instead of hiding it until runtime.**

And the cleanest way to think about annotation processing in Kora is this:

> **Annotation processing is not an extra runtime abstraction layer. It is the mechanism that removes runtime abstraction layers by turning framework behavior into ordinary compiled code.**
