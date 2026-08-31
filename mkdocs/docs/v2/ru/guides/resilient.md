---
search:
  exclude: true
title: Шаблоны отказоустойчивости
summary: Extend the HTTP Server guide by applying Kora resilience annotations directly to your existing UserService methods
description: "Step-by-step resilience for a Kora 2.0 service: the io.koraframework:resilient-kora artifact and ResilientModule, typed spec interfaces declared with @RetrySpec, @TimeoutSpec, @CircuitBreakerSpec and @RateLimiterSpec, the @Retryable, @Timeout, @CircuitBreakable, @RateLimited and @Fallback aspects that reference them by class, the resilient configuration section with countBased.windowSize and the circuit breaker type, a CircuitBreakerPredicate bound with @Tag, @Fallback.Reason, and the generated AOP proxy sources."
agent:
  use_when: "Use this file for questions about making a Kora 2.0 service fault tolerant: io.koraframework:resilient-kora, ResilientModule, @RetrySpec / @TimeoutSpec / @CircuitBreakerSpec / @RateLimiterSpec interfaces, @Retryable(Spec.class), @Timeout(Spec.class), @CircuitBreakable(Spec.class), @RateLimited(Spec.class), @Fallback(method) and @Fallback.Reason, CircuitBreakerPredicate and RetryPredicate bound with @Tag(Spec.class), the resilient.* config keys (attempts, delay, delayStep, backoff, jitter, retryBudget, duration, type, countBased.windowSize, minimumRequiredCalls, failureRateThreshold, waitDurationInOpenState, limitForPeriod, limitRefreshPeriod), aspect ordering, and reading the generated $UserService__AopProxy."
tags: resilient, retry, timeout, circuitbreaker, ratelimiter, fallback, http-server, hocon
---

# Шаблоны отказоустойчивости { #resilience-patterns }

Это руководство знакомит с шаблонами отказоустойчивости для сервисных методов Kora. В нем разбирается, как аннотации повторных попыток, ограничения времени, прерывателя, ограничителя частоты и
резервного метода оборачивают операции приложения, как конфигурация отказоустойчивости управляет поведением при сбоях и как HTTP API может оставаться неизменным, пока вызовы сервисов становятся более
устойчивыми к отказам. Вы также увидите, как каждый шаблон защищает свой тип нестабильной зависимости или операции.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java Resilient App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-resilient-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin Resilient App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-resilient-app).

## Что вы создадите { #youll-build }

Вы дополните `UserService` из руководства по HTTP-серверу:

- `@Retryable` на `getUser()` для кратковременных сбоев чтения
- `@Fallback` на `createUser()` для плавной деградации, когда создание не удалось
- `@Timeout` на `deleteUser()`, чтобы остановить зависшие операции удаления
- `@CircuitBreakable` на `updateUser()`, чтобы прекратить повторяющиеся неудачные обновления
- комбинированную цепочку `@CircuitBreakable + @Retryable + @Timeout` на `getUsers()`

Каждая из этих аннотаций указывает на небольшой интерфейс-спецификацию, который вы объявляете сами — именно так Kora 2.0 связывает метод с секцией конфигурации.

## Что вам понадобится { #youll-need }

- JDK 25 или новее
- Gradle 9+
- текстовый редактор или среда разработки
- рабочий проект из руководства [HTTP-сервер](http-server.md)

## Требования { #prerequisites }

!!! note "Обязательно: пройдите руководство по HTTP-серверу"

    Это руководство предполагает, что вы прошли **[HTTP-сервер](http-server.md)** и у вас уже есть `Application`, `UserController`, `UserService`, `UserRepository`, `InMemoryUserRepository`, `UserRequest` и `UserResponse`.

    Если вы еще не прошли руководство по HTTP-серверу, сначала сделайте это, потому что здесь шаблоны отказоустойчивости добавляются к существующему CRUD API, а не создают API с нуля.

## Обзор { #overview }

[Отказоустойчивость в Kora](../documentation/resilient.md) — это управление поведением приложения, когда зависимость медленная, нестабильная или временно недоступна. Без явных правил отказоустойчивости
сбои имеют свойство распространяться: одна медленная операция может занять потоки запросов, повторяющиеся кратковременные ошибки могут перегрузить зависимость, а падающий нижестоящий вызов может
сделать нерабочими все эндпоинты сразу.

Цель не в том, чтобы скрыть каждый сбой. Цель в том, чтобы поведение при сбое было осознанным. Сервис должен знать, когда повторить попытку, когда прекратить ожидание, когда на время отказаться от
зависимости и когда безопасный резервный ответ допустим.

### Основы отказоустойчивости { #resilience-basics }

В этом руководстве HTTP-контракт не меняется. Отказоустойчивость добавляется вокруг сервисных методов, потому что именно в сервисах операции приложения встречаются с нестабильной работой: вызовами
хранилища, удаленными вызовами, дорогими вычислениями или фоновыми зависимостями. Удержание отказоустойчивости на этой границе позволяет контроллерам сохранять роль маршрутизации, пока сервисные
операции становятся более защищенными.

### Основные подходы { #core-patterns }

Модуль отказоустойчивости Kora предоставляет несколько шаблонов, каждый со своим назначением:

- повторная попытка выполняет операцию заново, если сбой может быть временным
- ограничение времени прекращает ожидание, когда операция длится слишком долго
- прерыватель на время прекращает вызовы к постоянно падающей операции
- ограничитель частоты задает потолок числа вызовов операции за интервал времени
- резервный метод дает альтернативный результат или поведение, когда основной путь не сработал

Эти шаблоны нельзя применять вслепую. Повторение неидемпотентной записи может продублировать работу. Слишком короткий таймаут создает ложные сбои. Слишком широкий резервный метод способен скрыть
настоящую аварию. Руководство держит каждый шаблон на виду, чтобы компромисс был очевиден.

### Типизированные спецификации { #typed-specs }

Kora 2.0 не связывает политику отказоустойчивости с методом по имени. Каждая политика описывается интерфейсом-спецификацией, который вы объявляете в своем коде:

- это `interface`, а не класс
- он наследует контракт шаблона: `Retry`, `Timeouter`, `CircuitBreaker` или `RateLimiter`
- он несет одну аннотацию — `@RetrySpec`, `@TimeoutSpec`, `@CircuitBreakerSpec` или `@RateLimiterSpec`, значением которой является путь конфигурации, читаемый этой политикой

Обработчик аннотаций затем генерирует для каждой спецификации две вещи: реализацию `$DefaultRetry_Impl` и `@Module` с именем `$DefaultRetry_Module`, который публикует ее в графе. Аспекты уровня метода
ссылаются на спецификацию по классу, поэтому `@Retryable(DefaultRetry.class)` проверяется на этапе компиляции. Опечатка в имени политики теперь ошибка компиляции, а не поиск в рантайме, который молча
ничего не находит.

Интерфейс-спецификация также является компонентом, который вы внедряете, когда хотите использовать политику императивно. Поскольку `DefaultRetry` наследует `Retry`, внедрение `DefaultRetry` сразу дает
`retry(...)` и `asState()`. В Kora 2.0 нет отдельных объектов-менеджеров: спецификация и есть рукоятка управления.

### Конфигурация и композиция { #configuration-composition }

Поведение отказоустойчивости живет в конфигурации не меньше, чем в аннотациях. Пороги, число попыток, задержки и длительности таймаутов часто различаются между локальной разработкой и промышленной
средой. Интерфейс-спецификация называет применяемую секцию конфигурации, а сама конфигурация задает, насколько агрессивна политика.

Руководство также показывает комбинированное поведение. В реальных сервисах путь чтения может нуждаться в повторных попытках, таймауте и прерывателе одновременно. Главный урок — компоновать эти шаблоны
осознанно вокруг четко определенной операции, а затем проверять поведение как часть контракта сервиса.

Практический порядок такой:

1. подключить модуль отказоустойчивости в граф приложения
2. объявить интерфейс-спецификацию, указывающую на путь конфигурации
3. разметить сервисный метод соответствующим аспектом, по одному шаблону за раз
4. настроить пороги, задержки и таймауты в HOCON
5. смоделировать сценарии сбоев в тестах
6. убедиться, что HTTP-контракт остается стабильным, пока поведение сервиса становится более защищенным

## Зависимости { #dependencies }

Добавьте зависимость отказоустойчивости в существующий проект из руководства по HTTP-серверу.

===! ":fontawesome-brands-java: `Java`"

    Добавьте в блок `dependencies` в `build.gradle`:

    ```groovy
    dependencies {
        // ... existing dependencies ...

        implementation("io.koraframework:resilient-kora")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    Добавьте в блок `dependencies` в `build.gradle.kts`:

    ```kotlin
    dependencies {
        // ... existing dependencies ...

        implementation("io.koraframework:resilient-kora")
    }
    ```

Версия приходит из платформы `io.koraframework:kora-bom`, которая уже применена в руководстве по HTTP-серверу. Отдельный обработчик аннотаций не нужен: процессор отказоустойчивости и AOP-аспекты
поставляются внутри артефактов `annotation-processors` (Java) и `symbol-processors` (Kotlin), которые у вас уже есть.

## Модули { #modules }

Сначала включите инфраструктуру отказоустойчивости в граф приложения Kora. Это делает аспекты повторных попыток, таймаута, прерывателя, ограничителя частоты и резервного метода доступными вашим
компонентам.

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/io/koraframework/guide/resilient/Application.java`:

    ```java
    package io.koraframework.guide.resilient;

    import io.koraframework.application.graph.KoraApplication;
    import io.koraframework.common.annotation.KoraApp;
    import io.koraframework.config.hocon.HoconConfigModule;
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule;
    import io.koraframework.json.common.JsonModule;
    import io.koraframework.logging.logback.LogbackModule;
    import io.koraframework.resilient.ResilientModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            UndertowPublicHttpServerModule,
            JsonModule,
            LogbackModule,
            ResilientModule {  // <----- Connected module

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/io/koraframework/guide/resilient/Application.kt`:

    ```kotlin
    package io.koraframework.guide.resilient

    import io.koraframework.application.graph.KoraApplication
    import io.koraframework.common.annotation.KoraApp
    import io.koraframework.config.hocon.HoconConfigModule
    import io.koraframework.http.server.undertow.UndertowPublicHttpServerModule
    import io.koraframework.json.common.JsonModule
    import io.koraframework.logging.logback.LogbackModule
    import io.koraframework.resilient.ResilientModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        UndertowPublicHttpServerModule,
        JsonModule,
        LogbackModule,
        ResilientModule  // <----- Connected module

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

`ResilientModule` — это зонтичный модуль: он наследует `CircuitBreakerModule`, `RetryModule`, `TimeoutModule`, `FallbackModule` и `RateLimiterModule` и читает общие настройки телеметрии из
`resilient.telemetry`. Модули, сгенерированные для ваших собственных интерфейсов-спецификаций, обнаруживаются автоматически, потому что каждый из них помечен `@Module`.

## Повторные попытки { #retry }

`Retry` — самое безопасное место для начала, потому что кратковременные сбои чаще всего случаются на чтении. Короткий сетевой сбой, временная проблема с соединением или кратковременная перегрузка часто
исчезают, если ту же операцию повторить через мгновение.

Повторная попытка полезна, когда:

- сбои кратковременны и обычно проходят на следующей попытке
- операцию безопасно повторять
- дополнительная задержка от повторов приемлема

Применяйте осторожно, когда:

- операция меняет состояние и может быть неидемпотентной
- нижестоящий сервис уже перегружен, и повторы только усилят давление
- бюджет времени и без того очень мал

Поскольку на этом шаге используются аннотации, размеченный класс должен соблюдать правила AOP:

- в Java класс не должен быть `final`
- в Kotlin класс и размеченные методы должны быть `open`

Начните с конфигурации, потому что интерфейс-спецификация ссылается на нее по пути.

`src/main/resources/application.conf`:

Полный справочник по конфигурации смотрите в [Resilient](../documentation/resilient.md).

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
      retry {
        default {
          delay = 20ms //(1)!
          attempts = 3 //(2)!
          delayStep = 20ms //(3)!
        }
      }
    }
    ```

    1. Начальная задержка перед повторной попыткой.
    2. Максимальное число повторных попыток.
    3. Линейная добавка к задержке на каждой следующей попытке.

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      retry:
        default:
          delay: 20ms #(1)!
          attempts: 3 #(2)!
          delayStep: 20ms #(3)!
    ```

    1. Начальная задержка перед повторной попыткой.
    2. Максимальное число повторных попыток.
    3. Линейная добавка к задержке на каждой следующей попытке.

Теперь объявите интерфейс-спецификацию, которая связывает этот путь конфигурации с переиспользуемой типизированной политикой.

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/io/koraframework/guide/resilient/service/DefaultRetry.java`:

    ```java
    package io.koraframework.guide.resilient.service;

    import io.koraframework.resilient.retry.Retry;
    import io.koraframework.resilient.retry.annotation.RetrySpec;

    @RetrySpec("resilient.retry.default")
    public interface DefaultRetry extends Retry {

    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/io/koraframework/guide/resilient/service/DefaultRetry.kt`:

    ```kotlin
    package io.koraframework.guide.resilient.service

    import io.koraframework.resilient.retry.Retry
    import io.koraframework.resilient.retry.annotation.RetrySpec

    @RetrySpec("resilient.retry.default")
    interface DefaultRetry : Retry
    ```

Интерфейс намеренно остается пустым. Его единственная задача — дать пути конфигурации `resilient.retry.default` тип, чтобы аспект метода и любое императивное использование ссылались на одну и ту же
политику.

