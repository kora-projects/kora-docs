---
title: Does Compile-Time Code Generation Really Make Development Slower? — Kora Framework
date: 2026-08-10
description: Whether compile-time DI, repository, and mapper generation actually slow development in the Kora Framework, and how incremental builds and submodules keep feedback fast.
search:
  exclude: true
---

# Does Compile-Time Code Generation Really Make Development Slower? { #does-compile-time-code }

**August 10, 2026**

There is a persistent intuition in JVM backend development that sounds reasonable enough to become a rule of thumb: if a framework performs dependency injection, repository generation, HTTP routing, mapping, validation, AOP, or other infrastructure work during compilation, then compilation must become slower. From there, the conclusion is often extended one step further: a framework that relies heavily on annotation processing or compiler plugins must also produce a slower development experience than a framework that defers more work until application startup.

The first half of that argument contains a real observation. Compile-time generation is work. Parsing annotations, resolving types, building a dependency graph, validating contracts, and emitting source files all consume CPU time. A framework that performs those operations during a build cannot pretend that they cost nothing.

The second half, however, does not follow automatically.

Developer productivity is not determined by the amount of time spent inside an annotation processor. It is determined by how long developers wait between making a change and receiving useful feedback about that change. Those are different measurements. A system can spend somewhat more time validating and generating code during compilation while still producing a shorter end-to-end development loop because it performs less work at startup, catches failures earlier, initializes less runtime machinery, and allows tests to create application contexts cheaply. Conversely, a system can compile source code quickly and still provide a slow feedback loop if every verification step requires expensive runtime scanning, proxy creation, container initialization, classpath analysis, reflection metadata processing, or framework warm-up.

This distinction matters particularly for the Kora Framework because Kora deliberately moves a large amount of framework work from runtime into compilation. Its dependency graph is built and validated during compilation. Repository implementations are generated. HTTP handlers and mappings can be generated. Aspects are implemented as generated code rather than runtime dynamic proxies. Configuration mappings, serialization support, validation code, and other adapters are also produced ahead of execution.

Look only at that list and it is easy to assume that Kora must pay for all of this with slow builds.

The more interesting question is not whether Kora performs work during compilation. It clearly does. The interesting question is whether performing that work there makes the development feedback loop slower in practice.

That requires looking at the entire loop.

```text
change
  ↓
incremental compile
  ↓
start application or test context
  ↓
run test
  ↓
get result
```

That is the unit developers actually experience dozens or hundreds of times per day.

Measuring only this:

```text
time spent inside annotationProcessor
```

and treating it as equivalent to development speed ignores most of the system.

The same mistake appears in many performance discussions: measuring one isolated cost while ignoring which other costs it eliminates. Compile-time generation is best understood as a relocation of work. Kora performs framework analysis and construction earlier so that less framework machinery remains to be discovered, interpreted, assembled, and validated when the process starts. The engineering question therefore becomes a trade rather than a slogan: how much build work is introduced, how efficiently can it be rebuilt incrementally, and how much runtime work disappears in return?

That is a much more useful way to evaluate a compile-time framework.

---

## Where the “Annotation Processing Is Slow” Reputation Came From { #where-the-annotation-processing }

The reputation did not appear from nowhere. Java annotation processing has been associated with slow builds for legitimate reasons, especially in large codebases and in earlier generations of build tooling.

An annotation processor can be expensive. It can inspect large portions of the compilation model, generate many source files, trigger additional compiler rounds, perform non-incremental analysis, cause broad invalidation after small source changes, or generate code whose compilation cost is larger than the original processing cost. A poorly designed processor can turn a small edit into far more work than the developer expects.

This becomes particularly visible in large monoliths where hundreds or thousands of source files participate in a single compilation unit. If a processor effectively treats the whole module as one global input, then changing one class may force it to reconsider a large amount of state. If its outputs are not compatible with incremental compilation, Gradle may have fewer opportunities to avoid work. If the processor produces huge generic source trees, javac or kotlinc must compile those as well. If processors interact badly with Kotlin stubs or compiler plugins, the situation can become worse.

Developers who have experienced one of these builds reasonably remember annotation processing as the culprit.

But “annotation processing can be expensive” is not the same statement as “all annotation processing makes builds slow.” Annotation processing is a mechanism. The cost depends on what a processor does, how much code it examines, how much code it emits, how often that work is invalidated, and how the build tool can cache or incrementally execute the surrounding tasks.

A processor that generates a small, direct implementation for one interface has a very different cost profile from a processor that must analyze an entire application-wide model on every change. A processor that emits straightforward Java methods has a different downstream compiler cost from one that produces enormous deeply generic classes. A framework that divides generation into local, fine-grained processors can behave differently from one giant processor that couples unrelated source changes together.

The phrase “uses annotation processing” therefore tells us surprisingly little about build performance by itself.

It is similar to saying that an application “uses reflection” and trying to infer its throughput from that fact alone. Reflection can occur once at startup or millions of times per second. The mechanism matters, but frequency, scope, implementation, and placement matter more.

Compile-time frameworks deserve the same level of analysis.

---

## Code Generation Is Not One Thing { #code-generation-is-not }

When developers discuss code generation, they often imagine a compiler performing some mysterious and potentially enormous second build behind the real build. That mental model is frequently inaccurate.

Generated framework code can range from extremely small adapters to application-wide structures. Its performance characteristics depend strongly on its shape.

Kora tends to generate ordinary Java or Kotlin infrastructure code that resembles code a developer could write manually. A generated repository implementation executes the query and maps results. A generated HTTP route extracts parameters and invokes a controller. A mapper converts one representation into another. A generated AOP subclass or wrapper composes interception logic directly. The application graph becomes explicit generated wiring.

The important characteristic is that the generated result is usually procedural and direct.

There is no requirement that compile-time generation produce elaborate code. In fact, the most effective generated infrastructure is often intentionally boring. The processor resolves information once and emits the operations that would otherwise have to be reconstructed dynamically later.

Conceptually, instead of runtime logic repeatedly asking questions such as:

```text
Which implementation satisfies this dependency?
Which constructor should be called?
Which annotations apply to this method?
Which interceptor chain is required?
How should this HTTP parameter be converted?
Which mapper should handle this value?
How should this repository result be transformed?
```

the compiler answers those questions ahead of time and writes down the answer.

The resulting runtime code may be equivalent to:

```text
construct A
construct B using A
construct C using B
call mapper X
call handler Y
call interceptor Z
```

This is why it is misleading to judge the approach only by the number of framework capabilities implemented at compile time. The relevant metric is not the feature count but the amount and complexity of generated work.

Kora can generate dependency wiring, repositories, handlers, aspects, and mappings without necessarily producing an enormous generated program. Much of that output replaces repetitive infrastructure code that would otherwise have to exist somewhere else, either handwritten or embodied in runtime framework machinery.

The compiler cost is real, but the generated code is not inherently expensive merely because there is a lot of framework functionality behind it.

---

## Compile Time Is a Budget, Not a Moral Category { #compile-time-is-a }

Framework discussions sometimes treat compile-time and runtime work almost ideologically. Compile-time work is described as either obviously superior because it removes runtime magic, or obviously inferior because developers compile more often than production processes start.

Both positions are too simplistic.

Compile time and runtime are simply different places where work can be performed. Good framework design assigns work to the phase where it provides the best overall system behavior.

Some work clearly belongs at compilation. If a dependency is impossible to satisfy, discovering that before the application runs is better than discovering it after startup. If two dependency candidates are ambiguous, a compiler error is usually more useful than a runtime container exception. If an HTTP mapping is structurally invalid, there is little value in waiting until deployment to complain. If generated repository code cannot map a database type to a method contract, early failure is preferable.

Other work naturally remains dynamic because it depends on configuration, external systems, traffic, or values only known at runtime.

The goal is therefore not “move everything to compile time.” The goal is to move deterministic framework work to a phase where it can be performed once, validated precisely, and represented directly.

