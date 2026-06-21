---
description: "Explains Kora validation annotations, class and method validation, argument and result validation, custom validators, and supported validation signatures. Use when working with @Validate, @Valid, @NotNull, @NotEmpty, @Pattern, @Range, @Size, @Validator."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora validation annotations, class and method validation, argument and result validation, custom validators, and supported validation signatures; key triggers include @Validate, @Valid, @NotNull, @NotEmpty, @Pattern, @Range, @Size, @Validator, ValidationModule."
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

## Validation Annotations { #validation-annotations }

Validation annotations are used by Kora to check field values, method arguments, and method results.
Annotations can be applied directly or through nested `@Valid` validation if the type has a generated or manually provided `Validator`.

Available validation annotations:

- `@Valid` - marks a class for `Validator<T>` generation or marks a field, argument, or method result for nested validation through a `Validator` of the corresponding type.
- `@Validate` - marks a method whose arguments and/or result should be validated; the `failFast` parameter controls stopping on the first error (default: `false`).
- `@ValidatedBy` - connects a custom validation annotation with a `ValidatorFactory`.
- `@NotNull` / `@Nonnull` - checks that the value is not `null`; any compatible annotation from `javax.annotation`, `jakarta.annotation`, or other common packages can be used.
- `@NotEmpty` - checks that the value is not `null` and is not empty; supports `CharSequence`, `String`, `Iterable`, `Collection`, `List`, `Set`, and `Map`.
- `@NotBlank` - checks that the string is not `null` and contains at least one non-whitespace character; supports `CharSequence` and `String`.
- `@Pattern` - checks that `String` or `CharSequence` matches a regular expression; the `value` parameter sets the expression (`required`, no default), and the `flags` parameter sets `java.util.regex.Pattern` flags (default: `0`).
- `@Range` - checks that a number is within the specified range; the `from` parameter sets the lower bound (`required`, no default), the `to` parameter sets the upper bound (`required`, no default), and the `boundary` parameter controls bound inclusion (default: `INCLUSIVE_INCLUSIVE`).
- `@Size` - checks the size of `List`, `Collection`, `Map`, `String`, or `CharSequence`; the `min` parameter sets the minimum size (default: `0`), and the `max` parameter sets the maximum size (`required`, no default).

## Class Validation { #class-validation }

The `@Valid` annotation on a class or `record` tells Kora to create a `Validator<T>` for that type.
The generated validator becomes a regular dependency graph component and can be injected by the `Validator<Type>` signature.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Valid
    public record Foo(String number) { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Valid
    data class Foo(val number: String)
    ```

A validator for this class will then be available in the dependency container:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class Example {

        private final Validator<Foo> fooValidator;

        public Example(Validator<Foo> fooValidator) {
            this.fooValidator = fooValidator;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class Example(val fooValidator: Validator<Foo>)
    ```

Generated validators can be injected as dependencies into any component.
In the example above, the validator for `Foo` is injected by the `Validator<Foo>` signature and can be used manually.

The `validate(...)` method returns a list of `Violation`.
You can process this list yourself or call `validateAndThrow(...)`, which throws `ViolationException` if there are violations.

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

There are two validation modes:

- `Full` - all marked fields are checked, all possible validation errors are collected, and only then a list of violations is returned or an exception is thrown. This is the default behavior.
- `FailFast` - validation stops on the first found error.

Example of `FailFast` validation:
```java
ValidationContext context = ValidationContext.builder().failFast(true).build();
List<Violation> violations = fooValidator.validate(value, context);
```

## Method Validation { #method-validation }

Method argument and result validation uses the `@Validate` aspect and the set of [annotations](#validation-annotations) provided by the module.
Kora generates aspect code at compile time, so a class with such methods must support aspect application.

### Argument Validation { #argument-validation }

To validate method arguments, use the `@Validate` annotation on the method:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @Validate
        public int validate(@NotEmpty String argument) {
            return 1;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    open class SomeService {

        @Validate
        fun validate(@NotEmpty argument: String): Int {
            return 1
        }
    }
    ```

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
To check that the result is not `null`, use any `@NotNull` or `@Nonnull` annotation.

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
    class SomeService {

        @Validate(failFast = true)
        fun validate(@NotEmpty c2: String): Int = 1
    }
    ```

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
