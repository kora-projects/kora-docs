---
description: "Explains Kora JSON reader and writer generation, field requirements, naming, ignores, serialization levels, JsonNullable, sealed types, and Jackson integration. Use when working with @Json, @JsonReader, @JsonWriter, @JsonInclude, @JsonField, @JsonSkip, JsonNullable, JacksonModule."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora JSON reader and writer generation, field requirements, naming, ignores, serialization levels, JsonNullable, sealed types, and Jackson integration; key triggers include @Json, @JsonReader, @JsonWriter, @JsonInclude, @JsonField, @JsonSkip, JsonNullable, JacksonModule."
---

The `JSON` module creates efficient `JsonReader` and `JsonWriter` implementations for application classes at compile time and without using `Reflection` at runtime.
Generation is controlled by `@Json`, `@JsonReader`, `@JsonWriter`, and related field-level annotations.

`JsonModule` also provides ready-to-use mappers for `HTTP` client, `HTTP` server, string parameters, and `Kafka`.
This allows the same generated `JsonReader` or `JsonWriter` to be used across different Kora modules.

For a step-by-step walkthrough before the reference details, see [JSON](../guides/json.md).

## Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) in `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:json-module"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends JsonModule { }
    ```
    
=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) in `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:json-module")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : JsonModule
    ```

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

        public Dto read(String json) throws IOException {
            return this.reader.read(json);
        }

        public byte[] write(Dto dto) throws IOException {
            return this.writer.toByteArray(dto);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyService(
        private val reader: JsonReader<Dto>,
        private val writer: JsonWriter<Dto>
    ) {

        fun read(json: String): Dto? {
            return reader.read(json)
        }

        fun write(dto: Dto): ByteArray {
            return writer.toByteArray(dto)
        }
    }
    ```

`JsonReader` reads a value from `JsonParser`, `byte[]`, `String`, or `InputStream`.
The `readUnchecked(...)` methods do the same, but convert `IOException` to `UncheckedIOException`.

`JsonWriter` writes a value through `JsonGenerator` and can also return `byte[]`, a string, or a formatted string through `toByteArray(...)`, `toString(...)`, and `toPrettyString(...)`.
The `toByteArrayUnchecked(...)`, `toStringUnchecked(...)`, and `toPrettyStringUnchecked(...)` methods convert `IOException` to `UncheckedIOException`.

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

## Optional fields { #optional-fields }

===! ":fontawesome-brands-java: `Java`"

    If a `JSON` field is optional and can be absent, use the `@Nullable` annotation:

    ```java
    @Json
    public record Dto(@Nullable String field1, //(1)!
                      int field2) { }
    ```

    1. Any `@Nullable` annotation is suitable, for example `javax.annotation.Nullable`, `jakarta.annotation.Nullable`, or `org.jetbrains.annotations.Nullable`.

