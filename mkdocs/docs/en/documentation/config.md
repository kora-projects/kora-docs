---
description: "Explains Kora configuration system for HOCON and YAML, typed config extraction, config injection, config sources, watchers, and supported value types. Use when working with @ConfigSource, @ConfigValueExtractor, @Environment, @SystemProperties, Config, HoconConfigModule, YamlConfigModule."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora configuration system for HOCON and YAML, typed config extraction, config injection, config sources, watchers, and supported value types; key triggers include @ConfigSource, @ConfigValueExtractor, @Environment, @SystemProperties, Config, HoconConfigModule, YamlConfigModule."
---

The configuration module reads application settings from `HOCON` or `YAML` files, environment variables, `Java` system
properties, and maps them to typed classes in `Kora`. The resulting configuration objects become regular dependency
graph components and can be injected into services, clients, servers, and other integrations.

In `Kora`, application configuration is usually described by an interface annotated with `@ConfigSource`: the path in
the file points to the section to read, and the interface methods describe required values, optional values, and defaults.
Libraries and reusable configuration shapes use `@ConfigValueExtractor`, which creates only the extraction rule, while
the concrete path is selected in the library module.

For a step-by-step walkthrough before the reference details, see [HOCON Configuration](../guides/config-hocon.md) and [YAML Configuration](../guides/config-yaml.md).

## HOCON { #hocon }

