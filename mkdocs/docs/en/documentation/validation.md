Module for validating classes/records and methods using annotations.

## Dependency

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
    ```groovy
    implementation("ru.tinkoff.kora:validation-module")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : ValidationModule
    ```

## Validation annotations

Special validation annotations are used by Kora to validate fields/arguments, they represent simple checks.

Available validation annotations:

- `@NotEmpty` - Checks that the string is not empty
- `@NotBlank` - Checks that the string does not consist of empty characters
- `@Pattern` - Checks if the string matches Regular Expression (RegEx)
- `@Range` - Checks that the number is in the specified range
- `@Size` - Checks that a collection (List, Set, Map) or `String` has a size in the specified range.

## Class validation

It is suggested to use the `@Valid` annotation to mark a class that needs a validator from the Kora framework.

An example of a labeled class for validation looks like this:

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

A validator of that class will then be available in the dependency container:

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

Created validators can be implemented as dependencies in any component, in the examples above the validator for the `Foo` class,
can be implemented by its signature `Validator<Foo>` as a component dependency and used manually for validation.

The validator returns a list of violations after validation, they can be used to manually compose the error either
you can use the `validateAndThrow` method which throws a `ViolationException` exception in case of a validation error.

### Field validation

It is expected to use a special provided validation [annotation](#annotation-validation) validation set for field validation.

An example of an object marked up for validation looks like this:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Valid
    public record Foo(@NotEmpty String number) { }
    ```

    For Record classes, the syntax for accessing fields via Record-like getter contracts is used, 
    in the case of `Foo` and the `code` field, *getter* `code()` will be used in the created `Validator`.

    For a regular class it is expected that Java *Getters* syntax will be used, for example for the `id` field *getter* `getId()` will be used,
    where *getter* should have at least *package-private* visibility.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Valid
    Data class Foo(@field:NotEmpty val number: String)
    ```

#### Required fields

All fields are required (`NotNull`) by default, so `NotNull` checks will be created for all of them in the `Validator`.

#### Optional fields

===! ":fontawesome-brands-java: `Java`"

    In order to specify a field as not required, you need to mark it with any `@Nullable` annotation,
    **will not** create a *null* check for such a field:

    ```java
    @Valid
    public record Foo(@Nullable String number) { } //(1)!
    ```

    1. Any `@Nullable` annotation will do, such as `javax.annotation.Nullable` / `jakarta.annotation.Nullable` / `org.jetbrains.annotations.Nullable` / etc.

=== ":simple-kotlin: `Kotlin`"

    It is expected to use the [Kotlin Nullability](https://kotlinlang.org/docs/null-safety.html) syntax and mark such a field as Nullable:

    ```kotlin
    @Valid
    data class Foo(val number: String?)
    ```

#### Embedded fields

In order to validate fields of complex objects for which validators are created (or provided independently),
or fields that are not supported by standard validation tools,
the `@Valid` annotation is supposed to be used:

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

In the example above, a `Validator<Bar>` validator would be created for `Bar` and a `Validator<Foo>` would be created for `Foo`,
where when the `Validator<Foo>` validator is called, the validator for `Validator<Bar>` will be called internally.

### Validation options

There are two types of validation:

- `Full` - all fields that are just marked up are checked, all possible validation errors are collected
  and only then an exception is thrown. (**Default behavior**)
- `FailFast` - exception is thrown on the first validation error encountered.

Example of FailFast validation:
```java
ValidatorContext context = ValidationContext.builder().failFast(true).build();
List<Violation> violations = fooValidator.validate(value,context);
```

## Method validation

It is expected to use a special provided set of [annotations](#annotation-validation) validation for validating method arguments and result.

### Argument validation

It is required to use the `@Validate` annotation over the method to validate method arguments:

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

#### Required arguments

All arguments are required (`NotNull`) by default, so `NotNull` checks will be created for all of them.

#### Optional arguments

===! ":fontawesome-brands-java: `Java`"

    In order to specify an argument as not required requires marking it with any `@Nullable` annotation,
    **will not** create a *null* check for such an argument:

    ```java
    @Component
    Public class SomeService {

        @Validate
        public int validate(@Nullable String argument) { //(1)!
            return 1;
        }
    }
    ```

    1. Any `@Nullable` annotation will do, such as `javax.annotation.Nullable` / `jakarta.annotation.Nullable` / `org.jetbrains.annotations.Nullable` / etc.

=== ":simple-kotlin: `Kotlin`"

    It is expected to use the [Kotlin Nullability](https://kotlinlang.org/docs/null-safety.html) syntax and mark such an argument as Nullable:

    ```kotlin
    @Component
    open class SomeService {

        @Validate
        fun validate(argument: String?): Int {
            return 1
        }
    }
    ```

#### Embedded arguments

In order to validate fields of complex objects for which validators are created (or provided independently),
or fields that are not supported by standard validation tools,
`@Valid` annotation is supposed to be used:

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

In the example above, a `Validator<Bar>` validator would be created for `Bar` and a `Validator<Foo>` would be created for `Foo`,
where when the `Validator<Foo>` validator is called, the validator for `Validator<Bar>` will be called internally.

### Result validation

In order to validate the result of a method, it is required to use the `@Validate` annotation over the method and mark it up with the appropriate [annotations](#validate-annotations).
In order to check that the value is not `null`, you need to use any `@NotNull/@Nonnull` annotation:

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

    1. Indicates that the method requires validation
    2. Indicates that the result requires validation with a validator from the return value type
    3. Standard validation annotation

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

    1. Indicates that the method requires validation
    2. Indicates that the result requires validation with a validator from the return value type
    3. Standard validation annotation

### Validation options

There are two types of validation:

- `Full` - all fields that are just marked up are validated, all possible validation errors are collected
  and only then an exception is thrown. (**Default behavior**)
- `FailFast` - exception is thrown on the first validation error encountered.

Example of FailFast validation:

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

## Custom validation annotations

Creating your custom annotation requires:

1) Create an inheritor of `Validator`:

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

        fun validate(value: String?, context: ValidationContext): List<Violation> {
            if (value == null) {
                return listOf(context.violates("Should be not empty, but was null"))
            } else if (value.isEmpty()) {
                return listOf(context.violates("Should be not empty, but was empty"))
            }
            return listOf()
        }
    }
    ```

2) Create `ValidatorFactory` implementation:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface MyValidValidatorFactory extends ValidatorFactory<String> { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface MyValidValidatorFactory : ValidatorFactory<String?>
    ```

3) Register the inheritor of `ValidatorFactory` as a component:

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


4) Create a validation annotation and annotate it `@ValidatedBy` with the previously created `ValidatorFactory` inheritor:

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

5) Annotate field/argument/result:

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

## Signatures

Available signatures for repository methods out of the box:

===! ":fontawesome-brands-java: `Java`"

    Class must be non `final` in order for aspects to work.

    The `T` refers to the type of the return value.

    - `T myMethod()`
    - `Optional<T> myMethod()`
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (require [dependency](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))
    - `Flux<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (require [dependency](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

=== ":simple-kotlin: `Kotlin`"

    Class must be `open` in order for aspects to work.

    By `T` we mean the type of the return value, either `T?`, or `Unit`.

    - `myMethod(): T`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (require [dependency](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) as `implementation`)
    - `myMethod(): Flow<T>` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (require [dependency](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) as `implementation`)
