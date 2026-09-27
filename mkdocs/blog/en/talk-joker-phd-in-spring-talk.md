# The Price of a “PhD in Spring”: What Kora Tries to Remove From the JVM Framework Experience

**October 14, 2024**

https://www.youtube.com/watch?v=Ksvcq-PRfX4

There is a familiar way to describe mature frameworks: their complexity is treated as depth, their long history as accumulated wisdom, and the years required to master their edge cases as valuable
expertise. This talk deliberately challenges that assumption. Its central question is not whether Spring is powerful, popular, productive, or battle-tested—it clearly is—but whether the amount of
framework-specific knowledge required to use it confidently should itself be considered an engineering cost.

The speaker calls that cost a **“PhD in Spring.”** The phrase is intentionally provocative, but the idea behind it is concrete. A developer working in the ecosystem is expected to understand
constructor versus field injection, bean naming, qualifiers, lifecycle callbacks, proxy semantics, `@Transactional`, aspect ordering, configuration precedence, relaxed binding, test context caching,
slices, auto-configuration, startup optimization, native-image trade-offs, and many other details that are not necessarily visible from application code itself. None of these topics is individually
impossible to learn. The argument of the talk is that their cumulative effect becomes significant when multiplied by developers, teams, services, CI pipelines, production fleets, and years of
maintenance.

Kora appears throughout the presentation as a counterexample. It is not presented as “Spring but faster,” and the speaker does not claim that every Spring application should be rewritten. The more
fundamental idea is that many framework concerns can be moved from runtime into compilation and represented as readable generated source rather than hidden runtime machinery. The resulting
architecture tries to reduce both operational overhead and the amount of framework context developers must hold in their heads.

This presentation belongs to the **Kora 1.x era**, before the current Kora 2.0 generation. That historical framing matters. The version discussed in the talk was already much more mature than pre-1.0
Kora, but Kora 2 has since simplified and consolidated the model further: synchronous Java/Kotlin application contracts, virtual-thread-first execution, removal of reactive and `suspend` framework
contracts, refined compile-time graph processing, broader documentation, and a more coherent production stack. The principles discussed here—compile-time DI, explicit composition, thin abstractions,
generated source, direct SQL, and minimizing framework-specific cognitive load—remain central.

The talk itself is intentionally combative. Some slide titles use phrases such as “Spring bullshit,” “we cry,” or “victim of optimization.” Those are rhetorical devices from the presentation, not
neutral terminology. A useful companion article should preserve the technical substance while separating rhetoric from evidence. The strongest parts of the talk are not the insults; they are the
measurements and the repeated question: **what exactly does the abstraction cost, and who pays for it?**

## The Cost Begins With the Simplest Framework Features

Dependency injection is the first example because it is supposed to be the easiest feature to understand. In modern Spring code, constructor injection is widely considered the preferred pattern, but
the framework historically supports several other approaches: field injection, setter injection, XML configuration, bean names, qualifiers, and related variations. A team that wants one preferred
style therefore has to enforce that preference itself.

The gap is easy to visualize:

```text
What the framework allows
├── constructor injection
├── field injection
├── setter injection
├── XML
├── bean-name matching
├── qualifiers
└── historical variations

What many teams actually want
└── constructor injection
```

That gap creates organizational work. Senior developers review code for undesirable patterns, style guides explain what not to use, linters are introduced, and new engineers may copy older examples
from the internet. The framework provides freedom, but the team pays to constrain it.

Kora deliberately chooses a narrower model. Constructor injection is the model. Typed tags are used instead of depending on arbitrary string identity. The intention is not minimalism for its own sake;
it is to make the preferred pattern the framework's normal pattern so that the team does not have to repeatedly negotiate the same decision.

This is a recurring idea in the talk:

> **A framework can reduce cognitive load not only by adding capabilities, but by refusing to expose choices that teams do not actually want.**

## Runtime Feedback Is More Expensive Than Compiler Feedback

The talk then shows another seemingly minor example: factory methods that accidentally create a collision because of naming or graph composition rules. The important detail is not the specific
collision; it is when the developer discovers it.

In a runtime-oriented container, the feedback loop may be:

```text
write code
   ↓
compile
   ↓
package
   ↓
start application
   ↓
build context
   ↓
discover collision
```

Kora tries to move this class of structural error into compilation:

```text
write code
   ↓
compile application graph
   ↓
collision / missing dependency
   ↓
compiler error
```

