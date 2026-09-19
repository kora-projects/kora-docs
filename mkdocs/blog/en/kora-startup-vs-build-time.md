---
title: Startup vs Build Time — Why the Kora Framework Moves Work Left
date: 2026-08-29
description: Why the Kora Framework shifts framework work from every startup into the build, and what that trade means for deployments, tests, and autoscaling.
search:
  exclude: true
---

# Startup vs Build Time: Why Kora Moves Work Left { #startup-vs-build }

**August 29, 2026**

Framework performance is usually discussed at runtime. How quickly does the application start? How many requests per second can it process? How much memory does it consume? How much latency does the
framework add to a request?

Those are important questions, but they hide a more fundamental architectural choice: **when should framework work happen?**

A framework can postpone a large amount of work until the application starts. It can scan classes, inspect annotations, discover components, resolve dependency relationships, build metadata, construct
proxy structures, discover routes, interpret mappings, and assemble a runtime model after the JVM is already running.

Or it can perform much of that work earlier, during compilation.

The Kora Framework deliberately chooses the second model.

Its central trade-off can be summarized in one line:

```text
runtime work → compile-time work
```

The application graph is analyzed and generated during compilation. Dependency relationships are validated before the service starts. HTTP handlers, repositories, mappers, AOP wrappers, configuration
implementations, and other infrastructure can be generated as ordinary Java or Kotlin source. At runtime, Kora starts from structures that were already discovered and checked by the compiler toolchain
instead of rebuilding the same architectural knowledge from scratch.

That design has an obvious cost: compilation has more work to do.

Annotation processors and KSP processors must run. Generated source must be created and compiled. Changes that affect the application graph may invalidate processor outputs. A completely clean build
can therefore spend more time in the compiler than a framework whose architecture is assembled dynamically at startup.

Kora does not hide this trade-off. Its own performance positioning distinguishes startup and readiness from clean builds and cached builds, and explicitly describes compile-time graph generation as a
cost paid during the build in exchange for avoiding scanning, reflection, and runtime wiring while the service boots.

The interesting question is therefore not:

> Is compile-time generation free?

It is not.

The useful question is:

> **Where should the cost live, and how many times will we pay it?**

That is where the economics change.

A build usually happens once for an artifact.

That artifact may then start many times.

It may start in integration tests, black-box tests, staging, canaries, production deployments, horizontal autoscaling, Pod restarts, node replacements, spot recovery, disaster recovery, and developer
environments.

If a little extra build work removes repeated startup work, the trade can become favorable very quickly.

The Kora model is therefore not primarily about making compilation slower in order to make a benchmark faster. It is about moving deterministic framework work into the phase where it can be checked
once, materialized as source code, cached where possible, and reused by every runtime instance created from the resulting artifact.

That is what “moving work left” actually means.

---

## The Runtime-Heavy Model { #the-runtime-heavy }

To understand the trade-off, consider what a framework needs to know before it can execute an ordinary request.

It must know things such as:

- which components exist;
- which component depends on which interface;
- which implementation should satisfy that dependency;
- which HTTP route maps to which method;
- which mapper converts a request body;
- which mapper serializes the response;
- which repository implementation executes a query;
- which aspects wrap a method;
- which configuration object should be created;
- which telemetry and resilience components apply;
- in what order lifecycle components should start.

There are two broad ways to obtain that information.

The first is to discover it at runtime.

A simplified runtime-heavy startup path looks like this:

```text
JVM starts
    ↓
framework bootstrap begins
    ↓
classpath / metadata discovery
    ↓
annotation inspection
    ↓
component discovery
    ↓
dependency resolution
    ↓
proxy / metadata creation
    ↓
route and mapper assembly
    ↓
application initialization
    ↓
ready
```

The exact mechanics differ between frameworks. Some use reflection heavily, some use generated indexes, some use bytecode enhancement, some cache metadata, and modern frameworks often move selected
operations to build time.

The architectural point remains: any information that is not finalized before deployment has to be reconstructed, interpreted, or validated later.

That work sits on the startup critical path.

It is paid every time a new process starts.

---

## Kora's Model: Calculate the Structure Before Runtime { #kora-s-model }

Kora moves much of that structural work into the compiler pipeline.

A simplified flow becomes:

```text
source code
    ↓
Java annotation processing / Kotlin KSP
    ↓
inspect Kora declarations
    ↓
resolve graph and contracts
    ↓
generate source
    ↓
compile generated source
    ↓
package artifact
```

Runtime then becomes closer to:

```text
JVM starts
    ↓
load prebuilt application graph code
    ↓
construct and initialize components
    ↓
ready
```

The application still has real initialization work.

A database pool may have to start.

A Kafka consumer may have to initialize.

An HTTP server must bind a socket.

Telemetry exporters may create resources.

User-defined components may perform expensive initialization.

Moving work to compilation does not eliminate application startup.

What it removes is a class of **framework discovery and structural assembly** that can be known ahead of time.

This distinction matters.

Kora is not claiming that compilation can pre-open tomorrow's PostgreSQL connections.

It is saying that compilation can already know which component will create the PostgreSQL client, which configuration it needs, which repository depends on it, which controller depends on the
repository, and how those objects connect.

That architecture does not need to be rediscovered every time the process starts.

---

## Build Time and Startup Time Are Not Symmetric { #build-time-and }

At first glance, moving one second from startup into compilation can look like a zero-sum trade:

```text
+1 second build
-1 second startup
= no difference
```

That reasoning works only if every build corresponds to exactly one process start.

Modern backend systems rarely behave that way.

A single artifact may be started repeatedly:

```text
1 build
    ↓
5 integration environments
    ↓
10 CI test starts
    ↓
3 staging starts
    ↓
20 production replicas
    ↓
rolling deployment replacements
    ↓
autoscaling events
    ↓
restarts and rescheduling
```

The arithmetic is therefore closer to:

```text
extra compile cost × builds
vs
startup savings × starts
```

If:

```text
Δbuild = +2 seconds
Δstartup = -1 second
```

and the artifact starts once:

```text
net = +1 second
```

The compile-time approach loses.

If the same artifact starts 20 times:

```text
build penalty = 2 seconds
startup saving = 20 seconds
net saving = 18 seconds
```

If it starts 200 times:

```text
net saving = 198 seconds
```

This is the fundamental asymmetry.

Build cost is usually paid at artifact-production frequency.

Startup cost is paid at instance-creation frequency.

Cloud-native systems create instances frequently.

---

## The General Equation { #the-general-equation }

The trade can be described with a simple model.

Let:

```text
B = additional build cost caused by compile-time processing
S = startup time saved per process
N = number of process starts from the built artifact
```

Then the net time effect is approximately:

```text
net benefit = (S × N) - B
```

Compile-time work wins when:

```text
S × N > B
```

or:

```text
N > B / S
```

Suppose annotation processing adds:

```text
B = 3 seconds
```

while startup improves by:

```text
S = 0.75 seconds
```

The break-even point is:

```text
N > 3 / 0.75
N > 4
```

After roughly four starts, the runtime savings have repaid the build-time cost.

This model is intentionally simplistic. Build caches, incremental compilation, parallel startup, CI topology, developer workflows, image creation, and runtime warm-up all complicate real systems.

But the equation exposes the right multiplier.

The important variable is not just build time or startup time.

It is **how often each cost repeats**.

---

## Annotation Processing Is the Mechanism, Not the Goal { #annotation-processing-is }

For Java applications, Kora uses annotation processing.

The annotation processor sees program structure during compilation and generates additional Java source based on declarations in the application.

For Kotlin, Kora uses KSP, the Kotlin Symbol Processing API, to perform the equivalent role in the Kotlin toolchain.

These mechanisms are sometimes discussed as if annotation processing itself were the architectural objective.

It is not.

The objective is to obtain a reliable model of application structure before runtime.

Annotation processing and KSP are the tools that let Kora do that while staying inside normal Java and Kotlin build systems.

Instead of writing:

```text
framework runtime:
"Let me inspect the whole application and determine what it means."
```

Kora effectively asks:

```text
compiler phase:
"Tell me what the application means now,
while types and declarations are already available."
```

That timing provides two benefits at once.

First, source can be generated.

Second, invalid architecture can fail the build.

---

## Compile-Time Dependency Injection Is More Than Code Generation { #compile-time-dependency }

Dependency injection is the clearest example.

Suppose the application contains:

```text
Controller
    ↓
Service
    ↓
Repository
    ↓
Database
```

A runtime container can discover this graph after startup.

It can find the controller, inspect constructors, search for a compatible service, then recursively resolve the repository and database dependency.

Kora resolves that architecture during compilation.

That means the compiler phase can detect:

- missing dependencies;
- ambiguous dependencies;
- invalid graph relationships;
- cycles;
- tag mismatches;
- invalid aspect combinations;
- other structural errors.

The generated graph then contains explicit code describing how those components are constructed and connected.

Runtime no longer needs to solve the dependency problem.

It executes the solution that compilation already produced.

This is important because dependency resolution is deterministic for a given source tree and configuration of modules.

Repeating it on every process start provides little value if the result cannot legitimately change between starts.

Kora treats that as build-time knowledge.

---

## Generated Source Is the Materialized Result of Analysis { #generated-source-is }

The output of Kora's compile-time model is not only hidden metadata.

It is source code.

That distinction matters.

Generated source turns framework decisions into something the normal language toolchain can compile, optimize, inspect, debug, and reason about.

Examples of generated infrastructure can include:

```text
application graph implementations
HTTP route modules
JSON readers/writers
repository implementations
AOP wrappers
configuration implementations
mappers
client infrastructure
```

The specific generated artifacts depend on which modules the application uses.

Conceptually, the compiler pipeline is doing this:

```text
declarative application source
    ↓
framework analysis
    ↓
explicit generated implementation
    ↓
normal JVM bytecode
```

Runtime then executes ordinary compiled code rather than interpreting a large amount of framework metadata.

This is why generated source is central to the startup/build trade.

The build does more because it is **materializing future runtime decisions**.

---

## Generated Code Is a Form of Precomputation { #generated-code-is }

Another useful way to think about Kora is as precomputation.

Suppose a runtime framework must answer:

```text
Which object provides FooService?
Which constructor parameters does it need?
What mapper handles UserRequest?
What handler invokes GET /users/{id}?
Which aspects wrap method X?
```

