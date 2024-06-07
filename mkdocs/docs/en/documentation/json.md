Module allows you to create productive and reflection-free JSON readers and writers for application classes using annotations.

## Dependency

===! ":fontawesome-brands-java: `Java`"

    Dependency `build.gradle`:
    ```groovy
    annotationProcessor "ru.tinkoff.kora:annotation-processors"
    implementation "ru.tinkoff.kora:json-module"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends JsonModule { }
    ```
    
=== ":simple-kotlin: `Kotlin`"

    Dependency `build.gradle.kts`:
    ```groovy
    ksp("ru.tinkoff.kora:symbol-processors")
    implementation("ru.tinkoff.kora:json-module")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : JsonModule
    ```

## Writer

You can use `@JsonWriter` to create a writer only:

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

## Reader

You can use `@JsonReader` to create a reader only:

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

## Reader & Writer

You can use `@Json` to create a reader and a writer at once.
In most cases, it is the `@Json` annotation that is preferred:

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

## Required fields

===! ":fontawesome-brands-java: `Java`"

    By default, all fields declared in an object are considered **required** (*NotNull*).

    ```java
    @Json
    public record Dto(String field1, int field2) { }
    ```

=== ":simple-kotlin: `Kotlin`"

    By default, all fields declared in an object that do not use the [Kotlin Nullability](https://kotlinlang.org/docs/null-safety.html) syntax are considered **required** (*NotNull*).

    ```kotlin
    @Json
    data class Dto(val field1: String, val field2: Int)
    ```

## Optional fields

===! ":fontawesome-brands-java: `Java`"

    In case a field in Json is optional, that is, it may not exist then,
    you can use the `@Nullable` annotation to match the field in Json and DTO:

    ```java
    @Json
    public record Dto(@Nullable String field1, //(1)!
                      int field2) { }
    ```

    1.  Any `@Nullable` annotation will do, such as `javax.annotation.Nullable` / `jakarta.annotation.Nullable` / `org.jetbrains.annotations.Nullable` / etc.

=== ":simple-kotlin: `Kotlin`"

    It is expected to use the [Kotlin Nullability](https://kotlinlang.org/docs/null-safety.html) syntax and mark such a parameter as Nullable:

    ```kotlin
    @Json
    data class Dto(
        val field1: String?,
        val field2: Int
    )
    ```

## Field naming 

In case a field in Json is named differently from what you want to use in a class,
you can use the `@JsonField` annotation to match the field in Json and the DTO.

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

## Field ignore

In case you don't want to read/write a field in DTO,
you can use the `@JsonSkip` annotation and ignore such a field.

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

## Serialization levels

The default behavior is not to write fields with `null` values. (1)
{ .annotate }

1.  `IncludeType.NON_NULL` - include the field in the record if not `null`.

In case you want to change the behavior of the record in these moments, it is suggested to use the `@JsonInclude` annotation.
The annotation can be used not only over a field, but also over a class and then the rule will apply to all fields at once.

Various use cases are available:

- `IncludeType.ALWAYS` - include the field in the record always
- `IncludeType.NON_NULL` - include the field in the record if it is not `null`.
- `IncludeType.NON_EMPTY` - include the field in the record if it is not `null` and not an empty collection

Example of annotation usage:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
    @JsonInclude(IncludeType.NOT_NULL)
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

## Serialization constructor

If you want to use a specific constructor for serialization,
it can be done by specifying the `@JsonReader` annotation above the constructor or the lower-priority `@Json` annotation:

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

## Sealed classes and interfaces

In case you need to write different Json objects depending on the value in a particular field, you are supposed to use an
[isolated class/interface](https://habr.com/ru/companies/otus/articles/720044/) to represent such objects.

Two annotations are added to support isolated classes:

1. `@JsonDiscriminatorField` - specifies the discriminator field in the DTO with which the sealed class/interface is tagged
2. `@JsonDiscriminatorValue` - the value for the above field, marks the inheritor class of the sealed class/interface
3. 
===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
    @JsonDiscriminatorField("type")
    public sealed interface Event {

        @JsonDiscriminatorValue("firstType")
        record FirstTypeEvent(String id, FirstData data) implements Event {}

        @JsonDiscriminatorValue("secondType")
        record SecondTypeEvent(String id, SecondData data) implements Event {}

        @JsonDiscriminatorValue("thirdType")
        record ThirdTypeEvent(String id, ThirdData data) implements Event {}
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    @JsonDiscriminatorField("type")
    sealed interface Event {

        @JsonDiscriminatorValue("firstType")
        data class FirstTypeEvent(val id: String, data: FirstData) : Event

        @JsonDiscriminatorValue("secondType")
        data class SecondTypeEvent(val id: String, data: SecondData) : Event

        @JsonDiscriminatorValue("thirdType")
        data class ThirdTypeEvent(val id: String, data: ThirdData) : Event
    }
    ```

A `JsonReader` and `JsonWriter` will be created for the inheritor classes using the same rules as if they had the `@Json` annotation on them and a `JsonReader` and `JsonWriter` will be created for the sealed class/interface itself.

The Json object below will be written to the `FirstTypeEvent` class:
```json
{
    "id": "1",
    "type": "firstType",
    "data": {
        "megaData": "megaValue"
    }
}
```

## Supported types

Module provides an extensive list of supported out-of-the-box types that cover most of what you might need.

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
    * List<Integer>
    * Set<Integer>
    * LocalDate
    * LocalTime
    * LocalDateTime
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

### Custom types

In case you need to write/read your custom type, it is suggested to register your custom [factory](container.md) for `JsonReader` / `JsonWriter`:

Example of registering a `JsonWriter`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {

        default JsonWriter<ZoneOffset> zoneOffsetJsonWriter() {
            return (generator, value) -> {
                if(value != null) {
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

## Jackson

In case one wants to use `Jackson` for writing/reading, one can register [factory](container.md) that
provide `ObjectMapper` and the corresponding `Mappers` that are required in other Kora modules will be provided by the dependency below:

===! ":fontawesome-brands-java: `Java`"

    Dependency `build.gradle`:
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

    Dependency `build.gradle.kts`:
    ```groovy
    ksp("ru.tinkoff.kora:json-annotation-processor")
    implementation("ru.tinkoff.kora:jackson-module")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : JacksonModule
    ```
