---
description: "Explains Kora readiness and liveness probes on the system HTTP server, probe paths in the httpServer.system config section, built-in framework probes, aggregation and response semantics, and Kubernetes-style availability reporting. Use when working with ReadinessProbe, LivenessProbe, ReadinessProbeFailure, LivenessProbeFailure, /system/readiness, /system/liveness."
agent:
  use_when: "Use this file for Kora docs or implementation questions about readiness and liveness probes, the system HTTP server endpoints /system/readiness and /system/liveness, probe path configuration under httpServer.system, built-in framework readiness probes, and waiting on readiness during startup; key triggers include ReadinessProbe, LivenessProbe, ReadinessProbeFailure, LivenessProbeFailure, readinessPath, livenessPath, Probe is not ready yet."
---

Пробы позволяют проверять `жизнеспособность` (liveness) и `готовность` (readiness) приложения через системный HTTP-порт.
Их обычно используют оркестраторы и балансировщики нагрузки, чтобы понять, можно ли отправлять приложению запросы и нужно ли перезапускать его экземпляр.
Наличие двух отдельных проб помогает отличать временную неспособность принимать трафик от состояния, когда сам процесс следует считать неисправным.

Пробами занимается [системный HTTP-сервер](http-server.md#system-server), который по умолчанию слушает порт `8085` — отдельно от публичного сервера на порту `8080`.
Тот же системный сервер отдаёт [метрики](metrics.md), поэтому оркестратору достаточно доступа всего к одному дополнительному порту.

Обе конечные точки проб всегда присутствуют на системном сервере, даже если приложение не регистрирует ни одной собственной пробы соответствующего вида — в этом случае конечная точка просто сообщает об успехе.

Если нужен пошаговый разбор перед справочным описанием, смотрите [Пробы с Kora](../guides/observability-probes.md) и [Наблюдаемость](../guides/observability.md).

## Подключение { #dependency }

Интерфейсы `LivenessProbe` и `ReadinessProbe` находятся в артефакте `io.koraframework:common`,
который приходит транзитивно вместе с модулем [HTTP-сервера](http-server.md), поэтому для добавления пробы не нужна никакая дополнительная зависимость.

Конечные точки, которые их отдают, предоставляет `UndertowSystemHttpServerModule`.
`UndertowPublicHttpServerModule` наследует этот модуль, поэтому приложение с публичными контроллерами получает обе пробы автоматически:

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:http-server-undertow"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends UndertowPublicHttpServerModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:http-server-undertow")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : UndertowPublicHttpServerModule
    ```

Приложению, которому нужны только системные конечные точки — воркеру или консьюмеру без публичного API — достаточно подключить `UndertowSystemHttpServerModule`, обе пробы при этом останутся на месте.

## Жизнеспособность { #liveness }

Эта проба показывает, что приложение живо и его не нужно перезапускать.

Пример конфигурации пути системного HTTP-сервера, описанной в классе `SystemHttpServerConfig` (указано значение по умолчанию):

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer.system {
        livenessPath = "/system/liveness" //(1)!
    }
    ```

    1. Путь пробы `жизнеспособности` на системном HTTP-сервере (по умолчанию: `/system/liveness`).

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      system:
        livenessPath: "/system/liveness" #(1)!
    ```

    1. Путь пробы `жизнеспособности` на системном HTTP-сервере (по умолчанию: `/system/liveness`).

Чтобы создать собственную пробу `жизнеспособности`, зарегистрируйте [компонент](container.md#components), реализующий интерфейс `LivenessProbe`:

```java
public interface LivenessProbe {

