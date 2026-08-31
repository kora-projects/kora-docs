---
description: "Explains Kora SLF4J logging: obtaining a Logger, the logging.levels configuration and its runtime refresh, per-component telemetry logging, the Logback module with ConsoleTextRecordEncoder and KoraAsyncAppender, structured logs and the scoped MDC. Use when working with LoggingModule, LogbackModule, LoggingConfig, LoggingLevelApplier, StructuredArgument, MDC, KoraMdcConverter, telemetry.logging.enabled."
agent:
  use_when: "Use this file for Kora docs or implementation questions about SLF4J logging setup, logging.levels configuration and runtime refresh, per-component telemetry logging, Logback integration, alternative SLF4J implementations, structured log fields and MDC; key triggers include LoggingModule, LogbackModule, LoggingConfig, LoggingLevelApplier, LoggingLevelRefresher, ConsoleTextRecordEncoder, KoraAsyncAppender, KoraMdcConverter, KoraLoggingMarkerConverter, StructuredArgument, MDC, telemetry.logging.enabled."
---

Kora uses [`slf4j-api`](https://www.slf4j.org/) as the common logging facade across the framework.
`SLF4J` separates application code from the concrete logging implementation, and Kora expects [`Logback`](#logback) to be used as the main implementation.

The logging module is responsible for obtaining a `Logger` through the standard `SLF4J` factory, managing logging levels through Kora configuration, and passing structured data to log records.
Structured data can be added through `StructuredArgument`, `Marker`, `SLF4J` key-value pairs, and `MDC` so that it is emitted together with the regular text message.

For a step-by-step walkthrough before the reference details, see [Observability](../guides/observability.md).

## Usage { #usage }

A `Logger` is created through the [`SLF4J`](https://www.slf4j.org/manual.html#hello_world) factory:

===! ":fontawesome-brands-java: `Java`"

    ```java
    Logger logger = LoggerFactory.getLogger(SomeService.class);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val logger = LoggerFactory.getLogger(SomeService::class.java)
    ```

## Configuration { #configuration }

Logging levels are described by the `LoggingConfig` interface, which is mapped from the `logging` section of the [configuration file](config.md).
The section has a single `levels` map that assigns a level to `ROOT`, to a package, or to a specific logger:

===! ":material-code-json: `Hocon`"

    ```javascript
    logging {
      levels {  //(1)!
        "ROOT" = "WARN"
        "io.koraframework" = "INFO"
        "io.koraframework.http.server.common.HttpServer.request" = "DEBUG"
        "io.koraframework.example" = "INFO"
      }
    }
    ```

    1. Logging levels by logger name (default: empty map, optional).

=== ":simple-yaml: `YAML`"

    ```yaml
    logging:
      levels: #(1)!
        "ROOT": "WARN"
        "io.koraframework": "INFO"
        "io.koraframework.http.server.common.HttpServer.request": "DEBUG"
        "io.koraframework.example": "INFO"
    ```

    1. Logging levels by logger name (default: empty map, optional).

`levels` is a flat map of logger name to level: the key is the full logger name and the value is a plain string.

!!! warning "Quote logger names in HOCON"

    `HOCON` treats an unquoted dotted key as a path and expands it into nested objects, so `io.koraframework = "INFO"` becomes the object `{ io { koraframework = "INFO" } }`.
    A nested object is not a level string, and the configuration mapping fails with an unexpected value type.
    Always write logger names in quotes — `"io.koraframework" = "INFO"`.
    In `YAML` a dotted key is already a literal key, but quoting it keeps both formats identical.

!!! note

    When the `logging` section is absent, `levels` is an empty map and Kora applies no levels of its own.
    The [Logback](#logback) implementation, however, resets all loggers on every (re)apply: `ROOT` is normalized to `INFO` and every other per-logger level is cleared so that it inherits from its parent, after which the configured levels are applied on top.
    As a result, the `<root level="...">` value from `logback.xml` is effectively replaced by `INFO` at startup unless a `ROOT` level is set in the configuration.

### Runtime level refresh { #levels-refresh }

Configured levels are applied by the `LoggingLevelRefresher` — a root component that on startup resets all loggers and applies the levels from the `logging` section through the `LoggingLevelApplier`.
It re-runs on every configuration refresh, so when the [Config Watcher](config.md#config-watcher) is active, changing a level in the configuration file takes effect at runtime without restarting the application.

Because the refresher always resets first, a level removed from the configuration returns to its inherited value rather than sticking at its previous setting.

### Modules { #module }

Request and response logging of individual Kora components is a telemetry signal of those components and is switched on in their own configuration section through `telemetry.logging.enabled`.
This is a different knob from the logger levels above: `telemetry.logging.enabled` decides whether a component produces log records at all, while `logging.levels` decides how detailed those records are and whether they pass the level filter.

By default, telemetry logging is **disabled for every component**, so the configuration below shows how to enable it for most of them:

===! ":material-code-json: `Hocon`"

    ```javascript
    jdbc.telemetry.logging.enabled = true //(1)!
    cassandra.telemetry.logging.enabled = true //(2)!
    grpcServer.telemetry.logging.enabled = true //(3)!
    httpServer.telemetry.logging.enabled = true //(4)!
    scheduling.telemetry.logging.enabled = true //(5)!
    resilient.telemetry.circuitBreaker.logging.enabled = true //(6)!
    grpcClient.SomeGrpcServiceName.telemetry.logging.enabled = true //(7)!
    soapClient.SomeSoapServiceName.telemetry.logging.enabled = true //(8)!
    SomePathToConfigHttpClient.telemetry.logging.enabled = true //(9)!
    kafka.consumer.SomeConsumerName.telemetry.logging.enabled = true //(10)!
    kafka.producer.SomePublisherName.telemetry.logging.enabled = true //(11)!
    ```

    1. Logging for [JDBC](database-jdbc.md) database queries (default: `false`).
    2. Logging for [Cassandra](database-cassandra.md) database queries (default: `false`).
    3. Logging for [gRPC server](grpc-server.md) requests (default: `false`).
    4. Logging for [HTTP server](http-server.md) requests (default: `false`).
    5. Logging for [scheduler](scheduling.md) executions (default: `false`).
    6. Logging for [circuit breaker](resilient.md) state changes; `retry`, `timeout`, `fallback` and `rateLimiter` have their own subsections (default: `false`).
    7. Logging for [gRPC client](grpc-client.md) requests, specified for a particular service (default: `false`).
    8. Logging for [SOAP client](soap-client.md) requests, specified for a particular service (default: `false`).
    9. Logging for [HTTP client](http-client.md) requests, specified for a particular client at its own configuration path (default: `false`).
    10. Logging for a Kafka [consumer](kafka.md#config-consumer), specified for a particular consumer (default: `false`).
    11. Logging for a Kafka [producer](kafka.md#config-producer), specified for a particular producer (default: `false`).

=== ":simple-yaml: `YAML`"

    ```yaml
    jdbc.telemetry.logging.enabled: true #(1)!
    cassandra.telemetry.logging.enabled: true #(2)!
    grpcServer.telemetry.logging.enabled: true #(3)!
    httpServer.telemetry.logging.enabled: true #(4)!
    scheduling.telemetry.logging.enabled: true #(5)!
    resilient.telemetry.circuitBreaker.logging.enabled: true #(6)!
    grpcClient.SomeGrpcServiceName.telemetry.logging.enabled: true #(7)!
    soapClient.SomeSoapServiceName.telemetry.logging.enabled: true #(8)!
    SomePathToConfigHttpClient.telemetry.logging.enabled: true #(9)!
    kafka.consumer.SomeConsumerName.telemetry.logging.enabled: true #(10)!
    kafka.producer.SomePublisherName.telemetry.logging.enabled: true #(11)!
    ```

    1. Logging for [JDBC](database-jdbc.md) database queries (default: `false`).
    2. Logging for [Cassandra](database-cassandra.md) database queries (default: `false`).
    3. Logging for [gRPC server](grpc-server.md) requests (default: `false`).
    4. Logging for [HTTP server](http-server.md) requests (default: `false`).
    5. Logging for [scheduler](scheduling.md) executions (default: `false`).
    6. Logging for [circuit breaker](resilient.md) state changes; `retry`, `timeout`, `fallback` and `rateLimiter` have their own subsections (default: `false`).
    7. Logging for [gRPC client](grpc-client.md) requests, specified for a particular service (default: `false`).
    8. Logging for [SOAP client](soap-client.md) requests, specified for a particular service (default: `false`).
    9. Logging for [HTTP client](http-client.md) requests, specified for a particular client at its own configuration path (default: `false`).
    10. Logging for a Kafka [consumer](kafka.md#config-consumer), specified for a particular consumer (default: `false`).
    11. Logging for a Kafka [producer](kafka.md#config-producer), specified for a particular producer (default: `false`).

Components write their telemetry through dedicated loggers named after the component, and the amount of detail depends on the level of that logger.
The [HTTP server](http-server.md) uses `io.koraframework.http.server.common.HttpServer.request` and `...HttpServer.response`: at `INFO` it logs the operation, at `DEBUG` it adds query parameters and headers, at `TRACE` it adds the body.
A database pool uses `io.koraframework.database.<poolName>.query`, and it starts logging at `DEBUG` and adds the `SQL` text at `TRACE`.

!!! tip "Nothing is logged even though telemetry is enabled"

    Both conditions must hold at once: `telemetry.logging.enabled = true` for the component, and a `levels` entry low enough for that component's logger.
    A database pool that logs only at `DEBUG` stays silent under a `ROOT` level of `INFO`.

Logging parameters for specific modules are described in the documentation for those modules, for example [HTTP server](http-server.md), [HTTP client](http-client.md), [gRPC client](grpc-client.md).
Some of them extend the logging section with their own keys, such as header and query masking on the HTTP server.

## Logback { #logback }

The module provides a logging implementation based on [`Logback`](https://www.baeldung.com/logback), adds support for structured logs, and allows logging levels to be managed through the [configuration file](config.md).

### Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:logging-logback"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends LogbackModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:logging-logback")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : LogbackModule
    ```

`LogbackModule` extends `LoggingModule`, so a separate `logging-common` dependency is not required.

### Configuration { #configuration-2 }

`Logback` is configured through `logback.xml`, while Kora configuration usually contains only logging levels.
Example `logback.xml`:

```xml
<configuration debug="false">
    <statusListener class="ch.qos.logback.core.status.NopStatusListener"/>

    <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
        <encoder class="io.koraframework.logging.logback.ConsoleTextRecordEncoder"/>
    </appender>

    <appender name="ASYNC" class="io.koraframework.logging.logback.KoraAsyncAppender">
        <appender-ref ref="STDOUT"/>
    </appender>

    <root level="WARN">
        <appender-ref ref="ASYNC"/>
    </root>
</configuration>
```

`KoraAsyncAppender` does two jobs at once.
It hands the record to a worker thread for asynchronous writing, and before doing so it captures everything that lives in the current scope and would otherwise be lost on the way: the Kora [`MDC`](#mdc) values and the current `OpenTelemetry` span.
Both are stored in a `KoraLoggingEvent`, which is the event type the Kora encoder and converters understand.

!!! warning "KoraAsyncAppender is what makes Kora context visible"

    Kora `MDC` values, `traceId` and `spanId` are read from `KoraLoggingEvent`.
    An appender chain without `KoraAsyncAppender` produces plain `Logback` events, and those fields simply do not appear in the output.
    Wrap the real appender in `KoraAsyncAppender` even when asynchronous writing is not the goal.

### Log record format { #record-format }

`ConsoleTextRecordEncoder` is the only encoder shipped by the module.
It produces a text line with structured fields appended, not a single `JSON` document, and is composed as follows:

- `yyyy-MM-dd HH:mm:ss.SSS` timestamp in `UTC`, the level, the thread name in square brackets, and the logger name;
- `traceId=... spanId=...` when the record was produced inside a traced operation;
- the Kora `MDC` entries as `key=<json value>`;
- the `SLF4J` `MDC` entries as plain `key=value`;
- the formatted message;
- one tab-indented `fieldName={json}` line per structured field taken from markers, message arguments, and `SLF4J` key-value pairs;
- the stack trace, when the record carries a `Throwable`.

```text
2026-07-02 10:15:30.123 INFO  [kora-undertow-1] io.koraframework.example.SomeService - traceId=4bf92f3577b34da6a3ce929d0e0e4736 spanId=00f067aa0ba902b7 userId=42 user logged in
	role="admin"
```

The logger name is written in full and is shortened package by package only when it exceeds 100 characters.

### Custom pattern { #custom-pattern }

Instead of `ConsoleTextRecordEncoder`, a standard `PatternLayoutEncoder` can be used together with the converters that render Kora structured data.
`KoraMdcConverter` renders the Kora context `MDC` and `KoraLoggingMarkerConverter` renders a `StructuredArgument` marker; register them as conversion words and reference them in the pattern:

```xml
<configuration>
    <conversionRule conversionWord="koraMdc" converterClass="io.koraframework.logging.logback.KoraMdcConverter"/>
    <conversionRule conversionWord="koraMarker" converterClass="io.koraframework.logging.logback.KoraLoggingMarkerConverter"/>

    <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
        <encoder class="ch.qos.logback.classic.encoder.PatternLayoutEncoder">
            <pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} %-5level [%thread] %logger - %koraMdc%msg %koraMarker%n</pattern>
        </encoder>
    </appender>

    <appender name="ASYNC" class="io.koraframework.logging.logback.KoraAsyncAppender">
        <appender-ref ref="STDOUT"/>
    </appender>

    <root level="INFO">
        <appender-ref ref="ASYNC"/>
    </root>
</configuration>
```

`KoraMdcConverter` prefers the `MDC` snapshot carried by `KoraLoggingEvent` and only falls back to reading the currently bound `MDC` directly.
That fallback is defined only inside an [`MDC` scope](#mdc-scope), which is another reason to keep `KoraAsyncAppender` in front of the pattern appender: with it, records emitted during graph initialization or from a shutdown hook are encoded safely.

!!! note "A log line is not a startup contract"

    The wording of Kora's own startup messages is not part of the public contract and does change between versions, and an asynchronous appender may drop a record under load.
    Do not wait for a log line to decide that a service is up — poll the readiness [probe](probes.md) at `/system/readiness` instead.

## Other Implementation { #other-implementation }

Kora uses [`slf4j-api`](https://www.slf4j.org/) as the logging facade, so any compatible implementation can be connected.
The base module adds common components for structured logs and logging-level management through the [configuration file](config.md).

### Dependency { #dependency-2 }

The common logging module must be connected:

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:logging-common"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends LoggingModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:logging-common")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : LoggingModule
    ```

### Usage { #usage-2 }

`LoggingModule` provides the `LoggingConfig` component, the `LoggingLevelRefresher` root component, and an `ILoggerFactory` component obtained from `LoggerFactory.getILoggerFactory()`.
It does not provide a `LoggingLevelApplier`, so a custom implementation must supply one:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeLoggingLevelApplier implements LoggingLevelApplier {

        @Override
        public void apply(String logName, String logLevel) { //(1)!
            //...
        }

        @Override
        public void reset() { //(2)!
            //...
        }
    }
    ```

    1. Applies a level to the logger with the given name; the level comes from the `logging.levels` map as written in the configuration.
    2. Returns all loggers to their initial state; called before every apply pass, including on configuration refresh.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeLoggingLevelApplier : LoggingLevelApplier {

        override fun apply(logName: String, logLevel: String) { //(1)!
            //...
        }

        override fun reset() { //(2)!
            //...
        }
    }
    ```

    1. Applies a level to the logger with the given name; the level comes from the `logging.levels` map as written in the configuration.
    2. Returns all loggers to their initial state; called before every apply pass, including on configuration refresh.

If the application uses structured data, the custom implementation must also render `StructuredArgument`, `StructuredArgumentWriter`, and the Kora `MDC`, the way [`ConsoleTextRecordEncoder`](#record-format) does for `Logback`.

## Structured Logs { #structured-logs }

Structured logs make it possible to pass not only text but also named fields to a log record.
These fields are convenient for log collection tools and can be used for search, filtering, and views.

Structured data can be passed to a log record in three ways:

- through `Marker`;
- through a message parameter;
- through an `SLF4J` key-value pair.

All three are built from `io.koraframework.logging.common.arg.StructuredArgument`, and the `marker` and `arg` factory methods accept `String`, `Integer`, `Long`, `Boolean`, and `Map<String, String>` values.
For any other type, pass a `JsonWriter<T>` or a `StructuredArgumentWriter`.

### Marker { #marker }

`Marker` adds a structured field to a log record and does not take a parameter slot in the text message:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var logger = LoggerFactory.getLogger(getClass());
    var marker = StructuredArgument.marker("key", "value");
    logger.info(marker, "message");
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val logger = LoggerFactory.getLogger(javaClass)
    val marker = StructuredArgument.marker("key", "value")
    logger.info(marker, "message")
    ```

### Parameter { #parameter }

A message parameter adds a structured field through the regular `SLF4J` argument array:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var logger = LoggerFactory.getLogger(getClass());
    var parameter = StructuredArgument.arg("key", "value");
    logger.info("message", parameter);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val logger = LoggerFactory.getLogger(javaClass)
    val parameter = StructuredArgument.arg("key", "value")
    logger.info("message", parameter)
    ```

### Key-value pair { #key-value-pair }

The `SLF4J` fluent builder attaches a named value without touching the message or the marker list.
`StructuredArgument.value` wraps a writer into a `StructuredArgumentWriter`, which the Kora encoder renders as a structured field — this is the form Kora's own telemetry uses:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var logger = LoggerFactory.getLogger(getClass());
    logger.atInfo()
        .addKeyValue("user", StructuredArgument.value(gen -> {
            gen.writeStartObject();
            gen.writeStringProperty("id", "42");
            gen.writeStringProperty("role", "admin");
            gen.writeEndObject();
        }))
        .log("user logged in");
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val logger = LoggerFactory.getLogger(javaClass)
    logger.atInfo()
        .addKeyValue("user", StructuredArgument.value { gen ->
            gen.writeStartObject()
            gen.writeStringProperty("id", "42")
            gen.writeStringProperty("role", "admin")
            gen.writeEndObject()
        })
        .log("user logged in")
    ```

### Complex object { #complex-object }

For values that are not a `String`, number, `Boolean`, or `Map<String, String>`, pass a `JsonWriter<T>` (the same [`@Json`](json.md) writer generated for the type) or a raw `StructuredArgumentWriter` lambda that writes the field value directly to the `JsonGenerator`.
Both `arg` and `marker` provide these overloads:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var logger = LoggerFactory.getLogger(getClass());
    var parameter = StructuredArgument.arg("user", gen -> {
        gen.writeStartObject();
        gen.writeStringProperty("id", "42");
        gen.writeStringProperty("role", "admin");
        gen.writeEndObject();
    });
    logger.info("user logged in", parameter);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val logger = LoggerFactory.getLogger(javaClass)
    val parameter = StructuredArgument.arg("user") { gen ->
        gen.writeStartObject()
        gen.writeStringProperty("id", "42")
        gen.writeStringProperty("role", "admin")
        gen.writeEndObject()
    }
    logger.info("user logged in", parameter)
    ```

The `JsonGenerator` here is the `Jackson` generator used across Kora, so object fields are written with `writeStringProperty` / `writeNumberProperty` and names with `writeName`.
Writing does not declare a checked exception, so no `try`/`catch` is required.

The `JsonWriter<T>` overload takes a value and its writer, and writes `null` for a `null` value:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private static final Logger logger = LoggerFactory.getLogger(SomeService.class);

        private final JsonWriter<User> userWriter;

        public SomeService(JsonWriter<User> userWriter) { //(1)!
            this.userWriter = userWriter;
        }

        public void handle(User user) {
            logger.info("user logged in", StructuredArgument.arg("user", user, userWriter));
        }
    }
    ```

    1. The writer generated for a [`@Json`](json.md) annotated type is an ordinary graph component and is injected as a dependency.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(
        private val userWriter: JsonWriter<User>, //(1)!
    ) {

        fun handle(user: User) {
            logger.info("user logged in", StructuredArgument.arg("user", user, userWriter))
        }

        companion object {
            private val logger = LoggerFactory.getLogger(SomeService::class.java)
        }
    }
    ```

    1. The writer generated for a [`@Json`](json.md) annotated type is an ordinary graph component and is injected as a dependency.

### Argument mapper { #argument-mapper }

`StructuredArgumentMapper<T>` is the contract that turns a value of type `T` into a structured field.
`LoggingModule` supplies two default implementations built on top of an existing `JsonWriter<T>`:

- `JsonStructuredArgumentMapper` — writes the value as `JSON`;
- `MaskedStructuredArgumentMapper` — writes the value as `JSON` with the fields described by `MaskingRules` replaced.

Both are `@DefaultComponent` declarations, so providing your own `StructuredArgumentMapper<T>` component for a type replaces the default one for that type.
These mappers are what the [`@Log`](logging-aspect.md) aspect uses to serialize method arguments and results, and masking rules are described there.

### MDC { #mdc }

Structured data can be attached to all records within the current scope using the `io.koraframework.logging.common.MDC` class.
The value will be added to every log record until it is removed from `MDC`:

!!! warning "Import"

    Use `io.koraframework.logging.common.MDC`, not `org.slf4j.MDC`.
    The `SLF4J` `MDC` is a thread-local of strings: Kora clears it at the start of every HTTP request, it does not follow work handed to another thread, and its values are rendered as plain text.
    The Kora `MDC` lives in the request scope, is carried across Kora's own thread hand-offs, and its values are rendered as typed `JSON`.
    For a declarative alternative see [`@Mdc`](logging-aspect.md).

===! ":fontawesome-brands-java: `Java`"

    ```java
    MDC.put("key", "value");
    try {
        logger.info("message");
    } finally {
        MDC.remove("key");
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    MDC.put("key", "value")
    try {
        logger.info("message")
    } finally {
        MDC.remove("key")
    }
    ```

`put` accepts `String`, `Integer`, `Long`, and `Boolean` values, as well as a raw `StructuredArgumentWriter` for arbitrary `JSON`; typed values are rendered as their `JSON` type rather than as text, and a `null` value is rendered as `JSON` `null`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    MDC.put("userId", 42); //(1)!
    logger.info("user resolved");
    ```

    1. Rendered as a JSON number (`userId=42`), not as a string.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    MDC.put("userId", 42) //(1)!
    logger.info("user resolved")
    ```

    1. Rendered as a JSON number (`userId=42`), not as a string.

### MDC scope { #mdc-scope }

The `MDC` is not a global thread-local: it is bound to a scope, and `MDC.put` / `MDC.remove` / `MDC.get` work only inside one.
Kora opens that scope at every entry point it owns — an [HTTP server](http-server.md) request, a [gRPC server](grpc-server.md) call, a [Kafka](kafka.md) record, a [scheduled](scheduling.md) execution — and each scope starts empty, so values never leak from one request into the next.
When Kora itself hands work to another thread it re-binds the `MDC` explicitly; a Kafka listener, for example, gets a `fork()` of the poll-level `MDC` per record, so per-record values stay isolated.

Code that runs outside those entry points — graph initialization, a shutdown hook, a plain `ExecutorService` task, a unit test — has no `MDC` bound, and calling `MDC.put` there fails.
Open a scope explicitly for such code:

===! ":fontawesome-brands-java: `Java`"

    ```java
    ScopedValue.where(MDC.VALUE, new MDC()).run(() -> { //(1)!
        MDC.put("jobId", jobId);
        logger.info("job started");
    });
    ```

    1. `MDC.VALUE` is the `ScopedValue` holding the current `MDC`; the binding is visible only on this thread inside this block.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    ScopedValue.where(MDC.VALUE, MDC()).call<Unit, RuntimeException> { //(1)!
        MDC.put("jobId", jobId)
        logger.info("job started")
    }
    ```

    1. `MDC.VALUE` is the `ScopedValue` holding the current `MDC`. `call` is used rather than `run`, because `run` would resolve to the `Kotlin` standard library extension instead of the carrier method.

This scoping is also why [`KoraAsyncAppender`](#configuration-2) copies the `MDC` at append time: the asynchronous worker thread has no binding of its own, and the copy stored in `KoraLoggingEvent` is what the encoder later renders.
