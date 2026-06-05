---
search:
  exclude: true
title: YAML Configuration Management with Kora
summary: Learn how to bind YAML configuration to type-safe interfaces, separate required and defaulted values, and reuse one config shape across multiple integrations
tags: configuration, yaml, configsource, configvalueextractor
---

# YAML Configuration Management with Kora { #yaml-configuration-management-kora }

This guide introduces type-safe configuration with Kora and YAML. It covers how configuration records are extracted from `application.yaml`, how required and defaulted values are represented in Java
code, and how reusable config fragments can be injected into multiple components without duplicating the whole block. You will also see how environment variables and printed runtime output make
resolved configuration easy to inspect.

===! ":fontawesome-brands-java: `Java`"

    If you want to check your progress along the way, use the finished working example: [Kora Java Config YAML App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-config-yaml-app).

=== ":simple-kotlin: `Kotlin`"

    If you want to check your progress along the way, use the finished working example: [Kora Kotlin Config YAML App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-config-yaml-app).

## What You'll Build { #youll-build }

You'll build a small runnable Kora application that:

- binds `app.name`, `app.version`, and `app.environment` through `@ConfigSource`
- treats `APP_VERSION` as required and `APP_NAME` as an environment override with a default
- defines one reusable `LibConfig` with `endpoint` and `requestTimeout`
- extracts that same `LibConfig` for `lib1` and `lib2`
- reuses one shared YAML object and overrides only one field for the second library
- prints all resolved values to `stdout` during startup

## What You'll Need { #youll-need }

- JDK 17 or later
- Gradle 7+
- A text editor or IDE
- Completed [Creating Your First Kora App](getting-started.md) guide

## Prerequisites { #prerequisites }

!!! note "Required: Complete Getting Started"

    This guide assumes you have completed **[Creating Your First Kora App](getting-started.md)** and already have a runnable Kora project with the `application` plugin and a generated application graph.

    If you haven't created that baseline yet, complete the getting started guide first, because this guide focuses on typed configuration rather than initial project setup.

## Overview { #overview }

Configuration is how runtime environments influence application behavior without changing code. Ports, credentials, feature switches, timeouts, and external service addresses should live outside
compiled classes, but application code still needs a type-safe way to read them.

The main lesson is that configuration should be explicit at the application boundary. Components should not search environment variables or parse files by themselves; they should receive typed
configuration from the graph.

### YAML and Type-Safe Extraction { #yaml-type-safe-extraction }

