---
description: "Explains the Kora validation constraint annotations, class and method validation, argument and result validation, configuration validation, custom constraints, mapping validation failures to HTTP 400, and supported validation signatures. Use when working with @Valid, @Validate, @ValidatedBy, @NotBlank, @NotEmpty, @Pattern, @Size, @OneOf, @UUID, @Uri, @Url, @Range, @Min, @Max, @Positive, @Negative, @Digits, @Past, @Future, @AssertTrue, ValidatorModule, ValidationModule."
agent:
  use_when: "Use this file for Kora docs or implementation questions about validation constraint annotations, class and method validation, argument and result validation, configuration validation, custom constraints, mapping ViolationException to HTTP 400, and supported validation signatures; key triggers include @Valid, @Validate, @ValidatedBy, @NotBlank, @NotEmpty, @Pattern, @Size, @OneOf, @UUID, @Uri, @Url, @Range, @Min, @Max, @Positive, @PositiveOrZero, @Negative, @NegativeOrZero, @Digits, @Past, @PastOrPresent, @Future, @FutureOrPresent, @AssertTrue, @AssertFalse, Validator, ValidatorFactory, ValidationContext, Violation, ViolationException, ValidationHttpServerInterceptor, ViolationExceptionHttpServerResponseMapper, ValidatorModule, ValidationModule, validation-common, validation-module."
---

The Kora validation module checks models, method arguments, and method results using annotations.
For models, Kora generates a `Validator<T>` at compile time, and for methods it applies the `@Validate` aspect that calls the required checks before or after method execution.

Validation works without using `Reflection` at application runtime: object structure, nested fields, method signatures, and available validators are checked by annotation processors during the build.
Validation errors are returned as a list of `Violation` or thrown as `ViolationException`.

For a step-by-step walkthrough before the reference details, see [Validation](../guides/validation.md).

## Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) in `build.gradle`:
    ```groovy
    annotationProcessor "io.koraframework:annotation-processors" //(1)!
    implementation "io.koraframework:validation-module"
    ```

    1. The annotation processor generates the `Validator<T>` implementations and the `@Validate` aspect at compile time. Without it no validator is created and the graph build fails with a missing `Validator` dependency.

    Module:
    ```java
    @KoraApp
    public interface Application extends ValidationModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) in `build.gradle.kts`:
    ```groovy
    ksp("io.koraframework:symbol-processors:2.0.0.RC1") //(1)!
    implementation("io.koraframework:validation-module")
    ```

    1. The `KSP` processor generates the `Validator<T>` implementations and the `@Validate` aspect at compile time. Without it no validator is created and the graph build fails with a missing `Validator` dependency.

    Module:
    ```kotlin
    @KoraApp
    interface Application : ValidationModule
    ```

The framework ships two mixin interfaces, and you pick one depending on whether the application serves `HTTP`:

| Module | Type | Artifact | Provides | Use when |
|--------|------|----------|----------|----------|
| `ValidatorModule` | `io.koraframework.validation.common.constraint.ValidatorModule` | `validation-common` | Every built-in constraint factory and the element validators `Validator<List<T>>`, `Validator<Set<T>>`, `Validator<Collection<T>>` | Libraries, `CLI` tools and non-`HTTP` applications, or when you handle `ViolationException` yourself |
| `ValidationModule` | `io.koraframework.validation.module.ValidationModule` | `validation-module` | Everything from `ValidatorModule` **plus** the `ValidationHttpServerInterceptor` that maps `ViolationException` to an [HTTP 400 response](#validation-response-http) | `HTTP` services that should return `400` to clients automatically |

`ValidationModule` extends `ValidatorModule`, so wiring `ValidationModule` also gives you everything the base module provides.
Generated `Validator<T>` components do not come from either mixin — they are contributed by the annotation processor for every type marked with [`@Valid`](#class-validation) and can be injected without wiring anything else.

!!! warning "Applications without an HTTP server"

    `validation-module` declares `http-server-common` as a **compile-only** dependency, and `ValidationModule` contributes a `ValidationHttpServerInterceptor` whose signature is written in terms of `HttpServerRequest` and `HttpServerResponse`.
    An application that has no `HTTP` server therefore either has to put `http-server-common` on the classpath explicitly, or — the better option — depend on `validation-common` and wire `ValidatorModule` instead.
    That is exactly what a client-only or batch application should do.

## Validation Annotations { #validation-annotations }

Validation annotations tell Kora what to check on a field, method argument, or method result.
They can be applied directly, or nested validation can be triggered through `@Valid` when the type has a generated or manually provided `Validator`.

!!! warning "Kora validation is not Jakarta Bean Validation"

    Kora validation is **not** [Jakarta Bean Validation (JSR-380)](https://jakarta.ee/specifications/bean-validation/).
    All Kora constraint annotations live in the `io.koraframework.validation.common.annotation` package, are ordinary declaration annotations (not `TYPE_USE`), and are processed at compile time.
    Names overlap with the Jakarta ones on purpose, but the semantics are Kora's own — importing `jakarta.validation.constraints.*` by mistake produces a type that Kora simply ignores.
    In particular, Kora ships **no** `@NotNull` constraint annotation: a value is required by default, and to make it optional you mark it with any `@Nullable` annotation (see [Optional Fields](#optional-fields)).
    Kora does recognize an explicit not-`null` marker — any annotation whose simple name is `Nonnull`, `NotNull`, or `NonNull` — which matters mainly for [`JsonNullable`](#json-nullable) fields.

The structural annotations that drive validation:

- `@Valid` - on a class, `record` or `sealed` interface generates a `Validator<T>` for that type; on a field, argument, or method result triggers nested validation through the `Validator` of the corresponding type. Applicable to types, fields, parameters, and methods.
- `@Validate` - marks a method whose arguments and/or result should be validated by the aspect; the `failFast` parameter controls stopping on the first error (default: `false`). Applicable to methods only.
- `@ValidatedBy` - links a custom constraint annotation with a `ValidatorFactory` that builds its `Validator` (see [Custom Validation Annotations](#custom-validation-annotations)). Applicable to annotation types only.

Kora ships 22 built-in constraints. Every one of them is itself annotated with `@ValidatedBy`, so they use the same extension mechanism a custom constraint uses:

| Annotation | Supported types | Attributes (defaults) | Check |
|------------|-----------------|-----------------------|-------|
| `@NotBlank` | `String`, `CharSequence` | — | Value is not `null` and contains at least one non-whitespace character. |
| `@NotEmpty` | `String`, `CharSequence`, `Iterable<T>`, `Collection<T>`, `List<T>`, `Set<T>`, `Map<K, V>` | — | Value is not `null` and its length or size is greater than zero. |
| `@Pattern` | `String`, `CharSequence` | `value` (required, no default), `flags` (default: `0`) | Value **fully** matches the `value` regular expression; `flags` maps to [`java.util.regex.Pattern`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/regex/Pattern.html#field.summary) flags. |
| `@Size` | `String`, `CharSequence`, `Collection<V>`, `List<V>`, `Set<V>`, `Map<K, V>` | `min` (default: `0`), `max` (required, no default) | Length or size of the value lies within `[min, max]`, both bounds inclusive. |
| `@OneOf` | `String`, `CharSequence` | `value` (`String[]`, required, no default) | Value is `toString()`-equal to one of the listed strings. |
| `@UUID` | `String`, `CharSequence` | — | Value parses with `java.util.UUID.fromString(...)`. |
| `@Uri` | `String`, `CharSequence` | — | Value parses as a `java.net.URI`. |
| `@Url` | `String`, `CharSequence` | — | Value parses as a `java.net.URI` **and** has both a scheme and a host, i.e. it is an absolute `URL`. |
| `@Range` | `Short`, `Integer`, `Long`, `Float`, `Double`, `BigInteger`, `BigDecimal` | `from` (`double`, required, no default), `to` (`double`, required, no default), `boundary` (default: `INCLUSIVE_INCLUSIVE`) | Number lies between `from` and `to`; `boundary` decides whether each bound is inclusive. |
| `@Min` | `Short`, `Integer`, `Long`, `Float`, `Double`, `BigInteger`, `BigDecimal` | `value` (`long`, required, no default) | Number is greater than or equal to `value`. |
| `@Max` | `Short`, `Integer`, `Long`, `Float`, `Double`, `BigInteger`, `BigDecimal` | `value` (`long`, required, no default) | Number is less than or equal to `value`. |
| `@Positive` | any `Number` | — | Number is strictly greater than zero. |
| `@PositiveOrZero` | any `Number` | — | Number is greater than or equal to zero. |
| `@Negative` | any `Number` | — | Number is strictly less than zero. |
| `@NegativeOrZero` | any `Number` | — | Number is less than or equal to zero. |
| `@Digits` | `Short`, `Integer`, `Long`, `Float`, `Double`, `BigInteger`, `BigDecimal`, `String`, `CharSequence` | `integer` (`int`, required, no default), `fraction` (`int`, required, no default) | After trailing zeros are stripped, the integer part has at most `integer` digits and the fraction part at most `fraction` digits. |
| `@Past` | `LocalDate`, `LocalDateTime`, `Instant`, `OffsetDateTime`, `ZonedDateTime` | — | Value is strictly before the current moment. |
| `@PastOrPresent` | `LocalDate`, `LocalDateTime`, `Instant`, `OffsetDateTime`, `ZonedDateTime` | — | Value is before or equal to the current moment. |
| `@Future` | `LocalDate`, `LocalDateTime`, `Instant`, `OffsetDateTime`, `ZonedDateTime` | — | Value is strictly after the current moment. |
| `@FutureOrPresent` | `LocalDate`, `LocalDateTime`, `Instant`, `OffsetDateTime`, `ZonedDateTime` | — | Value is after or equal to the current moment. |
| `@AssertTrue` | `Boolean` | — | Value is `true`. |
| `@AssertFalse` | `Boolean` | — | Value is `false`. |

!!! note

    Every constraint reports a violation for a `null` value on its own, in addition to the required-value check that Kora generates for a non-optional field or argument.
    That means a required `String` field annotated with `@NotBlank` produces **two** violations when it is `null` in the default `Full` mode.
    Applying a constraint to a type it has no factory for is a build error: there is no `Validator` for that combination, and the graph fails with a missing dependency rather than silently skipping the check.

### Text constraints { #text-constraints }

`@NotBlank`, `@NotEmpty`, `@Pattern`, `@Size`, `@OneOf`, `@UUID`, `@Uri`, and `@Url` all work on `String` and `CharSequence`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Valid
    public record Account(@NotBlank String owner, //(1)!
                          @NotEmpty String reference, //(2)!
                          @Size(min = 3, max = 64) String title, //(3)!
                          @Pattern("ACC\\d{10}") String number, //(4)!
                          @OneOf({"NEW", "ACTIVE", "CLOSED"}) String status, //(5)!
                          @UUID String correlationId, //(6)!
                          @Url String callback, //(7)!
                          @Uri String resource) { } //(8)!
    ```

    1. Rejects `null`, an empty string, and a string of whitespace only.
    2. Rejects `null` and an empty string; a string of spaces passes.
    3. Length must be between `3` and `64`, both inclusive.
    4. `Pattern.matches` semantics — the **whole** value must match, no partial match.
    5. Exactly one of the listed strings.
    6. Must parse with `java.util.UUID.fromString(...)`.
    7. Must be an absolute `URL`, i.e. have a scheme and a host.
    8. Must parse as a `URI`; a relative reference such as `/orders/1` is accepted.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Valid
    data class Account(@field:NotBlank val owner: String, //(1)!
                       @field:NotEmpty val reference: String, //(2)!
                       @field:Size(min = 3, max = 64) val title: String, //(3)!
                       @field:Pattern("ACC\\d{10}") val number: String, //(4)!
                       @field:OneOf("NEW", "ACTIVE", "CLOSED") val status: String, //(5)!
                       @field:UUID val correlationId: String, //(6)!
                       @field:Url val callback: String, //(7)!
                       @field:Uri val resource: String) //(8)!
    ```

    1. Rejects `null`, an empty string, and a string of whitespace only.
    2. Rejects `null` and an empty string; a string of spaces passes.
    3. Length must be between `3` and `64`, both inclusive.
    4. `Pattern.matches` semantics — the **whole** value must match, no partial match.
    5. Exactly one of the listed strings.
    6. Must parse with `java.util.UUID.fromString(...)`.
    7. Must be an absolute `URL`, i.e. have a scheme and a host.
    8. Must parse as a `URI`; a relative reference such as `/orders/1` is accepted.

!!! note

    The Kora annotation is named `UUID`, which collides with `java.util.UUID` when both are star-imported.
    Import the constraint explicitly as `io.koraframework.validation.common.annotation.UUID`, or qualify `java.util.UUID` at its use site.

### Numeric constraints { #numeric-constraints }

`@Range`, `@Min`, `@Max`, `@Positive`, `@PositiveOrZero`, `@Negative`, `@NegativeOrZero`, and `@Digits` work on numbers:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Valid
    public record Order(@Range(from = 1, to = 900) int weight, //(1)!
                        @Range(from = 0, to = 1, boundary = Range.Boundary.INCLUSIVE_EXCLUSIVE) double share, //(2)!
                        @Min(1) long quantity, //(3)!
                        @Max(100) int discount, //(4)!
                        @Positive BigDecimal amount, //(5)!
                        @PositiveOrZero int retries, //(6)!
                        @Negative int correction, //(7)!
                        @NegativeOrZero int balanceDelta, //(8)!
                        @Digits(integer = 10, fraction = 2) BigDecimal price) { } //(9)!
    ```

    1. Both bounds inclusive by default.
    2. `[0, 1)` — the lower bound is included, the upper bound is not.
    3. `quantity >= 1`.
    4. `discount <= 100`.
    5. Strictly greater than zero.
    6. Greater than or equal to zero.
    7. Strictly less than zero.
    8. Less than or equal to zero.
    9. At most 10 digits before the decimal point and 2 after it.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Valid
    data class Order(@field:Range(from = 1.0, to = 900.0) val weight: Int, //(1)!
                     @field:Range(from = 0.0, to = 1.0, boundary = Range.Boundary.INCLUSIVE_EXCLUSIVE) val share: Double, //(2)!
                     @field:Min(1) val quantity: Long, //(3)!
                     @field:Max(100) val discount: Int, //(4)!
                     @field:Positive val amount: BigDecimal, //(5)!
                     @field:PositiveOrZero val retries: Int, //(6)!
                     @field:Negative val correction: Int, //(7)!
                     @field:NegativeOrZero val balanceDelta: Int, //(8)!
                     @field:Digits(integer = 10, fraction = 2) val price: BigDecimal) //(9)!
    ```

    1. Both bounds inclusive by default.
    2. `[0, 1)` — the lower bound is included, the upper bound is not.
    3. `quantity >= 1`.
    4. `discount <= 100`.
    5. Strictly greater than zero.
    6. Greater than or equal to zero.
    7. Strictly less than zero.
    8. Less than or equal to zero.
    9. At most 10 digits before the decimal point and 2 after it.

`Range.Boundary` has four variants — `EXCLUSIVE_EXCLUSIVE`, `INCLUSIVE_EXCLUSIVE`, `EXCLUSIVE_INCLUSIVE`, and `INCLUSIVE_INCLUSIVE` — and the default is `INCLUSIVE_INCLUSIVE`.

!!! note

    `@Range.from` and `@Range.to` are declared as `double`, and the runtime narrows them to the field type: to `long` for `Short`/`Integer`/`Long`, to `BigInteger`/`BigDecimal` for the big types, and to `double` for `Float`/`Double`.
    A bound larger than 2<sup>53</sup> therefore cannot be expressed exactly through `@Range` — use `@Min` and `@Max`, whose attribute is a `long`.
    `@Range` also rejects an inverted range at construction time: `to` must be greater than or equal to `from`, and the same rule holds for `@Size`, which additionally requires `min >= 0`.

### Temporal constraints { #temporal-constraints }

`@Past`, `@PastOrPresent`, `@Future`, and `@FutureOrPresent` compare the value with the current moment of the matching type — `LocalDate.now()` for `LocalDate`, `Instant.now()` for `Instant`, and so on:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Valid
    public record Contract(@Past LocalDate signedAt, //(1)!
                           @PastOrPresent Instant createdAt, //(2)!
                           @Future OffsetDateTime expiresAt, //(3)!
                           @FutureOrPresent ZonedDateTime activeFrom) { } //(4)!
    ```

    1. Strictly in the past.
    2. In the past or exactly now.
    3. Strictly in the future.
    4. In the future or exactly now.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Valid
    data class Contract(@field:Past val signedAt: LocalDate, //(1)!
                        @field:PastOrPresent val createdAt: Instant, //(2)!
                        @field:Future val expiresAt: OffsetDateTime, //(3)!
                        @field:FutureOrPresent val activeFrom: ZonedDateTime) //(4)!
    ```

    1. Strictly in the past.
    2. In the past or exactly now.
    3. Strictly in the future.
    4. In the future or exactly now.

The supported types are exactly `LocalDate`, `LocalDateTime`, `Instant`, `OffsetDateTime`, and `ZonedDateTime`.
For any other temporal type — `LocalTime`, `Year`, `java.util.Date` — declare a [custom constraint](#custom-validation-annotations).

### Boolean constraints { #boolean-constraints }

`@AssertTrue` and `@AssertFalse` apply to `Boolean`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Valid
    public record Consent(@AssertTrue Boolean termsAccepted, //(1)!
                          @AssertFalse Boolean blocked) { } //(2)!
    ```

    1. Must be `true`; `null` and `false` both produce a violation.
    2. Must be `false`; `null` and `true` both produce a violation.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Valid
    data class Consent(@field:AssertTrue val termsAccepted: Boolean, //(1)!
                       @field:AssertFalse val blocked: Boolean) //(2)!
    ```

    1. Must be `true`; `null` and `false` both produce a violation.
    2. Must be `false`; `null` and `true` both produce a violation.

### Collection constraints { #collection-constraints }

`@NotEmpty` and `@Size` also work on collections and maps, where they check the number of elements rather than a string length:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Valid
    public record Basket(@NotEmpty List<String> items, //(1)!
                         @Size(min = 1, max = 10) Set<String> tags, //(2)!
                         @Size(max = 20) Map<String, String> attributes) { } //(3)!
    ```

    1. At least one element.
    2. Between `1` and `10` elements.
    3. At most `20` entries; `min` defaults to `0`.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Valid
    data class Basket(@field:NotEmpty val items: List<String>, //(1)!
                      @field:Size(min = 1, max = 10) val tags: Set<String>, //(2)!
                      @field:Size(max = 20) val attributes: Map<String, String>) //(3)!
    ```

    1. At least one element.
    2. Between `1` and `10` elements.
    3. At most `20` entries; `min` defaults to `0`.

These constraints look only at the container. To also validate every element, combine them with `@Valid` — see [Collection Validation](#collection-validation).

### Violation Messages { #violation-messages }

Every built-in constraint produces an English message that names the rule and the actual value, so the default `HTTP` `400` body is already diagnosable without any extra wiring:

| Constraint | Message |
|------------|---------|
| `@NotBlank` | `Should be not blank, but was null` / `... but was empty` / `... but was blank` |
| `@NotEmpty` | `Should be not empty, but was null` / `... but was empty` |
| `@Pattern` | `Should match RegEx ACC\d{10} but was: ACC1` |
| `@Size` on a `String` | `Length should be in range from '3' to '64', but was smaller: 2` |
| `@Size` on a collection or map | `Size should be in range from '1' to '10', but was greater: 11` |
| `@OneOf` | `Should be one of [NEW, ACTIVE, CLOSED], but was: DRAFT` |
| `@UUID` / `@Uri` / `@Url` | `Should be valid UUID, but was: abc` (and the `URI` / `URL` variants) |
| `@Range` | `Should be in range from '1' to '900', but was greater: 1000` |
| `@Min` / `@Max` | `Should be greater than or equal to '1', but was: 0` / `Should be less than or equal to '100', but was: 101` |
| `@Positive` and friends | `Should be positive, but was: -1` |
| `@Digits` | `Should have digits with integer part up to '10' and fraction part up to '2', but was: 1.234` |
| `@Past` and friends | `Should be in the past, but was: 2999-01-01` |
| `@AssertTrue` / `@AssertFalse` | `Should be true, but was: false` |
| generated required check on a field | `Must be non null, but was null` |
| generated required check on an argument | `Parameter 'code' must be non null, but was null` |
| generated required check on a result | `Result must be non null, but was null` |

Each `Violation` also carries a `path()`. The path is built as the object is walked: a nested field appends `.field`, and a collection element appends `.[index]`.
A violation on the `number` field of the second element of a `bars` list therefore reports `bars.[1].number`, and `Violation.path().full()` returns exactly that string.

## Class Validation { #class-validation }

The `@Valid` annotation on a class or `record` tells Kora to create a `Validator<T>` for that type.
The generated validator becomes a regular dependency graph component and can be injected by the `Validator<Type>` signature.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Valid
    public record User(@NotBlank String id,
                       @Size(min = 3, max = 6) String name,
                       @Nullable String status) { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Valid
    data class User(@field:NotBlank val id: String,
                    @field:Size(min = 3, max = 6) val name: String,
                    val status: String?)
    ```

