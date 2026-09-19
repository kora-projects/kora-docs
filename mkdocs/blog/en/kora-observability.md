---
title: Observability by Design — One Request Across the Entire Kora Framework Stack
date: 2026-08-22
description: How the Kora Framework threads logging, metrics, and tracing through one request end to end, with consistent context across HTTP, database, clients, and messaging.
search:
  exclude: true
---

# Observability by Design: One Request Across the Entire Kora Stack { #observability-by-design }

**August 22, 2026**

Observability is often added to a backend service after the application already works. First the HTTP endpoint is implemented, then the repository, then the outbound client, and only after the first
serious incident does somebody ask for latency metrics, distributed tracing, structured logs, readiness probes, and a shutdown strategy that does not kill requests in flight. That sequence is
understandable, but operationally backward. By the time a production service is failing, the information required to explain the failure must already exist.

The Kora Framework takes a different view. Observability is part of the service architecture from the beginning. The framework integrates telemetry across modules, Micrometer metrics, OpenTelemetry tracing,
structured logging with trace correlation, liveness and readiness probes on a separate system port, and lifecycle behavior including graceful shutdown.

The important idea is not merely that Kora "supports metrics" or "supports tracing." Almost every modern framework does. The more interesting property is that these signals line up with the real
execution path of the application.

Consider one request:

```text
HTTP server span
      ↓
application service
      ↓
HTTP client span
      ↓
repository span
      ↓
database
```

That same request also contributes to aggregate metrics:

```text
HTTP request latency
HTTP status distribution
outbound client latency
database query duration
connection-pool saturation
JVM / process metrics
business counters and timers
```

and its logs can carry the same trace identity:

```text
traceId
spanId
structured event fields
business context
```

The result is not three unrelated observability products bolted onto the same service. It is one operational model observed from three complementary directions. Metrics tell you **that** something is
wrong. Tracing tells you **where** the time or failure went. Logs tell you **what the code decided while it happened**. Probes tell the platform **whether this process should receive traffic or be
restarted at all**. Graceful shutdown completes the model by defining what happens when the process is intentionally removed from service.

This article follows one request through the Kora stack and uses that path to explain how observability should work in a production backend.

## Observability Is a Runtime Contract { #runtime-contract }

A production service has two contracts. The first is the business contract: endpoints, payloads, status codes, semantics, and latency expectations. The second is operational. The platform and
operators need to know whether the process is alive, whether it is ready, how many requests it serves, how long those requests take, which dependencies are slow, which database query failed, which
request produced a given log line, and whether shutdown is draining traffic safely.

A service that satisfies its business API but cannot answer these questions is incomplete from an operations perspective.

Kora's observability model treats these capabilities as first-class modules and lifecycle concerns rather than optional debugging utilities. That matters because observability is most useful when it
is structurally consistent. If every controller invents its own logging, every repository invents its own metric names, every HTTP client uses a different tracing wrapper, and readiness lives on the
same public port as user traffic, the service technically emits signals but does not have an observability architecture.

Kora tries to provide that architecture across modules.

## One Request Is the Best Way to Understand the Stack { #one-request }

It is easy to discuss metrics, tracing, and logs as separate features. That is not how an incident happens. An incident begins with a request.

Imagine an API endpoint:

```text
GET /users/{id}/dashboard
```

The request enters a Kora HTTP server. The service then loads user information from PostgreSQL, calls a remote recommendation service, combines the results, and returns JSON.

The runtime path is:

```text
Client
  ↓
Kora HTTP server
  ↓
DashboardService
  ├── UserRepository
  │      ↓
  │   PostgreSQL
  │
  └── RecommendationClient
         ↓
      remote service
```

Now add telemetry:

```text
HTTP SERVER SPAN
  GET /users/{id}/dashboard
        ↓
   DashboardService
        ↓
   ┌───────────────┐
   │               │
DB CLIENT SPAN   HTTP CLIENT SPAN
SELECT user     GET /recommendations
   │               │
PostgreSQL      remote service
```

The trace provides a causal picture. Metrics provide aggregate behavior for each edge. Logs explain application decisions occurring inside those spans. This request-centric model is the foundation for
useful observability.

## The HTTP Server Is the First Observability Boundary { #http-server }

The incoming HTTP server is where the service first receives enough information to identify an operation. At minimum, the framework knows the HTTP method, route, request start, request completion,
status code, error, and duration. That is enough to produce both a tracing span and HTTP metrics.

A server span should represent:

```text
GET /users/{id}/dashboard
```

rather than the literal URL:

```text
GET /users/894192/dashboard
```

This distinction matters. Route templates are bounded; raw identifiers are not. A bounded route name works well for span names, metric labels, dashboards, and aggregation. A user ID belongs elsewhere.

This leads to one of the most important observability rules: aggregate on low-cardinality dimensions and attach high-cardinality context only where the backend is designed to handle it.

## Metrics and Traces Observe the Same Operation Differently { #metrics-traces }

For one incoming route, the HTTP server may contribute a metric conceptually like:

```text
http.server.request.duration
```

with dimensions such as:

```text
method=GET
route=/users/{id}/dashboard
status=200
```

and a trace span named:

```text
GET /users/{id}/dashboard
```

These signals answer different questions. The metric can answer, "What is the p95 latency of this route over the last thirty minutes?" The trace can answer, "Why did this specific 1.8-second request
take 1.8 seconds?"

It is a mistake to expect one signal to replace the other. A tracing backend is not a good substitute for cheap aggregate latency histograms. A metric dashboard is not a substitute for a request-level
causal tree. A healthy production stack needs both.

## The Trace ID Becomes the Request's Operational Identity { #trace-id }

Once the HTTP server creates or continues a trace, the request has an operational identity.

Conceptually:

```text
traceId = 79d65...
```

Every child span belongs to that trace. Structured logs emitted while the trace is current can carry:

```text
traceId
spanId
```

This gives operators a join key.

Suppose Grafana shows a spike in HTTP 500 rate. A trace explorer shows one failing request. A database span inside that trace shows a connection-pool timeout. A log line with the same trace ID says
that a fallback was deliberately disabled because the operation is write-sensitive.

Those are no longer independent clues. They belong to one execution.

That correlation is what makes observability operationally powerful.

## Context Propagation Is the Hidden Backbone { #context-propagation }

Distributed tracing looks simple in a diagram:

```text
server span
  ↓
client span
  ↓
remote server span
```

but the important mechanism is context propagation. The current trace context needs to survive through service method calls, virtual-thread execution, repository calls, outbound HTTP calls, and
asynchronous boundaries where applicable. Then the outbound client needs to inject trace context into request headers so the downstream service can continue the same trace.

Without propagation, every layer creates its own isolated root span:

```text
Trace A: incoming HTTP
Trace B: database
Trace C: outgoing HTTP
```

That is not distributed tracing. It is distributed span generation.

Kora's telemetry integrations matter because the framework modules participate in one context model instead of forcing every business method to manually forward trace IDs.

## The Service Layer Should Not Need Telemetry Plumbing Everywhere { #service-layer }

A well-designed observability stack should make infrastructure operations observable automatically. Business code should not repeatedly call `startHttpSpan()`, `recordHttpMetric()`,
`putTraceIdIntoMdc()`, or duplicate repository timing logic around every operation.

Kora's module-level telemetry is intended to handle infrastructure boundaries automatically. The HTTP server knows when a request starts and ends. The HTTP client knows when an outbound call starts
and ends. The database integration knows when a query acquires a connection, begins execution, succeeds, or fails.

Those components are in the best position to emit standardized infrastructure telemetry.

Business code should add telemetry only where the framework cannot know the semantic meaning.

That division of responsibility is important.

## Infrastructure Telemetry Versus Business Telemetry { #infra-vs-business }

Framework telemetry can know that an HTTP request completed in 42 ms, a database query took 8 ms, or an outbound HTTP call returned 503. It cannot know that a payment was approved, an order was
rejected because the risk score exceeded a threshold, a customer upgraded a subscription, or an inventory reservation succeeded.

