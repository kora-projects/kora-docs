---
date: 2026-08-12
description: Why fast startup and time-to-readiness are production capacity properties in the Kora Framework, not just developer convenience.
search:
  exclude: true
---
# Fast Startup Is Not Just Developer Convenience { #fast-startup }

**August 12, 2026**

Fast startup is often discussed as if it were a developer-experience feature. A framework starts in a fraction of a second, the local edit-run loop feels pleasant, and somebody puts the number into a
benchmark table. That is useful, but it is also the least interesting consequence of fast startup in a production service.

For a cloud-native backend, the more important question is not **how quickly the JVM process begins executing**, but **how quickly a new instance becomes useful capacity**. An instance that exists but
cannot safely receive traffic does not help a rolling deployment, does not absorb a traffic spike, does not replace a preempted node, and does not reduce the latency of a scale-from-zero event. From
the perspective of the platform, the critical transition is not `process started`; it is `Pod Ready`.

This distinction is central to the Kora Framework's design. Kora 2 moves application-graph construction and validation to compile time, generates the wiring and adapters as ordinary source code, avoids runtime
reflection for the application graph, and initializes the prebuilt graph as parallel as possible. The Kora 2 landing page therefore presents startup and readiness not merely as benchmark results but
as production properties: faster horizontal scaling, shorter rolling-deployment windows, lower warm-up impact, more practical scale-to-zero and spot capacity, and cheaper full-context integration
testing.

That framing matters because startup time is a small local number that is multiplied by operational events. Every deployment creates new instances. Every horizontal scale-out creates new instances.
Every node loss creates replacement instances. Every spot interruption may create replacement instances. Every scale-from-zero transition starts new instances. Every black-box test that boots the
actual application repeats initialization again. A few seconds that look irrelevant on a laptop can become accumulated unserved capacity, rollout risk, infrastructure headroom, and engineer waiting
time across a fleet.

The useful way to think about startup is therefore not:

```text
How quickly does main() return control to the framework?
```

but:

```text
How long after capacity is requested can that capacity safely do work?
```

For modern backend systems, that is an operational question.

---

## Startup Time and Time-to-Readiness Are Different Metrics { #startup-vs-readiness }

An application has several milestones during startup, and collapsing all of them into one number hides the behavior that matters in production. The operating system can create the process; the JVM can
initialize; application classes can load; configuration can be parsed; the dependency graph can be constructed; database pools, HTTP clients, telemetry exporters, Kafka consumers, schedulers, caches,
and servers can initialize; and finally the application can declare itself ready.

A simplified timeline looks like this:

```text
Container scheduled
      ↓
Image available
      ↓
Process starts
      ↓
JVM starts
      ↓
Framework initialization
      ↓
Application graph initialized
      ↓
Critical dependencies usable
      ↓
Readiness succeeds
      ↓
Traffic can be served
```

Only the last part changes the amount of usable service capacity.

Kubernetes makes that distinction explicit. A readiness probe answers whether a container is currently able to serve traffic. When a Pod is not ready, Kubernetes removes it from the set of endpoints
that should receive normal Service traffic. A startup probe serves a different purpose: it protects applications that legitimately need startup time by preventing liveness and readiness checks from
being treated as meaningful before startup has completed.

This means a production startup benchmark should ideally measure **time-to-readiness**, not just process-start or HTTP-port-open time. A server socket accepting TCP connections does not prove that a
service is operational. A controller may already be registered while a database pool is still unavailable. A management endpoint may respond while a required cache is still loading. Conversely, an
application may be perfectly capable of serving requests while an unnecessarily conservative readiness rule keeps it out of rotation.

The readiness boundary is therefore part of application architecture.

Kora exposes health-probe functionality as part of its operational model, and its broader production positioning includes probes, lifecycle, graceful shutdown, telemetry, and resilience. Its landing
page specifically connects fast startup with fast readiness. The important architectural benefit is not simply that initialization work happens quickly, but that less runtime framework
machinery stands between process creation and a trustworthy readiness transition.

A correct readiness implementation should answer a narrow question:

> If Kubernetes sends this instance normal production traffic now, can the instance handle it according to the service's contract?

That normally means request-critical initialization must have completed. It does **not** necessarily mean every optional background component has reached some ideal steady state. Making readiness
depend on nonessential systems can create unnecessary outages. Making it ignore critical systems can direct traffic to instances that immediately fail.

Fast startup is valuable only when paired with honest readiness.

---

## Where Kora Removes Startup Work { #where-kora-removes-work }

The most important optimization is often the work that never needs to happen.

Many general-purpose frameworks historically perform significant discovery and assembly at runtime: scanning classes or metadata, discovering components, resolving dependency relationships, creating
proxy structures, inspecting annotations reflectively, constructing framework metadata, and adapting user abstractions into runtime representations. Some of this work is individually cheap, but a
production application has many components, and the work sits directly on the critical path between process start and useful capacity.

Kora deliberately moves much of that structural work into compilation. Its application graph is built and validated from declarations such as `@KoraApp`, `@Component`, and `@Module`; generated code
represents the resolved structure; mappers, repositories, handlers, and aspects are generated rather than discovered dynamically at startup. The landing page describes startup as a **prebuilt graph
with parallel initialization** and explicitly contrasts that with runtime framework machinery.

This changes where the cost is paid.

```text
Traditional runtime-heavy approach

Build artifact
      ↓
Start instance
      ↓
Discover framework structure
      ↓
Resolve and construct runtime metadata
      ↓
Initialize application
      ↓
Ready
```

With compile-time construction, more of the structural work moves left:

```text
Kora-style compile-time approach

Compile
      ↓
Validate graph
      ↓
Generate wiring/adapters
      ↓
Build artifact
      ↓
Start instance
      ↓
Initialize prebuilt graph
      ↓
Ready
```

This is not free performance. Annotation processing and code generation add work to compilation. Kora's own landing explicitly acknowledges that trade: a small compile-time cost is paid once per build
in exchange for avoiding scanning, reflection, and graph construction every time an instance boots.

