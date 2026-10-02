---
search:
  exclude: true
title: Шаблоны отказоустойчивости
summary: Extend the HTTP Server guide by applying Kora resilience annotations directly to your existing UserService methods
tags: resilient, retry, timeout, circuitbreaker, fallback, http-server, hocon
---

# Шаблоны отказоустойчивости { #resilience-patterns }

Это руководство знакомит с шаблонами отказоотказоустойчивости для сервисных методов Kora. В нем разбирается, как аннотации повторная попытка, ограничитель времени, прерыватель и резервный метод оборачивают операции приложения, как
конфигурация отказоустойчивости управляет поведением при сбоях и как HTTP API может оставаться неизменным, пока вызовы сервисов становятся более устойчивыми к отказам. Вы также увидите, как каждый паттерн
защищает от своего вида нестабильной зависимости или операции.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java Resilient App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-resilient-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin Resilient App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-resilient-app).

## Что вы создадите { #youll-build }

Вы улучшите `UserService` из руководства по HTTP-сервер с помощью:

- `@Retry` на `getUser()` для временных сбоев чтения
- `@Fallback` на `createUser()` для мягкой деградации, когда создание не удается
- `@Timeout` на `deleteUser()`, чтобы останавливать зависающие операции удаления
- `@CircuitBreaker` на `updateUser()`, чтобы останавливать повторяющиеся падающие обновления
- объединенной цепочки `@CircuitBreaker + @Retry + @Timeout` на `getUsers()`

## Что вам понадобится { #youll-need }

- JDK 17 или новее
- Gradle 7.0 или новее
- текстовый редактор или среда разработки
- рабочий проект из руководства [HTTP-сервер](http-server.md)

## Требования { #prerequisites }

!!! note "Обязательно: пройдите руководство по HTTP-сервер"

    Это руководство предполагает, что вы прошли **[HTTP-сервер](http-server.md)** и у вас уже есть `Application`, `UserController`, `UserService`, `UserRepository`, `InMemoryUserRepository`, `UserRequest` и `UserResponse`.

    Если вы еще не прошли руководство по HTTP-серверу, сначала сделайте это, потому что здесь паттерны отказоустойчивости добавляются в существующий CRUD API, а не создают API с нуля.

## Обзор { #overview }

[Устойчивость Kora](../documentation/resilient.md) — это управление тем, как приложение ведет себя, когда зависимость работает медленно, нестабильно или временно недоступна. Без явных правил
отказоустойчивости сбои обычно распространяются: одна медленная операция может занять потоки обработки запросов, повторяющиеся временные ошибки могут перегрузить зависимость, а падающий нижестоящий вызов
может сделать все конечные точки выглядящими сломанными.

Цель не в том, чтобы скрыть каждый сбой. Цель в том, чтобы сделать поведение при сбоях осознанным. Сервис должен знать, когда попробовать еще раз, когда перестать ждать, когда на время не обращаться к
зависимости и когда безопасный запасной путь допустим.

### Основы отказоустойчивости { #resilience-basics }

В этом руководстве HTTP-контракт остается неизменным. Поведение отказоустойчивости добавляется вокруг сервисных методов, потому что сервисы — это место, где прикладные операции встречаются с нестабильной
работой: вызовами хранилища, удаленными вызовами, дорогими вычислениями или фоновыми зависимостями. Если держать отказоустойчивость на этой границе, контроллеры сохраняют роль маршрутизации, а сервисные
операции становятся более защитными.

### Основные подходы { #core-patterns }

Модуль отказоустойчивости Kora предоставляет несколько паттернов, каждый со своей задачей:

- повторная попытка повторяет операцию, когда сбой может быть временным
- ограничитель времени перестает ждать, когда операция выполняется слишком долго
- прерыватель на некоторое время перестает вызывать операцию, которая повторно падает
- резервный метод предоставляет альтернативный результат или поведение, когда основной путь не сработал

Эти паттерны не стоит применять вслепую. Повтор неидемпотентной записи может продублировать работу. Слишком короткий тайм-аут может создавать ложные сбои. Слишком широкий запасной путь может скрыть
настоящие аварии. Руководство держит каждый паттерн видимым, чтобы компромисс был понятен.

### Конфигурация и композиция { #configuration-composition }

Поведение отказоустойчивости принадлежит конфигурации не меньше, чем аннотациям. Пороги, попытки, задержки и длительности тайм-аутов часто отличаются между локальной разработкой и промышленной средой.
Аннотации Kora отмечают, какой паттерн применяется к какому методу, а конфигурация управляет тем, насколько агрессивно работает этот паттерн.

Руководство также показывает объединенное поведение отказоотказоустойчивости. В настоящих сервисах путь чтения может нуждаться в повторная попытка, ограничитель времени и прерыватель одновременно. Важный урок — осознанно компоновать
эти паттерны вокруг хорошо определенной операции, а затем тестировать поведение как часть контракта сервиса.

Практический путь такой:

1. добавить модуль отказоустойчивости в граф приложения
2. аннотировать сервисные методы по одному паттерну за раз
3. настроить пороги, задержки и тайм-ауты в HOCON
4. смоделировать режимы отказа в тестах
5. проверить, что HTTP-контракт остается стабильным, пока поведение сервиса становится более защитным

## Зависимости { #dependencies }

Добавьте зависимость отказоустойчивости в существующий проект из руководства по HTTP-сервер.

