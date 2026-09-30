---
seo_title: "Отказоустойчивость Kora: circuit breaker, retry, таймауты"
seo_description: "Справочник по отказоустойчивости Kora: circuit breaker, повторы с backoff и jitter, таймауты, rate limiter, fallback, фильтры исключений, конфигурация."
keywords: ["Kora Framework", "фреймворк Kora", "отказоустойчивость Kora", "circuit breaker", "retry", "rate limiter", "распределённый rate limiter", "retry budget"]
description: "Explains Kora resilience aspects built on typed specification interfaces: circuit breakers, retries with backoff/jitter/budget, timeouts, rate limiters (token bucket or fixed window, local or Redis-backed distributed), distributed retry budgets, fallback methods, exception filtering, telemetry, configuration, and supported signatures. Use when working with @CircuitBreakable, @Retryable, @Timeout, @RateLimited, @Fallback, @CircuitBreakerSpec, @RetrySpec, @TimeoutSpec, @RateLimiterSpec, @RateLimiterDistributedSpec, NonRetryableException, NonCircuitableException, RetryBudgetFactory, ResilientModule, LettuceDistributedResilientModule."
agent:
  use_when: "Use this file for Kora docs or implementation questions about resilience aspects bound to typed specification interfaces, circuit breaker implementations, retry backoff/jitter/budget, custom and distributed retry budgets, timeouts, rate limiting algorithms (TOKEN_BUCKET default, FIXED_WINDOW), distributed Redis-backed rate limiting, fallback methods, exception filtering, telemetry and supported signatures; key triggers include @CircuitBreakable, @CircuitBreakerSpec, @Retryable, @RetrySpec, @Timeout, @TimeoutSpec, @RateLimited, @RateLimiterSpec, @RateLimiterDistributedSpec, @Fallback, Fallback.Reason, CircuitBreaker, CircuitBreakerPredicate, NonCircuitableException, Retry, RetryPredicate, NonRetryableException, RetryBudget, KoraRetryBudget, RetryBudgetFactory, DistributedRetryBudgetFactory, Timeouter, RateLimiter, RateLimiterConfig.type, DistributedRateLimiterConfig, DistributedRateLimiterClient, LettuceDistributedResilientModule, resilient-kora-distributed-redis-lettuce, CallNotPermittedException, RetryExhaustedException, TimeoutExhaustedException, RateLimitExceededException, ResilientException, ResilientModule."
---