That shift is larger than it looks. It means the framework can use the compiler as part of the correctness model instead of relying on the developer to remember what combinations are safe.

The speaker repeatedly treats this as a way to unload framework-specific knowledge from developers. If the graph is invalid, the build should fail. If a dependency is missing, the compiler should say
so. The application should not need to start before the framework can tell the team that its structure is impossible.

## Lifecycle Shows How Quickly “Simple” Behavior Becomes Secret Knowledge

Lifecycle is used as the next example because it looks simple until multiple framework mechanisms overlap. A component may inherit initialization methods, use `@PostConstruct`, implement lifecycle
interfaces, participate in AOP, and be wrapped in a proxy. At that point, even an experienced Spring developer may not immediately know which initialization method runs first, whether an aspect
applies to a particular callback, or which object—the target or the proxy—is actually executing a method.

The speaker calls this “secret knowledge”: behavior that cannot be derived from the local code and must instead be remembered from documentation, prior incidents, or years of experience.

Kora's answer is to generate readable source. If an aspect creates a subclass, developers can open that subclass. If a parent lifecycle method is relevant, ordinary Java/Kotlin semantics such as
`super` can be used. The framework tries to make the actual execution structure inspectable.

The intended debugging workflow becomes:

```text
Question:
"Does this aspect apply here?"

        ↓

Open generated class

        ↓

Read actual implementation

        ↓

Know the answer
```

rather than:

```text
Question:
"Does this aspect apply here?"

        ↓

remember lifecycle rules
        ↓
remember proxy rules
        ↓
remember ordering rules
        ↓
remember version behavior
        ↓
search docs / issue / article
```

The difference is philosophical: **inspect instead of memorize**.

## Generated Source Is an Executable Explanation

Kora's generated code is often discussed in performance terms, but this talk places equal emphasis on transparency. Dependency graphs, repositories, JSON mappers, AOP wrappers, and HTTP adapters are
generated as normal Java or Kotlin source.

The contrast is:

```text
Runtime-oriented abstraction

source
  ↓
annotations
  ↓
framework internals
  ↓
proxy / reflection / metadata
  ↓
actual behavior
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
actual behavior
```

The generated layer becomes an executable explanation of what the framework decided to do.

That has two consequences. First, the application runtime contains less dynamic machinery. Second, the framework needs less “folklore” because a developer can navigate to the generated implementation
in the IDE.

Modern Kora 2 continues this approach. The framework has evolved substantially since this presentation, but generated human-readable source remains part of its architectural identity.

## Spring Configuration: Flexibility Becomes a Precedence Problem

The configuration slides make one of the strongest cognitive-load arguments in the entire talk. Spring Boot supports a large number of property sources and a defined precedence order. The slide lists
**15 configuration sources**, including default properties, `@PropertySource`, configuration data files, random values, environment variables, Java system properties, JNDI attributes, servlet
initialization parameters, `SPRING_APPLICATION_JSON`, command-line arguments, test properties, `@DynamicPropertySource`, `@TestPropertySource`, and devtools-specific global settings.

On top of that, configuration files themselves can come from several locations and be merged according to ordering rules.

The talk compresses the situation into this picture:

```text
15 possible configuration sources
          ↓
4 categories / locations of config files
          ↓
5 relaxed-binding name variants
          ↓
final value
```

The relaxed-binding slide makes the issue tangible. A property such as `hostName` can be represented in several forms:

```text
hostName
hostname
host_name
host-name
HOST_NAME
```

All can potentially bind to the same target.

This flexibility is useful in heterogeneous deployment environments. The speaker's criticism is not that relaxed binding is irrational. It is that the developer must know that all these sources and
aliases exist when debugging why a value differs between environments.

The core question becomes:

> Where did this configuration value actually come from?

If that answer depends on a precedence system spread across numerous potential sources, the framework has shifted a significant amount of complexity into operational troubleshooting.

Kora's configuration model prefers typed interfaces and explicit contracts, with required properties represented directly and defaults expressed through normal language constructs where possible. The
goal is not “zero configuration flexibility.” It is a smaller and more obvious resolution model.

## Configuration Complexity Is Also a Deployment Risk

The talk goes beyond developer convenience. A value can come from the environment, system properties, command-line arguments, test configuration, configuration files inside or outside the artifact,
profile-specific files, or other sources. That means the artifact alone does not necessarily describe the configuration that will govern production behavior.

Operationally, the full application state is closer to:

