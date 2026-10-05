---
search:
  exclude: true
title: Tracing with Kora
summary: Build focused OpenTelemetry tracing for a Kora HTTP service, including exporter configuration, manual spans, context propagation, Jaeger checks, and trace-aware troubleshooting.
tags: observability, tracing, opentelemetry, spans, tracer, jaeger, context
---

# Tracing with Kora { #observability-tracing-kora }

This guide focuses only on tracing. You will add the OpenTelemetry exporter, configure the service name, create a manual span around a business operation, and verify the trace in Jaeger.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java Observability App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-observability-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin Observability App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-observability-app).

## What You'll Build { #youll-build }

You will add:

- `OpentelemetryHttpExporterModule`
- OTLP HTTP exporter configuration
- the `guide-observability-app` service name
- `TracingService` with the manual `user.create` span
- span integration in `UserService`
- local trace verification in Jaeger

## What You'll Need { #youll-need }

- JDK 17 or later
- Gradle 7+
- Docker, if you want to run the black-box smoke test locally
- A text editor or IDE
- Completed [HTTP Server Guide](http-server.md)

## Prerequisites { #prerequisites }

!!! note "Required Foundation"

    This guide assumes you have completed **[HTTP Server Guide](http-server.md)** and already have the HTTP controllers, DTOs, repository, service, and configuration from that guide in place.

    If you haven't completed the HTTP server guide yet, do that first, because this observability guide keeps that HTTP surface and layers telemetry on top of it.

## Overview { #overview }

Tracing is useful when one number is not enough. A metric can say: "user creation became slow". It cannot show which exact request was slow, which steps it passed through, or where time was spent. A trace shows the path of one concrete request as a chain of related steps.

Kora as a framework already provides tracing for the main supported modules out of the box. HTTP servers, clients, databases, messaging, and other integrations can emit baseline spans in OpenTelemetry format when the relevant telemetry modules are connected. The manual span in this guide does not replace Kora's built-in tracing; it adds a business step that the framework cannot infer on its own.

Imagine that every request receives a small ticket with a number. This number travels with the request through the HTTP layer, services, and additional operations. Every important step adds a record: "I started", "I finished", "I had an error". At the end, you see an execution tree, not just a log line.

This guide uses these tools:

- OpenTelemetry API provides `Tracer`, `Span`, and `StatusCode`
- `OpentelemetryHttpExporterModule` connects the exporter to the Kora graph
- `OpentelemetryContext` connects OpenTelemetry context with Kora context
- Jaeger displays traces in a local UI

OpenTelemetry is a common language for tracing. The application creates spans, the exporter sends them out, and Jaeger or another collector shows them to operators. Kora helps connect that to the DI graph and request context.

### Trace Model { #trace-model }

Trace is the story of one request. If a user calls `POST /users`, the trace may contain an incoming HTTP span, the `user.create` span, and later perhaps a database or external service span. All of these parts are connected by one trace id.

Span is one step inside a trace. A span has a name, start time, end time, status, and optional data. In this guide, the span is named `user.create` because it describes the business step of creating a user. That name is clearer than a method or class name.

Parent context is the connection between steps. If the `user.create` span is created as a child of the HTTP request, Jaeger shows it inside the same trace. If the parent is lost, the span may become a separate trace, and you will not know which request created it.

Errors inside a span should be recorded explicitly. That is why the code calls `span.recordException(e)` and sets `StatusCode.ERROR`. This helps distinguish a normal slow request from a request that failed with an exception.

### Tools { #tools }

`OpentelemetryHttpExporterModule` adds OTLP HTTP trace export to the application. In configuration, the endpoint `http://localhost:4318/v1/traces` tells the exporter where to send collected spans. Locally, that is Jaeger.

`Tracer` is the span factory. `TracingService` receives `Tracer` from the Kora graph and creates a span with `tracer.spanBuilder("user.create")`. The `Tracer` does not contain business logic; it only helps create measured steps.

`OpentelemetryContext` makes the manual span part of the current request. Kora has its own `Context`, and OpenTelemetry context is stored inside it. The code reads `Context.current()`, gets `OpentelemetryContext.get(ctx)`, adds a new span, and restores the previous state in `finally`.

Jaeger is a local trace viewer. It is not required to compile the application, but it is very useful for verification. You create a user, open Jaeger UI, choose `guide-observability-app`, and check whether the `user.create` span appeared.

### Span Boundary { #span-boundary }

A span should describe meaningful work. Do not create a span around every line, every `if`, or every small DTO conversion. Too many spans turn a trace into noise.

A good manual span boundary:

- starts before the domain operation
- ends after the result is produced
- records an exception if the operation fails
- does not put personal data in the name or attributes
- restores the previous context

In this guide, the span wraps user creation. That is useful because it shows how long the business operation took, not only the HTTP handling. If you later add a database or external service, the trace can grow with new child spans.

The practical result is that tracing turns one request into a visible chain of actions. Metrics say "something became slow"; a trace lets you open one concrete example and see where it happened.

