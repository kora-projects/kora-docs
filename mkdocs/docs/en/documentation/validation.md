---
description: "Explains Kora validation annotations, class and method validation, argument and result validation, custom validators, mapping validation failures to HTTP 400, and supported validation signatures. Use when working with @Validate, @Valid, @NotBlank, @NotEmpty, @Pattern, @Range, @Size, @Validator, ValidatorModule, ValidationModule."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora validation annotations, class and method validation, argument and result validation, custom validators, mapping ViolationException to HTTP 400, and supported validation signatures; key triggers include @Validate, @Valid, @NotBlank, @NotEmpty, @Pattern, @Range, @Size, @ValidatedBy, Validator, ValidatorFactory, ViolationException, ValidationHttpServerInterceptor, ValidatorModule, ValidationModule."
---

The Kora validation module checks models, method arguments, and method results using annotations.
For models, Kora generates a `Validator<T>` at compile time, and for methods it applies the `@Validate` aspect that calls the required checks before or after method execution.

Validation works without using `Reflection` at application runtime: object structure, nested fields, method signatures, and available validators are checked by annotation processors during the build.
Validation errors are returned as a list of `Violation` or thrown as `ViolationException`.

For a step-by-step walkthrough before the reference details, see [Validation](../guides/validation.md).

## Dependency { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:validation-module"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends ValidationModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```kotlin
    implementation("ru.tinkoff.kora:validation-module")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : ValidationModule
    ```

The module ships two mixin interfaces, and you pick one depending on whether the application serves `HTTP`:

| Module | Artifact | Provides | Use when |
|--------|----------|----------|----------|
| `ValidatorModule` | `validation-common` | Generated `Validator<T>` beans, all built-in constraint factories, and element validators (`Validator<List<T>>`, `Validator<Set<T>>`, `Validator<Collection<T>>`) | Libraries and non-`HTTP` applications, or when you handle `ViolationException` yourself |
| `ValidationModule` | `validation-module` | Everything from `ValidatorModule` **plus** the `ValidationHttpServerInterceptor` that maps `ViolationException` to an [HTTP 400 response](#validation-response-http-400) | `HTTP` services that should return `400` to clients automatically |

`ValidationModule` extends `ValidatorModule`, so wiring `ValidationModule` also gives you everything the base module provides.
The dependency shown above (`validation-module`) is the right choice for an `HTTP` service; a library that only needs to generate validators can depend on `validation-common` and wire `ValidatorModule` instead.

## Validation Annotations { #validation-annotations }

Validation annotations tell Kora what to check on a field, method argument, or method result.
They can be applied directly, or nested validation can be triggered through `@Valid` when the type has a generated or manually provided `Validator`.

!!! warning "Kora validation is not Jakarta Bean Validation"

    Kora validation is **not** [Jakarta Bean Validation (JSR-380)](https://jakarta.ee/specifications/bean-validation/).
    All Kora constraint annotations live in the `ru.tinkoff.kora.validation.common.annotation` package and are processed at compile time.
    In particular, Kora ships **no** `@NotNull` constraint annotation: a value is required by default, and to make it optional you mark it with any `@Nullable` annotation (see [Optional Fields](#optional-fields)).
    Kora does recognize a standard `@Nonnull` / `@NotNull` marker (from `javax.annotation`, `jakarta.annotation`, and similar packages) as an explicit not-`null` requirement, which matters mainly for [`JsonNullable`](#json-nullable) fields.

The structural annotations that drive validation:

- `@Valid` - on a class or `record` generates a `Validator<T>` for that type; on a field, argument, or method result triggers nested validation through the `Validator` of the corresponding type. Applicable to types, fields, parameters, and methods.
- `@Validate` - marks a method whose arguments and/or result should be validated by the aspect; the `failFast` parameter controls stopping on the first error (default: `false`). Applicable to methods only.
- `@ValidatedBy` - links a custom constraint annotation with a `ValidatorFactory` that builds its `Validator` (see [Custom Validation Annotations](#custom-validation-annotations)). Applicable to annotation types only.

The built-in constraint annotations and their parameters:

| Annotation | Supported types | Parameters (defaults) | Description |
|------------|-----------------|-----------------------|-------------|
| `@NotBlank` | `String`, `CharSequence` | — | Value is not `null` and contains at least one non-whitespace character. |
| `@NotEmpty` | `String`, `CharSequence`, `Iterable`, `Collection`, `List`, `Set`, `Map` | — | Value is not `null` and not empty. |
| `@Pattern` | `String`, `CharSequence` | `value` (required, no default), `flags` (default: `0`) | Value matches the `value` regular expression; `flags` maps to [`java.util.regex.Pattern`](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/regex/Pattern.html#field.summary) flags. |
| `@Range` | `Short`, `Integer`, `Long`, `Float`, `Double`, `BigInteger`, `BigDecimal` | `from` (required, no default), `to` (required, no default), `boundary` (default: `INCLUSIVE_INCLUSIVE`) | Number lies within `[from, to]`; `boundary` controls whether the bounds are inclusive. |
| `@Size` | `String`, `CharSequence`, `Collection`, `List`, `Set`, `Map` | `min` (default: `0`), `max` (required, no default) | Size (length) of the value is within `min` and `max`. |

!!! note

    Watch the required parameters: `@Size.max` has **no default**, so omitting it is a compile error; `@Range.from` and `@Range.to` are both required and are declared as `double`.
    The `@Range.boundary` value is a `Range.Boundary` enum with the variants `EXCLUSIVE_EXCLUSIVE`, `INCLUSIVE_EXCLUSIVE`, `EXCLUSIVE_INCLUSIVE`, and `INCLUSIVE_INCLUSIVE`.

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

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Valid
    data class Foo(@field:NotEmpty val number: String)
    ```

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

    1. Any `@Nullable` annotation is suitable, for example `javax.annotation.Nullable`, `jakarta.annotation.Nullable`, or `org.jetbrains.annotations.Nullable`.

