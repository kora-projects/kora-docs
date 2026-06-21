---
description: "Explains Kora validation annotations, class and method validation, argument and result validation, custom validators, and supported validation signatures. Use when working with @Validate, @Valid, @NotNull, @NotEmpty, @Pattern, @Range, @Size, @Validator."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora validation annotations, class and method validation, argument and result validation, custom validators, and supported validation signatures; key triggers include @Validate, @Valid, @NotNull, @NotEmpty, @Pattern, @Range, @Size, @Validator, ValidationModule."
---

Модуль валидации Kora проверяет модели, аргументы методов и результаты методов по аннотациям.
Для моделей Kora генерирует `Validator<T>` на этапе компиляции, а для методов применяет аспект `@Validate`, который вызывает нужные проверки до или после выполнения метода.

Валидация работает без использования `Reflection` во время работы приложения: структура объекта, вложенные поля, сигнатуры методов и доступные валидаторы проверяются обработчиками аннотаций при сборке.
Ошибки валидации возвращаются как список `Violation` или выбрасываются как `ViolationException`.

Если нужен пошаговый разбор перед справочным описанием, смотрите [Валидация](../guides/validation.md).

## Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:validation-module"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends ValidationModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```kotlin
    implementation("ru.tinkoff.kora:validation-module")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : ValidationModule
    ```

## Аннотации валидации { #validation-annotations }

Аннотации валидации используются Kora для проверки значений полей, аргументов метода и результата метода.
Аннотации можно применять как напрямую, так и через вложенную проверку `@Valid`, если для типа есть сгенерированный или вручную предоставленный `Validator`.

Доступные аннотации валидации:

- `@Valid` - помечает класс для генерации `Validator<T>` или поле, аргумент либо результат метода для вложенной проверки через `Validator` соответствующего типа.
- `@Validate` - помечает метод, для которого нужно проверить аргументы и/или результат; параметр `failFast` управляет остановкой на первой ошибке (по умолчанию: `false`).
- `@ValidatedBy` - связывает собственную аннотацию валидации с фабрикой `ValidatorFactory`.
- `@NotNull` / `@Nonnull` - проверяет, что значение не равно `null`; можно использовать любую совместимую аннотацию из `javax.annotation`, `jakarta.annotation` или других распространенных пакетов.
- `@NotEmpty` - проверяет, что значение не равно `null` и не пустое; поддерживает `CharSequence`, `String`, `Iterable`, `Collection`, `List`, `Set` и `Map`.
- `@NotBlank` - проверяет, что строка не равна `null` и содержит хотя бы один непустой символ; поддерживает `CharSequence` и `String`.
- `@Pattern` - проверяет, что `String` или `CharSequence` соответствует регулярному выражению; параметр `value` задает выражение (`обязательный`, по умолчанию не указано), параметр `flags` задает флаги `java.util.regex.Pattern` (по умолчанию: `0`).
- `@Range` - проверяет, что число находится в заданном диапазоне; параметр `from` задает нижнюю границу (`обязательный`, по умолчанию не указано), параметр `to` задает верхнюю границу (`обязательный`, по умолчанию не указано), параметр `boundary` задает включение границ (по умолчанию: `INCLUSIVE_INCLUSIVE`).
- `@Size` - проверяет размер `List`, `Collection`, `Map`, `String` или `CharSequence`; параметр `min` задает минимальный размер (по умолчанию: `0`), параметр `max` задает максимальный размер (`обязательный`, по умолчанию не указано).

## Валидация класса { #class-validation }

Аннотация `@Valid` на классе или `record` указывает Kora, что для типа нужно создать `Validator<T>`.
Сгенерированный валидатор становится обычным компонентом графа зависимостей и может внедряться по сигнатуре `Validator<Тип>`.

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

Затем в контейнере зависимостей будет доступен валидатор такого класса:

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

Созданные валидаторы можно внедрять как зависимости в любой компонент.
В примере выше валидатор для класса `Foo` внедряется по сигнатуре `Validator<Foo>` и может использоваться вручную.

Метод `validate(...)` возвращает список нарушений `Violation`.
Этот список можно обработать самостоятельно, либо вызвать `validateAndThrow(...)`, который выбросит `ViolationException`, если нарушения есть.

### Валидация полей { #field-validation }

Для валидации полей используется набор [аннотаций](#validation-annotations), предоставляемый модулем.

Пример размеченного для валидации объекта выглядит так:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Valid
    public record Foo(@NotEmpty String number) { }
    ```

    Для `record` используется доступ к полям через методы самого `record`.
    В случае `Foo` и поля `number` в созданном `Validator` будет использоваться метод `number()`.

    Для обычного класса используется синтаксис `JavaBeans`: например, для поля `id` будет использоваться метод `getId()`.
    Такой метод должен иметь как минимум `package-private` видимость.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Valid
    data class Foo(@field:NotEmpty val number: String)
    ```

#### Обязательные поля { #required-fields }

Все поля по умолчанию считаются обязательными, поэтому для них создаются проверки на `null`.

#### Необязательные поля { #optional-fields }

===! ":fontawesome-brands-java: `Java`"

    Чтобы указать поле как необязательное, нужно пометить его любой аннотацией `@Nullable`.
    Для такого поля **не будет** создана проверка на `null`:

    ```java
    @Valid
    public record Foo(@Nullable String number) { } //(1)!
    ```

    1. Подойдет любая аннотация `@Nullable`, например `javax.annotation.Nullable`, `jakarta.annotation.Nullable` или `org.jetbrains.annotations.Nullable`.

=== ":simple-kotlin: `Kotlin`"

    Чтобы указать поле как необязательное, используйте синтаксис [`Kotlin Nullability`](https://kotlinlang.ru/docs/null-safety.html) и добавьте `?` к типу поля.
    Для такого поля **не будет** создана проверка на `null`:

    ```kotlin
    @Valid
    data class Foo(val number: String?)
    ```

#### Вложенные поля { #embedded-fields }

Для валидации вложенных объектов, для которых сгенерированы или вручную предоставлены валидаторы, используется аннотация `@Valid`.

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

В примере выше для `Bar` будет создан `Validator<Bar>`, а для `Foo` - `Validator<Foo>`.
При вызове `Validator<Foo>` внутри будет вызываться `Validator<Bar>`.

#### `Sealed`-иерархии { #sealed-validation }

Kora умеет создавать `Validator` для `sealed`-иерархий.
Если `@Valid` стоит на `sealed`-типе, сгенерированный валидатор определяет фактический подтип и вызывает валидатор подходящей конечной реализации.

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

Для `JsonNullable<T>` Kora валидирует значение `T` внутри контейнера.
Если `JsonNullable` находится в состоянии `undefined`, обычные проверки значения не выполняются.
Чтобы запретить `undefined` или `null`, используйте `@NotNull` или `@Nonnull`.

#### Опции валидации { #validation-options }

Есть два режима валидации:

- `Full` - проверяются все размеченные поля, собираются все возможные ошибки валидации, и только потом возвращается список нарушений или выбрасывается исключение. Это поведение по умолчанию.
- `FailFast` - проверка останавливается на первой найденной ошибке.

Пример валидации в режиме `FailFast`:
```java
ValidationContext context = ValidationContext.builder().failFast(true).build();
List<Violation> violations = fooValidator.validate(value, context);
```

## Валидация метода { #method-validation }

Для валидации аргументов метода и результата используется аспект `@Validate` и набор [аннотаций](#validation-annotations), предоставляемый модулем.
Kora генерирует код аспекта на этапе компиляции, поэтому класс с такими методами должен поддерживать применение аспектов.

### Валидация аргументов { #argument-validation }

Чтобы проверить аргументы метода, используйте аннотацию `@Validate` над методом:

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

#### Обязательные аргументы { #required-arguments }

Все аргументы по умолчанию считаются обязательными, поэтому для них создаются проверки на `null`.

#### Необязательные аргументы { #optional-arguments }

===! ":fontawesome-brands-java: `Java`"

    Чтобы указать аргумент как необязательный, нужно пометить его любой аннотацией `@Nullable`.
    Для такого аргумента **не будет** создана проверка на `null`:

    ```java
    @Component
    public class SomeService {

        @Validate
        public int validate(@Nullable String argument) { //(1)!
            return 1;
        }
    }
    ```

    1. Подойдет любая аннотация `@Nullable`, например `javax.annotation.Nullable`, `jakarta.annotation.Nullable` или `org.jetbrains.annotations.Nullable`.

=== ":simple-kotlin: `Kotlin`"

    Чтобы указать аргумент как необязательный, используйте синтаксис [`Kotlin Nullability`](https://kotlinlang.ru/docs/null-safety.html) и добавьте `?` к типу аргумента.
    Для такого аргумента **не будет** создана проверка на `null`:

    ```kotlin
    @Component
    open class SomeService {

        @Validate
        fun validate(argument: String?): Int {
            return 1
        }
    }
    ```

#### Вложенные аргументы { #embedded-arguments }

Для валидации вложенных аргументов, для которых сгенерированы или вручную предоставлены валидаторы, используется аннотация `@Valid`.

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

В примере выше для `Foo` будет создан `Validator<Foo>`.
При вызове метода аспект `@Validate` вызовет этот валидатор для аргумента `argument`.

### Валидация результата { #result-validation }

Чтобы проверить результат метода, используйте аннотацию `@Validate` над методом и разметьте результат соответствующими [аннотациями](#validation-annotations).
Для проверки, что результат не равен `null`, используйте любую аннотацию `@NotNull` или `@Nonnull`.

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

    1. Указывает, что метод требует валидации.
    2. Указывает, что результат нужно валидировать через `Validator` возвращаемого типа.
    3. Стандартная аннотация валидации.

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

    1. Указывает, что метод требует валидации.
    2. Указывает, что результат нужно валидировать через `Validator` возвращаемого типа.
    3. Стандартная аннотация валидации.

### Опции валидации { #validation-options-2 }

Есть два режима валидации:

- `Full` - проверяются все размеченные аргументы и результат, собираются все возможные ошибки валидации, и только потом выбрасывается исключение. Это поведение по умолчанию.
- `FailFast` - исключение выбрасывается на первой найденной ошибке.

Пример валидации в режиме `FailFast`:

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

## Собственные аннотации валидации { #custom-validation-annotations }

Собственная аннотация валидации нужна, когда стандартных проверок недостаточно.
Она связывает аннотацию с `ValidatorFactory`, а фабрика создает `Validator` для конкретного типа значения.

Чтобы создать собственную аннотацию:

1. Создайте реализацию `Validator`:

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

2. Создайте наследника `ValidatorFactory`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public interface MyValidValidatorFactory extends ValidatorFactory<String> { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface MyValidValidatorFactory : ValidatorFactory<String?>
    ```

3. Зарегистрируйте `ValidatorFactory` как компонент:

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


4. Создайте аннотацию валидации и пометьте ее `@ValidatedBy` с ранее созданным наследником `ValidatorFactory`:

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

5. Пометьте поле, аргумент или результат новой аннотацией:

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

## Сигнатуры { #signatures }

Доступные сигнатуры методов, которые поддерживаются аспектом `@Validate` из коробки:

===! ":fontawesome-brands-java: `Java`"

    Класс не должен быть `final`, чтобы аспекты работали.

    Под `T` подразумевается тип возвращаемого значения.

    - `T myMethod()`
    - `Optional<T> myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletionStage.html)
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (нужно подключить [зависимость](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))
    - `Flux<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (нужно подключить [зависимость](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

=== ":simple-kotlin: `Kotlin`"

    Класс должен быть `open`, чтобы аспекты работали.

    Под `T` подразумевается тип возвращаемого значения, либо `T?`, либо `Unit`.

    - `myMethod(): T`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (нужно подключить [зависимость](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) как `implementation`)
    - `myMethod(): Flow<T>` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (нужно подключить [зависимость](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) как `implementation`)