===! ":fontawesome-brands-java: `Java`"

    `build.gradle`:

    ```groovy
    dependencies {
        implementation("ru.tinkoff.kora:resilient-kora")
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `build.gradle.kts`:

    ```kotlin
    dependencies {
        implementation("ru.tinkoff.kora:resilient-kora")
    }
    ```

## Модули { #modules }

Сначала включите инфраструктуру отказоотказоустойчивости в графе приложения Kora. Это делает аннотации повторная попытка, ограничитель времени, прерыватель и резервный метод доступными для ваших компонентов.

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/ru/tinkoff/kora/guide/resilient/Application.java`:

    ```java
    package ru.tinkoff.kora.guide.resilient;

    import ru.tinkoff.kora.application.graph.KoraApplication;
    import ru.tinkoff.kora.common.KoraApp;
    import ru.tinkoff.kora.config.hocon.HoconConfigModule;
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule;
    import ru.tinkoff.kora.json.module.JsonModule;
    import ru.tinkoff.kora.logging.logback.LogbackModule;
    import ru.tinkoff.kora.resilient.ResilientModule;

    @KoraApp
    public interface Application extends
            HoconConfigModule,
            UndertowHttpServerModule,
            JsonModule,
            LogbackModule,
            ResilientModule {  // <----- Подключили модуль

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/ru/tinkoff/kora/guide/resilient/Application.kt`:

    ```kotlin
    package ru.tinkoff.kora.guide.resilient

    import ru.tinkoff.kora.application.graph.KoraApplication
    import ru.tinkoff.kora.common.KoraApp
    import ru.tinkoff.kora.config.hocon.HoconConfigModule
    import ru.tinkoff.kora.http.server.undertow.UndertowHttpServerModule
    import ru.tinkoff.kora.json.module.JsonModule
    import ru.tinkoff.kora.logging.logback.LogbackModule
    import ru.tinkoff.kora.resilient.ResilientModule

    @KoraApp
    interface Application :
        HoconConfigModule,
        UndertowHttpServerModule,
        JsonModule,
        LogbackModule,
        ResilientModule  // <----- Подключили модуль

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

## Повторные попытки { #retry }

`Retry` — самое безопасное место для старта, потому что временные сбои чаще всего встречаются на чтении. Короткий сетевой сбой, временная проблема с соединением или краткая перегрузка часто исчезают,
если повторить ту же операцию через несколько мгновений.

Kora позволяет использовать отказоустойчивость и декларативно через аннотации, и императивно через API менеджеров, такие как `RetryManager`, `TimeoutManager`, `CircuitBreakerManager` и `FallbackManager`. В
этом руководстве мы используем AOP-стиль, потому что это самый короткий способ развить существующий `UserService`, а императивный подход описан
в [справочнике модуля отказоотказоустойчивости](../documentation/resilient.md).

Поскольку этот шаг использует аннотации, класс все еще должен удовлетворять правилам AOP:

- в Java класс не должен быть `final`
- в Kotlin класс должен быть `open`

Повторная попытка полезна, когда:

- сбои кратковременны и обычно проходят на следующей попытке
- операцию безопасно повторять
- дополнительная задержка от повторов допустима

Используйте его осторожно, когда:

- операция меняет состояние и может быть неидемпотентной
- нижестоящий сервис уже перегружен, и повторы усилят давление
- общий бюджет ожидания уже очень мал

Повторная попытка не обязана реагировать на каждое исключение. По умолчанию Kora использует встроенный предикат повторов, но вы можете сузить или заменить это поведение, реализовав `RetryPredicate` и привязав его
в конфигурации. Так вы говорите, какие сбои действительно временные и заслуживают повтора. Подробности о предикатах и конфигурации смотрите в [документации по отказоотказоустойчивости](../documentation/resilient.md).

Добавьте конфигурацию повторная попытка ровно там, где вводите аннотацию.

`src/main/resources/application.conf`:

Полный справочник по конфигурации смотрите в [отказоотказоустойчивости](../documentation/resilient.md).

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
    3. Прирост задержки между повторными попытками.

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
    3. Прирост задержки между повторными попытками.

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/ru/tinkoff/kora/guide/resilient/service/UserService.java`:

    ```java
    @Component
    public class UserService {

        private final UserRepository userRepository;

        public UserService(UserRepository userRepository) {
            this.userRepository = userRepository;
        }

        @Retry("default")
        public Optional<UserResponse> getUser(String id) {
            return userRepository.findById(id);
        }

        // other methods stay unchanged for now
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/ru/tinkoff/kora/guide/resilient/service/UserService.kt`:

    ```kotlin
    @Component
    open class UserService(
        private val userRepository: UserRepository,
    ) {

        @Retry("default")
        open fun getUser(id: String): UserResponse? = userRepository.findById(id)

        // other methods stay unchanged for now
    }
    ```

Контроллеру не нужна новая конечная точка. `GET /users/{userId}` уже делегирует в `getUser()`, поэтому поведение отказоотказоустойчивости автоматически применяется на границе сервиса.

