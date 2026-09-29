---
seo_title: "Kora Logging: SLF4J, Logback, JSON and Structured Logs"
seo_description: "Reference for Kora logging: SLF4J loggers, log level configuration with runtime refresh, the Logback module, text and JSON encoders, async appender, structured logs and scoped MDC."
keywords: ["Kora Framework", "Kora logging", "SLF4J", "Logback", "JSON logging", "structured logging", "MDC"]
description: "Explains Kora SLF4J logging: obtaining a Logger, the logging.levels configuration and its runtime refresh, per-component telemetry logging, the Logback module with KoraLogbackConfigurator, encoder selection (text, pretty, json), the logging-logback-json JsonRecordEncoder with field masking, KoraAsyncAppender and its bootstrap properties, structured logs and the scoped MDC. Use when working with LoggingModule, LogbackModule, LoggingConfig, LoggingLevelApplier, LogbackEncoderFactory, kora.logging.encoder, JsonRecordEncoder, StructuredArgument, MDC, KoraMdcConverter, telemetry.logging.enabled."
agent:
  use_when: "Use this file for Kora docs or implementation questions about SLF4J logging setup, logging.levels configuration and runtime refresh, per-component telemetry logging, Logback integration, text and JSON log encoders, encoder selection without logback.xml, JSON record masking, async appender tuning, alternative SLF4J implementations, structured log fields and MDC; key triggers include LoggingModule, LogbackModule, LoggingConfig, LoggingLevelApplier, LoggingLevelRefresher, KoraLogbackConfigurator, LogbackEncoderFactory, kora.logging.encoder, KORA_LOGGING_ENCODER, kora.logging.config, logging-logback-json, JsonRecordEncoder, LoggingEventJsonWriter, LoggingEventJsonMasker, FieldLoggingEventJsonMasker, maskField, ConsoleTextRecordEncoder, LoggingEventTextWriter, KoraAsyncAppender, KoraMdcConverter, KoraLoggingMarkerConverter, StructuredArgument, MDC, telemetry.logging.enabled."
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
    As a result, the `<root level="...">` value from `logback.xml`, or the [`kora.logging.levels.root`](#bootstrap-properties) property of the default pipeline, is effectively replaced by `INFO` at startup unless a `ROOT` level is set in the configuration.

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

A `logback.xml` file is optional.
The module registers `KoraLogbackConfigurator` through the `Logback` `Configurator` SPI, and it resolves the configuration in this order:

1. When `Logback` finds a configuration file (`logback-test.xml`, `logback.xml`, or the file named by the `logback.configurationFile` system property), the file is applied as usual and Kora adds no appenders of its own.
2. Otherwise Kora selects one [encoder](#encoder-selection) and attaches it to the root logger through a `ConsoleAppender` named `KORA_CONSOLE`, wrapped into a `KoraAsyncAppender` named `KORA_ASYNC`. The root level of this pipeline is taken from the [`kora.logging.levels.root`](#bootstrap-properties) property (default: `INFO`).

In both cases `java.util.logging` is routed into `Logback`: the default `JUL` console handler is removed, and `Logback` levels are mirrored into `JUL`, so a library logging through `JUL` follows the levels set in `logging.levels`.
The bridge is skipped when a configuration file has already installed it, and is switched off with `kora.logging.config.jul-bridge=false`.

A configuration file is needed only when the default pipeline does not fit, for example to add a file appender or a [custom pattern](#custom-pattern).
Example `logback.xml`:

```xml
<configuration debug="false">
    <statusListener class="ch.qos.logback.core.status.NopStatusListener"/>

    <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
        <encoder class="io.koraframework.logging.logback.text.ConsoleTextRecordEncoder"/>
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

The defaults of `KoraAsyncAppender` favour the application over the log: the queue is bounded, a full queue drops the record instead of blocking the logging thread, and shutdown waits at most a second for the queue to be flushed.
They are changed through the [bootstrap properties](#bootstrap-properties), and in `logback.xml` the nested `<queueSize>`, `<discardingThreshold>`, `<maxFlushTime>` and `<neverBlock>` elements of the appender override those properties.

### Encoder selection { #encoder-selection }

The encoder of the default pipeline is created by a `LogbackEncoderFactory`.
Factories are discovered through `java.util.ServiceLoader`, so putting a module on the classpath is enough to make its encoder available, and exactly one of them is used: the one named by `kora.logging.encoder` (case insensitive), or, when nothing is named, the one with the highest priority.

| Name | Factory | Module | Priority | Output |
|---|---|---|---|---|
| `text` | `ConsoleTextEncoderFactory` | `logging-logback` | `0` | [plain text](#record-format) |
| `pretty` | `ColorConsoleTextEncoderFactory` | `logging-logback` | `1000` in a `Gradle` test worker, the lowest possible otherwise | the same text with the timestamp and the level highlighted with `ANSI` colors |
| `json` | `JsonEncoderFactory` | `logging-logback-json` | `100` | [one `JSON` object per line](#json-format) |

As a result, an application logs plain text by default, switches to `JSON` as soon as `logging-logback-json` is on the classpath, and logs colored text in `Gradle` tests, which are detected by the `org.gradle.test.worker` system property.
A test that asserts on `JSON` output opts out of colors with `kora.logging.encoder=json`, and colored text is enabled anywhere with `KORA_LOGGING_ENCODER=pretty`.

The value `none` hands configuration back to the default configuration of `Logback` itself.
An unknown name is reported as a `Logback` status error and has the same effect.
A custom encoder is plugged in the same way, by [registering a factory](#json-masking) of your own.

### Bootstrap properties { #bootstrap-properties }

`Logback` starts before the application graph and its [configuration file](config.md) exist, so the module reads its own settings from `JVM` system properties and environment variables.
Every property is looked up as a system property first and then as an environment variable whose name is the property in upper case with `.` and `-` replaced by `_`:

| System property | Environment variable | Description |
|---|---|---|
| `kora.logging.encoder` | `KORA_LOGGING_ENCODER` | Name of the [encoder](#encoder-selection) of the default pipeline, or `none` (default: the discovered encoder with the highest priority). |
| `kora.logging.levels.root` | `KORA_LOGGING_LEVELS_ROOT` | Root logger level of the default pipeline until `logging.levels` is applied (default: `INFO`). |
| `kora.logging.config.jul-bridge` | `KORA_LOGGING_CONFIG_JUL_BRIDGE` | Routes `java.util.logging` into `Logback` (default: `true`). |
| `kora.logging.config.timestamp-epoch-millis` | `KORA_LOGGING_CONFIG_TIMESTAMP_EPOCH_MILLIS` | Writes the record timestamp as milliseconds since the epoch instead of a formatted date (default: `false`). |
| `kora.logging.config.queue-size` | `KORA_LOGGING_CONFIG_QUEUE_SIZE` | Capacity of the `KoraAsyncAppender` queue (default: `512`). |
| `kora.logging.config.discarding-threshold` | `KORA_LOGGING_CONFIG_DISCARDING_THRESHOLD` | Remaining queue capacity below which `TRACE`, `DEBUG` and `INFO` records are dropped, `0` never drops by level (default: a fifth of the queue size). |
| `kora.logging.config.max-flush-time` | `KORA_LOGGING_CONFIG_MAX_FLUSH_TIME` | How long shutdown waits for the queue to be flushed, as `1s`, `500ms` or `PT1S`, `0` waits without a limit (default: `1s`). |
| `kora.logging.config.never-block` | `KORA_LOGGING_CONFIG_NEVER_BLOCK` | Drops a record instead of blocking the logging thread when the queue is full (default: `true`). |

A malformed value does not stop logging from starting: the default is used instead. For `jul-bridge` and the `KoraAsyncAppender` settings the value is also reported as a `Logback` status warning, an unknown encoder name is reported as a status error, and an unknown root level silently falls back to `INFO`.

!!! warning "Not keys of the application configuration"

    These properties are read only from system properties and environment variables, never from `application.conf` or `application.yaml`.
    Logger levels of a running application are still set through the [`logging.levels`](#configuration) section, which replaces the root level of the default pipeline once the graph starts.

### Log record format { #record-format }

The `text` and `pretty` encoders are both `io.koraframework.logging.logback.text.ConsoleTextRecordEncoder`.
It produces a text line with structured fields appended, not a single `JSON` document, and is composed as follows:

- `yyyy-MM-dd HH:mm:ss.SSS` timestamp in `UTC` (the epoch milliseconds with `kora.logging.config.timestamp-epoch-millis=true`), the level, the thread name in square brackets, and the logger name;
- `traceId=... spanId=...` when the record was produced inside a traced operation;
- the Kora `MDC` entries as `key=<json value>`;
- the `SLF4J` `MDC` entries as plain `key=value`;
- the formatted message;
- one tab-indented `fieldName={json}` line per structured field taken from markers, message arguments, and `SLF4J` key-value pairs whose value is a `StructuredArgumentWriter`;
- the stack trace, when the record carries a `Throwable`.

```text
2026-07-02 10:15:30.123 INFO  [kora-undertow-1] io.koraframework.example.SomeService - traceId=4bf92f3577b34da6a3ce929d0e0e4736 spanId=00f067aa0ba902b7 userId=42 user logged in
	role="admin"
```

The logger name is written in full and is shortened package by package only when it exceeds 100 characters.

Each of these parts is appended by a `LoggingEventTextWriter` from the `io.koraframework.logging.logback.text.writer` package: `DefaultLoggingEventTextWriter`, `DefaultTraceTextWriter`, `DefaultMdcTextWriter`, `DefaultMessageTextWriter`, `DefaultStructuredTextWriter` and `DefaultExceptionTextWriter`, in this order.
Declaring `<writer>` elements in `logback.xml` replaces the default list as a whole, so a custom layout lists every part it keeps:

```xml
<encoder class="io.koraframework.logging.logback.text.ConsoleTextRecordEncoder">
    <writer class="io.koraframework.logging.logback.text.writer.DefaultLoggingEventTextWriter"/>
    <writer class="io.koraframework.logging.logback.text.writer.DefaultTraceTextWriter"/>
    <writer class="io.koraframework.logging.logback.text.writer.DefaultMessageTextWriter"/>
    <writer class="io.koraframework.logging.logback.text.writer.DefaultExceptionTextWriter"/>
</encoder>
```

A writer that throws does not lose the record: the encoder falls back to a line with the level, the logger, the message and the failure.

### JSON format { #json-format }

`JsonRecordEncoder` writes every record as a single line of `JSON`, which log collectors ingest without a parsing pattern.
It lives in a separate module:

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:logging-logback-json"
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:logging-logback-json")
    ```

The module has no Kora module interface to add: its `json` encoder is discovered on the classpath and, having a higher priority than `text`, becomes the [default encoder](#encoder-selection).

A record contains the following fields, and a field without a value is left out:

- `@timestamp` — an `ISO 8601` date in `UTC`, or a number of epoch milliseconds with `kora.logging.config.timestamp-epoch-millis=true`;
- `level`, `thread`, `logger`, `message`;
- `traceId`, `spanId` — when the record was produced inside a traced operation;
- `mdc` — an object with the Kora `MDC` entries as typed `JSON` values and the `SLF4J` `MDC` entries as strings; on the same key the Kora `MDC` wins;
- `data` — the structured argument named `data`, which is where the [`@Log`](logging-aspect.md) aspect writes arguments and results; several `data` arguments are merged into one object;
- `args` — the other structured arguments from markers and message parameters, and every `SLF4J` key-value pair; a plain key-value value keeps its number or boolean type and any other object is written through `toString()`;
- `exception` — an object with `class`, `message` and `stacktrace`, when the record carries a `Throwable`; a structured argument named `exception` or `throwable` is added to it as `data`.

```json
{"@timestamp":"2026-07-02T10:15:30.123Z","level":"INFO","thread":"kora-undertow-1","logger":"io.koraframework.example.SomeService","message":"user logged in","traceId":"4bf92f3577b34da6a3ce929d0e0e4736","spanId":"00f067aa0ba902b7","mdc":{"userId":42},"args":{"role":"admin"}}
```

The encoder can also be declared in `logback.xml`.
Like the text encoder, it is assembled from writers — `LoggingEventJsonWriter` implementations from the `io.koraframework.logging.logback.json.writer` package — and nested `<writer>` elements replace the default list as a whole.
A writer that throws does not lose the record: the encoder falls back to a record with `@timestamp`, `level`, `logger`, `message` and the failure in `exception`.

#### Record masking { #json-masking }

`JsonRecordEncoder` can mask fields of the finished record by name, whatever wrote them:

```xml
<appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
    <encoder class="io.koraframework.logging.logback.json.JsonRecordEncoder">
        <maskField>password</maskField>
        <maskField>token</maskField>
    </encoder>
</appender>

<appender name="ASYNC" class="io.koraframework.logging.logback.KoraAsyncAppender">
    <appender-ref ref="STDOUT"/>
</appender>
```

`<maskField>` values are turned into a `FieldLoggingEventJsonMasker`: a field with that name is matched case insensitively anywhere in the record — in `mdc`, `data` or `args` — and its value is replaced with `"***"`, an object or an array as a whole.
For other rules, implement `LoggingEventJsonMasker` and declare it as `<masker class="..."/>`: `shouldMask(path, fieldName)` receives the dotted path from the record root, such as `args.user.password`, and `writeMasked` writes the replacement (default: `"***"`).
When both `<masker>` and `<maskField>` are declared, the `<maskField>` values are ignored with a status warning.

This masking works on field names only and knows nothing about the logged types; to mask values of a type wherever it is logged, use [`@Mask`](logging-aspect.md#masking).

The `json` encoder of the default pipeline is created without masking.
To keep the pipeline without writing `logback.xml`, register an encoder factory of your own:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class MaskedJsonEncoderFactory implements LogbackEncoderFactory {

        @Override
        public String name() {
            return "masked-json"; //(1)!
        }

        @Override
        public int priority() {
            return 200; //(2)!
        }

        @Override
        public Encoder<ILoggingEvent> create(LoggerContext context) {
            var encoder = new JsonRecordEncoder();
            encoder.addMaskField("password");
            encoder.addMaskField("token");
            return encoder; //(3)!
        }
    }
    ```

    1. Name that selects this encoder through `kora.logging.encoder=masked-json`.
    2. Higher than `json` (`100`), so the factory wins without being named; in `Gradle` tests `pretty` (`1000`) still wins unless an encoder is named.
    3. The encoder is returned not started: `KoraLogbackConfigurator` sets its context and starts it.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class MaskedJsonEncoderFactory : LogbackEncoderFactory {

        override fun name(): String = "masked-json" //(1)!

        override fun priority(): Int = 200 //(2)!

        override fun create(context: LoggerContext): Encoder<ILoggingEvent> {
            val encoder = JsonRecordEncoder()
            encoder.addMaskField("password")
            encoder.addMaskField("token")
            return encoder //(3)!
        }
    }
    ```

    1. Name that selects this encoder through `kora.logging.encoder=masked-json`.
    2. Higher than `json` (`100`), so the factory wins without being named; in `Gradle` tests `pretty` (`1000`) still wins unless an encoder is named.
    3. The encoder is returned not started: `KoraLogbackConfigurator` sets its context and starts it.

The factory is discovered through `java.util.ServiceLoader`, so it is listed in a service file rather than declared as a graph component:

```text title="src/main/resources/META-INF/services/io.koraframework.logging.logback.LogbackEncoderFactory"
com.example.MaskedJsonEncoderFactory
```

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

`KoraMdcConverter` prefers the `MDC` snapshot carried by `KoraLoggingEvent` and only falls back to reading the `MDC` bound to the logging thread, rendering each entry as `key: <json value>`.
On a thread with no [`MDC` scope](#mdc-scope) — graph initialization, a shutdown hook, a library thread pool — it renders nothing, and the rest of the line is still written.
Behind a plain asynchronous appender the converter runs on the writer thread and sees no `MDC` at all, which is why `KoraAsyncAppender` takes the snapshot on the calling thread before handing the record over.

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