Support for [HOCON](https://github.com/lightbend/config/blob/master/HOCON.md) is implemented with [Typesafe Config](https://github.com/lightbend/config).
`HOCON` is a `JSON`-based configuration file format. It is less strict than `JSON` and supports substitutions, defaults,
and a convenient syntax for nested objects.

```javascript
services {
    foo {
      bar = "SomeValue" //(1)!
      baz = 10 //(2)!
      propRequired = ${REQUIRED_ENV_VALUE} //(3)!
      propOptional = ${?OPTIONAL_ENV_VALUE} //(4)!
      propDefault = 10
      propDefault = ${?NON_DEFAULT_ENV_VALUE} //(5)!
      propReference = ${services.foo.bar}Other${services.foo.baz} //(6)!
      propArray = ["v1", "v2"] //(7)!
      propArrayAsString = "v1, v2" //(8)!
      propMap = { //(9)!
          "k1" = "v1"
          "k2" = "v2"
      }
      propObject = { //(10)!
          p1 = "v1"
          p2 = "v2"
      }
      propObjects = [ //(11)!
        {
          p1 = "v1"
          p2 = "v2"
        },
        {
          p1 = "v3"
          p2 = "v4"
        }
      ]
    }
}
```

1. String configuration value
2. Numeric configuration value
3. Required configuration value substituted from the `REQUIRED_ENV_VALUE` environment variable
4. Optional configuration value substituted from the `OPTIONAL_ENV_VALUE` environment variable; if the variable is not found, the configuration value is omitted
5. Configuration value with a default: the default is specified as `propDefault = 10`, and `NON_DEFAULT_ENV_VALUE`, if found, replaces it
6. Configuration value assembled from substitutions of other configuration parts with the `Other` value between them
7.  String list configuration value; the value can be set as an array of strings or as a comma-separated string
8.  String list configuration value; the value can be set as a comma-separated string or as an array of strings
9.  Configuration value as a key-value dictionary
10. Configuration value as a mapped class
11. Configuration value as a list of mapped classes

Configuration representation in code:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @ConfigSource("services.foo")
    public interface FooConfig {

        String bar();

        Integer baz();

        String propRequired();

        @Nullable
        String propOptional();

        Integer propDefault();

        String propReference();

        List<String> propArray();

        List<String> propArrayAsString();

        Map<String, String> propMap();

        @ConfigValueExtractor
        public interface ObjectConfig {
            
            String p1();

            String p2();
        }

        ObjectConfig propObject();

        List<ObjectConfig> propObjects();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @ConfigSource("services.foo")
    interface FooConfig {

        fun bar(): String

        fun baz(): Int

        fun propRequired(): String

        fun propOptional(): String?

        fun propDefault(): Int

        fun propReference(): String

        fun propArray(): List<String>

        fun propArrayAsString(): List<String>

        fun propMap(): Map<String, String>

        @ConfigValueExtractor
        interface ObjectConfig {
            
            fun p1(): String

            fun p2(): String
        }

        fun propObject(): ObjectConfig

        fun propObjects(): List<ObjectConfig>
    }
    ```

### Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:config-hocon"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends HoconConfigModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:config-hocon")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : HoconConfigModule
    ```

### File { #file }

By default, the [`reference.conf` and `application.conf`](https://github.com/lightbend/config#note-about-resolving-substitutions-in-referenceconf-and-applicationconf) configuration files are expected.

First, all `reference.conf` files from the classpath are merged, then `application.conf` is overlaid on top of the
unresolved `reference.conf`, and after that the result is resolved and required substitutions are checked.

The application configuration is expected to be in `application.conf`, while library configuration is expected to be in `reference.conf`.

Application file selection priority for `HOCON`:

- Use the file from `config.resource` if specified (file from the `resources` directory)
- Use the file from `config.file` if specified (file from the file system)
- Use `application.conf` if present (file from the `resources` directory)
- Use an empty configuration if none of the above is present

Only one property can be specified at the same time: `config.resource` or `config.file`. If both properties are specified,
the application will fail on startup.

===! ":fontawesome-brands-java: `java`"

    Example of specifying configuration on startup through `java`:
    ```shell
    java -Dconfig.file=path/to/configFile application
    ```

=== ":simple-kotlin: `gradle`"

    Example of specifying configuration in `build.gradle`:
    ```groovy
    run {
        jvmArgs += [
                "-Dconfig.file=path/to/configFile"
        ]
    }
    ```

## YAML { #yaml }

Support for [YAML](https://yaml.org/) is implemented using [SnakeYAML](https://github.com/snakeyaml/snakeyaml).

```yaml
services:
    foo:
        bar: "SomeValue" #(1)!
        baz: 10 #(2)!
        propRequired: ${REQUIRED_ENV_VALUE} #(3)!
        propOptional: ${?OPTIONAL_ENV_VALUE} #(4)!
        propDefault: ${?NON_DEFAULT_ENV_VALUE:10} #(5)!
        propReference: ${services.foo.bar}Other${services.foo.baz} #(6)!
        propArray: ["v1", "v2"] #(7)!
        propArrayAsString: "v1, v2" #(8)!
        propMap: #(9)!
            k1: "v1"
            k2: "v2"
        propObject: #(10)!
            p1: "v1"
            p2: "v2"
        propObjects: #(11)!
            - p1: "v1"
              p2: "v2"
            - p1: "v1"
              p2: "v2"
```

1. String configuration value
2. Numeric configuration value
3. Required configuration value substituted from the `REQUIRED_ENV_VALUE` environment variable
4. Optional configuration value substituted from the `OPTIONAL_ENV_VALUE` environment variable; if the variable is not found, the configuration value is omitted
5. Configuration value with a default: the default is `10`, and `NON_DEFAULT_ENV_VALUE`, if found, replaces it
6. Configuration value assembled from substitutions of other configuration parts with the `Other` value between them
7.  String list configuration value; the value can be set as an array of strings or as a comma-separated string
8.  String list configuration value; the value can be set as a comma-separated string or as an array of strings
9.  Configuration value as a key-value dictionary
10. Configuration value as a mapped class
11. Configuration value as a list of mapped classes

Configuration representation in code:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @ConfigSource("services.foo")
    public interface FooConfig {

        String bar();

        Integer baz();

        String propRequired();

        @Nullable
        String propOptional();

        Integer propDefault();

        String propReference();

        List<String> propArray();

        List<String> propArrayAsString();

        Map<String, String> propMap();

        @ConfigValueExtractor
        public interface ObjectConfig {
            
            String p1();

            String p2();
        }

        ObjectConfig propObject();

        List<ObjectConfig> propObjects();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @ConfigSource("services.foo")
    interface FooConfig {

        fun bar(): String

        fun baz(): Int

        fun propRequired(): String

        fun propOptional(): String?

        fun propDefault(): Int

        fun propReference(): String

        fun propArray(): List<String>

        fun propArrayAsString(): List<String>

        fun propMap(): Map<String, String>

        @ConfigValueExtractor
        interface ObjectConfig {
            
            fun p1(): String

            fun p2(): String
        }

        fun propObject(): ObjectConfig

        fun propObjects(): List<ObjectConfig>
    }
    ```

### Dependency { #dependency-2 }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:config-yaml"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends YamlConfigModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:config-yaml")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : YamlConfigModule
    ```

### File { #file-2 }

By default, the `reference.yaml` and `application.yaml` configuration files are expected.

First, all `reference.yaml` files from the classpath are merged, then `application.yaml` is overlaid on top of
`reference.yaml`, and after that the result is resolved and required substitutions are checked.

The application configuration is expected to be in `application.yaml`, while library configuration is expected to be in `reference.yaml`.

Application file selection priority for `YAML`:

- Use the file from `config.resource` if specified (file from the `resources` directory)
- Use the file from `config.file` if specified (file from the file system)
- Use `application.yaml` if present (file from the `resources` directory)
- Use an empty configuration if none of the above is present

Only one property can be specified at the same time: `config.resource` or `config.file`. If both properties are specified,
the application will fail on startup.

===! ":fontawesome-brands-java: `java`"

    Example of specifying configuration on startup through `java`:
    ```shell
    java -Dconfig.file=path/to/configFile application
    ```

=== ":simple-kotlin: `gradle`"

    Example of specifying configuration in `build.gradle`:
    ```groovy
    run {
        jvmArgs += [
                "-Dconfig.file=path/to/configFile"
        ]
    }
    ```

## Custom configuration { #custom-configuration }

A custom configuration maps a configuration file section to a user type.
That type can then be injected as a dependency just like any other component.

### Application config { #application-config }

Use the `@ConfigSource` annotation to create custom configurations in an application.
It generates a `ConfigValueExtractor` for the interface and a module that adds the ready configuration object to the
dependency graph. The annotation value points to the section path inside the resulting configuration:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @ConfigSource("services.foo")
    public interface FooServiceConfig {

        String bar();
        
        int baz();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @ConfigSource("services.foo")
    interface FooServiceConfig {

        fun bar(): String

        fun baz(): Int
    }
    ```

This code sample will add an instance of the `FooServiceConfig` class to the dependency container, which when created will expect the following kind of configuration:

===! ":material-code-json: `Hocon`"

    ```javascript
    services {
      foo {
        bar = "SomeValue"
        baz = 10
      }
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    services:
      foo:
        bar: "SomeValue"
        baz: 10
    ```

After that, the `FooServiceConfig` class can already be used as a dependency in other classes:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class FooService {

        private final FooServiceConfig config;

        public FooService(FooServiceConfig config) {
            this.config = config;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class FooService(val config: FooServiceConfig)
    ```

### Library config { #library-config }

Use the `@ConfigValueExtractor` annotation to create custom configurations in libraries.
It creates a rule for extracting a value from `ConfigValue<?>`, but does not bind it to a concrete configuration path.
The path is selected in a library module factory method, so the same configuration shape can be reused for different sections.
`@ConfigValueExtractor` can be used on a `Java` interface, `record`, or class, and on a `Kotlin` interface or `data class`.

The annotation has the `mapNullAsEmptyObject` parameter (default: `true`). When enabled, a missing section is treated
as an empty object: required fields still fail, while optional fields and defaults behave as if an empty section was present.
If `mapNullAsEmptyObject = false`, a missing section is treated as `null` for the whole configuration object.

Consider this configuration class:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @ConfigValueExtractor
    public interface FooLibraryConfig {

        String bar();
        
        int baz();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @ConfigValueExtractor
    interface FooLibraryConfig {

        fun bar(): String

        fun baz(): Int
    }
    ```

For the library to provide configuration, implement a factory in a module:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface FooLibraryModule {

        default FooLibraryConfig config(Config config, ConfigValueExtractor<FooLibraryConfig> extractor) {
            return extractor.extract(config.get("library.foo"));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface FooLibraryModule {

        fun config(config: Config, extractor: ConfigValueExtractor<FooLibraryConfig>): FooLibraryConfig {
            return extractor.extract(config["library.foo"])!!
        }
    }
    ```

The factory will expect a configuration of the following kind:

===! ":material-code-json: `Hocon`"

    ```javascript
    library {
      foo {
        bar = "SomeValue"
        baz = 10
      }
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    library:
      foo:
        bar: "SomeValue"
        baz: 10
    ```

Then, after connecting `FooLibraryModule` in the application, `FooLibraryConfig` can be used as a dependency in other classes.

### Required values { #required-values }

By default, all values declared in the configuration are considered **required** (`NotNull`) and must be present in the
resulting configuration. If a required value is missing or has the `null` value, the application will fail while creating
the configuration object.

### Optional values { #optional-values }

If you need to specify a value from the configuration file as optional, you can use this format:

===! ":fontawesome-brands-java: `Java`"

    It is suggested to use the `@Nullable` annotation over the method signature:

    ```java
    @ConfigSource("services.foo")
    public interface FooServiceConfig {

        @Nullable//(1)!
        String bar();

        int baz();
    }
    ```

    1.  Any `@Nullable` annotation will do, for example `javax.annotation.Nullable` / `jakarta.annotation.Nullable` / `org.jetbrains.annotations.Nullable`.

=== ":simple-kotlin: `Kotlin`"

    Use [`Kotlin` null-safety](https://kotlinlang.org/docs/null-safety.html) syntax and mark the parameter as nullable:

    ```kotlin
    @ConfigSource("services.foo")
    interface FooServiceConfig {

        fun bar(): String?

        fun baz(): Int
    }
    ```

### Default values { #default-values }

If you need to set a default value in configuration mapping, use a `default` method:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @ConfigSource("services.foo")
    public interface FooServiceConfig {

        String bar();

        default int baz() {
            return 42;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @ConfigSource("services.foo")
    interface FooServiceConfig {

        fun bar(): String

        fun baz(): Int {
            return 42
        }
    }
    ```

### Recommended style { #recommended-configuration-style }

It is usually more convenient to describe configuration as a separate type for a concrete integration or subsystem:
an HTTP client, an external service connection, a queue handler, and so on. Such a type should clearly separate required
values, optional values, and values that come from environment variables.

In the example below:

1. `baseUrl` is a required value from the configuration file
2. `clientName` is an optional value from the `ORDERS_CLIENT_NAME` environment variable
3. `token` is a required value from the `ORDERS_API_TOKEN` environment variable
4. `requestTimeout` has the `2s` default value and can be overridden by the optional `ORDERS_REQUEST_TIMEOUT` environment variable

===! ":fontawesome-brands-java: `Java`"

    ```java
    import java.time.Duration;
    import javax.annotation.Nullable;

    @ConfigSource("clients.orders")
    public interface OrdersClientConfig {

        String baseUrl();

        @Nullable
        String clientName();

        String token();

        Duration requestTimeout();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import java.time.Duration

    @ConfigSource("clients.orders")
    interface OrdersClientConfig {

        fun baseUrl(): String

        fun clientName(): String?

        fun token(): String

        fun requestTimeout(): Duration
    }
    ```

===! "`HOCON`"

    ```javascript
    clients {
      orders {
        baseUrl = "https://orders.example.com"
        clientName = ${?ORDERS_CLIENT_NAME}
        token = ${ORDERS_API_TOKEN}
        requestTimeout = 2s
        requestTimeout = ${?ORDERS_REQUEST_TIMEOUT}
      }
    }
    ```

=== "`YAML`"

    ```yaml
    clients:
      orders:
        baseUrl: "https://orders.example.com"
        clientName: ${?ORDERS_CLIENT_NAME}
        token: ${ORDERS_API_TOKEN}
        requestTimeout: ${?ORDERS_REQUEST_TIMEOUT:2s}
    ```

This keeps the configuration structure readable: required settings are visible in the configuration type, secrets can be
passed through environment variables, and safe defaults stay directly in the configuration file.

## Injecting configuration { #injecting-configuration }

You can inject the base class `ru.tinkoff.kora.config.common.Config`, which represents the configuration tree and gives
access to values through the `get(...)` method. The resulting configuration consists of several layers:

- Environment variables
- `Java` system properties
- Configuration file

Layers are merged in this order: environment variables, then system properties, then the application configuration file.
Each next layer overlays the previous one.

### Environment variables { #environment-variables }

If you need to inject configuration that contains **only** [environment variables](https://en.wikipedia.org/wiki/Environment_variable),
use the `@Environment` annotation as a tag for the configuration class:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class FooService {

        private final Config config;

        public FooService(@Environment Config config) {
            this.config = config;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class FooService(@Environment val config: Config)
    ```

### System properties { #system-variables }

If you need to inject configuration that contains **only** [`Java` system properties](https://www.baeldung.com/java-system-get-property-vs-system-getenv),
use the `@SystemProperties` annotation as a tag for the configuration class:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class FooService {

        private final Config config;

        public FooService(@SystemProperties Config config) {
            this.config = config;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class FooService(@SystemProperties val config: Config)
    ```

### Configuration file { #configuration-file }

If you need to inject application configuration that consists **only** of the configuration file,
use the `@ApplicationConfig` annotation as a tag for the configuration class:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class FooService {

        private final Config config;

        public FooService(@ApplicationConfig Config config) {
            this.config = config;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class FooService(@ApplicationConfig val config: Config)
    ```

### Resulting configuration { #resulting-configuration }

If you need to inject the complete resulting application configuration, which consists of the configuration file,
environment variables and system properties, simply inject the configuration class without a tag:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class FooService {

        private final Config config;

        public FooService(Config config) {
            this.config = config;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class FooService(val config: Config)
    ```

### Recommendations { #recommendations }

???+ warning "Recommendation"

    **We do not recommend** using `ru.tinkoff.kora.config.common.Config` directly as a dependency in components,
    because when configuration is updated, all graph components that use it will be updated as well.
    We recommend always creating [custom configurations](#custom-configuration).

## Config Watcher { #config-watcher }

By default, `Kora` has a configuration file watcher that checks the application file for changes and starts dependency
graph refresh if the file changes. The check runs every `1000` milliseconds.

For `HOCON`, the watcher also tracks files included through `include` inside the main configuration file.
If such an included file changes, the configuration is reread and the dependency graph is refreshed as well.

The watcher works only for file-based configuration that has a trackable source. If configuration came from a resource
inside an archive or was built without an application file, there is nothing on disk to update.

You can disable the watcher by using:

1. Environment variable `KORA_CONFIG_WATCHER_ENABLED` (default: `true`)
2. System property `kora.config.watcher.enabled` (default: `true`)

## Supported types { #supported-types }

Configuration extractors provide an extensive list of supported types that covers most values you may need in custom
configurations. If the standard conversion is not enough, the behavior can be extended with a custom
`ConfigValueExtractor<T>` component.

??? abstract "List of supported types"

    * boolean / Boolean
    * short / Short
    * int / Integer
    * long / Long
    * double / Double
    * float / Float
    * double[]
    * String
    * BigInteger
    * BigDecimal
    * Period
    * Duration
    * Size
    * Properties
    * Pattern
    * UUID
    * LocalDate
    * LocalTime
    * LocalDateTime
    * OffsetTime
    * OffsetDateTime
    * ConfigValue.ObjectValue
    * Enum (any custom `enum`; mapping can be overridden through `toString()`)
    * `Optional<T>` (where `T` is any supported type)
    * `List<T>` (where `T` is any supported type)
    * `Set<T>` (where `T` is any supported type)
    * `Map<String, V>` or `Map<K, V>` (where `K` and `V` are supported by corresponding extractors)
    * `Either<A, B>` (where `A` and `B` are any supported types)

### Custom extractor { #custom-extractor }

If there is no standard conversion for a type or special parsing logic is required, add a custom
`ConfigValueExtractor<T>` component. The `extract(...)` method receives the configuration value as `ConfigValue<?>`
and must return the ready value of the required type.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class TokenConfigValueExtractor implements ConfigValueExtractor<Token> {

        @Override
        public Token extract(ConfigValue<?> value) {
            if (value instanceof ConfigValue.NullValue) {
                return null;
            }
            return new Token(value.asString());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class TokenConfigValueExtractor : ConfigValueExtractor<Token> {

        override fun extract(value: ConfigValue<*>): Token? {
            if (value is ConfigValue.NullValue) {
                return null
            }
            return Token(value.asString())
        }
    }
    ```

If a specific extractor should be used only for one field, specify it through `@Mapping`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @ConfigValueExtractor
    public interface ApiConfig {

        @Mapping(TokenConfigValueExtractor.class)
        Token token();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @ConfigValueExtractor
    interface ApiConfig {

        @Mapping(TokenConfigValueExtractor::class)
        fun token(): Token
    }
    ```

### Duration { #duration }

`Duration` can be set as a number or a string.
If a number is specified, it is treated as milliseconds.
If a string is specified, the `java.time.Duration` format is supported, for example `PT10S`, as well as `HOCON` style:

- `500ms`
- `10 seconds`
- `2 minutes`
- `1h`
- `1d`

### Period { #period }

`Period` can be set as a number or a string.
If a number is specified, it is treated as days.
If a string is specified, these units are supported:

- `d` / `days`
- `w` / `weeks`
- `m` / `mo` / `months`
- `y` / `years`

For example, `7d`, `2 weeks`, `3mo`, or `1 year`.

### Size { #size }

`Size` is a special type that allows specifying byte sizes in a human-friendly notation: according to the
[IEEE 1541-2002](https://en.wikipedia.org/wiki/IEEE_1541-2002) standard (binary) or the
[SI](https://en.wikipedia.org/wiki/Binary_prefix) standard (decimal).

Example values:

- `1Mb` - 1 megabyte (`1.000.000` bytes)
- `1Mib` - 1 mebibyte (`1.048.576` bytes)
- `1024b` - 1024 bytes
- `1024` - 1024 bytes

If just a number without a suffix is specified, it is considered that bytes are specified.