Kora’s architecture makes a deliberate trade in this direction. Dependency graph construction, a significant portion of adapter generation, and many cross-cutting framework mechanisms are decided before the application starts.

That has two consequences.

The first is visible build work.

The second is missing runtime work.

Any serious comparison has to count both.

---

## What Kora Actually Pays for During Compilation { #what-kora-actually-pays }

To understand the trade, it helps to be concrete about what Kora asks the compiler to do.

The application graph is one of the most important examples. Kora uses declarations such as `@KoraApp`, `@Component`, and `@Module` to describe components and their relationships. The compiler resolves dependencies, validates the graph, detects missing or ambiguous bindings, and generates the wiring required to construct the application.

That operation is not free. Graph analysis has a cost.

Repositories can also be generated. Instead of discovering repository behavior through runtime reflection or producing runtime proxy implementations, Kora can generate the concrete implementation that performs database operations and mapping.

HTTP handling follows the same broad philosophy. Declarative controller contracts can become generated handlers and mappers rather than routes reconstructed from reflective metadata each time an application process initializes.

AOP-style functionality such as validation, caching, resilience, transactions, scheduling, security, and logging can be integrated through generated classes instead of relying on runtime proxy chains and dynamic interception infrastructure.

Configuration interfaces and data mappings can likewise become concrete generated code.

From a narrow compilation perspective, each of these features adds work.

But note what is happening structurally: most of the work converts a declarative description into simple executable code. The processor is not running the application. It is resolving static structure.

That distinction becomes important for incremental development because static structure is often highly cacheable and locally invalidatable. If a developer changes a method body that does not affect the dependency graph, repository contract, routing declaration, or generated mapping, there is no theoretical reason for every generator in the entire application to repeat all of its work.

The quality of the implementation and build integration determines how closely reality approaches that ideal, but the architecture itself does not require every small source edit to behave like a clean build.

This is why measuring a clean compilation alone cannot tell us what everyday Kora development feels like.

---

## The First Benchmarking Mistake: Measuring Only Clean Builds { #the-first-benchmarking-mistake }

Clean builds are useful. They are also unusually easy to misuse.

A clean build answers a specific question:

> How long does it take to produce the requested outputs when previous build outputs are deliberately unavailable?

That matters in some environments. It matters when a new CI worker checks out a repository without a reusable cache. It matters when build artifacts have been deleted. It matters when developers intentionally run `clean`. It matters when investigating worst-case build behavior or comparing compiler work in isolation.

But it is not the dominant loop of normal local development.

A developer usually does not edit one method, delete every compiler output, terminate the Gradle daemon, disable incremental compilation, disable caches, disable parallelism, and rebuild the entire application from zero before running a test.

Yet framework build comparisons frequently approximate exactly that workflow.

Kora’s own landing-page benchmark is interesting because it explicitly separates clean artifact build from cached artifact build rather than pretending that one number answers both questions. The clean-build scenario uses ten PetClinic-style services with production integrations and intentionally removes many Gradle optimizations. The command builds the distributable artifact, while build cache, configuration cache, parallel execution, and the Gradle daemon are disabled.

That is a useful stress case because it exposes how the frameworks behave when the build system receives very little opportunity to reuse previous work.

It is not, however, the same thing as the developer feedback loop.

The landing page therefore shows a separate cached-build scenario with the Gradle build cache, configuration cache, daemon, parallel execution, multi-module structure, and incremental compilation enabled.

That distinction is exactly the one a serious discussion of code generation needs.

If a framework is condemned because its worst-case clean compilation performs additional work, while its normal incremental workflow is ignored, the benchmark has answered the wrong question.

---

## Clean Artifact Build and Developer Iteration Are Different Products { #clean-artifact-build-and }

There is another subtle problem with treating clean builds as development speed: an artifact build often does more than the developer needs during a local edit-test cycle.

Kora’s landing benchmark uses `distTar` for Kora and `bootJar` for Spring in the clean artifact scenario. Those tasks create deployable outputs. They are meaningful for CI and release pipelines, but local development may execute narrower task graphs depending on how tests and run configurations are organized.

A developer changing business logic may only need compilation plus one test task. A developer working on an HTTP endpoint may compile the affected modules and start the application from classes. An IDE may delegate compilation in a way that differs from the final packaging pipeline. A component test may initialize only the relevant graph.

The broader lesson is that “build time” is not one number.

At minimum, teams should distinguish among:

- cold clean compilation;
- clean deployable artifact production;
- warm full build;
- incremental compilation after a representative source change;
- incremental test execution;
- application restart time;
- component-test context initialization;
- integration-test startup;
- CI build with local cache;
- CI build with remote cache.

Those scenarios exercise different parts of the toolchain.

A compile-time framework can lose one of them and win another.

The developer experience is determined mostly by the ones that happen frequently.

---

## The Second Benchmarking Mistake: Treating Every Source Change as Equal { #the-second-benchmarking-mistake }

Incremental build performance depends on what changed.

A modification inside a method body is different from adding a dependency to a constructor. Changing a SQL query contract is different from renaming a private helper. Adding a controller endpoint is different from changing a constant. Editing build logic is different from editing application code.

This matters because compile-time generation is usually sensitive to structure.

Imagine four edits.

### Edit A: change business logic inside an existing method { #edit-a-change-business }

The dependency graph has not changed. HTTP declarations have not changed. Repository interfaces have not changed. Most generated infrastructure may remain valid.

### Edit B: add a constructor dependency { #edit-b-add-a }

Now the graph may need to change. The compiler should validate the new dependency and regenerate relevant wiring. That additional work is exactly what the developer wants because an invalid graph should fail immediately.

### Edit C: change a repository signature { #edit-c-change-a }

The repository implementation or mapping code may need regeneration. Again, this is useful work because the contract itself changed.

### Edit D: add a new controller route { #edit-d-add-a }

HTTP generation must update. The changed routing contract justifies the work.

A benchmark that changes a globally significant declaration on every run can make a processor appear expensive even if ordinary implementation edits are cheap. A benchmark that changes only an irrelevant method body can make generation look cheaper than structural development actually is.

Representative build benchmarking therefore needs a change matrix rather than one synthetic edit.

For most teams, the right question is not “how long is incremental compile?” It is “how long are the incremental compiles corresponding to the edits our developers actually make?”

That produces a distribution rather than a single number.

---

## Gradle Changes the Economics of Compile-Time Generation { #gradle-changes-the-economics }

Modern Gradle is explicitly designed to avoid repeating work when its inputs have not changed. That makes build-system behavior central to any discussion about annotation processors.

Several mechanisms matter.

Incremental builds allow Gradle tasks to remain up-to-date when their declared inputs and outputs have not changed. If nothing relevant changed for a task, the task can be skipped.

The build cache goes further by reusing outputs from previous executions when the same task inputs produce the same cache key. Those outputs can come from the local machine or from a shared remote cache. This means work does not necessarily have to be repeated even in a different workspace or on a different CI agent.

The configuration cache attacks a different source of overhead: Gradle’s configuration phase. Once the build structure and task graph can be safely reused, subsequent invocations can skip much of the repeated configuration work and move toward task execution more directly.

The Gradle daemon amortizes JVM startup, class loading, JIT compilation, and build-tool initialization across repeated invocations.

Parallel execution allows independent projects and tasks to progress concurrently when their dependency relationships permit it.

Incremental Java compilation reduces the amount of code that needs recompilation after compatible source changes.

In a multi-module project, module boundaries provide another axis of isolation. A change in one service or library should not require every unrelated module to rebuild if task inputs and dependencies are modeled correctly.

None of these features magically makes an expensive processor cheap. Poorly designed processing can still defeat incremental behavior or invalidate too much work. But they fundamentally change the question.

A benchmark that disables all of these mechanisms intentionally measures cold work.

A developer usually works in a warm system specifically designed to avoid cold work.

