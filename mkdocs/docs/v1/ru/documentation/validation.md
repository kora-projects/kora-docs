---
description: "Explains Kora validation annotations, class and method validation, argument and result validation, custom validators, mapping validation failures to HTTP 400, and supported validation signatures. Use when working with @Validate, @Valid, @NotBlank, @NotEmpty, @Pattern, @Range, @Size, @Validator, ValidatorModule, ValidationModule."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora validation annotations, class and method validation, argument and result validation, custom validators, mapping ViolationException to HTTP 400, and supported validation signatures; key triggers include @Validate, @Valid, @NotBlank, @NotEmpty, @Pattern, @Range, @Size, @ValidatedBy, Validator, ValidatorFactory, ViolationException, ValidationHttpServerInterceptor, ValidatorModule, ValidationModule."
---

Модуль валидации Kora проверяет модели, аргументы методов и результаты методов с помощью аннотаций.
Для моделей Kora генерирует `Validator<T>` во время компиляции, а для методов применяет аспект `@Validate`, который вызывает нужные проверки до или после выполнения метода.

Валидация работает без использования `Reflection` во время выполнения приложения: структура объекта, вложенные поля, сигнатуры методов и доступные валидаторы проверяются процессорами аннотаций во время сборки.
Ошибки валидации возвращаются в виде списка `Violation` либо выбрасываются как `ViolationException`.

Пошаговый разбор перед справочным описанием смотрите в разделе [Валидация](../guides/validation.md).

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

Модуль поставляет два интерфейса-примеси, и вы выбираете один в зависимости от того, обслуживает ли приложение `HTTP`:

| Модуль | Артефакт | Предоставляет | Когда использовать |
|--------|----------|---------------|--------------------|
| `ValidatorModule` | `validation-common` | Сгенерированные компоненты `Validator<T>`, все встроенные фабрики ограничений и валидаторы элементов (`Validator<List<T>>`, `Validator<Set<T>>`, `Validator<Collection<T>>`) | Библиотеки и приложения без `HTTP`, либо когда вы обрабатываете `ViolationException` самостоятельно |
| `ValidationModule` | `validation-module` | Всё из `ValidatorModule` **плюс** `ValidationHttpServerInterceptor`, который отображает `ViolationException` в [ответ HTTP 400](#validation-response-http) | `HTTP`-сервисы, которые должны автоматически возвращать `400` клиентам |

`ValidationModule` расширяет `ValidatorModule`, поэтому подключение `ValidationModule` даёт вам всё, что предоставляет базовый модуль.
Показанная выше зависимость (`validation-module`) — правильный выбор для `HTTP`-сервиса; библиотека, которой нужно только генерировать валидаторы, может зависеть от `validation-common` и подключать вместо этого `ValidatorModule`.

## Аннотации валидации { #validation-annotations }

Аннотации валидации указывают Kora, что нужно проверить в поле, аргументе метода или результате метода.
Их можно применять напрямую, либо вложенная валидация может запускаться через `@Valid`, когда у типа есть сгенерированный или предоставленный вручную `Validator`.

!!! warning "Валидация Kora — это не Jakarta Bean Validation"

    Валидация Kora — это **не** [Jakarta Bean Validation (JSR-380)](https://jakarta.ee/specifications/bean-validation/).
    Все аннотации ограничений Kora находятся в пакете `ru.tinkoff.kora.validation.common.annotation` и обрабатываются во время компиляции.
    В частности, Kora **не** поставляет аннотацию ограничения `@NotNull`: значение по умолчанию является обязательным, а чтобы сделать его необязательным, вы помечаете его любой аннотацией `@Nullable` (см. [Необязательные поля](#optional-fields)).
    Kora действительно распознаёт стандартный маркер `@Nonnull` / `@NotNull` (из `javax.annotation`, `jakarta.annotation` и подобных пакетов) как явное требование не-`null`, что важно главным образом для полей [`JsonNullable`](#json-nullable).

Структурные аннотации, управляющие валидацией:

- `@Valid` — на классе или `record` генерирует `Validator<T>` для этого типа; на поле, аргументе или результате метода запускает вложенную валидацию через `Validator` соответствующего типа. Применима к типам, полям, параметрам и методам.
- `@Validate` — помечает метод, аргументы и/или результат которого должны быть провалидированы аспектом; параметр `failFast` управляет остановкой на первой ошибке (по умолчанию: `false`). Применима только к методам.
- `@ValidatedBy` — связывает пользовательскую аннотацию ограничения с `ValidatorFactory`, которая строит её `Validator` (см. [Пользовательские аннотации валидации](#custom-validation-annotations)). Применима только к типам аннотаций.

Встроенные аннотации ограничений и их параметры:

| Аннотация | Поддерживаемые типы | Параметры (значения по умолчанию) | Описание |
|-----------|---------------------|-----------------------------------|----------|
| `@NotBlank` | `String`, `CharSequence` | — | Значение не `null` и содержит хотя бы один непробельный символ. |
| `@NotEmpty` | `String`, `CharSequence`, `Iterable`, `Collection`, `List`, `Set`, `Map` | — | Значение не `null` и не пустое. |
| `@Pattern` | `String`, `CharSequence` | `value` (обязательный, без значения по умолчанию), `flags` (по умолчанию: `0`) | Значение соответствует регулярному выражению `value`; `flags` отображается на флаги [`java.util.regex.Pattern`](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/regex/Pattern.html#field.summary). |
| `@Range` | `Short`, `Integer`, `Long`, `Float`, `Double`, `BigInteger`, `BigDecimal` | `from` (обязательный, без значения по умолчанию), `to` (обязательный, без значения по умолчанию), `boundary` (по умолчанию: `INCLUSIVE_INCLUSIVE`) | Число лежит в пределах `[from, to]`; `boundary` управляет тем, включаются ли границы. |
| `@Size` | `String`, `CharSequence`, `Collection`, `List`, `Set`, `Map` | `min` (по умолчанию: `0`), `max` (обязательный, без значения по умолчанию) | Размер (длина) значения находится в пределах `min` и `max`. |

!!! note

    Обращайте внимание на обязательные параметры: у `@Size.max` **нет значения по умолчанию**, поэтому его пропуск является ошибкой компиляции; `@Range.from` и `@Range.to` оба обязательны и объявлены как `double`.
    Значение `@Range.boundary` — это перечисление `Range.Boundary` с вариантами `EXCLUSIVE_EXCLUSIVE`, `INCLUSIVE_EXCLUSIVE`, `EXCLUSIVE_INCLUSIVE` и `INCLUSIVE_INCLUSIVE`.

## Валидация класса { #class-validation }

Аннотация `@Valid` на классе или `record` указывает Kora создать `Validator<T>` для этого типа.
Сгенерированный валидатор становится обычным компонентом графа зависимостей и может быть внедрён по сигнатуре `Validator<Type>`.

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

После этого валидатор для данного класса будет доступен в контейнере зависимостей:

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

Сгенерированные валидаторы можно внедрять как зависимости в любой компонент.
В примере выше валидатор для `User` внедряется по сигнатуре `Validator<User>` и может использоваться вручную.

Метод `validate(...)` возвращает список `Violation`.
Вы можете обработать этот список самостоятельно или вызвать `validateAndThrow(...)`, который выбрасывает `ViolationException`, если есть нарушения.
Полный императивный API смотрите в разделе [Ручная валидация](#manual-validation).

### Валидация поля { #field-validation }

Валидация поля использует набор [аннотаций](#validation-annotations), предоставляемых модулем.

Объект, помеченный для валидации, выглядит так:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Valid
    public record Foo(@NotEmpty String number) { }
    ```

    Для `record` доступ к полям осуществляется через методы самого `record`.
    Для `Foo` и поля `number` сгенерированный `Validator` будет использовать метод `number()`.

    Для обычного класса используется синтаксис `JavaBeans`: например, для поля `id` будет использоваться метод `getId()`.
    Этот метод должен иметь как минимум видимость `package-private`.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Valid
    data class Foo(@field:NotEmpty val number: String)
    ```

#### Обязательные поля { #required-fields }

Все поля по умолчанию считаются обязательными, поэтому для них создаются проверки на `null`.

#### Необязательные поля { #optional-fields }

===! ":fontawesome-brands-java: `Java`"

    Чтобы пометить поле как необязательное, аннотируйте его любой аннотацией `@Nullable`.
    Для такого поля проверка на `null` **не будет** создана:

    ```java
    @Valid
    public record Foo(@Nullable String number) { } //(1)!
    ```

    1. Подойдёт любая аннотация `@Nullable`, например `javax.annotation.Nullable`, `jakarta.annotation.Nullable` или `org.jetbrains.annotations.Nullable`.

=== ":simple-kotlin: `Kotlin`"

    Чтобы пометить поле как необязательное, используйте синтаксис [`Kotlin Nullability`](https://kotlinlang.org/docs/null-safety.html) и добавьте `?` к типу поля.
    Для такого поля проверка на `null` **не будет** создана:

    ```kotlin
    @Valid
    data class Foo(val number: String?)
    ```

#### Вложенные поля { #embedded-fields }

Используйте `@Valid` для валидации вложенных объектов, у которых есть сгенерированные или предоставленные вручную валидаторы.

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

В примере выше для `Bar` будет создан `Validator<Bar>`, а для `Foo` будет создан `Validator<Foo>`.
При вызове `Validator<Foo>` он внутри себя вызовет `Validator<Bar>`.

#### Валидация коллекции { #collection-validation }

`@Valid` на поле `List`, `Set` или `Collection` валидирует **каждый элемент** через `Validator` элемента.
`ValidatorModule` предоставляет эти валидаторы элементов из коробки (`Validator<List<T>>`, `Validator<Set<T>>`, `Validator<Collection<T>>`), поэтому дополнительной настройки не требуется.

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

Каждый `Bar` в списке валидируется, а путь нарушения индексируется по позиции элемента, например `bars[0].number`.
Ограничения, такие как [`@Size`](#validation-annotations), можно комбинировать с `@Valid` на одной и той же коллекции, чтобы проверить и размер коллекции, и каждый элемент.

#### Иерархии `Sealed` { #sealed-validation }

Kora может создать `Validator` для `sealed`-иерархий.
Если `@Valid` помещена на `sealed`-тип, сгенерированный валидатор определяет фактический подтип и вызывает валидатор для соответствующей финальной реализации.

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
Используйте `@NotNull` или `@Nonnull`, чтобы запретить `undefined` или `null`.

#### Параметры валидации { #validation-options }

Существует два режима валидации, выбираемых через `ValidationContext`, передаваемый в `validate(...)`:

- `Full` — проверяются все помеченные поля, собираются все возможные ошибки валидации, и только затем возвращается список нарушений или выбрасывается исключение. Это поведение по умолчанию.
- `FailFast` — валидация останавливается на первой найденной ошибке.

`ValidationContext` можно построить несколькими эквивалентными способами:

- `ValidationContext.builder().build()` — контекст `Full` по умолчанию (то же, что и вызов `validate(value)` без контекста).
- `ValidationContext.full()` — явный контекст `Full`.
- `ValidationContext.failFast()` — контекст `FailFast`.
- `ValidationContext.builder().failFast(true).build()` — форма `FailFast` через строитель.

Пример валидации `FailFast`:

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

### Ручная валидация { #manual-validation }

Сгенерированный `Validator<T>` — это обычный компонент, поэтому его можно внедрить и вызвать напрямую — например, в сервисе, который не является `HTTP`-контроллером, или когда вы хотите изучить нарушения вместо выбрасывания исключения.

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

    1. `validate(value)` собирает **все** нарушения; используйте `validate(value, context)`, чтобы передать параметры валидации.
    2. Каждый `Violation` предоставляет `path()` и `message()`.

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

    1. `validate(value)` собирает **все** нарушения; используйте `validate(value, context)`, чтобы передать параметры валидации.
    2. Каждый `Violation` предоставляет `path()` и `message()`.

Контракт `Validator<T>` предлагает следующие методы:

- `validate(value)` / `validate(value, context)` — возвращают `List<Violation>`, который пуст, когда значение валидно (значение `null` завершается нарушением).
- `validateAndThrow(value)` / `validateAndThrow(value, context)` — выбрасывают `ViolationException` при возникновении любого нарушения и не делают ничего в противном случае.

Когда `ViolationException` перехвачено, `getViolations()` возвращает агрегированный `List<Violation>`, а `getMessage()` возвращает предварительно отформатированную многострочную сводку по каждому пути и сообщению нарушения.

## Валидация метода { #method-validation }

Валидация аргументов и результата метода использует аспект `@Validate` и набор [аннотаций](#validation-annotations), предоставляемых модулем.
Kora генерирует код аспекта во время компиляции, поэтому класс с такими методами должен поддерживать применение аспектов.

### Валидация аргумента { #argument-validation }

Чтобы провалидировать аргументы метода, используйте аннотацию `@Validate` на методе и аннотируйте аргументы нужными [ограничениями](#validation-annotations).
Аргументы можно валидировать аннотациями ограничений напрямую или через `@Valid`, когда у типа аргумента есть собственный `Validator`:

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

    1. Вложенная валидация через `Validator<User>`.
    2. Ограничение числового диапазона, применённое напрямую к аргументу.
    3. Ограничение регулярного выражения, применённое напрямую к аргументу.

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

    1. Вложенная валидация через `Validator<User>`.
    2. Ограничение числового диапазона, применённое напрямую к аргументу.
    3. Ограничение регулярного выражения, применённое напрямую к аргументу.

Если какой-либо аргумент не проходит валидацию, аспект выбрасывает `ViolationException` **до** выполнения тела метода.

#### Обязательные аргументы { #required-arguments }

Все аргументы по умолчанию считаются обязательными, поэтому для них создаются проверки на `null`.

#### Необязательные аргументы { #optional-arguments }

===! ":fontawesome-brands-java: `Java`"

    Чтобы пометить аргумент как необязательный, аннотируйте его любой аннотацией `@Nullable`.
    Для такого аргумента проверка на `null` **не будет** создана:

    ```java
    @Component
    public class SomeService {

        @Validate
        public int validate(@Nullable String argument) { //(1)!
            return 1;
        }
    }
    ```

    1. Подойдёт любая аннотация `@Nullable`, например `javax.annotation.Nullable`, `jakarta.annotation.Nullable` или `org.jetbrains.annotations.Nullable`.

=== ":simple-kotlin: `Kotlin`"

    Чтобы пометить аргумент как необязательный, используйте синтаксис [`Kotlin Nullability`](https://kotlinlang.org/docs/null-safety.html) и добавьте `?` к типу аргумента.
    Для такого аргумента проверка на `null` **не будет** создана:

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

Используйте `@Valid` для валидации вложенных аргументов, у которых есть сгенерированные или предоставленные вручную валидаторы.

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

Чтобы провалидировать результат метода, используйте аннотацию `@Validate` на методе и аннотируйте результат соответствующими [аннотациями](#validation-annotations).
Поместите `@Valid` на метод, чтобы запустить вложенную валидацию через `Validator` возвращаемого типа.
Чтобы потребовать, чтобы результат был не `null`, используйте любую аннотацию `@Nonnull` или `@NotNull`.

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

    1. Ограничения можно накладывать друг на друга: `status` необязателен (`@Nullable`), но если он присутствует, его длина должна укладываться в `@Size`.
    2. Указывает, что метод требует валидации.
    3. Указывает, что результат должен быть провалидирован через `Validator` возвращаемого типа.

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

    1. Ограничения можно накладывать друг на друга: `status` необязателен (nullable), но если он присутствует, его длина должна укладываться в `@Size`.
    2. Указывает, что метод требует валидации.
    3. Указывает, что результат должен быть провалидирован через `Validator` возвращаемого типа.

Валидация результата выполняется **после** тела метода, над его возвращаемым значением; если она не проходит, аспект выбрасывает `ViolationException` вместо возврата значения.

Ограничения также можно применять к самому контейнеру результата. Например, у результата-коллекции можно одновременно проверить размер и провалидировать её элементы:

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
    2. Указывает, что результат должен быть провалидирован через `Validator` возвращаемого типа.
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
    2. Указывает, что результат должен быть провалидирован через `Validator` возвращаемого типа.
    3. Стандартная аннотация валидации.

### Параметры валидации { #validation-options-2 }

Существует два режима валидации:

- `Full` — проверяются все помеченные аргументы и результат, собираются все возможные ошибки валидации, и только затем выбрасывается исключение. Это поведение по умолчанию.
- `FailFast` — исключение выбрасывается на первой найденной ошибке.

Пример валидации `FailFast`:

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

## HTTP обработки ошибок { #validation-response-http }

Когда `HTTP`-сервис Kora использует `ValidationModule` (из артефакта `validation-module`), неудачная валидация может быть автоматически превращена в ответ `HTTP` `400` вместо неперехваченной ошибки.

Это обрабатывается `ValidationHttpServerInterceptor` — [перехватчиком HTTP-сервера](http-server.md#interceptors), который перехватывает `ViolationException`, выброшенное аспектом `@Validate` (включая исключение, обёрнутое в `CompletionException` для асинхронных сигнатур), и формирует ответ.
По умолчанию он возвращает статус `400` с [сообщением](#manual-validation) `ViolationException` в качестве тела в формате обычного текста; пользовательский [маппер ответа](#validation-response-custom) может заменить это.

Глобальные перехватчики собираются по тегу `@Tag(HttpServerModule.class)` (см. [Перехватчики](http-server.md#interceptors)), поэтому перехватчик должен быть предоставлен **с этим тегом**, чтобы применяться к каждому маршруту:

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

    1. `ValidationModule` расширяет `ValidatorModule` и предоставляет связывание `ValidationHttpServerInterceptor` и `ViolationExceptionHttpServerResponseMapper`.
    2. Регистрирует перехватчик как **глобальный** перехватчик HTTP-сервера.
    3. Передача `null` в качестве маппера сохраняет ответ `400` по умолчанию в формате обычного текста.

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

    1. `ValidationModule` расширяет `ValidatorModule` и предоставляет связывание `ValidationHttpServerInterceptor` и `ViolationExceptionHttpServerResponseMapper`.
    2. Регистрирует перехватчик как **глобальный** перехватчик HTTP-сервера.
    3. Передача `null` в качестве маппера сохраняет ответ `400` по умолчанию в формате обычного текста.

Метод контроллера, аннотированный `@Validate`, затем формирует `400` для клиента всякий раз, когда его аргументы или результат не проходят валидацию, без настройки для каждого контроллера:

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

    1. Включает валидацию аргументов (и результата) для этого маршрута.
    2. Вложенная валидация тела запроса; нарушение приводит к `HTTP` `400` до выполнения тела.

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

    1. Включает валидацию аргументов (и результата) для этого маршрута.
    2. Вложенная валидация тела запроса; нарушение приводит к `HTTP` `400` до выполнения тела.

### Пользовательский ответ { #validation-response-custom }

Чтобы управлять статусом, заголовками или телом ответа — например, чтобы вернуть структурированную ошибку `JSON` вместо обычного текста по умолчанию — предоставьте компонент `ViolationExceptionHttpServerResponseMapper`.
Его метод `apply(request, exception)` возвращает `HttpServerResponse` для отправки; возврат `null` откатывается к ответу `400` по умолчанию в формате обычного текста.

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

    1. Сериализуется с помощью [модуля JSON](json.md).
    2. `ViolationException.getViolations()` возвращает каждый `Violation`; `path().full()` — это путь через точку (например, `customer.address.city`).
    3. Может быть возвращён любой `HttpServerResponse`; возврат `null` откатился бы к `400` по умолчанию.

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

    1. Сериализуется с помощью [модуля JSON](json.md).
    2. `ViolationException.getViolations()` возвращает каждый `Violation`; `path().full()` — это путь через точку (например, `customer.address.city`).
    3. Может быть возвращён любой `HttpServerResponse`; возврат `null` откатился бы к `400` по умолчанию.

## Пользовательские аннотации валидации { #custom-validation-annotations }

Пользовательская аннотация валидации нужна, когда стандартных проверок недостаточно.
Она связывает аннотацию с `ValidatorFactory`, и фабрика создаёт `Validator` для конкретного типа значения.

Чтобы создать пользовательскую аннотацию:

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

2. Создайте подтип `ValidatorFactory`:

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


4. Создайте аннотацию валидации и пометьте её `@ValidatedBy`, используя ранее созданный подтип `ValidatorFactory`:

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

### Параметризованные ограничения { #parameterized-constraints }

Пользовательская аннотация ограничения может объявлять параметры.
Когда это так, её подтип `ValidatorFactory` должен объявить метод `create(...)`, список параметров которого совпадает с атрибутами аннотации (**то же количество параметров, в порядке объявления**).
Kora читает значения аннотации (с применёнными значениями по умолчанию) во время компиляции и передаёт их в этот метод `create(...)`; если подходящей перегрузки `create(...)` не существует, сборка завершается ошибкой.

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

    1. Единственный атрибут аннотации.
    2. Унаследованный фабричный метод без аргументов непригоден для этого ограничения.
    3. Соответствующий `create(...)` с одним параметром; Kora передаёт `value()` в `prefix`.

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

    1. Единственный атрибут аннотации.
    2. Унаследованный фабричный метод без аргументов непригоден для этого ограничения.
    3. Соответствующий `create(...)` с одним параметром; Kora передаёт `value` в `prefix`.

Фабрика регистрируется как компонент точно так же, как и в случае без параметров (шаг 3 выше).
Это тот же механизм, который используют встроенные ограничения, и их публичные интерфейсы фабрик предоставляют переиспользуемые перегрузки, которым может делегировать пользовательская фабрика:

- `RangeValidatorFactory` — `create(double from, double to)` и `create(double from, double to, Range.Boundary boundary)`.
- `SizeValidatorFactory` — `create(int to)` и `create(int from, int to)`.
- `PatternValidatorFactory` — `create(String pattern)` и `create(String pattern, int flags)`.
- `NotEmptyValidatorFactory` и `NotBlankValidatorFactory` — `create()` без параметров.

## Сигнатуры { #signatures }

Сигнатуры методов, поддерживаемые аспектом `@Validate` из коробки:

===! ":fontawesome-brands-java: `Java`"

    Класс не должен быть `final`, чтобы аспекты работали.

    `T` означает тип возвращаемого значения.

    - `T myMethod()`
    - `Optional<T> myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletionStage.html)
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (требует [зависимость](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))
    - `Flux<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (требует [зависимость](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

=== ":simple-kotlin: `Kotlin`"

    Класс должен быть `open`, чтобы аспекты работали.

    `T` означает тип возвращаемого значения, `T?` или `Unit`.

    - `myMethod(): T`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (требует [зависимость](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) как `implementation`)
    - `myMethod(): Flow<T>` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (требует [зависимость](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) как `implementation`)
