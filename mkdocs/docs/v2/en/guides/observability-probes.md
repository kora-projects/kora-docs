---
search:
  exclude: true
title: Probes with Kora
summary: Build focused liveness and readiness probes for a Kora HTTP service, including the system server endpoints, warm-up readiness, built-in framework probes, response semantics, and orchestration.
description: "Step-by-step liveness and readiness probes for a Kora HTTP service: the LivenessProbe and ReadinessProbe interfaces from io.koraframework:common, probe endpoints on the system HTTP server, the httpServer.system.port, livenessPath and readinessPath configuration, custom probe components registered as a plain @Component, warm-up readiness, built-in framework probes, aggregation across several probes, the 200/503/408 response contract, and Kubernetes probe wiring."
agent:
  use_when: "Use this file for questions about adding health checks to a Kora application step by step: LivenessProbe, ReadinessProbe, LivenessProbeFailure, ReadinessProbeFailure, /system/liveness, /system/readiness, httpServer.system.port 8085, livenessPath and readinessPath, why a probe does not need @Root or a tag, what 'Probe is not ready yet' means, the 30 second probe timeout and 408 response, built-in readiness probes of the HTTP and gRPC servers, readiness during graceful shutdown, and mapping probes to Kubernetes livenessProbe and readinessProbe."
tags: observability, probes, liveness, readiness, health-checks, kubernetes, system-server
---

# Probes with Kora { #observability-probes-kora }

This guide focuses only on probes. You will take the HTTP server application and give the platform two answers it can act on: whether the process is still healthy, and whether this instance should be
receiving traffic right now.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java Observability App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-observability-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin Observability App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-observability-app).

## What You Will Build { #youll-build }

You will add:

- the `/system/liveness` and `/system/readiness` endpoints on the system port
- a liveness probe for the process itself
- a readiness probe that reports a warm-up period
- a second readiness probe that reports on an internal component
- an understanding of the status codes and bodies the platform will see
- probe assertions in a test, and probe wiring in a Kubernetes manifest

## What You Will Need { #youll-need }

- JDK 25 or later
- Gradle 9+
- Docker, if you want to run the black-box smoke test locally
- A text editor or IDE
- Completed [HTTP Server Guide](http-server.md)

Kora 2.0 artifacts are compiled for Java 25, so the JDK that compiles the application must be 25 or newer.

## Prerequisites { #prerequisites }

!!! note "Required Foundation"

    This guide assumes you have completed **[HTTP Server Guide](http-server.md)** and already have the HTTP controllers, DTOs, repository, service, and configuration from that guide in place.

    If you haven't completed the HTTP server guide yet, do that first, because this observability guide keeps that HTTP surface and layers telemetry on top of it.

## Overview { #overview }

Probes are the smallest observability signal, and the only one with teeth. Metrics and traces are read by people looking into a problem. Probes are read by machines that will act on the answer:
Kubernetes will restart your process, a load balancer will take the instance out of rotation, a deployment will refuse to proceed. Nobody is going to read the nuance, so the answer has to be right.

Everything rests on separating two questions that sound alike and mean very different things. Liveness asks *"is this process broken beyond recovery, should it be restarted?"* Readiness asks *"can
this instance serve a request right now?"* An application can very reasonably be alive but not ready — it is warming a cache, finishing startup, or shedding traffic while it shuts down. Answering the
second question with the first is how a service ends up in a restart loop during a dependency blip.

### Probe Model { #probe-model }

A probe returns either `null` or a failure. `null` means "fine". A failure carries one short message explaining what is wrong. That is the entire model, and its bluntness is the point: there is no
degraded state, no percentage, nothing for the orchestrator to interpret.

Liveness should be **conservative**. A liveness failure gets the process killed. That is the right response to a deadlocked thread pool or unrecoverable internal corruption, and the wrong response to a
database that was unreachable for two seconds. When in doubt, liveness returns `null`.