This is why the Kora landing page’s decision to show both clean and cached build scenarios is more informative than publishing one headline build number. It acknowledges that build performance has modes.

---

## The Gradle Daemon Is Not a Benchmark Cheat { #the-gradle-daemon-is }

Framework comparisons sometimes disable the Gradle daemon in the name of fairness. That is reasonable when the objective is to measure completely cold build execution. It becomes misleading when the result is presented as ordinary developer experience.

The daemon exists precisely because developers run builds repeatedly.

Starting a new JVM, loading Gradle, loading plugins, preparing compiler infrastructure, and warming code all cost time. Reusing a long-lived process amortizes those costs across many invocations. Ignoring this optimization when measuring development iteration is similar to benchmarking a database while restarting the database server before every query.

A cold benchmark may still be useful, but it must be labeled correctly.

For local feedback-loop analysis, the daemon is not an optimization that developers are somehow cheating by using. It is part of the normal product.

The same applies to compiler daemons and IDE integration. The JVM ecosystem has spent years optimizing repeated builds around persistent processes because repeated builds are the common case.

A compile-time framework should be judged in that environment.

---

## Build Cache and Configuration Cache Solve Different Problems { #build-cache-and-configuration }

It is also important not to treat “cache” as one vague acceleration mechanism.

Gradle’s build cache reuses task outputs. If a cacheable compilation or generation task sees the same inputs, Gradle may restore the previous outputs rather than execute the task again.

The configuration cache reuses the configured task graph and related state. It reduces the time spent evaluating project configuration before task execution.

For a short incremental build, configuration overhead can become a surprisingly large fraction of total latency. If actual compilation after a small edit takes only a modest amount of time but Gradle spends substantial time configuring a large multi-module project, optimizing only annotation processing misses the real bottleneck.

This is another reason framework-level claims about compilation need end-to-end measurements.

The user does not care whether 300 milliseconds were spent inside javac, an annotation processor, Gradle configuration, Kotlin compilation, dependency resolution, or packaging. The user experiences the sum.

Optimization work should follow the critical path, not the most visible framework mechanism.

---

## Incremental Compilation Is the Real Battlefield { #incremental-compilation-is-the }

The strongest version of the criticism against compile-time generation is not that processors consume time during a clean build. That is obvious.

The serious concern is whether generation damages incremental compilation.

If changing one class causes processors to invalidate an entire module, regenerate a large source tree, and force broad recompilation, then the cost can directly damage local feedback. If this happens frequently enough, compile-time architecture becomes a developer-experience problem regardless of runtime benefits.

This is the right concern to measure.

A well-designed compile-time framework therefore needs to care about locality. Generated outputs should correspond as closely as practical to the declarations that require them. Unrelated edits should avoid unnecessary regeneration. Generated source should remain simple enough that compiling it is cheap. The application-wide graph, which by definition has global relationships, should be generated efficiently and only when inputs affecting that graph require reevaluation.

There will always be edits that legitimately affect broader structure. Adding or removing components can change dependency resolution. Changing modules can modify the graph. Altering shared contracts can invalidate downstream consumers.

That is not wasted work. The compiler is answering a new architectural question.

The useful comparison is how much extra work the framework causes beyond the minimum logically required by the change.

This cannot be inferred from the phrase “compile-time DI.” It has to be benchmarked.

---

## Kotlin Makes the Question More Complicated { #kotlin-makes-the-question }

Kotlin projects add another dimension because source processing can interact with Kotlin compiler infrastructure differently from plain Java annotation processing.

Historically, Kotlin projects often used kapt to bridge Java annotation processors into Kotlin builds. Kapt can introduce stub-generation and processing overhead, and its incremental characteristics depend on processors and project configuration. Modern Kotlin ecosystems may instead use KSP or native compiler-plugin mechanisms for some forms of generation.

The important point for a framework comparison is that “Kora compilation time” is not necessarily one universal value across Java and Kotlin applications.

Java and Kotlin compilation pipelines have different costs. Processor implementations can have different integration paths. Mixed-language modules behave differently from pure Java modules. The number of generated declarations, generic complexity, and compiler version can all matter.

A credible benchmark should therefore specify the language and generation path rather than generalize from one to the other.

This does not weaken the broader argument. It reinforces it: compile-time generation must be measured as an actual build system, not classified by mechanism.

---

## Why Simple Generated Code Matters { #why-simple-generated-code }

Generated source has a downstream cost because the compiler must compile it. That creates a straightforward design pressure: generated code should be simple.

Kora’s broader philosophy helps here. The framework emphasizes thin abstractions and direct generated implementations rather than large runtime interpretation layers. This approach can also make generated sources relatively ordinary from the compiler’s perspective.

Simple code generally means fewer surprises for javac and kotlinc. Straight-line constructor wiring, explicit method calls, ordinary repository implementations, and direct adapters are different from deeply nested type-level machinery or enormous generated DSL structures.

This matters not only for build time but also for debugging.

If generated code is readable enough that developers can inspect it, it is usually also structured enough that compiler diagnostics and profilers can identify where work is happening. Generation becomes part of the application’s explainable implementation rather than an opaque binary transformation.

That is valuable when optimizing builds. Teams can count generated files, inspect their size, profile annotation-processor execution, examine compiler task invalidation, and correlate source changes with generated outputs.

The framework does not need to be defended abstractly. The work can be measured.

---

## The Work That Disappears at Runtime { #the-work-that-disappears }

The central mistake in the “compile-time generation is slower” argument is often that it counts added compile work without counting removed runtime work.

Consider dependency injection.

A runtime-oriented container may need to discover candidate components, inspect metadata, resolve dependencies, construct proxy definitions, determine lifecycle relationships, and validate parts of the container during startup.

Kora builds and validates the dependency graph during compilation. The runtime begins with much more of that structure already known.

Consider AOP.

A proxy-oriented framework may create proxy classes or runtime interception structures around eligible components. Kora can generate the relevant subclass or wrapper ahead of time.

Consider HTTP mappings.

Runtime frameworks can discover controller metadata and build routing structures while initializing the application. Kora can move substantial parts of that derivation into generated handlers.

Consider repositories and mapping.

Dynamic proxy construction, reflective mapping, metadata inspection, or runtime implementation assembly can be replaced by generated code that already knows what operations to perform.

These runtime costs do not necessarily dominate every framework startup. Modern frameworks cache metadata, optimize scanning, index classes, and perform substantial ahead-of-time work of their own. The comparison must remain empirical.

But architecturally the trade is clear: work performed once during build does not need to be rediscovered identically each time a process starts.

This is why startup belongs in the feedback-loop equation.

---

## Application Startup Is Development Time Too { #application-startup-is-development }

Developers often talk about build time and startup time as if they belong to separate domains.

Build time is considered developer experience.

Startup time is considered production performance.

In reality, startup time belongs to both.

Every time a developer runs the application after a change, startup lies directly on the feedback path. Every integration test that creates the full application context pays some fraction of startup cost. Every black-box test that launches a service process pays it. Every CI stage that starts several services pays it. Every local test environment that repeatedly tears down and recreates applications pays it.

A framework that compiles 500 milliseconds faster but takes several additional seconds to initialize a realistic application context may deliver a worse edit-test loop.

The exact numbers depend on the applications being compared, but the accounting principle is universal.

The full local loop is approximately:

```text
feedback latency
=
build system overhead
+ incremental compilation
+ code generation
+ test discovery
+ application/context startup
+ test execution
+ shutdown/cleanup
```

Optimizing only one term can make the total slower.

Kora’s design is intentionally favorable to the startup portion because the application graph and much framework infrastructure have already been built. The landing page places startup/readiness next to clean and cached build charts for exactly this reason: the three measurements belong in one performance story.

Compile-time work and startup work are connected.

---

## The Landing Page’s Three Charts Should Be Read Together { #the-landing-page-s }

The Kora landing page presents startup/readiness, clean build, and cached build as separate views of the same broader engineering trade.

That is more important than any single bar.