Those are business semantics.

A strong Kora service therefore has two telemetry layers. The first is framework-provided infrastructure telemetry. The second is application-defined business telemetry.

For example:

```text
HTTP:
GET /users/{id}

Business:
subscription.lookup

Database:
UserRepository.findById

Outbound:
GET /billing/profile
```

This creates a useful trace without instrumenting every function. The goal is not maximum span count. The goal is maximum explanatory value.

## Do Not Turn Every Method into a Span { #method-spans }

Distributed tracing becomes less useful when every tiny helper method creates a span.

A bad trace can look like:

```text
HTTP span
  ↓
controller span
  ↓
service span
  ↓
validate span
  ↓
map span
  ↓
format span
  ↓
repository span
```

This produces visual noise and telemetry cost without adding much operational information.

A span should usually represent a meaningful operation boundary. Good candidates include incoming protocol operations, outgoing network calls, database queries, message processing, significant
business operations, and expensive internal computation. Trivial getters and mapping functions generally do not need spans.

Kora can automatically instrument infrastructure boundaries and provides tracing APIs for meaningful business spans. That is a good balance.

## Manual Business Spans Should Explain the Domain { #business-spans }

Suppose the request performs a business operation called:

```text
user.dashboard.build
```

A manual child span can represent it:

```text
HTTP SERVER
GET /users/{id}/dashboard
  ↓
BUSINESS
user.dashboard.build
  ├── DB CLIENT
  │   UserRepository.findById
  │
  └── HTTP CLIENT
      GET /recommendations
```

The business span gives the trace semantic structure. Now an operator can distinguish the transport boundary, business operation, and infrastructure dependencies without instrumenting every internal
method.

Kora's tracing helpers are useful because they can nest a manual span under the currently active request span rather than forcing application code to reconstruct context manually.

## Span Attributes Are Not Metric Tags { #span-attributes }

Suppose the request has:

```text
userId=982374723
```

Adding that to a span can be reasonable when it is operationally useful:

```text
user.id=982374723
```

Adding it as a metric tag can be catastrophic. A metrics backend might create one time series per user ID.

A useful rule is:

```text
bounded dimensions
→ metrics

request-specific / high-cardinality values
→ traces or logs
```

Kora can provide the plumbing, but application teams still need cardinality discipline.

## Metrics Answer Questions About Populations { #metric-populations }

Metrics are aggregate signals. They describe populations of operations over time.

For the incoming HTTP route, useful metrics include request rate, error rate, latency distribution, active requests, and status distribution. For an outbound client, useful metrics include request
rate, response status, latency, and timeouts. For PostgreSQL, useful metrics include query duration, connection-pool state, and acquisition pressure. For the JVM, useful metrics include CPU, heap, GC,
threads, file descriptors, and uptime.

A dashboard built from these signals tells you how the service behaves as a system.

## Histograms Matter More Than Averages { #histograms }

Averages hide tail latency.

Consider ten requests:

```text
9 requests = 10 ms
1 request  = 910 ms
```

The average is 100 ms, but no user actually experienced 100 ms. Most saw 10 ms. One saw almost a second.

Production systems care about distributions.

That is why latency metrics need SLO-oriented histogram buckets and percentile analysis. Questions such as "what is p95?" or "what percentage completes below 100 ms?" are much more useful than "what
is the average latency?"

Micrometer gives Kora a strong metrics surface for this kind of operational analysis.

## SLO Buckets Should Reflect Actual Objectives { #slo-buckets }

Default buckets are a starting point, not a universal truth. If an internal lookup endpoint has an SLO of 50 ms, a histogram that only distinguishes one second, five seconds, and ten seconds is
operationally weak.

Useful buckets might be:

```text
10 ms
25 ms
50 ms
100 ms
250 ms
```

for a fast endpoint, while a batch API may need completely different thresholds.

Observability becomes useful when metric configuration reflects service objectives rather than framework defaults alone.

## The HTTP Client Is the Next Major Boundary { #http-client }

Now continue the request. The dashboard service calls:

```text
RecommendationClient.getRecommendations(userId)
```

Kora's HTTP client telemetry can observe that outgoing operation.

The trace becomes:

```text
HTTP SERVER
GET /users/{id}/dashboard
  ↓
HTTP CLIENT
GET /recommendations
```

The client span should be a child of the current request trace. Trace context is then propagated over HTTP. The remote service receives the request and creates or continues its server span.

One trace can cross process boundaries:

```text
service A server span
  ↓
service A client span
  ↓
service B server span
  ↓
service B database span
```

This is the core value of distributed tracing.

## Client Metrics Explain Dependency Health in Aggregate { #client-metrics }

The outbound call also contributes aggregate metrics.

A client metric can answer:

```text
How often does Recommendation Service fail?
Did its p95 latency increase from 60 ms to 400 ms?
How many timeouts occurred?
```

These questions are expensive to answer from logs alone.

Every major remote dependency should have a useful operational view of rate, errors, duration, and where appropriate saturation.

Kora's HTTP client telemetry provides a consistent place for those signals.

## Tracing Explains Which Dependency Dominated One Request { #tracing-dependency }

Metrics may show that recommendation-client p95 is 700 ms. But imagine one user reports a 2.2-second request.

The trace can show:

```text
HTTP SERVER              2200 ms
└─ dashboard.build       2190 ms
   ├─ PostgreSQL            9 ms
   └─ Recommendation     2160 ms
```

Now the problem is immediately localized. The repository is not slow. JSON serialization is not consuming two seconds. The remote dependency dominates the latency budget.

That is the difference between aggregate detection and causal diagnosis.

## Client Logging Should Be Deliberately Bounded { #client-logging }

HTTP client logging is useful, but dangerous.

Requests may contain authorization headers, cookies, personal data, large JSON payloads, or binary bodies. Production logging therefore needs masking and size limits.

The goal is not to log every byte of every network operation. The goal is to log enough structured context to explain behavior safely.

Useful fields can include:

```text
client name
operation
method
route
status
duration
error type
traceId
```

Headers and bodies should be logged only when there is a clear reason and appropriate masking.

Observability that leaks credentials is not observability. It is an incident.

## The Repository Is Another Observability Boundary { #repository }

Now follow the other branch:

```text
UserRepository.findById(userId)
```

A generated Kora repository executes a JDBC query. That operation should be observable independently from the parent HTTP request.

The trace can contain:

```text
HTTP SERVER
GET /users/{id}/dashboard
  ↓
DB CLIENT
UserRepository.findById
```

The query also contributes to database metrics.

This matters because databases frequently dominate backend performance. If the repository layer is dark, one of the most important request boundaries is invisible.

## Database Telemetry Should Describe the Operation, Not Only the Driver { #database-telemetry }

Database telemetry can observe several meaningful phases:

```text
connection acquired
statement execution begins
query succeeds
query fails
operation ends
```

That distinction allows operators to separate waiting for a connection from the database actually executing a query.

Those are different problems.

If latency rises because the pool is saturated, adding an index may do nothing. If execution itself is slow, increasing pool size may make the system worse.

Good database observability helps distinguish resource waiting from actual database work.

## Stable Query Identity Is Better Than Unlimited SQL Labels { #query-identity }

Metrics need bounded identifiers.

A repository operation such as:

```text
UserRepository.findById
```

or a stable query ID works well for aggregation.

Full SQL text is usually a poor metric label because it may be long, dynamic, or high-cardinality.

A good design is:

```text
metrics:
stable operation identity

logs/traces:
richer query context when needed

TRACE logging:
full SQL where safe
```

This keeps dashboards useful without turning every slightly different query into a separate time series.

## SQL Logging Should Be a Debugging Instrument { #sql-logging }

Logging every SQL body at normal production levels can create large log volume, storage cost, and sensitive-data risk.

A better hierarchy is:

```text
INFO/DEBUG:
operation identity, duration, failure

TRACE:
full SQL text where appropriate
```

