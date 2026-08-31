---
description: "Explains Kora readiness and liveness probes on the system HTTP server, probe paths in the httpServer.system config section, built-in framework probes, aggregation and response semantics, and Kubernetes-style availability reporting. Use when working with ReadinessProbe, LivenessProbe, ReadinessProbeFailure, LivenessProbeFailure, /system/readiness, /system/liveness."
agent:
  use_when: "Use this file for Kora docs or implementation questions about readiness and liveness probes, the system HTTP server endpoints /system/readiness and /system/liveness, probe path configuration under httpServer.system, built-in framework readiness probes, and waiting on readiness during startup; key triggers include ReadinessProbe, LivenessProbe, ReadinessProbeFailure, LivenessProbeFailure, readinessPath, livenessPath, Probe is not ready yet."
---

Probes let you check application `liveness` and `readiness` through the system HTTP port.
They are usually used by orchestrators and load balancers to decide whether requests can be sent to the application and whether its instance should be restarted.
Having two separate probes helps distinguish temporary inability to receive traffic from a state where the process itself should be considered unhealthy.

Probes are handled by the [system HTTP server](http-server.md#system-server), which by default listens on port `8085` — separately from the public server on port `8080`.
The same system server also exposes [metrics](metrics.md), so an orchestrator needs access to just one extra port.

Both probe endpoints are always present on the system server, even when the application registers no custom probe of that kind — in that case the endpoint simply reports success.

For a step-by-step walkthrough before the reference details, see [Probes with Kora](../guides/observability-probes.md) and [Observability](../guides/observability.md).

## Dependency { #dependency }

The `LivenessProbe` and `ReadinessProbe` interfaces live in the `io.koraframework:common` artifact,
which comes transitively with the [HTTP server](http-server.md) module, so adding a probe requires no additional dependency.

The endpoints that expose them are provided by `UndertowSystemHttpServerModule`.
`UndertowPublicHttpServerModule` extends that module, so an application that already serves public controllers gets both probe endpoints automatically:

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:http-server-undertow"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends UndertowPublicHttpServerModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:http-server-undertow")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : UndertowPublicHttpServerModule
    ```

An application that only needs the system endpoints — a worker or a consumer without a public API — can connect `UndertowSystemHttpServerModule` instead and still get both probes.

## Liveness { #liveness }

This probe indicates that the application is alive and should not be restarted.

Example of the system HTTP server path configuration described in the `SystemHttpServerConfig` class (default value is shown):

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer.system {
        livenessPath = "/system/liveness" //(1)!
    }
    ```

    1. `Liveness` probe path on the system HTTP server (default: `/system/liveness`).

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      system:
        livenessPath: "/system/liveness" #(1)!
    ```

    1. `Liveness` probe path on the system HTTP server (default: `/system/liveness`).

To create a custom `liveness` probe, register a [component](container.md#components) that implements the `LivenessProbe` interface:

```java
public interface LivenessProbe {