```text
artifact
+ environment
+ system properties
+ command-line arguments
+ profile configuration
+ external files
+ test/deployment overrides
= effective configuration
```

This is common in cloud applications and is not inherently bad. The speaker's concern is that the number of supported mechanisms makes the resolution path difficult to reason about. A feature designed
to maximize compatibility and convenience becomes another knowledge surface developers must learn.

## Tests Are Where Framework Complexity Multiplies

The additional testing slides make this part of the argument much stronger. One slide simply says, in effect, “Spring tests: we cry,” surrounded by references to talks about Spring Test, test-context
caching, JPA testing antipatterns, and Spring Boot Test complexity. The joke is not the important part. The important part is the next slide, which lists the questions developers may have to answer
when writing modular Spring tests:

```text
Reuse the context or not?
Use a context with stubs or not?
Override components or not?
Cache the context or not?
How and when should it be cached?
Roll back transactions or not?
Provide configuration / profiles or not?
```

Next to this list is a long column of specialized test annotations: `@DataJpaTest`, `@WebMvcTest`, `@JsonTest`, `@JdbcTest`, `@DataRedisTest`, `@SpringBootTest`, `@MockBean`, `@Transactional`,
`@DirtiesContext`, `@TestPropertySource`, and many others.

Spring's test ecosystem is extremely capable, but capability and simplicity are not the same thing. The test framework can become its own programming model.

The cognitive path may look like:

```text
What do I want to test?
      ↓
Which test slice?
      ↓
Which context?
      ↓
Which mocks?
      ↓
Will the context be cached?
      ↓
Do I need @DirtiesContext?
      ↓
What happens to transactions?
      ↓
Which properties are active?
```

The speaker's criticism is that this is a lot of framework thinking before any application assertion is written.

Kora's testing model aims for a simpler relationship: the test graph is derived from the components explicitly needed by the test and their dependencies. Replacements, stubs, and configuration are
explicit. In simplified form:

```text
What the test declares
        =
what the test graph contains
```

The framework can start a small graph quickly enough that aggressive context caching is less necessary as a default optimization. If reuse is desired, it can be requested deliberately.

This is important because testing is performed continuously. A framework rule that costs one minute to learn once is cheap. A testing model that requires repeated reasoning across thousands of tests
becomes expensive.

## Context Caching Is a Symptom of Startup Cost

The talk's testing argument connects directly to startup performance. Spring's sophisticated test-context caching exists for a reason: starting an application context can be expensive. Caching is
therefore an optimization that makes large test suites practical.

But caching introduces its own complexity:

```text
slow context startup
      ↓
cache context
      ↓
define reuse rules
      ↓
invalidate selectively
      ↓
understand state leakage
      ↓
learn more framework rules
```

Kora tries to attack the problem earlier in the chain. If building the graph is cheap, each test can receive a fresh graph more often without forcing developers to optimize context reuse.

The key idea is architectural:

> A good optimization is sometimes not a better cache, but making the uncached operation cheaper.

## The Aspect Section: Correctness Before Performance

The aspect portion of the talk begins with a production-style example rather than a benchmark. A service method has multiple cross-cutting annotations—for example validation, caching, retry, metrics,
logging, or other policies. The developer has two basic questions:

```text
Do all of these actually execute?
In what order?
```

The talk shows why these questions can be non-trivial. Different Spring modules do not always support identical method signatures or return types. A caching annotation can exist in code while the
necessary module is absent. An expression inside an annotation may only fail once the aspect actually executes. A business-level test may pass even if the cache behavior never ran.

This is the origin of one of the talk's more memorable lines:

> If it works, that does not necessarily mean every framework feature around it is working.

The second problem is ordering. Aspect order may depend on implementation-defined priority, shared default values, or global configuration. The order seen in source annotations may not be the order
actually executed.

## Spring Aspects: the Speaker's Summary

One of the new slides provides a concise summary of the speaker's argument about Spring aspects:

1. a “glass ceiling” of fixed overhead;
2. a negative cumulative effect;
3. non-obvious call order;
4. limited ability to vary order flexibly;
5. unpleasant call chains and debugging.

The slide also concedes one advantage:

> writing custom aspects in Spring is easier.

That concession is important. The talk does not claim Kora wins every ergonomics comparison. Runtime proxy systems can make custom interception extremely flexible because they can apply behavior
dynamically without compile-time generation.

The trade is therefore more balanced:

