---
title: Compile-Time DI at Scale — How the Kora Framework Keeps Large Projects Fast
date: 2026-08-05
description: How the Kora Framework uses @KoraSubmodule and Gradle modularization to keep compile-time dependency injection fast in large codebases.
search:
  exclude: true
---
# Compile-Time DI at Scale: How Kora Keeps Large Projects Fast { #compile-time-di-at-scale }

**August 5, 2026**

Compile-time dependency injection has an obvious attraction: move dependency discovery, graph validation, and wiring out of application startup and into the compiler, then start the service with an
already known graph. The runtime becomes simpler, startup becomes more deterministic, and many errors that would otherwise appear only when a container is created become ordinary compilation failures.

There is also an obvious objection.

If the framework does more work during compilation, what happens when the application becomes large?

The naive picture is easy to draw:

```text
Huge monolithic compilation unit
        ↓
many components
        ↓
large dependency graph
        ↓
more annotation-processing work
        ↓
more invalidation after every change
        ↓
slower developer feedback
```

If that were the only possible architecture, compile-time DI would eventually run into a scaling problem of its own. The framework would save runtime work by concentrating more and more work into one
enormous compilation step. A change to a small feature could force the compiler and dependency-injection processor to reconsider a large part of the application. In that world, the objection would be
valid.

But a large application does not have to remain one enormous compilation unit.

That distinction is central to understanding how the Kora Framework approaches compile-time dependency injection in a large codebase. Kora does not require every component in a service to live under one Gradle
project and then ask a single annotation-processing invocation to rediscover the entire service after every edit. Its dependency-injection model includes an explicit mechanism for multi-module
applications: `@KoraSubmodule`.

That changes the scaling model.

A sufficiently large service can instead look like this:

```text
application
├── users
├── billing
├── orders
├── notifications
├── catalog
└── infrastructure
```

Each domain is a Gradle module. Each module is compiled independently. Each module can expose its Kora declarations through a submodule boundary. The final application module remains the composition
root, but it no longer needs every source file from the entire codebase to belong to its own compilation unit.

The resulting build topology is closer to this:

```text
Large codebase
        ↓
Gradle modules
        ↓
KoraSubmodule boundaries
        ↓
independent compilation
        ↓
incremental rebuild of affected modules
        ↓
final Kora graph composition
```

This leads to a more useful way to think about compile-time DI at scale:

> **Compile-time DI does not imply compiling the entire application from scratch after every edit. In a properly modularized codebase, compile-time boundaries and architectural boundaries can be the
same thing.**

That is a much stronger model than merely hoping an annotation processor becomes fast enough to survive an indefinitely growing monolith. It makes build scalability partly an architectural property.
The same module boundaries that reduce coupling, make ownership clearer, and constrain dependency direction can also limit how much framework processing has to happen after a local change.

Kora's approach is therefore not only "do DI at compile time." The more interesting idea is that compile-time DI can participate in the normal incremental build model of a modular JVM application.

## The Cost Model of Compile-Time Dependency Injection { #cost-model }

To understand why modularization matters, it helps to separate several kinds of work that are often collapsed into the phrase "compile time."

A Kora build does not simply run one mysterious DI phase. The build has a task graph, the compiler has source inputs, annotation processors or KSP have their own inputs and outputs, generated source
is compiled, and Gradle decides which tasks are up to date, which can be restored from cache, which can execute in parallel, and which downstream modules actually need recompilation.

At a high level, a Kora compilation may include work such as:

```text
Source compilation
├── language compilation
├── annotation processing / KSP
│   ├── component discovery
│   ├── graph analysis
│   ├── generated factories
│   ├── generated repositories
│   ├── generated mappers
│   ├── generated HTTP code
│   └── generated AOP code
└── compilation of generated sources
```

That work is real. Kora intentionally pays for framework analysis during the build because the result is ordinary generated code rather than runtime classpath scanning, reflective resolution, dynamic
proxies, or container assembly.

The crucial question is not whether compile-time work exists. It does.

The useful question is: **what is the invalidation unit of that work?**

If the invalidation unit is "the entire repository," then a growing repository eventually produces an increasingly expensive edit-compile cycle. If the invalidation unit is "the affected Gradle
project plus the downstream work whose inputs actually changed," then growth can be much more controlled.

That is exactly why the structure of the build matters.

A thousand classes in one compilation unit and a thousand classes divided into ten properly isolated modules may represent roughly the same amount of source code, but they do not represent the same
incremental-build problem. In the monolithic case, one compiler invocation sees everything. In the modular case, Gradle can reason about independent tasks, module outputs, dependency edges, ABI
changes, caches, and parallel execution.

The dependency graph inside the running application may still be large. The source graph that must be reconsidered after one edit does not have to be.

## `@KoraApp`: The Final Composition Root { #koraapp }

Kora's dependency container starts with `@KoraApp`. The annotated interface is the assembly point for the complete application graph.

