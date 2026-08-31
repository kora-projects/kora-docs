---
search:
  exclude: true
title: Пробы с Kora
summary: Build focused liveness and readiness probes for a Kora HTTP service, including the system server endpoints, warm-up readiness, built-in framework probes, response semantics, and orchestration.
description: "Step-by-step liveness and readiness probes for a Kora HTTP service: the LivenessProbe and ReadinessProbe interfaces from io.koraframework:common, probe endpoints on the system HTTP server, the httpServer.system.port, livenessPath and readinessPath configuration, custom probe components registered as a plain @Component, warm-up readiness, built-in framework probes, aggregation across several probes, the 200/503/408 response contract, and Kubernetes probe wiring."
agent:
  use_when: "Use this file for questions about adding health checks to a Kora application step by step: LivenessProbe, ReadinessProbe, LivenessProbeFailure, ReadinessProbeFailure, /system/liveness, /system/readiness, httpServer.system.port 8085, livenessPath and readinessPath, why a probe does not need @Root or a tag, what 'Probe is not ready yet' means, the 30 second probe timeout and 408 response, built-in readiness probes of the HTTP and gRPC servers, readiness during graceful shutdown, and mapping probes to Kubernetes livenessProbe and readinessProbe."
tags: observability, probes, liveness, readiness, health-checks, kubernetes, system-server
---

# Пробы с Kora { #observability-probes-kora }

Это руководство посвящено только пробам. Вы возьмете приложение из руководства по HTTP-серверу и дадите платформе два ответа, по которым она может действовать: цел ли процесс и должен ли этот экземпляр
прямо сейчас принимать трафик.

===! ":fontawesome-brands-java: `Java`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Java Observability App](https://github.com/kora-projects/kora-examples/tree/master/guides/java/kora-java-guide-observability-app).

