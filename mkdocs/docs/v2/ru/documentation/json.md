---
description: "Explains Kora compile-time JSON reader and writer generation, field requirements, naming strategies, ignores, serialization levels, value types, JsonNullable, sealed hierarchies, enums, custom codecs, parse errors, and the Jackson escape hatch. Use when working with @Json, @JsonReader, @JsonWriter, @JsonInclude, @JsonField, @JsonSkip, @JsonDiscriminatorField, @NamingStrategy, @Mapping, JsonNullable, RawJson, JacksonModule."
agent:
  use_when: "Use this file for Kora docs or implementation questions about compile-time JSON reader and writer generation, field requirements, naming strategies, ignores, serialization levels, value types, JsonNullable, sealed hierarchies, enums, custom codecs, parse errors, and the Jackson escape hatch; key triggers include @Json, @JsonReader, @JsonWriter, @JsonInclude, @JsonField, @JsonSkip, @JsonDiscriminatorField, @JsonDiscriminatorValue, @NamingStrategy, @Mapping, JsonNullable, RawJson, StreamReadException, JsonModule, JacksonModule, json-common."
---

Модуль `JSON` создает эффективные реализации `JsonReader` и `JsonWriter` для классов приложения во время компиляции и без использования `Reflection` во время выполнения.
Генерация управляется аннотациями `@Json`, `@JsonReader`, `@JsonWriter` и связанными аннотациями уровня поля.

Сгенерированные кодеки — это обычные компоненты графа приложения, поэтому остальные модули Kora используют их напрямую:
преобразователи тел запросов и ответов `HTTP`-сервера и `HTTP`-клиента, преобразователи строковых параметров, а также сериализаторы и десериализаторы `Kafka` принимают `JsonReader<T>` или `JsonWriter<T>` и зарегистрированы под тегом `@Json`.
Благодаря этому один и тот же сгенерированный кодек переиспользуется во всем приложении.

Пошаговый разбор перед справочным описанием смотрите в разделе [JSON](../guides/json.md).

## Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    annotationProcessor "io.koraframework:annotation-processors" //(1)!
    implementation "io.koraframework:json-common"
    ```

    1. Процессор аннотаций создает `JsonReader` и `JsonWriter` во время компиляции. Без него кодеки не создаются, и сборка графа падает с ошибкой об отсутствующей зависимости `JsonReader`/`JsonWriter`.

    Модуль:
    ```java
    @KoraApp
    public interface Application extends JsonModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    ksp("io.koraframework:symbol-processors:2.0.0.RC1") //(1)!
    implementation("io.koraframework:json-common")
    ```

    1. Процессор `KSP` создает `JsonReader` и `JsonWriter` во время компиляции. Без него кодеки не создаются, и сборка графа падает с ошибкой об отсутствующей зависимости `JsonReader`/`JsonWriter`.

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : JsonModule
    ```

`json-common` подтягивает потоковое ядро `Jackson`, поэтому написанные вручную кодеки работают с `tools.jackson.core.JsonParser` и `tools.jackson.core.JsonGenerator`.
Сгенерированные кодеки не используют ни `Jackson` databind, ни `Reflection`.

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

        public @Nullable Dto read(String json) { //(1)!
            return this.reader.read(json);
        }

        public byte[] write(Dto dto) { //(2)!
            return this.writer.toByteArray(dto);
        }
    }
    ```

    1. `JsonReader` объявлен возвращающим значение, допускающее `null`, потому что документ верхнего уровня `null` читается как `null`.
    2. Ни `throws`, ни `try`/`catch` не нужны: ошибки `JSON` не являются проверяемыми исключениями.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyService(
        private val reader: JsonReader<Dto>,
        private val writer: JsonWriter<Dto>
    ) {

        fun read(json: String): Dto = requireNotNull(reader.read(json)) //(1)!

        fun write(dto: Dto): ByteArray = writer.toByteArray(dto) //(2)!
    }
    ```

    1. `JsonReader` объявлен возвращающим значение, допускающее `null`, потому что документ верхнего уровня `null` читается как `null`. Поэтому для non-null результата нужна явная проверка.
    2. `try`/`catch` не нужен: ошибки `JSON` не являются проверяемыми исключениями.

