Module is responsible for mapping the values of configuration files to classes in Kora and then using them for application settings.

## HOCON

Support for [HOCON](https://github.com/lightbend/config/blob/master/HOCON.md) is implemented with [Typesafe Config](https://github.com/lightbend/config).
HOCON is a JSON-based config file format. The format is less strict than JSON and has a slightly different syntax.

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
      propMap { //(9)!
          "k1" = "v1"
          "k2" = "v2"
      }
    }
}
```

1. String configuration value
2. Numeric configuration value
3. Mandatory configuration value that is substituted from the `REQUIRED_ENV_VALUE` environment variable.
4. Optional configuration value which is substituted from the `OPTIONAL_ENV_VALUE` environment variable, if no such variable is found, the configuration value will be omitted. 5.
5. Configuration value with default value, the default value is specified in `propDefault = 10` and if `NON_DEFAULT_ENV_VALUE` environment variable is found, its value will replace the default value.
6. Configuration value assembled from substitutions of other parts of the configuration and the `Other` value between the
7.  String list configuration value, the value is set as an array of strings or can also be set as a string with values separated by commas
8.  String list configuration value, the value is set as a string with values separated by commas or can also be set as an array of strings
9.  Configuration value as a dictionary key and value

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
    }
    ```

### Dependency

===! ":fontawesome-brands-java: `Java`"

    Dependency `build.gradle`:
    ```groovy
    annotationProcessor "ru.tinkoff.kora:annotation-processors"
    implementation "ru.tinkoff.kora:config-hocon"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends HoconConfigModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Dependency `build.gradle.kts`:
    ```groovy
    ksp("ru.tinkoff.kora:symbol-processors")
    implementation("ru.tinkoff.kora:config-hocon")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : HoconConfigModule
    ```

### File

By default, the configuration files [reference.conf and application.conf](https://github.com/lightbend/config#note-about-resolving-substitutions-in-referenceconf-and-applicationconf) are expected.

First, all `reference.conf` files are merged, second, the `application.conf` file is overlaid on the unresolved
`reference.conf` file, the result is calculated and checked that all variable values are available.

It is assumed that the application configuration is in `application.conf` and the library configurations are in `reference.conf`.

Prioritize reading the `application.conf` configuration file:

- Use the file from `config.resource` if specified (file from `resources` directory)
- Use the file from `config.file` if specified (file from the file system)
- Use the `application.conf` file if available (file from `resources` directory)
- Use an empty configuration file if none of the above is present

## YAML

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
```

1. String configuration value
2. Numeric configuration value
3. Mandatory configuration value that is substituted from the `REQUIRED_ENV_VALUE` environment variable.
4. Optional configuration value which is substituted from the `OPTIONAL_ENV_VALUE` environment variable, if no such variable is found, the configuration value will be omitted. 5.
5. Configuration value with default value, the default value is specified as `10` and if `NON_DEFAULT_ENV_VALUE` environment variable is found, its value will replace the default value.
6. Configuration value assembled from substitutions of other parts of the configuration and the `Other` value between the
7.  String list configuration value, the value is set as an array of strings or can also be set as a string with values separated by commas
8.  String list configuration value, the value is set as a string with values separated by commas or can also be set as an array of strings
9.  Configuration value as a dictionary key and value

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
    }
    ```

### Dependency

===! ":fontawesome-brands-java: `Java`"

    Dependency `build.gradle`:
    ```groovy
    annotationProcessor "ru.tinkoff.kora:annotation-processors"
    implementation "ru.tinkoff.kora:config-yaml"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends YamlConfigModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Dependency `build.gradle.kts`:
    ```groovy
    ksp("ru.tinkoff.kora:symbol-processors")
    implementation("ru.tinkoff.kora:config-yaml")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : YamlConfigModule
    ```

#### File

By default, the `reference.yaml` and `application.yaml` configuration files are expected.

