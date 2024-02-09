Модуль для сбора метрик приложения с использованием [Micrometer](https://micrometer.io/docs/concepts#_purpose).

Требует подключения [HTTP сервера](http-server.md) для предоставления метрик в формате [prometheus](https://prometheus.io/docs/concepts/data_model/).

## Подключение

=== ":fontawesome-brands-java: `Java`"

    Зависимость `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:micrometer-module"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends MetricsModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Зависимость `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:micrometer-module")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : MetricsModule
    ```

## Конфигурация

По умолчанию метод для получения метрик в формате `prometheus` доступен по пути `/metrics`, но путь можно настроить через конфигурацию:

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
        privateApiHttpMetricsPath = "/metrics"
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      privateApiHttpMetricsPath: "/metrics"
    ```

Параметры конфигурации сбора метрик описываются в модулях в которых присутствует сбор метрик, например [HTTP сервер](http-server.md), [HTTP клиент](http-client.md) и т.д.

## Использование

Мы следуем и вам рекомендуем использовать нотацию, описанную в [спецификации](https://prometheus.io/docs/concepts/data_model/).

После подключения модуля `Metrics.globalRegistry` будет зарегистрирован `PrometheusMeterRegistry`, который будет использоваться во всех компонентах, собирающих метрики.

## Персонализация

Для внесения изменений в конфигурацию `PrometheusMeterRegistry` нужно добавить в контейнер `PrometheusMeterRegistryInitializer`.

**Важно**, `PrometheusMeterRegistryInitializer` применяется только один раз при инициализации приложения.

Например, мы хотим добавить общий тег для всех метрик:

=== ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface MetricsConfigModule {
        default PrometheusMeterRegistryInitializer commonTagsInit() {
            return registry -> {
                registry.config().commonTags("tag", "value");
                return registry;
            };
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface MetricsConfigModule {
        fun commonTagsInit(): PrometheusMeterRegistryInitializer? {
            return PrometheusMeterRegistryInitializer {
                it.config().commonTags("tag", "value")
                it
            }
        }
    }
    ```

Так же стандартные метрики имеют некоторые конфигурации, такие как `ServiceLayerObjectives` для Distribution summary метрик.
Имена полей конфигурации можно посмотреть в `ru.tinkoff.kora.micrometer.module.MetricsConfig`.