```text
Spring AOP
+ easy dynamic customization
+ enormous ecosystem
- runtime proxy overhead
- ordering can be indirect
- more framework call frames

Kora AOP
+ generated direct calls
+ explicit order
+ readable source
+ low runtime overhead
- compile-time model
- less dynamic
```

That is a more useful comparison than simply declaring one model universally superior.

## Measuring the Fixed Cost of Aspects

The presentation then benchmarks the aspect mechanism itself. Three variants are compared:

```text
Java baseline
    handwritten before/after calls

Kora
    compile-time generated aspect wrapper

Spring
    runtime proxy / interceptor path
```

The first microbenchmark deliberately gives the aspects almost no useful work. The point is to expose framework overhead.

The slide reports:

| Case      |                Java |                Kora |          Spring |
|-----------|--------------------:|--------------------:|----------------:|
| 1 aspect  | 1,526,304,670 ops/s | 1,305,622,052 ops/s | 1,589,510 ops/s |
| 5 aspects | 1,533,758,344 ops/s | 1,305,990,807 ops/s |   314,724 ops/s |

The slide's headline says Kora is approximately **4,149× faster than Spring for five empty aspects**.

A simple representation:

```text
5 empty aspects
operations / second

Java    ~1.534B  ██████████████████████████████
Kora    ~1.306B  █████████████████████████
Spring  ~0.315M  ▏
```

This does **not** mean a Kora service is 4,149× faster than a Spring service. The benchmark intentionally removes useful work so that the fixed machinery becomes the result. The number describes the
cost of this specific mechanism under an artificial microbenchmark.

That limitation is not a weakness of the measurement; it is the purpose of the measurement. Microbenchmarks isolate a particular mechanism.

The useful conclusion is:

```text
Spring proxy path has measurable fixed overhead.

Kora-generated direct calls are much closer
to handwritten Java when the intercepted work is tiny.
```

Whether that matters in a production system depends on how often such calls occur and how much useful work surrounds them.

## Why Empty Aspects Are Not Completely Artificial

The speaker answers the obvious objection: production aspects normally do something. A logging aspect, however, may simply check a log level and then return. Some metrics, cache, or validation paths
can also perform very little work in certain cases.

When useful work is small, fixed proxy cost becomes a larger percentage of the total operation.

The talk then increases the amount of work inside the aspect. As expected, the relative difference shrinks. Once each aspect performs significant computation, framework overhead is diluted by business
work.

The relationship is:

```text
almost no useful work
      → infrastructure dominates

moderate useful work
      → overhead still visible

large useful work
      → framework cost is smaller percentage
```

The speaker's production argument is that service methods are often nested and repeatedly intercepted, so small costs can accumulate across call chains.

## Stack Traces and Debugging Are Part of the Same Cost

Performance is only half of the AOP argument. Runtime proxy/interceptor chains also appear in stack traces and debuggers.

A Spring call may look conceptually like:

```text
business method
      ↑
proxy
      ↑
interceptor
      ↑
AOP dispatcher
      ↑
framework invocation
      ↑
...
```

A generated Kora path may look more like:

```text
generated wrapper
      ↓
business method
```

The exact stack depends on the integration, but the principle is straightforward: fewer runtime abstraction layers produce shorter and more application-oriented traces.

The same design choice therefore affects CPU overhead and debuggability simultaneously.

## Optimization Has Its Own Price

The new “optimization price” slides make the next section much clearer. The speaker's summary is:

1. developers spend a large amount of time on framework optimizations;
2. lazy initialization is not necessarily a real optimization;
3. optimization can require sacrificing functionality;
4. major optimizations are often too costly for teams to adopt broadly;
5. the benefit may not justify the price being paid.

This is the real subject of the optimization section. It is not whether Spring can be made faster. Of course it can. The question is how much additional expertise and maintenance work is required to
reach that state.

## Lazy Initialization Moves Work Rather Than Removing It

Lazy initialization is the speaker's favorite example. It can improve reported startup time by postponing bean creation until the bean is first used.

The objection is operational:

```text
process starts quickly
      ↓
readiness says "ready"
      ↓
production traffic arrives
      ↓
lazy initialization begins
      ↓
first requests pay startup cost
```

If Kubernetes has already replaced the old pod with the new one, the application can experience latency exactly when it is supposed to be taking traffic.

This does not mean lazy initialization is always wrong. The stronger point is that moving work out of the measured startup interval should not automatically be described as eliminating the work.

