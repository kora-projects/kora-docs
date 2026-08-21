---
description: "Explains Kora SLF4J logging setup, module log configuration, Logback integration, alternative implementations, structured logs, markers, parameters, and MDC. Use when working with LoggingModule, LogbackModule, LoggerFactory, StructuredArgument, Marker, MDC, loggingConfig."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora SLF4J logging setup, module log configuration, Logback integration, alternative implementations, structured logs, markers, parameters, and MDC; key triggers include LoggingModule, LogbackModule, LoggerFactory, StructuredArgument, Marker, MDC, loggingConfig."
---

Kora uses [`slf4j-api`](https://www.slf4j.org/) as the common logging facade across the framework.
`SLF4J` separates application code from the concrete logging implementation, and Kora expects [`Logback`](#logback) to be used as the main implementation.

The logging module is responsible for obtaining a `Logger` through the standard `SLF4J` factory, managing logging levels through Kora configuration, and passing structured data to log records.
Structured data can be added through `StructuredArgument`, `Marker`, and `MDC` so that it is emitted together with the regular text message.

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

Logging levels are described by the `LoggingConfig` class.
The configuration sets a level for `ROOT`, a package, or a specific class:

===! ":material-code-json: `Hocon`"

    ```javascript
    logging {
      levels {  //(1)!
        "ROOT": "WARN"
        "ru.tinkoff.kora": "INFO"
        "ru.tinkoff.kora.http.server.common.telemetry": "INFO"
        "ru.tinkoff.kora.http.client.common.telemetry.DefaultHttpClientTelemetry": "INFO"
      }
    }
    ```

    1. Logging levels for `ROOT`, classes, and packages (default: not specified, optional).

=== ":simple-yaml: `YAML`"

    ```yaml
    logging:
      levels: #(1)!
        ROOT: "WARN"
        ru.tinkoff.kora: "INFO"
        ru.tinkoff.kora.http.server.common.telemetry: "INFO"
        ru.tinkoff.kora.http.client.common.telemetry.DefaultHttpClientTelemetry: "INFO"
    ```

    1. Logging levels for `ROOT`, classes, and packages (default: not specified, optional).

The section key may be written as either `levels` or `level` — both are accepted as aliases.
Logger names may be listed as flat dotted strings (as above) or as a nested object; Kora flattens nested objects into dotted logger names.
The `ROOT` logger name is matched case-insensitively, so `ROOT` and `root` are equivalent.
For example, the shipped [examples](https://github.com/kora-projects/kora-examples) use the singular `level` alias with a nested lowercase `root`:

```javascript
logging.level {
  "root": "WARN"
  "ru.tinkoff.kora": "INFO"
  "ru.tinkoff.kora.example": "INFO"
}
```

!!! note

    When the `logging` section is absent, Kora applies no level map of its own.
    The [Logback](#logback) implementation, however, resets all loggers on every (re)apply: `ROOT` is normalized to `INFO` and every other per-logger level is cleared so that it inherits from its parent, after which the configured levels are applied on top.
    As a result, the `<root level="...">` value from `logback.xml` is effectively replaced by `INFO` at startup unless a `ROOT` level is set in the configuration.

### Runtime level refresh { #levels-refresh }

Configured levels are applied by the `LoggingLevelRefresher` — a root component that on startup resets all loggers and re-applies the levels from the `logging` section through the `LoggingLevelApplier`.
It re-runs on every configuration refresh, so when the [Config Watcher](config.md#config-watcher) is active, changing a level in the configuration file takes effect at runtime without restarting the application.

Logging parameters for specific modules are described in the documentation for those modules, for example [HTTP server](http-server.md), [HTTP client](http-client.md), [gRPC client](grpc-client.md).

### Modules { #module }

Logging for specific modules is enabled and disabled in the configuration of those modules through `telemetry.logging.enabled`.

By default, logging is **disabled for all modules**, so the configuration below shows how to enable logging for most modules:

===! ":material-code-json: `Hocon`"

    ```javascript
    db.telemetry.logging.enabled = true //(1)!
    cassandra.telemetry.logging.enabled = true //(2)!
    grpcServer.telemetry.logging.enabled = true //(3)!
    httpServer.telemetry.logging.enabled = true //(4)!
    scheduling.telemetry.logging.enabled = true //(5)!
    grpcClient.SomeGrpcServiceName.telemetry.logging.enabled = true //(6)!
    soapClient.SomeSoapServiceName.telemetry.logging.enabled = true //(7)!
    SomePathToConfigHttpClient.telemetry.logging.enabled = true //(8)!
    SomePathToConfigKafkaConsumer.telemetry.logging.enabled = true //(9)!
    SomePathToConfigKafkaProducer.telemetry.logging.enabled = true //(10)!
    ```

    1. Logging for [JDBC](database-jdbc.md), `R2DBC`, or `Vertx` database requests (default: `false`).
    2. Logging for [Cassandra](database-cassandra.md) database requests (default: `false`).
    3. Logging for [gRPC server](grpc-server.md) requests (default: `false`).
    4. Logging for [HTTP server](http-server.md) requests (default: `false`).
    5. Logging for [scheduler](scheduling.md) executions (default: `false`).
    6. Logging for [gRPC client](grpc-client.md) requests, specified for a particular service (default: `false`).
    7. Logging for [SOAP client](soap-client.md) requests, specified for a particular service (default: `false`).
    8. Logging for [HTTP client](http-client.md) requests, specified for a particular client (default: `false`).
    9. Logging for a Kafka [consumer](kafka.md#config-consumer), specified for a particular consumer (default: `false`).
    10. Logging for a Kafka [producer](kafka.md#config-producer), specified for a particular producer (default: `false`).

=== ":simple-yaml: `YAML`"

    ```yaml
    db.telemetry.logging.enabled: true #(1)!
    cassandra.telemetry.logging.enabled: true #(2)!
    grpcServer.telemetry.logging.enabled: true #(3)!
    httpServer.telemetry.logging.enabled: true #(4)!
    scheduling.telemetry.logging.enabled: true #(5)!
    grpcClient.SomeGrpcServiceName.telemetry.logging.enabled: true #(6)!
    soapClient.SomeSoapServiceName.telemetry.logging.enabled: true #(7)!
    SomePathToConfigHttpClient.telemetry.logging.enabled: true #(8)!
    SomePathToConfigKafkaConsumer.telemetry.logging.enabled: true #(9)!
    SomePathToConfigKafkaProducer.telemetry.logging.enabled: true #(10)!
    ```

    1. Logging for [JDBC](database-jdbc.md), `R2DBC`, or `Vertx` database requests (default: `false`).
    2. Logging for [Cassandra](database-cassandra.md) database requests (default: `false`).
    3. Logging for [gRPC server](grpc-server.md) requests (default: `false`).
    4. Logging for [HTTP server](http-server.md) requests (default: `false`).
    5. Logging for [scheduler](scheduling.md) executions (default: `false`).
    6. Logging for [gRPC client](grpc-client.md) requests, specified for a particular service (default: `false`).
    7. Logging for [SOAP client](soap-client.md) requests, specified for a particular service (default: `false`).
    8. Logging for [HTTP client](http-client.md) requests, specified for a particular client (default: `false`).
    9. Logging for a Kafka [consumer](kafka.md#config-consumer), specified for a particular consumer (default: `false`).
    10. Logging for a Kafka [producer](kafka.md#config-producer), specified for a particular producer (default: `false`).

## Logback { #logback }

The module provides a logging implementation based on [`Logback`](https://www.baeldung.com/logback), adds support for structured logs, and allows logging levels to be managed through the [configuration file](config.md).

### Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:logging-logback"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends LogbackModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:logging-logback")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : LogbackModule
    ```

### Configuration { #configuration-2 }

`Logback` is configured through `logback.xml`, while Kora configuration usually contains only logging levels.
Example `logback.xml`:

```xml
<configuration debug="false">
    <statusListener class="ch.qos.logback.core.status.NopStatusListener"/>

    <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
        <encoder class="ru.tinkoff.kora.logging.logback.ConsoleTextRecordEncoder"/>
    </appender>

    <appender name="ASYNC" class="ru.tinkoff.kora.logging.logback.KoraAsyncAppender">
        <appender-ref ref="STDOUT"/>
    </appender>

    <root level="WARN">
        <appender-ref ref="ASYNC"/>
    </root>
</configuration>
```

`ConsoleTextRecordEncoder` writes a text log record and adds structured data from `StructuredArgument`, `Marker`, `SLF4J` key-value pairs, and `MDC`.
This is the only encoder shipped by the module: it produces text with structured fields appended, not a single JSON document.
A record is emitted as a plain text line — `timestamp level [thread] logger - <mdc prefixes>message` — followed, when structured fields are present, by tab-indented `fieldName={json}` lines:

```text
2026-07-02 10:15:30.123 INFO  [main] r.t.k.example.SomeService - userId=42 user logged in
	role="admin"
```

`KoraAsyncAppender` is used for asynchronous log writing: it stores `MDC` values from the current context in `KoraLoggingEvent` so they are not lost when the record is passed to another thread.

### Custom pattern { #custom-pattern }

Instead of `ConsoleTextRecordEncoder`, a standard `PatternLayoutEncoder` can be used together with the converters that render Kora structured data.
`KoraMdcConverter` renders the Kora context `MDC` and `KoraLoggingMarkerConverter` renders a `StructuredArgument` marker; register them as conversion words and reference them in the pattern:

```xml
<configuration>
    <conversionRule conversionWord="koraMdc" converterClass="ru.tinkoff.kora.logging.logback.KoraMdcConverter"/>
    <conversionRule conversionWord="koraMarker" converterClass="ru.tinkoff.kora.logging.logback.KoraLoggingMarkerConverter"/>

    <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
        <encoder class="ch.qos.logback.classic.encoder.PatternLayoutEncoder">
            <pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} %-5level [%thread] %logger - %koraMdc%msg %koraMarker%n</pattern>
        </encoder>
    </appender>

    <root level="INFO">
        <appender-ref ref="STDOUT"/>
    </root>
</configuration>
```

## Other Implementation { #other-implementation }

Kora uses [`slf4j-api`](https://www.slf4j.org/) as the logging facade, so any compatible implementation can be connected.
The base module adds common components for structured logs and logging-level management through the [configuration file](config.md).

### Dependency { #dependency-2 }

The common logging module must be connected:

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:logging-common"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends LoggingModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:logging-common")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : LoggingModule
    ```

### Usage { #usage-2 }

When using a custom implementation, provide a `LoggingLevelApplier` component that can apply a logging level for the specified `Logger` and reset levels to their initial state.

If the application uses structured data, the custom implementation must also support writing `StructuredArgument`, `StructuredArgumentWriter`, and `MDC`.

## Structured Logs { #structured-logs }

Structured logs make it possible to pass not only text but also named fields to a log record.
These fields are convenient for log collection tools and can be used for search, filtering, and views.

Structured data can be passed to a log record in two ways:

- through `Marker`;
- through a message parameter.

The `marker` and `arg` methods also accept `Long`, `Integer`, `String`, `Boolean`, and `Map<String, String>` values.
For more complex objects, pass a custom `StructuredArgumentWriter` or `JsonWriter`.

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

### Complex object { #complex-object }

For values that are not a `String`, number, `Boolean`, or `Map<String, String>`, pass a `JsonWriter<T>` (the same [`@Json`](json.md) writer generated for the type) or a raw `StructuredArgumentWriter` lambda that writes the field value directly to the `JsonGenerator`.
Both `arg` and `marker` provide these overloads:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var logger = LoggerFactory.getLogger(getClass());
    var parameter = StructuredArgument.arg("user", gen -> {
        gen.writeStartObject();
        gen.writeStringField("id", "42");
        gen.writeStringField("role", "admin");
        gen.writeEndObject();
    });
    logger.info("user logged in", parameter);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val logger = LoggerFactory.getLogger(javaClass)
    val parameter = StructuredArgument.arg("user") { gen ->
        gen.writeStartObject()
        gen.writeStringField("id", "42")
        gen.writeStringField("role", "admin")
        gen.writeEndObject()
    }
    logger.info("user logged in", parameter)
    ```

### MDC { #mdc }

Structured data can be attached to all records within the current context using the `ru.tinkoff.kora.logging.common.MDC` class.
The value will be added to every log record until it is removed from `MDC`:

!!! warning "Import"

    Use `ru.tinkoff.kora.logging.common.MDC`, not `org.slf4j.MDC`. Kora keeps its `MDC` inside the Kora context rather than in a thread-local, so values placed into `org.slf4j.MDC` are not rendered by the Kora encoders and do not propagate across asynchronous boundaries. For a declarative alternative see [`@Mdc`](logging-aspect.md).

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

`put` accepts `String`, `Integer`, `Long`, and `Boolean` values, as well as a raw `StructuredArgumentWriter` for arbitrary JSON; typed values are rendered as their JSON type rather than as text.
There is also a `put(Context, key, value)` overload for writing into an explicitly provided context instead of the current one:

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

Because it lives in the Kora context, the `MDC` propagates across asynchronous and reactive boundaries together with the context.

If `AsyncAppender` is used, use `ru.tinkoff.kora.logging.logback.KoraAsyncAppender` to pass `MDC` parameters correctly.
It snapshots the current context `MDC` at append time and passes `ru.tinkoff.kora.logging.logback.KoraLoggingEvent` to the delegate, so the structured `MDC` is preserved when the record is handed to the async worker thread.