The asymmetry is important. A service artifact may be compiled once and started hundreds or thousands of times across CI, staging, rolling deployments, node replacement, autoscaling, disaster
recovery, and production restarts. Moving deterministic structural work from **every runtime start** to **one build** can therefore be economically attractive even if the total cost of the build
increases slightly.

This is the first reason fast startup is not merely developer convenience: startup happens at fleet frequency, not build frequency.

---

## Readiness Is Capacity { #readiness-is-capacity }

Suppose a service normally runs 20 replicas and each replica can safely sustain 500 requests per second at the target latency. The theoretical steady-state service capacity is approximately:

```text
20 × 500 req/s = 10,000 req/s
```

Now suppose the platform requests 10 additional replicas during a spike. Those replicas do not contribute capacity when the Deployment object is updated, when Pods are created, or even when JVM
processes start. They contribute capacity when they are ready and added to the serving endpoint set.

If new replicas become ready in one second, the service can approach the new capacity quickly. If they require 20 seconds of framework and application initialization, then for most of those 20 seconds
the autoscaler has made a correct decision but the system has not yet received the capacity it requested.

A useful model is:

```text
T_capacity =
    T_metric_detection
  + T_autoscaler_decision
  + T_scheduling
  + T_image
  + T_process
  + T_application_init
  + T_readiness_observation
```

Framework startup primarily influences `T_application_init`, and indirectly it can reduce startup-related CPU and memory pressure. It does not eliminate the other terms. The scheduler still has to
place Pods. Nodes may need to be provisioned. Images may need to be pulled. Metrics arrive on intervals. The readiness probe has its own observation cadence.

This is why claims such as "the application starts in 300 ms, therefore autoscaling takes 300 ms" are wrong.

But the opposite conclusion—"startup does not matter because Kubernetes has other delays"—is also wrong. The terms add together. Removing five or ten seconds of application initialization removes five
or ten seconds from the capacity-recovery path whenever application startup is on that path. If the platform is already optimized so images are local, spare node capacity exists, and autoscaling
metrics react quickly, application readiness can become one of the dominant remaining terms.

A fast application cannot make a slow control plane fast. It can avoid making a fast control plane wait.

---

## Rolling Deployments Turn Startup into Availability Risk { #rolling-deployments }

Rolling deployment is one of the clearest examples of why readiness time matters.

A Kubernetes Deployment using `RollingUpdate` gradually replaces old replicas with new ones. Two parameters bound the process: `maxUnavailable`, which controls how many desired replicas may be
unavailable, and `maxSurge`, which controls how many extra replicas may temporarily be created above the desired count. Kubernetes can make a newly created Pod count toward available
capacity only after it becomes ready.

Consider a service with ten replicas:

```text
Desired replicas:   10
maxUnavailable:      1
maxSurge:            1
```

A simplified replacement cycle is:

```text
Create new Pod
      ↓
Wait for it to become Ready
      ↓
Remove an old Pod
      ↓
Create another new Pod
      ↓
Wait for Ready
      ↓
...
```

The exact Deployment-controller behavior is more flexible than this diagram, but the operational dependency remains: new replicas have to become available before the rollout can safely advance within
its configured availability constraints.

If readiness takes 15 seconds, that delay appears repeatedly as the rollout progresses. If readiness takes one second, the deployment can advance much more aggressively without sacrificing the same
availability target. Across a large number of replicas and services, the difference becomes an observable deployment-window difference rather than a cosmetic startup benchmark.

Long startup has another cost: **surge capacity remains occupied longer**. During rolling updates, old and new replicas overlap. Those extra Pods consume CPU and memory. Kubernetes documentation also
notes that terminating Pods can temporarily make actual resource use exceed the simple `replicas + maxSurge` intuition until termination completes. When startup and shutdown windows
are long, transient rollout footprint is larger for longer.

That matters in tightly packed clusters. A rollout can need temporary capacity precisely when many teams are deploying simultaneously. Organizations often reserve cluster headroom partly so routine
changes do not deadlock on scheduling. Faster readiness reduces how long a deployment occupies that transient headroom.

There is also an SLA dimension. During a rollout, some fraction of the fleet is changing state. The faster replacement replicas become trustworthy capacity, the shorter the interval in which the
service operates with reduced margin. Kora's landing describes this as narrowing the window of reduced capacity and lowering SLA/error-budget risk.

The practical point is not that fast startup magically makes a rollout zero-risk. Readiness bugs, schema changes, connection storms, cache effects, bad code, and downstream limits can still break a
release. Rather, when a deployment is healthy, a framework that reaches readiness quickly removes unnecessary waiting from the controller's replacement loop.

---

## Warm-Up Matters After Readiness Too { #warm-up-after-readiness }

There is an important trap in startup discussions: **ready is not always steady-state**.

The JVM is a dynamic runtime. JIT compilation, class initialization on first use, lazy client setup, caches, TLS handshakes, connection establishment, branch profiling, and application-level
memoization can all continue after a Pod first becomes ready. A service can therefore pass readiness quickly but still exhibit temporarily elevated latency.

This gives us at least three distinct milestones:

```text
Process started
      ↓
Operationally ready
      ↓
Steady-state performance
```

The gap between the second and third milestones matters during scaling and deployments because fresh instances receive real traffic. If their first requests are much slower than steady state, they can
produce a temporary p95 or p99 latency spike even though readiness is technically correct.

Kora's landing page explicitly makes the narrower claim that compile-time wiring, thin abstractions, and reduced runtime machinery make warm-up **smaller, not nonexistent**. That
qualification is important. Kora is still a JVM framework. HotSpot still performs JIT compilation unless another execution mode is used. Application libraries may still initialize lazily. JDBC pools
still establish connections. TLS sessions still have to be created. User code can still create expensive first-request paths.

Framework design can reduce the framework-induced part of warm-up; it cannot repeal JVM or application behavior.

This suggests a more useful production metric than "startup time":

```text
time-to-steady-service
```

For example, teams can load-test a fresh replica and plot p50/p95/p99 latency from the first request until the distribution stabilizes. That measurement captures both readiness and post-readiness
warm-up. It is especially useful when deciding whether new replicas genuinely help during a short traffic spike.

