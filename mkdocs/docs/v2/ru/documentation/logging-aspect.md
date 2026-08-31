---
description: "Explains Kora logging aspects for argument and result logging, selective logging, structured JSON values, value masking, MDC enrichment and supported signatures. Use when working with @Log, @Log.in, @Log.out, @Log.result, @Log.off, @Mask, @Mdc, MaskingRules, MaskingStrategy, StructuredArgument, StructuredArgumentMapper, MDC."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora logging aspects for argument and result logging, selective logging, structured JSON values, value masking, MDC enrichment and supported signatures; key triggers include @Log, @Log.in, @Log.out, @Log.result, @Log.off, @Mask, @Mdc, MaskingRules, MaskingStrategy, MaskingFull, MaskingKeepFirst, MaskingKeepLast, StructuredArgument, StructuredArgumentMapper, MDC."
---

Модуль декларативного логирования позволяет описывать логирование метода с помощью аннотаций `@Log`, `@Mask` и `@Mdc`.
На этапе компиляции Kora создает аспект-обертку для метода; обертка логирует вход в метод, выход из метода, результат, ошибку и значения `MDC` без ручного кода в бизнес-логике.
Это удобно для единообразной диагностики вызовов, особенно когда нужно быстро понять, какой метод был вызван, с какими аргументами и как он завершился.

Пошаговый разбор перед справочным описанием смотрите в разделе [Наблюдаемость](../guides/observability.md).

## Подключение { #dependency }

Аннотации и вспомогательные классы предоставляются зависимостью `logging-common`.
Обычно она уже приходит через другие модули Kora или через [Logback](logging-slf4j.md#logback), но при использовании аннотаций напрямую зависимость можно добавить явно:

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:logging-common"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends LoggingModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:logging-common")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : LoggingModule
    ```

`LogbackModule` уже наследует `LoggingModule`, поэтому приложению с [Logback](logging-slf4j.md#logback) объявлять `LoggingModule` отдельно не нужно.

Для генерации аспектов также должны быть подключены общие [обработчики аннотаций](general.md#annotation-processor) или [`KSP`-обработчики](general.md#ksp).
В обычном приложении Kora они уже подключены как часть базовой настройки проекта.

## Логирование { #logging }

Логирование метода настраивается комбинациями аннотаций:

- `@Log` - логирует вход и выход метода (по умолчанию: `INFO`).
- `@Log.in` - логирует только вход в метод (по умолчанию: `INFO`).
- `@Log.out` - логирует только выход из метода (по умолчанию: `INFO`).
- `@Log.result` - задает уровень, начиная с которого в лог добавляется значение результата (по умолчанию: `DEBUG`).
- `@Log.off` - отключает логирование результата метода или отдельного параметра.
- `@Log(Level)` на параметре - задает уровень, начиная с которого параметр попадает в структурированные данные (по умолчанию: `DEBUG` для параметра без отдельной аннотации).

Уровень — это `org.slf4j.event.Level`.

Само событие входа или выхода пишется на уровне, указанном в `@Log`, `@Log.in` или `@Log.out`.
Значения аргументов и результата добавляются в структурированные данные только если включен соответствующий уровень детализации.
Уровень детализации никогда не бывает *менее* подробным, чем уровень самого события: если событие пишется на `DEBUG`, то параметр, объявленный как `@Log(Level.INFO)`, все равно попадет в лог на `DEBUG` — описывать событие, которое не пишется, смысла нет.
Какой уровень детализации активен, зависит от эффективного уровня логгера, настроенного через `logging.levels` — смотрите [настройку уровней логирования](logging-slf4j.md#configuration).

Значения пишутся в структурированный маркер `data`; энкодер `ConsoleTextRecordEncoder` из [Logback](logging-slf4j.md#logback) выводит его отдельной строкой после сообщения.

### Аргументов { #argument }

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Log.in
    public String doWork(@Log.off String strParam, int numParam) {
        return "testResult";
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Log.`in`
    fun doWork(@Log.off strParam: String?, numParam: Int): String {
        return "testResult"
    }
    ```

