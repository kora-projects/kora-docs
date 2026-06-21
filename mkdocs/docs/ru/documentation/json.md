---
description: "Explains Kora JSON reader and writer generation, field requirements, naming, ignores, serialization levels, JsonNullable, sealed types, and Jackson integration. Use when working with @Json, @JsonReader, @JsonWriter, @JsonInclude, @JsonField, @JsonSkip, JsonNullable, JacksonModule."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora JSON reader and writer generation, field requirements, naming, ignores, serialization levels, JsonNullable, sealed types, and Jackson integration; key triggers include @Json, @JsonReader, @JsonWriter, @JsonInclude, @JsonField, @JsonSkip, JsonNullable, JacksonModule."
---

Модуль `JSON` создает производительные `JsonReader` и `JsonWriter` для классов приложения на этапе компиляции и без использования `Reflection` во время работы.
Для генерации используются аннотации `@Json`, `@JsonReader`, `@JsonWriter` и связанные с ними настройки полей.

`JsonModule` также подключает готовые преобразователи для `HTTP`-клиента, `HTTP`-сервера, параметров строкового вида и `Kafka`.
Благодаря этому один и тот же сгенерированный `JsonReader` или `JsonWriter` можно использовать в разных модулях Kora.

Если нужен пошаговый разбор перед справочным описанием, смотрите [JSON](../guides/json.md).

## Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:json-module"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends JsonModule { }
    ```
    
=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:json-module")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : JsonModule
    ```

## Запись { #writer }

Можно воспользоваться `@JsonWriter` для создания только `JsonWriter`.
Этот вариант нужен, когда тип требуется только записывать в `JSON`:

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

## Чтение { #reader }

Можно воспользоваться `@JsonReader` для создания только `JsonReader`.
Этот вариант нужен, когда тип требуется только читать из `JSON`:

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

## Чтение & Запись { #reader-and-writer }

Можно воспользоваться `@Json` для создания сразу `JsonReader` и `JsonWriter`.
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

## Интерфейсы чтения и записи { #reader-writer-interfaces }

