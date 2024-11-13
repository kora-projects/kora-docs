Модуль Json позволяет создавать производительные и без использования рефлексии 
читатели и писатели для классов приложения посредствам разметки классов аннотациями.

## Подключение

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#_4) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:json-module"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends JsonModule { }
    ```
    
=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#_4) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:json-module")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : JsonModule
    ```

## Запись

Можно воспользоваться `@JsonWriter` для создания только писателя:

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

## Чтение

Можно воспользоваться `@JsonReader` для создания только читателя:

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

## Чтение & Запись

Можно воспользоваться `@Json` для создания сразу читателя и писателя.
В большинстве случаев предпочтительнее использовать именно аннотацию `@Json`:

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

## Обязательные поля

===! ":fontawesome-brands-java: `Java`"

    По умолчанию все поля объявленные в объекте считаются **обязательными** (*NotNull*).

    ```java
    @Json
    public record Dto(String field1, int field2) { }
    ```

=== ":simple-kotlin: `Kotlin`"

    По умолчанию все поля объявленные в объекте которые не используют [Kotlin Nullability](https://kotlinlang.ru/docs/null-safety.html) синтаксис считаются **обязательными** (*NotNull*).

    ```kotlin
    @Json
    data class Dto(val field1: String, val field2: Int)
    ```

## Необязательное поля

===! ":fontawesome-brands-java: `Java`"

    В случае если поле в Json является необязательным, то есть может отсутствовать то,
    можно использовать аннотацию `@Nullable` для соответствия поля в Json и DTO:

    ```java
    @Json
    public record Dto(@Nullable String field1, //(1)!
                      int field2) { }
    ```

    1.  Подойдет любая аннотация `@Nullable`, такие как `javax.annotation.Nullable` / `jakarta.annotation.Nullable` / `org.jetbrains.annotations.Nullable` / и т.д.

=== ":simple-kotlin: `Kotlin`"

    Предполагается использовать [Kotlin Nullability](https://kotlinlang.ru/docs/null-safety.html) синтаксис и помечать такой параметр как Nullable:

    ```kotlin
    @Json
    data class Dto(
        val field1: String?,
        val field2: Int
    )
    ```

## Именование поля

В случае если поле в Json называется иначе от того что требуется использовать в классе, 
можно использовать аннотацию `@JsonField` для соответствия поля в Json и DTO.

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

## Игнорирование поля

В случае если поле в DTO не хочется читать/писать,
можно использовать аннотацию `@JsonSkip` и проигнорировать такое поле.

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

## Уровни записи

Поведение по умолчанию не подразумевает запись полей с `null` значениями. (1)
{ .annotate }

1.  `IncludeType.NON_NULL` - включать поле в запись если не `null`

В случае если хочется изменить поведение записи в этих моментах то предлагается использовать аннотацию `@JsonInclude`.
Аннотацию можно использовать не только над полем, но также над классом и тогда правило будет действовать на все поля сразу.

Доступны различные варианты использования:

- `IncludeType.ALWAYS` - включать поле в запись всегда
- `IncludeType.NON_NULL` - включать поле в запись если не `null`
- `IncludeType.NON_EMPTY` - включать поле в запись если это не `null` и не пустая коллекция

Пример использования аннотации:

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

## Указание конструктора

В случае если хочется использовать определенный конструктор для сериализации, 
то это можно сделать с указанием над конструктором аннотации `@JsonReader` либо аннотации которая имеет меньший приоритет `@Json`:

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

## JsonNullable обертка

В случае если во время десериализации, хочется отличать отсутствующее поле от указанного `null` значения,
предполагается использовать специальный тип `JsonNullable`, который позволяет отражать все состояния поля после десериализации.

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

## Изолированные классы и интерфейсы

В случае если требуется писать различные Json объекты в зависимости от значения в конкретном поле, предполагается использовать
[изолированный класс/интерфейс](https://habr.com/ru/companies/otus/articles/720044/) для представления таких объектов.

Для поддержки изолированных классов добавлены две аннотации:

1. `@JsonDiscriminatorField` - указывает поле дискриминатора в DTO, которым помечается sealed класс/интерфейс
2. `@JsonDiscriminatorValue` - значение для вышеуказанного поля, помечает класс-наследник sealed класса/интерфейса

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

Для классов-наследников будут созданы `JsonReader` и `JsonWriter` по тем же правилам, как если бы на них была аннотация `@Json` и создастся `JsonReader` и `JsonWriter` для самого sealed класса/интерфейса. 

Json объект ниже будет записан в класс `FirstTypeEvent`:
```json
{
    "id": "1",
    "type": "firstType",
    "data": {
        "megaData": "megaValue"
    }
}
```

## Поддерживаемые типы

Модуль предоставляет обширный список поддерживаемых из коробки типов которые покрывают большую часть того что может понадобиться.

??? abstract "Список поддерживаемых типов"

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

### Собственные типы

В случае если требуется писать/читать собственный тип, то предлагается зарегистрировать собственную [фабрику](container.md) для `JsonReader` / `JsonWriter`:

Пример регистрации собственно `JsonWriter`:

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

В случае если хочется использовать `Jackson` для записи/чтения, то можно самому зарегистрировать [фабрику](container.md)
предоставляющую `ObjectMapper` и соответствующие `Mappers` которые требуются в других Kora модулях будут предоставлены зависимостью ниже:

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#_4) `build.gradle`:
    ```groovy
    annotationProcessor "ru.tinkoff.kora:json-annotation-processor"
    implementation "ru.tinkoff.kora:jackson-module"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends JacksonModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#_4) `build.gradle.kts`:
    ```groovy
    ksp("ru.tinkoff.kora:json-annotation-processor")
    implementation("ru.tinkoff.kora:jackson-module")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : JacksonModule
    ```