---

## Horizontal Autoscaling Has a Reaction Budget { #autoscaling-reaction-budget }

Horizontal autoscaling is frequently described as a simple feedback loop:

```text
Load rises
   ↓
HPA observes metric
   ↓
Desired replicas increase
   ↓
New Pods start
   ↓
Capacity rises
```

Operationally, the important number is the total time from **load increase** to **useful new capacity**.

For a CPU-driven HorizontalPodAutoscaler, Kubernetes has deliberate protections around metrics from starting Pods. The HPA treats not-yet-ready Pods conservatively, and the controller has
startup-related windows such as the initial readiness delay and CPU initialization period so transient startup CPU does not distort scaling decisions. This is particularly relevant to JVM
workloads because initialization and warm-up can consume substantial CPU.

That yields two separate ways slow startup can hurt:

1. the new replica does not serve traffic while it is unready;
2. startup behavior can complicate the autoscaler's interpretation of CPU metrics.

Fast and stable readiness reduces the period in which new Pods exist but are ambiguous participants in the feedback loop. It also makes the system easier to reason about because the interval between "
replica requested" and "replica contributing" becomes short and predictable.

However, startup is only one part of autoscaling latency. If metrics are sampled slowly, if the HPA reconciliation cadence is conservative, if the cluster has no spare nodes, if a cluster autoscaler
must provision a VM, or if an image has to be downloaded, a 300 ms application startup cannot compensate for a 60-second infrastructure path.

A useful engineering approach is therefore to maintain an **autoscaling latency budget**:

| Phase                      | Example responsibility           |
|----------------------------|----------------------------------|
| Signal generation          | application / metrics pipeline   |
| Signal collection          | metrics infrastructure           |
| Scale decision             | HPA or external autoscaler       |
| Pod scheduling             | Kubernetes scheduler             |
| Node availability          | cluster/node autoscaler          |
| Image availability         | registry, image size, node cache |
| JVM/process startup        | runtime                          |
| Application initialization | framework + application          |
| Readiness detection        | probe configuration              |
| Warm-up to target SLO      | JVM + libraries + application    |

The framework controls only part of this table, but that part should still be made as small and deterministic as practical.

Kora's value proposition is strongest when the rest of the infrastructure is already reasonably responsive. In that environment, moving graph work to compile time and minimizing runtime initialization
means the service itself is less likely to become the bottleneck in scale-out.

---

## Why HPA Reaction Time Changes Capacity Planning { #hpa-reaction-time }

Imagine two services with the same steady-state throughput per replica. Service A becomes ready in one second; Service B becomes ready in 20 seconds.

If traffic can jump abruptly, Service B has to survive roughly 19 additional seconds before newly requested replicas begin helping. There are only a few ways to do that:

- keep more baseline replicas running;
- allocate more per-replica headroom;
- rely on queues or admission control to absorb the spike;
- accept temporary latency/error degradation;
- predict the spike and scale ahead of it.

All of these are valid techniques. But several cost money or operational complexity.

This is how startup time becomes an infrastructure-cost variable. If scale-out is slow, a team often compensates by provisioning a larger static baseline. The slower the system can create useful
capacity, the more demand variability must be absorbed by capacity that already exists.

A simplified headroom relationship can be expressed as:

```text
required transient headroom
≈ rate of demand increase × capacity activation delay
```

That is not a complete capacity-planning formula—the real system has queueing, per-replica saturation curves, nonlinear latency, dependencies, and control-loop behavior—but it captures the direction
correctly. If demand rises quickly, activation delay determines how much excess work accumulates before new capacity joins.

Fast readiness therefore does not merely "make HPA faster." It makes **reactive autoscaling more economically useful** because less baseline overprovisioning is needed to bridge the reaction window.

This is exactly the operational interpretation highlighted on Kora's landing: readiness measured in seconds can allow horizontal scaling to absorb a spike instead of requiring the fleet to keep the
entire peak margin running all the time.

---

## Cold Instances Are Where Startup Cost Becomes Visible { #cold-instances }

A warm service hides startup cost because existing replicas continue to do the work. Cold capacity does not have that luxury.

A **cold instance** is any instance that has to be created before it can contribute. That includes:

- a new Pod created by HPA;
- a replacement after node failure;
- a Pod scheduled onto newly provisioned cluster capacity;
- a replica created during deployment;
- an instance restored after scale-to-zero;
- a replacement for preempted spot capacity;
- a full application started inside an integration or black-box test.

These scenarios differ in why the instance starts, but the same readiness path appears every time.

This is why a small benchmark result can have disproportionate operational value. A service that almost never restarts will barely notice startup differences. A highly elastic or frequently deployed
service will encounter the cold path constantly.

The relevant fleet-level quantity is closer to:

```text
startup cost per instance
× instance starts per day
× number of services
```

and not simply:

```text
startup cost per developer launch
```

Organizations that deploy often, use aggressive autoscaling, rely on spot capacity, or run large CI suites amplify startup behavior far more than long-lived static deployments do.

---

## Scale-to-Zero Makes Cold Start Part of Request or Work Latency { #scale-to-zero-cold-start }

Scale-to-zero changes the economics of idle services.

If a workload can have zero running replicas, the platform avoids paying the baseline runtime cost while the workload is unused. But the next unit of work must wait for capacity to be recreated. That
turns cold-start latency into part of the workload's externally visible behavior.

As of Kubernetes 1.37, HPA scale-to-zero support is Beta and enabled by default for suitable object or external metrics. CPU and memory resource metrics cannot perform the scale-from-zero decision
because there are no running Pods from which to collect those resource metrics. Queue depth, external demand, or another out-of-band signal can instead trigger scale-up.

The scale-from-zero path resembles:

```text
External work appears
      ↓
Metric changes
      ↓
Autoscaler observes metric
      ↓
Replica count 0 → N
      ↓
Pod scheduled
      ↓
Container starts
      ↓
Application initializes
      ↓
Readiness succeeds
      ↓
Work begins
```

Every term matters because there is no warm replica already serving traffic.