## Auto-Configuration Optimization Can Become a Manual Dependency Graph

Another slide shows the visual “price” of optimization: a large explicit list of configuration classes and ordering rules. The message is intentionally dramatic, but it illustrates a real trade.

Spring Boot begins with classpath-driven auto-configuration because that is convenient. If startup or footprint becomes a problem, teams may start excluding or explicitly importing only selected
auto-configurations. At that point they have to understand the internal configuration graph they were originally paying the framework to manage automatically.

The lifecycle becomes:

```text
Automatic discovery
      ↓
too much gets initialized
      ↓
optimize startup
      ↓
manually select configurations
      ↓
understand ordering and dependencies
      ↓
maintain optimization layer
```

The optimization can become a second application architecture.

Kora instead starts from explicit module composition. If a module is not connected to the application graph, it is not part of the application. The framework pays for this explicitness up front rather
than requiring a later phase whose goal is to undo automatic behavior.

## The Optimized Startup Benchmark

The speaker builds a more realistic Spring service with multiple controllers, service layers, metrics, health probes, OpenAPI, aspects, and integrations. He then gathers a set of Spring optimization
techniques from articles and conference talks and applies the subset he considers practical.

The benchmark environment shown on the slides uses a Docker container with **1 CPU and 1 GB of memory**, running on a 2019 MacBook Pro with an Intel i7-9750H. The figures are averaged over five runs.

The reported startup times are:

| Variant          | Startup time |
|------------------|-------------:|
| **Kora**         |   **4.89 s** |
| Optimized Spring |  **21.13 s** |
| Spring           |  **26.53 s** |

The slide summarizes this as Kora starting roughly **5.4× faster than default Spring** and **4.3× faster than the optimized Spring version** in this benchmark.

```text
Startup in Docker
1 CPU / 1 GB
lower is better

Kora              █████                         4.89 s
Spring optimized  █████████████████████        21.13 s
Spring            ███████████████████████████  26.53 s
```

These ratios are workload- and environment-specific. They should not be read as universal Spring/Kora startup laws. Their role in the presentation is to show that a large amount of optimization work
did not erase the architectural difference in this particular service.

## Optimization Can Move Cost Into Build Time

Kora performs significant compile-time processing, so the obvious next question is whether faster runtime simply means slower builds.

The clean-build benchmark without caches, daemons, or other accelerators reports:

| Variant          | Clean build |
|------------------|------------:|
| Spring           |  **9.33 s** |
| Kora             | **11.63 s** |
| Optimized Spring | **18.69 s** |

```text
Clean build
lower is better

Spring            █████████                 9.33 s
Kora              ████████████             11.63 s
Spring optimized  ███████████████████      18.69 s
```

This result is important because it shows the cost transfer clearly. Kora is not free. Annotation processing and code generation consume build time.

The optimized Spring application becomes slower to build because some of its optimization machinery moves additional work into packaging and build steps.

A second slide shows a more normal development build with caches, daemons, incremental work, and related optimizations enabled:

| Variant          | Development build |
|------------------|------------------:|
| Spring           |        **1.89 s** |
| Kora             |        **2.51 s** |
| Optimized Spring |        **2.84 s** |

```text
Ordinary development build
lower is better

Spring            ███████████████████       1.89 s
Kora              █████████████████████████ 2.51 s
Spring optimized  ████████████████████████████ 2.84 s
```

This is one of the most balanced measurements in the talk. Kora pays more during compilation, but the difference under normal developer build conditions is not enormous in the presented project.

## Compile-Time Frameworks Do Not Eliminate Work—They Relocate It

The build/start measurements make the architectural trade explicit:

```text
Runtime-heavy approach

less framework work during compile
        ↓
more discovery / proxies / startup work at runtime
```

versus:

```text
Compile-time approach

more analysis and generation during build
        ↓
less discovery and dynamic framework work at runtime
```

Neither architecture abolishes complexity.

The questions are:

- where does the work happen;
- when do errors become visible;
- how often is the work repeated;
- can the resulting implementation be inspected;
- what operational costs remain after deployment?

Kora's bet is that build time is the better place for framework machinery because compilation is controlled by developers and CI, while runtime work is paid during every startup and potentially on
every request.

## The “Spring Configuration” Slide Is a Perfect Example of Cognitive Accumulation

The configuration slide is especially useful because no single item on it looks unreasonable. Environment variables are useful. System properties are useful. CLI arguments are useful. Test property
sources are useful. Profile-specific files are useful. Relaxed binding is useful.