Readiness can be **strict**. A readiness failure only stops traffic; the process keeps running and can recover on its own. That makes it the correct home for warm-up, for a mandatory dependency that is
temporarily gone, and for draining during shutdown.

In this guide readiness models warm-up. For the first half second the application says "I am alive, but not yet ready". Then it starts returning `null` and the instance joins the rotation.

### Tools { #tools }

`LivenessProbe` and `ReadinessProbe` are Kora interfaces with a single `probe()` method each. `LivenessProbeFailure` and `ReadinessProbeFailure` are records with a single `message` field, and that
message becomes the HTTP response body.

The **system HTTP server** exposes both endpoints. It listens on its own port, separate from the public API, so an orchestrator can poll health without touching business traffic and without those
endpoints being reachable from outside the cluster.

**Component discovery** does the wiring. You write a plain `@Component` that implements the interface; Kora finds every such component and hands them to the endpoint. There is no registry to update and
no annotation to remember.

### Operational Semantics { #operational-semantics }

Think of a probe as a contract between the application and the platform. The application reports state briefly; the platform applies rules:

- liveness healthy → leave the process alone
- liveness unhealthy → the process may be restarted
- readiness healthy → route traffic to this instance
- readiness unhealthy → stop routing traffic here, but leave the process running

The practical consequence is that mixing the two checks is a real outage mechanism. If a shared database goes away for a second and you put that check in liveness, every instance of the service fails
liveness at the same moment and the orchestrator restarts the entire fleet — turning a one-second blip into a cold start. The same check in readiness parks traffic until the database comes back.

## Dependencies { #dependencies }