## Dependencies { #dependencies }

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    dependencies {
        // ... existing dependencies from the HTTP server guide ...

        implementation("ru.tinkoff.kora:opentelemetry-tracing-exporter-http")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    dependencies {
        // ... existing dependencies from the HTTP server guide ...

        implementation("ru.tinkoff.kora:opentelemetry-tracing-exporter-http")
    }
    ```

## Modules { #modules }

Add the OpenTelemetry exporter to the application graph.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            UndertowHttpServerModule,
            OpentelemetryHttpExporterModule {  // <----- Connected module

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        UndertowHttpServerModule,
        OpentelemetryHttpExporterModule  // <----- Connected module
    ```

## Configuration { #config }

Configure the OTLP HTTP exporter. Locally, traces are sent to Jaeger on port `4318`.

```hocon title="src/main/resources/application.conf"
tracing {
  exporter {
    endpoint = "http://localhost:4318/v1/traces"
    exportTimeout = "5s"
    scheduleDelay = "1s"
    maxExportBatchSize = 512
    maxQueueSize = 2048
  }
  attributes {
    "service.name" = "guide-observability-app"
    "service.namespace" = "kora-guide"
  }
}
```

`service.name` is especially important because this is how you find traces in the UI.

## Tracing Service { #tracing-service }

Create a component that owns the manual span. It reads the current Kora context, extracts the OpenTelemetry context, adds a new span, and restores the previous context in `finally`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class TracingService {

        private final Tracer tracer;

        public TracingService(Tracer tracer) {
            this.tracer = tracer;
        }

        public <T> T traceUserCreation(Callable<T> action) {
            var ctx = Context.current();
            var otctx = OpentelemetryContext.get(ctx);
            var span = tracer.spanBuilder("user.create")
                    .setParent(otctx.getContext())
                    .startSpan();

            OpentelemetryContext.set(ctx, otctx.add(span));
            try {
                var result = action.call();
                span.setStatus(StatusCode.OK);
                return result;
            } catch (RuntimeException e) {
                span.recordException(e);
                span.setStatus(StatusCode.ERROR, e.getMessage());
                throw e;
            } catch (Exception e) {
                span.recordException(e);
                span.setStatus(StatusCode.ERROR, e.getMessage());
                throw new IllegalStateException("Failed to trace user creation", e);
            } finally {
                span.end();
                OpentelemetryContext.set(ctx, otctx);
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class TracingService(
        private val tracer: Tracer
    ) {
        fun <T> traceUserCreation(action: () -> T): T {
            val ctx = Context.current()
            val otctx = OpentelemetryContext.get(ctx)
            val span = tracer.spanBuilder("user.create")
                .setParent(otctx.context)
                .startSpan()

            OpentelemetryContext.set(ctx, otctx.add(span))
            try {
                val result = action()
                span.setStatus(StatusCode.OK)
                return result
            } catch (e: RuntimeException) {
                span.recordException(e)
                span.setStatus(StatusCode.ERROR, e.message ?: "error")
                throw e
            } finally {
                span.end()
                OpentelemetryContext.set(ctx, otctx)
            }
        }
    }
    ```

Do not create a span without a parent context when work happens inside an HTTP request.

## Service Integration { #service-integration }

Inject `TracingService` into `UserService` and wrap user creation.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public UserResponse createUser(UserRequest request) {
        return tracingService.traceUserCreation(() -> {
            var generatedId = userRepository.save(request.name(), request.email());
            return new UserResponse(generatedId, request.name(), request.email(), LocalDateTime.now());
        });
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun createUser(request: UserRequest): UserResponse {
        return tracingService.traceUserCreation {
            val id = userRepository.save(request.name, request.email)
            UserResponse(id, request.name, request.email, LocalDateTime.now())
        }
    }
    ```

## Docker Compose { #docker-compose }

Run Jaeger with the OTLP HTTP endpoint:

```yaml title="docker-compose.yml"
services:
  jaeger:
    image: jaegertracing/all-in-one:1.57
    ports:
      - "16686:16686"
      - "4318:4318"
    environment:
      COLLECTOR_OTLP_ENABLED: "true"
```

## Check Application { #check-app }

Start Jaeger, run the application, and create a user:

```bash
docker compose up -d

curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@example.com"}'
```

Open [http://localhost:16686](http://localhost:16686), choose the `guide-observability-app` service, and find a trace with the `user.create` span.

## Best Practices { #best-practices }

- Name spans after operations, not Java or Kotlin method names.
- Record exceptions and error status inside the span.
- Do not put personal data in span attributes.
- Restore the previous context after a manual span.
- Keep `service.name` stable for the environment.

## Summary { #summary }

You connected the OpenTelemetry exporter, added a manual span, and verified the trace in Jaeger.

## Key Concepts { #key-concepts }

Tracer:
: creates spans.

Span:
: a measured step inside a trace.

Context propagation:
: keeps nested work connected to the incoming request.

OTLP:
: the protocol used to send telemetry to a collector.

## Troubleshooting { #troubleshooting }

Trace is missing:
: Check `http://localhost:4318/v1/traces` and Jaeger availability.

Span appears as a separate trace:
: Check `setParent(otctx.getContext())` and context restoration.

Service is missing in Jaeger:
: Check `tracing.attributes."service.name"`.

## What's Next? { #whats-next }

- add business metrics in [Metrics with Kora](observability-metrics.md)
- add health endpoints in [Probes with Kora](observability-probes.md)
- compare details with [Tracing documentation](../documentation/tracing.md)

## Help { #help }

- compare code with the finished Java and Kotlin observability apps
- check exporter settings in [Tracing documentation](../documentation/tracing.md)
