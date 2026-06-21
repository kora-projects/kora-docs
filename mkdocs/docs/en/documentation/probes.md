---
description: "Explains Kora readiness and liveness probes, probe configuration, dependency health checks, and Kubernetes-style availability reporting. Use when working with ReadinessProbe, LivenessProbe, ProbeFailure, ProbesModule, CircuitBreaker."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora readiness and liveness probes, probe configuration, dependency health checks, and Kubernetes-style availability reporting; key triggers include ReadinessProbe, LivenessProbe, ProbeFailure, ProbesModule, CircuitBreaker."
---

Probes let you check application `liveness` and `readiness` through the private HTTP port.
They are usually used by orchestrators and load balancers to decide whether requests can be sent to the application and whether its instance should be restarted.
Having two separate probes helps distinguish temporary inability to receive traffic from a state where the process itself should be considered unhealthy.

Probes are handled by the [private HTTP server](http-server.md). By default, it runs on port `8085`.

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

To create a custom `liveness` probe, the component must implement the interface:

```java
public interface LivenessProbe {

    @Nullable
    LivenessProbeFailure probe();
}
```

The probe must return `LivenessProbeFailure` on error and `null` on success.

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

To create a custom `readiness` probe, the component must implement the interface:

```java
public interface ReadinessProbe {

    @Nullable
    ReadinessProbeFailure probe();
}
```

The probe must return `ReadinessProbeFailure` on error and `null` on success.

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

## Response { #response }

The private HTTP server returns:

- `200 OK` — if all probes returned `null`.
- `503 Service Unavailable` — if a probe returned `LivenessProbeFailure` or `ReadinessProbeFailure`.
- `503 Service Unavailable` — if a probe component is not ready yet.
- `408 Request Timeout` — if probe execution did not finish within `30` seconds.

## Recommendations { #recommendations }

???+ warning "Recommendation"

    **Probes that directly check external dependencies, such as databases, queues, or other services, are not recommended.**

    Temporary unavailability of an external dependency should not automatically restart the application. For such cases, use the [CircuitBreaker](resilient.md#circuitbreaker) pattern.

A good example for `ReadinessProbe` is a probe that returns an error while the service is warming up.
