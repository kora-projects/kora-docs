---
search:
  exclude: true
title: Tracing with Kora
summary: Build focused OpenTelemetry tracing for a Kora HTTP service, including the OTLP exporter, KoraTracer business spans, trace context propagation, log correlation, and Jaeger verification.
description: "Step-by-step OpenTelemetry tracing for a Kora HTTP service: the io.koraframework:opentelemetry-tracing-exporter-http dependency, OpentelemetryHttpExporterModule, the tracing and tracing.exporter configuration sections, service.name resource attributes, business spans created with KoraTracer traceParent and traceNew, span attributes and error recording, ScopedValue-based trace context, traceId and spanId log correlation, and verifying a trace in Jaeger."
agent:
  use_when: "Use this file for questions about adding tracing to a Kora application step by step: io.koraframework:opentelemetry-tracing-exporter-http, OpentelemetryHttpExporterModule, OpentelemetryGrpcExporterModule, the tracing.exporter.endpoint setting, tracing.attributes with service.name, injecting KoraTracer, traceParent and traceNew, KoraTracer.TraceCallable in Kotlin, adding span attributes, why a manual span becomes a separate trace, why traceId is missing from logs, and running Jaeger locally to inspect a trace."
tags: observability, tracing, opentelemetry, spans, kora-tracer, jaeger, context
---

# Tracing with Kora { #observability-tracing-kora }

This guide focuses only on tracing. You will take the HTTP server application and make one request traceable end to end: connect the OpenTelemetry exporter, give the service an identity, add a
business span with `KoraTracer`, and read the resulting trace in Jaeger.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java Observability App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-observability-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin Observability App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-observability-app).

## What You Will Build { #youll-build }

You will add:

- `OpentelemetryHttpExporterModule`
- the `tracing.exporter` section pointing at a local collector
- the `guide-observability-app` service identity in `tracing.attributes`
- a `user.create` business span created with `KoraTracer`
- span attributes and error recording for that operation
- `traceId` and `spanId` in every log line of the request
- a trace read back in the Jaeger UI

## What You Will Need { #youll-need }

- JDK 25 or later
- Gradle 9+
- Docker, to run Jaeger locally
- A text editor or IDE
- Completed [HTTP Server Guide](http-server.md)

Kora 2.0 artifacts are compiled for Java 25, so the JDK that compiles the application must be 25 or newer.

## Prerequisites { #prerequisites }

!!! note "Required Foundation"

    This guide assumes you have completed **[HTTP Server Guide](http-server.md)** and already have the HTTP controllers, DTOs, repository, service, and configuration from that guide in place.

    If you haven't completed the HTTP server guide yet, do that first, because this observability guide keeps that HTTP surface and layers telemetry on top of it.

## Overview { #overview }

Tracing is what you reach for when one number is not enough. A metric can tell you that user creation became slow. It cannot tell you *which* request was slow, which steps it went through, or where
the time actually went. A trace answers that: it records the path of one concrete request as a chain of related, timed steps.

