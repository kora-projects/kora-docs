Модуль для подключения [REST API](https://docs.camunda.org/manual/7.21/reference/rest/overview/) для [Camunda Engine модуля](camunda-engine.md)

## Подключение

===! ":fontawesome-brands-java: `Java`"

    Зависимость `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:camunda-rest-undertow"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends CamundaRestUndertowModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    Зависимость `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:camunda-rest-undertow")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : CamundaRestUndertowModule
    ```

Требует подключения [Camunda Engine модуля](camunda-engine.md).

## Конфигурация

Пример полной конфигурации, описанной в классе `CamundaRestConfig` (указаны примеры значений или значения по умолчанию):

===! ":material-code-json: `Hocon`"

    ```javascript
    camunda {
        rest {
            enabled = false //(1)!
            path = "/engine-rest" //(2)!
            port = 8081 //(3)!
            shutdownWait = "100ms" //(4)!
            telemetry {
                logging {
                    enabled = false //(5)!
                    stacktrace = true //(6)!
                }
                metrics {
                    enabled = true //(7)!
                    slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(8)!
                }
                tracing {
                    enabled = true //(9)!
                }
            }
        }
    }
    ```

    1.  Включить/выключить REST API
    2.  Путь префикс до REST API
    3.  Порт на котором будет запускаться REST API сервер
    4.  Максимальное время ожидания завершения сервера после получения сигнала плавого завершения
    5.  Включает логгирование модуля (по умолчанию `false`)
    6.  Включает логгирование стека ошибки (по умолчанию `true`)
    7.  Включает метрики модуля (по умолчанию `true`)
    8.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    9.  Включает трассировку модуля (по умолчанию `true`)

=== ":simple-yaml: `YAML`"

    ```yaml
    camunda:
      rest:
        enabled = false #(1)!
        path = "/engine-rest" #(2)!
        port = 8081 #(3)!
        shutdownWait = "100ms" #(4)!
        telemetry:
          logging:
            enabled = false #(5)!
            stacktrace = true #(6)!
          metrics:
            enabled = true #(7)!
            slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(8)!
          tracing:
            enabled = true #(9)!
    ```

    1.  Включить/выключить REST API
    2.  Путь префикс до REST API
    3.  Порт на котором будет запускаться REST API сервер
    4.  Максимальное время ожидания завершения сервера после получения сигнала плавого завершения
    5.  Включает логгирование модуля (по умолчанию `false`)
    6.  Включает логгирование стека ошибки (по умолчанию `true`)
    7.  Включает метрики модуля (по умолчанию `true`)
    8.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    9.  Включает трассировку модуля (по умолчанию `true`)

## Приложения

Можно регистрировать произвольные `jakarta.ws.rs.core.Application` с ресурсами для API (например для других [webapp](https://docs.camunda.org/manual/7.21/webapps/)) предоставляя их как компоненты в контейнер зависимостей.
