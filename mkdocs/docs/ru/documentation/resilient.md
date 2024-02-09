Модуль для создания отказоустойчивого приложения с использованием таких подходов как [прерыватель](#_2), 
[резервный метод](#_16), [повторитель](#_7) и [ограничитель выполнения по времени](#_12) с помощью аннотаций в декларативном стиле.

## Подключение

=== ":fontawesome-brands-java: `Java`"

    Зависимость `build.gradle`:
    ```groovy
    annotationProcessor "ru.tinkoff.kora:annotation-processors"
    implementation "ru.tinkoff.kora:resilient-kora"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends ResilientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Зависимость `build.gradle.kts`:
    ```groovy
    ksp("ru.tinkoff.kora:symbol-processors")
    implementation("ru.tinkoff.kora:resilient-kora")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : ResilientModule
    ```

## Прерыватель

Прерыватель (`CircuitBreaker`) – это прокси, который контролирует поток к запросам конкретного метода
и может прекращать временно выполнение этого метода если метод бросает много исключений.

Цель применения прерывателя — дать системе время на исправление ошибки, которая вызвала сбой, прежде чем разрешить приложению попытаться выполнить операцию еще раз. 
Шаблон прерыватель обеспечивает стабильность, пока система восстанавливается после сбоя и снижает влияние на производительность.
Прерыватель может находиться в нескольких состояниях в зависимости от поведения (`OPEN, CLOSED, HALF_OPEN`) 

- `CLOSED`: Запрос приложения перенаправляется на операцию. Прокси ведет подсчет числа недавних сбоев в рамках установленного кол-ва операций (`slidingWindowSize`) поступающих через прокси, и если вызов операции не завершился успешно, прокси увеличивает это число. 
  Если число запросов превысило установленный минимальный потолок необходимый для подсчетов (`minimumRequiredCalls`) и число недавних сбоев превышает заданный порог (`failureRateThreshold`) в течение заданного периода времени, прокси переводится в состояние `OPEN`. 
- `OPEN`: Во время нахождения в таком статусе запрос от приложения немедленно завершает с ошибкой и исключение возвращается в приложение.
  На этом этапе прокси запускает таймер времени ожидания (`waitDurationInOpenState`), и по истечении времени этого таймера прокси переводится в состояние `HALF-OPEN`.
- `HALF-OPEN`: Ограниченному числу запросов (`permittedCallsInHalfOpenState`) от приложения разрешено проходить через операцию и вызывать ее. Если эти запросы выполняются успешно, предполагается, что ошибка, которая ранее вызывала
  сбой, устранена, а автоматический выключатель переходит в состояние `CLOSED` (счетчик сбоев сбрасывается). Если какой-либо запрос завершается со сбоем, автоматическое выключение предполагает, что
  неисправность все еще присутствует, поэтому он возвращается в состояние `OPEN` и перезапускает таймер времени ожидания (`waitDurationInOpenState`), чтобы дать системе дополнительное время на восстановление после сбоя.

Состояние `HALF-OPEN` помогает предотвратить быстрый рост запросов к сервису. Т.к. после начала работы сервиса, некоторое время он может быть способен обрабатывать ограниченное число запросов до полного
восстановления.

Изначально имеет состояние `CLOSED`.

### Декларативный подход

=== ":fontawesome-brands-java: `Java`"

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

### Конфигурация

Существует конфигурация по умолчанию, которая применяется ко всем прерывателям при создании
и затем применяются именованные настройки конкретного прерывателя для переопределения настроек по умолчанию.
Можно изменить настройки по умолчанию для всех прерывателей одновременно изменив конфигурацию по умолчанию (`default`).

Параметры, описанные в классе `CircuitBreakerConfig`:

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
        circuitbreaker {
            default {
                slidingWindowSize = 100 //(1)!
                minimumRequiredCalls = 50 //(2)!
                failureRateThreshold = 50 //(3)!
                waitDurationInOpenState = "25s" //(4)!
                permittedCallsInHalfOpenState = 10 //(5)!
            }
        }
    }
    ```

    1.  Предельное кол-во запросов в рамках которых рассчитывается *failureRateThreshold* для определения состояния
    2.  Минимальное кол-во запросов необходимое для начала расчета состояния
    3.  Процент неуспешных запросов который необходим для перехода в состояния **OPEN** (имеет значения от *1 до 100*)
    4.  Время ожидания в статусе **OPEN**, после которого осуществляется переход в статус **HALF-OPEN**
    5.  Необходимое кол-во запросов в статусе **HALF-OPEN** которые должны завершится успехом для перехода в **CLOSED**

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      circuitbreaker:
        default:
          slidingWindowSize: 100 #(1)!
          minimumRequiredCalls: 50 #(2)!
          failureRateThreshold: 50 #(3)!
          waitDurationInOpenState: "25s" #(4)!
          permittedCallsInHalfOpenState: 10 #(5)!
    ```

    1.  Предельное кол-во запросов в рамках которых рассчитывается *failureRateThreshold* для определения состояния CircuitBreaker
    2.  Минимальное кол-во запросов необходимое для начала расчета состояния CircuitBreaker
    3.  Процент неуспешных запросов который необходим для перехода в состояния **OPEN** (имеет значения от *1 до 100*)
    4.  Время ожидания в статусе **OPEN**, после которого осуществляется переход в статус **HALF-OPEN**
    5.  Необходимое кол-во запросов в статусе **HALF-OPEN** которые должны завершится успехом для перехода в **CLOSED**

Пример переопределения именованных настроек для определенного CircuitBreaker'а:

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

### Фильтрация исключений

Для регистрации какие ошибки следует записывать как ошибки со стороны CircuitBreaker, можно переопределить фильтр по умолчанию,
требуется реализовать `CircuitBreakerPredicate` и зарегистрировать свой компонент в контексте и указать в конфигурации CircuitBreaker его имя возвращаемое в методе `name()`.

=== ":fontawesome-brands-java: `Java`"

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
                failurePredicateName = "MyPredicate"
            }
        }
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      circuitbreaker:
        custom:
          failurePredicateName: "MyPredicate"
    ```

### Императивный подход

Можно использовать прерыватель в императивном коде, для этого понадобиться внедрить как зависимость `CircuitBreakerManager`
и взять из него `CircuitBreaker` по имени конфигурации которая указывалась бы в аннотации:

=== ":fontawesome-brands-java: `Java`"

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

## Повторитель

Повторитель (`Retry`) - предоставляет возможность настраивать политику повторного вызова проаннотированных методов.
Позволяет указать когда требуется повторить попытку выполнения метода, настроить параметры повторения, 
в случае если методом было брошено исключение соответствующая заданным требованиям фильтра (*RetrierFailurePredicate*).

### Декларативный подход

=== ":fontawesome-brands-java: `Java`"

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

### Конфигурация

Существует конфигурация по умолчанию, которая применяется ко всем повторителям при создании
и затем применяются именованные настройки конкретного повторителя для переопределения настроек по умолчанию.
Можно изменить настройки по умолчанию для всех повторителей одновременно изменив конфигурацию по умолчанию (`default`).

Параметры, описанные в классе `RetryConfig`:

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
        retry {
            default {
                delay = "100ms" //(1)!
                attempts = 2 //(2)!
                delayStep = "100ms" //(3)!
                failurePredicateName = "MyPredicate" //(4)!
            }
        }
    }
    ```

    1.  Начальное время задержки для операции при Retry
    2.  Кол-во попыток Retry для операции
    3.  Шаг задержки который аккумулируется в следствии последующих попыток Retry
    4.  Имя предиката который будет регистрировать ошибки подходящие под требования Retry

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      retry:
        default:
          delay: "100ms" #(1)!
          attempts: 2 #(2)!
          delayStep: "100ms" #(3)!
          failurePredicateName: "MyPredicate" #(4)!
    ```

    1.  Начальное время задержки для операции при Retry
    2.  Кол-во попыток Retry для операции
    3.  Шаг задержки который аккумулируется в следствии последующих попыток Retry
    4.  Имя предиката который будет регистрировать ошибки подходящие под требования Retry

### Фильтрация исключений

Для регистрации какие ошибки следует записывать как ошибки со стороны повторителя, можно переопределить фильтр по умолчанию,
требуется реализовать `RetryPredicate` и зарегистрировать свой компонент в контексте и указать в конфигурации повторителя его имя возвращаемое в методе `name()`.

=== ":fontawesome-brands-java: `Java`"

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
                failurePredicateName = "MyPredicate"
            }
        }
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      retry:
        custom:
          failurePredicateName: "MyPredicate"
    ```

### Императивный подход

Можно использовать повторитель в императивном коде, для этого понадобиться внедрить как зависимость `RetryManager`
и взять из него `Retry` по имени конфигурации которая указывалась бы в аннотации:

=== ":fontawesome-brands-java: `Java`"

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

## Ограничитель времени

Ограничитель времени (`Timeout`) - предоставляет возможность задавать максимальное время работы проаннотированного метода.

### Декларативный подход

=== ":fontawesome-brands-java: `Java`"

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

### Конфигурация

Существует конфигурация по умолчанию, которая применяется к ограничителю при создании
и затем применяются именованные настройки конкретного ограничителя для переопределения настроек по умолчанию.
Можно изменить настройки по умолчанию для всех ограничителей одновременно изменив конфигурацию по умолчанию (`default`).

Параметры, описанные в классе `TimeoutConfig`:

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
        timeout {
            default {
                duration = "1s" //(1)!
            }
        }
    }
    ```

    1.  Предельное время работы операции после которого будет брошен TimeoutExhaustedException.

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      timeout:
        default:
          delay: "1s" #(1)!
    ```

    1.  Предельное время работы операции после которого будет брошен TimeoutExhaustedException.

### Императивный подход

Можно использовать ограничитель времени в императивном коде, для этого понадобиться внедрить как зависимость `TimeoutManager`
и взять из него `Timeout` по имени конфигурации которая указывалась бы в аннотации:

=== ":fontawesome-brands-java: `Java`"

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

## Резервный метод

Резервный метод (`Fallback`) - предоставляет возможность указания метода который будет вызван в случае
если исключение брошенное проаннотированным методом будет удовлетворено фильтрам (*FallbackFailurePredicate*).

Метод **должен совпадать** по сигнатуре возвращаемого результата.

### Декларативный подход

Пример резервного метода без аргументов:

=== ":fontawesome-brands-java: `Java`"

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

        fun fallback(): String = "fallback"
    }
    ```

