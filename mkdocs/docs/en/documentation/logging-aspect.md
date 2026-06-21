---
description: "Explains Kora logging aspects for argument and result logging, selective logging, MDC enrichment, structured parameters, conversion, and signatures. Use when working with @Log, @Log.in, @Log.out, @Log.off, @Mdc, @StructuredArgument, MDC, LogAspect."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora logging aspects for argument and result logging, selective logging, MDC enrichment, structured parameters, conversion, and signatures; key triggers include @Log, @Log.in, @Log.out, @Log.off, @Mdc, @StructuredArgument, MDC, LogAspect."
---

The declarative logging module lets you describe method logging with `@Log` and `@Mdc` annotations.
At compile time, Kora creates an aspect wrapper for the method; the wrapper logs method entry, method exit, result, error, and `MDC` values without manual code in business logic.
This is useful for consistent call diagnostics, especially when you need to quickly understand which method was called, with which arguments, and how it completed.

For a step-by-step walkthrough before the reference details, see [Observability](../guides/observability.md).

## Dependency { #dependency }

Annotations and helper classes are provided by the `logging-common` dependency.
Usually it is already brought by other Kora modules or by [Logback](logging-slf4j.md#logback), but when using the annotations directly, the dependency can be added explicitly:

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

Aspect generation also requires the common [annotation processors](general.md#annotation-processor) or [`KSP` processors](general.md#ksp).
In a regular Kora application, they are already connected as part of the basic project setup.

## Logging { #logging }

Method logging is configured with annotation combinations:

- `@Log` - logs method entry and exit (default: `INFO`).
- `@Log.in` - logs only method entry (default: `INFO`).
- `@Log.out` - logs only method exit (default: `INFO`).
- `@Log.result` - sets the level from which the result value is added to the log (default: `DEBUG`).
- `@Log.off` - disables logging of the method result or a specific parameter.
- `@Log(Level)` on a parameter - sets the level from which the parameter is added to structured data (default: `DEBUG` for a parameter without a separate annotation).

The entry or exit event itself is written at the level specified in `@Log`, `@Log.in`, or `@Log.out`.
Argument and result values are added to structured data only when the corresponding detail level is enabled.

### Arguments { #argument }

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Log.in
    public String doWork(@Log.off String strParam, int numParam) {
        return "testResult";
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Log.`in`
    fun doWork(@Log.off strParam: String?, numParam: Int): String {
        return "testResult"
    }
    ```

<table>
    <thead>
        <th>Logging level</th>
        <th>Log</th>
    </thead>
    <tr>
        <td>DEBUG</td>
        <td>
            <p>INFO [main] r.t.e.e.Example.doWork: > {data: {numParam: "4"}}</p>
        </td>
    </tr>
    <tr>
        <td>TRACE</td>
        <td>
            <p>INFO [main] r.t.e.e.Example.doWork: > {data: {numParam: "4"}}</p>
        </td>
    </tr>
    <tr>
        <td>INFO</td>
        <td>
            <p>INFO [main] r.t.e.e.Example.doWork: ></p>
        </td>
    </tr>
</table>

### Result { #result }

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Log.out
    public String doWork(String strParam, int numParam) {
        return "testResult";
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Log.out
    fun doWork(strParam: String, numParam: Int): String {
        return "testResult"
    }
    ```

<table>
    <thead>
        <th>Logging level</th>
        <th>Log</th>
    </thead>
    <tr>
        <td>DEBUG</td>
        <td>
            <p>INFO [main] r.t.e.e.Example.doWork: < {data: {out: "testResult"}}</p>
        </td>
    </tr>
    <tr>
        <td>TRACE</td>
        <td>
            <p>INFO [main] r.t.e.e.Example.doWork: < {data: {out: "testResult"}}</p>
        </td>
    </tr>
    <tr>
        <td>INFO</td>
        <td>
            <p>INFO [main] r.t.e.e.Example.doWork: <</p>
        </td>
    </tr>
</table>

### Arguments And Result { #argument-and-result }

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Log
    public String doWork(String strParam, int numParam) {
        return "testResult";
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Log
    fun doWork(strParam: String, numParam: Int): String {
        return "testResult"
    }
    ```

<table>
    <thead>
        <th>Logging level</th>
        <th>Log</th>
    </thead>
    <tr>
        <td>DEBUG</td>
        <td>
            <p>INFO [main] r.t.e.e.Example.doWork: > {data: {strParam: "s", numParam: "4"}}</p>
            <p>INFO [main] r.t.e.e.Example.doWork: < {data: {out: "testResult"}}</p>
        </td>
    </tr>
    <tr>
        <td>TRACE</td>
        <td>
            <p>INFO [main] r.t.e.e.Example.doWork: > {data: {strParam: "s", numParam: "4"}}</p>
            <p>INFO [main] r.t.e.e.Example.doWork: < {data: {out: "testResult"}}</p>
        </td>
    </tr>
    <tr>
        <td>INFO</td>
        <td>
            <p>INFO [main] r.t.e.e.Example.doWork: ></p>
            <p>INFO [main] r.t.e.e.Example.doWork: <</p>
        </td>
    </tr>
</table>

If a method completes with an error, the aspect logs method exit with error data: `errorType` and `errorMessage`.
When `DEBUG` is enabled, the exception object is also passed to the log.

### Selective Logging { #selective-logging }

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Log.out
    @Log.off
    public String doWork(String strParam, int numParam) {
        return "testResult";
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Log.out
    @Log.off
    fun doWork(strParam: String, numParam: Int): String {
        return "testResult"
    }
    ```

<table>
    <thead>
        <th>Logging level</th>
        <th>Log</th>
    </thead>
    <tr>
        <td>TRACE, DEBUG</td>
        <td>
            <p>INFO [main] r.t.e.e.Example.doWork: <</p>
        </td>
    </tr>
    <tr>
        <td>INFO</td>
        <td>
            <p>INFO [main] r.t.e.e.Example.doWork: <</p>
        </td>
    </tr>
</table>

In this example, `@Log.off` on the method disables writing the result value, but does not disable the method exit event itself.
To exclude a specific argument from the log, put `@Log.off` on the parameter.

Parameter detail level can be configured separately:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Log.in
    public void doWork(@Log(Level.INFO) String id, @Log(Level.TRACE) String payload) { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Log.`in`
    fun doWork(@Log(Level.INFO) id: String, @Log(Level.TRACE) payload: String) { }
    ```

At `INFO`, only `id` is added to structured data, while `payload` appears only when `TRACE` is enabled.

The result value can be emitted already at `INFO` by explicitly setting `@Log.result(Level.INFO)`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Log.out
    @Log.result(Level.INFO)
    public String doWork() {
        return "testResult";
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Log.out
    @Log.result(Level.INFO)
    fun doWork(): String {
        return "testResult"
    }
    ```

### Structured Parameter { #structured-parameter }

If a string representation of a parameter is not suitable for the log, the parameter type can implement the `StructuredArgument` interface.
In that case, the object defines the field name through `fieldName()` and writes the value to `JsonGenerator` through `writeTo(...)`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record Entity(String name, String code) implements StructuredArgument {

        @Override
        public String fieldName() {
            return "name";
        }

        @Override
        public void writeTo(JsonGenerator generator) throws IOException {
            generator.writeString(name);
        }
    }

    @Log.in
    public String doWork(Entity entity) {
        return "testResult";
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class Entity(val name: String, val code: String) : StructuredArgument {

        override fun writeTo(generator: JsonGenerator) = generator.writeString(name)

        override fun fieldName(): String = "name"
    }

    @Log.`in`
    fun doWork(entity: Entity): String {
        return "testResult"
    }
    ```

<table>
    <thead>
        <th>Logging level</th>
        <th>Log</th>
    </thead>
    <tr>
        <td>DEBUG, TRACE</td>
        <td>
            <p>INFO [main] r.t.e.e.Example.doWork: ></p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp; data={"entity":"Bob"}</p>
        </td>
    </tr>
    <tr>
        <td>INFO</td>
        <td>
            <p>INFO [main] r.t.e.e.Example.doWork: ></p>
        </td>
    </tr>
</table>

### Parameter Conversion { #parameter-conversion }

If the parameter type cannot be changed, describe an external `StructuredArgumentMapper` and specify it through `@Mapping` on the required argument.
The mapper receives the original parameter value and writes the structured value to `JsonGenerator`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record Entity(String name, String code) { }

    public final class EntityLogMapper implements StructuredArgumentMapper<Entity> {
        public void write(JsonGenerator gen, Entity value) throws IOException {
            gen.writeString(value.name());
        }
    }

    @Log.in
    public String doWork(@Mapping(EntityLogMapper.class) Entity entity) {
        return "testResult";
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class Entity(val name: String, val code: String)

    class EntityLogMapper : StructuredArgumentMapper<Entity> {

        @Throws(IOException::class)
        override fun write(gen: JsonGenerator, value: Entity) = gen.writeString(value.name)
    }

    @Log.`in`
    fun doWork(@Mapping(EntityLogMapper::class) entity: Entity): String {
        return "testResult"
    }
    ```

<table>
    <thead>
        <th>Logging level</th>
        <th>Log</th>
    </thead>
    <tr>
        <td>DEBUG, TRACE</td>
        <td>
            <p>INFO [main] r.t.e.e.Example.doWork: ></p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp; data={"entity":"Bob"}</p>
        </td>
    </tr>
    <tr>
        <td>INFO</td>
        <td>
            <p>INFO [main] r.t.e.e.Example.doWork: ></p>
        </td>
    </tr>
</table>

### MDC (Mapped Diagnostic Context) { #mdc-mapped-diagnostic-context }

The `@Mdc` annotation adds key-value pairs to `MDC` (`Mapped Diagnostic Context`).
`MDC` stores execution context and lets you add it to log messages: for example, request, user, or operation identifiers.

The annotation can be applied to methods and method parameters.
Repeated `@Mdc` usage is supported on methods.
Values added without `global = true` are restored after method execution.

**`@Mdc` annotation parameters:**

- `key()` - `MDC` entry key (default: `""`).
- `value()` - `MDC` entry value (default: `""`).
- `global()` - keep the value in `MDC` after method exit (default: `false`).

For `@Mdc` on a method, non-empty `key` and `value` are required.
For `@Mdc` on a parameter, the key is taken from `key`, then from `value`; if both values are empty, the parameter name is used.
The entry value is the parameter value.

#### Parameter Annotation { #parameter-annotation }

===! ":fontawesome-brands-java: `Java`"

    ```java
    public String test(@Mdc String s) {
        return "1";
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun test(@Mdc s: String): String {
        return "1"
    }
    ```

In this case, the `MDC` key matches the parameter name `s`, and the value is the parameter value.

#### Parameter Annotation With Key { #parameter-annotation-with-key }

===! ":fontawesome-brands-java: `Java`"

    ```java
    public String test(@Mdc(key = "123") String s) {
        return "1";
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun test(@Mdc(key = "123") s: String): String {
        return "1"
    }
    ```

Here, the `MDC` key is `123`, and the value is the parameter value `s`.

#### Method Annotation { #method-use }

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Mdc(key = "key1", value = "value2")
    public String test(String s) {
        return "1";
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Mdc(key = "key1", value = "value2")
    fun test(s: String): String {
        return "1"
    }
    ```

In this example, the `key1=value2` entry is added to `MDC` before the method call.
After the method completes, the previous `key1` value is restored.

#### Combined { #combined }

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Mdc(key = "key", value = "value", global = true)
    @Mdc(key = "key1", value = "value2")
    public String test(@Mdc(key = "123") String s) {
        return "1";
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Mdc(key = "key", value = "value", global = true)
    @Mdc(key = "key1", value = "value2")
    fun test(@Mdc(key = "123") s: String): String {
        return "1"
    }
    ```

In this example, two `@Mdc` annotations are applied to the method, and one is applied to the parameter.
The `key=value` entry remains in `MDC` after method execution because of `global = true`; the other entries are restored or removed.

#### Generated Value From Code { #generated-value-for-mdc-value }

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Mdc(key = "key", value = "${java.util.UUID.randomUUID().toString()}")
    public String test(String s) {
        return "1";
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Mdc(key = "key", value = "\${java.util.UUID.randomUUID().toString()}")
    fun test(s: String): String {
        return "1";
    }
    ```

When the method is called, an `MDC` entry with key `key` is added, and the value is a random `UUID`.
For `Java`, a value in the `${...}` format is inserted into the generated code as an expression.

**Example log with `MDC`:**
```
INFO [main] r.t.e.e.Example.test: > {data: {s: "testValue"}} key=some-uuid-value key1=value2 123=testValue
```

`@Mdc` is not supported for methods that return `CompletionStage`, `Mono`, or `Flux`.
For `Kotlin`, regular methods and `suspend` methods are supported, but `global = true` cannot be used in `suspend` methods.

## Signatures { #signatures }

Method signatures supported for logging aspects:

===! ":fontawesome-brands-java: `Java`"

    The class must not be `final` so that aspects can create a subclass.

    `T` means the return value type or `Void`.

    - `T myMethod()`
    - `Optional<T> myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletionStage.html) (only for `@Log`)
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (only for `@Log`, requires [dependency](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))
    - `Flux<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (only for `@Log`, requires [dependency](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

=== ":simple-kotlin: `Kotlin`"

    The class must be `open` so that aspects can create a subclass.

    `T` means the return value type, `T?`, or `Unit`.

    - `myMethod(): T`
    - `suspend myMethod(): T` [Kotlin Coroutines](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (requires [dependency](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) as `implementation`)
    - `myMethod(): Flow<T>` [Kotlin Coroutines](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (requires [dependency](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) as `implementation`)
