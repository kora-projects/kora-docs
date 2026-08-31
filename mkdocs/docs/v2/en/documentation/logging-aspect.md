---
description: "Explains Kora logging aspects for argument and result logging, selective logging, structured JSON values, value masking, MDC enrichment and supported signatures. Use when working with @Log, @Log.in, @Log.out, @Log.result, @Log.off, @Mask, @Mdc, MaskingRules, MaskingStrategy, StructuredArgument, StructuredArgumentMapper, MDC."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora logging aspects for argument and result logging, selective logging, structured JSON values, value masking, MDC enrichment and supported signatures; key triggers include @Log, @Log.in, @Log.out, @Log.result, @Log.off, @Mask, @Mdc, MaskingRules, MaskingStrategy, MaskingFull, MaskingKeepFirst, MaskingKeepLast, StructuredArgument, StructuredArgumentMapper, MDC."
---

The declarative logging module lets you describe method logging with `@Log`, `@Mask` and `@Mdc` annotations.
At compile time, Kora creates an aspect wrapper for the method; the wrapper logs method entry, method exit, result, error, and `MDC` values without manual code in business logic.
This is useful for consistent call diagnostics, especially when you need to quickly understand which method was called, with which arguments, and how it completed.

For a step-by-step walkthrough before the reference details, see [Observability](../guides/observability.md).

## Dependency { #dependency }