=== ":simple-kotlin: `Kotlin`"

    For `Kotlin`, use [Kotlin Nullability](https://kotlinlang.org/docs/null-safety.html) syntax and mark the parameter as `nullable`:

    ```kotlin
    @Json
    data class Dto(
        val field1: String?,
        val field2: Int
    )
    ```

## Field Naming { #field-naming }

If a field in `JSON` has a different name than the field in the class, use `@JsonField`.
It sets the key name in `JSON` and also allows specifying separate `JsonReader` and `JsonWriter` implementations for a field.

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

If a field needs separate mappers, specify them in `reader` and `writer`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
    public record Dto(@JsonField(value = "created_at",
                                 reader = InstantJsonReader.class,
                                 writer = InstantJsonWriter.class)
                      Instant createdAt) { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    data class Dto(
        @field:JsonField(
            value = "created_at",
            reader = InstantJsonReader::class,
            writer = InstantJsonWriter::class
        )
        val createdAt: Instant
    )
    ```

## Field Ignore { #field-ignore }

If a field in a `DTO` should not be read or written, use `@JsonSkip`.
Such a field is ignored when reading and writing `JSON`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
    public record Dto(String field1, 
                      @JsonSkip int field2) { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    data class Dto(
        val field1: String,
        @field:JsonSkip val field2: Int
    )
    ```

## Serialization Levels { #serialization-levels }

By default, fields with `null` values are not written. (1)
{ .annotate }

1. `IncludeType.NON_NULL` - write the field only if the value is not `null`.

To change this behavior, use `@JsonInclude`.
The annotation can be placed not only on a field, but also on a class; in that case, the rule applies to all fields at once.

Available options:

- `IncludeType.ALWAYS` - always write the field.
- `IncludeType.NON_NULL` - write the field if the value is not `null`.
- `IncludeType.NON_EMPTY` - write the field if the value is not `null` and is not an empty collection or map.

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

`JsonReader` and `JsonWriter` can be generated for classes, `record`, `enum`, and `sealed` types.
For reading a class, there must be one public constructor or a constructor explicitly annotated with `@JsonReader` or `@Json`.

## JsonNullable Wrapper { #jsonnullable-wrapper }

If reading `JSON` must distinguish an absent field from a field with a `null` value, use `JsonNullable`.
Main states and factory methods:

- `JsonNullable.undefined()` - the field is absent in `JSON`.
- `JsonNullable.nullValue()` - the field is present and contains `null`.
- `JsonNullable.of(value)` - the field is present and contains a value.
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

        @JsonDiscriminatorValue("firstType")
        record FirstTypeEvent(String id, String type) implements Event {}

        @JsonDiscriminatorValue("secondType")
        record SecondTypeEvent(String id, Integer code) implements Event {}

        @JsonDiscriminatorValue("thirdType")
        record ThirdTypeEvent(String id, Boolean status) implements Event {}
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    @JsonDiscriminatorField("type")
    sealed interface Event {

        @JsonDiscriminatorValue("firstType")
        data class FirstTypeEvent(val id: String, val type: String) : Event

        @JsonDiscriminatorValue("secondType")
        data class SecondTypeEvent(val id: String, val code: Integer) : Event

        @JsonDiscriminatorValue("thirdType")
        data class ThirdTypeEvent(val id: String, val status: Boolean) : Event
    }
    ```

Subclasses receive `JsonReader` and `JsonWriter` by the same rules as if they were annotated with `@Json`.
The `sealed` class or interface itself also receives a common `JsonReader` and `JsonWriter`.
Nested `sealed` hierarchies are supported, and `@JsonDiscriminatorValue` can accept multiple values for one subclass.

The `JSON` object below is written to the `FirstTypeEvent` class:
```json
{
    "id": "1",
    "type": "firstType",
    "data": {
        "megaData": "megaValue"
    }
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

## RawJson { #raw-json }

`RawJson` is used when an object needs to include an already prepared `JSON` fragment without serializing it again.
When written, `RawJson` is passed to the output `JSON` as is, so the value must be a valid `JSON` fragment.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
    public record Dto(String id, RawJson payload) { }

    var dto = new Dto("1", new RawJson("{\"status\":\"ok\"}"));
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    data class Dto(val id: String, val payload: RawJson)

    val dto = Dto("1", RawJson("""{"status":"ok"}"""))
    ```

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

### Custom Types { #custom-types }

If a custom type must be read or written, register a custom [factory](container.md) for `JsonReader` or `JsonWriter`.

Example of registering a custom `JsonWriter`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {

        default JsonWriter<ZoneOffset> zoneOffsetJsonWriter() {
            return (generator, value) -> {
                if (value != null) {
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
                if (value != null) {
                    generator.writeString(value.id)
                }
            }
        }
    }
    ```

## Jackson { #jackson }

If `Jackson` must be used for reading and writing `JSON`, register a [factory](container.md) in the application graph that provides `ObjectMapper`.
`JacksonModule` adds mappers for `HTTP` client and `HTTP` server that use this `ObjectMapper`.

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) in `build.gradle`:
    ```groovy
    annotationProcessor "ru.tinkoff.kora:json-annotation-processor"
    implementation "ru.tinkoff.kora:jackson-module"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends JacksonModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) in `build.gradle.kts`:
    ```groovy
    ksp("ru.tinkoff.kora:json-annotation-processor")
    implementation("ru.tinkoff.kora:jackson-module")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : JacksonModule
    ```
