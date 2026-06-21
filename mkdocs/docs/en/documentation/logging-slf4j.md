---
description: "Explains Kora SLF4J logging setup, module log configuration, Logback integration, alternative implementations, structured logs, markers, parameters, and MDC. Use when working with Slf4jModule, LogbackModule, LoggerFactory, StructuredArgument, Marker, MDC, loggingConfig."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora SLF4J logging setup, module log configuration, Logback integration, alternative implementations, structured logs, markers, parameters, and MDC; key triggers include Slf4jModule, LogbackModule, LoggerFactory, StructuredArgument, Marker, MDC, loggingConfig."
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

If the `logging` section is not specified, Kora does not override logging levels through its configuration.

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
    9. Logging for a Kafka [consumer](kafka.md#configuration), specified for a particular consumer (default: `false`).
    10. Logging for a Kafka [producer](kafka.md#manual-override), specified for a particular producer (default: `false`).

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
    9. Logging for a Kafka [consumer](kafka.md#configuration), specified for a particular consumer (default: `false`).
    10. Logging for a Kafka [producer](kafka.md#manual-override), specified for a particular producer (default: `false`).

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
`KoraAsyncAppender` is used for asynchronous log writing: it stores `MDC` values from the current context in `KoraLoggingEvent` so they are not lost when the record is passed to another thread.

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

### MDC { #mdc }

Structured data can be attached to all records within the current context using the `ru.tinkoff.kora.logging.common.MDC` class.
The value will be added to every log record until it is removed from `MDC`:

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

If `AsyncAppender` is used, use `ru.tinkoff.kora.logging.logback.KoraAsyncAppender` to pass `MDC` parameters correctly.
It passes `ru.tinkoff.kora.logging.logback.KoraLoggingEvent` to the delegate, and that event also contains structured `MDC`.