For queue consumers and asynchronous workers, this can be an excellent trade. Work safely accumulates in a durable queue while capacity starts. The Kubernetes 1.37 scale-to-zero documentation
explicitly notes that this model works well when work can wait in a durable queue.

Request-driven HTTP services are harder. A normal Kubernetes Service does not itself buffer arbitrary requests until a zero-replica backend returns. A gateway, serverless layer, queueing proxy,
activation component, or external platform mechanism is needed if requests must survive the cold start. This is an important distinction: fast framework startup makes scale-to-zero **more
practical**, but it does not provide the activation and buffering architecture by itself.

The faster the application reaches readiness, the smaller the cold-start penalty that the surrounding platform must hide. If an application takes tens of seconds to initialize, scale-to-zero may be
unacceptable for interactive traffic. If it becomes ready very quickly, a broader class of internal tools, infrequently used APIs, event consumers, and scheduled workloads can release all baseline
replicas when idle.

Kora therefore changes the boundary of what is operationally reasonable. It does not make every service a serverless function; it makes cold application initialization less likely to be the reason a
scale-to-zero design fails.

---

## Low-Traffic Services Are Often Dominated by Baseline Cost { #low-traffic-baseline-cost }

The economic value of fast startup is closely related to another property: low baseline overhead.

High-traffic services are dominated by productive work. An instance spends most of its CPU and memory handling requests, messages, serialization, database access, business logic, and telemetry. For a
low-traffic admin panel or internal tool, the opposite may be true: most of the time, the process is simply alive.

That means the cost equation changes:

```text
High traffic:
total cost ≈ work + runtime overhead

Low traffic:
total cost ≈ runtime baseline + tiny amount of work
```

For a low-utilization fleet, framework baseline becomes disproportionately important. If a company has hundreds or thousands of small internal services, saving a modest amount of CPU or memory on each
idle replica multiplies across the fleet.

Fast startup contributes because it permits more aggressive lifecycle policies. You can keep fewer warm replicas, recover them quickly when needed, and reduce the operational fear associated with
restarting or rescheduling them. A thin runtime and fast readiness complement each other: one reduces the cost while an instance is alive; the other reduces the cost of not keeping it alive in
advance.

The Kora landing makes this connection directly by discussing low-utilization services alongside scale-to-zero and by framing framework efficiency as fleet economics rather than isolated
throughput.

---

## Spot Capacity Rewards Services That Recover Quickly { #spot-capacity }

Spot or preemptible compute trades reliability for price. The cloud provider can reclaim the underlying machine, and workloads must tolerate replacement.

Google Kubernetes Engine, for example, documents Spot VMs as capacity with no availability guarantee. When the infrastructure is reclaimed, managed workloads such as Deployments create and schedule
replacement Pods; the platform provides only a bounded graceful shutdown window during preemption.

For a stateless service, the core operational loop is:

```text
Spot node disappears
      ↓
Replica capacity is lost
      ↓
Replacement Pod is created
      ↓
Pod is scheduled somewhere else
      ↓
Application starts
      ↓
Readiness succeeds
      ↓
Capacity is restored
```

This makes both **shutdown speed** and **startup speed** valuable.

Graceful shutdown determines whether in-flight work can complete or be safely handed back. Fast startup determines how quickly replacement capacity becomes useful. Kora's production model includes
graceful shutdown as well as fast readiness, which is the right pairing: elasticity is a lifecycle problem, not just a boot benchmark.

Fast startup does not make spot capacity safe for every workload. Stateful systems, non-idempotent processing, tight local-data dependencies, or applications that cannot tolerate abrupt node loss need
additional architecture. Pod disruption budgets do not prevent involuntary infrastructure loss. Redundancy, retry semantics, durable state, queueing, and topology still matter.

But for suitable stateless and fault-tolerant services, recovery speed changes the economics. If a replica can be recreated cheaply and becomes ready quickly, a higher churn rate is less painful. That
makes discounted interruptible capacity easier to incorporate into the fleet.

A useful principle is:

> The cheaper the infrastructure is because it is less stable, the more valuable fast and deterministic application recovery becomes.

---

## Connection Storms: Fast Startup Needs Controlled Startup { #connection-storms }

There is one important counterexample to the idea that "faster is always better."

Suppose 100 replicas are created simultaneously and every replica immediately opens 20 database connections:

```text
100 replicas × 20 connections = 2,000 connection attempts
```

If the database can comfortably handle only 500 active connections, fast startup can transform a slow rollout into a very efficient denial-of-service attack against your own dependency.

The same problem can occur with Kafka metadata requests, TLS handshakes, cache warm-up, secrets backends, service discovery, configuration stores, or remote APIs. Parallel initialization inside one
process and concurrent initialization across many replicas can combine into a large startup burst.

Therefore, the objective is not:

```text
initialize everything as aggressively as possible
```

It is:

```text
reach safe useful capacity as quickly as the whole system permits
```

That can require:

- bounded connection-pool initialization;
- lazy creation of noncritical resources;
- jitter;
- rate limits;
- dependency-aware readiness;
- staggered rollout parameters;
- sane `maxSurge`;
- retry with backoff;
- load shedding;
- separating critical startup work from optional warm-up.

Fast framework startup is valuable because it removes avoidable framework overhead. It should not be confused with permission to ignore downstream capacity.

This is also where compile-time and runtime responsibilities separate cleanly. Kora can precompute wiring and avoid scanning. It cannot know how many simultaneous PostgreSQL connections the production
cluster can accept. Application and platform owners still have to design that operational contract.

---

## Rolling Deployment: A Concrete Capacity Example { #rolling-deployment-example }

Consider a service with:

```text
replicas = 12
capacity per ready replica = 1,000 req/s
normal traffic = 8,000 req/s
target safety margin = 25%
```

Twelve replicas provide 12,000 req/s of nominal capacity. The application has comfortable steady-state margin.

Now deploy a new version with:

```yaml
strategy:
    type: RollingUpdate
    rollingUpdate:
        maxUnavailable: 1
        maxSurge: 1
```