The problem only appears when they are all combined.

This is the cumulative pattern the talk criticizes:

```text
feature A is useful
feature B is useful
feature C is useful
...
feature N is useful
        ↓
all coexist
        ↓
developer must understand interactions
```

A mature framework becomes difficult not because any one feature is absurd, but because compatibility keeps old and new approaches alive simultaneously.

This is one of the areas where Kora has an inherent advantage as a younger, narrower framework. It can refuse some compatibility layers that Spring cannot remove without breaking enormous ecosystems.

## The Final Spring Summary: Breadth Has Consequences

One of the closing slides summarizes the speaker's Spring critique in seven points:

1. archaic tooling and architectural baggage;
2. many ways to perform the same task;
3. overcomplicated tooling and testing;
4. developers must hold a large amount of context in their heads;
5. time is spent on optimization, workarounds, and “magic”;
6. feedback is not always obvious;
7. recommendations and best practices are not always sufficiently explicit from the framework itself.

The slide uses much harsher wording than a neutral engineering article should, but the trade-off is real. Spring's broad historical compatibility creates a huge capability surface. That surface
produces more choices, more interactions, and more knowledge that teams must manage.

The important comparison is not:

```text
Spring bad
Kora good
```

It is:

```text
Spring
broad historical compatibility
huge ecosystem
many models and extension points
dynamic flexibility
        ↓
larger behavioral surface
```

versus:

```text
Kora
narrower model
compile-time composition
generated source
explicit modules
fewer parallel approaches
        ↓
smaller behavioral surface
```

Different organizations may prefer different trade-offs.

## Kora's Goal Is to Make Optimization the Default Architecture

The strongest part of the Kora argument is not that the framework has a secret startup switch or one unusually fast server implementation. The point is that many of the “optimizations” the speaker
discusses are simply consequences of the normal Kora architecture.

The graph is compiled.

Components are explicit.

AOP is generated.

Serialization is generated.

Repositories are generated.

Modules are opt-in.

There is less runtime discovery to disable later.

This changes who is responsible for optimization:

```text
Spring-style path in the talk

default convenience
      ↓
performance problem
      ↓
expert optimization
      ↓
special configuration
      ↓
maintenance burden
```

versus:

```text
Kora

compile-time model by default
      ↓
runtime already lean
      ↓
developer optimizes business logic
```

That is a much stronger argument than any individual benchmark.

## Kora Is Not Presented as a Universal Replacement

Despite the talk's aggressive style, the conclusion is more measured than the middle sections. The speaker explicitly says that if Spring solves a team's problems and the team is satisfied, that is a
valid choice.

The intention is not to establish a new dogma.

It is to challenge the assumption that Spring itself is the dogma.

A framework is a technology. It has strengths, trade-offs, historical constraints, and operational costs. Teams should be willing to evaluate alternatives when those costs become significant.

This applies equally to Kora. Kora's narrower model is useful precisely because it is not trying to be everything to everyone.

## AspectJ Is an Important Caveat

In the Q&A, someone asks whether compile-time AspectJ weaving would change the aspect benchmark. The speaker acknowledges that it could. Compile-time weaving is a different mechanism from the
conventional runtime proxy/interceptor path being tested.

That distinction matters. The benchmark is not “every possible way to implement AOP in the Spring ecosystem versus Kora.” It is the tested Spring AOP path used by the relevant modules versus Kora's
generated source and handwritten Java.

This caveat improves the technical interpretation of the results.

## No Special IDE Plugin Is Part of the Design

The Q&A also asks about IDE support. The answer is that Kora deliberately tries not to require a framework-specific plugin for basic understanding.

If dependencies are represented as types, ordinary navigation works.

If code is generated as source, the IDE can open it.

If the application graph is compiled, compiler diagnostics work.

The toolchain remains largely the normal Java/Kotlin toolchain.

That is another expression of the same philosophy:

> Prefer language and compiler semantics over a parallel framework semantic layer.

## Kotlin Uses the Same Architectural Model

The speaker confirms Kotlin support as a first-class part of Kora. The framework is not designed around a Java-only runtime container with Kotlin treated merely as alternate syntax.

Compile-time generation means Kotlin integration quality matters heavily because nullability, default arguments, and type information affect generated code directly.

The current Kora 2 generation has continued to develop this Java/Kotlin symmetry.

## Historical Context: This Is Kora 1.x, Not Kora 2

