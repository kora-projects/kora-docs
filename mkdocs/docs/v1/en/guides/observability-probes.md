---
search:
  exclude: true
title: Probes with Kora
summary: Build focused liveness and readiness probes for a Kora HTTP service, including private management endpoints, warm-up readiness, orchestration semantics, and practical checks.
tags: observability, probes, liveness, readiness, health-checks, kubernetes, management
---

# Probes with Kora { #observability-probes-kora }

This guide focuses only on probes. You will add liveness and readiness endpoints on the private port, create a custom readiness probe with a warm-up period, and verify how the application reports its
operational state to the platform.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java Observability App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-observability-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin Observability App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-observability-app).

## What You'll Build { #youll-build }

You will add:

- the private `/system/liveness` endpoint
- the private `/system/readiness` endpoint
- a simple process liveness probe
- a readiness probe that fails during warm-up
- practical verification with `curl`

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

Probes are small application health checks. They are not for normal users and they do not describe the business API. They are read by the platform: Kubernetes, a load balancer, a deployment system, or a local smoke check. The platform asks a simple question and decides what to do: send traffic, wait, or restart the process.

The most important part is to separate two questions. Liveness asks: "is the process alive or should it be restarted?". Readiness asks: "is this instance ready to receive traffic right now?". The answers can be different. An application can be alive but not ready: for example, it may be warming a cache, waiting for a mandatory downstream, or finishing startup initialization.

This guide uses these pieces:

- `LivenessProbe` describes process liveness
- `ReadinessProbe` describes traffic readiness
- `LivenessProbeFailure` and `ReadinessProbeFailure` explain unhealthy state
- private HTTP endpoints expose the result to the platform

Kora discovers probe components in the graph. You create a regular `@Component`, implement the required interface, and the HTTP server uses those components to answer private health endpoints.

### Probe Model { #probe-model }

A probe returns either `null` or a failure object. `null` means: "everything is fine". A failure means: "the check failed, here is a short reason". This model is intentionally simple, and that simplicity is useful.

Liveness should be conservative. If liveness returns a failure, the platform may decide that the process is stuck or broken and restart it. This is why liveness usually does not check every external system. A short network issue should not automatically become an application restart.

Readiness can be stricter. If readiness returns a failure, the platform usually stops sending traffic to this instance. The process keeps running, and readiness can become healthy again later. This is a good fit for warm-up, temporary dependency unavailability, or maintenance.

In this guide, readiness models warm-up with `WARMUP_PERIOD`. During the first milliseconds the application says: "I am alive, but still warming up". Later it returns `null`, and the instance becomes ready.

### Tools { #tools }

`LivenessProbe` and `ReadinessProbe` are Kora interfaces. They are intentionally small: each has a `probe()` method, and the result is easy to understand without extra infrastructure.

`ApplicationHealthProbe` is a simple liveness probe. It returns `null` because the minimal application is considered alive when the process is running and the graph works. This is still useful: the endpoint itself proves that the private HTTP server responds.

`CustomReadinessProbe` shows how to add domain readiness logic. In the example it is time-based warm-up, but in a real service this can check cache warm-up, migrations, a mandatory dependency, or internal state of a background worker.

The private port `8085` separates operational checks from the public API. Clients do not need to know how the application reports health to the platform. The platform needs a stable private path that it can call often and automatically.

### Operational Semantics { #operational-semantics }

Think of probes as a contract between the application and the platform. The application does not tell a long story. It reports state briefly, and the platform follows rules.

Typical logic looks like this:

- liveness healthy: do not restart the process
- liveness unhealthy: the process can be restarted
- readiness healthy: include the instance in traffic routing
- readiness unhealthy: temporarily stop sending traffic to this instance

This is why checks should not be mixed together. If the database is unavailable for one second, readiness may become unhealthy so traffic waits. But liveness does not have to fail unless the process itself is broken.

The practical result is that the application gets two clear private endpoints. One protects against stuck processes; the other helps the platform manage traffic during startup and temporary problems.

## Dependencies { #dependencies }

For basic probes, the HTTP server modules and Kora common components from the HTTP server application are enough. If you already completed the [HTTP Server Guide](http-server.md), no extra dependency
is usually required.

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

Keep the main HTTP application graph. Probes are discovered as regular graph components.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            UndertowHttpServerModule {  // <----- Connected module

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
        UndertowHttpServerModule  // <----- Connected module
    ```

## Configuration { #config }

Put probe endpoints on the private port:

```hocon title="src/main/resources/application.conf"
httpServer {
  publicApiHttpPort = 8080
  privateApiHttpPort = 8085
  privateApiHttpLivenessPath = "/system/liveness"
  privateApiHttpReadinessPath = "/system/readiness"
}
```

Keep paths explicit. That makes Docker Compose, Kubernetes probes, and local smoke checks easier to configure.

## Liveness Probe { #liveness-probe }

The liveness probe should be conservative. If it returns a failure, the platform may restart the process. In a minimal application, returning `null` means the process is alive.

===! ":fontawesome-brands-java: `Java`"

    ```java
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
    @Component
    class ApplicationHealthProbe : LivenessProbe {
        override fun probe(): LivenessProbeFailure? = null
    }
    ```

Do not check every external dependency in liveness. A short network issue can otherwise become unnecessary restarts.

## Readiness Probe { #readiness-probe }

Readiness can be stricter. It reports whether the instance can receive traffic right now. For demonstration, add a warm-up period.

===! ":fontawesome-brands-java: `Java`"

    ```java
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

In a real application, readiness often checks cache warm-up, mandatory downstream availability, or migration readiness. The meaning stays the same: if a failure is temporary, traffic should wait, but
the process does not necessarily need to restart.

## Check Application { #check-app }

Run the application and check the private endpoints:

```bash
curl -i http://localhost:8085/system/liveness
curl -i http://localhost:8085/system/readiness
```

Immediately after startup, readiness may return a warm-up failure. Shortly after that, the same request should succeed:

```bash
sleep 1
curl -i http://localhost:8085/system/readiness
```

The public port `8080` remains for the business API, not health endpoints.

## Best Practices { #best-practices }

- Keep liveness simple and resilient to short external failures.
- Use readiness for warm-up and temporary dependency unavailability.
- Keep probe endpoints on the private port.
- Return a clear failure message.
- Check probes locally before writing Kubernetes manifests.

## Summary { #summary }

You added liveness and readiness endpoints, implemented custom probe components, and verified warm-up behavior.

## Key Concepts { #key-concepts }

Liveness:
: signal that the process is alive and does not need restart.

Readiness:
: signal that the instance is ready to receive traffic.

Private management port:
: a closed port for operational endpoints.

Probe failure:
: a short message explaining the unhealthy state.

## Troubleshooting { #troubleshooting }

Endpoint is unavailable:
: Check `privateApiHttpPort`, `privateApiHttpLivenessPath`, and `privateApiHttpReadinessPath`.

Readiness is always unhealthy:
: Check the condition inside `CustomReadinessProbe`.

Application restarts too often:
: Make sure external dependencies are checked by readiness, not liveness.

## What's Next? { #whats-next }

- add business metrics in [Metrics with Kora](observability-metrics.md)
- add traces in [Tracing with Kora](observability-tracing.md)
- compare details with [Probes documentation](../documentation/probes.md)

## Help { #help }

- compare probe code with the finished Java and Kotlin observability apps
- check liveness/readiness semantics in [Probes documentation](../documentation/probes.md)
