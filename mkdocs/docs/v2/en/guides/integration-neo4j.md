---
seo_title: "Creating a Neo4j Integration Module | Kora"
seo_description: "Build a reusable Neo4j client with Kora configuration, lifecycle, metrics and tracing, then call it from Java or Kotlin HTTP routes."
keywords: ["Kora Framework", "Neo4j", "Kora integration", "Lifecycle", "ConfigSource", "Micrometer", "OpenTelemetry"]
search:
  exclude: true
title: "Creating a Neo4j Integration Module"
summary: "Build a reusable Neo4j client with Kora configuration, lifecycle, metrics and tracing, then call it from Java or Kotlin HTTP routes."
description: "Use this guide to create a Kora 2.0 Neo4j library: Java/Kotlin library with kora-bom, AP/KSP, HOCON/YAML, @ConfigSource, Duration timeouts, Lifecycle init/release, Driver and Session ownership, managed executeWrite retries, parameterized Cypher MERGE, Neo4jModule factories, MetricsModule, OpentelemetryTracingModule, ScopedValue tracing context, PUT /people/{name}, Docker healthcheck and uniqueness constraint, generated config sources and failure verification."
agent:
  use_when: "Use this guide to create a Kora 2.0 Neo4j library: Java/Kotlin library with kora-bom, AP/KSP, HOCON/YAML, @ConfigSource, Duration timeouts, Lifecycle init/release, Driver and Session ownership, managed executeWrite retries, parameterized Cypher MERGE, Neo4jModule factories, MetricsModule, OpentelemetryTracingModule, ScopedValue tracing context, PUT /people/{name}, Docker healthcheck and uniqueness constraint, generated config sources and failure verification."
tags: "integration, neo4j, lifecycle, telemetry"
---

# Creating a Neo4j Integration Module { #neo4j-integration }

This guide turns a third-party Java driver into a reusable Kora module. You will connect configuration, resource ownership and telemetry to the application graph, then verify a database write through HTTP. Choose Java or Kotlin for the integration library and the application; both branches implement the same configuration, lifecycle and telemetry contracts.

## What You'll Build { #youll-build }

- A `neo4j-integration` library with typed configuration and a lifecycle-managed client
- A factory module that connects the client to the compile-time graph
- Duration metrics, an operation span and failure logging
- `PUT /people/{name}` that creates or finds one person and returns their name
- A local database with a uniqueness constraint and repeatable verification

## What You'll Need { #youll-need }

- JDK 25 or later and Gradle 9+ Wrapper
- A working application from [Getting Started](getting-started.md)
- Docker with Compose v2 supporting `up --wait`
- An IDE or editor and basic Cypher familiarity

Use the baseline Kora `2.0.0.RC2` BOM. Kotlin applications keep the baseline Kotlin `2.4.20` and KSP `2.3.12`; the Kotlin library uses KSP to generate its typed configuration.

## Prerequisites { #prerequisites }

!!! note "Required: a working HTTP application"

    Complete [Getting Started](getting-started.md) first. Keep its application plugin, Kora processors, HTTP server, the selected HOCON/YAML config backend and Logback dependencies. This guide adds a library subproject to that application.

Read [Dependency Injection](dependency-injection.md) for factory modules and [Observability](observability.md) for metrics and tracing. All commands below run from the application project root.

## Overview { #overview }

An integration is the boundary between an external library and your application. Neo4j owns the network protocol and transactions; Kora owns how the client is configured, constructed, started and stopped. Business code depends on `Neo4jClient` rather than creating drivers or reading environment variables.

### Configuration and the graph { #configuration-graph }

`@ConfigSource("neo4j")` generates a config implementation, mapper and factory module. `Neo4jModule` contributes the remaining factories. Their parameters describe graph edges: config and telemetry are dependencies of the client, and the client is a dependency of the controller. Ordinary factories are enough; a custom AP/KSP generator is a later, optional convenience.

### Resource ownership { #resource-ownership }

One thread-safe `Driver` owns the connection pool. A session belongs to one operation, and its transaction result must be consumed before the session closes. Kora calls `init()` before serving requests and `release()` during graph shutdown. A plain constructor call outside the graph does not arrange that lifecycle.

### Operation telemetry { #operation-telemetry }

Instrumentation wraps the whole `savePerson` operation, including connection acquisition and managed transaction retries. It records one outcome and one child span per invocation. It does not measure each query or expose driver pool statistics. The HTTP handler runs synchronously on a virtual thread, so the blocking driver API fits this example.

The flow is: create the library, generate config, add telemetry and lifecycle, publish factories, connect the root, expose HTTP, then check data and observability.

## Dependencies and Project Layout { #project }

Add `include("neo4j-integration")` to the root `settings.gradle` or `settings.gradle.kts`. Configure `neo4j-integration/build.gradle` or `neo4j-integration/build.gradle.kts`:

