---
description: "Explains Kora resilience aspects for circuit breakers, retries, timeouts, fallback methods, imperative managers, exceptions, telemetry, configuration, and supported signatures. Use when working with @CircuitBreaker, @Retry, @Timeout, @Fallback, CircuitBreakerConfig, RetryConfig, TimeoutConfig, ResilientModule."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora resilience aspects for circuit breakers, retries, timeouts, fallback methods, imperative managers, exceptions, telemetry, configuration, and supported signatures; key triggers include @CircuitBreaker, @Retry, @Timeout, @Fallback, CircuitBreakerManager, RetryManager, TimeoutManager, FallbackManager, RetryState, CallNotPermittedException, RetryExhaustedException, TimeoutExhaustedException, CircuitBreakerConfig, RetryConfig, TimeoutConfig, ResilientModule."
---

Модуль для построения отказоустойчивого приложения с помощью таких механизмов, как [CircuitBreaker](#circuitbreaker),
[Fallback](#fallback), [Retry](#retry) и [Timeout](#timeout).
Эти механизмы можно применять декларативно через аннотации-аспекты либо напрямую через компоненты-менеджеры, когда защита требуется в императивном коде.

`ResilientModule` объединяет `CircuitBreakerModule`, `RetryModule`, `TimeoutModule` и `FallbackModule`.

Пошаговый разбор перед справочным описанием смотрите в разделе [Отказоустойчивость](../guides/resilient.md).

## Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:resilient-kora"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends ResilientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:resilient-kora")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : ResilientModule
    ```

## CircuitBreaker { #circuitbreaker }

`CircuitBreaker` — это прокси, который управляет потоком запросов к конкретному методу
и может временно запретить выполнение этого метода, если тот выбрасывает много исключений, попадающих под настроенный фильтр (`CircuitBreakerPredicate`).

Цель применения CircuitBreaker — дать системе время исправить ошибку, вызвавшую сбой, прежде чем позволить приложению снова попытаться выполнить операцию.
Паттерн `CircuitBreaker` обеспечивает стабильность на время восстановления системы после сбоя и снижает влияние на производительность.
`CircuitBreaker` может находиться в одном из нескольких состояний: `CLOSED`, `OPEN`, `HALF_OPEN`.

- `CLOSED`: запрос приложения передается защищаемой операции. Прокси подсчитывает недавние сбои в пределах настроенного числа операций (`slidingWindowSize`), проходящих через него, и увеличивает этот счетчик, когда операция завершается неуспешно.
  Если количество запросов превышает минимально необходимое для расчета (`minimumRequiredCalls`) и число недавних сбоев превышает настроенный порог (`failureRateThreshold`), прокси переходит в `OPEN`.
- `OPEN`: находясь в этом состоянии, запрос приложения немедленно завершается с ошибкой, и приложению возвращается исключение.
  В этот момент прокси запускает таймер ожидания (`waitDurationInOpenState`), и по его истечении прокси переходит в `HALF_OPEN`.
- `HALF_OPEN`: ограниченному числу запросов (`permittedCallsInHalfOpenState`) от приложения разрешается пройти и вызвать операцию. Если эти запросы успешны, считается, что ошибка, ранее вызвавшая
  сбой, устранена, и `CircuitBreaker` переходит в состояние `CLOSED` (счетчик сбоев сбрасывается). Если какой-либо запрос завершается сбоем, `CircuitBreaker` считает, что
  неисправность все еще присутствует, поэтому возвращается в состояние `OPEN` и перезапускает таймер ожидания (`waitDurationInOpenState`), чтобы дать системе дополнительное время на восстановление после сбоя.

Состояние `HALF_OPEN` помогает предотвратить лавинообразный рост числа запросов к сервису: после начала восстановления сервис некоторое время может справляться лишь с ограниченным числом запросов.

Изначально находится в состоянии `CLOSED`.

### Декларативное использование { #declarative-usage }

Если `CircuitBreaker` находится в состоянии `OPEN`, вызов завершается с `CallNotPermittedException`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @CircuitBreaker("custom")
        public String getValue() {
            throw new IllegalStateException("Ops");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    open class SomeService {

        @CircuitBreaker("custom")
        fun value(): String = throw IllegalStateException("Ops")
    }
    ```

### Конфигурация { #configuration }

Существует конфигурация по умолчанию, которая применяется к CircuitBreaker при его создании,
после чего именованные настройки конкретного CircuitBreaker применяются поверх настроек по умолчанию.

Вы можете изменить настройки по умолчанию сразу для всех CircuitBreaker, изменив конфигурацию `default`.

Пример полной конфигурации, описанной в классе `CircuitBreakerConfig` (указаны примерные значения или значения по умолчанию):

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
        circuitbreaker {
            default {
                slidingWindowSize = 100 //(1)!
                minimumRequiredCalls = 10 //(2)!
                failureRateThreshold = 50 //(3)!
                waitDurationInOpenState = "25s" //(4)!
                permittedCallsInHalfOpenState = 15 //(5)!
                enabled = true //(6)!
                failurePredicateName = "MyPredicate" //(7)!
            }
        }
    }
    ```

    1.  Максимальное число запросов, используемых для расчета `failureRateThreshold` и определения состояния (`required`, значение по умолчанию не задано).
    2.  Минимальное число запросов, необходимое для начала расчета состояния (`required`, значение по умолчанию не задано).
    3.  Процент неуспешных запросов, необходимый для перехода в `OPEN`; значение должно быть от `1` до `100` (`required`, значение по умолчанию не задано).
    4.  Время ожидания в `OPEN`, по истечении которого выполняется переход в `HALF_OPEN` (`required`, значение по умолчанию не задано).
    5.  Число запросов в `HALF_OPEN`, которые должны завершиться успешно для перехода в `CLOSED` (`required`, значение по умолчанию не задано).
    6.  Включение или отключение `CircuitBreaker` (по умолчанию: `true`).
    7.  Имя фильтра исключений из `CircuitBreakerPredicate#name()` (по умолчанию учитываются все ошибки).


=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      circuitbreaker:
        default:
          slidingWindowSize: 100 #(1)!
          minimumRequiredCalls: 10 #(2)!
          failureRateThreshold: 50 #(3)!
          waitDurationInOpenState: "25s" #(4)!
          permittedCallsInHalfOpenState: 15 #(5)!
          enabled: true #(6)!
          failurePredicateName: "MyPredicate" #(7)!
    ```

    1.  Максимальное число запросов, используемых для расчета `failureRateThreshold` и определения состояния (`required`, значение по умолчанию не задано).
    2.  Минимальное число запросов, необходимое для начала расчета состояния (`required`, значение по умолчанию не задано).
    3.  Процент неуспешных запросов, необходимый для перехода в `OPEN`; значение должно быть от `1` до `100` (`required`, значение по умолчанию не задано).
    4.  Время ожидания в `OPEN`, по истечении которого выполняется переход в `HALF_OPEN` (`required`, значение по умолчанию не задано).
    5.  Число запросов в `HALF_OPEN`, которые должны завершиться успешно для перехода в `CLOSED` (`required`, значение по умолчанию не задано).
    6.  Включение или отключение `CircuitBreaker` (по умолчанию: `true`).
    7.  Имя фильтра исключений из `CircuitBreakerPredicate#name()` (по умолчанию учитываются все ошибки).

Пример переопределения именованных настроек конкретного CircuitBreaker:

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
        circuitbreaker {
            custom {
                waitDurationInOpenState = "50s"
            }
        }
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      circuitbreaker:
        custom:
          waitDurationInOpenState: "50s"
    ```

!!! warning "Ограничения"

    Следующие условия проверяются при старте приложения — нарушение любого из них приводит к ошибке сборки графа:
    `failureRateThreshold` должен быть в диапазоне `1..100`; `slidingWindowSize` ≥ `1`; `minimumRequiredCalls` ≥ `1` **и** ≤ `slidingWindowSize`; `permittedCallsInHalfOpenState` ≥ `1`.
    Для каждого `@CircuitBreaker` **должна** присутствовать либо именованная, либо `default` конфигурация, иначе запуск завершится ошибкой.

!!! note "Примечание"

    Установка `enabled = false` превращает аспект в прозрачный проброс — метод вызывается напрямую, без размыкания цепи.
    `failurePredicateName` по умолчанию равен `KoraCircuitBreakerPredicate` (учитывает каждую ошибку); собственный `CircuitBreakerPredicate` может использоваться несколькими прерывателями через ссылку на его `name()`.

Метрики модуля описаны в разделе [Справочник метрик](metrics.md#resilience).

### Фильтрация исключений { #exception-filtering }

Чтобы задать, какие ошибки должны учитываться как ошибки CircuitBreaker, вы можете переопределить фильтр по умолчанию:
необходимо реализовать `CircuitBreakerPredicate`, зарегистрировать свой компонент в контексте и указать в конфигурации CircuitBreaker его имя, возвращаемое методом `name()`.

По умолчанию `CircuitBreaker` учитывает все ошибки.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MyFailurePredicate implements CircuitBreakerPredicate {

        @Override
        public String name() {
            return "MyPredicate";
        }

        @Override
        public boolean test(Throwable throwable) {
            return true;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyFailurePredicate : CircuitBreakerPredicate {

        override fun name(): String = "MyPredicate"

        override fun test(throwable: Throwable): Boolean = true
    }
    ```

Конфигурация:

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
        circuitbreaker {
            custom {
                failurePredicateName = "MyPredicate" //(1)!
            }
        }
    }
    ```

    1. Имя фильтра исключений из `CircuitBreakerPredicate#name()` (по умолчанию учитываются все ошибки).

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      circuitbreaker:
        custom:
          failurePredicateName: "MyPredicate" #(1)!
    ```

    1. Имя фильтра исключений из `CircuitBreakerPredicate#name()` (по умолчанию учитываются все ошибки).

