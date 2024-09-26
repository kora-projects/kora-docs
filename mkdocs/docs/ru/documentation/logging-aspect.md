Модуль для декларативного логирования аргументов и результата методов с помощью аннотаций аспектов.

## Подключение

Скорее всего уже транзитивно подключен из других зависимостей либо из [Logback](logging-slf4j.md#logback), в противном случае требуется подключить:

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#_4) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:logging-common"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends LoggingModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#_4) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:logging-common")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : LoggingModule
    ```

## Логирование

Предполагается использовать специальные комбинации аннотаций для настройки логирование методов.

### Аргументов

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
        <th>Уровень логгирования</th>
        <th>Лог</th>
    </thead>
    <tr>
        <td>TRACE, DEBUG</td>
        <td>
            <p>DEBUG [main] r.t.e.e.Example.doWork: > {data: {numParam: "4"}}</p>
        </td>
    </tr>
    <tr>
        <td>INFO</td>
        <td>
            <p>INFO [main] r.t.e.e.Example.doWork: ></p>
        </td>
    </tr>
</table>

### Результата

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
        <th>Уровень логгирования</th>
        <th>Лог</th>
    </thead>
    <tr>
        <td>TRACE, DEBUG</td>
        <td>
            <p>DEBUG [main] r.t.e.e.Example.doWork: < {data: {out: "testResult"}}</p>
        </td>
    </tr>
    <tr>
        <td>INFO</td>
        <td>
            <p>INFO [main] r.t.e.e.Example.doWork: <</p>
        </td>
    </tr>
</table>

### Аргументов и результата

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
        <th>Уровень логгирования</th>
        <th>Лог</th>
    </thead>
    <tr>
        <td>TRACE, DEBUG</td>
        <td>
            <p>DEBUG [main] r.t.e.e.Example.doWork: > {data: {strParam: "s", numParam: "4"}}</p>
            <p>DEBUG [main] r.t.e.e.Example.doWork: < {data: {out: "testResult"}}</p>
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

### Выборочное логирование

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
        <th>Уровень логгирования</th>
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

### Структурированный параметр

В случае если представление параметра как строкой не является желаемым поведением,
его можно реализовать интерфейс `StructuredArgument` и параметр научится логировать себя сам:

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
        <th>Уровень логгирования</th>
        <th>Лог</th>
    </thead>
    <tr>
        <td>TRACE, DEBUG</td>
        <td>
            <p>INFO [main] r.t.e.e.Example.doWork: ></p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp; data={"entity":"Bob"}</p>
        </td>
    </tr>
    <tr>
        <td>INFO</td>
        <td>
            <p>INFO [main] r.t.e.e.Example.doWork: ></p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp; data={"entity":"Bob"}</p>
        </td>
    </tr>
</table>

### Конвертация параметров

В случае если представление параметра как строкой не является желаемым поведением, 
его можно переназначить через указание `StructuredArgumentMapper` напротив желаемого аргумента:

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
        <th>Уровень логгирования</th>
        <th>Лог</th>
    </thead>
    <tr>
        <td>TRACE, DEBUG</td>
        <td>
            <p>INFO [main] r.t.e.e.Example.doWork: ></p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp; data={"entity":"Bob"}</p>
        </td>
    </tr>
    <tr>
        <td>INFO</td>
        <td>
            <p>INFO [main] r.t.e.e.Example.doWork: ></p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp; data={"entity":"Bob"}</p>
        </td>
    </tr>
</table>

## Сигнатуры

Доступные сигнатуры для методов которые поддерживают аннотации из коробки:

===! ":fontawesome-brands-java: `Java`"

    Класс не должен быть `final`, чтобы аспекты работали.

    Под `T` подразумевается тип возвращаемого значения, либо `Void`.

    - `T myMethod()`
    - `Optional<T> myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletionStage.html)
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (надо подключить [зависимость](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))
    - `Flux<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (надо подключить [зависимость](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

=== ":simple-kotlin: `Kotlin`"

    Класс должен быть `open`, чтобы аспекты работали.

    Под `T` подразумевается тип возвращаемого значения, либо `T?`, либо `Unit`.

    - `myMethod(): T`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (надо подключить [зависимость](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) как `implementation`)
    - `myMethod(): Flow<T>` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (надо подключить [зависимость](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) как `implementation`)
