Модуль для сбора метрик приложения с использованием [Micrometer](https://micrometer.io/docs/concepts#_purpose).

Требует подключения [служебного HTTP сервера](http-server.md) для предоставления метрик в формате [prometheus](https://prometheus.io/docs/concepts/data_model/).

## Подключение

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#_4) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:micrometer-module"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends MetricsModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#_4) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:micrometer-module")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : MetricsModule
    ```

## Конфигурация

Пример конфигурации пути HTTP сервера для получения метрик, описанной в классе `HttpServerConfig` (указаны значения по умолчанию):

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
        privateApiHttpMetricsPath = "/metrics" //(1)!
    }
    ```

    1. Путь для получения метрик в формате `prometheus` (если подключен модуль [HTTP сервера](http-server.md)):

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      privateApiHttpMetricsPath: "/metrics" #(1)!
    ```

    1. Путь для получения метрик в формате `prometheus` (если подключен модуль [HTTP сервера](http-server.md)):

Пример полной конфигурации, описанной в классе `MetricsConfig` (указаны значения по умолчанию):

===! ":material-code-json: `Hocon`"

    ```javascript
    metrics {
        opentelemetrySpec = "V120" //(1)!
    }
    ```

    1. Формат метрик по стандарту OpenTelemetry (доступные значения: [V120](https://opentelemetry.io/docs/specs/semconv/http/migration-guide/#migrating-from-a-version-prior-to-v1200) / [V123](https://opentelemetry.io/docs/specs/semconv/http/migration-guide/))

=== ":simple-yaml: `YAML`"

    ```yaml
    metrics:
      opentelemetrySpec: "V120" #(1)!
    ```

    1. Формат метрик по стандарту OpenTelemetry (доступные значения: [V120](https://opentelemetry.io/docs/specs/semconv/http/migration-guide/#migrating-from-a-version-prior-to-v1200) / [V123](https://opentelemetry.io/docs/specs/semconv/http/migration-guide/))

Параметры конфигурации сбора метрик описываются в модулях в которых присутствует сбор метрик, например [HTTP сервер](http-server.md), [HTTP клиент](http-client.md) и т.д.

## Использование

Мы следуем и вам советуем использовать нотацию, описанную в [спецификации](https://prometheus.io/docs/concepts/data_model/).

После подключения модуля `Metrics.globalRegistry` будет зарегистрирован `PrometheusMeterRegistry`, который будет использоваться во всех компонентах, собирающих метрики.

## Персонализация

Для внесения изменений в конфигурацию `PrometheusMeterRegistry` нужно добавить в контейнер `PrometheusMeterRegistryInitializer`.

**Важно**, `PrometheusMeterRegistryInitializer` применяется только один раз при инициализации приложения.

Например, мы хотим добавить общий тег для всех метрик:

===! ":fontawesome-brands-java: `Java`"

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
        fun commonTagsInit(): PrometheusMeterRegistryInitializer {
            return PrometheusMeterRegistryInitializer {
                it.config().commonTags("tag", "value")
                it
            }
        }
    }
    ```

Так же стандартные метрики имеют некоторые конфигурации, такие как `ServiceLayerObjectives` для Distribution summary метрик.
Имена полей конфигурации можно посмотреть в `ru.tinkoff.kora.micrometer.module.MetricsConfig`.

## Стандарты

Изначальный формат метрик использовал стандарт OpenTelemetry `V120`, после Kora `1.1.0` появилась возможность предоставления метрик
в стандарте OpenTelemetry `V123`, частичный список изменений можно посмотреть [в документации OpenTelemetry](https://opentelemetry.io/blog/2023/http-conventions-declared-stable/)
и [рекомендациях миграции OpenTelemetry](https://opentelemetry.io/docs/specs/semconv/http/migration-guide/)
