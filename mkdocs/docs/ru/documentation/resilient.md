---
description: "Explains Kora resilience aspects for circuit breakers, retries, timeouts, fallback methods, telemetry, configuration, and supported signatures. Use when working with @CircuitBreaker, @Retry, @Timeout, @Fallback, CircuitBreakerConfig, RetryConfig, TimeoutConfig, ResilientModule."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora resilience aspects for circuit breakers, retries, timeouts, fallback methods, telemetry, configuration, and supported signatures; key triggers include @CircuitBreaker, @Retry, @Timeout, @Fallback, CircuitBreakerConfig, RetryConfig, TimeoutConfig, ResilientModule."
---

Модуль для создания отказоустойчивого приложения с использованием таких механизмов, как [прерыватель](#circuitbreaker),
[резервный метод](#fallback), [повторитель](#retry) и [ограничитель времени](#timeout).
Механизмы можно применять декларативно через аннотации аспектов или напрямую через управляющие компоненты, если защита нужна в императивном коде.

`ResilientModule` объединяет модули `CircuitBreakerModule`, `RetryModule`, `TimeoutModule` и `FallbackModule`.

Если нужен пошаговый разбор перед справочным описанием, смотрите [Отказоустойчивость](../guides/resilient.md).

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

## Прерыватель { #circuitbreaker }

Прерыватель (`CircuitBreaker`) - это прокси, который контролирует поток запросов к конкретному методу
и может временно запрещать выполнение этого метода, если метод бросает много исключений, соответствующих заданным требованиям фильтра (`CircuitBreakerPredicate`).

Цель применения прерывателя — дать системе время на исправление ошибки, которая вызвала сбой, прежде чем разрешить приложению попытаться выполнить операцию еще раз. 
Шаблон `CircuitBreaker` обеспечивает стабильность, пока система восстанавливается после сбоя, и снижает влияние на производительность.
Прерыватель может находиться в нескольких состояниях в зависимости от поведения: `CLOSED`, `OPEN`, `HALF_OPEN`.

- `CLOSED`: запрос приложения передается в защищаемую операцию. Прокси считает число недавних сбоев в рамках установленного количества операций (`slidingWindowSize`), проходящих через прокси, и если вызов операции не завершился успешно, увеличивает это число.
  Если число запросов превысило минимальное количество, необходимое для расчета (`minimumRequiredCalls`), и число недавних сбоев превышает заданный порог (`failureRateThreshold`), прокси переводится в состояние `OPEN`.
- `OPEN`: Во время нахождения в таком статусе запрос от приложения немедленно завершает с ошибкой и исключение возвращается в приложение.
  На этом этапе прокси запускает таймер времени ожидания (`waitDurationInOpenState`), и по истечении времени этого таймера прокси переводится в состояние `HALF_OPEN`.
- `HALF_OPEN`: Ограниченному числу запросов (`permittedCallsInHalfOpenState`) от приложения разрешено проходить через операцию и вызывать ее. Если эти запросы выполняются успешно, предполагается, что ошибка, которая ранее вызывала
  сбой, устранена, а `CircuitBreaker` переходит в состояние `CLOSED` (счетчик сбоев сбрасывается). Если какой-либо запрос завершается со сбоем, `CircuitBreaker` предполагает, что
  неисправность все еще присутствует, поэтому возвращается в состояние `OPEN` и перезапускает таймер времени ожидания (`waitDurationInOpenState`), чтобы дать системе дополнительное время на восстановление после сбоя.

Состояние `HALF_OPEN` помогает предотвратить быстрый рост запросов к сервису: после начала восстановления сервис некоторое время может быть способен обрабатывать только ограниченное число запросов.

Изначально имеет состояние `CLOSED`.

### Декларативный подход { #declarative-usage }

Если `CircuitBreaker` находится в состоянии `OPEN`, вызов завершается исключением `CallNotPermittedException`.

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

Существует конфигурация по умолчанию, которая применяется ко всем прерывателям при создании
и затем применяются именованные настройки конкретного прерывателя для переопределения настроек по умолчанию.
Можно изменить настройки по умолчанию для всех прерывателей одновременно изменив конфигурацию по умолчанию (`default`).

Пример полной конфигурации, описанной в классе `CircuitBreakerConfig` (указаны примеры значений или значения по умолчанию):

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

    1.  Предельное количество запросов, в рамках которых рассчитывается `failureRateThreshold` для определения состояния (`обязательная`, по умолчанию не указано).
    2.  Минимальное количество запросов, необходимое для начала расчета состояния (`обязательная`, по умолчанию не указано).
    3.  Процент неуспешных запросов, необходимый для перехода в состояние `OPEN`; значение должно быть от `1` до `100` (`обязательная`, по умолчанию не указано).
    4.  Время ожидания в состоянии `OPEN`, после которого осуществляется переход в состояние `HALF_OPEN` (`обязательная`, по умолчанию не указано).
    5.  Количество запросов в состоянии `HALF_OPEN`, которые должны завершиться успехом для перехода в `CLOSED` (`обязательная`, по умолчанию не указано).
    6.  Включить или отключить `CircuitBreaker` (по умолчанию: `true`).
    7.  Имя фильтра исключений из метода `CircuitBreakerPredicate#name()` (по умолчанию учитываются все ошибки).

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

    1.  Предельное количество запросов, в рамках которых рассчитывается `failureRateThreshold` для определения состояния (`обязательная`, по умолчанию не указано).
    2.  Минимальное количество запросов, необходимое для начала расчета состояния (`обязательная`, по умолчанию не указано).
    3.  Процент неуспешных запросов, необходимый для перехода в состояние `OPEN`; значение должно быть от `1` до `100` (`обязательная`, по умолчанию не указано).
    4.  Время ожидания в состоянии `OPEN`, после которого осуществляется переход в состояние `HALF_OPEN` (`обязательная`, по умолчанию не указано).
    5.  Количество запросов в состоянии `HALF_OPEN`, которые должны завершиться успехом для перехода в `CLOSED` (`обязательная`, по умолчанию не указано).
    6.  Включить или отключить `CircuitBreaker` (по умолчанию: `true`).
    7.  Имя фильтра исключений из метода `CircuitBreakerPredicate#name()` (по умолчанию учитываются все ошибки).

Пример переопределения именованных настроек для определенного прерывателя:

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

Предоставляемые метрики модуля описаны в разделе [Справочник метрик](metrics.md#resilience).

### Фильтрация исключений { #exception-filtering }

Для регистрации какие ошибки следует записывать как ошибки со стороны прерывателя, можно переопределить фильтр по умолчанию,
требуется реализовать `CircuitBreakerPredicate` и зарегистрировать свой компонент в контексте и указать в конфигурации прерывателя его имя возвращаемое в методе `name()`.

По умолчанию прерыватель учитывает все ошибки.

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

    1. Имя фильтра исключений из метода `CircuitBreakerPredicate#name()` (по умолчанию учитываются все ошибки).

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      circuitbreaker:
        custom:
          failurePredicateName: "MyPredicate" #(1)!
    ```

    1. Имя фильтра исключений из метода `CircuitBreakerPredicate#name()` (по умолчанию учитываются все ошибки).

### Императивный подход { #imperative-usage }

Можно использовать прерыватель в императивном коде: для этого понадобится внедрить `CircuitBreakerManager`
и взять из него прерыватель по имени конфигурации, которое указывалось бы в аннотации:

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

## Повторитель { #retry }

Повторитель (`Retry`) - предоставляет возможность настраивать политику повторного вызова проаннотированных методов.
Позволяет указать, когда требуется повторить попытку выполнения метода, и настроить параметры повторения,
если метод бросил исключение, соответствующее заданным требованиям фильтра (`RetryPredicate`).

### Декларативный подход { #declarative-usage-2 }

Если все попытки исчерпаны, вызов завершается исключением `RetryExhaustedException`.

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

Существует конфигурация по умолчанию, которая применяется ко всем повторителям при создании
и затем применяются именованные настройки конкретного повторителя для переопределения настроек по умолчанию.
Можно изменить настройки по умолчанию для всех повторителей одновременно изменив конфигурацию по умолчанию (`default`).

Пример полной конфигурации, описанной в классе `RetryConfig` (указаны примеры значений или значения по умолчанию):

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

    1.  Начальное время задержки перед повторным вызовом (`обязательная`, по умолчанию не указано).
    2.  Количество повторных попыток (`обязательная`, по умолчанию не указано).
    3.  Шаг увеличения задержки для последующих попыток (по умолчанию: `0`).
    4.  Включить или отключить `Retry` (по умолчанию: `true`).
    5.  Имя фильтра исключений из метода `RetryPredicate#name()` (по умолчанию учитываются все ошибки).

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

    1.  Начальное время задержки перед повторным вызовом (`обязательная`, по умолчанию не указано).
    2.  Количество повторных попыток (`обязательная`, по умолчанию не указано).
    3.  Шаг увеличения задержки для последующих попыток (по умолчанию: `0`).
    4.  Включить или отключить `Retry` (по умолчанию: `true`).
    5.  Имя фильтра исключений из метода `RetryPredicate#name()` (по умолчанию учитываются все ошибки).

### Фильтрация исключений { #exception-filtering-2 }

Для регистрации какие ошибки следует записывать как ошибки со стороны повторителя, можно переопределить фильтр по умолчанию,
требуется реализовать `RetryPredicate` и зарегистрировать свой компонент в контексте и указать в конфигурации повторителя его имя возвращаемое в методе `name()`.

По умолчанию повторитель учитывает все ошибки.

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
    
    1. Имя фильтра исключений из метода `RetryPredicate#name()` (по умолчанию учитываются все ошибки).

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      retry:
        custom:
          failurePredicateName: "MyPredicate" #(1)!
    ```

    1. Имя фильтра исключений из метода `RetryPredicate#name()` (по умолчанию учитываются все ошибки).

### Императивный подход { #imperative-usage-2 }

Можно использовать повторитель в императивном коде: для этого понадобится внедрить `RetryManager`
и взять из него повторитель по имени конфигурации, которое указывалось бы в аннотации:

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

## Ограничитель { #timeout }

Ограничитель времени (`Timeout`) - задает максимальное время работы проаннотированного метода.

### Декларативный подход { #declarative-usage-3 }

Если метод не завершился за время `duration`, вызов завершается исключением `TimeoutExhaustedException`.

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

Существует конфигурация по умолчанию, которая применяется к ограничителю при создании
и затем применяются именованные настройки конкретного ограничителя для переопределения настроек по умолчанию.
Можно изменить настройки по умолчанию для всех ограничителей одновременно изменив конфигурацию по умолчанию (`default`).

Пример полной конфигурации, описанной в классе `TimeoutConfig` (указаны примеры значений или значения по умолчанию):

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

    1.  Предельное время работы операции, после которого будет брошен `TimeoutExhaustedException` (`обязательная`, по умолчанию не указано).
    2.  Включить или отключить `Timeout` (по умолчанию: `true`).

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      timeout:
        default:
          duration: "1s" #(1)!
          enabled: true #(2)!
    ```

    1.  Предельное время работы операции, после которого будет брошен `TimeoutExhaustedException` (`обязательная`, по умолчанию не указано).
    2.  Включить или отключить `Timeout` (по умолчанию: `true`).

### Императивный подход { #imperative-usage-3 }

Можно использовать ограничитель времени в императивном коде: для этого понадобится внедрить `TimeoutManager`
и взять из него ограничитель по имени конфигурации, которое указывалось бы в аннотации:

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

## Резервный метод { #fallback }

Резервный метод (`Fallback`) - предоставляет возможность указания метода который будет вызван в случае
если исключение брошенное проаннотированным методом будет удовлетворено фильтрам (`FallbackPredicate`).

Метод **должен совпадать** по сигнатуре возвращаемого результата.

### Декларативный подход { #declarative-usage-4 }

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

Пример резервного метода с аргументами:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @Fallback(value = "custom", method = "getFallback(arg3, arg1)") //(1)!
        public String getValue(String arg1, Integer arg2, Long arg3) {
            return "value";
        }

        protected String getFallback(Long argLong, String argString) {
            return "fallback";
        }
    }
    ```
    
    1. Передает аргументы проаннотированного метода в указанном порядке в резервный метод

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    open class SomeService {

        @Fallback(value = "custom", method = "getFallback(arg3, arg1)") //(1)! 
        fun getValue(arg1: String, arg2: Int, arg3: Long): String = "value"

        fun getFallback(argLong: Long, argString: String): String = "fallback"
    }
    ```

    1. Передает аргументы проаннотированного метода в указанном порядке в резервный метод

### Конфигурация { #configuration-4 }

Существует конфигурация по умолчанию, которая применяется ко всем резервным методам при создании
и затем применяются именованные настройки конкретного резервного метода для переопределения настроек по умолчанию.
Можно изменить настройки по умолчанию для всех резервных методов одновременно изменив конфигурацию по умолчанию (`default`).

Пример полной конфигурации, описанной в классе `FallbackConfig` (указаны примеры значений или значения по умолчанию):

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

    1. Имя фильтра исключений из метода `FallbackPredicate#name()` (по умолчанию учитываются все ошибки).
    2. Включить или отключить `Fallback` (по умолчанию: `true`).

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      fallback:
        custom:
          failurePredicateName: "MyPredicate" #(1)!
          enabled: true #(2)!
    ```

    1. Имя фильтра исключений из метода `FallbackPredicate#name()` (по умолчанию учитываются все ошибки).
    2. Включить или отключить `Fallback` (по умолчанию: `true`).

### Фильтрация исключений { #exception-filtering-3 }

Для регистрации какие ошибки следует записывать как ошибки со стороны резервного метода, можно переопределить фильтр по умолчанию,
требуется реализовать `FallbackPredicate` и зарегистрировать свой компонент в контексте 
и указать в конфигурации резервного метода его имя возвращаемое в методе `name()`.

По умолчанию резервный метод учитывает все ошибки.

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

### Императивный подход { #imperative-usage-4 }

Можно использовать резервный метод в императивном коде: для этого понадобится внедрить `FallbackManager`
и взять из него резервный метод по имени конфигурации, которое указывалось бы в аннотации:

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

## Комбинация { #combination }

Можно совмещать одновременно над одним методом все вышеперечисленные аннотации.

Порядок применения аннотаций зависит от порядка объявления аннотаций.
Вы можете поменять порядок по своему желанию и комбинировать его с другими аннотациями, которые точно также применяются в порядке объявления.

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

1. Применяется `@Timeout`, который проверяет, что метод не выполняется дольше времени, указанного в конфигурации.
2. Применяется `@Retry`, который пытается повторить выполнение метода указанное в конфигурации количество раз, если метод бросил исключение по цепочке, включая исключение от `@Timeout`.
3. Применяется `@CircuitBreaker`, который работает согласно конфигурации и [состоянию](#circuitbreaker) в зависимости от успешного результата метода или исключения по цепочке, включая исключения от `@Timeout` и `@Retry`.
4. Применяется `@Fallback`, который вызывает метод `getFallback` с аргументом `arg1`, если метод бросил исключение по цепочке, включая исключения от `@Timeout`, `@Retry` и `@CircuitBreaker`.

Порядок вызова аспектов соответствует порядку аннотаций над методом: сверху вниз.

Пример конфигурации всех аспектов:

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

## Сигнатуры { #signatures }

Доступные сигнатуры для методов которые поддерживают аннотации из коробки:
Все четыре аннотации поддерживают обычные синхронные методы, асинхронные типы и реактивные типы, но фактический набор зависит от языка и используемого обработчика.

===! ":fontawesome-brands-java: `Java`"

    Класс не должен быть `final`, чтобы аспекты работали.

    Под `T` подразумевается тип возвращаемого значения.

    - `void myMethod()`
    - `T myMethod()`
    - `Optional<T> myMethod()`
    - `CompletionStage<T> myMethod()` / `CompletableFuture<T> myMethod()` ([CompletionStage](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletionStage.html))
    - `Mono<T> myMethod()` ([Project Reactor](https://projectreactor.io/docs/core/release/reference/), требуется [зависимость](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))
    - `Flux<T> myMethod()` ([Project Reactor](https://projectreactor.io/docs/core/release/reference/), требуется [зависимость](https://mvnrepository.com/artifact/io.projectreactor/reactor-core))

=== ":simple-kotlin: `Kotlin`"

    Класс должен быть `open`, чтобы аспекты работали.

    Под `T` подразумевается тип возвращаемого значения, либо `T?`, либо `Unit`.

    - `myMethod(): T`
    - `suspend myMethod(): T` ([Kotlin Coroutines](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine), требуется [зависимость](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) как `implementation`)
    - `myMethod(): Flow<T>` ([Kotlin Coroutines](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine), требуется [зависимость](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) как `implementation`)
