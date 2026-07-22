---
description: "Описывает модуль управления OpenAPI в Kora для публикации сгенерированных спецификаций OpenAPI, а также страниц Swagger UI и RapiDoc через публичный HTTP-сервер. Используйте при работе с OpenApiManagementModule, OpenApiManagementConfig, маршруты OpenAPI, Swagger UI, RapiDoc."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora OpenAPI management module for serving generated OpenAPI specifications, Swagger UI, and RapiDoc pages through the public HTTP server; key triggers include OpenApiManagementModule, OpenApiManagementConfig, OpenAPI endpoint, Swagger UI, RapiDoc, /openapi, /swagger-ui, /rapidoc."
---

Модуль `openapi-management` предоставляет из приложения готовые файлы `OpenAPI`, а также страницы [Swagger UI](https://swagger.io/tools/swagger-ui/) и [RapiDoc](https://rapidocweb.com/) для их просмотра.
`OpenAPI` — это машиночитаемый контракт HTTP API: по нему удобно проверять доступные операции, модели данных и параметры запросов.

Модуль не создает контракт из кода, а публикует уже существующие файлы из ресурсов приложения.
Это полезно для локальной разработки, тестовых окружений и служебного доступа к описанию API без отдельного сервера документации.

Если нужен пошаговый разбор перед справочным описанием, смотрите [HTTP-сервер OpenAPI](../guides/openapi-http-server.md).

## Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "ru.tinkoff.kora:openapi-management"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends OpenApiManagementModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("ru.tinkoff.kora:openapi-management")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : OpenApiManagementModule
    ```

Требует подключения модуля [HTTP-сервера](http-server.md), так как регистрирует собственные `GET`-обработчики для выдачи файлов и страниц просмотра.
Это обычные бины `HttpServerRequestHandler`, которые собирает **публичный** HTTP-сервер, поэтому пути `/openapi`, `/swagger-ui` и `/rapidoc` доступны на публичном HTTP-порту, а не на приватном (management) порту.

## Конфигурация { #configuration }

Пример конфигурации, описанной в классе `OpenApiManagementConfig`:

===! ":material-code-json: `Hocon`"

    ```javascript
    openapi {
        management {
            file = [ "my-openapi-1.yaml", "my-openapi-2.yaml" ] //(1)!
            enabled = false  //(2)!
            endpoint = "/openapi" //(3)!
            swaggerui {
                enabled = false //(4)!
                endpoint = "/swagger-ui" //(5)!
            }
            rapidoc {
                enabled = false //(6)!
                endpoint = "/rapidoc" //(7)!
            }
        }
    }
    ```

    1.  Путь к файлу `OpenAPI` или список путей относительно ресурсов приложения (обязательный, по умолчанию не указан).
    2.  Включает выдачу файлов `OpenAPI` через HTTP-обработчик (по умолчанию: `false`).
    3.  Путь, по которому доступны файлы `OpenAPI` (по умолчанию: `/openapi`).
        Если указан один файл, он доступен ровно по этому пути.
        Если указано несколько файлов, путь становится префиксом вида `/openapi/{file}`.
        Значение `{file}` берется из имени файла без директорий и без расширения `.json`, `.yml` или `.yaml`: файл `someDirectory/my-openapi-1.yaml` будет доступен по пути `/openapi/my-openapi-1`.
    4.  Включает страницу `Swagger UI` (по умолчанию: `false`).
    5.  Путь, по которому доступна страница `Swagger UI` (по умолчанию: `/swagger-ui`).
    6.  Включает страницу `RapiDoc` (по умолчанию: `false`).
    7.  Путь, по которому доступна страница `RapiDoc` (по умолчанию: `/rapidoc`).

=== ":simple-yaml: `YAML`"

    ```yaml
    openapi:
      management:
        file: [ "my-openapi-1.yaml", "my-openapi-2.yaml" ] #(1)!
        enabled: false  #(2)!
        endpoint: "/openapi" #(3)!
        swaggerui:
          enabled: false #(4)!
          endpoint: "/swagger-ui" #(5)!
        rapidoc:
          enabled: false #(6)!
          endpoint: "/rapidoc" #(7)!
    ```

    1.  Путь к файлу `OpenAPI` или список путей относительно ресурсов приложения (обязательный, по умолчанию не указан).
    2.  Включает выдачу файлов `OpenAPI` через HTTP-обработчик (по умолчанию: `false`).
    3.  Путь, по которому доступны файлы `OpenAPI` (по умолчанию: `/openapi`).
        Если указан один файл, он доступен ровно по этому пути.
        Если указано несколько файлов, путь становится префиксом вида `/openapi/{file}`.
        Значение `{file}` берется из имени файла без директорий и без расширения `.json`, `.yml` или `.yaml`: файл `someDirectory/my-openapi-1.yaml` будет доступен по пути `/openapi/my-openapi-1`.
    4.  Включает страницу `Swagger UI` (по умолчанию: `false`).
    5.  Путь, по которому доступна страница `Swagger UI` (по умолчанию: `/swagger-ui`).
    6.  Включает страницу `RapiDoc` (по умолчанию: `false`).
    7.  Путь, по которому доступна страница `RapiDoc` (по умолчанию: `/rapidoc`).

Файлы читаются из ресурсов приложения при первом обращении и затем кэшируются в памяти (последующие запросы возвращают закэшированные байты).
Для файлов с расширением `.json` используется тип ответа `text/json; charset=utf-8`, для всех остальных файлов — `text/x-yaml; charset=utf-8`.

При нескольких файлах `Swagger UI` показывает список доступных контрактов, а `RapiDoc` открывает первый файл из списка.

Когда настроено несколько файлов, запрос к `/openapi/{file}` с неизвестным именем `{file}` возвращает `404` (`OpenAPI file not registered`), а запрос с пустым значением `{file}` возвращает `400` (`OpenAPI file not specified`).
Если настроенный ресурс не удается найти или прочитать в момент запроса, обработчик возвращает `404` или `500` соответственно, иначе он отвечает `200` и содержимым файла.

## Маршруты { #endpoints }

При включенной выдаче модуль регистрирует на публичном HTTP-сервере следующие `GET`-маршруты (пути показаны со значениями `endpoint` по умолчанию):

| Маршрут | Обработчик | Включается через |
|-------|-----------------|------------|
| `GET /openapi` (один файл) или `GET /openapi/{file}` (несколько файлов) | `OpenApiHttpServerHandler` | `enabled = true` |
| `GET /swagger-ui` | `SwaggerUIHttpServerHandler` | `swaggerui.enabled = true` |
| `GET /swagger-ui/oauth2-redirect` | `SwaggerOauthHttpServerHandler` | регистрируется автоматически вместе со `Swagger UI` |
| `GET /rapidoc` | `RapidocHttpServerHandler` | `rapidoc.enabled = true` |

Каждый маршрут использует значение `endpoint` из своей секции конфигурации, поэтому переопределение `endpoint` переносит соответствующий маршрут.
Путь `OAuth2`-перенаправления всегда равен `swaggerui.endpoint` с добавленным суффиксом `/oauth2-redirect`.

## Рекомендации { #recommendations }

???+ warning "Рекомендация"

    Мы советуем использовать подход, при котором сначала создается [контракт, а затем по нему генерируется код](openapi-codegen.md).
    В этом случае модуль публикует тот же файл контракта, который используется для генерации.

    Если сначала пишется код, а контракт должен создаваться по нему, можно использовать [Swagger Gradle Plugin](https://github.com/swagger-api/swagger-core/blob/master/modules/swagger-gradle-plugin/README.md)
    вместе с [аннотациями Swagger](https://github.com/swagger-api/swagger-core/wiki/Swagger-2.X---Annotations).