### Императивное использование { #imperative-usage }

Прерыватель можно использовать в императивном коде: внедрите `CircuitBreakerManager`
и получите из него `CircuitBreaker` по имени конфигурации, которое было бы указано в аннотации:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final CircuitBreakerManager manager;

        public SomeService(CircuitBreakerManager manager) {
            this.manager = manager;
        }

        public String doWork() {
            var circuitBreaker = manager.get("custom");
            return circuitBreaker.accept(this::doSomeWork);
        }

        private String doSomeWork() {
            // do some work
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(val manager: CircuitBreakerManager) {

        fun doWork(): String {
            val circuitBreaker = manager["custom"]
            return circuitBreaker.accept { doSomeWork() }
        }

        private fun doSomeWork(): String {
            // do some work
        }
    }
    ```

Чтобы вернуть резервное значение вместо выбрасывания `CallNotPermittedException`, когда прерыватель находится в `OPEN`, используйте перегрузку `accept`, принимающую второй `Supplier`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public String doWork() {
        var circuitBreaker = manager.get("custom");
        return circuitBreaker.accept(this::doSomeWork, () -> "fallback");
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun doWork(): String {
        val circuitBreaker = manager["custom"]
        return circuitBreaker.accept({ doSomeWork() }, { "fallback" })
    }
    ```

Когда защищаемый вызов нельзя обернуть в единственный `Supplier`, получите и освободите разрешение вручную.
Вызовите `acquire()` (выбрасывает `CallNotPermittedException`, когда прерыватель в `OPEN` либо в `HALF_OPEN` без оставшихся пробных вызовов), чтобы получить разрешение, затем **всегда** сообщайте о результате через `releaseOnSuccess()` или `releaseOnError(Throwable)` — иначе прерыватель теряет разрешение, и его учет становится некорректным:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public String doWork() {
        var circuitBreaker = manager.get("custom");
        circuitBreaker.acquire(); // throws CallNotPermittedException when the call is not permitted
        try {
            var result = doSomeWork();
            circuitBreaker.releaseOnSuccess();
            return result;
        } catch (Throwable e) {
            circuitBreaker.releaseOnError(e);
            throw e;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun doWork(): String {
        val circuitBreaker = manager["custom"]
        circuitBreaker.acquire() // throws CallNotPermittedException when the call is not permitted
        try {
            val result = doSomeWork()
            circuitBreaker.releaseOnSuccess()
            return result
        } catch (e: Throwable) {
            circuitBreaker.releaseOnError(e)
            throw e
        }
    }
    ```

`tryAcquire()` — это альтернатива без выбрасывания исключения: она возвращает `false`, когда вызов не разрешен, поэтому вы можете ветвить логику без перехвата `CallNotPermittedException`.
Когда `acquire()` все же выбрасывает исключение, текущее [состояние](#circuitbreaker) прерывателя (`OPEN` или `HALF_OPEN`) доступно через `CallNotPermittedException#state()`.

## Retry { #retry }

`Retry` предоставляет возможность настроить повторный вызов аннотированных методов.
Он позволяет задать, когда метод должен повторяться, и настроить параметры повторов, когда метод выбрасывает исключение, попадающее под настроенный фильтр (`RetryPredicate`).

### Декларативное использование { #declarative-usage-2 }

Если все попытки исчерпаны, вызов завершается с `RetryExhaustedException`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @Retry("custom1")
        public String getValue() {
            throw new IllegalStateException("Ops");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    open class SomeService {

        @Retry("custom1")
        fun execute(arg: String): Unit = throw IllegalStateException("Ops")
    }
    ```

### Конфигурация { #configuration-2 }

Существует конфигурация `default`, которая применяется к `Retry` при создании,
после чего именованные настройки конкретного `Retry` применяются поверх настроек по умолчанию.

Настройки по умолчанию можно изменить сразу для всех `Retry`, изменив конфигурацию `default`.

Пример полной конфигурации, описанной в классе `RetryConfig` (указаны значения по умолчанию или примерные значения):

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
        retry {
            default {
                delay = "100ms" //(1)!
                attempts = 2 //(2)!
                delayStep = "100ms" //(3)!
                enabled = true //(4)!
                failurePredicateName = "MyPredicate" //(5)!
            }
        }
    }
    ```

    1. Начальная задержка перед повторным вызовом (`required`, значение по умолчанию не задано).
    2. Число попыток повтора (`required`, значение по умолчанию не задано).
    3. Приращение задержки для последующих попыток (по умолчанию: `0`).
    4. Включение или отключение `Retry` (по умолчанию: `true`).
    5. Имя фильтра исключений из `RetryPredicate#name()` (по умолчанию учитываются все ошибки).

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      retry:
        default:
          delay: "100ms" #(1)!
          attempts: 2 #(2)!
          delayStep: "100ms" #(3)!
          enabled: true #(4)!
          failurePredicateName: "MyPredicate" #(5)!
    ```

    1. Начальная задержка перед повторным вызовом (`required`, значение по умолчанию не задано).
    2. Число попыток повтора (`required`, значение по умолчанию не задано).
    3. Приращение задержки для последующих попыток (по умолчанию: `0`).
    4. Включение или отключение `Retry` (по умолчанию: `true`).
    5. Имя фильтра исключений из `RetryPredicate#name()` (по умолчанию учитываются все ошибки).

!!! warning "Ограничения и прогрессия задержки"

    `delay` и `attempts` обязательны (берутся из именованной или `default` конфигурации), а `attempts` должно быть `≥ 0`; отсутствие `delay`/`attempts` или отрицательное `attempts` приводит к ошибке старта приложения.
    `attempts` считает повторы **после** первоначального вызова, поэтому `attempts = 2` допускает в сумме до `3` выполнений.
    Каждый повтор ждет на `delayStep` (по умолчанию `0`) дольше предыдущего, так что задержки составляют `delay`, `delay + delayStep`, `delay + 2·delayStep`, … .

!!! note "Примечание"

    Установка `enabled = false` превращает `@Retry` в прозрачный проброс (метод выполняется один раз).
    `failurePredicateName` по умолчанию равен `KoraRetryPredicate` (повторяет при каждой ошибке); собственный `RetryPredicate` может использоваться несколькими повторителями через ссылку на его `name()`.

### Фильтрация исключений { #exception-filtering-2 }

Чтобы задать, какие ошибки должны учитываться как ошибки на стороне Retry, вы можете переопределить фильтр по умолчанию:
необходимо реализовать `RetryPredicate`, зарегистрировать его компонент в контексте и указать в конфигурации Retry его имя, возвращаемое методом `name()`.

По умолчанию `Retry` учитывает все ошибки.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MyFailurePredicate implements RetryPredicate {

        @Override
        public String name() {
            return "MyPredicate";
        }

        @Override
        public boolean test(Throwable throwable) {
            return true;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyFailurePredicate : RetryPredicate {

        override fun name(): String = "MyPredicate"

        override fun test(throwable: Throwable): Boolean = true
    }
    ```

Конфигурация:

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
        retry {
            custom {
                failurePredicateName = "MyPredicate" //(1)!
            }
        }
    }
    ```
    
    1. Имя фильтра исключений из `RetryPredicate#name()` (по умолчанию учитываются все ошибки).

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      retry:
        custom:
          failurePredicateName: "MyPredicate" #(1)!
    ```

    1. Имя фильтра исключений из `RetryPredicate#name()` (по умолчанию учитываются все ошибки).

### Императивное использование { #imperative-usage-2 }

Повторитель можно использовать в императивном коде: внедрите `RetryManager`
и получите из него `Retry` по имени конфигурации, которое было бы указано в аннотации:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final RetryManager manager;

        public SomeService(RetryManager manager) {
            this.manager = manager;
        }

        public String doWork() {
            var retry = manager.get("custom");
            return retry.retry(this::doSomeWork);
        }

        private String doSomeWork() {
            // do some work
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(private val manager: RetryManager) {

        fun doWork(): String {
            val retry = manager["custom"]
            return retry.retry<String, RuntimeException> { doSomeWork() }
        }

        private fun doSomeWork(): String {
            // do some work
        }
    }
    ```

Чтобы вернуть резервное значение вместо выбрасывания `RetryExhaustedException`, когда все попытки исчерпаны, передайте второй `Supplier`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var retry = manager.get("custom");
    return retry.retry(this::doSomeWork, () -> "fallback");
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val retry = manager["custom"]
    return retry.retry<String, RuntimeException>({ doSomeWork() }, { "fallback" })
    ```

Для асинхронного императивного кода есть перегрузка, которая повторяет `Supplier<CompletionStage<T>>` и возвращает `CompletionStage<T>`, планируя каждую попытку после настроенной задержки без блокировки вызывающего потока.

#### Ручное управление состоянием повтора { #manual-retry-state }

Для полного контроля над циклом повторов используйте `retry.asState()`, который возвращает `RetryState`.
Он реализует `AutoCloseable`, поэтому оберните его в try-with-resources (Java) или `use` (Kotlin), чтобы записать метрики по завершении.
При каждом перехваченном исключении вызывайте `onException(Throwable)`, который возвращает `RetryStatus`:

- `ACCEPTED` — разрешена еще одна попытка; вызовите `doDelay()` (блокирует на время текущей задержки) и повторите.
- `REJECTED` — исключение отклонено `RetryPredicate` и не должно повторяться; пробросьте его.
- `EXHAUSTED` — все попытки исчерпаны; выбросьте `RetryExhaustedException` (или вернитесь к значению по умолчанию).

`getAttempts()` / `getAttemptsMax()` сообщают о прогрессе, а `getDelayNanos()` возвращает следующую задержку.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public String doWork() {
        var retry = manager.get("custom");
        try (var state = retry.asState()) {
            while (true) {
                try {
                    return doSomeWork();
                } catch (Exception e) {
                    switch (state.onException(e)) {
                        case ACCEPTED -> state.doDelay();   // wait, then loop and retry
                        case REJECTED -> throw e;           // not retryable
                        case EXHAUSTED -> throw new RetryExhaustedException("custom", state.getAttemptsMax(), e);
                    }
                }
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun doWork(): String {
        val retry = manager["custom"]
        retry.asState().use { state ->
            while (true) {
                try {
                    return doSomeWork()
                } catch (e: Exception) {
                    when (state.onException(e)) {
                        Retry.RetryState.RetryStatus.ACCEPTED -> state.doDelay()   // wait, then loop and retry
                        Retry.RetryState.RetryStatus.REJECTED -> throw e           // not retryable
                        Retry.RetryState.RetryStatus.EXHAUSTED -> throw RetryExhaustedException("custom", state.attemptsMax, e)
                    }
                }
            }
        }
    }
    ```

## Timeout { #timeout }

`Timeout` задает максимальное время выполнения аннотированного метода.

### Декларативное использование { #declarative-usage-3 }

Если метод не завершается в пределах `duration`, вызов завершается с `TimeoutExhaustedException`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @Timeout("custom")
        public String getValue() {
            try {
                Thread.sleep(3000);
                return "OK";
            } catch (InterruptedException e) {
                throw new IllegalStateException(e);
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    open class SomeService {

        @Timeout("custom")
        fun value(): String = try {
            Thread.sleep(3000)
            "OK"
        } catch (e: InterruptedException) {
            throw IllegalStateException(e)
        }
    }
    ```

### Конфигурация { #configuration-3 }

Существует конфигурация `default`, которая применяется к Timeout при его создании,
после чего именованные настройки конкретного Timeout применяются поверх настроек по умолчанию.

Настройки по умолчанию можно изменить сразу для всех Timeout, изменив конфигурацию `default`.

Пример полной конфигурации, описанной в классе `TimeoutConfig` (указаны значения по умолчанию или примерные значения):

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
        timeout {
            default {
                duration = "1s" //(1)!
                enabled = true //(2)!
            }
        }
    }
    ```

    1.  Ограничение времени операции, по превышении которого будет выброшено `TimeoutExhaustedException` (`required`, значение по умолчанию не задано).
    2.  Включение или отключение `Timeout` (по умолчанию: `true`).

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      timeout:
        default:
          duration: "1s" #(1)!
          enabled: true #(2)!
    ```

    1.  Ограничение времени операции, по превышении которого будет выброшено `TimeoutExhaustedException` (`required`, значение по умолчанию не задано).
    2.  Включение или отключение `Timeout` (по умолчанию: `true`).

!!! note "Примечание"

    `duration` обязателен (берется из именованной или `default` конфигурации), и без него запуск завершается ошибкой.
    Установка `enabled = false` превращает `@Timeout` в прозрачный проброс — метод выполняется без ограничения по времени.

### Императивное использование { #imperative-usage-3 }

Ограничитель времени можно использовать в императивном коде: внедрите `TimeoutManager`
и получите из него `Timeout` по имени конфигурации, которое было бы указано в аннотации:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final TimeoutManager manager;

        public SomeService(TimeoutManager manager) {
            this.manager = manager;
        }

        public String doWork() {
            var timeout = manager.get("custom");
            return timeout.execute(this::doSomeWork);
        }

        private String doSomeWork() {
            // do some work
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(private val manager: TimeoutManager) {

        fun doWork(): String {
            val timeout = manager["custom"]
            return timeout.execute<String> { doSomeWork() }
        }

        private fun doSomeWork(): String {
            // do some work
        }
    }
    ```

`Timeout` также предоставляет `execute(Runnable)` для операций, ничего не возвращающих, а `timeout()` возвращает настроенную `Duration`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var timeout = manager.get("custom");
    Duration limit = timeout.timeout();          // configured duration
    timeout.execute(() -> { /* do some work */ }); // Runnable variant, throws TimeoutExhaustedException on timeout
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val timeout = manager["custom"]
    val limit: Duration = timeout.timeout()            // configured duration
    timeout.execute(Runnable { /* do some work */ })   // Runnable variant, throws TimeoutExhaustedException on timeout
    ```

## Fallback { #fallback }

`Fallback` позволяет указать метод, который будет вызван, когда исключение, выброшенное аннотированным методом, попадает под настроенные фильтры (`FallbackPredicate`).

Резервный метод **должен совпадать** по типу возвращаемого значения с аннотированным методом.

### Декларативное использование { #declarative-usage-4 }

Пример резервного метода без аргументов:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @Fallback(value = "custom", method = "getFallback()")
        public String getValue() {
            return "value";
        }

        protected String getFallback() {
            return "fallback";
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    open class SomeService {

        @Fallback(value = "custom", method = "getFallback()")
        fun value(): String = "value"

        fun getFallback(): String = "fallback"
    }
    ```

Пример для *Fallback* с аргументами:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @Fallback(value = "custom", method = "getFallback(arg3, arg1)")     // Passes the arguments of the annotated method in the specified order to the Fallback method
        public String getValue(String arg1, Integer arg2, Long arg3) {
            return "value";
        }

        protected String getFallback(Long argLong, String argString) {
            return "fallback";
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    open class SomeService {

        // Passes the arguments of the annotated method in the specified order to the Fallback method
        @Fallback(value = "custom", method = "getFallback(arg3, arg1)")
        fun getValue(arg1: String, arg2: Int, arg3: Long): String = "value"

        fun getFallback(argLong: Long, argString: String): String = "fallback"
    }
    ```

### Конфигурация { #configuration-4 }

Существует конфигурация `default`, которая применяется к Fallback при создании,
после чего именованные настройки конкретного Fallback применяются поверх настроек по умолчанию.

Настройки по умолчанию можно изменить сразу для всех Fallback, изменив конфигурацию `default`.

Пример полной конфигурации, описанной в классе `FallbackConfig` (указаны значения по умолчанию или примерные значения):

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
        fallback {
            custom {
                failurePredicateName = "MyPredicate" //(1)!
                enabled = true //(2)!
            }
        }
    }
    ```

    1. Имя фильтра исключений из `FallbackPredicate#name()` (по умолчанию учитываются все ошибки).
    2. Включение или отключение `Fallback` (по умолчанию: `true`).

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      fallback:
        custom:
          failurePredicateName: "MyPredicate" #(1)!
          enabled: true #(2)!
    ```

    1. Имя фильтра исключений из `FallbackPredicate#name()` (по умолчанию учитываются все ошибки).
    2. Включение или отключение `Fallback` (по умолчанию: `true`).

!!! note "Примечание"

    В отличие от других аспектов, у `@Fallback` нет обязательных свойств — без конфигурации он использует значения по умолчанию.
    Установка `enabled = false` отключает резервный вариант, так что исходное исключение пробрасывается дальше.
    `failurePredicateName` по умолчанию равен `KoraFallbackPredicate` (запускает резервный вариант при каждой ошибке); собственный `FallbackPredicate` может использоваться несколькими резервными вариантами через ссылку на его `name()`.

### Фильтрация исключений { #exception-filtering-3 }

Чтобы задать, какие ошибки должны учитываться как ошибки Fallback, вы можете переопределить фильтр по умолчанию:
необходимо реализовать `FallbackPredicate`, зарегистрировать свой компонент в контексте и указать в конфигурации Fallback его имя, возвращаемое методом `name()`.

По умолчанию `Fallback` учитывает все ошибки.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class MyFailurePredicate implements FallbackPredicate {

        @Override
        public String name() {
            return "MyPredicate";
        }

        @Override
        public boolean test(Throwable throwable) {
            return true;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class MyFailurePredicate : FallbackPredicate {

        override fun name(): String = "MyPredicate"

        override fun test(throwable: Throwable): Boolean = true
    }
    ```

### Императивное использование { #imperative-usage-4 }

Резервный метод можно использовать в императивном коде: внедрите `FallbackManager`
и получите из него `Fallback` по имени конфигурации, которое было бы указано в аннотации:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final FallbackManager manager;

        public SomeService(FallbackManager manager) {
            this.manager = manager;
        }

        public String doWork() {
            var fallback = manager.get("custom");
            return fallback.fallback(this::doSomeWork, () -> "BackupValue");
        }

        private String doSomeWork() {
            // do some work
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(private val manager: FallbackManager) {

        fun doWork(): String {
            val fallback = manager["custom"]
            return fallback.fallback<String>({ doSomeWork() }) { "BackupValue" }
        }

        private fun doSomeWork(): String {
            // do some work
        }
    }
    ```

Для операций, ничего не возвращающих, используйте перегрузку с `Runnable`; а `canFallback(Throwable)` сообщает, запустит ли заданное исключение резервный вариант согласно настроенному `FallbackPredicate`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    var fallback = manager.get("custom");

    // canFallback tells whether the exception would trigger the fallback
    if (fallback.canFallback(exception)) {
        // exception matches the configured FallbackPredicate
    }

    // Runnable variant for operations that return nothing
    fallback.fallback(
        () -> { /* primary action */ },
        () -> { /* fallback action */ });
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val fallback = manager["custom"]

    // canFallback tells whether the exception would trigger the fallback
    if (fallback.canFallback(exception)) {
        // exception matches the configured FallbackPredicate
    }

    // Runnable variant for operations that return nothing
    fallback.fallback(Runnable { /* primary action */ }, Runnable { /* fallback action */ })
    ```

## Комбинирование { #combination }

Все перечисленные выше аннотации можно комбинировать одновременно над одним методом.

Порядок применения аннотаций зависит от порядка их объявления.
Вы можете менять порядок по своему усмотрению и комбинировать с другими аннотациями, которые также применяются в порядке объявления.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @Fallback(value = "default", method = "getFallback(arg1)")   // 4
        @CircuitBreaker("default")                                   // 3
        @Retry("default")                                            // 2
        @Timeout("default")                                          // 1
        public String getValueSync(String arg1) {
            return "result-" + arg1;
        }

        protected String getFallback(String arg1) {                  // 4
            return "fallback-" + arg1;
        }
    }   
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    open class SomeService {

        @Fallback(value = "default", method = "getFallback(arg1)")          // 4
        @CircuitBreaker("default")                                          // 3
        @Retry("default")                                                   // 2
        @Timeout("default")                                                 // 1
        fun getValueSync(arg1: String): String = "result-$arg1"

        protected fun getFallback(arg1: String): String = "fallback-$arg1"  // 4
    }
    ```

В примере выше:

1. Применяется `@Timeout` и проверяет, что метод не выполняется дольше времени, указанного в конфигурации.
2. Применяется `@Retry` и пытается повторить выполнение метода настроенное число раз, если метод выбрасывает исключение в цепочке, включая исключение из `@Timeout`.
3. Применяется `@CircuitBreaker` и работает согласно своей конфигурации и [состоянию](#circuitbreaker), в зависимости от успешного результата метода или исключения в цепочке, включая исключения из `@Timeout` и `@Retry`.
4. Применяется `@Fallback` и вызывает метод `getFallback` с аргументом `arg1`, если метод выбрасывает исключение в цепочке, включая исключения из `@Timeout`, `@Retry` и `@CircuitBreaker`.

Порядок вызова аспектов следует порядку аннотаций на методе: сверху вниз.

Пример конфигурации для всех аспектов:

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
        circuitbreaker {
            default {
                slidingWindowSize = 1
                minimumRequiredCalls = 1
                failureRateThreshold = 100
                permittedCallsInHalfOpenState = 1
                waitDurationInOpenState = "1s"
            }
        }
        timeout {
            default {
                duration = "300ms"
            }
        }
        retry {
            default {
                delay = "100ms"
                attempts = 2
            }
        }
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      circuitbreaker:
        default:
          slidingWindowSize: 1
          minimumRequiredCalls: 1
          failureRateThreshold: 100
          permittedCallsInHalfOpenState: 1
          waitDurationInOpenState: "1s"
      timeout:
        default:
          duration: "300ms"
      retry:
        default:
          delay: "100ms"
          attempts: 2
    ```

## Исключения { #exceptions }

Все исключения отказоустойчивости наследуются от `ru.tinkoff.kora.resilient.ResilientException` (это `RuntimeException`), который предоставляет `name()` — имя конфигурации аспекта, вызвавшего его.

| Исключение                   | Выбрасывается                                                                                      | Дополнительный API                                                                       |
|------------------------------|---------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| `ResilientException`         | базовый тип для всех перечисленных ниже                                                            | `name()`                                                                                 |
| `CallNotPermittedException`  | `@CircuitBreaker` / `CircuitBreaker#acquire()`, когда прерыватель в `OPEN` либо в `HALF_OPEN` без оставшихся пробных вызовов | `state()` возвращает `CircuitBreaker.State` (`OPEN` / `HALF_OPEN`)                        |
| `RetryExhaustedException`    | `@Retry` / `Retry#retry(...)`, когда каждая попытка завершилась неудачей                           | `name()`; в сообщении указано число попыток, последний сбой доступен через `getCause()`  |
| `TimeoutExhaustedException`  | `@Timeout` / `Timeout#execute(...)`, когда метод превышает `duration`                              | `name()`                                                                                  |

**Описание** — аспекты отказоустойчивости сигнализируют о сбое, выбрасывая одно из этих непроверяемых исключений из защищаемого метода.

**Причины**

- `CallNotPermittedException` — прерыватель размыкает вызовы, потому что доля сбоев достигла `failureRateThreshold`; вызов был отклонен без обращения к методу.
- `RetryExhaustedException` — метод продолжал выбрасывать повторяемое исключение, пока не было достигнуто `attempts`; исходный сбой доступен через `getCause()`.
- `TimeoutExhaustedException` — метод не завершился в пределах `duration`.

**Рекомендации**

- Перехватывайте `ResilientException`, чтобы единообразно обрабатывать любой сбой отказоустойчивости, либо перехватывайте конкретный тип, когда обработка различается.
- Когда аспекты [комбинируются](#combination), исключение нижележащего аспекта распространяется вверх по цепочке: например, `TimeoutExhaustedException` из `@Timeout` наблюдается `@Retry`, затем `@CircuitBreaker` и, наконец, `@Fallback`. Предпочитайте метод `@Fallback` или императивный резервный вариант превращению этих исключений в ошибки, видимые пользователю.

Пример обработки:

===! ":fontawesome-brands-java: `Java`"

    ```java
    try {
        return service.getValue();
    } catch (CallNotPermittedException e) {
        log.warn("CircuitBreaker '{}' is {}", e.name(), e.state());
        return cachedValue();
    } catch (TimeoutExhaustedException | RetryExhaustedException e) {
        log.warn("Resilient '{}' failed", e.name(), e);
        return cachedValue();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    try {
        return service.value()
    } catch (e: CallNotPermittedException) {
        log.warn("CircuitBreaker '{}' is {}", e.name(), e.state())
        return cachedValue()
    } catch (e: ResilientException) { // TimeoutExhaustedException, RetryExhaustedException, ...
        log.warn("Resilient '{}' failed", e.name(), e)
        return cachedValue()
    }
    ```

## Сигнатуры { #signatures }

Доступные сигнатуры методов, поддерживаемые этими аннотациями «из коробки»:
Все четыре аннотации поддерживают обычные синхронные методы, асинхронные типы и реактивные типы, но фактический набор зависит от языка и обработчика.

===! ":fontawesome-brands-java: `Java`"

    Класс должен быть не `final`, чтобы аспекты работали.

    `T` обозначает тип возвращаемого значения.

    - `void myMethod()`
    - `T myMethod()`
    - `Optional<T> myMethod()`
    - `CompletionStage<T> myMethod()` / `CompletableFuture<T> myMethod()` ([CompletionStage](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletionStage.html))
    - `Mono<T> myMethod()` ([Project Reactor](https://projectreactor.io/docs/core/release/reference/), требуется [зависимость](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))
    - `Flux<T> myMethod()` ([Project Reactor](https://projectreactor.io/docs/core/release/reference/), требуется [зависимость](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

=== ":simple-kotlin: `Kotlin`"

    Класс должен быть `open`, чтобы аспекты работали.

    Под `T` понимается тип возвращаемого значения, либо `T?`, либо `Unit`.

    - `myMethod(): T`
    - `suspend myMethod(): T` ([Kotlin Coroutines](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine), требуется [зависимость](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) как `implementation`)
    - `myMethod(): Flow<T>` ([Kotlin Coroutines](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine), требуется [зависимость](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) как `implementation`)
