Модуль для валидации объектов и методов с помощью аннотаций.

## Подключение

=== ":fontawesome-brands-java: `Java`"

    Зависимость `build.gradle`:
    ```groovy
    annotationProcessor "ru.tinkoff.kora:annotation-processors"
    implementation "ru.tinkoff.kora:validation-module"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends ValidationModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Зависимость `build.gradle.kts`:
    ```groovy
    ksp("ru.tinkoff.kora:symbol-processors")
    implementation("ru.tinkoff.kora:validation-module")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : ValidationModule
    ```


## Аннотации валидации

Специальные аннотации валидации используются Kora для проверки значений полей классов или аргументов метода.

Доступные аннотации валидации:

- `@NotEmpty` - Проверяет что строка не пустая
- `@NotBlank` - Проверяет что строка не состоит из пустых символов
- `@Pattern` - Проверяет соответствие Regular Expression (RegEx)
- `@Range` - Проверяет что число находится в заданном диапазоне
- `@Size` - Проверяет что коллекция (List, Set, Map) или `String` имеет размер в заданном диапазоне

## Валидация класса

Предлагается использовать аннотацию `@Valid` для маркировки класса которому требуется создать валидатор посредствам Kora.

=== ":fontawesome-brands-java: `Java`"

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

=== ":fontawesome-brands-java: `Java`"

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

Созданнные валидаторы могут быть внедрены как зависимости в любой компонент, на примерах выше валидатор для класса `Foo`,
может быть внедрен по своей сигнатуре `Validator<Foo>` как зависимость компонента и использовать вручную для валидации.

Валидатор после валидации возвращает список нарушений, они могут использоваться для ручного составление ошибки либо
можно использовать метод `validateAndThrow` который бросит исключение `ViolationException` в случае ошибки валидации.

### Валидация полей

Предполагается использовать для валидации полей специальный предоставляемый набор [аннотаций](#аннотации-валидации) валидации.

Пример размеченного для валидации объекта выглядит так:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @Valid
    public record Foo(@NotEmpty String number) { }
    ```

    Для Record классов используется синтаксис доступа к полям через Record-like контракты геттеров, 
    в случае `Foo` и поля `code` будет использоваться *getter* `code()` в созданом `Validator`.

    Для обычного класса ожидается что будет использоваться синтаксис Java *Getters*, например для поля `id` будет использоваться *getter* `getId()`,
    где *getter* должен иметь минимум *package-private* видимость.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Valid
    data class Foo(@field:NotEmpty val number: String)
    ```

#### Обязательные поля

Предполагается что все поля по умолчанию являются обязательными (`NotNull`), значит для всех них будут созданы `NotNull` проверки в `Validator`.

#### Необязательные поля

=== ":fontawesome-brands-java: `Java`"

    Чтобы указать поле как не обязательное, требуется пометить его любой `@Nullable` аннотацией,
    для такого поля **не будет** создана проверка на *null*:

    ```java
    @Valid
    public record Foo(@Nullable String number) { } //(1)!
    ```

    1.  Подойдет любая аннотация `@Nullable`, такие как `javax.annotation.Nullable` / `jakarta.annotation.Nullable` / `org.jetbrains.annotations.Nullable` / и т.д.

=== ":simple-kotlin: `Kotlin`"

    Предполагается использовать [Kotlin Nullability](https://kotlinlang.ru/docs/null-safety.html) синтаксис и помечать такое поле как Nullable:

    ```kotlin
    @Valid
    data class Foo(val number: String?)
    ```

#### Вложенные поля

Для валидации полей сложных объектов для которых созданы валидаторы (или предоставлены самостоятельно),
либо полей которые не поддерживаются стандартными средствами валидации,
предполагается использовать `@Valid` аннотацию:

=== ":fontawesome-brands-java: `Java`"

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

В примере выше для `Bar` будет создан валидатор `Validator<Bar>` и для `Foo` будет создан `Validator<Foo>`,
где при вызове валидатора `Validator<Foo>` будет вызываться внутри валидатор для `Validator<Bar>`.

#### Опции валидации

Есть два вида валидации:

- `Full` - проверяются все поля которые только размечены, собираются все возможные ошибки валидации 
  и только потом бросается исключение. (**Поведение по умолчанию**)
- `FailFast` - исключение бросается на первой встреченной ошибке валидации.

Пример FailFast валидации:
```java
ValidatorContext context = ValidationContext.builder().failFast(true).build();
List<Violation> violations = fooValidator.validate(value,context);
```

## Валидация метода

Предполагается использовать для валидации аргументов метода и результата специальный предоставляемый набор [аннотаций](#аннотации-валидации) валидации.

### Валидация аргументов

Чтобы провалидировать аргументы методы, требуется использовать аннотацию `@Validate` над методом:

=== ":fontawesome-brands-java: `Java`"

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

#### Обязательные аргументы

Предполагается что все аргументы по умолчанию являются обязательными (`NotNull`), значит для всех них будут созданы `NotNull` проверки.

#### Необязательные аргументы

=== ":fontawesome-brands-java: `Java`"

    Чтобы указать аргумент как не обязательное, требуется пометить его любой `@Nullable` аннотацией,
    для такого аргумента **не будет** создана проверка на *null*:

    ```java
    @Component
    public class SomeService {

        @Validate
        public int validate(@Nullable String argument) { //(1)!
            return 1;
        }
    }
    ```

    1.  Подойдет любая аннотация `@Nullable`, такие как `javax.annotation.Nullable` / `jakarta.annotation.Nullable` / `org.jetbrains.annotations.Nullable` / и т.д.

=== ":simple-kotlin: `Kotlin`"

    Предполагается использовать [Kotlin Nullability](https://kotlinlang.ru/docs/null-safety.html) синтаксис и помечать такой аргумент как Nullable:

    ```kotlin
    @Component
    open class SomeService {

        @Validate
        fun validate(argument: String?): Int {
            return 1
        }
    }
    ```

#### Вложенные аргументы

Для валидации полей сложных объектов для которых созданы валидаторы (или предоставлены самостоятельно),
либо полей которые не поддерживаются стандартными средствами валидации,
предполагается использовать `@Valid` аннотацию:

=== ":fontawesome-brands-java: `Java`"

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

В примере выше для `Bar` будет создан валидатор `Validator<Bar>` и для `Foo` будет создан `Validator<Foo>`,
где при вызове валидатора `Validator<Foo>` будет вызываться внутри валидатор для `Validator<Bar>`.

### Валидация результата

Чтобы провалидировать результат метода, требуется использовать аннотацию `@Validate` над методом и разметить его соответствующими [аннотациями](#аннотации-валидации):

=== ":fontawesome-brands-java: `Java`"

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

    1. Указывает что метод требует валидации
    2. Указывает что результат требуется валидировать валидатором с типа возвращаемого значения
    3. Стандартная аннотация валидации

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

    1. Указывает что метод требует валидации
    2. Указывает что результат требуется валидировать валидатором с типа возвращаемого значения
    3. Стандартная аннотация валидации

### Опции валидации

Есть два вида валидации:

- `Full` - проверяются все поля которые только размечены, собираются все возможные ошибки валидации
  и только потом бросается исключение. (**Поведение по умолчанию**)
- `FailFast` - исключение бросается на первой встреченной ошибке валидации.

Пример FailFast валидации:

=== ":fontawesome-brands-java: `Java`"

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

## Собственные аннотации валидации

Для создания собственной аннотации требуется:

1) Создать наследника `Validator`:

=== ":fontawesome-brands-java: `Java`"

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

2) Создать наследника `ValidatorFactory`:

=== ":fontawesome-brands-java: `Java`"

    ```java
    public interface MyValidValidatorFactory extends ValidatorFactory<String> { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    interface MyValidValidatorFactory : ValidatorFactory<String?>
    ```

3) Зарегистрировать наследника `ValidatorFactory` как компонент:

=== ":fontawesome-brands-java: `Java`"

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


4) Создать аннотацию валидации и проаннотировать ее `@ValidatedBy` с ранее созданным наследником `ValidatorFactory`:

=== ":fontawesome-brands-java: `Java`"

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

5) Проаннотировать поле/аргумент/результат:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @Valid
    public record Foo(@MyValid String number) { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Valid
    data class Foo(@field:MyValid val number: String)
    ```

## Сигнатуры

Доступные сигнатуры для методов которые поддерживают аннотации из коробки:

=== ":fontawesome-brands-java: `Java`"

    Под `T` подразумевается тип возвращаемого значения.

    - `T myMethod()`
    - `Optional<T> myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/CompletionStage.html)
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/)
    - `Flux<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/)

=== ":simple-kotlin: `Kotlin`"

    Под `T` подразумевается тип возвращаемого значения.

    - `myMethod(): T`
    - `myMethod(): T?`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine)
    - `suspend myMethod(): T?` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine)
    - `myMethod(): Flow<T>` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine)