    @Nullable
    LivenessProbeFailure probe() throws Exception;
}
```

The probe must return `null` on success or a `LivenessProbeFailure` describing the problem.
`LivenessProbeFailure` is a record whose single `message` field becomes the `503` response body:

```java
public record LivenessProbeFailure(String message) {}
```

The `probe()` method is declared `throws Exception`, so the implementation may call checked-exception APIs directly.
A thrown exception is treated as a failure — see [Response](#response) for the exact status codes and bodies.

===! ":fontawesome-brands-java: `Java`"

    ```java
    import io.koraframework.common.annotation.Component;
    import io.koraframework.common.liveness.LivenessProbe;
    import io.koraframework.common.liveness.LivenessProbeFailure;

    @Component
    public final class ApplicationHealthProbe implements LivenessProbe {

        @Override
        public LivenessProbeFailure probe() {
            return null;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import io.koraframework.common.annotation.Component
    import io.koraframework.common.liveness.LivenessProbe
    import io.koraframework.common.liveness.LivenessProbeFailure

    @Component
    class ApplicationHealthProbe : LivenessProbe {
        override fun probe(): LivenessProbeFailure? = null
    }
    ```

The return type is annotated with [JSpecify](https://jspecify.dev/) `@Nullable` in `Java`, so a `Kotlin` implementation must declare the result as `LivenessProbeFailure?`.

## Readiness { #readiness }

This probe indicates that the application is ready to receive workload.

Example of the system HTTP server path configuration described in the `SystemHttpServerConfig` class (default value is shown):

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer.system {
        readinessPath = "/system/readiness" //(1)!
    }
    ```

    1. `Readiness` probe path on the system HTTP server (default: `/system/readiness`).

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      system:
        readinessPath: "/system/readiness" #(1)!
    ```

    1. `Readiness` probe path on the system HTTP server (default: `/system/readiness`).

To create a custom `readiness` probe, register a [component](container.md#components) that implements the `ReadinessProbe` interface:

```java
public interface ReadinessProbe {

    @Nullable
    ReadinessProbeFailure probe() throws Exception;
}
```

The probe must return `null` on success or a `ReadinessProbeFailure` describing the problem.
`ReadinessProbeFailure` is a record whose single `message` field becomes the `503` response body:

```java
public record ReadinessProbeFailure(String message) {}
```

As with `LivenessProbe`, the `probe()` method is declared `throws Exception` and a thrown exception is treated as a failure.

===! ":fontawesome-brands-java: `Java`"

    ```java
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
                return new ReadinessProbeFailure("Service is warming up");
            }
            return null;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
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
                ReadinessProbeFailure("Service is warming up")
            } else {
                null
            }
        }
    }
    ```

## Multiple probes { #multiple-probes }

Kora collects **every** registered [component](container.md#components) that implements `LivenessProbe` (or `ReadinessProbe`) automatically —
you do not wire them together manually and a probe does not need to be a [@Root component](container.md#root-component).
Each endpoint runs all probes of its kind on separate virtual threads and aggregates the result:

- The endpoint returns `200 OK` only when **all** probes of that kind succeed.
- A single failing probe makes the whole endpoint report `503`. When several probes fail, the message of the first failing probe in registration order becomes the response body.
- When no probe of that kind is registered, the endpoint returns `200 OK` — the system server always exposes both paths.

Probes are injected into the endpoint as promises rather than as ready components, which is what lets the system server answer before the rest of the container is built.
Until the container has created a probe component, the endpoint answers `503` with `Probe is not ready yet` instead of silently skipping it.

This lets you split independent readiness or liveness conditions across several small, focused probe components.

===! ":fontawesome-brands-java: `Java`"

    ```java
    import io.koraframework.common.annotation.Component;
    import io.koraframework.common.readiness.ReadinessProbe;
    import io.koraframework.common.readiness.ReadinessProbeFailure;

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

    1. Any number of `ReadinessProbe` components can coexist; the endpoint fails if any of them fails
    2. Check the state of an **internal** component, not an external dependency

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import io.koraframework.common.annotation.Component
    import io.koraframework.common.readiness.ReadinessProbe
    import io.koraframework.common.readiness.ReadinessProbeFailure

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

    1. Any number of `ReadinessProbe` components can coexist; the endpoint fails if any of them fails
    2. Check the state of an **internal** component, not an external dependency

## Built-in probes { #built-in-probes }

Several Kora components implement `ReadinessProbe` themselves, so they are aggregated together with your own probes without any extra wiring:

| Component | Module | Reports `not ready` when |
|-----------|--------|-------------------------|
| `UndertowHttpServer` | `io.koraframework:http-server-undertow` | the public [HTTP server](http-server.md) has not started listening yet, or its shutdown has begun |
| `GrpcServer` | `io.koraframework:grpc-server` | the [gRPC server](grpc-server.md) has not started yet, or is shutting down |
| `JdbcDataSource` | `io.koraframework:database-jdbc` | `jdbc.readinessProbe` is enabled and a pool connection fails validation |
| `JobExecutorReadinessProbe` | `io.koraframework.experimental:camunda-engine-bpmn` | the [Camunda](camunda7-bpmn.md) `JobExecutor` is not active |

Because of these, `GET /system/readiness` answering `200` is a reliable "the application is up" signal —
which is why it is the right thing for an orchestrator, a smoke test, or a test container to wait on, rather than a startup log line.

The system server's own listener is deliberately **not** part of this aggregation: it is registered under a separate tag,
so the probe endpoints keep answering while the public server and the rest of the container are still starting.