Kora can read [YAML](https://yaml.org/spec/) configuration through [SnakeYAML](https://github.com/snakeyaml/snakeyaml) and extract it into Java interfaces or records. Instead of passing raw strings
and maps through the application, components receive typed configuration objects. This makes required values explicit and lets the compiler help with configuration usage.

This guide uses two complementary mapping styles:

- `@ConfigSource("app")` maps one fixed config section to a type-safe dependency
- `@ConfigValueExtractor` maps a reusable config shape that can be extracted from different paths

Use `@ConfigSource` when a component needs one stable section of application configuration. Use `@ConfigValueExtractor` when the same structure appears in several places and you want one reusable
extractor.

### Required and Default Values { #required-default }

YAML supports useful composition features:

- required environment substitution such as `${APP_VERSION}`
- defaulted environment substitution such as `${APP_NAME:Task Management App}`
- object reuse through Kora substitutions from another YAML section

These features let one configuration file stay readable while still adapting to local development, tests, and deployed environments.

Like the protobuf contract in gRPC or the cache contract in caching, a config type is a boundary contract. It says which runtime values the application expects and what shape those values must have.

### Configuration as a Graph Dependency { #configuration-graph-dependency }

In Kora, configuration is part of the dependency graph. A component can request a typed config object in its constructor just like it requests a repository or client. That makes configuration
dependencies visible and testable. It also keeps configuration parsing at the boundary of the graph instead of scattered across application code.

The practical flow is:

1. add the YAML configuration module
2. define a fixed application config source
3. bind required and defaulted values
4. define a reusable value extractor
5. reuse one config shape for multiple library settings
6. run the app and inspect resolved configuration

## Dependencies { #dependencies }

Add the YAML module to your existing project and keep logging enabled so startup behavior is visible while you learn.

===! ":fontawesome-brands-java: `Java`"

    Update `build.gradle`:

    ```groovy title="build.gradle"
    plugins {
        id "application"
    }

    dependencies {
        implementation "ru.tinkoff.kora:config-yaml"
        implementation "ru.tinkoff.kora:logging-logback"
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update `build.gradle.kts`:

    ```kotlin title="build.gradle.kts"
    plugins {
        id("application")
    }

    dependencies {
        implementation("ru.tinkoff.kora:config-yaml")
        implementation("ru.tinkoff.kora:logging-logback")
    }
    ```

Why this matters:

- `config-yaml` enables YAML file loading in the application graph
- `logging-logback` keeps startup and troubleshooting visible while the app runs

## Modules { #modules }

Start with the smallest possible application graph that can load YAML config and run a Kora application.

At this point we are not adding application-specific configuration yet. We are only preparing the graph so later steps can bind typed config and print resolved values.

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/guide/config/yaml/Application.java`:

    ```java
    package ru.tinkoff.kora.guide.config.yaml;

    import ru.tinkoff.kora.application.graph.KoraApplication;
    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.config.yaml.YamlConfigModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
            YamlConfigModule,  // <----- Connected module
            LogbackModule {

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/guide/config/yaml/Application.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.config.yaml

    import ru.tinkoff.kora.application.graph.KoraApplication
    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.config.yaml.YamlConfigModule
    import ru.tinkoff.kora.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        YamlConfigModule,  // <----- Connected module
        LogbackModule

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

Why this matters:

- `YamlConfigModule` activates YAML-based configuration loading
- `LogbackModule` adds basic startup and troubleshooting logs
- the graph stays minimal for now: it can start the application and read the config file

Typed sections are introduced gradually: first the application section, then a reusable library shape, and only after that the explicit mapping from `libs.lib1` and `libs.lib2` to two instances of the same type.

If you want more background on graph wiring and factories, see the [Container documentation](../documentation/container.md).

## Application Configuration { #app-config }

Now introduce the first typed config contract: a stable application section named `app`.

This is the simplest and most common config pattern in Kora. Instead of reading keys manually, you declare the shape once and inject it wherever it is needed.

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/guide/config/yaml/AppConfig.java`:

    ```java
    package ru.tinkoff.kora.guide.config.yaml;

    import ru.tinkoff.kora.config.common.annotation.ConfigSource;

    @ConfigSource("app")
    public interface AppConfig {

        String name();

        String version();

        String environment();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/guide/config/yaml/AppConfig.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.config.yaml

    import ru.tinkoff.kora.config.common.annotation.ConfigSource

    @ConfigSource("app")
    interface AppConfig {
        fun name(): String
        fun version(): String
        fun environment(): String
    }
    ```

Why this matters:

- `@ConfigSource("app")` makes the `app` section a first-class dependency
- the contract stays close to the code that consumes it
- refactoring config keys becomes safer because the structure is explicit in one place

## Required Values { #required-values }

With `AppConfig` defined, we can now decide which values are mandatory and which can fall back to defaults.

Update `src/main/resources/application.yaml`:

```yaml title="src/main/resources/application.yaml"
app:
    name: ${APP_NAME:Task Management App}
    version: ${APP_VERSION}
    environment: "development"
```

What this means:

- `version: ${APP_VERSION}` is required, so startup fails if `APP_VERSION` is missing
- `name: ${APP_NAME:Task Management App}` uses `APP_NAME` when it exists and otherwise falls back to the default value
- `environment` stays a normal static value because this guide does not need to vary it yet

This is an important YAML pattern: make critical values fail fast, but keep cosmetic or environment-specific values easy to override.

For more on substitution rules and supported value types, see the [Configuration documentation](../documentation/config.md).

## Library Configuration { #library-config }

Next, create a reusable config shape for one library.

Imagine that an abstract library needs two settings:

- `endpoint`
- `requestTimeout`

Instead of keeping those as raw keys, define them once as a type.

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/guide/config/yaml/LibConfig.java`:

    ```java
    package ru.tinkoff.kora.guide.config.yaml;

    import java.time.Duration;
    import ru.tinkoff.kora.config.common.annotation.ConfigValueExtractor;

    @ConfigValueExtractor
    public interface LibConfig {

        String endpoint();

        Duration requestTimeout();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/guide/config/yaml/LibConfig.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.config.yaml

    import java.time.Duration
    import ru.tinkoff.kora.config.common.annotation.ConfigValueExtractor

    @ConfigValueExtractor
    interface LibConfig {
        fun endpoint(): String
        fun requestTimeout(): Duration
    }
    ```

Now that `LibConfig` exists, return to the application graph and show explicitly where the two library configs come from.

`@ConfigValueExtractor` generates an extractor for the `LibConfig` shape, and the graph methods choose concrete branches of the config file. This gives Kora two different instances of the same type: one for `libs.lib1` and one for `libs.lib2`.

===! ":fontawesome-brands-java: `Java`"

    Update `src/main/java/ru/tinkoff/kora/guide/config/yaml/Application.java`:

    ```java
    package ru.tinkoff.kora.guide.config.yaml;

    import ru.tinkoff.kora.application.graph.KoraApplication;
    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.common.Tag;
    import ru.tinkoff.kora.config.common.Config;
    import ru.tinkoff.kora.config.common.extractor.ConfigValueExtractor;
    import ru.tinkoff.kora.config.yaml.YamlConfigModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;

    @KoraApp
    public interface Application extends
            YamlConfigModule,  // <----- Connected module
            LogbackModule {

        final class Lib1Tag {
            private Lib1Tag() {}
        }

        final class Lib2Tag {
            private Lib2Tag() {}
        }

        @Tag(Lib1Tag.class)
        default LibConfig lib1Config(Config config, ConfigValueExtractor<LibConfig> extractor) {
            return extractor.extract(config.get("libs.lib1"));
        }

        @Tag(Lib2Tag.class)
        default LibConfig lib2Config(Config config, ConfigValueExtractor<LibConfig> extractor) {
            return extractor.extract(config.get("libs.lib2"));
        }

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Update `src/main/kotlin/ru/tinkoff/kora/guide/config/yaml/Application.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.config.yaml

    import ru.tinkoff.kora.application.graph.KoraApplication
    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.common.Tag
    import ru.tinkoff.kora.config.common.Config
    import ru.tinkoff.kora.config.common.extractor.ConfigValueExtractor
    import ru.tinkoff.kora.config.yaml.YamlConfigModule
    import ru.tinkoff.kora.logging.logback.LogbackModule

    @KoraApp
    interface Application :
        YamlConfigModule,  // <----- Connected module
        LogbackModule {

        class Lib1Tag private constructor()
        class Lib2Tag private constructor()

        @Tag(Lib1Tag::class)
        fun lib1Config(config: Config, extractor: ConfigValueExtractor<LibConfig>): LibConfig {
            return extractor.extract(config.get("libs.lib1"))
        }

        @Tag(Lib2Tag::class)
        fun lib2Config(config: Config, extractor: ConfigValueExtractor<LibConfig>): LibConfig {
            return extractor.extract(config.get("libs.lib2"))
        }
    }

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

What happens here:

- `Lib1Tag` and `Lib2Tag` distinguish two `LibConfig` instances in the graph
- `config.get("libs.lib1")` and `config.get("libs.lib2")` select different config branches
- `ConfigValueExtractor<LibConfig>` converts each branch into a typed object

Add the first library section to `application.yaml`:

```yaml title="src/main/resources/application.yaml"
app:
    name: ${APP_NAME:Task Management App}
    version: ${APP_VERSION}
    environment: "development"

libs:
    lib1:
        endpoint: "https://integration.local/api"
        requestTimeout: "5s"
```

At this stage, `LibConfig` is only used for `lib1`. The application graph extracts it from `libs.lib1`, and Kora converts `"5s"` directly into `Duration`.

## Configuration file { #config-file }

Now suppose a second library needs exactly the same shape.

You could duplicate the whole config block, but YAML plus Kora substitutions gives you a better option: place shared scalar values in one section and reference those values where needed.

Update `application.yaml` again:

```yaml title="src/main/resources/application.yaml"
app:
    name: ${APP_NAME:Task Management App}
    version: ${APP_VERSION}
    environment: "development"

commonLib:
    endpoint: "https://integration.local/api"
    requestTimeout: "5s"

libs:
    lib1:
        endpoint: ${commonLib.endpoint}
        requestTimeout: ${commonLib.requestTimeout}
    lib2:
        endpoint: "https://integration-2.local/api"
        requestTimeout: ${commonLib.requestTimeout}
```

What changed:

- `commonLib` stores shared scalar values once
- `libs.lib1` references both shared values
- `libs.lib2` overrides only `endpoint`
- `libs.lib2.requestTimeout` still reuses the shared timeout

This is the payoff of combining YAML reuse with `@ConfigValueExtractor`: one config shape, multiple extracted instances, minimal duplication.

## Resolved Values { #resolved-values }

The last step is to prove that everything was injected correctly.

Instead of adding an HTTP endpoint, this guide uses a small `@Root` component that prints all resolved values to standard output during startup. This mirrors the console-style validation used in the
dependency injection guide.

===! ":fontawesome-brands-java: `Java`"

    Create `src/main/java/ru/tinkoff/kora/guide/config/yaml/ConfigRunner.java`:

    ```java
    package ru.tinkoff.kora.guide.config.yaml;

    import java.util.LinkedHashMap;
    import java.util.Map;
    import ru.tinkoff.kora.application.graph.Lifecycle;
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.Tag;
    import ru.tinkoff.kora.common.annotation.Root;

    @Root
    @Component
    public final class ConfigRunner implements Lifecycle {

        private final AppConfig appConfig;
        private final LibConfig lib1Config;
        private final LibConfig lib2Config;

        public ConfigRunner(
            AppConfig appConfig,
            @Tag(Application.Lib1Tag.class) LibConfig lib1Config,
            @Tag(Application.Lib2Tag.class) LibConfig lib2Config
        ) {
            this.appConfig = appConfig;
            this.lib1Config = lib1Config;
            this.lib2Config = lib2Config;
        }

        public Map<String, String> snapshot() {
            Map<String, String> values = new LinkedHashMap<>();
            values.put("name", this.appConfig.name());
            values.put("version", this.appConfig.version());
            values.put("environment", this.appConfig.environment());
            values.put("lib1.endpoint", this.lib1Config.endpoint());
            values.put("lib1.requestTimeout", this.lib1Config.requestTimeout().toString());
            values.put("lib2.endpoint", this.lib2Config.endpoint());
            values.put("lib2.requestTimeout", this.lib2Config.requestTimeout().toString());
            return values;
        }

        @Override
        public void init() {
            System.out.println("Config guide start");
            this.snapshot().forEach((key, value) -> System.out.println(key + "=" + value));
        }

        @Override
        public void release() {
            System.out.println("Application shutdown");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Create `src/main/kotlin/ru/tinkoff/kora/guide/config/yaml/ConfigRunner.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.config.yaml

    import ru.tinkoff.kora.application.graph.Lifecycle
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.Tag
    import ru.tinkoff.kora.common.annotation.Root

    @Root
    @Component
    class ConfigRunner(
        private val appConfig: AppConfig,
        @Tag(Application.Lib1Tag::class) private val lib1Config: LibConfig,
        @Tag(Application.Lib2Tag::class) private val lib2Config: LibConfig,
    ) : Lifecycle {

        fun snapshot(): Map<String, String> {
            return linkedMapOf(
                "name" to appConfig.name(),
                "version" to appConfig.version(),
                "environment" to appConfig.environment(),
                "lib1.endpoint" to lib1Config.endpoint(),
                "lib1.requestTimeout" to lib1Config.requestTimeout().toString(),
                "lib2.endpoint" to lib2Config.endpoint(),
                "lib2.requestTimeout" to lib2Config.requestTimeout().toString(),
            )
        }

        override fun init() {
            println("Config guide start")
            snapshot().forEach { (key, value) -> println("$key=$value") }
        }

        override fun release() {
            println("Application shutdown")
        }
    }
    ```

Why this matters:

- `@Root` ensures the runner is actually created when the application starts
- `Lifecycle` gives you a natural place to print or validate injected values
- `snapshot()` keeps the runtime output and the tests aligned around one contract

## Run Application { #run-app }

Use the standard guide flow:

```bash
./gradlew clean classes
./gradlew test
./gradlew run
```

In the runnable sample, `run` injects `APP_VERSION` from `koraVersion` in `gradle.properties`, so ordinary `./gradlew run` works out of the box.

If you want to override the application name too, add `APP_NAME` before startup:

```bash
APP_NAME="Custom Task App" ./gradlew run
```

## Application Output { #output }

When the application starts, it should print output similar to this:

```text
Config guide start
name=Task Management App
version=1.0.0
environment=development
lib1.endpoint=https://integration.local/api
lib1.requestTimeout=PT5S
lib2.endpoint=https://integration-2.local/api
lib2.requestTimeout=PT5S
```

If you provide `APP_NAME`, the printed `name=` line should reflect the override.

## Prod configuration { #config-2 }

A common next step is to keep separate config files for different environments such as development, staging, or production.

For example, create `src/main/resources/application-prod.yaml`:

```yaml
app:
    name: ${APP_NAME:Task Management App}
    version: ${APP_VERSION}
    environment: "production"

commonLib:
    endpoint: "https://integration.local/api"
    requestTimeout: "5s"

libs:
    lib1:
        endpoint: ${commonLib.endpoint}
        requestTimeout: ${commonLib.requestTimeout}
    lib2:
        endpoint: "https://integration-2.local/api"
        requestTimeout: ${commonLib.requestTimeout}
```

This file keeps the same shape as `application.yaml` and changes only the environment value. YAML configuration is selected through Kora's `config.resource` property, so the alternative resource
should be complete enough to start the app on its own.

You can run the application with that config by passing Kora's `config.resource` system property:

```bash
./gradlew run -Dconfig.resource=application-prod.yaml
```

With that override in place, the startup output should print:

```text
environment=production
```

For more on file resolution and external config files, see the [Configuration documentation](../documentation/config.md).

## Best Practices { #best-practices }

- Use `@ConfigSource` for stable application-level config that belongs to one well-known section.
- Use `@ConfigValueExtractor` when the same config shape is reused under multiple paths.
- Keep required values explicit with `${VAR_NAME}` and defaults explicit with `${VAR_NAME:default}`.
- Prefer shared YAML sections plus Kora substitutions over copying the same scalar values across several sections.
- Keep startup diagnostics simple while exploring configuration behavior; `System.out.println(...)` is enough for learning flows.

## Summary { #summary }

You now have a working YAML-based Kora application that binds configuration in two ways. `AppConfig` maps a stable `app` section, while `LibConfig` is extracted twice from two different paths with
different tags. YAML reuse keeps the file compact, and one override changes only the second library endpoint.

## Key Concepts { #key-concepts }

**`@ConfigSource`:**

- maps one fixed config section to a type-safe interface
- works well for application settings like `app.name` and `app.environment`

**Required vs Defaulted Values:**

- `${APP_VERSION}` is required and fails fast when missing
- `${APP_NAME:Task Management App}` uses an environment value when present and otherwise falls back to the configured default

**`@ConfigValueExtractor` and Reuse:**

- one config shape can be extracted from multiple paths
- a shared section such as `commonLib` can hold scalar defaults once
- substitutions such as `${commonLib.requestTimeout}` reuse those scalar defaults in multiple typed config sections

## Troubleshooting { #troubleshooting }

**Application fails at startup with an unresolved substitution:**

`app.version: ${APP_VERSION}` is mandatory. In the runnable sample, `run` provides it automatically from `koraVersion`. If you remove that Gradle wiring, you must set `APP_VERSION` before startup.

**`APP_NAME` does not change the default name:**

Use the defaulted substitution form:

```yaml
name: ${APP_NAME:Task Management App}
```

**Library config values are duplicated across sections:**

Move the shared scalar values into a section such as `commonLib` and reference them with substitutions like `${commonLib.requestTimeout}` instead of copying the same value into both libraries.

**Build hangs or fails unexpectedly:**

Stop Gradle daemons and retry:

```bash
./gradlew --stop
./gradlew clean classes
```

**`AccessDeniedException` in the Gradle cache on Windows:**

If cached files are locked by another process, retry with a fresh session cache:

```bash
GRADLE_USER_HOME=.gradle-user-home ./gradlew test
```

## What's Next? { #whats-next }

- [HOCON Configuration](config-hocon.md) to compare YAML with Kora's common HOCON-based setup.
- [JSON Processing](json.md) to make request and response DTOs explicit in the small application you already have.
- [Build an HTTP Server](http-server.md) after JSON, because that guide builds on JSON DTO mapping and turns the app into a fuller HTTP API.
- [Learn Dependency Injection Basics](dependency-injection-introduction.md) if the generated graph and config factories still feel unclear.

## Help { #help }

If you encounter issues:

- compare with [Kora Java Config YAML App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-config-yaml-app) and [Kora Kotlin Config YAML App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-config-yaml-app)
- check the [Configuration documentation](../documentation/config.md)
- check the [Container documentation](../documentation/container.md)
- read the [YAML specification](https://yaml.org/spec/)