First, all `reference.yaml` files are merged, second, the `application.yaml` file is overlaid on an unresolved
`reference.yaml` file, the result is calculated and it is checked that all variable values are available.

It is assumed that the application configuration is in the `application.yaml` file and the library configurations are in `reference.yaml`.

Prioritize reading the `application.yaml` configuration file:

- Use the file from `config.resource` if specified (file from `resources` directory)
- Use the file from `config.file` if specified (file from the file system)
- Use the `application.yaml` file if available (file from `resources` directory)
- Use an empty configuration file if none of the above is present

## Custom configuration

A custom configuration provides a mapping of the configuration file to a user interface.
Such a user interface can later be injected as a dependency along with other components.

### Application config

In order to simplify the creation of custom configurations, the `@ConfigSource` annotation should be used:

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

### Library config

In order to create custom configurations within custom libraries, use the `@ConfigValueExtractor` annotation
which will create rules for processing a configuration file into an instance of a configuration class.

Let's consider an example when there is such a configuration class:

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

In order for the library to provide configuration, you need to implement the factory in a module:

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

Then by connecting the `FooLibraryModule` module in the application, the `FooServiceConfig` config can be used as a dependency in other classes.

### Required values

By default, all values declared in the config are considered **required** (*NotNull*) and must be present in the configuration file.

### Optional values

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

    1.  Any `@Nullable` annotation will do, such as `javax.annotation.Nullable` / `jakarta.annotation.Nullable` / `org.jetbrains.annotations.Nullable` / etc.

=== ":simple-kotlin: `Kotlin`"

    It is expected to use the [Kotlin Nullability](https://kotlinlang.org/docs/null-safety.html) syntax and mark such a parameter as Nullable:

    ```kotlin
    @ConfigSource("services.foo")
    interface FooServiceConfig {

        fun bar(): String?

        fun baz(): Int
    }
    ```

### Default values

If there is a need to use default values in a class, you can use this format:

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

## Injecting configuration

You can inject the base class `ru.tinkoff.kora.config.common.Config` which provides a common abstraction over the
configuration file mapping. The resulting configuration mapping consists of several layers that represent:

- Environment variables
- System variables
- Configuration file

#### Environment variables

In case you want to embed the configuration **only** [environment variables](https://ru.hexlet.io/courses/cli-basics/lessons/environment-variables/theory_unit),
you can use the `@Environment` annotation as a tag for the configuration class:

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

### System variables

In case you want to inject a configuration of **only** [system variables](https://www.baeldung.com/java-system-get-property-vs-system-getenv),
then you can use the `@SystemProperties` annotation as a tag for the configuration class:

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

### Configuration file

In case you want to inject a complete application configuration that consists **only** of a configuration file,
you can use the `@ApplicationConfig` annotation as a tag for the configuration class:

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

### Resulting configuration

If you want to inject a complete application configuration that consists of a configuration file,
environment variables and system variables, you simply inject the configuration class without the tag:

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

### Recommendations

???+ warning "Tip"

    **We do not recommend** using `ru.tinkoff.kora.config.common.Config` directly as a dependency in components,
    because when you update the configuration it will cause all graph components that use it to be updated,
    it is recommended to always create custom user configuration interfaces.

## Supported types

Configuration Extractors provide an extensive list of supported types that covers most of what
you might need to specify in custom configurations, or you can extend the behavior with your custom `ConfigValueExtractor<T>` component.

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
    * Properties
    * Pattern
    * UUID
    * Properties
    * LocalDate
    * LocalTime
    * LocalDateTime
    * OffsetTime
    * OffsetDateTime
    * Enum (any custom ENUM type)
    * `List<T>` (where `T` is any of the above listed types)
    * `Set<T>` (where `T` is any of the above types)
    * `Map<String, T>` (where `T` is any of the above types)
    * `Either<A, B>` (where `A` and `B` are any of the above types)