During the rollout, the service may temporarily have one old replica unavailable while one additional new replica is starting. If a fresh replica requires 20 seconds before it can handle its share of
production traffic, the deployment spends substantially more time in transitional states. If traffic rises unexpectedly during that window, the fleet has less spare room to absorb it.

With one-second readiness, each successful replacement closes the transient window much faster. The rollout is not merely "20 times faster" in a simplistic sense because termination, probes,
controller reconciliation, scheduling, and other work still take time. But the **application-controlled waiting term** becomes almost negligible.

Multiply that difference by:

```text
replicas × deployments per week × services
```

and startup time becomes a delivery-system property.

This is why Kora's landing describes shorter deployment windows as an operational consequence of fast readiness rather than a local development convenience.

---

## Autoscaling: A Concrete Spike Example { #autoscaling-example }

Assume a service normally runs 10 replicas, each comfortably handling 400 req/s at the required SLO:

```text
steady safe capacity = 4,000 req/s
```

Traffic suddenly rises from 3,000 to 6,000 req/s. The autoscaler decides to add five replicas.

The overload interval is approximately bounded by:

```text
T_overload =
    T_detect
  + T_scale_decision
  + T_schedule
  + T_start
  + T_ready
  + T_ramp
```

Suppose the non-application terms total 8 seconds.

### Runtime A { #runtime-a }

```text
application startup/readiness = 1 second
ramp to useful performance     = 1 second
total response                 ≈ 10 seconds
```

### Runtime B { #runtime-b }

```text
application startup/readiness = 15 seconds
ramp to useful performance     = 5 seconds
total response                 ≈ 28 seconds
```

The absolute numbers are illustrative, but the engineering consequence is real. Runtime B needs almost three times as much time before the requested capacity is useful. During those extra seconds,
existing replicas are overloaded, queues grow, p99 latency increases, retries may amplify traffic, or requests fail.

Teams often solve this by provisioning extra baseline replicas. That works—but it means paying continuously to compensate for a slow cold path used occasionally.

The operational proposition behind Kora's startup design is that framework initialization should not force that trade.

---

## Readiness and HPA Need to Agree About Warm-Up { #readiness-hpa-warmup }

A subtle production problem appears when readiness transitions too early.

Suppose a new JVM becomes functionally able to answer requests after one second but experiences a large CPU/JIT warm-up for another 20 seconds. If readiness flips to true immediately, the HPA may
eventually include the new replica's metrics, traffic will begin flowing to it, and startup CPU can interact with CPU-based scaling decisions.

Kubernetes has specific logic for this problem. For CPU metrics, it can ignore samples from Pods that are not yet considered stably ready, using the controller's initial-readiness and
CPU-initialization windows. The Kubernetes documentation also recommends using startup/readiness behavior to separate initialization CPU from normal operation when appropriate.

The correct policy depends on what "ready" means for the service.

If the instance can satisfy the SLO during JIT warm-up, there may be no reason to hide it. If warm-up causes severe tail latency, readiness may need to remain false longer—or traffic may need to ramp
gradually through another mechanism. Keeping Pods unready solely to hide normal JVM optimization can also waste capacity.

The best answer comes from measurement:

1. start a completely cold application;
2. begin representative load as soon as readiness succeeds;
3. record throughput, CPU, allocation rate, and latency percentiles;
4. determine when performance stabilizes;
5. compare the result against the SLO;
6. tune readiness and autoscaling behavior around the actual curve.

Kora reduces framework-driven warm-up, but production validation should still measure the complete application.

---

## Scale-to-Zero Is a Budget, Not a Boolean Feature { #scale-to-zero-budget }

Teams sometimes discuss scale-to-zero as if it were simply enabled or disabled. A more useful model is to treat it as a latency budget.

For a queue worker, suppose the business permits 30 seconds between a message arriving and processing beginning. The cold path might look like:

```text
metric detection             5 s
autoscaler reconciliation    2 s
scheduling                   1 s
image already cached         0.5 s
JVM + application readiness  1 s
--------------------------------
total                        9.5 s
```

That workload has plenty of budget.

Now replace the application initialization term with 25 seconds:

```text
total ≈ 33.5 s
```

The same architecture now violates the requirement even though Kubernetes and the workload code did not change.

This is why startup characteristics determine which resource-management strategies are practical. A framework does not implement the whole scale-to-zero system, but it consumes part of the cold-start
budget. The less budget consumed by framework initialization, the more remains for unavoidable infrastructure work.

For HTTP workloads, the same equation applies but the budget is usually much smaller. Interactive users may tolerate hundreds of milliseconds or a few seconds, not tens of seconds. Those workloads
often need a warm minimum replica count, predictive scaling, or an activation proxy that can buffer and route around the cold period.

Fast startup expands the design space. It does not abolish latency requirements.

---

## CI Is Another Fleet of Cold Starts { #ci-cold-starts }

Production is not the only place where applications repeatedly start.

Modern CI pipelines often create short-lived environments. Integration tests launch databases or brokers with Testcontainers. Component tests create application graphs. Black-box tests package the
actual service, start it, wait for readiness, call real endpoints, and destroy it. Parallel jobs repeat the process across commits, branches, JDK versions, database versions, and test shards.

Kora's testing model explicitly supports graph-based component testing and Testcontainers-backed integration or black-box testing, and the project documentation recommends testing the packaged service
artifact as a black box.

If one test suite starts the application once, saving two seconds is unremarkable.

If a CI organization runs:

```text
2 seconds saved
× 20 application starts per pipeline
× 100 pipelines per day
= 4,000 seconds/day
≈ 67 minutes/day
```

that is already meaningful machine time.

More importantly, wall-clock feedback affects human behavior. Developers run cheap tests more often. Expensive integration suites migrate toward pre-merge gates or nightly builds because people avoid
waiting. When full-context tests become inexpensive, teams can move higher-confidence checks earlier.

This has a quality consequence:

```text
cheaper realistic tests
      ↓
more frequent realistic tests
      ↓
shorter defect feedback
      ↓
less expensive debugging
```

Startup speed therefore affects not just compute consumption but test strategy.

---

## Integration Tests Benefit More Than Unit Tests { #integration-tests }