The exact policy depends on environment and security requirements.

Kora's database telemetry supports the broader principle that structured query metadata and detailed SQL should not be conflated.

## Database Metrics Complete the Request Latency Picture { #database-metrics }

Suppose HTTP latency rises and tracing shows the database span is responsible.

Database metrics can answer whether this is one anomalous query or a fleet-wide slowdown.

For example:

```text
db.client.operation.duration p95 rising
connection pool active = max
acquisition latency rising
```

suggest saturation.

While:

```text
pool healthy
one query operation slow
```

suggests a query-plan or data-shape problem.

Observability works by narrowing the hypothesis space.

## The Full Trace Is an Execution Graph { #execution-graph }

For our example request, the trace may look like:

```text
HTTP SERVER
GET /users/{id}/dashboard
│
└── BUSINESS
    user.dashboard.build
    │
    ├── DB CLIENT
    │   UserRepository.findById
    │
    └── HTTP CLIENT
        GET /recommendations
        │
        └── downstream service spans...
```

Each node answers:

```text
How long did this step take?
Did it fail?
Which attributes describe it?
```

The tree answers:

```text
How did this request spend its latency budget?
```

This is why tracing is one of the best tools for debugging distributed latency.

## Latency Budgeting Becomes Visible { #latency-budgeting }

Suppose the request SLO is:

```text
p95 < 300 ms
```

The trace shows:

```text
HTTP total             260 ms
business overhead       10 ms
database                20 ms
remote HTTP            220 ms
serialization            5 ms
other                    5 ms
```

Now the service has only 40 ms of remaining budget before violating the SLO.

Observability turns latency into an engineering budget rather than an intuition.

Without trace structure, teams often optimize the wrong layer.

## Parallel Work Appears Clearly in Traces { #parallel-work }

If independent operations run in parallel using virtual threads or structured concurrency, a trace can reveal the overlap.

For example:

```text
HTTP SERVER                     180 ms
└─ dashboard.build              170 ms
   ├─ DB user                    60 ms
   └─ HTTP recommendations      150 ms
```

If both children start at nearly the same time, total latency is closer to the maximum child duration than their sum.

A trace visualization makes that obvious.

This is another reason context propagation across concurrent tasks matters: without it, parallel child work can become disconnected from the parent request.

## Virtual Threads Do Not Remove the Need for Context Propagation { #virtual-threads }

Kora 2's virtual-thread-oriented architecture simplifies synchronous programming, but virtual threads do not automatically make observability context correct.

Framework integration still needs to ensure that trace state, logging context, and other request-scoped data follow execution.

The benefit is that synchronous call stacks and thread-per-task semantics are often easier to understand than deeply asynchronous callback chains.

Observability should exploit that simplicity rather than reintroducing manual context plumbing.

## Structured Logs Are Not Just JSON Logs { #structured-logs }

Structured logging is sometimes reduced to "we output JSON." That misses the point.

A useful structured log has stable semantic fields.

For example:

```json
{
    "level": "WARN",
    "event": "recommendation_fallback",
    "userId": "982374723",
    "reason": "timeout",
    "traceId": "79d65...",
    "spanId": "03fa..."
}
```

The important property is not the braces. It is that the log can be queried by fields and correlated with a trace.

Human-readable messages can still exist. Structured fields make the event operationally searchable.

## Logs Should Record Decisions, Not Every Function Entry { #log-decisions }

A common anti-pattern is:

```text
Entering method A
Leaving method A
Entering method B
Leaving method B
```

Distributed tracing already describes execution shape more effectively.

Logs should record information the trace cannot infer.

Good examples include:

```text
fallback selected
risk policy rejected transaction
cache entry invalidated
remote response ignored because version stale
business state transition refused
configuration mode selected
```

The trace tells you where execution went.

The log tells you why the code chose that path.

That separation keeps log volume manageable.

## Trace Correlation Makes Logs Dramatically More Valuable { #trace-correlation }

Without trace correlation, a log such as:

```text
Recommendation timed out
```

may require searching around a timestamp and guessing which request produced it.

With:

```text
traceId=79d65...
```

the workflow becomes:

1. open the slow trace;
2. query logs by trace ID;
3. read application decisions for exactly that request.

This is one of the highest-leverage improvements a service can make to its logging model.

## Metrics Are Usually the First Incident Signal { #incident-signal }

Imagine the recommendation dependency becomes slow.

The first sign may be a dashboard:

```text
GET /users/{id}/dashboard
p95 latency:
120 ms → 850 ms
```

or an SLO burn-rate alert.

Metrics are ideal for detection because they are cheap to aggregate continuously.

They answer:

```text
Is something wrong?
How widespread is it?
When did it begin?
```

They usually do not answer why.

That is when traces and logs take over.

## Traces Narrow the Incident { #traces-narrow }

From the metric alert, an operator inspects representative slow traces.

Several show:

```text
RecommendationClient = 700 ms
Database = 10 ms
```

Now the incident scope narrows:

```text
incoming server healthy
database healthy
remote recommendation dependency slow
```

The service can focus immediately on the correct dependency.

This is observability doing useful work rather than simply generating data.

## Logs Explain Application Reaction { #logs-explain }

The same trace may contain:

```text
event=recommendation_fallback
reason=deadline_exceeded
fallback=empty_recommendations
```

Now the operator knows not only that the remote dependency was slow but also how the application reacted.

Maybe the endpoint still returned HTTP 200 with degraded data. Maybe it returned 503. Maybe fallback was disabled for a subset of requests.

Metrics and spans cannot always explain these application decisions. Logs can.

## Observability Is Most Powerful When Signals Agree { #signals-agree }

A well-instrumented incident may provide:

### Metric { #metric }

```text
http.server.request.duration p95 = 850 ms
```

### Trace { #trace }

```text
RecommendationClient span = 720 ms
```

### Client metric { #client-metric }

```text
http.client.request.duration p95 = 710 ms
```

### Log { #log }

```text
recommendation_fallback reason=timeout
```

### Downstream trace { #downstream-trace }

```text
database pool wait = 650 ms
```

Now the causal chain can continue across services.

Each signal corroborates and refines the others.

## Probes Solve a Different Problem { #probes }

Metrics, traces, and logs are primarily for humans and monitoring systems.

Probes are control signals for the platform.

A liveness probe asks:

```text
Should this process continue to exist?
```

A readiness probe asks:

```text
Should this instance receive traffic right now?
```

Confusing these questions can create serious production incidents.

Kora exposes them as distinct operational concepts.

## Liveness Should Be Conservative { #liveness }

A liveness failure can cause Kubernetes or another supervisor to restart the process.

That is a powerful action.

Therefore liveness should represent a condition that restarting the process can plausibly fix.

A temporary database outage is usually not a good liveness failure.

Imagine one hundred replicas and a two-second database network interruption. If every application fails liveness because the database is temporarily unreachable, the orchestrator may restart the whole
fleet.

Now a brief dependency problem has become a restart storm.

Observability controls can amplify failures if they are modeled incorrectly.

## Readiness Is About Traffic Admission { #readiness }

Readiness is a better place for temporary conditions that make an instance unsuitable for serving traffic.

During startup:

```text
application graph initializing
database pool warming
required dependency unavailable
```

the process may be alive but not ready.

During shutdown, readiness should eventually stop advertising the instance for new traffic while in-flight work drains.

The core rule is:

```text
alive
≠
ready
```

A process can be perfectly alive while intentionally not serving traffic.

## Probes Belong on a Separate System Port { #system-port }

Operational endpoints generally should not be exposed on the same public interface as business traffic.

A clean deployment can use:

```text
public port
8080

system port
8085
```

with system endpoints such as:

```text
/metrics
/system/liveness
/system/readiness
```

This creates a useful security and topology boundary.

Business clients reach the public API.

Prometheus, kubelet, sidecars, and monitoring agents reach the system API.

This separation should be designed from the start rather than patched into ingress rules later.

## The System Port Is Part of Production Architecture { #system-port-architecture }

