---
description: "Explains Kora HTTP server, declarative and imperative controllers, routing, request and response mapping, interceptors, error handling, authorization and Undertow configuration. Use when working with @HttpController, @HttpRoute, @Path, @Query, @Header, @Cookie, @Json, @InterceptWith."
agent:
  use_when: "Use this file for Kora docs or implementation questions about Kora HTTP server, declarative and imperative controllers, routing, request and response mapping, interceptors, error handling, authorization and Undertow configuration; key triggers include @HttpController, @HttpRoute, @Path, @Query, @Header, @Cookie, @Json, @InterceptWith, HttpServerInterceptor, HttpServerParameterReader, UndertowPublicHttpServerModule, @Tag(HttpServer.class), httpServer.port, httpServer.system."
---

Модуль `HTTP-сервера` описывает входящую HTTP-границу приложения: прием запроса, разбор параметров, чтение тела,
выбор обработчика, формирование ответа, телеметрию и перехватчики. В Kora можно описывать контроллеры декларативно
через `@HttpController` и `@HttpRoute`, либо регистрировать обработчики императивно через `HttpServerRequestHandler`.

Декларативный подход подходит для большинства API: сигнатура метода описывает HTTP-контракт, а Kora во время компиляции
создает обработчик без использования `Reflection` в рантайме. Императивный подход полезен для низкоуровневых
или динамических маршрутов, где запрос удобнее обрабатывать вручную.

Обработка запросов **синхронная**. Каждый запрос выполняется на виртуальном потоке, поэтому обработчик
может блокироваться: методы контроллеров, перехватчики и мапперы возвращают результат напрямую и никогда не возвращают
`CompletionStage`, `Mono`/`Flux` или `suspend`-функцию.

???+ tip "Совет"

    **Мы советуем** использовать подход, при котором первичен контракт в формате `OpenAPI`,
    а контроллеры создаются с помощью генератора.
    Такой подход помогает сохранить согласованность контракта между потребителем и владельцем контракта
    и позволяет использовать тот же контракт для генерации клиентов.
    Подробнее про генератор смотрите в [разделе про генерацию из OpenAPI](openapi-codegen.md).

Если нужен пошаговый разбор перед справочным описанием, смотрите [HTTP-сервер](../guides/http-server.md) и [продвинутый HTTP-сервер](../guides/http-server-advanced.md).

## Подключение { #dependency }

