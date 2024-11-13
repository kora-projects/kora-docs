??? warning "Экспериментальный модуль"

    **Эксперементальный** модуль является полностью рабочим и протестированным, но не гарантирует полностью стабилизированный API и может
    притерпеть какие либо незначительные изменения перед полной готовностью.

Модуль для подключения [REST API](https://docs.camunda.org/manual/7.21/reference/rest/overview/) для [Camunda 7 BPMN модуля](camunda7-bpmn.md)

## Подключение

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#_4) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora.experimental:camunda-rest-undertow"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends CamundaRestUndertowModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#_4) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora.experimental:camunda-rest-undertow")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : CamundaRestUndertowModule
    ```

Требует подключения [Camunda BPMN модуля](camunda7-bpmn.md).

## Конфигурация

Пример полной конфигурации, описанной в классе `CamundaRestConfig` (указаны примеры значений или значения по умолчанию):

===! ":material-code-json: `Hocon`"

    ```javascript
    camunda {
        rest {
            enabled = false //(1)!
            path = "/engine-rest" //(2)!
            port = 8081 //(3)!
            shutdownWait = "30s" //(4)!
            openapi {
                file = [ "openapi.json" ] //(5)!
                enabled = false  //(6)!
                endpoint = "/openapi" //(7)!
                swaggerui {
                    enabled = false //(8)!
                    endpoint = "/swagger-ui" //(9)!
                }
                rapidoc {
                    enabled = false //(10)!
                    endpoint = "/rapidoc" //(11)!
                }
            }
            telemetry {
                logging {
                    enabled = false //(12)!
                    stacktrace = true //(13)!
                    mask = "***" //(14)!
                    maskQueries = [ ] //(15)!
                    maskHeaders = [ "authorization" ] //(16)!
                    pathTemplate = true //(17)!
                }
                metrics {
                    enabled = true //(18)!
                    slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(19)!
                }
                tracing {
                    enabled = true //(20)!
                }
            }
        }
    }
    ```

    1.  Включить/выключить REST API
    2.  Путь префикс до REST API
    3.  Порт на котором будет запускаться REST API сервер
    4.  Максимальное время ожидания [штатного завершения](container.md#_24)
    5.  Относительный путь до OpenAPI файлов в `resources` директории, по умолчанию указан файл `openapi.json` OpenAPI из [зависимости Camunda](https://mvnrepository.com/artifact/org.camunda.bpm/camunda-engine-rest-openapi)
    6.  Вкл/Выкл контроллера который отдает OpenAPI 
    7.  Путь по которому будет доступен OpenAPI
        5. Если указан один OpenAPI файл, является целиком путем по которому доступен файл
        6. Если указаны несколько OpenAPI файлов, является префиксом к пути перед именем файла `/openapi/{fileName}`, берется указанный путь и к нему добавляется имя файла без диреторий и его расширения, в случае файла `someDirectory/my-openapi-1.yaml` путь к файлу будет `/openapi/my-openapi-1`
    8.  Вкл/Выкл контроллера который отдает SwaggerUI
    9.  Путь по которому будет доступен SwaggerUI
    10.  Вкл/Выкл контроллера который отдает Rapidoc
    11.  Путь по которому будет доступен Rapidoc
    12. Включает логгирование модуля (по умолчанию `false`)
    13. Включает логгирование стэка вызовов в случае исключения
    14. Маска которая используется для скрытия указанных заголовков и параметров запроса/ответа
    15. Список параметров запроса которые следует скрывать
    16. Список заголовков запроса/ответа которые следует скрывать
    17. Использовать ли всегда шаблон пути запроса при логгировании. По умолчанию используется всегда шаблон пути, за исключением уровня логирования `TRACE` где использует полный путь.
    18.  Включает метрики модуля (по умолчанию `true`)
    19.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    20.  Включает трассировку модуля (по умолчанию `true`)

=== ":simple-yaml: `YAML`"

    ```yaml
    camunda:
      rest:
        enabled: false #(1)!
        path: "/engine-rest" #(2)!
        port: 8081 #(3)!
        shutdownWait: "30s" #(4)!
        openapi:
          file: [ "openapi.json" ] #(5)!
          enabled: false  #(6)!
          endpoint: "/openapi" #(7)!
          swaggerui:
            enabled: false #(8)!
            endpoint: "/swagger-ui" #(9)!
          rapidoc:
            enabled: false #(10)!
            endpoint: "/rapidoc" #(11)!
        telemetry:
          logging:
            enabled: false #(12)!
            stacktrace: true #(13)!
            mask: "***" #(14)!
            maskQueries: [ ] #(15)!
            maskHeaders: [ "authorization" ] #(16)!
            pathTemplate: true #(17)!
          metrics:
            enabled: true #(18)!
            slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(19)!
          tracing:
            enabled: true #(20)!
    ```

    1.  Включить/выключить REST API
    2.  Путь префикс до REST API
    3.  Порт на котором будет запускаться REST API сервер
    4.  Максимальное время ожидания [штатного завершения](container.md#_24)
    5.  Относительный путь до OpenAPI файлов в `resources` директории, по умолчанию указан файл `openapi.json` OpenAPI из [зависимости Camunda](https://mvnrepository.com/artifact/org.camunda.bpm/camunda-engine-rest-openapi)
    6.  Вкл/Выкл контроллера который отдает OpenAPI 
    7.  Путь по которому будет доступен OpenAPI
        5. Если указан один OpenAPI файл, является целиком путем по которому доступен файл
        6. Если указаны несколько OpenAPI файлов, является префиксом к пути перед именем файла `/openapi/{fileName}`, берется указанный путь и к нему добавляется имя файла без диреторий и его расширения, в случае файла `someDirectory/my-openapi-1.yaml` путь к файлу будет `/openapi/my-openapi-1`
    8.  Вкл/Выкл контроллера который отдает SwaggerUI
    9.  Путь по которому будет доступен SwaggerUI
    10.  Вкл/Выкл контроллера который отдает Rapidoc
    11.  Путь по которому будет доступен Rapidoc
    12. Включает логгирование модуля (по умолчанию `false`)
    13. Включает логгирование стэка вызовов в случае исключения
    14. Маска которая используется для скрытия указанных заголовков и параметров запроса/ответа
    15. Список параметров запроса которые следует скрывать
    16. Список заголовков запроса/ответа которые следует скрывать
    17. Использовать ли всегда шаблон пути запроса при логгировании. По умолчанию используется всегда шаблон пути, за исключением уровня логирования `TRACE` где использует полный путь.
    18.  Включает метрики модуля (по умолчанию `true`)
    19.  Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) метрики
    20.  Включает трассировку модуля (по умолчанию `true`)

## Приложения

Можно регистрировать произвольные `jakarta.ws.rs.core.Application` с ресурсами для API (например для других [webapp](https://docs.camunda.org/manual/7.21/webapps/)) предоставляя их как компоненты в контейнер зависимостей.