Теперь разметьте метод чтения:

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/io/koraframework/guide/resilient/service/UserService.java`:

    ```java
    @Component
    public class UserService {

        private final UserRepository userRepository;

        public UserService(UserRepository userRepository) {
            this.userRepository = userRepository;
        }

        @Retryable(DefaultRetry.class)
        public Optional<UserResponse> getUser(String id) {
            return userRepository.findById(id);
        }

        // other methods stay unchanged for now
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/io/koraframework/guide/resilient/service/UserService.kt`:

    ```kotlin
    @Component
    open class UserService(
        private val userRepository: UserRepository,
    ) {

        @Retryable(DefaultRetry::class)
        open fun getUser(id: String): UserResponse? = userRepository.findById(id)

        // other methods stay unchanged for now
    }
    ```

Контроллеру не нужен новый эндпоинт. `GET /users/{userId}` уже делегирует в `getUser()`, поэтому поведение отказоустойчивости применяется автоматически на границе сервиса.

Повторная попытка не обязана реагировать на каждое исключение. Реализуйте `RetryPredicate` и привяжите его к спецификации через `@Tag` — тогда повторяться будут только принятые вами сбои:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(DefaultRetry.class)
    @Component
    public final class TransientOnlyRetryPredicate implements RetryPredicate {

        @Override
        public boolean isRetryFailure(Throwable throwable) {
            return !(throwable instanceof IllegalArgumentException);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(DefaultRetry::class)
    @Component
    class TransientOnlyRetryPredicate : RetryPredicate {

        override fun isRetryFailure(throwable: Throwable): Boolean =
            throwable !is IllegalArgumentException
    }
    ```

Предикат необязателен. Без него повторяется любое исключение — именно это поведение и оставляет руководство.

Помимо `delay`, `delayStep` и `attempts` секция повторных попыток принимает блок `backoff` (`type = EXPONENTIAL`, `multiplier`, `delayMax`), блок `jitter` (`type = NONE` или `FULL`, `ratio`) и блок
`retryBudget`, ограничивающий, какую долю трафика могут составлять повторы. К ним стоит обращаться, когда сервис повторяет запросы к зависимости, общей с другими вызывающими сторонами.

После компиляции сгенерированный прокси показывает, что `@Retryable` оборачивает исходный вызов метода напрямую:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/java/kora-java-guide-resilient-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/resilient/service/$UserService__AopProxy.java
    ```

    ```java
    private Optional<UserResponse> _getUser_AopProxy_RetryKoraAspect(String id) {
        return defaultRetry1.retry(() -> super.getUser(id));
    }

    @Override
    public Optional<UserResponse> getUser(String id) {
        return this._getUser_AopProxy_RetryKoraAspect(id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/kora-kotlin-guide-resilient-app/build/generated/ksp/main/kotlin/io/koraframework/guide/resilient/service/$UserService__AopProxy.kt
    ```

    ```kotlin
    private fun _getUser_AopProxy_RetryKoraAspect(id: String): UserResponse? =
        defaultRetry1.retry(ThrowableCallable { super.getUser(id) })

    override fun getUser(id: String): UserResponse? = _getUser_AopProxy_RetryKoraAspect(id)
    ```

Главное здесь — `defaultRetry1.retry(() -> super.getUser(id))`: Kora сгенерировала границу повторных попыток вокруг вашего сервисного метода, внедренное поле — это ваша собственная спецификация
`DefaultRetry`, а исходный код по-прежнему остается вызовом `super.getUser(id)` внутри этой границы.

## Резервный метод { #fallback }

`Fallback` — это про плавную деградацию. Если основной путь не сработал, вы возвращаете контролируемую альтернативу вместо простого пробрасывания сбоя.

Резервный метод полезен, когда:

- вы можете вернуть безопасную замену или ответ об отложенной обработке
- пользователю лучше получить ухудшенный ответ, чем жесткую ошибку
- у вас есть четко определенная запасная политика

Применяйте осторожно, когда:

- резервный метод слишком долго скрывает серьезный инцидент
- резервный метод может создать несогласованное бизнес-состояние
- команда начинает использовать резервный метод как молчаливую замену настоящему сохранению или гарантиям доставки

`@Fallback` — единственный шаблон в этом руководстве без интерфейса-спецификации и без секции конфигурации, потому что настраивать нечего: у него единственный атрибут `method`, называющий запасной
метод для вызова.

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/io/koraframework/guide/resilient/service/UserService.java`:

    ```java
    @Fallback(method = "createUserFallback(request)")
    public UserResponse createUser(UserRequest request) {
        var generatedId = userRepository.save(request.name(), request.email());
        return new UserResponse(generatedId, request.name(), request.email(), LocalDateTime.now());
    }

    protected UserResponse createUserFallback(UserRequest request) {
        // Never do this in real systems: imagine we wrote the request to a file
        // and planned to recreate the user during application startup.
        return new UserResponse("pending-file-write", request.name(), request.email(), LocalDateTime.now());
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/io/koraframework/guide/resilient/service/UserService.kt`:

    ```kotlin
    @Fallback(method = "createUserFallback(request)")
    open fun createUser(request: UserRequest): UserResponse {
        val generatedId = userRepository.save(request.name, request.email)
        return UserResponse(generatedId, request.name, request.email, LocalDateTime.now())
    }

    // Never do this in real systems: imagine we wrote the request to a file
    // and planned to recreate the user during application startup.
    protected open fun createUserFallback(request: UserRequest): UserResponse =
        UserResponse("pending-file-write", request.name, request.email, LocalDateTime.now())
    ```

Резервный метод не меняет контракт контроллера. `POST /users` по-прежнему возвращает `UserResponse`, но теперь сервис умеет плавно деградировать, когда основной путь не сработал.

Важно понимать, когда именно вызывается резервный метод:

1. Kora сначала вызывает исходный метод.
2. Если исходный метод отработал успешно, резервный не используется вовсе.
3. Если исходный метод выбросил исключение, Kora решает, относится ли этот сбой к тем, что резервный метод должен обработать.
4. Если да, Kora вызывает метод, объявленный в `method = "..."`.
5. Результат резервного метода становится итоговым результатом для вызывающей стороны.

Так что резервный метод никогда не является основным путем выполнения. Это только запасной путь, который выполняется после того, как исходный метод уже упал.

`createUserFallback(request)` получает тот же аргумент `request` из неудавшегося вызова `createUser(request)`. Именно это и означает объявление `method = "createUserFallback(request)"`: имена в скобках
должны быть именами параметров размеченного метода, и Kora передает именно их, в том же порядке, в резервный метод. Ссылка на имя, которое не является параметром, — ошибка компиляции.

Чтобы ограничить, какие сбои доходят до резервного метода, добавьте один параметр с аннотацией `@Fallback.Reason`. Он получает исключение, вызвавшее резервный путь, а все, что не является экземпляром
объявленного типа, пробрасывается без изменений:

===! ":fontawesome-brands-java: `Java`"

    ```java
    protected UserResponse createUserFallback(UserRequest request, @Fallback.Reason RuntimeException reason) {
        log.warn("Falling back on user creation: {}", reason.getMessage());
        return new UserResponse("pending-file-write", request.name(), request.email(), LocalDateTime.now());
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    protected open fun createUserFallback(request: UserRequest, @Fallback.Reason reason: RuntimeException): UserResponse {
        log.warn("Falling back on user creation: {}", reason.message)
        return UserResponse("pending-file-write", request.name, request.email, LocalDateTime.now())
    }
    ```

Тип параметра выбирается не свободно: это `RuntimeException`, когда размеченный метод не объявляет проверяемых исключений, `Exception`, когда объявляет, и `Throwable`, когда объявлен
`throws Throwable`. Допускается не более одного параметра `@Fallback.Reason`, и он не входит в число аргументов, перечисленных в `method = "..."`.

Резервный метод отлично подходит для плавной деградации, но он же способен скрыть настоящие сбои, если ответ слишком похож на успешный. Этот риск особенно важен для операций записи вроде
`createUser()`, где резервный метод может вернуть что-то полезное вызывающей стороне, хотя исходная запись на самом деле не выполнилась.

`@Fallback` поддерживает синхронные методы и `CompletionStage`. Обычный `Future` и реактивный `Publisher` отклоняются на этапе компиляции.

После компиляции сгенерированный прокси показывает решение о резервном пути рядом с исходным вызовом:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/java/kora-java-guide-resilient-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/resilient/service/$UserService__AopProxy.java
    ```

    ```java
    private UserResponse _createUser_AopProxy_FallbackKoraAspect(UserRequest request) {
        try {
            return super.createUser(request);
        } catch (Throwable _e) {
            var _fallbackObservation = fallbackTelemetry1.observe();
            try {
                _fallbackObservation.recordExecute(_e);
                return createUserFallback(request);
            } catch (Throwable _fallbackException) {
                _fallbackObservation.observeError(_fallbackException);
                throw _fallbackException;
            } finally {
                _fallbackObservation.end();
            }
        }
    }

    @Override
    public UserResponse createUser(UserRequest request) {
        return this._createUser_AopProxy_FallbackKoraAspect(request);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/kora-kotlin-guide-resilient-app/build/generated/ksp/main/kotlin/io/koraframework/guide/resilient/service/$UserService__AopProxy.kt
    ```

    ```kotlin
    private fun _createUser_AopProxy_FallbackKoraAspect(request: UserRequest): UserResponse = try {
      super.createUser(request)
    } catch (_e: Throwable) {
      val _fallbackObservation = fallbackTelemetry1.observe()
      try {
        _fallbackObservation.recordExecute(_e)
        createUserFallback(request)
      } catch (_fallbackException: Throwable) {
        _fallbackObservation.observeError(_fallbackException)
        throw _fallbackException
      } finally {
        _fallbackObservation.end()
      }
    }

    override fun createUser(request: UserRequest): UserResponse =
        _createUser_AopProxy_FallbackKoraAspect(request)
    ```

Это делает правило резервного метода наглядным: Kora сначала вызывает `super.createUser(request)`, и только если этот вызов упал, она фиксирует сбой и вызывает `createUserFallback(request)`. При
наличии параметра `@Fallback.Reason` в начале блока `catch` появляется охрана `if (!(_e instanceof RuntimeException)) { throw _e; }`.

## Ограничение времени { #timeout }

`Timeout` не дает медленным операциям бесконечно потреблять ресурсы. Даже когда сбой редок, зависший вызов способен навредить всему приложению, занимая потоки и емкость обработки запросов.

Ограничение времени полезно, когда:

- медленные операции хуже быстрой ошибки
- вызывающей стороне нужна предсказуемая верхняя граница задержки
- вы хотите, чтобы повторы или прерыватель работали поверх ограниченного времени выполнения

Применяйте осторожно, когда:

- таймаут короче нормальной здоровой задержки
- у операции есть побочные эффекты, которые продолжаются после того, как вызывающая сторона отвалилась по таймауту
- вы кладете повторы поверх таймаутов, не подумав об общей худшей задержке

`@Timeout` сохранила свое имя в Kora 2.0, но ее атрибут теперь класс спецификации, а не имя политики. Сначала добавьте конфигурацию таймаута:

`src/main/resources/application.conf`:

Полный справочник по конфигурации смотрите в [Resilient](../documentation/resilient.md).

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
      retry {
        default {
          delay = 20ms //(1)!
          attempts = 3 //(2)!
          delayStep = 20ms //(3)!
        }
      }
      timeout {
        default {
          duration = 100ms //(4)!
        }
      }
    }
    ```

    1. Начальная задержка перед повторной попыткой.
    2. Максимальное число повторных попыток.
    3. Линейная добавка к задержке на каждой следующей попытке.
    4. Длительность таймаута для защищаемой операции.

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      retry:
        default:
          delay: 20ms #(1)!
          attempts: 3 #(2)!
          delayStep: 20ms #(3)!
      timeout:
        default:
          duration: 100ms #(4)!
    ```

    1. Начальная задержка перед повторной попыткой.
    2. Максимальное число повторных попыток.
    3. Линейная добавка к задержке на каждой следующей попытке.
    4. Длительность таймаута для защищаемой операции.

Затем объявите спецификацию. Обратите внимание на имя контракта: интерфейс наследует `Timeouter`, а не `Timeout`, потому что `Timeout` — это аннотация аспекта.

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/io/koraframework/guide/resilient/service/DefaultTimeouter.java`:

    ```java
    package io.koraframework.guide.resilient.service;

    import io.koraframework.resilient.timeout.Timeouter;
    import io.koraframework.resilient.timeout.annotation.TimeoutSpec;

    @TimeoutSpec("resilient.timeout.default")
    public interface DefaultTimeouter extends Timeouter {

    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/io/koraframework/guide/resilient/service/DefaultTimeouter.kt`:

    ```kotlin
    package io.koraframework.guide.resilient.service

    import io.koraframework.resilient.timeout.Timeouter
    import io.koraframework.resilient.timeout.annotation.TimeoutSpec

    @TimeoutSpec("resilient.timeout.default")
    interface DefaultTimeouter : Timeouter
    ```

Теперь ограничьте операцию удаления:

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/io/koraframework/guide/resilient/service/UserService.java`:

    ```java
    @Timeout(DefaultTimeouter.class)
    public void deleteUser(String id) {
        boolean deleted = userRepository.deleteById(id);
        if (!deleted) {
            throw HttpServerResponseException.of(404, "User not found");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/io/koraframework/guide/resilient/service/UserService.kt`:

    ```kotlin
    @Timeout(DefaultTimeouter::class)
    open fun deleteUser(id: String) {
        if (!userRepository.deleteById(id)) {
            throw HttpServerResponseException.of(404, "User not found")
        }
    }
    ```

Эндпоинт остается `DELETE /users/{userId}`. Меняется только сервисный метод. Когда длительность истекает, вызывающая сторона получает `TimeoutExhaustedException`.

После компиляции сгенерированный прокси показывает, что таймаут ограничивает исходную операцию удаления:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/java/kora-java-guide-resilient-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/resilient/service/$UserService__AopProxy.java
    ```

    ```java
    private void _deleteUser_AopProxy_TimeoutKoraAspect(String id) {
        defaultTimeouter1.execute(() -> {
            super.deleteUser(id);
            return null;
        });
    }

    @Override
    public void deleteUser(String id) {
        this._deleteUser_AopProxy_TimeoutKoraAspect(id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/kora-kotlin-guide-resilient-app/build/generated/ksp/main/kotlin/io/koraframework/guide/resilient/service/$UserService__AopProxy.kt
    ```

    ```kotlin
    private fun _deleteUser_AopProxy_TimeoutKoraAspect(id: String) {
      defaultTimeouter1.execute(ThrowableRunnable { super.deleteUser(id) })
    }

    override fun deleteUser(id: String) {
      _deleteUser_AopProxy_TimeoutKoraAspect(id)
    }
    ```

Сгенерированный код особенно нагляден для методов без возвращаемого значения: Kora оборачивает `super.deleteUser(id)` в `defaultTimeouter1.execute(...)` и в Java возвращает `null` лишь для того, чтобы
подошла форма вызываемого объекта.

## Прерыватель { #circuit-breaker }

`CircuitBreaker` защищает систему от повторяющихся вызовов пути, который уже падает. Как только сбоев набирается достаточно, Kora размыкает прерыватель и на время начинает быстро отказывать вместо того,
чтобы снова и снова делать дорогую работу, которая, скорее всего, снова не удастся.

Этот шаблон особенно полезен, когда настоящая проблема не в логике вашего контроллера или сервиса, а в чем-то, от чего зависит метод: база данных, другой HTTP-сервис, брокер сообщений или любая
нестабильная нижестоящая операция. Без прерывателя каждый новый запрос продолжает пробовать тот же падающий путь, что тратит потоки, увеличивает задержку и часто усугубляет аварию.

Kora описывает прерыватель как прокси вокруг конкретного метода. Он следит за недавними вызовами и переходит между тремя классическими состояниями:

- `CLOSED`: вызовы проходят обычным образом, и Kora считает недавние сбои внутри настроенного окна
- `OPEN`: как только вызовов хватает для оценки (`minimumRequiredCalls`) и доля сбоев переходит `failureRateThreshold`, Kora перестает вызывать защищаемый метод и сразу отказывает с `CallNotPermittedException`
- `HALF_OPEN`: после истечения `waitDurationInOpenState` Kora пропускает лишь ограниченное число пробных вызовов (`permittedCallsInHalfOpenState`), чтобы проверить, восстановилась ли зависимость

Если пробные вызовы в полуоткрытом состоянии успешны, прерыватель снова замыкается, и обычный трафик возобновляется. Если один из них падает, прерыватель размыкается опять и начинает новый период
ожидания. В этом и есть главная ценность шаблона: дать нездоровой зависимости время восстановиться вместо непрерывного долбления, но при этом периодически проверять, здорова ли она снова.

Прерыватель полезен, когда:

- нижестоящая зависимость нездорова, и повторные вызовы только тратят ресурсы
- быстрый отказ лучше долгих повторяющихся таймаутов
- вам нужно окно восстановления, прежде чем снова пускать трафик

Применяйте осторожно, когда:

- пороги настроены слишком агрессивно, и здоровый трафик оказывается заблокирован
- сбои, которые следовало бы разделять, свалены в одну кучу
- прерыватель ставится вокруг очень дешевых внутрипроцессных операций, где цена срабатывания выше цены повтора

Kora 2.0 позволяет выбрать способ подсчета окна через ключ `type`, и от этого выбора зависит форма блока окна:

| `type`           | Блок окна    | Что считается                                                                  |
|------------------|--------------|--------------------------------------------------------------------------------|
| `STRIPED_APPROX` | `countBased` | По умолчанию. Приблизительный подсчет по полосам счетчиков, дешевле всего при конкуренции. |
| `FIXED_WINDOW`   | `countBased` | Точный подсчет по фиксированному числу вызовов. Проще всего рассуждать в тестах. |
| `RING_BUFFER`    | `countBased` | Точный подсчет по скользящему кольцевому буферу последних `windowSize` вызовов.  |
| `TIME_BASED`     | `timeBased`  | Подсчет по `windowDuration`, разбитой на `sampleCount` корзин, а не по вызовам.  |

Поскольку руководству нужен прерыватель, предсказуемо срабатывающий после двух сбоев, оно использует `FIXED_WINDOW`.

`src/main/resources/application.conf`:

Полный справочник по конфигурации смотрите в [Resilient](../documentation/resilient.md).

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
      retry {
        default {
          delay = 20ms //(1)!
          attempts = 3 //(2)!
          delayStep = 20ms //(3)!
        }
      }
      timeout {
        default {
          duration = 100ms //(4)!
        }
      }
      circuitbreaker {
        default {
          type = FIXED_WINDOW //(5)!
          countBased.windowSize = 2 //(6)!
          minimumRequiredCalls = 2 //(7)!
          failureRateThreshold = 100 //(8)!
          permittedCallsInHalfOpenState = 1 //(9)!
          waitDurationInOpenState = 200ms //(10)!
        }
      }
    }
    ```

    1. Начальная задержка перед повторной попыткой.
    2. Максимальное число повторных попыток.
    3. Линейная добавка к задержке на каждой следующей попытке.
    4. Длительность таймаута для защищаемой операции.
    5. Реализация окна. При отсутствии ключа используется `STRIPED_APPROX`.
    6. Число вызовов, хранимых в окне прерывателя.
    7. Минимальное число вызовов, прежде чем прерыватель оценивает сбои.
    8. Доля сбоев в процентах, при которой прерыватель размыкается.
    9. Число пробных вызовов, разрешенных в полуоткрытом состоянии.
    10. Время, которое прерыватель остается разомкнутым до проверки восстановления.

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      retry:
        default:
          delay: 20ms #(1)!
          attempts: 3 #(2)!
          delayStep: 20ms #(3)!
      timeout:
        default:
          duration: 100ms #(4)!
      circuitbreaker:
        default:
          type: FIXED_WINDOW #(5)!
          countBased:
            windowSize: 2 #(6)!
          minimumRequiredCalls: 2 #(7)!
          failureRateThreshold: 100 #(8)!
          permittedCallsInHalfOpenState: 1 #(9)!
          waitDurationInOpenState: 200ms #(10)!
    ```

    1. Начальная задержка перед повторной попыткой.
    2. Максимальное число повторных попыток.
    3. Линейная добавка к задержке на каждой следующей попытке.
    4. Длительность таймаута для защищаемой операции.
    5. Реализация окна. При отсутствии ключа используется `STRIPED_APPROX`.
    6. Число вызовов, хранимых в окне прерывателя.
    7. Минимальное число вызовов, прежде чем прерыватель оценивает сбои.
    8. Доля сбоев в процентах, при которой прерыватель размыкается.
    9. Число пробных вызовов, разрешенных в полуоткрытом состоянии.
    10. Время, которое прерыватель остается разомкнутым до проверки восстановления.

В двух ключах легко ошибиться. Размер окна живет в `countBased.windowSize`, а не на верхнем уровне секции, а минимальное число вызовов — это `minimumRequiredCalls`, а не `minimumNumberOfCalls`. Kora
проверяет весь блок при старте и отказывается собирать граф, называя проблемный ключ в сообщении, так что опечатка падает сразу, а не тихо отключает прерыватель.

Объявите спецификацию:

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/io/koraframework/guide/resilient/service/DefaultCircuitBreaker.java`:

    ```java
    package io.koraframework.guide.resilient.service;

    import io.koraframework.resilient.circuitbreaker.CircuitBreaker;
    import io.koraframework.resilient.circuitbreaker.annotation.CircuitBreakerSpec;

    @CircuitBreakerSpec("resilient.circuitbreaker.default")
    public interface DefaultCircuitBreaker extends CircuitBreaker {

    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/io/koraframework/guide/resilient/service/DefaultCircuitBreaker.kt`:

    ```kotlin
    package io.koraframework.guide.resilient.service

    import io.koraframework.resilient.circuitbreaker.CircuitBreaker
    import io.koraframework.resilient.circuitbreaker.annotation.CircuitBreakerSpec

    @CircuitBreakerSpec("resilient.circuitbreaker.default")
    interface DefaultCircuitBreaker : CircuitBreaker
    ```

И защитите метод обновления через `@CircuitBreakable`:

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/io/koraframework/guide/resilient/service/UserService.java`:

    ```java
    @CircuitBreakable(DefaultCircuitBreaker.class)
    public UserResponse updateUser(String id, UserRequest request) {
        boolean updated = userRepository.update(id, request.name(), request.email());
        if (!updated) {
            throw HttpServerResponseException.of(404, "User not found");
        }
        return new UserResponse(id, request.name(), request.email(), LocalDateTime.now());
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/io/koraframework/guide/resilient/service/UserService.kt`:

    ```kotlin
    @CircuitBreakable(DefaultCircuitBreaker::class)
    open fun updateUser(id: String, request: UserRequest): UserResponse {
        if (!userRepository.update(id, request.name, request.email)) {
            throw HttpServerResponseException.of(404, "User not found")
        }
        return UserResponse(id, request.name, request.email, LocalDateTime.now())
    }
    ```

Контроллер снова не меняется. `PUT /users/{userId}` по-прежнему вызывает `updateUser()`, но после достаточного числа сбоев прерыватель может разомкнуться и быстро отказывать.

После компиляции сгенерированный прокси показывает жизненный цикл прерывателя вокруг исходного обновления:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/java/kora-java-guide-resilient-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/resilient/service/$UserService__AopProxy.java
    ```

    ```java
    private UserResponse _updateUser_AopProxy_CircuitBreakerKoraAspect(String id, UserRequest request) {
        try {
            defaultCircuitBreaker1.acquire();
            var _result = super.updateUser(id, request);
            defaultCircuitBreaker1.releaseOnSuccess();
            return _result;
        } catch (CallNotPermittedException _e) {
            throw _e;
        } catch (Throwable _e) {
            defaultCircuitBreaker1.releaseOnError(_e);
            throw _e;
        }
    }

    @Override
    public UserResponse updateUser(String id, UserRequest request) {
        return this._updateUser_AopProxy_CircuitBreakerKoraAspect(id, request);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/kora-kotlin-guide-resilient-app/build/generated/ksp/main/kotlin/io/koraframework/guide/resilient/service/$UserService__AopProxy.kt
    ```

    ```kotlin
    private fun _updateUser_AopProxy_CircuitBreakerKoraAspect(id: String, request: UserRequest):
        UserResponse = try {
      defaultCircuitBreaker1.acquire()
      val t = super.updateUser(id, request)
      defaultCircuitBreaker1.releaseOnSuccess()
      t
    } catch (e: CallNotPermittedException) {
      throw e
    } catch (e: Throwable) {
      defaultCircuitBreaker1.releaseOnError(e)
      throw e
    }

    override fun updateUser(id: String, request: UserRequest): UserResponse =
        _updateUser_AopProxy_CircuitBreakerKoraAspect(id, request)
    ```

Этот фрагмент прямо показывает протокол прерывателя: получить разрешение, вызвать исходный метод, отпустить с успехом на хорошем результате и отпустить с ошибкой, когда защищаемый метод упал. Обратите
внимание, что `CallNotPermittedException` пробрасывается без учета, потому что отклоненный вызов — это прерыватель, делающий свою работу, а не новый сбой для подсчета.

## Предикат прерывателя { #circuit-breaker-predicate }

Теперь сделаем прерыватель умнее применительно к конкретно этому API. Мы не хотим, чтобы каждое исключение считалось сбоем прерывателя.

В этом руководстве `updateUser()` может упасть по двум очень разным причинам:

- пользователя действительно нет, и это нормальный бизнес-исход, который должен просто вернуть `404 Not Found`
- путь обновления по-настоящему нездоров, например потому что какая-то нижестоящая зависимость или внутренняя операция падает раз за разом

`CircuitBreakerPredicate` позволяет разделить эти случаи. Мы не хотим, чтобы отсутствующий пользователь толкал прерыватель к `OPEN`, потому что это научило бы прерыватель неверному представлению о
здоровье системы. Мы хотим, чтобы прерыватель реагировал только на сбои, действительно указывающие на нестабильность.

Kora вызывает этот предикат каждый раз, когда защищаемый метод выбрасывает исключение. Если `isCircuitBreakerFailure` возвращает `true`, сбой учитывается прерывателем. Если возвращает `false`,
исключение все равно доходит до вызывающей стороны, но не влияет на состояние прерывателя.

В Kora 2.0 предикат привязывается к прерывателю пометкой класса спецификации. Ключа `failurePredicateName` больше нет, как нет и метода `name()` для переопределения: привязкой служит `@Tag`.

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/io/koraframework/guide/resilient/service/CircuitBreakerFailurePredicate.java`:

    ```java
    package io.koraframework.guide.resilient.service;

    import io.koraframework.common.annotation.Component;
    import io.koraframework.common.annotation.Tag;
    import io.koraframework.http.server.common.response.HttpServerResponseException;
    import io.koraframework.resilient.circuitbreaker.CircuitBreakerPredicate;

    @Tag(DefaultCircuitBreaker.class)
    @Component
    public final class CircuitBreakerFailurePredicate implements CircuitBreakerPredicate {

        @Override
        public boolean isCircuitBreakerFailure(Throwable throwable) {
            if (throwable instanceof HttpServerResponseException exception) {
                return exception.code() >= 500;
            }
            return true;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/io/koraframework/guide/resilient/service/CircuitBreakerFailurePredicate.kt`:

    ```kotlin
    package io.koraframework.guide.resilient.service

    import io.koraframework.common.annotation.Component
    import io.koraframework.common.annotation.Tag
    import io.koraframework.http.server.common.response.HttpServerResponseException
    import io.koraframework.resilient.circuitbreaker.CircuitBreakerPredicate

    @Tag(DefaultCircuitBreaker::class)
    @Component
    class CircuitBreakerFailurePredicate : CircuitBreakerPredicate {

        override fun isCircuitBreakerFailure(throwable: Throwable): Boolean {
            if (throwable is HttpServerResponseException) {
                return throwable.code() >= 500
            }
            return true
        }
    }
    ```

Менять конфигурацию не нужно. Модуль, сгенерированный для `DefaultCircuitBreaker`, объявляет параметр `@Tag(DefaultCircuitBreaker.class) @Nullable CircuitBreakerPredicate`, поэтому ваш помеченный
компонент подхватывается просто фактом своего присутствия в графе. Уберите `@Tag` — и предикат больше не связан с этим прерывателем; уберите компонент целиком — и прерыватель вернется к подсчету всех
исключений.

Тот же механизм привязывает `RetryPredicate` к интерфейсу с `@RetrySpec`. У `@TimeoutSpec` и `@RateLimiterSpec` предиката нет: таймаут решается прошедшим временем, а ограничитель частоты —
разрешениями, так что классифицировать нечего.

## Ограничитель частоты { #rate-limiter }

`RateLimiter` появился в Kora 2.0. Там, где прерыватель реагирует на сбои, ограничитель частоты реагирует на объем: он задает потолок числа вызовов операции за период обновления и сразу отклоняет
остальные через `RateLimitExceededException`.

Ограничитель частоты полезен, когда:

- нижестоящая зависимость публикует жесткую квоту, которую нельзя превышать
- дорогая операция никогда не должна занимать весь пул потоков
- вам нужно обратное давление, которое предсказуемо, а не возникает само собой

Применяйте осторожно, когда:

- лимит общий для всех экземпляров, ведь у каждого экземпляра приложения свой локальный ограничитель
- у вызывающих сторон нет разумного способа отреагировать на отказ
- операция настолько дешева, что ограничение лишь добавляет задержку

Он следует ровно тому же шаблону спецификации. Добавьте конфигурацию:

===! ":material-code-json: `Hocon`"

    ```javascript
    resilient {
      ratelimiter {
        default {
          limitForPeriod = 100 //(1)!
          limitRefreshPeriod = 1s //(2)!
        }
      }
    }
    ```

    1. Число разрешений, выдаваемых в каждом периоде обновления.
    2. Как часто пополняется бюджет разрешений.

=== ":simple-yaml: `YAML`"

    ```yaml
    resilient:
      ratelimiter:
        default:
          limitForPeriod: 100 #(1)!
          limitRefreshPeriod: 1s #(2)!
    ```

    1. Число разрешений, выдаваемых в каждом периоде обновления.
    2. Как часто пополняется бюджет разрешений.

Объявите спецификацию и разметьте метод:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @RateLimiterSpec("resilient.ratelimiter.default")
    public interface DefaultRateLimiter extends RateLimiter {

    }
    ```

    ```java
    @RateLimited(DefaultRateLimiter.class)
    public List<UserResponse> getUsers(int page, int size, String sort) {
        // ...
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @RateLimiterSpec("resilient.ratelimiter.default")
    interface DefaultRateLimiter : RateLimiter
    ```

    ```kotlin
    @RateLimited(DefaultRateLimiter::class)
    open fun getUsers(page: Int, size: Int, sort: String): List<UserResponse> {
        // ...
    }
    ```

В отличие от остальных аспектов, `@RateLimited` поддерживает только синхронные методы и `Flow` в Kotlin. Возвращаемые типы `CompletionStage`, `Future` и реактивный `Publisher` отклоняются на этапе
компиляции, потому что разрешение, полученное перед асинхронным вызовом, ничего не говорит о том, когда этот вызов на самом деле завершится.

Дальше в руководстве ограничитель частоты не используется, так что оставьте `getUsers()` без него и переходите к комбинированной цепочке ниже.

## Комбинированный подход { #combined-pattern }

Последний шаг показывает, как несколько инструментов отказоустойчивости могут работать вместе на одном методе. `getUsers()` — хорошее место для демонстрации, потому что операции получения списков часто
становятся точками агрегации: сортировка, постраничная выдача, обращения к кешу, получение удаленных данных или дорогие чтения.

Эта комбинированная цепочка полезна, когда:

- вам нужен жесткий верхний предел по времени
- вы все же хотите несколько повторов для кратковременных сбоев
- вы также хотите, чтобы прерыватель размыкался, если метод продолжает падать

Применяйте осторожно, когда:

- вы наслаиваете слишком много политик и итоговое поведение становится трудно понять
- повторы вместе с таймаутом дают гораздо большую худшую задержку, чем ожидалось
- сбои сложнее отлаживать, потому что несколько слоев могут преобразовать итоговый путь ошибки

Все три блока конфигурации уже на месте, поэтому меняется только метод:

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/io/koraframework/guide/resilient/service/UserService.java`:

    ```java
    @CircuitBreakable(DefaultCircuitBreaker.class)
    @Retryable(DefaultRetry.class)
    @Timeout(DefaultTimeouter.class)
    public List<UserResponse> getUsers(int page, int size, String sort) {
        return userRepository.findAll().stream()
                .sorted(getComparator(sort))
                .skip((long) page * size)
                .limit(size)
                .toList();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/io/koraframework/guide/resilient/service/UserService.kt`:

    ```kotlin
    @CircuitBreakable(DefaultCircuitBreaker::class)
    @Retryable(DefaultRetry::class)
    @Timeout(DefaultTimeouter::class)
    open fun getUsers(page: Int, size: Int, sort: String): List<UserResponse> =
        userRepository.findAll()
            .sortedWith(getComparator(sort))
            .drop(page * size)
            .take(size)
    ```

Порядок аннотаций важен, потому что он задает порядок, в котором Kora применяет аспекты вокруг метода. Аннотация, ближайшая к методу, — самый внутренний слой, а перечисленная первой становится самым
внешним слоем.

В этом руководстве поток вызова такой:

1. `@CircuitBreakable`
2. `@Retryable`
3. `@Timeout`

Очень распространенный порядок, который хорошо работает во многих реальных системах:

1. `@Fallback` первым, чтобы он был самым внешним слоем и видел только те сбои, которые внутренние слои не смогли поглотить
2. `@CircuitBreakable`, чтобы повторяющиеся неудачные вызовы не продолжались бесконечно
3. `@Retryable`, чтобы ограниченное число раз повторить кратковременные сбои
4. `@Timeout`, чтобы ограничить одну попытку

Этот порядок распространен, потому что `@Timeout` — самый внутренний слой и ограничивает одну конкретную попытку, `@Retryable` оборачивает эту ограниченную попытку и повторяет ее ограниченное число раз,
`@CircuitBreakable` оборачивает поток повторов и наблюдает, продолжает ли падать операция целиком, а `@Fallback` — самый внешний слой, который получает шанс выдать ухудшенный ответ только после того,
как внутренние слои уже не справились. Это не единственный допустимый порядок, но обычно о нем проще всего рассуждать.

Поскольку прерыватель стоит снаружи повторов, обратите внимание, что именно он считает: одну исчерпанную последовательность повторов, а не каждую отдельную попытку. Обычно это то, что нужно, но это
значит, что `minimumRequiredCalls` считает операции целиком, а не попытки.

Помните также, что повторы и прерыватель можно по отдельности сузить помеченным предикатом, так что даже в комбинированной цепочке они не обязаны относиться ко всем исключениям одинаково. Это
соответствует [правилам комбинирования из документации](../documentation/resilient.md).

После компиляции сгенерированный прокси показывает точную вложенность для комбинированного метода:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/java/kora-java-guide-resilient-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/resilient/service/$UserService__AopProxy.java
    ```

    ```java
    private List<UserResponse> _getUsers_AopProxy_TimeoutKoraAspect(int page, int size, String sort) {
        return defaultTimeouter1.execute(() -> super.getUsers(page, size, sort));
    }

    private List<UserResponse> _getUsers_AopProxy_RetryKoraAspect(int page, int size, String sort) {
        return defaultRetry1.retry(() -> _getUsers_AopProxy_TimeoutKoraAspect(page, size, sort));
    }

    private List<UserResponse> _getUsers_AopProxy_CircuitBreakerKoraAspect(int page, int size, String sort) {
        try {
            defaultCircuitBreaker1.acquire();
            var _result = _getUsers_AopProxy_RetryKoraAspect(page, size, sort);
            defaultCircuitBreaker1.releaseOnSuccess();
            return _result;
        } catch (CallNotPermittedException _e) {
            throw _e;
        } catch (Throwable _e) {
            defaultCircuitBreaker1.releaseOnError(_e);
            throw _e;
        }
    }

    @Override
    public List<UserResponse> getUsers(int page, int size, String sort) {
        return this._getUsers_AopProxy_CircuitBreakerKoraAspect(page, size, sort);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/kora-kotlin-guide-resilient-app/build/generated/ksp/main/kotlin/io/koraframework/guide/resilient/service/$UserService__AopProxy.kt
    ```

    ```kotlin
    private fun _getUsers_AopProxy_TimeoutKoraAspect(
      page: Int,
      size: Int,
      sort: String,
    ): List<UserResponse> = defaultTimeouter1.execute(ThrowableCallable { super.getUsers(page, size, sort) })

    private fun _getUsers_AopProxy_RetryKoraAspect(
      page: Int,
      size: Int,
      sort: String,
    ): List<UserResponse> = defaultRetry1.retry(ThrowableCallable {
      _getUsers_AopProxy_TimeoutKoraAspect(page, size, sort)
    })

    private fun _getUsers_AopProxy_CircuitBreakerKoraAspect(
      page: Int,
      size: Int,
      sort: String,
    ): List<UserResponse> = try {
      defaultCircuitBreaker1.acquire()
      val t = _getUsers_AopProxy_RetryKoraAspect(page, size, sort)
      defaultCircuitBreaker1.releaseOnSuccess()
      t
    } catch (e: CallNotPermittedException) {
      throw e
    } catch (e: Throwable) {
      defaultCircuitBreaker1.releaseOnError(e)
      throw e
    }
    ```

Это самый ясный способ проверить порядок аспектов: публичный метод входит в прерыватель, прерыватель вызывает повторы, повторы вызывают таймаут, а таймаут наконец вызывает `super.getUsers(...)`.

## Сгенерированный код { #generated-code }

Kora генерирует для этого руководства два вида исходников, и их стоит различать.

Исходники спецификаций порождаются из `@RetrySpec`, `@TimeoutSpec`, `@CircuitBreakerSpec` и `@RateLimiterSpec`. Для каждого размеченного интерфейса процессор пишет реализацию и модуль:

```text
$DefaultRetry_Impl.java
$DefaultRetry_Module.java
```

`$DefaultRetry_Impl` наследует реализацию фреймворка (`KoraRetry`, `KoraTimeouter`, `KoraCircuitBreaker`, `KoraRateLimiter`) и закрепляет объявленный вами путь конфигурации. `$DefaultRetry_Module`
помечен `@Module`, читает этот путь в `RetryConfig` и публикует ваш интерфейс как компонент. Именно поэтому регистрировать что-либо вручную не нужно.

Исходник прокси порождается аспектами методов. Kora не меняет `UserService.java` или `UserService.kt` напрямую. Вместо этого она генерирует класс-наследник вокруг `UserService` и помещает поведение
отказоустойчивости в этот сгенерированный класс. Этот прокси решает, когда:

- повторить исходный вызов
- прекратить ожидание из-за таймаута
- закоротить вызов через прерыватель
- отклонить вызов, потому что лимит частоты исчерпан
- вызвать резервный метод после сбоя

Именно поэтому так важны правила наследования:

- в Java размеченный класс сервиса не должен быть `final`
- в Kotlin размеченный класс сервиса и размеченные методы должны быть `open`

После выполнения:

```bash
./gradlew clean classes
```

сгенерированный прокси можно посмотреть здесь:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/java/kora-java-guide-resilient-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/resilient/service/$UserService__AopProxy.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/kora-kotlin-guide-resilient-app/build/generated/ksp/main/kotlin/io/koraframework/guide/resilient/service/$UserService__AopProxy.kt
    ```

В предыдущих главах сгенерированные фрагменты показывались прямо рядом с породившей их возможностью. Используйте этот финальный раздел как карту: когда поведение удивляет, откройте прокси и найдите имя
метода, который отлаживаете.

Читать сгенерированный прокси полезно, когда:

- вы хотите подтвердить реальный порядок аспектов
- вы хотите понять, почему один инструмент отказоустойчивости срабатывает раньше другого
- вы выясняете, пришел сбой из тела вашего метода или из внешнего слоя отказоустойчивости
- вы хотите, чтобы AI-ассистент изучил реальное скомпилированное поведение фреймворка, а не гадал, как применяются аннотации

## Проверка приложения { #check-app }

Скомпилируйте приложение после добавления аннотаций и конфигурации:

```bash
./gradlew clean classes
```

Запустите тесты:

```bash
./gradlew test
```

Запустите приложение:

```bash
./gradlew run
```

Затем обратитесь к тем же HTTP-эндпоинтам из руководства по HTTP-серверу:

```bash
curl http://localhost:8080/users/1
curl "http://localhost:8080/users?page=0&size=10&sort=name"
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com"}'
curl -X PUT http://localhost:8080/users/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"John Updated","email":"john.updated@example.com"}'
curl -X DELETE http://localhost:8080/users/1
```

Пути эндпоинтов не меняются. Отказоустойчивость применяется внутри слоя сервиса.

## Лучшие практики { #best-practices }

- Добавляйте отказоустойчивость на существующую границу сервиса, а не создавайте отдельные демонстрационные методы вроде `getUserWithRetry()` или `deleteUserWithTimeout()`.
- Сохраняйте контракт контроллера стабильным, развивая поведение сервиса.
- Называйте интерфейсы-спецификации по политике, которую они представляют, а не по методу, который их использует, чтобы одну настроенную политику могли делить несколько методов.
- Начинайте с единственной секции `default` на шаблон, а именованные секции вводите только тогда, когда действительно нужно разное поведение.
- Внедряйте интерфейс-спецификацию, когда нужен императивный контроль: он уже и есть `Retry`, `Timeouter`, `CircuitBreaker` или `RateLimiter`.
- Держите Java-классы не `final`, а Kotlin-классы `open`, когда используете стиль AOP на аннотациях.
- Относитесь к резервному методу как к плавной деградации, а не как к скрытому слою хранения, и сужайте его через `@Fallback.Reason`, когда ухудшенного ответа заслуживают только некоторые сбои.
- Будьте сдержанны с повторами и таймаутами, чтобы общая худшая задержка оставалась понятной, и подумайте о `retryBudget`, когда зависимость делят несколько вызывающих сторон.
- Используйте помеченные предикаты, когда часть ошибок — допустимые бизнес-исходы и не должны влиять на состояние отказоустойчивости.
- Изучайте исходник сгенерированного прокси, когда поведение комбинированных аннотаций в рантайме кажется неожиданным.

## Итоги { #summary }

Вы начали с CRUD-сервиса, созданного в руководстве по HTTP-серверу, и сделали те же методы более устойчивыми:

- `getUser()` теперь повторяет кратковременные сбои
- `createUser()` умеет уходить в резервный ответ
- `deleteUser()` ограничен таймаутом
- `updateUser()` защищен прерывателем, предикат которого игнорирует ответы `404`
- `getUsers()` демонстрирует, как повторы, таймаут и прерыватель работают вместе

Каждая политика — небольшой типизированный интерфейс, указывающий на путь конфигурации, так что вся поверхность отказоустойчивости сервиса видна в четырех коротких файлах.

## Ключевые понятия { #key-concepts }

- Политика отказоустойчивости в Kora 2.0 — это интерфейс-спецификация: интерфейс, наследующий `Retry`, `Timeouter`, `CircuitBreaker` или `RateLimiter`, с соответствующей аннотацией `Spec`, значение которой — путь конфигурации.
- Аспекты методов ссылаются на спецификации по классу, поэтому `@Retryable(DefaultRetry.class)`, `@Timeout(DefaultTimeouter.class)`, `@CircuitBreakable(DefaultCircuitBreaker.class)` и `@RateLimited(DefaultRateLimiter.class)` проверяются на этапе компиляции.
- У `@Fallback` единственный атрибут `method` и необязательный параметр `@Fallback.Reason`, сужающий круг обрабатываемых исключений.
- Предикаты привязываются через `@Tag(DefaultCircuitBreaker.class)`: `CircuitBreakerPredicate.isCircuitBreakerFailure` и `RetryPredicate.isRetryFailure`.
- Окно прерывателя живет в `countBased.windowSize` (или в `timeBased` при `type = TIME_BASED`), а ключ минимального числа вызовов — `minimumRequiredCalls`.
- Отказоустойчивость на аннотациях требует в Java не `final` класса, а в Kotlin — `open` класса с `open` методами.
- Порядок аннотаций решает вложенность аспектов: аннотация ближе к методу — внутреннее.
- Исходник сгенерированного `$UserService__AopProxy` показывает, как Kora на самом деле наслаивает аспекты отказоустойчивости.

## Устранение неполадок { #troubleshooting }

**Аннотации отказоустойчивости не срабатывают:**

Убедитесь, что Java-класс не `final`, а Kotlin-класс и его методы `open`. Для стиля на аннотациях Kora использует сгенерированные AOP-обертки.

**`@RetrySpec can only be applied to an interface`:**

Спецификация должна быть `interface`, а не классом или записью. То же правило действует для `@TimeoutSpec`, `@CircuitBreakerSpec` и `@RateLimiterSpec`.

**`@RetrySpec annotated interface must extend Retry`:**

У каждой аннотации спецификации один соответствующий контракт: `@RetrySpec` требует `Retry`, `@TimeoutSpec` — `Timeouter`, `@CircuitBreakerSpec` — `CircuitBreaker`, `@RateLimiterSpec` — `RateLimiter`.
На `Timeouter` часто спотыкаются, потому что аннотация называется `@Timeout`.

**Хочу увидеть, где на самом деле применяются повторы, таймаут, прерыватель и резервный метод:**

Выполните:

```bash
./gradlew clean classes
```

Затем откройте:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/java/kora-java-guide-resilient-app/build/generated/sources/annotationProcessor/java/main/io/koraframework/guide/resilient/service/$UserService__AopProxy.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/kora-kotlin-guide-resilient-app/build/generated/ksp/main/kotlin/io/koraframework/guide/resilient/service/$UserService__AopProxy.kt
    ```

Этот сгенерированный файл показывает реальную логику оберток вокруг ваших методов `UserService` и является лучшим местом для проверки порядка аспектов и потока сбоев.

**Повторы делают эндпоинт медленнее, чем ожидалось:**

Повторы добавляют задержку и могут умножать общее время. Проверьте настроенные `attempts`, `delay` и `delayStep`, затем оцените худший бюджет времени. Если присутствует блок `backoff`, рост будет
мультипликативным, а не линейным.

**`CircuitBreaker 'default' property 'countBased' is not configured`:**

Всем типам, кроме `TIME_BASED`, нужен блок `countBased` с `windowSize`. Если вы выбрали `type = TIME_BASED`, задайте вместо него блок `timeBased` с `windowDuration`.

**Прерыватель никогда не размыкается:**

Проверьте, что в конфигурации используется `minimumRequiredCalls` и что `countBased.windowSize` не меньше его, затем убедитесь, что сбоев достаточно для перехода через `failureRateThreshold`.

**Прерыватель реагирует на бизнес-ошибки:**

Добавьте компонент `CircuitBreakerPredicate` с аннотацией `@Tag(DefaultCircuitBreaker.class)`, чтобы бизнес-исходы вроде `404 Not Found` не считались инфраструктурными сбоями.

**Мой предикат игнорируется:**

`@Tag` должен называть интерфейс-спецификацию, а не контракт. `@Tag(CircuitBreaker.class)` не привяжется, а `@Tag(DefaultCircuitBreaker.class)` привяжется.

**Резервный метод не вызывается:**

Проверьте, что имена внутри `@Fallback(method = "...")` — это параметры размеченного метода и что метод с подходящей сигнатурой существует в том же классе. Если резервный метод объявляет параметр
`@Fallback.Reason`, проверьте, что выброшенное исключение действительно является экземпляром типа этого параметра.

**Таймаут никогда не срабатывает:**

Убедитесь, что операция действительно превышает настроенную `duration`, и помните, что таймаут на блокирующем вызове прерывает ожидающего, а не обязательно саму работу.

**Gradle зависает или неожиданно падает:**

Остановите демоны Gradle и повторите:

```bash
./gradlew --stop
./gradlew clean classes
```

**Windows показывает AccessDeniedException в кеше Gradle:**

Обычно это значит, что другой процесс Gradle или Java еще держит файлы открытыми. Остановите демоны через `./gradlew --stop`, закройте запуски тестов в IDE и повторите сборку.

**Эндпоинт готовности недоступен:**

Системный HTTP-сервер использует порт `8085`. Проверьте:

```text
http://localhost:8085/system/readiness
```

## Что дальше? { #whats-next }

- [Наблюдаемость](observability.md), чтобы измерять число повторных попыток, сбои по таймауту, смены состояния прерывателя и использование резервного метода.
- [HTTP-клиент](http-client.md), чтобы применить отказоустойчивость вокруг исходящих вызовов.
- [HTTP-сервер продвинутый](http-server-advanced.md), а затем [HTTP-клиент продвинутый](http-client-advanced.md), если нужны продвинутые примеры исходящих вызовов.
- [Тестирование с JUnit](testing-junit.md), чтобы протестировать резервный метод и поведение при сбоях на уровне компонентов.
- [База данных JDBC](database-jdbc.md) перед черноящичным тестированием, если нужен сквозной путь тестов поверх JDBC.

## Помощь { #help }

Если возникнут сложности:

- сравните с [Kora Java Resilient App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-resilient-app) и [Kora Kotlin Resilient App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-resilient-app)
- посмотрите [документацию по Resilient](../documentation/resilient.md)
- перечитайте [HTTP-сервер](http-server.md) для базового CRUD-потока
- перечитайте [Тестирование с JUnit](testing-junit.md) для приемов проверки на уровне компонентов