If those answers are stable for a built artifact, they can be computed once.

This resembles many classic performance techniques:

```text
compute once
store result
reuse many times
```

A database creates an index because searching from scratch on every query is expensive.

A compiler performs constant folding because repeating the expression at runtime is unnecessary.

A build system caches outputs because unchanged work should not be repeated.

Kora applies the same philosophy to framework structure.

Generated source is effectively a compiled cache of architectural decisions.

The difference is that the cache is type-checked code.

---

## Runtime Reflection Is Flexible but Has a Cost Model { #runtime-reflection-is }

Reflection and dynamic discovery are powerful because they postpone decisions.

The runtime can inspect classes after deployment.

Libraries can register behavior dynamically.

Frameworks can interpret annotations without requiring a generation step.

That flexibility is valuable in systems that genuinely need runtime extensibility.

But most business services have relatively static architecture.

A controller does not usually change dependencies after the JAR is built.

A repository does not suddenly acquire a new constructor at runtime.

A method annotated with a resilience policy normally keeps that policy until a new artifact is deployed.

In that environment, runtime discovery repeatedly answers questions whose answers were already knowable at build time.

Kora chooses to sacrifice some of that dynamic flexibility in favor of:

```text
earlier validation
+
explicit generated code
+
less startup work
+
less runtime machinery
```

This is an architectural trade, not a universal law.

A plugin platform that loads arbitrary modules from unknown JARs at runtime may prefer dynamic discovery.

A statically packaged cloud service usually has much less need for it.

---

## Build Time Is Not One Number { #build-time-is }

When discussing the cost of annotation processing, people often say:

> "But Kora makes the build slower."

That statement is too vague to be useful.

There are several different build paths:

```text
clean build
incremental build
cached build
configuration-cached build
CI build
local IDE build
multi-module partial rebuild
```

Their economics differ substantially.

A clean build starts with no compiled outputs.

An incremental build starts with most outputs already available and recompiles only what changed and what must be invalidated.

A cached build may reuse task outputs produced previously.

A developer build may benefit from a warm Gradle daemon.

A CI build may use remote caches.

A release build may intentionally disable caches for reproducibility measurements.

Treating all of them as one "build time" hides the path developers actually experience most often.

---

## Clean Build: The Worst-Case Compiler Path { #clean-build-the }

A clean build is the easiest scenario to reason about.

Everything must be recreated:

```text
source compilation
annotation processing / KSP
generated source
generated source compilation
resource processing
packaging
```

This is where compile-time frameworks expose their largest visible build-time cost.

If the framework generates substantial infrastructure, a clean build has to generate it all again.

That is real work.

For benchmarking framework build cost, a clean build is useful because it gives a controlled upper-bound-like comparison and avoids accidentally measuring cache reuse instead of compiler work.

Kora's own landing separates clean artifact build measurements from cached/incremental measurements for exactly this reason.

But a clean build is not necessarily the dominant developer workflow.

Developers do not usually run:

```bash
./gradlew clean build
```

after every changed method.

Nor should they.

---

## Why `clean` Is Often an Artificial Development Benchmark { #why-clean-is }

Running `clean` deliberately destroys information the build system could have reused.

It removes generated sources, compiled classes, and task outputs.

That is useful when:

- testing build reproducibility;
- diagnosing stale-output problems;
- measuring full-build cost;
- creating controlled benchmark conditions.

It is a poor model for normal edit-compile-test development.

The ordinary loop is closer to:

```text
edit one or several files
    ↓
compile changed inputs
    ↓
rerun affected processors/tasks
    ↓
reuse unchanged outputs
    ↓
test
```

The distinction matters especially for compile-time frameworks.

If a generated artifact depends only on a small portion of the source graph, an incremental processor can avoid rebuilding unrelated outputs.

The question therefore becomes not just:

```text
How expensive is annotation processing?
```

but:

```text
How much annotation processing is invalidated by a normal change?
```

That is a much better developer-experience metric.

---

## Incremental Compilation Is What Makes the Trade Practical { #incremental-compilation-is }

Compile-time generation would be much less attractive if every tiny source edit forced regeneration of the whole application.

Modern build tooling is designed to avoid that.

Gradle incremental compilation tracks source relationships and recompiles affected classes instead of automatically rebuilding everything.

Annotation processors can also be designed with incremental processing in mind.

Kora has added incremental processing support for its Java annotation processing and Kotlin KSP processing so that compile-time generation can participate more effectively in this model.

The ideal edit path therefore looks like:

```text
change local code
    ↓
invalidate a limited set of symbols
    ↓
rerun required processors
    ↓
regenerate affected output
    ↓
compile
```

rather than:

```text
change one line
    ↓
regenerate the world
```

Not every source change is local.

Changing the application graph can have wider consequences.

Changing a shared module contract can invalidate many consumers.

Changing generated API models may trigger broad recompilation.

But that is conceptually appropriate: a structural change should cost more than a local method-body change because more of the program actually changed.

---

## Incremental Compilation Rewards Stable Architecture { #incremental-compilation-rewards }

There is an interesting secondary effect.

Compile-time frameworks make architectural boundaries visible to the build system.

Consider two changes.

### Change A { #change-a }

