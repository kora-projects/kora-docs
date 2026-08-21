---
description: "Explains Kora logging aspects for argument and result logging, selective logging, MDC enrichment, structured parameters, conversion, and signatures. Use when working with @Log, @Log.in, @Log.out, @Log.off, @Mdc, @StructuredArgument, MDC, LogAspect."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora logging aspects for argument and result logging, selective logging, MDC enrichment, structured parameters, conversion, and signatures; key triggers include @Log, @Log.in, @Log.out, @Log.off, @Mdc, @StructuredArgument, MDC, LogAspect."
---

Модуль декларативного логирования позволяет описывать логирование метода с помощью аннотаций `@Log` и `@Mdc`.
На этапе компиляции Kora создает аспект-обертку для метода; обертка логирует вход в метод, выход из метода, результат, ошибку и значения `MDC` без ручного кода в бизнес-логике.
Это удобно для единообразной диагностики вызовов, особенно когда нужно быстро понять, какой метод был вызван, с какими аргументами и как он завершился.

Пошаговый разбор перед справочным описанием смотрите в разделе [Наблюдаемость](../guides/observability.md).

## Подключение { #dependency }

Аннотации и вспомогательные классы предоставляются зависимостью `logging-common`.
Обычно она уже приходит через другие модули Kora или через [Logback](logging-slf4j.md#logback), но при использовании аннотаций напрямую зависимость можно добавить явно:

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:logging-common"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends LoggingModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:logging-common")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : LoggingModule
    ```

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

Само событие входа или выхода пишется на уровне, указанном в `@Log`, `@Log.in` или `@Log.out`.
Значения аргументов и результата добавляются в структурированные данные только если включен соответствующий уровень детализации.
Какой уровень детализации активен, зависит от эффективного уровня логгера, настроенного через `logging.level` / `logging.levels` — смотрите [настройку уровней логирования](logging-slf4j.md#configuration).

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
            <p>INFO [main] r.t.e.e.Example.doWork: > {data: {numParam: "4"}}</p>
        </td>
    </tr>
    <tr>
        <td>TRACE</td>
        <td>
            <p>INFO [main] r.t.e.e.Example.doWork: > {data: {numParam: "4"}}</p>
        </td>
    </tr>
    <tr>
        <td>INFO</td>
        <td>
            <p>INFO [main] r.t.e.e.Example.doWork: ></p>
        </td>
    </tr>
</table>

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
            <p>INFO [main] r.t.e.e.Example.doWork: < {data: {out: "testResult"}}</p>
        </td>
    </tr>
    <tr>
        <td>TRACE</td>
        <td>
            <p>INFO [main] r.t.e.e.Example.doWork: < {data: {out: "testResult"}}</p>
        </td>
    </tr>
    <tr>
        <td>INFO</td>
        <td>
            <p>INFO [main] r.t.e.e.Example.doWork: <</p>
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
            <p>INFO [main] r.t.e.e.Example.doWork: > {data: {strParam: "s", numParam: "4"}}</p>
            <p>INFO [main] r.t.e.e.Example.doWork: < {data: {out: "testResult"}}</p>
        </td>
    </tr>
    <tr>
        <td>TRACE</td>
        <td>
            <p>INFO [main] r.t.e.e.Example.doWork: > {data: {strParam: "s", numParam: "4"}}</p>
            <p>INFO [main] r.t.e.e.Example.doWork: < {data: {out: "testResult"}}</p>
        </td>
    </tr>
    <tr>
        <td>INFO</td>
        <td>
            <p>INFO [main] r.t.e.e.Example.doWork: ></p>
            <p>INFO [main] r.t.e.e.Example.doWork: <</p>
        </td>
    </tr>
</table>

Если метод завершается ошибкой, аспект записывает выход из метода с данными об ошибке: `errorType` и `errorMessage`.
При включенном `DEBUG` в лог также передается объект исключения.

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
            <p>INFO [main] r.t.e.e.Example.doWork: <</p>
        </td>
    </tr>
    <tr>
        <td>INFO</td>
        <td>
            <p>INFO [main] r.t.e.e.Example.doWork: <</p>
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

Если строковое представление параметра не подходит для лога, тип параметра может реализовать интерфейс `StructuredArgument`.
В этом случае объект сам задает имя поля через `fieldName()` и записывает значение в `JsonGenerator` через `writeTo(...)`.

===! ":fontawesome-brands-java: `Java`"

    ```java 
    public record Entity(String name, String code) implements StructuredArgument {

        @Override
        public String fieldName() {
            return "name";
        }

        @Override
        public void writeTo(JsonGenerator generator) throws IOException {
            generator.writeString(name);
        }
    }

    @Log.in
    public String doWork(Entity entity) {
        return "testResult";
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class Entity(val name: String, val code: String) : StructuredArgument {

        override fun writeTo(generator: JsonGenerator) = generator.writeString(name)

        override fun fieldName(): String = "name"
    }

    @Log.`in`
    fun doWork(entity: Entity): String {
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
            <p>INFO [main] r.t.e.e.Example.doWork: ></p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp; data={"entity":"Bob"}</p>
        </td>
    </tr>
    <tr>
        <td>INFO</td>
        <td>
            <p>INFO [main] r.t.e.e.Example.doWork: ></p>
        </td>
    </tr>
</table>

Когда нужно структурированное значение без введения отдельного типа, интерфейс `StructuredArgument` предоставляет статические фабричные методы:
`arg(fieldName, value)` / `arg(fieldName, value, JsonWriter)` создают структурированный аргумент (перегрузки принимают `String`, `Integer`, `Long`, `Boolean`, `Map<String, String>`, `JsonWriter` или сырой `StructuredArgumentWriter`),
а `marker(fieldName, value)` создает `org.slf4j.Marker` для одного вызова лога. Полученный `StructuredArgument` можно также передать напрямую в `MDC.put`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    // ad-hoc structured value fed into MDC
    MDC.put("order", StructuredArgument.arg("orderId", orderId));

    // or as an SLF4J marker on a single log line
    log.info(StructuredArgument.marker("orderId", orderId), "order accepted");
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    // ad-hoc structured value fed into MDC
    MDC.put("order", StructuredArgument.arg("orderId", orderId))

    // or as an SLF4J marker on a single log line
    log.info(StructuredArgument.marker("orderId", orderId), "order accepted")
    ```

### Конвертация параметров { #parameter-conversion }

Если менять сам тип параметра нельзя, можно описать внешний преобразователь `StructuredArgumentMapper` и указать его через `@Mapping` на нужном аргументе.
Такой преобразователь получает исходное значение параметра и записывает структурированное значение в `JsonGenerator`.

===! ":fontawesome-brands-java: `Java`"

    ```java 
    public record Entity(String name, String code) { }

    public final class EntityLogMapper implements StructuredArgumentMapper<Entity> {
        public void write(JsonGenerator gen, Entity value) throws IOException {
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

        @Throws(IOException::class)
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
            <p>INFO [main] r.t.e.e.Example.doWork: ></p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp; data={"entity":"Bob"}</p>
        </td>
    </tr>
    <tr>
        <td>INFO</td>
        <td>
            <p>INFO [main] r.t.e.e.Example.doWork: ></p>
        </td>
    </tr>
</table>

### MDC (Mapped Diagnostic Context) { #mdc-mapped-diagnostic-context }

Аннотация `@Mdc` добавляет пары ключ-значение в `MDC` (`Mapped Diagnostic Context`).
`MDC` хранит контекст выполнения и позволяет добавлять его к лог-сообщениям: например, идентификатор запроса, пользователя или операции.

Аннотация может применяться к методам и параметрам методов.
На методе поддерживается множественное применение `@Mdc`.
Значения, добавленные без `global = true`, восстанавливаются после выполнения метода.

**Параметры аннотации `@Mdc`:**

- `key()` - ключ записи `MDC` (по умолчанию: `""`).
- `value()` - значение записи `MDC` (по умолчанию: `""`).
- `global()` - оставлять значение в `MDC` после выхода из метода (по умолчанию: `false`).

Для `@Mdc` на методе обязательны непустые `key` и `value`.
Для `@Mdc` на параметре ключ берется из `key`, затем из `value`, а если оба значения пустые - из имени параметра.
Значением записи становится значение параметра.

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

В этом случае ключ `MDC` будет совпадать с именем параметра `s`, а значением будет значение параметра.

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

Здесь ключом `MDC` будет `123`, а значением - значение параметра `s`.

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

В этом примере перед вызовом метода в `MDC` будет добавлена запись `key1=value2`.
После завершения метода предыдущее значение `key1` будет восстановлено.

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

В этом примере к методу применены две аннотации `@Mdc`, а к параметру - одна.
Запись `key=value` останется в `MDC` после выполнения метода из-за `global = true`, остальные записи будут восстановлены или удалены.

Под капотом неглобальные записи сохраняются в виде снимка до вызова и восстанавливаются в блоке `finally` после возврата из метода, поэтому они никогда не выходят за пределы области видимости метода.
Записи, добавленные с `global = true` (а также любое значение, установленное через императивный `MDC.put`, смотрите ниже), остаются в `Context` на протяжении всей области видимости запроса/потока и потому видны в каждой последующей строке лога.

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

При вызове метода в `MDC` будет добавлена запись с ключом `key`, а значением будет случайный `UUID`.
Для `Java` значение в формате `${...}` вставляется в сгенерированный код как выражение.

**Пример лога с `MDC`:**
```
INFO [main] r.t.e.e.Example.test: > {data: {s: "testValue"}} key=some-uuid-value key1=value2 123=testValue
```

`@Mdc` не поддерживается для методов, которые возвращают `CompletionStage`, `Mono` или `Flux`.
Для `Kotlin` поддерживаются обычные методы и `suspend`-методы, но `global = true` нельзя использовать в `suspend`-методах.

### Императивный MDC { #imperative-mdc }

Там, где аннотация не подходит — внутри перехватчиков, фильтров или обычного кода сервиса — используйте императивный API `ru.tinkoff.kora.logging.common.MDC`.
Это программный аналог `@Mdc`: записи привязываются к `Context` Kora, поэтому они распространяются через асинхронные границы точно так же, как записи `@Mdc(global = true)`, и появляются в каждой строке лога, выводимой на протяжении оставшейся области видимости текущего `Context`.

Статический метод `put` имеет перегрузки для значений `String`, `Integer`, `Long` и `Boolean`, а также перегрузку с `StructuredArgumentWriter` для структурированных значений.
`remove(key)` удаляет одну запись, а `get().values()` возвращает текущие записи как неизменяемую `Map<String, StructuredArgumentWriter>`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    import ru.tinkoff.kora.logging.common.MDC;

    @Component
    public final class OrderService {

        public void process(String orderId) {
            MDC.put("orderId", orderId);                  // String
            MDC.put("attempt", 1);                        // Integer
            MDC.put("bytes", 1024L);                      // Long
            MDC.put("retryable", true);                   // Boolean
            MDC.put("payload", gen -> gen.writeString(orderId)); // StructuredArgumentWriter

            // ... business logic; every log line in this Context now carries the keys

            MDC.remove("attempt");                        // drop a single key
            var current = MDC.get().values();             // read current entries
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import ru.tinkoff.kora.logging.common.MDC

    @Component
    class OrderService {

        fun process(orderId: String) {
            MDC.put("orderId", orderId)                   // String
            MDC.put("attempt", 1)                         // Integer
            MDC.put("bytes", 1024L)                       // Long
            MDC.put("retryable", true)                    // Boolean
            MDC.put("payload") { gen -> gen.writeString(orderId) } // StructuredArgumentWriter

            // ... business logic; every log line in this Context now carries the keys

            MDC.remove("attempt")                         // drop a single key
            val current = MDC.get().values()              // read current entries
        }
    }
    ```

Когда у вас уже есть `Context` (например, внутри перехватчика), обращайтесь к нему явно через `MDC.get(ctx)` и `MDC.put(ctx, key, writer)` вместо сокращений для текущего `Context`.
В отличие от `@Mdc`, у императивного API нет ограничения на реактивные/`suspend`-методы, поскольку он пишет напрямую в `Context`, а не оборачивает вызов метода.

!!! warning "Используйте `MDC` из Kora, а не из SLF4J"

    Всегда импортируйте `ru.tinkoff.kora.logging.common.MDC` — никогда `org.slf4j.MDC`.
    Класс SLF4J пишет в отдельный `ThreadLocal`, не связанный с `Context` Kora: помещенные туда значения не появятся в структурированных логах Kora и не будут распространяться через асинхронные границы (реактивные операторы, `suspend`-функции, передача между потоками).

## Сигнатуры { #signatures }

Сигнатуры методов, поддерживаемые для аспектов логирования:

===! ":fontawesome-brands-java: `Java`"

    Класс не должен быть `final`, чтобы аспекты могли создать наследника.

    Под `T` подразумевается тип возвращаемого значения, либо `Void`.

    - `T myMethod()`
    - `Optional<T> myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletionStage.html) (только для `@Log`)
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (только для `@Log`, требует [зависимость](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))
    - `Flux<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (только для `@Log`, требует [зависимость](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

=== ":simple-kotlin: `Kotlin`"

    Класс должен быть `open`, чтобы аспекты могли создать наследника.

    Под `T` подразумевается тип возвращаемого значения, либо `T?`, либо `Unit`.

    - `myMethod(): T`
    - `suspend myMethod(): T` [Kotlin Coroutines](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (требует [зависимость](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) как `implementation`)
    - `myMethod(): Flow<T>` [Kotlin Coroutines](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (требует [зависимость](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) как `implementation`)
