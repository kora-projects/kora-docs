---
description: "Explains Kora JSON reader and writer generation, field requirements, naming, ignores, custom mappings, serialization levels, JsonNullable, sealed types, and Jackson integration. Use when working with @Json, @JsonReader, @JsonWriter, @JsonInclude, @JsonField, @JsonSkip, @Mapping, JsonNullable, JacksonModule."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora JSON reader and writer generation, field requirements, naming, ignores, custom mappings, serialization levels, JsonNullable, sealed types, and Jackson integration; key triggers include @Json, @JsonReader, @JsonWriter, @JsonInclude, @JsonField, @JsonSkip, @Mapping, JsonNullable, JacksonModule."
---

Модуль `JSON` создает эффективные реализации `JsonReader` и `JsonWriter` для классов приложения во время компиляции и без использования `Reflection` во время выполнения.
Генерация управляется аннотациями `@Json`, `@JsonReader`, `@JsonWriter` и связанными аннотациями уровня поля.

`JsonModule` также предоставляет готовые преобразователи для `HTTP`-клиента, `HTTP`-сервера, строковых параметров и `Kafka`.
Это позволяет использовать один и тот же сгенерированный `JsonReader` или `JsonWriter` в разных модулях Kora.

Пошаговый разбор перед справочным описанием смотрите в разделе [JSON](../guides/json.md).

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

Используйте `@JsonWriter`, чтобы создать только `JsonWriter`.
Этот вариант полезен, когда тип нужно только записывать в `JSON`:

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

Используйте `@JsonReader`, чтобы создать только `JsonReader`.
Этот вариант полезен, когда тип нужно только читать из `JSON`:

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

## Чтение и запись { #reader-and-writer }

Используйте `@Json`, чтобы создать одновременно `JsonReader` и `JsonWriter`.
В большинстве случаев `@Json` — предпочтительная аннотация:

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

`JsonReader<T>` и `JsonWriter<T>` — это обычные компоненты графа приложения.
После генерации или ручной регистрации их можно внедрять по сигнатуре, как любую другую зависимость.

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

`JsonWriter` записывает значение через `JsonGenerator` и также может вернуть `byte[]`, строку или форматированную строку через `toByteArray(...)`, `toString(...)` и `toPrettyString(...)`.
Методы `toByteArrayUnchecked(...)`, `toStringUnchecked(...)` и `toPrettyStringUnchecked(...)` преобразуют `IOException` в `UncheckedIOException`.

Особенности поведения во время выполнения при прямом вызове кодеков:

- `read(...)` возвращает `null`, когда парсер находится на токене `JSON` `null`, поэтому документ верхнего уровня `null` десериализуется в `null`.
- Некорректный `JSON` или неожиданный токен приводит к `JsonParseException` из `Jackson`, который является подтипом `IOException`.
- Варианты `readUnchecked(...)` и `to...Unchecked(...)` пробрасывают любой `IOException` (включая `JsonParseException`), обернутый в `UncheckedIOException`.

## Обязательные поля { #required-fields }

===! ":fontawesome-brands-java: `Java`"

    По умолчанию все поля, объявленные в объекте, считаются **обязательными** (`NotNull`).

    ```java
    @Json
    public record Dto(String field1, int field2) { }
    ```