During [graceful shutdown](container.md#graceful-shutdown) the public server flips its readiness state to a failure at the very beginning of its release,
before it waits out `httpServer.shutdownWait` (default: `30s`) for in-flight requests.
A load balancer polling readiness therefore sees the instance leave rotation before it starts refusing connections.

## Response { #response }

Each probe endpoint is served by the [system HTTP server](http-server.md#system-server), accepts `GET` and returns a `text/plain;charset=utf-8` body together with a status code:

| Status | Body | Meaning |
|--------|------|---------|
| `200 OK` | `OK` | all registered probes returned `null`, or no probe of that kind is registered |
| `503 Service Unavailable` | the `message` of the returned `LivenessProbeFailure` / `ReadinessProbeFailure` | at least one probe reported a failure |
| `503 Service Unavailable` | `Probe failed: <error>` | a probe threw an exception; the thrown exception is treated as a failure |
| `503 Service Unavailable` | `Probe is not ready yet` | a probe component has not been created in the [dependency container](container.md) yet |
| `408 Request Timeout` | `Probe failed: timeout` | probe execution did not finish within `30` seconds |
| `500 Internal Server Error` | the error message | the endpoint could not run the probes at all, for example a probe task could not be submitted for execution |

The endpoint responds as soon as the aggregated result is known; orchestrator and load-balancer health checks can therefore match on either the status code or the plaintext body.

Only `GET` is routed for the probe paths, so any other method gets the router's standard `405 Method Not Allowed` with an `Allow` header.

## Testing { #testing }

A probe is an ordinary [component](junit5.md#component), so an in-process [@KoraAppTest](junit5.md) can inject it and call `probe()` directly,
without going through the HTTP endpoint:

===! ":fontawesome-brands-java: `Java`"

    ```java
    import io.koraframework.test.extension.junit5.KoraAppTest;
    import io.koraframework.test.extension.junit5.TestComponent;
    import org.junit.jupiter.api.Test;

    import static org.junit.jupiter.api.Assertions.assertNull;

    @KoraAppTest(Application.class)
    class ProbeTests {

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

    1. `null` means the probe succeeded
    2. Readiness with a warm-up period becomes healthy only after some time, so poll it instead of asserting once

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import io.koraframework.test.extension.junit5.KoraAppTest
    import io.koraframework.test.extension.junit5.TestComponent
    import org.junit.jupiter.api.Assertions.assertNull
    import org.junit.jupiter.api.Test

    @KoraAppTest(Application::class)
    class ProbeTests {

        @TestComponent
        lateinit var livenessProbe: ApplicationHealthProbe
        @TestComponent
        lateinit var readinessProbe: CustomReadinessProbe

        @Test
        fun probesEventuallyReportHealthyState() {
            assertNull(livenessProbe.probe()) //(1)!

            for (i in 0 until 10) {
                if (readinessProbe.probe() == null) { //(2)!
                    return
                }
                Thread.sleep(100L)
            }

            assertNull(readinessProbe.probe())
        }
    }
    ```

    1. `null` means the probe succeeded
    2. Readiness with a warm-up period becomes healthy only after some time, so poll it instead of asserting once

In a [black-box test](../guides/testing-black-box.md) the readiness endpoint is the startup signal for the container.
Wait on it rather than on a log line — the wording of Kora startup messages is not a contract and can change between versions:

===! ":fontawesome-brands-java: `Java`"

    ```java
    import org.testcontainers.containers.GenericContainer;
    import org.testcontainers.containers.wait.strategy.Wait;

    import java.net.URI;
    import java.time.Duration;

    final class AppContainer extends GenericContainer<AppContainer> {

        AppContainer() {
            super("my-application:latest");

            withExposedPorts(8080, 8085); //(1)!
            withStartupTimeout(Duration.ofSeconds(30));
            waitingFor(Wait.forHttp("/system/readiness").forPort(8085).forStatusCode(200)); //(2)!
        }

        URI getURI() {
            return URI.create("http://" + getHost() + ":" + getMappedPort(8080));
        }

        URI getSystemURI() { //(3)!
            return URI.create("http://" + getHost() + ":" + getMappedPort(8085));
        }
    }
    ```

    1. Both the public port and the system port have to be exposed
    2. The readiness probe is polled on the system port, not the public one
    3. Handy for asserting on `/system/liveness`, `/system/readiness` and `/metrics` inside the test

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import org.testcontainers.containers.GenericContainer
    import org.testcontainers.containers.wait.strategy.Wait
    import java.net.URI
    import java.time.Duration

    class AppContainer : GenericContainer<AppContainer>("my-application:latest") {

        init {
            withExposedPorts(8080, 8085) //(1)!
            withStartupTimeout(Duration.ofSeconds(30))
            waitingFor(Wait.forHttp("/system/readiness").forPort(8085).forStatusCode(200)) //(2)!
        }

        fun getURI(): URI = URI.create("http://$host:${getMappedPort(8080)}")

        fun getSystemURI(): URI = URI.create("http://$host:${getMappedPort(8085)}") //(3)!
    }
    ```

    1. Both the public port and the system port have to be exposed
    2. The readiness probe is polled on the system port, not the public one
    3. Handy for asserting on `/system/liveness`, `/system/readiness` and `/metrics` inside the test

## Recommendations { #recommendations }

???+ warning "Recommendation"

    **Probes that directly check external dependencies, such as databases, queues, or other services, are not recommended.**

    Temporary unavailability of an external dependency should not automatically restart the application. For such cases, use the [CircuitBreaker](resilient.md#circuitbreaker) pattern.

A probe should reflect the state of the application **itself**, not of the systems it talks to.
Good examples are a `ReadinessProbe` that reports a failure while the service is warming up,
or one that checks whether an internal component has finished its initialization.

Each probe runs on its own virtual thread, so a probe body may block without stalling the system HTTP server.
The whole endpoint is still bounded by a `30` second timeout, after which it responds with `408`, so keep probe logic fast and avoid long-running or unbounded work.

A probe is invoked on every request to its endpoint and several requests may overlap, so the implementation must be cheap, side-effect free and safe to call concurrently.
Cache or precompute anything expensive in the component itself and let `probe()` only read the already-known state.