<table>
    <thead>
        <th>Уровень логирования</th>
        <th>Лог</th>
    </thead>
    <tr>
        <td>DEBUG</td>
        <td>
            <p>INFO&nbsp;&nbsp;[main] io.koraframework.example.Example.doWork - &gt;</p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp;data={"numParam":"4"}</p>
        </td>
    </tr>
    <tr>
        <td>TRACE</td>
        <td>
            <p>INFO&nbsp;&nbsp;[main] io.koraframework.example.Example.doWork - &gt;</p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp;data={"numParam":"4"}</p>
        </td>
    </tr>
    <tr>
        <td>INFO</td>
        <td>
            <p>INFO&nbsp;&nbsp;[main] io.koraframework.example.Example.doWork - &gt;</p>
        </td>
    </tr>
</table>

Аргументы, для которых не задан отдельный конвертер, пишутся через `String.valueOf(...)`, поэтому в `JSON` они всегда выглядят как строки.

### Результата { #result }

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Log.out
    public String doWork(String strParam, int numParam) {
        return "testResult";
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Log.out
    fun doWork(strParam: String, numParam: Int): String {
        return "testResult"
    }
    ```

<table>
    <thead>
        <th>Уровень логирования</th>
        <th>Лог</th>
    </thead>
    <tr>
        <td>DEBUG</td>
        <td>
            <p>INFO&nbsp;&nbsp;[main] io.koraframework.example.Example.doWork - &lt;</p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp;data={"out":"testResult"}</p>
        </td>
    </tr>
    <tr>
        <td>TRACE</td>
        <td>
            <p>INFO&nbsp;&nbsp;[main] io.koraframework.example.Example.doWork - &lt;</p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp;data={"out":"testResult"}</p>
        </td>
    </tr>
    <tr>
        <td>INFO</td>
        <td>
            <p>INFO&nbsp;&nbsp;[main] io.koraframework.example.Example.doWork - &lt;</p>
        </td>
    </tr>
</table>

### Аргументов и результата { #argument-and-result }

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Log
    public String doWork(String strParam, int numParam) {
        return "testResult";
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Log
    fun doWork(strParam: String, numParam: Int): String {
        return "testResult"
    }
    ```

<table>
    <thead>
        <th>Уровень логирования</th>
        <th>Лог</th>
    </thead>
    <tr>
        <td>DEBUG</td>
        <td>
            <p>INFO&nbsp;&nbsp;[main] io.koraframework.example.Example.doWork - &gt;</p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp;data={"strParam":"s","numParam":"4"}</p>
            <p>INFO&nbsp;&nbsp;[main] io.koraframework.example.Example.doWork - &lt;</p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp;data={"out":"testResult"}</p>
        </td>
    </tr>
    <tr>
        <td>TRACE</td>
        <td>
            <p>INFO&nbsp;&nbsp;[main] io.koraframework.example.Example.doWork - &gt;</p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp;data={"strParam":"s","numParam":"4"}</p>
            <p>INFO&nbsp;&nbsp;[main] io.koraframework.example.Example.doWork - &lt;</p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp;data={"out":"testResult"}</p>
        </td>
    </tr>
    <tr>
        <td>INFO</td>
        <td>
            <p>INFO&nbsp;&nbsp;[main] io.koraframework.example.Example.doWork - &gt;</p>
            <p>INFO&nbsp;&nbsp;[main] io.koraframework.example.Example.doWork - &lt;</p>
        </td>
    </tr>
</table>

Если метод завершается ошибкой, аспект пишет выход из метода на уровне `WARN` с данными об ошибке `errorType` и `errorMessage`, после чего пробрасывает исключение дальше без изменений.
При включенном `DEBUG` в лог также передается объект исключения, поэтому печатается стектрейс.
Логирование ошибки выполняется для любой из аннотаций `@Log`, `@Log.in` и `@Log.out` — метод, помеченный только `@Log.in`, тоже сообщает о своих падениях.

```
WARN  [main] io.koraframework.example.Example.doWork - <
    data={"errorType":"java.lang.IllegalStateException","errorMessage":"OPS"}
```

### Выборочное логирование { #selective-logging }

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Log.out
    @Log.off
    public String doWork(String strParam, int numParam) {
        return "testResult";
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Log.out
    @Log.off
    fun doWork(strParam: String, numParam: Int): String {
        return "testResult"
    }
    ```

<table>
    <thead>
        <th>Уровень логирования</th>
        <th>Лог</th>
    </thead>
    <tr>
        <td>TRACE, DEBUG</td>
        <td>
            <p>INFO&nbsp;&nbsp;[main] io.koraframework.example.Example.doWork - &lt;</p>
        </td>
    </tr>
    <tr>
        <td>INFO</td>
        <td>
            <p>INFO&nbsp;&nbsp;[main] io.koraframework.example.Example.doWork - &lt;</p>
        </td>
    </tr>
</table>

В этом примере `@Log.off` на методе отключает запись значения результата, но не отключает само событие выхода из метода.
Чтобы исключить из лога отдельный аргумент, `@Log.off` ставится на параметр.

Уровень детализации параметров можно задавать отдельно:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Log.in
    public void doWork(@Log(Level.INFO) String id, @Log(Level.TRACE) String payload) { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Log.`in`
    fun doWork(@Log(Level.INFO) id: String, @Log(Level.TRACE) payload: String) { }
    ```

При уровне `INFO` в структурированные данные попадет только `id`, а `payload` появится только при включенном `TRACE`.

Значение результата можно вывести уже на уровне `INFO`, если явно указать `@Log.result(Level.INFO)`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Log.out
    @Log.result(Level.INFO)
    public String doWork() {
        return "testResult";
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Log.out
    @Log.result(Level.INFO)
    fun doWork(): String {
        return "testResult"
    }
    ```

### Структурированный параметр { #structured-parameter }

Если строковое представление параметра не подходит для лога, пометьте параметр аннотацией `@Json`.
Тогда аспект возьмет `JSON`-писатель, сгенерированный для типа [модулем JSON](json.md), и запишет значение вложенным `JSON`-объектом, а не строкой.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Json
    public record Entity(String name, String code) { }

    @Log.in
    public String doWork(@Json Entity entity) {
        return "testResult";
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Json
    data class Entity(val name: String, val code: String)

    @Log.`in`
    fun doWork(@Json entity: Entity): String {
        return "testResult"
    }
    ```

<table>
    <thead>
        <th>Уровень логирования</th>
        <th>Лог</th>
    </thead>
    <tr>
        <td>DEBUG, TRACE</td>
        <td>
            <p>INFO&nbsp;&nbsp;[main] io.koraframework.example.Example.doWork - &gt;</p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp;data={"entity":{"name":"Bob","code":"42"}}</p>
        </td>
    </tr>
    <tr>
        <td>INFO</td>
        <td>
            <p>INFO&nbsp;&nbsp;[main] io.koraframework.example.Example.doWork - &gt;</p>
        </td>
    </tr>
</table>

`@Json` ставится именно на логируемый элемент — на параметр либо на метод, если структурированным должен быть *результат*:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Log.out
    @Json
    public Entity doWork() {
        return new Entity("Bob", "42");
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Log.out
    @Json
    fun doWork(): Entity {
        return Entity("Bob", "42")
    }
    ```

Для значений, которые формируются в месте вызова, а не приходят аргументами метода, интерфейс `StructuredArgument` предоставляет статические фабрики:

- `arg(fieldName, value)` — создает структурированное значение; перегрузки принимают `String`, `Integer`, `Long`, `Boolean`, `Map<String, String>`, `JsonWriter<T>` вместе со значением или произвольный `StructuredArgumentWriter`.
- `marker(fieldName, value)` — создает `org.slf4j.Marker` с тем же набором перегрузок, чтобы прикрепить структурированные данные к одной записи лога.

===! ":fontawesome-brands-java: `Java`"

    ```java
    // structured value written into MDC
    MDC.put("orderId", gen -> gen.writeString(orderId));

    // or as an SLF4J marker on a single log line
    log.info(StructuredArgument.marker("orderId", orderId), "order accepted");
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // structured value written into MDC
    MDC.put("orderId") { gen -> gen.writeString(orderId) }

    // or as an SLF4J marker on a single log line
    log.info(StructuredArgument.marker("orderId", orderId), "order accepted")
    ```

Любой `StructuredArgumentWriter` можно отрендерить вручную методом `writeToString()` — это удобно в тестах.

### Конвертация параметров { #parameter-conversion }

Если тип параметра нельзя пометить `@Json` или представление в логе должно отличаться от представления на проводе, опишите внешний `StructuredArgumentMapper` и укажите его через `@Mapping` у нужного аргумента.
Маппер получает исходное значение параметра и пишет структурированное значение в `JsonGenerator`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record Entity(String name, String code) { }

    public final class EntityLogMapper implements StructuredArgumentMapper<Entity> {

        @Override
        public void write(JsonGenerator gen, Entity value) {
            gen.writeString(value.name());
        }
    }

    @Log.in
    public String doWork(@Mapping(EntityLogMapper.class) Entity entity) {
        return "testResult";
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class Entity(val name: String, val code: String)

    class EntityLogMapper : StructuredArgumentMapper<Entity> {

        override fun write(gen: JsonGenerator, value: Entity) = gen.writeString(value.name)
    }

    @Log.`in`
    fun doWork(@Mapping(EntityLogMapper::class) entity: Entity): String {
        return "testResult"
    }
    ```

<table>
    <thead>
        <th>Уровень логирования</th>
        <th>Лог</th>
    </thead>
    <tr>
        <td>DEBUG, TRACE</td>
        <td>
            <p>INFO&nbsp;&nbsp;[main] io.koraframework.example.Example.doWork - &gt;</p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp;data={"entity":"Bob"}</p>
        </td>
    </tr>
    <tr>
        <td>INFO</td>
        <td>
            <p>INFO&nbsp;&nbsp;[main] io.koraframework.example.Example.doWork - &gt;</p>
        </td>
    </tr>
</table>

`JsonGenerator` здесь — это `tools.jackson.core.JsonGenerator`; его методы записи бросают непроверяемое `JacksonException`, поэтому методы мапперов не объявляют проверяемых исключений.

Тот же `@Mapping` можно повесить на сам метод, чтобы сконвертировать *результат*.
Обобщенный маппер вида `MyMapper<T> implements StructuredArgumentMapper<T>` тоже поддерживается — аспект параметризует его типом значения.

!!! warning "Маппер и контейнер зависимостей"

    Маппер **с** зависимостями в конструкторе должен быть компонентом графа и помечаться `@Component`.
    Маппер **без** зависимостей помечать `@Component` **нельзя** — Kora создает его сама, а лишний компонент приводит к ошибке сборки графа `Multiple components match`.

### Маскирование { #masking }

Чувствительные значения можно замаскировать до попадания в лог с помощью аннотации `@Mask`.
Маскирование работает поверх `JSON`-представления значения: вывод писателя пропускается через делегирующий генератор, который подменяет совпавшие поля значением от `MaskingStrategy`.

У `@Mask` есть единственный атрибут `value()` — реализация `MaskingStrategy` (по умолчанию: `MaskingFull.class`). Аннотацию можно ставить на:

- класс или запись (не абстрактные) — включает генерацию правил маскирования для типа и задает стратегию по умолчанию для его полей;
- поле или компонент записи — помечает соответствующее поле `JSON` как маскируемое;
- логируемый параметр или метод — указывает аспекту `@Log` писать значение через маскирующий маппер.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Mask(MaskingKeepFirst.class)
    @Json
    public record Credentials(@Mask String password,
                              @Mask(MaskingKeepLast.class) String cardNumber,
                              String login) { }

    @Mask
    @Json
    public record User(String name, Credentials credentials) { }

    @Log.in
    public void register(@Mask @Json User user) { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Mask(MaskingKeepFirst::class)
    @Json
    data class Credentials(@Mask val password: String,
                           @Mask(MaskingKeepLast::class) val cardNumber: String,
                           val login: String)

    @Mask
    @Json
    data class User(val name: String, val credentials: Credentials)

    @Log.`in`
    fun register(@Mask @Json user: User) { }
    ```

```
INFO  [main] io.koraframework.example.Example.register - >
    data={"user":{"name":"Bob","credentials":{"password":"s3cr***","cardNumber":"***3456","login":"bob"}}}
```

Маскируются только поля, помеченные `@Mask` — `@Mask` на типе не маскирует всё подряд, а объявляет, что для этого типа нужно сгенерировать правила, и задает стратегию по умолчанию для его маскируемых полей.
Стратегия поля выбирается в таком порядке: стратегия, указанная на самом поле, затем указанная на объемлющем типе, затем `MaskingFull`.
Имена полей берутся из `JSON`-представления, поэтому переименования `@JsonField` и стратегии именования учитываются, а поля `@JsonSkip` игнорируются.
Вложенные типы, помеченные `@Json` или `@Mask`, обходятся рекурсивно, в том числе через коллекции, массивы и словари, поэтому `@Mask` на листовом поле действует везде, куда до этого поля можно добраться от логируемого объекта.

`@Mask` и `@Json` на логируемом элементе независимы:

- `@Mask @Json` - значение пишется вложенным `JSON`-объектом с подмененными полями (рекомендуемый вариант).
- `@Mask` без `@Json` - значение пишется одной `JSON`-строкой, внутри которой лежит замаскированный документ.

#### Стратегии маскирования { #masking-strategies }

Стратегия — это реализация `MaskingStrategy` с единственным методом `String mask(Object value)`.
В модуле есть три реализации, и все они зарегистрированы как компоненты по умолчанию с настройками по умолчанию:

- `MaskingFull` - заменяет значение целиком строкой-заменителем (по умолчанию: `***`).
- `MaskingKeepFirst` - оставляет первые `keep` символов (по умолчанию: `4`) и дописывает заменитель (по умолчанию: `***`). Если значение не длиннее `keep`, пишется только заменитель.
- `MaskingKeepLast` - пишет заменитель (по умолчанию: `***`) и дописывает последние `keep` символов (по умолчанию: `4`).

Чтобы изменить строку-заменитель или количество сохраняемых символов, объявите стратегию своим компонентом — он перекроет компонент по умолчанию:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends LoggingModule {

        default MaskingKeepLast maskingKeepLast() {
            return new MaskingKeepLast("###", 2);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : LoggingModule {

        fun maskingKeepLast(): MaskingKeepLast = MaskingKeepLast("###", 2)
    }
    ```

Собственная стратегия — это обычный класс, реализующий `MaskingStrategy`.
Сгенерированные правила получают его из контейнера зависимостей, поэтому действует то же правило, что и для мапперов: помечайте класс `@Component`, только если у него есть зависимости в конструкторе.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class EmailMaskingStrategy implements MaskingStrategy {

        @Override
        public String mask(Object value) {
            var email = String.valueOf(value);
            var at = email.indexOf('@');
            return at > 0 ? "***" + email.substring(at) : "***";
        }
    }

    @Mask
    @Json
    public record User(String name, @Mask(EmailMaskingStrategy.class) String email) { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class EmailMaskingStrategy : MaskingStrategy {

        override fun mask(value: Any?): String {
            val email = value.toString()
            val at = email.indexOf('@')
            return if (at > 0) "***" + email.substring(at) else "***"
        }
    }

    @Mask
    @Json
    data class User(val name: String, @Mask(EmailMaskingStrategy::class) val email: String)
    ```

В `mask(...)` приходит исходное значение `JSON`: `String`, `Boolean`, `Number`, `BigInteger`, `BigDecimal` либо `byte[]` для бинарных значений.
Значения `null` не маскируются и метод для них не вызывается, ключи словарей как значения тоже не маскируются.

#### Правила маскирования { #masking-rules }

Для каждого типа с аннотацией `@Mask` обработчик генерирует модуль, который поставляет компонент `MaskingRules<T>` с описанием того, какие поля `JSON` и какой стратегией подменять.
Сгенерированный модуль подхватывается контейнером зависимостей автоматически, регистрировать его вручную не нужно.

Когда правила нужно собрать динамически — например, для типа, исходники которого вам не принадлежат — унаследуйтесь от `MaskingRules<T>` и укажите класс на логируемом элементе через `@Mapping`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class UserMaskingRules extends MaskingRules<User> {

        public UserMaskingRules() {
            super(User.class, Map.of("password", new MaskingFull(),
                                     "credentials.cardNumber", new MaskingKeepLast()));
        }
    }

    @Log.in
    public void register(@Mask @Json @Mapping(UserMaskingRules.class) User user) { }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class UserMaskingRules : MaskingRules<User>(
        User::class.java,
        mapOf("password" to MaskingFull(),
              "credentials.cardNumber" to MaskingKeepLast())
    )

    @Log.`in`
    fun register(@Mask @Json @Mapping(UserMaskingRules::class) user: User) { }
    ```

Ключ правила — это либо имя поля, либо путь от корня логируемого объекта через точку:

- `password` - маскирует любое поле `JSON` с именем `password`, где бы оно ни встретилось;
- `credentials.cardNumber` - маскирует `cardNumber` только тогда, когда до него добрались через поле `credentials`;
- `payments.*.cardNumber` - `*` соответствует ровно одному динамическому сегменту пути, что как раз дают ключи словарей.

Те же правила можно собрать билдером: `MaskingRules.builder(User.class).mask("password", new MaskingFull()).build()`.

### MDC (Mapped Diagnostic Context) { #mdc-mapped-diagnostic-context }

Аннотация `@Mdc` добавляет пары ключ-значение в `MDC` (`Mapped Diagnostic Context`).
`MDC` хранит контекст выполнения и позволяет добавлять его в сообщения лога: например, идентификаторы запроса, пользователя или операции.

Аннотацию можно применять к методам и параметрам методов.
На методах поддерживается повторное использование `@Mdc`.
Значения, добавленные без `global = true`, восстанавливаются после выполнения метода.

**Параметры аннотации `@Mdc`:**

- `key()` - ключ записи `MDC` (по умолчанию: `""`).
- `value()` - значение записи `MDC` (по умолчанию: `""`).
- `global()` - оставить значение в `MDC` после выхода из метода (по умолчанию: `false`).

Для `@Mdc` на методе требуются непустые `key` и `value`, иначе компиляция завершится ошибкой.
Для `@Mdc` на параметре ключ берется из `key`, затем из `value`; если оба значения пустые, используется имя параметра.
Значением записи становится значение параметра.

Параметры типов `String`, `Integer`/`Int`, `Long`, `Boolean` и `StructuredArgumentWriter` сохраняют свой тип в `JSON`, остальные примитивы пишутся через `String.valueOf(...)`, а любой другой тип — через `toString()`.
Если значение непримитивного параметра равно `null`, запись в `MDC` просто не добавляется.

#### Аннотация параметра { #parameter-annotation }

===! ":fontawesome-brands-java: `Java`"

    ```java
    public String test(@Mdc String s) {
        return "1";
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun test(@Mdc s: String): String {
        return "1"
    }
    ```

В этом случае ключ `MDC` совпадает с именем параметра `s`, а значением становится значение параметра.

#### Аннотация параметра с ключом { #parameter-annotation-with-key }

===! ":fontawesome-brands-java: `Java`"

    ```java
    public String test(@Mdc(key = "123") String s) {
        return "1";
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun test(@Mdc(key = "123") s: String): String {
        return "1"
    }
    ```

Здесь ключ `MDC` — `123`, а значение — значение параметра `s`.

#### Аннотация метода { #method-use }

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Mdc(key = "key1", value = "value2")
    public String test(String s) {
        return "1";
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Mdc(key = "key1", value = "value2")
    fun test(s: String): String {
        return "1"
    }
    ```

В этом примере перед вызовом метода в `MDC` добавляется запись `key1=value2`.
После завершения метода предыдущее значение `key1` восстанавливается.

#### Комбинированное { #combined }

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Mdc(key = "key", value = "value", global = true)
    @Mdc(key = "key1", value = "value2")
    public String test(@Mdc(key = "123") String s) {
        return "1";
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Mdc(key = "key", value = "value", global = true)
    @Mdc(key = "key1", value = "value2")
    fun test(@Mdc(key = "123") s: String): String {
        return "1"
    }
    ```

В этом примере к методу применены две аннотации `@Mdc`, и одна — к параметру.
Запись `key=value` остается в `MDC` после выполнения метода из-за `global = true`; остальные записи восстанавливаются или удаляются.

Под капотом неглобальные записи снимаются слепком до вызова и восстанавливаются в блоке `finally` при возврате из метода, поэтому за границы метода они не утекают.
Записи с `global = true` — как на аннотации метода, так и на аннотации параметра — и любые значения, выставленные императивным `MDC.put`, остаются в текущей области `MDC` и потому видны во всех последующих строках лога этого запроса, сообщения или задания.

#### Генерация значения из кода { #generated-value-for-mdc-value }

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Mdc(key = "key", value = "${java.util.UUID.randomUUID().toString()}")
    public String test(String s) {
        return "1";
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Mdc(key = "key", value = "\${java.util.UUID.randomUUID().toString()}")
    fun test(s: String): String {
        return "1";
    }
    ```

При вызове метода в `MDC` добавляется запись с ключом `key`, значением которой будет случайный `UUID`.
Значение в формате `${...}` вставляется в сгенерированный код как выражение, поэтому оно должно быть корректным кодом на языке аннотированного класса.

**Пример лога с `MDC`:**
```
INFO  [main] io.koraframework.example.Example.test - key="ee1a1a0e-3fdf-4e46-8b6e-2f16d2f0f0a1" key1="value2" 123="testValue" >
    data={"s":"testValue"}
```

`@Mdc` не поддерживается для методов, возвращающих `CompletionStage`, `CompletableFuture`, `Future`, `Mono` или `Flux`.
Для `Kotlin` поддерживаются обычные и `suspend` методы, но в `suspend` методах нельзя использовать `global = true`.

### Императивный MDC { #imperative-mdc }

Там, где аннотация не подходит — внутри перехватчиков, фильтров или обычного кода сервиса — используйте императивный API `io.koraframework.logging.common.MDC`.
Это программный аналог `@Mdc`: записи попадают в `MDC`, привязанный к текущей области, и появляются во всех строках лога до конца этой области.

Kora создает новый `MDC` в начале каждой единицы работы — HTTP-запроса, записи Kafka, вызова gRPC, запуска задания планировщика, сообщения JMS — поэтому записи одного запроса не протекают в другой.

У статического метода `put` есть перегрузки для значений `String`, `Integer`, `Long` и `Boolean`, а также перегрузка с `StructuredArgumentWriter` для структурированных значений.
`remove(key)` удаляет одну запись, а `get().values()` возвращает текущие записи неизменяемой картой `Map<String, StructuredArgumentWriter>`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    import io.koraframework.logging.common.MDC;

    @Component
    public final class OrderService {

        public void process(String orderId) {
            MDC.put("orderId", orderId);                  // String
            MDC.put("attempt", 1);                        // Integer
            MDC.put("bytes", 1024L);                      // Long
            MDC.put("retryable", true);                   // Boolean
            MDC.put("payload", gen -> gen.writeString(orderId)); // StructuredArgumentWriter

            // ... business logic; every log line in this scope now carries the keys

            MDC.remove("attempt");                        // drop a single key
            var current = MDC.get().values();             // read current entries
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import io.koraframework.logging.common.MDC

    @Component
    class OrderService {

        fun process(orderId: String) {
            MDC.put("orderId", orderId)                   // String
            MDC.put("attempt", 1)                         // Integer
            MDC.put("bytes", 1024L)                       // Long
            MDC.put("retryable", true)                    // Boolean
            MDC.put("payload") { gen -> gen.writeString(orderId) } // StructuredArgumentWriter

            // ... business logic; every log line in this scope now carries the keys

            MDC.remove("attempt")                         // drop a single key
            val current = MDC.get().values()              // read current entries
        }
    }
    ```

В отличие от `@Mdc`, у императивного API нет ограничений на сигнатуру метода, потому что он пишет в текущую область, а не оборачивает вызов метода.

`MDC` доступен как `ScopedValue` с именем `MDC.VALUE`.
Вне области запроса, сообщения или задания — во время инициализации графа, в shutdown hook или в обычном юнит-тесте — ничего не привязано и `MDC.get()` падает, поэтому такой код нужно защищать:

===! ":fontawesome-brands-java: `Java`"

    ```java
    if (MDC.VALUE.isBound()) {
        MDC.put("orderId", orderId);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    if (MDC.VALUE.isBound()) {
        MDC.put("orderId", orderId)
    }
    ```

Чтобы выполнить собственный код в новой области `MDC`, привяжите значение явно через `ScopedValue.where(MDC.VALUE, new MDC())`; `MDC.fork()` создает независимую копию текущих записей — именно так Kora поступает, когда передает работу во вложенную область.

!!! warning "Используйте `MDC` от Kora, а не от SLF4J"

    Всегда импортируйте `io.koraframework.logging.common.MDC`, но не `org.slf4j.MDC`.
    Класс SLF4J пишет в обычный `ThreadLocal`, не связанный с областью, которую Kora открывает на запрос, сообщение или задание: такие значения не очищаются между единицами работы, теряются при передаче работы другому потоку и умеют хранить только строки.
    `MDC` от Kora ограничен областью, распространяется самим фреймворком и хранит структурированные значения `JSON`.

    Асинхронное логирование должно идти через `KoraAsyncAppender` — он снимает слепок текущего `MDC` в вызывающем потоке до того, как событие уйдет в поток аппендера. Смотрите [Logback](logging-slf4j.md#logback).

## Сигнатуры { #signatures }

Поддерживаемые сигнатуры методов для аспектов логирования:

===! ":fontawesome-brands-java: `Java`"

    Класс не должен быть `final`, чтобы аспект мог создать наследника, метод не должен быть `final` или `private`, а у класса должен быть конструктор, видимый сгенерированному прокси.

    `T` — тип возвращаемого значения либо `void`.

    - `T myMethod()`
    - `Optional<T> myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/CompletionStage.html) (только для `@Log`, вход логируется при вызове, а выход — при завершении)
    - `CompletableFuture<T> myMethod()` (только для `@Log`, вход логируется при вызове, а выход — при завершении)

    `Mono<T>` и `Flux<T>` из `Project Reactor`, как и обычный `Future<T>`, не являющийся `CompletionStage`, не поддерживаются — компиляция завершится явной ошибкой.

=== ":simple-kotlin: `Kotlin`"

    Класс должен быть `open` и не абстрактным, чтобы аспект мог создать наследника, а функция должна быть `open` и членом этого класса — функции верхнего уровня проксировать нельзя.

    `T` — тип возвращаемого значения, `T?` либо `Unit`.

    - `myMethod(): T`
    - `suspend myMethod(): T` [Kotlin Coroutines](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (требуется [зависимость](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) как `implementation`)
    - `myMethod(): Flow<T>` [Kotlin Coroutines](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (только для `@Log`, требуется [зависимость](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) как `implementation`)

    Для `Flow<T>` событие входа логируется при старте потока, каждый выданный элемент логируется сообщением `<<<`, а сообщение `<` пишется при завершении потока.

    `Mono<T>` и `Flux<T>` из `Project Reactor` не поддерживаются — компиляция завершится явной ошибкой.

`@Mdc` строже `@Log`: он принимает только синхронные методы и, в `Kotlin`, `suspend` функции.