Пример резервного метода с аргументами:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @Fallback(value = "custom", method = "getFallback(arg3, arg1)")     // Передает аргументы проаннотированного метода в указанном порядке в Fallback метод
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

        // Передает аргументы проаннотированного метода в указанном порядке в Fallback метод
        @Fallback(value = "custom", method = "getFallback(arg3, arg1)")
        fun getValue(arg1: String, arg2: Int, arg3: Long): String = "value"

        fun getFallback(argLong: Long, argString: String): String = "fallback"
    }
    ```

### Конфигурация

Существует конфигурация по умолчанию, которая применяется ко всем резервным метода при создании
и затем применяются именованные настройки конкретного резервного метода для переопределения настроек по умолчанию.
Можно изменить настройки по умолчанию для всех резервных методов одновременно изменив конфигурацию по умолчанию (`default`).

Параметры, описанные в классе `FallbackConfig`:

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
        fallback {
            custom {
                failurePredicateName = "MyPredicate"
            }
        }
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      fallback:
        custom:
          failurePredicateName: "MyPredicate"
    ```

### Фильтрация исключений

Для регистрации какие ошибки следует записывать как ошибки со стороны резервного метода, можно переопределить фильтр по умолчанию,
требуется реализовать `FallbackPredicate` и зарегистрировать свой компонент в контексте 
и указать в конфигурации резервного метода его имя возвращаемое в методе `name()`.