The version discussed in the presentation belongs to the Kora 1.x generation. Modern Kora 2 has pushed several of these ideas further rather than abandoning them.

A simplified evolution is:

```text
Early Kora
    ↓
prove compile-time DI
and generated-source architecture

Kora 1.x
    ↓
expand modules
mature AOP / testing / telemetry / OpenAPI
grow production adoption

Kora 2.x
    ↓
simplify again
synchronous application contracts
virtual-thread-first execution
remove reactive / suspend framework APIs
refine graph processing
broaden docs and production guidance
```

The 2.0 generation is therefore an even stronger expression of the talk's “reduce the number of models” thesis. Instead of accumulating every execution style indefinitely, Kora removed several
framework contracts and standardized around a simpler synchronous model.

## How to Interpret the Benchmarks Correctly

The talk contains deliberately dramatic numbers, especially around AOP. The best way to interpret them is to distinguish three levels:

```text
Microbenchmark
→ isolates mechanism overhead

Application benchmark
→ mechanism + application work

Production system
→ application + I/O + DB + network
   + queues + scaling + operational behavior
```

A 4,149× gap in an empty-aspect microbenchmark does not imply a 4,149× production throughput advantage.

But dismissing the number because it is synthetic would also miss the point. It demonstrates that the mechanism itself has a significant fixed cost under the tested path.

Likewise, a 4.89-second Kora startup versus 26.53-second Spring startup in one Docker benchmark does not imply every Kora service starts 5.4× faster than every Spring service. It demonstrates how the
two architectures behaved in that specific service, environment, and configuration.

The scientifically useful reading is:

> The benchmark identifies where overhead exists. Production significance depends on workload frequency and scale.

## Framework Economics: Small Costs Multiplied by the Organization

The deepest argument in the presentation is organizational rather than microarchitectural.

Twenty minutes spent learning an optimization is trivial.

Twenty minutes multiplied by hundreds of developers and many services is not.

A few microseconds of proxy overhead are trivial.

The same overhead on billions of calls may not be.

One confusing test annotation is trivial.

An entire organization maintaining thousands of tests around complex context rules is not.

The speaker is effectively proposing this model:

```text
small framework cost
        ×
developers
        ×
services
        ×
tests
        ×
builds
        ×
deployments
        ×
requests
        ×
years
        =
platform-scale cost
```

That is the economic meaning of the “PhD in Spring” metaphor.

The price is accumulated engineering attention.

## Conclusion: The Real Problem Is the Permanent Trade Between Capability and Consequence

The strongest closing slide in the talk is not a benchmark. It is the summary titled, bluntly, “Spring bullshit,” followed by a bingo card of framework concepts and a sentence that captures the
speaker's entire argument: **Spring becomes an endless balancing act between functionality and the consequences of that functionality.**

That framing matters because the presentation is not really about one bad annotation, one slow proxy, one confusing test slice, or one expensive startup path. The speaker's criticism is cumulative.
Spring's strengths are inseparable from its history: an enormous ecosystem, long-term compatibility, broad auto-configuration, multiple programming models, extensive testing infrastructure, and a vast
number of integrations. Every one of those strengths exists for a reason, but every one also expands the behavioral surface developers must understand.

The final slide condenses that accumulated cost into seven complaints:

1. **Archaic tooling and architectural baggage.** Old decisions remain visible because compatibility matters, so modern applications inherit concepts that originated under very different JVM and
   deployment assumptions.
2. **Many ways to perform the same task.** Flexibility becomes a governance problem when teams must decide which supported mechanisms are still acceptable and which are merely historical.
3. **Overcomplicated tools and testing.** The framework does not merely help test the application; teams may need substantial expertise in the testing framework itself.
4. **A large amount of context must be held in developers' heads.** Lifecycle, proxies, property precedence, test contexts, aspect order, auto-configuration, profiles, and optimization rules become a
   parallel body of knowledge.
5. **Time is lost on optimization, workarounds, and “magic.”** When the normal framework path becomes expensive, developers begin spending engineering time learning how to partially undo or constrain
   it.
6. **Feedback is not always obvious or immediate.** Some structural problems appear only when the context starts, a particular aspect runs, or a specific configuration combination is activated.
7. **Recommended practices are not always obvious from the framework itself.** Teams frequently depend on conference talks, articles, Stack Overflow discussions, institutional knowledge, and senior
   developers to determine the preferred path.

