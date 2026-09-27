# Kora in Practice: What a Real JVM Framework Benchmark Revealed

**September 26, 2024**

https://www.youtube.com/live/3-FXxOotLVs?si=Zhze6VPWpEGASCWx&t=2968

Kora was probably one of the least familiar frameworks discussed in the talk. It originated inside T-Bank and was later released publicly under the Kora Projects organization. At first glance, it may
look like one more JVM backend framework competing in an already crowded space. The interesting part is not that another framework exists, but the design choices behind it and what happened when those
choices were tested against several more familiar alternatives.

The speaker approached Kora with almost no prior hands-on experience. That makes the result especially interesting: this was not a benchmark produced by a long-time Kora specialist who had spent
months tuning the framework. It was a practical experiment in which the same service was implemented with several JVM technologies and then measured under the same workload.

Kora ended up producing the strongest result in that particular benchmark.

But the most useful part of the talk was not simply that Kora finished first. The experiment also exposed why the framework behaves differently, what trade-offs it makes, where the ecosystem is still
smaller, how resource consumption compared with Spring Boot WebFlux, and why benchmarking the existing system before a rewrite is at least as important as benchmarking the replacement.

## What Makes Kora Different

The central architectural idea is that Kora tries to move framework work out of runtime and into compilation.

Instead of relying heavily on runtime reflection, dynamic discovery, or large amounts of container logic at startup, Kora uses annotation processing and code generation. Developers describe
controllers, repositories, mappings, dependency relationships, and other framework concerns in source code, and the required implementation is generated while the application is being built.

Conceptually, the model is straightforward:

```text
Application source
      ↓
annotations
      ↓
compile-time processing
      ↓
generated code
      ↓
compiled application
```

The resulting runtime does not need to rediscover the application structure every time the process starts.

The speaker also emphasized a second design choice: Kora tries to keep framework abstractions relatively thin. Instead of wrapping every underlying technology in multiple framework-specific layers, it
stays comparatively close to the actual clients and libraries used by the application.

The practical implication is that a Kora service can behave much closer to a manually assembled JVM service than frameworks with heavier runtime infrastructure.

These two properties—compile-time generation and relatively thin abstractions—form the foundation of the performance story shown later in the benchmark.

## Explicit Rather Than Magical

Kora's programming model is more explicit than what many Spring developers are used to.

The speaker notes that annotations have to be placed in more locations because Kora's processors need enough information at compile time to generate the final application correctly. With frameworks
that rely more heavily on runtime discovery or convention, some of that information can remain implicit.

That difference can initially feel slightly verbose.

The benefit is that application structure becomes more predictable. There is less hidden framework behavior waiting until runtime to decide what a component means or how it should be wired.

The speaker's assessment was essentially that the approach is reasonable even if, coming from Spring, the additional explicit annotations can occasionally be mildly irritating.

Kora supports both Java and Kotlin, so the same overall framework model can be used in either language.

## Data Access: Generated Repositories, but SQL Remains Visible

The data-access layer follows the same philosophy.

Kora uses JDBC rather than replacing relational database access with a heavy ORM model. It can generate repository implementations and entity mappings, but SQL remains explicit.

That makes the repository concept familiar without hiding the actual database interaction.

The flow is approximately:

```text
Repository interface
      ↓
explicit SQL
      ↓
generated implementation
      ↓
JDBC
      ↓
database
```

The framework provides macros to reduce repetitive SQL fragments, for example when long column lists or table names would otherwise have to be repeated. But those conveniences do not turn the
repository layer into an ORM.

That means some SQL still has to be written.

The speaker treats this as a reasonable compromise: Kora removes boilerplate but keeps the actual database contract visible.

## Kora's Exact Benchmark Result

The Kora implementation produced the strongest numbers in the benchmark.

The measured result was:

| Metric                |         Kora |
|-----------------------|-------------:|
| Average throughput    | **3729 RPS** |
| Average response time | **19.62 ms** |
| Median response time  | **19.82 ms** |
| P95 response time     | **37.76 ms** |

Those numbers placed Kora first in the final sorted table.

The key point is not only the throughput. Kora also maintained the best or near-best latency characteristics in the same test.

The full result table shown in the talk was:

| Variant                 | Average, ms | Median, ms |   P95, ms |      RPS |
|-------------------------|------------:|-----------:|----------:|---------:|
| **Kora**                |   **19.62** |  **19.82** | **37.76** | **3729** |
| Spring Boot WebFlux     |       22.13 |      22.76 |     40.80 |     3305 |
| Spring Boot Undertow    |       30.60 |      31.50 |     55.73 |     2393 |
| Spring Boot Tomcat + VT |       31.44 |      30.13 |     71.68 |     2330 |
| Original service        |       35.82 |      34.64 |     70.27 |     2044 |
| Helidon                 |       49.01 |      50.03 |     89.05 |     1496 |
| Ktor                    |      279.36 |     280.45 |    537.38 |      263 |