Реализация основана на [Undertow](https://undertow.io/).
`Undertow` — это легковесный веб-сервер с открытым исходным кодом для `Java`-приложений.
Он построен на асинхронных и неблокирующих операциях ввода-вывода с использованием `NIO`,
что обеспечивает высокую производительность и низкое потребление ресурсов.

===! ":fontawesome-brands-java: `Java`"

    [Зависимость](general.md#dependencies) `build.gradle`:
    ```groovy
    implementation "io.koraframework:http-server-undertow"
    ```

    Модуль:
    ```java
    @KoraApp
    public interface Application extends UndertowPublicHttpServerModule { }
    ```

=== ":simple-kotlin: `Kotlin`"

    [Зависимость](general.md#dependencies) `build.gradle.kts`:
    ```groovy
    implementation("io.koraframework:http-server-undertow")
    ```

    Модуль:
    ```kotlin
    @KoraApp
    interface Application : UndertowPublicHttpServerModule
    ```

`UndertowPublicHttpServerModule` поднимает **два** сервера: публичный для контроллеров приложения
и системный для [проб](probes.md) и [метрик](metrics.md).
Если приложению нужен только системный сервер, подключите `UndertowSystemHttpServerModule`.

## Конфигурация { #configuration }

Основные параметры конфигурации HTTP-сервера:

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer {
        port = 8080 //(1)!
        system.port = 8085 //(2)!
        maxRequestBodySize = "256MiB" //(3)!
        telemetry.logging.enabled = false //(4)!
    }
    ```

    1.  Порт публичного `HTTP` сервера (по умолчанию: `8080`)
    2.  Порт системного `HTTP` сервера (по умолчанию: `8085`)
    3.  Максимально допустимый размер тела входящего запроса (по умолчанию: `256MiB`)
    4.  Включает логирование запросов и ответов (по умолчанию: `false`)

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      port: 8080 #(1)!
      system:
        port: 8085 #(2)!
      maxRequestBodySize: "256MiB" #(3)!
      telemetry:
        logging:
          enabled: false #(4)!
    ```

    1.  Порт публичного `HTTP` сервера (по умолчанию: `8080`)
    2.  Порт системного `HTTP` сервера (по умолчанию: `8085`)
    3.  Максимально допустимый размер тела входящего запроса (по умолчанию: `256MiB`)
    4.  Включает логирование запросов и ответов (по умолчанию: `false`)

??? note "Полная конфигурация"

    Пример полной конфигурации, описанной в классе `HttpServerConfig` (указаны значения по умолчанию либо примеры значений):

    ===! ":material-code-json: `Hocon`"

        ```javascript
        httpServer {
            port = 8080 //(1)!
            ignoreTrailingSlash = false //(2)!
            shutdownWait = "30s" //(3)!
            socketReadTimeout = "0s" //(4)!
            socketWriteTimeout = "0s" //(5)!
            socketKeepAliveEnabled = false //(6)!
            headerKeepAliveEnabled = false //(7)!
            headerServerDateEnabled = true //(8)!
            maxRequestBodySize = "256MiB" //(9)!
            telemetry {
                logging {
                    enabled = false //(10)!
                    stacktrace = true //(11)!
                    mask = "***" //(12)!
                    maskQueries = [ ] //(13)!
                    maskHeaders = [ "authorization", "cookie", "set-cookie" ] //(14)!
                    pathFull = false //(15)!
                    maxRequestBodyLogSize = "2MiB" //(16)!
                    maxResponseBodyLogSize = "2MiB" //(17)!
                }
                metrics {
                    enabled = false //(18)!
                    slo = [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] //(19)!
                    tags = { // (20)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
                tracing {
                    enabled = true //(21)!
                    tracePathFull = true //(22)!
                    attributes = { // (23)!
                        "key1" = "value1"
                        "key2" = "value2"
                    }
                }
            }
        }
        ```

        1.  Порт публичного `HTTP` сервера (по умолчанию: `8080`)
        2.  Игнорировать ли завершающий `/` в пути: при включении `/my/path` и `/my/path/` считаются одним маршрутом (по умолчанию: `false`)
        3.  Время ожидания обработки запросов перед остановкой сервера при [graceful shutdown](container.md#component-lifecycle) (по умолчанию: `30s`)
        4.  Максимальное время ожидания чтения данных из сокета или соединения, `0s` отключает таймаут (по умолчанию: `0s`)
        5.  Максимальное время ожидания записи данных в сокет или соединение, `0s` отключает таймаут (по умолчанию: `0s`)
        6.  Включать ли `TCP keep-alive` для сокета или соединения (по умолчанию: `false`)
        7.  Всегда ли отправлять заголовок ответа `Connection: keep-alive` (по умолчанию: `false`)
        8.  Всегда ли отправлять заголовок ответа `Date` (по умолчанию: `true`)
        9.  Максимально допустимый размер тела входящего запроса (по умолчанию: `256MiB`)
        10.  Включает логирование модуля (по умолчанию: `false`)
        11.  Включает логирование стектрейса при исключении (по умолчанию: `true`)
        12.  Маска, которой скрываются указанные заголовки и параметры запроса или ответа (по умолчанию: `***`)
        13.  Список параметров запроса, которые надо скрыть (по умолчанию: `[]`)
        14.  Список заголовков запроса или ответа, которые надо скрыть (по умолчанию: `[ "authorization", "cookie", "set-cookie" ]`)
        15.  Логировать ли полный путь запроса вместо шаблона маршрута; если не указано, используется шаблон, а на уровне `TRACE` — полный путь (по умолчанию не указано, опционально)
        16.  Максимальный размер тела запроса, который может быть записан в лог; тело большего размера логируется без содержимого (по умолчанию: `2MiB`)
        17.  Максимальный размер тела ответа, который может быть записан в лог; тело большего размера логируется без содержимого (по умолчанию: `2MiB`)
        18.  Включает метрики модуля (по умолчанию: `false`)
        19.  Настраивает [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
        20.  Настраивает теги метрик (по умолчанию: `{}`)
        21.  Включает трассировку модуля (по умолчанию: `true`)
        22.  Записывать ли полный путь запроса в атрибут спана `url.path` (по умолчанию: `true`)
        23.  Настраивает атрибуты трассировки (по умолчанию: `{}`)

    === ":simple-yaml: `YAML`"

        ```yaml
        httpServer:
          port: 8080 #(1)!
          ignoreTrailingSlash: false #(2)!
          shutdownWait: "30s" #(3)!
          socketReadTimeout: "0s" #(4)!
          socketWriteTimeout: "0s" #(5)!
          socketKeepAliveEnabled: false #(6)!
          headerKeepAliveEnabled: false #(7)!
          headerServerDateEnabled: true #(8)!
          maxRequestBodySize: "256MiB" #(9)!
          telemetry:
            logging:
              enabled: false #(10)!
              stacktrace: true #(11)!
              mask: "***" #(12)!
              maskQueries: [ ] #(13)!
              maskHeaders: [ "authorization", "cookie", "set-cookie" ] #(14)!
              pathFull: false #(15)!
              maxRequestBodyLogSize: "2MiB" #(16)!
              maxResponseBodyLogSize: "2MiB" #(17)!
            metrics:
              enabled: false #(18)!
              slo: [ 1, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 30000, 60000, 90000 ] #(19)!
              tags: #(20)!
                key1: value1
                key2: value2
            tracing:
              enabled: true #(21)!
              tracePathFull: true #(22)!
              attributes: #(23)!
                key1: value1
                key2: value2
        ```

        1.  Порт публичного `HTTP` сервера (по умолчанию: `8080`)
        2.  Игнорировать ли завершающий `/` в пути: при включении `/my/path` и `/my/path/` считаются одним маршрутом (по умолчанию: `false`)
        3.  Время ожидания обработки запросов перед остановкой сервера при [graceful shutdown](container.md#component-lifecycle) (по умолчанию: `30s`)
        4.  Максимальное время ожидания чтения данных из сокета или соединения, `0s` отключает таймаут (по умолчанию: `0s`)
        5.  Максимальное время ожидания записи данных в сокет или соединение, `0s` отключает таймаут (по умолчанию: `0s`)
        6.  Включать ли `TCP keep-alive` для сокета или соединения (по умолчанию: `false`)
        7.  Всегда ли отправлять заголовок ответа `Connection: keep-alive` (по умолчанию: `false`)
        8.  Всегда ли отправлять заголовок ответа `Date` (по умолчанию: `true`)
        9.  Максимально допустимый размер тела входящего запроса (по умолчанию: `256MiB`)
        10.  Включает логирование модуля (по умолчанию: `false`)
        11.  Включает логирование стектрейса при исключении (по умолчанию: `true`)
        12.  Маска, которой скрываются указанные заголовки и параметры запроса или ответа (по умолчанию: `***`)
        13.  Список параметров запроса, которые надо скрыть (по умолчанию: `[]`)
        14.  Список заголовков запроса или ответа, которые надо скрыть (по умолчанию: `[ "authorization", "cookie", "set-cookie" ]`)
        15.  Логировать ли полный путь запроса вместо шаблона маршрута; если не указано, используется шаблон, а на уровне `TRACE` — полный путь (по умолчанию не указано, опционально)
        16.  Максимальный размер тела запроса, который может быть записан в лог; тело большего размера логируется без содержимого (по умолчанию: `2MiB`)
        17.  Максимальный размер тела ответа, который может быть записан в лог; тело большего размера логируется без содержимого (по умолчанию: `2MiB`)
        18.  Включает метрики модуля (по умолчанию: `false`)
        19.  Настраивает [SLO](https://www.atlassian.com/ru/incident-management/kpis/sla-vs-slo-vs-sli) для метрик (по умолчанию: `io.koraframework.telemetry.common.TelemetryConfig.MetricsConfig#DEFAULT_SLO`)
        20.  Настраивает теги метрик (по умолчанию: `{}`)
        21.  Включает трассировку модуля (по умолчанию: `true`)
        22.  Записывать ли полный путь запроса в атрибут спана `url.path` (по умолчанию: `true`)
        23.  Настраивает атрибуты трассировки (по умолчанию: `{}`)

Метрики модуля описаны в разделе [Справочник метрик](metrics.md#http-server).

### Системный сервер { #system-server }

Системный сервер настраивается в собственной секции `httpServer.system`.
`SystemHttpServerConfig` наследует `HttpServerConfig`, поэтому там доступны все перечисленные выше опции,
плюс пути системных эндпоинтов:

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer.system {
        port = 8085 //(1)!
        metricsPath = "/metrics" //(2)!
        readinessPath = "/system/readiness" //(3)!
        livenessPath = "/system/liveness" //(4)!
        telemetry.tracing.enabled = false //(5)!
    }
    ```

    1.  Порт системного `HTTP` сервера (по умолчанию: `8085`)
    2.  Путь для получения [метрик](metrics.md) на системном сервере (по умолчанию: `/metrics`)
    3.  Путь для получения статуса [readiness пробы](probes.md) на системном сервере (по умолчанию: `/system/readiness`)
    4.  Путь для получения статуса [liveness пробы](probes.md) на системном сервере (по умолчанию: `/system/liveness`)
    5.  Включает трассировку запросов системного сервера (по умолчанию: `false`, в отличие от публичного сервера)

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      system:
        port: 8085 #(1)!
        metricsPath: "/metrics" #(2)!
        readinessPath: "/system/readiness" #(3)!
        livenessPath: "/system/liveness" #(4)!
        telemetry:
          tracing:
            enabled: false #(5)!
    ```

    1.  Порт системного `HTTP` сервера (по умолчанию: `8085`)
    2.  Путь для получения [метрик](metrics.md) на системном сервере (по умолчанию: `/metrics`)
    3.  Путь для получения статуса [readiness пробы](probes.md) на системном сервере (по умолчанию: `/system/readiness`)
    4.  Путь для получения статуса [liveness пробы](probes.md) на системном сервере (по умолчанию: `/system/liveness`)
    5.  Включает трассировку запросов системного сервера (по умолчанию: `false`, в отличие от публичного сервера)

### Undertow { #undertow }

Транспортные настройки самого `Undertow` вынесены в отдельную секцию `httpServer.undertow` и общие для обоих серверов,
поскольку настраивают единый `XnioWorker`:

===! ":material-code-json: `Hocon`"

    ```javascript
    httpServer.undertow {
        ioThreads = 4 //(1)!
        threadKeepAliveTimeout = "60s" //(2)!
    }
    ```

    1.  Количество потоков сетевого ввода-вывода (по умолчанию: количество доступных процессоров, но не меньше `2`)
    2.  Максимальное время простоя рабочего потока (по умолчанию: `60s`)

=== ":simple-yaml: `YAML`"

    ```yaml
    httpServer:
      undertow:
        ioThreads: 4 #(1)!
        threadKeepAliveTimeout: "60s" #(2)!
    ```

    1.  Количество потоков сетевого ввода-вывода (по умолчанию: количество доступных процессоров, но не меньше `2`)
    2.  Максимальное время простоя рабочего потока (по умолчанию: `60s`)

Сама обработка запроса не использует ограниченный пул блокирующих потоков: каждое соединение обслуживается
виртуальным потоком, поэтому опций `blockingThreads` и `virtualThreadsEnabled` больше нет.

Для всего, что не вынесено в конфигурацию, Kora предоставляет точки расширения `Configurer<T>`.
`Configurer<T>` получает собираемый объект и возвращает тот, который будет использован:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends UndertowPublicHttpServerModule {

        default Configurer<Undertow.Builder> undertowConfigurer() { //(1)!
            return builder -> builder.setServerOption(UndertowOptions.ENABLE_HTTP2, true);
        }

        default Configurer<HttpHandler> handlerConfigurer() { //(2)!
            return handler -> new RequestDumpingHandler(handler);
        }

        default Configurer<XnioWorker.Builder> workerConfigurer() { //(3)!
            return builder -> builder.setWorkerName("my-worker");
        }
    }
    ```

    1.  Настраивает билдер `Undertow` публичного сервера до его старта
    2.  Оборачивает корневой `HttpHandler` публичного сервера
    3.  Настраивает `XnioWorker`, общий для обоих серверов

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application : UndertowPublicHttpServerModule {

        fun undertowConfigurer(): Configurer<Undertow.Builder> = //(1)!
            Configurer { builder -> builder.setServerOption(UndertowOptions.ENABLE_HTTP2, true) }

        fun handlerConfigurer(): Configurer<HttpHandler> = //(2)!
            Configurer { handler -> RequestDumpingHandler(handler) }

        fun workerConfigurer(): Configurer<XnioWorker.Builder> = //(3)!
            Configurer { builder -> builder.setWorkerName("my-worker") }
    }
    ```

    1.  Настраивает билдер `Undertow` публичного сервера до его старта
    2.  Оборачивает корневой `HttpHandler` публичного сервера
    3.  Настраивает `XnioWorker`, общий для обоих серверов

`Configurer<Undertow.Builder>` или `Configurer<HttpHandler>` без тега применяется к **публичному** серверу.
Чтобы настроить системный сервер, пометьте компонент тегом `@SystemApi`.

## SomeController декларативный { #somecontroller-declarative }

Для создания контроллера используется аннотация `@HttpController`, а для регистрации его как зависимости — аннотация `@Component`.
Аннотация `@HttpRoute` отвечает за указание HTTP-пути и метода для конкретного метода-обработчика.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component //(1)!
    @HttpController //(2)!
    public final class SomeController {

        //(3)!
        @HttpRoute(method = HttpMethod.POST,  //(4)!
                   path = "/hello/world")  //(5)!
        public String helloWorld() {
            return "Hello World";
        }
    }
    ```

    1. Указывает, что класс является компонентом и должен быть зарегистрирован в контейнере зависимостей приложения
    2. Указывает, что класс является контроллером и содержит HTTP-обработчики
    3. Указывает, что метод является обработчиком пути в контроллере
    4. Указывает тип `HTTP` метода обработчика
    5. Указывает путь метода-обработчика

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component //(1)!
    @HttpController //(2)!
    class SomeController {

        //(3)!
        @HttpRoute(method = HttpMethod.POST,  //(4)!
                   path = "/hello/world") //(5)!
        fun helloWorld(): String {
            return "Hello World"
        }
    }
    ```

    1. Указывает, что класс является компонентом и должен быть зарегистрирован в контейнере зависимостей приложения
    2. Указывает, что класс является контроллером и содержит HTTP-обработчики
    3. Указывает, что метод является обработчиком пути в контроллере
    4. Указывает тип `HTTP` метода обработчика
    5. Указывает путь метода-обработчика

`HttpRoute.method()` имеет тип `String`, а `HttpMethod` — это набор констант (`GET`, `HEAD`, `POST`, `PUT`, `DELETE`,
`CONNECT`, `OPTIONS`, `TRACE`, `PATCH`, `QUERY`), поэтому нестандартный метод можно указать литералом:
`@HttpRoute(method = "PURGE", path = "/cache")`.

### Запрос { #request }

В этом разделе описано, как `HTTP` запрос превращается в аргументы метода контроллера.
Для частей запроса используются специальные аннотации, а тело запроса передается аргументом без такой аннотации.

#### Конвертация строковых параметров { #string-parameter-reader }

Значения из пути, параметров запроса, заголовков и `cookie` приходят строками.
Для преобразования строки в целевой тип Kora использует `HttpServerParameterReader<T>`:

```java
public interface HttpServerParameterReader<T> {
    T read(String string);
}
```

`HttpServerParameterReader<T>` ищется как компонент графа по точному типу параметра. Если параметр объявлен как `List<T>` или `Set<T>`,
конвертер применяется к каждому значению по отдельности.

`String`, `Boolean`, `Integer`, `Long`, `Double` и `UUID` разбираются самим сгенерированным обработчиком и конвертера не требуют.
Из коробки Kora также предоставляет конвертеры для `Float`, `BigInteger`, `BigDecimal`, `Duration`,
`LocalDate`, `LocalTime`, `LocalDateTime`, `OffsetTime`, `OffsetDateTime`, `ZonedDateTime` и любого `enum`.
Для `enum` по умолчанию используется имя значения через `Enum.name()`. Если значение не удалось сконвертировать, запрос завершается
ответом `400` через `HttpServerResponseException`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record UserId(long value) {}

    @Module
    public interface UserIdModule {

        default HttpServerParameterReader<UserId> userIdParameterReader() {
            return HttpServerParameterReader.of(
                value -> new UserId(Long.parseLong(value)),
                value -> "Invalid user id: " + value
            );
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class UserId(val value: Long)

    @Module
    interface UserIdModule {

        fun userIdParameterReader(): HttpServerParameterReader<UserId> {
            return HttpServerParameterReader.of(
                { value -> UserId(value.toLong()) },
                { value -> "Invalid user id: $value" }
            )
        }
    }
    ```

После регистрации конвертера пользовательский тип можно использовать в параметрах контроллера:

```java
@HttpRoute(method = HttpMethod.GET, path = "/users/{id}")
public User get(@Path("id") UserId id) {
    return userService.get(id);
}
```

#### Параметр пути { #path-parameter }

`@Path` — обозначает значение части пути запроса, сам параметр указывается в пути как `{path}`,
а имя параметра задается в `value` либо по умолчанию равно имени аргумента метода.
Значение преобразуется через `HttpServerParameterReader<T>`, поэтому доступны как встроенные, так и пользовательские типы.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/{pathName}")
        public String helloWorld(@Path("pathName") String pathValue) {
            return "Hello World";
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/{pathName}")
        fun helloWorld(
            @Path("pathName") pathValue: String
        ): String {
            return "Hello World";
        }
    }
    ```

Параметр пути всегда обязателен: если указанное в `@Path` имя отсутствует в шаблоне маршрута,
компиляция завершается ошибкой `Path parameter '...' is not present in the request mapping path`.

#### Параметр запроса { #query-parameter }

`@Query` — значение параметра запроса, имя параметра задается в `value` либо по умолчанию равно имени аргумента метода.
Поддерживаются одиночные значения, `List<T>` и `Set<T>`. `List<T>` сохраняет все значения параметра,
а `Set<T>` убирает дубликаты и сохраняет порядок первого вхождения.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        public String helloWorld(@Query("queryName") String queryValue,
                                 @Query("queryNameList") List<String> queryValues) {
            return "Hello World";
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun helloWorld(
            @Query("queryName") queryValue: String,
            @Query("queryNameList") queryValues: List<String>
        ): String {
            return "Hello World";
        }
    }
    ```

Параметр без значения (`/hello/world?queryName`) считается отсутствующим:
обязательный параметр приведет к ответу `400` с сообщением `Query parameter 'queryName' is required`.

#### Заголовок запроса { #request-header }

`@Header` — значение [заголовка запроса](https://developer.mozilla.org/ru/docs/Web/HTTP/Headers), имя параметра задается в `value` либо по умолчанию равно имени аргумента метода.
Поддерживаются одиночные значения, `List<T>` и `Set<T>`. `List<T>` и `Set<T>` используют все значения заголовка.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        public String helloWorld(@Header("headerName") String headerValue,
                                 @Header("headerNameList") List<String> headerValues) {
            return "Hello World";
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun helloWorld(
            @Header("headerName") headerValue: String,
            @Header("headerNameList") headerValues: List<String>
        ): String {
            return "Hello World";
        }
    }
    ```

#### Тело запроса { #request-body }

Для указания тела запроса используется аргумент метода без специальных аннотаций.
По умолчанию поддерживаются `byte[]`, `ByteBuffer`, `String`, `InputStream`, `HttpBodyInput`, `FormUrlEncoded`, `FormMultipart`,
а также пользовательские типы через `HttpServerRequestMapper<T>`.

`InputStream` и `HttpBodyInput` дают доступ к телу без буферизации его в памяти, что удобно для больших загрузок.

##### JSON { #json }

Чтобы указать, что тело является `JSON` и требует автоматически созданного и внедренного `JsonReader<T>`,
используется аннотация `@Json`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        @Json
        public record Request(String name) {}

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        public String helloWorld(@Json Request body) { //(1)!
            return "Hello World";
        }
    }
    ```

    1. Указывает, что тело должно читаться как `JSON`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        @Json
        data class Request(val name: String)

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun helloWorld(@Json body: Request): String { //(1)!
            return "Hello World"
        }
    }
    ```

    1. Указывает, что тело должно читаться как `JSON`

Требуется модуль [JSON](json.md).

##### Form UrlEncoded { #form-urlencoded }

В качестве типа аргумента тела можно использовать `FormUrlEncoded`, и оно будет обработано как [данные формы](https://www.w3.org/TR/html401/interact/forms.html#h-17.13.4.1).

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        public String helloWorld(FormUrlEncoded body) {
            var part = body.get("name"); //(1)!
            return "Hello World";
        }
    }
    ```

    1. `FormUrlEncoded.get(String)` возвращает `FormPart(String name, List<String> values)` либо `null`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun helloWorld(body: FormUrlEncoded): String {
            val part = body.get("name") //(1)!
            return "Hello World"
        }
    }
    ```

    1. `FormUrlEncoded.get(String)` возвращает `FormPart(String name, List<String> values)` либо `null`

##### Form Multipart { #form-multipart }

В качестве типа аргумента тела можно использовать `FormMultipart`, и оно будет обработано как [бинарная форма](https://www.w3.org/TR/html401/interact/forms.html#h-17.13.4.2).

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        public String helloWorld(FormMultipart body) {
            for (var part : body.parts()) { //(1)!
                System.out.println(part.name());
            }
            return "Hello World";
        }
    }
    ```

    1. `FormMultipart.parts()` возвращает запечатанный `FormPart`: `MultipartData`, `MultipartFile` либо `MultipartFileStream`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun helloWorld(body: FormMultipart): String {
            for (part in body.parts()) { //(1)!
                println(part.name())
            }
            return "Hello World"
        }
    }
    ```

    1. `FormMultipart.parts()` возвращает запечатанный `FormPart`: `MultipartData`, `MultipartFile` либо `MultipartFileStream`

#### Cookie { #cookie }

`@Cookie` — значение [Cookie](https://developer.mozilla.org/ru/docs/Glossary/Cookie), имя параметра задается в `value` либо по умолчанию равно имени аргумента метода.
Значение можно получить как `String`, как тип `Cookie` с именем, значением и атрибутами, либо как другой тип через `HttpServerParameterReader<T>`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        public String helloWorld(@Cookie("cookieName") String cookieValue) {
            return "Hello World";
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun helloWorld(
            @Cookie("cookieName") cookieValue: String
        ): String {
            return "Hello World";
        }
    }
    ```

#### Пользовательский параметр { #custom-parameter }

Если аргумент метода нужно собрать из запроса вручную, используется интерфейс `HttpServerRequestMapper<T>`.
Это удобно для пользовательского контекста, авторизации, сложной валидации заголовков или сразу нескольких частей запроса:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        public record UserContext(String userId, String traceId) {}

        @Component //(1)!
        public static final class RequestMapper implements HttpServerRequestMapper<UserContext> {

            @Override
            public UserContext apply(HttpServerRequest request) {
                return new UserContext(request.headers().getFirst("x-user-id"), request.headers().getFirst("x-trace-id"));
            }
        }

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        public String get(@Mapping(RequestMapper.class) UserContext context) {
            return "Hello World";
        }
    }
    ```

    1. Сгенерированный модуль контроллера **внедряет** маппер как зависимость, поэтому класс маппера обязан быть компонентом графа

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        data class UserContext(val userId: String?, val traceId: String?)

        @Component //(1)!
        class RequestMapper : HttpServerRequestMapper<UserContext> {

            override fun apply(request: HttpServerRequest): UserContext {
                return UserContext(
                    request.headers().getFirst("x-user-id"),
                    request.headers().getFirst("x-trace-id")
                )
            }
        }

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun get(@Mapping(RequestMapper::class) context: UserContext): String {
            return "Hello World"
        }
    }
    ```

    1. Сгенерированный модуль контроллера **внедряет** маппер как зависимость, поэтому класс маппера обязан быть компонентом графа

???+ warning "No component found for dependency"

    Класс маппера, указанный в `@Mapping`, никогда не создается сгенерированным модулем — он запрашивается из контейнера.
    Забытая аннотация `@Component` приводит к ошибке сборки графа:

    ```
    No component found for dependency:
      SomeController.RequestMapper (no tags)
    ```

    То же самое относится к классам перехватчиков из `@InterceptWith`.

Исключение, выброшенное маппером, превращается в ответ `400`, если только оно само не является `HttpServerResponse`,
поэтому маппер — еще и удобное место, чтобы отклонить некорректный запрос с точным статус-кодом.

#### Полный запрос { #full-request }

Метод контроллера может принимать сам `HttpServerRequest`, когда обработчику нужен исходный запрос:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        @HttpRoute(method = HttpMethod.GET, path = "/request")
        public HttpServerResponse get(HttpServerRequest request) {
            var header = request.headers().getFirst("header"); //(1)!
            var query = request.queryParams().get("query"); //(2)!
            var path = request.pathParams().get("path"); //(3)!
            return HttpServerResponse.of(200, HttpBody.plaintext(request.path()));
        }
    }
    ```

    1. `HttpHeaders` с методами `getFirst` и `getAll`
    2. `Map<String, List<String>>` параметров запроса
    3. `Map<String, String>` параметров пути, разобранных по шаблону маршрута

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        @HttpRoute(method = HttpMethod.GET, path = "/request")
        fun get(request: HttpServerRequest): HttpServerResponse {
            val header = request.headers().getFirst("header") //(1)!
            val query = request.queryParams()["query"] //(2)!
            val path = request.pathParams()["path"] //(3)!
            return HttpServerResponse.of(200, HttpBody.plaintext(request.path()))
        }
    }
    ```

    1. `HttpHeaders` с методами `getFirst` и `getAll`
    2. `Map<String, List<String>>` параметров запроса
    3. `Map<String, String>` параметров пути, разобранных по шаблону маршрута

`HttpServerRequest` также предоставляет `host()`, `scheme()`, `method()`, `path()`, `pathTemplate()`, `cookies()` и `body()`.

#### Обязательные параметры { #required-parameters }

===! ":fontawesome-brands-java: `Java`"

    По умолчанию все объявленные в методе аргументы **обязательны**.
    Если обязательное значение отсутствует в запросе, Kora возвращает ответ `400`.

=== ":simple-kotlin: `Kotlin`"

    По умолчанию обязательны все аргументы метода, которые не используют синтаксис [Kotlin Nullability](https://kotlinlang.org/docs/null-safety.html).
    Если обязательное значение отсутствует в запросе, Kora возвращает ответ `400`.

#### Необязательные параметры { #optional-parameters }

===! ":fontawesome-brands-java: `Java`"

    Если аргумент метода необязателен, то есть может отсутствовать в запросе,
    используйте `@Nullable` либо `Optional<T>` для одиночных значений:

    ```java
    @Component
    @HttpController
    public final class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        public String helloWorld(@Nullable @Query("queryName") String queryValue) { //(1)!
            return "Hello World";
        }
    }
    ```

    1.  Kora и примеры используют `org.jspecify.annotations.Nullable`; подойдет любая аннотация с простым именем `Nullable`.

=== ":simple-kotlin: `Kotlin`"

    Используйте синтаксис [Kotlin Nullability](https://kotlinlang.org/docs/null-safety.html) и отметьте такой параметр как необязательный:

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun helloWorld(@Query("queryName") queryValue: String?): String {
            return "Hello World"
        }
    }
    ```

### Ответ { #response }

По умолчанию можно использовать стандартные типы возвращаемых значений: `byte[]`, `ByteBuffer`, `String`, `HttpBodyOutput`.
Они обрабатываются со статусом `200` и соответствующим заголовком типа содержимого ответа.
Метод с типом `void` также отвечает `200` с пустым телом.

Если статус, заголовки или тело нужно указать вручную, метод может возвращать `HttpServerResponse`.
Основной контракт `HttpServerResponse` состоит из кода ответа, заголовков и опционального тела:

```java
public interface HttpServerResponse {
    int code();
    HttpHeaders headers();
    @Nullable
    HttpBodyOutput body();
}
```

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        public HttpServerResponse helloWorld() {
            return HttpServerResponse.of(
                    200, //(1)!
                    HttpHeaders.of("headerName", "headerValue"), //(2)!
                    HttpBody.plaintext("Hello World") //(3)!
            );
        }
    }
    ```

    1. Статус-код `HTTP` ответа
    2. Заголовки ответа
    3. Тело ответа

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun helloWorld(): HttpServerResponse {
            return HttpServerResponse.of(
                200, //(1)!
                HttpHeaders.of("headerName", "headerValue"), //(2)!
                HttpBody.plaintext("Hello World") //(3)!
            )
        }
    }
    ```

    1. Статус-код `HTTP` ответа
    2. Заголовки ответа
    3. Тело ответа

`HttpBody` предоставляет фабричные методы `empty()`, `plaintext(...)`, `json(...)`, `octetStream(...)` и `of(contentType, ...)`.
Для потокового ответа используйте `HttpBodyOutput.of(contentType, InputStream)` либо `HttpBodyOutput.of(contentType, os -> ...)`.

#### JSON { #json-2 }

Если ответ нужно вернуть в виде `JSON`, используется аннотация `@Json` на методе.
Kora найдет или создаст `JsonWriter<T>` для типа ответа:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        @Json
        public record Response(String greeting) {}

        @Json //(1)!
        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        public Response helloWorld() {
            return new Response("Hello World");
        }
    }
    ```

    1. Указывает, что ответ должен быть в формате `JSON`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        @Json
        data class Response(val greeting: String)

        @Json //(1)!
        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun helloWorld(): Response {
            return Response("Hello World")
        }
    }
    ```

    1. Указывает, что ответ должен быть в формате `JSON`

Требуется модуль [JSON](json.md).

#### Сущность ответа { #response-entity }

Если тело, заголовки и статус-код ответа нужно вернуть вместе,
используется `HttpResponseEntity<T>` — обертка над телом ответа.

Ниже пример, аналогичный примеру с `JSON`, но с оберткой `HttpResponseEntity`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        @Json
        public record Response(String greeting) {}

        @Json
        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        public HttpResponseEntity<Response> helloWorld() {
            return HttpResponseEntity.of(200, HttpHeaders.of("myHeader", "12345"), new Response("Hello World"));
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        @Json
        data class Response(val greeting: String)

        @Json
        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun helloWorld(): HttpResponseEntity<Response> {
            return HttpResponseEntity.of(200, HttpHeaders.of("myHeader", "12345"), Response("Hello World"));
        }
    }
    ```

Если переопределить нужно только статус-код, доступен `HttpResponseEntity.of(code, body)`.
Заголовок `content-type`, заданный в сущности, имеет приоритет над тем, который сформировал нижележащий маппер.

#### Ответ исключением { #respond-exception }

Если обработку нужно прервать и сразу вернуть ошибку, выбрасывается `HttpServerResponseException`.
Он одновременно является исключением и `HttpServerResponse`, поэтому его можно бросить из контроллера, сервиса или конвертера параметров.

Фабричные методы `HttpServerResponseException.of(...)` позволяют указать статус-код, текст ответа, причину и заголовки.
Тело ответа записывается как `text/plain;charset=utf-8`.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/{pathName}")
        public String helloWorld(@Path("pathName") String pathValue) {
            if("null".equals(pathValue)) {
                throw HttpServerResponseException.of(400, "Bad request");
            }
            return "OK";
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        @HttpRoute(method = HttpMethod.POST, path = "/hello/{pathName}")
        fun helloWorld(@Path("pathName") pathValue: String): String {
            if ("null" == pathValue) {
                throw HttpServerResponseException.of(400, "Bad request")
            }
            return "OK"
        }
    }
    ```

#### Пользовательский ответ { #custom-response }

Если ответ нужно формировать особым образом, используется интерфейс `HttpServerResponseMapper<T>`.
Он получает исходный `HttpServerRequest` и результат метода контроллера, а возвращает готовый `HttpServerResponse`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public final class SomeController {

        public record HelloWorldResponse(String greeting, String name) {}

        @Component //(1)!
        public static final class ResponseMapper implements HttpServerResponseMapper<HelloWorldResponse> {

            @Override
            public HttpServerResponse apply(HttpServerRequest request, HelloWorldResponse result) {
                return HttpServerResponse.of(200, HttpBody.plaintext(result.greeting() + " - " + result.name()));
            }
        }

        @Mapping(ResponseMapper.class)
        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        public HelloWorldResponse helloWorld() {
            return new HelloWorldResponse("Hello World", "Bob");
        }
    }
    ```

    1. Как и мапперы запроса, класс внедряется в сгенерированный модуль и обязан быть компонентом графа

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SomeController {

        data class HelloWorldResponse(val greeting: String, val name: String)

        @Component //(1)!
        class ResponseMapper : HttpServerResponseMapper<HelloWorldResponse> {

            override fun apply(request: HttpServerRequest, result: HelloWorldResponse?): HttpServerResponse { //(2)!
                requireNotNull(result)
                return HttpServerResponse.of(200, HttpBody.plaintext("${result.greeting} - ${result.name}"))
            }
        }

        @Mapping(ResponseMapper::class)
        @HttpRoute(method = HttpMethod.POST, path = "/hello/world")
        fun helloWorld(): HelloWorldResponse {
            return HelloWorldResponse("Hello World", "Bob")
        }
    }
    ```

    1. Как и мапперы запроса, класс внедряется в сгенерированный модуль и обязан быть компонентом графа
    2. Контракт объявляет результат nullable, поэтому Kotlin-переопределение обязано принимать `HelloWorldResponse?` — иначе оно не будет распознано как override

### Маршруты { #routes }

Маршрут складывается из префикса пути `@HttpController` и пути `@HttpRoute`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController("/api/v1") //(1)!
    public final class SomeController {

        @HttpRoute(method = HttpMethod.GET, path = "/pets/{id}") //(2)!
        public String get(@Path long id) {
            return "OK";
        }

        @HttpRoute(method = HttpMethod.GET, path = "/files/*") //(3)!
        public String file() {
            return "OK";
        }
    }
    ```

    1. Префикс пути, применяемый ко всем маршрутам контроллера
    2. Маршрут с параметром пути, итоговый маршрут — `/api/v1/pets/{id}`
    3. Маршрут с завершающим шаблоном, итоговый маршрут — `/api/v1/files/*`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController("/api/v1") //(1)!
    class SomeController {

        @HttpRoute(method = HttpMethod.GET, path = "/pets/{id}") //(2)!
        fun get(@Path id: Long): String = "OK"

        @HttpRoute(method = HttpMethod.GET, path = "/files/*") //(3)!
        fun file(): String = "OK"
    }
    ```

    1. Префикс пути, применяемый ко всем маршрутам контроллера
    2. Маршрут с параметром пути, итоговый маршрут — `/api/v1/pets/{id}`
    3. Маршрут с завершающим шаблоном, итоговый маршрут — `/api/v1/files/*`

Правила сопоставления маршрутов:

- Параметр пути `{name}` соответствует одному сегменту пути.
- Шаблон `*` допустим **один раз** и только в **последнем** сегменте: `/files/*`, `/files/*.js`, `/files/file-*.txt`,
  `/tenant/{id}/report-*.json`. Все остальное (`/foo/*/bar`, `/foo/**`, `/foo/a*b*c`, `/foo/{*}`) не компилируется с ошибкой
  `HTTP server route path is invalid`.
- Два обработчика с эквивалентными шаблонами для одного метода приводят к падению сервера на старте с сообщением
  `Cannot add path template ..., matcher already contains an equivalent pattern ...`.
- Неизвестный путь отвечает `404`; известный путь с неподдерживаемым методом отвечает `405`
  и заголовком `Allow` со списком зарегистрированных методов.
- При `httpServer.ignoreTrailingSlash = true` для каждого маршрута без шаблона регистрируется дополнительный вариант,
  поэтому `/my/path` и `/my/path/` попадают в один обработчик.

### Сигнатуры { #signatures }

Доступные из коробки сигнатуры декларативных методов-обработчиков `HTTP`:

===! ":fontawesome-brands-java: `Java`"

    Под `T` подразумевается тип возвращаемого значения.

    - `T myMethod()`
    - `void myMethod()` — отвечает `200` с пустым телом

    Возврат `CompletionStage<T>`, `Future<T>` либо реактивного `Publisher<T>` **не поддерживается**:
    процессор выводит предупреждение, что такой тип *"is unsupported and has no meaning"*,
    а сборка графа затем падает, потому что для такого типа нет `HttpServerResponseMapper`.

=== ":simple-kotlin: `Kotlin`"

    Под `T` подразумевается тип возвращаемого значения.

    - `myMethod(): T`
    - `myMethod(): Unit` — отвечает `200` с пустым телом

    `suspend`-методы **не поддерживаются** и отклоняются на этапе компиляции с сообщением
    *"Suspend methods are not supported by the HTTP server controller generator"*.
    Для параллельной работы внутри обработчика используйте `StructuredTaskScope` вместо корутин.

## Перехватчики { #interceptors }

Перехватчики позволяют изменить поведение или добавить общую логику вокруг обработки запроса.
Используется интерфейс `HttpServerInterceptor`:

```java
public interface HttpServerInterceptor {
    HttpServerResponse intercept(HttpServerRequest request, InterceptChain chain) throws Exception;

    interface InterceptChain {
        HttpServerResponse process(HttpServerRequest request) throws Exception;
    }
}
```

Перехватчик получает `HttpServerRequest` и цепочку дальнейшей обработки.
Чтобы передать запрос дальше, вызывается `chain.process(request)`. Если перехватчик сам возвращает ответ,
обработчик контроллера не вызывается. Поскольку вызов синхронный, исключение из глубины цепочки
перехватывается обычным `try/catch`.

Перехватчики можно применять:

- К конкретным методам контроллера — `@InterceptWith` на методе
- Ко всему контроллеру — `@InterceptWith` на классе
- Сразу ко всем контроллерам — зарегистрировать компонент перехватчика с тегом `@Tag(HttpServer.class)`; глобальных перехватчиков может быть несколько

`@InterceptWith` — повторяемая аннотация, при этом перехватчики, объявленные на классе, выполняются раньше объявленных на методе.
Глобальные перехватчики применяются в детерминированном порядке, отсортированном по простому имени класса перехватчика.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    @InterceptWith(SomeController.ControllerInterceptor.class) //(1)!
    public final class SomeController {

        @Component
        public static final class ControllerInterceptor implements HttpServerInterceptor {

            @Override
            public HttpServerResponse intercept(HttpServerRequest request, InterceptChain chain) throws Exception {
                return chain.process(request);
            }
        }

        @Component
        public static final class MethodInterceptor implements HttpServerInterceptor {

            @Override
            public HttpServerResponse intercept(HttpServerRequest request, InterceptChain chain) throws Exception {
                return chain.process(request);
            }
        }

        @Tag(HttpServer.class) //(2)!
        @Component
        public static final class ServerInterceptor implements HttpServerInterceptor {

            @Override
            public HttpServerResponse intercept(HttpServerRequest request, InterceptChain chain) throws Exception {
                return chain.process(request);
            }
        }

        @InterceptWith(MethodInterceptor.class) //(3)!
        @HttpRoute(method = HttpMethod.POST, path = "/intercepted")
        public String helloWorld() {
            return "Hello World";
        }
    }
    ```

    1. Перехватывает все маршруты этого контроллера
    2. Перехватывает все маршруты публичного сервера, включая ответы `404` и `405`
    3. Перехватывает только этот маршрут

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    @InterceptWith(SomeController.ControllerInterceptor::class) //(1)!
    class SomeController {

        @Component
        class ControllerInterceptor : HttpServerInterceptor {

            override fun intercept(request: HttpServerRequest, chain: HttpServerInterceptor.InterceptChain): HttpServerResponse {
                return chain.process(request)
            }
        }

        @Component
        class MethodInterceptor : HttpServerInterceptor {

            override fun intercept(request: HttpServerRequest, chain: HttpServerInterceptor.InterceptChain): HttpServerResponse {
                return chain.process(request)
            }
        }

        @Tag(HttpServer::class) //(2)!
        @Component
        class ServerInterceptor : HttpServerInterceptor {

            override fun intercept(request: HttpServerRequest, chain: HttpServerInterceptor.InterceptChain): HttpServerResponse {
                return chain.process(request)
            }
        }

        @InterceptWith(MethodInterceptor::class) //(3)!
        @HttpRoute(method = HttpMethod.POST, path = "/intercepted")
        fun helloWorld(): String {
            return "Hello World"
        }
    }
    ```

    1. Перехватывает все маршруты этого контроллера
    2. Перехватывает все маршруты публичного сервера, включая ответы `404` и `405`
    3. Перехватывает только этот маршрут

???+ warning "Тег глобального перехватчика"

    Фреймворк собирает глобальные перехватчики **только** по тегу `@Tag(HttpServer.class)` —
    в `HttpServerModule` зависимость объявлена как `@Tag(HttpServer.class) All<HttpServerInterceptor> interceptors`.
    Любой другой тег компилируется без ошибок, а перехватчик просто никогда не вызывается,
    и обработка ошибок, аутентификация или логирование исчезают без единого предупреждения. Проверяйте это тестом.

    Чтобы перехватывать все запросы **системного** сервера, используйте тег `@SystemApi`.

### Обработка ошибок { #error-handling }

Обработку ошибок для всех `HTTP` ответов также можно реализовать через перехватчик.
Ниже пример глобального обработчика, который превращает исключения в `JSON` ответ.

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(HttpServer.class)
    @Component
    public final class ErrorInterceptor implements HttpServerInterceptor {

        private static final Logger logger = LoggerFactory.getLogger(ErrorInterceptor.class);

        private final JsonWriter<ErrorTO> errorWriter;

        public ErrorInterceptor(JsonWriter<ErrorTO> errorWriter) { //(1)!
            this.errorWriter = errorWriter;
        }

        @Override
        public HttpServerResponse intercept(HttpServerRequest request, InterceptChain chain) {
            try {
                return chain.process(request);
            } catch (HttpServerResponseException e) { //(2)!
                return e;
            } catch (Exception e) {
                var body = HttpBody.json(errorWriter.toByteArray(new ErrorTO(e.getMessage()))); //(3)!
                if (e instanceof IllegalArgumentException) {
                    return HttpServerResponse.of(400, body);
                } else if (e instanceof TimeoutException) {
                    return HttpServerResponse.of(408, body);
                } else {
                    logger.error("Request '{} {}' failed", request.method(), request.path(), e);
                    return HttpServerResponse.of(500, body);
                }
            }
        }
    }
    ```

    1. У перехватчика есть зависимость в конструкторе, поэтому он обязан быть компонентом графа
    2. `HttpServerResponseException` сам является ответом, поэтому он возвращается в том виде, в каком его должен увидеть клиент
    3. `JsonWriter.toByteArray(...)` не объявляет проверяемых исключений, поэтому обрабатывать `IOException` не нужно

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(HttpServer::class)
    @Component
    class ErrorInterceptor(private val errorWriter: JsonWriter<ErrorTO>) : HttpServerInterceptor { //(1)!

        private val logger = LoggerFactory.getLogger(ErrorInterceptor::class.java)

        override fun intercept(request: HttpServerRequest, chain: HttpServerInterceptor.InterceptChain): HttpServerResponse {
            try {
                return chain.process(request)
            } catch (e: HttpServerResponseException) { //(2)!
                return e
            } catch (e: Exception) {
                val body = HttpBody.json(errorWriter.toByteArray(ErrorTO(e.message))) //(3)!
                return when (e) {
                    is IllegalArgumentException -> HttpServerResponse.of(400, body)
                    is TimeoutException -> HttpServerResponse.of(408, body)
                    else -> {
                        logger.error("Request '{} {}' failed", request.method(), request.path(), e)
                        HttpServerResponse.of(500, body)
                    }
                }
            }
        }
    }
    ```

    1. У перехватчика есть зависимость в конструкторе, поэтому он обязан быть компонентом графа
    2. `HttpServerResponseException` сам является ответом, поэтому он возвращается в том виде, в каком его должен увидеть клиент
    3. `JsonWriter.toByteArray(...)` не объявляет проверяемых исключений, поэтому обрабатывать `IOException` не нужно

Ошибки разбора параметров Kora обрабатывает до вызова метода контроллера: значение, которое не удалось прочитать,
приводит к ответу `400` с сообщением от `HttpServerParameterReader`. Такой ответ тоже проходит через цепочку перехватчиков,
поэтому глобальный обработчик может его переформировать.

## SomeController императивный { #somecontroller-imperative }

Чтобы создать контроллер, надо реализовать интерфейс `HttpServerRequestHandler.HandlerFunction`,
а затем зарегистрировать его в обработчике `HttpServerRequestHandler`.

Следующий пример показывает, как обработать все описанные выше декларативные параметры запроса:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface SomeModule {

        default HttpServerRequestHandler someHttpHandler() {
            return HttpServerRequestHandlerImpl.of(HttpMethod.POST, //(1)!
                                                   "/hello/{world}", //(2)!
                                                   (request) -> {
                var path = HttpRequestHandlerUtils.parsePathString(request, "world");
                var query = HttpRequestHandlerUtils.parseQueryStringNullable(request, "query");
                var queries = HttpRequestHandlerUtils.parseQueryStringListNullable(request, "Queries");
                var header = HttpRequestHandlerUtils.parseHeaderStringNullable(request, "header");
                var headers = HttpRequestHandlerUtils.parseHeaderStringListNullable(request, "Headers");
                return HttpServerResponse.of(200, HttpBody.plaintext("Hello World"));
            });
        }
    }
    ```

    1. Указывает тип `HTTP` метода обработчика
    2. Указывает путь метода-обработчика

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface SomeModule {

        fun someHttpHandler(): HttpServerRequestHandler {
            return HttpServerRequestHandlerImpl.of(
                HttpMethod.POST, //(1)!
                "/hello/{world}" //(2)!
            ) { request: HttpServerRequest ->
                val path = HttpRequestHandlerUtils.parsePathString(request, "world")
                val query = HttpRequestHandlerUtils.parseQueryStringNullable(request, "query")
                val queries = HttpRequestHandlerUtils.parseQueryStringListNullable(request, "Queries")
                val header = HttpRequestHandlerUtils.parseHeaderStringNullable(request, "header")
                val headers = HttpRequestHandlerUtils.parseHeaderStringListNullable(request, "Headers")
                HttpServerResponse.of(200, HttpBody.plaintext("Hello World"))
            }
        }
    }
    ```

    1. Указывает тип `HTTP` метода обработчика
    2. Указывает путь метода-обработчика

У `HttpServerRequestHandlerImpl` есть и сокращенные фабрики под каждый метод — `get`, `head`, `post`, `put`, `delete`,
`connect`, `options`, `trace`, `patch` — а также перегрузка с флагом `enabled`, позволяющая исключить обработчик из маршрутизации,
не убирая его из графа.

`HttpServerRequestHandler` без тега регистрируется на публичном сервере; обработчик с тегом `@SystemApi`
регистрируется на системном сервере.

## Авторизация { #authorization }

Kora предоставляет механизм извлечения контекста авторизации из HTTP-запросов через интерфейс `HttpServerPrincipalExtractor`.
Этот интерфейс позволяет реализовать любую схему аутентификации: [Basic/ApiKey/Bearer/OAuth](https://swagger.io/docs/specification/authentication/).

### Как это работает { #how-it-works }

`HttpServerPrincipalExtractor<T, P>` получает извлеченные из запроса учетные данные и возвращает объект `Principal`
либо `null`, если данные не приняты.

```java
public interface HttpServerPrincipalExtractor<T, P extends Principal> {
    @Nullable
    P extract(HttpServerRequest request, @Nullable T token);
}
```

Где:

- `request` — текущий HTTP-запрос, из которого можно извлечь дополнительные данные (заголовки, параметры)
- `token` — учетные данные, взятые из запроса (заголовок `Authorization`, заголовок с API-ключом, параметр запроса либо cookie)
- `T` — тип учетных данных: `String` для одной схемы безопасности либо сгенерированная запись `AuthData`, если схем несколько
- `P extends Principal` — тип контекста авторизации

Экстрактор **вызывается перехватчиками, сгенерированными из OpenAPI-контракта** — смотрите [Интеграцию с OpenAPI](#openapi).
Сгенерированный перехватчик читает учетные данные, вызывает `extract(...)` и при ненулевом результате выполняет остаток цепочки
внутри `Principal.with(principal, () -> chain.process(request))`. Если результат `null` (либо не хватает требуемых scope),
он выбрасывает `HttpServerResponseException.of(401, "Unauthorized")`.

Для сервиса без OpenAPI-контракта пишется обычный [перехватчик](#interceptors) — смотрите [Авторизацию без OpenAPI](#authorization-manual).

### Пользовательский Principal { #custom-principal }

При необходимости можно создать простой principal для API с полями или без них:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record ApiPrincipal(String client) implements Principal {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class ApiPrincipal(val client: String) : Principal
    ```

Чтобы передавать дополнительную информацию об авторизации (userId, роли, scope), создайте свою реализацию `Principal`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record UserPrincipal(String userId, List<String> roles) implements Principal {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class UserPrincipal(val userId: String, val roles: List<String>) : Principal
    ```

Если требуется работа со scope, используется интерфейс `PrincipalWithScopes`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    public record ScopedUser(String userId, Collection<String> scopes) implements PrincipalWithScopes {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    data class ScopedUser(val userId: String, val scopes: Collection<String>) : PrincipalWithScopes
    ```

### Простой пример { #basic-example }

Простой пример проверки API-ключа, где `ApiKeyAuth` — имя схемы безопасности из OpenAPI-контракта:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface AuthModule {

        @ConfigSource("auth.apiKey")
        interface ApiKeyAuthConfig {
            String value();
        }

        @Tag(ApiSecurity.ApiKeyAuth.class) //(1)!
        default HttpServerPrincipalExtractor<String, Principal> apiKeyExtractor(ApiKeyAuthConfig config) {
            return (request, value) -> {
                if (value == null || !config.value().equals(value)) {
                    return null; //(2)!
                }
                return new ApiPrincipal("api-client");
            };
        }
    }
    ```

    1. Тег назван по имени схемы безопасности из контракта
    2. Возврат `null` заставляет сгенерированный перехватчик ответить `401 Unauthorized`

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface AuthModule {

        @ConfigSource("auth.apiKey")
        interface ApiKeyAuthConfig {
            fun value(): String
        }

        @Tag(ApiSecurity.ApiKeyAuth::class) //(1)!
        fun apiKeyExtractor(config: ApiKeyAuthConfig): HttpServerPrincipalExtractor<String, Principal> {
            return HttpServerPrincipalExtractor { request, value ->
                if (value == null || config.value() != value) {
                    null //(2)!
                } else {
                    ApiPrincipal("api-client")
                }
            }
        }
    }
    ```

    1. Тег назван по имени схемы безопасности из контракта
    2. Возврат `null` заставляет сгенерированный перехватчик ответить `401 Unauthorized`

### Bearer-токен { #bearer }

Пример проверки Bearer-токена с собственной реализацией `Principal`.
Для схем `Bearer`, `Basic` и `OAuth` сгенерированный перехватчик передает целиком значение заголовка `Authorization`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface BearerAuthModule {

        @Tag(ApiSecurity.BearerAuth.class)
        default HttpServerPrincipalExtractor<String, Principal> bearerExtractor(TokenValidator validator) {
            return (request, value) -> {
                if (value == null || !value.startsWith("Bearer ")) {
                    return null;
                }

                var token = value.substring("Bearer ".length());
                var userData = validator.validate(token);
                return userData == null
                    ? null
                    : new UserPrincipal(userData.userId(), userData.roles());
            };
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface BearerAuthModule {

        @Tag(ApiSecurity.BearerAuth::class)
        fun bearerExtractor(validator: TokenValidator): HttpServerPrincipalExtractor<String, Principal> {
            return HttpServerPrincipalExtractor { request, value ->
                if (value == null || !value.startsWith("Bearer ")) {
                    null
                } else {
                    val token = value.substring("Bearer ".length)
                    validator.validate(token)
                        ?.let { UserPrincipal(it.userId, it.roles) }
                }
            }
        }
    }
    ```

### Получение Principal { #getting-principal }

Текущий контекст авторизации привязан к `ScopedValue` и доступен в любом месте обработки запроса:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    @HttpController
    public class SecureController {

        @HttpRoute(method = HttpMethod.GET, path = "/secure")
        public String getSecureData() {
            Principal principal = Principal.current(); //(1)!
            if (principal instanceof UserPrincipal user) {
                return "Hello, user: " + user.userId();
            }
            throw new SecurityException("Not authenticated");
        }
    }
    ```

    1. Возвращает `null`, если для текущего запроса principal не привязан

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    @HttpController
    class SecureController {

        @HttpRoute(method = HttpMethod.GET, path = "/secure")
        fun getSecureData(): String {
            val principal = Principal.current() //(1)!
            return if (principal is UserPrincipal) {
                "Hello, user: ${principal.userId}"
            } else {
                throw SecurityException("Not authenticated")
            }
        }
    }
    ```

    1. Возвращает `null`, если для текущего запроса principal не привязан

### OAuth2 { #oauth2 }

Для авторизации OAuth2 создается `HttpServerPrincipalExtractor`, который проверяет токен через OAuth2-провайдер.
Для схемы безопасности `OAuth` сгенерированный код ожидает `PrincipalWithScopes`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Module
    public interface OAuth2Module {

        @Tag(ApiSecurity.OAuth.class)
        default HttpServerPrincipalExtractor<String, PrincipalWithScopes> oauth2Extractor(OAuth2Client oauth2Client) {
            return (request, value) -> {
                if (value == null || !value.startsWith("Bearer ")) {
                    return null;
                }

                var token = value.substring("Bearer ".length());
                var introspection = oauth2Client.introspect(token);
                return introspection == null
                    ? null
                    : new ScopedUser(introspection.subject(), introspection.scopes());
            };
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Module
    interface OAuth2Module {

        @Tag(ApiSecurity.OAuth::class)
        fun oauth2Extractor(oauth2Client: OAuth2Client): HttpServerPrincipalExtractor<String, PrincipalWithScopes> {
            return HttpServerPrincipalExtractor { request, value ->
                if (value == null || !value.startsWith("Bearer ")) {
                    null
                } else {
                    val token = value.substring("Bearer ".length)
                    oauth2Client.introspect(token)
                        ?.let { ScopedUser(it.subject, it.scopes) }
                }
            }
        }
    }
    ```

#### Проверка Scope { #scope-check }

Если scope объявлены в OpenAPI-контракте, сгенерированный перехватчик проверяет их сам:
если возвращенный `PrincipalWithScopes.scopes()` не содержит требуемого scope, запрос завершается ответом `401`.

Вне OpenAPI перехватчик проверяет scope и сам привязывает principal через `Principal.with(...)`,
чтобы остаток цепочки мог прочитать его через `Principal.current()`:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class ScopeCheckingInterceptor implements HttpServerInterceptor {

        private final AuthConfig config;
        private final TokenValidator validator;

        public ScopeCheckingInterceptor(AuthConfig config, TokenValidator validator) {
            this.config = config;
            this.validator = validator;
        }

        @Override
        public HttpServerResponse intercept(HttpServerRequest request, InterceptChain chain) throws Exception {
            var principal = validator.validate(request.headers().getFirst("authorization"));
            if (!(principal instanceof PrincipalWithScopes scoped)) {
                throw HttpServerResponseException.of(403, "No scopes available");
            }
            if (!scoped.scopes().contains(config.requiredScope())) {
                throw HttpServerResponseException.of(403, "Insufficient scope");
            }

            return Principal.with(scoped, () -> chain.process(request)); //(1)!
        }
    }
    ```

    1. Привязывает principal к текущему запросу, чтобы дальше по цепочке `Principal.current()` возвращал его

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ScopeCheckingInterceptor(
        private val config: AuthConfig,
        private val validator: TokenValidator
    ) : HttpServerInterceptor {

        override fun intercept(request: HttpServerRequest, chain: HttpServerInterceptor.InterceptChain): HttpServerResponse {
            val principal = validator.validate(request.headers().getFirst("authorization"))
            if (principal !is PrincipalWithScopes) {
                throw HttpServerResponseException.of(403, "No scopes available")
            }
            if (!principal.scopes.contains(config.requiredScope())) {
                throw HttpServerResponseException.of(403, "Insufficient scope")
            }

            return Principal.with(principal) { chain.process(request) } //(1)!
        }
    }
    ```

    1. Привязывает principal к текущему запросу, чтобы дальше по цепочке `Principal.current()` возвращал его

### Интеграция с OpenAPI { #openapi }

При использовании [генератора OpenAPI](openapi-codegen.md) авторизация настраивается автоматически на основе OpenAPI-спецификации.
Генератор создает:

1. Интерфейс `ApiSecurity` с классом-маркером для каждой схемы безопасности, названным по имени схемы (`ApiKeyAuth`, `BearerAuth`, `BasicAuth`, `CookieAuth`, `OAuth`)
2. `HttpServerInterceptor` для каждого требования безопасности, применяемый к сгенерированному контроллеру
3. Требование предоставить `HttpServerPrincipalExtractor` с соответствующим `@Tag`

Пример из [kora-examples](https://github.com/kora-projects/kora-examples):

===! ":fontawesome-brands-java: `Java`"

    ```java
    @KoraApp
    public interface Application extends
            HoconConfigModule,
            UndertowPublicHttpServerModule,
            JsonModule {

        @Tag(ApiSecurity.ApiKeyAuth.class)
        default HttpServerPrincipalExtractor<String, Principal> apiKeyExtractor(DataApiAuthConfig config) {
            return (request, value) -> {
                if (value == null || !config.value().equals(value)) {
                    return null;
                }
                return new DataApiPrincipal("data-api-client");
            };
        }
    }
    ```

    где `DataApiPrincipal`:

    ```java
    public record DataApiPrincipal(String name) implements Principal {}
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @KoraApp
    interface Application :
        HoconConfigModule,
        UndertowPublicHttpServerModule,
        JsonModule {

        @Tag(ApiSecurity.ApiKeyAuth::class)
        fun apiKeyExtractor(config: DataApiAuthConfig): HttpServerPrincipalExtractor<String, Principal> {
            return HttpServerPrincipalExtractor { request, value ->
                if (value == null || config.value() != value) {
                    null
                } else {
                    DataApiPrincipal("data-api-client")
                }
            }
        }
    }
    ```

    где `DataApiPrincipal`:

    ```kotlin
    data class DataApiPrincipal(val name: String) : Principal
    ```

Конфигурация:

```hocon
auth.apiKey {
  value = "secret-api-key-123"
}
```

Если одна операция требует сразу несколько схем, тег экстрактора склеивает имена схем через `With`
(`BearerAuthWithApiKeyAuth`), а генератор добавляет запись `ApiSecurity.<Tag>AuthData` со всеми учетными данными,
поэтому экстрактор объявляется как `HttpServerPrincipalExtractor<ApiSecurity.BearerAuthWithApiKeyAuthAuthData, Principal>`.
Перехватчик для такого требования получает отдельный тег, где имена схем склеены через `And`
(`ApiSecurity.BearerAuthAndApiKeyAuth`); альтернативные требования одной операции склеиваются через `_`.

### Авторизация без OpenAPI { #authorization-manual }

Без сгенерированного `ApiSecurity` никто не вызывает `HttpServerPrincipalExtractor`, поэтому авторизация реализуется
обычным [перехватчиком](#interceptors) на контроллере, на маршруте либо глобально:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Component
    public final class ApiKeyAuthInterceptor implements HttpServerInterceptor {

        private final ApiKeyAuthConfig config;

        public ApiKeyAuthInterceptor(ApiKeyAuthConfig config) {
            this.config = config;
        }

        @Override
        public HttpServerResponse intercept(HttpServerRequest request, InterceptChain chain) throws Exception {
            var authorization = request.headers().getFirst("authorization");
            if (!this.config.value().equals(authorization)) {
                throw new SecurityException("Invalid API key"); //(1)!
            }
            return chain.process(request);
        }
    }
    ```

    1. Исключение превращается в `403` глобальным [обработчиком ошибок авторизации](#auth-error-handling)

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Component
    class ApiKeyAuthInterceptor(private val config: ApiKeyAuthConfig) : HttpServerInterceptor {

        override fun intercept(request: HttpServerRequest, chain: HttpServerInterceptor.InterceptChain): HttpServerResponse {
            val authorization = request.headers().getFirst("authorization")
            if (config.value() != authorization) {
                throw SecurityException("Invalid API key") //(1)!
            }
            return chain.process(request)
        }
    }
    ```

    1. Исключение превращается в `403` глобальным [обработчиком ошибок авторизации](#auth-error-handling)

Далее перехватчик подключается через `@InterceptWith(ApiKeyAuthInterceptor.class)` на контроллере либо на отдельном маршруте.

### Обработка ошибок авторизации { #auth-error-handling }

Когда экстрактор возвращает `null` либо не хватает требуемых scope, сгенерированный перехватчик отвечает
статусом `401` и телом `Unauthorized`.
Чтобы формировать ошибки авторизации самостоятельно, добавьте глобальный перехватчик:

===! ":fontawesome-brands-java: `Java`"

    ```java
    @Tag(HttpServer.class)
    @Component
    public final class AuthErrorInterceptor implements HttpServerInterceptor {

        @Override
        public HttpServerResponse intercept(HttpServerRequest request, InterceptChain chain) throws Exception {
            try {
                return chain.process(request);
            } catch (IllegalAccessException e) {
                return HttpServerResponse.of(401, HttpBody.plaintext("Unauthorized: " + e.getMessage()));
            } catch (SecurityException e) {
                return HttpServerResponse.of(403, HttpBody.plaintext("Forbidden: " + e.getMessage()));
            }
        }
    }
    ```

=== ":simple-kotlin: `Kotlin`"

    ```kotlin
    @Tag(HttpServer::class)
    @Component
    class AuthErrorInterceptor : HttpServerInterceptor {

        override fun intercept(request: HttpServerRequest, chain: HttpServerInterceptor.InterceptChain): HttpServerResponse {
            try {
                return chain.process(request)
            } catch (e: IllegalAccessException) {
                return HttpServerResponse.of(401, HttpBody.plaintext("Unauthorized: ${e.message}"))
            } catch (e: SecurityException) {
                return HttpServerResponse.of(403, HttpBody.plaintext("Forbidden: ${e.message}"))
            }
        }
    }
    ```

Поскольку глобальный перехватчик оборачивает сгенерированный перехватчик безопасности, он также видит
`HttpServerResponseException` с кодом `401`, выброшенный сгенерированным кодом, и может заменить его собственным ответом.

## Телеметрия { #telemetry }

HTTP-сервер использует контракт телеметрии для логирования, метрик и трассировки запросов.
Конфигурация телеметрии (секция `telemetry { logging / metrics / tracing }`) описана в разделе [Конфигурация](#configuration).
Точки расширения находятся в `io.koraframework.http.server.common.telemetry`.

На каждый HTTP-запрос создается `HttpServerObservation`, который закрывается при завершении запроса.
Он наблюдает запрос, ответ, `HttpResultCode` и возникшее исключение.

Фабрика по умолчанию `DefaultHttpServerTelemetryFactory` объединяет три части:

- `DefaultHttpServerLoggerFactory` создает логгер начала и завершения запроса;
- `DefaultHttpServerMetricsFactory` создает метрики запроса;
- `io.opentelemetry.api.trace.Tracer`, если он есть в графе, создает спан запроса.

Логи запроса и ответа пишутся двумя отдельными логгерами, поэтому их уровень настраивается независимо:

===! ":material-code-json: `Hocon`"

    ```javascript
    logging.levels {
        "io.koraframework.http.server.common.HttpServer.request" = "DEBUG" //(1)!
        "io.koraframework.http.server.common.HttpServer.response" = "TRACE" //(2)!
    }
    ```

    1. На уровне `INFO` логируется только операция, `DEBUG` добавляет заголовки и параметры запроса
    2. `TRACE` дополнительно пишет тело, ограниченное `maxRequestBodyLogSize` / `maxResponseBodyLogSize`

=== ":simple-yaml: `YAML`"

    ```yaml
    logging:
      levels:
        "io.koraframework.http.server.common.HttpServer.request": "DEBUG" #(1)!
        "io.koraframework.http.server.common.HttpServer.response": "TRACE" #(2)!
    ```

    1. На уровне `INFO` логируется только операция, `DEBUG` добавляет заголовки и параметры запроса
    2. `TRACE` дополнительно пишет тело, ограниченное `maxRequestBodyLogSize` / `maxResponseBodyLogSize`

Заголовки из `maskHeaders` и параметры запроса из `maskQueries` заменяются значением `mask`.
В логируемой операции по умолчанию используется шаблон маршрута, а полный путь — при `pathFull = true` либо на уровне логгера `TRACE`.

Метрики и трассировка описаны в разделе [Справочник метрик](metrics.md#http-server).