Taken separately, none of these points proves that Spring is a poor framework. Taken together, they describe the cost of a framework that has optimized for breadth, compatibility, and flexibility for
more than two decades.

The “bingo” metaphor is therefore more than a joke. It illustrates how framework complexity accumulates horizontally. A team starts with dependency injection, then adds transactions, caching,
security, configuration, test slices, metrics, auto-configuration, lifecycle callbacks, expression languages, custom qualifiers, optimization rules, and increasingly specialized annotations. Each
square is useful. The problem appears when enough squares are active that developers spend more time reasoning about their interactions than about the business operation the framework was supposed to
simplify.

A simplified version of the slide's argument looks like this:

```text
More framework capability
        ↓
more conventions
        ↓
more interactions
        ↓
more edge cases
        ↓
more expert knowledge
        ↓
more optimization / workarounds
        ↓
more framework-specific cognitive load
```

This is the loop the speaker calls an “eternal bingo”: teams continuously balance new functionality against the secondary complexity it introduces.

The benchmark sections of the talk then give this philosophical argument something measurable. Spring configuration can involve **15 property sources**, several configuration-file locations, and
multiple relaxed-binding variants. Spring tests can require decisions about context reuse, stubs, overrides, caching, transaction rollback, active configuration, and a large collection of specialized
annotations. Aspect composition can be correct yet non-obvious, and the runtime proxy mechanism has measurable fixed overhead. Startup can be improved, but the optimization itself may introduce
additional build steps, configuration selection, ordering knowledge, and maintenance work.

Kora chooses a different trade. It compiles the application graph. It generates aspect wrappers. It generates JSON readers and writers. It generates repositories. It keeps SQL visible. It uses typed
configuration. It makes modules explicit. It accepts additional compile-time work in exchange for less runtime machinery and a smaller amount of hidden framework state.

The measurements in the talk illustrate that trade rather than prove a universal winner. In the empty-aspect microbenchmark, handwritten Java and Kora operate at roughly the
billion-operations-per-second scale while the tested Spring AOP path falls to the million or sub-million scale. In the Docker startup benchmark, Kora starts in **4.89 seconds**, compared with **21.13
seconds** for the optimized Spring configuration and **26.53 seconds** for the default Spring configuration. In a clean build, Kora is slower than ordinary Spring because code generation is doing real
work: **11.63 seconds versus 9.33 seconds**. Under ordinary development builds, that gap narrows to **2.51 seconds versus 1.89 seconds**.

That balance is the real story. Kora does not eliminate framework work; it deliberately chooses a different place to pay for it.

```text
Spring-style architecture in the talk

runtime flexibility
dynamic discovery
proxies
large compatibility surface
many overlapping mechanisms
        ↓
more runtime work
more framework-specific knowledge
more optimization work later
```

versus:

```text
Kora-style architecture

compile-time analysis
generated source
explicit graph
narrower model
fewer parallel mechanisms
        ↓
more build-time work
less runtime machinery
less hidden context
```

The speaker's conclusion is therefore not simply “Spring is slow,” and it is not even “Kora is faster.” The stronger claim is that **framework complexity has compound interest**. Every convenient
mechanism that adds another rule, another ordering constraint, another testing annotation, or another optimization technique may be locally reasonable while still increasing the total cost of
understanding the system.

That is why the final slide matters so much. It reframes the problem from individual features to architecture. Spring's problem, in the speaker's view, is not any single square on the bingo card. It
is that after enough years and enough features, the framework forces teams into a continuous negotiation between capability and consequence.

Kora's design tries to break that cycle by making fewer choices available, pushing more validation into compilation, generating inspectable source, and making the normal path already resemble the
optimized path. The goal is not to eliminate expertise, but to redirect expertise away from framework trivia and toward Java, Kotlin, SQL, HTTP, concurrency, distributed systems, databases,
observability, and the actual application.

Which model is better still depends on the application and organization. Spring's ecosystem breadth and compatibility can be enormously valuable. Kora's narrower model can be valuable precisely when
teams decide that the accumulated cost of flexibility has become too high.

The provocative phrase in the talk is “a PhD in Spring.”

The more precise engineering translation is:

> **A framework should not make its own complexity the main thing engineers become experts in. Its functionality should justify the cognitive, operational, and maintenance consequences that come with
it.**

Or, stated in the language of the closing slide:

> **The real framework problem begins when adding functionality repeatedly creates another square in the bingo card that developers must remember forever.**