A service diagram should not show only:

```text
Client → 8080
```

It should also show:

```text
Prometheus → 8085 /metrics
Kubernetes → 8085 /system/readiness
Kubernetes → 8085 /system/liveness
```

These are real production traffic paths.

If network policy or service-mesh configuration blocks them, the application can be functionally correct while operationally broken.

Operational endpoints are deployment architecture.

## Readiness Is Part of Startup Performance { #readiness-startup }

Kora emphasizes fast startup, but the operationally meaningful metric is not:

```text
main() started
```

It is:

```text
instance is ready to receive traffic
```

A JVM can boot quickly and still spend twenty seconds waiting on initialization before readiness.

From the platform's perspective, that is a twenty-second startup.

This is why readiness belongs in startup benchmarks and deployment SLOs.

## Readiness Is Also Part of Autoscaling { #readiness-autoscaling }

Suppose the horizontal autoscaler adds ten Pods during a spike.

Those Pods provide useful capacity only after becoming ready.

If readiness arrives quickly, the new instances can absorb the spike.

If readiness takes tens of seconds, the autoscaler reacts too slowly and existing instances remain overloaded.

Here observability is not merely diagnostic.

The readiness signal directly participates in capacity management.

## Graceful Shutdown Completes the Lifecycle { #graceful-shutdown }

Starting correctly is only half of production lifecycle behavior.

Services also need to stop correctly.

A dangerous shutdown sequence is:

```text
termination signal
  ↓
kill server immediately
  ↓
drop in-flight requests
```

A safer sequence is:

```text
termination begins
  ↓
stop accepting new work / become unready
  ↓
allow in-flight work to finish
  ↓
close resources
  ↓
exit
```

Kora's HTTP server includes graceful-shutdown behavior with a configurable wait period.

That is an operational feature and an availability feature.

## Graceful Shutdown Should Preserve Trace Completion { #shutdown-trace-completion }

Imagine a request is in progress when deployment begins.

The service has already created:

```text
HTTP server span
database span
remote client span
```

If the process dies abruptly, telemetry may be incomplete. The client can receive a reset. The server span may never export. A transaction may be interrupted.

A graceful drain increases the chance that the request completes, spans close, logs flush, and telemetry exporters send buffered data before the process exits.

Observability and shutdown behavior reinforce each other.

## Exporters Need Shutdown Semantics Too { #exporter-shutdown }

Tracing exporters often buffer spans before sending them. Logging appenders may buffer. Other telemetry components may own resources.

A correct application lifecycle should give those components an opportunity to flush and stop cleanly.

This is another reason observability should live in the application graph and lifecycle instead of ad hoc static initialization.

If infrastructure is a real component, the framework can manage startup and shutdown ordering.

## Application Graph Lifecycle Helps Operations { #graph-lifecycle }

Kora's graph model is useful operationally because components have explicit dependencies and lifecycle.

A simplified graph may look like:

```text
HTTP server
  ↓
controllers
  ↓
services
  ↓
repositories / clients
  ↓
database / network resources

telemetry
  ↓
MeterRegistry / Tracer / logging
```

Initialization and shutdown can follow known dependency relationships.

Infrastructure does not need to guess which runtime singleton should stop first.

## Observability Should Be Modular but Consistent { #modular-consistent }

Kora's module system allows services to enable only what they need.

That is useful because not every application has exactly the same integrations.

But modularity should not produce incompatible telemetry conventions.

JDBC, Kafka, HTTP, gRPC, scheduling, and other integrations should still share common operational ideas:

```text
logging
metrics
tracing
context
operation identity
duration
error
```

This consistency reduces the number of custom wrappers each team needs to invent.

## One Telemetry Model Across Modules Reduces Platform Fragmentation { #telemetry-model }

Imagine a company with two hundred services.

If every team implements HTTP metrics differently, database metrics differently, and Kafka tracing differently, the platform team cannot build reusable dashboards or runbooks.

Framework-level conventions allow common operational views:

```text
request rate
error rate
dependency latency
database duration
consumer processing
```

This is an organizational advantage much larger than the convenience of any individual metric API.

## Micrometer and OpenTelemetry Form a Pragmatic Stack { #micrometer-otel }

Kora uses Micrometer for metrics and OpenTelemetry for tracing and semantic conventions.

This is a pragmatic JVM combination.

Micrometer is deeply established for Prometheus-oriented metrics. OpenTelemetry provides a vendor-neutral tracing model and common semantic language.

The important architectural property is not brand selection. It is that the framework uses widely understood standards rather than inventing a proprietary telemetry world.

That keeps the observability backend replaceable.

## Observability Should Not Lock the Service to One Vendor { #vendor-lock }

A service should be able to send traces to Jaeger, Tempo, a managed observability vendor, or another OpenTelemetry-compatible backend without rewriting business code.

Similarly, Prometheus-style metrics can be consumed by a large ecosystem.

Vendor-neutral instrumentation reduces the cost of changing the backend later.

The framework should own instrumentation semantics, not vendor lock-in.

## Metric Names and Semantic Conventions Matter { #metric-names }

A metric is not useful merely because it exists.

Names and dimensions need stable meaning.

For example:

```text
http.server.request.duration
```

is much more reusable than:

```text
my_http_timer_2
```

Common semantic conventions let dashboards and alerts work across services and reduce documentation burden.

Consistency is a force multiplier.

## Business Metrics Need Even More Discipline { #business-metrics }

Framework metrics come with defined semantics.

Business metrics do not.

Suppose an application creates:

```text
orders.created
```

The team needs to define exactly when this increments.

Before transaction commit?

After commit?

On retry?

Does an idempotent replay count again?

Without a precise definition, the metric can look authoritative while measuring the wrong thing.

Business telemetry should be treated as an API.

## Avoid Counting One Business Event at Several Layers { #double-counting }

A common mistake is incrementing:

```text
order.created
```

in the controller, service, and event publisher.

Now one semantic event may be counted multiple times.

Infrastructure metrics belong at infrastructure boundaries.

Business metrics should live at the semantic point where the event becomes true.

For order creation, that may be after a successful transaction commit.

The exact location depends on the domain.

## Logs Need Stable Event Names Too { #event-names }

A structured log is easier to query when it contains:

```text
event=order_creation_failed
```

than when the message varies between:

```text
Could not create order
Order creation error
Failed creating order
```

Human-readable messages can change.

Stable event fields provide machine-readable semantics.

This makes incident search and alerting more reliable.

## Trace Sampling Changes What Traces Can Tell You { #trace-sampling }

Metrics are usually designed to represent every operation.

Traces may be sampled.

That means tracing should not be the aggregate source of truth for questions such as:

```text
How many requests failed?
```

If only a fraction of traces are retained, counting errors in traces is misleading.

Metrics remain the aggregate truth.

Tracing provides detailed examples and causal paths.

The signals are complementary.

## Error Traces May Deserve Different Sampling { #error-sampling }

A production tracing strategy may retain all errors, a fraction of normal requests, and a higher share of slow requests, depending on backend capabilities.

The framework's job is to emit correct trace data.

Sampling policy belongs to the platform.

For high-volume systems, sampling has a direct cost impact.

## High-Cardinality Logs Also Cost Money { #high-cardinality }

Moving a user ID out of metric tags and into logs does not make it free.

Logs still consume storage and indexing.

The difference is that log systems are designed for event-level records, while metrics systems are optimized around bounded time-series dimensions.

Teams should still avoid logging identifiers that provide no operational value.

Observability should be intentional.

## PII and Secrets Need Explicit Policy { #pii-secrets }

Observability data often leaves the application and enters centralized systems.

That means traces and logs can become secondary data stores.

Headers such as:

```text
Authorization
Cookie
Set-Cookie
API keys
```

must be masked.

Bodies can contain personal, financial, or credential data.

Span attributes also need review.

The observability pipeline deserves the same security discipline as any other data system.

## Logging Levels Should Have Operational Meaning { #logging-levels }