    @Nullable
    LivenessProbeFailure probe() throws Exception;
}
```

В случае успеха проба должна возвращать `null`, а при ошибке — `LivenessProbeFailure` с описанием проблемы.
`LivenessProbeFailure` — это запись, единственное поле `message` которой становится телом ответа `503`:

```java
public record LivenessProbeFailure(String message) {}
```

Метод `probe()` объявлен с `throws Exception`, поэтому реализация может напрямую вызывать API, бросающие проверяемые исключения.
Выброшенное исключение трактуется как сбой — точные коды статуса и тела ответа смотрите в разделе [Ответ](#response).

===! ":fontawesome-brands-java: `Java`"

    ```java
    import io.koraframework.common.annotation.Component;
    import io.koraframework.common.liveness.LivenessProbe;
    import io.koraframework.common.liveness.LivenessProbeFailure;

    @Component
    public final class ApplicationHealthProbe implements LivenessProbe {

        @Override
        public LivenessProbeFailure probe() {
            return null;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import io.koraframework.common.annotation.Component
    import io.koraframework.common.liveness.LivenessProbe
    import io.koraframework.common.liveness.LivenessProbeFailure

    @Component
    class ApplicationHealthProbe : LivenessProbe {
        override fun probe(): LivenessProbeFailure? = null
    }
    ```

Возвращаемое значение размечено в `Java` аннотацией [JSpecify](https://jspecify.dev/) `@Nullable`, поэтому реализация на `Kotlin` обязана объявлять результат как `LivenessProbeFailure?`.

## Готовность { #readiness }

Эта проба показывает, что приложение готово принимать рабочую нагрузку.

Пример конфигурации пути системного HTTP-сервера, описанной в классе `SystemHttpServerConfig` (указано значение по умолчанию):

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer.system {
        readinessPath = "/system/readiness" //(1)!
    }
    ```

    1. Путь пробы `готовности` на системном HTTP-сервере (по умолчанию: `/system/readiness`).

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      system:
        readinessPath: "/system/readiness" #(1)!
    ```

    1. Путь пробы `готовности` на системном HTTP-сервере (по умолчанию: `/system/readiness`).

Чтобы создать собственную пробу `готовности`, зарегистрируйте [компонент](container.md#components), реализующий интерфейс `ReadinessProbe`:

```java
public interface ReadinessProbe {

    @Nullable
    ReadinessProbeFailure probe() throws Exception;
}
```

В случае успеха проба должна возвращать `null`, а при ошибке — `ReadinessProbeFailure` с описанием проблемы.
`ReadinessProbeFailure` — это запись, единственное поле `message` которой становится телом ответа `503`:

```java
public record ReadinessProbeFailure(String message) {}
```

Как и в случае с `LivenessProbe`, метод `probe()` объявлен с `throws Exception`, и выброшенное исключение трактуется как сбой.

===! ":fontawesome-brands-java: `Java`"

    ```java
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
                return new ReadinessProbeFailure("Service is warming up");
            }
            return null;
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
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
                ReadinessProbeFailure("Service is warming up")
            } else {
                null
            }
        }
    }
    ```

## Несколько проб { #multiple-probes }

Kora автоматически собирает **каждый** зарегистрированный [компонент](container.md#components), реализующий `LivenessProbe` (или `ReadinessProbe`) —
связывать их между собой вручную не нужно, и проба не обязана быть [корневым компонентом](container.md#root-component).
Каждая конечная точка выполняет все пробы своего вида на отдельных виртуальных потоках и агрегирует результат:

- Конечная точка возвращает `200 OK` только тогда, когда успешны **все** пробы этого вида.
- Единственная неуспешная проба заставляет всю конечную точку вернуть `503`. Если неуспешных проб несколько, телом ответа становится сообщение первой из них в порядке регистрации.
- Если ни одна проба этого вида не зарегистрирована, конечная точка возвращает `200 OK` — системный сервер всегда предоставляет оба пути.

Пробы внедряются в конечную точку не готовыми компонентами, а обещаниями (promise) — именно это позволяет системному серверу отвечать раньше, чем будет построен весь контейнер.
Пока контейнер не создал компонент пробы, конечная точка отвечает `503` с телом `Probe is not ready yet`, а не молча пропускает эту пробу.

Это позволяет разбить независимые условия готовности или жизнеспособности на несколько небольших узконаправленных компонентов-проб.

===! ":fontawesome-brands-java: `Java`"

    ```java
    import io.koraframework.common.annotation.Component;
    import io.koraframework.common.readiness.ReadinessProbe;
    import io.koraframework.common.readiness.ReadinessProbeFailure;

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

    1. Компонентов `ReadinessProbe` может быть сколько угодно; конечная точка завершается неуспехом, если неуспешен хотя бы один из них
    2. Проверяйте состояние **внутреннего** компонента, а не внешней зависимости

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import io.koraframework.common.annotation.Component
    import io.koraframework.common.readiness.ReadinessProbe
    import io.koraframework.common.readiness.ReadinessProbeFailure

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

    1. Компонентов `ReadinessProbe` может быть сколько угодно; конечная точка завершается неуспехом, если неуспешен хотя бы один из них
    2. Проверяйте состояние **внутреннего** компонента, а не внешней зависимости

