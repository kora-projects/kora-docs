Модуль для декларативного логирования аргументов и результата методов с помощью аннотаций.

## Подключение

Скорее всего уже транзитивно подключен из других зависимостей либо из [Logback](logging-slf4j.md#logback), в противном случае требуется подключить:

=== ":fontawesome-brands-java: `Java`"

    Зависимость `build.gradle`:
    ```groovy
    annotationProcessor "ru.tinkoff.kora:annotation-processors"
    implementation "ru.tinkoff.kora:logging-common"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends LoggingModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Зависимость `build.gradle.kts`:
    ```groovy
    ksp("ru.tinkoff.kora:symbol-processors")
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

```java 
@Log.in
public String methodWithReturnAndOnlyLogArgs(@Log.off String strParam,int numParam) {
    return"testResult";
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
            <p>DEBUG [] r.t.e.e.Example.methodWithArgs: > {data: {numParam: "4"}}</p>
        </td>
    </tr>
    <tr>
        <td>INFO</td>
        <td>
            <p>INFO [] r.t.e.e.Example.methodWithArgs: ></p>
        </td>
    </tr>
</table>

### Результата

```java 
@Log.out
public String methodWithOnlyLogReturnAndArgs(String strParam, int numParam) {
    return "testResult";
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
            <p>DEBUG [] r.t.e.e.Example.methodWithArgs: < {data: {out: "testResult"}}</p>
        </td>
    </tr>
    <tr>
        <td>INFO</td>
        <td>
            <p>INFO [] r.t.e.e.Example.methodWithArgs: <</p>
        </td>
    </tr>
</table>

### Аргументов и результата

```java 
@Log
public String methodWithArgs(String strParam, int numParam) {
    return "testResult";
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
            <p>DEBUG [] r.t.e.e.Example.methodWithArgs: > {data: {strParam: "s", numParam: "4"}}</p>
            <p>DEBUG [] r.t.e.e.Example.methodWithArgs: < {data: {out: "testResult"}}</p>
        </td>
    </tr>
    <tr>
        <td>INFO</td>
        <td>
            <p>INFO [] r.t.e.e.Example.methodWithArgs: ></p>
            <p>INFO [] r.t.e.e.Example.methodWithArgs: <</p>
        </td>
    </tr>
</table>

### Выборочное логирование

```java 
@Log.out
@Log.off
public String methodWithOnlyLogReturnAndArgs(String strParam,int numParam) {
    return"testResult";
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
            <p>INFO [] r.t.e.e.Example.methodWithArgs: <</p>
        </td>
    </tr>
    <tr>
        <td>INFO</td>
        <td>
            <p>INFO [] r.t.e.e.Example.methodWithArgs: <</p>
        </td>
    </tr>
</table>

## Сигнатуры

Доступные сигнатуры для методов которые поддерживают аннотации из коробки:

=== ":fontawesome-brands-java: `Java`"

    Под `T` подразумевается тип возвращаемого значения, либо `Void`.

    - `T myMethod()`
    - `Optional<T> myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/CompletionStage.html)
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/)

=== ":simple-kotlin: `Kotlin`"

    Под `T` подразумевается тип возвращаемого значения, либо `Unit`.

    - `myMethod(): T`
    - `myMethod(): T?`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine)
    - `suspend myMethod(): T?` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine)
