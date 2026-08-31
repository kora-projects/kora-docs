---
description: "Explains Kora compile-time JSON reader and writer generation, field requirements, naming strategies, ignores, serialization levels, value types, JsonNullable, sealed hierarchies, enums, custom codecs, parse errors, and the Jackson escape hatch. Use when working with @Json, @JsonReader, @JsonWriter, @JsonInclude, @JsonField, @JsonSkip, @JsonDiscriminatorField, @NamingStrategy, @Mapping, JsonNullable, RawJson, JacksonModule."
agent:
  use_when: "Use this file for Kora docs or implementation questions about compile-time JSON reader and writer generation, field requirements, naming strategies, ignores, serialization levels, value types, JsonNullable, sealed hierarchies, enums, custom codecs, parse errors, and the Jackson escape hatch; key triggers include @Json, @JsonReader, @JsonWriter, @JsonInclude, @JsonField, @JsonSkip, @JsonDiscriminatorField, @JsonDiscriminatorValue, @NamingStrategy, @Mapping, JsonNullable, RawJson, StreamReadException, JsonModule, JacksonModule, json-common."
---

The `JSON` module creates efficient `JsonReader` and `JsonWriter` implementations for application classes at compile time and without using `Reflection` at runtime.
Generation is controlled by `@Json`, `@JsonReader`, `@JsonWriter`, and related field-level annotations.

Generated codecs are ordinary application graph components, so the rest of Kora consumes them directly:
`HTTP` server and `HTTP` client body mappers, string parameter readers and writers, and `Kafka` serializers and deserializers all accept a `JsonReader<T>` or `JsonWriter<T>` and are registered under the `@Json` tag.
The same generated codec is therefore reused across the whole application.

For a step-by-step walkthrough before the reference details, see [JSON](../guides/json.md).

## Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) in `build.gradle`:
    ```groovy
    annotationProcessor "io.koraframework:annotation-processors" //(1)!
    implementation "io.koraframework:json-common"
    ```

    1. The annotation processor generates `JsonReader` and `JsonWriter` at compile time. Without it no codec is created and the graph fails with a missing `JsonReader`/`JsonWriter` dependency.

    Module:
    ```java
    @KoraApp
    public interface Application extends JsonModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) in `build.gradle.kts`:
    ```groovy
    ksp("io.koraframework:symbol-processors:2.0.0.RC1") //(1)!
    implementation("io.koraframework:json-common")
    ```

    1. The `KSP` processor generates `JsonReader` and `JsonWriter` at compile time. Without it no codec is created and the graph fails with a missing `JsonReader`/`JsonWriter` dependency.

    Module:
    ```kotlin
    @KoraApp
    interface Application : JsonModule
    ```

`json-common` brings in the `Jackson` streaming core, so hand-written codecs work against `tools.jackson.core.JsonParser` and `tools.jackson.core.JsonGenerator`.
Generated codecs never use `Jackson` databind and never use `Reflection`.

## Writer { #writer }

Use `@JsonWriter` to create only a `JsonWriter`.
This option is useful when the type only needs to be written to `JSON`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @JsonWriter
    public record Dto(String field1, int field2) { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @JsonWriter
    data class Dto(val field1: String, val field2: Int)
    ```

## Reader { #reader }

