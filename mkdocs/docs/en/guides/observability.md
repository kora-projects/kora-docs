---
title: Observability & Monitoring with Kora
summary: Learn how to add comprehensive monitoring, metrics, tracing, and health checks to your Kora applications
tags: observability, metrics, tracing, logging, health-checks, monitoring
---

# Observability & Monitoring with Kora

This guide shows you how to add comprehensive observability to your Kora applications with metrics, distributed tracing, structured logging, and health checks.

## What You'll Build

You'll enhance your JSON API with:

- **Metrics collection**: HTTP request metrics, custom business metrics
- **Distributed tracing**: Request tracing with OpenTelemetry
- **Structured logging**: Consistent log formatting and levels
- **Health checks**: Liveness and readiness probes for container orchestration
- **Monitoring endpoints**: Metrics and health check HTTP endpoints

## What You'll Need

- JDK 17 or later
- Gradle 7.0+
- A text editor or IDE
- Completed [Creating Your First Kora App](../getting-started.md) guide

## Prerequisites

!!! note "Required: Complete Basic Kora Setup"

    This guide assumes you have completed the **[Create Your First Kora App](../getting-started.md)** guide and have a working Kora project with basic setup.

    If you haven't completed the basic guide yet, please do so first as this guide builds upon that foundation.

## Add Dependencies

Add the following observability dependencies to your existing Kora project:

===! ":fontawesome-brands-java: `Java`"

    ```gradle title="build.gradle"
    dependencies {
        // ... existing dependencies ...

        implementation("ru.tinkoff.kora:micrometer-module")
        implementation("ru.tinkoff.kora:opentelemetry-tracing")
    }
    ```

===! ":simple-kotlin: `Kotlin`"

    ```kotlin title="build.gradle.kts"
    dependencies {
        // ... existing dependencies ...

        implementation("ru.tinkoff.kora:micrometer-module")
        implementation("ru.tinkoff.kora:opentelemetry-tracing")
    }
    ```

## Add Modules

