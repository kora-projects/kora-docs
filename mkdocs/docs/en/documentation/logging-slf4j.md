Kora uses [slf4j-api](https://www.slf4j.org/) as the logging engine for the entire framework,
it is expected that an implementation based on [Logback](#logback) will be used.

## Usage

Loggers are required to be provided through the [SLF4J](https://www.slf4j.org/manual.html#hello_world) factory.

=== ":fontawesome-brands-java: `Java`"

    ```java
    Logger logger = LoggerFactory.getLogger(SomeService.class)
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val logger = LoggerFactory.getLogger(SomeService::class.java);
    ```

## Configuration

Logging levels described in the `LoggingConfig` class:

===! ":material-code-json: `Hocon`"

    ```javascript
    logging {
      levels {  //(1)!
        "ru.tinkoff.kora.http.server.common.telemetry": "INFO"
        "ru.tinkoff.kora.http.client.common.telemetry.DefaultHttpClientTelemetry": "INFO"
      }
    }
    ```

    1.  Logging levels for classes and packages are specified

=== ":simple-yaml: `YAML`"

    ```yaml
    logging:
      levels: #(1)!
        ru.tinkoff.kora.http.server.common.telemetry: "INFO"
        ru.tinkoff.kora.http.client.common.telemetry.DefaultHttpClientTelemetry: "INFO"
    }
    ```

    1.  Logging levels for classes and packages are specified

Logback configuration parameters are described in the modules that include logback, e.g. [HTTP server](http-server.md), [HTTP client](http-client.md), etc.

## Logback

The module provides a logging implementation based on [Logback](https://www.baeldung.com/logback), adds support for structured logs and the ability to configure logging levels via [config file](config.md).

### Dependency

=== ":fontawesome-brands-java: `Java`"

    Dependency `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:logging-logback"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends LogbackModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Dependency `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:logging-logback")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : LogbackModule
    ```

### Configuration

It is assumed that [Logback](https://logback.qos.ch/manual/configuration.html) will be configured via `logback.xml`, and only logging levels will be specified in the Kora configuration, example `logback.xml`:

```xml
<configuration debug="false">
    <statusListener class="ch.qos.logback.core.status.NopStatusListener" />
    <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
        <encoder>
            <charset>UTF-8</charset>
            <pattern>%d{HH:mm:ss.SSS} %-5level [%thread] %logger{36} - %msg%n</pattern>
        </encoder>
    </appender>

    <appender name="ASYNC" class="ru.tinkoff.kora.logging.logback.KoraAsyncAppender">
        <appender-ref ref="STDOUT"/>
    </appender>

    <root level="WARN">
        <appender-ref ref="ASYNC"/>
    </root>
</configuration>
```

## Other implementation

Kora uses [slf4j-api](https://www.slf4j.org/) as the logging engine, you can plug in your own any compatible implementation.
The base module adds support for structured logs and the ability to configure logging levels via [config file](config.md).

### Dependency

A generic logging implementation will need to be connected:

=== ":fontawesome-brands-java: `Java`"

    Dependency `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:logging-common"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends LoggingModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Dependency `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:logging-common")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : LoggingModule
    ```

### Usage

When using your own implementation, you would need to provide an implementation of `LoggingLevelApplier` that implements the
setting the logging level and resetting it.

It will also be necessary for the implementation to independently support `StructuredArgument`, `StructuredArgumentWriter` and `MDC` if they are to be used.

## Structured Logs

You can pass structured data to a log record in two ways via:

- Marker
- Parameter

The marker and parameter methods also take `Long`, `Integer`, `String`, `Boolean` and `Map<String, String>` as arguments.

### Marker

You can pass structured data to the log via a marker:

=== ":fontawesome-brands-java: `Java`"

    ```java
    var logger = LoggerFactory.getLogger(getClass());
    var marker = StructuredArgument.marker("key", gen -> {
       gen.writeString("value");
    });
    logger.info(marker, "message");
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val logger = LoggerFactory.getLogger(javaClass)
    val marker = StructuredArgument.marker("key") { it.writeString("value") }
    logger.info(marker, "message")
    ```

### Parameter

You can transfer structured data to the log via parameters:

=== ":fontawesome-brands-java: `Java`"

    ```java
    var logger = LoggerFactory.getLogger(getClass());
    var parameter = StructuredArgument.arg("key", gen -> {
      gen.writeString("value");
    });
    log.info("message", parameter);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val logger = LoggerFactory.getLogger(javaClass)
    val parameter = StructuredArgument.arg("key") { it.writeString("value") }
    logger.info("message", parameter)
    ```

### MDC

Structured data can be attached to all records within a context using the `ru.tinkoff.kora.logging.common.MDC` class:

=== ":fontawesome-brands-java: ``Java``"

    ```java
    MDC.put("key", gen -> gen.writeString("value"));
    ```

=== ":simple-kotlin: `Kotlin`"

    ````kotlin
    MDC.put("key") { it.writeString("value") }
    ```

If you are using `AsyncAppender` to send logs, you need to use `ru.tinkoff.kora.logging.logback.KoraAsyncAppender` to correctly pass MDC parameters,
which will pass to the delegate `ru.tinkoff.kora.kora.logging.logging.logback.KoraLoggingEvent` containing, among other things, a structured MDC.