=== ":simple-kotlin: `Kotlin`"

    To mark a field as optional, use [`Kotlin Nullability`](https://kotlinlang.org/docs/null-safety.html) syntax and add `?` to the field type.
    For such a field, a `null` check **will not** be created:

    ```kotlin
    @Valid
    data class Foo(val number: String?)
    ```

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
When `Validator<Foo>` is called, it will call `Validator<Bar>` internally.

#### Collection Validation { #collection-validation }

`@Valid` on a `List`, `Set`, or `Collection` field validates **every element** through the element's `Validator`.
The `ValidatorModule` provides these element validators out of the box (`Validator<List<T>>`, `Validator<Set<T>>`, `Validator<Collection<T>>`), so no extra wiring is needed.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Valid
    public record Foo(@Valid List<Bar> bars) { }

    @Valid
    public record Bar(@NotBlank String number) { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Valid
    data class Foo(@field:Valid val bars: List<Bar>)

    @Valid
    data class Bar(@field:NotBlank val number: String)
    ```

Each `Bar` in the list is validated, and the violation path is indexed by element position, for example `bars[0].number`.
Constraints such as [`@Size`](#validation-annotations) can be combined with `@Valid` on the same collection to check both the collection size and each element.

#### `Sealed` Hierarchies { #sealed-validation }

Kora can create a `Validator` for `sealed` hierarchies.
If `@Valid` is placed on a `sealed` type, the generated validator determines the actual subtype and calls the validator for the matching final implementation.

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

#### `JsonNullable` { #json-nullable }

For `JsonNullable<T>`, Kora validates the `T` value inside the container.
If `JsonNullable` is in the `undefined` state, regular value checks are not performed.
Use `@NotNull` or `@Nonnull` to disallow `undefined` or `null`.

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
                Violation first = violations.get(0);
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

- `validate(value)` / `validate(value, context)` - return a `List<Violation>` that is empty when the value is valid (a `null` value fails with a violation).
- `validateAndThrow(value)` / `validateAndThrow(value, context)` - throw `ViolationException` when any violation occurs, and do nothing otherwise.

When a `ViolationException` is caught, `getViolations()` returns the aggregated `List<Violation>`, and `getMessage()` returns a preformatted multi-line summary of every violation path and message.

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
        fun calculate(@Valid user: User, //(1)!
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

#### Required Arguments { #required-arguments }

All arguments are considered required by default, so `null` checks are created for them.

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

    1. Any `@Nullable` annotation is suitable, for example `javax.annotation.Nullable`, `jakarta.annotation.Nullable`, or `org.jetbrains.annotations.Nullable`.

=== ":simple-kotlin: `Kotlin`"

    To mark an argument as optional, use [`Kotlin Nullability`](https://kotlinlang.org/docs/null-safety.html) syntax and add `?` to the argument type.
    For such an argument, a `null` check **will not** be created:

    ```kotlin
    @Component
    open class SomeService {

        @Validate
        fun validate(argument: String?): Int {
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
        fun validate(@Valid argument: Foo): Int {
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
        fun create(name: String, status: String): User {
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
        fun validate(): List<Foo> {
            // do something
        }
    }
    ```

    1. Indicates that the method requires validation.
    2. Indicates that the result should be validated through the `Validator` of the return type.
    3. Standard validation annotation.

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
        fun validate(@NotEmpty c2: String): Int = 1
    }
    ```

## Validation Response (HTTP 400) { #validation-response-http-400 }

When a Kora `HTTP` service uses the `ValidationModule` (from the `validation-module` artifact), a failed validation can be turned into an `HTTP` `400` response automatically instead of an uncaught error.

This is handled by the `ValidationHttpServerInterceptor` — an [HTTP server interceptor](http-server.md#interceptors) that catches `ViolationException` thrown by the `@Validate` aspect (including an exception wrapped in `CompletionException` for asynchronous signatures) and produces the response.
By default it returns status `400` with the `ViolationException` [message](#manual-validation) as a plain-text body; a custom [response mapper](#validation-response-custom) can replace that.

Global interceptors are collected by the `@Tag(HttpServerModule.class)` tag (see [Interceptors](http-server.md#interceptors)), so the interceptor must be provided **with that tag** to apply to every route:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends
            ValidationModule, //(1)!
            UndertowHttpServerModule,
            JsonModule {

        @Tag(HttpServerModule.class) //(2)!
        default ValidationHttpServerInterceptor validationHttpServerInterceptor(@Nullable ViolationExceptionHttpServerResponseMapper mapper) {
            return new ValidationHttpServerInterceptor(mapper); //(3)!
        }
    }
    ```

    1. `ValidationModule` extends `ValidatorModule` and provides the `ValidationHttpServerInterceptor` and `ViolationExceptionHttpServerResponseMapper` wiring.
    2. Registers the interceptor as a **global** HTTP server interceptor.
    3. Passing `null` as the mapper keeps the default `400` plain-text response.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : ValidationModule, //(1)!
        UndertowHttpServerModule,
        JsonModule {

        @Tag(HttpServerModule::class) //(2)!
        fun validationInterceptor(mapper: ViolationExceptionHttpServerResponseMapper?): ValidationHttpServerInterceptor {
            return ValidationHttpServerInterceptor(mapper) //(3)!
        }
    }
    ```

    1. `ValidationModule` extends `ValidatorModule` and provides the `ValidationHttpServerInterceptor` and `ViolationExceptionHttpServerResponseMapper` wiring.
    2. Registers the interceptor as a **global** HTTP server interceptor.
    3. Passing `null` as the mapper keeps the default `400` plain-text response.

A `@Validate`-annotated controller method then produces a `400` for the client whenever its arguments or result fail validation, with no per-controller wiring:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
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
    }
    ```

    1. Enables argument (and result) validation for this route.
    2. Nested validation of the request body; a violation yields `HTTP` `400` before the body runs.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    data class UserRequest(@field:NotBlank @field:Size(min = 2, max = 100) val name: String,
                           @field:NotBlank @field:Pattern("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$") val email: String)

    @Component
    @HttpController
    class UserController {

        @HttpRoute(method = HttpMethod.POST, path = "/users")
        @Validate //(1)!
        @Json
        fun createUser(@Valid @Json request: UserRequest): UserResponse {
            // request is already validated here
        }
    }
    ```

    1. Enables argument (and result) validation for this route.
    2. Nested validation of the request body; a violation yields `HTTP` `400` before the body runs.

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
            UndertowHttpServerModule,
            JsonModule {

        default ViolationExceptionHttpServerResponseMapper violationExceptionMapper(JsonWriter<ValidationErrorResponse> writer) {
            return (request, exception) -> {
                var errors = exception.getViolations().stream() //(2)!
                        .map(v -> new ValidationErrorDetails(v.path().full(), v.message()))
                        .toList();
                var body = new ValidationErrorResponse("VALIDATION_ERROR", "Validation failed", errors);
                return HttpServerResponse.of(400, HttpBody.json(writer.toByteArrayUnchecked(body))); //(3)!
            };
        }

        @Tag(HttpServerModule.class)
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
        UndertowHttpServerModule,
        JsonModule {

        fun violationExceptionMapper(writer: JsonWriter<ValidationErrorResponse>): ViolationExceptionHttpServerResponseMapper {
            return ViolationExceptionHttpServerResponseMapper { request, exception ->
                val errors = exception.violations.map { //(2)!
                    ValidationErrorDetails(it.path().full(), it.message())
                }
                val body = ValidationErrorResponse("VALIDATION_ERROR", "Validation failed", errors)
                HttpServerResponse.of(400, HttpBody.json(writer.toByteArrayUnchecked(body))) //(3)!
            }
        }

        @Tag(HttpServerModule::class)
        fun validationInterceptor(mapper: ViolationExceptionHttpServerResponseMapper): ValidationHttpServerInterceptor {
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

        @Nonnull
        @Override
        public List<Violation> validate(String value, @Nonnull ValidationContext context) {
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
    @Target(allowedTargets = [AnnotationTarget.FUNCTION, AnnotationTarget.FIELD, AnnotationTarget.PROPERTY])
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

### Parameterized Constraints { #parameterized-constraints }

A custom constraint annotation may declare parameters.
When it does, its `ValidatorFactory` subtype must declare a `create(...)` method whose parameter list matches the annotation attributes (the **same number of parameters, in declaration order**).
Kora reads the annotation values (with defaults applied) at compile time and passes them into that `create(...)` method; if no matching `create(...)` overload exists, the build fails.

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

- `RangeValidatorFactory` - `create(double from, double to)` and `create(double from, double to, Range.Boundary boundary)`.
- `SizeValidatorFactory` - `create(int to)` and `create(int from, int to)`.
- `PatternValidatorFactory` - `create(String pattern)` and `create(String pattern, int flags)`.
- `NotEmptyValidatorFactory` and `NotBlankValidatorFactory` - the parameterless `create()`.

## Signatures { #signatures }

Method signatures supported by the `@Validate` aspect out of the box:

===! ":fontawesome-brands-java: `Java`"

    The class must not be `final` for aspects to work.

    `T` means the return value type.

    - `T myMethod()`
    - `Optional<T> myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletionStage.html)
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (requires [dependency](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))
    - `Flux<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (requires [dependency](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

=== ":simple-kotlin: `Kotlin`"

    The class must be `open` for aspects to work.

    `T` means the return value type, `T?`, or `Unit`.

    - `myMethod(): T`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (requires [dependency](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) as `implementation`)
    - `myMethod(): Flow<T>` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (requires [dependency](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) as `implementation`)