A useful convention might be:

```text
ERROR
unexpected operation failure requiring attention

WARN
degraded behavior or recoverable anomaly

INFO
meaningful lifecycle or business event

DEBUG
diagnostic context normally disabled

TRACE
very detailed protocol/query information
```

If every routine request logs at INFO, meaningful information events disappear in noise.

Kora can provide module logging. Teams still need to define what levels mean operationally.

## HTTP Request Logs Should Not Replace HTTP Metrics { #request-log-vs-metrics }

It is possible to calculate request rate by logging every request and aggregating the logs.

It is usually a poor substitute for a metric.

Metrics are designed for aggregate rate, errors, and latency distributions.

Use logs when individual request records are actually needed.

Use metrics for aggregate health.

The same principle applies to database operations.

## Probes Should Not Become Dependency Monitoring { #probe-dependency }

A readiness probe can include selected dependency state when serving traffic is impossible without that dependency.

But probes should not become a complete monitoring system.

If a readiness request synchronously checks ten downstream services, the probe itself becomes fragile and slow.

Dependency monitoring belongs primarily in metrics, tracing, resilience state, and alerts.

Probe design should remain focused on process health and traffic admission.

## Readiness Can Represent Warm-Up Explicitly { #readiness-warmup }

Some applications have legitimate warm-up:

```text
load configuration
initialize connection pool
preload essential data
build local indexes
```

During that time:

```text
liveness = healthy
readiness = false
```

Once the application can satisfy its serving contract:

```text
readiness = true
```

This is far better than arbitrary startup sleeps.

The application tells the platform the truth about its state.

## False Readiness Is Worse Than Slow Readiness { #false-readiness }

A service that reports ready before it can handle real traffic may receive requests while critical resources are still unusable.

The first users after deployment pay the initialization cost or receive errors.

Fast readiness is valuable only if it is truthful.

Kora's fast startup architecture should be paired with realistic readiness semantics.

## Probes Need Their Own SLO { #probe-slo }

Operational endpoints need to be fast.

If readiness itself takes three seconds because it performs heavyweight diagnostics, the orchestrator cannot make quick decisions.

Probe endpoints should usually return from state the application already maintains rather than performing expensive synchronous work on every call.

This keeps orchestration responsive.

## Graceful Shutdown Has a Budget { #shutdown-budget }

Kora's HTTP server can wait for in-flight processing during shutdown.

That wait cannot be infinite.

The platform also has a termination grace period.

The lifecycle needs a budget:

```text
time to become unready
+
load-balancer propagation
+
in-flight drain
+
resource shutdown
<
platform termination grace period
```

If the application waits longer than the orchestrator allows, it may still be killed.

Graceful shutdown has to be designed against the deployment environment.

## Long Requests Complicate Graceful Shutdown { #long-requests }

Suppose an endpoint can run for two minutes while termination grace is thirty seconds.

No framework can magically guarantee every request completes during rollout.

The service needs an explicit strategy:

- make the operation idempotent;
- increase the grace period;
- move long work to a job system;
- checkpoint progress;
- stop admitting long work before shutdown.

Graceful shutdown is architecture, not merely an HTTP server setting.

## Scheduled Jobs and Consumers Need Shutdown Semantics Too { #scheduled-jobs }

The same lifecycle concern exists outside HTTP.

A scheduler may have running jobs.

A Kafka consumer may be processing a record.

A database operation may be in flight.

Each module needs to define whether it waits for current work, interrupts it, commits progress, or retries elsewhere.

A shared lifecycle model makes shutdown coherent across the whole application.

## Messaging Observability Follows the Same Pattern { #messaging }

The article is centered on an HTTP request, but the same architecture applies to Kafka or other messaging.

A consumer operation has:

```text
message receive
processing
outbound calls
database work
ack / commit
```

It needs duration metrics, error metrics, tracing/context where appropriate, structured logs, and lifecycle behavior.

Framework-wide telemetry consistency means developers do not need a new observability philosophy for every integration.

## gRPC Is the Same Story at Another Protocol Boundary { #grpc }

A gRPC server call is another incoming operation.

A gRPC client is another outbound dependency.

The protocol differs, but the observability pattern does not:

```text
incoming server span
  ↓
business work
  ↓
outgoing client span
  ↓
repository span
```

This commonality matters for platforms supporting mixed protocols.

## Observability Should Follow Real Technology Boundaries { #technology-boundaries }

Kora's thin-abstraction philosophy is useful here.

Operators already understand:

```text
HTTP
JDBC
Kafka
gRPC
```

Telemetry should describe those technologies directly.

A database query should look like a database query.

An HTTP client call should look like an HTTP client call.

A Kafka consumer should look like message processing.

This lets engineers reason using transferable technology knowledge rather than framework-specific terminology.

## The Framework Should Instrument Where It Has the Best Context { #best-context }

Instrumentation quality is highest close to the operation.

The HTTP server knows the route template.

The generated HTTP client knows the client method and route.

The repository knows the query identifier.

The scheduler knows the job identity.

The Kafka integration knows the consumer operation.

This allows Kora to emit stable operation names without forcing application developers to reconstruct them manually.

That is one of the strongest arguments for framework-level observability.

## Custom Telemetry Components Are an Escape Hatch { #custom-telemetry }

Default telemetry should be useful for most services.

Organizations may still need custom metric tags, special structured-log fields, custom operation naming, proprietary correlation data, or organization-wide masking policy.

Kora's application graph model makes telemetry components replaceable or customizable.

This follows the same pattern as the rest of the framework: strong defaults, explicit components, replaceable implementation.

## Customization Should Improve Consistency, Not Fragment It { #customization }

If every service replaces the database logger differently, the platform loses the value of standardization.

Customization is most valuable when it enforces company-wide rules:

```text
service metadata
environment
region
team
operation naming
masking policy
```

Extension points should be used centrally where possible.

## Service Identity Must Be Correct { #service-identity }

Tracing backends need to know which service produced a span.

Metrics platforms need stable service identity.

Logs need source identity.

Operational metadata commonly includes:

```text
service.name
service.version
environment
region / datacenter
instance identity
```

The exact schema depends on platform conventions.

If service identity is inconsistent, cross-service observability becomes painful.

## Version Metadata Is Essential During Rollouts { #version-metadata }

Suppose error rate rises during deployment.

If telemetry carries application version, operators can compare:

```text
version A
error rate 0.1%

version B
error rate 7%
```

Now rollback confidence is high.

Without version dimensions, the regression appears as a generic service problem.

Observability should answer:

```text
Did this deployment cause the incident?
```

quickly.

## Instance Identity Is Useful but Expensive { #instance-identity }

Instance-level diagnosis sometimes matters:

```text
one Pod has abnormal latency
```

But instance IDs create high-cardinality dimensions.

They may belong in logs, traces, or selected infrastructure metrics rather than every application metric.

Cardinality should be treated as a budget.

## Observability Cost Is a Real Production Cost { #observability-cost }

A service can spend significant money on:

- log ingestion;
- trace storage;
- metric cardinality;
- network export;
- backend compute.

"More telemetry" is not automatically better.

The goal is:

```text
maximum operational information
per unit of telemetry cost
```

Framework-standardized telemetry helps because it provides high-value signals without every team independently over-instrumenting.

## Metrics Need Cardinality Budgets { #cardinality-budgets }

A platform should have explicit rules.

Do not casually tag metrics with:

```text
userId
requestId
orderId
sessionId
raw URL
exception message
```

Safer dimensions include:

```text
route template
HTTP method
status
operation name
client name
database system
bounded error type
```

A metric with unbounded labels is a production risk.

## Trace Attributes Need Payload Budgets Too { #trace-attributes }

Tracing backends also have limits and cost.

A span with hundreds of attributes or large request bodies is expensive.

Attach fields that explain or filter the operation.

Do not duplicate the full application payload into telemetry.

The same rule applies to logs.

Observability should preserve meaning, not reproduce every byte of business data.