Use `@JsonReader` to create only a `JsonReader`.
This option is useful when the type only needs to be read from `JSON`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @JsonReader
    public record Dto(String field1, int field2) { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @JsonReader
    data class Dto(val field1: String, val field2: Int)
    ```

## Reader & Writer { #reader-and-writer }

Use `@Json` to create both `JsonReader` and `JsonWriter`.
In most cases, `@Json` is the preferred annotation:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
    public record Dto(String field1, int field2) { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    data class Dto(val field1: String, val field2: Int)
    ```

## Reader And Writer Interfaces { #reader-writer-interfaces }

`JsonReader<T>` and `JsonWriter<T>` are regular application graph components.
After generation or manual registration, they can be injected by signature like any other dependency.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MyService {

        private final JsonReader<Dto> reader;
        private final JsonWriter<Dto> writer;

        public MyService(JsonReader<Dto> reader, JsonWriter<Dto> writer) {
            this.reader = reader;
            this.writer = writer;
        }

        public @Nullable Dto read(String json) { //(1)!
            return this.reader.read(json);
        }

        public byte[] write(Dto dto) { //(2)!
            return this.writer.toByteArray(dto);
        }
    }
    ```

    1. `JsonReader` is declared as returning a nullable value, because a top-level `null` document reads as `null`.
    2. No `throws` clause and no `try`/`catch` are required: `JSON` failures are unchecked.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyService(
        private val reader: JsonReader<Dto>,
        private val writer: JsonWriter<Dto>
    ) {

        fun read(json: String): Dto = requireNotNull(reader.read(json)) //(1)!

        fun write(dto: Dto): ByteArray = writer.toByteArray(dto) //(2)!
    }
    ```

    1. `JsonReader` is declared as returning a nullable value, because a top-level `null` document reads as `null`. A non-null target therefore needs an explicit check.
    2. No `try`/`catch` is required: `JSON` failures are unchecked.

`JsonReader<T>` reads a value from a `JsonParser`, a `byte[]` (optionally with an offset and a length), a `String`, or an `InputStream`.
Every one of these methods is declared as returning a nullable value.

`JsonWriter<T>` writes a value through a `JsonGenerator` and can also produce the whole document at once:

- `toByteArray(value)` - `UTF-8` bytes.
- `toString(value)` - a compact string.
- `toPrettyString(value)` - a formatted string.

Runtime behavior worth noting when calling the codecs directly:

- `read(...)` returns `null` when the parser is positioned on a `JSON` `null` token, so a top-level `null` document deserializes to `null`.
- All failures are `tools.jackson.core.JacksonException` subtypes, and that class extends `RuntimeException`, so no method declares a checked exception. See [Errors](#errors).
- The generated codec class lives in the package of the annotated type and is named `$Dto_JsonReader` / `$Dto_JsonWriter`, with outer class names folded into the prefix for nested types (`$Outer_Inner_JsonReader`). Inject the `JsonReader<Dto>` interface rather than referring to that class.

## Required fields { #required-fields }

===! ":fontawesome-brands-java: `Java`"

    By default, all fields declared in an object are considered **required** (`NotNull`).

    ```java
    @Json
    public record Dto(String field1, int field2) { }
    ```

=== ":simple-kotlin: `Kotlin`"

    By default, all fields declared in an object without [Kotlin Nullability](https://kotlinlang.org/docs/null-safety.html) syntax are considered **required** (`NotNull`).

    ```kotlin
    @Json
    data class Dto(val field1: String, val field2: Int)
    ```

A required field that is absent from the document and a required field that is present with an explicit `null` are two different errors, and both are reported with the field name and the `JSON` path.

## Optional fields { #optional-fields }

===! ":fontawesome-brands-java: `Java`"

    If a `JSON` field is optional and can be absent, use the `@Nullable` annotation:

    ```java
    @Json
    public record Dto(@Nullable String field1, //(1)!
                      int field2) { }
    ```

    1. Kora uses [JSpecify](https://jspecify.dev/) `org.jspecify.annotations.Nullable`. Any annotation whose simple name is `Nullable` is also recognized.

    `JSpecify` `@Nullable` is a *type-use* annotation, so its position matters for nested and array types:

    ```java
    @Json
    public record Dto(java.util.@Nullable List<String> labels, //(1)!
                      byte @Nullable [] payload) { } //(2)!
    ```

    1. The annotation applies to `List`, not to `String`.
    2. The annotation applies to the array, not to `byte`.

=== ":simple-kotlin: `Kotlin`"

    For `Kotlin`, use [Kotlin Nullability](https://kotlinlang.org/docs/null-safety.html) syntax and mark the parameter as `nullable`:

    ```kotlin
    @Json
    data class Dto(
        val field1: String?,
        val field2: Int
    )
    ```

    `Kotlin` expresses nullability in the type itself, so no annotation is needed:

    ```kotlin
    @Json
    data class Dto(
        val labels: List<String>?,
        val payload: ByteArray?
    )
    ```

## Field Naming { #field-naming }

If a field in `JSON` has a different name than the field in the class, use `@JsonField`.
It sets the key name in `JSON`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
    public record Dto(@JsonField("field_1") String field1,
                      int field2) { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    data class Dto(
        @field:JsonField("field_1") val field1: String,
        val field2: Int
    )
    ```

`@JsonField` only renames the key.
To read or write a single field with a specific codec, use `@Mapping` - see [Custom Field Mappers](#custom-field-mappers).

### Naming Strategy { #naming-strategy }

To rename every field of a class at once, annotate the class with `@NamingStrategy` and pass a `NameConverter` implementation.
The strategy applies to both the generated `JsonReader` and the generated `JsonWriter`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
    @NamingStrategy(SnakeCaseNameConverter.class)
    public record Dto(String stringField, //(1)!
                      Integer integerField) { }
    ```

    1. Written and read as `string_field`.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    @NamingStrategy(SnakeCaseNameConverter::class)
    data class Dto(
        val stringField: String, //(1)!
        val integerField: Int
    )
    ```

    1. Written and read as `string_field`.

Available converters in `io.koraframework.common.naming`:

- `NoopNameConverter` - `myFieldNAME` &#8594; `myFieldNAME`.
- `CamelCaseNameConverter` - `myFieldNAME` &#8594; `myFieldName`.
- `PascalCaseNameConverter` - `myFieldNAME` &#8594; `MyFieldName`.
- `SnakeCaseNameConverter` - `myFieldNAME` &#8594; `my_field_name`.
- `SnakeCaseUpperNameConverter` - `myFieldNAME` &#8594; `MY_FIELD_NAME`.

A field annotated with `@JsonField` keeps the name from the annotation.
A bare `@JsonField` with no value opts the field out of the naming strategy and keeps the declared field name.

## Field Ignore { #field-ignore }

If a field in a `DTO` should not appear in the written `JSON`, use `@JsonSkip`.
The generated `JsonWriter` omits such a field entirely.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
    public record Dto(String field1,
                      @JsonSkip @Nullable Integer field2) { } //(1)!
    ```

    1. `@JsonSkip` affects writing only. The generated `JsonReader` still maps the field, so a skipped field that is not present in the input must be [optional](#optional-fields).

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    data class Dto(
        val field1: String,
        @field:JsonSkip val field2: Int? //(1)!
    )
    ```

    1. `@JsonSkip` affects writing only. The generated `JsonReader` still maps the field, so a skipped field that is not present in the input must be [optional](#optional-fields).

A type that is only ever written can be annotated with `@JsonWriter` instead of `@Json`; then no reader is generated and the skipped field imposes no constraint at all.

## Serialization Levels { #serialization-levels }

By default, fields with `null` values are not written. (1)
{ .annotate }

1. `IncludeType.NON_NULL` - write the field only if the value is not `null`.

To change this behavior, use `@JsonInclude`.
The annotation can be placed not only on a field, but also on a class; in that case, the rule applies to all fields at once, and a field-level annotation wins over the class-level one.

Available options:

- `IncludeType.ALWAYS` - always write the field.
- `IncludeType.NON_NULL` - write the field if the value is not `null`.
- `IncludeType.NON_EMPTY` - write the field if the value is not `null` and is not an empty collection or map.

`IncludeType.NON_EMPTY` is resolved at compile time, so it only takes effect when the field type is statically known to be a `Collection` or a `Map`.
On a type variable the emptiness check cannot be generated and the field behaves as `IncludeType.NON_NULL`.

Example:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
    @JsonInclude(IncludeType.NON_NULL)
    public record Dto(@JsonInclude(IncludeType.ALWAYS) @Nullable String field1,
                      int field2) { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    data class Dto(
        @field:JsonInclude(IncludeType.ALWAYS) val field1: String?,
        val field2: Int
    )
    ```

## Serialization Constructor { #serialization-constructor }

If a specific constructor should be used for reading `JSON`, annotate it with `@JsonReader`.
You can also use `@Json`, but `@JsonReader` has higher priority:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
    public record Dto(String field1, int field2) {

        @JsonReader
        public Dto(String field1) {
            this(field1, 0);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    data class Dto(val field1: String, val field2: Int) {

        @JsonReader
        constructor(field1: String) : this(field1, 0)
    }
    ```

`JsonReader` and `JsonWriter` can be generated for classes, `record`, `data class`, `enum`, and `sealed` types.
Reading requires a concrete, non-abstract type and exactly one constructor to be selectable, in this order:

1. The single public constructor, if there is only one.
2. The single public constructor annotated with `@JsonReader`.
3. The single public constructor annotated with `@Json`.
4. The single public constructor with parameters, if there is exactly one such constructor.

If none of these rules produces a single candidate, compilation fails with a message that names the type and the reason.

### Java Bean and plain classes { #java-bean }

`@Json`, `@JsonReader`, and `@JsonWriter` are not limited to `record` and `data class`.
A plain class works too: reading follows the constructor rules above, and writing uses the field accessors.
For every non-static field the writer needs a zero-argument method named `field()` or `getField()` whose return type is the field type; otherwise compilation fails and suggests adding an accessor or excluding the field with `@JsonSkip`.
`@JsonField` may be placed on private fields to rename the `JSON` key:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @JsonWriter
    public class DtoJavaBean {

        @JsonField("string_field")
        private String field1;
        @JsonField("int_field")
        private int field2;

        public DtoJavaBean(String field1, int field2) {
            this.field1 = field1;
            this.field2 = field2;
        }

        public String getField1() { return field1; }

        public int getField2() { return field2; }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @JsonWriter
    class DtoJavaBean(
        @field:JsonField("string_field") val field1: String,
        @field:JsonField("int_field") val field2: Int
    )
    ```

## Value Types { #value-types }

A wrapper type that should appear in `JSON` as a bare scalar rather than as an object is described by putting `@JsonReader` on a static factory method and `@JsonWriter` on the accessor that yields the underlying value.
Kora then generates codecs that delegate to the codecs of that underlying type:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record UserId(long id) {

        @JsonReader //(1)!
        public static UserId of(long value) {
            return new UserId(value);
        }

        @JsonWriter //(2)!
        public long id() {
            return id;
        }
    }
    ```

    1. A `static` factory method with exactly one parameter. The parameter type decides which `JsonReader` is delegated to.
    2. An instance accessor without parameters. A `static` method taking the type itself (`public static long toJson(UserId u)`) works as well.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class UserId(val id: Long) {

        @JsonWriter //(1)!
        fun toJson(): Long = id

        companion object {

            @JsonReader //(2)!
            fun of(value: Long): UserId = UserId(value)
        }
    }
    ```

    1. An instance function without parameters. A `companion object` function taking the type itself (`fun toJson(u: UserId): Long`) works as well.
    2. A `companion object` function with exactly one parameter. The parameter type decides which `JsonReader` is delegated to.

A `UserId` field is then written as `42` instead of `{"id":42}`, and `null` is written as `null`.
This is the equivalent of `Jackson` `@JsonValue` and `@JsonCreator(mode = DELEGATING)`.

Constraints enforced at compile time:

- At most one `@JsonReader` factory method and at most one `@JsonWriter` method per type.
- The factory method must be `public static`, take exactly one parameter, and return the type itself.
- A type cannot have both a `@JsonReader` factory method and a `@JsonReader`/`@Json` constructor.
- The `@JsonWriter` method must be `public` and return a value; a `static` one takes the type as its only parameter, an instance one takes none.
- The delegated type must itself have a `JsonReader` or `JsonWriter` in the graph, which is true for every [supported type](#supported-types).

## JsonNullable Wrapper { #jsonnullable-wrapper }

If reading `JSON` must distinguish an absent field from a field with a `null` value, use `JsonNullable`.
Main states and factory methods:

- `JsonNullable.undefined()` - the field is absent in `JSON`.
- `JsonNullable.nullValue()` - the field is present and contains `null`.
- `JsonNullable.of(value)` - the field is present and contains a value; the argument must not be `null`.
- `JsonNullable.ofNullable(value)` - creates `nullValue()` if the value is `null`, otherwise `of(value)`.

When writing `JSON`, `undefined()` is skipped, `nullValue()` is written as `null`, and `of(value)` writes the value itself.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
    public record Dto(String field1, JsonNullable<Integer> field2) { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    data class Dto(val field1: String, val field2: JsonNullable<Int>)
    ```

### @Nullable vs JsonNullable { #nullable-vs-jsonnullable }

A plain [optional field](#optional-fields) (`@Nullable` in `Java` or a nullable type in `Kotlin`) collapses two different `JSON` inputs into the same value: a field that is **absent** and a field that is present with an explicit `null` both read as `null`.
`JsonNullable` keeps these apart, which is what makes it the correct type for `HTTP` `PATCH` bodies where the client sends only the fields it actually wants to change.

The three read outcomes for a `JsonNullable<T>` field:

| `JSON` input           | Read result               | `isDefined()` | `isNull()` | `value()`     |
|------------------------|---------------------------|---------------|------------|---------------|
| `{}` (field absent)    | `JsonNullable.undefined()`| `false`       | `false`    | throws        |
| `{"field": null}`      | `JsonNullable.nullValue()`| `true`        | `true`     | `null`        |
| `{"field": value}`     | `JsonNullable.of(value)`  | `true`        | `false`    | `value`       |

Because `value()` throws a `NullPointerException` on `undefined()`, always guard access with `isDefined()` (or check `isNull()`) before calling it.

### PATCH partial update { #jsonnullable-patch }

In a `PATCH` request, an absent field means "leave unchanged" while an explicit `null` means "clear the value".
`JsonNullable` lets the handler tell the two apart and apply only the fields the client actually sent:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
    public record UserPatch(JsonNullable<String> name,
                            JsonNullable<String> email) { }

    public void apply(User user, UserPatch patch) {
        if (patch.name().isDefined()) { //(1)!
            user.setName(patch.name().value());
        }
        if (patch.email().isDefined()) {
            user.setEmail(patch.email().value()); //(2)!
        }
        // fields left as undefined() are not touched
    }
    ```

    1. The field was present in the request body, so it must be applied (even if the value is an explicit `null`).
    2. `value()` returns `null` when the client sent `{"email": null}`, which clears the field.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    data class UserPatch(
        val name: JsonNullable<String>,
        val email: JsonNullable<String>
    )

    fun apply(user: User, patch: UserPatch) {
        if (patch.name.isDefined()) { //(1)!
            user.name = patch.name.value()
        }
        if (patch.email.isDefined()) {
            user.email = patch.email.value() //(2)!
        }
        // fields left as undefined() are not touched
    }
    ```

    1. The field was present in the request body, so it must be applied (even if the value is an explicit `null`).
    2. `value()` returns `null` when the client sent `{"email": null}`, which clears the field.

Interaction with [serialization levels](#serialization-levels): `IncludeType.ALWAYS` and `IncludeType.NON_NULL` do **not** change how `JsonNullable` is written - its own rules always win, so an `undefined()` field is omitted and a `nullValue()` field is written as `null` under both.
`IncludeType.NON_EMPTY` is the only level that adds anything, and only when the wrapped type is statically a `Collection` or a `Map`: then a `nullValue()` field and a field holding an empty collection or map are omitted as well.

## Sealed Classes And Interfaces { #sealed-classes-and-interfaces }

If different `JSON` objects should be read and written depending on a specific field value, use a
[sealed class or interface](https://kotlinlang.org/docs/sealed-classes.html) to represent those objects.

Two annotations support sealed types:

1. `@JsonDiscriminatorField` - specifies the discriminator field in the `DTO` marked as a `sealed` class or interface.
2. `@JsonDiscriminatorValue` - specifies one or more discriminator values for a subclass.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
    @JsonDiscriminatorField("type")
    public sealed interface Event {

        @Json
        @JsonDiscriminatorValue("created")
        record Created(String id) implements Event {}

        @Json
        @JsonDiscriminatorValue({"deleted", "removed"}) //(1)!
        record Deleted(String id, boolean permanent) implements Event {}
    }
    ```

    1. Several discriminator values may map to one subclass. On writing, the first value is used.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    @JsonDiscriminatorField("type")
    sealed interface Event {

        @Json
        @JsonDiscriminatorValue("created")
        data class Created(val id: String) : Event

        @Json
        @JsonDiscriminatorValue("deleted", "removed") //(1)!
        data class Deleted(val id: String, val permanent: Boolean) : Event
    }
    ```

    1. Several discriminator values may map to one subclass. On writing, the first value is used.

The `sealed` class or interface itself receives a common `JsonReader` and `JsonWriter`, and that is what an application injects to read or write any subtype.
Each concrete subclass must have its own codec as well, because the generated codec of the `sealed` type takes the subclass codecs as dependencies.
Annotating every subclass with `@Json` (or `@JsonReader`/`@JsonWriter`) is the simplest way to satisfy that.
Sealed abstract classes and nested `sealed` sub-interfaces are supported too - the hierarchy is flattened down to its concrete subclasses.

Rules that apply to the discriminator itself:

- `@JsonDiscriminatorValue` is optional. Without it the discriminator value of a subclass is its simple class name.
- The discriminator field may appear anywhere inside the object; the reader buffers the tokens it has to look past.
- On writing, the discriminator is emitted automatically unless the subclass already declares a field with that `JSON` name - in that case the field itself provides the value.
- `@JsonDiscriminatorField` also accepts `defaultValue`, which is the discriminator used when the field is missing from the document. Without it a missing discriminator is an error.

The `JSON` object below is read into the `Created` class:
```json
{
    "type": "created",
    "id": "1"
}
```

Generic `DTO` types are supported, including generic `sealed` hierarchies.
The codec for each concrete type argument is resolved from the graph like any other field type:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
    @JsonDiscriminatorField("@type")
    public sealed interface Response<T> {

        @Json
        @JsonDiscriminatorValue("ok")
        record Ok<T>(T data) implements Response<T> {}

        @Json
        @JsonDiscriminatorValue("fail")
        record Fail<T>(String error) implements Response<T> {}
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    @JsonDiscriminatorField("@type")
    sealed interface Response<T> {

        @Json
        @JsonDiscriminatorValue("ok")
        data class Ok<T>(val data: T) : Response<T>

        @Json
        @JsonDiscriminatorValue("fail")
        data class Fail<T>(val error: String) : Response<T>
    }
    ```

## Enums { #enum }

For `enum`, `JsonReader` and `JsonWriter` can be generated with the same `@Json`, `@JsonReader`, and `@JsonWriter` annotations.
By default, the `enum` value in `JSON` is the result of `toString()`, so it can be overridden:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
    public enum Status {
        CREATED,
        DELETED;

        @Override
        public String toString() {
            return this.name().toLowerCase();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    enum class Status {
        CREATED,
        DELETED;

        override fun toString(): String {
            return name.lowercase()
        }
    }
    ```

If a value other than the string from `toString()` is needed, annotate a public parameterless method with `@Json`.
In that case, a corresponding `JsonReader` and `JsonWriter` must be available for the return type:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
    public enum Status {
        CREATED(1),
        DELETED(2);

        private final int code;

        Status(int code) {
            this.code = code;
        }

        @Json
        public int code() {
            return this.code;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    enum class Status(private val code: Int) {
        CREATED(1),
        DELETED(2);

        @Json
        fun code(): Int = code
    }
    ```

The mapping from `JSON` values to constants is built once when the codec is created, so reading an `enum` is a single map lookup.
A `JSON` value that does not match any constant is rejected with an error listing the accepted values.

## RawJson { #raw-json }

`RawJson` is used when an object needs to include an already prepared `JSON` fragment without serializing it again.
When written, `RawJson` is passed to the output `JSON` as is, so the value must be a valid `JSON` fragment.

`RawJson` is a **write-only** type: the module provides a `JsonWriter<RawJson>` but no reader, so a `DTO` containing it is annotated with `@JsonWriter` rather than `@Json`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @JsonWriter
    public record Dto(String id, RawJson payload) { }

    var dto = new Dto("1", new RawJson("{\"status\":\"ok\"}"));
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @JsonWriter
    data class Dto(val id: String, val payload: RawJson)

    val dto = Dto("1", RawJson("""{"status":"ok"}"""))
    ```

`RawJson` accepts either a `String` or a `byte[]` and keeps the value as `UTF-8` bytes.
Because the content is already encoded, it is written unquoted; a value that needs `JSON` string quoting must be passed as a regular `String` field instead.

## Custom Field Mappers { #custom-field-mappers }

To use specific mappers only for one field, annotate the field with `@Mapping`.
The annotation can be repeated to specify both a `JsonReader` and a `JsonWriter`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
    public record Dto(
        @Mapping(HexReader.class)
        @Mapping(HexWriter.class)
        Integer code
    ) { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    data class Dto(
        @Mapping(HexReader::class)
        @Mapping(HexWriter::class)
        val code: Int
    )
    ```

Here, `HexReader` implements `JsonReader<Integer>` (`JsonReader<Int>` in `Kotlin`), and `HexWriter` implements the corresponding `JsonWriter`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class HexWriter implements JsonWriter<Integer> { //(1)!

        @Override
        public void write(JsonGenerator generator, Integer value) {
            generator.writeString(Integer.toHexString(value));
        }
    }

    public final class HexReader implements JsonReader<Integer> {

        @Override
        public Integer read(JsonParser parser) {
            if (parser.currentToken() != JsonToken.VALUE_STRING) {
                throw new StreamReadException(parser, "Expected hexadecimal string");
            }
            return Integer.parseInt(parser.getValueAsString(), 16);
        }
    }
    ```

    1. A `final` mapper without constructor dependencies is instantiated by the generated code itself and must **not** be a `@Component`. A mapper that has constructor dependencies must be a graph component - see [Components](container.md#components).

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class HexWriter : JsonWriter<Int> { //(1)!

        override fun write(generator: JsonGenerator, value: Int?) {
            generator.writeString(value!!.toString(16))
        }
    }

    class HexReader : JsonReader<Int> {

        override fun read(parser: JsonParser): Int {
            if (parser.currentToken() != JsonToken.VALUE_STRING) {
                throw StreamReadException(parser, "Expected hexadecimal string")
            }
            return parser.valueAsString.toInt(16)
        }
    }
    ```

    1. A mapper without constructor dependencies (in `Kotlin` classes are `final` by default) is instantiated by the generated code itself and must **not** be a `@Component`. A mapper that has constructor dependencies must be a graph component - see [Components](container.md#components).

## Supported Types { #supported-types }

The module provides built-in types that cover most common tasks.
For collections and maps, Kora uses the `JsonReader` or `JsonWriter` of the element type.

??? abstract "List of supported types"

    * Boolean
    * boolean
    * Short
    * short
    * Integer
    * int
    * Long
    * long
    * Double
    * double
    * Float
    * float
    * byte[]
    * String
    * UUID
    * BigInteger
    * BigDecimal
    * RawJson
    * Object
    * Enum
    * List<T>
    * Set<T>
    * SortedSet<T>
    * Map<String, T>
    * LocalDate
    * LocalTime
    * LocalDateTime
    * Instant
    * OffsetTime
    * OffsetDateTime
    * ZonedDateTime
    * Year
    * YearMonth
    * MonthDay
    * Month
    * DayOfWeek
    * ZoneId
    * Duration

Details worth knowing about that list:

- `byte[]` is written and read as a `Base64` string.
- `RawJson` has a writer only, and `SortedSet<T>` has a reader only.
- `Enum` requires `@Json` on the enum type itself, see [Enums](#enum).
- `Object` reads a `JSON` object into a `LinkedHashMap`, an array into an `ArrayList`, an integer number into a `BigInteger`, and a fractional number into a `Double`.
- Date and time types use the corresponding `ISO` formats; `Month` and `DayOfWeek` are written by name and read from either a name or a number.
- `Map` keys must be strings.

### Custom Types { #custom-types }

If a custom type must be read or written, register a custom [factory](container.md#method-factory) for `JsonReader` or `JsonWriter`.

Example of registering a custom `JsonWriter`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {

        default JsonWriter<ZoneOffset> zoneOffsetJsonWriter() {
            return (generator, value) -> {
                if (value == null) {
                    generator.writeNull();
                } else {
                    generator.writeString(value.getId());
                }
            };
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application {

        fun zoneOffsetJsonWriter(): JsonWriter<ZoneOffset> {
            return JsonWriter { generator, value ->
                if (value == null) {
                    generator.writeNull()
                } else {
                    generator.writeString(value.id)
                }
            }
        }
    }
    ```

Example of registering a custom `JsonReader`.
The reader switches on the current parser token, returns `null` on a `JSON` `null`, reads the expected token, and throws a `StreamReadException` for anything else:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {

        default JsonReader<ZoneOffset> zoneOffsetJsonReader() {
            return parser -> switch (parser.currentToken()) {
                case VALUE_NULL -> null;
                case VALUE_STRING -> ZoneOffset.of(parser.getValueAsString());
                default -> throw new StreamReadException(parser,
                    "Expecting VALUE_STRING token, got " + parser.currentToken());
            };
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application {

        fun zoneOffsetJsonReader(): JsonReader<ZoneOffset> = JsonReader { parser ->
            when (parser.currentToken()) {
                JsonToken.VALUE_NULL -> null
                JsonToken.VALUE_STRING -> ZoneOffset.of(parser.valueAsString)
                else -> throw StreamReadException(parser,
                    "Expecting VALUE_STRING token, got ${parser.currentToken()}")
            }
        }
    }
    ```

A custom `JsonReader<T>` or `JsonWriter<T>` is an ordinary graph component.
Once registered, generated codecs pick it up automatically wherever a field of type `T` occurs, and it can also be pinned to a single field through `@Mapping` (see [Custom Field Mappers](#custom-field-mappers)).

## Errors { #errors }

Everything a codec throws at runtime is a `tools.jackson.core.JacksonException`, which extends `RuntimeException`.
No `JsonReader` or `JsonWriter` method declares a checked exception, so calling code needs neither `throws` nor `try`/`catch` unless it wants to handle the failure.

Reading failures are reported as `tools.jackson.core.exc.StreamReadException`.
Generated readers build messages that name the type, the member, and the `JSON` path of the failing value:

```text
Failed to read json Dto: missing required field(s): field_1 (at <root>)
Failed to read json Dto.field4: required field must not be null (at <root>)
Failed to read json Dto.field2: expected an integer number, but got a string "abc" (at /field2)
```

Sealed hierarchies and enums add their own messages, both listing what was accepted:

```text
Failed to read json Event: missing required discriminator field "type", expected one of [created, deleted, removed] (at <root>)
Failed to read json Event: unknown discriminator value "updated" for field "type", expected one of [created, deleted, removed] (at <root>)
Failed to read json enum: expected one of [1, 2], but got "3" (at /status)
```

When the codec is used through another Kora module the exception is translated at the boundary: a declarative [HTTP server](http-server.md) controller turns a body or parameter that cannot be parsed into a `400` response, and a `Kafka` producer wraps a serialization failure into a `SerializationException`.

Compile-time problems are reported by the Kora processor with the same structure - the type, the problem, a hint, and a fix.
The most common ones are a missing accessor for a written field, an abstract or interface type that is not a supported `sealed` hierarchy, and an ambiguous constructor for a reader.

## Jackson { #jackson }

If `Jackson` databind must be used for reading and writing `JSON` instead of the compile-time generated codecs, use `JacksonModule`.
It provides `@Json`-tagged mappers for the `HTTP` client and the `HTTP` server, and because those are ordinary components while the codec-based ones are default components, the `Jackson` mappers take precedence - see [Standard factory](container.md#default-factory).

`JacksonModule` covers exactly these mappers:

- `HttpServerRequestMapper<T>` and `HttpServerResponseMapper<T>`.
- `HttpClientRequestMapper<T>`, `HttpClientResponseMapper<T>`, and `HttpClientResponseMapper<HttpResponseEntity<T>>`.

Everything else - string parameters, `Kafka`, and any direct `JsonReader`/`JsonWriter` injection - keeps using the generated codecs.

Every `JacksonModule` mapper depends on an `ObjectMapper` component, so a [factory](container.md#method-factory) that supplies `ObjectMapper` **must** be present in the graph. Without it the graph fails to build.

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) in `build.gradle`:
    ```groovy
    annotationProcessor "io.koraframework:annotation-processors"
    implementation "io.koraframework:jackson-module"
    ```

    Module and `ObjectMapper` factory:
    ```java
    @KoraApp
    public interface Application extends JacksonModule {

        default ObjectMapper objectMapper() { //(1)!
            return new ObjectMapper();
        }
    }
    ```

    1. Required by all `JacksonModule` mappers; configure it as needed (modules, features, and so on).

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) in `build.gradle.kts`:
    ```groovy
    ksp("io.koraframework:symbol-processors:2.0.0.RC1")
    implementation("io.koraframework:jackson-module")
    ```

    Module and `ObjectMapper` factory:
    ```kotlin
    @KoraApp
    interface Application : JacksonModule {

        fun objectMapper(): ObjectMapper = ObjectMapper() //(1)!
    }
    ```

    1. Required by all `JacksonModule` mappers; configure it as needed (modules, features, and so on).

The `ObjectMapper` here is `tools.jackson.databind.ObjectMapper`; `jackson-module` brings `Jackson` databind in transitively.

The Kora processor shown above lets `@Json`, `@JsonReader`, and `@JsonWriter` continue to generate codecs, so generated and `Jackson` serialization can coexist (for example, `Jackson` for `HTTP` and generated codecs for [Kafka](kafka.md)).
