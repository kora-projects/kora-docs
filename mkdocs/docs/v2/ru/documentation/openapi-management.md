---
description: "Explains the Kora OpenAPI management module that publishes OpenAPI contract files and the Swagger UI and Scalar viewer pages through the public HTTP server. Use when working with OpenApiManagementModule, OpenApiManagementConfig, openapi.management.files, CacheMode, Swagger UI, Scalar."
agent:
  use_when: "Use this file for Kora docs or implementation questions about the Kora OpenAPI management module that publishes OpenAPI contract files and the Swagger UI and Scalar viewer pages through the public HTTP server; key triggers include OpenApiManagementModule, OpenApiManagementConfig, OpenApiHttpServerHandler, SwaggerUIHttpServerHandler, ScalarHttpServerHandler, openapi.management.files, openapi.management.path, swaggerui, scalar, CacheMode, /openapi, /swagger-ui, /scalar."
---

Модуль `openapi-management` предоставляет из приложения готовые файлы `OpenAPI`, а также страницы [Swagger UI](https://swagger.io/tools/swagger-ui/) и [Scalar](https://scalar.com/) для их просмотра.
`OpenAPI` — это машиночитаемый контракт HTTP API: по нему удобно проверять доступные операции, модели данных и параметры запросов.

Модуль не создает контракт из кода, а публикует уже существующие файлы из ресурсов приложения.
Это полезно для локальной разработки, тестовых окружений и служебного доступа к описанию API без отдельного сервера документации.

Обе страницы просмотра поставляются внутри модуля как полностью самодостаточные ресурсы, поэтому `Swagger UI` и `Scalar` открываются без доступа в интернет и без какого-либо `CDN`.

Если нужен пошаговый разбор перед справочным описанием, смотрите [HTTP-сервер OpenAPI](../guides/openapi-http-server.md).

## Подключение { #dependency }

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:openapi-management"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends OpenApiManagementModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:openapi-management")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : OpenApiManagementModule
    ```

Требует подключения модуля [HTTP-сервера](http-server.md), так как регистрирует собственные `GET`-обработчики для выдачи файлов и страниц просмотра.
Это обычные компоненты `HttpServerRequestHandler`, объявленные без системного тега, поэтому их собирает **публичный** HTTP-сервер: пути `/openapi`, `/swagger-ui` и `/scalar` доступны на `httpServer.port`, а не на системном порту `httpServer.system.port`.

## Конфигурация { #configuration }

Конфигурация читается из секции `openapi.management` и описана классом `OpenApiManagementConfig`:

===! ":material-code-json: `Hocon`"

    ```javascript
    openapi {
        management {
            enabled = true //(1)!
            files = [ "openapi/my-openapi-1.yaml", "openapi/my-openapi-2.yaml" ] //(2)!
            path = "/openapi" //(3)!
            cache = "GZIP" //(4)!
            swaggerui {
                enabled = true //(5)!
                path = "/swagger-ui" //(6)!
                withCredentials = true //(7)!
                cache = "GZIP" //(8)!
                options { //(9)!
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
                enabled = true //(10)!
                path = "/scalar" //(11)!
                cache = "GZIP" //(12)!
            }
        }
    }
    ```

    1.  Включает выдачу файлов `OpenAPI` через HTTP-обработчик (по умолчанию: `false`).
    2.  Список путей к файлам `OpenAPI` относительно ресурсов приложения (обязательный, значения по умолчанию нет), смотрите [Файлы контрактов](#files).
    3.  Путь, по которому доступны файлы `OpenAPI` (по умолчанию: `/openapi`).
        Если указан один файл, он доступен ровно по этому пути.
        Если указано больше одного файла, путь становится префиксом вида `/openapi/{file}`.
    4.  Режим кэширования ответа для файлов `OpenAPI`: `NONE`, `GZIP` или `FULL` (по умолчанию: `GZIP`), смотрите [Кэширование](#cache).
    5.  Включает страницу `Swagger UI` (по умолчанию: `false`).
    6.  Путь, по которому доступна страница `Swagger UI` (по умолчанию: `/swagger-ui`).
    7.  Отправлять учетные данные браузера (куки, заголовок `Authorization`) в запросах из `Swagger UI` (по умолчанию: `true`).
    8.  Режим кэширования ответа для страницы `Swagger UI`: `NONE`, `GZIP` или `FULL` (по умолчанию: `GZIP`), смотрите [Кэширование](#cache).
    9.  Параметры инициализации `Swagger UI`, смотрите [Параметры Swagger UI](#swagger-ui-options) (по умолчанию: семь значений, показанных выше).
    10. Включает страницу `Scalar` (по умолчанию: `false`).
    11. Путь, по которому доступна страница `Scalar` (по умолчанию: `/scalar`).
    12. Режим кэширования ответа для страницы `Scalar`: `NONE`, `GZIP` или `FULL` (по умолчанию: `GZIP`), смотрите [Кэширование](#cache).

=== ":simple-yaml: `YAML`"

    ```yaml
    openapi:
      management:
        enabled: true #(1)!
        files: [ "openapi/my-openapi-1.yaml", "openapi/my-openapi-2.yaml" ] #(2)!
        path: "/openapi" #(3)!
        cache: "GZIP" #(4)!
        swaggerui:
          enabled: true #(5)!
          path: "/swagger-ui" #(6)!
          withCredentials: true #(7)!
          cache: "GZIP" #(8)!
          options: #(9)!
            layout: "StandaloneLayout"
            validatorUrl: "null"
            defaultModelsExpandDepth: "0"
            deepLinking: "true"
            persistAuthorization: "true"
            displayOperationId: "true"
            filter: "true"
        scalar:
          enabled: true #(10)!
          path: "/scalar" #(11)!
          cache: "GZIP" #(12)!
    ```

    1.  Включает выдачу файлов `OpenAPI` через HTTP-обработчик (по умолчанию: `false`).
    2.  Список путей к файлам `OpenAPI` относительно ресурсов приложения (обязательный, значения по умолчанию нет), смотрите [Файлы контрактов](#files).
    3.  Путь, по которому доступны файлы `OpenAPI` (по умолчанию: `/openapi`).
        Если указан один файл, он доступен ровно по этому пути.
        Если указано больше одного файла, путь становится префиксом вида `/openapi/{file}`.
    4.  Режим кэширования ответа для файлов `OpenAPI`: `NONE`, `GZIP` или `FULL` (по умолчанию: `GZIP`), смотрите [Кэширование](#cache).
    5.  Включает страницу `Swagger UI` (по умолчанию: `false`).
    6.  Путь, по которому доступна страница `Swagger UI` (по умолчанию: `/swagger-ui`).
    7.  Отправлять учетные данные браузера (куки, заголовок `Authorization`) в запросах из `Swagger UI` (по умолчанию: `true`).
    8.  Режим кэширования ответа для страницы `Swagger UI`: `NONE`, `GZIP` или `FULL` (по умолчанию: `GZIP`), смотрите [Кэширование](#cache).
    9.  Параметры инициализации `Swagger UI`, смотрите [Параметры Swagger UI](#swagger-ui-options) (по умолчанию: семь значений, показанных выше).
    10. Включает страницу `Scalar` (по умолчанию: `false`).
    11. Путь, по которому доступна страница `Scalar` (по умолчанию: `/scalar`).
    12. Режим кэширования ответа для страницы `Scalar`: `NONE`, `GZIP` или `FULL` (по умолчанию: `GZIP`), смотрите [Кэширование](#cache).

Значения `cache` сопоставляются с константами перечисления точно, поэтому их нужно писать в верхнем регистре.

Минимальная рабочая конфигурация состоит из `files` и флагов того, что нужно опубликовать:

===! ":material-code-json: `Hocon`"

    ```javascript
    openapi {
        management {
            enabled = true
            files = "openapi/http-server.yaml"
            swaggerui.enabled = true
            scalar.enabled = true
        }
    }
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    openapi:
      management:
        enabled: true
        files: "openapi/http-server.yaml"
        swaggerui:
          enabled: true
        scalar:
          enabled: true
    ```

### Файлы контрактов { #files }

`files` — единственный обязательный параметр секции: значения по умолчанию у него нет, поэтому приложение, которое подключает `OpenApiManagementModule`, но не задает `openapi.management.files`, падает на этапе сборки графа с `ConfigValueException`, указывающим на этот путь.
Проверка происходит независимо от `enabled` — конфигурация отображается до того, как какой-либо флаг будет прочитан.

Ожидается список путей, но обычная строка тоже принимается и разбивается по `,`, поэтому все три записи ниже эквивалентны списку из двух элементов:

===! ":material-code-json: `Hocon`"

    ```javascript
    files = [ "openapi/user.yaml", "openapi/data.yaml" ]
    files = "openapi/user.yaml,openapi/data.yaml"
    files = "openapi/user.yaml, openapi/data.yaml"
    ```

=== ":simple-yaml: `YAML`"

    ```yaml
    files: [ "openapi/user.yaml", "openapi/data.yaml" ]
    files: "openapi/user.yaml,openapi/data.yaml"
    files: "openapi/user.yaml, openapi/data.yaml"
    ```

Каждый путь ищется как ресурс на classpath — сначала как написан, затем с добавленным ведущим `/`, поэтому `openapi/user.yaml` и `/openapi/user.yaml` указывают на один и тот же ресурс.

Когда настроено больше одного файла, публичное имя файла в URL выводится из имени файла: директории отбрасываются, а завершающее расширение `.json`, `.yml` или `.yaml` удаляется.
Так, файл `someDirectory/my-openapi-1.yaml` доступен по пути `/openapi/my-openapi-1`.

Тип содержимого ответа зависит от расширения: файлы, оканчивающиеся на `.json`, отдаются как `text/json; charset=utf-8`, все остальные — как `text/x-yaml; charset=utf-8`.

Сценарии отказа у обработчика файлов:

| Ситуация | Ответ |
|-----------|----------|
| Настроено больше одного файла, `{file}` пустой | `400`, `OpenAPI file not specified` |
| `{file}` не совпадает ни с одним настроенным файлом | `404`, `OpenAPI file not registered: <name>` |
| Настроенный ресурс не найден на classpath | `404`, `OpenAPI file not found while reading: <path>` |
| Ресурс существует, но прочитать его не удалось | `500`, `Can't read OpenAPI file: <path>` |

Ресурсы читаются лениво при первом обращении, поэтому опечатка в `files` не ломает запуск приложения — она проявляется как `404` на маршруте.

### Кэширование { #cache }

У каждого выдаваемого ресурса — у каждого файла `OpenAPI`, у страницы `Swagger UI` и у страницы `Scalar` — есть свой параметр `cache`, который определяет, что остается в памяти после первого чтения:

| Режим | Запрос с `gzip` | Запрос без `gzip` |
|------|---------------------|------------------------|
| `NONE` | ресурс читается и сжимается на каждый запрос | ресурс читается на каждый запрос |
| `GZIP` | ресурс читается и сжимается один раз, затем переиспользуется | ресурс читается на каждый запрос |
| `FULL` | ресурс читается и сжимается один раз, затем переиспользуется | ресурс читается один раз, затем переиспользуется |

`GZIP` используется по умолчанию и покрывает обычный случай, когда браузеры и API-клиенты сообщают о поддержке `gzip`.
`FULL` дополнительно кэширует несжатую форму, а `NONE` полностью отключает кэширование, что удобно, пока файл контракта еще правится.

Сжатие применяется только если о нем сообщил запрос: в `Accept-Encoding` должен быть указан `gzip` без коэффициента качества `q=0`.
Сжатый ответ содержит `Content-Encoding: gzip`; и сжатый, и несжатый ответ содержат `Vary: Accept-Encoding`, чтобы промежуточные кэши не перепутали два представления.

Страница `OAuth2`-перенаправления `Swagger UI` — исключение: она никогда не сжимается и всегда кэшируется в памяти после первого запроса.

### Параметры Swagger UI { #swagger-ui-options }

`swaggerui.options` — это набор параметров инициализации `Swagger UI`, которые подставляются в генерируемую страницу.
Значения по умолчанию:

| Параметр | Значение в конфигурации | Значение на странице |
|--------|------------------|-------------------|
| `layout` | `"StandaloneLayout"` | `"StandaloneLayout"` |
| `validatorUrl` | `"null"` | `null` |
| `defaultModelsExpandDepth` | `"0"` | `0` |
| `deepLinking` | `"true"` | `true` |
| `persistAuthorization` | `"true"` | `true` |
| `displayOperationId` | `"true"` | `true` |
| `filter` | `"true"` | `true` |

Значения хранятся как строки, но подставляются в страницу как сырой `JavaScript`, если после обрезки пробелов они равны `null`, `true`, `false`, являются числом или начинаются с `{`, `[`, `function` или `(`.
Все остальное подставляется как строковый литерал `JavaScript`, а пустое значение превращается в `""`.
Это позволяет передавать через конфигурацию объекты и функции:

===! ":material-code-json: `Hocon`"

    ```javascript
    openapi.management.swaggerui.options {
        layout = "BaseLayout" //(1)!
        defaultModelsExpandDepth = "-1"
        syntaxHighlight = "{ activated: false }" //(2)!
        onComplete = "() => window.swaggerReady = true" //(3)!
    }
    ```

    1. Подставляется как строка `JavaScript`.
    2. Подставляется как объект `JavaScript`, так как значение начинается с `{`.
    3. Подставляется как стрелочная функция `JavaScript`, так как значение начинается с `(`.

=== ":simple-yaml: `YAML`"

    ```yaml
    openapi:
      management:
        swaggerui:
          options:
            layout: "BaseLayout" #(1)!
            defaultModelsExpandDepth: "-1"
            syntaxHighlight: "{ activated: false }" #(2)!
            onComplete: "() => window.swaggerReady = true" #(3)!
    ```

    1. Подставляется как строка `JavaScript`.
    2. Подставляется как объект `JavaScript`, так как значение начинается с `{`.
    3. Подставляется как стрелочная функция `JavaScript`, так как значение начинается с `(`.

???+ warning "Параметры заменяют значения по умолчанию"

    Набор не объединяется со встроенными значениями по умолчанию: как только `options` появляется в конфигурации, на страницу попадают только перечисленные там ключи.
    Если нужно изменить один параметр, перечислите рядом с ним и те значения по умолчанию, которые нужно сохранить.

`withCredentials` настраивается отдельно от `options`, потому что влияет сразу на две вещи: он передается в `Swagger UI` как флаг `withCredentials`, и при значении `true` страница дополнительно устанавливает перехватчик, который проставляет `credentials = "include"` каждому запросу из кнопки «Try it out».
Отключайте его, когда API вызывается из `Swagger UI` с другого origin и учетные данные браузера прикреплять не нужно.

Страница также понимает значение `contextPath`, которое берется из куки `contextPath`, а если куки нет — из строки запроса страницы (`/swagger-ui?contextPath=/api`).
Когда оно задано, все пути отображаемого контракта показываются с этим префиксом, что удобно, если сервис опубликован за префиксом пути.

### Scalar { #scalar }

`Scalar` — вторая встроенная страница просмотра, она включается независимо от `Swagger UI`: обе страницы можно опубликовать одновременно над одними и теми же файлами контрактов.
Она получает тот же список контрактов, поэтому при нескольких файлах переключатель документов перечисляет каждый файл по его публичному имени.

Обе страницы вычисляют `URL` контракта в браузере: они берут текущий адрес страницы и заменяют в нем сегмент `swaggerui.path` или `scalar.path` на `path`.
Настраивать конкретный хост или порт не нужно, но если обратный прокси публикует страницу по пути, отличному от настроенного, замена ничего не находит и контракт не загружается.

## Маршруты { #endpoints }

При включенной выдаче модуль регистрирует на публичном HTTP-сервере следующие `GET`-маршруты (пути показаны со значениями `path` по умолчанию):

| Маршрут | Обработчик | Включается через |
|-------|-----------------|------------|
| `GET /openapi` (один файл) или `GET /openapi/{file}` (больше одного файла) | `OpenApiHttpServerHandler` | `enabled = true` |
| `GET /swagger-ui` | `SwaggerUIHttpServerHandler` | `swaggerui.enabled = true` |
| `GET /swagger-ui/oauth2-redirect` | `SwaggerOauthHttpServerHandler` | регистрируется автоматически вместе со `Swagger UI` |
| `GET /scalar` | `ScalarHttpServerHandler` | `scalar.enabled = true` |

Каждый маршрут использует значение `path` из своей секции конфигурации, поэтому переопределение `path` переносит соответствующий маршрут.
Путь `OAuth2`-перенаправления всегда равен `swaggerui.path` с добавленным суффиксом `/oauth2-redirect`.

Маршрут, чья секция выключена, вообще не добавляется в роутер, поэтому отвечает так же, как любой неизвестный путь.
Из-за этого включение страницы просмотра без `enabled = true` дает страницу, которая открывается, но не может получить свой контракт — маршрута выдачи файла просто нет.

## Рекомендации { #recommendations }

???+ warning "Рекомендация"

    Мы советуем использовать подход, при котором сначала создается [контракт, а затем по нему генерируется код](openapi-codegen.md).
    В этом случае модуль публикует тот же файл контракта, который используется для генерации.

    Если сначала пишется код, а контракт должен создаваться по нему, можно использовать [Swagger Gradle Plugin](https://github.com/swagger-api/swagger-core/blob/master/modules/swagger-gradle-plugin/README.md)
    вместе с [аннотациями Swagger](https://github.com/swagger-api/swagger-core/wiki/Swagger-2.X---Annotations).

???+ warning "Не опубликуйте контракт наружу по невнимательности"

    Все три маршрута живут на публичном HTTP-сервере, поэтому все включенное здесь доступно любому клиенту, который может достучаться до сервиса.
    `enabled`, `swaggerui.enabled` и `scalar.enabled` по умолчанию равны `false`; держите страницы просмотра включенными только в тех окружениях, где описание API можно читать свободно.