Kora traces the supported modules for you. The HTTP server and client, the database, `Kafka`, the gRPC server and client and other subsystems create their own spans through their telemetry, and the
trace context travels between services using the [W3C Trace Context](https://www.w3.org/TR/trace-context/) standard. The manual span in this guide does not replace that instrumentation; it adds the
one step the framework cannot infer — the business meaning of the operation.

Imagine every incoming request being handed a ticket with a number on it. The number travels with the request through the HTTP layer, into services, and on into anything they call. Each important step
writes on the ticket: "I started", "I finished", "I failed here". At the end you get an execution tree instead of a scattering of log lines.

### Trace Model { #trace-model }

A **trace** is the story of one request. When a client calls `POST /users`, the trace holds the incoming HTTP server span, the `user.create` span you are about to add, and later perhaps database or
outbound HTTP spans. Everything in that story shares one trace id.

A **span** is one step inside a trace. It has a name, a start and end time, a status, and optional attributes. The span in this guide is called `user.create` because it names the business step. That is
a better name than the class or method that happens to implement it today, because the business step outlives the refactoring.

A **parent** is what connects the steps. If `user.create` is created as a child of the HTTP server span, Jaeger nests it inside the same trace. If the parent is lost, the span starts a trace of its
own and you can no longer tell which request produced it.

**Errors** must be put on the span deliberately. A span that ended is not automatically a span that succeeded — recording the exception and setting the error status is what separates "this request was
merely slow" from "this request blew up".

### Tools { #tools }

`OpentelemetryHttpExporterModule` adds `OTLP/HTTP` span export to the application graph. Its configuration says where collected spans go; locally that is Jaeger on port `4318`. There is a matching
`OpentelemetryGrpcExporterModule` for collectors that speak `OTLP/gRPC` — pick exactly one of the two.

`KoraTracer` is the component you inject to create a business span. It builds the span, makes it the current context for the duration of the call, sets the status, records an exception if one escapes,
and ends the span. One call, no bookkeeping.

The **trace context** is carried by a `ScopedValue`, not a thread local. Kora registers its own `ContextStorage` for OpenTelemetry, so `io.opentelemetry.context.Context.current()` and
`io.opentelemetry.api.trace.Span.current()` return the right thing anywhere inside a traced operation, virtual threads included.

**Jaeger** is a local trace viewer. It is not needed to compile or run the application, but it is how you verify the result: create a user, open the UI, pick the service, and look for the span.

### Span Boundary { #span-boundary }

A span should describe work worth measuring. Do not wrap every line, every branch, and every DTO conversion in one — too many spans turn a trace into noise, and each span costs memory and export
bandwidth.

A good manual span:

- starts before the domain operation and ends after its result exists
- is named after the operation, not after the method implementing it
- carries a few low-cardinality attributes that help you filter
- records the exception when the operation fails
- contains no personal data in its name or attributes

In this guide the span wraps user creation. That is useful because it isolates the business operation from the HTTP handling around it: if the trace shows the HTTP span taking 200ms and `user.create`
taking 4ms, the time went somewhere else, and the trace tells you where to look next.

## Dependencies { #dependencies }

`OTLP/HTTP` export lives in the `opentelemetry-tracing-exporter-http` artifact. Its version comes from the `io.koraframework:kora-bom` platform, so it is not written on the dependency line.

===! ":fontawesome-brands-java: `Java`"

    Update `build.gradle`:

    ```groovy
    dependencies {
        // ... existing dependencies from the HTTP server guide ...

        implementation "io.koraframework:opentelemetry-tracing-exporter-http" //(1)!
    }
    ```

    1.  `OTLP/HTTP` span exporter. It transitively brings the core tracing wiring, so no separate tracing dependency is needed.

=== ":simple-kotlin: `Kotlin`"

    Update `build.gradle.kts`:

    ```kotlin
    dependencies {
        // ... existing dependencies from the HTTP server guide ...

        implementation("io.koraframework:opentelemetry-tracing-exporter-http") //(1)!
    }
    ```

    1.  `OTLP/HTTP` span exporter. It transitively brings the core tracing wiring, so no separate tracing dependency is needed.

The `OTLP/HTTP` module sends spans through the `JDK` HTTP client and does not pull `OkHttp` into the application. If your collector accepts `OTLP/gRPC` instead, swap the artifact for
`io.koraframework:opentelemetry-tracing-exporter-grpc` and the module for `OpentelemetryGrpcExporterModule` — both exporters share the same configuration shape, so nothing else in this guide changes.

## Modules { #modules }

Add the exporter module to the application graph next to the modules from the HTTP server guide.

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/java/io/koraframework/guide/observability/Application.java`:

    ```java
    package io.koraframework.guide.observability;

    import io.koraframework.application.graph.KoraApplication;
    import io.koraframework.common.annotation.KoraApp;
    import io.koraframework.config.hocon.HoconConfigModule;
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule;
    import io.koraframework.json.common.JsonModule;
    import io.koraframework.logging.logback.LogbackModule;
    import io.koraframework.opentelemetry.tracing.exporter.http.OpentelemetryHttpExporterModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            UndertowPublicHttpServerModule,
            OpentelemetryHttpExporterModule {  // <----- Connected module

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update `src/main/kotlin/io/koraframework/guide/observability/Application.kt`:

    ```kotlin
    package io.koraframework.guide.observability

    import io.koraframework.application.graph.KoraApplication
    import io.koraframework.common.annotation.KoraApp
    import io.koraframework.config.hocon.HoconConfigModule
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule
    import io.koraframework.json.common.JsonModule
    import io.koraframework.logging.logback.LogbackModule
    import io.koraframework.opentelemetry.tracing.exporter.http.OpentelemetryHttpExporterModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        UndertowPublicHttpServerModule,
        OpentelemetryHttpExporterModule  // <----- Connected module

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

`OpentelemetryHttpExporterModule` extends `OpentelemetryTracingModule`, which is what actually puts the `TracerProvider`, the `Tracer` and the `KoraTracer` into the graph. That is why connecting one
exporter module is enough to both create spans and ship them.

## Configuration { #config }

Tracing is described by two sections: `tracing` for the service itself, and `tracing.exporter` for the transport that carries spans out.

For the full configuration reference, see [Tracing](../documentation/tracing.md#configuration).

===! ":material-code-json: `Hocon`"

    ```javascript
    tracing {
      exporter {
        endpoint = "http://localhost:4318/v1/traces" //(1)!
        exportTimeout = "5s" //(2)!
        scheduleDelay = "1s" //(3)!
        maxExportBatchSize = 512 //(4)!
        maxQueueSize = 2048 //(5)!
      }
      attributes { //(6)!
        "service.name" = "guide-observability-app"
        "service.namespace" = "kora-guide"
      }
    }
    ```

    1.  Collector endpoint spans are exported to. For `OTLP/HTTP` the path `/v1/traces` is part of the URL (no default).
    2.  Maximum time to wait while the exporter sends data (default: `3s`).
    3.  Delay between sending accumulated spans to the collector (default: `2s`).
    4.  Maximum number of spans in one export batch (default: `512`).
    5.  Maximum number of spans queued while waiting to be sent (default: `2048`).
    6.  `OpenTelemetry Resource` attributes attached to every exported span of the service (default: `{}`).

=== ":simple-yaml: `YAML`"

    ```yaml
    tracing:
      exporter:
        endpoint: "http://localhost:4318/v1/traces" #(1)!
        exportTimeout: "5s" #(2)!
        scheduleDelay: "1s" #(3)!
        maxExportBatchSize: 512 #(4)!
        maxQueueSize: 2048 #(5)!
      attributes: #(6)!
        "service.name": "guide-observability-app"
        "service.namespace": "kora-guide"
    ```

    1.  Collector endpoint spans are exported to. For `OTLP/HTTP` the path `/v1/traces` is part of the URL (no default).
    2.  Maximum time to wait while the exporter sends data (default: `3s`).
    3.  Delay between sending accumulated spans to the collector (default: `2s`).
    4.  Maximum number of spans in one export batch (default: `512`).
    5.  Maximum number of spans queued while waiting to be sent (default: `2048`).
    6.  `OpenTelemetry Resource` attributes attached to every exported span of the service (default: `{}`).

`service.name` deserves attention because it is how you find anything at all. `tracing.attributes` is empty by default, so a service that skips it exports spans without an identity and shows up in the
collector as an unnamed producer. Set at least the name, and a namespace if you run several related services.

`scheduleDelay = "1s"` is a deliberate choice for a local guide: the default `2s` is fine in production but feels like a hang when you create a user and immediately refresh the Jaeger UI.

### Tracing Switches { #tracing-switches }

!!! note "Tracing is on by default — metrics and logging are not"

    `OpentelemetryTracingConfig#enabled` returns `true`, and so does `TelemetryConfig.TracingConfig#enabled` for every module. This is the opposite of metrics and logging telemetry, which are off
    until you enable them. If you connected the exporter module and set an endpoint, spans start flowing without any further switch.

Two independent things can turn tracing off:

===! ":material-code-json: `Hocon`"

    ```javascript
    tracing.enabled = false //(1)!
    httpServer.telemetry.tracing.enabled = false //(2)!
    ```

    1.  Global switch. Kora installs a no-op `TracerProvider`, so no span is recorded anywhere (default: `true`).
    2.  Per-module switch. The public HTTP server stops creating its own spans (default: `true`).

=== ":simple-yaml: `YAML`"

    ```yaml
    tracing:
      enabled: false #(1)!
    httpServer:
      telemetry:
        tracing:
          enabled: false #(2)!
    ```

    1.  Global switch. Kora installs a no-op `TracerProvider`, so no span is recorded anywhere (default: `true`).
    2.  Per-module switch. The public HTTP server stops creating its own spans (default: `true`).

There is one more thing worth knowing: if `tracing.exporter.endpoint` is not set at all, no exporter and no span processor are created. The application still starts, spans are still created and the
trace context still propagates — they are simply never sent anywhere. That is exactly the shape you want in a unit test, and it is why forgetting the endpoint produces no error message.

The system HTTP server is the deliberate exception to the "tracing is on" rule: `SystemHttpServerConfig` overrides its tracing to `false`, so orchestrator polling of `/system/readiness` every few
seconds does not bury your real traces.

## Business Span { #business-span }

Framework telemetry already produced a span for the incoming `POST /users`. What it cannot know is that this particular request means "create a user" in your domain. That is the span you add by hand.

### KoraTracer { #kora-tracer }

Inject `KoraTracer` into `UserService` and wrap the creation logic. `traceParent` nests the new span under the currently active one — the HTTP server span — so the result is one trace, not two.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class UserService {

        private final UserRepository userRepository;
        private final KoraTracer tracer;

        public UserService(UserRepository userRepository, KoraTracer tracer) {
            this.userRepository = userRepository;
            this.tracer = tracer;
        }

        public UserResponse createUser(UserRequest request) {
            return tracer.traceParent("user.create", span -> { //(1)!
                var generatedId = userRepository.save(request.name(), request.email());
                return new UserResponse(generatedId, request.name(), request.email(), LocalDateTime.now());
            });
        }
    }
    ```

    1.  The span is created, made current, ended, and given a status by `KoraTracer` — the lambda only contains business logic.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class UserService(
        private val userRepository: UserRepository,
        private val tracer: KoraTracer
    ) {

        fun createUser(request: UserRequest): UserResponse {
            return tracer.traceParent("user.create", KoraTracer.TraceCallable<UserResponse, RuntimeException> { span -> //(1)!
                val id = userRepository.save(request.name, request.email)
                UserResponse(id, request.name, request.email, LocalDateTime.now())
            })
        }
    }
    ```

    1.  `traceParent` is overloaded for `TraceCallable` and `TraceRunnable`, and `Kotlin` cannot choose between two functional interfaces on its own — pass the explicit SAM constructor.

`KoraTracer` gives you three entry points:

- `traceParent(name, …)` — a span nested under the currently active one. This is what you want inside a request.
- `traceNew(name, …)` — a root span that starts its own trace. Use it for work that is genuinely not part of the incoming request, such as a background job.
- `tracer()` — the underlying `io.opentelemetry.api.trace.Tracer`, for cases the two helpers do not cover.

Each accepts either a `TraceCallable`, which returns a value, or a `TraceRunnable`, which does not. Both hand you the created `Span`.

### Span Attributes { #span-attributes }

The `Span` passed into the lambda is where you record what makes this execution different from the last one. Attributes are for filtering and grouping in the trace UI, so keep their values bounded.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public UserResponse createUser(UserRequest request) {
        return tracer.traceParent("user.create", span -> {
            span.setAttribute("user.email.provider", emailProvider(request.email())); //(1)!

            var generatedId = userRepository.save(request.name(), request.email());
            span.setAttribute("user.id", generatedId); //(2)!

            return new UserResponse(generatedId, request.name(), request.email(), LocalDateTime.now());
        });
    }

    private static String emailProvider(String email) {
        var at = email.lastIndexOf('@');
        return at < 0 ? "unknown" : email.substring(at + 1);
    }
    ```

    1.  A low-cardinality attribute: useful for filtering, bounded in the number of distinct values.
    2.  A high-cardinality attribute is acceptable on a span — unlike on a metric, it does not create a new time series.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun createUser(request: UserRequest): UserResponse {
        return tracer.traceParent("user.create", KoraTracer.TraceCallable<UserResponse, RuntimeException> { span ->
            span.setAttribute("user.email.provider", emailProvider(request.email)) //(1)!

            val id = userRepository.save(request.name, request.email)
            span.setAttribute("user.id", id) //(2)!

            UserResponse(id, request.name, request.email, LocalDateTime.now())
        })
    }

    private fun emailProvider(email: String): String =
        email.substringAfterLast('@', "unknown")
    ```

    1.  A low-cardinality attribute: useful for filtering, bounded in the number of distinct values.
    2.  A high-cardinality attribute is acceptable on a span — unlike on a metric, it does not create a new time series.

This is a real difference between the two signals. On a [metric](observability-metrics.md#metric-caching), a tag with an unbounded value set multiplies the number of stored time series and will
eventually take the monitoring system down. On a span, an identifier is just a field on one recorded event, so `user.id` is fine here and would not be fine on the counter.

What must not go on a span in either case is personal data. The email address itself, a full name, a token — these end up in the collector, get indexed, and are read by anyone with access to the trace
UI. The *provider* part of the address answers "are Gmail signups failing?" without storing the address.

### Errors in a Span { #span-errors }

You do not need a `try`/`catch` to record failures. If the lambda throws, `KoraTracer` records the exception on the span, sets the status to `ERROR` with the exception message, ends the span, and
rethrows. On a normal return it sets `OK`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public void deleteUser(String id) {
        tracer.traceParent("user.delete", span -> { //(1)!
            span.setAttribute("user.id", id);
            if (!userRepository.deleteById(id)) {
                throw HttpServerResponseException.of(404, "User not found"); //(2)!
            }
        });
    }
    ```

    1.  The lambda returns nothing, so this resolves to `TraceRunnable`.
    2.  The exception is recorded on the span and rethrown — the `404` still reaches the client unchanged.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun deleteUser(id: String) {
        tracer.traceParent("user.delete", KoraTracer.TraceRunnable<RuntimeException> { span -> //(1)!
            span.setAttribute("user.id", id)
            if (!userRepository.deleteById(id)) {
                throw HttpServerResponseException.of(404, "User not found") //(2)!
            }
        })
    }
    ```

    1.  Nothing is returned, so this is the `TraceRunnable` overload — again with an explicit SAM constructor.
    2.  The exception is recorded on the span and rethrown — the `404` still reaches the client unchanged.

Tracing never swallows an exception. It observes it on the way past and lets it continue to the HTTP layer, which turns it into the response the client actually gets.

### When KoraTracer Is Not Enough { #manual-span }

`KoraTracer` covers the common case. When you need something it does not expose — a specific `SpanKind`, a link to another trace, a span that outlives the call — build the span from the `Tracer` and
bind the context yourself.

===! ":fontawesome-brands-java: `Java`"

    ```java
    var span = tracer.tracer().spanBuilder("user.create")
            .setSpanKind(SpanKind.INTERNAL)
            .setParent(io.opentelemetry.context.Context.current())
            .startSpan();

    return ScopedValue.where(OpentelemetryContext.VALUE, io.opentelemetry.context.Context.current().with(span)) //(1)!
            .call(() -> {
                try {
                    var result = doWork();
                    span.setStatus(StatusCode.OK);
                    return result;
                } catch (Exception e) {
                    span.recordException(e);
                    span.setStatus(StatusCode.ERROR, e.getMessage());
                    throw e;
                } finally {
                    span.end(); //(2)!
                }
            });
    ```

    1.  Binding the `ScopedValue` is how a context becomes current. `Context#makeCurrent()` deliberately throws `IllegalStateException` in Kora.
    2.  A span that is never ended is a span that is never exported — hence the `finally`.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val span = tracer.tracer().spanBuilder("user.create")
        .setSpanKind(SpanKind.INTERNAL)
        .setParent(io.opentelemetry.context.Context.current())
        .startSpan()

    val carrier = ScopedValue.where( //(1)!
        OpentelemetryContext.VALUE,
        io.opentelemetry.context.Context.current().with(span)
    )
    return carrier.call<UserResponse, RuntimeException> {
        try {
            val result = doWork()
            span.setStatus(StatusCode.OK)
            result
        } catch (e: Exception) {
            span.recordException(e)
            span.setStatus(StatusCode.ERROR, e.message)
            throw e
        } finally {
            span.end() //(2)!
        }
    }
    ```

    1.  Binding the `ScopedValue` is how a context becomes current. `Context#makeCurrent()` deliberately throws `IllegalStateException` in Kora.
    2.  A span that is never ended is a span that is never exported — hence the `finally`.

A `ScopedValue` is visible only inside the dynamic scope that bound it, so handing work to another thread drops the trace context. If you submit to an executor, capture
`io.opentelemetry.context.Context.current()` in the calling thread and re-bind it in the worker — see [Asynchronous tracing](../documentation/tracing.md#async-tracing).

## Log Correlation { #log-correlation }

The most immediately useful result of connecting tracing is not the trace UI — it is that your log lines gain a trace id.

`KoraAsyncAppender` captures the current span context when a log event is queued, and `ConsoleTextRecordEncoder` writes `traceId=` and `spanId=` into the line whenever that context is valid. The
Logback configuration from the HTTP server guide already has both:

```xml title="src/main/resources/logback.xml"
<appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
    <encoder class="io.koraframework.logging.logback.ConsoleTextRecordEncoder"/>
</appender>

<appender name="ASYNC" class="io.koraframework.logging.logback.KoraAsyncAppender">
    <appender-ref ref="STDOUT"/>
</appender>
```

Log a line inside the traced operation and it carries the identifiers automatically:

```text
09:41:12.508 INFO  [kora-undertow-4] i.k.g.o.service.UserService - traceId=4bf92f3577b34da6a3ce929d0e0e4736 spanId=00f067aa0ba902b7 Created user with id=1
```

Nothing has to be put into or taken out of `MDC` for this — the trace identifiers do not travel through it. Lines logged outside any traced operation simply have no such fields.

This is the bridge between the two signals. You find a failing request in the logs, copy its `traceId`, paste it into Jaeger, and see the whole request; or you find a slow trace and search the logs
for its id to read what the code was saying at the time.

## Docker Compose { #docker-compose }

Run Jaeger with the `OTLP/HTTP` receiver enabled:

```yaml title="docker-compose.yml"
services:
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686" #(1)!
      - "4318:4318" #(2)!
    environment:
      COLLECTOR_OTLP_ENABLED: "true" #(3)!
```

1.  Jaeger UI.
2.  `OTLP/HTTP` receiver — the port `tracing.exporter.endpoint` points at.
3.  Enables the `OTLP` receivers in the all-in-one image.

## Check Application { #check-app }

Start Jaeger, run the application, and create a user:

```bash
docker compose up -d

./gradlew run
```

```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@example.com"}'
```

Watch the application log for the line confirming the request was traced:

```text
09:41:12.508 INFO  [kora-undertow-4] i.k.g.o.service.UserService - traceId=4bf92f3577b34da6a3ce929d0e0e4736 spanId=00f067aa0ba902b7 Created user with id=1
```

Then open [http://localhost:16686](http://localhost:16686), select the `guide-observability-app` service and press **Find Traces**. Give it a second or two — spans leave the application in batches
every `scheduleDelay`.

Open the trace and you should see the HTTP server span with `user.create` nested inside it, carrying the `user.email.provider` and `user.id` attributes you set. That nesting is the whole point: it is
the proof that the manual span found its parent.

## Best Practices { #best-practices }

- Name spans after operations, not after the Java or Kotlin methods implementing them.
- Prefer `KoraTracer` over hand-rolled span bookkeeping; drop to the raw `Tracer` only for what it does not cover.
- Use `traceParent` inside a request and `traceNew` only for work that genuinely starts its own trace.
- Let exceptions propagate through the span instead of catching and re-throwing them yourself.
- Keep personal data out of span names and attributes.
- Set `service.name` and keep it stable for the environment.
- Span attributes may be high-cardinality; metric tags may not.

## Summary { #summary }

You connected the `OTLP/HTTP` exporter, gave the service an identity, added a `user.create` span with `KoraTracer` including attributes and error recording, saw `traceId` appear in the logs, and read
the finished trace in Jaeger.

## Key Concepts { #key-concepts }

Trace:
: the full story of one request, shared by every span in it.

Span:
: one measured step inside a trace, with a name, timing, status and attributes.

`KoraTracer`:
: the injected component that creates a business span and handles its status, errors and lifetime.

Parent context:
: what makes a manual span part of the incoming request instead of a trace of its own.

Resource attributes:
: `tracing.attributes` — the service identity attached to every exported span.

OTLP:
: the protocol used to ship spans to a collector, over `HTTP` or `gRPC`.

## Troubleshooting { #troubleshooting }

Nothing arrives in Jaeger:
: Check that `tracing.exporter.endpoint` is set. With no endpoint, spans are created and propagated but never exported, and nothing is logged about it.

Nothing arrives, and the endpoint is set:
: Confirm Jaeger is running with `COLLECTOR_OTLP_ENABLED=true` and that the URL includes the `/v1/traces` path.

The trace appears only after a delay:
: That is `tracing.exporter.scheduleDelay` batching spans (default: `2s`).

The service is missing from the Jaeger dropdown:
: Set `tracing.attributes."service.name"`. Without it spans are exported without a service identity.

`user.create` shows up as a separate trace:
: Something lost the parent context. Use `traceParent`, not `traceNew`, and check whether the work was handed to another thread without carrying the context over.

No spans at all:
: Check `tracing.enabled` and the module's own `<module>.telemetry.tracing.enabled`. Both default to `true`, so an explicit `false` is the only way they are off.

Logs have no `traceId`:
: The line was logged outside a traced operation, or `logback.xml` is not using `KoraAsyncAppender` with `ConsoleTextRecordEncoder`.

## What's Next? { #whats-next }

- add business metrics in [Metrics with Kora](observability-metrics.md)
- add liveness and readiness checks in [Probes with Kora](observability-probes.md)
- wire all signals into one application in [Observability and Monitoring with Kora](observability.md)
- compare details with [Tracing documentation](../documentation/tracing.md)

## Help { #help }

- inspect the finished Java and Kotlin observability applications
- check exporter and sampling settings in [Tracing documentation](../documentation/tracing.md)
- see how trace identifiers reach the log line in [Logging documentation](../documentation/logging-slf4j.md#logback)