Модуль для построения отказоустойчивого приложения с помощью таких механизмов, как [CircuitBreaker](#circuitbreaker),
[Retry](#retry), [Timeout](#timeout), [RateLimiter](#ratelimiter) и [Fallback](#fallback).

Каждый механизм, кроме `Fallback`, описывается [интерфейсом-спецификацией](#specifications) — типизированным контрактом,
который указывает на путь в конфигурации. Аннотация на защищаемом методе ссылается на этот интерфейс, поэтому связь
метода с его настройками отказоустойчивости проверяет компилятор, а не строковое совпадение имён.

`ResilientModule` объединяет `CircuitBreakerModule`, `RetryModule`, `TimeoutModule`, `FallbackModule` и `RateLimiterModule`.

Пошаговое введение перед справочником — в разделе [Отказоустойчивость](../guides/resilient.md).

## Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:resilient-kora"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends ResilientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:resilient-kora")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : ResilientModule
    ```

Обработчик аннотаций (`annotation-processors`) либо `KSP`-обработчик (`symbol-processors`) обязателен: он одновременно
генерирует реализации спецификаций и применяет аспекты.

### Распределённое состояние { #dependency-distributed }

По умолчанию каждый ограничитель частоты и бюджет повторов хранит своё состояние в памяти одного экземпляра приложения.
[Распределённый rate limiter](#ratelimiter-distributed) и [распределённый бюджет повторов](#retry-budget-factory) делят это
состояние между экземплярами через `Redis`. Для них нужен дополнительный модуль на клиенте `Lettuce`:

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:resilient-kora-distributed-redis-lettuce"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends ResilientModule, LettuceDistributedResilientModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:resilient-kora-distributed-redis-lettuce")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : ResilientModule, LettuceDistributedResilientModule
    ```

Артефакт подтягивает `resilient-kora-distributed` (независимые от хранилища контракты `DistributedRateLimiterClient` и
`DistributedRetryBudgetClient`, алгоритмы и `@RateLimiterDistributedSpec`) и `redis-lettuce`.
`LettuceDistributedResilientModule` расширяет `LettuceModule`, поэтому подключение настраивается в секции `lettuce`
так же, как для [кеша Redis](cache.md#configuration-2). Поддерживаются и одиночный, и кластерный клиент, а все
операции выполняются обычными командами `Redis` без серверных `Lua`-скриптов.

Чтобы выделить компонентам отказоустойчивости собственный клиент Redis вместо общего, зарегистрируйте `AbstractRedisClient`
с тегом `@Tag(LettuceDistributedResilientModule.class)`.

## Спецификации { #specifications }

Спецификация — это интерфейс, который наследует контракт отказоустойчивости и помечен аннотацией с путём конфигурации:

| Аннотация метода   | Аннотация спецификации   | Контракт, который наследует интерфейс | Пакет                                          |
|--------------------|--------------------------|---------------------------------------|------------------------------------------------|
| `@CircuitBreakable` | `@CircuitBreakerSpec`    | `CircuitBreaker`                      | `io.koraframework.resilient.circuitbreaker`     |
| `@Retryable`       | `@RetrySpec`             | `Retry`                               | `io.koraframework.resilient.retry`              |
| `@Timeout`         | `@TimeoutSpec`           | `Timeouter`                           | `io.koraframework.resilient.timeout`            |
| `@RateLimited`     | `@RateLimiterSpec`       | `RateLimiter`                         | `io.koraframework.resilient.ratelimiter`        |
| `@Fallback`        | —                        | —                                     | `io.koraframework.resilient.fallback.annotation` |

Аннотации методов лежат в подпакете `annotation` рядом с контрактом, например
`io.koraframework.resilient.circuitbreaker.annotation.CircuitBreakable`.

`@RateLimited` также принимает интерфейс с аннотацией `@RateLimiterDistributedSpec`
(`io.koraframework.resilient.distributed.ratelimiter.annotation`), лимит которого общий для всех экземпляров — см.
[Распределённый rate limiter](#ratelimiter-distributed).

===! ":fontawesome-brands-java: `Java`"

    ```java
    @CircuitBreakerSpec("resilient.circuitbreaker.pet") //(1)!
    public interface PetCircuitBreaker extends CircuitBreaker { }

    @RetrySpec("resilient.retry.pet")
    public interface PetRetry extends Retry { }

    @TimeoutSpec("resilient.timeout.pet")
    public interface PetTimeouter extends Timeouter { }

    @Component
    public class PetService {

        @CircuitBreakable(PetCircuitBreaker.class) //(2)!
        @Retryable(PetRetry.class)
        @Timeout(PetTimeouter.class)
        public Optional<Pet> findById(long id) {
            return petRepository.findById(id);
        }
    }
    ```

    1.  Полный путь секции конфигурации, которая описывает этот экземпляр.
    2.  Аспект связывается с типом спецификации, а не со строковым именем.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @CircuitBreakerSpec("resilient.circuitbreaker.pet") //(1)!
    interface PetCircuitBreaker : CircuitBreaker

    @RetrySpec("resilient.retry.pet")
    interface PetRetry : Retry

    @TimeoutSpec("resilient.timeout.pet")
    interface PetTimeouter : Timeouter

    @Component
    open class PetService {

        @CircuitBreakable(PetCircuitBreaker::class) //(2)!
        @Retryable(PetRetry::class)
        @Timeout(PetTimeouter::class)
        open fun findById(id: Long): Pet? = petRepository.findById(id)
    }
    ```

    1.  Полный путь секции конфигурации, которая описывает этот экземпляр.
    2.  Аспект связывается с типом спецификации, а не со строковым именем.

Что обработчик делает со спецификацией:

- генерирует её реализацию и модуль, который её публикует; модуль подхватывается `@KoraApp` автоматически — вручную ничего подключать не нужно;
- публикует сам интерфейс спецификации как компонент графа приложения, поэтому его можно внедрить для [императивного использования](#imperative-usage);
- читает конфигурацию ровно из того пути, который указан в аннотации.

Сгенерированные реализации наследуют `toString()`, который выводит текущее состояние — состояние прерывателя и его счётчики,
оставшиеся разрешения локального rate limiter, настройки повтора и токены бюджета повторов, — поэтому по записи внедрённой спецификации
в лог или по её виду в отладчике видно, что она делает прямо сейчас.

!!! warning "Один экземпляр на спецификацию"

    Все методы, помеченные одной и той же спецификацией, разделяют **один** экземпляр, а значит одно состояние и один
    набор метрик. Если два метода не должны влиять на состояние circuit breaker друг друга, им нужны два интерфейса-спецификации,
    указывающих на две разные секции конфигурации.

!!! warning "Путь конфигурации абсолютный и ни с чем не объединяется"

    Путь в аннотации — это полный путь до секции. Секции `default`, от которой наследуется именованная секция, больше нет:
    все обязательные значения должны присутствовать именно по этому пути. Подойдёт любой путь, в том числе вне префикса
    `resilient` — `@CircuitBreakerSpec("payment")` читает корневую секцию `payment`.

Типичные ошибки компиляции:

- `@CircuitBreakerSpec can only be applied to an interface` — аннотация поставлена на класс или запись.
- `@CircuitBreakerSpec annotated interface 'X' must extend io.koraframework.resilient.circuitbreaker.CircuitBreaker` — интерфейс не наследует контракт.
- `config path can't be blank` — в значении аннотации пустая строка.
- `@CircuitBreakable on 'X#y()' references an invalid resilient component type` — класс, переданный в аннотацию метода, не реализует ожидаемый контракт.

## CircuitBreaker { #circuitbreaker }

`CircuitBreaker` — это прокси, который управляет потоком запросов к конкретному методу
и может временно запретить его выполнение, если метод бросает много исключений, подходящих под настроенный фильтр.

Смысл применения CircuitBreaker в том, чтобы дать системе время исправить ошибку, вызвавшую сбой, прежде чем позволить приложению повторить операцию.
Шаблон `CircuitBreaker` обеспечивает стабильность на время восстановления системы после сбоя и снижает влияние на производительность.
`CircuitBreaker` может находиться в одном из состояний: `CLOSED`, `OPEN`, `HALF_OPEN`.

- `CLOSED`: запрос приложения передаётся в защищаемую операцию. Прокси считает недавние отказы в пределах настроенного количества операций (`countBased.windowSize`), проходящих через него, и увеличивает счётчик, когда операция завершается неуспешно.
  Если число запросов превысило минимально необходимое для расчёта (`minimumRequiredCalls`), а доля недавних отказов превысила настроенный порог (`failureRateThreshold`), прокси переходит в `OPEN`.
- `OPEN`: в этом состоянии запрос приложения немедленно завершается ошибкой, и приложению возвращается исключение.
  В этот момент прокси запускает таймер ожидания (`waitDurationInOpenState`), по истечении которого переходит в `HALF_OPEN`.
- `HALF_OPEN`: ограниченному числу запросов (`permittedCallsInHalfOpenState`) разрешается пройти и вызвать операцию. Если эти запросы успешны, считается, что ошибка,
  ранее вызвавшая сбой, устранена, и `CircuitBreaker` переходит в состояние `CLOSED` (счётчик отказов сбрасывается). Если хотя бы один запрос завершается отказом, `CircuitBreaker` считает,
  что неисправность сохраняется, возвращается в состояние `OPEN` и перезапускает таймер ожидания (`waitDurationInOpenState`), давая системе дополнительное время на восстановление.

Состояние `HALF_OPEN` помогает избежать лавинообразного роста запросов к сервису: после начала восстановления сервис какое-то время может выдерживать лишь ограниченное число запросов.

Изначально находится в состоянии `CLOSED`.

### Декларативное использование { #declarative-usage }

Если `CircuitBreaker` находится в состоянии `OPEN`, вызов завершается исключением `CallNotPermittedException`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @CircuitBreakerSpec("resilient.circuitbreaker.custom")
    public interface CustomCircuitBreaker extends CircuitBreaker { }

    @Component
    public class SomeService {

        @CircuitBreakable(CustomCircuitBreaker.class)
        public String getValue() {
            throw new IllegalStateException("Ops");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @CircuitBreakerSpec("resilient.circuitbreaker.custom")
    interface CustomCircuitBreaker : CircuitBreaker

    @Component
    open class SomeService {

        @CircuitBreakable(CustomCircuitBreaker::class)
        open fun value(): String = throw IllegalStateException("Ops")
    }
    ```

### Конфигурация { #configuration }

Секция, на которую указывает `@CircuitBreakerSpec`, описана в классе `CircuitBreakerConfig`:

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
        circuitbreaker {
            custom {
                type = STRIPED_APPROX //(1)!
                failureRateThreshold = 50 //(2)!
                minimumRequiredCalls = 10 //(3)!
                waitDurationInOpenState = "25s" //(4)!
                permittedCallsInHalfOpenState = 15 //(5)!
                enabled = true //(6)!
                countBased {
                    windowSize = 100 //(7)!
                    stripedApprox {
                        stripes = 16 //(8)!
                    }
                }
            }
        }
    }
    ```

    1.  [Реализация](#circuitbreaker-implementations) окна вызовов: `STRIPED_APPROX`, `FIXED_WINDOW`, `RING_BUFFER` или `TIME_BASED` (по умолчанию: `STRIPED_APPROX`).
    2.  Процент неуспешных запросов, необходимый для перехода в `OPEN`; значение должно быть от `1` до `100` (обязательное, без значения по умолчанию).
    3.  Минимальное число запросов, необходимое для начала расчёта состояния (обязательное, без значения по умолчанию).
    4.  Время ожидания в `OPEN`, по истечении которого выполняется переход в `HALF_OPEN` (обязательное, без значения по умолчанию).
    5.  Число запросов в `HALF_OPEN`, которые должны завершиться успешно для перехода в `CLOSED` (обязательное, без значения по умолчанию).
    6.  Включение или отключение `CircuitBreaker` (по умолчанию: `true`).
    7.  Максимальное число запросов, используемых для расчёта `failureRateThreshold` и определения состояния (обязательное для всех типов, кроме `TIME_BASED`, без значения по умолчанию).
    8.  Количество независимых полос счётчиков, от `1` до `64`; используется только реализацией `STRIPED_APPROX` (по умолчанию: `16`).

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      circuitbreaker:
        custom:
          type: STRIPED_APPROX #(1)!
          failureRateThreshold: 50 #(2)!
          minimumRequiredCalls: 10 #(3)!
          waitDurationInOpenState: "25s" #(4)!
          permittedCallsInHalfOpenState: 15 #(5)!
          enabled: true #(6)!
          countBased:
            windowSize: 100 #(7)!
            stripedApprox:
              stripes: 16 #(8)!
    ```

    1.  [Реализация](#circuitbreaker-implementations) окна вызовов: `STRIPED_APPROX`, `FIXED_WINDOW`, `RING_BUFFER` или `TIME_BASED` (по умолчанию: `STRIPED_APPROX`).
    2.  Процент неуспешных запросов, необходимый для перехода в `OPEN`; значение должно быть от `1` до `100` (обязательное, без значения по умолчанию).
    3.  Минимальное число запросов, необходимое для начала расчёта состояния (обязательное, без значения по умолчанию).
    4.  Время ожидания в `OPEN`, по истечении которого выполняется переход в `HALF_OPEN` (обязательное, без значения по умолчанию).
    5.  Число запросов в `HALF_OPEN`, которые должны завершиться успешно для перехода в `CLOSED` (обязательное, без значения по умолчанию).
    6.  Включение или отключение `CircuitBreaker` (по умолчанию: `true`).
    7.  Максимальное число запросов, используемых для расчёта `failureRateThreshold` и определения состояния (обязательное для всех типов, кроме `TIME_BASED`, без значения по умолчанию).
    8.  Количество независимых полос счётчиков, от `1` до `64`; используется только реализацией `STRIPED_APPROX` (по умолчанию: `16`).

Ключ `telemetry` внутри той же секции переопределяет общемодульные настройки из раздела [Телеметрия](#telemetry).

!!! warning "Ограничения"

    Перечисленное ниже проверяется при построении графа — нарушение любого правила прерывает старт приложения
    с явным сообщением вида `CircuitBreaker '<name>' property '<key>' ...`:
    `countBased` обязателен для всех типов, кроме `TIME_BASED`, а `timeBased` обязателен для `TIME_BASED`;
    `failureRateThreshold` в диапазоне `1..100`; `countBased.windowSize` ≥ `1`; `minimumRequiredCalls` ≥ `1`
    **и** ≤ `countBased.windowSize`; `permittedCallsInHalfOpenState` в диапазоне `1..65535`;
    `waitDurationInOpenState` не может быть отрицательным;
    `countBased.stripedApprox.stripes` в диапазоне `1..64`, а `countBased.windowSize` не может превышать `stripes * 65535`;
    для `RING_BUFFER` значение `countBased.windowSize` не может превышать `4194304`.

!!! note

    Значение `enabled = false` превращает аспект в прозрачный проброс — метод вызывается напрямую без защиты.
    Остальные значения при этом всё равно читаются и валидируются, потому что объект конфигурации создаётся в любом случае.

Метрики модуля описаны в разделе [Справочник метрик](metrics.md#resilience).

### Реализации { #circuitbreaker-implementations }

`type` выбирает способ сбора статистики в состоянии `CLOSED`. Сама машина состояний во всех четырёх реализациях одинакова и строго атомарна.

| `type`           | Окно                                 | Статистика                                               | Когда использовать                                                        |
|------------------|--------------------------------------|-----------------------------------------------------------|---------------------------------------------------------------------------|
| `STRIPED_APPROX` | по числу вызовов, `countBased.windowSize` | приблизительная — запись распределяется по независимым полосам | по умолчанию; самый быстрый вариант на горячих и высоконагруженных путях   |
| `FIXED_WINDOW`   | по числу вызовов, `countBased.windowSize` | фиксированный счётчик, сбрасываемый при заполнении окна   | минимальные накладные расходы, один упакованный счётчик, без точной истории последних N вызовов |
| `RING_BUFFER`    | по числу вызовов, `countBased.windowSize` | точная история последних N вызовов в глобальном порядке   | когда точная семантика по числу вызовов важнее накладных расходов на синхронизацию |
| `TIME_BASED`     | по времени, `timeBased.windowDuration` | последнее временное окно, согласованность в пределах смены корзины | когда интенсивность нагрузки меняется и фиксированное число вызовов не является осмысленным окном |

`TIME_BASED` игнорирует `countBased` и читает собственную секцию:

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
        circuitbreaker {
            custom {
                type = TIME_BASED
                failureRateThreshold = 50
                minimumRequiredCalls = 10
                waitDurationInOpenState = "25s"
                permittedCallsInHalfOpenState = 15
                timeBased {
                    windowDuration = "10s" //(1)!
                    sampleCount = 16 //(2)!
                    counterStripes = 16 //(3)!
                    counterType = ATOMIC //(4)!
                }
            }
        }
    }
    ```

    1.  Длительность временного окна, по которому считается доля отказов (обязательное для `TIME_BASED`, без значения по умолчанию).
    2.  Число корзин, на которые делится окно, от `1` до `1024` (по умолчанию: `16`).
    3.  Число независимых полос счётчиков внутри корзины, от `1` до `64` (по умолчанию: `16`).
    4.  Реализация счётчиков: `ATOMIC` даёт предсказуемый сброс, `LONG_ADDER` быстрее при высокой конкуренции ценой более приблизительного сброса на границах корзин (по умолчанию: `ATOMIC`).

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      circuitbreaker:
        custom:
          type: TIME_BASED
          failureRateThreshold: 50
          minimumRequiredCalls: 10
          waitDurationInOpenState: "25s"
          permittedCallsInHalfOpenState: 15
          timeBased:
            windowDuration: "10s" #(1)!
            sampleCount: 16 #(2)!
            counterStripes: 16 #(3)!
            counterType: ATOMIC #(4)!
    ```

    1.  Длительность временного окна, по которому считается доля отказов (обязательное для `TIME_BASED`, без значения по умолчанию).
    2.  Число корзин, на которые делится окно, от `1` до `1024` (по умолчанию: `16`).
    3.  Число независимых полос счётчиков внутри корзины, от `1` до `64` (по умолчанию: `16`).
    4.  Реализация счётчиков: `ATOMIC` даёт предсказуемый сброс, `LONG_ADDER` быстрее при высокой конкуренции ценой более приблизительного сброса на границах корзин (по умолчанию: `ATOMIC`).

### Фильтрация исключений { #exception-filtering }

По умолчанию `CircuitBreaker` считает отказом любую ошибку, кроме исключений, реализующих интерфейс-маркер
`NonCircuitableException`. Пометить им собственный тип исключения — самый простой способ не пускать ожидаемую бизнес-ошибку
в статистику прерывателя, а тот же тип может реализовать и `NonRetryableException`, чтобы не попадать под
[Retry](#exception-filtering-2):

===! ":fontawesome-brands-java: `Java`"

    ```java
    public final class InvalidPetException extends RuntimeException
        implements NonCircuitableException, NonRetryableException { //(1)!

        public InvalidPetException(String message) {
            super(message);
        }
    }
    ```

    1.  `io.koraframework.resilient.circuitbreaker.NonCircuitableException` и `io.koraframework.resilient.retry.NonRetryableException` — интерфейсы-маркеры без методов.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    class InvalidPetException(message: String) : RuntimeException(message),
        NonCircuitableException, NonRetryableException //(1)!
    ```

    1.  `io.koraframework.resilient.circuitbreaker.NonCircuitableException` и `io.koraframework.resilient.retry.NonRetryableException` — интерфейсы-маркеры без методов.

Если решение нельзя выразить через тип исключения, изменить поведение по умолчанию можно двумя способами.

Первый — переопределить `isFailure` прямо в интерфейсе-спецификации: без отдельного компонента и без конфигурации:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @CircuitBreakerSpec("resilient.circuitbreaker.custom")
    public interface CustomCircuitBreaker extends CircuitBreaker {

        @Override
        default boolean isFailure(Throwable throwable) {
            return !(throwable instanceof HttpServerResponseException e) || e.code() >= 500;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @CircuitBreakerSpec("resilient.circuitbreaker.custom")
    interface CustomCircuitBreaker : CircuitBreaker {

        override fun isFailure(throwable: Throwable): Boolean =
            throwable !is HttpServerResponseException || throwable.code() >= 500
    }
    ```

Второй способ — компонент `CircuitBreakerPredicate`, привязанный к спецификации через `@Tag`. Он имеет приоритет над
`isFailure` и подходит, когда самому фильтру нужны зависимости:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(CustomCircuitBreaker.class) //(1)!
    @Component
    public final class MyFailurePredicate implements CircuitBreakerPredicate {

        @Override
        public boolean isCircuitBreakerFailure(Throwable throwable) { //(2)!
            return !(throwable instanceof HttpServerResponseException e) || e.code() >= 500;
        }
    }
    ```

    1.  Привязывает предикат к одной спецификации; без тега предикат не будет использован.
    2.  Возврат `true` означает, что исключение засчитывается как отказ.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(CustomCircuitBreaker::class) //(1)!
    @Component
    class MyFailurePredicate : CircuitBreakerPredicate {

        override fun isCircuitBreakerFailure(throwable: Throwable): Boolean = //(2)!
            throwable !is HttpServerResponseException || throwable.code() >= 500
    }
    ```

    1.  Привязывает предикат к одной спецификации; без тега предикат не будет использован.
    2.  Возврат `true` означает, что исключение засчитывается как отказ.

Исключение, отклонённое фильтром, не засчитывается ни как отказ, ни как успех: circuit breaker его просто игнорирует,
а вызывающему коду оно возвращается без изменений.

!!! warning "Собственный фильтр заменяет проверку маркера"

    `NonCircuitableException` проверяется реализацией `isFailure` по умолчанию. Переопределённый `isFailure` или
    `CircuitBreakerPredicate` с тегом заменяют эту проверку, поэтому собственный фильтр, который должен по-прежнему
    учитывать маркер, проверяет `throwable instanceof NonCircuitableException` сам.

### Императивное использование { #imperative-usage }

Интерфейс спецификации — обычный компонент графа приложения, поэтому в императивном коде его достаточно внедрить напрямую:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final CustomCircuitBreaker circuitBreaker;

        public SomeService(CustomCircuitBreaker circuitBreaker) {
            this.circuitBreaker = circuitBreaker;
        }

        public String doWork() {
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
    class SomeService(private val circuitBreaker: CustomCircuitBreaker) {

        fun doWork(): String {
            return circuitBreaker.accept(ThrowableCallable { doSomeWork() })
        }

        private fun doSomeWork(): String {
            // do some work
        }
    }
    ```

Методы `accept` принимают `ThrowableCallable<T, E>` или `ThrowableRunnable<E>` из пакета `io.koraframework.resilient.common`,
поэтому защищаемый код может бросать проверяемые исключения.

Чтобы в состоянии `OPEN` вернуть резервное значение вместо `CallNotPermittedException`, используйте перегрузку `accept` со вторым аргументом:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public String doWork() {
        return circuitBreaker.accept(this::doSomeWork, () -> "fallback");
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    fun doWork(): String {
        return circuitBreaker.accept(ThrowableCallable { doSomeWork() }, ThrowableCallable { "fallback" })
    }
    ```

Если защищаемый вызов не удаётся обернуть в один callable, разрешение можно получать и освобождать вручную.
Вызовите `acquire()` (бросает `CallNotPermittedException`, когда состояние `OPEN` либо `HALF_OPEN` и все пробные вызовы уже израсходованы), а затем **обязательно** сообщите результат через `releaseOnSuccess()` или `releaseOnError(Throwable)` — иначе разрешение утечёт и учёт вызовов станет неверным:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public String doWork() {
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

`tryAcquire()` — вариант без исключения: он возвращает `false`, когда вызов не разрешён, и позволяет ветвиться без перехвата `CallNotPermittedException`.
Если же `acquire()` бросил исключение, текущее [состояние](#circuitbreaker) (`OPEN` или `HALF_OPEN`) доступно через `CallNotPermittedException#state()`.

## Retry { #retry }

`Retry` даёт возможность настроить повторные вызовы аннотированных методов.
Он позволяет указать, когда метод следует повторить, и настроить параметры повторов, если метод бросает исключение, подходящее под настроенный фильтр.

### Декларативное использование { #declarative-usage-2 }

Когда все попытки исчерпаны, вызов завершается исключением `RetryExhaustedException`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @RetrySpec("resilient.retry.custom")
    public interface CustomRetry extends Retry { }

    @Component
    public class SomeService {

        @Retryable(CustomRetry.class)
        public String getValue() {
            throw new IllegalStateException("Ops");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @RetrySpec("resilient.retry.custom")
    interface CustomRetry : Retry

    @Component
    open class SomeService {

        @Retryable(CustomRetry::class)
        open fun execute(arg: String): Unit = throw IllegalStateException("Ops")
    }
    ```

### Конфигурация { #configuration-2 }

Секция, на которую указывает `@RetrySpec`, описана в классе `RetryConfig`:

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
        retry {
            custom {
                delay = "100ms" //(1)!
                attempts = 2 //(2)!
                delayStep = "100ms" //(3)!
                enabled = true //(4)!
            }
        }
    }
    ```

    1.  Начальная задержка перед повторным вызовом (обязательное, без значения по умолчанию).
    2.  Количество повторных попыток (обязательное, без значения по умолчанию).
    3.  Приращение задержки для последующих попыток; игнорируется, если задана секция `backoff` (по умолчанию: `0`).
    4.  Включение или отключение `Retry` (по умолчанию: `true`).

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      retry:
        custom:
          delay: "100ms" #(1)!
          attempts: 2 #(2)!
          delayStep: "100ms" #(3)!
          enabled: true #(4)!
    ```

    1.  Начальная задержка перед повторным вызовом (обязательное, без значения по умолчанию).
    2.  Количество повторных попыток (обязательное, без значения по умолчанию).
    3.  Приращение задержки для последующих попыток; игнорируется, если задана секция `backoff` (по умолчанию: `0`).
    4.  Включение или отключение `Retry` (по умолчанию: `true`).

Необязательные секции `backoff`, `jitter` и `retryBudget` описаны в разделах [Backoff и jitter](#retry-backoff) и
[Бюджет повторов](#retry-budget), а ключ `telemetry` переопределяет настройки из раздела [Телеметрия](#telemetry).

!!! warning "Ограничения и рост задержки"

    `delay` и `attempts` обязательны, без них приложение не стартует.
    `attempts` считает повторы **после** первоначального вызова, поэтому `attempts = 2` допускает до `3` выполнений суммарно,
    а `attempts = 0` превращает аспект в прозрачный проброс.
    Без секции `backoff` каждый повтор ждёт на `delayStep` (по умолчанию `0`) дольше предыдущего, то есть задержки составляют
    `delay`, `delay + delayStep`, `delay + 2·delayStep`, … .

!!! note

    Значение `enabled = false` превращает `@Retryable` в прозрачный проброс (метод выполняется один раз).
    Когда попытки заканчиваются, бросается `RetryExhaustedException`, у которого `getCause()` — последний отказ,
    а в подавленных (`suppressed`) исключениях лежат все предыдущие.

### Backoff и jitter { #retry-backoff }

Секция `backoff` заменяет линейный рост `delayStep` на экспоненциальный, а `jitter` разводит задержки параллельных
вызовов, чтобы они не повторяли запрос синхронно:

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
        retry {
            custom {
                delay = "100ms"
                attempts = 4
                backoff {
                    type = EXPONENTIAL //(1)!
                    multiplier = 2.0 //(2)!
                    delayMax = "5s" //(3)!
                }
                jitter {
                    type = FULL //(4)!
                    ratio = 1.0 //(5)!
                }
            }
        }
    }
    ```

    1.  Стратегия роста задержки; поддерживается единственное значение `EXPONENTIAL` (по умолчанию: `EXPONENTIAL`).
    2.  Множитель, применяемый на каждой попытке, должен быть больше `0` (по умолчанию: `2.0`).
    3.  Верхняя граница вычисленной задержки (опционально, по умолчанию не ограничена).
    4.  Стратегия разброса: `NONE` отключает его, `FULL` рандомизирует задержку (по умолчанию: `NONE`).
    5.  Доля вычисленной задержки, которая может быть вычтена, значение в диапазоне `0..1` (по умолчанию: `1.0`).

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      retry:
        custom:
          delay: "100ms"
          attempts: 4
          backoff:
            type: EXPONENTIAL #(1)!
            multiplier: 2.0 #(2)!
            delayMax: "5s" #(3)!
          jitter:
            type: FULL #(4)!
            ratio: 1.0 #(5)!
    ```

    1.  Стратегия роста задержки; поддерживается единственное значение `EXPONENTIAL` (по умолчанию: `EXPONENTIAL`).
    2.  Множитель, применяемый на каждой попытке, должен быть больше `0` (по умолчанию: `2.0`).
    3.  Верхняя граница вычисленной задержки (опционально, по умолчанию не ограничена).
    4.  Стратегия разброса: `NONE` отключает его, `FULL` рандомизирует задержку (по умолчанию: `NONE`).
    5.  Доля вычисленной задержки, которая может быть вычтена, значение в диапазоне `0..1` (по умолчанию: `1.0`).

С приведёнными настройками вычисленная задержка для попытки `n` равна `delay * multiplier^(n-1)` и ограничена сверху `delayMax`:
`100ms`, `200ms`, `400ms`, `800ms`. Затем jitter выбирает фактическую задержку равномерно из отрезка
`[computed - computed * ratio, computed]`, поэтому `ratio = 1.0` означает любое значение от `0` до вычисленной задержки.

### Бюджет повторов { #retry-budget }

Бюджет повторов ограничивает, сколько дополнительной нагрузки могут создать повторы. Это ведро токенов: каждый повтор
забирает один токен, каждый успешный вызов возвращает `ratio` токенов, а когда ведро пусто, повтор запрещается и исходное
исключение пробрасывается как есть — без ожидания и без `RetryExhaustedException`.

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
        retry {
            custom {
                delay = "100ms"
                attempts = 3
                retryBudget {
                    enabled = true //(1)!
                    ratio = 0.1 //(2)!
                    tokensMax = 100 //(3)!
                    tokensInitial = 10 //(4)!
                    minTokensPerSecond = 0.0 //(5)!
                }
            }
        }
    }
    ```

    1.  Включение или отключение бюджета (по умолчанию: `true`).
    2.  Сколько токенов добавляет успешный вызов — `0.1` разрешает примерно один повтор на десять успешных вызовов (по умолчанию: `0.1`).
    3.  Верхняя граница ведра (по умолчанию: `100`).
    4.  Начальное количество токенов, не должно превышать `tokensMax` (по умолчанию: `10`).
    5.  Гарантированная скорость пополнения, которая работает даже без успешных вызовов (по умолчанию: `0.0`).

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      retry:
        custom:
          delay: "100ms"
          attempts: 3
          retryBudget:
            enabled: true #(1)!
            ratio: 0.1 #(2)!
            tokensMax: 100 #(3)!
            tokensInitial: 10 #(4)!
            minTokensPerSecond: 0.0 #(5)!
    ```

    1.  Включение или отключение бюджета (по умолчанию: `true`).
    2.  Сколько токенов добавляет успешный вызов — `0.1` разрешает примерно один повтор на десять успешных вызовов (по умолчанию: `0.1`).
    3.  Верхняя граница ведра (по умолчанию: `100`).
    4.  Начальное количество токенов, не должно превышать `tokensMax` (по умолчанию: `10`).
    5.  Гарантированная скорость пополнения, которая работает даже без успешных вызовов (по умолчанию: `0.0`).

!!! note

    Бюджет выключен, пока секция `retryBudget` не объявлена. Объявление её с `enabled = false` также оставляет бюджет выключенным.

#### Собственный и распределённый бюджет { #retry-budget-factory }

Сам бюджет — это `RetryBudget` (`tryAcquireRetryToken()`, `onSuccess()`, `availableTokens()`), и каждая спецификация
повтора получает свой экземпляр от компонента `RetryBudgetFactory` через `get(name, config)`, где `name` — простое имя
интерфейса-спецификации, а `config` — её `RetryConfig`. Если фабрика возвращает `null`, повтор работает без бюджета.
`RetryModule` регистрирует `DefaultRetryBudgetFactory`, которая строит хранящийся в памяти `KoraRetryBudget` из секции
`retryBudget`, поэтому по умолчанию у каждого экземпляра приложения своя корзина.

Фабрика заменяется обычным способом: компонент `RetryBudgetFactory` без тега переопределяет фабрику по умолчанию для всех
повторов, а фабрика с тегом спецификации, `@Tag(PetRetry.class)`, используется только для этого повтора и имеет приоритет
над фабрикой без тега.

`DistributedRetryBudgetFactory` из [распределённого модуля](#dependency-distributed) хранит один баланс токенов на
спецификацию в `Redis`, поэтому бюджет ограничивает повторы всех экземпляров вместе. Автоматически она не регистрируется:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends ResilientModule, LettuceDistributedResilientModule {

        default RetryBudgetFactory distributedRetryBudgetFactory(DistributedRetryBudgetClient client) { //(1)!
            return new DistributedRetryBudgetFactory(client);
        }

        @Tag(PetRetry.class) //(2)!
        default RetryBudgetFactory petRetryBudgetFactory(DistributedRetryBudgetClient client) {
            return new DistributedRetryBudgetFactory(client, "pets:retrybudget", Duration.ofMinutes(30)); //(3)!
        }
    }
    ```

    1.  Фабрика без тега заменяет `DefaultRetryBudgetFactory` для всех повторов.
    2.  Фабрика с тегом спецификации используется только `PetRetry` и побеждает фабрику без тега.
    3.  Префикс ключа и время жизни неиспользуемого ключа баланса (по умолчанию: `kora:retrybudget` и `10` минут).

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : ResilientModule, LettuceDistributedResilientModule {

        fun distributedRetryBudgetFactory(client: DistributedRetryBudgetClient): RetryBudgetFactory = //(1)!
            DistributedRetryBudgetFactory(client)

        @Tag(PetRetry::class) //(2)!
        fun petRetryBudgetFactory(client: DistributedRetryBudgetClient): RetryBudgetFactory =
            DistributedRetryBudgetFactory(client, "pets:retrybudget", Duration.ofMinutes(30)) //(3)!
    }
    ```

    1.  Фабрика без тега заменяет `DefaultRetryBudgetFactory` для всех повторов.
    2.  Фабрика с тегом спецификации используется только `PetRetry` и побеждает фабрику без тега.
    3.  Префикс ключа и время жизни неиспользуемого ключа баланса (по умолчанию: `kora:retrybudget` и `10` минут).

Баланс хранится под ключом `<keyPrefix>:<простое имя спецификации>`, и каждое изменение продлевает срок жизни ключа,
поэтому неиспользуемый бюджет исчезает из `Redis` и начинается заново с `tokensInitial`. Сервисы, работающие с одним `Redis`
и использующие спецификации с одинаковым простым именем, делят один баланс, если их префиксы ключей не различаются.

!!! note

    Распределённый бюджет читает ту же секцию `retryBudget`, и она по-прежнему должна быть объявлена: `enabled`, `ratio`,
    `tokensMax` и `tokensInitial` сохраняют свой смысл, а `minTokensPerSecond` игнорируется — общий баланс пополняется
    только успешными вызовами.

### Фильтрация исключений { #exception-filtering-2 }

По умолчанию `Retry` повторяет вызов при любой ошибке, кроме исключений, реализующих интерфейс-маркер
`NonRetryableException` (см. [пример](#exception-filtering) в разделе circuit breaker). Два способа сузить это дальше повторяют подход
[circuit breaker](#exception-filtering): переопределить `isFailure` в спецификации либо зарегистрировать компонент
`RetryPredicate` с тегом спецификации. Если есть оба, побеждает компонент с тегом, и любой из них заменяет проверку
`NonRetryableException` по умолчанию.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @RetrySpec("resilient.retry.custom")
    public interface CustomRetry extends Retry {

        @Override
        default boolean isFailure(Throwable throwable) {
            return throwable instanceof IOException;
        }
    }

    @Tag(CustomRetry.class)
    @Component
    public final class MyRetryPredicate implements RetryPredicate {

        @Override
        public boolean isRetryFailure(Throwable throwable) {
            return throwable instanceof IOException;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @RetrySpec("resilient.retry.custom")
    interface CustomRetry : Retry {

        override fun isFailure(throwable: Throwable): Boolean = throwable is IOException
    }

    @Tag(CustomRetry::class)
    @Component
    class MyRetryPredicate : RetryPredicate {

        override fun isRetryFailure(throwable: Throwable): Boolean = throwable is IOException
    }
    ```

Исключение, отклонённое фильтром, пробрасывается сразу — без дальнейших попыток и без оборачивания в
`RetryExhaustedException`.

### Императивное использование { #imperative-usage-2 }

Внедрите интерфейс спецификации и вызывайте его напрямую:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final CustomRetry retry;

        public SomeService(CustomRetry retry) {
            this.retry = retry;
        }

        public String doWork() {
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
    class SomeService(private val retry: CustomRetry) {

        fun doWork(): String {
            return retry.retry(ThrowableCallable { doSomeWork() })
        }

        private fun doSomeWork(): String {
            // do some work
        }
    }
    ```

Чтобы после исчерпания всех попыток вернуть резервное значение вместо `RetryExhaustedException`, передайте второй callable:

===! ":fontawesome-brands-java: `Java`"

    ```java
    return retry.retry(this::doSomeWork, () -> "fallback");
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    return retry.retry(ThrowableCallable { doSomeWork() }, ThrowableCallable { "fallback" })
    ```

Для асинхронного императивного кода есть перегрузка, которая повторяет `Supplier<CompletionStage<T>>` и возвращает `CompletionStage<T>`, планируя каждую попытку после настроенной задержки и не блокируя вызывающий поток.

#### Ручное управление состоянием повтора { #manual-retry-state }

Для полного контроля над циклом повторов используйте `retry.asState()`, возвращающий `Retry.RetryState`.
Он реализует `AutoCloseable`, поэтому оборачивайте его в try-with-resources (Java) или `use` (Kotlin), чтобы метрики записались по завершении.
На каждое пойманное исключение вызывайте `onException(Throwable)`, который возвращает `RetryStatus`:

- `ACCEPTED` — очередная попытка разрешена; вызовите `doDelay()` (блокирует на текущую задержку) и повторите вызов.
- `REJECTED` — исключение отклонено фильтром либо [бюджет повторов](#retry-budget) исчерпан, повторять нельзя; пробросьте его дальше.
- `EXHAUSTED` — все попытки израсходованы; бросьте `RetryExhaustedException` (или верните значение по умолчанию).

`getAttempts()` / `getAttemptsMax()` показывают прогресс, а `getDelayNanos()` возвращает следующую задержку.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public String doWork() {
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

`Timeout` задаёт максимальное время выполнения аннотированного метода.
Синхронные методы выполняются на виртуальном потоке и прерываются по достижении лимита, а для Kotlin `suspend`-функций
корутина отменяется через `withTimeout`.

### Декларативное использование { #declarative-usage-3 }

Если метод не завершается в пределах `duration`, вызов падает с `TimeoutExhaustedException`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @TimeoutSpec("resilient.timeout.custom")
    public interface CustomTimeouter extends Timeouter { }

    @Component
    public class SomeService {

        @Timeout(CustomTimeouter.class)
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
    @TimeoutSpec("resilient.timeout.custom")
    interface CustomTimeouter : Timeouter

    @Component
    open class SomeService {

        @Timeout(CustomTimeouter::class)
        open fun value(): String = try {
            Thread.sleep(3000)
            "OK"
        } catch (e: InterruptedException) {
            throw IllegalStateException(e)
        }
    }
    ```

### Конфигурация { #configuration-3 }

Секция, на которую указывает `@TimeoutSpec`, описана в классе `TimeoutConfig`:

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
        timeout {
            custom {
                duration = "1s" //(1)!
                enabled = true //(2)!
            }
        }
    }
    ```

    1.  Ограничение времени операции, по истечении которого будет брошено `TimeoutExhaustedException` (обязательное, без значения по умолчанию).
    2.  Включение или отключение `Timeout` (по умолчанию: `true`).

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      timeout:
        custom:
          duration: "1s" #(1)!
          enabled: true #(2)!
    ```

    1.  Ограничение времени операции, по истечении которого будет брошено `TimeoutExhaustedException` (обязательное, без значения по умолчанию).
    2.  Включение или отключение `Timeout` (по умолчанию: `true`).

Ключ `telemetry` внутри той же секции переопределяет общемодульные настройки из раздела [Телеметрия](#telemetry).

!!! note

    `duration` обязателен, без него приложение не стартует.
    Значение `enabled = false` превращает `@Timeout` в прозрачный проброс — метод выполняется без ограничения времени.
    Исключение, брошенное методом до истечения лимита, пробрасывается без изменений, включая проверяемые исключения.

### Императивное использование { #imperative-usage-3 }

Внедрите интерфейс спецификации и вызывайте его напрямую:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final CustomTimeouter timeouter;

        public SomeService(CustomTimeouter timeouter) {
            this.timeouter = timeouter;
        }

        public String doWork() {
            return timeouter.execute(this::doSomeWork);
        }

        private String doSomeWork() {
            // do some work
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(private val timeouter: CustomTimeouter) {

        fun doWork(): String {
            return timeouter.execute(ThrowableCallable { doSomeWork() })
        }

        private fun doSomeWork(): String {
            // do some work
        }
    }
    ```

У `Timeouter` также есть перегрузка `execute` для операций, ничего не возвращающих, а `timeout()` возвращает настроенный `Duration`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    Duration limit = timeouter.timeout();  // configured duration
    timeouter.execute(this::cleanup);      // void operation, throws TimeoutExhaustedException on timeout
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    val limit: Duration = timeouter.timeout()           // configured duration
    timeouter.execute(ThrowableRunnable { cleanup() })  // void operation, throws TimeoutExhaustedException on timeout
    ```

## RateLimiter { #ratelimiter }

`RateLimiter` ограничивает, сколько раз метод может быть вызван за период: `limitForPeriod` разрешений на
`limitRefreshPeriod`. Способ выдачи разрешений определяет [алгоритм](#ratelimiter-algorithms), по умолчанию это token
bucket. Получение разрешения никогда не блокирует — вызов, для которого нет доступного разрешения, сразу падает с
`RateLimitExceededException`.

### Декларативное использование { #declarative-usage-5 }

===! ":fontawesome-brands-java: `Java`"

    ```java
    @RateLimiterSpec("resilient.ratelimiter.custom")
    public interface CustomRateLimiter extends RateLimiter { }

    @Component
    public class SomeService {

        @RateLimited(CustomRateLimiter.class)
        public String getValue() {
            return "OK";
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @RateLimiterSpec("resilient.ratelimiter.custom")
    interface CustomRateLimiter : RateLimiter

    @Component
    open class SomeService {

        @RateLimited(CustomRateLimiter::class)
        open fun value(): String = "OK"
    }
    ```

### Конфигурация { #configuration-5 }

Секция, на которую указывает `@RateLimiterSpec`, описана в классе `RateLimiterConfig`:

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
        ratelimiter {
            custom {
                limitForPeriod = 100 //(1)!
                limitRefreshPeriod = "1s" //(2)!
                type = TOKEN_BUCKET //(3)!
                enabled = true //(4)!
            }
        }
    }
    ```

    1.  Количество вызовов, разрешённых в пределах одного периода (обязательное, без значения по умолчанию).
    2.  Длительность периода, по истечении которого разрешения восстанавливаются (обязательное, без значения по умолчанию).
    3.  [Алгоритм](#ratelimiter-algorithms) ограничения: `TOKEN_BUCKET` или `FIXED_WINDOW` (по умолчанию: `TOKEN_BUCKET`).
    4.  Включение или отключение `RateLimiter` (по умолчанию: `true`).

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      ratelimiter:
        custom:
          limitForPeriod: 100 #(1)!
          limitRefreshPeriod: "1s" #(2)!
          type: TOKEN_BUCKET #(3)!
          enabled: true #(4)!
    ```

    1.  Количество вызовов, разрешённых в пределах одного периода (обязательное, без значения по умолчанию).
    2.  Длительность периода, по истечении которого разрешения восстанавливаются (обязательное, без значения по умолчанию).
    3.  [Алгоритм](#ratelimiter-algorithms) ограничения: `TOKEN_BUCKET` или `FIXED_WINDOW` (по умолчанию: `TOKEN_BUCKET`).
    4.  Включение или отключение `RateLimiter` (по умолчанию: `true`).

Ключ `telemetry` внутри той же секции переопределяет общемодульные настройки из раздела [Телеметрия](#telemetry).

!!! note

    Значение `enabled = false` превращает `@RateLimited` в прозрачный проброс — разрешается любой вызов.
    Ограничитель работает в пределах одного экземпляра приложения: при нескольких репликах фактический лимит равен `limitForPeriod`, умноженному на число реплик.
    Для лимита, общего для всех реплик, нужен [распределённый rate limiter](#ratelimiter-distributed).

### Алгоритмы { #ratelimiter-algorithms }

Ключ `type` выбирает одну из двух неблокирующих реализаций, каждая из которых хранит всё состояние в одном атомарном значении:

| `type`                   | Поведение                                                                                                                                         | Когда использовать                                                                                       |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| `TOKEN_BUCKET` (по умолчанию) | token bucket на основе GCRA: разрешения восполняются непрерывно, по одному каждые `limitRefreshPeriod / limitForPeriod`, а простаивающий ограничитель допускает всплеск до `limitForPeriod` вызовов | ровный темп без пиков на границах периодов; выбор общего назначения                                       |
| `FIXED_WINDOW`           | счётчик на `limitForPeriod` разрешений для каждого следующего окна длиной `limitRefreshPeriod`, отсчитываемого от создания ограничителя              | строгая квота «N вызовов на окно»; на стыке двух соседних окон может пройти до двух `limitForPeriod` вызовов |

`FIXED_WINDOW` упаковывает счётчик в 24 бита, поэтому его `limitForPeriod` должен быть меньше `16777216`.

### Императивное использование { #imperative-usage-5 }

Внедрите интерфейс спецификации и вызывайте его напрямую:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class SomeService {

        private final CustomRateLimiter rateLimiter;

        public SomeService(CustomRateLimiter rateLimiter) {
            this.rateLimiter = rateLimiter;
        }

        public String doWork() {
            return rateLimiter.execute(this::doSomeWork); //(1)!
        }

        public boolean doWorkIfPermitted() {
            if (!rateLimiter.tryAcquire()) { //(2)!
                return false;
            }
            doSomeWork();
            return true;
        }

        private String doSomeWork() {
            // do some work
        }
    }
    ```

    1.  Получает разрешение и выполняет операцию, бросая `RateLimitExceededException`, когда лимит исчерпан.
    2.  Вариант без исключения: возвращает `false` вместо ошибки.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class SomeService(private val rateLimiter: CustomRateLimiter) {

        fun doWork(): String {
            return rateLimiter.execute(ThrowableCallable { doSomeWork() }) //(1)!
        }

        fun doWorkIfPermitted(): Boolean {
            if (!rateLimiter.tryAcquire()) { //(2)!
                return false
            }
            doSomeWork()
            return true
        }

        private fun doSomeWork(): String {
            // do some work
        }
    }
    ```

    1.  Получает разрешение и выполняет операцию, бросая `RateLimitExceededException`, когда лимит исчерпан.
    2.  Вариант без исключения: возвращает `false` вместо ошибки.

`acquire()` забирает разрешение, ничего не выполняя, и бросает `RateLimitExceededException`, когда разрешений не осталось.

### Распределённый rate limiter { #ratelimiter-distributed }

Локальный ограничитель считает только вызовы своего экземпляра. Когда лимит относится ко всему сервису — например, квота
API партнёра, — объявите спецификацию через `@RateLimiterDistributedSpec` вместо `@RateLimiterSpec`: тогда лимит
соблюдается через `Redis` для всех экземпляров вместе. Распределённый модуль должен быть
[подключён](#dependency-distributed).

===! ":fontawesome-brands-java: `Java`"

    ```java
    @RateLimiterDistributedSpec("resilient.ratelimiter.partner") //(1)!
    public interface PartnerRateLimiter extends RateLimiter { }

    @Component
    public class PartnerService {

        @RateLimited(PartnerRateLimiter.class) //(2)!
        public String getValue() {
            return "OK";
        }
    }
    ```

    1.  Вместо `@RateLimiterSpec`; интерфейс по-прежнему расширяет `RateLimiter`.
    2.  Аннотация метода, поддерживаемые сигнатуры и `RateLimitExceededException` те же, что у локального ограничителя.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @RateLimiterDistributedSpec("resilient.ratelimiter.partner") //(1)!
    interface PartnerRateLimiter : RateLimiter

    @Component
    open class PartnerService {

        @RateLimited(PartnerRateLimiter::class) //(2)!
        open fun value(): String = "OK"
    }
    ```

    1.  Вместо `@RateLimiterSpec`; интерфейс по-прежнему расширяет `RateLimiter`.
    2.  Аннотация метода, поддерживаемые сигнатуры и `RateLimitExceededException` те же, что у локального ограничителя.

Секция описана классом `DistributedRateLimiterConfig`:

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
        ratelimiter {
            partner {
                limitForPeriod = 100 //(1)!
                limitRefreshPeriod = "1s" //(2)!
                keyPrefix = "pets" //(3)!
                algorithm = TOKEN_BUCKET //(4)!
                enabled = true //(5)!
            }
        }
    }
    ```

    1.  Количество вызовов, разрешённых в пределах одного периода для всех экземпляров вместе (обязательное, без значения по умолчанию).
    2.  Длительность периода (обязательное, без значения по умолчанию).
    3.  Префикс ключей `Redis`, отделяющий ограничители этого сервиса (обязательное, без значения по умолчанию).
    4.  Алгоритм: `TOKEN_BUCKET` или `FIXED_WINDOW`, с тем же смыслом, что у [локального ограничителя](#ratelimiter-algorithms) (по умолчанию: `TOKEN_BUCKET`).
    5.  Включение или отключение ограничителя (по умолчанию: `true`).

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      ratelimiter:
        partner:
          limitForPeriod: 100 #(1)!
          limitRefreshPeriod: "1s" #(2)!
          keyPrefix: "pets" #(3)!
          algorithm: TOKEN_BUCKET #(4)!
          enabled: true #(5)!
    ```

    1.  Количество вызовов, разрешённых в пределах одного периода для всех экземпляров вместе (обязательное, без значения по умолчанию).
    2.  Длительность периода (обязательное, без значения по умолчанию).
    3.  Префикс ключей `Redis`, отделяющий ограничители этого сервиса (обязательное, без значения по умолчанию).
    4.  Алгоритм: `TOKEN_BUCKET` или `FIXED_WINDOW`, с тем же смыслом, что у [локального ограничителя](#ratelimiter-algorithms) (по умолчанию: `TOKEN_BUCKET`).
    5.  Включение или отключение ограничителя (по умолчанию: `true`).

Ключ `telemetry` и настройки `resilient.telemetry.rateLimiter` действуют так же, как для локального ограничителя.

!!! warning "Ключ алгоритма называется `algorithm`, а не `type`"

    В `DistributedRateLimiterConfig` ключ алгоритма называется `algorithm`, тогда как в локальном `RateLimiterConfig` — `type`.
    Ключ `type` в распределённой секции игнорируется, и ограничитель остаётся на `TOKEN_BUCKET`.

Как это работает:

- Сгенерированная реализация наследует `KoraDistributedRateLimiter` и требует `DistributedRateLimiterClient` в графе; его предоставляет `LettuceDistributedResilientModule`.
- Состояние ограничителя хранится под ключом `<keyPrefix>:<простое имя спецификации>`. `FIXED_WINDOW` использует отдельный ключ на каждое окно, `<keyPrefix>:<простое имя спецификации>:<номер окна>`, причём окна выровнены по системным часам, а не по моменту запуска приложения. Ключи истекают сами, когда становятся не нужны.
- `TOKEN_BUCKET` берёт текущее время из системных часов вызывающего экземпляра, поэтому расхождение часов между экземплярами делает лимит приблизительным. Он также немного приблизителен сразу после простоя и точен в установившемся режиме.
- Каждое разрешение стоит синхронных команд `Redis`, то есть добавляет к защищаемому вызову сетевой обмен. Ошибка `Redis` не подавляется: она выходит из `@RateLimited` к вызывающему коду.

## Fallback { #fallback }

`Fallback` указывает метод, который будет вызван при сбое аннотированного метода.
В отличие от остальных механизмов у него нет ни интерфейса-спецификации, ни собственной секции конфигурации: весь контракт —
это сам резервный метод.

Резервный метод **обязан совпадать** по типу возвращаемого значения с аннотированным методом и **должен быть объявлен в том же классе**.

### Декларативное использование { #declarative-usage-4 }

Пример резервного метода без аргументов:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @Fallback(method = "getFallback()")
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

        @Fallback(method = "getFallback()")
        open fun value(): String = "value"

        fun getFallback(): String = "fallback"
    }
    ```

Пример *Fallback* с аргументами:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @Fallback(method = "getFallback(arg3, arg1)")     // Passes the arguments of the annotated method in the specified order to the Fallback method
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
        @Fallback(method = "getFallback(arg3, arg1)")
        open fun getValue(arg1: String, arg2: Int, arg3: Long): String = "value"

        fun getFallback(argLong: Long, argString: String): String = "fallback"
    }
    ```

Ссылка проверяется на этапе компиляции. Типичные ошибки:

- `@Fallback method reference '…' has invalid syntax` — значение должно иметь вид `name()` или `name(arg1, arg2)`.
- `@Fallback method reference '…' uses unknown source arguments` — указан аргумент, которого нет у аннотированного метода.
- `@Fallback method '…' was not found` — метода с таким именем нет в том же классе.
- `@Fallback method '…' does not match requested signature` — резервный метод должен принимать ровно перечисленные аргументы плюс необязательный параметр `@Fallback.Reason`.

### Фильтрация исключений { #exception-filtering-3 }

По умолчанию резервный метод вызывается на любой `Throwable`. Единственный параметр `@Fallback.Reason` в резервном методе
одновременно передаёт вызвавшее фолбэк исключение и сужает условие срабатывания: исключение, не являющееся экземпляром
объявленного типа параметра, пробрасывается дальше, а резервный метод не вызывается.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @Fallback(method = "getFallback()")
        public String getValue() {
            throw new IllegalStateException("Ops");
        }

        protected String getFallback(@Fallback.Reason RuntimeException reason) { //(1)!
            return "fallback: " + reason.getMessage();
        }
    }
    ```

    1.  Такой параметр допускается не более одного, и он не входит в список аргументов в `method = "..."`.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    open class SomeService {

        @Fallback(method = "getFallback()")
        open fun value(): String = throw IllegalStateException("Ops")

        fun getFallback(@Fallback.Reason reason: RuntimeException): String = //(1)!
            "fallback: " + reason.message
    }
    ```

    1.  Такой параметр допускается не более одного, и он не входит в список аргументов в `method = "..."`.

В Java тип параметра должен соответствовать тому, что может бросить аннотированный метод: `RuntimeException`, если у него
нет `throws`, `Exception`, если объявлены проверяемые исключения, и `Throwable`, если объявлено `throws Throwable`.
Более узкий тип приводит к ошибке компиляции, поэтому для более тонкой фильтрации используйте обычную проверку `instanceof` внутри резервного метода.

## Телеметрия { #telemetry }

Логирование, метрики и трассировка настраиваются отдельно для каждого механизма в секции `resilient.telemetry`, а любая
спецификация может переопределить общемодульные значения ключом `telemetry` внутри своей секции конфигурации:

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
        telemetry {
            circuitBreaker { //(1)!
                logging.enabled = false //(2)!
                metrics {
                    enabled = false //(3)!
                    tags { "service" = "pets" } //(4)!
                }
                tracing {
                    enabled = false //(5)!
                    attributes { "component" = "resilient" } //(6)!
                }
            }
            retry {}
            timeout {}
            fallback {}
            rateLimiter {}
        }
        circuitbreaker {
            custom {
                telemetry.metrics.enabled = true //(7)!
            }
        }
    }
    ```

    1.  Секции: `circuitBreaker`, `retry`, `timeout`, `fallback`, `rateLimiter`.
    2.  Включает логирование механизма (по умолчанию: `false`).
    3.  Включает метрики механизма (по умолчанию: `false`).
    4.  Дополнительные теги, добавляемые ко всем метрикам механизма (по умолчанию: пусто).
    5.  Включает трассировку механизма (по умолчанию: `false`).
    6.  Дополнительные атрибуты, добавляемые ко всем спанам механизма (по умолчанию: пусто).
    7.  Переопределение для конкретной спецификации; незаданные ключи берутся из `resilient.telemetry`.

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      telemetry:
        circuitBreaker: #(1)!
          logging:
            enabled: false #(2)!
          metrics:
            enabled: false #(3)!
            tags:
              service: "pets" #(4)!
          tracing:
            enabled: false #(5)!
            attributes:
              component: "resilient" #(6)!
        retry: {}
        timeout: {}
        fallback: {}
        rateLimiter: {}
      circuitbreaker:
        custom:
          telemetry:
            metrics:
              enabled: true #(7)!
    ```

    1.  Секции: `circuitBreaker`, `retry`, `timeout`, `fallback`, `rateLimiter`.
    2.  Включает логирование механизма (по умолчанию: `false`).
    3.  Включает метрики механизма (по умолчанию: `false`).
    4.  Дополнительные теги, добавляемые ко всем метрикам механизма (по умолчанию: пусто).
    5.  Включает трассировку механизма (по умолчанию: `false`).
    6.  Дополнительные атрибуты, добавляемые ко всем спанам механизма (по умолчанию: пусто).
    7.  Переопределение для конкретной спецификации; незаданные ключи берутся из `resilient.telemetry`.

Весь блок `resilient.telemetry` необязателен — если его не указывать, все механизмы получат перечисленные значения по умолчанию.
Имена метрик перечислены в разделе [Справочник метрик](metrics.md#resilience).

## Комбинирование { #combination }

Все перечисленные аннотации можно комбинировать одновременно над одним методом.

Порядок применения аннотаций зависит от порядка их объявления.
Порядок можно менять как угодно и сочетать с другими аннотациями, которые также применяются в порядке объявления.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public class SomeService {

        @Fallback(method = "getFallback(arg1)")           // 4
        @CircuitBreakable(CustomCircuitBreaker.class)     // 3
        @Retryable(CustomRetry.class)                     // 2
        @Timeout(CustomTimeouter.class)                   // 1
        public String getValueSync(String arg1) {
            return "result-" + arg1;
        }

        protected String getFallback(String arg1) {       // 4
            return "fallback-" + arg1;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    open class SomeService {

        @Fallback(method = "getFallback(arg1)")             // 4
        @CircuitBreakable(CustomCircuitBreaker::class)      // 3
        @Retryable(CustomRetry::class)                      // 2
        @Timeout(CustomTimeouter::class)                    // 1
        open fun getValueSync(arg1: String): String = "result-$arg1"

        protected fun getFallback(arg1: String): String = "fallback-$arg1"  // 4
    }
    ```

В примере выше:

1. Применяется `@Timeout` и проверяет, что метод не выполняется дольше указанного в конфигурации времени.
2. Применяется `@Retryable` и повторяет выполнение метода настроенное число раз, если в цепочке возникло исключение, в том числе исключение от `@Timeout`.
3. Применяется `@CircuitBreakable` и работает согласно своей конфигурации и [состоянию](#circuitbreaker), в зависимости от успешного результата метода или исключения в цепочке, включая исключения от `@Timeout` и `@Retryable`.
4. Применяется `@Fallback` и вызывает метод `getFallback` с аргументом `arg1`, если в цепочке возникло исключение, включая исключения от `@Timeout`, `@Retryable` и `@CircuitBreakable`.

Порядок вызова аспектов соответствует порядку аннотаций на методе: сверху вниз, то есть самая верхняя аннотация — самая внешняя обёртка.
`@RateLimited` встраивается в ту же цепочку и обычно ставится выше `@CircuitBreakable`, чтобы отклонённые вызовы вообще не доходили до circuit breaker.

Пример конфигурации для всех аспектов:

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
        circuitbreaker {
            custom {
                type = FIXED_WINDOW
                countBased.windowSize = 1
                minimumRequiredCalls = 1
                failureRateThreshold = 100
                permittedCallsInHalfOpenState = 1
                waitDurationInOpenState = "1s"
            }
        }
        timeout {
            custom {
                duration = "300ms"
            }
        }
        retry {
            custom {
                delay = "100ms"
                attempts = 2
            }
        }
        ratelimiter {
            custom {
                limitForPeriod = 100
                limitRefreshPeriod = "1s"
            }
        }
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      circuitbreaker:
        custom:
          type: FIXED_WINDOW
          countBased:
            windowSize: 1
          minimumRequiredCalls: 1
          failureRateThreshold: 100
          permittedCallsInHalfOpenState: 1
          waitDurationInOpenState: "1s"
      timeout:
        custom:
          duration: "300ms"
      retry:
        custom:
          delay: "100ms"
          attempts: 2
      ratelimiter:
        custom:
          limitForPeriod: 100
          limitRefreshPeriod: "1s"
    ```

## Исключения { #exceptions }

Все исключения отказоустойчивости наследуют `io.koraframework.resilient.exception.ResilientException` (наследник `RuntimeException`), который предоставляет `name()` — простое имя интерфейса-спецификации, вызвавшего ошибку.

| Исключение                   | Кем бросается                                                                                                     | Дополнительный API                                                                       |
|------------------------------|-------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| `ResilientException`         | базовый тип для всех перечисленных ниже                                                                           | `name()`                                                                                 |
| `CallNotPermittedException`  | `@CircuitBreakable` / `CircuitBreaker#acquire()`, когда состояние `OPEN` либо `HALF_OPEN` без оставшихся пробных вызовов | `state()` возвращает `CircuitBreaker.State` (`OPEN` / `HALF_OPEN`)                        |
| `RetryExhaustedException`    | `@Retryable` / `Retry#retry(...)`, когда все попытки завершились неуспешно                                        | `name()`; в сообщении указано число попыток, последний отказ доступен через `getCause()`, предыдущие — в `suppressed` |
| `TimeoutExhaustedException`  | `@Timeout` / `Timeouter#execute(...)`, когда метод превысил `duration`                                            | `name()`                                                                                  |
| `RateLimitExceededException` | `@RateLimited` / `RateLimiter#acquire()`, когда нет доступного разрешения                                         | `name()`                                                                                  |

Каждое исключение лежит в подпакете `exception` своего механизма, например `io.koraframework.resilient.circuitbreaker.exception.CallNotPermittedException`.

**Описание** — аспекты отказоустойчивости сигнализируют о сбое, выбрасывая одно из этих непроверяемых исключений из защищаемого метода.

**Причины**

- `CallNotPermittedException` — circuit breaker обрывает вызовы, потому что доля отказов достигла `failureRateThreshold`; вызов отклонён без обращения к методу.
- `RetryExhaustedException` — метод продолжал бросать повторяемое исключение, пока не были исчерпаны `attempts`; исходная ошибка доступна через `getCause()`.
- `TimeoutExhaustedException` — метод не завершился в пределах `duration`.
- `RateLimitExceededException` — уже разрешённые вызовы исчерпали `limitForPeriod` разрешений: token bucket ещё не восполнился либо текущее окно `FIXED_WINDOW` исчерпано.

**Рекомендации**

- Ловите `ResilientException`, чтобы единообразно обрабатывать любой отказ механизмов, либо конкретный тип, когда обработка различается.
- При [комбинировании](#combination) аспектов исключение нижележащего аспекта поднимается по цепочке: например, `TimeoutExhaustedException` от `@Timeout` увидит `@Retryable`, затем `@CircuitBreakable` и в конце `@Fallback`. Предпочтительнее обработать это методом `@Fallback` или императивным резервным значением, чем превращать в ошибку, видимую пользователю.
- Исключение, отклонённое [фильтром](#exception-filtering), пробрасывается как есть и никогда не оборачивается, поэтому вызывающий код видит исходный тип.

Пример обработки:

===! ":fontawesome-brands-java: `Java`"

    ```java
    try {
        return service.getValue();
    } catch (CallNotPermittedException e) {
        log.warn("CircuitBreaker '{}' is {}", e.name(), e.state());
        return cachedValue();
    } catch (TimeoutExhaustedException | RetryExhaustedException | RateLimitExceededException e) {
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
    } catch (e: ResilientException) { // TimeoutExhaustedException, RetryExhaustedException, RateLimitExceededException, ...
        log.warn("Resilient '{}' failed", e.name(), e)
        return cachedValue()
    }
    ```

## Сигнатуры { #signatures }

Доступные сигнатуры методов, которые поддерживают эти аннотации из коробки.
Реактивные типы возвращаемого значения (`Mono`, `Flux` и любой другой `Publisher`) не поддерживаются ни одним из аспектов отказоустойчивости.

===! ":fontawesome-brands-java: `Java`"

    Класс должен быть не `final`, чтобы аспекты работали.

    Под `T` подразумевается тип возвращаемого значения.

    - `void myMethod()`
    - `T myMethod()`
    - `Optional<T> myMethod()`
    - `CompletionStage<T> myMethod()` / `CompletableFuture<T> myMethod()` ([CompletionStage](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/CompletionStage.html)) — поддерживается всеми аннотациями, кроме `@RateLimited`

=== ":simple-kotlin: `Kotlin`"

    Класс должен быть `open`, чтобы аспекты работали.

    Под `T` подразумевается тип возвращаемого значения, либо `T?`, либо `Unit`.

    - `myMethod(): T`
    - `suspend myMethod(): T` ([Kotlin Coroutines](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine), требует [зависимости](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) как `implementation`)
    - `myMethod(): Flow<T>` ([Kotlin Coroutines](https://kotlinlang.org/docs/coroutines-basics.html#your-first-coroutine), требует [зависимости](https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-core) как `implementation`)

    `CompletionStage` и `CompletableFuture` в Kotlin не поддерживаются — используйте `suspend`.

Применение аспекта к неподдерживаемому типу возвращаемого значения приводит к ошибке компиляции вида
`@Retryable cannot be applied to '…' because return type '…' is not supported by this aspect`.