The startup benchmark uses ten PetClinic services with production integrations inside a constrained Docker environment. The purpose is to measure how quickly applications become ready to serve traffic.

The clean artifact build deliberately removes Gradle optimizations: no build cache, no configuration cache, no parallel build, and no persistent Gradle daemon. Kora produces its distribution artifact; Spring produces its executable application artifact. The result is averaged across repeated runs.

The cached artifact build changes the conditions to something much closer to an optimized development build: Gradle build cache, configuration cache, daemon, parallel execution, multi-module organization, and incremental compilation are enabled.

These scenarios answer different questions.

The clean chart asks how expensive the entire pipeline is when previous work cannot be reused.

The cached chart asks how the pipeline behaves when the build tool is allowed to do what modern build tools are designed to do.

The startup chart asks what happens after compilation has finished.

A framework with compile-time generation should be evaluated across all three.

If compile-time generation made artifact production catastrophically slower, that would appear in the clean scenario.

If it fundamentally prevented effective incremental development, that would appear in the cached scenario.

If it successfully moved useful work out of runtime, that should appear in startup and context-creation scenarios.

The correct conclusion is not that one chart “proves” a framework is faster universally. Benchmark results are always bounded by hardware, application shape, plugins, versions, JVM, Gradle configuration, filesystem state, and the exact changes being measured.

The useful conclusion is methodological: compile-time generation cannot be evaluated from annotation-processor presence alone. The complete pipeline must be measured.

---

## Artifact Build Performance Can Be Competitive Even With Generation { #artifact-build-performance-can }

There is an intuitive model in which Spring-like runtime frameworks “just compile the code” while compile-time frameworks “compile the code plus run a framework compiler,” making the latter inevitably slower.

Modern frameworks do not divide that cleanly.

A production Spring application may involve annotation processing of its own, configuration metadata generation, code generation from OpenAPI or database schemas, bytecode enhancement, test instrumentation, packaging work, resource processing, layered archive creation, and framework plugins. Projects also commonly use Lombok, MapStruct, QueryDSL, jOOQ generation, protobuf, gRPC, Avro, Kotlin compiler plugins, and other build-time systems independently of the main framework.

Likewise, a Kora project does not necessarily execute every Kora processor for every module. The enabled modules and declarations determine what generation is needed.

The artifact build is therefore the sum of the real build graph, not a binary distinction between “generated” and “not generated.”

For small and medium backend services, it is entirely plausible for a compile-time framework’s full artifact build to remain competitive with a runtime-oriented framework because the generation itself can be relatively cheap compared with Java/Kotlin compilation, dependency processing, packaging, tests, and general Gradle overhead.

That claim should never be asserted as a universal law. It should be demonstrated with reproducible benchmarks for representative services.

The Kora landing benchmark is best read as one such data point, not as a theorem.

A team evaluating Kora should repeat the comparison with its own application shape.

---

## Why “Annotation Processor Time” Is the Wrong Primary Metric { #why-annotation-processor-time }

Profiling annotation processors is useful engineering work. It can reveal regressions, expensive analysis, excessive generation, or non-incremental behavior.

It is not the primary user metric.

Suppose Framework A spends:

```text
1.2 s compile
0.0 s generation
4.0 s startup
2.0 s test
```

and Framework B spends:

```text
1.5 s compile
0.7 s generation
0.5 s startup
2.0 s test
```

Framework B has a much larger visible compile-time generation cost but a shorter total loop.

Now suppose incremental build tooling allows most of Framework B’s generation to be skipped after an ordinary method-body change:

```text
0.8 s incremental compile
0.1 s relevant generation
0.5 s startup
2.0 s test
```

The clean processor benchmark has become almost irrelevant to the common iteration.

These numbers are illustrative, not Kora benchmark results. Their purpose is to show why the unit of measurement changes the conclusion.

The developer is waiting for the result, not for the processor.

That makes wall-clock feedback latency the primary metric and processor time a diagnostic metric.

---

## Compile-Time Errors Can Shorten the Loop Even When Compilation Takes Longer { #compile-time-errors-can }

There is another dimension that ordinary stopwatch benchmarks often miss: not all feedback has equal value.

Consider a missing dependency.

In a compile-time DI model, the build can fail while compiling the graph. The developer receives a diagnostic without successfully starting the process.

In a runtime DI model, source compilation may succeed. Packaging may succeed. The developer starts the application. The framework initializes. Only when the container reaches the invalid dependency does the failure appear.

Even if the compiler-first model spends more time before producing its error, it may still produce useful feedback sooner.

The same principle applies to ambiguous components, invalid generated mappings, unsupported repository contracts, incorrect aspect usage, and other structural problems that can be statically validated.

This changes the shape of debugging.

A runtime failure often produces:

```text
edit
↓
compile
↓
package
↓
start
↓
initialize framework
↓
fail
```

A compile-time failure can produce:

```text
edit
↓
compile
↓
fail
```

When the failure is architectural, skipping runtime is a meaningful savings.

This is especially relevant in automated coding loops, but it is equally relevant to human developers. The best feedback is not only fast; it is early and specific.

---

## Fast Failure Is Part of Build Performance { #fast-failure-is-part }

Traditional benchmark discussions separate correctness diagnostics from performance, but developers experience them together.

Imagine two builds.

Build A completes compilation in four seconds and then requires an eight-second application startup before reporting a wiring error.

Build B spends six seconds compiling and reports the same problem immediately.

If the developer’s goal is to fix the wiring problem, Build B has the faster feedback loop despite having the slower compiler.

The distinction becomes even more important when repeated several times while developing a new feature. Early failures prevent wasted startup, test discovery, network setup, container initialization, and other downstream work.

Kora’s compile-time graph validation is therefore not merely a correctness feature. It can be a latency optimization for invalid iterations.

That is difficult to summarize in one build-time bar, but it is real developer time.

---

## Component and Integration Tests Change the Equation { #component-and-integration-tests }

Unit tests that instantiate plain classes are largely framework-independent. The interesting differences appear when tests need framework context.

Component tests may need dependency injection, configuration, generated handlers, aspects, or selected infrastructure modules.

Integration tests may start the full application, connect Testcontainers-backed databases or brokers, initialize HTTP servers, and verify actual framework wiring.

Black-box tests may repeatedly launch one or more service processes.

In these tests, context startup becomes part of test runtime.

Kora’s testing model benefits from the fact that production wiring is already explicit and generated. Test components can replace dependencies, configuration can be overridden, and the graph can be assembled without performing the same degree of runtime discovery expected from a heavier dynamic container.

The performance consequence is straightforward: if application contexts are cheap to create, higher-level tests become cheaper to run frequently.

This can matter more than shaving a small amount from compilation because developers often tolerate slow integration tests by running them less frequently. A framework that makes them cheap enough to run continuously changes behavior, not just benchmark numbers.

The feedback loop improves because validation becomes both faster and more comprehensive.

---

## CI Feedback Is Also a Development Loop { #ci-feedback-is-also }

The same argument extends beyond the laptop.

A pull request often triggers:

```text
checkout
↓
configure build
↓
compile
↓
generate
↓
unit tests
↓
start integration services
↓
start application contexts
↓
integration tests
↓
package
↓
publish result
```

Developers wait for that pipeline before merging or discovering failures.

A framework’s build-time generation contributes to one portion of the critical path. Startup contributes to another. Test-context creation contributes to another. Cacheability can eliminate large parts of the build altogether.

Remote Gradle build caches make this especially interesting. If CI agents or developers can reuse cacheable outputs generated elsewhere for identical inputs, the cost model of compile-time generation changes again. Work that appears expensive in an isolated cold benchmark may be performed once and reused many times.

This does not happen automatically. Tasks and processors have to participate correctly in Gradle’s model, cache keys must reflect inputs accurately, and infrastructure must be configured sensibly.

But when evaluating compile-time code generation as an architecture, cacheability is part of the architecture’s real operational environment.

