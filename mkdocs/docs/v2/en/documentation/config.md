---
description: "Explains the Kora configuration system for HOCON and YAML, typed configuration mapping, configuration injection, config sources, the config watcher, and supported value types. Use when working with @ConfigSource, @ConfigMapper, ConfigValueMapper, @EnvironmentConfig, @SystemPropertiesConfig, @ApplicationConfig, Config, HoconConfigModule, YamlConfigModule."
agent:
  use_when: "Use this file for Kora docs or implementation questions about the Kora configuration system for HOCON and YAML, typed configuration mapping, configuration injection, config sources, the config watcher, and supported value types; key triggers include @ConfigSource, @ConfigMapper, ConfigValueMapper, @EnvironmentConfig, @SystemPropertiesConfig, @ApplicationConfig, Config, HoconConfigModule, YamlConfigModule."
---

The configuration module reads application settings from `HOCON` or `YAML` files, environment variables, `Java` system
properties, and maps them to typed classes in `Kora`. The resulting configuration objects become regular dependency
graph components and can be injected into services, clients, servers, and other integrations.

In `Kora`, application configuration is usually described by an interface annotated with `@ConfigSource`: the path in
the file points to the section to read, and the interface methods describe required values, optional values, and defaults.
Libraries and reusable configuration shapes use `@ConfigMapper`, which creates only the mapping rule, while
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

Values can also reference other configuration keys (self-reference / cross-reference) via `${path}`, and environment
variables via `${VAR}` (required) or `${?VAR}` (optional). A default is expressed the `HOCON` way: assign the key twice,
first with the fallback literal and then with an optional substitution, as `propDefault` does above. Substitutions inside
a `HOCON` file are resolved by `Typesafe Config` after every layer of that file is merged, so a reference can point at a
key defined in another `HOCON` file pulled in through `include`.

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

        @ConfigMapper
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

        @ConfigMapper
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
    implementation "io.koraframework:config-hocon"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends HoconConfigModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:config-hocon")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : HoconConfigModule
    ```

### File { #file }

By default, the [`reference.conf` and `application.conf`](https://github.com/lightbend/config#note-about-resolving-substitutions-in-referenceconf-and-applicationconf) configuration files are expected.

First, all `reference.conf` files from the classpath are merged, then `application.conf` is overlaid on top of the
unresolved `reference.conf`, and `Java` system properties are overlaid on top of that. Only after the whole stack is
assembled is the result resolved and required substitutions are checked.

The application configuration is expected to be in `application.conf`, while library configuration is expected to be in `reference.conf`.

`HOCON` also supports the [`include`](https://github.com/lightbend/config/blob/master/HOCON.md#includes) directive:
files pulled in through `include` participate in the same merge and substitution resolution as the main file.
Includes that resolve to real files on disk are also tracked by the [Config Watcher](#config-watcher), so changing an
included file refreshes the graph too; includes that resolve to classpath resources or `URL`s are not tracked.

Application file selection priority for `HOCON`:

- Use the file from `config.resource` if specified (file from the `resources` directory)
- Use the file from `config.file` if specified (file from the file system)
- Use `application.conf` if present (file from the `resources` directory)
- Use an empty configuration if none of the above is present

Only one property can be specified at the same time: `config.resource` or `config.file`. If both properties are specified,
the application will fail on startup with `Application config source is ambiguous`.

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
        propDefault: ${NON_DEFAULT_ENV_VALUE:10} #(5)!
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

`YAML` has no substitution syntax of its own, so references are resolved by `Kora` itself once all configuration layers
are merged. Three forms are supported:

- `${path}` — required: the reference must resolve, otherwise the application fails on startup
- `${?path}` — optional: an unresolved reference yields no value, and the key behaves as if it were absent
- `${path:defaultValue}` — an unresolved reference falls back to `defaultValue`

The same forms work for environment variables and for references to other configuration keys, because environment
variables and system properties are configuration layers themselves. Several references can be embedded into one string,
as `propReference` does above.

???+ warning "Attention"

    The `?` and the default value cannot be combined: in `${?path:defaultValue}` the whole `path:defaultValue` text is
    treated as the reference name, and the key resolves to nothing. Use `${path:defaultValue}` — it already falls back
    when the reference is missing.

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

        @ConfigMapper
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

        @ConfigMapper
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
    implementation "io.koraframework:config-yaml"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends YamlConfigModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:config-yaml")
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

Every `reference.yaml` must be resolvable on its own, without the application file: it is validated at startup, and an
unresolvable reference fails the application with `Reference config ... cannot be resolved without external application config`.
Give such keys a literal default, make the reference optional with `${?path}`, or provide a fallback with `${path:defaultValue}`.

Application file selection priority for `YAML`:

- Use the file from `config.resource` if specified (file from the `resources` directory)
- Use the file from `config.file` if specified (file from the file system)
- Use `application.yaml` if present (file from the `resources` directory)
- Use an empty configuration if none of the above is present

Only one property can be specified at the same time: `config.resource` or `config.file`. If both properties are specified,
the application will fail on startup with `Application config source is ambiguous`.

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

Both `@ConfigSource` and `@ConfigMapper` generate a `ConfigValueMapper<T>` implementation at compile time.
The declaration shapes they accept are:

- `Java` — an `interface`, a `record`, or a class. A class must be non-abstract and must override both `equals` and `hashCode`
- `Kotlin` — an `interface` or a `data class`

Methods of a configuration interface describe fields, so they must take no parameters, must not be generic, and must
return a value. Anything else has to be a `default` method. Fields declared in super-interfaces are inherited into the
mapping.

### Application config { #application-config }

Use the `@ConfigSource` annotation to create custom configurations in an application.
It generates a `ConfigValueMapper` for the type and a module that adds the ready configuration object to the
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

Use the `@ConfigMapper` annotation to create custom configurations in libraries.
It creates a rule for mapping a `ConfigValue<?>` to the type, but does not bind it to a concrete configuration path.
The path is selected in a library module factory method, so the same configuration shape can be reused for different sections.

The annotation has the `mapNullAsEmptyObject` parameter (default: `true`). When enabled, a missing section is treated
as an empty object: required fields still fail, while optional fields and defaults behave as if an empty section was present.
If `mapNullAsEmptyObject = false`, a missing section is mapped to `null` for the whole configuration object.
A type annotated only with `@ConfigSource` always behaves as if `mapNullAsEmptyObject = true`.

Consider this configuration class:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @ConfigMapper
    public interface FooLibraryConfig {

        String bar();

        int baz();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @ConfigMapper
    interface FooLibraryConfig {

        fun bar(): String

        fun baz(): Int
    }
    ```

