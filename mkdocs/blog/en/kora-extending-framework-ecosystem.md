---
title: The Ecosystem You Can Build — Why Extending the Kora Framework Is Deliberately Simple
description: How the Kora Framework's thin abstractions and module model let teams integrate any Java library through the same application graph.
search:
  exclude: true
---
# The Ecosystem You Can Build: Why Extending Kora Is Deliberately Simple

Framework ecosystems are usually discussed as inventories.

How many database integrations does the framework ship with? How many messaging systems have official modules? Is there a starter for Elasticsearch? Is there a starter for NATS? Is there a starter for MinIO? What about ClickHouse, a new cloud SDK, a workflow engine, a feature-flag client, a proprietary internal service, or the infrastructure product that appeared six months ago and is not yet on anyone's framework roadmap?

That way of measuring an ecosystem is understandable because prebuilt integrations are useful. If a framework already supports the exact technology a team needs, someone else has already solved configuration, lifecycle, dependency injection, metrics, tracing, health checks, shutdown behavior, testing, and perhaps code generation. The team can start from a working integration instead of building one.

But counting integrations is only one way to evaluate an ecosystem, and it can become misleading when treated as the primary measure of framework maturity.

A more important question is often this:

> **The real question is not how many integrations a framework already ships with, but how expensive it is to add the one you actually need.**

That distinction matters for the Kora Framework because Kora does not try to win an ecosystem contest by wrapping every Java library behind a framework-specific API. Its stated philosophy is narrower: use a controlled set of production-oriented modules, keep abstractions thin, keep application wiring explicit, allow framework components to be replaced, and let teams add their own modules through the same application model used by Kora itself.

This produces a different definition of ecosystem.

In a traditional large-ecosystem model, the framework's value is partly the number of adapters already available:

```text
Large ecosystem model

Need technology X
      ↓
Find official/community starter
      ↓
Learn its abstraction
      ↓
Learn its configuration
      ↓
Depend on its maintenance
      ↓
Use technology X through the starter
```

In an extensible-framework model, the path can be shorter:

```text
Extensible framework model

Need technology X
      ↓
Use native Java library
      ↓
Expose it through a small Kora module
      ↓
Add lifecycle/config/telemetry/probes
      ↓
Use it normally through DI
```

The second model does not eliminate integrations. Kora itself ships integrations for HTTP, JDBC, Cassandra, Kafka, gRPC, S3 and other infrastructure. It also provides production concerns such as configuration, telemetry, health probes, resilience, scheduling, validation, caching and testing. The difference is that those integrations are not supposed to establish a rule that every external technology must first be translated into a large Kora-specific subsystem before application code may use it.

That is the central argument of this article.

A small ecosystem is a serious problem when the framework is difficult to extend. It is much less serious when extending the framework is a local, typed and transparent exercise.

And Kora's architecture is unusually well suited to that second model.

---

## Ecosystem Size and Ecosystem Friction Are Different Things

Imagine two frameworks.

Framework A ships 500 integrations. Most are exposed through framework-specific abstractions, configuration conventions, lifecycle hooks, starter dependencies and runtime extension mechanisms. Integrating a technology outside that catalog requires understanding several framework internals and reproducing conventions that are not obvious from ordinary application code.

Framework B ships 50 integrations. Its application graph is explicit, modules are regular interfaces with factory methods, configuration is typed, lifecycle is a small interface, probes are ordinary components, telemetry is built from normal Java contracts, and the application can replace default components simply by declaring another factory.

Which framework has the better ecosystem?

If the exact technology you need is integration number 327 in Framework A, Framework A may clearly be more convenient today.

If the technology you need is integration number 501, the answer becomes less obvious.

A framework with 500 integrations that are difficult to understand is not necessarily more extensible than a framework with 50 integrations where the 51st can be written in a few straightforward classes.

This is the difference between *ecosystem breadth* and *ecosystem elasticity*.

Breadth asks:

```text
How much is already present?
```

Elasticity asks:

```text
How expensive is the next missing thing?
```

Both matter, but the second is often underappreciated.

The reason is simple: real production systems eventually contain something outside the framework's official catalog.

It may be an internal RPC client. It may be a vendor SDK. It may be a database driver the framework does not know. It may be a security appliance. It may be a new messaging platform. It may be a specialized cloud product. It may be a proprietary library maintained by another team in the same company.

At that point the practical quality of the framework is determined not by the size of its existing ecosystem but by the cost of crossing its boundary.

---

## Why Large Ecosystems Became So Valuable

There is a historical reason Java developers often equate framework maturity with integration count.

For years, integrating infrastructure into enterprise Java applications was genuinely expensive. A library rarely needed only construction. It also needed configuration binding, connection lifecycle, thread management, health checks, transaction participation, metrics, tracing, retry policies, shutdown handling, dependency injection and test infrastructure.

Framework starters packaged those concerns into reusable units.

Spring's ecosystem is the obvious example. The value of Spring Boot has never been only dependency injection. A major part of its value is that teams can add a dependency, configure a few properties and receive a substantial amount of infrastructure behavior automatically.

That is enormously useful.

But there is a trade-off. The more behavior a starter owns, the more developers depend on the starter's abstraction, configuration model, conditional logic, runtime conventions and maintenance schedule. The underlying library's own documentation may become insufficient because the framework integration changes how the library is created or used.

This leads to a second ecosystem layered on top of the first.

For example, instead of learning only:

```text
NATS Java client
```

developers may need to learn:

```text
Framework NATS starter
+
framework properties
+
framework wrapper API
+
framework lifecycle rules
+
framework telemetry behavior
+
native NATS concepts
```

That additional layer can be worth it when it provides substantial value.

The question is whether it is required for every integration.

Kora's design suggests that often it is not.

---

## Kora's Extension Model Starts With Ordinary Java

Kora's dependency injection model is important here because modules are not hidden runtime plugin descriptors.

A module is fundamentally an interface containing factory methods.