---

## The Hidden Advantage of Deterministic Generation { #the-hidden-advantage-of }

Compile-time generation has another property that can improve build systems: deterministic work is easier to cache.

If a generator produces the same output for the same declared inputs, its result is a natural candidate for build caching. The more deterministic and isolated the generation is, the more confidently a build system can reuse outputs.

Runtime discovery cannot help a local build cache in the same way because the work occurs after the build has already completed, during each process startup.

This does not mean runtime frameworks cannot optimize startup. They can precompute indexes, persist metadata, introduce AOT modes, or cache internal structures in various ways. Indeed, the JVM framework ecosystem has increasingly moved toward more ahead-of-time processing precisely because repeated runtime discovery has costs.

The broader trend is therefore not “compile time versus runtime” as two static camps. It is a continuum of how much deterministic work a framework chooses to precompute.

Kora starts much farther toward the compile-time end of that continuum.

---

## Clean Builds Still Matter { #clean-builds-still-matter }

Arguing for end-to-end feedback metrics should not become an excuse to ignore clean-build regressions.

Clean builds matter for several reasons.

New developer environments perform them. Fresh CI agents perform them unless remote caches are effective. Dependency upgrades and branch switches can invalidate caches. Major refactors can force broad recompilation. Release pipelines may intentionally use clean workspaces. Build reproducibility investigations often begin from a cold state.

A framework that adds ten or twenty minutes to clean compilation would have a real problem even if incremental builds were excellent.

The correct position is therefore not “clean builds do not matter.”

It is:

> Clean builds are one workload among several, and their importance depends on how frequently they occur and whether their outputs can be reused.

Kora should be benchmarked and optimized there too.

The myth-busting argument succeeds only if it remains willing to admit where compile-time generation costs time.

---

## When Compile-Time Generation Really Can Make Development Slower { #when-compile-time-generation }

There are conditions under which the criticism becomes correct.

If generated work is globally invalidated by small edits, development gets slower.

If processors are not incremental, development can get slower.

If generated code becomes enormous, compiling it can get slower.

If a processor performs expensive classpath-wide searches repeatedly, development can get slower.

If Kotlin processing requires costly stub generation and broad reprocessing, development can get slower.

If build plugins are incompatible with configuration caching, build-system overhead can remain unnecessarily high.

If project module boundaries cause small changes to invalidate large dependency cones, feedback can get slower regardless of framework.

If generated code triggers additional compiler rounds or pathological type inference, development can get slower.

If processors do I/O, network access, non-deterministic discovery, or other work poorly suited to compilation, development can get much slower.

If framework generation is fast but the project attaches dozens of unrelated code generators to every compilation, the combined pipeline can still be slow.

None of these problems can be dismissed by saying “the runtime is faster.”

Developer experience deserves its own performance budget.

A compile-time framework has to earn its design by keeping the compile-time portion disciplined.

---

## Framework Authors Should Treat Build Latency as a First-Class Performance Metric { #framework-authors-should-treat }

Runtime throughput has mature performance culture. Teams publish requests per second, latency percentiles, allocation rates, startup time, memory footprint, and CPU profiles.

Build performance deserves similar rigor.

A compile-time framework should ideally track:

- clean Java compilation;
- clean Kotlin compilation;
- clean artifact build;
- warm artifact build;
- incremental method-body change;
- incremental dependency-graph change;
- incremental repository-contract change;
- incremental HTTP-contract change;
- incremental configuration change;
- generated source count;
- generated source size;
- annotation-processing time;
- compiler time;
- Gradle configuration time;
- cache hit behavior;
- configuration-cache compatibility;
- test-context startup;
- full integration-test iteration.

Those measurements can be placed under continuous performance testing just like runtime benchmarks.

If a release causes an ordinary method change to trigger significantly broader regeneration, that is a regression.

If a new module adds large generated sources, that is a regression candidate.

If configuration-cache compatibility breaks, that is a build-performance concern.

Once compile-time generation is treated as infrastructure rather than magic, its cost becomes measurable and optimizable.

That is exactly how it should be approached.

---

## Teams Should Benchmark the Workflow They Actually Use { #teams-should-benchmark-the }

A team deciding between frameworks should resist generic claims from both sides.

Instead, build a representative service.

Include the technologies the production service will actually use: database access, HTTP endpoints, telemetry, configuration, resilience, security, migrations, messaging, and whatever else materially affects startup and build behavior.

Then define representative changes.

For example:

```text
Scenario 1
Change a line inside business logic.

Scenario 2
Add a constructor dependency.

Scenario 3
Add a repository method.

Scenario 4
Add an HTTP endpoint.

Scenario 5
Change a shared DTO.

Scenario 6
Change configuration schema.

Scenario 7
Run one component test.

Scenario 8
Run one Testcontainers-backed integration test.

Scenario 9
Produce a deployable artifact from a clean checkout.
```

Measure each scenario repeatedly.

Record wall-clock time as well as build scans or profiler data explaining where time went.

Keep the hardware, JDK, Gradle version, compiler version, filesystem state, and JVM settings controlled.

Run both cold and warm scenarios.

Do not silently disable the build optimizations developers normally use and then call the result “developer experience.”

Do not silently keep warmed caches and then call the result “clean build performance.”

Label each number honestly.

That methodology will reveal whether compile-time generation is actually a problem for the project.

---

## Why Multi-Module Architecture Matters { #why-multi-module-architecture }

Large JVM services are often divided into modules for architecture, ownership, dependency control, and build performance.

Module boundaries can strongly influence generation cost.

Suppose an application has separate modules for domain logic, HTTP adapters, database access, integrations, and the final application graph. A domain-only change may not require repository or HTTP generation. A repository change may avoid recompiling unrelated adapters. A final graph module can contain the global wiring boundary.

That kind of structure gives Gradle more opportunities to execute and cache work independently.

By contrast, placing thousands of classes and every processor into one giant module increases the chance that structurally unrelated changes participate in the same compiler invocation.

This observation is framework-neutral, but it matters more when evaluating code generation because processor scope is tied to compilation scope.

A Kora project that cares about large-scale build performance should therefore view module design not only as architectural organization but also as an incremental-build boundary.

Good architecture and good build behavior often reinforce each other.

---

## “More Work at Compile Time” Can Mean Less Work Everywhere Else { #more-work-at-compile }

The trade becomes easier to see if we draw it as a pipeline.

A runtime-heavy model may look conceptually like:

```text
source
  ↓
compile
  ↓
artifact
  ↓
start JVM
  ↓
scan/discover metadata
  ↓
build runtime container
  ↓
create proxies/adapters
  ↓
validate wiring
  ↓
start application
```

A compile-time-oriented model moves several of those stages earlier:

```text
source
  ↓
compile
  ├─ validate graph
  ├─ generate wiring
  ├─ generate handlers
  ├─ generate repositories
  ├─ generate aspects
  └─ generate mappings
  ↓
artifact
  ↓
start JVM
  ↓
construct precomputed graph
  ↓
start application
```

The second compile stage is heavier because it contains more useful work.

The second startup stage can be lighter because less framework interpretation remains.

Neither pipeline is automatically faster. The relative costs must be measured.

But calling the second approach “slow development” merely because the compiler performs more steps confuses where work happens with how long the complete workflow takes.

---

## This Is Similar to Database Query Planning { #this-is-similar-to }

A useful analogy comes from databases.

Suppose one system performs more query planning up front but then executes the query efficiently. Another begins execution quickly but discovers or optimizes more dynamically during execution.

It would be strange to compare them solely by planning time if the user cares about time to result.

Planning latency matters, especially for short queries. But it is one component of a larger latency budget.

Compile-time framework generation is similar.

The build performs planning.

Startup and request processing consume the plan.

The right balance depends on how often the plan changes, how reusable the result is, and how much execution cost it removes.

Incremental compilation and build caching improve the economics because they make the planning work reusable across edits.

---