===! ":fontawesome-brands-java: `Java`"

    ===! "Groovy — build.gradle"

        ```groovy
        plugins { id 'java-library' }
        repositories { mavenCentral() }
        java { toolchain { languageVersion = JavaLanguageVersion.of(25) } }
        dependencies {
            annotationProcessor platform("io.koraframework:kora-bom:2.0.0.RC2")
            annotationProcessor "io.koraframework:annotation-processors"
            api platform("io.koraframework:kora-bom:2.0.0.RC2")
            api "io.koraframework:common"
            api "io.koraframework:config-common"
            api "io.koraframework:application-graph"
            api "io.koraframework:micrometer-module"
            api "io.koraframework:opentelemetry-tracing"
            implementation "org.neo4j.driver:neo4j-java-driver:6.1.0"
        }
        ```

    === "Kotlin DSL — build.gradle.kts"

        ```kotlin
        plugins { id("java-library") }
        repositories { mavenCentral() }
        java { toolchain { languageVersion.set(JavaLanguageVersion.of(25)) } }
        dependencies {
            annotationProcessor(platform("io.koraframework:kora-bom:2.0.0.RC2"))
            annotationProcessor("io.koraframework:annotation-processors")
            api(platform("io.koraframework:kora-bom:2.0.0.RC2"))
            api("io.koraframework:common")
            api("io.koraframework:config-common")
            api("io.koraframework:application-graph")
            api("io.koraframework:micrometer-module")
            api("io.koraframework:opentelemetry-tracing")
            implementation("org.neo4j.driver:neo4j-java-driver:6.1.0")
        }
        ```

=== ":simple-kotlin: `Kotlin`"

    ===! "Groovy — build.gradle"

        ```groovy
        plugins {
            id 'java-library'
            id 'org.jetbrains.kotlin.jvm' version '2.4.20'
            id 'com.google.devtools.ksp' version '2.3.12'
        }
        repositories { mavenCentral() }
        kotlin { jvmToolchain(25) }
        dependencies {
            ksp "io.koraframework:symbol-processors:2.0.0.RC2"
            api platform("io.koraframework:kora-bom:2.0.0.RC2")
            api "io.koraframework:common"
            api "io.koraframework:config-common"
            api "io.koraframework:application-graph"
            api "io.koraframework:micrometer-module"
            api "io.koraframework:opentelemetry-tracing"
            implementation "org.neo4j.driver:neo4j-java-driver:6.1.0"
        }
        ```

    === "Kotlin DSL — build.gradle.kts"

        ```kotlin
        plugins {
            id("java-library")
            id("org.jetbrains.kotlin.jvm") version "2.4.20"
            id("com.google.devtools.ksp") version "2.3.12"
        }
        repositories { mavenCentral() }
        kotlin { jvmToolchain(25) }
        dependencies {
            ksp("io.koraframework:symbol-processors:2.0.0.RC2")
            api(platform("io.koraframework:kora-bom:2.0.0.RC2"))
            api("io.koraframework:common")
            api("io.koraframework:config-common")
            api("io.koraframework:application-graph")
            api("io.koraframework:micrometer-module")
            api("io.koraframework:opentelemetry-tracing")
            implementation("org.neo4j.driver:neo4j-java-driver:6.1.0")
        }
        ```

