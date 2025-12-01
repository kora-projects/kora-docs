---
title: Configuration Management with Kora
summary: Learn how to create type-safe configuration with @ConfigSource interfaces and HOCON
tags: configuration, hocon, configsource, type-safe-config
---

# Configuration Management with Kora

This guide shows you how to create type-safe configuration using Kora's `@ConfigSource` interfaces and HOCON-based configuration system. You'll learn to externalize application settings with compile-time safety and proper dependency injection.

## What You'll Build

You'll enhance the task management application with:

- Type-safe configuration interfaces using `@ConfigSource`
- Externalized application settings with HOCON
- Environment-specific configuration overrides
- Configuration validation and debugging endpoints
- Proper dependency injection of configuration

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

Now add the HOCON configuration module to your project:

===! ":fontawesome-brands-java: `Java`"

    Add to the `dependencies` block in `build.gradle`:

    ```groovy
    dependencies {
        // ... existing dependencies ...

        implementation("ru.tinkoff.kora:config-hocon")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Add to the `dependencies` block in `build.gradle.kts`:

    ```kotlin
    dependencies {
        // ... existing dependencies ...

        implementation("ru.tinkoff.kora:config-hocon")
    }
    ```

## Add Modules

Update your Application interface to include the HOCON configuration module:

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/ru/tinkoff/kora/example/Application.java`:

    ```java
    package ru.tinkoff.kora.example;

    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.config.hocon.HoconConfigModule;
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
            UndertowHttpServerModule,
            HoconConfigModule,
            LogbackModule
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/ru/tinkoff/kora/example/Application.kt`:

    ```kotlin
    package ru.tinkoff.kora.example

    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.config.hocon.HoconConfigModule
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule
    import ru.tinkoff.kora.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        UndertowHttpServerModule,
        HoconConfigModule,
        LogbackModule
    ```

## What is HOCON?

**HOCON (Human-Optimized Config Object Notation)** is a configuration file format designed to be more readable and user-friendly than traditional formats like JSON, XML, or Properties files. Developed by Lightbend (formerly Typesafe) for the Akka framework, HOCON combines the simplicity of JSON with additional features that make it ideal for configuration management.

### Why HOCON for Configuration?

HOCON was chosen for Kora applications because it offers the perfect balance between human readability and machine parseability:

- **Human-Friendly**: More readable than JSON with less punctuation and noise
- **Flexible Syntax**: Supports both JSON-like and Properties-like formats
- **Hierarchical**: Natural representation of nested configuration structures
- **Type-Safe**: Clear distinction between strings, numbers, booleans, and objects
- **Environment Integration**: Built-in support for environment variables and system properties
- **Include Support**: Ability to compose configurations from multiple files

### HOCON Syntax Basics

#### Simple Values
```hocon
# Strings (quoted or unquoted)
app.name = "My Application"
app.version = 1.0.0
environment = development

# Booleans
features.enabled = true
debug.mode = false

# Numbers
server.port = 8080
timeout.seconds = 30
```

#### Objects and Nesting
```hocon
# Nested objects using braces
database {
    host = "localhost"
    port = 5432
    credentials {
        username = "admin"
        password = "secret"
    }
}

# Or using dotted notation
database.host = "localhost"
database.port = 5432
database.credentials.username = "admin"
database.credentials.password = "secret"
```

#### Arrays and Lists
```hocon
# Arrays with square brackets
allowed.origins = ["http://localhost:3000", "https://myapp.com"]

# Or multi-line format
features = [
    "authentication"
    "authorization"
    "logging"
]
```

#### Environment Variables
```hocon
# Required environment variable (fails if not set)
database.password = ${DATABASE_PASSWORD}

# Optional environment variable with default
database.host = ${?DATABASE_HOST}
database.host = "localhost"  # fallback if env var not set

# With default value inline
cache.ttl = ${?CACHE_TTL}
cache.ttl = 300  # 5 minutes default
```

#### Includes and Overrides
```hocon
# Include base configuration
include "application"

# Override specific values
app.environment = "production"
database.pool.size = 20
```

### HOCON in Kora Applications

Kora uses HOCON as its primary configuration format because it naturally maps to the hierarchical, type-safe configuration interfaces you'll create. The `HoconConfigModule` provides:

- **Automatic Parsing**: Converts HOCON files to configuration objects
- **Validation**: Ensures required configuration is present and correctly typed
- **Environment Integration**: Seamlessly combines file-based and environment-based configuration
- **Profile Support**: Easy switching between development, test, and production configurations

### Configuration File Locations

Kora looks for configuration files in this order:
1. `application.conf` - Base configuration
2. `application-{profile}.conf` - Environment-specific overrides
3. System properties and environment variables

### Best Practices for HOCON

- **Use meaningful names**: `database.connection.pool.size` vs `dbPoolSize`
- **Group related settings**: Use nested objects for logical grouping
- **Document complex configs**: Add comments for non-obvious settings
- **Use environment variables**: For secrets and environment-specific values
- **Keep it DRY**: Use includes to avoid duplication across environments
- **Validate regularly**: Use HOCON validators to catch syntax errors early

## Create Configuration Classes