После компиляции сгенерированный прокси показывает, что `@Retry` оборачивает исходный вызов метода напрямую:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-resilient-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/resilient/service/$UserService__AopProxy.java
    ```

    ```java
    private Optional<UserResponse> _getUser_AopProxy_RetryKoraAspect(String id) {
        return retry1.retry(() -> super.getUser(id));
    }

    @Override
    public Optional<UserResponse> getUser(String id) {
        return this._getUser_AopProxy_RetryKoraAspect(id);
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-resilient-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/resilient/service/$UserService__AopProxy.kt
    ```

    ```kotlin
    private fun _getUser_AopProxy_RetryKoraAspect(id: String): UserResponse? =
        retry1.retry(Retry.RetrySupplier { super.getUser(id) })

    override fun getUser(id: String): UserResponse? = _getUser_AopProxy_RetryKoraAspect(id)
    ```

Важная часть — `retry1.retry(() -> super.getUser(id))`: Kora сгенерировала границу повтора вокруг вашего сервисного метода, а ваш исходный код по-прежнему остается вызовом `super.getUser(id)` внутри
этой границы.

## Резервный метод { #fallback }

`Fallback` отвечает за мягкую деградацию. Если основной путь падает, вы возвращаете контролируемую альтернативу вместо простого распространения сбоя.

Kora снова поддерживает и AOP-аннотации, и императивное использование резервный метод через `FallbackManager`. В этом руководстве мы остаемся в стиле аннотаций, чтобы существующий метод `createUser()`
развивался на месте.

Резервный метод полезен, когда:

- можно вернуть безопасную замену или ответ об отложенной обработке
- пользовательский опыт лучше с ухудшенным ответом, чем с жестким сбоем
- у вас есть четко определенная резервная политика

Используйте его осторожно, когда:

- запасной путь слишком долго скрывает серьезный инцидент
- запасной путь может создать несогласованное бизнес-состояние
- команда начинает использовать резервный метод как тихую замену нормальной надежности хранения или доставки

Резервный метод также не обязан реагировать на каждое исключение. Kora может решать, должен ли конкретный сбой запускать запасной путь, через предикат. Если нужно управлять этим поведением,
реализуйте `FallbackPredicate` и подключите его через именованную конфигурацию. Смотрите раздел о предикатах в [документации по отказоотказоустойчивости](../documentation/resilient.md).

Теперь добавьте только то поведение с резервный метод, которое нужно для `createUser()`.

`src/main/resources/application.conf`:

Полный справочник по конфигурации смотрите в [отказоотказоустойчивости](../documentation/resilient.md).

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
    3. Прирост задержки между повторными попытками.

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
    3. Прирост задержки между повторными попытками.

Отдельный блок `fallback.default {}` здесь не нужен, потому что стандартное поведение резервный метод уже доступно.

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/ru/tinkoff/kora/guide/resilient/service/UserService.java`:

    ```java
    @Fallback(value = "default", method = "createUserFallback(request)")
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

    `src/main/kotlin/ru/tinkoff/kora/guide/resilient/service/UserService.kt`:

    ```kotlin
    @Fallback(value = "default", method = "createUserFallback(request)")
    open fun createUser(request: UserRequest): UserResponse {
        val generatedId = userRepository.save(request.name, request.email)
        return UserResponse(generatedId, request.name, request.email, LocalDateTime.now())
    }

    protected open fun createUserFallback(request: UserRequest): UserResponse {
        // Never do this in real systems: imagine we wrote the request to a file
        // and planned to recreate the user during application startup.
        return UserResponse("pending-file-write", request.name, request.email, LocalDateTime.now())
    }
    ```

Метод резервный метод не меняет контракт контроллера. `POST /users` по-прежнему возвращает `UserResponse`, но теперь сервис может мягко деградировать, когда основной путь падает.

Важно точно понимать, когда вызывается резервный метод:

1. Kora сначала вызывает исходный метод.
2. Если исходный метод успешно возвращает результат, резервный метод вообще не используется.
3. Если исходный метод выбрасывает исключение, Kora проверяет, может ли резервный метод обработать этот сбой.
4. Если сбой соответствует правилам резервный метод, Kora вызывает резервный метод, объявленный в `method = "..."`.
5. Результат резервный метода становится итоговым результатом, возвращенным вызывающему коду.

Поэтому резервный метод никогда не является основным путем выполнения. Это только резервный путь, который запускается после того, как исходный метод уже упал.

В этом примере `createUserFallback(request)` получает тот же аргумент `request` из упавшего вызова `createUser(request)`. Именно это означает объявление `method = "createUserFallback(request)"`: Kora
берет аргументы исходного метода и передает выбранные из них в резервный метод в объявленном порядке.

Поэтому резервный метод также нужно использовать осторожно. Он отлично подходит для мягкой деградации, но может скрыть реальные сбои, если запасной ответ слишком похож на настоящий успех. Этот риск особенно
важен для операций записи, таких как `createUser()`, где резервный метод может вернуть вызывающему коду что-то полезное, хотя исходная запись фактически не завершилась.

Kora поддерживает и AOP-использование на основе аннотаций, и императивное использование резервный метод через `FallbackManager`. В этом руководстве мы используем AOP-стиль, потому что он держит объяснение
близко к существующему сервисному методу.

После компиляции сгенерированный прокси показывает решение резервный метод рядом с исходным вызовом:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-resilient-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/resilient/service/$UserService__AopProxy.java
    ```

    ```java
    private UserResponse _createUser_AopProxy_FallbackKoraAspect(UserRequest request) {
        try {
            return super.createUser(request);
        } catch (Throwable _e) {
            if (fallback1.canFallback(_e)) {
                return createUserFallback(request);
            } else {
                throw _e;
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
    guides/kotlin/guide-kotlin-resilient-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/resilient/service/$UserService__AopProxy.kt
    ```

    ```kotlin
    private fun _createUser_AopProxy_FallbackKoraAspect(request: UserRequest): UserResponse = try {
      super.createUser(request)
    } catch (_e: Throwable) {
      if(fallback1.canFallback(_e)) {
        createUserFallback(request)
      } else {
        throw _e
      }
    }

    override fun createUser(request: UserRequest): UserResponse =
        _createUser_AopProxy_FallbackKoraAspect(request)
    ```

Это делает правило резервный метод конкретным: Kora сначала вызывает `super.createUser(request)`, и только если этот вызов выбрасывает исключение, спрашивает `fallback1.canFallback(_e)` перед
вызовом `createUserFallback(request)`.

## Ограничение времени { #timeout }

`Timeout` не дает медленным операциям бесконечно потреблять ресурсы. Даже если сбой редок, зависающий вызов все равно может повредить всему приложению, заняв потоки и емкость обработки запросов.

Kora поддерживает ограничитель времени и через аннотации, и через `TimeoutManager`. Здесь мы оставляем подход с аннотацией, потому что он естественно читается на существующем методе.

Ограничитель времени полезен, когда:

- медленные операции хуже быстрого отказа
- вызывающему коду нужна предсказуемая верхняя граница задержки
- вы хотите, чтобы повторная попытка или прерыватель работали поверх ограниченного времени выполнения

Используйте его осторожно, когда:

- тайм-аут короче обычной здоровой задержки
- операция имеет побочные эффекты, которые могут продолжиться после того, как вызывающий код перестал ждать
- вы накладываете повторная попытка поверх ограничитель времени, не думая об общей худшей задержке

Ограничитель времени сам по себе основан на длительности, но когда вы сочетаете его с повторная попытка, прерыватель или резервный метод, итоговый поток исключений все равно определяет, что произойдет дальше. Это означает, что
последующие слои могут реагировать или не реагировать на исключения ограничитель времени в зависимости от настроенных предикатов. Подробности о композиции смотрите
в [документации по отказоотказоустойчивости](../documentation/resilient.md).

Теперь добавьте конфигурацию ограничитель времени для `deleteUser()`.

`src/main/resources/application.conf`:

Полный справочник по конфигурации смотрите в [отказоотказоустойчивости](../documentation/resilient.md).

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
    3. Прирост задержки между повторными попытками.
    4. Длительность тайм-аута для защищенной операции.

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
    3. Прирост задержки между повторными попытками.
    4. Длительность тайм-аута для защищенной операции.

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/ru/tinkoff/kora/guide/resilient/service/UserService.java`:

    ```java
    @Timeout("default")
    public void deleteUser(String id) {
        boolean deleted = userRepository.deleteById(id);
        if (!deleted) {
            throw HttpServerResponseException.of(404, "User not found");
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/ru/tinkoff/kora/guide/resilient/service/UserService.kt`:

    ```kotlin
    @Timeout("default")
    open fun deleteUser(id: String) {
        val deleted = userRepository.deleteById(id)
        if (!deleted) {
            throw HttpServerResponseException.of(404, "User not found")
        }
    }
    ```

Конечная точка остается `DELETE /users/{userId}`. Меняется только метод сервиса.

После компиляции сгенерированный прокси показывает, что ограничитель времени ограничивает исходную операцию удаления:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-resilient-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/resilient/service/$UserService__AopProxy.java
    ```

    ```java
    private void _deleteUser_AopProxy_TimeoutKoraAspect(String id) {
        timeout1.execute(() -> {
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
    guides/kotlin/guide-kotlin-resilient-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/resilient/service/$UserService__AopProxy.kt
    ```

    ```kotlin
    private fun _deleteUser_AopProxy_TimeoutKoraAspect(id: String) {
      timeout1.execute(Callable { super.deleteUser(id) })
    }

    override fun deleteUser(id: String) {
      _deleteUser_AopProxy_TimeoutKoraAspect(id)
    }
    ```

Сгенерированный код особенно полезен для методов `void`: Kora оборачивает `super.deleteUser(id)` в `timeout1.execute(...)` и возвращает `null` только для соответствия форме лямбды.

## Прерыватель { #circuit-breaker }

`CircuitBreaker` защищает систему от повторных вызовов пути, который уже падает. Когда происходит достаточно сбоев, Kora открывает прерыватель и некоторое время быстро завершает вызовы ошибкой вместо
того, чтобы снова и снова выполнять дорогую работу, которая, скорее всего, снова упадет.

Этот паттерн особенно полезен, когда настоящая проблема не в логике вашего контроллера или сервиса, а в том, от чего зависит метод: базе данных, другом HTTP-сервисе, брокере сообщений или любой
нестабильной нижестоящей операции. Без прерыватель каждый новый запрос продолжает пробовать тот же падающий путь, что тратит потоки, увеличивает задержку и часто ухудшает аварию.

Kora описывает прерыватель как прокси вокруг конкретного метода. Он наблюдает за недавними вызовами и проходит через три классических состояния:

- `CLOSED`: вызовы пропускаются обычно, а Kora считает недавние сбои внутри настроенного `slidingWindowSize`
- `OPEN`: когда есть достаточно вызовов для оценки (`minimumRequiredCalls`) и доля сбоев пересекает `failureRateThreshold`, Kora перестает вызывать защищенный метод и сразу быстро отказывает
- `HALF-OPEN`: после истечения `waitDurationInOpenState` Kora разрешает только ограниченное число пробных вызовов (`permittedCallsInHalfOpenState`), чтобы проверить, восстановилась ли зависимость

Если эти пробные вызовы в полуоткрытом состоянии проходят успешно, прерыватель снова закрывается и обычный трафик возобновляется. Если один из них падает, прерыватель снова открывается и начинает новый период
ожидания. В этом главная ценность паттерна: дать нездоровой зависимости время восстановиться вместо постоянного давления на нее, но при этом периодически проверять, стала ли она снова здоровой.

Kora поддерживает и аннотированное, и императивное использование прерыватель. Здесь мы сохраняем декларативный стиль, потому что он чисто ложится на существующий метод `updateUser()`. Если нужен
более тонкий контроль, можно внедрить `CircuitBreakerManager` и использовать прерыватель императивно, как описано в [документации модуля отказоотказоустойчивости](../documentation/resilient.md).

Прерыватель полезен, когда:

- нижестоящая зависимость нездорова, и повторные вызовы только тратят ресурсы
- быстрый отказ лучше долгих повторяющихся тайм-аутов
- вы хотите дать окно восстановления перед повторным допуском трафика

Используйте его осторожно, когда:

- пороги настроены слишком агрессивно и здоровый трафик блокируется
- сбои, которые должны обрабатываться по-разному, все сгруппированы вместе
- прерыватель поставлен вокруг очень дешевых внутрипроцессных операций, где цена срабатывания выше цены повтора

Прерыватель не обязан считать каждое исключение сбоем прерывателя. Kora поддерживает пользовательскую фильтрацию через `CircuitBreakerPredicate`, поэтому вы можете решить, какие ошибки должны
влиять на состояние прерывателя, а какие нужно игнорировать. В этом руководстве мы используем это на следующем шаге, потому что `updateUser()` может законно возвращать `404 Not Found`, а отсутствующий
пользователь не должен выглядеть как нестабильность инфраструктуры.

Начните с добавления самой конфигурации прерыватель.

`src/main/resources/application.conf`:

Полный справочник по конфигурации смотрите в [отказоотказоустойчивости](../documentation/resilient.md).

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
          slidingWindowSize = 2 //(5)!
          minimumRequiredCalls = 2 //(6)!
          failureRateThreshold = 100 //(7)!
          permittedCallsInHalfOpenState = 1 //(8)!
          waitDurationInOpenState = 200ms //(9)!
        }
      }
    }
    ```

    1. Начальная задержка перед повторной попыткой.
    2. Максимальное число повторных попыток.
    3. Прирост задержки между повторными попытками.
    4. Длительность тайм-аута для защищенной операции.
    5. Число вызовов, хранящихся в скользящем окне прерыватель.
    6. Минимальное число вызовов, необходимое до оценки сбоев прерыватель.
    7. Доля сбоев, при которой прерыватель открывается.
    8. Число пробных вызовов, разрешенных, пока прерыватель находится в полуоткрытом состоянии.
    9. Время, которое прерыватель остается открытым перед проверкой восстановления.

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
          slidingWindowSize: 2 #(5)!
          minimumRequiredCalls: 2 #(6)!
          failureRateThreshold: 100 #(7)!
          permittedCallsInHalfOpenState: 1 #(8)!
          waitDurationInOpenState: 200ms #(9)!
    ```

    1. Начальная задержка перед повторной попыткой.
    2. Максимальное число повторных попыток.
    3. Прирост задержки между повторными попытками.
    4. Длительность тайм-аута для защищенной операции.
    5. Число вызовов, хранящихся в скользящем окне прерыватель.
    6. Минимальное число вызовов, необходимое до оценки сбоев прерыватель.
    7. Доля сбоев, при которой прерыватель открывается.
    8. Число пробных вызовов, разрешенных, пока прерыватель находится в полуоткрытом состоянии.
    9. Время, которое прерыватель остается открытым перед проверкой восстановления.

