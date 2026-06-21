---
description: "Explains Kora readiness and liveness probes, probe configuration, dependency health checks, and Kubernetes-style availability reporting. Use when working with ReadinessProbe, LivenessProbe, ProbeFailure, ProbesModule, CircuitBreaker."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora readiness and liveness probes, probe configuration, dependency health checks, and Kubernetes-style availability reporting; key triggers include ReadinessProbe, LivenessProbe, ProbeFailure, ProbesModule, CircuitBreaker."
---

Пробы позволяют проверять `жизнеспособность` и `готовность` приложения через служебный HTTP-порт.
Их обычно используют оркестраторы и балансировщики нагрузки, чтобы понять, можно ли отправлять приложению запросы и нужно ли перезапускать его экземпляр.
Разделение на две пробы помогает отличать временную неготовность приложения к приему трафика от состояния, когда процесс действительно считается неисправным.

Пробами управляет [служебный HTTP-сервер](http-server.md). По умолчанию он работает на порту `8085`.

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

Для создания собственной пробы `жизнеспособности` требуется, чтобы компонент реализовывал интерфейс:

```java
public interface LivenessProbe {

    @Nullable
    LivenessProbeFailure probe();
}
```

В случае ошибки проба должна возвращать `LivenessProbeFailure`, а в случае успеха `null`.

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

Для создания собственной пробы `готовности` требуется, чтобы компонент реализовывал интерфейс:

```java
public interface ReadinessProbe {

    @Nullable
    ReadinessProbeFailure probe();
}
```

В случае ошибки проба должна возвращать `ReadinessProbeFailure`, а в случае успеха `null`.

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

## Ответ { #response }

Служебный HTTP-сервер возвращает:

- `200 OK` — если все пробы вернули `null`.
- `503 Service Unavailable` — если проба вернула `LivenessProbeFailure` или `ReadinessProbeFailure`.
- `503 Service Unavailable` — если компонент пробы еще не готов.
- `408 Request Timeout` — если выполнение проб не завершилось за `30` секунд.

## Совет { #recommendations }

???+ warning "Совет"

    **Не рекомендуется делать пробы, которые напрямую проверяют внешние зависимости: базы данных, очереди или другие сервисы.**

    Временная недоступность внешней зависимости не должна автоматически приводить к перезапуску приложения. Для таких случаев лучше использовать шаблон [Прерыватель](resilient.md#circuitbreaker).

Хорошим примером для `ReadinessProbe` может служить проба, которая возвращает ошибку во время прогрева сервиса.