=== ":fontawesome-brands-java: `Java`"

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

### Императивный подход

Можно использовать резервный метод в императивном коде, для этого понадобиться внедрить как зависимость `FallbackManager`
и взять из него `Fallback` по имени конфигурации которая указывалась бы в аннотации:

=== ":fontawesome-brands-java: `Java`"

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

## Комбинация

Можно совмещать одновременно над одним методом все вышеперечисленные аннотации.

Порядок применения аннотаций зависит от порядка объявления аннотаций.
Вы можете поменять порядок по своему желанию и комбинировать его с другими аннотациями, которые точно также применяются в порядке объявления.

=== ":fontawesome-brands-java: `Java`"

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

1. Применяется `@Timeout` который, говорит что метод не должен выполняться дольше времени указанного в конфигурации
2. Применяется `@Retry` который будет пытаться повторить выполнение метода указанное в конфигурации кол-во раз в случае, если метод бросил исключение по цепочке (включая `@Timeout`)
3. Применяется `@CircuitBreaker` который будет работать согласно конфигурации и [состоянию](#circuitbreaker) в зависимости успешного результата метода или если метод бросил исключение по цепочке (включая `@Timeout` & `@Retry`)
4. Применяется `@Fallback` который будет вызвать `getFallback` метод с аргументом `arg1` в случае если метод бросил исключение по цепочке (включая `@Timeout` & `@Retry` & `@CircuitBreaker`)

Порядок вызова аспектов соответствует порядку аннотаций над методом, сверху внизу.

Пример конфигурации:

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

## Сигнатуры

Доступные сигнатуры для методов которые поддерживают аннотации из коробки:

=== ":fontawesome-brands-java: `Java`"

    Под `T` подразумевается тип возвращаемого значения, либо `Void`.

    - `T myMethod()`
    - `Optional<T> myMethod()`
    - `CompletionStage<T> myMethod()` [CompletionStage](https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/CompletionStage.html)
    - `Mono<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/)
    - `Flux<T> myMethod()` [Project Reactor](https://projectreactor.io/docs/core/release/reference/)

=== ":simple-kotlin: `Kotlin`"

    Под `T` подразумевается тип возвращаемого значения, либо `Unit`.

    - `myMethod(): T`
    - `myMethod(): T?`
    - `suspend myMethod(): T` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine)
    - `suspend myMethod(): T?` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine)
    - `myMethod(): Flow<T>` [Kotlin Coroutine](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine)