A small application can reasonably keep most of its declarations in one Gradle module:

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

Components discovered in that compilation scope, module factories connected to the application, and generated components required by the graph are resolved into the final application container.

For a small or medium service, this can be exactly what you want. One module is easy to navigate, easy to build, and avoids build-structure overhead. Modularization is not automatically an improvement
merely because it is possible.

The scaling issue appears when the codebase becomes large enough that a single source set is no longer the natural unit of ownership or compilation. A service may accumulate multiple business domains,
integration layers, data-access areas, and feature groups. If all of those remain physically inside the same Gradle project, every framework processor operating in that compilation sees an
increasingly broad world.

The tempting but wrong conclusion is that compile-time DI therefore requires a permanent trade:

```text
fast runtime startup
        vs
slow local compilation
```

Kora's model does not require that trade to grow without bound. The application composition point can stay centralized while component discovery is distributed across compilation modules.

That is what `@KoraSubmodule` is for.

## `@KoraSubmodule`: Preserving DI Across Compilation Boundaries { #korasubmodule }

`@KoraSubmodule` marks a module boundary that participates in Kora's compile-time dependency-injection model.

Conceptually, a submodule says:

> This Gradle module owns a set of Kora components and module declarations. Compile and summarize them here, then make that set available to the final application graph.