=== ":simple-kotlin: `Kotlin`"

    Если в процессе захочется сверить результат, используйте готовое рабочее приложение: [Kora Kotlin Observability App](https://github.com/kora-projects/kora-examples/tree/master/guides/kotlin/kora-kotlin-guide-observability-app).

## Что вы создадите { #youll-build }

Вы добавите:

- конечные точки `/system/liveness` и `/system/readiness` на системном порту
- пробу жизнеспособности для самого процесса
- пробу готовности, сообщающую о периоде прогрева
- вторую пробу готовности, сообщающую о состоянии внутреннего компонента
- понимание кодов ответа и тел, которые увидит платформа
- проверки проб в тесте и подключение проб в манифесте Kubernetes

## Что вам понадобится { #youll-need }

- JDK 25 или новее
- Gradle 9+
- Docker, если хотите запустить черноящичный smoke-тест локально
- Текстовый редактор или IDE
- Пройденное [Руководство по HTTP-серверу](http-server.md)

Артефакты Kora 2.0 собраны под Java 25, поэтому JDK, которым компилируется приложение, должен быть версии 25 или новее.

## Требования { #prerequisites }

!!! note "Необходимая основа"

    Это руководство предполагает, что вы прошли **[Руководство по HTTP-серверу](http-server.md)** и у вас уже есть HTTP-контроллеры, DTO, репозиторий, сервис и конфигурация из него.

    Если руководство по HTTP-серверу еще не пройдено, начните с него: это руководство по наблюдаемости сохраняет тот же HTTP-слой и надстраивает телеметрию поверх него.

## Обзор { #overview }

Пробы — самый маленький сигнал наблюдаемости и единственный, у которого есть зубы. Метрики и трассировки читают люди, разбирающиеся в проблеме. Пробы читают машины, которые по ответу будут действовать:
Kubernetes перезапустит ваш процесс, балансировщик выведет экземпляр из ротации, деплой откажется продолжаться. Никто не будет вчитываться в нюансы, поэтому ответ должен быть правильным.

Все держится на разделении двух вопросов, которые звучат похоже, а значат совершенно разное. Жизнеспособность спрашивает: *«этот процесс сломан безвозвратно, нужно ли его перезапустить?»* Готовность
спрашивает: *«может ли этот экземпляр обслужить запрос прямо сейчас?»* Приложение вполне закономерно может быть живым, но не готовым — оно прогревает кэш, доводит инициализацию до конца или сбрасывает
трафик при выключении. Ответ на второй вопрос через первый — это то, как сервис попадает в цикл перезапусков из-за секундной недоступности зависимости.

### Модель пробы { #probe-model }

Проба возвращает либо `null`, либо ошибку. `null` означает «все в порядке». Ошибка несет одно короткое сообщение о том, что не так. Это вся модель целиком, и ее прямолинейность — это замысел: нет
деградированного состояния, нет процентов, нет ничего, что оркестратору пришлось бы трактовать.

Жизнеспособность должна быть **консервативной**. Ее провал убивает процесс. Это правильная реакция на заклиненный пул потоков или невосстановимое повреждение внутреннего состояния и неправильная — на
базу данных, которая была недоступна две секунды. В сомнительном случае жизнеспособность возвращает `null`.

Готовность может быть **строгой**. Ее провал всего лишь останавливает трафик; процесс продолжает работать и может восстановиться сам. Поэтому именно ей место заниматься прогревом, временно пропавшей
обязательной зависимостью и сливом трафика при выключении.

В этом руководстве готовность моделирует прогрев. Первые полсекунды приложение говорит: «я живо, но еще не готово». Затем оно начинает возвращать `null`, и экземпляр входит в ротацию.

### Инструменты { #tools }

`LivenessProbe` и `ReadinessProbe` — это интерфейсы Kora с единственным методом `probe()` у каждого. `LivenessProbeFailure` и `ReadinessProbeFailure` — записи с единственным полем `message`, и это
сообщение становится телом HTTP-ответа.

**Системный HTTP-сервер** отдает обе конечные точки. Он слушает собственный порт, отдельный от публичного API, поэтому оркестратор может опрашивать здоровье, не задевая бизнес-трафик и не делая эти
конечные точки доступными снаружи кластера.

**Обнаружение компонентов** отвечает за связывание. Вы пишете обычный `@Component`, реализующий интерфейс; Kora находит все такие компоненты и передает их в конечную точку. Нет ни реестра, который надо
обновлять, ни аннотации, которую надо помнить.

### Эксплуатационная семантика { #operational-semantics }

Считайте пробу договором между приложением и платформой. Приложение коротко сообщает состояние, платформа применяет правила:

- жизнеспособность в порядке → не трогать процесс
- жизнеспособность нарушена → процесс можно перезапустить
- готовность в порядке → направлять трафик на этот экземпляр
- готовность нарушена → перестать направлять сюда трафик, но оставить процесс работать

Практическое следствие: смешивание двух проверок — это настоящий механизм аварии. Если общая база данных пропала на секунду, а вы поместили эту проверку в жизнеспособность, то жизнеспособность падает
одновременно у всех экземпляров сервиса, и оркестратор перезапускает весь парк — превращая секундную заминку в холодный старт. Та же проверка в готовности просто придержит трафик, пока база не
вернется.

## Зависимости { #dependencies }

Никаких. `LivenessProbe` и `ReadinessProbe` живут в артефакте `io.koraframework:common`, который приходит транзитивно вместе с уже подключенным модулем HTTP-сервера.

===! ":fontawesome-brands-java: `Java`"

    ```groovy
    dependencies {
        // ... existing dependencies from the HTTP server guide ...
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    dependencies {
        // ... existing dependencies from the HTTP server guide ...
    }
    ```

## Модули { #modules }

Здесь тоже добавлять нечего. Конечные точки дает `UndertowSystemHttpServerModule`, а `UndertowPublicHttpServerModule` — модуль, уже подключенный в руководстве по HTTP-серверу, — наследует его.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends
            HoconConfigModule,
            JsonModule,
            LogbackModule,
            UndertowPublicHttpServerModule {  // <----- Already gives you both probe endpoints

        static void main(String[] args) {
            KoraApplication.run(ApplicationGraph::graph);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application :
        HoconConfigModule,
        JsonModule,
        LogbackModule,
        UndertowPublicHttpServerModule  // <----- Already gives you both probe endpoints

    fun main() {
        KoraApplication.run(ApplicationGraph::graph)
    }
    ```

Оба пути проб обслуживаются независимо от того, написали вы пробу или нет. Если ни одна проба не зарегистрирована, они отвечают `200 OK`, и это осознанный выбор: приложение, которое не задумывалось о
здоровье, все равно сообщает «работаю», а не блокирует собственный деплой.

Приложение вообще без публичного API — воркер, консьюмер Kafka — может подключить только `UndertowSystemHttpServerModule` и получить конечные точки проб, не поднимая публичный сервер.

## Конфигурация { #config }

Пробы живут на системном порту рядом с `/metrics`.

Полный справочник по конфигурации — в [Пробах](../documentation/probes.md) и [HTTP-сервере](../documentation/http-server.md#system-server).

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
      port = 8080 //(1)!
      system {
        port = 8085 //(2)!
        livenessPath = "/system/liveness" //(3)!
        readinessPath = "/system/readiness" //(4)!
      }
    }
    ```

    1.  Публичный HTTP-порт для эндпоинтов приложения (по умолчанию: `8080`).
    2.  Системный HTTP-порт, обслуживающий пробы и метрики (по умолчанию: `8085`).
    3.  Путь конечной точки жизнеспособности на системном сервере (по умолчанию: `/system/liveness`).
    4.  Путь конечной точки готовности на системном сервере (по умолчанию: `/system/readiness`).

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      port: 8080 #(1)!
      system:
        port: 8085 #(2)!
        livenessPath: "/system/liveness" #(3)!
        readinessPath: "/system/readiness" #(4)!
    ```

    1.  Публичный HTTP-порт для эндпоинтов приложения (по умолчанию: `8080`).
    2.  Системный HTTP-порт, обслуживающий пробы и метрики (по умолчанию: `8085`).
    3.  Путь конечной точки жизнеспособности на системном сервере (по умолчанию: `/system/liveness`).
    4.  Путь конечной точки готовности на системном сервере (по умолчанию: `/system/readiness`).

Каждый из этих ключей и так уже имеет это значение по умолчанию, поэтому приложение работает, даже если не писать ни одного из них. Выписать их все равно стоит: эти пути потом копируются в манифест
Kubernetes, в healthcheck Compose и в стратегию ожидания Testcontainers, и именно наличие их в конфигурации удерживает эти четыре места в согласии друг с другом.

## Проба жизнеспособности { #liveness-probe }

Зарегистрируйте обычный компонент, реализующий `LivenessProbe`. Возврат `null` означает, что процесс жив.

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/io/koraframework/guide/observability/health/ApplicationHealthProbe.java`:

    ```java
    package io.koraframework.guide.observability.health;

    import io.koraframework.common.annotation.Component;
    import io.koraframework.common.liveness.LivenessProbe;
    import io.koraframework.common.liveness.LivenessProbeFailure;

    @Component //(1)!
    public final class ApplicationHealthProbe implements LivenessProbe {

        @Override
        public LivenessProbeFailure probe() {
            return null; //(2)!
        }
    }
    ```

    1.  Достаточно обычного компонента. Пробе не нужен ни `@Root`, ни тег.
    2.  `null` — это успех. Все остальное — ошибка с сообщением.

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/io/koraframework/guide/observability/health/ApplicationHealthProbe.kt`:

    ```kotlin
    package io.koraframework.guide.observability.health

    import io.koraframework.common.annotation.Component
    import io.koraframework.common.liveness.LivenessProbe
    import io.koraframework.common.liveness.LivenessProbeFailure

    @Component //(1)!
    class ApplicationHealthProbe : LivenessProbe {
        override fun probe(): LivenessProbeFailure? = null //(2)!
    }
    ```

    1.  Достаточно обычного компонента. Пробе не нужен ни `@Root`, ни тег.
    2.  `null` — это успех. Все остальное — ошибка с сообщением.

Возвращаемый тип помечен `@Nullable` из [JSpecify](https://jspecify.dev/) в `Java`, поэтому реализация на `Kotlin` обязана объявлять результат как `LivenessProbeFailure?`.

Проба жизнеспособности, которая всегда возвращает `null`, все равно приносит пользу: сам факт ответа конечной точки доказывает, что системный сервер поднят, граф собран, а процесс отзывчив, а не завис.
Не поддавайтесь искушению сделать ее умной. Вопрос, на который она отвечает, — «поможет ли перезапуск?», и почти для всех видов отказов честный ответ: нет.

## Проба готовности { #readiness-probe }

Готовность — это то место, где живет интересная логика, потому что ее провал дешев и обратим.

### Прогрев { #warmup }

===! ":fontawesome-brands-java: `Java`"

    Создайте `src/main/java/io/koraframework/guide/observability/health/CustomReadinessProbe.java`:

    ```java
    package io.koraframework.guide.observability.health;

    import io.koraframework.common.annotation.Component;
    import io.koraframework.common.readiness.ReadinessProbe;
    import io.koraframework.common.readiness.ReadinessProbeFailure;

    import java.time.Duration;
    import java.time.Instant;

    @Component
    public final class CustomReadinessProbe implements ReadinessProbe {

        private static final Duration WARMUP_PERIOD = Duration.ofMillis(500);

        private final Instant startedAt = Instant.now();

        @Override
        public ReadinessProbeFailure probe() {
            var readyAt = startedAt.plus(WARMUP_PERIOD);
            if (Instant.now().isBefore(readyAt)) {
                return new ReadinessProbeFailure("Service is warming up"); //(1)!
            }
            return null;
        }
    }
    ```

    1.  Это сообщение становится телом ответа `503`, поэтому пусть оно говорит что-то полезное человеку, читающему алерт.

=== ":simple-kotlin: `Kotlin`"

    Создайте `src/main/kotlin/io/koraframework/guide/observability/health/CustomReadinessProbe.kt`:

    ```kotlin
    package io.koraframework.guide.observability.health

    import io.koraframework.common.annotation.Component
    import io.koraframework.common.readiness.ReadinessProbe
    import io.koraframework.common.readiness.ReadinessProbeFailure
    import java.time.Duration
    import java.time.Instant

    @Component
    class CustomReadinessProbe : ReadinessProbe {
        private val startedAt = Instant.now()

        override fun probe(): ReadinessProbeFailure? {
            val readyAt = startedAt.plus(Duration.ofMillis(500))
            return if (Instant.now().isBefore(readyAt)) {
                ReadinessProbeFailure("Service is warming up") //(1)!
            } else {
                null
            }
        }
    }
    ```

    1.  Это сообщение становится телом ответа `503`, поэтому пусть оно говорит что-то полезное человеку, читающему алерт.

Полсекунды — демонстрационное значение, при котором поведение можно увидеть через `curl`. Настоящий прогрев — это то, что вашему сервису действительно нужно доделать в первую очередь: предзагрузка кэша,
таблица правил, модель, начальная синхронизация.

### Готовность компонента { #component-readiness }

Kora собирает **все** компоненты, реализующие `ReadinessProbe`, и запускает их все, поэтому условиям готовности не обязательно жить в одном классе. Их разделение держит каждую пробу сфокусированной и
дает куда более полезное сообщение об ошибке, чем одна общая проверка.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class ComponentReadinessProbe implements ReadinessProbe { //(1)!

        private final SomeComponent component;

        public ComponentReadinessProbe(SomeComponent component) {
            this.component = component;
        }

        @Override
        public ReadinessProbeFailure probe() {
            if (component.isInitialized()) { //(2)!
                return null;
            }
            return new ReadinessProbeFailure("SomeComponent is not initialized yet");
        }
    }
    ```

    1.  Компонентов `ReadinessProbe` может быть сколько угодно; конечная точка падает, если падает любой из них.
    2.  Проверяйте состояние **внутреннего** компонента, а не внешней зависимости.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ComponentReadinessProbe(
        private val component: SomeComponent
    ) : ReadinessProbe { //(1)!

        override fun probe(): ReadinessProbeFailure? {
            return if (component.isInitialized) { //(2)!
                null
            } else {
                ReadinessProbeFailure("SomeComponent is not initialized yet")
            }
        }
    }
    ```

    1.  Компонентов `ReadinessProbe` может быть сколько угодно; конечная точка падает, если падает любой из них.
    2.  Проверяйте состояние **внутреннего** компонента, а не внешней зависимости.

Каждая проба своего вида выполняется на собственном виртуальном потоке, а конечная точка агрегирует результаты: `200` — только когда все вернули `null`, `503` — как только упала хотя бы одна. Если упало
несколько, телом ответа становится сообщение первой упавшей пробы в порядке регистрации.

???+ warning "Рекомендация"

    **Пробы, которые напрямую проверяют внешние зависимости — базы данных, очереди или другие сервисы, — не рекомендуются.**

    Временная недоступность внешней зависимости не должна автоматически перезапускать приложение. Для таких случаев используйте паттерн [CircuitBreaker](../documentation/resilient.md#circuitbreaker).

Проба вызывается на каждый запрос к ее конечной точке, и несколько запросов могут накладываться, поэтому `probe()` обязан быть дешевым, без побочных эффектов и безопасным для конкурентного вызова.
Вычисляйте все дорогое заранее в самом компоненте, а `probe()` пусть только читает уже известное состояние.

## Встроенные пробы { #built-in-probes }

Несколько компонентов Kora сами реализуют `ReadinessProbe` и агрегируются вместе с вашими без какой-либо дополнительной обвязки:

| Компонент | Модуль | Сообщает `не готов`, когда |
|-----------|--------|---------------------------|
| `UndertowHttpServer` | `io.koraframework:http-server-undertow` | публичный [HTTP-сервер](../documentation/http-server.md) еще не начал слушать или уже начал выключение |
| `GrpcServer` | `io.koraframework:grpc-server` | [gRPC-сервер](../documentation/grpc-server.md) еще не стартовал или выключается |
| `JdbcDataSource` | `io.koraframework:database-jdbc` | включен `jdbc.readinessProbe` и соединение из пула не проходит проверку |

Именно поэтому ответ `200` на `GET /system/readiness` — надежный сигнал «приложение поднялось» даже до того, как вы написали хоть одну собственную пробу, и именно поэтому его правильно ждать
оркестратору, smoke-тесту или тест-контейнеру вместо строки лога о старте, формулировка которой контрактом не является.

Собственный слушатель системного сервера намеренно не входит в эту агрегацию. Он зарегистрирован под отдельным тегом, и именно это позволяет конечным точкам проб отвечать, пока публичный сервер и
остальной контейнер еще стартуют.

Во время [плавного выключения](../documentation/container.md#graceful-shutdown) публичный сервер переводит свою готовность в состояние ошибки в самом начале освобождения — *до* того, как выждет
`httpServer.shutdownWait` (по умолчанию: `30s`) на завершение текущих запросов. Балансировщик, опрашивающий готовность, поэтому видит уход экземпляра из ротации раньше, чем тот начнет отклонять
соединения, — а это ровно тот порядок, который нужен при плавающем деплое.

## Семантика ответов { #response-semantics }

Обе конечные точки принимают `GET` и отвечают телом `text/plain;charset=utf-8`:

| Статус | Тело | Значение |
|--------|------|----------|
| `200 OK` | `OK` | все зарегистрированные пробы вернули `null` либо ни одной пробы этого вида не зарегистрировано |
| `503 Service Unavailable` | `message` ошибки | как минимум одна проба сообщила об ошибке |
| `503 Service Unavailable` | `Probe failed: <error>` | проба бросила исключение; брошенное исключение считается ошибкой |
| `503 Service Unavailable` | `Probe is not ready yet` | компонент пробы еще не создан в контейнере |
| `408 Request Timeout` | `Probe failed: timeout` | выполнение проб не уложилось в `30` секунд |
| `500 Internal Server Error` | сообщение об ошибке | конечная точка вообще не смогла запустить пробы |

Две из них стоит запомнить, потому что при первой встрече они выглядят как баги.

`Probe is not ready yet` — это не падение вашей пробы, это ее отсутствие. Пробы внедряются как обещания, а не как готовые компоненты, и именно это позволяет системному серверу отвечать до сборки всего
контейнера. Во время старта конечная точка сообщает об этом, а не молча пропускает пробу.

`408` с телом `Probe failed: timeout` означает, что агрегация вышла за 30 секунд. Поскольку `probe()` объявлен как `throws Exception` и выполняется на виртуальном потоке, блокироваться внутри него
разрешено, и написать пробу, ждущую того, что никогда не придет, легко. Таймаут — это страховка, а не бюджет, который надо потратить.

Для путей проб маршрутизируется только `GET`, поэтому на любой другой метод роутер вернет стандартный `405 Method Not Allowed` с заголовком `Allow`.

## Тестирование проб { #testing-probes }

Проба — обычный компонент, поэтому тест может внедрить ее и вызвать `probe()` напрямую, без HTTP.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraAppTest(Application.class)
    class ObservabilityAppTest {

        @TestComponent
        private ApplicationHealthProbe livenessProbe;
        @TestComponent
        private CustomReadinessProbe readinessProbe;

        @Test
        void probesEventuallyReportHealthyState() throws Exception {
            assertNull(livenessProbe.probe()); //(1)!

            for (int i = 0; i < 10; i++) {
                if (readinessProbe.probe() == null) { //(2)!
                    return;
                }
                Thread.sleep(100L);
            }

            assertNull(readinessProbe.probe());
        }
    }
    ```

    1.  `null` означает, что проба прошла успешно.
    2.  Готовность с периодом прогрева становится здоровой только спустя время, поэтому опрашивайте ее, а не проверяйте один раз.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraAppTest(Application::class)
    class ObservabilityAppTest {

        @TestComponent
        lateinit var livenessProbe: ApplicationHealthProbe
        @TestComponent
        lateinit var readinessProbe: CustomReadinessProbe

        @Test
        fun probesEventuallyReportHealthyState() {
            assertNull(livenessProbe.probe()) //(1)!

            repeat(10) {
                if (readinessProbe.probe() == null) { //(2)!
                    return
                }
                Thread.sleep(100L)
            }

            assertNull(readinessProbe.probe())
        }
    }
    ```

    1.  `null` означает, что проба прошла успешно.
    2.  Готовность с периодом прогрева становится здоровой только спустя время, поэтому опрашивайте ее, а не проверяйте один раз.

В [черноящичном тесте](testing-black-box.md) конечная точка готовности служит сигналом старта контейнера:

===! ":fontawesome-brands-java: `Java`"

    ```java
    withExposedPorts(8080, 8085); //(1)!
    withStartupTimeout(Duration.ofSeconds(30));
    waitingFor(Wait.forHttp("/system/readiness").forPort(8085).forStatusCode(200)); //(2)!
    ```

    1.  Пробросить надо и публичный, и системный порт.
    2.  Готовность опрашивается на системном порту, а не на публичном.

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    withExposedPorts(8080, 8085) //(1)!
    withStartupTimeout(Duration.ofSeconds(30))
    waitingFor(Wait.forHttp("/system/readiness").forPort(8085).forStatusCode(200)) //(2)!
    ```

    1.  Пробросить надо и публичный, и системный порт.
    2.  Готовность опрашивается на системном порту, а не на публичном.

## Проверка приложения { #check-app }

Запустите приложение и вызовите обе конечные точки:

```bash
./gradlew run
```

```bash
curl -i http://localhost:8085/system/liveness
curl -i http://localhost:8085/system/readiness
```

Сразу после старта готовность может еще сообщать о прогреве:

```text
HTTP/1.1 503 Service Unavailable
Content-Type: text/plain;charset=utf-8

Service is warming up
```

Через мгновение тот же запрос проходит успешно:

```bash
sleep 1
curl -i http://localhost:8085/system/readiness
```

```text
HTTP/1.1 200 OK
Content-Type: text/plain;charset=utf-8

OK
```

Заодно убедитесь в разделении — проб нет на публичном порту, а бизнес-API нет на системном:

```bash
curl -i http://localhost:8080/system/readiness  # 404, this port serves the business API
```

## Kubernetes { #kubernetes }

Две конечные точки напрямую ложатся на две пробы Kubernetes. Объявите системный порт на контейнере и направьте каждую пробу на свой путь:

```yaml
ports:
  - name: http
    containerPort: 8080
  - name: system
    containerPort: 8085 #(1)!

livenessProbe:
  httpGet:
    path: /system/liveness
    port: system
  periodSeconds: 10
  failureThreshold: 3 #(2)!

readinessProbe:
  httpGet:
    path: /system/readiness
    port: system
  periodSeconds: 5 #(3)!
```

1.  Системный порт должен быть объявлен на контейнере, чтобы пробы до него достучались.
2.  Несколько подряд идущих провалов до перезапуска, чтобы один медленный ответ не убил здоровый процесс.
3.  Готовность опрашивается чаще жизнеспособности, потому что реакция на нее дешевая.

В `Service` попадает только публичный порт. Системный остается доступным с узла для kubelet и агента мониторинга и не попадает на публичный маршрут.

## Лучшие практики { #best-practices }

- Держите жизнеспособность простой и устойчивой к коротким внешним сбоям; в сомнении возвращайте `null`.
- Используйте готовность для прогрева, слива трафика и временной внутренней недоступности.
- Проверяйте внутреннее состояние, а не внешние зависимости — для них есть [CircuitBreaker](../documentation/resilient.md#circuitbreaker).
- Разносите независимые условия по нескольким небольшим пробам, чтобы получать осмысленное сообщение об ошибке.
- Держите `probe()` дешевым, без побочных эффектов и безопасным для конкурентного вызова.
- В тестах и контейнерах ждите `/system/readiness`, а не строку лога.
- Держите конечные точки проб на системном порту и вне публичного `Service`.

## Итоги { #summary }

Вы вывели жизнеспособность и готовность на системный порт, написали консервативную пробу жизнеспособности и пробу готовности с периодом прогрева, увидели, как Kora агрегирует несколько проб вместе со
своими встроенными, разобрались в значении каждого кода ответа и тела и подключили конечные точки к тесту и манифесту Kubernetes.

## Ключевые понятия { #key-concepts }

Жизнеспособность:
: сигнал о том, что процесс здоров и не нуждается в перезапуске.

Готовность:
: сигнал о том, что этот экземпляр может обслуживать трафик прямо сейчас.

Ошибка пробы:
: запись с единственным `message`, который становится телом ответа `503`.

Системный сервер:
: отдельный порт, обслуживающий пробы и метрики в стороне от бизнес-API.

Агрегация:
: все пробы одного вида выполняются параллельно; одна упавшая роняет конечную точку.

## Устранение неполадок { #troubleshooting }

Конечная точка отвечает `404`:
: Вы на публичном порту. Пробы живут на `httpServer.system.port` (по умолчанию: `8085`).

Конечная точка отвечает `200`, но ваша проба не вызывается:
: Убедитесь, что класс помечен `@Component` и реализует интерфейс из `io.koraframework.common.liveness` или `io.koraframework.common.readiness`.

`Probe is not ready yet`:
: Компонент пробы еще не создан в контейнере. Во время старта это нормально; если сохраняется — компонент не собирается.

`408` с телом `Probe failed: timeout`:
: Проба блокировалась дольше `30` секунд. Уберите ожидание из `probe()` и дайте ей читать заранее вычисленное состояние.

Готовность никогда не становится здоровой:
: Проверьте условие в своей пробе, затем встроенные — публичный HTTP-сервер сообщает «не готов», пока действительно не начнет слушать.

Приложение перезапускается по кругу:
: В жизнеспособности проверяется внешняя зависимость. Перенесите эту проверку в готовность.

Готовность падает при выключении:
: Так и задумано. Публичный сервер переводит готовность в ошибку до того, как выждать `httpServer.shutdownWait`, чтобы трафик успел слиться.

## Что дальше? { #whats-next }

- добавьте бизнес-метрики в [Метриках с Kora](observability-metrics.md)
- добавьте трассировки в [Трассировке с Kora](observability-tracing.md)
- соберите все сигналы в одном приложении в [Наблюдаемости и мониторинге с Kora](observability.md)
- сверьтесь с деталями в [документации по пробам](../documentation/probes.md)

## Помощь { #help }

- изучите готовые приложения по наблюдаемости на Java и Kotlin
- проверьте агрегацию и семантику ответов в [документации по пробам](../documentation/probes.md)
- посмотрите, как контейнер ждет готовности, в [Черноящичном тестировании](testing-black-box.md)