Update your Application interface to include telemetry modules:

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/ru/tinkoff/kora/example/Application.java`:

    ```java
    package ru.tinkoff.kora.example;

    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule;
    import ru.tinkoff.kora.micrometer.module.MetricsModule;
    import ru.tinkoff.kora.opentelemetry.tracing.TracingModule;

    @KoraApp
    public interface Application extends
            UndertowHttpServerModule,
            MetricsModule,
            TracingModule {

    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/ru/tinkoff/kora/example/Application.kt`:

    ```kotlin
    package ru.tinkoff.kora.example

    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule
    import ru.tinkoff.kora.micrometer.module.MetricsModule
    import ru.tinkoff.kora.opentelemetry.tracing.TracingModule

    @KoraApp
    interface Application :
        UndertowHttpServerModule,
        MetricsModule,
        TracingModule {

    }
    ```

## Understanding Private HTTP Server Ports

**Health checks, metrics, and monitoring endpoints are exposed on a separate private HTTP server port** to ensure security separation between your public API and internal monitoring infrastructure.

### Configuration

Kora provides a private HTTP server port as part of the `UndertowHttpServerModule`. The metrics endpoint is always exposed on this port, but metrics collection for specific modules only starts when you include the `MetricsModule`. Configure the private port using HOCON configuration:

===! ":material-code-json: `HOCON`"

    Create `src/main/resources/application.conf`:

    ```hocon
    httpServer {
        publicApiHttpPort = 8080           # Public API port
        privateApiHttpPort = 8085          # Private management port
        privateApiHttpMetricsPath = "/metrics"  # Metrics endpoint path
    }
    ```

You can also configure it programmatically by overriding the `httpServerManagementPort()` method in your Application interface, though HOCON configuration is preferred for production deployments.

### What is a Private HTTP Server Port?

Kora supports running **two separate HTTP servers** simultaneously - one for your public API endpoints and another for private monitoring and management endpoints. This architectural pattern, commonly known as the "management port" or "actuator port," provides better security and operational control.

### Why Use a Private Port?

**Security Separation**: Sensitive monitoring endpoints (health checks, metrics, configuration) are isolated from your public API, reducing the attack surface and preventing information leakage.

**Operational Safety**: Management endpoints can be exposed to different networks - internal monitoring systems can access private endpoints while public clients only see your API.

**Container Orchestration**: In Kubernetes and Docker environments, the private port enables proper readiness/liveness probes without exposing sensitive information to external clients.

**Access Control**: Different authentication and authorization rules can be applied to public vs private endpoints.

### What Runs on the Private Port?

- **Health Checks**: `/system/liveness` and `/system/readiness` endpoints for container orchestration
- **Metrics**: `/metrics` endpoint for Prometheus scraping and monitoring systems

### Network Configuration Best Practices

**Development Environment**:
- Both ports accessible locally for testing
- Use different ports (8080 for API, 8085 for management)

**Production Environment**:
- Public port (8080) exposed to external clients
- Private port (8085) only accessible to:
  - Load balancers and ingress controllers
  - Monitoring systems (Prometheus, Grafana)
  - Container orchestration platforms (Kubernetes)
  - Internal management tools

### Create Metrics Service

!!! note "Kora's Built-in Metrics Coverage"

    Kora automatically provides comprehensive metrics for all its modules out-of-the-box. This includes HTTP server metrics (request counts, response times, error rates), database connection pool metrics, cache hit/miss ratios, and more. You should only create custom metrics for your specific business logic that isn't covered by Kora's built-in instrumentation.

Create a service to demonstrate custom business metrics:

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/example/service/MetricsService.java`:

    ```java
    package ru.tinkoff.kora.example.service;

    import io.micrometer.core.instrument.Counter;
    import io.micrometer.core.instrument.MeterRegistry;
    import io.micrometer.core.instrument.Timer;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.example.dto.UserRequest;

    import java.util.concurrent.TimeUnit;

    @Component
    public final class MetricsService {

        private final Counter userCreationCounter;
        private final Timer userCreationTimer;

        public MetricsService(MeterRegistry meterRegistry) {
            this.userCreationCounter = Counter.builder("user.creation.total")
                    .description("Total number of users created")
                    .register(meterRegistry);

            this.userCreationTimer = Timer.builder("user.creation.duration")
                    .description("Time taken to create users")
                    .register(meterRegistry);
        }

        public void recordUserCreation(UserRequest request) {
            userCreationCounter.increment();

            // Simulate some processing time
            long startTime = System.nanoTime();
            try {
                // Simulate business logic processing
                Thread.sleep(10 + (long) (Math.random() * 50));
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
            long duration = System.nanoTime() - startTime;

            userCreationTimer.record(duration, TimeUnit.NANOSECONDS);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/example/service/MetricsService.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.service

    import io.micrometer.core.instrument.Counter
    import io.micrometer.core.instrument.MeterRegistry
    import io.micrometer.core.instrument.Timer
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.example.dto.UserRequest
    import java.util.concurrent.TimeUnit

    @Component
    class MetricsService(
        meterRegistry: MeterRegistry
    ) {
        private val userCreationCounter: Counter = Counter.builder("user.creation.total")
            .description("Total number of users created")
            .register(meterRegistry)

        private val userCreationTimer: Timer = Timer.builder("user.creation.duration")
            .description("Time taken to create users")
            .register(meterRegistry)

        fun recordUserCreation(request: UserRequest) {
            userCreationCounter.increment()

            // Simulate some processing time
            val startTime = System.nanoTime()
            try {
                // Simulate business logic processing
                Thread.sleep(10 + (Math.random() * 50).toLong())
            } catch (e: InterruptedException) {
                Thread.currentThread().interrupt()
            }
            val duration = System.nanoTime() - startTime

            userCreationTimer.record(duration, TimeUnit.NANOSECONDS)
        }
    }
    ```

### Create Health Check Probes

Health checks are critical for container orchestration platforms like Kubernetes and Docker to determine if your application is healthy and ready to serve traffic. Kora provides a comprehensive health check system with two types of probes: **liveness probes** and **readiness probes**.

#### Liveness vs Readiness Probes

**Liveness Probes** (`/system/liveness`):
- Check if the application is running properly
- Used by container orchestrators to determine if the application needs to be restarted
- Should return healthy when the application is functioning normally
- Return a failure only when the application is in an unrecoverable state

**Readiness Probes** (`/system/readiness`):
- Check if the application is ready to serve traffic
- Used by load balancers and service meshes to route traffic
- Should return healthy when the application can handle requests
- Can return failure during startup, configuration loading, or dependency checks

#### Why Health Checks Matter

**Container Orchestration Integration**:
- Kubernetes uses health checks for pod lifecycle management
- Load balancers route traffic only to healthy instances
- Service meshes make routing decisions based on health status

**Operational Benefits**:
- Automatic recovery from application failures
- Zero-downtime deployments through rolling updates
- Better resource utilization by removing unhealthy instances
- Proactive monitoring and alerting

#### Implementing Custom Health Checks

Kora allows you to implement custom health checks by creating classes that implement `LivenessProbe` or `ReadinessProbe` interfaces. These probes are automatically discovered and executed when the health endpoints are called.

**When to Implement Custom Probes**:
- Database connectivity checks
- External service dependencies
- Configuration validation
- Business-specific health criteria
- Resource availability (disk space, memory, etc.)

**Probe Implementation Guidelines**:
- Keep probes lightweight and fast (sub-second execution)
- Avoid complex business logic that could fail
- Return `null` or empty result for healthy state
- Return `ReadinessProbeFailure` or `LivenessProbeFailure` with descriptive message for unhealthy state
- Make probes idempotent and side-effect free

Create custom liveness and readiness probes:

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/example/health/CustomReadinessProbe.java`:

    ```java
    package ru.tinkoff.kora.example.health;

    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.readiness.ReadinessProbe;
    import ru.tinkoff.kora.common.readiness.ReadinessProbeFailure;

    @Component
    public final class CustomReadinessProbe implements ReadinessProbe {

        @Override
        public ReadinessProbeFailure probe() {
            return new ReadinessProbeFailure("Service is warming up");
        }
    }
    ```

    Create `src/main/java/ru/tinkoff/kora/example/health/ApplicationHealthProbe.java`:

    ```java
    package ru.tinkoff.kora.example.health;

    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.liveness.LivenessProbe;
    import ru.tinkoff.kora.common.liveness.LivenessProbeFailure;

    @Component
    public final class ApplicationHealthProbe implements LivenessProbe {

        @Override
        public LivenessProbeFailure probe() throws Exception {
            // Check if application is running properly
            // In a real application, you might check memory, threads, etc.
            return null; // null means healthy
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/example/health/CustomReadinessProbe.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.health

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.readiness.ReadinessProbe
    import ru.tinkoff.kora.common.readiness.ReadinessProbeFailure

    @Component
    class CustomReadinessProbe : ReadinessProbe {

        override fun probe(): ReadinessProbeFailure {
            return ReadinessProbeFailure("Service is warming up")
        }
    }
    ```

    Create `src/main/kotlin/ru/tinkoff/kora/example/health/ApplicationHealthProbe.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.health

    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.liveness.LivenessProbe
    import ru.tinkoff.kora.common.liveness.LivenessProbeFailure

    @Component
    class ApplicationHealthProbe : LivenessProbe {

        override fun probe(): LivenessProbeFailure? {
            // Check if application is running properly
            // In a real application, you might check memory, threads, etc.
            return null // null means healthy
        }
    }
    ```

### Update User Service with Logging and Metrics

Update the UserService to include logging and metrics:

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/java/ru/tinkoff/kora/example/service/UserService.java`:

    ```java
    package ru.tinkoff.kora.example.service;

    import org.slf4j.Logger;
    import org.slf4j.LoggerFactory;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.example.dto.UserRequest;
    import ru.tinkoff.kora.example.dto.UserResponse;

    import java.time.LocalDateTime;
    import java.util.*;
    import java.util.concurrent.ConcurrentHashMap;
    import java.util.concurrent.atomic.AtomicLong;

    @Component
    public final class UserService {

        private static final Logger logger = LoggerFactory.getLogger(UserService.class);

        private final Map<String, UserResponse> users = new ConcurrentHashMap<>();
        private final AtomicLong idGenerator = new AtomicLong(1);
        private final MetricsService metricsService;

        public UserService(MetricsService metricsService) {
            this.metricsService = metricsService;
        }

        public UserResponse createUser(UserRequest request) {
            logger.info("Creating user with name: {} and email: {}", request.name(), request.email());

            String id = String.valueOf(idGenerator.getAndIncrement());
            UserResponse user = new UserResponse(
                id,
                request.name(),
                request.email(),
                LocalDateTime.now()
            );

            users.put(id, user);
            metricsService.recordUserCreation(request);

            logger.info("Successfully created user with ID: {}", id);
            return user;
        }

        public Optional<UserResponse> getUser(String id) {
            logger.debug("Retrieving user with ID: {}", id);
            Optional<UserResponse> user = Optional.ofNullable(users.get(id));

            if (user.isPresent()) {
                logger.debug("Found user: {}", user.get().name());
            } else {
                logger.warn("User with ID {} not found", id);
            }

            return user;
        }

        public List<UserResponse> getAllUsers() {
            logger.debug("Retrieving all users, count: {}", users.size());
            return new ArrayList<>(users.values());
        }

        public boolean deleteUser(String id) {
            logger.info("Deleting user with ID: {}", id);
            boolean deleted = users.remove(id) != null;

            if (deleted) {
                logger.info("Successfully deleted user with ID: {}", id);
            } else {
                logger.warn("User with ID {} not found for deletion", id);
            }

            return deleted;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update `src/main/kotlin/ru/tinkoff/kora/example/service/UserService.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.service

    import org.slf4j.LoggerFactory
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.example.dto.UserRequest
    import ru.tinkoff.kora.example.dto.UserResponse
    import java.time.LocalDateTime
    import java.util.concurrent.ConcurrentHashMap
    import java.util.concurrent.atomic.AtomicLong

    @Component
    class UserService(
        private val metricsService: MetricsService
    ) {
        private val logger = LoggerFactory.getLogger(UserService::class.java)
        private val users = ConcurrentHashMap<String, UserResponse>()
        private val idGenerator = AtomicLong(1)

        fun createUser(request: UserRequest): UserResponse {
            logger.info("Creating user with name: {} and email: {}", request.name, request.email)

            val id = idGenerator.getAndIncrement().toString()
            val user = UserResponse(
                id = id,
                name = request.name,
                email = request.email,
                createdAt = LocalDateTime.now()
            )

            users[id] = user
            metricsService.recordUserCreation(request)

            logger.info("Successfully created user with ID: {}", id)
            return user
        }

        fun getUser(id: String): UserResponse? {
            logger.debug("Retrieving user with ID: {}", id)
            val user = users[id]

            if (user != null) {
                logger.debug("Found user: {}", user.name)
            } else {
                logger.warn("User with ID {} not found", id)
            }

            return user
        }

        fun getAllUsers(): List<UserResponse> {
            logger.debug("Retrieving all users, count: {}", users.size)
            return users.values.toList()
        }

        fun deleteUser(id: String): Boolean {
            logger.info("Deleting user with ID: {}", id)
            val deleted = users.remove(id) != null

            if (deleted) {
                logger.info("Successfully deleted user with ID: {}", id)
            } else {
                logger.warn("User with ID {} not found for deletion", id)
            }

            return deleted
        }
    }
    ```

### Set Up Jaeger for Tracing Verification (Optional)

To verify distributed tracing in action, you can run Jaeger locally using Docker Compose:

Create `docker-compose.yml` in your project root:

```yaml
version: '3.8'
services:
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"  # Jaeger UI
      - "14268:14268"  # Accept jaeger.thrift over HTTP
    environment:
      - COLLECTOR_OTLP_ENABLED=true
```

Start Jaeger:

```bash
docker-compose up -d
```

The Jaeger UI will be available at http://localhost:16686

### Configure External Monitoring (Optional)

For production monitoring, you can configure external systems to collect traces and metrics. Kora supports integration with popular observability backends through OpenTelemetry exporters.

#### Tracing Configuration

To export traces to an external tracing system like Jaeger, Zipkin, or an OpenTelemetry collector, configure the tracing exporter:

Create `src/main/resources/application.conf`:

```hocon
tracing {
  exporter {
    endpoint = "http://localhost:14268/api/traces"  # Jaeger HTTP endpoint
    exportTimeout = "30s"                           # Maximum time to wait for export
    scheduleDelay = "5s"                            # Time between export batches
    maxExportBatchSize = 512                        # Maximum spans per batch
    maxQueueSize = 2048                             # Maximum queued spans
  }
  attributes {
    "service.name" = "kora-observability-example"   # Service identification
    "service.namespace" = "kora"
  }
}
```

!!! tip "Tracing Exporters"

    For different tracing backends, you may need additional dependencies:

    - **Jaeger**: Add `ru.tinkoff.kora:opentelemetry-tracing-exporter-http` for HTTP transport
    - **OpenTelemetry Collector**: Use the HTTP or gRPC exporter based on your collector configuration
    - **Zipkin**: Compatible with OpenTelemetry exporters

#### Metrics Export

Metrics are automatically exposed in Prometheus format at the `/metrics` endpoint on the private HTTP server. External monitoring systems like Prometheus can scrape these metrics directly without additional configuration.

!!! note "Automatic Metrics Collection"

    When you include the `MetricsModule`, Kora automatically collects and exposes metrics for all Kora modules out of the box, like:
    - HTTP server requests (response times, status codes, request counts)
    - Database connection pools (active connections, idle connections)
    - Cache operations (hits, misses, evictions)
    - JVM metrics (memory, garbage collection, threads)
    - etc.

### Test Observability Features

Build and run your application:

```bash
./gradlew build
./gradlew run
```

Test the API and observe the logs:

```bash
# Create a user and see structured logging
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com"}'

# Get all users
curl http://localhost:8080/users

# Check health endpoints
curl http://localhost:8080/system/readiness
curl http://localhost:8080/system/liveness

# Check metrics endpoint
curl http://localhost:8080/metrics
```

Test tracing by making requests and viewing them in the Jaeger UI.

You should see:
- **Structured logs** in the console with proper levels and context
- **Health check responses** indicating system status
- **Metrics data** showing HTTP requests, custom metrics, and system metrics

## Key Concepts Learned

### Metrics Collection
- **Micrometer integration**: Standard metrics collection with `MetricsModule`
- **Custom metrics**: Counters, timers, and gauges for business logic
- **Automatic HTTP metrics**: Request counts, response times, error rates
- **Metrics endpoints**: `/metrics` for Prometheus scraping

### Distributed Tracing
- **OpenTelemetry integration**: `TracingModule` for request tracing
- **Automatic instrumentation**: HTTP requests automatically traced
- **Trace context propagation**: Across service boundaries
- **External exporters**: Jaeger, Zipkin, and other tracing backends

### Structured Logging
- **SLF4J integration**: `LogbackModule` for consistent logging
- **Log levels**: DEBUG, INFO, WARN, ERROR with appropriate usage
- **Contextual logging**: Include relevant data in log messages
- **Performance**: Efficient logging without impacting application performance

### Health Checks
- **Liveness probes**: Check if application is running (`/system/liveness`)
- **Readiness probes**: Check if application is ready to serve traffic (`/system/readiness`)
- **Custom probes**: Implement business-specific health checks
- **Container orchestration**: Kubernetes readiness/liveness probe integration

## Next Steps

Continue your learning journey:

- **Next Guide**: [Caching Strategies](../cache.md) - Learn about performance optimization with in-memory and distributed caching
- **Related Documentation**:
  - [Metrics Module](../../documentation/metrics.md)
  - [Tracing Module](../../documentation/tracing.md)
  - [Logging Module](../../documentation/logging-slf4j.md)
  - [Health Checks](../../documentation/probes.md)
- **Advanced Topics**:
  - [Custom Metrics](../../documentation/metrics.md#custom-metrics)
  - [Distributed Tracing Setup](../../documentation/tracing.md#exporters)

## Troubleshooting

### Metrics Not Appearing
- Ensure `MetricsModule` is included in Application interface
- Check that Micrometer registry is properly injected
- Verify metrics endpoint is accessible at `/metrics`

### Tracing Not Working
- Confirm `TracingModule` is included in Application interface
- Check OpenTelemetry configuration in `application.conf`
- Verify tracing exporter (Jaeger, Zipkin) is running and accessible

### Logs Not Structured
- Ensure `LogbackModule` is included in Application interface
- Check logging configuration and logback.xml if custom logging is needed
- Verify SLF4J logger usage in code

### Health Checks Failing
- Implement proper probe logic that returns `null` for healthy state
- Check that probes are registered as `@Component` classes
- Verify health endpoints are accessible at `/system/liveness` and `/system/readiness`