Ключевая деталь здесь в том, что Kora использует `minimumRequiredCalls`, а не `minimumNumberOfCalls`.

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/ru/tinkoff/kora/guide/resilient/service/UserService.java`:

    ```java
    @CircuitBreaker("default")
    public UserResponse updateUser(String id, UserRequest request) {
        boolean updated = userRepository.update(id, request.name(), request.email());
        if (!updated) {
            throw HttpServerResponseException.of(404, "User not found");
        }
        return new UserResponse(id, request.name(), request.email(), LocalDateTime.now());
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/ru/tinkoff/kora/guide/resilient/service/UserService.kt`:

    ```kotlin
    @CircuitBreaker("default")
    open fun updateUser(id: String, request: UserRequest): UserResponse {
        val updated = userRepository.update(id, request.name, request.email)
        if (!updated) {
            throw HttpServerResponseException.of(404, "User not found")
        }
        return UserResponse(id, request.name, request.email, LocalDateTime.now())
    }
    ```

Контроллер снова остается тем же. `PUT /users/{userId}` по-прежнему вызывает `updateUser()`, но после достаточного числа сбоев прерыватель может открыться и быстро отказывать.

После компиляции сгенерированный прокси показывает жизненный цикл прерыватель вокруг исходного обновления:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-resilient-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/resilient/service/$UserService__AopProxy.java
    ```

    ```java
    private UserResponse _updateUser_AopProxy_CircuitBreakerKoraAspect(String id, UserRequest request) {
        try {
            circuitBreaker1.acquire();
            var _result = super.updateUser(id, request);
            circuitBreaker1.releaseOnSuccess();
            return _result;
        } catch (CallNotPermittedException _e) {
            throw _e;
        } catch (Throwable _e) {
            circuitBreaker1.releaseOnError(_e);
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
    guides/kotlin/guide-kotlin-resilient-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/resilient/service/$UserService__AopProxy.kt
    ```

    ```kotlin
    private fun _updateUser_AopProxy_CircuitBreakerKoraAspect(id: String, request: UserRequest):
        UserResponse = try {
      circuitBreaker1.acquire()
      val t = super.updateUser(id, request)
      circuitBreaker1.releaseOnSuccess()
      t
    } catch (e: CallNotPermittedException) {
      throw e
    } catch (e: Throwable) {
      circuitBreaker1.releaseOnError(e)
      throw e
    }

    override fun updateUser(id: String, request: UserRequest): UserResponse =
        _updateUser_AopProxy_CircuitBreakerKoraAspect(id, request)
    ```

Этот фрагмент прямо показывает протокол прерывателя: получить разрешение, вызвать исходный метод, отметить успех при хорошем результате и отметить ошибку, когда защищенный метод падает.

## Предикат прерывателя { #circuit-breaker-predicate }

Теперь сделаем прерыватель умнее для этого конкретного API. Мы не хотим, чтобы каждое исключение считалось сбоем прерыватель.

В этом руководстве `updateUser()` может падать по двум очень разным причинам:

- пользователь действительно не существует, это нормальный бизнес-исход и должен просто возвращать `404 Not Found`
- путь обновления действительно нездоров, например из-за того, что какая-то нижестоящая зависимость или внутренняя операция повторно падает

`CircuitBreakerFailurePredicate` позволяет разделить эти случаи. Мы не хотим, чтобы отсутствующий пользователь толкал прерыватель к `OPEN`, потому что это научило бы прерыватель неверному выводу о
здоровье системы. Мы хотим, чтобы прерыватель реагировал только на сбои, которые действительно указывают на нестабильность.

Kora вызывает этот предикат всякий раз, когда защищенный метод выбрасывает исключение. Если предикат возвращает `true`, этот сбой учитывается прерыватель. Если он возвращает `false`, исключение
все равно возвращается вызывающему коду, но не влияет на состояние прерывателя.

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/ru/tinkoff/kora/guide/resilient/service/CircuitBreakerFailurePredicate.java`:

    ```java
    @Component
    public final class CircuitBreakerFailurePredicate implements CircuitBreakerPredicate {

        @Override
        public String name() {
            return "RecordServerErrorsOnly";
        }

        @Override
        public boolean test(Throwable throwable) {
            if (throwable instanceof HttpServerResponseException exception) {
                return exception.code() >= 500;
            }
            return true;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/ru/tinkoff/kora/guide/resilient/service/CircuitBreakerFailurePredicate.kt`:

    ```kotlin
    @Component
    class CircuitBreakerFailurePredicate : CircuitBreakerPredicate {

        override fun name(): String = "RecordServerErrorsOnly"

        override fun test(throwable: Throwable): Boolean {
            return if (throwable is HttpServerResponseException) {
                throwable.code() >= 500
            } else {
                true
            }
        }
    }
    ```

Затем привяжите его в конфигурации прерыватель:

`src/main/resources/application.conf`:

Полный справочник по конфигурации смотрите в [отказоотказоустойчивости](../documentation/resilient.md).

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
          slidingWindowSize = 2 //(5)!
          minimumRequiredCalls = 2 //(6)!
          failureRateThreshold = 100 //(7)!
          permittedCallsInHalfOpenState = 1 //(8)!
          waitDurationInOpenState = 200ms //(9)!
          failurePredicateName = "RecordServerErrorsOnly" //(10)!
        }
      }
    }
    ```

    1. Начальная задержка перед повторной попыткой.
    2. Максимальное число повторных попыток.
    3. Прирост задержки между повторными попытками.
    4. Длительность тайм-аута для защищенной операции.
    5. Число вызовов, хранящихся в скользящем окне прерыватель.
    6. Минимальное число вызовов, необходимое до оценки сбоев прерыватель.
    7. Доля сбоев, при которой прерыватель открывается.
    8. Число пробных вызовов, разрешенных, пока прерыватель находится в полуоткрытом состоянии.
    9. Время, которое прерыватель остается открытым перед проверкой восстановления.
    10. Значение для `resilient.circuitbreaker.default.failurePredicateName`.

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
          slidingWindowSize: 2 #(5)!
          minimumRequiredCalls: 2 #(6)!
          failureRateThreshold: 100 #(7)!
          permittedCallsInHalfOpenState: 1 #(8)!
          waitDurationInOpenState: 200ms #(9)!
          failurePredicateName: "RecordServerErrorsOnly" #(10)!
    ```

    1. Начальная задержка перед повторной попыткой.
    2. Максимальное число повторных попыток.
    3. Прирост задержки между повторными попытками.
    4. Длительность тайм-аута для защищенной операции.
    5. Число вызовов, хранящихся в скользящем окне прерыватель.
    6. Минимальное число вызовов, необходимое до оценки сбоев прерыватель.
    7. Доля сбоев, при которой прерыватель открывается.
    8. Число пробных вызовов, разрешенных, пока прерыватель находится в полуоткрытом состоянии.
    9. Время, которое прерыватель остается открытым перед проверкой восстановления.
    10. Значение для `resilient.circuitbreaker.default.failurePredicateName`.

## Комбинированный подход { #combined-pattern }

Финальный шаг показывает, как несколько инструментов отказоустойчивости могут совместно работать на одном методе. `getUsers()` хорошо подходит для демонстрации, потому что операции получения списка часто
становятся точками агрегации: сортировка, постраничный вывод, обращения к кешу, удаленное получение данных или дорогие чтения.

Kora позволяет выразить ту же объединенную логику и декларативно через аннотации, и императивно через API менеджеров. В этом руководстве мы остаемся на декларативном пути, потому что порядок виден
прямо над методом.

Эта объединенная цепочка полезна, когда:

- вам нужна жесткая верхняя граница времени
- вы все еще хотите несколько повторов для временных сбоев
- вы также хотите, чтобы прерыватель открылся, если метод продолжает падать

Используйте ее осторожно, когда:

- вы накладываете слишком много политик и делаете итоговое поведение трудным для понимания
- повторные попытки вместе с ограничитель времени создают намного большую худшую задержку, чем ожидалось
- сбои становится сложнее отлаживать, потому что несколько слоев могут преобразовать финальный путь ошибки

Добавьте те же блоки конфигурации, которые нужны объединенному методу.

`src/main/resources/application.conf`:

Полный справочник по конфигурации смотрите в [отказоотказоустойчивости](../documentation/resilient.md).

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
          slidingWindowSize = 2 //(5)!
          minimumRequiredCalls = 2 //(6)!
          failureRateThreshold = 100 //(7)!
          permittedCallsInHalfOpenState = 1 //(8)!
          waitDurationInOpenState = 200ms //(9)!
          failurePredicateName = "RecordServerErrorsOnly" //(10)!
        }
      }
    }
    ```

    1. Начальная задержка перед повторной попыткой.
    2. Максимальное число повторных попыток.
    3. Прирост задержки между повторными попытками.
    4. Длительность тайм-аута для защищенной операции.
    5. Число вызовов, хранящихся в скользящем окне прерыватель.
    6. Минимальное число вызовов, необходимое до оценки сбоев прерыватель.
    7. Доля сбоев, при которой прерыватель открывается.
    8. Число пробных вызовов, разрешенных, пока прерыватель находится в полуоткрытом состоянии.
    9. Время, которое прерыватель остается открытым перед проверкой восстановления.
    10. Значение для `resilient.circuitbreaker.default.failurePredicateName`.

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
          slidingWindowSize: 2 #(5)!
          minimumRequiredCalls: 2 #(6)!
          failureRateThreshold: 100 #(7)!
          permittedCallsInHalfOpenState: 1 #(8)!
          waitDurationInOpenState: 200ms #(9)!
          failurePredicateName: "RecordServerErrorsOnly" #(10)!
    ```

    1. Начальная задержка перед повторной попыткой.
    2. Максимальное число повторных попыток.
    3. Прирост задержки между повторными попытками.
    4. Длительность тайм-аута для защищенной операции.
    5. Число вызовов, хранящихся в скользящем окне прерыватель.
    6. Минимальное число вызовов, необходимое до оценки сбоев прерыватель.
    7. Доля сбоев, при которой прерыватель открывается.
    8. Число пробных вызовов, разрешенных, пока прерыватель находится в полуоткрытом состоянии.
    9. Время, которое прерыватель остается открытым перед проверкой восстановления.
    10. Значение для `resilient.circuitbreaker.default.failurePredicateName`.

===! ":fontawesome-brands-java: `Java`"

    `src/main/java/ru/tinkoff/kora/guide/resilient/service/UserService.java`:

    ```java
    @CircuitBreaker("default")
    @Retry("default")
    @Timeout("default")
    public List<UserResponse> getUsers(int page, int size, String sort) {
        return userRepository.findAll().stream()
                .sorted(getComparator(sort))
                .skip((long) page * size)
                .limit(size)
                .toList();
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    `src/main/kotlin/ru/tinkoff/kora/guide/resilient/service/UserService.kt`:

    ```kotlin
    @CircuitBreaker("default")
    @Retry("default")
    @Timeout("default")
    open fun getUsers(page: Int, size: Int, sort: String): List<UserResponse> =
        userRepository.findAll().stream()
            .sorted(getComparator(sort))
            .skip((page.toLong()) * size)
            .limit(size.toLong())
            .toList()
    ```

Порядок аннотаций важен, потому что он определяет порядок, в котором Kora применяет аспекты вокруг метода. Другими словами, аннотация, ближайшая к методу, становится самым внутренним слоем, а
аннотация, указанная первой, становится самым внешним слоем.

В этом руководстве процесс вызова такой:

1. `@CircuitBreaker`
2. `@Retry`
3. `@Timeout`

Очень распространенный порядок, который хорошо работает для многих реальных систем:

1. `@Fallback` последним, если вам действительно нужен ухудшенный резервный ответ
2. `@CircuitBreaker`, чтобы остановить повторяющиеся падающие вызовы, которые иначе продолжались бы бесконечно
3. `@Retry`, чтобы ограниченно повторять временные сбои
4. `@Timeout`, чтобы ограничить одну попытку

Такой порядок распространен, потому что `@Timeout` является самым внутренним слоем и ограничивает одну конкретную попытку, `@Retry` оборачивает эту ограниченную попытку и повторяет ее ограниченное
число раз, `@CircuitBreaker` оборачивает поток повторов и наблюдает, продолжает ли вся операция падать, а `@Fallback` является самым внешним слоем, который получает шанс вернуть ухудшенный ответ
только после того, как внутренние слои уже упали. Это не единственно допустимый порядок, но обычно его проще всего понимать.

Также помните, что эти аспекты могут реагировать только на выбранные сбои. Повторная попытка, прерыватель и резервный метод все могут быть настроены пользовательскими предикатами, поэтому даже в объединенной цепочке
они не обязаны одинаково трактовать каждое исключение. Это соответствует [правилам комбинирования в документации](../documentation/resilient.md#combination).

После компиляции сгенерированный прокси показывает точную вложенность для объединенного метода:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-resilient-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/resilient/service/$UserService__AopProxy.java
    ```

    ```java
    private List<UserResponse> _getUsers_AopProxy_TimeoutKoraAspect(int page, int size, String sort) {
        return timeout1.execute(() -> super.getUsers(page, size, sort));
    }

    private List<UserResponse> _getUsers_AopProxy_RetryKoraAspect(int page, int size, String sort) {
        return retry1.retry(() -> _getUsers_AopProxy_TimeoutKoraAspect(page, size, sort));
    }

    private List<UserResponse> _getUsers_AopProxy_CircuitBreakerKoraAspect(int page, int size, String sort) {
        try {
            circuitBreaker1.acquire();
            var _result = _getUsers_AopProxy_RetryKoraAspect(page, size, sort);
            circuitBreaker1.releaseOnSuccess();
            return _result;
        } catch (CallNotPermittedException _e) {
            throw _e;
        } catch (Throwable _e) {
            circuitBreaker1.releaseOnError(_e);
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
    guides/kotlin/guide-kotlin-resilient-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/resilient/service/$UserService__AopProxy.kt
    ```

    ```kotlin
    private fun _getUsers_AopProxy_TimeoutKoraAspect(
      page: Int,
      size: Int,
      sort: String,
    ): List<UserResponse> = timeout1.execute(Callable { super.getUsers(page, size, sort) })

    private fun _getUsers_AopProxy_RetryKoraAspect(
      page: Int,
      size: Int,
      sort: String,
    ): List<UserResponse> = retry1.retry(Retry.RetrySupplier {
      _getUsers_AopProxy_TimeoutKoraAspect(page, size, sort)
    })

    private fun _getUsers_AopProxy_CircuitBreakerKoraAspect(
      page: Int,
      size: Int,
      sort: String,
    ): List<UserResponse> = try {
      circuitBreaker1.acquire()
      val t = _getUsers_AopProxy_RetryKoraAspect(page, size, sort)
      circuitBreaker1.releaseOnSuccess()
      t
    } catch (e: Throwable) {
      circuitBreaker1.releaseOnError(e)
      throw e
    }
    ```

Это самый ясный способ проверить порядок аспектов: публичный метод входит в прерыватель, прерыватель вызывает повторная попытка, повторная попытка вызывает ограничитель времени, и ограничитель времени наконец вызывает `super.getUsers(...)`.

## Сгенерированный код { #generated-code }

Аннотации отказоустойчивости в этом руководстве применяются через AOP во время компиляции так же, как аннотации проверки данных и кеширования.

Kora не изменяет `UserService.java` или `UserService.kt` напрямую. Вместо этого она генерирует подкласс-прокси вокруг `UserService` и помещает поведение отказоотказоустойчивости в этот сгенерированный класс. Этот
прокси решает, когда:

- повторить исходный вызов
- перестать ждать из-за ограничитель времени
- быстро оборвать вызов через прерыватель
- вызвать резервный метод после сбоя

Именно поэтому правила наследования так важны:

- в Java аннотированный сервисный класс не должен быть `final`
- в Kotlin аннотированный сервисный класс и аннотированные методы должны быть `open`

После запуска:

```bash
./gradlew clean classes
```

можно изучить сгенерированный прокси здесь:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-resilient-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/resilient/service/$UserService__AopProxy.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-resilient-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/resilient/service/$UserService__AopProxy.kt
    ```

Этот файл — самое практичное место, где видно, как Kora компонует методы, введенные выше:

- `@Retry`
- `@Fallback`
- `@Timeout`
- `@CircuitBreaker`

Предыдущие главы показывали сгенерированные фрагменты прямо рядом с возможностью, которая их породила. Используйте этот финальный раздел как карту: когда поведение удивляет, откройте прокси и найдите
имя метода, который отлаживаете.

Читать сгенерированный прокси полезно, когда:

- вы хотите подтвердить реальный порядок аспектов
- вы хотите понять, почему один инструмент отказоустойчивости реагирует раньше другого
- вы отлаживаете, пришел ли сбой из тела вашего метода или из внешнего слоя отказоустойчивости
- вы хотите, чтобы ИИ-помощник изучил фактическое скомпилированное поведение фреймворка, а не угадывал, как применяются аннотации

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

Затем выполните те же HTTP-конечные точки из руководства HTTP-сервер:

```bash
curl http://localhost:8080/users/1
curl http://localhost:8080/users?page=0&size=10&sort=name
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com"}'
curl -X PUT http://localhost:8080/users/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"John Updated","email":"john.updated@example.com"}'
curl -X DELETE http://localhost:8080/users/1
```

Пути конечных точек не меняются. Устойчивость применяется внутри сервисного слоя.

## Лучшие практики { #best-practices }

- Добавляйте отказоустойчивость к существующей сервисной границе вместо создания отдельных демонстрационных методов вроде `getUserWithRetry()` или `deleteUserWithTimeout()`.
- Держите контракт контроллера стабильным, пока развиваете поведение сервиса.
- Начните с одной конфигурации отказоустойчивости `default`, затем вводите именованные конфигурации только когда действительно нужны разные поведения.
- Помните, что Kora поддерживает и AOP-аннотации, и императивные менеджеры, и выбирайте стиль, в котором код проще всего понимать.
- Держите Java-классы не-`final`, а Kotlin-классы `open`, когда используете AOP-стиль на основе аннотаций.
- Относитесь к резервный метод как к мягкой деградации, а не как к скрытому слою постоянного хранения.
- Будьте консервативны с повторная попытка и ограничитель времени, чтобы общая худшая задержка оставалась понятной.
- Используйте пользовательские предикаты, когда некоторые ошибки являются допустимыми бизнес-исходами и не должны влиять на состояние отказоустойчивости.
- Изучайте сгенерированный исходник прокси, когда поведение объединенных аннотаций во время выполнения кажется неожиданным.

## Итоги { #summary }

Вы взяли CRUD-сервис, созданный в руководстве HTTP-сервер, и сделали те же методы более устойчивыми:

- `getUser()` теперь повторяет временные сбои
- `createUser()` может вернуться к резервному ответу
- `deleteUser()` ограничен тайм-аутом
- `updateUser()` защищен прерыватель
- `getUsers()` демонстрирует, как повторная попытка, ограничитель времени и прерыватель работают вместе

В результате руководство развивает тот же контракт API, а не заменяет его отдельными конечными точками только для отказоустойчивости.

## Ключевые понятия { #key-concepts }

- Устойчивость Kora можно использовать и через AOP-аннотации, и через императивные API менеджеров.
- Устойчивость на основе аннотаций в Java требует не-`final` класс, а в Kotlin — `open` класс.
- `@Retry`, `@Timeout`, `@CircuitBreaker` и `@Fallback` решают разные режимы отказа и должны выбираться осознанно.
- `CircuitBreakerPredicate` позволяет исключить бизнес-ошибки, такие как `404`, из статистики прерывателя.
- Порядок аннотаций важен, когда несколько паттернов отказоустойчивости объединены.
- `minimumRequiredCalls` — правильный ключ прерыватель в конфигурации Kora.
- исходник сгенерированного `$UserService__AopProxy` показывает, как Kora на самом деле наслаивает аспекты отказоустойчивости

## Устранение неполадок { #troubleshooting }

**Аннотации отказоустойчивости не срабатывают:**

Убедитесь, что Java-класс не является `final`, а Kotlin-класс является `open`. Kora использует сгенерированные AOP-обертки для стиля на основе аннотаций.

**Я хочу увидеть, где на самом деле применяются повторная попытка, ограничитель времени, прерыватель и резервный метод:**

Запустите:

```bash
./gradlew clean classes
```

Затем изучите:

===! ":fontawesome-brands-java: `Java`"

    ```text
    guides/guide-resilient-app/build/generated/sources/annotationProcessor/java/main/ru/tinkoff/kora/guide/resilient/service/$UserService__AopProxy.java
    ```

=== ":simple-kotlin: `Kotlin`"

    ```text
    guides/kotlin/guide-kotlin-resilient-app/build/generated/ksp/main/kotlin/ru/tinkoff/kora/guide/resilient/service/$UserService__AopProxy.kt
    ```

Этот сгенерированный файл показывает фактическую логику оберток вокруг методов `UserService` и является лучшим местом для проверки порядка аспектов и потока сбоев.

**Повторные попытки делают конечную точку медленнее ожидаемого:**

Повторы добавляют задержку и могут умножить общую задержку. Проверьте настроенные `attempts`, `delay` и `delayStep`, затем оцените худший временной бюджет.

**Прерыватель никогда не открывается:**

Проверьте, что в конфигурации используется `minimumRequiredCalls`, а не `minimumNumberOfCalls`, и убедитесь, что происходит достаточно сбоев для пересечения порога.

**Прерыватель реагирует на бизнес-ошибки:**

Добавьте пользовательский `CircuitBreakerPredicate` и привяжите его через `failurePredicateName`, чтобы бизнес-исходы вроде `404 Not Found` не считались инфраструктурными сбоями.

**Резервный метод не вызывается:**

Проверьте, что сигнатура резервный метода совпадает с объявлением метода, используемым в `@Fallback(value = "default", method = "...")`.

**Ограничитель времени никогда не срабатывает:**

Убедитесь, что операция действительно превышает настроенную длительность ограничитель времени.

**Gradle зависает или неожиданно падает:**

Остановите демоны Gradle и запустите повторно:

```bash
./gradlew --stop
./gradlew clean classes
```

**Windows показывает AccessDeniedException в кеше Gradle:**

Обычно это означает, что другой процесс Gradle или Java все еще держит файлы открытыми. Остановите демоны через `./gradlew --stop`, закройте запускатели тестов в среда разработки и повторите сборку.

**Конечная точка готовности недоступна:**

Приватный HTTP-сервер использует порт `8085`. Проверьте:

```text
http://localhost:8085/system/readiness
```

## Что дальше? { #whats-next }

- [Наблюдаемость](observability.md), чтобы измерять попытки повторная попытка, сбои ограничитель времени, изменения состояния прерыватель и использование резервный метод.
- [HTTP-клиент](http-client.md), чтобы применять отказоустойчивость вокруг исходящих вызовов.
- [Продвинутый HTTP-сервер](http-server-advanced.md), а затем [Продвинутый HTTP-клиент](http-client-advanced.md), если нужны продвинутые примеры исходящих вызовов.
- [Тестирование с JUnit](testing-junit.md), чтобы тестировать резервный метод и поведение при сбоях на уровне компонентов.
- [База данных JDBC](database-jdbc.md) перед руководством по тестированию как черный ящик, если вам нужен сквозной путь тестирования с JDBC.

## Помощь { #help }

Если вы столкнулись с проблемами:

- сравните с [Kora Java Resilient App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-resilient-app) и [Kora Kotlin Resilient App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-resilient-app)
- проверьте [документацию по отказоотказоустойчивости](../documentation/resilient.md)
- вернитесь к [HTTP-сервер](http-server.md) для базового CRUD-потока
- вернитесь к [Тестирование с JUnit](testing-junit.md) для шаблонов проверки на уровне компонентов