Conceptually:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface MyLibraryModule {

        default MyClient myClient(MyClientConfig config) {
            return new MyClient(config.endpoint());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface MyLibraryModule {

        fun myClient(config: MyClientConfig): MyClient {
            return MyClient(config.endpoint())
        }
    }
    ```

The return value becomes a component in the application graph. Method parameters are dependencies. Kora validates that graph at compile time and generates ordinary startup code.

That is already enough to integrate many Java libraries.

The library does not need to know about Kora.

The library does not need a Kora-specific adapter interface.

The library does not need to be discovered dynamically.

The application does not need a runtime plugin registry.

The integration boundary is simply a factory:

```text
Kora graph
   ↓
factory method
   ↓
native library object
```

Once that object is in the graph, other components inject it normally.

This sounds almost trivial, and that is precisely the point.

A framework extension mechanism is healthiest when simple extensions are simple.

---

## `@Module` Is a Composition Mechanism, Not a Mini-Framework

The temptation when building framework integrations is to invent another framework inside the framework.

Suppose a team wants NATS support. It could create a large Kora-specific abstraction:

```text
KoraNatsClient
KoraNatsPublisher
KoraNatsSubscriber
KoraNatsMessage
KoraNatsHeaders
KoraNatsConsumerFactory
KoraNatsConnectionManager
KoraNatsTemplate
KoraNatsProperties
```

Application code would then use these types instead of the official NATS Java API.

That may be justified if the framework can provide meaningful semantics that the native library lacks. But doing it by default creates a semantic gap.

Developers now have to translate documentation:

```text
NATS documentation
        ↓
How does this map to KoraNatsTemplate?
        ↓
What does Kora hide?
        ↓
What is configurable?
        ↓
What version of the underlying library is wrapped?
```

Kora's module model allows a much smaller integration:

```text
NatsConfig
NatsModule
NatsTelemetry
NatsReadinessProbe
```

and the actual client can still be:

===! ":fontawesome-brands-java: `Java`"

    ```java
    io.nats.client.Connection
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    io.nats.client.Connection
    ```

That means every example in the official NATS Java documentation remains useful.

If NATS adds a new API tomorrow, application code can often use it immediately after upgrading the dependency. The framework integration does not necessarily need a new abstraction first.

This is one of the strongest consequences of thin abstractions:

> **Thin abstractions preserve the documentation and ecosystem of the underlying technology.**

Kora does not need to recreate the NATS ecosystem because it can compose with it.

---

## What an Infrastructure Integration Actually Needs

It is useful to separate the essential framework responsibilities from the native library responsibilities.

For a typical client library, the native library should own domain-specific behavior:

```text
protocol
serialization
connection semantics
reconnect semantics
requests
publishing
subscriptions
client-specific errors
client-specific tuning
```

The application framework needs to connect that library to the service lifecycle:

```text
typed configuration
dependency wiring
startup
shutdown
telemetry
health/readiness
testing
optional policy wrappers
```

This gives us a generic integration pipeline:

```text
Native library
      ↓
Typed config
      ↓
Client factory
      ↓
Lifecycle
      ↓
Kora module
      ↓
Telemetry
      ↓
Probes
      ↓
Application injection
```

Most custom Kora integrations can stop there.

There is no need to build a general-purpose extension subsystem unless the integration genuinely requires code generation or deeper compile-time behavior.

That distinction is important because Kora does have a compile-time extension mechanism for advanced cases. Framework modules can teach the compiler how to create dependencies such as generated repositories, declarative HTTP clients, mappers, validators or gRPC stubs. But that is a system-level tool, not the normal starting point for integrating a Java SDK.

The ordinary path is much simpler: factory methods and graph components first; compiler extension only when generation creates real value.

---

# Walkthrough: Let's Integrate a Library Kora Doesn't Support

To make the argument concrete, consider NATS.

Assume our Kora application needs the official NATS Java client. We want:

- typed configuration;
- one shared NATS connection;
- startup connection establishment;
- graceful shutdown;
- connection readiness;
- basic telemetry around publishing;
- normal dependency injection;
- direct access to the native NATS API.

The important constraint is that we will not invent a NATS framework inside Kora.

Application code should still understand that it is using NATS.

The final dependency shape will look like this:

```text
application.conf
      ↓
NatsConfig
      ↓
NatsModule
      ↓
Nats Connection
      ├─────────────→ NatsPublisher
      ├─────────────→ NatsReadinessProbe
      └─────────────→ application services
                         ↓
                    native NATS API
```

This is deliberately boring.

That is a feature.

---

## Step 1: Add the Native Library

The Gradle dependency belongs to the NATS ecosystem, not to Kora:

```groovy
dependencies {
    implementation "io.nats:jnats:<version>"
}
```

Nothing about this dependency needs to change because the application uses Kora.

If the team reads an official NATS example showing:

===! ":fontawesome-brands-java: `Java`"

    ```java
    Connection connection = Nats.connect(options);
    connection.publish("orders.created", payload);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val connection = Nats.connect(options)
    connection.publish("orders.created", payload)
    ```

that knowledge remains directly applicable.

This is the first sign that the integration is thin.

---

## Step 2: Define Typed Configuration

In Kora 2, configuration can be modeled as a typed interface and bound directly to a configuration path.

For example:

===! ":fontawesome-brands-java: `Java`"

    ```java
    package com.example.nats;

    import io.koraframework.config.common.annotation.ConfigSource;

    import java.time.Duration;
    import java.util.List;

    @ConfigSource("nats")
    public interface NatsConfig {

        List<String> servers();

        default String connectionName() {
            return "orders-service";
        }

        default int maxReconnects() {
            return -1;
        }

        default Duration connectionTimeout() {
            return Duration.ofSeconds(5);
        }

        default boolean readinessEnabled() {
            return true;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package com.example.nats

    import io.koraframework.config.common.annotation.ConfigSource
    import java.time.Duration

    @ConfigSource("nats")
    interface NatsConfig {

        fun servers(): List<String>

        fun connectionName(): String {
            return "orders-service"
        }

        fun maxReconnects(): Int {
            return -1
        }

        fun connectionTimeout(): Duration {
            return Duration.ofSeconds(5)
        }

        fun readinessEnabled(): Boolean {
            return true
        }
    }
    ```

The application's HOCON configuration can remain equally direct:

===! ":material-code-json: Hocon"

    ```hocon
    nats {
      servers = [
        "nats://nats-1:4222",
        "nats://nats-2:4222"
      ]

      connectionName = "orders-service"
      maxReconnects = -1
      connectionTimeout = 5s
      readinessEnabled = true
    }
    ```

=== ":simple-yaml: YAML"

    ```yaml
    nats:
      servers:
        - "nats://nats-1:4222"
        - "nats://nats-2:4222"
      connectionName: "orders-service"
      maxReconnects: -1
      connectionTimeout: 5s
      readinessEnabled: true
    ```

There is no generic property bag passed around the application.

`NatsConfig` is a typed graph dependency.

That matters for custom integrations because configuration becomes part of the compile-time architecture. Factory methods request `NatsConfig`; services do not repeatedly search raw configuration trees; tests can replace or provide configuration explicitly.

The integration now has a clear contract:

```text
configuration
     ↓
NatsConfig
```

---

## Step 3: Create Native NATS Options

The next component translates service configuration into the native NATS `Options` object.

===! ":fontawesome-brands-java: `Java`"

    ```java
    package com.example.nats;

    import io.nats.client.Options;
    import io.koraframework.common.annotation.Module;

    @Module
    public interface NatsModule {

        default Options natsOptions(NatsConfig config) {
            var builder = new Options.Builder()
                .servers(config.servers().toArray(String[]::new))
                .connectionName(config.connectionName())
                .maxReconnects(config.maxReconnects())
                .connectionTimeout(config.connectionTimeout());

            return builder.build();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package com.example.nats

    import io.nats.client.Options
    import io.koraframework.common.annotation.Module

    @Module
    interface NatsModule {

        fun natsOptions(config: NatsConfig): Options {
            val builder = Options.Builder()
                .servers(config.servers().toTypedArray())
                .connectionName(config.connectionName())
                .maxReconnects(config.maxReconnects())
                .connectionTimeout(config.connectionTimeout())

            return builder.build()
        }
    }
    ```

Notice what we are *not* doing.

We are not reproducing every `Options.Builder` property in a new framework abstraction.

If the project only needs four options, expose four options.

If later it needs authentication, TLS, reconnect tuning or another NATS feature, add those deliberately.

The integration remains application-shaped rather than trying to mirror the entire third-party API.

This is one of the advantages of local integrations over universal starters: they can be exactly as large as the application requires.

---

## Step 4: Give the Connection a Lifecycle

A connection is not just a value. It owns resources and must be closed.

Kora's lifecycle model makes this explicit.

One option is to create a small component that implements `Lifecycle`. Another is to return a wrapped component from a module factory. If a native client is `AutoCloseable`, Kora can also close it automatically when the graph is released.

For clarity, we can use a dedicated holder:

===! ":fontawesome-brands-java: `Java`"

    ```java
    package com.example.nats;

    import io.nats.client.Connection;
    import io.nats.client.Nats;
    import io.nats.client.Options;
    import io.koraframework.application.graph.Lifecycle;

    public final class NatsConnectionLifecycle implements Lifecycle {

        private final Options options;
        private volatile Connection connection;

        public NatsConnectionLifecycle(Options options) {
            this.options = options;
        }

        @Override
        public void init() throws Exception {
            this.connection = Nats.connect(options);
        }

        @Override
        public void release() throws Exception {
            var current = this.connection;
            if (current != null) {
                current.close();
            }
        }

        public Connection connection() {
            var current = this.connection;
            if (current == null) {
                throw new IllegalStateException("NATS connection is not initialized");
            }
            return current;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package com.example.nats

    import io.nats.client.Connection
    import io.nats.client.Nats
    import io.nats.client.Options
    import io.koraframework.application.graph.Lifecycle

    class NatsConnectionLifecycle(private val options: Options) : Lifecycle {

        @Volatile
        private var connection: Connection? = null

        override fun init() {
            this.connection = Nats.connect(options)
        }

        override fun release() {
            connection?.close()
        }

        fun connection(): Connection {
            return connection
                ?: throw IllegalStateException("NATS connection is not initialized")
        }
    }
    ```

Then expose both lifecycle and connection through the module:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface NatsModule {

        default Options natsOptions(NatsConfig config) {
            return new Options.Builder()
                .servers(config.servers().toArray(String[]::new))
                .connectionName(config.connectionName())
                .maxReconnects(config.maxReconnects())
                .connectionTimeout(config.connectionTimeout())
                .build();
        }

        default NatsConnectionLifecycle natsConnectionLifecycle(Options options) {
            return new NatsConnectionLifecycle(options);
        }

        default Connection natsConnection(NatsConnectionLifecycle lifecycle) {
            return lifecycle.connection();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface NatsModule {

        fun natsOptions(config: NatsConfig): Options {
            return Options.Builder()
                .servers(config.servers().toTypedArray())
                .connectionName(config.connectionName())
                .maxReconnects(config.maxReconnects())
                .connectionTimeout(config.connectionTimeout())
                .build()
        }

        fun natsConnectionLifecycle(options: Options): NatsConnectionLifecycle {
            return NatsConnectionLifecycle(options)
        }

        fun natsConnection(lifecycle: NatsConnectionLifecycle): Connection {
            return lifecycle.connection()
        }
    }
    ```

In a production implementation we would be careful about the precise graph initialization relationship so the connection component becomes available after lifecycle initialization. Kora also provides lifecycle wrappers specifically for factories that return a value requiring initialization and release.

The architectural point is unchanged:

```text
create native client
      ↓
attach lifecycle
      ↓
put native client in graph
```

The framework does not need a hidden bean post-processor to discover that a NATS connection has startup and shutdown behavior.

The lifecycle is code.

---

## A Cleaner Version With a Lifecycle Wrapper

For a library object that should be injected directly, Kora's wrapper mechanism can keep the graph even smaller.

Conceptually:

===! ":fontawesome-brands-java: `Java`"

    ```java
    default Wrapped<Connection> natsConnection(Options options) {
        var holder = new AtomicReference<Connection>();

        return new LifecycleWrapper<>(
            Nats.connect(options),
            connection -> {
                // optional initialization hook
            },
            connection -> {
                connection.close();
            }
        );
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun natsConnection(options: Options): Wrapped<Connection> {
        val holder = AtomicReference<Connection>()

        return LifecycleWrapper(
            Nats.connect(options),
            { connection ->
                // optional initialization hook
            },
            { connection ->
                connection.close()
            }
        )
    }
    ```

The exact factory can be adapted to whether connection establishment occurs during construction or explicit initialization, but the useful property of `Wrapped<T>` is that application code can request `Connection`, while the graph still knows that the value has lifecycle behavior.

This pattern generalizes to many native clients:

```text
ClickHouse client
Elasticsearch client
MinIO client
vendor SDK
custom connection pool
embedded engine
```

If the client is just a normal Java object, Kora usually needs only a normal factory plus lifecycle semantics.

---

## Step 5: Add a Small Application-Level Publisher

The application could inject `Connection` directly everywhere:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class OrderEvents {

        private final Connection nats;

        public OrderEvents(Connection nats) {
            this.nats = nats;
        }

        public void created(byte[] payload) {
            nats.publish("orders.created", payload);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class OrderEvents(private val nats: Connection) {

        fun created(payload: ByteArray) {
            nats.publish("orders.created", payload)
        }
    }
    ```

For many systems this is perfectly acceptable.

If the team wants centralized telemetry or subject naming, add one thin application-level wrapper:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class NatsPublisher {

        private final Connection connection;
        private final NatsTelemetry telemetry;

        public NatsPublisher(Connection connection, NatsTelemetry telemetry) {
            this.connection = connection;
            this.telemetry = telemetry;
        }

        public void publish(String subject, byte[] payload) {
            var context = telemetry.publish(subject, payload.length);
            try {
                connection.publish(subject, payload);
                context.success();
            } catch (RuntimeException e) {
                context.failure(e);
                throw e;
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class NatsPublisher(
        private val connection: Connection,
        private val telemetry: NatsTelemetry
    ) {

        fun publish(subject: String, payload: ByteArray) {
            val context = telemetry.publish(subject, payload.size)
            try {
                connection.publish(subject, payload)
                context.success()
            } catch (e: RuntimeException) {
                context.failure(e)
                throw e
            }
        }
    }
    ```

This wrapper is not trying to replace the NATS client.

It adds one concern the application wants to standardize.

Application code that needs low-level NATS operations can still inject `Connection`.

Application code that only publishes events can inject `NatsPublisher`.

That is what a thin abstraction looks like in practice.

---

## Step 6: Add Telemetry Without Rebuilding NATS

Suppose we want metrics and tracing around application publishes.

Define a small contract:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface NatsTelemetry {

        PublishContext publish(String subject, int payloadBytes);

        interface PublishContext {
            void success();
            void failure(Throwable error);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface NatsTelemetry {

        fun publish(subject: String, payloadBytes: Int): PublishContext

        interface PublishContext {
            fun success()
            fun failure(error: Throwable)
        }
    }
    ```

A Micrometer/OpenTelemetry-backed implementation can use the telemetry components already present in the application graph.

For example, conceptually:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class DefaultNatsTelemetry implements NatsTelemetry {

        private final MeterRegistry meterRegistry;

        public DefaultNatsTelemetry(MeterRegistry meterRegistry) {
            this.meterRegistry = meterRegistry;
        }

        @Override
        public PublishContext publish(String subject, int payloadBytes) {
            var start = System.nanoTime();

            return new PublishContext() {
                @Override
                public void success() {
                    meterRegistry.counter(
                        "nats.publish",
                        "subject", subject,
                        "result", "success"
                    ).increment();

                    recordDuration(start, subject);
                }

                @Override
                public void failure(Throwable error) {
                    meterRegistry.counter(
                        "nats.publish",
                        "subject", subject,
                        "result", "failure"
                    ).increment();

                    recordDuration(start, subject);
                }
            };
        }

        private void recordDuration(long start, String subject) {
            var elapsed = System.nanoTime() - start;

            // Timer recording omitted for brevity.
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class DefaultNatsTelemetry(private val meterRegistry: MeterRegistry) : NatsTelemetry {

        override fun publish(subject: String, payloadBytes: Int): NatsTelemetry.PublishContext {
            val start = System.nanoTime()

            return object : NatsTelemetry.PublishContext {
                override fun success() {
                    meterRegistry.counter(
                        "nats.publish",
                        "subject", subject,
                        "result", "success"
                    ).increment()

                    recordDuration(start, subject)
                }

                override fun failure(error: Throwable) {
                    meterRegistry.counter(
                        "nats.publish",
                        "subject", subject,
                        "result", "failure"
                    ).increment()

                    recordDuration(start, subject)
                }
            }
        }

        private fun recordDuration(start: Long, subject: String) {
            val elapsed = System.nanoTime() - start

            // Timer recording omitted for brevity.
        }
    }
    ```

In a real production implementation, high-cardinality subject values must be considered carefully. Dynamic NATS subjects may need normalization before becoming metric tags.

The important architectural point is that telemetry is compositional.

We did not have to modify Kora's runtime.

We did not need a central plugin registry.

We did not need to wait for an official `kora-nats` module.

We took the telemetry primitives already used by the application and composed them around the native client.

This is exactly how Kora's own integrations are conceptually structured: runtime operations expose logging, metrics and tracing through small telemetry contracts.

---

## Step 7: Add Readiness

A production integration also needs operational semantics.

If this service cannot safely handle traffic when NATS is disconnected, the NATS connection can participate in readiness.

Kora probes are ordinary graph components implementing small interfaces.

A readiness component might look like:

===! ":fontawesome-brands-java: `Java`"

    ```java
    package com.example.nats;

    import io.nats.client.Connection;
    import io.koraframework.common.annotation.Component;
    import io.koraframework.common.readiness.ReadinessProbe;
    import io.koraframework.common.readiness.ReadinessProbeFailure;

    @Component
    public final class NatsReadinessProbe implements ReadinessProbe {

        private final Connection connection;
        private final NatsConfig config;

        public NatsReadinessProbe(Connection connection, NatsConfig config) {
            this.connection = connection;
            this.config = config;
        }

        @Override
        public ReadinessProbeFailure probe() {
            if (!config.readinessEnabled()) {
                return null;
            }

            if (connection.getStatus() == Connection.Status.CONNECTED) {
                return null;
            }

            return new ReadinessProbeFailure(
                "NATS connection is not connected: " + connection.getStatus()
            );
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    package com.example.nats

    import io.nats.client.Connection
    import io.koraframework.common.annotation.Component
    import io.koraframework.common.readiness.ReadinessProbe
    import io.koraframework.common.readiness.ReadinessProbeFailure

    @Component
    class NatsReadinessProbe(
        private val connection: Connection,
        private val config: NatsConfig
    ) : ReadinessProbe {

        override fun probe(): ReadinessProbeFailure? {
            if (!config.readinessEnabled()) {
                return null
            }

            if (connection.status == Connection.Status.CONNECTED) {
                return null
            }

            return ReadinessProbeFailure(
                "NATS connection is not connected: " + connection.status
            )
        }
    }
    ```

Now the integration participates in the same application readiness model as the HTTP server, gRPC server, JDBC datasource and any other registered readiness component.

Again, there is no special NATS extension registry.

The graph sees an ordinary `ReadinessProbe`.

The management endpoint aggregates it with the others.

That is reuse through contracts rather than reuse through hidden extension points.

---

## Should an External Broker Be a Readiness Dependency?

This walkthrough also reveals an important architectural advantage of explicit integrations: policy decisions remain visible.

Whether NATS disconnection should make the whole service unready is not a framework question. It is an application question.

For some services, NATS is essential. Without it the instance cannot perform its job, so failing readiness may be appropriate.

For another service, NATS publishing is optional or buffered. Taking the instance out of rotation because the broker is temporarily unreachable may make an outage worse.

The integration should not silently decide that policy.

A typed config flag such as:

```text
readinessEnabled
```

makes the decision explicit.

This is another benefit of not overbuilding the abstraction. Framework integrations should provide mechanisms; service architecture should choose policy.

---

## Step 8: Inject the Native Connection Normally

Once the module is connected to the application, any component can request `Connection`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class FraudEvents {

        private final Connection nats;

        public FraudEvents(Connection nats) {
            this.nats = nats;
        }

        public void suspiciousTransaction(byte[] event) {
            nats.publish("fraud.suspicious", event);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class FraudEvents(private val nats: Connection) {

        fun suspiciousTransaction(event: ByteArray) {
            nats.publish("fraud.suspicious", event)
        }
    }
    ```

Or it can request the telemetry wrapper:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class OrderEvents {

        private final NatsPublisher publisher;

        public OrderEvents(NatsPublisher publisher) {
            this.publisher = publisher;
        }

        public void created(byte[] event) {
            publisher.publish("orders.created", event);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class OrderEvents(private val publisher: NatsPublisher) {

        fun created(event: ByteArray) {
            publisher.publish("orders.created", event)
        }
    }
    ```

Nothing else changes.

The application remains ordinary constructor-injected Java.

---

## Step 9: Connect the Module Explicitly

Kora deliberately does not search external dependencies for arbitrary modules at runtime.

That means the integration is connected explicitly.

For an application-local module:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application
    ```

the compiler can discover local `@Module` declarations in the same compilation scope.

If the NATS integration is moved into a reusable library module, the application can connect its external module explicitly through the application interface.

Conceptually:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends NatsModule, LogbackModule {
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : NatsModule, LogbackModule
    ```

The final application architecture is visible at the assembly point.

This matters because extension mechanisms tend to become difficult to reason about when adding a dependency silently adds runtime behavior.

Kora's model prefers:

```text
dependency present
+
module explicitly connected
=
integration active
```

rather than:

```text
dependency present
=
maybe some runtime auto-configuration activates
depending on classpath and configuration
```

That explicitness makes custom integrations easier to audit.

---

## The Entire Integration Is Small Enough to Understand

Collect the pieces:

```text
NatsConfig
NatsModule
NatsTelemetry
DefaultNatsTelemetry
NatsPublisher
NatsReadinessProbe
```

That is already a production-shaped integration.

If lifecycle handling is encapsulated in the module, the application-specific surface may be only a few classes.

A reusable internal library could organize them like this:

```text
company-kora-nats/
├── NatsConfig.java
├── NatsModule.java
├── NatsTelemetry.java
├── DefaultNatsTelemetry.java
└── NatsReadinessProbe.java
```

The application uses:

```text
io.nats.client.Connection
```

for the actual NATS protocol API.

There is no framework inside the framework.

That is the key result of the walkthrough.

---

# Why `@Module` Works So Well for Integrations

The power of `@Module` comes from how little it assumes.

A factory method says:

```text
Given these graph dependencies,
create this graph component.
```

That is enough to express:

- native clients;
- connection pools;
- SDKs;
- serializers;
- registries;
- executors;
- managers;
- factories;
- adapters;
- policy objects;
- infrastructure services.

Consider ClickHouse.

A module can map config to a native client:

```text
ClickHouseConfig
      ↓
ClickHouseClient
```

Consider Elasticsearch:

```text
ElasticsearchConfig
      ↓
transport
      ↓
ElasticsearchClient
```

Consider MinIO:

```text
MinioConfig
      ↓
MinioClient
```

Consider a new cloud SDK:

```text
CloudConfig
      ↓
credentials provider
      ↓
SDK client
```

None of these require Kora to know the technology.

The graph only needs to know object dependencies.

---

# Configuration Is an Integration Boundary

Configuration is often where third-party integrations become messy because frameworks try to support every option of every library.

Kora's typed configuration model encourages a narrower strategy.

Define only what your service needs.

For example:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @ConfigSource("search")
    public interface SearchConfig {

        String endpoint();

        Duration timeout();

        default int maxConnections() {
            return 50;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @ConfigSource("search")
    interface SearchConfig {

        fun endpoint(): String

        fun timeout(): Duration

        fun maxConnections(): Int {
            return 50
        }
    }
    ```

Then build the native library configuration:

===! ":fontawesome-brands-java: `Java`"

    ```java
    default SearchClient searchClient(SearchConfig config) {
        return SearchClient.builder()
            .endpoint(config.endpoint())
            .timeout(config.timeout())
            .maxConnections(config.maxConnections())
            .build();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun searchClient(config: SearchConfig): SearchClient {
        return SearchClient.builder()
            .endpoint(config.endpoint())
            .timeout(config.timeout())
            .maxConnections(config.maxConnections())
            .build()
    }
    ```

This has several advantages.

First, application configuration remains stable even if the native library changes some builder names.

Second, the service does not expose 80 irrelevant tuning properties merely because the library has 80.

Third, configuration becomes part of the graph and can be replaced in tests.

Fourth, required values are statically represented as required methods rather than undocumented strings.

Fifth, configuration mapping code can be generated by Kora instead of manually parsing maps.

The custom integration therefore gets a production-grade configuration story almost for free.

---

# Lifecycle Is a First-Class Contract

Infrastructure libraries frequently allocate resources:

- sockets;
- executors;
- connection pools;
- file descriptors;
- background workers;
- network channels;
- native memory.

A framework integration has to ensure those resources start and stop with the application.

Kora makes that concern explicit through lifecycle contracts.

A component can implement:

===! ":fontawesome-brands-java: `Java`"

    ```java
    Lifecycle
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    Lifecycle
    ```

with:

```text
init()
release()
```

or a factory can return a lifecycle-wrapped value. Components implementing `AutoCloseable` can also participate naturally in cleanup.

This is important for extensibility because lifecycle is not tied to a special built-in integration registry.

Your custom client receives the same container behavior as framework-provided infrastructure.

The dependency graph also controls order.

If:

```text
OrderConsumer
      ↓
NATS Connection
```

then creation and release order follow those dependencies.

The integration author does not have to build another shutdown manager.

---

# Health and Probes Are Also Ordinary Components

The same pattern appears in health checks.

Kora's liveness and readiness systems aggregate components implementing probe interfaces.

A custom infrastructure integration does not need to register a callback with a hidden health subsystem.

It can simply expose:

===! ":fontawesome-brands-java: `Java`"

    ```java
    ReadinessProbe
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    ReadinessProbe
    ```

or:

===! ":fontawesome-brands-java: `Java`"

    ```java
    LivenessProbe
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    LivenessProbe
    ```

as a component.

That means an unsupported technology can participate in operational readiness exactly like a built-in technology.

This is an important difference between an extension API and a composition model.

An extension API usually asks:

```text
How do I plug into subsystem X?
```

A composition model asks:

```text
Which ordinary contract represents this concern?
```

The second tends to produce simpler integrations.

---

# Telemetry Does Not Need a Universal Adapter

Telemetry is where framework integrations often become large because every library operation may need metrics and tracing.

But even here, not every integration needs a full framework-specific API.

There are at least three levels of integration.

### Level 1: use native telemetry

If the Java library already emits OpenTelemetry or Micrometer metrics, simply configure those facilities and expose the relevant registries through the graph.

### Level 2: wrap application operations

If only a few operations matter, use a small wrapper such as `NatsPublisher`.

```text
application
    ↓
small telemetry wrapper
    ↓
native client
```

### Level 3: build a reusable Kora telemetry contract

If the integration becomes widely shared across many services, define a structured telemetry factory similar to Kora's built-in HTTP, database, Kafka or gRPC telemetry contracts.

The important point is that teams can evolve from Level 1 to Level 3 as actual reuse appears.

They do not need to build Level 3 on day one merely to connect the library.

That dramatically lowers the initial cost of the 51st integration.

---

# AOP Is Available When the Integration Actually Needs It

Most library integrations do not require AOP.

If an integration needs cross-cutting policies around application methods, Kora's compile-time AOP model can be used.

Examples might include:

- retry around selected SDK calls;
- circuit breaker policies;
- timeout boundaries;
- custom authorization;
- logging;
- validation;
- transaction-like scopes.

But this should be a second-order decision.

The integration itself can usually remain a normal module.

This is important because frameworks sometimes make extension development difficult by requiring custom annotations and interceptors for even basic wiring.

Kora's simpler path is:

```text
factory first
AOP only if needed
```

not:

```text
everything is an extension plugin
```

---

# Generated Code Does Not Make Custom Integrations Opaque

Kora uses code generation heavily, but that does not mean application integrations have to become compiler projects.

The generated part primarily connects the graph and framework contracts.

If `NatsPublisher` depends on `Connection` and `NatsTelemetry`, the generated application graph contains the wiring corresponding to that relationship.

The integration author still writes ordinary Java.

This creates a useful separation:

```text
Your integration logic
       ↓
plain Java classes and factories

Framework assembly
       ↓
generated graph code
```

If dependency wiring is wrong, compilation fails.

If two connections are ambiguous, tags can make them explicit.

If a required component is missing, graph construction fails at compile time.

There is no need to debug a runtime plugin loader to understand why the integration did not activate.

---

# Replacing Framework Components Is Part of Extensibility

Extensibility is not only about adding new technologies.

It is also about replacing pieces of existing integrations.

Kora's DI model supports default components that application code can override with a non-default component of the same type and tags.

This matters because built-in integrations inevitably make choices.

A framework may provide a default logger, telemetry factory, mapper, HTTP client component, executor, serializer or policy implementation.

A closed integration says:

```text
Use our implementation or replace the whole module.
```

A compositional integration says:

```text
This component is a default.
Provide your own if you need different behavior.
```

That makes customization local.

For example:

```text
Kora default telemetry factory
            ↓
application supplies custom implementation
            ↓
graph selects application component
```

No fork.

No reflection hack.

No bean-definition surgery.

No undocumented ordering trick.

This property is especially important for organizations that standardize infrastructure differently from framework defaults.

---

# Thin Abstractions Preserve Vendor Knowledge

Suppose a developer already understands Kafka.

A thick framework abstraction can reduce how much of that knowledge transfers.

The developer now needs to know which Kafka features are exposed, how partition assignment maps into the framework abstraction, where consumer settings live, how native types are hidden, how errors are translated and whether a framework-specific retry layer changes semantics.

A thin abstraction preserves more of the original mental model.

The same applies to:

- JDBC;
- gRPC;
- HTTP;
- NATS;
- Elasticsearch;
- ClickHouse;
- MinIO;
- AWS SDKs;
- Google Cloud SDKs;
- internal company clients.

This has a major ecosystem implication:

> A framework does not need to own the documentation of every technology if it preserves the native technology well enough that its documentation remains valid.

That is a different scalability model.

Instead of building:

```text
Kora ecosystem
    containing
    new documentation for everything
```

you get:

```text
Kora composition model
        +
native technology ecosystem
```

The second can be much larger in practice.

---

# Why This Matters More in the AI Era

This architecture becomes even more valuable when coding agents participate in development.

An AI agent often already has substantial knowledge of mainstream Java libraries and protocols.

It may know:

```text
NATS Java
Elasticsearch Java API Client
MinIO Java SDK
JDBC
Kafka
gRPC
OpenTelemetry
Micrometer
```

If Kora wraps every technology behind a unique abstraction, the agent has to learn a new translation layer.

If the Kora integration stays thin, existing knowledge transfers directly.

The agent only needs to understand the composition layer:

```text
How is this object placed in the Kora graph?
How is config mapped?
How is lifecycle attached?
How is readiness exposed?
```

Those are relatively stable Kora concepts.

The technology-specific work remains technology-specific.

This is a powerful scaling property for both humans and machines.

---

# The Native Library Remains the Escape Hatch

Every abstraction leaks eventually.

A starter may support 95% of a library and miss the exact advanced feature a project needs.

With a thick abstraction, developers face several options:

```text
wait for framework support
fork integration
reach through abstraction
reimplement feature
```

With a thin integration, the escape hatch is already present:

===! ":fontawesome-brands-java: `Java`"

    ```java
    Connection nats
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val nats: Connection
    ```

or:

===! ":fontawesome-brands-java: `Java`"

    ```java
    ElasticsearchClient client
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val client: ElasticsearchClient
    ```

or:

===! ":fontawesome-brands-java: `Java`"

    ```java
    MinioClient client
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val client: MinioClient
    ```

The native object is part of the graph.

Advanced features remain available.

That reduces ecosystem dependency.

---

# Internal Platforms Benefit Even More

The argument is not limited to public open-source libraries.

Large companies often have internal infrastructure:

- proprietary RPC clients;
- authorization clients;
- configuration services;
- feature flag systems;
- internal object stores;
- audit systems;
- internal event buses;
- company observability SDKs;
- policy engines;
- secrets clients.

No public framework ecosystem can ship official integrations for these.

Every organization eventually has to extend the framework.

A Kora internal integration library might look like:

```text
company-kora/
├── auth/
│   └── CompanyAuthModule
├── audit/
│   └── AuditModule
├── featureflags/
│   └── FeatureFlagsModule
├── messaging/
│   └── CompanyBusModule
└── telemetry/
    └── CompanyTelemetryModule
```

Each module can expose normal components through the same graph model.

This turns framework extensibility into platform engineering.

The company does not need to modify Kora itself.

---

# Reusable Integrations Can Evolve Gradually

A common mistake is to treat a new integration as a public framework project from the beginning.

A better path is incremental.

### Stage 1: application-local factory

===! ":fontawesome-brands-java: `Java`"

    ```java
    default Client client(Config config) {
        return new Client(...);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun client(config: Config): Client {
        return Client(...)
    }
    ```

### Stage 2: local typed config

```text
ClientConfig
Client factory
```

### Stage 3: lifecycle

```text
startup
shutdown
```

### Stage 4: operational integration

```text
readiness
metrics
tracing
logging
```

### Stage 5: reusable internal module

Move the code into a shared library.

### Stage 6: compile-time extension

Only if the integration benefits from code generation or generic type synthesis.

This progression avoids premature framework engineering.

The integration grows only when reuse justifies it.

---

# Kora Has a Deeper Extension Mechanism When You Need One

So far we have deliberately avoided Kora's compiler extension mechanism.

That is the right default for ordinary SDK integration.

But some integrations genuinely benefit from compile-time generation.

Imagine a custom declarative client:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @MyRpcClient
    public interface BillingClient {
        Invoice getInvoice(String id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @MyRpcClient
    interface BillingClient {
        fun getInvoice(id: String): Invoice
    }
    ```

If the organization wants Kora to synthesize an implementation whenever `BillingClient` is requested, a compiler extension can participate in dependency resolution and generate that implementation.

Kora uses this kind of mechanism internally for things such as:

- JSON readers and writers;
- repositories;
- declarative HTTP clients;
- gRPC stubs;
- configuration mappers;
- validators;
- mapping integrations.

This gives the framework two layers of extensibility:

```text
ordinary integration
      ↓
@Module + components

advanced generated integration
      ↓
compile-time extension
```

That separation is healthy.

Most teams can remain at the first layer.

Framework authors and platform teams can use the second when compile-time synthesis provides enough value.

---

# Explicit External Modules Prevent Classpath Surprise

One subtle but important feature of Kora's module design is that external modules are not automatically activated merely because a dependency is present.

They must be connected to the application.

This reduces a common form of framework uncertainty:

```text
Why did adding this dependency change startup behavior?
Which auto-configuration became active?
Which condition matched?
Which default component was registered?
```

Kora's explicit model looks more like:

```text
Application
   extends
   NatsModule
   HttpServerModule
   JsonModule
```

or equivalent composition through submodules.

The application assembly becomes architectural documentation.

For custom integrations, this is valuable because adoption is controlled by source code rather than classpath side effects.

---

# Modules Scale Into Multi-Module Applications

A reusable integration does not have to live next to the final application.

Kora supports submodule composition for multi-project builds.

That means a domain module can own both its own components and the infrastructure integrations it requires.

For example:

```text
orders module
├── OrdersService
├── OrdersRepository
├── OrdersEvents
└── OrdersInfrastructure
       ├── JDBC
       └── NATS
```

The application module then composes domain submodules.

Conceptually:

```text
Application
├── OrdersModule
├── BillingModule
├── CatalogModule
└── NotificationsModule
```

This is relevant to ecosystem design because integrations can be packaged at the same granularity as architecture.

Not every technology has to become a global framework feature.

An integration can belong to the domain that needs it.

---

# Two Connections Do Not Require a New Framework

Suppose an application needs two NATS clusters.

A thick integration may need custom multi-client support.

Kora's graph already has tags to distinguish components of the same type.

Conceptually:

```text
@Tag(MainNats)
Connection

@Tag(AuditNats)
Connection
```

Factories can map each connection to a different config section.

The same module pattern works for:

```text
primary database / replica database
internal / external HTTP client
main / archive object store
regional SDK clients
```

This illustrates another useful property: generic DI capabilities solve many integration requirements before a specialized framework abstraction is necessary.

---

# A Factory Module Can Parameterize Reusable Infrastructure

Kora 2 also supports parameterized factory modules.

This is useful when one reusable integration must be instantiated multiple times with different configuration paths or tags.

Conceptually:

```text
NatsFactoryModule("nats.main")
NatsFactoryModule("nats.audit")
```

Each produces a separate set of components.

That is a more scalable pattern than duplicating integration code.

It also shows that Kora's module model is not merely a list of singleton factories; it can express reusable infrastructure templates while staying type-driven and explicit.

---

# Testing a Custom Integration Is Straightforward

A good extension model must also be testable.

Because a custom integration is just part of the application graph, Kora's component testing model can request the relevant graph slice.

A test might ask for:

```text
NatsPublisher
NatsReadinessProbe
```

and replace `Connection` with a test component.

Conceptually:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(Application.class)
    class NatsPublisherTest {

        @TestComponent
        NatsPublisher publisher;

        // provide replacement connection
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(Application::class)
    class NatsPublisherTest {

        @TestComponent
        lateinit var publisher: NatsPublisher

        // provide replacement connection
    }
    ```

The important property is that testing does not require starting the entire application merely because the integration lives in the DI graph.

The graph can be sliced to required components and dependencies.

For integration tests, a real NATS container can be used and readiness can become the synchronization contract.

This gives the custom integration the same testing model as built-in components.

---

# Custom Integrations Should Be Boring

This is perhaps the strongest design criterion.

A good Kora integration should be boring to read.

Something like:

```text
Config
↓
Builder
↓
Client
↓
Lifecycle
↓
Telemetry
↓
Probe
```

If integrating a normal Java SDK requires:

```text
custom classpath scanner
custom reflection registry
runtime proxy factory
custom plugin descriptor
framework bootstrap hook
custom annotation processor
dynamic metadata cache
specialized context object
```

something has probably gone wrong.

Complexity may be justified for powerful declarative features, but it should not be the entrance fee.

Kora's architecture keeps that entrance fee low.

---

# The Ecosystem Count Can Hide Integration Quality

Imagine a framework advertises support for 300 technologies.

That number says nothing about whether each integration is:

- current;
- well maintained;
- transparent;
- customizable;
- compatible with the latest native client;
- observable;
- efficient;
- easy to debug;
- easy to replace.

An integration can exist and still become a liability.

For example, a framework adapter may lag two major versions behind the vendor SDK. The vendor's documentation may describe APIs unavailable through the wrapper. Advanced options may not be exposed. Bugs may require waiting for the adapter maintainer.

A thin integration reduces this dependency surface.

The application can often upgrade the native library directly because the Kora side consists of a small constructor or builder mapping.

This makes integration ownership cheaper.

---

# A Small Community Can Still Produce Useful Extensions Quickly

A framework with a smaller community will naturally have fewer ready-made modules than Spring.

That is a real disadvantage when the missing integration is complex.

But the severity of the disadvantage depends on how hard community modules are to create.

If an integration can start as:

```text
one config interface
one module
one probe
one telemetry adapter
```

then a small community can still cover missing technologies quickly.

The contribution does not require deep knowledge of hidden container internals.

It can be reviewed by reading ordinary code.

This lowers the barrier for both company-internal and open-source extensions.

---

# The Documentation Burden Also Becomes Smaller

Large integration ecosystems create a documentation scaling problem.

Every wrapper needs documentation for:

- configuration;
- lifecycle;
- features;
- examples;
- error handling;
- version compatibility;
- limitations;
- advanced options.

If the integration preserves the native library, the framework documentation can focus on the composition boundary.

For example:

```text
How to put NATS Connection in the graph
How to configure it
How lifecycle works
How telemetry hooks in
How readiness works
```

Everything else can point conceptually back to the official NATS API.

This avoids duplicating an entire vendor manual.

Again, thin abstractions preserve the native ecosystem.

---

# This Is Why JDBC Is Such a Powerful Model

JDBC remains one of the best examples of ecosystem leverage.

A framework can provide:

- datasource lifecycle;
- repository generation;
- transactions;
- telemetry;
- mapping;

while application developers still understand that the underlying technology is JDBC.

Knowledge about SQL, drivers, connection pools and database semantics transfers.

Kora's broader integration philosophy follows that pattern: add framework value around a technology without pretending the technology disappeared.

The same principle can be applied to new SDKs.

---

# When a Thick Abstraction Is Justified

Thin abstractions are not always sufficient.

Sometimes a framework can provide major value by introducing a stronger abstraction.

Examples include:

- generated repository interfaces;
- declarative HTTP clients;
- generated OpenAPI endpoints;
- cache annotations;
- resilience annotations;
- validation;
- cross-technology telemetry contracts.

These abstractions can remove substantial repetitive code.

The important question is whether the abstraction compresses real complexity.

A useful framework abstraction should satisfy something like:

```text
complexity removed
>
new framework-specific knowledge introduced
```

If it does, the abstraction earns its place.

If not, exposing the native library is often better.

---

# NATS Does Not Need to Become "Kora NATS"

Return to our example.

What did Kora add?

```text
typed config
graph construction
lifecycle
telemetry composition
readiness
testability
```

What remains NATS?

```text
Connection
Options
publish
subscribe
request/reply
JetStream
reconnection behavior
protocol semantics
subjects
messages
```

That division is healthy.

It gives us production integration without losing the native technology.

This is exactly why integrating NATS, ClickHouse, Elasticsearch, MinIO or a new SDK does not require writing "a framework inside the framework."

---

# The Integration Surface Can Be Visualized as a Thin Layer

A thick framework adapter often looks like this:

```text
Application
    ↓
Framework DSL
    ↓
Framework domain abstraction
    ↓
Framework adapter
    ↓
Native Java library
    ↓
Technology
```

A Kora-style thin integration can look like:

```text
Application
    ↓
Native Java API
    ↓
Technology

with a side layer for:

Config ─┐
DI ─────┤
Life ───┤──→ native client
OTel ───┤
Probe ──┘
```

The framework participates where the application lifecycle needs it.

It does not have to own the technology's conceptual model.

---

# Extension Cost Is a Better Long-Term Metric

Technology portfolios change continuously.

Today a team uses Kafka.

Tomorrow another workload uses NATS.

One service adds ClickHouse.

Another adopts a vector database.

A vendor introduces a new payments SDK.

A cloud provider releases a new managed API.

No framework can predict all of these.

Therefore ecosystem completeness is temporary.

Extension cost is structural.

A framework can add more official modules over time, but the more durable property is whether unknown future technologies can be connected without fighting the framework.

That is why extension cost deserves to be a first-class evaluation criterion.

---

# A Practical Integration Checklist for Kora

When adding an unsupported library, a team can ask a small set of questions.

## 1. What is the native object we actually want to inject?

Examples:

```text
Connection
Client
DataSource
Transport
SDK
Manager
```

Prefer exposing the native object unless a wrapper adds clear value.

## 2. What configuration does this service actually need?

Create a typed config contract.

Do not mirror the entire native library blindly.

## 3. Does the object own resources?

If yes, integrate it with lifecycle or `AutoCloseable`.

## 4. What does readiness mean?

Only add a probe if the external dependency genuinely affects the instance's ability to serve workload.

## 5. What telemetry is missing?

Reuse native telemetry when possible. Add a small wrapper where necessary.

## 6. Does the integration need cross-cutting policies?

Use resilience or AOP only where the application actually needs them.

## 7. Do we need more than one instance?

Use tags or a parameterized factory module.

## 8. Should this become reusable?

Start local. Extract a shared module when multiple services need the same integration.

## 9. Does it require code generation?

If not, stop at normal modules and components.

That checklist covers a surprising amount of infrastructure integration work.

---

# What This Model Does Not Solve

This architecture is not magic.

Some integrations are genuinely hard.

A Kafka integration is not just a client constructor because consumer lifecycle, partition assignment, retries, offset commits, backpressure, telemetry and shutdown semantics are substantial.

A database integration may need transactions, pooling, query telemetry, repository generation and mapping.

A workflow engine may require worker registration, state management and complex runtime coordination.

For these technologies, an official framework module can save a lot of work.

The argument is not that ecosystems do not matter.

The argument is that ecosystem *size alone* is a weak predictor of how painful missing integrations will be.

A framework that is easy to extend reduces the penalty of gaps.

---

# Official Integrations Still Matter

There are several reasons to prefer an official Kora module when one exists.

First, it is already integrated with Kora's telemetry conventions.

Second, lifecycle and readiness behavior have already been designed.

Third, configuration conventions are consistent with other modules.

Fourth, the module is tested against framework releases.

Fifth, code generation may provide capabilities that a simple factory cannot.

Sixth, performance tuning may already be done.

So the decision tree is not:

```text
Never use framework integrations.
```

It is:

```text
Official integration exists and fits?
        ↓ yes
Use it.

        ↓ no
Can native Java library + small module solve it?
        ↓ yes
Build thin integration.

        ↓ no
Create deeper reusable extension.
```

That is a healthy ecosystem strategy.

---

# Kora's Philosophy Makes This Deliberate

The Kora 2 landing page explicitly states that the framework does not pursue breadth for its own sake or wrap every possible technology behind a framework-specific abstraction. It also emphasizes that applications can use only the modules they need, replace or customize components, and add modules through the same explicit application model.

That philosophy is important because extensibility is easier when the framework itself follows the same rules expected of user code.

If framework internals rely on hidden privileged extension mechanisms while applications receive only a simplified public surface, reproducing framework-quality integrations becomes difficult.

Kora exposes enough of its composition model that application and platform teams can build integrations in the same architectural language:

```text
module
component
config
lifecycle
telemetry
probe
graph
```

That symmetry lowers the learning curve.

---

# Ecosystem Is Not Only What Ships in the Box

This gives us a broader definition.

A framework ecosystem consists of at least three layers.

### Layer 1: built-in framework modules

```text
HTTP
JDBC
Kafka
gRPC
S3
resilience
cache
validation
telemetry
...
```

### Layer 2: native Java ecosystem

```text
vendor SDKs
database drivers
messaging clients
cloud SDKs
libraries
protocol implementations
```

### Layer 3: organization-specific modules

```text
internal clients
platform libraries
security
company telemetry
shared infrastructure
```

A framework is powerful when those layers compose easily.

Kora does not have to duplicate Layer 2 in order to benefit from it.

That is the larger meaning of thin abstractions.

---

# The Most Important Ecosystem Property May Be Escape Velocity

There is a useful metaphor here.

Some frameworks have a large gravitational field. It is easy to enter because everything has a starter, but difficult to leave framework abstractions once inside.

Other frameworks provide less initial coverage but make boundaries easier to cross.

For long-lived systems, the ability to cross those boundaries matters.

Teams need to:

- upgrade native libraries;
- replace clients;
- adopt new infrastructure;
- migrate vendors;
- customize defaults;
- debug protocol-specific failures;
- use advanced native features.

A thin integration gives the application escape velocity.

It can move between framework and native library without a large translation layer.

---

# Maintenance Cost Is Where the Model Pays Off

The first version of an integration is only part of the cost.

The larger cost often appears over years.

Suppose NATS changes its API.

With a thick adapter:

```text
NATS changes
     ↓
adapter maintainers update wrapper
     ↓
framework releases new adapter
     ↓
application upgrades adapter
     ↓
application adapts to wrapper changes
```

With a thin module:

```text
NATS changes
     ↓
application upgrades dependency
     ↓
small factory mapping changes if needed
```

The difference can be significant.

This is particularly valuable for less popular integrations where community adapters may lag behind vendor releases.

---

# The 51st Integration Is the Real Test

The quality of a framework's first 50 integrations tells you how much work its maintainers have already done.

The difficulty of the 51st tells you how much work *you* will have to do when the roadmap diverges from theirs.

That is why the following statement is more than rhetoric:

> **A framework with 500 integrations that are difficult to understand is not necessarily more extensible than a framework with 50 integrations where the 51st can be written in a few straightforward classes.**

A mature framework should optimize both sides.

Ship useful integrations.

And make the missing one unsurprising to build.

---

# A Small Ecosystem Can Become a Local Ecosystem Quickly

Teams should also distinguish public ecosystem size from local ecosystem size.

A company adopting Kora can create its own curated integration layer.

After a year, its internal platform may include:

```text
company-kora-postgres
company-kora-nats
company-kora-clickhouse
company-kora-auth
company-kora-featureflags
company-kora-object-storage
company-kora-secrets
company-kora-audit
```

These modules encode company policy rather than generic framework policy.

That is often more valuable than having a public starter for every technology because internal modules can standardize:

- naming;
- telemetry tags;
- credentials;
- timeout defaults;
- TLS;
- readiness policy;
- security;
- deployment assumptions.

Kora's simple module model makes that kind of platform layer practical.

---

# Why This Can Be Better Than Generic Starters

A generic starter has to satisfy many environments.

It therefore accumulates options.

A company module can be opinionated.

For example:

```text
All NATS clients:
- use company TLS
- use standard connection names
- export standard metrics
- use approved reconnect policy
- expose no readiness dependency by default
```

The reusable module can encode those choices in ordinary factory code.

That is ecosystem construction tailored to the organization.

---

# Compile-Time DI Makes Custom Integration Errors Cheap

There is another benefit to using custom modules in Kora.

If the integration is wired incorrectly, graph validation happens during compilation.

Suppose `NatsPublisher` requires `NatsTelemetry`, but no telemetry implementation exists.

The application graph fails to build.

Suppose two untagged `Connection` components exist.

The graph reports ambiguity.

Suppose a module factory requires a config mapper that cannot be generated.

The compiler identifies the missing dependency.

This makes custom integration development less risky because structural mistakes are caught early.

The framework does not require the application to start before revealing whether the integration is internally coherent.

---

# Generated Graph Code Makes the Integration Explainable

When debugging a custom module, generated code is useful.

You can inspect how the graph constructs:

```text
NatsConfig
Options
Connection
NatsTelemetry
NatsPublisher
NatsReadinessProbe
```

This is an underrated extensibility feature.

Opaque runtime extension systems make custom integrations harder because the wiring lives inside framework machinery.

Readable generated graph code turns the application assembly into something inspectable.

That matters for humans.

It matters even more for AI coding agents.

---

# Extensibility and AI-Native Design Reinforce Each Other

An AI agent asked to integrate a new SDK into Kora can follow a relatively mechanical process:

```text
read SDK docs
↓
identify client builder
↓
define typed config
↓
create Kora module factory
↓
attach lifecycle
↓
add telemetry/probe if required
↓
compile
↓
fix graph errors
```

There is little hidden state.

The agent can inspect generated sources if necessary.

The native SDK documentation remains relevant.

This is another reason a modest official ecosystem is less limiting than it once was. The cost of writing small glue code has fallen, while the cost of understanding opaque framework behavior has not fallen nearly as much.

In an AI-assisted environment, reviewability becomes more valuable than raw integration count.

---

# Review Is the New Bottleneck

As code generation becomes cheaper—whether generated by annotation processors or AI agents—the bottleneck moves toward review.

A custom integration that consists of six transparent classes is reviewable.

A framework plugin involving classpath scanning, dynamic conditions and runtime proxies is harder to review, even if an AI can produce it quickly.

Kora's extension model aligns well with this shift.

The ideal integration is not merely easy to generate.

It is easy to verify.

That means:

```text
small
typed
local
explicit
native
testable
```

Those properties matter more as software production accelerates.

---

# You Do Not Need a Starter for Everything

The phrase "there is no starter" sounds frightening only if the framework makes ordinary library construction difficult.

For many Java technologies, a starter is primarily a convenience bundle around:

```text
new Client(config)
```

plus lifecycle and observability.

If the framework already makes those concerns easy to compose, absence of a starter becomes an inconvenience rather than a blocker.

This does not apply equally to every technology.

But it applies to far more technologies than framework ecosystems sometimes imply.

---

# A More Useful Framework Comparison

Instead of comparing ecosystems only by module count, evaluate this matrix:

| Question | Why It Matters |
| --- | --- |
| How many integrations already exist? | Immediate coverage |
| Can I use the native Java client directly? | Escape hatch |
| How much framework-specific API is added? | Learning cost |
| How do I bind configuration? | Integration boilerplate |
| How do I manage lifecycle? | Production safety |
| How do I add readiness? | Operational integration |
| How do I add metrics/tracing? | Observability |
| Can I replace defaults? | Customization |
| Can I have multiple instances? | Real-world topology |
| Can I test a graph slice? | Development cost |
| Are wiring errors compile-time? | Feedback quality |
| Can I package this as an internal module? | Platform reuse |
| Do I need framework internals? | Extension barrier |

This gives a much more meaningful picture than "Framework A has 430 starters, Framework B has 70."

---

# Where Kora Still Has Work to Do

A defense of Kora should not pretend ecosystem size is irrelevant.

A smaller ecosystem means:

- fewer copy-paste examples for unusual technologies;
- fewer ready-made telemetry conventions;
- fewer community-tested adapters;
- fewer integrations maintained by specialists;
- more cases where teams must write their own glue;
- fewer Stack Overflow answers and blog posts for edge cases.

For complex technologies, that is real engineering cost.

Kora's answer is not to make that cost disappear.

Its answer is to make the glue as cheap and unsurprising as possible.

That is a different strategy.

Whether it is the right strategy depends on the team.

A team that wants every possible technology pre-integrated may prefer a larger ecosystem.

A team that values control, native APIs, compile-time clarity and the ability to build small local integrations may find Kora's model more attractive.

---

# The Best Integration Is Sometimes No Integration

There is a final provocative point.

Sometimes the correct framework integration for a Java library is simply:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface VendorModule {

        default VendorClient vendorClient(VendorConfig config) {
            return VendorClient.builder()
                .endpoint(config.endpoint())
                .build();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface VendorModule {

        fun vendorClient(config: VendorConfig): VendorClient {
            return VendorClient.builder()
                .endpoint(config.endpoint())
                .build()
        }
    }
    ```

That may be enough.

If the client is thread-safe, manages no unusual lifecycle, exports its own OpenTelemetry signals and does not affect readiness, adding more framework code would make the system worse.

Framework maturity includes knowing when not to wrap.

Kora's thin-abstraction philosophy makes that answer socially acceptable.

---

# Conclusion: The Ecosystem Is What You Can Add Safely

A framework ecosystem is often presented as a shelf of ready-made parts.

That shelf matters. Kora benefits from every official integration it ships, and there will always be cases where a mature built-in module saves substantial engineering effort.

But the shelf is not the whole workshop.

Sooner or later a production system needs something outside the catalog. A new database appears. A team adopts NATS. A vendor ships a new SDK. An internal platform exposes a proprietary client. A cloud service has no official framework module. At that moment, the real quality of the framework is revealed by what happens next.

Does the team have to understand hidden runtime extension points?

Does it need to reproduce a complex starter architecture?

Does it need to create framework-specific mirrors of the native API?

Does it have to wait for official support?

Or can it do this?

```text
New library
   ↓
Config
   ↓
Client factory
   ↓
Lifecycle
   ↓
Kora Module
   ↓
Telemetry
   ↓
Probes
   ↓
Injection into application
```

Kora is deliberately designed so that the second path is often enough.

Its modules are ordinary composition units. Configuration is typed. Lifecycle is explicit. Readiness and liveness are ordinary component contracts. Telemetry can be layered around native operations. Default framework components can be replaced. Tags and factory modules handle multiple instances. Compile-time graph validation catches structural mistakes early. Generated code remains inspectable. And when ordinary factories are no longer enough, the framework also exposes a deeper compile-time extension mechanism for integrations that genuinely benefit from generated implementations.

Most importantly, thin abstractions preserve the ecosystem of the underlying technology.

A developer who knows JDBC still knows JDBC.

A developer who knows Kafka still understands Kafka.

A developer adding NATS can continue reading NATS documentation.

A team adopting Elasticsearch, ClickHouse, MinIO or a new cloud SDK does not necessarily have to wait for those technologies to be translated into a new framework dialect.

That changes the meaning of ecosystem size.

The relevant comparison is no longer only:

```text
How many integrations ship today?
```

It becomes:

```text
How expensive is tomorrow's missing integration?
```

And that leads to the more durable principle:

> **The real question is not how many integrations a framework already ships with, but how expensive it is to add the one you actually need.**

A framework with hundreds of integrations can be valuable because someone has already done the work.

But extensibility is something different.

> **A framework with 500 integrations that are difficult to understand is not necessarily more extensible than a framework with 50 integrations where the 51st can be written in a few straightforward classes.**

Kora's smaller ecosystem should therefore be evaluated together with the architecture that surrounds it. The framework does not need to predict every technology a team will ever use if unknown technologies can enter the application through a small, typed and transparent boundary.

That is the ecosystem Kora is really offering.

Not only the integrations that ship in the box.

The ecosystem you can build.