## Metrics, Logs, and Traces Should Share Vocabulary { #shared-vocabulary }

Suppose the outbound operation is:

```text
RecommendationClient.getRecommendations
```

It is helpful if the signals describe the same conceptual operation consistently.

For example:

```text
span:
GET /recommendations

metric:
client=RecommendationClient
route=/recommendations

log:
operation=getRecommendations
```

The schemas need not be identical.

They should be mutually understandable.

## Error Classification Should Be Consistent { #error-classification }

One module might report:

```text
timeout
```

another:

```text
SocketTimeoutException
```

and a log:

```text
deadline_exceeded
```

Those may describe the same operational failure.

Metrics benefit from bounded error categories.

Traces and logs can retain detailed exception information.

A platform should normalize error vocabulary where useful without discarding rich diagnostic detail.

## Exceptions Should Not Become Metric Tags Directly { #exception-tags }

Raw exception messages are unstable and often high-cardinality.

Metrics should generally use bounded error categories.

Traces and logs are better places for stack traces and detailed exception information.

This is another example of giving each signal the type of information it handles best.

## RED Fits HTTP Services Well { #red }

A basic service dashboard can begin with RED:

```text
Rate
Errors
Duration
```

For each important route:

```text
requests/sec
error rate
latency histogram
```

This answers most first-level service-health questions.

Then resource dashboards add saturation signals such as CPU, heap, database pools, and file descriptors.

Kora's standard telemetry provides much of the raw material.

## USE Fits Resources { #use }

For resources such as connection pools and CPUs, USE is helpful:

```text
Utilization
Saturation
Errors
```

For a JDBC pool:

```text
utilization:
active connections / max

saturation:
waiters / acquisition latency

errors:
connection / query failures
```

Combining RED for service operations with USE for scarce resources gives operators a disciplined investigation model.

## A Good Dashboard Mirrors the Request Path { #dashboard }

For our example service, a useful dashboard hierarchy looks like this.

Incoming:

```text
HTTP RPS
HTTP error rate
HTTP p50/p95/p99
active requests
```

Business:

```text
dashboard builds
fallback usage
business failures
```

Outgoing HTTP:

```text
RecommendationClient RPS
status distribution
timeouts
latency
```

Database:

```text
query duration
connection-pool usage
acquisition latency
query errors
```

Runtime:

```text
CPU
heap
GC
threads / carrier behavior where relevant
uptime
file descriptors
```

The dashboard follows the same mental path as the code.

That makes incident navigation intuitive.

## Alerting Should Start from User Impact { #alerting }

Not every metric deserves an alert.

Useful alert conditions often include:

```text
SLO burn rate
sustained error rate
readiness failure
pool saturation with latency impact
dependency timeout rate
resource exhaustion
```

A brief CPU spike may not require action if latency and error rate remain healthy.

Alert on symptoms that matter to users, then use internal metrics for diagnosis.

## Traces Are Especially Valuable After an Alert { #traces-after-alert }

A strong incident workflow is:

```text
alert
  ↓
metric dashboard
  ↓
representative trace
  ↓
logs for trace
  ↓
dependency / resource dashboard
```

Each step narrows the problem.

Kora's module-level telemetry supports this workflow because the major request boundaries are already instrumented.

## Logs Should Be Searchable by Trace ID { #logs-searchable }

If logs include `traceId` and `spanId` as structured fields, the observability UI can link between a trace and its logs.

Instead of guessing around a timestamp, the operator searches:

```text
traceId=79d65...
```

and gets exactly the relevant events.

This is one of the most valuable integrations between tracing and logging.

## Do Not Manually Concatenate Trace IDs Everywhere { #trace-id-concatenation }

Application code should not repeatedly do:

===! ":fontawesome-brands-java: `Java`"

    ```java
    log.info("traceId={} ...", traceId);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    log.info("traceId={} ...", traceId)
    ```

The logging integration should enrich records from the current context automatically.

Business code should log business fields and events.

The framework should provide correlation identity.

That separation keeps logging consistent.

## Observability Must Survive Failure Paths { #failure-paths }

Instrumentation is easiest to implement on success.

Its value is highest on failure.

Every observation needs a clear end path when:

- a handler throws;
- an HTTP client times out;
- a database query fails;
- cancellation occurs;
- fallback executes.

Spans should end.

Errors should be recorded.

Metrics should reflect failure.

Logs should preserve context.

Framework-level observation abstractions help centralize this correctness.

## Always Closing the Observation Is a Hidden Correctness Rule { #closing-observation }

Conceptually, instrumentation does:

```text
observation.start()
try
    operation()
catch
    observation.error(...)
finally
    observation.end()
```

If the observation is not ended on an exception, metrics and spans become misleading.

This is exactly the kind of repetitive correctness code that belongs in framework telemetry rather than every business method.

## Disabled Telemetry Should Become Cheap { #disabled-telemetry }

Sometimes a signal is intentionally disabled for a module.

A good implementation should not continue expensive body capture or string formatting only to discard the result.

Kora modules can use no-op telemetry paths when signals are disabled.

That matters because observability configuration should have predictable runtime cost.

## But Turning Everything Off Is Usually a False Economy { #false-economy }

A service may save a small amount of CPU by disabling observability and then lose hours during the next incident.

A better pattern is:

```text
metrics always on
basic tracing on with sensible sampling
structured INFO/WARN logs
body logging off
very verbose SQL logging off
```

Keep high-value, low-cost signals available. Control expensive detail with configuration and sampling.

## Production Defaults Should Favor Safe Visibility { #production-defaults }

Framework defaults matter because many services do not customize every setting.

Safe defaults should avoid:

- leaking secrets;
- unbounded metric labels;
- huge payload logging;
- excessive trace attributes.

At the same time they should provide enough information to operate the service.

Observability should be safe by default, not absent by default.

## Local Development Should Use the Same Signals { #local-development }

Observability is easier to trust when developers use it before production.

A local environment can run:

```text
service
Prometheus-style metrics
Jaeger / Tempo / collector
structured logs
```

Then a developer can send one request and inspect its trace, metrics, logs, and probes.

This makes telemetry part of normal development rather than emergency infrastructure nobody understands until an outage.

## Component Tests Can Assert the Operational Contract { #component-tests }

Tests can verify that:

```text
metrics endpoint exists
readiness behaves correctly
business metric increments
logs carry trace context
manual span is nested under the HTTP span
```

These tests do not test Micrometer or OpenTelemetry themselves.

They test the application's operational contract.

If a platform upgrade accidentally removes a required probe or metric, CI should catch it.

## Black-Box Tests Should Include the System Port { #black-box-tests }

Most black-box tests focus on public business APIs.

A production-focused suite should also verify basic behavior of:

```text
/system/liveness
/system/readiness
/metrics
```

The deployment depends on those endpoints.

They deserve confidence too.

## Probe Tests Should Verify State Transitions { #probe-tests }

A readiness test that checks only "returns 200 after startup" is weak.

More useful tests verify lifecycle transitions where practical:

```text
before dependency ready
→ not ready

after initialization
→ ready

during shutdown
→ no longer admitting new work
```

Operational correctness is about state transitions, not static endpoints.

## Observability Configuration Is Production Code { #observability-config }

Telemetry configuration includes:

```text
metric enablement
SLO buckets
tracing exporter
service identity
log levels
masking
probe paths
shutdown timeout
```

These settings should be versioned and reviewed.

Changing metric labels or sampling policy can be as operationally important as changing Java code.

## Dashboards and Alerts Should Be Versioned Too { #dashboards-versioned }

Telemetry is only useful if its consumers remain in sync.

Mature platforms version:

- dashboards;
- alert rules;
- SLO definitions;

alongside service or platform configuration.

Otherwise a service can rename a metric and silently break operational visibility.

## Telemetry Is an Internal API { #telemetry-api }

Metrics, span names, structured log fields, and probe behavior are internal operational APIs.

Dashboards depend on them.

Alerts query them.