## Встроенные пробы { #built-in-probes }

Часть компонентов Kora сама реализует `ReadinessProbe`, поэтому они агрегируются вместе с вашими пробами без какой-либо дополнительной настройки:

| Компонент | Модуль | Сообщает `not ready`, когда |
|-----------|--------|-----------------------------|
| `UndertowHttpServer` | `io.koraframework:http-server-undertow` | публичный [HTTP-сервер](http-server.md) ещё не начал слушать порт либо уже начал останавливаться |
| `GrpcServer` | `io.koraframework:grpc-server` | [gRPC-сервер](grpc-server.md) ещё не запущен либо останавливается |
| `JdbcDataSource` | `io.koraframework:database-jdbc` | включён `jdbc.readinessProbe`, и соединение из пула не проходит проверку |
| `JobExecutorReadinessProbe` | `io.koraframework.experimental:camunda-engine-bpmn` | `JobExecutor` [Camunda](camunda7-bpmn.md) не активен |

Благодаря им ответ `200` на `GET /system/readiness` — надёжный признак того, что приложение поднялось.
Именно поэтому ждать стоит эту конечную точку, а не строку в логе: формулировки стартовых сообщений Kora не являются контрактом.

Слушатель самого системного сервера намеренно **не** входит в эту агрегацию: он зарегистрирован под отдельным тегом,
поэтому конечные точки проб продолжают отвечать, пока публичный сервер и остальной контейнер ещё запускаются.

