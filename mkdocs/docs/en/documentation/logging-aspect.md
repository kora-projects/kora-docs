Module for declarative logging of method arguments and result using annotations.

## Dependency

Most likely already transitively connected from other dependencies or from [Logback](logging-slf4j.md#logback), otherwise it needs to be added:

===! ":fontawesome-brands-java: `Java`"

    Dependency `build.gradle`:
    ```groovy
    annotationProcessor "ru.tinkoff.kora:annotation-processors"
    implementation "ru.tinkoff.kora:logging-common"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends LoggingModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Dependency `build.gradle.kts`:
    ```groovy
    ksp("ru.tinkoff.kora:symbol-processors")
    implementation("ru.tinkoff.kora:logging-common")
    ```

    Module:
    ```kotlin
    @KoraApp
    interface Application : LoggingModule
    ```

## Logging

It is expected to use special combinations of annotations to customize method logging.

### Argument

```java 
@Log.in
public String methodWithReturnAndOnlyLogArgs(@Log.off String strParam,int numParam) {
    return"testResult";
}
```

<table>
    <thead>
        <th>Logging Level</th>
        <th>Logging</th>
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

### Result

```java 
@Log.out
public String methodWithOnlyLogReturnAndArgs(String strParam, int numParam) {
    return "testResult"
}
```

<table>
    <thead>
        <th>Logging level</th>
        <th>Logging</th>
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

### Argument and result

```java 
@Log
public String methodWithArgs(String strParam, int numParam) {
    return "testResult";
}
```

<table>
    <thead>
        <th>Logging Level</th>
        <th>Logging</th>
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

### Selective logging

```java 
@Log.out
@Log.off
public String methodWithOnlyLogReturnAndArgs(String strParam,int numParam) {
    return"testResult";
}
```

<table>
    <thead>
        <th>Logging Level</th>
        <th>Logging</th>
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

## Signatures

Available signatures for repository methods out of the box:

===! ":fontawesome-brands-java: `Java`"

    Class must be non `final` in order for aspects to work.

    The `T` refers to the type of the return value, either `Void`.

    - `T myMethod()`
    - `Optional<T> myMethod()`
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/)

=== ":simple-kotlin: `Kotlin`"

    Class must be `open` in order for aspects to work.

    By `T` we mean the type of the return value, either `Void`.

    - `myMethod(): T`
    - `myMethod(): T?`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine)
    - `suspend myMethod(): T?` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine)