Runbooks reference them.

Changing them casually can break operations.

Naming discipline matters because other systems consume telemetry.

## One Request Should Be Traceable End to End { #traceable-end-to-end }

Return to the original request:

```text
Client
  ↓
HTTP server
  ↓
DashboardService
  ├── UserRepository
  │      ↓
  │   PostgreSQL
  │
  └── RecommendationClient
         ↓
      Recommendation Service
```

An ideal trace can look like:

```text
Trace 79d65...

SERVER  GET /users/{id}/dashboard           184 ms
  │
  └─ INTERNAL user.dashboard.build          176 ms
       │
       ├─ CLIENT DB UserRepository.findById   12 ms
       │
       └─ CLIENT HTTP GET /recommendations   151 ms
            │
            └─ SERVER downstream ...         145 ms
```

The corresponding metrics say:

```text
dashboard p95 = 190 ms
DB query p95 = 14 ms
recommendation p95 = 155 ms
error rate = 0.3%
```

The correlated logs might say:

```text
traceId=79d65...
event=recommendation_cache_miss
```

or:

```text
traceId=79d65...
event=recommendation_fallback
reason=timeout
```

Meanwhile the system port reports:

```text
liveness = healthy
readiness = ready
```

This is observability by design.

## What Happens During an Incident { #during-incident }

Suppose at 13:40 the endpoint p95 rises from 180 ms to 1.4 seconds.

Metrics detect the symptom:

```text
http.server.request.duration
route=/users/{id}/dashboard
p95=1.4s
```

Representative traces localize it:

```text
RecommendationClient = 1.25s
Database = 10ms
```

Client metrics confirm that the dependency is slow across many requests:

```text
http.client.request.duration
client=RecommendationClient
p95=1.2s
```

Logs show the application response:

```text
event=recommendation_fallback
rate increasing
```

Downstream traces reveal:

```text
database pool acquisition = 900ms
```

and downstream resource metrics confirm:

```text
pool active = max
pool waiters increasing
database CPU normal
```

The likely problem is now a saturated downstream connection pool rather than the original HTTP server.

Without correlated observability, the same incident can become hours of speculation.

## Good Observability Reduces Mean Time to Understanding { #mttu }

Teams often measure MTTR, mean time to recovery.

Recovery depends heavily on mean time to understanding.

How long does it take to form the correct explanation of the failure?

Metrics reduce detection time.

Traces reduce localization time.

Logs reduce semantic interpretation time.

Probes reduce orchestration ambiguity.

Graceful lifecycle behavior prevents deployments from creating extra noise.

Observability improves reliability partly because it shortens the path from symptom to explanation.

## Observability Improves Performance Engineering Too { #performance-engineering }

The same tools used during incidents are valuable for performance work.

A performance engineer can ask:

```text
Where does p99 spend time?
```

and inspect traces.

They can correlate CPU, GC, database latency, remote-client latency, and request distributions.

They can compare behavior before and after a deployment.

This is much more informative than a synthetic throughput number by itself.

Observability turns production into a source of performance evidence.

## Capacity Planning Requires Metrics { #capacity-planning }

How many replicas does a service need?

How many database connections?

How much CPU?

Without metrics, teams guess.

With metrics they can estimate peak request rate, CPU per request, active concurrency, database concurrency, pool saturation, and latency under load.

Autoscaling and resource requests can be based on measured behavior.

The operational stack is therefore connected directly to infrastructure cost.

## Graceful Shutdown Protects Error Budgets During Deployments { #shutdown-error-budgets }

A rollout can create failures even when the new version is healthy.

If old instances terminate too abruptly, requests can be reset during every deployment.

At fleet scale, this can consume error budget continuously.

Graceful shutdown turns deployment from:

```text
kill capacity
```

into:

```text
drain capacity
```

That is an availability feature.

## Fast Readiness and Graceful Shutdown Are Two Sides of the Same Rollout { #readiness-shutdown-rollout }

During rolling replacement:

```text
new instance
→ become ready quickly

old instance
→ become unready and drain safely
```

The deployment controller depends on both.

A framework focused only on startup speed but not graceful shutdown optimizes half the transition.

Kora's production model is stronger because readiness, lifecycle, and graceful stop belong to the same operational story.

## Observability Should Explain Deployments { #deployments }

During rollout, dashboards should reveal:

```text
old version traffic decreasing
new version traffic increasing
new version latency
new version errors
readiness failures
shutdown anomalies
```

Version-aware telemetry makes deployment validation measurable.

## Cold Instances Need Immediate Telemetry { #cold-instances }

A newly started instance is most interesting precisely when it is least warmed.

If observability appears only after long initialization, operators lose visibility into startup problems.

The system port and lifecycle telemetry should become usable early enough to explain initialization and readiness.

This is important for autoscaling, crash loops, cold starts, and spot-instance replacement.

## Startup Logs Should Be Structured Around Lifecycle { #startup-logs }

Useful lifecycle events include:

```text
application graph initialized
system HTTP server started
public HTTP server started
database pool initialized
readiness=true
```

and failures should identify which component failed.

Kora's explicit application graph gives lifecycle logs a real structural basis.

## Shutdown Logs Should Mirror Startup { #shutdown-logs }

Shutdown should also be understandable.

Useful events may include:

```text
shutdown initiated
readiness disabled
HTTP drain started
resource shutdown
telemetry flush
shutdown complete
```

If a Pod consistently exceeds termination grace, the telemetry should make the reason visible.

## Observability Is Part of Resilience { #resilience }

Retries, circuit breakers, fallbacks, and timeouts need telemetry.

A circuit breaker without metrics is dangerous because operators cannot see its state or rejection rate.

A retry without telemetry can silently amplify downstream load.

A fallback without logs or metrics can hide persistent dependency failure.

A successful HTTP 200 may represent degraded operation.

Observability needs to expose resilience behavior, not only transport behavior.

## Fallback Rate Can Be More Important Than Error Rate { #fallback-rate }

Suppose recommendation failures are hidden by fallback.

The API still returns 200.

HTTP error rate remains zero.

But the product is degraded.

A business or resilience metric such as:

```text
recommendation.fallback.count
```

can reveal the problem.

This is why framework infrastructure telemetry is necessary but not sufficient.

The application must expose meaningful degradation states.

## Retry Attempts Need Visibility { #retry-visibility }

If a dependency normally succeeds on the first attempt but starts requiring two or three retries, user latency increases before outright failures appear.

Retry-attempt and retry-exhaustion metrics can provide early warning.

Tracing can show repeated child calls.

Logs can explain why retry occurred.

Resilience policy should be observable rather than silently hiding failure.

## Circuit-Breaker Rejection Is Different from Remote Failure { #circuit-breaker }

A request rejected because a breaker is open did not reach the downstream service.

That is operationally different from a request that reached the service and failed.

Metrics and traces should preserve that distinction.

Different causes require different remediation.

## Timeouts Need Their Own Classification { #timeouts }

A timeout is a latency-budget failure.

It often indicates dependency slowness or an overly strict timeout.

Metrics should classify timeouts with bounded dimensions.

Traces and logs can contain richer exception/context data.

This supports both alerting and diagnosis.

## Observability Should Exist Before Load Testing { #load-testing }

A load test without internal telemetry tells you only throughput, latency, and errors from outside.

With observability you can also see CPU, GC, database-pool pressure, query latency, client latency, retry amplification, and thread behavior.

That tells you why the benchmark behaves as it does.

Framework telemetry therefore improves performance testing, not only production debugging.

## Virtual-Thread Behavior Needs Telemetry Too { #virtual-thread-telemetry }

For Kora 2, virtual-thread behavior is an important operational subject.

During load spikes, useful signals include request concurrency, CPU, database-pool saturation, latency, and carrier/thread behavior where available.

If latency increases while pool wait rises, the bottleneck is database concurrency.

If CPU saturates, adding virtual threads does not help.

Observability prevents vague diagnoses such as "virtual threads are slow" when the scarce resource is elsewhere.