For the library to provide configuration, implement a factory in a module:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface FooLibraryModule {

        default FooLibraryConfig fooLibraryConfig(Config config, ConfigValueMapper<FooLibraryConfig> mapper) {
            return mapper.mapOrThrow(config.get("library.foo"));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface FooLibraryModule {

        fun fooLibraryConfig(config: Config, mapper: ConfigValueMapper<FooLibraryConfig>): FooLibraryConfig {
            return mapper.mapOrThrow(config.get("library.foo"))
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

`ConfigValueMapper<T>` has two reading methods: `map(...)` may return `null` — for a generated mapper that happens when
`mapNullAsEmptyObject = false` and the section is missing — while `mapOrThrow(...)` turns the same `null` into a
`ConfigValueException`. Factory methods normally use `mapOrThrow(...)`, because a missing library section is a startup
error rather than a valid state.

The same shape can be bound to several sections at once by adding a [tag](container.md#tags) to each factory method:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface FooLibraryModule {

        final class Lib1Tag {}

        final class Lib2Tag {}

        @Tag(Lib1Tag.class)
        default FooLibraryConfig lib1Config(Config config, ConfigValueMapper<FooLibraryConfig> mapper) {
            return mapper.mapOrThrow(config.get("libs.lib1"));
        }

        @Tag(Lib2Tag.class)
        default FooLibraryConfig lib2Config(Config config, ConfigValueMapper<FooLibraryConfig> mapper) {
            return mapper.mapOrThrow(config.get("libs.lib2"));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface FooLibraryModule {

        class Lib1Tag private constructor()

        class Lib2Tag private constructor()

        @Tag(Lib1Tag::class)
        fun lib1Config(config: Config, mapper: ConfigValueMapper<FooLibraryConfig>): FooLibraryConfig {
            return mapper.mapOrThrow(config.get("libs.lib1"))
        }

        @Tag(Lib2Tag::class)
        fun lib2Config(config: Config, mapper: ConfigValueMapper<FooLibraryConfig>): FooLibraryConfig {
            return mapper.mapOrThrow(config.get("libs.lib2"))
        }
    }
    ```

### Required values { #required-values }

By default, all values declared in the configuration are considered **required** and must be present in the
resulting configuration. If a required value is missing or has the `null` value, the application will fail while creating
the configuration object with `Config expected value, but got null at path: '...'`.

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

    1.  [JSpecify](https://jspecify.dev/) `org.jspecify.annotations.Nullable`, the annotation `Kora` itself is built on.

=== ":simple-kotlin: `Kotlin`"

    Use [`Kotlin` null-safety](https://kotlinlang.org/docs/null-safety.html) syntax and mark the parameter as nullable:

    ```kotlin
    @ConfigSource("services.foo")
    interface FooServiceConfig {

        fun bar(): String?

        fun baz(): Int
    }
    ```

`JSpecify` `@Nullable` is a *type-use* annotation, so for a qualified or generic type it is written immediately before
the type name rather than before the whole declaration:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @ConfigSource("services.foo")
    public interface FooServiceConfig {

        java.time.@Nullable Duration timeout();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @ConfigSource("services.foo")
    interface FooServiceConfig {

        fun timeout(): java.time.Duration?
    }
    ```

An `Optional<T>` return type is also supported (an absent value maps to `Optional.empty()`), but a `@Nullable` value
(or a `Kotlin` nullable type) is the recommended style.

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

Defaults are available for the other declaration forms too, but the mechanism differs by language: a `Kotlin`
`data class` takes them from constructor parameter defaults, while a `Java` class takes them from field
initializers and therefore needs a public no-argument constructor together with accessors:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @ConfigMapper
    public class FooServiceConfig {

        private String bar;
        private int baz = 42;

        public String getBar() {
            return this.bar;
        }

        public void setBar(String bar) {
            this.bar = bar;
        }

        public int getBaz() {
            return this.baz;
        }

        public void setBaz(int baz) {
            this.baz = baz;
        }

        @Override
        public boolean equals(Object o) {
            return o instanceof FooServiceConfig that
                && Objects.equals(this.bar, that.bar)
                && this.baz == that.baz;
        }

        @Override
        public int hashCode() {
            return Objects.hash(this.bar, this.baz);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @ConfigMapper
    data class FooServiceConfig(val bar: String, val baz: Int = 42)
    ```

A `Java` `record` has no default mechanism: every component is read as a required value unless it is marked
`@Nullable`. Use an interface with `default` methods when a record would need defaults.

### Validation { #validation }

A configuration type can additionally be checked by [validation](validation.md) constraints. Annotate it with `@Valid`
and put the constraints on the fields: the generated mapper calls the `Validator` right after the object is built,
so an invalid configuration fails the application on startup rather than at the first use.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Valid
    @ConfigSource("services.foo")
    public interface FooServiceConfig {

        @NotBlank
        String bar();

        @Range(from = 1.0, to = 65535.0)
        int port();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Valid
    @ConfigSource("services.foo")
    interface FooServiceConfig {

        @NotBlank
        fun bar(): String

        @Range(from = 1.0, to = 65535.0)
        fun port(): Int
    }
    ```

### Relaxed key names { #relaxed-key-names }

Configuration keys are matched with relaxed naming. A method name is compared against the key in the file not only in
its exact form, but also in its `kebab-case` and `snake_case` variants. This means a method `someBarString()` resolves
equally from `someBarString`, `some-bar-string`, or `some_bar_string` in the configuration file, so teams that prefer
kebab-case or snake_case keys can keep their style without renaming methods.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @ConfigMapper
    public interface BarConfig {

        String someBarString();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @ConfigMapper
    interface BarConfig {

        fun someBarString(): String
    }
    ```

All three key spellings below are read into `someBarString()`:

===! ":material-code-json: `Hocon`"

    ```javascript
    bar {
      someBarString = "value"        //(1)!
      # some-bar-string = "value"    //(2)!
      # some_bar_string = "value"    //(3)!
    }
    ```

    1. Exact `camelCase` spelling of the method name
    2. Relaxed `kebab-case` spelling
    3. Relaxed `snake_case` spelling

=== ":simple-yaml: `YAML`"

    ```yaml
    bar:
      someBarString: "value"         #(1)!
      # some-bar-string: "value"     #(2)!
      # some_bar_string: "value"     #(3)!
    ```

    1. Exact `camelCase` spelling of the method name
    2. Relaxed `kebab-case` spelling
    3. Relaxed `snake_case` spelling

Digits and consecutive capitals are treated as separate parts as well, so `someFieldWithCAPSAnd42Numbers()` also reads
`some-field-with-caps-and-42-numbers` and `some_field_with_caps_and_42_numbers`.

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
    import org.jspecify.annotations.Nullable;

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

===! ":material-code-json: `Hocon`"

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

=== ":simple-yaml: `YAML`"

    ```yaml
    clients:
      orders:
        baseUrl: "https://orders.example.com"
        clientName: ${?ORDERS_CLIENT_NAME}
        token: ${ORDERS_API_TOKEN}
        requestTimeout: ${ORDERS_REQUEST_TIMEOUT:2s}
    ```

This keeps the configuration structure readable: required settings are visible in the configuration type, secrets can be
passed through environment variables, and safe defaults stay directly in the configuration file.

## Injecting configuration { #injecting-configuration }

You can inject the base class `io.koraframework.config.common.Config`, which represents the configuration tree and gives
access to values through the `get(...)` method. The resulting configuration consists of several layers:

- Environment variables
- `Java` system properties
- Configuration file

Layers are merged so that an earlier layer wins over a later one: an environment variable overrides a system property,
and a system property overrides a value from the configuration file. Environment variables become flat keys named exactly
as the variable (`ORDERS_API_TOKEN`), while system properties are split on `.` into a tree, so `-Dservices.foo.bar=value`
overrides the `services.foo.bar` configuration key directly.

After merging, `Kora` resolves the `${...}` references across the whole tree. Values that came from environment variables
are never re-resolved, so a `$` inside a secret is safe. Resolving values that came from system properties can be turned
off with the `KORA_SYSTEM_PROPERTIES_RESOLVE_ENABLED` environment variable or the `kora.system.properties.resolve.enabled`
system property (default: `true`).

### Environment variables { #environment-variables }

If you need to inject configuration that contains **only** [environment variables](https://en.wikipedia.org/wiki/Environment_variable),
use the `@EnvironmentConfig` annotation as a tag for the configuration class:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class FooService {

        private final Config config;

        public FooService(@EnvironmentConfig Config config) {
            this.config = config;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class FooService(@EnvironmentConfig val config: Config)
    ```

### System properties { #system-variables }

If you need to inject configuration that contains **only** [`Java` system properties](https://www.baeldung.com/java-system-get-property-vs-system-getenv),
use the `@SystemPropertiesConfig` annotation as a tag for the configuration class:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class FooService {

        private final Config config;

        public FooService(@SystemPropertiesConfig Config config) {
            this.config = config;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class FooService(@SystemPropertiesConfig val config: Config)
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

### Reading raw Config values { #reading-raw-config-values }

When a raw `Config` is injected, values are read through the `get(...)` method, which returns a `ConfigValue<?>` node
for the requested path. `ConfigValue<?>` is a sealed type with typed accessors: `asString()`, `asNumber()`,
`asBoolean()`, `asObject()`, `asArray()`, and `isNull()`. If the value has an unexpected type, the accessor throws
`ConfigValueException`. A missing path never throws by itself — it returns `ConfigValue.NullValue`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class FooService {

        public FooService(Config config) {
            ConfigValue<?> value = config.get("services.foo.bar");
            if (!value.isNull()) {
                String bar = value.asString();
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class FooService(config: Config) {

        init {
            val value = config.get("services.foo.bar")
            if (!value.isNull) {
                val bar = value.asString()
            }
        }
    }
    ```

Array elements are addressed with an index inside the path, for example `config.get("services.foo.propObjects[0].p1")`.

As noted in [Recommended style](#recommended-configuration-style), prefer typed [custom configurations](#custom-configuration) over
reading a raw `Config`.
Use the raw read API only for dynamic or generic access when there is no other choice, and use `ValueOf<Config>` to avoid refreshing the component on every configuration change.

???+ warning "Attention"

    **We do not recommend** using `io.koraframework.config.common.Config` directly as a dependency in components,
    because when configuration is updated, all graph components that use it will be updated as well.
    We recommend always creating [custom configurations](#custom-configuration).

## Config Watcher { #config-watcher }

By default, `Kora` has a configuration file watcher that checks the application file for changes and starts dependency
graph refresh if the file changes. The check runs every `1000` milliseconds on a virtual thread.

For `HOCON`, the watcher also tracks files included through `include` inside the main configuration file.
If such an included file changes, the configuration is reread and the dependency graph is refreshed as well.

The watcher works only for file-based configuration that has a trackable source. If configuration came from a resource
inside an archive or was built without an application file, there is nothing on disk to update.
Replacing the symlink a configuration file points at counts as a change too, which is what makes mounted secrets and
`ConfigMap` updates visible without a restart.

You can disable the watcher by using:

1. Environment variable `KORA_CONFIG_WATCHER_ENABLED` (default: `true`)
2. System property `kora.config.watcher.enabled` (default: `true`)

## Supported types { #supported-types }

Configuration mappers provide an extensive list of supported types that covers most values you may need in custom
configurations. If the standard conversion is not enough, the behavior can be extended with a custom
`ConfigValueMapper<T>` component.

??? abstract "List of supported types"

    * boolean / Boolean
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
    * Duration[]
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
    * `Map<String, V>` or `Map<K, V>` (where `K` and `V` are supported by corresponding mappers)
    * `Either<A, B>` (where `A` and `B` are any supported types)

`List<T>` and `Set<T>` accept both an array and a comma-separated string, so `["v1", "v2"]` and `"v1, v2"` produce the
same value. `Map<K, V>` is read from an object: keys are taken as strings and passed through the key mapper, values
through the value mapper.

### Custom mapper { #custom-extractor }

If there is no standard conversion for a type or special parsing logic is required, add a custom
`ConfigValueMapper<T>` component. The `map(...)` method receives the configuration value as `ConfigValue<?>`
and must return the ready value of the required type, or `null` when the value is absent.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class TokenConfigValueMapper implements ConfigValueMapper<Token> {

        @Override
        public @Nullable Token map(ConfigValue<?> value) {
            if (value.isNull()) {
                return null;
            }
            return new Token(value.asString());
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class TokenConfigValueMapper : ConfigValueMapper<Token> {

        override fun map(value: ConfigValue<*>): Token? {
            if (value.isNull) {
                return null
            }
            return Token(value.asString())
        }
    }
    ```

Registered this way, the mapper is used for every configuration field of type `Token`.

If a specific mapper should be used only for one field, specify it through `@Mapping`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @ConfigMapper
    public interface ApiConfig {

        @Mapping(TokenConfigValueMapper.class)
        Token token();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @ConfigMapper
    interface ApiConfig {

        @Mapping(TokenConfigValueMapper::class)
        fun token(): Token
    }
    ```

Where the mapper instance comes from depends on its declaration. If the class is `final` (`Java`) / not `open`
(`Kotlin`), has a public no-argument constructor and carries no `@Tag`, `Kora` instantiates it itself for that field.
In any other case — constructor dependencies, an `open` class, or a `@Tag` next to `@Mapping` — the mapper is taken from
the dependency graph and therefore has to be registered there. A mapper used without `@Mapping`, as the mapper for its
type across the whole graph, is always taken from the graph and must be a component.

### Duration { #duration }

`Duration` can be set as a number or a string.
If a number is specified, it is treated as milliseconds.
If a string is specified, the `java.time.Duration` format is supported, for example `PT10S`, as well as `HOCON` style:

- `500ms`
- `10 seconds`
- `2 minutes`
- `1h`
- `1d`

Supported unit suffixes are `ns` / `nanos` / `nanoseconds`, `us` / `micros` / `microseconds`, `ms` / `millis` / `milliseconds`,
`s` / `seconds`, `m` / `minutes`, `h` / `hours`, `d` / `days`. A value without a suffix is read as milliseconds.

### Period { #period }

`Period` can be set as a number or a string.
If a number is specified, it is treated as days.
If a string is specified, these units are supported:

- `d` / `days`
- `w` / `weeks`
- `m` / `mo` / `months`
- `y` / `years`

For example, `7d`, `2 weeks`, `3mo`, or `1 year`. A value without a suffix is read as days.

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
Suffixes are matched case-insensitively and cover `b`, `kb` / `kib`, `mb` / `mib`, `gb` / `gib`, `tb` / `tib`,
`pb` / `pib`, `eb` / `eib`.

### Either { #either }

`Either<A, B>` lets a single field accept two alternative shapes. The mapper tries the left type `A` first, and if
mapping fails with any exception, it falls back to the right type `B`. This is useful when a value may be either a
plain scalar or a structured object.

===! ":fontawesome-brands-java: `Java`"

    ```java
    import io.koraframework.common.Either;

    @ConfigMapper
    public interface EndpointConfig {

        String host();

        int port();
    }

    @ConfigSource("services.foo")
    public interface FooServiceConfig {

        Either<String, EndpointConfig> endpoint();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import io.koraframework.common.Either

    @ConfigMapper
    interface EndpointConfig {

        fun host(): String

        fun port(): Int
    }

    @ConfigSource("services.foo")
    interface FooServiceConfig {

        fun endpoint(): Either<String, EndpointConfig>
    }
    ```

Both of these forms are valid for the `endpoint` field:

===! ":material-code-json: `Hocon`"

    ```javascript
    services {
      foo {
        endpoint = "https://example.com"   //(1)!
      }
    }
    ```

    1. Resolved as the left type (`String`)

=== ":simple-yaml: `YAML`"

    ```yaml
    services:
      foo:
        endpoint:                          #(1)!
          host: "example.com"
          port: 8080
    ```

    1. Resolved as the right type (`EndpointConfig`)

Use `isLeft()` / `isRight()` to check which side was resolved, and `left()` / `right()` to read the value.