## The Feedback Loop Is the Product { #the-feedback-loop-is }

For a developer, a framework is not experienced as a set of internal implementation techniques. It is experienced as a loop.

You edit.

The toolchain answers.

You run.

The application becomes ready.

The test executes.

You see whether your idea worked.

Then you repeat.

Every framework optimization should ultimately be judged by how it changes that cycle.

Kora’s compile-time architecture can improve the loop in several ways simultaneously:

- invalid graph states can stop at compilation;
- generated code eliminates runtime discovery for many mechanisms;
- application startup can remain small because the graph is already known;
- component and integration tests can initialize contexts quickly;
- generated sources expose what the framework built;
- Gradle can reuse unaffected work across incremental builds.

Against those benefits, Kora pays annotation-processing and generated-source compilation costs.

That is the actual balance sheet.

Anything less is incomplete.

---

## Why Fast Startup Becomes More Valuable as Tests Become More Realistic { #why-fast-startup-becomes }

Modern backend tests increasingly blur the line between unit and integration tests. Testcontainers makes it practical to run real databases, Kafka brokers, Redis, or other infrastructure. HTTP-level tests can exercise almost the complete application stack. Contract tests may start real server components rather than mocks.

As tests become more realistic, framework startup occupies a larger share of the iteration budget.

If an application context takes ten seconds to initialize and the actual assertion takes 200 milliseconds, optimization effort should obviously target context initialization before obsessing over a 100-millisecond compiler difference.

This does not imply that every Kora test starts a full application or that every competing framework necessarily starts slowly. It means startup is structurally part of modern test economics.

Kora’s landing page explicitly connects fast startup with development and CI feedback because integration and black-box suites often start applications repeatedly.

This is the point that compile-only comparisons miss most often.

---

## Runtime Failures Have a Debugging Tax Beyond Their Timestamp { #runtime-failures-have-a }

There is also a qualitative difference between compiler errors and startup errors.

A compiler error usually appears near the code and type relationships that caused it. IDEs parse it. Build tools surface it directly. An AI coding agent can feed it into the next edit loop. Developers do not need to inspect application logs after partial container initialization.

A runtime container error can include nested causes, proxy classes, framework lifecycle stages, reflection exceptions, conditional configuration, or classpath state. Modern frameworks have improved these diagnostics substantially, but the developer still has to reach the runtime phase before receiving them.

The time cost is therefore not only:

```text
compile versus compile + startup
```

It may also include interpretation time.

Precise compile-time diagnostics reduce uncertainty about the invalid state.

That is part of feedback quality.

---

## The Same Argument Matters Even More for AI Coding Agents { #the-same-argument-matters }

Although the development-speed question applies directly to humans, AI coding agents make the loop especially visible.

An autonomous coding agent often works approximately like this:

```text
inspect code
↓
make edit
↓
compile/test
↓
read diagnostics
↓
make next edit
```

The cost of each iteration determines how many corrections can be attempted within a given amount of time.

For such a system, compile-time validation can be particularly efficient because structural mistakes become machine-readable diagnostics before the process starts. Fast application-context initialization makes integration verification cheaper. Deterministic generated sources can also help the agent understand the framework behavior it is testing.

But the principle is not fundamentally about AI.

AI simply makes the feedback loop impossible to ignore.

Human developers have always depended on the same cycle.

---

## Build Optimization Should Focus on Work Avoidance { #build-optimization-should-focus }

The most important idea in modern build performance is not “make every individual operation faster.”

It is “do less unnecessary work.”

A ten-millisecond processor that executes 5,000 unnecessary times can be worse than a 500-millisecond processor that runs only when its real inputs change.

Gradle’s incremental model, build cache, and configuration cache all follow this principle. The fastest task is the one that does not execute because its output is already valid.

Compile-time frameworks should align with that philosophy.

Generated outputs should have precise inputs.

Tasks should be cacheable where correctness permits.

Processors should avoid reading undeclared environmental state.

Unrelated source changes should avoid invalidating unrelated outputs.

Application graph generation should minimize unnecessary global churn.

Generated code should be deterministic.

When those properties hold, the fact that generation exists becomes much less important than how often it actually has to run.

---

## The Real Cost Model Is Frequency × Latency { #the-real-cost-model }

A useful way to think about framework build performance is:

```text
developer cost
≈
Σ (frequency of workflow × latency of workflow)
```

A clean artifact build taking ten seconds longer matters differently if it runs once per day than if an incremental test loop takes two seconds longer and runs 200 times per day.

For example:

```text
clean build:
+10 s × 2 per day = +20 s

incremental test:
-1 s × 150 per day = -150 s
```

Even if the compile-time framework loses the clean build, it can still save developer time overall.

Again, those numbers are illustrative. The equation is what matters.

This is why benchmark weighting should reflect workflow frequency.

Organizations with enormous release pipelines may weight clean CI builds more heavily. Teams with remote build caches may nearly eliminate that concern. Services with intensive local integration testing may weight startup much more heavily. Large Kotlin monoliths may care disproportionately about incremental compiler behavior.

There is no universal weighting.

There is only a universal need to measure the correct workload.

---

## Clean Build Numbers Are Still Valuable for Framework Engineering { #clean-build-numbers-are }

Although developer iteration should dominate the UX discussion, clean builds remain useful diagnostics for framework authors.

They expose total framework-generation cost without cache reuse.

If generation becomes significantly more expensive between releases, the clean benchmark will detect it even if warm builds temporarily hide the regression.

Clean builds also establish an upper bound for environments where caches are unavailable.

The ideal benchmark suite therefore contains both clean and incremental scenarios rather than choosing one camp.

This is another reason the Kora landing page’s chart structure is sensible: it avoids collapsing the problem into one headline metric.

---

## Startup Should Be Included in Framework Build Benchmarks More Often { #startup-should-be-included }

One provocative implication follows from this argument: framework build benchmarks that claim to represent development experience should often include startup.

Not production startup as a separate marketing number, but startup directly after the incremental build.

A realistic benchmark might be:

```text
1. Modify controller implementation.
2. Run the build required by local workflow.
3. Start the application.
4. Wait for readiness.
5. Execute one verification request.
6. Record total wall-clock time.
```

Another could be:

```text
1. Modify repository contract.
2. Run one integration test.
3. Record time until result.
```

These benchmarks measure what developers actually perceive.

They also expose framework tradeoffs naturally. Compile-time generation appears in step two. Runtime scanning and container initialization appear in step three. Database setup and test logic appear later.

No framework gets to hide its cost by moving it into another phase.

That is a much healthier comparison.

---

## A Better Benchmark Matrix { #a-better-benchmark-matrix }

For Kora and any competing framework, a useful matrix might look like this:

| Workflow | What It Measures |
| --- | --- |
| Clean compile | Raw compiler + generation cost |
| Clean artifact | Compiler + generation + packaging |
| Warm artifact | Repeated full build behavior |
| Method-body edit | Best-case ordinary incremental work |
| DI change | Incremental graph-generation cost |
| Repository change | Data code-generation invalidation |
| Controller change | HTTP generation invalidation |
| DTO change | Downstream compilation and mapping impact |
| Unit test | Framework-independent baseline |
| Component test | Graph/context construction cost |
| Integration test | Build + context + infrastructure |
| Restart after edit | Developer run-loop latency |
| Fresh CI | Worst-case pipeline |
| CI with remote cache | Real optimized pipeline |

A framework can then be described honestly.

Perhaps Kora pays slightly more for one structural incremental case and much less for startup. Perhaps one processor becomes expensive in Kotlin but not Java. Perhaps Spring’s clean artifact packaging is faster in a given project while Kora’s integration loop is shorter. Perhaps a specific application uses so little framework infrastructure that the difference is negligible.

Those are useful conclusions.

“Annotation processing is slow” is not.

---

## What the Kora Benchmark Does and Does Not Prove { #what-the-kora-benchmark }

The landing-page results should not be treated as universal evidence that every Kora project will build faster than every Spring project.

