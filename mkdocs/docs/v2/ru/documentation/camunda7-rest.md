---
description: "Explains how Kora exposes the Camunda 7 REST API over a dedicated Undertow HTTP server, with OpenAPI, Swagger UI and Scalar pages, CORS, telemetry, and graceful shutdown. Use when working with CamundaRestUndertowModule, CamundaRestModule, CamundaRestConfig, CamundaRest, KoraProcessEngineProvider, camunda.rest, CORS, telemetry."
agent:
  use_when: "Use this file for Kora docs or implementation questions about exposing the Camunda 7 REST API from a Kora application over its own Undertow HTTP server, its OpenAPI / Swagger UI / Scalar pages, CORS, telemetry, and graceful shutdown; key triggers include CamundaRestUndertowModule, CamundaRestModule, CamundaRestConfig, CamundaRest, KoraProcessEngineProvider, camunda.rest, camunda.rest.openapi.files, camunda.rest.cors, engine-rest, CamundaRestResources."
---

??? warning "Экспериментальный модуль"

    **Экспериментальный** модуль является полностью рабочим и протестированным, но требует дополнительной апробации и аналитики по использованию.
    Поэтому `API` может получить незначительные изменения до полной готовности.

???+ warning "Camunda 7 устарела"

    `CamundaRestModule` помечен как `@Deprecated`, потому что [Camunda 7 достигла конца жизненного цикла](https://camunda.com/blog/2025/02/camunda-7-enterprise-end-of-life-extension/).
    Модуль по-прежнему работает и поставляется, но новых возможностей для него не планируется.
    Для новых сервисов рассмотрите [Camunda 8](camunda8-worker.md) или движок [Operaton](https://operaton.org/) — форк Camunda 7, развиваемый сообществом.

Модуль публикует [`Camunda 7 REST API`](https://docs.camunda.org/manual/7.24/reference/rest/overview/) приложения Kora:
он разворачивает стандартные `JAX-RS`-ресурсы `CamundaRestResources` в деплойменте `RESTEasy` и отдает их через **отдельный** HTTP-сервер `Undertow`.

Он используется вместе с [модулем Camunda 7 BPMN](camunda7-bpmn.md): `BPMN`-движок выполняет процессы, а этот модуль дает HTTP-доступ к операциям `Camunda 7` —
запуску экземпляров процессов, запросам задач и загрузок, корреляции сообщений и всему остальному, что предоставляет REST API движка.

Дополнительно модуль может отдавать `OpenAPI`-описание `REST API` вместе со страницами `Swagger UI` и `Scalar`.
Для запросов к `REST API` доступны собственные настройки `CORS`, логирования, метрик, трассировки и штатного завершения сервера.

## Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework.experimental:camunda-rest-undertow"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends CamundaRestUndertowModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework.experimental:camunda-rest-undertow")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : CamundaRestUndertowModule
    ```

Требует подключения [модуля Camunda 7 BPMN](camunda7-bpmn.md).
Сам движок `Camunda` подключен к этому модулю как `compileOnly`-зависимость, поэтому в classpath он попадает только через `camunda-engine-bpmn`, который к тому же и создает обслуживаемый `ProcessEngine`.

`CamundaRestUndertowModule` наследует `CamundaRestModule`: базовый модуль предоставляет конфигурацию, фабрику телеметрии и стандартное `JAX-RS`-приложение, а `Undertow`-модуль добавляет HTTP-обработчик и сам сервер.
В приложении подключается `CamundaRestUndertowModule` — подключение только `CamundaRestModule` оставит `REST API` без транспорта.

## HTTP-сервер { #http-server }

Модуль запускает **отдельный** независимый HTTP-сервер `Undertow`, выделенный под `Camunda 7 REST API`.
Он слушает собственный `port` (по умолчанию: `8081`) и полностью изолирован от основного модуля [HTTP-сервера](http-server.md):
у него собственный фильтр [CORS](#cors), собственная [телеметрия](#telemetry) и собственное [штатное завершение](container.md#component-lifecycle).
Таким образом, `Camunda REST API` и собственные контроллеры приложения работают на разных портах и не разделяют обработку запросов или конфигурацию.

По умолчанию сервер выключен и запускается опцией `camunda.rest.enabled = true`.
Сам `REST`-обработчик всегда собирается при инициализации графа — `enabled` определяет лишь то, будет ли открыт HTTP-слушатель.
Если указанный `port` уже занят, запуск падает с ошибкой `Camunda HTTP Server (Undertow) failed to start, cause port '<port>' is already in use`.

`ProcessEngine`, обслуживающий эти запросы, предоставляется [модулем Camunda 7 BPMN](camunda7-bpmn.md).
Внутри контейнера Kora зависимости между двумя модулями нет: `BPMN`-модуль регистрирует созданный движок в статическом реестре `ProcessEngines` из `Camunda`,
а этот модуль публикует `KoraProcessEngineProvider` через `ServiceLoader` по контракту `org.camunda.bpm.engine.rest.spi.ProcessEngineProvider`, который и достает движок по умолчанию из этого реестра.
Данный модуль лишь открывает к движку HTTP-доступ по настроенному `path` (по умолчанию: `/engine-rest`).

Запросы обрабатываются на виртуальных потоках, поэтому вызов `Camunda REST`, заблокированный на базе данных, не занимает I/O-поток `Undertow`.

При завершении работы сервер перестает принимать новые запросы и ждет до `shutdownWait` (по умолчанию: `30s`)
завершения уже обрабатываемых запросов, прежде чем остановиться.

## Конфигурация { #configuration }

Пример полной конфигурации, описанной в интерфейсе `CamundaRestConfig`:

===! ":material-code-json: `Hocon`"

    ```javascript
    camunda {
        rest {
            enabled = false //(1)!
            path = "/engine-rest" //(2)!
            port = 8081 //(3)!
            shutdownWait = "30s" //(4)!
            openapi {
                enabled = false //(5)!
                files = [ "openapi.json" ] //(6)!
                path = "/openapi" //(7)!
                cache = "GZIP" //(8)!
                swaggerui {
                    enabled = false //(9)!
                    path = "/swagger-ui" //(10)!
                    withCredentials = true //(11)!
                    cache = "GZIP" //(12)!
                    options { //(13)!
                        layout = "StandaloneLayout"
                        validatorUrl = "null"
                        defaultModelsExpandDepth = "0"
                        deepLinking = "true"
                        persistAuthorization = "true"
                        displayOperationId = "true"
                        filter = "true"
                    }
                }
                scalar {
                    enabled = false //(14)!
                    path = "/scalar" //(15)!
                    cache = "GZIP" //(16)!
                }
            }
            cors {
                enabled = false //(17)!
                allowOrigin = "*" //(18)!
                allowHeaders = [ "*" ] //(19)!
                allowMethods = [ "GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD" ] //(20)!
                allowCredentials = true //(21)!
                exposeHeaders = [ "*" ] //(22)!
                maxAge = "1h" //(23)!
            }
            telemetry {
                logging {
                    enabled = false //(24)!
                    stacktrace = true //(25)!
                    mask = "***" //(26)!
                    maskQueries = [ ] //(27)!
                    maskHeaders = [ "authorization", "cookie", "set-cookie" ] //(28)!
                    pathFull = false //(29)!
                }
                metrics {
                    enabled = false //(30)!
                    slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(31)!
                    tags = { //(32)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
                tracing {
                    enabled = true //(33)!
                    attributes = { //(34)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
            }
        }
    }
    ```

    1.  Запускает отдельный HTTP-сервер с `Camunda 7 REST API` (по умолчанию: `false`).
    2.  Префикс пути `Camunda 7 REST API` (по умолчанию: `/engine-rest`).
    3.  Порт отдельного HTTP-сервера `Undertow`, обслуживающего `REST API` (по умолчанию: `8081`).
    4.  Максимальное время ожидания [штатного завершения](container.md#component-lifecycle) HTTP-сервера (по умолчанию: `30s`).
    5.  Включает отдачу файлов `OpenAPI` (по умолчанию: `false`).
    6.  Список файлов `OpenAPI` в ресурсах приложения (по умолчанию: `[ "openapi.json" ]`), см. [OpenAPI](#openapi). Значение по умолчанию — спецификация, поставляемая в составе зависимости [`camunda-engine-rest-openapi`](https://mvnrepository.com/artifact/org.camunda.bpm/camunda-engine-rest-openapi).
    7.  Путь, по которому доступны файлы `OpenAPI` (по умолчанию: `/openapi`). При одном файле это ровно этот путь, при нескольких — префикс вида `/openapi/{file}`.
    8.  Режим кеширования ответов для файлов `OpenAPI`: `NONE`, `GZIP` или `FULL` (по умолчанию: `GZIP`), см. [Кэширование](openapi-management.md#cache).
    9.  Включает страницу `Swagger UI` (по умолчанию: `false`).
    10. Путь, по которому доступна страница `Swagger UI` (по умолчанию: `/swagger-ui`).
    11. Отправлять учетные данные браузера (куки, заголовок `Authorization`) в запросах из `Swagger UI` (по умолчанию: `true`).
    12. Режим кеширования ответов для страницы `Swagger UI`: `NONE`, `GZIP` или `FULL` (по умолчанию: `GZIP`).
    13. Параметры инициализации `Swagger UI`, см. [Параметры Swagger UI](openapi-management.md#swagger-ui-options) (по умолчанию: семь значений, показанных выше).
    14. Включает страницу `Scalar` (по умолчанию: `false`).
    15. Путь, по которому доступна страница `Scalar` (по умолчанию: `/scalar`).
    16. Режим кеширования ответов для страницы `Scalar`: `NONE`, `GZIP` или `FULL` (по умолчанию: `GZIP`).
    17. Включает фильтр `CORS` (по умолчанию: `false`).
    18. Разрешенный источник для `CORS` (по умолчанию не указан, опционально). Если значение не указано, фильтр возвращает заголовок `Origin` из запроса, а при его отсутствии — `*`.
    19. Разрешенные заголовки для `CORS`-запросов (по умолчанию: `[ "*" ]`).
    20. Разрешенные HTTP-методы для `CORS`-запросов (по умолчанию: `[ "GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD" ]`).
    21. Разрешена ли передача учетных данных в `CORS`-запросах (по умолчанию: `true`).
    22. Заголовки, доступные клиенту в `CORS`-ответе (по умолчанию: `[ "*" ]`).
    23. Максимальное время кеширования предварительных `CORS`-запросов (по умолчанию: `1h`).
    24. Включает логирование модуля (по умолчанию: `false`).
    25. Включает логирование стек-трейса при ошибке (по умолчанию: `true`).
    26. Маска, которой скрываются указанные заголовки и параметры запроса (по умолчанию: `***`).
    27. Список параметров запроса, которые нужно скрывать (по умолчанию: `[]`).
    28. Список заголовков запроса или ответа, которые нужно скрывать (по умолчанию: `[ "authorization", "cookie", "set-cookie" ]`).
    29. Логировать ли полный путь запроса вместо шаблона маршрута; если не указано, используется шаблон, кроме уровня `TRACE`, где используется полный путь (по умолчанию не указан, опционально).
    30. Включает метрики модуля (по умолчанию: `false`).
    31. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
    32. Теги метрик (по умолчанию: `{}`).
    33. Включает трассировку модуля (по умолчанию: `true`).
    34. Атрибуты трассировки (по умолчанию: `{}`).

=== ":simple-yaml: `YAML`"

    ```yaml
    camunda:
      rest:
        enabled: false #(1)!
        path: "/engine-rest" #(2)!
        port: 8081 #(3)!
        shutdownWait: "30s" #(4)!
        openapi:
          enabled: false #(5)!
          files: [ "openapi.json" ] #(6)!
          path: "/openapi" #(7)!
          cache: "GZIP" #(8)!
          swaggerui:
            enabled: false #(9)!
            path: "/swagger-ui" #(10)!
            withCredentials: true #(11)!
            cache: "GZIP" #(12)!
            options: #(13)!
              layout: "StandaloneLayout"
              validatorUrl: "null"
              defaultModelsExpandDepth: "0"
              deepLinking: "true"
              persistAuthorization: "true"
              displayOperationId: "true"
              filter: "true"
          scalar:
            enabled: false #(14)!
            path: "/scalar" #(15)!
            cache: "GZIP" #(16)!
        cors:
          enabled: false #(17)!
          allowOrigin: "*" #(18)!
          allowHeaders: [ "*" ] #(19)!
          allowMethods: [ "GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD" ] #(20)!
          allowCredentials: true #(21)!
          exposeHeaders: [ "*" ] #(22)!
          maxAge: "1h" #(23)!
        telemetry:
          logging:
            enabled: false #(24)!
            stacktrace: true #(25)!
            mask: "***" #(26)!
            maskQueries: [ ] #(27)!
            maskHeaders: [ "authorization", "cookie", "set-cookie" ] #(28)!
            pathFull: false #(29)!
          metrics:
            enabled: false #(30)!
            slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(31)!
            tags: #(32)!
              key1: value1
              key2: value2
          tracing:
            enabled: true #(33)!
            attributes: #(34)!
              key1: value1
              key2: value2
    ```

    1.  Запускает отдельный HTTP-сервер с `Camunda 7 REST API` (по умолчанию: `false`).
    2.  Префикс пути `Camunda 7 REST API` (по умолчанию: `/engine-rest`).
    3.  Порт отдельного HTTP-сервера `Undertow`, обслуживающего `REST API` (по умолчанию: `8081`).
    4.  Максимальное время ожидания [штатного завершения](container.md#component-lifecycle) HTTP-сервера (по умолчанию: `30s`).
    5.  Включает отдачу файлов `OpenAPI` (по умолчанию: `false`).
    6.  Список файлов `OpenAPI` в ресурсах приложения (по умолчанию: `[ "openapi.json" ]`), см. [OpenAPI](#openapi). Значение по умолчанию — спецификация, поставляемая в составе зависимости [`camunda-engine-rest-openapi`](https://mvnrepository.com/artifact/org.camunda.bpm/camunda-engine-rest-openapi).
    7.  Путь, по которому доступны файлы `OpenAPI` (по умолчанию: `/openapi`). При одном файле это ровно этот путь, при нескольких — префикс вида `/openapi/{file}`.
    8.  Режим кеширования ответов для файлов `OpenAPI`: `NONE`, `GZIP` или `FULL` (по умолчанию: `GZIP`), см. [Кэширование](openapi-management.md#cache).
    9.  Включает страницу `Swagger UI` (по умолчанию: `false`).
    10. Путь, по которому доступна страница `Swagger UI` (по умолчанию: `/swagger-ui`).
    11. Отправлять учетные данные браузера (куки, заголовок `Authorization`) в запросах из `Swagger UI` (по умолчанию: `true`).
    12. Режим кеширования ответов для страницы `Swagger UI`: `NONE`, `GZIP` или `FULL` (по умолчанию: `GZIP`).
    13. Параметры инициализации `Swagger UI`, см. [Параметры Swagger UI](openapi-management.md#swagger-ui-options) (по умолчанию: семь значений, показанных выше).
    14. Включает страницу `Scalar` (по умолчанию: `false`).
    15. Путь, по которому доступна страница `Scalar` (по умолчанию: `/scalar`).
    16. Режим кеширования ответов для страницы `Scalar`: `NONE`, `GZIP` или `FULL` (по умолчанию: `GZIP`).
    17. Включает фильтр `CORS` (по умолчанию: `false`).
    18. Разрешенный источник для `CORS` (по умолчанию не указан, опционально). Если значение не указано, фильтр возвращает заголовок `Origin` из запроса, а при его отсутствии — `*`.
    19. Разрешенные заголовки для `CORS`-запросов (по умолчанию: `[ "*" ]`).
    20. Разрешенные HTTP-методы для `CORS`-запросов (по умолчанию: `[ "GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD" ]`).
    21. Разрешена ли передача учетных данных в `CORS`-запросах (по умолчанию: `true`).
    22. Заголовки, доступные клиенту в `CORS`-ответе (по умолчанию: `[ "*" ]`).
    23. Максимальное время кеширования предварительных `CORS`-запросов (по умолчанию: `1h`).
    24. Включает логирование модуля (по умолчанию: `false`).
    25. Включает логирование стек-трейса при ошибке (по умолчанию: `true`).
    26. Маска, которой скрываются указанные заголовки и параметры запроса (по умолчанию: `***`).
    27. Список параметров запроса, которые нужно скрывать (по умолчанию: `[]`).
    28. Список заголовков запроса или ответа, которые нужно скрывать (по умолчанию: `[ "authorization", "cookie", "set-cookie" ]`).
    29. Логировать ли полный путь запроса вместо шаблона маршрута; если не указано, используется шаблон, кроме уровня `TRACE`, где используется полный путь (по умолчанию не указан, опционально).
    30. Включает метрики модуля (по умолчанию: `false`).
    31. Настройка [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`).
    32. Теги метрик (по умолчанию: `{}`).
    33. Включает трассировку модуля (по умолчанию: `true`).
    34. Атрибуты трассировки (по умолчанию: `{}`).

В листинге выше показаны все доступные опции; на практике включают только то, что действительно нужно.
Типовая конфигурация публикует `REST API` на своем `port` вместе с описанием `OpenAPI`, страницей `Swagger UI` и логированием запросов:

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

Значения `cache` сопоставляются с константами перечисления буквально, поэтому их нужно писать в верхнем регистре.

## OpenAPI { #openapi }

Помимо самого `REST API`, отдельный сервер может отдавать `OpenAPI`-описание API вместе со
страницами [Swagger UI](https://swagger.io/tools/swagger-ui/) и [Scalar](https://scalar.com/).
Все три по умолчанию отключены и включаются независимо друг от друга через секцию конфигурации `openapi`,
и все три отдаются теми же обработчиками, что использует модуль [управления OpenAPI](openapi-management.md), поэтому их поведение совпадает.

При включении страницы доступны на `port` `REST`-сервера по настроенным путям:

| Страница             | Флаг конфигурации           | Путь по умолчанию |
|----------------------|-----------------------------|-------------------|
| Спецификация OpenAPI | `openapi.enabled`           | `/openapi`        |
| Swagger UI           | `openapi.swaggerui.enabled` | `/swagger-ui`     |
| Scalar               | `openapi.scalar.enabled`    | `/scalar`         |

Например, при `port = 8090` и `openapi.enabled = true` спецификация отдается по адресу `http://localhost:8090/openapi`,
а `Swagger UI` (если включен) — по адресу `http://localhost:8090/swagger-ui`.
Все, что не попадает ни в эти пути, ни в префикс `path` `REST API`, отвечает `404`.

По умолчанию модуль отдает `OpenAPI`-спецификацию, поставляемую в составе зависимости
[`camunda-engine-rest-openapi`](https://mvnrepository.com/artifact/org.camunda.bpm/camunda-engine-rest-openapi), поэтому у `files` уже есть рабочее значение по умолчанию.
Перед отправкой файла модуль заменяет в нем порт `8080` на настроенный `port`, а если `path` отличается от `/engine-rest` — заменяет и префикс `engine-rest`,
поэтому отдаваемый `OpenAPI` всегда соответствует актуальному адресу `REST API`.

Чтобы вместо этого отдавать собственную спецификацию, укажите в `openapi.files` один или несколько файлов в `resources`:

===! ":material-code-json: `Hocon`"

    ```javascript
    camunda.rest.openapi {
        enabled = true
        files = [ "my-openapi.json" ]
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    camunda:
      rest:
        openapi:
          enabled: true
          files: [ "my-openapi.json" ]
    ```

Каждый путь разрешается как ресурс classpath — сначала как записан, затем с добавленным ведущим `/`, поэтому `openapi/my.json` и `/openapi/my.json` указывают на один и тот же ресурс.
Файл с расширением `.json` отдается как `text/json`, любое другое расширение — как `text/x-yaml`.

Когда файлов несколько, публичное имя файла в URL выводится из имени файла: каталоги отбрасываются, а расширение `.json`, `.yml` или `.yaml` удаляется.
Так, при `files = [ "openapi/engine.json", "openapi/custom.json" ]` спецификации доступны по адресам `/openapi/engine` и `/openapi/custom`, а сам `/openapi` отвечает `404`.

## CORS { #cors }

У `REST`-сервера есть собственный фильтр [CORS](https://developer.mozilla.org/ru/docs/Web/HTTP/CORS), отключенный по умолчанию и включаемый через `cors.enabled`.
При включении фильтр оборачивает сервер целиком — и `REST API`, и страницы `OpenAPI` — и добавляет заголовки `Access-Control-*` к каждому ответу, не перехватывая предварительные запросы самостоятельно.

Если `cors.allowOrigin` не задан, фильтр возвращает в ответе заголовок `Origin` из запроса,
а при отсутствии заголовка `Origin` в запросе использует `*`.
Остальные параметры `cors.*` управляют разрешенными заголовками и методами, разрешена ли передача учетных данных,
заголовками, доступными клиенту, и временем кеширования предварительных запросов.
Заголовок, который ресурс уже выставил сам, никогда не перезаписывается, а `Access-Control-Expose-Headers` не добавляется вовсе, если `exposeHeaders` пуст.

## Телеметрия { #telemetry }

Запросы, обрабатываемые `REST`-сервером, охвачены стандартными сигналами телеметрии Kora — [логированием](logging-slf4j.md),
[метриками](metrics.md) и [трассировкой](tracing.md) — которые настраиваются в секции `telemetry`.
Логирование и метрики по умолчанию отключены, трассировка по умолчанию включена; когда выключено все три, модуль подставляет пустую телеметрию и не добавляет накладных расходов на запрос.

Логирование пишется в логгер `io.koraframework.http.server.common.HttpServer` и создает событие `CamundaRest received request` перед вызовом
и событие `CamundaRest succeed response` (или `CamundaRest errored response` при ошибке) после него.
Поле `operation` содержит метод и шаблон маршрута, к событию ответа добавляются `resultCode`, `statusCode` и `processingTime`, а параметры запроса и заголовки добавляются на уровне `DEBUG`.
Заголовки из `maskHeaders` и параметры запроса из `maskQueries` заменяются значением `mask`.
В логируемой операции по умолчанию используется шаблон маршрута, а полный путь — при `pathFull = true` либо на уровне логгера `TRACE`.

Трассировка создает на каждый запрос span `<METHOD> <шаблон маршрута>` типа `SERVER` с атрибутами `http.request.method`, `url.scheme`, `server.address`, `url.path`, `http.route`, `http.response.status_code` и `http.response.result_code`.
Входящий контекст трассировки `W3C` пробрасывается в span, а результирующий контекст записывается обратно в заголовки ответа.

Метрики модуля описаны в разделе [Справочник метрик](metrics.md#camunda-rest).

Стандартную телеметрию можно переопределить, зарегистрировав как `@Component` собственного наследника `DefaultCamundaRestLoggerFactory` или `DefaultCamundaRestMetricsFactory`;
вся `CamundaRestTelemetryFactory` предоставляется через `@DefaultComponent` и также может быть заменена.

### Шаблоны маршрутов { #route-templates }

Метрики, трассировка и логирование опознают запрос по шаблону маршрута, а не по полному пути, поэтому `/engine-rest/process-instance/{id}` остается одним временным рядом независимо от количества экземпляров процессов.

Модуль не может узнать подобранный шаблон у `RESTEasy`, поэтому хранит встроенную таблицу всех маршрутов `Camunda 7 REST API` с настроенным префиксом `path` и сопоставляет запрос с ней.
Запрос, которому в этой таблице ничего не соответствует — неизвестный endpoint или собственный `JAX-RS`-ресурс, добавленный через [Приложения](#applications), — все равно обслуживается, но не создает ни записи в логе, ни span'а,
а его метрика длительности записывается с тегом `http.route`, равным `UNKNOWN_ROUTE`.

## Приложения { #applications }

Модуль уже регистрирует стандартный `@Tag(CamundaRest.class)` `jakarta.ws.rs.core.Application`, который публикует стандартные
ресурсы `Camunda 7 REST API` (`CamundaRestResources`) вместе с `ResteasyJackson2Provider` для сериализации в `JSON`.

Чтобы добавить собственные ресурсы `JAX-RS`, зарегистрируйте свой компонент `jakarta.ws.rs.core.Application`, помеченный тегом `@Tag(CamundaRest.class)`.
Все такие приложения собираются и объединяются со стандартным — их `getClasses()`, `getSingletons()` и `getProperties()` комбинируются —
поэтому пользовательские ресурсы отдаются на том же `REST`-сервере вместе со стандартными endpoint'ами Camunda и под тем же префиксом `path`.

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

Собственные ресурсы не входят во встроенную таблицу маршрутов, поэтому в метриках они отражаются как `UNKNOWN_ROUTE` и не логируются и не трассируются, см. [Шаблоны маршрутов](#route-templates).