A developer modifies internal business logic:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public Money calculatePrice(Order order) {
        // changed algorithm
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun calculatePrice(order: Order): Money {
        // changed algorithm
    }
    ```

The dependency graph has not changed.

The repository contract has not changed.

The HTTP API has not changed.

A well-behaved incremental toolchain should be able to keep most generated infrastructure untouched.

### Change B { #change-b }

A developer changes:

```text
constructor dependencies
module wiring
component type
HTTP route signature
repository method
OpenAPI contract
```

Now framework-generated outputs legitimately need to change.

The build becomes more expensive because the architecture changed.

This is not necessarily a drawback.

It means compile cost correlates with the scope of the change.

A structural edit causes structural work.

A local edit should remain comparatively local.

---

## KSP Makes the Same Trade for Kotlin { #ksp-makes-the }

Kotlin cannot simply reuse Java annotation processing as its ideal symbol-processing model.

Kora therefore uses KSP for Kotlin projects.

Conceptually the architecture remains the same:

```text
Kotlin source
    ↓
KSP sees symbols
    ↓
Kora analyzes declarations
    ↓
Kora generates Kotlin/Java infrastructure as appropriate
    ↓
compiler compiles the result
```

KSP was designed specifically to expose Kotlin program structure efficiently to code generators.

For a framework like Kora, this is important because Java and Kotlin are both first-class application languages while the framework philosophy remains the same:

```text
analyze early
generate explicitly
execute directly
```

The tool differs.

The architectural principle does not.

---

## Generated Source Has a Build Cost and a Debugging Dividend { #generated-source-has }

Generated source takes time to create and compile.

That is the obvious cost.

The less obvious benefit is that it remains inspectable after generation.

Suppose a developer wants to know how a request reaches a controller.

In a runtime-heavy system, the explanation may involve:

- scanning rules;
- reflection;
- dynamic proxies;
- framework metadata;
- runtime interceptors;
- container internals.

In Kora, much of the answer can be traced through generated code.

The compiler has already transformed declarative framework usage into explicit implementation.

That makes the additional build work productive in two dimensions:

```text
runtime optimization
+
diagnostic artifact
```

A generated class is not merely an optimization cache.

It is documentation of what the framework decided.

---

## Build-Time Errors Are Also Runtime Work Removed { #build-time-errors }

Moving work left does more than move CPU cycles.

It moves failure detection.

Suppose a dependency is missing.

A runtime-oriented sequence might be:

```text
edit code
    ↓
compile successfully
    ↓
package
    ↓
start application
    ↓
framework builds container
    ↓
dependency resolution fails
```

Kora aims for:

```text
edit code
    ↓
compile
    ↓
dependency resolution fails
```

The second pipeline is shorter.

This means some of the extra compiler work replaces not only startup work but also failed runtime attempts.

The cost model should therefore include:

```text
time saved by avoiding invalid starts
```

This is especially important in CI.

A failure discovered during compilation can stop a pipeline before:

- container packaging;
- image upload;
- test environment creation;
- application boot;
- integration tests;
- deployment.

The earlier the failure, the smaller its computational radius.

---

## The Build Is a Better Place for Deterministic Failure { #the-build-is }

There is a broader engineering principle here:

> If a property can be proven before deployment, runtime is usually the wrong place to discover that it is invalid.

Examples include:

```text
missing dependency
ambiguous provider
invalid generated mapping
bad repository signature
unsupported aspect combination
broken route contract
```

These are properties of the program.

They do not become more meaningful after a Kubernetes Pod starts.

Checking them during compilation increases build work, but it reduces uncertainty later.

That is why "startup versus build time" is not purely a performance trade.

It is also:

```text
runtime uncertainty
→ compile-time certainty
```

Kora spends compiler effort to reduce operational ambiguity.

---

## Cached Builds Change the Economics Again { #cached-builds-change }

Build caches add another asymmetry.

Generated outputs are deterministic functions of inputs.

When a build system can safely determine that the inputs have not changed, it can reuse previous task outputs rather than recomputing them.

That means some compile-time cost can disappear entirely on later builds.

The exact behavior depends on task configuration, Gradle versions, processor implementation, project structure, cache locality, and whether remote caching is configured.

But conceptually:

```text
first build:
pay generation

later compatible build:
reuse generation output
```

Startup cannot use the same kind of organizational cache as easily.

Every new JVM still needs to become a running process.

Every new Pod still has to initialize its application components.

Every test container still has to reach readiness.

Build work has more opportunities for reuse because it produces static artifacts.

Runtime startup creates ephemeral state.

This is another reason build-time work can be economically attractive.

---

## Configuration Cache Is Different From Build Cache { #configuration-cache-is }

It is useful to separate two often-confused Gradle concepts.

The **build cache** reuses task outputs.

The **configuration cache** reuses Gradle's configured task graph and project configuration state.

They optimize different phases.

A compile-time framework benefits primarily when its processing tasks and compilation outputs can participate efficiently in incremental execution and build caching.

But configuration cache still matters to developer feedback because Gradle itself has less setup work to repeat before tasks begin.

A realistic fast local workflow therefore combines several layers:

```text
warm Gradle daemon
+
configuration cache
+
incremental compilation
+
incremental annotation/KSP processing
+
build cache
```

The result can be very different from:

```text
clean
no daemon
no cache
no parallelism
```

Both measurements are valid.

They answer different questions.

---

## Clean Build Answers "What Does the Compiler Cost From Zero?" { #clean-build-answers }

A controlled clean-build benchmark answers:

> If nothing is reusable, how much work does this framework add to producing an artifact?

That is important for:

- fresh CI runners;
- release pipelines;
- repository bootstrap;
- cache misses;
- reproducibility analysis.

A compile-time framework may legitimately perform worse here than a runtime-heavy framework.

There is no reason to hide that result.

The build is doing more.

The relevant question is whether the extra work is proportional and whether the resulting artifact repays that work later.

---

## Cached Build Answers "What Does Development Feel Like?" { #cached-build-answers }

A cached or incremental build answers a different question:

> After the project already exists and a developer changes normal code, how expensive is the next useful iteration?

For engineering productivity, this can matter more than clean build time.

Developers may do hundreds of incremental iterations for every full clean build.

The ideal framework/build combination is therefore not merely:

```text
fast clean build
```

but:

```text
reasonable clean build
+
very fast incremental loop
```

Kora's compile-time architecture depends on this distinction.

Moving work left is much more attractive when build tooling can avoid repeating unchanged work.

---

## Local Development Is a Frequency Problem Too { #local-development-is }

Consider a developer working for one day.

They may perform:

```text
1 clean build
60 incremental compiles
30 test runs
20 application starts
```

The total feedback cost is:

```text
clean build cost
+
incremental compile cost × 60
+
test cost × 30
+
startup cost × 20
```

A framework comparison that measures only the first term may predict the wrong developer experience.

Likewise, measuring only startup can hide expensive compile-time behavior.

The correct object is the whole iteration loop:

```text
edit
→ compile
→ process annotations/symbols
→ generate
→ test/start
→ observe result
```

This is the unit developers actually experience.

---

## Build Time Can Be Paid Once While Startup Is Paid Per Replica { #build-time-can }

Now consider production.

A CI pipeline produces one immutable artifact.

That artifact is promoted to:

```text
staging
region A
region B
canary
production
```

Suppose the release eventually creates 100 JVM processes.

The annotation processor ran when the artifact was built.

It does not run again in each container.

The generated graph is already inside the artifact.

This gives compile-time work exceptional leverage.

One analysis pass feeds many runtime instances.

Conceptually:

```text
          compile once
              ↓
        generated artifact
        ↙      ↓      ↘
   instance instance instance
      ↓        ↓        ↓
   no graph rediscovery
```

The larger the deployment, the more favorable this asymmetry becomes.

---

## Rolling Deployments Multiply Startup Savings { #rolling-deployments-multiply }

Suppose an application runs 50 replicas.

A new release causes Kubernetes to gradually create 50 replacements.

If Kora reaches readiness two seconds faster per instance, the simplistic aggregate startup saving is:

```text
50 × 2 seconds = 100 instance-seconds
```

The deployment does not necessarily become 100 seconds faster because replicas may start concurrently.

But the fleet spends 100 fewer aggregate instance-seconds waiting for application readiness.

That affects:

- rollout duration;
- surge occupancy;
- time under mixed versions;
- recovery margin;
- autoscaling overlap.

The build-time work was paid once.

The startup advantage was collected 50 times.

Deploy twice that day:

```text
100 runtime starts
```

without another clean framework analysis if the same artifact is being redeployed.

The multiplier grows.

---

## Horizontal Scaling Multiplies It Again { #horizontal-scaling-multiplies }

A production artifact may live for days while replicas come and go.

Suppose traffic creates:

```text
200 scale-out starts
```

during the artifact's lifetime.

If compilation added:

```text
3 seconds
```

to produce the artifact, and each instance saves:

```text
1 second
```

of startup:

```text
build cost:      +3 seconds
runtime saving: -200 seconds
```

The runtime payoff dominates.

This is why cloud-native infrastructure strengthens the compile-time argument.

Elastic systems are designed to create and destroy processes.

Anything paid per process is multiplied by elasticity.

Anything paid once per artifact is amortized.

---

## Restarts and Rescheduling Are Hidden Multipliers { #restarts-and-rescheduling }

Not all starts are planned.

Pods restart because of:

- node maintenance;
- memory pressure;
- application failure;
- node loss;
- cluster upgrades;
- autoscaler consolidation;
- availability-zone events;
- spot interruption.

Every restart replays startup.

It does not replay the original application build.

That makes startup work recurring operational debt.

Compile-time generation converts part of that recurring debt into a one-time artifact-production cost.

This is especially valuable in unstable or highly elastic environments.

---

## CI Can Contain More Starts Than Production { #ci-can-contain }

A surprising multiplier appears in testing.

An application might run 20 production replicas but start hundreds of times per day in CI.

Consider:

```text
50 pull requests/day
× 4 test shards
× 2 application starts/shard
= 400 starts/day
```

A one-second startup improvement saves:

```text
400 seconds/day
```

for one repository.

Across 100 repositories:

```text
40,000 seconds/day
≈ 11 hours/day
```

of aggregate CI wait/compute.

Again, parallel execution means wall-clock effects differ from aggregate compute effects.

But the multiplier is real.

Compile-time generation is particularly attractive when the generated artifact or test classes can be reused while application contexts are repeatedly started.

---

## Full-Context Tests Benefit Disproportionately { #full-context-tests }

Unit tests do not care much about application startup.

They typically instantiate a handful of objects.

The trade becomes important in:

- component tests;
- integration tests;
- black-box tests;
- end-to-end service tests.

These tests often follow:

```text
compile
→ start context/application
→ execute scenario
→ stop
```

If startup is cheap, realistic tests become cheap enough to run more frequently.

That changes engineering behavior.

Teams can prefer:

```text
real application graph
```

over:

```text
large mock structure
```

in more cases.

The build may have done more work, but that work enables many cheap runtime verifications.

---

## Build Once, Test Many Is a Powerful Pattern { #build-once-test }

A particularly favorable pipeline structure is:

```text
compile + generate once
    ↓
produce application/test artifacts
    ↓
run many test scenarios against them
```

For example:

```text
generated graph
    ↓
test shard A
test shard B
test shard C
test shard D
```

The compile-time analysis is shared.

The runtime startup is repeated.

This is exactly the pattern where Kora's trade-off compounds.

The more post-build stages reuse the same compiled architecture, the more valuable moving work left becomes.

---

## Build-Time Processing Can Improve Runtime Memory Too { #build-time-processing }

The startup benefit is obvious, but moving work left can also change runtime footprint.

A runtime container may need metadata structures describing:

- components;
- dependency relationships;
- annotations;
- proxy behavior;
- route definitions;
- reflection metadata.

If those structures are converted into ordinary compiled code, less runtime metadata may need to remain resident.

The exact memory outcome depends on application structure and implementation details, so it should be measured rather than assumed.

But architecturally, generated direct code can reduce the need for framework-owned runtime representations.

That means compile-time work can pay back over the entire process lifetime, not only during startup.

---

## Generated Direct Calls Can Help the Hot Path Too { #generated-direct-calls }

Moving decisions to compilation can also eliminate layers from request processing.

If the framework generates a direct handler or repository implementation, runtime execution can often be closer to:

```text
direct method call
```

than:

```text
generic metadata lookup
→ reflective invocation
→ adapter dispatch
```

Again, modern JVMs optimize many dynamic patterns surprisingly well, and production performance must be measured.

But the architecture gives the JIT straightforward code to optimize.

This matters because the same generated source that increases build work may improve:

```text
startup
+
steady-state throughput
+
allocation behavior
+
debuggability
```

The build cost is paying for more than one runtime property.

---

## Compile-Time AOP Shows the Trade Clearly { #compile-time-aop }

Cross-cutting behavior is another example.

A runtime AOP system may need to create proxies dynamically and interpret interception metadata.

Kora generates AOP-related wrappers during compilation.

For annotations such as:

- resilience;
- validation;
- caching;
- transactions;
- security;
- logging;

the application can receive generated implementations that contain the wrapping logic explicitly.

This shifts proxy construction from:

```text
application startup
```

to:

```text
source generation
```

and shifts some failure detection from runtime to compilation.

The runtime executes already-generated behavior.

The price is additional processor work.

The payoff is repeated every time that artifact starts and every time the method executes.

---

## Repository Generation Is Another Example { #repository-generation-is }

A repository abstraction has enough static information to generate substantial implementation code.

The compiler knows:

- method signatures;
- return types;
- query annotations;
- parameter types;
- mapping contracts.

Kora can generate repository infrastructure from that information.

A runtime framework could instead inspect repository interfaces and construct dynamic implementations after startup.

Both models can present a similarly convenient API to the developer.

The difference is where implementation work occurs.

Kora's answer is:

```text
prefer generation before runtime
```

when the necessary information is already known.

This is the recurring architectural theme.

---

## HTTP Routing Can Be Precomputed Too { #http-routing-can }

Routes are typically static for a built service.

The compiler knows:

```text
HTTP method
path
controller
method signature
request mapper
response mapper
interceptors/aspects
```

There is rarely a business reason to rediscover that entire mapping from annotations after every JVM process starts.

Generated route infrastructure converts that static contract into executable code ahead of time.

The runtime still has to register handlers with the server, but the framework does not need to reinterpret as much application structure.

Again:

```text
compile-time analysis
→ generated implementation
→ cheaper startup
```

---

## Moving Work Left Is Not the Same as Native Image Compilation { #moving-work-left }

Compile-time framework generation is sometimes confused with ahead-of-time native compilation.

They are different layers.

Kora can generate application infrastructure at build time while still producing normal JVM bytecode and running on HotSpot.

The flow is:

```text
Kora compile-time processing
    ↓
Java/Kotlin source generated
    ↓
JVM bytecode
    ↓
HotSpot runtime
```

This retains familiar JVM deployment characteristics:

- JIT optimization;
- normal JVM tooling;
- standard profiling;
- standard libraries;
- virtual threads;
- mature GC options.

The build-time architecture does not require abandoning the JVM runtime model.

That distinction is important because the trade is comparatively modest: do more semantic framework work during ordinary compilation, not necessarily compile the entire application into a native
executable.

---

## The Compiler Becomes Part of the Framework Runtime Architecture { #the-compiler-becomes }

In a runtime-heavy framework, the framework engine is primarily a runtime component.

In Kora, part of the framework effectively lives in the build toolchain.

Conceptually:

```text
Kora framework
├── compile-time processors
│   ├── graph analysis
│   ├── code generation
│   ├── validation
│   └── contract checking
│
└── runtime modules
    ├── HTTP server
    ├── data integrations
    ├── Kafka
    ├── telemetry
    ├── resilience
    └── lifecycle
```

This separation is important.

A larger compile-time system allows a smaller runtime system.

That is the architectural exchange.

---

## Build-Time Complexity Must Be Engineered Carefully { #build-time-complexity }

Moving work left is not automatically good.

A bad annotation processor can destroy development productivity.

Problems can include:

- processing the entire project after every edit;
- generating unstable outputs;
- defeating incremental compilation;
- excessive generated source volume;
- poor diagnostics;
- long processor initialization;
- unnecessary cross-module invalidation.

If compile-time generation is part of the framework architecture, processor performance becomes a first-class product concern.

Kora therefore has to optimize two runtimes:

```text
application runtime
+
compiler/build-time runtime
```

The landing's separation of clean and cached build measurements is important because it acknowledges this.

A compile-time framework should be judged not only by how quickly the resulting service starts, but by whether normal development builds remain efficient.

---

## Incremental Processing Is Not Optional for a Mature Compile-Time Framework { #incremental-processing-is }

Once code generation becomes broad—DI, repositories, HTTP, JSON, AOP, configuration, and more—incremental processing becomes strategically important.

Without it, the trade could become:

```text
fast production startup
for
slow developer iteration
```

That would merely move pain from operations to engineering.

The desirable trade is:

```text
slightly more compiler work
+
efficient incremental invalidation
→
fast development loop
+
very fast runtime startup
```

This is why Gradle incremental annotation-processing support and KSP incremental processing matter more than they may appear from a feature list.

They are what make moving work left scalable for large codebases.

---

## Multi-Module Builds Make Boundaries More Important { #multi-module-builds }

Large services are often split into Gradle modules.

That can improve compile-time economics because unchanged modules do not always need to be rebuilt.

Imagine:

```text
:domain
:service
:database
:http
:application
```

A local change in:

```text
:domain
```

may affect only a subset of downstream modules.

A change in the application graph root may affect broader generation.

Good module boundaries therefore help both architecture and build performance.

This creates a useful interaction:

```text
modular source architecture
→ smaller invalidation scope
→ faster incremental compile
```

Compile-time frameworks reward clean dependency structure.

Poorly designed modules with broad API coupling can make any build system slower.

Kora does not remove that reality.

---

## ABI Changes Are More Expensive Than Implementation Changes { #abi-changes-are }

A build system can often isolate changes that do not alter a module's public binary interface.

Changing method internals may require recompiling one class.

Changing a constructor signature can invalidate callers.

Changing a component contract may alter generated graph wiring.

This means developers should distinguish:

```text
implementation change
```

from:

```text
structural/ABI change
```

Compile-time processing makes this distinction particularly visible.

That is not an arbitrary processor penalty.

Structural changes genuinely affect more of the program.

---

## Generated Source Size Is a Real Cost { #generated-source-size }

Another trade-off is source and bytecode volume.

If the framework generates explicit implementations instead of using a smaller generic runtime interpreter, the artifact may contain more generated classes.

That can affect:

- compilation;
- artifact size;
- class loading;
- IDE indexing;
- debugging navigation.

These effects should be measured.

But code volume and runtime machinery trade against one another.

A small generic interpreter may require more metadata and runtime branching.

Generated explicit code may produce more classes but less interpretation.

Kora chooses explicitness.

The best balance depends on processor quality and application scale.

---

## Clean CI Runners Expose the Full Cost { #clean-ci-runners }

Some CI systems use disposable workers with empty local caches.

For them, every pipeline may resemble a clean build more closely than a developer machine.

That can make compile-time processing cost highly visible.

There are several ways to address this operationally:

```text
remote Gradle build cache
dependency cache
persistent workers
layered pipeline artifacts
compile once / test many
```

The right architecture depends on CI infrastructure.

The important point is that moving work left changes where optimization effort belongs.

A runtime-heavy framework may need startup optimization.

A compile-time framework may benefit more from build-cache architecture.

Both are engineering problems.

The question is which one scales better for the organization.

---

## Remote Build Caches Strengthen the Compile-Time Model { #remote-build-caches }

A remote build cache allows one machine's build outputs to be reused by another machine when inputs match.

This is particularly interesting for generated code because the output is static.

If generation tasks are cacheable and deterministic, a CI agent may not need to regenerate the same result that another build already produced.

Runtime startup has no exact equivalent.

A Pod in another region cannot simply reuse the already-running object graph from another process.

It still needs its own live objects.

Therefore, moving deterministic work into a cacheable phase creates optimization possibilities that do not exist when the same work is deferred until process startup.

This is a strong systems argument for build-time computation.

---

## Artifact Promotion Makes the Trade Even Better { #artifact-promotion-makes }

Good deployment pipelines build an artifact once and promote the same artifact through environments.

For example:

```text
commit
    ↓
build artifact
    ↓
integration
    ↓
staging
    ↓
canary
    ↓
production
```

The annotation processor runs at the top.

The generated application graph is reused everywhere below it.

This means the compile-time cost is amortized across:

```text
all test starts
+
all staging instances
+
all canary instances
+
all production instances
```

Rebuilding separately for every environment would weaken this advantage and is usually undesirable for reproducibility anyway.

Immutable artifact promotion and compile-time frameworks fit naturally together.

---

## "N Times Every Deployment" Is the Core Production Argument { #n-times-every }

Suppose one application artifact is deployed to:

```text
N replicas
```

If Kora startup saves:

```text
S seconds/replica
```

then each full replacement cycle saves roughly:

```text
N × S instance-seconds
```

of startup occupancy.

Deploy:

```text
D times
```

and the repeated effect is:

```text
N × S × D
```

Across:

```text
M services
```

the aggregate becomes:

```text
N × S × D × M
```

The compile-time cost is associated primarily with:

```text
builds × B
```

This is why the trade must be evaluated at deployment frequency, not just developer compile frequency.

For cloud-native services:

```text
startup saved N× every deployment
```

is often the dominant insight.

---

## Autoscaling Adds Starts Without Adding Builds { #autoscaling-adds-starts }

Autoscaling makes the asymmetry even sharper.

A service can scale:

```text
10 → 30 → 10 → 40 → 10
```

many times while running exactly the same artifact.

No annotation processing occurs during these events.

No generated source is rebuilt.

The runtime benefit is collected repeatedly for free from the perspective of the build.

This means the more elastic the service, the more valuable fast startup becomes relative to build overhead.

Static services have a smaller multiplier.

Elastic services have a larger one.

---

## Spot and Node Churn Add More Runtime Reuse { #spot-and-node }

Spot nodes and aggressive cluster autoscaling create additional process churn.

The artifact remains unchanged.

Instances disappear and reappear.

Every replacement pays startup.

None repays compilation.

That makes compile-time precomputation especially well aligned with disposable infrastructure.

Traditional long-lived application servers started rarely.

Modern container platforms start processes as routine control-plane operations.

The economic environment changed.

Framework architecture should reflect that.

---

## Scale-to-Zero Is the Extreme Case { #scale-to-zero }

Scale-to-zero takes the concept to its logical endpoint.

When no instance remains, the next work event requires cold capacity to be created again.

The same artifact may repeatedly transition:

```text
0 → N → 0 → N → 0
```

Build cost is unchanged.

Startup cost repeats every activation.

This makes startup latency part of the workload's service model.

Moving deterministic initialization work into compilation therefore directly increases the practicality of scale-to-zero.

---

## The Developer Loop Has a Different Break-Even Point { #the-developer-loop }

Production strongly favors one build feeding many starts.

Development can be different.

A developer often changes source and recompiles before each start:

```text
edit
→ build
→ start
→ edit
→ build
→ start
```

Now the compile cost and startup saving may occur at similar frequency.

This is why incremental compilation matters so much.

If each edit forces a full expensive processor pass, the runtime benefit may not compensate in the local loop.

If most edits produce cheap incremental builds, then the developer can receive both:

```text
fast compile
+
fast startup
```

The quality of the build pipeline determines the local break-even point.

---

## The Correct Developer Metric Is Time-to-Verified-Change { #the-correct-developer }

Instead of separately optimizing:

```text
compile time
startup time
test time
```

measure:

```text
time-to-verified-change
```

That is:

```text
edit
    ↓
compile
    ↓
process/generate
    ↓
start context
    ↓
run relevant test
    ↓
result
```

A framework that builds one second slower but starts tests five seconds faster can still provide a better loop.

A framework that starts instantly but adds 30 seconds to every incremental compile may be worse.

The total loop decides.

Kora's philosophy is strongest when annotation/KSP processing remains incremental enough that startup savings dominate normal workflows.

---

## Build Time Also Buys Better Diagnostics { #build-time-also }

There is another reason not to compare seconds mechanically.

A compiler error is usually more useful than a startup exception.

The build may spend additional time analyzing the graph, but the output can be:

```text
precise structural diagnostic
```

instead of:

```text
runtime failure after initialization begins
```

Better diagnostics reduce human investigation time.

Suppose compile-time processing adds:

```text
500 ms
```

to an iteration but avoids one 15-minute debugging session each month.

The human economics dwarf the CPU cost.

Not every generated error is perfect, of course.

But moving structural checks into compilation creates the opportunity for precise diagnostics at the location where source relationships are already known.

---

## AI Agents Benefit From the Same Shift { #ai-agents-benefit }

AI-assisted development makes this trade even more interesting.

An agent works best with short, deterministic feedback:

```text
generate code
→ compiler responds
→ inspect error
→ patch
→ retry
```

If architectural mistakes appear only at runtime, each agent iteration must:

```text
compile
→ package
→ start
→ fail
→ parse runtime logs
```

That loop is slower and more ambiguous.

Generated source also gives the agent something concrete to inspect.

For a framework increasingly used alongside coding agents, compile-time work can reduce the number of expensive speculative runtime cycles.

The cost moves into a deterministic machine-checkable stage.

---

## Moving Work Left Is a Risk-Reduction Strategy { #moving-work-left-2 }

The performance argument is only half the story.

Every activity moved from runtime to build time reduces the number of things that can unexpectedly fail after deployment.

If a dependency graph is already validated, production does not need to discover basic wiring failure.

If a mapper is already generated and type-checked, runtime does not need to synthesize it dynamically.

If a repository contract is validated during generation, some classes of misuse are eliminated before packaging.

The deployment artifact contains more resolved decisions.

Operationally, this means the artifact is closer to:

```text
known executable architecture
```

and further from:

```text
instructions for constructing architecture later
```

That is a meaningful reliability property.

---

## A Useful Analogy: Link Time { #a-useful-analogy }

Traditional compiled systems already accept similar trade-offs.

A linker spends time resolving symbols and constructing a final executable.

Nobody argues that the program should resolve all ordinary symbol relationships from scratch every time it starts simply because linking takes time.

The build phase exists precisely because some work is better done once before execution.

Kora applies a similar philosophy at a higher application-framework level.

Dependency injection, route wiring, repository implementation, and aspects become closer to compilation/linking concerns.

They are part of producing the executable architecture.

---

## Another Analogy: Database Query Planning { #another-analogy-database }

Databases distinguish between planning work and execution work.

In some situations, preparing or caching a plan is worthwhile because the same structure executes repeatedly.

Framework generation follows a similar idea:

```text
analyze structure once
→ execute many times
```

If the structure changes constantly at runtime, precomputation is less useful.

If the structure is stable for the lifetime of an artifact, precomputation is natural.

Backend service architecture is usually very stable between deployments.

That makes it a good candidate.

---

## Build Cost Is Visible; Runtime Cost Is Diffuse { #build-cost-is }

One psychological reason teams resist compile-time processing is that build cost is painfully visible.

A developer runs a command and watches it take longer.

Runtime structural cost is diffuse.

It is spread across:

```text
every Pod
every test context
every deployment
every restart
every developer run
```

No individual event looks large.

This can bias decisions toward minimizing build time even when total system time increases.

The same bias appears in many engineering systems:

```text
centralized visible cost
vs
distributed invisible cost
```

Fleet-scale thinking corrects for it.

---

## One Extra Second in the Build Is Not Equal to One Extra Second in Startup { #one-extra-second }

Even when frequency is equal, the context differs.

Builds often happen on dedicated CI hardware where tasks can run in parallel and outputs can be cached.

Startup often happens during a capacity-sensitive event:

- a deployment;
- a traffic spike;
- a restart;
- a failover.

One startup second may therefore have a higher operational value than one build second.

During a spike, delayed readiness means missing serving capacity.

During deployment, delayed readiness extends the rollout window.

During failure recovery, delayed readiness prolongs reduced redundancy.

Build time usually affects delivery latency.

Startup time can affect availability.

The seconds are not economically interchangeable.

---

## But Build Time Still Matters { #but-build-time }

This does not mean build performance can be ignored.

A framework that makes clean and incremental builds unacceptably slow damages:

- developer productivity;
- CI throughput;
- merge velocity;
- release frequency.

The correct philosophy is not:

```text
move unlimited work into compilation
```

It is:

```text
move deterministic runtime work left
when it can be processed efficiently,
incrementally, transparently, and reused.
```

Kora's build architecture has to earn the startup benefit.

The trade should always be measured.

---

## What Should Be Moved Left? { #what-should-be }

Good candidates have several properties.

They are:

```text
deterministic
known from source/contracts
stable for a built artifact
expensive or unnecessary to rediscover repeatedly
```

Examples include:

- dependency topology;
- route declarations;
- mapping code;
- repository structure;
- AOP wrapping;
- configuration interfaces;
- serialization logic;
- OpenAPI-derived contracts.

Poor candidates are values that are genuinely runtime-dependent:

- live database state;
- current service-discovery membership;
- dynamic credentials;
- current feature flags;
- remote configuration values;
- active network connections.

Kora does not try to compile the live world.

It compiles the static architecture that interacts with that world.

---

## The Boundary Between Static and Dynamic Is the Architecture { #the-boundary-between }

A well-designed compile-time framework needs a clear boundary:

```text
compile-time:
What is the application structurally?

runtime:
What is the current environment and state?
```

Compile-time can decide:

```text
This repository needs this database client.
```

Runtime decides:

```text
Which database host is configured today?
```

Compile-time can decide:

```text
This route invokes this controller method.
```

Runtime decides:

```text
What request just arrived?
```

Compile-time can decide:

```text
This method has a retry aspect.
```

Runtime decides:

```text
Did this particular call fail?
```

This separation is what allows Kora to move substantial work left without turning the application into a static executable configuration.

---

## Build-Time Generation Improves Architecture Visibility { #build-time-generation }

Another side effect is that architecture becomes inspectable before runtime.

Generated graph code can show:

```text
component creation
dependency edges
module calls
handler assembly
```

This is useful during code review and debugging.

A runtime container often requires tools or framework knowledge to inspect its resolved state after startup.

Kora can externalize much of that state into generated source.

The compiler phase therefore produces not only executable code but an architectural trace.

That transparency is difficult to express as a benchmark number, but it reduces operational and maintenance cost.

---

## Clean Build vs Cached Build Should Always Be Reported Separately { #clean-build-vs }

Framework performance discussions often publish a single build number.

That is inadequate for compile-time frameworks.

At minimum, distinguish:

```text
clean build
cached/incremental build
```

The clean build reveals:

```text
total generation and compilation cost
```

The cached build reveals:

```text
day-to-day iteration efficiency
```

Both matter.

A framework can have a slower clean build but excellent incremental behavior.

Another can have a fast clean build but poor invalidation.

Without both numbers, platform teams cannot judge the real developer trade-off.

Kora's landing explicitly presenting startup/readiness, clean build, and cached build as separate views is therefore the right methodology.

---

## CI Should Measure Cache-Hit and Cache-Miss Paths Too { #ci-should-measure }

Large engineering organizations should go further.

Track:

```text
cold CI build
warm dependency-cache build
remote build-cache hit
partial cache hit
incremental PR build
```

These paths may have dramatically different costs.

If most production pipelines get high cache-hit rates, cold build performance matters less.

If security policy forces every CI runner to start from nothing, clean build performance matters more.

Framework architecture does not exist independently of build infrastructure.

The platform needs to evaluate the combination.

---

## Build Caches Turn Compute Into Storage { #build-caches-turn }

There is another systems trade.

Caching generated outputs means exchanging:

```text
CPU time
```

for:

```text
cache storage + transfer
```

This is usually favorable when outputs are reused frequently, but not always.

A remote cache with very large generated artifacts and slow network transfer can become counterproductive.

Therefore, generated output size and cacheability matter.

The general principle remains:

```text
precompute if reuse is cheaper than recomputation
```

Kora's architecture creates reusable static outputs, but the build platform still has to manage them intelligently.

---

## Generated Source Should Be Deterministic { #generated-source-should }

Caching works best when the same inputs produce the same outputs.

Code generators should avoid unnecessary nondeterminism such as:

- timestamps in generated source;
- unstable ordering;
- environment-specific paths;
- random identifiers.

Deterministic generation improves:

- cache hits;
- reproducible builds;
- code inspection;
- test stability.

This is another reason build-time frameworks need mature compiler engineering.

The generator is effectively part of the build compiler.

Its output quality matters.

---

## Parallelism Exists on Both Sides of the Trade { #parallelism-exists-on }

The comparison is not simply sequential build versus sequential startup.

Build systems can parallelize independent modules and tasks.

Kora runtime initialization can also initialize parts of the graph in parallel where dependencies allow it.

This creates two graphs:

```text
build dependency graph
runtime component graph
```

Efficient systems exploit parallelism in both.

At build time:

```text
independent modules compile concurrently
```

At startup:

```text
independent application components initialize concurrently
```

Moving work left does not mean all latency is transferred directly from one critical path to another.

The actual wall-clock effect depends on graph parallelism.

---

## Critical Path Matters More Than Total CPU Work { #critical-path-matters }

Suppose annotation processing performs two seconds of CPU work but runs partly in parallel with other build activity.

The wall-clock build penalty may be less than two seconds.

Likewise, removing two seconds of aggregate startup work may reduce the critical readiness path by only one second if components were already initializing concurrently.

This is why measurements should distinguish:

```text
CPU work
```

from:

```text
wall-clock critical path
```

For deployment and developer experience, wall clock matters most.

For infrastructure efficiency, total CPU can matter too.

---

## Startup Saved N× Is About Critical Capacity, Not Just CPU { #startup-saved-n }

When a new replica starts during HPA scale-out, the relevant outcome is not how much CPU startup consumed.

It is:

```text
when does the replica become useful?
```

Compile-time generation helps because the structural framework phase is already complete.

That can shorten:

```text
process start → readiness
```

The value is operational.

One second saved on 50 replicas starting during a traffic surge can mean capacity arrives one second earlier across the fleet.

That cannot be evaluated purely as saved compute time.

It is saved response time of the infrastructure itself.

---

## Build-Time Work Has Better Failure Locality { #build-time-work }

A processor failure happens close to the source change that caused it.

A runtime startup failure may happen:

- on a developer machine;
- in CI;
- in staging;
- during deployment;
- after an autoscaler creates a rare code path.

Moving checks earlier narrows failure locality.

The earlier the failure:

```text
fewer systems involved
fewer logs
fewer infrastructure layers
smaller debugging search space
```

This is an engineering productivity benefit.

---

## Compile-Time Generation Fits Immutable Infrastructure { #compile-time-generation }

Immutable infrastructure assumes:

```text
artifact is built
artifact is tested
artifact is deployed unchanged
```

Kora's model aligns with this naturally.

The generated graph becomes part of the immutable artifact.

Runtime is not expected to reinterpret application structure based on whatever happens to be on the classpath after deployment.

That makes the executable architecture more deterministic.

For modern container platforms, this is often exactly what the deployment model already wants.

---

## Dynamic Runtime Extensibility Is the Counter-Trade { #dynamic-runtime-extensibility }

There are situations where moving work left is less attractive.

Imagine a platform that must:

- load arbitrary plugins after deployment;
- discover implementations from externally supplied JARs;
- enable new component types without rebuilding;
- construct application topology dynamically from runtime state.

Compile-time graph resolution can become restrictive in such a system.

A runtime container has an advantage because it intentionally delays decisions.

Kora is optimized for another category:

```text
statically built server applications
```

where deployment itself is the mechanism for changing architecture.

For that workload, compile-time resolution is usually a better fit.

This is why no architectural trade is universally optimal.

---

## Microservices Strengthen Kora's Choice { #microservices-strengthen-kora }

Microservice architecture tends to produce:

```text
many small artifacts
many replicas
frequent deployments
frequent restarts
lots of CI
```

That is exactly the environment where:

```text
build once
start many
```

becomes common.

Monolithic systems with one huge application and rare restarts may have a different cost balance.

Kora's cloud-oriented design is therefore consistent with its compile-time architecture.

The infrastructure model amplifies the runtime savings.

---

## Deployment Frequency Changes the Equation { #deployment-frequency-changes }

Consider two organizations.

### Organization A { #organization-a }

```text
deploy each service once per month
2 replicas
little autoscaling
```

Startup speed matters, but the multiplier is modest.

### Organization B { #organization-b }

```text
continuous delivery
20 replicas/service
multiple regions
frequent autoscaling
ephemeral test environments
spot nodes
```

The same per-start saving is worth far more.

This suggests a useful framework-evaluation principle:

> **The more frequently your infrastructure creates JVMs, the more valuable compile-time precomputation becomes.**

Kora's trade is most compelling in high-churn environments.

---

## Developer Count Changes the Build Side { #developer-count-changes }

The other side of the equation also has multipliers.

A slower incremental build affects:

```text
developers × iterations/day
```

A slower clean CI build affects:

```text
repositories × pipelines/day
```

Therefore, build cost must also be evaluated at fleet scale.

The complete model is not biased toward runtime.

It is:

```text
build cost × build frequency
vs
startup/runtime saving × runtime frequency
```

Both frequencies can be enormous.

This is why cached/incremental behavior is critical.

---

## A More Complete Economic Formula { #a-more-complete }

For one service:

```text
Annual compile-time overhead =
    Δclean_build × clean_build_count
  + Δincremental_build × incremental_build_count
```

Runtime benefit:

```text
Annual runtime benefit =
    Δstartup
  × (
        developer_starts
      + CI_starts
      + staging_starts
      + production_deploy_starts
      + autoscaling_starts
      + restart_starts
    )
```

Then add the value of:

```text
earlier compiler failures
reduced warm-up
lower runtime metadata
hot-path efficiency
```

The break-even calculation becomes more realistic.

---

## Example: One Service { #example-one-service }

Suppose:

```text
Kora clean build penalty:        +4 s
Kora incremental build penalty:  +0.2 s
startup saving:                  2 s
```

Per working day:

```text
1 clean build
40 incremental builds
20 local/context starts
30 CI starts
5 deployment/staging starts
```

Build-side extra time:

```text
4
+ 40 × 0.2
= 12 s
```

Startup-side saving:

```text
(20 + 30 + 5) × 2
= 110 s
```

Net:

```text
98 s/day
```

This is only illustrative.

The real values must be measured.

But it shows why a visibly slower clean compile can coexist with a substantially faster total system loop.

---

## Example: Production Fleet { #example-production-fleet }

Suppose a service has:

```text
30 replicas
4 deployments/day
```

A full rollout creates roughly:

```text
30 starts
```

ignoring canary and failure retries.

Daily deployment starts:

```text
30 × 4 = 120
```

At a two-second startup advantage:

```text
240 instance-seconds/day
```

Now add HPA activity:

```text
80 starts/day
```

and node/restart churn:

```text
20 starts/day
```

Total:

```text
220 starts/day
× 2 s
= 440 instance-seconds/day
```

The artifact may have been built only four times.

The runtime multiplier is already large.

---

## Example: Company Scale { #example-company-scale }

Now imagine:

```text
300 services
average 50 starts/service/day
startup saving 1.5 s
```

Aggregate:

```text
300 × 50 × 1.5
= 22,500 instance-seconds/day
≈ 6.25 instance-hours/day
```

The direct compute saving may not be the important part.

Those seconds occur during:

- deployment;
- scaling;
- recovery;
- CI.

Their real value is shorter control loops.

This is the same fleet-economics logic applied to time.

---

## Startup Cost Has a Reserve-Capacity Consequence { #startup-cost-has }

If new instances take longer to become ready, existing instances must carry load longer.

That can require more static reserve.

A compile-time framework that starts faster may therefore allow:

```text
lower minimum replica count
lower per-replica headroom
faster scale-to-zero activation
```

when the rest of the platform supports it.

Now the build-time trade can influence recurring infrastructure cost.

A few extra seconds in compilation may reduce months of baseline capacity reservation.

That is a radically asymmetric exchange.

---

## Build-Time Work Is Easier to Centralize { #build-time-work-2 }

Build optimization can be addressed once at platform level:

- remote cache;
- standard Gradle configuration;
- optimized CI images;
- daemon strategy;
- module conventions;
- processor upgrades.

The benefit propagates across services.

Runtime startup work is distributed across every process.

This makes build-side optimization organizationally attractive.

A platform team can invest in one high-quality build pipeline and amortize the cost.

---

## Processor Upgrades Can Improve Every Service { #processor-upgrades-can }

Because compile-time generation is centralized inside the framework, performance improvements in processors can reduce build cost fleet-wide.

Likewise, runtime generation improvements can improve startup for every service after upgrade.

This creates leverage:

```text
one framework optimization
× all applications
```

Kora's compiler architecture therefore gives the framework maintainers a place to concentrate optimization effort that individual application teams inherit automatically.

---

## A Build Regression Is Easier to Observe Than a Startup Regression { #a-build-regression }

Another advantage of the compile-time boundary is measurability.

CI can track:

```text
compileJava duration
KSP duration
annotation processor time
generated source count
artifact build duration
```

and alert when they regress.

Startup can also be measured, but it is more environment-sensitive:

- CPU throttling;
- DNS;
- database availability;
- image pulls;
- node contention;
- remote services.

Build-time deterministic work is often easier to isolate.

That does not make build cost unimportant.

It makes it more controllable.

---

## The Right Dashboard Has Both Build and Startup { #the-right-dashboard }

Platform teams evaluating Kora should track at least:

```text
clean artifact build p50/p95
incremental build p50/p95
cache hit ratio
annotation/KSP processing duration
generated source volume
application startup p50/p95
time-to-readiness p50/p95
```

Then connect those metrics to frequency:

```text
builds/day
starts/day
deployments/day
test starts/day
```

Without frequency, the raw times cannot be valued correctly.

---

## Don't Optimize One Side Blindly { #don-t-optimize }

There are two failure modes.

### Failure mode one { #failure-mode-one }

Optimize runtime at any build cost.

Result:

```text
fast service
slow engineering organization
```

### Failure mode two { #failure-mode-two }

Optimize build at any runtime cost.

Result:

```text
fast compilation
slow deployment/scaling/recovery
```

The correct target is minimum total lifecycle cost.

Kora intentionally accepts some build work because its architecture expects the runtime saving to repeat.

The trade is successful only if incremental builds remain sufficiently cheap.

---

## Performance Work Should Follow Multiplicity { #performance-work-should }

This suggests a general optimization rule:

> Optimize work in proportion to how often it is repeated.

If a calculation occurs:

```text
once/build
```

and saves work that would otherwise occur:

```text
100 times/artifact
```

spending more effort on the first phase can be rational.

If the calculation occurs:

```text
100 times during development
```

and saves work:

```text
once in production
```

it may not be.

Multiplicity matters more than the location of the work alone.

Kora's architecture is based on the observation that many framework decisions are stable and runtime starts are numerous.

---

## "Move Left" Also Means Move Understanding Left { #move-left-also }

The phrase “shift left” is often used for security and testing.

Kora applies a similar idea to framework understanding.

Instead of discovering architecture during execution:

```text
run application
→ inspect container
→ infer graph
```

the developer gets:

```text
source
→ compiler analysis
→ generated source
→ explicit graph
```

Understanding moves earlier too.

This improves:

- code review;
- onboarding;
- debugging;
- AI-assisted development.

The build becomes a place where the framework explains itself.

---

## Build Artifacts Become More Complete { #build-artifacts-become }

A runtime-heavy artifact can be thought of as containing:

```text
application code
+
instructions for framework discovery
```

A compile-time artifact contains more of:

```text
application code
+
resolved framework implementation
```

That makes the built artifact semantically richer.

More architectural decisions have already been finalized.

This is part of why startup can be smaller.

The process is executing a more complete product.

---

## Why Kora's Approach Fits Modern CPUs Better { #why-kora-s }

Generated direct code also gives the JVM compiler a conventional optimization target.

The JIT is very good at optimizing:

- ordinary method calls;
- predictable branches;
- stable types;
- inlining.

Deep runtime interpretation can introduce generic layers that the JIT may or may not eliminate completely.

Generated source makes the execution model explicit.

This is not merely a startup optimization.

It aligns framework infrastructure with the optimization model Java already does well.

Again, the cost is compile-time generation.

The benefit may persist through the entire process lifetime.

---

## The Build Pipeline Becomes Part of Runtime Performance Engineering { #the-build-pipeline }

This is perhaps the most important conceptual shift.

In Kora, runtime performance cannot be separated from the build pipeline.

The framework achieves runtime properties partly by doing work before runtime.

Therefore:

```text
build engineering
```

is part of:

```text
runtime performance engineering
```

Annotation processor performance, KSP performance, incremental invalidation, generated-code quality, cacheability, and artifact construction all influence the final service economics.

This is a more compiler-oriented way to build a backend framework.

---

## What CTOs Should Ask { #what-ctos-should }

A CTO or platform team evaluating this trade should ask more than:

```text
Which framework has the fastest startup?
```

Ask:

```text
What is the clean-build penalty?
What is the incremental-build penalty?
How much processor work is invalidated by normal edits?
Does remote caching work well?
How much startup is saved?
How many times is each artifact started?
How often do we deploy?
How elastic are our services?
How many full-context tests do we run?
How much earlier do structural failures appear?
```

Then model the organization.

The right answer depends on the multiplication factors.

---

## What Developers Should Ask { #what-developers-should }

At the project level, measure:

```text
./gradlew clean distTar
```

or the actual release artifact task.

Then measure a normal edit:

```text
change method body
→ compile/test
```

Then a structural edit:

```text
change component dependency
→ compile/test
```

Then measure:

```text
process start → readiness
```

Finally, measure:

```text
edit → verified behavior
```

The last number is usually the most important developer metric.

---

## The Best Result Is Not Minimum Build Time { #the-best-result }

A framework whose build finishes in one second but requires ten seconds of startup may be worse for a workflow that starts the application 20 times.

A framework whose clean build takes five seconds longer but whose incremental path is fast and whose application starts almost immediately may produce a better overall loop.

The goal is not:

```text
min(build)
```

or:

```text
min(startup)
```

It is closer to:

```text
min(
    build_frequency × build_cost
  + start_frequency × startup_cost
  + runtime_frequency × runtime_overhead
)
```

subject to:

```text
correctness
developer productivity
operational reliability
```

That is the actual optimization problem.

---

## The Trade Is Strongest When Generated Knowledge Is Reused { #the-trade-is }

The more times the same architectural knowledge is reused, the better compile-time generation looks.

Reuse occurs across:

```text
process starts
test starts
deployment replicas
regions
developer runs
CI shards
restarts
```

The generated source does not need to be reinterpreted into architecture each time.

It is already architecture.

This is Kora's central bet.

---

## When the Trade Becomes Weak { #when-the-trade }

The model is less compelling when:

- the application starts once and runs for years;
- builds happen extremely frequently but starts rarely;
- processors invalidate almost the entire project after small edits;
- runtime architecture must be highly dynamic;
- generated code becomes excessively large;
- startup is dominated entirely by external systems.

Suppose:

```text
framework startup difference = 300 ms
database migration = 60 s
```

Moving framework work left does not meaningfully change readiness until the migration architecture is addressed.

Likewise, if a code generator adds 20 seconds to every incremental compile to save 100 ms at startup, the trade is poor.

Architecture must be judged with real measurements.

---

## External Startup Work Still Dominates Some Applications { #external-startup-work }

A Kora process can still start slowly if application components perform expensive work.

Examples:

- schema migration;
- large cache preload;
- remote secret retrieval;
- slow DNS;
- slow TLS handshake;
- unavailable database;
- synchronous remote API calls during startup.

Compile-time graph generation cannot eliminate those costs.

It only removes work that the framework itself can know and precompute.

This is useful because it makes remaining startup cost more honest.

If the framework overhead is small, profiling points more directly to actual application dependencies.

---

## Move Migrations Left Too—But Usually Into Deployment { #move-migrations-left }

The same reasoning often applies to database migration.

If a migration blocks every application replica during startup, then:

```text
migration work × replicas
```

may be repeated or serialized awkwardly.

Many organizations instead move migration into a deployment phase:

```text
migration job
→ deploy application
```

That is another form of moving work left.

The general pattern is:

```text
do one-time deterministic work once
not once per replica
```

Kora's compile-time architecture fits the same systems principle.

---

## The Broader Rule: Don't Make Every Replica Solve the Same Problem { #the-broader-rule }

If every replica independently performs work that could have been resolved earlier, the fleet repeats effort.

Examples include:

- architecture discovery;
- static code generation;
- schema preparation;
- asset compilation;
- dependency indexing.

The cloud-native multiplier punishes repeated initialization.

A scalable architecture tries to shift stable work into:

```text
build
image creation
deployment preparation
```

and reserve runtime for state that actually changes at runtime.

Kora applies this aggressively to framework structure.

---

## Clean Build Is an Investment { #clean-build-is }

A clean Kora build can be viewed as constructing a more specialized artifact.

The processor spends time converting general declarations into application-specific implementation.

That specialization has a cost.

But the result is an artifact that needs less interpretation later.

This resembles an investment:

```text
pay once now
→ reduce repeated costs later
```

Whether the investment is good depends on reuse.

In modern backend fleets, reuse is usually high.

---

## Cached Build Is the Amortized Cost { #cached-build-is }

If clean build is the up-front investment, incremental and cached builds represent the amortized development cost.

They answer:

```text
How much of that investment must be repeated after this edit?
```

A mature compile-time framework should make the answer:

```text
only what changed
```

as often as possible.

That is why incremental processing quality is not a secondary implementation detail.

It is part of the framework's economic model.

---

## Startup Is a Per-Instance Tax { #startup-is-a }

Conversely, runtime discovery behaves like a tax on every process.

No matter how many times the same artifact has already started elsewhere, each JVM pays again.

This is tolerable when the tax is tiny.

It becomes expensive when:

```text
instances × starts
```

is large.

Cloud systems multiply per-instance taxes aggressively.

Kora chooses to prepay many of them.

---

## The Same Logic Applies to Warm-Up { #the-same-logic }

Generated direct code can also reduce the amount of framework-specific machinery the JVM must encounter before reaching stable performance.

It does not remove JIT warm-up.

It does not remove class loading.

It does not remove application caches.

But it can reduce the framework portion.

That means moving work left can save not just:

```text
time-to-process-start
```

but part of:

```text
time-to-steady-service
```

This increases the runtime payoff.

---

## The Same Logic Applies to Memory { #the-same-logic-2 }

If runtime metadata is unnecessary because behavior is encoded in generated classes, the process may keep less framework state alive.

Any reduction is paid back continuously:

```text
memory saved
× instances
× runtime hours
```

Now the extra build work is being exchanged not only for startup time but for ongoing fleet footprint.

That can make the trade even more favorable.

---

## The Same Logic Applies to Debugging { #the-same-logic-3 }

Generated source also amortizes debugging knowledge.

Once generated, it can be inspected by:

- every developer;
- every code reviewer;
- every incident responder;
- every AI agent.

The compiler work produced a reusable explanation of framework behavior.

That is difficult to quantify but valuable at scale.

---

## A Useful Mental Model { #a-useful-mental }

Think of a Kora build as partially executing the framework ahead of time.

Not the application business logic.

Not its runtime state.

But the framework's questions about structure.

During compilation, Kora asks:

```text
What components exist?
How are they connected?
What code should adapt this contract?
What wrapper implements this aspect?
What mapper implements this conversion?
```

It writes down the answers as source.

Runtime then uses those answers.

This is the essence of the model.

---

## Runtime Work Should Be About Runtime Facts { #runtime-work-should }

A clean separation is:

### Compile time { #compile-time }

```text
types
contracts
dependencies
routes
mappers
repository shapes
aspects
static architecture
```

### Runtime { #runtime }

```text
requests
connections
database state
configuration values
traffic
failures
timeouts
live topology
```

The less runtime spends re-deriving compile-time facts, the more of runtime is devoted to actual runtime work.

That is a useful design principle beyond Kora.

---

## Why This Matters for Platform Teams { #why-this-matters }

Platform teams optimize repeated patterns.

If every service independently pays startup discovery cost, that cost becomes a fleet property.

If every service instead pays a moderate build-time generation cost, the platform can optimize the build centrally with:

- shared Gradle conventions;
- incremental processing;
- remote caches;
- standardized CI images;
- parallel execution.

The resulting artifacts can then start cheaply everywhere.

This is a strong centralization advantage.

---

## Why This Matters for Application Teams { #why-this-matters-2 }

Application teams receive:

```text
compile-time diagnostics
generated inspectable code
fast application startup
cheap context tests
```

without manually implementing a compile-time architecture.

Their responsibility is mostly to preserve good build hygiene:

- do not `clean` unnecessarily;
- keep Gradle caches healthy;
- use sensible module boundaries;
- avoid processor combinations that defeat incremental builds;
- measure regressions.

The framework and build toolchain do the rest.

---

## Why This Matters for Operations { #why-this-matters-3 }

Operations teams receive artifacts that have already resolved more of their structure.

That can mean:

- faster readiness;
- less startup variance;
- shorter rollout windows;
- faster replacement;
- cheaper elasticity;
- fewer structural failures after launch.

They do not directly care how annotation processing works.

They care that the cost was paid before the artifact reached them.

This is a useful separation of concerns.

---

## Why This Matters for CI { #why-this-matters-4 }

CI is where both sides meet.

CI pays the build cost.

Then it often collects the startup benefit repeatedly in:

- test shards;
- integration environments;
- black-box runs;
- packaging validation.

A well-designed pipeline should exploit this by:

```text
compile once
→ fan out tests
```

rather than rebuilding independently inside every shard.

The more the pipeline reuses the generated artifact, the more favorable Kora's architecture becomes.

---

## The Ideal Pipeline Shape { #the-ideal-pipeline }

A Kora-friendly CI pipeline might conceptually look like:

```text
          source
             ↓
     compile + generate
             ↓
        build artifact
       ↙      ↓       ↘
unit tests  integration  static checks
             ↓
        black-box tests
             ↓
          container
             ↓
           deploy
```

The expensive structural compiler work is centralized near the top.

Everything below consumes the resolved artifact.

This maximizes reuse.

---

## Don't Recompile Per Environment { #don-t-recompile }

An anti-pattern would be:

```text
build staging artifact
build canary artifact
build production artifact
```

from the same commit with environment-specific source generation.

That repeats compile-time work and weakens artifact reproducibility.

Prefer runtime configuration for environment values while keeping structural architecture fixed.

Then:

```text
one build
→ many environments
```

preserves the compile-time payoff.

---

## Startup Saved Per Deployment Is Repeated Forever { #startup-saved-per }

One of the strongest arguments for moving work left is temporal.

A framework's build penalty exists only while that version is built.

Its startup advantage is collected for the lifetime of that version.

Every:

- redeploy;
- restart;
- reschedule;
- scale-out;
- environment creation;

collects the benefit again.

In that sense, generated source behaves like an asset.

The build paid to create it.

The organization keeps reusing it.

---

## The Compounding Effect Across Versions { #the-compounding-effect }

Now multiply over releases.

Suppose a service deploys:

```text
3 times/day
250 working days/year
```

That is:

```text
750 releases/year
```

At 20 replicas per release:

```text
15,000 deployment starts/year
```

A one-second startup saving becomes:

```text
15,000 instance-seconds/year
```

for deployments alone.

Add autoscaling, CI, restarts, and staging.

The extra compile work occurs on roughly:

```text
750 builds
```

or fewer if one build feeds several promotions.

The frequency ratio is the story.

---

## Build-Time Cost Is Front-Loaded { #build-time-cost }

The entire architecture can be summarized economically as:

```text
Kora:
front-load more deterministic framework work

runtime-heavy model:
defer more framework work until process execution
```

Front-loaded cost has several useful properties:

- easier to cache;
- easier to parallelize;
- easier to fail early;
- reused by many instances;
- outside the availability critical path.

Deferred runtime cost has one major advantage:

- more dynamic flexibility.

Kora chooses front-loading because it targets statically packaged production services.

---

## This Is a Compiler Philosophy { #this-is-a }

Kora is often described as a backend framework, but this trade makes it partly a compiler project.

Its job is not merely to provide runtime APIs.

It transforms:

```text
high-level application declarations
```

into:

```text
explicit executable infrastructure
```

That transformation is the source of several Kora properties:

- compile-time DI;
- generated repositories;
- generated handlers;
- generated aspects;
- transparency;
- fast startup;
- low runtime machinery.

These are not independent features.

They are consequences of the same compiler-oriented architecture.

---

## The Trade Is Architectural, Not a Benchmark Trick { #the-trade-is-2 }

It would be easy to frame the strategy narrowly:

```text
move work to build
so startup benchmark looks better
```

That misses the point.

Moving work left changes:

```text
when errors appear
where architecture is represented
what runtime must remember
how many times work repeats
what can be cached
what developers can inspect
how quickly instances become useful
```

Startup is only the most visible outcome.

The deeper benefit is lifecycle efficiency.

---

## Practical Guidance: How to Measure the Trade { #practical-guidance-how }

For a real service, collect four measurements.

### 1. Clean artifact build { #1-clean-artifact }

Measure from zero:

```text
./gradlew clean <artifact-task>
```

Use controlled settings.

Record:

- total time;
- Java/Kotlin compile time;
- processor/KSP time;
- generated output size.

### 2. Incremental local build { #2-incremental-local }

Make representative changes:

```text
method body change
component dependency change
repository change
controller signature change
```

Measure each separately.

### 3. Cached CI build { #3-cached-ci }

Measure realistic cache behavior:

```text
dependency cache
build cache
configuration cache
remote cache
```

### 4. Startup/readiness { #4-startup-readiness }

Measure:

```text
process start → readiness
```

under realistic CPU and memory limits.

Then apply frequencies.

Without frequencies, the comparison is incomplete.

---

## Include Failure Feedback in the Measurement { #include-failure-feedback }

Also measure how quickly invalid changes fail.

Examples:

```text
missing component
ambiguous dependency
invalid repository contract
broken mapper
invalid aspect target
```

Record:

```text
time from edit → actionable failure
```

This is often more relevant than successful build time.

A framework that catches invalid architecture during compile may save entire runtime attempts.

---

## Include Full Developer Loop { #include-full-developer }

Finally measure:

```text
edit → green test
```

This is the strongest developer metric.

It includes:

- incremental processing;
- compilation;
- context startup;
- test execution.

If Kora's extra processor work is more than compensated by faster startup and precise failures, the architecture is delivering on its intended trade.

If not, that is a build-performance problem worth fixing.

---

## Do Not Use `clean` in Normal Development { #do-not-use }

One practical conclusion follows directly from this architecture.

Do not make `clean` part of routine developer commands unless necessary.

For example, avoid workflows like:

```bash
./gradlew clean test
```

on every iteration.

Prefer:

```bash
./gradlew test
```

and let Gradle decide what changed.

A compile-time framework gets much of its developer ergonomics from incremental reuse.

Destroying outputs before every build removes that advantage.

Use clean builds deliberately, not habitually.

---

## Preserve the Gradle Daemon { #preserve-the-gradle }

Similarly, a warm Gradle daemon avoids repeatedly paying JVM and build-tool initialization overhead.

For CI reproducibility benchmarks you may disable it.

For local development, doing so usually makes little sense.

The goal is not to simulate a sterile benchmark environment.

The goal is the fastest correct feedback loop.

---

## Use Build Cache Where It Fits { #use-build-cache }

If a large organization uses Kora across many repositories or modules, build caching can be strategically valuable.

Generated and compiled outputs are exactly the kind of deterministic artifacts that can benefit from reuse when task configuration supports it.

A platform team should track cache hit rates rather than merely enabling the feature and assuming it works.

Poor cache keys or unstable inputs can erase the benefit.

---

## Avoid Accidental Processor Invalidation { #avoid-accidental-processor }

Build performance can also be damaged by source structure.

Broad shared modules and frequently changing public APIs can cause large invalidation waves.

Good modularity helps:

```text
stable interfaces
localized implementation
clear dependencies
```

This is good architecture independently of Kora.

Compile-time generation simply makes the cost of broad coupling more visible.

---

## Keep Generated Source Inspectable but Ephemeral { #keep-generated-source }

Generated source should usually remain a build product, not hand-maintained application code.

Developers should be able to inspect it when needed.

But it should be regenerated from authoritative source declarations.

Conceptually:

```text
application source = source of truth
generated source = compiler product
```

This preserves reproducibility and prevents divergence.

---

## Treat Processor Performance as a Framework Regression Metric { #treat-processor-performance }

If Kora is a platform standard, processor timing should be monitored across upgrades.

Track representative applications.

A new release that improves runtime by 3% but doubles incremental build time may not be a net win.

Likewise, a processor optimization that reduces build latency across thousands of developers can have enormous organizational value even if runtime behavior is unchanged.

Compile-time architecture makes compiler performance part of framework quality.

---

## The Trade Changes With Team Scale { #the-trade-changes }

For a small team with one service:

```text
build performance
```

may dominate perception.

For a platform with hundreds of services:

```text
runtime startup × fleet
```

becomes much larger.

For an organization with thousands of developers:

```text
incremental build × developers
```

becomes large again.

There is no universal weighting.

The correct decision depends on organizational scale on both sides.

This is why platform teams need measurements rather than ideology.

---

## The Best Kora Outcome Is Both Fast Build and Fast Runtime { #the-best-kora }

It is important not to turn the trade-off into a false choice.

The long-term goal should be:

```text
fast clean build
fast incremental build
fast startup
fast runtime
```

Moving work left explains why some build cost exists.

It does not justify unnecessary build inefficiency.

Annotation processors can be optimized.

KSP processing can be incremental.

Generated output can be minimized.

Gradle caches can be exploited.

The compiler architecture should continuously improve.

The trade explains *where the work belongs*, not why the work should be slow.

---

## Moving Work Left Is About Paying at the Cheapest Time { #moving-work-left-3 }

The deepest way to describe Kora's choice is:

> Perform work at the cheapest phase where all required information is already available.

If the compiler already knows the application structure, solving it again at runtime is redundant.

If the information is genuinely runtime-dependent, compilation cannot replace it.

The architecture should place each problem at the earliest valid phase.

For Kora:

```text
application topology
→ compile time

live infrastructure state
→ runtime
```

That boundary is both a performance decision and a software-design decision.

---

## The Result: Runtime Does Less Framework Work { #the-result-runtime }

After the artifact is built, Kora's runtime can focus more directly on:

- initializing real components;
- binding servers;
- connecting to infrastructure;
- processing requests;
- executing business logic;
- emitting telemetry;
- handling failures.

It spends less time asking:

```text
What is this application?
```

because the build already answered that question.

That is why startup is fast.

---

## The Result: Builds Become More Semantically Valuable { #the-result-builds }

Conversely, the build does more than turn `.java` or `.kt` files into bytecode.

It also:

- validates architecture;
- generates implementations;
- materializes dependency wiring;
- produces readable framework code.

A successful build therefore proves more about the application than a build that postpones those questions until startup.

This makes build time more valuable work, not merely more work.

---

## The Result: One Artifact Can Serve Many Runtime Events { #the-result-one }

The generated artifact can be reused across:

```text
local starts
CI
integration tests
staging
canary
production
autoscaling
restarts
```

Each event benefits from work already performed.

This reuse is where the architecture pays off.

---

## The Core Equation Revisited { #the-core-equation }

The whole article can be reduced to:

```text
compile-time cost
vs
runtime saving × runtime repetition
```

or:

```text
B
vs
S × N
```

But the real equation is richer:

```text
Build-side cost:
    annotation processing
  + KSP
  + generated source compilation
  + invalidation

Runtime-side benefit:
    faster startup
  + less runtime discovery
  + earlier failures
  + thinner runtime machinery
  + possibly lower memory/CPU
  + easier debugging
```

And the multipliers differ.

That is why Kora chooses to move work left.

---

## Conclusion { #conclusion }

Startup time and build time should not be evaluated as isolated benchmark categories.

They are two points in the lifecycle of the same application.

A framework can perform structural work while producing the artifact, or it can postpone that work until every process starts. Kora deliberately chooses to front-load much of it.

Java annotation processors and Kotlin KSP analyze application declarations during compilation. Dependency wiring is resolved. Structural errors can fail early. HTTP adapters, repositories, mappers,
aspects, configuration implementations, and graph code can be generated as readable source. The build becomes somewhat more expensive because it is producing a more specialized and more fully resolved
artifact.

Runtime then receives the benefit.

There is less framework structure to discover. The application graph is already known. Generated code is already compiled. Startup can focus on initializing real runtime resources rather than
rebuilding architectural knowledge.

The trade is especially favorable because the two costs have different multiplicities.

A build may happen once.

The resulting artifact may start dozens, hundreds, or thousands of times across CI, staging, deployment replicas, autoscaling, restarts, multiple regions, spot recovery, and developer environments.

That gives the central equation:

```text
extra build work once
<
startup work saved N times
```

But the build side still matters. That is why clean build and cached/incremental build must be treated separately. Clean builds reveal the full cost of code generation. Incremental compilation, Gradle
caches, the daemon, multi-module boundaries, and incremental annotation/KSP processing determine whether ordinary development remains fast. A compile-time architecture succeeds only when the build
toolchain avoids repeating unchanged work.

This is also why `clean` is the wrong default lens for developer experience. A compile-time framework is designed to cooperate with incremental computation. Destroying all outputs before every edit
intentionally disables one of the main mechanisms that makes the trade economical.

The broader architectural principle is simple:

```text
Do deterministic work once,
at the earliest phase where it can be proven,
then reuse the result.
```

Kora applies that principle to framework structure.

It moves architecture from runtime interpretation into compile-time generation.

It exchanges some build work for less startup work, earlier diagnostics, explicit generated code, and a smaller amount of runtime machinery.

For one local launch, the difference may look like a benchmark detail.

Across every build, every test context, every deployment, every replica, every restart, and every region, it becomes a lifecycle optimization.

That is why Kora moves work left.
