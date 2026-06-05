---
description: "Explains Kora readiness and liveness probes, probe configuration, dependency health checks, and Kubernetes-style availability reporting. Use when working with ReadinessProbe, LivenessProbe, ProbeFailure, ProbesModule, CircuitBreaker."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora readiness and liveness probes, probe configuration, dependency health checks, and Kubernetes-style availability reporting; key triggers include ReadinessProbe, LivenessProbe, ProbeFailure, ProbesModule, CircuitBreaker."
---

Functionality that gives the application two methods for obtaining probes on a private port about service readiness/liveness.

Provided by adding a [private HTTP server](http-server.md) module.

For a step-by-step walkthrough before the reference details, see [Observability](../guides/observability.md).

## Liveness { #liveness }

This sample is responsible for indicating whether the application is currently alive. Kora tries to start giving this sample as early as possible, so that orchestrators know for sure that there are no problems at startup and don't try to restart the application.

Example of the HTTP server path configuration for probe ping described in the `HttpServerConfig` class (default values are specified):

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
        privateApiHttpLivenessPath = "/system/liveness"
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      privateApiHttpLivenessPath: "/system/liveness"
    ```

Creating your custom viability sample requires the component to implement the interface:
```java
public interface LivenessProbe {

    @Nullable
    LivenessProbeFailure probe();
}
```

The sample shall return `LivenessProbeFailure` on error, and `null` on success.

## Readiness { #readiness }

This sample is responsible for indicating whether the application is currently ready to run.

Example of the HTTP server path configuration for probe ping described in the `HttpServerConfig` class (default values are specified):

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
        privateApiHttpReadinessPath = "/system/readiness"
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      privateApiHttpReadinessPath: "/system/readiness"
    ```

Creating your custom viability sample requires the component to implement the interface:
```java
public interface ReadinessProbe {

    @Nullable
    ReadinessProbeFailure probe();
}
```

The sample shall return `ReadinessProbeFailure` in case of error, and `null` in case of success.

## Recommendations { #recommendations }

???+ warning "Recommendation"

    **We strongly discourage runs that test external dependencies such as databases or other services.**

    If external dependencies are not available, we recommend using the [CircuitBreaker](resilient.md#circuitbreaker) pattern. 

A good example for `ReadinessProbe` is prob that returns an error while the service is warming up.