For example, imagine a `catalog` Gradle project:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraSubmodule
    public interface CatalogModule {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraSubmodule
    interface CatalogModule
    ```

That project can contain its own `@Component` classes and `@Module` interfaces. During compilation, Kora generates a submodule implementation representing the declarations visible in that compilation
unit.

The final `application` project can then connect that boundary:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application
        extends CatalogModule,
        OrdersModule,
        BillingModule,
        NotificationsModule {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application :
        CatalogModule,
        OrdersModule,
        BillingModule,
        NotificationsModule
    ```

The important architectural detail is that the main application does not need all of those domain sources to become one giant compilation unit. Each domain module is compiled as its own Gradle project
and contributes a generated module surface to the final composition.

A more realistic dependency shape might be:

```text
                         ┌─────────────────┐
                         │   application   │
                         │    @KoraApp     │
                         └────────┬────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                   │
              ▼                   ▼                   ▼
      ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
      │    users     │    │    orders    │    │   billing    │
      │@KoraSubmodule│    │@KoraSubmodule│    │@KoraSubmodule│
      └──────┬───────┘    └──────┬───────┘    └──────┬───────┘
             │                   │                   │
             ▼                   ▼                   ▼
       components,         components,         components,
       repositories,       repositories,       repositories,
       controllers         integrations        clients
```

The runtime still receives one coherent dependency graph. The build does not need to treat the entire repository as one compiler invocation.

This is the central scaling property.

## Architectural Modularity Becomes Build Modularity { #architectural-modularity }

Large systems are usually modularized for architectural reasons long before build performance becomes the dominant concern.

The reasons are familiar:

- one domain should not casually reach into another domain's implementation;
- ownership should be visible;
- dependencies should have a direction;
- public APIs should be smaller than implementation details;
- infrastructure code should not leak everywhere;
- tests should be able to target a coherent subsystem;
- teams should be able to change one area without understanding the entire repository.

Compile-time DI adds another benefit: those same boundaries can constrain framework analysis.

Consider two designs.

### One Giant Module { #one-giant-module }

```text
src/main/java
├── users/...
├── orders/...
├── billing/...
├── catalog/...
├── notifications/...
└── infrastructure/...
```

Everything belongs to the same Gradle `compileJava` or KSP compilation. A change inside `catalog` belongs to the same compiler task that owns `orders`, `billing`, and everything else.

### Domain Modules { #domain-modules }

```text
:application
:users
:orders
:billing
:catalog
:notifications
:infrastructure
```

Now each project has its own compilation tasks and outputs. Gradle can reason about them separately.

This does not mean every edit rebuilds exactly one module. A change can propagate downstream when dependent inputs change. The point is that propagation is governed by actual build dependencies and
API changes rather than by the mere fact that all source files happen to share one compilation unit.

The ideal architecture therefore aligns three graphs:

```text
Business architecture
        ≈
Gradle project graph
        ≈
Kora submodule graph
```

They do not need to be perfectly identical, but when they broadly agree, the system gains a useful property: **the area of code that is conceptually affected by a change is closer to the area the
build system must reconsider.**

That is a much healthier scaling strategy than attempting to optimize a single ever-growing global compilation phase.

## What Happens After a Local Change? { #after-local-change }

Suppose a developer changes an internal implementation inside the `catalog` module.

A simplistic mental model says:

```text
change one class
    ↓
Kora uses compile-time DI
    ↓
entire application graph must be rebuilt
    ↓
entire repository recompiles
```

That is not how a modern multi-project Gradle build necessarily behaves.

A more realistic flow is:

```text
edit in :catalog
      ↓
:catalog compilation becomes dirty
      ↓
Kora processing for :catalog runs as needed
      ↓
generated :catalog submodule output is rebuilt
      ↓
Gradle evaluates dependent tasks
      ↓
only downstream tasks whose effective inputs changed need work
```

There are several layers of optimization here.

First, unrelated sibling modules are independent compilation units. If `billing` does not depend on `catalog`, a source edit in `catalog` does not inherently make `billing`'s compiler task dirty.

Second, Gradle supports incremental compilation and compile avoidance. An implementation-only change that does not alter the relevant ABI of a dependency may not require downstream Java compilation in
the same way as a public type or method signature change. The exact behavior depends on language, plugins, generated outputs, processor characteristics, and task inputs, so it should not be reduced to
a universal promise that "private changes never rebuild anything." But the general principle is important: a project dependency changing on disk is not equivalent to "recompile the whole repository
from zero."

Third, the build cache can reuse task outputs when Gradle finds an identical input fingerprint. This is especially valuable in CI, where a clean workspace does not necessarily imply that every task
must execute if a remote build cache already contains valid outputs.

Fourth, the Gradle daemon and configuration cache reduce repeated build overhead outside compilation itself.

Fifth, independent project tasks can execute in parallel when the task graph allows it.

The result is not magic. It is ordinary Gradle engineering applied to a framework whose compile-time work respects explicit module boundaries.

## The Kora Build Charts Need the Right Interpretation { #build-charts }

Kora's landing page separates build behavior into two categories: a clean artifact build and a cached or incremental artifact build. That distinction is more important than any single number on the
chart.

A clean build answers a useful but limited question:

> If nothing from the previous build can be reused, how much total work is required to produce the application artifact?

That matters in reproducibility testing, some CI environments, release pipelines, and cold build scenarios.

But it is not the dominant loop for a developer changing one service all day.

The normal loop is closer to:

```text
edit
 ↓
incremental compile
 ↓
test
 ↓
edit
 ↓
incremental compile
 ↓
test
```

Kora's cached-build scenario explicitly reflects the tools expected in that loop: Gradle build cache, configuration cache, daemon reuse, parallel execution, a multi-module build, and incremental
compilation.

That creates a better performance model:

```text
Clean build cost
= all required compilation and generation work

Incremental build cost
= invalidated work
+ affected generated work
+ required downstream work
+ packaging/test work
- reusable outputs
- up-to-date tasks
- cached tasks
- parallelizable independent work
```

The second formula is what matters for developer feedback at scale.

Compile-time frameworks are sometimes judged only by the first formula, while runtime frameworks are informally judged by the second. That comparison is misleading. If the question is developer
productivity, both should be measured under the same realistic edit-build-test workflow.

A framework that moves work into compilation can still have an excellent feedback loop when that work is incremental, partitioned, cacheable, and parallelizable.

## Gradle's Task Graph Is Part of the Architecture { #task-graph }

Once a service becomes multi-project, the Gradle task graph becomes a concrete representation of architectural dependency direction.

Imagine this project structure:

```text
:domain-model
:users
:catalog
:orders
:billing
:notifications
:infrastructure
:application
```

Dependencies might look like this:

```text
                 :domain-model
                 /     |      \
                /      |       \
               ▼       ▼        ▼
           :users   :catalog   :orders
                              /       \
                             ▼         ▼
                        :billing   :notifications
                              \       /
                               \     /
                                ▼   ▼
                             :application
                                  ▲
                                  │
                          :infrastructure
```

This topology tells Gradle something useful. `:users` and `:catalog` may be compiled independently. If they do not depend on one another, they may also compile concurrently. `:application` waits for
the module outputs it consumes, but it does not force all upstream modules to become a single task.

The build therefore has two kinds of parallelism.

The first is **task-level parallelism**: unrelated module compilation tasks can run simultaneously.

The second is **work avoidance**: tasks whose inputs have not changed may not run at all.

Work avoidance is usually more powerful than simply adding threads. The fastest compiler task is the one Gradle can prove does not need to execute.

This is why sensible project decomposition matters so much. A poorly structured module graph can accidentally serialize the build:

```text
:A → :B → :C → :D → :E → :application
```

Even if the modules are individually small, a deep dependency chain limits parallelism and increases the downstream impact of changes near the bottom.

A healthier structure often has wider independent areas and a thin composition layer:

```text
:users ─────────┐
:catalog ───────┤
:orders ────────┤
:billing ───────┼──> :application
:notifications ─┤
:infra-db ──────┤
:infra-http ────┘
```

The goal is not maximum fan-out for its own sake. The goal is a dependency graph that represents the actual architecture and avoids unnecessary transitive coupling.

## Dependency Direction Matters More Than Module Count { #dependency-direction }

Multi-module builds are not fast merely because they contain many modules.

A repository with fifty modules can compile worse than one with ten if every module depends on almost every other module. The performance benefit comes from **boundaries plus dependency discipline**.

Suppose `orders` depends directly on internal classes from `catalog`, `users`, `billing`, `notifications`, and `infrastructure`. A small public change in a foundational module can propagate widely.
The repository may be physically split but logically remain a monolith.

A better design exposes narrow contracts.

For example:

```text
:catalog-api
     ▲
     │
:catalog-impl
```

Consumers depend on `:catalog-api`, not on `:catalog-impl`.

Or, if splitting API and implementation into separate Gradle projects would be excessive, the same principle can be applied within one project using normal Java/Kotlin visibility and carefully chosen
exported types.

The central rule is:

> **A module boundary only limits build invalidation when the dependency surface across that boundary is reasonably stable.**

That is not a Kora-specific constraint. It is how compile avoidance works in any large JVM build. Kora simply makes the relationship especially relevant because framework graph discovery itself
happens at compilation time.

## Where the Root Composition Should Live { #root-composition }

A large Kora service benefits from a deliberately boring root `application` module.

Its job is not to contain business logic. Its job is composition.

A typical root can own:

- the `@KoraApp` interface;
- top-level module connections;
- process entrypoint;
- environment-wide configuration glue where necessary;
- application packaging;
- possibly system-level overrides.

Conceptually:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application
        extends UserModule,
        CatalogModule,
        OrderModule,
        BillingModule,
        NotificationModule,
        InfrastructureModule {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application :
        UserModule,
        CatalogModule,
        OrderModule,
        BillingModule,
        NotificationModule,
        InfrastructureModule
    ```

This gives the project a visible answer to the question: **what constitutes the deployed application?**

The domain modules own their own components. The application module decides which domains and infrastructure modules are assembled into the process.

That arrangement also keeps the composition layer relatively stable. Most daily edits happen below it.

The root graph still matters because Kora ultimately needs to validate the complete dependency graph. A missing dependency that crosses submodule boundaries must still fail somewhere. Compile-time
modularization should not be misunderstood as creating isolated runtime containers. The final application remains one graph.

The advantage is that the processor can consume compiled module declarations rather than requiring every source file to live in the same discovery scope.

This is an important distinction:

```text
one runtime graph
≠
one source compilation unit
```

Kora can have the former without requiring the latter.

## A Practical Large-Service Layout { #large-service-layout }

A genuinely large service should normally be split around coherent capabilities rather than framework layers.

A weak modularization looks like this:

```text
:controllers
:services
:repositories
:models
```

That structure often creates dense cross-module dependencies because one business feature spans every layer. Changing a feature may touch four projects. The build boundaries do not match ownership
boundaries.

A stronger design is usually domain-oriented:

```text
:application

:users
  ├── api
  ├── service
  └── persistence

:catalog
  ├── api
  ├── service
  └── persistence

:orders
  ├── api
  ├── service
  └── persistence

:billing
  ├── client
  ├── service
  └── persistence

:notifications
  ├── listener
  └── service

:infrastructure
  ├── database
  ├── telemetry
  └── shared integrations
```

Not every directory shown here needs another Gradle module. That would often be too granular. The important Gradle boundaries are `:users`, `:catalog`, `:orders`, and similar domain-level units.

Each domain can expose one Kora submodule:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraSubmodule
    public interface OrdersModule {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraSubmodule
    interface OrdersModule
    ```

It can also connect the external Kora modules it owns or requires, where that ownership is semantically appropriate. The final application then composes the domains.

The build topology becomes roughly:

```text
             ┌──────────────┐
             │  application │
             └───────┬──────┘
                     │
     ┌───────────────┼────────────────┐
     │               │                │
     ▼               ▼                ▼
  users           catalog           orders
                                      │
                              ┌───────┴────────┐
                              ▼                ▼
                           billing      notifications
```

This arrangement produces several useful effects at once:

1. domain ownership is visible;
2. accidental dependencies are harder to introduce;
3. tests can target a domain module directly;
4. Kora processing is partitioned;
5. Gradle can avoid unrelated work;
6. independent modules can compile in parallel;
7. CI cache hits become more granular.

The build improvement is not a trick added after architecture. It is a consequence of architecture.

## Implementation Changes Versus API Changes { #implementation-vs-api }

One of the most important details in any incremental build discussion is the difference between changing implementation and changing a module's externally visible contract.

Consider this class in `:catalog`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class PriceCalculator {
        public Money calculate(Product product) {
            return newAlgorithm(product);
        }

        private Money newAlgorithm(Product product) {
            // changed implementation
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class PriceCalculator {
        fun calculate(product: Product): Money {
            return newAlgorithm(product)
        }

        private fun newAlgorithm(product: Product): Money {
            // changed implementation
        }
    }
    ```

If the developer changes only the private algorithm, the module itself must obviously compile again. Its generated code may also need to be reconsidered depending on processor inputs.

But consumers of `:catalog` have not necessarily observed a source-level contract change. The public type and method shape may be identical.

Now compare that with:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public Money calculate(Product product, CustomerSegment segment)
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun calculate(product: Product, segment: CustomerSegment): Money
    ```

The public contract changed. Downstream code using that method may need recompilation or may fail compilation.

This distinction is what a modular build can exploit.

In practical terms, the performance goal is not:

> Never rebuild anything downstream.

That would be impossible and undesirable. If a contract changed, downstream validation is exactly what you want.

The real goal is:

> Do not make unrelated code pay for a change merely because everything shares the same compilation unit.

That is a much more defensible promise.

Compile-time safety and incremental compilation are not enemies. A well-designed build lets the compiler aggressively re-check code when contracts change while avoiding irrelevant work when they do
not.

## Generated Code Does Not Eliminate Incrementality { #generated-code }

Another common misconception is that source generation inherently defeats incremental builds.

It can, if a processor behaves like a global black box whose output depends on the entire source tree for every input. But source generation itself does not imply that model.

Kora's submodule mechanism is explicitly designed to establish discovery boundaries. A submodule compilation summarizes the components and modules owned by that Gradle project into generated source
that can be connected by the final application.

That means generated source participates in the module's output just like other compiled artifacts.

A useful mental model is:

```text
handwritten source
       +
Kora declarations
       ↓
module-local processing
       ↓
generated module source
       ↓
compiled module artifact
       ↓
consumed by downstream project
```

The generated source is not hidden runtime state. It is a build product.

This has a practical debugging benefit too. If a developer wants to know what a module contributes to the final application, the generated source provides something concrete to inspect. Build
performance and transparency reinforce one another: the framework creates an explicit artifact at the same boundary Gradle already understands.

## Build Cache: Reusing Compile-Time Framework Work { #build-cache }

Compile-time generation becomes even more attractive when task outputs can be cached.

A build cache changes the question from:

> Has this task run in this workspace before?

to:

> Have we already built this exact set of inputs somewhere?

If the answer is yes, Gradle can restore outputs instead of executing the task.

For a modular Kora service, this can be particularly effective in CI. Consider a pull request that changes only `:orders`.

Without a useful cache strategy:

```text
fresh CI worker
      ↓
recompile everything
      ↓
regenerate everything
      ↓
run tests
```

With a healthy remote build cache:

```text
fresh CI worker
      ↓
restore unchanged module outputs
      ↓
compile changed/affected modules
      ↓
compose/package
      ↓
run required tests
```

This is one reason a clean filesystem should not automatically be equated with a full cold computation. Modern CI builds can be ephemeral and still reuse work.

Of course, cache effectiveness depends on reproducible task inputs, stable toolchains, correct plugin behavior, and disciplined build configuration. A cache is not a substitute for modularity. But
modularity improves the granularity at which cached results can be reused.

A single enormous compile task gives the cache one enormous key. Change any relevant input and the whole task misses.

Ten coherent compile tasks give the build ten independent opportunities for hits.

## Configuration Cache and the Non-Compilation Part of Feedback { #configuration-cache }

Developers often attribute all build latency to compilation even when project configuration consumes a noticeable part of every invocation.

Gradle's configuration cache attacks a different layer of the problem. It can reuse the configured task graph rather than re-evaluating all build scripts on every invocation when the build is
compatible with it.

This matters more as repositories grow. A large multi-project build can otherwise spend meaningful time before compilation even begins.

The total feedback loop is roughly:

```text
developer feedback time
=
Gradle startup/configuration
+ task scheduling
+ source processing
+ compilation
+ tests
+ packaging or execution
```

Optimizing only the annotation processor while ignoring the rest of this equation gives an incomplete picture.

That is why Kora's own cached-build scenario is notable for including the whole modern Gradle toolchain rather than presenting processor speed in isolation.

Compile-time DI lives inside a build system. Its practical performance should be judged there.

## Parallel Compilation Helps, But Dependency Shape Decides How Much { #parallel-compilation }

Gradle can execute tasks from independent projects concurrently. A multi-module Kora application can therefore use available CPU cores more effectively than a single monolithic compilation task in
some workloads.

Suppose `users`, `catalog`, and `notifications` are independent:

```text
           ┌─ compile :users ──────────┐
edit/build ├─ compile :catalog ────────┼─> compile :application
           └─ compile :notifications ──┘
```

The three upstream tasks can potentially overlap.

But parallelism is bounded by dependency order. If every module depends on a common module that itself changes constantly, that common dependency becomes a synchronization point. If the graph is a
long chain, the build remains serial regardless of `--parallel`.

This leads to a broader engineering lesson:

> **Build parallelism is an architectural property before it is a Gradle flag.**

`--parallel` cannot create independence that the dependency graph does not contain.

A good module graph creates opportunities for parallel execution. Gradle then exploits them.

## Why a "Shared" Module Can Become a Build Hotspot { #shared-module-hotspot }

Many large repositories eventually create a module named something like:

```text
:common
:shared
:core
:utils
```

At first this looks efficient. Everyone can reuse the same helpers.

Over time, it often becomes one of the worst locations for build invalidation because nearly every domain depends on it.

The graph turns into:

```text
                :shared
              /   |   |   \
             ▼    ▼   ▼    ▼
          users orders billing catalog
             \    |    |    /
              \   |    |   /
               application
```

A change to `:shared` potentially affects nearly the entire repository.

Compile-time DI makes this cost visible, but it does not create the underlying architectural problem. A highly connected shared module is already a coupling hotspot.

The remedy is usually to make shared modules smaller and more stable:

```text
:domain-types
:money
:observability-api
:test-support
```

or to move helpers back into the domain that actually owns them.

The principle is simple: dependencies near the bottom of the project graph should change less frequently than dependencies near the leaves.

If everything depends on a module, treat its API as infrastructure.

## How Far Should You Modularize? { #how-far-modularize }

If modules can improve incremental compilation, why not create hundreds of them?

Because module boundaries have costs too.

Every Gradle project can add:

- configuration overhead;
- task graph size;
- dependency-management complexity;
- IDE synchronization work;
- more build files or convention-plugin logic;
- more published/internal artifacts;
- more places to reason about visibility;
- more cross-module test setup;
- more opportunities for accidental dependency cycles at the project level.

Extremely fine-grained modularization can also make ordinary development annoying. Moving a small class may require changing dependencies. Simple refactorings can cross artifact boundaries. Developers
spend more time navigating build structure than business code.

There is therefore a U-shaped curve:

```text
Build / maintenance cost
^
| \                         /
|  \                       /
|   \_____           _____/
|         \_________/
|
+---------------------------------> number of modules
   too few      useful        too many
```

With too few modules, compilation units become large, dependencies are unconstrained, and changes invalidate broad areas.

With too many modules, orchestration overhead and architectural ceremony dominate.

The target is not maximum modularity. It is **coherent modularity**.

A practical module usually deserves to exist when it has several of these properties:

- clear domain ownership;
- a reasonably stable boundary;
- meaningful independent tests;
- enough implementation to amortize build-project overhead;
- a dependency direction that makes architectural sense;
- a lifecycle of change different from neighboring code;
- value as an independently reusable internal capability.

If a module would contain three classes that always change together with another module, it is probably not a useful boundary.

If a module contains a complete domain area owned by a team and depended on through a small set of contracts, it probably is.

## A Sensible Migration Path for a Growing Kora Service { #migration-path }

A service does not need to begin life with an elaborate multi-project build.

That would optimize for a scale the codebase does not yet have.

A more natural progression is:

```text
Stage 1
single Gradle module
single @KoraApp

        ↓ growth

Stage 2
extract clear infrastructure or domain boundaries

        ↓ growth

Stage 3
domain Gradle modules with @KoraSubmodule

        ↓ growth

Stage 4
stabilize dependency direction
introduce build cache
enable configuration cache
parallelize independent tasks
measure critical-path modules
```

The key is to modularize when the architecture already suggests a boundary.

Kora makes that extraction compatible with its DI model. A domain does not lose compile-time injection merely because it moved into another Gradle project. `@KoraSubmodule` provides a bridge between
the module-local compilation and the final application graph.

That means architectural decomposition does not require retreating to runtime scanning or a service-locator pattern.

The application remains statically composed.

## Clean Build Performance Still Matters { #clean-build }

Incremental compilation should not become an excuse to ignore clean builds.

CI pipelines occasionally invalidate caches. Toolchains change. Dependency versions change. Release builds may intentionally run without reuse. Developers clone the repository for the first time. A
healthy project should not require an hour-long bootstrap just because subsequent builds are fast.

Kora's build story therefore has two responsibilities:

```text
Clean build
    → total framework/compiler efficiency

Incremental build
    → locality, invalidation, cacheability, parallelism
```

The first is partly a framework implementation problem.

The second is a framework-plus-architecture-plus-build-system problem.

This distinction prevents two opposite mistakes.

The first mistake is saying, "Incremental builds exist, so processor cost does not matter." It does matter.

The second mistake is saying, "Annotation processing adds work to a clean build, therefore every edit in a large service must be slow." That does not follow.

A good large-project design addresses both.

## The Runtime Payoff Is Still the Point { #runtime-payoff }

Why accept compile-time work at all?

Because Kora uses it to remove work from a much more operationally sensitive phase: application startup and request handling.

At compile time, Kora can resolve and validate the dependency graph, generate wiring, generate integration code, and turn framework behavior into ordinary compiled Java/Kotlin.

At runtime, the service does not need to rediscover that architecture by scanning the classpath and building a container from metadata.

The trade can be represented as:

```text
Traditional runtime work
------------------------
discover
reflect
resolve
proxy
wire
start

Kora
----
compile:
  discover
  validate
  generate
  wire

runtime:
  instantiate
  initialize
  serve
```

Compile-time cost is paid per build.

Runtime cost is paid per application instance, per deployment, per restart, per test process, and often across a fleet containing many copies of the service.

That does not mean compile time is free or unimportant. Developer time is expensive too. It means the correct engineering objective is not "move as much work to compilation as possible regardless of
build latency." The objective is to make compile-time work **bounded and incremental enough** that the runtime advantages do not damage the developer loop.

`@KoraSubmodule` is important because it supports exactly that balance.

## Compile-Time Boundaries Can Be Architectural Boundaries { #compile-time-boundaries }

There is a deeper idea here than build optimization.

Runtime DI containers can make application composition globally convenient. Put classes on a classpath, add annotations, let scanning discover them, and allow the runtime container to assemble the
result.

That convenience can blur boundaries. If every class is globally discoverable, the framework provides little pressure to decide which compilation unit actually owns a component.

Kora's model is more explicit. The processor analyzes the module containing `@KoraApp` and modules explicitly marked as Kora submodules. Ordinary project modules do not automatically become discovery
scopes.

That makes module participation intentional.

The architecture can say:

```text
This domain owns these components.
This Gradle project compiles them.
This Kora submodule exposes them.
The root application composes them.
```

The same boundary therefore has multiple meanings:

```text
Domain boundary
     =
source ownership boundary
     =
Gradle compilation boundary
     =
Kora component-discovery boundary
```

When those boundaries align, developers get a system that is easier to reason about both statically and operationally.

The build does not merely become faster. The architecture becomes more legible.

## What to Measure in a Real Repository { #what-to-measure }

Teams evaluating compile-time DI should avoid measuring only one number.

A useful benchmark suite for a large Kora repository should include at least several scenarios.

### 1. Cold clean build { #cold-clean-build }

```bash
./gradlew clean build --no-build-cache
```

This shows the total cost when nothing can be reused.

### 2. Warm no-change build { #warm-no-change-build }

Run the same build twice and measure how much Gradle avoids when no inputs changed.

This catches configuration or task-model problems.

### 3. Leaf implementation edit { #leaf-implementation-edit }

Change a private implementation detail in a low-level domain module and rebuild.

This approximates a common local development iteration.

### 4. Leaf public API edit { #leaf-public-api-edit }

Change a public signature and measure how far recompilation propagates.

This reveals the real dependency fan-out of the architecture.

### 5. Shared foundational edit { #shared-foundational-edit }

Change a heavily depended-on module.

This gives the worst realistic incremental case and often exposes architecture hotspots.

### 6. Remote-cache CI build { #remote-cache-ci-build }

Build a change on a fresh worker with a populated remote cache.

This measures what contributors actually experience in an optimized pipeline.

### 7. Parallel versus non-parallel build { #parallel-vs-nonparallel }

Compare the critical path and CPU utilization. If `--parallel` barely helps, inspect the project dependency graph rather than assuming Gradle is at fault.

The resulting table is much more informative than "framework A compiles in X seconds."

For example:

```text
Scenario                     What it tells you
---------------------------------------------------------------
Clean build                  Total compile/generation efficiency
No-change build              Up-to-date/configuration efficiency
Leaf implementation edit     Locality of invalidation
Public API edit              Downstream dependency fan-out
Shared-module edit           Architectural worst case
Remote-cache CI              Cache granularity/reproducibility
Parallel build               Available task-level concurrency
```

The most important number for developer experience is often the leaf implementation edit, not the clean build.

## When Build Performance Starts Degrading { #when-build-degrades }

If a large Kora service becomes slow to compile, the response should not immediately be "compile-time DI does not scale."

First identify which layer is actually expensive.

A useful diagnostic sequence is:

```text
Slow build
   ↓
Is Gradle configuration slow?
   ├─ yes → configuration cache / build logic
   ↓ no
Are many unrelated compile tasks running?
   ├─ yes → inspect invalidation and module dependencies
   ↓ no
Is one module's compile/KSP task dominant?
   ├─ yes → module may be too large or processor-heavy
   ↓ no
Is the critical path serialized?
   ├─ yes → inspect project dependency chain
   ↓ no
Are cache hit rates poor?
   ├─ yes → inspect task inputs and reproducibility
   ↓ no
Are tests dominating?
   └─ yes → compilation is not the primary problem
```

This matters because "build time" is an aggregate metric. A team can waste weeks tuning an annotation processor while 60 percent of the wall clock is actually integration tests or build-script
configuration.

The profiler should decide where optimization effort goes.

## When a Kora Module Is Too Large { #module-too-large }

A Gradle module is probably becoming too large when several symptoms appear together:

- compile or KSP tasks dominate incremental builds;
- unrelated teams frequently modify the same project;
- the project contains multiple business domains;
- changes repeatedly invalidate generated code for distant functionality;
- the module's dependency list is large and heterogeneous;
- tests require broad fixtures because the module has no coherent responsibility;
- developers cannot describe the module without saying "most of the application."

At that point, splitting can improve architecture and build locality simultaneously.

The right split is usually not arbitrary package slicing. Look for independently changing domains.

For example:

```text
:commerce
```

might naturally become:

```text
:catalog
:pricing
:orders
:checkout
```

if those areas already have distinct concepts and ownership.

Each can then expose a Kora submodule boundary and be composed by the application.

## When a Repository Has Too Many Modules { #too-many-modules }

The opposite failure mode is also visible.

You probably have too many modules when:

- developers routinely change five or ten build files for one feature;
- most modules contain only a handful of classes;
- project dependencies form a maze more complicated than the business architecture;
- Gradle configuration and project synchronization become significant;
- circular architectural relationships are "solved" by creating more tiny interface modules;
- tests require elaborate cross-project fixture wiring;
- developers no longer know where new code belongs.

A build system should support the architecture, not become the architecture.

If two modules always change together, are owned together, are deployed together, and have no meaningful independent contract, merging them can be an optimization.

The objective is a stable middle ground where modules are large enough to be coherent and small enough to bound change.

## Kora's Scaling Strategy Is Deliberately Ordinary { #scaling-strategy }

Perhaps the most interesting aspect of this design is that Kora does not need a proprietary distributed compiler or a special incremental DI daemon to make the model work.

It uses concepts JVM teams already understand:

- Gradle multi-project builds;
- compiler modules;
- annotation processing or KSP;
- generated source;
- stable project dependencies;
- incremental compilation;
- build caching;
- configuration caching;
- parallel task execution.

`@KoraSubmodule` fits the DI graph into those existing mechanics.

That is consistent with Kora's broader design philosophy. Rather than hiding application structure behind a runtime container, it tries to turn framework behavior into explicit source and normal build
artifacts.

The scaling strategy is therefore not:

> Make one giant processor invocation infinitely fast.

It is:

> Keep processor work efficient, but also stop asking one invocation to own an infinitely growing source universe.

That is a more sustainable answer.

## The Most Important Mental Model { #mental-model }

For small applications, this is sufficient:

```text
source
  ↓
@KoraApp
  ↓
compile
  ↓
generated application graph
  ↓
run
```

For large applications, use this model instead:

```text
users source ───────────────> users compilation ───────┐
                                                       │
catalog source ─────────────> catalog compilation ─────┤
                                                       │
orders source ──────────────> orders compilation ──────┼─> application composition
                                                       │        @KoraApp
billing source ─────────────> billing compilation ─────┤
                                                       │
notifications source ───────> notifications compilation┘
```

Each domain has its own compile-time scope.

Each domain can expose its declarations through `@KoraSubmodule`.

Gradle determines what is dirty, what is reusable, and what can run concurrently.

The final Kora application validates and composes the complete graph.

This is the key to understanding the phrase **compile-time DI at scale**. The compile-time nature of the framework does not require the compile-time unit to be the entire codebase.

## Conclusion { #conclusion }

Compile-time dependency injection creates a straightforward concern: as the application grows, the framework has more declarations and a larger dependency graph to process. If the entire codebase
remains one monolithic compilation unit, build latency can grow along with it.

The solution is not to pretend that compilation is free.

The solution is to stop treating "large application" and "single compilation unit" as synonyms.

Kora provides `@KoraSubmodule` specifically for multi-project applications. Domain modules can own their components and module declarations, compile them independently, and expose them to a separate
root application where `@KoraApp` performs final composition. That allows the DI architecture to follow normal Gradle compilation boundaries instead of collapsing the repository back into one
source-processing scope.

Once that structure exists, the rest of the modern Gradle toolchain becomes relevant: incremental compilation reduces unnecessary downstream work, compile avoidance distinguishes implementation
changes from API changes where possible, the build cache reuses module outputs, the configuration cache reduces repeated configuration cost, and independent modules can compile in parallel.

None of these mechanisms guarantees that every edit is local. A public contract change should propagate. A frequently modified shared module can invalidate many consumers. A badly designed module
graph can serialize the build. Too many tiny modules can create overhead of their own.

That is exactly the point.

Build scalability becomes an architecture problem with understandable rules rather than an unavoidable tax of compile-time DI.

A large Kora service should therefore be designed so that business boundaries, Gradle boundaries, and DI discovery boundaries reinforce one another. The root application remains the place where the
complete graph is assembled, while individual domains become independently compiled contributors to that graph.

The resulting principle is simple:

> **A large application does not have to remain one enormous compilation unit. The same modularization that improves architecture also bounds compile-time framework work.**

And the stronger conclusion follows from it:

> **Compile-time DI does not mean compiling the entire application from scratch after every edit. In a properly modularized codebase, compile-time boundaries and architectural boundaries can be the
same thing.**
