Module for declarative logging of method arguments and result using annotations.

## Dependency

Most likely already transitively connected from other dependencies or from [Logback](logging-slf4j.md#logback), otherwise it needs to be added:

===! ":fontawesome-brands-java: `Java`"

    [Dependency](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:logging-common"
    ```

    Module:
    ```java
    @KoraApp
    public interface Application extends LoggingModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Dependency](general.md#dependencies) `build.gradle.kts`:
    ```groovy
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

### MDC (Mapped Diagnostic Context)

The `@Mdc` annotation allows adding key-value pairs to MDC (Mapped Diagnostic Context) for structured logging.
MDC allows adding contextual information to each log message.

The annotation can be applied to methods and method parameters. Multiple application is supported.

**Parameters of the `@Mdc` annotation:**

- `key()` - Key for the MDC entry. If not specified, the name of the annotated parameter is used.
- `value()` - Value for the MDC entry. If not specified, the value of the annotated parameter is used.
- `global()` - If true, the MDC value will be available globally within the thread, not just during method execution.

#### Parameter annotation

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

In this case, the MDC key will match the parameter name ("s"), and the value will be the parameter value.

#### Parameter annotation with key

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

Here, the MDC key will be "123", and the value will be the value of parameter "s".

#### Method use

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

This example demonstrates:
- Method annotation with local MDC value

#### Combined

===! ":fontawesome-brands-java: `Java`"

    ```java 
    @Mdc(key = "key", value = "value", global = true)
    @Mdc(key = "key1", value = "value2")
    public Integer test(@Mdc(key = "123") String s) {
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

In this example, two MDC annotations are applied to the method, and one annotation is applied to the parameter.

#### Generated value for MDC value

===! ":fontawesome-brands-java: `Java`"

    ```java 
    @Mdc(key = "key", value = "${java.util.UUID.randomUUID().toString()}")
    public Integer test(String s) {
        return "1";
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Mdc(key = "key", value = "\${java.util.UUID.randomUUID().toString()}")
    fun test(s: String): String {
        return "1"
    }
    ```

When calling the method, an MDC entry will be added with the key "key" and a value as generated random UUID.

**Example log with MDC:**
```
INFO [main] r.t.e.e.Example.test: > {data: {s: "testValue"}} key=some-uuid-value key1=value2 123=testValue
```

## Signatures

Available signatures for repository methods out of the box:

===! ":fontawesome-brands-java: `Java`"

    Class must be non `final` in order for aspects to work.

    The `T` refers to the type of the return value, either `Void`.

    - `T myMethod()`
    - `Optional<T> myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletionStage.html)
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (require [dependency](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))
    - `Flux<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/) (require [dependency](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

=== ":simple-kotlin: `Kotlin`"

    Class must be `open` in order for aspects to work.

    By `T` we mean the type of the return value, either `T?`, either `Unit`.

    - `myMethod(): T`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (require [dependency](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) as `implementation`)
    - `myMethod(): Flow<T>` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine) (require [dependency](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) as `implementation`)