При [плавной остановке](container.md#graceful-shutdown) публичный сервер переводит свою пробу готовности в состояние сбоя в самом начале освобождения,
ещё до того, как выждет `httpServer.shutdownWait` (по умолчанию: `30s`) для запросов в обработке.
Балансировщик, опрашивающий готовность, поэтому успевает вывести экземпляр из ротации до того, как соединения начнут отвергаться.

## Ответ { #response }

Каждая конечная точка пробы обслуживается [системным HTTP-сервером](http-server.md#system-server), принимает `GET` и возвращает тело `text/plain;charset=utf-8` вместе с кодом статуса:

| Статус | Тело | Значение |
|--------|------|----------|
| `200 OK` | `OK` | все зарегистрированные пробы вернули `null` либо ни одна проба этого вида не зарегистрирована |
| `503 Service Unavailable` | `message` возвращённого `LivenessProbeFailure` / `ReadinessProbeFailure` | как минимум одна проба сообщила о сбое |
| `503 Service Unavailable` | `Probe failed: <error>` | проба выбросила исключение; выброшенное исключение трактуется как сбой |
| `503 Service Unavailable` | `Probe is not ready yet` | компонент пробы ещё не создан в [контейнере зависимостей](container.md) |
| `408 Request Timeout` | `Probe failed: timeout` | выполнение пробы не завершилось за `30` секунд |
| `500 Internal Server Error` | сообщение об ошибке | конечная точка вообще не смогла выполнить пробы, например задача пробы не была принята на исполнение |

Конечная точка отвечает, как только становится известен агрегированный результат; поэтому проверки здоровья оркестратора и балансировщика нагрузки могут ориентироваться либо на код статуса, либо на текстовое тело ответа.

Для путей проб маршрутизируется только `GET`, поэтому на любой другой метод роутер вернёт стандартный `405 Method Not Allowed` с заголовком `Allow`.

## Тестирование { #testing }

Проба — это обычный [компонент](junit5.md#component), поэтому внутрипроцессный тест [@KoraAppTest](junit5.md) может внедрить её и вызвать `probe()` напрямую,
не обращаясь к HTTP-конечной точке:

===! ":fontawesome-brands-java: `Java`"

    ```java
    import io.koraframework.test.extension.junit5.KoraAppTest;
    import io.koraframework.test.extension.junit5.TestComponent;
    import org.junit.jupiter.api.Test;

    import static org.junit.jupiter.api.Assertions.assertNull;

    @KoraAppTest(Application.class)
    class ProbeTests {

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

    1. `null` означает, что проба успешна
    2. Готовность с периодом прогрева становится успешной лишь спустя время, поэтому её опрашивают, а не проверяют однократно

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import io.koraframework.test.extension.junit5.KoraAppTest
    import io.koraframework.test.extension.junit5.TestComponent
    import org.junit.jupiter.api.Assertions.assertNull
    import org.junit.jupiter.api.Test

    @KoraAppTest(Application::class)
    class ProbeTests {

        @TestComponent
        lateinit var livenessProbe: ApplicationHealthProbe
        @TestComponent
        lateinit var readinessProbe: CustomReadinessProbe

        @Test
        fun probesEventuallyReportHealthyState() {
            assertNull(livenessProbe.probe()) //(1)!

            for (i in 0 until 10) {
                if (readinessProbe.probe() == null) { //(2)!
                    return
                }
                Thread.sleep(100L)
            }

            assertNull(readinessProbe.probe())
        }
    }
    ```

    1. `null` означает, что проба успешна
    2. Готовность с периодом прогрева становится успешной лишь спустя время, поэтому её опрашивают, а не проверяют однократно

В [чёрном ящике](../guides/testing-black-box.md) конечная точка готовности служит признаком старта контейнера.
Ждите именно её, а не строку в логе — формулировки стартовых сообщений Kora не являются контрактом и меняются между версиями:

===! ":fontawesome-brands-java: `Java`"

    ```java
    import org.testcontainers.containers.GenericContainer;
    import org.testcontainers.containers.wait.strategy.Wait;

    import java.net.URI;
    import java.time.Duration;

    final class AppContainer extends GenericContainer<AppContainer> {

        AppContainer() {
            super("my-application:latest");

            withExposedPorts(8080, 8085); //(1)!
            withStartupTimeout(Duration.ofSeconds(30));
            waitingFor(Wait.forHttp("/system/readiness").forPort(8085).forStatusCode(200)); //(2)!
        }

        URI getURI() {
            return URI.create("http://" + getHost() + ":" + getMappedPort(8080));
        }

        URI getSystemURI() { //(3)!
            return URI.create("http://" + getHost() + ":" + getMappedPort(8085));
        }
    }
    ```

    1. Пробрасывать нужно и публичный, и системный порт
    2. Пробу готовности опрашивают на системном порту, а не на публичном
    3. Удобно для проверок `/system/liveness`, `/system/readiness` и `/metrics` внутри теста

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    import org.testcontainers.containers.GenericContainer
    import org.testcontainers.containers.wait.strategy.Wait
    import java.net.URI
    import java.time.Duration

    class AppContainer : GenericContainer<AppContainer>("my-application:latest") {

        init {
            withExposedPorts(8080, 8085) //(1)!
            withStartupTimeout(Duration.ofSeconds(30))
            waitingFor(Wait.forHttp("/system/readiness").forPort(8085).forStatusCode(200)) //(2)!
        }

        fun getURI(): URI = URI.create("http://$host:${getMappedPort(8080)}")

        fun getSystemURI(): URI = URI.create("http://$host:${getMappedPort(8085)}") //(3)!
    }
    ```

    1. Пробрасывать нужно и публичный, и системный порт
    2. Пробу готовности опрашивают на системном порту, а не на публичном
    3. Удобно для проверок `/system/liveness`, `/system/readiness` и `/metrics` внутри теста

## Рекомендации { #recommendations }

???+ warning "Рекомендация"

    **Не рекомендуется делать пробы, которые напрямую проверяют внешние зависимости: базы данных, очереди или другие сервисы.**

    Временная недоступность внешней зависимости не должна автоматически приводить к перезапуску приложения. Для таких случаев используйте шаблон [CircuitBreaker](resilient.md#circuitbreaker).

Проба должна отражать состояние **самого** приложения, а не систем, с которыми оно взаимодействует.
Хорошие примеры — это `ReadinessProbe`, которая возвращает ошибку, пока сервис прогревается,
или та, что проверяет, завершил ли внутренний компонент свою инициализацию.

Каждая проба выполняется на собственном виртуальном потоке, поэтому тело пробы может блокироваться, не задерживая системный HTTP-сервер.
При этом вся конечная точка по-прежнему ограничена тайм-аутом в `30` секунд, по истечении которого она отвечает `408`, поэтому держите логику пробы быстрой и избегайте длительной или неограниченной работы.

Проба вызывается на каждый запрос к её конечной точке, и несколько запросов могут выполняться одновременно, поэтому реализация должна быть дешёвой, без побочных эффектов и безопасной для параллельного вызова.
Всё дорогое кэшируйте или вычисляйте заранее в самом компоненте, а `probe()` пусть только читает уже известное состояние.