This table is more informative than the simple statement that "Kora was fastest."

Spring Boot WebFlux was actually very close. Its average latency was only a few milliseconds behind Kora, its P95 was close, and its throughput reached 3305 RPS.

The more significant differences appeared when resource consumption was taken into account.

## Kora and WebFlux Were the Two Clear Leaders

The speaker singled out Kora and Spring Boot WebFlux as the two strongest performers and compared their behavior over time.

Across the benchmark runs, both maintained relatively stable throughput once the system had warmed up. Kora generally remained above WebFlux, while their latency behavior followed a similar overall
shape.

That matters because the benchmark was not simply one instantaneous measurement. The graphs showed behavior across the duration of the run, including startup, warm-up, active load, a pause, and
another load interval.

Kora's lead was visible early and remained broadly consistent.

The exact values naturally fluctuated from run to run, but the relative ordering stayed similar enough for the speaker to treat the result as meaningful rather than a one-off spike.

## Resource Consumption Made the Difference More Interesting

The biggest distinction between Kora and WebFlux appeared in CPU consumption.

The slide comparing resource usage states that Kora was approximately **50% more CPU-efficient** in this test.

Spring Boot WebFlux spent most of the active benchmark period close to very high CPU utilization, while Kora remained substantially lower. Kora initially showed a short utilization spike, but then
settled at roughly the mid-range rather than remaining close to full CPU saturation.

The important point is not the exact percentage at every second of the run. The important point is that Kora delivered higher throughput while using materially less CPU.

That changes the interpretation of the benchmark.

A result like:

```text
higher RPS
+
similar CPU
```

is already interesting.

A result like:

```text
higher RPS
+
lower latency
+
substantially lower CPU
```

is considerably more significant operationally.

The heap graphs also showed different behavior. Both implementations exhibited expected allocation and garbage-collection cycles, but WebFlux generally operated with a higher memory envelope, while
Kora remained lower.

The speaker also observed that Spring Boot used roughly a few hundred megabytes even while mostly idle, whereas Kora had a smaller baseline.

Again, the benchmark should not be interpreted as a universal memory law for either framework. Heap behavior depends on application code, GC configuration, JVM options, traffic shape, and
dependencies. But within this experiment, Kora's resource profile was clearly better.

## The Original Service Was Better Than Expected

One of the most important moments in the talk came after the framework comparison.

The speaker decided to benchmark the original service.

That should arguably have happened before the rewrite.

The original service produced:

| Metric                | Original service |
|-----------------------|-----------------:|
| Average throughput    |     **2044 RPS** |
| Average response time |     **35.82 ms** |
| Median response time  |     **34.64 ms** |
| P95 response time     |     **70.27 ms** |

Those results were not exceptional, but they were far from disastrous.

The original implementation sat roughly in the middle of the final table.

This was a critical observation because it changed the context of the rewrite. The new Kora implementation was significantly faster, but the old application may already have been sufficient for the
workload the business actually required.

The lesson is not that the rewrite was necessarily wrong.

The lesson is that the original system should have been measured first.

Before replacing a working service because another technology is expected to be faster, the team should know whether performance is genuinely the limiting factor and how much improvement is actually
required.

## The Real-World Result Was Even More Dramatic

One of the final slides adds an important production detail.

The service rewritten with Kora ultimately replaced the original service, and according to the speaker it showed approximately a **5× improvement in real operating conditions**.

In the spoken commentary, he qualifies that number somewhat: after more statistics accumulated, the effective improvement may have been closer to roughly three times rather than exactly five.

That qualification matters.

The slide captures the headline outcome from the project, while the speaker's commentary reflects the more conservative view after additional observations.

The broader conclusion remains unchanged: the Kora rewrite delivered a substantial real-world improvement, not merely a synthetic benchmark win.

But the exact multiplier should be treated as workload-specific rather than as a generic Kora performance claim.

## A Smaller Ecosystem Was a Real Limitation

Kora was not perfect in the experiment.

The speaker encountered a missing authorization integration.

Instead of finding a ready-made module for the exact case, he had to use an external library and write some integration code manually. That involved creating the necessary interceptor and validation
behavior.

The key point is that the problem was inconvenient rather than blocking.

According to the speaker, the additional work took roughly half an hour.

That experience demonstrates both sides of a smaller framework ecosystem.

The downside is obvious:

```text
fewer ready-made integrations
```

The upside is that Kora's framework model is explicit enough that adding a missing integration does not necessarily require deep framework internals.

This is an important distinction.

A framework does not need a prebuilt adapter for everything if adding the missing one remains cheap.

## The Documentation Was Good Enough for a First-Time User

Another interesting detail is that the speaker was not an experienced Kora user.

