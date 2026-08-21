---
description: "Explains Kora readiness and liveness probes, probe configuration, dependency health checks, and Kubernetes-style availability reporting. Use when working with ReadinessProbe, LivenessProbe, LivenessProbeFailure, ReadinessProbeFailure, CircuitBreaker."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora readiness and liveness probes, probe configuration, dependency health checks, and Kubernetes-style availability reporting; key triggers include ReadinessProbe, LivenessProbe, LivenessProbeFailure, ReadinessProbeFailure, CircuitBreaker."
---

Пробы позволяют проверять `жизнеспособность` (liveness) и `готовность` (readiness) приложения через служебный HTTP-порт.
Их обычно используют оркестраторы и балансировщики нагрузки, чтобы понять, можно ли отправлять приложению запросы и нужно ли перезапускать его экземпляр.
Наличие двух отдельных проб помогает отличать временную неспособность принимать трафик от состояния, когда сам процесс следует считать неисправным.

Пробами управляет [служебный HTTP-сервер](http-server.md). По умолчанию он работает на порту `8085`.
Интерфейсы `LivenessProbe` и `ReadinessProbe` находятся в базовом модуле `ru.tinkoff.kora:common` (транзитивная зависимость любого приложения Kora),
а конечные точки, которые их предоставляют, поставляются модулем [HTTP-сервера](http-server.md), поэтому для добавления пробы не требуется никакой дополнительной зависимости.

Обе конечные точки проб всегда присутствуют на служебном сервере, даже если приложение не регистрирует ни одной собственной пробы соответствующего вида — в этом случае конечная точка просто сообщает об успехе.

Если нужен пошаговый разбор перед справочным описанием, смотрите [Наблюдаемость](../guides/observability.md).

## Жизнеспособность { #liveness }

Эта проба показывает, что приложение живо и его не нужно перезапускать. Kora старается начать отдавать эту пробу как можно раньше, чтобы оркестратор не перезапускал приложение во время штатного запуска.

Пример конфигурации пути служебного HTTP-сервера, описанной в классе `HttpServerConfig` (указано значение по умолчанию):

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
        privateApiHttpLivenessPath = "/system/liveness" //(1)!
    }
    ```

    1. Путь пробы `жизнеспособности` на служебном HTTP-сервере (по умолчанию: `/system/liveness`).

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      privateApiHttpLivenessPath: "/system/liveness" #(1)!
    ```

    1. Путь пробы `жизнеспособности` на служебном HTTP-сервере (по умолчанию: `/system/liveness`).

Чтобы создать собственную пробу `жизнеспособности`, зарегистрируйте [компонент](container.md), реализующий интерфейс `LivenessProbe`:

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
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.liveness.LivenessProbe;
    import ru.tinkoff.kora.common.liveness.LivenessProbeFailure;

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
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.liveness.LivenessProbe
    import ru.tinkoff.kora.common.liveness.LivenessProbeFailure

    @Component
    class ApplicationHealthProbe : LivenessProbe {
        override fun probe(): LivenessProbeFailure? = null
    }
    ```

## Готовность { #readiness }

Эта проба показывает, что приложение готово принимать рабочую нагрузку.

Пример конфигурации пути служебного HTTP-сервера, описанной в классе `HttpServerConfig` (указано значение по умолчанию):

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
        privateApiHttpReadinessPath = "/system/readiness" //(1)!
    }
    ```

    1. Путь пробы `готовности` на служебном HTTP-сервере (по умолчанию: `/system/readiness`).

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      privateApiHttpReadinessPath: "/system/readiness" #(1)!
    ```

    1. Путь пробы `готовности` на служебном HTTP-сервере (по умолчанию: `/system/readiness`).

Чтобы создать собственную пробу `готовности`, зарегистрируйте [компонент](container.md), реализующий интерфейс `ReadinessProbe`:

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
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.readiness.ReadinessProbe;
    import ru.tinkoff.kora.common.readiness.ReadinessProbeFailure;

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
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.readiness.ReadinessProbe
    import ru.tinkoff.kora.common.readiness.ReadinessProbeFailure
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

Kora автоматически собирает **каждый** зарегистрированный [компонент](container.md), реализующий `LivenessProbe` (или `ReadinessProbe`) —
связывать их между собой вручную не нужно. Каждая конечная точка выполняет все пробы своего вида и агрегирует результат:

- Конечная точка возвращает `200 OK` только тогда, когда успешны **все** пробы этого вида.
- Единственная неуспешная проба заставляет всю конечную точку вернуть `503`, а телом ответа становится сообщение этой неуспешной пробы.
- Если ни одна проба этого вида не зарегистрирована, конечная точка возвращает `200 OK` — служебный сервер всегда предоставляет оба пути.

Это позволяет разбить независимые условия готовности или жизнеспособности на несколько небольших узконаправленных компонентов-проб.

===! ":fontawesome-brands-java: `Java`"

    ```java
    import ru.tinkoff.kora.common.Component;
    import ru.tinkoff.kora.common.readiness.ReadinessProbe;
    import ru.tinkoff.kora.common.readiness.ReadinessProbeFailure;

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
    import ru.tinkoff.kora.common.Component
    import ru.tinkoff.kora.common.readiness.ReadinessProbe
    import ru.tinkoff.kora.common.readiness.ReadinessProbeFailure

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

## Ответ { #response }

Каждая конечная точка пробы обслуживается [служебным HTTP-сервером](http-server.md) и возвращает тело `text/plain` вместе с кодом статуса:

- `200 OK` — тело `OK` — все зарегистрированные пробы вернули `null` либо ни одна проба этого вида не зарегистрирована.
- `503 Service Unavailable` — телом становится `message` возвращённого `LivenessProbeFailure` / `ReadinessProbeFailure` — как минимум одна проба сообщила о сбое.
- `503 Service Unavailable` — тело `Probe failed: <message>` — проба выбросила исключение; выброшенное исключение трактуется как сбой.
- `503 Service Unavailable` — тело `Probe is not ready yet` — компонент пробы ещё не инициализирован в контейнере зависимостей.
- `408 Request Timeout` — тело `Probe failed: timeout` — выполнение пробы не завершилось за `30` секунд.

Конечная точка отвечает, как только становится известен агрегированный результат; поэтому проверки здоровья оркестратора и балансировщика нагрузки могут ориентироваться либо на код статуса, либо на текстовое тело ответа.

## Рекомендации { #recommendations }

???+ warning "Рекомендация"

    **Не рекомендуется делать пробы, которые напрямую проверяют внешние зависимости: базы данных, очереди или другие сервисы.**

    Временная недоступность внешней зависимости не должна автоматически приводить к перезапуску приложения. Для таких случаев используйте шаблон [CircuitBreaker](resilient.md#circuitbreaker).

Проба должна отражать состояние **самого** приложения, а не систем, с которыми оно взаимодействует.
Хорошие примеры — это `ReadinessProbe`, которая возвращает ошибку, пока сервис прогревается,
или та, что проверяет, завершил ли внутренний компонент свою инициализацию.

Каждая проба выполняется на выделенном исполнителе (исполнитель на виртуальных потоках, если он доступен, иначе `ForkJoinPool.commonPool()`),
поэтому тело пробы может блокироваться, не задерживая служебный HTTP-сервер. При этом вся конечная точка по-прежнему ограничена тайм-аутом в `30` секунд,
по истечении которого она отвечает `408`, поэтому держите логику пробы быстрой и избегайте длительной или неограниченной работы.