## Telemetry Should Lead You to the Scarce Resource { #scarce-resource }

Every system eventually bottlenecks on something:

```text
CPU
database connections
database locks
remote dependency concurrency
memory
network
file descriptors
```

Observability is useful when it leads from a request symptom to the scarce resource.

Kora's thin module-level instrumentation fits this well because it follows real technology boundaries.

## Production Operations Need Consistent Runbooks { #runbooks }

A fleet is easier to operate when investigation is standardized.

For example:

```text
1. Check RED dashboard.
2. Check rollout/readiness state.
3. Open representative slow/error trace.
4. Identify dominant child span.
5. Open dependency/resource dashboard.
6. Query logs by traceId.
7. Check resilience metrics.
```

This workflow can apply across many services if telemetry conventions are consistent.

That is a platform advantage far larger than the convenience of any single API.

## Observability Improves Onboarding { #onboarding }

A developer joining a service can learn architecture by looking at representative traces.

A trace effectively documents:

```text
HTTP endpoint
business operation
database dependency
remote services
```

Metrics reveal which paths are high-volume.

Logs reveal important business decisions.

Observability becomes a runtime architecture map.

This is especially useful when static diagrams become stale.

## AI Agents Benefit for the Same Reason { #ai-agents }

An AI agent diagnosing a production issue benefits from structured evidence.

Instead of guessing from code, it can correlate route latency, trace hierarchy, database-span duration, client status, and structured error logs.

Kora's explicit generated architecture plus standardized telemetry is a strong combination: the model can inspect both static generated source and live operational signals.

## Telemetry Must Be Trustworthy { #trustworthy }

Bad observability is worse than no observability when it creates false confidence.

Examples include a metric incrementing before transaction commit, readiness reporting healthy while a required resource is unusable, spans ending before work actually finishes, or logs dropping
failures due to wrong level configuration.

Framework integration can solve infrastructure correctness.

Business telemetry still needs tests and review.

## Observability Must Not Become a Business Dependency { #business-dependency }

Instrumentation should not change business outcomes.

A logging failure should not fail a payment.

A trace exporter outage should not block HTTP traffic indefinitely.

A metrics backend failure should not stop request processing.

Telemetry pipelines need failure isolation.

Observability should observe the system, not become the reason the system is unavailable.

## Monitoring Backends Will Fail Too { #monitoring-backends }

Prometheus can be unreachable.

An OpenTelemetry collector can be down.

Log shipping can fail.

The service should normally continue operating.

This is why buffered/asynchronous export and scrape-based metrics are useful patterns.

Observability infrastructure needs its own resilience model.

## Backpressure Applies to Telemetry Pipelines { #backpressure }

A tracing exporter may have a bounded queue.

A logging appender may become saturated.

The system needs clear policies:

```text
drop?
block?
sample?
```

For most application telemetry, blocking user traffic because the trace backend is slow is undesirable.

The telemetry pipeline itself is part of operational architecture.

## The Observability Pipeline Needs Observability { #pipeline-observability }

A mature platform monitors the telemetry pipeline:

```text
dropped spans
exporter queue
log-shipping errors
scrape failures
collector health
```

Otherwise missing telemetry can be misread as a healthy service.

Loss of telemetry is itself a signal.

## The System Port Needs Network Policy { #system-port-policy }

A separate operational port is safer than exposing metrics publicly, but "private" still needs enforcement.

Metrics can reveal internal route names, service versions, database operation names, and topology.

NetworkPolicy, firewall rules, service-mesh policy, or infrastructure ACLs should restrict access appropriately.

Operational endpoints deserve security design too.

## Do Not Overcomplicate Local Probes with Authentication { #probe-authentication }

At the same time, requiring a complex remote authentication flow for local kubelet probes can create reliability problems.

A common design is network-level restriction plus simple local system endpoints.

The exact threat model depends on environment.

The important point is to treat the system port as infrastructure traffic with deliberate policy.

## One Request Across the Entire Kora Stack { #one-request-kora-stack }

Now compress the whole architecture into one path.

A client calls:

```text
GET /users/982374723/dashboard
```

The public HTTP server maps it to the route:

```text
GET /users/{id}/dashboard
```

The HTTP telemetry starts or continues a trace and records request timing.

Structured logging receives the active trace context.

The controller calls the application service.

The service optionally creates a business span:

```text
user.dashboard.build
```

The repository executes:

```text
UserRepository.findById
```

Database telemetry creates a child observation and records query duration.

The HTTP client calls:

```text
RecommendationClient.getRecommendations
```

Client telemetry creates a child span, propagates trace context, records latency/status metrics, and logs according to policy.

The downstream service continues the trace.

The response returns.

The HTTP observation records status and duration and closes.

Fleet-level metrics update.

The trace is complete.

If the business code emitted an important event, the log carries the same trace ID.

Meanwhile the system port reports liveness, readiness, and metrics.

If the process receives termination, graceful shutdown stops new work and allows current work to drain within its configured budget.

That is not a collection of observability features.

It is an operationally coherent request lifecycle.

## The Three Main Signals Answer Three Different Questions { #three-signals }

A useful summary is:

### Metrics { #metrics }

```text
What is happening across many operations?
```

Examples include p95 latency, request rate, error rate, pool saturation, and fallback rate.

### Tracing { #tracing }

```text
What happened to this specific operation?
```

Examples include which dependency dominated latency, where an error originated, and which operations ran in parallel.

### Logs { #logs }

```text
What did the application decide or observe?
```

Examples include fallback selection, business-invariant rejection, and unexpected state.

Probes answer a different platform question:

```text
Should this process receive traffic or be restarted?
```

Each signal becomes stronger when it is not forced to do another signal's job.

## A Production Kora Service Should Be Able to Answer These Questions { #production-questions }

```text
Can I see HTTP rate, errors, and latency?
Can I see outbound dependency latency?
Can I see database query duration?
Can I correlate logs with traces?
Can I inspect one request end to end?
Are metric labels bounded?
Are secrets masked?
Can I see retry, fallback, and breaker activity?
Are liveness and readiness semantically correct?
Are operational endpoints private?
Does graceful shutdown drain requests?
Can telemetry exporters fail without breaking traffic?
Do tests verify the operational contract?
```

If several answers are no, adding another dashboard is probably not the first priority.

The observability architecture itself needs work.

## Conclusion { #conclusion }

Observability in Kora is most useful when it is understood as part of the framework's production architecture rather than as a separate monitoring feature.

A request enters through the HTTP server. The server establishes an observable boundary. Application code performs business work. Outbound clients and repositories create their own child observations.
Trace context connects the operations. Micrometer records aggregate behavior. OpenTelemetry reconstructs individual request paths. Structured logs add semantic decisions and carry trace correlation.
Probes expose process and traffic-admission state on the system port. Lifecycle and graceful shutdown define what happens when the instance is removed from service.

The whole request can be pictured as:

```text
HTTP server span
       ↓
service / business span
       ↓
 ┌───────────────┐
 ↓               ↓
HTTP client    repository
span           DB span
 ↓               ↓
remote         database
service
```

while the same operations feed metrics:

```text
HTTP latency
HTTP errors
client latency
client status
database duration
connection-pool state
business counters
JVM / process metrics
```

and logs remain correlated through:

```text
traceId
spanId
structured event fields
```

This is the core idea behind observability by design.

Metrics should detect.

Traces should localize.

Logs should explain.

Probes should control traffic and restart decisions.

Graceful shutdown should preserve correctness while an instance leaves the fleet.

The framework should provide infrastructure telemetry where it has the best context, while application code adds the business meaning the framework cannot know. That division keeps observability
useful without filling business code with telemetry plumbing.

It also aligns with Kora's broader architecture: explicit modules, thin abstractions, generated infrastructure, one coherent model across HTTP, clients, repositories, messaging, and lifecycle.

A production service should not wait for an incident to become observable.

By the time the incident begins, the request has already happened.

The telemetry has to be there first.