A validator for this class will then be available in the dependency container:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class Example {

        private final Validator<User> userValidator;

        public Example(Validator<User> userValidator) {
            this.userValidator = userValidator;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class Example(val userValidator: Validator<User>)
    ```

Generated validators can be injected as dependencies into any component.
In the example above, the validator for `User` is injected by the `Validator<User>` signature and can be used manually.

The `validate(...)` method returns a list of `Violation`.
You can process this list yourself or call `validateAndThrow(...)`, which throws `ViolationException` if there are violations.
See [Manual Validation](#manual-validation) for the full imperative API.

### Field Validation { #field-validation }

Field validation uses the set of [annotations](#validation-annotations) provided by the module.

An object marked for validation looks like this:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Valid
    public record Foo(@NotEmpty String number) { }
    ```

    For a `record`, fields are accessed through the methods of the `record` itself.
    For `Foo` and the `number` field, the generated `Validator` will use the `number()` method.

    For a regular class, the `JavaBeans` syntax is used: for example, the `getId()` method will be used for the `id` field.
    This method must have at least `package-private` visibility.
    `static` fields are skipped, so a constant next to the validated data is never picked up.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Valid
    data class Foo(@field:NotEmpty val number: String)
    ```

    Properties are read directly, so both a `data class` and a plain `class` with `var` properties work.
    `const` and `@JvmStatic` members are skipped, so a constant in a `companion object` next to the validated data is never picked up.

    The constraint can be written either with the `@field:` use-site target or without it — for a constructor property Kora also reads the annotations of the matching primary-constructor parameter.
    For a property declared in the class body, put the annotation on the property.

#### Required Fields { #required-fields }

All fields are considered required by default, so `null` checks are created for them.

#### Optional Fields { #optional-fields }

===! ":fontawesome-brands-java: `Java`"

    To mark a field as optional, annotate it with any `@Nullable` annotation.
    For such a field, a `null` check **will not** be created:

    ```java
    @Valid
    public record Foo(@Nullable String number) { } //(1)!
    ```

    1. Kora is built on [JSpecify](https://jspecify.dev/), so `org.jspecify.annotations.Nullable` is the recommended annotation; any annotation whose simple name is `Nullable` is accepted. `JSpecify` `@Nullable` is a *type-use* annotation, so its position matters for qualified and generic types: `List<@Nullable String>`, `Outer.@Nullable Inner`.

=== ":simple-kotlin: `Kotlin`"

    To mark a field as optional, use [`Kotlin Nullability`](https://kotlinlang.org/docs/null-safety.html) syntax and add `?` to the field type.
    For such a field, a `null` check **will not** be created:

    ```kotlin
    @Valid
    data class Foo(val number: String?)
    ```

    `Kotlin` carries no nullability annotation of its own — `T?` is the whole declaration.

A constraint still runs on an optional field when the value is present, so `@Nullable @Size(min = 1, max = 10) String status` means "may be absent, but if present its length is between 1 and 10".

#### Nested Fields { #embedded-fields }

Use `@Valid` to validate nested objects that have generated or manually provided validators.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Valid
    public record Foo(@Valid Bar bar) { }

    @Valid
    public record Bar(String number) { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Valid
    data class Foo(@field:Valid val bar: Bar)

    @Valid
    data class Bar(val number: String)
    ```

In the example above, `Validator<Bar>` will be created for `Bar`, and `Validator<Foo>` will be created for `Foo`.
When `Validator<Foo>` is called, it will call `Validator<Bar>` internally, and a violation inside `Bar` is reported at the path `bar.<field>`.

#### Collection Validation { #collection-validation }

`@Valid` on a `List`, `Set`, or `Collection` field validates **every element** through the element's `Validator`.
The `ValidatorModule` provides these element validators out of the box (`Validator<List<T>>`, `Validator<Set<T>>`, `Validator<Collection<T>>`), so no extra wiring is needed.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Valid
    public record Foo(@Size(min = 1, max = 5) @Valid List<Bar> bars) { }

    @Valid
    public record Bar(@NotBlank String number) { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Valid
    data class Foo(@field:Size(min = 1, max = 5) @field:Valid val bars: List<Bar>)

    @Valid
    data class Bar(@field:NotBlank val number: String)
    ```

Each `Bar` in the list is validated, and the violation path is indexed by element position, for example `bars.[0].number`.
Constraints such as [`@Size`](#collection-constraints) can be combined with `@Valid` on the same collection to check both the collection size and each element, as above.

!!! note

    Element validation itself is silent about a `null` collection — the required check for the field is what reports it.
    A `Map` has no element validator out of the box: `@Valid` on a `Map` field needs a `Validator<Map<K, V>>` supplied by the application.

#### `Sealed` Hierarchies { #sealed-validation }

Kora can create a `Validator` for `sealed` hierarchies.
If `@Valid` is placed on a `sealed` type, the generated validator determines the actual subtype and calls the validator for the matching final implementation, so every permitted subtype must be annotated with `@Valid` too.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Valid
    public sealed interface Command permits CreateCommand {

        @Valid
        record CreateCommand(@NotBlank String name) implements Command { }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Valid
    sealed interface Command {

        @Valid
        data class CreateCommand(@field:NotBlank val name: String) : Command
    }
    ```

Only `sealed` **interfaces** are dispatched this way, and only final permitted subtypes are collected.

#### `JsonNullable` { #json-nullable }

For [`JsonNullable<T>`](json.md#jsonnullable-wrapper), Kora validates the `T` value inside the container:

- `undefined` — the field was absent from the payload; the constraints are **not** executed.
- `null` — the field was present with a `null` value; the constraints run against `null` and normally report a violation.
- present — the constraints run against the value.

To reject both `undefined` and `null` outright, add an explicit not-`null` marker (any annotation whose simple name is `Nonnull`, `NotNull`, or `NonNull`) next to the `JsonNullable` field.
This is the only place where such a marker changes validation: everywhere else "required" is simply the absence of `@Nullable`.

#### Unsupported Targets { #unsupported-targets }

`@Valid` needs a type that exposes fields or properties to check, so the processor rejects two shapes with a build error:

- an `enum` — put the constraints on the class that holds the enum value, or write a [custom constraint](#custom-validation-annotations) for it;
- a non-`sealed` interface that is not a [configuration](#configuration-validation) interface — annotate the implementation instead.

#### Validation Options { #validation-options }

There are two validation modes, selected through the `ValidationContext` passed to `validate(...)`:

- `Full` - all marked fields are checked, all possible validation errors are collected, and only then a list of violations is returned or an exception is thrown. This is the default behavior.
- `FailFast` - validation stops on the first found error.

A `ValidationContext` can be built in several equivalent ways:

- `ValidationContext.builder().build()` - default `Full` context (same as calling `validate(value)` without a context).
- `ValidationContext.full()` - explicit `Full` context.
- `ValidationContext.failFast()` - `FailFast` context.
- `ValidationContext.builder().failFast(true).build()` - builder form of `FailFast`.

Example of `FailFast` validation:

===! ":fontawesome-brands-java: `Java`"

    ```java
    ValidationContext context = ValidationContext.failFast();
    List<Violation> violations = userValidator.validate(value, context);
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val context = ValidationContext.failFast()
    val violations = userValidator.validate(value, context)
    ```

### Configuration Validation { #configuration-validation }

`@Valid` also applies to a [configuration](config.md#custom-configuration) interface annotated with `@ConfigSource` or `@ConfigMapper`.
The accessor methods are treated as the fields to check, and the generated configuration mapper calls `validateAndThrow(...)` right after the configuration object is built — so a wrong value fails the application on startup instead of at the first use.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Valid
    @ConfigSource("services.foo")
    public interface FooServiceConfig {

        @NotBlank
        String url();

        @Range(from = 1, to = 65535)
        int port();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Valid
    @ConfigSource("services.foo")
    interface FooServiceConfig {

        @NotBlank
        fun url(): String

        @Range(from = 1.0, to = 65535.0)
        fun port(): Int
    }
    ```

This is the one case where `@Valid` on an interface is allowed, and it is described together with the rest of the configuration rules in [Configuration](config.md#validation).

### Manual Validation { #manual-validation }

A generated `Validator<T>` is an ordinary component, so it can be injected and called directly — for example in a service that is not an `HTTP` controller, or when you want to inspect violations instead of throwing.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class UserService {

        private final Validator<User> validator;

        public UserService(Validator<User> validator) {
            this.validator = validator;
        }

        public void process(User user) {
            List<Violation> violations = validator.validate(user); //(1)!
            if (!violations.isEmpty()) {
                Violation first = violations.getFirst();
                throw new IllegalStateException(first.path().full() + ": " + first.message()); //(2)!
            }
        }
    }
    ```

    1. `validate(value)` collects **all** violations; use `validate(value, context)` to pass validation options.
    2. Each `Violation` exposes `path()` and `message()`.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class UserService(private val validator: Validator<User>) {

        fun process(user: User) {
            val violations = validator.validate(user) //(1)!
            if (violations.isNotEmpty()) {
                val first = violations.first()
                throw IllegalStateException("${first.path().full()}: ${first.message()}") //(2)!
            }
        }
    }
    ```

    1. `validate(value)` collects **all** violations; use `validate(value, context)` to pass validation options.
    2. Each `Violation` exposes `path()` and `message()`.

The `Validator<T>` contract offers the following methods:

- `validate(value)` / `validate(value, context)` - return a `List<Violation>` that is empty when the value is valid.
- `validateAndThrow(value)` / `validateAndThrow(value, context)` - throw `ViolationException` when any violation occurs, and do nothing otherwise.

Passing `null` to any of them is not a shortcut for "nothing to check": a generated validator reports a single violation for the `null` input.

When a `ViolationException` is caught, `getViolations()` returns the aggregated `List<Violation>`, and `getMessage()` returns a preformatted multi-line summary:

```text
Validation failed with 2 violations:
1) Path 'name' violation: Length should be in range from '3' to '6', but was smaller: 2
2) Path 'bars.[0].number' violation: Should be not blank, but was blank
```

## Method Validation { #method-validation }

Method argument and result validation uses the `@Validate` aspect and the set of [annotations](#validation-annotations) provided by the module.
Kora generates aspect code at compile time, so a class with such methods must support aspect application.

### Argument Validation { #argument-validation }

To validate method arguments, use the `@Validate` annotation on the method and annotate the arguments with the required [constraints](#validation-annotations).
Arguments can be validated by constraint annotations directly, or by `@Valid` when the argument type has its own `Validator`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class ArgumentValidator {

        @Valid
        public record User(@NotBlank String id,
                           @Size(min = 3, max = 6) String name,
                           @Nullable String status) { }

        @Validate
        public int calculate(@Valid User user, //(1)!
                             @Range(from = 1, to = 900) int weight, //(2)!
                             @Pattern("ME\\d+") String code) { //(3)!
            return Integer.parseInt(code.substring(2));
        }
    }
    ```

    1. Nested validation through `Validator<User>`.
    2. Numeric range constraint applied directly to the argument.
    3. Regular expression constraint applied directly to the argument.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    open class ArgumentValidator {

        @Valid
        data class User(@field:NotBlank val id: String,
                        @field:Size(min = 3, max = 6) val name: String,
                        val status: String?)

        @Validate
        open fun calculate(@Valid user: User, //(1)!
                           @Range(from = 1.0, to = 900.0) weight: Int, //(2)!
                           @Pattern("ME\\d+") code: String): Int { //(3)!
            return code.substring(2).toInt()
        }
    }
    ```

    1. Nested validation through `Validator<User>`.
    2. Numeric range constraint applied directly to the argument.
    3. Regular expression constraint applied directly to the argument.

If any argument fails validation, the aspect throws `ViolationException` **before** the method body runs.
Argument violations are reported at the path of the parameter name, for example `code` or `user.name`.

#### Required Arguments { #required-arguments }

All arguments are considered required by default, so `null` checks are created for them.
Primitive arguments are never `null`-checked — there is nothing to check.

#### Optional Arguments { #optional-arguments }

===! ":fontawesome-brands-java: `Java`"

    To mark an argument as optional, annotate it with any `@Nullable` annotation.
    For such an argument, a `null` check **will not** be created:

    ```java
    @Component
    public class SomeService {

        @Validate
        public int validate(@Nullable String argument) { //(1)!
            return 1;
        }
    }
    ```

    1. `org.jspecify.annotations.Nullable` is the annotation Kora itself is built on; any annotation whose simple name is `Nullable` is accepted.

=== ":simple-kotlin: `Kotlin`"

    To mark an argument as optional, use [`Kotlin Nullability`](https://kotlinlang.org/docs/null-safety.html) syntax and add `?` to the argument type.
    For such an argument, a `null` check **will not** be created:

    ```kotlin
    @Component
    open class SomeService {

        @Validate
        open fun validate(argument: String?): Int {
            return 1
        }
    }
    ```

#### Nested Arguments { #embedded-arguments }

Use `@Valid` to validate nested arguments that have generated or manually provided validators.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Valid
    public record Foo(@NotEmpty String number) { }

    @Component
    public class SomeService {

        @Validate
        public int validate(@Valid Foo argument) {
            return 1;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Valid
    data class Foo(@field:NotEmpty val number: String)

    @Component
    open class SomeService {

        @Validate
        open fun validate(@Valid argument: Foo): Int {
            return 1
        }
    }
    ```

In the example above, `Validator<Foo>` will be created for `Foo`.
When the method is called, the `@Validate` aspect will call this validator for the `argument` argument.

### Result Validation { #result-validation }

To validate a method result, use the `@Validate` annotation on the method and annotate the result with the corresponding [annotations](#validation-annotations).
Place `@Valid` on the method to run nested validation through the return type's `Validator`.
To require that the result is not `null`, use any `@Nonnull` or `@NotNull` annotation.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class ResultValidator {

        @Valid
        public record User(@NotBlank String id,
                           @Size(min = 3, max = 6) String name,
                           @Nullable @Size(min = 1, max = 10) String status) { } //(1)!

        @Valid //(3)!
        @Validate //(2)!
        public User create(String name, String status) {
            return new User(UUID.randomUUID().toString(), name, status);
        }
    }
    ```

    1. Constraints can be stacked: `status` is optional (`@Nullable`), but when present its length must be within `@Size`.
    2. Indicates that the method requires validation.
    3. Indicates that the result should be validated through the `Validator` of the return type.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    open class ResultValidator {

        @Valid
        data class User(@field:NotBlank val id: String,
                        @field:Size(min = 3, max = 6) val name: String,
                        @field:Size(min = 1, max = 10) val status: String?) //(1)!

        @Valid //(3)!
        @Validate //(2)!
        open fun create(name: String, status: String?): User {
            return User(UUID.randomUUID().toString(), name, status)
        }
    }
    ```

    1. Constraints can be stacked: `status` is optional (nullable), but when present its length must be within `@Size`.
    2. Indicates that the method requires validation.
    3. Indicates that the result should be validated through the `Validator` of the return type.

The result validation runs **after** the method body, on its return value; if it fails, the aspect throws `ViolationException` instead of returning the value.

Constraints can also be applied to the result container itself. For example, a collection result can be size-checked and its elements validated at the same time:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Valid
    public record Foo(@Valid Bar bar) { }

    @Component
    public class SomeService {

        @Size(min = 1, max = 3) //(3)!
        @Valid //(2)!
        @Validate //(1)!
        public List<Foo> validate() {
            // do something
        }
    }
    ```

    1. Indicates that the method requires validation.
    2. Indicates that the result should be validated through the `Validator` of the return type.
    3. Standard validation annotation.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    open class SomeService {

        @Size(min = 1, max = 3) //(3)!
        @Valid //(2)!
        @Validate //(1)!
        open fun validate(): List<Foo> {
            // do something
        }
    }
    ```

    1. Indicates that the method requires validation.
    2. Indicates that the result should be validated through the `Validator` of the return type.
    3. Standard validation annotation.

A method that returns nothing can still validate its arguments, but result validation on a `void` / `Unit` return is a build error — there is no value to check.

### Validation Options { #validation-options-2 }

There are two validation modes:

- `Full` - all marked arguments and the result are checked, all possible validation errors are collected, and only then an exception is thrown. This is the default behavior.
- `FailFast` - an exception is thrown on the first found error.

Example of `FailFast` validation:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @Validate(failFast = true)
        public int validate(@NotEmpty String c2) {
            return 1;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    open class SomeService {

        @Validate(failFast = true)
        open fun validate(@NotEmpty c2: String): Int = 1
    }
    ```

Arguments and the result are two separate stages: with the default `Full` mode all argument violations are collected and thrown together, and the result is checked only if the arguments passed.

## Validation HTTP Response { #validation-response-http }

When a Kora `HTTP` service uses the `ValidationModule` (from the `validation-module` artifact), a failed validation can be turned into an `HTTP` `400` response automatically instead of an uncaught error.

This is handled by the `ValidationHttpServerInterceptor` — an [HTTP server interceptor](http-server.md#interceptors) that catches the `ViolationException` thrown by the `@Validate` aspect and produces the response.
By default it returns status `400` with the `ViolationException` [message](#manual-validation) as a `text/plain` body; a custom [response mapper](#validation-response-custom) can replace that.

`ValidationModule` contributes the interceptor **untagged**, while the `HTTP` server collects global interceptors under the `@Tag(HttpServer.class)` tag (see [Interceptors](http-server.md#interceptors)).
Override the module method and add that tag to apply the interceptor to every route:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends
            ValidationModule, //(1)!
            UndertowPublicHttpServerModule,
            JsonModule {

        @Tag(HttpServer.class) //(2)!
        default ValidationHttpServerInterceptor validationHttpServerInterceptor(@Nullable ViolationExceptionHttpServerResponseMapper mapper) {
            return new ValidationHttpServerInterceptor(mapper); //(3)!
        }
    }
    ```

    1. `ValidationModule` extends `ValidatorModule` and declares the `ValidationHttpServerInterceptor` default.
    2. Registers the interceptor as a **global** HTTP server interceptor; `HttpServer` is `io.koraframework.http.server.common.HttpServer`.
    3. A `null` mapper keeps the default `400` plain-text response.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : ValidationModule, //(1)!
        UndertowPublicHttpServerModule,
        JsonModule {

        @Tag(HttpServer::class) //(2)!
        override fun validationHttpServerInterceptor(mapper: ViolationExceptionHttpServerResponseMapper?): ValidationHttpServerInterceptor {
            return ValidationHttpServerInterceptor(mapper) //(3)!
        }
    }
    ```

    1. `ValidationModule` extends `ValidatorModule` and declares the `ValidationHttpServerInterceptor` default.
    2. Registers the interceptor as a **global** HTTP server interceptor; `HttpServer` is `io.koraframework.http.server.common.HttpServer`.
    3. The parameter is declared `@Nullable` in the Kora contract, so the `Kotlin` override must accept `ViolationExceptionHttpServerResponseMapper?`; a `null` mapper keeps the default `400` plain-text response.

A `@Validate`-annotated controller method then produces a `400` for the client whenever its arguments or result fail validation, with no per-controller wiring:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
    @Valid
    public record UserRequest(@NotBlank @Size(min = 2, max = 100) String name,
                              @NotBlank @Pattern("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$") String email) { }

    @Component
    @HttpController
    public final class UserController {

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Validate //(1)!
        @Json
        public UserResponse createUser(@Valid @Json UserRequest request) { //(2)!
            // request is already validated here
        }

        @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}")
        @Validate
        @Json
        public UserResponse getUser(@Path @NotBlank @Pattern("^\\d+$") String userId) { //(3)!
            // userId is already validated here
        }
    }
    ```

    1. Enables argument (and result) validation for this route.
    2. Nested validation of the request body; a violation yields `HTTP` `400` before the body runs.
    3. Constraints work on any bound parameter — `@Path`, `@Query`, `@Header`, `@Cookie` — not only on the `JSON` body.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    @Valid
    data class UserRequest(@field:NotBlank @field:Size(min = 2, max = 100) val name: String,
                           @field:NotBlank @field:Pattern("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$") val email: String)

    @Component
    @HttpController
    open class UserController {

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Validate //(1)!
        @Json
        open fun createUser(@Valid @Json request: UserRequest): UserResponse { //(2)!
            // request is already validated here
        }

        @HttpRoute(method = HttpMethod.GET, path = "/users/{userId}")
        @Validate
        @Json
        open fun getUser(@Path @NotBlank @Pattern("^\\d+$") userId: String): UserResponse { //(3)!
            // userId is already validated here
        }
    }
    ```

    1. Enables argument (and result) validation for this route.
    2. Nested validation of the request body; a violation yields `HTTP` `400` before the body runs.
    3. Constraints work on any bound parameter — `@Path`, `@Query`, `@Header`, `@Cookie` — not only on the `JSON` body.

### Custom Response { #validation-response-custom }

To control the status, headers, or body of the response — for example, to return a structured `JSON` error instead of the default plain text — provide a `ViolationExceptionHttpServerResponseMapper` component.
Its `apply(request, exception)` method returns the `HttpServerResponse` to send; returning `null` falls back to the default `400` plain-text response.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json //(1)!
    public record ValidationErrorResponse(String code, String message, List<ValidationErrorDetails> errors) { }

    @Json
    public record ValidationErrorDetails(String field, String message) { }

    @KoraApp
    public interface Application extends
            ValidationModule,
            UndertowPublicHttpServerModule,
            JsonModule {

        default ViolationExceptionHttpServerResponseMapper violationExceptionMapper(JsonWriter<ValidationErrorResponse> writer) {
            return (request, exception) -> {
                var errors = exception.getViolations().stream() //(2)!
                        .map(v -> new ValidationErrorDetails(v.path().full(), v.message()))
                        .toList();
                var body = new ValidationErrorResponse("VALIDATION_ERROR", "Validation failed", errors);
                return HttpServerResponse.of(400, HttpBody.json(writer.toByteArray(body))); //(3)!
            };
        }

        @Tag(HttpServer.class)
        default ValidationHttpServerInterceptor validationHttpServerInterceptor(ViolationExceptionHttpServerResponseMapper mapper) {
            return new ValidationHttpServerInterceptor(mapper);
        }
    }
    ```

    1. Serialized with the [JSON module](json.md).
    2. `ViolationException.getViolations()` returns every `Violation`; `path().full()` is the dotted path (e.g. `customer.address.city`).
    3. Any `HttpServerResponse` may be returned; returning `null` would fall back to the default `400`.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json //(1)!
    data class ValidationErrorResponse(val code: String, val message: String, val errors: List<ValidationErrorDetails>)

    @Json
    data class ValidationErrorDetails(val field: String, val message: String)

    @KoraApp
    interface Application : ValidationModule,
        UndertowPublicHttpServerModule,
        JsonModule {

        fun violationExceptionMapper(writer: JsonWriter<ValidationErrorResponse>): ViolationExceptionHttpServerResponseMapper {
            return ViolationExceptionHttpServerResponseMapper { _, exception ->
                val errors = exception.violations.map { //(2)!
                    ValidationErrorDetails(it.path().full(), it.message())
                }
                val body = ValidationErrorResponse("VALIDATION_ERROR", "Validation failed", errors)
                HttpServerResponse.of(400, HttpBody.json(writer.toByteArray(body))) //(3)!
            }
        }

        @Tag(HttpServer::class)
        override fun validationHttpServerInterceptor(mapper: ViolationExceptionHttpServerResponseMapper?): ValidationHttpServerInterceptor {
            return ValidationHttpServerInterceptor(mapper)
        }
    }
    ```

    1. Serialized with the [JSON module](json.md).
    2. `ViolationException.getViolations()` returns every `Violation`; `path().full()` is the dotted path (e.g. `customer.address.city`).
    3. Any `HttpServerResponse` may be returned; returning `null` would fall back to the default `400`.

## Custom Validation Annotations { #custom-validation-annotations }

A custom validation annotation is needed when the standard checks are not enough.
It connects an annotation with a `ValidatorFactory`, and the factory creates a `Validator` for a specific value type.

To create a custom annotation:

1. Create a `Validator` implementation:

===! ":fontawesome-brands-java: `Java`"

    ```java
    final class MyValidStringValidator implements Validator<String> {

        @Override
        public List<Violation> validate(@Nullable String value, ValidationContext context) {
            if (value == null) {
                return List.of(context.violates("Should be not empty, but was null"));
            } else if (value.isEmpty()) {
                return List.of(context.violates("Should be not empty, but was empty"));
            }

            return Collections.emptyList();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class MyValidStringValidator : Validator<String?> {

        override fun validate(value: String?, context: ValidationContext): List<Violation> {
            if (value == null) {
                return listOf(context.violates("Should be not empty, but was null"))
            } else if (value.isEmpty()) {
                return listOf(context.violates("Should be not empty, but was empty"))
            }
            return listOf()
        }
    }
    ```

2. Create a `ValidatorFactory` subtype:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface MyValidValidatorFactory extends ValidatorFactory<String> { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface MyValidValidatorFactory : ValidatorFactory<String?>
    ```

3. Register the `ValidatorFactory` as a component:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {

        default MyValidValidatorFactory myValidStringConstraintFactory() {
            return MyValidStringValidator::new;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application {

        fun myValidStringConstraintFactory(): MyValidValidatorFactory {
            return object : MyValidValidatorFactory {
                override fun create(): Validator<String?> {
                    return MyValidStringValidator()
                }
            }
        }
    }
    ```

4. Create a validation annotation and mark it with `@ValidatedBy` using the previously created `ValidatorFactory` subtype:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Retention(value = RetentionPolicy.CLASS)
    @Target(value = {ElementType.METHOD, ElementType.FIELD, ElementType.PARAMETER})
    @ValidatedBy(MyValidValidatorFactory.class)
    public @interface MyValid { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Retention(AnnotationRetention.RUNTIME)
    @Target(AnnotationTarget.FUNCTION, AnnotationTarget.FIELD, AnnotationTarget.PROPERTY, AnnotationTarget.VALUE_PARAMETER)
    @ValidatedBy(MyValidValidatorFactory::class)
    annotation class MyValid
    ```

5. Mark a field, argument, or result with the new annotation:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Valid
    public record Foo(@MyValid String number) { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Valid
    data class Foo(@field:MyValid val number: String)
    ```

!!! note

    The `ValidatorFactory` is looked up in the dependency graph by the factory **subtype** you declared, parameterized with the annotated value type — `MyValidValidatorFactory<String>` for a `String` field.
    Register one factory component per value type the constraint should support; that is exactly how the built-in constraints cover `String` and `CharSequence` separately.

### Parameterized Constraints { #parameterized-constraints }

A custom constraint annotation may declare parameters.
When it does, its `ValidatorFactory` subtype must declare a `create(...)` method whose parameter list matches the annotation attributes (the **same number of parameters, in declaration order**).
Kora reads the annotation values (with defaults applied) at compile time and passes them into that `create(...)` method; if no matching `create(...)` overload exists, the build fails with `Expected <Factory>#create() method with N parameters, but was didn't find such`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Retention(RetentionPolicy.CLASS)
    @Target({ElementType.FIELD, ElementType.PARAMETER})
    @ValidatedBy(PrefixedValidatorFactory.class)
    public @interface Prefixed {

        String value(); //(1)!
    }

    public interface PrefixedValidatorFactory extends ValidatorFactory<String> {

        @Override
        default Validator<String> create() { //(2)!
            throw new UnsupportedOperationException("Prefix is required");
        }

        Validator<String> create(String prefix); //(3)!
    }
    ```

    1. A single annotation attribute.
    2. The inherited no-argument factory method is not usable for this constraint.
    3. Matching single-parameter `create(...)`; Kora passes `value()` into `prefix`.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Retention(AnnotationRetention.RUNTIME)
    @Target(AnnotationTarget.FIELD, AnnotationTarget.PROPERTY, AnnotationTarget.VALUE_PARAMETER)
    @ValidatedBy(PrefixedValidatorFactory::class)
    annotation class Prefixed(val value: String) //(1)!

    interface PrefixedValidatorFactory : ValidatorFactory<String> {

        override fun create(): Validator<String> = //(2)!
            throw UnsupportedOperationException("Prefix is required")

        fun create(prefix: String): Validator<String> //(3)!
    }
    ```

    1. A single annotation attribute.
    2. The inherited no-argument factory method is not usable for this constraint.
    3. Matching single-parameter `create(...)`; Kora passes `value` into `prefix`.

The factory is registered as a component exactly like the parameterless case (step 3 above).
This is the same mechanism the built-in constraints use, and their public factory interfaces expose reusable overloads that a custom factory can delegate to:

| Factory | Overloads |
|---------|-----------|
| `RangeValidatorFactory` | `create(double from, double to)`, `create(double from, double to, Range.Boundary boundary)` |
| `SizeValidatorFactory` | `create(int to)`, `create(int from, int to)` |
| `PatternValidatorFactory` | `create(String pattern)`, `create(String pattern, int flags)` — the inherited `create()` throws, a pattern is mandatory |
| `MinValidatorFactory` / `MaxValidatorFactory` | `create(long value)` |
| `DigitsValidatorFactory` | `create(int integer, int fraction)` |
| `OneOfValidatorFactory` | `create(String[] value)` |
| `NotEmptyValidatorFactory`, `NotBlankValidatorFactory`, `UuidValidatorFactory`, `UriValidatorFactory`, `UrlValidatorFactory`, `AssertTrueValidatorFactory`, `AssertFalseValidatorFactory`, `PositiveValidatorFactory`, `PositiveOrZeroValidatorFactory`, `NegativeValidatorFactory`, `NegativeOrZeroValidatorFactory`, `PastValidatorFactory`, `PastOrPresentValidatorFactory`, `FutureValidatorFactory`, `FutureOrPresentValidatorFactory` | the parameterless `create()` |

Because these are ordinary graph components declared with `@DefaultComponent`, providing your own factory for the same type replaces the built-in behaviour of that constraint.

## Signatures { #signatures }

Method signatures supported by the `@Validate` aspect out of the box:

===! ":fontawesome-brands-java: `Java`"

    The class must not be `final` for aspects to work.

    `T` means the return value type.

    - `T myMethod()`
    - `void myMethod()` (arguments only — a result constraint on `void` is a build error)
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/CompletionStage.html)
    - `CompletableFuture<T> myMethod()`

    `Publisher`, `Mono`, `Flux`, and a bare `Future<T>` are **not** supported and fail the build with an explicit message.

=== ":simple-kotlin: `Kotlin`"

    The class must be `open` for aspects to work.

    `T` means the return value type, `T?`, or `Unit`.

    - `myMethod(): T`
    - `myMethod(): Unit` (arguments only — a result constraint on `Unit` is a build error)
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (requires [dependency](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) as `implementation`)
    - `myMethod(): Flow<T>` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (requires [dependency](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) as `implementation`)

    For a `Flow<T>`, arguments are validated when the flow is collected and the result constraints are applied to each emitted element.
    `CompletionStage`, `Future`, `Mono`, and `Flux` are **not** supported and fail the build with an explicit message.