Unit tests rarely care about framework startup because they usually instantiate a small object graph directly. The benefits appear as the test boundary grows.

Consider three levels:

```text
Unit test
business object only

Component test
selected application graph

Integration test
application graph + real infrastructure

Black-box test
packaged application + infrastructure + network boundary
```

At each step downward, startup becomes a larger fraction of test cost.

For an integration test that performs 300 ms of useful assertions but waits five seconds for the application, startup dominates the test. If application readiness takes 500 ms instead, the economics
change dramatically. The suite can afford finer isolation, more parallel shards, or per-class/per-scenario application contexts where those improve correctness.

Kora's compile-time graph helps in two ways. First, it reduces the runtime work required to assemble the application. Second, graph-oriented testing can initialize only the relevant portion for
component tests rather than always starting every unrelated branch.

The broader principle is that **fast startup increases the amount of production-realistic behavior you can afford to test continuously**.

That is more strategically useful than merely making `gradle run` feel faster.

---

## Black-Box Tests Turn Startup into Pipeline Latency { #black-box-tests }

Black-box testing is the strongest illustration because the test treats the service like production does.

A typical pipeline stage is:

```text
Build artifact
      ↓
Build container
      ↓
Start dependencies
      ↓
Start application container
      ↓
Wait for readiness
      ↓
Run HTTP/API tests
      ↓
Stop environment
```

The readiness wait is explicit. A correct black-box harness cannot send meaningful tests before the service is operational.

Kora's documentation describes a Testcontainers-oriented pattern in which a real application image is started and the harness waits for application readiness before using the service.
This makes startup/readiness a directly measurable part of CI wall-clock time.

Fast readiness can also reduce flakiness. Slow-starting applications often force test harnesses to use large generic timeouts. Those timeouts hide real startup regressions and make failures expensive:
a broken service may take 30 or 60 seconds to be declared dead. A consistently fast service permits tighter bounds.

For example:

```text
Normal ready time:       < 1 s
Test readiness timeout:   5 s
```

A five-second timeout now means something. A test that reaches it is likely unhealthy.

With a service whose startup varies between 5 and 25 seconds depending on class loading, environmental timing, or runtime discovery, the timeout has to be much larger and provides less diagnostic
value.

Predictability is as valuable as raw speed.

---

## Startup Variance Matters as Much as Startup Average { #startup-variance }

Benchmark charts often show averages, but production systems care about tails.

Suppose two frameworks have the same five-second mean startup:

```text
Framework A:
4.8, 5.0, 5.1, 5.0, 5.1

Framework B:
1.5, 2.0, 3.0, 7.0, 11.5
```

The average is similar, but operational behavior is very different.

Rolling deployments, startup probes, readiness timeouts, autoscaling, and CI all need bounds. High startup variance forces conservative configuration. A team sets a longer startup-probe failure window
because once in a while initialization takes much longer. That increases the time to detect real startup failures. CI timeouts become larger for the same reason.

Compile-time resolution can improve not just startup speed but determinism by removing dynamic discovery work from the runtime path. It does not guarantee zero variance—network dependencies and
external systems can still dominate—but it reduces one source of runtime variability.

A mature startup benchmark should therefore report something like:

```text
p50 time-to-readiness
p95 time-to-readiness
p99 time-to-readiness
time-to-steady-state p95 latency
startup CPU
startup RSS / heap
external dependency calls during startup
```

A single "started in 740 ms" line cannot describe all of this.

---

## Fast Startup Does Not Mean Everything Should Be Eager { #not-everything-eager }

Compile-time wiring solves structural discovery, but application initialization policy remains a design choice.

Some components should be eager because they are necessary to serve requests safely. Others should be lazy because initializing them would delay readiness even though they are rarely used.

For example:

```text
Probably readiness-critical
- HTTP server routing
- required configuration
- request-critical database access
- mandatory credentials
- essential serialization/mapping

Potentially deferrable
- rarely used admin integration
- optional cache prefill
- background report client
- noncritical analytics exporter
```

The correct classification depends on service semantics.

Fast framework startup gives teams room to make these choices based on the application rather than compensating for expensive framework bootstrap. But it does not remove the need to decide what
belongs on the startup critical path.

A good review question is:

> If this component takes ten seconds to initialize, must the entire service remain unavailable for ten seconds?

If the answer is no, it may not belong in readiness-critical initialization.

---

## Fast Startup Changes Failure Recovery { #failure-recovery }

Most startup discussions focus on planned events—deployments and scaling—but unplanned recovery is equally important.

When a node fails, Kubernetes eventually schedules replacement workloads. When a process crashes, the container may restart. When an availability zone experiences disruption, capacity may have to
appear elsewhere. In all of these cases, recovery has a cold-start segment.

A rough recovery-time model is:

```text
T_recovery =
    T_failure_detection
  + T_control_plane_reaction
  + T_rescheduling
  + T_application_readiness
```

Framework startup cannot change failure detection or infrastructure repair, but it can reduce the final term.

This becomes particularly relevant when many replicas are lost simultaneously. Recovery after a single Pod crash may be uninteresting because the remaining fleet has large redundancy. Recovery after a
node or zone event can involve many cold instances at once. The faster each replacement reaches readiness—and the less aggressively it overwhelms shared dependencies while doing so—the faster the
service restores safety margin.

Fast startup is therefore part of resilience even though it is not, by itself, a resilience mechanism.

---

## Startup and Graceful Shutdown Form One Lifecycle { #startup-shutdown-lifecycle }

Elastic systems create and destroy instances constantly. Optimizing only startup gives half of the lifecycle.

A healthy instance lifecycle looks more like:

```text
Create
  ↓
Initialize
  ↓
Ready
  ↓
Serve
  ↓
Readiness removed
  ↓
Drain
  ↓
Graceful shutdown
  ↓
Exit
```

Fast readiness improves the left side. Graceful shutdown improves the right side.

During deployments and spot interruptions, both sides run at once: old replicas are leaving while new replicas are arriving. If startup is fast but shutdown drops in-flight work, rollout quality
suffers. If shutdown is elegant but startup takes 30 seconds, rollout capacity remains constrained.