He effectively encountered Kora for the first time while working on this benchmark implementation.

Despite that, the documentation and repository examples were sufficient to build the service and solve the missing integration problem.

That is a useful practical signal.

A high-performance framework is much less attractive if reaching that performance requires years of framework-specific expertise.

In this case, the speaker was able to understand enough of the framework from its documentation to produce the strongest implementation in his comparison.

This reinforces Kora's broader advantage: much of the framework behavior is explicit and compile-time generated rather than hidden behind runtime conventions.

## Reactive Programming Was Still Extremely Competitive

Another interesting conclusion from the benchmark is that reactive programming was far from obsolete.

Spring Boot WebFlux came second:

- 3305 RPS;
- 22.13 ms average latency;
- 22.76 ms median;
- 40.80 ms P95.

That result was significantly better than the tested Spring Boot Undertow and Tomcat + Virtual Threads variants.

So although virtual threads simplify synchronous application code enormously, this experiment did not show them immediately outperforming a well-established reactive stack.

The speaker jokes that virtual threads may eventually catch up in a few years as the JVM improves further.

The serious conclusion is simpler:

> Do not assume a concurrency model has won simply because the industry narrative says it has.

Measure the workload.

## Why the Ranking Should Not Be Generalized

The speaker is careful to qualify the result.

Kora won this benchmark.

That does not mean Kora will win every JVM benchmark.

Different parameters could change the ranking:

- different database workload;
- different serialization;
- different concurrency;
- different HTTP stack;
- different JVM options;
- different connection-pool configuration;
- more tuning time;
- a different machine;
- a CPU-bound rather than I/O-bound workload.

The ranking is evidence, not a universal law.

That caveat is especially important because public framework benchmarks are frequently misused as architecture decisions.

A framework can dominate TechEmpower or another synthetic benchmark and still be the wrong fit for a particular application.

Conversely, a framework that does not dominate a public leaderboard may perform perfectly well under the actual business workload.

## The Most Valuable Conclusion Was Methodological

The final slides make the speaker's broader conclusion explicit.

If time and resources permit, teams should try several technologies before committing to one.

More importantly, they should benchmark the existing solution before rewriting it.

The decision process should ideally be:

```text
Existing service
      ↓
measure current behavior
      ↓
identify actual bottleneck
      ↓
define representative workload
      ↓
prototype realistic alternatives
      ↓
measure throughput
      ↓
measure latency
      ↓
measure CPU and memory
      ↓
compare implementation cost
      ↓
choose
```

The bad sequence is:

```text
read benchmark
      ↓
assume technology X is faster
      ↓
rewrite service
      ↓
benchmark old service afterwards
```

The speaker explicitly admits that the existing solution analysis happened too late.

That is probably the most transferable lesson in the entire talk.

## What This Benchmark Says About Kora

Within the limits of this experiment, Kora demonstrated several notable properties.

First, compile-time code generation can produce a full-featured framework without carrying a large runtime cost.

Second, thin abstractions can preserve familiar technologies such as JDBC while still removing repetitive framework boilerplate.

Third, a smaller ecosystem does not necessarily make the framework difficult to extend.

Fourth, Kora can be learned quickly enough for a developer with little prior experience to build a serious comparison implementation.

Fifth, the strongest result was not merely throughput. Kora combined:

```text
highest RPS
+
lowest average latency
+
lowest median latency
+
lowest P95
+
much lower CPU consumption
```

among the compared variants.

That combination is what makes the result interesting.

## Conclusion

Kora entered the talk as one of the lesser-known frameworks and left the benchmark at the top of the table.

Its measured result was:

```text
3729 RPS
19.62 ms average
19.82 ms median
37.76 ms P95
```

Spring Boot WebFlux came close in latency and throughput, but Kora consumed substantially less CPU in the test. The resource comparison presented Kora as roughly 50% more CPU-efficient under the
measured workload.

The original service, meanwhile, turned out to be much healthier than expected at 2044 RPS, with 35.82 ms average latency and 70.27 ms P95. That finding became a useful reminder that an existing
system should be measured before a rewrite begins.

The production result after adopting Kora was also substantial: the speaker reports several-fold acceleration in real conditions, while cautioning that the exact multiplier depends on which period and
accumulated statistics are used.

So the strongest takeaway is not simply "Kora is the fastest JVM framework."

It is more precise than that.

Kora's compile-time design, thin abstractions, JDBC-oriented data access, low runtime overhead, and resource efficiency made it the strongest performer in this particular realistic comparison. It also
proved approachable enough for a developer with very little prior Kora experience to build and extend successfully.

The final lesson of the talk is therefore both about Kora and about engineering discipline:

> **Do not choose a framework because a benchmark says it should be fast. Build a representative implementation, measure the system you already have, compare several realistic alternatives, and let
your own workload decide.**

In this experiment, that process led to Kora.