They use a specific PetClinic-style workload, specific integrations, specific build tasks, specific Gradle settings, specific hardware, and repeated runs under a defined environment.

Change the application shape and the result can change.

A generated-heavy Kora application with hundreds of repositories may behave differently from a tiny HTTP service. A Spring application carefully optimized for AOT and startup may behave differently from a stock application. Kotlin may change the balance. A remote build cache can transform CI behavior. A large corporate Gradle build with custom plugins may be dominated by configuration or dependency resolution rather than framework processing.

The benchmark is valuable because it disproves a simplistic assumption, not because it establishes a permanent ranking.

If a compile-time framework can produce competitive artifact-build results while also precomputing substantial runtime infrastructure, then the statement “code generation necessarily means slow builds” is already too strong.

The next step is to measure your workload.

---

## The Right Question for Kora Is Not “Does It Generate Code?” { #the-right-question-for }

It obviously does.

The better questions are:

How much code is generated?

How complex is it?

How much of generation is local versus application-wide?

Which changes invalidate which generated outputs?

How much of that work participates in incremental compilation?

Can Gradle reuse outputs from cache?

How does Java compare with Kotlin?

What happens on a constructor dependency change?

What happens on a business-logic-only change?

How quickly does the application start afterward?

How quickly can a component context start?

How quickly does an integration test return a result?

How often does compile-time validation prevent a wasted runtime cycle?

Those questions produce engineering answers.

---

## Compile-Time DI Should Be Judged by Total Graph Lifecycle Cost { #compile-time-di-should }

Dependency injection is a particularly useful case study because every framework has to solve the same conceptual problem: construct objects in a valid dependency order and manage their lifecycle.

The difference is when that problem is solved.

In Kora, graph structure is largely resolved during compilation.

A runtime container resolves more of it when the process initializes.

Suppose graph resolution costs some amount of CPU time. Paying that during compilation means it may be paid after graph-affecting source changes. Paying it at runtime means it may be paid every time a process or test context starts.

Which is cheaper depends on frequencies.

If a developer changes dependency topology occasionally but starts tests and services frequently, compile-time resolution may amortize well.

If an application graph changes constantly while processes rarely restart, the balance shifts.

Again, the right unit is lifecycle cost rather than isolated phase cost.

---

## Production Economics Reinforce the Same Trade { #production-economics-reinforce-the }

Although this article focuses on development, the same relocation of work affects production.

Compilation happens once per artifact.

An artifact may start many times: developer machines, tests, CI jobs, staging, rolling deployments, autoscaling events, node replacements, failover, scale-to-zero recovery, spot-instance replacement, and disaster recovery.

Work removed from startup is therefore potentially amortized across many process launches.

This production benefit does not justify arbitrarily slow builds. Developer time is valuable too.

But it explains why framework architects may rationally spend some build CPU to reduce startup CPU.

The relevant optimization target is the lifecycle of the artifact, not one invocation of javac.

---

## Compilation Is Also Easier to Provision Than Runtime Warm-Up { #compilation-is-also-easier }

There is another operational asymmetry.

Build infrastructure is often centralized, parallel, cacheable, and predictable. CI machines can be provisioned with substantial CPU. Build outputs can be shared. Compilation occurs outside the request path.

Runtime startup happens on machines that may already be resource constrained, during deploys or load spikes, at exactly the moment new capacity is needed.

A second of build time and a second of readiness delay therefore have different operational value.

Again, this does not mean build time is irrelevant. It means seconds are not interchangeable across phases.

Framework design has to price them differently.

---

## Why This Matters for Small Services { #why-this-matters-for }

Microservices strengthen both sides of the trade.

On one hand, a company may compile many services, so build cost multiplies.

On the other hand, small services start frequently across many environments and often have short test suites where framework initialization becomes a large fraction of runtime.

A five-second context startup is relatively unimportant in a 40-minute test suite. It is dominant in a 700-millisecond test body.

This is why lightweight service frameworks care so much about startup and build feedback simultaneously.

Kora’s architecture is aimed at that region: relatively small, explicit application graphs; generated infrastructure; thin integrations; fast startup; direct JVM code.

The compile-time cost should therefore be judged against the workload the framework targets.

---

## What Developers Should Watch in a Real Kora Project { #what-developers-should-watch }

If a Kora project begins feeling slow to build, do not start from the assumption that “annotation processing is the price of Kora.”

Measure.

Use Gradle profiling or build scans to identify the critical path.

Determine whether time is spent in configuration, dependency resolution, Java compilation, Kotlin compilation, Kora processing, tests, packaging, or custom plugins.

Compare a clean build with a warm build.

Compare a business-logic edit with a graph edit.

Check whether configuration cache is enabled and compatible.

Check whether the build cache is useful.

Inspect whether modules are unnecessarily coupled.

Look at generated-source volume.

Check compiler-daemon behavior.

Separate test execution time from context startup.

Measure application readiness independently.

If the Kora processors dominate, that is actionable evidence for framework optimization.

If Gradle configuration dominates, changing DI strategy will not fix the problem.

If Kotlin compilation dominates, generated Java may not be the main issue.

If tests dominate because external containers restart unnecessarily, annotation processing is a distraction.

Performance work becomes effective when the bottleneck is measured rather than assumed.

---

## Avoid Benchmark Theater { #avoid-benchmark-theater }

Framework performance discussions are especially vulnerable to benchmark theater because small configuration choices can produce dramatic results.

A fair comparison should avoid several traps.

Do not compare one framework with a warm daemon and another from a cold process.

Do not enable build cache for one and disable it for the other.

Do not compare a thin application in one framework with a production-integrated application in another.

Do not run different packaging tasks and describe them as identical without explaining the difference.

Do not compare startup before readiness in one framework with full readiness in another.

Do not ignore JVM version.

Do not ignore Kotlin versus Java.

Do not benchmark a single run.

Do not hide whether filesystem caches are warm.

Do not report only the scenario that produces the desired conclusion.

The Kora question is interesting enough without manipulating it.

---

## A Framework Can Shift Cost Without Increasing Total Cost { #a-framework-can-shift }

This is the key conceptual point.

Suppose a framework moves dependency analysis from runtime startup to compilation.

The compile stage becomes more expensive.

The startup stage becomes less expensive.

That is a cost shift.

Whether total cost rises depends on:

```text
added compile cost
-
removed runtime cost × number of runtime initializations
```

For development alone, replace runtime initializations with local application starts and test-context starts.

For CI, include pipeline starts.

For production, include deployments and scaling.

The same artifact can consume the result of one compilation many times.

Therefore, even a nontrivial build-time cost can be a good trade.

And if incremental compilation prevents that cost from being paid after every edit, the trade becomes even more favorable.

---

## The Myth Is Not That Compile-Time Generation Has No Cost { #the-myth-is-not }

A useful myth-busting article should not replace one oversimplification with another.

The false claim is not:

> Compile-time code generation adds build work.

That claim is true.

The false claim is:

> Because compile-time code generation adds build work, development must be slower.

That conclusion is unsupported without measuring the rest of the loop.

Kora provides an unusually clear example because it intentionally performs substantial framework work during compilation while also optimizing startup and exposing explicit generated code.

Its architecture forces us to use the right accounting model.

---

## The Metric That Actually Matters { #the-metric-that-actually }

For everyday development, the primary metric should be something like:

```text
T_feedback =
T_build_setup
+ T_incremental_compile
+ T_generation
+ T_context_start
+ T_test
```

For invalid structural edits, it may instead be:

```text
T_feedback =
T_build_setup
+ T_compile_until_diagnostic
```

For CI:

```text
T_ci =
T_checkout
+ T_configure
+ T_compile
+ T_generate
+ T_tests
+ T_context_starts
+ T_package
```

For clean release builds:

```text
T_release =
T_clean_build
+ T_test
+ T_package
```

A framework can optimize different equations differently.

