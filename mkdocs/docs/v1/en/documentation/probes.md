---
description: "Explains Kora readiness and liveness probes, probe configuration, dependency health checks, and Kubernetes-style availability reporting. Use when working with ReadinessProbe, LivenessProbe, LivenessProbeFailure, ReadinessProbeFailure, CircuitBreaker."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora readiness and liveness probes, probe configuration, dependency health checks, and Kubernetes-style availability reporting; key triggers include ReadinessProbe, LivenessProbe, LivenessProbeFailure, ReadinessProbeFailure, CircuitBreaker."
---

Probes let you check application `liveness` and `readiness` through the private HTTP port.
They are usually used by orchestrators and load balancers to decide whether requests can be sent to the application and whether its instance should be restarted.
Having two separate probes helps distinguish temporary inability to receive traffic from a state where the process itself should be considered unhealthy.

Probes are handled by the [private HTTP server](http-server.md). By default, it runs on port `8085`.
The `LivenessProbe` and `ReadinessProbe` interfaces come from the core `ru.tinkoff.kora:common` module (a transitive dependency of every Kora application),
and the endpoints that expose them are provided by the [HTTP server](http-server.md) module, so no additional dependency is required to add a probe.

Both probe endpoints are always present on the private server, even when the application registers no custom probe of that kind — in that case the endpoint simply reports success.

For a step-by-step walkthrough before the reference details, see [Observability](../guides/observability.md).

## Liveness { #liveness }

This probe indicates that the application is alive and should not be restarted. Kora tries to expose this probe as early as possible so the orchestrator does not restart the application during normal startup.

Example of the private HTTP server path configuration described in the `HttpServerConfig` class (default value is shown):

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
        privateApiHttpLivenessPath = "/system/liveness" //(1)!
    }
    ```

    1. `Liveness` probe path on the private HTTP server (default: `/system/liveness`).

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      privateApiHttpLivenessPath: "/system/liveness" #(1)!
    ```

    1. `Liveness` probe path on the private HTTP server (default: `/system/liveness`).

To create a custom `liveness` probe, register a [component](container.md) that implements the `LivenessProbe` interface:

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
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.liveness.LivenessProbe;
    import ru.tinkoff.kora.common.liveness.LivenessProbeFailure;

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
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.liveness.LivenessProbe
    import ru.tinkoff.kora.common.liveness.LivenessProbeFailure

    @Component
    class ApplicationHealthProbe : LivenessProbe {
        override fun probe(): LivenessProbeFailure? = null
    }
    ```

## Readiness { #readiness }

This probe indicates that the application is ready to receive workload.

Example of the private HTTP server path configuration described in the `HttpServerConfig` class (default value is shown):

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
        privateApiHttpReadinessPath = "/system/readiness" //(1)!
    }
    ```

    1. `Readiness` probe path on the private HTTP server (default: `/system/readiness`).

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      privateApiHttpReadinessPath: "/system/readiness" #(1)!
    ```

    1. `Readiness` probe path on the private HTTP server (default: `/system/readiness`).

To create a custom `readiness` probe, register a [component](container.md) that implements the `ReadinessProbe` interface:

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
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.readiness.ReadinessProbe;
    import ru.tinkoff.kora.common.readiness.ReadinessProbeFailure;

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
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.readiness.ReadinessProbe
    import ru.tinkoff.kora.common.readiness.ReadinessProbeFailure
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

Kora collects **every** registered [component](container.md) that implements `LivenessProbe` (or `ReadinessProbe`) automatically —
you do not wire them together manually. Each endpoint runs all probes of its kind and aggregates the result:

- The endpoint returns `200 OK` only when **all** probes of that kind succeed.
- A single failing probe makes the whole endpoint report `503`, with the failing probe's message as the body.
- When no probe of that kind is registered, the endpoint returns `200 OK` — the private server always exposes both paths.

This lets you split independent readiness or liveness conditions across several small, focused probe components.

===! ":fontawesome-brands-java: `Java`"

    ```java
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.readiness.ReadinessProbe;
    import ru.tinkoff.kora.common.readiness.ReadinessProbeFailure;

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
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.readiness.ReadinessProbe
    import ru.tinkoff.kora.common.readiness.ReadinessProbeFailure

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

## Response { #response }

Each probe endpoint is served by the [private HTTP server](http-server.md) and returns a `text/plain` body together with a status code:

- `200 OK` — body `OK` — all registered probes returned `null`, or no probe of that kind is registered.
- `503 Service Unavailable` — body is the `message` of the returned `LivenessProbeFailure` / `ReadinessProbeFailure` — at least one probe reported a failure.
- `503 Service Unavailable` — body `Probe failed: <message>` — a probe threw an exception; the thrown exception is treated as a failure.
- `503 Service Unavailable` — body `Probe is not ready yet` — a probe component has not been initialized in the dependency container yet.
- `408 Request Timeout` — body `Probe failed: timeout` — probe execution did not finish within `30` seconds.

The endpoint responds as soon as the aggregated result is known; orchestrator and load-balancer health checks can therefore match on either the status code or the plaintext body.

## Recommendations { #recommendations }

???+ warning "Recommendation"

    **Probes that directly check external dependencies, such as databases, queues, or other services, are not recommended.**

    Temporary unavailability of an external dependency should not automatically restart the application. For such cases, use the [CircuitBreaker](resilient.md#circuitbreaker) pattern.

A probe should reflect the state of the application **itself**, not of the systems it talks to.
Good examples are a `ReadinessProbe` that reports a failure while the service is warming up,
or one that checks whether an internal component has finished its initialization.

Each probe runs on a dedicated executor (a virtual-thread executor when available, otherwise `ForkJoinPool.commonPool()`),
so a probe body may block without stalling the private HTTP server. The whole endpoint is still bounded by a `30` second timeout,
after which it responds with `408`, so keep probe logic fast and avoid long-running or unbounded work.