Annotations and helper classes are provided by the `logging-common` dependency.
Usually it is already brought by other Kora modules or by [Logback](logging-slf4j.md#logback), but when using the annotations directly, the dependency can be added explicitly:

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

`LogbackModule` already extends `LoggingModule`, so an application that uses [Logback](logging-slf4j.md#logback) does not have to declare `LoggingModule` separately.

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

The level is `org.slf4j.event.Level`.

The entry or exit event itself is written at the level specified in `@Log`, `@Log.in`, or `@Log.out`.
Argument and result values are added to structured data only when the corresponding detail level is enabled.
A detail level is never *less* verbose than the event level: if the event is logged at `DEBUG`, a parameter declared as `@Log(Level.INFO)` is still emitted at `DEBUG`, because it is pointless to describe an event that is not written at all.
Which detail level is active depends on the effective logger level configured through `logging.levels` — see [logging levels configuration](logging-slf4j.md#configuration).

Values are written into a structured `data` marker; with the `ConsoleTextRecordEncoder` from [Logback](logging-slf4j.md#logback) it is rendered on a separate line after the message.

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
            <p>INFO&nbsp;&nbsp;[main] io.koraframework.example.Example.doWork - &gt;</p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp;data={"numParam":"4"}</p>
        </td>
    </tr>
    <tr>
        <td>TRACE</td>
        <td>
            <p>INFO&nbsp;&nbsp;[main] io.koraframework.example.Example.doWork - &gt;</p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp;data={"numParam":"4"}</p>
        </td>
    </tr>
    <tr>
        <td>INFO</td>
        <td>
            <p>INFO&nbsp;&nbsp;[main] io.koraframework.example.Example.doWork - &gt;</p>
        </td>
    </tr>
</table>

Arguments that do not have a dedicated converter are written with `String.valueOf(...)`, so they always appear as `JSON` strings.

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
            <p>INFO&nbsp;&nbsp;[main] io.koraframework.example.Example.doWork - &lt;</p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp;data={"out":"testResult"}</p>
        </td>
    </tr>
    <tr>
        <td>TRACE</td>
        <td>
            <p>INFO&nbsp;&nbsp;[main] io.koraframework.example.Example.doWork - &lt;</p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp;data={"out":"testResult"}</p>
        </td>
    </tr>
    <tr>
        <td>INFO</td>
        <td>
            <p>INFO&nbsp;&nbsp;[main] io.koraframework.example.Example.doWork - &lt;</p>
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
            <p>INFO&nbsp;&nbsp;[main] io.koraframework.example.Example.doWork - &gt;</p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp;data={"strParam":"s","numParam":"4"}</p>
            <p>INFO&nbsp;&nbsp;[main] io.koraframework.example.Example.doWork - &lt;</p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp;data={"out":"testResult"}</p>
        </td>
    </tr>
    <tr>
        <td>TRACE</td>
        <td>
            <p>INFO&nbsp;&nbsp;[main] io.koraframework.example.Example.doWork - &gt;</p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp;data={"strParam":"s","numParam":"4"}</p>
            <p>INFO&nbsp;&nbsp;[main] io.koraframework.example.Example.doWork - &lt;</p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp;data={"out":"testResult"}</p>
        </td>
    </tr>
    <tr>
        <td>INFO</td>
        <td>
            <p>INFO&nbsp;&nbsp;[main] io.koraframework.example.Example.doWork - &gt;</p>
            <p>INFO&nbsp;&nbsp;[main] io.koraframework.example.Example.doWork - &lt;</p>
        </td>
    </tr>
</table>

If a method completes with an error, the aspect logs the method exit at `WARN` with error data: `errorType` and `errorMessage`, and then rethrows the exception unchanged.
When `DEBUG` is enabled, the exception object is also passed to the log so that the stack trace is printed.
Error logging is emitted for any of `@Log`, `@Log.in` and `@Log.out` — a method annotated only with `@Log.in` still reports its failures.

```
WARN  [main] io.koraframework.example.Example.doWork - <
    data={"errorType":"java.lang.IllegalStateException","errorMessage":"OPS"}
```

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
            <p>INFO&nbsp;&nbsp;[main] io.koraframework.example.Example.doWork - &lt;</p>
        </td>
    </tr>
    <tr>
        <td>INFO</td>
        <td>
            <p>INFO&nbsp;&nbsp;[main] io.koraframework.example.Example.doWork - &lt;</p>
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

If the string representation of a parameter is not suitable for the log, mark the parameter with `@Json`.
The aspect then takes the `JSON` writer generated for the type by the [JSON module](json.md) and writes the value as a nested `JSON` object instead of a string.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
    public record Entity(String name, String code) { }

    @Log.in
    public String doWork(@Json Entity entity) {
        return "testResult";
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    data class Entity(val name: String, val code: String)

    @Log.`in`
    fun doWork(@Json entity: Entity): String {
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
            <p>INFO&nbsp;&nbsp;[main] io.koraframework.example.Example.doWork - &gt;</p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp;data={"entity":{"name":"Bob","code":"42"}}</p>
        </td>
    </tr>
    <tr>
        <td>INFO</td>
        <td>
            <p>INFO&nbsp;&nbsp;[main] io.koraframework.example.Example.doWork - &gt;</p>
        </td>
    </tr>
</table>

`@Json` must be placed on the logged element itself — on the parameter, or on the method when the *result* should be structured:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Log.out
    @Json
    public Entity doWork() {
        return new Entity("Bob", "42");
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Log.out
    @Json
    fun doWork(): Entity {
        return Entity("Bob", "42")
    }
    ```

For values that are built at the call site rather than passed as method arguments, the `StructuredArgument` interface exposes static factory helpers:

- `arg(fieldName, value)` builds a structured value; overloads accept `String`, `Integer`, `Long`, `Boolean`, `Map<String, String>`, a `JsonWriter<T>` together with the value, or a raw `StructuredArgumentWriter`.
- `marker(fieldName, value)` builds an `org.slf4j.Marker` with the same set of overloads, for attaching structured data to a single log call.

===! ":fontawesome-brands-java: `Java`"

    ```java
    // structured value written into MDC
    MDC.put("orderId", gen -> gen.writeString(orderId));

    // or as an SLF4J marker on a single log line
    log.info(StructuredArgument.marker("orderId", orderId), "order accepted");
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // structured value written into MDC
    MDC.put("orderId") { gen -> gen.writeString(orderId) }

    // or as an SLF4J marker on a single log line
    log.info(StructuredArgument.marker("orderId", orderId), "order accepted")
    ```

Any `StructuredArgumentWriter` can be rendered on demand with `writeToString()`, which is handy in tests.

### Parameter Conversion { #parameter-conversion }

If the parameter type cannot be annotated with `@Json`, or the log representation must differ from the wire representation, describe an external `StructuredArgumentMapper` and specify it through `@Mapping` on the required argument.
The mapper receives the original parameter value and writes the structured value to `JsonGenerator`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record Entity(String name, String code) { }

    public final class EntityLogMapper implements StructuredArgumentMapper<Entity> {

        @Override
        public void write(JsonGenerator gen, Entity value) {
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
            <p>INFO&nbsp;&nbsp;[main] io.koraframework.example.Example.doWork - &gt;</p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp;data={"entity":"Bob"}</p>
        </td>
    </tr>
    <tr>
        <td>INFO</td>
        <td>
            <p>INFO&nbsp;&nbsp;[main] io.koraframework.example.Example.doWork - &gt;</p>
        </td>
    </tr>
</table>

`JsonGenerator` here is `tools.jackson.core.JsonGenerator`; its write methods throw the unchecked `JacksonException`, so mapper methods do not declare checked exceptions.

The same `@Mapping` can be applied to the method itself to convert the *result*.
A generic mapper such as `MyMapper<T> implements StructuredArgumentMapper<T>` is supported as well — the aspect parameterizes it with the value type.

!!! warning "Mapper and the dependency container"

    A mapper **with** constructor dependencies must be a graph component and be annotated with `@Component`.
    A mapper **without** dependencies must **not** be annotated with `@Component` — Kora instantiates it itself, and an extra component leads to a `Multiple components match` graph build error.

### Masking { #masking }

Sensitive values can be masked before they reach the log with the `@Mask` annotation.
Masking works on the `JSON` representation of a value: the writer output is passed through a delegating generator that replaces matched fields with the value produced by a `MaskingStrategy`.

`@Mask` has a single attribute `value()` — the `MaskingStrategy` implementation (default: `MaskingFull.class`) — and can be placed on:

- a class or record (not abstract) — enables masking rules generation for the type and sets the default strategy for the fields of that type;
- a field or record component — marks that `JSON` field as masked;
- a logged parameter or method — tells the `@Log` aspect to write the value through the masking mapper.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Mask(MaskingKeepFirst.class)
    @Json
    public record Credentials(@Mask String password,
                              @Mask(MaskingKeepLast.class) String cardNumber,
                              String login) { }

    @Mask
    @Json
    public record User(String name, Credentials credentials) { }

    @Log.in
    public void register(@Mask @Json User user) { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Mask(MaskingKeepFirst::class)
    @Json
    data class Credentials(@Mask val password: String,
                           @Mask(MaskingKeepLast::class) val cardNumber: String,
                           val login: String)

    @Mask
    @Json
    data class User(val name: String, val credentials: Credentials)

    @Log.`in`
    fun register(@Mask @Json user: User) { }
    ```

```
INFO  [main] io.koraframework.example.Example.register - >
    data={"user":{"name":"Bob","credentials":{"password":"s3cr***","cardNumber":"***3456","login":"bob"}}}
```

Only the fields that carry `@Mask` are masked — `@Mask` on the type does not mask everything, it declares that rules must be generated for this type and provides the default strategy for its masked fields.
The strategy for a field is chosen in this order: the strategy named on the field itself, then the one named on the enclosing type, then `MaskingFull`.
Field names follow the `JSON` representation, so `@JsonField` renames and naming strategies are honoured and `@JsonSkip` fields are ignored.
Nested types annotated with `@Json` or `@Mask` are traversed recursively, including through collections, arrays and maps, so `@Mask` on a leaf field applies wherever that field is reached from the logged object.

`@Mask` and `@Json` on the logged element are independent:

- `@Mask @Json` - the value is written as a nested `JSON` object with the masked fields replaced (recommended).
- `@Mask` alone - the value is written as a single `JSON` string containing the masked document.

#### Masking Strategies { #masking-strategies }

A strategy is a `MaskingStrategy` implementation with a single `String mask(Object value)` method.
Three implementations are shipped with the module and are registered as default components with their default settings:

- `MaskingFull` - replaces the whole value with the replacement string (default: `***`).
- `MaskingKeepFirst` - keeps the first `keep` characters (default: `4`) and appends the replacement (default: `***`). If the value is not longer than `keep`, only the replacement is written.
- `MaskingKeepLast` - writes the replacement (default: `***`) and appends the last `keep` characters (default: `4`).

To change the replacement string or the number of kept characters, declare the strategy as your own component — it then overrides the default one:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends LoggingModule {

        default MaskingKeepLast maskingKeepLast() {
            return new MaskingKeepLast("###", 2);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : LoggingModule {

        fun maskingKeepLast(): MaskingKeepLast = MaskingKeepLast("###", 2)
    }
    ```

A custom strategy is an ordinary class implementing `MaskingStrategy`.
It is resolved from the dependency container by the generated rules, so the same rule as for mappers applies: annotate it with `@Component` only if it has constructor dependencies.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class EmailMaskingStrategy implements MaskingStrategy {

        @Override
        public String mask(Object value) {
            var email = String.valueOf(value);
            var at = email.indexOf('@');
            return at > 0 ? "***" + email.substring(at) : "***";
        }
    }

    @Mask
    @Json
    public record User(String name, @Mask(EmailMaskingStrategy.class) String email) { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class EmailMaskingStrategy : MaskingStrategy {

        override fun mask(value: Any?): String {
            val email = value.toString()
            val at = email.indexOf('@')
            return if (at > 0) "***" + email.substring(at) else "***"
        }
    }

    @Mask
    @Json
    data class User(val name: String, @Mask(EmailMaskingStrategy::class) val email: String)
    ```

`mask(...)` receives the original `JSON` value: `String`, `Boolean`, `Number`, `BigInteger`, `BigDecimal`, or `byte[]` for binary values.
`JSON` `null` values are never masked and the method is not called for them, and map keys are not masked as values.

#### Masking Rules { #masking-rules }

For every type annotated with `@Mask` the processor generates a module that provides a `MaskingRules<T>` component describing which `JSON` fields must be replaced and by which strategy.
The generated module is picked up by the dependency container automatically, so nothing has to be registered by hand.

When the rules must be built dynamically — for example for a type whose sources you do not own — extend `MaskingRules<T>` and point the logged element at it with `@Mapping`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class UserMaskingRules extends MaskingRules<User> {

        public UserMaskingRules() {
            super(User.class, Map.of("password", new MaskingFull(),
                                     "credentials.cardNumber", new MaskingKeepLast()));
        }
    }

    @Log.in
    public void register(@Mask @Json @Mapping(UserMaskingRules.class) User user) { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class UserMaskingRules : MaskingRules<User>(
        User::class.java,
        mapOf("password" to MaskingFull(),
              "credentials.cardNumber" to MaskingKeepLast())
    )

    @Log.`in`
    fun register(@Mask @Json @Mapping(UserMaskingRules::class) user: User) { }
    ```

A rule key is either a field name or a dotted path from the logged root object:

- `password` - masks every `JSON` field named `password` wherever it appears;
- `credentials.cardNumber` - masks `cardNumber` only when it is reached through the `credentials` field;
- `payments.*.cardNumber` - `*` matches exactly one dynamic path segment, which is what map keys produce.

The same rules can also be assembled through the builder: `MaskingRules.builder(User.class).mask("password", new MaskingFull()).build()`.

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

For `@Mdc` on a method, non-empty `key` and `value` are required; otherwise compilation fails.
For `@Mdc` on a parameter, the key is taken from `key`, then from `value`; if both values are empty, the parameter name is used.
The entry value is the parameter value.

Parameters of type `String`, `Integer`/`Int`, `Long`, `Boolean` and `StructuredArgumentWriter` keep their `JSON` type, other primitives are written through `String.valueOf(...)`, and any other type is written through `toString()`.
A `null` value of a non-primitive parameter simply adds no `MDC` entry.

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

Under the hood, non-global entries are snapshotted before the call and restored in a `finally` block once the method returns, so they never leak beyond the method scope.
Entries added with `global = true` — on a method annotation or on a parameter annotation — and any value set through the imperative `MDC.put` stay in the current `MDC` scope and are therefore visible to every subsequent log line of that request, message or job.

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
A value in the `${...}` format is inserted into the generated code as an expression, so it must be valid code in the language of the annotated class.

**Example log with `MDC`:**
```
INFO  [main] io.koraframework.example.Example.test - key="ee1a1a0e-3fdf-4e46-8b6e-2f16d2f0f0a1" key1="value2" 123="testValue" >
    data={"s":"testValue"}
```

`@Mdc` is not supported for methods that return `CompletionStage`, `CompletableFuture`, `Future`, `Mono`, or `Flux`.
For `Kotlin`, regular methods and `suspend` methods are supported, but `global = true` cannot be used in `suspend` methods.

### Imperative MDC { #imperative-mdc }

Where an annotation does not fit — inside interceptors, filters, or plain service code — use the imperative `io.koraframework.logging.common.MDC` API.
It is the programmatic counterpart of `@Mdc`: entries are written into the `MDC` bound to the current scope and appear in every log line emitted for the remainder of that scope.

Kora binds a fresh `MDC` at the start of every unit of work — an HTTP server request, a Kafka record, a gRPC call, a scheduled job, a JMS message — so entries of one request never leak into another.

The static `put` method has overloads for `String`, `Integer`, `Long`, and `Boolean` values, plus a `StructuredArgumentWriter` overload for structured values.
`remove(key)` drops a single entry, and `get().values()` returns the current entries as an immutable `Map<String, StructuredArgumentWriter>`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    import io.koraframework.logging.common.MDC;

    @Component
    public final class OrderService {

        public void process(String orderId) {
            MDC.put("orderId", orderId);                  // String
            MDC.put("attempt", 1);                        // Integer
            MDC.put("bytes", 1024L);                      // Long
            MDC.put("retryable", true);                   // Boolean
            MDC.put("payload", gen -> gen.writeString(orderId)); // StructuredArgumentWriter

            // ... business logic; every log line in this scope now carries the keys

            MDC.remove("attempt");                        // drop a single key
            var current = MDC.get().values();             // read current entries
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import io.koraframework.logging.common.MDC

    @Component
    class OrderService {

        fun process(orderId: String) {
            MDC.put("orderId", orderId)                   // String
            MDC.put("attempt", 1)                         // Integer
            MDC.put("bytes", 1024L)                       // Long
            MDC.put("retryable", true)                    // Boolean
            MDC.put("payload") { gen -> gen.writeString(orderId) } // StructuredArgumentWriter

            // ... business logic; every log line in this scope now carries the keys

            MDC.remove("attempt")                         // drop a single key
            val current = MDC.get().values()              // read current entries
        }
    }
    ```

Unlike `@Mdc`, the imperative API has no restriction on the method signature, because it writes into the current scope rather than wrapping the method call.

The `MDC` is exposed as a `ScopedValue` named `MDC.VALUE`.
Outside a request, message or job scope — during graph initialization, in a shutdown hook, or in a plain unit test — nothing is bound and `MDC.get()` fails, so guard such code:

===! ":fontawesome-brands-java: `Java`"

    ```java
    if (MDC.VALUE.isBound()) {
        MDC.put("orderId", orderId);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    if (MDC.VALUE.isBound()) {
        MDC.put("orderId", orderId)
    }
    ```

To run your own code in a new `MDC` scope, bind the value explicitly with `ScopedValue.where(MDC.VALUE, new MDC())`; `MDC.fork()` produces an independent copy of the current entries, which is what Kora itself does when it hands work to a nested scope.

!!! warning "Use Kora's `MDC`, not SLF4J's"

    Always import `io.koraframework.logging.common.MDC` — never `org.slf4j.MDC`.
    The SLF4J class writes to a plain `ThreadLocal` that is not tied to the scope Kora opens per request, message or job: values placed there are not cleaned up between units of work, are lost on thread hand-offs, and can only hold strings.
    Kora's `MDC` is scoped, propagated by the framework, and keeps structured `JSON` values.

    Asynchronous logging must go through `KoraAsyncAppender` — it captures a snapshot of the current `MDC` on the calling thread before the event is handed to the appender thread. See [Logback](logging-slf4j.md#logback).

## Signatures { #signatures }

Method signatures supported for logging aspects:

===! ":fontawesome-brands-java: `Java`"

    The class must not be `final` so that aspects can create a subclass, the method must not be `final` or `private`, and the class must have a constructor visible to the generated proxy.

    `T` means the return value type or `void`.

    - `T myMethod()`
    - `Optional<T> myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/CompletionStage.html) (only for `@Log`, entry is logged on call and exit on completion)
    - `CompletableFuture<T> myMethod()` (only for `@Log`, entry is logged on call and exit on completion)

    `Mono<T>` and `Flux<T>` from `Project Reactor`, as well as a plain `Future<T>` that is not a `CompletionStage`, are not supported and the compilation fails with an explicit error.

=== ":simple-kotlin: `Kotlin`"

    The class must be `open` and not abstract so that aspects can create a subclass, and the function must be `open` and a member of that class — top-level functions cannot be proxied.

    `T` means the return value type, `T?`, or `Unit`.

    - `myMethod(): T`
    - `suspend myMethod(): T` [Kotlin Coroutines](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (requires [dependency](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) as `implementation`)
    - `myMethod(): Flow<T>` [Kotlin Coroutines](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (only for `@Log`, requires [dependency](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) as `implementation`)

    For `Flow<T>` the entry event is logged when the flow starts, every emitted element is logged with the `<<<` message, and the `<` message is written when the flow completes.

    `Mono<T>` and `Flux<T>` from `Project Reactor` are not supported and the compilation fails with an explicit error.

`@Mdc` is stricter than `@Log`: it accepts only synchronous methods and, in `Kotlin`, `suspend` functions.