No single annotation-processor timer answers all of them.

---

## What “Fast Compilation” Should Mean in 2026 { #what-fast-compilation-should }

Historically, fast compilation often meant how quickly a compiler could turn source files into class files.

For modern JVM backend projects, that definition is too narrow.

A developer invokes a build system, not javac in isolation. The build system configures plugins, resolves task graphs, runs source generators, compilers, resource processors, test engines, packaging steps, and sometimes containers. Persistent daemons and caches make later iterations different from the first.

The meaningful concept is therefore “time to actionable feedback.”

Compile-time generation should be included in that measurement, but it should not define it.

Kora’s design is well suited to that interpretation because compilation itself produces actionable architectural feedback. The compiler does not merely create bytecode; it verifies framework structure.

In that sense, some of the “extra compilation” is actually test work performed earlier.

---

## Compile-Time Validation Is a Form of Testing { #compile-time-validation-is }

This point deserves emphasis.

A compiler that validates dependency wiring, generated mappings, repository contracts, or aspect composition is executing assertions about the application.

Those assertions would otherwise need to be discovered later through startup or tests.

Viewed this way, some compile-time generation cost belongs conceptually in the verification budget, not merely the compilation budget.

The pipeline becomes:

```text
compile + structural verification
↓
runtime behavioral verification
```

rather than:

```text
compile
↓
runtime structural discovery
↓
runtime structural verification
↓
runtime behavioral verification
```

Moving deterministic verification earlier can shorten the path to useful failure.

That is a developer-experience feature even if javac’s stopwatch becomes larger.

---

## Why Kora’s Generated Sources Help Diagnose Build Behavior { #why-kora-s-generated }

One practical advantage of source generation rather than hidden runtime transformation is observability.

If a framework generates a class, developers can inspect it.

If an unexpectedly small source change produces hundreds of regenerated files, that can be observed.

If a graph class becomes enormous, that can be measured.

If a generated repository contains pathological generic structures, it can be profiled.

If generation changes between framework versions, source diffs can show what happened.

This transparency makes performance investigation less speculative.

The same philosophy that makes Kora runtime behavior understandable also helps make its build-time behavior understandable.

---

## What Would Falsify the Argument? { #what-would-falsify-the }

A serious engineering thesis should be falsifiable.

The argument that Kora’s compile-time generation need not slow development would be weakened if representative benchmarks showed that:

- ordinary method changes repeatedly trigger broad Kora regeneration;
- cached builds remain substantially slower because processors prevent effective incremental behavior;
- generated code causes significant compiler overhead even when structure is unchanged;
- context startup savings are too small to compensate for added build latency;
- integration-test loops are slower end to end;
- Kotlin processing imposes large recurring penalties;
- configuration-cache or build-cache behavior is poor in realistic Kora projects.

If those results appeared consistently, the correct response would be to optimize the framework, not to redefine the metric.

Myth-busting should defend measurement, not a predetermined winner.

---

## A Better Claim { #a-better-claim }

The strongest defensible claim is therefore modest but important:

> Compile-time code generation does not tell you whether development is slow.

You need additional information.

How much work is generated?

How often does it rerun?

What invalidates it?

Can outputs be reused?

How fast does the application start afterward?

How early are failures detected?

How expensive are component and integration tests?

What is the end-to-end latency of the edit-test loop?

Only then can you say whether compile-time generation helps or hurts.

---

## The Kora Trade in One Diagram { #the-kora-trade-in }

Kora’s design can be summarized as a movement of framework work:

```text
                         Kora build
                            │
              ┌─────────────┼─────────────┐
              │             │             │
        resolve graph   generate code   validate
              │             │             │
              └─────────────┼─────────────┘
                            ↓
                      explicit artifact
                            ↓
                   small runtime startup
                            ↓
                     direct execution
```

The cost is concentrated earlier.

The benefit appears later.

Gradle’s incremental machinery determines how often the earlier cost must actually be repaid.

That last sentence is the one most simplistic discussions leave out.

---

## From Compiler Cost to Feedback-Loop Engineering { #from-compiler-cost-to }

Once the problem is framed correctly, framework optimization becomes feedback-loop engineering.

The compiler should validate as much deterministic structure as possible without performing unnecessary global work.

Generated code should be direct and inexpensive to compile.

Gradle integration should preserve incremental compilation.

Tasks should be cache-friendly.

Application startup should consume precomputed structure rather than rediscover it.

Testing APIs should make context creation cheap.

Diagnostics should be precise enough that invalid iterations stop early.

Those properties reinforce each other.

A framework that performs compile-time generation badly can absolutely produce frustrating builds.

A framework that performs it well can use the compiler as part of a fast development system.

---

## The Broader JVM Trend Is Moving in This Direction Anyway { #the-broader-jvm-trend }

Kora is not alone in recognizing the value of moving deterministic work earlier.

Across the JVM ecosystem, frameworks increasingly use indexes, ahead-of-time analysis, generated metadata, generated proxies, native-image configuration generation, build-time augmentation, compile-time DI, and other forms of precomputation.

The exact implementation philosophies differ, but the trend reflects the same engineering reality: runtime discovery has costs, and many framework decisions do not actually need to wait until runtime.

This makes the old binary classification—“runtime framework fast to compile, compile-time framework slow to compile”—increasingly obsolete.

Modern frameworks occupy different points on an AOT spectrum.

The meaningful comparison is how effectively each one manages the full lifecycle.

---

## Build Performance Is a System Property { #build-performance-is-a }

This leads to a final general lesson.

Build speed is not a property of an annotation processor.

It is a property of a system.

That system includes:

- project architecture;
- module boundaries;
- source language;
- compiler;
- processors;
- generated code;
- Gradle version;
- plugin behavior;
- daemon state;
- build cache;
- configuration cache;
- incremental compilation;
- hardware;
- filesystem;
- test design;
- application startup;
- external test infrastructure;
- CI topology.

Framework design influences many of these, but no one mechanism determines the result alone.

Whenever someone says “annotation processing makes builds slow,” the correct response is not “no, it does not.”

The correct response is:

> Show the workflow.

---

## Conclusion: Measure Time to Knowledge { #conclusion-measure-time-to }

Compile-time generation undeniably performs work. Kora builds and validates its dependency graph, generates repositories and handlers, creates aspects and mappings, and turns declarative framework contracts into ordinary source code before the application starts. That work consumes build time and should be profiled, benchmarked, and optimized just like runtime performance.

But compilation time is not synonymous with development time.

Developers care about how quickly a change becomes knowledge.

Did the code compile?

Is the graph valid?

Can the application start?

Does the test pass?

If something is wrong, how soon do we know?

The real feedback loop is:

```text
change
  ↓
incremental compile
  ↓
start application/context
  ↓
run test
  ↓
get result
```

In that loop, moving work to compilation can be beneficial if the work is efficiently incremental, if Gradle can avoid repeating unaffected tasks, if generated code remains simple, if structural errors fail before runtime, and if application/context startup becomes correspondingly cheaper.

That is why a clean build benchmark is necessary but insufficient. It measures the cold cost of producing an artifact. It does not describe the repeated workflow developers spend most of their day inside. Cached builds, incremental compilation, the Gradle daemon, build cache, configuration cache, module isolation, startup time, and test-context creation all belong in the same analysis.

Kora’s architecture makes the trade unusually visible because the framework is explicit about both sides. Graph generation adds build work. The payoff is that much of the framework is already constructed, validated, and represented as direct code before the JVM starts serving the application.

The right conclusion is therefore not that compile-time generation is free, nor that compile-time frameworks always build faster.

It is more precise:

> **Compile-time generation is not synonymous with slow compilation. What matters is how much work is generated, how incrementally that work can be rebuilt, and how much runtime work disappears as a result.**

And for developers, the final metric should be even broader:

> **Do not optimize time spent inside the compiler in isolation. Optimize time from changing the code to knowing whether the change works.**

That is the feedback loop that matters.