Create configuration interfaces to define your application's settings:

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/example/config/AppConfig.java`:

    ```java
    package ru.tinkoff.kora.example.config;

    import ru.tinkoff.kora.config.common.annotation.ConfigSource;

    @ConfigSource("app")
    public interface AppConfig {

        String name();

        String version();

        String environment();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/example/config/AppConfig.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.config

    import ru.tinkoff.kora.config.common.annotation.ConfigSource

    @ConfigSource("app")
    interface AppConfig {

        fun name(): String

        fun version(): String

        fun environment(): String
    }
    ```

## Update Application Configuration

Update your `src/main/resources/application.conf` to include application configuration:

```hocon
app {
    name = "Task Management App"
    version = "1.0.0"
    environment = "development"
    }
    ```

## Add Configuration EndpointAdd an endpoint to display current configuration (for debugging):

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/ru/tinkoff/kora/example/controller/ConfigController.java`:

    ```java
    package ru.tinkoff.kora.example.controller;

    import ru.tinkoff.kora.example.config.AppConfig;
    import ru.tinkoff.kora.http.common.annotation.HttpController;
    import ru.tinkoff.kora.http.common.annotation.HttpRoute;
    import ru.tinkoff.kora.json.common.annotation.Json;

    import java.util.Map;

    @HttpController
    public final class ConfigController {

        private final AppConfig appConfig;

        public ConfigController(AppConfig appConfig) {
            this.appConfig = appConfig;
        }

        @HttpRoute(method = "GET", path = "/config")
        @Json
        public Map<String, Object> getConfig() {
            return Map.of(
                "app", Map.of(
                    "name", appConfig.name(),
                    "version", appConfig.version(),
                    "environment", appConfig.environment()
                )
            );
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/ru/tinkoff/kora/example/controller/ConfigController.kt`:

    ```kotlin
    package ru.tinkoff.kora.example.controller

    import ru.tinkoff.kora.example.config.AppConfig
    import ru.tinkoff.kora.http.common.annotation.HttpController
    import ru.tinkoff.kora.http.common.annotation.HttpRoute
    import ru.tinkoff.kora.json.common.annotation.Json

    @HttpController
    class ConfigController(
        private val appConfig: AppConfig
    ) {

        @HttpRoute(method = "GET", path = "/config")
        @Json
        fun getConfig(): Map<String, Any> {
            return mapOf(
                "app" to mapOf(
                    "name" to appConfig.name(),
                    "version" to appConfig.version(),
                    "environment" to appConfig.environment()
                )
            )
        }
    }
    ```

## Test the Configuration

Build and run your application:

```bash
./gradlew build
./gradlew run
```

Test the configuration endpoint:

```bash
curl http://localhost:8080/config
```

You should see output similar to:
```json
{
  "app": {
    "name": "Task Management App",
    "version": "1.0.0",
    "environment": "development"
  }
}
```

## Benefits of Type-Safe Configuration

Using `@ConfigSource` interfaces provides several advantages over direct configuration access:

- **Compile-time Safety**: Configuration keys are validated at compile time
- **IDE Support**: Auto-completion and refactoring support for configuration properties
- **Type Safety**: Proper typing prevents runtime casting errors
- **Documentation**: Configuration interfaces serve as living documentation
- **Testing**: Easy to mock configuration in unit tests
- **Refactoring**: Safe renaming of configuration properties across the codebase

### When to Use @ConfigSource vs Direct Config Access

- **Use @ConfigSource** for application-specific configuration that needs type safety and validation
- **Use direct Config access** for dynamic configuration or when you need to access arbitrary keys
- **Use @ConfigSource** when configuration structure is stable and well-defined
- **Use direct Config access** for framework internals or highly dynamic configuration needs

### Environment-Specific Configuration

Create different configuration files for different environments:

Create `src/main/resources/application-dev.conf`:
```hocon
include "application"

app {
    environment = "development"
}
```

Create `src/main/resources/application-prod.conf`:
```hocon
include "application"

app {
    environment = "production"
}
```

Run with different environments:

```bash
# Development
./gradlew run

# Production
./gradlew run -Dconfig.override=application-prod.conf
```

## Key Concepts Learned

### Configuration Sources
- **@ConfigSource**: Maps configuration sections to type-safe interfaces
- **HOCON format**: Human-readable configuration syntax with hierarchical structure
- **Environment variables**: `${VAR_NAME}` and `${?VAR_NAME}` syntax for external configuration
- **Default values**: Fallback values when environment variables aren't set

### Type-Safe Configuration
- **Interface-based**: Compile-time checked configuration access
- **Dependency injection**: Configuration interfaces injected like services
- **Validation**: Required vs optional configuration values with proper typing
- **Static configuration**: Use static values for predictable, documented behavior

### Environment Management
- **Profile-based configs**: Different settings per environment using include mechanism
- **Override mechanism**: `-Dconfig.override` for runtime config selection
- **Hierarchical configuration**: Base config with environment-specific overrides

## Next Steps

Continue your learning journey:

- **Next Guide**: [Database Integration](../database-jdbc.md) - Learn about database connectivity and data persistence
- **Related Documentation**:
  - [Configuration Module](../../documentation/config.md)
  - [HOCON Config Example](../../examples/kora-java-config-hocon/)
- **Advanced Topics**:
  - [YAML Configuration](../../documentation/config-yaml.md)
  - [Custom Config Sources](../../documentation/config.md#custom-sources)

## Troubleshooting

### Configuration Not Loading
- Verify `application.conf` is in `src/main/resources/`
- Check HOCON syntax with a [validator](https://github.com/lightbend/config#hocon-human-optimized-config-object-notation)
- Ensure `HoconConfigModule` is included in your Application interface

### Environment Variables Not Working
- Use `${?VAR_NAME}` for optional variables
- Provide default values after the optional syntax
- Check variable names match exactly (case-sensitive)
- Ensure environment variables are set before application startup