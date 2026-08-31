---
description: "Explains the Kora validation constraint annotations, class and method validation, argument and result validation, configuration validation, custom constraints, mapping validation failures to HTTP 400, and supported validation signatures. Use when working with @Valid, @Validate, @ValidatedBy, @NotBlank, @NotEmpty, @Pattern, @Size, @OneOf, @UUID, @Uri, @Url, @Range, @Min, @Max, @Positive, @Negative, @Digits, @Past, @Future, @AssertTrue, ValidatorModule, ValidationModule."
agent:
  use_when: "Use this file for Kora docs or implementation questions about validation constraint annotations, class and method validation, argument and result validation, configuration validation, custom constraints, mapping ViolationException to HTTP 400, and supported validation signatures; key triggers include @Valid, @Validate, @ValidatedBy, @NotBlank, @NotEmpty, @Pattern, @Size, @OneOf, @UUID, @Uri, @Url, @Range, @Min, @Max, @Positive, @PositiveOrZero, @Negative, @NegativeOrZero, @Digits, @Past, @PastOrPresent, @Future, @FutureOrPresent, @AssertTrue, @AssertFalse, Validator, ValidatorFactory, ValidationContext, Violation, ViolationException, ValidationHttpServerInterceptor, ViolationExceptionHttpServerResponseMapper, ValidatorModule, ValidationModule, validation-common, validation-module."
---

Модуль валидации Kora проверяет модели, аргументы методов и результаты методов с помощью аннотаций.
Для моделей Kora генерирует `Validator<T>` во время компиляции, а для методов применяет аспект `@Validate`, который вызывает нужные проверки до или после выполнения метода.

Валидация работает без использования `Reflection` во время выполнения приложения: структура объекта, вложенные поля, сигнатуры методов и доступные валидаторы проверяются процессорами аннотаций во время сборки.
Ошибки валидации возвращаются в виде списка `Violation` либо выбрасываются как `ViolationException`.

Пошаговый разбор перед справочным описанием смотрите в разделе [Валидация](../guides/validation.md).

## Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) в `build.gradle`:
    ```groovy
    annotationProcessor "io.koraframework:annotation-processors" //(1)!
    implementation "io.koraframework:validation-module"
    ```

    1. Процессор аннотаций генерирует реализации `Validator<T>` и аспект `@Validate` во время компиляции. Без него валидатор не создаётся, и сборка графа падает на отсутствующей зависимости `Validator`.

    Модуль:
    ```java
    @KoraApp
    public interface Application extends ValidationModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) в `build.gradle.kts`:
    ```groovy
    ksp("io.koraframework:symbol-processors:2.0.0.RC1") //(1)!
    implementation("io.koraframework:validation-module")
    ```

    1. Процессор `KSP` генерирует реализации `Validator<T>` и аспект `@Validate` во время компиляции. Без него валидатор не создаётся, и сборка графа падает на отсутствующей зависимости `Validator`.

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : ValidationModule
    ```

Фреймворк поставляет два интерфейса-примеси, и вы выбираете один в зависимости от того, обслуживает ли приложение `HTTP`:

| Модуль | Тип | Артефакт | Предоставляет | Когда использовать |
|--------|-----|----------|---------------|--------------------|
| `ValidatorModule` | `io.koraframework.validation.common.constraint.ValidatorModule` | `validation-common` | Все встроенные фабрики ограничений и валидаторы элементов `Validator<List<T>>`, `Validator<Set<T>>`, `Validator<Collection<T>>` | Библиотеки, `CLI`-утилиты и приложения без `HTTP`, либо когда `ViolationException` вы обрабатываете сами |
| `ValidationModule` | `io.koraframework.validation.module.ValidationModule` | `validation-module` | Всё из `ValidatorModule` **плюс** `ValidationHttpServerInterceptor`, который превращает `ViolationException` в [ответ HTTP 400](#validation-response-http) | `HTTP`-сервисы, которые должны автоматически отвечать клиенту `400` |

`ValidationModule` наследует `ValidatorModule`, поэтому подключение `ValidationModule` даёт и всё содержимое базового модуля.
Сгенерированные компоненты `Validator<T>` не приходят ни из одной примеси — их добавляет процессор аннотаций для каждого типа с [`@Valid`](#class-validation), и внедрять их можно без дополнительной настройки.

!!! warning "Приложения без HTTP-сервера"

    `validation-module` объявляет `http-server-common` как **compile-only** зависимость, а `ValidationModule` поставляет `ValidationHttpServerInterceptor`, сигнатура которого выражена через `HttpServerRequest` и `HttpServerResponse`.
    Поэтому приложению без `HTTP`-сервера придётся либо явно добавить `http-server-common` в classpath, либо — что правильнее — зависеть от `validation-common` и подключать `ValidatorModule`.
    Именно так стоит поступать клиентскому или пакетному приложению.

## Аннотации валидации { #validation-annotations }

Аннотации валидации указывают Kora, что нужно проверить в поле, аргументе метода или результате метода.
Их можно применять напрямую, либо вложенная валидация может запускаться через `@Valid`, когда у типа есть сгенерированный или предоставленный вручную `Validator`.

!!! warning "Валидация Kora — это не Jakarta Bean Validation"

    Валидация Kora — это **не** [Jakarta Bean Validation (JSR-380)](https://jakarta.ee/specifications/bean-validation/).
    Все аннотации ограничений Kora находятся в пакете `io.koraframework.validation.common.annotation`, являются обычными аннотациями объявления (не `TYPE_USE`) и обрабатываются во время компиляции.
    Имена намеренно совпадают с именами из Jakarta, но семантика у Kora своя — случайно импортированный `jakarta.validation.constraints.*` даст аннотацию, которую Kora просто проигнорирует.
    В частности, Kora **не** поставляет аннотацию ограничения `@NotNull`: значение по умолчанию обязательное, а чтобы сделать его необязательным, его помечают любой аннотацией `@Nullable` (см. [Необязательные поля](#optional-fields)).
    При этом Kora распознаёт явный маркер обязательности — любую аннотацию с простым именем `Nonnull`, `NotNull` или `NonNull` — и это важно главным образом для полей [`JsonNullable`](#json-nullable).

Структурные аннотации, управляющие валидацией:

- `@Valid` — на классе, `record` или `sealed`-интерфейсе генерирует `Validator<T>` для этого типа; на поле, аргументе или результате метода запускает вложенную валидацию через `Validator` соответствующего типа. Применима к типам, полям, параметрам и методам.
- `@Validate` — помечает метод, аргументы и/или результат которого должны быть провалидированы аспектом; параметр `failFast` управляет остановкой на первой ошибке (по умолчанию: `false`). Применима только к методам.
- `@ValidatedBy` — связывает пользовательскую аннотацию ограничения с `ValidatorFactory`, которая строит её `Validator` (см. [Пользовательские аннотации валидации](#custom-validation-annotations)). Применима только к типам аннотаций.

Kora поставляет 22 встроенных ограничения. Каждое из них само помечено `@ValidatedBy`, то есть использует ровно тот же механизм расширения, что и пользовательское ограничение:

| Аннотация | Поддерживаемые типы | Атрибуты (значения по умолчанию) | Проверка |
|-----------|---------------------|----------------------------------|----------|
| `@NotBlank` | `String`, `CharSequence` | — | Значение не `null` и содержит хотя бы один непробельный символ. |
| `@NotEmpty` | `String`, `CharSequence`, `Iterable<T>`, `Collection<T>`, `List<T>`, `Set<T>`, `Map<K, V>` | — | Значение не `null`, а его длина или размер больше нуля. |
| `@Pattern` | `String`, `CharSequence` | `value` (обязательный, без значения по умолчанию), `flags` (по умолчанию: `0`) | Значение **целиком** соответствует регулярному выражению `value`; `flags` отображается на флаги [`java.util.regex.Pattern`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/regex/Pattern.html#field.summary). |
| `@Size` | `String`, `CharSequence`, `Collection<V>`, `List<V>`, `Set<V>`, `Map<K, V>` | `min` (по умолчанию: `0`), `max` (обязательный, без значения по умолчанию) | Длина или размер значения лежит в `[min, max]`, обе границы включительно. |
| `@OneOf` | `String`, `CharSequence` | `value` (`String[]`, обязательный, без значения по умолчанию) | Значение по `toString()` равно одной из перечисленных строк. |
| `@UUID` | `String`, `CharSequence` | — | Значение разбирается через `java.util.UUID.fromString(...)`. |
| `@Uri` | `String`, `CharSequence` | — | Значение разбирается как `java.net.URI`. |
| `@Url` | `String`, `CharSequence` | — | Значение разбирается как `java.net.URI` **и** содержит схему и хост, то есть является абсолютным `URL`. |
| `@Range` | `Short`, `Integer`, `Long`, `Float`, `Double`, `BigInteger`, `BigDecimal` | `from` (`double`, обязательный, без значения по умолчанию), `to` (`double`, обязательный, без значения по умолчанию), `boundary` (по умолчанию: `INCLUSIVE_INCLUSIVE`) | Число лежит между `from` и `to`; `boundary` определяет, включается ли каждая граница. |
| `@Min` | `Short`, `Integer`, `Long`, `Float`, `Double`, `BigInteger`, `BigDecimal` | `value` (`long`, обязательный, без значения по умолчанию) | Число больше либо равно `value`. |
| `@Max` | `Short`, `Integer`, `Long`, `Float`, `Double`, `BigInteger`, `BigDecimal` | `value` (`long`, обязательный, без значения по умолчанию) | Число меньше либо равно `value`. |
| `@Positive` | любой `Number` | — | Число строго больше нуля. |
| `@PositiveOrZero` | любой `Number` | — | Число больше либо равно нулю. |
| `@Negative` | любой `Number` | — | Число строго меньше нуля. |
| `@NegativeOrZero` | любой `Number` | — | Число меньше либо равно нулю. |
| `@Digits` | `Short`, `Integer`, `Long`, `Float`, `Double`, `BigInteger`, `BigDecimal`, `String`, `CharSequence` | `integer` (`int`, обязательный, без значения по умолчанию), `fraction` (`int`, обязательный, без значения по умолчанию) | После отбрасывания хвостовых нулей целая часть содержит не более `integer` цифр, а дробная — не более `fraction`. |
| `@Past` | `LocalDate`, `LocalDateTime`, `Instant`, `OffsetDateTime`, `ZonedDateTime` | — | Значение строго раньше текущего момента. |
| `@PastOrPresent` | `LocalDate`, `LocalDateTime`, `Instant`, `OffsetDateTime`, `ZonedDateTime` | — | Значение раньше текущего момента или равно ему. |
| `@Future` | `LocalDate`, `LocalDateTime`, `Instant`, `OffsetDateTime`, `ZonedDateTime` | — | Значение строго позже текущего момента. |
| `@FutureOrPresent` | `LocalDate`, `LocalDateTime`, `Instant`, `OffsetDateTime`, `ZonedDateTime` | — | Значение позже текущего момента или равно ему. |
| `@AssertTrue` | `Boolean` | — | Значение равно `true`. |
| `@AssertFalse` | `Boolean` | — | Значение равно `false`. |

!!! note

    Каждое ограничение само по себе сообщает о нарушении для значения `null` — вдобавок к проверке обязательности, которую Kora генерирует для необязательного поля или аргумента.
    Это значит, что обязательное поле `String` с `@NotBlank` при значении `null` в режиме `Full` по умолчанию даст **два** нарушения.
    Применение ограничения к типу, для которого нет фабрики, — ошибка сборки: для такой комбинации `Validator` отсутствует, и граф падает на отсутствующей зависимости, а не молча пропускает проверку.

### Строковые ограничения { #text-constraints }

`@NotBlank`, `@NotEmpty`, `@Pattern`, `@Size`, `@OneOf`, `@UUID`, `@Uri` и `@Url` работают с `String` и `CharSequence`:

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

    1. Отклоняет `null`, пустую строку и строку из одних пробельных символов.
    2. Отклоняет `null` и пустую строку; строка из пробелов проходит проверку.
    3. Длина должна быть от `3` до `64` включительно.
    4. Семантика `Pattern.matches` — соответствовать должно **всё** значение целиком, частичное совпадение не считается.
    5. Ровно одна из перечисленных строк.
    6. Должно разбираться через `java.util.UUID.fromString(...)`.
    7. Должно быть абсолютным `URL`, то есть содержать схему и хост.
    8. Должно разбираться как `URI`; относительная ссылка вида `/orders/1` допустима.

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

    1. Отклоняет `null`, пустую строку и строку из одних пробельных символов.
    2. Отклоняет `null` и пустую строку; строка из пробелов проходит проверку.
    3. Длина должна быть от `3` до `64` включительно.
    4. Семантика `Pattern.matches` — соответствовать должно **всё** значение целиком, частичное совпадение не считается.
    5. Ровно одна из перечисленных строк.
    6. Должно разбираться через `java.util.UUID.fromString(...)`.
    7. Должно быть абсолютным `URL`, то есть содержать схему и хост.
    8. Должно разбираться как `URI`; относительная ссылка вида `/orders/1` допустима.

!!! note

    Аннотация Kora называется `UUID` и конфликтует с `java.util.UUID`, если оба типа импортированы через `*`.
    Импортируйте ограничение явно как `io.koraframework.validation.common.annotation.UUID` либо указывайте `java.util.UUID` полным именем в месте использования.

### Числовые ограничения { #numeric-constraints }

`@Range`, `@Min`, `@Max`, `@Positive`, `@PositiveOrZero`, `@Negative`, `@NegativeOrZero` и `@Digits` работают с числами:

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

    1. Обе границы по умолчанию включаются.
    2. `[0, 1)` — нижняя граница включена, верхняя нет.
    3. `quantity >= 1`.
    4. `discount <= 100`.
    5. Строго больше нуля.
    6. Больше либо равно нулю.
    7. Строго меньше нуля.
    8. Меньше либо равно нулю.
    9. Не более 10 цифр до десятичной точки и 2 после неё.

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

    1. Обе границы по умолчанию включаются.
    2. `[0, 1)` — нижняя граница включена, верхняя нет.
    3. `quantity >= 1`.
    4. `discount <= 100`.
    5. Строго больше нуля.
    6. Больше либо равно нулю.
    7. Строго меньше нуля.
    8. Меньше либо равно нулю.
    9. Не более 10 цифр до десятичной точки и 2 после неё.

У `Range.Boundary` четыре варианта — `EXCLUSIVE_EXCLUSIVE`, `INCLUSIVE_EXCLUSIVE`, `EXCLUSIVE_INCLUSIVE` и `INCLUSIVE_INCLUSIVE`, значение по умолчанию — `INCLUSIVE_INCLUSIVE`.

!!! note

    `@Range.from` и `@Range.to` объявлены как `double`, и на этапе выполнения границы приводятся к типу поля: к `long` для `Short`/`Integer`/`Long`, к `BigInteger`/`BigDecimal` для больших типов и к `double` для `Float`/`Double`.
    Границу больше 2<sup>53</sup> через `@Range` точно выразить нельзя — используйте `@Min` и `@Max`, у которых атрибут имеет тип `long`.
    Перевёрнутый диапазон `@Range` отвергает уже при создании валидатора: `to` должно быть не меньше `from`. То же правило действует для `@Size`, где дополнительно требуется `min >= 0`.

### Ограничения даты и времени { #temporal-constraints }

`@Past`, `@PastOrPresent`, `@Future` и `@FutureOrPresent` сравнивают значение с текущим моментом соответствующего типа — `LocalDate.now()` для `LocalDate`, `Instant.now()` для `Instant` и так далее:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Valid
    public record Contract(@Past LocalDate signedAt, //(1)!
                           @PastOrPresent Instant createdAt, //(2)!
                           @Future OffsetDateTime expiresAt, //(3)!
                           @FutureOrPresent ZonedDateTime activeFrom) { } //(4)!
    ```

    1. Строго в прошлом.
    2. В прошлом либо ровно сейчас.
    3. Строго в будущем.
    4. В будущем либо ровно сейчас.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Valid
    data class Contract(@field:Past val signedAt: LocalDate, //(1)!
                        @field:PastOrPresent val createdAt: Instant, //(2)!
                        @field:Future val expiresAt: OffsetDateTime, //(3)!
                        @field:FutureOrPresent val activeFrom: ZonedDateTime) //(4)!
    ```

    1. Строго в прошлом.
    2. В прошлом либо ровно сейчас.
    3. Строго в будущем.
    4. В будущем либо ровно сейчас.

Поддерживаются ровно типы `LocalDate`, `LocalDateTime`, `Instant`, `OffsetDateTime` и `ZonedDateTime`.
Для любого другого временного типа — `LocalTime`, `Year`, `java.util.Date` — объявите [пользовательское ограничение](#custom-validation-annotations).

### Логические ограничения { #boolean-constraints }

`@AssertTrue` и `@AssertFalse` применяются к `Boolean`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Valid
    public record Consent(@AssertTrue Boolean termsAccepted, //(1)!
                          @AssertFalse Boolean blocked) { } //(2)!
    ```

    1. Должно быть `true`; и `null`, и `false` дают нарушение.
    2. Должно быть `false`; и `null`, и `true` дают нарушение.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Valid
    data class Consent(@field:AssertTrue val termsAccepted: Boolean, //(1)!
                       @field:AssertFalse val blocked: Boolean) //(2)!
    ```

    1. Должно быть `true`; и `null`, и `false` дают нарушение.
    2. Должно быть `false`; и `null`, и `true` дают нарушение.

### Ограничения коллекций { #collection-constraints }

`@NotEmpty` и `@Size` работают также с коллекциями и словарями, где проверяют количество элементов, а не длину строки:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Valid
    public record Basket(@NotEmpty List<String> items, //(1)!
                         @Size(min = 1, max = 10) Set<String> tags, //(2)!
                         @Size(max = 20) Map<String, String> attributes) { } //(3)!
    ```

    1. Не менее одного элемента.
    2. От `1` до `10` элементов.
    3. Не более `20` записей; `min` по умолчанию равен `0`.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Valid
    data class Basket(@field:NotEmpty val items: List<String>, //(1)!
                      @field:Size(min = 1, max = 10) val tags: Set<String>, //(2)!
                      @field:Size(max = 20) val attributes: Map<String, String>) //(3)!
    ```

    1. Не менее одного элемента.
    2. От `1` до `10` элементов.
    3. Не более `20` записей; `min` по умолчанию равен `0`.

Эти ограничения смотрят только на контейнер. Чтобы проверить ещё и каждый элемент, скомбинируйте их с `@Valid` — см. [Валидация коллекций](#collection-validation).

### Сообщения о нарушениях { #violation-messages }

Каждое встроенное ограничение формирует сообщение на английском, называющее и правило, и фактическое значение, поэтому тело ответа `HTTP` `400` по умолчанию уже пригодно для диагностики без дополнительной настройки:

| Ограничение | Сообщение |
|-------------|-----------|
| `@NotBlank` | `Should be not blank, but was null` / `... but was empty` / `... but was blank` |
| `@NotEmpty` | `Should be not empty, but was null` / `... but was empty` |
| `@Pattern` | `Should match RegEx ACC\d{10} but was: ACC1` |
| `@Size` для `String` | `Length should be in range from '3' to '64', but was smaller: 2` |
| `@Size` для коллекции или словаря | `Size should be in range from '1' to '10', but was greater: 11` |
| `@OneOf` | `Should be one of [NEW, ACTIVE, CLOSED], but was: DRAFT` |
| `@UUID` / `@Uri` / `@Url` | `Should be valid UUID, but was: abc` (и варианты для `URI` / `URL`) |
| `@Range` | `Should be in range from '1' to '900', but was greater: 1000` |
| `@Min` / `@Max` | `Should be greater than or equal to '1', but was: 0` / `Should be less than or equal to '100', but was: 101` |
| `@Positive` и соседние | `Should be positive, but was: -1` |
| `@Digits` | `Should have digits with integer part up to '10' and fraction part up to '2', but was: 1.234` |
| `@Past` и соседние | `Should be in the past, but was: 2999-01-01` |
| `@AssertTrue` / `@AssertFalse` | `Should be true, but was: false` |
| сгенерированная проверка обязательности поля | `Must be non null, but was null` |
| сгенерированная проверка обязательности аргумента | `Parameter 'code' must be non null, but was null` |
| сгенерированная проверка обязательности результата | `Result must be non null, but was null` |

Каждое `Violation` несёт также `path()`. Путь собирается по мере обхода объекта: вложенное поле добавляет `.field`, а элемент коллекции — `.[index]`.
Нарушение в поле `number` второго элемента списка `bars` поэтому даёт `bars.[1].number`, и `Violation.path().full()` возвращает ровно эту строку.

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

Валидатор для этого класса станет доступен в контейнере зависимостей:

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
Этот список можно обработать самостоятельно либо вызвать `validateAndThrow(...)`, который выбросит `ViolationException` при наличии нарушений.
Полное описание императивного API — в разделе [Ручная валидация](#manual-validation).

### Валидация полей { #field-validation }

Валидация полей использует набор [аннотаций](#validation-annotations), предоставляемых модулем.

Объект, помеченный для валидации, выглядит так:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Valid
    public record Foo(@NotEmpty String number) { }
    ```

    Для `record` поля читаются через методы самого `record`.
    Для `Foo` и поля `number` сгенерированный `Validator` использует метод `number()`.

    Для обычного класса используется синтаксис `JavaBeans`: например, для поля `id` будет использован метод `getId()`.
    У этого метода должна быть видимость минимум `package-private`.
    Поля `static` пропускаются, поэтому константа рядом с валидируемыми данными никогда не попадает в проверку.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Valid
    data class Foo(@field:NotEmpty val number: String)
    ```

    Свойства читаются напрямую, поэтому подходит и `data class`, и обычный `class` со свойствами `var`.
    Члены `const` и `@JvmStatic` пропускаются, поэтому константа в `companion object` рядом с валидируемыми данными никогда не попадает в проверку.

    Ограничение можно писать как с use-site целью `@field:`, так и без неё — для свойства из конструктора Kora читает также аннотации соответствующего параметра первичного конструктора.
    Для свойства, объявленного в теле класса, аннотацию ставьте на само свойство.

#### Обязательные поля { #required-fields }

Все поля по умолчанию считаются обязательными, поэтому для них создаются проверки на `null`.

#### Необязательные поля { #optional-fields }

===! ":fontawesome-brands-java: `Java`"

    Чтобы пометить поле как необязательное, аннотируйте его любой аннотацией `@Nullable`.
    Для такого поля проверка на `null` **не** создаётся:

    ```java
    @Valid
    public record Foo(@Nullable String number) { } //(1)!
    ```

    1. Kora построен на [JSpecify](https://jspecify.dev/), поэтому рекомендуемая аннотация — `org.jspecify.annotations.Nullable`; принимается любая аннотация с простым именем `Nullable`. `@Nullable` из `JSpecify` — это *type-use* аннотация, поэтому для квалифицированных и обобщённых типов её позиция важна: `List<@Nullable String>`, `Outer.@Nullable Inner`.

=== ":simple-kotlin: `Kotlin`"

    Чтобы пометить поле как необязательное, используйте синтаксис [`Kotlin Nullability`](https://kotlinlang.org/docs/null-safety.html) и добавьте `?` к типу поля.
    Для такого поля проверка на `null` **не** создаётся:

    ```kotlin
    @Valid
    data class Foo(val number: String?)
    ```

    В `Kotlin` собственной аннотации nullability нет — всю информацию несёт сам тип `T?`.

Ограничение по-прежнему выполняется на необязательном поле, если значение присутствует: `@Nullable @Size(min = 1, max = 10) String status` означает «может отсутствовать, но если есть — длина от 1 до 10».

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

В примере выше для `Bar` будет создан `Validator<Bar>`, а для `Foo` — `Validator<Foo>`.
При вызове `Validator<Foo>` он внутри вызовет `Validator<Bar>`, а нарушение внутри `Bar` будет отражено по пути `bar.<поле>`.

#### Валидация коллекций { #collection-validation }

`@Valid` на поле типа `List`, `Set` или `Collection` валидирует **каждый элемент** через `Validator` элемента.
`ValidatorModule` предоставляет эти валидаторы элементов из коробки (`Validator<List<T>>`, `Validator<Set<T>>`, `Validator<Collection<T>>`), поэтому ничего дополнительно подключать не нужно.

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

Валидируется каждый `Bar` из списка, а путь нарушения индексируется позицией элемента, например `bars.[0].number`.
Ограничения вроде [`@Size`](#collection-constraints) можно комбинировать с `@Valid` на одной и той же коллекции, чтобы проверить и размер коллекции, и каждый элемент, как в примере выше.

!!! note

    Сама валидация элементов ничего не сообщает про коллекцию, равную `null`, — об этом сообщает проверка обязательности поля.
    Для `Map` валидатора элементов из коробки нет: `@Valid` на поле `Map` требует `Validator<Map<K, V>>`, предоставленный приложением.

#### Иерархии `Sealed` { #sealed-validation }

Kora умеет создавать `Validator` для иерархий `sealed`.
Если `@Valid` стоит на `sealed`-типе, сгенерированный валидатор определяет фактический подтип и вызывает валидатор соответствующей финальной реализации, поэтому каждый разрешённый подтип тоже должен быть помечен `@Valid`.

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

Таким образом диспетчеризуются только `sealed`-**интерфейсы**, и собираются только финальные разрешённые подтипы.

#### `JsonNullable` { #json-nullable }

Для [`JsonNullable<T>`](json.md#jsonnullable-wrapper) Kora валидирует значение `T` внутри контейнера:

- `undefined` — поле отсутствовало в теле запроса; ограничения **не** выполняются.
- `null` — поле присутствовало со значением `null`; ограничения выполняются над `null` и, как правило, дают нарушение.
- значение задано — ограничения выполняются над значением.

Чтобы запретить сразу и `undefined`, и `null`, поставьте рядом с полем `JsonNullable` явный маркер обязательности — любую аннотацию с простым именем `Nonnull`, `NotNull` или `NonNull`.
Это единственное место, где такой маркер влияет на валидацию: во всех остальных случаях «обязательно» означает просто отсутствие `@Nullable`.

#### Неподдерживаемые цели { #unsupported-targets }

`@Valid` нужен тип, у которого есть поля или свойства для проверки, поэтому процессор отвергает с ошибкой сборки две конструкции:

- `enum` — переносите ограничения на класс, который хранит значение перечисления, либо пишите [пользовательское ограничение](#custom-validation-annotations) для него;
- не-`sealed` интерфейс, не являющийся [конфигурационным](#configuration-validation), — аннотируйте вместо него реализацию.

#### Опции валидации { #validation-options }

Существует два режима валидации, выбираемых через `ValidationContext`, передаваемый в `validate(...)`:

- `Full` — проверяются все помеченные поля, собираются все возможные ошибки валидации, и только затем возвращается список нарушений или выбрасывается исключение. Это поведение по умолчанию.
- `FailFast` — валидация останавливается на первой найденной ошибке.

`ValidationContext` можно построить несколькими равнозначными способами:

- `ValidationContext.builder().build()` — контекст `Full` по умолчанию (то же самое, что вызов `validate(value)` без контекста).
- `ValidationContext.full()` — явный контекст `Full`.
- `ValidationContext.failFast()` — контекст `FailFast`.
- `ValidationContext.builder().failFast(true).build()` — форма `FailFast` через builder.

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

### Валидация конфигурации { #configuration-validation }

`@Valid` применима и к [конфигурационному](config.md#custom-configuration) интерфейсу, помеченному `@ConfigSource` или `@ConfigMapper`.
Методы-аксессоры рассматриваются как проверяемые поля, а сгенерированный маппер конфигурации вызывает `validateAndThrow(...)` сразу после сборки объекта конфигурации — поэтому неверное значение роняет приложение на старте, а не при первом использовании.

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

Это единственный случай, когда `@Valid` разрешена на интерфейсе; вместе с остальными правилами конфигурации он описан в разделе [Конфигурация](config.md#validation).

### Ручная валидация { #manual-validation }

Сгенерированный `Validator<T>` — обычный компонент, поэтому его можно внедрить и вызвать напрямую: например, в сервисе, который не является `HTTP`-контроллером, или когда нужно разобрать нарушения, а не бросать исключение.

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

    1. `validate(value)` собирает **все** нарушения; используйте `validate(value, context)`, чтобы передать опции валидации.
    2. Каждое `Violation` предоставляет `path()` и `message()`.

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

    1. `validate(value)` собирает **все** нарушения; используйте `validate(value, context)`, чтобы передать опции валидации.
    2. Каждое `Violation` предоставляет `path()` и `message()`.

Контракт `Validator<T>` предлагает следующие методы:

- `validate(value)` / `validate(value, context)` — возвращают `List<Violation>`, пустой, если значение корректно.
- `validateAndThrow(value)` / `validateAndThrow(value, context)` — выбрасывают `ViolationException` при любом нарушении и ничего не делают в противном случае.

Передача `null` в любой из них не означает «проверять нечего»: сгенерированный валидатор сообщает об одном нарушении для входного `null`.

При перехвате `ViolationException` метод `getViolations()` возвращает накопленный `List<Violation>`, а `getMessage()` — готовую многострочную сводку:

```text
Validation failed with 2 violations:
1) Path 'name' violation: Length should be in range from '3' to '6', but was smaller: 2
2) Path 'bars.[0].number' violation: Should be not blank, but was blank
```

## Валидация метода { #method-validation }

Валидация аргументов и результата метода использует аспект `@Validate` и набор [аннотаций](#validation-annotations), предоставляемых модулем.
Kora генерирует код аспекта во время компиляции, поэтому класс с такими методами должен поддерживать применение аспектов.

### Валидация аргументов { #argument-validation }

Чтобы валидировать аргументы метода, поставьте аннотацию `@Validate` на метод и пометьте аргументы нужными [ограничениями](#validation-annotations).
Аргументы можно валидировать либо аннотациями ограничений напрямую, либо через `@Valid`, если у типа аргумента есть собственный `Validator`:

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
    2. Числовое ограничение диапазона, применённое к аргументу напрямую.
    3. Ограничение регулярным выражением, применённое к аргументу напрямую.

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

    1. Вложенная валидация через `Validator<User>`.
    2. Числовое ограничение диапазона, применённое к аргументу напрямую.
    3. Ограничение регулярным выражением, применённое к аргументу напрямую.

Если хотя бы один аргумент не проходит валидацию, аспект выбрасывает `ViolationException` **до** выполнения тела метода.
Нарушения по аргументам сообщаются по пути с именем параметра, например `code` или `user.name`.

#### Обязательные аргументы { #required-arguments }

Все аргументы по умолчанию считаются обязательными, поэтому для них создаются проверки на `null`.
Примитивные аргументы на `null` не проверяются — там нечего проверять.

#### Необязательные аргументы { #optional-arguments }

===! ":fontawesome-brands-java: `Java`"

    Чтобы пометить аргумент как необязательный, аннотируйте его любой аннотацией `@Nullable`.
    Для такого аргумента проверка на `null` **не** создаётся:

    ```java
    @Component
    public class SomeService {

        @Validate
        public int validate(@Nullable String argument) { //(1)!
            return 1;
        }
    }
    ```

    1. `org.jspecify.annotations.Nullable` — аннотация, на которой построена сама Kora; принимается любая аннотация с простым именем `Nullable`.

=== ":simple-kotlin: `Kotlin`"

    Чтобы пометить аргумент как необязательный, используйте синтаксис [`Kotlin Nullability`](https://kotlinlang.org/docs/null-safety.html) и добавьте `?` к типу аргумента.
    Для такого аргумента проверка на `null` **не** создаётся:

    ```kotlin
    @Component
    open class SomeService {

        @Validate
        open fun validate(argument: String?): Int {
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
        open fun validate(@Valid argument: Foo): Int {
            return 1
        }
    }
    ```

В примере выше для `Foo` будет создан `Validator<Foo>`.
При вызове метода аспект `@Validate` вызовет этот валидатор для аргумента `argument`.

### Валидация результата { #result-validation }

Чтобы валидировать результат метода, поставьте аннотацию `@Validate` на метод и пометьте результат соответствующими [аннотациями](#validation-annotations).
Поставьте `@Valid` на метод, чтобы запустить вложенную валидацию через `Validator` возвращаемого типа.
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

    1. Ограничения можно совмещать: `status` необязателен (`@Nullable`), но если он задан, его длина должна укладываться в `@Size`.
    2. Указывает, что метод требует валидации.
    3. Указывает, что результат должен валидироваться через `Validator` возвращаемого типа.

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

    1. Ограничения можно совмещать: `status` необязателен (nullable), но если он задан, его длина должна укладываться в `@Size`.
    2. Указывает, что метод требует валидации.
    3. Указывает, что результат должен валидироваться через `Validator` возвращаемого типа.

Валидация результата выполняется **после** тела метода, над возвращаемым значением; при неудаче аспект выбрасывает `ViolationException` вместо возврата значения.

Ограничения можно применять и к самому контейнеру результата. Например, результат-коллекцию можно одновременно проверить по размеру и провалидировать её элементы:

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
    2. Указывает, что результат должен валидироваться через `Validator` возвращаемого типа.
    3. Обычная аннотация валидации.

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

    1. Указывает, что метод требует валидации.
    2. Указывает, что результат должен валидироваться через `Validator` возвращаемого типа.
    3. Обычная аннотация валидации.

Метод, который ничего не возвращает, всё равно может валидировать свои аргументы, но валидация результата для `void` / `Unit` — ошибка сборки: проверять нечего.

### Опции валидации { #validation-options-2 }

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
        open fun validate(@NotEmpty c2: String): Int = 1
    }
    ```

Аргументы и результат — две отдельные стадии: в режиме `Full` по умолчанию все нарушения по аргументам собираются и выбрасываются вместе, а результат проверяется только если аргументы прошли.

## HTTP-ответ при ошибке валидации { #validation-response-http }

Когда `HTTP`-сервис Kora использует `ValidationModule` (из артефакта `validation-module`), неуспешную валидацию можно автоматически превратить в ответ `HTTP` `400` вместо необработанной ошибки.

Этим занимается `ValidationHttpServerInterceptor` — [перехватчик HTTP-сервера](http-server.md#interceptors), который ловит `ViolationException`, брошенное аспектом `@Validate`, и формирует ответ.
По умолчанию он возвращает статус `400` с [сообщением](#manual-validation) `ViolationException` в теле `text/plain`; заменить это можно [собственным маппером ответа](#validation-response-custom).

`ValidationModule` поставляет перехватчик **без тега**, тогда как `HTTP`-сервер собирает глобальные перехватчики по тегу `@Tag(HttpServer.class)` (см. [Перехватчики](http-server.md#interceptors)).
Переопределите метод модуля и добавьте этот тег, чтобы перехватчик применялся ко всем маршрутам:

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

    1. `ValidationModule` наследует `ValidatorModule` и объявляет умолчание для `ValidationHttpServerInterceptor`.
    2. Регистрирует перехватчик как **глобальный** перехватчик HTTP-сервера; `HttpServer` — это `io.koraframework.http.server.common.HttpServer`.
    3. Маппер, равный `null`, оставляет ответ `400` с текстом по умолчанию.

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

    1. `ValidationModule` наследует `ValidatorModule` и объявляет умолчание для `ValidationHttpServerInterceptor`.
    2. Регистрирует перехватчик как **глобальный** перехватчик HTTP-сервера; `HttpServer` — это `io.koraframework.http.server.common.HttpServer`.
    3. В контракте Kora параметр объявлен как `@Nullable`, поэтому переопределение в `Kotlin` обязано принимать `ViolationExceptionHttpServerResponseMapper?`; маппер, равный `null`, оставляет ответ `400` с текстом по умолчанию.

После этого метод контроллера с `@Validate` отдаёт клиенту `400` всякий раз, когда его аргументы или результат не проходят валидацию, без настройки на уровне каждого контроллера:

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

    1. Включает валидацию аргументов (и результата) для этого маршрута.
    2. Вложенная валидация тела запроса; нарушение даёт `HTTP` `400` до выполнения тела метода.
    3. Ограничения работают на любом связанном параметре — `@Path`, `@Query`, `@Header`, `@Cookie`, — а не только на теле `JSON`.

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

    1. Включает валидацию аргументов (и результата) для этого маршрута.
    2. Вложенная валидация тела запроса; нарушение даёт `HTTP` `400` до выполнения тела метода.
    3. Ограничения работают на любом связанном параметре — `@Path`, `@Query`, `@Header`, `@Cookie`, — а не только на теле `JSON`.

### Собственный ответ { #validation-response-custom }

Чтобы управлять статусом, заголовками или телом ответа — например, вернуть структурированную ошибку `JSON` вместо текста по умолчанию — предоставьте компонент `ViolationExceptionHttpServerResponseMapper`.
Его метод `apply(request, exception)` возвращает `HttpServerResponse` для отправки; возврат `null` откатывает к ответу `400` с текстом по умолчанию.

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

    1. Сериализуется [модулем JSON](json.md).
    2. `ViolationException.getViolations()` возвращает все `Violation`; `path().full()` — путь через точку (например, `customer.address.city`).
    3. Вернуть можно любой `HttpServerResponse`; возврат `null` откатил бы к ответу `400` по умолчанию.

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

    1. Сериализуется [модулем JSON](json.md).
    2. `ViolationException.getViolations()` возвращает все `Violation`; `path().full()` — путь через точку (например, `customer.address.city`).
    3. Вернуть можно любой `HttpServerResponse`; возврат `null` откатил бы к ответу `400` по умолчанию.

## Пользовательские аннотации валидации { #custom-validation-annotations }

Пользовательская аннотация валидации нужна, когда стандартных проверок недостаточно.
Она связывает аннотацию с `ValidatorFactory`, а фабрика создаёт `Validator` для конкретного типа значения.

Чтобы создать собственную аннотацию:

1. Создайте реализацию `Validator`:

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

4. Создайте аннотацию валидации и пометьте её `@ValidatedBy`, указав созданный ранее подтип `ValidatorFactory`:

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

!!! note

    `ValidatorFactory` ищется в графе зависимостей по объявленному вами **подтипу** фабрики, параметризованному типом аннотированного значения, — `MyValidValidatorFactory<String>` для поля `String`.
    Регистрируйте по одному компоненту-фабрике на каждый тип значения, который должно поддерживать ограничение; именно так встроенные ограничения по отдельности покрывают `String` и `CharSequence`.

### Параметризованные ограничения { #parameterized-constraints }

Пользовательская аннотация ограничения может объявлять параметры.
В этом случае её подтип `ValidatorFactory` обязан объявить метод `create(...)`, список параметров которого соответствует атрибутам аннотации (**то же количество параметров, в порядке объявления**).
Kora читает значения аннотации (с применёнными значениями по умолчанию) во время компиляции и передаёт их в этот метод `create(...)`; если подходящей перегрузки `create(...)` нет, сборка падает с сообщением `Expected <Factory>#create() method with N parameters, but was didn't find such`.

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
    2. Унаследованный метод фабрики без аргументов для этого ограничения не применим.
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
    2. Унаследованный метод фабрики без аргументов для этого ограничения не применим.
    3. Соответствующий `create(...)` с одним параметром; Kora передаёт `value` в `prefix`.

Фабрика регистрируется как компонент точно так же, как в случае без параметров (шаг 3 выше).
Это тот же механизм, который используют встроенные ограничения, и их публичные интерфейсы фабрик предоставляют переиспользуемые перегрузки, к которым может обращаться пользовательская фабрика:

| Фабрика | Перегрузки |
|---------|------------|
| `RangeValidatorFactory` | `create(double from, double to)`, `create(double from, double to, Range.Boundary boundary)` |
| `SizeValidatorFactory` | `create(int to)`, `create(int from, int to)` |
| `PatternValidatorFactory` | `create(String pattern)`, `create(String pattern, int flags)` — унаследованный `create()` бросает исключение, шаблон обязателен |
| `MinValidatorFactory` / `MaxValidatorFactory` | `create(long value)` |
| `DigitsValidatorFactory` | `create(int integer, int fraction)` |
| `OneOfValidatorFactory` | `create(String[] value)` |
| `NotEmptyValidatorFactory`, `NotBlankValidatorFactory`, `UuidValidatorFactory`, `UriValidatorFactory`, `UrlValidatorFactory`, `AssertTrueValidatorFactory`, `AssertFalseValidatorFactory`, `PositiveValidatorFactory`, `PositiveOrZeroValidatorFactory`, `NegativeValidatorFactory`, `NegativeOrZeroValidatorFactory`, `PastValidatorFactory`, `PastOrPresentValidatorFactory`, `FutureValidatorFactory`, `FutureOrPresentValidatorFactory` | `create()` без параметров |

Поскольку это обычные компоненты графа, объявленные через `@DefaultComponent`, собственная фабрика для того же типа заменяет встроенное поведение соответствующего ограничения.

## Сигнатуры { #signatures }

Сигнатуры методов, поддерживаемые аспектом `@Validate` из коробки:

===! ":fontawesome-brands-java: `Java`"

    Класс не должен быть `final`, чтобы аспекты работали.

    `T` — тип возвращаемого значения.

    - `T myMethod()`
    - `void myMethod()` (только аргументы — ограничение на результат `void` является ошибкой сборки)
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/CompletionStage.html)
    - `CompletableFuture<T> myMethod()`

    `Publisher`, `Mono`, `Flux` и «голый» `Future<T>` **не** поддерживаются и роняют сборку с явным сообщением.

=== ":simple-kotlin: `Kotlin`"

    Класс должен быть `open`, чтобы аспекты работали.

    `T` — тип возвращаемого значения, `T?` или `Unit`.

    - `myMethod(): T`
    - `myMethod(): Unit` (только аргументы — ограничение на результат `Unit` является ошибкой сборки)
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (требуется [зависимость](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) как `implementation`)
    - `myMethod(): Flow<T>` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (требуется [зависимость](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) как `implementation`)

    Для `Flow<T>` аргументы валидируются в момент сбора потока, а ограничения на результат применяются к каждому испущенному элементу.
    `CompletionStage`, `Future`, `Mono` и `Flux` **не** поддерживаются и роняют сборку с явным сообщением.
