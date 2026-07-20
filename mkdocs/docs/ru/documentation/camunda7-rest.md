---
description: "Explains Kora Camunda 7 REST API exposure, OpenAPI management, REST configuration, CORS, telemetry, and graceful shutdown settings. Use when working with CamundaRestModule, OpenAPI, HttpServerConfig, CamundaRestConfig, CORS, telemetry."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora Camunda 7 REST API exposure, OpenAPI management, REST configuration, CORS, telemetry, and graceful shutdown settings; key triggers include CamundaRestModule, OpenAPI, HttpServerConfig, CamundaRestConfig, CORS, telemetry."
---

??? warning "Экспериментальный модуль"

    **Экспериментальный** модуль является полностью рабочим и протестированным, но требует дополнительной апробации и аналитики по использованию.
    По этой причине `API` может претерпеть незначительные изменения перед полной готовностью.

Модуль подключает [`Camunda 7 REST API`](https://docs.camunda.org/manual/7.21/reference/rest/overview/) к приложению Kora и публикует стандартные ресурсы `CamundaRestResources` через отдельный `Undertow` HTTP-сервер.
Он используется вместе с [модулем `Camunda 7 BPMN`](camunda7-bpmn.md): `BPMN`-движок выполняет процессы, а REST-модуль открывает HTTP-доступ к операциям `Camunda 7`.

Дополнительно модуль может отдавать `OpenAPI`-описание `REST API`, а также страницы `Swagger UI` и `RapiDoc`.
Для запросов к `REST API` доступны отдельные настройки `CORS`, логирования, метрик, трассировки и штатного завершения сервера.

## Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora.experimental:camunda-rest-undertow"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends CamundaRestUndertowModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora.experimental:camunda-rest-undertow")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : CamundaRestUndertowModule
    ```

Требует подключения [модуля `Camunda 7 BPMN`](camunda7-bpmn.md).

## HTTP-сервер { #http-server }

Модуль запускает **отдельный** независимый `Undertow` HTTP-сервер, выделенный под `Camunda 7 REST API`.
Он слушает собственный `port` (по умолчанию: `8081`) и полностью изолирован от основного модуля [HTTP-сервера](http-server.md):
у него собственный фильтр [CORS](#cors), собственная [телеметрия](#telemetry) и собственное [штатное завершение](container.md#component-lifecycle).
Таким образом, `Camunda REST API` и собственные контроллеры приложения работают на разных портах и не разделяют обработку запросов или конфигурацию.

`ProcessEngine`, обслуживающий эти запросы, предоставляется [модулем `Camunda 7 BPMN`](camunda7-bpmn.md);
данный модуль лишь открывает к нему HTTP-доступ по настроенному `path` (по умолчанию: `/engine-rest`).

При завершении работы сервер перестает принимать новые запросы и ждет до `shutdownWait` (по умолчанию: `30s`)
завершения уже обрабатываемых запросов, прежде чем остановиться.

## Конфигурация { #configuration }

Пример полной конфигурации, описанной в классе `CamundaRestConfig`:

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
            cors {
                enabled = false //(12)!
                allowOrigin = "*" //(13)!
                allowHeaders = [ "*" ] //(14)!
                allowMethods = [ "GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD" ] //(15)!
                allowCredentials = true //(16)!
                exposeHeaders = [ "*" ] //(17)!
                maxAge = "1h" //(18)!
            }
            telemetry {
                logging {
                    enabled = false //(19)!
                    stacktrace = true //(20)!
                    mask = "***" //(21)!
                    maskQueries = [ ] //(22)!
                    maskHeaders = [ "authorization" ] //(23)!
                    pathTemplate = true //(24)!
                }
                metrics {
                    enabled = true //(25)!
                    slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(26)!
                    tags = { // (27)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
                tracing {
                    enabled = true //(28)!
                    attributes = { // (29)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
            }
        }
    }
    ```

    1. Включает `Camunda 7 REST API` (по умолчанию: `false`).
    2. Префикс пути для `Camunda 7 REST API` (по умолчанию: `/engine-rest`).
    3. Порт отдельного `Undertow` HTTP-сервера для `REST API` (по умолчанию: `8081`).
    4. Максимальное время ожидания [штатного завершения](container.md#component-lifecycle) HTTP-сервера (по умолчанию: `30s`).
    5. Путь к `OpenAPI`-файлу в `resources` (по умолчанию: `[ "openapi.json" ]`). По умолчанию используется файл из [зависимости `camunda-engine-rest-openapi`](https://mvnrepository.com/artifact/org.camunda.bpm/camunda-engine-rest-openapi).
    6. Включает контроллер, который отдает `OpenAPI`-файл (по умолчанию: `false`).
    7. Путь, по которому будет доступен `OpenAPI`-файл (по умолчанию: `/openapi`).
    8. Включает контроллер, который отдает `Swagger UI` (по умолчанию: `false`).
    9. Путь, по которому будет доступен `Swagger UI` (по умолчанию: `/swagger-ui`).
    10. Включает контроллер, который отдает `RapiDoc` (по умолчанию: `false`).
    11. Путь, по которому будет доступен `RapiDoc` (по умолчанию: `/rapidoc`).
    12. Включает фильтр `CORS` (по умолчанию: `false`).
    13. Разрешенный источник для `CORS` (по умолчанию не указано, необязательно). Если значение не указано, фильтр использует заголовок `Origin` из запроса, а если его нет, возвращает `*`.
    14. Разрешенные заголовки для `CORS`-запросов (по умолчанию: `[ "*" ]`).
    15. Разрешенные HTTP-методы для `CORS`-запросов (по умолчанию: `[ "GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD" ]`).
    16. Разрешает передачу учетных данных в `CORS`-запросах (по умолчанию: `true`).
    17. Заголовки, которые могут быть доступны клиенту в `CORS`-ответе (по умолчанию: `[ "*" ]`).
    18. Максимальное время кеширования предварительных `CORS`-запросов (по умолчанию: `1h`).
    19. Включает логирование модуля (по умолчанию: `false`).
    20. Включает логирование стека вызовов при исключении (по умолчанию: `true`).
    21. Маска для скрытия указанных заголовков и параметров запроса или ответа (по умолчанию: `***`).
    22. Список параметров запроса, которые нужно скрывать в логах (по умолчанию: `[ ]`).
    23. Список заголовков запроса или ответа, которые нужно скрывать в логах (по умолчанию: `[ "authorization" ]`).
    24. Определяет, использовать ли шаблон пути при логировании (по умолчанию не указано, необязательно). Если не указано, полный путь используется только на уровне логирования `TRACE`; если `true`, используется шаблон пути; если `false`, используется полный путь.
    25. Включает метрики модуля (по умолчанию: `true`).
    26. Настраивает [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрики [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
    27. Дополнительные теги для метрик (по умолчанию: `{}`).
    28. Включает трассировку модуля (по умолчанию: `true`).
    29. Дополнительные атрибуты для трассировки (по умолчанию: `{}`).

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
        cors:
          enabled: false #(12)!
          allowOrigin: "*" #(13)!
          allowHeaders: [ "*" ] #(14)!
          allowMethods: [ "GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD" ] #(15)!
          allowCredentials: true #(16)!
          exposeHeaders: [ "*" ] #(17)!
          maxAge: "1h" #(18)!
        telemetry:
          logging:
            enabled: false #(19)!
            stacktrace: true #(20)!
            mask: "***" #(21)!
            maskQueries: [ ] #(22)!
            maskHeaders: [ "authorization" ] #(23)!
            pathTemplate: true #(24)!
          metrics:
            enabled: true #(25)!
            slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(26)!
            tags: #(27)!
              key1: value1
              key2: value2
          tracing:
            enabled: true #(28)!
            attributes: #(29)!
              key1: value1
              key2: value2
    ```

    1. Включает `Camunda 7 REST API` (по умолчанию: `false`).
    2. Префикс пути для `Camunda 7 REST API` (по умолчанию: `/engine-rest`).
    3. Порт отдельного `Undertow` HTTP-сервера для `REST API` (по умолчанию: `8081`).
    4. Максимальное время ожидания [штатного завершения](container.md#component-lifecycle) HTTP-сервера (по умолчанию: `30s`).
    5. Путь к `OpenAPI`-файлу в `resources` (по умолчанию: `[ "openapi.json" ]`). По умолчанию используется файл из [зависимости `camunda-engine-rest-openapi`](https://mvnrepository.com/artifact/org.camunda.bpm/camunda-engine-rest-openapi).
    6. Включает контроллер, который отдает `OpenAPI`-файл (по умолчанию: `false`).
    7. Путь, по которому будет доступен `OpenAPI`-файл (по умолчанию: `/openapi`).
    8. Включает контроллер, который отдает `Swagger UI` (по умолчанию: `false`).
    9. Путь, по которому будет доступен `Swagger UI` (по умолчанию: `/swagger-ui`).
    10. Включает контроллер, который отдает `RapiDoc` (по умолчанию: `false`).
    11. Путь, по которому будет доступен `RapiDoc` (по умолчанию: `/rapidoc`).
    12. Включает фильтр `CORS` (по умолчанию: `false`).
    13. Разрешенный источник для `CORS` (по умолчанию не указано, необязательно). Если значение не указано, фильтр использует заголовок `Origin` из запроса, а если его нет, возвращает `*`.
    14. Разрешенные заголовки для `CORS`-запросов (по умолчанию: `[ "*" ]`).
    15. Разрешенные HTTP-методы для `CORS`-запросов (по умолчанию: `[ "GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD" ]`).
    16. Разрешает передачу учетных данных в `CORS`-запросах (по умолчанию: `true`).
    17. Заголовки, которые могут быть доступны клиенту в `CORS`-ответе (по умолчанию: `[ "*" ]`).
    18. Максимальное время кеширования предварительных `CORS`-запросов (по умолчанию: `1h`).
    19. Включает логирование модуля (по умолчанию: `false`).
    20. Включает логирование стека вызовов при исключении (по умолчанию: `true`).
    21. Маска для скрытия указанных заголовков и параметров запроса или ответа (по умолчанию: `***`).
    22. Список параметров запроса, которые нужно скрывать в логах (по умолчанию: `[ ]`).
    23. Список заголовков запроса или ответа, которые нужно скрывать в логах (по умолчанию: `[ "authorization" ]`).
    24. Определяет, использовать ли шаблон пути при логировании (по умолчанию не указано, необязательно). Если не указано, полный путь используется только на уровне логирования `TRACE`; если `true`, используется шаблон пути; если `false`, используется полный путь.
    25. Включает метрики модуля (по умолчанию: `true`).
    26. Настраивает [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрики [DistributionSummary](https://github.com/micrometer-metrics/micrometer-docs/blob/main/src/docs/concepts/distribution-summaries.adoc) (по умолчанию: `ru.tinkoff.kora.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
    27. Дополнительные теги для метрик (по умолчанию: `{}`).
    28. Включает трассировку модуля (по умолчанию: `true`).
    29. Дополнительные атрибуты для трассировки (по умолчанию: `{}`).

В листинге выше показаны все доступные параметры; на практике включают только то, что нужно.
Типовая настройка публикует `REST API` на произвольном `port` вместе с `OpenAPI`-описанием, `Swagger UI` и логированием запросов:

===! ":material-code-json: `Hocon`"

    ```javascript
    camunda {
        rest {
            enabled = true
            port = 8090
            openapi {
                enabled = true
                swaggerui.enabled = true
            }
            telemetry.logging.enabled = true
        }
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    camunda:
      rest:
        enabled: true
        port: 8090
        openapi:
          enabled: true
          swaggerui:
            enabled: true
        telemetry:
          logging:
            enabled: true
    ```

## OpenAPI { #openapi }

Помимо самого `REST API`, отдельный сервер может отдавать `OpenAPI`-описание API вместе со
страницами [Swagger UI](https://swagger.io/tools/swagger-ui/) и [RapiDoc](https://rapidocweb.com/).
Все три по умолчанию отключены и включаются независимо друг от друга через секцию конфигурации `openapi`.

При включении страницы доступны на `port` `REST`-сервера по настроенным путям:

| Страница             | Флаг конфигурации           | Путь по умолчанию |
|----------------------|-----------------------------|-------------------|
| Спецификация OpenAPI | `openapi.enabled`           | `/openapi`        |
| Swagger UI           | `openapi.swaggerui.enabled` | `/swagger-ui`     |
| RapiDoc              | `openapi.rapidoc.enabled`   | `/rapidoc`        |

Например, при `port = 8090` и `openapi.enabled = true` спецификация отдается по адресу `http://localhost:8090/openapi`,
а `Swagger UI` (если включен) — по адресу `http://localhost:8090/swagger-ui`.

По умолчанию модуль отдает `OpenAPI`-спецификацию, поставляемую в составе зависимости
[`camunda-engine-rest-openapi`](https://mvnrepository.com/artifact/org.camunda.bpm/camunda-engine-rest-openapi).
Когда используется эта встроенная спецификация, модуль подставляет в нее настроенные `port` и `path`,
поэтому отдаваемый `OpenAPI` всегда соответствует актуальному адресу `REST API`, даже если заданы значения, отличные от `8081` или `/engine-rest`.

Чтобы вместо этого отдавать собственную спецификацию, укажите в `openapi.file` один или несколько файлов в `resources`:

===! ":material-code-json: `Hocon`"

    ```javascript
    camunda.rest.openapi {
        enabled = true
        file = [ "my-openapi.json" ]
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    camunda:
      rest:
        openapi:
          enabled: true
          file: [ "my-openapi.json" ]
    ```

## CORS { #cors }

У `REST`-сервера есть собственный фильтр [CORS](https://developer.mozilla.org/ru/docs/Web/HTTP/CORS), отключенный по умолчанию и включаемый через `cors.enabled`.
Если `cors.allowOrigin` не задан, фильтр возвращает в ответе заголовок `Origin` из запроса,
а при отсутствии заголовка `Origin` в запросе использует `*`.
Остальные параметры `cors.*` управляют разрешенными заголовками и методами, разрешена ли передача учетных данных,
заголовками, доступными клиенту, и временем кеширования предварительных запросов.

## Телеметрия { #telemetry }

Запросы, обрабатываемые `REST`-сервером, охвачены стандартными сигналами телеметрии Kora — [логированием](logging-slf4j.md),
[метриками](metrics.md) и [трассировкой](tracing.md) — которые настраиваются в секции `telemetry`.
Логирование по умолчанию отключено (`telemetry.logging.enabled`), а метрики и трассировка по умолчанию включены.

Параметр `telemetry.logging.pathTemplate` управляет тем, как путь запроса отображается в логах: если он не задан,
используется шаблон пути, кроме уровня `TRACE`, где логируется полный путь;
`true` всегда использует шаблон пути, а `false` всегда использует полный путь.

Метрики модуля описаны в разделе [Справочник метрик](metrics.md#camunda-rest).

Стандартную телеметрию можно переопределить, зарегистрировав собственный компонент `CamundaRestLoggerFactory`, `CamundaRestMetricsFactory`
или `CamundaRestTracerFactory`, который заменяет соответствующий стандартный компонент, предоставленный через `@DefaultComponent`.

## Приложения { #applications }

Модуль уже регистрирует стандартный `@Tag(CamundaRest.class)` `jakarta.ws.rs.core.Application`, который публикует стандартные
ресурсы `Camunda 7 REST API` (`CamundaRestResources`) вместе с `ResteasyJackson2Provider` для сериализации в `JSON`.

Чтобы добавить собственные ресурсы `JAX-RS`, зарегистрируйте свой компонент `jakarta.ws.rs.core.Application`, помеченный тегом `@Tag(CamundaRest.class)`.
Все такие приложения собираются и объединяются со стандартным — их `getClasses()` и `getSingletons()` комбинируются —
поэтому пользовательские ресурсы отдаются на том же `REST`-сервере вместе со стандартными endpoint'ами Camunda.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(CamundaRest.class)
    @Component
    public final class CustomCamundaApplication extends Application {

        @Override
        public Set<Class<?>> getClasses() {
            return Set.of(CustomResource.class);
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(CamundaRest::class)
    @Component
    class CustomCamundaApplication : Application() {

        override fun getClasses(): Set<Class<*>> {
            return setOf(CustomResource::class.java)
        }
    }
    ```