Select the library source language, then one Gradle DSL. Java uses AP; Kotlin uses KSP. Keep the Kotlin/KSP versions aligned with the root and omit repeated plugin versions if already declared there. The source language and Gradle DSL are independent. `api` exposes Kora types in public signatures; `implementation` keeps the Neo4j driver behind the wrapper. See the [driver manual](https://neo4j.com/docs/java-manual/current/install/) for server compatibility.

Add the runtime project to the existing application dependencies:

===! ":fontawesome-brands-java: `Java`"

    ===! "Groovy — build.gradle"

        ```groovy
        dependencies {
            // Keep existing Kora dependencies.
            implementation project(":neo4j-integration")
        }
        ```

    === "Kotlin DSL — build.gradle.kts"

        ```kotlin
        dependencies {
            // Keep existing Kora dependencies.
            implementation(project(":neo4j-integration"))
        }
        ```

=== ":simple-kotlin: `Kotlin`"

    ===! "Groovy — build.gradle"

        ```groovy
        dependencies {
            // Keep existing Kora dependencies.
            implementation project(":neo4j-integration")
        }
        ```

    === "Kotlin DSL — build.gradle.kts"

        ```kotlin
        dependencies {
            // Keep existing Kora dependencies.
            implementation(project(":neo4j-integration"))
        }
        ```

Put Java library files in `neo4j-integration/src/main/java/example/neo4j/` or Kotlin files in `neo4j-integration/src/main/kotlin/example/neo4j/`, according to the selected branch. Create only one version of each type. The application files use `example.app`.

```text
settings.gradle[.kts]
build.gradle[.kts]
compose.yaml
neo4j-integration/
  build.gradle[.kts]
  src/main/java/example/neo4j/
    Neo4jConfig.java
    Neo4jTelemetry.java
    Neo4jClient.java
    Neo4jModule.java
  src/main/kotlin/example/neo4j/                # Kotlin library branch
    Neo4jConfig.kt
    Neo4jTelemetry.kt
    Neo4jClient.kt
    Neo4jModule.kt
src/main/resources/application.conf           # HOCON branch
src/main/resources/application.yaml           # YAML branch
src/main/java/example/app/       # Java application
src/main/kotlin/example/app/     # Kotlin application
```

### Configuration format { #configuration-format }

Keep exactly one config backend in the application. HOCON uses `config-hocon`, `HoconConfigModule` and `application.conf`; YAML uses `config-yaml`, `YamlConfigModule` and `application.yaml`. Replace the baseline config dependency with the selected one. The complete roots below show both module choices.

===! ":material-code-json: `HOCON`"

    ===! "Groovy — build.gradle"

        ```groovy
        dependencies {
            implementation "io.koraframework:config-hocon"
        }
        ```

    === "Kotlin DSL — build.gradle.kts"

        ```kotlin
        dependencies {
            implementation("io.koraframework:config-hocon")
        }
        ```

=== ":simple-yaml: `YAML`"

    ===! "Groovy — build.gradle"

        ```groovy
        dependencies {
            implementation "io.koraframework:config-yaml"
        }
        ```

    === "Kotlin DSL — build.gradle.kts"

        ```kotlin
        dependencies {
            implementation("io.koraframework:config-yaml")
        }
        ```


## Configuration { #config }

===! ":fontawesome-brands-java: `Java`"

    Create `neo4j-integration/src/main/java/example/neo4j/Neo4jConfig.java`:

    ```java
    package example.neo4j;

    import io.koraframework.config.common.annotation.ConfigSource;
    import java.time.Duration;

    @ConfigSource("neo4j")
    public interface Neo4jConfig {
        String uri();
        String username();
        String password();
        default String database() { return "neo4j"; }
        default Duration connectionTimeout() { return Duration.ofSeconds(5); }
        default Duration acquisitionTimeout() { return Duration.ofSeconds(10); }
        default Duration retryTimeout() { return Duration.ofSeconds(15); }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `neo4j-integration/src/main/kotlin/example/neo4j/Neo4jConfig.kt`:

    ```kotlin
    package example.neo4j

    import io.koraframework.config.common.annotation.ConfigSource
    import java.time.Duration

    @ConfigSource("neo4j")
    interface Neo4jConfig {
        fun uri(): String
        fun username(): String
        fun password(): String
        fun database(): String = "neo4j"
        fun connectionTimeout(): Duration = Duration.ofSeconds(5)
        fun acquisitionTimeout(): Duration = Duration.ofSeconds(10)
        fun retryTimeout(): Duration = Duration.ofSeconds(15)
    }
    ```


URI, username and password are required. Defaults belong to the typed contract; the application can override them without rebuilding the library.

Choose one configuration format and add the matching resource:

===! ":material-code-json: `HOCON`"

    `src/main/resources/application.conf`:

    ```hocon
    neo4j {
      uri = "bolt://localhost:7687"
      username = "neo4j"
      password = ${NEO4J_PASSWORD}
      database = "neo4j"
      connectionTimeout = "5s"
      acquisitionTimeout = "10s"
      retryTimeout = "15s"
    }
    httpServer.port = 8080
    httpServer.system.port = 8085
    metrics.enabled = true
    httpServer.telemetry.metrics.enabled = true
    tracing.enabled = true
    httpServer.telemetry.tracing.enabled = true
    ```

=== ":simple-yaml: `YAML`"

    `src/main/resources/application.yaml`:

    ```yaml
    neo4j:
      uri: "bolt://localhost:7687"
      username: "neo4j"
      password: "${NEO4J_PASSWORD}"
      database: "neo4j"
      connectionTimeout: "5s"
      acquisitionTimeout: "10s"
      retryTimeout: "15s"
    httpServer:
      port: 8080
      system:
        port: 8085
      telemetry:
        metrics:
          enabled: true
        tracing:
          enabled: true
    metrics:
      enabled: true
    tracing:
      enabled: true
    ```


The password is resolved from the environment at startup. These are driver connection/acquisition and retry limits, not a total HTTP deadline or a Cypher query timeout. An exporter is a separate [tracing setup](observability-tracing.md); enabling tracing alone does not send spans to a collector.

## Telemetry { #telemetry }

===! ":fontawesome-brands-java: `Java`"

    Create `neo4j-integration/src/main/java/example/neo4j/Neo4jTelemetry.java`:

    ```java
    package example.neo4j;

    import io.koraframework.common.telemetry.OpentelemetryContext;
    import io.micrometer.core.instrument.MeterRegistry;
    import io.micrometer.core.instrument.Timer;
    import io.opentelemetry.api.trace.StatusCode;
    import io.opentelemetry.api.trace.Tracer;
    import io.opentelemetry.context.Context;
    import org.slf4j.Logger;
    import org.slf4j.LoggerFactory;
    import java.util.concurrent.TimeUnit;
    import java.util.function.Supplier;

    public final class Neo4jTelemetry {
        private static final Logger log = LoggerFactory.getLogger(Neo4jTelemetry.class);
        private final Tracer tracer;
        private final Timer success;
        private final Timer failure;

        public Neo4jTelemetry(MeterRegistry registry, Tracer tracer) {
            this.tracer = tracer;
            this.success = Timer.builder("neo4j.operation.duration")
                .tag("operation", "savePerson").tag("result", "success").register(registry);
            this.failure = Timer.builder("neo4j.operation.duration")
                .tag("operation", "savePerson").tag("result", "failure").register(registry);
        }

        public <T> T observeSavePerson(Supplier<T> callback) {
            var started = System.nanoTime();
            var parent = Context.current();
            var span = tracer.spanBuilder("neo4j.savePerson").setParent(parent).startSpan();
            try {
                return ScopedValue.where(OpentelemetryContext.VALUE, parent.with(span)).call(() -> {
                    try {
                        var result = callback.get();
                        success.record(System.nanoTime() - started, TimeUnit.NANOSECONDS);
                        return result;
                    } catch (RuntimeException | Error e) {
                        span.setStatus(StatusCode.ERROR);
                        log.warn("Neo4j operation savePerson failed: {}", e.getClass().getSimpleName());
                        throw e;
                    }
                });
            } catch (RuntimeException | Error e) {
                failure.record(System.nanoTime() - started, TimeUnit.NANOSECONDS);
                throw e;
            } finally {
                span.end();
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `neo4j-integration/src/main/kotlin/example/neo4j/Neo4jTelemetry.kt`:

    ```kotlin
    package example.neo4j

    import io.koraframework.common.telemetry.OpentelemetryContext
    import io.micrometer.core.instrument.MeterRegistry
    import io.micrometer.core.instrument.Timer
    import io.opentelemetry.api.trace.StatusCode
    import io.opentelemetry.api.trace.Tracer
    import io.opentelemetry.context.Context
    import org.slf4j.LoggerFactory
    import java.util.concurrent.TimeUnit

    class Neo4jTelemetry(registry: MeterRegistry, private val tracer: Tracer) {
        private val log = LoggerFactory.getLogger(Neo4jTelemetry::class.java)
        private val success = Timer.builder("neo4j.operation.duration")
            .tag("operation", "savePerson").tag("result", "success").register(registry)
        private val failure = Timer.builder("neo4j.operation.duration")
            .tag("operation", "savePerson").tag("result", "failure").register(registry)

        fun <T> observeSavePerson(callback: () -> T): T {
            val started = System.nanoTime()
            val parent = Context.current()
            val span = tracer.spanBuilder("neo4j.savePerson").setParent(parent).startSpan()
            try {
                return ScopedValue.where(OpentelemetryContext.VALUE, parent.with(span)).call<T, Throwable> {
                    try {
                        val result = callback()
                        success.record(System.nanoTime() - started, TimeUnit.NANOSECONDS)
                        result
                    } catch (e: Throwable) {
                        span.setStatus(StatusCode.ERROR)
                        log.warn("Neo4j operation savePerson failed: {}", e.javaClass.simpleName)
                        throw e
                    }
                }
            } catch (e: Throwable) {
                failure.record(System.nanoTime() - started, TimeUnit.NANOSECONDS)
                throw e
            } finally {
                span.end()
            }
        }
    }
    ```


Timers are registered once with fixed `operation` and `result` tags, so person names do not create unbounded metric series. `Context.current()` captures the HTTP parent; the new span is bound through Kora’s `OpentelemetryContext.VALUE` for the callback. Leaving `ScopedValue.where(...).call(...)` restores the parent even on failure, and `finally` ends the span. Avoid `makeCurrent()` with Kora’s scoped context storage.

Only the error class is logged; credentials, names and parameter values are not included. If you add other operations, give each its own bounded telemetry contract instead of passing arbitrary user strings as operation names.

## Client and Lifecycle { #lifecycle }

===! ":fontawesome-brands-java: `Java`"

    Create `neo4j-integration/src/main/java/example/neo4j/Neo4jClient.java`:

    ```java
    package example.neo4j;

    import io.koraframework.application.graph.Lifecycle;
    import org.neo4j.driver.AuthTokens;
    import org.neo4j.driver.Driver;
    import org.neo4j.driver.Config;
    import java.util.concurrent.TimeUnit;
    import org.neo4j.driver.GraphDatabase;
    import org.neo4j.driver.SessionConfig;
    import org.neo4j.driver.Values;

    public final class Neo4jClient implements Lifecycle {
        private final Driver driver;
        private final SessionConfig sessionConfig;
        private final Neo4jTelemetry telemetry;

        public Neo4jClient(Neo4jConfig config, Neo4jTelemetry telemetry) {
            var driverConfig = Config.builder()
                .withConnectionTimeout(config.connectionTimeout().toMillis(), TimeUnit.MILLISECONDS)
                .withConnectionAcquisitionTimeout(config.acquisitionTimeout().toMillis(), TimeUnit.MILLISECONDS)
                .withMaxTransactionRetryTime(config.retryTimeout().toMillis(), TimeUnit.MILLISECONDS)
                .build();
            this.driver = GraphDatabase.driver(config.uri(),
                AuthTokens.basic(config.username(), config.password()), driverConfig);
            this.sessionConfig = SessionConfig.builder().withDatabase(config.database()).build();
            this.telemetry = telemetry;
        }

        @Override
        public void init() {
            try {
                driver.verifyConnectivity();
            } catch (RuntimeException e) {
                try {
                    driver.close();
                } catch (RuntimeException closeError) {
                    e.addSuppressed(closeError);
                }
                throw e;
            }
        }

        @Override
        public void release() { driver.close(); }

        public String savePerson(String name) {
            return telemetry.observeSavePerson( () -> {
                try (var session = driver.session(sessionConfig)) {
                    return session.executeWrite(tx -> tx.run(
                        "MERGE (p:Person {name: $name}) RETURN p.name AS name",
                        Values.parameters("name", name)
                    ).single().get("name").asString());
                }
            });
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `neo4j-integration/src/main/kotlin/example/neo4j/Neo4jClient.kt`:

    ```kotlin
    package example.neo4j

    import io.koraframework.application.graph.Lifecycle
    import org.neo4j.driver.AuthTokens
    import org.neo4j.driver.Config
    import org.neo4j.driver.GraphDatabase
    import org.neo4j.driver.SessionConfig
    import org.neo4j.driver.Values
    import java.util.concurrent.TimeUnit

    class Neo4jClient(config: Neo4jConfig, private val telemetry: Neo4jTelemetry) : Lifecycle {
        private val driver = GraphDatabase.driver(config.uri(),
            AuthTokens.basic(config.username(), config.password()), Config.builder()
                .withConnectionTimeout(config.connectionTimeout().toMillis(), TimeUnit.MILLISECONDS)
                .withConnectionAcquisitionTimeout(config.acquisitionTimeout().toMillis(), TimeUnit.MILLISECONDS)
                .withMaxTransactionRetryTime(config.retryTimeout().toMillis(), TimeUnit.MILLISECONDS)
                .build())
        private val sessionConfig = SessionConfig.builder().withDatabase(config.database()).build()

        override fun init() {
            try {
                driver.verifyConnectivity()
            } catch (e: RuntimeException) {
                try {
                    driver.close()
                } catch (closeError: RuntimeException) {
                    e.addSuppressed(closeError)
                }
                throw e
            }
        }

        override fun release() { driver.close() }

        fun savePerson(name: String): String = telemetry.observeSavePerson {
            driver.session(sessionConfig).use { session ->
                session.executeWrite { tx ->
                    tx.run("MERGE (p:Person {name: \$name}) RETURN p.name AS name",
                        Values.parameters("name", name)).single().get("name").asString()
                }
            }
        }
    }
    ```


The constructor creates the shared driver; `init()` verifies connectivity and closes it if verification fails. A cleanup failure is attached as a suppressed exception so the original connectivity error remains visible. `release()` closes the pool when the graph stops.

The session is local to one invocation. `single().get("name").asString()` materializes the value inside the transaction; returning a lazy `Result` would leave the caller dependent on a closed session. `$name` is a Cypher parameter rather than string interpolation.

Managed `executeWrite` may repeat its callback. Keep email, HTTP calls and other external side effects outside that callback. The [transaction manual](https://neo4j.com/docs/java-manual/current/transactions/) explains managed transaction behavior.

## Modules { #module }

===! ":fontawesome-brands-java: `Java`"

    Create `neo4j-integration/src/main/java/example/neo4j/Neo4jModule.java`:

    ```java
    package example.neo4j;

    import io.koraframework.common.annotation.Module;
    import io.micrometer.core.instrument.MeterRegistry;
    import io.opentelemetry.api.trace.Tracer;

    @Module
    public interface Neo4jModule extends Neo4jConfigModule {
        default Neo4jTelemetry neo4jTelemetry(MeterRegistry registry, Tracer tracer) {
            return new Neo4jTelemetry(registry, tracer);
        }

        default Neo4jClient neo4jClient(Neo4jConfig config, Neo4jTelemetry telemetry) {
            return new Neo4jClient(config, telemetry);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `neo4j-integration/src/main/kotlin/example/neo4j/Neo4jModule.kt`:

    ```kotlin
    package example.neo4j

    import io.koraframework.common.annotation.Module
    import io.micrometer.core.instrument.MeterRegistry
    import io.opentelemetry.api.trace.Tracer

    @Module
    interface Neo4jModule : Neo4jConfigModule {
        fun neo4jTelemetry(registry: MeterRegistry, tracer: Tracer): Neo4jTelemetry =
            Neo4jTelemetry(registry, tracer)

        fun neo4jClient(config: Neo4jConfig, telemetry: Neo4jTelemetry): Neo4jClient =
            Neo4jClient(config, telemetry)
    }
    ```


===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/example/app/Application.java`:

    ===! ":material-code-json: `HOCON`"

        ```java
        package example.app;

        import example.neo4j.Neo4jModule;
        import io.koraframework.application.graph.KoraApplication;
        import io.koraframework.common.annotation.KoraApp;
        import io.koraframework.config.hocon.HoconConfigModule;
        import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule;
        import io.koraframework.logging.logback.LogbackModule;
        import io.koraframework.micrometer.module.MetricsModule;
        import io.koraframework.opentelemetry.tracing.OpentelemetryTracingModule;

        @KoraApp
        public interface Application extends HoconConfigModule, LogbackModule,
                UndertowPublicHttpServerModule, Neo4jModule, MetricsModule,
                OpentelemetryTracingModule {
            static void main(String[] args) {
                KoraApplication.run(ApplicationGraph::graph);
            }
        }
        ```

    === ":simple-yaml: `YAML`"

        ```java
        package example.app;

        import example.neo4j.Neo4jModule;
        import io.koraframework.application.graph.KoraApplication;
        import io.koraframework.common.annotation.KoraApp;
        import io.koraframework.config.yaml.YamlConfigModule;
        import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule;
        import io.koraframework.logging.logback.LogbackModule;
        import io.koraframework.micrometer.module.MetricsModule;
        import io.koraframework.opentelemetry.tracing.OpentelemetryTracingModule;

        @KoraApp
        public interface Application extends YamlConfigModule, LogbackModule,
                UndertowPublicHttpServerModule, Neo4jModule, MetricsModule,
                OpentelemetryTracingModule {
            static void main(String[] args) {
                KoraApplication.run(ApplicationGraph::graph);
            }
        }
        ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/example/app/Application.kt`:

    ===! ":material-code-json: `HOCON`"

        ```kotlin
        package example.app

        import example.neo4j.Neo4jModule
        import io.koraframework.application.graph.KoraApplication
        import io.koraframework.common.annotation.KoraApp
        import io.koraframework.config.hocon.HoconConfigModule
        import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule
        import io.koraframework.logging.logback.LogbackModule
        import io.koraframework.micrometer.module.MetricsModule
        import io.koraframework.opentelemetry.tracing.OpentelemetryTracingModule

        @KoraApp
        interface Application : HoconConfigModule, LogbackModule,
            UndertowPublicHttpServerModule, Neo4jModule, MetricsModule,
            OpentelemetryTracingModule

        fun main() {
            KoraApplication.run(ApplicationGraph::graph)
        }
        ```

    === ":simple-yaml: `YAML`"

        ```kotlin
        package example.app

        import example.neo4j.Neo4jModule
        import io.koraframework.application.graph.KoraApplication
        import io.koraframework.common.annotation.KoraApp
        import io.koraframework.config.yaml.YamlConfigModule
        import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule
        import io.koraframework.logging.logback.LogbackModule
        import io.koraframework.micrometer.module.MetricsModule
        import io.koraframework.opentelemetry.tracing.OpentelemetryTracingModule

        @KoraApp
        interface Application : YamlConfigModule, LogbackModule,
            UndertowPublicHttpServerModule, Neo4jModule, MetricsModule,
            OpentelemetryTracingModule

        fun main() {
            KoraApplication.run(ApplicationGraph::graph)
        }
        ```

`Neo4jModule` extends the generated `Neo4jConfigModule` so its config factory is explicitly inherited across the library boundary. The application root then extends `Neo4jModule`. An annotation on a module in a dependency JAR alone is not sufficient to connect that factory. `MetricsModule` supplies `MeterRegistry`; `OpentelemetryTracingModule` supplies `Tracer`. Kora recognizes the returned client’s `Lifecycle` contract.

Because this root uses a new package, update the existing `application` block:

===! ":fontawesome-brands-java: `Java`"

    ===! "Groovy — build.gradle"

        ```groovy
        application {
            mainClass = "example.app.Application"
        }
        ```

    === "Kotlin DSL — build.gradle.kts"

        ```kotlin
        application {
            mainClass.set("example.app.Application")
        }
        ```

=== ":simple-kotlin: `Kotlin`"

    ===! "Groovy — build.gradle"

        ```groovy
        application {
            mainClass = "example.app.ApplicationKt"
        }
        ```

    === "Kotlin DSL — build.gradle.kts"

        ```kotlin
        application {
            mainClass.set("example.app.ApplicationKt")
        }
        ```

Replace the old `@KoraApp` root rather than retaining two roots. The original `/hello` controller may remain.

## Controller { #controller }

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/example/app/PeopleController.java`:

    ```java
    package example.app;

    import example.neo4j.Neo4jClient;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.http.common.HttpMethod;
    import io.koraframework.http.common.annotation.HttpRoute;
    import io.koraframework.http.common.body.HttpBody;
    import io.koraframework.http.server.common.annotation.HttpController;
    import io.koraframework.http.common.annotation.Path;
    import io.koraframework.http.server.common.response.HttpServerResponse;

    @Component
    @HttpController
    public final class PeopleController {
        private final Neo4jClient client;

        public PeopleController(Neo4jClient client) {
            this.client = client;
        }

        @HttpRoute(method = HttpMethod.PUT, path = "/people/{name}")
        public HttpServerResponse savePerson(@Path String name) {
            return HttpServerResponse.of(200, HttpBody.plaintext(client.savePerson(name)));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/example/app/PeopleController.kt`:

    ```kotlin
    package example.app

    import example.neo4j.Neo4jClient
    import io.koraframework.common.annotation.Component
    import io.koraframework.http.common.HttpMethod
    import io.koraframework.http.common.annotation.HttpRoute
    import io.koraframework.http.common.body.HttpBody
    import io.koraframework.http.server.common.annotation.HttpController
    import io.koraframework.http.common.annotation.Path
    import io.koraframework.http.server.common.response.HttpServerResponse

    @Component
    @HttpController
    class PeopleController(private val client: Neo4jClient) {
        @HttpRoute(method = HttpMethod.PUT, path = "/people/{name}")
        fun savePerson(@Path name: String): HttpServerResponse =
            HttpServerResponse.of(200, HttpBody.plaintext(client.savePerson(name)))
    }
    ```

`PUT` matches the write semantics: the name identifies the resource, and repeating the request returns the same name. A uniqueness constraint below makes that identity explicit in the database. `GET` must not create data. The driver exception follows the ordinary HTTP error path; domain error mapping is beyond this small integration.

## Generated Configuration and Graph { #generated-code }

After compiling the library, inspect:

===! ":fontawesome-brands-java: `Java`"

    ```text
    neo4j-integration/build/generated/sources/annotationProcessor/java/main/example/neo4j/Neo4jConfigModule.java
    neo4j-integration/build/generated/sources/annotationProcessor/java/main/example/neo4j/$Neo4jConfig_ConfigValueMapper.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    neo4j-integration/build/generated/ksp/main/kotlin/example/neo4j/Neo4jConfigModule.kt
    neo4j-integration/build/generated/ksp/main/kotlin/example/neo4j/$Neo4jConfig_ConfigValueMapper.kt
    ```

The config module contains this factory (annotations omitted):

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface Neo4jConfigModule {
        default Neo4jConfig neo4jConfig(
                io.koraframework.config.common.Config config,
                io.koraframework.config.common.mapper.ConfigValueMapper<Neo4jConfig> mapper) {
            return mapper.mapOrThrow(config.get("neo4j"));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface Neo4jConfigModule {
        fun neo4jConfig(
            config: io.koraframework.config.common.Config,
            mapper: io.koraframework.config.common.mapper.ConfigValueMapper<Neo4jConfig>
        ): Neo4jConfig = mapper.mapOrThrow(config.get("neo4j"))
    }
    ```


The mapper reads fields and applies interface defaults. In the application’s `ApplicationGraph`, follow `PeopleController → Neo4jClient → Neo4jConfig + Neo4jTelemetry → MeterRegistry + Tracer`. Java graph output is under `build/generated/sources/annotationProcessor/java/main/example/app/`; Kotlin graph output is under `build/generated/ksp/main/kotlin/example/app/`. Generated sources explain wiring; edit input declarations, never generated files.

## Run Application { #run-app }

Create `compose.yaml` in the application root:

```yaml
services:
  neo4j:
    image: neo4j:5.26-community
    ports:
      - "127.0.0.1:7687:7687"
    environment:
      NEO4J_AUTH: neo4j/localpassword
    healthcheck:
      test: ["CMD", "cypher-shell", "-u", "neo4j", "-p", "localpassword", "RETURN 1"]
      interval: 5s
      timeout: 10s
      retries: 30
      start_period: 20s
```

These credentials are for the local example. Wait for a healthy database, then create the schema constraint:

```shell
docker compose up -d --wait
docker compose exec neo4j cypher-shell -u neo4j -p localpassword "CREATE CONSTRAINT person_name_unique IF NOT EXISTS FOR (p:Person) REQUIRE p.name IS UNIQUE"
```

Compile and start the application; in PowerShell use `gradlew.bat`:

===! "Bash"

    ```bash
    ./gradlew clean classes
    NEO4J_PASSWORD=localpassword ./gradlew run
    ```

=== "PowerShell"

    ```powershell
    ./gradlew.bat clean classes
    $env:NEO4J_PASSWORD = 'localpassword'
    ./gradlew.bat run
    ```

## Check Application { #check-app }

In another terminal, call the same resource twice (`curl.exe` in PowerShell):

```shell
curl -i -X PUT http://localhost:8080/people/Alice
curl -i -X PUT http://localhost:8080/people/Alice
```

Both responses have status `200` and body `Alice`. Confirm the database contains one matching node:

```shell
docker compose exec neo4j cypher-shell -u neo4j -p localpassword "MATCH (p:Person {name: 'Alice'}) RETURN count(p) AS people"
```

The `people` value is `1`. Check operation metrics:

```shell
curl http://localhost:8085/metrics
```

Look for `neo4j_operation_duration_seconds_count` with `operation="savePerson"` and `result="success"`; after these two requests its count increases by two. Duration sum is also exported; histogram buckets depend on registry configuration. With an exporter connected, find `neo4j.savePerson` under the HTTP request span.

### Check failures and shutdown { #failure-checks }

Stop the application, set `NEO4J_PASSWORD` to an incorrect value and run again. Initialization must fail before the HTTP service becomes usable. Restore `localpassword` and restart. To exercise operation failure, stop the database with `docker compose stop neo4j` and send another PUT: expect a server error, a warning with the error class and an increased failure timer count. Restore the database with `docker compose up -d --wait`. Driver retry limits are not an overall request deadline.

Stop the application with Ctrl+C so the graph releases the driver, then run `docker compose down`. This compose file has no persistent volume; its data is disposable.

## Best Practices { #best-practices }

- Keep one driver per graph and one session per operation.
- Parameterize Cypher and define database constraints for business keys.
- Keep transaction callbacks safe to retry; materialize results before closing resources.
- Configure limits for the environment and keep secrets outside source code.
- Use bounded metric tags and operation names; attach traces through Kora context.
- Separate integration mechanics from domain error mapping and schema migrations.

## Summary { #summary }

You created a reusable library, generated typed config, connected client lifecycle and telemetry to the graph, and verified a repeatable PUT against a real local database. Java and Kotlin share the same integration implementation.

## Key Concepts { #key-concepts }

- `@ConfigSource` generates mapping and a config factory module.
- Factory parameters describe dependencies; `@Module` provides reusable graph components.
- `Lifecycle` connects startup verification and cleanup to graph ownership.
- `Driver` is shared; `Session` and transaction results stay within an operation.
- Metrics, logs and traces describe the application operation, including retries.

## Troubleshooting { #troubleshooting }

**Missing `Neo4jConfig` or mapper at compilation**

Check AP in the library, the library runtime dependency and generated `Neo4jConfigModule`. A generated source in an unrelated output directory is not sufficient.

**Missing `Tracer` or `MeterRegistry`**

Extend the corresponding modules on `Application`. A dependency JAR alone does not connect its factories.

**Startup connectivity or authentication failure**

Run `docker compose ps`, check health and Bolt port `7687`, and compare the application password with `NEO4J_AUTH`. No HTTP call is needed to trigger this check.

**No metrics or exported spans**

Enable `metrics.enabled`, call PUT and inspect port `8085`. For traces check both tracing flags and exporter configuration; the driver wrapper does not install an exporter.

**Non-unique result or duplicate person nodes**

Create the uniqueness constraint before requests. Existing duplicate data must be cleaned before the constraint can be created.

## What's Next? { #whats-next }

- [AP and KSP for an Integration](integration-processors.md) demonstrates source generation with a small `@GenerateBuilder` processor; it is independent of this database client.
- [Creating a Kora Aspect](integration-aspect.md) adds compile-time method interception.
- [Integration Testing](testing-integration.md) shows how to verify infrastructure behavior in tests.

## Help { #help }

Compare graph wiring with [Dependency Injection](../documentation/container.md), config with [Configuration](../documentation/config.md), and telemetry with [Metrics](../documentation/metrics.md) and [Tracing](../documentation/tracing.md). For driver behavior use the [Neo4j Java driver manual](https://neo4j.com/docs/java-manual/current/).