Kora's production positioning deliberately groups fast readiness and graceful shutdown together. That is the correct systems view. Cloud-native efficiency is about **instance turnover
**, not a stopwatch around one method.

---

## Measuring Kora Startup Correctly { #measuring-kora-startup }

If you want to evaluate Kora for your own system, reproduce the operational condition rather than relying only on a framework microbenchmark.

A useful experiment is to package the real service and run it under production-like CPU and memory limits. Then repeatedly measure:

```text
container creation → process start
process start       → management endpoint available
process start       → readiness success
readiness success   → stable latency/throughput
```

Also capture:

```text
startup CPU
peak RSS
heap after readiness
number of DB connections created
outbound requests during initialization
class-loading/JIT activity
probe timing
```

Run enough iterations to understand the distribution, not just the best result.

Kora's landing startup comparison itself describes a constrained Docker environment and distinguishes startup/readiness from build measurements. That is a better direction than a bare "
Hello World started in X ms" benchmark because production services include configuration, telemetry, persistence, clients, health endpoints, and other integrations.

For your own decision, however, the only benchmark that matters is your service. Framework architecture tells you where to expect differences; measurement tells you whether those differences are
material under your workload.

---

## Do Not Benchmark Startup Without the Database { #benchmark-with-database }

A common mistake is to compare framework initialization while excluding real dependencies, then assume the same ratio will appear in production.

Suppose:

```text
Framework A bootstrap: 0.3 s
Framework B bootstrap: 3.0 s
Database migration:    8.0 s
External config:       2.0 s
```

Total readiness might become:

```text
A = 10.3 s
B = 13.0 s
```

The framework difference is still real, but the operational ratio is much smaller.

Or, if migrations are moved outside application startup and connections are established lazily:

```text
A = 0.5 s
B = 3.2 s
```

the framework becomes dominant again.

Neither result invalidates the framework benchmark. It simply shows that **time-to-readiness is the sum of the entire critical path**.

When evaluating Kora, include exactly the components that production readiness requires. That is also the best way to identify whether the next optimization should be framework initialization, Flyway,
database connection establishment, secret retrieval, DNS, TLS, remote configuration, or something else.

---

## The Build-Time Trade Is Usually Favorable for Server Fleets { #build-time-trade }

Compile-time frameworks shift work into the build, which can sound like merely moving cost from one place to another.

But build and runtime have different multiplicities:

```text
builds per artifact:            1
runtime starts per artifact:    potentially many
test context starts:            potentially many
production replicas:            many
restarts / reschedules:         many
```

If 500 ms of additional compilation removes two seconds from every runtime start, the payoff appears after the first few starts.

The trade can be even more attractive in immutable-container environments because one artifact is promoted through several stages:

```text
CI
→ integration
→ staging
→ canary
→ production region A
→ production region B
```

The compile-time investment is reused everywhere.

Of course, build latency is not irrelevant. Very expensive annotation processing can damage local feedback. The goal is not to maximize compile-time work; it is to move deterministic structural work
to the phase where it is cheapest overall.

Kora's architecture makes that bet explicitly: pay for validation and generation at compile time, then keep runtime startup lean.

---

## The Cost Model Is Larger Than CPU Seconds { #cost-model }

The business impact of startup appears in several different budgets.

### Infrastructure headroom { #infrastructure-headroom }

Slower scale-out requires more preexisting spare capacity to tolerate sudden load.

### Deployment headroom { #deployment-headroom }

Long readiness increases the duration of surge replicas and transitional capacity during rollouts.

### Reliability budget { #reliability-budget }

Long cold recovery extends the period after failure or preemption in which redundancy is reduced.

### Latency budget { #latency-budget }

Fresh replicas that warm slowly can raise tail latency during scale-out or deployment.

### CI compute { #ci-compute }

Repeated application boots consume pipeline CPU and wall-clock time.

### Engineer attention { #engineer-attention }

Long feedback loops interrupt development and reduce the frequency with which developers run realistic tests.

### Architectural optionality { #architectural-optionality }

Slow startup can make scale-to-zero, aggressive autoscaling, ephemeral environments, and spot-heavy fleets unattractive even when they would otherwise reduce cost.

This is why it is too narrow to ask whether "users notice a two-second startup difference." Users do not directly watch the process boot. They notice the second-order effects: overloaded replicas
during a spike, elevated p99 during a rollout, longer recovery after capacity loss, slower preview environments, or slower delivery because integration tests are expensive.

---

## Fast Startup Is Most Valuable When You Actually Use Elasticity { #elasticity-value }

Not every service needs to optimize startup aggressively.

If a backend has exactly four replicas, is deployed once per month, never autos-scales, runs on fixed machines, and starts only during maintenance windows, startup may simply not matter much.
Framework choice should not be reduced to one benchmark.

Fast readiness becomes strategically important when one or more of the following are true:

- deployments are frequent;
- replica counts are large;
- traffic is bursty;
- HPA is expected to respond rather than merely protect against long-term drift;
- cluster capacity is elastic;
- scale-to-zero is desirable;
- workloads use spot or preemptible nodes;
- Pods are frequently rescheduled;
- many low-traffic services exist;
- integration and black-box tests boot the application repeatedly;
- ephemeral environments are common.

Kora is explicitly designed for the latter style of environment: cloud-oriented services where runtime efficiency and predictable lifecycle behavior compound across a fleet.

This is also why startup should not be evaluated independently of deployment architecture. A framework can make capacity cheap to activate; the platform must then be configured to take advantage of
that property.

---

## Practical Kubernetes Guidance for a Fast-Starting Kora Service { #kubernetes-guidance }

A fast application can still be made slow by conservative platform configuration. The probe interval alone can erase much of the framework advantage.

For example, imagine the application becomes ready after 400 ms, but the readiness probe is configured to run every 10 seconds. Depending on timing, Kubernetes may not observe readiness immediately.
Current Kubernetes behavior may probe an unready container more aggressively than the normal period in order to make it ready faster, but probe configuration still belongs in the latency
budget.