`JsonReader<T>` и `JsonWriter<T>` - это обычные компоненты графа приложения.
После генерации или ручной регистрации их можно внедрять по сигнатуре, как и другие зависимости.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MyService {

        private final JsonReader<Dto> reader;
        private final JsonWriter<Dto> writer;

        public MyService(JsonReader<Dto> reader, JsonWriter<Dto> writer) {
            this.reader = reader;
            this.writer = writer;
        }

        public Dto read(String json) throws IOException {
            return this.reader.read(json);
        }

        public byte[] write(Dto dto) throws IOException {
            return this.writer.toByteArray(dto);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyService(
        private val reader: JsonReader<Dto>,
        private val writer: JsonWriter<Dto>
    ) {

        fun read(json: String): Dto? {
            return reader.read(json)
        }

        fun write(dto: Dto): ByteArray {
            return writer.toByteArray(dto)
        }
    }
    ```

`JsonReader` читает значение из `JsonParser`, `byte[]`, `String` или `InputStream`.
Методы `readUnchecked(...)` делают то же самое, но преобразуют `IOException` в `UncheckedIOException`.

`JsonWriter` записывает значение через `JsonGenerator`, а также умеет возвращать `byte[]`, строку и форматированную строку через `toByteArray(...)`, `toString(...)` и `toPrettyString(...)`.
Методы `toByteArrayUnchecked(...)`, `toStringUnchecked(...)` и `toPrettyStringUnchecked(...)` преобразуют `IOException` в `UncheckedIOException`.

## Обязательные поля { #required-fields }

===! ":fontawesome-brands-java: `Java`"

    По умолчанию все поля, объявленные в объекте, считаются **обязательными** (`NotNull`).

    ```java
    @Json
    public record Dto(String field1, int field2) { }
    ```

=== ":simple-kotlin: `Kotlin`"

    По умолчанию все поля, объявленные в объекте без синтаксиса [Kotlin Nullability](https://kotlinlang.ru/docs/null-safety.html), считаются **обязательными** (`NotNull`).

    ```kotlin
    @Json
    data class Dto(val field1: String, val field2: Int)
    ```

## Необязательные поля { #optional-fields }

===! ":fontawesome-brands-java: `Java`"

    Если поле в `JSON` является необязательным и может отсутствовать, используйте аннотацию `@Nullable`:

    ```java
    @Json
    public record Dto(@Nullable String field1, //(1)!
                      int field2) { }
    ```

    1.  Подойдет любая аннотация `@Nullable`, например `javax.annotation.Nullable`, `jakarta.annotation.Nullable` или `org.jetbrains.annotations.Nullable`.

=== ":simple-kotlin: `Kotlin`"

    Для `Kotlin` предполагается использовать синтаксис [Kotlin Nullability](https://kotlinlang.ru/docs/null-safety.html) и помечать такой параметр как `nullable`:

    ```kotlin
    @Json
    data class Dto(
        val field1: String?,
        val field2: Int
    )
    ```

## Именование поля { #field-naming }

Если поле в `JSON` называется иначе, чем поле в классе, можно использовать аннотацию `@JsonField`.
Она задает имя ключа в `JSON`, а также позволяет указать отдельные `JsonReader` и `JsonWriter` для конкретного поля.

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

Если для поля нужно использовать отдельные преобразователи, укажите их в `reader` и `writer`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
    public record Dto(@JsonField(value = "created_at",
                                 reader = InstantJsonReader.class,
                                 writer = InstantJsonWriter.class)
                      Instant createdAt) { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    data class Dto(
        @field:JsonField(
            value = "created_at",
            reader = InstantJsonReader::class,
            writer = InstantJsonWriter::class
        )
        val createdAt: Instant
    )
    ```

## Игнорирование поля { #field-ignore }

Если поле в `DTO` не нужно читать или писать, можно использовать аннотацию `@JsonSkip`.
Такое поле будет проигнорировано при чтении и записи `JSON`.

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

## Уровни записи { #serialization-levels }

По умолчанию поля со значением `null` не записываются. (1)
{ .annotate }

1.  `IncludeType.NON_NULL` - записывать поле, только если значение не равно `null`.

Чтобы изменить это поведение, используйте аннотацию `@JsonInclude`.
Аннотацию можно поставить не только на поле, но и на класс, тогда правило будет действовать на все поля сразу.

Доступны различные варианты использования:

- `IncludeType.ALWAYS` - всегда записывать поле.
- `IncludeType.NON_NULL` - записывать поле, если значение не равно `null`.
- `IncludeType.NON_EMPTY` - записывать поле, если значение не равно `null` и не является пустой коллекцией или пустым словарем.

Пример использования аннотации:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
    @JsonInclude(IncludeType.NON_NULL)
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

## Указание конструктора { #serialization-constructor }

Если для чтения `JSON` нужно использовать определенный конструктор, укажите над ним аннотацию `@JsonReader`.
Также можно использовать аннотацию `@Json`, но у `@JsonReader` приоритет выше:

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

`JsonReader` и `JsonWriter` можно генерировать для классов, `record`, `enum` и `sealed`-типов.
Для чтения класса должен быть доступен один публичный конструктор, либо конструктор, явно помеченный `@JsonReader` или `@Json`.

## Обертка JsonNullable { #jsonnullable-wrapper }

Если при чтении `JSON` нужно отличать отсутствующее поле от поля со значением `null`, используйте специальный тип `JsonNullable`.
Основные состояния и фабричные методы:

- `JsonNullable.undefined()` - поле отсутствует в `JSON`.
- `JsonNullable.nullValue()` - поле присутствует и содержит `null`.
- `JsonNullable.of(value)` - поле присутствует и содержит значение.
- `JsonNullable.ofNullable(value)` - создает `nullValue()`, если значение равно `null`, иначе `of(value)`.

При записи `JSON` значение `undefined()` пропускается, `nullValue()` записывается как `null`, а `of(value)` записывает само значение.

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

## Изолированные классы и интерфейсы { #sealed-classes-and-interfaces }

Если нужно читать и писать разные `JSON`-объекты в зависимости от значения конкретного поля, используйте
[изолированный класс или интерфейс](https://habr.com/ru/companies/otus/articles/720044/) для представления таких объектов.

Для поддержки изолированных типов добавлены две аннотации:

1. `@JsonDiscriminatorField` - указывает поле дискриминатора в `DTO`, которым помечается `sealed`-класс или интерфейс.
2. `@JsonDiscriminatorValue` - задает одно или несколько значений дискриминатора для класса-наследника.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
    @JsonDiscriminatorField("type")
    public sealed interface Event {

        @JsonDiscriminatorValue("firstType")
        record FirstTypeEvent(String id, String type) implements Event {}

        @JsonDiscriminatorValue("secondType")
        record SecondTypeEvent(String id, Integer code) implements Event {}

        @JsonDiscriminatorValue("thirdType")
        record ThirdTypeEvent(String id, Boolean status) implements Event {}
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    @JsonDiscriminatorField("type")
    sealed interface Event {

        @JsonDiscriminatorValue("firstType")
        data class FirstTypeEvent(val id: String, val type: String) : Event

        @JsonDiscriminatorValue("secondType")
        data class SecondTypeEvent(val id: String, val code: Integer) : Event

        @JsonDiscriminatorValue("thirdType")
        data class ThirdTypeEvent(val id: String, val status: Boolean) : Event
    }
    ```

Для классов-наследников будут созданы `JsonReader` и `JsonWriter` по тем же правилам, как если бы на них была аннотация `@Json`.
Для самого `sealed`-класса или интерфейса также будет создан общий `JsonReader` и `JsonWriter`.
Поддерживаются вложенные `sealed`-иерархии, а `@JsonDiscriminatorValue` может принимать несколько значений для одного класса-наследника.

`JSON`-объект ниже будет записан в класс `FirstTypeEvent`:
```json
{
    "id": "1",
    "type": "firstType",
    "data": {
        "megaData": "megaValue"
    }
}
```

## Перечисления { #enum }

Для `enum` можно генерировать `JsonReader` и `JsonWriter` теми же аннотациями `@Json`, `@JsonReader` и `@JsonWriter`.
По умолчанию значением `enum` в `JSON` будет результат метода `toString()`, поэтому его можно переопределить:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
    public enum Status {
        CREATED,
        DELETED;

        @Override
        public String toString() {
            return this.name().toLowerCase();
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    enum class Status {
        CREATED,
        DELETED;

        override fun toString(): String {
            return name.lowercase()
        }
    }
    ```

Если нужно использовать не строковое значение из `toString()`, можно пометить публичный метод без параметров аннотацией `@Json`.
В этом случае для типа возвращаемого значения должен быть доступен соответствующий `JsonReader` и `JsonWriter`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
    public enum Status {
        CREATED(1),
        DELETED(2);

        private final int code;

        Status(int code) {
            this.code = code;
        }

        @Json
        public int code() {
            return this.code;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    enum class Status(private val code: Int) {
        CREATED(1),
        DELETED(2);

        @Json
        fun code(): Int = code
    }
    ```

## RawJson { #raw-json }

`RawJson` нужен, когда в объект требуется вставить уже готовый фрагмент `JSON` без повторной сериализации.
При записи `RawJson` передается в выходной `JSON` как есть, поэтому значение должно быть корректным `JSON`-фрагментом.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
    public record Dto(String id, RawJson payload) { }

    var dto = new Dto("1", new RawJson("{\"status\":\"ok\"}"));
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    data class Dto(val id: String, val payload: RawJson)

    val dto = Dto("1", RawJson("""{"status":"ok"}"""))
    ```

## Поддерживаемые типы { #supported-types }

Модуль предоставляет список поддерживаемых из коробки типов, которые покрывают большую часть типовых задач.
Для коллекций и словарей Kora использует `JsonReader` или `JsonWriter` типа элемента.

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
    * RawJson
    * Object
    * Enum
    * List<T>
    * Set<T>
    * SortedSet<T>
    * Map<String, T>
    * LocalDate
    * LocalTime
    * LocalDateTime
    * Instant
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

### Собственные типы { #custom-types }

Если требуется читать или писать собственный тип, зарегистрируйте собственную [фабрику](container.md) для `JsonReader` или `JsonWriter`.

Пример регистрации собственного `JsonWriter`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {

        default JsonWriter<ZoneOffset> zoneOffsetJsonWriter() {
            return (generator, value) -> {
                if (value != null) {
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

## Jackson { #jackson }

Если для чтения и записи `JSON` нужно использовать `Jackson`, зарегистрируйте в графе приложения [фабрику](container.md), которая предоставляет `ObjectMapper`.
Модуль `JacksonModule` добавляет преобразователи для `HTTP`-клиента и `HTTP`-сервера, которые используют этот `ObjectMapper`.

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
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

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    ksp("ru.tinkoff.kora:json-annotation-processor")
    implementation("ru.tinkoff.kora:jackson-module")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : JacksonModule
    ```