`JsonReader<T>` читает значение из `JsonParser`, `byte[]` (при необходимости со смещением и длиной), `String` или `InputStream`.
Все эти методы объявлены возвращающими значение, допускающее `null`.

`JsonWriter<T>` записывает значение через `JsonGenerator`, а также может сформировать документ целиком:

- `toByteArray(value)` — байты в `UTF-8`.
- `toString(value)` — компактная строка.
- `toPrettyString(value)` — форматированная строка.

Особенности поведения во время выполнения при прямом вызове кодеков:

- `read(...)` возвращает `null`, когда парсер находится на токене `JSON` `null`, поэтому документ верхнего уровня `null` десериализуется в `null`.
- Все ошибки являются наследниками `tools.jackson.core.JacksonException`, а этот класс наследуется от `RuntimeException`, поэтому ни один метод не объявляет проверяемых исключений. Смотрите раздел [Ошибки](#errors).
- Сгенерированный класс кодека находится в пакете аннотированного типа и называется `$Dto_JsonReader` / `$Dto_JsonWriter`, а для вложенных типов имена внешних классов попадают в префикс (`$Outer_Inner_JsonReader`). Внедряйте интерфейс `JsonReader<Dto>`, а не этот класс.

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

Отсутствие обязательного поля в документе и явный `null` в обязательном поле — это две разные ошибки, и обе сообщаются с именем поля и путем в `JSON`.

## Необязательные поля { #optional-fields }

===! ":fontawesome-brands-java: `Java`"

    Если поле `JSON` необязательное и может отсутствовать, используйте аннотацию `@Nullable`:

    ```java
    @Json
    public record Dto(@Nullable String field1, //(1)!
                      int field2) { }
    ```

    1. Kora использует [JSpecify](https://jspecify.dev/) `org.jspecify.annotations.Nullable`. Любая аннотация с простым именем `Nullable` также распознается.

    `@Nullable` из `JSpecify` — аннотация *уровня типа*, поэтому для вложенных типов и массивов важна ее позиция:

    ```java
    @Json
    public record Dto(java.util.@Nullable List<String> labels, //(1)!
                      byte @Nullable [] payload) { } //(2)!
    ```

    1. Аннотация относится к `List`, а не к `String`.
    2. Аннотация относится к массиву, а не к `byte`.

=== ":simple-kotlin: `Kotlin`"

    Для `Kotlin` используйте синтаксис [Kotlin Nullability](https://kotlinlang.org/docs/null-safety.html) и пометьте параметр как `nullable`:

    ```kotlin
    @Json
    data class Dto(
        val field1: String?,
        val field2: Int
    )
    ```

    `Kotlin` выражает допустимость `null` в самом типе, поэтому аннотация не нужна:

    ```kotlin
    @Json
    data class Dto(
        val labels: List<String>?,
        val payload: ByteArray?
    )
    ```

## Именование полей { #field-naming }

Если поле в `JSON` имеет имя, отличное от имени поля в классе, используйте `@JsonField`.
Она задает имя ключа в `JSON`:

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

`@JsonField` только переименовывает ключ.
Чтобы читать или записывать отдельное поле конкретным кодеком, используйте `@Mapping` — смотрите раздел [Пользовательские преобразователи полей](#custom-field-mappers).

### Стратегия именования { #naming-strategy }

Чтобы переименовать сразу все поля класса, пометьте класс аннотацией `@NamingStrategy` и укажите реализацию `NameConverter`.
Стратегия применяется и к сгенерированному `JsonReader`, и к сгенерированному `JsonWriter`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
    @NamingStrategy(SnakeCaseNameConverter.class)
    public record Dto(String stringField, //(1)!
                      Integer integerField) { }
    ```

    1. Записывается и читается как `string_field`.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    @NamingStrategy(SnakeCaseNameConverter::class)
    data class Dto(
        val stringField: String, //(1)!
        val integerField: Int
    )
    ```

    1. Записывается и читается как `string_field`.

Доступные конвертеры в пакете `io.koraframework.common.naming`:

- `NoopNameConverter` — `myFieldNAME` &#8594; `myFieldNAME`.
- `CamelCaseNameConverter` — `myFieldNAME` &#8594; `myFieldName`.
- `PascalCaseNameConverter` — `myFieldNAME` &#8594; `MyFieldName`.
- `SnakeCaseNameConverter` — `myFieldNAME` &#8594; `my_field_name`.
- `SnakeCaseUpperNameConverter` — `myFieldNAME` &#8594; `MY_FIELD_NAME`.

Поле, помеченное `@JsonField`, сохраняет имя из аннотации.
Пустая `@JsonField` без значения выводит поле из-под стратегии именования и оставляет объявленное имя поля.

## Игнорирование поля { #field-ignore }

Если поле `DTO` не должно попадать в записываемый `JSON`, используйте `@JsonSkip`.
Сгенерированный `JsonWriter` полностью пропускает такое поле.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
    public record Dto(String field1,
                      @JsonSkip @Nullable Integer field2) { } //(1)!
    ```

    1. `@JsonSkip` влияет только на запись. Сгенерированный `JsonReader` по-прежнему отображает это поле, поэтому пропущенное поле, которого нет во входных данных, должно быть [необязательным](#optional-fields).

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    data class Dto(
        val field1: String,
        @field:JsonSkip val field2: Int? //(1)!
    )
    ```

    1. `@JsonSkip` влияет только на запись. Сгенерированный `JsonReader` по-прежнему отображает это поле, поэтому пропущенное поле, которого нет во входных данных, должно быть [необязательным](#optional-fields).

Тип, который только записывается, можно пометить `@JsonWriter` вместо `@Json` — тогда читатель вообще не генерируется и пропущенное поле ни к чему не обязывает.

## Уровни сериализации { #serialization-levels }

По умолчанию поля со значением `null` не записываются. (1)
{ .annotate }

1. `IncludeType.NON_NULL` — записывать поле только в том случае, если значение не `null`.

Чтобы изменить это поведение, используйте `@JsonInclude`.
Аннотацию можно разместить не только на поле, но и на классе; в этом случае правило применяется сразу ко всем полям, а аннотация на поле имеет приоритет над аннотацией на классе.

Доступные варианты:

- `IncludeType.ALWAYS` — всегда записывать поле.
- `IncludeType.NON_NULL` — записывать поле, если значение не `null`.
- `IncludeType.NON_EMPTY` — записывать поле, если значение не `null` и не является пустой коллекцией или ассоциативным массивом.

`IncludeType.NON_EMPTY` разрешается во время компиляции, поэтому работает только тогда, когда тип поля статически известен как `Collection` или `Map`.
Для параметра типа проверку на пустоту сгенерировать невозможно, и поле ведет себя как при `IncludeType.NON_NULL`.

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

`JsonReader` и `JsonWriter` могут быть сгенерированы для классов, `record`, `data class`, `enum` и `sealed`-типов.
Для чтения требуется конкретный, не абстрактный тип и однозначно выбираемый конструктор — правила применяются в таком порядке:

1. Единственный публичный конструктор, если он один.
2. Единственный публичный конструктор, помеченный `@JsonReader`.
3. Единственный публичный конструктор, помеченный `@Json`.
4. Единственный публичный конструктор с параметрами, если такой ровно один.

Если ни одно из правил не дает единственного кандидата, компиляция завершается ошибкой с указанием типа и причины.

### Java Bean и обычные классы { #java-bean }

`@Json`, `@JsonReader` и `@JsonWriter` не ограничиваются `record` и `data class`.
Обычный класс тоже подходит: чтение подчиняется правилам выбора конструктора выше, а для записи используются методы доступа к полям.
Для каждого нестатического поля писателю нужен метод без аргументов с именем `field()` или `getField()`, возвращающий тип поля; иначе компиляция падает с подсказкой добавить метод доступа или исключить поле через `@JsonSkip`.
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

## Типы-значения { #value-types }

Тип-обертка, который должен выглядеть в `JSON` как обычное скалярное значение, а не как объект, описывается так: `@JsonReader` ставится на статический фабричный метод, а `@JsonWriter` — на метод доступа, возвращающий значение внутри обертки.
Kora генерирует кодеки, которые делегируют работу кодекам этого внутреннего типа:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record UserId(long id) {

        @JsonReader //(1)!
        public static UserId of(long value) {
            return new UserId(value);
        }

        @JsonWriter //(2)!
        public long id() {
            return id;
        }
    }
    ```

    1. `static`-фабрика ровно с одним параметром. Тип параметра определяет, какому `JsonReader` делегируется чтение.
    2. Метод экземпляра без параметров. Точно так же подходит `static`-метод, принимающий сам тип (`public static long toJson(UserId u)`).

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class UserId(val id: Long) {

        @JsonWriter //(1)!
        fun toJson(): Long = id

        companion object {

            @JsonReader //(2)!
            fun of(value: Long): UserId = UserId(value)
        }
    }
    ```

    1. Функция экземпляра без параметров. Точно так же подходит функция `companion object`, принимающая сам тип (`fun toJson(u: UserId): Long`).
    2. Функция `companion object` ровно с одним параметром. Тип параметра определяет, какому `JsonReader` делегируется чтение.

Поле типа `UserId` тогда записывается как `42`, а не как `{"id":42}`, а `null` записывается как `null`.
Это эквивалент `@JsonValue` и `@JsonCreator(mode = DELEGATING)` из `Jackson`.

Ограничения, проверяемые во время компиляции:

- Не более одного фабричного метода `@JsonReader` и не более одного метода `@JsonWriter` на тип.
- Фабричный метод должен быть `public static`, принимать ровно один параметр и возвращать сам тип.
- У типа не может быть одновременно фабричного метода `@JsonReader` и конструктора с `@JsonReader`/`@Json`.
- Метод `@JsonWriter` должен быть `public` и возвращать значение; `static`-вариант принимает сам тип единственным параметром, вариант экземпляра — ни одного.
- Для внутреннего типа в графе должен быть `JsonReader` или `JsonWriter`, что верно для любого [поддерживаемого типа](#supported-types).

## Обертка JsonNullable { #jsonnullable-wrapper }

Если при чтении `JSON` необходимо отличать отсутствующее поле от поля со значением `null`, используйте `JsonNullable`.
Основные состояния и фабричные методы:

- `JsonNullable.undefined()` — поле отсутствует в `JSON`.
- `JsonNullable.nullValue()` — поле присутствует и содержит `null`.
- `JsonNullable.of(value)` — поле присутствует и содержит значение; аргумент не должен быть `null`.
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

Поскольку `value()` выбрасывает `NullPointerException` при `undefined()`, всегда защищайте доступ проверкой `isDefined()` (или проверяйте `isNull()`) перед вызовом.

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

Взаимодействие с [уровнями сериализации](#serialization-levels): `IncludeType.ALWAYS` и `IncludeType.NON_NULL` **не** меняют способ записи `JsonNullable` — всегда действуют его собственные правила, поэтому поле `undefined()` опускается, а поле `nullValue()` при обоих уровнях записывается как `null`.
Единственный уровень, который добавляет здесь дополнительное поведение, — `IncludeType.NON_EMPTY`, и только если обёрнутый тип статически является `Collection` или `Map`: тогда поле `nullValue()` и поле с пустой коллекцией или картой также опускаются.

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

        @Json
        @JsonDiscriminatorValue("created")
        record Created(String id) implements Event {}

        @Json
        @JsonDiscriminatorValue({"deleted", "removed"}) //(1)!
        record Deleted(String id, boolean permanent) implements Event {}
    }
    ```

    1. Одному подклассу можно сопоставить несколько значений дискриминатора. При записи используется первое значение.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    @JsonDiscriminatorField("type")
    sealed interface Event {

        @Json
        @JsonDiscriminatorValue("created")
        data class Created(val id: String) : Event

        @Json
        @JsonDiscriminatorValue("deleted", "removed") //(1)!
        data class Deleted(val id: String, val permanent: Boolean) : Event
    }
    ```

    1. Одному подклассу можно сопоставить несколько значений дискриминатора. При записи используется первое значение.

Сам `sealed`-класс или интерфейс получает общий `JsonReader` и `JsonWriter` — именно их приложение и внедряет, чтобы прочитать или записать любой подтип.
При этом у каждого конкретного подкласса должен быть собственный кодек, потому что сгенерированный кодек `sealed`-типа принимает кодеки подклассов как зависимости.
Проще всего это обеспечить, пометив каждый подкласс аннотацией `@Json` (либо `@JsonReader`/`@JsonWriter`).
Sealed-абстрактные классы и вложенные `sealed`-подынтерфейсы также поддерживаются — иерархия разворачивается до конкретных подклассов.

Правила, относящиеся к самому дискриминатору:

- `@JsonDiscriminatorValue` необязательна. Без нее значением дискриминатора подкласса становится его простое имя класса.
- Поле-дискриминатор может находиться в любом месте объекта; читатель буферизует токены, которые приходится пропустить.
- При записи дискриминатор добавляется автоматически, если только подкласс уже не объявляет поле с таким именем в `JSON` — в этом случае значение берется из самого поля.
- `@JsonDiscriminatorField` принимает еще и `defaultValue` — дискриминатор, который используется, когда поле отсутствует в документе. Без него отсутствие дискриминатора считается ошибкой.

Приведенный ниже `JSON`-объект читается в класс `Created`:
```json
{
    "type": "created",
    "id": "1"
}
```

Поддерживаются обобщенные (`generic`) типы `DTO`, включая обобщенные `sealed`-иерархии.
Кодек для каждого конкретного аргумента типа разрешается из графа, как и для любого другого типа поля:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
    @JsonDiscriminatorField("@type")
    public sealed interface Response<T> {

        @Json
        @JsonDiscriminatorValue("ok")
        record Ok<T>(T data) implements Response<T> {}

        @Json
        @JsonDiscriminatorValue("fail")
        record Fail<T>(String error) implements Response<T> {}
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    @JsonDiscriminatorField("@type")
    sealed interface Response<T> {

        @Json
        @JsonDiscriminatorValue("ok")
        data class Ok<T>(val data: T) : Response<T>

        @Json
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

Соответствие значений `JSON` константам строится один раз при создании кодека, поэтому чтение `enum` — это один поиск по ассоциативному массиву.
Значение `JSON`, не совпадающее ни с одной константой, отвергается с ошибкой, в которой перечислены допустимые значения.

## RawJson { #raw-json }

`RawJson` используется, когда в объект нужно включить уже готовый фрагмент `JSON`, не сериализуя его повторно.
При записи `RawJson` передается в выходной `JSON` как есть, поэтому значение должно быть корректным фрагментом `JSON`.

`RawJson` — тип **только для записи**: модуль предоставляет `JsonWriter<RawJson>`, но не предоставляет читателя, поэтому содержащий его `DTO` помечается `@JsonWriter`, а не `@Json`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @JsonWriter
    public record Dto(String id, RawJson payload) { }

    var dto = new Dto("1", new RawJson("{\"status\":\"ok\"}"));
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @JsonWriter
    data class Dto(val id: String, val payload: RawJson)

    val dto = Dto("1", RawJson("""{"status":"ok"}"""))
    ```

`RawJson` принимает либо `String`, либо `byte[]` и хранит значение как байты в `UTF-8`.
Так как содержимое уже закодировано, оно записывается без кавычек; значение, которое требует экранирования как строка `JSON`, нужно передавать обычным полем типа `String`.

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

Здесь `HexReader` реализует `JsonReader<Integer>` (`JsonReader<Int>` в `Kotlin`), а `HexWriter` — соответствующий `JsonWriter`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class HexWriter implements JsonWriter<Integer> { //(1)!

        @Override
        public void write(JsonGenerator generator, Integer value) {
            generator.writeString(Integer.toHexString(value));
        }
    }

    public final class HexReader implements JsonReader<Integer> {

        @Override
        public Integer read(JsonParser parser) {
            if (parser.currentToken() != JsonToken.VALUE_STRING) {
                throw new StreamReadException(parser, "Expected hexadecimal string");
            }
            return Integer.parseInt(parser.getValueAsString(), 16);
        }
    }
    ```

    1. `final`-преобразователь без зависимостей в конструкторе создается самим сгенерированным кодом и **не** должен быть `@Component`. Преобразователь, у которого есть зависимости в конструкторе, обязан быть компонентом графа — смотрите раздел [Компоненты](container.md#components).

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class HexWriter : JsonWriter<Int> { //(1)!

        override fun write(generator: JsonGenerator, value: Int?) {
            generator.writeString(value!!.toString(16))
        }
    }

    class HexReader : JsonReader<Int> {

        override fun read(parser: JsonParser): Int {
            if (parser.currentToken() != JsonToken.VALUE_STRING) {
                throw StreamReadException(parser, "Expected hexadecimal string")
            }
            return parser.valueAsString.toInt(16)
        }
    }
    ```

    1. Преобразователь без зависимостей в конструкторе (в `Kotlin` классы `final` по умолчанию) создается самим сгенерированным кодом и **не** должен быть `@Component`. Преобразователь, у которого есть зависимости в конструкторе, обязан быть компонентом графа — смотрите раздел [Компоненты](container.md#components).

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

Что стоит знать об этом списке:

- `byte[]` записывается и читается как строка в `Base64`.
- У `RawJson` есть только писатель, а у `SortedSet<T>` — только читатель.
- `Enum` требует аннотации `@Json` на самом типе перечисления, смотрите раздел [Перечисления](#enum).
- `Object` читает `JSON`-объект в `LinkedHashMap`, массив — в `ArrayList`, целое число — в `BigInteger`, а дробное — в `Double`.
- Типы даты и времени используют соответствующие форматы `ISO`; `Month` и `DayOfWeek` записываются по имени, а читаются как по имени, так и по числу.
- Ключи `Map` должны быть строками.

### Пользовательские типы { #custom-types }

Если необходимо читать или записывать пользовательский тип, зарегистрируйте пользовательскую [фабрику](container.md#method-factory) для `JsonReader` или `JsonWriter`.

Пример регистрации пользовательского `JsonWriter`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {

        default JsonWriter<ZoneOffset> zoneOffsetJsonWriter() {
            return (generator, value) -> {
                if (value == null) {
                    generator.writeNull();
                } else {
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
                if (value == null) {
                    generator.writeNull()
                } else {
                    generator.writeString(value.id)
                }
            }
        }
    }
    ```

Пример регистрации пользовательского `JsonReader`.
Читатель переключается по текущему токену парсера, возвращает `null` для `JSON` `null`, читает ожидаемый токен и выбрасывает `StreamReadException` для всего остального:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application {

        default JsonReader<ZoneOffset> zoneOffsetJsonReader() {
            return parser -> switch (parser.currentToken()) {
                case VALUE_NULL -> null;
                case VALUE_STRING -> ZoneOffset.of(parser.getValueAsString());
                default -> throw new StreamReadException(parser,
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
                else -> throw StreamReadException(parser,
                    "Expecting VALUE_STRING token, got ${parser.currentToken()}")
            }
        }
    }
    ```

Пользовательский `JsonReader<T>` или `JsonWriter<T>` — это обычный компонент графа.
После регистрации сгенерированные кодеки автоматически подхватывают его везде, где встречается поле типа `T`, а также его можно закрепить за отдельным полем через `@Mapping` (см. [Пользовательские преобразователи полей](#custom-field-mappers)).

## Ошибки { #errors }

Все, что кодек выбрасывает во время выполнения, — это наследники `tools.jackson.core.JacksonException`, а этот класс наследуется от `RuntimeException`.
Ни один метод `JsonReader` или `JsonWriter` не объявляет проверяемых исключений, поэтому вызывающему коду не нужны ни `throws`, ни `try`/`catch`, если он не собирается обрабатывать ошибку.

Ошибки чтения сообщаются как `tools.jackson.core.exc.StreamReadException`.
Сгенерированные читатели формируют сообщения, в которых указаны тип, поле и путь в `JSON` до проблемного значения:

```text
Failed to read json Dto: missing required field(s): field_1 (at <root>)
Failed to read json Dto.field4: required field must not be null (at <root>)
Failed to read json Dto.field2: expected an integer number, but got a string "abc" (at /field2)
```

У sealed-иерархий и перечислений есть свои сообщения, и оба перечисляют допустимые значения:

```text
Failed to read json Event: missing required discriminator field "type", expected one of [created, deleted, removed] (at <root>)
Failed to read json Event: unknown discriminator value "updated" for field "type", expected one of [created, deleted, removed] (at <root>)
Failed to read json enum: expected one of [1, 2], but got "3" (at /status)
```

Когда кодек используется через другой модуль Kora, исключение транслируется на границе: декларативный контроллер [HTTP-сервера](http-server.md) превращает неразобранное тело или параметр в ответ `400`, а продюсер `Kafka` заворачивает ошибку сериализации в `SerializationException`.

Проблемы времени компиляции процессор Kora сообщает в той же структуре — тип, проблема, подсказка и способ исправления.
Чаще всего это отсутствие метода доступа для записываемого поля, абстрактный тип или интерфейс, не являющийся поддерживаемой `sealed`-иерархией, и неоднозначный конструктор для читателя.

## Jackson { #jackson }

Если для чтения и записи `JSON` вместо сгенерированных во время компиляции кодеков нужно использовать `Jackson` databind, применяйте `JacksonModule`.
Он предоставляет помеченные тегом `@Json` преобразователи для `HTTP`-клиента и `HTTP`-сервера, и поскольку это обычные компоненты, а преобразователи на основе кодеков — компоненты по умолчанию, приоритет получают преобразователи `Jackson` — смотрите раздел [Фабрика по умолчанию](container.md#default-factory).

`JacksonModule` покрывает ровно такой набор преобразователей:

- `HttpServerRequestMapper<T>` и `HttpServerResponseMapper<T>`.
- `HttpClientRequestMapper<T>`, `HttpClientResponseMapper<T>` и `HttpClientResponseMapper<HttpResponseEntity<T>>`.

Все остальное — строковые параметры, `Kafka` и любое прямое внедрение `JsonReader`/`JsonWriter` — продолжает работать на сгенерированных кодеках.

Каждый преобразователь `JacksonModule` зависит от компонента `ObjectMapper`, поэтому в графе **обязательно** должна присутствовать [фабрика](container.md#method-factory), предоставляющая `ObjectMapper`. Без нее граф не соберется.

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    annotationProcessor "io.koraframework:annotation-processors"
    implementation "io.koraframework:jackson-module"
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
    ksp("io.koraframework:symbol-processors:2.0.0.RC1")
    implementation("io.koraframework:jackson-module")
    ```

    Модуль и фабрика `ObjectMapper`:
    ```kotlin
    @KoraApp
    interface Application : JacksonModule {

        fun objectMapper(): ObjectMapper = ObjectMapper() //(1)!
    }
    ```

    1. Требуется всем преобразователям `JacksonModule`; настройте его по необходимости (модули, возможности и так далее).

`ObjectMapper` здесь — это `tools.jackson.databind.ObjectMapper`; `jackson-module` подтягивает `Jackson` databind транзитивно.

Показанный выше процессор Kora позволяет `@Json`, `@JsonReader` и `@JsonWriter` по-прежнему генерировать кодеки, так что сгенерированная и `Jackson`-сериализация могут сосуществовать (например, `Jackson` для `HTTP` и сгенерированные кодеки для [Kafka](kafka.md)).
