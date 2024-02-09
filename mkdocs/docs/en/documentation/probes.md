Functionality that gives the application two methods for obtaining samples on a private port to provide information about service viability and readiness.

Requires a [HTTP server](http-server.md) connection.

## Liveness

This sample is responsible for indicating whether the application is currently alive. Kora tries to start giving this sample as early as possible, so that orchestrators know for sure that there are no problems at startup and don't try to restart the application.

By default, it is available under the `/system/liveness` path, but it can be customized through configuration:

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

## Readiness

This sample is responsible for indicating whether the application is currently ready to run.

By default, it is available at the `/system/readiness` path, but it can be customized through configuration.

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

## Recommendations

???+ warning "Tip"

    **We strongly discourage runs that test external dependencies such as databases or other services.**

    If external dependencies are not available, we recommend using the [CircuitBreaker](resilient.md#circuitbreaker) pattern. 

A good example for `ReadinessProbe` is prob that returns an error while the service is warming up.
