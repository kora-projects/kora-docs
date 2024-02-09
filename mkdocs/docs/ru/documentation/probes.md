Функционал дающий приложению два метода для получения проб на приватном порту для предоставления информации о жизнеспособности и готовности сервиса.

Требует подключения [HTTP сервера](http-server.md).

## Жизнеспособности

Эта проба отвечает за признак — является ли приложение живым в данный момент. Kora старается начать отдавать эту пробу как можно раньше, чтобы оркестраторы точно знали, что нет проблем при старте и не пытались сделать рестарт приложения.

По умолчанию она доступна по пути `/system/liveness`, но её можно настроить через конфигурацию:

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
        privateApiHttpLivenessPath = "/system/liveness"
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      privateApiHttpLivenessPath: "/system/liveness"
    ```

Для создания собственной пробы жизнеспособности требуется чтобы компонент реализовывал интерфейс:
```java
public interface LivenessProbe {

    @Nullable
    LivenessProbeFailure probe();
}
```

В случае ошибки проба должна возвращать `LivenessProbeFailure`, а в случае успеха `null`.

## Готовности

Эта проба отвечает за признак — является ли приложение готовым к работе в данный момент. 

По умолчанию она доступна по пути `/system/readiness`, но её можно настроить через конфигурацию.

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
        privateApiHttpReadinessPath = "/system/readiness"
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      privateApiHttpReadinessPath: "/system/readiness"
    ```

Для создания собственной пробы жизнеспособности требуется чтобы компонент реализовывал интерфейс:
```java
public interface ReadinessProbe {

    @Nullable
    ReadinessProbeFailure probe();
}
```

В случае ошибки проба должна возвращать `ReadinessProbeFailure`, а в случае успеха `null`.

## Рекомендации

???+ warning "Совет"

    **Мы крайне не рекомендуем делать пробы, проверяющие внешние зависимости, такие как базы данных или другие сервисы.**

    В случае недоступности внешних зависимостей рекомендуется использовать паттерн [Прерыватель](resilient.md#_2). 

Хорошим примером для `ReadinessProbe` может служить проба, которая возвращает ошибку во время прогрева сервиса.
