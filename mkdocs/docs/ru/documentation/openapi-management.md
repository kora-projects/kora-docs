---
description: "Explains Kora OpenAPI management module for serving generated OpenAPI specifications through the management HTTP server. Use when working with OpenApiManagementModule, OpenAPI, management endpoint, private HTTP server."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora OpenAPI management module for serving generated OpenAPI specifications through the management HTTP server; key triggers include OpenApiManagementModule, OpenAPI, management endpoint, private HTTP server."
---

Модуль `openapi-management` предоставляет из приложения готовые файлы `OpenAPI`, а также страницы [Swagger UI](https://swagger.io/tools/swagger-ui/) и [RapiDoc](https://rapidocweb.com/) для их просмотра.
`OpenAPI` — это машиночитаемый контракт HTTP API: по нему удобно проверять доступные операции, модели данных и параметры запросов.

Модуль не создает контракт из кода, а публикует уже существующие файлы из ресурсов приложения.
Это полезно для локальной разработки, тестовых окружений и служебного доступа к описанию API без отдельного сервера документации.

Если нужен пошаговый разбор перед справочным описанием, смотрите [OpenAPI HTTP сервер](../guides/openapi-http-server.md).

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

Требует подключения [HTTP-сервера](http-server.md), так как регистрирует собственные `GET`-обработчики для выдачи файлов и страниц просмотра.

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

    1.  Путь к файлу `OpenAPI` или список путей относительно ресурсов приложения (`обязательная`, по умолчанию не указано).
    2.  Включает выдачу файлов `OpenAPI` через HTTP-обработчик (по умолчанию: `false`).
    3.  Путь, по которому доступны файлы `OpenAPI` (по умолчанию: `/openapi`).
        Если указан один файл, он доступен ровно по этому пути.
        Если указано несколько файлов, путь становится префиксом вида `/openapi/{file}`.
        Значение `{file}` берется из имени файла без директорий и расширения `.json`, `.yml` или `.yaml`: файл `someDirectory/my-openapi-1.yaml` будет доступен по пути `/openapi/my-openapi-1`.
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

    1.  Путь к файлу `OpenAPI` или список путей относительно ресурсов приложения (`обязательная`, по умолчанию не указано).
    2.  Включает выдачу файлов `OpenAPI` через HTTP-обработчик (по умолчанию: `false`).
    3.  Путь, по которому доступны файлы `OpenAPI` (по умолчанию: `/openapi`).
        Если указан один файл, он доступен ровно по этому пути.
        Если указано несколько файлов, путь становится префиксом вида `/openapi/{file}`.
        Значение `{file}` берется из имени файла без директорий и расширения `.json`, `.yml` или `.yaml`: файл `someDirectory/my-openapi-1.yaml` будет доступен по пути `/openapi/my-openapi-1`.
    4.  Включает страницу `Swagger UI` (по умолчанию: `false`).
    5.  Путь, по которому доступна страница `Swagger UI` (по умолчанию: `/swagger-ui`).
    6.  Включает страницу `RapiDoc` (по умолчанию: `false`).
    7.  Путь, по которому доступна страница `RapiDoc` (по умолчанию: `/rapidoc`).

Файлы читаются из ресурсов приложения при первом обращении и затем сохраняются в памяти.
Для файлов `.json` используется тип ответа `text/json; charset=utf-8`, для остальных файлов — `text/x-yaml; charset=utf-8`.

При нескольких файлах `Swagger UI` показывает список доступных контрактов.
`RapiDoc` открывает первый файл из списка.
Если включен `Swagger UI`, дополнительно регистрируется путь для `OAuth`-перенаправления.

## Совет { #recommendations }

???+ warning "Совет"

    Мы советуем использовать подход, при котором сначала создается [контракт, а затем по нему создается код](openapi-codegen.md).
    В этом случае модуль публикует тот же файл контракта, который используется для генерации.

    Если сначала пишется код, а контракт должен создаваться по нему, можно использовать [Swagger Gradle Plugin](https://github.com/swagger-api/swagger-core/blob/master/modules/swagger-gradle-plugin/README.md)
    вместе с [аннотациями Swagger](https://github.com/swagger-api/swagger-core/wiki/Swagger-2.X---Annotations).