None. `LivenessProbe` and `ReadinessProbe` live in the `io.koraframework:common` artifact, which arrives transitively with the HTTP server module you already have.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    dependencies {
        // ... existing dependencies from the HTTP server guide ...
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    dependencies {
        // ... existing dependencies from the HTTP server guide ...
    }
    ```

## Modules { #modules }

Nothing to add here either. The endpoints come from `UndertowSystemHttpServerModule`, and `UndertowPublicHttpServerModule` — the module the HTTP server guide already connected — extends it.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            UndertowPublicHttpServerModule {  // <----- Already gives you both probe endpoints

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
        UndertowPublicHttpServerModule  // <----- Already gives you both probe endpoints

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

Both probe paths are served whether or not you write a probe. With no probe registered they answer `200 OK`, which is a deliberate choice: an application that has not thought about health still reports
"up" rather than blocking its own deployment.

An application with no public API at all — a worker, a Kafka consumer — can connect `UndertowSystemHttpServerModule` on its own and get the probe endpoints without starting a public server.

## Configuration { #config }

Probes live on the system port next to `/metrics`.

For the full configuration reference, see [Probes](../documentation/probes.md) and [HTTP Server](../documentation/http-server.md#system-server).

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
      port = 8080 //(1)!
      system {
        port = 8085 //(2)!
        livenessPath = "/system/liveness" //(3)!
        readinessPath = "/system/readiness" //(4)!
      }
    }
    ```

    1.  Public HTTP port used by application endpoints (default: `8080`).
    2.  System HTTP port that serves probes and metrics (default: `8085`).
    3.  Path of the liveness endpoint on the system server (default: `/system/liveness`).
    4.  Path of the readiness endpoint on the system server (default: `/system/readiness`).

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      port: 8080 #(1)!
      system:
        port: 8085 #(2)!
        livenessPath: "/system/liveness" #(3)!
        readinessPath: "/system/readiness" #(4)!
    ```

    1.  Public HTTP port used by application endpoints (default: `8080`).
    2.  System HTTP port that serves probes and metrics (default: `8085`).
    3.  Path of the liveness endpoint on the system server (default: `/system/liveness`).
    4.  Path of the readiness endpoint on the system server (default: `/system/readiness`).

Every one of these keys already holds that value by default, so the application works without writing any of them. Spelling them out is still worth it: these paths end up copied into a Kubernetes
manifest, a Compose healthcheck, and a Testcontainers wait strategy, and having them visible in the config is what keeps those four places agreeing with each other.

## Liveness Probe { #liveness-probe }

Register a plain component that implements `LivenessProbe`. Returning `null` means the process is alive.

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/io/koraframework/guide/observability/health/ApplicationHealthProbe.java`:

    ```java
    package io.koraframework.guide.observability.health;

    import io.koraframework.common.annotation.Component;
    import io.koraframework.common.liveness.LivenessProbe;
    import io.koraframework.common.liveness.LivenessProbeFailure;

    @Component //(1)!
    public final class ApplicationHealthProbe implements LivenessProbe {

        @Override
        public LivenessProbeFailure probe() {
            return null; //(2)!
        }
    }
    ```

    1.  A plain component is enough. A probe does not need `@Root` and does not need a tag.
    2.  `null` is success. Anything else is a failure with a message.

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/io/koraframework/guide/observability/health/ApplicationHealthProbe.kt`:

    ```kotlin
    package io.koraframework.guide.observability.health

    import io.koraframework.common.annotation.Component
    import io.koraframework.common.liveness.LivenessProbe
    import io.koraframework.common.liveness.LivenessProbeFailure

    @Component //(1)!
    class ApplicationHealthProbe : LivenessProbe {
        override fun probe(): LivenessProbeFailure? = null //(2)!
    }
    ```

    1.  A plain component is enough. A probe does not need `@Root` and does not need a tag.
    2.  `null` is success. Anything else is a failure with a message.

The return type is annotated with [JSpecify](https://jspecify.dev/) `@Nullable` in `Java`, so a `Kotlin` implementation must declare the result as `LivenessProbeFailure?`.

A liveness probe that always returns `null` still earns its keep: the endpoint answering at all proves the system server is up, the graph was built, and the process is responsive rather than wedged.
Resist the temptation to make it clever. The question it answers is "would a restart help?", and for almost every failure mode the honest answer is no.

## Readiness Probe { #readiness-probe }

Readiness is where the interesting logic goes, because a failure here is cheap and recoverable.

### Warm-Up { #warmup }

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/io/koraframework/guide/observability/health/CustomReadinessProbe.java`:

    ```java
    package io.koraframework.guide.observability.health;

    import io.koraframework.common.annotation.Component;
    import io.koraframework.common.readiness.ReadinessProbe;
    import io.koraframework.common.readiness.ReadinessProbeFailure;

    import java.time.Duration;
    import java.time.Instant;

    @Component
    public final class CustomReadinessProbe implements ReadinessProbe {

        private static final Duration WARMUP_PERIOD = Duration.ofMillis(500);

        private final Instant startedAt = Instant.now();

        @Override
        public ReadinessProbeFailure probe() {
            var readyAt = startedAt.plus(WARMUP_PERIOD);
            if (Instant.now().isBefore(readyAt)) {
                return new ReadinessProbeFailure("Service is warming up"); //(1)!
            }
            return null;
        }
    }
    ```

    1.  This message becomes the body of the `503` response, so make it say something a person reading an alert can use.

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/io/koraframework/guide/observability/health/CustomReadinessProbe.kt`:

    ```kotlin
    package io.koraframework.guide.observability.health

    import io.koraframework.common.annotation.Component
    import io.koraframework.common.readiness.ReadinessProbe
    import io.koraframework.common.readiness.ReadinessProbeFailure
    import java.time.Duration
    import java.time.Instant

    @Component
    class CustomReadinessProbe : ReadinessProbe {
        private val startedAt = Instant.now()

        override fun probe(): ReadinessProbeFailure? {
            val readyAt = startedAt.plus(Duration.ofMillis(500))
            return if (Instant.now().isBefore(readyAt)) {
                ReadinessProbeFailure("Service is warming up") //(1)!
            } else {
                null
            }
        }
    }
    ```

    1.  This message becomes the body of the `503` response, so make it say something a person reading an alert can use.

Half a second is a demo value that makes the behavior observable with `curl`. A real warm-up is whatever your service actually has to finish first: a cache preload, a rules table, a model, an initial
sync.

### Component Readiness { #component-readiness }

Kora collects **every** component implementing `ReadinessProbe` and runs them all, so readiness conditions do not have to live in one class. Splitting them keeps each probe focused and gives a much
more useful failure message than a single combined check.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class ComponentReadinessProbe implements ReadinessProbe { //(1)!

        private final SomeComponent component;

        public ComponentReadinessProbe(SomeComponent component) {
            this.component = component;
        }

        @Override
        public ReadinessProbeFailure probe() {
            if (component.isInitialized()) { //(2)!
                return null;
            }
            return new ReadinessProbeFailure("SomeComponent is not initialized yet");
        }
    }
    ```

    1.  Any number of `ReadinessProbe` components can coexist; the endpoint fails if any of them fails.
    2.  Check the state of an **internal** component, not an external dependency.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ComponentReadinessProbe(
        private val component: SomeComponent
    ) : ReadinessProbe { //(1)!

        override fun probe(): ReadinessProbeFailure? {
            return if (component.isInitialized) { //(2)!
                null
            } else {
                ReadinessProbeFailure("SomeComponent is not initialized yet")
            }
        }
    }
    ```

    1.  Any number of `ReadinessProbe` components can coexist; the endpoint fails if any of them fails.
    2.  Check the state of an **internal** component, not an external dependency.

Each probe of a kind runs on its own virtual thread and the endpoint aggregates the results: `200` only when all of them return `null`, `503` as soon as one fails. When several fail, the message of the
first failing probe in registration order becomes the body.

???+ warning "Recommendation"

    **Probes that directly check external dependencies, such as databases, queues, or other services, are not recommended.**

    Temporary unavailability of an external dependency should not automatically restart the application. For such cases, use the [CircuitBreaker](../documentation/resilient.md#circuitbreaker) pattern.

A probe is invoked on every request to its endpoint, and several requests can overlap, so `probe()` must be cheap, side-effect free, and safe to call concurrently. Precompute anything expensive in the
component itself and let `probe()` only read state that is already known.

## Built-in Probes { #built-in-probes }

Several Kora components implement `ReadinessProbe` themselves and are aggregated together with yours, with no extra wiring:

| Component | Module | Reports `not ready` when |
|-----------|--------|-------------------------|
| `UndertowHttpServer` | `io.koraframework:http-server-undertow` | the public [HTTP server](../documentation/http-server.md) has not started listening yet, or its shutdown has begun |
| `GrpcServer` | `io.koraframework:grpc-server` | the [gRPC server](../documentation/grpc-server.md) has not started yet, or is shutting down |
| `JdbcDataSource` | `io.koraframework:database-jdbc` | `jdbc.readinessProbe` is enabled and a pool connection fails validation |

This is why `GET /system/readiness` answering `200` is a trustworthy "the application is up" signal even before you write a single probe of your own — and why it is the right thing for an orchestrator,
a smoke test, or a test container to wait on instead of a startup log line, whose wording is not a contract.

The system server's own listener is deliberately left out of this aggregation. It is registered under a separate tag, which is what lets the probe endpoints answer while the public server and the rest
of the container are still starting.

During [graceful shutdown](../documentation/container.md#graceful-shutdown) the public server flips its readiness to a failure at the very beginning of its release, *before* it waits out
`httpServer.shutdownWait` (default: `30s`) for in-flight requests. A load balancer polling readiness therefore sees the instance leave rotation before it starts refusing connections — which is exactly
the ordering you want during a rolling deploy.

## Response Semantics { #response-semantics }

Both endpoints accept `GET` and answer with a `text/plain;charset=utf-8` body:

| Status | Body | Meaning |
|--------|------|---------|
| `200 OK` | `OK` | all registered probes returned `null`, or no probe of that kind is registered |
| `503 Service Unavailable` | the failure `message` | at least one probe reported a failure |
| `503 Service Unavailable` | `Probe failed: <error>` | a probe threw an exception; a thrown exception is treated as a failure |
| `503 Service Unavailable` | `Probe is not ready yet` | a probe component has not been created in the container yet |
| `408 Request Timeout` | `Probe failed: timeout` | probe execution did not finish within `30` seconds |
| `500 Internal Server Error` | the error message | the endpoint could not run the probes at all |

Two of these are worth remembering because they look like bugs the first time you see them.

`Probe is not ready yet` is not your probe failing — it is your probe not existing yet. Probes are injected as promises rather than as ready components, which is what allows the system server to answer
before the whole container is built. During startup the endpoint reports this instead of silently skipping the probe.

`408` with `Probe failed: timeout` means the aggregate ran past 30 seconds. Since `probe()` is declared `throws Exception` and runs on a virtual thread, blocking inside it is allowed and it is easy to
write a probe that waits on something that never arrives. The timeout is the backstop, not a budget to spend.

Only `GET` is routed for probe paths, so any other method gets the router's standard `405 Method Not Allowed` with an `Allow` header.

## Testing Probes { #testing-probes }

A probe is an ordinary component, so a test can inject it and call `probe()` directly, without HTTP.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(Application.class)
    class ObservabilityAppTest {

        @TestComponent
        private ApplicationHealthProbe livenessProbe;
        @TestComponent
        private CustomReadinessProbe readinessProbe;

        @Test
        void probesEventuallyReportHealthyState() throws Exception {
            assertNull(livenessProbe.probe()); //(1)!

            for (int i = 0; i < 10; i++) {
                if (readinessProbe.probe() == null) { //(2)!
                    return;
                }
                Thread.sleep(100L);
            }

            assertNull(readinessProbe.probe());
        }
    }
    ```

    1.  `null` means the probe succeeded.
    2.  Readiness with a warm-up period only becomes healthy after some time, so poll it instead of asserting once.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(Application::class)
    class ObservabilityAppTest {

        @TestComponent
        lateinit var livenessProbe: ApplicationHealthProbe
        @TestComponent
        lateinit var readinessProbe: CustomReadinessProbe

        @Test
        fun probesEventuallyReportHealthyState() {
            assertNull(livenessProbe.probe()) //(1)!

            repeat(10) {
                if (readinessProbe.probe() == null) { //(2)!
                    return
                }
                Thread.sleep(100L)
            }

            assertNull(readinessProbe.probe())
        }
    }
    ```

    1.  `null` means the probe succeeded.
    2.  Readiness with a warm-up period only becomes healthy after some time, so poll it instead of asserting once.

In a [black-box test](testing-black-box.md) the readiness endpoint is the startup signal for the container:

===! ":fontawesome-brands-java: `Java`"

    ```java
    withExposedPorts(8080, 8085); //(1)!
    withStartupTimeout(Duration.ofSeconds(30));
    waitingFor(Wait.forHttp("/system/readiness").forPort(8085).forStatusCode(200)); //(2)!
    ```

    1.  Both the public port and the system port have to be exposed.
    2.  Readiness is polled on the system port, not the public one.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    withExposedPorts(8080, 8085) //(1)!
    withStartupTimeout(Duration.ofSeconds(30))
    waitingFor(Wait.forHttp("/system/readiness").forPort(8085).forStatusCode(200)) //(2)!
    ```

    1.  Both the public port and the system port have to be exposed.
    2.  Readiness is polled on the system port, not the public one.

## Check Application { #check-app }

Run the application and call both endpoints:

```bash
./gradlew run
```

```bash
curl -i http://localhost:8085/system/liveness
curl -i http://localhost:8085/system/readiness
```

Immediately after startup, readiness may still report warm-up:

```text
HTTP/1.1 503 Service Unavailable
Content-Type: text/plain;charset=utf-8

Service is warming up
```

A moment later the same request succeeds:

```bash
sleep 1
curl -i http://localhost:8085/system/readiness
```

```text
HTTP/1.1 200 OK
Content-Type: text/plain;charset=utf-8

OK
```

Confirm the separation while you are here — the probes are not on the public port, and the business API is not on the system port:

```bash
curl -i http://localhost:8080/system/readiness  # 404, this port serves the business API
```

## Kubernetes { #kubernetes }

The two endpoints map directly onto the two Kubernetes probes. Expose the system port on the container and point each probe at its path:

```yaml
ports:
  - name: http
    containerPort: 8080
  - name: system
    containerPort: 8085 #(1)!

livenessProbe:
  httpGet:
    path: /system/liveness
    port: system
  periodSeconds: 10
  failureThreshold: 3 #(2)!

readinessProbe:
  httpGet:
    path: /system/readiness
    port: system
  periodSeconds: 5 #(3)!
```

1.  The system port has to be declared on the container for the probes to reach it.
2.  Several consecutive failures before a restart, so one slow answer does not kill a healthy process.
3.  Readiness is polled more often than liveness, because acting on it is cheap.

Only the public port belongs in a `Service`. The system port stays reachable from the node for the kubelet and from a monitoring agent, and stays off the public routing path.

## Best Practices { #best-practices }

- Keep liveness simple and resilient to short external failures; when unsure, return `null`.
- Use readiness for warm-up, draining, and temporary internal unavailability.
- Check internal state, not external dependencies — use a [CircuitBreaker](../documentation/resilient.md#circuitbreaker) for those.
- Split independent conditions into several small probes to get a useful failure message.
- Keep `probe()` cheap, side-effect free, and safe to call concurrently.
- Wait on `/system/readiness` in tests and containers instead of on a log line.
- Keep the probe endpoints on the system port and off the public `Service`.

## Summary { #summary }

You exposed liveness and readiness on the system port, wrote a conservative liveness probe and a readiness probe with a warm-up period, saw how Kora aggregates several probes with its own built-in
ones, learned what each status code and body means, and wired the endpoints into a test and a Kubernetes manifest.

## Key Concepts { #key-concepts }

Liveness:
: the signal that the process is healthy and should not be restarted.

Readiness:
: the signal that this instance can serve traffic right now.

Probe failure:
: a record with one `message` that becomes the `503` response body.

System server:
: the separate port that serves probes and metrics, away from the business API.

Aggregation:
: all probes of a kind run in parallel; one failure fails the endpoint.

## Troubleshooting { #troubleshooting }

The endpoint answers `404`:
: You are on the public port. Probes live on `httpServer.system.port` (default: `8085`).

The endpoint answers `200` but your probe never runs:
: Confirm the class is annotated `@Component` and implements the interface from `io.koraframework.common.liveness` or `io.koraframework.common.readiness`.

`Probe is not ready yet`:
: The probe component has not been created in the container yet. Normal during startup; persistent means the component is failing to build.

`408` with `Probe failed: timeout`:
: A probe blocked for more than `30` seconds. Move the waiting out of `probe()` and let it read precomputed state.

Readiness never becomes healthy:
: Check the condition in your probe, then check the built-in ones — the public HTTP server reports not-ready until it is actually listening.

The application restarts in a loop:
: An external dependency is being checked in liveness. Move that check to readiness.

Readiness fails during shutdown:
: That is intended. The public server flips readiness before waiting out `httpServer.shutdownWait` so traffic drains first.

## What's Next? { #whats-next }

- add business metrics in [Metrics with Kora](observability-metrics.md)
- add traces in [Tracing with Kora](observability-tracing.md)
- wire all signals into one application in [Observability and Monitoring with Kora](observability.md)
- compare details with [Probes documentation](../documentation/probes.md)

## Help { #help }

- inspect the finished Java and Kotlin observability applications
- check aggregation and response semantics in [Probes documentation](../documentation/probes.md)
- see how a container waits on readiness in [Black-Box Testing](testing-black-box.md)