=== ":simple-kotlin: `Kotlin`"

    По умолчанию все поля, объявленные в объекте без синтаксиса [Kotlin Nullability](https://kotlinlang.org/docs/null-safety.html), считаются **обязательными** (`NotNull`).

    ```kotlin
    @Json
    data class Dto(val field1: String, val field2: Int)
    ```

## Необязательные поля { #optional-fields }

===! ":fontawesome-brands-java: `Java`"

    Если поле `JSON` необязательное и может отсутствовать, используйте аннотацию `@Nullable`:

    ```java
    @Json
    public record Dto(@Nullable String field1, //(1)!
                      int field2) { }
    ```

    1. Подойдет любая аннотация `@Nullable`, например `javax.annotation.Nullable`, `jakarta.annotation.Nullable` или `org.jetbrains.annotations.Nullable`.

=== ":simple-kotlin: `Kotlin`"

    Для `Kotlin` используйте синтаксис [Kotlin Nullability](https://kotlinlang.org/docs/null-safety.html) и пометьте параметр как `nullable`:

    ```kotlin
    @Json
    data class Dto(
        val field1: String?,
        val field2: Int
    )
    ```

## Именование полей { #field-naming }

Если поле в `JSON` имеет имя, отличное от имени поля в классе, используйте `@JsonField`.
Она задает имя ключа в `JSON`, а также позволяет указать отдельные реализации `JsonReader` и `JsonWriter` для поля.

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

Если для поля нужны отдельные преобразователи, укажите их в `reader` и `writer`:

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

Если поле в `DTO` не нужно читать или записывать, используйте `@JsonSkip`.
Такое поле игнорируется при чтении и записи `JSON`.

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

## Уровни сериализации { #serialization-levels }

По умолчанию поля со значением `null` не записываются. (1)
{ .annotate }

1. `IncludeType.NON_NULL` — записывать поле только в том случае, если значение не `null`.

Чтобы изменить это поведение, используйте `@JsonInclude`.
Аннотацию можно разместить не только на поле, но и на классе; в этом случае правило применяется сразу ко всем полям.

Доступные варианты:

- `IncludeType.ALWAYS` — всегда записывать поле.
- `IncludeType.NON_NULL` — записывать поле, если значение не `null`.
- `IncludeType.NON_EMPTY` — записывать поле, если значение не `null` и не является пустой коллекцией или ассоциативным массивом.

Пример:

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

## Конструктор сериализации { #serialization-constructor }

Если для чтения `JSON` должен использоваться конкретный конструктор, пометьте его аннотацией `@JsonReader`.
Можно также использовать `@Json`, но `@JsonReader` имеет более высокий приоритет:

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

`JsonReader` и `JsonWriter` могут быть сгенерированы для классов, `record`, `enum` и `sealed`-типов.
Для чтения класса должен быть один публичный конструктор либо конструктор, явно помеченный `@JsonReader` или `@Json`.

### Java Bean и обычные классы { #java-bean }

`@Json`, `@JsonReader` и `@JsonWriter` не ограничиваются `record` и `data class`.
Обычный класс тоже подходит: для чтения требуется единственный публичный конструктор (или конструктор, помеченный `@JsonReader`/`@Json`), а для записи используются методы доступа к полям.
`@JsonField` можно разместить на приватных полях, чтобы переименовать ключ в `JSON`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @JsonWriter
    public class DtoJavaBean {

        @JsonField("string_field")
        private String field1;
        @JsonField("int_field")
        private int field2;

        public DtoJavaBean(String field1, int field2) {
            this.field1 = field1;
            this.field2 = field2;
        }

        public String getField1() { return field1; }

        public int getField2() { return field2; }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @JsonWriter
    class DtoJavaBean(
        @field:JsonField("string_field") val field1: String,
        @field:JsonField("int_field") val field2: Int
    )
    ```

## Обертка JsonNullable { #jsonnullable-wrapper }

Если при чтении `JSON` необходимо отличать отсутствующее поле от поля со значением `null`, используйте `JsonNullable`.
Основные состояния и фабричные методы:

- `JsonNullable.undefined()` — поле отсутствует в `JSON`.
- `JsonNullable.nullValue()` — поле присутствует и содержит `null`.
- `JsonNullable.of(value)` — поле присутствует и содержит значение.
- `JsonNullable.ofNullable(value)` — создает `nullValue()`, если значение равно `null`, иначе `of(value)`.

При записи `JSON` `undefined()` пропускается, `nullValue()` записывается как `null`, а `of(value)` записывает само значение.

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

### @Nullable против JsonNullable { #nullable-vs-jsonnullable }

Обычное [необязательное поле](#optional-fields) (`@Nullable` в `Java` или nullable-тип в `Kotlin`) сводит два разных входных значения `JSON` к одному и тому же результату: и **отсутствующее** поле, и поле с явным значением `null` читаются как `null`.
`JsonNullable` разделяет эти случаи, что и делает его правильным типом для тел `HTTP`-запросов `PATCH`, где клиент отправляет только те поля, которые действительно хочет изменить.

Три возможных результата чтения для поля `JsonNullable<T>`:

| Входной `JSON`          | Результат чтения          | `isDefined()` | `isNull()` | `value()`     |
|-------------------------|---------------------------|---------------|------------|---------------|
| `{}` (поле отсутствует) | `JsonNullable.undefined()`| `false`       | `false`    | выбрасывает   |
| `{"field": null}`       | `JsonNullable.nullValue()`| `true`        | `true`     | `null`        |
| `{"field": value}`      | `JsonNullable.of(value)`  | `true`        | `false`    | `value`       |

Поскольку `value()` выбрасывает исключение при `undefined()`, всегда защищайте доступ проверкой `isDefined()` (или проверяйте `isNull()`) перед вызовом.

### Частичное обновление PATCH { #jsonnullable-patch }

В запросе `PATCH` отсутствующее поле означает «оставить без изменений», а явный `null` означает «очистить значение».
`JsonNullable` позволяет обработчику различить эти два случая и применить только те поля, которые клиент действительно отправил:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
    public record UserPatch(JsonNullable<String> name,
                            JsonNullable<String> email) { }

    public void apply(User user, UserPatch patch) {
        if (patch.name().isDefined()) { //(1)!
            user.setName(patch.name().value());
        }
        if (patch.email().isDefined()) {
            user.setEmail(patch.email().value()); //(2)!
        }
        // fields left as undefined() are not touched
    }
    ```

    1. Поле присутствовало в теле запроса, поэтому его необходимо применить (даже если значение — явный `null`).
    2. `value()` возвращает `null`, когда клиент отправил `{"email": null}`, что очищает поле.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    data class UserPatch(
        val name: JsonNullable<String>,
        val email: JsonNullable<String>
    )

    fun apply(user: User, patch: UserPatch) {
        if (patch.name.isDefined()) { //(1)!
            user.name = patch.name.value()
        }
        if (patch.email.isDefined()) {
            user.email = patch.email.value() //(2)!
        }
        // fields left as undefined() are not touched
    }
    ```

    1. Поле присутствовало в теле запроса, поэтому его необходимо применить (даже если значение — явный `null`).
    2. `value()` возвращает `null`, когда клиент отправил `{"email": null}`, что очищает поле.

Взаимодействие с [уровнями сериализации](#serialization-levels): `IncludeType.ALWAYS` и `IncludeType.NON_NULL` **не** меняют способ записи `JsonNullable` (применяются его собственные правила `undefined`/`nullValue`/`of`).
Только `IncludeType.NON_EMPTY` влияет на `JsonNullable`, рассматривая поле `undefined()` или `nullValue()` как пустое, так что оно опускается в выводе.

## Sealed-классы и интерфейсы { #sealed-classes-and-interfaces }

Если в зависимости от значения конкретного поля нужно читать и записывать разные `JSON`-объекты, используйте
[sealed-класс или интерфейс](https://kotlinlang.org/docs/sealed-classes.html) для представления этих объектов.

Sealed-типы поддерживаются двумя аннотациями:

1. `@JsonDiscriminatorField` — задает поле-дискриминатор в `DTO`, помеченном как `sealed`-класс или интерфейс.
2. `@JsonDiscriminatorValue` — задает одно или несколько значений дискриминатора для подкласса.

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

Подклассы получают `JsonReader` и `JsonWriter` по тем же правилам, как если бы они были помечены `@Json`.
Сам `sealed`-класс или интерфейс также получает общий `JsonReader` и `JsonWriter`.
Поддерживаются вложенные `sealed`-иерархии, а `@JsonDiscriminatorValue` может принимать несколько значений для одного подкласса.

Приведенный ниже `JSON`-объект записывается в класс `FirstTypeEvent`:
```json
{
    "id": "1",
    "type": "firstType",
    "data": {
        "megaData": "megaValue"
    }
}
```

Поддерживаются обобщенные (`generic`) типы `DTO`, включая обобщенные `sealed`-иерархии.
Кодек для каждого конкретного аргумента типа разрешается из графа, как и для любого другого типа поля:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
    @JsonDiscriminatorField("@type")
    public sealed interface Response<T> {

        @JsonDiscriminatorValue("ok")
        record Ok<T>(T data) implements Response<T> {}

        @JsonDiscriminatorValue("fail")
        record Fail<T>(String error) implements Response<T> {}
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    @JsonDiscriminatorField("@type")
    sealed interface Response<T> {

        @JsonDiscriminatorValue("ok")
        data class Ok<T>(val data: T) : Response<T>

        @JsonDiscriminatorValue("fail")
        data class Fail<T>(val error: String) : Response<T>
    }
    ```

## Перечисления { #enum }

Для `enum` `JsonReader` и `JsonWriter` можно сгенерировать теми же аннотациями `@Json`, `@JsonReader` и `@JsonWriter`.
По умолчанию значением `enum` в `JSON` является результат `toString()`, поэтому его можно переопределить:

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

Если требуется значение, отличное от строки из `toString()`, пометьте публичный метод без параметров аннотацией `@Json`.
В этом случае для возвращаемого типа должны быть доступны соответствующие `JsonReader` и `JsonWriter`:

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

При чтении значение `JSON`, не совпадающее ни с одной константой `enum`, приводит к `JsonParseException` из `Jackson`, где перечислены допустимые значения.

## RawJson { #raw-json }

`RawJson` используется, когда в объект нужно включить уже готовый фрагмент `JSON`, не сериализуя его повторно.
При записи `RawJson` передается в выходной `JSON` как есть, поэтому значение должно быть корректным фрагментом `JSON`.

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

## Пользовательские преобразователи полей { #custom-field-mappers }

Чтобы использовать конкретные преобразователи только для одного поля, пометьте поле аннотацией `@Mapping`.
Аннотацию можно повторить, чтобы указать одновременно `JsonReader` и `JsonWriter`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
    public record Dto(
        @Mapping(HexReader.class)
        @Mapping(HexWriter.class)
        Integer code
    ) { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    data class Dto(
        @Mapping(HexReader::class)
        @Mapping(HexWriter::class)
        val code: Int
    )
    ```

Здесь `HexReader` реализует `JsonReader<Integer>` (`JsonReader<Int>` в `Kotlin`), а `HexWriter` — соответствующий `JsonWriter`.

## Поддерживаемые типы { #supported-types }

Модуль предоставляет встроенные типы, которые покрывают большинство распространенных задач.
Для коллекций и ассоциативных массивов Kora использует `JsonReader` или `JsonWriter` типа элемента.

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

### Пользовательские типы { #custom-types }

Если необходимо читать или записывать пользовательский тип, зарегистрируйте пользовательскую [фабрику](container.md) для `JsonReader` или `JsonWriter`.

Пример регистрации пользовательского `JsonWriter`:

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

Пример регистрации пользовательского `JsonReader`.
Reader переключается по текущему токену парсера, возвращает `null` для `JSON` `null`, читает ожидаемый токен и выбрасывает `JsonParseException` для всего остального:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {

        default JsonReader<ZoneOffset> zoneOffsetJsonReader() {
            return parser -> switch (parser.currentToken()) {
                case VALUE_NULL -> null;
                case VALUE_STRING -> ZoneOffset.of(parser.getValueAsString());
                default -> throw new JsonParseException(parser,
                    "Expecting VALUE_STRING token, got " + parser.currentToken());
            };
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application {

        fun zoneOffsetJsonReader(): JsonReader<ZoneOffset> = JsonReader { parser ->
            when (parser.currentToken()) {
                JsonToken.VALUE_NULL -> null
                JsonToken.VALUE_STRING -> ZoneOffset.of(parser.valueAsString)
                else -> throw JsonParseException(parser,
                    "Expecting VALUE_STRING token, got ${parser.currentToken()}")
            }
        }
    }
    ```

Пользовательский `JsonReader<T>` или `JsonWriter<T>` — это обычный компонент графа.
После регистрации сгенерированные кодеки автоматически подхватывают его везде, где встречается поле типа `T`, а также его можно закрепить за отдельным полем через `@JsonField(reader = ..., writer = ...)` (см. [Именование полей](#field-naming)).

## Jackson { #jackson }

Если для чтения и записи `JSON` вместо сгенерированных во время компиляции кодеков нужно использовать `Jackson`, применяйте `JacksonModule`.
Он заменяет преобразователи запросов/ответов `HTTP`-клиента и `HTTP`-сервера на основанные на `Jackson`.

Каждый преобразователь `JacksonModule` зависит от компонента `ObjectMapper`, поэтому в графе **обязательно** должна присутствовать [фабрика](container.md), предоставляющая `ObjectMapper`. Без нее граф не соберется.

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    annotationProcessor "ru.tinkoff.kora:json-annotation-processor"
    implementation "ru.tinkoff.kora:jackson-module"
    ```

    Модуль и фабрика `ObjectMapper`:
    ```java
    @KoraApp
    public interface Application extends JacksonModule {

        default ObjectMapper objectMapper() { //(1)!
            return new ObjectMapper();
        }
    }
    ```

    1. Требуется всем преобразователям `JacksonModule`; настройте его по необходимости (модули, возможности и так далее).

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    ksp("ru.tinkoff.kora:json-annotation-processor")
    implementation("ru.tinkoff.kora:jackson-module")
    ```

    Модуль и фабрика `ObjectMapper`:
    ```kotlin
    @KoraApp
    interface Application : JacksonModule {

        fun objectMapper(): ObjectMapper = ObjectMapper() //(1)!
    }
    ```

    1. Требуется всем преобразователям `JacksonModule`; настройте его по необходимости (модули, возможности и так далее).

Показанный выше `json-annotation-processor` позволяет `@Json`, `@JsonReader` и `@JsonWriter` по-прежнему генерировать кодеки, так что сгенерированная и `Jackson`-сериализация могут сосуществовать (например, `Jackson` для `HTTP` и сгенерированные кодеки для [Kafka](kafka.md)).
Сами `HTTP`-преобразователи `JacksonModule` зависят только от `ObjectMapper`.