The goal is not to use the smallest values everywhere. Overly aggressive probes can create noise and unnecessary traffic. Instead, choose probe configuration that reflects measured startup behavior
and failure semantics.

A representative structure might be:

```yaml
readinessProbe:
    httpGet:
        path: /readiness
        port: management
    periodSeconds: 2
    timeoutSeconds: 1
    failureThreshold: 3

livenessProbe:
    httpGet:
        path: /liveness
        port: management
    periodSeconds: 10
    timeoutSeconds: 1
    failureThreshold: 3
```

Whether a separate `startupProbe` is useful depends on the service. For a consistently fast-starting application, it may be unnecessary. For a service with occasional legitimately long
initialization—perhaps a migration or data-loading mode—a startup probe can prevent liveness from killing the application while it is still starting.

The critical rule is to avoid carrying over probe defaults and delays designed for a much slower runtime without checking whether they are still necessary. If the framework becomes ready in hundreds
of milliseconds but `initialDelaySeconds` remains 30 seconds, the platform will not fully realize the startup improvement.

Measure the entire orchestration path.

---

## Readiness Should Not Test the Entire Internet { #readiness-scope }

Another operational anti-pattern is an excessively broad readiness probe.

Suppose the service depends on five remote systems and readiness fails whenever any one is temporarily unavailable. Kubernetes then removes the instance from traffic. If all replicas observe the same
downstream outage, every replica can become unready at once, converting a partial dependency problem into total service unavailability.

Readiness should represent whether the instance itself can serve its contract, taking the service's degradation model into account. If the service can return cached data when one downstream is
unavailable, that dependency may not belong in readiness. If every request absolutely requires the primary database, database availability may matter—but even then, teams need to understand whether
removing all replicas helps.

Fast startup does not fix readiness semantics. It makes getting to the readiness decision cheap. The decision itself must still be designed carefully.

Kora's explicit probe model is useful because readiness is treated as an application capability rather than hidden framework state. The architecture remains visible to the team.

---

## CI and Production Should Agree on Readiness { #ci-production-readiness }

One underrated benefit of black-box testing is that the same readiness contract used by Kubernetes can be exercised in CI.

Instead of:

```text
sleep 10
curl localhost:8080
```

a test harness can:

```text
start application
      ↓
poll readiness
      ↓
begin tests as soon as ready
      ↓
fail if readiness exceeds a tight bound
```

This turns startup performance into a regression-tested property.

If a new library unexpectedly adds five seconds to initialization, CI notices. If a migration accidentally blocks startup, CI notices. If a readiness probe never turns healthy after a configuration
change, CI notices before Kubernetes gets stuck during a production rollout.

Fast baseline startup makes this especially effective because there is room to set a tight threshold. A service normally ready in 500 ms can treat five seconds as suspicious. A service that normally
fluctuates between 10 and 40 seconds has a much weaker signal.

One useful engineering practice is therefore to record `time_to_ready` as a CI metric and track it over time, just like test duration or artifact size.

---

## Startup Performance Is an Architecture Property { #architecture-property }

It is tempting to treat startup as a final tuning exercise: build the service first, then profile the boot path and shave milliseconds.

Kora takes the opposite approach. Startup follows from architectural decisions:

```text
compile-time graph
+ generated wiring
+ no runtime graph reflection
+ thin adapters
+ limited runtime discovery
+ parallel initialization
= short framework-controlled startup path
```

That is qualitatively different from a framework that performs substantial dynamic work by design and then offers flags to disable parts of it later.

This does not mean every Kora application will start instantly. User code can perform expensive startup operations. Infrastructure can be slow. A database can be unavailable. DNS can time out. Secrets
can come from a remote control plane. A migration can take minutes.

What Kora can do is make the **framework tax** small and make the remaining startup work visible. That is valuable because the team can then reason about the real application-critical path instead of
reverse-engineering framework bootstrap.

---

## The Most Important Metric: Capacity Activation Time { #capacity-activation-time }

For a cloud-native service, the strongest way to summarize startup is:

> **How long does it take to convert requested compute into SLO-compliant serving capacity?**

That metric forces all the right questions:

- Did the autoscaler notice demand?
- Was a node available?
- Was the image local?
- Did the JVM start quickly?
- Did the framework perform runtime discovery?
- Were dependencies initialized?
- Was readiness truthful?
- How soon did Kubernetes observe readiness?
- Did the new replica immediately meet the latency SLO?
- Did startup overload a database or another shared dependency?

Kora improves one important portion of that chain by reducing framework-controlled startup work and minimizing framework warm-up. Because the chain runs during deployments, scaling, restarts, spot
recovery, scale-to-zero activation, and tests, that optimization is repeatedly reused.

The framework's startup benchmark is therefore not primarily a story about impatience at a developer laptop. It is evidence about the cost of creating a new unit of service capacity.

---

## Conclusion { #conclusion }

Fast startup is easy to underestimate because the raw number looks small. Five seconds is nothing compared with the lifetime of a service that runs for weeks. But production infrastructure does not
experience startup only once. It starts replicas continuously as the fleet deploys, scales, recovers, reschedules, tests, and releases idle capacity.

That changes the economics.

During a rolling deployment, readiness controls how quickly replacement replicas can become available and how long the service remains in a transitional capacity state. During HPA scale-out, readiness
is one term in the delay between a demand spike and useful new capacity. For scale-to-zero, startup becomes part of cold-path latency. On spot infrastructure, it affects how rapidly lost capacity can
be restored. In CI, it determines how expensive realistic integration and black-box tests are to execute repeatedly.

Kora's compile-time application graph, generated wiring, lack of runtime graph reflection, parallel initialization, and thin runtime model are important because they remove framework work from all of
those paths. The compile-time cost is paid once; the runtime benefit is collected on every instance start.

The deeper point is not that every application should optimize startup above everything else. It is that **startup and readiness are production capacity characteristics**. When a platform is elastic,
ephemeral, frequently deployed, and heavily tested, time-to-readiness is part of availability, scaling behavior, infrastructure cost, and delivery speed.

A fast local restart is pleasant.

A fast transition from requested replica to trustworthy production capacity is architecture.
